#!/usr/bin/env bash
set -e

# ————————————————————————————————
# Source ROS 2 Humble and your workspace
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
# ————————————————————————————————

echo "🤖 JetRover Weed Detection Camera Test Script"
echo "============================================="

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

detect_camera_type() {
    if ros2 topic list 2>/dev/null | grep -q "/depth_cam/color"; then
        echo "depth"
    elif ros2 topic list 2>/dev/null | grep -q "/usb_cam"; then
        echo "usb"
    else
        echo "none"
    fi
}

test_usb_camera() {
    echo -e "\n📷 Testing USB Camera..."
    if command_exists v4l2-ctl; then
        echo "✅ v4l2-ctl found"
        echo -e "\n📋 Camera capabilities:"
        v4l2-ctl --list-devices
        echo -e "\n📊 Supported formats for /dev/video0:"
        v4l2-ctl -d /dev/video0 --list-formats-ext
    else
        echo "⚠️  v4l2-ctl not installed. Install with: sudo apt install v4l-utils"
    fi
}

test_depth_camera() {
    echo -e "\n🔍 Testing depth camera via ROS2 launch..."
    ros2 launch peripherals depth_camera.launch.py \
      device_id:=/dev/dabai_dcw \
      rgb_device_id:=/dev/dabai_dcw_rgb \
      enable_ir:=false \
      enable_depth:=true \
      enable_color:=true
}

test_ros2_camera() {
    echo -e "\n📡 Testing ROS2 camera topics..."
    ros2 topic list | grep -E "depth_cam|usb_cam" || echo "⚠️  No expected camera topics found."
}

create_camera_config() {
    echo -e "\n📝 Creating camera configuration..."
    CONFIG_DIR="$HOME/ros2_ws/src/yolo_detect/config"
    mkdir -p "$CONFIG_DIR"
    cat > "$CONFIG_DIR/camera_config.yaml" << EOF
# Camera configuration for weed detection
usb_cam:
  ros__parameters:
    video_device: "/dev/video0"
    framerate: 30.0
    image_width: 640
    image_height: 480
depth_cam:
  ros__parameters:
    device_id: "/dev/dabai_dcw"
    rgb_device_id: "/dev/dabai_dcw_rgb"
    enable_ir: false
    enable_depth: true
    enable_color: true
    fps: 30
    frame_id: "depth_camera_link"
EOF
    echo "✅ Camera config saved to $CONFIG_DIR/camera_config.yaml"
}

test_yolo_model() {
    echo -e "\n🧪 Testing YOLO model load..."
    MODEL="$HOME/ros2_ws/src/yolo_detect/models/best.pt"
    python3 - <<PYCODE
import os, sys
from ultralytics import YOLO
path = os.path.expanduser("$MODEL")
if not os.path.isfile(path):
    print(f"❌ Model file not found at {path}")
    sys.exit(1)
try:
    _ = YOLO(path)
    print("✅ YOLO model loaded successfully")
except Exception as e:
    print(f"❌ Failed to load YOLO model: {e}")
    sys.exit(1)
PYCODE
}

test_gpu() {
    echo -e "\n🔌 Checking GPU availability..."
    if command_exists nvcc; then
        echo "✅ nvcc found:"
        nvcc --version | grep "release"
    else
        echo "⚠️  No NVIDIA CUDA compiler found. CPU inference only."
    fi
    echo -e "\n🔥 Checking PyTorch GPU support:"
    python3 - << 'PYCODE'
import torch
print("PyTorch version:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())
PYCODE
}

test_auto_camera() {
    echo -e "\n🔍 Auto-detecting and testing cameras..."
    camera_type=$(detect_camera_type)
    echo "🎯 Detected camera type: $camera_type"
    case $camera_type in
        depth) test_depth_camera ;;
        usb)   test_usb_camera ;;
        *)     echo "❌ No compatible camera detected." ;;
    esac
}

run_all_tests() {
    echo -e "\n🧪 Running Comprehensive Camera Tests..."
    echo "========================================"
    test_auto_camera
    test_ros2_camera
    test_yolo_model
    test_gpu
    echo -e "\n✅ All tests completed!"
}

launch_weed_detection() {
    echo -e "\n🚀 Launching Weed Detection System…"
    camera_type=$(detect_camera_type)
    echo "🎯 Detected camera type: $camera_type"
    case $camera_type in
        depth)
            echo "🚀 Running YOLO on center (RGB) camera"
            python3 -m yolo_detect.yolo_node --ros-args \
                -p camera_type:=depth \
                -p camera_topic:=/depth_cam/rgb/image_raw \
                -p confidence_threshold:=0.2 \
                -p save_detections:=true \
                -p debug_mode:=true
            ;;
        usb)
            echo "🚀 Running YOLO on USB camera"
            python3 -m yolo_detect.yolo_node --ros-args \
                -p camera_type:=usb \
                -p camera_topic:=/usb_cam/image_raw \
                -p confidence_threshold:=0.5 \
                -p save_detections:=true \
                -p debug_mode:=true
            ;;
        *)
            echo "❌ No compatible camera detected. Please run tests first."
            ;;
    esac
}

main_menu() {
    while true; do
        echo -e "\n====== JetRover Weed Detection ======"
        echo "1) Test USB camera"
        echo "2) Test depth camera"
        echo "3) List ROS2 camera topics"
        echo "4) Create camera config"
        echo "5) Test YOLO model"
        echo "6) Test GPU"
        echo "7) Run all tests"
        echo "8) Launch weed detection"
        echo "0) Exit"
        read -p "Select an option: " opt
        case $opt in
            1) test_usb_camera ;;
            2) test_depth_camera ;;
            3) test_ros2_camera ;;
            4) create_camera_config ;;
            5) test_yolo_model ;;
            6) test_gpu ;;
            7) run_all_tests ;;
            8) launch_weed_detection ;;
            0) echo "👋 Goodbye!"; exit 0 ;;
            *) echo "❌ Invalid option" ;;
        esac
    done
}

main_menu

