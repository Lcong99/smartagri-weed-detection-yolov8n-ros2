cmake_minimum_required(VERSION 3.5)
project(yolo_detect)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclpy REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(image_transport REQUIRED)

# installs your Python modules under lib/yolo_detect
ament_python_install_package(${PROJECT_NAME})

# installs any launch/ config files
install(DIRECTORY launch
  DESTINATION share/${PROJECT_NAME})

install(PROGRAMS 
  yolo_detect/yolo_node.py
  DESTINATION lib/${PROJECT_NAME})

ament_package()

