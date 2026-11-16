#!/usr/bin/env bash
set -eo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-137}"
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp
export PYTHONPATH="$root/scripts:${PYTHONPATH:-}"
exec /usr/bin/python3 "$root/scripts/semantic_debug_viewer.py" "$@"
