#!/bin/bash
# ==============================================================================
# NVIDIA cuVSLAM (Isaac ROS Visual SLAM) Benchmark Launcher
# ==============================================================================
# Single-command launcher for GPU-accelerated cuVSLAM.
#
# Usage:
#   ./scripts/run_cuvslam.sh [suedhoehe | euroc_MH01 | /path/to/bag]
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TARGET="${1:-suedhoehe}"
RESULTS_DIR="${REPO_ROOT}/results/${TARGET}/cuvslam"
DATASETS_DIR="${REPO_ROOT}/datasets"
ISAAC_WS="${REPO_ROOT}/workspace/isaac_ros_ws"

mkdir -p "$RESULTS_DIR"

if [ "$TARGET" == "suedhoehe" ]; then
    BAG_PATH="${DATASETS_DIR}/suedhoehe_gps_schnee_02"
    LAUNCH_FILE="isaac_ros_visual_slam_suedhoehe.launch.py"
elif [ "$TARGET" == "euroc_MH01" ]; then
    BAG_PATH="${DATASETS_DIR}/Euroc/machine_hall/MH_01_easy/MH_01_easy_ros2"
    LAUNCH_FILE="isaac_ros_visual_slam_euroc.launch.py"
else
    BAG_PATH="$TARGET"
    LAUNCH_FILE="isaac_ros_visual_slam_suedhoehe.launch.py"
fi

BAG_DIR="$(dirname "$(realpath "$BAG_PATH")")"
BAG_NAME="$(basename "$BAG_PATH")"

echo "=========================================================="
echo " NVIDIA cuVSLAM GPU Benchmark"
echo " Target Dataset : $BAG_PATH"
echo " Output Folder  : $RESULTS_DIR"
echo " GPU Acceleration: NVIDIA CUDA (RTX 3050)"
echo " Base Image     : slam-base:latest (ROS 2, OpenCV, CUDA)"
echo " Resource Limits: 2 Cores Max, 3 GB RAM Max"
echo "=========================================================="

# Clean previous containers
docker kill cuvslam_node_run cuvslam_saver suedhoehe_player 2>/dev/null || true
docker rm -f cuvslam_node_run cuvslam_saver suedhoehe_player 2>/dev/null || true

echo "[1/3] Starting cuVSLAM container with GPU passthrough..."
docker run -d --name cuvslam_node_run \
  --cpus=2 --memory=3g \
  --runtime=nvidia --gpus all --net=host --ipc=host \
  -v "${RESULTS_DIR}":/results \
  -v "${BAG_DIR}":/dataset_dir \
  -v "${ISAAC_WS}":/workspaces/isaac_ros-dev \
  slam-base:latest \
  bash -c "source /opt/ros/humble/setup.bash && \
           source /workspaces/isaac_ros-dev/install/setup.bash && \
           export LD_LIBRARY_PATH=/workspaces/isaac_ros-dev/install/isaac_ros_visual_slam/share/cuvslam/lib:\$LD_LIBRARY_PATH && \
           ros2 launch isaac_ros_visual_slam ${LAUNCH_FILE}"

echo "[2/3] Waiting for cuVSLAM node to initialize..."
sleep 5

# Start trajectory recorder
docker run -d --name cuvslam_saver \
  --net=host --ipc=host \
  -v "${RESULTS_DIR}":/results \
  -v "${REPO_ROOT}/scripts":/scripts \
  cuvslam:latest \
  bash -c "source /opt/ros/humble/setup.bash && python3 /scripts/cuvslam_save_trajectory.py /results/cuvslam_tum.txt"

sleep 2

echo "[3/3] Playing dataset bag..."
docker run --rm --name suedhoehe_player \
  --runtime=nvidia --gpus all --net=host --ipc=host \
  -v "${BAG_DIR}":/dataset_dir \
  cuvslam:latest \
  bash -c "source /opt/ros/humble/setup.bash && ros2 bag play /dataset_dir/${BAG_NAME}"

sleep 3

# Cleanup
docker kill cuvslam_node_run cuvslam_saver 2>/dev/null || true
docker rm -f cuvslam_node_run cuvslam_saver 2>/dev/null || true

echo "=========================================================="
echo " cuVSLAM run completed!"
echo " Results saved to: ${RESULTS_DIR}/cuvslam_tum.txt"
echo "=========================================================="
