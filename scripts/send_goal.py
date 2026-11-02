"""Wait for live odometry and cloud, then publish a live navigation goal."""
import json
import argparse
import time
from pathlib import Path
import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import PointCloud2
from experiment import load_experiment

c = load_experiment()
parser=argparse.ArgumentParser()
parser.add_argument('--delay-sim-seconds',type=float,default=0.)
parser.add_argument('--goal', nargs=2, type=float, metavar=('X','Y'),
                    help='goal position in world metres; z is fixed to the planner depth (1.0 m)')
args=parser.parse_args()
rclpy.init()
node = rclpy.create_node("rov_goal_sender")
ready = set()
odom_time=[None]
def receive_odom(msg):
    ready.add('odom');odom_time[0]=msg.header.stamp.sec+msg.header.stamp.nanosec/1e9
node.create_subscription(Odometry, "/rov/odom", receive_odom, 10)
node.create_subscription(PointCloud2, "/rov/cloud_navigation", lambda _: ready.add("cloud"), 10)
pub = node.create_publisher(PoseStamped, "/move_base_simple/goal", 10)
deadline = time.monotonic() + 120
while (len(ready) < 2 or pub.get_subscription_count() == 0) and time.monotonic() < deadline:
    rclpy.spin_once(node, timeout_sec=0.1)
if len(ready) < 2 or pub.get_subscription_count() == 0:
    raise RuntimeError("No live odometry/cloud/planner within 120 seconds")
first_time=odom_time[0]
deadline=time.monotonic()+650
while odom_time[0]-first_time < args.delay_sim_seconds:
    if time.monotonic()>deadline:raise RuntimeError('Simulation did not advance during goal delay')
    rclpy.spin_once(node,timeout_sec=.1)
goal = [float(args.goal[0]), float(args.goal[1]), 1.0] if args.goal else list(map(float, c["goal"]))
msg = PoseStamped()
msg.header.frame_id = "world"
msg.pose.position.x, msg.pose.position.y, msg.pose.position.z = goal
msg.pose.orientation.w = 1.0
pub.publish(msg)
for _ in range(10):
    rclpy.spin_once(node, timeout_sec=0.1)
print("Goal sent:", goal)
node.destroy_node()
rclpy.shutdown()
