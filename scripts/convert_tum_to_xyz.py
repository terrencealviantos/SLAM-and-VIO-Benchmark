#!/usr/bin/env python3
"""
Convert TUM format trajectory files (timestamp tx ty tz qx qy qz qw)
to 3D XYZ coordinate files.

Outputs:
  1. Standard .xyz file: 'x y z' per line (compatible with MeshLab, CloudCompare, etc.)
  2. Timestamped .txt file: 'timestamp x y z'
  3. CSV file: 'timestamp,x,y,z'
"""

import sys
import os
import argparse

def convert_tum_to_xyz(input_tum, output_prefix=None):
    if not os.path.exists(input_tum):
        print(f"[ERROR] Input TUM file does not exist: {input_tum}")
        return False

    if output_prefix is None:
        base, _ = os.path.splitext(input_tum)
        if base.endswith("_tum"):
            output_prefix = f"{base[:-4]}_3d"
        else:
            output_prefix = f"{base}_3d"

    xyz_file = f"{output_prefix}.xyz"
    txt_file = f"{output_prefix}_xyz.txt"
    csv_file = f"{output_prefix}_coordinates.csv"

    os.makedirs(os.path.dirname(os.path.abspath(xyz_file)), exist_ok=True)

    poses = []
    with open(input_tum, 'r') as fin:
        for line_num, line in enumerate(fin, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = [p.strip() for p in line.split() if p.strip()]
            if len(parts) < 4:
                continue
            try:
                t = float(parts[0])
                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3])
                poses.append((t, x, y, z))
            except ValueError as e:
                print(f"[WARN] Skipping line {line_num}: invalid float value ({e})")
                continue

    if not poses:
        print("[ERROR] No valid poses extracted.")
        return False

    # 1. Write standard .xyz format (x y z)
    with open(xyz_file, 'w') as f_xyz:
        for _, x, y, z in poses:
            f_xyz.write(f"{x:.6f} {y:.6f} {z:.6f}\n")

    # 2. Write timestamped txt format (timestamp x y z)
    with open(txt_file, 'w') as f_txt:
        for t, x, y, z in poses:
            f_txt.write(f"{t:.6f} {x:.6f} {y:.6f} {z:.6f}\n")

    # 3. Write CSV format (timestamp,x,y,z)
    with open(csv_file, 'w') as f_csv:
        f_csv.write("timestamp,x,y,z\n")
        for t, x, y, z in poses:
            f_csv.write(f"{t:.6f},{x:.6f},{y:.6f},{z:.6f}\n")

    xs = [p[1] for p in poses]
    ys = [p[2] for p in poses]
    zs = [p[3] for p in poses]
    ts = [p[0] for p in poses]

    print(f"[SUCCESS] Converted {len(poses)} poses from {input_tum}:")
    print(f"  -> Pure XYZ (.xyz):     {xyz_file}")
    print(f"  -> Timestamped (.txt):  {txt_file}")
    print(f"  -> CSV format (.csv):   {csv_file}")
    print(f"  Pose count:   {len(poses)}")
    print(f"  Time span:    {ts[0]:.3f}s to {ts[-1]:.3f}s (duration: {ts[-1] - ts[0]:.2f}s)")
    print(f"  X bounds:     [{min(xs):.4f}, {max(xs):.4f}] (span: {max(xs) - min(xs):.4f} m)")
    print(f"  Y bounds:     [{min(ys):.4f}, {max(ys):.4f}] (span: {max(ys) - min(ys):.4f} m)")
    print(f"  Z bounds:     [{min(zs):.4f}, {max(zs):.4f}] (span: {max(zs) - min(zs):.4f} m)")

    return True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Convert TUM trajectory to 3D XYZ coordinates")
    parser.add_argument("input", help="Path to input TUM file")
    parser.add_argument("--prefix", "-o", default=None, help="Output path prefix (optional)")
    args = parser.parse_args()

    convert_tum_to_xyz(args.input, args.prefix)
