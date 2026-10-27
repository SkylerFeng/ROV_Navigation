"""Sensor-derived columns for the first fixed-depth pool experiment.

Retain observed occupied XY cells and extrude them through the navigation slab.
Add configured top/bottom planes to prevent EGO finding vertical shortcuts.
This is a 2.5D baseline, not an inferred full 3D underwater reconstruction.
"""
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from sensor_msgs.msg import PointCloud2, PointField


class LocalMap(Node):
    def __init__(self):
        super().__init__("rov_local_map")
        self.occupied = set()
        self.publisher = self.create_publisher(PointCloud2, "/rov/cloud_navigation", 10)
        self.create_subscription(PointCloud2, "/rov/cloud_world", self.receive, 10)
        x, y = np.meshgrid(np.arange(-8, 8, .1), np.arange(-6, 6, .1))
        self.planes = np.concatenate([np.column_stack([x.ravel(), y.ravel(), np.full(x.size, z)]) for z in [.80, 1.25]])

    def receive(self, msg):
        points = np.frombuffer(msg.data, dtype=np.float32).reshape(-1, 3)
        points = points[np.isfinite(points).all(axis=1)]
        # Hull spans z=.986..1.246 at the reference height. Include its top
        # and contact margin; the old 1.24 cutoff omitted collidable surfaces.
        points = points[(points[:, 2] > .84) & (points[:, 2] < 1.28) &
                        (np.abs(points[:, 0]) < 8) & (np.abs(points[:, 1]) < 6)]
        cells = np.unique(np.floor(points[:, :2] / .1).astype(int), axis=0)
        self.occupied.update(map(tuple, cells))
        if self.occupied:
            xy = (np.array(list(self.occupied)) + .5) * .1
            columns = np.concatenate([np.column_stack([xy, np.full(len(xy), z)]) for z in np.arange(.8, 1.31, .05)])
            output = np.concatenate([columns, self.planes])
        else:
            output = self.planes
        output = np.ascontiguousarray(output, dtype=np.float32)
        self.publisher.publish(PointCloud2(header=msg.header, height=1, width=len(output),
            fields=[PointField(name=n, offset=i*4, datatype=PointField.FLOAT32, count=1) for i, n in enumerate("xyz")],
            point_step=12, row_step=len(output)*12, data=output.tobytes(), is_dense=True))


def main():
    rclpy.init()
    node = LocalMap()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
