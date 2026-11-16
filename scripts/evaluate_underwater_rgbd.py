"""Known synthetic chart physics check and real saved RGB-D processing preview.
Synthetic inverse-model result is not evidence of real-water generalization.
"""
import argparse,json,time
from pathlib import Path
import numpy as np
import cv2
from semantic_vision import load_vision,enhance
from semantic_core import color_mask,localize_detection
from semantic_detector import Detector
from semantic_color import ColorModel

def run(output):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    cv2.setNumThreads(1);output.mkdir(parents=True,exist_ok=True);cfg=load_vision()
    methods=['none','white_balance','clahe','wb_clahe','fusion','range_restore']
    colors=[('red',[180,30,25]),('yellow',[190,175,20]),('blue',[20,45,180])]
    clear=np.zeros((240,320,3),np.uint8);depth=np.zeros((240,320),np.float32)
    for i,(name,color) in enumerate(colors):
        clear[i*80:(i+1)*80]=color
        for j,z in enumerate([.5,2,4,6]):depth[i*80:(i+1)*80,j*80:(j+1)*80]=z
    z=depth[:,:,None]
    observed=np.uint8(np.clip(clear/255*np.exp(-z*np.array(cfg['attenuation_rgb']))+np.array(cfg['veiling_rgb'])*(1-np.exp(-z*np.array(cfg['backscatter_rgb']))),0,1)*255)
    rows=[];fig,axes=plt.subplots(1,7,figsize=(21,4))
    axes[0].imshow(clear);axes[0].set_title('Synthetic clean');axes[0].axis('off')
    for ax,m in zip(axes[1:],methods):
        out=enhance(observed,depth,{**cfg,'method':m});correct=0
        for i,(name,_) in enumerate(colors):
            for j in range(4):correct+=color_mask(out[i*80:(i+1)*80,j*80:(j+1)*80])[0]==name
        rows.append({'method':m,'synthetic_rgb_mae_0_255':float(np.abs(out.astype(float)-clear).mean()),'synthetic_hsv_correct_patches':correct,'patches':12})
        ax.imshow(out);ax.set_title(m);ax.axis('off')
    fig.tight_layout();fig.savefig(output/'synthetic_range_chart.png',dpi=150);plt.close(fig)
    (output/'synthetic_metrics.json').write_text(json.dumps({'note':'Same known coefficients generate and invert the chart; ideal range, no noise. Not Sea-thru parameter estimation or real camera color accuracy.','results':rows},indent=2)+'\n')
    detector=Detector('logs/semantic_detector_lit/train/weights/best.onnx',.45);color=ColorModel('config/semantic/color_model.npz')
    for case in ('blue_pipe','yellow_box','red_box'):
        src=Path('logs/meeting_report_20261111')/case/'semantic/latest_sensor.npz'
        with np.load(src) as data:rgb=data['rgb'];d=data['depth'];k=data['k'];cp=data['cp'];cq=data['cq']
        results=[];fig,axes=plt.subplots(2,3,figsize=(15,7))
        for ax,m in zip(axes.ravel(),methods):
            start=time.perf_counter();out=enhance(rgb,d,{**cfg,'method':m});lat=(time.perf_counter()-start)*1000
            boxes=detector.predict(out);localized=[]
            for b in boxes:
                raw=localize_detection(rgb,d,k,cp,cq,b['bbox'],color)
                processed=localize_detection(out,d,k,cp,cq,b['bbox'],None)
                localized.append({'detector':b,'raw_color_model':raw,'processed_hsv':processed})
            ax.imshow(out);ax.set_title(m);ax.axis('off')
            results.append({'method':m,'preprocessing_ms':lat,'detections':localized})
        fig.tight_layout();fig.savefig(output/(case+'_rgbd_comparison.png'),dpi=150);plt.close(fig)
        (output/(case+'_rgbd.json')).write_text(json.dumps({'source':str(src),'note':'Re-inference preview, not a new navigation trial or labeled detection benchmark.','results':results},indent=2)+'\n')
    print(json.dumps(rows,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)
