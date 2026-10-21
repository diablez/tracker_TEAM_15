# Group report and repository discrepancy review

This table records discrepancies that can be established from the repository and the audit brief. The final group-report PDF, signed contribution attestation and October 14 lab workspace were not present in the accessible checkout or laptop paths searched on 21 October 2026. Page numbers and exact quotations therefore cannot be independently verified; obtain the PDF before proposing any academic-report amendment. No PDF or attestation has been edited or published.

| Report claim and location | Repository source or evidence | Discrepancy | Recommended correction | Affects |
| --- | --- | --- | --- | --- |
| October 14 hardware interface used a top-level `std_msgs/Header header` (page/section unavailable) | [`TrackerReport.msg`](../tracker_interfaces_team_15/msg/TrackerReport.msg), [`RELEASE_REVIEW.md`](RELEASE_REVIEW.md#report-interface-reconciliation) | The repository and lecturer September 16 reporting slide use five top-level fields; the reported lab revision has six. These DDS types are incompatible. The working lab `.msg` and receiver type are missing. | Preserve the five-field repository type. Before hardware use, recover both authoritative definitions, choose one deliberately, and rebuild every publisher/subscriber. | Code/deployment; proposed report clarification requires approval |
| 45 tests (page/section unavailable) | [`CHECK_RESULTS.json`](CHECK_RESULTS.json), root `tests/` | The canonical source suite contains 23 tests. The 45 may describe another branch, implementation or a cumulative count; no mapping was supplied. | Keep both counts revision-qualified. Add the missing test list/commit if 45 is to remain an assessed claim. | Documentation/report |
| Hardware tracking/reporting demonstrated (page/section unavailable) | [`RELEASE_REVIEW.md`](RELEASE_REVIEW.md), [`LAPTOP_AUDIT_HANDOFF.md`](LAPTOP_AUDIT_HANDOFF.md) | The October 14 source, installed interface and receiver evidence are unavailable. Simulation success cannot establish TurtleBot4 compatibility. | Describe hardware results only against recovered dated logs/source; retain physical validation as an open gate. | Documentation/report/deployment |
| Pursuit behaviour described as working (page/section unavailable) | [`CONSTRUCT_VALIDATION_20261021.md`](CONSTRUCT_VALIDATION_20261021.md#navigation-evidence-and-limits) | One forward 13.3 cm goal succeeded. Rearward motion timed out and sustained moving-target pursuit was not attempted after correction. | State the bounded successful manoeuvre and failed rearward case separately; do not generalize to sustained pursuit. | Documentation/report |
| Map/localization operation (page/section unavailable) | [`CONSTRUCT_VALIDATION_20261021.md`](CONSTRUCT_VALIDATION_20261021.md#alignment-diagnosis-and-correction) | Earlier localization was badly misaligned; after measured initialization, aggregate 30-scan median errors were about 2.2 cm and 2.5 cm. These are different session states. | Report before/after values with dates and method; do not combine them as one run. | Documentation/report |
| Camera/report topic and delivery (page/section unavailable) | Root [`README.md`](../README.md#camera-dependency-and-evidence), Construct validation final check | Construct used `/tb3_0/camera/image_raw/compressed`; the physical template defaults to `/<chaser>/oakd/rgb/preview/image_raw/compressed`. One historical report/image was received, while a later 15-second check received 48 camera frames and no new report. | Name platform and revision with every topic/result. Do not imply continuous report delivery or physical camera validation. | Documentation/report/deployment |
| Source paths and line references (page/section unavailable) | Current four-package tree and Git history | Older report references may target superseded branches or the unavailable lab workspace. | Replace fragile line numbers with commit SHA plus file/symbol after the PDF and original source are recovered. | Report only, subject to approval |

## Interface decision

The repository intentionally retains these top-level fields in order: `my_id`, `opp_id`, `image`, `rel_dist`, `rel_orient`. `CompressedImage` already contains its own nested header, but that is not wire-equivalent to adding a top-level header. `scripts/verify_interface.py` provides an exact comparison and should be run against the lecturer/referee definition before deployment.

## Missing authoritative evidence

- `ENME703 Group Report FINAL.pdf` for exact pages, wording and the 45-test inventory.
- `Team15_Contribution_Attestation_SIGNED.pdf`; preserve it privately and unchanged.
- The lecturer-supplied reference `.msg` and receiver's installed `ros2 interface show` output.
- The October 14 lab source/overlay and dated hardware logs or captures.
- The original brief/rubric and supplied ROS packages needed for requirements traceability.
