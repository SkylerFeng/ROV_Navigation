"""Offline comparison of recorded paths; never supplies truth to navigation."""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT=Path(__file__).resolve().parents[1]

def plot(before,after,output):
    cases=json.loads((ROOT/'config/semantic/complex_scenes.json').read_text())
    boundary=np.asarray(json.loads((ROOT/'config/platform_water_boundary.json').read_text()))
    fig,axes=plt.subplots(3,1,figsize=(13,12),sharex=True,sharey=True)
    rows=[]
    for ax,case in zip(axes,cases):
        name=case['name'];ax.plot(*np.vstack([boundary,boundary[0]]).T,color='#555555',lw=1)
        for obstacle in case['obstacles']:
            size=np.asarray(obstacle['size'][:2]);pos=np.asarray(obstacle['position'][:2])
            ax.add_patch(Rectangle(pos-size/2,*size,color='#68737d',alpha=.8))
        for obj_name,kind,color,pos,yaw in case['objects']:
            ax.scatter(*pos[:2],c={'yellow':'gold','blue':'royalblue','red':'tomato'}[color],
                marker='s' if kind=='box' else 'o',s=65,edgecolors='black',zorder=5)
            ax.annotate(obj_name,pos[:2],xytext=(5,5),textcoords='offset points',fontsize=8)
        row={'case':name}
        for label,directory,color,style in [('v9',before,'#cf593c','--'),('v13',after,'#008f8b','-')]:
            run=directory/name;result=json.loads((run/'semantic/result.json').read_text())
            path=np.asarray(result['path']);audit=json.loads((run/'audit.json').read_text())
            ax.plot(path[:,1],path[:,2],color=color,ls=style,lw=1.8,
                label=f"{label}: {result['status']}, {result['simulation_seconds']:.1f}s, {audit['path_length_m']:.2f}m")
            ax.scatter(*path[-1,1:3],marker='x',s=65,color=color,zorder=6)
            row[label]={k:audit.get(k) for k in ('runtime_status','simulation_seconds','path_length_m','contact_pairs','offline_verified')}
        rows.append(row)
        ax.set(title=name,ylabel='World Y (m)',aspect='equal',xlim=(-7,7.5),ylim=(-3.7,2.8))
        ax.grid(alpha=.15);ax.legend(fontsize=8,loc='lower right')
    axes[-1].set_xlabel('World X (m)')
    fig.suptitle('Recorded navigation paths: original layouts and hydrodynamics retained',fontsize=13)
    fig.tight_layout();output.mkdir(parents=True,exist_ok=True)
    fig.savefig(output/'before_after_paths.png',dpi=170);plt.close(fig)
    (output/'before_after_metrics.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True)
    p.add_argument('--after',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();plot(a.before,a.after,a.output)
