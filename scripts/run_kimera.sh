#!/bin/bash
# ==============================================================================
# Kimera-VIO Benchmark Launcher
# ==============================================================================
# Single-command launcher for running Kimera-VIO in the ROS 2 environment.
#
# Usage:
#   ./scripts/run_kimera.sh [suedhoehe | euroc_MH01 | /path/to/bag]
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TARGET="${1:-suedhoehe}"
RESULTS_DIR="${REPO_ROOT}/results/${TARGET}/kimera"
DATASETS_DIR="${REPO_ROOT}/datasets"
KIMERA_WS="${REPO_ROOT}/workspace/kimera_ws"

mkdir -p "$RESULTS_DIR"

if [ "$TARGET" == "suedhoehe" ]; then
    BAG_PATH="${DATASETS_DIR}/suedhoehe_gps_schnee_02"
    DATASET_NAME="suedhoehe"
elif [ "$TARGET" == "euroc_MH01" ]; then
    BAG_PATH="${DATASETS_DIR}/Euroc/machine_hall/MH_01_easy/MH_01_easy_ros2"
    DATASET_NAME="Euroc"
else
    BAG_PATH="$TARGET"
    DATASET_NAME="Euroc"
fi

echo "=========================================================="
echo " Kimera-VIO Benchmark"
echo " Target Dataset : $BAG_PATH"
echo " Output Folder  : $RESULTS_DIR"
echo " Base Image     : slam-base:latest (ROS 2, OpenCV, GTSAM)"
echo " Resource Limits: 2 Cores Max, 3 GB RAM Max"
echo "=========================================================="

BAG_DIR="$(dirname "$(realpath "$BAG_PATH")")"
BAG_NAME="$(basename "$BAG_PATH")"

docker run --rm \
  --cpus=2 --memory=3g \
  -v "${BAG_DIR}":/dataset_dir \
  -v "${RESULTS_DIR}":/output \
  slam-base:latest \
  bash -c "source /opt/ros/humble/setup.bash && \
           if [ -f /opt/ros/wrapper_ws/install/setup.bash ]; then \
             source /opt/ros/wrapper_ws/install/setup.bash; \
             ros2 launch kimera_vio_ros kimera_vio_ros.launch.xml dataset_name:=${DATASET_NAME} log_output:=true & \
             K_PID=\$! && sleep 3 && \
             ros2 bag play /dataset_dir/${BAG_NAME} --clock 200 && sleep 3 && \
             cp -r /opt/ros/wrapper_ws/install/kimera_vio_ros/share/kimera_vio_ros/output_logs/* /output/ 2>/dev/null || true && \
             kill \$K_PID 2>/dev/null || true; \
           fi"

echo "=========================================================="
echo " Kimera-VIO run completed!"
echo " Results saved to: ${RESULTS_DIR}"
echo "=========================================================="
