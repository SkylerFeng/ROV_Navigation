"""Validated, ROS-independent semantic configuration; no credentials in snapshots."""
import copy
import json
import math
import os
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config/semantic'
TASK_KEYS = set('instruction category color depth_m surface_standoff_m arrival_tolerance_m hold_seconds max_speed_at_completion max_observation_age_s detector_confidence confirmation_frames grid_resolution_m clearance_m timeout_sim_s action_timeout_sim_s'.split())
RUNTIME_KEYS = {
    'recovery': 'timeout_s look_s sweep_deg max_attempts association_radius_m target_memory_s cooldown_s explore_commit_s',
    'scan': 'sweep_deg timeout_s yaw_step_rad max_sectors_per_viewpoint',
    'verification': 'timeout_s freshness_s heading_tolerance_deg distance_near_margin_m distance_far_margin_m',
    'execution': 'tick_s snapshot_interval_s hold_s blocked_grace_s max_llm_calls progress_timeout_s progress_distance_m',
    'motion': 'hold_max_speed_m_s position_kp yaw_kp max_yaw_rate_rad_s lease_timeout_s',
    'exploration': 'max_candidates min_travel_m min_viewpoint_separation_m candidate_separation_m viewpoint_radius_m min_unknown_cells approach_retry_separation_m explore_retry_separation_m inspection_range_m gain_power travel_cost_weight',
    'llm': 'timeout_s temperature max_tokens enable_thinking max_consecutive_errors',
}

def exact_keys(value, expected, name):
    if not isinstance(value,dict) or set(value)!=set(expected):
        raise ValueError(f'{name}: expected keys {sorted(expected)}')

def read_object(path):
    with Path(path).open(encoding='utf-8') as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f'{path}: expected a JSON object')
    return value

def merge_known(base, patch, prefix='config'):
    result = copy.deepcopy(base)
    for key, value in patch.items():
        if key not in base:
            raise ValueError(f'{prefix}.{key}: unknown parameter')
        if isinstance(base[key], dict):
            if not isinstance(value, dict):
                raise ValueError(f'{prefix}.{key}: expected an object')
            result[key] = merge_known(base[key], value, f'{prefix}.{key}')
        else:
            result[key] = value
    return result

def number(value, name, low=0, high=None, integer=False, allow_zero=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{name}: expected a finite number')
    if integer and not isinstance(value, int):
        raise ValueError(f'{name}: expected an integer')
    if (value < low if allow_zero else value <= low) or (high is not None and value > high):
        raise ValueError(f'{name}: out of range')

def load_task(path=None):
    base = read_object(CONFIG / 'task.json')
    exact_keys(base,TASK_KEYS,'task')
    value = merge_known(base, read_object(path), 'task') if path else base
    for key in ('instruction', 'category', 'color'):
        if not isinstance(value[key], str) or not value[key].strip():
            raise ValueError(f'task.{key}: expected nonempty text')
    if value['category'] not in ('pipe', 'box') or value['color'] not in ('yellow', 'blue', 'red'):
        raise ValueError('task: unsupported detector category or color')
    for key, item in value.items():
        if key not in ('instruction', 'category', 'color'):
            number(item, 'task.'+key, integer=key=='confirmation_frames')
    if value['depth_m'] != 1.0:
        raise ValueError('task.depth_m must be 1.0: planner/tracker currently use fixed world Z, not depth below water')
    if value['detector_confidence'] > 1:
        raise ValueError('task.detector_confidence must be <= 1')
    return value

def load_runtime(path=None):
    base = read_object(CONFIG / 'runtime.json')
    exact_keys(base,RUNTIME_KEYS,'runtime')
    for group,keys in RUNTIME_KEYS.items():exact_keys(base[group],keys.split(),'runtime.'+group)
    path = path or os.environ.get('ROV_SEMANTIC_RUNTIME_CONFIG')
    value = merge_known(base, read_object(path), 'runtime') if path else base
    for group, entries in value.items():
        for key, item in entries.items():
            if key == 'enable_thinking':
                if item is not False:
                    raise ValueError('llm.enable_thinking must be false for the current JSON action contract')
                continue
            number(item, group+'.'+key, integer=key in ('max_llm_calls','max_candidates','min_unknown_cells','max_tokens','max_consecutive_errors','max_attempts','max_sectors_per_viewpoint'),
                   allow_zero=key=='temperature')
    if value['recovery']['look_s']>=value['recovery']['timeout_s'] or value['recovery']['sweep_deg']>90:
        raise ValueError('recovery requires look_s < timeout_s and sweep_deg <= 90')
    if value['scan']['sweep_deg'] > 360 or value['verification']['heading_tolerance_deg'] > 180:
        raise ValueError('scan sweep must be <= 360 deg; heading tolerance must be <= 180 deg')
    if value['llm']['temperature'] > 2:
        raise ValueError('llm.temperature must be <= 2')
    if value['execution']['tick_s'] >= value['motion']['lease_timeout_s']:
        raise ValueError('execution.tick_s must be less than motion.lease_timeout_s')
    return value

def load_providers(path=None):
    base = read_object(CONFIG / 'providers.json')
    exact_keys(base,('qwen','deepseek'),'providers')
    value = merge_known(base, read_object(path), 'providers') if path else base
    for name, entry in value.items():
        if set(entry) != {'base_url','model','key_env'}:
            raise ValueError(f'providers.{name}: use base_url, model and key_env only; keep secrets in environment')
        if not all(isinstance(v,str) and v.strip() for v in entry.values()):
            raise ValueError(f'providers.{name}: expected nonempty strings')
        validate_url(entry['base_url'])
    return value

def validate_url(url):
    parts = urlsplit(url)
    if parts.scheme not in ('http','https') or not parts.netloc or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError('API base URL must be HTTP(S) without embedded credentials, query or fragment')

def effective_provider(provider, providers):
    value = dict(providers[provider])
    value['model'] = os.getenv('ROV_LLM_MODEL') or value['model']
    value['base_url'] = os.getenv('ROV_LLM_BASE_URL') or value['base_url']
    validate_url(value['base_url'])
    return value
