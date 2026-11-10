from pathlib import Path
from PIL import Image,ImageDraw
import json,shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--input',type=Path,default=Path('logs/platform_navigation_final'))
parser.add_argument('--output',type=Path,default=Path('docs/validation/platform_navigation_20261028'))
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
src=args.input.resolve()
out=args.output.resolve()
out.mkdir(parents=True,exist_ok=True)
d=json.loads((src/'motion.json').read_text())
shutil.copy2(src/'motion.json',out/'motion.json')
frames=[]
for i,p in enumerate(sorted(src.glob('frame_*.png'))):
 im=Image.open(p).convert('RGB').resize((960,540))
 draw=ImageDraw.Draw(im)
 draw.rectangle((0,0,960,40),fill=(12,22,35))
 draw.text((12,12),f'Platform water | PhysX + buoyancy + drag + actuator lag | current 0.06 m/s | t ~ {i*.5:.1f}s',fill='white')
 frames.append(im)
frames[0].save(out/'demo.gif',save_all=True,append_images=frames[1:],duration=500,loop=0,optimize=True)
frames[len(frames)//2].save(out/'preview.png')
s=d['samples'];t=np.array([x['t'] for x in s]);p=np.array([x['position'] for x in s]);v=np.array([x['velocity'] for x in s])
fig,axs=plt.subplots(1,3,figsize=(14,4))
axs[0].plot(p[:,0],p[:,1]);w=np.array(d['waypoints']);axs[0].plot(w[:,0],w[:,1],'go',label='Waypoints');
if d.get('navigation'):
 for x,y,r in d['navigation']['obstacles']:
  axs[0].add_patch(plt.Circle((x,y),r,color='orange'))
axs[0].axis('equal');axs[0].set(xlabel='World X (m)',ylabel='World Y (m)',title='Measured PhysX trajectory');axs[0].legend()
axs[1].plot(t,p[:,2]);axs[1].axhline(-.3,color='gray',linestyle='--');axs[1].set(xlabel='Time (s)',ylabel='World Z (m)',title='Depth control')
axs[2].plot(t,np.linalg.norm(v,axis=1));axs[2].set(xlabel='Time (s)',ylabel='Speed (m/s)',title='ROV speed')
fig.tight_layout();fig.savefig(out/'result.png',dpi=140)
metrics={k:d[k] for k in ['completed','duration_s','final_error_m','max_depth_error_m','path_length_m','min_submerged_fraction','contacts']}
if 'min_obstacle_hull_clearance_m' in d: metrics['min_obstacle_hull_clearance_m']=d['min_obstacle_hull_clearance_m']
(out/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n');print(json.dumps(metrics,indent=2))
