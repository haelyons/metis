#!/usr/bin/env python3
"""Black-box contract tests for `python3 -I m5/score_card.py` (U54).

Contract: m5/SCHEMAS.md "Card calibration (U54)", the `A/card_inputs.json`, `A/harness/card_extract.json` and
Scoring bullets. Never inspect m5/score_card.py, the pipeline or git history: every case builds a run layout
by hand (control/, agent/harness/card_extract.json, agent/card_inputs.json and fetched outputs under
agent/results/reproduce/out/), runs the script as the pipeline does and reads only its exit status, its
output file and its diagnostics.

Usage: python3 -I tools/test_m5_card_score.py
"""
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, 'm5', 'score_card.py')
# Input content that must never appear in diagnostics ("Diagnostics contain no input content").
SENT = 'CARDSCORE_PRIVATE_SENTINEL_40917'
TOP_KEYS = ['key', 'run', 'pipeline_commit', 'box_type', 'box_started_utc', 'card_sha256', 'extract_sha256', 'predictions',
            'anchor', 'rows', 'inputs_total', 'measured_total', 'holds_total', 'refuted_total']
ROW_KEYS = ['id', 'name', 'unit', 'basis', 'value', 'band_source', 'band_lo', 'band_hi', 'measured_value', 'verdict',
            'gate_passed', 'decided_by', 'decision', 'rule']
ANCHOR_KEYS = ['published_value', 'tolerance', 'measured_value', 'difference', 'passed']

checks = 0
failures = 0
SCRATCH = tempfile.mkdtemp(prefix='test_m5_card_score_')


def check(label, fn):
    global checks, failures
    checks += 1
    try:
        fn()
        print('ok %s' % label)
    except Exception as error:  # noqa: BLE001 - every failure is reported, none stops the suite
        failures += 1
        print('FAIL %s: %s' % (label, ' '.join(str(error).split())[:1500]))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


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


# ---- Contract oracle (SCHEMAS.md Scoring bullets) ---------------------------------------------------
def band_of(item, bands):
    value = item.get('value')
    own = item.get('band')
    if item['id'] in bands:
        source, half = 'launch', bands[item['id']]['abs']
    elif isinstance(own, dict) and list(own) == ['abs'] and finite(own['abs']) and own['abs'] > 0:
        source, half = 'card', own['abs']
    else:
        source = None
    if source is not None:
        assert finite(value), 'oracle: an absolute band with a non-finite value is not used in oracle cases'
        return source, value - half, value + half
    if finite(value) and value != 0:
        k = 2.5 if item['basis'] == 'PROXY' else 3
        return ('multiplicative',) + ((value / k, value * k) if value > 0 else (value * k, value / k))
    return None, None, None


def expect_row(item, rule, measured, bands):
    source, lo, hi = band_of(item, bands)
    if measured is None:
        verdict = 'not_measured'
    elif lo is None:
        verdict = 'no_band'
    elif lo <= measured <= hi:
        verdict = 'within_band'
    else:
        verdict = 'below_band' if measured < lo else 'above_band'
    phase = item.get('phase')
    gate = phase.get('gate') if isinstance(phase, dict) else None
    gate_passed = None
    if (isinstance(gate, dict) and gate.get('on') == item['id'] and gate.get('op') in ('>=', '<=')
            and finite(gate.get('value')) and measured is not None):
        gate_passed = measured >= gate['value'] if gate['op'] == '>=' else measured <= gate['value']
    if gate_passed is not None:
        decided_by, decision = 'gate', 'holds' if gate_passed else 'refuted'
    elif verdict in ('within_band', 'below_band', 'above_band'):
        decided_by, decision = 'band', 'holds' if verdict == 'within_band' else 'refuted'
    else:
        decided_by, decision = None, 'not_measured' if measured is None else 'undecidable'
    return {'id': item['id'], 'name': item.get('name'), 'unit': item.get('unit'), 'basis': item['basis'],
            'value': item.get('value'), 'band_source': source, 'band_lo': lo, 'band_hi': hi, 'measured_value': measured,
            'verdict': verdict, 'gate_passed': gate_passed, 'decided_by': decided_by, 'decision': decision,
            'rule': {key: rule[key] for key in ('file', 'kind', 'expr')}}


# ---- One run of the script on a hand-built layout -----------------------------------------------------
def item(id_, basis, value, rule, measured, **extra):
    """A `required` item plus its extraction rule and the measured value the contract expects from it."""
    entry = {'id': id_, 'basis': basis, 'value': value, 'name': 'name of %s' % id_, 'unit': 'u/%s' % id_,
             'measured_by': 'P1', 'phase': {'id': 'P1', 'what': 'pilot run', 'stop_rule': 'stop on failure'}}
    if value is DROP:
        del entry['value']
    for key, val in extra.items():
        if val is DROP:
            entry.pop(key, None)
        else:
            entry[key] = val
    return entry, dict(rule, id=id_), measured


DROP = object()


def json_rule(file, expr):
    return {'file': file, 'kind': 'json', 'expr': expr}


def regex_rule(file, expr):
    return {'file': file, 'kind': 'regex', 'expr': expr}


RECORD_BASE = {'key': 'R1:physical:W1 ' + SENT, 'title': 'calibration fixture ' + SENT, 'state': 'calibration_required',
               'plan_usd': 868.22, 'resolved': [], 'judged': None,
               'predictions': {'if_lever': 'more than 5 points ' + SENT, 'if_not': 'within 2 points'}}


class Run:
    pass


