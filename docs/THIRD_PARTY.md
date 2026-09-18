# Fuentes técnicas y modelos externos

- Django 5.2: https://docs.djangoproject.com/en/5.2/releases/5.2/ — framework LTS, licencia BSD.
- Ultralytics tracking: https://docs.ultralytics.com/modes/track/ — detección YOLO y ByteTrack.
- YOLO11n weights: https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt
- Ultralytics licensing: https://www.ultralytics.com/license — revisar AGPL-3.0/condiciones aplicables antes de redistribuir el sistema o llevarlo a un uso distinto al proyecto académico.
- OpenCV face tutorial: https://docs.opencv.org/4.x/d0/dd4/tutorial_dnn_face.html
- YuNet: https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet
- SFace: https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface
- ByteTrack: https://github.com/ifzhang/ByteTrack

Los modelos conservan las licencias de sus autores. El ZIP de código no incluye los pesos: el script descarga desde sus fuentes y verifica SHA-256. La implementación propia de visualizaciones no requiere librerías JS externas, fuentes web ni CDN.

## Evidencia del requisito ML

| Modelo | Entrada | Salida | Papel |
|---|---|---|---|
| YOLO11n | Frame RGB/BGR convertido por el predictor | Cajas de personas | Localizar cuerpos para tracking |
| YuNet | Recorte de una persona | Rostro y puntos faciales | Ubicar/alinear el rostro |
| SFace | Rostro alineado | Vector de 128 dimensiones | Comparar identidad con referencias locales |

Son tres redes preentrenadas. La aplicación no entrena una red propia; el registro de alumnos construye una galería de características. ByteTrack no se cuenta como cuarto modelo de ML. Los parámetros de similitud deben calibrarse con datos consentidos del escenario real.
