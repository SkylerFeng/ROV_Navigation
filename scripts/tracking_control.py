"""World-frame tracking with a forward-looking camera's heading constraint."""
import math


def translation_command(position, reference_position, reference_velocity):
    values = [reference_velocity[i]+2*(reference_position[i]-position[i]) for i in range(3)]
    speed = math.hypot(*reference_velocity[:2])
    if speed > .01 and math.dist(position[:2], reference_position[:2]) < .1:
        # Inertia can carry the ROV slightly beyond a frozen reference. Do not
        # turn a centimetre-scale overshoot into a 180-degree heading reversal.
        # Retain cross-track correction and let the phase resume forward.
        tangent = [v/speed for v in reference_velocity[:2]]
        forward = sum(values[i]*tangent[i] for i in range(2))
        if forward < .5*speed:
            for i in range(2):
                values[i] += (.5*speed-forward)*tangent[i]
    values[2] = .8*(1-position[2])
    return values


def control(position, reference_position, reference_velocity, yaw, reference_yaw,
            max_speed=.3, align=True, max_heading_error_deg=20):
    values = translation_command(position, reference_position, reference_velocity)
    if not all(math.isfinite(v) for v in [*values, yaw, reference_yaw]):
        return [0., 0., 0.], 0., {"mode": "INVALID_REFERENCE"}
    speed = math.sqrt(sum(v*v for v in values))
    values = [v*min(1.,max_speed/max(speed,1e-9)) for v in values]
    # ROV can translate sideways, but its only range camera cannot see behind.
    holding = math.hypot(*reference_velocity[:2]) < .01 and math.dist(position[:2],reference_position[:2]) < .03
    # Even a slow translation must face its actual direction. Falling back to
    # spline yaw below .02 m/s could approve motion in the opposite direction.
    target_yaw = (yaw if holding else math.atan2(values[1],values[0])
                  if align and math.hypot(*values[:2])>1e-6 else yaw if align else reference_yaw)
    error = math.atan2(math.sin(target_yaw-yaw),math.cos(target_yaw-yaw))
    scale = 1.
    if align and not holding:
        scale = math.cos(error)**2 if abs(error)<math.radians(max_heading_error_deg) else 0.
        values[0] *= scale; values[1] *= scale
    return values, max(-.5,min(.5,error)), {
        "mode":"HOLDING" if holding else "ALIGNING" if scale==0 else "TRACKING", "heading_error_deg":math.degrees(error),
        "translation_scale":scale, "target_yaw":target_yaw,
        "position_error":math.dist(position,reference_position)}
