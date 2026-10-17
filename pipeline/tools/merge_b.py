#!/usr/bin/env python3
"""Merge the six phase-B outputs into one B.json of the single-run shape the scorer expects.

usage: python3 -I tools/merge_b.py replay/B_1.json ... replay/B_5.json replay/B_branch.json replay/B.json
"""
import json
import sys


def main(paths, out):
    slices, branch = [], None
    for p in paths:
        d = json.load(open(p, encoding='utf-8'))
        if d.get('error'):
            sys.exit(f'{p} is an error object: {d["error"]}')
        (slices if d.get('slice') is not None else [branch := d]) if False else None
        if d.get('slice') is not None:
            slices.append(d)
        else:
            branch = d
    if branch is None:
        sys.exit('no branch-level output among the inputs')
    slices.sort(key=lambda d: d['slice'])
    merged = dict(branch)
    merged['dramaturg'] = [x for d in slices for x in (d.get('dramaturg') or [])]
    merged['critic'] = [x for d in slices for x in (d.get('critic') or [])]
    merged['planted'] = [x for d in slices for x in (d.get('planted') or [])]
    merged['log'] = [l for d in slices for l in (d.get('log') or [])] + (branch.get('log') or [])
    merged.pop('slice', None)
    json.dump(merged, open(out, 'w', encoding='utf-8'))
    print(f'wrote {out}: {len(merged["dramaturg"])} dramaturg, {len(merged["critic"])} critic, '
          f'{len(merged["planted"])} planted, {len(merged.get("option_critic") or {})} branches scored')


if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    main(sys.argv[1:-1], sys.argv[-1])
