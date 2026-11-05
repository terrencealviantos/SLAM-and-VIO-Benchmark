import re

with open("main.tex.bak_before_merge", "r") as f:
    text = f.read()

# 1. Header (up to Chapter 1)
idx_ch1 = text.find(r"\chapter{Introduction}")
header = text[:idx_ch1]

# 2. Chapter 1: Introduction
idx_ch2 = text.find(r"\chapter{Background and Related Work}")
ch1_intro = text[idx_ch1:idx_ch2].strip()

# Research Objectives and Scope & Related Work and Positioning
idx_obj = text.find(r"\section{Research Objectives and Scope}")
idx_rel = text.find(r"\section{Related Work and Positioning}")
idx_ch3 = text.find(r"\chapter{Foundational Concepts in Visual-Inertial Navigation}")

research_objectives = text[idx_obj:idx_rel].strip()
related_work = text[idx_rel:idx_ch3].strip()

ch1_body = ch1_intro + "\n\n" + research_objectives + "\n\n" + related_work + "\n"

# 3. Chapter 2: Foundational Concepts and Evaluated System Architectures
ch2_title = r"""% =============================================================================
% CHAPTER 2: FOUNDATIONAL CONCEPTS AND EVALUATED SYSTEM ARCHITECTURES
% =============================================================================
\chapter{Foundational Concepts and Evaluated System Architectures}

Robust state estimation for agile robotic platforms requires representations that capture the physics of 3D motion while respecting the operational boundaries between local visual-inertial odometry and global map optimization. Rather than separating theory from software realization across disparate chapters, this chapter provides a unified treatment of the foundational concepts and algorithmic architectures evaluated throughout this monograph:
\begin{enumerate}
    \item \textbf{The State Estimation Continuum:} The hierarchical progression from pure Visual Odometry (VO) to sliding-window Visual-Inertial Odometry (VIO) and full Simultaneous Localization and Mapping (SLAM).
    \item \textbf{Sensor Physics and Preintegration:} The physical complementarity of cameras and MEMS IMUs, IMU preintegration theory, pinhole camera projections, and coordinate frame conventions.
    \item \textbf{Visual Front-End Representations:} Sparse differential optical flow tracking (Shi-Tomasi, Kanade--Lucas--Tomasi, and pyramidal coarse-to-fine matching) versus invariant feature descriptors (ORB detection, patch orientation, steered BRIEF, and DBoW2 place recognition).
    \item \textbf{Evaluated System Architectures and Concurrency:} In-depth analysis of the five evaluated frameworks (OpenVINS, Kimera-VIO, Baseline ORB-SLAM3, Hybrid KLT ORB-SLAM3, and NVIDIA cuVSLAM), covering their mathematical formulation, multi-thread scheduling dynamics, and execution timelines.
\end{enumerate}
"""

# Extract Section 2.1: Continuum
idx_mot = text.find(r"\section{Motivation: State Estimation in GPS-Denied Environments}")
idx_phys = text.find(r"\section{Physics and Complementarity of Visual-Inertial Fusion}")
sec_continuum_raw = text[idx_mot:idx_phys].strip()

# Extract Section 2.2: Sensor Physics & Preintegration
idx_coord = text.find(r"\section{Coordinate Systems and Reference Frames}")
sec_physics_raw = text[idx_phys:idx_coord].strip()

# Coordinate frames & notation table
idx_arch_figs = text.find("The thread concurrency patterns and inter-thread data flow architectures")
sec_coords_raw = text[idx_coord:idx_arch_figs].strip()

# Inertial dynamics, preintegration, visual sensing (from Ch 3 in backup)
idx_imu = text.find(r"\section{Inertial Sensor Dynamics and Physical Complementarity}")
idx_feat = text.find(r"\section{Feature Detection and Optical Flow Tracking}")
sec_imu_preint_raw = text[idx_imu:idx_feat].strip()

sensor_complementarity_table = sec_physics_raw.replace(r"\section{Physics and Complementarity of Visual-Inertial Fusion}", "").strip()

sec_sensor_dynamics = (
    r"\section{Sensor Dynamics, Calibration, and Preintegration}" + "\n" +
    r"\label{sec:sensor_dynamics}" + "\n\n" +
    "The fusion of cameras and IMUs represents one of the most powerful sensor pairings in cyber-physical systems. Table~\\ref{tab:sensor_complementarity} summarizes the complementary physical characteristics of vision and inertial sensing.\n\n" +
    sensor_complementarity_table + "\n\n" +
    sec_imu_preint_raw + "\n\n" +
    sec_coords_raw + "\n"
)

