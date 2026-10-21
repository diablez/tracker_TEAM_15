"""Shared capture checks; independent of ROS imports for isolated tests."""
import math


def stamp_ns(header):
    return int(header.stamp.sec) * 1_000_000_000 + int(header.stamp.nanosec)


def image_valid(image, max_bytes=8_000_000):
    """Metadata gate; decoding is performed once when a frame is received."""
    fmt = image.format.lower()
    return (bool(image.header.frame_id) and 0 < len(image.data) <= max_bytes
            and stamp_ns(image.header) > 0 and 'compresseddepth' not in fmt
            and any(kind in fmt for kind in ('jpeg', 'jpg', 'png')))


def decode_image(image):
    """Reject mislabeled/corrupt payloads. No synthesized image fallback."""
    import cv2
    import numpy as np
    try:
        decoded = cv2.imdecode(np.frombuffer(bytes(image.data), dtype=np.uint8),
                               cv2.IMREAD_COLOR)
        return decoded is not None and decoded.size > 0
    except (cv2.error, ValueError):
        return False


def pose_pair(buffer, global_frame, frames, image_stamp, now_ns, time_at_ns,
              latest_time, *, max_skew_sec=0.25, allow_latest=False,
              max_tf_age_sec=1.0, future_tolerance_sec=0.0):
    """Nonwaiting lookup at image time, or explicitly bounded common TF time.

    Adapter must raise ValueError for TF lookup failure. It never waits for TF.
    Fallback queries BOTH frames at the older latest stamp, not unrelated times.
    """
    image_ns = int(image_stamp.sec)*1_000_000_000+int(image_stamp.nanosec)
    try:
        exact = [buffer(global_frame, frame, time_at_ns(image_ns)) for frame in frames]
        return [t.transform for t in exact], False
    except ValueError:
        if not allow_latest:
            raise
    latest = [buffer(global_frame, frame, latest_time) for frame in frames]
    stamps = [stamp_ns(t.header) for t in latest]
    common_ns = min(stamps)
    if any(s <= 0 or not -future_tolerance_sec <= (now_ns-s)/1e9 <= max_tf_age_sec
           for s in stamps):
        raise ValueError('Latest TF is unstamped, stale or future-dated')
    if abs(common_ns-image_ns)/1e9 > max_skew_sec:
        raise ValueError('Latest common TF exceeds image skew limit')
    pair = [buffer(global_frame, frame, time_at_ns(common_ns)) for frame in frames]
    return [t.transform for t in pair], True


def capture_geometry(chaser, opponent, min_distance=.4, max_distance=.6,
                     half_fov_deg=40., exclusion_deg=70.):
    """Return distance/yaw degrees only when the geometric capture gates pass."""
    def yaw(q):
        return math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))
    def wrap(a):
        return math.atan2(math.sin(a), math.cos(a))
    dx = opponent.translation.x-chaser.translation.x
    dy = opponent.translation.y-chaser.translation.y
    cyaw, oyaw = yaw(chaser.rotation), yaw(opponent.rotation)
    if not all(math.isfinite(v) for v in (dx, dy, cyaw, oyaw)):
        raise ValueError('Nonfinite pose')
    distance = math.hypot(dx, dy)
    camera = abs(math.degrees(wrap(math.atan2(dy, dx)-cyaw)))
    zone = abs(math.degrees(wrap(math.atan2(-dy, -dx)-oyaw)))
    if not (distance > 0 and min_distance <= distance <= max_distance
            and camera <= half_fov_deg and zone >= exclusion_deg):
        raise ValueError('Capture geometry outside configured gates')
    return distance, math.degrees(wrap(oyaw-cyaw))


def populate_report(report, image, my_id, opp_id, distance, orientation):
    """Support an installed header-bearing type without changing the wire schema.

    This does not make different DDS schemas interoperable. All peers must use
    the exact same compiled interface. Header, when present, describes the image.
    """
    report.my_id, report.opp_id = my_id, opp_id
    report.image = image
    report.rel_dist, report.rel_orient = float(distance), float(orientation)
    if hasattr(report, 'header'):
        report.header.stamp = image.header.stamp
        report.header.frame_id = image.header.frame_id
    return report
