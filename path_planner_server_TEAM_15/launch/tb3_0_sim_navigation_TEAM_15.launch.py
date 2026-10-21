"""Run chaser navigation only; retain the existing map and AMCL nodes."""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    params = os.path.join(get_package_share_directory('path_planner_server_TEAM_15'), 'config', 'tb3_0_sim_nav2.yaml')
    servers = [('nav2_controller', 'controller_server'), ('nav2_planner', 'planner_server'), ('nav2_behaviors', 'behavior_server'), ('nav2_bt_navigator', 'bt_navigator')]
    nodes = [Node(package=package, executable=name, name=name, namespace='tb3_0', output='screen', parameters=[params]) for package, name in servers]
    nodes.append(Node(package='nav2_lifecycle_manager', executable='lifecycle_manager', name='lifecycle_manager_navigation', namespace='tb3_0', output='screen', parameters=[{'use_sim_time': True, 'autostart': True, 'bond_timeout': 4.0, 'node_names': [name for _, name in servers]}]))
    return LaunchDescription(nodes)
