"""Physical TB4: delegate to the installed namespaced TurtleBot4 Nav2 stack.

The original TEAM15 handwritten Nav2 templates contained placeholders and the
old custom YAMLs are not tested on assessed hardware. Do not launch both stacks.
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    launch_file = os.path.join(get_package_share_directory('turtlebot4_navigation'),
                               'launch', 'nav2.launch.py')
    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value='tb402'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(launch_file),
            launch_arguments={'namespace': LaunchConfiguration('namespace'),
                              'use_sim_time': 'false'}.items(),
        ),
    ])
