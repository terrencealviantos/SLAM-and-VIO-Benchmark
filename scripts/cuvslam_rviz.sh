#!/usr/bin/env bash
# Helper script to launch RViz2 inside the Isaac ROS Docker container

set -e

CONTAINER_NAME="isaac_ros_dev-x86_64-container"

if [ ! "$(docker ps -q -f name=${CONTAINER_NAME})" ]; then
    echo "[ERROR] Docker container '${CONTAINER_NAME}' is not running."
    echo "Please start the container first."
    exit 1
fi

echo "[INFO] Launching RViz2 with RealSense / SLAM configuration..."
docker exec -it "${CONTAINER_NAME}" bash -i -c "run_rviz"
