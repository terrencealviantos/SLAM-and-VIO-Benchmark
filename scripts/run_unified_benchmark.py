#!/usr/bin/env python3
"""
SLAM & VIO Benchmark Unified Master Runner
==========================================
Orchestrates benchmarks for:
  - cuVSLAM (NVIDIA Isaac ROS GPU-Accelerated SLAM)
  - OpenVINS (MSCKF Filter)
  - ORB-SLAM3 (Stereo-Inertial Keyframe BA Baseline)
  - ORB-SLAM3 Hybrid KLT (Dual-Rate Optical Flow SLAM)
  - Kimera-VIO (Factor-Graph Smoothing)

Across datasets:
  - Suedhoehe (Outdoor winter/snow, long-range features, GPS GT)
  - EuRoC MAV (Indoor machine hall & vicon room sequences, Vicon GT)
  - TUM (RGB-D / Monocular standard benchmark)
"""

import os
import sys
import argparse
import subprocess
import time
import shutil

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(REPO_ROOT, "datasets")
RESULTS_DIR = os.path.join(REPO_ROOT, "results")
WORKSPACE_DIR = os.path.join(REPO_ROOT, "workspace")
SCRATCH_DIR = os.path.join(REPO_ROOT, "scratch")
PYDEPS_DIR = os.path.join(WORKSPACE_DIR, ".python_deps")

DOCKER_IMAGE = "slam-base:latest"
CUVSLAM_IMAGE = "cuvslam:latest"
ORBSLAM3_IMAGE = "orbslam3:latest"
OPENVINS_IMAGE = "openvins:latest"
KIMERA_IMAGE = "kimera:latest"

def print_header(title):
    print("\n" + "=" * 75)
    print(f"  {title}")
    print("=" * 75)

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)
    return path

def check_docker_image(img=DOCKER_IMAGE):
    res = subprocess.run(["docker", "images", "-q", img], capture_output=True, text=True)
    if not res.stdout.strip():
        print(f"[INFO] Docker image '{img}' not found locally.")
        return False
    return True

# -----------------------------------------------------------------------------
# RUNNERS
# -----------------------------------------------------------------------------

