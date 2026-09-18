# Diccionario de indicadores

## Presencia de una sesión

Primero se unen todos los intervalos de una misma identidad, se intersectan con los segmentos activos y se vuelven a unir para eliminar duplicados.

`tiempo_observado = duración(unión(intervalos_presencia ∩ segmentos_activos))`

`presencia_% = 100 × tiempo_observado / duración_activa`

El resultado se limita a 100%. Una duración nula produce Revisión, nunca un porcentaje concluyente. El motor puede interpolar continuidad de hasta lost_seconds entre observaciones consecutivas de una misma identidad; por defecto dos segundos. No equivale a cobertura perfecta del aula.

Umbrales iniciales, configurables antes de una sesión:

- Presente: ≥70%.
- Parcial: ≥30% y <70%.
- Ausente: <30%.
- Revisión: sesión con fallo de cobertura o sin duración válida.

## Asistencia histórica

`asistencia_% = 100 × sesiones_presente / sesiones_evaluables_del_alumno`

Se incluyen solo sesiones finalizadas/interrumpidas con registro del alumno y resultado distinto de Revisión. Un Parcial está en el denominador pero no en el numerador. Una sesión anterior a su inscripción no se inventa como ausencia. Alumnos sin sesiones evaluables muestran —.

## Permanencia

`permanencia_alumno_% = 100 × suma(tiempos_observados) / suma(duraciones_activas_evaluables)`

Esto pondera sesiones de distinta duración. El KPI grupal muestra el promedio de estas tasas individuales; no una mezcla de todos los segundos del grupo. Asistencia promedio también es promedio por alumno. La tendencia por sesión, en cambio, es presentes / participantes evaluables de esa sesión. Las etiquetas distinguen esos denominadores.

## Riesgo

`bajo_mínimo = asistencia_histórica < mínimo_configurado`

Se excluyen alumnos sin datos evaluables. La etiqueta expresa riesgo respecto a un mínimo, no predice abandono ni rendimiento. El mínimo por defecto es 80%, pendiente de confirmar con el profesor.

## Timeline y atlas

Timeline: eje temporal desde el comienzo; verde = observado; fondo claro = segmento activo sin observación; rayado = pausa/interrupción fuera de segmentos activos.

Atlas: filas de alumnos, columnas de sesiones; ● Presente, ◐ Parcial, ○ Ausente, ? Revisión, — no participante. El tooltip muestra el porcentaje de presencia aunque la clasificación esté en revisión.

El número de desconocidos por sesión cuenta identidades pendientes distintas observadas, no frames ni todas las personas no detectadas.

## Revisión humana

Una desconexión no genera automáticamente ausencias definitivas. Si el profesor acepta la medición parcial, se exige justificación; la bitácora conserva quién lo hizo. Aceptarla cambia el denominador a la duración efectivamente capturada, por lo que requiere juicio del docente. No existe corrección manual de intervalos en esta versión.
