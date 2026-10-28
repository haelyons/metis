"""Independent fixed-work output gate. No simulation or candidate code execution."""
import json
import math
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SPEC = json.loads((HERE / 'sealed.json').read_text())
IDS = ['dropped_inputs', 'duplicated_inputs', 'ordering', 'tail_handling',
       'seeds', 'equivalence', 'output_contract', 'upstream']


def finite(x, positive=False):
    return (type(x) in (int, float) and math.isfinite(x)
            and (not positive or x > 0))


def load(path):
    def unique(pairs):
        obj = {}
        for k, v in pairs:
            if k in obj:
                raise ValueError('duplicate JSON key')
            obj[k] = v
        return obj
    return json.loads(path.read_text(), object_pairs_hook=unique,
                      parse_constant=lambda s: (_ for _ in ()).throw(ValueError(s)))


def check(base, method):
    results = []

    def add(id, ok, reason=None):
        results.append(dict(id=id, pass_=bool(ok), reason_code=None if ok else reason or id))

    def valid_record(r):
        return (isinstance(r, dict)
                and all(type(r.get(k)) is int for k in ('replica', 'seed', 'steps'))
                and r['steps'] == SPEC['steps']
                and finite(r.get('wall_s'), True)
                and all(finite(r.get(k)) for k in SPEC['margins']))

    def contract(p):
        return (isinstance(p, dict) and p.get('platform') == 'CUDA'
                and p.get('properties') == {'Precision': 'single', 'DeterministicForces': 'true'}
                and type(p.get('simulated_ns')) in (int, float)
                and p['simulated_ns'] == SPEC['simulated_ns']
                and finite(p.get('total_wall_s'), True)
                and isinstance(p.get('replicas'), list)
                and len(p['replicas']) == 8 and all(valid_record(r) for r in p['replicas']))

    # Frozen baseline is validated too, so corrupt/misconfigured references fail closed.
    base_ok = contract(base)
    rows = method.get('replicas', []) if isinstance(method, dict) else []
    if not isinstance(rows, list):
        rows = []
    expected = [(i, s) for i, s in enumerate(SPEC['seeds'])]
    identities = [(r.get('replica'), r.get('seed')) if isinstance(r, dict)
                  else (None, None) for r in rows]
    typed = all(isinstance(r, dict) and type(r.get('replica')) is int
                and type(r.get('seed')) is int for r in rows)
    add('dropped_inputs', typed and all(pair in identities for pair in expected))
    add('duplicated_inputs', typed and len(rows) == 8
        and len(set(identities)) == len(identities))
    add('ordering', typed and identities == expected)
    # Fixed scale must not be changed to manufacture another workload. Exercise
    # non-divisible views of the actual eight records (3, 5, 7), including final
    # seed 1007 and its final-step energy; these are inspection windows only,
    # not claims about the candidate's private dispatch width or energy series.
    tails = typed and len(rows) == 8
    for width in (3, 5, 7):
        for start in range(0, 8, width):
            chunk = rows[start:start + width]
            tails = tails and len(chunk) == min(width, 8-start)
            for offset, r in enumerate(chunk):
                i = start + offset
                tails = tails and valid_record(r) and identities[i] == expected[i]
    add('tail_handling', tails)
    # Seal declares stochastic outputs, despite DeterministicForces=true.
    # Require the exact fixed paired seed list, never a deterministic exemption.
    base_ids = [(r.get('replica'), r.get('seed')) for r in base['replicas']] if base_ok else []
    paired = base_ok and base_ids == expected and typed and identities == expected
    add('seeds', paired)
    equivalent = paired and contract(method)
    if equivalent:
        for key, margin in SPEC['margins'].items():
            diffs = [rows[i][key] - base['replicas'][i][key] for i in range(8)]
            # Exact eight-seed median CI: [min, max], coverage 0.9921875;
            # Bonferroni across two metrics exceeds required family 0.95.
            equivalent = equivalent and min(diffs) > -margin and max(diffs) < margin
    add('equivalence', equivalent)
    add('output_contract', contract(method) and base_ok, 'invalid_output')
    # Reuse output assertions from supplied run_anchors/run_evaluation harnesses.
    add('upstream', contract(method) and base_ok and paired, 'upstream')
    return [{'id': r['id'], 'pass': r['pass_'], 'reason_code': r['reason_code']} for r in results]


def main():
    report = Path('out/tests.json')
    cases = []
    try:
        baseline = Path(os.environ.get('BASELINE_OUT', 'baseline-out')) / 'run/ensemble.json'
        candidate = Path(os.environ.get('METHOD_OUT', 'out')) / 'run/ensemble.json'
        base = load(baseline)
        method = load(candidate)
        cases = check(base, method)
    except FileNotFoundError:
        cases = [dict(id=id, **{'pass': False}, reason_code='missing_output') for id in IDS]
    except Exception:
        cases = [dict(id=id, **{'pass': False}, reason_code='invalid_output') for id in IDS]
    finally:
        passed = sum(c['pass'] for c in cases)
        payload = dict(passed=passed, failed=len(cases)-passed, cases=cases)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(payload, allow_nan=False, indent=2) + '\n')
    return 1 if payload['failed'] else 0


if __name__ == '__main__':
    sys.exit(main())
