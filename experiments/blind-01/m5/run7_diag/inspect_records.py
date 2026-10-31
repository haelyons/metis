"""Summarize saved records and cached archive metadata without extraction or execution."""
import collections
import csv
import hashlib
import json
from pathlib import Path
import tarfile

base = Path(__file__).resolve().parent.parent
out = base / 'run7_diag/evidence'
rows = list(csv.DictReader((base / 'intake_mirror/HASHES.tsv').open(), delimiter='\t'))
data = json.loads((base / 'run7/agent/intake/data.json').read_text())
by_url = {x['url']: x for x in rows}
assert len(rows) == len(data['inventory']) == 3602
assert all(by_url[x['url']]['sha256'] == x['sha256'] for x in data['inventory'])
assert all(x['match'] == 'true' and x['sha256'] == x['refetch_sha256'] for x in rows)
summary = {
    'intake_brief_equals_named_brief': (base / 'intake_mirror/BRIEF_run5.md').read_bytes() == (base / 'run7/agent/intake/brief.md').read_bytes(),
    'inventory_rows': len(rows),
    'intake_inventory_hashes_equal_HASHES_tsv': True,
    'HASHES_tsv_records_all_historical_refetch_matches': True,
    'release_files_selected_by_setup': sum(x['url'].startswith('https://pinderdata.org/2024-02/') and not x['name'].endswith('.zip') for x in data['inventory']),
    'receipts': {},
    'local_archive_hashes': {},
}
for name in ['0003-upload', '0004-setup', '0005-upload', '0006-setup', '0007-upload', '0008-setup']:
    summary['receipts'][name] = json.loads((base / 'run7/control/receipts' / (name + '.json')).read_text())
for name in ['frodock.tar.gz', 'pinder-source.tar.gz']:
    p = base / 'run7/agent/harness' / name
    summary['local_archive_hashes'][name] = hashlib.sha256(p.read_bytes()).hexdigest()
with tarfile.open(base / 'run7/agent/harness/frodock.tar.gz') as archive:
    members = archive.getmembers()
    summary['frodock_archive'] = {
        'members': len(members),
        'types': dict(collections.Counter(m.type.decode() for m in members)),
        'links': [{'name': m.name, 'target': m.linkname} for m in members if m.issym() or m.islnk()],
    }
    soap = archive.getmember('frodock3_linux64/bin/soap.bin')
    summary['frodock_archive']['soap'] = {'bytes': soap.size, 'sha256': hashlib.sha256(archive.extractfile(soap).read()).hexdigest()}
(out / 'record-checks.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({k: v for k, v in summary.items() if k != 'receipts'}, indent=2))
