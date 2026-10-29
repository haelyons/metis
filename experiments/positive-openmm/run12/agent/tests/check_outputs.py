"""Output-only fixed-scale checks. Never import or execute either implementation.

Only the published JSON summaries are observable. The tail check covers the
last two replicas in a logical partition of eight by three, without changing
work or claiming to observe internal worker batches or unrecorded samples.
No upstream fixed-work output test exists; stdout/config checks below reuse
harness/run_anchors.sh validations without running its workload command.
"""
import json
import math
import os
from pathlib import Path
import re
import sys

IDS = ['dropped_inputs', 'duplicated_inputs', 'ordering', 'tail_handling',
       'seeds', 'equivalence', 'output_schema', 'configuration', 'stdout']
cases = []


def add(name, ok, reason):
    cases.append({'id': name, 'pass': bool(ok),
                  'reason_code': None if ok else reason})


def number(x):
    return type(x) in (int, float) and math.isfinite(x)


def integer(x):
    return type(x) is int


def no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def load(path):
    return json.loads(path.read_text(), object_pairs_hook=no_duplicates,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def rows_valid(doc):
    if not isinstance(doc, dict) or not isinstance(doc.get('replicas'), list):
        return False
    for row in doc['replicas']:
        if not isinstance(row, dict):
            return False
        if not all(integer(row.get(k)) for k in ('replica', 'seed', 'steps')):
            return False
        if not all(number(row.get(k)) for k in
                   ('wall_s', 'final_potential_kj_mol', 'mean_potential_kj_mol')):
            return False
        if row['wall_s'] <= 0:
            return False
    return (number(doc.get('total_wall_s')) and doc['total_wall_s'] > 0
            and number(doc.get('simulated_ns')))


def median_interval(differences, confidence, metrics):
    # Central exact binomial CI, with Bonferroni across metrics. For n=8,
    # k=1 gives [min,max], coverage 1-2/256=0.9921875 >= 0.975.
    n = len(differences)
    tail = (1 - confidence) / (2 * metrics)
    ranks = [k for k in range(1, (n + 1)//2 + 1)
             if sum(math.comb(n, j) for j in range(k)) / 2**n <= tail]
    if not ranks:
        return -math.inf, math.inf  # insufficient pairs cannot reject
    k = max(ranks)
    ordered = sorted(differences)
    return ordered[k-1], ordered[n-k]


def check():
    seal = load(Path(__file__).with_name('seal.json'))
    execution = seal['execution']
    scale = execution['representative_scale']
    config = execution['inputs']['configuration']
    seeds = seal['paired_seed_tests']['seeds']
    count = scale['replicas']
    expected = list(range(count))
    documents = []
    roots = []
    for env in ('BASELINE_OUT', 'METHOD_OUT'):
        root = Path(os.environ[env])
        roots.append(root)
        # Both arms use the frozen published output layout; no recursive search
        # that might accidentally use evaluation records or stale runs.
        documents.append(load(root / 'baseline-run' / 'ensemble.json'))
    schema = all(rows_valid(d) for d in documents)
    if not schema:
        for name in IDS:
            add(name, False, 'invalid_output')
        return
    records = [d['replicas'] for d in documents]
    add('dropped_inputs', all(set(expected) <= {r['replica'] for r in rows}
                             for rows in records), 'dropped_inputs')
    add('duplicated_inputs', all(len(rows) == count
        and len({r['replica'] for r in rows}) == len(rows)
        and len({r['seed'] for r in rows}) == len(rows) for rows in records),
        'duplicated_inputs')
    add('ordering', all([r['replica'] for r in rows] == expected
                        for rows in records), 'ordering')
    # Explicitly inspect every full logical chunk and the non-divisible tail,
    # including the final input. No altered-scale method run is needed.
    chunks = [expected[i:i+3] for i in range(0, count, 3)]
    add('tail_handling', all(len(rows) == count
        and all([r['replica'] for r in rows[i*3:i*3+len(chunk)]] == chunk
                and all(r['steps'] == scale['steps_per_replica']
                        for r in rows[i*3:i*3+len(chunk)])
                for i, chunk in enumerate(chunks))
        and rows[-1]['replica'] == expected[-1]
        and rows[-1]['seed'] == seeds[-1] for rows in records), 'tail_handling')
    paired = all(len(rows) == count and
        sorted((r['replica'], r['seed']) for r in rows) == list(zip(expected, seeds))
        for rows in records)
    add('seeds', paired, 'seeds')
    add('output_schema', True, 'invalid_output')
    add('configuration', all(d.get('platform') == config['platform']
        and d.get('properties') == config['properties']
        and d['simulated_ns'] == scale['simulated_ns']
        and all(r['steps'] == scale['steps_per_replica'] for r in d['replicas'])
        for d in documents), 'invalid_output')
    if paired:
        # The sole input ID is implicit in the fixed baseline-run output path;
        # join replicas by identity and seed, never by list position or value.
        maps = [{(r['replica'], r['seed']): r for r in rows} for rows in records]
        metrics = seal['equivalence_metrics']
        equivalent = True
        for metric in metrics:
            name = metric['name']
            differences = [maps[1][key][name] - maps[0][key][name]
                           for key in maps[0]]
            if not all(math.isfinite(x) for x in differences):
                add('equivalence', False, 'invalid_output')
                break
            lo, hi = median_interval(differences,
                seal['confidence_rule']['equivalence']['confidence'], len(metrics))
            margin = metric['tolerance']['abs']
            equivalent &= not (hi <= -margin or lo >= margin)
        else:
            add('equivalence', equivalent, 'equivalence')
    else:
        add('equivalence', False, 'seeds')
    stdout_ok = True
    for root, d in zip(roots, documents):
        log = (root / 'baseline.stdout.log').read_text()
        for key, value, tolerance in (
                ('total_wall_s', d['total_wall_s'], .00051),
                ('aggregate_ns_per_day', d['simulated_ns']/d['total_wall_s']*86400, .051)):
            matches = re.findall(r'^'+key+r': ([0-9.eE+\-]+)$', log, re.M)
            stdout_ok &= bool(matches) and math.isfinite(float(matches[-1])) and math.isclose(
                float(matches[-1]), value, abs_tol=tolerance)
    add('stdout', stdout_ok, 'upstream')


def main():
    try:
        check()
    except Exception as exc:
        reason = 'missing_output' if isinstance(exc, (FileNotFoundError, KeyError)) else 'invalid_output'
        print('Output validation error: ' + str(exc), file=sys.stderr)
        for name in IDS:
            if name not in {c['id'] for c in cases}:
                add(name, False, reason)
    passed = sum(c['pass'] for c in cases)
    report = {'passed': passed, 'failed': len(cases)-passed, 'cases': cases}
    target = Path('out/tests.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    return int(report['failed'] > 0)


if __name__ == '__main__':
    sys.exit(main())
