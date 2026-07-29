#!/usr/bin/env python3
"""
Pipeline Timing Visualizer for SLAM / VIO Benchmarking
======================================================
Reads scoped-timer CSVs and generates clean, presentation-ready Gantt charts.
"""

import argparse
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

STAGE_COLOURS = {
    "feature_tracking":      "#DD8452",
    "track_stereo":          "#DD8452",
    "imu_propagation":       "#55A868",
    "msckf_update":          "#C44E52",
    "slam_update":           "#8172B2",
    "slam_delayed_init":     "#937860",
    "retriangulation":       "#DA8BC3",
    "marginalization":       "#8C8C8C",
    "zupt_update":           "#CCB974",
    "image_preprocessing":   "#4C72B0",
    "featureDetectionTime":  "#DD8452",
    "featureTrackingTime":   "#55A868",
    "monoRansacTime":        "#C44E52",
    "stereoRansacTime":      "#8172B2",
    "featureSelectionTime":  "#937860",
}
DEFAULT_COLOUR = "#64b5f6"

def stage_colour(name: str) -> str:
    return STAGE_COLOURS.get(name, DEFAULT_COLOUR)


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    assert {"frame_id", "module", "thread_id", "start_ns", "end_ns", "duration_ms"}.issubset(
        df.columns
    ), f"Missing columns. Got: {list(df.columns)}"
    uid_map = {uid: f"Thread-{i+1}" for i, uid in enumerate(sorted(df["thread_id"].unique()))}
    df["thread_label"] = df["thread_id"].map(uid_map)
    return df


def plot_gantt_zoomed(df: pd.DataFrame, out_path: str, algo_name: str, dataset_name: str, start_frame: int = 100, num_frames: int = 8):
    frames = [f for f in sorted(df["frame_id"].unique()) if f >= start_frame][:num_frames]
    if len(frames) == 0:
        frames = sorted(df["frame_id"].unique())[:num_frames]

    df_zoom = df[(df["frame_id"].isin(frames)) & (df["module"] != "total_frame")].copy()
    if df_zoom.empty:
        print(f"[!] Warning: Zoomed range empty for {algo_name}, skipping")
        return

    t0 = df_zoom["start_ns"].min()
    df_zoom["start_ms"] = (df_zoom["start_ns"] - t0) * 1e-6
    df_zoom["end_ms"]   = (df_zoom["end_ns"]   - t0) * 1e-6

    frame_y = {f: i for i, f in enumerate(reversed(frames))}
    lane_height = 0.55

    fig, ax = plt.subplots(figsize=(16, 1.2 + 1.1 * len(frames)))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    for _, row in df_zoom.iterrows():
        y = frame_y[row["frame_id"]]
        width = max(row["end_ms"] - row["start_ms"], 0.08)
        rect = mpatches.FancyBboxPatch(
            (row["start_ms"], y - lane_height / 2),
            width, lane_height,
            boxstyle="round,pad=0.03",
            facecolor=stage_colour(row["module"]),
            edgecolor="#ffffff",
            linewidth=0.6,
            alpha=0.9,
        )
        ax.add_patch(rect)
        if width > 1.0:
            ax.text(
                row["start_ms"] + width / 2,
                y,
                f"{row['module'].replace('_', ' ')}\n({row['duration_ms']:.1f}ms)",
                ha="center", va="center",
                fontsize=8, color="white", fontweight="bold",
                clip_on=True,
            )

    ax.set_yticks([frame_y[f] for f in reversed(frames)])
    ax.set_yticklabels([f"Frame {f}" for f in reversed(frames)], color="white", fontsize=11, fontweight="bold")
    ax.set_ylim(-0.8, len(frames) - 0.2)
    ax.set_xlim(-1, df_zoom["end_ms"].max() * 1.05)
    ax.set_xlabel("Relative Time (ms)", color="white", fontsize=12, fontweight="bold")
    ax.set_title(
        f"{algo_name} Pipeline Gantt Chart — {dataset_name} Dataset (Frames {frames[0]}–{frames[-1]})",
        color="white", fontsize=15, fontweight="bold", pad=16,
    )
    ax.tick_params(colors="white")
    ax.spines[:].set_edgecolor("#555")
    ax.grid(axis="x", color="#ffffff22", linestyle="--", linewidth=0.5)

    legend_handles = [
        Line2D([0], [0], color=stage_colour(s), linewidth=8, label=s.replace("_", " "))
        for s in df_zoom["module"].unique()
    ]
    ax.legend(handles=legend_handles, loc="upper right",
              facecolor="#0f3460", edgecolor="#555", labelcolor="white",
              fontsize=9, ncol=2, framealpha=0.85)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[✔] Saved {algo_name} Gantt chart → {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Timing visualizer")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--algo", default="OpenVINS")
    parser.add_argument("--dataset", default="Suedhohe")
    parser.add_argument("--start-frame", type=int, default=100)
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df = load_csv(args.csv)
    plot_gantt_zoomed(df, args.out, args.algo, args.dataset, start_frame=args.start_frame)

if __name__ == "__main__":
    main()
