#!/usr/bin/env bash
set -e
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=${ROV_RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}
project_dir=$(cd "$(dirname "$0")/.." && pwd)
# Upstream EGO manual-goal callback fixes z=1.0; this baseline matches it.
exec /usr/bin/python3 "$project_dir/scripts/send_goal.py" "$@"
