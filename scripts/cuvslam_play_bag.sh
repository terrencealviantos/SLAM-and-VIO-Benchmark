#!/usr/bin/env bash
# Helper script to play Suedhoehe dataset bag inside the container

set -e

CONTAINER_NAME="isaac_ros_dev-x86_64-container"
RATE="${1:-1.0}"

if [ ! "$(docker ps -q -f name=${CONTAINER_NAME})" ]; then
    echo "[ERROR] Docker container '${CONTAINER_NAME}' is not running."
    echo "Please start the container first."
    exit 1
fi

echo "[INFO] Playing Suedhoehe dataset bag at rate: ${RATE}x..."
docker exec -it "${CONTAINER_NAME}" bash -i -c "ros2 bag play /workspaces/isaac_ros-dev/datasets/suedhoehe_gps_schnee_02 -r ${RATE}"
