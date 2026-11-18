import unittest
from semantic_config import load_runtime
from semantic_support import evaluate_support
from semantic_core import ObjectMemory

class SupportTests(unittest.TestCase):
    def setUp(self):
        self.settings=load_runtime()['perception']
    def detection(self,samples=300,score=.95,mad=.008):
        d={'category':'pipe','color':'yellow','detector_score':score,'bbox':[0,0,140,60]}
        loc={'depth_samples':samples,'depth_mad_m':mad,'surface_world':[-4.6,.5,1.1]}
        return {**d,**loc,**evaluate_support(d,loc,self.settings)}
    def test_hollow_pipe_support_requires_extended_confirmation(self):
        d=self.detection()
        self.assertEqual(d['support_mode'],'sparse_temporal')
        self.assertEqual(d['required_confirmation_frames'],8)
        m=ObjectMemory(3)
        for i in range(7):m.update([d],i*.2)
        self.assertFalse(m.observe(1.2)[0]['confirmed'])
        m.update([d],1.4)
        self.assertTrue(m.observe(1.4)[0]['confirmed'])
    def test_small_fragments_remain_rejected(self):
        for n in (14,25,65,100,199):
            with self.subTest(n=n):self.assertEqual(self.detection(n)['support_mode'],'rejected')
    def test_sparse_requires_confidence_and_consistent_depth(self):
        self.assertEqual(self.detection(score=.8)['support_mode'],'rejected')
        self.assertEqual(self.detection(mad=.06)['support_mode'],'rejected')
    def test_normal_support_keeps_original_confirmation(self):
        d=self.detection(samples=1000)
        self.assertEqual(d['support_mode'],'normal')
        m=ObjectMemory(3)
        for i in range(3):m.update([d],i*.2)
        self.assertTrue(m.observe(.4)[0]['confirmed'])
    def test_sparse_evidence_cannot_bypass_category_lock(self):
        m=ObjectMemory(3,memory_seconds=900,class_lock_frames=8)
        box={**self.detection(samples=1000),'category':'box'}
        for i in range(8):m.update([box],i*.2)
        for i in range(12):m.update([self.detection()],10+i*.2)
        self.assertFalse(m.observe(12.2)[0]['confirmed'])
        self.assertEqual(m.observe(12.2)[0]['class_lock'],'box')
    def test_gap_resets_sparse_confirmation(self):
        m=ObjectMemory(3);d=self.detection()
        for i in range(7):m.update([d],i*.2)
        m.update([d],4.)
        self.assertFalse(m.observe(4.)[0]['confirmed'])
        self.assertEqual(m.observe(4.)[0]['category_streak'],1)
    def test_normal_frame_does_not_shortcut_pending_sparse_confirmation(self):
        m=ObjectMemory(3)
        for i in range(3):m.update([self.detection()],i*.2)
        m.update([self.detection(samples=1000)],.6)
        self.assertFalse(m.observe(.6)[0]['confirmed'])
    def test_configurable_confirmation_window_above_eight_frames(self):
        m=ObjectMemory(3);d={**self.detection(),'required_confirmation_frames':12}
        for i in range(11):m.update([d],i*.2)
        self.assertFalse(m.observe(2.)[0]['confirmed'])
        m.update([d],2.2)
        self.assertTrue(m.observe(2.2)[0]['confirmed'])

if __name__=='__main__':unittest.main()
