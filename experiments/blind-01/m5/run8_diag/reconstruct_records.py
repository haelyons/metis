"""Inspect saved records and reconstruct scripts without executing their code."""
import ast
import collections
import csv
import hashlib
import json
from pathlib import Path
import re
import shlex
import struct
import tarfile

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / 'run8_diag/evidence'
OUT.mkdir(parents=True, exist_ok=True)
AGENTS = BASE / 'run8/agent/wf/agents'


def item(folder, line):
    record = AGENTS / folder / 'codex-1.jsonl'
    return json.loads(record.read_text().splitlines()[line - 1])['params']['item']


def shell(folder, line):
    command = shlex.split(item(folder, line)['command'])
    assert command[:2] == ['/bin/bash', '-lc'] and len(command) == 3
    return command[2]


def heredoc(text, start, end):
    return text.split(start + '\n', 1)[1].split('\n' + end, 1)[0] + '\n'


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
        assert lines[start:start + len(new)] == new
        lines[start:start + len(new)] = old
    return ''.join(lines)


# First repair's read prints the full pre-repair scripts, in this exact order.
snapshot = item('0005-anchors-repair', 37)['aggregatedOutput']
parts = snapshot.split('#!/usr/bin/env bash\n')
assert len(parts) == 5
initial_command, initial_anchors = ['#!/usr/bin/env bash\n' + p for p in parts[1:3]]
initial_setup = '#!/usr/bin/env bash\n' + parts[4]
assert initial_setup == (BASE / 'run8/agent/harness/setup.sh').read_text()

# Independently reconstruct original harness creation using literals only.
creation = shell('0002-harness', 250)
created_command = heredoc(creation, "cat > harness/run_command.sh <<'BASH'", 'BASH')
created_command = created_command.replace('export PINDER_BASE_DIR="$PWD/data"',
                                          'export PINDER_BASE_DIR=data')
created_command = created_command.replace('export PINDER_RELEASE=2024-02\n',
    'export PINDER_RELEASE=2024-02\nexport PINDER_DATA_DIR=data/2024-02\n')
assert created_command == initial_command
generator = heredoc(creation, "python3 - <<'GENERATOR'", 'GENERATOR')
tree = ast.parse(generator)
assignment = next(n for n in tree.body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == 'script' for t in n.targets))
literal = ast.literal_eval(assignment.value.func.value)
ids = [a['id'] for a in json.loads((BASE / 'run8/agent/intake/anchors.json').read_text())]
assert literal.replace('IDS', repr(ids)) == initial_anchors
baseline = heredoc(initial_setup, "cat > baseline-published/run_baseline.py <<'PY'", 'PY')

final_command = (BASE / 'run8/agent/harness/run_command.sh').read_text()
final_anchors = (BASE / 'run8/agent/harness/run_anchors.sh').read_text()
changes = item('0006-anchors-repair', 116)['changes']
assert len(changes) == 1 and changes[0]['path'].endswith('/harness/run_anchors.sh')
patch = changes[0]['diff']
second_anchors = reverse_patch(final_anchors, patch)
assert heredoc(shell('0005-anchors-repair', 110),
               "cat > harness/run_command.sh <<'SH'", 'SH') == final_command
created_anchors = heredoc(shell('0005-anchors-repair', 116),
                          "cat > harness/run_anchors.sh <<'SH'", 'SH')
created_anchors = created_anchors.replace(
    'start=$(wc -c < out/baseline.log 2>/dev/null || echo 0)',
    'start=0\nif [[ -f out/baseline.log ]]; then start=$(wc -c < out/baseline.log); fi'
).replace('import os\n', '')
assert created_anchors == second_anchors
second_snapshot = item('0006-anchors-repair', 47)['aggregatedOutput']
assert final_command + second_anchors in second_snapshot

provenance = {
    'attempt1': {'snapshot': '0005-anchors-repair/codex-1.jsonl:37',
                 'creation': '0002-harness/codex-1.jsonl:250',
                 'data_directory_addition': '0002-harness/codex-1.jsonl:277',
                 'environment_edit': '0002-harness/codex-1.jsonl:380',
                 'creation_matches_snapshot': True},
    'attempt2': {'command_creation': '0005-anchors-repair/codex-1.jsonl:110',
                 'anchors_creation': '0005-anchors-repair/codex-1.jsonl:116',
                 'anchors_edit': '0005-anchors-repair/codex-1.jsonl:122',
                 'snapshot': '0006-anchors-repair/codex-1.jsonl:47',
                 'creation_and_reversed_patch_match_snapshot': True},
    'attempt3': {'anchors_edit': '0006-anchors-repair/codex-1.jsonl:116',
                 'command_unchanged': True},
}
scripts = {}
for receipt, command, anchors in [('0054', initial_command, initial_anchors),
                                   ('0056', final_command, second_anchors),
                                   ('0058', final_command, final_anchors)]:
    for name, content in [('run_command.sh', command), ('run_anchors.sh', anchors)]:
        filename = f'{receipt}-{name}'
        (OUT / filename).write_text(content)
        scripts[filename] = hashlib.sha256(content.encode()).hexdigest()
(OUT / '0054-run_baseline.py').write_text(baseline)
(OUT / 'repair2.recorded.diff').write_text(patch)

