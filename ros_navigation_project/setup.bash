#!/bin/bash
# This script sets up the environment for the ROS navigation project

# Source the ROS setup file
source /opt/ros/noetic/setup.bash

# Source the workspace setup file
source ~/ros_navigation_project/devel/setup.bash

# Optionally, add any additional environment variables or paths here
export ROS_PACKAGE_PATH=~/ros_navigation_project/src:$ROS_PACKAGE_PATH

echo "ROS navigation project environment is set up."