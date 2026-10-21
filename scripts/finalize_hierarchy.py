with open("main.tex", "r") as f:
    text = f.read()

# Replace top-level sections in 2.1 to be under a single \section{The State Estimation Continuum: VO, VIO, and Full SLAM}
# Change:
# \section{Motivation: State Estimation in GPS-Denied Environments} -> \subsection{Motivation: State Estimation in GPS-Denied Environments}
# \section{VIO as the High-Rate Inner Loop of Full SLAM} -> \subsection{VIO as the High-Rate Inner Loop of Full SLAM}
# \section{The Evaluated Paradigms Across the VIO-to-SLAM Continuum} -> \subsection{The Evaluated Paradigms Across the VIO-to-SLAM Continuum}
# \section{The Frontend Tracking Bottleneck: Descriptors vs. Optical Flow} -> \subsection{The Frontend Tracking Bottleneck: Descriptors vs. Optical Flow}

sec2_1 = r"""\section{The State Estimation Continuum: VO, VIO, and Full SLAM}
\label{sec:state_estimation_continuum}
"""

text = text.replace(
    r"\section{Motivation: State Estimation in GPS-Denied Environments}",
    sec2_1 + "\n" + r"\subsection{Motivation: State Estimation in GPS-Denied Environments}"
)
text = text.replace(
    r"\section{VIO as the High-Rate Inner Loop of Full SLAM}",
    r"\subsection{VIO as the High-Rate Inner Loop of Full SLAM}"
)
text = text.replace(
    r"\section{The Evaluated Paradigms Across the VIO-to-SLAM Continuum}",
    r"\subsection{The Evaluated Paradigms Across the VIO-to-SLAM Continuum}"
)
text = text.replace(
    r"\section{The Frontend Tracking Bottleneck: Descriptors vs. Optical Flow}",
    r"\subsection{The Frontend Tracking Bottleneck: Descriptors vs. Optical Flow}"
)

# Under 2.2:
# \section{Inertial Sensor Dynamics and Physical Complementarity} -> \subsection{Inertial Sensor Dynamics and Stochastic Errors}
# \section{The Principle of IMU Preintegration} -> \subsection{The Principle of IMU Preintegration}
# \section{Visual Sensing and 3D Scene Geometry} -> \subsection{Visual Sensing, Lens Distortion, and Stereo Depth Recovery}
# \section{Coordinate Systems and Reference Frames} -> \subsection{Coordinate Systems, Reference Frames, and Mathematical Conventions}

text = text.replace(
    r"\section{Inertial Sensor Dynamics and Physical Complementarity}",
    r"\subsection{Inertial Sensor Dynamics and Stochastic Errors}"
)
text = text.replace(
    r"\section{The Principle of IMU Preintegration}",
    r"\subsection{The Principle of IMU Preintegration}"
)
text = text.replace(
    r"\section{Visual Sensing and 3D Scene Geometry}",
    r"\subsection{Visual Sensing, Lens Distortion, and Stereo Depth Recovery}"
)
text = text.replace(
    r"\section{Coordinate Systems and Reference Frames}",
    r"\subsection{Coordinate Systems, Reference Frames, and Mathematical Conventions}"
)

# Under 2.4 Evaluated Systems:
# Inside OpenVINS:
# \subsection{Foundations of Recursive Filtering...} -> \subsubsection{Foundations of Recursive Filtering: Linear and Extended Kalman Filtering}
# \subsubsection{The Linear Kalman Filter Cycle} -> \paragraph{The Linear Kalman Filter Cycle.}
# \subsubsection{The Breakdown of Linearity...} -> \paragraph{The Breakdown of Linearity and the Extended Kalman Filter (EKF).}
# \subsection{MSCKF Core Philosophy...} -> \subsubsection{MSCKF Core Philosophy vs. Traditional EKF-SLAM}
# \subsection{State Vector Composition...} -> \subsubsection{State Vector Composition and Camera Pose Cloning}
# \subsection{Geometric Constraint Formation...} -> \subsubsection{Geometric Constraint Formation via Landmark Marginalization}
# \subsection{Dual Feature Representations...} -> \subsubsection{Dual Feature Representations: MSCKF Features vs. SLAM Features}
# \subsection{Visual Frontend: Grid Bucketing...} -> \subsubsection{Visual Frontend: Grid Bucketing and KLT Optical Flow}
# \subsection{Single-Thread Sequential Execution Pipeline} -> \subsubsection{Single-Thread Sequential Execution Pipeline}

