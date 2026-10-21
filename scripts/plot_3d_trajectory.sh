#!/usr/bin/env bash
# ==============================================================================
# Plot 3D Trajectory vs Ground Truth (evo_traj & evo_ape)
# ==============================================================================
# Supports:
#   Algorithms: openvins, cuvslam, orbslam3, orbslam3_klt, kimera
#   Datasets:   euroc / MH_01_easy, suedhoehe / schnee
#
# Usage:
#   ./scripts/plot_3d_trajectory.sh [algorithm] [dataset] [--gui]
#
# Examples:
#   ./scripts/plot_3d_trajectory.sh openvins MH_01_easy
#   ./scripts/plot_3d_trajectory.sh openvins schnee
#   ./scripts/plot_3d_trajectory.sh openvins MH_01_easy --gui
# ==============================================================================

set -e

REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/.." && pwd)"

ALGO="${1:-openvins}"
DATASET="${2:-euroc}"
SHOW_GUI=false

for arg in "$@"; do
    case "$arg" in
        --gui|-g|-p|--plot)
            SHOW_GUI=true
            ;;
    esac
done

# Normalize algorithm
case "$ALGO" in
    openvins*|ov*)
        ALGO="openvins"
        ;;
    cuvslam*)
        ALGO="cuvslam"
        ;;
    orbslam3_klt*|klt*)
        ALGO="orbslam3_klt"
        ;;
    orbslam3*)
        ALGO="orbslam3"
        ;;
    kimera*)
        ALGO="kimera"
        ;;
    *)
        ALGO="openvins"
        ;;
esac

# Normalize dataset
case "$DATASET" in
    euroc*|mh01*|MH_01*|MH01*)
        DATASET="euroc"
        GT_FILE="/repo/datasets/MH_01_easy/gt_tum.txt"
        ;;
    suedhoehe*|schnee*|snow*)
        DATASET="suedhoehe"
        GT_FILE="/repo/datasets/suedhoehe_gps_schnee_02/gps_trajectory.txt"
        ;;
    *)
        DATASET="euroc"
        GT_FILE="/repo/datasets/MH_01_easy/gt_tum.txt"
        ;;
esac

# Resolve trajectory path
TRAJ_FILE=""
if [ "$ALGO" = "openvins" ]; then
    if [ "$DATASET" = "euroc" ]; then
        if [ -f "${REPO_ROOT}/results/euroc/openvins/openvins_tum.txt" ]; then
            TRAJ_FILE="/repo/results/euroc/openvins/openvins_tum.txt"
        elif [ -f "${REPO_ROOT}/results/euroc/openvins/ov_estimate.txt" ]; then
            python3 "${REPO_ROOT}/scripts/convert_openvins_to_tum.py" \
                "${REPO_ROOT}/results/euroc/openvins/ov_estimate.txt" \
                "${REPO_ROOT}/results/euroc/openvins/openvins_tum.txt"
            TRAJ_FILE="/repo/results/euroc/openvins/openvins_tum.txt"
        elif [ -f "${REPO_ROOT}/results/euroc/MH_01_easy/open_vins.txt" ]; then
            python3 "${REPO_ROOT}/scripts/convert_openvins_to_tum.py" \
                "${REPO_ROOT}/results/euroc/MH_01_easy/open_vins.txt" \
                "${REPO_ROOT}/results/euroc/openvins/openvins_tum.txt"
            TRAJ_FILE="/repo/results/euroc/openvins/openvins_tum.txt"
        fi
    else
        if [ -f "${REPO_ROOT}/results/suedhoehe/openvins/openvins_tum.txt" ]; then
            TRAJ_FILE="/repo/results/suedhoehe/openvins/openvins_tum.txt"
        elif [ -f "${REPO_ROOT}/results/suedhoehe/openvins/ov_estimate.txt" ]; then
            python3 "${REPO_ROOT}/scripts/convert_openvins_to_tum.py" \
                "${REPO_ROOT}/results/suedhoehe/openvins/ov_estimate.txt" \
                "${REPO_ROOT}/results/suedhoehe/openvins/openvins_tum.txt"
            TRAJ_FILE="/repo/results/suedhoehe/openvins/openvins_tum.txt"
        fi
    fi
elif [ "$ALGO" = "cuvslam" ]; then
    if [ "$DATASET" = "euroc" ]; then
        TRAJ_FILE="/repo/results/euroc/MH_01_easy/cuvslam_tum.txt"
    else
        TRAJ_FILE="/repo/results/suedhoehe/cuvslam/cuvslam_tum.txt"
    fi
