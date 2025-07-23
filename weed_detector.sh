#!/usr/bin/env bash
set -e

# ————————————————————————————————
# Source ROS 2 Humble and your workspace
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
# ————————————————————————————————

echo "🤖 JetRover Weed Detection System v2.0"
echo "============================================="
echo "Enhanced with multi-color visualization and data transmission"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration file path
CONFIG_FILE="$HOME/.jetrover_weed_config"

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

detect_camera_type() {
    if ros2 topic list 2>/dev/null | grep -q "/depth_cam/rgb"; then
        echo "depth"
    elif ros2 topic list 2>/dev/null | grep -q "/usb_cam"; then
        echo "usb"
    else
        echo "none"
    fi
}

install_dependencies() {
    echo -e "\n${BLUE}📦 Checking and installing dependencies...${NC}"
    
    # Python packages
    python3 -m pip install --upgrade pip
    python3 -m pip install psutil GPUtil requests
    
    # System packages
    if ! command_exists v4l2-ctl; then
        echo "Installing v4l-utils..."
        sudo apt-get update && sudo apt-get install -y v4l-utils
    fi
    
    echo -e "${GREEN}✅ Dependencies installed${NC}"
}

setup_remote_receiver() {
    echo -e "\n${BLUE}🖥️  Setting up remote data receiver on your Mac...${NC}"
    echo ""
    echo "Run this Python script on your Mac to receive data:"
    echo ""
    cat << 'EOF'
#!/usr/bin/env python3
# Save this as weed_receiver.py on your Mac

from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# Create data directory
os.makedirs('received_weed_data', exist_ok=True)

@app.route('/weed_data', methods=['POST'])
def receive_weed_data():
    try:
        data = request.get_json()
        
        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        filename = f'received_weed_data/weed_data_{timestamp}.json'
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Print summary
        detections = data.get('detections', [])
        neutral_count = sum(1 for d in detections if d['class'] == 0)
        opp_count = sum(1 for d in detections if d['class'] == 1)
        
        print(f"📦 Received data - Frame: {data.get('frame_count', 'N/A')}, "
              f"Neutral: {neutral_count}, Opp: {opp_count}")
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("🌐 Weed data receiver running on http://0.0.0.0:8080")
    print("Press Ctrl+C to stop")
    app.run(host='0.0.0.0', port=8080, debug=True)
EOF
    
    echo ""
    echo "Install Flask on your Mac with: pip3 install flask"
    echo "Then run: python3 weed_receiver.py"
    echo ""
}

configure_network() {
    echo -e "\n${BLUE}🌐 Network Configuration${NC}"
    
    # Load existing config if available
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
        echo "Current configuration:"
        echo "  Remote Host: ${REMOTE_HOST:-Not set}"
        echo "  Remote Port: ${REMOTE_PORT:-8080}"
        echo ""
    fi
    
    read -p "Enter your Mac's IP address (or press Enter to skip): " new_host
    if [ ! -z "$new_host" ]; then
        REMOTE_HOST="$new_host"
        echo "REMOTE_HOST=\"$REMOTE_HOST\"" > "$CONFIG_FILE"
        echo "REMOTE_PORT=\"${REMOTE_PORT:-8080}\"" >> "$CONFIG_FILE"
        echo -e "${GREEN}✅ Network configuration saved${NC}"
    fi
}

test_network_connection() {
    if [ -z "$REMOTE_HOST" ]; then
        echo -e "${YELLOW}⚠️  No remote host configured${NC}"
        return 1
    fi
    
    echo -e "\n${BLUE}🔌 Testing network connection to $REMOTE_HOST:${REMOTE_PORT:-8080}...${NC}"
    
    if ping -c 1 -W 2 "$REMOTE_HOST" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Host is reachable${NC}"
        
        # Test if receiver is running
        if curl -s -o /dev/null -w "%{http_code}" "http://$REMOTE_HOST:${REMOTE_PORT:-8080}" | grep -q "404\|200"; then
            echo -e "${GREEN}✅ Receiver service detected${NC}"
        else
            echo -e "${YELLOW}⚠️  Receiver service not detected. Make sure weed_receiver.py is running on your Mac${NC}"
        fi
    else
        echo -e "${RED}❌ Cannot reach host. Check IP address and network connection${NC}"
    fi
}

