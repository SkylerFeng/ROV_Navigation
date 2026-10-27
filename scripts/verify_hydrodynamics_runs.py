"""Check actual arrival/contact/force evidence and export a portable report."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from hydrodynamics_metrics import dynamics_metrics


CORE = ['scripts/hydrodynamics.py', 'scripts/run_sim.py', 'scripts/tracking_control.py',
        'ros_ws/src/plan_manage/src/ego_replan_fsm.cpp',
        'ros_ws/src/plan_manage/src/traj_server.cpp']


def verify(directory):
    run = json.loads((directory/'run.json').read_text())
    controls = json.loads((directory/'controls.json').read_text())
    manifest = json.loads((directory/'manifest.json').read_text())
    samples = np.asarray(run['samples'])
    times = samples[:, 0]
    errors = np.linalg.norm(samples[:, 1:4]-run['config']['goal'], axis=1)
    tail = errors[times >= run['simulation_seconds']-run['settle_time']-1e-6]
    metrics = dynamics_metrics(run, controls)
    finite = all(np.all(np.isfinite(c[key])) for c in controls
                 for key in ['velocity', 'force', 'torque', 'orientation'])
    limits_ok = True
    for c in controls:
        h = c.get('hydrodynamics')
        if h:
            p = run['config']['hydrodynamics']
            limits_ok &= bool(np.all(np.abs(h['actuator_force_body_n']) <= np.array(p['force_limit_n'])+1e-6))
            limits_ok &= bool(np.all(np.abs(h['actuator_torque_body_nm']) <= np.array(p['torque_limit_nm'])+1e-6))
    checks = {
        'arrived': run['stop_reason'] == 'goal_reached',
        'tail_within_tolerance': len(tail) >= 2 and bool(np.all(tail < run['arrival_tolerance'])),
        'no_nonzero_contact_impulse': metrics['max_contact_impulse_ns'] <= 1e-6,
        'finite_controls': bool(controls) and finite,
        'actuator_limits_respected': bool(limits_ok),
        'settle_window_sampled': len(tail) >= int(run['settle_time']/.21),
        'simulation_log_has_no_physx_errors': 'PhysX error:' not in (directory/'simulation.log').read_text(errors='replace'),
    }
    source_hashes = {}
    for key in CORE:
        snapshot = directory/'sources'/key
        if snapshot.exists():
            source_hashes[key] = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    return dict(directory=str(directory), scenario=run['scenario'], checks=checks,
                passed=all(checks.values()), final_error_m=run['goal_distance'],
                simulation_seconds=run['simulation_seconds'],
                tail_max_error_m=float(max(tail)) if len(tail) else None,
                source_sha256=source_hashes, config=run['config'], metrics=metrics,
                git_commit_before_run=manifest.get('git_commit'),
                source_tree_status=manifest.get('git_status'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directories', type=Path, nargs='+')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    results = [verify(d.resolve()) for d in args.directories]
    same_core = all(r['source_sha256'] == results[0]['source_sha256'] for r in results)
    report = {'runs': results, 'same_core_sources': same_core,
              'passed': same_core and all(r['passed'] for r in results),
              'note': 'Finite single trials; sampled telemetry, not a statistical success rate.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    for r in results:
        print(r['scenario'], r['passed'], r['final_error_m'], r['simulation_seconds'], r['checks'])
    raise SystemExit(0 if report['passed'] else 1)
