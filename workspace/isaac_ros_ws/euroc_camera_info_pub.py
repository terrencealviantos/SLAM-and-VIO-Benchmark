#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo, Imu
from rclpy.qos import qos_profile_sensor_data

class EurocCameraInfoPublisher(Node):
    def __init__(self):
        super().__init__('euroc_camera_info_publisher')
        
        self.pub_cam0 = self.create_publisher(CameraInfo, '/visual_slam/camera_info_0', qos_profile_sensor_data)
        self.pub_cam1 = self.create_publisher(CameraInfo, '/visual_slam/camera_info_1', qos_profile_sensor_data)
        self.pub_imu = self.create_publisher(Imu, '/visual_slam/imu_flu', qos_profile_sensor_data)
        
        self.sub_img0 = self.create_subscription(
            Image,
            '/cam0/image_raw',
            self.cam0_callback,
            qos_profile_sensor_data
        )
        self.sub_img1 = self.create_subscription(
            Image,
            '/cam1/image_raw',
            self.cam1_callback,
            qos_profile_sensor_data
        )
        self.sub_imu = self.create_subscription(
            Imu,
            '/imu0',
            self.imu_callback,
            qos_profile_sensor_data
        )
        self.get_logger().info('Publishing EuRoC CameraInfo & FLU IMU synchronized to image/IMU stamps...')

    def imu_callback(self, msg: Imu):
        # Convert EuRoC sensor frame (X=Up, Y=Right, Z=Forward)
        # to ROS canonical FLU frame (X=Forward, Y=Left, Z=Up)
        out = Imu()
        out.header = msg.header
        out.header.frame_id = 'base_link'
        out.linear_acceleration.x = msg.linear_acceleration.z
        out.linear_acceleration.y = -msg.linear_acceleration.y
        out.linear_acceleration.z = msg.linear_acceleration.x
        out.angular_velocity.x = msg.angular_velocity.z
        out.angular_velocity.y = -msg.angular_velocity.y
        out.angular_velocity.z = msg.angular_velocity.x
        self.pub_imu.publish(out)

    def cam0_callback(self, msg: Image):
        cam0 = CameraInfo()
        cam0.header.stamp = msg.header.stamp
        cam0.header.frame_id = 'cam0'
        cam0.height = 480
        cam0.width = 752
        cam0.distortion_model = 'plumb_bob'
        cam0.d = [-0.28340811, 0.07395907, 0.00019359, 1.76187114e-05, 0.0]
        cam0.k = [458.654, 0.0, 367.215, 0.0, 457.296, 248.375, 0.0, 0.0, 1.0]
        cam0.r = [
            0.99996335, -0.00362622,  0.00775510,
            0.00368080,  0.99996847, -0.00703572,
           -0.00772935,  0.00706400,  0.99994518
        ]
        cam0.p = [
            422.494977, 0.0, 364.454346, 0.0,
            0.0, 422.494977, 256.924709, 0.0,
            0.0, 0.0, 1.0, 0.0
        ]
        self.pub_cam0.publish(cam0)

    def cam1_callback(self, msg: Image):
        cam1 = CameraInfo()
        cam1.header.stamp = msg.header.stamp
        cam1.header.frame_id = 'cam1'
        cam1.height = 480
        cam1.width = 752
        cam1.distortion_model = 'plumb_bob'
        cam1.d = [-0.28368365, 0.07451284, -0.00010473, -3.55590700e-05, 0.0]
        cam1.k = [457.587, 0.0, 379.999, 0.0, 456.134, 255.238, 0.0, 0.0, 1.0]
        cam1.r = [
            0.99996635, -0.00142272,  0.00807956,
            0.00136572,  0.99997418,  0.00705550,
           -0.00808938, -0.00704423,  0.99994247
        ]
        # Tx = -fx_rect * baseline = -422.494977 * 0.1100778 = -46.507336
        cam1.p = [
            422.494977, 0.0, 364.454346, -46.507336,
            0.0, 422.494977, 256.924709, 0.0,
            0.0, 0.0, 1.0, 0.0
        ]
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
