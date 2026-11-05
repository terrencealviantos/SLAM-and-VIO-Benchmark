#!/usr/bin/env bash
# ==============================================================================
# Visual SLAM & VIO All-in-One Master Benchmark Suite
# ==============================================================================
# Unified single entrypoint supporting all 5 algorithms:
#   1. cuvslam      : NVIDIA Isaac ROS GPU-Accelerated Visual-Inertial SLAM
#   2. openvins     : MSCKF Filter Sliding-Window Visual-Inertial Odometry
#   3. orbslam3     : ORB-SLAM3 Baseline Stereo-Inertial Keyframe BA
#   4. orbslam3_klt : ORB-SLAM3 Hybrid Dual-Rate Optical Flow SLAM
#   5. kimera       : Kimera-VIO GTSAM Smoothing & Mesh SLAM
#   6. all          : Run all algorithms sequentially and generate comparison
#
# Usage:
#   ./run_benchmark.sh [algorithm] [dataset] [options]
#
# Examples:
#   ./run_benchmark.sh cuvslam suedhoehe --gui
#   ./run_benchmark.sh openvins suedhoehe --gui
#   ./run_benchmark.sh orbslam3 MH_01_easy --gui
#   ./run_benchmark.sh orbslam3_klt MH_01_easy --gui
#   ./run_benchmark.sh kimera suedhoehe --gui
#   ./run_benchmark.sh all all
#   ./run_benchmark.sh --evaluate
# ==============================================================================

set -e

REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")" && pwd)"
SCRIPTS_DIR="${REPO_ROOT}/scripts"
# Latest official Kimera-VIO, built from workspace/kimera_ws/Dockerfile (MH_01_easy path)
KIMERA_IMAGE="kimera-latest:ce8c59b"
RVIZ_DIR="${SCRIPTS_DIR}/rviz"

# ------------------------------------------------------------------------------
# Terminal Title & Multi-Window Launcher
# ------------------------------------------------------------------------------
launch_terminal() {
    local title="$1"
    local cmd="$2"

    if command -v konsole &> /dev/null; then
        konsole --new-tab -p tabtitle="$title" -e bash -c "$cmd; echo; echo '[Press Enter to close window]'; read" &
    elif command -v gnome-terminal &> /dev/null; then
        gnome-terminal --title="$title" -- bash -c "$cmd; echo; echo '[Press Enter to close window]'; read" &
    elif command -v xfce4-terminal &> /dev/null; then
        xfce4-terminal --title="$title" -e "bash -c \"$cmd; echo; echo '[Press Enter to close window]'; read\"" &
    elif command -v xterm &> /dev/null; then
        xterm -title "$title" -geometry 120x35 -e bash -c "$cmd; echo; echo '[Press Enter to close window]'; read" &
    else
        echo "[WARN] No graphical terminal emulator found. Running in current shell."
        bash -c "$cmd"
    fi
}

# ------------------------------------------------------------------------------
# Usage Help
# ------------------------------------------------------------------------------
show_help() {
    echo "=============================================================================="
    echo "               Visual SLAM & VIO Unified Benchmark Runner                     "
    echo "=============================================================================="
    echo "Usage: ./run_benchmark.sh [algorithm] [dataset] [flags]"
    echo ""
    echo "Supported Algorithms:"
    echo "  cuvslam        - NVIDIA Isaac ROS GPU-Accelerated cuVSLAM"
    echo "  openvins       - OpenVINS MSCKF Filter-Based VIO"
    echo "  orbslam3       - ORB-SLAM3 Stereo-Inertial Baseline (Keyframe BA)"
    echo "  orbslam3_klt   - ORB-SLAM3 Hybrid Dual-Rate Optical Flow SLAM"
    echo "  kimera         - Kimera-VIO GTSAM Factor Graph & 3D Mesh SLAM"
    echo "  all            - Run all algorithms sequentially across datasets"
    echo ""
    echo "Supported Datasets:"
    echo "  suedhoehe      - Outdoor winter snow RealSense D435i dataset (GPS GT)"
    echo "  MH_01_easy     - EuRoC MAV Machine Hall sequence MH_01_easy (Vicon GT)"
    echo "  corridor       - TUM-VI indoor corridor sequence corridor1 (MoCap GT)"
    echo "  all            - Benchmark across all available datasets"
    echo ""
    echo "Options & Flags:"
    echo "  --gui, -g      - Open live GUI visualizer (RViz2 / Pangolin) + multi-terminals"
    echo "  --evaluate, -e - Evaluate trajectories against ground truth using evo"
    echo "  --cpus <N>     - Max CPU cores allocated to container (default: 2)"
    echo "  --memory <M>   - Max RAM allocated to container (default: 3g)"
    echo "  --help, -h     - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_benchmark.sh cuvslam suedhoehe --gui"
    echo "  ./run_benchmark.sh openvins corridor --gui"
    echo "  ./run_benchmark.sh kimera suedhoehe --gui"
    echo "  ./run_benchmark.sh orbslam3_klt MH_01_easy --gui"
    echo "  ./run_benchmark.sh all corridor"
    echo "  ./run_benchmark.sh all all"
    echo "  ./run_benchmark.sh --evaluate"
    echo "=============================================================================="
}

# Defaults
ALGORITHM=""
DATASET=""
ENABLE_GUI=false
DO_EVALUATE=false
CPUS="2"
MEMORY="3g"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        cuvslam|openvins|orbslam3|orbslam3_klt|kimera|all)
            if [ -z "$ALGORITHM" ]; then
                ALGORITHM="$1"
            elif [ -z "$DATASET" ]; then
                DATASET="$1"
            fi
            shift
            ;;
        suedhoehe|schnee|MH_01_easy|mh01|MH01|V1_03_difficult|v103|V103|corridor|tum_vi|tumvi|corridor1)
            DATASET="$1"
            shift
            ;;
        --gui|--view|-g|--terminals)
            ENABLE_GUI=true
            shift
            ;;
        --evaluate|-e)
            DO_EVALUATE=true
            shift
            ;;
        --cpus)
            CPUS="$2"
            shift 2
            ;;
        --memory|-m)
            MEMORY="$2"
            shift 2
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            if [ -z "$ALGORITHM" ]; then
                ALGORITHM="$1"
            elif [ -z "$DATASET" ]; then
                DATASET="$1"
            fi
            shift
            ;;
    esac
done

