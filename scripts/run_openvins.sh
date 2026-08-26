#!/bin/bash
# ==============================================================================
# OpenVINS (MSCKF Filter) Benchmark Launcher
# ==============================================================================
# Single-command launcher for running OpenVINS in the ROS 2 environment.
#
# Usage:
#   ./scripts/run_openvins.sh [suedhoehe | euroc_MH01 | /path/to/bag]
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

TARGET="${1:-suedhoehe}"
RESULTS_DIR="${REPO_ROOT}/results/${TARGET}/openvins"
DATASETS_DIR="${REPO_ROOT}/datasets"
CATKIN_WS="${REPO_ROOT}/workspace/catkin_ws_ov"

mkdir -p "$RESULTS_DIR"

if [ "$TARGET" == "suedhoehe" ]; then
    BAG_PATH="${DATASETS_DIR}/suedhoehe_gps_schnee_02"
    CONFIG_PATH="/catkin_ws/src/open_vins/config/suedhoehe/estimator_config.yaml"
    if [ ! -f "${CATKIN_WS}/src/open_vins/config/suedhoehe/estimator_config.yaml" ]; then
        CONFIG_PATH="/catkin_ws/src/open_vins/config/euroc_mav/estimator_config.yaml"
    fi
elif [ "$TARGET" == "euroc_MH01" ]; then
    BAG_PATH="${DATASETS_DIR}/Euroc/machine_hall/MH_01_easy/MH_01_easy_ros2"
    CONFIG_PATH="/catkin_ws/src/open_vins/config/euroc_mav/estimator_config.yaml"
else
    BAG_PATH="$TARGET"
    CONFIG_PATH="/catkin_ws/src/open_vins/config/euroc_mav/estimator_config.yaml"
fi

echo "=========================================================="
echo " OpenVINS MSCKF Benchmark"
echo " Target Dataset : $BAG_PATH"
echo " Output Folder  : $RESULTS_DIR"
echo " Base Image     : slam-base:latest (ROS 2, OpenCV, Ceres)"
echo " Resource Limits: 2 Cores Max, 3 GB RAM Max"
echo "=========================================================="

BAG_DIR="$(dirname "$(realpath "$BAG_PATH")")"
BAG_NAME="$(basename "$BAG_PATH")"

docker run --rm \
  --cpus=2 --memory=3g \
  -v "${CATKIN_WS}":/catkin_ws \
  -v "${BAG_DIR}":/dataset_dir \
  -v "${RESULTS_DIR}":/results \
  slam-base:latest \
  bash -c "source /opt/ros/humble/setup.bash && \
           source /catkin_ws/install/setup.bash && \
           ros2 run open_vins_eval run_subscribe_msckf --ros-args -p sys_config_path:=${CONFIG_PATH} & \
           OV_PID=\$! && sleep 3 && \
           ros2 bag play /dataset_dir/${BAG_NAME} --clock 200 && sleep 3 && \
           cp /tmp/ov_estimate.txt /results/openvins_tum.txt 2>/dev/null || true && \
           kill \$OV_PID 2>/dev/null || true"

echo "=========================================================="
echo " OpenVINS run completed successfully!"
echo " Results saved to: ${RESULTS_DIR}/openvins_tum.txt"
echo "=========================================================="
