with open("/tmp/main_clean_base.tex", "r") as f:
    text = f.read()

# 1. Table 1 header: replace Hybrid KLT (Ours) with ORB-SLAM3 (Hybrid KLT)
text = text.replace(
    r"\textbf{Hybrid KLT (Ours)}",
    r"\textbf{ORB-SLAM3 (Hybrid KLT)}"
)

# 2. Section 2.6: Replace Contribution and Novelty paragraph with neutral formulation
old_p = r"\textbf{Contribution and Novelty.} While hybrid tracking strategies have been explored in systems like VINS-Mono and SVO, no prior work has integrated pyramidal KLT optical flow into the full ORB-SLAM3 three-thread Atlas architecture while preserving DBoW2 loop closing and $\Simthree$ multi-map merging. Our \textbf{Hybrid KLT ORB-SLAM3}~\cite{orbslam3klt} is the first to demonstrate that dual-rate tracking (KLT on non-keyframes, ORB on keyframes) within the ORB-SLAM3 framework achieves a $36.1\%$ latency reduction and $40\%$ keyframe reduction while maintaining centimeter-level accuracy on standard benchmarks."

new_p = r"\textbf{Hybrid Tracking Formulation.} To evaluate whether the frontend descriptor bottleneck can be alleviated on CPU architectures, the evaluated \textbf{Hybrid KLT ORB-SLAM3} framework~\cite{orbslam3klt} incorporates dual-rate tracking (sparse pyramidal KLT optical flow on non-keyframes and ORB descriptor extraction on keyframes), preserving DBoW2 loop closing while achieving a $36.1\%$ latency reduction and $40\%$ keyframe reduction on standard benchmarks."

assert old_p in text, "Could not find Contribution and Novelty paragraph!"
text = text.replace(old_p, new_p)

# 3. Section 7.2: Replace 'The Implemented Hybrid Tracking Architecture' and 'we designed and implemented'
text = text.replace(
    r"\section{The Implemented Hybrid Tracking Architecture}" + "\n" +
    r"To resolve the fundamental conflict between KLT optical flow speed and descriptor-based loop closing accuracy, we designed and implemented the \textbf{Hybrid Tracking Architecture} (Algorithm~\ref{alg:hybrid_tracking}), released openly in the \path{ORB_SLAM_3_KLT} repository.",
    r"\section{Hybrid Tracking Architecture}" + "\n" +
    r"To resolve the fundamental conflict between KLT optical flow speed and descriptor-based loop closing accuracy, the \textbf{Hybrid Tracking Architecture} (Algorithm~\ref{alg:hybrid_tracking}) evaluates a dual-rate tracking scheme, released openly in the \path{ORB_SLAM_3_KLT} repository."
)

# 4. Abstract: Replace 'Breakthrough'
text = text.replace(
    r"\textbf{High-Efficiency Hybrid Tracking Breakthrough (ORB-SLAM3 KLT):}",
    r"\textbf{High-Efficiency Hybrid Tracking Performance (ORB-SLAM3 KLT):}"
)

# 5. Conclusion: Replace 'Breakthrough' and 'The implemented Hybrid'
text = text.replace(
    r"\textbf{High-Efficiency Hybrid Tracking Breakthrough:} The implemented Hybrid ORB-SLAM3 KLT system",
    r"\textbf{High-Efficiency Hybrid Tracking Trade-Off:} The evaluated Hybrid ORB-SLAM3 KLT system"
)

# Write to main.tex
with open("main.tex", "w") as f:
    f.write(text)

print("Successfully restored main.tex to clean pre-expansion state without novelty claims!")
