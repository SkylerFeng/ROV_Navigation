"""Real planner regression: heading waits freeze phase without recovery loops."""
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time
import numpy as np
import rclpy
from rosgraph_msgs.msg import Clock
from nav_msgs.msg import Odometry
from sensor_msgs.msg import PointCloud2, PointField
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import String, Header
from experiment import ROOT
from traj_utils.msg import Bspline
from spline import sample_spline

rclpy.init();node=rclpy.create_node('planner_feedback_regression')
statuses=[]
splines=[]
node.create_subscription(Bspline,'/rov/bspline',splines.append,100)
node.create_subscription(String,'/rov/planner_status',lambda m:statuses.append(json.loads(m.data)),100)
clocks=node.create_publisher(Clock,'/clock',10)
odoms=node.create_publisher(Odometry,'/rov/odom',10)
clouds=node.create_publisher(PointCloud2,'/rov/cloud_navigation',10)
goals=node.create_publisher(PoseStamped,'/move_base_simple/goal',10)
output=ROOT/'logs/diagnostics/slalom_phase_20261014';output.mkdir(parents=True,exist_ok=True)
log=(output/'heading_execution_test.log').open('w')
process=subprocess.Popen(['bash',str(ROOT/'scripts/start_navigation.sh')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
sim_time=10.
yaw=0.
forward_velocity=0.

def tick(count):
    global sim_time
    for _ in range(count):
        sim_time+=.05
        stamp=Clock();stamp.clock.sec=int(sim_time);stamp.clock.nanosec=int((sim_time%1)*1e9);clocks.publish(stamp)
        od=Odometry();od.header=Header(stamp=stamp.clock,frame_id='world');od.pose.pose.position.x=-2.7;od.pose.pose.position.z=1.;od.pose.pose.orientation.w=math.cos(yaw/2);od.pose.pose.orientation.z=math.sin(yaw/2)
        od.twist.twist.linear.x=forward_velocity;odoms.publish(od)
        points=np.array([[3.5,0,1]],dtype=np.float32)
        clouds.publish(PointCloud2(header=od.header,height=1,width=1,fields=[PointField(name=a,offset=i*4,datatype=7,count=1) for i,a in enumerate('xyz')],point_step=12,row_step=12,data=points.tobytes(),is_dense=True))
        end=time.monotonic()+.025
        while time.monotonic()<end:rclpy.spin_once(node,timeout_sec=.002)

def send(x,y):
    msg=PoseStamped();msg.header.frame_id='world';msg.pose.position.x=float(x);msg.pose.position.y=float(y);msg.pose.position.z=1.;msg.pose.orientation.w=1.;goals.publish(msg)

try:
    deadline=time.monotonic()+10
    while (not statuses or goals.get_subscription_count()==0) and time.monotonic()<deadline:tick(5)
    assert statuses and goals.get_subscription_count(), 'Planner did not start'
    send(-2.7,2);tick(180)
    assert statuses[-1]['heading_paused'],statuses[-1]
    assert statuses[-1]['tracking_recoveries']==0,statuses[-1]
    assert statuses[-1]['tracking_error']<.1,statuses[-1]
    yaw=math.pi/2
    tick(180)
    assert any(s['tracking_recoveries']>0 for s in statuses), 'Aligned reference did not resume'
    assert statuses[-1]['have_target'], 'Stationary odometry must not mark arrival'
    send(3.5,0);tick(60)
    assert statuses[-1]['state']=='BLOCKED_GOAL',statuses[-1]
    assert statuses[-1]['have_target'] and statuses[-1]['goal_occupancy']==1
    yaw=0.
    send(0,0);tick(60)
    assert any(s['state']=='EXEC_TRAJ' and s.get('goal_occupancy')==0 for s in statuses[-30:]), statuses[-1]
    splines.clear()
    send(-2.6,0);tick(80)
    terminal=[m for m in splines if len(m.pos_pts)==6 and
              all(abs(p.x+2.6)<1e-8 and abs(p.y)<1e-8 for p in m.pos_pts[-3:])]
    assert terminal,'No exact terminal B-spline for a 0.1 m goal'
    m=terminal[0]
    _,points=sample_spline([[p.x,p.y,p.z] for p in m.pos_pts],m.knots,m.order)
    assert np.linalg.norm(points[-1]-np.array([-2.6,0,1]))<1e-8
    assert statuses[-1]['have_target'],'Stationary robot falsely finished terminal approach'
    # HighBay regression: the free-endpoint optimizer overshot by 0.25 m,
    # outside the old 0.2 m terminal range. Check a half-metre approach.
    splines.clear()
    send(-2.2,0);tick(80)
    terminal=[m for m in splines if len(m.pos_pts)==6 and
              all(abs(p.x+2.2)<1e-8 and abs(p.y)<1e-8 for p in m.pos_pts[-3:])]
    assert terminal,'No exact terminal B-spline for a 0.5 m goal'
    m=terminal[0]
    _,points=sample_spline([[p.x,p.y,p.z] for p in m.pos_pts],m.knots,m.order)
    assert np.linalg.norm(points[-1]-np.array([-2.2,0,1]))<1e-8
    assert statuses[-1]['have_target'],'Stationary robot falsely finished half-metre approach'
    # A final target can enter the 3 m horizon long before the old 0.6 m
    # exact-approach range. Preserve measured initial velocity as well.
    splines.clear()
    forward_velocity=.12
    send(-.2,0);tick(80)
    terminal=[m for m in splines if len(m.pos_pts)==6 and
              all(abs(p.x+.2)<1e-8 and abs(p.y)<1e-8 for p in m.pos_pts[-3:])]
    assert terminal,'No exact terminal B-spline for a moving 2.5 m approach'
    m=terminal[0]
    points=np.array([[p.x,p.y,p.z] for p in m.pos_pts])
    dt=m.knots[m.order+1]-m.knots[m.order]
    assert np.linalg.norm((points[2]-points[0])/(2*dt)-[.12,0,0])<1e-8
    times,positions=sample_spline(points,m.knots,m.order,count=1001)
    assert np.linalg.norm(positions[-1]-[-.2,0,1])<1e-8
    assert positions[:,0].max()<=-.2+1e-8,'Approach overshoots endpoint'
    velocity=np.diff(positions,axis=0)/np.diff(times)[:,None]
    acceleration=np.diff(velocity,axis=0)/np.diff(times[:-1])[:,None]
    assert np.linalg.norm(velocity,axis=1).max()<=.15+1e-6
    assert np.linalg.norm(acceleration,axis=1).max()<=.1+1e-6
    (output/'heading_execution_test.json').write_text(json.dumps(statuses,indent=2))
    print('Passed: heading wait/resume, replacement goals, exact 0.1/0.5/2.5 m terminal splines, initial velocity and dynamics, no stationary arrival')
finally:
    process.send_signal(signal.SIGINT)
    try:process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGKILL);process.wait()
    log.close();node.destroy_node();rclpy.shutdown()
