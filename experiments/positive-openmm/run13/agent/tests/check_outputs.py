"""Read representative output data only; never import either implementation."""
import json
import math
import os
import re
import sys
from pathlib import Path

SEEDS = list(range(1000, 1008))
METRICS = {
    'mean_potential_kj_mol': 38.64607384469149,
    'final_potential_kj_mol': 103.46087706490006,
}
IDS = ['dropped_inputs', 'duplicated_inputs', 'ordering', 'tail_handling',
       'seeds', 'equivalence', 'output_schema', 'fixed_work', 'upstream_output']

class OutputError(Exception):
    def __init__(self, code):
        self.code = code


def reject_constant(_):
    raise OutputError('invalid_output')


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise OutputError('invalid_output')
        result[key] = value
    return result


def load(root):
    # Both published harness nesting and direct ensemble.json are supported.
    # Do not read evaluation records, scripts, or arbitrary JSON files.
    root = Path(root)
    direct = root / 'ensemble.json'
    candidates = [direct] if direct.is_file() else sorted(root.glob('*/ensemble.json'))
    if not candidates:
        raise OutputError('missing_output')
    if len(candidates) != 1:
        raise OutputError('invalid_output')
    path = candidates[0]
    try:
        obj = json.loads(path.read_text(), parse_constant=reject_constant,
                         object_pairs_hook=unique_keys)
        if not isinstance(obj, dict) or not isinstance(obj.get('replicas'), list):
            raise OutputError('invalid_output')
        if not all(isinstance(r, dict) for r in obj['replicas']):
            raise OutputError('invalid_output')
        return obj, path.parent
    except OutputError:
        raise
    except (OSError, ValueError, TypeError):
        raise OutputError('invalid_output')


def number(value, positive=False):
    return (type(value) in (int, float) and math.isfinite(value)
            and (not positive or value > 0))


def identity(r):
    return (type(r.get('replica')) is int and type(r.get('seed')) is int)


def median_interval(differences):
    """Exact sign/order-statistic CI; Bonferroni over the two sealed metrics."""
    n = len(differences)
    # P(Binomial(n,.5) <= k-1) <= .05 / (2 metrics * 2 tails).
    valid = [k for k in range(1, n // 2 + 1)
             if sum(math.comb(n, j) for j in range(k)) / (2 ** n) <= 0.0125]
    if not valid:
        return -math.inf, math.inf
    k = max(valid)
    ordered = sorted(differences)
    return ordered[k-1], ordered[n-k]


def equivalence(base, method):
    # Pair by scientific identity, not by completion position. Missing/duplicate
    # identities are rejected by their own cases, never counted as extra pairs.
    def keyed(rows):
        groups = {}
        for row in rows:
            if identity(row) and (row['replica'], row['seed']) in expected:
                groups.setdefault((row['replica'], row['seed']), []).append(row)
        return {key: rows[0] for key, rows in groups.items() if len(rows) == 1}
    expected = set(enumerate(SEEDS))
    b, m = keyed(base), keyed(method)
    for metric, margin in METRICS.items():
        differences = []
        for key in sorted(b.keys() & m.keys()):
            if not number(b[key].get(metric)) or not number(m[key].get(metric)):
                raise OutputError('invalid_output')
            difference = m[key][metric] - b[key][metric]
            if not math.isfinite(difference):
                raise OutputError('invalid_output')
            differences.append(difference)
        lo, hi = median_interval(differences)
        # Only disjointness from the OPEN margin interval rejects here.
        # Overlap or too few pairs passes; evaluate decides acceptance.
        if hi <= -margin or lo >= margin:
            return False
    return True


def check(base, method, directory):
    rows = method['replicas']
    expected = set(enumerate(SEEDS))
    pairs = [(r['replica'], r['seed']) for r in rows if identity(r)]
    indices = [r.get('replica') for r in rows]
    seeds = [r.get('seed') for r in rows]
    result = {}
    result['dropped_inputs'] = expected.issubset(set(pairs))
    result['duplicated_inputs'] = (len(rows) == 8 and len(pairs) == len(set(pairs))
        and len(set(i for i, _ in pairs)) == len(pairs)
        and len(set(s for _, s in pairs)) == len(pairs))
    result['ordering'] = (all(identity(r) for r in rows)
                          and indices == list(range(8)) and seeds == SEEDS)
    result['seeds'] = (len(rows) == 8 and all(identity(r) for r in rows)
                       and set(pairs) == expected)
    # Examine the suffix after two full groups of three: the representative
    # eight-record output has a two-record remainder and includes final seed 1007.
    # This asserts output coverage, not unobservable internal scheduler behavior.
    result['tail_handling'] = (len(rows) == 8 and all(
        identity(rows[i]) and (rows[i]['replica'], rows[i]['seed']) == (i, SEEDS[i])
        and type(rows[i].get('steps')) is int and rows[i]['steps'] == 25000
        and all(number(rows[i].get(metric)) for metric in METRICS)
        for i in range(6, 8)))
    result['output_schema'] = (
        method.get('platform') == 'CUDA'
        and method.get('properties') == {'Precision': 'single', 'DeterministicForces': 'true'}
        and number(method.get('total_wall_s'), True)
        and all(identity(r) and number(r.get('wall_s'), True)
                and all(number(r.get(metric)) for metric in METRICS) for r in rows))
    result['fixed_work'] = (number(method.get('simulated_ns'))
        and method['simulated_ns'] == 0.8 and len(rows) == 8
        and all(type(r.get('steps')) is int and r['steps'] == 25000 for r in rows))
    # Reuse the non-executing stdout consistency checks from run_anchors.sh.
    result['upstream_output'] = False
    try:
        stdout = (directory / 'stdout.log').read_text()
        total = method['total_wall_s']
        if number(total, True):
            values = {'total_wall_s': (total, 3),
                      'aggregate_ns_per_day': (0.8 * 86400 / total, 1)}
            result['upstream_output'] = all(
                len(matches := re.findall(r'^' + key + r': ([0-9.eE+\-]+)$', stdout, re.M)) == 1
                and number(float(matches[0]))
                and abs(float(matches[0]) - value) <= 0.51 * 10**(-decimals)
                for key, (value, decimals) in values.items())
    except (OSError, KeyError, ValueError, TypeError):
        pass
    try:
        result['equivalence'] = equivalence(base['replicas'], rows)
    except OutputError as exc:
        result['equivalence'] = exc.code
    return [{'id': key, 'pass': result[key] is True,
             'reason_code': None if result[key] is True else
             (result[key] if isinstance(result[key], str) else
              {'output_schema': 'invalid_output', 'fixed_work': 'invalid_output',
               'upstream_output': 'upstream'}.get(key, key))} for key in IDS]


def main():
    method_root = Path(os.environ.get('METHOD_OUT', 'out'))
    try:
        base, _ = load(os.environ['BASELINE_OUT'])
        method, directory = load(method_root)
        cases = check(base, method, directory)
    except Exception as exc:
        code = exc.code if isinstance(exc, OutputError) else 'invalid_output'
        cases = [{'id': key, 'pass': False, 'reason_code': code} for key in IDS]
    report = {'passed': sum(c['pass'] for c in cases),
              'failed': sum(not c['pass'] for c in cases), 'cases': cases}
    method_root.mkdir(parents=True, exist_ok=True)
    (method_root / 'tests.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    return int(report['failed'] != 0)

if __name__ == '__main__':
    sys.exit(main())
