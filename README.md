# angular--nodejs-jwt

Este repositorio contiene la documentación funcional para una app Canvas de Power Apps integrada con Power Automate que automatiza la solicitud de pagos a mutuas por servicios de anestesia. Consulta [docs/powerapps-solicitud-pago.md](docs/powerapps-solicitud-pago.md) para el prompt completo en español que detalla listas de SharePoint, pantallas, flujo y plantilla HTML base.

Para ver la solución en funcionamiento en tu entorno de Power Platform, sigue los pasos guiados de [docs/powerapps-demo.md](docs/powerapps-demo.md), donde se describe cómo crear las listas de SharePoint, generar el flujo de Power Automate, probar el envío de PDF y validar el historial de solicitudes.

Para enseñar rápidamente el front en el navegador, abre el archivo estático [docs/preview.html](docs/preview.html).

Opciones de arranque local:
- Con Node.js: `npm run preview` (sirve la vista en `http://localhost:8000/preview.html`).
- Con Python: `python -m http.server` desde la raíz y visitar `http://localhost:8000/docs/preview.html`.
