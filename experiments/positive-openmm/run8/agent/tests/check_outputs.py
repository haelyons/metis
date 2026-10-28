#!/usr/bin/env python3
"""Independent output checks. No OpenMM import, GPU access, or source execution.

The published interface persists final/mean summaries, not energy series. Thus
step/sample coverage is checkable only through reported work and the final
summary. No full trajectory identity is claimed. The sealed scale is unchanged;
100 samples have a four-sample remainder when partitioned into eight lanes.
Upstream simulation tests require source execution/GPU access and cannot serve
as output-only gates here. Scientific inference uses held-out outputs only.
"""
import hashlib
import json
import math
import os
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
SEAL = json.loads((HERE / 'protocol.json').read_text())
CASES = []


def case(name, passed, reason):
    CASES.append(dict(id=name, pass_=bool(passed), reason_code=None if passed else reason))


def finite(x, positive=False):
    return type(x) in (int, float) and math.isfinite(x) and (not positive or x > 0)


def load(path):
    def pairs(items):
        d = {}
        for k, v in items:
            if k in d:
                raise ValueError('duplicate JSON key')
            d[k] = v
        return d
    return json.loads(path.read_text(), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def ensemble(root):
    for relative in ('run/ensemble.json', 'ensemble.json'):
        path = root / relative
        if path.is_file():
            return load(path)
    raise FileNotFoundError('ensemble.json')


def valid_replica(r):
    return (isinstance(r, dict) and type(r.get('replica')) is int
            and type(r.get('seed')) is int and type(r.get('steps')) is int
            and r['steps'] == 25000 and finite(r.get('wall_s'), True)
            and all(finite(r.get(k)) for k in METRICS))


METRICS = {m['name']: m['tolerance']['abs'] for m in SEAL['equivalence_metrics']}


def observations(root):
    """Consume the supplied evaluation adapter's serialized records.

    Its session copy may mirror EVAL_OUT. Ignore byte-identical mirrors, never
    count one invocation twice. Every budget/group needs all 32 repetitions.
    No calibration output substitutes for a held-out observation.
    """
    values = {b: {s: {k: [] for k in METRICS} for s in range(2000, 2032)}
              for b in SEAL['compute_budgets']}
    counts = {b: {s: 0 for s in (2000, 2008, 2016, 2024)} for b in values}
    seen = set()
    for path in sorted(root.rglob('evaluation.json')):
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).digest()
        if digest in seen:
            continue
        seen.add(digest)
        doc = load(path)
        budget = doc.get('compute_budget')
        if budget is None:  # warmup/performance/equivalence adapter invocations
            continue
        if type(budget) not in (int, float) or budget not in values:
            raise ValueError('unexpected budget')
        if (doc.get('gpu_count') != 1 or not finite(doc.get('wall_s'), True)
                or doc['wall_s'] > budget or doc.get('timing_scope') != SEAL['timing_scope']):
            raise ValueError('invalid or censored observation')
        records = doc['records']
        if not isinstance(records, list) or not records:
            raise ValueError('empty observation')
        groups = set()
        for record in records:
            start = record['seed']
            if (type(start) is not int or start not in counts[budget] or start in groups
                    or record['input_id'] != SEAL['evaluation_inputs']['ids'][0]):
                raise ValueError('unexpected or duplicate group')
            groups.add(start)
            metrics = record['metrics']
            if metrics.get('simulated_ns') != 0.8 or not finite(metrics.get('total_wall_s'), True):
                raise ValueError('invalid fixed work')
            for i in range(8):
                if not finite(metrics.get(f'replica_{i}_wall_s'), True):
                    raise ValueError('missing replica')
                for k in METRICS:
                    v = metrics[f'replica_{i}_{k}']
                    if not finite(v):
                        raise ValueError('invalid energy')
                    values[budget][start+i][k].append(v)
            counts[budget][start] += 1
    if any(n != SEAL['repetitions'] for groups in counts.values() for n in groups.values()):
        raise FileNotFoundError('complete sealed paired repetitions unavailable')
    return values


def main():
    method = Path(os.environ['METHOD_OUT'])
    baseline = Path(os.environ['BASELINE_OUT'])
    try:
        m = ensemble(method)
        b = ensemble(baseline)
        rows = m.get('replicas')
        if not isinstance(rows, list) or not isinstance(b.get('replicas'), list):
            raise ValueError('invalid replicas')
    except FileNotFoundError:
        for name in ('dropped_inputs', 'duplicated_inputs', 'ordering', 'tail_handling', 'seeds', 'equivalence', 'output_schema'):
            case(name, False, 'missing_output')
        return
    except (ValueError, TypeError, KeyError):
        for name in ('dropped_inputs', 'duplicated_inputs', 'ordering', 'tail_handling', 'seeds', 'equivalence', 'output_schema'):
            case(name, False, 'invalid_output')
        return
    ids = [r.get('replica') if isinstance(r, dict) else None for r in rows]
    seeds = [r.get('seed') if isinstance(r, dict) else None for r in rows]
    case('dropped_inputs', all(i in ids for i in range(8)), 'dropped_inputs')
    case('duplicated_inputs', len(rows) == 8 and len(set(ids)) == 8
         and len(set(seeds)) == 8, 'duplicated_inputs')
    case('ordering', ids == list(range(8)), 'ordering')
    case('tail_handling', len(rows) == 8 and all(valid_replica(r) for r in rows)
         and ids[-1:] == [7] and seeds[-1:] == [1007]
         and sum(r['steps'] for r in rows) == 200000
         and m.get('simulated_ns') == 0.8, 'tail_handling')
    case('seeds', seeds == list(range(1000, 1008))
         and seeds == [r.get('seed') for r in b['replicas']], 'seeds')
    case('output_schema', all(valid_replica(r) for r in rows)
         and m.get('platform') == 'CUDA'
         and m.get('properties') == {'Precision': 'single', 'DeterministicForces': 'true'}
         and finite(m.get('total_wall_s'), True), 'invalid_output')
    try:
        bv, mv = observations(baseline), observations(method)
        good = True
        lo, hi = SEAL['confidence_rule']['equivalence_order_statistic_ranks']
        for budget in SEAL['compute_budgets']:
            for metric, margin in METRICS.items():
                diffs = sorted(median(mv[budget][s][metric]) - median(bv[budget][s][metric])
                               for s in SEAL['paired_seed_tests']['seeds'])
                passed = -margin < diffs[lo-1] and diffs[hi-1] < margin
                case(f'equivalence_{budget}_{metric}', passed, 'equivalence')
                good = good and passed
        case('equivalence', good, 'equivalence')
    except FileNotFoundError:
        case('equivalence', False, 'missing_output')
    except (ValueError, KeyError, TypeError):
        case('equivalence', False, 'invalid_output')


if __name__ == '__main__':
    try:
        main()
    except Exception:
        case('output_inspection', False, 'invalid_output')
    finally:
        # Keep required cases present even after unexpected malformed output.
        for name in ('dropped_inputs', 'duplicated_inputs', 'ordering', 'tail_handling', 'seeds', 'equivalence', 'output_schema'):
            if not any(c['id'] == name for c in CASES):
                case(name, False, 'invalid_output')
        cases = [dict(id=c['id'], **{'pass': c['pass_']}, reason_code=c['reason_code']) for c in CASES]
        failed = sum(not c['pass'] for c in cases)
        report = dict(passed=len(cases)-failed, failed=failed, cases=cases)
        out = Path('out')
        out.mkdir(parents=True, exist_ok=True)
        (out / 'tests.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    raise SystemExit(bool(failed))
