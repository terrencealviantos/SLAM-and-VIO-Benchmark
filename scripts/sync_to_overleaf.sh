#!/bin/bash
set -e

OVERLEAF_DIR="/home/boris/.overleaf_slam_repo"
BENCHMARK_DIR="/home/boris/SLAM-and-VIO-Benchmark"

echo "=== Syncing to TU Dresden Overleaf ==="

# Copy updated main.tex and figures
cp "$BENCHMARK_DIR/main.tex" "$OVERLEAF_DIR/main.tex"
if [ -f "$BENCHMARK_DIR/original_main.tex" ]; then
    cp "$BENCHMARK_DIR/original_main.tex" "$OVERLEAF_DIR/original_main.tex"
fi
cp "$BENCHMARK_DIR/figures/"*.png "$OVERLEAF_DIR/"

cd "$OVERLEAF_DIR"

git add -A
if git diff-index --quiet HEAD --; then
    echo "No changes to push. Overleaf is already up to date!"
else
    COMMIT_MSG="${1:-Update paper and benchmark figures from workspace}"
    git commit -m "$COMMIT_MSG"
    git push origin main
    echo "Successfully pushed latest changes to TU Dresden Overleaf!"
fi
