
# smartagri-weed-detection-yolov8n-ros2
AI ROS2 weed detection with YOLOv8-nano on JetRover
=======
# Smart Agriculture Weed Detection System 

An intelligent agricultural robotics solution for autonomous weed detection using YOLOv8n on the JetRover platform with ROS2 Humble.

![Smart Agriculture](https://img.shields.io/badge/Smart-Agriculture-green) ![ROS2](https://img.shields.io/badge/ROS2-Humble-blue) ![Python](https://img.shields.io/badge/Python-3.10-brightgreen) ![YOLOv8](https://img.shields.io/badge/YOLOv8n-Ultralytics-orange) ![License](https://img.shields.io/badge/License-Apache%202.0-lightgrey)

## Features

- **Real-time Weed Detection**: YOLOv8n-powered computer vision for accurate weed identification
- **Multiple Camera Support**: Compatible with USB cameras and depth cameras (Dabai DCW)
- **ROS2 Integration**: Full ROS2 Humble ecosystem integration with topic publishing
- **GPU Acceleration**: CUDA support for high-performance inference
- **Data Logging**: Automatic saving of detection results with timestamps and metadata
- **Interactive Testing**: Comprehensive testing suite with automated camera detection
- **Visualization**: Real-time annotated video streams with detection statistics

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Camera Node   │────│  YOLO Detector   │────│  Data Logger    │
│  (USB/Depth)    │    │     Node         │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │  ROS2 Publishers │
                       │ - Bounding Boxes │
                       │ - Visualizations │
                       │ - JSON Data      │
                       └──────────────────┘
```

## Prerequisites

### Hardware Requirements

- **JetRover Robot**: Mecanum/Tank/Ackermann chassis with ROS2 support
- **Camera**: USB camera or Dabai DCW depth camera
- **Compute**: NVIDIA Jetson (Nano/Orin) or Raspberry Pi 5
- **Storage**: Minimum 8GB free space for model and logs

### Software Requirements

- **OS**: Ubuntu 22.04 (for Jetson) or Debian 12 (for Raspberry Pi)
- **ROS2**: Humble Hawksbill
- **Python**: 3.10+
- **CUDA**: 11.4+ (optional, for GPU acceleration)

## Installation

### 1. Clone the Repository

```bash
cd ~/ros2_ws/src
git clone https://github.com/Lcong99/smartagri-weed-detection-yolov8n-ros2.git AI_weed_detection_ros2_ws
cd ~/ros2_ws
```

### 2. Install Dependencies

```bash
# Install Python packages
pip install ultralytics opencv-python torch torchvision

# Install ROS2 dependencies
sudo apt install ros-humble-cv-bridge ros-humble-sensor-msgs
```

### 3. Build the Package

```bash
cd ~/ros2_ws
colcon build --packages-select yolo_detect
source install/setup.bash
```

### 4. Download Pre-trained Model

```bash
# Place your trained weed detection model in the models directory
cp your_weed_model.pt ~/ros2_ws/src/AI_weed_detection_ros2_ws/src/yolo_detect/models/best.pt

# Or download a test model
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O ~/ros2_ws/src/AI_weed_detection_ros2_ws/src/yolo_detect/models/yolov8n.pt
```

### 2. Install Dependencies

```bash
# Install Python packages
pip install ultralytics opencv-python torch torchvision

# Install ROS2 dependencies
sudo apt install ros-humble-cv-bridge ros-humble-sensor-msgs
```

### 3. Build the Package

```bash
cd ~/ros2_ws
colcon build --packages-select AI_weed_detection_ros2_ws
source install/setup.bash
```

### 4. Download Pre-trained Model

```bash
# Place your trained weed detection model in the models directory
cp your_weed_model.pt ~/ros2_ws/src/AI_weed_detection_ros2_ws/models/best.pt
```

## Usage

### Quick Start

```bash
# Make the script executable
chmod +x ~/ros2_ws/src/AI_weed_detection_ros2_ws/weed_detector.sh

# Run the interactive testing and launch script
cd ~/ros2_ws/src/AI_weed_detection_ros2_ws
./weed_detector.sh
```

### Manual Launch

```bash
# Launch with USB camera
ros2 launch yolo_detect yolo.launch.py camera_type:=usb

# Launch with depth camera
ros2 launch yolo_detect yolo.launch.py camera_type:=depth

# Launch with custom parameters
ros2 launch yolo_detect yolo.launch.py \
    camera_type:=depth \
    confidence_threshold:=0.3 \
    save_detections:=true \
    debug_mode:=true
```

### Parameters

| Parameter                | Type   | Default                                  | Description                          |
| ------------------------ | ------ | ---------------------------------------- | ------------------------------------ |
| `camera_type`          | string | `depth`                                | Camera type:`usb` or `depth`     |
| `camera_topic`         | string | `/depth_cam/depth_cam/color/image_raw` | ROS2 camera topic                    |
| `model_path`           | string | `models/best.pt`                       | Path to YOLO model                   |
| `confidence_threshold` | float  | `0.5`                                  | Detection confidence threshold       |
| `device`               | string | `cuda`                                 | Inference device:`cuda` or `cpu` |
| `save_detections`      | bool   | `true`                                 | Save detection images and data       |
| `output_dir`           | string | `/home/ubuntu/weed_detections`         | Output directory                     |
| `debug_mode`           | bool   | `true`                                 | Enable debug logging                 |

## ROS2 Topics

### Published Topics

| Topic                          | Type                  | Description                     |
| ------------------------------ | --------------------- | ------------------------------- |
| `/weed_detect/boxes`         | `Float32MultiArray` | Bounding box coordinates        |
| `/weed_detect/visualization` | `Image`             | Annotated image with detections |
| `/weed_detect/json_data`     | `String`            | JSON detection metadata         |

### Subscribed Topics

| Topic                                    | Type      | Description           |
| ---------------------------------------- | --------- | --------------------- |
| `/usb_cam/image_raw`                   | `Image` | USB camera feed       |
| `/depth_cam/depth_cam/color/image_raw` | `Image` | Depth camera RGB feed |

## Testing

The `weed_detector.sh` script provides comprehensive testing:

```bash
./weed_detector.sh
```

**Available Tests:**

1. **USB Camera Test** - Verify USB camera connectivity and formats
2. **Depth Camera Test** - Test depth camera functionality
3. **ROS2 Topics** - List available camera topics
4. **YOLO Model** - Validate model loading
5. **GPU Support** - Check CUDA availability
6. **Complete Test Suite** - Run all tests automatically
7. **Launch Detection** - Start weed detection system

## Project Structure

```
AI_weed_detection_ros2_ws/
├── 📁 src/
│   └── 📁 yolo_detect/                # ROS2 package
│       ├── 📁 config/
│       │   └── camera_config.yaml    # Camera configuration
│       ├── 📁 launch/
│       │   └── yolo.launch.py       # ROS2 launch file
│       ├── 📁 models/
│       │   ├── best.pt             # YOLO weed detection model
│       │   ├── yolov8n.pt          # Downloaded test model
│       │   └── test_model.py       # Model validation script
│       ├── 📁 yolo_detect/
│       │   ├── __init__.py
│       │   ├── yolo_node.py        # Main detection node
│       │   └── yolo_node_debug.py  # Debug version
│       ├── package.xml            # ROS2 package definition
│       ├── setup.py              # Python package setup
│       └── CMakeLists.txt        # Build configuration
├── weed_detector.sh              # Interactive testing script
├── README.md                    # This file
├── LICENSE                     # Apache 2.0 license
└── .gitignore                 # Git ignore file
```

## Configuration

### Camera Configuration

Edit `config/camera_config.yaml` to adjust camera settings:

```yaml
usb_cam:
  ros__parameters:
    video_device: "/dev/video0"
    framerate: 30.0
    image_width: 640
    image_height: 480
    # ... additional parameters
```

### Model Training

To train your own weed detection model:

1. Prepare your dataset with weed annotations
2. Use YOLOv8 training pipeline:

```python
from ultralytics import YOLO

# Load a model
model = YOLO('yolov8n.pt')  # load a pretrained model

# Train the model
results = model.train(data='weed_dataset.yaml', epochs=100, imgsz=640)
```

## Performance Metrics

- **Inference Speed**: ~15 FPS on Jetson Orin
- **Detection Accuracy**: Depends on trained model quality
- **Memory Usage**: ~2GB GPU memory (CUDA), ~1GB RAM (CPU)
- **Power Consumption**: ~10W additional load during inference

## Output Data

### Detection Files

Each detection saves:

- **Image**: `weed_YYYYMMDD_HHMMSS_mmm.jpg`
- **Metadata**: `weed_YYYYMMDD_HHMMSS_mmm.json`

### JSON Format

```json
{
  "timestamp": 1234567890.123,
  "frame_id": "camera_link",
  "frame_count": 42,
  "detections": [
    {
      "id": 0,
      "class": 0,
      "confidence": 0.85,
      "bbox": [100, 150, 200, 250],
      "center": [150, 200],
      "size": [100, 100],
      "area": 10000
    }
  ]
}
```

## Troubleshooting

### Common Issues

**Camera Not Detected**

```bash
# Check camera devices
ls /dev/video*
v4l2-ctl --list-devices

# Test camera manually
ros2 topic list | grep cam
```

**Model Loading Error**

- Verify model file exists and has correct permissions
- Check model compatibility with ultralytics version
- Test model loading manually

**Low FPS Performance**

- Enable GPU acceleration
- Reduce confidence threshold
- Optimize camera resolution

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Hiwonder** for the JetRover platform and documentation
- **Ultralytics** for the YOLOv8 framework
- **ROS2 Community** for the robotics middleware
- **Open Source Computer Vision** community

