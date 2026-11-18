"""OFFLINE known-layout feasibility audit; never imported by runtime navigation.
Includes the pool collision prior that the older layout sanity check omitted.
Fixture boxes/cylinders use conservative XY rectangles; not a PhysX proof.
"""
import argparse,json,math
from pathlib import Path
import numpy as np
from semantic_core import ExplorationGrid
from static_collision_prior import seed_grid

def audit(output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    boundary=json.loads(Path('config/platform_water_boundary.json').read_text())
    cases=json.loads(Path('config/semantic/complex_scenes.json').read_text())
    prior=np.load('config/maps/platform_static_collision_005.npz')['xy']
    fig,axes=plt.subplots(1,3,figsize=(15,5));rows=[]
    for case,ax in zip(cases,axes):
        g=ExplorationGrid(boundary,.05,.4,inflation_metric='euclidean');seed_grid(g,prior);g.inflation_metric='euclidean';g.free[:]=g.inside
        cells=np.indices(g.shape).reshape(2,-1).T;xy=g.origin+(cells+.5)*g.res
        for o in case['obstacles']:
            d=np.abs(xy-np.array(o['position'][:2]));g.occupied|=(d<=np.array(o['size'][:2])/2+g.res/math.sqrt(2)).all(1).reshape(g.shape)
        for name,kind,color,pos,yaw in case['objects']:
            a=math.radians(yaw);rotation=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
            local=(xy-pos[:2])@rotation;half=np.array([.19,.19]) if kind=='box' else np.array([.325,.13])
            g.occupied|=(np.abs(local)<=half+g.res/math.sqrt(2)).all(1).reshape(g.shape)
        g.free &= ~g.occupied;costs,_=g.reachable([-2,0,1]);reachable=np.zeros(g.shape,bool)
        if costs:reachable[tuple(np.array(list(costs)).T)]=True
        target=next(o for o in case['objects'] if o[0]=={'west_baffles':'YellowPipe','east_equipment':'BluePipe','wrong_hint_box':'YellowBox'}[case['name']])
        a=math.radians(target[4]);rotation=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
        delta=(xy-target[3][:2])@rotation;half=np.array([.19,.19]) if target[1]=='box' else np.array([.325,.13])
        distances=np.linalg.norm(np.maximum(np.abs(delta)-half,0),axis=1).reshape(g.shape)
        ring=(distances>=1)&(distances<=1.28)&reachable
        rows.append({'case':case['name'],'known_map_all_free_assumed':True,'radius_m':.4,'resolution_m':.05,
            'reachable_standoff_ring_cells':int(ring.sum()),'nearest_reachable_target_surface_m':float(distances[reachable].min()),
            'limitations':'Offline conservative fixture XY rectangles and pool collider raster. Not runtime observations; no orientation-dependent footprint; not a proof of physical impossibility.'})
        ax.scatter(xy[g.occupied.ravel(),0],xy[g.occupied.ravel(),1],s=1,c='#555555')
        ax.scatter(xy[reachable.ravel(),0],xy[reachable.ravel(),1],s=1,c='#bbe6ee')
        ax.scatter(xy[ring.ravel(),0],xy[ring.ravel(),1],s=3,c='green')
        ax.scatter([-2],[0],c='green',s=40);ax.scatter([target[3][0]],[target[3][1]],marker='*',c='gold',edgecolors='black',s=130)
        ax.set(xlim=(-7,7),ylim=(-4,3),aspect='equal',title=case['name']+'\nreachable standoff cells: '+str(int(ring.sum())),xlabel='World X (m)',ylabel='World Y (m)')
    output.mkdir(parents=True,exist_ok=True);fig.tight_layout();fig.savefig(output/'geometry.png',dpi=180);plt.close(fig)
    (output/'geometry.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();audit(a.output)
