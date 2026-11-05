# Kimera-VIO parameters for EuRoC MH_01_easy

Used by `run_benchmark.sh kimera MH_01_easy` with the latest Kimera-VIO image
(`workspace/kimera_ws/Dockerfile`, Kimera-VIO @ ce8c59b), passed as `--params_folder_path`.

These are the official `params/Euroc` files of MIT-SPARK/Kimera-VIO @ ce8c59b. Only one line
differs from upstream:

- `BackendParams.yaml`: `autoInitialize: 1` (upstream 0 initialises the state from the
  ground truth, an advantage the other benchmarked algorithms do not get).