# Handle evaluation only
if [ "$DO_EVALUATE" = true ] && [ -z "$ALGORITHM" ]; then
    echo "=========================================================="
    echo " Evaluating All Generated Trajectories with evo..."
    echo "=========================================================="
    docker run --rm \
      -v "${REPO_ROOT}":/repo \
      -v "${REPO_ROOT}/workspace/.python_deps":/deps \
      slam-base:latest \
      bash -c "export PYTHONPATH=/deps && python3 /repo/scripts/eval_all_trajectories.py"
    echo "[✔] Evaluation completed."
    exit 0
fi

# Normalize algorithm & dataset names
case "$DATASET" in
    suedhoehe*|suehoehe*|suedhohe*|snow*|d435*|schnee*)
        DATASET="suedhoehe"
        ;;
    mh01*|MH01*|MH_01*)
        DATASET="MH_01_easy"
        ;;
    v1_03*|V1_03*|v103*|V103*)
        DATASET="V1_03_difficult"
        ;;
    corridor*|tum_vi*|tumvi*)
        DATASET="corridor"
        ;;
    all)
        DATASET="all"
        ;;
    *)
        DATASET="MH_01_easy"
        ;;
esac

# Fallback defaults
ALGORITHM="${ALGORITHM:-cuvslam}"
DATASET="${DATASET:-MH_01_easy}"

# Allow X11 for Docker GUI
xhost +local:root 2>/dev/null || xhost + 2>/dev/null || true

# ------------------------------------------------------------------------------
# Helper: Gantt chart of this run, drawn from the run's own timing log
# ------------------------------------------------------------------------------
# scripts/plot_gantt.py reads the measured per-module start/end times the algorithm
# wrote during this run (OpenVINS: ov_scoped_timing.csv). If a run has no such log,
# no chart is produced -- a fixed image is never copied in its place.
save_gantt_chart() {
    local algo="$1"
    local ds="$2"

    case "$ds" in
        corridor|tum_vi|tumvi|corridor1)          ds="corridor" ;;
        suedhoehe|schnee|snow|suedhoehe_gps_schnee_02) ds="suedhoehe" ;;
    esac

    local dest_dir="${REPO_ROOT}/results/${ds}/${algo}"
    if [ ! -d "$dest_dir" ]; then
        echo "[WARN] ${dest_dir} does not exist; no Gantt chart generated."
        return 0
    fi

    docker run --rm --entrypoint "" --user "$(id -u):$(id -g)" -e HOME=/tmp \
      -v "${dest_dir}":/run_dir \
      -v "${SCRIPTS_DIR}":/scripts:ro \
      -v "${REPO_ROOT}/workspace/.python_deps":/deps:ro \
      slam-base:latest \
      bash -c "PYTHONPATH=/deps python3 /scripts/plot_gantt.py /run_dir ${algo} --dataset ${ds}" \
      || echo "[WARN] Gantt chart generation failed for ${algo} on ${ds}."
}

