"""Retained physical pursuit executable, optional nonblocking capture timer."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    args = {
        'chaser': 'tb402', 'enemy': 'tb407', 'global_frame': 'map',
        'enable_reporting': 'false', 'allow_latest_tf': 'false',
        'max_tf_image_skew_sec': '0.25', 'my_id': '-1', 'opp_id': '-1',
    }
    params = {k: ParameterValue(LaunchConfiguration(k), value_type=str)
              for k in ('chaser', 'enemy', 'global_frame', 'camera_topic')}
    params.update({k: ParameterValue(LaunchConfiguration(k), value_type=bool)
                   for k in ('enable_reporting', 'allow_latest_tf')})
    params.update({k: ParameterValue(LaunchConfiguration(k), value_type=int)
                   for k in ('my_id', 'opp_id')})
    params['max_tf_image_skew_sec'] = ParameterValue(
        LaunchConfiguration('max_tf_image_skew_sec'), value_type=float)
    params['use_sim_time'] = False
    return LaunchDescription([
        *(DeclareLaunchArgument(k, default_value=v) for k, v in args.items()),
        DeclareLaunchArgument('camera_topic', default_value=[
            '/', LaunchConfiguration('chaser'), '/oakd/rgb/preview/image_raw/compressed']),
        Node(package='tracker_TEAM_15', executable='tracker_two_tb4_TEAM_15',
             name='tracker_two_tb4_TEAM_15', output='screen', parameters=[params]),
    ])
