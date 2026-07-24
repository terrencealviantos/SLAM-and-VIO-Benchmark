#!/usr/bin/env python3
"""
OpenVINS Pipeline Timing Visualizer
====================================
Reads the scoped-timer CSV produced by the instrumented OpenVINS build
and generates:
  1. Violin + box plot — distribution of per-stage durations across all frames
  2. Macro Gantt chart — thread timeline across frames
  3. Detailed Zoomed Gantt chart — frame-by-frame breakdown showing sub-stage sequence

Usage:
    python3 plot_timing.py --csv /output/ov_scoped_timing.csv --out /output/timing_plots
"""

import argparse
import os

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

# ── Colour palette (one colour per stage) ───────────────────────────────────────
STAGE_COLOURS = {
    "feature_tracking":  "#DD8452",
    "imu_propagation":   "#55A868",
    "msckf_update":      "#C44E52",
    "slam_update":       "#8172B2",
    "slam_delayed_init": "#937860",
    "retriangulation":   "#DA8BC3",
    "marginalization":   "#8C8C8C",
    "zupt_update":       "#CCB974",
}
DEFAULT_COLOUR = "#64b5f6"


def stage_colour(name: str) -> str:
    return STAGE_COLOURS.get(name, DEFAULT_COLOUR)


# ── Load CSV ─────────────────────────────────────────────────────────────────────
def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    assert {"frame_id", "module", "thread_id", "start_ns", "end_ns", "duration_ms"}.issubset(
        df.columns
    ), f"Missing columns. Got: {list(df.columns)}"
    uid_map = {uid: f"Thread-{i+1}" for i, uid in enumerate(sorted(df["thread_id"].unique()))}
    df["thread_label"] = df["thread_id"].map(uid_map)
    return df


# ── 1. Violin + Box Distribution Plot ────────────────────────────────────────────
def plot_distribution(df: pd.DataFrame, out_dir: str):
    stages = [s for s in df["module"].unique() if s != "total_frame"]
    order = [
        "feature_tracking", "imu_propagation", "msckf_update",
        "slam_update", "slam_delayed_init", "retriangulation",
        "marginalization", "zupt_update",
    ]
    stages_ordered = [s for s in order if s in stages] + [s for s in stages if s not in order]
    data_per_stage = [df[df["module"] == s]["duration_ms"].dropna().values for s in stages_ordered]

    fig, ax = plt.subplots(figsize=(14, 7))
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
        [s.replace("_", "\n") for s in stages_ordered],
        color="white", fontsize=10, fontweight="bold",
    )
    ax.set_ylabel("Duration (ms)", color="white", fontsize=12)
    ax.set_title(
        "OpenVINS Pipeline — Stage Duration Distributions (EuRoC MH_01_easy)",
        color="white", fontsize=15, fontweight="bold", pad=16,
    )
    ax.tick_params(colors="white")
    ax.spines[:].set_edgecolor("#555")
    ax.yaxis.set_minor_locator(ticker.AutoMinorLocator())
    ax.grid(axis="y", color="#ffffff22", linestyle="--", linewidth=0.6)
    ax.grid(axis="y", which="minor", color="#ffffff11", linestyle=":", linewidth=0.4)

    plt.tight_layout()
    path = os.path.join(out_dir, "timing_distribution.png")
    plt.savefig(path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"[✔] Distribution plot saved → {path}")


