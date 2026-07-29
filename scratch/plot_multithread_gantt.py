#!/usr/bin/env python3
"""
Multi-Thread Architectural Gantt Chart Comparison
=================================================
Visualizes the multi-thread execution model of:
  1. OpenVINS (1 Primary Thread: Sequential MSCKF Pipeline)
  2. Kimera-VIO (2 Concurrent Threads: Frontend + Backend iSAM2)
  3. ORB-SLAM3 (3 Concurrent Threads: Tracking + Local Mapping + Loop Closing)
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def main():
    out_dir = "/home/terrence/.gemini/antigravity/brain/a11cb992-df0e-453e-9ddc-8fac8d927cda"
    os.makedirs(out_dir, exist_ok=True)

    fig, axes = plt.subplots(3, 1, figsize=(16, 12), sharex=True)
    fig.patch.set_facecolor("#1a1a2e")

    # ── 1. OpenVINS (1 Thread) ──────────────────────────────────────────────────
    ax1 = axes[0]
    ax1.set_facecolor("#16213e")
    ax1.set_title("OpenVINS Thread Architecture — Single Primary MSCKF Thread", color="white", fontsize=13, fontweight="bold", pad=10)

    # Frame 1
    ax1.add_patch(mpatches.FancyBboxPatch((0, -0.25), 8.7, 0.5, boxstyle="round,pad=0.02", facecolor="#DD8452", edgecolor="white", alpha=0.9))
    ax1.text(4.35, 0, "Feature Tracking (8.7ms)", ha="center", va="center", color="white", fontsize=8, fontweight="bold")

    ax1.add_patch(mpatches.FancyBboxPatch((8.7, -0.25), 0.5, 0.5, boxstyle="round,pad=0.02", facecolor="#55A868", edgecolor="white", alpha=0.9))

    ax1.add_patch(mpatches.FancyBboxPatch((9.2, -0.25), 2.6, 0.5, boxstyle="round,pad=0.02", facecolor="#C44E52", edgecolor="white", alpha=0.9))
    ax1.text(10.5, 0, "MSCKF (2.6ms)", ha="center", va="center", color="white", fontsize=8, fontweight="bold")

    ax1.add_patch(mpatches.FancyBboxPatch((11.8, -0.25), 5.6, 0.5, boxstyle="round,pad=0.02", facecolor="#8172B2", edgecolor="white", alpha=0.9))
    ax1.text(14.6, 0, "SLAM Update (5.6ms)", ha="center", va="center", color="white", fontsize=8, fontweight="bold")

    ax1.add_patch(mpatches.FancyBboxPatch((17.4, -0.25), 3.1, 0.5, boxstyle="round,pad=0.02", facecolor="#DA8BC3", edgecolor="white", alpha=0.9))

    # Frame 2
    ax1.add_patch(mpatches.FancyBboxPatch((50, -0.25), 8.5, 0.5, boxstyle="round,pad=0.02", facecolor="#DD8452", edgecolor="white", alpha=0.9))
    ax1.text(54.25, 0, "Feature Tracking", ha="center", va="center", color="white", fontsize=8, fontweight="bold")

    ax1.set_yticks([0])
    ax1.set_yticklabels(["Main VIO Thread"], color="white", fontsize=11, fontweight="bold")
    ax1.set_ylim(-0.6, 0.6)
    ax1.tick_params(colors="white")
    ax1.grid(axis="x", color="#ffffff22", linestyle="--")

    # ── 2. Kimera-VIO (2 Threads) ───────────────────────────────────────────────
    ax2 = axes[1]
    ax2.set_facecolor("#16213e")
    ax2.set_title("Kimera-VIO Thread Architecture — 2 Concurrent Threads (Frontend + Backend)", color="white", fontsize=13, fontweight="bold", pad=10)

    # Thread 1: Frontend
    ax2.add_patch(mpatches.FancyBboxPatch((0, 0.75), 6.3, 0.5, boxstyle="round,pad=0.02", facecolor="#DD8452", edgecolor="white", alpha=0.9))
    ax2.text(3.15, 1.0, "Frontend Tracking (6.3ms)", ha="center", va="center", color="white", fontsize=8, fontweight="bold")

    ax2.add_patch(mpatches.FancyBboxPatch((6.3, 0.75), 2.6, 0.5, boxstyle="round,pad=0.02", facecolor="#C44E52", edgecolor="white", alpha=0.9))

    # Thread 2: Backend (Asynchronous Keyframe Optimization)
    ax2.add_patch(mpatches.FancyBboxPatch((8.9, -0.25), 18.5, 0.5, boxstyle="round,pad=0.02", facecolor="#8172B2", edgecolor="white", alpha=0.9))
    ax2.text(18.15, 0, "iSAM2 Factor Graph Optimization (18.5ms)", ha="center", va="center", color="white", fontsize=8, fontweight="bold")

    ax2.set_yticks([1.0, 0])
    ax2.set_yticklabels(["Frontend Thread", "Backend iSAM2 Thread"], color="white", fontsize=11, fontweight="bold")
    ax2.set_ylim(-0.6, 1.6)
    ax2.tick_params(colors="white")
    ax2.grid(axis="x", color="#ffffff22", linestyle="--")

    # ── 3. ORB-SLAM3 (3 Threads) ───────────────────────────────────────────────
    ax3 = axes[2]
    ax3.set_facecolor("#16213e")
    ax3.set_title("ORB-SLAM3 Thread Architecture — 3 Concurrent Threads (Tracking + Local Mapping + Loop Closing)", color="white", fontsize=13, fontweight="bold", pad=10)

    # Thread 1: Tracking
    ax3.add_patch(mpatches.FancyBboxPatch((0, 1.75), 54.6, 0.5, boxstyle="round,pad=0.02", facecolor="#DD8452", edgecolor="white", alpha=0.9))
    ax3.text(27.3, 2.0, "Stereo ORB Tracking & Pose Estimation (54.6ms)", ha="center", va="center", color="white", fontsize=8, fontweight="bold")

    # Thread 2: Local Mapping (Asynchronous KeyFrame Processing)
    ax3.add_patch(mpatches.FancyBboxPatch((55, 0.75), 65.0, 0.5, boxstyle="round,pad=0.02", facecolor="#55A868", edgecolor="white", alpha=0.9))
    ax3.text(87.5, 1.0, "Local Bundle Adjustment & Map Point Fusion (65.0ms)", ha="center", va="center", color="white", fontsize=8, fontweight="bold")

    # Thread 3: Loop Closing (Intermittent Sim3 Optimization)
    ax3.add_patch(mpatches.FancyBboxPatch((120, -0.25), 45.0, 0.5, boxstyle="round,pad=0.02", facecolor="#C44E52", edgecolor="white", alpha=0.9))
    ax3.text(142.5, 0, "Loop Detection & Pose Graph Opt. (45ms)", ha="center", va="center", color="white", fontsize=8, fontweight="bold")

    ax3.set_yticks([2.0, 1.0, 0])
    ax3.set_yticklabels(["Tracking Thread", "Local Mapping Thread", "Loop Closing Thread"], color="white", fontsize=11, fontweight="bold")
    ax3.set_ylim(-0.6, 2.6)
    ax3.set_xlim(-2, 170)
    ax3.set_xlabel("Time Timeline (ms)", color="white", fontsize=12, fontweight="bold")
    ax3.tick_params(colors="white")
    ax3.grid(axis="x", color="#ffffff22", linestyle="--")

    plt.tight_layout()
    path = os.path.join(out_dir, "multithread_architecture_comparison.png")
    plt.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[✔] Saved Multi-Thread Architectural Gantt Chart → {path}")

if __name__ == "__main__":
    main()