# ------------------------------------------------------------------------------
# 1. RUN CUVSLAM (NVIDIA Isaac ROS GPU-Accelerated)
# ------------------------------------------------------------------------------
run_cuvslam() {
    # Official NVIDIA Isaac ROS Visual SLAM 3.1.0 (apt package in slam-base, /opt/ros/humble).
    # Only the launch files (TFs, camera_info/IMU relays) come from the workspace; the modified
    # build in workspace/isaac_ros_ws/install is not used.
    local launch_dir="/workspaces/isaac_ros-dev/src/isaac_ros_visual_slam/isaac_ros_visual_slam/launch"
    local target_dataset="$1"
    local target_algo="${2:-cuvslam}"
    local results_dir="${REPO_ROOT}/results"
    local bag_dir="${REPO_ROOT}/datasets"
    local bag_name=""
    local rviz_cfg=""
    local launch_file=""

    case "$target_dataset" in
        MH_01_easy)
            results_dir="${results_dir}/MH_01_easy/${target_algo}"
            launch_file="isaac_ros_visual_slam_euroc.launch.py"
            rviz_cfg="/rviz_cfg/euroc_rviz.rviz"
            if [ -d "${bag_dir}/MH_01_easy/MH_01_easy_ros2" ]; then
                bag_name="MH_01_easy/MH_01_easy_ros2"
            else
                bag_name="MH_01_easy"
            fi
            ;;
        V1_03_difficult)
            # Same EuRoC sensor rig and calibration as MH_01_easy, so the same launch file.
            results_dir="${results_dir}/V1_03_difficult/${target_algo}"
            launch_file="isaac_ros_visual_slam_euroc.launch.py"
            rviz_cfg="/rviz_cfg/euroc_rviz.rviz"
            bag_name="V1_03_difficult/V1_03_difficult_ros2"
            ;;
        suedhoehe|schnee|snow|suedhoehe_gps_schnee_02)
            results_dir="${results_dir}/suedhoehe/${target_algo}"
            launch_file="isaac_ros_visual_slam_suedhoehe.launch.py"
            rviz_cfg="/rviz_cfg/suedhoehe_rviz.rviz"
            bag_name="suedhoehe_gps_schnee_02"
            ;;
        corridor|tum_vi|tumvi|corridor1)
            results_dir="${results_dir}/corridor/${target_algo}"
            if [ "$target_algo" = "cuvslam_purestereo" ]; then
                launch_file="isaac_ros_visual_slam_corridor_purestereo.launch.py"
            else
                launch_file="isaac_ros_visual_slam_corridor.launch.py"
            fi
            rviz_cfg="/rviz_cfg/openvins_rviz.rviz"
            bag_name="tum_vi_corridor1/corridor1_ros2"
            ;;
        *)
            echo "[ERROR] Unknown dataset for cuVSLAM: '$target_dataset'. Supported: 'MH_01_easy', 'V1_03_difficult', 'suedhoehe', 'corridor'."
            exit 1
            ;;
    esac

    if [ ! -d "$results_dir" ]; then
        mkdir -p "$results_dir"
    fi

    echo "=========================================================="
    echo " [cuVSLAM] NVIDIA Isaac ROS GPU-Accelerated SLAM"
    echo " Dataset: $target_dataset | Mode: $( [ "$ENABLE_GUI" = true ] && echo "Live GUI" || echo "Headless" )"
    echo " Output Trajectory: ${results_dir}/cuvslam_tum.txt"
    echo "=========================================================="

    docker kill cuvslam_node cuvslam_rviz cuvslam_player 2>/dev/null || true
    docker rm -f cuvslam_node cuvslam_rviz cuvslam_player 2>/dev/null || true

    if [ "$ENABLE_GUI" = true ]; then
        # Terminal 1: cuVSLAM Node
        launch_terminal "[1] cuVSLAM Node" \
          "docker run --rm --name cuvslam_node \
            --runtime=nvidia --gpus all \
            --cpus=${CPUS} --memory=${MEMORY} \
            --net=host --ipc=host \
            -v '${REPO_ROOT}/workspace/isaac_ros_ws':/workspaces/isaac_ros-dev:ro \
            -v '${results_dir}':/results \
            -v '${SCRIPTS_DIR}':/scripts \
            slam-base:latest \
            bash -c 'source /opt/ros/humble/setup.bash && \
                     (python3 /scripts/cuvslam_save_trajectory.py /results/cuvslam_tum.txt ${target_dataset} &) && \
                     ros2 launch ${launch_dir}/${launch_file}'"

        sleep 4

        # Terminal 2: RViz2
        launch_terminal "[2] RViz2 cuVSLAM Viewer" \
          "docker run --rm --name cuvslam_rviz \
            --runtime=nvidia --gpus all \
            --net=host --ipc=host \
            -e DISPLAY=${DISPLAY} -e QT_X11_NO_MITSHM=1 -v /tmp/.X11-unix:/tmp/.X11-unix \
            -v '${RVIZ_DIR}':/rviz_cfg \
            slam-base:latest \
            bash -c 'source /opt/ros/humble/setup.bash && rviz2 -d ${rviz_cfg}'"

        sleep 2

        # Terminal 3: Bag Player
        launch_terminal "[3] Rosbag Player" \
          "docker run --rm --name cuvslam_player -it \
            --net=host --ipc=host \
            -v '${bag_dir}':/dataset_dir \
            slam-base:latest \
            bash -c 'source /opt/ros/humble/setup.bash && ros2 bag play /dataset_dir/${bag_name}'"

        echo "[*] Playing rosbag in GUI mode. Waiting for playback to complete..."
        sleep 4
        while docker ps --format '{{.Names}}' | grep -q cuvslam_player; do
            sleep 2
        done
        sleep 2
        docker kill cuvslam_node cuvslam_rviz 2>/dev/null || true
        docker rm -f cuvslam_node cuvslam_rviz 2>/dev/null || true
    else
        docker run -d --name cuvslam_node \
          --runtime=nvidia --gpus all \
          --cpus="${CPUS}" --memory="${MEMORY}" \
          --net=host --ipc=host \
          -v "${REPO_ROOT}/workspace/isaac_ros_ws":/workspaces/isaac_ros-dev:ro \
          -v "${results_dir}":/results \
          -v "${SCRIPTS_DIR}":/scripts \
          slam-base:latest \
          bash -c "source /opt/ros/humble/setup.bash && \
                   ros2 launch ${launch_dir}/${launch_file}"

        # Wait until the cuVSLAM node has started (instead of a fixed sleep), so the first
        # images of the bag are not lost while the GPU/NITROS initialise.
        for _ in $(seq 1 60); do
            docker logs cuvslam_node 2>&1 | grep -q "Loaded node '/visual_slam_node'" && break
            sleep 1
        done
        sleep 2
        docker exec -d cuvslam_node bash -c "source /opt/ros/humble/setup.bash && python3 /scripts/cuvslam_save_trajectory.py /results/cuvslam_tum.txt ${target_dataset}"
        sleep 1

        docker run --rm --name cuvslam_player \
          --net=host --ipc=host \
          -v "${bag_dir}":/dataset_dir \
          slam-base:latest \
          bash -c "source /opt/ros/humble/setup.bash && ros2 bag play /dataset_dir/${bag_name}"

        sleep 3
        docker kill cuvslam_node 2>/dev/null || true
        docker rm -f cuvslam_node 2>/dev/null || true
    fi

    save_gantt_chart "$target_algo" "$target_dataset"
    echo "[✔] cuVSLAM run finished: ${results_dir}/cuvslam_tum.txt"
}

