# Integration review and release record

## Scope and provenance

Prepared on 21 October 2026 on `team15/demo-integration-20261021`, continuing the existing local audit. Base: `a43c7bd5ae852b061bc20face78c1b3fd3f57987`. No running Construct or physical robot session was modified. The separate Documents workspace was read for comparison only; unsaved editor buffers were not inspected or synchronized.

| Source | Observed state |
| --- | --- |
| Canonical `main`, `Dibyas-updated-verion`, remote integration branch at audit start | Same base SHA above |
| Canonical `construct-tb3-sim-prep` | `80eb96bd5ca0b4336049514941a3d02d8fb221a9`; one commit ahead, four-file sim-client addition |
| Guided workspace `main` | `90e97d89cd8493d527d1e85213c8d9a96bf45fdc` |
| Guided `integration/construct-sim` | `c08a7eafa981df8f897f6cc46f57e6af270688ee`; different pursuit/report implementation and operator-confirmed capture |
| Construct TAR vs supplied candidate ZIP | 122 regular source members inspected: 36 identical, 22 changed, 64 absent; course source accounts for additional TAR contents |
| Existing editor workspace | 48 regular source files compared read-only; differs from this integration; not synchronized |
| October 14 lab workspace | Not available as actual source/installed interface in this audit; do not call the GitHub base a proven copy of that workspace |

SHA-256 of the supplied candidate ZIP: `e2c00567abd0f36fa09f8213b789570460373180d16aabf130f7ab187cf03822`. Both local ZIP variants matched. TAR: `fb3fbb15c7ec254898f7e631a2e9b58f3a6f9f736c6837813e691003cc3933f0`.

## Changes and preservation

- Retained physical executable, class and TF/Nav2 pursuit implementation. Moved capture to an independent timer, made reporting explicitly opt-in with explicit IDs and configurable camera topic, removed blank-image reports, and added decoder/freshness/image-time TF/cooldown checks. This is a modified review version, not a claim of unchanged or hardware-qualified source. The original GitHub source remains at the base commit; the separate working lab workspace was untouched.
- Retained `tracker_node` and the Construct simulation pursuit client. The simulation client has the earlier future-TF rejection fix in addition to its existing action handling. No camera gate was added to pursuit.
- Shared capture policy prefers nonwaiting exact image-time TF. Optional fallback queries both poses at one common TF timestamp within a configured image-skew bound, rejects stale/future/unstamped transforms, and defaults off. Images are decoded on receipt; corrupt images cannot become captures.
- Preserved five-field report schema and field order, added exact installed/source comparison utility and conditional header population only for an intentionally installed header-bearing type. This does not bridge incompatible DDS schemas.
- Added physical launch dependencies and explicit wall-time wrapper arguments, configurable report launch arguments, portable build/preflight commands, VS Code settings/workspace/extensions, tests and one authoritative README.
- Removed tracked bytecode/editor-machine settings; excluded redundant inherited readmes, unused physical handwritten configs and copied world/model/map/reference assets. Source histories/backups and excluded materials remain outside the release tree locally; they are not uploaded by these commits. Build/install/log/cache/archive/environment patterns are ignored.

## Report interface reconciliation

Evidence checked:

1. Lecturer September 16 project-description slide, reporting table: exactly `my_id`, `opp_id`, `image`, `rel_dist`, `rel_orient` in that order. The full slide was extracted and visually checked. The source document is not redistributed.
2. Available lecturer tracker template: five named fields with image listed first, plus prose warning about a header. It explicitly explains that the custom report cannot directly display in RViz and requests a separate compressed-image publisher. This creates ambiguity about field order and header interpretation; it is not authority for silently adding a field.
3. Fourteen available archive schemas, GitHub and saved editor interface: the same five fields in repository order.
4. Ciaron's independent static review: describes an additional top-level header in the October 14 lab version. That `.msg` and the lecturer/referee consumer's installed type are still needed. The three referenced lab photos were not exposed by the recovered attachment listings, so no claim is made about their contents.

Resolution for this branch: no sixth field and no claimed compatibility with a different installed lab schema. Run `scripts/verify_interface.py` against the actual authoritative source and generated type. A mismatch blocks integration deployment/merge approval for capture consumers. Image timestamps/frame IDs and the separate image topic are preserved in either deliberate build.

## Test evidence

The review environment is Windows with an isolated Python 3.12 runtime. Ubuntu 22.04 is installed in WSL, but read-only inspection found no `/opt/ros`, `ros2`, `colcon` or `gzserver`. No ROS or Gazebo packages were installed. No ROS build, generated-message test, DDS test, fresh-start simulation or physical test was run.

The maintained isolated suite initially passed 18 tests, including a real OpenCV decode/reject test after isolated dependency installation. It tests production policy functions and unmodified timer method bodies with substituted ROS imports/clock/TF/publishers. Follow-up additions and final counts are recorded in `docs/CHECK_RESULTS.json`. A generated synthetic JPEG is used only as a unit-test fixture, never as a robot capture. Tests include missing-camera pursuit, exact/fallback common-time TF, skew/freshness rejection, five-field report population, cooldown, missing TF and schema incompatibility.

Earlier eight-test results describe the previous candidate and are superseded by this suite. Static parsing is not runtime validation. Hardware claims in older readmes were removed rather than repeated as new evidence. The original live simulation client had prior-session evidence; this revision has not reproduced it.

## Public release

Targeted working-tree/history checks look for common credential formats and machine paths, with no secret values printed. No matching credentials were found in the original 52 reachable historical blobs. Five historical bytecode blobs contained generic local filesystem paths. Removing bytecode now does not erase history; no history rewrite or force-push is authorized or performed. Pattern scanning cannot guarantee absence of every possible secret.

