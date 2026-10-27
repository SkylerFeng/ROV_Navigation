#!/usr/bin/env bash
set -e
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=${ROV_RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}
source /home/ache/Coding/ego/ego-planner-swarm/install/setup.bash
project_dir=$(cd "$(dirname "$0")/.." && pwd)
if [ ! -f "$project_dir/ros_ws/install/setup.bash" ]; then
  echo 'Build the simulation-clock planner first: bash scripts/build_planner.sh' >&2
  exit 1
fi
source "$project_dir/ros_ws/install/setup.bash"
exec ros2 launch "$project_dir/scripts/navigation.launch.py"
