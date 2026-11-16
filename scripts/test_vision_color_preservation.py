import unittest,tempfile,json
from pathlib import Path
import numpy as np
from semantic_vision import enhance,load_vision,ratio_preserving_exposure,estimate_neutral_gains

class PreservationTests(unittest.TestCase):
    def test_neutral_uncalibrated_is_identity_even_blue_dominated(self):
        rgb=np.full((40,50,3),[12,30,90],np.uint8)
        rgb[:5,:5]=[200,200,200]
        np.testing.assert_array_equal(enhance(rgb,None,{**load_vision(),'method':'neutral_balance'}),rgb)
    def test_exposure_preserves_channel_ratios_and_gray(self):
        rgb=np.array([[[12,24,80],[80,80,80],[180,100,40],[0,0,0]]],np.uint8)
        out=ratio_preserving_exposure(rgb)
        norm=lambda x:x.astype(float)/np.maximum(1,x.sum(axis=2,keepdims=True))
        np.testing.assert_allclose(norm(out),norm(rgb),atol=.01)
        self.assertEqual(len(set(out[0,1])),1);self.assertGreater(out[0,0,2],rgb[0,0,2])
    def test_explicit_neutral_mask_not_blue_scene(self):
        rgb=np.full((60,80,3),[5,20,90],np.uint8);mask=np.zeros((60,80),bool)
        mask[:10,:10]=True;rgb[mask]=[90,100,110]
        gain=estimate_neutral_gains(rgb,mask)
        np.testing.assert_allclose(np.array(gain)*[90,100,110],[100]*3)
        with self.assertRaises(ValueError):estimate_neutral_gains(rgb,~mask)
        with self.assertRaises(ValueError):estimate_neutral_gains(rgb,np.zeros_like(mask))
    def test_range_preserve_invalid_depth_unchanged_and_dark_neutral(self):
        rgb=np.full((30,40,3),[10,30,60],np.uint8);depth=np.ones((30,40),np.float32)
        depth[0,:]=np.nan;depth[1,:]=0;depth[2,:]=np.inf
        out=enhance(rgb,depth,{**load_vision(),'method':'range_preserve'})
        np.testing.assert_array_equal(out[:3],rgb[:3]);self.assertEqual(out.dtype,np.uint8)
    def test_bad_gains_rejected_by_loader(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'bad.json'
            for patch in ({'neutral_gain_rgb':[2,1,1]},{'preview_gamma':.01},{'preview_max_gain':10}):
                p.write_text(json.dumps(patch))
                with self.assertRaises(ValueError):load_vision(p)
if __name__=='__main__':unittest.main()
