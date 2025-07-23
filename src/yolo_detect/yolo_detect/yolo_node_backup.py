#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CompressedImage
from std_msgs.msg import Float32MultiArray, String, Header
from geometry_msgs.msg import Point
from cv_bridge import CvBridge
from ultralytics import YOLO
import cv2
import numpy as np
import json
import os
from datetime import datetime
import threading
import torch

class YoloWeedDetectorNode(Node):
    def __init__(self):
        super().__init__('yolo_weed_detect_node')
        
        # Declare parameters
        self.declare_parameter('model_path', 'models/best.pt')
        self.declare_parameter('camera_topic', '/usb_cam/image_raw')
        self.declare_parameter('use_compressed', False)
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        self.declare_parameter('save_detections', True)
        self.declare_parameter('output_dir', '/home/ubuntu/weed_detections')
        self.declare_parameter('debug_mode', True)
        
        # Get parameters
        self.model_path = self.get_parameter('model_path').value
        self.camera_topic = self.get_parameter('camera_topic').value
        self.use_compressed = self.get_parameter('use_compressed').value
        self.confidence = self.get_parameter('confidence_threshold').value
        self.device = self.get_parameter('device').value
        self.save_detections = self.get_parameter('save_detections').value
        self.output_dir = self.get_parameter('output_dir').value
        self.debug_mode = self.get_parameter('debug_mode').value
        
        self.get_logger().info(f'🚀 Loading YOLO model from: {self.model_path}')
        self.get_logger().info(f'📷 Camera topic: {self.camera_topic}')
        self.get_logger().info(f'🖥️  Device: {self.device}')
        
        # Create output directory
        if self.save_detections:
            os.makedirs(self.output_dir, exist_ok=True)
            self.get_logger().info(f'📁 Output directory: {self.output_dir}')
        
        # Load YOLO model
        try:
            self.model = YOLO(self.model_path)
            if self.device == 'cuda':
                self.model.to('cuda')
            self.get_logger().info('✅ YOLO model loaded successfully')
        except Exception as e:
            self.get_logger().error(f'❌ Failed to load YOLO model: {e}')
            raise
        
        # Initialize CV Bridge
        self.bridge = CvBridge()
        
        # Create subscriber based on compression setting
        if self.use_compressed:
            self.sub = self.create_subscription(
                CompressedImage,
                f'{self.camera_topic}/compressed',
                self.compressed_image_callback,
                10
            )
            self.get_logger().info(f'📡 Subscribed to {self.camera_topic}/compressed')
        else:
            self.sub = self.create_subscription(
                Image,
                self.camera_topic,
                self.image_callback,
                10
            )
            self.get_logger().info(f'📡 Subscribed to {self.camera_topic}')
        
        # Publishers
        self.pub_boxes = self.create_publisher(Float32MultiArray, '/weed_detect/boxes', 10)
        self.pub_image = self.create_publisher(Image, '/weed_detect/visualization', 10)
        self.pub_data = self.create_publisher(String, '/weed_detect/json_data', 10)
        
        # Statistics
        self.frame_count = 0
        self.detection_count = 0
        self.start_time = datetime.now()
        self.last_log_time = datetime.now()
        
        # Create timer for periodic statistics
        self.stats_timer = self.create_timer(30.0, self.log_statistics)
    
    def image_callback(self, msg: Image):
        """Handle uncompressed image messages"""
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            self.process_image(cv_image, msg.header)
        except Exception as e:
            self.get_logger().error(f'❌ CVBridge conversion failed: {e}')
    
    def compressed_image_callback(self, msg: CompressedImage):
        """Handle compressed image messages"""
        try:
            np_arr = np.frombuffer(msg.data, np.uint8)
            cv_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            self.process_image(cv_image, msg.header)
        except Exception as e:
            self.get_logger().error(f'❌ Compressed image decode failed: {e}')
    
    def process_image(self, cv_image, header):
        """Process image for weed detection"""
        self.frame_count += 1
        
        if self.debug_mode and self.frame_count % 30 == 0:
            self.get_logger().info(f'📷 Processing frame {self.frame_count}')
        
        try:
            # Run YOLO inference
            results = self.model(cv_image, conf=self.confidence)[0]
            
            # Prepare detection data
            detection_data = {
                'timestamp': header.stamp.sec + header.stamp.nanosec * 1e-9,
                'frame_id': header.frame_id,
                'frame_count': self.frame_count,
                'detections': []
            }
            
            boxes_data = []
            
            # Process detections
            if results.boxes is not None and len(results.boxes) > 0:
                for i, det in enumerate(results.boxes):
                    x1, y1, x2, y2 = det.xyxy[0].tolist()
                    conf = det.conf[0].item()
                    cls = int(det.cls[0].item())
                    
                    # Calculate additional metrics
                    cx = (x1 + x2) / 2
                    cy = (y1 + y2) / 2
                    width = x2 - x1
                    height = y2 - y1
                    area = width * height
                    
                    # Add to detection data
                    detection_info = {
                        'id': i,
                        'class': cls,
                        'confidence': conf,
                        'bbox': [x1, y1, x2, y2],
                        'center': [cx, cy],
                        'size': [width, height],
                        'area': area
                    }
                    detection_data['detections'].append(detection_info)
                    
                    # Add to boxes array for compatibility
                    boxes_data.extend([x1, y1, x2, y2, conf, cls])
                    
                    # Draw on image
                    self.draw_detection(cv_image, x1, y1, x2, y2, conf, cls)
                    
                self.detection_count += len(results.boxes)
                
                if self.debug_mode:
                    self.get_logger().info(
                        f'🌿 Detected {len(results.boxes)} weed(s) in frame {self.frame_count}'
                    )
            
            # Add statistics to image
            self.add_statistics_overlay(cv_image, len(detection_data['detections']))
            
            # Publish detection boxes
            if boxes_data:
                fa = Float32MultiArray(data=boxes_data)
                self.pub_boxes.publish(fa)
            
            # Publish annotated image
            try:
                debug_msg = self.bridge.cv2_to_imgmsg(cv_image, 'bgr8')
                debug_msg.header = header
                self.pub_image.publish(debug_msg)
            except Exception as e:
                self.get_logger().error(f'❌ Error publishing image: {e}')
            
            # Publish JSON data
            json_msg = String()
            json_msg.data = json.dumps(detection_data)
            self.pub_data.publish(json_msg)
            
            # Save detection if enabled
            if self.save_detections and len(detection_data['detections']) > 0:
                self.save_detection(cv_image, detection_data)
                
        except Exception as e:
            self.get_logger().error(f'❌ YOLO inference error: {e}')
    
    def draw_detection(self, image, x1, y1, x2, y2, conf, cls):
        """Draw bounding box and label on image"""
        # Define colors for different classes (if needed)
        color = (0, 255, 0)  # Green for weeds
        
        # Draw rectangle
        cv2.rectangle(image, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
        
        # Prepare label
        label = f'Weed {conf:.2f}'
        
        # Calculate label size
        (label_width, label_height), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
        )
        
        # Draw label background
        cv2.rectangle(
            image,
            (int(x1), int(y1) - label_height - 10),
            (int(x1) + label_width, int(y1)),
            color,
            -1
        )
        
        # Draw label text
        cv2.putText(
            image,
            label,
            (int(x1), int(y1) - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1
        )
    
    def add_statistics_overlay(self, image, detection_count):
        """Add statistics overlay to image"""
        h, w = image.shape[:2]
        
        # Calculate FPS
        elapsed = (datetime.now() - self.start_time).total_seconds()
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        
        # Create overlay text
        stats = [
            f'FPS: {fps:.1f}',
            f'Frame: {self.frame_count}',
            f'Weeds: {detection_count}',
            f'Total: {self.detection_count}'
        ]
        
        # Draw background rectangle
        cv2.rectangle(image, (10, 10), (200, 90), (0, 0, 0), -1)
        cv2.rectangle(image, (10, 10), (200, 90), (0, 255, 0), 2)
        
        # Draw text
        y_offset = 30
        for stat in stats:
            cv2.putText(
                image,
                stat,
                (20, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1
            )
            y_offset += 18
    
    def save_detection(self, image, detection_data):
        """Save detection image and data"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            
            # Save image
            image_path = os.path.join(self.output_dir, f'weed_{timestamp}.jpg')
            cv2.imwrite(image_path, image)
            
            # Save JSON data
            json_path = os.path.join(self.output_dir, f'weed_{timestamp}.json')
            with open(json_path, 'w') as f:
                json.dump(detection_data, f, indent=2)
                
        except Exception as e:
            self.get_logger().error(f'❌ Error saving detection: {e}')
    
    def log_statistics(self):
        """Log periodic statistics"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        fps = self.frame_count / elapsed if elapsed > 0 else 0
        detection_rate = self.detection_count / self.frame_count if self.frame_count > 0 else 0
        
        self.get_logger().info(
            f'📊 Statistics - Frames: {self.frame_count}, '
            f'FPS: {fps:.1f}, Total Detections: {self.detection_count}, '
            f'Avg Detections/Frame: {detection_rate:.2f}'
        )

def main(args=None):
    rclpy.init(args=args)
    
    try:
        node = YoloWeedDetectorNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('🛑 Shutting down YOLO Weed Detect node')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        if 'node' in locals():
            node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
