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

RESULTS_DIR="${REPO_ROOT}/results/${TARGET}/cuvslam"
DATASETS_DIR="${REPO_ROOT}/datasets"
ISAAC_WS="${REPO_ROOT}/workspace/isaac_ros_ws"
RVIZ_DIR="${REPO_ROOT}/scripts/rviz"

mkdir -p "$RESULTS_DIR"

if [ "$TARGET" == "suedhoehe" ]; then
    BAG_PATH="${DATASETS_DIR}/suedhoehe_gps_schnee_02"
    LAUNCH_FILE="isaac_ros_visual_slam_suedhoehe.launch.py"
    RVIZ_FILE="/rviz_cfg/suedhoehe_rviz.rviz"
elif [ "$TARGET" == "euroc_MH01" ]; then
    BAG_PATH="${DATASETS_DIR}/Euroc/machine_hall/MH_01_easy/MH_01_easy_ros2"
    LAUNCH_FILE="isaac_ros_visual_slam_euroc.launch.py"
    RVIZ_FILE="/rviz_cfg/euroc_rviz.rviz"
else
    BAG_PATH="$TARGET"
    LAUNCH_FILE="isaac_ros_visual_slam_suedhoehe.launch.py"
    RVIZ_FILE="/rviz_cfg/suedhoehe_rviz.rviz"
fi

BAG_DIR="$(dirname "$(realpath "$BAG_PATH")")"
BAG_NAME="$(basename "$BAG_PATH")"

echo "=========================================================="
echo " NVIDIA cuVSLAM GPU Benchmark"
echo " Target Dataset : $BAG_PATH"
echo " Output Folder  : $RESULTS_DIR"
echo " GPU Acceleration: NVIDIA CUDA (RTX 3050)"
echo " Base Image     : slam-base:latest (ROS 2, OpenCV, CUDA)"
echo " Resource Limits: ${CPUS} Cores Max, ${MEMORY} RAM Max"
echo " GUI Viewer Mode: $ENABLE_GUI"
echo "=========================================================="

# Clean previous containers
docker kill cuvslam_node_run cuvslam_saver suedhoehe_player cuvslam_rviz 2>/dev/null || true
docker rm -f cuvslam_node_run cuvslam_saver suedhoehe_player cuvslam_rviz 2>/dev/null || true

# Allow X11 access for Docker
xhost +local:root 2>/dev/null || xhost + 2>/dev/null || true

if [ "$ENABLE_GUI" = true ]; then
    echo "[INFO] Multi-Terminal GUI Mode Enabled: Opening Node, RViz2, and Bag Player..."
    
    # 1. Start cuVSLAM in Terminal 1
    "${REPO_ROOT}/scripts/launch_terminal.sh" "[1] cuVSLAM Node" \
      "docker run --rm --name cuvslam_node_run \
        --cpus=${CPUS} --memory=${MEMORY} \
        --runtime=nvidia --gpus all --net=host --ipc=host \
        -e DISPLAY=${DISPLAY} -e QT_X11_NO_MITSHM=1 -v /tmp/.X11-unix:/tmp/.X11-unix \
        -v '${RESULTS_DIR}':/results \
        -v '${BAG_DIR}':/dataset_dir \
        -v '${ISAAC_WS}':/workspaces/isaac_ros-dev \
        -v '${REPO_ROOT}/scripts':/scripts \
        slam-base:latest \
        bash -c 'source /opt/ros/humble/setup.bash && source /workspaces/isaac_ros-dev/install/setup.bash && export LD_LIBRARY_PATH=/workspaces/isaac_ros-dev/install/isaac_ros_visual_slam/share/cuvslam/lib:\$LD_LIBRARY_PATH && (python3 /scripts/cuvslam_save_trajectory.py /results/cuvslam_tum.txt &) && ros2 launch isaac_ros_visual_slam ${LAUNCH_FILE}'"

    sleep 4

    # 2. Start RViz2 in Terminal 2
    "${REPO_ROOT}/scripts/launch_terminal.sh" "[2] RViz2 SLAM Viewer" \
      "docker run --rm --name cuvslam_rviz \
        --net=host --ipc=host \
        -e DISPLAY=${DISPLAY} -e QT_X11_NO_MITSHM=1 -v /tmp/.X11-unix:/tmp/.X11-unix \
        -v '${ISAAC_WS}':/workspaces/isaac_ros-dev \
        -v '${RVIZ_DIR}':/rviz_cfg \
        slam-base:latest \
        bash -c 'source /opt/ros/humble/setup.bash && rviz2 -d ${RVIZ_FILE}'"

    sleep 2

    # 3. Start Rosbag Player in Terminal 3
    "${REPO_ROOT}/scripts/launch_terminal.sh" "[3] Rosbag Player" \
      "docker run --rm --name suedhoehe_player -it \
        --net=host --ipc=host \
        -v '${BAG_DIR}':/dataset_dir \
        slam-base:latest \
        bash -c 'source /opt/ros/humble/setup.bash && ros2 bag play /dataset_dir/${BAG_NAME}'"

else
    echo "[1/3] Starting cuVSLAM container with GPU passthrough..."
    docker run -d --name cuvslam_node_run \
      --cpus="${CPUS}" --memory="${MEMORY}" \
      --runtime=nvidia --gpus all --net=host --ipc=host \
      -v "${RESULTS_DIR}":/results \
      -v "${BAG_DIR}":/dataset_dir \
      -v "${ISAAC_WS}":/workspaces/isaac_ros-dev \
      -v "${REPO_ROOT}/scripts":/scripts \
      slam-base:latest \
      bash -c "source /opt/ros/humble/setup.bash && \
               source /workspaces/isaac_ros-dev/install/setup.bash && \
               export LD_LIBRARY_PATH=/workspaces/isaac_ros-dev/install/isaac_ros_visual_slam/share/cuvslam/lib:\$LD_LIBRARY_PATH && \
               ros2 launch isaac_ros_visual_slam ${LAUNCH_FILE}"

    echo "[2/3] Waiting for cuVSLAM node to initialize and starting trajectory recorder..."
    sleep 5

    # Start trajectory recorder inside the same container
    docker exec -d cuvslam_node_run bash -c \
      "source /opt/ros/humble/setup.bash && python3 /scripts/cuvslam_save_trajectory.py /results/cuvslam_tum.txt"

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
fi
