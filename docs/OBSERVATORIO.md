# Observatorio y Most Wanted

During class incluye un pulso con personas visibles, alumnos identificados, identidades pendientes y pico de personas visibles. El eje vertical muestra personas; el horizontal, hora local del navegador. El motor toma una muestra cada dos segundos como máximo y conserva hasta 601 muestras en memoria. La ventana visible es de veinte minutos. Una pausa, cambio de sesión o interrupción rompe la línea; reiniciar el servidor borra este historial temporal.

La vista previa no ejecuta detección: hay que iniciar una sesión. El panel muestra guiones cuando no está capturando. La bitácora usa eventos persistidos; «fuera de vista» significa pérdida de seguimiento, no salida física del salón. No se estima cobertura del salón, atención ni probabilidad de identidad.

La calidad de captura muestra cuántas personas tienen un rostro útil en la última extracción facial (cada 0.7 segundos aproximadamente). Reutiliza los criterios existentes de tamaño, rostro único y nitidez. Una captura limitada no identifica su causa exacta; puede deberse a distancia, ángulo, oclusión o desenfoque.

Most Wanted ordena identidades pendientes y marcadas manualmente como posible intruso por sesiones distintas y luego tiempo observado. Une intervalos superpuestos dentro de cada sesión para no duplicar minutos. La foto principal es la primera referencia disponible; todas se pueden consultar en el expediente. No se inventan puntuaciones de similitud histórica.

Los visitantes, ignorados y alumnos con referencia aparecen en el archivo clasificado. Al vincular con un alumno se conserva la lógica existente de unión de referencias y reconstrucción de asistencia. Las acciones siguen reservadas al profesor; el coordinador puede consultar.

Una identidad tiene un nombre o alias independiente de su clasificación. «Guardar nombre y clasificación» permite nombrar visitantes o posibles intrusos sin crear estudiantes, inscripciones ni registros de asistencia. «Registrar o vincular como alumno» es una acción explícita y conserva la reconstrucción histórica. Los nombres se muestran en Most Wanted, seguimiento y bitácora. El archivo clasificado también permite editar nombres de visitantes.

Los avisos individuales siguen solo a alumnos identificados al menos una vez durante el tramo de captura actual. Los valores predeterminados en Settings son 30 s («Fuera del radar»), 120 s («¿Pausa técnica?») y 300 s («¿Se nos escapó?»). Siempre se muestra el tiempo fuera de vista; no se afirma que alguien fue al baño o abandonó la clase. El regreso aparece durante 30 s. Estos avisos no afectan el cálculo de asistencia.

Al pausar, terminar, cambiar de sesión, reclasificar identidades o fallar la cámara, los avisos se reinician; es necesario volver a observar al alumno para iniciar otro aviso. Un intervalo mayor a 5 s entre cuadros también reinicia el monitor. Si se pierden al menos tres identidades en 5 s y representan al menos la mitad del grupo recién observado, se muestra una advertencia colectiva y se suprimen los avisos de esas personas hasta volver a detectarlas. Es una heurística, no una medición de cobertura física.

Todos los estilos y gráficos son locales, sin fuentes externas ni dependencias de visualización nuevas. Esta versión requiere `python manage.py migrate` para alias y umbrales (migración 0002). Reinicia `manage.py runlocal` y recarga el navegador con Ctrl+F5 para ver los cambios.
