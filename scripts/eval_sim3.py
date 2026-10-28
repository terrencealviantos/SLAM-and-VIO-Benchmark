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

def align_sim3(gt, est):
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
        
    A = np.array(est_matched)
    B = np.array(gt_matched)
    
    # Umeyama Sim(3)
    mu_A = np.mean(A, axis=0)
    mu_B = np.mean(B, axis=0)
    
    AA = A - mu_A
    BB = B - mu_B
    
    H = AA.T @ BB / len(A)
    U, D, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R) < 0:
        Vt[2, :] *= -1
        R = Vt.T @ U.T
        
    var_A = np.var(A, axis=0).sum()
    scale = np.trace(np.diag(D)) / var_A if var_A > 0 else 1.0
    
    t_opt = mu_B - scale * (R @ mu_A)
    A_aligned = scale * (R @ A.T).T + t_opt
    
    errors = np.linalg.norm(B - A_aligned, axis=1)
    return {
        'rmse': np.sqrt(np.mean(errors**2)),
        'mean': np.mean(errors),
        'max': np.max(errors),
        'scale': scale,
        'matched': len(errors)
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
    print("=======================================================")
    print("      VISUAL SLAM & VIO SIM(3) EVALUATION")
    print(f"      Repository Root: {root}")
    print("=======================================================")

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
        ])
    ]
    for dname, gt_path, algos in benchmarks:
        print(f"\n=======================================================")
        print(f" Dataset: {dname}")
        print(f"=======================================================")
        gt = load_tum(gt_path)
        if gt is None:
            print(f"  [ERROR] Ground truth not found at: {gt_path}")
            continue
        for aname, epath in algos:
            est = load_tum(epath)
            if est is None:
                print(f"  {aname:15s} | ❌ Not available")
                continue
            res, _ = align_sim3(gt, est)
            if res:
                print(f"  {aname:15s} | APE RMSE: {res['rmse']:.4f} m ({res['rmse']*100:.2f} cm) | Mean: {res['mean']:.4f} m | Scale: {res['scale']:.4f} | Poses: {res['matched']}")

