#!/usr/bin/env python3
"""
Multi-Thread Architectural Gantt Chart Comparison
=================================================
Visualizes and compares the multi-thread execution model of 4 major VIO/SLAM systems:
  1. OpenVINS (1 Primary Thread: Sequential MSCKF Pipeline)
  2. Kimera-VIO (2 Concurrent Threads: Frontend + Backend iSAM2)
  3. ORB-SLAM3 (3 Concurrent Threads: Tracking + Local Mapping + Loop Closing)
  4. NVIDIA cuVSLAM (3 GPU-Accelerated Pipelines: GPU Tracking 5.8ms + Asynchronous Local BA + GPU Loop PGO)
"""

import os
import sys

# Import PureCanvas from local scratch package
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
from pure_canvas import PureCanvas

def render_multithread_comparison(out_png: str, out_svg: str):
    W = 2400
    H = 1900
    
    margin_left = 320
    margin_right = 80
    margin_top = 130
    margin_bottom = 90
    
    W = 2400
    H = 2050
    
    margin_left = 340
    margin_right = 80
    margin_top = 125
    margin_bottom = 85
    
    plot_w = W - margin_left - margin_right
    max_time_ms = 180.0
    
    panels = [
        {
            "title": "1. OpenVINS Thread Architecture -- Single Primary MSCKF Thread (CPU)",
            "subtitle": "Sequential single-threaded execution per frame (Total ~20.6 ms)",
            "height": 220,
            "lanes": [
                {"name": "Main VIO Thread", "tag": "MSCKF Pipeline"}
            ],
            "blocks": [
                # Frame 1
                {"lane": 0, "start": 0.0, "dur": 8.7, "color": "#DD8452", "label": "Feature Tracking (8.7ms)"},
                {"lane": 0, "start": 8.7, "dur": 0.5, "color": "#55A868", "label": ""},
                {"lane": 0, "start": 9.2, "dur": 2.6, "color": "#C44E52", "label": "MSCKF (2.6ms)"},
                {"lane": 0, "start": 11.8, "dur": 5.6, "color": "#8172B2", "label": "SLAM Update (5.6ms)"},
                {"lane": 0, "start": 17.4, "dur": 3.1, "color": "#DA8BC3", "label": "Marg."},
                # Frame 2
                {"lane": 0, "start": 50.0, "dur": 8.5, "color": "#DD8452", "label": "Feature Tracking (8.5ms)"},
                {"lane": 0, "start": 58.5, "dur": 0.5, "color": "#55A868", "label": ""},
                {"lane": 0, "start": 59.0, "dur": 2.5, "color": "#C44E52", "label": "MSCKF (2.5ms)"},
                {"lane": 0, "start": 61.5, "dur": 5.5, "color": "#8172B2", "label": "SLAM Update (5.5ms)"},
                {"lane": 0, "start": 67.0, "dur": 3.0, "color": "#DA8BC3", "label": "Marg."},
            ]
        },
        {
            "title": "2. Kimera-VIO Thread Architecture -- 2 Concurrent Threads (Frontend + Backend, CPU)",
            "subtitle": "Continuous lightweight frontend (8.9 ms) + Asynchronous iSAM2 keyframe optimization (18.5 ms)",
            "height": 290,
            "lanes": [
                {"name": "Frontend Thread", "tag": "CPU Tracking"},
                {"name": "Backend iSAM2 Thread", "tag": "CPU Factor Graph"}
            ],
            "blocks": [
                # Frontend Thread
                {"lane": 0, "start": 0.0, "dur": 6.3, "color": "#DD8452", "label": "Frontend Tracking (6.3ms)"},
                {"lane": 0, "start": 6.3, "dur": 2.6, "color": "#C44E52", "label": "Stereo RANSAC (2.6ms)"},
                {"lane": 0, "start": 20.0, "dur": 8.5, "color": "#DD8452", "label": "KLT Non-KF (8.5ms)"},
                {"lane": 0, "start": 40.0, "dur": 8.5, "color": "#DD8452", "label": "KLT Non-KF (8.5ms)"},
                {"lane": 0, "start": 60.0, "dur": 8.9, "color": "#DD8452", "label": "KF Frontend (8.9ms)"},
                # Backend Thread
                {"lane": 1, "start": 9.2, "dur": 18.5, "color": "#8172B2", "label": "iSAM2 Factor Graph Optimization (18.5ms)"},
                {"lane": 1, "start": 69.5, "dur": 19.0, "color": "#8172B2", "label": "iSAM2 Factor Graph Optimization (19.0ms)"}
            ]
        },
        {
            "title": "3. ORB-SLAM3 Original Baseline -- 3 Concurrent Threads (High CPU Contention)",
            "subtitle": "Heavy ORB extraction every frame (54.6 ms) + Local BA mutex lock contention (65.0 ms)",
            "height": 360,
            "lanes": [
                {"name": "Tracking Thread", "tag": "Stereo ORB Track"},
                {"name": "Local Mapping Thread", "tag": "Local BA Optimizer"},
                {"name": "Loop Closing Thread", "tag": "Atlas & Sim3 Engine"}
            ],
            "blocks": [
                # Tracking Thread (Heavy per frame)
                {"lane": 0, "start": 0.0, "dur": 54.6, "color": "#DD8452", "label": "Stereo ORB Extraction & Tracking (54.6ms)"},
                {"lane": 0, "start": 60.0, "dur": 53.2, "color": "#DD8452", "label": "Stereo ORB Extraction & Tracking (53.2ms)"},
                {"lane": 0, "start": 120.0, "dur": 55.1, "color": "#DD8452", "label": "Stereo ORB Extraction & Tracking (55.1ms)"},
                # Local Mapping Thread
                {"lane": 1, "start": 55.0, "dur": 65.0, "color": "#55A868", "label": "Local BA & Map Point Fusion (65.0ms)"},
                # Loop Closing Thread
                {"lane": 2, "start": 125.0, "dur": 45.0, "color": "#C44E52", "label": "Loop Detection & Pose Graph Opt. (45.0ms)"}
            ]
        },
        {
            "title": "4. ORB-SLAM3 Hybrid KLT Tracking (Ours) -- 3 Concurrent Threads (Optimized CPU)",
            "subtitle": "Lightweight KLT on non-KFs (19-25 ms) + Selective ORB on KFs + 40% reduced keyframe load",
            "height": 360,
            "lanes": [
                {"name": "Hybrid Tracking Thread", "tag": "KLT / Selective ORB"},
                {"name": "Local Mapping Thread", "tag": "Reduced BA Load (-40%)"},
                {"name": "Loop Closing Thread", "tag": "Atlas & DBoW2"}
            ],
            "blocks": [
                # Hybrid Tracking Thread
                {"lane": 0, "start": 0.0, "dur": 42.0, "color": "#E377C2", "label": "F0 Keyframe ORB (42.0ms)"},
                {"lane": 0, "start": 44.0, "dur": 19.0, "color": "#55A868", "label": "F1 KLT (19.0ms)"},
                {"lane": 0, "start": 65.0, "dur": 18.5, "color": "#55A868", "label": "F2 KLT (18.5ms)"},
                {"lane": 0, "start": 85.0, "dur": 19.5, "color": "#55A868", "label": "F3 KLT (19.5ms)"},
                {"lane": 0, "start": 106.0, "dur": 18.8, "color": "#55A868", "label": "F4 KLT (18.8ms)"},
                {"lane": 0, "start": 126.0, "dur": 40.5, "color": "#E377C2", "label": "F5 Keyframe ORB (40.5ms)"},
                {"lane": 0, "start": 168.0, "dur": 11.5, "color": "#55A868", "label": "F6 KLT"},
                # Local Mapping Thread (Fewer keyframes = low contention)
                {"lane": 1, "start": 43.0, "dur": 38.0, "color": "#8172B2", "label": "Sparse Local BA (38.0ms)"},
                {"lane": 1, "start": 128.0, "dur": 39.0, "color": "#8172B2", "label": "Sparse Local BA (39.0ms)"},
                # Loop Closing Thread
                {"lane": 2, "start": 82.0, "dur": 32.0, "color": "#C44E52", "label": "DBoW2 Loop Detection & Sim3 (32.0ms)"}
            ]
        },
        {
            "title": "5. NVIDIA cuVSLAM Thread Architecture -- 3 GPU-Accelerated Pipelines (CUDA Cores)",
            "subtitle": "Real-Time GPU Frontend (5.8 ms / >170 FPS) + Asynchronous Local BA (9.5 ms) + GPU Loop PGO (12.0 ms)",
            "height": 360,
            "lanes": [
                {"name": "GPU Tracking Frontend", "tag": "CUDA Kernel Streams"},
                {"name": "GPU Local Mapping", "tag": "Asynch Keyframe BA"},
                {"name": "GPU Loop Closing", "tag": "DBoW & PGO Engine"}
            ],
            "blocks": [
                # GPU Tracking Frontend (Ultra fast 5.8ms per frame)
                {"lane": 0, "start": 0.0, "dur": 1.0, "color": "#64B5F6", "label": "Rect."},
                {"lane": 0, "start": 1.0, "dur": 1.9, "color": "#DD8452", "label": "GPU KLT (1.9ms)"},
                {"lane": 0, "start": 2.9, "dur": 0.5, "color": "#55A868", "label": "IMU"},
                {"lane": 0, "start": 3.4, "dur": 2.4, "color": "#C44E52", "label": "GPU Pose Opt (2.4ms)"},

                {"lane": 0, "start": 12.0, "dur": 5.8, "color": "#DD8452", "label": "F51 GPU Tracking (5.8ms)"},
                {"lane": 0, "start": 24.0, "dur": 5.7, "color": "#DD8452", "label": "F52 GPU Tracking (5.7ms)"},
                {"lane": 0, "start": 36.0, "dur": 5.9, "color": "#DD8452", "label": "F53 GPU Tracking (5.9ms)"},
                {"lane": 0, "start": 48.0, "dur": 5.8, "color": "#DD8452", "label": "F54 GPU Tracking (5.8ms)"},
                {"lane": 0, "start": 60.0, "dur": 5.8, "color": "#DD8452", "label": "F55 GPU Tracking (5.8ms)"},

                # GPU Local Mapping Thread
                {"lane": 1, "start": 6.0, "dur": 9.5, "color": "#8172B2", "label": "GPU Local Bundle Adjustment (9.5ms)"},
                {"lane": 1, "start": 54.0, "dur": 9.8, "color": "#8172B2", "label": "GPU Local Bundle Adjustment (9.8ms)"},

                # GPU Loop Closing Thread
                {"lane": 2, "start": 64.0, "dur": 12.0, "color": "#DA8BC3", "label": "GPU Loop Detection & PGO (12.0ms)"}
            ]
        }
    ]

    # 1. RENDER SVG
    svg_lines = []
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg_lines.append(f'<defs><style>text {{ font-family: "DejaVu Sans", "Helvetica", Arial, sans-serif; }}</style></defs>')
    svg_lines.append(f'<rect width="{W}" height="{H}" fill="#1a1a2e"/>')

    # Main Header
    svg_lines.append(f'<text x="{W//2}" y="50" fill="#ffffff" font-size="32" font-weight="bold" text-anchor="middle">Multi-Thread SLAM / VIO Architectural Execution Comparison</text>')
    svg_lines.append(f'<text x="{W//2}" y="85" fill="#64B5F6" font-size="18" font-weight="bold" text-anchor="middle">Comparing MSCKF Filter vs Factor Graph vs ORB-SLAM3 Baseline vs Hybrid KLT vs GPU cuVSLAM</text>')

    cur_y = margin_top
    for p_idx, p in enumerate(panels):
        panel_h = p["height"]
        svg_lines.append(f'<rect x="{margin_left}" y="{cur_y}" width="{plot_w}" height="{panel_h}" rx="8" fill="#16213e" stroke="#2a3b5c" stroke-width="1.5"/>')
        
        # Panel Title
        svg_lines.append(f'<text x="{margin_left + 18}" y="{cur_y + 28}" fill="#ffffff" font-size="18" font-weight="bold">{p["title"]}</text>')
        svg_lines.append(f'<text x="{margin_left + 18}" y="{cur_y + 48}" fill="#a0a0b0" font-size="13">{p["subtitle"]}</text>')

        # Grid lines inside panel
        lanes_start_y = cur_y + 60
        lanes_total_h = panel_h - 72
        num_lanes = len(p["lanes"])
        lane_step_h = lanes_total_h / num_lanes

        t_val = 0.0
        while t_val <= max_time_ms:
            gx = margin_left + (t_val / max_time_ms) * plot_w
            svg_lines.append(f'<line x1="{gx}" y1="{lanes_start_y}" x2="{gx}" y2="{lanes_start_y + lanes_total_h}" stroke="#ffffff1a" stroke-dasharray="4,4" stroke-width="1"/>')
            if p_idx == len(panels) - 1:
                svg_lines.append(f'<text x="{gx}" y="{cur_y + panel_h + 26}" fill="#a0a0b0" font-size="15" text-anchor="middle" font-weight="bold">{int(t_val)} ms</text>')
            t_val += 20.0

        # Lanes & labels
        for l_idx, lane in enumerate(p["lanes"]):
            ly = lanes_start_y + l_idx * lane_step_h
            if l_idx > 0:
                svg_lines.append(f'<line x1="{margin_left}" y1="{ly}" x2="{margin_left + plot_w}" y2="{ly}" stroke="#ffffff15" stroke-width="1"/>')
            
            l_mid = ly + lane_step_h / 2
            svg_lines.append(f'<text x="{margin_left - 16}" y="{l_mid - 2}" fill="#ffffff" font-size="15" font-weight="bold" text-anchor="end">{lane["name"]}</text>')
            svg_lines.append(f'<text x="{margin_left - 16}" y="{l_mid + 16}" fill="#8172B2" font-size="12" font-weight="bold" text-anchor="end">[{lane["tag"]}]</text>')

        # Blocks
        bar_h = min(lane_step_h * 0.70, 46)
        for b in p["blocks"]:
            lane_idx = b["lane"]
            ly = lanes_start_y + lane_idx * lane_step_h
            l_mid = ly + lane_step_h / 2
            by = l_mid - bar_h / 2
            bx = margin_left + (b["start"] / max_time_ms) * plot_w
            bw = max(4.0, (b["dur"] / max_time_ms) * plot_w)

            svg_lines.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bar_h}" rx="6" fill="{b["color"]}" stroke="#ffffff" stroke-width="1" opacity="0.95"/>')
            if bw > 55 and b["label"]:
                svg_lines.append(f'<text x="{bx + bw/2}" y="{l_mid + 5}" fill="#ffffff" font-size="12" font-weight="bold" text-anchor="middle">{b["label"]}</text>')

        cur_y += panel_h + 24

    # X-axis label
    svg_lines.append(f'<text x="{margin_left + plot_w//2}" y="{H - 25}" fill="#ffffff" font-size="18" font-weight="bold" text-anchor="middle">Timeline (ms) from sequence start</text>')
    svg_lines.append('</svg>')

    os.makedirs(os.path.dirname(out_svg), exist_ok=True)
    with open(out_svg, "w") as f:
        f.write("\n".join(svg_lines))
    print(f"[✔] Saved 5-Way Comparison SVG → {out_svg}")

    # 2. RENDER PURE PNG
    canvas = PureCanvas(W, H, "#1a1a2e")
    canvas.draw_text(W // 2, 35, "Multi-Thread SLAM / VIO Architectural Execution Comparison", 28, "#ffffff", bold=True, align="center")
    canvas.draw_text(W // 2, 70, "Comparing MSCKF Filter vs Factor Graph vs ORB-SLAM3 Baseline vs Hybrid KLT vs GPU cuVSLAM", 16, "#64B5F6", bold=True, align="center")

    cur_y = margin_top
    for p_idx, p in enumerate(panels):
        panel_h = p["height"]
        canvas.draw_rounded_rect(margin_left, cur_y, plot_w, panel_h, 8, "#16213e", "#2a3b5c", 2)
        canvas.draw_text(margin_left + 18, cur_y + 16, p["title"], 16, "#ffffff", bold=True)
        canvas.draw_text(margin_left + 18, cur_y + 38, p["subtitle"], 12, "#a0a0b0")

        lanes_start_y = cur_y + 60
        lanes_total_h = panel_h - 72
        num_lanes = len(p["lanes"])
        lane_step_h = lanes_total_h / num_lanes

        t_val = 0.0
        while t_val <= max_time_ms:
            gx = int(margin_left + (t_val / max_time_ms) * plot_w)
            canvas.draw_line(gx, lanes_start_y, gx, lanes_start_y + lanes_total_h, "#ffffff1a", 1, dashed=True, dash_len=6)
            if p_idx == len(panels) - 1:
                canvas.draw_text(gx, cur_y + panel_h + 12, f"{int(t_val)} ms", 14, "#a0a0b0", bold=True, align="center")
            t_val += 20.0

        for l_idx, lane in enumerate(p["lanes"]):
            ly = lanes_start_y + int(l_idx * lane_step_h)
            if l_idx > 0:
                canvas.draw_line(margin_left, ly, margin_left + plot_w, ly, "#ffffff15", 1)
            l_mid = int(ly + lane_step_h / 2)
            canvas.draw_text(margin_left - 16, l_mid - 14, lane["name"], 14, "#ffffff", bold=True, align="right")
            canvas.draw_text(margin_left - 16, l_mid + 3, f"[{lane['tag']}]", 12, "#8172B2", bold=True, align="right")

        bar_h = min(lane_step_h * 0.70, 46)
        for b in p["blocks"]:
            lane_idx = b["lane"]
            ly = lanes_start_y + int(lane_idx * lane_step_h)
            l_mid = int(ly + lane_step_h / 2)
            by = int(l_mid - bar_h / 2)
            bx = int(margin_left + (b["start"] / max_time_ms) * plot_w)
            bw = max(5, int((b["dur"] / max_time_ms) * plot_w))

            canvas.draw_rounded_rect(bx, by, bw, int(bar_h), 5, b["color"], "#ffffff", 1)
            if bw > 55 and b["label"]:
                canvas.draw_text(bx + bw // 2, l_mid - 6, b["label"], 11, "#ffffff", bold=True, align="center")

        cur_y += panel_h + 24

    canvas.draw_text(margin_left + plot_w // 2, H - 35, "Timeline (ms) from sequence start", 16, "#ffffff", bold=True, align="center")
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    canvas.save_png(out_png)

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_png1 = os.path.join(project_root, "multithread_architecture_comparison.png")
    out_png2 = os.path.join(project_root, "gantt_charts", "multithread_architecture_comparison.png")
    out_svg = os.path.join(project_root, "gantt_charts", "multithread_architecture_comparison.svg")

    render_multithread_comparison(out_png1, out_svg)
    import shutil
    shutil.copyfile(out_png1, out_png2)
    print(f"[✔] Copied 5-Way comparison PNG to gantt_charts/ directory")

if __name__ == "__main__":
    main()
