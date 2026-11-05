import os
import subprocess
import glob
import time
import pandas as pd

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

results_root = os.environ.get("RESULTS_ROOT", os.path.join(project_root, "results", "euroc"))
euroc_base = os.environ.get("EUROC_BASE", os.path.join(project_root, "datasets", "Euroc"))

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
    
    print(f"\n==========================================")
    print(f" PROCESSING SEQUENCE: {seq_name}")
    print(f"==========================================")

    # ----------------------------------------------------
    # 1. ORB-SLAM3
    # ----------------------------------------------------
    orb_raw = os.path.join(out_dir, "orb_slam3_raw.txt")
    orb_tum = os.path.join(out_dir, "orb_slam3.txt")
    if os.path.exists(ts_file):
        print(f"Running ORB-SLAM3 on {seq_name}...")
        cmd_orb = [
            "docker", "run", "--rm",
            "-v", f"{seq_dir}:/dataset",
            "-v", f"{out_dir}:/output",
            "orbslam3-baseline:latest",
            "/opt/ORB_SLAM3/Examples/Stereo-Inertial/stereo_inertial_euroc",
            "/opt/ORB_SLAM3/Vocabulary/ORBvoc.txt",
            "/opt/ORB_SLAM3/Examples/Stereo-Inertial/EuRoC.yaml",
            "/dataset", "/dataset/timestamps.txt", "/output/orb_slam3_raw.txt"
        ]
        try:
            subprocess.run(cmd_orb, check=True, timeout=300)
            if os.path.exists(orb_raw):
                # Format to TUM (t x y z qx qy qz qw)
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
                print(f"ORB-SLAM3 trajectory saved to {orb_tum}")
        except Exception as e:
            print(f"ORB-SLAM3 failed on {seq_name}: {e}")

    # ----------------------------------------------------
    # 2. OpenVINS
    # ----------------------------------------------------
    ros2_bag = os.path.join(seq_dir, f"{seq_name}_ros2")
    ov_tum = os.path.join(out_dir, "open_vins.txt")
    if os.path.exists(ros2_bag):
        print(f"Running OpenVINS on {seq_name}...")
        cmd_ov = [
            "docker", "run", "--rm",
            "-v", f"{ros2_bag}:/dataset",
            "-v", f"{out_dir}:/output",
            "ov_ros2_22_04:latest",
            "bash", "-c",
            "source /opt/ros/humble/setup.bash && source /opt/ros/catkin_ws_ov/install/setup.bash && "
            "ros2 run open_vins_eval run_subscribe_msckf --ros-args -p sys_config_path:=/opt/ros/catkin_ws_ov/src/open_vins/config/euroc_mav/estimator_config.yaml & "
            "OV_PID=$! && sleep 2 && ros2 bag play /dataset && sleep 2 && kill $OV_PID || true"
        ]
        try:
            subprocess.run(cmd_ov, timeout=300)
        except Exception as e:
            print(f"OpenVINS run completed/finished: {e}")

    # ----------------------------------------------------
    # 3. Kimera-VIO
    # ----------------------------------------------------
    kimera_tum = os.path.join(out_dir, "kimera.txt")
    if os.path.exists(ros2_bag):
        print(f"Running Kimera-VIO on {seq_name}...")
        cmd_kimera = [
            "docker", "run", "--rm",
            "-v", f"{ros2_bag}:/dataset",
            "-v", f"{out_dir}:/output",
            "kimera_vio_ros2:latest",
            "bash", "-c",
            "source /opt/ros/humble/setup.bash && source /opt/ros/wrapper_ws/install/setup.bash && "
            "ros2 launch kimera_vio_ros kimera_vio_ros_euroc.launch.py use_camera_info:=false & "
            "K_PID=$! && sleep 2 && ros2 bag play /dataset && sleep 2 && kill $K_PID || true"
        ]
        try:
            subprocess.run(cmd_kimera, timeout=300)
        except Exception as e:
            print(f"Kimera-VIO run completed/finished: {e}")

    # ----------------------------------------------------
    # 4. NVIDIA cuVSLAM (GPU-Accelerated)
    # ----------------------------------------------------
    cuvslam_tum = os.path.join(out_dir, "cuvslam.txt")
    if os.path.exists(ros2_bag):
        print(f"Running NVIDIA cuVSLAM (GPU) on {seq_name}...")
        isaac_ros_ws = os.path.join(project_root, "workspace", "isaac_ros_ws")
        cmd_cuvslam = [
            "docker", "run", "--rm",
            "--runtime=nvidia", "--gpus", "all",
            "-v", f"{ros2_bag}:/dataset",
            "-v", f"{out_dir}:/output",
            "-v", f"{isaac_ros_ws}:/workspaces/isaac_ros-dev",
            "isaac_ros_dev-x86_64:latest",
            "bash", "-c",
            "source /opt/ros/humble/setup.bash && source /workspaces/isaac_ros-dev/install/setup.bash 2>/dev/null || true && "
            "ros2 launch isaac_ros_visual_slam isaac_ros_visual_slam.launch.py num_cameras:=2 enable_imu_fusion:=true & "
            "C_PID=$! && sleep 2 && "
            "ros2 bag play /dataset --remap /cam0/image_raw:=/visual_slam/image_0 --remap /cam1/image_raw:=/visual_slam/image_1 --remap /imu0:=/visual_slam/imu && "
            "sleep 2 && kill $C_PID || true"
        ]
        try:
            subprocess.run(cmd_cuvslam, timeout=300)
        except Exception as e:
            print(f"cuVSLAM run completed/finished: {e}")

print("\nAll sequence benchmark executions completed!")
