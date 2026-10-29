"""Exercise the test runner using frozen baseline and synthetic output mutations."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('checker', HERE / 'check_outputs.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
ROOT = HERE.parent
baseline, _ = checker.load(ROOT / 'baseline-out')
assert checker.median_interval(list(range(8))) == (0, 7)
assert checker.median_interval(list(range(6))) == (-float('inf'), float('inf'))

with tempfile.TemporaryDirectory(prefix='self-check-', dir=HERE) as temporary:
    work = Path(temporary)
    base_dir = work / 'baseline'
    base_dir.mkdir()
    (base_dir / 'ensemble.json').write_text(json.dumps(baseline))
    def run(name, mutate, failed_ids):
        candidate = copy.deepcopy(baseline)
        mutate(candidate)
        out = work / name
        out.mkdir()
        (out / 'ensemble.json').write_text(json.dumps(candidate))
        total = candidate['total_wall_s']
        (out / 'stdout.log').write_text(
            f'total_wall_s: {total:.3f}\naggregate_ns_per_day: {0.8*86400/total:.1f}\n')
        env = dict(os.environ, BASELINE_OUT=str(base_dir), METHOD_OUT=str(out))
        completed = subprocess.run(['bash', str(HERE / 'run_tests.sh')], cwd=work, env=env)
        report = json.loads((out / 'tests.json').read_text())
        actual = {c['id'] for c in report['cases'] if not c['pass']}
        assert actual == failed_ids, (name, actual, failed_ids)
        assert completed.returncode == bool(failed_ids), name
        assert set(report) == {'passed', 'failed', 'cases'}
        assert report['passed'] + report['failed'] == len(report['cases'])
        assert report['failed'] == len(actual)
    run('identical', lambda o: None, set())
    run('missing-final', lambda o: o['replicas'].pop(),
        {'dropped_inputs','duplicated_inputs','ordering','tail_handling','seeds','fixed_work'})
    run('duplicate', lambda o: o['replicas'].__setitem__(7, copy.deepcopy(o['replicas'][6])),
        {'dropped_inputs','duplicated_inputs','ordering','tail_handling','seeds'})
    run('reversed', lambda o: o['replicas'].reverse(), {'ordering','tail_handling'})
    run('short-final', lambda o: o['replicas'][-1].__setitem__('steps',24750),
        {'tail_handling','fixed_work'})
    run('wrong-seed', lambda o: o['replicas'][0].__setitem__('seed',999),
        {'dropped_inputs','ordering','seeds'})
    def shift(o, amount):
        for row in o['replicas']:
            row['mean_potential_kj_mol'] += amount
    run('disjoint-positive', lambda o: shift(o, 100), {'equivalence'})
    run('disjoint-negative', lambda o: shift(o, -100), {'equivalence'})
    run('overlap', lambda o: o['replicas'][0].__setitem__(
        'mean_potential_kj_mol', 1e6), set())
    run('nan-energy', lambda o: o['replicas'][0].__setitem__(
        'mean_potential_kj_mol', float('nan')), set(checker.IDS))
    # Boundary checks use zero-valued baselines to avoid cancellation rounding.
    b = copy.deepcopy(baseline)
    for row in b['replicas']:
        for metric in checker.METRICS:
            row[metric] = 0
    for sign in (-1, 1):
        m = copy.deepcopy(b)
        for row in m['replicas']:
            row['mean_potential_kj_mol'] = sign * checker.METRICS['mean_potential_kj_mol']
        assert not checker.equivalence(b['replicas'], m['replicas'])
    assert checker.equivalence([], [])  # Structural cases reject missing records.
    missing = work / 'missing'
    env = dict(os.environ, BASELINE_OUT=str(base_dir), METHOD_OUT=str(missing))
    completed = subprocess.run(['bash', str(HERE / 'run_tests.sh')], cwd=work, env=env)
    report = json.loads((missing / 'tests.json').read_text())
    assert completed.returncode == 1
    assert all(c['reason_code'] == 'missing_output' for c in report['cases'])
print('Output runner self-checks passed.')
