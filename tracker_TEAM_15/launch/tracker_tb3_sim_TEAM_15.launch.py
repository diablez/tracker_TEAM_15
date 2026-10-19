"""Start Team 15 pursuit client only; do not start Gazebo, AMCL, or Nav2."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    args = {
        'chaser': 'tb3_0',
        'enemy': 'tb3_1',
        'global_frame': 'map',
        'chaser_frame': '',
        'enemy_frame': '',
        'goal_offset': '0.5',
        'dry_run': 'true',
        'use_sim_time': 'true',
        'min_goal_interval': '1.5',
        'max_tf_age': '2.5',
    }
    str_params = ('chaser', 'enemy', 'global_frame', 'chaser_frame', 'enemy_frame')
    float_params = ('goal_offset', 'min_goal_interval', 'max_tf_age')
    bool_params = ('dry_run', 'use_sim_time')

    return LaunchDescription([
        *(DeclareLaunchArgument(name, default_value=value)
          for name, value in args.items()),
        Node(
            package='tracker_TEAM_15',
            executable='tracker_tb3_sim_TEAM_15',
            name='tracker_tb3_sim_TEAM_15',
            output='screen',
            parameters=[{
                **{name: ParameterValue(LaunchConfiguration(name), value_type=str)
                   for name in str_params},
                **{name: ParameterValue(LaunchConfiguration(name), value_type=float)
                   for name in float_params},
                **{name: ParameterValue(LaunchConfiguration(name), value_type=bool)
                   for name in bool_params},
            }],
        ),
    ])
