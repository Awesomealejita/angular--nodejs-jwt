# Automatización de plantillas Word para mutuas

Aplicación web sencilla (Python estándar + HTML) para subir plantillas Word (`.docx`), rellenarlas con los datos de cada mutua y enviarlas por correo de forma masiva.

## Requisitos
- Python 3.10 o superior (no requiere dependencias externas ni acceso a Internet para instalar paquetes).
- Credenciales SMTP (opcional). Si no se configuran, los documentos se generarán en modo "dry-run" en `storage/outgoing`.

## Puesta en marcha
```bash
python app.py
```
La aplicación queda disponible en `http://localhost:8000`.

Variables de entorno soportadas:
- `SMTP_HOST`, `SMTP_PORT` (por defecto `587`)
- `SMTP_USER`, `SMTP_PASS`
- `SMTP_FROM` (si no se define, se usa el usuario SMTP)

## Uso
1. Sube una plantilla `.docx` con los marcadores `{{MUTUA}}`, `{{CONTACTO}}`, `{{REFERENCIA}}`, `{{FECHA}}`, `{{IMPORTE}}` y `{{DESCRIPCION}}`.
2. Añade las mutuas con sus datos y pulsa **Generar y enviar**.
3. Los documentos personalizados se guardan en `storage/outgoing`. Si SMTP está configurado, también se envían por correo.

## Notas técnicas
- El servidor se basa en `http.server` y `smtplib` del estándar de Python.
- La personalización de la plantilla se realiza reemplazando los marcadores en `word/document.xml` dentro del `.docx`.
- Endpoints disponibles: `GET /api/templates`, `POST /api/templates` (subida multipart) y `POST /api/send` (JSON con `template` y lista `mutuas`).