text = text.replace(
    r"\subsection{Foundations of Recursive Filtering: Linear and Extended Kalman Filtering}",
    r"\subsubsection{Foundations of Recursive Filtering: Linear and Extended Kalman Filtering}"
)
text = text.replace(
    r"\subsubsection{The Linear Kalman Filter Cycle}",
    r"\paragraph{The Linear Kalman Filter Cycle.}"
)
text = text.replace(
    r"\subsubsection{The Breakdown of Linearity and the Extended Kalman Filter (EKF)}",
    r"\paragraph{The Breakdown of Linearity and the Extended Kalman Filter (EKF).}"
)
text = text.replace(
    r"\subsection{MSCKF Core Philosophy vs. Traditional EKF-SLAM}",
    r"\subsubsection{MSCKF Core Philosophy vs. Traditional EKF-SLAM}"
)
text = text.replace(
    r"\subsection{State Vector Composition and Camera Pose Cloning}",
    r"\subsubsection{State Vector Composition and Camera Pose Cloning}"
)
text = text.replace(
    r"\subsection{Geometric Constraint Formation via Landmark Marginalization}",
    r"\subsubsection{Geometric Constraint Formation via Landmark Marginalization}"
)
text = text.replace(
    r"\subsection{Dual Feature Representations: MSCKF Features vs. SLAM Features}",
    r"\subsubsection{Dual Feature Representations: MSCKF Features vs. SLAM Features}"
)
text = text.replace(
    r"\subsection{Visual Frontend: Grid Bucketing and KLT Optical Flow}",
    r"\subsubsection{Visual Frontend: Grid Bucketing and KLT Optical Flow}"
)
text = text.replace(
    r"\subsection{Single-Thread Sequential Execution Pipeline}",
    r"\subsubsection{Single-Thread Sequential Execution Pipeline}"
)

# Inside Kimera-VIO:
# \subsection{Factor Graph Formulation and Bounded Fixed-Lag Horizon} -> \subsubsection{Factor Graph Formulation and Bounded Fixed-Lag Horizon}
# \subsection{Incremental iSAM2 on Bayes Trees and Decoupled Concurrency} -> \subsubsection{Incremental iSAM2 on Bayes Trees and Decoupled Concurrency}
text = text.replace(
    r"\subsection{Factor Graph Formulation and Bounded Fixed-Lag Horizon}",
    r"\subsubsection{Factor Graph Formulation and Bounded Fixed-Lag Horizon}"
)
text = text.replace(
    r"\subsection{Incremental iSAM2 on Bayes Trees and Decoupled Concurrency}",
    r"\subsubsection{Incremental iSAM2 on Bayes Trees and Decoupled Concurrency}"
)

# Inside ORB-SLAM3:
# \subsection{The Three Concurrent Threads in the Atlas Architecture} -> \subsubsection{The Three Concurrent Threads in the Atlas Architecture}
# \subsubsection{1. Tracking Thread...} -> \paragraph{1. Tracking Thread (High-Rate Sensor Synchronization \& Pose Estimation).}
# \subsubsection{2. Local Mapping Thread...} -> \paragraph{2. Local Mapping Thread (Local Map Construction \& Optimization).}
# \subsubsection{3. Loop Closing and Map Merging Thread...} -> \paragraph{3. Loop Closing and Map Merging Thread (Global Consistency \& Atlas).}
# \subsection{Thread Synchronization Dynamics and Mutex Lock Contention} -> \subsubsection{Thread Synchronization Dynamics and Mutex Lock Contention}
text = text.replace(
    r"\subsection{The Three Concurrent Threads in the Atlas Architecture}",
    r"\subsubsection{The Three Concurrent Threads in the Atlas Architecture}"
)
text = text.replace(
    r"\subsubsection{1. Tracking Thread (High-Rate Sensor Synchronization \& Pose Estimation)}",
    r"\paragraph{1. Tracking Thread (High-Rate Sensor Synchronization \& Pose Estimation).}"
)
text = text.replace(
    r"\subsubsection{2. Local Mapping Thread (Local Map Construction \& Optimization)}",
    r"\paragraph{2. Local Mapping Thread (Local Map Construction \& Optimization).}"
)
text = text.replace(
    r"\subsubsection{3. Loop Closing and Map Merging Thread (Global Consistency \& Atlas)}",
    r"\paragraph{3. Loop Closing and Map Merging Thread (Global Consistency \& Atlas).}"
)
text = text.replace(
    r"\subsection{Thread Synchronization Dynamics and Mutex Lock Contention}",
    r"\subsubsection{Thread Synchronization Dynamics and Mutex Lock Contention}"
)

# Inside Hybrid KLT:
# \subsection{Selective KLT Optical Flow on Non-Keyframes} -> \subsubsection{Selective KLT Optical Flow on Non-Keyframes}
# \subsection{Zero-Copy Descriptor Binding and Keyframe Filtering} -> \subsubsection{Zero-Copy Descriptor Binding and Keyframe Filtering}
text = text.replace(
    r"\subsection{Selective KLT Optical Flow on Non-Keyframes}",
    r"\subsubsection{Selective KLT Optical Flow on Non-Keyframes}"
)
text = text.replace(
    r"\subsection{Zero-Copy Descriptor Binding and Keyframe Filtering}",
    r"\subsubsection{Zero-Copy Descriptor Binding and Keyframe Filtering}"
)

with open("main.tex", "w") as f:
    f.write(text)

print("Hierarchy successfully refined!")
