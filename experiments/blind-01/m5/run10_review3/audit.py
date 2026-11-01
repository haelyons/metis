"""Local file audit. No experiment imports or workload runs; bash is used only for syntax parsing."""
import ast
import contextlib
import csv
from datetime import datetime
import difflib
import hashlib
import io
import json
import math
from pathlib import Path
import re
import stat
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / 'run10_review3'
ORIG = ROOT / 'run9/agent/harness'
CAND = ROOT / 'run10_harness3'
REPRO = ROOT / 'run9/agent/results/reproduce/out'
PROFILE = ROOT / 'run9/agent/results/profile/out'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def unique(pairs):
    result = {}
    for key, value in pairs:
        assert key not in result, key
        result[key] = value
    return result

copies = []
for p in sorted(ORIG.iterdir()):
    q = CAND / p.name
    assert p.is_file() and q.is_file()
    a, b = p.stat(), q.stat()
    rec = dict(name=p.name, bytes=a.st_size, sha256=sha(p.read_bytes()),
               bytes_equal=p.read_bytes() == q.read_bytes(),
               mode_equal=stat.S_IMODE(a.st_mode) == stat.S_IMODE(b.st_mode),
               mtime_ns_equal=a.st_mtime_ns == b.st_mtime_ns)
    assert rec['bytes_equal'] and rec['mode_equal'] and rec['mtime_ns_equal']
    copies.append(rec)
o = (ORIG / 'run_command.sh').read_text()
u = (CAND / 'run_units.sh').read_text()
ol, ul = o.splitlines(True), u.splitlines(True)
assert ol[20:116] == ul[22:118]
assert ol[116:] == ul[148:]
diff = ''.join(difflib.unified_diff(ol, ul,
    fromfile='run9/agent/harness/run_command.sh', tofile='run10_harness3/run_units.sh'))
