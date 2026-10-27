"""Explain the recorded gates/slalom failures using measured motion and map data."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from experiment import ROOT

OUT=ROOT/'docs/figures/freeze_diagnosis';OUT.mkdir(parents=True,exist_ok=True)
CASES={'gates':ROOT/'logs/scenario_tests/recheck_20261014_gui/gates',
       'slalom':ROOT/'logs/scenario_tests/recheck_20261014_diagnostic/slalom'}
fig,axes=plt.subplots(3,2,figsize=(15,11),sharex=True)
source=[]
for col,(name,directory) in enumerate(CASES.items()):
    r=json.loads((directory/'run.json').read_text());controls=json.loads((directory/'controls.json').read_text());samples=np.array(r['samples'])
    t=np.array([c['t'] for c in controls]);v=np.array([c['velocity'] for c in controls]);cmd=np.array([c['desired_velocity'] for c in controls]);q=np.array([c['orientation'] for c in controls]);w,x,y,z=q.T
    yaw=np.arctan2(2*(w*z+x*y),1-2*(y*y+z*z));heading=np.arctan2(cmd[:,1],cmd[:,0]);error=np.degrees(abs(np.arctan2(np.sin(heading-yaw),np.cos(heading-yaw))));error[np.linalg.norm(cmd[:,:2],axis=1)<.03]=np.nan
    axes[0,col].plot(t,np.linalg.norm(cmd[:,:2],axis=1),label='Commanded XY speed');axes[0,col].plot(t,np.linalg.norm(v[:,:2],axis=1),label='Measured XY speed');axes[0,col].set_ylabel('Speed (m/s)');axes[0,col].set_title(name)
    axes[1,col].plot(t,error,color='#b55835',label='Command direction vs actual yaw');axes[1,col].axhline(53.03184/2,color='gray',ls='--',label='Camera half FOV: 26.5 deg');axes[1,col].set_ylabel('Absolute heading mismatch (deg)')
    plans=json.loads((directory/'plans.json').read_text());pt=np.array([p['start_time'] for p in plans]);p0=np.array([p['points'][0] for p in plans]);actual=np.column_stack([np.interp(pt,samples[:,0],samples[:,i]) for i in [1,2,3]]);gap=np.linalg.norm(p0-actual,axis=1)
    axes[2,col].plot(pt,gap,'o-',ms=3,color='#5555aa',label='New plan start vs measured pose');axes[2,col].set_ylabel('Plan start discrepancy (m)');axes[2,col].set_xlabel('Simulation time (s)')
    for contact in r['contacts']:
        first=contact.get('first_impulse_time')
        if first is not None:
            for ax in axes[:,col]:ax.axvline(first,color='#bc1515',ls=':',alpha=.7)
    for ax in axes[:,col]:ax.set_xlim(0,65);ax.grid(alpha=.25);ax.legend(fontsize=8)
    source.append({'scenario':name,'directory':str(directory),'first_contacts':r['contacts']})
fig.suptitle('Failure timeline: direction changes, physical contact, and nominal-state divergence\nRed dotted lines: first nonzero contact impulse for each collider pair',fontsize=14)
fig.tight_layout(rect=(0,0,1,.95));fig.savefig(OUT/'freeze_timeline.png',dpi=200);plt.close(fig)
base=ROOT/'logs/diagnostics/freeze_20261014/heading20_map_audit'
paths=list(base.glob('map_*.json'));path=max(paths,key=lambda p:json.loads(p.read_text())['t']);meta=json.loads(path.read_text());a=np.load(path.with_suffix('.npz'));xy=a['inflated_xy'];raw=a['input_xy']
fig,axes=plt.subplots(1,2,figsize=(15,7))
for ax in axes:
    ax.scatter(xy[:,0],xy[:,1],s=5,marker='s',color='#bec3c8',label='Actual inflated planner grid',rasterized=True)
    ax.scatter(raw[:,0],raw[:,1],s=10,color='tomato',label='Map input: observed occupied cells')
    ax.scatter(3.5,0,s=230,marker='*',color='blue',label='Original goal: occupied',zorder=5)
    ax.scatter(3.5,.4,s=160,marker='*',color='#009b75',label='Separate test goal: free in this map',zorder=5)
    ax.grid(alpha=.2);ax.set_aspect('equal');ax.set_xlabel('World X (m)');ax.set_ylabel('World Y (m)')
axes[0].set(xlim=(-3.65,4.35),ylim=(-2.15,3.25),title=f"Measured grid snapshot at sim {meta['t']:.1f} s")
axes[1].set(xlim=(2.7,4.3),ylim=(-.8,1),title='Goal region: 0.50 m XY inflation')
axes[0].legend(loc='lower left',fontsize=8);fig.suptitle('Why planning cannot finish: the original goal lies in occupied configuration space',fontsize=15);fig.tight_layout(rect=(0,0,1,.94));fig.savefig(OUT/'goal_occupancy.png',dpi=200);plt.close(fig)
(OUT/'sources.json').write_text(json.dumps({'timeline':source,'map_snapshot':str(path),'map_metadata':meta},indent=2))
print(OUT)

# Controlled layout comparison: same corrected controller and same requested goal.
from plot_five_routes import draw_case
geometry=json.loads((ROOT/'scenes/pool_collision_sections.json').read_text())['segments']
def draw_run(ax,directory,title):
    r=json.loads((directory/'run.json').read_text());r['pool_sections']=geometry
    points=np.vstack([np.array(r['samples'])[:,1:3],r['final_position'][:2]])
    draw_case(ax,'gates',r,points,r['stop_reason']=='goal_reached',compact=True)
    ax.set_title(f"{title}\nFinal error: {r['goal_distance']:.4f} m",fontsize=11)
    return r
root=ROOT/'logs/diagnostics/freeze_20261014'
fig,axes=plt.subplots(1,2,figsize=(16,7))
left=draw_run(axes[0],root/'free_goal_validation/gates','Original gate layout + free goal')
right=draw_run(axes[1],root/'clearance_validation/gates','Shortened north wall + same free goal')
fig.suptitle('Gate clearance comparison | goal = (3.5, 0.4, 1.0) m | same 0.50 m XY inflation',fontsize=15)
fig.tight_layout(rect=(0,0,1,.94));fig.savefig(OUT/'gate_clearance_comparison.png',dpi=220);plt.close(fig)
fig,axes=plt.subplots(1,3,figsize=(18,6))
for ax,name,directory in zip(axes,['Baseline','Slalom','gates_clearance (GUI)'],[root/'free_goal_validation/baseline',root/'free_goal_validation/slalom',root/'clearance_gui_validation/gates_clearance']):
    draw_run(ax,directory,name)
fig.suptitle('Validated executions after corrections | all use explicit goal (3.5, 0.4, 1.0) m',fontsize=16)
fig.tight_layout(rect=(0,0,1,.91));fig.savefig(OUT/'validated_routes.png',dpi=220);plt.close(fig)

water_file=root/'water_boundary_world.json'
connectivity_file=root/'water_constrained_connectivity.json'
if water_file.exists() and connectivity_file.exists():
    water=np.array(json.loads(water_file.read_text()));route=np.load(root/'inflated_grid_astar.npy')
    fig,ax=plt.subplots(figsize=(12,8))
    ax.scatter(xy[:,0],xy[:,1],s=6,marker='s',color='#c2c6ca',label='Actual inflated grid (z around 1 m)',rasterized=True)
    boundary=np.vstack([water,water[0]])
    ax.plot(boundary[:,0],boundary[:,1],color='#006c9c',lw=2.5,label='Provided water boundary')
    ax.plot(route[:,0],route[:,1],'--',color='#bf4141',lw=2,label='Search without water constraint: exits water')
    ax.scatter(-2.7,0,color='green',s=75,label='Start',zorder=5)
    ax.scatter(3.5,.4,color='#009b75',marker='*',s=200,label='Free target used for comparison',zorder=5)
    ax.set(xlim=(-5.6,5.8),ylim=(-2.6,4.8),xlabel='World X (m)',ylabel='World Y (m)',title='Original gate layout: no connected route inside water at current inflation\nWater-boundary margin: 0.40 m; both start and comparison target are free')
    ax.set_aspect('equal');ax.grid(alpha=.2);ax.legend(fontsize=10,loc='lower left');fig.tight_layout();fig.savefig(OUT/'water_constrained_connectivity.png',dpi=200);plt.close(fig)

metadata=json.loads((OUT/'sources.json').read_text())
metadata['validated_runs']=[str(root/d/'run.json') for d in ['free_goal_validation/baseline','free_goal_validation/slalom','free_goal_validation/gates','clearance_validation/gates','clearance_gui_validation/gates_clearance']]
metadata['water_connectivity']=str(root/'water_constrained_connectivity.json')
(OUT/'sources.json').write_text(json.dumps(metadata,indent=2))