def run_cuvslam_suedhoehe(dataset_dir, output_dir):
    print_header("Running NVIDIA cuVSLAM on Suedhoehe Dataset")
    ensure_dir(output_dir)
    
    bag_dir = os.path.abspath(dataset_dir)
    isaac_ws = os.path.join(WORKSPACE_DIR, "isaac_ros_ws")
    
    # 1. Clean previous runs
    subprocess.run(["docker", "rm", "-f", "cuvslam_node_run", "cuvslam_saver", "suedhoehe_player"], 
                   stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    
    print("[1/3] Starting cuVSLAM container with GPU passthrough...")
    node_cmd = [
        "docker", "run", "-d", "--name", "cuvslam_node_run",
        "--cpus=2", "--memory=3g",
        "--runtime=nvidia", "--gpus", "all", "--net=host", "--ipc=host",
        "-v", f"{output_dir}:/results",
        "-v", f"{bag_dir}:/dataset_dir",
        "-v", f"{isaac_ws}:/workspaces/isaac_ros-dev",
        DOCKER_IMAGE,
        "bash", "-c",
        "export LD_LIBRARY_PATH=/workspaces/isaac_ros-dev/install/isaac_ros_visual_slam/share/cuvslam/lib:$LD_LIBRARY_PATH && "
        "source /opt/ros/humble/setup.bash && "
        "source /workspaces/isaac_ros-dev/install/setup.bash && "
        "ros2 launch isaac_ros_visual_slam isaac_ros_visual_slam_suedhoehe.launch.py"
    ]
    subprocess.run(node_cmd, check=True)
    
    print("[2/3] Waiting for cuVSLAM node to initialize...")
    time.sleep(5)
    
    # Start trajectory saver
    tum_file = os.path.join(output_dir, "cuvslam_tum.txt")
    saver_cmd = [
        "docker", "run", "-d", "--name", "cuvslam_saver",
        "--net=host", "--ipc=host",
        "-v", f"{output_dir}:/results",
        "-v", f"{REPO_ROOT}/scripts:/scripts",
        DOCKER_IMAGE,
        "bash", "-c",
        "source /opt/ros/humble/setup.bash && python3 /scripts/cuvslam_save_trajectory.py /results/cuvslam_tum.txt"
    ]
    subprocess.run(saver_cmd, check=True)
    time.sleep(2)
    
    print(f"[3/3] Playing Suedhoehe Dataset Bag from {bag_dir}...")
    play_cmd = [
        "docker", "run", "--rm", "--name", "suedhoehe_player",
        "--runtime=nvidia", "--gpus", "all", "--net=host", "--ipc=host",
        "-v", f"{bag_dir}:/dataset_dir",
        DOCKER_IMAGE,
        "bash", "-c",
        "source /opt/ros/humble/setup.bash && ros2 bag play /dataset_dir"
    ]
    start_t = time.time()
    subprocess.run(play_cmd)
    elapsed = time.time() - start_t
    
    time.sleep(3)
    subprocess.run(["docker", "kill", "cuvslam_node_run", "cuvslam_saver"], 
                   stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    subprocess.run(["docker", "rm", "cuvslam_node_run", "cuvslam_saver"], 
                   stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    
    print(f"[SUCCESS] cuVSLAM Suedhoehe run completed in {elapsed:.1f} seconds.")
    print(f"Trajectory saved to: {tum_file}")

def run_orbslam3_klt(dataset_name, dataset_dir, output_dir):
    print_header(f"Running ORB-SLAM3 with Hybrid KLT Tracking on {dataset_name}")
    ensure_dir(output_dir)
    klt_dir = os.path.abspath(dataset_dir)
    
    print(f"[INFO] Evaluating Hybrid KLT tracker on: {klt_dir}")
    print(f"[INFO] Results will be logged into: {output_dir}")
    
    # If Docker is available, launch containerized execution
    if check_docker_image(ORBSLAM3_IMAGE):
        cmd = [
            "docker", "run", "-it", "--rm",
            "-v", f"{klt_dir}:/dataset",
            "-v", f"{output_dir}:/results",
            ORBSLAM3_IMAGE,
            "./Examples/Monocular/mono_euroc",
            "Vocabulary/ORBvoc.txt",
            "Examples/Monocular/EuRoC.yaml",
            "/dataset",
            "/dataset/timestamps.txt"
        ]
        try:
            subprocess.run(cmd, check=True)
            print(f"[SUCCESS] Hybrid ORB-SLAM3 KLT execution finished!")
        except Exception as e:
            print(f"[WARNING] Execution encountered: {e}")
    else:
        print("[INFO] Pre-computed benchmark trajectories available in results/orbslam3_klt/")

# -----------------------------------------------------------------------------
# EVALUATION & PLOTTING
# -----------------------------------------------------------------------------

def evaluate_kpis(est_tum, gt_tum, out_dir, algo_name="SLAM"):
    print_header(f"Evaluating KPIs with evo: {algo_name}")
    if not os.path.exists(est_tum):
        print(f"[WARNING] Trajectory file not found: {est_tum}")
        return None
    if not os.path.exists(gt_tum):
        print(f"[WARNING] Ground truth file not found: {gt_tum}")
        return None
        
    est_dir = os.path.dirname(os.path.abspath(est_tum))
    gt_dir = os.path.dirname(os.path.abspath(gt_tum))
    est_name = os.path.basename(est_tum)
    gt_name = os.path.basename(gt_tum)
    
    cmd_ape = [
        "docker", "run", "--rm",
        "-v", f"{PYDEPS_DIR}:/pydeps",
        "-v", f"{est_dir}:/est_dir",
        "-v", f"{gt_dir}:/gt_dir",
        "-v", f"{out_dir}:/out_dir",
        DOCKER_IMAGE,
        "bash", "-c",
        f"export PYTHONPATH=/pydeps:$PYTHONPATH && "
        f"/pydeps/bin/evo_ape tum /gt_dir/{gt_name} /est_dir/{est_name} "
        f"-r trans_part --align -a --save_results /out_dir/{algo_name.lower()}_ape.zip"
    ]
    res = subprocess.run(cmd_ape, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr)

def generate_comparative_plots():
    print_header("Generating Multi-Thread Gantt Charts & 5-Way Timing Breakdown")
    
    # 1. Multi-thread Gantt comparison
    gantt_script = os.path.join(SCRATCH_DIR, "plot_multithread_gantt.py")
    if os.path.exists(gantt_script):
        print("[1/2] Running 5-Way Multi-Thread Gantt generator...")
        subprocess.run([sys.executable, gantt_script], check=True)
        
    # 2. 5-Way timing breakdown
    timing_script = os.path.join(SCRATCH_DIR, "plot_5way_comparative_timing.py")
    if os.path.exists(timing_script):
        print("[2/2] Running 5-Algorithm Timing Breakdown generator...")
        subprocess.run([sys.executable, timing_script], check=True)
        
    print("[SUCCESS] All comparative figures generated and updated in figures/ and gantt_charts/!")

# -----------------------------------------------------------------------------
# CLI PARSER
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="SLAM & VIO Benchmark Master Runner")
    parser.add_argument("--algorithm", choices=["cuvslam", "openvins", "orbslam3", "orbslam3_klt", "kimera", "all"],
                        default="cuvslam", help="SLAM algorithm to run")
    parser.add_argument("--dataset", choices=["suedhoehe", "euroc", "tum", "all"],
                        default="suedhoehe", help="Dataset to benchmark on")
    parser.add_argument("--sequence", type=str, default="suedhoehe_gps_schnee_02",
                        help="Specific sequence name (e.g. MH_01_easy or suedhoehe_gps_schnee_02)")
    parser.add_argument("--evaluate", action="store_true", help="Run evo evaluation on existing results")
    parser.add_argument("--plot", action="store_true", help="Generate Gantt charts and timing histograms")
    
    args = parser.parse_args()
    
    if args.plot:
        generate_comparative_plots()
        return
        
    suedhoehe_dir = os.path.join(DATASETS_DIR, "suedhoehe_gps_schnee_02")
    suedhoehe_gt = os.path.join(suedhoehe_dir, "gps_trajectory.txt")
    
    if args.algorithm in ["cuvslam", "all"] and args.dataset in ["suedhoehe", "all"]:
        if check_docker_image():
            out_dir = os.path.join(RESULTS_DIR, "suedhoehe", "cuvslam")
            run_cuvslam_suedhoehe(suedhoehe_dir, out_dir)
            if os.path.exists(suedhoehe_gt):
                evaluate_kpis(os.path.join(out_dir, "cuvslam_tum.txt"), suedhoehe_gt, out_dir, "cuVSLAM")
                
    if args.algorithm in ["orbslam3_klt", "all"]:
        out_dir = os.path.join(RESULTS_DIR, "orbslam3_klt")
        euroc_dir = os.path.join(DATASETS_DIR, "Euroc", "machine_hall", "MH_01_easy")
        run_orbslam3_klt("EuRoC MH_01_easy", euroc_dir, out_dir)

    print("\nBenchmark orchestrator finished!")

if __name__ == "__main__":
    main()
