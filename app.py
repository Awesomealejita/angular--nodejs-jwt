import json
import os
import smtplib
import ssl
import time
import zipfile
from email.message import EmailMessage
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List
import cgi

BASE_DIR = Path(__file__).parent
PUBLIC_DIR = BASE_DIR / "public"
TEMPLATE_DIR = BASE_DIR / "storage" / "templates"
OUTGOING_DIR = BASE_DIR / "storage" / "outgoing"

TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
OUTGOING_DIR.mkdir(parents=True, exist_ok=True)


def escape_xml(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\"", "&quot;")
        .replace("'", "&apos;")
    )


def render_docx(template_path: Path, context: Dict[str, str], output_path: Path) -> Path:
    with zipfile.ZipFile(template_path, "r") as zin:
        with zipfile.ZipFile(output_path, "w") as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "word/document.xml":
                    xml = data.decode("utf-8")
                    for key, value in context.items():
                        xml = xml.replace(f"{{{{{key}}}}}", escape_xml(value))
                    data = xml.encode("utf-8")
                zout.writestr(item, data)
    return output_path


def smtp_configured() -> bool:
    return bool(os.getenv("SMTP_HOST"))


def send_email(recipient: str, subject: str, body: str, attachment_path: Path) -> Dict[str, str]:
    host = os.getenv("SMTP_HOST")
    if not host:
        return {"status": "skipped", "reason": "SMTP not configured"}

    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    sender = os.getenv("SMTP_FROM", user or "noreply@example.com")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(body)

    attachment_bytes = attachment_path.read_bytes()
    message.add_attachment(
        attachment_bytes,
        maintype="application",
        subtype="vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=attachment_path.name,
    )

    context = ssl.create_default_context()
    with smtplib.SMTP(host, port) as server:
        server.starttls(context=context)
        if user and password:
            server.login(user, password)
        server.send_message(message)

    return {"status": "sent", "to": recipient}


class TemplateServer(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def _set_headers(self, status: int = 200, content_type: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        if self.path.startswith("/api/templates"):
            self.handle_list_templates()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api/templates"):
            self.handle_upload_template()
        elif self.path.startswith("/api/send"):
            self.handle_send_documents()
        else:
            self._set_headers(404)
            self.wfile.write(b"{\"error\":\"Not found\"}")

    def handle_list_templates(self):
        templates = [f.name for f in TEMPLATE_DIR.glob("*.docx")]
        self._set_headers()
        self.wfile.write(json.dumps({"templates": templates}).encode())

    def handle_upload_template(self):
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            self._set_headers(400)
            self.wfile.write(b"{\"error\":\"Multipart form required\"}")
            return

        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": content_type,
                "CONTENT_LENGTH": self.headers.get("Content-Length", "0"),
            },
        )
        file_field = form["file"] if "file" in form else None
        if not file_field or not getattr(file_field, "file", None):
            self._set_headers(400)
            self.wfile.write(b"{\"error\":\"No file provided\"}")
            return

        filename = Path(file_field.filename).name
        if not filename.lower().endswith(".docx"):
            self._set_headers(400)
            self.wfile.write(b"{\"error\":\"Only .docx files are allowed\"}")
            return

        destination = TEMPLATE_DIR / filename
        with destination.open("wb") as f:
            f.write(file_field.file.read())

        self._set_headers(201)
        self.wfile.write(json.dumps({"message": "Template uploaded", "name": filename}).encode())

    def handle_send_documents(self):
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            self._set_headers(400)
            self.wfile.write(b"{\"error\":\"Invalid JSON\"}")
            return

        template_name = payload.get("template")
        mutuas: List[Dict[str, str]] = payload.get("mutuas", [])
        if not template_name or not mutuas:
            self._set_headers(400)
            self.wfile.write(b"{\"error\":\"Template and mutuas are required\"}")
            return

        template_path = TEMPLATE_DIR / template_name
        if not template_path.exists():
            self._set_headers(404)
            self.wfile.write(b"{\"error\":\"Template not found\"}")
            return

        timestamp = int(time.time())
        sent = []
        failures = []
        for entry in mutuas:
            context = {
                "MUTUA": str(entry.get("mutua", "") or ""),
                "CONTACTO": str(entry.get("contacto", "") or ""),
                "REFERENCIA": str(entry.get("referencia", "") or ""),
                "FECHA": str(entry.get("fecha", "") or ""),
                "IMPORTE": str(entry.get("importe", "") or ""),
                "DESCRIPCION": str(entry.get("descripcion", "") or ""),
            }
            safe_mutua = entry.get("mutua", "destino").replace(" ", "_") or "destino"
            output_name = f"{timestamp}_{safe_mutua}.docx"
            output_path = OUTGOING_DIR / output_name
            try:
                render_docx(template_path, context, output_path)
                subject = f"Solicitud de pago - {entry.get('mutua', 'Mutua')}"
                body = (
                    f"Hola {entry.get('contacto', 'equipo')},\n\n"
                    "Adjuntamos la carta de solicitud de pago de la intervención.\n"
                    "Si necesitan información adicional, quedamos atentos.\n\n"
                    "Saludos."
                )
                recipient = entry.get("email", "") or "destino@ejemplo.com"
                if smtp_configured() and not entry.get("email"):
                    raise ValueError("Falta el correo electrónico de la mutua")

                result = send_email(recipient, subject, body, output_path)
                result["file"] = output_name
                sent.append(result)
            except Exception as exc:  # pylint: disable=broad-except
                failures.append({"mutua": entry.get("mutua"), "error": str(exc)})

        status_code = 200 if not failures else 207
        self._set_headers(status_code)
        response = {
            "template": template_name,
            "sent": sent,
            "failed": failures,
            "mode": "smtp" if smtp_configured() else "dry-run",
            "outputDirectory": str(OUTGOING_DIR.relative_to(BASE_DIR)),
        }
        self.wfile.write(json.dumps(response).encode())


def run(server_class=ThreadingHTTPServer, handler_class=TemplateServer, port: int = 8000):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"Servidor escuchando en http://localhost:{port}")
    print("API disponible en /api/templates y /api/send")
    httpd.serve_forever()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    run(port=port)
