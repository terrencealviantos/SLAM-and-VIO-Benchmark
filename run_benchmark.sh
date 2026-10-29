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
#   ./run_benchmark.sh orbslam3 euroc --gui
#   ./run_benchmark.sh orbslam3_klt euroc --gui
#   ./run_benchmark.sh kimera suedhoehe --gui
#   ./run_benchmark.sh all all
#   ./run_benchmark.sh --evaluate
# ==============================================================================

set -e

REPO_ROOT="$(cd "$(dirname "$(realpath "${BASH_SOURCE[0]}")")" && pwd)"
SCRIPTS_DIR="${REPO_ROOT}/scripts"
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
    echo "  euroc          - EuRoC MAV Machine Hall sequence MH_01_easy (Vicon GT)"
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
    echo "  ./run_benchmark.sh kimera suedhoehe --gui"
    echo "  ./run_benchmark.sh orbslam3_klt euroc --gui"
    echo "  ./run_benchmark.sh all suedhoehe"
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
        suedhoehe|euroc|euroc_MH01|schnee|MH_01_easy)
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
    euroc*|mh01*|MH01*|MH_01*)
        DATASET="euroc"
        ;;
    all)
        DATASET="all"
        ;;
    *)
        DATASET="euroc"
        ;;
esac

# Fallback defaults
ALGORITHM="${ALGORITHM:-cuvslam}"
DATASET="${DATASET:-euroc}"

# Allow X11 for Docker GUI
xhost +local:root 2>/dev/null || xhost + 2>/dev/null || true

# ------------------------------------------------------------------------------
# Helper: Save algorithm-specific Gantt Chart to results folder
# ------------------------------------------------------------------------------
save_gantt_chart() {
    local algo="$1"
    local ds="$2"

    if [ "$ds" = "euroc" ] || [ "$ds" = "euroc_MH01" ] || [ "$ds" = "MH_01_easy" ]; then
        ds="euroc"
    else
        ds="suedhoehe"
    fi

    local dest_dir="${REPO_ROOT}/results/${ds}/${algo}"
    mkdir -p "$dest_dir"

    local src_chart=""
    case "$algo" in
        openvins)     src_chart="${REPO_ROOT}/figures/1_openvins_gantt_chart.png" ;;
        kimera)       src_chart="${REPO_ROOT}/figures/2_kimera_gantt_chart.png" ;;
        orbslam3)     src_chart="${REPO_ROOT}/figures/3_orbslam3_gantt_chart.png" ;;
        orbslam3_klt) src_chart="${REPO_ROOT}/figures/5_orbslam3_klt_gantt_chart.png" ;;
        cuvslam*)     src_chart="${REPO_ROOT}/figures/4_cuvslam_gantt_chart.png" ;;
    esac

    if [ ! -f "$src_chart" ]; then
        case "$algo" in
            openvins)     src_chart="${REPO_ROOT}/gantt_charts/1_openvins_gantt_chart.png" ;;
            kimera)       src_chart="${REPO_ROOT}/gantt_charts/2_kimera_gantt_chart.png" ;;
            orbslam3)     src_chart="${REPO_ROOT}/gantt_charts/3_orbslam3_gantt_chart.png" ;;
            orbslam3_klt) src_chart="${REPO_ROOT}/gantt_charts/5_orbslam3_klt_gantt_chart.png" ;;
            cuvslam*)     src_chart="${REPO_ROOT}/gantt_charts/4_cuvslam_gantt_chart.png" ;;
        esac
    fi

    if [ ! -f "$src_chart" ]; then
        python3 "${REPO_ROOT}/scripts/generate_publication_plots.py" 2>/dev/null || true
    fi

    if [ -f "$src_chart" ]; then
        cp -f "$src_chart" "${dest_dir}/gantt_chart.png"
        echo "[✔] Gantt chart saved: ${dest_dir}/gantt_chart.png"
    fi
}

