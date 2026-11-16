import unittest,tempfile
from pathlib import Path
import cv2
import numpy as np
from calibrate_underwater_camera import calibrate

class CalibrationTests(unittest.TestCase):
    def test_rendered_board_recovers_known_intrinsics_and_holdout(self):
        cv2.setNumThreads(1)
        k=np.array([[570.,0,320],[0,575.,240],[0,0,1]])
        cols,rows=9,6;square=.025
        board=np.zeros((350,500),np.uint8)
        for y in range(7):
            for x in range(10):board[y*50:(y+1)*50,x*50:(x+1)*50]=255*((x+y)%2)
        plane=np.array([[-square,-square,0],[cols*square,-square,0],[cols*square,rows*square,0],[-square,rows*square,0]],float)
        source=np.array([[0,0],[500,0],[500,350],[0,350]],np.float32)
        rng=np.random.default_rng(93)
        with tempfile.TemporaryDirectory() as directory:
            images=[]
            for i in range(18):
                r=rng.uniform([-.5,-.5,-.2],[.5,.5,.2]);t=np.array([-.10+rng.uniform(-.03,.03),-.065+rng.uniform(-.025,.025),rng.uniform(.5,.8)])
                dest,_=cv2.projectPoints(plane,r,t,k,np.zeros(5));h=cv2.getPerspectiveTransform(source,dest.reshape(-1,2).astype(np.float32))
                image=cv2.warpPerspective(board,h,(640,480),borderValue=160)
                p=Path(directory)/(str(i)+'.png');cv2.imwrite(str(p),image);images.append(p)
            result=calibrate(images,cols,rows,square)
            estimated=np.asarray(result['k'])
            self.assertLess(abs(estimated[0,0]/k[0,0]-1),.03)
            self.assertLess(abs(estimated[1,1]/k[1,1]-1),.03)
            self.assertLess(max(x['rms_px'] for x in result['holdout']),1.)
            self.assertGreaterEqual(len(result['holdout']),3)
    def test_missing_board_cannot_produce_calibration(self):
        with self.assertRaises(ValueError):calibrate([],9,6,.025)
if __name__=='__main__':unittest.main()
