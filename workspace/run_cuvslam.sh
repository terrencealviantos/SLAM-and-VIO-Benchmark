#!/bin/bash
# Launcher for NVIDIA cuVSLAM in the ROS2 Humble workspace.
# Run this on your NVIDIA GPU-enabled PC or Jetson board.

# Locate workspace root directory
WORKSPACE_DIR="/home/terrence/researchProject/workspace/isaac_ros_ws"

if [ ! -d "$WORKSPACE_DIR" ]; then
  echo "Error: Directory $WORKSPACE_DIR does not exist."
  exit 1
fi

echo "=========================================================="
echo "NVIDIA cuVSLAM Launcher"
echo "=========================================================="
echo "NOTE: This container requires an NVIDIA GPU and the NVIDIA"
echo "      Container Toolkit configured on the host."
echo "=========================================================="

# Export workspace path for isaac_ros_common scripts
export ISAAC_ROS_WS="$WORKSPACE_DIR"

# Allow docker local container connection to X11 server for displays
xhost +local:docker &>/dev/null || true

# Run the development container
echo "Starting Isaac ROS Humble Development container..."
cd "$WORKSPACE_DIR/src/isaac_ros_common"
./scripts/run_dev.sh
