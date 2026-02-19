# llm_goal_bridge (ROS1)

TCP(JSONL) -> move_base goal (/move_base_simple/goal) + optional /cmd_vel.

## Build & Run
```bash
cd ~/catkin_ws
catkin_make
source devel/setup.bash
roslaunch llm_goal_bridge tcp_goal_bridge.launch
```

## Test
```bash
printf '{"type":"goal","frame":"map","x":1.2,"y":-0.4,"yaw":1.57}\n' | nc 127.0.0.1 9000
printf '{"intent":"go_to","destination":"kitchen"}\n' | nc 127.0.0.1 9000
printf '{"action":"left","duration":0.5}\n' | nc 127.0.0.1 9000
```

Edit destination DB: `config/place_db.yaml`
