"""Run once with internet; subsequent camera use is local."""
from pathlib import Path
from urllib.request import urlopen
import hashlib
ROOT=Path(__file__).resolve().parents[1]/'model_weights'
FILES={
'yolo11n.pt':'https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt',
'face_detection_yunet_2023mar.onnx':'https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx',
'face_recognition_sface_2021dec.onnx':'https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx'}
HASHES={
'yolo11n.pt':'0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1',
'face_detection_yunet_2023mar.onnx':'8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4',
'face_recognition_sface_2021dec.onnx':'0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79'}
ROOT.mkdir(exist_ok=True)
for name,url in FILES.items():
    path=ROOT/name
    if not path.exists():
        print('Descargando',name,flush=True)
        try:
            with urlopen(url,timeout=120) as r: data=r.read()
            if len(data)<100000: raise ValueError('Respuesta demasiado pequeña para un modelo.')
            if hashlib.sha256(data).hexdigest()!=HASHES[name]: raise ValueError('Hash del modelo diferente del esperado.')
            tmp=path.with_suffix('.tmp');tmp.write_bytes(data);tmp.replace(path)
        except Exception as exc: raise SystemExit(f'No se descargó {name}: {exc}. Reintenta con conexión a internet.')
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest!=HASHES[name]: raise SystemExit(f'Modelo inválido: {name}. Retíralo y vuelve a descargarlo.')
    print(name,digest)
