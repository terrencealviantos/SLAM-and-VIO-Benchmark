import launch
from launch_ros.actions import ComposableNodeContainer, Node
from launch_ros.descriptions import ComposableNode

def generate_launch_description():
    camera_info_node = Node(
        name='corridor_camera_info_publisher',
        executable='/workspaces/isaac_ros-dev/corridor_camera_info_pub.py',
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
        arguments=['--x', '0.047280', '--y', '-0.047443', '--z', '-0.068200',
                   '--qx', '-0.013355', '--qy', '-0.694797', '--qz', '0.719041', '--qw', '-0.007689',
                   '--frame-id', 'base_link',
                   '--child-frame-id', 'cam0']
    )

    tf_base_to_cam1 = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='tf_base_to_cam1',
        arguments=['--x', '-0.053697', '--y', '-0.046132', '--z', '-0.071493',
                   '--qx', '0.013494', '--qy', '0.711473', '--qz', '-0.702540', '--qw', '0.007898',
                   '--frame-id', 'base_link',
                   '--child-frame-id', 'cam1']
    )

    visual_slam_node = ComposableNode(
        name='visual_slam_node',
        package='isaac_ros_visual_slam',
        plugin='nvidia::isaac_ros::visual_slam::VisualSlamNode',
        parameters=[{
            'rectified_images': False,
            'enable_imu_fusion': False,
            'base_frame': 'base_link',
            'camera_optical_frames': [
                'cam0',
                'cam1',
            ],
        }],
        remappings=[
            ('visual_slam/image_0', '/corridor/cam0/image_mono8'),
            ('visual_slam/camera_info_0', '/visual_slam/camera_info_0'),
            ('visual_slam/image_1', '/corridor/cam1/image_mono8'),
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
