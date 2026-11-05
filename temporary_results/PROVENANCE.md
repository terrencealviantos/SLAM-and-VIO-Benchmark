# Provenance of archived results (snapshot 2026-11-03, before the integrity fix)

This folder freezes `results/`, `figures/` and `gantt_charts/` exactly as they were on
`main` at commit `d0ab286` (plus the untracked Kimera outputs), together with the
scripts that produced the synthetic/hardcoded material. **Nothing in here may be cited
as a measured result.** Re-generated, measured results live in `results/` again.

Status legend: **real** = measured output of a run, still consistent with its inputs;
**stale** = real once, but no longer matches the current trajectory file or was computed
on a broken run; **hardcoded** = numbers typed into a plotting script; **fabricated** =
numbers drawn at random or invented and presented as measurements.

## Timing / profiling figures

| Artifact | Producer | Status |
|---|---|---|
| `figures/4_cuvslam_gantt_chart.png`, `gantt_charts/4_cuvslam_gantt_chart.{png,svg}`, `figures/arch_5_cuvslam.png` | `scratch_generators_from_history/generate_cuvslam_timing.py` (`random.gauss`, seed 42) → `plot_cuvslam_timing.py`; later redrawn by `generate_publication_plots.py` with the gauss means | **fabricated** |
| `figures/1_openvins_gantt_chart.png`, `2_kimera_gantt_chart.png`, `3_orbslam3_gantt_chart.png`, `5_orbslam3_klt_gantt_chart.png`, `figures/arch_*.png`, `figures/comparative_5way_timing.png` | `generate_publication_plots.py` (`draw_bar` constants, reads no file) | **hardcoded** (OpenVINS/ORB-SLAM3 constants were copied from an old real log; Kimera backend, KLT and cuVSLAM bars have no source) |
| `gantt_charts/3_orbslam3_gantt_chart.png` | `plot_timing.py` (real `track_stereo` split by fixed fractions; Local Mapping / Loop Closing invented) | **hardcoded** |
| `gantt_charts/2_kimera_*gantt_chart.png` | `plot_kimera_timing.py` (frontend real, backend invented — backend timing CSV was all zeros) | **hardcoded** |
| `gantt_charts/multithread_architecture_comparison.*`, `figures/multithread_architecture_comparison.png` | `plot_multithread_gantt.py` | **hardcoded** |
| `figures/multi_frame_gantt.png` | no script exists; no KLT timing log ever existed | **unknown / unsupported** |
| `results/*/*/gantt_chart.png` (16 files) | `run_benchmark.sh save_gantt_chart` copied the figures above into every dataset folder (byte-identical per algorithm) | **hardcoded, not dataset-specific** |
| `results/euroc/openvins/ov_scoped_timing.csv`, `ov_msckf_timing.txt`, `results/suedhoehe/openvins/ov_scoped_timing.csv` | OpenVINS native timing | real |
| `results/suedhoehe/kimera/output_frontend_stats.csv` | Kimera logger | real (broken run) |

## Trajectory accuracy

| Dataset / algo | Status | Reason |
|---|---|---|
| euroc/orbslam3, corridor/orbslam3 | real | plausible, consistent |
| euroc/openvins, corridor/openvins | real (translation only) | `convert_openvins_to_tum.py` read the JPL xyzw quaternion as wxyz, so orientations/RPE are wrong |
| corridor/orbslam3_klt | real, wrong alignment | evaluated with Sim3 although stereo-inertial |
| euroc/orbslam3_klt | not comparable | ran **monocular** `mono_euroc`, Sim3 scale 4.78 |
| euroc/kimera | not comparable | initialized from ground truth (stock params, `autoInitialize: 0`) |
| euroc/cuvslam, euroc/cuvslamPURESTEREO | invalid | VIO worse than pure stereo; spikes; PURESTEREO launch file not in repo, stats header mislabelled |
| corridor/cuvslam, corridor/cuvslam_purestereo | invalid | base→cam TF inverted (T_cam_imu used), tracking resets |
| corridor/kimera | no output | crashed at frame 2 |
| suedhoehe/* (all) | invalid | calibration copied from a public D455 colour camera (recording camera is a D435i), IMU rate 400 vs 200 Hz, inverted extrinsics; stats for openvins/orbslam3 stale vs trajectory files |
| `figures/trajectories_comparison_*`, `evo_bar_chart_*`, `*_ape_map/raw.png` | stale | evo output from the first-commit trajectories (ORB-SLAM3 had 74 poses) |

Ground truth caveats: corridor `gt_tum.txt` (from the bag's /vrpn_client/raw_transform) is
identical to the official TUM-VI mocap0 ground truth (IMU pose) but covers only ~17 % of the
sequence (mocap room at start and end); suedhoehe `gps_trajectory.txt` is GPS zero-order-held onto camera
stamps with identity orientation and no generating script.

## Numbers in `main.tex` that came from the above
EuRoC ATE table (old l.751-755), cuVSLAM stage table and all cuVSLAM ms/FPS figures,
P95/FPS/CPU-core rows, Kimera backend 18.5 ms, ORB-SLAM3 extraction/BA split, all KLT timing
and keyframe-reduction claims, the TUM fr1_xyz comparison (dataset never present), RPE claims.
These were replaced by `\TBD{}` in `main.tex`.
