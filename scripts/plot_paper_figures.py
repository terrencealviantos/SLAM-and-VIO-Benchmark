#!/usr/bin/env python3
"""Draw the paper figures and summary table from the files in results/.

Everything is read from the outputs of run_benchmark.sh / plot_3d_trajectory.sh:
  results/<dataset>/<algo>/<algo>_tum.txt          estimated trajectory (TUM)
  results/<dataset>/<algo>/<algo>_ape_stats.txt    evo_ape output (SE(3), 0.05 s)
  results/<dataset>/<algo>/gantt_module_summary.csv measured per-module timing
  datasets/.../gt_tum.txt                          ground truth (TUM)

Trajectories are aligned to the ground truth with the same method as evo_ape -va
(Umeyama SE(3), nearest-stamp matching within 0.05 s), so the plots show what the
APE numbers measure.

Usage (inside slam-base, from the repo root mounted at /repo):
    python3 scripts/plot_paper_figures.py [--repo /repo]

Writes figures/fig_*.png and results/summary.csv.
"""
import argparse
import csv
import os
import re
import shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

DATASETS = {
    "MH_01_easy": "datasets/MH_01_easy/gt_tum.txt",
    "V1_03_difficult": "datasets/V1_03_difficult/gt_tum.txt",
    "corridor": "datasets/tum_vi_corridor1/gt_tum.txt",
    "suedhoehe": "datasets/suedhoehe_gps_schnee_02/gt_gnss_tum.txt",
}
ALGOS = ["orbslam3", "openvins", "kimera", "cuvslam"]
LABEL = {"orbslam3": "ORB-SLAM3", "openvins": "OpenVINS", "kimera": "Kimera-VIO",
         "cuvslam": "cuVSLAM"}
COLOR = {"orbslam3": "#1f77b4", "openvins": "#ff7f0e", "kimera": "#2ca02c",
         "cuvslam": "#d62728"}
# Runs reported as failures (report.md section 2); plotted only where stated.
FAILED = {("corridor", "kimera"): "diverged", ("suedhoehe", "orbslam3"): "tracking lost",
          ("V1_03_difficult", "cuvslam"): "failed", ("MH_01_easy", "cuvslam"): "scale error",
          ("corridor", "cuvslam"): "not reproducible"}
# Per-frame (front-end) timer of each algorithm
FRAME_MODULE = {"orbslam3": "tracking/total_frame", "openvins": "total_frame",
                "kimera": "VioFrontend"}
MAX_DT = 0.05


def load_tum(path):
    d = np.loadtxt(path, comments="#", ndmin=2)
    return d[:, 0], d[:, 1:4]


def associate(t_est, t_gt):
    idx = np.searchsorted(t_gt, t_est)
    idx = np.clip(idx, 1, len(t_gt) - 1)
    left, right = t_gt[idx - 1], t_gt[idx]
    idx -= (t_est - left) < (right - t_est)
    ok = np.abs(t_gt[idx] - t_est) <= MAX_DT
    return np.nonzero(ok)[0], idx[ok]


def umeyama_se3(src, dst):
    mu_s, mu_d = src.mean(0), dst.mean(0)
    cov = (dst - mu_d).T @ (src - mu_s) / len(src)
    u, _, vt = np.linalg.svd(cov)
    s = np.eye(3)
    if np.linalg.det(u) * np.linalg.det(vt) < 0:
        s[2, 2] = -1
    r = u @ s @ vt
    return r, mu_d - r @ mu_s


def aligned(repo, ds, algo):
    est_path = os.path.join(repo, "results", ds, algo, f"{algo}_tum.txt")
    if not os.path.isfile(est_path):
        return None
    t_gt, p_gt = load_tum(os.path.join(repo, DATASETS[ds]))
    t_est, p_est = load_tum(est_path)
    i_est, i_gt = associate(t_est, t_gt)
    r, t = umeyama_se3(p_est[i_est], p_gt[i_gt])
    p_all = p_est @ r.T + t
    err = np.linalg.norm(p_all[i_est] - p_gt[i_gt], axis=1)
    return {"t": t_est, "p": p_all, "err": err, "t_err": t_est[i_est]}


