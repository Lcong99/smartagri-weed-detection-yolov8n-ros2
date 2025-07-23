from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # RViz2
        Node(
            package='rviz2', executable='rviz2', name='rviz2',
            arguments=['-d', 
              '/mnt/data/rviz/field_view.rviz'],  # you can save a .rviz config
        ),
        # our pubs
        Node(package='field_visualizer', executable='odom_pub'),
        Node(package='field_visualizer', executable='detect_pub'),
        Node(package='field_visualizer', executable='heatmap_pub'),
    ])

