# Team 15 ROS 2 tracker

TF/Nav2 pursuit and compressed-camera reporting for physical TurtleBot4 robots and The Construct's dual-TurtleBot3 Humble simulation. Canonical repository: [diablez/tracker_TEAM_15](https://github.com/diablez/tracker_TEAM_15).

**Verified scope:** the four packages build from a clean checkout under the local ROS 2 Humble environment. Earlier Construct evidence records report publication, receipt of one non-empty opponent-visible image and one successful 13.3 cm forward Nav2 manoeuvre. It does not establish sustained pursuit, a reproducible fresh simulator start, calibrated camera geometry, referee compatibility or physical-hardware compatibility. Missing camera frames never gate pursuit; empty or fabricated captures are not published.

**Latest live validation (21 October):** laser/map misalignment was corrected by initializing AMCL in the measured map coordinate system; the course map and simulator models were preserved. Median latest-scan error fell to about 2.2 cm for both robots. One forward Nav2 goal produced 13.3 cm of commanded motion and succeeded. Rearward manoeuvring timed out and was explicitly cancelled; sustained moving-target pursuit remains unverified. See [measured evidence and corrected initialization procedure](docs/CONSTRUCT_VALIDATION_20261021.md).

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
source /opt/ros/humble/setup.bash
rosdep install --from-paths . --ignore-src -r -y --rosdistro humble
bash scripts/build_team15.sh
source install/setup.bash
ros2 pkg executables tracker_TEAM_15
```

These commands use the default `main` branch. The project is not a complete simulator distribution: its course map, world, meshes, camera-equipped model and RViz preset are external. Package names containing uppercase `TEAM_15` are retained identities and cause non-fatal ROS naming warnings.

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

### Current Construct session: quick run

Preserve `/home/user/ros2_ws` and its running simulator. The integration overlay is `/home/user/team15_candidate_ws`; do not build another package copy into the original workspace. This is an existing-simulator procedure, not a self-contained world/camera installer.

For a **new, empty candidate workspace only**:

```bash
mkdir -p ~/team15_candidate_ws/src
git clone https://github.com/diablez/tracker_TEAM_15.git ~/team15_candidate_ws/src/tracker_TEAM_15
source /opt/ros/humble/setup.bash
cd ~/team15_candidate_ws
rosdep install --from-paths src --ignore-src -r -y --rosdistro humble
bash src/tracker_TEAM_15/scripts/build_team15.sh "$HOME/team15_candidate_ws"
```

In **every launch/check terminal**, source the same overlay:

```bash
source /opt/ros/humble/setup.bash
source ~/team15_candidate_ws/install/setup.bash
# This hostname belongs to the current Construct environment; confirm it elsewhere.
export GAZEBO_MASTER_URI=http://4_simulation:11345
ros2 pkg prefix tracker_TEAM_15
```

Expected package prefix: `/home/user/team15_candidate_ws/install/tracker_TEAM_15`. Preserve the session's ROS discovery settings. Use simulation time throughout. Check existing processes/nodes first and skip any launch already running; do not start duplicate map, AMCL, Nav2, tracker or reporter instances.

1. Keep the existing two-robot Gazebo simulator and camera-equipped Red model running. The map is an **external original-workspace asset**; verify both the YAML and its referenced image exist:

   ```bash
   test -r /home/user/ros2_ws/install/localization_server_TEAM_15/share/localization_server_TEAM_15/maps/turtlebot_area_two_robots_clean.yaml
   ros2 launch localization_server_TEAM_15 multi_localization_TEAM_15.launch.py map:=/home/user/ros2_ws/install/localization_server_TEAM_15/share/localization_server_TEAM_15/maps/turtlebot_area_two_robots_clean.yaml
   ```

2. In another terminal, open the existing RViz configuration:

   ```bash
   rviz2 -d ~/ros2_ws/tb3_team15_success.rviz --ros-args -p use_sim_time:=true
   ```

   Initialize both AMCL poses on `/tb3_0/initialpose` and `/tb3_1/initialpose` using their actual poses in the shared `map`. Check laser/wall alignment and both `map -> tb3_N/odom -> tb3_N/base_link` chains. Gazebo coordinates are not automatically map coordinates. Do not replay the previous teleport coordinates or reset/reposition models to make a check pass.

3. Launch Red navigation once, then check it from another sourced terminal:

   ```bash
   ros2 launch path_planner_server_TEAM_15 tb3_0_sim_navigation_TEAM_15.launch.py
   ```

   ```bash
   for n in bt_navigator planner_server controller_server; do
     echo "$n"
     timeout 5s ros2 lifecycle get /tb3_0/$n
   done
   ros2 action info /tb3_0/navigate_to_pose
   timeout 8s ros2 run tf2_ros tf2_echo map tb3_0/base_link
   timeout 8s ros2 run tf2_ros tf2_echo map tb3_1/base_link
   ```

   All three lifecycle checks must return `active [3]`. If a server crashes, stop its owning failed Nav2 launch, verify its navigation processes have exited, then relaunch once. Preserve localization, map server and camera. Do not use broad process-kill commands. Recheck lifecycle and map alignment before motion.

4. Preview a goal with `dry_run:=true`, then stop that launch before starting exactly one live client:

   ```bash
   ros2 launch tracker_TEAM_15 tracker_tb3_sim_TEAM_15.launch.py dry_run:=true use_sim_time:=true
   # Ctrl-C the preview, then supervise motion:
   ros2 launch tracker_TEAM_15 tracker_tb3_sim_TEAM_15.launch.py dry_run:=false use_sim_time:=true
   ```

   Observe accepted goals, action results, fresh TF and actual Red motion. Drift alone is not proof of commanded pursuit. If map/laser alignment is wrong or navigation becomes unhealthy, stop the tracker and cancel any outstanding navigation goal through the active action client/operator controls; stopping this tracker alone does not guarantee goal cancellation.

5. In a separate terminal, run one reporter (the current session already has this in terminal #1):

   ```bash
   ros2 launch tracker_TEAM_15 capture_report.launch.py enable_reporting:=true use_sim_time:=true my_id:=0 opp_id:=1 image_topic:=/tb3_0/camera/image_raw/compressed allow_latest_tf:=true
   ```

   `allow_latest_tf` enables the bounded common-time approximation described below; it is not exact image-time TF proof. IDs 0/1 are this simulation's assignments, not universal referee IDs.

### Camera dependency and evidence

The camera-equipped SDF exists only at `~/ros2_ws/TEAM15_HANDOFF_ASSETS/camera_candidate/team15_red_with_camera.sdf` in the original workspace; it is **not bundled in this integration repository**. Its existence and the reporter's image bytes were checked live. A clean clone cannot recreate the camera model from this repository. Manual camera injection/replacement has not been verified as a reproducible procedure and is deliberately not prescribed here; preserve the currently working model.

```bash
ros2 topic info /tb3_0/camera/image_raw/compressed -v
timeout 8s ros2 topic hz /tb3_0/camera/image_raw/compressed
ros2 topic echo /tb3_0/tracker_report --once --field my_id
ros2 topic echo /tb3_0/tracker_report --once --field rel_dist
```

Inspect `/tb3_0/tracker_report_img/compressed` in RViz and the actual JPEGs under `~/.ros/team15_captures`. Retain terminal logs, lifecycle results, action results, pose measurements and screenshots with their time/source. A publication log does not prove subscriber delivery, opponent visibility or full assignment completion.

On 21 October the live terminal #1 showed `CAPTURE REPORT PUBLISHED: 8715 bytes, distance=0.478m, rel_yaw=1.2deg`, saved as `/home/user/.ros/team15_captures/capture_my0_opp1_5660_431000000.jpg`, with preceding repeated publications. This witnesses reporter publication with nonempty image data; image contents and downstream delivery were not yet inspected at that checkpoint. Nav2 had previously failed; after a single relaunch all three named servers returned `active [3]`. Earlier handoff reports of approximately 5 Hz camera input and a successful four-package build are prior-session evidence, not a fresh build in this documentation check.

Remaining demonstration gaps include sustained moving-target pursuit, repeatability from a fresh launch and calibrated camera geometry. Physical deployment, authoritative referee schema and licensing remain unresolved as described below. No simulator reset or model replacement is required by this procedure.

Later in the same live check, one tracker goal `(0.14, -0.78)` was accepted and returned success. All three navigation servers remained active afterwards. A subscriber received `rel_dist=0.46691790223121643`; a saved JPEG preview visibly showed the opponent. Red Gazebo positions changed from `(0.199246, -0.733818)` to `(0.208998, -0.732742)`, but known background drift and the near-current-position goal prevent attributing this small change to pursuit. RViz showed substantial laser/map misalignment, so pursuit was stopped after the completed goal; localization, camera, map and Nav2 were preserved. Sustained pursuit and corrected alignment remain outstanding; report receipt and one opponent-visible image have now been observed, without asserting referee acceptance or exact physical camera geometry.

The existing candidate source's `scripts/check_source.py` was rerun inside Construct: 23 tests passed, no failures/errors/skips; 30 Python, 4 XML, 4 JSON/workspace and 3 YAML files parsed without errors. This is source verification, not `colcon test`. The README-only handoff change passed `git diff --check`; local Windows Python launcher aliases were unavailable, so the source checks were run on the existing remote revision rather than claiming a local rerun of the edited Markdown test.

### General simulation notes

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

The final audit results, including separate source-suite and `colcon test` counts, are recorded in [`docs/CHECK_RESULTS.json`](docs/CHECK_RESULTS.json). Use the [requirements and deployment checklist](docs/DEPLOYMENT_CHECKLIST.md) before demonstration or physical use. The [report/repository discrepancy table](docs/REPORT_REPOSITORY_DISCREPANCIES.md) separates unresolved group-report claims from verified repository evidence.

Before a demonstration pass: build four packages; compare report schemas; verify both AMCL/TF chains, the camera and clocks; inspect a dry-run goal; supervise moving-opponent pursuit; inspect action results and post-goal poses; verify report delivery and an image visibly showing the opponent; repeat after five seconds.

- No camera: pursuit continues. Check topic type, QoS and compressed transport; never supply blank images.
- No capture: check reporting enablement/IDs, timestamps, TF, geometry and cooldown. A bounded fallback is optional, not exact-time evidence.
- RViz “No Image”: select the separate compressed stream and inspect bytes/header/frame/QoS before editing the interface.
- No goals: check clock source, base frames, fresh TF, dry-run, Nav2 lifecycle and namespaced action.
- Duplicate packages: exclude the extra checkout from the colcon search path without deleting working source.
- Lost target/shutdown: explicitly cancel active Nav2 goals; no new safety controller is claimed.

## Redistribution

No course PDFs, private email, lab photos, downloaded archives, robot meshes or maps are included. External ROS packages stay upstream. Repository-level licensing and inherited course-code rights remain for the team to confirm before advertising an open-source release; package metadata is not a complete license grant. See [public release review](docs/RELEASE_REVIEW.md#public-release).

## Project history

Terence Xu developed the initial TF-based opponent tracking and pursuit-goal implementation, which Dibya Karki subsequently extended through integration, navigation-goal handling, capture/reporting development, testing and repository consolidation. This brief history does not replace or modify the team's signed contribution attestation.
