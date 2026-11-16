"""Bounded local reacquisition; memory is a look direction, never success evidence."""
import math

def matching_target(objects, target, now, max_age, anchor=None, radius=.7):
    choices=[o for o in objects if o.get('confirmed') and
             o['category']==target['category'] and o['color']==target['color'] and
             0<=now-o['last_seen']<=max_age and
             (anchor is None or math.dist(o['surface_world'],anchor)<=radius)]
    return max(choices,key=lambda o:o['last_seen'],default=None)

def bearing(position, target):
    return math.atan2(target[1]-position[1],target[0]-position[0])

def recovery_heading(position, target, elapsed, settings):
    # Look directly at last observed surface, then one bounded left/right sweep.
    center=bearing(position,target)
    fraction=max(0.,min(1.,(elapsed-settings['look_s'])/
                       max(.1,settings['timeout_s']-settings['look_s'])))
    offset=math.radians(settings['sweep_deg'])*math.sin(2*math.pi*fraction)
    return center+offset


def scan_entry(yaw, center, sweep_deg):
    """Enter the same observed-space inspection sector from its nearest endpoint.

    Return entry yaw and signed sweep direction; never use target ground truth.
    Ties preserve the legacy clockwise sweep.
    """
    half=math.radians(sweep_deg)/2
    high,low=center+half,center-half
    distance=lambda a:abs(math.atan2(math.sin(a-yaw),math.cos(a-yaw)))
    return (low,1.) if distance(low)+1e-9<distance(high) else (high,-1.)
