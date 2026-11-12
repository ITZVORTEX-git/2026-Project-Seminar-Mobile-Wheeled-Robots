import math
import os

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import rclpy
import rclpy.time
from rclpy.node import Node
import tf2_ros
from geometry_msgs.msg import TwistStamped
from rosgraph_msgs.msg import Clock


class DataHandler(Node):
    def __init__(self):
        super().__init__('data_handler')
        self.declare_parameter('duration', 120.0)
        self.declare_parameter('output_name', 'noise_0')
        self.declare_parameter('output_directory', 'results')
        self.declare_parameter('sample_rate', 20.0)
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('gt_frame', 'base_link_gt')
        self.declare_parameter('odom_frame', 'base_link')
        self.duration = self.get_parameter('duration').value
        self.output_name = self.get_parameter('output_name').value
        self.output_directory = self.get_parameter('output_directory').value
        self.sample_rate = self.get_parameter('sample_rate').value
        self.map_frame = self.get_parameter('map_frame').value
        self.gt_frame = self.get_parameter('gt_frame').value
        self.odom_frame = self.get_parameter('odom_frame').value
        self.state = 'STANDBY'
        self.done = False
        self.sim_time = None
        self.t0 = None
        self.last_t = None
        self.cmd_log = []
        self.cmd_index = 0
        self.pos_x = self.pos_y = self.pos_yaw = 0.0
        self.pos_t = 0.0
        self.t_list = []
        self.gt_list = []
        self.enc_list = []
        self.cmd_list = [] 
        self.create_subscription(TwistStamped, '/cmd_vel', self.cmd_callback, 10)
        self.create_subscription(Clock, '/clock', self.clock_callback, 10)
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        self.timer = self.create_timer(1.0 / self.sample_rate, self.tick)

    def clock_callback(self, msg):
        self.sim_time = msg.clock.sec + msg.clock.nanosec * 1e-9

    def cmd_callback(self, msg):
        if self.sim_time is not None:
            self.cmd_log.append((self.sim_time, msg.twist.linear.x, msg.twist.angular.z))

    def tick(self):
        if self.done:
            return
        match self.state:
            case 'STANDBY':
                if self.sim_time is None or not self.cmd_log:
                    return
                try:
                    t_gt, x, y, yaw = self.lookup(self.gt_frame)
                    self.lookup(self.odom_frame)
                except tf2_ros.TransformException:
                    return
                self.t0 = self.last_t = self.pos_t = t_gt
                self.pos_x, self.pos_y, self.pos_yaw = x, y, yaw
                self.cmd_index = 0
                self.state = 'RUNNING'
                self.get_logger().info(
                    f'Start: t0={self.t0:.2f} x={x:.3f} y={y:.3f} yaw={yaw:.3f}')

            case 'RUNNING':
                try:
                    t_gt, *_ = self.lookup(self.gt_frame)
                    t_enc, *_ = self.lookup(self.odom_frame)
                    t_q = min(t_gt, t_enc)
                    if t_q <= self.last_t:
                        return
                    _, *gt = self.lookup(self.gt_frame, t_q)
                    _, *enc = self.lookup(self.odom_frame, t_q)
                except tf2_ros.TransformException:
                    return
                self.advance_position(t_q)
                self.t_list.append(t_q - self.t0)
                self.gt_list.append(gt)
                self.enc_list.append(enc)
                self.cmd_list.append((self.pos_x, self.pos_y, self.pos_yaw))
                self.last_t = t_q
                if t_q - self.t0 >= self.duration:
                    self.finish()

    def advance_position(self, t):
        while self.pos_t < t:
            while (self.cmd_index + 1 < len(self.cmd_log)
                   and self.cmd_log[self.cmd_index + 1][0] <= self.pos_t):
                self.cmd_index += 1
            t_next = t
            if self.cmd_index + 1 < len(self.cmd_log):
                t_next = min(t, self.cmd_log[self.cmd_index + 1][0])
            dt = t_next - self.pos_t
            _, v, w = self.cmd_log[self.cmd_index]
            avg_ang = self.pos_yaw + 0.5 * w * dt
            self.pos_x += v * math.cos(avg_ang) * dt
            self.pos_y += v * math.sin(avg_ang) * dt
            self.pos_yaw += w * dt
            self.pos_t = t_next

    def lookup(self, frame, t=None):
        when = (rclpy.time.Time() if t is None
                else rclpy.time.Time(nanoseconds=int(t * 1e9)))
        tr = self.tf_buffer.lookup_transform(self.map_frame, frame, when)
        stamp = tr.header.stamp.sec + tr.header.stamp.nanosec * 1e-9
        p, q = tr.transform.translation, tr.transform.rotation
        yaw = math.atan2(2 * (q.w * q.z + q.x * q.y),
                         1 - 2 * (q.y * q.y + q.z * q.z))
        return stamp, p.x, p.y, yaw
    
    def finish(self):
        self.timer.cancel()
        try:
            t = np.array(self.t_list)
            gt = np.array(self.gt_list)
            enc = np.array(self.enc_list)
            cmd = np.array(self.cmd_list)

            err_pos_enc = np.hypot(enc[:, 0] - gt[:, 0], enc[:, 1] - gt[:, 1])
            err_pos_cmd = np.hypot(cmd[:, 0] - gt[:, 0], cmd[:, 1] - gt[:, 1])

            def yaw_err(est):
                d = est[:, 2] - gt[:, 2]
                return np.abs(np.arctan2(np.sin(d), np.cos(d)))

            err_yaw_enc = yaw_err(enc)
            err_yaw_cmd = yaw_err(cmd)

            out_dir = self.output_directory
            os.makedirs(out_dir, exist_ok=True)
            base = os.path.join(self.output_directory, self.output_name)

            header = ('t,gt_x,gt_y,gt_yaw,enc_x,enc_y,enc_yaw,cmd_x,cmd_y,cmd_yaw,'
                    'err_pos_enc,err_pos_cmd,err_yaw_enc,err_yaw_cmd')
            table = np.column_stack([t, gt, enc, cmd,
                                    err_pos_enc, err_pos_cmd,
                                    err_yaw_enc, err_yaw_cmd])
            np.savetxt(base + '.csv', table, delimiter=',', header=header, comments='')

            fig = plt.figure(figsize=(14, 5))
            ax_xy = fig.add_subplot(1, 3, 1)
            ax_pos = fig.add_subplot(1, 3, 2)
            ax_yaw = fig.add_subplot(1, 3, 3)

            ax_xy.plot(gt[:, 0], gt[:, 1], label='GT')
            ax_xy.plot(enc[:, 0], enc[:, 1], label='Одометрия по энкодерам')
            ax_xy.plot(cmd[:, 0], cmd[:, 1], label='Одометрия по командам')
            ax_xy.set_aspect('equal', adjustable='datalim')
            ax_xy.set_xlabel('x, м')
            ax_xy.set_ylabel('y, м')
            ax_xy.set_title('Траектории')
            ax_xy.legend()
            ax_xy.grid(True)

            ax_pos.plot(t, err_pos_enc, label='По энкодерам')
            ax_pos.plot(t, err_pos_cmd, label='По командам')
            ax_pos.set_xlabel('Время от начала эксперимента, с')
            ax_pos.set_ylabel('Ошибка положения, м')
            ax_pos.set_title('Ошибка положения')
            ax_pos.legend()
            ax_pos.grid(True)

            ax_yaw.plot(t, err_yaw_enc, label='По энкодерам')
            ax_yaw.plot(t, err_yaw_cmd, label='По командам')
            ax_yaw.set_xlabel('Время от начала эксперимента, с')
            ax_yaw.set_ylabel('Ошибка угла, рад')
            ax_yaw.set_title('Ошибка угла рысканья')
            ax_yaw.legend()
            ax_yaw.grid(True)

            fig.suptitle(f'{self.output_name}')
            fig.tight_layout()
            fig.savefig(base + '.png', dpi=150)
            plt.close(fig)

            self.get_logger().info(
                f'Сохранено: {base}.png и {base}.csv '
                f'({len(t)} точек, итоговая ошибка по энкодерам {err_pos_enc[-1]:.3f} м, '
                f'по командам {err_pos_cmd[-1]:.3f} м)')
        except Exception as e:
            self.get_logger().error(f'Не удалось сохранить результаты: {e}')
        finally:
            self.done = True


def main():
    rclpy.init()
    node = DataHandler()
    while rclpy.ok() and not node.done:
        rclpy.spin_once(node, timeout_sec=0.1)
    node.destroy_node()
    rclpy.shutdown()