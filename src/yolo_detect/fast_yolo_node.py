#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CompressedImage
from std_msgs.msg import String
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2
import numpy as np
import torch
import time
from collections import deque

class FastYoloWeedDetectorNode(Node):
    def __init__(self):
        super().__init__('fast_yolo_weed_detector')
        
        # Declare minimal parameters for maximum speed
        self.declare_parameter('model_path', 'models/best.pt')
        self.declare_parameter('camera_topic', '/depth_cam/rgb/image_raw')
        self.declare_parameter('confidence_threshold', 0.3)
        self.declare_parameter('resize_width', 320)  # Much smaller for speed
        self.declare_parameter('skip_frames', 3)     # Skip more frames
        self.declare_parameter('use_yolov8n', False) # Option to use YOLOv8n
        
        # Get parameters
        self.model_path = self.get_parameter('model_path').value
        self.camera_topic = self.get_parameter('camera_topic').value
        self.confidence = self.get_parameter('confidence_threshold').value
        self.resize_width = self.get_parameter('resize_width').value
        self.skip_frames = self.get_parameter('skip_frames').value
        self.use_yolov8n = self.get_parameter('use_yolov8n').value
        
        # Use YOLOv8n if requested
        if self.use_yolov8n:
            self.model_path = 'yolov8n.pt'
            self.get_logger().info('🚀 Using YOLOv8n for maximum speed')
        
        # Class mapping (simplified)
        self.class_colors = {
            0: (0, 255, 0),    # Green for weeds
            1: (0, 165, 255)   # Orange for other objects
        }
        
        # Performance tracking (minimal)
        self.fps_buffer = deque(maxlen=10)  # Smaller buffer
        self.frame_skip_counter = 0
        self.frame_count = 0
        self.last_time = time.time()
        
        self.get_logger().info(f'🚀 Loading model: {self.model_path}')
        self.get_logger().info(f'📐 Resize to: {self.resize_width}px')
        self.get_logger().info(f'⏭️  Skip frames: {self.skip_frames}')
        
        # Load YOLO model with PyTorch fix
        try:
            # Add safe globals for ultralytics
            try:
                import ultralytics.nn.tasks
                torch.serialization.add_safe_globals([
                    ultralytics.nn.tasks.DetectionModel,
                    torch.nn.modules.container.Sequential
                ])
            except:
                pass
            
            try:
                self.model = YOLO(self.model_path)
            except:
                # Fallback with weights_only=False
                original_load = torch.load
                def patched_load(*args, **kwargs):
                    kwargs['weights_only'] = False
                    return original_load(*args, **kwargs)
                
                torch.load = patched_load
                self.model = YOLO(self.model_path)
                torch.load = original_load
            
            # Set to CPU and optimize
            self.model.to('cpu')
            
            # Warm up with tiny image
            self.get_logger().info('🔥 Warming up...')
            dummy = np.zeros((160, 160, 3), dtype=np.uint8)
            _ = self.model(dummy, conf=self.confidence, verbose=False)
            
            self.get_logger().info('✅ Model ready!')
            
        except Exception as e:
            self.get_logger().error(f'❌ Model loading failed: {e}')
            raise
        
        # Initialize CV Bridge
        self.bridge = CvBridge()
        
        # Create subscriber with very small queue
        self.sub = self.create_subscription(
            Image,
            self.camera_topic,
            self.image_callback,
            1  # Smallest possible queue
        )
        
        # Only create visualization publisher (nothing else!)
        self.pub_image = self.create_publisher(Image, '/weed_detect/visualization', 1)
        
        self.get_logger().info('🏃‍♂️ Ultra-fast weed detector ready!')
    
    def image_callback(self, msg: Image):
        """Super optimized image processing"""
        self.frame_count += 1
        
        # Frame skipping
        self.frame_skip_counter += 1
        if self.frame_skip_counter < self.skip_frames:
            return
        self.frame_skip_counter = 0
        
        start_time = time.time()
        
        try:
            # Convert image (fastest method)
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            
            # Aggressive resize for speed
            height, width = cv_image.shape[:2]
            if width > self.resize_width:
                scale = self.resize_width / width
                new_height = int(height * scale)
                # Use INTER_NEAREST for maximum speed (lower quality but fastest)
                small_image = cv2.resize(cv_image, (self.resize_width, new_height), 
                                       interpolation=cv2.INTER_NEAREST)
            else:
                small_image = cv_image
                scale = 1.0
            
            # Run YOLO (minimal settings)
            results = self.model(small_image, conf=self.confidence, verbose=False)[0]
            
            # Process detections (minimal drawing)
            if results.boxes is not None and len(results.boxes) > 0:
                for det in results.boxes:
                    # Scale back to original
                    x1, y1, x2, y2 = det.xyxy[0].tolist()
                    if scale != 1.0:
                        x1, x2 = int(x1 / scale), int(x2 / scale)
                        y1, y2 = int(y1 / scale), int(y2 / scale)
                    else:
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    
                    conf = det.conf[0].item()
                    cls = int(det.cls[0].item())
                    
                    # Super simple drawing
                    color = self.class_colors.get(cls, (255, 255, 255))
                    cv2.rectangle(cv_image, (x1, y1), (x2, y2), color, 2)
                    
                    # Minimal label
                    label = f'{conf:.2f}'
                    cv2.putText(cv_image, label, (x1, y1-5), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # Calculate FPS
            current_time = time.time()
            fps = 1.0 / (current_time - self.last_time)
            self.last_time = current_time
            self.fps_buffer.append(fps)
            
            # Minimal overlay (just FPS)
            avg_fps = sum(self.fps_buffer) / len(self.fps_buffer)
            cv2.putText(cv_image, f'FPS: {avg_fps:.1f}', (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Publish (with compression for speed)
            try:
                # Compress to reduce publishing overhead
                encode_param = [cv2.IMWRITE_JPEG_QUALITY, 60]  # Lower quality = faster
                _, buffer = cv2.imencode('.jpg', cv_image, encode_param)
                compressed_image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
                
                vis_msg = self.bridge.cv2_to_imgmsg(compressed_image, 'bgr8')
                vis_msg.header = msg.header
                self.pub_image.publish(vis_msg)
            except Exception as e:
                # Fallback: publish without compression
                vis_msg = self.bridge.cv2_to_imgmsg(cv_image, 'bgr8')
                vis_msg.header = msg.header
                self.pub_image.publish(vis_msg)
            
            # Debug logging (very occasional)
            if self.frame_count % 150 == 0:  # Every 150 frames
                process_time = (time.time() - start_time) * 1000
                self.get_logger().info(f'⚡ FPS: {avg_fps:.1f}, Process: {process_time:.1f}ms')
                
        except Exception as e:
            self.get_logger().error(f'❌ Error: {e}')

def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = FastYoloWeedDetectorNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        print('🛑 Shutting down fast detector')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        if 'node' in locals():
            node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
