import unittest
import numpy as np
from semantic_debug_camera import detection_rows,encode_frame,decode_frame
from semantic_debug_viewer import accept_debug

class CameraTests(unittest.TestCase):
    def test_detector_only_boxes_remain_visible(self):
        boxes=[{'bbox':[1,2,10,15],'category':'pipe','detector_score':.8},
               {'bbox':[12,2,20,16],'category':'box','detector_score':.7}]
        localized=[{**boxes[0],'color':'blue','range_m':1.2}]
        rows=detection_rows(boxes,localized)
        self.assertTrue(rows[0]['localized']);self.assertFalse(rows[1]['localized'])
        self.assertNotIn('range_m',rows[1]);self.assertEqual(len(rows),2)

    def test_rgb_channels_dimensions_and_timestamp(self):
        rgb=np.zeros((24,32,3),np.uint8);rgb[:,:,0]=240
        packet=encode_frame(rgb,2.5,[])
        decoded=decode_frame(packet)
        self.assertEqual(decoded.shape,rgb.shape);self.assertEqual(packet['sim_time'],2.5)
        self.assertGreater(decoded[:,:,0].mean(),230);self.assertLess(decoded[:,:,2].mean(),10)
        packet['width']=31
        with self.assertRaises(ValueError):decode_frame(packet)

    def test_bad_or_missing_frame_never_keeps_old_image(self):
        packet=encode_frame(np.zeros((16,16,3),np.uint8),1,[]);state={}
        accept_debug(state,{'camera':packet});self.assertIn('camera_rgb',state)
        accept_debug(state,{'camera':{**packet,'jpeg_base64':'invalid!'}})
        self.assertNotIn('camera_rgb',state);self.assertIn('camera_decode_error',state)
        accept_debug(state,{})
        self.assertNotIn('camera_rgb',state);self.assertNotIn('camera_decode_error',state)

if __name__=='__main__':unittest.main()