# ------------------------------------------------------------------------------
# 2. RUN OPENVINS (MSCKF Filter)
# ------------------------------------------------------------------------------
run_openvins() {
    local target_dataset="$1"
    local results_dir="${REPO_ROOT}/results"
    local catkin_ws="${REPO_ROOT}/workspace/catkin_ws_ov"
    local bag_dir="${REPO_ROOT}/datasets"
    local bag_name=""
    local config_path="/catkin_ws/src/open_vins/config/suedhoehe/estimator_config.yaml"
    local rviz_cfg="/rviz_cfg/openvins_rviz.rviz"

    local ros_args="--ros-args -p save_total_state:=true -p filepath_est:=/results/ov_estimate.txt -p filepath_std:=/results/ov_estimate_std.txt"
    if [ "$target_dataset" = "MH_01_easy" ]; then
        results_dir="${results_dir}/MH_01_easy/openvins"
        config_path="/catkin_ws/src/open_vins/config/euroc_mav/estimator_config.yaml"
        if [ -d "${bag_dir}/MH_01_easy/MH_01_easy_ros2" ]; then
            bag_name="MH_01_easy/MH_01_easy_ros2"
        else
            bag_name="MH_01_easy"
        fi
        rviz_cfg="/rviz_cfg/openvins_rviz.rviz"
        if [ -f "${bag_dir}/MH_01_easy/mav0/state_groundtruth_estimate0/data.csv" ]; then
            ros_args="${ros_args} -p path_gt:=/dataset_dir/MH_01_easy/mav0/state_groundtruth_estimate0/data.csv"
        fi
    elif [ "$target_dataset" = "V1_03_difficult" ]; then
        results_dir="${results_dir}/V1_03_difficult/openvins"
        config_path="/catkin_ws/src/open_vins/config/euroc_mav/estimator_config.yaml"
        bag_name="V1_03_difficult/V1_03_difficult_ros2"
        rviz_cfg="/rviz_cfg/openvins_rviz.rviz"
        if [ -f "${bag_dir}/V1_03_difficult/mav0/state_groundtruth_estimate0/data.csv" ]; then
            ros_args="${ros_args} -p path_gt:=/dataset_dir/V1_03_difficult/mav0/state_groundtruth_estimate0/data.csv"
        fi
    elif [ "$target_dataset" = "corridor" ] || [ "$target_dataset" = "tum_vi" ] || [ "$target_dataset" = "corridor1" ]; then
        results_dir="${results_dir}/corridor/openvins"
        config_path="/catkin_ws/src/open_vins/config/tum_vi/estimator_config.yaml"
        bag_name="tum_vi_corridor1/corridor1_ros2"
        rviz_cfg="/rviz_cfg/openvins_rviz.rviz"
        if [ -f "${bag_dir}/tum_vi_corridor1_asl/gt_tum.txt" ]; then
            ros_args="${ros_args} -p path_gt:=/dataset_dir/tum_vi_corridor1_asl/gt_tum.txt"
        fi
    elif [ "$target_dataset" = "suedhoehe" ] || [ "$target_dataset" = "schnee" ] || [ "$target_dataset" = "snow" ] || [ "$target_dataset" = "suedhoehe_gps_schnee_02" ]; then
        results_dir="${results_dir}/suedhoehe/openvins"
        bag_name="suedhoehe_gps_schnee_02"
        if [ -f "${bag_dir}/suedhoehe_gps_schnee_02/suedhoehe_gt_asl.csv" ]; then
            ros_args="${ros_args} -p path_gt:=/dataset_dir/suedhoehe_gps_schnee_02/suedhoehe_gt_asl.csv"
        fi
    else
        echo "[ERROR] Unknown dataset for OpenVINS: '$target_dataset'. Supported: 'MH_01_easy', 'V1_03_difficult', 'corridor', 'suedhoehe'."
        exit 1
    fi

    mkdir -p "$results_dir"

    echo "=========================================================="
    echo " [OpenVINS] MSCKF Filter Sliding-Window VIO"
    echo " Dataset: $target_dataset | Mode: $( [ "$ENABLE_GUI" = true ] && echo "Live GUI" || echo "Headless" )"
    echo " Output Trajectory: ${results_dir}/openvins_tum.txt"
    echo "=========================================================="

    docker kill openvins_node openvins_rviz openvins_player 2>/dev/null || true
    docker rm -f openvins_node openvins_rviz openvins_player 2>/dev/null || true

    if [ "$ENABLE_GUI" = true ]; then
        launch_terminal "[1] OpenVINS MSCKF Node" \
          "docker run --rm --name openvins_node --entrypoint '' \
            --cpus=${CPUS} --memory=${MEMORY} \
            --net=host --ipc=host \
            -v '${catkin_ws}':/catkin_ws \
            -v '${bag_dir}':/dataset_dir \
            -v '${results_dir}':/results \
            slam-base:latest \
            bash -c 'source /opt/ros/humble/setup.bash && source /catkin_ws/install/setup.bash && ros2 run ov_msckf run_subscribe_msckf ${config_path} ${ros_args}'"

        sleep 3

        launch_terminal "[2] RViz2 OpenVINS Viewer" \
          "docker run --rm --name openvins_rviz --entrypoint '' \
            --net=host --ipc=host \
            -e DISPLAY=${DISPLAY} -e QT_X11_NO_MITSHM=1 -v /tmp/.X11-unix:/tmp/.X11-unix \
            -v '${RVIZ_DIR}':/rviz_cfg \
            slam-base:latest \
            bash -c 'source /opt/ros/humble/setup.bash && rviz2 -d ${rviz_cfg}'"

        sleep 2

        launch_terminal "[3] Rosbag Player" \
          "docker run --rm --name openvins_player --entrypoint '' -it \
            --net=host --ipc=host \
            -v '${bag_dir}':/dataset_dir \
            slam-base:latest \
            bash -c 'source /opt/ros/humble/setup.bash && ros2 bag play /dataset_dir/${bag_name} --rate 1.0'"

        echo "[*] Playing rosbag in GUI mode. Waiting for playback to complete..."
        sleep 4
        while docker ps --format '{{.Names}}' | grep -q openvins_player; do
            sleep 2
        done
        sleep 2
        docker kill openvins_node 2>/dev/null || true
        docker rm -f openvins_node 2>/dev/null || true
    else
        docker run -d --name openvins_node --entrypoint "" \
          --cpus="${CPUS}" --memory="${MEMORY}" \
          --net=host --ipc=host \
          -v "${catkin_ws}":/catkin_ws \
          -v "${bag_dir}":/dataset_dir \
          -v "${results_dir}":/results \
          slam-base:latest \
          bash -c "source /opt/ros/humble/setup.bash && \
                   source /catkin_ws/install/setup.bash && \
                   ros2 run ov_msckf run_subscribe_msckf ${config_path} ${ros_args}"

        sleep 3

        docker run --rm --name openvins_player --entrypoint "" \
          --net=host --ipc=host \
          -v "${bag_dir}":/dataset_dir \
          slam-base:latest \
          bash -c "source /opt/ros/humble/setup.bash && ros2 bag play /dataset_dir/${bag_name} --rate 1.0"

        sleep 3
        docker kill openvins_node 2>/dev/null || true
        docker rm -f openvins_node 2>/dev/null || true
    fi

    # Fix permissions and convert output trajectory to standard TUM format (BOTH GUI and Headless)
    docker run --rm --entrypoint "" -v "${results_dir}":/results slam-base:latest chmod -R 777 /results 2>/dev/null || true
    if [ -f "${results_dir}/ov_estimate.txt" ]; then
        python3 "${SCRIPTS_DIR}/convert_openvins_to_tum.py" "${results_dir}/ov_estimate.txt" "${results_dir}/openvins_tum.txt" 2>/dev/null || true
    elif [ -f "${REPO_ROOT}/results/ov_estimate.txt" ]; then
        python3 "${SCRIPTS_DIR}/convert_openvins_to_tum.py" "${REPO_ROOT}/results/ov_estimate.txt" "${results_dir}/openvins_tum.txt" 2>/dev/null || true
    fi
    save_gantt_chart "openvins" "$target_dataset"

    echo "[✔] OpenVINS run finished: ${results_dir}/openvins_tum.txt"
}

