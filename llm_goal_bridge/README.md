# llm_goal_bridge (v0.0.2)

TCP(JSONL) -> Nav2 NavigateToPose goal bridge + optional cmd_vel publisher.

## Supported input examples

### Goal by coordinates
```json
{"type":"goal","frame":"map","x":1.2,"y":-0.4,"yaw":1.57}
```

Also accepts alternate keys:
- frame: frame_id, map_frame
- x/y: px/py, pos_x/pos_y
- yaw: theta, heading

Nested:
```json
{"action":"navigate","pose":{"x":1.2,"y":-0.4,"yaw":1.57},"frame_id":"map"}
```

### Goal by destination name (place_db.yaml)
```json
{"intent":"go_to","destination":"kitchen"}
```

### cmd_vel (optional)
Direct:
```json
{"type":"cmd_vel","linear":0.2,"angular":0.0,"duration":1.0}
```

Action shorthand:
```json
{"action":"forward","speed":0.2,"duration":1.0}
{"action":"left","angular":0.6,"duration":0.8}
{"action":"stop"}
```

## Build
```bash
cd ~/ros2_ws
cp -r llm_goal_bridge src/
colcon build --packages-select llm_goal_bridge
source install/setup.bash
```

## Run
```bash
ros2 launch llm_goal_bridge tcp_goal_bridge.launch.py
```

## Test
```bash
printf '{"type":"goal","frame":"map","x":1.2,"y":-0.4,"yaw":1.57}\n' | nc 127.0.0.1 9000
printf '{"intent":"go_to","destination":"kitchen"}\n' | nc 127.0.0.1 9000
printf '{"action":"left","duration":0.5}\n' | nc 127.0.0.1 9000
```
