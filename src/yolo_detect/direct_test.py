#!/usr/bin/env python3
"""
Fast YOLOv8n test using your local model
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2
import torch
import time
import os

def main():
    print("🚀 YOLOv8n Fast Test")
    print("=" * 30)
    
    # Model path
    model_path = "/home/ubuntu/ros2_ws/src/yolo_detect/yolov8n.pt"
    camera_topic = '/depth_cam/rgb/image_raw'
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found at: {model_path}")
        print("Downloading YOLOv8n...")
        model_path = 'yolov8n.pt'  # Will auto-download
    
    print(f"📁 Model: {model_path}")
    print(f"📷 Camera: {camera_topic}")
    
    # Fix PyTorch loading
    original_load = torch.load
    def patched_load(*args, **kwargs):
        kwargs['weights_only'] = False
        return original_load(*args, **kwargs)
    torch.load = patched_load
    
    class YOLOv8nFastDetector(Node):
        def __init__(self):
            super().__init__('yolov8n_fast_detector')
            self.bridge = CvBridge()
            
            print("🔄 Loading YOLOv8n model...")
            self.model = YOLO(model_path)
            self.model.to('cpu')
            print("✅ YOLOv8n loaded!")
            
            # Optimized settings for speed
            self.resize_width = 320
            self.skip_frames = 2  # Process every 2nd frame
            self.conf_threshold = 0.5
            
            print(f"⚡ Settings: {self.resize_width}px, skip {self.skip_frames}, conf {self.conf_threshold}")
            
            self.pub = self.create_publisher(Image, '/weed_detect/visualization', 1)
            self.sub = self.create_subscription(Image, camera_topic, self.callback, 1)
            
            self.counter = 0
            self.last_time = time.time()
            self.fps_history = []
            self.total_detections = 0
            
            print("🏃‍♂️ Fast detector ready!")
            
        def callback(self, msg):
            self.counter += 1
            
            # Skip frames for speed
            if self.counter % self.skip_frames != 0:
                return
                
            start_time = time.time()
            
            try:
                # Convert image
                img = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
                original_height, original_width = img.shape[:2]
                
                # Resize for speed (maintain aspect ratio)
                if original_width > self.resize_width:
                    scale = self.resize_width / original_width
                    new_width = self.resize_width
                    new_height = int(original_height * scale)
                    small_img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_NEAREST)
                else:
                    small_img = img
                    scale = 1.0
                
                # Run YOLOv8n inference
                results = self.model(small_img, conf=self.conf_threshold, verbose=False)[0]
                
                # Process detections
                current_detections = 0
                if results.boxes is not None and len(results.boxes) > 0:
                    for box in results.boxes:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        
                        # Scale back to original image size
                        if scale != 1.0:
                            x1 = int(x1 / scale)
                            x2 = int(x2 / scale)
                            y1 = int(y1 / scale)
                            y2 = int(y2 / scale)
                        else:
                            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        
                        conf = box.conf[0].item()
                        cls = int(box.cls[0].item())
                        
                        # Draw bounding box
                        color = (0, 255, 0)  # Green
                        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
                        
                        # Draw label
                        label = f'Obj {conf:.2f}'
                        cv2.putText(img, label, (x1, y1-5), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                        
                        current_detections += 1
                
                self.total_detections += current_detections
                
                # Calculate FPS
                current_time = time.time()
                fps = 1.0 / (current_time - self.last_time)
                self.last_time = current_time
                self.fps_history.append(fps)
                
                # Keep only last 10 FPS values
                if len(self.fps_history) > 10:
                    self.fps_history.pop(0)
                
                avg_fps = sum(self.fps_history) / len(self.fps_history)
                process_time = (time.time() - start_time) * 1000
                
                # Add performance overlay
                cv2.rectangle(img, (5, 5), (300, 120), (0, 0, 0), -1)  # Black background
                cv2.rectangle(img, (5, 5), (300, 120), (0, 255, 0), 2)  # Green border
                
                cv2.putText(img, f'FPS: {avg_fps:.1f}', (15, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.putText(img, f'Detections: {current_detections}', (15, 55), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.putText(img, f'Process: {process_time:.1f}ms', (15, 80), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                cv2.putText(img, f'Total: {self.total_detections}', (15, 105), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Publish visualization
                vis_msg = self.bridge.cv2_to_imgmsg(img, 'bgr8')
                vis_msg.header = msg.header
                self.pub.publish(vis_msg)
                
                # Occasional logging
                if self.counter % 60 == 0:
                    print(f"⚡ Frame {self.counter}: FPS={avg_fps:.1f}, "
                          f"Process={process_time:.1f}ms, Detections={current_detections}, "
                          f"Total={self.total_detections}")
                
            except Exception as e:
                print(f"❌ Error processing frame: {e}")
    
    # Run the node
    rclpy.init()
    
    try:
        node = YOLOv8nFastDetector()
        print("\n🎯 Fast YOLOv8n detector running!")
        print("📺 Open rqt_image_view and select: /weed_detect/visualization")
        print("🛑 Press Ctrl+C to stop")
        print("-" * 50)
        
        rclpy.spin(node)
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping detector...")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'node' in locals():
            node.destroy_node()
        rclpy.shutdown()
        print("✅ Shutdown complete!")

if __name__ == '__main__':
    main()
