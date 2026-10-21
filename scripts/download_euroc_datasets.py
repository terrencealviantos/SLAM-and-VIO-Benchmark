#!/usr/bin/env python3
import os
import sys
import zipfile
import urllib.request
import time

DATASETS_DIR = "/home/boris/SLAM-and-VIO-Benchmark/datasets"
os.makedirs(DATASETS_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Accept": "*/*"
}

ARCHIVES = [
    {
        "name": "vicon_room1",
        "url": "https://www.research-collection.ethz.ch/server/api/core/bitstreams/02ecda9a-298f-498b-970c-b7c44334d880/content",
        "target_seqs": ["V1_03_difficult"],
        "size_gb": 6.0
    },
    {
        "name": "machine_hall",
        "url": "https://www.research-collection.ethz.ch/server/api/core/bitstreams/7b2419c1-62b5-4714-b7f8-485e5fe3e5fe/content",
        "target_seqs": ["MH_01_easy"],
        "size_gb": 12.6
    }
]

def download_and_extract(archive_info):
    name = archive_info["name"]
    url = archive_info["url"]
    targets = archive_info["target_seqs"]
    
    # Check if all targets already exist
    all_exist = True
    for seq in targets:
        seq_dir = os.path.join(DATASETS_DIR, seq, "mav0")
        if not os.path.exists(seq_dir):
            all_exist = False
            break
            
    if all_exist:
        print(f"[✔] Targets {targets} already exist in {DATASETS_DIR}")
        return

    zip_path = os.path.join(DATASETS_DIR, f"{name}.zip")
    print(f"\n=======================================================")
    print(f" [Downloading] {name}.zip ({archive_info['size_gb']} GB)")
    print(f" Source: {url}")
    print(f"=======================================================")

    if not os.path.exists(zip_path) or os.path.getsize(zip_path) < 1000000:
        req = urllib.request.Request(url, headers=HEADERS)
        start_time = time.time()
        with urllib.request.urlopen(req) as resp, open(zip_path, 'wb') as out_f:
            total_size = int(resp.headers.get('content-length', 0))
            downloaded = 0
            chunk_size = 1024 * 1024 * 4 # 4MB chunks
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                out_f.write(chunk)
                downloaded += len(chunk)
                elapsed = time.time() - start_time
                speed_mb = (downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                pct = (downloaded / total_size) * 100 if total_size > 0 else 0
                print(f"\rDownloading: {downloaded/(1024*1024):.1f} MB / {total_size/(1024*1024):.1f} MB ({pct:.1f}%) @ {speed_mb:.1f} MB/s", end="", flush=True)
        print(f"\nDownload finished in {time.time() - start_time:.1f}s.")

    print(f"Inspecting and extracting {targets} from {zip_path}...")
    with zipfile.ZipFile(zip_path, 'r') as z:
        # Check files in zip
        names = z.namelist()
        for seq in targets:
            print(f"Extracting files for {seq}...")
            seq_members = [m for m in names if seq in m]
            if seq_members:
                z.extractall(DATASETS_DIR, members=seq_members)
                print(f"[✔] Extracted {len(seq_members)} files for {seq}")
            else:
                print(f"[WARN] No matching files found for {seq} in {name}.zip. Listing top items:")
                top_items = set([m.split('/')[0] for m in names[:30]])
                print(top_items)

    # Check extracted directory structure and normalize
    for seq in targets:
        # Sometimes zip extracts to datasets/vicon_room1/V1_03_difficult or datasets/V1_03_difficult/mav0
        # Let's ensure datasets/<seq>/mav0 exists
        possible_paths = [
            os.path.join(DATASETS_DIR, seq),
            os.path.join(DATASETS_DIR, name, seq),
        ]
        for p in possible_paths:
            if os.path.exists(p):
                # If it's in a subdirectory, move it to DATASETS_DIR/<seq>
                dest_dir = os.path.join(DATASETS_DIR, seq)
                if p != dest_dir:
                    os.makedirs(os.path.dirname(dest_dir), exist_ok=True)
                    os.rename(p, dest_dir)
                
                # Check if mav0 is inside or if p IS mav0
                if not os.path.exists(os.path.join(dest_dir, "mav0")) and os.path.exists(os.path.join(dest_dir, "cam0")):
                    # p contains cam0 directly, wrap it in mav0
                    tmp_mav0 = os.path.join(dest_dir, "mav0")
                    os.makedirs(tmp_mav0, exist_ok=True)
                    for item in os.listdir(dest_dir):
                        if item != "mav0":
                            os.rename(os.path.join(dest_dir, item), os.path.join(tmp_mav0, item))
                print(f"[✔] Normalized {seq} structure at {dest_dir}")

    # Remove the large zip archive to save space
    if os.path.exists(zip_path):
        print(f"Cleaning up {zip_path} to conserve disk space...")
        os.remove(zip_path)

if __name__ == '__main__':
    for arc in ARCHIVES:
        download_and_extract(arc)
    print("\n[✔] All requested EuRoC datasets downloaded and prepared!")
