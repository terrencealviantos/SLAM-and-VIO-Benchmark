#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo, Imu
from rclpy.qos import qos_profile_sensor_data
import numpy as np

class CorridorCameraInfoPublisher(Node):
    def __init__(self):
        super().__init__('corridor_camera_info_publisher')
        
        self.pub_cam0 = self.create_publisher(CameraInfo, '/visual_slam/camera_info_0', qos_profile_sensor_data)
        self.pub_cam1 = self.create_publisher(CameraInfo, '/visual_slam/camera_info_1', qos_profile_sensor_data)
        self.pub_img0 = self.create_publisher(Image, '/corridor/cam0/image_mono8', qos_profile_sensor_data)
        self.pub_img1 = self.create_publisher(Image, '/corridor/cam1/image_mono8', qos_profile_sensor_data)
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
        self.get_logger().info('Publishing TUM-VI Corridor CameraInfo & mono8 Image synchronized...')

    def imu_callback(self, msg: Imu):
        out = Imu()
        out.header = msg.header
        out.header.frame_id = 'imu'
        out.linear_acceleration = msg.linear_acceleration
        out.angular_velocity = msg.angular_velocity
        self.pub_imu.publish(out)

    def convert_image(self, msg: Image, frame_id: str) -> Image:
        out = Image()
        out.header = msg.header
        out.header.frame_id = frame_id
        out.height = msg.height
        out.width = msg.width
        out.is_bigendian = msg.is_bigendian
        
        if msg.encoding in ['mono16', '16UC1'] or len(msg.data) == msg.height * msg.width * 2:
            img16 = np.frombuffer(msg.data, dtype=np.uint16)
            img8 = (img16 >> 8).astype(np.uint8)
            out.encoding = 'mono8'
            out.step = msg.width
            out.data = img8.tobytes()
        else:
            out.encoding = msg.encoding
            out.step = msg.step
            out.data = msg.data
        return out

    def cam0_callback(self, msg: Image):
        out_img = self.convert_image(msg, 'cam0')
        self.pub_img0.publish(out_img)

        cam0 = CameraInfo()
        cam0.header.stamp = msg.header.stamp
        cam0.header.frame_id = 'cam0'
        cam0.height = 512
        cam0.width = 512
        cam0.distortion_model = 'equidistant'
        cam0.d = [0.0034823894022493434, 0.0007150348452162257, -0.0020532361418706202, 0.00020293673591811182]
        cam0.k = [190.978477, 0.0, 254.931706, 0.0, 190.973307, 256.897443, 0.0, 0.0, 1.0]
        cam0.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        cam0.p = [190.978477, 0.0, 254.931706, 0.0, 0.0, 190.973307, 256.897443, 0.0, 0.0, 0.0, 1.0, 0.0]
        self.pub_cam0.publish(cam0)

    def cam1_callback(self, msg: Image):
        out_img = self.convert_image(msg, 'cam1')
        self.pub_img1.publish(out_img)

        cam1 = CameraInfo()
        cam1.header.stamp = msg.header.stamp
        cam1.header.frame_id = 'cam1'
        cam1.height = 512
        cam1.width = 512
        cam1.distortion_model = 'equidistant'
        cam1.d = [0.0034003170790442797, 0.001766278153469831, -0.00266312569781606, 0.0003299517423931039]
        cam1.k = [190.442370, 0.0, 252.599497, 0.0, 190.434438, 254.917231, 0.0, 0.0, 1.0]
        cam1.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        # Tx = -fx * baseline = -190.442370 * 0.101063 = -19.2466
        cam1.p = [190.442370, 0.0, 252.599497, -19.2466, 0.0, 190.434438, 254.917231, 0.0, 0.0, 0.0, 1.0, 0.0]
        self.pub_cam1.publish(cam1)

def main(args=None):
    rclpy.init(args=args)
    node = CorridorCameraInfoPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
