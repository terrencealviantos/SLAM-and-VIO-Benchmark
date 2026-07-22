import os
import subprocess
import time
import pandas as pd
import json

results_root = "/home/terrence/researchProject/results/euroc"
euroc_base = "/home/terrence/researchProject/datasets/Euroc"

sequences = [
    ("MH_01_easy", os.path.join(euroc_base, "machine_hall", "MH_01_easy")),
    ("MH_02_easy", os.path.join(euroc_base, "machine_hall", "MH_02_easy")),
    ("MH_04_difficult", os.path.join(euroc_base, "machine_hall", "MH_04_difficult")),
    ("MH_05_difficult", os.path.join(euroc_base, "machine_hall", "MH_05_difficult")),
    ("V1_01_easy", os.path.join(euroc_base, "vicon_room1", "V1_01_easy")),
    ("V1_02_medium", os.path.join(euroc_base, "vicon_room1", "V1_02_medium")),
    ("V1_03_difficult", os.path.join(euroc_base, "vicon_room1", "V1_03_difficult")),
]

os.makedirs(results_root, exist_ok=True)

for seq_name, seq_dir in sequences:
    out_dir = os.path.join(results_root, seq_name)
    os.makedirs(out_dir, exist_ok=True)
    gt_tum = os.path.join(seq_dir, "gt_tum.txt")
    ts_file = os.path.join(seq_dir, "timestamps.txt")
    ros2_bag = os.path.join(seq_dir, f"{seq_name}_ros2")

    print(f"\n==========================================")
    print(f" BENCHMARKING SEQUENCE: {seq_name}")
    print(f"==========================================")

    # 1. ORB-SLAM3
    orb_raw = os.path.join(out_dir, "orb_slam3_raw.txt")
    orb_tum = os.path.join(out_dir, "orb_slam3.txt")
    if os.path.exists(ts_file) and not os.path.exists(orb_tum):
        print(f"[ORB-SLAM3] Starting run on {seq_name}...")
        cmd_orb = [
            "docker", "run", "--rm",
            "-v", f"{seq_dir}:/dataset",
            "-v", f"{out_dir}:/output",
            "orbslam3-baseline:latest",
            "/ORB_SLAM3/Examples/Stereo-Inertial/stereo_inertial_euroc",
            "/ORB_SLAM3/Vocabulary/ORBvoc.txt",
            "/ORB_SLAM3/Examples/Stereo-Inertial/EuRoC.yaml",
            "/dataset", "/dataset/timestamps.txt", "/output/orb_slam3_raw.txt"
        ]
        try:
            subprocess.run(cmd_orb, check=True)
            if os.path.exists(orb_raw):
                with open(orb_raw, 'r') as f_in, open(orb_tum, 'w') as f_out:
                    for line in f_in:
                        if line.startswith("#"):
                            continue
                        parts = line.strip().split()
                        if len(parts) >= 8:
                            t_val = float(parts[0])
                            if t_val > 1e12:
                                t_val *= 1e-9
                            f_out.write(f"{t_val:.9f} {' '.join(parts[1:8])}\n")
                print(f"[ORB-SLAM3] Trajectory formatted -> {orb_tum}")
        except Exception as e:
            print(f"[ORB-SLAM3] Exception on {seq_name}: {e}")

    # 2. OpenVINS
    ov_tum = os.path.join(out_dir, "open_vins.txt")
    ov_raw = os.path.join(out_dir, "ov_estimate.txt")
    if os.path.exists(ros2_bag) and not os.path.exists(ov_tum):
        print(f"[OpenVINS] Starting run on {seq_name}...")
        cmd_ov = [
            "docker", "run", "--rm",
            "-v", "/home/terrence/researchProject/workspace/catkin_ws_ov:/catkin_ws",
            "-v", f"{ros2_bag}:/dataset",
            "-v", f"{out_dir}:/output",
            "ov_ros2_22_04:latest",
            "bash", "-c",
            "source /opt/ros/humble/setup.bash && cd /catkin_ws && colcon build --packages-select open_vins_eval ov_msckf --cmake-args -DCMAKE_BUILD_TYPE=Release >/dev/null 2>&1 && source /catkin_ws/install/setup.bash && ros2 run open_vins_eval run_subscribe_msckf --ros-args -p sys_config_path:=/catkin_ws/src/open_vins/config/euroc_mav/estimator_config.yaml & OV_PID=$! && sleep 3 && ros2 bag play /dataset --clock 200 && sleep 5 && cp /tmp/ov_estimate.txt /output/ 2>/dev/null || true && kill $OV_PID || true"
        ]
        try:
            subprocess.run(cmd_ov)
            if os.path.exists(ov_raw):
                with open(ov_raw, 'r') as f_in, open(ov_tum, 'w') as f_out:
                    for line in f_in:
                        if line.startswith("#"):
                            continue
                        parts = line.strip().split()
                        if len(parts) >= 8:
                            t_val = float(parts[0])
                            if t_val > 1e12:
                                t_val *= 1e-9
                            f_out.write(f"{t_val:.9f} {' '.join(parts[1:8])}\n")
                print(f"[OpenVINS] Trajectory formatted -> {ov_tum}")
        except Exception as e:
            print(f"[OpenVINS] Exception on {seq_name}: {e}")

    # 3. Kimera-VIO
    kimera_tum = os.path.join(out_dir, "kimera.txt")
    kimera_raw = os.path.join(out_dir, "traj_vio.csv")
    if os.path.exists(ros2_bag) and not os.path.exists(kimera_tum):
        print(f"[Kimera-VIO] Starting run on {seq_name}...")
        cmd_kimera = [
            "docker", "run", "--rm",
            "-v", f"{ros2_bag}:/dataset",
            "-v", f"{out_dir}:/output",
            "kimera_vio_ros2:latest",
            "bash", "-c",
            "mkdir -p /opt/ros/wrapper_ws/install/kimera_vio_ros/share/kimera_vio_ros/params /opt/ros/wrapper_ws/install/kimera_vio_ros/share/kimera_vio_ros/output_logs && cp -r /opt/ros/overlay_ws/src/MIT-SPARK/Kimera-VIO/params/Euroc /opt/ros/wrapper_ws/install/kimera_vio_ros/share/kimera_vio_ros/params/Euroc && cp -r /opt/ros/overlay_ws/src/MIT-SPARK/Kimera-VIO/params/Euroc /opt/ros/wrapper_ws/install/kimera_vio_ros/share/kimera_vio_ros/params/EuRoC && source /opt/ros/humble/setup.bash && source /opt/ros/wrapper_ws/install/setup.bash && ros2 launch kimera_vio_ros kimera_vio_ros.launch.xml dataset_name:=Euroc log_output:=true & K_PID=$! && sleep 3 && ros2 bag play /dataset --clock 200 && sleep 5 && cp -r /opt/ros/wrapper_ws/install/kimera_vio_ros/share/kimera_vio_ros/output_logs/* /output/ 2>/dev/null || true && kill $K_PID || true"
        ]
        try:
            subprocess.run(cmd_kimera)
            if os.path.exists(kimera_raw):
                with open(kimera_raw, 'r') as f_in, open(kimera_tum, 'w') as f_out:
                    for line in f_in:
                        if line.startswith("#") or "timestamp" in line:
                            continue
                        parts = line.strip().split(",")
                        if len(parts) >= 8:
                            ts_ns = float(parts[0])
                            t_sec = ts_ns * 1e-9 if ts_ns > 1e12 else ts_ns
                            p_x, p_y, p_z = parts[1], parts[2], parts[3]
                            q_x, q_y, q_z, q_w = parts[4], parts[5], parts[6], parts[7]
                            f_out.write(f"{t_sec:.9f} {p_x} {p_y} {p_z} {q_x} {q_y} {q_z} {q_w}\n")
                print(f"[Kimera-VIO] Trajectory formatted -> {kimera_tum}")
        except Exception as e:
            print(f"[Kimera-VIO] Exception on {seq_name}: {e}")

print("\nAll benchmark sequence runs finished successfully!")