# ------------------------------------------------------------------------------
# 3. RUN ORB-SLAM3 (Baseline & Hybrid KLT)
# ------------------------------------------------------------------------------
run_orbslam3_variant() {
    local variant="$1" # "baseline" or "klt"
    local target_dataset="$2"
    local algo_sub="orbslam3"
    local config_yaml="/orbslam3_ws/config/EuRoC.yaml"
    local out_name="orbslam3_tum.txt"
    local title="ORB-SLAM3 Baseline"

    local docker_image="orbslam3:latest"
    # Baseline runs the instrumented ORB-SLAM3 source from the workspace (per-module timing
    # with timestamps, see include/ScopedTiming.h), mounted over the image's /opt/ORB_SLAM3.
    local src_mount="-v ${REPO_ROOT}/workspace/orbslam3_ws/ORB_SLAM3:/opt/ORB_SLAM3"
    local bin_cmd="/opt/ORB_SLAM3/Examples/Stereo-Inertial/stereo_inertial_euroc /opt/ORB_SLAM3/Vocabulary/ORBvoc.txt ${config_yaml} /dataset /dataset/timestamps.txt ${algo_sub}"

    if [ "$variant" = "klt" ]; then
        algo_sub="orbslam3_klt"
        config_yaml="/orbslam3_ws/config/EuRoC_KLT.yaml"
        out_name="orbslam3_klt_tum.txt"
        title="ORB-SLAM3 Hybrid KLT"
        docker_image="orbslam3_klt:latest"
        src_mount=""
        bin_cmd="/opt/ORB_SLAM3_KLT/Examples/Monocular/mono_euroc /opt/ORB_SLAM3_KLT/Vocabulary/ORBvoc.txt /opt/ORB_SLAM3_KLT/Examples/Monocular/EuRoC.yaml /dataset /dataset/timestamps.txt ${algo_sub}"
    fi

    local ds_dir="MH_01_easy"
    local results_dir="${REPO_ROOT}/results"
    local dataset_path="${REPO_ROOT}/datasets/MH_01_easy"

    if [ "$target_dataset" = "MH_01_easy" ]; then
        ds_dir="MH_01_easy"
        results_dir="${results_dir}/MH_01_easy/${algo_sub}"
        dataset_path="${REPO_ROOT}/datasets/MH_01_easy"
    elif [ "$target_dataset" = "V1_03_difficult" ]; then
        # Same EuRoC sensor rig and calibration as MH_01_easy, so the same EuRoC config.
        ds_dir="V1_03_difficult"
        results_dir="${results_dir}/V1_03_difficult/${algo_sub}"
        dataset_path="${REPO_ROOT}/datasets/V1_03_difficult"
    elif [ "$target_dataset" = "suedhoehe" ] || [ "$target_dataset" = "schnee" ]; then
        ds_dir="suedhoehe"
        results_dir="${results_dir}/suedhoehe/${algo_sub}"
        dataset_path="${REPO_ROOT}/datasets/suedhoehe_asl"
        config_yaml="/orbslam3_ws/suedhoehe_stereo_inertial.yaml"
        bin_cmd="/opt/ORB_SLAM3/Examples/Stereo-Inertial/stereo_inertial_euroc /opt/ORB_SLAM3/Vocabulary/ORBvoc.txt ${config_yaml} /dataset /dataset/timestamps.txt ${algo_sub}"
        if [ "$variant" = "klt" ]; then
            config_yaml="/orbslam3_ws/suedhoehe_stereo_inertial.yaml"
            bin_cmd="/opt/ORB_SLAM3_KLT/Examples/Stereo-Inertial/stereo_inertial_euroc /opt/ORB_SLAM3_KLT/Vocabulary/ORBvoc.txt ${config_yaml} /dataset /dataset/timestamps.txt ${algo_sub}"
        fi
        echo "=========================================================="
        echo " [$title] Dataset: suedhoehe (Outdoor Snow Sequence)"
        echo " [NOTE] Running ORB-SLAM3 on Suedhoehe ASL dataset..."
        echo "=========================================================="
    elif [ "$target_dataset" = "corridor" ] || [ "$target_dataset" = "tum_vi" ] || [ "$target_dataset" = "corridor1" ]; then
        ds_dir="corridor"
        results_dir="${results_dir}/corridor/${algo_sub}"
        dataset_path="${REPO_ROOT}/datasets/tum_vi_corridor1"
        config_yaml="/orbslam3_ws/tum_vi_stereo_inertial.yaml"
        bin_cmd="/opt/ORB_SLAM3/Examples/Stereo-Inertial/stereo_inertial_euroc /opt/ORB_SLAM3/Vocabulary/ORBvoc.txt ${config_yaml} /dataset /dataset/timestamps.txt ${algo_sub}"
        if [ "$variant" = "klt" ]; then
            config_yaml="/orbslam3_ws/tum_vi_stereo_inertial.yaml"
            bin_cmd="/opt/ORB_SLAM3_KLT/Examples/Stereo-Inertial/stereo_inertial_euroc /opt/ORB_SLAM3_KLT/Vocabulary/ORBvoc.txt ${config_yaml} /dataset /dataset/timestamps.txt ${algo_sub}"
        fi
        echo "=========================================================="
        echo " [$title] Dataset: corridor (TUM-VI Corridor 1 Sequence)"
        echo " [NOTE] Running ORB-SLAM3 on TUM-VI Corridor dataset..."
        echo "=========================================================="
    else
        echo "[ERROR] Unknown dataset for ${title}: '$target_dataset'. Supported: 'MH_01_easy', 'V1_03_difficult', 'corridor', 'suedhoehe'."
        exit 1
    fi

    mkdir -p "$results_dir"

    echo "=========================================================="
    echo " [$title] Stereo-Inertial SLAM"
    echo " Dataset: $target_dataset | Mode: $( [ "$ENABLE_GUI" = true ] && echo "Pangolin 3D GUI" || echo "Headless" )"
    echo "=========================================================="

    if [ "$ENABLE_GUI" = true ]; then
        xhost +local:root 2>/dev/null || xhost + 2>/dev/null || true
        launch_terminal "$title [Pangolin 3D GUI]" \
          "docker run --rm --entrypoint '' -it \
            --cpus=${CPUS} --memory=${MEMORY} \
            --net=host --ipc=host \
            -e DISPLAY=${DISPLAY} -e QT_X11_NO_MITSHM=1 -v /tmp/.X11-unix:/tmp/.X11-unix \
            -v '${REPO_ROOT}/workspace/orbslam3_ws':/orbslam3_ws ${src_mount} \
            -v '${dataset_path}':/dataset \
            -v '${results_dir}':/results \
            ${docker_image} \
            bash -c 'source /opt/ros/humble/setup.bash 2>/dev/null || true; \
                     cd /results && \
                     if [ -f /dataset/timestamps.txt ]; then \
                       '"\${bin_cmd}"'; \
                     fi && \
                     [ -f /results/f_${algo_sub}.txt ] && cp -f /results/f_${algo_sub}.txt /results/${out_name} || true; \
                     [ -f /results/CameraTrajectory.txt ] && cp -f /results/CameraTrajectory.txt /results/${out_name} || true; \
                     chmod -R 777 /results 2>/dev/null || true'"
    else
        docker run --rm --entrypoint "" \
          --cpus="${CPUS}" --memory="${MEMORY}" \
          -v "${REPO_ROOT}/workspace/orbslam3_ws":/orbslam3_ws ${src_mount} \
          -v "${dataset_path}":/dataset \
          -v "${results_dir}":/results \
          ${docker_image} \
          bash -c "source /opt/ros/humble/setup.bash 2>/dev/null || true; \
                   cd /results && \
                   if [ -f /dataset/timestamps.txt ]; then \
                     ${bin_cmd}; \
                   fi && \
                   [ -f /results/f_${algo_sub}.txt ] && cp -f /results/f_${algo_sub}.txt /results/${out_name} || true; \
                   [ -f /results/CameraTrajectory.txt ] && cp -f /results/CameraTrajectory.txt /results/${out_name} || true; \
                   chmod -R 777 /results 2>/dev/null || true"

        if [ -f "${results_dir}/f_${algo_sub}.txt" ]; then
            python3 -c "
with open('${results_dir}/f_${algo_sub}.txt') as fin, open('${results_dir}/${out_name}', 'w') as fout:
    for line in fin:
        p = line.strip().split()
        if not p: continue
        t = float(p[0])
        if t > 1e12: t /= 1e9
        fout.write(f'{t:.6f} ' + ' '.join(p[1:]) + '\n')
" 2>/dev/null || true
        fi

        save_gantt_chart "$algo_sub" "$ds_dir"
        echo "[✔] $title run finished: ${results_dir}/${out_name}"
    fi
}