def execute(name, items, anchor=None, rules_extra=None, files=None, bands=None, box='default', run_tag='run-tag-1',
            commit='c0ffee1', record_extra=None, tamper=None, argv=None, extract_text=None, predictions='default',
            readonly_control=False):
    """Builds R/control, R/agent and fetched outputs; runs the script; returns a Run."""
    root = os.path.join(SCRATCH, name)
    control = os.path.join(root, 'control')
    agent = os.path.join(root, 'agent')
    out = os.path.join(agent, 'results', 'reproduce', 'out')
    harness = os.path.join(agent, 'harness')
    for directory in (control, harness, out):
        os.makedirs(directory, exist_ok=True)
    record = dict(RECORD_BASE)
    record['required'] = [entry for entry, _, _ in items]
    record['anchor'] = anchor if anchor is not None else {'absent_reason': 'no published value ' + SENT}
    if predictions != 'default':
        if predictions is DROP:
            record.pop('predictions')
        else:
            record['predictions'] = predictions
    record.update(record_extra or {})
    bands = bands or {}
    card = {'source': '/nonexistent/tree-run/result.json', 'source_sha256': 'a' * 64, 'record': record, 'bands': bands}
    card_bytes = (json.dumps(card, indent=1) + '\n').encode()
    with open(os.path.join(control, 'card.json'), 'wb') as handle:
        handle.write(card_bytes)
    with open(os.path.join(control, 'card_seal.json'), 'w') as handle:
        json.dump({'card_sha256': sha(card_bytes), 'sealed_utc': '2026-11-03T09:00:00Z'}, handle)
    has_anchor = isinstance(anchor, dict) and finite(anchor.get('published_value'))
    inputs = {'inputs': [{'id': e['id'], 'name': e.get('name'), 'unit': e.get('unit'), 'measured_by': e.get('measured_by'),
                          'phase': e['phase'].get('what') if isinstance(e.get('phase'), dict) else None}
                         for e, _, _ in items],
              'anchor': {'what': anchor['what']} if has_anchor else None}
    with open(os.path.join(agent, 'card_inputs.json'), 'w') as handle:
        json.dump(inputs, handle)
    rules = [rule for _, rule, _ in items] + list(rules_extra or [])
    extract_bytes = extract_text.encode() if extract_text is not None else (json.dumps({'rules': rules}, indent=1) + '\n').encode()
    extract = os.path.join(harness, 'card_extract.json')
    with open(extract, 'wb') as handle:
        handle.write(extract_bytes)
    with open(os.path.join(control, 'card_extract_seal.json'), 'w') as handle:
        json.dump({'extract_sha256': sha(extract_bytes), 'sealed_utc': '2026-11-03T09:05:00Z'}, handle)
    if box == 'default':
        box = {'type': 'gpu_1x_a10', 'started_utc': '2026-11-03T08:59:00Z', 'gpu_count': 1, 'note': SENT}
    if isinstance(box, dict):
        with open(os.path.join(control, 'box.json'), 'w') as handle:
            json.dump(box, handle)
    elif isinstance(box, str):
        with open(os.path.join(control, 'box.json'), 'w') as handle:
            handle.write(box)
    for rel, content in (files or {}).items():
        target = os.path.join(out, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        if content is DIRECTORY:
            os.makedirs(target, exist_ok=True)
            continue
        with open(target, 'wb') as handle:
            handle.write(content if isinstance(content, bytes) else content.encode())
    if tamper:
        tamper(root)
    before = {name_: open(os.path.join(control, name_), 'rb').read() for name_ in sorted(os.listdir(control))}
    command = argv(control, extract, out) if argv else [control, extract, out, '--run', run_tag, '--commit', commit]
    if readonly_control:
        os.chmod(control, 0o555)
    try:
        proc = subprocess.run([sys.executable, '-I', SCRIPT] + command, cwd=SCRATCH, capture_output=True, timeout=120)
    finally:
        if readonly_control:
            os.chmod(control, 0o755)
    r = Run()
    r.name, r.root, r.control, r.items, r.anchor, r.bands, r.record = name, root, control, items, anchor, bands, record
    r.rc, r.stdout, r.stderr = proc.returncode, proc.stdout, proc.stderr
    r.card_bytes, r.extract_bytes, r.before = card_bytes, extract_bytes, before
    scored = os.path.join(control, 'card_scored.json')
    r.exists = os.path.exists(scored)
    r.scored = None
    if r.exists:
        with open(scored) as handle:
            r.scored = json.load(handle)
    r.control_after = sorted(os.listdir(control))
    return r


DIRECTORY = object()


def no_leak(r):
    check('%s: diagnostics carry no input content' % r.name, lambda: (
        assert_(SENT.encode() not in r.stdout + r.stderr, 'sentinel in diagnostics: %r' % (r.stdout + r.stderr)[-300:])))


def assert_(condition, message):
    assert condition, message


def valid_checks(r, expected_rows=True):
    """Exit 0, exact output keys, rows from the oracle, totals, inputs unchanged, no stray files."""
    check('%s: exit 0 and control/card_scored.json written' % r.name, lambda: (
        assert_(r.rc == 0, 'exit %s; stderr %s' % (r.rc, r.stderr[-600:])), assert_(r.exists, 'no card_scored.json')))
    no_leak(r)
    if not r.exists:
        return

    def keys():
        assert list(sorted(r.scored)) == sorted(TOP_KEYS), 'keys %s' % sorted(r.scored)
        for i, row in enumerate(r.scored['rows']):
            assert sorted(row) == sorted(ROW_KEYS), 'row %d keys %s' % (i, sorted(row))
        if r.scored['anchor'] is not None:
            assert sorted(r.scored['anchor']) == sorted(ANCHOR_KEYS), 'anchor keys %s' % sorted(r.scored['anchor'])
    check('%s: exact keys of the file, every row and the anchor' % r.name, keys)

    def order():
        assert [row['id'] for row in r.scored['rows']] == [e['id'] for e, _, _ in r.items]
    check('%s: rows follow `required` order, one per item' % r.name, order)
    if expected_rows:
        for entry, rule, measured in r.items:
            def one(entry=entry, rule=rule, measured=measured):
                row = next(row for row in r.scored['rows'] if row['id'] == entry['id'])
                same(row, expect_row(entry, rule, measured, r.bands), entry['id'])
            check('%s: row %s as the contract computes it' % (r.name, entry['id']), one)

    def totals():
        rows = r.scored['rows']
        same(r.scored['inputs_total'], len(rows), 'inputs_total')
        same(r.scored['measured_total'], sum(1 for row in rows if finite(row['measured_value'])), 'measured_total')
        same(r.scored['holds_total'], sum(1 for row in rows if row['decision'] == 'holds'), 'holds_total')
        same(r.scored['refuted_total'], sum(1 for row in rows if row['decision'] == 'refuted'), 'refuted_total')
        for key in ('inputs_total', 'measured_total', 'holds_total', 'refuted_total'):
            assert type(r.scored[key]) is int and r.scored[key] >= 0, key
    check('%s: totals count rows, measured rows, holds and refuted' % r.name, totals)

    def seals():
        assert r.scored['card_sha256'] == sha(r.card_bytes)
        assert r.scored['extract_sha256'] == sha(r.extract_bytes)
        assert r.scored['key'] == r.record['key']
    check('%s: key, card_sha256 and extract_sha256' % r.name, seals)

    def untouched():
        for name_, data in r.before.items():
            with open(os.path.join(r.control, name_), 'rb') as handle:
                assert handle.read() == data, '%s changed' % name_
        assert r.control_after == sorted(list(r.before) + ['card_scored.json']), 'control/ holds %s' % r.control_after
    check('%s: inputs unchanged; only card_scored.json added (atomic write leaves no temporary file)' % r.name, untouched)


def invalid_checks(r, what):
    check('%s: %s exits 1 with no output file' % (r.name, what), lambda: (
        assert_(r.rc == 1, 'exit %s; stderr %s' % (r.rc, r.stderr[-400:])), assert_(not r.exists, 'card_scored.json written'),
        assert_(r.control_after == sorted(r.before), 'control/ holds %s' % r.control_after)))
    no_leak(r)


# ---- Cases ------------------------------------------------------------------------------------------
M = 'm/metrics.json'
LOG = 'logs/run_1+x=y.txt'
METRICS = json.dumps({'rates': {'thr': 2, 'hi': 12.5, 'below': 1.999, 'above': 18.0001, 'g_edge': 2, 'neg': -3.5,
                                'neg2': -1.5, 'zero': 3, 'card_b': 10.5, 'launch_b': 10.3, 'launch_zero': -2, 'card_neg': -4,
                                'card_rel': 13, 'str_val': 7, 'bool_val': 1, 'gate_ge': 3000, 'gate_override': 5500,
                                'gate_le': 20, 'gate_other': 100, 'gate_bad_op': 100, 'gate_str_val': 3,
                                'gate_no_on': 1, 'gate_noband': 0, 'gate_not_obj': 4, 'no_phase': 12, 'nameless': 9,
                                'gate_le_fail': 51},
                      'note': SENT})


def gate(on, op, value, **extra):
    return dict({'on': on, 'op': op, 'value': value, 'else': 'drop the last level'}, **extra)


def phase(gate_value=None, **extra):
    entry = {'id': 'P1', 'what': 'pilot run'}
    if gate_value is not None:
        entry['gate'] = gate_value
    entry.update(extra)
    return entry


def r_(id_):
    return json_rule(M, '/rates/' + id_)


BAND_ITEMS = [
    # Multiplicative band, PROXY k = 2.5 and GUESS k = 3; edges inclusive.
    item('thr', 'PROXY', 5, r_('thr'), 2),                     # [2, 12.5]: lower edge holds
    item('hi', 'PROXY', 5, r_('hi'), 12.5),                    # upper edge holds
    item('below', 'PROXY', 5, r_('below'), 1.999),             # below_band refutes
    item('above', 'GUESS', 6, r_('above'), 18.0001),           # [2, 18]: above_band refutes
    item('g_edge', 'GUESS', 6, r_('g_edge'), 2),               # GUESS lower edge
    item('neg', 'GUESS', -10, r_('neg'), -3.5),                # negative value: [-30, -10/3]
    item('neg2', 'PROXY', -4, r_('neg2'), -1.5),               # [-10, -1.6]: above_band
    item('zero', 'GUESS', 0, r_('zero'), 3),                   # value 0: no band, undecidable
    # Card band {abs: x}; launch band takes precedence over the card band and the multiplicative band.
    item('card_b', 'GUESS', 10, r_('card_b'), 10.5, band={'abs': 0.5}),
    item('launch_b', 'PROXY', 10, r_('launch_b'), 10.3, band={'abs': 100}),
    item('launch_zero', 'GUESS', 0, r_('launch_zero'), -2),    # launch band with value 0: [-2, 2]
    item('card_neg', 'PROXY', -3, r_('card_neg'), -4, band={'abs': 1}),
    item('card_rel', 'GUESS', 4, r_('card_rel'), 13, band={'rel': 0.5}),   # not {abs: x}: multiplicative [4/3, 12]
    # Values that are not finite numbers: no band.
    item('str_val', 'GUESS', '7', r_('str_val'), 7),
    item('null_val', 'PROXY', None, json_rule('m/absent.json', '/x'), None),
    item('bool_val', 'GUESS', True, r_('bool_val'), 1),
    item('missing_val', 'GUESS', DROP, r_('thr'), 2),          # no `value` key at all
    # Gates: decide over the band; >= and <=; on another id or malformed: band decides.
    item('gate_ge', 'PROXY', 5000, r_('gate_ge'), 3000, phase=phase(gate('gate_ge', '>=', 3000))),
    item('gate_override', 'PROXY', 5000, r_('gate_override'), 5500, phase=phase(gate('gate_override', '>=', 6000))),
    item('gate_le', 'GUESS', 100, r_('gate_le'), 20, phase=phase(gate('gate_le', '<=', 50))),
    item('gate_le_fail', 'GUESS', 100, r_('gate_le_fail'), 51, phase=phase(gate('gate_le_fail', '<=', 50))),
    item('gate_other', 'PROXY', 5, r_('gate_other'), 100, phase=phase(gate('thr', '>=', 1))),
    item('gate_bad_op', 'PROXY', 50, r_('gate_bad_op'), 100, phase=phase(gate('gate_bad_op', '>', 1))),
    item('gate_str_val', 'GUESS', 2, r_('gate_str_val'), 3, phase=phase(gate('gate_str_val', '>=', '1'))),
    item('gate_no_on', 'GUESS', 2, r_('gate_no_on'), 1, phase=phase({'op': '>=', 'value': 0})),
    item('gate_unmeasured', 'PROXY', 5, json_rule(M, '/rates/nothing_here'), None,
         phase=phase(gate('gate_unmeasured', '>=', 1))),
    item('gate_noband', 'GUESS', 0, r_('gate_noband'), 0, phase=phase(gate('gate_noband', '>=', -1))),
    item('gate_not_obj', 'GUESS', 4, r_('gate_not_obj'), 4, phase=phase('gate_not_obj >= 3')),
    item('no_phase', 'GUESS', 4, r_('no_phase'), 12, phase=DROP),
    item('nameless', 'PROXY', 9, r_('nameless'), 9, name=DROP, unit=DROP),
]
BANDS = {'launch_b': {'abs': 0.25}, 'launch_zero': {'abs': 2}}

TEXT = ('rate=1\nrate=2\nwarmup ' + SENT + '\nrate=3.5\nsci 2.5e3 done\nnan=nan\ninf=inf\nhuge=1e400\nbad=1.2.3\n'
        'opt=xy\nnamed: 41\n').encode() + b'\xff\xfe bytes=17 \xc3\x28\n'
EXTRACT_ITEMS = [
    item('j_int', 'GUESS', 0, json_rule('x/v.json', '/int'), 7),
    item('j_neg', 'GUESS', 0, json_rule('x/v.json', '/neg'), -2.25),
    item('j_array', 'GUESS', 0, json_rule('x/v.json', '/list/1'), 20.5),
    item('j_escape', 'GUESS', 0, json_rule('x/v.json', '/a~1b/c~0d'), 3),
    item('j_bool', 'GUESS', 0, json_rule('x/v.json', '/flag'), None),
    item('j_string', 'GUESS', 0, json_rule('x/v.json', '/str'), None),
    item('j_null', 'GUESS', 0, json_rule('x/v.json', '/nul'), None),
    item('j_missing_key', 'GUESS', 0, json_rule('x/v.json', '/no/such'), None),
    item('j_index_out', 'GUESS', 0, json_rule('x/v.json', '/list/7'), None),
    item('j_object', 'GUESS', 0, json_rule('x/v.json', '/a~1b'), None),
    item('j_nan', 'GUESS', 0, json_rule('x/nan.json', '/v'), None),
    item('j_inf', 'GUESS', 0, json_rule('x/inf.json', '/v'), None),
    item('j_huge', 'GUESS', 0, json_rule('x/huge.json', '/v'), None),
    item('j_bad_json', 'GUESS', 0, json_rule('x/bad.json', '/v'), None),
    item('j_missing_file', 'GUESS', 0, json_rule('x/none.json', '/v'), None),
    item('j_directory', 'GUESS', 0, json_rule('x/dir.json', '/v'), None),
    item('j_whole', 'GUESS', 0, json_rule('x/whole.json', ''), 64),
    item('x_last', 'GUESS', 0, regex_rule(LOG, r'rate=([0-9.]+)'), 3.5),
    item('x_sci', 'GUESS', 0, regex_rule(LOG, r'sci (\S+) done'), 2500),
    item('x_nomatch', 'GUESS', 0, regex_rule(LOG, r'absent=(\d+)'), None),
    item('x_nan', 'GUESS', 0, regex_rule(LOG, r'nan=(\w+)'), None),
    item('x_inf', 'GUESS', 0, regex_rule(LOG, r'inf=(\w+)'), None),
    item('x_huge', 'GUESS', 0, regex_rule(LOG, r'huge=(\S+)'), None),
    item('x_unparsable', 'GUESS', 0, regex_rule(LOG, r'bad=(\S+)'), None),
    item('x_optional', 'GUESS', 0, regex_rule(LOG, r'opt=x(\d+)?y'), None),
    item('x_named', 'GUESS', 0, regex_rule(LOG, r'(?:named): (?P<v>\d+)'), 41),
    item('x_bytes', 'GUESS', 0, regex_rule(LOG, r'bytes=(\d+)'), 17),
    item('x_missing_file', 'GUESS', 0, regex_rule('logs/none.txt', r'rate=(\d+)'), None),
    item('x_bool_like', 'GUESS', 0, regex_rule(LOG, r'(True)'), None),
]
EXTRACT_FILES = {
    'x/v.json': json.dumps({'int': 7, 'neg': -2.25, 'list': [1, 20.5, 3], 'a/b': {'c~d': 3}, 'flag': True, 'str': '5',
                            'nul': None, 'secret': SENT}),
    'x/nan.json': '{"v": NaN}', 'x/inf.json': '{"v": Infinity}', 'x/huge.json': '{"v": 1e400}',
    'x/bad.json': '{"v": 1,', 'x/dir.json': DIRECTORY, 'x/whole.json': '64\n', LOG: TEXT,
}


def anchor_case(name, published, tolerance, measured_text, expect, **extra):
    """One anchor form: the record anchor plus the anchor rule reading `measured_text` (None = file absent)."""
    anchor = dict({'what': 'reproduce the published rate', 'published_value': published, 'tolerance': tolerance,
                   'source_id': 's2'}, **extra)
    files = {M: METRICS}
    if measured_text is not None:
        files['a/anchor.json'] = '{"value": %s}' % measured_text
    r = execute('anchor-' + name, [item('thr', 'PROXY', 5, r_('thr'), 2)], anchor=anchor,
                rules_extra=[json_rule('a/anchor.json', '/value') | {'id': 'anchor'}], files=files)
    valid_checks(r)

    def anchored():
        same(r.scored['anchor'], dict(expect, published_value=published, tolerance=tolerance), 'anchor')
    check('%s: anchor object (%s)' % (r.name, name), anchored)

    def rows_unaffected():
        same(r.scored['rows'][0], expect_row(*r.items[0][:2], 2, {}), 'thr')
    check('%s: the anchor never decides an input' % r.name, rows_unaffected)


def rerun(r, tag='run-tag-1', commit='c0ffee1'):
    """Runs the script again on an existing layout, as the pipeline does."""
    out = os.path.join(r.root, 'agent', 'results', 'reproduce', 'out')
    extract = os.path.join(r.root, 'agent', 'harness', 'card_extract.json')
    proc = subprocess.run([sys.executable, '-I', SCRIPT, r.control, extract, out, '--run', tag, '--commit', commit],
                          cwd=SCRATCH, capture_output=True, timeout=120)
    return proc


def review_cases():
    """Review of U54/U56 (2026-11-03): positional rules with an input named `anchor`, integers too long for a double,
    and a failed run that never leaves a card_scored.json behind."""
    # Rules belong to inputs by position; an input whose id is `anchor` is matched like any other.
    files = {'k/in.json': json.dumps({'v': 10}), 'k/pub.json': json.dumps({'v': 100}), M: METRICS}
    lone = execute('input-named-anchor-no-anchor', [item('anchor', 'GUESS', 8, json_rule('k/in.json', '/v'), 10)], files=files)
    valid_checks(lone)
    if lone.exists:
        check('input-named-anchor-no-anchor: the input `anchor` is scored like any other; anchor object null', lambda: (
            same(lone.scored['rows'][0]['measured_value'], 10, 'measured_value'),
            same(lone.scored['rows'][0]['decision'], 'holds', 'decision'),
            same(lone.scored['anchor'], None, 'anchor')))
    pub = {'what': 'reproduce the published rate', 'published_value': 100, 'tolerance': 5, 'source_id': 's2'}
    both = execute('input-named-anchor-with-anchor',
                   [item('thr', 'PROXY', 5, r_('thr'), 2), item('anchor', 'GUESS', 8, json_rule('k/in.json', '/v'), 10)],
                   anchor=pub, rules_extra=[dict(json_rule('k/pub.json', '/v'), id='anchor')], files=files)
    valid_checks(both)
    if both.exists:
        def by_position():
            row = both.scored['rows'][1]
            same(row['id'], 'anchor', 'row id')
            same(row['measured_value'], 10, 'input row measured by the input rule (the second rule)')
            same(row['rule'], json_rule('k/in.json', '/v'), 'input row rule')
            same(both.scored['anchor'], {'published_value': 100, 'tolerance': 5, 'measured_value': 100, 'difference': 0,
                                         'passed': True}, 'anchor object measured by the anchor rule (the last rule)')
        check('input-named-anchor-with-anchor: input row uses the input rule, the anchor object the anchor rule', by_position)

    # A json value that is an integer too long for a double is not a finite number: unmeasured, exit 0.
    big = '9' * 400
    huge = execute('json-integer-too-long', [
        item('long_int', 'GUESS', 5, json_rule('h/big.json', '/v'), None),
        item('long_neg', 'GUESS', 5, json_rule('h/big.json', '/n'), None),
        item('long_top', 'GUESS', 5, json_rule('h/top.json', ''), None),
        item('thr', 'PROXY', 5, r_('thr'), 2)],
        files={'h/big.json': '{"v": %s, "n": -%s}' % (big, big), 'h/top.json': big + '\n', M: METRICS})
    valid_checks(huge)
    if huge.exists:
        check('json-integer-too-long: 400-digit integers give unmeasured rows (measured_value null, not_measured)', lambda: [
            same([row['measured_value'], row['verdict'], row['decision']], [None, 'not_measured', 'not_measured'], row['id'])
            for row in huge.scored['rows'][:3]])

    # A failed run after an earlier successful one: exit 1 and no card_scored.json left.
    for name, tamper in (('card-altered', lambda root: open(os.path.join(root, 'control', 'card.json'), 'ab').write(b' ')),
                         ('extract-altered', lambda root: open(os.path.join(root, 'agent', 'harness', 'card_extract.json'),
                                                                'ab').write(b' ')),
                         ('card-seal-removed', lambda root: os.remove(os.path.join(root, 'control', 'card_seal.json')))):
        first = execute('stale-' + name, [item('thr', 'PROXY', 5, r_('thr'), 2)], files={M: METRICS})
        check('stale-%s: the first run exits 0 and writes card_scored.json' % name,
              lambda first=first: assert_(first.rc == 0 and first.exists, 'exit %s' % first.rc))
        tamper(first.root)
        proc = rerun(first)
        scored = os.path.join(first.control, 'card_scored.json')
        check('stale-%s: the failed rerun exits 1 and leaves no card_scored.json' % name, lambda proc=proc, scored=scored: (
            assert_(proc.returncode == 1, 'exit %s; %s' % (proc.returncode, proc.stderr[-300:])),
            assert_(not os.path.exists(scored), 'the earlier card_scored.json is still there'),
            assert_(not [f for f in os.listdir(first.control) if f not in ('card.json', 'card_seal.json',
                     'card_extract_seal.json', 'box.json')], 'control/ holds %s' % os.listdir(first.control))))
        check('stale-%s: diagnostics carry no input content' % name,
              lambda proc=proc: assert_(SENT.encode() not in proc.stdout + proc.stderr, 'sentinel in diagnostics'))


def main():
    try:
        if not os.path.isfile(SCRIPT):
            raise SystemExit('m5/score_card.py missing')
        review_cases()
        # 1. Bands, gates, verdicts and decisions on one card.
        bands = execute('bands-and-gates', BAND_ITEMS, bands=BANDS, files={M: METRICS})
        valid_checks(bands)

        def spot():
            rows = {row['id']: row for row in bands.scored['rows']}
            literal = {
                'thr': ('multiplicative', 2, 12.5, 'within_band', None, 'band', 'holds'),
                'below': ('multiplicative', 2, 12.5, 'below_band', None, 'band', 'refuted'),
                'above': ('multiplicative', 2, 18, 'above_band', None, 'band', 'refuted'),
                'neg2': ('multiplicative', -10, -1.6, 'above_band', None, 'band', 'refuted'),
                'zero': (None, None, None, 'no_band', None, None, 'undecidable'),
                'card_b': ('card', 9.5, 10.5, 'within_band', None, 'band', 'holds'),
                'launch_b': ('launch', 9.75, 10.25, 'above_band', None, 'band', 'refuted'),
                'launch_zero': ('launch', -2, 2, 'within_band', None, 'band', 'holds'),
                'card_neg': ('card', -4, -2, 'within_band', None, 'band', 'holds'),
                'card_rel': ('multiplicative', 4 / 3, 12, 'above_band', None, 'band', 'refuted'),
                'str_val': (None, None, None, 'no_band', None, None, 'undecidable'),
                'null_val': (None, None, None, 'not_measured', None, None, 'not_measured'),
                'gate_ge': ('multiplicative', 2000, 12500, 'within_band', True, 'gate', 'holds'),
                'gate_override': ('multiplicative', 2000, 12500, 'within_band', False, 'gate', 'refuted'),
                'gate_le': ('multiplicative', 100 / 3, 300, 'below_band', True, 'gate', 'holds'),
                'gate_le_fail': ('multiplicative', 100 / 3, 300, 'within_band', False, 'gate', 'refuted'),
                'gate_other': ('multiplicative', 2, 12.5, 'above_band', None, 'band', 'refuted'),
                'gate_unmeasured': ('multiplicative', 2, 12.5, 'not_measured', None, None, 'not_measured'),
                'gate_noband': (None, None, None, 'no_band', True, 'gate', 'holds'),
            }
            for id_, want in literal.items():
                got = tuple(rows[id_][key] for key in ('band_source', 'band_lo', 'band_hi', 'verdict', 'gate_passed',
                                                       'decided_by', 'decision'))
                same(list(got), list(want), id_)
            same([rows['nameless']['name'], rows['nameless']['unit']], [None, None], 'nameless name/unit')
            same(rows['missing_val']['value'], None, 'missing value copies as null')
            same(rows['gate_ge']['rule'], {'file': M, 'kind': 'json', 'expr': '/rates/gate_ge'}, 'rule without id')
        check('bands-and-gates: literal spot values (independent of the oracle)', spot)

        # 2. Absolute band with a value that is not a finite number: no band (lo/hi null, verdict no_band).
        odd = execute('absolute-band-nonfinite-value', [
            item('lv', 'GUESS', None, r_('thr'), 2), item('cv', 'PROXY', 'x', r_('thr'), 2, band={'abs': 1})],
            bands={'lv': {'abs': 1}}, files={M: METRICS})
        check('absolute-band-nonfinite-value: exit 0', lambda: assert_(odd.rc == 0 and odd.exists, 'exit %s %s' % (odd.rc, odd.stderr[-300:])))
        if odd.exists:
            def nonfinite_band():
                for row in odd.scored['rows']:
                    same([row['band_lo'], row['band_hi'], row['verdict'], row['decided_by'], row['decision']],
                         [None, None, 'no_band', None, 'undecidable'], row['id'])
            check('absolute-band-nonfinite-value: launch or card band without a finite value gives no band', nonfinite_band)

        # 3. Extraction rules: json and regex.
        extraction = execute('extraction', EXTRACT_ITEMS, files=EXTRACT_FILES)
        valid_checks(extraction)

        def measured_spot():
            rows = {row['id']: row['measured_value'] for row in extraction.scored['rows']}
            for entry, _, measured in EXTRACT_ITEMS:
                got = rows[entry['id']]
                if measured is None:
                    assert got is None, '%s: %r should be unmeasured' % (entry['id'], got)
                else:
                    assert finite(got) and math.isclose(got, measured), '%s: %r != %r' % (entry['id'], got, measured)
        check('extraction: measured values (last regex match; booleans, strings, nonfinite, missing unmeasured)', measured_spot)

        # 4. Anchor object with each tolerance form.
        anchor_case('number', 0.5, 0.25, '0.75', {'measured_value': 0.75, 'difference': 0.25, 'passed': True})
        anchor_case('number-fails', 0.5, 0.25, '0.7501', {'measured_value': 0.7501, 'difference': 0.7501 - 0.5, 'passed': False})
        anchor_case('abs', 0.5, {'abs': 0.25}, '0.25', {'measured_value': 0.25, 'difference': -0.25, 'passed': True})
        anchor_case('rel', 2, {'rel': 0.125}, '2.3', {'measured_value': 2.3, 'difference': 2.3 - 2, 'passed': False})
        anchor_case('rel-negative-published', -2, {'rel': 0.125}, '-1.75', {'measured_value': -1.75, 'difference': 0.25, 'passed': True})
        anchor_case('zero', 0, 0, '0', {'measured_value': 0, 'difference': 0, 'passed': True})
        anchor_case('string-tolerance', 0.31, '3 points', '0.3', {'measured_value': 0.3, 'difference': 0.3 - 0.31, 'passed': None})
        anchor_case('null-tolerance', 0.31, None, '0.3', {'measured_value': 0.3, 'difference': 0.3 - 0.31, 'passed': None})
        anchor_case('negative-tolerance', 0.31, -1, '0.31', {'measured_value': 0.31, 'difference': 0, 'passed': None})
        anchor_case('two-key-tolerance', 0.31, {'abs': 1, 'rel': 1}, '0.31', {'measured_value': 0.31, 'difference': 0, 'passed': None})
        anchor_case('unmeasured', 0.31, 0.05, None, {'measured_value': None, 'difference': None, 'passed': None})
        anchor_case('boolean-measurement', 0.31, 0.05, 'true', {'measured_value': None, 'difference': None, 'passed': None})
        for name, anchor in (('absent', {'absent_reason': 'none published'}),
                             ('string-published', {'what': 'rate', 'published_value': '0.31', 'tolerance': 0.1})):
            r = execute('anchor-' + name, [item('thr', 'PROXY', 5, r_('thr'), 2)], anchor=anchor, files={M: METRICS})
            valid_checks(r)
            check('%s: anchor null when card_inputs has no anchor' % r.name, lambda r=r: same(r.scored['anchor'], None, 'anchor'))

        # 5. Identity fields: box.json, --run, --commit.
        ident = execute('identity', [item('thr', 'PROXY', 5, r_('thr'), 2)], files={M: METRICS}, run_tag='blind-02-run3',
                        commit='9f1e2d3')

        def identity():
            same([ident.scored[k] for k in ('run', 'pipeline_commit', 'box_type', 'box_started_utc')],
                 ['blind-02-run3', '9f1e2d3', 'gpu_1x_a10', '2026-11-03T08:59:00Z'])
            same(ident.scored['predictions'], RECORD_BASE['predictions'], 'predictions copied unchanged')
        valid_checks(ident)
        if ident.exists:
            check('identity: run, pipeline_commit, box_type, box_started_utc, predictions', identity)
        for name, box, commit, want in (
                ('no-box-dash-commit', None, '-', [None, None, None]),
                ('box-invalid-json', '{"type": ', 'abc', ['abc', None, None]),
                ('box-partial', {'type': 'cpu_32x'}, '-', [None, 'cpu_32x', None]),
                ('box-not-object', '[1, 2]', '-', [None, None, None])):
            r = execute('identity-' + name, [item('thr', 'PROXY', 5, r_('thr'), 2)], files={M: METRICS}, box=box, commit=commit,
                        predictions=DROP)
            valid_checks(r)
            if r.exists:
                check('%s: pipeline_commit, box_type, box_started_utc; predictions null when absent' % r.name, lambda r=r, want=want: (
                    same([r.scored[k] for k in ('pipeline_commit', 'box_type', 'box_started_utc')], want),
                    same(r.scored['predictions'], None, 'predictions')))

        # 6. Invalid input: exit 1, no output, no input content in diagnostics.
        one = [item('thr', 'PROXY', 5, r_('thr'), 2)]
        anchored = {'what': 'rate', 'published_value': 0.5, 'tolerance': 0.1}
        anchor_rule = [dict(json_rule('a/anchor.json', '/value'), id='anchor')]

        def append(path_, data=b' '):
            def tamper(root):
                with open(os.path.join(root, path_), 'ab') as handle:
                    handle.write(data)
            return tamper

        def write(path_, data):
            def tamper(root):
                target = os.path.join(root, path_)
                if data is None:
                    os.remove(target)
                else:
                    with open(target, 'w') as handle:
                        handle.write(data)
            return tamper
        two = [item('thr', 'PROXY', 5, r_('thr'), 2), item('hi', 'PROXY', 5, r_('hi'), 12.5)]
        rules = lambda *rs: json.dumps({'rules': list(rs)})  # noqa: E731
        invalid = [
            ('card-seal-mismatch', 'a card.json changed after its seal', dict(items=one, tamper=append('control/card.json'))),
            ('card-seal-wrong-digest', 'a wrong card seal digest', dict(items=one, tamper=write('control/card_seal.json', json.dumps({'card_sha256': '0' * 64, 'sealed_utc': 'x'})))),
            ('extract-seal-mismatch', 'a card_extract.json changed after its seal', dict(items=one, tamper=append('agent/harness/card_extract.json'))),
            ('extract-seal-wrong-digest', 'a wrong extract seal digest', dict(items=one, tamper=write('control/card_extract_seal.json', json.dumps({'extract_sha256': 'f' * 64, 'sealed_utc': 'x'})))),
            ('missing-card', 'a missing card.json', dict(items=one, tamper=write('control/card.json', None))),
            ('missing-card-seal', 'a missing card_seal.json', dict(items=one, tamper=write('control/card_seal.json', None))),
            ('missing-extract-seal', 'a missing card_extract_seal.json', dict(items=one, tamper=write('control/card_extract_seal.json', None))),
            ('missing-extract', 'a missing card_extract.json', dict(items=one, tamper=write('agent/harness/card_extract.json', None))),
            ('card-seal-not-json', 'an unreadable card seal', dict(items=one, tamper=write('control/card_seal.json', '{' + SENT))),
            ('extract-not-json', 'card_extract.json not JSON', dict(items=one, extract_text='{"rules": [' + SENT)),
            ('extract-not-object', 'card_extract.json an array', dict(items=one, extract_text='[]')),
            ('extract-extra-top-key', 'an extra top-level key', dict(items=one, extract_text=json.dumps({'rules': [dict(r_('thr'), id='thr')], 'note': SENT}))),
            ('extract-too-few-rules', 'a missing rule', dict(items=two, extract_text=rules(dict(r_('thr'), id='thr')))),
            ('extract-too-many-rules', 'an extra rule', dict(items=one, extract_text=rules(dict(r_('thr'), id='thr'), dict(r_('hi'), id='hi')))),
            ('extract-wrong-order', 'rules out of `inputs` order', dict(items=two, extract_text=rules(dict(r_('hi'), id='hi'), dict(r_('thr'), id='thr')))),
            ('extract-wrong-id', 'a rule id that is not the input id', dict(items=one, extract_text=rules(dict(r_('thr'), id='thr_' + 'x')))),
            ('extract-extra-rule-key', 'an extra rule key', dict(items=one, extract_text=rules(dict(r_('thr'), id='thr', note=SENT)))),
            ('extract-missing-rule-key', 'a rule without expr', dict(items=one, extract_text=rules({'id': 'thr', 'file': M, 'kind': 'json'}))),
            ('extract-unknown-kind', 'an unknown kind', dict(items=one, extract_text=rules({'id': 'thr', 'file': M, 'kind': 'yaml', 'expr': '/x'}))),
            ('extract-dotdot', 'a `..` file component', dict(items=one, extract_text=rules({'id': 'thr', 'file': 'm/../metrics.json', 'kind': 'json', 'expr': '/x'}))),
            ('extract-dot', 'a `.` file component', dict(items=one, extract_text=rules({'id': 'thr', 'file': './m/metrics.json', 'kind': 'json', 'expr': '/x'}))),
            ('extract-absolute', 'an absolute file', dict(items=one, extract_text=rules({'id': 'thr', 'file': '/etc/' + SENT, 'kind': 'json', 'expr': '/x'}))),
            ('extract-empty-component', 'an empty file component', dict(items=one, extract_text=rules({'id': 'thr', 'file': 'm//metrics.json', 'kind': 'json', 'expr': '/x'}))),
            ('extract-space-in-file', 'a file outside the character set', dict(items=one, extract_text=rules({'id': 'thr', 'file': 'm/metrics ' + SENT + '.json', 'kind': 'json', 'expr': '/x'}))),
            ('extract-two-groups', 'a regex with two groups', dict(items=one, extract_text=rules({'id': 'thr', 'file': LOG, 'kind': 'regex', 'expr': '(' + SENT + ')=(\\d+)'}))),
            ('extract-no-group', 'a regex without a group', dict(items=one, extract_text=rules({'id': 'thr', 'file': LOG, 'kind': 'regex', 'expr': SENT + '=\\d+'}))),
            ('extract-bad-regex', 'an invalid regex', dict(items=one, extract_text=rules({'id': 'thr', 'file': LOG, 'kind': 'regex', 'expr': '(' + SENT + '=(\\d+'}))),
            ('extract-bad-pointer', 'a JSON Pointer without a leading slash', dict(items=one, extract_text=rules({'id': 'thr', 'file': M, 'kind': 'json', 'expr': 'rates/' + SENT}))),
            ('extract-bad-pointer-escape', 'a JSON Pointer with an invalid escape', dict(items=one, extract_text=rules({'id': 'thr', 'file': M, 'kind': 'json', 'expr': '/a~2' + SENT}))),
            ('extract-expr-not-string', 'a non-string expr', dict(items=one, extract_text=rules({'id': 'thr', 'file': M, 'kind': 'json', 'expr': 7}))),
            ('extract-missing-anchor-rule', 'no anchor rule although the anchor is set', dict(items=one, anchor=anchored)),
            ('extract-anchor-rule-without-anchor', 'an anchor rule without an anchor', dict(items=one, rules_extra=anchor_rule)),
            ('cli-missing-run', 'a missing --run', dict(items=one, argv=lambda c, e, o: [c, e, o, '--commit', '-'])),
            ('cli-missing-positional', 'a missing output directory argument', dict(items=one, argv=lambda c, e, o: [c, e, '--run', 'x', '--commit', '-'])),
        ]
        for name, what, spec in invalid:
            spec.setdefault('files', {M: METRICS, LOG: TEXT})
            invalid_checks(execute('invalid-' + name, **spec), what)
        # The anchor rule placed between input rules is out of order (inputs first, then the anchor).
        r = execute('invalid-extract-anchor-rule-first', one, anchor=anchored, files={M: METRICS},
                    extract_text=rules(anchor_rule[0], dict(r_('thr'), id='thr')))
        invalid_checks(r, 'the anchor rule before the input rules')
        # A failed write: control/ is not writable.
        if os.geteuid() == 0:
            print('note: running as root; the unwritable control/ case is skipped (not counted)')
        else:
            r = execute('invalid-unwritable-control', one, files={M: METRICS}, readonly_control=True)
            invalid_checks(r, 'a failed write')
    except Exception as error:  # noqa: BLE001
        global failures
        failures += 1
        import traceback
        print('FAIL test harness: %s' % ' '.join(traceback.format_exc().split('\n')))
    finally:
        for parent, dirs, _ in os.walk(SCRATCH):
            for directory in dirs:
                os.chmod(os.path.join(parent, directory), 0o755)
        shutil.rmtree(SCRATCH, ignore_errors=True)
    print('%d failure(s) (%d checks)' % (failures, checks) if failures else 'all %d checks passed' % checks)
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
