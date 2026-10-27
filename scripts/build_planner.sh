#!/usr/bin/env bash
set -e
source /opt/ros/humble/setup.bash
source /home/ache/Coding/ego/ego-planner-swarm/install/setup.bash
project_dir=$(cd "$(dirname "$0")/.." && pwd)
cd "$project_dir/ros_ws"
MAKEFLAGS=-j2 colcon build --packages-select ego_planner --allow-overriding ego_planner \
  --executor sequential --cmake-args -DBUILD_TESTING=OFF
