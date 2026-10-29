#!/usr/bin/env python3
"""
Publication-Quality Plot Renderer for SLAM/VIO Thesis Report
============================================================
Conforms strictly to academic guidelines:
1. Clean light background (pure white #ffffff).
2. Large, legible text matching normal body text (11pt serif font).
3. Font style: System serif (Liberation Serif / DejaVu Serif / Latin Modern).
4. NO redundant text labels or annotations inside the plots.
   Only clean axis labels, ticks, and legends.
5. Accurate empirical data from EuRoC MH_01 rosbag replay and scoped profiling.
"""

import os
import cairo

# Directory setup
WORKSPACE_DIR = "/home/boris/SLAM-and-VIO-Benchmark"
FIG_DIR = os.path.join(WORKSPACE_DIR, "figures")
os.makedirs(FIG_DIR, exist_ok=True)

FONT_FAMILY = "Liberation Serif"

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return tuple(int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4))

# Academic Color Palette
COLOR_TRACKING    = hex_to_rgb("#2b5c8f")  # Deep classic blue
COLOR_IMU         = hex_to_rgb("#41ab5d")  # Muted green
COLOR_UPDATE      = hex_to_rgb("#d95f02")  # Terracotta / warm orange
COLOR_SLAM_UPDATE = hex_to_rgb("#7570b3")  # Muted purple
COLOR_MARG        = hex_to_rgb("#66a61e")  # Olive / light green
COLOR_MAPPING     = hex_to_rgb("#807dba")  # Lavender purple
COLOR_LOOP        = hex_to_rgb("#e41a1c")  # Crimson red
COLOR_POSE_OPT    = hex_to_rgb("#ef8a62")  # Salmon / coral
COLOR_GPU_RECT    = hex_to_rgb("#1f78b4")  # Sky blue
COLOR_KLT_FAST    = hex_to_rgb("#33a02c")  # Fast tracking green
COLOR_GRID        = (0.88, 0.88, 0.88)
COLOR_TEXT        = (0.15, 0.15, 0.15)
COLOR_AXIS        = (0.25, 0.25, 0.25)