def ape_from_stats(path):
    if not os.path.isfile(path):
        return None
    txt = open(path).read()
    out = {k: float(re.search(rf"\b{k}\s+([0-9.eE+-]+)", txt).group(1))
           for k in ("rmse", "mean", "median", "max")}
    m = re.search(r"Found (\d+) of max\. (\d+)", txt)
    out["matched"], out["poses"] = int(m.group(1)), int(m.group(2))
    return out


def timing(repo, ds, algo):
    path = os.path.join(repo, "results", ds, algo, "gantt_module_summary.csv")
    if not os.path.isfile(path):
        return {}
    with open(path) as f:
        return {r["module"]: r for r in csv.DictReader(f)}


def write_summary(repo):
    rows = []
    for ds in DATASETS:
        for algo in ALGOS:
            ape = ape_from_stats(os.path.join(repo, "results", ds, algo, f"{algo}_ape_stats.txt"))
            if ape is None:
                continue
            tm = timing(repo, ds, algo).get(FRAME_MODULE.get(algo, ""), {})
            rows.append({"dataset": ds, "algorithm": algo,
                         "status": FAILED.get((ds, algo), "ok"),
                         "ape_rmse_m": ape["rmse"], "ape_mean_m": ape["mean"],
                         "ape_max_m": ape["max"], "matched": ape["matched"],
                         "poses": ape["poses"],
                         "frame_ms_mean": tm.get("mean_ms", ""),
                         "frame_ms_p95": tm.get("p95_ms", "")})
    path = os.path.join(repo, "results", "summary.csv")
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("wrote", path)


def plot_trajectories(repo, out_dir, ds, algos, title, fname, plane=(0, 1)):
    t_gt, p_gt = load_tum(os.path.join(repo, DATASETS[ds]))
    fig, ax = plt.subplots(figsize=(4.6, 4.0))
    gt_style = dict(color="k", lw=1.2, label="Ground truth")
    if ds == "corridor":
        # Mocap covers only the start and end room: draw the samples, not a connecting line.
        ax.plot(p_gt[:, plane[0]], p_gt[:, plane[1]], ".", ms=1.5, color="k",
                label="Ground truth (mocap)")
    elif ds == "suedhoehe":
        ax.plot(p_gt[:, plane[0]], p_gt[:, plane[1]], ".", ms=2, color="k", label="GNSS")
    else:
        ax.plot(p_gt[:, plane[0]], p_gt[:, plane[1]], **gt_style)
    for algo in algos:
        a = aligned(repo, ds, algo)
        if a is None:
            continue
        lab = LABEL[algo]
        if (ds, algo) in FAILED:
            lab += f" ({FAILED[(ds, algo)]})"
        ax.plot(a["p"][:, plane[0]], a["p"][:, plane[1]], lw=0.9, color=COLOR[algo], label=lab)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_title(title, fontsize=10)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, loc="best")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, fname), dpi=200)
    plt.close(fig)
    print("wrote", fname)


def plot_error_over_time(repo, out_dir):
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.0), sharey=False)
    for ax, ds in zip(axes, ["MH_01_easy", "V1_03_difficult"]):
        t0 = load_tum(os.path.join(repo, DATASETS[ds]))[0][0]
        for algo in ["orbslam3", "openvins", "kimera"]:
            a = aligned(repo, ds, algo)
            ax.plot(a["t_err"] - t0, a["err"], lw=0.8, color=COLOR[algo], label=LABEL[algo])
        ax.set_title(ds, fontsize=10)
        ax.set_xlabel("time since start of sequence [s]")
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("translation error [m]")
    axes[0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "fig_ape_over_time_euroc.png"), dpi=200)
    plt.close(fig)
    print("wrote fig_ape_over_time_euroc.png")


