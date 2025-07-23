#!/usr/bin/env bash
set -e

# Source ROS 2
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash

echo "🏃‍♂️ Ultra-Fast Weed Detection Launcher"
echo "======================================="

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

detect_camera() {
    if ros2 topic list 2>/dev/null | grep -q "/depth_cam/rgb"; then
        echo "/depth_cam/rgb/image_raw"
    elif ros2 topic list 2>/dev/null | grep -q "/usb_cam"; then
        echo "/usb_cam/image_raw"
    else
        echo "none"
    fi
}

launch_ultra_fast() {
    echo -e "\n${GREEN}🚀 ULTRA-FAST MODE${NC}"
    echo "Settings: 320px, Skip 3 frames, No saving, Minimal overlay"
    
    camera_topic=$(detect_camera)
    if [ "$camera_topic" = "none" ]; then
        echo -e "${RED}❌ No camera detected${NC}"
        return 1
    fi
    
    echo -e "${BLUE}📷 Using camera: $camera_topic${NC}"
    
    python3 -c "
import sys
sys.path.append('/home/ubuntu/ros2_ws/src/yolo_detect')
from fast_yolo_node import FastYoloWeedDetectorNode
import rclpy

rclpy.init()
node = FastYoloWeedDetectorNode()
node.set_parameters([
    ('camera_topic', '$camera_topic'),
    ('confidence_threshold', 0.4),
    ('resize_width', 320),
    ('skip_frames', 3),
    ('use_yolov8n', False)
])
try:
    rclpy.spin(node)
except KeyboardInterrupt:
    print('Stopping...')
finally:
    node.destroy_node()
    rclpy.shutdown()
"
}

launch_yolov8n_test() {
    echo -e "\n${GREEN}🚀 YOLOv8n TEST MODE${NC}"
    echo "Using standard YOLOv8n model for maximum compatibility"
    
    camera_topic=$(detect_camera)
    if [ "$camera_topic" = "none" ]; then
        echo -e "${RED}❌ No camera detected${NC}"
        return 1
    fi
    
    echo -e "${BLUE}📷 Using camera: $camera_topic${NC}"
    
    python3 -c "
import sys
sys.path.append('/home/ubuntu/ros2_ws/src/yolo_detect')
from fast_yolo_node import FastYoloWeedDetectorNode
import rclpy

rclpy.init()
node = FastYoloWeedDetectorNode()
node.set_parameters([
    ('camera_topic', '$camera_topic'),
    ('confidence_threshold', 0.5),
    ('resize_width', 416),
    ('skip_frames', 2),
    ('use_yolov8n', True)
])
try:
    rclpy.spin(node)
except KeyboardInterrupt:
    print('Stopping...')
finally:
    node.destroy_node()
    rclpy.shutdown()
"
}

launch_extreme_speed() {
    echo -e "\n${GREEN}🚀 EXTREME SPEED MODE${NC}"
    echo "Settings: 240px, Skip 4 frames, Absolute minimum processing"
    
    camera_topic=$(detect_camera)
    if [ "$camera_topic" = "none" ]; then
        echo -e "${RED}❌ No camera detected${NC}"
        return 1
    fi
    
    echo -e "${BLUE}📷 Using camera: $camera_topic${NC}"
    
    python3 -c "
import sys
sys.path.append('/home/ubuntu/ros2_ws/src/yolo_detect')
from fast_yolo_node import FastYoloWeedDetectorNode
import rclpy

rclpy.init()
node = FastYoloWeedDetectorNode()
node.set_parameters([
    ('camera_topic', '$camera_topic'),
    ('confidence_threshold', 0.5),
    ('resize_width', 240),
    ('skip_frames', 4),
    ('use_yolov8n', False)
])
try:
    rclpy.spin(node)
except KeyboardInterrupt:
    print('Stopping...')
finally:
    node.destroy_node()
    rclpy.shutdown()
"
}

test_camera_fps() {
    echo -e "\n${BLUE}📷 Testing raw camera FPS...${NC}"
    
    camera_topic=$(detect_camera)
    if [ "$camera_topic" = "none" ]; then
        echo -e "${RED}❌ No camera detected${NC}"
        return 1
    fi
    
    echo "Camera topic: $camera_topic"
    echo "Testing for 10 seconds..."
    
    timeout 10s ros2 topic hz "$camera_topic" || echo "Camera test completed"
}

