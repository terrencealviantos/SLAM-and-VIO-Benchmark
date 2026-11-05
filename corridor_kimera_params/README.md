# Kimera-VIO parameters for TUM-VI corridor1

Used by `run_benchmark.sh kimera corridor` with the latest Kimera-VIO image
(`workspace/kimera_ws/Dockerfile`, Kimera-VIO @ ce8c59b), passed as `--params_folder_path`.

Start: the official `params/Euroc` of MIT-SPARK/Kimera-VIO @ ce8c59b (same as
`euroc_kimera_params/`, incl. `autoInitialize: 1`). Only the sensor description differs:

- `LeftCameraParams.yaml`, `RightCameraParams.yaml`: TUM-VI 512x512 fisheye (equidistant)
  intrinsics/distortion and `T_BS` = camera pose in the IMU frame (inverse of Kalibr T_cam_imu),
  from the dataset calibration (identical to OpenVINS `config/tum_vi`).
- `ImuParams.yaml`: TUM-VI IMU noise densities and random walks.
- `FrontendParams.yaml`: `nominalBaseline: 0.101` (TUM-VI stereo baseline).
