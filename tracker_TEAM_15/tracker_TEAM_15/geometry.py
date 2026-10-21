"""Pure-Python planar pursuit geometry for independent validation.

This module contains no ROS imports so it can be tested on Windows.
It is not a complete robot tracker, perception system, or Nav2 controller.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, degrees, hypot, pi, radians, sin


@dataclass(frozen=True)
class Pose2D:
    """2D pose. x and y in metres; yaw in radians, counter-clockwise."""
    x: float
    y: float
    yaw: float


def wrap_angle(angle_rad: float) -> float:
    """Normalize an angle to [-pi, pi]."""
    return atan2(sin(angle_rad), cos(angle_rad))


def relative_pose(origin: Pose2D, target: Pose2D) -> Pose2D:
    """Pose of target expressed in origin's body frame (SE(2) inverse transform)."""
    dx, dy = target.x - origin.x, target.y - origin.y
    c, s = cos(origin.yaw), sin(origin.yaw)
    return Pose2D(c*dx+s*dy, -s*dx+c*dy, wrap_angle(target.yaw-origin.yaw))


def desired_pose_behind(opponent: Pose2D, offset_m: float = 0.5) -> Pose2D:
    """Planar goal behind the opponent, facing along the opponent's heading.

    This is one design choice inside the lecturer's allowed rear operating arc;
    it is not the only possible pursuit policy. It has not been Nav2-tested.
    """
    if offset_m <= 0:
        raise ValueError("Pursuit offset must be positive")
    return Pose2D(opponent.x-offset_m*cos(opponent.yaw),
                  opponent.y-offset_m*sin(opponent.yaw),
                  wrap_angle(opponent.yaw))


def operating_zone_angle_deg(opponent: Pose2D, chaser: Pose2D) -> float:
    """Angular location of the chaser around the opponent, relative to its heading."""
    return degrees(wrap_angle(atan2(chaser.y-opponent.y,
                                   chaser.x-opponent.x)-opponent.yaw))


def is_in_operating_zone(opponent: Pose2D, chaser: Pose2D,
                         fov_deg: float = 80.0, buffer_deg: float = 30.0) -> bool:
    """True if chaser lies outside the opponent's forward HFOV plus buffers.

    Tests only angular geometry, not distance, occlusion or camera visibility.
    The zero-distance case is excluded because bearing is undefined.
    """
    if not (0 < fov_deg < 360 and 0 <= buffer_deg and fov_deg+2*buffer_deg < 360):
        raise ValueError("Invalid FOV/buffer geometry")
    if hypot(chaser.x-opponent.x, chaser.y-opponent.y) < 1e-12:
        return False
    exclusion_half_angle = fov_deg / 2.0 + buffer_deg
    return abs(operating_zone_angle_deg(opponent, chaser)) >= exclusion_half_angle - 1e-9


def relative_distance_m(chaser: Pose2D, opponent: Pose2D) -> float:
    """Euclidean separation, metres."""
    return hypot(opponent.x-chaser.x, opponent.y-chaser.y)


def relative_orientation_deg(chaser: Pose2D, opponent: Pose2D) -> float:
    """Opponent's yaw relative to chaser's yaw, in degrees (not bearing)."""
    return degrees(wrap_angle(opponent.yaw-chaser.yaw))
