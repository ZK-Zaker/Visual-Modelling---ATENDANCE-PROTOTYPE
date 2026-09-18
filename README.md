# Attendance Viz — UA1 / UPY

Aplicación local de Python + Django para asistencia basada en intervalos observados. Proyecto de Visual Modelling for Information. Entrega de la asignación: 17 de septiembre de 2026, 23:30, según las instrucciones proporcionadas.

## Qué incluye esta versión

- Tres momentos de decisión: During class, After class y Course insights.
- Captura de cámara integrada/USB, detección de personas, seguimiento y reconocimiento facial local.
- Tres modelos preentrenados: YOLO11n, YuNet y SFace. ByteTrack es el algoritmo de tracking y no se cuenta como modelo de ML adicional.
- Identidades pendientes, referencias locales, asignación de nombre/matrícula y vinculación con alumno existente.
- Sesiones con pausa, intervalos de presencia, checkpoints y recuperación tras reinicio.
- Dashboard, mapa alumno × sesión, ribbons temporales, dispersión asistencia/permanencia, rankings separados y perfiles.
- CSV/PDF, filtro por curso/fechas/alumno; roles profesor (staff) y coordinador (lectura).
- Migraciones, pruebas y documentación de requisitos, arquitectura, decisiones y aceptación.

No contiene alumnos reales ni cuentas preconfiguradas. Las imágenes faciales y la base de datos se crean localmente. El curso sintético es opcional y está claramente etiquetado.

## Obtener el proyecto

```bash
git clone https://github.com/zakerzel/Visual-Modelling---ATENDANCE-PROTOTYPE.git
cd Visual-Modelling---ATENDANCE-PROTOTYPE
```

Continúa con la instalación para tu sistema. Para contribuir, consulta `CONTRIBUTING.md`.

## Inicio rápido — macOS

Usa Python 3.11 o 3.12. Abre Terminal en la raíz del repositorio, donde está `manage.py`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts/download_models.py
python manage.py migrate
python manage.py bootstrap
python manage.py createsuperuser
python manage.py runlocal
```

Abre http://127.0.0.1:8000 e inicia sesión con tu usuario. La primera instalación necesita internet; las páginas y la inferencia funcionan localmente después de instalar dependencias y modelos.

## Inicio rápido — Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/download_models.py
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py bootstrap
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runlocal
```

Usar la ruta del ejecutable evita cambiar políticas de ejecución de PowerShell.

## Explorar visualizaciones sin cámara

```bash
python manage.py seed_demo
```

Selecciona `DEMO · Attendance Lab · SYNTHETIC` en el menú de curso. Son 12 alumnos ficticios y ocho sesiones ficticias. La página muestra una franja de advertencia. El curso real permanece vacío. No uses este curso para afirmar resultados de reconocimiento.

Para una instalación exclusivamente de revisión de páginas puedes instalar `requirements-core.txt`. Para cámara y pruebas de integración necesitas `requirements.txt` completo.

## Primer recorrido con cámara real

1. Entra en During class. Usa el curso real de VM.
2. Si aún no conoces el índice, pulsa Buscar 0–3. Puedes escribir manualmente un índice de 0 a 10.
3. Pulsa Start camera y espera. La primera carga de modelos puede tardar. El estado debe cambiar a Connected y mostrar video.
4. Crea una sesión indicando ese mismo índice. Pulsa Start session.
5. Una persona debe aparecer dentro de la imagen con rostro suficientemente grande y nítido. Tras varias observaciones se crea Unknown y se guardan referencias.
6. Abre Pending identities. Asigna nombre/matrícula, o vincula con un alumno ya creado. La inscripción se añade y se reconstruye la presencia previa de esa identidad.
7. Regresa a la vista en vivo. Mantén el rostro visible unos segundos para confirmar el reconocimiento. Después prueba girarte sin salir del encuadre.
8. Usa Pause/Resume si hace falta. Pulsa End session para calcular resultados.
9. Revisa After class, abre el timeline y consulta Course insights.
10. Para apagar: primero termina la sesión, luego Stop camera y finalmente Ctrl+C en Terminal.

Para iniciar otro día, activa el entorno y ejecuta `python manage.py runlocal`. No repitas migrate/bootstrap salvo que corresponda una actualización.

## Operación y recuperación

- Un proceso local y una cámara a la vez. No ejecutar varios servidores contra la misma base. Usa `runlocal`, que desactiva autoreload.
- La cámara pertenece a la computadora que ejecuta Django; no a otro dispositivo que abra una URL.
- Si la cámara se desconecta, la sesión pasa a pausa y revisión. Reinicia la cámara y reanuda si procede. Los intervalos sin captura no se inventan.
- Un apagado inesperado conserva checkpoints, con pérdida posible de aproximadamente dos segundos más el tiempo de una inferencia. El siguiente `runlocal` marca la sesión interrumpida.
- El profesor puede aceptar explícitamente la medición capturada de una sesión en revisión, con justificación guardada en bitácora. Esto recalcula sobre la duración capturada; no recupera el periodo desconocido.
- Los usuarios sin `is_staff` tienen acceso de lectura de todos los cursos de esta instancia, pensado para un coordinador de confianza. Esta versión no tiene aislamiento por profesor/curso.
- La desactivación de un alumno conserva el historial. Admin permite administrar cursos e inscripciones. La eliminación física de datos históricos no se ofrece en UI.

## Troubleshooting

| Síntoma | Acción |
|---|---|
| Cámara no abre | Cierra Zoom/Teams/otra app; revisa permisos de cámara para Terminal/Python; prueba otro índice. |
| Faltan modelos | Ejecuta `python scripts/download_models.py`. Comprueba internet y permisos de escritura. |
| Error de importación | Confirma que usas el Python de `.venv` y que instalaste requirements.txt. |
| Solo aparece Track | Acércate, mejora iluminación y muestra el rostro; no se guarda una identidad facial sin una referencia útil. |
| Se duplican desconocidos | Revisa referencias y vincúlalos con el mismo estudiante. No bajes el umbral sin medir falsos positivos. |
| Reconocimiento tarda | Se exigen varias observaciones consistentes. El modelo corre en CPU por portabilidad. |
| Base bloqueada | Cierra otros procesos del proyecto; no ejecutes dos servidores ni tareas de administración intensivas durante captura. |
| Gráficas vacías | Finaliza una sesión con participantes o selecciona explícitamente el curso sintético. |

## Pruebas

```bash
python manage.py check
python manage.py test classroom
```

Ver `docs/VALIDACION.md` para evidencia y límites; `docs/ACEPTACION.md` para la prueba en salón. El archivo `requirements-tested.txt` registra las versiones directas usadas en la validación Linux. Los rangos de requirements.txt permiten resolver ruedas compatibles en Mac y Windows.

## Documentación

- `docs/REQUISITOS.md`: alcance, requisitos trazables y preguntas al cliente.
- `docs/ARQUITECTURA.md`: componentes, modelos, flujo y decisiones.
- `docs/METRICAS.md`: fórmulas, denominadores y políticas de revisión.
- `docs/ACEPTACION.md`: casos de uso, matriz de prueba física y guion de demostración.
- `docs/VALIDACION.md`: qué se probó y qué no.
- `docs/THIRD_PARTY.md`: modelos, fuentes y licencias externas.

Las capacidades avanzadas pendientes se señalan en los documentos. La exactitud biométrica y los FPS de tu salón todavía deben medirse con cámara real.
