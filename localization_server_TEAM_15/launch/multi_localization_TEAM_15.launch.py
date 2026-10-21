
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_dir = get_package_share_directory(
        "localization_server_TEAM_15"
    )

    map_file = LaunchConfiguration('map')

    nodes = [
        DeclareLaunchArgument(
            'map',
            description='Absolute path to the external Construct map YAML',
        ),
        Node(
            package="nav2_map_server",
            executable="map_server",
            name="map_server",
            output="screen",
            parameters=[{
                "use_sim_time": True,
                "topic_name": "map",
                "frame_id": "map",
                "yaml_filename": map_file,
            }],
        )
    ]

    # Give each robot its own AMCL node.
    for robot in ["tb3_0", "tb3_1"]:
        config = os.path.join(
            package_dir, "config", f"{robot}_amcl_config.yaml"
        )

        nodes.append(
            Node(
                namespace=robot,
                package="nav2_amcl",
                executable="amcl",
                name="amcl",
                output="screen",
                parameters=[config],
            )
        )

    # Activate the map server and both AMCL nodes.
    nodes.append(
        Node(
            package="nav2_lifecycle_manager",
            executable="lifecycle_manager",
            name="lifecycle_manager_localization",
            output="screen",
            parameters=[{
                "use_sim_time": True,
                "autostart": True,
                "bond_timeout": 0.0,
                "node_names": [
                    "map_server",
                    "tb3_0/amcl",
                    "tb3_1/amcl",
                ],
            }],
        )
    )

    return LaunchDescription(nodes)
