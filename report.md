# Benchmark status report: divergences and anomalies

State of `results/` on 2026-11-04. All runs listed here were made with
`./run_benchmark.sh <algorithm> <dataset>` and evaluated with
`./scripts/plot_3d_trajectory.sh <algorithm> <dataset>`. The evaluation is evo APE on
translation with SE(3) alignment (no scale correction) and a 0.05 s timestamp tolerance.

## 1. Overview

| Dataset | Algorithm | APE RMSE | Matched poses | Status |
|---|---|---|---|---|
| MH_01_easy | ORB-SLAM3 | 0.045 m | 3640 / 3678 | OK |
| MH_01_easy | OpenVINS | 0.065 m | 2763 / 2784 | OK |
| MH_01_easy | Kimera-VIO | 0.194 m | 714 / 719 | OK, see anomaly 3.1 |
| MH_01_easy | cuVSLAM | 1.973 m | 3507 / 3528 | Baseline runs, but large scale error (section 2.2) |
| V1_03_difficult | ORB-SLAM3 | 0.025 m | 1995 / 2013 | OK (section 3.8) |
| V1_03_difficult | OpenVINS | 0.062 m | 1987 / 2005 | OK (section 3.8) |
| V1_03_difficult | Kimera-VIO | 0.103 m | 500 / 506 | OK (section 3.8) |
| V1_03_difficult | cuVSLAM | 2.651 m | 1957 / 1975 | **Failed**: trajectory does not follow GT (section 2.4) |
| corridor | ORB-SLAM3 | 0.034 m | 976 / 5925 | OK, see anomaly 3.3 |
| corridor | OpenVINS | 0.530 m | 912 / 5853 | OK, see anomaly 3.2 |
| corridor | Kimera-VIO | 201 284 m | 227 / 1382 | **Diverged** (section 2.1) |
| corridor | cuVSLAM | 1.5–4.2 m | ~600 / ~3900 | **Not reproducible**: frame drops (section 3.6) |
| Suedhoehe | ORB-SLAM3 | 24.5 m | 665 / 685 | **Failed**: tracking lost repeatedly (section 2.3) |
| Suedhoehe | others | — | — | Not run yet |

ORB-SLAM3-KLT has not been run yet: its source has no scoped timing instrumentation.

## 1a. How each algorithm reads the data

Two input routes are used, depending on what each algorithm supports natively.

| Algorithm | Input | Output for evaluation |
|---|---|---|
| OpenVINS | ROS 2 bag, played with `ros2 bag play` | `ov_estimate.txt` → TUM |
| cuVSLAM | ROS 2 bag, played with `ros2 bag play` | TUM directly (`cuvslam_save_trajectory.py`) |
| ORB-SLAM3 | EuRoC/ASL folder, read offline | `f_orbslam3.txt` → TUM |
| Kimera-VIO | EuRoC/ASL folder, read offline | `traj_vio.csv` → TUM |

**ROS 2 bag (OpenVINS, cuVSLAM).** `run_benchmark.sh` plays the bag in real time
(`--rate 1.0`) and the algorithm subscribes to the image and IMU topics like any ROS node.
For cuVSLAM, a small helper node also publishes the camera calibration (`camera_info`) and
the IMU in ROS axes. "Raw-image mode" for cuVSLAM means the images are passed on as recorded
(`/cam0/image_raw`, still lens-distorted, `rectified_images: False`); it does not mean the
bag is bypassed.

**EuRoC/ASL folder (ORB-SLAM3, Kimera-VIO).** Their example programs
(`stereo_inertial_euroc`, `stereoVIOEuroc`) cannot read ROS 2 bags. They read
`mav0/cam0/data/*.png`, `mav0/cam1/data/*.png`, `mav0/imu0/data.csv` and a
`timestamps.txt`.

