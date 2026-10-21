import re

with open("main.tex", "r") as f:
    text = f.read()

# Header up to \chapter{Background and Related Work}
idx_ch1 = text.find("\\chapter{Introduction}")
header = text[:idx_ch1]

# Chapter 1: Introduction & Research Objectives
# Let's extract the intro text
idx_ch2 = text.find("\\chapter{Background and Related Work}")
ch1_intro = text[idx_ch1:idx_ch2].strip()

# In current Chapter 2:
# \section{Research Objectives and Scope}
idx_obj = text.find("\\section{Research Objectives and Scope}")
idx_rel = text.find("\\section{Related Work and Positioning}")
idx_ch3 = text.find("\\chapter{Foundational Concepts in Visual-Inertial Navigation}")

research_objectives = text[idx_obj:idx_rel].strip()
related_work = text[idx_rel:idx_ch3].strip()

# Combine Chapter 1 with Research Objectives
ch1_full = ch1_intro + "\n\n" + research_objectives + "\n\n" + related_work + "\n\n"

# Now construct Chapter 2: Foundational Concepts and Evaluated System Architectures
# Let's pull out:
# 1. State Estimation Continuum:
# From current Ch 2:
# \section{Motivation: State Estimation in GPS-Denied Environments}
# \section{VIO as the High-Rate Inner Loop of Full SLAM} (with Table 1.1)
# \section{The Evaluated Paradigms Across the VIO-to-SLAM Continuum} (with Table 1.2)
# \section{The Frontend Tracking Bottleneck: Descriptors vs. Optical Flow}
idx_mot = text.find("\\section{Motivation: State Estimation in GPS-Denied Environments}")
idx_phys = text.find("\\section{Physics and Complementarity of Visual-Inertial Fusion}")
sec_continuum = text[idx_mot:idx_phys].strip()

# 2. Sensor Dynamics and Complementary Fusion:
# \section{Physics and Complementarity of Visual-Inertial Fusion} (with Table 1.3)
idx_coord = text.find("\\section{Coordinate Systems and Reference Frames}")
sec_physics = text[idx_phys:idx_coord].strip()

# Coordinate systems and notation table:
idx_arch_figs = text.find("The thread concurrency patterns and inter-thread data flow architectures")
sec_coords = text[idx_coord:idx_arch_figs].strip()

# Inertial sensor dynamics and preintegration (from current Ch 3):
idx_imu = text.find("\\section{Inertial Sensor Dynamics and Physical Complementarity}")
idx_feat = text.find("\\section{Feature Detection and Optical Flow Tracking}")
sec_imu_preint_vis = text[idx_imu:idx_feat].strip()

# 3. Visual Front-End Representations: Optical Flow vs. Feature Descriptors
# From current Ch 3:
# \section{Feature Detection and Optical Flow Tracking} (Shi-Tomasi, KLT, Pyramidal)
idx_ch4 = text.find("\\chapter{State Estimation Paradigms in VIO and SLAM}")
sec_klt = text[idx_feat:idx_ch4].strip()

# From current Ch 4:
# ORB features and DBoW2 Place recognition
idx_orb = text.find("\\subsection{Visual Representation: ORB Features}")
idx_orb_threads = text.find("\\subsection{The Three Concurrent Threads in the Atlas Architecture}")
sec_orb_dbow = text[idx_orb:idx_orb_threads].strip()

# 4. Evaluated System Architectures and Concurrency Profiles
# Table 4.1 Comprehensive Matrix
idx_ch5 = text.find("\\chapter{In-Depth Architectural Analysis of Evaluated Systems}")
idx_mat = text.find("\\begin{table}[H]\n\\centering\n\\scriptsize\n\\caption{Comprehensive Multi-Dimensional Architectural Comparison Matrix")
idx_gantt_sec = text.find("\\section{Thread Concurrency and Inter-Thread Dynamics}")
table_matrix = text[idx_mat:idx_gantt_sec].strip()

# Gantt chart figures (OpenVINS/Kimera and ORB-SLAM3/cuVSLAM)
idx_gantt_fig1 = text.find("\\begin{figure}[p]\n    \\centering\n    \\begin{subfigure}[b]{\\textwidth}\n        \\centering\n        \\includegraphics[width=\\textwidth]{1_openvins_gantt_chart.png}")
idx_ov_dyn = text.find("\\subsection{OpenVINS Thread Dynamics}")
gantt_figures = text[idx_gantt_fig1:idx_ov_dyn].strip()

# OpenVINS complete description:
idx_ov = text.find("\\section{The Multi-State Constraint Kalman Filter (OpenVINS)}")
idx_orb_sec = text.find("\\section{Full Keyframe Visual-Inertial SLAM (ORB-SLAM3)}")
sec_openvins = text[idx_ov:idx_orb_sec].strip()

# Kimera complete description:
idx_kim = text.find("\\section{Fixed-Lag Factor Graph Smoothing (Kimera-VIO)}")
idx_hyb = text.find("\\section{Dual-Rate Hybrid KLT--Descriptor Visual-Inertial SLAM (Hybrid KLT ORB-SLAM3)}")
sec_kimera = text[idx_kim:idx_hyb].strip()

# ORB-SLAM3 three threads & mutex contention:
idx_mutex_end = idx_kim
sec_orbslam3_threads = text[idx_orb_threads:idx_mutex_end].strip()

# Hybrid KLT complete description + optimizations:
idx_cuv = text.find("\\section{Hardware-Accelerated Stream Computing (NVIDIA cuVSLAM)}")
sec_hybrid = text[idx_hyb:idx_cuv].strip()

# cuVSLAM complete description:
sec_cuvslam = text[idx_cuv:idx_ch5].strip()

# Conceptual architecture figures (ch1_vio_arch and ch1_slam_arch)
idx_arch_end = idx_obj
arch_concept_figures = text[idx_arch_figs:idx_arch_end].strip()

# Suffix: Experimental Methodology onwards
idx_ch6 = text.find("\\chapter{Experimental Methodology and Benchmark Setup}")
suffix = text[idx_ch6:]

print("All components extracted successfully!")
