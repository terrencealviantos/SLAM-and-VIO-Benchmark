# Visual SLAM & Visual-Inertial Odometry Benchmark Suite

[![ROS 2](https://img.shields.io/badge/ROS%202-Humble-blue.svg)](https://docs.ros.org/en/humble/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![CUDA](https://img.shields.io/badge/CUDA-13.0%20%7C%20RTX%203050-76B900.svg)](https://developer.nvidia.com/cuda-toolkit)
[![Evaluation](https://img.shields.io/badge/Evaluation-evo%20APE%2FRPE-orange.svg)](https://github.com/MichaelGrupp/evo)

An automated, containerized benchmarking suite and comparative state estimation framework evaluating **NVIDIA cuVSLAM**, **OpenVINS**, **ORB-SLAM3 (Baseline & Hybrid KLT)**, and **Kimera-VIO** across indoor MAV (*EuRoC MAV*) and challenging outdoor winter snow (*Suedhoehe*) datasets.

---

## 🏛️ Modular Docker Architecture

To guarantee mathematical reproducibility and prevent dependency conflicts across different SLAM frameworks, the repository uses a clean **layered container architecture**:

```
                          ┌───────────────────────────┐
                          │     slam-base:latest      │
                          │───────────────────────────│
                          │ • Ubuntu 22.04 LTS        │
                          │ • ROS 2 Humble Core/TF2   │
                          │ • OpenCV 4.5.4 (Contrib)  │
                          │ • Eigen 3.4.0 & Ceres 2.0 │
                          │ • NVIDIA CUDA 13.0 Runtime│
                          │ • evo Trajectory Evaluator│
                          └─────────────┬─────────────┘
                                        │
         ┌──────────────────┬───────────┴───────────┬──────────────────┐
         ▼                  ▼                       ▼                  ▼
┌─────────────────┐┌─────────────────┐┌───────────────────┐┌──────────────────┐
│ cuvslam:latest  ││ openvins:latest ││  orbslam3:latest  ││  kimera:latest   │
│ (NVIDIA GPU VIO ││ (MSCKF EKF      ││  (Keyframe Bundle ││  (GTSAM Factor   │
│  Optical Flow)  ││  Sliding Window)││   Adjustment)     ││   Graph Mesh)    │
└─────────────────┘└─────────────────┘└───────────────────┘└──────────────────┘
```

---

## ⚡ Quickstart: Unified Benchmark Runner

The entire benchmark suite is controlled by a single unified script in the repository root: **`./run_benchmark.sh`**.

### 1. Run a Single Algorithm (One Command)

```bash
# Run NVIDIA cuVSLAM (GPU-Accelerated) on Suedhoehe
./run_benchmark.sh cuvslam suedhoehe

# Run OpenVINS (MSCKF Filter) on Suedhoehe
./run_benchmark.sh openvins suedhoehe

# Run ORB-SLAM3 Baseline (Stereo-Inertial BA) on EuRoC MH_01
./run_benchmark.sh orbslam3 euroc

# Run ORB-SLAM3 Hybrid KLT (Dual-Rate Optical Flow SLAM) on EuRoC MH_01
./run_benchmark.sh orbslam3_klt euroc

# Run Kimera-VIO (GTSAM Factor Graph) on Suedhoehe
./run_benchmark.sh kimera suedhoehe
```

---

### 🖥️ Live GUI & Multi-Terminal Visualizer Mode (`--gui`)

To watch any algorithm compute state estimation live with real-time 3D point clouds, camera streams, and trajectory visualizers:

```bash
# Launch cuVSLAM with live RViz2 GUI + separate terminal windows:
./run_benchmark.sh cuvslam suedhoehe --gui

# Launch ORB-SLAM3 Baseline with live Pangolin 3D SLAM Map Viewer:
./run_benchmark.sh orbslam3 euroc --gui

# Launch ORB-SLAM3 Hybrid KLT with Pangolin 3D GUI:
./run_benchmark.sh orbslam3_klt euroc --gui

# Launch OpenVINS with multi-terminal RViz2 visualizer:
./run_benchmark.sh openvins suedhoehe --gui

# Launch Kimera-VIO with multi-terminal RViz2 Factor Graph & Mesh visualizer:
./run_benchmark.sh kimera suedhoehe --gui
```

When `--gui` is passed:
1. **Terminal 1 (Algorithm Node)**: Displays live tracking performance, telemetry, and GPU acceleration status.
2. **Terminal 2 (Viewer GUI)**: Opens **RViz2** (or native **Pangolin 3D Viewer** for ORB-SLAM3) showing landmark clouds, camera frustum, and trajectory path.
3. **Terminal 3 (Rosbag Player)**: Interactive dataset playback with keyboard controls (<kbd>SPACE</kbd> to pause/resume, arrow keys to change rate).

---

### 2. Batch Benchmarks & Evaluation

```bash
# View all available CLI options
./run_benchmark.sh --help

# Run all 5 algorithms sequentially across datasets
./run_benchmark.sh all all

# Run evo evaluation on existing generated trajectories
./run_benchmark.sh --evaluate
```

---

## 📊 Algorithmic Comparison Matrix

| Algorithm | Paradigm | Frontend | Backend | Loop Closure / Map | Target Hardware |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NVIDIA cuVSLAM** | GPU Visual SLAM | GPU Optical Flow | CUDA Sparse BA | Pose Graph (GPU) | NVIDIA GPU / Jetson |
| **OpenVINS** | Filter (MSCKF) | KLT FAST Corners | MSCKF EKF Covariance | None ($O(1)$ Memory) | Low-power CPU |
| **ORB-SLAM3** | Optimization SLAM | ORB Descriptors | Local Bundle Adjust. | DBoW2 + Atlas Maps | Multi-core CPU |
| **ORB-SLAM3 (KLT)**| Dual-Rate Hybrid | KLT (Non-KF) + ORB | Local Bundle Adjust. | DBoW2 Keyframes | Multi-core CPU |
| **Kimera-VIO** | Factor Graph | Shi-Tomasi + KLT | GTSAM iSAM2 Bayes | Kimera-RPGO (GNC) | Multi-core CPU |

---

## 🛡️ Resource Allocation & Hardware Protection

All benchmarks feature **configurable resource flags** with safe defaults to prevent system freezing:
* **Default CPU Limit**: Capped to **2 Cores** (`--cpus 2`)
* **Default RAM Limit**: Capped to **3 GB** (`--memory 3g`)
* **Custom Allocation**: You can easily override these on any runner script:
  ```bash
  # Run cuVSLAM with 4 CPU cores and 6 GB RAM
  ./run_cuvslam.sh suedhoehe --cpus 4 --memory 6g

  # Run Master Suite with custom hardware limits
  ./run_benchmark.sh --algorithm all --dataset all --cpus 4 --memory 8g
  ```
* **Process Priority**: Executed with `nice -n 19` (low background priority)

---

## 📁 Repository Structure

```
SLAM-and-VIO-Benchmark/
├── run_benchmark.sh             # Master benchmark entrypoint
├── run_cuvslam.sh               # Shortcut for cuVSLAM
├── run_openvins.sh              # Shortcut for OpenVINS
├── run_orbslam3.sh              # Shortcut for ORB-SLAM3
├── run_kimera.sh                # Shortcut for Kimera-VIO
├── datasets/                    # Datasets (Suedhoehe, EuRoC)
├── results/                     # TUM trajectory logs and evo metrics
├── scripts/
│   ├── run_unified_benchmark.py # Python benchmark orchestrator
│   └── sync_to_overleaf.sh      # Paper sync utility
└── workspace/                   # Algorithm source trees & configs
```

---

## 📄 Academic Citation & Overleaf Sync

This repository contains the experimental framework for the research report:
> **Comprehensive Empirical Benchmarking and Architectural Analysis of Visual SLAM and Visual-Inertial Odometry Systems**  
> *TU Dresden, Faculty of Electrical and Computer Engineering, 2026.*

To sync local LaTeX changes and benchmark figures with Overleaf:
```bash
./scripts/sync_to_overleaf.sh "Update paper figures and metrics"
```
