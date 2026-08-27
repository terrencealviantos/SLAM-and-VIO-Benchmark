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

RESULTS_DIR="${REPO_ROOT}/results/${TARGET}/kimera"
DATASETS_DIR="${REPO_ROOT}/datasets"
KIMERA_WS="${REPO_ROOT}/workspace/kimera_ws"
RVIZ_DIR="${REPO_ROOT}/scripts/rviz"

mkdir -p "$RESULTS_DIR"

if [ "$TARGET" == "suedhoehe" ]; then
    BAG_PATH="${DATASETS_DIR}/suedhoehe_gps_schnee_02"
    PARAMS_PATH="${REPO_ROOT}/suedhoehe_kimera_params"
    DATASET_NAME="suedhoehe"
    RVIZ_FILE="/rviz_cfg/suedhoehe_rviz.rviz"
    LEFT_TOPIC="/camera/infra1/image_rect_raw"
    RIGHT_TOPIC="/camera/infra2/image_rect_raw"
    IMU_TOPIC="/camera/imu"
elif [ "$TARGET" == "euroc_MH01" ]; then
    BAG_PATH="${DATASETS_DIR}/Euroc/machine_hall/MH_01_easy/MH_01_easy_ros2"
    PARAMS_PATH="${REPO_ROOT}/workspace/kimera_ws/src/Kimera-VIO-ROS2/kimera_vio_ros/params/Euroc"
    DATASET_NAME="Euroc"
    RVIZ_FILE="/rviz_cfg/euroc_rviz.rviz"
    LEFT_TOPIC="/cam0/image_raw"
    RIGHT_TOPIC="/cam1/image_raw"
    IMU_TOPIC="/imu0"
else
    BAG_PATH="$TARGET"
    PARAMS_PATH="${REPO_ROOT}/suedhoehe_kimera_params"
    DATASET_NAME="suedhoehe"
    RVIZ_FILE="/rviz_cfg/suedhoehe_rviz.rviz"
    LEFT_TOPIC="/camera/infra1/image_rect_raw"
    RIGHT_TOPIC="/camera/infra2/image_rect_raw"
    IMU_TOPIC="/camera/imu"
fi

echo "=========================================================="
echo " Kimera-VIO Benchmark"
echo " Target Dataset : $BAG_PATH"
echo " Output Folder  : $RESULTS_DIR"
echo " Base Image     : kimera:latest (ROS 2, OpenCV, GTSAM, iSAM2)"
echo " Resource Limits: ${CPUS} Cores Max, ${MEMORY} RAM Max"
echo " GUI Viewer Mode: $ENABLE_GUI"
echo "=========================================================="

BAG_DIR="$(dirname "$(realpath "$BAG_PATH")")"
BAG_NAME="$(basename "$BAG_PATH")"

# Allow X11 access for Docker GUI
xhost +local:root 2>/dev/null || xhost + 2>/dev/null || true

# Cleanup previous instances
docker kill kimera_node kimera_rviz kimera_player 2>/dev/null || true
docker rm -f kimera_node kimera_rviz kimera_player 2>/dev/null || true

if [ "$ENABLE_GUI" = true ]; then
    echo "[INFO] Multi-Terminal GUI Mode Enabled: Opening Kimera-VIO Node, RViz2, and Bag Player..."

    # 1. Start Kimera-VIO in Terminal 1
    "${REPO_ROOT}/scripts/launch_terminal.sh" "[1] Kimera-VIO Node" \
      "docker run --rm --name kimera_node \
        --cpus=${CPUS} --memory=${MEMORY} \
        --net=host --ipc=host \
        -v '${BAG_DIR}':/dataset_dir \
        -v '${RESULTS_DIR}':/output \
        -v '${PARAMS_PATH}':/params \
        -v '${REPO_ROOT}/scripts':/scripts \
        kimera:latest \
        bash -c 'source /opt/wrapper_ws/install/setup.bash && \
                 (python3 /scripts/kimera_save_trajectory.py /output/kimera_tum.txt &) && \
                 ros2 launch kimera_vio_ros kimera_vio_ros.launch.xml \
                   params_folder:=/params \
                   parallel:=false \
                   use_camera_info:=false \
                   topic.left.image:=${LEFT_TOPIC} \
                   topic.right.image:=${RIGHT_TOPIC} \
                   topic.imu.data:=${IMU_TOPIC} \
                   log_output:=true'"

    sleep 4

    # 2. Start RViz2 in Terminal 2
    "${REPO_ROOT}/scripts/launch_terminal.sh" "[2] RViz2 Kimera Viewer" \
      "docker run --rm --name kimera_rviz \
        --net=host --ipc=host \
        -e DISPLAY=${DISPLAY} -e QT_X11_NO_MITSHM=1 -v /tmp/.X11-unix:/tmp/.X11-unix \
        -v '${RVIZ_DIR}':/rviz_cfg \
        slam-base:latest \
        bash -c 'source /opt/ros/humble/setup.bash && rviz2 -d ${RVIZ_FILE}'"

    sleep 2

    # 3. Start Rosbag Player in Terminal 3
    "${REPO_ROOT}/scripts/launch_terminal.sh" "[3] Rosbag Player" \
      "docker run --rm --name kimera_player -it \
        --net=host --ipc=host \
        -v '${BAG_DIR}':/dataset_dir \
        slam-base:latest \
        bash -c 'source /opt/ros/humble/setup.bash && ros2 bag play /dataset_dir/${BAG_NAME}'"

else
    echo "[1/3] Starting Kimera-VIO container..."
    docker run -d --name kimera_node \
      --cpus="${CPUS}" --memory="${MEMORY}" \
      --net=host --ipc=host \
      -v "${BAG_DIR}":/dataset_dir \
      -v "${RESULTS_DIR}":/output \
      -v "${PARAMS_PATH}":/params \
      -v "${REPO_ROOT}/scripts":/scripts \
      kimera:latest \
      bash -c "source /opt/wrapper_ws/install/setup.bash && \
               (python3 /scripts/kimera_save_trajectory.py /output/kimera_tum.txt &) && \
               ros2 launch kimera_vio_ros kimera_vio_ros.launch.xml \
                 params_folder:=/params \
                 parallel:=false \
                 use_camera_info:=false \
                 topic.left.image:=${LEFT_TOPIC} \
                 topic.right.image:=${RIGHT_TOPIC} \
                 topic.imu.data:=${IMU_TOPIC} \
                 log_output:=true"

    echo "[2/3] Waiting for node to initialize..."
    sleep 4

    echo "[3/3] Playing dataset bag..."
    docker run --rm --name kimera_player \
      --net=host --ipc=host \
      -v "${BAG_DIR}":/dataset_dir \
      slam-base:latest \
      bash -c "source /opt/ros/humble/setup.bash && ros2 bag play /dataset_dir/${BAG_NAME}"

    sleep 3

    # Cleanup
    docker kill kimera_node 2>/dev/null || true
    docker rm -f kimera_node 2>/dev/null || true

    echo "=========================================================="
    echo " Kimera-VIO run completed!"
    echo " Results saved to: ${RESULTS_DIR}/kimera_tum.txt"
    echo "=========================================================="
fi
