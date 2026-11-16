"""Real perception method routing: processed preview must not silently feed detector."""
import tempfile,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock
import numpy as np
from semantic_navigation import SemanticNavigation
from semantic_vision import VisionFrontend,load_vision
from semantic_debug_camera import encode_frame
from semantic_debug_viewer import accept_debug

class RoutingTests(unittest.TestCase):
    def test_raw_detection_and_processed_preview_saved_separately(self):
        rgb=np.full((20,24,3),[20,50,100],np.uint8);depth=np.full((20,24),2,np.float32)
        header=NS(stamp=NS(sec=1,nanosec=0))
        position=NS(x=0.,y=0.,z=1.);q=NS(w=1.,x=0.,y=0.,z=0.)
        frame={'rgb':NS(header=header,encoding='rgb8',data=rgb.tobytes(),height=20,width=24,step=72),
               'depth':NS(encoding='32FC1',is_bigendian=False,data=depth.tobytes(),height=20,width=24,step=96),
               'pose':NS(pose=NS(position=position,orientation=q)),
               'info':NS(k=[20.,0,12,0,20.,10,0,0,1],d=[0.]*5,distortion_model='plumb_bob')}
        with tempfile.TemporaryDirectory() as d:
            n=NS(frame=frame,last_processed=-1.,vision=VisionFrontend({**load_vision(),'method':'range_preserve','detector_source':'raw'}),
                 color_model=Mock(),detector=Mock(),memory=Mock(),grid=Mock(),odom=NS(pose=NS(pose=NS(position=position))),
                 frames=0,path=[],last_snapshot=0.,runtime={'execution':{'snapshot_interval_s':.1}},args=NS(output=Path(d)),record=Mock())
            n.detector.predict.return_value=[];n.memory.observe.return_value=[]
            n.grid.free=n.grid.occupied=n.grid.inspected=np.zeros((2,2),bool)
            SemanticNavigation.perceive(n)
            np.testing.assert_array_equal(n.detector.predict.call_args.args[0],rgb)
            self.assertFalse(np.array_equal(n.debug_preview_source[0],rgb))
            with np.load(Path(d)/'latest_sensor.npz') as saved:
                np.testing.assert_array_equal(saved['rgb'],rgb)
                np.testing.assert_array_equal(saved['processed_rgb'],n.debug_preview_source[0])
            self.assertEqual(n.vision_metadata['detector_source'],'raw')
    def test_preview_timestamp_mismatch_or_error_clears_old_preview(self):
        rgb=np.full((20,24,3),70,np.uint8);camera=encode_frame(rgb,1.,[]);preview=encode_frame(rgb,1.,[]);state={}
        accept_debug(state,{'camera':camera,'camera_preview':preview});self.assertIn('preview_rgb',state)
        accept_debug(state,{'camera':camera,'camera_preview':{**preview,'sim_time':2.}});self.assertNotIn('preview_rgb',state)
        accept_debug(state,{'camera':camera,'camera_preview':preview})
        accept_debug(state,{'camera':camera,'camera_preview':{**preview,'jpeg_base64':'bad'}});self.assertNotIn('preview_rgb',state)
        accept_debug(state,{});self.assertNotIn('preview_rgb',state)
if __name__=='__main__':unittest.main()
