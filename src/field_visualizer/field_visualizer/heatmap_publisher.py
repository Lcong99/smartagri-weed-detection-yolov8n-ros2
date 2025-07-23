#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import cv2

class HeatmapPublisher(Node):
    def __init__(self):
        super().__init__('heatmap_publisher')
        self.pub = self.create_publisher(Image, 'weed_heatmap', 1)
        self.bridge = CvBridge()
        self.make_and_publish()

    def make_and_publish(self):
        od = pd.read_csv('/mnt/data/odom.csv')
        det = pd.read_csv('/mnt/data/field_test_log.csv')
        # rel times
        od['rel'] = od['t'] - od['t'].iloc[0]
        det['rel'] = det['elapsed_s'] - det['elapsed_s'].iloc[0]

        # map each det→odom point
        pts = []
        for _, d in det.iterrows():
            idx = (od['rel'] - d['rel']).abs().idxmin()
            pts.append((od.at[idx,'x'], od.at[idx,'y']))
        xs, ys = zip(*pts)

        # 2D histogram
        heat, xedges, yedges = np.histogram2d(xs, ys, bins=50)
        heat = np.flipud(heat)  # origin at bottom

        # plot
        plt.imshow(heat, interpolation='nearest', origin='lower')
        plt.axis('off')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
        plt.close()
        buf.seek(0)
        arr = np.frombuffer(buf.getvalue(), dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)

        # publish once latched
        msg = self.bridge.cv2_to_imgmsg(img, encoding='rgba8')
        msg.header.frame_id = 'odom'
        msg.header.stamp = self.get_clock().now().to_msg()
        self.pub.publish(msg)

def main():
    rclpy.init()
    node = HeatmapPublisher()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()

