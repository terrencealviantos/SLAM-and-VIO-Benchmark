import os
import sys
import numpy as np

def load_tum(path):
    data = []
    if not os.path.exists(path):
        return None
    with open(path, 'r') as f:
        for line in f:
            if line.startswith('#'): continue
            p = line.strip().split()
            if len(p) >= 8:
                t = float(p[0])
                if t > 1e12: t *= 1e-9
                data.append((t, float(p[1]), float(p[2]), float(p[3])))
    return np.array(data) if len(data) > 0 else None

def compute_ape_rmse(gt, est, correct_scale=False):
    gt_t = gt[:, 0]
    gt_xyz = gt[:, 1:4]
    
    est_t = est[:, 0]
    est_xyz = est[:, 1:4]
    
    gt_matched = []
    est_matched = []
    
    for i, t in enumerate(est_t):
        idx = np.argmin(np.abs(gt_t - t))
        if np.abs(gt_t[idx] - t) < 0.05:
            gt_matched.append(gt_xyz[idx])
            est_matched.append(est_xyz[i])
            
    if len(gt_matched) < 10:
        return None, len(gt_matched)
        
    gt_m = np.array(gt_matched)
    est_m = np.array(est_matched)
    
    mu_gt = np.mean(gt_m, axis=0)
    mu_est = np.mean(est_m, axis=0)
    
    H = (est_m - mu_est).T @ (gt_m - mu_gt) / len(gt_m)
    U, D, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R) < 0:
        Vt[2, :] *= -1
        R = Vt.T @ U.T
        
    s = 1.0
    if correct_scale:
        var_est = np.var(est_m, axis=0).sum()
        if var_est > 1e-9:
            s = np.sum(D) / var_est

    t_opt = mu_gt - s * (R @ mu_est)
    est_aligned = s * (R @ est_m.T).T + t_opt
    errors = np.linalg.norm(gt_m - est_aligned, axis=1)
    
    rmse = np.sqrt(np.mean(errors**2))
    mean_err = np.mean(errors)
    max_err = np.max(errors)
    std_err = np.std(errors)
    
    return {
        'rmse': rmse,
        'mean': mean_err,
        'max': max_err,
        'std': std_err,
        'matched_points': len(errors)
    }, len(errors)

def find_repo_root():
    if os.path.exists("/repo/datasets"):
        return "/repo"
    cand = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.exists(os.path.join(cand, "datasets")):
        return cand
    return "/home/boris/SLAM-and-VIO-Benchmark"

def find_first_existing(candidates):
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]

if __name__ == '__main__':
    root = find_repo_root()
    print("==========================================================")
    print("      VISUAL SLAM & VIO BENCHMARK EVALUATION (SE3 APE)")
    print(f"      Repository Root: {root}")
    print("==========================================================")
    
    benchmarks = [
        ("EuRoC MH_01_easy", os.path.join(root, "datasets/MH_01_easy/gt_tum.txt"), [
            ("cuVSLAM", find_first_existing([
                os.path.join(root, "results/euroc/cuvslam/cuvslam_tum.txt"),
                os.path.join(root, "results/euroc/MH_01_easy/cuvslam_tum.txt"),
                os.path.join(root, "results/euroc/cuvslam_tum.txt"),
            ])),
            ("OpenVINS", find_first_existing([
                os.path.join(root, "results/euroc/openvins/openvins_tum.txt"),
                os.path.join(root, "results/euroc/MH_01_easy/open_vins.txt"),
                os.path.join(root, "results/euroc/open_vins.txt"),
            ])),
            ("Kimera-VIO", find_first_existing([
                os.path.join(root, "results/euroc/kimera/kimera_tum.txt"),
                os.path.join(root, "results/euroc/kimera.txt"),
            ])),
            ("ORB-SLAM3", find_first_existing([
                os.path.join(root, "results/euroc/orbslam3/orbslam3_tum.txt"),
                os.path.join(root, "results/euroc/orbslam3/orbslam3_raw.txt"),
                os.path.join(root, "results/euroc/orb_slam3.txt"),
            ])),
            ("ORB-SLAM3 KLT", find_first_existing([
                os.path.join(root, "results/euroc/orbslam3_klt/orbslam3_klt_tum.txt"),
                os.path.join(root, "results/orbslam3_klt/klt_trajectory.txt"),
            ])),
        ]),
        ("EuRoC V1_03_difficult", os.path.join(root, "datasets/V1_03_difficult/gt_tum.txt"), [
            ("cuVSLAM", os.path.join(root, "results/euroc/V1_03_difficult/cuvslam/cuvslam_tum.txt")),
            ("OpenVINS", os.path.join(root, "results/euroc/V1_03_difficult/openvins/openvins_tum.txt")),
            ("Kimera-VIO", os.path.join(root, "results/euroc/V1_03_difficult/kimera/kimera_tum.txt")),
        ]),
        ("Suedhoehe (Snow Outdoor)", os.path.join(root, "datasets/suedhoehe_gps_schnee_02/gps_trajectory.txt"), [
            ("cuVSLAM", os.path.join(root, "results/suedhoehe/cuvslam/cuvslam_tum.txt")),
            ("OpenVINS", os.path.join(root, "results/suedhoehe/openvins/openvins_tum.txt")),
            ("Kimera-VIO", os.path.join(root, "results/suedhoehe/kimera/kimera_tum.txt")),
        ])
    ]
    
    for dataset_name, gt_path, algorithms in benchmarks:
        print(f"\n--- Dataset: {dataset_name} ---")
        gt = load_tum(gt_path)
        if gt is None:
            print(f"  [ERROR] Ground truth not found at: {gt_path}")
            continue
        print(f"  Ground Truth: {len(gt)} points")
        
        for algo_name, est_path in algorithms:
            est = load_tum(est_path)
            if est is None:
                print(f"  {algo_name:15s}: ❌ Not available / No trajectory file")
                continue
            is_monocular = "klt" in algo_name.lower()
            res, count = compute_ape_rmse(gt, est, correct_scale=is_monocular)
            if res is not None:
                print(f"  {algo_name:15s}: ✅ APE RMSE = {res['rmse']:6.4f} m ({res['rmse']*100:5.2f} cm) | Mean = {res['mean']:6.4f} m | Max = {res['max']:6.4f} m | Poses = {res['matched_points']}")
            else:
                print(f"  {algo_name:15s}: ⚠️  Timestamp alignment failed ({count} matches)")
    print("\n==========================================================")

