#!/usr/bin/env bash
# READ-ONLY. Run before enabling autonomous physical motion.
set -uo pipefail
CHASER="${CHASER:-tb402}"
OPPONENT="${OPPONENT:-tb407}"
echo "ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-unset}"
echo "RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION:-unset}"
echo "ROS_DISCOVERY_SERVER=${ROS_DISCOVERY_SERVER:-unset}"
echo '--- Robot topics ---'
ros2 topic list -t | grep -E "^/(${CHASER}|${OPPONENT})/" | head -80 || true
echo '--- Camera candidates (must verify actual type/header) ---'
ros2 topic list -t | grep -Ei '(oakd|rgb|color|preview|compressed)' || true
echo '--- Chaser scan ---'
ros2 topic info "/${CHASER}/scan" -v || true
echo '--- Chaser Nav2 action ---'
ros2 action list | grep "/${CHASER}/navigate_to_pose" || true
echo '--- TF map -> chaser ---'
timeout 5s ros2 run tf2_ros tf2_echo map "${CHASER}/base_link" || true
echo '--- TF map -> opponent ---'
timeout 5s ros2 run tf2_ros tf2_echo map "${OPPONENT}/base_link" || true
