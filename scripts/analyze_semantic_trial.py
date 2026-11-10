"""Offline truth audit and trajectory plot. Never imported by runtime policy."""
import argparse,json,math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
def analyze(directory,output):
    required=['semantic/result.json','semantic/map.npz','semantic/events.jsonl','manifest.json','sim/run.json']
    missing=[name for name in required if not (directory/name).is_file()]
    if missing:
        raise ValueError('Incomplete trial: '+str(directory.resolve())+'; missing '+', '.join(missing)+
                         '. Wait for the trial to finish and its processes to exit normally. '
                         'If Isaac has closed, stop the matching semantic node gracefully so it can save interrupted results. '
                         'Check semantic.log and simulation.log; do not treat this as a successful trial.')
    semantic=json.loads((directory/'semantic/result.json').read_text())
    runfile=directory/'sim/run.json';run=json.loads(runfile.read_text()) if runfile.exists() else {}
    events=[json.loads(l) for l in (directory/'semantic/events.jsonl').read_text().splitlines()]
    manifest=json.loads((directory/'manifest.json').read_text());scene=Path(manifest['scene']).stem
    task_file=directory/'config/task.json'
    task=json.loads(task_file.read_text()) if task_file.exists() else next(e['task'] for e in events if e['event']=='start')
    truth_file=ROOT/'scenes'/(scene+'.truth.json')
    truth=json.loads((truth_file if truth_file.exists() else ROOT/'config/semantic/evaluation_scene.json').read_text())['objects']
    targets=[o for o in truth if o['category']==task['category'] and o['color']==task['color']]
    if len(targets)!=1:raise ValueError('Offline audit needs one uniquely labelled target')
    target=targets[0].copy()
    if not truth_file.exists() and target['id']=='YellowPipe':
        if scene.endswith('occluded'):target['position']=[1.2,-1.6,1.12]
        if scene.endswith('relocated'):target['position']=[-3.6,-1.4,1.12]
        if scene.endswith('screened'):target['position']=[-4.35,.25,1.12]
    def local_delta(point):
        delta=np.asarray(point)-target['position'];angle=math.radians(target.get('yaw',0))
        c,s=math.cos(angle),math.sin(angle)
        return np.array([c*delta[0]+s*delta[1],-s*delta[0]+c*delta[1],delta[2]])
    def surface_error(point):
        p=local_delta(point)
        if target['category']=='box':
            q=np.abs(p)-.19
            return abs(float(np.linalg.norm(np.maximum(q,0))+min(max(q),0)))
        r=math.hypot(p[1],p[2])
        if abs(p[0])<=.325:return min(abs(r-.13),abs(r-.09),math.hypot(.325-abs(p[0]),max(.09-r,0,r-.13)))
        return math.hypot(abs(p[0])-.325,max(.09-r,0,r-.13))
    points=np.asarray(semantic['path']);trajectory=points[:,1:4] if len(points) else np.empty((0,3))
    clock_valid=bool(semantic['simulation_seconds']>=0 and (not len(points) or np.all(np.diff(points[:,0])>=0)))
    errors=[]
    for event in events:
        for d in event.get('detections',[]):
            if d['color']!=task['color'] or d['category']!=task['category']:continue
            err=surface_error(d['surface_world'])
            errors.append(err)
    decisions=[{'sim_time':e['sim_time'],**e['action']} for e in events if e['event']=='decision']
    initial=next((e for e in events if e['event']=='initial_observation'),{})
    target_initially_detected=any(d['category']==task['category'] and d['color']==task['color'] for d in initial.get('detections',[]))
    result={
        'target':target,'instruction':task['instruction'],'policy':semantic['policy'],'scene':scene,'runtime_status':semantic['status'],'reason':semantic['reason'],
        'simulation_seconds':semantic['simulation_seconds'],'frames':semantic['frames'],
        'path_length_m':float(np.linalg.norm(np.diff(trajectory,axis=0),axis=1).sum()) if len(points) else None,
        'actual_ego_updates':run.get('plan_updates'),'contact_pairs':len(run.get('contacts',[])),
        'contact_min_separation_m':min((c['min_separation_m'] for c in run.get('contacts',[]) if 'min_separation_m' in c),default=None),
        'max_contact_impulse_norm':max((c.get('max_impulse_norm',0) for c in run.get('contacts',[])),default=0),
        'physics_mode':run.get('physics_mode'),'component_model_file':run.get('config',{}).get('hydrodynamics',{}).get('component_model_file'),
        'target_initially_detected':target_initially_detected,'actions':decisions,
        'target_surface_error_median_m':float(np.median(errors)) if errors else None,
        'target_surface_error_p95_m':float(np.percentile(errors,95)) if errors else None,
        'llm_calls':semantic['llm_calls'],'evidence_directory':str(directory),
        'recorded_clock_valid':clock_valid,
        'limitations':['single trial per scene; not a success-rate estimate','ideal range and true camera/robot pose','visible-surface centroid, not complete object reconstruction','fixture ground truth used offline only','horizontal surface distance is distance to rotated projected footprint; not optical range']}
    if len(trajectory):
        delta=local_delta(trajectory[-1]);result['final_target_center_distance_xy_m']=float(np.linalg.norm(delta[:2]))
        result['final_target_surface_distance_xy_m']=float(np.linalg.norm(np.maximum(np.abs(delta[:2])-.19,0))) if target['category']=='box' else float(np.linalg.norm(np.maximum(np.abs(delta[:2])-[.325,.13],0)))
    if not clock_valid:
        result['limitations'].append('Recorded simulation clock reset or invalid duration; do not use duration as a valid task-time metric.')
    result['offline_verified']=bool(clock_valid and result['runtime_status']=='SUCCEEDED' and result['contact_pairs']==0 and max(0,task['surface_standoff_m']-.25)<=result.get('final_target_surface_distance_xy_m',99)<task['surface_standoff_m']+.5 and result.get('target_surface_error_median_m',99)<.2)
    result['exploration_verified']=bool(result['offline_verified'] and not target_initially_detected)
    contacts=run.get('contacts',[])
    result['contact_evidence']=('no_reports' if not contacts else
        'positive_separation_zero_impulse_only' if all(c.get('min_separation_m',-1)>0 and c.get('max_impulse_norm',0)==0 for c in contacts) else
        'penetration_or_impulse_recorded' if any(c.get('min_separation_m',1)<0 or c.get('max_impulse_norm',0)>0 for c in contacts) else
        'insufficient_separation_evidence')
    output.mkdir(parents=True,exist_ok=True);(output/'audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    fig,ax=plt.subplots(figsize=(9,6));boundary=np.asarray(json.loads((ROOT/'config/platform_water_boundary.json').read_text()));ax.plot(*np.vstack([boundary,boundary[0]]).T,color='gray',label='Water boundary')
    mp=np.load(directory/'semantic/map.npz');origin=mp['origin'];res=float(mp['res'])
    for field,color,label in [('free','#cce8f0','Observed free'),('occupied','#666666','Observed occupied')]:
        cells=np.argwhere(mp[field]);xy=origin+(cells+.5)*res
        ax.scatter(xy[:,0],xy[:,1],s=5,c=color,marker='s',label=label)
    if 'inspected' in mp.files:
        cells=np.argwhere(mp['inspected'] & mp['free']);xy=origin+(cells+.5)*res
        ax.scatter(xy[:,0],xy[:,1],s=5,c='#8ccfa7',marker='s',label='Near-range visual coverage')
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
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    try:analyze(a.directory,a.output)
    except (ValueError,FileNotFoundError) as exc:p.exit(2,str(exc)+'\n')
