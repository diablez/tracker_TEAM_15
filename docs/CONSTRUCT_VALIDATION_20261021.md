# Construct validation — 21 October 2026

Live ROS 2 Humble checks used the existing simulator, camera-equipped Red model, map server, dual AMCL and candidate overlay. No world reset, teleport, model replacement, course-map edit or fabricated static TF was used. The Gazebo master for this session was http://4_simulation:11345.

## Alignment diagnosis and correction

Both laser frames were correctly namespaced (tb3_0/base_scan and tb3_1/base_scan). The map was 137 x 141 cells, 0.05 m resolution, origin (-3.46, -1.84). Before correction, latest-scan median/90th-percentile nearest occupied-cell errors were 0.584/1.432 m for Red and 0.454/1.430 m for Green. Only 24.8%/32.0% of valid returns were within 0.10 m of occupied cells.

Independent rigid fits of the two scans to the unchanged occupancy map gave similar corrections: (0.049, 1.651, -0.108 rad) and (0.059, 1.654, -0.121 rad). To distinguish a localization error from a different world, the live Gazebo room was queried read-only: turtlebot3_room had identity world pose and used the preserved turtleroom_v2.dae collision mesh. A horizontal mesh section at laser height 0.18 m was sampled and registered against occupied cells. The measured world-to-map planar relationship was approximately tx=-0.0443 m, ty=1.6933 m, yaw=-0.0470 rad; trimmed RMS residual was 0.0291 m. These are measured coordinates for this map/session, not universal constants.

Actual Gazebo robot poses were read using gz model -m turtlebot3_burger_N -p. Their planar positions and headings were transformed using that measured relationship, then published once to the existing AMCL initialpose topics. This changes pose estimates, not Gazebo robot positions. After correction, latest-scan median/90th-percentile errors were 0.0222/0.0416 m and 0.0229/0.0377 m, with 96.3%/96.2% of valid returns within 0.10 m. RViz visually showed scans following walls and cylinders. A 20-scan acquisition preceded each latest-scan check; these particular values describe the latest scan, not an average over 20 scans. Background pose arrows in the saved RViz configuration can retain historical initial-pose displays.

## Navigation evidence and limits

All three Red Nav2 lifecycle servers were active before and after the tests. One rearward goal was accepted but timed out after 40 wall seconds; displacement was about 0.007 m and is not evidence of commanded translation. A shorter repeated rearward probe recorded mostly zero linear velocity and alternating small angular commands, with maximum linear command 0.00632 m/s. Each unfinished goal was explicitly cancelled, and Nav2 logged cancellation and stopping.

A forward goal (1.00, 1.04) was subsequently accepted and succeeded (action status 4). Red map pose changed from (0.793545, 1.055401) at simulation time 6834.878 to (0.925802, 1.064803) at 6837.470: 0.13259 m in 2.592 simulation seconds. Recorded forward command reached 0.12 m/s. This direction, speed and duration distinguish commanded translation from the slow preceding drift. Minimum received scan range in the reported final sample was 0.3175 m. This proves one commanded forward navigation manoeuvre, not sustained pursuit or a general collision-free navigation guarantee.

No moving-target chase was attempted after the rearward-controller limitation was found and the user requested a quick wrap-up. Sustained moving-target pursuit, robust rearward/turn-around behaviour, repeatability from a fresh launch and full camera acceptance remain outstanding. No duplicate tracker was launched. The existing reporter and simulator were preserved.

## Reproducing the alignment check

1. Source /opt/ros/humble/setup.bash and ~/team15_candidate_ws/install/setup.bash. Inspect existing nodes/processes and the current Gazebo master before launching anything.
2. Confirm /clock advances, RViz uses map and simulation time, and both scans carry namespaced frames with fresh TF.
3. Compare valid finite scan endpoints, transformed at their acquisition timestamps where available, against occupied map cells across multiple scans. Keep a before/after record. The initial latest-scan checks used latest TF for stationary robots; they are not exact-time moving-scan proof.
4. Confirm the live room collision geometry and its world pose. Determine the map/world relationship from static geometry; do not assume Gazebo x/y equal map x/y. For a measured planar transform (tx, ty, a), map coordinates are x_m=cos(a)*x_w-sin(a)*y_w+tx, y_m=sin(a)*x_w+cos(a)*y_w+ty, yaw_m=yaw_w+a.
5. Re-read actual current robot poses because this session drifts. Initialize the existing AMCL instances in map coordinates, without moving models or editing the course map. Recheck numerical residuals and visual alignment before motion.
6. Verify active lifecycle states and costmaps; supervise one bounded clear forward goal with an explicit cancellation path. A successful near-current goal or drifting pose is insufficient evidence of pursuit.

The adjacent evidence directory preserves measured JSON/logs and source-check results. The course world, mesh, map and camera model remain external. No redistribution of those assets is added.

## Final timestamped scan and camera check

A final check transformed 30 scans per robot at acquisition timestamps. Aggregate metrics (metres; fraction within 10 cm) follow:

{
  "0": {
    "scans": 30,
    "mean_median_m": 0.022013570430824074,
    "mean_p90_m": 0.047486667126429155,
    "mean_fraction_within_10cm": 0.9490066000556221
  },
  "1": {
    "scans": 30,
    "mean_median_m": 0.02469003106833265,
    "mean_p90_m": 0.050570525336935575,
    "mean_fraction_within_10cm": 0.950195746321887
  }
}

Both local and global costmap grids were received in tb3_0/odom and map. Receipt alone is not comprehensive costmap-health proof. The same 15-wall-second acquisition received 48 compressed camera frames (latest 9707 bytes) and no new capture report. The advertised tb3_0/camera_optical_frame was absent from TF. Optical extrinsics and new valid camera reporting remain unverified. Preserve the camera model and determine its real frame geometry before claiming calibrated camera validation. Previous report/image observations remain historical evidence.
