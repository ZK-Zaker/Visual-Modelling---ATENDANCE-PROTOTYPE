# Validación de la entrega — 16 septiembre 2026

## Verificado en este entorno

- `python manage.py check`: sin errores.
- Migraciones aplicadas desde una base vacía; bootstrap ejecutado.
- 24 pruebas automáticas aprobadas (sin duplicar casos heredados).
- Unión de intervalos, recorte contra segmentos, pausas, límites 30/70, cero duración y ausencia de doble conteo.
- Recalcular asistencia es idempotente; cambios de Settings no cambian umbrales históricos.
- Recuperación de sesiones en último heartbeat y clasificación Revisión.
- Bloqueo de sesiones concurrentes y guardado de intervalo al pausar.
- Todas las páginas principales y exportaciones CSV/PDF devuelven respuestas correctas con cliente Django.
- Login, permisos de lectura/staff y protección CSRF verificados.
- Identificación nueva preserva historial; fusionar no duplica tiempo; matrícula duplicada revierte transacción.
- Filtros de fechas inválidos rechazados; exportación CSV escapa fórmulas al inicio de celdas.
- Curso demo aislado e idempotente.
- Motor completo con cámara/modelos simulados: identidad existente, presencia persistida y desconexión a Pausa/Revisión.
- Cámara no disponible muestra error; comparación facial ambigua no asigna identidad.
- JavaScript pasa `node --check`.
- Cargados YOLO11n, YuNet y SFace reales. Frame vacío: cero personas, ningún rostro; SFace devuelve 128 dimensiones.
- Imagen bus.jpg incluida por Ultralytics: cuatro personas detectadas y continuidad de IDs al repetir el frame. No es una evaluación de precisión en video de un salón.

Las pruebas de páginas mediante Django validan respuestas y templates, no el resultado visual de JavaScript.

## No verificado / límites materiales

- No hay acceso a la cámara del usuario: pendientes integrada/USB, permisos, FPS y comportamiento térmico del equipo.
- No se midió precisión facial, reidentificación tras oclusiones ni desempeño con alumnos sentados en el aula.
- La revisión gráfica completa en navegador no se completó: el navegador local encontró una restricción de sockets del entorno y el navegador remoto no completó acceso al servidor local. No se adjuntan capturas como si se hubiera validado el diseño renderizado.
- Compatibilidad de instalación en macOS y Windows documentada, pero ejecutada aquí solo en Linux/Python 3.12.14.
- No se probaron carga concurrente de producción ni varias cámaras; quedan fuera de esta versión.

Ver **ACEPTACION.md** para ejecutar y registrar la validación física. No utilizar datos sintéticos como evidencia de precisión de visión.
