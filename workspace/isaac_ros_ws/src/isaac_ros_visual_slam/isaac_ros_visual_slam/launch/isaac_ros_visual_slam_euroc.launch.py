import launch
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    camera_info_node = Node(
        name='euroc_camera_info_publisher',
        executable='/workspaces/isaac_ros-dev/euroc_camera_info_pub.py',
        output='screen'
    )

    tf_base_to_imu = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_base_to_imu',
        arguments=['--x', '0.0', '--y', '0.0', '--z', '0.0',
                   '--roll', '0.0', '--pitch', '0.0', '--yaw', '0.0',
                   '--frame-id', 'base_link',
                   '--child-frame-id', 'imu']
    )

    tf_base_to_cam0 = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_base_to_cam0',
        arguments=['--x', '0.009811', '--y', '0.064677', '--z', '-0.021640',
                   '--qx', '0.496249', '--qy', '-0.501664', '--qz', '0.511097', '--qw', '-0.490764',
                   '--frame-id', 'base_link',
                   '--child-frame-id', 'cam0']
    )

    tf_base_to_cam1 = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_base_to_cam1',
        arguments=['--x', '0.007862', '--y', '-0.045369', '--z', '-0.019844',
                   '--qx', '0.492290', '--qy', '-0.498536', '--qz', '0.513961', '--qw', '-0.494930',
                   '--frame-id', 'base_link',
                   '--child-frame-id', 'cam1']
    )

    visual_slam_node = ComposableNode(
        name='visual_slam_node',
        package='isaac_ros_visual_slam',
        plugin='nvidia::isaac_ros::visual_slam::VisualSlamNode',
        parameters=[{
            'rectified_images': False,
            'enable_imu_fusion': True,
            'gyro_noise_density': 0.00016968,
            'gyro_random_walk': 1.9393e-05,
            'accel_noise_density': 0.002,
            'accel_random_walk': 0.003,
            'calibration_frequency': 200.0,
            'base_frame': 'base_link',
            'imu_frame': 'base_link',
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
            ('visual_slam/imu', '/visual_slam/imu_flu')
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
        tf_base_to_imu,
        tf_base_to_cam0,
        tf_base_to_cam1,
        visual_slam_launch_container
    ])
