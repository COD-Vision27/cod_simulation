#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped


class OdomToTF(Node):
    def __init__(self):
        super().__init__('odom_to_tf')
        # 发布成 URDF 的根坐标系，避免和 robot_state_publisher 的树冲突
        self.declare_parameter('child_frame_id', 'baselink')
        # True：把收到的第一帧里程计的位置当作原点（启动时只平移一次，朝向不归零），
        # 即 odom 原点落在机器人出生点，odom 坐标轴始终与世界/场地坐标轴平行。
        self.declare_parameter('zero_on_start', True)
        self.child_frame_id = (
            self.get_parameter('child_frame_id').get_parameter_value().string_value
        )
        self.zero_on_start = (
            self.get_parameter('zero_on_start').get_parameter_value().bool_value
        )
        self.br = TransformBroadcaster(self)
        self.sub = self.create_subscription(Odometry, 'chassis_odometry_gt', self.cb, 10)
        # 出生点位置 (x, y, z)，首帧到达时写入
        self._origin = None

    def cb(self, msg):
        t = TransformStamped()
        t.header.stamp = msg.header.stamp
        # 去掉命名空间前缀
        frame_id = msg.header.frame_id
        child_frame_id = msg.child_frame_id if msg.child_frame_id else 'base_link'
        if '/' in frame_id:
            frame_id = frame_id.split('/')[-1]
        if '/' in child_frame_id:
            child_frame_id = child_frame_id.split('/')[-1]
        if self.child_frame_id:
            child_frame_id = self.child_frame_id
        t.header.frame_id = frame_id
        t.child_frame_id = child_frame_id

        p = msg.pose.pose.position
        q = msg.pose.pose.orientation

        if self.zero_on_start:
            if self._origin is None:
                self._origin = (p.x, p.y, p.z)
            # 只把位置平移到出生点（在世界坐标轴下相减），朝向保留世界姿态
            ox, oy, oz = self._origin
            tx, ty, tz = p.x - ox, p.y - oy, p.z - oz
        else:
            tx, ty, tz = p.x, p.y, p.z
        rx, ry, rz, rw = q.x, q.y, q.z, q.w

        t.transform.translation.x = tx
        t.transform.translation.y = ty
        t.transform.translation.z = tz
        t.transform.rotation.x = rx
        t.transform.rotation.y = ry
        t.transform.rotation.z = rz
        t.transform.rotation.w = rw
        self.br.sendTransform(t)


def main():
    rclpy.init()
    rclpy.spin(OdomToTF())


if __name__ == '__main__':
    main()
