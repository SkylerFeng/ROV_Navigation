"""Offline truth audit and trajectory plot. Never imported by runtime policy."""
import argparse,json,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
def analyze(directory,output):
    semantic=json.loads((directory/'semantic/result.json').read_text())
    runfile=directory/'sim/run.json';run=json.loads(runfile.read_text()) if runfile.exists() else {}
    events=[json.loads(l) for l in (directory/'semantic/events.jsonl').read_text().splitlines()]
    manifest=json.loads((directory/'manifest.json').read_text());scene=Path(manifest['scene']).stem
    truth=json.loads((ROOT/'config/semantic/evaluation_scene.json').read_text())['objects']
    target=next(o for o in truth if o['id']=='YellowPipe').copy()
    if scene.endswith('occluded'):target['position']=[1.2,-1.6,1.12]
    if scene.endswith('relocated'):target['position']=[-3.6,-1.4,1.12]
    if scene.endswith('screened'):target['position']=[-4.35,.25,1.12]
    points=np.asarray(semantic['path']);trajectory=points[:,1:4] if len(points) else np.empty((0,3))
    errors=[]
    for event in events:
        for d in event.get('detections',[]):
            if d['color']!='yellow' or d['category']!='pipe':continue
            # Distance to ideal hollow cylinder visible surface, ignoring end-ring thickness.
            p=np.asarray(d['surface_world'])-target['position'];r=math.hypot(p[1],p[2])
            if abs(p[0])<=.325:err=abs(r-.13)
            else:err=math.hypot(abs(p[0])-.325,max(.09-r,0,r-.13))
            errors.append(err)
    decisions=[{'sim_time':e['sim_time'],**e['action']} for e in events if e['event']=='decision']
    initial=next((e for e in events if e['event']=='initial_observation'),{})
    target_initially_detected=any(d['category']=='pipe' and d['color']=='yellow' for d in initial.get('detections',[]))
    result={
        'policy':semantic['policy'],'scene':scene,'runtime_status':semantic['status'],'reason':semantic['reason'],
        'simulation_seconds':semantic['simulation_seconds'],'frames':semantic['frames'],
        'path_length_m':float(np.linalg.norm(np.diff(trajectory,axis=0),axis=1).sum()) if len(points) else None,
        'actual_ego_updates':run.get('plan_updates'),'contact_pairs':len(run.get('contacts',[])),
        'physics_mode':run.get('physics_mode'),'component_model_file':run.get('config',{}).get('hydrodynamics',{}).get('component_model_file'),
        'target_initially_detected':target_initially_detected,'actions':decisions,
        'target_surface_error_median_m':float(np.median(errors)) if errors else None,
        'target_surface_error_p95_m':float(np.percentile(errors,95)) if errors else None,
        'llm_calls':semantic['llm_calls'],'evidence_directory':str(directory),
        'limitations':['single trial per scene; not a success-rate estimate','ideal range and true camera/robot pose','visible-surface centroid, not complete object reconstruction','fixture ground truth used offline only']}
    if len(trajectory):
        delta=trajectory[-1]-target['position'];result['final_target_center_distance_xy_m']=float(np.linalg.norm(delta[:2]))
        result['final_target_surface_distance_xy_m']=float(math.hypot(max(abs(delta[0])-.325,0),delta[1])-.13)
    result['offline_verified']=bool(result['runtime_status']=='SUCCEEDED' and result['contact_pairs']==0 and not target_initially_detected and result.get('final_target_surface_distance_xy_m',99)<1.3 and result.get('target_surface_error_median_m',99)<.2)
    output.mkdir(parents=True,exist_ok=True);(output/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    fig,ax=plt.subplots(figsize=(9,6));boundary=np.asarray(json.loads((ROOT/'config/platform_water_boundary.json').read_text()));ax.plot(*np.vstack([boundary,boundary[0]]).T,color='gray',label='Water boundary')
    mp=np.load(directory/'semantic/map.npz');origin=mp['origin'];res=float(mp['res'])
    for field,color,label in [('free','#cce8f0','Observed free'),('occupied','#666666','Observed occupied')]:
        cells=np.argwhere(mp[field]);xy=origin+(cells+.5)*res
        ax.scatter(xy[:,0],xy[:,1],s=5,c=color,marker='s',label=label)
    if len(trajectory):
        ax.plot(trajectory[:,0],trajectory[:,1],color='#0068b5',lw=2,label='Measured ROV path')
        ax.scatter(*trajectory[0,:2],marker='o',c='green',s=50,label='Start')
        ax.scatter(*trajectory[-1,:2],marker='x',c='red',s=60,label='Finish')
    ax.scatter(*target['position'][:2],marker='*',s=170,c='#e5b700',edgecolor='black',label='Target (offline truth)')
    ax.set_aspect('equal');ax.set_xlabel('World X (m)');ax.set_ylabel('World Y (m)');ax.set_title(scene+' / '+result['runtime_status']);ax.legend(fontsize=8,loc='best');fig.tight_layout();fig.savefig(output/'trajectory.png',dpi=180);plt.close(fig)
    import shutil
    for filename in ['latest_detection.jpg']:
        if (directory/'semantic'/filename).exists():shutil.copy2(directory/'semantic'/filename,output/filename)
    print(json.dumps(result,ensure_ascii=False,indent=2));return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();analyze(a.directory,a.output)
