"""Live read-only ROS debug window. No API calls, commands, or simulator truth."""
import argparse,json,time,textwrap
from pathlib import Path
import numpy as np

def configure_fonts():
    """Use an installed CJK font so Chinese task text is not missing glyphs."""
    import matplotlib
    from matplotlib import font_manager
    preferred=('Noto Sans CJK SC','Noto Sans CJK JP','WenQuanYi Micro Hei','Droid Sans Fallback')
    available={f.name for f in font_manager.fontManager.ttflist}
    chosen=next((name for name in preferred if name in available),None)
    if chosen:matplotlib.rcParams['font.sans-serif']=[chosen,'DejaVu Sans']
    matplotlib.rcParams['axes.unicode_minus']=False
    return chosen

def draw(fig,state):
    from matplotlib.colors import ListedColormap
    fig.clear()
    layout=fig.add_gridspec(2,3,width_ratios=[1.15,1.,1.25])
    ax=fig.add_subplot(layout[:,0]);raw_ax=fig.add_subplot(layout[0,1]);det_ax=fig.add_subplot(layout[1,1])
    panel=fig.add_subplot(layout[:,2]);panel.axis('off')
    for image_ax in (raw_ax,det_ax):image_ax.axis('off')
    raw_ax.set_title('Camera RGB / 相机原图');det_ax.set_title('YOLO / 检测结果')
    data=state.get('debug')
    if not data:
        panel.text(0,1,'Waiting for /rov/semantic/debug\nStart a NEW trial using the updated code.',va='top')
        return
    camera=data.get('camera')
    rgb=state.get('camera_rgb')
    if camera and rgb is not None:
        from matplotlib.patches import Rectangle
        raw_ax.imshow(rgb);det_ax.imshow(rgb)
        camera_age=data['sim_time']-camera['sim_time']
        wall_age=time.monotonic()-state.get('received',time.monotonic())
        stale=camera_age>1. or camera_age<-.05 or wall_age>3.
        caption=f"Frame {camera['sim_time']:.2f}s | lag {camera_age:.2f}s"+(' | STALE' if stale else '')
        raw_ax.set_title('Camera RGB / 相机原图\n'+caption,fontsize=10)
        det_ax.set_title(f"YOLO: {len(camera['detections'])} detections / 同帧检测",fontsize=10)
        for d in camera['detections']:
            x0,y0,x1,y1=d['bbox'];color='lime' if d['localized'] else 'orange'
            det_ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,edgecolor=color,linewidth=1.5))
            label=f"{d.get('color','?')} {d['category']} {d['confidence']:.2f}"
            label+=f" {d['range_m']:.2f}m" if d['localized'] else ' | no localization'
            det_ax.text(max(0,x0),max(10,y0-3),label,fontsize=7,color=color,
                        bbox={'facecolor':'black','alpha':.65,'pad':1})
        det_ax.text(0,-.10,'Green: localized; orange: detector-only.\nColor/range are from localization, not YOLO; boxes are not confirmed tracks.',
                    transform=det_ax.transAxes,fontsize=8)
    else:
        message='Waiting for same-frame camera + detections\nRestart navigation after this update.'
        if data.get('camera_error'):message='Camera encode error: '+data['camera_error']
        if state.get('camera_decode_error'):message='Camera decode error: '+state['camera_decode_error']
        raw_ax.text(.05,.5,message,transform=raw_ax.transAxes,fontsize=9)
    g=data['grid'];cells=np.asarray(g['cells']);x,y=g['origin'];r=g['resolution']
    ax.imshow(cells.T,origin='lower',extent=[x,x+cells.shape[0]*r,y,y+cells.shape[1]*r],
              cmap=ListedColormap(['#aeb4bc','#343a40','#edf5ee','#eea760','#b52727']),vmin=0,vmax=4,interpolation='nearest')
    path=np.asarray(data['path'])
    if len(path):ax.plot(path[:,1],path[:,2],color='green',label='Executed path')
    plan=state.get('plan',[])
    if len(plan):ax.plot(*np.asarray(plan)[:,:2].T,color='cyan',label='Latest EGO plan')
    cloud=state.get('inflated',[])
    if len(cloud):ax.scatter(*np.asarray(cloud).T,s=3,c='purple',alpha=.3,label='EGO inflated slice')
    decision=data.get('decision') or {};obs=decision.get('observation',{})
    for c in obs.get('candidates',[]):
        p=c['position'];ax.scatter(p[0],p[1],marker='x',c='blue',s=22)
    for o in data['objects']:
        p=o['surface_world'];ax.scatter(p[0],p[1],s=35,facecolors='none',edgecolors='black')
        ax.annotate(o['id']+(' OK' if o['confirmed'] else ' ?'),p[:2],fontsize=7)
    if data.get('active'):
        p=data['active']['position'];ax.scatter(p[0],p[1],marker='*',c='magenta',s=130,label='Active waypoint')
    if data['position']:
        p=data['position'];a=data['yaw'];ax.arrow(p[0],p[1],.3*np.cos(a),.3*np.sin(a),width=.035,color='black')
    ax.set_aspect('equal');ax.set_xlabel('World X (m)');ax.set_ylabel('World Y (m)')
    ax.set_title('Semantic map + safety mask\n(not Nav2 costmap)',fontsize=10)
    ax.legend(loc='upper right',fontsize=7)
    age=time.monotonic()-state.get('received',time.monotonic())
    lines=[f"Telemetry age: {age:.1f}s"+('  STALE' if age>3 else ''),
           f"Sim time: {data['sim_time']:.1f}s   Policy: {data['policy']}",
           'Task / 任务: '+(data.get('instruction') or '[任务文本未收到]'),'State: '+data['state'],'Reason: '+data['reason'],
           'Planner: '+data['planner_state'],'Tracker: '+str(state.get('tracker',{}).get('mode','waiting')),
           '', 'Last accepted decision at '+str(decision.get('sim_time','-'))+' s:',
           json.dumps(decision.get('action',{}),ensure_ascii=False),
           '', 'Blue crosses: candidates at last decision (NOT live)',
           'Circles: estimated objects, OK = confirmed (may be wrong)',
           'Gray=unknown; dark=outside; pale=observed safe',
           'Orange=free but insufficient clearance; red=occupied',
           'Purple=actual EGO inflated cloud, slice near robot Z',
           'EGO cloud: '+state.get('cloud_topic','waiting for publisher'),
           'Cloud age: '+(f"{time.monotonic()-state['cloud_received']:.1f}s" if 'cloud_received' in state else 'not received'),
           'Plan age: '+(f"{time.monotonic()-state['plan_received']:.1f}s" if 'plan_received' in state else 'not received'),
           '', 'Recent stages (simulation seconds):',
           *[f"{e['t']:.1f}s {e['event']} {e['action']} {e['reason']}" for e in data.get('stages',[])],
           '', 'No ground-truth object coordinates are displayed.']
    panel.text(0,1,'\n'.join(textwrap.fill(str(t),53) for t in lines),va='top',fontsize=8)
    fig.tight_layout()