| Dataset | Folder ORB-SLAM3 / Kimera read | Where it comes from |
|---|---|---|
| MH_01_easy | `datasets/MH_01_easy/mav0` | EuRoC's own download, already in this layout |
| V1_03_difficult | `datasets/V1_03_difficult/mav0` | EuRoC's own download, already in this layout |
| corridor | `datasets/tum_vi_corridor1/mav0` | converted from the ROS 2 bag by `scripts/rosbag_to_euroc.py` |
| Suedhoehe | `datasets/suedhoehe_asl/mav0` | converted from the ROS 2 bag by `scripts/rosbag_to_euroc.py` |

- The conversion copies the images as PNGs with their original header timestamps and
  writes the IMU samples to CSV. No values are changed, except that the 16-bit corridor
  images become 8-bit with `>> 8` (section 3.7).
- Only synchronised stereo pairs are listed, because Kimera pairs left/right images by row.

**TUM is the output format, not an input format.** TUM is one line per pose:
`time x y z qx qy qz qw`. After each run, the algorithm's own trajectory file is converted to
TUM so evo can compare it with the ground truth (also in TUM format).

## 2. Failed runs

### 2.1 Kimera-VIO on corridor: diverged

**What happened.** The estimated trajectory runs away within seconds:

- The estimated speed is about 200 m/s at t = 17 s; a person walking moves at about 1–1.5 m/s.
- Position after 4 minutes is about 2.5 km (z ≈ −2460 m). Total path length is about 441 km.
- APE RMSE is about 201 km. This number is meaningless and must not be reported as an
  accuracy value.

**Why.** The failure is in **initialisation**, not in the camera frontend:

1. `BackendParams.yaml` uses `autoInitialize: 1`. This initialises from the IMU and does not
   use ground truth, which is correct for a fair benchmark. Kimera's IMU initialisation
   assumes the sensor is **standing still**: `run.log` prints *"InitializationFromImu: assumes
   that the vehicle is stationary"*.
2. TUM-VI corridor1 is recorded **handheld**, so there is no stationary window at the start
   (or anywhere else). The start frame (`initial_k = 70`) was the calmest window available,
   but the sensor was still moving.
3. Because the sensor was moving, the rotation during that window was read as sensor error.
   The initial gyroscope bias came out as **bgx = −0.232 rad/s** (first row of
   `traj_vio.csv`). A real gyroscope bias is around 0.001–0.01 rad/s.
4. `ImuParams.yaml` sets `imu_bias_init_sigma: 1e-3`, which tells the optimiser to trust this
   initial bias strongly. The wrong bias is therefore **never corrected**. Integrating a wrong
   rotation rate tilts the estimated gravity direction, and part of gravity is integrated as
   acceleration. Velocity then grows without limit (≈ 200 m/s after 17 s).

**Evidence that the frontend works.** About 90 % of frames are tracked as VALID stereo
frames (`output_frontend_stats.csv`). Visual tracking is fine; the IMU state is wrong from the
first keyframe on.

**What is still valid.** The Gantt chart and `gantt_module_summary.csv` come from the real
measured timing (`kimera_scoped_timing.csv`), so the runtime profile is usable:

| Module | Count | Mean |
|---|---|---|
| VioFrontend | 5919 | 17.6 ms |
| VioBackend | 1382 | 23.3 ms |
| Mesher | 1382 | 4.2 ms |

These timings belong to a diverging estimator and may differ from a healthy run.

**Decision: reported as a failure case.** Kimera-VIO's static-IMU initialisation does not
work on handheld data without a stationary start. The parameters stay as they are (no tuning
of `imu_bias_init_sigma`, no ground-truth initialisation). In the results table this run is
listed as "diverged" with no APE value, and the timing profile is still reported.

### 2.2 cuVSLAM on MH_01_easy: baseline runs, but with a large scale error

**Setup (fair baseline).**
- Official NVIDIA Isaac ROS Visual SLAM 3.1.0 (apt package, unmodified).
- The repo's committed launch file `isaac_ros_visual_slam_euroc.launch.py` and helper
  `euroc_camera_info_pub.py`.
