"""Synthetic checker regression tests; no method or simulation is executed."""
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile

here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('checker', here / 'check_outputs.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
seal = json.loads((here / 'seal.json').read_text())
base = json.loads((here.parent / 'baseline-out/run/ensemble.json').read_text())
log = (here.parent / 'baseline-out/run/baseline.log').read_text()


def results(output):
    return {c['id']: c['pass'] for c in checker.assess(base, output, seal, [log, log])}


assert all(results(base).values())
for case, change in (
    ('dropped_inputs', lambda x: x['replicas'].pop(2)),
    ('duplicated_inputs', lambda x: x['replicas'].append(copy.deepcopy(x['replicas'][0]))),
    ('ordering', lambda x: x['replicas'].reverse()),
    ('tail_handling', lambda x: x['replicas'][-1].update(steps=24999)),
    ('tail_handling', lambda x: x['replicas'].pop()),
    ('seeds', lambda x: x['replicas'][3].update(seed=2003)),
    ('output_schema', lambda x: x['replicas'][0].update(mean_potential_kj_mol=float('nan'))),
):
    output = copy.deepcopy(base)
    change(output)
    assert not results(output)[case], case

metric = seal['equivalence_metrics'][0]
name, margin = metric['name'], metric['tolerance']['abs']
for sign in (-1, 1):
    output = copy.deepcopy(base)
    for row in output['replicas']:
        row[name] += sign * 2 * margin
    assert not results(output)['equivalence']

# A large outlier with a CI overlapping the margin cannot reject.
output = copy.deepcopy(base)
output['replicas'][-1][name] += 100 * margin
assert results(output)['equivalence']
assert checker.median_interval([0] * 8, .95, 2) == (0, 0)
assert checker.median_interval([1] * 6, .95, 2) == (-math.inf, math.inf)
assert checker.median_interval([-margin] * 8, .95, 2) == (-margin, -margin)

# Exercise the actual shell entrypoint and report contract, using frozen
# baseline artifacts as both arms, then synthetic missing/invalid outputs.
with tempfile.TemporaryDirectory(prefix='selfcheck-', dir=here) as directory:
    work = Path(directory)
    method = work / 'synthetic-output'
    (method / 'run').mkdir(parents=True)
    (method / 'run/ensemble.json').write_text(json.dumps(base))
    (method / 'run/baseline.log').write_text(log)
    env = dict(os.environ, BASELINE_OUT=str(here.parent / 'baseline-out'), METHOD_OUT=str(method),
               PYTHONDONTWRITEBYTECODE='1')
    for mode in ('valid', 'missing', 'invalid'):
        if mode == 'missing':
            (method / 'run/ensemble.json').unlink()
        elif mode == 'invalid':
            (method / 'run/ensemble.json').write_text('{')
        run = subprocess.run(['bash', str(here / 'run_tests.sh')], cwd=work, env=env,
                             capture_output=True, text=True, timeout=10)
        report = json.loads((work / 'out/tests.json').read_text())
        assert set(report) == {'passed', 'failed', 'cases'}
        assert report['passed'] + report['failed'] == len(report['cases'])
        assert report['passed'] == sum(c['pass'] for c in report['cases'])
        assert len({c['id'] for c in report['cases']}) == len(report['cases'])
        assert (run.returncode == 0) == (mode == 'valid')
        assert report['failed'] == (0 if mode == 'valid' else len(checker.CASE_IDS))
print('Checker self-checks passed.')
