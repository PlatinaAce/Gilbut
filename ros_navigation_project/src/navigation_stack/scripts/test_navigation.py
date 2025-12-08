#!/usr/bin/env python

import rospy
import actionlib
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal, MoveBaseActionResult
from actionlib_msgs.msg import GoalStatus
import tf.transformations as tf_trans

class NavigationTester:
    def __init__(self):
        rospy.init_node('navigation_tester')
        
        # Move Base Action Client
        self.client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
        rospy.loginfo("Waiting for move_base action server...")
        self.client.wait_for_server()
        rospy.loginfo("Connected to move_base server")
        
        # Status subscriber
        self.status_sub = rospy.Subscriber('/move_base/status', 
                                          GoalStatus, 
                                          self.status_callback)
        
    def status_callback(self, msg):
        if msg.status == GoalStatus.ACTIVE:
            rospy.loginfo("Goal is being processed")
        elif msg.status == GoalStatus.SUCCEEDED:
            rospy.loginfo("✓ Goal reached successfully!")
        elif msg.status == GoalStatus.ABORTED:
            rospy.logwarn("✗ Goal was aborted")
        elif msg.status == GoalStatus.REJECTED:
            rospy.logwarn("✗ Goal was rejected")
    
    def send_goal(self, x, y, yaw=0.0):
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = "map"
        goal.target_pose.header.stamp = rospy.Time.now()
        
        # 위치
        goal.target_pose.pose.position.x = x
        goal.target_pose.pose.position.y = y
        goal.target_pose.pose.position.z = 0.0
        
        # 방향 (quaternion)
        quaternion = tf_trans.quaternion_from_euler(0, 0, yaw)
        goal.target_pose.pose.orientation.x = quaternion[0]
        goal.target_pose.pose.orientation.y = quaternion[1]
        goal.target_pose.pose.orientation.z = quaternion[2]
        goal.target_pose.pose.orientation.w = quaternion[3]
        
        rospy.loginfo(f"Sending goal: x={x}, y={y}, yaw={yaw}")
        self.client.send_goal(goal, done_cb=self.done_callback, 
                            feedback_cb=self.feedback_callback)
        
        # 결과 대기
        self.client.wait_for_result()
        
        return self.client.get_state()
    
    def done_callback(self, status, result):
        if status == GoalStatus.SUCCEEDED:
            rospy.loginfo("🎉 Navigation completed successfully!")
        else:
            rospy.logwarn(f"Navigation failed with status: {status}")
    
    def feedback_callback(self, feedback):
        current_pose = feedback.base_position.pose
        rospy.loginfo_throttle(2.0, f"Current position: x={current_pose.position.x:.2f}, y={current_pose.position.y:.2f}")

if __name__ == '__main__':
    try:
        tester = NavigationTester()
        
        # 테스트 목표 지점 (맵 좌표계 기준)
        rospy.loginfo("Sending test goal...")
        result = tester.send_goal(x=10.0, y=5.0, yaw=0.0)
        
        if result == GoalStatus.SUCCEEDED:
            rospy.loginfo("Test passed!")
        else:
            rospy.logwarn("Test failed!")
            
    except rospy.ROSInterruptException:
        pass