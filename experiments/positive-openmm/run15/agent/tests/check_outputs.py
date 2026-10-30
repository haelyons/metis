"""Read only canonical output artifacts. Never import or execute either driver."""
import json
import math
import os
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
CASE_IDS = ('output_schema', 'dropped_inputs', 'duplicated_inputs', 'ordering',
            'tail_handling', 'seeds', 'equivalence', 'upstream')


def finite(x):
    return type(x) in (int, float) and math.isfinite(x)


def strict_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    return json.loads(path.read_text(), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def median_interval(values, confidence, metric_count):
    """Exact equal-tail sign/order-statistic CI, Bonferroni over metrics.

    For sorted n observations, [x[k-1], x[n-k]] has tail probability
    P(Binomial(n,.5) <= k-1). No finite bound exists if k=1 is too large.
    """
    n = len(values)
    tail_alpha = (1 - confidence) / (2 * metric_count)
    eligible = [k for k in range(1, (n + 1) // 2 + 1)
                if sum(math.comb(n, j) for j in range(k)) / 2**n <= tail_alpha]
    if not eligible:
        return -math.inf, math.inf
    k = max(eligible)
    ordered = sorted(values)
    return ordered[k - 1], ordered[n - k]


def assess(base, method, seal, logs):
    results = []
    def case(name, ok, reason):
        results.append({'id': name, 'pass': bool(ok),
                        'reason_code': None if ok else reason})
    config = seal['configuration']
    seeds = seal['paired_seed_tests']['seeds']
    count, steps = config['replicas'], config['steps_per_replica']
    metrics = seal['equivalence_metrics']
    fields = ('wall_s',) + tuple(m['name'] for m in metrics)
    schema = True
    for output in (base, method):
        schema &= isinstance(output, dict)
        if not isinstance(output, dict):
            continue
        schema &= (output.get('platform') == 'CUDA' and
                   output.get('properties') == {'Precision': 'single', 'DeterministicForces': 'true'} and
                   finite(output.get('simulated_ns')) and output['simulated_ns'] == 0.8 and
                   finite(output.get('total_wall_s')) and output['total_wall_s'] > 0)
        rows = output.get('replicas')
        schema &= isinstance(rows, list)
        if not isinstance(rows, list):
            continue
        for row in rows:
            schema &= (isinstance(row, dict) and
                       all(type(row.get(k)) is int for k in ('replica', 'seed', 'steps')) and
                       all(finite(row.get(k)) for k in fields) and row.get('wall_s', 0) > 0)
    case('output_schema', schema, 'invalid_output')
    if not schema:
        for name in CASE_IDS[1:]:
            case(name, False, 'invalid_output')
        return results

    collections = [output['replicas'] for output in (base, method)]
    case('dropped_inputs', all(set(range(count)) <= {r['replica'] for r in rows}
                               and set(seeds) <= {r['seed'] for r in rows}
                               for rows in collections), 'dropped_inputs')
    case('duplicated_inputs', all(len(rows) == count and
                                   len({r['replica'] for r in rows}) == len(rows) and
                                   len({r['seed'] for r in rows}) == len(rows)
                                   for rows in collections), 'duplicated_inputs')
    case('ordering', all([r['replica'] for r in rows] == list(range(count))
                         for rows in collections), 'ordering')
    # Inspect all fixed-work records in windows of three: 8 = 3+3+2.
    # This includes the non-divisible final window and final seed explicitly;
    # it does not change workload size or claim access to internal energy series.
    tail_ok = True
    for rows in collections:
        tail_ok &= len(rows) == count
        for start in range(0, count, 3):
            window = rows[start:min(start + 3, count)]
            tail_ok &= len(window) == min(3, count - start)
            tail_ok &= all(r['replica'] == i and r['seed'] == seeds[i] and
                           r['steps'] == steps for i, r in enumerate(window, start))
        tail_ok &= bool(rows) and rows[-1]['replica'] == count - 1 and rows[-1]['steps'] == steps
        tail_ok &= sum(r['steps'] for r in rows) == seal['representative_scale']['steps_total']
    case('tail_handling', tail_ok, 'tail_handling')
    seed_ok = all([r['seed'] for r in rows] == seeds and
                  all(r['seed'] == config['seed0'] + r['replica'] for r in rows)
                  for rows in collections)
    case('seeds', seed_ok, 'seeds')

    # One published input; pair by (input_id, seed), never by completion position.
    input_id, = seal['input_ids']
    keyed = [{(input_id, r['seed']): r for r in rows} for rows in collections]
    identities = {(input_id, seed) for seed in seeds}
    paired = (all(set(k) == identities and len(rows) == count
                  for k, rows in zip(keyed, collections)) and seed_ok)
    equivalent = paired
    if paired:
        for metric in metrics:
            name, margin = metric['name'], metric['tolerance']['abs']
            differences = [keyed[1][key][name] - keyed[0][key][name]
                           for key in sorted(identities)]
            lo, hi = median_interval(differences,
                                     seal['confidence_rule']['equivalence']['confidence'],
                                     len(metrics))
            # Reject only disjointness from the OPEN allowed interval.
            equivalent &= not (hi <= -margin or lo >= margin)
    case('equivalence', equivalent, 'equivalence')

    # Reuse the artifact-only validation from harness/run_anchors.sh.
    upstream = True
    for output, log in zip((base, method), logs):
        wall = output['total_wall_s']
        for name, expected in (('total_wall_s', float(f'{wall:.3f}')),
                               ('aggregate_ns_per_day', float(f'{0.8 / wall * 86400:.1f}'))):
            matches = re.findall(r'^' + name + r':\s*(\S+)\s*$', log, re.M)
            try:
                upstream &= len(matches) == 1 and float(matches[0]) == expected
            except (ValueError, OverflowError):
                upstream = False
    case('upstream', upstream, 'upstream')
    return results


def main():
    # Report path is independent of output environment validity.
    report = Path('out/tests.json')
    results = []
    try:
        seal = strict_json(HERE / 'seal.json')
        roots = [Path(os.environ[name]) for name in ('BASELINE_OUT', 'METHOD_OUT')]
        outputs = [strict_json(root / 'run/ensemble.json') for root in roots]
        logs = [(root / 'run/baseline.log').read_text() for root in roots]
        results = assess(*outputs, seal, logs)
    except Exception as exc:
        reason = 'missing_output' if isinstance(exc, (FileNotFoundError, KeyError)) else 'invalid_output'
        results = [{'id': name, 'pass': False, 'reason_code': reason} for name in CASE_IDS]
        print(f'Output validation failed: {type(exc).__name__}: {exc}', file=sys.stderr)
    passed = sum(case['pass'] for case in results)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({'passed': passed, 'failed': len(results) - passed,
                                  'cases': results}, allow_nan=False, indent=2) + '\n')
    return int(passed != len(results))


if __name__ == '__main__':
    sys.exit(main())