logs = {}
for receipt in ('0054', '0056', '0058'):
    path = BASE / f'run8/agent/results/reproduce/{receipt}-anchors.log'
    lines = path.read_bytes().decode().split('\n')
    cases = [{'line': i, **json.loads(s[len('CASE_WALL '):])}
             for i, s in enumerate(lines, 1) if s.startswith('CASE_WALL ')]
    logs[receipt] = {'case_count': len(cases), 'cases': cases,
                     'case_wall_sum_s': sum(c['wall_s'] for c in cases),
                     'measurement_lines': sum(s.startswith('MEASUREMENT ') for s in lines)}
for folder, receipt in [('0005-anchors-repair', '0054'), ('0006-anchors-repair', '0056')]:
    prompt = (AGENTS / folder / 'prompt.md').read_bytes().decode()
    tail = prompt.split('Log tail (at most 200 lines):\n', 1)[1].rstrip()
    log = (BASE / f'run8/agent/results/reproduce/{receipt}-anchors.log').read_bytes().decode()
    assert tail == '\n'.join(log.rstrip().split('\n')[-200:])
    logs[receipt]['repair_tail_exact_match'] = True
    logs[receipt]['repair_tail_lines'] = len(tail.split('\n'))

groups = collections.defaultdict(lambda: {'bytes': 0, 'files': 0})
extensions = collections.defaultdict(lambda: {'bytes': 0, 'files': 0})
root = BASE / 'run8/agent/results/reproduce/out'
for path in root.rglob('*'):
    if not path.is_file():
        continue
    size = path.stat().st_size
    for group in (groups[path.relative_to(root).parts[0]], extensions[path.suffix]):
        group['bytes'] += size
        group['files'] += 1
output = {'bytes': sum(g['bytes'] for g in groups.values()),
          'files': sum(g['files'] for g in groups.values()),
          'by_top_level': dict(groups), 'by_extension': dict(extensions),
          'anchors_measured_exists': (root / 'anchors_measured.json').exists(),
          'anchors_scored_exists': (root.parent / 'anchors_scored.json').exists()}

brief_match = ((BASE / 'run8/agent/intake/brief.md').read_bytes()
               == (BASE / 'intake_mirror/BRIEF_run5.md').read_bytes())
with (BASE / 'intake_mirror/HASHES.tsv').open(newline='') as stream:
    rows = list(csv.DictReader(stream, delimiter='\t'))
data = json.loads((BASE / 'run8/agent/intake/data.json').read_text())
pins = data['pins_and_hashes']
inventory = {(p['url'], p['sha256']) for p in pins}
hashes = {(p['url'], p['sha256']) for p in rows}
materials = {'intake_brief_equals_named_brief': brief_match,
             'hash_rows': len(rows), 'intake_pin_count': len(pins),
             'url_hash_sets_equal': inventory == hashes,
             'all_recorded_refetch_matches': all(p['match'] == 'true' for p in rows)}
assert brief_match and inventory == hashes

# Inspect cached archive as data only; no extraction or binary execution.
mirror = next(p for p in rows if p['input'] == 'frodock_distribution:unverified_mirror')
archive = Path(mirror['local_path'])
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
assert digest == mirror['sha256']
with tarfile.open(archive) as tar:
    member = 'frodock3_linux64/src/frodockgrid/frodockgrid.cpp'
    native_source = tar.extractfile(member).read().decode()
    soap_digest = hashlib.sha256(tar.extractfile('frodock3_linux64/bin/soap.bin').read()).hexdigest()
    excerpt = '\n'.join(f'{i}: {s}' for i, s in enumerate(native_source.splitlines(), 1)
                        if 250 <= i <= 322) + '\n'
    (OUT / 'native-grid-exit-excerpt.txt').write_text(excerpt)
materials.update({'cached_mirror_sha256': digest, 'cached_mirror_matches_inventory': True,
                  'grid_source_member': member, 'soap_sha256': soap_digest,
                  'grid_exit_excerpt': 'native-grid-exit-excerpt.txt'})
map_path = root / 'run-1793485237586031601/scratch/1a19__A1_P11540--1a19__B1_P11540/receptor_W.mrc'
with map_path.open('rb') as stream:
    header = stream.read(1024)
nx, ny, nz, mode = struct.unpack_from('<4i', header)
nsymbt = struct.unpack_from('<i', header, 92)[0]
expected = 1024 + nsymbt + nx * ny * nz * {0: 1, 1: 2, 2: 4, 6: 2}[mode]
assert len(header) == 1024 and map_path.stat().st_size == expected
materials['attempt1_grid_map'] = {'dimensions': [nx, ny, nz], 'mode': mode,
    'bytes': map_path.stat().st_size, 'expected_bytes': expected,
    'complete_header_and_payload': True}

checks = {'provenance': provenance, 'script_sha256': scripts,
          'logs': logs, 'output': output, 'materials': materials}
(OUT / 'checks.json').write_text(json.dumps(checks, indent=2) + '\n')
print(json.dumps({'scripts_reconstructed': len(scripts), 'logs': logs,
                  'output_bytes': output['bytes'], 'output_files': output['files'],
                  'materials': materials}, indent=2))
