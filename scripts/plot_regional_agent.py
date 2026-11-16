"""Offline comparison: prior rectangles, actual trajectories and action timeline."""
import argparse,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

def plot(root,output):
    cases=['no_hint','correct_hint','incorrect_hint']
    fig,axes=plt.subplots(2,3,figsize=(16,9),sharex='row',sharey='row')
    summary=[]
    for col,name in enumerate(cases):
        d=root/name
        result=json.loads((d/'semantic/result.json').read_text())
        cfg=json.loads((d/'config/agent.json').read_text())
        events=[json.loads(l) for l in (d/'semantic/events.jsonl').read_text().splitlines()]
        points=np.asarray(result['path'])
        ax=axes[0,col];ax.plot(points[:,1],points[:,2],label='Measured ROV path');ax.scatter(*points[0,1:3],marker='o',label='Start');ax.scatter(*points[-1,1:3],marker='x',label='Finish')
        audit_path=output/name/'audit.json'
        if audit_path.exists():
            target=json.loads(audit_path.read_text())['target']['position']
            ax.scatter(*target[:2],marker='*',s=100,c='goldenrod',label='Target (offline truth)')
        r=cfg['coarse_region_xyxy']
        if r:ax.add_patch(Rectangle(r[:2],r[2]-r[0],r[3]-r[1],fill=False,color='orange',ls='--',label='Initial hint (not target)'))
        mp=np.load(d/'semantic/map.npz');cells=np.argwhere(mp['occupied']);xy=mp['origin']+(cells+.5)*float(mp['res'])
        if len(xy):ax.scatter(xy[:,0],xy[:,1],s=2,c='gray',alpha=.4,label='Observed occupied')
        ax.set_aspect('equal');ax.set(xlabel='World X (m)',ylabel='World Y (m)',title=name);ax.legend(fontsize=7);ax.grid(alpha=.2)
        ax=axes[1,col]
        tools=[e for e in events if e['event']=='agent_tool_result']
        for i,e in enumerate(tools):
            ax.barh(i,e['duration_s'],left=e['started_s'],color={'scan':'#cca53d','explore':'#398cbf','approach':'#4ba66d'}.get(e['action'],'gray'))
        ax.set_yticks(range(len(tools)),[e['action']+' / '+e['status'] for e in tools],fontsize=7)
        expansions=[e for e in events if e['event']=='agent_search_expanded']
        for e in expansions:ax.axvline(e['sim_time'],c='red',ls=':',alpha=.7)
        ax.set(xlabel='Simulation time (s)',title='Action feedback; dotted lines = hint expansion');ax.grid(axis='x',alpha=.2)
        summary.append({'case':name,'status':result['status'],'simulation_seconds':result['simulation_seconds'],
                        'path_length_m':float(np.linalg.norm(np.diff(points[:,1:4],axis=0),axis=1).sum()),
                        'expansion_events':expansions,'local_refinements':sum(e['event']=='target_local_refinement' for e in events)})
    output.mkdir(parents=True,exist_ok=True);fig.tight_layout();fig.savefig(output/'comparison.png',dpi=160);fig.savefig(output/'comparison.pdf');plt.close(fig)
    (output/'comparison.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();plot(a.root,a.output)
