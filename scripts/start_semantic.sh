#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
source /opt/ros/humble/setup.bash
export PYTHONPATH="$root/.venv/semantic_ros:$root/scripts:${PYTHONPATH:-}"
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
exec /usr/bin/python3 "$root/scripts/semantic_navigation.py" "$@" --ros-args -p use_sim_time:=true
