"""Offline 2D clearance/connectivity sanity check, not a PhysX collision proof."""
import json
from pathlib import Path
import numpy as np
from matplotlib.path import Path as Polygon
from scipy.ndimage import distance_transform_edt,label
ROOT=Path(__file__).resolve().parents[1]
def check():
    boundary=json.loads((ROOT/'config/platform_water_boundary.json').read_text())
    step=.05;x=np.arange(-7,8.6,step);y=np.arange(-4,3,step);xx,yy=np.meshgrid(x,y,indexing='ij');xy=np.stack([xx,yy],axis=-1)
    inside=Polygon(boundary).contains_points(xy.reshape(-1,2)).reshape(xx.shape);rows=[]
    for c in json.loads((ROOT/'config/semantic/complex_scenes.json').read_text()):
        occupied=~inside
        for o in c['obstacles']:
            occupied |= (np.abs(xy-np.array(o['position'][:2]))<=np.array(o['size'][:2])/2).all(-1)
        for name,kind,color,pos,yaw in c['objects']:
            delta=xy-np.array(pos[:2]);angle=np.deg2rad(yaw);rot=np.array([[np.cos(angle),np.sin(angle)],[-np.sin(angle),np.cos(angle)]])
            local=delta@rot.T;half=np.array([.325,.13] if kind=='pipe' else [.19,.19]);occupied|=(np.abs(local)<=half).all(-1)
        # More conservative than configured .25 m costmap: check a .4 m disk.
        safe=distance_transform_edt(~occupied)*step>.4
        labels,_=label(safe);start=(np.abs(x+2).argmin(),np.abs(y).argmin());connected=(labels==labels[start])&safe
        target_id={'west_baffles':'YellowPipe','east_equipment':'BluePipe','wrong_hint_box':'YellowBox'}[c['name']]
        obj=next(o for o in c['objects'] if o[0]==target_id)
        radius=np.linalg.norm(xy-np.array(obj[3][:2]),axis=-1);ring=(radius>1)&(radius<1.4)
        rows.append({'scene':c['name'],'start_safe':bool(safe[start]),'reachable_standoff_cells':int((ring&connected).sum()),'clearance_disk_m':.4})
    assert all(r['start_safe'] and r['reachable_standoff_cells']>0 for r in rows),rows
    return rows
if __name__=='__main__':print(json.dumps(check(),indent=2))
