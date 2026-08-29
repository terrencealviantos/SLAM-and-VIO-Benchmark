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
        suedhoehe|euroc|euroc_MH01)
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
    docker run --rm --entrypoint "" \
      -v "${REPO_ROOT}/results":/results \
      -v "${REPO_ROOT}/datasets":/datasets \
      slam-base:latest \
      bash -c "source /opt/ros/humble/setup.bash && \
        if [ -f /results/euroc/ground_truth.txt ] && [ -f /results/euroc/orb_slam3.txt ]; then \
          echo '=== EuRoC MH_01 APE Evaluation ==='; \
          evo_ape tum /results/euroc/ground_truth.txt /results/euroc/orb_slam3.txt -a --plot --plot_mode xy --save_results /results/euroc/ape_orbslam3.zip 2>/dev/null || true; \
        fi"
    echo "[✔] Evaluation completed. Results saved in ${REPO_ROOT}/results/"
    exit 0
fi

# Fallback defaults
ALGORITHM="${ALGORITHM:-cuvslam}"
DATASET="${DATASET:-suedhoehe}"

# Allow X11 for Docker GUI
xhost +local:root 2>/dev/null || xhost + 2>/dev/null || true

# ------------------------------------------------------------------------------
# 1. RUN CUVSLAM (NVIDIA Isaac ROS GPU-Accelerated)
# ------------------------------------------------------------------------------
run_cuvslam() {
    local target_dataset="$1"
    local results_dir="${REPO_ROOT}/results/suedhoehe/cuvslam"
    local bag_dir="${REPO_ROOT}/datasets"
    local bag_name="suedhoehe_gps_schnee_02"
    local rviz_cfg="/rviz_cfg/suedhoehe_rviz.rviz"

    mkdir -p "$results_dir"

    echo "=========================================================="
    echo " [cuVSLAM] NVIDIA Isaac ROS GPU-Accelerated SLAM"
    echo " Dataset: $target_dataset | Mode: $( [ "$ENABLE_GUI" = true ] && echo "Live GUI" || echo "Headless" )"
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
                     (python3 /scripts/cuvslam_save_trajectory.py /results/cuvslam_tum.txt &) && \
                     ros2 launch isaac_ros_visual_slam isaac_ros_visual_slam_suedhoehe.launch.py'"

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
                   ros2 launch isaac_ros_visual_slam isaac_ros_visual_slam_suedhoehe.launch.py"

        sleep 4
        docker exec -d cuvslam_node bash -c "source /opt/ros/humble/setup.bash && python3 /scripts/cuvslam_save_trajectory.py /results/cuvslam_tum.txt"
        sleep 1

        docker run --rm --name cuvslam_player \
          --net=host --ipc=host \
          -v "${bag_dir}":/dataset_dir \
          slam-base:latest \
          bash -c "source /opt/ros/humble/setup.bash && ros2 bag play /dataset_dir/${bag_name}"

        sleep 3
        docker kill cuvslam_node 2>/dev/null || true
        docker rm -f cuvslam_node 2>/dev/null || true
        echo "[✔] cuVSLAM run finished: ${results_dir}/cuvslam_tum.txt"
    fi
}