def plot_frame_timing(repo, out_dir):
    dsets = ["MH_01_easy", "V1_03_difficult", "corridor", "suedhoehe"]
    algos = ["orbslam3", "openvins", "kimera"]
    fig, ax = plt.subplots(figsize=(7.0, 3.2))
    w = 0.26
    for j, algo in enumerate(algos):
        means, p95s, xs = [], [], []
        for i, ds in enumerate(dsets):
            r = timing(repo, ds, algo).get(FRAME_MODULE[algo])
            if not r:
                continue
            xs.append(i + (j - 1) * w)
            means.append(float(r["mean_ms"]))
            p95s.append(float(r["p95_ms"]))
        ax.bar(xs, means, w, color=COLOR[algo], label=LABEL[algo] + " (mean)")
        ax.scatter(xs, p95s, marker="_", s=150, color="k", zorder=3)
    ax.scatter([], [], marker="_", s=150, color="k", label="95th percentile")
    ax.axhline(50, color="grey", ls="--", lw=0.8)
    ax.text(-0.45, 52, "50 ms = 20 Hz camera period", fontsize=7, color="grey")
    ax.set_xticks(range(len(dsets)))
    ax.set_xticklabels([d + ("\n(Kimera diverged)" if d == "corridor" else "") for d in dsets],
                       fontsize=8)
    ax.set_ylim(0, 140)
    ax.set_ylabel("per-frame time [ms]")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(fontsize=7, ncol=4, loc="lower center", bbox_to_anchor=(0.5, 1.0), frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "fig_frame_timing.png"), dpi=200)
    plt.close(fig)
    print("wrote fig_frame_timing.png")


def plot_module_breakdown(repo, out_dir):
    """Mean time per module on MH_01_easy, one panel per algorithm."""
    sel = {
        "openvins": ["feature_tracking", "imu_propagation", "msckf_update", "slam_update",
                     "slam_delayed_init", "retriangulation", "marginalization"],
        "orbslam3": ["tracking/orb_extraction", "tracking/stereo_matching",
                     "tracking/track_local_map", "local_mapping/map_point_creation",
                     "local_mapping/local_ba", "local_mapping/keyframe_culling",
                     "loop_closing/place_recognition"],
        "kimera": ["VioFrontend", "VioBackend", "Mesher"],
    }
    fig, axes = plt.subplots(1, 3, figsize=(10, 2.9),
                             gridspec_kw={"width_ratios": [7, 7, 3]})
    for ax, algo in zip(axes, ["openvins", "orbslam3", "kimera"]):
        tm = timing(repo, "MH_01_easy", algo)
        names = [m for m in sel[algo] if m in tm]
        means = [float(tm[m]["mean_ms"]) for m in names]
        p95 = [float(tm[m]["p95_ms"]) for m in names]
        y = np.arange(len(names))
        ax.barh(y, means, color=COLOR[algo])
        ax.scatter(p95, y, marker="|", s=80, color="k", zorder=3)
        ax.set_yticks(y)
        ax.set_yticklabels([n.split("/")[-1] for n in names], fontsize=7)
        ax.invert_yaxis()
        ax.set_xscale("log")
        ax.set_xlabel("ms (bar: mean, |: p95)", fontsize=8)
        ax.set_title(LABEL[algo], fontsize=9)
        ax.grid(axis="x", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "fig_module_timing_mh01.png"), dpi=200)
    plt.close(fig)
    print("wrote fig_module_timing_mh01.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    repo = ap.parse_args().repo
    out_dir = os.path.join(repo, "figures")
    os.makedirs(out_dir, exist_ok=True)
    write_summary(repo)
    plot_trajectories(repo, out_dir, "MH_01_easy", ["orbslam3", "openvins", "kimera", "cuvslam"],
                      "EuRoC MH_01_easy", "fig_traj_mh01.png")
    plot_trajectories(repo, out_dir, "V1_03_difficult", ["orbslam3", "openvins", "kimera", "cuvslam"],
                      "EuRoC V1_03_difficult", "fig_traj_v103.png")
    plot_trajectories(repo, out_dir, "corridor", ["orbslam3", "openvins", "cuvslam"],
                      "TUM-VI corridor1", "fig_traj_corridor.png")
    plot_trajectories(repo, out_dir, "suedhoehe", ["orbslam3"],
                      "Suedhoehe (snow)", "fig_traj_suedhoehe.png")
    plot_error_over_time(repo, out_dir)
    plot_frame_timing(repo, out_dir)
    plot_module_breakdown(repo, out_dir)
    # Measured Gantt charts drawn by plot_gantt.py during evaluation
    for algo in ["openvins", "orbslam3", "kimera"]:
        src = os.path.join(repo, "results", "MH_01_easy", algo, "gantt_chart.png")
        shutil.copy(src, os.path.join(out_dir, f"fig_gantt_{algo}_mh01.png"))
        print("copied", src)


if __name__ == "__main__":
    main()
