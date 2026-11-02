#!/usr/bin/env python3
"""Extract stereo images and IMU from TUM-VI Corridor ROS 2 MCAP bag to ASL / EuRoC format.

Creates:
  datasets/tum_vi_corridor1/mav0/cam0/data/<timestamp_ns>.png
  datasets/tum_vi_corridor1/mav0/cam0/data.csv
  datasets/tum_vi_corridor1/mav0/cam1/data/<timestamp_ns>.png
  datasets/tum_vi_corridor1/mav0/cam1/data.csv
  datasets/tum_vi_corridor1/mav0/imu0/data.csv
  datasets/tum_vi_corridor1/timestamps.txt
  datasets/tum_vi_corridor1/gt_tum.txt
"""

import os
import sys
import csv
import cv2
import numpy as np

import rclpy
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import Image, Imu
from geometry_msgs.msg import TransformStamped
import rosbag2_py

def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bag_path = os.path.join(repo_root, "datasets", "tum_vi_corridor1", "corridor1_ros2")
    output_dir = os.path.join(repo_root, "datasets", "tum_vi_corridor1")
    mav0 = os.path.join(output_dir, "mav0")
    
    cam0_data_dir = os.path.join(mav0, "cam0", "data")
    cam1_data_dir = os.path.join(mav0, "cam1", "data")
    imu0_dir = os.path.join(mav0, "imu0")
    
    if os.path.exists(os.path.join(output_dir, "timestamps.txt")) and os.path.exists(cam0_data_dir) and len(os.listdir(cam0_data_dir)) > 100:
        print(f"[✔] {mav0} already extracted.")
        return
        
    os.makedirs(cam0_data_dir, exist_ok=True)
    os.makedirs(cam1_data_dir, exist_ok=True)
    os.makedirs(imu0_dir, exist_ok=True)
    
    reader = rosbag2_py.SequentialReader()
    storage_options = rosbag2_py.StorageOptions(uri=bag_path, storage_id='mcap')
    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format='cdr',
        output_serialization_format='cdr'
    )
    reader.open(storage_options, converter_options)
    
    print(f"Reading {bag_path}...")
    
    cam0_csv = open(os.path.join(mav0, "cam0", "data.csv"), 'w', newline='')
    cam1_csv = open(os.path.join(mav0, "cam1", "data.csv"), 'w', newline='')
    imu_csv = open(os.path.join(imu0_dir, "data.csv"), 'w', newline='')
    ts_file = open(os.path.join(output_dir, "timestamps.txt"), 'w')
    gt_file_path = os.path.join(output_dir, "gt_tum.txt")
    need_gt = not os.path.exists(gt_file_path)
    gt_file = open(gt_file_path, 'w') if need_gt else None
    
    cam0_writer = csv.writer(cam0_csv)
    cam1_writer = csv.writer(cam1_csv)
    imu_writer = csv.writer(imu_csv)
    
    cam0_writer.writerow(["#timestamp [ns]", "filename"])
    cam1_writer.writerow(["#timestamp [ns]", "filename"])
    imu_writer.writerow(["#timestamp [ns]", "w_RS_S_x [rad s^-1]", "w_RS_S_y [rad s^-1]", "w_RS_S_z [rad s^-1]", "a_RS_S_x [m s^-2]", "a_RS_S_y [m s^-2]", "a_RS_S_z [m s^-2]"])
    
    msg_count = 0
    cam0_count = 0
    cam1_count = 0
    imu_count = 0
    gt_count = 0
    
    timestamps_set = set()
    
    while reader.has_next():
        topic, data, t = reader.read_next()
        msg_count += 1
        
        if topic == "/cam0/image_raw":
            msg = deserialize_message(data, Image)
            ts_ns = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
            if msg.encoding in ['mono16', '16UC1'] or len(msg.data) == msg.height * msg.width * 2:
                img16 = np.frombuffer(msg.data, dtype=np.uint16).reshape((msg.height, msg.width))
                img = (img16 >> 8).astype(np.uint8)
            else:
                img = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.width))
            fn = f"{ts_ns}.png"
            cv2.imwrite(os.path.join(cam0_data_dir, fn), img)
            cam0_writer.writerow([ts_ns, fn])
            cam0_count += 1
            if ts_ns not in timestamps_set:
                timestamps_set.add(ts_ns)
                ts_file.write(f"{ts_ns}\n")
                
        elif topic == "/cam1/image_raw":
            msg = deserialize_message(data, Image)
            ts_ns = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
            if msg.encoding in ['mono16', '16UC1'] or len(msg.data) == msg.height * msg.width * 2:
                img16 = np.frombuffer(msg.data, dtype=np.uint16).reshape((msg.height, msg.width))
                img = (img16 >> 8).astype(np.uint8)
            else:
                img = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.width))
            fn = f"{ts_ns}.png"
            cv2.imwrite(os.path.join(cam1_data_dir, fn), img)
            cam1_writer.writerow([ts_ns, fn])
            cam1_count += 1
            
        elif topic == "/imu0":
            msg = deserialize_message(data, Imu)
            ts_ns = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
            imu_writer.writerow([
                ts_ns,
                msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z,
                msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z
            ])
            imu_count += 1
            
        elif topic == "/vrpn_client/raw_transform" and gt_file is not None:
            msg = deserialize_message(data, TransformStamped)
            t_sec = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            tx = msg.transform.translation.x
            ty = msg.transform.translation.y
            tz = msg.transform.translation.z
            qx = msg.transform.rotation.x
            qy = msg.transform.rotation.y
            qz = msg.transform.rotation.z
            qw = msg.transform.rotation.w
            gt_file.write(f"{t_sec:.6f} {tx:.6f} {ty:.6f} {tz:.6f} {qx:.6f} {qy:.6f} {qz:.6f} {qw:.6f}\n")
            gt_count += 1

        if msg_count % 10000 == 0:
            print(f"Processed {msg_count} msgs: {cam0_count} cam0, {cam1_count} cam1, {imu_count} IMU...")
            
    cam0_csv.close()
    cam1_csv.close()
    imu_csv.close()
    ts_file.close()
    if gt_file is not None:
        gt_file.close()
    
    print(f"\n[✔] Extracted TUM-VI Corridor ASL dataset:")
    print(f"    cam0: {cam0_count} images")
    print(f"    cam1: {cam1_count} images")
    print(f"    imu:  {imu_count} samples")
    print(f"    saved at: {mav0}")

if __name__ == '__main__':
    main()