elif [ "$ALGO" = "orbslam3" ]; then
    TRAJ_FILE="/repo/results/euroc/orbslam3/orbslam3_tum.txt"
elif [ "$ALGO" = "orbslam3_klt" ]; then
    TRAJ_FILE="/repo/results/euroc/orbslam3_klt/orbslam3_klt_tum.txt"
elif [ "$ALGO" = "kimera" ]; then
    if [ "$DATASET" = "euroc" ]; then
        TRAJ_FILE="/repo/results/euroc/kimera/kimera_tum.txt"
    else
        TRAJ_FILE="/repo/results/suedhoehe/kimera/kimera_tum.txt"
    fi
fi

if [ -z "$TRAJ_FILE" ] || [ ! -f "${REPO_ROOT}${TRAJ_FILE#/repo}" ]; then
    echo "[ERROR] Trajectory file not found for ${ALGO} on ${DATASET}."
    echo "Please run the benchmark first: ./run_benchmark.sh ${ALGO} ${DATASET}"
    exit 1
fi

HOST_TRAJ_FILE="${REPO_ROOT}${TRAJ_FILE#/repo}"
HOST_GT_FILE="${REPO_ROOT}${GT_FILE#/repo}"

if [ ! -f "$HOST_GT_FILE" ]; then
    echo "[ERROR] Ground truth file not found: $HOST_GT_FILE"
    exit 1
fi

OUT_DIR="$(dirname "$HOST_TRAJ_FILE")"
OUT_PREFIX="${OUT_DIR}/${ALGO}_3d"
CONTAINER_DIR="$(dirname "$TRAJ_FILE")"
CONTAINER_OUT_PREFIX="${CONTAINER_DIR}/${ALGO}_3d.png"

echo "=========================================================="
echo " Evaluating 3D Trajectory vs Ground Truth"
echo " Algorithm:    $ALGO"
echo " Dataset:      $DATASET"
echo " Trajectory:   $HOST_TRAJ_FILE"
echo " Ground Truth: $HOST_GT_FILE"
echo " Output Plots: ${OUT_PREFIX}_*.png"
echo "=========================================================="

if [ "$SHOW_GUI" = true ]; then
    xhost +local:root 2>/dev/null || xhost + 2>/dev/null || true
    docker run --rm \
      -e DISPLAY="${DISPLAY}" -v /tmp/.X11-unix:/tmp/.X11-unix \
      -v "${REPO_ROOT}":/repo \
      -v "${REPO_ROOT}/workspace/.python_deps":/deps \
      slam-base:latest \
      bash -c "export PYTHONPATH=/deps && \
        echo '=== 1. Absolute Pose Error (SE3 Umeyama Alignment) ===' && \
        python3 /deps/bin/evo_ape tum --no_warnings '${GT_FILE}' '${TRAJ_FILE}' -va --t_max_diff 0.05 && \
        echo '=== 2. Opening Interactive 3D Trajectory Plot Viewer ===' && \
        python3 /deps/bin/evo_traj tum --no_warnings '${TRAJ_FILE}' --ref='${GT_FILE}' -va --t_max_diff 0.05 -p --plot_mode=xyz \
          --save_plot='${CONTAINER_OUT_PREFIX}'"
else
    docker run --rm \
      -v "${REPO_ROOT}":/repo \
      -v "${REPO_ROOT}/workspace/.python_deps":/deps \
      slam-base:latest \
      bash -c "export PYTHONPATH=/deps && \
        echo '=== 1. Absolute Pose Error (SE3 Umeyama Alignment) ===' && \
        python3 /deps/bin/evo_ape tum --no_warnings '${GT_FILE}' '${TRAJ_FILE}' -va --t_max_diff 0.05 && \
        echo '=== 2. Generating 3D Trajectory Plots ===' && \
        python3 /deps/bin/evo_traj tum --no_warnings '${TRAJ_FILE}' --ref='${GT_FILE}' -va --t_max_diff 0.05 --plot_mode=xyz \
          --save_plot='${CONTAINER_OUT_PREFIX}'"
fi

echo ""
echo "[✔] Done! 3D trajectory plots saved to:"
echo "    ${OUT_PREFIX}_trajectories.png"
echo "    ${OUT_PREFIX}_xyz.png"
echo "    ${OUT_PREFIX}_rpy.png"
echo "    ${OUT_PREFIX}_speeds.png"
