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

# Parse CLI arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --cpus)
            CPUS="$2"
            shift 2
            ;;
        --memory|-m)
            MEMORY="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [dataset_target] [--cpus <N>] [--memory <MEM>]"
            echo ""
            echo "Arguments:"
            echo "  dataset_target       Target dataset: suedhoehe, euroc_MH01, or custom bag path (default: suedhoehe)"
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

mkdir -p "$RESULTS_DIR"

if [ "$TARGET" == "suedhoehe" ]; then
    BAG_PATH="${DATASETS_DIR}/suedhoehe_gps_schnee_02"
    PARAMS_PATH="${REPO_ROOT}/suedhoehe_kimera_params"
elif [ "$TARGET" == "euroc_MH01" ]; then
    BAG_PATH="${DATASETS_DIR}/Euroc/machine_hall/MH_01_easy/MH_01_easy_ros2"
    PARAMS_PATH="${REPO_ROOT}/workspace/kimera_ws/src/Kimera-VIO/params/Euroc"
else
    BAG_PATH="$TARGET"
    PARAMS_PATH="${REPO_ROOT}/suedhoehe_kimera_params"
fi

echo "=========================================================="
echo " Kimera-VIO Benchmark"
echo " Target Dataset : $BAG_PATH"
echo " Output Folder  : $RESULTS_DIR"
echo " Base Image     : slam-base:latest (ROS 2, OpenCV, GTSAM)"
echo " Resource Limits: ${CPUS} Cores Max, ${MEMORY} RAM Max"
echo "=========================================================="

BAG_DIR="$(dirname "$(realpath "$BAG_PATH")")"
BAG_NAME="$(basename "$BAG_PATH")"

docker run --rm \
  --cpus="${CPUS}" --memory="${MEMORY}" \
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
