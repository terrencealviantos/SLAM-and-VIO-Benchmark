#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo

class SuedhoeheCameraInfoPublisher(Node):
    def __init__(self):
        super().__init__('suedhoehe_camera_info_publisher')
        
        self.pub_cam0 = self.create_publisher(CameraInfo, '/visual_slam/camera_info_0', 10)
        self.pub_cam1 = self.create_publisher(CameraInfo, '/visual_slam/camera_info_1', 10)
        
        # Publish at 30 Hz
        self.timer = self.create_timer(1.0 / 30.0, self.timer_callback)
        self.get_logger().info('Publishing Suedhoehe CameraInfo on /visual_slam/camera_info_0 and _1 at 30Hz...')

    def timer_callback(self):
        now = self.get_clock().now().to_msg()

        # Left camera info
        cam0 = CameraInfo()
        cam0.header.stamp = now
        cam0.header.frame_id = 'camera_infra1_optical_frame'
        cam0.height = 480
        cam0.width = 848
        cam0.distortion_model = 'plumb_bob'
        cam0.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        cam0.k = [416.85223, 0.0, 421.02459, 0.0, 414.92069, 237.76181, 0.0, 0.0, 1.0]
        cam0.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        cam0.p = [416.85223, 0.0, 421.02459, 0.0, 0.0, 414.92069, 237.76181, 0.0, 0.0, 0.0, 1.0, 0.0]

        # Right camera info
        cam1 = CameraInfo()
        cam1.header.stamp = now
        cam1.header.frame_id = 'camera_infra2_optical_frame'
        cam1.height = 480
        cam1.width = 848
        cam1.distortion_model = 'plumb_bob'
        cam1.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        cam1.k = [416.85223, 0.0, 421.02459, 0.0, 414.92069, 237.76181, 0.0, 0.0, 1.0]
        cam1.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        # Tx = -fx * baseline = -416.85223 * 0.0950000000 = -39.60096185
        cam1.p = [416.85223, 0.0, 421.02459, -39.60096185, 0.0, 414.92069, 237.76181, 0.0, 0.0, 0.0, 1.0, 0.0]

        self.pub_cam0.publish(cam0)
        self.pub_cam1.publish(cam1)

def main(args=None):
    rclpy.init(args=args)
    node = SuedhoeheCameraInfoPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