- cuVSLAM reads the **raw EuRoC images** (`rectified_images: False`) and handles the lens
  distortion itself, using the distortion model from `camera_info`. This is NVIDIA's
  supported mode.
- Run with `./run_benchmark.sh cuvslam MH_01_easy`; evaluated with `plot_3d_trajectory.sh`.
- An uncommitted attempt to rectify the images on the GPU first was reverted, because it
  stopped cuVSLAM from receiving images (0 poses). It is kept outside the repo for reference.
  Stale files from older runs were deleted before this run.

**Result.**
- APE RMSE **1.973 m** (mean 1.83 m, max 3.69 m) on 3507 of 3528 poses.
- With Sim(3) alignment (scale allowed) the scale factor is **0.766**: cuVSLAM's trajectory
  is about **30 % too large**. Even after the scale correction the APE is still 1.55 m.
- In `cuvslam_3d_xyz.png` the shape of the motion matches the ground truth, but every
  movement is amplified, and an offset builds up.
- 64 gaps longer than one frame in 3528 poses. Few frames were dropped, unlike on corridor.

**Run-to-run variation.**

| Run | Setup | APE RMSE |
|---|---|---|
| Earlier (09:26) | same baseline | 1.31 m |
| This run (14:16) | same baseline | 1.97 m |
| Repo's old modified build | raw images | 1.57 m |

The same setup gives 1.3–2.0 m, so a single number should be reported together with this
spread (or as the mean of several runs).

**Why the error is so large.**
- EuRoC images are strongly distorted (radial-tangential, k1 ≈ −0.28).
- The following were checked and found correct: base→camera TFs, intrinsics, distortion
  coefficients and their order, and the IMU frame and noise parameters.
- In a manual experiment outside `run_benchmark.sh`, the same images were rectified
  beforehand with OpenCV, and the error dropped to **0.063 m**. So cuVSLAM's internal
  handling of strong distortion on raw images is what causes the scale error, not our
  calibration.

**For the thesis.**
- Report 1.3–2.0 m as cuVSLAM's result in its standard raw-image mode, with the explanation
  above.
- The rectified-input variant (0.063 m) is a different configuration. It may be reported
  only once it is reproduced through `run_benchmark.sh`, and must be labelled as a
  preprocessing variant.
- No Gantt chart: cuVSLAM is closed source (section 3.6).

### 2.3 ORB-SLAM3 on Suedhoehe: tracking lost repeatedly

Run with `./run_benchmark.sh orbslam3 suedhoehe` and evaluated against the GNSS reference
with `./scripts/plot_3d_trajectory.sh orbslam3 suedhoehe`.

**Calibration used.** The bag contains no `camera_info`, so no factory calibration was
recorded. `workspace/orbslam3_ws/suedhoehe_stereo_inertial.yaml` was rewritten for the
D435i. The old file held values for a different camera (D455 colour: 95 mm baseline, lens
distortion, 400 Hz IMU).

| Parameter | Value | Source |
|---|---|---|
| Camera model | `Rectified` (no distortion) | the topics are `image_rect_raw`, already rectified by the camera |
| Resolution / rate | 848×480, 30 Hz; IMU 200 Hz | read from the bag |
| Baseline b | 0.0499585 m | ORB-SLAM3's official `RealSense_D435i.yaml` |
| fx = fy | 421.35 px | **measured from this bag** (see below) |
| cx, cy | 424, 240 | image centre (nominal) |
| IMU→camera, IMU noise | identity rotation, (−5, −5, 11.7) mm; noise as in the official file | ORB-SLAM3's official `RealSense_D435i.yaml`; the bag's IMU is in `camera_imu_optical_frame` (gravity reads −9.75 m/s² on y = up in optical axes, as expected) |

