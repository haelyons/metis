"""Print each workflow agent's context floor from a run's transcripts.

Usage: python3 -I tools/measure_floor.py <dir>     dir: ~/.claude/projects/<project>/<session>/subagents/workflows/<run>/
Per agent (agent-*.jsonl with its agent-*.meta.json): the label (the .meta.json description), the agentType, the first
API request's input tokens (the first message.usage in the .jsonl: input_tokens + cache_creation_input_tokens +
cache_read_input_tokens), and the tool count (the tools in the first api-request-shape record). This is the
restricted-role context floor. The Stage-1 thresholds, checked when the agentType or the label names the role:
qt-bare <= 12K tokens, qt-research <= 15K tokens.
"""
import glob
import json
import os
import sys

FLOOR = {'qt-bare': 12000, 'qt-research': 15000}


def first(path):
    tokens = tools = None
    with open(path, encoding='utf-8') as f:
        for line in f:
            try: r = json.loads(line)
            except ValueError: continue
            if tools is None and r.get('type') == 'api-request-shape':
                tools = len((r.get('shape') or {}).get('tools') or [])
            u = (r.get('message') or {}).get('usage')
            if tokens is None and u:
                tokens = u.get('input_tokens', 0) + u.get('cache_creation_input_tokens', 0) + u.get('cache_read_input_tokens', 0)
            if tokens is not None and tools is not None: break
    return tokens, tools


def main():
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]): sys.exit(__doc__)
    rows = []
    for meta_path in sorted(glob.glob(os.path.join(sys.argv[1], '*.meta.json'))):
        meta = json.load(open(meta_path, encoding='utf-8'))
        tokens, tools = first(meta_path[:-len('.meta.json')] + '.jsonl')
        label, kind = meta.get('description', '?'), meta.get('agentType', '?')
        role = kind if kind in FLOOR else next((r for r in FLOOR if r in label), None)
        check = '-' if role is None or tokens is None else ('ok' if tokens <= FLOOR[role] else 'OVER') + f' (<= {FLOOR[role] // 1000}K {role})'
        rows.append((label, kind, '?' if tokens is None else str(tokens), '?' if tools is None else str(tools), check))
    head = ('label', 'agentType', 'first_input_tokens', 'tools', 'floor')
    w = [max(len(r[i]) for r in rows + [head]) for i in range(len(head))]
    for r in [head] + sorted(rows): print('  '.join(c.ljust(w[i]) for i, c in enumerate(r)).rstrip())


if __name__ == '__main__':
    main()
