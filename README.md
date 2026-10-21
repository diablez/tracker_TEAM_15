# Team 15 ROS 2 tracker

TF/Nav2 pursuit and compressed-camera reporting for physical TurtleBot4 robots and The Construct's dual-TurtleBot3 Humble simulation. Canonical repository: [diablez/tracker_TEAM_15](https://github.com/diablez/tracker_TEAM_15).

**Integration review candidate:** this revision has not been built with ROS, launched in Gazebo, or tested on physical robots. Keep the October 14 lab workspace unchanged until deployment checks pass. Missing camera frames never gate pursuit. Empty or fabricated captures are not published.

## Architecture

Both robots must be localized in one shared `map`, with separate namespaced `odom` and base frames. Pursuit reads their TF poses, calculates a goal 0.5 m behind the opponent and submits it to `/<chaser>/navigate_to_pose`. Nav2 handles planning and obstacle avoidance. Camera reporting separately checks received images, geometry, timestamps and TF.

| Package | Responsibility |
| --- | --- |
| `localization_server_TEAM_15` | Physical localization wrapper; shared map and dual TB3 AMCL |
| `path_planner_server_TEAM_15` | Physical Nav2 wrapper; TB3 chaser navigation |
| `tracker_TEAM_15` | Pursuit, pose preview, camera reporting |
| `tracker_interfaces_team_15` | Five-field report interface |

| Executable | Behaviour |
| --- | --- |
| `tracker_two_tb4_TEAM_15` | Retained physical pursuit implementation; independent capture timer, reporting off by default |
| `tracker_tb3_sim_TEAM_15` | Retained simulation Nav2 action client; dry-run by default |
| `tracker_node` | Publishes `/tracker/desired_pose` for inspection; sends no navigation goals |
| `capture_report` | Separate configurable reporter; off by default |

Run one pursuit client and one reporter per chaser. The physical executable's internal reporter and the separate reporter are alternatives.

## Installation and VS Code

Use Ubuntu 22.04 and ROS 2 Humble. Windows users should run ROS through VS Code Remote WSL/SSH; native Windows editing does not supply ROS. Install platform drivers and ROS/Nav2 through their official distributions.

```bash
git clone https://github.com/diablez/tracker_TEAM_15.git
cd tracker_TEAM_15
# Available remotely only after the reviewed commits have been pushed.
git switch team15/demo-integration-20261021
source /opt/ros/humble/setup.bash
rosdep install --from-paths . --ignore-src -r -y --rosdistro humble
bash scripts/build_team15.sh
source install/setup.bash
ros2 pkg executables tracker_TEAM_15
```

Four ROS packages live at repository root. Alternatively clone once beneath an outer colcon workspace's `src` directory and pass that workspace to the build script. Do not build duplicate copies of the same packages.