# Extract Section 2.3: Visual Front-End Representations: Optical Flow vs. Descriptors
idx_ch4 = text.find(r"\chapter{State Estimation Paradigms in VIO and SLAM}")
sec_klt_raw = text[idx_feat:idx_ch4].strip()

# ORB Features & DBoW2
idx_orb = text.find(r"\subsection{Visual Representation: ORB Features}")
idx_orb_threads = text.find(r"\subsection{The Three Concurrent Threads in the Atlas Architecture}")
sec_orb_dbow_raw = text[idx_orb:idx_orb_threads].strip()

sec_visual_representations = (
    r"\section{Visual Front-End Representations: Optical Flow vs. Feature Descriptors}" + "\n" +
    r"\label{sec:visual_representations}" + "\n" +
    "Visual-inertial navigation systems require continuous, accurate temporal correspondences between camera frames to constrain motion estimates. Frontends broadly separate into two paradigms: \\textit{differential optical flow} (which tracks pixel patches directly across consecutive frames using image intensity gradients) and \\textit{indirect feature-matching} (which extracts high-dimensional invariant descriptors such as ORB to match points across arbitrary baselines or historical keyframes).\n\n" +
    sec_klt_raw.replace(r"\section{Feature Detection and Optical Flow Tracking}", "% Feature Detection and Optical Flow Tracking") + "\n\n" +
    sec_orb_dbow_raw + "\n"
)

# Extract Section 2.4: Evaluated System Architectures and Concurrency Profiles
idx_mat = text.find(r"\begin{table}[H]" + "\n" + r"\centering" + "\n" + r"\scriptsize" + "\n" + r"\caption{Comprehensive Multi-Dimensional Architectural Comparison Matrix")
idx_gantt_sec = text.find(r"\section{Thread Concurrency and Inter-Thread Dynamics}")
table_matrix = text[idx_mat:idx_gantt_sec].strip()

# Conceptual architecture figures
idx_arch_end = idx_obj
arch_concept_figures = text[idx_arch_figs:idx_arch_end].strip()

# Gantt chart figures
idx_gantt_fig1 = text.find(r"\begin{figure}[p]" + "\n" + r"    \centering" + "\n" + r"    \begin{subfigure}[b]{\textwidth}" + "\n" + r"        \centering" + "\n" + r"        \includegraphics[width=\textwidth]{1_openvins_gantt_chart.png}")
idx_ov_dyn = text.find(r"\subsection{OpenVINS Thread Dynamics}")
gantt_figures = text[idx_gantt_fig1:idx_ov_dyn].strip()

# OpenVINS section
idx_ov = text.find(r"\section{The Multi-State Constraint Kalman Filter (OpenVINS)}")
idx_orb_sec = text.find(r"\section{Full Keyframe Visual-Inertial SLAM (ORB-SLAM3)}")
sec_openvins_raw = text[idx_ov:idx_orb_sec].strip()

# Kimera section
idx_kim = text.find(r"\section{Fixed-Lag Factor Graph Smoothing (Kimera-VIO)}")
idx_hyb = text.find(r"\section{Dual-Rate Hybrid KLT--Descriptor Visual-Inertial SLAM (Hybrid KLT ORB-SLAM3)}")
sec_kimera_raw = text[idx_kim:idx_hyb].strip()

# ORB-SLAM3 threads & mutex contention
sec_orbslam3_threads_raw = text[idx_orb_threads:idx_kim].strip()

# Hybrid KLT section
idx_cuv = text.find(r"\section{Hardware-Accelerated Stream Computing (NVIDIA cuVSLAM)}")
idx_ch5 = text.find(r"\chapter{In-Depth Architectural Analysis of Evaluated Systems}")
sec_hybrid_raw = text[idx_hyb:idx_cuv].strip()

# cuVSLAM section
sec_cuvslam_raw = text[idx_cuv:idx_ch5].strip()

# Additional detail from Ch 5 for Hybrid KLT:
idx_hyb_dyn = text.find(r"\subsection{ORB-SLAM3 Hybrid KLT Concurrency and Keyframe Reduction Dynamics}")
idx_cuv_dyn = text.find(r"\subsection{NVIDIA cuVSLAM GPU Pipeline Dynamics}")
hyb_optimizations = text[idx_hyb_dyn:idx_cuv_dyn].strip()

