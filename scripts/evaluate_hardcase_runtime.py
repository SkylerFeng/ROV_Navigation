"""Actual ONNX threshold (.45), visible focus-object IoU>=.5, held-out views."""
import json,argparse
from pathlib import Path
import numpy as np
from PIL import Image
from semantic_detector import Detector
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('logs/hardening_20261116'));a=p.parse_args();root=a.root
manifest=json.loads((root/'data_heldout/manifest.json').read_text());result={}
def iou(a,b):
 a=np.asarray(a);b=np.asarray(b);wh=np.maximum(0,np.minimum(a[2:],b[2:])-np.maximum(a[:2],b[:2]));inter=np.prod(wh)
 return inter/max(1,np.prod(a[2:]-a[:2])+np.prod(b[2:]-b[:2])-inter)
for name,path in [('baseline',Path('logs/semantic_detector_lit/train/weights/best.onnx')),('candidate',root/'detector/train/weights/best.onnx')]:
 detector=Detector(path);groups={};rows=[]
 for row in manifest['rows']:
  target=next((v for v in row['visible'] if v['id']==row['focus']),None)
  if target is None:continue
  cls='pipe' if 'Pipe' in row['focus'] else 'box'
  angle=row['angle_relative_deg']%180
  group=('pipe_end' if angle==0 else 'pipe_side' if angle==90 else 'pipe_oblique') if cls=='pipe' else 'box'
  preds=detector.predict(np.asarray(Image.open(root/'data_heldout/images/test'/(row['id']+'.png'))))
  pred=max(preds,key=lambda d:iou(d['bbox'],target['bbox']),default=None)
  outcome='miss' if pred is None or iou(pred['bbox'],target['bbox'])<.5 else ('correct' if pred['category']==cls else 'wrong_class')
  counts=groups.setdefault(group,dict(correct=0,miss=0,wrong_class=0));counts[outcome]+=1
  rows.append({'id':row['id'],'group':group,'outcome':outcome,'prediction':pred})
 result[name]={'groups':groups,'rows':rows}
(root/'runtime_detection_eval.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v['groups'] for k,v in result.items()},indent=2))
