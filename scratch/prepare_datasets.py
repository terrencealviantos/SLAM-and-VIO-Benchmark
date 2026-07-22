import os
import glob

euroc_base = "/home/terrence/researchProject/datasets/Euroc"

sequences = [
    os.path.join(euroc_base, "machine_hall", "MH_01_easy"),
    os.path.join(euroc_base, "machine_hall", "MH_02_easy"),
    os.path.join(euroc_base, "machine_hall", "MH_03_medium"),
    os.path.join(euroc_base, "machine_hall", "MH_04_difficult"),
    os.path.join(euroc_base, "machine_hall", "MH_05_difficult"),
    os.path.join(euroc_base, "vicon_room1", "V1_01_easy"),
    os.path.join(euroc_base, "vicon_room1", "V1_02_medium"),
    os.path.join(euroc_base, "vicon_room1", "V1_03_difficult"),
]

for seq in sequences:
    mav0 = os.path.join(seq, "mav0")
    if not os.path.exists(mav0):
        print(f"Skipping {seq}, no mav0 folder")
        continue

    # Extract timestamps.txt from cam0/data.csv
    cam0_csv = os.path.join(mav0, "cam0", "data.csv")
    ts_file = os.path.join(seq, "timestamps.txt")
    if os.path.exists(cam0_csv) and not os.path.exists(ts_file):
        with open(cam0_csv, 'r') as f_in, open(ts_file, 'w') as f_out:
            lines = f_in.readlines()
            for line in lines:
                if line.startswith("#"):
                    continue
                parts = line.strip().split(",")
                if len(parts) >= 1 and parts[0]:
                    f_out.write(parts[0] + "\n")
        print(f"Created timestamps.txt for {seq}")

    # Extract groundtruth gt_tum.txt from state_groundtruth_estimate0/data.csv
    gt_csv = os.path.join(mav0, "state_groundtruth_estimate0", "data.csv")
    gt_tum = os.path.join(seq, "gt_tum.txt")
    if os.path.exists(gt_csv):
        with open(gt_csv, 'r') as f_in, open(gt_tum, 'w') as f_out:
            lines = f_in.readlines()
            for line in lines:
                if line.startswith("#"):
                    continue
                parts = line.strip().split(",")
                if len(parts) >= 8:
                    ts_ns = int(parts[0])
                    t_sec = ts_ns * 1e-9
                    p_x, p_y, p_z = parts[1], parts[2], parts[3]
                    q_w, q_x, q_y, q_z = parts[4], parts[5], parts[6], parts[7]
                    f_out.write(f"{t_sec:.9f} {p_x} {p_y} {p_z} {q_x} {q_y} {q_z} {q_w}\n")
        print(f"Created gt_tum.txt for {seq}")

print("Dataset preparation complete.")
