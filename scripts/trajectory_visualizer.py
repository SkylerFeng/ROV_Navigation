"""Publish every accepted EGO spline as a Path for Isaac's viewport overlay."""
import json
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from rclpy.qos import QoSProfile, DurabilityPolicy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path
from std_msgs.msg import String
from traj_utils.msg import Bspline
from spline import sample_spline


class TrajectoryVisualizer(Node):
    def __init__(self):
        super().__init__("rov_trajectory_visualizer")
        qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.path_pub = self.create_publisher(Path, "/rov/planned_path", qos)
        self.controls_pub = self.create_publisher(Path, "/rov/control_polygon", qos)
        self.meta_pub = self.create_publisher(String, "/rov/plan_info", qos)
        self.create_subscription(Bspline, "/rov/bspline", self.receive, 10)
        self.updates = 0

    def receive(self, msg):
        controls = [[p.x, p.y, p.z] for p in msg.pos_pts]
        try:
            times, points = sample_spline(controls, msg.knots, msg.order)
        except ValueError as exc:
            self.get_logger().warning(str(exc))
            return
        self.updates += 1
        def path_message(values):
            path = Path()
            path.header.frame_id = "world"
            # Receipt in the node's simulation clock aligns replay with odometry.
            path.header.stamp = self.get_clock().now().to_msg()
            for xyz in values:
                pose = PoseStamped(header=path.header)
                pose.pose.position.x, pose.pose.position.y, pose.pose.position.z = map(float, xyz)
                pose.pose.orientation.w = 1.0
                path.poses.append(pose)
            return path
        self.path_pub.publish(path_message(points))
        self.controls_pub.publish(path_message(controls))
        self.meta_pub.publish(String(data=json.dumps({"trajectory_id": msg.traj_id,
            "updates": self.updates, "duration": float(times[-1]), "control_points": len(controls),
            "trajectory_start_time": msg.start_time.sec + msg.start_time.nanosec/1e9})))


if __name__ == "__main__":
    rclpy.init()
    node = TrajectoryVisualizer()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
