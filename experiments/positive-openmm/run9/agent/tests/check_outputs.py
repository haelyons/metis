"""Read representative output artifacts only; never invoke either workload."""
import json
import math
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
IDS = ['dropped_inputs', 'duplicated_inputs', 'ordering', 'tail_handling',
       'seeds', 'equivalence', 'output_schema', 'fixed_work']
cases = []


def add(name, ok, reason):
    cases.append({'id': name, 'pass': bool(ok), 'reason_code': None if ok else reason})


def finite(x, positive=False):
    return type(x) in (int, float) and math.isfinite(x) and (not positive or x > 0)


def strict_object(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError('duplicate JSON key')
        obj[key] = value
    return obj


def read(path):
    return json.loads(path.read_text(), object_pairs_hook=strict_object)


def median_bounds(differences, confidence, metric_count):
    """Exact symmetric binomial order-statistic interval, Bonferroni adjusted.

    For sorted n observations the kth and (n-k+1)th have coverage
    1 - 2*P(Binomial(n, .5) <= k-1). Use tightest qualifying interval.
    With n=8 and two metrics at joint .95 this selects min/max (.9921875).
    """
    ordered = sorted(differences)
    n = len(ordered)
    alpha = (1 - confidence) / metric_count
    candidates = [k for k in range(1, n // 2 + 1)
                  if 2 * sum(math.comb(n, j) for j in range(k)) / 2**n <= alpha]
    if not candidates:
        return -math.inf, math.inf
    k = max(candidates)
    return ordered[k - 1], ordered[n - k]


def check():
    seal = read(HERE / 'sealed_fixture.json')
    scale = seal['representative_scale']
    n = scale['replicas']
    expected = list(range(n))
    seeds = seal['paired_seed_tests']['seeds']
    metrics = seal['equivalence_metrics']
    outputs = []
    for variable, default in [('BASELINE_OUT', 'baseline-out'), ('METHOD_OUT', 'out')]:
        path = Path(os.environ.get(variable, default)) / 'run' / 'ensemble.json'
        try:
            data = read(path)
        except FileNotFoundError:
            for name in IDS:
                add(name, False, 'missing_output')
            return
        except (ValueError, OSError):
            for name in IDS:
                add(name, False, 'invalid_output')
            return
        outputs.append(data)

    # Both arms must implement the frozen baseline output interface.
    valid = all(isinstance(d, dict) and isinstance(d.get('replicas'), list)
                and all(isinstance(r, dict) for r in d['replicas']) for d in outputs)
    if not valid:
        for name in IDS:
            add(name, False, 'invalid_output')
        return
    replicas = [d['replicas'] for d in outputs]
    ids = [[r.get('replica') for r in rows] for rows in replicas]
    identities_valid = all(all(type(i) is int for i in values) for values in ids)
    complete = identities_valid and all(set(values) == set(expected) for values in ids)
    unique = identities_valid and all(len(values) == len(set(values)) for values in ids)
    ordered = all(values == expected for values in ids)
    add('dropped_inputs', complete and all(len(rows) >= n for rows in replicas), 'dropped_inputs')
    add('duplicated_inputs', unique, 'duplicated_inputs')
    add('ordering', ordered, 'ordering')

    # Preserve the fixed scale: inspect every actual output in ragged groups of
    # 3 and 5 (8 % 3 = 2, 8 % 5 = 3), including final input/seed 7/1007.
    # This detects missing/truncated suffixes without launching a new scale.
    tail = ordered
    for rows in replicas:
        for width in (3, 5):
            for start in range(0, n, width):
                group = rows[start:min(start + width, n)]
                tail = tail and len(group) == min(width, n - start)
                tail = tail and all(r.get('replica') == start + j
                                    and type(r.get('steps')) is int
                                    and r['steps'] == scale['steps_per_replica']
                                    and all(finite(r.get(m['name'])) for m in metrics)
                                    for j, r in enumerate(group))
    add('tail_handling', tail, 'tail_handling')
    seed_ok = complete and unique and all(
        len(rows) == n and all(type(r.get('seed')) is int
                              and r['seed'] == seeds[r['replica']]
                              for r in rows) for rows in replicas)
    add('seeds', seed_ok, 'seeds')
    schema = all(
        d.get('platform') == seal['inputs']['configuration']['platform']
        and d.get('properties') == seal['inputs']['configuration']['properties']
        and finite(d.get('total_wall_s'), True)
        and finite(d.get('simulated_ns'), True)
        and all(finite(r.get('wall_s'), True)
                and all(finite(r.get(m['name'])) for m in metrics) for r in d['replicas'])
        for d in outputs)
    add('output_schema', schema, 'invalid_output')
    work = all(len(d['replicas']) == n
               and all(type(r.get('steps')) is int and r['steps'] == scale['steps_per_replica']
                       for r in d['replicas'])
               and finite(d.get('simulated_ns'))
               and math.isclose(d['simulated_ns'], scale['total_simulated_ns'],
                                rel_tol=0, abs_tol=1e-12) for d in outputs)
    add('fixed_work', work, 'invalid_output')

    equivalent = unique and schema and identities_valid
    if equivalent:
        # One input, one observation per seed. Never use timing repetitions or
        # evaluation.json. Pair by input identity and seed, independently of order.
        input_id, = seal['input_ids']
        arms = [{(input_id, r['seed']): r for r in rows
                 if type(r.get('seed')) is int and r['seed'] in seeds
                 and r['replica'] in expected
                 and r['seed'] == seeds[r['replica']]} for rows in replicas]
        for metric in metrics:
            name, margin = metric['name'], metric['tolerance']['abs']
            differences = [arms[1][(input_id, seed)][name] - arms[0][(input_id, seed)][name]
                           for seed in seeds if (input_id, seed) in arms[0] and (input_id, seed) in arms[1]]
            lower, upper = median_bounds(differences, seal['confidence_rule']['confidence'], len(metrics))
            # Representative tests reject only disjoint intervals. Inconclusive
            # overlaps (including infinite bounds) pass; evaluate decides acceptance.
            if lower >= margin or upper <= -margin:
                equivalent = False
    add('equivalence', equivalent, 'equivalence')


try:
    check()
except Exception as exc:
    print('Output validation error: ' + str(exc), file=sys.stderr)
    cases = []
    for name in IDS:
        add(name, False, 'invalid_output')
report = {'passed': sum(c['pass'] for c in cases),
          'failed': sum(not c['pass'] for c in cases), 'cases': cases}
# Required report location is relative to the remote run directory.
Path('out').mkdir(parents=True, exist_ok=True)
Path('out/tests.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
sys.exit(1 if report['failed'] else 0)
