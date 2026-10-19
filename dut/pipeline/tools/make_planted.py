"""Build the planted-card set for replay phase B from a phase-A output.

Usage: python3 -I tools/make_planted.py A.json [out.json]     (default out: replay/planted_cards.json in the repo)
  A.json  the return value of dist/replay_v2.js phase A (records[] with pick, plan, card), saved verbatim
Writes {"planted_cards": [{id, card_text, sources: [{id, url, quote}], expected, defect}]}, the form replay.js phase B
reads, from the records of R3 physical W11, R2 physical W13 and R1 interp I1:
  a_quote_W11   one source quote altered so it is not on the page          expected REJECT
  b_number_W13  a number in a core sentence changed against its source     expected REJECT
  c_url_I1      one core source URL broken (its host made unresolvable)     expected REJECT (UNREACHABLE)
  d_clean_W11   the card as rendered                                        expected PASS
card_text is the rendered card body before its Judges (or Halted) line, without the HTML anchor. sources are the plan's
sources the body cites as [id], plus the anchor's and the closest prior's source. A number is changed by multiplying
it by 3, keeping its decimals and commas. Deterministic: the same A.json gives the same file. Prints what it changed.
"""
import json
import os
import re
import sys
from urllib.parse import urlsplit, urlunsplit

PICKS = {'W11': ('R3', 'physical', 'W11'), 'W13': ('R2', 'physical', 'W13'), 'I1': ('R1', 'interp', 'I1')}
# core card fields (gates.js gate_CORE), in the order a changed number is looked for
CORE = ['anchor.what', 'novelty.closest_prior', 'question', 'hypothesis', 'predictions.if_lever', 'predictions.if_not', 'test_summary']
NUM = re.compile(r'(?<![\w.])\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\w])|(?<![\w.,])\d+(?:\.\d+)?(?![\w,])')


def get(d, path):
    for k in path.split('.'):
        if not isinstance(d, dict): return None
        d = d.get(k)
    return d


def value(tok):
    return float(tok.replace(',', ''))


def bump(tok):
    v = value(tok) * 3
    if '.' in tok:
        out = f"{v:.{len(tok.split('.')[1])}f}"
    else:
        out = f'{int(round(v)):,}' if ',' in tok else str(int(round(v)))
    return out


def body(card):
    text = re.split(r'\n\n\*\*(?:Judges|Halted at)', card)[0]
    return re.sub(r'<a id="[^"]*"></a>', '', text)


def card_sources(plan, text):
    by_id = {s['id']: s for s in plan.get('sources') or []}
    ids = [i.strip() for m in re.findall(r'\[([^\[\]]+)\]', text) for i in re.split(r'[,;]', m)]
    ids += [get(plan, 'anchor.source_id'), get(plan, 'novelty.closest_source_id')]
    seen, out = set(), []
    for i in ids:
        if i in by_id and i not in seen:
            seen.add(i)
            out.append({'id': i, 'url': by_id[i]['url'], 'quote': by_id[i]['quote']})
    return out


def base(rec, tag):
    if not rec or not rec.get('plan') or not rec.get('card'):
        sys.exit(f'{tag}: the phase-A record has no plan or no card; cannot plant on it')
    text = body(rec['card'])
    return text, card_sources(rec['plan'], text)


def main():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    A = json.load(open(sys.argv[1], encoding='utf-8'))
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, 'replay', 'planted_cards.json')
    recs = {}
    for r in A['records']:
        p = r.get('pick') or {}
        for name, (root, br, oid) in PICKS.items():
            if (p.get('root'), p.get('branch'), p.get('id')) == (root, br, oid): recs[name] = r
    cards = []

    # (a) W11: the first cited source whose quote holds a number gets that number changed; else "not" is inserted
    text, srcs = base(recs.get('W11'), 'W11')
    if not srcs: sys.exit('W11: the card cites no source')
    s = next((x for x in srcs if NUM.search(x['quote'])), srcs[0])
    m = NUM.search(s['quote'])
    if m:
        new = s['quote'][:m.start()] + bump(m.group()) + s['quote'][m.end():]
    else:
        new = re.sub(r'\b(is|are|was|were)\b', r'\1 not', s['quote'], count=1)
        if new == s['quote']: new = 'It is not the case that ' + s['quote']
    print(f"a_quote_W11: source {s['id']} quote {s['quote']!r} -> {new!r}")
    altered = [dict(x, quote=new) if x is s else x for x in srcs]
    cards.append({'id': 'a_quote_W11', 'card_text': text, 'sources': altered, 'expected': 'REJECT',
                  'defect': f"source {s['id']}: quote altered so it is not on the page ({m.group() + ' -> ' + bump(m.group()) if m else 'negated'})"})

    # (b) W13: the first number in a core field that a cited quote also states is multiplied by 3 in the card body
    text, srcs = base(recs.get('W13'), 'W13')
    plan = recs['W13']['plan']
    quoted = {value(t) for x in srcs for t in NUM.findall(x['quote'])}
    pick = None
    for f in CORE:
        seg = str(get(plan, f) or '')
        if not seg or seg not in text: continue
        for m in NUM.finditer(seg):
            if pick is None: pick = (f, seg, m, False)   # fallback: the first core number, even if no quote states it
            if value(m.group()) in quoted: pick = (f, seg, m, True); break
        if pick and pick[3]: break
    if not pick: sys.exit('W13: no number in a core card field')
    f, seg, m, sourced = pick
    new_seg = seg[:m.start()] + bump(m.group()) + seg[m.end():]
    text_b = text.replace(seg, new_seg, 1)
    print(f"b_number_W13: {f}: {m.group()} -> {bump(m.group())}{'' if sourced else ' (WARNING: no cited quote states this number)'}")
    cards.append({'id': 'b_number_W13', 'card_text': text_b, 'sources': srcs, 'expected': 'REJECT',
                  'defect': f'{f}: {m.group()} changed to {bump(m.group())}, against its source'})

    # (c) I1: the anchor's source if the card cites it, else the first cited source, gets an unresolvable host
    text, srcs = base(recs.get('I1'), 'I1')
    if not srcs: sys.exit('I1: the card cites no source')
    aid = get(recs['I1']['plan'], 'anchor.source_id')
    s = next((x for x in srcs if x['id'] == aid), srcs[0])
    u = urlsplit(s['url'])
    broken = urlunsplit((u.scheme or 'https', (u.hostname or 'example.org') + '.invalid', u.path, u.query, u.fragment))
    print(f"c_url_I1: source {s['id']} url {s['url']} -> {broken}")
    cards.append({'id': 'c_url_I1', 'card_text': text, 'sources': [dict(x, url=broken) if x is s else x for x in srcs], 'expected': 'REJECT',
                  'defect': f"source {s['id']}: URL host made unresolvable (UNREACHABLE)"})

    # (d) W11 clean
    text, srcs = base(recs.get('W11'), 'W11')
    print(f'd_clean_W11: unchanged ({len(srcs)} sources)')
    cards.append({'id': 'd_clean_W11', 'card_text': text, 'sources': srcs, 'expected': 'PASS', 'defect': 'none'})

    with open(out_path, 'w', encoding='utf-8') as fh:
        json.dump({'planted_cards': cards}, fh, indent=1, ensure_ascii=False)
        fh.write('\n')
    print(f'wrote {out_path} ({len(cards)} cards)')


if __name__ == '__main__':
    main()
