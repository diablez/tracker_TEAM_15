#!/usr/bin/env python3
"""TF-based TurtleBot3 pursuit through the existing namespaced Nav2 action."""

import math
import time

import rclpy
from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener


def yaw_from_quaternion(q):
    """Return yaw in radians without a tf_transformations dependency."""
    return math.atan2(
        2.0 * (q.w * q.z + q.x * q.y),
        1.0 - 2.0 * (q.y * q.y + q.z * q.z),
    )


def angle_error(a, b):
    return math.atan2(math.sin(a - b), math.cos(a - b))


class TrackerTB3Sim(Node):
    def __init__(self):
        super().__init__('tracker_tb3_sim_TEAM_15')

        self.declare_parameter('chaser', 'tb3_0')
        self.declare_parameter('enemy', 'tb3_1')
        self.declare_parameter('global_frame', 'map')
        self.declare_parameter('chaser_frame', '')
        self.declare_parameter('enemy_frame', '')
        self.declare_parameter('goal_offset', 0.5)
        self.declare_parameter('dry_run', True)
        self.declare_parameter('min_goal_interval', 1.5)
        self.declare_parameter('max_tf_age', 2.5)

        chaser = self.get_parameter('chaser').value.strip('/')
        enemy = self.get_parameter('enemy').value.strip('/')
        self.global_frame = self.get_parameter('global_frame').value.lstrip('/')
        self.chaser_frame = (
            self.get_parameter('chaser_frame').value
            or f'{chaser}/base_link'
        ).lstrip('/')
        self.enemy_frame = (
            self.get_parameter('enemy_frame').value
            or f'{enemy}/base_link'
        ).lstrip('/')
        self.goal_offset = float(self.get_parameter('goal_offset').value)
        self.dry_run = bool(self.get_parameter('dry_run').value)
        self.min_goal_interval = float(self.get_parameter('min_goal_interval').value)
        self.max_tf_age = float(self.get_parameter('max_tf_age').value)

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.nav_client = ActionClient(
            self, NavigateToPose, f'/{chaser}/navigate_to_pose'
        )

        self.last_goal = None
        self.pending_goal = None
        self.request_pending = False
        self.active_goal_handle = None
        self.last_attempt_monotonic = -float('inf')
        self.last_diagnostic_monotonic = -float('inf')
        self.create_timer(0.5, self.update)

        self.get_logger().info(
            f'TB3 sim pursuit: {chaser} -> {enemy}; '
            f'frames {self.global_frame} -> '
            f'{self.chaser_frame}, {self.enemy_frame}; '
            f'dry_run={self.dry_run}'
        )

    def diagnostic(self, message):
        now = time.monotonic()
        if now - self.last_diagnostic_monotonic >= 5.0:
            self.get_logger().warn(message)
            self.last_diagnostic_monotonic = now

    def update(self):
        now_ros = self.get_clock().now()
        if now_ros.nanoseconds == 0:
            self.diagnostic('Waiting for /clock (use_sim_time=true)')
            return

        try:
            target_tf = self.tf_buffer.lookup_transform(
                self.global_frame, self.enemy_frame, Time()
            )
            chaser_tf = self.tf_buffer.lookup_transform(
                self.global_frame, self.chaser_frame, Time()
            )
        except Exception as exc:
            self.diagnostic(f'TF unavailable: {exc}')
            return

        for name, transform in [('target', target_tf), ('chaser', chaser_tf)]:
            age = (now_ros - Time.from_msg(transform.header.stamp)).nanoseconds / 1e9
            if not math.isfinite(age) or age < -0.25 or age > self.max_tf_age:
                self.diagnostic(f'{name} TF stale ({age:.1f}s): skipping update')
                return

        tx = target_tf.transform.translation.x
        ty = target_tf.transform.translation.y
        yaw = yaw_from_quaternion(target_tf.transform.rotation)
        gx = tx - self.goal_offset * math.cos(yaw)
        gy = ty - self.goal_offset * math.sin(yaw)
        desired = (gx, gy, yaw)

        if self.dry_run:
            self.diagnostic(
                f'DRY RUN: would send goal x={gx:.2f}, y={gy:.2f}, '
                f'yaw={math.degrees(yaw):.0f}deg'
            )
            return

        if self.request_pending:
            return

        if self.last_goal is not None:
            lx, ly, lyaw = self.last_goal
            if (math.hypot(gx - lx, gy - ly) < 0.15
                    and abs(angle_error(yaw, lyaw)) < math.radians(10.0)):
                return

        now_monotonic = time.monotonic()
        if now_monotonic - self.last_attempt_monotonic < self.min_goal_interval:
            return
        self.last_attempt_monotonic = now_monotonic

        if not self.nav_client.wait_for_server(timeout_sec=0.1):
            self.diagnostic('Nav2 action unavailable')
            return

        pose = PoseStamped()
        pose.header.frame_id = self.global_frame
        pose.header.stamp = now_ros.to_msg()
        pose.pose.position.x = gx
        pose.pose.position.y = gy
        pose.pose.orientation.z = math.sin(yaw / 2.0)
        pose.pose.orientation.w = math.cos(yaw / 2.0)

        goal = NavigateToPose.Goal()
        goal.pose = pose
        self.pending_goal = desired
        self.request_pending = True
        try:
            future = self.nav_client.send_goal_async(goal)
            future.add_done_callback(self.goal_response)
        except Exception as exc:
            self.request_pending = False
            self.pending_goal = None
            self.get_logger().error(f'Nav2 request failed: {exc}')

    def goal_response(self, future):
        attempted_goal = self.pending_goal
        self.pending_goal = None
        self.request_pending = False
        try:
            handle = future.result()
            if handle is None or not handle.accepted:
                self.diagnostic('Nav2 goal rejected; will retry')
                return
            self.active_goal_handle = handle
            self.last_goal = attempted_goal
            self.get_logger().info(
                f'Nav2 accepted pursuit goal ({attempted_goal[0]:.2f}, '
                f'{attempted_goal[1]:.2f})'
            )
            handle.get_result_async().add_done_callback(
                lambda result_future, h=handle: self.goal_result(result_future, h)
            )
        except Exception as exc:
            self.get_logger().error(f'Nav2 goal response failed: {exc}')

    def goal_result(self, future, handle):
        if handle is not self.active_goal_handle:
            return  # A newer goal has replaced this one.
        self.active_goal_handle = None
        try:
            status = future.result().status
            if status == GoalStatus.STATUS_SUCCEEDED:
                self.get_logger().info('Nav2 pursuit goal succeeded')
            else:
                self.last_goal = None  # Retry if the target is still reachable.
                self.diagnostic(f'Nav2 goal finished with status {status}; retrying')
        except Exception as exc:
            self.last_goal = None
            self.get_logger().error(f'Nav2 result failed: {exc}')


def main(args=None):
    rclpy.init(args=args)
    node = TrackerTB3Sim()
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