test_yolo_model() {
    echo -e "\n${BLUE}🧪 Testing YOLO model load...${NC}"
    MODEL="$HOME/ros2_ws/src/yolo_detect/models/best.pt"
    
    python3 - <<PYCODE
import os, sys
from ultralytics import YOLO
import torch

path = os.path.expanduser("$MODEL")
if not os.path.isfile(path):
    print("❌ Model file not found at {}".format(path))
    sys.exit(1)

try:
    model = YOLO(path)
    print("✅ YOLO model loaded successfully")
    print("   Classes: 0=neutral_weed, 1=opp_weed")
    print("   Device: {}".format('CUDA' if torch.cuda.is_available() else 'CPU'))
except Exception as e:
    print("❌ Failed to load YOLO model: {}".format(e))
    sys.exit(1)
PYCODE
}

launch_weed_detection_performance() {
    echo -e "\n${BLUE}🚀 Launching Weed Detection in PERFORMANCE Mode...${NC}"
    echo "⚡ Optimized for real-time visualization and demo"
    
    camera_type=$(detect_camera_type)
    echo "🎯 Detected camera type: $camera_type"
    
    case $camera_type in
        depth)
            echo -e "${GREEN}🚀 Running YOLO on depth camera - PERFORMANCE MODE${NC}"
            echo "⚡ Settings: Skip frames=1, Resize=640px, Fast overlay"
            python3 -m yolo_detect.yolo_node --ros-args \
                -p camera_type:=depth \
                -p camera_topic:=/depth_cam/rgb/image_raw \
                -p confidence_threshold:=0.3 \
                -p save_detections:=false \
                -p debug_mode:=false \
                -p enable_transmission:=false \
                -p performance_mode:=true \
                -p skip_frames:=1 \
                -p resize_width:=640 \
                -p visualization_quality:=0.8 \
                -p enable_overlay:=true \
                -p save_frequency:=60
            ;;
        usb)
            echo -e "${GREEN}🚀 Running YOLO on USB camera - PERFORMANCE MODE${NC}"
            python3 -m yolo_detect.yolo_node --ros-args \
                -p camera_type:=usb \
                -p camera_topic:=/usb_cam/image_raw \
                -p confidence_threshold:=0.3 \
                -p save_detections:=false \
                -p debug_mode:=false \
                -p enable_transmission:=false \
                -p performance_mode:=true \
                -p skip_frames:=1 \
                -p resize_width:=640 \
                -p visualization_quality:=0.8
            ;;
        *)
            echo -e "${RED}❌ No compatible camera detected. Please check camera connection.${NC}"
            ;;
    esac
}

launch_weed_detection_demo() {
    echo -e "\n${BLUE}🎭 Launching Weed Detection in DEMO Mode...${NC}"
    echo "🎯 Ultra-fast mode for live demonstrations"
    
    camera_type=$(detect_camera_type)
    echo "🎯 Detected camera type: $camera_type"
    
    case $camera_type in
        depth)
            echo -e "${GREEN}🚀 Running YOLO - DEMO MODE (Maximum FPS)${NC}"
            echo "⚡ Settings: Skip frames=2, Resize=480px, Minimal overlay"
            python3 -m yolo_detect.yolo_node --ros-args \
                -p camera_type:=depth \
                -p camera_topic:=/depth_cam/rgb/image_raw \
                -p confidence_threshold:=0.35 \
                -p save_detections:=false \
                -p debug_mode:=false \
                -p enable_transmission:=false \
                -p performance_mode:=true \
                -p skip_frames:=2 \
                -p resize_width:=480 \
                -p visualization_quality:=0.6 \
                -p enable_overlay:=true \
                -p save_frequency:=999999
            ;;
        usb)
            echo -e "${GREEN}🚀 Running YOLO - DEMO MODE (Maximum FPS)${NC}"
            python3 -m yolo_detect.yolo_node --ros-args \
                -p camera_type:=usb \
                -p camera_topic:=/usb_cam/image_raw \
                -p confidence_threshold:=0.35 \
                -p save_detections:=false \
                -p debug_mode:=false \
                -p enable_transmission:=false \
                -p performance_mode:=true \
                -p skip_frames:=2 \
                -p resize_width:=480 \
                -p visualization_quality:=0.6
            ;;
        *)
            echo -e "${RED}❌ No compatible camera detected.${NC}"
            ;;
    esac
}

