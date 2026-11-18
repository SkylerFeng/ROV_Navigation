import unittest
from semantic_core import ObjectMemory

class StaticLandmarks(unittest.TestCase):
    def detection(self,category,x=0):
        return {'category':category,'color':'yellow','surface_world':[x,0,1],'detector_score':.9}
    def test_long_revisit_cannot_rename_established_box_to_pipe(self):
        m=ObjectMemory(3,memory_seconds=900,class_lock_frames=8)
        for i in range(10):m.update([self.detection('box')],i*.2)
        original=m.observe(2)[0]['id']
        for i in range(12):m.update([self.detection('pipe')],320+i*.2)
        o=m.observe(322.2)[0]
        self.assertEqual(o['id'],original);self.assertFalse(o['confirmed'])
        self.assertEqual(o['class_lock'],'box');self.assertTrue(o['category_conflict'])
        for i in range(10):m.update([self.detection('box')],323+i*.2)
        self.assertTrue(m.observe(325)[0]['confirmed'])
    def test_distant_same_colour_object_is_separate(self):
        m=ObjectMemory(3,memory_seconds=900,class_lock_frames=8)
        for i in range(10):m.update([self.detection('box')],i*.2)
        for i in range(5):m.update([self.detection('pipe',2)],320+i*.2)
        self.assertEqual(len(m.objects),2)
        self.assertTrue(any(o['category']=='pipe' and o['confirmed'] for o in m.observe(321)))
if __name__=='__main__':unittest.main()
