#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image

class TestYolo(Node):
    def __init__(self):
        super().__init__('test_yolo')
        print("🚀 Starting test YOLO node")
        self.sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10)
        print("📡 Subscribed to /camera/image_raw")

    def image_callback(self, msg):
        print(f"📷 GOT IMAGE! Size: {len(msg.data)} bytes")

def main():
    rclpy.init()
    node = TestYolo()
    print("🔄 Spinning node...")
    rclpy.spin(node)

if __name__ == '__main__':
    main()
