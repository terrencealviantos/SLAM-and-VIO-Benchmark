#!/usr/bin/env python3
"""Draw a Gantt chart of one benchmark run from the timing log that run wrote.

Every bar is a measured interval (start and end timestamp) from the run's own log;
nothing is typed in or simulated. If an algorithm's run has no per-module timing log,
no chart is produced.

Usage (inside slam-base, evo/matplotlib from workspace/.python_deps):
    python3 plot_gantt.py <results/<dataset>/<algo>> <algo> [--dataset NAME] [--frames N] [--start-frame F]

Writes into the results folder:
    gantt_chart.png            N consecutive frames on a real time axis
    gantt_module_summary.csv   per-module count/mean/median/p95/max over the whole run

Supported logs (same columns: frame_id, module, thread_id, start_ns, end_ns, duration_ms):
    openvins  ov_scoped_timing.csv        written by OpenVINS' scoped timers (ov_core/src/utils/timing.h)
    orbslam3  orbslam3_scoped_timing.csv  written at ORB-SLAM3's REGISTER_TIMES points
                                          (workspace/orbslam3_ws/ORB_SLAM3/include/ScopedTiming.h)
    kimera    kimera_scoped_timing.csv    written in Kimera's PipelineModule::spin()
                                          (workspace/kimera_ws/kimera_benchmark.patch);
                                          frame_id is the camera timestamp [ns]

This script only plots. The timing itself is recorded by the algorithm while it runs.
"""
import argparse
import csv
import os
import sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

# Pipeline order of the OpenVINS scoped timers (VioManager.cpp)
OPENVINS_MODULES = [
    "total_frame", "feature_tracking", "zupt_update", "imu_propagation", "msckf_update",
    "slam_update", "slam_delayed_init", "retriangulation", "marginalization",
]


# Tracking, local mapping and loop closing are separate threads in ORB-SLAM3
ORBSLAM3_MODULES = [
    "tracking/total_frame", "tracking/orb_extraction", "tracking/stereo_matching",
    "tracking/imu_preintegration", "tracking/pose_prediction", "tracking/track_local_map",
    "tracking/keyframe_decision",
    "local_mapping/total", "local_mapping/process_new_keyframe", "local_mapping/map_point_culling",
    "local_mapping/map_point_creation", "local_mapping/local_ba", "local_mapping/keyframe_culling",
    "loop_closing/place_recognition", "loop_closing/map_merge", "loop_closing/loop_correction",
]

ALGORITHMS = {
    # log file, module order, module that marks a frame boundary,
    # module that marks frames worth showing (full pipeline / keyframe processing)
    "openvins": dict(log="ov_scoped_timing.csv", order=OPENVINS_MODULES,
                     frame_module="total_frame", focus_module="msckf_update"),
    "orbslam3": dict(log="orbslam3_scoped_timing.csv", order=ORBSLAM3_MODULES,
                     frame_module="tracking/total_frame", focus_module="local_mapping/local_ba"),
    # Kimera modules run in their own threads (parallel_run); the backend only gets keyframes
    "kimera": dict(log="kimera_scoped_timing.csv", order=["VioFrontend", "VioBackend", "Mesher"],
                   frame_module="VioFrontend", focus_module="VioBackend"),
}


def read_log(results_dir, log_name):
    path = os.path.join(results_dir, log_name)
    if not os.path.exists(path):
        return None, path
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            if not r.get("duration_ms"):  # the last row can be cut off when the node is stopped
                continue
            rows.append(dict(frame=int(r["frame_id"]), module=r["module"], thread=r["thread_id"],
                             start=int(r["start_ns"]), end=int(r["end_ns"]),
                             dur=float(r["duration_ms"])))
    return rows, path


def summary(rows, out_csv, order):
    per = defaultdict(list)
    for r in rows:
        per[r["module"]].append(r["dur"])
    modules = [m for m in order if m in per] + sorted(m for m in per if m not in order)
    with open(out_csv, "w") as f:
        f.write("module,count,mean_ms,median_ms,p95_ms,max_ms\n")
        for m in modules:
            v = np.array(per[m])
            f.write(f"{m},{v.size},{v.mean():.4f},{np.median(v):.4f},"
                    f"{np.percentile(v, 95):.4f},{v.max():.4f}\n")
    return modules


