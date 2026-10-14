# Thesis Structure & Roadmap: Visual-Inertial Odometry (VIO) Benchmark

---

## 1. Abstract Outline (Key Points to Cover)

- **Context & Motivation:** Importance of real-time state estimation in GPS-denied autonomous navigation using visual-inertial sensor fusion.
- **Problem Statement:** State-of-the-art pipelines use fundamentally distinct paradigms (filtering vs. optimization, optical flow vs. feature matching, CPU vs. GPU), requiring a systematic, fair comparison.
- **Scope & Evaluated Systems:** Evaluation of OpenVINS (MSCKF), Kimera-VIO (factor graph), ORB-SLAM3 (optimization), and NVIDIA cuVSLAM (CUDA-accelerated) normalized to pure VIO mode (loop closure disabled).
- **Evaluation Metrics:** Trajectory accuracy (ATE, RPE) and computational profiling (per-stage latency, thread utilization, memory footprint).
- **Key Takeaways & Contributions:** Architectural trade-offs (e.g., KLT vs. continuous ORB extraction, filter vs. graph optimization) and practical recommendations for embedded robotic platforms.

---

## 2. Table of Contents

### 1. Introduction
- **1.1** Problem Statement & Dilemma: Algorithmic Diversity vs. Embedded Hardware Constraints
- **1.2** The Role of Visual-Inertial Fusion (Complementary Sensor Dynamics)
- **1.3** Research Objectives and Questions
- **1.4** Contributions of the Thesis
- **1.5** Thesis Structure

### 2. Fundamentals & Related Work
- **2.1** State Estimation in GPS-Denied Environments (The VO, VIO, and SLAM Continuum)
  - **2.1.1** Progression from Visual Odometry (VO) to Visual-Inertial Odometry (VIO)
  - **2.1.2** VIO as the High-Rate Inner Loop of Full SLAM (OpenVINS as the Base Odometry Engine)
- **2.2** Sensor Models and Dynamics
  - **2.2.1** Pinhole Camera Model, Intrinsic Calibration, and Distortion
  - **2.2.2** IMU Kinematic Model and Noise Characteristics (Allan Variance, Biases, Random Walk)
- **2.3** Visual Front-End Paradigms
  - **2.3.1** Sparse Optical Flow Tracking (Lucas-Kanade / KLT)
  - **2.3.2** Invariant Feature Extraction & Matching (ORB Descriptors, Brute-Force / DBoW)
- **2.4** Visual-Inertial Back-End Paradigms
  - **2.4.1** Filter-Based Estimation (MSCKF - Multi-State Constraint Kalman Filter)
  - **2.4.2** Optimization-Based Estimation (Fixed-Lag Smoothing, Factor Graphs, iSAM2)
  - **2.4.3** On-Manifold IMU Preintegration ($SO(3)$ and $SE(3)$)
- **2.5** Evaluated System Architectures
  - **2.5.1** OpenVINS: EKF-based On-Manifold Sliding Window Filter
  - **2.5.2** Kimera-VIO: Modular Factor-Graph Architecture
  - **2.5.3** ORB-SLAM3: Optimization Pipeline in Pure VIO Configuration
  - **2.5.4** NVIDIA cuVSLAM: CUDA-Accelerated Visual Odometry Pipeline

### 3. Benchmarking Methodology & Experimental Setup
- **3.1** Datasets and Sensor Configurations (e.g., EuRoC MAV, TUM-VI)
- **3.2** System Normalization: Isolating Pure VIO Mode (Disabling Relocalization & Loop Closure)
- **3.3** Evaluation Metrics
  - **3.3.1** Trajectory Accuracy: ATE (Absolute Trajectory Error) and RPE (Relative Pose Error)
  - **3.3.2** Computational Metrics: Per-Frame Latency, Jitter, CPU/GPU Thread Utilization, Memory Footprint
- **3.4** Hardware Testbed & Profiling Toolchain (`perf`, Valgrind, ROS Profiler, NVIDIA Nsight / `jtop`)

### 4. Experimental Results & Comparative Analysis
- **4.1** Trajectory Accuracy Across Sequence Types (Nominal, Fast Motion, Dynamic Lighting)
- **4.2** Failure Modes and Tracking Robustness (Lost Tracks, Covariance Divergence, Recovery)
- **4.3** Computational Performance & Latency Breakdown
  - **4.3.1** Front-End Latency: Feature Extraction vs. KLT Tracking
  - **4.3.2** Back-End Latency: Filter Update vs. Bundle Adjustment Iterations
- **4.4** Thread Profiling and Resource Distribution (Multi-Threading Efficiency, CPU vs. GPU)

### 5. Architectural Discussion & Design Trade-offs
- **5.1** Filter vs. Factor Graph: Does Optimization Justify the Computational Overhead?
- **5.2** The Front-End Bottleneck: Continuous ORB Extraction vs. Sparse Optical Flow
- **5.3** Feasibility of a Hybrid Front-End (KLT Frame Tracking with Periodic ORB Keyframe Extraction)
- **5.4** GPU Acceleration in Robotics: Practical Deployment Considerations for cuVSLAM

### 6. Conclusion & Future Work
- **6.1** Summary of Findings
- **6.2** Practical Recommendations for Robotic Platform Selection
- **6.3** Future Work (Implementation of Hybrid Front-End, Semantic/Volumetric Mapping)

---

## 3. Action Plan & Task Checklist

### Phase 1: Data Organization & Metric Computation
- [ ] **Align Ground Truth Trajectories:** Use `evo` (`evo_ape`, `evo_rpe`) to align estimated trajectories with ground truth using $SE(3)$ alignment.
- [ ] **Generate Accuracy Tables:** Tabulate ATE (RMSE) and RPE across all tested sequences for OpenVINS, Kimera-VIO, ORB-SLAM3 (VIO mode), and cuVSLAM.
- [ ] **Plot Trajectories:** Export side-by-side $x-y$ and $x-y-z$ trajectory plots for representative datasets (e.g., easy, aggressive motion, low-light).

### Phase 2: Timing & Profiling Extraction
- [ ] **Parse Execution Logs:** Extract mean, standard deviation, and 95th percentile latency for:
  - Total per-frame processing time
  - Front-end processing time (KLT tracking vs. ORB feature detection)
  - Back-end optimization / filter update step
- [ ] **Thread & Hardware Stats:** Summarize CPU core loads, thread counts, and GPU memory / compute utilization.
- [ ] **Visualizations:** Create stacked bar charts or box plots displaying the time spent per pipeline stage across all four systems.

### Phase 3: Writing Order
1. **Chapter 3 (Methodology):** Write first. Document the exact hardware setup, software versions, ROS configurations, datasets, and flags used to isolate VIO mode.
2. **Chapter 4 (Results):** Insert tables and figures. Describe the observed trends objectively.
3. **Chapter 2 (Fundamentals & Related Work):** Detail the theoretical foundations: start with the GPS-denied state estimation context and the VO-to-SLAM continuum (from 1.1), followed by sensor kinematics, and the theoretical differences between MSCKF, factor graphs, KLT, and ORB descriptors.
4. **Chapter 5 (Discussion):** Analyze *why* the metrics differ (e.g., ORB descriptor latency vs. KLT efficiency; CPU vs. GPU trade-offs). Introduce the hybrid KLT+ORB tracking rationale here.
5. **Chapters 1 & 6 (Introduction & Conclusion):** Write last to ensure seamless alignment with your final findings.
