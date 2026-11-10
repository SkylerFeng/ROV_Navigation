"""Exclusive tracker-side semantic control lease; navigator stays goal-level."""
import math

def motion_override(command,now,position,yaw,maximum=.12,settings=None):
    settings=settings or {}
    maximum=settings.get('hold_max_speed_m_s',maximum)
    if not command or now-command['stamp']>settings.get('lease_timeout_s',.6) or now<command['stamp']-.05:
        return [0.,0.,max(-.08,min(.08,.8*(1-position[2])))],0.,'SEMANTIC_STALE'
    if command['mode']=='navigate':return None
    delta=[command['position'][i]-position[i] for i in range(3)]
    velocity=[max(-maximum,min(maximum,settings.get('position_kp',.8)*d)) for d in delta]
    yaw_error=math.atan2(math.sin(command['yaw']-yaw),math.cos(command['yaw']-yaw))
    limit=settings.get('max_yaw_rate_rad_s',.25)
    return velocity,max(-limit,min(limit,settings.get('yaw_kp',.8)*yaw_error)),'SEMANTIC_'+command['mode'].upper()

def parse_motion(data):
    import json
    c=json.loads(data)
    if set(c)!={'mode','position','yaw','stamp'} or c['mode'] not in ('navigate','hold','scan'):raise ValueError('invalid motion lease')
    if len(c['position'])!=3 or not all(math.isfinite(v) for v in [*c['position'],c['yaw'],c['stamp']]):raise ValueError('nonfinite motion')
    return c
