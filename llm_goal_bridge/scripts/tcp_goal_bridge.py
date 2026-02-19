#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""llm_goal_bridge (ROS1)

TCP(JSONL) -> move_base goal (/move_base_simple/goal) + optional /cmd_vel.

Input: one JSON object per line.
Examples:
  {"type":"goal","frame":"map","x":1.2,"y":-0.4,"yaw":1.57}
  {"intent":"go_to","destination":"kitchen"}
  {"type":"cmd_vel","linear":0.2,"angular":0.0,"duration":1.0}
  {"action":"left","duration":0.6}
"""

import json
import socket
import threading
from typing import Dict, Any

import rospy
from geometry_msgs.msg import PoseStamped, Twist
from tf.transformations import quaternion_from_euler
import yaml


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
    mapping = {
        "앞": "forward", "앞으로": "forward", "전진": "forward", "forward": "forward", "go": "forward",
        "뒤": "backward", "뒤로": "backward", "후진": "backward", "backward": "backward",
        "왼쪽": "left", "좌회전": "left", "left": "left", "turn_left": "left",
        "오른쪽": "right", "우회전": "right", "right": "right", "turn_right": "right",
        "정지": "stop", "멈춰": "stop", "멈춤": "stop", "stop": "stop",
    }
    return mapping.get(s, s)


class BridgeNode:
    def __init__(self):
        self.listen_host = rospy.get_param("~listen_host", "0.0.0.0")
        self.listen_port = int(rospy.get_param("~listen_port", 9000))

        self.default_frame = rospy.get_param("~default_frame", "map")
        self.place_db_path = rospy.get_param("~place_db_path", "")

        self.goal_topic = rospy.get_param("~goal_topic", "/move_base_simple/goal")

        self.enable_cmd_vel = bool(rospy.get_param("~enable_cmd_vel", True))
        self.cmd_vel_topic = rospy.get_param("~cmd_vel_topic", "/cmd_vel")
        self.default_linear_speed = float(rospy.get_param("~default_linear_speed", 0.2))
        self.default_angular_speed = float(rospy.get_param("~default_angular_speed", 0.6))
        self.cmd_publish_hz = float(rospy.get_param("~cmd_publish_hz", 10.0))

        self.place_db = self._load_place_db(self.place_db_path)

        self.goal_pub = rospy.Publisher(self.goal_topic, PoseStamped, queue_size=1)
        self.cmd_pub = rospy.Publisher(self.cmd_vel_topic, Twist, queue_size=1) if self.enable_cmd_vel else None

        self._cmd_timer = None
        self._cmd_until = None
        self._cmd_twist = Twist()

        rospy.loginfo("[llm_goal_bridge] ROS1 bridge starting")
        rospy.loginfo(f"[TCP] {self.listen_host}:{self.listen_port}")
        rospy.loginfo(f"[GOAL] topic={self.goal_topic} default_frame={self.default_frame}")
        rospy.loginfo(f"[CMD] enabled={self.enable_cmd_vel} topic={self.cmd_vel_topic}")

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.listen_host, self.listen_port))
        self.server.listen(5)

        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _load_place_db(self, path: str) -> Dict[str, Dict[str, Any]]:
        if not path:
            rospy.logwarn("[place_db] place_db_path is empty. destination/place messages will be rejected.")
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                y = yaml.safe_load(f) or {}
            places = (y.get("places") or {})
            rospy.loginfo(f"[place_db] loaded: {list(places.keys())}")
            return places
        except Exception as e:
            rospy.logerr(f"[place_db] failed to load: {e}")
            return {}

    def _accept_loop(self):
        while not rospy.is_shutdown():
            conn, addr = self.server.accept()
            rospy.loginfo(f"[TCP] client connected: {addr}")
            threading.Thread(target=self._client_loop, args=(conn,), daemon=True).start()

    def _client_loop(self, conn: socket.socket):
        buf = b""
        try:
            while not rospy.is_shutdown():
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
            rospy.loginfo("[TCP] client disconnected")

    def _handle_line(self, s: str):
        try:
            raw = json.loads(s)
        except Exception as e:
            rospy.logwarn(f"[JSON] bad json: {s[:120]}... ({e})")
            return

        msg = raw.get("data", raw) if isinstance(raw, dict) else raw
        if not isinstance(msg, dict):
            rospy.logwarn("[JSON] payload is not an object")
            return

        mtype = _first(msg, ["type", "msg_type", "message_type"])
        action = _first(msg, ["action", "intent", "command", "cmd", "mode"])
        action_norm = _normalize_action(str(action)) if action is not None else ""

        if str(mtype).lower() in ["cmd_vel", "twist", "velocity", "vel"]:
            if not self.enable_cmd_vel:
                rospy.logwarn("[CMD] received but disabled")
                return
            lin = _as_float(_first(msg, ["linear", "lin", "vx", "v"]), 0.0) or 0.0
            ang = _as_float(_first(msg, ["angular", "ang", "wz", "w"]), 0.0) or 0.0
            dur = _as_float(_first(msg, ["duration", "time", "sec", "seconds"]), 0.0) or 0.0
            self._publish_cmd_vel(lin, ang, dur)
            return

        if action_norm in ["forward", "backward", "left", "right", "stop"]:
            if not self.enable_cmd_vel:
                rospy.logwarn("[CMD] received but disabled")
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

        pose = _first(msg, ["pose", "goal", "target", "target_pose", "nav_goal"], None)
        frame = _first(msg, ["frame", "frame_id", "header_frame", "map_frame"], self.default_frame)

        x = y = yaw = None
        if isinstance(pose, dict):
            x = _as_float(_first(pose, ["x", "px", "pos_x"]), None)
            y = _as_float(_first(pose, ["y", "py", "pos_y"]), None)
            yaw = _as_float(_first(pose, ["yaw", "theta", "heading", "rz"]), 0.0)

        x = x if x is not None else _as_float(_first(msg, ["x", "px", "pos_x"]), None)
        y = y if y is not None else _as_float(_first(msg, ["y", "py", "pos_y"]), None)
        yaw = yaw if yaw is not None else _as_float(_first(msg, ["yaw", "theta", "heading", "rz"]), 0.0)

        if x is not None and y is not None:
            self._publish_goal(str(frame), float(x), float(y), float(yaw or 0.0))
            return

        dest = _first(msg, ["destination", "dest", "place", "location", "name"], None)
        if dest is not None:
            name = str(dest)
            place = self.place_db.get(name)
            if not place:
                rospy.logwarn(f"[NAV] unknown destination/place: {name}")
                return
            p_frame = place.get("frame", self.default_frame)
            self._publish_goal(str(p_frame), float(place["x"]), float(place["y"]), float(place.get("yaw", 0.0)))
            return

        rospy.logwarn(f"[JSON] unrecognized keys={list(msg.keys())}")

    def _publish_goal(self, frame: str, x: float, y: float, yaw: float):
        qx, qy, qz, qw = quaternion_from_euler(0.0, 0.0, yaw)
        ps = PoseStamped()
        ps.header.stamp = rospy.Time.now()
        ps.header.frame_id = frame
        ps.pose.position.x = x
        ps.pose.position.y = y
        ps.pose.orientation.x = qx
        ps.pose.orientation.y = qy
        ps.pose.orientation.z = qz
        ps.pose.orientation.w = qw
        self.goal_pub.publish(ps)
        rospy.loginfo(f"[NAV] goal -> frame={frame} x={x:.2f} y={y:.2f} yaw={yaw:.2f}")

    def _publish_cmd_vel(self, linear: float, angular: float, duration: float):
        if not self.enable_cmd_vel or self.cmd_pub is None:
            return

        if duration is None or duration <= 0.0:
            tw = Twist()
            tw.linear.x = float(linear)
            tw.angular.z = float(angular)
            self.cmd_pub.publish(tw)
            rospy.loginfo(f"[CMD] one-shot lin={linear:.2f} ang={angular:.2f}")
            self._stop_cmd_timer()
            return

        self._cmd_twist = Twist()
        self._cmd_twist.linear.x = float(linear)
        self._cmd_twist.angular.z = float(angular)
        self._cmd_until = rospy.Time.now() + rospy.Duration.from_sec(float(duration))

        if self._cmd_timer is None:
            period = 1.0 / max(self.cmd_publish_hz, 1.0)
            self._cmd_timer = rospy.Timer(rospy.Duration.from_sec(period), self._cmd_timer_cb)

        rospy.loginfo(f"[CMD] lin={linear:.2f} ang={angular:.2f} dur={duration:.2f}s")

    def _cmd_timer_cb(self, _evt):
        if self._cmd_until is None or rospy.Time.now() >= self._cmd_until:
            tw = Twist()
            self.cmd_pub.publish(tw)
            self._stop_cmd_timer()
            rospy.loginfo("[CMD] done -> stop")
            return
        self.cmd_pub.publish(self._cmd_twist)

    def _stop_cmd_timer(self):
        if self._cmd_timer is not None:
            try:
                self._cmd_timer.shutdown()
            except Exception:
                pass
            self._cmd_timer = None
        self._cmd_until = None


def main():
    rospy.init_node("llm_goal_bridge")
    BridgeNode()
    rospy.spin()


if __name__ == "__main__":
    main()
