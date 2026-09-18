# Colaborar en Attendance Viz V1

1. Clona el repositorio y sigue README.md. Cada persona crea su entorno virtual, base de datos y usuario local.
2. Antes de una mejora, actualiza main y crea una rama descriptiva: `git switch main`, `git pull --ff-only`, `git switch -c feature/nombre-del-cambio`.
3. Mantén cada cambio acotado; documenta su propósito, comportamiento y limitaciones.
4. Ejecuta `python manage.py check` y `python manage.py test classroom`. Para cambios en cámara, añade evidencia de prueba física; el curso demo no acredita precisión facial.
5. Si cambias modelos Django, incluye la migración. No subas db.sqlite3, .secret, .env, entornos virtuales, pesos de modelos ni fotos de personas.
6. Haz commit y push de tu rama y abre un pull request hacia main con qué cambió y cómo se verificó.

Para enviar cambios necesitas permiso de escritura o utilizar un fork. La validación y las limitaciones conocidas de V1 están en docs/VALIDACION.md y docs/REQUISITOS.md.
