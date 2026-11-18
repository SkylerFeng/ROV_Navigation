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
        from experiment import load_experiment
        from static_collision_prior import load_static_xy
        c=load_experiment();xy=load_static_xy(c)
        self.planner=c["navigation"]["planner"];self.res=self.planner["cloud_resolution_m"]
        self.cached_cloud=None;self.cached_count=-1
        self.occupied = set(map(tuple,np.floor(xy/self.res).astype(int)))
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
        cells = np.unique(np.floor(points[:, :2] / self.res).astype(int), axis=0)
        self.occupied.update(map(tuple, cells))
        if self.occupied:
            if self.cached_count!=len(self.occupied):
                cells=np.array(list(self.occupied))
                if self.planner['preinflate_cloud']:
                    from cloud_inflation import inflate_columns
                    cells=inflate_columns(cells,self.res,self.planner['obstacle_inflation_m'],self.planner['circular_xy_inflation'])
                xy=(cells+.5)*self.res
                columns=np.concatenate([np.column_stack([xy,np.full(len(xy),z)]) for z in np.arange(.825,1.326,.1)])
                self.cached_cloud=np.concatenate([columns,self.planes]);self.cached_count=len(self.occupied)
            output=self.cached_cloud
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
