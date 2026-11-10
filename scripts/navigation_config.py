"""Validated navigation tuning, independent of ROS and Isaac."""
import json
import math
import os
from pathlib import Path

DEFAULT = Path(__file__).resolve().parents[1] / 'config/navigation/default.json'
LIMITS = {'max_velocity', 'max_acceleration', 'max_heading_error_deg',
          'tracking_error_limit', 'planner_goal_tolerance', 'align_before_translation',
          'observed_global_guide'}
BOOLEANS = {'align_before_translation', 'observed_global_guide'}

def load_navigation(path=None):
    config = json.loads(DEFAULT.read_text())
    path = path or os.environ.get('ROV_NAVIGATION_CONFIG')
    if path:
        patch = json.loads(Path(path).read_text())
        if not isinstance(patch, dict) or set(patch)-set(config):
            raise ValueError('navigation: expected limits, planner, tracker sections')
        for group, values in patch.items():
            allowed = LIMITS if group == 'limits' else set(config[group])
            if not isinstance(values, dict) or set(values)-allowed:
                raise ValueError('navigation.'+group+': unknown parameters')
            config[group].update(values)
    validate_navigation(config)
    return config

def validate_navigation(config):
    expected = json.loads(DEFAULT.read_text())
    if not isinstance(config, dict) or set(config)!=set(expected):
        raise ValueError('navigation: invalid sections')
    for group, values in config.items():
        allowed = LIMITS if group=='limits' else set(expected[group])
        if not isinstance(values, dict) or set(values)-allowed or (group!='limits' and set(values)!=allowed):
            raise ValueError('navigation.'+group+': invalid parameters')
        for key, value in values.items():
            if key in BOOLEANS:
                if type(value) is not bool:raise ValueError(key+': expected boolean')
            elif isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:
                raise ValueError(key+': expected positive finite number')
    if config['limits'].get('max_heading_error_deg',20)>90:
        raise ValueError('max_heading_error_deg must be <= 90')
    if config['tracker']['near_track_crab_deg']>30:
        raise ValueError('near_track_crab_deg must be <= 30')
    if config['tracker']['input_timeout_s']<=1/config['tracker']['update_hz']:
        raise ValueError('input_timeout_s must exceed tracker period')
    return config

def planner_parameters(config):
    p=config['planner']
    return {'fsm/thresh_replan_time':p['replan_time_s'],
            'fsm/near_track_crab_deg':config['tracker']['near_track_crab_deg'],
            'fsm/tracker_position_kp':config['tracker']['position_kp'],
            'fsm/thresh_no_replan_meter':p['no_replan_distance_m'],
            'fsm/planning_horizon':p['planning_horizon_m'],
            'manager/planning_horizon':p['planning_horizon_m'],
            'grid_map/resolution':p['map_resolution_m'],
            'grid_map/obstacles_inflation':p['obstacle_inflation_m'],
            'optimization/dist0':p['collision_distance_m'],
            'optimization/lambda_collision':p['collision_weight']}
