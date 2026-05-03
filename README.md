# 🌱 Smart Agriculture Weed Detection (YOLOv8 + ROS2)

An end-to-end **edge AI perception pipeline** for real-time weed detection, built using YOLOv8n and ROS2 on the JetRover platform.

This project demonstrates how deep learning models can be integrated into a robotics system for precision agriculture, enabling automated weed identification in real-world environments on resource-constrained devices.

---

##  Key Highlights

* Real-time weed detection using **YOLOv8n (lightweight, edge-optimized)**
* Full **ROS2-based perception pipeline** (camera → inference → publishing)
* Designed for **embedded deployment** (Jetson Nano / Orin)
* Modular and extensible architecture for robotics integration
* Built-in **data logging, debugging, and visualization tools**

---

## Problem Motivation

Weed detection in agricultural environments is non-trivial due to:

* **Green-on-green problem** (weeds vs crops visually similar)
* Variable lighting and outdoor conditions
* Need for **real-time inference on low-power hardware**

This project addresses these constraints by combining:

* Efficient object detection (YOLOv8n)
* Robotics middleware (ROS2)
* Edge deployment considerations (Jetson platform)

---

## 🎥 Demo


https://github.com/user-attachments/assets/66446c6e-16b6-4a4b-9fba-b35be7b9eaea

https://github.com/user-attachments/assets/e7de20ba-d96a-41b4-8182-a8dd31e86234


---

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
                       │ - Visualization  │
                       │ - JSON Data      │
                       └──────────────────┘
```

### Pipeline Explanation

1. Camera node publishes image stream
2. YOLO detection node performs real-time inference
3. Results are published as:

   * bounding boxes
   * annotated image stream
   * structured JSON metadata
4. Data logger stores outputs for offline analysis

This modular design enables seamless integration with downstream robotics tasks such as navigation or precision spraying.

---

## My Contribution

* Designed and implemented the full ROS2-based perception pipeline
* Integrated YOLOv8 inference into a real-time robotics workflow
* Built modular nodes for camera input, detection, and publishing
* Implemented structured logging (image + JSON outputs)
* Developed testing and debugging utilities for system validation
* Optimized system for edge deployment on Jetson hardware

---

## Tech Stack

* **Framework**: ROS2 (Humble)
* **Model**: YOLOv8n (Ultralytics)
* **Language**: Python 3.10
* **Hardware**: NVIDIA Jetson (Nano / Orin), JetRover platform
* **Libraries**: OpenCV, PyTorch

---

## Installation

### 1. Clone Repository

```bash
cd ~/ros2_ws/src
git clone https://github.com/Lcong99/smartagri-weed-detection-yolov8n-ros2.git
cd ~/ros2_ws
```

### 2. Install Dependencies

```bash
pip install ultralytics opencv-python torch torchvision

sudo apt update
sudo apt install -y \
  ros-humble-cv-bridge \
  ros-humble-sensor-msgs
```

### 3. Build ROS2 Package

```bash
colcon build --packages-select yolo_detect
source install/setup.bash
```

### 4. Add Model

```bash
mkdir -p src/yolo_detect/models

# Place trained model
cp best.pt src/yolo_detect/models/best.pt

# OR download base model
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt \
  -O src/yolo_detect/models/yolov8n.pt
```

---

##  Usage

### Quick Start

```bash
chmod +x weed_detector.sh
./weed_detector.sh
```

### Manual Launch

```bash
ros2 launch yolo_detect yolo.launch.py camera_type:=usb

ros2 launch yolo_detect yolo.launch.py camera_type:=depth

ros2 launch yolo_detect yolo.launch.py \
    camera_type:=depth \
    confidence_threshold:=0.3 \
    save_detections:=true \
    debug_mode:=true
```

---

##  Parameters

| Parameter            | Type   | Default                  | Description          |
| -------------------- | ------ | ------------------------ | -------------------- |
| camera_type          | string | depth                    | usb / depth          |
| camera_topic         | string | /depth_cam/.../image_raw | Input image topic    |
| model_path           | string | models/best.pt           | YOLO model path      |
| confidence_threshold | float  | 0.5                      | Detection threshold  |
| device               | string | cuda                     | cuda / cpu           |
| save_detections      | bool   | true                     | Save output data     |
| output_dir           | string | ~/weed_detections        | Output directory     |
| debug_mode           | bool   | true                     | Enable debug logging |

---

## 📡 ROS2 Interfaces

### Published Topics

| Topic                      | Type              | Description              |
| -------------------------- | ----------------- | ------------------------ |
| /weed_detect/boxes         | Float32MultiArray | Bounding box coordinates |
| /weed_detect/visualization | Image             | Annotated output stream  |
| /weed_detect/json_data     | String            | Detection metadata       |

### Subscribed Topics

| Topic                    | Type  | Description           |
| ------------------------ | ----- | --------------------- |
| /usb_cam/image_raw       | Image | USB camera feed       |
| /depth_cam/.../image_raw | Image | Depth camera RGB feed |

---

##  Testing

Run full system validation:

```bash
./weed_detector.sh
```

Includes:

* Camera detection test
* ROS2 topic validation
* Model loading check
* GPU (CUDA) availability
* End-to-end pipeline test

---

##  Performance

* ~15 FPS on Jetson Orin (GPU)
* ~5–8 FPS on CPU-only systems
* Model: YOLOv8n (low-latency optimized)

Performance depends on:

* input resolution
* hardware configuration
* model size

---

## 📁 Project Structure

```
.
├── src/
│   └── yolo_detect/
│       ├── config/
│       ├── launch/
│       ├── models/
│       ├── yolo_detect/
│       ├── package.xml
│       ├── setup.py
│       └── CMakeLists.txt
├── weed_detector.sh
├── README.md
├── LICENSE
└── .gitignore
```

---

## 📤 Output Format

Each detection produces:

* Image: `weed_<timestamp>.jpg`
* Metadata: `weed_<timestamp>.json`

### JSON Schema

```json
{
  "timestamp": 0.0,
  "detections": [
    {
      "class": 0,
      "confidence": 0.85,
      "bbox": [x1, y1, x2, y2]
    }
  ]
}
```

---

##  Model Training (Optional)

```python
from ultralytics import YOLO

model = YOLO('yolov8n.pt')
model.train(data='weed_dataset.yaml', epochs=100, imgsz=640)
```

---

## ⚠️ Troubleshooting

**Camera not detected**

```bash
ls /dev/video*
ros2 topic list
```

**Low FPS**

* Enable CUDA
* Reduce resolution
* Use smaller model

**Model load issues**

* Verify file path
* Check compatibility with ultralytics version

---

## License

Apache License 2.0

---

## Acknowledgments

* Ultralytics (YOLOv8)
* ROS2 community
* Jetson platform ecosystem
* Open-source computer vision community
