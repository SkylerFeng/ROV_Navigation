"""Rendered training-pixel likelihoods, with explicit background rejection."""
from pathlib import Path
import numpy as np
class ColorModel:
    def __init__(self,path):
        data=np.load(path);self.likelihood=data['likelihood'];self.names=data['names'].tolist()
    def classify(self,rgb):
        ix=np.minimum(np.asarray(rgb,dtype=int)//8,31)
        prob=self.likelihood[:,ix[:,:,0],ix[:,:,1],ix[:,:,2]]
        best=prob.argmax(0);confidence=prob.max(0)
        eligible=(confidence>.65)&(np.max(rgb,axis=-1)>15)
        counts=[int(((best==i)&eligible).sum()) for i in range(3)]
        idx=int(np.argmax(counts));mask=(best==idx)&eligible
        if counts[idx]<max(12,.025*mask.size):return 'unknown',np.zeros(mask.shape,bool),0.
        return self.names[idx],mask,float(confidence[mask].mean())
def train(source,destination):
    from scipy.ndimage import gaussian_filter
    samples=np.load(source);names=['yellow','blue','red','background'];hist=[]
    for name in names:
        rgb=samples[name];bins=np.minimum(rgb.astype(int)//8,31)
        h=np.zeros((32,32,32));np.add.at(h,tuple(bins.T),1)
        h=gaussian_filter(h,.7)+1e-6;hist.append(h/h.sum())
    likelihood=np.array(hist);likelihood[3]*=1.5
    likelihood/=likelihood.sum(0,keepdims=True)
    np.savez_compressed(destination,likelihood=likelihood.astype(np.float32),names=np.array(names))
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--samples',default='logs/semantic_dataset_lit/color_samples.npz');p.add_argument('--output',default='config/semantic/color_model.npz');a=p.parse_args();train(a.samples,a.output)
