from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    pkg_share = get_package_share_directory('llm_goal_bridge')
    place_db = os.path.join(pkg_share, 'place_db.yaml')

    return LaunchDescription([
        Node(
            package='llm_goal_bridge',
            executable='tcp_goal_bridge',
            name='tcp_goal_bridge',
            output='screen',
            parameters=[{
                'listen_host': '0.0.0.0',
                'listen_port': 9000,
                'default_frame': 'map',
                'place_db_path': place_db,

                # cmd_vel options
                'enable_cmd_vel': True,
                'cmd_vel_topic': '/cmd_vel',
                'default_linear_speed': 0.2,
                'default_angular_speed': 0.6,
                'cmd_publish_hz': 10.0,
            }]
        )
    ])
