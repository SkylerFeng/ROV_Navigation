"""Export report evidence from one recorded trial; no simulation or inference."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

def export(source, output):
    output.mkdir(parents=True, exist_ok=False)
    plt.rcParams.update({'font.family':'Noto Sans CJK JP', 'axes.unicode_minus':False,
                         'font.size':10, 'savefig.facecolor':'white'})
    inputs = ['semantic/latest_sensor.npz','semantic/latest_detection.jpg',
              'semantic/events.jsonl','semantic/result.json','semantic/map.npz',
              'sim/controls.json','sim/run.json','manifest.json']
    events=[json.loads(line) for line in (source/'semantic/events.jsonl').read_text().splitlines()]
    perceptions=[e for e in events if e['event']=='perception']
    snapshot=perceptions[-1]
    sensor=np.load(source/'semantic/latest_sensor.npz')
    result=json.loads((source/'semantic/result.json').read_text())
    run=json.loads((source/'sim/run.json').read_text())
    manifest=json.loads((source/'manifest.json').read_text())
    scene=Path(manifest['scene']).stem
    caption=scene+' | '+result['policy']+' | '+result['status']
    def save(fig, name):
        fig.savefig(output/(name+'.png'),dpi=220,bbox_inches='tight')
        fig.savefig(output/(name+'.pdf'),bbox_inches='tight')
        plt.close(fig)
    fig, axes=plt.subplots(1,3,figsize=(15,4.6),layout='constrained')
    axes[0].imshow(sensor['rgb']); axes[0].set_title('水下相机 RGB（原始保存帧）')
    depth=sensor['depth']; valid=np.isfinite(depth)&(depth>0)
    im=axes[1].imshow(np.ma.masked_where(~valid,depth),cmap='viridis',vmin=0,vmax=8)
    axes[1].set_title('沿视线距离图（仿真理想测距）')
    fig.colorbar(im,ax=axes[1],shrink=.7,label='距离 / m（显示上限 8 m）')
    axes[2].imshow(plt.imread(source/'semantic/latest_detection.jpg'))
    axes[2].set_title('检测类别、颜色与目标表面距离')
    for ax in axes: ax.set_axis_off()
    fig.suptitle('视觉观测与目标识别 | 保存记录时间 %.2f s\n%s' % (snapshot['sim_time'],caption))
    save(fig,'01_camera_and_detection')
    plt.imsave(output/'camera_rgb.png',sensor['rgb'])
    detections=snapshot.get('detections',[])
    with (output/'snapshot_detections.csv').open('w',newline='') as f:
        w=csv.writer(f); w.writerow(['record_time_s','category','color','detector_score','color_score','surface_x_m','surface_y_m','surface_z_m','camera_to_surface_range_m'])
        for d in detections:
            w.writerow([snapshot['sim_time'],d['category'],d['color'],d['detector_score'],d['color_score'],*d['surface_world'],d['range_m']])
    path=np.asarray(result['path']); decisions=[e for e in events if e['event']=='decision']
    fig,(ax,timeline)=plt.subplots(2,1,figsize=(10,8),gridspec_kw={'height_ratios':[5,1]},layout='constrained')
    mp=np.load(source/'semantic/map.npz'); origin=mp['origin']; res=float(mp['res'])
    for field,color,label in [('free','#dcecf0','已观测可通行'),('occupied','#646c72','已观测占据')]:
        cells=np.argwhere(mp[field]); xy=origin+(cells+.5)*res
        ax.scatter(xy[:,0],xy[:,1],s=20,c=color,marker='s',label=label)
    ax.plot(path[:,1],path[:,2],color='#1565c0',lw=2.5,label='实测 ROV 轨迹')
    ax.scatter(*path[0,1:3],c='#228b22',s=75,label='起点',zorder=5)
    ax.scatter(*path[-1,1:3],c='#c62828',marker='X',s=80,label='终点',zorder=5)
    targets=[d for d in detections if d['category']=='pipe' and d['color']=='yellow']
    ext=path[:,1:3]
    if targets:
        target=np.asarray(targets[0]['surface_world'])[:2]; ext=np.vstack([ext,target])
        ax.scatter(*target,c='#efba00',edgecolor='black',marker='*',s=180,label='最终视觉估计表面点',zorder=6)
    names={'scan':'扫描','explore':'探索','approach':'接近','hold':'等待','report':'报告'}
    colors={'scan':'#7593b9','explore':'#2e9c91','approach':'#e7a339','hold':'#999999','report':'#c44e52'}
    end=float(path[-1,0])
    for i,e in enumerate(decisions):
        t=e['sim_time']; action=e['action']['action']; j=np.abs(path[:,0]-t).argmin()
        ax.annotate(str(i+1),path[j,1:3],xytext=(5,7+10*(i%2)),textcoords='offset points',weight='bold')
        stop=decisions[i+1]['sim_time'] if i+1<len(decisions) else end
        timeline.broken_barh([(t,max(0,stop-t))],(0,1),facecolors=colors.get(action,'gray'))
        timeline.text((t+stop)/2,.5,str(i+1)+' '+names.get(action,action),ha='center',va='center',fontsize=8)
    ax.set_xlim(ext[:,0].min()-1.2,ext[:,0].max()+1.2); ax.set_ylim(ext[:,1].min()-1,ext[:,1].max()+1)
    ax.set_aspect('equal'); ax.set_xlabel('世界 X / m');ax.set_ylabel('世界 Y / m');ax.legend(fontsize=8,loc='best')
    ax.set_title('实测轨迹与最终观测地图（局部放大）\n'+caption)
    timeline.set_xlim(0,end);timeline.set_ylim(0,1);timeline.set_yticks([]);timeline.set_xlabel('仿真时间 / s；色段表示决策发出至下一次决策，不等同运动状态')
    save(fig,'02_trajectory_and_decisions')
    np.savetxt(output/'measured_trajectory.csv',path,delimiter=',',header='sensor_time_s,world_x_m,world_y_m,world_z_m',comments='')
    controls=json.loads((source/'sim/controls.json').read_text()); t=np.array([c['t'] for c in controls])
    q=np.array([c['orientation'] for c in controls]);q=q/np.linalg.norm(q,axis=1)[:,None]; w,x,y,z=q.T
    roll=np.degrees(np.arctan2(2*(w*x+y*z),1-2*(x*x+y*y)))
    pitch=np.degrees(np.arcsin(np.clip(2*(w*y-z*x),-1,1)))
    vel=np.array([c['velocity'] for c in controls]); desired=np.array([c['desired_velocity'] for c in controls])
    drag=np.array([c['hydrodynamics']['drag_body_n'] for c in controls])
    torque=np.array([c['hydrodynamics']['drag_torque_body_nm'] for c in controls])
    fig,axes=plt.subplots(2,2,figsize=(12,7),layout='constrained')
    axes[0,0].plot(t,np.linalg.norm(desired[:,:2],axis=1),'--',label='指令水平速度')
    axes[0,0].plot(t,np.linalg.norm(vel[:,:2],axis=1),label='实测水平速度');axes[0,0].set_ylabel('m/s')
    axes[0,1].plot(t,roll,label='横滚 Roll');axes[0,1].plot(t,pitch,label='俯仰 Pitch');axes[0,1].set_ylabel('deg')
    for i,label in enumerate(['X','Y','Z']):
        axes[1,0].plot(t,drag[:,i],label=label);axes[1,1].plot(t,torque[:,i],label=label)
    for ax,title,unit in [(axes[1,0],'模型计算的部件阻力合力（机体系）','N'),(axes[1,1],'模型计算的部件阻力合力矩（机体系）','N·m')]:
        ax.set_title(title);ax.set_ylabel(unit)
    axes[0,0].set_title('速度指令与运动响应');axes[0,1].set_title('ROV 实测姿态')
    for ax in axes.flat:ax.set_xlabel('仿真时间 / s');ax.grid(alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('水动力闭环运行记录（单次实验，非模型精度或因果对照）\n'+caption)
    save(fig,'03_motion_and_hydrodynamics')
    np.savetxt(output/'motion_and_hydrodynamics.csv',np.column_stack([t,vel,desired,roll,pitch,drag,torque]),delimiter=',',header='time_s,vx,vy,vz,cmd_vx,cmd_vy,cmd_vz,roll_deg,pitch_deg,drag_x_N,drag_y_N,drag_z_N,drag_tx_Nm,drag_ty_Nm,drag_tz_Nm',comments='')
    provenance={'source_trial':str(source.resolve()),'scene':scene,'policy':result['policy'],'status':result['status'],
                'snapshot_record_time_s':snapshot['sim_time'],'simulation_seconds':result['simulation_seconds'],
                'plan_updates':run['plan_updates'],'contact_pairs':len(run['contacts']),
                'sha256':{f:hashlib.sha256((source/f).read_bytes()).hexdigest() for f in inputs},
                'limitations':['Recorded before 2026-11-05 water appearance repair; do not label as repaired-scene results.',
                    'Only latest sensor snapshot is retained, not a camera sequence or video.',
                    'Range is radial distance, not optical Z-depth; ideal simulated range and true camera pose.',
                    'Snapshot time is perception event record time, not a saved image acquisition timestamp.',
                    'Rule policy; no cloud LLM inference. One trial, not success rate.',
                    'Force and torque are model-computed; not measured experimental ground truth.']}
    (output/'sources.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2))
    print(json.dumps({k:v for k,v in provenance.items() if k!='sha256'},ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();export(a.source,a.output)
