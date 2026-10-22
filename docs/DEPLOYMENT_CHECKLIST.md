# Requirements and deployment checklist

Use this checklist with the root README. A checked source/build item is not evidence of simulated or physical behaviour.

## Fresh clone and build

- [ ] Ubuntu 22.04 and ROS 2 Humble are installed and sourced.
- [ ] Clone default `main`; do not add a second copy to the same colcon workspace.
- [ ] Run `rosdep install --from-paths . --ignore-src -r -y --rosdistro humble` after initializing rosdep on the host.
- [ ] Run `bash scripts/build_team15.sh`, source `install/setup.bash`, and confirm all four packages build.
- [ ] Confirm `ros2 pkg executables tracker_TEAM_15` lists `tracker_node`, `tracker_two_tb4_TEAM_15`, `tracker_tb3_sim_TEAM_15`, and `capture_report`.
- [ ] Confirm installed launch/config files resolve from package shares, not source-relative paths.
- [ ] Run `python3 scripts/check_source.py`, `colcon test`, `colcon test-result --verbose`, and `git diff --check`.

## Interface gate

- [ ] Obtain the lecturer/referee `TrackerReport.msg` and the receiver's installed interface.
- [ ] Run `python3 scripts/verify_interface.py --expected /path/to/authoritative/TrackerReport.msg --installed`.
- [ ] Stop deployment on any field-count, order or type mismatch; rebuild every peer only after the schema is agreed.
- [ ] Confirm IDs and the degree/radian convention with the assessment requirements.

## Construct simulation

- [ ] Supply the external course world, map plus referenced image, meshes, camera-equipped model and RViz configuration; they are not in this repository.
- [ ] Reuse the working Construct session/overlay when applicable; do not duplicate nodes or package overlays.
- [ ] Confirm `/clock`, both namespaced scan streams, and fresh `map -> tb3_N/odom -> tb3_N/base_link` TF chains.
- [ ] Initialize AMCL from measured map/world geometry and verify scan alignment numerically and visually.
- [ ] Confirm Red Nav2 lifecycle servers are active and `/tb3_0/navigate_to_pose` exists.
- [ ] Run `tracker_tb3_sim_TEAM_15` in dry-run first; stop it before starting one supervised live client.
- [ ] Verify action acceptance/result, commanded velocity and measured displacement; distinguish these from Gazebo drift.
- [ ] Verify real compressed frames, timestamps/frame IDs, report receipt and an opponent-visible saved image.
- [ ] Cancel unfinished goals explicitly. Do not infer cancellation merely from stopping the tracker process.

## Physical TurtleBot4

- [ ] Use a human supervisor and a tested stop method; preserve the known working lab bringup.
- [ ] Confirm robot namespaces, shared map, discovery configuration, TF conventions and actual OAK-D topic/QoS.
- [ ] Avoid launching duplicate map, localization or Nav2 stacks.
- [ ] Keep reporting disabled until schema, IDs, timestamps, camera/body alignment and receiver compatibility pass.
- [ ] Repeat pursuit, loss-of-target, corrupt/missing-camera, cooldown and receiver tests on the actual fleet.
- [ ] Archive dated logs and real captures without publishing private communications or the signed attestation.

## Release gates still open

- Authoritative six-versus-five-field hardware interface evidence.
- Fresh-start Construct reproducibility with redistributable or clearly supplied external assets.
- Sustained moving-target pursuit, rearward/turn-around behaviour and explicit shutdown cancellation.
- Calibrated physical camera geometry and supervised TurtleBot4 validation.
- Repository-level licensing and inherited course-source redistribution permission.
