from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
import launch.conditions
import launch.substitutions
import os

def generate_launch_description():
    # Find package shares
    yolo_detect_share = FindPackageShare('yolo_detect')
    peripherals_share = FindPackageShare('peripherals')
    
    # Declare launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    
    camera_type = LaunchConfiguration('camera_type', default='depth')  # Changed default to depth
    
    model_path = LaunchConfiguration('model_path', 
        default=PathJoinSubstitution([yolo_detect_share, 'models', 'best.pt']))
    
    # Updated default camera topic for depth camera RGB stream
    camera_topic = LaunchConfiguration('camera_topic', 
        default='/depth_cam/depth_cam/color/image_raw')
    
    use_compressed = LaunchConfiguration('use_compressed', default='false')
    
    confidence_threshold = LaunchConfiguration('confidence_threshold', default='0.5')
    
    device = LaunchConfiguration('device', default='cuda')
    
    save_detections = LaunchConfiguration('save_detections', default='true')
    
    output_dir = LaunchConfiguration('output_dir', 
        default='/home/ubuntu/weed_detections')
    
    debug_mode = LaunchConfiguration('debug_mode', default='true')
    
    # Launch arguments
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation time'
    )
    
    camera_type_arg = DeclareLaunchArgument(
        'camera_type',
        default_value='depth',  # Changed default
        description='Camera type: usb or depth'
    )
    
    model_path_arg = DeclareLaunchArgument(
        'model_path',
        default_value=PathJoinSubstitution([yolo_detect_share, 'models', 'best.pt']),
        description='Path to YOLO model file'
    )
    
    camera_topic_arg = DeclareLaunchArgument(
        'camera_topic',
        default_value='/depth_cam/depth_cam/color/image_raw',  # Updated for depth camera
        description='Camera topic to subscribe to'
    )
    
    use_compressed_arg = DeclareLaunchArgument(
        'use_compressed',
        default_value='false',
        description='Use compressed image topic'
    )
    
    confidence_threshold_arg = DeclareLaunchArgument(
        'confidence_threshold',
        default_value='0.5',
        description='YOLO confidence threshold'
    )
    
    device_arg = DeclareLaunchArgument(
        'device',
        default_value='cuda',
        description='Device to run inference on: cuda or cpu'
    )
    
    save_detections_arg = DeclareLaunchArgument(
        'save_detections',
        default_value='true',
        description='Save detection images and data'
    )
    
    output_dir_arg = DeclareLaunchArgument(
        'output_dir',
        default_value='/home/ubuntu/weed_detections',
        description='Directory to save detections'
    )
    
    debug_mode_arg = DeclareLaunchArgument(
        'debug_mode',
        default_value='true',
        description='Enable debug logging'
    )
    
    # USB Camera launch (conditional)
    usb_cam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([peripherals_share, 'launch', 'usb_cam.launch.py'])
        ]),
        condition=launch.conditions.IfCondition(
            launch.substitutions.PythonExpression(["'", camera_type, "' == 'usb'"])
        )
    )
    
    # Depth Camera launch (conditional) - NEW
    depth_cam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([peripherals_share, 'launch', 'depth_camera.launch.py'])
        ]),
        condition=launch.conditions.IfCondition(
            launch.substitutions.PythonExpression(["'", camera_type, "' == 'depth'"])
        )
    )
    
    # Weed detector node
    weed_detector_node = Node(
        package='yolo_detect',
        executable='yolo_node',
        name='yolo_weed_detector',
        parameters=[{
            'use_sim_time': use_sim_time,
            'model_path': model_path,
            'camera_topic': camera_topic,
            'use_compressed': use_compressed,
            'confidence_threshold': confidence_threshold,
            'device': device,
            'save_detections': save_detections,
            'output_dir': output_dir,
            'debug_mode': debug_mode
        }],
        output='screen',
        respawn=True,
        respawn_delay=2
    )
    
    # Optional visualization node (for viewing in RViz)
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', PathJoinSubstitution([yolo_detect_share, 'config', 'weed_detection.rviz'])],
        condition=launch.conditions.IfCondition(
            launch.substitutions.EnvironmentVariable('DISPLAY', default_value='false')
        )
    )
    
    return LaunchDescription([
        # Arguments
        use_sim_time_arg,
        camera_type_arg,
        model_path_arg,
        camera_topic_arg,
        use_compressed_arg,
        confidence_threshold_arg,
        device_arg,
        save_detections_arg,
        output_dir_arg,
        debug_mode_arg,
        
        # Nodes
        usb_cam_launch,      # Only launches if camera_type=usb
        depth_cam_launch,    # Only launches if camera_type=depth
        weed_detector_node,
        # rviz_node  # Uncomment if you want to auto-launch RViz
    ])