launch_weed_detection_enhanced() {
    echo -e "\n${BLUE}🚀 Launching Enhanced Weed Detection System...${NC}"
    
    # Load config
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
    fi
    
    camera_type=$(detect_camera_type)
    echo "🎯 Detected camera type: $camera_type"
    
    # Build parameter arguments
    PARAMS=""
    if [ ! -z "$REMOTE_HOST" ]; then
        PARAMS="$PARAMS -p remote_host:=$REMOTE_HOST -p enable_transmission:=true"
        echo "📡 Network transmission enabled to $REMOTE_HOST"
    fi
    
    case $camera_type in
        depth)
            echo -e "${GREEN}🚀 Running enhanced YOLO on depth camera (RGB stream)${NC}"
            python3 -m yolo_detect.yolo_node --ros-args \
                -p camera_type:=depth \
                -p camera_topic:=/depth_cam/rgb/image_raw \
                -p confidence_threshold:=0.25 \
                -p save_detections:=true \
                -p debug_mode:=true \
                $PARAMS
            ;;
        usb)
            echo -e "${GREEN}🚀 Running enhanced YOLO on USB camera${NC}"
            python3 -m yolo_detect.yolo_node --ros-args \
                -p camera_type:=usb \
                -p camera_topic:=/usb_cam/image_raw \
                -p confidence_threshold:=0.25 \
                -p save_detections:=true \
                -p debug_mode:=true \
                $PARAMS
            ;;
        *)
            echo -e "${RED}❌ No compatible camera detected. Please check camera connection.${NC}"
            ;;
    esac
}

launch_weed_detection_offline() {
    echo -e "\n${BLUE}🚀 Launching Weed Detection in OFFLINE Mode...${NC}"
    echo "📴 Network transmission disabled - Local analysis only"
    
    camera_type=$(detect_camera_type)
    echo "🎯 Detected camera type: $camera_type"
    
    case $camera_type in
        depth)
            echo -e "${GREEN}🚀 Running YOLO on depth camera (RGB stream) - OFFLINE${NC}"
            python3 -m yolo_detect.yolo_node --ros-args \
                -p camera_type:=depth \
                -p camera_topic:=/depth_cam/rgb/image_raw \
                -p confidence_threshold:=0.25 \
                -p save_detections:=true \
                -p debug_mode:=true \
                -p enable_transmission:=false
            ;;
        usb)
            echo -e "${GREEN}🚀 Running YOLO on USB camera - OFFLINE${NC}"
            python3 -m yolo_detect.yolo_node --ros-args \
                -p camera_type:=usb \
                -p camera_topic:=/usb_cam/image_raw \
                -p confidence_threshold:=0.25 \
                -p save_detections:=true \
                -p debug_mode:=true \
                -p enable_transmission:=false
            ;;
        *)
            echo -e "${RED}❌ No compatible camera detected. Please check camera connection.${NC}"
            ;;
    esac
}

check_data_files() {
    DATA_DIR="$HOME/jetrover_weed_data"
    echo -e "\n${BLUE}📁 Checking data files in $DATA_DIR...${NC}"
    
    if [ -d "$DATA_DIR" ]; then
        echo "Latest detection logs:"
        ls -la "$DATA_DIR/logs/" 2>/dev/null | tail -5 || echo "  No logs yet"
        echo ""
        echo "Latest performance logs:"
        ls -la "$DATA_DIR/performance/" 2>/dev/null | tail -5 || echo "  No performance logs yet"
        echo ""
        echo "Total images saved: $(find "$DATA_DIR/images" -name "*.jpg" 2>/dev/null | wc -l || echo 0)"
        echo "Total detections saved: $(find "$DATA_DIR/detections" -name "*.json" 2>/dev/null | wc -l || echo 0)"
    else
        echo "No data directory found yet. Run detection first."
    fi
}