def pick_window(rows, n_frames, start_frame, frame_module, focus_module):
    """N consecutive processed frames (in the order of `frame_module`). By default centred
    on the middle one of the frames that have `focus_module` (OpenVINS: frames after
    initialisation; ORB-SLAM3 / Kimera: keyframes, so the mapping/backend thread is visible).
    Frame ids may be numbers (OpenVINS, ORB-SLAM3) or timestamps (Kimera)."""
    frames = sorted({r["frame"] for r in rows if r["module"] == frame_module})
    focus = sorted({r["frame"] for r in rows if r["module"] == focus_module} & set(frames))
    if start_frame is not None:
        i0 = frames.index(start_frame)
    else:
        centre = focus[len(focus) // 2] if focus else frames[len(frames) // 2]
        i0 = max(frames.index(centre) - n_frames // 2, 0)
    return frames[i0:i0 + n_frames], i0


def plot(rows, modules, window, first_index, title, source, out_png, frame_module):
    sel = [r for r in rows if r["frame"] in window]
    if not sel:
        sys.exit(f"no timing rows for frames {window[0]}..{window[-1]}")
    t0 = min(r["start"] for r in sel)
    lanes = [m for m in modules if any(r["module"] == m for r in sel)]
    colors = {m: plt.cm.tab20(i % 20) for i, m in enumerate(lanes)}

    fig, ax = plt.subplots(figsize=(13, 0.5 * len(lanes) + 2.2))
    for r in sel:
        y = len(lanes) - 1 - lanes.index(r["module"])
        start_ms = (r["start"] - t0) * 1e-6
        ax.barh(y, (r["end"] - r["start"]) * 1e-6, left=start_ms, height=0.6,
                color=colors[r["module"]], edgecolor="white", linewidth=1.2)
    # frame boundaries = start of each frame's total timer
    for i, f in enumerate(window):
        starts = [r["start"] for r in sel if r["frame"] == f and r["module"] == frame_module]
        if starts:
            x = (starts[0] - t0) * 1e-6
            ax.axvline(x, color="gray", lw=0.6, ls="--")
            ax.text(x, len(lanes) - 0.45, f"frame {first_index + i}", fontsize=7, color="gray",
                    rotation=90, va="bottom", ha="right")
    ax.set_yticks(range(len(lanes)), list(reversed(lanes)))
    ax.set_xlabel("wall-clock time since first bar [ms]")
    ax.set_title(title)
    ax.set_ylim(-0.6, len(lanes) + 0.6)
    ax.grid(axis="x", alpha=0.3)
    fig.text(0.01, 0.01, f"measured intervals from {source}", fontsize=7, color="gray")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out_png, dpi=150)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results_dir")
    ap.add_argument("algo")
    ap.add_argument("--dataset", default=None, help="name for the title (default: parent folder name)")
    ap.add_argument("--frames", type=int, default=5)
    ap.add_argument("--start-frame", type=int, default=None)
    args = ap.parse_args()

    dataset = args.dataset or os.path.basename(os.path.dirname(os.path.abspath(args.results_dir)))
    out_png = os.path.join(args.results_dir, "gantt_chart.png")
    if os.path.exists(out_png):
        os.remove(out_png)  # never leave a chart from an earlier run behind

    if args.algo not in ALGORITHMS:
        print(f"[INFO] No per-module timing log is recorded for '{args.algo}' yet; no Gantt chart generated.")
        return
    cfg = ALGORITHMS[args.algo]
    rows, source = read_log(args.results_dir, cfg["log"])
    order = cfg["order"]
    if not rows:
        print(f"[INFO] {source} missing or empty; no Gantt chart generated.")
        return

    modules = summary(rows, os.path.join(args.results_dir, "gantt_module_summary.csv"), order)
    window, i0 = pick_window(rows, args.frames, args.start_frame, cfg["frame_module"], cfg["focus_module"])
    label = f"frames {i0}-{i0 + len(window) - 1}"
    if args.algo == "kimera":
        label += " of the processed sequence"
    plot(rows, modules, window, i0, f"{args.algo} on {dataset}: {label} (measured)",
         os.path.basename(source), out_png, cfg["frame_module"])
    print(f"[OK] {out_png} ({label}), summary in gantt_module_summary.csv")


if __name__ == "__main__":
    main()
