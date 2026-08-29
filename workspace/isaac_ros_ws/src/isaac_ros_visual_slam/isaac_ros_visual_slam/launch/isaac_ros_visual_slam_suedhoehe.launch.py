import launch
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    # Camera Info publisher node
    camera_info_node = Node(
        name='suedhoehe_camera_info_publisher',
        executable='/workspaces/isaac_ros-dev/suedhoehe_camera_info_pub.py',
        output='screen'
    )

    # Static transforms between Left camera, Right camera, and IMU
    tf_cam1_to_cam2 = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_cam1_to_cam2',
        arguments=['--x', '-0.095', '--y', '0.0', '--z', '0.0',
                   '--roll', '0.0', '--pitch', '0.0', '--yaw', '0.0',
                   '--frame-id', 'camera_infra1_optical_frame',
                   '--child-frame-id', 'camera_infra2_optical_frame']
    )

    tf_cam1_to_imu = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_cam1_to_imu',
        arguments=['--x', '-0.006', '--y', '0.005', '--z', '0.012',
                   '--roll', '0.0', '--pitch', '0.0', '--yaw', '0.0',
                   '--frame-id', 'camera_infra1_optical_frame',
                   '--child-frame-id', 'camera_imu_optical_frame']
    )

    visual_slam_node = ComposableNode(
        name='visual_slam_node',
        package='isaac_ros_visual_slam',
        plugin='nvidia::isaac_ros::visual_slam::VisualSlamNode',
        parameters=[{
            'enable_image_denoising': False,
            'rectified_images': True,
            'enable_imu_fusion': True,
            'enable_localization_n_mapping': True,
            'enable_slam_visualization': True,
            'enable_landmarks_view': True,
            'enable_observations_view': True,
            'override_publishing_stamp': False,
            'image_qos': 'SENSOR_DATA',
            'imu_qos': 'SENSOR_DATA',
            'sync_matching_threshold_ms': 15.0,
            'image_jitter_threshold_ms': 100.0,
            'gyro_noise_density': 0.000244,
            'gyro_random_walk': 0.000019393,
            'accel_noise_density': 0.001862,
            'accel_random_walk': 0.003,
            'calibration_frequency': 200.0,
            'base_frame': 'camera_infra1_optical_frame',
            'imu_frame': 'camera_imu_optical_frame',
            'camera_optical_frames': [
                'camera_infra1_optical_frame',
                'camera_infra2_optical_frame',
            ],
        }],
        remappings=[
            ('visual_slam/image_0', '/camera/infra1/image_rect_raw'),
            ('visual_slam/camera_info_0', '/visual_slam/camera_info_0'),
            ('visual_slam/image_1', '/camera/infra2/image_rect_raw'),
            ('visual_slam/camera_info_1', '/visual_slam/camera_info_1'),
            ('visual_slam/imu', '/camera/imu')
        ]
    )

    visual_slam_launch_container = ComposableNodeContainer(
        name='visual_slam_launch_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container',
        composable_node_descriptions=[visual_slam_node],
        output='screen'
    )

    return launch.LaunchDescription([
        camera_info_node,
        tf_cam1_to_cam2,
        tf_cam1_to_imu,
        visual_slam_launch_container
    ])
