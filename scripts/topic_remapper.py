#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image

class TopicRemapper(Node):
    def __init__(self):
        super().__init__('topic_remapper')
        self.subscription = self.create_subscription(
            Image,
            '/depth_cam/rgb/image_raw',
            self.image_callback,
            10)
        self.publisher = self.create_publisher(Image, '/camera/image_raw', 10)
        self.get_logger().info("Topic remapper started")

    def image_callback(self, msg):
        # Simply republish the message to the new topic
        self.publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    remapper = TopicRemapper()
    rclpy.spin(remapper)
    remapper.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
