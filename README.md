# ENME703 Team 15 Tracking Project

## Team 15 packages
- localization_server_TEAM_15
- path_planner_server_TEAM_15
- tracker_interfaces_team_15
- tracker_TEAM_15

## Real TurtleBot4 startup

Source the workspace in every terminal:

cd ~/ros2_ws
source install/setup.bash

### Localisation
ros2 launch localization_server_TEAM_15 localization_namespaced_TEAM_15.launch.py namespace:=tb402

### Nav2
ros2 launch path_planner_server_TEAM_15 pathplanner_namespaced_TEAM_15.launch.py namespace:=tb402

### Tracker
ros2 launch tracker_TEAM_15 tracker_two_tb4_TEAM_15.launch.py chaser:=tb402 enemy:=tb407 global_frame:=map

## Tracker behaviour
- Opponent localisation through TF
- Continuous Nav2 pursuit
- 0.5 m nominal tracking offset
- 80 degree camera HFOV
- 30 degree safety buffer on each side
- 220 degree safe operating zone
- 5 second reporting cooldown

## TrackerReport
Topic:
/<chaser>/tracker_report

Fields:
- my_id
- opp_id
- image
- rel_dist
- rel_orient

Captured image topic:
/<chaser>/tracker_report_img/compressed

Expected TurtleBot4 camera topic:
/<chaser>/oakd/rgb/preview/image_raw/compressed

## Construct simulation

Chaser: tb3_0
Opponent: tb3_1

Tracker:
ros2 launch tracker_TEAM_15 tracker_two_tb4_TEAM_15.launch.py chaser:=tb3_0 enemy:=tb3_1 global_frame:=map

Monitor reports:
ros2 topic echo /tb3_0/tracker_report

Teleoperate opponent:
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/tb3_1/cmd_vel

Note: Construct has no TurtleBot4 OAK-D image publisher, so camera image validation must be completed on the physical TurtleBot4.

## Construct validation completed
- Two-robot localisation
- Autonomous Nav2 navigation
- TF-based opponent localisation
- Continuous opponent pursuit
- Dynamic Nav2 goal updates
- Obstacle avoidance during pursuit
- Safe operating-zone capture logic
- Relative distance/orientation calculation
- TrackerReport publishing
- Correct robot IDs
- Robust operation through repeated movements and obstacles