- **fx check:** the RealSense depth image is computed by the camera with its factory
  calibration, so depth × disparity = fx · b.
- Stereo-matching infra1/infra2 on 10 frames spread over the run gives
  **fx · b = 21.05 px·m** (21.00–21.08 on well-textured frames), so fx = 421.35 px.
- Independent check: ORB-SLAM3's 640×480 value (382.6 px) scaled to the 848×480 mode gives
  about 422 px.

**Ground truth.** GNSS from `/fmu/out/vehicle_gps_position`, made by
`scripts/make_suedhoehe_gt.py`:
- 1173 fixes, all 3D fixes;
- reported horizontal accuracy 0.53 m on average;
- position only, starting 24 s into the bag;
- 408 m path over 117 s, i.e. about 3.5 m/s.

The old `gps_trajectory.txt` repeated the last GNSS position at every camera timestamp and
was all zeros for its first 729 rows. The evaluation now uses `gt_gnss_tum.txt`.

**What happened.**
1. First ~26 s: the camera hardly moves, and ORB-SLAM3 waits ("not enough acceleration").
2. ORB-SLAM3 then initialises the map and the IMU successfully (VIBA 1 and 2 finish).
3. Tracking is then lost ("Fail to track local map", 615 times in total). The map is reset
   13 times, and each new map survives only about 150 frames (5 s).
4. ORB-SLAM3 saves the trajectory of its largest map: 685 poses (22.8 s).
   - Over that time it estimates **221 m (≈ 10 m/s)**; GNSS shows ≈ 3.5 m/s.
   - The trajectory curves away (see `orbslam3_3d_trajectories.png`). This is IMU dead
     reckoning after vision was lost, not a tracked trajectory.
   - **APE 24.5 m** on 665 poses. Not a valid accuracy result.

**Why.**
- **The scene has almost no usable texture** (sample frames: snow-covered field, overcast
  sky, distant tree line):
  - the lower half of the image is uniform snow;
  - most ORB features are on trees tens of metres away.
- **The baseline is short.** With 50 mm baseline and fx = 421 px, disparity at 20 m is about
  1 px. Distant points give almost no depth, so ORB-SLAM3 has very few "close" stereo points
  (ThDepth = 40·b = 2 m) to fix scale and translation.
- **Fast motion.** About 3.5 m/s at 30 Hz is about 12 cm between frames, on a mostly
  featureless foreground.
- **Calibration uncertainty** (nominal cx, cy, IMU extrinsics) may add to this. However,
  ORB-SLAM3 does initialise with these values, and the measured fx · b matches the camera.
  The failure pattern (lost after a few seconds, every time) points to the scene, not the
  calibration.

**What is still valid.** The per-module timing (Gantt chart) was measured over all 4244
frames: tracking total_frame mean 31.5 ms, ORB extraction 18.2 ms.

**For the thesis:** report Suedhoehe as a failure case for ORB-SLAM3 (low-texture snow,
short baseline, nominal calibration), not as an accuracy number.

### 2.4 cuVSLAM on V1_03_difficult: trajectory does not follow the ground truth

**Setup.**
- Same fair baseline as MH_01_easy (section 2.2): official package, the EuRoC launch file
  (same sensor rig and calibration), raw images, no rectification.
- Run with `./run_benchmark.sh cuvslam V1_03_difficult`.
- `run_benchmark.sh`, `plot_3d_trajectory.sh` and `cuvslam_save_trajectory.py` were
  extended for this dataset. The saver now also converts the orientation to the EuRoC body
  frame for V1_03.

**Result.**
- APE RMSE **2.651 m** (mean 2.48 m, max 4.94 m) on 1957 of 1975 poses.
- With Sim(3) alignment evo picks a scale of **0.198**, which leaves 1.47 m. A scale that
  small is not a real scale error: the best fit simply shrinks a trajectory that does not
  match.