Course PDFs, photos, private messages, archives, maps, simulator worlds and robot meshes are excluded. Use platform-provided resources separately. The repository does not grant rights to third-party material merely by linking dependencies. Retained generated ROS lint test templates contain their existing Apache notices.

The inherited source includes course-template-derived structure and inconsistent/missing license declarations. `LicenseRef-Team15-Pending` is an explicit placeholder, not a license grant or SPDX approval. Team ownership/permission and a repository-level license must be settled before describing this as an open-source release. Public visibility is separate from licensing and does not deploy the integration or modify main.

## Synchronizing an existing VS Code copy

The local integration commits are not automatically on GitHub or in the existing Documents workspace. Do not copy this tree over unsaved work. Save/backup open buffers first and inspect `git status` in the intended checkout. A folder without `.git` is an exported workspace, not a branch checkout; keep it intact.

After explicit authorization to push this branch, the safest review method is a new clone in a sibling folder:

```bash
git clone --branch team15/demo-integration-20261021 https://github.com/diablez/tracker_TEAM_15.git tracker_TEAM_15-review
cd tracker_TEAM_15-review
code team15.code-workspace
```

For an existing Git checkout, fetch without changing its working tree, inspect the fetched diff, and create a separate worktree:

```bash
git status --short
git fetch origin
git diff --stat HEAD origin/team15/demo-integration-20261021
git worktree add --detach ../tracker_TEAM_15-review origin/team15/demo-integration-20261021
```

Choose a new destination; do not force overwrite, reset, auto-stash or switch a dirty checkout. ROS overlays must be sourced from the chosen build, not an older install tree. No notebooks were present in the inspected canonical/integration/editor sources, and none were manufactured for this robotics release.

## Recommended merge procedure

1. Review local commits and the exact changed-file list. Confirm main/base SHA is unchanged.
2. Recover the October 14 source/installed interface and compare against lecturer/referee consumers. Decide schema deliberately; preserve the known-working lab fallback.
3. In a separate Humble workspace, build all four packages, inspect installed interfaces/executables and run colcon tests. Verify physical wrapper availability/arguments against the installed fleet version.
4. Test camera loss/corrupt frames without interruption to pursuit, exact/fallback TF timing, real report/image delivery and five-second cooldown. Then supervise fresh-start Construct and physical moving-target tests; preserve logs and actual images. Check shutdown/cancel handling.
5. Resolve license/redistribution issues before an open-source release. The authorized publication targets only `team15/demo-integration-20261021` and a draft PR against main; it does not approve a merge or a repository-wide license grant.
6. Merge only after approval and the required checks. Preserve history and the hardware fallback; never force-push or rewrite main as a synchronization shortcut.

Upstream launch arguments were checked against the official [Humble localization source](https://github.com/turtlebot/turtlebot4/blob/humble/turtlebot4_navigation/launch/localization.launch.py) and [Humble navigation source](https://github.com/turtlebot/turtlebot4/blob/humble/turtlebot4_navigation/launch/nav2.launch.py). Actual installed behaviour still needs testing.

## Final publication review

On 21 October 2026, fetched remote refs confirmed both `main` and the remote
integration branch at the recorded base. The local branch contained `f2445f8`
and `b1c8e41`. A plain Windows Python rerun exposed a Markdown-test decoding
error; explicitly reading UTF-8 fixed it. The rerun passed all 23 tests with
zero failures, errors or skips. Parsing passed for 30 Python, 4 XML, 3 YAML and
4 JSON/workspace files, including Python 3.10 grammar checks.

The final credential-pattern scan covered 94 reachable historical blobs and
the release working tree: no matching credentials were found. The only five
machine-path findings were previously committed bytecode blobs already on the
remote base; bytecode is absent from the release tree. No history rewrite was
performed. Pattern scans are not a guarantee against every possible secret.

The retained Apache-noticed ROS templates now include their accompanying
license text; see [third-party notices](../THIRD_PARTY_NOTICES.md). No unresolved
external assets are added. Inherited code permission and repository licensing
remain explicit gates for an open-source release. The draft PR is for source
review, not a claim of deployment readiness or resolved licensing.

ROS/Humble build, generated messages/DDS, Gazebo, real cameras, physical
hardware and the authoritative October 14 message interface remain unvalidated.
The working hardware fallback remains untouched outside this review checkout;
its original GitHub version is preserved in base history.

## Final laptop audit verification

The audit branch was checked again on 21 October 2026 in an isolated Ubuntu
22.04 ROS 2 Humble workspace. All four packages built successfully. The
generated five-field interface, four tracker executables, seven launch files
and three YAML configurations were present in the install tree. Simulation
launch descriptions resolved from installed package shares and exposed their
arguments without starting nodes.

The source suite ran 23 tests: 22 passed and the OpenCV decoder test skipped
because this host combines a NumPy 2.2.6 runtime with an OpenCV extension built
for NumPy 1.x. Static parsing reported no errors. The final `colcon test` run
reported six generated lint tests: four passed, two copyright-template checks
skipped, and none failed. Formatting failures found in the first colcon run
were corrected without changing launch behaviour. Exact counts and remaining
environment limits are in [the machine-readable results](CHECK_RESULTS.json).

`rosdep check` could not run because the host rosdep database is not
initialized. Direct package checks found all declared Nav2 dependencies, but
`turtlebot4_navigation` is absent. Consequently, the physical wrapper launch
files build and install but cannot resolve on this host. No simulator or
physical robot was started. The authoritative report PDF, signed attestation,
October 14 workspace and lecturer/referee installed interface were not found;
the resulting evidence gaps are itemized in the
[discrepancy review](REPORT_REPOSITORY_DISCREPANCIES.md).
