#!/usr/bin/env bash
set -euo pipefail
isaac_dir=${ISAAC_SIM_PATH:-/home/ache/isaac-sim}
usd_lib=$(compgen -G "$isaac_dir/extscache/omni.usd.libs-*.cp311" | head -n 1)
export PYTHONPATH="$usd_lib${PYTHONPATH:+:$PYTHONPATH}"
export LD_LIBRARY_PATH="$usd_lib/bin${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
exec "$isaac_dir/python.sh" "$@"