- In `cuvslam_3d_xyz.png`:
  - motion is exaggerated in x and y from the start;
  - z drifts by about 3 m between 55 s and 90 s;
  - there are large swings where the ground truth moves gently.
- Few frames were dropped (58 gaps in 1975 poses), so input loss is not the cause.

**Why.**
- This is the same problem as on MH_01_easy, made worse by V1_03's fast, aggressive motion
  and motion blur.
- cuVSLAM's handling of EuRoC's strongly distorted raw images already produced a 30 % scale
  error on the easy sequence. On fast motion the visual constraints degrade further, and the
  estimate stops following the true motion.
- OpenVINS gets 0.062 m on the same bag, so the data itself is fine.

**For the thesis:** report it as a failure case of cuVSLAM in raw-image mode on fast
EuRoC motion.

## 3. Anomalies in valid runs

### 3.1 Kimera-VIO on MH_01_easy: higher error, late start, keyframe-only output

- **APE 0.194 m** is about 3–4× ORB-SLAM3 and OpenVINS. Published Kimera results on MH_01 are lower,
  but the upstream EuRoC parameters initialise from ground truth (`autoInitialize: 0`). Here Kimera initialises itself from the IMU, which is fairer but less
  accurate.
- **Late start.** Self-initialisation needs the sensor to stand still. Starting at frame 50
  gave an accelerometer bias of 3.35 m/s² and a smoother failure. The run therefore starts at
  `initial_k = 460`, inside the stationary window at about 22–44 s. The first ~23 s of the
  sequence are not estimated.
- **Only keyframes are output** (719 poses vs. 3682 images). `traj_vio.csv` contains one pose
  per keyframe, so APE is computed on fewer, sparser poses than for the other algorithms.
- Frontend 32.8 ms mean / backend 90.3 ms mean (measured).

### 3.2 OpenVINS on corridor: APE 0.53 m is drift, not local error

- The TUM-VI corridor ground truth exists only where the motion-capture system sees the
  sensor: the **start and end of the run** in the mocap room. Only 912 of 5853 poses (~16 %)
  match a ground-truth timestamp. Everything in the corridors in between is not evaluated.
- With SE(3) alignment, start and end are aligned together, so the APE mostly measures
  **accumulated drift between leaving and re-entering the room**.
- Split by segment:
  - start segment: 0.019 m APE (locally very accurate);
  - end-point drift: 1.40 m over a 299 m path, i.e. 0.47 %.
- This is normal for a pure odometry method (OpenVINS has no loop closure). It should be
  described as drift, not as "0.53 m accuracy".
- Max error 2.39 m.
- `total_frame` 14.4 ms mean (measured).

### 3.3 ORB-SLAM3 on corridor: loop closure makes it not comparable to pure odometry

- APE 0.034 m and end drift 0.066 m. These are this low because ORB-SLAM3 **closed the loop**
  when returning to the mocap room: there are 2 loop corrections in the timing log, about
  930 ms each.
- OpenVINS, Kimera (as configured) and cuVSLAM odometry do not correct drift this way.
- The comparison with OpenVINS (0.53 m) is therefore **SLAM vs. odometry**, and the thesis
  should say so explicitly.
- The two loop corrections are visible as about 1 s spikes in the loop-closing thread. They
  run in the background thread and do not block tracking.

### 3.4 OpenVINS on MH_01_easy: first ~900 frames without pose

- `total_frame` was timed on 3682 frames, but there are only 2784 state updates and poses.
  OpenVINS waits until its IMU initialiser detects enough motion, so the first ~900 frames
  (about 45 s at 20 Hz) produce no pose.
- This is expected behaviour. Report it as "time to initialise" rather than as missing data.

### 3.6 cuVSLAM on corridor: runs, but the setup has two known errors

Run with `./run_benchmark.sh cuvslam corridor` using the official NVIDIA package 3.1.0 and
the existing launch file `isaac_ros_visual_slam_corridor.launch.py`, unchanged.

