#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import os
import sys

class TrajectorySaver(Node):
    def __init__(self, output_file, dataset=""):
        super().__init__('cuvslam_trajectory_saver')
        self.output_file = output_file
        self.dataset = dataset
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        self.f = open(output_file, 'w')
        self.count = 0
        self.sub = self.create_subscription(
            Odometry,
            '/visual_slam/tracking/odometry',
            self.odom_callback,
            10
        )
        self.get_logger().info(f"Recording odometry to TUM format at: {output_file} (dataset: {dataset})")

    def odom_callback(self, msg: Odometry):
        t = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        pos = msg.pose.pose.position
        ori = msg.pose.pose.orientation

        line = f"{t:.9f} {pos.x:.6f} {pos.y:.6f} {pos.z:.6f} {ori.x:.6f} {ori.y:.6f} {ori.z:.6f} {ori.w:.6f}\n"
        self.f.write(line)
        self.f.flush()
        self.count += 1
        if self.count % 100 == 0:
            self.get_logger().info(f"Recorded {self.count} poses...")

    def destroy_node(self):
        self.f.close()
        self.get_logger().info(f"Finished recording {self.count} poses.")
        super().destroy_node()

def main():
    output_path = sys.argv[1] if len(sys.argv) > 1 else "/workspaces/isaac_ros-dev/results/suedhoehe/cuvslam/cuvslam_tum.txt"
    dataset = sys.argv[2] if len(sys.argv) > 2 else ""
    rclpy.init()
    node = TrajectorySaver(output_path, dataset)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
