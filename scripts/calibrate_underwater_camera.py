"""Empirical in-water checkerboard calibration. Does not estimate a refractive port model.
Keep housing, focus, resolution and water conditions fixed. Holdout reprojection
is a diagnostic, not independent metric-distance validation.
"""
import argparse,json
from pathlib import Path
import cv2
import numpy as np

def calibrate(images,cols,rows,square_m):
    if cols<3 or rows<3 or square_m<=0:raise ValueError('Invalid board')
    grid=np.zeros((cols*rows,3),np.float32);grid[:,:2]=np.mgrid[:cols,:rows].T.reshape(-1,2)*square_m
    corners=[];names=[];size=None
    for path in images:
        im=cv2.imread(str(path),cv2.IMREAD_GRAYSCALE)
        if im is None:raise ValueError('Unreadable image '+str(path))
        current=(im.shape[1],im.shape[0])
        if size and current!=size:raise ValueError('Mixed image resolutions')
        size=current
        found,points=cv2.findChessboardCornersSB(im,(cols,rows))
        if found:corners.append(points.astype(np.float32));names.append(str(path))
    if len(corners)<12:raise ValueError('Need >=12 detected board views; include different depths, tilts and image edges')
    holdout=[i for i in range(len(corners)) if i%5==0];train=[i for i in range(len(corners)) if i not in holdout]
    rms,k,d,_,_=cv2.calibrateCamera([grid]*len(train),[corners[i] for i in train],size,None,None)
    errors=[]
    for i in holdout:
        ok,r,t=cv2.solvePnP(grid,corners[i],k,d)
        if not ok:raise ValueError('Held-out pose estimation failed')
        projected,_=cv2.projectPoints(grid,r,t,k,d)
        errors.append({'file':names[i],'rms_px':float(np.sqrt(np.mean(np.sum((projected-corners[i])**2,axis=2))))})
    return {'model':'plumb_bob','resolution':list(size),'k':k.tolist(),'d':d.ravel().tolist(),
            'train_rms_px':rms,'train_images':[names[i] for i in train],'holdout':errors,
            'square_m':square_m,'warning':'Empirical central model, not explicit flat-port refraction. Validate independent known distances throughout operating volume.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('images',type=Path);p.add_argument('--cols',type=int,required=True);p.add_argument('--rows',type=int,required=True);p.add_argument('--square-m',type=float,required=True);p.add_argument('--vision-output',type=Path,help='Optional ready-to-use vision config patch');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    files=sorted(x for x in a.images.iterdir() if x.suffix.lower() in ('.png','.jpg','.jpeg'))
    result=calibrate(files,a.cols,a.rows,a.square_m);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')

    if a.vision_output:
        a.vision_output.parent.mkdir(parents=True,exist_ok=True)
        a.vision_output.write_text(json.dumps({'calibration':result},indent=2)+'\n')
