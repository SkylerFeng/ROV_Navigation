"""Integration: occupied goal is explicit, replacement goal does not block,
and a stationary robot is never declared finished by nominal spline time."""
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

rclpy.init();node=rclpy.create_node('planner_feedback_regression')
statuses=[]
node.create_subscription(String,'/rov/planner_status',lambda m:statuses.append(json.loads(m.data)),100)
clocks=node.create_publisher(Clock,'/clock',10)
odoms=node.create_publisher(Odometry,'/rov/odom',10)
clouds=node.create_publisher(PointCloud2,'/rov/cloud_navigation',10)
goals=node.create_publisher(PoseStamped,'/move_base_simple/goal',10)
output=ROOT/'logs/diagnostics/slalom_phase_20261014';output.mkdir(parents=True,exist_ok=True)
log=(output/'planner_feedback_test.log').open('w')
process=subprocess.Popen(['bash',str(ROOT/'scripts/start_navigation.sh')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
sim_time=10.
yaw=0.

def tick(count):
    global sim_time
    for _ in range(count):
        sim_time+=.05
        stamp=Clock();stamp.clock.sec=int(sim_time);stamp.clock.nanosec=int((sim_time%1)*1e9);clocks.publish(stamp)
        od=Odometry();od.header=Header(stamp=stamp.clock,frame_id='world');od.pose.pose.position.x=-2.7;od.pose.pose.position.z=1.;od.pose.pose.orientation.w=math.cos(yaw/2);od.pose.pose.orientation.z=math.sin(yaw/2);odoms.publish(od)
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
    send(3.5,0);tick(60)
    assert statuses[-1]['state']=='BLOCKED_GOAL',statuses[-1]
    assert statuses[-1]['have_target'] and statuses[-1]['goal_occupancy']==1
    # Point the synthetic camera at the valid goal so this test exercises
    # measured-state recovery, rather than an intentional heading wait.
    yaw=math.atan2(2.,2.7)
    send(0,2);tick(60)
    assert any(s['state']=='EXEC_TRAJ' and s.get('goal_occupancy')==0 for s in statuses[-30:]), statuses[-1]
    tick(400)
    assert statuses[-1]['have_target'], 'Nominal time incorrectly marked stationary robot as arrived'
    assert statuses[-1]['tracking_recoveries']>0, statuses[-1]
    assert statuses[-1]['goal_error']>3
    (output/'planner_feedback_test.json').write_text(json.dumps(statuses,indent=2))
    print('Passed: occupied-goal hold, responsive replacement goal, measured-state recovery, no phantom arrival')
finally:
    process.send_signal(signal.SIGINT)
    try:process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGKILL);process.wait()
    log.close();node.destroy_node();rclpy.shutdown()