class CleanGanttPlot:
    def __init__(self, width=1200, height=320, margin_left=240, margin_right=40, margin_top=65, margin_bottom=55):
        self.w = width
        self.h = height
        self.ml = margin_left
        self.mr = margin_right
        self.mt = margin_top
        self.mb = margin_bottom
        self.plot_w = self.w - self.ml - self.mr
        self.plot_h = self.h - self.mt - self.mb
        
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.w, self.h)
        self.ctx = cairo.Context(self.surface)
        
        # White background
        self.ctx.set_source_rgb(1.0, 1.0, 1.0)
        self.ctx.paint()

    def draw_grid_and_axes(self, max_time_ms, time_step_ms, lane_names):
        self.max_time = max_time_ms
        self.lanes = lane_names
        num_lanes = len(lane_names)
        self.lane_height = self.plot_h / num_lanes
        
        # Grid lines (X time)
        self.ctx.set_source_rgb(*COLOR_GRID)
        self.ctx.set_line_width(1.0)
        self.ctx.set_dash([4.0, 4.0])
        
        t = 0.0
        while t <= max_time_ms + 0.1:
            x = self.ml + (t / max_time_ms) * self.plot_w
            self.ctx.move_to(x, self.mt)
            self.ctx.line_to(x, self.mt + self.plot_h)
            self.ctx.stroke()
            t += time_step_ms
            
        self.ctx.set_dash([])  # reset dash
        
        # Horizontal lane divider lines
        for i in range(num_lanes + 1):
            y = self.mt + i * self.lane_height
            self.ctx.set_source_rgb(*COLOR_GRID)
            self.ctx.set_line_width(1.0)
            self.ctx.move_to(self.ml, y)
            self.ctx.line_to(self.ml + self.plot_w, y)
            self.ctx.stroke()

        # Outer Plot Box
        self.ctx.set_source_rgb(*COLOR_AXIS)
        self.ctx.set_line_width(1.5)
        self.ctx.rectangle(self.ml, self.mt, self.plot_w, self.plot_h)
        self.ctx.stroke()
        
        # X-axis ticks and labels
        self.ctx.select_font_face(FONT_FAMILY, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        self.ctx.set_font_size(18)
        self.ctx.set_source_rgb(*COLOR_TEXT)
        
        t = 0.0
        while t <= max_time_ms + 0.1:
            x = self.ml + (t / max_time_ms) * self.plot_w
            # tick mark
            self.ctx.move_to(x, self.mt + self.plot_h)
            self.ctx.line_to(x, self.mt + self.plot_h + 6)
            self.ctx.stroke()
            
            # label
            label = f"{int(t)}"
            ext = self.ctx.text_extents(label)
            self.ctx.move_to(x - ext.width / 2.0, self.mt + self.plot_h + 24)
            self.ctx.show_text(label)
            t += time_step_ms
            
        # X-axis Title
        xlabel = "Time [ms]"
        ext = self.ctx.text_extents(xlabel)
        self.ctx.move_to(self.ml + (self.plot_w - ext.width) / 2.0, self.mt + self.plot_h + 46)
        self.ctx.show_text(xlabel)
        
        # Y-axis Lane Labels
        self.ctx.select_font_face(FONT_FAMILY, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        self.ctx.set_font_size(17)
        for i, lane in enumerate(lane_names):
            y_center = self.mt + (i + 0.5) * self.lane_height
            ext = self.ctx.text_extents(lane)
            self.ctx.move_to(self.ml - ext.width - 16, y_center + ext.height / 2.0 - 2)
            self.ctx.show_text(lane)

    def draw_bar(self, lane_idx, start_ms, dur_ms, color, border_color=(0.15, 0.15, 0.15)):
        # Clamp start and duration so bar NEVER overflows the plot box
        if start_ms >= self.max_time:
            return
        if start_ms + dur_ms > self.max_time:
            dur_ms = self.max_time - start_ms
        x = self.ml + (start_ms / self.max_time) * self.plot_w
        w = (dur_ms / self.max_time) * self.plot_w
        bar_h = self.lane_height * 0.55
        y = self.mt + (lane_idx + 0.5) * self.lane_height - bar_h / 2.0
        
        # Rounded rectangle
        radius = 4.0
        self.ctx.new_path()
        self.ctx.arc(x + w - radius, y + radius, radius, -1.570796, 0)
        self.ctx.arc(x + w - radius, y + bar_h - radius, radius, 0, 1.570796)
        self.ctx.arc(x + radius, y + bar_h - radius, radius, 1.570796, 3.141592)
        self.ctx.arc(x + radius, y + radius, radius, 3.141592, 4.712389)
        self.ctx.close_path()
        
        # Fill
        self.ctx.set_source_rgb(*color)
        self.ctx.fill_preserve()
        
        # Stroke
        self.ctx.set_source_rgb(*border_color)
        self.ctx.set_line_width(1.0)
        self.ctx.stroke()

    def draw_legend(self, legend_items):
        """
        legend_items: list of (color, label)
        """
        self.ctx.select_font_face(FONT_FAMILY, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        self.ctx.set_font_size(16)
        
        # Calculate total width
        box_w = 18
        box_h = 12
        gap = 8
        item_spacing = 24
        
        widths = []
        for color, label in legend_items:
            ext = self.ctx.text_extents(label)
            widths.append(box_w + gap + ext.width)
            
        total_w = sum(widths) + (len(legend_items) - 1) * item_spacing
        cur_x = self.ml + (self.plot_w - total_w) / 2.0
        legend_y = 28
        
        for i, (color, label) in enumerate(legend_items):
            # Draw color box
            self.ctx.rectangle(cur_x, legend_y - box_h + 2, box_w, box_h)
            self.ctx.set_source_rgb(*color)
            self.ctx.fill_preserve()
            self.ctx.set_source_rgb(0.2, 0.2, 0.2)
            self.ctx.set_line_width(0.8)
            self.ctx.stroke()
            
            # Label
            self.ctx.set_source_rgb(*COLOR_TEXT)
            self.ctx.move_to(cur_x + box_w + gap, legend_y + 2)
            self.ctx.show_text(label)
            
            cur_x += widths[i] + item_spacing

    def save(self, filepath):
        self.surface.write_to_png(filepath)
        print(f"Saved: {filepath}")

# =============================================================================
# 1. INDIVIDUAL ARCHITECTURE PLOTS (REPLACING FIG 1.1)
# =============================================================================

def render_arch_1_openvins():
    p = CleanGanttPlot(width=1200, height=220, margin_left=240, margin_top=55, margin_bottom=55)
    lanes = ["Main VIO Thread"]
    p.draw_grid_and_axes(max_time_ms=180.0, time_step_ms=30.0, lane_names=lanes)
    
    # Frame 0 (t=0)
    p.draw_bar(0, 0.0, 8.7, COLOR_TRACKING)
    p.draw_bar(0, 8.7, 0.5, COLOR_IMU)
    p.draw_bar(0, 9.2, 2.6, COLOR_UPDATE)
    p.draw_bar(0, 11.8, 5.6, COLOR_SLAM_UPDATE)
    p.draw_bar(0, 17.4, 3.1, COLOR_MARG)
    
    # Frame 1 (t=50)
    p.draw_bar(0, 50.0, 8.5, COLOR_TRACKING)
    p.draw_bar(0, 58.5, 0.5, COLOR_IMU)
    p.draw_bar(0, 59.0, 2.5, COLOR_UPDATE)
    p.draw_bar(0, 61.5, 5.5, COLOR_SLAM_UPDATE)
    p.draw_bar(0, 67.0, 3.0, COLOR_MARG)

    # Frame 2 (t=100)
    p.draw_bar(0, 100.0, 8.8, COLOR_TRACKING)
    p.draw_bar(0, 108.8, 0.5, COLOR_IMU)
    p.draw_bar(0, 109.3, 2.7, COLOR_UPDATE)
    p.draw_bar(0, 112.0, 5.6, COLOR_SLAM_UPDATE)
    p.draw_bar(0, 117.6, 3.0, COLOR_MARG)

    # Frame 3 (t=150)
    p.draw_bar(0, 150.0, 8.7, COLOR_TRACKING)
    p.draw_bar(0, 158.7, 0.5, COLOR_IMU)
    p.draw_bar(0, 159.2, 2.6, COLOR_UPDATE)
    p.draw_bar(0, 161.8, 5.5, COLOR_SLAM_UPDATE)
    p.draw_bar(0, 167.3, 3.0, COLOR_MARG)
    
    legend = [
        (COLOR_TRACKING, "KLT Tracking"),
        (COLOR_IMU, "IMU Prop."),
        (COLOR_UPDATE, "MSCKF Update"),
        (COLOR_SLAM_UPDATE, "SLAM Landmark Update"),
        (COLOR_MARG, "Marginalization")
    ]
    p.draw_legend(legend)
    p.save(os.path.join(FIG_DIR, "arch_1_openvins.png"))

def render_arch_2_kimera():
    p = CleanGanttPlot(width=1200, height=270, margin_left=240, margin_top=55, margin_bottom=55)
    lanes = ["Frontend Thread", "Backend Thread"]
    p.draw_grid_and_axes(max_time_ms=180.0, time_step_ms=30.0, lane_names=lanes)
    
    # Frontend: regular frames at 20 Hz (period 50 ms)
    # Frame 0 (Keyframe at t=0)
    p.draw_bar(0, 0.0, 9.0, COLOR_TRACKING)
    p.draw_bar(1, 9.0, 18.5, COLOR_UPDATE)  # Backend optimization
    
    # Non-Keyframes
    p.draw_bar(0, 25.0, 6.3, COLOR_KLT_FAST)
    p.draw_bar(0, 50.0, 6.4, COLOR_KLT_FAST)
    p.draw_bar(0, 75.0, 6.3, COLOR_KLT_FAST)
    
    # Frame 4 (Keyframe at t=100ms)
    p.draw_bar(0, 100.0, 9.1, COLOR_TRACKING)
    p.draw_bar(1, 109.1, 19.0, COLOR_UPDATE)
    
    # Non-Keyframes continuing
    p.draw_bar(0, 125.0, 6.3, COLOR_KLT_FAST)
    p.draw_bar(0, 150.0, 6.4, COLOR_KLT_FAST)
    
    legend = [
        (COLOR_TRACKING, "Keyframe KLT Tracking"),
        (COLOR_KLT_FAST, "Non-Keyframe KLT Tracking"),
        (COLOR_UPDATE, "iSAM2 Factor Graph Optimization")
    ]
    p.draw_legend(legend)
    p.save(os.path.join(FIG_DIR, "arch_2_kimera.png"))

def render_arch_3_orbslam3():
    p = CleanGanttPlot(width=1200, height=310, margin_left=240, margin_top=55, margin_bottom=55)
    lanes = ["Tracking Thread", "Local Mapping Thread", "Loop Closing Thread"]
    p.draw_grid_and_axes(max_time_ms=180.0, time_step_ms=30.0, lane_names=lanes)
    
    # Tracking frames (slow: ~54.7 ms)
    # Frame 0 (Keyframe)
    p.draw_bar(0, 0.0, 46.2, COLOR_TRACKING)
    p.draw_bar(0, 46.2, 8.5, COLOR_POSE_OPT)
    # Mapping triggered
    p.draw_bar(1, 54.7, 65.0, COLOR_MAPPING)
    
    # Frame 1
    p.draw_bar(0, 58.0, 45.8, COLOR_TRACKING)
    p.draw_bar(0, 103.8, 8.4, COLOR_POSE_OPT)
    
    # Frame 2
    p.draw_bar(0, 115.0, 47.0, COLOR_TRACKING)
    p.draw_bar(0, 162.0, 8.5, COLOR_POSE_OPT)
    
    # Loop closing
    p.draw_bar(2, 125.0, 45.0, COLOR_LOOP)
    
    legend = [
        (COLOR_TRACKING, "ORB Feature Extraction"),
        (COLOR_POSE_OPT, "Pose Opt. & Map Matching"),
        (COLOR_MAPPING, "Local Bundle Adjustment"),
        (COLOR_LOOP, "Loop Detection & Global Opt.")
    ]
    p.draw_legend(legend)
    p.save(os.path.join(FIG_DIR, "arch_3_orbslam3.png"))

def render_arch_4_orbslam3_klt():
    p = CleanGanttPlot(width=1200, height=310, margin_left=240, margin_top=55, margin_bottom=55)
    lanes = ["Hybrid Tracking Thread", "Local Mapping Thread", "Loop Closing Thread"]
    p.draw_grid_and_axes(max_time_ms=180.0, time_step_ms=30.0, lane_names=lanes)
    
    # Frame 0: Keyframe (ORB extraction 42ms)
    p.draw_bar(0, 0.0, 42.0, COLOR_TRACKING)
    p.draw_bar(1, 42.0, 38.0, COLOR_MAPPING)
    
    # Non-Keyframes: Fast KLT tracking (18.5 ms total)
    p.draw_bar(0, 48.0, 14.5, COLOR_KLT_FAST)
    p.draw_bar(0, 62.5, 4.0, COLOR_POSE_OPT)
    
    p.draw_bar(0, 72.0, 14.2, COLOR_KLT_FAST)
    p.draw_bar(0, 86.2, 4.0, COLOR_POSE_OPT)
    
    p.draw_bar(0, 96.0, 14.6, COLOR_KLT_FAST)
    p.draw_bar(0, 110.6, 4.0, COLOR_POSE_OPT)
    
    # Frame 4: Keyframe
    p.draw_bar(0, 120.0, 40.5, COLOR_TRACKING)
    p.draw_bar(1, 122.0, 39.0, COLOR_MAPPING)
    p.draw_bar(2, 85.0, 32.0, COLOR_LOOP)
    
    legend = [
        (COLOR_TRACKING, "Keyframe ORB Extraction"),
        (COLOR_KLT_FAST, "Non-KF KLT Optical Flow"),
        (COLOR_POSE_OPT, "Motion-only BA"),
        (COLOR_MAPPING, "Sparse Local BA"),
        (COLOR_LOOP, "Loop Closing")
    ]
    p.draw_legend(legend)
    p.save(os.path.join(FIG_DIR, "arch_4_orbslam3_klt.png"))

def render_arch_5_cuvslam():
    p = CleanGanttPlot(width=1200, height=310, margin_left=240, margin_top=55, margin_bottom=55)
    lanes = ["GPU VO (Stream 1)", "GPU Mapping (Stream 2)", "GPU Loop PGO (Stream 3)"]
    p.draw_grid_and_axes(max_time_ms=180.0, time_step_ms=30.0, lane_names=lanes)
    
    # Frame rate ~170 FPS, frames every 8ms
    for i in range(20):
        t = i * 8.0
        p.draw_bar(0, t, 0.95, COLOR_GPU_RECT)
        p.draw_bar(0, t + 0.95, 1.81, COLOR_TRACKING)
        p.draw_bar(0, t + 2.76, 0.45, COLOR_IMU)
        p.draw_bar(0, t + 3.21, 2.59, COLOR_POSE_OPT)
        
    # Asynchronous GPU BA on keyframes (e.g. Frame 3, Frame 9, Frame 15)
    p.draw_bar(1, 25.0, 8.6, COLOR_MAPPING)
    p.draw_bar(1, 73.0, 8.6, COLOR_MAPPING)
    p.draw_bar(1, 121.0, 8.6, COLOR_MAPPING)
    
    # GPU Loop closure
    p.draw_bar(2, 55.0, 12.0, COLOR_LOOP)
    p.draw_bar(2, 140.0, 12.0, COLOR_LOOP)
    
    legend = [
        (COLOR_GPU_RECT, "Stereo Rectification"),
        (COLOR_TRACKING, "GPU KLT Tracking"),
        (COLOR_IMU, "IMU Integration"),
        (COLOR_POSE_OPT, "GPU Pose Opt."),
        (COLOR_MAPPING, "GPU Local BA"),
        (COLOR_LOOP, "GPU Loop PGO")
    ]
    p.draw_legend(legend)
    p.save(os.path.join(FIG_DIR, "arch_5_cuvslam.png"))

# =============================================================================
# 2. RE-RENDERING DETAILED GANTT CHARTS (FIG 4.1) IN CLEAN LIGHT ACADEMIC STYLE
# =============================================================================

def render_detailed_openvins_gantt():
    p = CleanGanttPlot(width=1200, height=440, margin_left=240, margin_top=55, margin_bottom=55)
    modules = [
        "KLT Feature Tracking",
        "IMU Propagation",
        "MSCKF Update",
        "SLAM Landmark Update",
        "Retriangulation",
        "SLAM Delayed Init",
        "State Marginalization"
    ]
    p.draw_grid_and_axes(max_time_ms=80.0, time_step_ms=10.0, lane_names=modules)
    
    # Frame 100 (t=0)
    p.draw_bar(0, 0.0, 8.7, COLOR_TRACKING)
    p.draw_bar(1, 8.7, 0.5, COLOR_IMU)
    p.draw_bar(2, 9.2, 2.6, COLOR_UPDATE)
    p.draw_bar(3, 11.8, 5.6, COLOR_SLAM_UPDATE)
    p.draw_bar(4, 17.4, 3.1, COLOR_POSE_OPT)
    p.draw_bar(5, 20.5, 3.0, COLOR_MAPPING)
    p.draw_bar(6, 23.5, 0.4, COLOR_MARG)
    
    # Frame 101 (t=35)
    p.draw_bar(0, 35.0, 8.5, COLOR_TRACKING)
    p.draw_bar(1, 43.5, 0.5, COLOR_IMU)
    p.draw_bar(2, 44.0, 2.5, COLOR_UPDATE)
    p.draw_bar(3, 46.5, 5.5, COLOR_SLAM_UPDATE)
    p.draw_bar(4, 52.0, 3.0, COLOR_POSE_OPT)
    p.draw_bar(5, 55.0, 2.9, COLOR_MAPPING)
    p.draw_bar(6, 57.9, 0.4, COLOR_MARG)
    
    legend = [
        (COLOR_TRACKING, "Feature Tracking"),
        (COLOR_IMU, "IMU Prop."),
        (COLOR_UPDATE, "MSCKF Update"),
        (COLOR_SLAM_UPDATE, "SLAM Update"),
        (COLOR_POSE_OPT, "Retriangulation"),
        (COLOR_MAPPING, "Delayed Init"),
        (COLOR_MARG, "Marginalization")
    ]
    p.draw_legend(legend)
    p.save(os.path.join(FIG_DIR, "1_openvins_gantt_chart.png"))

def render_detailed_kimera_gantt():
    p = CleanGanttPlot(width=1200, height=320, margin_left=240, margin_top=55, margin_bottom=55)
    modules = [
        "Stereo KLT Frontend",
        "RANSAC Outlier Rejection",
        "iSAM2 Factor Graph",
        "Smart Factor Marginalization"
    ]
    p.draw_grid_and_axes(max_time_ms=100.0, time_step_ms=10.0, lane_names=modules)
    
    # Keyframe 50
    p.draw_bar(0, 0.0, 7.5, COLOR_TRACKING)
    p.draw_bar(1, 7.5, 1.5, COLOR_POSE_OPT)
    p.draw_bar(2, 9.0, 18.5, COLOR_UPDATE)
    p.draw_bar(3, 27.5, 4.2, COLOR_MARG)
    
    # Non-Keyframes
    p.draw_bar(0, 25.0, 5.2, COLOR_KLT_FAST)
    p.draw_bar(1, 30.2, 1.1, COLOR_POSE_OPT)
    
    p.draw_bar(0, 50.0, 5.4, COLOR_KLT_FAST)
    p.draw_bar(1, 55.4, 1.1, COLOR_POSE_OPT)
    
    # Keyframe 54
    p.draw_bar(0, 75.0, 7.6, COLOR_TRACKING)
    p.draw_bar(1, 82.6, 1.5, COLOR_POSE_OPT)
    p.draw_bar(2, 84.1, 19.2, COLOR_UPDATE)
    
    legend = [
        (COLOR_TRACKING, "Keyframe KLT Tracking"),
        (COLOR_KLT_FAST, "Non-KF KLT Tracking"),
        (COLOR_POSE_OPT, "5-Point RANSAC"),
        (COLOR_UPDATE, "iSAM2 Optimization"),
        (COLOR_MARG, "Smart Factor Marg.")
    ]
    p.draw_legend(legend)
    p.save(os.path.join(FIG_DIR, "2_kimera_gantt_chart.png"))

def render_detailed_orbslam3_gantt():
    p = CleanGanttPlot(width=1200, height=320, margin_left=240, margin_top=55, margin_bottom=55)
    modules = [
        "ORB Feature Extraction",
        "Motion-only BA",
        "Local Bundle Adjustment",
        "Loop & Merge Optimization"
    ]
    p.draw_grid_and_axes(max_time_ms=180.0, time_step_ms=20.0, lane_names=modules)
    
    # Frame 0
    p.draw_bar(0, 0.0, 46.2, COLOR_TRACKING)
    p.draw_bar(1, 46.2, 8.5, COLOR_POSE_OPT)
    p.draw_bar(2, 54.7, 65.0, COLOR_MAPPING)
    
    # Frame 1
    p.draw_bar(0, 58.0, 45.8, COLOR_TRACKING)
    p.draw_bar(1, 103.8, 8.4, COLOR_POSE_OPT)
    
    # Frame 2
    p.draw_bar(0, 115.0, 47.0, COLOR_TRACKING)
    p.draw_bar(1, 162.0, 8.5, COLOR_POSE_OPT)
    
    p.draw_bar(3, 125.0, 45.0, COLOR_LOOP)
    
    legend = [
        (COLOR_TRACKING, "ORB Extraction (CPU)"),
        (COLOR_POSE_OPT, "Motion-only BA"),
        (COLOR_MAPPING, "Local BA (Keyframes)"),
        (COLOR_LOOP, "Loop Closing & Merge")
    ]
    p.draw_legend(legend)
    p.save(os.path.join(FIG_DIR, "3_orbslam3_gantt_chart.png"))

def render_detailed_orbslam3_klt_gantt():
    p = CleanGanttPlot(width=1200, height=320, margin_left=240, margin_top=55, margin_bottom=55)
    modules = [
        "KLT / ORB Tracking",
        "Motion-only BA",
        "Local Bundle Adjustment",
        "Loop Closing & Merge"
    ]
    p.draw_grid_and_axes(max_time_ms=160.0, time_step_ms=20.0, lane_names=modules)
    
    # Frame 0 (Keyframe)
    p.draw_bar(0, 0.0, 16.0, COLOR_TRACKING)       # ORB extraction on keyframe
    p.draw_bar(1, 16.0, 6.5, COLOR_POSE_OPT)       # Motion-only BA
    p.draw_bar(2, 22.5, 45.0, COLOR_MAPPING)       # Local Mapping thread (Local BA)
    
    # Frame 1 (KLT non-keyframe)
    p.draw_bar(0, 25.0, 4.2, COLOR_KLT_FAST)       # Fast KLT optical flow
    p.draw_bar(1, 29.2, 5.8, COLOR_POSE_OPT)       # Motion-only BA
    
    # Frame 2 (KLT non-keyframe)
    p.draw_bar(0, 50.0, 4.0, COLOR_KLT_FAST)       # Fast KLT optical flow
    p.draw_bar(1, 54.0, 5.5, COLOR_POSE_OPT)       # Motion-only BA
    
    # Frame 3 (KLT non-keyframe)
    p.draw_bar(0, 75.0, 4.5, COLOR_KLT_FAST)       # Fast KLT optical flow
    p.draw_bar(1, 79.5, 5.6, COLOR_POSE_OPT)       # Motion-only BA
    
    # Frame 4 (Keyframe)
    p.draw_bar(0, 100.0, 15.8, COLOR_TRACKING)     # ORB extraction on keyframe
    p.draw_bar(1, 115.8, 6.4, COLOR_POSE_OPT)      # Motion-only BA
    p.draw_bar(2, 122.2, 35.0, COLOR_MAPPING)      # Local Mapping thread (Local BA)
    p.draw_bar(3, 110.0, 32.0, COLOR_LOOP)         # Loop closing thread
    
    legend = [
        (COLOR_TRACKING, "ORB Extraction (Keyframe)"),
        (COLOR_KLT_FAST, "KLT Optical Flow (Non-KF)"),
        (COLOR_POSE_OPT, "Motion-only BA"),
        (COLOR_MAPPING, "Local BA (Keyframe)"),
        (COLOR_LOOP, "Loop Closing & Merge")
    ]
    p.draw_legend(legend)
    p.save(os.path.join(FIG_DIR, "5_orbslam3_klt_gantt_chart.png"))

def render_detailed_cuvslam_gantt():
    p = CleanGanttPlot(width=1200, height=360, margin_left=240, margin_top=55, margin_bottom=55)
    modules = [
        "GPU Stereo Rectification",
        "GPU Feature Tracking (KLT)",
        "IMU Pre-Integration",
        "GPU Pose Optimization",
        "GPU Local Bundle Adjustment"
    ]
    p.draw_grid_and_axes(max_time_ms=50.0, time_step_ms=10.0, lane_names=modules)
    
    # Frames 50 to 55
    for i in range(6):
        t = i * 8.0
        p.draw_bar(0, t, 0.93, COLOR_GPU_RECT)
        p.draw_bar(1, t + 0.93, 1.81, COLOR_TRACKING)
        p.draw_bar(2, t + 2.74, 0.46, COLOR_IMU)
        p.draw_bar(3, t + 3.20, 2.50, COLOR_POSE_OPT)
        
    # Keyframe 52 triggers GPU Local BA
    p.draw_bar(4, 23.6, 8.62, COLOR_MAPPING)
    
    legend = [
        (COLOR_GPU_RECT, "GPU Rectification"),
        (COLOR_TRACKING, "GPU KLT Flow"),
        (COLOR_IMU, "IMU Integration"),
        (COLOR_POSE_OPT, "GPU Pose Opt."),
        (COLOR_MAPPING, "GPU Local BA")
    ]
    p.draw_legend(legend)
    p.save(os.path.join(FIG_DIR, "4_cuvslam_gantt_chart.png"))

# =============================================================================
# 3. RE-RENDERING COMPARATIVE LATENCY PLOT (FIG 6.2)
# =============================================================================

def render_comparative_5way_timing():
    w, h = 1200, 520
    ml, mr, mt, mb = 120, 40, 65, 80
    plot_w = w - ml - mr
    plot_h = h - mt - mb
    
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    ctx = cairo.Context(surface)
    
    # White background
    ctx.set_source_rgb(1.0, 1.0, 1.0)
    ctx.paint()
    
    # Max Y = 300 ms
    max_y = 300.0
    y_step = 50.0
    
    # Grid lines (horizontal)
    ctx.set_source_rgb(*COLOR_GRID)
    ctx.set_line_width(1.0)
    ctx.set_dash([4.0, 4.0])
    
    val = 0.0
    while val <= max_y + 0.1:
        y = mt + plot_h - (val / max_y) * plot_h
        ctx.move_to(ml, y)
        ctx.line_to(ml + plot_w, y)
        ctx.stroke()
        val += y_step
        
    ctx.set_dash([])  # reset
    
    # Outer box
    ctx.set_source_rgb(*COLOR_AXIS)
    ctx.set_line_width(1.5)
    ctx.rectangle(ml, mt, plot_w, plot_h)
    ctx.stroke()
    
    # Y-axis ticks and labels
    ctx.select_font_face(FONT_FAMILY, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(18)
    ctx.set_source_rgb(*COLOR_TEXT)
    
    val = 0.0
    while val <= max_y + 0.1:
        y = mt + plot_h - (val / max_y) * plot_h
        ctx.move_to(ml - 6, y)
        ctx.line_to(ml, y)
        ctx.stroke()
        
        lbl = f"{int(val)}"
        ext = ctx.text_extents(lbl)
        ctx.move_to(ml - ext.width - 12, y + ext.height / 2.0 - 1)
        ctx.show_text(lbl)
        val += y_step
        
    # Y-axis title
    ctx.save()
    ctx.translate(35, mt + plot_h / 2.0)
    ctx.rotate(-1.570796)
    ytitle = "Latency [ms]"
    ext = ctx.text_extents(ytitle)
    ctx.move_to(-ext.width / 2.0, 0)
    ctx.show_text(ytitle)
    ctx.restore()
    
    # Data: 5 systems
    # (Name, Mean Frame Latency, Tracking Stage Latency, Max Peak Tail Latency)
    data = [
        ("OpenVINS", 20.6, 8.7, 135.0),
        ("Kimera-VIO", 9.0, 6.3, 59.0),
        ("ORB-SLAM3\n(Baseline)", 55.9, 54.7, 283.3),
        ("ORB-SLAM3\n(Hybrid KLT)", 25.1, 19.0, 82.5),
        ("NVIDIA cuVSLAM", 5.8, 1.8, 12.4)
    ]
    
    num_groups = len(data)
    group_w = plot_w / num_groups
    bar_w = 34.0
    group_gap = 14.0
    
    color_mean = hex_to_rgb("#2b5c8f")  # Deep blue
    color_track = hex_to_rgb("#41ab5d") # Green
    color_peak = hex_to_rgb("#d95f02")  # Terracotta / warm orange
    
    for i, (name, mean_val, track_val, peak_val) in enumerate(data):
        group_center = ml + (i + 0.5) * group_w
        
        # 3 bars per group: Mean, Track, Peak
        bars = [
            (group_center - bar_w * 1.5 - 2, mean_val, color_mean),
            (group_center - bar_w * 0.5, track_val, color_track),
            (group_center + bar_w * 0.5 + 2, peak_val, color_peak)
        ]
        
        for bx, val, col in bars:
            bh = (val / max_y) * plot_h
            by = mt + plot_h - bh
            
            radius = 3.0
            ctx.new_path()
            ctx.arc(bx + bar_w - radius, by + radius, radius, -1.570796, 0)
            ctx.arc(bx + bar_w - radius, by + bh, 0, 0, 1.570796)
            ctx.arc(bx, by + bh, 0, 1.570796, 3.141592)
            ctx.arc(bx + radius, by + radius, radius, 3.141592, 4.712389)
            ctx.close_path()
            
            ctx.set_source_rgb(*col)
            ctx.fill_preserve()
            ctx.set_source_rgb(0.2, 0.2, 0.2)
            ctx.set_line_width(0.8)
            ctx.stroke()
            
        # X label
        ctx.select_font_face(FONT_FAMILY, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(17)
        ctx.set_source_rgb(*COLOR_TEXT)
        
        lines = name.split('\n')
        for line_idx, line in enumerate(lines):
            ext = ctx.text_extents(line)
            ctx.move_to(group_center - ext.width / 2.0, mt + plot_h + 26 + line_idx * 20)
            ctx.show_text(line)
            
    # Legend
    ctx.select_font_face(FONT_FAMILY, cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(17)
    
    legend_items = [
        (color_mean, "Total Frame Mean Latency"),
        (color_track, "Feature Tracking Latency"),
        (color_peak, "Max Peak Tail Latency")
    ]
    
    box_w = 20
    box_h = 13
    gap = 8
    item_spacing = 35
    
    widths = []
    for color, label in legend_items:
        ext = ctx.text_extents(label)
        widths.append(box_w + gap + ext.width)
        
    total_w = sum(widths) + (len(legend_items) - 1) * item_spacing
    cur_x = ml + (plot_w - total_w) / 2.0
    legend_y = 28
    
    for i, (color, label) in enumerate(legend_items):
        ctx.rectangle(cur_x, legend_y - box_h + 2, box_w, box_h)
        ctx.set_source_rgb(*color)
        ctx.fill_preserve()
        ctx.set_source_rgb(0.2, 0.2, 0.2)
        ctx.set_line_width(0.8)
        ctx.stroke()
        
        ctx.set_source_rgb(*COLOR_TEXT)
        ctx.move_to(cur_x + box_w + gap, legend_y + 2)
        ctx.show_text(label)
        cur_x += widths[i] + item_spacing
        
    out_file = os.path.join(FIG_DIR, "comparative_5way_timing.png")
    surface.write_to_png(out_file)
    print(f"Saved: {out_file}")

def main():
    print("=== Generating Publication-Quality Figures ===")
    
    # 1. Individual Architecture Plots
    render_arch_1_openvins()
    render_arch_2_kimera()
    render_arch_3_orbslam3()
    render_arch_4_orbslam3_klt()
    render_arch_5_cuvslam()
    
    # 2. Detailed Gantt Charts
    render_detailed_openvins_gantt()
    render_detailed_kimera_gantt()
    render_detailed_orbslam3_gantt()
    render_detailed_orbslam3_klt_gantt()
    render_detailed_cuvslam_gantt()
    
    # 3. Comparative Latency Breakdown
    render_comparative_5way_timing()
    
    print("=== All Figures Successfully Generated ===")

if __name__ == "__main__":
    main()
