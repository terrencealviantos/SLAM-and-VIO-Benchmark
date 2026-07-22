import os
import zipfile
import glob

euroc_base = "/home/terrence/researchProject/datasets/Euroc"
zip_files = glob.glob(os.path.join(euroc_base, "**", "*.zip"), recursive=True)

for zpath in zip_files:
    target_dir = os.path.dirname(zpath)
    mav0_dir = os.path.join(target_dir, "mav0")
    if not os.path.exists(mav0_dir):
        print(f"Unpacking {zpath} -> {target_dir}")
        with zipfile.ZipFile(zpath, 'r') as zip_ref:
            zip_ref.extractall(target_dir)
        print(f"Finished {zpath}")
    else:
        print(f"Already unpacked: {target_dir}")

print("All zip unpacking done!")
