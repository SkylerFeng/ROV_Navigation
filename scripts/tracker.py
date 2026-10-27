#!/usr/bin/env python3
"""Convert EGO PositionCommand into explicitly world-frame velocity targets."""
import math
import json
from std_msgs.msg import String
from experiment import load_experiment
from tracking_control import control
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from quadrotor_msgs.msg import PositionCommand


class Tracker(Node):
    def __init__(self):
        super().__init__("rov_tracker")
        self.config = load_experiment()
        self.status_pub = self.create_publisher(String, "/rov/tracking_status", 10)
        self.last_status = -math.inf
        self.odom = self.reference = None
        self.last_odom = self.last_reference = -math.inf
        self.publisher = self.create_publisher(Twist, "/rov/cmd_vel_world", 10)
        self.create_subscription(Odometry, "/rov/odom", self.receive_odom, 10)
        self.create_subscription(PositionCommand, "/rov/position_cmd", self.receive_reference, 10)
        self.create_timer(1 / 30, self.update)

    def receive_odom(self, msg):
        self.odom = msg
        self.last_odom = self.get_clock().now().nanoseconds / 1e9

    def receive_reference(self, msg):
        self.reference = msg
        self.last_reference = self.get_clock().now().nanoseconds / 1e9

    def update(self):
        now = self.get_clock().now().nanoseconds / 1e9
        out = Twist()
        status = {"t": now, "mode": "STALE_INPUT"}
        if self.odom and self.reference and now-self.last_odom < .5 and now-self.last_reference < .5:
            p = self.odom.pose.pose.position
            ref = self.reference
            q = self.odom.pose.pose.orientation
            yaw = math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))
            position = [getattr(p,a) for a in "xyz"]
            ref_position = [getattr(ref.position,a) for a in "xyz"]
            ref_velocity = [getattr(ref.velocity,a) for a in "xyz"]
            values, rate, detail = control(position, ref_position, ref_velocity, yaw, ref.yaw,
                max_speed=self.config["max_velocity"], align=self.config.get("align_before_translation",True),
                max_heading_error_deg=self.config.get("max_heading_error_deg",20))
            out.linear.x, out.linear.y, out.linear.z = values
            out.angular.z = rate
            status.update(detail)
            if detail["mode"] != "INVALID_REFERENCE":
                status.update(position=position, reference_position=ref_position, reference_velocity=ref_velocity,
                              command_velocity=values, yaw=yaw, trajectory_id=ref.trajectory_id)
        self.publisher.publish(out)
        if now-self.last_status >= .1:
            self.status_pub.publish(String(data=json.dumps(status,allow_nan=False)))
            self.last_status = now


def main():
    rclpy.init()
    node = Tracker()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        if rclpy.ok():
            node.publisher.publish(Twist())
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