# ── 2. Macro Thread Gantt Chart ──────────────────────────────────────────────────
def plot_gantt_macro(df: pd.DataFrame, out_dir: str, max_frames: int = 50):
    # Filter out total_frame to prevent overlapping blocks!
    df_sub = df[df["module"] != "total_frame"].copy()
    frames = sorted(df_sub["frame_id"].unique())[:max_frames]
    df_g = df_sub[df_sub["frame_id"].isin(frames)].copy()

    t0 = df_g["start_ns"].min()
    df_g["start_ms"] = (df_g["start_ns"] - t0) * 1e-6
    df_g["end_ms"]   = (df_g["end_ns"]   - t0) * 1e-6

    threads = sorted(df_g["thread_label"].unique())
    thread_y = {t: i for i, t in enumerate(threads)}
    lane_height = 0.65

    fig, ax = plt.subplots(figsize=(20, 3 + 2 * len(threads)))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    for _, row in df_g.iterrows():
        y = thread_y[row["thread_label"]]
        width = max(row["end_ms"] - row["start_ms"], 0.1)
        rect = mpatches.FancyBboxPatch(
            (row["start_ms"], y - lane_height / 2),
            width, lane_height,
            boxstyle="round,pad=0.02",
            facecolor=stage_colour(row["module"]),
            edgecolor="#1a1a2e",
            linewidth=0.3,
            alpha=0.9,
        )
        ax.add_patch(rect)

    ax.set_yticks(list(thread_y.values()))
    ax.set_yticklabels(list(thread_y.keys()), color="white", fontsize=11, fontweight="bold")
    ax.set_ylim(-0.8, len(threads) - 0.2)
    ax.set_xlim(0, df_g["end_ms"].max() * 1.02)
    ax.set_xlabel("Elapsed Time (ms)", color="white", fontsize=12)
    ax.set_title(
        f"OpenVINS Thread Execution Timeline — Macro View ({max_frames} frames, {len(threads)} thread(s))",
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
    print(f"[✔] Macro Gantt chart saved → {path}")


# ── 3. Zoomed Sequential Sub-stage Gantt Chart ────────────────────────────────────
def plot_gantt_zoomed(df: pd.DataFrame, out_dir: str, start_frame: int = 200, num_frames: int = 8):
    # Filter for initialized frames (e.g. frame 200 to 208)
    frames = [f for f in sorted(df["frame_id"].unique()) if f >= start_frame][:num_frames]
    df_zoom = df[(df["frame_id"].isin(frames)) & (df["module"] != "total_frame")].copy()

    if df_zoom.empty:
        print("[!] Warning: Zoomed range empty, skipping zoomed gantt")
        return

    t0 = df_zoom["start_ns"].min()
    df_zoom["start_ms"] = (df_zoom["start_ns"] - t0) * 1e-6
    df_zoom["end_ms"]   = (df_zoom["end_ns"]   - t0) * 1e-6

    # Plot each frame on its own row to show exact sequence of stages!
    frame_y = {f: i for i, f in enumerate(reversed(frames))}
    lane_height = 0.55

    fig, ax = plt.subplots(figsize=(18, 1 + 1.2 * len(frames)))
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
        if width > 1.2:
            ax.text(
                row["start_ms"] + width / 2,
                y,
                f"{row['module'].replace('_', ' ')}\n({row['duration_ms']:.1f}ms)",
                ha="center", va="center",
                fontsize=7, color="white", fontweight="bold",
                clip_on=True,
            )

    ax.set_yticks([frame_y[f] for f in reversed(frames)])
    ax.set_yticklabels([f"Frame {f}" for f in reversed(frames)], color="white", fontsize=11, fontweight="bold")
    ax.set_ylim(-0.8, len(frames) - 0.2)
    ax.set_xlim(-1, df_zoom["end_ms"].max() * 1.02)
    ax.set_xlabel("Relative Time (ms)", color="white", fontsize=12)
    ax.set_title(
        f"OpenVINS Detailed Pipeline Sequence — Zoomed (Frames {frames[0]}–{frames[-1]})",
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
    print(f"[✔] Zoomed Gantt chart saved → {path}")


# ── 4. Summary statistics CSV ─────────────────────────────────────────────────────
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
    print(f"[✔] Summary CSV saved → {path}")
    print("\n" + stats.to_string(index=False))


# ── Main ──────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="OpenVINS timing visualizer")
    parser.add_argument("--csv", required=True, help="Path to ov_scoped_timing.csv")
    parser.add_argument("--out", default=".", help="Output directory for plots and summary")
    parser.add_argument("--max-frames", type=int, default=50, help="Max frames shown in macro Gantt")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    print(f"[•] Loading {args.csv} …")
    df = load_csv(args.csv)
    print(f"[•] Loaded {len(df):,} timing events across {df['frame_id'].nunique()} frames "
          f"and {df['thread_id'].nunique()} thread(s)")

    plot_distribution(df, args.out)
    plot_gantt_macro(df, args.out, max_frames=args.max_frames)
    plot_gantt_zoomed(df, args.out, start_frame=200, num_frames=8)
    compute_summary(df, args.out)
    print("\n[✔] All plots generated successfully!")


if __name__ == "__main__":
    main()
