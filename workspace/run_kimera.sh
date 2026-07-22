#!/bin/bash
# run_kimera.sh
# Script to run Kimera-VIO-ROS2 on the suedhoehe dataset and convert the trajectory output

set -e

RESULTS_DIR="/home/terrence/researchProject/results"
DATASETS_DIR="/home/terrence/researchProject/datasets"
PARAMS_DIR="/home/terrence/researchProject/suedhoehe_kimera_params"
LAUNCH_FILE="/home/terrence/researchProject/workspace/kimera_ws/src/Kimera-VIO-ROS2/kimera_vio_ros/launch/kimera_vio_ros.launch.xml"

# Make sure results directory exists
mkdir -p "$RESULTS_DIR"

# Clean any existing traj_vio.csv
rm -f "$RESULTS_DIR/traj_vio.csv"

echo "=== Starting Kimera-VIO-ROS2 Container ==="
docker run -d --name kimera_run --net=host \
  -v "$RESULTS_DIR":/results \
  -v "$PARAMS_DIR":/suedhoehe_kimera_params \
  -v "$LAUNCH_FILE":/opt/ros/wrapper_ws/install/kimera_vio_ros/share/kimera_vio_ros/launch/kimera_vio_ros.launch.xml \
  kimera_vio_ros2:latest \
  ros2 launch kimera_vio_ros kimera_vio_ros.launch.xml \
    dataset_name:=Suedhoehe \
    params_folder:=/suedhoehe_kimera_params \
    use_camera_info:=false \
    topic.left.image:=/camera/infra1/image_rect_raw \
    topic.right.image:=/camera/infra2/image_rect_raw \
    topic.imu.data:=/camera/imu \
    log_output:=true \
    log_output_path:=/results/

# Wait a few seconds for the VIO node to initialize and start spinning
echo "Waiting for Kimera VIO node to initialize..."
sleep 5

# Start playing the bag file
echo "=== Playing Suedhoehe MCAP Bag File ==="
docker run --rm --name bag_player --net=host \
  -v "$DATASETS_DIR":/datasets \
  ros:humble \
  bash -c "apt-get update && apt-get install -y ros-humble-rosbag2-storage-mcap && source /opt/ros/humble/setup.bash && ros2 bag play /datasets/suedhoehe_gps_schnee_02"

echo "=== Bag play finished ==="
echo "Giving VIO node 5 seconds to process remaining queue..."
sleep 5

# Stop Kimera VIO container
echo "Stopping Kimera VIO container..."
docker kill kimera_run || true
docker rm kimera_run || true

# Convert traj_vio.csv to TUM format (kimera.txt)
CSV_FILE="$RESULTS_DIR/traj_vio.csv"
TXT_FILE="$RESULTS_DIR/kimera.txt"

if [ -f "$CSV_FILE" ]; then
  echo "=== Converting traj_vio.csv to TUM format (kimera.txt) ==="
  python3 -c "
import csv
with open('$CSV_FILE', 'r') as f_in, open('$TXT_FILE', 'w') as f_out:
    reader = csv.reader(f_in)
    header = next(reader) # Skip header
    for row in reader:
        if not row or row[0].startswith('#'):
            continue
        # csv: timestamp,x,y,z,qw,qx,qy,qz,vx,vy,vz,bgx,bgy,bgz,bax,bay,baz
        # tum: timestamp tx ty tz qx qy qz qw
        timestamp_sec = float(row[0]) / 1e9
        tx, ty, tz = row[1], row[2], row[3]
        qw, qx, qy, qz = row[4], row[5], row[6], row[7]
        f_out.write(f'{timestamp_sec:.6f} {tx} {ty} {tz} {qx} {qy} {qz} {qw}\n')
"
  echo "TUM trajectory saved to: $TXT_FILE"
  echo "VIO run finished successfully!"
else
  echo "Error: traj_vio.csv was not generated. Please check container logs."
  exit 1
fi
