#!/bin/bash
# run_cuvslam_euroc.sh
# Launcher for NVIDIA cuVSLAM on EuRoC MAV datasets
# Processes ROS 2 bag files and extracts estimated trajectory in TUM format

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SEQ_NAME="${1:-MH_01_easy}"
RESULTS_DIR="${WORKSPACE_ROOT}/results/euroc/${SEQ_NAME}"
DATASET_BAG="${WORKSPACE_ROOT}/datasets/Euroc/machine_hall/${SEQ_NAME}/${SEQ_NAME}_ros2"
ISAAC_ROS_WS="${SCRIPT_DIR}/isaac_ros_ws"

if [ ! -d "$DATASET_BAG" ]; then
  # Check vicon room
  DATASET_BAG="${WORKSPACE_ROOT}/datasets/Euroc/vicon_room1/${SEQ_NAME}/${SEQ_NAME}_ros2"
fi

if [ ! -e "$DATASET_BAG" ]; then
  echo "=========================================================="
  echo " NVIDIA cuVSLAM Benchmark — EuRoC Dataset"
  echo "=========================================================="
  echo "Error: EuRoC dataset bag for '$SEQ_NAME' does not exist."
  echo "Looked for: $DATASET_BAG"
  echo ""
  echo "Usage:"
  echo "  ./run_cuvslam_euroc.sh [sequence_name]"
  echo "Example:"
  echo "  ./run_cuvslam_euroc.sh MH_01_easy"
  echo "=========================================================="
  exit 1
fi

echo "=========================================================="
echo " NVIDIA cuVSLAM Benchmark — EuRoC Sequence: $SEQ_NAME"
echo " Hardware: NVIDIA GPU Accelerated (CUDA / Tensor Cores)"
echo "=========================================================="

xhost +local:docker &>/dev/null || true

# Run cuVSLAM container with GPU support
docker run -d --name cuvslam_euroc_run \
  --runtime=nvidia --gpus all --net=host --ipc=host \
  -v "$RESULTS_DIR":/results \
  -v "$ISAAC_ROS_WS":/workspaces/isaac_ros-dev \
  isaac_ros_dev-x86_64:latest \
  bash -c "source /opt/ros/humble/setup.bash && \
           source /workspaces/isaac_ros-dev/install/setup.bash 2>/dev/null || true && \
           ros2 launch isaac_ros_visual_slam isaac_ros_visual_slam.launch.py \
             num_cameras:=2 \
             enable_imu_fusion:=true \
             rectified_images:=false \
             enable_localization_n_mapping:=true" &

echo "Waiting for cuVSLAM node to initialize..."
sleep 4

echo "Playing EuRoC bag: $DATASET_BAG ..."
docker run --rm --name euroc_player --net=host \
  -v "$DATASET_BAG":/dataset \
  isaac_ros_dev-x86_64:latest \
  bash -c "source /opt/ros/humble/setup.bash && \
           ros2 bag play /dataset \
             --remap /cam0/image_raw:=/visual_slam/image_0 \
             --remap /cam1/image_raw:=/visual_slam/image_1 \
             --remap /imu0:=/visual_slam/imu"

echo "Bag play finished."
sleep 3

docker kill cuvslam_euroc_run 2>/dev/null || true
docker rm cuvslam_euroc_run 2>/dev/null || true

echo "cuVSLAM benchmark completed for $SEQ_NAME."
