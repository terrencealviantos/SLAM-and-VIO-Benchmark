#!/usr/bin/env python3
import sys
import os

def convert_kimera_to_tum(input_csv, output_tum):
    if not os.path.exists(input_csv):
        print(f"[WARN] Input file does not exist: {input_csv}")
        return False

    os.makedirs(os.path.dirname(os.path.abspath(output_tum)), exist_ok=True)
    count = 0
    with open(input_csv, 'r') as f_in, open(output_tum, 'w') as f_out:
        for line in f_in:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 8:
                continue
            try:
                # timestamp in nanoseconds or seconds
                t_raw = float(parts[0])
                t_sec = t_raw * 1e-9 if t_raw > 1e12 else t_raw
                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3])
                qw = float(parts[4])
                qx = float(parts[5])
                qy = float(parts[6])
                qz = float(parts[7])
                # TUM format: timestamp x y z qx qy qz qw
                f_out.write(f"{t_sec:.9f} {x:.6f} {y:.6f} {z:.6f} {qx:.6f} {qy:.6f} {qz:.6f} {qw:.6f}\n")
                count += 1
            except ValueError:
                continue

    print(f"[SUCCESS] Converted {count} poses from {input_csv} to TUM format at {output_tum}")
    return count > 0

if __name__ == '__main__':
    in_file = sys.argv[1] if len(sys.argv) > 1 else "/results/suedhoehe/kimera/traj_vio.csv"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "/results/suedhoehe/kimera/kimera_tum.txt"
    convert_kimera_to_tum(in_file, out_file)
