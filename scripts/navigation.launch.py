"""Use existing EGO binaries and defaults, without launching the UAV simulator."""
import importlib.util
import json
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from experiment import load_experiment


def generate_launch_description():
    root = Path(__file__).resolve().parents[1]
    c = load_experiment()
    defaults = Path(get_package_share_directory("ego_planner")) / "launch/advanced_param.launch.py"
    spec = importlib.util.spec_from_file_location("ego_defaults", defaults)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Keep upstream optimizer settings; override map and vehicle assumptions.
    template = next(a for a in module.generate_launch_description().entities if isinstance(a, Node))
    params = list(template._Node__parameters)
    params.append({
        "use_sim_time": True,
        "fsm/flight_type": 1,
        "fsm/max_tracking_error": c.get("tracking_error_limit", .25),
        "fsm/arrival_tolerance": c.get("planner_goal_tolerance", .05),
        "fsm/heading_aware_execution": c.get("align_before_translation", True),
        "fsm/max_heading_error_deg": c.get("max_heading_error_deg", 20.0),
        "fsm/observed_global_guide": c.get("observed_global_guide", True),
        "fsm/navigation_polygon": [coordinate for point in json.loads(
            (root / "config/pool_water_boundary.json").read_text()) for coordinate in point],
        "fsm/thresh_replan_time": 0.5,
        "fsm/thresh_no_replan_meter": 0.2,
        "fsm/planning_horizon": 3.0,
        "manager/planning_horizon": 3.0,
        "manager/drone_id": 0,
        "grid_map/map_size_x": 16.0,
        "grid_map/map_size_y": 12.0,
        "grid_map/map_size_z": 3.0,
        "grid_map/ground_height": 0.6,
        "grid_map/virtual_ceil_height": 1.5,
        "grid_map/visualization_truncate_height": 1.7,
        "grid_map/resolution": 0.05,
        "grid_map/obstacles_inflation": 0.5,
        "grid_map/local_update_range_x": 8.0,
        "grid_map/local_update_range_y": 6.0,
        "grid_map/local_update_range_z": 2.0,
        "optimization/dist0": 0.35,
        "optimization/lambda_collision": 3.0,
        "manager/max_vel": c["max_velocity"],
        "optimization/max_vel": c["max_velocity"],
        "bspline/limit_vel": c["max_velocity"],
        "manager/max_acc": c["max_acceleration"],
        "optimization/max_acc": c["max_acceleration"],
        "bspline/limit_acc": c["max_acceleration"],
        "prediction/obj_num": 0,
    })
    # Resolve the template's launch substitutions by retaining its declarations.
    declarations = [a for a in module.generate_launch_description().entities if not isinstance(a, Node)]
    planner = Node(package="ego_planner", executable="ego_planner_node", name="rov_ego_planner",
        output="screen", parameters=params,
        remappings=[("odom_world", "/rov/odom"), ("grid_map/odom", "/rov/odom"),
                    ("grid_map/cloud", "/rov/cloud_navigation"),
                    ("planning/bspline", "/rov/bspline")])
    trajectory = Node(package="ego_planner", executable="traj_server", name="rov_trajectory_server",
        output="screen", parameters=[{"use_sim_time": True, "traj_server/time_forward": 0.5,
                                      "traj_server/use_execution_phase": c.get("align_before_translation", True)}],
        remappings=[("planning/bspline", "/rov/bspline"), ("position_cmd", "/rov/position_cmd")])
    tracker = ExecuteProcess(cmd=["/usr/bin/python3", str(root / "scripts/tracker.py"),
                                 "--ros-args", "-p", "use_sim_time:=true"], output="screen")
    mapping = ExecuteProcess(cmd=["/usr/bin/python3", str(root / "scripts/local_map.py"),
                                 "--ros-args", "-p", "use_sim_time:=true"], output="screen")
    visualization = ExecuteProcess(cmd=["/usr/bin/python3", str(root / "scripts/trajectory_visualizer.py"),
                                 "--ros-args", "-p", "use_sim_time:=true"], output="screen")
    return LaunchDescription(declarations + [planner, trajectory, tracker, mapping, visualization])
