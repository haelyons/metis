#!/usr/bin/env python3
"""Black-box contract tests for `python3 -I m5/score_comparison.py` (U58).

Contract: m5/SCHEMAS.md "Sealed comparison (U57, U58)": the design format, the "Values" bullet and the whole
"Scoring (U58)" bullet. Never inspect m5/score_comparison.py, the pipeline or git history: every case builds a
layout by hand (C dir with comparison.json, comparison_seal.json and arms_seal.json; a harness dir with the sealed
adapters, cmp_files.json, cmp_extract.json, versions.sh and, with an evaluator, fetch_private.sh and evaluate.sh;
fetched invocation folders <comparison dir>/<w<r>|r<r>>/<arm>/<input>/ with wrap.json, out/, log/ and eval/), runs
the script as the pipeline does and reads only its exit status, its output file and its diagnostics.

Conventions the contract leaves open, fixed here in one place each (see round_dir and the bootstrap draw):
  - round folders are numbered from 1 within their kind: warmups w1..wW, replicates r1..rR; a pair row's
    `replicate` is that number;
  - a bootstrap resample draws n replicate indices with replacement from the one random.Random(bootstrap_seed)
    stream, either by n calls of randrange(n) (as random.choice/randint do) or by one choices(range(n), k=n); the
    suite accepts exactly one of these two draws, the same one for every comparison of the run.

Usage: python3 -I tools/test_m5_comparison_score.py [-v]   (-v also lists passing checks)
"""
import hashlib
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, 'm5', 'score_comparison.py')
# Input content that must never appear in diagnostics. No digits, no lowercase nan/inf: it may sit in number files.
SENT = 'CMPSCORE_PRIVATE_SENTINEL_QXZ'
TOP_KEYS = ['comparison_sha256', 'comparisons', 'totals']
CMP_KEYS = ['id', 'arm', 'against', 'criterion', 'unit', 'outcome', 'rows']
ROW_KEYS = ['input', 'n', 'n_missing', 'estimate', 'lo', 'hi', 'margin_value', 'threshold', 'outcome', 'sign', 'reason',
            'pairs']
PAIR_KEYS = ['replicate', 'agrees', 'missing', 'max_abs_error', 'max_rel_error']
TOTAL_KEYS = ['supported', 'not_supported', 'inconclusive', 'void']
S, NS, I, V = 'supported', 'not_supported', 'inconclusive', 'void'

checks = 0
failures = 0
SCRATCH = tempfile.mkdtemp(prefix='test_m5_comparison_score_')
MISSING = object()
DIRECTORY = object()


def check(label, fn):
    global checks, failures
    checks += 1
    try:
        fn()
        if VERBOSE:
            print('ok %s' % label)
    except Exception as error:  # noqa: BLE001 - every failure is reported, none stops the suite
        failures += 1
        print('FAIL %s: %s' % (label, ' '.join(str(error).split())[:1500]))
        FAILED.append('%s: %s' % (label, ' '.join(str(error).split())[:300]))


FAILED = []
# Passing checks are listed only with -v (the suite has several hundred); failures are always printed.
VERBOSE = '-v' in sys.argv[1:]


def assert_(condition, message):
    assert condition, message


def sha(data):
    return hashlib.sha256(data).hexdigest()


def same(a, b, where='value'):
    """Deep equality; floats compared with a tight relative tolerance; bool never equals a number."""
    if isinstance(a, bool) or isinstance(b, bool) or a is None or b is None or isinstance(a, str) or isinstance(b, str):
        assert type(a) is type(b) and a == b, '%s: %r != %r' % (where, a, b)
        return
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        assert math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12), '%s: %r != %r' % (where, a, b)
        return
    if isinstance(a, list) and isinstance(b, list):
        assert len(a) == len(b), '%s: length %d != %d' % (where, len(a), len(b))
        for i, (x, y) in enumerate(zip(a, b)):
            same(x, y, '%s[%d]' % (where, i))
        return
    if isinstance(a, dict) and isinstance(b, dict):
        assert sorted(a) == sorted(b), '%s: keys %s != %s' % (where, sorted(a), sorted(b))
        for key in a:
            same(a[key], b[key], '%s.%s' % (where, key))
        return
    raise AssertionError('%s: %r != %r' % (where, a, b))


def round_dir(kind, rnd):
    """Fetched round folder: `w<r>` for warmups, `r<r>` for replicates, numbered from 1 within the kind."""
    return ('w' if kind == 'warmup' else 'r') + str(rnd)


# ---- Design builders (every design is valid for U57 unless a case says otherwise) ---------------------------
class PerArm(dict):
    """A location or rule that differs per arm."""


def arm_def(i):
    return {'id': 'A%d' % i, 'what': 'published arm %d %s' % (i, SENT),
            'commands': [['bin/run', '--case', '{input}', '--out', '{out}'], ['bin/post', '{run}/post.cfg']],
            'env': {'OMP_NUM_THREADS': '4'} if i % 2 else None}


EVALUATOR = {'what': 'published evaluator ' + SENT, 'spec': {'program': 'scorer', 'pin': 'v1.2'}, 'timeout_s': 600}


def design(n_arms=2, inputs=('in1',), outputs=(), metrics=(), evaluator=False, replicates=1, warmup=0, comparisons=(),
           **over):
    d = {'arms': [arm_def(i) for i in range(n_arms)],
         'inputs': [{'id': i, 'spec': {'case': i, 'note': SENT}} for i in inputs],
         'outputs': list(outputs), 'metrics': list(metrics), 'evaluator': dict(EVALUATOR) if evaluator else None,
         'replicates': replicates, 'warmup': warmup, 'order_seed': 7, 'timeout_s': None, 'budget_s': 3600,
         'bootstrap_seed': 20261103, 'bootstrap_resamples': 1000, 'comparisons': list(comparisons)}
    d.update(over)
    return d


def output(name, fmt, select=None):
    return {'name': name, 'what': 'logical output %s %s' % (name, SENT), 'format': fmt, 'select': select}


def metric(name, source='sealed_extraction', reduce='first', expect_count=None):
    if source == 'trusted_wall':
        reduce = expect_count = None
    return {'name': name, 'unit': 's', 'what': 'metric %s %s' % (name, SENT), 'source': source, 'reduce': reduce,
            'expect_count': expect_count}


WALL = {'name': 'wall', 'unit': 's', 'what': 'wall seconds ' + SENT, 'source': 'trusted_wall', 'reduce': None,
        'expect_count': None}  # designs need 1 to 10 metrics, also when they compare outputs only


def comparison(id_, measure, criterion, direction, arm='A1', against='A0', unit='per_input_each',
               pairing='paired_replicate', rule='all_pairs', confidence=None, margin=None, threshold=None, strict=None,
               reference=None, missing='void', given=()):
    return {'id': id_, 'arm': arm, 'against': against, 'measure': measure, 'criterion': criterion,
            'direction': direction, 'unit': unit, 'pairing': pairing, 'rule': rule, 'confidence': confidence,
            'margin': margin, 'threshold': threshold, 'strict': strict, 'reference': reference, 'missing': missing,
            'given': list(given), 'parts': ['part of %s' % id_]}


def agreement(id_, out, comparator, margin=None, **kw):
    return comparison(id_, {'output': out, 'comparator': comparator}, 'agreement', 'two_sided', margin=margin, **kw)


def ni(id_, met, direction, margin=None, **kw):
    return comparison(id_, {'metric': met}, 'non_inferiority', direction, margin=margin, **kw)


def sup(id_, met, margin=None, **kw):
    return comparison(id_, {'metric': met}, 'superiority', 'two_sided', margin=margin, **kw)


def ratio(id_, met, direction, threshold, strict, confidence=0.9, **kw):
    return comparison(id_, {'metric': met}, 'ratio_at_least', direction, unit='pooled_mean', rule='bootstrap',
                      confidence=confidence, threshold=threshold, strict=strict, **kw)


def vs_ref(values, **kw):
    return dict(against='reference', pairing='unpaired',
                reference={'source': 'run blind-02-r1 and its derivation rule ' + SENT, 'values': values}, **kw)


def json_rule(file, expr):
    return {'file': file, 'kind': 'json', 'expr': expr}


def regex_rule(file, expr):
    return {'file': file, 'kind': 'regex', 'expr': expr}


def wrap(status='ok', ev=False, eval_status=None, adapter_wall=0.5, walls=(1.25, 2.0), eval_wall=0.25):
    """A wrap.json as the trusted wrapper writes it."""
    rcs = {'ok': [0] * len(walls), 'failed': [0] * (len(walls) - 1) + [1],
           'timeout': [0] * (len(walls) - 1) + [None], 'invalid': [0] * len(walls)}[status]
    commands = [{'argv': ['bin/run', str(k)], 'rc': rc, 'wall_s': w, 'executable': '/srv/run/bin/run',
                 'sha256': 'b' * 64} for k, (rc, w) in enumerate(zip(rcs, walls))]
    if eval_status is None:
        eval_status = 'ok' if ev and status == 'ok' else 'skipped'
    eval_rc = {'ok': 0, 'failed': 1, 'timeout': None, 'skipped': None}[eval_status]
    eval_w = None if eval_status == 'skipped' else eval_wall
    return {'status': status, 'adapter_rc': 0, 'adapter_wall_s': adapter_wall, 'commands': commands,
            'gpu_busy_s': 1.0, 'gpu_busy_known': True, 'eval_status': eval_status, 'eval_rc': eval_rc,
            'eval_wall_s': eval_w, 'eval_gpu_busy_s': None if eval_w is None else 0.0,
            'eval_gpu_busy_known': eval_w is not None}


