# Guía rápida para ver la app en funcionamiento

Esta guía indica cómo preparar un entorno mínimo de Power Platform para ejecutar la app Canvas y el flujo de Power Automate descritos en [powerapps-solicitud-pago.md](powerapps-solicitud-pago.md).

## Requisitos previos
- Acceso a Power Apps y Power Automate.
- SharePoint Online con permisos para crear listas y bibliotecas.
- Cuenta de correo habilitada para enviar desde Power Automate.

## 1) Crear las listas y biblioteca en SharePoint
1. En SharePoint crea un sitio de prueba (por ejemplo, **PagosAnestesia**).
2. Crea las listas con las columnas indicadas en la guía principal:
   - **Mutuas**
   - **PlantillasMutuas**
   - **DatosAnestesistas**
   - **HistorialSolicitudes**
3. Crea la biblioteca de documentos **SolicitudesPago** para guardar los PDF.
4. Añade al menos un registro de ejemplo en **Mutuas** y **DatosAnestesistas** (nombre, email, NIF, colegiado) y una plantilla HTML sencilla en **PlantillasMutuas** con el contenido del bloque "Plantilla HTML base" de la guía principal para que la prueba pueda ejecutarse sin rediseñar nada.

> Tip: puedes cargar un archivo PDF de muestra en tu PC para probar el adjunto; se enviará en el correo junto al PDF generado.

## 2) Construir rápidamente la app Canvas
1. En Power Apps, crea una **Canvas app** en formato tablet y conéctala a las listas anteriores.
2. Replica las pantallas mínimas:
   - **PantallaPrincipal**: botones para ir a Nueva Solicitud, Historial, Plantillas y Anestesistas.
   - **NuevaSolicitudScreen**: formulario con campos Mutua, Paciente, Fecha, Especialidad, Anestesista, Importe, Texto adicional y Adjuntos.
   - **HistorialScreen**: galería vinculada a *HistorialSolicitudes* con descarga de PDF mediante `Launch(ThisItem.PdfUrl)`.
3. En el botón **Guardar y enviar**, llama al flujo de Power Automate (creado en el paso 3) usando `PowerAutomate.Run(JSON(payload))` pasando todos los campos del formulario y los adjuntos en base64.

### Fórmula sugerida para el botón "Guardar y enviar"
```powerfx
// Convierte adjuntos a una colección con base64
ClearCollect(colAdjuntos,
    ForAll(Upload.Attachments,
        {
            Nombre: DisplayName,
            Contenido: JSON(Value, JSONFormat.IncludeBinaryData)
        }
    )
);

// Crea el payload
Set(varPayload,
    {
        MutuaId: DropdownMutua.Selected.ID,
        MutuaNombre: DropdownMutua.Selected.Title,
        MutuaEmail: DropdownMutua.Selected.EmailRecepcion,
        Paciente: DataCardValuePaciente.Text,
        Fecha: DataCardValueFecha.SelectedDate,
        Especialidad: DataCardValueEspecialidad.Text,
        Importe: Value(DataCardValueImporte.Text),
        TextoAdicional: DataCardValueTexto.Text,
        AnestesistaId: DropdownAnestesista.Selected.ID,
        AnestesistaNombre: DropdownAnestesista.Selected.Title,
        AnestesistaNif: DropdownAnestesista.Selected.NIF,
        AnestesistaColegiado: DropdownAnestesista.Selected.Colegiado,
        Adjuntos: colAdjuntos
    }
);

// Llamada al flujo
Set(varRespuesta, PowerAutomate.Run(JSON(varPayload)));

If(varRespuesta.status = "Enviado",
    Notify("Solicitud enviada", NotificationType.Success);
    Refresh('HistorialSolicitudes'),
    Notify(Coalesce(varRespuesta.error,"Error al enviar"), NotificationType.Error)
);
```

## 3) Crear el flujo de Power Automate
1. Desde Power Automate, crea un flujo **automatizado desde cero** con disparador **Power Apps (V2)**.
2. Añade pasos para:
   - **Parsear el payload**: acción **Compose** con `@json(triggerOutputs()?['body'])` para acceder a cada campo y adjunto.
   - **Obtener plantilla HTML** desde *PlantillasMutuas* (usando el ID enviado o una plantilla genérica).
   - **Reemplazar marcadores** `{{campo}}` con expresiones `replace()` encadenadas; ejemplo:
     ```
     @{replace(replace(outputs('Plantilla_HTML'), '{{Paciente}}', outputs('Compose')['Paciente']), '{{Importe}}', outputs('Compose')['Importe'])}
     ```
   - **Construir PDF**: crea archivo temporal en OneDrive/SharePoint con el HTML y conviértelo con **Convertir archivo (PDF)**.
   - **Guardar en biblioteca** *SolicitudesPago* con nombre `Solicitud_@{outputs('Compose')['Paciente']}_@{formatDateTime(outputs('Compose')['Fecha'],'yyyyMMdd')}.pdf` y guarda la URL.
   - **Enviar correo** a la mutua (`Send email (V2)`) con asunto `Solicitud de pago – @{outputs('Compose')['Paciente']} – @{formatDateTime(outputs('Compose')['Fecha'],'dd/MM/yyyy')}` adjuntando el PDF.
   - **Registrar historial** en *HistorialSolicitudes* (estado Enviado o Error) y **Responder a Power Apps** con `status` y `pdfUrl`.
3. Guarda el flujo y conéctalo a la app en el botón **Guardar y enviar**.

## 4) Prueba de extremo a extremo
1. En la app, abre **Nueva solicitud de pago** y rellena los campos obligatorios.
2. Adjunta un archivo de prueba (por ejemplo, un PDF pequeño).
3. Pulsa **Guardar y enviar**. La app debería mostrar una notificación de éxito o error.
4. Ve a **Historial** y confirma que aparece el registro con estado **Enviado** y un enlace al PDF.
5. Abre el enlace para validar que el PDF se guardó correctamente y revisa el correo enviado a la mutua de prueba.

## 5) Depuración rápida
- Si el PDF no se genera, revisa el paso de conversión en el flujo y comprueba que el HTML no contenga marcadores sin reemplazar.
- Si no se envía el correo, verifica que el campo **EmailRecepcion** de la mutua está poblado y que la acción de correo no está bloqueada por DLP.
- Si la app no recibe respuesta, agrega un paso **Responder a Power Apps** al final del flujo con `status` y `pdfUrl` para mostrar mensajes claros.

## 6) Escenario de prueba listo para usar (10 minutos)
1. Crea las listas/biblioteca y pega la **plantilla HTML base** en un ítem de *PlantillasMutuas* llamado "Genérica".
2. Inserta datos de ejemplo:
   - Mutua: Nombre "Mutua Demo", EmailRecepcion `mutua.demo@contoso.com`.
   - Anestesista: Nombre "Dra. Ana Pérez", NIF `12345678A`, Colegiado `COL-9999`.
3. Publica la app con la pantalla de **Nueva solicitud** usando la fórmula de arriba y ejecuta el flujo asociado.
4. En la app, selecciona la mutua y anestesista de prueba, escribe Paciente "Juan López", Fecha hoy, Importe `250`, y adjunta un PDF cualquiera.
5. Pulsa **Guardar y enviar** y confirma en el historial que el PDF y el correo se enviaron. Con esto tendrás la solución funcionando end-to-end.

Con estos pasos tendrás la solución mínima funcionando y podrás ajustarla según las necesidades de tu organización.
