# Sensor contract

Required sensors: `joint_state`, `imu`.

Read the public HIM kit's `/safety/policy_observation` (`RobotFeedback`) and `/safety/policy_state` (JSON in `std_msgs/String`). Joint arrays follow `vendor/him/hardware_constants.py`'s exact 29-slot order, in radians and radians/second. Quaternion uses `w,x,y,z`; gyro is pelvis/body-frame radians/second. No image, lidar, external object state or global translation is consumed.

The ROS adapter updates at 50 Hz, uses the checker-issued session ID and current observation ID, and increments sequence for every publication. Feedback and IMU JSON must both have been received within 0.12 s; otherwise an active controller stops publishing. `/safety/abort` latches a permanent stop for the process. The host's own freshness/deadline checks remain enabled.

Quaternion/gyro alignment, calibration, latency and source integrity must be qualified by the hardware runner. The adapter uses the kit's standard timestamped feeds and does not claim a real sensor test. A tipped initial pose triggers a damped hold (zero proportional gains in the policy proposal); the host owns effective gains and all motor output.
