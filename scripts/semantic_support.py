"""Sensor support gates for solid and sparse/occluded object appearances."""
def evaluate_support(detection, location, settings, confirmation_frames=3):
    x0,y0,x1,y1=detection['bbox']
    fraction=location['depth_samples']/max(1.,(x1-x0)*(y1-y0))
    normal=(location['depth_samples']>=settings['min_depth_samples'] and
            fraction>=settings['min_foreground_fraction'])
    sparse=(location['depth_samples']>=settings['sparse_min_depth_samples'] and
            fraction>=settings['sparse_min_foreground_fraction'] and
            detection['detector_score']>=settings['sparse_detector_confidence'] and
            location.get('depth_mad_m',float('inf'))<=settings['sparse_max_depth_mad_m'])
    return {'support_mode':'normal' if normal else 'sparse_temporal' if sparse else 'rejected',
            'foreground_fraction':float(fraction),
            'required_confirmation_frames':confirmation_frames if normal else settings['sparse_confirmation_frames']}
