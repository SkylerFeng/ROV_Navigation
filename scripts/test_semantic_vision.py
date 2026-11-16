import unittest
import cv2
import numpy as np
from semantic_vision import VisionFrontend,load_vision,enhance

class VisionTests(unittest.TestCase):
    def setUp(self):
        self.cfg=load_vision();self.rgb=np.full((48,64,3),70,np.uint8)
        self.depth=np.full((48,64),2,np.float32);self.k=np.array([[55.,0,32],[0,55,24],[0,0,1]])
    def test_identity_no_double_distortion(self):
        raw,out,d,k,m=VisionFrontend(self.cfg).process(self.rgb,self.depth,self.k,[0]*5)
        np.testing.assert_array_equal(out,self.rgb);np.testing.assert_array_equal(d,self.depth)
        self.assertFalse(m['rectified'])
    def test_geometry_matches_opencv_and_invalid_border(self):
        d=[.4,.03,0,0,0]
        raw,out,depth,k,m=VisionFrontend(self.cfg).process(self.rgb,self.depth,self.k,d)
        expected=cv2.undistort(self.rgb,self.k,np.array(d),None,self.k)
        np.testing.assert_array_equal(raw,expected);self.assertTrue(m['rectified']);self.assertTrue(np.isnan(depth).any())
    def test_recovered_normalized_rays(self):
        points=np.array([[.4,.2,1],[-.45,-.25,1],[.2,-.3,1]],float)
        d=np.array([.3,.02,.005,-.003,0])
        distorted,_=cv2.projectPoints(points,np.zeros(3),np.zeros(3),self.k,d)
        uv=cv2.undistortPoints(distorted,self.k,d,P=self.k).reshape(-1,2)
        rays=(np.c_[uv,np.ones(3)]@np.linalg.inv(self.k).T)
        np.testing.assert_allclose(rays,points,atol=1e-4)
    def test_distance_inverse_has_separate_coefficients(self):
        cfg={**self.cfg,'method':'range_restore'}
        clear=np.full((48,64,3),100.,float)/255
        z=self.depth[:,:,None]
        observed=clear*np.exp(-z*np.array(cfg['attenuation_rgb']))+np.array(cfg['veiling_rgb'])*(1-np.exp(-z*np.array(cfg['backscatter_rgb'])))
        rgb=np.uint8(observed*255);out=enhance(rgb,self.depth,cfg)
        self.assertLess(np.abs(out.astype(float)-100).max(),3)
        invalid=self.depth.copy();invalid[0,0]=np.nan
        np.testing.assert_array_equal(enhance(rgb,invalid,cfg)[0,0],rgb[0,0])
    def test_methods_are_bounded_and_do_not_mutate(self):
        rgb=np.random.default_rng(1).integers(0,256,(48,64,3),dtype=np.uint8);old=rgb.copy()
        for method in ('white_balance','clahe','wb_clahe','fusion','range_restore'):
            out=enhance(rgb,self.depth,{**self.cfg,'method':method})
            self.assertEqual(out.shape,rgb.shape);self.assertEqual(out.dtype,np.uint8)
        np.testing.assert_array_equal(rgb,old)
    def test_bad_geometry_rejected(self):
        with self.assertRaises(ValueError):VisionFrontend({**self.cfg,'geometry':'none'}).process(self.rgb,self.depth,self.k,[.2,0,0,0,0])
        with self.assertRaises(ValueError):VisionFrontend(self.cfg).process(self.rgb,self.depth,self.k,[.2,0,0,0],'equidistant')
if __name__=='__main__':unittest.main()