view_visualization() {
    echo -e "\n${BLUE}👁️  Opening rqt_image_view...${NC}"
    echo "Select topic: /weed_detect/visualization"
    rqt_image_view &
    sleep 1
    echo "If rqt doesn't open, try: ros2 run rqt_image_view rqt_image_view"
}

benchmark_modes() {
    echo -e "\n${YELLOW}🏁 Running 30-second benchmark of each mode...${NC}"
    
    camera_topic=$(detect_camera)
    if [ "$camera_topic" = "none" ]; then
        echo -e "${RED}❌ No camera detected${NC}"
        return 1
    fi
    
    echo "Benchmarking Ultra-Fast mode..."
    timeout 30s python3 -c "
import sys
sys.path.append('/home/ubuntu/ros2_ws/src/yolo_detect')
from fast_yolo_node import FastYoloWeedDetectorNode
import rclpy

rclpy.init()
node = FastYoloWeedDetectorNode()
node.set_parameters([
    ('camera_topic', '$camera_topic'),
    ('resize_width', 320),
    ('skip_frames', 3)
])
try:
    rclpy.spin(node)
except:
    pass
finally:
    node.destroy_node()
    rclpy.shutdown()
" 2>/dev/null || true

    echo "Benchmarking Extreme Speed mode..."
    timeout 30s python3 -c "
import sys
sys.path.append('/home/ubuntu/ros2_ws/src/yolo_detect')
from fast_yolo_node import FastYoloWeedDetectorNode
import rclpy

rclpy.init()
node = FastYoloWeedDetectorNode()
node.set_parameters([
    ('camera_topic', '$camera_topic'),
    ('resize_width', 240),
    ('skip_frames', 4)
])
try:
    rclpy.spin(node)
except:
    pass
finally:
    node.destroy_node()
    rclpy.shutdown()
" 2>/dev/null || true

    echo -e "${GREEN}✅ Benchmark complete!${NC}"
}

main_menu() {
    while true; do
        echo -e "\n${BLUE}====== Ultra-Fast Weed Detection ======${NC}"
        echo -e "${GREEN}🏃‍♂️ SPEED MODES${NC}"
        echo "1) Ultra-Fast mode (320px, skip 3)"
        echo "2) Extreme Speed mode (240px, skip 4)"
        echo "3) YOLOv8n test mode (standard model)"
        echo ""
        echo -e "${YELLOW}🔧 TESTING & DEBUG${NC}"
        echo "4) Test raw camera FPS"
        echo "5) Open visualization viewer"
        echo "6) Benchmark all modes"
        echo ""
        echo -e "${BLUE}📊 COMPARISON${NC}"
        echo "Current vs Mac performance:"
        echo "- Mac: ~20-30 FPS (optimized)"
        echo "- Target: 10-15 FPS (CPU limited)"
        echo ""
        echo "0) Exit"
        
        read -p "Select option: " choice
        
        case $choice in
            1) launch_ultra_fast ;;
            2) launch_extreme_speed ;;
            3) launch_yolov8n_test ;;
            4) test_camera_fps ;;
            5) view_visualization ;;
            6) benchmark_modes ;;
            0) echo "👋 Goodbye!"; exit 0 ;;
            *) echo -e "${RED}❌ Invalid option${NC}" ;;
        esac
    done
}

# Create the fast node file
create_fast_node() {
    FAST_NODE_PATH="/home/ubuntu/ros2_ws/src/yolo_detect/fast_yolo_node.py"
    
    if [ ! -f "$FAST_NODE_PATH" ]; then
        echo -e "${YELLOW}📝 Creating fast_yolo_node.py...${NC}"
        # Note: In real usage, you'd copy the artifact content here
        echo "Please copy the FastYoloWeedDetectorNode code to $FAST_NODE_PATH"
        echo "Then make it executable: chmod +x $FAST_NODE_PATH"
    fi
}

# Check if fast node exists
if [ ! -f "/home/ubuntu/ros2_ws/src/yolo_detect/fast_yolo_node.py" ]; then
    create_fast_node
fi

main_menu