| Measure | cuVSLAM | OpenVINS | ORB-SLAM3 |
|---|---|---|---|
| APE RMSE (SE(3), whole run) | 1.542 m | 0.530 m | 0.034 m |
| Start segment only (aligned on start) | 0.125 m | 0.019 m | 0.011 m |
| End-segment drift | 3.40 m (1.15 %) | 1.40 m (0.47 %) | 0.065 m |
| Poses / camera frames | 3881 / 5990 | 5853 / 5990 | 5925 / 5990 |

The overall shape of the trajectory is right (path length 296.5 m vs. 299 m for OpenVINS).
However, the end segment is about **3.2 m too high (z)**, and even the start segment is 6×
worse than OpenVINS. Two causes were found:

1. **Wrong camera–IMU transform (bug in the launch file).**
   - The `base_link → cam0/cam1` TFs use TUM-VI's **T_cam_imu** (the IMU pose in camera
     coordinates). A TF from base (= IMU) to camera must be the inverse, **T_imu_cam**.
   - cam0 translation is published as (0.047, −0.047, −0.068) m; the correct value is
     (0.046, −0.071, −0.045) m. The rotation is nearly 180°, so only the sign of w differs.
   - A wrong lever arm between camera and IMU produces exactly this kind of error: a steady
     drift, here mostly vertical, in a visual-inertial filter.
   - (The same bug was already listed in the first audit.)
2. **Dropped frames (35 %).**
   - There are only 3881 poses for 5990 stereo frames, and 1634 gaps longer than one frame
     (up to 0.35 s).
   - The images are mono16 and cuVSLAM needs mono8. The conversion is done by a Python relay
     node (`corridor_camera_info_pub.py`) inside a container capped at 2 CPUs, and it cannot
     keep up with real-time playback.
   - cuVSLAM's own warning threshold (34 ms) assumes 30 fps. At 20 Hz a 50 ms gap is normal;
     the 100–350 ms gaps are real drops.

**No Gantt chart can be reported for cuVSLAM.** The cuVSLAM library is closed source
(NVIDIA ships only a binary). Its internal modules cannot be instrumented the way OpenVINS,
ORB-SLAM3 and Kimera-VIO were, so a per-module timeline cannot be measured. Drawing one would
mean inventing the numbers, which is exactly what the old `generate_cuvslam_timing.py` did.
Only externally measurable quantities can be reported for cuVSLAM: poses per second, dropped
frames, end-to-end latency, and GPU/CPU usage.

**Follow-up runs (2026-11-04).**
- The TF in `isaac_ros_visual_slam_corridor.launch.py` was corrected to T_imu_cam. This is
  the same convention the EuRoC launch file already uses, and the one the node expects:
  `GetFrameTransform(base, camera)` looks up the camera pose in the base frame.
- Three runs, all through `run_benchmark.sh`:

| Run | TF | CPUs | Poses | Frame gaps | APE RMSE | Start segment | End drift |
|---|---|---|---|---|---|---|---|
| 1 | T_cam_imu (old, wrong) | 2 | 3881 | 1634 | 1.54 m | 0.13 m | 3.4 m |
| 2 | T_imu_cam (fixed) | 2 | 3873 | 1876 | 4.15 m | 0.59 m | 9.0 m |
| 3 | T_imu_cam (fixed) | 4 | 3971 | 1614 | 2.56 m | 2.03 m | 4.7 m |

- **Conclusion: the dropped frames dominate, not the TF.** With the same setup, runs 2 and 3
  differ by a factor of 1.6 in APE, and the start-segment error ranges from 0.13 m to 2 m.
  Which frames are lost changes from run to run, so the result is not reproducible.
- Doubling the CPUs did not reduce the drops (about 1600 gaps either way). The relay is
  therefore not simply short of CPU. Where the frames are lost (relay QoS, stereo pair sync,
  or cuVSLAM processing time on the RTX 3050) still has to be measured.
