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
        if [ -f "${REPO_ROOT}/results/euroc/openvins/ov_estimate.txt" ]; then
            python3 "${REPO_ROOT}/scripts/convert_openvins_to_tum.py" \
                "${REPO_ROOT}/results/euroc/openvins/ov_estimate.txt" \
                "${REPO_ROOT}/results/euroc/openvins/openvins_tum.txt"
            TRAJ_FILE="/repo/results/euroc/openvins/openvins_tum.txt"
        elif [ -f "${REPO_ROOT}/results/euroc/openvins/openvins_tum.txt" ]; then
            TRAJ_FILE="/repo/results/euroc/openvins/openvins_tum.txt"
        elif [ -f "${REPO_ROOT}/results/euroc/MH_01_easy/open_vins.txt" ]; then
            python3 "${REPO_ROOT}/scripts/convert_openvins_to_tum.py" \
                "${REPO_ROOT}/results/euroc/MH_01_easy/open_vins.txt" \
                "${REPO_ROOT}/results/euroc/openvins/openvins_tum.txt"
            TRAJ_FILE="/repo/results/euroc/openvins/openvins_tum.txt"
        fi
    else
        if [ -f "${REPO_ROOT}/results/suedhoehe/openvins/ov_estimate.txt" ]; then
            python3 "${REPO_ROOT}/scripts/convert_openvins_to_tum.py" \
                "${REPO_ROOT}/results/suedhoehe/openvins/ov_estimate.txt" \
                "${REPO_ROOT}/results/suedhoehe/openvins/openvins_tum.txt"
            TRAJ_FILE="/repo/results/suedhoehe/openvins/openvins_tum.txt"
        elif [ -f "${REPO_ROOT}/results/suedhoehe/openvins/openvins_tum.txt" ]; then
            TRAJ_FILE="/repo/results/suedhoehe/openvins/openvins_tum.txt"
        fi
    fi
elif [ "$ALGO" = "cuvslam" ]; then
    if [ "$DATASET" = "euroc" ]; then
        if [ -f "${REPO_ROOT}/results/euroc/cuvslam/cuvslam_tum.txt" ]; then
            TRAJ_FILE="/repo/results/euroc/cuvslam/cuvslam_tum.txt"
        elif [ -f "${REPO_ROOT}/results/euroc/MH_01_easy/cuvslam_tum.txt" ]; then
            TRAJ_FILE="/repo/results/euroc/MH_01_easy/cuvslam_tum.txt"
        elif [ -f "${REPO_ROOT}/results/euroc/cuvslam_tum.txt" ]; then
            TRAJ_FILE="/repo/results/euroc/cuvslam_tum.txt"
        fi
    else
        if [ -f "${REPO_ROOT}/results/suedhoehe/cuvslam/cuvslam_tum.txt" ]; then
            TRAJ_FILE="/repo/results/suedhoehe/cuvslam/cuvslam_tum.txt"
        else
            echo "[INFO] cuVSLAM was not evaluated on Suedhoehe (per Thesis Table 6.3)."
            exit 0
        fi
    fi
elif [ "$ALGO" = "orbslam3" ]; then
    if [ "$DATASET" = "euroc" ]; then
        if [ -f "${REPO_ROOT}/results/euroc/orbslam3/orbslam3_tum.txt" ]; then
            TRAJ_FILE="/repo/results/euroc/orbslam3/orbslam3_tum.txt"
        elif [ -f "${REPO_ROOT}/results/euroc/orbslam3/orbslam3_raw.txt" ]; then
            TRAJ_FILE="/repo/results/euroc/orbslam3/orbslam3_raw.txt"
        elif [ -f "${REPO_ROOT}/results/euroc/orb_slam3.txt" ]; then
            TRAJ_FILE="/repo/results/euroc/orb_slam3.txt"
        fi
    else
        echo "[INFO] ORB-SLAM3 is evaluated on EuRoC. On Suedhoehe snow, tracking repeatedly failed (per Thesis Table 6.3)."
        exit 0
    fi
