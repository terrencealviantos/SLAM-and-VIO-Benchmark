#!/bin/bash
# run_cuvslam_suedhoehe.sh
# Launcher for NVIDIA cuVSLAM (Isaac ROS Visual SLAM) on the Suedhoehe dataset
# Uses NVIDIA GPU acceleration (CUDA) inside the Isaac ROS container.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

RESULTS_DIR="${WORKSPACE_ROOT}/results/suedhoehe/cuvslam"
DATASETS_DIR="${WORKSPACE_ROOT}/datasets"
PARAMS_DIR="${WORKSPACE_ROOT}/suedhoehe_kimera_params"
ISAAC_ROS_WS="${SCRIPT_DIR}/isaac_ros_ws"

BAG_INPUT="${1:-${DATASETS_DIR}/suedhoehe_gps_schnee_02}"

if [ ! -e "$BAG_INPUT" ]; then
  echo "=========================================================="
  echo " NVIDIA cuVSLAM Benchmark — Suedhoehe Dataset"
  echo "=========================================================="
  echo "Error: Dataset bag '$BAG_INPUT' does not exist."
  echo ""
  echo "Usage:"
  echo "  ./run_cuvslam_suedhoehe.sh [/path/to/suedhoehe_bag]"
  echo ""
  echo "Example:"
  echo "  ./run_cuvslam_suedhoehe.sh /home/boris/datasets/suedhoehe_gps_schnee_02"
  echo "  (or copy/symlink your bag into '${DATASETS_DIR}/suedhoehe_gps_schnee_02')"
  echo "=========================================================="
  exit 1
fi

BAG_ABS="$(realpath "$BAG_INPUT")"
BAG_DIR="$(dirname "$BAG_ABS")"
BAG_NAME="$(basename "$BAG_ABS")"

mkdir -p "$RESULTS_DIR"

echo "=========================================================="
echo " NVIDIA cuVSLAM Benchmark — Suedhoehe Dataset"
echo " Dataset Bag: $BAG_ABS"
echo " Hardware: NVIDIA GPU Accelerated (RTX 3050 Mobile)"
echo "=========================================================="

# Allow local container connection to X11 server
xhost +local:docker &>/dev/null || true

# Export workspace path for isaac_ros_common
export ISAAC_ROS_WS="$ISAAC_ROS_WS"

echo "[1/3] Starting Isaac ROS Visual SLAM Container with GPU passthrough..."
docker kill cuvslam_suedhoehe_run 2>/dev/null || true
docker rm cuvslam_suedhoehe_run 2>/dev/null || true

docker run -d --name cuvslam_suedhoehe_run \
  --runtime=nvidia --gpus all --net=host --ipc=host \
  -v "$RESULTS_DIR":/results \
  -v "$BAG_DIR":/dataset_dir \
  -v "$ISAAC_ROS_WS":/workspaces/isaac_ros-dev \
  isaac_ros_dev-x86_64:latest \
  bash -c "source /opt/ros/humble/setup.bash && \
           source /workspaces/isaac_ros-dev/install/setup.bash && \
           ros2 launch isaac_ros_visual_slam isaac_ros_visual_slam_suedhoehe.launch.py"

echo "[2/3] Waiting for cuVSLAM node to initialize..."
sleep 5

PLAY_PATH="/dataset_dir/${BAG_NAME}"

echo "[3/3] Playing Suedhoehe Dataset Bag: $PLAY_PATH..."
docker run --rm --name suedhoehe_player \
  --runtime=nvidia --gpus all --net=host --ipc=host \
  -v "$BAG_DIR":/dataset_dir \
  isaac_ros_dev-x86_64:latest \
  bash -c "source /opt/ros/humble/setup.bash && \
           ros2 bag play ${PLAY_PATH}"

echo "=== Bag playback finished ==="
sleep 3

# Clean up container
docker kill cuvslam_suedhoehe_run 2>/dev/null || true
docker rm cuvslam_suedhoehe_run 2>/dev/null || true

echo "cuVSLAM Suedhoehe run finished successfully!"
