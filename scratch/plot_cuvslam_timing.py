#!/usr/bin/env python3
"""
NVIDIA cuVSLAM Pipeline Timing Visualizer & Gantt Chart Generator
================================================================
Visualizes the multi-thread GPU-accelerated pipeline of NVIDIA cuVSLAM (Isaac ROS Visual SLAM)
following the exact Fig. 2 System Architecture standards used for OpenVINS, Kimera-VIO, and ORB-SLAM3.

Threads & Modules:
  1. GPU Tracking Frontend Thread:
     - GPU Stereo Rectification & Preprocessing
     - GPU Feature Tracking (Pyramidal KLT)
     - IMU Pre-Integration & EKF Propagation
     - GPU Pose Optimization (Gauss-Newton + Robust Loss)
  2. GPU Local Mapping Backend Thread:
     - Keyframe Insertion
     - GPU Local Bundle Adjustment (Local BA)
     - Map Point Maintenance & Culling
  3. GPU Loop Closing Backend Thread:
     - GPU Loop Detection & Verification (DBoW)
     - Pose Graph Optimization (PGO)
"""

import os
import csv
import sys

# Import PureCanvas from local scratch package
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
from pure_canvas import PureCanvas, parse_hex_color

FRAME_COLOURS = [
    "#4C72B0", "#55A868", "#C44E52", "#8172B2", "#CCB974",
    "#64B5F6", "#E377C2", "#8C564B", "#9467BD", "#7F7F7F"
]

def load_timing_csv(path: str):
    rows = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "frame_id": int(r["frame_id"]),
                "module": r["module"].strip(),
                "thread_id": int(r["thread_id"]),
                "thread_label": r["thread_label"].strip(),
                "start_ns": int(r["start_ns"]),
                "end_ns": int(r["end_ns"]),
                "duration_ms": float(r["duration_ms"]),
                "is_keyframe": r.get("is_keyframe", "False").lower() == "true"
            })
    return rows

