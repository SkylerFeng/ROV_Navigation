"""Aligned geometry and bounded underwater enhancement; no semantic scene truth.
Fusion is a lightweight inspired baseline; range recovery is NOT full Sea-thru.
"""
import time
from pathlib import Path
import cv2
import numpy as np
from semantic_config import read_object, merge_known

ROOT = Path(__file__).resolve().parents[1]

def load_vision(path=None):
    cfg = read_object(ROOT/'config/semantic/vision.json')
    if path: cfg = merge_known(cfg, read_object(path), 'vision')
    if cfg['method'] not in ('none','white_balance','clahe','wb_clahe','fusion','range_restore','range_preserve','neutral_balance'):
        raise ValueError('Unknown vision method')
    if cfg['detector_source'] not in ('raw','processed'):raise ValueError('Invalid detector_source')
    if cfg['color_source'] not in ('raw','processed_hsv'):
        raise ValueError('color_source must be raw or processed_hsv')
    if cfg['geometry'] not in ('auto','none'): raise ValueError('geometry must be auto or none')
    for key in ('max_gain','clahe_clip','gamma','min_transmission','neutral_max_gain','preview_gamma','preview_max_gain'):
        x=cfg[key]
        if isinstance(x,bool) or not isinstance(x,(int,float)) or not np.isfinite(x) or x<=0: raise ValueError('Invalid '+key)
    if not 1<=cfg['max_gain']<=8 or cfg['min_transmission']>1: raise ValueError('Unbounded gain')
    for key in ('attenuation_rgb','backscatter_rgb','veiling_rgb'):
        x=np.asarray(cfg[key],float)
        if x.shape!=(3,) or not np.isfinite(x).all() or (x<0).any(): raise ValueError('Invalid '+key)
        cfg[key]=x.tolist()
    if max(cfg['veiling_rgb'])>1: raise ValueError('veiling_rgb must be normalized')
    neutral=np.asarray(cfg['neutral_gain_rgb'],float)
    if not 1<=cfg['neutral_max_gain']<=2 or not 1<=cfg['preview_max_gain']<=4 or not .5<=cfg['preview_gamma']<=1:
        raise ValueError('Unsafe neutral/preview gain')
    if neutral.shape!=(3,) or not np.isfinite(neutral).all() or (neutral<1/cfg['neutral_max_gain']).any() or (neutral>cfg['neutral_max_gain']).any():
        raise ValueError('neutral_gain_rgb exceeds bounded calibration gains')
    cfg['neutral_gain_rgb']=neutral.tolist()
    if cfg['calibration'] is not None:
        cal=cfg['calibration']
        if not isinstance(cal,dict) or not {'k','d','resolution','model'}<=set(cal):raise ValueError('Calibration requires k,d,resolution,model')
        k=np.asarray(cal['k'],float);d=np.asarray(cal['d'],float)
        if k.shape!=(3,3) or not np.isfinite(k).all() or d.shape not in ((4,),(5,),(8,),(12,),(14,)) or not np.isfinite(d).all():raise ValueError('Invalid calibration')
        if cal['model'] not in ('plumb_bob','rational_polynomial'):raise ValueError('Unsupported calibration model')
        if len(cal['resolution'])!=2 or any(type(x) is not int or x<=0 for x in cal['resolution']):raise ValueError('Invalid calibration resolution')
    return cfg

def white_balance(rgb, max_gain=2.):
    x=rgb.astype(np.float32)/255
    # Gray-world is only a heuristic; bound gains for scenes dominated by one color.
    means=x.reshape(-1,3).mean(0)
    gain=np.clip(means.mean()/np.maximum(means,1e-4),1/max_gain,max_gain)
    return np.uint8(np.clip(x*gain,0,1)*255)

def clahe(rgb, clip=2.):
    lab=cv2.cvtColor(rgb,cv2.COLOR_RGB2LAB)
    lab[:,:,0]=cv2.createCLAHE(clipLimit=clip,tileGridSize=(8,8)).apply(lab[:,:,0])
    return cv2.cvtColor(lab,cv2.COLOR_LAB2RGB)

