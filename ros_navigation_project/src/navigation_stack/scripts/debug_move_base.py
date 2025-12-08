#!/usr/bin/env python
# filepath: /home/viplab/catkin_ws/src/motion_planning_control/ros_navigation_project/src/navigation_stack/scripts/debug_move_base.py

import rospy
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import OccupancyGrid
import tf

class MoveBaseDebugger:
    def __init__(self):
        rospy.init_node('move_base_debugger')
        
        self.scan_received = False
        self.map_received = False
        
        rospy.Subscriber('/carla/ego_vehicle/lidar/scan', LaserScan, self.scan_cb)
        rospy.Subscriber('/map', OccupancyGrid, self.map_cb)
        
        self.tf_listener = tf.TransformListener()
        
        rospy.sleep(2.0)
        self.check_all()
    
    def scan_cb(self, msg):
        self.scan_received = True
    
    def map_cb(self, msg):
        self.map_received = True
    
    def check_all(self):
        rospy.loginfo("="*60)
        rospy.loginfo("MOVE BASE DEBUG")
        rospy.loginfo("="*60)
        
        # 1. Map 확인
        rospy.loginfo("Map received: {}".format("✓" if self.map_received else "✗"))
        
        # 2. Scan 확인
        rospy.loginfo("LaserScan received: {}".format("✓" if self.scan_received else "✗"))
        
        # 3. TF 확인
        try:
            self.tf_listener.waitForTransform('/map', '/ego_vehicle', rospy.Time(0), rospy.Duration(2.0))
            (trans, rot) = self.tf_listener.lookupTransform('/map', '/ego_vehicle', rospy.Time(0))
            rospy.loginfo("TF map->ego_vehicle: ✓")
            rospy.loginfo("  Position: x={:.2f}, y={:.2f}, z={:.2f}".format(trans[0], trans[1], trans[2]))
        except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException) as e:
            rospy.logerr("TF map->ego_vehicle: ✗")
            rospy.logerr("  Error: {}".format(e))
        
        try:
            self.tf_listener.waitForTransform('/odom', '/ego_vehicle', rospy.Time(0), rospy.Duration(2.0))
            rospy.loginfo("TF odom->ego_vehicle: ✓")
        except:
            rospy.logerr("TF odom->ego_vehicle: ✗")
        
        # 4. Move Base 파라미터 확인
        try:
            global_frame = rospy.get_param('/move_base/global_costmap/global_frame')
            robot_frame = rospy.get_param('/move_base/global_costmap/robot_base_frame')
            rospy.loginfo("Global costmap frames: {} -> {}".format(global_frame, robot_frame))
        except:
            rospy.logerr("Cannot get costmap parameters!")
        
        rospy.loginfo("="*60)

if __name__ == '__main__':
    try:
        debugger = MoveBaseDebugger()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass