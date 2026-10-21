#!/usr/bin/env python3
"""Team 15: compressed camera capture and geometry-gated TrackerReport.

This node does not detect a robot in pixels. If an external vision detector is
available, enable require_target_visible and supply its fresh Bool topic.
"""
from __future__ import annotations

import math
import os
import time
from pathlib import Path

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from rclpy.time import Time
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import Bool
from tf2_ros import Buffer, TransformListener, TransformException
from tracker_interfaces_team_15.msg import TrackerReport
from .capture_policy import (image_valid, decode_image, pose_pair,
                             capture_geometry, populate_report)


def stamp_ns(header) -> int:
    return int(header.stamp.sec) * 1_000_000_000 + int(header.stamp.nanosec)


def extension(fmt: str) -> str | None:
    fmt = (fmt or '').lower()
    if 'compresseddepth' in fmt:
        return None
    if 'jpeg' in fmt or 'jpg' in fmt:
        return 'jpg'
    if 'png' in fmt:
        return 'png'
    return None


class CaptureReport(Node):
    def __init__(self):
        super().__init__('team15_capture_report')
        defaults = {
            'image_topic': '/tb3_0/camera/image_raw/compressed',
            'report_topic': '/tb3_0/tracker_report',
            'report_image_topic': '/tb3_0/tracker_report_img/compressed',
            'global_frame': 'map',
            'chaser_frame': 'tb3_0/base_link',
            'opponent_frame': 'tb3_1/base_link',
            'camera_frame': '',              # Empty = accept supplied camera frame.
            'my_id': -1, 'opp_id': -1,
            'enable_reporting': False,
            'allow_latest_tf': False,
            'max_tf_image_skew_sec': 0.25,
            'min_distance_m': 0.40, 'max_distance_m': 0.60,
            'camera_half_fov_deg': 40.0,
            'opponent_front_exclusion_deg': 70.0,
            'max_image_age_sec': 1.0,
            'max_receive_age_sec': 0.9,
            'capture_cooldown_sec': 5.0,
            'require_target_visible': False,
            'target_visible_topic': '',
            'max_visibility_age_sec': 0.75,
            'max_image_bytes': 8_000_000,
            'capture_dir': os.path.expanduser('~/.ros/team15_captures'),
            'save_images': True,
            'status_period_sec': 5.0,
        }
        for key, value in defaults.items():
            self.declare_parameter(key, value)
        cfg = {k: self.get_parameter(k).value for k in defaults}
        self.cfg = cfg
        self.global_frame = str(cfg['global_frame']).lstrip('/')
        self.chaser_frame = str(cfg['chaser_frame']).lstrip('/')
        self.opponent_frame = str(cfg['opponent_frame']).lstrip('/')
        self.camera_frame = str(cfg['camera_frame']).lstrip('/')
        self.my_id = int(cfg['my_id'])
        self.opp_id = int(cfg['opp_id'])
        if cfg['enable_reporting'] and not (0 <= self.my_id <= 255 and 0 <= self.opp_id <= 255 and self.my_id != self.opp_id):
            raise ValueError('my_id and opp_id must be distinct uint8 values (0..255)')
        if not (math.isfinite(cfg['min_distance_m']) and math.isfinite(cfg['max_distance_m'])
                and 0 <= cfg['min_distance_m'] <= cfg['max_distance_m']):
            raise ValueError('invalid capture distance interval')
        for key in ('camera_half_fov_deg', 'opponent_front_exclusion_deg'):
            if not math.isfinite(cfg[key]) or not 0 < cfg[key] <= 180:
                raise ValueError(f'{key} must be finite and in (0, 180]')
        if cfg['max_image_bytes'] < 1:
            raise ValueError('max_image_bytes must be positive')
        if not math.isfinite(cfg['capture_cooldown_sec']) or cfg['capture_cooldown_sec'] < 5.0:
            raise ValueError('capture cooldown must be finite and at least five seconds')
        for key in ('max_image_age_sec', 'max_receive_age_sec', 'max_visibility_age_sec',
                    'max_tf_image_skew_sec', 'status_period_sec'):
            if not math.isfinite(cfg[key]) or cfg[key] < 0:
                raise ValueError(f'{key} must be finite and nonnegative')
        if cfg['require_target_visible'] and not cfg['target_visible_topic']:
            raise ValueError('require_target_visible needs target_visible_topic')

        sensor_qos = QoSProfile(
            depth=5, reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )
        report_qos = QoSProfile(
            depth=10, reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
        )
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.sub = self.create_subscription(
            CompressedImage, str(cfg['image_topic']), self.on_image, sensor_qos
        )
        self.visible_sub = None
        if cfg['target_visible_topic']:
            self.visible_sub = self.create_subscription(
                Bool, str(cfg['target_visible_topic']), self.on_visible, sensor_qos
            )
        self.publisher = self.create_publisher(
            TrackerReport, str(cfg['report_topic']), report_qos
        )
        self.image_pub = self.create_publisher(
            CompressedImage, str(cfg['report_image_topic']), report_qos
        )
        self.image = None
        self.image_received = -float('inf')
        self.visible = False
        self.visible_received = -float('inf')
        self.last_report = -float('inf')
        self.last_report_stamp = -1
        self.last_status = -float('inf')
        self.capture_dir = Path(os.path.expanduser(str(cfg['capture_dir'])))
        if cfg['save_images']:
            try:
                self.capture_dir.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                self.get_logger().warn(f'Image saving disabled: {exc}')
                self.cfg['save_images'] = False
        self.timer = self.create_timer(0.2, self.check)
        self.get_logger().info(
            f'Capture ready: {cfg["image_topic"]} -> {cfg["report_topic"]}; '
            f'frames {self.chaser_frame}/{self.opponent_frame}; IDs {self.my_id}/{self.opp_id}'
        )
        if not cfg['require_target_visible']:
            self.get_logger().warn(
                'Geometry-only mode: cannot verify Green is visible or not occluded in pixels'
            )

    def log(self, message: str, warning=True):
        current = time.monotonic()
        if current - self.last_status >= float(self.cfg['status_period_sec']):
            self.last_status = current
            (self.get_logger().warn if warning else self.get_logger().info)(message)

    def on_image(self, msg):
        self.image = None
        if not image_valid(msg, self.cfg['max_image_bytes']) or not decode_image(msg):
            self.log('Waiting for a stamped, decodable compressed RGB image')
            return
        if self.camera_frame and msg.header.frame_id.lstrip('/') != self.camera_frame:
            self.log(f'Image frame mismatch: got {msg.header.frame_id!r}')
            return
        self.image = msg
        self.image_received = time.monotonic()

    def on_visible(self, msg):
        self.visible = bool(msg.data)
        self.visible_received = time.monotonic()

    def check(self):
        if not self.cfg['enable_reporting']:
            return
        msg = self.image
        if msg is None:
            self.log('Waiting for compressed camera frames')
            return
        mono = time.monotonic()
        if mono - self.image_received > self.cfg['max_receive_age_sec']:
            self.log('Image stream stale (receipt age)')
            return
        now_ros = self.get_clock().now().nanoseconds
        stamp = stamp_ns(msg.header)
        age = (now_ros - stamp) / 1e9
        if not (0 <= age <= self.cfg['max_image_age_sec']):
            self.log(f'Image header age invalid: {age:.2f}s; check use_sim_time/clocks')
            return
        if self.cfg['require_target_visible']:
            if (not self.visible or mono - self.visible_received > self.cfg['max_visibility_age_sec']):
                self.log('Waiting for fresh target-visible detector confirmation')
                return

        def lookup(target, source, when):
            try:
                return self.tf_buffer.lookup_transform(target, source, when)
            except TransformException as exc:
                raise ValueError(str(exc)) from exc
        try:
            pair, approximate = pose_pair(
                lookup, self.global_frame, (self.chaser_frame, self.opponent_frame),
                msg.header.stamp, now_ros, lambda ns: Time(nanoseconds=ns), Time(),
                allow_latest=self.cfg['allow_latest_tf'],
                max_skew_sec=self.cfg['max_tf_image_skew_sec'])
            dist, orient = capture_geometry(
                *pair, min_distance=self.cfg['min_distance_m'],
                max_distance=self.cfg['max_distance_m'],
                half_fov_deg=self.cfg['camera_half_fov_deg'],
                exclusion_deg=self.cfg['opponent_front_exclusion_deg'])
            if approximate:
                self.log('Capture uses bounded common-time TF fallback')
        except ValueError as exc:
            self.log(f'Capture skipped: {exc}')
            return
        if mono - self.last_report < self.cfg['capture_cooldown_sec'] or stamp <= self.last_report_stamp:
            return
        report = populate_report(TrackerReport(), msg, self.my_id, self.opp_id, dist, orient)
        self.publisher.publish(report)
        self.image_pub.publish(msg)
        self.last_report, self.last_report_stamp = mono, stamp
        path = None
        if self.cfg['save_images']:
            suffix = extension(msg.format)
            path = self.capture_dir / (
                f'capture_my{self.my_id}_opp{self.opp_id}_'
                f'{msg.header.stamp.sec}_{msg.header.stamp.nanosec:09d}.{suffix}'
            )
            tmp = path.with_name(path.name + '.tmp')
            try:
                tmp.write_bytes(bytes(msg.data))
                tmp.replace(path)
            except OSError as exc:
                self.get_logger().error(f'Report published but image file could not be saved: {exc}')
        self.get_logger().info(
            f'CAPTURE REPORT PUBLISHED: {len(msg.data)} bytes, '
            f'distance={dist:.3f}m, rel_yaw={report.rel_orient:.1f}deg, '
            f'file={path}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = CaptureReport()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
