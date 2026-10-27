#!/usr/bin/env bash
set -euo pipefail
project_dir=$(cd "$(dirname "$0")/.." && pwd)
exec bash "$project_dir/scripts/usd_python.sh" "$project_dir/scripts/build_scene.py" --scenario "${1:-slalom}"