elif [ "$ALGO" = "orbslam3_klt" ]; then
    if [ "$DATASET" = "euroc" ]; then
        if [ -f "${REPO_ROOT}/results/euroc/orbslam3_klt/orbslam3_klt_tum.txt" ]; then
            TRAJ_FILE="/repo/results/euroc/orbslam3_klt/orbslam3_klt_tum.txt"
        elif [ -f "${REPO_ROOT}/results/orbslam3_klt/klt_trajectory.txt" ]; then
            TRAJ_FILE="/repo/results/orbslam3_klt/klt_trajectory.txt"
        elif [ -f "${REPO_ROOT}/results/orbslam3_klt/orbslam3_klt_raw.txt" ]; then
            TRAJ_FILE="/repo/results/orbslam3_klt/orbslam3_klt_raw.txt"
        fi
    else
        echo "[INFO] ORB-SLAM3 KLT is evaluated on EuRoC. On Suedhoehe snow, tracking repeatedly failed (per Thesis Table 6.3)."
        exit 0
    fi
elif [ "$ALGO" = "kimera" ]; then
    if [ "$DATASET" = "euroc" ]; then
        if [ -f "${REPO_ROOT}/results/euroc/kimera/output_lcd_optimized_traj.csv" ]; then
            python3 "${REPO_ROOT}/scripts/convert_kimera_to_tum.py" \
                "${REPO_ROOT}/results/euroc/kimera/output_lcd_optimized_traj.csv" \
                "${REPO_ROOT}/results/euroc/kimera/kimera_tum.txt"
            TRAJ_FILE="/repo/results/euroc/kimera/kimera_tum.txt"
        elif [ -f "${REPO_ROOT}/results/euroc/kimera/kimera_tum.txt" ]; then
            TRAJ_FILE="/repo/results/euroc/kimera/kimera_tum.txt"
        elif [ -f "${REPO_ROOT}/results/euroc/kimera/traj_vio.csv" ]; then
            python3 "${REPO_ROOT}/scripts/convert_kimera_to_tum.py" \
                "${REPO_ROOT}/results/euroc/kimera/traj_vio.csv" \
                "${REPO_ROOT}/results/euroc/kimera/kimera_tum.txt"
            TRAJ_FILE="/repo/results/euroc/kimera/kimera_tum.txt"
        elif [ -f "${REPO_ROOT}/results/euroc/kimera/output_posesVIO.csv" ]; then
            python3 "${REPO_ROOT}/scripts/convert_kimera_to_tum.py" \
                "${REPO_ROOT}/results/euroc/kimera/output_posesVIO.csv" \
                "${REPO_ROOT}/results/euroc/kimera/kimera_tum.txt"
            TRAJ_FILE="/repo/results/euroc/kimera/kimera_tum.txt"
        fi
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

ALIGN_FLAGS="-va"
if [ "$ALGO" = "orbslam3_klt" ]; then
    ALIGN_FLAGS="-vas"
fi

if [ "$SHOW_GUI" = true ]; then
    xhost +local:root 2>/dev/null || xhost + 2>/dev/null || true
    docker run --rm \
      -e DISPLAY="${DISPLAY}" -v /tmp/.X11-unix:/tmp/.X11-unix \
      -v "${REPO_ROOT}":/repo \
      -v "${REPO_ROOT}/workspace/.python_deps":/deps \
      slam-base:latest \
      bash -c "export PYTHONPATH=/deps && \
        echo '=== 1. Absolute Pose Error (Umeyama Alignment) ===' && \
        python3 /deps/bin/evo_ape tum --no_warnings '${GT_FILE}' '${TRAJ_FILE}' ${ALIGN_FLAGS} --t_max_diff 0.05 \
          --save_results='${CONTAINER_DIR}/${ALGO}_ape.zip' | tee '${CONTAINER_DIR}/${ALGO}_ape_stats.txt' && \
        echo '=== 2. Opening Interactive 3D Trajectory Plot Viewer ===' && \
        python3 /deps/bin/evo_traj tum --no_warnings '${TRAJ_FILE}' --ref='${GT_FILE}' ${ALIGN_FLAGS} --t_max_diff 0.05 -p --plot_mode=xyz \
          --save_plot='${CONTAINER_OUT_PREFIX}'"
