#!/usr/bin/env python3
"""Convert a ROS 2 bag into the EuRoC / ASL folder layout read by ORB-SLAM3 and Kimera-VIO.

ORB-SLAM3 (stereo_inertial_euroc) and Kimera-VIO (stereoVIOEuroc) cannot read ROS 2 bags;
both read this layout. The data is not modified: images keep their pixels (16-bit images
are shifted to 8-bit, >> 8) and every sample keeps its header timestamp.

Output:
    <out>/mav0/cam0/data/<t_ns>.png   <out>/mav0/cam0/data.csv
    <out>/mav0/cam1/data/<t_ns>.png   <out>/mav0/cam1/data.csv
    <out>/mav0/imu0/data.csv          (t_ns, gyro xyz [rad/s], accel xyz [m/s^2])
    <out>/timestamps.txt              (one t_ns per stereo pair, used by ORB-SLAM3)
    <out>/gt_tum.txt                  (only with --gt-topic: t[s] x y z qx qy qz qw)

Only stereo pairs with the same header stamp on both cameras are listed in cam0/data.csv,
cam1/data.csv and timestamps.txt: Kimera pairs left/right images by row index, so a single
unpaired image would shift every later pair.

Run inside the slam-base container (rosbag2_py, cv2, numpy), e.g.
    python3 scripts/rosbag_to_euroc.py datasets/tum_vi_corridor1/corridor1_ros2 datasets/tum_vi_corridor1 \
        --left /cam0/image_raw --right /cam1/image_raw --imu /imu0 --gt-topic /vrpn_client/raw_transform
    python3 scripts/rosbag_to_euroc.py datasets/suedhoehe_gps_schnee_02 datasets/suedhoehe_asl \
        --left /camera/infra1/image_rect_raw --right /camera/infra2/image_rect_raw --imu /camera/imu
"""
import argparse
import os
import sys

import cv2
import numpy as np
import rosbag2_py
from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message


def stamp_ns(msg):
    return msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec


def to_gray8(msg):
    enc = msg.encoding.lower()
    if enc in ("mono16", "16uc1"):
        dtype = ">u2" if msg.is_bigendian else "<u2"
        img = np.frombuffer(msg.data, dtype=dtype).reshape(msg.height, msg.step // 2)[:, :msg.width]
        return (img >> 8).astype(np.uint8)
    if enc in ("mono8", "8uc1"):
        return np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.step)[:, :msg.width]
    if enc in ("rgb8", "bgr8"):
        img = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.step)[:, :msg.width * 3]
        img = img.reshape(msg.height, msg.width, 3)
        return cv2.cvtColor(img, cv2.COLOR_RGB2GRAY if enc == "rgb8" else cv2.COLOR_BGR2GRAY)
    sys.exit(f"unsupported image encoding '{msg.encoding}'")


def gt_pose(msg):
    """Position + orientation from TransformStamped, PoseStamped or Odometry."""
    if hasattr(msg, "transform"):
        return msg.transform.translation, msg.transform.rotation
    if hasattr(msg, "pose") and hasattr(msg.pose, "pose"):
        return msg.pose.pose.position, msg.pose.pose.orientation
    return msg.pose.position, msg.pose.orientation


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("bag", help="ROS 2 bag folder (with metadata.yaml)")
    ap.add_argument("out", help="output dataset folder (mav0/ is created inside)")
    ap.add_argument("--left", required=True, help="left image topic (cam0)")
    ap.add_argument("--right", required=True, help="right image topic (cam1)")
    ap.add_argument("--imu", required=True, help="IMU topic")
    ap.add_argument("--gt-topic", help="optional pose topic written to <out>/gt_tum.txt")
    ap.add_argument("--max-frames", type=int, default=0, help="stop after N left images (testing)")
    ap.add_argument("--overwrite", action="store_true", help="allow writing into an existing mav0/")
    args = ap.parse_args()

    mav0 = os.path.join(args.out, "mav0")
    if os.path.exists(mav0) and not args.overwrite:
        sys.exit(f"{mav0} already exists (use --overwrite to write into it)")
    cam_dirs = {args.left: os.path.join(mav0, "cam0"), args.right: os.path.join(mav0, "cam1")}
    for d in cam_dirs.values():
        os.makedirs(os.path.join(d, "data"), exist_ok=True)
    os.makedirs(os.path.join(mav0, "imu0"), exist_ok=True)

    info = rosbag2_py.Info().read_metadata(args.bag, "")
    reader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=args.bag, storage_id=info.storage_identifier),
                rosbag2_py.ConverterOptions("cdr", "cdr"))
    types = {t.name: t.type for t in reader.get_all_topics_and_types()}
    wanted = [args.left, args.right, args.imu] + ([args.gt_topic] if args.gt_topic else [])
    for topic in wanted:
        if topic not in types:
            sys.exit(f"topic {topic} not in bag; available: {sorted(types)}")
    reader.set_filter(rosbag2_py.StorageFilter(topics=wanted))
    msg_class = {t: get_message(types[t]) for t in wanted}

    stamps = {args.left: set(), args.right: set()}
    imu_rows, gt_rows = [], []
    n_left = 0
    while reader.has_next():
        topic, data, _ = reader.read_next()
        msg = deserialize_message(data, msg_class[topic])
        if topic in cam_dirs:
            t = stamp_ns(msg)
            cv2.imwrite(os.path.join(cam_dirs[topic], "data", f"{t}.png"), to_gray8(msg))
            stamps[topic].add(t)
            if topic == args.left:
                n_left += 1
                if n_left % 500 == 0:
                    print(f"  {n_left} left images")
                if args.max_frames and n_left >= args.max_frames:
                    break
        elif topic == args.imu:
            w, a = msg.angular_velocity, msg.linear_acceleration
            imu_rows.append((stamp_ns(msg), w.x, w.y, w.z, a.x, a.y, a.z))
        else:
            p, q = gt_pose(msg)
            gt_rows.append((stamp_ns(msg), p.x, p.y, p.z, q.x, q.y, q.z, q.w))

    pairs = sorted(stamps[args.left] & stamps[args.right])
    for d in cam_dirs.values():
        with open(os.path.join(d, "data.csv"), "w") as f:
            f.write("#timestamp [ns],filename\n")
            f.writelines(f"{t},{t}.png\n" for t in pairs)
    with open(os.path.join(args.out, "timestamps.txt"), "w") as f:
        f.writelines(f"{t}\n" for t in pairs)

    imu_rows.sort()
    with open(os.path.join(mav0, "imu0", "data.csv"), "w") as f:
        f.write("#timestamp [ns],w_RS_S_x [rad s^-1],w_RS_S_y [rad s^-1],w_RS_S_z [rad s^-1],"
                "a_RS_S_x [m s^-2],a_RS_S_y [m s^-2],a_RS_S_z [m s^-2]\n")
        f.writelines(f"{r[0]},{r[1]!r},{r[2]!r},{r[3]!r},{r[4]!r},{r[5]!r},{r[6]!r}\n" for r in imu_rows)

    if args.gt_topic:
        gt_rows.sort()
        with open(os.path.join(args.out, "gt_tum.txt"), "w") as f:
            f.writelines(f"{r[0] * 1e-9:.9f} " + " ".join(f"{v:.9f}" for v in r[1:]) + "\n" for r in gt_rows)

    unpaired = len(stamps[args.left] ^ stamps[args.right])
    print(f"stereo pairs: {len(pairs)} (unpaired images skipped: {unpaired}), "
          f"IMU samples: {len(imu_rows)}" + (f", GT poses: {len(gt_rows)}" if args.gt_topic else ""))


if __name__ == "__main__":
    main()