def fusion(rgb,cfg):
    x=rgb.astype(np.float32)/255
    means=x.mean((0,1))
    x[:,:,0]+=max(0,float(means[1]-means[0]))*(1-x[:,:,0])*x[:,:,1]
    base=white_balance(np.uint8(np.clip(x,0,1)*255),cfg['max_gain']).astype(np.float32)/255
    detail=base-cv2.GaussianBlur(base,(0,0),1.2)
    span=float(detail.max()-detail.min())
    normalized=(detail-detail.min())/span if span>1e-6 else base
    inputs=[np.power(base,cfg['gamma']),np.clip((base+normalized)/2,0,1)]
    weights=[]
    for a in inputs:
        lum=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY)
        contrast=np.abs(cv2.Laplacian(lum,cv2.CV_32F))
        saturation=np.sqrt(np.mean((a-lum[:,:,None])**2,axis=2))
        lab=cv2.cvtColor(a,cv2.COLOR_RGB2LAB)
        saliency=np.linalg.norm(cv2.GaussianBlur(lab,(5,5),0)-lab.mean((0,1)),axis=2)/100
        weights.append(contrast+saturation+saliency+.1)
    total=weights[0]+weights[1];weights=[w/total for w in weights]
    levels=min(4,int(np.log2(min(rgb.shape[:2])))-1)
    pyramids=[]
    for a,w in zip(inputs,weights):
        gp=[a];wp=[w]
        for _ in range(levels):gp.append(cv2.pyrDown(gp[-1]));wp.append(cv2.pyrDown(wp[-1]))
        lp=[gp[i]-cv2.pyrUp(gp[i+1],dstsize=(gp[i].shape[1],gp[i].shape[0])) for i in range(levels)]+[gp[-1]]
        pyramids.append([l*wt[:,:,None] for l,wt in zip(lp,wp)])
    out=pyramids[0][-1]+pyramids[1][-1]
    for i in reversed(range(levels)):
        layer=pyramids[0][i]+pyramids[1][i]
        out=cv2.pyrUp(out,dstsize=(layer.shape[1],layer.shape[0]))+layer
    return np.uint8(np.clip(out,0,1)*255)

def ratio_preserving_exposure(rgb,gamma=.8,max_gain=2.):
    """One scalar per pixel: preserve RGB ratios, avoid per-channel clipping."""
    x=rgb.astype(np.float32)/255
    value=x.max(axis=2,keepdims=True)
    gain=np.minimum(np.power(np.maximum(value,1e-6),gamma-1),max_gain)
    gain=np.minimum(gain,1/np.maximum(value,1e-6))
    return np.uint8(np.clip(np.rint(x*gain*255),0,255))

def estimate_neutral_gains(rgb,mask,max_gain=1.25):
    """Explicit user-labelled neutral card only; never discover gray from scene color."""
    rgb=np.asarray(rgb);mask=np.asarray(mask,bool)
    if rgb.dtype!=np.uint8 or mask.shape!=rgb.shape[:2]:raise ValueError('Invalid neutral calibration image/mask')
    valid=mask&(rgb.min(axis=2)>=20)&(rgb.max(axis=2)<=235)
    if valid.sum()<64:raise ValueError('Not enough unclipped neutral-card pixels')
    means=np.median(rgb[valid].astype(float),axis=0)
    gains=means.mean()/means
    if not 1<=max_gain<=2 or (gains>max_gain).any() or (gains<1/max_gain).any():
        raise ValueError('Neutral calibration needs excessive gain; check exposure/water parameters')
    return gains.tolist()

