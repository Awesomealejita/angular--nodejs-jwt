# App "Solicitud de Pago a Mutuas – Anestesistas"

Esta guía describe cómo construir una app Canvas de Power Apps integrada con Power Automate para que el personal administrativo genere y envíe solicitudes de pago en PDF a mutuas y centros médicos.

## Objetivos
- Automatizar la generación y el envío de solicitudes de pago con formato homogéneo.
- Reducir tiempos administrativos y errores manuales.
- Centralizar historiales, plantillas, mutuas y datos de anestesistas en SharePoint.

## Origen de datos en SharePoint
Crea las siguientes listas y bibliotecas:

- **Mutuas** (lista)
  - Nombre (Título)
  - EmailRecepcion (Correo)
  - PersonaContacto (Texto)
  - Telefono (Texto)
  - Direccion (Texto)

- **PlantillasMutuas** (lista)
  - Nombre (Título)
  - MutuaId (Búsqueda a Mutuas, opcional para plantilla específica)
  - EncabezadoHtml (Texto enriquecido o texto largo)
  - SaludoHtml (Texto largo)
  - CuerpoHtml (Texto largo)
  - PieHtml (Texto largo)
  - MarcadoresDisponibles (Texto de referencia)

- **DatosAnestesistas** (lista)
  - Nombre (Título)
  - NIF (Texto)
  - Colegiado (Texto)
  - Email (Correo)
  - Teléfono (Texto)

- **HistorialSolicitudes** (lista)
  - Título (concatenar Paciente + Fecha)
  - MutuaId (Búsqueda a Mutuas)
  - Paciente (Texto)
  - FechaIntervencion (Fecha)
  - Especialidad (Texto)
  - Importe (Moneda)
  - EstadoEnvio (Opción: Enviado, Pendiente, Error)
  - AnestesistaId (Búsqueda a DatosAnestesistas)
  - PdfUrl (Hipervínculo)
  - Observaciones (Texto)

- **SolicitudesPago** (biblioteca de documentos)
  - Usada para almacenar los PDF generados.

## Estructura de pantallas (Power Apps)
1. **PantallaPrincipal**: menú con botones a:
   - Nueva solicitud de pago
   - Historial de solicitudes enviadas
   - Plantillas configurables
   - Datos de anestesistas

2. **NuevaSolicitudScreen**:
   - Formulario edit form conectado a una colección temporal.
   - Campos: Mutua (dropdown conectado a *Mutuas*), Paciente, Fecha de intervención, Especialidad, Anestesista (dropdown *DatosAnestesistas*), Importe, Texto adicional, Adjuntos (control Attachments).
   - Botones: Guardar y enviar, Guardar borrador, Duplicar (rellena el formulario con último registro enviado).
   - Validaciones: campos obligatorios (Mutua, Paciente, Fecha, Importe, Anestesista), formato de importe (>0), máximo de adjuntos, límite de peso.
   - Acción principal: `OnSelect` llama a `PowerAutomate.Run(payloadJSON)` pasando todos los datos y los adjuntos codificados en base64.

3. **HistorialScreen**:
   - Galería conectada a *HistorialSolicitudes*.
   - Columnas: FechaIntervencion, Mutua.Nombre, Paciente, Importe, EstadoEnvio.
   - Botón/ícono para descargar PDF usando `Launch(ThisItem.PdfUrl)`.
   - Filtros por fecha, mutua y estado.

4. **PlantillasScreen**:
   - Galería de plantillas (lista *PlantillasMutuas*).
   - Formulario de edición con campos HTML (puede usarse control de texto enriquecido) para Encabezado, Saludo, Cuerpo y Pie.
   - Vista previa renderizada usando control HTML y datos de ejemplo.
   - Botón "Guardar" para enviar cambios a SharePoint.

5. **AnestesistasScreen**:
   - Formulario de mantenimiento de *DatosAnestesistas* (crear/editar/eliminar).

## Marcadores dinámicos sugeridos
Usa estos tokens en la plantilla HTML y reemplázalos en el flujo:
- `{{NombreMutua}}`, `{{EmailMutua}}`, `{{DireccionMutua}}`
- `{{Paciente}}`, `{{Fecha}}`, `{{Especialidad}}`
- `{{Importe}}`, `{{TextoAdicional}}`
- `{{NombreAnestesista}}`, `{{NIFAnestesista}}`, `{{Colegiado}}`