(DEST / 'run_units.diff').write_text(diff)
syntax = []
for name in ['setup.sh', 'run_anchors.sh', 'run_command.sh', 'run_evaluation.sh', 'run_units.sh']:
    result = subprocess.run(['bash', '-n', str(CAND / name)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    syntax.append(dict(name=name, rc=result.returncode, stderr=result.stderr))
blocks = []
for n, line in enumerate(ul):
    if line.rstrip().endswith("<<'PY'"):
        end = next(i for i in range(n + 1, len(ul)) if ul[i].strip() == 'PY')
        body = ''.join(ul[n + 1:end])
        ast.parse(body)
        blocks.append(dict(first_line=n+2, last_line=end, body=body))
assert len(blocks) == 3

text = (CAND / 'units.json').read_text()
manifest = json.loads(text, object_pairs_hook=unique)
assert set(manifest) == {'units'}
units = manifest['units']
assert len(units) >= 4
ids = [x['id'] for x in units]
assert len(set(ids)) == len(ids)
assert all(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:+=-]{0,127}', key) for key in ids)
raw = (REPRO / 'results/frodock_setup.csv').read_bytes()
rawlines = raw.splitlines(keepends=True)
rows = list(csv.DictReader(io.StringIO(raw.decode(), newline='')))
assert len(rawlines) == len(rows) + 1
assert all(set(row) == {'id','kind','receptor','ligand'} and all(row.values()) for row in rows)
assert ids == [row['id'] + ':' + row['kind'] for row in rows]
details_text = (REPRO / 'anchors_details.json').read_text()
details = json.loads(details_text, object_pairs_hook=unique)
assert ids == [j['id'] + ':' + j['kind'] for j in details['jobs']]
log = (REPRO / 'run_command/run_command.log').read_bytes().decode()
starts, ends = {}, {}
for n, line in enumerate(log.split('\n'), 1):
    m = re.search(r'^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3}) \|.*Running FroDock \(50 solutions\) on complex (\S+) (\S+) ', line)
    if m:
        starts[m[2]+':'+m[3]] = dict(line=n, timestamp=m[1])
    m = re.search(r'^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3}) \|.*Copying the results to \S*/frodock/([^/\s]+)/(\w+)_decoys', line)
    if m:
        ends[m[2]+':'+m[3]] = dict(line=n, timestamp=m[1])
assert list(starts) == ids and list(ends) == ids
def epoch(ts):
    return datetime.strptime(ts, '%Y-%m-%d %H:%M:%S,%f').timestamp()
records, files, total_bytes = [], [], 0
owned = set()
for i, (unit, row, job) in enumerate(zip(units, rows, details['jobs'])):
    assert set(unit) == {'id', 'outputs', 'cost_s'}
    cost = unit['cost_s']
    assert isinstance(cost, (int, float)) and not isinstance(cost, bool) and math.isfinite(cost) and cost > 0
    key = unit['id']
    elapsed = epoch(ends[key]['timestamp']) - epoch(starts[key]['timestamp'])
    assert cost == job['docking_wall_s'] == elapsed
    expected = [f"results/frodock/{row['id']}/{row['kind']}_decoys/model_{rank}.pdb" for rank in range(1,51)]
    assert unit['outputs'] == expected
    assert len(set(expected)) == len(expected) and not owned.intersection(expected)
    owned.update(expected)
    directory = REPRO / Path(expected[0]).parent
    assert {p.name for p in directory.iterdir()} == {Path(p).name for p in expected}
    for path in expected:
        assert all(re.fullmatch(r'[A-Za-z0-9._+=-]+', part) and part not in ('.','..') for part in path.split('/'))
        a, b = (REPRO/path).read_bytes(), (PROFILE/path).read_bytes()
        assert a == b, path
        total_bytes += len(a)
        files.append(dict(path=path, bytes=len(a), sha256=sha(a), profile_byte_equal=True))
    records.append(dict(index=i, id=key, csv_line=i+2, cost_s=cost,
        manifest_id_line=next(n for n,line in enumerate(text.split('\n'),1) if '"id": '+json.dumps(key) in line),
        manifest_cost_line=next(n for n,line in enumerate(text.split('\n'),1) if '"cost_s": '+str(cost) in line),
        details_cost_line=next(n for n,line in enumerate(details_text.split('\n'),1) if '"docking_wall_s": '+str(cost) in line),
        start=starts[key], end=ends[key], output_count=len(expected)))
assert {str(p.relative_to(REPRO)) for p in (REPRO/'results/frodock').rglob('*') if p.is_file()} == owned
assert (PROFILE/'results/frodock_setup.csv').read_bytes() == raw
ordered = sorted(range(len(units)), key=lambda i:(units[i]['cost_s'], i))
offset = (len(units)-4)//2
sample = ordered[offset:offset+4]

# Execute only detached standard-library CSV selector, against review-owned fixtures.
# Never execute validation, prediction, repair, scoring, or any shell script.
selector = compile(blocks[1]['body'], str(CAND/'run_units.sh')+':122-146', 'exec')
selection_checks = []
requests = [[key] for key in ids] + [ids, [ids[i] for i in sample], [ids[i] for i in reversed(sample)]]
with tempfile.TemporaryDirectory(prefix='csv-audit-', dir=DEST) as td:
    target = Path(td)/'frodock_setup.csv'
    def select(request):
        old = sys.argv
        try:
            sys.argv = ['-', str(target), *request]
            with contextlib.redirect_stdout(io.StringIO()):
                exec(selector, {'__name__':'__review_selector__'})
        finally:
            sys.argv = old
    for request in requests:
        target.write_bytes(raw)
        select(request)
        expected = rawlines[0] + b''.join(rawlines[ids.index(key)+1] for key in request)
        assert target.read_bytes() == expected
        selection_checks.append(dict(request=request, bytes_equal=True, bytes=len(expected), sha256=sha(expected)))
    for label, request in [('empty', []), ('duplicate',[ids[0],ids[0]]), ('unknown',['not-a-unit'])]:
        target.write_bytes(raw)
        try:
            select(request)
        except SystemExit as exc:
            assert exc.code
        else:
            raise AssertionError(label)
        assert target.read_bytes() == raw
        selection_checks.append(dict(rejected=label, input_unchanged=True))
sample_raw = rawlines[0] + b''.join(rawlines[i+1] for i in sample)
(DEST/'sample_frodock_setup.csv').write_bytes(sample_raw)

# Primary source: retained archives, hash-bound to reproduce setup record.
setup = json.loads((REPRO/'setup/setup_record.json').read_text())
cache = Path('/home/hal/.cache/blind01/intake_check_dl')
source_records = []
(DEST/'evidence').mkdir(exist_ok=True)
specs = [
    (cache/'codex/pinder_code.1.body', setup['pinder_archive_sha256'], 'pinder-'+setup['pinder_commit']+'/', {
        'src/pinder-methods/pinder/methods/main.py':'main.py.txt',
        'src/pinder-methods/pinder/methods/run/frodock/predict.py':'predict.py.txt',
        'src/pinder-eval/pinder/eval/dockq/method.py':'eval_method.py.txt',
        'src/pinder-eval/pinder/eval/run.py':'eval_run.py.txt',
        'src/pinder-core/pinder/core/index/utils.py':'core_index_utils.py.txt'}),
    (cache/'acquire/gcp_mirror_package.body', setup['frodock_archive_sha256'], 'frodock3_linux64/', {
        'src/frodockgrid/frodockgrid.cpp':'frodockgrid.cpp.txt',
        'src/libsas/sas.cpp':'sas.cpp.txt',
        'src/libsas/include/mersenne.h':'mersenne.h.txt',
        'src/frodockgrid/Release_MPI_GCC/objects.mk':'grid_MPI_GCC_objects.mk.txt',
        'src/frodockgrid/Release_MPI_GCC/subdir.mk':'grid_MPI_GCC_subdir.mk.txt'})]
for archive, expected_sha, prefix, members in specs:
    actual = sha(archive.read_bytes())
    assert actual == expected_sha
    member_records = []
    with tarfile.open(archive, 'r:gz') as tf:
        for member, filename in members.items():
            data = tf.extractfile(prefix+member).read()
            earlier = ROOT/'run10_inputs/evidence'/filename
            if earlier.is_file():
                assert data == earlier.read_bytes()
            (DEST/'evidence'/filename).write_bytes(data)
            member_records.append(dict(member=prefix+member, copy='evidence/'+filename, sha256=sha(data)))
    source_records.append(dict(archive=str(archive), sha256=actual, members=member_records))
# Corroborate source with run9's own saved source-bearing events; never run their commands.
workflow = ROOT/'run9/agent/wf/agents/0006-anchors-repair/codex-1.jsonl'
for n, line in enumerate(workflow.open(), 1):
    if n not in (103, 129):
        continue
    item = json.loads(line)['params']['item']
    assert item['status'] == 'completed' and item['exitCode'] == 0
    output = item['aggregatedOutput']
    (DEST/'evidence'/f'run9_source_event_{n}.txt').write_text(output)
    if n == 103:
        part = output.split('FILE src/pinder-methods/pinder/methods/run/frodock/predict.py\n',1)[1].split('\nFILE ',1)[0]
        assert part.rstrip() == (DEST/'evidence/predict.py.txt').read_text().rstrip()
    else:
        excerpt = (ROOT/'run10_review2/saved_core_utils_excerpt.py.txt').read_text()
        assert output.rstrip() == excerpt.rstrip()
assert (REPRO/'setup/pinder_frodock_fixes.applied.patch').read_bytes() == (ORIG/'pinder_frodock_fixes.patch').read_bytes()
assert (REPRO/'run_command/frodock_config.yaml').read_text() == 'n_solutions: 50\nmpi_np: 8\nforce: false\n'
result = dict(copies=copies, unchanged_ranges=[{'original':[21,116],'unit':[23,118]}, {'original':[117,185],'unit':[149,217]}],
    syntax=syntax, python_blocks=[{k:v for k,v in b.items() if k!='body'} for b in blocks],
    prepared_csv_sha256=sha(raw), records=records, files=files, output_count=len(files),
    full_run_identical_files=len(files), total_bytes_per_run=total_bytes, cost_sum_s=sum(x['cost_s'] for x in units),
    sample_indices=sample, sample_cost_sum_s=sum(units[i]['cost_s'] for i in sample),
    sample_csv_sha256=sha(sample_raw), selection_checks=selection_checks, primary_sources=source_records)
(DEST/'audit.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k in ['output_count','total_bytes_per_run','cost_sum_s','sample_indices','sample_cost_sum_s','sample_csv_sha256']}))
print('All static/file/CSV checks passed; no experiment workload executed.')