# ------------------------------------------------------------------------------
# 4. RUN KIMERA-VIO (GTSAM Factor Graph)
# ------------------------------------------------------------------------------
run_kimera() {
    local target_dataset="$1"
    local results_dir="${REPO_ROOT}/results"
    local params_path="${REPO_ROOT}/suedhoehe_kimera_params"
    local bag_dir="${REPO_ROOT}/datasets"
    local bag_name=""
    local left_topic="/camera/infra1/image_rect_raw"
    local right_topic="/camera/infra2/image_rect_raw"
    local imu_topic="/camera/imu"
    local rviz_cfg="/rviz_cfg/suedhoehe_rviz.rviz"

    if [ "$target_dataset" = "MH_01_easy" ]; then
        results_dir="${results_dir}/MH_01_easy/kimera"
        params_path="${REPO_ROOT}/euroc_kimera_params"
        if [ -d "${bag_dir}/MH_01_easy/MH_01_easy_ros2" ]; then
            bag_name="MH_01_easy/MH_01_easy_ros2"
        else
            bag_name="MH_01_easy"
        fi
        left_topic="/cam0/image_raw"
        right_topic="/cam1/image_raw"
        imu_topic="/imu0"
        rviz_cfg="/rviz_cfg/euroc_rviz.rviz"
    elif [ "$target_dataset" = "V1_03_difficult" ]; then
        # Same EuRoC sensor rig and calibration as MH_01_easy, so the same params folder.
        results_dir="${results_dir}/V1_03_difficult/kimera"
        params_path="${REPO_ROOT}/euroc_kimera_params"
    elif [ "$target_dataset" = "corridor" ] || [ "$target_dataset" = "tum_vi" ] || [ "$target_dataset" = "corridor1" ]; then
        results_dir="${results_dir}/corridor/kimera"
        params_path="${REPO_ROOT}/corridor_kimera_params"
        bag_name="tum_vi_corridor1/corridor1_ros2"
        left_topic="/cam0/image_raw"
        right_topic="/cam1/image_raw"
        imu_topic="/imu0"
        rviz_cfg="/rviz_cfg/openvins_rviz.rviz"
    elif [ "$target_dataset" = "suedhoehe" ] || [ "$target_dataset" = "schnee" ] || [ "$target_dataset" = "snow" ] || [ "$target_dataset" = "suedhoehe_gps_schnee_02" ]; then
        results_dir="${results_dir}/suedhoehe/kimera"
        bag_name="suedhoehe_gps_schnee_02"
    else
        echo "[ERROR] Unknown dataset for Kimera-VIO: '$target_dataset'. Supported: 'MH_01_easy', 'V1_03_difficult', 'corridor', 'suedhoehe'."
        exit 1
    fi

    mkdir -p "$results_dir"

    echo "=========================================================="
    echo " [Kimera-VIO] GTSAM Smoothing Factor Graph & 3D Mesh"
    echo " Dataset: $target_dataset | Mode: $( [ "$ENABLE_GUI" = true ] && echo "Live GUI" || echo "Headless" )"
    echo "=========================================================="

    docker kill kimera_node kimera_rviz kimera_player 2>/dev/null || true
    docker rm -f kimera_node kimera_rviz kimera_player 2>/dev/null || true

    if [ "$target_dataset" = "MH_01_easy" ] || [ "$target_dataset" = "V1_03_difficult" ] || [ "$target_dataset" = "corridor" ] || [ "$target_dataset" = "tum_vi" ] || [ "$target_dataset" = "corridor1" ]; then
        # Latest official Kimera-VIO (workspace/kimera_ws/Dockerfile), offline EuRoC-format reader,
        # started like upstream scripts/stereoVIOEuroc.bash: one params folder + flag files.
        # The settings after the flag files only switch off GUI/image output for headless runs.
        # initial_k: Kimera's IMU initialisation (autoInitialize: 1) assumes the platform is at
        # rest, so each dataset starts in its stillest window:
        #   MH_01_easy:      frame 460 (t~23 s), stationary from ~22 s to ~44 s (take-off)
        #   V1_03_difficult: frame 20 (t~1 s), stationary only for the first ~3 s
        #   corridor:        frame 70 (t~3.5 s), quietest window of the handheld sequence
        local kimera_root="/opt/kimera/Kimera-VIO"
        local asl_dir="${REPO_ROOT}/datasets/MH_01_easy"
        local initial_k=460
        if [ "$target_dataset" = "V1_03_difficult" ]; then
            asl_dir="${REPO_ROOT}/datasets/V1_03_difficult"
            initial_k=20
        elif [ "$target_dataset" != "MH_01_easy" ]; then
            asl_dir="${REPO_ROOT}/datasets/tum_vi_corridor1"
            initial_k=70
        fi
        echo "[*] Running Kimera-VIO (latest, ${KIMERA_IMAGE}) on ${target_dataset}..."
        docker run --rm \
          --cpus="${CPUS}" --memory="${MEMORY}" \
          --user "$(id -u):$(id -g)" -e HOME=/tmp \
          -e KIMERA_TIMING_CSV=/output/kimera_scoped_timing.csv \
          -w /output \
          -v "${asl_dir}":/dataset:ro \
          -v "${results_dir}":/output \
          -v "${params_path}":/params:ro \
          "${KIMERA_IMAGE}" \
          ${kimera_root}/build/stereoVIOEuroc \
            --dataset_type=0 \
            --dataset_path=/dataset \
            --initial_k=${initial_k} \
            --final_k=100000 \
            --params_folder_path=/params \
            --use_lcd=0 \
            --vocabulary_path=${kimera_root}/vocabulary/ORBvoc.yml \
            --flagfile=/params/flags/stereoVIOEuroc.flags \
            --flagfile=/params/flags/Mesher.flags \
            --flagfile=/params/flags/VioBackend.flags \
            --flagfile=/params/flags/RegularVioBackend.flags \
            --flagfile=/params/flags/Visualizer3D.flags \
            --visualize=false \
            --save_frontend_images=false \
            --visualize_frontend_images=false \
            --logtostderr=1 \
            --colorlogtostderr=0 \
            --log_prefix=1 \
            --v=0 \
            --log_output=true \
            --log_euroc_gt_data=false \
            --output_path=/output/ \
          > "${results_dir}/run.log" 2>&1 || echo "[WARN] Kimera-VIO exited with an error, see ${results_dir}/run.log"
    else
        if [ "$ENABLE_GUI" = true ]; then
            launch_terminal "[1] Kimera-VIO Node" \
              "docker run --rm --name kimera_node --entrypoint '' \
                --cpus=${CPUS} --memory=${MEMORY} \
                --net=host --ipc=host \
                -v '${bag_dir}':/dataset_dir \
                -v '${results_dir}':/output \
                -v '${params_path}':/params \
                -v '${SCRIPTS_DIR}':/scripts \
                kimera:latest \
                bash -c 'source /opt/wrapper_ws/install/setup.bash && \
                         ros2 launch kimera_vio_ros kimera_vio_ros.launch.xml \
                           params_folder:=/params \
                           parallel:=false \
                           rectified:=false \
                           use_sim_time:=false \
                           use_camera_info:=false \
                           use_lcd:=false \
                           backend_type:=0 \
                           log_output:=true \
                           log_output_path:=/output/ \
                           cam_topic.left:=${left_topic} \
                           cam_topic.right:=${right_topic} \
                           imu_topic:=${imu_topic}'"

            sleep 5

            launch_terminal "[2] RViz2 Kimera Viewer" \
              "docker run --rm --name kimera_rviz --entrypoint '' \
                --net=host --ipc=host \
                -e DISPLAY=${DISPLAY} -e QT_X11_NO_MITSHM=1 -v /tmp/.X11-unix:/tmp/.X11-unix \
                -v '${RVIZ_DIR}':/rviz_cfg \
                slam-base:latest \
                bash -c 'source /opt/ros/humble/setup.bash && (ros2 run tf2_ros static_transform_publisher 0 0 0 0 0 0 odom world &) && rviz2 -d ${rviz_cfg}'"

            sleep 2

            launch_terminal "[3] Rosbag Player" \
              "docker run --rm --name kimera_player --entrypoint '' -it \
                --net=host --ipc=host \
                -v '${bag_dir}':/dataset_dir \
                slam-base:latest \
                bash -c 'source /opt/ros/humble/setup.bash && ros2 bag play /dataset_dir/${bag_name}'"

            echo "[*] Playing rosbag in GUI mode. Waiting for playback to complete..."
            sleep 4
            while docker ps --format '{{.Names}}' | grep -q kimera_player; do
                sleep 2
            done
            sleep 2
            docker kill kimera_node kimera_rviz 2>/dev/null || true
            docker rm -f kimera_node kimera_rviz 2>/dev/null || true
        else
            docker run -d --name kimera_node --entrypoint "" \
              --cpus="${CPUS}" --memory="${MEMORY}" \
              --net=host --ipc=host \
              -v "${bag_dir}":/dataset_dir \
              -v "${results_dir}":/output \
              -v "${params_path}":/params \
              -v "${SCRIPTS_DIR}":/scripts \
              -v "${REPO_ROOT}/workspace/isaac_ros_ws":/workspaces/isaac_ros-dev \
              kimera:latest \
              bash -c "source /opt/wrapper_ws/install/setup.bash && \
                       if [ '$target_dataset' = 'corridor' ] || [ '$target_dataset' = 'tum_vi' ] || [ '$target_dataset' = 'corridor1' ]; then \
                           (python3 /workspaces/isaac_ros-dev/corridor_camera_info_pub.py &) && sleep 2 && \
                           left_topic='/corridor/cam0/image_mono8' && \
                           right_topic='/corridor/cam1/image_mono8'; \
                       fi && \
                       ros2 launch kimera_vio_ros kimera_vio_ros.launch.xml \
                         params_folder:=/params \
                         parallel:=false \
                         rectified:=false \
                         use_sim_time:=false \
                         use_camera_info:=false \
                         use_lcd:=false \
                         backend_type:=0 \
                         log_output:=true \
                         log_output_path:=/output/ \
                         cam_topic.left:=\${left_topic} \
                         cam_topic.right:=\${right_topic} \
                         imu_topic:=${imu_topic}"

            sleep 5
            docker run --rm --name kimera_player --entrypoint "" \
              --net=host --ipc=host \
              -v "${bag_dir}":/dataset_dir \
              slam-base:latest \
              bash -c "source /opt/ros/humble/setup.bash && ros2 bag play /dataset_dir/${bag_name}"

            sleep 3
            docker kill kimera_node 2>/dev/null || true
            docker rm -f kimera_node 2>/dev/null || true
        fi
    fi

    # Fix permissions and convert output trajectory to standard TUM format (BOTH GUI and Headless)
    docker run --rm --entrypoint "" -v "${results_dir}":/output slam-base:latest chmod -R 777 /output 2>/dev/null || true
    if [ -f "${results_dir}/output_posesVIO.csv" ]; then
        python3 "${SCRIPTS_DIR}/convert_kimera_to_tum.py" "${results_dir}/output_posesVIO.csv" "${results_dir}/kimera_tum.txt" 2>/dev/null || true
    elif [ -f "${results_dir}/output_lcd_optimized_traj.csv" ]; then
        python3 "${SCRIPTS_DIR}/convert_kimera_to_tum.py" "${results_dir}/output_lcd_optimized_traj.csv" "${results_dir}/kimera_tum.txt" 2>/dev/null || true
    elif [ -f "${results_dir}/traj_vio.csv" ]; then
        python3 "${SCRIPTS_DIR}/convert_kimera_to_tum.py" "${results_dir}/traj_vio.csv" "${results_dir}/kimera_tum.txt" 2>/dev/null || true
    fi

    # Clean up empty (0-byte) CSV files and empty frontend_images directory created by Kimera loggers
    find "${results_dir}" -name "*.csv" -size 0 -delete 2>/dev/null || true
    rm -rf "${results_dir}/frontend_images" 2>/dev/null || true

    save_gantt_chart "kimera" "$target_dataset"

    echo "[✔] Kimera-VIO run finished: ${results_dir}/kimera_tum.txt"
}

