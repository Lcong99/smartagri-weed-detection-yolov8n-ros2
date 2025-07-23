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
import csv
import psutil
import GPUtil
import socket
import requests
import time
import queue
import platform
from collections import deque

class YoloWeedDetectorNode(Node):
    def __init__(self):
        super().__init__('yolo_weed_detect_node')
        
        # Declare parameters
        self.declare_parameter('model_path', 'models/best.pt')
        self.declare_parameter('camera_topic', '/depth_cam/rgb/image_raw')
        self.declare_parameter('use_compressed', False)
        self.declare_parameter('confidence_threshold', 0.25)
        self.declare_parameter('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        self.declare_parameter('save_detections', True)
        self.declare_parameter('output_dir', os.path.expanduser('~/jetrover_weed_data'))
        self.declare_parameter('debug_mode', True)
        self.declare_parameter('remote_host', '')
        self.declare_parameter('remote_port', 8080)
        self.declare_parameter('enable_transmission', False)
        
        # Performance optimization parameters
        self.declare_parameter('skip_frames', 2)  # Process every Nth frame
        self.declare_parameter('resize_width', 640)  # Resize image for faster processing
        self.declare_parameter('visualization_quality', 0.7)  # JPEG quality for visualization
        self.declare_parameter('enable_overlay', True)  # Toggle statistics overlay
        self.declare_parameter('save_frequency', 30)  # Save every Nth detection
        self.declare_parameter('performance_mode', True)  # Enable performance optimizations
        
        # Get parameters
        self.model_path = self.get_parameter('model_path').value
        self.camera_topic = self.get_parameter('camera_topic').value
        self.use_compressed = self.get_parameter('use_compressed').value
        self.confidence = self.get_parameter('confidence_threshold').value
        self.device = self.get_parameter('device').value
        self.save_detections = self.get_parameter('save_detections').value
        self.output_dir = self.get_parameter('output_dir').value
        self.debug_mode = self.get_parameter('debug_mode').value
        self.remote_host = self.get_parameter('remote_host').value
        self.remote_port = self.get_parameter('remote_port').value
        self.enable_transmission = self.get_parameter('enable_transmission').value
        
        # Performance parameters
        self.skip_frames = self.get_parameter('skip_frames').value
        self.resize_width = self.get_parameter('resize_width').value
        self.visualization_quality = self.get_parameter('visualization_quality').value
        self.enable_overlay = self.get_parameter('enable_overlay').value
        self.save_frequency = self.get_parameter('save_frequency').value
        self.performance_mode = self.get_parameter('performance_mode').value
        
        # Class mapping
        self.class_names = {0: 'neutral_weed', 1: 'opp_weed'}
        self.class_colors = {
            0: (0, 100, 0),    # Dark green for neutral weeds
            1: (0, 165, 255)   # Orange for opp weeds (BGR format)
        }
        
        # Performance tracking with deques for efficiency
        self.fps_buffer = deque(maxlen=30)
        self.processing_times = deque(maxlen=30)
        self.frame_skip_counter = 0
        self.save_counter = 0
        
        # Create output directories
        self.setup_directories()
        
        self.get_logger().info(f'🚀 Loading YOLO model from: {self.model_path}')
        self.get_logger().info(f'📷 Camera topic: {self.camera_topic}')
        self.get_logger().info(f'🖥️  Device: {self.device}')
        self.get_logger().info(f'⚡ Performance mode: {self.performance_mode}')
        self.get_logger().info(f'📐 Resize width: {self.resize_width}')
        self.get_logger().info(f'🎯 Skip frames: {self.skip_frames}')
        
        # Load YOLO model with PyTorch 2.6 compatibility
        try:
            self.get_logger().info('🔧 Configuring PyTorch for YOLO model loading...')
            
            # Method 1: Add safe globals for ultralytics
            try:
                import ultralytics.nn.tasks
                torch.serialization.add_safe_globals([ultralytics.nn.tasks.DetectionModel])
                self.get_logger().info('✅ Added ultralytics.nn.tasks.DetectionModel to safe globals')
            except Exception as e:
                self.get_logger().warn(f'⚠️  Could not add safe globals: {e}')
            
            # Method 2: Load with weights_only=False (fallback)
            try:
                self.get_logger().info('🔄 Attempting to load model with safe globals...')
                self.model = YOLO(self.model_path)
            except Exception as e:
                self.get_logger().warn(f'⚠️  Safe loading failed: {e}')
                self.get_logger().info('🔄 Falling back to weights_only=False loading...')
                
                # Monkey patch torch.load to use weights_only=False
                original_load = torch.load
                def patched_load(*args, **kwargs):
                    kwargs['weights_only'] = False
                    return original_load(*args, **kwargs)
                
                torch.load = patched_load
                self.model = YOLO(self.model_path)
                torch.load = original_load  # Restore original
                
                self.get_logger().info('✅ Model loaded with weights_only=False')
            
            if self.device == 'cuda':
                self.model.to('cuda')
            
            # Warm up the model for better performance
            self.get_logger().info('🔥 Warming up model...')
            dummy_img = np.zeros((self.resize_width, self.resize_width, 3), dtype=np.uint8)
            for _ in range(3):
                _ = self.model(dummy_img, conf=self.confidence, verbose=False)
            
            self.get_logger().info('✅ YOLO model ready!')
            
        except Exception as e:
            self.get_logger().error(f'❌ Failed to load YOLO model: {e}')
            self.get_logger().error('💡 Try one of these solutions:')
            self.get_logger().error('   1. Retrain your model with a newer version of ultralytics')
            self.get_logger().error('   2. Use a different model file')
            self.get_logger().error('   3. Downgrade PyTorch to version < 2.6')
            raise
        
        # Initialize CV Bridge
        self.bridge = CvBridge()
        
        # Performance data (simplified for speed)
        self.performance_data = {
            'detection_counts': {'neutral': 0, 'opp': 0},
            'total_frames': 0,
            'processed_frames': 0
        }
        
        # Data logging setup (lightweight)
        if self.save_detections:
            self.setup_data_logging()
        
        # Network transmission setup (if enabled)
        if self.enable_transmission:
            self.setup_network_transmission()
        
        # Create subscriber with smaller queue for real-time
        if self.use_compressed:
            self.sub = self.create_subscription(
                CompressedImage,
                f'{self.camera_topic}/compressed',
                self.compressed_image_callback,
                1  # Small queue for real-time
            )
        else:
            self.sub = self.create_subscription(
                Image,
                self.camera_topic,
                self.image_callback,
                1  # Small queue for real-time
            )
        
        # Publishers
        self.pub_image = self.create_publisher(Image, '/weed_detect/visualization', 1)
        self.pub_data = self.create_publisher(String, '/weed_detect/json_data', 10)
        
        # Only create other publishers if not in performance mode
        if not self.performance_mode:
            self.pub_boxes = self.create_publisher(Float32MultiArray, '/weed_detect/boxes', 10)
            self.pub_stats = self.create_publisher(String, '/weed_detect/performance_stats', 10)
        
        # Statistics
        self.frame_count = 0
        self.start_time = time.time()
        self.last_process_time = time.time()
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Timers (reduced frequency for performance)
        if not self.performance_mode:
            self.stats_timer = self.create_timer(10.0, self.log_performance_stats)
            self.system_timer = self.create_timer(5.0, self.monitor_system_resources)
        
        self.get_logger().info('🌱 Weed detection system initialized in performance mode!')
    
    def setup_directories(self):
        """Create organized directory structure for data logging"""
        self.dirs = {
            'root': self.output_dir,
            'images': os.path.join(self.output_dir, 'images'),
            'detections': os.path.join(self.output_dir, 'detections'),
            'logs': os.path.join(self.output_dir, 'logs'),
            'performance': os.path.join(self.output_dir, 'performance')
        }
        
        for dir_path in self.dirs.values():
            os.makedirs(dir_path, exist_ok=True)
    
    def setup_data_logging(self):
        """Initialize CSV logging files (lightweight)"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Simple detection log
        self.detection_csv_path = os.path.join(self.dirs['logs'], f'detections_{timestamp}.csv')
        with open(self.detection_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'frame_id', 'class', 'confidence', 'x1', 'y1', 'x2', 'y2'])
    
    def setup_network_transmission(self):
        """Setup network transmission queue and thread"""
        self.transmission_queue = queue.Queue(maxsize=50)
        self.transmission_thread = threading.Thread(target=self.transmission_worker, daemon=True)
        self.transmission_thread.start()
        
    def transmission_worker(self):
        """Worker thread for network transmission"""
        while rclpy.ok():
            try:
                data = self.transmission_queue.get(timeout=1.0)
                if data is None:
                    break
                
                try:
                    url = f'http://{self.remote_host}:{self.remote_port}/weed_data'
                    response = requests.post(url, json=data, timeout=1.0)
                except Exception:
                    pass  # Silently fail to not affect performance
                
            except queue.Empty:
                continue
    
    def image_callback(self, msg: Image):
        """Handle uncompressed image messages"""
        self.frame_count += 1
        
        # Frame skipping for performance
        if self.performance_mode:
            self.frame_skip_counter += 1
            if self.frame_skip_counter < self.skip_frames:
                return
            self.frame_skip_counter = 0
        
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
            self.process_image_fast(cv_image, msg.header)
        except Exception as e:
            if self.debug_mode:
                self.get_logger().error(f'❌ Processing error: {e}')
    
    def compressed_image_callback(self, msg: CompressedImage):
        """Handle compressed image messages"""
        self.frame_count += 1
        
        # Frame skipping
        if self.performance_mode:
            self.frame_skip_counter += 1
            if self.frame_skip_counter < self.skip_frames:
                return
            self.frame_skip_counter = 0
        
        try:
            np_arr = np.frombuffer(msg.data, np.uint8)
            cv_image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            header = Header()
            header.stamp = msg.header.stamp
            header.frame_id = msg.header.frame_id
            self.process_image_fast(cv_image, header)
        except Exception as e:
            if self.debug_mode:
                self.get_logger().error(f'❌ Processing error: {e}')
    
    def process_image_fast(self, cv_image, header):
        """Optimized image processing for real-time performance"""
        process_start = time.time()
        
        # Resize image for faster processing
        height, width = cv_image.shape[:2]
        if width > self.resize_width:
            scale = self.resize_width / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            resized_image = cv2.resize(cv_image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        else:
            resized_image = cv_image
            scale = 1.0
        
        # Run YOLO inference on resized image
        results = self.model(resized_image, conf=self.confidence, verbose=False)[0]
        
        # Create visualization on original image
        vis_image = cv_image.copy()
        
        detection_data = {
            'timestamp': time.time(),
            'frame_count': self.frame_count,
            'detections': []
        }
        
        neutral_count = 0
        opp_count = 0
        
        # Process detections
        if results.boxes is not None and len(results.boxes) > 0:
            for det in results.boxes:
                # Scale coordinates back to original size
                x1, y1, x2, y2 = det.xyxy[0].tolist()
                x1, x2 = int(x1 / scale), int(x2 / scale)
                y1, y2 = int(y1 / scale), int(y2 / scale)
                
                conf = det.conf[0].item()
                cls = int(det.cls[0].item())
                
                # Count by class
                if cls == 0:
                    neutral_count += 1
                else:
                    opp_count += 1
                
                # Draw on image (simplified for speed)
                self.draw_detection_fast(vis_image, x1, y1, x2, y2, conf, cls)
                
                # Add to detection data (simplified)
                detection_data['detections'].append({
                    'class': cls,
                    'confidence': conf,
                    'bbox': [x1, y1, x2, y2]
                })
        
        # Update counts
        self.performance_data['detection_counts']['neutral'] += neutral_count
        self.performance_data['detection_counts']['opp'] += opp_count
        self.performance_data['processed_frames'] += 1
        
        # Calculate FPS
        current_time = time.time()
        fps = 1.0 / (current_time - self.last_process_time) if self.last_process_time else 0
        self.last_process_time = current_time
        self.fps_buffer.append(fps)
        
        # Add lightweight overlay
        if self.enable_overlay:
            self.add_fast_overlay(vis_image, neutral_count, opp_count, np.mean(self.fps_buffer))
        
        # Publish visualization
        try:
            # Compress image for faster publishing
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), int(self.visualization_quality * 100)]
            _, buffer = cv2.imencode('.jpg', vis_image, encode_param)
            vis_decoded = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
            
            debug_msg = self.bridge.cv2_to_imgmsg(vis_decoded, 'bgr8')
            debug_msg.header = header
            self.pub_image.publish(debug_msg)
        except Exception as e:
            if self.debug_mode:
                self.get_logger().error(f'❌ Publishing error: {e}')
        
        # Lightweight data publishing
        if len(detection_data['detections']) > 0:
            json_msg = String()
            json_msg.data = json.dumps(detection_data)
            self.pub_data.publish(json_msg)
        
        # Save detections (throttled)
        if self.save_detections and len(detection_data['detections']) > 0:
            self.save_counter += 1
            if self.save_counter >= self.save_frequency:
                self.save_counter = 0
                self.save_detection_fast(vis_image, detection_data)
        
        # Log processing time
        process_time = (time.time() - process_start) * 1000
        self.processing_times.append(process_time)
        
        # Performance logging (reduced frequency)
        if self.debug_mode and self.frame_count % 100 == 0:
            avg_fps = np.mean(self.fps_buffer) if self.fps_buffer else 0
            avg_time = np.mean(self.processing_times) if self.processing_times else 0
            self.get_logger().info(
                f'⚡ Performance - FPS: {avg_fps:.1f}, Process: {avg_time:.1f}ms, '
                f'Frames: {self.frame_count}, Detections: N={neutral_count} O={opp_count}'
            )
    
    def draw_detection_fast(self, image, x1, y1, x2, y2, conf, cls):
        """Simplified drawing for performance"""
        color = self.class_colors.get(cls, (255, 255, 255))
        
        # Draw rectangle
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        
        # Simple label
        label = f'{self.class_names.get(cls, "?")} {conf:.2f}'
        cv2.putText(image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    
    def add_fast_overlay(self, image, neutral_count, opp_count, fps):
        """Lightweight overlay for performance"""
        h, w = image.shape[:2]
        
        # Simple stats in corner
        stats = [
            f'FPS: {fps:.0f}',
            f'N: {neutral_count} | O: {opp_count}',
            f'Total: N={self.performance_data["detection_counts"]["neutral"]} O={self.performance_data["detection_counts"]["opp"]}'
        ]
        
        # Draw semi-transparent background
        overlay = image.copy()
        cv2.rectangle(overlay, (5, 5), (200, 65), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, image, 0.5, 0, image)
        
        # Draw text
        y = 20
        for stat in stats:
            cv2.putText(image, stat, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            y += 20
    
    def save_detection_fast(self, image, detection_data):
        """Lightweight saving"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            
            # Save image with compression
            image_path = os.path.join(self.dirs['images'], f'weed_{timestamp}.jpg')
            cv2.imwrite(image_path, image, [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            # Save simple JSON
            json_path = os.path.join(self.dirs['detections'], f'weed_{timestamp}.json')
            with open(json_path, 'w') as f:
                json.dump(detection_data, f)
            
            # Log to CSV (simplified)
            with open(self.detection_csv_path, 'a', newline='') as f:
                writer = csv.writer(f)
                for det in detection_data['detections']:
                    writer.writerow([
                        detection_data['timestamp'],
                        self.frame_count,
                        det['class'],
                        det['confidence'],
                        *det['bbox']
                    ])
                    
        except Exception as e:
            if self.debug_mode:
                self.get_logger().error(f'Save error: {e}')
    
    def log_performance_stats(self):
        """Lightweight performance logging"""
        if not self.fps_buffer:
            return
            
        avg_fps = np.mean(self.fps_buffer)
        avg_process = np.mean(self.processing_times)
        
        self.get_logger().info(
            f'📊 Stats - Avg FPS: {avg_fps:.1f}, Process: {avg_process:.1f}ms, '
            f'Frames: {self.frame_count}/{self.performance_data["processed_frames"]}, '
            f'Neutral: {self.performance_data["detection_counts"]["neutral"]}, '
            f'Opp: {self.performance_data["detection_counts"]["opp"]}'
        )
    
    def monitor_system_resources(self):
        """Minimal resource monitoring"""
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory().percent
            self.get_logger().info(f'💻 System - CPU: {cpu:.1f}%, Memory: {mem:.1f}%')
        except:
            pass

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