else
    docker run --rm \
      -v "${REPO_ROOT}":/repo \
      -v "${REPO_ROOT}/workspace/.python_deps":/deps \
      slam-base:latest \
      bash -c "export PYTHONPATH=/deps && \
        echo '=== 1. Absolute Pose Error (Umeyama Alignment) ===' && \
        python3 /deps/bin/evo_ape tum --no_warnings '${GT_FILE}' '${TRAJ_FILE}' ${ALIGN_FLAGS} --t_max_diff 0.05 \
          --save_results='${CONTAINER_DIR}/${ALGO}_ape.zip' | tee '${CONTAINER_DIR}/${ALGO}_ape_stats.txt' && \
        echo '=== 2. Generating 3D Trajectory Plots ===' && \
        python3 /deps/bin/evo_traj tum --no_warnings '${TRAJ_FILE}' --ref='${GT_FILE}' ${ALIGN_FLAGS} --t_max_diff 0.05 --plot_mode=xyz \
          --save_plot='${CONTAINER_OUT_PREFIX}'"
fi

# Ensure Gantt chart is present in the results folder
GANTT_SRC=""
case "$ALGO" in
    openvins)     GANTT_SRC="${REPO_ROOT}/figures/1_openvins_gantt_chart.png" ;;
    kimera)       GANTT_SRC="${REPO_ROOT}/figures/2_kimera_gantt_chart.png" ;;
    orbslam3)     GANTT_SRC="${REPO_ROOT}/figures/3_orbslam3_gantt_chart.png" ;;
    orbslam3_klt) GANTT_SRC="${REPO_ROOT}/figures/5_orbslam3_klt_gantt_chart.png" ;;
    cuvslam*)     GANTT_SRC="${REPO_ROOT}/figures/4_cuvslam_gantt_chart.png" ;;
esac
if [ ! -f "$GANTT_SRC" ]; then
    case "$ALGO" in
        openvins)    GANTT_SRC="${REPO_ROOT}/gantt_charts/1_openvins_gantt_chart.png" ;;
        kimera)      GANTT_SRC="${REPO_ROOT}/gantt_charts/2_kimera_gantt_chart.png" ;;
        orbslam3)    GANTT_SRC="${REPO_ROOT}/gantt_charts/3_orbslam3_gantt_chart.png" ;;
        orbslam3_klt) GANTT_SRC="${REPO_ROOT}/gantt_charts/5_orbslam3_klt_gantt_chart.png" ;;
        cuvslam*)     GANTT_SRC="${REPO_ROOT}/gantt_charts/4_cuvslam_gantt_chart.png" ;;
    esac
fi
if [ -f "$GANTT_SRC" ]; then
    cp -f "$GANTT_SRC" "${OUT_DIR}/gantt_chart.png"
fi

echo ""
echo "[✔] Done! Evaluation results saved to ${OUT_DIR}/:"
echo "    - 3D Trajectory Plot: ${OUT_PREFIX}_trajectories.png"
echo "    - Coordinate Errors:  ${OUT_PREFIX}_xyz.png"
echo "    - Orientation Errors: ${OUT_PREFIX}_rpy.png"
echo "    - Speed Profiles:     ${OUT_PREFIX}_speeds.png"
echo "    - APE Results (zip):  ${OUT_DIR}/${ALGO}_ape.zip"
echo "    - APE Summary Text:   ${OUT_DIR}/${ALGO}_ape_stats.txt"
if [ -f "${OUT_DIR}/gantt_chart.png" ]; then
    echo "    - Gantt Chart:        ${OUT_DIR}/gantt_chart.png"
fi