- **16-bit input is not possible.** The official node converts the image encoding in
  `cuvslam_ros_conversion.cpp:222-230` and accepts only `mono8` and `rgb8`. Every other
  encoding, mono16 included, throws "Received unknown image encoding". The 16→8-bit
  conversion (>> 8, the same as for ORB-SLAM3 and Kimera) is required; the only choice is
  where it happens.

**Fair to report now?** No. First remove the frame drops, for example by converting the bag
to mono8 once offline so that no relay is needed, and confirm that repeated runs give the
same result.

### 3.7 16-bit images (TUM-VI corridor) are converted to 8-bit for every algorithm

The TUM-VI `512_16` export stores camera images as **16-bit grey (mono16)**. None of the
five algorithms works on 16-bit images:

| Algorithm | Where 16→8 bit happens | Method |
|---|---|---|
| OpenVINS | inside OpenVINS: `cv_bridge::toCvShare(msg, MONO8)` (`ROS2Visualizer.cpp:551`) | cv_bridge depth conversion |
| ORB-SLAM3 / KLT | `scripts/rosbag_to_euroc.py` when writing the PNG folder | `>> 8` |
| Kimera-VIO | same PNG folder as ORB-SLAM3 | `>> 8` |
| cuVSLAM | Python relay `corridor_camera_info_pub.py` during playback | `>> 8` |

- **All algorithms see identical 8-bit pixels.** cv_bridge's mono16 → mono8 conversion was
  checked against `>> 8`. For the inputs 0, 256, 25600 and 65535 both give 0, 1, 100 and
  255, so OpenVINS gets the same image as the others.
- **`>> 8` keeps the 8 most significant bits** (value / 256). No contrast stretching or
  normalisation is applied. The 8 dropped low bits are mostly sensor noise, but some
  dark-region detail is lost. This applies equally to all algorithms, so the comparison
  stays fair.
- **cuVSLAM cannot be given 16-bit input at all.** The official Isaac ROS node
  (`cuvslam_ros_conversion.cpp:222-230`) maps only `mono8` and `rgb8` to the cuVSLAM
  library. Any other encoding, including mono16, throws "Received unknown image encoding".
  The library API (`CUVSLAM_ImageEncoding`) also only defines MONO8 and RGB8.
- **Side effect for cuVSLAM:** the other algorithms convert inside their own process or
  offline. cuVSLAM is the only one that needs an extra ROS node between bag and algorithm,
  and that node is where the frame-drop problem of section 3.6 can arise. Converting the bag
  to mono8 once offline (same `>> 8`) would give cuVSLAM the same pixels without the extra
  node.
- EuRoC MH_01_easy and the Suedhoehe RealSense infrared images are already 8-bit, so no
  conversion happens there.

### 3.8 OpenVINS on EuRoC V1_03_difficult: new dataset, valid

Run with `./run_benchmark.sh openvins V1_03_difficult` and evaluated with
`./scripts/plot_3d_trajectory.sh openvins V1_03_difficult`.

- **Runner fixes needed first.**
  - `run_benchmark.sh` silently turned any unknown dataset name into `MH_01_easy`, so its
    V1_03 branch was unreachable. `V1_03_difficult` is now recognised.
  - The bag path pointed at the folder with the old ROS 1 `.bag`; it now points at
    `V1_03_difficult/V1_03_difficult_ros2`.
  - `plot_3d_trajectory.sh` had no V1_03 case; added, with GT `datasets/V1_03_difficult/gt_tum.txt`.
- **Result.** APE RMSE **0.062 m** (mean 0.056 m, max 0.142 m) on 1987 of 2005 poses. The
  trajectory follows the Vicon ground truth closely through the fast, aggressive motion
  (`openvins_3d_trajectories.png`).
