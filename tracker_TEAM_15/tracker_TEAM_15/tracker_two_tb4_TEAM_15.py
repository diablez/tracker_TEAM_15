#!/usr/bin/env python3

import math
import re

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.time import Time
from rclpy.qos import qos_profile_sensor_data

from nav2_msgs.action import NavigateToPose
from geometry_msgs.msg import TransformStamped
from sensor_msgs.msg import CompressedImage
from tf2_ros import Buffer, TransformListener, TransformBroadcaster
from tf_transformations import euler_from_quaternion, quaternion_from_euler

from tracker_interfaces_team_15.msg import TrackerReport


class TrackerTwoTB4(Node):

    def __init__(self):
        super().__init__('tracker_two_tb4_TEAM_15')

        self.declare_parameter('chaser', 'tb402')
        self.declare_parameter('enemy', 'tb407')
        self.declare_parameter('global_frame', 'map')

        self.chaser = self.get_parameter('chaser').value
        self.enemy = self.get_parameter('enemy').value
        self.global_frame = self.get_parameter('global_frame').value

        self.my_id = self.robot_id_from_name(self.chaser)
        self.opp_id = self.robot_id_from_name(self.enemy)

        self.chaser_base = f'{self.chaser}/base_link'
        self.enemy_base = f'{self.enemy}/base_link'

        self.enemy_offset = 0.5

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.tf_broadcaster = TransformBroadcaster(self)

        self.nav_client = ActionClient(
            self,
            NavigateToPose,
            f'/{self.chaser}/navigate_to_pose'
        )

        self.report_pub = self.create_publisher(
            TrackerReport,
            f'/{self.chaser}/tracker_report',
            10
        )

        self.last_goal_x = None
        self.last_goal_y = None
        self.last_goal_yaw = None

        self.last_report_time = self.get_clock().now()

        # TurtleBot4 OAK-D compressed RGB camera.
        # Construct currently has no publisher on this topic, but
        # the same code can run unchanged on the real TurtleBot4.
        self.camera_topic = (
            f'/{self.chaser}/oakd/rgb/preview/image_raw/compressed'
        )

        self.latest_image = None
        self.camera_received_logged = False

        # The Construct TB3 simulation has no camera publisher.
        # Real TurtleBot4 operation must have a valid image before
        # a capture report is sent.
        self.allow_empty_image = self.chaser.startswith('tb3_')

        self.camera_sub = self.create_subscription(
            CompressedImage,
            self.camera_topic,
            self.tracker_image_callback,
            qos_profile_sensor_data
        )

        # Required separate image topic for visualisation/RViz.
        self.report_image_pub = self.create_publisher(
            CompressedImage,
            f'/{self.chaser}/tracker_report_img/compressed',
            10
        )

        self.get_logger().info(
            f'Camera subscription: {self.camera_topic}'
        )

        self.timer = self.create_timer(0.5, self.update_goal)

        self.get_logger().info(
            f'TEAM 15 tracker started: '
            f'chaser={self.chaser}, enemy={self.enemy}'
        )

    @staticmethod
    def robot_id_from_name(robot_name):
        match = re.search(r'(\d)$', robot_name)

        if match:
            return int(match.group(1))

        return 0

    def tracker_image_callback(self, msg):
        self.latest_image = msg

        if not self.camera_received_logged:
            self.get_logger().info(
                'Compressed camera image received'
            )
            self.camera_received_logged = True

    @staticmethod
    def angle_difference(a, b):
        return math.atan2(
            math.sin(a - b),
            math.cos(a - b)
        )

    @staticmethod
    def yaw_from_transform(transform):
        q = transform.transform.rotation

        _, _, yaw = euler_from_quaternion([
            q.x,
            q.y,
            q.z,
            q.w
        ])

        return yaw

    def update_goal(self):

        try:
            enemy_tf = self.tf_buffer.lookup_transform(
                self.global_frame,
                self.enemy_base,
                Time()
            )

            chaser_tf = self.tf_buffer.lookup_transform(
                self.global_frame,
                self.chaser_base,
                Time()
            )

        except Exception as e:
            self.get_logger().warn(f'TF unavailable: {e}')
            return

        enemy_x = enemy_tf.transform.translation.x
        enemy_y = enemy_tf.transform.translation.y
        enemy_yaw = self.yaw_from_transform(enemy_tf)

        chaser_x = chaser_tf.transform.translation.x
        chaser_y = chaser_tf.transform.translation.y
        chaser_yaw = self.yaw_from_transform(chaser_tf)

        # ---------------------------------------------------------
        # RELATIVE MEASUREMENTS
        # ---------------------------------------------------------

        rel_dist = math.hypot(
            enemy_x - chaser_x,
            enemy_y - chaser_y
        )

        rel_orient = math.degrees(
            self.angle_difference(enemy_yaw, chaser_yaw)
        )

        # ---------------------------------------------------------
        # CAPTURE / OPERATING-ZONE GEOMETRY
        # ---------------------------------------------------------

        # Position of the chaser around the opponent, expressed
        # relative to the opponent's forward direction.
        enemy_to_chaser_bearing = math.atan2(
            chaser_y - enemy_y,
            chaser_x - enemy_x
        )

        safe_zone_angle = abs(math.degrees(
            self.angle_difference(
                enemy_to_chaser_bearing,
                enemy_yaw
            )
        ))

        # Opponent camera: 80 deg HFOV = +/-40 deg.
        # Add the specified 30 deg safety buffer to either side.
        # Therefore the chaser must be outside +/-70 deg.
        in_operating_zone = safe_zone_angle >= 70.0

        # Also confirm the opponent is inside the chaser's
        # own 80 deg camera field of view.
        chaser_to_enemy_bearing = math.atan2(
            enemy_y - chaser_y,
            enemy_x - chaser_x
        )

        camera_angle = abs(math.degrees(
            self.angle_difference(
                chaser_to_enemy_bearing,
                chaser_yaw
            )
        ))

        opponent_in_camera = camera_angle <= 40.0

        # ---------------------------------------------------------
        # TRACKING GOAL
        # ---------------------------------------------------------

        goal_x = enemy_x - self.enemy_offset * math.cos(enemy_yaw)
        goal_y = enemy_y - self.enemy_offset * math.sin(enemy_yaw)
        goal_yaw = enemy_yaw

        self.broadcast_goal_frame(
            goal_x,
            goal_y,
            goal_yaw
        )

        # ---------------------------------------------------------
        # REPORTING TEST
        # ---------------------------------------------------------
        # In simulation, publish when the chaser is reasonably close
        # to the intended 0.5 m tracking distance.
        # 5 second cooldown matches the game hit cooldown.
        # ---------------------------------------------------------

        elapsed = (
            self.get_clock().now() - self.last_report_time
        ).nanoseconds / 1e9

        image_ready = (
            self.latest_image is not None
            or self.allow_empty_image
        )

        if (
            0.40 <= rel_dist <= 0.60
            and in_operating_zone
            and opponent_in_camera
            and image_ready
            and elapsed >= 5.0
        ):
            self.publish_report(rel_dist, rel_orient)
            self.last_report_time = self.get_clock().now()

        # ---------------------------------------------------------
        # NAV2 GOAL UPDATE
        # ---------------------------------------------------------

        if self.last_goal_x is not None:

            goal_move = math.hypot(
                goal_x - self.last_goal_x,
                goal_y - self.last_goal_y
            )

            goal_turn = abs(
                self.angle_difference(
                    goal_yaw,
                    self.last_goal_yaw
                )
            )

            if (
                goal_move < 0.10 and
                goal_turn < math.radians(8.0)
            ):
                return

        if self.send_goal(goal_x, goal_y, goal_yaw):

            self.last_goal_x = goal_x
            self.last_goal_y = goal_y
            self.last_goal_yaw = goal_yaw

    def publish_report(self, rel_dist, rel_orient):

        msg = TrackerReport()

        msg.my_id = int(self.my_id)
        msg.opp_id = int(self.opp_id)

        if self.latest_image is not None:
            msg.image = self.latest_image
            image_status = 'YES'
        else:
            # Construct simulation has no camera publisher.
            msg.image = CompressedImage()
            image_status = 'NO'

        msg.rel_dist = float(rel_dist)
        msg.rel_orient = float(rel_orient)

        self.report_pub.publish(msg)

        # Publish the same captured image separately as required
        # by the lecturer template for RViz/image visualisation.
        if self.latest_image is not None:
            self.report_image_pub.publish(self.latest_image)

        self.get_logger().info(
            f'Report published: '
            f'my_id={self.my_id}, '
            f'opp_id={self.opp_id}, '
            f'distance={rel_dist:.2f} m, '
            f'orientation={rel_orient:.1f} deg, '
            f'image={image_status}'
        )

    def broadcast_goal_frame(self, x, y, yaw):

        transform = TransformStamped()

        transform.header.stamp = \
            self.get_clock().now().to_msg()

        transform.header.frame_id = \
            self.global_frame

        transform.child_frame_id = \
            'TEAM_15_tracking_goal'

        transform.transform.translation.x = x
        transform.transform.translation.y = y
        transform.transform.translation.z = 0.0

        q = quaternion_from_euler(
            0.0,
            0.0,
            yaw
        )

        transform.transform.rotation.x = q[0]
        transform.transform.rotation.y = q[1]
        transform.transform.rotation.z = q[2]
        transform.transform.rotation.w = q[3]

        self.tf_broadcaster.sendTransform(transform)

    def send_goal(self, x, y, yaw):

        if not self.nav_client.wait_for_server(
            timeout_sec=0.2
        ):
            self.get_logger().warn(
                'Nav2 action server unavailable'
            )
            return False

        goal = NavigateToPose.Goal()

        goal.pose.header.frame_id = \
            self.global_frame

        goal.pose.header.stamp = \
            self.get_clock().now().to_msg()

        goal.pose.pose.position.x = x
        goal.pose.pose.position.y = y
        goal.pose.pose.position.z = 0.0

        q = quaternion_from_euler(
            0.0,
            0.0,
            yaw
        )

        goal.pose.pose.orientation.x = q[0]
        goal.pose.pose.orientation.y = q[1]
        goal.pose.pose.orientation.z = q[2]
        goal.pose.pose.orientation.w = q[3]

        self.get_logger().info(
            f'New tracking goal: '
            f'x={x:.2f}, y={y:.2f}, '
            f'yaw={math.degrees(yaw):.1f} deg'
        )

        future = self.nav_client.send_goal_async(goal)
        future.add_done_callback(
            self.goal_response_callback
        )

        return True

    def goal_response_callback(self, future):

        try:
            goal_handle = future.result()

        except Exception as e:
            self.get_logger().error(
                f'Goal request failed: {e}'
            )
            return

        if goal_handle.accepted:
            self.get_logger().info(
                'Tracking goal accepted'
            )
        else:
            self.get_logger().warn(
                'Tracking goal rejected'
            )


def main(args=None):

    rclpy.init(args=args)

    node = TrackerTwoTB4()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    node.destroy_node()

    if rclpy.ok():
        rclpy.shutdown()


if __name__ == '__main__':
    main()
