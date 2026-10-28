"""Gate verification using only frozen baseline and synthetic corruptions."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
from check_outputs import check, HERE, SPEC

base = json.loads((HERE / 'baseline_fixture.json').read_text())
assert all(c['pass'] for c in check(base, base))


def rejects(data, case):
    cases = {c['id']: c for c in check(base, data)}
    assert not cases[case]['pass'], case


for i in range(8):
    p = copy.deepcopy(base)
    del p['replicas'][i]
    rejects(p, 'dropped_inputs')
    rejects(p, 'tail_handling')
    p = copy.deepcopy(base)
    p['replicas'][i] = copy.deepcopy(p['replicas'][(i+1) % 8])
    rejects(p, 'duplicated_inputs')
    rejects(p, 'seeds')
p = copy.deepcopy(base)
p['replicas'].reverse()
rejects(p, 'ordering')
for key, margin in SPEC['margins'].items():
    for i in range(8):
        for sign in (-1, 1):
            p = copy.deepcopy(base)
            p['replicas'][i][key] += sign * margin * 1.001
            rejects(p, 'equivalence')
    p = copy.deepcopy(base)
    for r in p['replicas']:
        r[key] += margin * 0.99
    assert all(c['pass'] for c in check(base, p))
p = copy.deepcopy(base)
p['replicas'][-1]['steps'] = 24750
rejects(p, 'tail_handling')
for value in (float('nan'), float('inf'), True, '0', None):
    p = copy.deepcopy(base)
    p['replicas'][-1]['final_potential_kj_mol'] = value
    rejects(p, 'output_contract')
    rejects(p, 'equivalence')
p = copy.deepcopy(base)
p['replicas'][-1]['seed'] = 1008
rejects(p, 'seeds')

# Exercise the actual shell entry point, report schema and failure exit codes.
work = HERE / 'validation'
(work / 'candidate/run').mkdir(parents=True, exist_ok=True)
(work / 'baseline/run').mkdir(parents=True, exist_ok=True)
(work / 'baseline/run/ensemble.json').write_text(json.dumps(base))
env = dict(os.environ, BASELINE_OUT=str(work/'baseline'), METHOD_OUT=str(work/'candidate'),
           PYTHONDONTWRITEBYTECODE='1')
for mutation in ('valid', 'missing', 'malformed', 'duplicate_key', 'tail'):
    output = work/'candidate/run/ensemble.json'
    output.unlink(missing_ok=True)
    if mutation == 'valid':
        output.write_text(json.dumps(base))
    elif mutation == 'malformed':
        output.write_text('{')
    elif mutation == 'duplicate_key':
        output.write_text('{"replicas": [], "replicas": []}')
    elif mutation == 'tail':
        p = copy.deepcopy(base)
        p['replicas'].pop()
        output.write_text(json.dumps(p))
    result = subprocess.run(['bash', str(HERE/'run_tests.sh')], cwd=work, env=env,
                            timeout=10, check=False)
    report = json.loads((work/'out/tests.json').read_text())
    assert set(report) == {'passed','failed','cases'}
    assert report['passed'] == sum(c['pass'] for c in report['cases'])
    assert report['failed'] == sum(not c['pass'] for c in report['cases'])
    assert len({c['id'] for c in report['cases']}) == len(report['cases'])
    assert (result.returncode == 0) == (mutation == 'valid')
    assert all(set(c) == {'id','pass','reason_code'} for c in report['cases'])
    assert all(type(c['pass']) is bool and (c['reason_code'] is None) == c['pass']
               for c in report['cases'])
# Leave a passing local validation report, clearly using the baseline fixture.
(work/'candidate/run/ensemble.json').write_text(json.dumps(base))
subprocess.run(['bash', str(HERE/'run_tests.sh')], cwd=work, env=env,
               timeout=10, check=True)
print('Output gate self-tests passed.')