# ------------------------------------------------------------------------------
# 2. RUN OPENVINS (MSCKF Filter)
# ------------------------------------------------------------------------------
run_openvins() {
    local target_dataset="$1"
    local results_dir="${REPO_ROOT}/results/suedhoehe/openvins"
    local catkin_ws="${REPO_ROOT}/workspace/catkin_ws"
    local bag_dir="${REPO_ROOT}/datasets"
    local bag_name="suedhoehe_gps_schnee_02"
    local config_path="/catkin_ws/src/open_vins/config/suedhoehe/estimator_config.yaml"
    local rviz_cfg="/rviz_cfg/suedhoehe_rviz.rviz"

    if [ "$target_dataset" = "euroc" ] || [ "$target_dataset" = "euroc_MH01" ]; then
        results_dir="${REPO_ROOT}/results/euroc/openvins"
        config_path="/catkin_ws/src/open_vins/config/euroc_mav/estimator_config.yaml"
        bag_name="MH_01_easy"
        rviz_cfg="/rviz_cfg/euroc_rviz.rviz"
    fi

    mkdir -p "$results_dir"

    echo "=========================================================="
    echo " [OpenVINS] MSCKF Filter Sliding-Window VIO"
    echo " Dataset: $target_dataset | Mode: $( [ "$ENABLE_GUI" = true ] && echo "Live GUI" || echo "Headless" )"
    echo "=========================================================="

    if [ "$ENABLE_GUI" = true ]; then
        launch_terminal "[1] OpenVINS MSCKF Node" \
          "docker run --rm --name openvins_node --entrypoint '' \
            --cpus=${CPUS} --memory=${MEMORY} \
            --net=host --ipc=host \
            -v '${catkin_ws}':/catkin_ws \
            -v '${results_dir}':/results \
            slam-base:latest \
            bash -c 'source /opt/ros/humble/setup.bash && source /catkin_ws/install/setup.bash && ros2 run open_vins_eval run_subscribe_msckf --ros-args -p sys_config_path:=${config_path}'"

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
            bash -c 'source /opt/ros/humble/setup.bash && ros2 bag play /dataset_dir/${bag_name} --clock 200'"

    else
        docker run --rm --entrypoint "" \
          --cpus="${CPUS}" --memory="${MEMORY}" \
          -v "${catkin_ws}":/catkin_ws \
          -v "${bag_dir}":/dataset_dir \
          -v "${results_dir}":/results \
          slam-base:latest \
          bash -c "source /opt/ros/humble/setup.bash && \
                   source /catkin_ws/install/setup.bash && \
                   ros2 run open_vins_eval run_subscribe_msckf --ros-args -p sys_config_path:=${config_path} & \
                   OV_PID=\$! && sleep 3 && \
                   ros2 bag play /dataset_dir/${bag_name} --clock 200 && sleep 3 && \
                   cp /tmp/ov_estimate.txt /results/openvins_tum.txt 2>/dev/null || true && \
                   kill \$OV_PID 2>/dev/null || true"

        echo "[✔] OpenVINS run finished: ${results_dir}/openvins_tum.txt"
    fi
}

