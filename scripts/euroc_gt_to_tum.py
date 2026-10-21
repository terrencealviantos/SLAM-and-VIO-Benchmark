#!/usr/bin/env python3
"""Convert EuRoC ground truth CSV to TUM format.

Usage:
    python3 euroc_gt_to_tum.py /path/to/mav0/state_groundtruth_estimate0/data.csv /path/to/output.txt
    
Reads: timestamp[ns], p_RS_R_x, p_RS_R_y, p_RS_R_z, q_RS_w, q_RS_x, q_RS_y, q_RS_z, ...
Writes: timestamp tx ty tz qx qy qz qw
"""

import csv
import sys
import os

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <euroc_gt.csv> <output_tum.txt>")
        sys.exit(1)
    
    gt_csv = sys.argv[1]
    output_tum = sys.argv[2]
    
    if not os.path.exists(gt_csv):
        print(f"[ERROR] {gt_csv} not found")
        sys.exit(1)
    
    os.makedirs(os.path.dirname(os.path.abspath(output_tum)), exist_ok=True)
    
    count = 0
    with open(gt_csv, 'r') as fin, open(output_tum, 'w') as fout:
        reader = csv.reader(fin)
        for row in reader:
            if not row or row[0].startswith('#') or row[0].startswith('timestamp'):
                continue
            if len(row) < 8:
                continue
            ts_ns = int(row[0])
            ts_s = ts_ns / 1e9
            px, py, pz = float(row[1]), float(row[2]), float(row[3])
            qw, qx, qy, qz = float(row[4]), float(row[5]), float(row[6]), float(row[7])
            # TUM format: timestamp tx ty tz qx qy qz qw
            fout.write(f"{ts_s:.9f} {px:.6f} {py:.6f} {pz:.6f} {qx:.6f} {qy:.6f} {qz:.6f} {qw:.6f}\n")
            count += 1
    
    print(f"[✔] Wrote {count} ground truth poses to {output_tum}")

if __name__ == '__main__':
    main()
