#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker
import csv
import time
import math

class DetectionPublisher(Node):
    def __init__(self):
        super().__init__('detection_marker_publisher')
        self.pub = self.create_publisher(Marker, 'weed_markers', 10)

        # load odom & detections
        with open('/mnt/data/odom.csv') as f:
            od = list(csv.DictReader(f))
        with open('/mnt/data/field_test_log.csv') as f:
            det = list(csv.DictReader(f))

        # compute rel times
        t0 = float(od[0]['t'])
        for r in od:
            r['rel'] = float(r['t']) - t0
        d0 = float(det[0]['elapsed_s'])
        for r in det:
            r['rel'] = float(r['elapsed_s']) - d0

        # build mapping: for each det, find nearest odom idx
        self.events = []
        for d in det:
            rt = d['rel']
            # find od_idx
            od_idx = min(range(len(od)), key=lambda i: abs(od[i]['rel'] - rt))
            x = float(od[od_idx]['x'])
            y = float(od[od_idx]['y'])
            self.events.append((rt, x, y))

        self.start_time = time.time()
        self.run()

    def run(self):
        for idx, (rt, x, y) in enumerate(self.events):
            now = time.time() - self.start_time
            sleep = rt - now
            if sleep > 0:
                time.sleep(sleep)

            m = Marker()
            m.header.frame_id = 'odom'
            m.header.stamp = self.get_clock().now().to_msg()
            m.ns = 'weeds'
            m.id = idx
            m.type = Marker.SPHERE
            m.action = Marker.ADD
            m.pose.position.x = x
            m.pose.position.y = y
            m.pose.position.z = 0.1
            m.scale.x = m.scale.y = m.scale.z = 0.2
            # red
            m.color.r = 1.0
            m.color.a = 0.8

            self.pub.publish(m)

def main():
    rclpy.init()
    node = DetectionPublisher()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()

