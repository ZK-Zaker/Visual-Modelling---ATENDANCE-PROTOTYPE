# Observatorio y Most Wanted

During class incluye un pulso con personas visibles, alumnos identificados, identidades pendientes y pico de personas visibles. El eje vertical muestra personas; el horizontal, hora local del navegador. El motor toma una muestra cada dos segundos como máximo y conserva hasta 601 muestras en memoria. La ventana visible es de veinte minutos. Una pausa, cambio de sesión o interrupción rompe la línea; reiniciar el servidor borra este historial temporal.

La vista previa no ejecuta detección: hay que iniciar una sesión. El panel muestra guiones cuando no está capturando. La bitácora usa eventos persistidos; «fuera de vista» significa pérdida de seguimiento, no salida física del salón. No se estima cobertura del salón, atención ni probabilidad de identidad.

La calidad de captura muestra cuántas personas tienen un rostro útil en la última extracción facial (cada 0.7 segundos aproximadamente). Reutiliza los criterios existentes de tamaño, rostro único y nitidez. Una captura limitada no identifica su causa exacta; puede deberse a distancia, ángulo, oclusión o desenfoque.

Most Wanted ordena identidades pendientes y marcadas manualmente como posible intruso por sesiones distintas y luego tiempo observado. Une intervalos superpuestos dentro de cada sesión para no duplicar minutos. La foto principal es la primera referencia disponible; todas se pueden consultar en el expediente. No se inventan puntuaciones de similitud histórica.

Los visitantes, ignorados y alumnos con referencia aparecen en el archivo clasificado. Al vincular con un alumno se conserva la lógica existente de unión de referencias y reconstrucción de asistencia. Las acciones siguen reservadas al profesor; el coordinador puede consultar.

Todos los estilos y gráficos son locales, sin fuentes externas ni dependencias de visualización nuevas. No requiere migraciones. Reinicia `manage.py runlocal` y recarga el navegador con Ctrl+F5 para ver los cambios.
