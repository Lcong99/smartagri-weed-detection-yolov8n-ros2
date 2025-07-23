from ultralytics import YOLO

try:
    model = YOLO('best.pt')
    print("Model loaded successfully!")
    print(f"Model type: {type(model)}")
except Exception as e:
    print(f"Error loading model: {e}")
