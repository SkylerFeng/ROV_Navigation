"""Train two custom classes; export ONNX for CPU runtime separate from Isaac."""
import argparse,json,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--data',default='logs/semantic_dataset_lit/dataset.yaml');p.add_argument('--epochs',type=int,default=45);p.add_argument('--output',default='logs/semantic_detector_lit');a=p.parse_args()
if (Path(a.output)/'train').exists():raise FileExistsError('Choose a fresh training output directory')
from ultralytics import YOLO
model=YOLO(str(Path('logs/semantic_detector/pretrained/yolo11n.pt').resolve()))
model.train(data=a.data,epochs=a.epochs,imgsz=640,batch=12,workers=2,device=0,project=str(Path(a.output).resolve()),name='train',exist_ok=True,seed=41,patience=12,plots=True,verbose=False,save=True,close_mosaic=8)
best=Path(model.trainer.save_dir)/'weights/best.pt';model=YOLO(best)
val=model.val(data=a.data,split='test',device=0,plots=True,project=str(Path(a.output).resolve()),name='test')
export=model.export(format='onnx',imgsz=640,opset=17,simplify=False,device='cpu')
result={'weights':str(best),'sha256':hashlib.sha256(best.read_bytes()).hexdigest(),'onnx':str(export),'test_metrics':{k:float(v) for k,v in val.results_dict.items()},'classes':model.names}
(Path(a.output)/'metrics.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
