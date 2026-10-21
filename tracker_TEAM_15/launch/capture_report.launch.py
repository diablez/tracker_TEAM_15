"""Parametrised capture pipeline for both Gazebo TB3 and physical TB4."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    strings = {
        'image_topic': '/tb3_0/camera/image_raw/compressed',
        'report_topic': '/tb3_0/tracker_report',
        'report_image_topic': '/tb3_0/tracker_report_img/compressed',
        'global_frame': 'map',
        'chaser_frame': 'tb3_0/base_link',
        'opponent_frame': 'tb3_1/base_link',
        'camera_frame': '',
        'target_visible_topic': '',
        'capture_dir': '~/.ros/team15_captures',
    }
    ints = {'my_id': '-1', 'opp_id': '-1'}
    bools = {
        'use_sim_time': 'true',
        'require_target_visible': 'false',
        'save_images': 'true',
        'enable_reporting': 'false',
        'allow_latest_tf': 'false',
    }
    floats = {'max_tf_image_skew_sec': '0.25', 'max_image_age_sec': '1.0',
              'max_receive_age_sec': '0.9', 'capture_cooldown_sec': '5.0',
              'min_distance_m': '0.4', 'max_distance_m': '0.6',
              'camera_half_fov_deg': '40.0', 'opponent_front_exclusion_deg': '70.0'}
    args = {**strings, **ints, **bools, **floats}
    params = {k: ParameterValue(LaunchConfiguration(k), value_type=str)
              for k in strings}
    params.update({k: ParameterValue(LaunchConfiguration(k), value_type=int)
                   for k in ints})
    params.update({k: ParameterValue(LaunchConfiguration(k), value_type=bool)
                   for k in bools})
    params.update({k: ParameterValue(LaunchConfiguration(k), value_type=float)
                   for k in floats})
    return LaunchDescription([
        *(DeclareLaunchArgument(k, default_value=v) for k, v in args.items()),
        Node(package='tracker_TEAM_15', executable='capture_report',
             name='team15_capture_report', output='screen', parameters=[params]),
    ])
