#!/usr/bin/env python3
"""
Kimera-VIO Pipeline Timing Visualizer for Suedhohe Dataset
"""

import os
import argparse
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

STAGE_COLOURS = {
    "featureDetectionTime":  "#DD8452",
    "featureTrackingTime":   "#55A868",
    "monoRansacTime":        "#C44E52",
    "stereoRansacTime":      "#8172B2",
    "featureSelectionTime":  "#937860",
}
DEFAULT_COLOUR = "#64b5f6"

def stage_colour(name: str) -> str:
    return STAGE_COLOURS.get(name, DEFAULT_COLOUR)


def load_kimera_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    
    timing_cols = [c for c in ["featureDetectionTime", "featureTrackingTime", "monoRansacTime", "stereoRansacTime", "featureSelectionTime"] if c in df.columns]
    
    rows = []
    t0 = df["#timestamp_lkf"].iloc[0]
    
    for i, row in df.iterrows():
        frame_id = i
        t_curr = (row["#timestamp_lkf"] - t0) * 1e-6 # convert to ms
        
        cum_offset = 0.0
        for col in timing_cols:
            dur = float(row[col])
            if dur > 0:
                rows.append({
                    "frame_id": frame_id,
                    "module": col,
                    "thread_id": 1,
                    "thread_label": "Frontend Thread",
                    "start_ms": t_curr + cum_offset,
                    "end_ms": t_curr + cum_offset + dur,
                    "duration_ms": dur
                })
                cum_offset += dur
                
    df_long = pd.DataFrame(rows)
    return df_long


def plot_gantt_zoomed(df: pd.DataFrame, out_path: str, algo_name: str, dataset_name: str, start_frame: int = 50, num_frames: int = 8):
    frames = [f for f in sorted(df["frame_id"].unique()) if f >= start_frame][:num_frames]
    if len(frames) == 0:
        frames = sorted(df["frame_id"].unique())[:num_frames]

    df_zoom = df[df["frame_id"].isin(frames)].copy()
    if df_zoom.empty:
        return

    t0 = df_zoom["start_ms"].min()
    df_zoom["rel_start_ms"] = df_zoom["start_ms"] - t0
    df_zoom["rel_end_ms"]   = df_zoom["end_ms"] - t0

    frame_y = {f: i for i, f in enumerate(reversed(frames))}
    lane_height = 0.55

    fig, ax = plt.subplots(figsize=(16, 1.2 + 1.1 * len(frames)))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    for _, row in df_zoom.iterrows():
        y = frame_y[row["frame_id"]]
        width = max(row["rel_end_ms"] - row["rel_start_ms"], 0.08)
        rect = mpatches.FancyBboxPatch(
            (row["rel_start_ms"], y - lane_height / 2),
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
                row["rel_start_ms"] + width / 2,
                y,
                f"{row['module'].replace('Time', '')}\n({row['duration_ms']:.1f}ms)",
                ha="center", va="center",
                fontsize=8, color="white", fontweight="bold",
                clip_on=True,
            )

    ax.set_yticks([frame_y[f] for f in reversed(frames)])
    ax.set_yticklabels([f"Frame {f}" for f in reversed(frames)], color="white", fontsize=11, fontweight="bold")
    ax.set_ylim(-0.8, len(frames) - 0.2)
    ax.set_xlim(-1, df_zoom["rel_end_ms"].max() * 1.05)
    ax.set_xlabel("Relative Time (ms)", color="white", fontsize=12, fontweight="bold")
    ax.set_title(
        f"{algo_name} Pipeline Gantt Chart — {dataset_name} Dataset (Frames {frames[0]}–{frames[-1]})",
        color="white", fontsize=15, fontweight="bold", pad=16,
    )
    ax.tick_params(colors="white")
    ax.spines[:].set_edgecolor("#555")
    ax.grid(axis="x", color="#ffffff22", linestyle="--", linewidth=0.5)

    legend_handles = [
        Line2D([0], [0], color=stage_colour(s), linewidth=8, label=s.replace("Time", ""))
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
    parser = argparse.ArgumentParser(description="Kimera timing visualizer")
    parser.add_argument("--csv", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--algo", default="Kimera-VIO")
    parser.add_argument("--dataset", default="Suedhohe")
    parser.add_argument("--start-frame", type=int, default=50)
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df = load_kimera_csv(args.csv)
    plot_gantt_zoomed(df, args.out, args.algo, args.dataset, start_frame=args.start_frame)

if __name__ == "__main__":
    main()
