"""Build replay/args_A.json for the Stage-2 replay workflow (dist/replay_v2.js, phase A).

The workflow script cannot read files, so every stored input it needs is gathered here:
  picks             the last run's 20 picks, from table.md (write-up path column gives the dir;
                    producer.md sits beside writeup.md under runs-v3/seed-1)
  options_by_branch each branch's stored options {id, title, summary}, from flow-work/results.json
                    (each agent's returned JSON keyed by label; built by flow-work/extract_opts.py)
  old_scores        each branch's stored option-critic items, from cutoffs-work/oc.json
  roots             the five root questions: R1 is the run script's EX2_TEXT; R2, R3 from PLAYWRIGHT;
                    R4, R5 from GUEST (results.json)
  given             the budget semantics fixed by the human on 2026-10-16

Run: python3 -I tools/prepare_replay_args.py [out_path]   (default: replay/args_A.json beside tools/)
Inputs are opened read-only. Exits non-zero if any count or cross-check fails.
"""
import json
import os
import re
import sys

SCRATCH = '/tmp/claude-1000/-home-hal-stage/01679595-7e0a-4a87-9dfe-92f32b9672f2/scratchpad'
TABLE = f'{SCRATCH}/table.md'
RESULTS = f'{SCRATCH}/meta/flow-work/results.json'
OC = f'{SCRATCH}/meta/cutoffs-work/oc.json'
RUN_SCRIPT = '/home/hal/.claude/projects/-home-hal-stage/01679595-7e0a-4a87-9dfe-92f32b9672f2/workflows/scripts/question-tree-wf_670c1d45-049.js'
RUN_DIR = '/home/hal/stage/runs-v3/seed-1/'
ROOTS = ['R1', 'R2', 'R3', 'R4', 'R5']
BRANCHES = ['physical', 'interp']
GIVEN = {'budget_usd': 1000, 'budget_covers_storage': True, 'budget_covers_tax': False}


def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def table_rows():
    rows = []
    with open(TABLE, encoding='utf-8') as f:
        for line in f:
            if not line.startswith('| R'):
                continue
            cells = [c.strip() for c in re.split(r'(?<!\\)\|', line.strip())[1:-1]]
            rows.append(cells)
    return rows


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'replay', 'args_A.json')
    results, oc = load(RESULTS), load(OC)

    # branch labels in the run: R1:widener (all five framers said NOT COMPUTE-BOUND) and R1:interp
    options_by_branch, old_scores = {}, {}
    for r in ROOTS:
        for b, label in (('physical', f'{r}:widener'), ('interp', f'{r}:interp')):
            items = results[label]['result']['items']
            options_by_branch[f'{r}:{b}'] = [{'id': o['id'], 'title': o['title'], 'summary': o['summary']} for o in items]
            old_scores[f'{r}:{b}'] = oc[f'{r}:{b}:option-critic']
            ids = [o['id'] for o in items]
            assert len(ids) == len(set(ids)), f'{r}:{b}: duplicate option ids'
            assert sorted(ids) == sorted(s['id'] for s in old_scores[f'{r}:{b}']), f'{r}:{b}: scored ids differ from option ids'

    with open(RUN_SCRIPT, encoding='utf-8') as f:
        ex2 = re.search(r'const EX2_TEXT = `([^`]*)`', f.read()).group(1)
    pw, gu = results['playwright']['result']['items'], results['guest']['result']['items']
    roots = [{'id': 'R1', 'source': 'EX2', 'question': ex2},
             {'id': 'R2', 'source': 'PLAYWRIGHT', 'question': pw[0]['question']},
             {'id': 'R3', 'source': 'PLAYWRIGHT', 'question': pw[1]['question']},
             {'id': 'R4', 'source': 'GUEST', 'question': gu[0]['question']},
             {'id': 'R5', 'source': 'GUEST', 'question': gu[1]['question']}]

    picks = []
    for cells in table_rows():
        root, branch, pick_cell, path = cells[0], cells[2].split()[0], cells[3], cells[7]
        m = re.match(r'(top|random): (\S+) (.*) \(total ([\d.]+)\)$', pick_cell)
        kind, pid, title = m.group(1), m.group(2), m.group(3)
        opt = next(o for o in options_by_branch[f'{root}:{branch}'] if o['id'] == pid)
        assert opt['title'] == title, f'{root}:{branch}:{pid}: table title differs from stored title'
        d = os.path.dirname(path)
        assert d.startswith(RUN_DIR), path
        picks.append({'root': root, 'branch': branch, 'kind': kind, 'id': pid, 'title': title,
                      'producer_path': f'{d}/producer.md', 'dir': d})

    assert len(picks) == 20, len(picks)
    assert all(os.path.isfile(p['producer_path']) for p in picks), [p['producer_path'] for p in picks if not os.path.isfile(p['producer_path'])]
    assert len({(p['root'], p['branch'], p['id']) for p in picks}) == 20
    assert len(options_by_branch) == 10 and all(options_by_branch.values()) and all(old_scores.values())
    assert len(roots) == 5 and all(r['question'] for r in roots)

    args = {'phase': 'A', 'seed': 1, 'given': GIVEN, 'picks': picks, 'options_by_branch': options_by_branch,
            'roots': roots, 'old_scores': old_scores}
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(args, f, indent=1, ensure_ascii=False)
        f.write('\n')
    n_opts = sum(len(v) for v in options_by_branch.values())
    print(f'wrote {out}: {len(picks)} picks, {len(options_by_branch)} branches ({n_opts} options), {len(roots)} roots')


if __name__ == '__main__':
    main()