# ------------------------------------------------------------------------------
# 3. RUN ORB-SLAM3 (Baseline & Hybrid KLT)
# ------------------------------------------------------------------------------
run_orbslam3_variant() {
    local variant="$1" # "baseline" or "klt"
    local target_dataset="$2"
    local results_dir="${REPO_ROOT}/results/euroc/orbslam3"
    local config_yaml="/orbslam3_ws/config/EuRoC.yaml"
    local out_name="orbslam3_raw.txt"
    local title="ORB-SLAM3 Baseline"

    if [ "$variant" = "klt" ]; then
        results_dir="${REPO_ROOT}/results/orbslam3_klt"
        config_yaml="/orbslam3_ws/config/EuRoC_KLT.yaml"
        out_name="orbslam3_klt_raw.txt"
        title="ORB-SLAM3 Hybrid KLT"
    fi

    mkdir -p "$results_dir"
    local dataset_path="${REPO_ROOT}/datasets/MH_01_easy/mav0"

    echo "=========================================================="
    echo " [$title] Stereo-Inertial SLAM"
    echo " Dataset: $target_dataset | Mode: $( [ "$ENABLE_GUI" = true ] && echo "Pangolin 3D GUI" || echo "Headless" )"
    echo "=========================================================="

    if [ "$ENABLE_GUI" = true ]; then
        launch_terminal "$title [Pangolin 3D GUI]" \
          "docker run --rm --entrypoint '' -it \
            --cpus=${CPUS} --memory=${MEMORY} \
            --net=host --ipc=host \
            -e DISPLAY=${DISPLAY} -e QT_X11_NO_MITSHM=1 -v /tmp/.X11-unix:/tmp/.X11-unix \
            -v '${REPO_ROOT}/workspace/orbslam3_ws':/orbslam3_ws \
            -v '${dataset_path}':/dataset \
            -v '${results_dir}':/results \
            slam-base:latest \
            bash -c 'source /opt/ros/humble/setup.bash && \
                     if [ -f /dataset/timestamps.txt ]; then \
                       /opt/ORB_SLAM3/Examples/Stereo-Inertial/stereo_inertial_euroc \
                         /opt/ORB_SLAM3/Vocabulary/ORBvoc.txt \
                         ${config_yaml} \
                         /dataset /dataset/timestamps.txt /results/${out_name}; \
                     fi'"
    else
        docker run --rm --entrypoint "" \
          --cpus="${CPUS}" --memory="${MEMORY}" \
          -v "${REPO_ROOT}/workspace/orbslam3_ws":/orbslam3_ws \
          -v "${dataset_path}":/dataset \
          -v "${results_dir}":/results \
          slam-base:latest \
          bash -c "source /opt/ros/humble/setup.bash && \
                   if [ -f /dataset/timestamps.txt ]; then \
                     /opt/ORB_SLAM3/Examples/Stereo-Inertial/stereo_inertial_euroc \
                       /opt/ORB_SLAM3/Vocabulary/ORBvoc.txt \
                       ${config_yaml} \
                       /dataset /dataset/timestamps.txt /results/${out_name}; \
                   fi"

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

    if [ "$target_dataset" = "euroc" ] || [ "$target_dataset" = "euroc_MH01" ]; then
        results_dir="${REPO_ROOT}/results/euroc/kimera"
        params_path="/opt/overlay_ws/src/MIT-SPARK/Kimera-VIO/params/Euroc"
        bag_name="MH_01_easy"
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
                       log_output:=true \
                       log_output_path:=/output/ \
                       cam_topic.left:=${left_topic} \
                       cam_topic.right:=${right_topic} \
                       imu_topic:=${imu_topic}'"

        sleep 4

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
                     log_output:=true \
                     log_output_path:=/output/ \
                     cam_topic.left:=${left_topic} \
                     cam_topic.right:=${right_topic} \
                     imu_topic:=${imu_topic}"

        sleep 4
        docker run --rm --name kimera_player --entrypoint "" \
          --net=host --ipc=host \
          -v "${bag_dir}":/dataset_dir \
          slam-base:latest \
          bash -c "source /opt/ros/humble/setup.bash && ros2 bag play /dataset_dir/${bag_name}"

        sleep 3
        docker kill kimera_node 2>/dev/null || true
        docker rm -f kimera_node 2>/dev/null || true

        docker run --rm -v "${results_dir}":/output slam-base:latest chmod -R 777 /output 2>/dev/null || true
        python3 "${SCRIPTS_DIR}/convert_kimera_to_tum.py" "${results_dir}/traj_vio.csv" "${results_dir}/kimera_tum.txt" 2>/dev/null || true

        echo "[✔] Kimera-VIO run finished: ${results_dir}/kimera_tum.txt"
    fi
}

# ------------------------------------------------------------------------------
# DISPATCHER
# ------------------------------------------------------------------------------
case "$ALGORITHM" in
    cuvslam)
        run_cuvslam "$DATASET"
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
        echo " Running ALL 5 Algorithms Sequentially..."
        echo "=========================================================="
        run_cuvslam "suedhoehe"
        run_openvins "suedhoehe"
        run_kimera "suedhoehe"
        run_orbslam3_variant "baseline" "euroc"
        run_orbslam3_variant "klt" "euroc"
        echo "[✔] All benchmark runs complete!"
        ;;
    *)
        echo "[ERROR] Unknown algorithm: '$ALGORITHM'"
        show_help
        exit 1
        ;;
esac