def accept_debug(state,data):
    from semantic_debug_camera import decode_frame
    camera=data.get('camera');old=state.get('debug',{}).get('camera')
    state.update(debug=data,received=time.monotonic())
    if not camera:
        state.pop('camera_rgb',None);state.pop('camera_decode_error',None)
        return
    if camera!=old or state.get('camera_rgb') is None:
        try:
            state['camera_rgb']=decode_frame(camera);state.pop('camera_decode_error',None)
        except Exception as exc:
            state.pop('camera_rgb',None);state['camera_decode_error']=type(exc).__name__

def main():
    p=argparse.ArgumentParser();p.add_argument('--save',type=Path,help='Save latest frame on close');a=p.parse_args()
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import QoSProfile,DurabilityPolicy,qos_profile_sensor_data
    from std_msgs.msg import String
    from nav_msgs.msg import Path as RosPath
    from sensor_msgs.msg import PointCloud2
    from sensor_msgs_py import point_cloud2
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    configure_fonts()
    rclpy.init();node=Node('rov_semantic_debug_viewer');state={};subscriptions=[]
    def debug(msg):
        accept_debug(state,json.loads(msg.data))
    def plan(msg):state.update(plan=[[p.pose.position.x,p.pose.position.y] for p in msg.poses],plan_received=time.monotonic())
    def cloud(msg):
        xyz=point_cloud2.read_points_numpy(msg,field_names=('x','y','z'),skip_nans=True)
        pos=state.get('debug',{}).get('position');z=pos[2] if pos else 1.
        xy=xyz[np.abs(xyz[:,2]-z)<.06,:2]
        state.update(inflated=xy[::max(1,len(xy)//6000)],cloud_received=time.monotonic())
    subscriptions.append(node.create_subscription(String,'/rov/semantic/debug',debug,1))
    subscriptions.append(node.create_subscription(String,'/rov/tracking_status',lambda m:state.update(tracker=json.loads(m.data)),1))
    subscriptions.append(node.create_subscription(RosPath,'/rov/planned_path',plan,QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL)))
    def discover():
        if state.get('cloud_topic'):return
        for topic,types in node.get_topic_names_and_types():
            if topic.endswith('/occupancy_inflate') and 'sensor_msgs/msg/PointCloud2' in types:
                subscriptions.append(node.create_subscription(PointCloud2,topic,cloud,qos_profile_sensor_data));state['cloud_topic']=topic;break
    node.create_timer(2.,discover)
    fig=plt.figure(figsize=(19,9));plt.show(block=False);last=0.
    try:
        while rclpy.ok() and plt.fignum_exists(fig.number):
            rclpy.spin_once(node,timeout_sec=.02)
            if time.monotonic()-last>.5:
                draw(fig,state);fig.canvas.draw_idle();last=time.monotonic()
            plt.pause(.01)
    except KeyboardInterrupt:pass
    finally:
        if a.save:a.save.parent.mkdir(parents=True,exist_ok=True);fig.savefig(a.save,dpi=160)
        node.destroy_node()
        if rclpy.ok():rclpy.shutdown()
if __name__=='__main__':main()
