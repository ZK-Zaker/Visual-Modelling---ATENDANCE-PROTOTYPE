"""Three pretrained ML models. No remote inference; model loading is explicit."""
from pathlib import Path
import time
from django.conf import settings

class Vision:
    def __init__(self):
        import cv2
        from ultralytics import YOLO
        base=settings.BASE_DIR/'model_weights'
        paths=[base/'yolo11n.pt',base/'face_detection_yunet_2023mar.onnx',base/'face_recognition_sface_2021dec.onnx']
        if not all(p.exists() for p in paths):
            raise RuntimeError('Faltan modelos. Ejecuta: python scripts/download_models.py')
        self.cv=cv2
        self.person=YOLO(str(paths[0]))
        self.face=cv2.FaceDetectorYN.create(str(paths[1]),'',(320,320),.85,.3,5000)
        self.rec=cv2.FaceRecognizerSF.create(str(paths[2]),'')

    def extract(self, crop):
        cv=self.cv
        h,w=crop.shape[:2]
        if min(h,w)<60: return None
        self.face.setInputSize((w,h));_,faces=self.face.detect(crop)
        if faces is None or len(faces)!=1: return None
        f=faces[0]
        if min(f[2],f[3])<45: return None
        aligned=self.rec.alignCrop(crop,f)
        if cv.Laplacian(cv.cvtColor(aligned,cv.COLOR_BGR2GRAY),cv.CV_64F).var()<35: return None
        feature=self.rec.feature(aligned).flatten()
        import numpy as np
        feature=feature/(np.linalg.norm(feature)+1e-9)
        return feature,aligned

    def detect(self, frame):
        # Persist tracker across consecutive frames. ByteTrack itself is not counted as ML.
        result=self.person.track(frame,persist=True,tracker='bytetrack.yaml',classes=[0],conf=.3,imgsz=640,verbose=False,device='cpu')[0]
        if result.boxes.id is None: return []
        h,w=frame.shape[:2];out=[]
        for box,tid in zip(result.boxes.xyxy.cpu().tolist(),result.boxes.id.int().cpu().tolist()):
            a,b,c,d=map(int,box);a=max(0,a);b=max(0,b);c=min(w,c);d=min(h,d)
            if c>a and d>b: out.append((tid,(a,b,c,d)))
        return out
