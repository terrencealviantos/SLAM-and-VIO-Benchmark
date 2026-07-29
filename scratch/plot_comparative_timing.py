#!/usr/bin/env python3
"""
3-Algorithm Comparative Timing Visualizer
=========================================
Generates side-by-side comparison bar chart for OpenVINS, ORB-SLAM3, and Kimera-VIO.
"""

import os
import matplotlib.pyplot as plt
import numpy as np

def main():
    out_dir = "/home/terrence/.gemini/antigravity/brain/a11cb992-df0e-453e-9ddc-8fac8d927cda"
    os.makedirs(out_dir, exist_ok=True)

    algorithms = ["OpenVINS\n(MSCKF Filter)", "Kimera-VIO\n(Factor Graph)", "ORB-SLAM3\n(Stereo-Inertial)"]
    mean_latencies = [20.62, 8.99, 55.86]  # total frame latency in ms
    tracking_latencies = [8.72, 6.35, 54.66] # tracking stage latency in ms
    max_latencies = [36.70, 59.00, 283.30]

    x = np.arange(len(algorithms))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    rects1 = ax.bar(x - width, mean_latencies, width, label="Total Frame Mean Latency (ms)", color="#4C72B0", edgecolor="white", alpha=0.9)
    rects2 = ax.bar(x, tracking_latencies, width, label="Feature Tracking Stage Latency (ms)", color="#DD8452", edgecolor="white", alpha=0.9)
    rects3 = ax.bar(x + width, max_latencies, width, label="Max Peak Latency (ms)", color="#C44E52", edgecolor="white", alpha=0.9)

    ax.set_ylabel("Duration (ms)", color="white", fontsize=12, fontweight="bold")
    ax.set_title("Cross-Algorithm Latency & Module Breakdown (EuRoC MH_01_easy)", color="white", fontsize=14, fontweight="bold", pad=16)
    ax.set_xticks(x)
    ax.set_xticklabels(algorithms, color="white", fontsize=11, fontweight="bold")
    ax.tick_params(colors="white")
    ax.spines[:].set_edgecolor("#555")
    ax.grid(axis="y", color="#ffffff22", linestyle="--", linewidth=0.6)
    ax.legend(facecolor="#0f3460", edgecolor="#555", labelcolor="white", fontsize=10)

    # Add data labels
    for rects in [rects1, rects2, rects3]:
        for rect in rects:
            h = rect.get_height()
            ax.annotate(f"{h:.1f}ms",
                        xy=(rect.get_x() + rect.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", color="white", fontsize=9, fontweight="bold")

    plt.tight_layout()
    path = os.path.join(out_dir, "comparative_pipeline_timing.png")
    plt.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[✔] 3-Algorithm Comparative Timing plot saved → {path}")

if __name__ == "__main__":
    main()
