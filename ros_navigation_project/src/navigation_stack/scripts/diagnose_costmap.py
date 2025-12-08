#!/usr/bin/env python
# filepath: /home/viplab/catkin_ws/src/motion_planning_control/ros_navigation_project/src/navigation_stack/scripts/diagnose_costmap.py

import rospy
from nav_msgs.msg import OccupancyGrid
import sys

class CostmapDiagnostic:
    def __init__(self):
        rospy.init_node('costmap_diagnostic')
        
        self.map_received = False
        self.global_costmap_received = False
        self.local_costmap_received = False
        
        rospy.Subscriber('/map', OccupancyGrid, self.map_cb)
        rospy.Subscriber('/move_base/global_costmap/costmap', OccupancyGrid, self.global_costmap_cb)
        rospy.Subscriber('/move_base/local_costmap/costmap', OccupancyGrid, self.local_costmap_cb)
        
        rospy.loginfo("Waiting for costmap data...")
        rospy.sleep(3.0)
        
        self.print_status()
    
    def map_cb(self, msg):
        if not self.map_received:
            self.map_received = True
            rospy.loginfo("✓ MAP RECEIVED")
            rospy.loginfo("  Size: {}x{} cells".format(msg.info.width, msg.info.height))
            rospy.loginfo("  Resolution: {}m/cell".format(msg.info.resolution))
            rospy.loginfo("  Origin: x={}, y={}".format(msg.info.origin.position.x, msg.info.origin.position.y))
            
            # 빈 맵인지 확인
            occupied_count = sum(1 for cell in msg.data if cell > 50)
            free_count = sum(1 for cell in msg.data if cell == 0)
            unknown_count = sum(1 for cell in msg.data if cell < 0)
            
            rospy.loginfo("  Occupied cells: {}".format(occupied_count))
            rospy.loginfo("  Free cells: {}".format(free_count))
            rospy.loginfo("  Unknown cells: {}".format(unknown_count))
    
    def global_costmap_cb(self, msg):
        if not self.global_costmap_received:
            self.global_costmap_received = True
            rospy.loginfo("✓ GLOBAL COSTMAP RECEIVED")
            rospy.loginfo("  Size: {}x{} cells".format(msg.info.width, msg.info.height))
            rospy.loginfo("  Resolution: {}m/cell".format(msg.info.resolution))
            rospy.loginfo("  Frame: {}".format(msg.header.frame_id))
    
    def local_costmap_cb(self, msg):
        if not self.local_costmap_received:
            self.local_costmap_received = True
            rospy.loginfo("✓ LOCAL COSTMAP RECEIVED")
            rospy.loginfo("  Size: {}x{} cells".format(msg.info.width, msg.info.height))
            rospy.loginfo("  Resolution: {}m/cell".format(msg.info.resolution))
            rospy.loginfo("  Frame: {}".format(msg.header.frame_id))
    
    def print_status(self):
        rospy.loginfo("\n" + "="*60)
        rospy.loginfo("COSTMAP STATUS")
        rospy.loginfo("="*60)
        rospy.loginfo("Static Map:      {}".format("✓" if self.map_received else "✗ NOT RECEIVED"))
        rospy.loginfo("Global Costmap:  {}".format("✓" if self.global_costmap_received else "✗ NOT RECEIVED"))
        rospy.loginfo("Local Costmap:   {}".format("✓" if self.local_costmap_received else "✗ NOT RECEIVED"))
        rospy.loginfo("="*60 + "\n")
        
        if not self.map_received:
            rospy.logerr("Map Server is not publishing! Check:")
            rospy.logerr("  1. Map file exists")
            rospy.logerr("  2. Map Server node is running: rosnode info /map_server")
        
        if not self.global_costmap_received:
            rospy.logerr("Global Costmap is not publishing! This prevents path planning.")

if __name__ == '__main__':
    try:
        diag = CostmapDiagnostic()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass