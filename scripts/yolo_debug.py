#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray
from cv_bridge import CvBridge

print("🚀 Starting YOLO debug node...")

class YoloDebugNode(Node):
    def __init__(self):
        super().__init__('yolo_debug_node')
        print("📝 Node initialized")
        
        # Test model loading
        print("🔍 Testing model loading...")
        try:
            from ultralytics import YOLO
            print("✅ Ultralytics imported successfully")
            self.model = YOLO('best.pt')
            print("✅ YOLO model loaded successfully")
        except Exception as e:
            print(f"❌ Model loading failed: {e}")
            return
            
        self.bridge = CvBridge()
        print("✅ CVBridge initialized")
        
        # Create subscription
        self.sub = self.create_subscription(
            Image,
            '/camera/image_raw',
            self.image_callback,
            10)
        print("✅ Subscribed to /camera/image_raw")
        
        # Create publishers
        self.pub_boxes = self.create_publisher(Float32MultiArray, '/yolo_detect/boxes', 10)
        self.pub_image = self.create_publisher(Image, '/yolo_detect/image_debug', 10)
        print("✅ Publishers created")
        
        print("🎯 YOLO debug node ready!")

    def image_callback(self, msg):
        print(f"📷 Image received! Size: {len(msg.data)} bytes, {msg.width}x{msg.height}")
        
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            print(f"✅ Image converted to OpenCV: {cv_image.shape}")
        except Exception as e:
            print(f"❌ CVBridge conversion failed: {e}")
            return
            
        try:
            print("🧠 Running YOLO inference...")
            results = self.model(cv_image)[0]
            print(f"✅ YOLO inference complete. {len(results.boxes)} objects detected.")
        except Exception as e:
            print(f"❌ YOLO inference error: {e}")
            return
            
        print("📦 Publishing results...")
        # Simple publish test
        fa = Float32MultiArray(data=[1.0, 2.0, 3.0])  # Test data
        self.pub_boxes.publish(fa)
        print("✅ Results published!")

def main(args=None):
    print("🔧 Initializing ROS2...")
    rclpy.init(args=args)
    print("✅ ROS2 initialized")
    
    node = YoloDebugNode()
    
    try:
        print("🔄 Starting node spin...")
        rclpy.spin(node)
    except KeyboardInterrupt:
        print('🛑 Shutting down')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
