cmake_minimum_required(VERSION 3.0.2)
project(navigation_stack)

find_package(catkin REQUIRED COMPONENTS
  rospy
  roscpp
  std_msgs
  geometry_msgs
  sensor_msgs
  nav_msgs
  tf
  tf2_ros
  move_base
  global_planner
  dwa_local_planner
  teb_local_planner
  costmap_2d
  carla_msgs
)

catkin_package(
  CATKIN_DEPENDS
    rospy
    roscpp
    std_msgs
    geometry_msgs
    sensor_msgs
    nav_msgs
    tf
    tf2_ros
    move_base
    global_planner
    dwa_local_planner
    teb_local_planner
    costmap_2d
    carla_msgs
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)

# Install Python scripts
catkin_install_python(PROGRAMS
  scripts/cmd_vel_to_ackermann.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

# Install launch files
install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)

# Install config files
install(DIRECTORY config/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/config
)

# Install rviz files
install(DIRECTORY rviz/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/rviz
)