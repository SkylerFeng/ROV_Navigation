"""Isaac Sim 5.1/OceanSim navigation baseline; run with Isaac's python.sh."""
import argparse
import json
from pathlib import Path
from experiment import load_experiment

parser = argparse.ArgumentParser()
parser.add_argument("--headless", action="store_true")
parser.add_argument("--steps", type=int, default=0)
parser.add_argument("--scenario")
parser.add_argument("--scene-file", type=Path)
parser.add_argument("--output-dir")
parser.add_argument("--cloud-stride", type=int, choices=(1, 2, 4, 8), default=1)
parser.add_argument("--capture", action="store_true", help="Save overview viewport snapshots")
parser.add_argument("--top-view", action="store_true")
parser.add_argument("--view", choices=("top", "perspective"), default="top")
parser.add_argument("--wall-time-limit", type=float, default=0)
parser.add_argument("--stop-on-blocked-goal", action="store_true")
parser.add_argument("--stop-on-goal", action="store_true")
parser.add_argument("--sim-time-limit", type=float, default=0)
parser.add_argument("--arrival-tolerance", type=float, default=None)
parser.add_argument("--settle-time", type=float, default=0)
args = parser.parse_args()
ROOT = Path(__file__).resolve().parents[1]
C = load_experiment(args.scenario)
if args.scene_file:
    C["scene_file"] = str(args.scene_file.resolve())
from datetime import datetime
from zoneinfo import ZoneInfo
run_id = C["scenario"] + "_" + datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d_%H%M%S")
OUTPUT = Path(args.output_dir) if args.output_dir else ROOT / "logs/runs" / run_id
OUTPUT.mkdir(parents=True, exist_ok=True)

