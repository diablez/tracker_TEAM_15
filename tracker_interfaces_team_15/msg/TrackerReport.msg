# TEAM15 tracker ID, as distinct uint8 (not a 3-digit robot namespace).
uint8 my_id
# Opponent ID, agreed with competition/referee.
uint8 opp_id
# Original compressed RGB frame acquired by the chaser camera.
sensor_msgs/CompressedImage image
# Planar robot-center separation, metres.
float32 rel_dist
# Relative yaw: opponent yaw minus chaser yaw, wrapped, DEGREES.
# Verify the required angle convention against the official assessment before use.
float32 rel_orient
