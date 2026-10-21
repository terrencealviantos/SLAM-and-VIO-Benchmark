#!/usr/bin/env python3
"""Convert EuRoC MAV ASL dataset format to ROS 2 bag (mcap).

Usage:
    python3 euroc_to_ros2bag.py /path/to/V1_03_difficult/mav0 /path/to/output_bag

Creates a ROS 2 bag with:
  - /cam0/image_raw        (sensor_msgs/msg/Image, mono8)
  - /cam1/image_raw        (sensor_msgs/msg/Image, mono8)
  - /imu0                  (sensor_msgs/msg/Imu)
  - /leica/position        (geometry_msgs/msg/PointStamped)  [if available]
"""

import argparse
import csv
import os
import sys

import cv2
import numpy as np

import rclpy
from rclpy.serialization import serialize_message
from sensor_msgs.msg import Image, Imu
from geometry_msgs.msg import PointStamped
from std_msgs.msg import Header
from builtin_interfaces.msg import Time
import rosbag2_py


def ns_to_time(ns: int) -> Time:
    t = Time()
    t.sec = int(ns // 1_000_000_000)
    t.nanosec = int(ns % 1_000_000_000)
    return t


def make_header(ns: int, frame_id: str) -> Header:
    h = Header()
    h.stamp = ns_to_time(ns)
    h.frame_id = frame_id
    return h


def read_imu_csv(imu_csv_path):
    """Read EuRoC IMU CSV: timestamp[ns],wx,wy,wz,ax,ay,az"""
    rows = []
    with open(imu_csv_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0].startswith('#') or row[0].startswith('timestamp'):
                continue
            ts_ns = int(row[0])
            wx, wy, wz = float(row[1]), float(row[2]), float(row[3])
            ax, ay, az = float(row[4]), float(row[5]), float(row[6])
            rows.append((ts_ns, wx, wy, wz, ax, ay, az))
    return rows


def read_image_timestamps(data_csv_path):
    """Read EuRoC image CSV: timestamp[ns],filename"""
    rows = []
    with open(data_csv_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0].startswith('#') or row[0].startswith('timestamp'):
                continue
            ts_ns = int(row[0])
            filename = row[1].strip()
            rows.append((ts_ns, filename))
    return rows


def read_groundtruth_csv(gt_csv_path):
    """Read EuRoC ground truth (Leica) CSV: timestamp[ns],px,py,pz,..."""
    rows = []
    if not os.path.exists(gt_csv_path):
        return rows
    with open(gt_csv_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if row[0].startswith('#') or row[0].startswith('timestamp'):
                continue
            ts_ns = int(row[0])
            px, py, pz = float(row[1]), float(row[2]), float(row[3])
            rows.append((ts_ns, px, py, pz))
    return rows


def main():
    parser = argparse.ArgumentParser(description='Convert EuRoC ASL to ROS 2 bag')
    parser.add_argument('mav0_dir', help='Path to the mav0 directory')
    parser.add_argument('output_bag', help='Output bag directory path')
    args = parser.parse_args()

    mav0 = args.mav0_dir
    output_bag = args.output_bag

    # Verify structure
    for required in ['cam0/data.csv', 'cam0/data', 'cam1/data.csv', 'cam1/data',
                      'imu0/data.csv']:
        if not os.path.exists(os.path.join(mav0, required)):
            print(f"[ERROR] Missing {required} in {mav0}")
            sys.exit(1)

    # os.makedirs(output_bag, exist_ok=True)

    # Set up bag writer
    writer = rosbag2_py.SequentialWriter()
    storage_options = rosbag2_py.StorageOptions(uri=output_bag, storage_id='mcap')
    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format='cdr',
        output_serialization_format='cdr'
    )
    writer.open(storage_options, converter_options)

    # Create topics
    cam0_topic = rosbag2_py.TopicMetadata(
        name='/cam0/image_raw', type='sensor_msgs/msg/Image',
        serialization_format='cdr')
    cam1_topic = rosbag2_py.TopicMetadata(
        name='/cam1/image_raw', type='sensor_msgs/msg/Image',
        serialization_format='cdr')
    imu_topic = rosbag2_py.TopicMetadata(
        name='/imu0', type='sensor_msgs/msg/Imu',
        serialization_format='cdr')

    writer.create_topic(cam0_topic)
    writer.create_topic(cam1_topic)
    writer.create_topic(imu_topic)

    # Ground truth (optional)
    gt_csv = os.path.join(mav0, 'state_groundtruth_estimate0', 'data.csv')
    if not os.path.exists(gt_csv):
        gt_csv = os.path.join(mav0, 'leica0', 'data.csv')
    gt_rows = read_groundtruth_csv(gt_csv)
    if gt_rows:
        gt_topic = rosbag2_py.TopicMetadata(
            name='/leica/position', type='geometry_msgs/msg/PointStamped',
            serialization_format='cdr')
        writer.create_topic(gt_topic)

    # Collect all messages with timestamps for sorted writing
    all_messages = []

    # IMU messages
    print("[1/4] Reading IMU data...")
    imu_rows = read_imu_csv(os.path.join(mav0, 'imu0', 'data.csv'))
    for ts_ns, wx, wy, wz, ax, ay, az in imu_rows:
        msg = Imu()
        msg.header = make_header(ts_ns, 'imu')
        msg.angular_velocity.x = wx
        msg.angular_velocity.y = wy
        msg.angular_velocity.z = wz
        msg.linear_acceleration.x = ax
        msg.linear_acceleration.y = ay
        msg.linear_acceleration.z = az
        all_messages.append((ts_ns, '/imu0', serialize_message(msg)))
    print(f"      {len(imu_rows)} IMU messages")

    # cam0
    print("[2/4] Reading cam0 images...")
    cam0_rows = read_image_timestamps(os.path.join(mav0, 'cam0', 'data.csv'))
    for i, (ts_ns, filename) in enumerate(cam0_rows):
        img_path = os.path.join(mav0, 'cam0', 'data', filename)
        if not os.path.exists(img_path):
            continue
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        msg = Image()
        msg.header = make_header(ts_ns, 'cam0')
        msg.height, msg.width = img.shape[:2]
        msg.encoding = 'mono8'
        msg.step = msg.width
        msg.data = img.tobytes()
        all_messages.append((ts_ns, '/cam0/image_raw', serialize_message(msg)))
        if (i + 1) % 200 == 0:
            print(f"      cam0: {i+1}/{len(cam0_rows)}")
    print(f"      {len(cam0_rows)} cam0 images")

    # cam1
    print("[3/4] Reading cam1 images...")
    cam1_rows = read_image_timestamps(os.path.join(mav0, 'cam1', 'data.csv'))
    for i, (ts_ns, filename) in enumerate(cam1_rows):
        img_path = os.path.join(mav0, 'cam1', 'data', filename)
        if not os.path.exists(img_path):
            continue
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        msg = Image()
        msg.header = make_header(ts_ns, 'cam1')
        msg.height, msg.width = img.shape[:2]
        msg.encoding = 'mono8'
        msg.step = msg.width
        msg.data = img.tobytes()
        all_messages.append((ts_ns, '/cam1/image_raw', serialize_message(msg)))
        if (i + 1) % 200 == 0:
            print(f"      cam1: {i+1}/{len(cam1_rows)}")
    print(f"      {len(cam1_rows)} cam1 images")

    # Ground truth
    if gt_rows:
        print(f"[3.5/4] Adding {len(gt_rows)} ground truth points...")
        for ts_ns, px, py, pz in gt_rows:
            msg = PointStamped()
            msg.header = make_header(ts_ns, 'leica')
            msg.point.x = px
            msg.point.y = py
            msg.point.z = pz
            all_messages.append((ts_ns, '/leica/position', serialize_message(msg)))

    # Sort by timestamp and write
    print("[4/4] Writing bag (sorted by timestamp)...")
    all_messages.sort(key=lambda x: x[0])
    for ts_ns, topic, serialized in all_messages:
        writer.write(topic, serialized, ts_ns)

    del writer
    print(f"[✔] ROS 2 bag created at: {output_bag}")
    print(f"    Total messages: {len(all_messages)}")


if __name__ == '__main__':
    main()