Open `team15.code-workspace`. Recommended extensions cover Python, YAML, Markdown and Remote WSL. In Linux, select the ROS interpreter and open VS Code from a terminal with ROS and the built workspace sourced. Settings contain no machine-specific interpreter, and exclude build/install/log/cache folders. No relevant notebooks were found or added. See [safe synchronization](docs/RELEASE_REVIEW.md#synchronizing-an-existing-vs-code-copy) before updating an existing editor checkout.

## Physical TurtleBot4

Preserve the working lab bringup. Verify actual robot namespaces, the physical arena map, discovery configuration, shared-map TF and OAK-D stream. `tb402`/`tb407` and IDs 2/7 below are examples to confirm with the team/referee.

If localization/Nav2 are not already active, optional wrappers delegate to the installed `turtlebot4_navigation` Humble launches:

```bash
# Separate terminals; use the actual physical map.
ros2 launch localization_server_TEAM_15 localization_namespaced_TEAM_15.launch.py namespace:=tb402 map:=/absolute/path/to/arena.yaml
ros2 launch localization_server_TEAM_15 localization_namespaced_TEAM_15.launch.py namespace:=tb407 map:=/absolute/path/to/arena.yaml
ros2 launch path_planner_server_TEAM_15 pathplanner_namespaced_TEAM_15.launch.py namespace:=tb402
CHASER=tb402 OPPONENT=tb407 bash scripts/physical_preflight.sh
```

These wrappers explicitly use wall time. Their arguments were checked against upstream Humble source; fleet behaviour is untested. Do not duplicate existing map, AMCL or Nav2 stacks. The lecturer's working bringup takes precedence where its TF conventions differ.

The template camera topic is `/<chaser>/oakd/rgb/preview/image_raw/compressed`. Confirm the real topic with `ros2 topic list -t`, then inspect its type, frame, advancing timestamp and visible image. Configure `camera_topic` rather than assuming the default is correct.

Only launch motion with a human supervising and a stop method available. The retained physical executable sends goals immediately and has no dry-run mode:

```bash
# Camera-independent pursuit; captures disabled.
ros2 launch tracker_TEAM_15 tracker_two_tb4_TEAM_15.launch.py chaser:=tb402 enemy:=tb407 enable_reporting:=false
```

After interface/image checks, add `enable_reporting:=true my_id:=2 opp_id:=7 camera_topic:=/tb402/oakd/rgb/preview/image_raw/compressed` to use its internal reporter. Or leave internal reporting disabled and run the separate reporter. New capture checks are not hardware validation and do not replace the lab fallback.

## Construct / TB3 simulation

Use the existing two-robot Humble simulator and its supplied map. Worlds, robot meshes and course maps are external because their redistribution provenance was not established. Do not reset an active simulation to install this source.

If localization/Nav2 are not already running:

```bash
ros2 launch localization_server_TEAM_15 multi_localization_TEAM_15.launch.py map:=/absolute/path/to/two_robot_map.yaml
# Initialize both AMCL poses against actual robot locations in RViz.
ros2 launch path_planner_server_TEAM_15 tb3_0_sim_navigation_TEAM_15.launch.py
```

Verify `/clock`, both scan/AMCL streams, fresh shared-map TF and `/tb3_0/navigate_to_pose`. The Nav2 configuration is for the `tb3_0` chaser, not a second opponent navigation stack.

```bash
ros2 launch tracker_TEAM_15 tracker_tb3_sim_TEAM_15.launch.py dry_run:=true
# Stop dry-run first; supervise before enabling motion.
ros2 launch tracker_TEAM_15 tracker_tb3_sim_TEAM_15.launch.py dry_run:=false
```

The simulation client retains target-change thresholds, 1.5-second minimum goal spacing and action-result retry handling. Stale/future TF skips updates; it does not cancel an already active goal. Explicitly cancel/stop if tracking is lost. Both preserved pursuit implementations still need supervised stop handling.

Base Construct models may lack RGB cameras. Pursuit continues while reporting waits. For raw `sensor_msgs/Image`, install/configure `image_transport` externally and verify its compressed output; this project consumes `sensor_msgs/CompressedImage` only.

## Camera and TrackerReport

The lecturer's September 16 reporting slide specifies these five fields in order:

```text
uint8 my_id
uint8 opp_id
sensor_msgs/CompressedImage image
float32 rel_dist
float32 rel_orient
```

No sixth field is added. Acquisition time/frame stay in `image.header`. The lecturer template also asks for a separate `/<chaser>/tracker_report_img/compressed` publisher: display that image topic in RViz rather than the custom report.

Ciaron describes a header-bearing October 14 lab version; its actual installed/source definition is not available here. All peers must agree on field count, order and types. Verify the authoritative interface before deployment:

```bash
ros2 interface show tracker_interfaces_team_15/msg/TrackerReport
python3 scripts/verify_interface.py --expected /path/to/authoritative/TrackerReport.msg --installed
```

If different, stop and reconcile with the lecturer/team; rebuild every peer using the agreed schema. Assigning an optional top-level header in Python does not make mismatched DDS interfaces compatible. Reporting code preserves an installed header when present, but this is not an interface migration.

Separate simulation reporter example:

```bash
ros2 launch tracker_TEAM_15 capture_report.launch.py enable_reporting:=true my_id:=0 opp_id:=1 image_topic:=/tb3_0/camera/image_raw/compressed
```

For physical use, also pass `use_sim_time:=false`, actual image/report/image-report topics, physical chaser/opponent frames and agreed IDs. `camera_frame` optionally enforces an expected image frame. Do not run two reporters on the same topic.

Both reporters reject empty/corrupt/unstamped images, missing image frame IDs, stale/future images and reused/older stamps. Cooldown is at least five monotonic seconds. Geometry requires 0.40–0.60 m separation, opponent centre within the chaser's +/-40-degree view and a chaser position outside the opponent's forward +/-70 degrees (220-degree allowed arc). The distance window is an implementation tolerance. Physical camera/body alignment, FOV and full-robot visibility require measurement. Orientation is wrapped opponent yaw minus chaser yaw, in degrees.

TF lookup never waits in capture callbacks. Exact image-time transforms are preferred and retried on later ticks. Optional `allow_latest_tf:=true` uses both poses at a common TF time, within `max_tf_image_skew_sec` (default 0.25 seconds) of the image, with fresh stamped transforms. It never combines unrelated latest poses. Enable approximation only after measuring acceptable skew.

The separate reporter can save real compressed frames under `~/.ros/team15_captures`; save failures do not affect pursuit. Optional recent target-visible Bool gating is not an image-linked detector. Neither reporter proves visual identification or lack of occlusion. Inspect saved images before claiming a valid capture.

## Verification, troubleshooting and limitations

```bash
python3 -m unittest discover -s tests -v
# In a real Humble environment, after building:
colcon test --packages-select tracker_interfaces_team_15 tracker_TEAM_15 localization_server_TEAM_15 path_planner_server_TEAM_15
colcon test-result --verbose
```

Unit tests substitute clocks, TF and publishers while exercising production policies/timer methods. The decoder test uses OpenCV/numpy; install the declared dependencies or it reports a skip. Tests do not prove DDS, message generation, Gazebo or hardware behaviour. [Review evidence and merge procedure](docs/RELEASE_REVIEW.md) records tests actually run.

Before a demonstration pass: build four packages; compare report schemas; verify both AMCL/TF chains, the camera and clocks; inspect a dry-run goal; supervise moving-opponent pursuit; inspect action results and post-goal poses; verify report delivery and an image visibly showing the opponent; repeat after five seconds.

- No camera: pursuit continues. Check topic type, QoS and compressed transport; never supply blank images.
- No capture: check reporting enablement/IDs, timestamps, TF, geometry and cooldown. A bounded fallback is optional, not exact-time evidence.
- RViz “No Image”: select the separate compressed stream and inspect bytes/header/frame/QoS before editing the interface.
- No goals: check clock source, base frames, fresh TF, dry-run, Nav2 lifecycle and namespaced action.
- Duplicate packages: exclude the extra checkout from the colcon search path without deleting working source.
- Lost target/shutdown: explicitly cancel active Nav2 goals; no new safety controller is claimed.

## Redistribution

No course PDFs, private email, lab photos, downloaded archives, robot meshes or maps are included. External ROS packages stay upstream. Repository-level licensing and inherited course-code rights remain for the team to confirm before advertising an open-source release; package metadata is not a complete license grant. See [public release review](docs/RELEASE_REVIEW.md#public-release).
