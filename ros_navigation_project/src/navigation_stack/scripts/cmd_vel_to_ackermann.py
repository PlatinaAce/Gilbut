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
        self.max_steer_angle = rospy.get_param('~max_steer_angle', 0.7)  # 증가
        
        # 속도 제어 파라미터
        self.max_speed = 15.0  # m/s (54 km/h)
        self.min_throttle = 0.15  # 최소 throttle
        self.brake_threshold = 0.1  # 브레이크 활성화 임계값
        
        # Publishers and Subscribers - cmd_vel 토픽 수정
        self.ackermann_pub = rospy.Publisher('/carla/ego_vehicle/vehicle_control_cmd', 
                                            CarlaEgoVehicleControl, queue_size=1)
        self.cmd_vel_sub = rospy.Subscriber('/cmd_vel',  # move_base 출력 토픽
                                           Twist, self.cmd_vel_callback)
        
        rospy.loginfo("CMD_VEL to Ackermann converter initialized")
        rospy.loginfo("Subscribing to: /cmd_vel")
        rospy.loginfo("Publishing to: /carla/ego_vehicle/vehicle_control_cmd")
        
    def cmd_vel_callback(self, msg):
        ackermann_msg = CarlaEgoVehicleControl()
        
        # Convert linear velocity to throttle/brake
        linear_vel = msg.linear.x
        
        # 음수 속도는 절대값으로 변환 (항상 전진)
        speed = abs(linear_vel)
        
        # 매우 작은 속도는 정지로 간주 (3cm/s 미만)
        if speed < 0.03:
            ackermann_msg.throttle = 0.0
            ackermann_msg.brake = 1.0  # 강한 브레이크로 완전 정지
            ackermann_msg.reverse = False
            ackermann_msg.steer = 0.0  # 조향도 중립
            
        # 저속: 0.03 m/s 이상은 모두 움직임
        else:
            # 속도에 비례하는 throttle (최소 0.3, 최대 1.0)
            throttle_raw = speed / self.max_speed
            ackermann_msg.throttle = min(max(throttle_raw * 2.0, 0.3), 1.0)  # 최소 0.3
            ackermann_msg.brake = 0.0
            ackermann_msg.reverse = False
            
            # 조향각 계산
            if speed > 0.05:  # 5cm/s 이상일 때만 정상 조향
                steering_angle = math.atan(self.wheelbase * msg.angular.z / speed)
                ackermann_msg.steer = max(min(steering_angle / self.max_steer_angle, 1.0), -1.0)
            else:  # 매우 저속일 때는 각속도 기반
                ackermann_msg.steer = max(min(msg.angular.z * 0.5, 1.0), -1.0)
        
        ackermann_msg.hand_brake = False
        ackermann_msg.manual_gear_shift = False
        ackermann_msg.gear = 0
        
        self.ackermann_pub.publish(ackermann_msg)
        
        # 디버그 로깅 (더 자주)
        if rospy.get_time() % 1 < 0.1:  # 1초마다 로깅
            rospy.loginfo(f"CMD: vel={linear_vel:.2f} → throttle={ackermann_msg.throttle:.2f}, brake={ackermann_msg.brake:.2f}, steer={ackermann_msg.steer:.2f}")
    
    def run(self):
        rospy.spin()

if __name__ == '__main__':
    try:
        node = CmdVelToAckermann()
        node.run()
    except rospy.ROSInterruptException:
        pass