# ---- One run of the script on a hand-built layout ------------------------------------------------------------
class Run:
    def cmp(self, id_):
        return next(c for c in self.scored['comparisons'] if c['id'] == id_)

    def row(self, id_, inp):
        return next(row for row in self.cmp(id_)['rows'] if row['input'] == inp)


def write_bytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as handle:
        handle.write(data if isinstance(data, bytes) else data.encode())


def execute(name, d, locs=None, rules=None, cell=None, tamper=None, argv=None, comparison_raw=None,
            cmp_files_raw=None, extract_raw=None, readonly_c=False):
    """Builds the C dir, the harness dir and fetched invocations; runs the script; returns a Run.

    locs: output name -> location (or PerArm); rules: metric name -> {file, kind, expr} (or PerArm);
    cell(kind, round, arm, input) -> {'wrap': dict | str | MISSING, 'files': {relpath: bytes | str | DIRECTORY}}."""
    root = os.path.join(SCRATCH, name)
    cdir = os.path.join(root, 'control')
    results = os.path.join(root, 'agent', 'results', 'evaluate', 'comparison')
    harness = os.path.join(root, 'agent', 'harness')
    for directory in (cdir, results, harness):
        os.makedirs(directory, exist_ok=True)
    doc = {'source': '/nonexistent/designs/comparison-design.json', 'source_sha256': 'a' * 64, 'design': d}
    cbytes = comparison_raw if comparison_raw is not None else (json.dumps(doc, indent=1) + '\n').encode()
    write_bytes(os.path.join(cdir, 'comparison.json'), cbytes)
    write_bytes(os.path.join(cdir, 'comparison_seal.json'),
                json.dumps({'comparison_sha256': sha(cbytes), 'sealed_utc': '2026-11-03T09:00:00Z'}))
    arms = [a['id'] for a in d['arms']]
    has_eval = d.get('evaluator') is not None
    sealed = {}
    for a in arms:
        sealed['arms/%s.sh' % a] = ('#!/bin/bash\n# adapter for %s %s\nmkdir -p "$CMP_OUT"\n' % (a, SENT)).encode()
    sealed['versions.sh'] = ('#!/bin/bash\n# %s\necho "{}"\n' % SENT).encode()
    if has_eval:
        sealed['fetch_private.sh'] = ('#!/bin/bash\n# fetch %s\ntrue\n' % SENT).encode()
        sealed['evaluate.sh'] = ('#!/bin/bash\n# evaluate %s\ntrue\n' % SENT).encode()

    def per_arm(table, key, a):
        value = (table or {})[key]
        return value[a] if isinstance(value, PerArm) else value
    files_doc = {'files': {a: {o['name']: per_arm(locs, o['name'], a) for o in d['outputs']} for a in arms}}
    sealed['cmp_files.json'] = cmp_files_raw if cmp_files_raw is not None else (json.dumps(files_doc, indent=1) + '\n').encode()
    extract_doc = {'rules': [dict({'arm': a, 'metric': m['name']}, **per_arm(rules, m['name'], a))
                             for a in arms for m in d['metrics'] if m['source'] == 'sealed_extraction']}
    sealed['cmp_extract.json'] = extract_raw if extract_raw is not None else (json.dumps(extract_doc, indent=1) + '\n').encode()
    for rel, data in sealed.items():
        write_bytes(os.path.join(harness, rel), data)
    write_bytes(os.path.join(harness, 'setup.sh'), '#!/bin/bash\n# unsealed %s\n' % SENT)
    write_bytes(os.path.join(cdir, 'arms_seal.json'), json.dumps(
        {'files': {rel: sha(data) for rel, data in sealed.items()}, 'sealed_utc': '2026-11-03T09:30:00Z'}))
    rounds = [('warmup', k) for k in range(1, d.get('warmup', 0) + 1)] + \
             [('replicate', k) for k in range(1, d.get('replicates', 1) + 1)]
    for kind, rnd in rounds:
        for a in arms:
            for inp in [i['id'] for i in d['inputs']]:
                spec = (cell or (lambda *_: {}))(kind, rnd, a, inp) or {}
                inv = os.path.join(results, round_dir(kind, rnd), a, inp)
                for sub in ('out', 'log', 'eval'):
                    os.makedirs(os.path.join(inv, sub), exist_ok=True)
                w = spec.get('wrap', wrap(ev=has_eval))
                if isinstance(w, dict):
                    write_bytes(os.path.join(inv, 'wrap.json'), json.dumps(w))
                elif isinstance(w, str):
                    write_bytes(os.path.join(inv, 'wrap.json'), w)
                for rel, content in spec.get('files', {}).items():
                    target = os.path.join(inv, rel)
                    if content is DIRECTORY:
                        os.makedirs(target, exist_ok=True)
                    else:
                        write_bytes(target, content)
    if tamper:
        tamper(root)
    outfile = os.path.join(cdir, 'comparison_scored.json')
    before = {n: open(os.path.join(cdir, n), 'rb').read() for n in sorted(os.listdir(cdir))}
    command = argv(cdir, results, harness, outfile) if argv else [cdir, results, harness, outfile]
    if readonly_c:
        os.chmod(cdir, 0o555)
    try:
        proc = subprocess.run([sys.executable, '-I', SCRIPT] + command, cwd=SCRATCH, capture_output=True, timeout=600)
    finally:
        if readonly_c:
            os.chmod(cdir, 0o755)
    r = Run()
    r.name, r.design, r.cdir, r.cbytes, r.before = name, d, cdir, cbytes, before
    r.rc, r.stdout, r.stderr = proc.returncode, proc.stdout, proc.stderr
    r.exists = os.path.exists(outfile)
    r.scored = None
    if r.exists:
        with open(outfile) as handle:
            r.scored = json.load(handle)
    r.c_after = sorted(os.listdir(cdir))
    return r


def table_cell(tables, ev=False, extra=None):
    """Metric files from tables {path: {arm: {input: [value per replicate, None = no file]}}}; warmups get none.
    extra(kind, round, arm, input, spec) may change the cell."""
    def cell(kind, rnd, a, inp):
        spec = {'files': {}}
        if kind == 'replicate':
            for path, table in tables.items():
                values = table.get(a, {}).get(inp)
                if values is not None and values[rnd - 1] is not None:
                    spec['files'][path] = json.dumps({'v': values[rnd - 1], 'note': SENT})
        if extra:
            extra(kind, rnd, a, inp, spec)
        return spec
    return cell


def no_leak(r):
    check('%s: diagnostics carry no input content' % r.name, lambda: assert_(
        SENT.encode() not in r.stdout + r.stderr, 'sentinel in diagnostics: %r' % (r.stdout + r.stderr)[-300:]))


def valid_checks(r):
    """Exit 0; exact keys; comparison and row order; totals; seal digest; C dir unchanged but for the output."""
    ok = r.rc == 0 and r.exists
    check('%s: exit 0 and comparison_scored.json written' % r.name, lambda: (
        assert_(r.rc == 0, 'exit %s; stderr %s' % (r.rc, r.stderr[-800:])), assert_(r.exists, 'no output file')))
    no_leak(r)
    if not r.exists:
        return False
    d = r.design

    def keys():
        assert sorted(r.scored) == sorted(TOP_KEYS), 'top keys %s' % sorted(r.scored)
        assert sorted(r.scored['totals']) == sorted(TOTAL_KEYS), 'totals keys %s' % sorted(r.scored['totals'])
        for c in r.scored['comparisons']:
            assert sorted(c) == sorted(CMP_KEYS), '%s keys %s' % (c.get('id'), sorted(c))
            for row in c['rows']:
                assert sorted(row) == sorted(ROW_KEYS), '%s row keys %s' % (c['id'], sorted(row))
                if row['pairs'] is not None:
                    for p in row['pairs']:
                        assert sorted(p) == sorted(PAIR_KEYS), '%s pair keys %s' % (c['id'], sorted(p))
    check('%s: exact keys of the file, totals, comparisons, rows and pairs' % r.name, keys)

    def order():
        same([c['id'] for c in r.scored['comparisons']], [c['id'] for c in d['comparisons']], 'comparison order')
        inputs = [i['id'] for i in d['inputs']]
        for c, dc in zip(r.scored['comparisons'], d['comparisons']):
            same([c['arm'], c['against'], c['criterion'], c['unit']],
                 [dc['arm'], dc['against'], dc['criterion'], dc['unit']], '%s identity' % dc['id'])
            want = [None] if dc['unit'] == 'pooled_mean' else inputs
            same([row['input'] for row in c['rows']], want, '%s row inputs' % dc['id'])
            for row in c['rows']:
                if 'output' not in dc['measure']:
                    same(row['pairs'], None, '%s pairs of a metric comparison' % dc['id'])
                if row['outcome'] == V:
                    same([row['estimate'], row['lo'], row['hi']], [None, None, None], '%s void numbers' % dc['id'])
                assert row['outcome'] in (S, NS, I, V), '%s row outcome %r' % (dc['id'], row['outcome'])
                assert row['reason'] in (None, 'missing_values', 'insufficient_replicates', 'not_eligible'), row['reason']
    check('%s: comparisons in design order with arm/against/criterion/unit; rows per decision unit' % r.name, order)

    def combined():
        for c, dc in zip(r.scored['comparisons'], d['comparisons']):
            outs = [row['outcome'] for row in c['rows']]
            if dc['unit'] == 'pooled_mean':
                want = outs[0]
            elif dc['unit'] == 'per_input_each':
                want = 'per_input'
            elif all(o == S for o in outs):
                want = S
            elif NS in outs:
                want = NS
            elif V in outs:
                want = V
            else:
                want = I
            same(c['outcome'], want, '%s outcome from its rows' % dc['id'])
    check('%s: each comparison outcome follows its unit rule from its rows' % r.name, combined)

    def totals():
        rows = [row for c in r.scored['comparisons'] for row in c['rows']]
        for key in TOTAL_KEYS:
            assert type(r.scored['totals'][key]) is int, key
        same(r.scored['totals'], {key: sum(1 for row in rows if row['outcome'] == key) for key in TOTAL_KEYS}, 'totals')
    check('%s: totals count decision units by outcome' % r.name, totals)
    check('%s: comparison_sha256 is the digest of C/comparison.json' % r.name,
          lambda: same(r.scored['comparison_sha256'], sha(r.cbytes), 'comparison_sha256'))

    def untouched():
        for n, data in r.before.items():
            with open(os.path.join(r.cdir, n), 'rb') as handle:
                assert handle.read() == data, '%s changed' % n
        assert r.c_after == sorted(list(r.before) + ['comparison_scored.json']), 'C dir holds %s' % r.c_after
    check('%s: inputs unchanged; only the output added (no temporary file left)' % r.name, untouched)
    return ok


