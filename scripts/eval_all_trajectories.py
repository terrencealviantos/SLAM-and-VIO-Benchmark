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

def compute_ape_rmse(gt, est):
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
        
    t_opt = mu_gt - R @ mu_est
    est_aligned = (R @ est_m.T).T + t_opt
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

if __name__ == '__main__':
    print("==========================================================")
    print("      VISUAL SLAM & VIO BENCHMARK EVALUATION (SE3 APE)")
    print("==========================================================")
    
    benchmarks = [
        ("EuRoC MH_01_easy", "/home/boris/SLAM-and-VIO-Benchmark/datasets/MH_01_easy/gt_tum.txt", [
            ("cuVSLAM", "/home/boris/SLAM-and-VIO-Benchmark/results/euroc/MH_01_easy/cuvslam_tum.txt"),
            ("OpenVINS", "/home/boris/SLAM-and-VIO-Benchmark/results/euroc/open_vins.txt"),
            ("Kimera-VIO", "/home/boris/SLAM-and-VIO-Benchmark/results/euroc/kimera.txt"),
            ("ORB-SLAM3", "/home/boris/SLAM-and-VIO-Benchmark/results/euroc/orb_slam3.txt"),
        ]),
        ("EuRoC V1_03_difficult", "/home/boris/SLAM-and-VIO-Benchmark/datasets/V1_03_difficult/gt_tum.txt", [
            ("cuVSLAM", "/home/boris/SLAM-and-VIO-Benchmark/results/euroc/V1_03_difficult/cuvslam/cuvslam_tum.txt"),
        ]),
        ("Suedhoehe (Snow Outdoor)", "/home/boris/SLAM-and-VIO-Benchmark/datasets/suedhoehe_gps_schnee_02/gps_trajectory.txt", [
            ("cuVSLAM", "/home/boris/SLAM-and-VIO-Benchmark/results/suedhoehe/cuvslam/cuvslam_tum.txt"),
            ("OpenVINS", "/home/boris/SLAM-and-VIO-Benchmark/results/suedhoehe/openvins/openvins_tum.txt"),
            ("Kimera-VIO", "/home/boris/SLAM-and-VIO-Benchmark/results/suedhoehe/kimera/kimera_tum.txt"),
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
                print(f"  {algo_name:12s}: ❌ Not available / No trajectory file")
                continue
            res, count = compute_ape_rmse(gt, est)
            if res is not None:
                print(f"  {algo_name:12s}: ✅ APE RMSE = {res['rmse']:6.4f} m ({res['rmse']*100:5.2f} cm) | Mean = {res['mean']:6.4f} m | Max = {res['max']:6.4f} m | Poses = {res['matched_points']}")
            else:
                print(f"  {algo_name:12s}: ⚠️  Timestamp alignment failed ({count} matches)")
    print("\n==========================================================")
