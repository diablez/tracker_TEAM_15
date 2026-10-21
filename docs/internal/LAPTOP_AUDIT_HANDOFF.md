# Repository audit checkpoint - 21 October 2026

This is an incomplete audit checkpoint for continuing on the laptop that holds
the original uploads and working source. Requirements compliance is not yet
established. Do not merge or deploy this checkpoint as a completed repair.

## Branch and bounded changes

- Review branch: `audit/ros2-humble-packaging`.
- Base: `b88fa06c2f0b272b278443484d73b685fa66228a` on canonical `main`.
- Added `ament_python` build-tool declarations to the localization and planner
  manifests, matching their existing exported build type.
- Declared Navfn, DWB core/critics, costmap and behavior-tree dependencies used by
  the existing TB3 Nav2 YAML. These declarations still need Humble rosdep/build
  verification; no Nav2 tuning was changed.
- Ignored local dependency caches and Python build outputs.
- No tracker implementations, entry points, launches, message definitions,
  configuration values, maps or simulator assets were modified.

The user requested a pause on uncertain repairs until the actual project
requirements can be checked. Broader packaging/organization work was stopped.

## Sources checked in this session

The canonical main branch already contains the earlier integration, release
review, and bounded Construct evidence. Read [the previous review](RELEASE_REVIEW.md)
and [live validation record](../CONSTRUCT_VALIDATION_20261021.md) as historical
evidence, not new testing in this checkpoint.

The other Team 15 repository was inspected read-only through GitHub. Its main
remains `90e97d89cd8493d527d1e85213c8d9a96bf45fdc`; its
`integration/construct-sim` branch remains
`c08a7eafa981df8f897f6cc46f57e6af270688ee`, matching the previous review's refs.
Git blob identity confirmed these canonical files exactly match that integration:

| Canonical file | Blob SHA |
| --- | --- |
| `localization_server_TEAM_15/config/tb3_0_amcl_config.yaml` | `c738ebdbfe6ee075be0277efa02cceacdf63ff81` |
| `localization_server_TEAM_15/config/tb3_1_amcl_config.yaml` | `c3b5e3088b57f9b6279c8f065d686804dab13b0a` |
| `path_planner_server_TEAM_15/config/tb3_0_sim_nav2.yaml` | `f29af63686d3169de97251c39b8ada7b78877f0d` |

The canonical `tracker_node.py` also matches the guided main's blob
`9b25debe9177d68ef9ec143d656901138972440c`. Simulation launch files differ;
do not replace them wholesale. The original physical tracker remains in Git
history and the current tracker implementations were left unchanged here.

The original verified Construct TAR and QA-reviewed ZIP were unavailable on
this device. Their recorded hashes and previous comparison are in the earlier
review; they were not independently reproduced. The referenced earlier chat
could not be read with the tools available in this session.

## Checks actually run

`scripts/check_source.py` passed using isolated Windows Python 3.14.7 with
PyYAML, OpenCV and numpy: 23 tests, zero failures/errors/skips; 30 Python files
checked with Python 3.10 grammar, 4 XML, 9 JSON/workspace and 3 YAML files parsed.
`git diff --check` passed. These are source/unit checks, not a ROS build.

No usable WSL installation, ROS, colcon, simulator or hardware was available
here. Humble dependency resolution, installation, generated messages, launch
execution, DDS, sustained pursuit and physical behavior were not tested.

## Resume from the existing laptop source

1. Save open editor buffers and inspect the original folder and `git status`.
   Preserve unsaved work and local changes. If it is an exported folder without
   Git metadata, keep it intact and compare from a sibling checkout.
2. In the canonical Git checkout, confirm `origin` points to
   `diablez/tracker_TEAM_15`, then fetch this review branch. If the checkout is
   clean, switch to it; otherwise use a sibling worktree rather than overwrite
   the working files. No reset, force push or merge to main is needed.
3. Locate the authoritative project brief/rubric, lecturer interface source,
   verified Construct snapshot and QA-reviewed handoff ZIP on the laptop.
   Check the archives against the previously recorded SHA-256 values before
   treating them as the same inputs. Read any applicable `AGENTS.md` first.
4. Map proposed repairs to requirements before editing. Preserve the three TB3
   YAML files and both tracker implementations. Keep legacy TB4 templates out
   of the active TB3 configuration. The old physical YAMLs and behavior tree
   are already absent from main and recoverable in history; document their
   status rather than reintroducing them as tested defaults.
5. Remaining audit: nested asset installation (current setup rules are mostly
   flat globs), launch references, case-sensitive filenames, package manifests,
   runnable installed entry points, README consistency, and VS Code visibility.
   Mixed-case ROS package names are existing identities; renaming them requires
   a deliberate migration, not cosmetic normalization.
6. Maps and RViz presets are absent from this canonical tree. The earlier review
   deliberately excluded external course assets. Recover and assess the actual
   laptop assets before deciding what belongs in the repo and what is supplied
   externally; do not invent replacements or copy legacy reference defaults.
7. Run source checks, then rosdep, colcon build/test, installed asset/entry-point
   checks and launch argument checks in an isolated Humble workspace. Do not
   disturb the working Construct/lab workspace. Record actual results and skips.
8. Update the review branch/PR with evidence, requirements coverage, and remaining
   interface, camera, cancellation, pursuit and hardware gaps. Merge only after
   user approval.

Suggested continuation request:

> Continue the tracker_TEAM_15 audit from docs/LAPTOP_AUDIT_HANDOFF.md on
> audit/ros2-humble-packaging. First inspect this laptop's original workspace,
> project requirements and verified snapshot/QA ZIP. Preserve local work, TB3
> configuration and both tracker implementations. Check every proposed repair
> against requirements; finish with a tested review branch and PR, without
> merging main or changing the working robot/simulator session.
