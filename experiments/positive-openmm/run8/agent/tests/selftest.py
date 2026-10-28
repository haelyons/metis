#!/usr/bin/env python3
"""Exercise output gates using synthetic interface fixtures, never workloads."""
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
seal = json.loads((HERE/'protocol.json').read_text())
frozen = json.loads((HERE.parent/'baseline-out/run/ensemble.json').read_text())
with tempfile.TemporaryDirectory(prefix='selftest.', dir=HERE) as temporary:
    root = Path(temporary)
    baseline, method = root/'baseline', root/'method'
    for arm in (baseline, method):
        (arm/'run').mkdir(parents=True)
        (arm/'run/ensemble.json').write_text(json.dumps(frozen))
        for budget in seal['compute_budgets']:
            for rep in range(32):
                records = []
                for seed in (2000, 2008, 2016, 2024):
                    metrics = {'simulated_ns': 0.8, 'total_wall_s': 60.0}
                    for i, row in enumerate(frozen['replicas']):
                        for key in ('wall_s', 'final_potential_kj_mol', 'mean_potential_kj_mol'):
                            metrics[f'replica_{i}_{key}'] = row[key]
                    records.append({'input_id':seal['evaluation_inputs']['ids'][0],
                                    'seed':seed, 'metrics':metrics})
                # Different serialized wall values distinguish genuine invocations
                # from the adapter's byte-identical session mirrors.
                doc = dict(records=records, compute_budget=budget, gpu_count=1,
                           timing_scope=seal['timing_scope'], wall_s=61 + rep/100)
                directory = arm/str(budget)/str(rep)
                directory.mkdir(parents=True)
                (directory/'evaluation.json').write_text(json.dumps(doc))
    env = dict(os.environ, BASELINE_OUT=str(baseline), METHOD_OUT=str(method))
    def run(expected=None):
        result = subprocess.run(['bash',str(HERE/'run_tests.sh')],cwd=root,env=env,check=False)
        report = json.loads((root/'out/tests.json').read_text())
        assert set(report)=={'passed','failed','cases'}
        assert report['failed']==sum(not x['pass'] for x in report['cases'])
        assert report['passed']+report['failed']==len(report['cases'])
        assert (result.returncode==0)==(report['failed']==0)
        if expected is None:
            assert result.returncode==0, report
        else:
            assert any(x['id']==expected and not x['pass'] for x in report['cases']), report
    run()
    mutations = {
        'dropped_inputs': lambda d:d['replicas'].pop(),
        'duplicated_inputs': lambda d:d['replicas'].__setitem__(7,copy.deepcopy(d['replicas'][6])),
        'ordering': lambda d:d['replicas'].reverse(),
        'tail_handling': lambda d:d['replicas'][7].__setitem__('steps',24750),
        'seeds': lambda d:d['replicas'][7].__setitem__('seed',1008),
        'output_schema': lambda d:d.__setitem__('total_wall_s',float('nan')),
    }
    for expected, mutate in mutations.items():
        doc=copy.deepcopy(frozen)
        mutate(doc)
        (method/'run/ensemble.json').write_text(json.dumps(doc))
        run(expected)
    (method/'run/ensemble.json').write_text(json.dumps(frozen))
    # All paired differences outside the exact margin must fail; no pooling
    # across budgets or repeated timings as extra scientific seeds.
    for path in (method/'120').rglob('evaluation.json'):
        doc=json.loads(path.read_text())
        for row in doc['records']:
            for i in range(8):
                row['metrics'][f'replica_{i}_mean_potential_kj_mol'] += 124
        path.write_text(json.dumps(doc))
    run('equivalence')
    for path in (method/'240').rglob('evaluation.json'):
        path.unlink()
        break
    run('equivalence')
print('Output gate self-tests passed.')
