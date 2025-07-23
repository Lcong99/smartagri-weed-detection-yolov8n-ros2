#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ultralytics import YOLO

class LiveYoloRqt(Node):
    def __init__(self):
        super().__init__('live_yolo_rqt')
        self.model  = YOLO('models/best.pt')
        self.bridge = CvBridge()
        self.create_subscription(
            Image,
            '/depth_cam/rgb/image_raw',
            self.cb_image,
            1
        )
        self.pub_annot = self.create_publisher(
            Image,
            '/yolo/annotated_image',
            1
        )
        self.get_logger().info('Publishing annotated on /yolo/annotated_image')

    def cb_image(self, msg: Image):
        frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        results = self.model(frame, conf=0.25, verbose=False)
        annotated = results[0].plot()
        out = self.bridge.cv2_to_imgmsg(annotated, 'bgr8')
        out.header = msg.header
        self.pub_annot.publish(out)

def main():
    rclpy.init()
    node = LiveYoloRqt()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()

