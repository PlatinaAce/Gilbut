#!/usr/bin/env python3
import json
import math
import socket
import threading
from typing import Dict, Any, Optional, Tuple

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from geometry_msgs.msg import PoseStamped, Twist
from nav2_msgs.action import NavigateToPose

import yaml
from tf_transformations import quaternion_from_euler


def _first(d: Dict[str, Any], keys, default=None):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def _as_float(v, default=None):
    try:
        return float(v)
    except Exception:
        return default


def _normalize_action(s: str) -> str:
    s = (s or "").strip().lower()
    # Korean / English variants
    mapping = {
        "앞": "forward", "앞으로": "forward", "전진": "forward", "forward": "forward", "go": "forward",
        "뒤": "backward", "뒤로": "backward", "후진": "backward", "backward": "backward",
        "왼쪽": "left", "좌회전": "left", "left": "left", "turn_left": "left",
        "오른쪽": "right", "우회전": "right", "right": "right", "turn_right": "right",
        "정지": "stop", "멈춰": "stop", "멈춤": "stop", "stop": "stop",
    }
    return mapping.get(s, s)


class TcpGoalBridge(Node):
    """
    TCP(JSONL) -> Nav2 NavigateToPose action + (optional) /cmd_vel publisher bridge.

    Accepts multiple message formats to match existing llmService outputs.
    One JSON object per line (newline delimited).

    Supported "goal" shapes (examples):
      - {"type":"goal","frame":"map","x":1.2,"y":-0.4,"yaw":1.57}
      - {"action":"navigate","pose":{"x":1.2,"y":-0.4,"yaw":1.57},"frame_id":"map"}
      - {"intent":"go_to","destination":"kitchen"}  (uses place_db)
      - {"command":"goal","data":{"px":1.2,"py":-0.4,"theta":1.57}}

    Supported "cmd_vel" shapes (examples):
      - {"type":"cmd_vel","linear":0.2,"angular":0.0,"duration":1.0}
      - {"action":"forward","speed":0.2,"duration":1.0}
      - {"action":"left","angular":0.6,"duration":0.8}
      - {"action":"stop"}
    """

    def __init__(self):
        super().__init__("tcp_goal_bridge")

        # Parameters
        self.declare_parameter("listen_host", "0.0.0.0")
        self.declare_parameter("listen_port", 9000)

        # Goal / Nav2
        self.declare_parameter("default_frame", "map")
        self.declare_parameter("place_db_path", "")

        # cmd_vel options
        self.declare_parameter("enable_cmd_vel", True)
        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("default_linear_speed", 0.2)
        self.declare_parameter("default_angular_speed", 0.6)
        self.declare_parameter("cmd_publish_hz", 10.0)

        host = self.get_parameter("listen_host").value
        port = int(self.get_parameter("listen_port").value)

        self.default_frame = self.get_parameter("default_frame").value
        self.place_db_path = self.get_parameter("place_db_path").value

        self.enable_cmd_vel = bool(self.get_parameter("enable_cmd_vel").value)
        self.cmd_vel_topic = self.get_parameter("cmd_vel_topic").value
        self.default_linear_speed = float(self.get_parameter("default_linear_speed").value)
        self.default_angular_speed = float(self.get_parameter("default_angular_speed").value)
        self.cmd_publish_hz = float(self.get_parameter("cmd_publish_hz").value)

        self.place_db = self._load_place_db(self.place_db_path)

        # Nav2 action client
        self.nav_client = ActionClient(self, NavigateToPose, "navigate_to_pose")

        # cmd_vel publisher
        self.cmd_pub = self.create_publisher(Twist, self.cmd_vel_topic, 10) if self.enable_cmd_vel else None
        self._cmd_timer = None
        self._cmd_until = None  # rclpy time
        self._cmd_twist = Twist()

        if self.enable_cmd_vel:
            self.get_logger().info(f"[cmd_vel] enabled, topic={self.cmd_vel_topic}, hz={self.cmd_publish_hz}")

        self.get_logger().info(f"[TCP] listening on {host}:{port}")
        self.get_logger().info("[Nav2] action client: navigate_to_pose")

        # TCP server
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(5)

        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _load_place_db(self, path: str) -> Dict[str, Dict[str, Any]]:
        if not path:
            self.get_logger().warn("place_db_path is empty. 'place/destination' messages will be rejected.")
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                y = yaml.safe_load(f) or {}
            places = (y.get("places") or {})
            self.get_logger().info(f"Loaded places: {list(places.keys())}")
            return places
        except Exception as e:
            self.get_logger().error(f"Failed to load place DB: {e}")
            return {}

    def _accept_loop(self):
        while rclpy.ok():
            conn, addr = self.server.accept()
            self.get_logger().info(f"Client connected: {addr}")
            threading.Thread(target=self._client_loop, args=(conn,), daemon=True).start()

    def _client_loop(self, conn: socket.socket):
        buf = b""
        try:
            while rclpy.ok():
                data = conn.recv(4096)
                if not data:
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    self._handle_line(line.decode("utf-8", errors="ignore"))
        finally:
            conn.close()
            self.get_logger().info("Client disconnected")

    # ---------------- Parsing ----------------
    def _handle_line(self, s: str):
        try:
            raw = json.loads(s)
        except Exception as e:
            self.get_logger().warn(f"Bad JSON: {s[:120]}... ({e})")
            return

        # Some services wrap in {"data": {...}} etc.
        msg = raw
        if isinstance(raw, dict):
            msg = raw.get("data", raw)

        if not isinstance(msg, dict):
            self.get_logger().warn("Unsupported payload (not an object)")
            return

        # Decide intent/type
        mtype = _first(msg, ["type", "msg_type", "message_type"])
        action = _first(msg, ["action", "intent", "command", "cmd", "mode"])
        action_norm = _normalize_action(str(action)) if action is not None else ""

        # 1) Explicit cmd_vel type
        if str(mtype).lower() in ["cmd_vel", "twist", "velocity", "vel"]:
            if not self.enable_cmd_vel:
                self.get_logger().warn("cmd_vel received but enable_cmd_vel=false")
                return
            lin = _as_float(_first(msg, ["linear", "lin", "vx", "v"]), 0.0) or 0.0
            ang = _as_float(_first(msg, ["angular", "ang", "wz", "w"]), 0.0) or 0.0
            dur = _as_float(_first(msg, ["duration", "time", "sec", "seconds"]), 0.0) or 0.0
            self._publish_cmd_vel(lin, ang, dur)
            return

        # 2) Action-like cmd: forward/left/right/stop/backward
        if action_norm in ["forward", "backward", "left", "right", "stop"]:
            if not self.enable_cmd_vel:
                self.get_logger().warn("movement cmd received but enable_cmd_vel=false")
                return
            speed = _as_float(_first(msg, ["speed", "linear", "v", "vx"]), self.default_linear_speed)
            ang_speed = _as_float(_first(msg, ["angular", "w", "wz"]), self.default_angular_speed)
            dur = _as_float(_first(msg, ["duration", "time", "sec", "seconds"]), 0.8)

            lin = 0.0
            ang = 0.0
            if action_norm == "forward":
                lin = abs(speed)
            elif action_norm == "backward":
                lin = -abs(speed)
            elif action_norm == "left":
                ang = abs(ang_speed)
            elif action_norm == "right":
                ang = -abs(ang_speed)
            elif action_norm == "stop":
                lin = 0.0
                ang = 0.0
                dur = 0.0

            self._publish_cmd_vel(lin, ang, dur)
            return

        # 3) Goal navigation by coordinates
        pose = _first(msg, ["pose", "goal", "target", "target_pose", "nav_goal"], None)
        frame = _first(msg, ["frame", "frame_id", "header_frame", "map_frame"], self.default_frame)

        # If pose nested object, pull x/y/yaw from it
        x = y = yaw = None
        if isinstance(pose, dict):
            x = _as_float(_first(pose, ["x", "px", "pos_x"]), None)
            y = _as_float(_first(pose, ["y", "py", "pos_y"]), None)
            yaw = _as_float(_first(pose, ["yaw", "theta", "heading", "rz"]), 0.0)

        # Or direct fields
        x = x if x is not None else _as_float(_first(msg, ["x", "px", "pos_x"]), None)
        y = y if y is not None else _as_float(_first(msg, ["y", "py", "pos_y"]), None)
        yaw = yaw if yaw is not None else _as_float(_first(msg, ["yaw", "theta", "heading", "rz"]), 0.0)

        # Some messages use latitude/longitude etc (not supported here)
        if x is not None and y is not None:
            self._send_nav_goal(str(frame), float(x), float(y), float(yaw or 0.0))
            return

        # 4) Goal navigation by place/destination name
        dest = _first(msg, ["destination", "dest", "place", "location", "name"], None)
        if dest is not None:
            name = str(dest)
            place = self.place_db.get(name)
            if not place:
                self.get_logger().warn(f"Unknown destination/place: {name}")
                return
            p_frame = place.get("frame", self.default_frame)
            self._send_nav_goal(str(p_frame), float(place["x"]), float(place["y"]), float(place.get("yaw", 0.0)))
            return

        self.get_logger().warn(f"Unrecognized message shape: keys={list(msg.keys())}")

    # ---------------- Nav2 ----------------
    def _make_pose_stamped(self, frame: str, x: float, y: float, yaw: float) -> PoseStamped:
        qx, qy, qz, qw = quaternion_from_euler(0.0, 0.0, yaw)
        ps = PoseStamped()
        ps.header.stamp = self.get_clock().now().to_msg()
        ps.header.frame_id = frame
        ps.pose.position.x = x
        ps.pose.position.y = y
        ps.pose.orientation.x = qx
        ps.pose.orientation.y = qy
        ps.pose.orientation.z = qz
        ps.pose.orientation.w = qw
        return ps

    def _send_nav_goal(self, frame: str, x: float, y: float, yaw: float):
        if not self.nav_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().warn("Nav2 action server not available yet (navigate_to_pose).")
            return

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose = self._make_pose_stamped(frame, x, y, yaw)

        self.get_logger().info(f"[NAV] goal frame={frame} x={x:.2f} y={y:.2f} yaw={yaw:.2f}")
        send_future = self.nav_client.send_goal_async(goal_msg)
        send_future.add_done_callback(self._goal_response_cb)

    def _goal_response_cb(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn("Goal rejected by Nav2")
            return
        self.get_logger().info("Goal accepted")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._result_cb)

    def _result_cb(self, future):
        res = future.result()
        self.get_logger().info(f"Nav result status={res.status}, result={res.result}")

    # ---------------- cmd_vel ----------------
    def _publish_cmd_vel(self, linear: float, angular: float, duration: float):
        if not self.enable_cmd_vel or self.cmd_pub is None:
            return

        # If duration <= 0: one-shot publish (stop / impulse)
        if duration is None or duration <= 0.0:
            tw = Twist()
            tw.linear.x = float(linear)
            tw.angular.z = float(angular)
            self.cmd_pub.publish(tw)
            self.get_logger().info(f"[CMD] one-shot lin={linear:.2f} ang={angular:.2f}")
            # also stop timer if running
            self._stop_cmd_timer()
            return

        self._cmd_twist = Twist()
        self._cmd_twist.linear.x = float(linear)
        self._cmd_twist.angular.z = float(angular)
        self._cmd_until = self.get_clock().now() + rclpy.time.Duration(seconds=float(duration))

        if self._cmd_timer is None:
            period = 1.0 / max(self.cmd_publish_hz, 1.0)
            self._cmd_timer = self.create_timer(period, self._cmd_timer_cb)

        self.get_logger().info(f"[CMD] lin={linear:.2f} ang={angular:.2f} dur={duration:.2f}s")

    def _cmd_timer_cb(self):
        now = self.get_clock().now()
        if self._cmd_until is None or now >= self._cmd_until:
            # publish stop once then stop timer
            tw = Twist()
            self.cmd_pub.publish(tw)
            self._stop_cmd_timer()
            self.get_logger().info("[CMD] done -> stop")
            return
        self.cmd_pub.publish(self._cmd_twist)

    def _stop_cmd_timer(self):
        if self._cmd_timer is not None:
            try:
                self._cmd_timer.cancel()
            except Exception:
                pass
            self._cmd_timer = None
        self._cmd_until = None


def main():
    rclpy.init()
    node = TcpGoalBridge()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
