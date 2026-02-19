cmake_minimum_required(VERSION 3.0.2)
project(llm_goal_bridge)

find_package(catkin REQUIRED COMPONENTS
  rospy
  geometry_msgs
  tf
)

catkin_package()

catkin_install_python(PROGRAMS
  scripts/tcp_goal_bridge.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch config
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