# ------------------------------------------------------------------------------
# 1. RUN CUVSLAM (NVIDIA Isaac ROS GPU-Accelerated)
# ------------------------------------------------------------------------------
run_cuvslam() {
    local target_dataset="$1"
    local target_algo="${2:-cuvslam}"
    local results_dir="${REPO_ROOT}/results"
    local bag_dir="${REPO_ROOT}/datasets"
    local bag_name=""
    local rviz_cfg=""
    local launch_file=""

    case "$target_dataset" in
        euroc|euroc_MH01|MH_01_easy)
            results_dir="${results_dir}/euroc/${target_algo}"
            launch_file="isaac_ros_visual_slam_euroc.launch.py"
            rviz_cfg="/rviz_cfg/euroc_rviz.rviz"
            if [ -d "${bag_dir}/MH_01_easy/MH_01_easy_ros2" ]; then
                bag_name="MH_01_easy/MH_01_easy_ros2"
            else
                bag_name="MH_01_easy"
            fi
            ;;
        suedhoehe|schnee|snow|suedhoehe_gps_schnee_02)
            results_dir="${results_dir}/suedhoehe/${target_algo}"
            launch_file="isaac_ros_visual_slam_suedhoehe.launch.py"
            rviz_cfg="/rviz_cfg/suedhoehe_rviz.rviz"
            bag_name="suedhoehe_gps_schnee_02"
            ;;
        *)
            echo "[ERROR] Unknown dataset for cuVSLAM: '$target_dataset'. Supported: 'euroc', 'suedhoehe'."
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
            -v '${REPO_ROOT}/workspace/isaac_ros_ws':/workspaces/isaac_ros-dev \
            -v '${results_dir}':/results \
            -v '${SCRIPTS_DIR}':/scripts \
            slam-base:latest \
            bash -c 'export LD_LIBRARY_PATH=/workspaces/isaac_ros-dev/install/isaac_ros_visual_slam/share/cuvslam/lib:\$LD_LIBRARY_PATH && \
                     source /opt/ros/humble/setup.bash && \
                     source /workspaces/isaac_ros-dev/install/setup.bash && \
                     (python3 /scripts/cuvslam_save_trajectory.py /results/cuvslam_tum.txt ${target_dataset} &) && \
                     ros2 launch isaac_ros_visual_slam ${launch_file}'"

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
          -v "${REPO_ROOT}/workspace/isaac_ros_ws":/workspaces/isaac_ros-dev \
          -v "${results_dir}":/results \
          -v "${SCRIPTS_DIR}":/scripts \
          slam-base:latest \
          bash -c "export LD_LIBRARY_PATH=/workspaces/isaac_ros-dev/install/isaac_ros_visual_slam/share/cuvslam/lib:\$LD_LIBRARY_PATH && \
                   source /opt/ros/humble/setup.bash && \
                   source /workspaces/isaac_ros-dev/install/setup.bash && \
                   ros2 launch isaac_ros_visual_slam ${launch_file}"

        sleep 4
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
    local results_dir="${REPO_ROOT}/results/suedhoehe/openvins"
    local catkin_ws="${REPO_ROOT}/workspace/catkin_ws_ov"
    local bag_dir="${REPO_ROOT}/datasets"
    local bag_name="suedhoehe_gps_schnee_02"
    local config_path="/catkin_ws/src/open_vins/config/suedhoehe/estimator_config.yaml"
    local rviz_cfg="/rviz_cfg/openvins_rviz.rviz"

    local ros_args="--ros-args -p save_total_state:=true -p filepath_est:=/results/ov_estimate.txt -p filepath_std:=/results/ov_estimate_std.txt"
    if [ "$target_dataset" = "euroc" ] || [ "$target_dataset" = "euroc_MH01" ] || [ "$target_dataset" = "MH_01_easy" ]; then
        results_dir="${REPO_ROOT}/results/euroc/openvins"
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
        results_dir="${REPO_ROOT}/results/euroc/V1_03_difficult/openvins"
        config_path="/catkin_ws/src/open_vins/config/euroc_mav/estimator_config.yaml"
        bag_name="V1_03_difficult"
        rviz_cfg="/rviz_cfg/openvins_rviz.rviz"
        if [ -f "${bag_dir}/V1_03_difficult/mav0/state_groundtruth_estimate0/data.csv" ]; then
            ros_args="${ros_args} -p path_gt:=/dataset_dir/V1_03_difficult/mav0/state_groundtruth_estimate0/data.csv"
        fi
    else
        if [ -f "${bag_dir}/suedhoehe_gps_schnee_02/suedhoehe_gt_asl.csv" ]; then
            ros_args="${ros_args} -p path_gt:=/dataset_dir/suedhoehe_gps_schnee_02/suedhoehe_gt_asl.csv"
        fi
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
    local bin_cmd="/opt/ORB_SLAM3/Examples/Stereo-Inertial/stereo_inertial_euroc /opt/ORB_SLAM3/Vocabulary/ORBvoc.txt ${config_yaml} /dataset /dataset/timestamps.txt ${algo_sub}"

    if [ "$variant" = "klt" ]; then
        algo_sub="orbslam3_klt"
        config_yaml="/orbslam3_ws/config/EuRoC_KLT.yaml"
        out_name="orbslam3_klt_tum.txt"
        title="ORB-SLAM3 Hybrid KLT"
        docker_image="orbslam3_klt:latest"
        bin_cmd="/opt/ORB_SLAM3_KLT/Examples/Monocular/mono_euroc /opt/ORB_SLAM3_KLT/Vocabulary/ORBvoc.txt /opt/ORB_SLAM3_KLT/Examples/Monocular/EuRoC.yaml /dataset /dataset/timestamps.txt ${algo_sub}"
    fi

    local ds_dir="euroc"
    local results_dir="${REPO_ROOT}/results/euroc/${algo_sub}"
    local dataset_path="${REPO_ROOT}/datasets/MH_01_easy"

    if [ "$target_dataset" = "suedhoehe" ] || [ "$target_dataset" = "schnee" ]; then
        ds_dir="suedhoehe"
        results_dir="${REPO_ROOT}/results/suedhoehe/${algo_sub}"
        dataset_path="${REPO_ROOT}/datasets/suedhoehe_asl"
        config_yaml="/orbslam3_ws/suedhoehe_stereo_inertial.yaml"
        bin_cmd="/opt/ORB_SLAM3/Examples/Stereo-Inertial/stereo_inertial_euroc /opt/ORB_SLAM3/Vocabulary/ORBvoc.txt ${config_yaml} /dataset /dataset/timestamps.txt ${algo_sub}"
        if [ "$variant" = "klt" ]; then
            config_yaml="/orbslam3_ws/suedhoehe_mono.yaml"
            bin_cmd="/opt/ORB_SLAM3_KLT/Examples/Monocular/mono_euroc /opt/ORB_SLAM3_KLT/Vocabulary/ORBvoc.txt ${config_yaml} /dataset /dataset/timestamps.txt ${algo_sub}"
        fi
        echo "=========================================================="
        echo " [$title] Dataset: suedhoehe (Outdoor Snow Sequence)"
        echo " [NOTE] Running ORB-SLAM3 on Suedhoehe ASL dataset..."
        echo "=========================================================="
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
            -v '${REPO_ROOT}/workspace/orbslam3_ws':/orbslam3_ws \
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
          -v "${REPO_ROOT}/workspace/orbslam3_ws":/orbslam3_ws \
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
    local results_dir="${REPO_ROOT}/results/suedhoehe/kimera"
    local params_path="${REPO_ROOT}/suedhoehe_kimera_params"
    local bag_dir="${REPO_ROOT}/datasets"
    local bag_name="suedhoehe_gps_schnee_02"
    local left_topic="/camera/infra1/image_rect_raw"
    local right_topic="/camera/infra2/image_rect_raw"
    local imu_topic="/camera/imu"
    local rviz_cfg="/rviz_cfg/suedhoehe_rviz.rviz"

    if [ "$target_dataset" = "euroc" ] || [ "$target_dataset" = "euroc_MH01" ] || [ "$target_dataset" = "MH_01_easy" ]; then
        results_dir="${REPO_ROOT}/results/euroc/kimera"
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
    fi

    mkdir -p "$results_dir"

    echo "=========================================================="
    echo " [Kimera-VIO] GTSAM Smoothing Factor Graph & 3D Mesh"
    echo " Dataset: $target_dataset | Mode: $( [ "$ENABLE_GUI" = true ] && echo "Live GUI" || echo "Headless" )"
    echo "=========================================================="

    docker kill kimera_node kimera_rviz kimera_player 2>/dev/null || true
    docker rm -f kimera_node kimera_rviz kimera_player 2>/dev/null || true

    if [ "$target_dataset" = "euroc" ] || [ "$target_dataset" = "euroc_MH01" ] || [ "$target_dataset" = "MH_01_easy" ]; then
        echo "[*] Running Kimera-VIO on EuRoC MH_01_easy..."
        docker run --rm \
          --cpus="${CPUS}" --memory="${MEMORY}" \
          -v "${REPO_ROOT}/datasets/MH_01_easy":/euroc_data \
          -v "${results_dir}":/output \
          -v "${params_path}":/euroc_kimera_params \
          kimera:latest \
          bash -c "/opt/overlay_ws/build/kimera_vio/stereoVIOEuroc \
            --dataset_type=0 \
            --dataset_path=/euroc_data \
            --initial_k=50 \
            --final_k=3680 \
            --backend_type=0 \
            --left_cam_params_path=/opt/overlay_ws/src/MIT-SPARK/Kimera-VIO/params/Euroc/LeftCameraParams.yaml \
            --right_cam_params_path=/opt/overlay_ws/src/MIT-SPARK/Kimera-VIO/params/Euroc/RightCameraParams.yaml \
            --imu_params_path=/opt/overlay_ws/src/MIT-SPARK/Kimera-VIO/params/Euroc/ImuParams.yaml \
            --backend_params_path=/opt/overlay_ws/src/MIT-SPARK/Kimera-VIO/params/Euroc/regularVioParameters.yaml \
            --frontend_params_path=/euroc_kimera_params/trackerParameters.yaml \
            --vocabulary_path=/opt/overlay_ws/src/MIT-SPARK/Kimera-VIO/vocabulary/ORBvoc.yml \
            --visualize=false \
            --visualize_mesh=false \
            --visualize_point_cloud=false \
            --viz_type=0 \
            --use_lcd=0 \
            --parallel_run=0 \
            --logtostderr=1 \
            --colorlogtostderr=1 \
            --log_prefix=1 \
            --log_output=1 \
            --output_path=/output/"
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
              kimera:latest \
              bash -c "source /opt/wrapper_ws/install/setup.bash && \
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
            echo "[*] Target: Suedhoehe Outdoor Snow Benchmark (OpenVINS, Kimera-VIO)"
            run_openvins "suedhoehe"
            run_kimera "suedhoehe"
            save_gantt_chart "openvins" "suedhoehe"
            save_gantt_chart "kimera" "suedhoehe"
        elif [ "$DATASET" = "all" ]; then
            echo "[*] Target: Complete Suite (EuRoC 5-way + Suedhoehe 2-way)"
            run_cuvslam "euroc"
            run_openvins "euroc"
            run_kimera "euroc"
            run_orbslam3_variant "baseline" "euroc"
            run_orbslam3_variant "klt" "euroc"
            save_gantt_chart "cuvslam" "euroc"
            save_gantt_chart "openvins" "euroc"
            save_gantt_chart "kimera" "euroc"
            save_gantt_chart "orbslam3" "euroc"
            save_gantt_chart "orbslam3_klt" "euroc"

            run_openvins "suedhoehe"
            run_kimera "suedhoehe"
            save_gantt_chart "openvins" "suedhoehe"
            save_gantt_chart "kimera" "suedhoehe"
        else
            echo "[*] Target: EuRoC MH_01_easy 5-Way Benchmark (All 5 Algorithms)"
            run_cuvslam "euroc"
            run_openvins "euroc"
            run_kimera "euroc"
            run_orbslam3_variant "baseline" "euroc"
            run_orbslam3_variant "klt" "euroc"
            save_gantt_chart "cuvslam" "euroc"
            save_gantt_chart "openvins" "euroc"
            save_gantt_chart "kimera" "euroc"
            save_gantt_chart "orbslam3" "euroc"
            save_gantt_chart "orbslam3_klt" "euroc"
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

