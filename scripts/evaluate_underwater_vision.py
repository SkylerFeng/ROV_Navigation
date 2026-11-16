"""Same detector, confidence and labeled split for every image-processing baseline."""
import argparse,csv,json,time,hashlib
from pathlib import Path
import cv2
import numpy as np
from semantic_vision import load_vision,enhance
from semantic_detector import Detector

def iou(a,b):
    a=np.array(a);b=np.array(b);area=np.maximum(0,np.minimum(a[2:],b[2:])-np.maximum(a[:2],b[:2])).prod()
    return float(area/max(1e-9,(a[2:]-a[:2]).prod()+(b[2:]-b[:2]).prod()-area))

def run(dataset,output,model,split='test'):
    output.mkdir(parents=True,exist_ok=True);cv2.setNumThreads(1)
    detector=Detector(model,.45);cfg=load_vision();rows=[];images=sorted((dataset/'images'/split).glob('*.png'))
    if not images:raise ValueError('No labeled images')
    methods=['none','white_balance','clahe','wb_clahe','fusion']
    for method in methods:
        tp=fp=fn=0;latency=[];details=[]
        for index,path in enumerate(images):
            rgb=cv2.cvtColor(cv2.imread(str(path)),cv2.COLOR_BGR2RGB);h,w=rgb.shape[:2]
            gt=[]
            for line in (dataset/'labels'/split/(path.stem+'.txt')).read_text().splitlines():
                cls,x,y,bw,bh=map(float,line.split());gt.append((['pipe','box'][int(cls)],[(x-bw/2)*w,(y-bh/2)*h,(x+bw/2)*w,(y+bh/2)*h]))
            t=time.perf_counter();out=enhance(rgb,None,{**cfg,'method':method});latency.append((time.perf_counter()-t)*1000)
            detections=sorted(detector.predict(out),key=lambda d:d['detector_score'],reverse=True);used=set();matched=0
            for d in detections:
                options=[(iou(d['bbox'],b),i) for i,(c,b) in enumerate(gt) if c==d['category'] and i not in used]
                score,i=max(options,default=(0,-1))
                if score>=.5:used.add(i);matched+=1
            tp+=matched;fp+=len(detections)-matched;fn+=len(gt)-matched
            details.append({'image':path.name,'tp':matched,'fp':len(detections)-matched,'fn':len(gt)-matched})
            if index==0:cv2.imwrite(str(output/(method+'.png')),cv2.cvtColor(out,cv2.COLOR_RGB2BGR))
        row={'method':method,'frames':len(images),'tp':tp,'fp':fp,'fn':fn,'precision':tp/max(1,tp+fp),'recall':tp/max(1,tp+fn),'preprocess_median_ms':float(np.median(latency)),'preprocess_p95_ms':float(np.percentile(latency,95))}
        rows.append(row);(output/(method+'_per_frame.json')).write_text(json.dumps(details,indent=2));print(row,flush=True)
    (output/'metrics.json').write_text(json.dumps(rows,indent=2)+'\n')
    with (output/'metrics.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys(),lineterminator='\n');w.writeheader();w.writerows(rows)
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,len(methods),figsize=(20,4))
    for ax,m in zip(axes,methods):ax.imshow(cv2.cvtColor(cv2.imread(str(output/(m+'.png'))),cv2.COLOR_BGR2RGB));ax.set_title(m);ax.axis('off')
    fig.tight_layout();fig.savefig(output/'comparison.png',dpi=160);plt.close(fig)
    sources=[model,*images,*sorted((dataset/'labels'/split).glob('*.txt'))]
    (output/'sources.json').write_text(json.dumps({'dataset':str(dataset),'split':split,'confidence':.45,'iou_threshold':.5,'note':'Frozen detector; no retraining. Test split is diagnostic, not a tuning set. No RGB-D range restoration on dataset without range.','sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}},indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dataset',type=Path,default=Path('logs/semantic_dataset_lit'));p.add_argument('--model',type=Path,default=Path('logs/semantic_detector_lit/train/weights/best.onnx'));p.add_argument('--split',choices=['val','test'],default='test');p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.dataset,a.output,a.model,a.split)
