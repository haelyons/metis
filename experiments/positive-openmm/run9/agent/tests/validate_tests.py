"""Synthetic artifact checks only; no method execution or method source reads."""
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile

here = Path(__file__).resolve().parent
baseline = here.parent / 'baseline-out'
original = json.loads((baseline / 'run/ensemble.json').read_text())


def run(label, change, expect_failure=None, equivalent=None):
    with tempfile.TemporaryDirectory(prefix='validation-', dir=here) as temp:
        root = Path(temp)
        method = root / 'candidate-output'
        (method / 'run').mkdir(parents=True)
        data = copy.deepcopy(original)
        change(data)
        if label != 'missing':
            (method / 'run/ensemble.json').write_text(json.dumps(data))
        env = dict(os.environ, BASELINE_OUT=str(baseline), METHOD_OUT=str(method))
        result = subprocess.run(['bash', str(here / 'run_tests.sh')], cwd=root,
                                env=env, capture_output=True, text=True, timeout=10)
        report = json.loads((root / 'out/tests.json').read_text())
        assert set(report) == {'passed', 'failed', 'cases'}, label
        cases = {c['id']: c for c in report['cases']}
        assert len(cases) == len(report['cases']), label
        assert report['failed'] == sum(not c['pass'] for c in cases.values()), label
        assert report['passed'] + report['failed'] == len(cases), label
        assert (result.returncode == 0) == (report['failed'] == 0), label
        if expect_failure:
            assert not cases[expect_failure]['pass'], (label, report)
        else:
            assert result.returncode == 0, (label, report, result.stderr)
        if equivalent is not None:
            assert cases['equivalence']['pass'] is equivalent, (label, report)


run('identical', lambda d: None)
run('missing', lambda d: None, 'output_schema')
run('dropped-final', lambda d: d['replicas'].pop(), 'tail_handling', True)
run('dropped-middle', lambda d: d['replicas'].pop(3), 'dropped_inputs', True)
run('duplicate', lambda d: d['replicas'].append(copy.deepcopy(d['replicas'][0])), 'duplicated_inputs')
run('reverse', lambda d: d['replicas'].reverse(), 'ordering', True)
run('seed', lambda d: d['replicas'][7].update(seed=1006), 'seeds', True)
run('steps', lambda d: d['replicas'][7].update(steps=24750), 'tail_handling')
run('nan', lambda d: d['replicas'][7].update(mean_potential_kj_mol=float('nan')), 'output_schema')
run('boolean-id', lambda d: d['replicas'][0].update(replica=False), 'dropped_inputs')
run('work', lambda d: d.update(simulated_ns=0.7), 'fixed_work')
for metric, margin in [('mean_potential_kj_mol',43.55585000714341), ('final_potential_kj_mol',192.24836483013772)]:
    for sign in (-1,1):
        def disjoint(d, metric=metric, margin=margin, sign=sign):
            for r in d['replicas']:
                r[metric] += sign * margin * 2
        run(metric + str(sign), disjoint, 'equivalence', False)
    def overlap(d, metric=metric, margin=margin):
        for i,r in enumerate(d['replicas']):
            r[metric] += (0 if i == 0 else 5 * margin)
    run(metric + '-overlap', overlap, equivalent=True)
print('17 synthetic artifact checks passed')