def invalid_checks(r, what):
    check('%s: %s exits 1 with no output file' % (r.name, what), lambda: (
        assert_(r.rc == 1, 'exit %s; stderr %s' % (r.rc, r.stderr[-400:])), assert_(not r.exists, 'output written'),
        assert_(r.c_after == sorted(r.before), 'C dir holds %s' % r.c_after)))
    no_leak(r)


def expect(r, id_, inp, label, **fields):
    def fn():
        row = r.row(id_, inp)
        for key, want in fields.items():
            same(row[key], want, '%s %s %s' % (id_, inp, key))
    check('%s: %s %s: %s' % (r.name, id_, inp, label), fn)


def expect_outcome(r, id_, want):
    check('%s: %s outcome %s' % (r.name, id_, want), lambda: same(r.cmp(id_)['outcome'], want, id_))


# ---- Contract oracle for all_pairs metric units (Scoring bullets) --------------------------------------------
def all_pairs_row(c, arm, against):
    """arm/against: values per replicate (None = missing); against a number for a reference."""
    ref = not isinstance(against, list)
    nm = sum(v is None for v in arm) + (0 if ref else sum(v is None for v in against))
    if nm:
        if c['missing'] == 'void' or not any(v is None for v in arm):
            return {'outcome': V, 'reason': 'missing_values', 'n_missing': nm, 'sign': None}
        return {'outcome': NS, 'reason': 'missing_values', 'n_missing': nm}
    if ref:
        diffs = [a - against for a in arm]
    elif c['pairing'] == 'paired_replicate':
        diffs = [a - b for a, b in zip(arm, against)]
    else:
        diffs = [a - b for a in arm for b in against]
    lo, hi, est = min(diffs), max(diffs), sum(diffs) / len(diffs)
    m = c['margin']['abs'] if c['margin'] else 0
    sign = None
    if c['criterion'] == 'non_inferiority' and c['direction'] == 'higher_better':
        out = S if lo >= -m else NS if hi < -m else I
    elif c['criterion'] == 'non_inferiority':
        out = S if hi <= m else NS if lo > m else I
    else:
        if lo > m:
            out, sign = S, 'higher'
        elif hi < -m:
            out, sign = S, 'lower'
        else:
            out = NS if -m <= lo and hi <= m else I
    return {'outcome': out, 'reason': None, 'n': len(diffs), 'n_missing': 0, 'estimate': est, 'lo': lo, 'hi': hi,
            'margin_value': m, 'threshold': None, 'sign': sign, 'pairs': None}


def oracle_checks(r, values):
    """values: {arm: {input: [per replicate]}}; every all_pairs metric comparison of the design checked per row."""
    for c in r.design['comparisons']:
        if c['rule'] != 'all_pairs' or 'metric' not in c['measure'] or c['given']:
            continue
        for inp in [i['id'] for i in r.design['inputs']]:
            against = c['reference']['values'][inp] if c['against'] == 'reference' else values[c['against']][inp]
            want = all_pairs_row(c, values[c['arm']][inp], against)
            expect(r, c['id'], inp, 'row as the contract computes it (%s)' % want['outcome'], **want)


def value_rows(r, id_, expected):
    """A comparison against reference 0 (one replicate) shows each input's value as estimate = lo = hi."""
    for inp, value in expected.items():
        if value is None:
            expect(r, id_, inp, 'missing value: void, missing_values, one missing', outcome=V, reason='missing_values',
                   n_missing=1, estimate=None)
        else:
            expect(r, id_, inp, 'value %r' % value, estimate=value, lo=value, hi=value, n=1, n_missing=0, reason=None,
                   outcome=S if value >= 0 else NS)


# ---- Cases -------------------------------------------------------------------------------------------------
def invalid_cases():
    def base(name, evaluator=True, d=None, **kw):
        d = d or design(inputs=['in1'], outputs=[output('o', 'text_numbers')], metrics=[metric('v')], evaluator=evaluator,
                        comparisons=[agreement('K1', 'o', 'elementwise_abs', {'abs': 0}), ni('K2', 'v', 'higher_better')])
        cell = lambda *_: {'files': {'out/o.txt': '1 2 ' + SENT, 'out/m.json': '{"v": 1, "s": "%s"}' % SENT}}  # noqa: E731
        return execute(name, d, locs={'o': 'out/o.txt'}, rules={'v': json_rule('out/m.json', '/v')}, cell=cell, **kw)

    good = base('invalid-baseline')
    check('invalid-baseline: the unaltered layout scores (exit 0), so every case below fails for its one change',
          lambda: assert_(good.rc == 0 and good.exists, 'exit %s %s' % (good.rc, good.stderr[-400:])))

    def append(rel, data=b' '):
        return lambda root: open(os.path.join(root, rel), 'ab').write(data)

    def put(rel, data):
        def tamper(root):
            path = os.path.join(root, rel)
            if data is None:
                os.remove(path)
            else:
                write_bytes(path, data)
        return tamper

    def reseal(fn):
        def tamper(root):
            path = os.path.join(root, 'control', 'arms_seal.json')
            seal = json.load(open(path))
            fn(seal['files'])
            write_bytes(path, json.dumps(seal))
        return tamper
    H = 'agent/harness/'
    cases = [
        ('comparison-altered', 'C/comparison.json changed after its seal', dict(tamper=append('control/comparison.json'))),
        ('comparison-seal-wrong', 'a wrong comparison seal digest', dict(tamper=put('control/comparison_seal.json', json.dumps({'comparison_sha256': '0' * 64, 'sealed_utc': 'x'})))),
        ('comparison-seal-missing', 'a missing comparison_seal.json', dict(tamper=put('control/comparison_seal.json', None))),
        ('comparison-seal-not-json', 'an unreadable comparison seal', dict(tamper=put('control/comparison_seal.json', '{' + SENT))),
        ('comparison-missing', 'a missing comparison.json', dict(tamper=put('control/comparison.json', None))),
        ('arms-seal-missing', 'a missing arms_seal.json', dict(tamper=put('control/arms_seal.json', None))),
        ('arms-seal-not-json', 'an unreadable arms_seal.json', dict(tamper=put('control/arms_seal.json', '[' + SENT))),
        ('adapter-altered', 'arms/A1.sh changed after its seal', dict(tamper=append(H + 'arms/A1.sh'))),
        ('adapter-removed', 'arms/A0.sh removed', dict(tamper=put(H + 'arms/A0.sh', None))),
        ('cmp-files-altered', 'cmp_files.json changed after its seal', dict(tamper=append(H + 'cmp_files.json'))),
        ('cmp-extract-altered', 'cmp_extract.json changed after its seal', dict(tamper=append(H + 'cmp_extract.json'))),
        ('versions-altered', 'versions.sh changed after its seal', dict(tamper=append(H + 'versions.sh'))),
        ('evaluate-altered', 'evaluate.sh changed after its seal', dict(tamper=append(H + 'evaluate.sh'))),
        ('fetch-private-removed', 'fetch_private.sh removed', dict(tamper=put(H + 'fetch_private.sh', None))),
        ('arms-seal-wrong-digest', 'a wrong cmp_files.json digest in arms_seal.json', dict(tamper=reseal(lambda f: f.update({'cmp_files.json': 'f' * 64})))),
        ('arms-seal-omits-file', 'arms_seal.json without versions.sh', dict(tamper=reseal(lambda f: f.pop('versions.sh')))),
        ('arms-seal-omits-extract', 'arms_seal.json without cmp_extract.json', dict(tamper=reseal(lambda f: f.pop('cmp_extract.json')))),
        ('arms-seal-omits-adapter', 'arms_seal.json without arms/A1.sh', dict(tamper=reseal(lambda f: f.pop('arms/A1.sh')))),
        ('arms-seal-extra-key', 'arms_seal.json with an extra top-level key', dict(tamper=lambda root: write_bytes(
            os.path.join(root, 'control', 'arms_seal.json'), json.dumps(dict(json.load(open(os.path.join(
                root, 'control', 'arms_seal.json'))), note=SENT))))),
        ('comparison-not-json', 'a sealed comparison.json that is not JSON', dict(comparison_raw=('{"design": ' + SENT).encode())),
        ('comparison-extra-key', 'a sealed comparison.json with an extra key', dict(comparison_raw=json.dumps({'source': 'x', 'source_sha256': 'a' * 64, 'design': None, 'note': SENT}).encode())),
        ('cmp-files-not-json', 'a sealed cmp_files.json that is not JSON', dict(cmp_files_raw=('{' + SENT).encode())),
        ('cmp-files-missing-output', 'cmp_files.json without A1\'s output', dict(cmp_files_raw=json.dumps({'files': {'A0': {'o': 'out/o.txt'}, 'A1': {}}}).encode())),
        ('cmp-files-dotdot', 'a location with a `..` component', dict(cmp_files_raw=json.dumps({'files': {'A0': {'o': 'out/../o.txt'}, 'A1': {'o': 'out/o.txt'}}}).encode())),
        ('cmp-files-bad-root', 'a location whose first component is not out, log or eval', dict(cmp_files_raw=json.dumps({'files': {'A0': {'o': 'tmp/o.txt'}, 'A1': {'o': 'out/o.txt'}}}).encode())),
        ('cmp-files-glob-extra-key', 'a glob location with an extra key', dict(cmp_files_raw=json.dumps({'files': {'A0': {'o': {'glob': 'out/*.txt', 'note': SENT}}, 'A1': {'o': 'out/o.txt'}}}).encode())),
        ('cmp-extract-missing-rule', 'cmp_extract.json without A1\'s rule', dict(extract_raw=json.dumps({'rules': [{'arm': 'A0', 'metric': 'v', 'file': 'out/m.json', 'kind': 'json', 'expr': '/v'}]}).encode())),
        ('cmp-extract-two-groups', 'a regex with two groups for reduce first', dict(extract_raw=json.dumps({'rules': [{'arm': a, 'metric': 'v', 'file': 'out/m.json', 'kind': 'regex', 'expr': '(a)=(\\d+)' + SENT} for a in ('A0', 'A1')]}).encode())),
        ('cmp-extract-bad-kind', 'a rule of an unknown kind', dict(extract_raw=json.dumps({'rules': [{'arm': a, 'metric': 'v', 'file': 'out/m.json', 'kind': 'yaml', 'expr': '/v'} for a in ('A0', 'A1')]}).encode())),
        ('cmp-extract-bad-root', 'a rule file under neither out, log nor eval', dict(extract_raw=json.dumps({'rules': [{'arm': a, 'metric': 'v', 'file': 'run/m.json', 'kind': 'json', 'expr': '/v'} for a in ('A0', 'A1')]}).encode())),
        ('cli-three-arguments', 'three arguments', dict(argv=lambda c, res, h, o: [c, res, h])),
        ('cli-five-arguments', 'five arguments', dict(argv=lambda c, res, h, o: [c, res, h, o, '--extra'])),
        ('failed-write-no-directory', 'an output path in a missing directory (failed write)', dict(argv=lambda c, res, h, o: [c, res, h, os.path.join(c, 'absent', 'comparison_scored.json')])),
    ]
    for name, what, kw in cases:
        invalid_checks(base('invalid-' + name, **kw), what)
    # Sealed designs that are invalid for U57.
    bad = design(inputs=['in1'], outputs=[output('o', 'text_numbers')], metrics=[metric('v')], evaluator=True,
                 comparisons=[agreement('K1', 'zz', 'elementwise_abs', {'abs': 0})])
    invalid_checks(base('invalid-design-unknown-output', d=bad), 'a sealed design comparing an unknown output')
    bad = design(inputs=['in1'], outputs=[output('o', 'text_numbers')], metrics=[metric('v')], evaluator=True,
                 comparisons=[ni('K1', 'v', 'higher_better')])
    del bad['bootstrap_seed']
    invalid_checks(base('invalid-design-missing-key', d=bad), 'a sealed design without bootstrap_seed')
    bad = design(inputs=['in1'], outputs=[output('o', 'text_numbers')], metrics=[metric('v')], evaluator=True,
                 comparisons=[ni('K1', 'v', 'higher_better', given=['K2']), ni('K2', 'v', 'higher_better')])
    invalid_checks(base('invalid-design-given-later', d=bad), 'a sealed design whose `given` names a later comparison')
    # An eval location when the design has no evaluator.
    invalid_checks(base('invalid-eval-location-without-evaluator', evaluator=False,
                        cmp_files_raw=json.dumps({'files': {'A0': {'o': 'eval/o.txt'}, 'A1': {'o': 'out/o.txt'}}}).encode()),
                   'an eval location without an evaluator')
    if os.geteuid() == 0:
        print('note: running as root; the unwritable C dir case is skipped (not counted)')
    else:
        invalid_checks(base('invalid-unwritable-c-dir', readonly_c=True), 'a failed write (C dir not writable)')


