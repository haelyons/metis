"""Recover historical setup scripts from local workflow records; never execute them."""
import difflib
import hashlib
import json
from pathlib import Path
import re

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / 'run7_diag' / 'evidence'
OUT.mkdir(exist_ok=True)


def edits(folder):
    result = []
    source = BASE / 'run7/agent/wf/agents' / folder / 'codex-1.jsonl'
    for number, line in enumerate(source.read_text().splitlines(), 1):
        obj = json.loads(line)
        if obj.get('method') != 'item/completed':
            continue
        item = obj.get('params', {}).get('item', {})
        if item.get('type') == 'fileChange' and item.get('status') == 'completed':
            for change in item.get('changes', []):
                if change['path'].endswith('/harness/setup.sh'):
                    result.append((number, change['diff']))
    return source, result


def reverse_patch(content, patch):
    lines = content.splitlines(keepends=True)
    hunks = []
    for line in patch.splitlines(keepends=True):
        match = re.match(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
        if match:
            hunks.append((int(match[3]) - 1, [], []))
        elif hunks and line[:1] in (' ', '+', '-'):
            if line[0] in (' ', '+'):
                hunks[-1][1].append(line[1:])
            if line[0] in (' ', '-'):
                hunks[-1][2].append(line[1:])
    for start, new, old in reversed(hunks):
        assert lines[start:start + len(new)] == new, ('patch mismatch', start)
        lines[start:start + len(new)] = old
    return ''.join(lines)


final = (BASE / 'run7/agent/harness/setup.sh').read_text()
versions = {3: final}
provenance = []
for attempt, folder in [(3, '0004-harness-repair'), (2, '0003-harness-repair')]:
    source, changes = edits(folder)
    assert len(changes) == 1
    number, patch = changes[0]
    (OUT / f'repair-{attempt - 1}.recorded.diff').write_text(patch)
    versions[attempt - 1] = reverse_patch(versions[attempt], patch)
    provenance.append({'repair': attempt - 1, 'record': str(source.relative_to(BASE)),
                       'line': number, 'operation': 'reverse completed setup.sh fileChange'})

# Check complete pre-repair setup against the setup text printed in each repair record.
for attempt, folder in [(1, '0003-harness-repair'), (2, '0004-harness-repair')]:
    source = BASE / 'run7/agent/wf/agents' / folder / 'codex-1.jsonl'
    matches = []
    for number, line in enumerate(source.read_text().splitlines(), 1):
        obj = json.loads(line)
        if obj.get('method') != 'item/completed':
            continue
        item = obj.get('params', {}).get('item', {})
        output = item.get('aggregatedOutput') or ''
        if item.get('type') == 'commandExecution' and versions[attempt] in output:
            matches.append(number)
    assert matches, ('no exact historical setup snapshot', attempt)
    provenance.append({'attempt': attempt, 'record': str(source.relative_to(BASE)),
                       'lines': matches, 'exact_full_script_snapshot_match': True})

for attempt, content in versions.items():
    receipt = {1: '0004', 2: '0006', 3: '0008'}[attempt]
    target = OUT / f'setup-{receipt}.sh'
    target.write_text(content)
    provenance.append({'attempt': attempt, 'receipt': receipt + '-setup',
                       'script': str(target.relative_to(BASE)),
                       'sha256': hashlib.sha256(content.encode()).hexdigest(),
                       'python_start_line': content.splitlines().index("python3 - <<'PY'") + 2})

for repair in [1, 2]:
    diff = ''.join(difflib.unified_diff(versions[repair].splitlines(True),
                                     versions[repair + 1].splitlines(True),
                                     f'setup-attempt-{repair}.sh', f'setup-attempt-{repair + 1}.sh'))
    (OUT / f'repair-{repair}.diff').write_text(diff)

for folder, receipt in [('0003-harness-repair', '0004'), ('0004-harness-repair', '0006')]:
    prompt_path = BASE / 'run7/agent/wf/agents' / folder / 'prompt.md'
    prompt = prompt_path.read_bytes().decode()
    tail = prompt.split('Log tail (at most 200 lines):\n', 1)[1].rstrip()
    log = (BASE / 'run7/agent/results/reproduce' / f'{receipt}-setup.log').read_bytes().decode()
    assert tail == '\n'.join(log.rstrip().split('\n')[-200:])
    provenance.append({'repair': folder, 'prompt': str(prompt_path.relative_to(BASE)),
                       'tail_matches_latest_log_last_200_lines': True,
                       'tail_lines': len(tail.split('\n'))})

(OUT / 'provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
print(json.dumps(provenance, indent=2))
