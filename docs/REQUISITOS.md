# Requisitos y trazabilidad — Attendance Viz

## Contexto y alcance

Cliente académico: profesor de Visual Modelling for Information, UPY. Usuarios: profesor durante/después de la clase; coordinador al cierre. La asignación vale 40% de UA1 y exige como mínimo dos modelos de ML, visualizaciones y buenas prácticas de ingeniería. Fuente: instrucciones compartidas por el usuario el 16-09-2026 y prompt maestro adjunto (17 páginas).

Esta versión es un sistema local de una instancia, un proceso y una cámara. La medición es presencia OBSERVADA. No se infiere atención, emoción, aprendizaje ni rendimiento cognitivo.

## Matriz de requisitos

| ID | Requisito / decisión | Implementación | Evidencia |
|---|---|---|---|
| RF01 | Seleccionar cámara integrada/USB | Índice 0–10, explorar 0–3, iniciar/detener | During class; prueba física AC01 |
| RF02 | Detectar personas y conservar tracks | YOLO11n + ByteTrack | services/vision.py; smoke e integración simulada |
| RF03 | Detectar/reconocer rostro registrado | YuNet + SFace, similitud y margen, tres confirmaciones | services/vision.py y engine.py |
| RF04 | Desconocido con referencias locales | Identity pendiente + ReferenceImage | Pending identities; AC03 |
| RF05 | Asignar nombre o unir a alumno existente | Formulario, transacción y bitácora | Pruebas de identificación/fusión |
| RF06 | Sesiones con pausa y cierre | Máquina new/live/paused/finished/interrupted | Pruebas de transiciones y recuperación |
| RF07 | Tiempo real para profesor | Video, cajas, estados, roster provisional, FPS/error | During class |
| RF08 | Análisis después de clase | Timeline, porcentaje, tiempo y mayor intervalo continuo | After class / Session detail |
| RF09 | Cierre de curso para coordinador | Tendencia, mapa alumno-sesión, dispersión y riesgo | Course insights |
| RF10 | Mínimo dos modelos ML | Tres redes preentrenadas distintas | Documentación de modelos + smoke |
| RF11 | Reglas configurables | Present/Partial por sesión; mínimo histórico global | Settings y pruebas de umbrales |
| RF12 | Historial por alumno | Sesiones, resultados, referencias y permanencia | Student detail |
| RF13 | Rankings separados | Asistencia y permanencia | Leaderboard |
| RF14 | No confundir desconocido/intruso | Estado pendiente inicial; clasificación manual | Unknown People |
| RF15 | Reportes | Resumen curso, fechas, alumno, CSV/PDF | Reports y prueba HTTP |
| RF16 | Fallos sin falsear ausencias | Pausa/revisión, checkpoints y recuperación | Tests de desconexión y recovery |
| RNF01 | Ejecución local | SQLite, recursos estáticos propios, pesos locales | README |
| RNF02 | Acceso controlado | Login, CSRF, mutaciones solo staff, medios protegidos | Tests de permisos |
| RNF03 | Visualización interpretable | Leyendas, tooltips, texto además de color, filtros | SVG/HTML + revisión de interfaz |
| RNF04 | Mantenibilidad | Servicios separados, migración, tests, documentación | Árbol del proyecto |

## Decisiones provisionales que requieren conversación con el cliente

No bloquean la construcción; Settings y la documentación hacen visibles los supuestos.

1. ¿El 70% observado basta para Presente y el 80% histórico es el mínimo institucional? Se usan como ejemplos configurables, NO como política UPY confirmada.
2. ¿Las faltas justificadas y llegadas tardías deben tener estados propios? Por ahora solo Presente/Parcial/Ausente/Revisión.
3. ¿Un parcial debe contar fraccionalmente para asistencia histórica? Por ahora no suma una sesión presente.
4. ¿Se aceptan intervalos breves sin detección como continuidad? Actualmente se interpolan huecos entre observaciones de la MISMA identidad de hasta 2 s, configurable entre 0.5–5 s; no se prolonga presencia indefinidamente tras perderla.
5. ¿Quién puede consultar fotos y rankings? En esta instancia local: usuarios autenticados, con profesores staff y coordinadores de lectura.
6. ¿Qué periodo de conservación y procedimiento de eliminación requiere el curso? No se impone un plazo automático inventado.
7. ¿Se permite usar modelos preentrenados para el requisito de dos ML? Se emplean tres; no se entrenó un modelo propio.

## Pendientes respecto al prompt aspiracional

- Reidentificación corporal avanzada y seguimiento fiable en oclusiones prolongadas.
- Editor manual de intervalos y estados de falta justificada, con auditoría detallada.
- Carga/reentrenamiento de referencias desde archivo y eliminación selectiva desde UI. En esta versión las referencias nuevas se capturan automáticamente; no se reentrena SFace.
- Fusionar dos identidades pendientes entre sí directamente: actualmente se vinculan al mismo estudiante para consolidarlas.
- Reportes PDF detallados por sesión y de alumnos en riesgo: el PDF actual es resumen de curso/alumno por fechas.
- Listado de todas las sesiones por identidad desconocida y última aparición en su tarjeta: se muestra número de sesiones y fecha de creación.
- Despliegue multiusuario de producción, varias cámaras e aislamiento por profesor.

No se presentan estas funciones pendientes como implementadas. La prioridad de esta entrega es completar el flujo local y las tres etapas de visualización con evidencia verificable.
