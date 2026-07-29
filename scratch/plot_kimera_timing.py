#!/usr/bin/env python3
"""
Kimera-VIO Pipeline Timing Visualizer
====================================
Parses Kimera-VIO's output_frontend_stats.csv and generates:
  1. Distribution plot (Violin + Box)
  2. Macro Gantt chart across frames
  3. Zoomed frame-by-frame Gantt chart
  4. Summary statistics CSV
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

# ── Colour palette ─────────────────────────────────────────────────────────────
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
    
    # Melt timing columns into long format
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


def plot_distribution(df: pd.DataFrame, out_dir: str):
    order = ["featureDetectionTime", "featureTrackingTime", "monoRansacTime", "stereoRansacTime", "featureSelectionTime"]
    stages_ordered = [s for s in order if s in df["module"].unique()]
    data_per_stage = [df[df["module"] == s]["duration_ms"].dropna().values for s in stages_ordered]

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    positions = range(1, len(stages_ordered) + 1)
    vp = ax.violinplot(data_per_stage, positions=list(positions), showmedians=False, showextrema=False)

    for i, body in enumerate(vp["bodies"]):
        col = stage_colour(stages_ordered[i])
        body.set_facecolor(col)
        body.set_edgecolor("white")
        body.set_alpha(0.7)

    ax.boxplot(
        data_per_stage,
        positions=list(positions),
        widths=0.12,
        patch_artist=True,
        showfliers=True,
        medianprops=dict(color="white", linewidth=2),
        boxprops=dict(facecolor="#ffffff22", edgecolor="white"),
        whiskerprops=dict(color="white"),
        capprops=dict(color="white"),
        flierprops=dict(marker=".", color="white", alpha=0.3, markersize=3),
    )

    for i, vals in enumerate(data_per_stage):
        if len(vals) == 0:
            continue
        jitter = np.random.uniform(-0.08, 0.08, size=len(vals))
        ax.scatter(i + 1 + jitter, vals, alpha=0.2, s=6, color=stage_colour(stages_ordered[i]), zorder=3)

    ax.set_xticks(list(positions))
    ax.set_xticklabels(
        [s.replace("Time", "").replace("feature", "feat_") for s in stages_ordered],
        color="white", fontsize=10, fontweight="bold",
    )
    ax.set_ylabel("Duration (ms)", color="white", fontsize=12)
    ax.set_title(
        "Kimera-VIO Frontend Pipeline — Stage Duration Distributions (EuRoC MH_01_easy)",
        color="white", fontsize=14, fontweight="bold", pad=16,
    )
    ax.tick_params(colors="white")
    ax.spines[:].set_edgecolor("#555")
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.grid(axis="y", color="#ffffff22", linestyle="--", linewidth=0.6)

    plt.tight_layout()
    path = os.path.join(out_dir, "timing_distribution.png")
    plt.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[✔] Kimera distribution plot saved → {path}")


def plot_gantt_macro(df: pd.DataFrame, out_dir: str, max_frames: int = 50):
    frames = sorted(df["frame_id"].unique())[:max_frames]
    df_g = df[df["frame_id"].isin(frames)].copy()

    t0 = df_g["start_ms"].min()
    df_g["rel_start_ms"] = df_g["start_ms"] - t0
    df_g["rel_end_ms"]   = df_g["end_ms"] - t0

    fig, ax = plt.subplots(figsize=(18, 4))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    lane_height = 0.6
    for _, row in df_g.iterrows():
        width = max(row["rel_end_ms"] - row["rel_start_ms"], 0.1)
        rect = mpatches.FancyBboxPatch(
            (row["rel_start_ms"], -lane_height / 2),
            width, lane_height,
            boxstyle="round,pad=0.02",
            facecolor=stage_colour(row["module"]),
            edgecolor="#1a1a2e",
            linewidth=0.3,
            alpha=0.9,
        )
        ax.add_patch(rect)

    ax.set_yticks([0])
    ax.set_yticklabels(["Frontend Thread"], color="white", fontsize=11, fontweight="bold")
    ax.set_ylim(-0.8, 0.8)
    ax.set_xlim(0, df_g["rel_end_ms"].max() * 1.02)
    ax.set_xlabel("Elapsed Time (ms)", color="white", fontsize=12)
    ax.set_title(
        f"Kimera-VIO Frontend Timeline — Macro View ({max_frames} frames)",
        color="white", fontsize=14, fontweight="bold", pad=14,
    )
    ax.tick_params(colors="white")
    ax.spines[:].set_edgecolor("#555")
    ax.grid(axis="x", color="#ffffff22", linestyle="--", linewidth=0.5)

    legend_handles = [
        Line2D([0], [0], color=stage_colour(s), linewidth=8, label=s)
        for s in STAGE_COLOURS
        if s in df_g["module"].values
    ]
    ax.legend(handles=legend_handles, loc="upper right",
              facecolor="#0f3460", edgecolor="#555", labelcolor="white",
              fontsize=9, ncol=2, framealpha=0.85)

    plt.tight_layout()
    path = os.path.join(out_dir, "timing_gantt.png")
    plt.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[✔] Kimera Macro Gantt chart saved → {path}")


def plot_gantt_zoomed(df: pd.DataFrame, out_dir: str, start_frame: int = 50, num_frames: int = 8):
    frames = [f for f in sorted(df["frame_id"].unique()) if f >= start_frame][:num_frames]
    df_zoom = df[df["frame_id"].isin(frames)].copy()

    if df_zoom.empty:
        return

    t0 = df_zoom["start_ms"].min()
    df_zoom["rel_start_ms"] = df_zoom["start_ms"] - t0
    df_zoom["rel_end_ms"]   = df_zoom["end_ms"] - t0

    frame_y = {f: i for i, f in enumerate(reversed(frames))}
    lane_height = 0.55

    fig, ax = plt.subplots(figsize=(16, 1 + 1.2 * len(frames)))
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
                fontsize=7, color="white", fontweight="bold",
                clip_on=True,
            )

    ax.set_yticks([frame_y[f] for f in reversed(frames)])
    ax.set_yticklabels([f"Frame {f}" for f in reversed(frames)], color="white", fontsize=11, fontweight="bold")
    ax.set_ylim(-0.8, len(frames) - 0.2)
    ax.set_xlim(-1, df_zoom["rel_end_ms"].max() * 1.02)
    ax.set_xlabel("Relative Time (ms)", color="white", fontsize=12)
    ax.set_title(
        f"Kimera-VIO Detailed Frontend Sequence — Zoomed (Frames {frames[0]}–{frames[-1]})",
        color="white", fontsize=14, fontweight="bold", pad=14,
    )
    ax.tick_params(colors="white")
    ax.spines[:].set_edgecolor("#555")
    ax.grid(axis="x", color="#ffffff22", linestyle="--", linewidth=0.5)

    legend_handles = [
        Line2D([0], [0], color=stage_colour(s), linewidth=8, label=s)
        for s in STAGE_COLOURS
        if s in df_zoom["module"].values
    ]
    ax.legend(handles=legend_handles, loc="upper right",
              facecolor="#0f3460", edgecolor="#555", labelcolor="white",
              fontsize=9, ncol=2, framealpha=0.85)

    plt.tight_layout()
    path = os.path.join(out_dir, "timing_gantt_zoomed.png")
    plt.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[✔] Kimera Zoomed Gantt chart saved → {path}")


def compute_summary(df: pd.DataFrame, out_dir: str):
    stats = (
        df.groupby("module")["duration_ms"]
        .agg(
            count="count",
            mean="mean",
            median="median",
            std="std",
            min="min",
            max="max",
            p95=lambda x: x.quantile(0.95),
        )
        .reset_index()
        .round(4)
    )
    path = os.path.join(out_dir, "timing_summary.csv")
    stats.to_csv(path, index=False)
    print(f"[✔] Kimera Summary CSV saved → {path}")
    print("\n" + stats.to_string(index=False))


def main():
    csv_path = "/home/terrence/researchProject/results/euroc/output_frontend_stats.csv"
    out_dir = "/home/terrence/.gemini/antigravity/brain/a11cb992-df0e-453e-9ddc-8fac8d927cda/kimera_timing_plots"
    os.makedirs(out_dir, exist_ok=True)

    print(f"[•] Loading Kimera stats from {csv_path} …")
    df = load_kimera_csv(csv_path)
    print(f"[•] Loaded {len(df):,} timing records across {df['frame_id'].nunique()} frames")

    plot_distribution(df, out_dir)
    plot_gantt_macro(df, out_dir, max_frames=50)
    plot_gantt_zoomed(df, out_dir, start_frame=50, num_frames=8)
    compute_summary(df, out_dir)
    print("\n[✔] All Kimera plots generated successfully!")


if __name__ == "__main__":
    main()