analyze_offline_data() {
    echo -e "\n${BLUE}📊 Analyzing Offline Detection Data...${NC}"
    
    DATA_DIR="$HOME/jetrover_weed_data"
    
    if [ ! -d "$DATA_DIR" ]; then
        echo -e "${RED}No data directory found. Run detection first.${NC}"
        return
    fi
    
    # Run Python analysis script
    python3 - << 'PYEOF'
import os
import json
import csv
import numpy as np
from datetime import datetime
import glob

data_dir = os.path.expanduser("~/jetrover_weed_data")

print("\n📈 WEED DETECTION ANALYSIS REPORT")
print("=" * 50)

# Analyze detection logs
detection_files = glob.glob(os.path.join(data_dir, "logs", "detections_*.csv"))
if detection_files:
    latest_detection = max(detection_files, key=os.path.getctime)
    print(f"\n📁 Analyzing: {os.path.basename(latest_detection)}")
    
    neutral_count = 0
    opp_count = 0
    confidences = {'neutral': [], 'opp': []}
    
    with open(latest_detection, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['class'] == '0':
                neutral_count += 1
                confidences['neutral'].append(float(row['confidence']))
            else:
                opp_count += 1
                confidences['opp'].append(float(row['confidence']))
    
    print(f"\n🌿 Detection Summary:")
    print(f"  - Neutral weeds: {neutral_count}")
    print(f"  - Opposite weeds: {opp_count}")
    print(f"  - Total detections: {neutral_count + opp_count}")
    
    if confidences['neutral']:
        print(f"\n📊 Neutral Weed Confidence:")
        print(f"  - Average: {np.mean(confidences['neutral']):.3f}")
        print(f"  - Min: {np.min(confidences['neutral']):.3f}")
        print(f"  - Max: {np.max(confidences['neutral']):.3f}")
    
    if confidences['opp']:
        print(f"\n📊 Opposite Weed Confidence:")
        print(f"  - Average: {np.mean(confidences['opp']):.3f}")
        print(f"  - Min: {np.min(confidences['opp']):.3f}")
        print(f"  - Max: {np.max(confidences['opp']):.3f}")

# Analyze performance logs
perf_files = glob.glob(os.path.join(data_dir, "performance", "performance_*.csv"))
if perf_files:
    latest_perf = max(perf_files, key=os.path.getctime)
    print(f"\n\n🚀 Performance Analysis")
    print(f"📁 File: {os.path.basename(latest_perf)}")
    
    fps_values = []
    frame_times = []
    detection_times = []
    cpu_values = []
    gpu_values = []
    
    with open(latest_perf, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fps_values.append(float(row['fps']))
            frame_times.append(float(row['frame_time_ms']))
            detection_times.append(float(row['detection_time_ms']))
            cpu_values.append(float(row['cpu_percent']))
            if row['gpu_percent']:
                gpu_values.append(float(row['gpu_percent']))
    
    if fps_values:
        print(f"\n📊 FPS Statistics:")
        print(f"  - Average: {np.mean(fps_values):.1f}")
        print(f"  - Min: {np.min(fps_values):.1f}")
        print(f"  - Max: {np.max(fps_values):.1f}")
    
    if frame_times:
        print(f"\n⏱️  Processing Time:")
        print(f"  - Avg Frame Time: {np.mean(frame_times):.2f} ms")
        print(f"  - Avg Detection Time: {np.mean(detection_times):.2f} ms")
    
    if cpu_values:
        print(f"\n💻 Resource Usage:")
        print(f"  - Avg CPU: {np.mean(cpu_values):.1f}%")
        if gpu_values:
            print(f"  - Avg GPU: {np.mean(gpu_values):.1f}%")

# Count saved files
image_count = len(glob.glob(os.path.join(data_dir, "images", "*.jpg")))
json_count = len(glob.glob(os.path.join(data_dir, "detections", "*.json")))

print(f"\n\n📁 Data Storage Summary:")
print(f"  - Saved images: {image_count}")
print(f"  - Saved JSON files: {json_count}")

# Latest session summary
summary_files = glob.glob(os.path.join(data_dir, "performance", "summary_*.json"))
if summary_files:
    latest_summary = max(summary_files, key=os.path.getctime)
    with open(latest_summary, 'r') as f:
        summary = json.load(f)
    
    print(f"\n\n📋 Session Summary:")
    print(f"  - Session ID: {summary['session_id']}")
    print(f"  - Total frames: {summary['total_frames']}")
    print(f"  - Duration: {summary['duration_seconds']:.1f} seconds")
    print(f"  - Average FPS: {summary['average_fps']:.1f}")

print("\n" + "=" * 50)
print("✅ Analysis complete!")
PYEOF
}

generate_analysis_report() {
    echo -e "\n${BLUE}📝 Generating Detailed Analysis Report...${NC}"
    
    REPORT_FILE="$HOME/jetrover_weed_data/analysis_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "JETROVER WEED DETECTION ANALYSIS REPORT"
        echo "Generated: $(date)"
        echo "========================================"
        echo ""
        
        # System info
        echo "SYSTEM INFORMATION:"
        echo "- Hostname: $(hostname)"
        echo "- Platform: $(uname -a)"
        echo "- ROS2 Distribution: Humble"
        echo ""
        
        # Data summary
        echo "DATA COLLECTION SUMMARY:"
        find ~/jetrover_weed_data -type f -name "*.csv" -o -name "*.json" -o -name "*.jpg" | wc -l | xargs echo "- Total files:"
        du -sh ~/jetrover_weed_data | xargs echo "- Total size:"
        echo ""
        
        # Run Python analysis and append
        python3 -c "
import os, json, csv, glob
import numpy as np

data_dir = os.path.expanduser('~/jetrover_weed_data')

# Get all performance files
perf_files = sorted(glob.glob(os.path.join(data_dir, 'performance', 'performance_*.csv')))
if perf_files:
    print('PERFORMANCE METRICS ACROSS ALL SESSIONS:')
    all_fps = []
    all_frame_times = []
    
    for pf in perf_files:
        with open(pf, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                all_fps.append(float(row['fps']))
                all_frame_times.append(float(row['frame_time_ms']))
    
    print(f'- Overall Average FPS: {np.mean(all_fps):.2f}')
    print(f'- Overall Average Frame Time: {np.mean(all_frame_times):.2f} ms')
    print(f'- FPS Standard Deviation: {np.std(all_fps):.2f}')
    print()

# Detection statistics
detection_files = sorted(glob.glob(os.path.join(data_dir, 'logs', 'detections_*.csv')))
if detection_files:
    print('DETECTION STATISTICS:')
    total_neutral = 0
    total_opp = 0
    
    for df in detection_files:
        with open(df, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['class'] == '0':
                    total_neutral += 1
                else:
                    total_opp += 1
    
    total = total_neutral + total_opp
    print(f'- Total Detections: {total}')
    print(f'- Neutral Weeds: {total_neutral} ({total_neutral/total*100:.1f}%)')
    print(f'- Opposite Weeds: {total_opp} ({total_opp/total*100:.1f}%)')
"
    } > "$REPORT_FILE"
    
    echo -e "\n${GREEN}✅ Report saved to: $REPORT_FILE${NC}"
    echo -e "${YELLOW}📋 Opening report...${NC}"
    cat "$REPORT_FILE"
}

view_visualization() {
    echo -e "\n${BLUE}👁️  Opening visualization in rqt_image_view...${NC}"
    echo "Select topic: /weed_detect/visualization"
    ros2 run rqt_image_view rqt_image_view &
}

monitor_performance() {
    echo -e "\n${BLUE}📊 Monitoring performance data...${NC}"
    ros2 topic echo /weed_detect/performance_stats
}

run_comprehensive_test() {
    echo -e "\n${BLUE}🧪 Running Comprehensive System Test...${NC}"
    echo "========================================"
    
    # Install dependencies
    install_dependencies
    
    # Test model
    test_yolo_model
    
    # Test network if configured
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
        test_network_connection
    fi
    
    # Check data files
    check_data_files
    
    echo -e "\n${GREEN}✅ System test completed!${NC}"
}

main_menu() {
    # Load config if exists
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
    fi
    
    while true; do
        echo -e "\n${BLUE}====== JetRover Enhanced Weed Detection ======${NC}"
        echo -e "${GREEN}--- PERFORMANCE MODES ---${NC}"
        echo "1) ⚡ PERFORMANCE mode (balanced speed/quality)"
        echo "2) 🎭 DEMO mode (maximum FPS for presentations)"
        echo ""
        echo -e "${GREEN}--- ONLINE MODE ---${NC}"
        echo "3) 🌐 Launch detection WITH network transmission"
        echo "4) 🌐 Configure network transmission"
        echo "5) 🖥️  Show Mac receiver setup"
        echo "6) 🔌 Test network connection"
        echo ""
        echo -e "${YELLOW}--- OFFLINE MODE ---${NC}"
        echo "7) 📴 Launch detection WITHOUT network (full quality)"
        echo "8) 📊 Analyze offline data"
        echo "9) 📝 Generate analysis report"
        echo ""
        echo -e "${BLUE}--- COMMON FEATURES ---${NC}"
        echo "10) 👁️  View live visualization (rqt_image_view)"
        echo "11) 📊 Monitor real-time performance"
        echo "12) 📁 Check data files"
        echo "13) 🧪 Run system test"
        echo "14) 📦 Install/update dependencies"
        echo "0) Exit"
        echo ""
        if [ ! -z "$REMOTE_HOST" ]; then
            echo -e "${GREEN}✅ Network configured: $REMOTE_HOST:${REMOTE_PORT:-8080}${NC}"
        else
            echo -e "${YELLOW}⚠️  Network not configured (offline mode available)${NC}"
        fi
        echo ""
        read -p "Select an option: " opt
        
        case $opt in
            1) launch_weed_detection_performance ;;
            2) launch_weed_detection_demo ;;
            3) launch_weed_detection_enhanced ;;
            4) configure_network ;;
            5) setup_remote_receiver ;;
            6) test_network_connection ;;
            7) launch_weed_detection_offline ;;
            8) analyze_offline_data ;;
            9) generate_analysis_report ;;
            10) view_visualization ;;
            11) monitor_performance ;;
            12) check_data_files ;;
            13) run_comprehensive_test ;;
            14) install_dependencies ;;
            0) echo "👋 Goodbye!"; exit 0 ;;
            *) echo -e "${RED}❌ Invalid option${NC}" ;;
        esac
    done
}

# Start the enhanced menu
main_menu
