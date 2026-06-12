# ROS Navigation Project

This project implements a navigation stack for a robot using ROS Noetic. It utilizes global path planning with the A* algorithm through the `global_planner` package and local path planning with the `dwa_local_planner` package. The navigation stack is designed to integrate with LiDAR for obstacle detection and avoidance.

## Project Structure

```
ros_navigation_project
├── src
│   ├── navigation_stack
│   │   ├── CMakeLists.txt
│   │   ├── package.xml
│   │   ├── launch
│   │   │   ├── move_base.launch
│   │   │   ├── global_planner.launch
│   │   │   ├── dwa_local_planner.launch
│   │   │   └── navigation.launch
│   │   ├── config
│   │   │   ├── costmap_common_params.yaml
│   │   │   ├── global_costmap_params.yaml
│   │   │   ├── local_costmap_params.yaml
│   │   │   ├── global_planner_params.yaml
│   │   │   ├── dwa_local_planner_params.yaml
│   │   │   └── move_base_params.yaml
│   │   ├── maps
│   │   │   └── map.yaml
│   │   └── rviz
│   │       └── navigation.rviz
│   └── robot_description
│       ├── CMakeLists.txt
│       ├── package.xml
│       ├── urdf
│       │   └── robot.urdf
│       └── launch
│           └── robot_state_publisher.launch
├── README.md
└── setup.bash
```

## Setup Instructions

1. **Install ROS Noetic**: Ensure that you have ROS Noetic installed on your system. Follow the official installation guide for your operating system.

2. **Clone the Repository**: Clone this project into your ROS workspace's `src` directory.

   ```bash
   cd ~/catkin_ws/src
   git clone <repository-url>
   ```

3. **Build the Project**: Navigate to your workspace and build the project using `catkin_make`.

   ```bash
   cd ~/catkin_ws
   catkin_make
   ```

4. **Source the Setup File**: Source the setup file to overlay this workspace on top of your environment.

   ```bash
   source devel/setup.bash
   ```

5. **Launch the Navigation Stack**: Use the provided launch files to start the navigation stack.

   ```bash
   roslaunch navigation_stack navigation.launch
   ```

## Usage Guidelines

- Ensure that your robot is equipped with the necessary sensors, such as LiDAR, for obstacle detection.
- Modify the configuration files in the `config` directory to suit your robot's specifications and environment.
- Use RViz to visualize the navigation process and monitor the robot's path planning.

## Dependencies

This project depends on the following ROS packages:

- `global_planner`
- `move_base`
- `dwa_local_planner`
- `costmap_2d`

Make sure these packages are installed in your ROS environment.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.