#!/usr/bin/env bash
set -euo pipefail
WS="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
source /opt/ros/humble/setup.bash
cd "$WS"
colcon build --symlink-install --packages-up-to \
  tracker_interfaces_team_15 tracker_TEAM_15 \
  localization_server_TEAM_15 path_planner_server_TEAM_15
source install/setup.bash
ros2 interface show tracker_interfaces_team_15/msg/TrackerReport
ros2 pkg executables tracker_TEAM_15
