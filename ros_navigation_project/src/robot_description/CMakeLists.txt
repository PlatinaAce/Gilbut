cmake_minimum_required(VERSION 3.0.2)
project(robot_description)

find_package(catkin REQUIRED COMPONENTS
  rospy
  roscpp
  urdf
  xacro
  robot_state_publisher
  tf
)

catkin_package(
  CATKIN_DEPENDS
    rospy
    roscpp
    urdf
    xacro
    robot_state_publisher
    tf
)

include_directories(
  ${catkin_INCLUDE_DIRS}
)

# Install launch files
install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
  OPTIONAL
)

# Install URDF files
install(DIRECTORY urdf/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/urdf
  OPTIONAL
)