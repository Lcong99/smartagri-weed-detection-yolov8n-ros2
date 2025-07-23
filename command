# === STOP ROS NODES ===
~/.stop_ros.sh


# === BUILD WORKSPACE ===
cd ~/ros2_ws && ~/.build.sh

# OR manual colcon build:
# colcon build --event-handlers console_direct+ --cmake-args -DCMAKE_BUILD_TYPE=Release --symlink-install

# Build specific package:
# colcon build --event-handlers console_direct+ --cmake-args -DCMAKE_BUILD_TYPE=Release --symlink-install --packages-select <package_name>


# === CALIBRATION ===
# Angular velocity calibration (Mecanum/Tank)
ros2 launch calibration angular_calib.launch.py

# Linear velocity calibration (Mecanum/Tank)
ros2 launch calibration linear_calib.launch.py

# IMU calibration
ros2 launch ros_robot_controller ros_robot_controller.launch.py
ros2 run imu_calib do_calib --ros-args -r imu:=/ros_robot_controller/imu_raw --param output_file:=/home/ubuntu/ros2_ws/src/calibration/config/imu_calib.yaml

# View IMU calibration result
ros2 launch peripherals imu_view.launch.py


# === CAMERA & SENSOR VISUALIZATION ===
# Depth camera (RGB + point cloud)
ros2 launch peripherals depth_camera.launch.py
rviz2

# USB monocular camera
ros2 launch peripherals usb_cam.launch.py
rviz2

# Lidar view
ros2 launch peripherals lidar_view.launch.py


# === APPLICATION NODES ===
# Lidar functionality
ros2 launch app lidar_node.launch.py debug:=true
ros2 service call /lidar_app/enter std_srvs/srv/Trigger {}
ros2 service call /lidar_app/set_running interfaces/srv/SetInt64 "{data: 1}"  # Obstacle avoidance
ros2 service call /lidar_app/set_running interfaces/srv/SetInt64 "{data: 2}"  # Following
ros2 service call /lidar_app/set_running interfaces/srv/SetInt64 "{data: 3}"  # Guard mode

# Line following
ros2 launch app line_following_node.launch.py debug:=true
ros2 service call /line_following/enter std_srvs/srv/Trigger {}
ros2 service call /line_following/set_running std_srvs/srv/SetBool "{data: True}"

# Object tracking
ros2 launch app object_tracking_node.launch.py debug:=true
ros2 service call /object_tracking/enter std_srvs/srv/Trigger {}
ros2 service call /object_tracking/set_running std_srvs/srv/SetBool "{data: True}"

# AR app
ros2 launch app ar_app_node.launch.py debug:=true
ros2 service call /ar_app/enter std_srvs/srv/Trigger {}
ros2 service call /ar_app/set_model interfaces/srv/SetString "{data: \"bicycle\"}"

# Hand gesture control
ros2 launch app hand_gesture_node.launch.py debug:=true
ros2 service call /hand_gesture/enter std_srvs/srv/Trigger {}
ros2 service call /hand_gesture/set_running std_srvs/srv/SetBool "{data: True}"


# === EXAMPLES ===
# QR code generation and detection
cd ~/ros2_ws/src/example/example/qrcode && python3 qrcode_creater.py
cd ~/ros2_ws/src/example/example/qrcode && python3 qrcode_detecter.py

# Mediapipe examples
cd ~/ros2_ws/src/example/example/mediapipe_example && python3 face_detect.py
cd ~/ros2_ws/src/example/example/mediapipe_example && python3 face_mesh.py
cd ~/ros2_ws/src/example/example/mediapipe_example && python3 hand.py
cd ~/ros2_ws/src/example/example/mediapipe_example && python3 pose.py
cd ~/ros2_ws/src/example/example/mediapipe_example && python3 self_segmentation.py
cd ~/ros2_ws/src/example/example/mediapipe_example && python3 holistic.py
cd ~/ros2_ws/src/example/example/mediapipe_example && python3 objectron.py
cd ~/ros2_ws/src/example/example/mediapipe_example && python3 hand_gesture.py

# Color detection
cd ~/ros2_ws/src/example/example/color_detect && python3 color_detect_demo.py

# Color sorting & tracking
ros2 launch example color_sorting_node.launch.py debug:=true
ros2 launch example color_track_node.launch.py

# Hand tracking & gesture control
ros2 launch example hand_gesture_control_node.launch.py
ros2 launch example hand_track_node.launch.py
ros2 launch example finger_control.launch.py
ros2 launch example hand_trajectory_node.launch.py

# Line follow and obstacle clearing
ros2 launch example line_follow_clean_node.launch.py debug:=true

# Automatic pick & place
ros2 launch example automatic_pick.launch.py debug:=true
ros2 service call /automatic_pick/pick std_srvs/srv/Trigger {}
ros2 service call /automatic_pick/place std_srvs/srv/Trigger {}

# Navigation & mapping
ros2 launch example navigation_transport.launch.py map:=map_01
ros2 launch slam slam.launch.py
ros2 launch slam rviz_slam.launch.py
ros2 launch peripherals teleop_key_control.launch.py
cd ~/ros2_ws/src/slam/maps && ros2 run nav2_map_server map_saver_cli -f "map_01" --ros-args -p map_subscribe_transient_local:=true

# 3D mapping
ros2 launch slam rtabmap_slam.launch.py
ros2 launch slam rviz_rtabmap.launch.py

# Navigation
ros2 launch navigation navigation.launch.py map:=map_01
ros2 launch navigation rviz_navigation.launch.py
ros2 launch navigation rtabmap_navigation.launch.py
ros2 launch navigation rviz_rtabmap_navigation.launch.py

# URDF visualization
ros2 launch jetrover_description display.launch.py


# === VOICE CONTROL (Offline ASR) ===
ros2 launch xf_mic_asr_offline voice_control_arm.launch.py
ros2 launch xf_mic_asr_offline voice_control_color_detect.launch.py
ros2 launch xf_mic_asr_offline voice_control_color_sorting.launch.py
ros2 launch xf_mic_asr_offline voice_control_color_track.launch.py
ros2 launch xf_mic_asr_offline voice_control_move.launch.py
ros2 launch xf_mic_asr_offline voice_control_garbage_classification.launch.py
ros2 launch xf_mic_asr_offline voice_control_navigation.launch.py map:='map_01'
ros2 launch xf_mic_asr_offline voice_control_navigation_transport.launch.py map:='map_01'


# === SOFTWARE TOOLS ===
python3 ~/software/lab_tool/main.py
python3 ~/software/collect_picture/main.py
python3 ~/software/servo_tool/main.py


# === LLM/Visual Examples ===
ros2 launch large_models_examples llm_control_move.launch.py
ros2 launch large_models_examples llm_color_track.launch.py
ros2 launch large_models_examples llm_visual_patrol.launch.py
ros2 launch large_models_examples vllm_with_camera.launch.py
ros2 launch large_models_examples vllm_track.launch.py
ros2 launch large_models_examples vllm_navigation.launch.py map:=map_01
ros2 launch large_models_examples automatic_transport.launch.py debug:=pick/debug:=place
ros2 launch large_models_examples vllm_transport_dietitianl.launch.py map:=map_01
