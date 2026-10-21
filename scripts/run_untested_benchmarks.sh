#!/usr/bin/env bash
# Script to run all untested benchmark combinations and record trajectories
set -e

REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")/.." && pwd)"
RESULTS_DIR="${REPO_ROOT}/results"

echo "=========================================================="
echo " Preparing Untested SLAM & VIO Benchmarks"
echo "=========================================================="

# 1. Convert EuRoC datasets to ROS 2 MCAP bags if needed
for seq in MH_01_easy V1_03_difficult; do
    seq_dir="${REPO_ROOT}/datasets/${seq}"
    mav0="${seq_dir}/mav0"
    bag="${seq_dir}/${seq}_ros2"
    gt_tum="${seq_dir}/gt_tum.txt"
    
    if [ -d "$mav0" ]; then
        if [ ! -d "$bag" ]; then
            echo "[Conversion] Creating ROS 2 MCAP bag for $seq..."
            docker run --rm --entrypoint "" \
              -v "${REPO_ROOT}":/repo \
              slam-base:latest \
              bash -c "source /opt/ros/humble/setup.bash && python3 /repo/scripts/euroc_to_ros2bag.py /repo/datasets/${seq}/mav0 /repo/datasets/${seq}/${seq}_ros2"
        fi
        if [ ! -f "$gt_tum" ]; then
            echo "[Ground Truth] Converting GT for $seq..."
            gt_csv="${mav0}/state_groundtruth_estimate0/data.csv"
            [ -f "$gt_csv" ] && python3 "${REPO_ROOT}/scripts/euroc_gt_to_tum.py" "$gt_csv" "$gt_tum" 2>/dev/null || true
        fi
    fi
done

echo "[✔] Setup verification complete."