from isaacsim import SimulationApp
app = SimulationApp({"headless": args.headless, "width": 1280, "height": 720})
try:
    import sys
    import time
    import numpy as np
    from pxr import Gf, PhysicsSchemaTools, PhysxSchema, UsdGeom
    from omni.physx import get_physx_simulation_interface
    from omni.physx.bindings._physx import ContactEventType
    from isaacsim.core.api import World
    from isaacsim.core.prims import SingleRigidPrim
    from isaacsim.core.utils.extensions import enable_extension
    from isaacsim.core.utils.stage import open_stage
    from isaacsim.core.utils.viewports import set_camera_view

    enable_extension("isaacsim.ros2.bridge")
    enable_extension("isaacsim.util.debug_draw")
    app.update()
    # Import only the OceanSim camera module; don't open its example UI.
    import isaacsim
    isaacsim.__path__.append("/home/ache/isaac-sim/extsUser/OceanSim/isaacsim")
    from isaacsim.oceansim.sensors.UW_Camera import UW_Camera
    import rclpy
    from geometry_msgs.msg import Twist
    from nav_msgs.msg import Odometry
    from nav_msgs.msg import Path as RosPath
    from rclpy.qos import QoSProfile, DurabilityPolicy
    from std_msgs.msg import String
    from viewport_paths import ViewportPaths, top_view
    from rosgraph_msgs.msg import Clock
    from sensor_msgs.msg import Image, PointCloud2, PointField
    from std_msgs.msg import Header
    from tf2_msgs.msg import TFMessage
    from geometry_msgs.msg import TransformStamped

    open_stage(C["scene_file"])
    world = World(stage_units_in_meters=1.0, physics_dt=1/60, rendering_dt=1/30)
    stage = world.stage
    if C.get("render_pool_collision", False):
        from build_scene import reveal_pool_collision
        reveal_pool_collision(stage)
    from build_scene import translate
    translate(stage.GetPrimAtPath("/World/Markers/Goal"), [*C["goal"][:2], C["water_surface"]+.1])
    translate(stage.GetPrimAtPath("/World/Markers/Start"), [*C["start"][:2], C["water_surface"]+.1])
    body = stage.GetPrimAtPath("/World/ROV")
    api = PhysxSchema.PhysxRigidBodyAPI.Apply(body)
    api.CreateDisableGravityAttr(True)
    api.CreateLinearDampingAttr(2.0)
    api.CreateAngularDampingAttr(4.0)
    forces = PhysxSchema.PhysxForceAPI.Apply(body)
    forces.CreateForceEnabledAttr(True)
    forces.CreateWorldFrameEnabledAttr(True)
    forces.CreateModeAttr("force")
    forces.CreateForceAttr(Gf.Vec3f(0))
    forces.CreateTorqueAttr(Gf.Vec3f(0))
    PhysxSchema.PhysxContactReportAPI.Apply(body).CreateThresholdAttr().Set(0)
    contacts = {}
    def on_contacts(headers, data):
        for header in headers:
            if header.type == ContactEventType.CONTACT_LOST:
                continue
            pair = sorted(str(PhysicsSchemaTools.intToSdfPath(v)) for v in (header.collider0, header.collider1))
            if not any(path.startswith("/World/ROV/") for path in pair):
                continue
            key = " | ".join(pair)
            now = float(world.current_time)
            entry = contacts.setdefault(key, {"colliders": pair, "first_time": now, "reports": 0})
            entry["last_time"] = now
            entry["reports"] += 1
            if header.num_contact_data:
                contact = data[header.contact_data_offset]
                entry["last_contact_position"] = list(map(float, contact.position))
                entry["last_contact_normal"] = list(map(float, contact.normal))
                entry["last_contact_impulse"] = list(map(float, contact.impulse))
                impulses = [float(np.linalg.norm(data[i].impulse)) for i in range(header.contact_data_offset, header.contact_data_offset+header.num_contact_data)]
                impulse = max(impulses, default=0)
                entry["max_impulse_norm"] = max(entry.get("max_impulse_norm", 0), impulse)
                if impulse > 1e-6:
                    entry["nonzero_impulse_reports"] = entry.get("nonzero_impulse_reports", 0)+1
                    entry.setdefault("first_impulse_time", now)
                    entry["last_impulse_time"] = now
    contact_subscription = get_physx_simulation_interface().subscribe_contact_report_events(on_contacts)
    robot = world.scene.add(SingleRigidPrim("/World/ROV", name="rov", position=np.array(C["start"])))
    robot.set_default_state(position=np.array(C["start"]), orientation=np.array([1.0, 0, 0, 0]))
    camera = UW_Camera("/World/ROV/FrontCamera", resolution=C["camera_resolution"],
                       translation=np.array([0.3, 0.0, 0.1]))
    world.reset()
    camera.set_local_pose(translation=np.array([0.3, 0, 0.1]),
                          orientation=np.array([1.0, 0, 0, 0]), camera_axes="world")
    # Explicit simulated camera coverage; use matching aperture/focal units.
    hfov = np.radians(C.get("camera_horizontal_fov_deg", 53.03184))
    camera.set_focal_length(camera.get_horizontal_aperture()/(2*np.tan(hfov/2)))
    camera.set_clipping_range(0.08, 15.0)
    camera.initialize(viewport=False, max_range=8.0)
    camera._camera_k = camera.get_intrinsics_matrix()
    (OUTPUT / "camera_calibration.json").write_text(json.dumps({
        "intrinsics": np.asarray(camera._camera_k).tolist(), "resolution": C["camera_resolution"],
        "horizontal_fov_deg": float(np.degrees(2*np.arctan(C["camera_resolution"][0]/(2*camera._camera_k[0,0]))))}, indent=2))
    set_camera_view(eye=np.array([0, -6, 5]), target=np.array([0, 0, 1]))
    if args.top_view or args.view == "top":
        top_view()
    rclpy.init()
    node = rclpy.create_node("rov_oceansim")
    odom_pub = node.create_publisher(Odometry, "/rov/odom", 10)
    cloud_pub = node.create_publisher(PointCloud2, "/rov/cloud_world", 10)
    rgb_pub = node.create_publisher(Image, "/rov/rgb", 10)
    clock_pub = node.create_publisher(Clock, "/clock", 10)
    tf_pub = node.create_publisher(TFMessage, "/tf", 10)
    command = {"linear": np.zeros(3), "yaw_rate": 0.0, "received": -float("inf")}

    def receive(msg):
        command["linear"] = np.array([msg.linear.x, msg.linear.y, msg.linear.z])
        command["yaw_rate"] = msg.angular.z
        command["received"] = time.monotonic()

    node.create_subscription(Twist, "/rov/cmd_vel_world", receive, 10)
    visualization = ViewportPaths(C)
    visualization.window.visible = not args.headless
    path_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
    node.create_subscription(RosPath, "/rov/planned_path", visualization.receive_path, path_qos)
    node.create_subscription(RosPath, "/rov/control_polygon", visualization.receive_controls, path_qos)
    node.create_subscription(String, "/rov/plan_info", lambda msg: setattr(visualization, "info", json.loads(msg.data)), path_qos)
    history = []
    samples = []
    controls = []
    telemetry = {"tracking": None, "planner": None}
    def receive_status(kind, msg):
        data = json.loads(msg.data)
        telemetry[kind] = data
        setattr(visualization, kind+"_status", data)
    node.create_subscription(String, "/rov/tracking_status", lambda msg: receive_status("tracking", msg), 10)
    node.create_subscription(String, "/rov/planner_status", lambda msg: receive_status("planner", msg), 10)
    arrival_since = None
    blocked_since = None
    arrival_tolerance = args.arrival_tolerance if args.arrival_tolerance is not None else C.get("goal_tolerance", .3)
    points = np.empty((0, 3), dtype=np.float32)
    step = 0
    pos, quat = robot.get_world_pose()
    loop_started = time.monotonic()
    stop_reason = "step_limit"
    node.get_logger().info("ROV ready. World velocities: /rov/cmd_vel_world; start planner separately.")
    while app.is_running() and (not args.steps or step < args.steps):
        if args.wall_time_limit and time.monotonic()-loop_started > args.wall_time_limit:
            stop_reason = "wall_time_limit"
            break
        blocked = telemetry["planner"] and telemetry["planner"].get("state") == "BLOCKED_GOAL"
        blocked_since = (world.current_time if blocked_since is None else blocked_since) if blocked else None
        if args.stop_on_blocked_goal and blocked_since is not None and world.current_time-blocked_since > 1 and np.linalg.norm(robot.get_linear_velocity()) < .02:
            stop_reason = "goal_occupied"
            break
        if args.sim_time_limit and world.current_time >= args.sim_time_limit:
            stop_reason = "simulation_time_limit"
            break
        inside_goal = step > 60 and np.linalg.norm(pos-np.array(C["goal"])) < arrival_tolerance
        arrival_since = (world.current_time if arrival_since is None else arrival_since) if inside_goal else None
        if args.stop_on_goal and arrival_since is not None and world.current_time-arrival_since >= args.settle_time:
            stop_reason = "goal_reached"
            break
        for _ in range(4):
            rclpy.spin_once(node, timeout_sec=0)
        if not world.is_playing():
            world.step(render=True)
            continue
        pos, quat = robot.get_world_pose()
        velocity = robot.get_linear_velocity()
        angular = robot.get_angular_velocity()
        fresh = time.monotonic() - command["received"] <= C["command_timeout"]
        desired = command["linear"].copy() if fresh else np.zeros(3)
        if not np.all(np.isfinite(desired)):
            desired[:] = 0
        speed = np.linalg.norm(desired)
        if speed > C["max_velocity"]:
            desired *= C["max_velocity"] / speed
        # Bound vertical motion to keep the full hull submerged and above floor.
        if pos[2] < 0.88:
            desired[2] = max(desired[2], 0.08)
        if pos[2] > 1.18:
            desired[2] = min(desired[2], -0.08)
        # Closed-loop force tracking, not teleporting the pose or setting velocity.
        force = np.clip(5.0 * (6.0 * (desired - velocity) + 2.0 * velocity), -12, 12)
        yaw_rate = float(np.clip(command["yaw_rate"], -0.5, 0.5)) if fresh else 0.0
        if not np.isfinite(yaw_rate):
            yaw_rate = 0.0
        # Restoring roll/pitch torque makes this a 4-DOF baseline.
        q = Gf.Quatd(float(quat[0]), Gf.Vec3d(*map(float, quat[1:])))
        up = np.array(Gf.Rotation(q).TransformDir(Gf.Vec3d(0, 0, 1)))
        torque = 2 * np.cross(up, [0, 0, 1]) - 0.5 * angular
        torque[2] = 0.4 * (yaw_rate - angular[2])
        forces.GetForceAttr().Set(Gf.Vec3f(*map(float, force)))
        forces.GetTorqueAttr().Set(Gf.Vec3f(*map(float, torque)))
        world.step(render=True)
        step += 1
        stamp = Clock()
        t = world.current_time
        stamp.clock.sec = int(t)
        stamp.clock.nanosec = int((t % 1) * 1e9)
        clock_pub.publish(stamp)
        pos, quat = robot.get_world_pose()
        odom = Odometry()
        odom.header = Header(stamp=stamp.clock, frame_id="world")
        odom.child_frame_id = "base_link"
        odom.pose.pose.position.x, odom.pose.pose.position.y, odom.pose.pose.position.z = map(float, pos)
        odom.pose.pose.orientation.w, odom.pose.pose.orientation.x, odom.pose.pose.orientation.y, odom.pose.pose.orientation.z = map(float, quat)
        # EGO's odometry callback expects world-frame linear velocity.
        odom.twist.twist.linear.x, odom.twist.twist.linear.y, odom.twist.twist.linear.z = map(float, robot.get_linear_velocity())
        odom_pub.publish(odom)
        tf = TransformStamped(header=odom.header, child_frame_id="base_link")
        tf.transform.translation.x, tf.transform.translation.y, tf.transform.translation.z = map(float, pos)
        tf.transform.rotation = odom.pose.pose.orientation
        tf_pub.publish(TFMessage(transforms=[tf]))
        if step % 300 == 0:
            progress = {"simulation_seconds": float(t), "position": pos.tolist(),
                        "goal_distance": float(np.linalg.norm(pos-np.array(C["goal"]))),
                        "contacts": list(contacts.values()), "desired_velocity": desired.tolist(), "force": force.tolist()}
            (OUTPUT / "progress.json").write_text(json.dumps(progress, indent=2))
            print("Progress", json.dumps(progress), flush=True)
        if step % 6 == 0:
            samples.append([float(t), *map(float, pos)])
            controls.append({"t": float(t), "desired_velocity": desired.tolist(), "force": force.tolist(),
                             "velocity": robot.get_linear_velocity().tolist(), "orientation": quat.tolist(), "fresh_command": fresh, **telemetry})
            camera.render()
            # Establish the planner/controller baseline before testing optical
            # depth dropout. OceanSim RGB remains underwater-rendered.
            if C.get("depth_mode", "ideal") == "ideal":
                raw_depth = camera._depth_annot.get_data().numpy()
                camera._degraded_depth_frame = np.where(
                    np.isfinite(raw_depth) & (raw_depth > 0.08) & (raw_depth < 8.0),
                    raw_depth, 0.0).astype(np.float32)
            points = camera._build_pointcloud(stride=args.cloud_stride)
            if len(points):
                cp, cq = camera.get_world_pose(camera_axes="ros")
                rotation = Gf.Rotation(Gf.Quatd(float(cq[0]), Gf.Vec3d(*map(float, cq[1:]))))
                matrix = np.array([rotation.TransformDir(Gf.Vec3d(*axis)) for axis in np.eye(3)])
                points = np.ascontiguousarray(points @ matrix + cp, dtype=np.float32)
                cloud = PointCloud2(header=odom.header, height=1, width=len(points),
                    fields=[PointField(name=n, offset=i*4, datatype=PointField.FLOAT32, count=1) for i, n in enumerate("xyz")],
                    is_bigendian=False, point_step=12, row_step=len(points)*12,
                    data=points.tobytes(), is_dense=True)
                cloud_pub.publish(cloud)
            if camera._uw_frame is not None:
                rgb = np.ascontiguousarray(camera._uw_frame[:, :, :3], dtype=np.uint8)
                rgb_pub.publish(Image(header=Header(stamp=stamp.clock, frame_id="front_camera"),
                    height=rgb.shape[0], width=rgb.shape[1], encoding="rgb8", step=rgb.shape[1]*3, data=rgb.tobytes()))
            history.append(tuple(map(float, pos)))
            history = history[-2000:]
            visualization.update(history, pos)
            # Debug overlays are viewport-only, not part of the sensor scene.
            if args.capture and step in (120, 600, 1800, 3600):
                from omni.kit.viewport.utility import capture_viewport_to_file, get_active_viewport
                capture_viewport_to_file(get_active_viewport(), str(OUTPUT / f"viewport_{step}.png"))
    if not samples:
        samples.append([float(world.current_time), *map(float, pos)])
    result = {
        "steps": step, "samples": samples,
        "simulation_seconds": float(world.current_time), "wall_seconds": time.monotonic()-loop_started,
        "pool_collision_visibility": str(UsdGeom.Imageable(stage.GetPrimAtPath("/World/Environment/Platform/Collision/Platform_collision_clean/mesh")).ComputeVisibility()),
        "cloud_stride": args.cloud_stride,
        "arrival_tolerance": arrival_tolerance, "settle_time": args.settle_time,
        "sim_time_limit": args.sim_time_limit, "wall_time_limit": args.wall_time_limit,
        "contacts": list(contacts.values()),
        "final_position": list(map(float, pos)),
        "goal_distance": float(np.linalg.norm(pos - np.array(C["goal"]))),
        "cloud_frames": camera._id,
        "depth_mode": C.get("depth_mode", "ideal"),
        "scenario": C["scenario"], "config": C, "plan_updates": visualization.updates,
        "output_dir": str(OUTPUT), "stop_reason": stop_reason,
    }
    (ROOT / "logs/last_run.json").write_text(json.dumps(result, indent=2))
    (OUTPUT / "run.json").write_text(json.dumps(result, indent=2))
    (OUTPUT / "controls.json").write_text(json.dumps(controls))
    (OUTPUT / "plans.json").write_text(json.dumps(list(visualization.journal)))
    if camera._uw_frame is not None:
        np.save(ROOT / "logs/last_camera.npy", camera._uw_frame)
        np.save(OUTPUT / "camera.npy", camera._uw_frame)
    if len(points):
        np.save(ROOT / "logs/last_cloud.npy", points)
    print("Simulation completed", step, "steps; goal distance", np.linalg.norm(pos - C["goal"]), flush=True)
    camera.close()
    node.destroy_node()
    rclpy.shutdown()
except BaseException:
    import traceback
    traceback.print_exc()
    raise
finally:
    app.close()
