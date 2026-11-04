"""Synchronized optical-frame RGB/range/intrinsics/pose; no semantic truth."""
import numpy as np
from sensor_msgs.msg import CameraInfo, Image
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Header
class SemanticSensors:
    def __init__(self,node):
        self.depth=node.create_publisher(Image,'/rov/depth_range',3)
        self.info=node.create_publisher(CameraInfo,'/rov/camera_info',3)
        self.pose=node.create_publisher(PoseStamped,'/rov/camera_pose',3)
    def publish(self,camera,stamp):
        d=camera._degraded_depth_frame
        if d is None:return
        d=np.ascontiguousarray(d,dtype=np.float32)
        h=Header(stamp=stamp,frame_id='front_camera')
        self.depth.publish(Image(header=h,height=d.shape[0],width=d.shape[1],encoding='32FC1',step=d.shape[1]*4,data=d.tobytes()))
        k=np.asarray(camera._camera_k,dtype=float)
        self.info.publish(CameraInfo(header=h,height=d.shape[0],width=d.shape[1],distortion_model='plumb_bob',d=[0.]*5,k=k.ravel().tolist(),r=np.eye(3).ravel().tolist(),p=np.c_[k,np.zeros(3)].ravel().tolist()))
        p,q=camera.get_world_pose(camera_axes='ros')
        msg=PoseStamped(header=Header(stamp=stamp,frame_id='world'))
        msg.pose.position.x,msg.pose.position.y,msg.pose.position.z=map(float,p)
        msg.pose.orientation.w,msg.pose.orientation.x,msg.pose.orientation.y,msg.pose.orientation.z=map(float,q)
        self.pose.publish(msg)