def wall_cases():
    # No evaluator: adapter wall plus command walls; eval wall never added.
    ins = ['ok', 'fast', 'failed', 'timeout', 'nowrap', 'badwrap', 'invalid']
    cells = {'ok': wrap(), 'fast': wrap(adapter_wall=0.125, walls=(0.25, 0.5)), 'failed': wrap('failed'),
             'timeout': wrap('timeout'), 'nowrap': MISSING, 'badwrap': '{"status": "ok", "x": "%s' % SENT,
             'invalid': wrap('invalid')}
    d = design(inputs=ins, metrics=[metric('wall', 'trusted_wall')], comparisons=[
        ni('K1', 'wall', 'lower_better', {'abs': 100}, **vs_ref({i: 0 for i in ins})),
        ni('K2', 'wall', 'lower_better', {'abs': 100}, arm='A0', **vs_ref({i: 0 for i in ins}))])
    r = execute('trusted-wall', d, cell=lambda k, rnd, a, inp: {'wrap': cells[inp]} if a == 'A1' else {})
    if valid_checks(r):
        value_rows(r, 'K1', {'ok': 3.75, 'fast': 0.875, 'failed': None, 'timeout': None, 'nowrap': None,
                             'badwrap': None, 'invalid': None})
        value_rows(r, 'K2', {i: 3.75 for i in ins})
        expect(r, 'K1', 'ok', 'lower_better non-inferiority, margin 100: margin_value 100, threshold null, sign null',
               margin_value=100, threshold=None, sign=None, outcome=S)
    # With an evaluator: plus eval_wall_s, null unless eval_status ok.
    ins = ['eok', 'efail', 'etimeout', 'afail', 'atimeout']
    cells = {'eok': wrap(ev=True), 'efail': wrap(ev=True, eval_status='failed'),
             'etimeout': wrap(ev=True, eval_status='timeout'), 'afail': wrap('failed', ev=True),
             'atimeout': wrap('timeout', ev=True)}
    d = design(inputs=ins, metrics=[metric('wall', 'trusted_wall')], evaluator=True, comparisons=[
        ni('K1', 'wall', 'lower_better', {'abs': 100}, **vs_ref({i: 0 for i in ins}))])
    r = execute('trusted-wall-evaluator', d, cell=lambda k, rnd, a, inp: {'wrap': cells[inp]} if a == 'A1' else {})
    if valid_checks(r):
        value_rows(r, 'K1', {'eok': 4.0, 'efail': None, 'etimeout': None, 'afail': None, 'atimeout': None})


def json_extraction_cases():
    ins = ['i%d' % k for k in range(1, 11)]
    content = {
        'i1': '{"v": 2.5, "p": [[1, 10], [5, 20], [5, 30], [2, 40]]}',
        'i2': '{"v": [3, 1, 4], "p": [[-1, 7]]}',
        'i3': '{"v": [3, true], "p": [[1, true]]}',
        'i4': '{"v": []}',
        'i5': '{"v": "5", "p": [["1", 2]]}',
        'i6': '{"v": [1, NaN], "p": [[NaN, 1], [1, 2]]}',
        'i7': '{"v": 1e400, "p": [[1, 1e400]]}',
        'i8': None,
        'i9': '{"v": ' + SENT,
        'i10': '{"v": [-1, 2, -3, 9.5], "p": [[1, 2, 3]], "q": 1}',
    }
    mets = [metric('jf', reduce='first'), metric('jm', reduce='max'), metric('jk', reduce='value_at_max_key'),
            metric('jc', reduce='first', expect_count=3), metric('jc1', reduce='first', expect_count=1)]
    ref = {i: 0 for i in ins}
    d = design(inputs=ins, metrics=mets, comparisons=[ni('K%d' % k, m['name'], 'higher_better', **vs_ref(ref))
                                                      for k, m in enumerate(mets, 1)])
    rules = {'jf': json_rule('out/j.json', '/v'), 'jm': json_rule('out/j.json', '/v'), 'jk': json_rule('out/j.json', '/p'),
             'jc': json_rule('out/j.json', '/v'), 'jc1': json_rule('out/j.json', '/v')}

    def cell(kind, rnd, a, inp):
        if a != 'A1' or content[inp] is None:
            return {}
        return {'files': {'out/j.json': content[inp]}}
    r = execute('extraction-json', d, rules=rules, cell=cell)
    if valid_checks(r):
        none = {i: None for i in ins}
        value_rows(r, 'K1', dict(none, i1=2.5, i2=3, i10=-1))                     # first
        value_rows(r, 'K2', dict(none, i1=2.5, i2=4, i10=9.5))                    # max
        value_rows(r, 'K3', dict(none, i1=20, i2=7))                              # value at the first largest key
        value_rows(r, 'K4', dict(none, i2=3))                                     # expect_count 3
        value_rows(r, 'K5', dict(none, i1=2.5))                                   # expect_count 1


