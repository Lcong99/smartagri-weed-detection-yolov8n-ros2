#!/usr/bin/env python3

import torch
import torch.serialization
from ultralytics import YOLO
import sys
import os

def safe_load_yolo_model(model_path):
    """Safely load YOLO model with proper error handling"""
    try:
        print(f"📦 Loading YOLO model from: {model_path}")
        
        # For PyTorch 2.6+, we need to set weights_only=False
        original_load = torch.load
        torch.load = lambda *args, **kwargs: original_load(*args, **kwargs, weights_only=False)
        
        model = YOLO(model_path)
        
        # Restore original torch.load
        torch.load = original_load
        
        print("✅ YOLO model loaded successfully!")
        return model
        
    except Exception as e:
        print(f"❌ Failed to load YOLO model: {e}")
        return None

# Test loading
model = safe_load_yolo_model('best.pt')

if model and torch.cuda.is_available():
    print("🔥 Testing GPU inference...")
    model.to('cuda')
    
    # Test inference speed
    import time
    import numpy as np
    
    dummy_input = np.random.randint(0, 255, (416, 416, 3), dtype=np.uint8)
    
    # Warmup
    for i in range(3):
        results = model(dummy_input, verbose=False)
    
    # Benchmark
    start = time.time()
    results = model(dummy_input, verbose=False)
    torch.cuda.synchronize()
    inference_time = time.time() - start
    
    fps = 1.0 / inference_time
    print(f"✅ Inference time: {inference_time:.3f}s")
    print(f"✅ Theoretical FPS: {fps:.1f}")
    
    # Try TensorRT export
    try:
        print("🚀 Exporting to TensorRT...")
        model.export(format='engine', imgsz=416, device=0)
        print("✅ TensorRT export successful!")
    except Exception as e:
        print(f"⚠️  TensorRT export failed: {e}")
