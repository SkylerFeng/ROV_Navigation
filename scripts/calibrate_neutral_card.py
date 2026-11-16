"""Export bounded gains from an explicitly labelled neutral-card region.
Mask must describe a physically neutral card under matching capture conditions.
"""
import argparse,json,hashlib
from pathlib import Path
import cv2
from semantic_vision import estimate_neutral_gains
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--image',type=Path,required=True);p.add_argument('--mask',type=Path,required=True);p.add_argument('--max-gain',type=float,default=1.25);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    bgr=cv2.imread(str(a.image));mask=cv2.imread(str(a.mask),cv2.IMREAD_GRAYSCALE)
    if bgr is None or mask is None:raise ValueError('Cannot read image/mask')
    gains=estimate_neutral_gains(cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB),mask>0,a.max_gain)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps({'method':'neutral_balance','neutral_gain_rgb':gains,'neutral_max_gain':a.max_gain},indent=2)+'\n')
    a.output.with_suffix('.provenance.json').write_text(json.dumps({'note':'User-labelled neutral region; no automatic verification that material is neutral.','sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [a.image,a.mask]}},indent=2)+'\n')