def regex_extraction_cases():
    ins = ['i%d' % k for k in range(1, 8)]
    base_files = {'out/r.txt': 't=1\nt=7\nt=3\nk=1 v=10\nk=3 v=5\nk=3 v=6\nk=2 v=8\n',
                  'log/cmd1.stdout': 'acc=0.5\nacc=0.75\n', 'eval/score.txt': 'score=9\n'}
    cells = {
        'i1': {'files': base_files},
        'i2': {'files': {'out/r.txt': 't=2\nt=nan\nk=1 v=1\nk=2 v=2\nk=0 v=3\n', 'eval/score.txt': 'score=4\n'},
               'wrap': wrap(ev=True, eval_status='failed')},
        'i3': {'files': {'out/r.txt': 't=4\nt=5\nk=2 v=1e400\n', 'log/cmd1.stdout': 'acc=x\n', 'eval/score.txt': 'score=3'}},
        'i4': {'files': base_files, 'wrap': wrap('failed', ev=True)},
        'i5': {'files': {'out/r.txt': DIRECTORY, 'log/cmd1.stdout': 'acc=2\nacc=1\n', 'eval/score.txt': 'score=-1.5e1\n'}},
        'i6': {'files': {'out/r.txt': b'\xff\xfet=6 \n' + SENT.encode()}},
        'i7': {'files': base_files, 'wrap': MISSING},
    }
    mets = [metric('rf', reduce='first'), metric('rm', reduce='max'), metric('rk', reduce='value_at_max_key'),
            metric('rl', reduce='first'), metric('re', reduce='first'), metric('rc', reduce='first', expect_count=2),
            metric('rkc', reduce='value_at_max_key', expect_count=3)]
    t = regex_rule('out/r.txt', r't=(\S+)')
    kv = regex_rule('out/r.txt', r'k=(\S+) v=(\S+)')
    rules = {'rf': t, 'rm': t, 'rk': kv, 'rl': regex_rule('log/cmd1.stdout', r'acc=(\S+)'),
             're': regex_rule('eval/score.txt', r'score=(\S+)'), 'rc': t, 'rkc': kv}
    ref = {i: 0 for i in ins}
    d = design(inputs=ins, metrics=mets, evaluator=True,
               comparisons=[ni('K%d' % k, m['name'], 'higher_better', **vs_ref(ref)) for k, m in enumerate(mets, 1)])
    r = execute('extraction-regex', d, rules=rules, cell=lambda k, rnd, a, inp: cells[inp] if a == 'A1' else {})
    if valid_checks(r):
        none = {i: None for i in ins}
        value_rows(r, 'K1', dict(none, i1=1, i3=4, i6=6))            # first match, not the last
        value_rows(r, 'K2', dict(none, i1=7, i3=5, i6=6))            # max; a nan match voids i2
        value_rows(r, 'K3', dict(none, i1=5, i2=2))                  # first pair with the largest key
        value_rows(r, 'K4', dict(none, i1=0.5, i5=2))                # log/ file; unparsable `x` and no file are null
        value_rows(r, 'K5', dict(none, i1=9, i3=3, i5=-15))          # eval/ file needs eval_status ok
        value_rows(r, 'K6', dict(none, i3=4))                        # expect_count 2 (i2 matches 2 but one is nan)
        value_rows(r, 'K7', dict(none, i2=2))                        # expect_count 3 pairs


def comparator_cases():
    pairs = {  # input: (A0 content, A1 content)
        'e1': ('1 2 3', '1 2 3'), 'e2': ('1.0 2', '1 2'), 'e3': ('1 2', '1.5 2'), 'e4': ('1 2', '1.5000001 2'),
        'e5': ('2', '4.5'), 'e6': ('2', '4'), 'e7': ('nan 1', 'nan 1'), 'e8': ('nan 1', '1 nan'),
        'e9': ('inf -inf 1', 'inf -inf 1.25'), 'e10': ('inf', '-inf')}
    ins = list(pairs)
    d = design(inputs=ins, outputs=[output('o', 'text_numbers')], metrics=[WALL], comparisons=[
        agreement('K1', 'o', 'exact'), agreement('K2', 'o', 'elementwise_abs', {'abs': 0.5}),
        agreement('K3', 'o', 'elementwise_abs_plus_rel_max', {'abs': 0, 'rel': 0.5}),
        agreement('K4', 'o', 'elementwise_abs_plus_rel_max', {'abs': 0.25, 'rel': 0.0625})])
    r = execute('comparators', d, locs={'o': 'out/v.txt'},
                cell=lambda k, rnd, a, inp: {'files': {'out/v.txt': pairs[inp][0 if a == 'A0' else 1]}})
    if not valid_checks(r):
        return
    agrees = {  # input: (exact, abs 0.5, abs 0 + rel 0.5, abs 0.25 + rel 1/16)
        'e1': (True, True, True, True), 'e2': (False, True, True, True), 'e3': (False, True, True, False),
        'e4': (False, False, True, False), 'e5': (False, False, False, False), 'e6': (False, False, True, False),
        'e7': (True, True, True, True), 'e8': (False, False, False, False), 'e9': (False, True, True, True),
        'e10': (False, False, False, False)}
    # e3 under K4: |0.5| <= 0.25 + 1.5/16 = 0.34375 fails. e9 under K4: 0.25 <= 0.25 + 1.25/16 holds.
    max_abs = {'e1': 0, 'e2': 0, 'e3': 0.5, 'e4': 1.5000001 - 1, 'e5': 2.5, 'e6': 2, 'e7': 0, 'e9': 0.25}
    for k, cid in enumerate(('K1', 'K2', 'K3', 'K4')):
        for inp in ins:
            a = agrees[inp][k]
            expect(r, cid, inp, 'one compared pair, %s' % ('agrees: supported' if a else 'disagrees: not supported'),
                   outcome=S if a else NS, reason=None, n=1, n_missing=0, sign=None)
            check('%s: %s %s: pair row replicate 1, agrees %s, missing false' % (r.name, cid, inp, a), lambda cid=cid, inp=inp, a=a: (
                same(len(r.row(cid, inp)['pairs']), 1, 'pairs'),
                same([r.row(cid, inp)['pairs'][0][key] for key in ('replicate', 'agrees', 'missing')], [1, a, False], 'pair')))
            if cid != 'K1' and inp in max_abs:
                check('%s: %s %s: max_abs_error %r over finite elements' % (r.name, cid, inp, max_abs[inp]),
                      lambda cid=cid, inp=inp: same(r.row(cid, inp)['pairs'][0]['max_abs_error'], max_abs[inp], 'max_abs_error'))
            if cid != 'K1' and inp in ('e1', 'e2', 'e7'):
                check('%s: %s %s: max_rel_error 0 for equal elements' % (r.name, cid, inp),
                      lambda cid=cid, inp=inp: same(r.row(cid, inp)['pairs'][0]['max_rel_error'], 0, 'max_rel_error'))
            if cid != 'K1' and inp == 'e10':
                check('%s: %s e10: no finite element: both errors null' % (r.name, cid), lambda cid=cid: same(
                    [r.row(cid, 'e10')['pairs'][0][key] for key in ('max_abs_error', 'max_rel_error')], [None, None]))


