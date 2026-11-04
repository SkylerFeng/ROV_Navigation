"""Evaluate held-out rendered layouts and export trained YOLO ONNX."""
import json,hashlib
from pathlib import Path
from ultralytics import YOLO
root=Path(__file__).resolve().parents[1];out=root/'logs/semantic_detector_lit'
best=out/'train/weights/best.pt';model=YOLO(best)
val=model.val(data=str(root/'logs/semantic_dataset_lit/dataset.yaml'),split='test',device=0,plots=True,project=str(out),name='test',exist_ok=True)
export=model.export(format='onnx',imgsz=640,opset=17,simplify=False,device='cpu')
result={'weights':str(best),'sha256':hashlib.sha256(best.read_bytes()).hexdigest(),'onnx':str(export),'onnx_sha256':hashlib.sha256(Path(export).read_bytes()).hexdigest(),'test_metrics':{k:float(v) for k,v in val.results_dict.items()},'classes':model.names}
(out/'metrics.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
