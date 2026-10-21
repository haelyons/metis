#!/usr/bin/env python3
"""Contamination check for a blind run: grep every agent transcript and the journal of a workflow run for terms
that would show an agent saw material it must not have seen. Prints one line per hit (agent label, term, context)
and a summary; exit 1 on any hit.

usage: python3 -I tools/contamination_grep.py <workflow transcript dir> [extra term ...]

The term list is deliberately kept out of the pipeline's own files; pass extra terms on the command line.
Default terms cover the design notes' location and the public pages the project denies to agents.
"""
import glob
import json
import os
import re
import sys

DEFAULT_TERMS = [
    r'sotaletters', r'luma\.com', r'\blu\.ma\b', r'hackathon', r'scratchpad/meta', r'harry-delta', r'harry\.md',
]


def label_of(meta_path):
    try:
        return json.load(open(meta_path, encoding='utf-8')).get('description', '?')
    except Exception:
        return '?'


def main(run_dir, extra):
    terms = [re.compile(t, re.I) for t in DEFAULT_TERMS + extra]
    hits = 0
    files = sorted(glob.glob(os.path.join(run_dir, 'agent-*.jsonl'))) + [os.path.join(run_dir, 'journal.jsonl')]
    for f in files:
        if not os.path.exists(f):
            continue
        label = label_of(f.replace('.jsonl', '.meta.json')) if 'agent-' in f else 'journal'
        for line in open(f, encoding='utf-8', errors='replace'):
            for t in terms:
                for m in t.finditer(line):
                    hits += 1
                    s = max(0, m.start() - 60)
                    print(f'{label}\t{t.pattern}\t...{line[s:m.end() + 60].strip()}...')
    print(f'{hits} hit(s) across {len(files)} files')
    return 1 if hits else 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2:]))
