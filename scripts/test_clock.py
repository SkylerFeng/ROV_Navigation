"""Regression: the C++ trajectory server follows /clock, including pauses."""
import math
import os
import signal
import subprocess
import time
import sys
import rclpy
from rosgraph_msgs.msg import Clock
from geometry_msgs.msg import Point, Vector3Stamped
from quadrotor_msgs.msg import PositionCommand
from traj_utils.msg import Bspline
from experiment import ROOT

rclpy.init()
node = rclpy.create_node("trajectory_clock_test")
phase_mode = "--execution-phase" in sys.argv
phase = None
phase_pub = node.create_publisher(Vector3Stamped, "/rov/trajectory_phase", 10)
clock = node.create_publisher(Clock, "/clock", 10)
splines = node.create_publisher(Bspline, "/clock_test/spline", 10)
commands = []
node.create_subscription(PositionCommand, "/clock_test/cmd", commands.append, 10)
process = subprocess.Popen([str(ROOT / "ros_ws/install/ego_planner/lib/ego_planner/traj_server"),
    "--ros-args", "-p", "use_sim_time:=true", "-p", "traj_server/time_forward:=0.1",
    "-p", f"traj_server/use_execution_phase:={str(phase_mode).lower()}",
    "-r", "planning/bspline:=/clock_test/spline", "-r", "position_cmd:=/clock_test/cmd"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


def tick(seconds, wall_duration):
    end = time.monotonic()+wall_duration
    while time.monotonic() < end:
        msg = Clock();msg.clock.sec = int(seconds);msg.clock.nanosec = int(round((seconds % 1)*1e9))
        clock.publish(msg)
        if phase_mode and phase is not None:
            progress = Vector3Stamped();progress.header.stamp=msg.clock
            progress.vector.x=1.;progress.vector.y=phase;phase_pub.publish(progress)
        rclpy.spin_once(node, timeout_sec=.01)


try:
    tick(10.0, 1.4)
    msg = Bspline();msg.order=3;msg.traj_id=1;msg.start_time.sec=10
    msg.knots=[-.6,-.4,-.2,0.,.2,.4,.6,.8]
    msg.pos_pts=[Point(x=float(i), y=0., z=1.) for i in range(4)]
    splines.publish(msg)
    tick(10.0, .15)
    phase = .05
    tick(10.05, .25)
    assert commands, "No trajectory commands received"
    first = commands[-1]
    assert abs(first.position.x-1.25) < 1e-5, first.position
    assert first.header.stamp.sec == 10
    assert all(math.isfinite(x) for x in [first.yaw,first.yaw_dot,first.velocity.x])
    count = len(commands)
    tick(10.05, .2)
    assert len(commands) == count, "Paused /clock must not advance trajectory"
    if phase_mode:
        tick(10.8, .2)
        assert abs(commands[-1].position.x-1.25)<1e-5, "Heading wait advanced the reference"
    phase = .1
    tick(10.9 if phase_mode else 10.1, .2)
    assert abs(commands[-1].position.x-1.5) < 1e-5
    if phase_mode:
        phase = None
        tick(11.5, .2)
        assert abs(commands[-1].position.x-1.5)<1e-5
        assert commands[-1].velocity.x==0, "Stale phase must hold"
        print("Execution-phase regression passed: held reference, resume, stale heartbeat hold")
    print("Clock regression passed: simulation-time sampling, pause, finite yaw")
finally:
    os.killpg(process.pid, signal.SIGINT)
    process.wait(timeout=5)
    node.destroy_node()
    rclpy.shutdown()
