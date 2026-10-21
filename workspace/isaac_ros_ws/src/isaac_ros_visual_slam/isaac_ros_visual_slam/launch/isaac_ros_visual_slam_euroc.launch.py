import launch
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    camera_info_node = Node(
        name='euroc_camera_info_publisher',
        executable='/workspaces/isaac_ros-dev/euroc_camera_info_pub.py',
        output='screen'
    )

    tf_cam0_to_cam1 = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_cam0_to_cam1',
        arguments=['--x', '-0.11007', '--y', '0.0', '--z', '0.0',
                   '--roll', '0.0', '--pitch', '0.0', '--yaw', '0.0',
                   '--frame-id', 'cam0',
                   '--child-frame-id', 'cam1']
    )

    tf_cam0_to_imu = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_cam0_to_imu',
        arguments=['--x', '-0.02164', '--y', '-0.06468', '--z', '0.00981',
                   '--roll', '0.0', '--pitch', '0.0', '--yaw', '0.0',
                   '--frame-id', 'cam0',
                   '--child-frame-id', 'imu']
    )

    visual_slam_node = ComposableNode(
        name='visual_slam_node',
        package='isaac_ros_visual_slam',
        plugin='nvidia::isaac_ros::visual_slam::VisualSlamNode',
        parameters=[{
            'enable_image_denoising': False,
            'rectified_images': False,
            'enable_imu_fusion': True,
            'enable_localization_n_mapping': True,
            'enable_slam_visualization': True,
            'enable_landmarks_view': True,
            'enable_observations_view': True,
            'override_publishing_stamp': False,
            'image_qos': 'SENSOR_DATA',
            'imu_qos': 'SENSOR_DATA',
            'sync_matching_threshold_ms': 25.0,
            'image_jitter_threshold_ms': 100.0,
            'gyro_noise_density': 0.00016968,
            'gyro_random_walk': 1.9393e-05,
            'accel_noise_density': 0.002,
            'accel_random_walk': 0.003,
            'calibration_frequency': 200.0,
            'base_frame': 'cam0',
            'imu_frame': 'imu',
            'camera_optical_frames': [
                'cam0',
                'cam1',
            ],
        }],
        remappings=[
            ('visual_slam/image_0', '/cam0/image_raw'),
            ('visual_slam/camera_info_0', '/visual_slam/camera_info_0'),
            ('visual_slam/image_1', '/cam1/image_raw'),
            ('visual_slam/camera_info_1', '/visual_slam/camera_info_1'),
            ('visual_slam/imu', '/imu0')
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
        tf_cam0_to_cam1,
        tf_cam0_to_imu,
        visual_slam_launch_container
    ])
