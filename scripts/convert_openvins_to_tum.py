#!/usr/bin/env python3
import sys
import os

def convert_openvins_to_tum(input_txt, output_tum):
    if not os.path.exists(input_txt):
        print(f"[WARN] Input file does not exist: {input_txt}")
        return False

    os.makedirs(os.path.dirname(os.path.abspath(output_tum)), exist_ok=True)
    count = 0
    with open(input_txt, 'r') as f_in, open(output_tum, 'w') as f_out:
        for line in f_in:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = [p.strip() for p in line.split(' ')]
            parts = [p for p in parts if p]
            if len(parts) < 8:
                continue
            try:
                t = float(parts[0])
                qw = float(parts[1])
                qx = float(parts[2])
                qy = float(parts[3])
                qz = float(parts[4])
                x = float(parts[5])
                y = float(parts[6])
                z = float(parts[7])
                # TUM format: timestamp x y z qx qy qz qw
                f_out.write(f"{t:.6f} {x:.6f} {y:.6f} {z:.6f} {qx:.6f} {qy:.6f} {qz:.6f} {qw:.6f}\n")
                count += 1
            except ValueError:
                continue

    print(f"[SUCCESS] Converted {count} poses from {input_txt} to TUM format at {output_tum}")
    return count > 0

if __name__ == '__main__':
    in_file = sys.argv[1] if len(sys.argv) > 1 else "/results/ov_estimate.txt"
    out_file = sys.argv[2] if len(sys.argv) > 2 else "/results/openvins_tum.txt"
    convert_openvins_to_tum(in_file, out_file)
