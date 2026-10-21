#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo

class EurocCameraInfoPublisher(Node):
    def __init__(self):
        super().__init__('euroc_camera_info_publisher')
        
        self.pub_cam0 = self.create_publisher(CameraInfo, '/visual_slam/camera_info_0', 10)
        self.pub_cam1 = self.create_publisher(CameraInfo, '/visual_slam/camera_info_1', 10)
        
        # Publish at 20 Hz (EuRoC camera rate)
        self.timer = self.create_timer(1.0 / 20.0, self.timer_callback)
        self.get_logger().info('Publishing EuRoC CameraInfo on /visual_slam/camera_info_0 and _1 at 20Hz...')

    def timer_callback(self):
        now = self.get_clock().now().to_msg()

        # Left camera info (cam0)
        cam0 = CameraInfo()
        cam0.header.stamp = now
        cam0.header.frame_id = 'cam0'
        cam0.height = 480
        cam0.width = 752
        cam0.distortion_model = 'plumb_bob'
        cam0.d = [-0.28340811, 0.07395907, 0.00019359, 1.76187114e-05, 0.0]
        cam0.k = [458.654, 0.0, 367.215, 0.0, 457.296, 248.375, 0.0, 0.0, 1.0]
        cam0.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        cam0.p = [458.654, 0.0, 367.215, 0.0, 0.0, 457.296, 248.375, 0.0, 0.0, 0.0, 1.0, 0.0]

        # Right camera info (cam1)
        cam1 = CameraInfo()
        cam1.header.stamp = now
        cam1.header.frame_id = 'cam1'
        cam1.height = 480
        cam1.width = 752
        cam1.distortion_model = 'plumb_bob'
        cam1.d = [-0.28368365, 0.07451284, -0.00010473, -3.55590700e-05, 0.0]
        cam1.k = [457.587, 0.0, 379.999, 0.0, 456.134, 255.238, 0.0, 0.0, 1.0]
        cam1.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        # Tx = -fx * baseline = -458.654 * 0.11007 = -50.484
        cam1.p = [458.654, 0.0, 367.215, -50.484, 0.0, 457.296, 248.375, 0.0, 0.0, 0.0, 1.0, 0.0]

        self.pub_cam0.publish(cam0)
        self.pub_cam1.publish(cam1)

def main(args=None):
    rclpy.init(args=args)
    node = EurocCameraInfoPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