def format_cases():
    """Formats, select, relative-path and glob locations, natural sort, missing content."""
    ins = ['g1', 'g2', 'g3', 'g4', 'g5']
    outs = [output('ob', 'bytes'), output('ojn', 'json_numbers'), output('otn', 'text_numbers', r'^acc: (.*)$'),
            output('obs', 'bytes', r'v=(\d+)(?:/(\d*))?'), output('og', 'bytes'), output('ogn', 'text_numbers'),
            output('oe', 'text_numbers')]
    locs = {'ob': PerArm(A0='out/b.bin', A1='out/c.bin'), 'ojn': PerArm(A0='out/j.json', A1='out/k.json'),
            'otn': PerArm(A0='log/cmd1.stdout', A1='log/cmd2.stdout'), 'obs': 'out/s.txt',
            'og': PerArm(A0={'glob': 'out/shard_*.txt'}, A1='out/all.txt'),
            'ogn': PerArm(A0={'glob': 'out/p*/v.txt'}, A1={'glob': 'out/q?.txt'}), 'oe': 'eval/e.txt'}
    comps = [agreement('K1', 'ob', 'exact'), agreement('K2', 'ojn', 'elementwise_abs', {'abs': 0}),
             agreement('K3', 'otn', 'elementwise_abs', {'abs': 0}), agreement('K4', 'obs', 'exact'),
             agreement('K5', 'og', 'exact'), agreement('K6', 'ogn', 'elementwise_abs', {'abs': 0}),
             agreement('K7', 'oe', 'elementwise_abs', {'abs': 0})]
    d = design(inputs=ins, outputs=outs, metrics=[WALL], evaluator=True, comparisons=comps)
    base = {
        'A0': {'out/b.bin': b'\x00\x01' + SENT.encode(), 'out/j.json': '{"a": 1, "b": [2, true, {"c": 3.5}], "s": "4", "n": null}',
               'log/cmd1.stdout': 'noise 99\nacc: 1.5 and 2\nother 7\n', 'out/s.txt': 'v=1/2 v=3',
               'out/shard_1.txt': '1', 'out/shard_10.txt': '10', 'out/shard_2.txt': '2',
               'out/p1/v.txt': '1', 'out/p10/v.txt': '10', 'out/p2/v.txt': '2', 'out/p3/v.txt': DIRECTORY,
               'eval/e.txt': '5'},
        'A1': {'out/c.bin': b'\x00\x01' + SENT.encode(), 'out/k.json': '[1, 2, 3.5]', 'log/cmd2.stdout': 'acc: 1.5 2\nend 3\n',
               'out/s.txt': 'v=1/2 v=3/', 'out/all.txt': '1\n2\n10', 'out/q1.txt': '1', 'out/q2.txt': '2 10',
               'eval/e.txt': '5'}}
    g2 = {
        'A0': {'out/b.bin': 'abc', 'out/j.json': '{"a": [1, 2]}', 'log/cmd1.stdout': 'acc: 1\nacc: 2\n', 'out/s.txt': 'v=1/2',
               'out/shard_01.txt': '6', 'out/shard_1.txt': '5', 'out/p1/v.txt': '1', 'out/p10/v.txt': '3', 'eval/e.txt': '5'},
        'A1': {'out/c.bin': 'abd', 'out/k.json': '[1, 2, 3]', 'log/cmd2.stdout': 'acc: 1 2\n', 'out/s.txt': 'v=12',
               'out/all.txt': '6\n5', 'out/q1.txt': '3', 'out/q2.txt': '1', 'eval/e.txt': '5'}}
    g3 = {'A0': {k: v for k, v in base['A0'].items() if not k.startswith('out/shard_')},
          'A1': {k: v for k, v in base['A1'].items() if k not in ('out/s.txt', 'out/q1.txt', 'out/q2.txt')}}
    g3['A0'].update({'out/b.bin': b'', 'out/j.json': '{"a": "x", "b": [true]}', 'log/cmd1.stdout': 'no match here\n',
                     'eval/e.txt': 'none'})
    g5 = {'A0': dict(base['A0'], **{'log/cmd1.stdout': 'acc: 3\n'}),
          'A1': dict(base['A1'], **{'out/k.json': '[1, 2', 'out/c.bin': DIRECTORY, 'log/cmd2.stdout': b'\xff\nacc: 3\n'})}
    del g5['A1']['out/c.bin']
    g5['A1']['out/c.bin'] = DIRECTORY

    def cell(kind, rnd, a, inp):
        files = {'g1': base, 'g2': g2, 'g3': g3, 'g4': base, 'g5': g5}[inp][a]
        spec = {'files': files}
        if inp == 'g2' and a == 'A1':
            spec['wrap'] = wrap(ev=True, eval_status='failed')
        if inp == 'g4' and a == 'A0':
            spec['wrap'] = wrap('failed', ev=True)
        return spec
    r = execute('formats-and-locations', d, locs=locs, cell=cell)
    if not valid_checks(r):
        return
    A, D, M = 'agree', 'disagree', 'missing'
    want = {  # comparison: outcome kind for g1..g5
        'K1': (A, D, M, M, M),   # bytes; g3 empty file; g5 A1 location is a directory
        'K2': (A, D, M, M, M),   # json_numbers: booleans and strings skipped; g2 lengths differ; g3 no numbers; g5 bad JSON
        'K3': (A, A, M, M, A),   # select ^acc: (.*)$ multiline; g3 no match; g5 invalid UTF-8 read with replacement
        'K4': (A, D, M, M, A),   # unmatched group joined as the empty string; g3 A1 file absent
        'K5': (A, A, M, M, A),   # glob natural sort 1, 2, 10 joined by b"\n"; g2 tie broken by path (shard_01 first)
        'K6': (A, D, M, M, A),   # multi-component glob skips the directory p3/v.txt; g3 glob names no file
        'K7': (A, M, M, M, A),   # eval/: g2 A1 eval_status failed; g3 A0 no numbers
    }
    for cid, kinds in want.items():
        for inp, kind in zip(ins, kinds):
            if kind == A:
                expect(r, cid, inp, 'agrees: supported', outcome=S, reason=None, n=1, n_missing=0)
            elif kind == D:
                expect(r, cid, inp, 'disagrees: not supported', outcome=NS, reason=None, n=1, n_missing=0)
            else:
                expect(r, cid, inp, 'a missing side: void, missing_values', outcome=V, reason='missing_values', n_missing=1)


def agreement_missing_cases():
    ins = ['h1', 'h2', 'h3', 'h4', 'h5']
    d = design(inputs=ins, outputs=[output('o', 'text_numbers')], metrics=[WALL], replicates=3, comparisons=[
        agreement('K1', 'o', 'elementwise_abs', {'abs': 0}), agreement('K2', 'o', 'elementwise_abs', {'abs': 0}, unit='per_input_all'),
        agreement('K3', 'o', 'elementwise_abs', {'abs': 0}, missing='fail'),
        agreement('K4', 'o', 'exact', unit='per_input_all', missing='fail')])
    absent = {('h2', 3, 'A1'), ('h3', 1, 'A1'), ('h4', 2, 'A0'), ('h5', 1, 'A0'), ('h5', 1, 'A1')}

    def cell(kind, rnd, a, inp):
        if (inp, rnd, a) in absent:
            return {}
        return {'files': {'out/v.txt': '1 2 3' if (inp, rnd, a) == ('h2', 2, 'A1') else '1 2'}}
    r = execute('agreement-missing', d, locs={'o': 'out/v.txt'}, cell=cell)
    if not valid_checks(r):
        return
    for cid in ('K1', 'K2'):
        expect(r, cid, 'h1', 'three agreeing pairs: supported', outcome=S, n=3, n_missing=0, reason=None)
        expect(r, cid, 'h2', 'a length mismatch decides before the missing pair: not supported, reason null',
               outcome=NS, n=2, n_missing=1, reason=None)
        for inp in ('h3', 'h4', 'h5'):
            expect(r, cid, inp, 'void rule: void, missing_values, one missing pair', outcome=V, reason='missing_values', n_missing=1)
    for cid in ('K3', 'K4'):
        expect(r, cid, 'h1', 'supported', outcome=S, n=3, n_missing=0, reason=None)
        expect(r, cid, 'h2', 'disagreement first: not supported, reason null', outcome=NS, reason=None)
        expect(r, cid, 'h3', 'fail rule, arm missing: not supported, missing_values', outcome=NS, reason='missing_values', n_missing=1)
        expect(r, cid, 'h4', 'fail rule, against missing: void, missing_values', outcome=V, reason='missing_values', n_missing=1)
        expect(r, cid, 'h5', 'fail rule, both sides of one pair missing: not supported, counted once', outcome=NS,
               reason='missing_values', n_missing=1)
    expect_outcome(r, 'K1', 'per_input')
    expect_outcome(r, 'K2', NS)
    expect_outcome(r, 'K4', NS)
    check('agreement-missing: K1 h1 pairs: replicates 1..3, all agree, errors 0', lambda: same(
        r.row('K1', 'h1')['pairs'], [{'replicate': k, 'agrees': True, 'missing': False, 'max_abs_error': 0,
                                      'max_rel_error': 0} for k in (1, 2, 3)], 'pairs'))
    check('agreement-missing: K1 h2 pairs: agrees, disagrees (length), missing with agrees null and null errors', lambda: (
        same([[p['replicate'], p['agrees'], p['missing']] for p in r.row('K1', 'h2')['pairs']],
             [[1, True, False], [2, False, False], [3, None, True]], 'pairs'),
        same([r.row('K1', 'h2')['pairs'][2][key] for key in ('max_abs_error', 'max_rel_error')], [None, None], 'errors')))


M1_VALUES = {
    'A0': {'p1': [10, 12, 14], 'p2': [10, 10, 10], 'p3': [10, 10, 10], 'p4': [5, 5, 5], 'p5': [4, 4, 4]},
    'A1': {'p1': [11, 15, 13], 'p2': [12, 13, 14], 'p3': [7, 8, 9], 'p4': [5, 5, 5], 'p5': [3, 3, 3]},
}
M1_VALUES['A2'] = {k: [x + 1 for x in v] for k, v in M1_VALUES['A0'].items()}
M1_VALUES['A3'] = {k: [x + 0.5 for x in v] for k, v in M1_VALUES['A0'].items()}
M1_VALUES['A3']['p2'][1] = None


def metric_cases():
    ins = list(M1_VALUES['A0'])
    v = 'v'
    comps = [
        ni('K1', v, 'higher_better'), ni('K2', v, 'higher_better', pairing='unpaired'),
        ni('K3', v, 'higher_better', {'abs': 1}, unit='per_input_all'), ni('K4', v, 'lower_better'),
        ni('K5', v, 'lower_better', {'abs': 1}, pairing='unpaired'), sup('K6', v), sup('K7', v, {'abs': 1}),
        sup('K8', v, {'abs': 2}, pairing='unpaired'), ni('K9', v, 'higher_better', arm='A2', unit='per_input_all'),
        ni('K10', v, 'higher_better', arm='A3', unit='per_input_all'), ni('K11', v, 'higher_better', unit='per_input_all'),
        sup('K12', v, arm='A0', against='A1')]
    d = design(n_arms=4, inputs=ins, metrics=[metric(v)], replicates=3, comparisons=comps)
    r = execute('metrics-all-pairs', d, rules={v: json_rule('out/m.json', '/v')},
                cell=table_cell({'out/m.json': M1_VALUES}))
    if not valid_checks(r):
        return
    oracle_checks(r, M1_VALUES)
    # Literal spot values, independent of the oracle.
    expect(r, 'K1', 'p1', 'paired diffs [1, 3, -1]', n=3, estimate=1, lo=-1, hi=3, outcome=I, margin_value=0, sign=None)
    expect(r, 'K2', 'p1', 'unpaired: 9 differences in [-3, 5], mean 1', n=9, estimate=1, lo=-3, hi=5, outcome=I)
    expect(r, 'K6', 'p2', 'superiority lo 2 > 0: supported, sign higher', lo=2, hi=4, estimate=3, outcome=S, sign='higher')
    expect(r, 'K6', 'p3', 'superiority hi -1 < 0: supported, sign lower', outcome=S, sign='lower')
    expect(r, 'K6', 'p4', 'superiority, all differences 0: not supported', outcome=NS, sign=None)
    expect(r, 'K7', 'p5', 'superiority margin 1, diffs -1: not supported (-m <= lo, hi <= m)', outcome=NS, margin_value=1, sign=None)
    expect(r, 'K7', 'p3', 'superiority margin 1, diffs [-3, -1]: inconclusive', outcome=I, sign=None)
    expect(r, 'K8', 'p2', 'unpaired superiority margin 2, lo 2 not above 2: inconclusive', outcome=I, lo=2, hi=4, n=9, margin_value=2)
    expect(r, 'K3', 'p5', 'non-inferiority higher margin 1, lo -1 >= -1 (edge): supported', outcome=S, margin_value=1)
    expect(r, 'K4', 'p2', 'non-inferiority lower, lo 2 > 0: not supported', outcome=NS)
    expect(r, 'K4', 'p4', 'non-inferiority lower, hi 0 <= 0 (edge): supported', outcome=S)
    expect(r, 'K12', 'p3', 'reversed arms: diffs [3, 2, 1], sign higher', outcome=S, sign='higher', lo=1, hi=3)
    expect(r, 'K10', 'p2', 'one missing replicate of A3: void, missing_values', outcome=V, reason='missing_values', n_missing=1)
    expect_outcome(r, 'K3', I)
    expect_outcome(r, 'K9', S)
    expect_outcome(r, 'K10', V)
    expect_outcome(r, 'K11', NS)
    expect_outcome(r, 'K1', 'per_input')