## Flujo principal en Power Automate
1. **Disparador**: Power Apps (V2).
2. **Inicializar variables**: payload de Power Apps (JSON) y diccionario de marcadores.
3. **Obtener plantilla HTML**: de *PlantillasMutuas*; si la mutua tiene plantilla específica úsala, si no, usa la genérica.
4. **Reemplazar marcadores**: con acciones de tipo `Compose` o `replace()`; construir HTML final concatenando encabezado + saludo + cuerpo + pie.
5. **Adjuntar documentación**: convertir adjuntos recibidos en base64 a contenido de archivo.
6. **Generar PDF**: con acción “Convertir archivo (OneDrive/SharePoint)” o con `Encabezado/HTML to PDF` si se dispone de conector premium.
7. **Guardar en SharePoint**: crear archivo en biblioteca *SolicitudesPago* con nombre `Solicitud_[Paciente]_[Fecha].pdf` y obtener URL pública/compartida si procede.
8. **Enviar correo**: `Send email (V2)` a EmailRecepcion de la mutua con asunto: `Solicitud de pago intervención anestésica – [Paciente] – [Fecha]`; adjuntar PDF.
9. **Registrar historial**: crear item en *HistorialSolicitudes* con estado Enviado o Error y la URL del PDF.
10. **Responder a Power Apps**: devolver estado y vínculo para mostrar notificación y refrescar el historial.

## Lógica de duplicado de solicitudes
- Guarda en una colección `colUltimaSolicitud` el último payload enviado.
- El botón Duplicar usa `Set(varSolicitud, Last(colUltimaSolicitud)); ResetForm(EditFormSolicitud); Patch(...)` para precargar datos.

## Seguridad y control
- Usa roles de SharePoint o grupos de seguridad para restringir edición de plantillas y datos maestros.
- En Power Apps, controla visibilidad de botones mediante `User().Email` o lista de roles.
- Registra errores en *HistorialSolicitudes* con detalle del mensaje devuelto por el flujo.

## Diseño
- Tema claro con colores pastel y tipografía profesional (Segoe UI / Open Sans).
- Layout responsive: usa contenedores flexibles y propiedades `X`, `Y`, `Width`, `Height` basadas en `Parent` y `App.Width`.
- Añade encabezados cortos por pantalla y mensajes de validación inmediatos (`If(IsBlank(DataCardValueMutua.Selected.Value), Notify(...))`).

## Plantilla HTML base (ejemplo)
```html
<div style="font-family: 'Segoe UI', Arial; color:#1a1a1a; font-size:12pt;">
  <div style="border-bottom:2px solid #0078D4; padding-bottom:12px; margin-bottom:16px;">
    <h2>Solicitud de pago por servicios de anestesia</h2>
    <p>{{Fecha}}</p>
  </div>
  <p>{{Saludo}}</p>
  <p>Por medio de la presente, solicitamos el abono de los honorarios correspondientes a la intervención realizada a <strong>{{Paciente}}</strong> el día <strong>{{Fecha}}</strong> en la especialidad de <strong>{{Especialidad}}</strong>.</p>
  <p>Importe a reclamar: <strong>{{Importe}}</strong></p>
  <p>{{TextoAdicional}}</p>
  <p>Datos del profesional: {{NombreAnestesista}} – NIF: {{NIFAnestesista}} – Colegiado: {{Colegiado}}</p>
  <p>Datos de contacto de la mutua: {{NombreMutua}} – {{EmailMutua}} – {{DireccionMutua}}</p>
  <div style="margin-top:24px; border-top:1px solid #d9d9d9; padding-top:12px;">
    <p>Atentamente,</p>
    <p>{{NombreAnestesista}}</p>
  </div>
</div>
```

## Buenas prácticas de implementación
- Normaliza fechas al formato `dd/MM/yyyy` antes del reemplazo de marcadores.
- Usa `Text(Importe, "#,##0.00€")` en Power Apps para pasar el valor ya formateado al flujo.
- Maneja varias copias de email separadas por `;` para CC/CCO si es necesario.
- Incluye un control de progreso/spinner durante la ejecución del flujo y notificaciones de éxito o error.
- Programar pruebas con datos ficticios en un entorno sandbox antes de producción.

## Extensiones opcionales
- Añadir firma digital o sello corporativo en el PDF.
- Exponer botón "Reenviar" desde el historial para repetir el flujo con el mismo PDF o con una nueva generación.
- Crear un cuadro de mando en Power BI conectado a *HistorialSolicitudes* para seguimiento de estados e importes.
