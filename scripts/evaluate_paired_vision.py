"""Evaluate against same-frame pre-OceanSim reference. Truth is offline only."""
import argparse,json,hashlib,time,shutil
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from semantic_vision import load_vision,enhance,ratio_preserving_exposure
from semantic_detector import Detector
from semantic_color import ColorModel
from semantic_core import color_mask
from evaluate_underwater_vision import iou

def run(source,output):
    import matplotlib;matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output.mkdir(parents=True,exist_ok=True);cv2.setNumThreads(1)
    cfg=load_vision();detector=Detector('logs/semantic_detector_lit/train/weights/best.onnx',.45)
    color=ColorModel('config/semantic/color_model.npz');allrows=[];sources={}
    methods=['reference','none','white_balance','fusion','clahe','range_restore','range_preserve','exposure_only']
    for case in ('blue_pipe','yellow_box','red_box'):
        folder=source/case;dest=output/case;dest.mkdir(exist_ok=True)
        metadata=json.loads((folder/'metadata.json').read_text())
        for key in ('attenuation_rgb','backscatter_rgb','veiling_rgb'):
            if not np.allclose(cfg[key],metadata[key],atol=1e-6):raise ValueError('Capture and recovery water parameters differ')
        with np.load(folder/'paired.npz') as data:rgb=data['rgb'];depth=data['depth'];ref=data['reference']
        masks=np.load(folder/'object_masks.npz')
        valid=np.isfinite(depth)&(depth>.08)&(depth<8)
        ref_float=ref.astype(np.float32)/255
        ref_hsv=cv2.cvtColor(ref_float,cv2.COLOR_RGB2HSV)
        meaningful=valid&(ref.max(axis=2)>20)
        ref_chroma=ref_float/np.maximum(ref_float.sum(axis=2,keepdims=True),1e-6)
        fig,axes=plt.subplots(2,4,figsize=(18,6.8));rows=[]
        for ax,method in zip(axes.ravel(),methods):
            start=time.perf_counter()
            out=ref if method=='reference' else ratio_preserving_exposure(rgb,cfg['preview_gamma'],cfg['preview_max_gain']) if method=='exposure_only' else enhance(rgb,depth,{**cfg,'method':method})
            latency=(time.perf_counter()-start)*1000
            Image.fromarray(out).save(dest/(method+'.png'))
            predicted=detector.predict(out);used=set();tp=0
            for det in sorted(predicted,key=lambda d:d['detector_score'],reverse=True):
                overlaps=[(iou(det['bbox'],o['bbox']),i) for i,o in enumerate(metadata['objects']) if i not in used and o['category']==det['category']]
                score,i=max(overlaps,default=(0,-1))
                if score>=.5:used.add(i);tp+=1
            f=out.astype(np.float32)/255;hsv=cv2.cvtColor(f,cv2.COLOR_RGB2HSV)
            chroma=f/np.maximum(f.sum(axis=2,keepdims=True),1e-6)
            row={'case':case,'method':method,'valid_pixels':int(valid.sum()),'reference_lit_pixels':int(meaningful.sum()),
                 'rgb_mae_0_255':float(np.abs(out.astype(float)-ref)[valid].mean()),
                 'chromaticity_l1_lit':float(np.abs(chroma-ref_chroma)[meaningful].sum(axis=1).mean()) if meaningful.any() else None,
                 'detector_tp':tp,'detector_fp':len(predicted)-tp,'detector_fn':len(metadata['objects'])-tp,'preprocessing_ms':latency,'objects':[]}
            for obj in metadata['objects']:
                mask=masks[obj['id']];eligible=mask&meaningful&(ref_hsv[:,:,1]>.15)
                hue_delta=np.abs(hsv[:,:,0]-ref_hsv[:,:,0]);hue_delta=np.minimum(hue_delta,360-hue_delta)
                x0,y0,x1,y1=obj['bbox'];crop=out[y0:y1,x0:x1]
                crop_mask=mask[y0:y1,x0:x1];pixels=np.zeros_like(crop);pixels[crop_mask]=crop[crop_mask]
                row['objects'].append({'id':obj['id'],'expected_color':obj['color'],'mask_pixels':int(mask.sum()),
                    'rgb_mae':float(np.abs(out.astype(float)-ref)[mask&valid].mean()) if (mask&valid).any() else None,
                    'hue_valid_pixels':int(eligible.sum()),
                    'hue_error_deg':float(hue_delta[eligible].mean()) if eligible.any() else None,
                    'hsv_color_on_offline_mask':color_mask(pixels)[0],
                    'trained_color_on_offline_mask':color.classify(pixels)[0]})
            rows.append(row);ax.imshow(out);ax.set_title(method);ax.axis('off')
        fig.suptitle(case+' | Same-frame reference and processing comparison',fontsize=14)
        fig.tight_layout();fig.savefig(dest/'comparison.png',dpi=160);plt.close(fig)
        (dest/'metrics.json').write_text(json.dumps(rows,indent=2)+'\n')
        shutil.copy2(folder/'metadata.json',dest/'capture_metadata.json')
        allrows.extend(rows)
        for path in folder.iterdir():
            if path.is_file():sources[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
        print(case,[(r['method'],round(r['rgb_mae_0_255'],2),r['detector_tp'],r['detector_fp']) for r in rows],flush=True)
    (output/'metrics.json').write_text(json.dumps(allrows,indent=2)+'\n')
    (output/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
    note=['# 同帧水下处理对照','','每幅图：reference 为场景渲染后、OceanSim 衰减/散射前的 LdrColor，不是空气中拍摄的真值。none 为同一帧经过 OceanSim 后的图像。','', 'range_restore 用已知渲染参数恢复；range_preserve 在恢复后按像素同比例提亮；exposure_only 仅同比例提亮原图。提亮图的亮度不同于 reference，应结合色度/色相而非只看 RGB 误差。','','检测阈值 0.45，IoU≥0.5，三个固定视角，不是完整测试集；目标颜色的掩码来自离线实例分割，不提供给运行时。','']
    for case in ('blue_pipe','yellow_box','red_box'):note.append(f'- [{case} 对比图]({case}/comparison.png)')
    (output/'README.md').write_text('\n'.join(note)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.source,a.output)
