#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
import csv
import time
import tf_transformations

class OdomPublisher(Node):
    def __init__(self):
        super().__init__('odom_publisher')
        self.pub = self.create_publisher(Odometry, 'odom', 10)

        # load CSV
        with open('/mnt/data/odom.csv') as f:
            reader = csv.DictReader(f)
            self.rows = list(reader)

        # compute relative times
        t0 = float(self.rows[0]['t'])
        for r in self.rows:
            r['rel'] = float(r['t']) - t0

        self.start_time = time.time()
        self.publish_loop()

    def publish_loop(self):
        last_rel = 0.0
        for r in self.rows:
            target = r['rel']
            now = time.time() - self.start_time
            to_sleep = target - now
            if to_sleep > 0:
                time.sleep(to_sleep)

            msg = Odometry()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = 'odom'
            msg.child_frame_id = 'base_link'
            msg.pose.pose.position.x = float(r['x'])
            msg.pose.pose.position.y = float(r['y'])
            # assume planar θ
            q = tf_transformations.quaternion_from_euler(0, 0, float(r['theta']))
            msg.pose.pose.orientation.x = q[0]
            msg.pose.pose.orientation.y = q[1]
            msg.pose.pose.orientation.z = q[2]
            msg.pose.pose.orientation.w = q[3]

            self.pub.publish(msg)

def main():
    rclpy.init()
    node = OdomPublisher()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()

