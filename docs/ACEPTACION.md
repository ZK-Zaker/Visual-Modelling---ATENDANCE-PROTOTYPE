# Casos de uso y aceptación con cliente

## UC01 — Conducir una sesión

Actor: profesor autenticado staff. Precondiciones: modelos disponibles, curso creado, cámara local autorizada. Flujo: seleccionar cámara → vista previa → crear sesión → iniciar → observar roster → pausar/reanudar si hace falta → finalizar → consultar resumen. Postcondición: una asistencia por participante y timeline reconstruible. Alternativa: sin cámara, se muestra error y no se inicia la sesión. Excepción: desconexión pausa y exige revisión.

## UC02 — Identificar alumno nuevo

Actor: profesor. Precondición: identidad pendiente con referencias útiles. Flujo: abrir Pending identities → inspeccionar referencias → indicar nombre/matrícula o alumno existente → guardar. Postcondición: identidad, referencias e intervalos se conservan; se actualizan registros de sesiones donde fue observado. Alternativa: visitante/ignorado/posible intruso se marca manualmente. Excepción: matrícula duplicada revierte la transacción.

## UC03 — Evaluar el curso

Actor: coordinador autenticado sin staff. Flujo: seleccionar curso/fechas → leer tendencia → explorar atlas → revisar alumnos bajo mínimo → comparar asistencia/permanencia → exportar. Postcondición: información accesible sin modificar registros. Alternativa: sesiones sin cobertura aparecen en revisión y se excluyen de tasas.

## Matriz de pruebas reales (aún por ejecutar)

| ID | Procedimiento | Criterio esperado | Estado |
|---|---|---|---|
| AC01 | Probar cámara integrada y USB | Video, fuente correcta, FPS y parada sin bloqueo | Pendiente equipo real |
| AC02 | Iniciar sin cámara/permisos | Error legible; no sesión falsa | Pendiente equipo real |
| AC03 | Persona nueva frente a cámara | Pending + referencias no idénticas, sin estudiante definitivo | Pendiente voluntario |
| AC04 | Asignar nombre y volver a entrar | Nombre correcto tras confirmaciones, sin duplicar tiempo | Pendiente voluntario |
| AC05 | Girar rostro durante 5 s sin salir | Seguimiento conserva identidad si el cuerpo sigue observable | Pendiente salón |
| AC06 | Dos personas se cruzan | Medir intercambios de identidad; no asumir cero errores | Pendiente salón |
| AC07 | Salir 20 s y regresar | No sumar automáticamente los 20 s perdidos | Pendiente salón |
| AC08 | Desconectar cámara durante sesión | Pausa/revisión; no inventar ausencia definitiva | Pendiente equipo real |
| AC09 | Pausar 30 s | Denominador excluye esos 30 s | Pendiente comparación cronómetro |
| AC10 | Cerrar proceso inesperadamente | runlocal recupera hasta heartbeat y marca interrumpida | Pendiente equipo real |
| AC11 | Aula con alumnos sentados al fondo | Registrar detecciones perdidas, FPS y límites de encuadre | Pendiente salón |

No marcar estas filas como aprobadas hasta ejecutar y registrar evidencia. Usar voluntarios informados registrados específicamente para la clase; evitar incluir personas ajenas en las pruebas.

## Medición mínima

Para 3–5 voluntarios y dos sesiones cortas, anotar manualmente entradas/salidas y comparar contra los intervalos. Medir error absoluto de tiempo, identificaciones incorrectas, desconocidos duplicados, pérdidas del track y FPS aproximados. Reportar cámara, resolución, iluminación, distancia y equipo. No confundir un smoke test con exactitud biométrica.

## Guion de demostración (6–8 minutos)

1. Problema: asistencia como continuidad, no solo Boolean (30 s).
2. Mostrar tres modelos y responsabilidades; aclarar preentrenamiento (45 s).
3. During class: seleccionar cámara, iniciar sesión y detectar (90 s).
4. Pending identities: registrar nuevo alumno y volver a mostrar nombre (60 s).
5. After class: terminar y explicar ribbon, pausa y porcentaje (90 s).
6. Course insights: seleccionar curso sintético marcado, explorar atlas y dispersión (60 s).
7. Pruebas, documentación y límites medidos / pendientes (45 s).

Si la cámara falla, mostrar el estado real del fallo y usar el curso sintético SOLO para demostrar visualización. No presentarlo como resultado experimental.
