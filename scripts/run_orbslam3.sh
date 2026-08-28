#!/bin/bash
# ==============================================================================
# ORB-SLAM3 Benchmark Launcher
# ==============================================================================
# Single-command launcher for running ORB-SLAM3 in the ROS 2 environment.
#
# Usage:
#   ./scripts/run_orbslam3.sh [suedhoehe | euroc_MH01 | /path/to/dataset]
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Defaults (can be overridden via CLI flags or env vars)
CPUS="${CPUS:-2}"
MEMORY="${MEMORY:-3g}"
TARGET="euroc_MH01"
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
            echo "  dataset_target       Target dataset: euroc_MH01, suedhoehe, or custom directory (default: euroc_MH01)"
            echo "  --gui, --view, -g    Open live Pangolin 3D SLAM visualizer window & interactive terminal"
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
RESULTS_DIR="${REPO_ROOT}/results/${TARGET}/orbslam3"
DATASETS_DIR="${REPO_ROOT}/datasets"
ORBSLAM_WS="${REPO_ROOT}/workspace/orbslam3_ws"

mkdir -p "$RESULTS_DIR"

if [ "$TARGET" == "euroc_MH01" ]; then
    DATASET_PATH="${DATASETS_DIR}/Euroc/machine_hall/MH_01_easy"
    CONFIG_YAML="/opt/ORB_SLAM3/Examples/Stereo-Inertial/EuRoC.yaml"
elif [ "$TARGET" == "suedhoehe" ]; then
    DATASET_PATH="${DATASETS_DIR}/suedhoehe_gps_schnee_02"
    CONFIG_YAML="/orbslam3_ws/suedhoehe_mono.yaml"
else
    DATASET_PATH="$TARGET"
    CONFIG_YAML="/opt/ORB_SLAM3/Examples/Stereo-Inertial/EuRoC.yaml"
fi

echo "=========================================================="
echo " ORB-SLAM3 Benchmark"
echo " Target Dataset : $DATASET_PATH"
echo " Output Folder  : $RESULTS_DIR"
echo " Base Image     : slam-base:latest (ROS 2, OpenCV, Pangolin)"
echo " Resource Limits: ${CPUS} Cores Max, ${MEMORY} RAM Max"
echo " GUI Viewer Mode: $ENABLE_GUI"
echo "=========================================================="

# Allow X11 access for Docker Pangolin GUI
xhost +local:root 2>/dev/null || xhost + 2>/dev/null || true

if [ "$ENABLE_GUI" = true ]; then
    echo "[INFO] Multi-Terminal GUI Mode Enabled: Launching ORB-SLAM3 with live Pangolin 3D Viewer..."
    "${REPO_ROOT}/scripts/launch_terminal.sh" "ORB-SLAM3 [Pangolin 3D SLAM GUI]" \
      "docker run --rm --entrypoint '' -it \
        --cpus=${CPUS} --memory=${MEMORY} \
        --net=host --ipc=host \
        -e DISPLAY=${DISPLAY} -e QT_X11_NO_MITSHM=1 -v /tmp/.X11-unix:/tmp/.X11-unix \
        -v '${ORBSLAM_WS}':/orbslam3_ws \
        -v '${DATASET_PATH}':/dataset \
        -v '${RESULTS_DIR}':/results \
        slam-base:latest \
        bash -c 'source /opt/ros/humble/setup.bash && \
                 if [ -f /dataset/timestamps.txt ]; then \
                   /opt/ORB_SLAM3/Examples/Stereo-Inertial/stereo_inertial_euroc \
                     /opt/ORB_SLAM3/Vocabulary/ORBvoc.txt \
                     ${CONFIG_YAML} \
                     /dataset /dataset/timestamps.txt /results/orbslam3_raw.txt; \
                 fi'"
else
    docker run --rm --entrypoint "" \
      --cpus="${CPUS}" --memory="${MEMORY}" \
      -v "${ORBSLAM_WS}":/orbslam3_ws \
      -v "${DATASET_PATH}":/dataset \
      -v "${RESULTS_DIR}":/results \
      slam-base:latest \
      bash -c "source /opt/ros/humble/setup.bash && \
               if [ -f /dataset/timestamps.txt ]; then \
                 /opt/ORB_SLAM3/Examples/Stereo-Inertial/stereo_inertial_euroc \
                   /opt/ORB_SLAM3/Vocabulary/ORBvoc.txt \
                   ${CONFIG_YAML} \
                   /dataset /dataset/timestamps.txt /results/orbslam3_raw.txt; \
               fi"

    echo "=========================================================="
    echo " ORB-SLAM3 run completed!"
    echo " Results saved to: ${RESULTS_DIR}/orbslam3_raw.txt"
    echo "=========================================================="
fi