- **Pose count.** 2005 poses for 2149 frames: the first ~7 s are used for IMU
  initialisation, as on MH_01_easy.
- **Measured timing.** total_frame mean 16.1 ms (p95 26.6 ms); feature tracking 5.8 ms.
- **ORB-SLAM3** (`./run_benchmark.sh orbslam3 V1_03_difficult`):
  - It reads the EuRoC folder `datasets/V1_03_difficult/mav0` with the same EuRoC config as
    MH_01_easy (same sensor rig).
  - APE RMSE **0.025 m** (mean 0.023 m, max 0.103 m) on 1995 of 2013 poses.
  - One map for the whole run (123 keyframes): no tracking loss, no map reset and no loop
    correction. The accuracy therefore comes from tracking and local BA alone.
  - Measured timing: tracking 34.5 ms per frame (p95 68.8 ms), local BA 173 ms per keyframe.
- **Kimera-VIO** (`./run_benchmark.sh kimera V1_03_difficult`):
  - It reads the EuRoC folder with the same `euroc_kimera_params` as MH_01_easy and
    self-initialises from the IMU (`autoInitialize: 1`, no ground truth).
  - **Start frame.** V1_03 is stationary only for its first ~3 s: the accelerometer
    standard deviation is 0.024–0.030 m/s² in seconds 0–2, 0.22 m/s² at 3 s and about
    2 m/s² in flight. The run therefore starts at `initial_k = 20` (t ≈ 1 s).
  - The initial gyro bias estimate is realistic: (−0.002, 0.020, 0.078) rad/s, matching the
    ~0.08 rad/s the gyro reads at rest. Maximum estimated speed is 2.0 m/s, so there is no
    divergence (compare corridor, section 2.1).
  - APE RMSE **0.103 m** (mean 0.099 m, max 0.175 m) on 500 of 506 poses. Only keyframe
    poses are written (section 3.1).
  - Measured timing: frontend 33.0 ms mean, backend 51.3 ms, mesher 36.1 ms.
  - **Dataset header fix.** The first run aborted while parsing
    `mav0/state_groundtruth_estimate0/sensor.yaml`. Kimera reads it with OpenCV, which needs
    a `%YAML:1.0` first line, and EuRoC's original file has none. The MH_01_easy copy already
    had this line added (Oct 22). The same single line was added to the V1_03 copy; no data
    was changed, and Kimera does not use the ground truth for initialisation.
- V1_03 has the fastest motion and strongest motion blur of the EuRoC Vicon-room sequences,
  so it complements MH_01_easy (easy) well.

### 3.5 General points for the thesis

- **Different number of output poses per algorithm.** Values range from keyframes only
  (Kimera) to every frame (ORB-SLAM3, OpenVINS), so APE is computed on different sample sets.
  Mention this next to the results table.
- **Timing comes from different instrumentation points.** Each algorithm's modules are
  defined by its own code:
  - OpenVINS: built-in timing;
  - ORB-SLAM3: its `REGISTER_TIMES` points;
  - Kimera: `PipelineModule::spin`.

  Module names are therefore not one-to-one comparable across algorithms; `total_frame` /
  tracking time is the fairest common measure.
- **No fabricated data.** Gantt charts are drawn by `scripts/plot_gantt.py` only from the
  `*_scoped_timing.csv` files written during each run. The old hardcoded generator
  (`scripts/generate_publication_plots.py`) has been deleted; an archived copy is in
  `temporary_results/`.

## 4. Open decisions

1. ~~Kimera corridor~~: decided, reported as a failure case (section 2.1).
2. cuVSLAM: which rectification route to use (section 2.2)?
3. Remaining runs: ORB-SLAM3-KLT (needs timing instrumentation); OpenVINS, Kimera and cuVSLAM
   on Suedhoehe (they need the same D435i calibration).
4. ~~More datasets~~: done, EuRoC V1_03_difficult has been run for all four algorithms (section 3.8).