# ------------------------------------------------------------------------------
# DISPATCHER
# ------------------------------------------------------------------------------
case "$ALGORITHM" in
    cuvslam)
        run_cuvslam "$DATASET" "cuvslam"
        ;;
    cuvslam_purestereo)
        run_cuvslam "$DATASET" "cuvslam_purestereo"
        ;;
    openvins)
        run_openvins "$DATASET"
        ;;
    orbslam3)
        run_orbslam3_variant "baseline" "$DATASET"
        ;;
    orbslam3_klt)
        run_orbslam3_variant "klt" "$DATASET"
        ;;
    kimera)
        run_kimera "$DATASET"
        ;;
    all)
        echo "=========================================================="
        echo " Running Master Benchmark Suite..."
        echo "=========================================================="
        if [ "$DATASET" = "suedhoehe" ]; then
            echo "[*] Target: Suedhoehe Outdoor Snow Benchmark (All Algorithms)"
            run_cuvslam "suedhoehe"
            run_openvins "suedhoehe"
            run_kimera "suedhoehe"
            run_orbslam3_variant "baseline" "suedhoehe"
            run_orbslam3_variant "klt" "suedhoehe"
            save_gantt_chart "cuvslam" "suedhoehe"
            save_gantt_chart "openvins" "suedhoehe"
            save_gantt_chart "kimera" "suedhoehe"
            save_gantt_chart "orbslam3" "suedhoehe"
            save_gantt_chart "orbslam3_klt" "suedhoehe"
        elif [ "$DATASET" = "corridor" ]; then
            echo "[*] Target: TUM-VI Corridor 1 Benchmark (All 5 Algorithms)"
            run_cuvslam "corridor"
            run_openvins "corridor"
            run_kimera "corridor"
            run_orbslam3_variant "baseline" "corridor"
            run_orbslam3_variant "klt" "corridor"
            save_gantt_chart "cuvslam" "corridor"
            save_gantt_chart "openvins" "corridor"
            save_gantt_chart "kimera" "corridor"
            save_gantt_chart "orbslam3" "corridor"
            save_gantt_chart "orbslam3_klt" "corridor"
        elif [ "$DATASET" = "all" ]; then
            echo "[*] Target: Complete Suite (EuRoC + Suedhoehe + Corridor)"
            run_cuvslam "MH_01_easy"
            run_openvins "MH_01_easy"
            run_kimera "MH_01_easy"
            run_orbslam3_variant "baseline" "MH_01_easy"
            run_orbslam3_variant "klt" "MH_01_easy"
            save_gantt_chart "cuvslam" "MH_01_easy"
            save_gantt_chart "openvins" "MH_01_easy"
            save_gantt_chart "kimera" "MH_01_easy"
            save_gantt_chart "orbslam3" "MH_01_easy"
            save_gantt_chart "orbslam3_klt" "MH_01_easy"

            run_cuvslam "suedhoehe"
            run_openvins "suedhoehe"
            run_kimera "suedhoehe"
            run_orbslam3_variant "baseline" "suedhoehe"
            run_orbslam3_variant "klt" "suedhoehe"
            save_gantt_chart "cuvslam" "suedhoehe"
            save_gantt_chart "openvins" "suedhoehe"
            save_gantt_chart "kimera" "suedhoehe"
            save_gantt_chart "orbslam3" "suedhoehe"
            save_gantt_chart "orbslam3_klt" "suedhoehe"

            run_cuvslam "corridor"
            run_openvins "corridor"
            run_kimera "corridor"
            run_orbslam3_variant "baseline" "corridor"
            run_orbslam3_variant "klt" "corridor"
            save_gantt_chart "cuvslam" "corridor"
            save_gantt_chart "openvins" "corridor"
            save_gantt_chart "kimera" "corridor"
            save_gantt_chart "orbslam3" "corridor"
            save_gantt_chart "orbslam3_klt" "corridor"
        else
            echo "[*] Target: EuRoC MH_01_easy 5-Way Benchmark (All 5 Algorithms)"
            run_cuvslam "MH_01_easy"
            run_openvins "MH_01_easy"
            run_kimera "MH_01_easy"
            run_orbslam3_variant "baseline" "MH_01_easy"
            run_orbslam3_variant "klt" "MH_01_easy"
            save_gantt_chart "cuvslam" "MH_01_easy"
            save_gantt_chart "openvins" "MH_01_easy"
            save_gantt_chart "kimera" "MH_01_easy"
            save_gantt_chart "orbslam3" "MH_01_easy"
            save_gantt_chart "orbslam3_klt" "MH_01_easy"
        fi
        echo "[✔] All benchmark runs complete!"
        ;;
    *)
        echo "[ERROR] Unknown algorithm: '$ALGORITHM'"
        show_help
        exit 1
        ;;
esac

# ------------------------------------------------------------------------------
# POST-RUN EVALUATION
# ------------------------------------------------------------------------------
if [ "$DO_EVALUATE" = true ]; then
    echo ""
    echo "=========================================================="
    echo " Evaluating Trajectory against Ground Truth (--evaluate)"
    echo "=========================================================="
    eval_flags=""
    if [ "$ENABLE_GUI" = true ]; then
        eval_flags="--gui"
    fi

    if [ "$ALGORITHM" = "all" ]; then
        docker run --rm \
          -v "${REPO_ROOT}":/repo \
          -v "${REPO_ROOT}/workspace/.python_deps":/deps \
          slam-base:latest \
          bash -c "export PYTHONPATH=/deps && python3 /repo/scripts/eval_all_trajectories.py"
    else
        "${SCRIPTS_DIR}/plot_3d_trajectory.sh" "$ALGORITHM" "$DATASET" $eval_flags
    fi
fi

