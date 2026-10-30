"""Output-only checks; no workloads, method sources, or evaluation records.

The seal is stochastic despite DeterministicForces=true. Seeds are checked
explicitly. Output records are also traversed in groups of three: eight has a
non-divisible two-record tail. This is a validator partition, not a new run or
a requirement on implementation concurrency. Raw samples are not exposed;
step metadata and final energies are the available completion evidence.
"""
import json
import math
import os
from pathlib import Path
import sys

CASES = ('missing_output', 'invalid_output', 'dropped_inputs',
         'duplicated_inputs', 'ordering', 'tail_handling', 'seeds',
         'upstream', 'equivalence')
results = {}


def record(name, passed, reason=None):
    results[name] = {'id': name, 'pass': bool(passed),
                     'reason_code': None if passed else (reason or name)}


def number(value, positive=False):
    return (type(value) in (int, float) and math.isfinite(value)
            and (not positive or value > 0))


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('Duplicate JSON key')
        obj[key] = value
    return obj


def load(path):
    if not path.is_file():
        raise FileNotFoundError(str(path))
    return json.loads(path.read_text(), object_pairs_hook=unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(
                          ValueError('Nonfinite JSON constant')))


def check():
    seal = load(Path(__file__).resolve().parent / 'sealed.json')
    baseline = load(Path(os.environ['BASELINE_OUT']) / 'ensemble.json')
    method = load(Path(os.environ['METHOD_OUT']) / 'ensemble.json')
    record('missing_output', True)
    scale = seal['representative_scale']
    count = scale['replicas']
    steps = scale['steps_per_replica']
    seeds = seal['paired_seed_tests']['seeds']
    metrics = seal['equivalence_metrics']
    assert seal['paired_seed_tests']['kind'] == 'paired_median'
    assert seal['outputs_stochastic'] is True
    assert len(seal['evaluation_inputs']['ids']) == 1
    assert len(seeds) == count

    def valid_schema(obj):
        if not isinstance(obj, dict) or not isinstance(obj.get('replicas'), list):
            return False
        if not all(k in obj for k in ('platform', 'properties', 'simulated_ns', 'total_wall_s')):
            return False
        for r in obj['replicas']:
            if not isinstance(r, dict):
                return False
            if not all(type(r.get(k)) is int for k in ('replica', 'seed', 'steps')):
                return False
            if not number(r.get('wall_s'), True):
                return False
            if not all(number(r.get(m['name'])) for m in metrics):
                return False
        return number(obj['total_wall_s'], True) and number(obj['simulated_ns'], True)

    if not valid_schema(baseline) or not valid_schema(method):
        for name in CASES[1:]:
            record(name, False, 'invalid_output')
        return
    record('invalid_output', True)
    br, mr = baseline['replicas'], method['replicas']
    expected = set(range(count))
    ids = [r['replica'] for r in mr]
    record('dropped_inputs', expected.issubset(ids) and set(seeds).issubset(r['seed'] for r in mr))
    record('duplicated_inputs', len(ids) == len(set(ids)) and
           len(mr) == len(set(r['seed'] for r in mr)))
    record('ordering', ids == list(range(count)))
    record('seeds', len(mr) == count and sorted(r['seed'] for r in mr) == seeds and
           all(r['replica'] in expected and r['seed'] == seeds[r['replica']] for r in mr))

    # Visit all records, including both records in the last partial group.
    groups = [mr[start:start + 3] for start in range(0, count, 3)]
    tail_ok = (len(mr) == count and len(groups[-1]) == count % 3 and
               all([r['replica'] for r in group] == list(range(start, min(start + 3, count)))
                   for start, group in zip(range(0, count, 3), groups)) and
               all(r['steps'] == steps and all(number(r[m['name']]) for m in metrics)
                   for group in groups for r in group) and
               mr[-1]['replica'] == count - 1 and mr[-1]['seed'] == seeds[-1])
    record('tail_handling', tail_ok)

    # Reuse output validation from harness/run_anchors.sh, without launching it.
    def upstream(obj):
        return (obj['platform'] == 'CUDA' and
                obj['properties'] == {'Precision': 'single', 'DeterministicForces': 'true'} and
                math.isclose(obj['simulated_ns'], scale['total_simulated_ns'],
                             rel_tol=0, abs_tol=1e-12) and
                len(obj['replicas']) == count and
                all((r['replica'], r['seed'], r['steps']) == (i, seeds[i], steps)
                    for i, r in enumerate(obj['replicas'])))
    record('upstream', upstream(baseline) and upstream(method))

    # Paired by (the single sealed molecular input, seed), never completion order.
    # Exact two-sided median CI, Bonferroni over the sealed two metrics.
    # A finite interval unavailable at this n is uninformative and cannot reject.
    if len({r['seed'] for r in br}) != len(br) or len({r['seed'] for r in mr}) != len(mr):
        record('equivalence', False, 'duplicated_inputs')
        return
    bmap = {r['seed']: r for r in br}
    mmap = {r['seed']: r for r in mr}
    paired = [seed for seed in seeds if seed in bmap and seed in mmap]
    n = len(paired)
    confidence = seal['confidence_rule']['equivalence']['confidence']
    alpha_metric = (1 - confidence) / len(metrics)
    ranks = [k for k in range(1, n // 2 + 1)
             if 2 * sum(math.comb(n, j) for j in range(k)) / (2 ** n) <= alpha_metric]
    equivalent = True
    if ranks:
        k = max(ranks)
        for metric in metrics:
            differences = sorted(mmap[s][metric['name']] - bmap[s][metric['name']] for s in paired)
            low, high = differences[k - 1], differences[n - k]
            margin = metric['tolerance']['abs']
            if low >= margin or high <= -margin:
                equivalent = False
    record('equivalence', equivalent)


try:
    check()
except FileNotFoundError:
    for name in CASES:
        record(name, False, 'missing_output')
except Exception as exc:
    print('Output validation error: ' + type(exc).__name__, file=sys.stderr)
    for name in CASES:
        if name not in results:
            record(name, False, 'invalid_output')
finally:
    for name in CASES:
        if name not in results:
            record(name, False, 'other')
    cases = [results[name] for name in CASES]
    passed = sum(c['pass'] for c in cases)
    report = {'passed': passed, 'failed': len(cases) - passed, 'cases': cases}
    target = Path('out/tests.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    sys.exit(1 if report['failed'] else 0)
