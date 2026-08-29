#!/bin/bash
# ==============================================================================
# SLAM & VIO Benchmark Master Runner
# ==============================================================================
# Single-command launcher for evaluating:
#   - NVIDIA cuVSLAM (GPU-Accelerated)
#   - OpenVINS (MSCKF Filter)
#   - ORB-SLAM3 (Feature-Based Keyframe BA Baseline)
#   - ORB-SLAM3 Hybrid KLT (Dual-Rate Optical Flow SLAM)
#   - Kimera-VIO (Factor-Graph Smoothing)
#
# Usage:
#   ./run_benchmark.sh --algorithm orbslam3_klt --dataset euroc
#   ./run_benchmark.sh --algorithm cuvslam --dataset suedhoehe
#   ./run_benchmark.sh --algorithm all --dataset all
#   ./run_benchmark.sh --evaluate
#   ./run_benchmark.sh --help
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_RUNNER="${SCRIPT_DIR}/run_unified_benchmark.py"

# Make sure runner is executable
chmod +x "$PYTHON_RUNNER" 2>/dev/null || true

# Check for Docker installation
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed or not in PATH."
    exit 1
fi

# Print banner
echo "=========================================================="
echo "       SLAM & VIO Benchmark Suite — Master Runner         "
echo "=========================================================="
echo " Repository: ${REPO_ROOT}"
echo " Date/Time : $(date)"
echo " GPU Device: $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'No NVIDIA GPU detected')"
echo "=========================================================="

# Pass arguments to the python unified benchmark orchestrator
python3 "$PYTHON_RUNNER" "$@"
