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

SCRIPT_DIR="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Defaults (can be overridden via CLI flags or env vars)
CPUS="${CPUS:-2}"
MEMORY="${MEMORY:-3g}"
TARGET="suedhoehe"
ENABLE_GUI=false

# Parse CLI arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --gui|--view|-g|--terminals)
            ENABLE_GUI=true
            shift
            ;;
        --cpus)
            CPUS="$2"
            shift 2
            ;;
        --memory|-m)
            MEMORY="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [dataset_target] [--gui] [--cpus <N>] [--memory <MEM>]"
            echo ""
            echo "Arguments:"
            echo "  dataset_target       Target dataset: suedhoehe, euroc_MH01, or custom bag path (default: suedhoehe)"
            echo "  --gui, --view, -g    Open live GUI (RViz2) and separate terminal windows for Node, Bag & Viewer"
            echo "  --cpus <N>           Max CPU cores for container (default: 2)"
            echo "  --memory, -m <MEM>   Max RAM for container (default: 3g)"
            echo "  -h, --help           Show this help message"
            exit 0
            ;;
        *)
            TARGET="$1"
            shift
            ;;
    esac
done

RESULTS_DIR="${REPO_ROOT}/results/${TARGET}/openvins"
DATASETS_DIR="${REPO_ROOT}/datasets"
CATKIN_WS="${REPO_ROOT}/workspace/catkin_ws_ov"
RVIZ_CFG="/catkin_ws/src/open_vins/ov_msckf/launch/display_ros2.rviz"

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
echo " Resource Limits: ${CPUS} Cores Max, ${MEMORY} RAM Max"
echo " GUI Viewer Mode: $ENABLE_GUI"
echo "=========================================================="

BAG_DIR="$(dirname "$(realpath "$BAG_PATH")")"
BAG_NAME="$(basename "$BAG_PATH")"

# Allow X11 access for Docker GUI
xhost +local:root 2>/dev/null || xhost + 2>/dev/null || true

if [ "$ENABLE_GUI" = true ]; then
    echo "[INFO] Multi-Terminal GUI Mode Enabled: Opening OpenVINS Node, RViz2, and Bag Player..."

    # 1. Start OpenVINS in Terminal 1
    "${REPO_ROOT}/scripts/launch_terminal.sh" "[1] OpenVINS MSCKF Node" \
      "docker run --rm --name openvins_node --entrypoint '' \
        --cpus=${CPUS} --memory=${MEMORY} \
        --net=host --ipc=host \
        -v '${CATKIN_WS}':/catkin_ws \
        -v '${RESULTS_DIR}':/results \
        slam-base:latest \
        bash -c 'source /opt/ros/humble/setup.bash && source /catkin_ws/install/setup.bash && ros2 run open_vins_eval run_subscribe_msckf --ros-args -p sys_config_path:=${CONFIG_PATH}'"

    sleep 3

    # 2. Start RViz2 in Terminal 2
    "${REPO_ROOT}/scripts/launch_terminal.sh" "[2] RViz2 OpenVINS Viewer" \
      "docker run --rm --name openvins_rviz --entrypoint '' \
        --net=host --ipc=host \
        -e DISPLAY=${DISPLAY} -e QT_X11_NO_MITSHM=1 -v /tmp/.X11-unix:/tmp/.X11-unix \
        -v '${CATKIN_WS}':/catkin_ws \
        slam-base:latest \
        bash -c 'source /opt/ros/humble/setup.bash && source /catkin_ws/install/setup.bash && rviz2 -d ${RVIZ_CFG}'"

    sleep 2

    # 3. Start Rosbag Player in Terminal 3
    "${REPO_ROOT}/scripts/launch_terminal.sh" "[3] Rosbag Player" \
      "docker run --rm --name openvins_player --entrypoint '' -it \
        --net=host --ipc=host \
        -v '${BAG_DIR}':/dataset_dir \
        slam-base:latest \
        bash -c 'source /opt/ros/humble/setup.bash && ros2 bag play /dataset_dir/${BAG_NAME} --clock 200'"

else
    docker run --rm --entrypoint "" \
      --cpus="${CPUS}" --memory="${MEMORY}" \
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
fi
