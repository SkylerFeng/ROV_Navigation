#!/usr/bin/env bash
set -euo pipefail
project_dir=$(cd "$(dirname "$0")/.." && pwd)
isaac_dir=${ISAAC_SIM_PATH:-/home/ache/isaac-sim}
# Isaac Python 3.11 uses bundled ROS, not system Humble's Python 3.10 modules.
export ROS_DISTRO=humble
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export PYTHONPATH="$isaac_dir/exts/isaacsim.ros2.bridge/humble/rclpy"
export LD_LIBRARY_PATH="$isaac_dir/exts/isaacsim.ros2.bridge/humble/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec "$isaac_dir/python.sh" -u "$project_dir/scripts/run_sim.py" "$@"
