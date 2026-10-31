"""Audit existing inputs and anonymous streaming refetches; mirror remains unverified_mirror."""
import base64
import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading

OUT = Path(__file__).resolve().parent
WORK = OUT.parent
CACHE = Path('/home/hal/.cache/blind01/intake_check_dl')
PIN = 'ebeb28a2f8411363cef722b7d293c978f7442672'
LOCK = threading.Lock()
STOP = threading.Event()

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')

def digest_file(path):
    sha, md5, size = hashlib.sha256(), hashlib.md5(), 0
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            sha.update(chunk)
            md5.update(chunk)
            size += len(chunk)
    return size, sha.hexdigest(), base64.b64encode(md5.digest()).decode()

def prepare():
    prior = json.loads((WORK / 'intake_check_codex/input_inventory.json').read_text())
    extra = json.loads((WORK / 'intake_check_codex/api_extra_inventory.json').read_text())
    evidence = {r['key']: r for r in json.loads((WORK / 'intake_acquire/per_file_evidence.json').read_text())}
    rows = []
    for r in prior + extra:
        rows.append(dict(input=r['key'], url='https://pinderdata.org/2024-02/' + r['key'],
                         local_path=r['body'], provenance='official_original_location',
                         coverage='250_case_inputs' if r in prior else '93_case_default_API_extras',
                         earlier_sha256=r['sha256'], earlier_bytes=r['bytes'],
                         published_md5=evidence[r['key']]['published_md5']))
    assert len(rows) == len({r['input'] for r in rows}) == 3590
    for name, label in [('index.parquet', 'pinder_index'), ('metadata.parquet', 'pinder_metadata'),
                        ('test_set_pdbs.zip', 'pinder_testzip')]:
        root = json.loads((WORK / 'intake_acquire/protein_verification.json').read_text())
        old = next(r for r in root['root_files'] if r['key'] == name)
        rows.append(dict(input=name, url='https://pinderdata.org/2024-02/' + name,
                         local_path=str(CACHE / 'acquire' / (label + '.body')),
                         provenance='official_original_location', earlier_sha256=old['sha256'],
                         earlier_bytes=old['bytes'], published_md5=old['published_md5']))
    for name in ['6IHB', '6JCQ', '6JCS']:
        rows.append(dict(input=name + '.cif', url=f'https://files.rcsb.org/download/{name}.cif',
                         local_path=str(CACHE / 'acquire' / (name + '.body')),
                         provenance='official_original_location'))
    rows.append(dict(input='frodock_distribution:unverified_mirror',
                     url='https://storage.googleapis.com/gke-dja-demo_static_assets/frodock3_linux64.tgz',
                     local_path=str(CACHE / 'acquire/gcp_mirror_package.body'),
                     provenance='unverified_mirror',
                     earlier_sha256='91b9aeff747346046c7f8c4c92fa5749c9f082d8122ee9d2d4769855d35368f4',
                     earlier_bytes=26637000))
    rows.append(dict(input='pinder_source@' + PIN,
                     url=f'https://codeload.github.com/pinder-org/pinder/tar.gz/{PIN}',
                     local_path=str(CACHE / 'codex/pinder_code.1.body'),
                     provenance='official_original_location',
                     earlier_sha256='b577532820ebbe5c16432b78c5e9c197690e863cb70a0a35a8ebcbe5277b76dd',
                     earlier_bytes=22835334))
    for name in ['root', 'pdbs', 'mappings', 'test_set_pdbs']:
        rows.append(dict(input=f'manifests/{name}.jsonl.gz',
                         url=f'https://pinderdata.org/2024-02/manifests/{name}.jsonl.gz',
                         local_path=str(CACHE / 'acquire' / ('manifest_' + name + '.body')),
                         provenance='official_original_location'))
    for row in rows:
        path = Path(row['local_path'])
        assert path.is_relative_to(CACHE) and path.resolve().is_relative_to(CACHE)
        row['local_checked_utc'] = now()
        row['bytes'], row['sha256'], row['local_md5_base64'] = digest_file(path)
        row['cache_mtime_ns'] = path.stat().st_mtime_ns
        assert row['sha256'] == row.get('earlier_sha256', row['sha256'])
        assert row['bytes'] == row.get('earlier_bytes', row['bytes'])
        assert row['local_md5_base64'] == row.get('published_md5', row['local_md5_base64'])
    write('local_checks.json', rows)
    print(f'Local hashes checked: {len(rows)} files, {sum(r["bytes"] for r in rows)} bytes.', flush=True)
    return rows

def fetch(row):
    if STOP.is_set():
        return dict(row, result='not_done_after_access_barrier')
    start = now()
    command = ['curl', '-q', '--fail', '--silent', '--show-error', '--location', '--globoff',
               '--max-redirs', '5', '--connect-timeout', '20', '--max-time', '180',
               '--proto', '=https', '--proto-redir', '=https',
               '--write-out', '%{stderr}\nCURL_META:%{json}\n', row['url']]
    # No cookie jar, netrc, credentials, login, or configuration file is used.
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    sha, md5, size = hashlib.sha256(), hashlib.md5(), 0
    for chunk in iter(lambda: proc.stdout.read(1024 * 1024), b''):
        sha.update(chunk)
        md5.update(chunk)
        size += len(chunk)
    err = proc.stderr.read().decode(errors='replace')
    code = proc.wait()
    prefix, marker, metadata = err.rpartition('CURL_META:')
    meta = json.loads(metadata) if marker else {}
    http = meta.get('http_code')
    if http in [401, 403, 429]:
        STOP.set()
    success = code == 0 and http == 200
    match = success and size == row['bytes'] and sha.hexdigest() == row['sha256']
    record = dict(row, started_utc=start, ended_utc=now(), curl_exit=code, http_status=http,
                  effective_url=meta.get('url_effective'), refetch_bytes=size,
                  refetch_sha256=sha.hexdigest() if success else '',
                  refetch_md5_base64=base64.b64encode(md5.digest()).decode() if success else '',
                  match=match, result='match' if match else 'mismatch' if success else 'unreachable',
                  error=prefix.strip(), stream_only=True, login_used=False)
    with LOCK:
        with (OUT / 'fetch_checks.jsonl').open('a') as stream:
            stream.write(json.dumps(record) + '\n')
    return record

def main():
    assert not (OUT / 'fetch_checks.jsonl').exists(), 'Preserve prior audit; do not overwrite.'
    rows = prepare()
    # Top-level inputs first, then case inputs. Eight ordinary concurrent GETs.
    rows = rows[3590:] + rows[:3590]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for record in pool.map(fetch, rows):
            results.append(record)
            if len(results) % 250 == 0 or record['result'] != 'match':
                print(f'{len(results)}/{len(rows)} completed; {record["result"]}', flush=True)
    write('refetch_results.json', results)
    print(json.dumps({'files': len(results), 'matches': sum(r.get('match', False) for r in results),
                      'failures': [r['input'] for r in results if not r.get('match')]}), flush=True)

if __name__ == '__main__':
    main()
