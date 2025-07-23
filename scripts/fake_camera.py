#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np

class FakeCamera(Node):
    def __init__(self):
        super().__init__('fake_camera')
        self.publisher = self.create_publisher(Image, '/camera/image_raw', 10)
        self.timer = self.create_timer(0.1, self.timer_callback)  # 10 FPS
        self.bridge = CvBridge()
        self.counter = 0
        print("🎬 Fake camera started - publishing test images")

    def timer_callback(self):
        # Create a simple test image
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add some moving content
        cv2.circle(img, (320 + int(100 * np.sin(self.counter * 0.1)), 240), 50, (0, 255, 0), -1)
        cv2.putText(img, f"Frame: {self.counter}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Convert to ROS message
        msg = self.bridge.cv2_to_imgmsg(img, 'bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'camera'
        
        self.publisher.publish(msg)
        print(f"📷 Published frame {self.counter}")
        self.counter += 1

def main():
    rclpy.init()
    node = FakeCamera()
    rclpy.spin(node)

if __name__ == '__main__':
    main()
