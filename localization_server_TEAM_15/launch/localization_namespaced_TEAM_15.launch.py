"""
Physical TB4: use the installed TurtleBot4 localisation launch, not a template.

Requires the actual physical arena map path; this is intentionally not the
Construct simulation map. The physical system must still be field-tested.
"""
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    launch_file = os.path.join(get_package_share_directory('turtlebot4_navigation'),
                               'launch', 'localization.launch.py')
    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value='tb402'),
        DeclareLaunchArgument('map', description='Absolute path to mapped physical arena YAML'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(launch_file),
            launch_arguments={
                'namespace': LaunchConfiguration('namespace'),
                'map': LaunchConfiguration('map'),
                'use_sim_time': 'false',
            }.items(),
        ),
    ])
