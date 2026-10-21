#!/usr/bin/env python3
"""Assemble replay phase-B args as small launches (the operator passes args inline, so each must stay well under 100 KB).

usage: python3 -I tools/prepare_phase_b.py replay/args_A.json replay/A.json replay/planted_cards.json replay/

Writes, into the output directory:
  args_B_1.json .. args_B_N.json   two records each, slimmed to what phase B reads (pick, plan, card, halted, beyond_prior);
                                   options_by_branch restricted to the picked options; old_scores empty; skip_branch_jobs;
                                   planted cards in slice 1 only
  args_B_branch.json               no records; skip_records; the branch-level jobs (option critic x3, dedup, overlap, pick runs)
"""
import json
import os
import sys

KEEP = ('pick', 'plan', 'card', 'halted', 'beyond_prior')
PER_SLICE = 2


def main(a_args, a_out, planted, out_dir):
    base = json.load(open(a_args, encoding='utf-8'))
    A = json.load(open(a_out, encoding='utf-8'))
    P = json.load(open(planted, encoding='utf-8'))
    if A.get('error'):
        sys.exit(f'phase A returned an error: {A["error"]}')
    cards = P['planted_cards'] if isinstance(P, dict) else P
    base.pop('agent_types', None)   # fresh session: the qt-* roles resolve
    base.update({'phase': 'B', 'price_sheet': A['price_sheet']})
    recs = [{k: r[k] for k in KEEP if k in r} for r in A['records']]
    slices = [recs[i:i + PER_SLICE] for i in range(0, len(recs), PER_SLICE)]
    for i, chunk in enumerate(slices, 1):
        keys = {r['pick'].get('key') or f"{r['pick']['root']}:{r['pick']['branch']}:{r['pick']['id']}" for r in chunk}
        obb = {bk: [o for o in opts if f'{bk}:{o["id"]}' in keys] for bk, opts in base['options_by_branch'].items()}
        obb = {bk: v for bk, v in obb.items() if v}
        args = dict(base, records=chunk, planted_cards=cards if i == 1 else [], skip_branch_jobs=True, slice=i,
                    options_by_branch=obb, old_scores={})
        p = os.path.join(out_dir, f'args_B_{i}.json')
        json.dump(args, open(p, 'w', encoding='utf-8'))
        print(f'{p}: {len(chunk)} records, {len(args["planted_cards"])} planted, {os.path.getsize(p):,} bytes')
    args = dict(base, records=[], planted_cards=[], skip_records=True)
    p = os.path.join(out_dir, 'args_B_branch.json')
    json.dump(args, open(p, 'w', encoding='utf-8'))
    print(f'{p}: branch-level run, {os.path.getsize(p):,} bytes')
    print(f'{len(slices)} slices + 1 branch run')


if __name__ == '__main__':
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    main(*sys.argv[1:])
