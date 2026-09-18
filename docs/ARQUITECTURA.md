# Arquitectura y decisiones

## Componentes

Django sirve templates, JSON, acciones POST, medios protegidos y MJPEG. Un singleton Engine posee la cámara en un hilo. Las solicitudes comparten el productor de frames. SQLite conserva entidades, segmentos, presencia y eventos; no se guarda video completo. El arranque `runlocal` usa un proceso, sin autoreload, y recupera sesiones activas interrumpidas.

La primera propuesta mencionaba ECharts. La implementación usa SVG y HTML propios para eliminar CDN y permitir una entrega completamente local; soporta tooltips, filtros, navegación por celda y diseño responsive.

## Modelo de datos

- Course tiene inscripciones Enrollment y sesiones ClassSession.
- Identity es el identificador persistente. Student lo extiende con nombre, matrícula y activo.
- ReferenceImage pertenece a Identity y conserva vector SFace + versión.
- Participant congela la lista esperada de una sesión; una identificación posterior agrega al alumno solo en sesiones donde su identidad ya tuvo presencia.
- Segment conserva los periodos activos, excluyendo pausas.
- Presence almacena intervalos observados por identidad y sesión.
- Attendance resume Student × ClassSession y tiene restricción única.
- Event registra apariciones/pérdidas/cambios de sesión. Audit registra acciones humanas.
- SystemSettings contiene configuración global. ClassSession copia sus umbrales Present/Partial al empezar.

No se borra ni recrea una identidad al asignarle nombre. Al vincular un pendiente con un alumno existente, las referencias y los intervalos se reasocian; la unión matemática impide sumar dos veces una presencia simultánea.

## Pipeline real

1. OpenCV VideoCapture lee una cámara local.
2. YOLO11n detecta la clase person; ByteTrack entrega identificadores temporales.
3. Cada ~0.7 s por track se intenta YuNet sobre la caja corporal.
4. Se exige un rostro único, tamaño mínimo y nitidez Laplaciana.
5. SFace alinea el rostro y obtiene un vector de 128 dimensiones normalizado.
6. Se calcula similitud coseno con referencias locales elegibles para el curso y pendientes.
7. Se exige umbral configurable, margen mínimo 0.06 frente a otra identidad y tres confirmaciones.
8. Si no hay coincidencia en tres observaciones útiles, se crea un pendiente y su primera referencia.
9. Se agregan referencias hasta el límite; al menos 1.5 s entre capturas y se evita similitud ≥0.995 con las anteriores.
10. La continuidad corporal mantiene la identidad; una coincidencia facial contradictoria la invalida. Un track perdido más del timeout requiere confirmar otra vez.
11. Se agrupan actualizaciones de presencia y heartbeat cada aproximadamente dos segundos. Se guardan eventos significativos, no cada frame.

Una referencia facial no garantiza identidad real sin validación humana. La similitud no se interpreta como porcentaje de certeza. Las identidades desconocidas de distintos días pueden duplicarse si las imágenes son malas.

## Estados de sesión

`new → live → paused → live → finished`

Desde `live` o `paused`, End finaliza. Una desconexión pasa de live a paused y activa review. Un reinicio transforma las sesiones que quedaron live/paused en interrupted, cerrando en el último heartbeat. Iniciar y reanudar requiere video conectado y cámara coincidente. Solo se admite una sesión live/paused en la instancia.

## Concurrencia y límites

Engine usa RLock para que cambios de sesión/identidad no intercalen cambios con el procesamiento. Esto favorece coherencia para una cámara pero puede aumentar latencia HTTP durante una inferencia lenta. No se prometen FPS. La siguiente evolución sería un proceso worker y mensajes, si las mediciones locales lo justifican.

SQLite usa transacciones breves y timeout; sigue siendo una solución local, no una arquitectura de captura distribuida. Las duraciones persistentes usan timestamps UTC; la UI presenta America/Merida. El reloj del sistema debe ser correcto.

## Autenticación y datos

Los endpoints requieren login; las mutaciones exigen staff y CSRF. Las imágenes se sirven mediante vista autenticada, sin exponer MEDIA_ROOT públicamente. El servidor escucha solo 127.0.0.1. No hay búsqueda facial externa. Los modelos se descargan una vez con SHA-256 y luego se cargan desde disco.

Los coordinadores de lectura pueden ver todos los cursos de esta instancia. Esta es una decisión explícita para un equipo pequeño; no existe autorización granular por objeto.
