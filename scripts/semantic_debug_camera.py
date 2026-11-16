"""Same-frame debug imagery; no additional detector invocation or inference."""
import base64
import numpy as np

def detection_rows(boxes, localized):
    rows=[]
    for box in boxes:
        match=next((d for d in localized if list(d['bbox'])==list(box['bbox']) and d['category']==box['category']),None)
        row={'bbox':[float(v) for v in box['bbox']], 'category':box['category'],
             'confidence':float(box['detector_score']), 'localized':match is not None}
        if match is not None:
            row.update(color=match.get('color','unknown'),range_m=float(match['range_m']))
        rows.append(row)
    return rows

def encode_frame(rgb, sim_time, detections):
    import cv2
    ok,jpeg=cv2.imencode('.jpg',cv2.cvtColor(rgb,cv2.COLOR_RGB2BGR),[cv2.IMWRITE_JPEG_QUALITY,80])
    if not ok:raise ValueError('debug camera JPEG encode failed')
    return {'sim_time':float(sim_time),'width':int(rgb.shape[1]),'height':int(rgb.shape[0]),
            'jpeg_base64':base64.b64encode(jpeg.tobytes()).decode('ascii'), 'detections':detections}

def decode_frame(camera):
    from io import BytesIO
    from PIL import Image
    raw=base64.b64decode(camera['jpeg_base64'],validate=True)
    with Image.open(BytesIO(raw)) as im:
        if im.size!=(camera['width'],camera['height']):raise ValueError('debug camera dimensions mismatch')
        return np.asarray(im.convert('RGB'))
