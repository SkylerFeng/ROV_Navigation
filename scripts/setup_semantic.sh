#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"
isaac_dir=/home/ache/isaac-sim
mkdir -p .venv/semantic_ros .venv/semantic_packages logs/semantic_detector/pretrained
python3 -m pip install --target .venv/semantic_ros --no-deps onnxruntime==1.23.2
"$isaac_dir/python.sh" -m pip install --target .venv/semantic_packages --no-deps ultralytics==8.4.202 ultralytics-thop==2.2.5 polars==2.1.0 polars-runtime-32==2.1.0 onnx==1.23.2 protobuf==7.36.2 ml_dtypes==0.6.0
if [ ! -f logs/semantic_detector/pretrained/yolo11n.pt ]; then
  curl -fL --retry 2 https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11n.pt -o logs/semantic_detector/pretrained/yolo11n.pt
fi
