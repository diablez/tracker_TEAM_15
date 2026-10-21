"""Team 15 TF-based pursuit target publisher.

Milestone: read robot poses and publish a calculated goal.
This node does not command robot movement.
"""

from math import atan2, cos, hypot, sin

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener
from tf2_ros import TransformException  # pyright: ignore[reportAttributeAccessIssue]
from .geometry import Pose2D, desired_pose_behind


def transform_to_pose2d(transform):
    """Extract planar x, y and yaw from a TF transform."""
    position = transform.transform.translation
    q = transform.transform.rotation

    yaw = atan2(
        2.0 * (q.w * q.z + q.x * q.y),
        1.0 - 2.0 * (q.y * q.y + q.z * q.z),
    )

    return Pose2D(position.x, position.y, yaw)


class TrackerNode(Node):
    def __init__(self):
        super().__init__("tracker_node")

        # Robot frame names are configurable.

        self.global_frame = (
            self.declare_parameter("global_frame", "map")
            .get_parameter_value()
            .string_value
        )

        self.chaser_frame = (
            self.declare_parameter("chaser_frame", "tb3_0/base_footprint")
            .get_parameter_value()
            .string_value
        )

        self.opponent_frame = (
            self.declare_parameter("opponent_frame", "tb3_1/base_footprint")
            .get_parameter_value()
            .string_value
        )

        # Store incoming coordinate transforms.
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Publish the target for inspection in ROS 2.
        self.goal_publisher = self.create_publisher(
            PoseStamped, "/tracker/desired_pose", 10
        )

        # Recalculate once per second.
        self.timer = self.create_timer(1.0, self.update_target)

        self.get_logger().info("Team 15 TF tracker initialized")

    def update_target(self):
        try:
            # Time() requests the latest available transforms.
            chaser_tf = self.tf_buffer.lookup_transform(
                self.global_frame,
                self.chaser_frame,
                Time(),
            )

            opponent_tf = self.tf_buffer.lookup_transform(
                self.global_frame,
                self.opponent_frame,
                Time(),
            )

        except TransformException as error:
            self.get_logger().warn(f"Waiting for robot TF: {error}")
            return

        chaser = transform_to_pose2d(chaser_tf)
        opponent = transform_to_pose2d(opponent_tf)

        # Use our previously tested pursuit geometry.
        target = desired_pose_behind(opponent, offset_m=0.5)

        message = PoseStamped()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = self.global_frame

        message.pose.position.x = target.x
        message.pose.position.y = target.y

        # Convert planar yaw into a ROS quaternion.
        message.pose.orientation.z = sin(target.yaw / 2.0)
        message.pose.orientation.w = cos(target.yaw / 2.0)

        self.goal_publisher.publish(message)

        distance = hypot(
            opponent.x - chaser.x,
            opponent.y - chaser.y,
        )

        self.get_logger().info(
            f"Opponent distance: {distance:.2f} m | "
            f"Goal: ({target.x:.2f}, {target.y:.2f})"
        )


def main(args=None):
    rclpy.init(args=args)
    node = TrackerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
