"""ONNX YOLO detector; CPU runtime leaves GPU memory for Isaac Sim."""
import cv2,numpy as np
class Detector:
    def __init__(self,path,confidence=.45):
        import onnxruntime as ort
        options=ort.SessionOptions();options.intra_op_num_threads=2;options.inter_op_num_threads=1
        self.session=ort.InferenceSession(str(path),sess_options=options,providers=['CPUExecutionProvider'])
        self.input=self.session.get_inputs()[0].name;self.conf=confidence
        self.names=['pipe','box']
    def predict(self,rgb):
        h,w=rgb.shape[:2];scale=min(640/w,640/h);nw,nh=round(w*scale),round(h*scale)
        left,top=(640-nw)//2,(640-nh)//2
        resized=cv2.resize(rgb,(nw,nh));padded=np.full((640,640,3),114,np.uint8);padded[top:top+nh,left:left+nw]=resized
        inp=np.ascontiguousarray(padded.transpose(2,0,1)[None],np.float32)/255.
        output=self.session.run(None,{self.input:inp})[0][0].T
        if output.shape[1]!=6:raise ValueError('Expected two-class YOLO output (4 box + 2 classes)')
        labels=output[:,4:].argmax(1);scores=output[:,4:].max(1);good=scores>=self.conf
        output,labels,scores=output[good],labels[good],scores[good]
        if not len(output):return []
        boxes=output[:,:4].copy();boxes[:,:2]-=boxes[:,2:]/2
        indices=[]
        for cls in range(2):
            ix=np.flatnonzero(labels==cls)
            keep=cv2.dnn.NMSBoxes(boxes[ix].tolist(),scores[ix].tolist(),self.conf,.45)
            indices.extend(ix[np.asarray(keep).reshape(-1)].tolist() if len(keep) else [])
        results=[]
        for i in indices:
            x,y,bw,bh=boxes[i];xyxy=[(x-left)/scale,(y-top)/scale,(x+bw-left)/scale,(y+bh-top)/scale]
            xyxy=np.clip(xyxy,[0,0,0,0],[w,h,w,h]).tolist()
            results.append({'category':self.names[labels[i]],'detector_score':float(scores[i]),'bbox':xyxy})
        return results
