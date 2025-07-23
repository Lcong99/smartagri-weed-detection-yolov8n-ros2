import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2

class YoloNode(Node):
    def __init__(self):
        super().__init__('yolo_detect_node')
        self.declare_parameter('model_path', 'best.pt')
        model_path = self.get_parameter('model_path').value
        self.get_logger().info(f'🚀 Loading YOLO model from: {model_path}')

        try:
            self.model = YOLO(model_path)
            self.get_logger().info('✅ YOLO model loaded successfully')
        except Exception as e:
            self.get_logger().error(f'❌ Failed to load YOLO model: {e}')
            return

        self.bridge = CvBridge()

        self.sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10)
        self.get_logger().info('📡 Subscribed to /camera/image_raw ✅')

        self.pub_boxes = self.create_publisher(
            Float32MultiArray,
            '/yolo_detect/boxes',
            10)
        self.pub_image = self.create_publisher(
            Image,
            '/yolo_detect/image_debug',
            10)

    def image_callback(self, msg: Image):
        self.get_logger().info(f'📷 Image received at {self.get_clock().now().to_msg()}')
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        except Exception as e:
            self.get_logger().error(f'❌ CVBridge conversion failed: {e}')
            return

        try:
            results = self.model(cv_image)[0]
            self.get_logger().info(f'🧠 YOLO inference complete. {len(results.boxes)} object(s) detected.')
        except Exception as e:
            self.get_logger().error(f'❌ YOLO inference error: {e}')
            return

        boxes_data = []
        for det in results.boxes:
            x1, y1, x2, y2 = det.xyxy[0].tolist()
            conf = det.conf[0].item()
            cls = int(det.cls[0].item())
            boxes_data.extend([x1, y1, x2, y2, conf, cls])
            self.get_logger().info(f'Detected class {cls} with {conf:.2f} confidence at box ({int(x1)}, {int(y1)}, {int(x2)}, {int(y2)})')

            cv2.rectangle(cv_image,
                          (int(x1), int(y1)),
                          (int(x2), int(y2)),
                          (0, 255, 0), 2)
            cv2.putText(
                cv_image,
                f'{cls}:{conf:.2f}',
                (int(x1), int(y1) - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1)

        fa = Float32MultiArray(data=boxes_data)
        self.pub_boxes.publish(fa)
        self.get_logger().info('📦 Published detection boxes')

        try:
            debug_msg = self.bridge.cv2_to_imgmsg(cv_image, 'bgr8')
            self.pub_image.publish(debug_msg)
            self.get_logger().info('🖼️ Published annotated debug image')
        except Exception as e:
            self.get_logger().error(f'❌ Error publishing debug image: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = YoloNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('🛑 Shutting down YOLO Detect node')
    finally:
        node.destroy_node()
        rclpy.shutdown()