M2_VALUES = {'A0': {'q1': [10, 10], 'q2': [10, None], 'q3': [10, None], 'q4': [10, 10]},
             'A1': {'q1': [None, 12], 'q2': [11, 12], 'q3': [None, 12], 'q4': [11, 13]}}


def missing_and_reference_cases():
    ins = list(M2_VALUES['A0'])
    v = 'v'
    comps = [ni('K1', v, 'higher_better'), ni('K2', v, 'higher_better', missing='fail'),
             ni('K3', v, 'higher_better', pairing='unpaired', missing='fail'),
             ni('K4', v, 'higher_better', {'abs': 1}, missing='fail', **vs_ref({'q1': 10, 'q2': 10, 'q3': 10, 'q4': 12})),
             sup('K5', v, **vs_ref({'q1': 10, 'q2': 10, 'q3': 10, 'q4': 12})),
             ni('K6', v, 'higher_better', unit='per_input_all', missing='fail'),
             ni('K7', v, 'higher_better', unit='per_input_all')]
    d = design(inputs=ins, metrics=[metric(v)], replicates=2, comparisons=comps)
    r = execute('missing-and-reference', d, rules={v: json_rule('out/m.json', '/v')},
                cell=table_cell({'out/m.json': M2_VALUES}))
    if not valid_checks(r):
        return
    oracle_checks(r, M2_VALUES)
    expect(r, 'K1', 'q3', 'void rule: one missing value on each side: n_missing 2', outcome=V, reason='missing_values', n_missing=2)
    expect(r, 'K2', 'q1', 'fail rule, arm missing: not supported, missing_values', outcome=NS, reason='missing_values', n_missing=1)
    expect(r, 'K2', 'q2', 'fail rule, only against missing: void, missing_values', outcome=V, reason='missing_values', n_missing=1)
    expect(r, 'K3', 'q4', 'unpaired: 4 differences [1, 1, 3, 3]', n=4, estimate=2, lo=1, hi=3, outcome=S)
    expect(r, 'K4', 'q2', 'reference 10: diffs [1, 2]', n=2, n_missing=0, estimate=1.5, lo=1, hi=2, outcome=S, margin_value=1)
    expect(r, 'K4', 'q1', 'reference, fail rule, arm missing: not supported', outcome=NS, reason='missing_values', n_missing=1)
    expect(r, 'K5', 'q4', 'reference 12: diffs [-1, 1]: inconclusive', estimate=0, lo=-1, hi=1, outcome=I, sign=None)
    expect(r, 'K5', 'q2', 'reference 10: superiority supported, sign higher', outcome=S, sign='higher')
    expect_outcome(r, 'K6', NS)
    expect_outcome(r, 'K7', V)
    check('missing-and-reference: totals 8 supported, 8 not supported, 1 inconclusive, 11 void', lambda: same(
        r.scored['totals'], {'supported': 8, 'not_supported': 8, 'inconclusive': 1, 'void': 11}, 'totals'))


def given_cases():
    ins = ['u1', 'u2', 'u3']
    values = {'A0': {i: [10, 10] for i in ins}, 'A1': {'u1': [11, 12], 'u2': [12, 11], 'u3': [10, 13]}}
    wvalues = {'A0': values['A0'], 'A1': {'u1': [None, 12], 'u2': [12, None], 'u3': [10, 13]}}
    v, w = 'v', 'w'
    comps = [
        agreement('K1', 'o', 'elementwise_abs', {'abs': 0}),
        ni('K2', v, 'higher_better', given=['K1']),
        ni('K3', v, 'higher_better', unit='per_input_all', given=['K1']),
        ratio('K4', v, 'higher_better', 1, False, given=['K1']),
        ni('K5', v, 'higher_better', unit='per_input_all'),
        ratio('K6', v, 'higher_better', 1, False, given=['K5']),
        ni('K7', v, 'higher_better', given=['K6']),
        ni('K8', v, 'higher_better', given=['K2', 'K4']),
        ni('K9', w, 'higher_better', given=['K1']),
        agreement('K10', 'o', 'elementwise_abs', {'abs': 0}, given=['K2']),
        ni('K11', v, 'higher_better', unit='per_input_all', given=['K3']),
        ni('K12', v, 'higher_better', given=['K11', 'K7'])]
    d = design(inputs=ins, outputs=[output('o', 'text_numbers')], metrics=[metric(v), metric(w)], replicates=2,
               comparisons=comps)

    def extra(kind, rnd, a, inp, spec):
        spec['files']['out/o.txt'] = '1 3' if (inp, rnd, a) == ('u2', 1, 'A1') else '1 2'
    r = execute('given', d, locs={'o': 'out/o.txt'},
                rules={v: json_rule('out/m.json', '/v'), w: json_rule('out/w.json', '/v')},
                cell=table_cell({'out/m.json': values, 'out/w.json': wvalues}, extra=extra))
    if not valid_checks(r):
        return
    ne = dict(outcome=V, reason='not_eligible', estimate=None, lo=None, hi=None)
    expect(r, 'K1', 'u2', 'agreement disagrees on replicate 1', outcome=NS)
    expect(r, 'K2', 'u1', 'eligible (K1 u1 supported): decided', outcome=S, lo=1, hi=2, estimate=1.5, reason=None)
    expect(r, 'K2', 'u2', 'K1 u2 not supported: void, not_eligible', **ne)
    expect(r, 'K2', 'u3', 'eligible: decided', outcome=S, lo=0, hi=3, reason=None)
    expect(r, 'K3', 'u2', 'per_input_all given per_input_each: row-wise, void not_eligible', **ne)
    expect_outcome(r, 'K3', V)
    expect(r, 'K4', None, 'pooled given a per_input_each comparison with a row not supported: void, not_eligible', **ne)
    expect_outcome(r, 'K5', S)
    expect(r, 'K6', None, 'pooled given a supported per_input_all: decided (resample ratios in [1.1, 1.2])',
           outcome=S, reason=None, estimate=1.15, threshold=1, sign=None)
    for inp in ins:
        expect(r, 'K7', inp, 'given a supported pooled comparison: decided', outcome=S, reason=None)
        expect(r, 'K8', inp, 'given a void pooled comparison: void, not_eligible', **ne)
    expect(r, 'K9', 'u1', 'eligible but a missing value: void, missing_values', outcome=V, reason='missing_values', n_missing=1)
    expect(r, 'K9', 'u2', 'eligibility decides before missing values: not_eligible', **ne)
    expect(r, 'K9', 'u3', 'eligible and complete: supported', outcome=S, reason=None)
    expect(r, 'K10', 'u1', 'agreement given K2: eligible, supported', outcome=S, reason=None)
    expect(r, 'K10', 'u2', 'eligibility decides before a disagreement: void, not_eligible', outcome=V, reason='not_eligible')
    expect(r, 'K11', 'u2', 'given a per_input_all void row: not_eligible', **ne)
    expect(r, 'K11', 'u1', 'given a per_input_all supported row: supported', outcome=S, reason=None)
    expect(r, 'K12', 'u1', 'given two per-input comparisons, both supported on u1: decided', outcome=S, reason=None)
    expect(r, 'K12', 'u2', 'given two per-input comparisons, K11 u2 void: not_eligible', **ne)
    expect(r, 'K12', 'u3', 'decided', outcome=S, reason=None)


# ---- Bootstrap -----------------------------------------------------------------------------------------------
def pooled(values, arm, inputs, reps):
    out = []
    for k in range(reps):
        xs = [values[arm][i][k] for i in inputs]
        out.append(None if any(x is None for x in xs) else sum(xs) / len(xs))
    return out


def bootstrap(rng, arm, against, direction, B, conf, method):
    n = len(arm)

    def ratio_of(idx):
        a = sum(arm[i] for i in idx) / len(idx)
        b = sum(against[i] for i in idx) / len(idx)
        return a / b if direction == 'higher_better' else b / a
    est = ratio_of(range(n))
    rs = []
    for _ in range(B):
        idx = [rng.randrange(n) for _ in range(n)] if method == 'randrange' else rng.choices(range(n), k=n)
        rs.append(ratio_of(idx))
    rs.sort()
    return est, rs[math.floor((1 - conf) / 2 * (B - 1))], rs[math.floor((1 + conf) / 2 * (B - 1))]


def ratio_outcome(lo, hi, threshold, strict):
    if strict:
        return S if lo > threshold else NS if hi <= threshold else I
    return S if lo >= threshold else NS if hi < threshold else I