def generate_svg_and_png(rows, out_png: str, out_svg: str, dataset_name="suedhoehe", start_frame=50, num_frames=6):
    # Filter frames for zoomed Gantt view
    unique_fids = sorted(list(set(r["frame_id"] for r in rows)))
    target_fids = [f for f in unique_fids if f >= start_frame][:num_frames]
    if not target_fids:
        target_fids = unique_fids[:num_frames]
        
    filtered = [r for r in rows if r["frame_id"] in target_fids]
    if not filtered:
        print("[!] No records in window!")
        return

    # Normalize timeline to earliest start
    t0_ns = min(r["start_ns"] for r in filtered)
    for r in filtered:
        r["start_ms"] = (r["start_ns"] - t0_ns) * 1e-6
        r["end_ms"] = (r["end_ns"] - t0_ns) * 1e-6

    max_time_ms = max(r["end_ms"] for r in filtered) * 1.08

    # Fig 2 System Architecture ordering (from top to bottom)
    module_order = [
        ("GPU Stereo Rectification", "GPU Tracking Frontend"),
        ("GPU Feature Tracking (KLT)", "GPU Tracking Frontend"),
        ("IMU Pre-Integration", "GPU Tracking Frontend"),
        ("GPU Pose Optimization", "GPU Tracking Frontend"),
        ("Keyframe Insertion", "GPU Local Mapping Thread"),
        ("GPU Local Bundle Adjustment", "GPU Local Mapping Thread"),
        ("Map Point Maintenance", "GPU Local Mapping Thread"),
        ("GPU Loop Detection & Verification", "GPU Loop Closing Thread"),
        ("Pose Graph Optimization (PGO)", "GPU Loop Closing Thread")
    ]

    modules_present = [m for m, t in module_order if any(r["module"] == m for r in filtered)]
    
    # Canvas dimensions
    W = 2250
    H = 1360
    
    # Margins & Plot area
    margin_left = 480
    margin_right = 90
    margin_top = 170
    margin_bottom = 120
    
    plot_x = margin_left
    plot_y = margin_top
    plot_w = W - margin_left - margin_right
    plot_h = H - margin_top - margin_bottom

    lane_h = plot_h / len(modules_present)
    bar_h = min(lane_h * 0.72, 60)

    # Frame color mapping
    frame_color_map = {fid: FRAME_COLOURS[idx % len(FRAME_COLOURS)] for idx, fid in enumerate(target_fids)}

    # 1. RENDER SVG
    svg_lines = []
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg_lines.append(f'<defs><style>')
    svg_lines.append(f'  text {{ font-family: "DejaVu Sans", "Helvetica", Arial, sans-serif; }}')
    svg_lines.append(f'</style></defs>')
    # Backgrounds
    svg_lines.append(f'<rect width="{W}" height="{H}" fill="#1a1a2e"/>')
    svg_lines.append(f'<rect x="{plot_x}" y="{plot_y}" width="{plot_w}" height="{plot_h}" rx="6" fill="#16213e" stroke="#2a3b5c" stroke-width="1.5"/>')

    # Grid lines
    time_step = 10 if max_time_ms < 100 else 20
    t_val = 0.0
    while t_val <= max_time_ms:
        gx = plot_x + (t_val / max_time_ms) * plot_w
        svg_lines.append(f'<line x1="{gx}" y1="{plot_y}" x2="{gx}" y2="{plot_y + plot_h}" stroke="#ffffff22" stroke-dasharray="6,6" stroke-width="1.2"/>')
        svg_lines.append(f'<text x="{gx}" y="{plot_y + plot_h + 30}" fill="#a0a0b0" font-size="18" text-anchor="middle" font-weight="bold">{int(t_val)} ms</text>')
        t_val += time_step

    # Title & Subtitle
    svg_lines.append(f'<text x="{W//2}" y="65" fill="#ffffff" font-size="32" font-weight="bold" text-anchor="middle">NVIDIA cuVSLAM Fig. 2 Architecture Timeline — {dataset_name.capitalize()} Dataset</text>')
    svg_lines.append(f'<text x="{W//2}" y="105" fill="#64B5F6" font-size="20" font-weight="bold" text-anchor="middle">Hardware: NVIDIA GeForce RTX 3050 Mobile (CUDA Accelerated, Compute Capability 8.6)</text>')

    # Render lanes, labels and bars
    for idx, mod_name in enumerate(modules_present):
        y_top = plot_y + idx * lane_h
        y_mid = y_top + lane_h / 2
        y_bar = y_mid - bar_h / 2
        
        # Lane divider
        if idx > 0:
            svg_lines.append(f'<line x1="{plot_x}" y1="{y_top}" x2="{plot_x + plot_w}" y2="{y_top}" stroke="#ffffff15" stroke-width="1"/>')

        # Y-axis labels with thread tags
        thread_tag = next((t for m, t in module_order if m == mod_name), "")
        svg_lines.append(f'<text x="{plot_x - 20}" y="{y_mid - 4}" fill="#ffffff" font-size="18" font-weight="bold" text-anchor="end">{mod_name}</text>')
        svg_lines.append(f'<text x="{plot_x - 20}" y="{y_mid + 20}" fill="#8172B2" font-size="15" font-weight="bold" text-anchor="end">[{thread_tag}]</text>')

        # Bars
        mod_records = [r for r in filtered if r["module"] == mod_name]
        for r in mod_records:
            bx = plot_x + (r["start_ms"] / max_time_ms) * plot_w
            bw = max(4.0, ((r["end_ms"] - r["start_ms"]) / max_time_ms) * plot_w)
            color = frame_color_map[r["frame_id"]]
            
            svg_lines.append(f'<rect x="{bx}" y="{y_bar}" width="{bw}" height="{bar_h}" rx="6" fill="{color}" stroke="#ffffff" stroke-width="1.2" opacity="0.95"/>')
            
            # Text label inside bar
            if bw > 75:
                svg_lines.append(f'<text x="{bx + bw/2}" y="{y_mid + 6}" fill="#ffffff" font-size="15" font-weight="bold" text-anchor="middle">F{r["frame_id"]} ({r["duration_ms"]:.1f}ms)</text>')
            elif bw > 35:
                svg_lines.append(f'<text x="{bx + bw/2}" y="{y_mid + 6}" fill="#ffffff" font-size="14" font-weight="bold" text-anchor="middle">F{r["frame_id"]}</text>')

    # Legend for frames
    legend_x = plot_x + plot_w - 600
    legend_y = 125
    svg_lines.append(f'<rect x="{legend_x}" y="{legend_y}" width="590" height="38" rx="6" fill="#0f3460" stroke="#394b6e" stroke-width="1.5" opacity="0.9"/>')
    for f_i, fid in enumerate(target_fids):
        lx = legend_x + 15 + f_i * 95
        fc = frame_color_map[fid]
        svg_lines.append(f'<rect x="{lx}" y="{legend_y + 11}" width="24" height="16" rx="3" fill="{fc}"/>')
        svg_lines.append(f'<text x="{lx + 32}" y="{legend_y + 24}" fill="#ffffff" font-size="14" font-weight="bold">F{fid}</text>')

    # X-axis label
    svg_lines.append(f'<text x="{plot_x + plot_w//2}" y="{H - 35}" fill="#ffffff" font-size="20" font-weight="bold" text-anchor="middle">Timeline (ms) from first frame start</text>')
    svg_lines.append('</svg>')

    os.makedirs(os.path.dirname(out_svg), exist_ok=True)
    with open(out_svg, "w") as f:
        f.write("\n".join(svg_lines))
    print(f"[✔] Saved SVG chart → {out_svg}")

    # 2. RENDER HIGH RES PURE PNG
    canvas = PureCanvas(W, H, "#1a1a2e")
    # Plot background
    canvas.draw_rounded_rect(plot_x, plot_y, plot_w, plot_h, 8, "#16213e", "#2a3b5c", 2)

    # Grid lines
    t_val = 0.0
    while t_val <= max_time_ms:
        gx = int(plot_x + (t_val / max_time_ms) * plot_w)
        canvas.draw_line(gx, plot_y, gx, plot_y + plot_h, "#ffffff22", 1, dashed=True, dash_len=8)
        canvas.draw_text(gx, plot_y + plot_h + 15, f"{int(t_val)} ms", 16, "#a0a0b0", bold=True, align="center")
        t_val += time_step

    # Title & Subtitle
    canvas.draw_text(W // 2, 45, f"NVIDIA cuVSLAM Fig. 2 Architecture Timeline -- {dataset_name.capitalize()} Dataset", 28, "#ffffff", bold=True, align="center")
    canvas.draw_text(W // 2, 85, "Hardware: NVIDIA GeForce RTX 3050 Mobile (CUDA Accelerated, Compute Capability 8.6)", 18, "#64B5F6", bold=True, align="center")

    # Lanes and bars
    for idx, mod_name in enumerate(modules_present):
        y_top = plot_y + int(idx * lane_h)
        y_mid = int(y_top + lane_h / 2)
        y_bar = int(y_mid - bar_h / 2)

        if idx > 0:
            canvas.draw_line(plot_x, y_top, plot_x + plot_w, y_top, "#ffffff15", 1)

        thread_tag = next((t for m, t in module_order if m == mod_name), "")
        canvas.draw_text(plot_x - 20, y_mid - 18, mod_name, 16, "#ffffff", bold=True, align="right")
        canvas.draw_text(plot_x - 20, y_mid + 4, f"[{thread_tag}]", 14, "#8172B2", bold=True, align="right")

        mod_records = [r for r in filtered if r["module"] == mod_name]
        for r in mod_records:
            bx = int(plot_x + (r["start_ms"] / max_time_ms) * plot_w)
            bw = max(5, int(((r["end_ms"] - r["start_ms"]) / max_time_ms) * plot_w))
            color = frame_color_map[r["frame_id"]]

            canvas.draw_rounded_rect(bx, y_bar, bw, int(bar_h), 6, color, "#ffffff", 1)

            if bw > 75:
                canvas.draw_text(bx + bw // 2, y_mid - 8, f"F{r['frame_id']} ({r['duration_ms']:.1f}ms)", 14, "#ffffff", bold=True, align="center")
            elif bw > 30:
                canvas.draw_text(bx + bw // 2, y_mid - 8, f"F{r['frame_id']}", 14, "#ffffff", bold=True, align="center")

    # Legend
    canvas.draw_rounded_rect(legend_x, legend_y, 590, 36, 6, "#0f3460", "#394b6e", 1)
    for f_i, fid in enumerate(target_fids):
        lx = legend_x + 15 + f_i * 95
        fc = frame_color_map[fid]
        canvas.fill_rect(lx, legend_y + 10, 22, 16, fc)
        canvas.draw_text(lx + 30, legend_y + 10, f"F{fid}", 14, "#ffffff", bold=True)

    # X-axis label
    canvas.draw_text(plot_x + plot_w // 2, H - 55, "Timeline (ms) from first frame start", 18, "#ffffff", bold=True, align="center")

    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    canvas.save_png(out_png)

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(project_root, "results", "suedhoehe", "cuvslam", "cuvslam_timing.csv")
    
    out_gantt_dir = os.path.join(project_root, "gantt_charts")
    out_png1 = os.path.join(out_gantt_dir, "4_cuvslam_gantt_chart.png")
    out_png2 = os.path.join(project_root, "4_cuvslam_gantt_chart.png")
    out_svg = os.path.join(out_gantt_dir, "4_cuvslam_gantt_chart.svg")

    rows = load_timing_csv(csv_path)
    generate_svg_and_png(rows, out_png1, out_svg, dataset_name="suedhoehe", start_frame=50, num_frames=6)
    
    # Also save to root
    import shutil
    shutil.copyfile(out_png1, out_png2)
    print(f"[✔] Copied 4_cuvslam_gantt_chart.png to repository root")

if __name__ == "__main__":
    main()
