#!/usr/bin/env python3
"""
Pure Empirical Pipeline Timing Visualizer for SLAM / VIO Benchmarking
======================================================================
Reads 100% raw, un-modified C++ timer records directly from the logged CSV files.
No sub-function interpolation, no artificial threads, no simulated frames.
"""

import argparse
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

# Consistent modern discrete color palette for frames
FRAME_COLOURS = [
    "#4C72B0", "#55A868", "#C44E52", "#8172B2", "#CCB974",
    "#64B5F6", "#E377C2", "#8C564B", "#9467BD", "#7F7F7F"
]

# Set specific stage colors for rendering
STAGE_COLOURS = {
    "feature_tracking":    "#DD8452",
    "track_stereo":        "#55A868",
    "imu_propagation":     "#55A868",
    "msckf_update":        "#C44E52",
    "slam_update":         "#8172B2",
    "slam_delayed_init":   "#937860",
    "retriangulation":     "#DA8BC3",
    "marginalization":     "#8C8C8C",
    "zupt_update":         "#CCB974",
    "image_preprocessing": "#4C72B0",
}

def stage_colour(name: str) -> str:
    return STAGE_COLOURS.get(name, "#64b5f6")

def load_csv_pure_empirical(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    assert {"frame_id", "module", "thread_id", "start_ns", "end_ns", "duration_ms"}.issubset(
        df.columns
    ), f"Missing columns. Got: {list(df.columns)}"
    return df

def plot_gantt_pure_empirical(df: pd.DataFrame, out_path: str, algo_name: str, dataset_name: str, start_frame: int = 100, num_frames: int = 5):
    frames = [f for f in sorted(df["frame_id"].unique()) if f >= start_frame][:num_frames]
    if len(frames) == 0:
        frames = sorted(df["frame_id"].unique())[:num_frames]

    df_zoom = df[(df["frame_id"].isin(frames)) & (df["module"] != "total_frame")].copy()
    if df_zoom.empty:
        print(f"[!] Warning: Zoomed range empty for {algo_name}, skipping")
        return

    # Normalize time relative to the earliest start time in zoom window
    t0 = df_zoom["start_ns"].min()
    df_zoom["start_ms"] = (df_zoom["start_ns"] - t0) * 1e-6
    df_zoom["end_ms"]   = (df_zoom["end_ns"]   - t0) * 1e-6

    raw_modules = df_zoom["module"].unique()
    if algo_name == "OpenVINS":
        order = ["feature_tracking", "imu_propagation", "msckf_update", "slam_update", "marginalization"]
        modules = [m for m in order if m in raw_modules] + [m for m in raw_modules if m not in order]
    elif algo_name == "ORB-SLAM3":
        order = ["image_preprocessing", "track_stereo"]
        modules = [m for m in order if m in raw_modules] + [m for m in raw_modules if m not in order]
    else:
        modules = sorted(raw_modules)

    module_y = {mod: i for i, mod in enumerate(reversed(modules))}
    lane_height = 0.55

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 1.8 + 1.1 * len(modules)))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    # Map each frame ID to a color
    frame_colors = {f: FRAME_COLOURS[i % len(FRAME_COLOURS)] for i, f in enumerate(frames)}

    for _, row in df_zoom.iterrows():
        y = module_y[row["module"]]
        width = max(row["end_ms"] - row["start_ms"], 0.1)
        color = frame_colors[row["frame_id"]]

        rect = mpatches.FancyBboxPatch(
            (row["start_ms"], y - lane_height / 2),
            width, lane_height,
            boxstyle="round,pad=0.03",
            facecolor=color,
            edgecolor="#ffffff",
            linewidth=0.6,
            alpha=0.9,
        )
        ax.add_patch(rect)

        # Label inside or next to the bar
        label_text = f"F{row['frame_id']} ({row['duration_ms']:.1f}ms)"
        if width > 10.0:
            ax.text(
                row["start_ms"] + width / 2,
                y,
                label_text,
                ha="center", va="center",
                fontsize=8, color="white", fontweight="bold",
                clip_on=True,
            )
        elif width > 2.0:
            ax.text(
                row["start_ms"] + width / 2,
                y,
                f"F{row['frame_id']}",
                ha="center", va="center",
                fontsize=8, color="white", fontweight="bold",
                clip_on=True,
            )

    # Set axis properties
    ax.set_yticks([module_y[m] for m in reversed(modules)])
    ax.set_yticklabels([m.replace("_", " ").title() for m in reversed(modules)], color="white", fontsize=10.5, fontweight="bold")
    ax.set_ylim(-0.8, len(modules) - 0.2)
    ax.set_xlim(-1, df_zoom["end_ms"].max() * 1.05)
    ax.set_xlabel("Empirical Timeline (ms) from first frame start", color="white", fontsize=11, fontweight="bold")
    
    # Subtitle with hardware info
    hardware_info = "Intel Core i7-7600U @ 2.80GHz (2 Cores, 4 Threads)"
    ax.set_title(
        f"{algo_name} Pure Empirical CSV Benchmark — {dataset_name.capitalize()} Dataset\nHardware: {hardware_info}",
        color="white", fontsize=13.5, fontweight="bold", pad=16,
    )
    
    ax.tick_params(colors="white")
    ax.spines[:].set_edgecolor("#555")
    ax.grid(axis="x", color="#ffffff22", linestyle="--", linewidth=0.5)

    # Legend for frames
    legend_handles = [
        Line2D([0], [0], color=frame_colors[f], linewidth=8, label=f"Frame {f}")
        for f in frames
    ]
    ax.legend(handles=legend_handles, loc="upper right",
              facecolor="#0f3460", edgecolor="#555", labelcolor="white",
              fontsize=8.5, ncol=min(len(frames), 5), framealpha=0.85)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[✔] Saved {algo_name} Pure Empirical Gantt chart → {out_path}")

def main():
    parser = argparse.ArgumentParser(description="Pure Empirical Timing Visualizer")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--algo", default="OpenVINS")
    parser.add_argument("--dataset", default="suedhoehe")
    parser.add_argument("--start-frame", type=int, default=100)
    parser.add_argument("--num-frames", type=int, default=5)
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df = load_csv_pure_empirical(args.csv)
    plot_gantt_pure_empirical(
        df, args.out, args.algo, args.dataset,
        start_frame=args.start_frame, num_frames=args.num_frames
    )

if __name__ == "__main__":
    main()