def bootstrap_cases():
    ins = ['a', 'b']
    R = 8
    values = {'A0': {'a': [10, 12, 9, 11, 13, 10.5, 9.5, 12.5], 'b': [20, 18, 22, 21, 19, 23, 20.5, 18.5]},
              'A1': {'a': [5, 6, 7, 5, 6.5, 5.5, 7.5, 4.5], 'b': [9, 10, 8, 12, 11, 9.5, 8.5, 10.5]}}
    values['A2'] = {k: [2 * x for x in xs] for k, xs in values['A0'].items()}
    v = 'v'
    comps = [ratio('K1', v, 'lower_better', 1.5, False, 0.9),
             ratio('K2', v, 'lower_better', 2.0, True, 0.9),
             ratio('K3', v, 'higher_better', 1.9, False, 0.5, arm='A0', against='A1'),
             ratio('K4', v, 'higher_better', 2, False, arm='A2'),
             ratio('K5', v, 'higher_better', 2, True, arm='A2'),
             ratio('K6', v, 'lower_better', 0.6, False, arm='A2'),
             ratio('K7', v, 'lower_better', 0.5, False, arm='A2'),
             ratio('K8', v, 'lower_better', 0.4, True, arm='A2')]
    d = design(n_arms=3, inputs=ins, metrics=[metric(v)], replicates=R, comparisons=comps, bootstrap_resamples=1000)
    B, seed = d['bootstrap_resamples'], d['bootstrap_seed']
    r = execute('bootstrap', d, rules={v: json_rule('out/m.json', '/v')}, cell=table_cell({'out/m.json': values}))
    p = {a: pooled(values, a, ins, R) for a in ('A0', 'A1', 'A2')}
    expected = {}
    for method in ('randrange', 'choices'):
        rng = random.Random(seed)
        expected[method] = [bootstrap(rng, p[c['arm']], p[c['against']], c['direction'], B, c['confidence'], method)
                            for c in comps]
    print('note: bootstrap K1 expected (estimate, lo, hi) by randrange draws %r, by choices draws %r'
          % (expected['randrange'][0], expected['choices'][0]))
    if not valid_checks(r):
        return

    def got(cid):
        row = r.row(cid, None)
        return row['estimate'], row['lo'], row['hi']

    def reproduced():
        errors = {}
        for method, rows in expected.items():
            try:
                for c, (est, lo, hi) in zip(comps[:3], rows[:3]):
                    same(list(got(c['id'])), [est, lo, hi], '%s (%s draws)' % (c['id'], method))
                print('note: bootstrap intervals match the %s draws' % method)
                return
            except AssertionError as error:
                errors[method] = str(error)
        raise AssertionError('; '.join('%s: %s' % kv for kv in errors.items()))
    check('bootstrap: K1-K3 intervals reproduced from one random.Random(bootstrap_seed) stream in comparison order, '
          'quantile index floor(q * (B - 1))', reproduced)
    for c, (est, lo, hi) in zip(comps[:3], expected['randrange'][:3]):
        alt = expected['choices'][comps.index(c)]
        outs = {ratio_outcome(lo, hi, c['threshold'], c['strict']), ratio_outcome(alt[1], alt[2], c['threshold'], c['strict'])}
        if len(outs) == 1:
            expect(r, c['id'], None, 'outcome %s from the interval and threshold %s (strict %s)' % (outs.copy().pop(), c['threshold'], c['strict']),
                   outcome=outs.pop(), threshold=c['threshold'], reason=None, sign=None, margin_value=0, n_missing=0)
        else:
            check('%s: %s outcome follows the interval' % (r.name, c['id']), lambda c=c: same(
                r.row(c['id'], None)['outcome'], ratio_outcome(r.row(c['id'], None)['lo'], r.row(c['id'], None)['hi'],
                                                             c['threshold'], c['strict']), c['id']))
    check('bootstrap: K1 estimate is the ratio of means mean(A0)/mean(A1) for lower_better', lambda: same(
        r.row('K1', None)['estimate'], (sum(p['A0']) / R) / (sum(p['A1']) / R), 'estimate'))
    for cid, want, thr in (('K4', S, 2), ('K5', NS, 2), ('K6', NS, 0.6), ('K7', S, 0.5), ('K8', S, 0.4)):
        ratio_value = 2 if cid in ('K4', 'K5') else 0.5
        expect(r, cid, None, 'every resample ratio %s: %s' % (ratio_value, want), outcome=want, estimate=ratio_value,
               lo=ratio_value, hi=ratio_value, threshold=thr, reason=None, sign=None)
    expect_outcome(r, 'K5', NS)

    # Too few replicates, pooled missing values counted once per replicate.
    d = design(inputs=ins, metrics=[metric(v)], replicates=1, comparisons=[
        ratio('K1', v, 'higher_better', 1, False), ni('K2', v, 'higher_better')])
    one = {'A0': {'a': [10], 'b': [10]}, 'A1': {'a': [11], 'b': [12]}}
    r = execute('bootstrap-one-replicate', d, rules={v: json_rule('out/m.json', '/v')}, cell=table_cell({'out/m.json': one}))
    if valid_checks(r):
        expect(r, 'K1', None, 'one replicate: void, insufficient_replicates', outcome=V, reason='insufficient_replicates',
               estimate=None, lo=None, hi=None, n_missing=0)
        expect(r, 'K2', 'a', 'all_pairs needs one difference: decided', outcome=S, n=1, estimate=1)
    pv = {'A0': {'a': [10, 10, None], 'b': [10, 10, 10]}, 'A1': {'a': [5, None, 5], 'b': [5, None, 5]},
          'A2': {'a': [20, 20, 20], 'b': [20, 20, 20]}}
    d = design(n_arms=3, inputs=ins, metrics=[metric(v)], replicates=3, comparisons=[
        ratio('K1', v, 'lower_better', 1, False), ratio('K2', v, 'lower_better', 1, False, missing='fail'),
        ratio('K3', v, 'higher_better', 1, False, arm='A2', missing='fail')])
    r = execute('bootstrap-pooled-missing', d, rules={v: json_rule('out/m.json', '/v')}, cell=table_cell({'out/m.json': pv}))
    if valid_checks(r):
        expect(r, 'K1', None, 'pooled: a replicate missing two inputs counts once, plus against: n_missing 2, void',
               outcome=V, reason='missing_values', n_missing=2)
        expect(r, 'K2', None, 'fail rule, arm missing: not supported, missing_values', outcome=NS, reason='missing_values', n_missing=2)
        expect(r, 'K3', None, 'fail rule, only against missing: void, missing_values', outcome=V, reason='missing_values', n_missing=1)


def warmup_cases():
    v = 'v'
    values = {'A0': {'x': [10, 10]}, 'A1': {'x': [11, 12]}}
    d = design(inputs=['x'], outputs=[output('o', 'text_numbers')], metrics=[metric(v)], replicates=2, warmup=2,
               comparisons=[ni('K1', v, 'higher_better'), ni('K2', v, 'higher_better', pairing='unpaired'),
                            agreement('K3', 'o', 'elementwise_abs', {'abs': 0})])

    def extra(kind, rnd, a, inp, spec):
        if kind == 'warmup':
            spec['files']['out/m.json'] = json.dumps({'v': 1000 if a == 'A0' else 0})
            spec['files']['out/o.txt'] = '9 9 9' if a == 'A1' else '1'
            if rnd == 2 and a == 'A1':
                spec['wrap'] = wrap('failed')
        else:
            spec['files']['out/o.txt'] = '1 2'
    r = execute('warmup-ignored', d, locs={'o': 'out/o.txt'}, rules={v: json_rule('out/m.json', '/v')},
                cell=table_cell({'out/m.json': values}, extra=extra))
    if valid_checks(r):
        expect(r, 'K1', 'x', 'replicate rounds only: paired diffs [1, 2]', outcome=S, n=2, n_missing=0, lo=1, hi=2, estimate=1.5)
        expect(r, 'K2', 'x', 'replicate rounds only: 4 unpaired differences', outcome=S, n=4, n_missing=0, lo=1, hi=2)
        expect(r, 'K3', 'x', 'replicate rounds only: two agreeing pairs', outcome=S, n=2, n_missing=0)


def empty_cases():
    d = design(inputs=['in1'], metrics=[metric('wall', 'trusted_wall')], comparisons=[])
    r = execute('no-comparisons', d)
    if valid_checks(r):
        check('no-comparisons: comparisons [] and zero totals', lambda: (
            same(r.scored['comparisons'], [], 'comparisons'),
            same(r.scored['totals'], {'supported': 0, 'not_supported': 0, 'inconclusive': 0, 'void': 0}, 'totals')))


def main():
    try:
        if not os.path.isfile(SCRIPT):
            raise SystemExit('m5/score_comparison.py missing')
        invalid_cases()
        wall_cases()
        json_extraction_cases()
        regex_extraction_cases()
        comparator_cases()
        format_cases()
        agreement_missing_cases()
        metric_cases()
        missing_and_reference_cases()
        given_cases()
        bootstrap_cases()
        warmup_cases()
        empty_cases()
    except Exception:  # noqa: BLE001
        global failures
        failures += 1
        import traceback
        print('FAIL test harness: %s' % ' '.join(traceback.format_exc().split('\n')))
    finally:
        for parent, dirs, _ in os.walk(SCRATCH):
            for directory in dirs:
                os.chmod(os.path.join(parent, directory), 0o755)
        shutil.rmtree(SCRATCH, ignore_errors=True)
    if FAILED:
        print('summary of failed checks:')
        for line in FAILED:
            print('  FAIL ' + line)
    print('%d failure(s) (%d checks)' % (failures, checks) if failures else 'all %d checks passed' % checks)
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
