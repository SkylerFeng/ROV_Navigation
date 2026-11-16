"""Offline layouts / measured paths. Never used by navigation."""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
ROOT=Path(__file__).resolve().parents[1]
def plot(output,runs=None,retry=None):
    cases=json.loads((ROOT/'config/semantic/complex_scenes.json').read_text())
    boundary=np.array(json.loads((ROOT/'config/platform_water_boundary.json').read_text()))
    regions=json.loads((ROOT/'config/semantic/search_regions.json').read_text())
    fig,axes=plt.subplots(3,1,figsize=(14,14),sharex=True,sharey=True)
    for ax,case in zip(axes,cases):
        ax.plot(*np.vstack([boundary,boundary[0]]).T,color='gray');ax.scatter(-2,0,c='black',marker='x',label='Start')
        r=regions[case['search_region']];ax.add_patch(Rectangle(r[:2],r[2]-r[0],r[3]-r[1],fill=False,ls='--',ec='orange',label='Coarse hint'))
        for o in case['obstacles']:
            p=np.array(o['position'][:2]);size=np.array(o['size'][:2]);ax.add_patch(Rectangle(p-size/2,*size,color='#606a72'))
        for name,kind,color,pos,yaw in case['objects']:
            ax.scatter(*pos[:2],c={'yellow':'gold','red':'red','blue':'blue'}[color],s=75,marker='s' if kind=='box' else 'o',edgecolor='black')
            ax.annotate(name,pos[:2],xytext=(4,5),textcoords='offset points',fontsize=8)
        result=runs/case['name']/'semantic/result.json' if runs else None
        if retry and (retry/case['name']/'semantic/result.json').exists():result=retry/case['name']/'semantic/result.json'
        title=case['name']+' (offline layout)'
        if result and result.exists():
            data=json.loads(result.read_text());path=np.array(data['path'])
            if len(path):ax.plot(path[:,1],path[:,2],label='Measured trajectory',color='#009688');ax.scatter(*path[-1,1:3],marker='*',s=100,c='#009688')
            title=case['name']+' / '+data['status']+' / '+str(round(data['simulation_seconds'],1))+' s'
        ax.set(title=title,ylabel='World Y (m)',aspect='equal');ax.grid(alpha=.2);ax.legend(loc='lower right')
    axes[-1].set_xlabel('World X (m)');fig.tight_layout();output.mkdir(parents=True,exist_ok=True)
    fig.savefig(output/'complex_scenes.png',dpi=150);fig.savefig(output/'complex_scenes.pdf');plt.close(fig)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--runs',type=Path);p.add_argument('--retry',type=Path);a=p.parse_args();plot(a.output,a.runs,a.retry)