def enhance(rgb,depth,cfg):
    method=cfg['method']
    if method=='none': return rgb.copy()
    if method=='white_balance': return white_balance(rgb,cfg['max_gain'])
    if method=='clahe': return clahe(rgb,cfg['clahe_clip'])
    if method=='wb_clahe': return clahe(white_balance(rgb,cfg['max_gain']),cfg['clahe_clip'])
    if method=='fusion': return fusion(rgb,cfg)
    if method=='neutral_balance':
        # Fixed calibrated gains: do not infer illuminant from a blue-dominated frame.
        x=rgb.astype(float)*np.asarray(cfg['neutral_gain_rgb'])
        x/=np.maximum(1,x.max(axis=2,keepdims=True)/255)
        return np.uint8(np.clip(np.rint(x),0,255))
    if method not in ('range_restore','range_preserve'):raise ValueError('Unknown vision method')
    if depth is None: raise ValueError('range_restore requires aligned ray range in metres')
    valid=np.isfinite(depth)&(depth>.08)&(depth<8.)
    z=np.where(valid,depth,0)[:,:,None]
    direct=np.maximum(np.exp(-z*np.asarray(cfg['attenuation_rgb'])),cfg['min_transmission'])
    scatter=np.asarray(cfg['veiling_rgb'])*(1-np.exp(-z*np.asarray(cfg['backscatter_rgb'])))
    recovered=(rgb.astype(float)/255-scatter)*np.minimum(1/direct,cfg['max_gain'])
    out=np.uint8(np.clip(recovered,0,1)*255);out[~valid]=rgb[~valid]
    if method=='range_preserve':
        out=ratio_preserving_exposure(out,cfg['preview_gamma'],cfg['preview_max_gain'])
        out[~valid]=rgb[~valid]
    return out

class VisionFrontend:
    def __init__(self,cfg): self.cfg=cfg;self.maps={}
    def process(self,rgb,depth,k,distortion=(),model='plumb_bob'):
        start=time.perf_counter();rgb=np.asarray(rgb);depth=np.asarray(depth)
        cal=self.cfg.get('calibration')
        if cal:
            if list(cal['resolution'])!=[rgb.shape[1],rgb.shape[0]]:raise ValueError('Calibration resolution mismatch; do not silently scale intrinsics')
            k=cal['k'];distortion=cal['d'];model=cal['model']
        k=np.asarray(k,float).reshape(3,3);d=np.asarray(distortion,float)
        if rgb.dtype!=np.uint8 or rgb.shape!=(*depth.shape,3):raise ValueError('Unaligned RGB/range')
        if not np.isfinite(k).all() or k[0,0]<=0 or k[1,1]<=0 or abs(k[0,1])>1e-8 or not np.allclose(k[2],[0,0,1]):raise ValueError('Invalid intrinsics')
        if not np.isfinite(d).all():raise ValueError('Invalid distortion')
        rectified=bool(d.size and np.any(d!=0))
        if rectified:
            if self.cfg['geometry']=='none':raise ValueError('Nonzero distortion cannot use pinhole localization without rectification')
            if model not in ('plumb_bob','rational_polynomial'):raise ValueError('Unsupported calibration model')
            if d.size not in (4,5,8,12,14):raise ValueError('Unsupported distortion coefficients')
            key=(depth.shape,k.tobytes(),d.tobytes())
            if key not in self.maps:
                self.maps={key:cv2.initUndistortRectifyMap(k,d,None,k,(rgb.shape[1],rgb.shape[0]),cv2.CV_32FC1)}
            mx,my=self.maps[key]
            # Same map for both streams; nearest range avoids mixing different surfaces.
            rgb=cv2.remap(rgb,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
            depth=cv2.remap(depth,mx,my,cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT,borderValue=float('nan'))
        processed=enhance(rgb,depth,self.cfg)
        return rgb,processed,depth,k,{'method':self.cfg['method'],'rectified':rectified,
            'color_source':self.cfg['color_source'],'detector_source':self.cfg['detector_source'],'processing_ms':(time.perf_counter()-start)*1000,
            'invalid_range_fraction':float((~np.isfinite(depth)|(depth<=0)).mean())}
