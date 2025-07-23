#!/bin/bash

# 🔍 YOLO Performance Diagnosis Script for Jetson Orin Nano
# This script helps identify why you're getting only 1 FPS

echo "🔍 YOLO Performance Diagnosis"
echo "============================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
}

check_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
}

check_warning() {
    echo -e "${YELLOW}⚠️  WARNING${NC}: $1"
}

# 1. Check Jetson Model
echo -e "\n1. 🤖 Checking Jetson Model..."
if [[ -f /proc/device-tree/model ]]; then
    MODEL=$(cat /proc/device-tree/model)
    echo "   Device: $MODEL"
    if [[ $MODEL == *"Orin Nano"* ]]; then
        check_pass "Jetson Orin Nano detected"
    else
        check_warning "Different Jetson model detected"
    fi
else
    check_fail "Not running on Jetson device"
fi

# 2. Check Power Mode
echo -e "\n2. ⚡ Checking Power Mode..."
if command -v nvpmodel &> /dev/null; then
    POWER_MODE=$(sudo nvpmodel -q | grep "NV Power Mode" | cut -d: -f2)
    echo "   Current mode:$POWER_MODE"
    if [[ $POWER_MODE == *"MAXN"* ]]; then
        check_pass "Maximum performance mode enabled"
    else
        check_fail "Not in maximum performance mode. Run: sudo nvpmodel -m 0"
    fi
else
    check_fail "nvpmodel command not found"
fi

# 3. Check GPU Status
echo -e "\n3. 🔥 Checking GPU Status..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total,memory.free,utilization.gpu,temperature.gpu --format=csv,noheader,nounits
    check_pass "GPU is available"
    
    # Check temperature
    TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits)
    if [[ $TEMP -gt 80 ]]; then
        check_fail "GPU temperature too high: ${TEMP}°C (thermal throttling likely)"
    else
        check_pass "GPU temperature normal: ${TEMP}°C"
    fi
else
    check_fail "nvidia-smi not available"
fi

# 4. Check PyTorch Installation
echo -e "\n4. 🐍 Checking PyTorch..."
python3 << 'EOF'
import sys
try:
    import torch
    print(f"   PyTorch version: {torch.__version__}")
    print(f"   CUDA available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"   CUDA version: {torch.version.cuda}")
        print(f"   GPU device: {torch.cuda.get_device_name(0)}")
        
        # Test GPU performance
        import time
        x = torch.randn(1000, 1000).cuda()
        start = time.time()
        y = torch.matmul(x, x)
        torch.cuda.synchronize()
        gpu_time = time.time() - start
        print(f"   GPU matmul test: {gpu_time:.4f}s")
        
        if gpu_time > 0.1:
            print("❌ GPU performance seems slow")
        else:
            print("✅ GPU performance normal")
    else:
        print("❌ CUDA not available in PyTorch")
        
except ImportError:
    print("❌ PyTorch not installed")
except Exception as e:
    print(f"❌ PyTorch error: {e}")
EOF

# 5. Check System Resources
echo -e "\n5. 💾 Checking System Resources..."
echo "   Memory usage:"
free -h
echo "   Disk usage:"
df -h /
echo "   CPU usage:"
top -bn1 | grep "Cpu(s)"

# Check swap
SWAP_TOTAL=$(free -h | grep Swap | awk '{print $2}')
if [[ $SWAP_TOTAL == "0B" ]]; then
    check_fail "No swap space available"
else
    check_pass "Swap space: $SWAP_TOTAL"
fi

# 6. Check YOLO Model
echo -e "\n6. 🎯 Checking YOLO Model..."
MODEL_PATH="$HOME/ros2_ws/src/yolo_detect/models/best.pt"
if [[ -f "$MODEL_PATH" ]]; then
    MODEL_SIZE=$(du -h "$MODEL_PATH" | cut -f1)
    echo "   Model size: $MODEL_SIZE"
    check_pass "YOLO model found"
    
    # Test model loading speed
    python3 << EOF
import sys
sys.path.append('$HOME/ros2_ws/src/yolo_detect')
import time
try:
    from ultralytics import YOLO
    start = time.time()
    model = YOLO('$MODEL_PATH')
    load_time = time.time() - start
    print(f"   Model load time: {load_time:.2f}s")
    
    if load_time > 10:
        print("❌ Model loading too slow")
    else:
        print("✅ Model loading normal")
        
    # Test inference speed
    import torch
    if torch.cuda.is_available():
        model.to('cuda')
        
    # Warmup
    dummy_input = torch.randn(1, 3, 640, 640)
    if torch.cuda.is_available():
        dummy_input = dummy_input.cuda()
        
    start = time.time()
    results = model(dummy_input)
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    inference_time = time.time() - start
    
    print(f"   Inference time: {inference_time:.3f}s")
    fps = 1.0 / inference_time
    print(f"   Theoretical FPS: {fps:.1f}")
    
    if fps < 5:
        print("❌ Inference too slow")
    else:
        print("✅ Inference speed acceptable")
        
except Exception as e:
    print(f"❌ Model test failed: {e}")
EOF
else
    check_fail "YOLO model not found at $MODEL_PATH"
fi

# 7. Check ROS2 Topics
echo -e "\n7. 📡 Checking ROS2 Topics..."
if command -v ros2 &> /dev/null; then
    echo "   Available camera topics:"
    ros2 topic list | grep -E "(image|camera)" || echo "   No camera topics found"
    
    # Check if depth camera is running
    if ros2 topic list | grep -q "depth_cam"; then
        check_pass "Depth camera topics available"
    else
        check_warning "Depth camera not running"
    fi
else
    check_fail "ROS2 not available"
fi

# 8. Performance Recommendations
echo -e "\n8. 🚀 Performance Recommendations:"
echo "   Based on the diagnosis above, here are the recommended fixes:"
echo ""
echo "   📋 Quick Fixes:"
echo "   1. Enable max performance: sudo nvpmodel -m 0 && sudo jetson_clocks"
echo "   2. Install optimized PyTorch for Jetson"
echo "   3. Use smaller input size (416x416 instead of 640x640)"
echo "   4. Enable TensorRT optimization"
echo "   5. Add swap space if missing"
echo ""
echo "   🔧 Advanced Optimizations:"
echo "   1. Use threading for image processing"
echo "   2. Skip frames (process every 2nd frame)"
echo "   3. Reduce confidence threshold"
echo "   4. Limit max detections"
echo ""
echo "   🎯 Expected Results:"
echo "   - Current: 1 FPS"
echo "   - After optimization: 12-20 FPS"
echo ""
echo "   📝 Next Steps:"
echo "   1. Run the optimization script: ./jetson_optimization.sh"
echo "   2. Use the optimized YOLO node"
echo "   3. Monitor performance with: ros2 topic hz /weed_detect/visualization"

echo -e "\n🔍 Diagnosis Complete!"
echo "Run the optimization script to fix identified issues."