cuvslam_extra = r"""As visualized in the multi-stream Gantt chart of Figure~\ref{fig:gantt_cuvslam}, cuVSLAM distributes workloads across dedicated CUDA streams:
\begin{itemize}
    \item Complete end-to-end stereo frame tracking (rectification + KLT + IMU + pose) executes in $\SI{5.92}{\milli\second}$ median ($>170\,\text{FPS}$), with peak latency $\SI{12.40}{\milli\second}$ occurring only when loop detection and pose graph optimization are triggered.
    \item Local bundle adjustment executes asynchronously on secondary CUDA streams ($\SI{8.28}{\milli\second}$ mean, $\SI{8.79}{\milli\second}$ median), completely offloading the host CPU.
\end{itemize}
"""

sec_evaluated_systems = (
    r"\section{Evaluated System Architectures and Concurrency Profiles}" + "\n" +
    r"\label{sec:evaluated_system_architectures}" + "\n\n" +
    "Beyond algorithmic formulations, the real-world performance, execution determinism, and scalability of state estimation systems are dictated by their thread concurrency models, queue synchronization, and hardware utilization.\n\n" +
    "Table~\\ref{tab:detailed_system_matrix} provides an exhaustive comparative matrix summarizing the architectural attributes of the five evaluated systems.\n\n" +
    table_matrix + "\n\n" +
    arch_concept_figures + "\n\n" +
    "Figures~\\ref{fig:all_gantt_charts} and~\\ref{fig:all_gantt_charts_part2} display the microsecond-level execution timeline Gantt charts across the five evaluated systems, capturing sub-module latencies, thread scheduling, and queue stalls.\n\n" +
    gantt_figures + "\n\n" +
    r"\subsection{OpenVINS: Multi-State Constraint Kalman Filter (MSCKF)}" + "\n" +
    r"\label{subsec:openvins_arch}" + "\n" +
    sec_openvins_raw.replace(r"\section{The Multi-State Constraint Kalman Filter (OpenVINS)}", "") + "\n\n" +
    r"\subsection{Kimera-VIO: Fixed-Lag Factor Graph Smoothing}" + "\n" +
    r"\label{subsec:kimera_arch}" + "\n" +
    sec_kimera_raw.replace(r"\section{Fixed-Lag Factor Graph Smoothing (Kimera-VIO)}", "") + "\n\n" +
    r"\subsection{ORB-SLAM3: Three-Thread Keyframe Atlas Architecture}" + "\n" +
    r"\label{subsec:orbslam3_arch}" + "\n" +
    "In contrast to the sliding-window filtering of OpenVINS and fixed-lag smoothing of Kimera-VIO, ORB-SLAM3~\\cite{orbslam3} represents full Simultaneous Localization and Mapping (SLAM). It maintains a persistent 3D landmark map, an Atlas multi-map management engine, and DBoW2 visual place recognition.\n\n" +
    sec_orbslam3_threads_raw + "\n\n" +
    r"\subsection{ORB-SLAM3 (Hybrid KLT Tracking): Dual-Rate Concurrency}" + "\n" +
    r"\label{subsec:hybrid_klt_arch}" + "\n" +
    sec_hybrid_raw.replace(r"\section{Dual-Rate Hybrid KLT--Descriptor Visual-Inertial SLAM (Hybrid KLT ORB-SLAM3)}", "") + "\n\n" +
    hyb_optimizations.replace(r"\subsection{ORB-SLAM3 Hybrid KLT Concurrency and Keyframe Reduction Dynamics}", r"\subsubsection{Algorithmic Realization and Mutex Relief}") + "\n\n" +
    r"\subsection{NVIDIA cuVSLAM: Hardware-Accelerated Stream Computing}" + "\n" +
    r"\label{subsec:cuvslam_arch}" + "\n" +
    sec_cuvslam_raw.replace(r"\section{Hardware-Accelerated Stream Computing (NVIDIA cuVSLAM)}", "") + "\n\n" +
    cuvslam_extra + "\n"
)

# Suffix starting from Experimental Methodology
idx_suffix = text.find(r"\chapter{Experimental Methodology and Benchmark Setup}")
suffix_raw = text[idx_suffix:]

# Combine everything
new_text = (
    header + "\n" +
    ch1_body + "\n\n" +
    ch2_title + "\n\n" +
    sec_continuum_raw + "\n\n" +
    sec_sensor_dynamics + "\n\n" +
    sec_visual_representations + "\n\n" +
    sec_evaluated_systems + "\n\n" +
    suffix_raw
)

with open("main.tex", "w") as f:
    f.write(new_text)

print("Consolidated main.tex written successfully!")
