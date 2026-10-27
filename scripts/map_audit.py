"""Read-only snapshots of the planner's actual inflated grid and input columns."""
import argparse
import json
from pathlib import Path
import time
import numpy as np
import rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import PointCloud2
from nav_msgs.msg import Odometry
from std_msgs.msg import String
from experiment import load_experiment


def xyz(msg):
    return np.ndarray((msg.width*msg.height,3),dtype='<f4',buffer=msg.data,
                      offset=next(f.offset for f in msg.fields if f.name=='x'),strides=(msg.point_step,4))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,required=True)
    args,rosargs=parser.parse_known_args();args.output_dir.mkdir(parents=True,exist_ok=True)
    rclpy.init(args=rosargs);node=rclpy.create_node('rov_map_audit')
    config=load_experiment();state={'input_xy':np.empty((0,2)), 'position':None, 'planner':None,'tracking':None,'last':-100.}
    def odom(msg):state['position']=[getattr(msg.pose.pose.position,a) for a in 'xyz']
    def cloud(msg):
        a=xyz(msg);state['input_xy']=np.unique(a[abs(a[:,2]-1)<.03,:2],axis=0).copy()
    def receive(msg):
        t=node.get_clock().now().nanoseconds/1e9  # Upstream grid-map publication has no stamp.
        if t-state['last']<5:return
        state['last']=t;a=xyz(msg);xy=np.unique(a[abs(a[:,2]-1)<.051,:2],axis=0).copy()
        goal=np.array(config['goal'][:2]);pos=state['position']
        # Grid voxel centres can differ by up to half a cell from queried XY.
        def occupied(point):
            centre=(np.floor((point+np.array([8.,6.]))/.05)+.5)*.05-np.array([8.,6.])
            return bool(len(xy) and np.any(np.max(abs(xy-centre),axis=1)<.001))
        meta={'t':t,'position':pos,'goal':config['goal'],'goal_occupied':occupied(goal),
              'position_occupied':occupied(np.array(pos[:2])) if pos else None,
              'planner':state['planner'],'tracking':state['tracking'],
              'input_cells':len(state['input_xy']),'inflated_cells':len(xy),
              'goal_input_distance_m':float(np.min(np.linalg.norm(state['input_xy']-goal,axis=1))) if len(state['input_xy']) else None}
        stem=args.output_dir/f'map_{t:07.2f}'
        np.savez_compressed(Path(str(stem)+'.npz'),inflated_xy=xy,input_xy=state['input_xy'])
        Path(str(stem)+'.json').write_text(json.dumps(meta,indent=2))
        (args.output_dir/'latest.json').write_text(json.dumps(meta,indent=2))
    qos=qos_profile_sensor_data
    node.create_subscription(Odometry,'/rov/odom',odom,qos)
    node.create_subscription(PointCloud2,'/rov/cloud_navigation',cloud,qos)
    node.create_subscription(PointCloud2,'/grid_map/occupancy_inflate',receive,qos)
    node.create_subscription(String,'/rov/planner_status',lambda m:state.update(planner=json.loads(m.data)),10)
    node.create_subscription(String,'/rov/tracking_status',lambda m:state.update(tracking=json.loads(m.data)),10)
    deadline=time.monotonic()+600
    try:
        while rclpy.ok() and time.monotonic()<deadline:rclpy.spin_once(node,timeout_sec=.1)
    except KeyboardInterrupt:pass
    finally:node.destroy_node();rclpy.shutdown()

if __name__=='__main__':main()
