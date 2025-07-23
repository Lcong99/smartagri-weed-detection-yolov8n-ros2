#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2

# Suppose your YOLO node publishes an array of boxes on /weed/detections
from yolo_detect.msg import BoundingBoxes  # ← your custom msg

class WeedVisualizer(Node):
    def __init__(self):
        super().__init__('weed_visualizer')
        self.bridge = CvBridge()
        self.image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.on_image, 10)
        self.box_sub   = self.create_subscription(
            BoundingBoxes, '/weed/detections', self.on_boxes, 10)
        self.latest_img = None
        self.latest_boxes = []

    def on_image(self, msg: Image):
        # store the newest frame
        self.latest_img = self.bridge.imgmsg_to_cv2(msg, 'bgr8')

    def on_boxes(self, msg: BoundingBoxes):
        # each box has x_min, y_min, x_max, y_max, class_id, score
        self.latest_boxes = msg.boxes

    def spin_once(self):
        # Draw on the latest image and show it
        if self.latest_img is None:
            return

        img = self.latest_img.copy()
        for box in self.latest_boxes:
            x1, y1, x2, y2 = int(box.xmin), int(box.ymin), int(box.xmax), int(box.ymax)
            color = (0,255,0) if box.class_id == 1 else (255,0,0)
            cv2.rectangle(img, (x1,y1), (x2,y2), color, 2)
            label = f"{box.class_id}:{box.score:.2f}"
            cv2.putText(img, label, (x1, y1-5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        cv2.imshow("Weed Demo", img)
        cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    node = WeedVisualizer()
    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.1)
            node.spin_once()
    except KeyboardInterrupt:
        pass
    finally:
        cv2.destroyAllWindows()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
