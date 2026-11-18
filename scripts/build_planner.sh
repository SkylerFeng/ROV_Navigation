#!/usr/bin/env bash
set -e
source /opt/ros/humble/setup.bash
source /home/ache/Coding/ego/ego-planner-swarm/install/setup.bash
project_dir=$(cd "$(dirname "$0")/.." && pwd)
cd "$project_dir/ros_ws"
MAKEFLAGS=-j2 colcon build --packages-select plan_env ego_planner --allow-overriding plan_env ego_planner \
  --executor sequential --cmake-force-configure --cmake-args -DBUILD_TESTING=OFF \
  -Dplan_env_DIR="$project_dir/ros_ws/install/plan_env/share/plan_env/cmake"
