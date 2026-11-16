"""Identical held-out images and metrics for old/new detectors; no tuning on test."""
import argparse,json
from pathlib import Path
from ultralytics import YOLO
p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('logs/hardening_20261116'));a=p.parse_args();root=a.root.resolve();result={}
for name,weights in [('baseline',Path('logs/semantic_detector_lit/train/weights/best.pt')),('candidate',root/'detector/train/weights/best.pt')]:
 model=YOLO(str(weights));result[name]={}
 for split,data in [('original',Path('logs/semantic_dataset_lit/dataset.yaml')),('hard',root/'data_heldout/dataset.yaml')]:
  v=model.val(data=str(data),split='test',device=0,plots=True,project=str(root/'evaluation'),name=name+'_'+split,verbose=False)
  result[name][split]={k:float(x) for k,x in v.results_dict.items()}
 (root/'evaluation.json').write_text(json.dumps(result,indent=2))
