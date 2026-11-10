"""Measured motion and semantic events on one simulation clock; no cloud calls."""
import argparse
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def analyze(directory, output):
    controls=json.loads((directory/'sim/controls.json').read_text())
    result=json.loads((directory/'semantic/result.json').read_text())
    events=[json.loads(line) for line in (directory/'semantic/events.jsonl').read_text().splitlines()]
    t=np.array([c['t'] for c in controls]);dt=np.diff(t)
    if len(dt)==0 or np.any(dt<=0):raise ValueError('Need monotonic recorded simulation time')
    v=np.array([c['velocity'] for c in controls]);speed=np.linalg.norm(v,axis=1)
    q=np.array([c['orientation'] for c in controls]);w,x,y,z=q.T
    yaw=np.unwrap(np.arctan2(2*(w*z+x*y),1-2*(y*y+z*z)))
    rate=np.diff(yaw)/dt
    rotating=(speed[:-1]<.03)&(np.abs(rate)>np.radians(3))
    path=np.array(result['path'])
    metrics={'run':str(directory),'status':result['status'],'reason':result['reason'],
             'simulation_seconds':result['simulation_seconds'],
             'path_length_m':float(np.linalg.norm(np.diff(path[:,1:4],axis=0),axis=1).sum()),
             'stationary_turn_seconds':float(dt[rotating].sum()),
             'total_yaw_travel_deg':float(np.degrees(np.abs(np.diff(yaw)).sum())),
             'yaw_acceleration_p95_rad_s2':float(np.percentile(np.abs(np.diff(rate)/dt[1:]),95)),
             'llm_calls':result['llm_calls'],
             'recovery_attempts':sum(e['event']=='recovery_started' for e in events),
             'verification_failures':sum(e['event']=='verification_failed' for e in events),
             'definition':'stationary turn: measured 3D speed <0.03 m/s and yaw rate >3 deg/s; includes useful scanning/alignment, not all wasted time'}
    output.mkdir(parents=True,exist_ok=True)
    (output/'motion_metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    fig,axes=plt.subplots(3,1,figsize=(11,8),sharex=True)
    axes[0].plot(t,speed);axes[0].set_ylabel('Speed (m/s)')
    axes[1].plot(t,np.degrees(yaw));axes[1].set_ylabel('Unwrapped yaw (deg)')
    axes[2].plot(t[:-1],np.degrees(rate));axes[2].set_ylabel('Yaw rate (deg/s)')
    for e in events:
        if e['event']=='decision':
            axes[0].axvline(e['sim_time'],alpha=.3,color='gray')
            axes[0].text(e['sim_time'],.02,e['action']['action'],rotation=90,fontsize=8)
    for ax in axes:ax.grid(alpha=.2)
    axes[-1].set_xlabel('Simulation time (s)');fig.suptitle(directory.name+' / '+result['status'])
    fig.tight_layout();fig.savefig(output/'motion.png',dpi=160);plt.close(fig)
    return metrics

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(analyze(a.directory,a.output),indent=2))
