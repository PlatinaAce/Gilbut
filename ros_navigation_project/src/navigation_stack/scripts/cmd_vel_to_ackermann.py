#!/usr/bin/env python

import rospy
import math
from geometry_msgs.msg import Twist
from carla_msgs.msg import CarlaEgoVehicleControl

class CmdVelToAckermann:
    def __init__(self):
        rospy.init_node('cmd_vel_to_ackermann')
        
        # Parameters
        self.wheelbase = rospy.get_param('~wheelbase', 2.85)
        self.max_steer_angle = rospy.get_param('~max_steer_angle', 0.7)
        
        # Publishers and Subscribers
        self.ackermann_pub = rospy.Publisher('/carla/ego_vehicle/vehicle_control_cmd', 
                                            CarlaEgoVehicleControl, queue_size=1)
        self.cmd_vel_sub = rospy.Subscriber('/carla/ego_vehicle/cmd_vel', 
                                           Twist, self.cmd_vel_callback)
        
    def cmd_vel_callback(self, msg):
        ackermann_msg = CarlaEgoVehicleControl()
        
        # Convert linear velocity to throttle/brake
        linear_vel = msg.linear.x
        
        if linear_vel > 0:
            ackermann_msg.throttle = min(linear_vel / 5.0, 1.0)  # Normalize to [0, 1]
            ackermann_msg.brake = 0.0
        elif linear_vel < 0:
            ackermann_msg.throttle = 0.0
            ackermann_msg.brake = min(abs(linear_vel) / 5.0, 1.0)
        else:
            ackermann_msg.throttle = 0.0
            ackermann_msg.brake = 0.0
        
        # Convert angular velocity to steering angle
        # Using bicycle model: tan(delta) = L * omega / v
        if abs(linear_vel) > 0.1:
            steering_angle = math.atan(self.wheelbase * msg.angular.z / linear_vel)
            ackermann_msg.steer = max(min(steering_angle / self.max_steer_angle, 1.0), -1.0)
        else:
            ackermann_msg.steer = 0.0
        
        ackermann_msg.hand_brake = False
        ackermann_msg.reverse = linear_vel < 0
        ackermann_msg.manual_gear_shift = False
        
        self.ackermann_pub.publish(ackermann_msg)
    
    def run(self):
        rospy.spin()

if __name__ == '__main__':
    try:
        node = CmdVelToAckermann()
        node.run()
    except rospy.ROSInterruptException:
        pass