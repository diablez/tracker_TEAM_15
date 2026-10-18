from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    return LaunchDescription([

        DeclareLaunchArgument(
            'chaser',
            default_value='tb402'
        ),

        DeclareLaunchArgument(
            'enemy',
            default_value='tb407'
        ),

        DeclareLaunchArgument(
            'global_frame',
            default_value='map'
        ),

        Node(
            package='tracker_TEAM_15',
            executable='tracker_two_tb4_TEAM_15',
            name='tracker_two_tb4_TEAM_15',
            output='screen',
            parameters=[{
                'chaser': LaunchConfiguration('chaser'),
                'enemy': LaunchConfiguration('enemy'),
                'global_frame': LaunchConfiguration('global_frame')
            }]
        )
    ])
