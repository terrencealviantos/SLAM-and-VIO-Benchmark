#!/usr/bin/env python3
"""Extract stereo images and IMU from Suedhoehe ROS 2 MCAP bag to ASL / EuRoC format.

Creates:
  datasets/suedhoehe_asl/mav0/cam0/data/<timestamp_ns>.png
  datasets/suedhoehe_asl/mav0/cam0/data.csv
  datasets/suedhoehe_asl/mav0/cam1/data/<timestamp_ns>.png
  datasets/suedhoehe_asl/mav0/cam1/data.csv
  datasets/suedhoehe_asl/mav0/imu0/data.csv
  datasets/suedhoehe_asl/timestamps.txt
"""

import os
import sys
import csv
import cv2
import numpy as np

import rclpy
from rclpy.serialization import deserialize_message
from sensor_msgs.msg import Image, Imu
import rosbag2_py

def main():
    bag_path = "/home/boris/SLAM-and-VIO-Benchmark/datasets/suedhoehe_gps_schnee_02"
    output_dir = "/home/boris/SLAM-and-VIO-Benchmark/datasets/suedhoehe_asl"
    mav0 = os.path.join(output_dir, "mav0")
    
    cam0_data_dir = os.path.join(mav0, "cam0", "data")
    cam1_data_dir = os.path.join(mav0, "cam1", "data")
    imu0_dir = os.path.join(mav0, "imu0")
    
    if os.path.exists(os.path.join(output_dir, "timestamps.txt")):
        print(f"[✔] {output_dir} already extracted.")
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
    
    timestamps_set = set()
    
    while reader.has_next():
        topic, data, t = reader.read_next()
        msg_count += 1
        
        if topic == "/camera/infra1/image_rect_raw":
            msg = deserialize_message(data, Image)
            ts_ns = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
            img = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.width))
            fn = f"{ts_ns}.png"
            cv2.imwrite(os.path.join(cam0_data_dir, fn), img)
            cam0_writer.writerow([ts_ns, fn])
            cam0_count += 1
            if ts_ns not in timestamps_set:
                timestamps_set.add(ts_ns)
                ts_file.write(f"{ts_ns}\n")
                
        elif topic == "/camera/infra2/image_rect_raw":
            msg = deserialize_message(data, Image)
            ts_ns = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
            img = np.frombuffer(msg.data, dtype=np.uint8).reshape((msg.height, msg.width))
            fn = f"{ts_ns}.png"
            cv2.imwrite(os.path.join(cam1_data_dir, fn), img)
            cam1_writer.writerow([ts_ns, fn])
            cam1_count += 1
            
        elif topic == "/camera/imu":
            msg = deserialize_message(data, Imu)
            ts_ns = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
            imu_writer.writerow([
                ts_ns,
                msg.angular_velocity.x, msg.angular_velocity.y, msg.angular_velocity.z,
                msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z
            ])
            imu_count += 1
            
        if msg_count % 5000 == 0:
            print(f"Processed {msg_count} msgs: {cam0_count} cam0, {cam1_count} cam1, {imu_count} IMU...")
            
    cam0_csv.close()
    cam1_csv.close()
    imu_csv.close()
    ts_file.close()
    
    print(f"\n[✔] Extracted Suedhoehe ASL dataset:")
    print(f"    cam0: {cam0_count} images")
    print(f"    cam1: {cam1_count} images")
    print(f"    imu:  {imu_count} samples")
    print(f"    saved at: {output_dir}")

if __name__ == '__main__':
    main()
