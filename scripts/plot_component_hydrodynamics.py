"""Local evidence and figures for mesh-component hydrodynamics."""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from hydrodynamics import Hydrodynamics, rotation_matrix
from hydrodynamics_metrics import dynamics_metrics
from component_hydrodynamics import ROOT


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--probe',type=Path,required=True)
    parser.add_argument('--suite',type=Path)
    args=parser.parse_args()
    out=ROOT/'docs/figures/component_hydrodynamics_20261102';out.mkdir(parents=True,exist_ok=True)
    evidence=ROOT/'docs/validation/component_hydrodynamics_20261102';evidence.mkdir(parents=True,exist_ok=True)
    config=json.loads((ROOT/'config/experiments/hydro_components.json').read_text())['hydrodynamics']
    h=Hydrodynamics(config,2,-5,[[-10,-10],[10,-10],[10,10],[-10,10]])
    geometry=json.loads(h.components.path.read_text());probe=json.loads(args.probe.read_text())
    fig,axes=plt.subplots(1,3,figsize=(15,4.5))
    centers=h.components.centers
    for ax,dims,title in zip(axes,[(0,1),(0,2),(1,2)],['XY','XZ','YZ']):
        ax.scatter(centers[:,dims[0]],centers[:,dims[1]],s=2,c=h.components.index,cmap='turbo',alpha=.5)
        ax.scatter(*np.array(h.p['center_of_mass_body_m'])[list(dims)],c='black',marker='x',s=60,label='Configured COM')
        ax.set(title=title,xlabel='Body axis (m)',ylabel='Body axis (m)',aspect='equal');ax.grid(alpha=.2)
    fig.suptitle('Actual transformed USD surface | geometric shell IDs, not semantic parts')
    fig.tight_layout();fig.savefig(out/'mesh_components.png',dpi=170);plt.close(fig)
    angles=np.linspace(-np.pi,np.pi,181);forces=[];torques=[]
    for a in angles:
        f,t,_=h.components.wrench(.3*np.array([np.cos(a),np.sin(a),0]),[0]*3)
        forces.append(f);torques.append(t)
    forces=np.array(forces);torques=np.array(torques)
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    for i,label in enumerate(['X','Y','Z']):
        axes[0].plot(np.degrees(angles),forces[:,i],label=label)
        axes[1].plot(np.degrees(angles),torques[:,i],label=label)
    for ax in axes:ax.set_xlabel('Relative translation heading (deg)');ax.grid(alpha=.2);ax.legend()
    axes[0].set_ylabel('Drag force (N)');axes[1].set_ylabel('Drag moment about COM (Nm)')
    fig.suptitle('Geometry sensitivity at 0.3 m/s | uncalibrated two-sided surface law')
    fig.tight_layout();fig.savefig(out/'directional_wrench.png',dpi=170);plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(12,8))
    for name in ['braking','coast']:
        rows=probe['cases'][name];t=np.array([r['t'] for r in rows]);v=np.array([r['velocity'] for r in rows]);pos=np.array([r['position'] for r in rows])
        axes[0,0].plot(t,v[:,0],label=name)
        axes[0,1].plot(t,pos[:,0]-pos[0,0],label=name)
    for name in ['yaw_stop','moving_turn']:
        rows=probe['cases'][name];t=[r['t'] for r in rows]
        axes[1,0].plot(t,np.degrees([r['angular_velocity'][2] for r in rows]),label=name)
        axes[1,1].plot(t,[r['nose_up_deg'] for r in rows],label=name+' pitch')
        axes[1,1].plot(t,[r['roll_deg'] for r in rows],linestyle='--',label=name+' roll')
    axes[0,0].set_ylabel('World X velocity (m/s)');axes[0,1].set_ylabel('X excursion (m)')
    axes[1,0].set_ylabel('Yaw rate (deg/s)');axes[1,1].set_ylabel('Attitude (deg)')
    for ax in axes.flat:ax.set_xlabel('Simulation time (s)');ax.grid(alpha=.2);ax.legend(fontsize=8)
    axes[1,0].axvline(6,c='gray',linestyle=':');axes[1,0].axvline(8,c='gray',linestyle=':')
    fig.suptitle('Actual PhysX | zero-flow motion probes | no pose animation')
    fig.tight_layout();fig.savefig(out/'motion_probes.png',dpi=170);plt.close(fig)
    shutil.copy2(args.probe,evidence/'physx_probe.json')
    summary=dict(geometry={k:geometry[k] for k in ['source_asset','source_mesh','source_sha256','bounds_body_m','source_triangle_count','degenerate_triangles','method','limits']},
        component_count=h.components.count,patch_count=h.components.patch_count,surface_area_m2=float(h.components.areas.sum()),
        geometry_sha256=h.components.sha256,probe_summary=probe['summary'],probe_checks=probe['checks'],navigation=[])
    if args.suite:
        for directory in sorted(args.suite.iterdir()):
            if not (directory/'run.json').exists():continue
            run=json.loads((directory/'run.json').read_text());controls=json.loads((directory/'controls.json').read_text())
            metrics=json.loads((directory/'metrics.json').read_text())
            dst=evidence/directory.name;dst.mkdir(exist_ok=True)
            for f in ['run.json','plans.json','metrics.json','manifest.json','scene_evidence.json','trajectory_updates.png','trajectory_updates.gif']:
                if (directory/f).exists():shutil.copy2(directory/f,dst/f)
            (dst/'controls_sampled.json').write_text(json.dumps(controls))
            summary['navigation'].append(metrics)
            a=np.array(run['samples']);rot=np.array([rotation_matrix(r['orientation']) for r in controls])
            fig,axes=plt.subplots(1,3,figsize=(15,4))
            from matplotlib.patches import Rectangle,Circle
            for ob in run['config']['obstacles']:
                x,y=ob['position'][:2];sx,sy=ob['size'][:2]
                axes[0].add_patch(Circle((x,y),sx/2,color='coral') if ob.get('type')=='cylinder' else Rectangle((x-sx/2,y-sy/2),sx,sy,color='coral'))
            axes[0].plot(a[:,1],a[:,2],label='Actual path');axes[0].scatter(*run['config']['goal'][:2],marker='*',c='green');axes[0].axis('equal')
            t=[r['t'] for r in controls]
            axes[1].plot(t,np.degrees(np.arcsin(np.clip(rot[:,2,0],-1,1))),label='Nose-up')
            axes[1].plot(t,np.degrees(np.arctan2(rot[:,2,1],rot[:,2,2])),label='Roll')
            axes[2].plot(t,np.linalg.norm([r['velocity'] for r in controls],axis=1),label='Actual')
            axes[2].plot(t,np.linalg.norm([r['desired_velocity'] for r in controls],axis=1),alpha=.5,label='Requested')
            axes[0].set(xlabel='World X (m)',ylabel='World Y (m)');axes[1].set(xlabel='Time (s)',ylabel='Attitude (deg)');axes[2].set(xlabel='Time (s)',ylabel='Speed (m/s)')
            for ax in axes:ax.grid(alpha=.2);ax.legend()
            fig.suptitle(directory.name+' | mesh-component drag | '+('reached' if metrics['goal_reached'] else 'not_reached')+' | error %.3f m'%metrics['goal_error_m'])
            fig.tight_layout();fig.savefig(out/(directory.name+'.png'),dpi=170);plt.close(fig)
    files=['scripts/hydrodynamics.py','scripts/component_hydrodynamics.py','scripts/export_hydrodynamic_components.py','scripts/probe_component_hydrodynamics.py','scripts/run_suite.py','config/experiments/hydro_components.json']
    summary['source_sha256']={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    (evidence/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps({k:summary[k] for k in ['component_count','patch_count','probe_checks','navigation']},indent=2))


if __name__=='__main__':main()
