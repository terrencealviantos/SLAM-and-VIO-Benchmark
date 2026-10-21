#!/usr/bin/env python3
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def load_tum(filepath):
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) >= 8:
                t = float(parts[0])
                x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                qx, qy, qz, qw = float(parts[4]), float(parts[5]), float(parts[6]), float(parts[7])
                data.append((t, x, y, z, qx, qy, qz, qw))
    data = np.array(data)
    idx = np.argsort(data[:, 0])
    return data[idx]

def associate(gt, est, max_diff=0.05):
    gt_times = gt[:, 0]
    est_times = est[:, 0]
    matches = []
    j = 0
    for i, t_est in enumerate(est_times):
        while j < len(gt_times) - 1 and gt_times[j+1] <= t_est:
            j += 1
        best_j = j
        diff = abs(gt_times[j] - t_est)
        if j + 1 < len(gt_times) and abs(gt_times[j+1] - t_est) < diff:
            best_j = j + 1
            diff = abs(gt_times[j+1] - t_est)
        if diff <= max_diff:
            matches.append((best_j, i))
    return matches

def umeyama_alignment(model, data):
    mu_m = model.mean(axis=1, keepdims=True)
    mu_d = data.mean(axis=1, keepdims=True)
    m_centered = model - mu_m
    d_centered = data - mu_d
    
    H = d_centered @ m_centered.T
    U, S, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = Vt.T @ U.T
    t = mu_m - R @ mu_d
    return R, t

def main():
    if len(sys.argv) < 4:
        print("Usage: plot_openvins_gt.py <est_tum> <gt_tum> <out_png> [title]")
        sys.exit(1)
        
    est_path = sys.argv[1]
    gt_path = sys.argv[2]
    out_png = sys.argv[3]
    title = sys.argv[4] if len(sys.argv) > 4 else "OpenVINS vs Ground Truth"

    print(f"Loading Estimate: {est_path}")
    est = load_tum(est_path)
    print(f"Loaded {len(est)} poses.")

    print(f"Loading Ground Truth: {gt_path}")
    gt = load_tum(gt_path)
    print(f"Loaded {len(gt)} poses.")

    matches = associate(gt, est, max_diff=0.05)
    print(f"Associated {len(matches)} matching poses.")

    if len(matches) < 10:
        print("Warning: Few or no matching timestamps, plotting without temporal alignment.")
        gt_xyz = gt[:, 1:4]
        est_xyz = est[:, 1:4]
        aligned_est_xyz = est_xyz
        has_matched = False
    else:
        gt_idx = [m[0] for m in matches]
        est_idx = [m[1] for m in matches]
        
        m_pts = gt[gt_idx, 1:4].T
        d_pts = est[est_idx, 1:4].T
        
        R, t = umeyama_alignment(m_pts, d_pts)
        
        all_est_pts = est[:, 1:4].T
        aligned_est_xyz = (R @ all_est_pts + t).T
        gt_xyz = gt[:, 1:4]
        
        matched_gt_xyz = m_pts.T
        matched_est_xyz = (R @ d_pts + t).T
        errors = np.linalg.norm(matched_gt_xyz - matched_est_xyz, axis=1)
        rel_times = gt[gt_idx, 0] - gt[gt_idx[0], 0]
        
        rmse = np.sqrt(np.mean(errors**2))
        mean_err = np.mean(errors)
        max_err = np.max(errors)
        has_matched = True
        print(f"Trajectory RMSE: {rmse:.4f} m | Mean: {mean_err:.4f} m | Max: {max_err:.4f} m")

    fig = plt.figure(figsize=(16, 9))
    fig.suptitle(f"{title}\nTrajectory Benchmark Comparison", fontsize=16, fontweight='bold', y=0.98)

    # Subplot 1: 3D Trajectory
    ax3d = fig.add_subplot(1, 2, 1, projection='3d')
    ax3d.plot(gt_xyz[:, 0], gt_xyz[:, 1], gt_xyz[:, 2], 'b--', label='Ground Truth (Ref)', linewidth=1.8, alpha=0.85)
    ax3d.plot(aligned_est_xyz[:, 0], aligned_est_xyz[:, 1], aligned_est_xyz[:, 2], 'r-', label='OpenVINS (Estimate)', linewidth=1.8, alpha=0.9)
    ax3d.scatter(gt_xyz[0, 0], gt_xyz[0, 1], gt_xyz[0, 2], c='green', marker='o', s=60, label='Start')
    ax3d.scatter(gt_xyz[-1, 0], gt_xyz[-1, 1], gt_xyz[-1, 2], c='black', marker='X', s=60, label='End')
    ax3d.set_xlabel('X [m]', fontsize=11, labelpad=8)
    ax3d.set_ylabel('Y [m]', fontsize=11, labelpad=8)
    ax3d.set_zlabel('Z [m]', fontsize=11, labelpad=8)
    ax3d.set_title('3D Trajectory (SE3 Aligned)', fontsize=13, fontweight='bold')
    ax3d.legend(loc='upper right', frameon=True, fontsize=10)
    ax3d.grid(True, linestyle=':', alpha=0.6)

    # Subplot 2: Top-Down (X-Y Projection)
    ax2d = fig.add_subplot(2, 2, 2)
    ax2d.plot(gt_xyz[:, 0], gt_xyz[:, 1], 'b--', label='Ground Truth', linewidth=1.8, alpha=0.85)
    ax2d.plot(aligned_est_xyz[:, 0], aligned_est_xyz[:, 1], 'r-', label='OpenVINS', linewidth=1.8, alpha=0.9)
    ax2d.scatter(gt_xyz[0, 0], gt_xyz[0, 1], c='green', marker='o', s=50, label='Start')
    ax2d.scatter(gt_xyz[-1, 0], gt_xyz[-1, 1], c='black', marker='X', s=50, label='End')
    ax2d.set_xlabel('X [m]', fontsize=11)
    ax2d.set_ylabel('Y [m]', fontsize=11)
    ax2d.set_title('Top-Down View (X-Y Plane)', fontsize=13, fontweight='bold')
    ax2d.axis('equal')
    ax2d.legend(loc='best', frameon=True, fontsize=9)
    ax2d.grid(True, linestyle=':', alpha=0.6)

    # Subplot 3: Absolute Position Error over Time
    ax_err = fig.add_subplot(2, 2, 4)
    if has_matched:
        ax_err.plot(rel_times, errors, 'm-', linewidth=1.2, label=f'Position Error')
        ax_err.axhline(rmse, color='darkred', linestyle='--', linewidth=1.5, label=f'RMSE: {rmse:.2f} m')
        ax_err.axhline(mean_err, color='navy', linestyle=':', linewidth=1.5, label=f'Mean: {mean_err:.2f} m')
        ax_err.set_xlabel('Time [s]', fontsize=11)
        ax_err.set_ylabel('Absolute Error [m]', fontsize=11)
        ax_err.set_title('Translation Error vs Time', fontsize=13, fontweight='bold')
        ax_err.legend(loc='upper right', frameon=True, fontsize=9)
        ax_err.grid(True, linestyle=':', alpha=0.6)
    else:
        ax_err.text(0.5, 0.5, "No temporal matches within threshold", ha='center', va='center', fontsize=12)

    plt.tight_layout()
    plt.savefig(out_png, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"[✔] Successfully saved plot to: {out_png}")

if __name__ == '__main__':
    main()
