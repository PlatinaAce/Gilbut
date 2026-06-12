#!/usr/bin/env python
# filepath: /home/viplab/catkin_ws/src/motion_planning_control/ros_navigation_project/src/navigation_stack/scripts/check_path_planning.py

import rospy
from nav_msgs.msg import Path, Odometry
from geometry_msgs.msg import PoseStamped
from move_base_msgs.msg import MoveBaseActionGoal
from actionlib_msgs.msg import GoalStatusArray
import sys

class PathPlanningChecker:
    def __init__(self):
        rospy.init_node('path_planning_checker', anonymous=True)
        
        self.goal_received = False
        self.global_plan_received = False
        self.local_plan_received = False
        self.current_position = None
        self.goal_position = None
        self.global_plan_length = 0
        self.local_plan_length = 0
        self.move_base_status = None
        
        # Subscribers
        rospy.Subscriber('/move_base_simple/goal', PoseStamped, self.goal_cb)
        rospy.Subscriber('/move_base/goal', MoveBaseActionGoal, self.action_goal_cb)
        rospy.Subscriber('/move_base/status', GoalStatusArray, self.status_cb)
        rospy.Subscriber('/move_base/GlobalPlanner/plan', Path, self.global_plan_cb)
        rospy.Subscriber('/move_base/DWAPlannerROS/global_plan', Path, self.dwa_global_plan_cb)
        rospy.Subscriber('/move_base/DWAPlannerROS/local_plan', Path, self.local_plan_cb)
        rospy.Subscriber('/carla/ego_vehicle/odometry', Odometry, self.odom_cb)
        
        rospy.loginfo("="*60)
        rospy.loginfo("PATH PLANNING CHECKER STARTED")
        rospy.loginfo("="*60)
        rospy.loginfo("Waiting for data... Set a goal in RViz using 2D Nav Goal")
        rospy.loginfo("="*60)
        
    def goal_cb(self, msg):
        self.goal_received = True
        self.goal_position = msg.pose.position
        rospy.loginfo("\n" + "="*60)
        rospy.loginfo("✓ GOAL RECEIVED")
        rospy.loginfo("  Frame: {}".format(msg.header.frame_id))
        rospy.loginfo("  Position: x={:.2f}, y={:.2f}, z={:.2f}".format(
            msg.pose.position.x, msg.pose.position.y, msg.pose.position.z))
        if self.current_position:
            distance = ((msg.pose.position.x - self.current_position.x)**2 + 
                       (msg.pose.position.y - self.current_position.y)**2)**0.5
            rospy.loginfo("  Distance from robot: {:.2f}m".format(distance))
        rospy.loginfo("="*60)
    
    def action_goal_cb(self, msg):
        rospy.loginfo("✓ Move Base Action Goal received")
    
    def status_cb(self, msg):
        if msg.status_list:
            status = msg.status_list[-1].status
            text = msg.status_list[-1].text
            
            status_names = {
                0: "PENDING",
                1: "ACTIVE",
                2: "PREEMPTED",
                3: "SUCCEEDED",
                4: "ABORTED",
                5: "REJECTED",
                6: "PREEMPTING",
                7: "RECALLING",
                8: "RECALLED",
                9: "LOST"
            }
            
            if self.move_base_status != status:
                self.move_base_status = status
                rospy.loginfo("\n" + "-"*60)
                rospy.loginfo("MOVE BASE STATUS: {} ({})".format(
                    status_names.get(status, "UNKNOWN"), status))
                if text:
                    rospy.loginfo("  Message: {}".format(text))
                rospy.loginfo("-"*60)
                
                if status == 4:  # ABORTED
                    rospy.logerr("⚠ PATH PLANNING FAILED!")
                    rospy.logerr("  Possible reasons:")
                    rospy.logerr("  - Goal is in obstacle")
                    rospy.logerr("  - Goal is out of map bounds")
                    rospy.logerr("  - No valid path exists")
                    rospy.logerr("  - TF transform failed")
    
    def global_plan_cb(self, msg):
        if len(msg.poses) > 0:
            if not self.global_plan_received or len(msg.poses) != self.global_plan_length:
                self.global_plan_received = True
                self.global_plan_length = len(msg.poses)
                rospy.loginfo("\n" + "="*60)
                rospy.loginfo("✓ GLOBAL PLAN GENERATED (GlobalPlanner)")
                rospy.loginfo("  Waypoints: {}".format(len(msg.poses)))
                rospy.loginfo("  First point: x={:.2f}, y={:.2f}".format(
                    msg.poses[0].pose.position.x, msg.poses[0].pose.position.y))
                rospy.loginfo("  Last point: x={:.2f}, y={:.2f}".format(
                    msg.poses[-1].pose.position.x, msg.poses[-1].pose.position.y))
                
                # 경로 길이 계산
                total_distance = 0.0
                for i in range(1, len(msg.poses)):
                    dx = msg.poses[i].pose.position.x - msg.poses[i-1].pose.position.x
                    dy = msg.poses[i].pose.position.y - msg.poses[i-1].pose.position.y
                    total_distance += (dx**2 + dy**2)**0.5
                rospy.loginfo("  Total path length: {:.2f}m".format(total_distance))
                rospy.loginfo("="*60)
    
    def dwa_global_plan_cb(self, msg):
        if len(msg.poses) > 0:
            rospy.loginfo_once("✓ DWA received global plan: {} waypoints".format(len(msg.poses)))
    
    def local_plan_cb(self, msg):
        if len(msg.poses) > 0:
            if not self.local_plan_received:
                self.local_plan_received = True
                rospy.loginfo("\n" + "="*60)
                rospy.loginfo("✓ LOCAL PLAN GENERATED (DWA)")
                rospy.loginfo("  Waypoints: {}".format(len(msg.poses)))
                rospy.loginfo("="*60)
    
    def odom_cb(self, msg):
        self.current_position = msg.pose.pose.position
    
    def run(self):
        rate = rospy.Rate(0.5)  # 2초마다
        last_check_time = rospy.Time.now()
        
        while not rospy.is_shutdown():
            # 5초마다 상태 요약
            if (rospy.Time.now() - last_check_time).to_sec() > 5.0:
                if self.goal_received:
                    rospy.loginfo("\n" + "="*60)
                    rospy.loginfo("STATUS SUMMARY")
                    rospy.loginfo("="*60)
                    rospy.loginfo("Goal received: ✓")
                    rospy.loginfo("Global plan: {}".format("✓ ({} points)".format(self.global_plan_length) if self.global_plan_received else "✗ NOT GENERATED"))
                    rospy.loginfo("Local plan: {}".format("✓" if self.local_plan_received else "✗"))
                    if self.current_position and self.goal_position:
                        distance = ((self.goal_position.x - self.current_position.x)**2 + 
                                   (self.goal_position.y - self.current_position.y)**2)**0.5
                        rospy.loginfo("Distance to goal: {:.2f}m".format(distance))
                    rospy.loginfo("="*60 + "\n")
                    
                    # 경로가 생성되지 않았다면 문제 진단
                    if not self.global_plan_received:
                        rospy.logwarn("\n⚠ GLOBAL PLAN NOT GENERATED!")
                        rospy.logwarn("Checking possible issues...")
                        self.diagnose_issues()
                
                last_check_time = rospy.Time.now()
            
            rate.sleep()
    
    def diagnose_issues(self):
        import tf
        
        # TF 확인
        try:
            listener = tf.TransformListener()
            rospy.sleep(1.0)
            listener.lookupTransform('/map', '/ego_vehicle', rospy.Time(0))
            rospy.loginfo("  ✓ TF transform available: map -> ego_vehicle")
        except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException) as e:
            rospy.logerr("  ✗ TF transform FAILED: {}".format(e))
            rospy.logerr("    → This is likely the problem!")
        
        # Costmap 확인
        try:
            rospy.wait_for_message('/move_base/global_costmap/costmap', rospy.AnyMsg, timeout=2.0)
            rospy.loginfo("  ✓ Global costmap is being published")
        except:
            rospy.logerr("  ✗ Global costmap NOT being published")
        
        # Move Base 파라미터 확인
        try:
            planner = rospy.get_param('/move_base/base_global_planner')
            rospy.loginfo("  ✓ Global planner: {}".format(planner))
        except:
            rospy.logerr("  ✗ Cannot get global planner parameter")

if __name__ == '__main__':
    try:
        checker = PathPlanningChecker()
        checker.run()
    except rospy.ROSInterruptException:
        pass