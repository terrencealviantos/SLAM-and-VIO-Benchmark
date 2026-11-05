#!/usr/bin/env python3
"""
5-Algorithm Comparative Timing Visualizer
=========================================
Generates side-by-side comparison bar chart for:
  - OpenVINS (MSCKF Filter)
  - Kimera-VIO (Factor Graph)
  - ORB-SLAM3 Baseline (Stereo-VI)
  - ORB-SLAM3 Hybrid KLT (Stereo-VI)
  - NVIDIA cuVSLAM (GPU Isaac ROS)
"""

import os
import sys

# Import PureCanvas from local scratch package
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
from pure_canvas import PureCanvas

def render_5way_timing(out_png: str):
    W = 1800
    H = 950
    
    margin_left = 180
    margin_right = 80
    margin_top = 130
    margin_bottom = 120
    
    plot_w = W - margin_left - margin_right
    plot_h = H - margin_top - margin_bottom
    
    canvas = PureCanvas(W, H, "#1a1a2e")
    
    # Title
    canvas.draw_text(W // 2, 40, "5-Algorithm Comparative Latency and Throughput Breakdown", 26, "#ffffff", bold=True, align="center")
    canvas.draw_text(W // 2, 80, "Benchmarked on EuRoC MAV Machine Hall (MH_01_easy) & TUM Benchmark", 16, "#64B5F6", bold=True, align="center")
    
    # Background panel
    canvas.draw_rounded_rect(margin_left, margin_top, plot_w, plot_h, 8, "#16213e", "#2a3b5c", 2)
    
    algorithms = [
        "OpenVINS\n(MSCKF Filter)",
        "Kimera-VIO\n(Factor Graph)",
        "ORB-SLAM3\n(Original)",
        "ORB-SLAM3\n(Hybrid KLT)",
        "NVIDIA cuVSLAM\n(GPU Isaac ROS)"
    ]
    
    # Values in ms: Total Frame Mean, Tracking Stage Mean, Peak Max Latency
    data = [
        {"name": "OpenVINS", "total": 20.62, "track": 8.72, "max": 134.97, "fps": "~48 FPS"},
        {"name": "Kimera-VIO", "total": 8.99, "track": 6.35, "max": 59.00, "fps": "~111 FPS"},
        {"name": "ORB-SLAM3 Baseline", "total": 55.86, "track": 54.66, "max": 283.30, "fps": "~18 FPS"},
        {"name": "ORB-SLAM3 Hybrid KLT", "total": 25.15, "track": 19.00, "max": 82.50, "fps": "~45 FPS"},
        {"name": "NVIDIA cuVSLAM", "total": 5.80, "track": 1.81, "max": 12.40, "fps": ">170 FPS"}
    ]
    
    max_y = 300.0  # Max ms on Y axis
    
    # Grid lines
    for y_val in [0, 50, 100, 150, 200, 250, 300]:
        gy = int(margin_top + plot_h - (y_val / max_y) * plot_h)
        canvas.draw_line(margin_left, gy, margin_left + plot_w, gy, "#ffffff1a", 1, dashed=True, dash_len=5)
        canvas.draw_text(margin_left - 15, gy - 7, f"{y_val} ms", 13, "#a0a0b0", bold=True, align="right")
    
    # Group widths
    n_groups = len(data)
    group_w = plot_w / n_groups
    bar_w = 42
    bar_gap = 12
    
    # Colors
    c_total = "#4C72B0"
    c_track = "#55A868"
    c_max = "#C44E52"
    
    for i, d in enumerate(data):
        gx_center = margin_left + int((i + 0.5) * group_w)
        
        # Bars positions
        bx_total = gx_center - bar_w - bar_gap
        bx_track = gx_center - bar_w // 2
        bx_max = gx_center + bar_gap
        
        # Total bar
        h_total = max(3, int((d["total"] / max_y) * plot_h))
        by_total = margin_top + plot_h - h_total
        canvas.draw_rounded_rect(bx_total, by_total, bar_w, h_total, 4, c_total, "#ffffff", 1)
        canvas.draw_text(bx_total + bar_w // 2, by_total - 18, f"{d['total']:.1f}", 11, "#ffffff", bold=True, align="center")
        
        # Track bar
        h_track = max(3, int((d["track"] / max_y) * plot_h))
        by_track = margin_top + plot_h - h_track
        canvas.draw_rounded_rect(bx_track, by_track, bar_w, h_track, 4, c_track, "#ffffff", 1)
        canvas.draw_text(bx_track + bar_w // 2, by_track - 18, f"{d['track']:.1f}", 11, "#ffffff", bold=True, align="center")
        
        # Max bar
        h_max = max(3, int((d["max"] / max_y) * plot_h))
        by_max = margin_top + plot_h - h_max
        canvas.draw_rounded_rect(bx_max, by_max, bar_w, h_max, 4, c_max, "#ffffff", 1)
        canvas.draw_text(bx_max + bar_w // 2, by_max - 18, f"{d['max']:.1f}", 11, "#ffffff", bold=True, align="center")
        
        # X-Axis labels
        label_lines = algorithms[i].split("\n")
        canvas.draw_text(gx_center, margin_top + plot_h + 20, label_lines[0], 14, "#ffffff", bold=True, align="center")
        canvas.draw_text(gx_center, margin_top + plot_h + 40, label_lines[1], 12, "#64B5F6", bold=True, align="center")
        canvas.draw_text(gx_center, margin_top + plot_h + 60, f"[{d['fps']}]", 11, "#55A868", bold=True, align="center")
        
    # Legend
    lx = margin_left + plot_w - 420
    ly = margin_top + 25
    canvas.draw_rounded_rect(lx, ly, 400, 110, 6, "#0f3460", "#3a506b", 1)
    
    # Legend items
    canvas.draw_rounded_rect(lx + 15, ly + 15, 20, 14, 2, c_total, "#ffffff", 1)
    canvas.draw_text(lx + 45, ly + 14, "Total Frame Mean Latency (ms)", 12, "#ffffff", bold=True)
    
    canvas.draw_rounded_rect(lx + 15, ly + 45, 20, 14, 2, c_track, "#ffffff", 1)
    canvas.draw_text(lx + 45, ly + 44, "Feature Tracking Stage Latency (ms)", 12, "#ffffff", bold=True)
    
    canvas.draw_rounded_rect(lx + 15, ly + 75, 20, 14, 2, c_max, "#ffffff", 1)
    canvas.draw_text(lx + 45, ly + 74, "Max Peak Tail Latency (ms)", 12, "#ffffff", bold=True)
    
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    canvas.save_png(out_png)
    print(f"[✔] Successfully generated 5-Way timing chart → {out_png}")

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_png1 = os.path.join(project_root, "figures", "comparative_5way_timing.png")
    out_png2 = os.path.join(project_root, "results", "euroc", "comparative_5way_timing.png")
    
    render_5way_timing(out_png1)
    import shutil
    shutil.copyfile(out_png1, out_png2)

if __name__ == "__main__":
    main()
