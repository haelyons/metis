"""Inspect acquired materials without installing or executing benchmark software."""
import base64
import datetime
import gzip
import hashlib
import json
import pathlib
import tarfile
import zipfile

import gemmi
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent
WORK = ROOT.parent
CACHE = pathlib.Path('/home/hal/.cache/blind01/intake_check_dl/acquire')


def digest(data, algorithm='sha256'):
    return hashlib.new(algorithm, data).hexdigest()


def write(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2) + '\n')


now = datetime.datetime.now(datetime.timezone.utc).isoformat()
prior = json.loads((WORK / 'intake_check_codex/input_inventory.json').read_text())
extra = json.loads((WORK / 'intake_check_codex/api_extra_inventory.json').read_text())
requested = {row['key']: row for row in prior + extra}
published = {}
manifest_counts = {}
for directory in ['root', 'pdbs', 'mappings', 'test_set_pdbs']:
    count = 0
    with gzip.open(CACHE / ('manifest_' + directory + '.body'), 'rt') as stream:
        for line in stream:
            row = json.loads(line)
            count += 1
            if directory == 'root' or row['key'] in requested:
                published[row['key']] = row
    manifest_counts[directory] = count
    print('Manifest checked:', directory, count, flush=True)

file_checks = []
for key, row in sorted(requested.items()):
    # Paths come only from the explicitly authorized earlier reader inventory.
    body = pathlib.Path(row['body'])
    assert body.is_relative_to('/home/hal/.cache/blind01/intake_check_dl/codex')
    data = body.read_bytes()
    pub = published.get(key, {})
    actual_md5 = base64.b64encode(hashlib.md5(data).digest()).decode()
    check = dict(key=key, url='https://pinderdata.org/2024-02/' + key,
                 bytes=len(data), sha256=digest(data), published_md5=pub.get('md5'),
                 size_match=len(data) == pub.get('size'),
                 published_md5_match=actual_md5 == pub.get('md5'),
                 earlier_sha256_match=digest(data) == row['sha256'],
                 earlier_validation=row.get('validation', row.get('parsed_nonempty')),
                 network_retrieval='Earlier authorized reader; see ../intake_check_codex/fetch_attempts.jsonl',
                 verification_utc=now)
    file_checks.append(check)
failures = [row for row in file_checks if not all(row[x] for x in
            ['size_match', 'published_md5_match', 'earlier_sha256_match'])]
write('per_file_evidence.json', file_checks)

root_checks = []
for label, key in [('pinder_index', 'index.parquet'), ('pinder_metadata', 'metadata.parquet'),
                   ('pinder_testzip', 'test_set_pdbs.zip')]:
    data = (CACHE / (label + '.body')).read_bytes()
    pub = published[key]
    root_checks.append(dict(key=key, bytes=len(data), sha256=digest(data),
        published_md5=pub['md5'], size_match=len(data) == pub['size'],
        md5_match=base64.b64encode(hashlib.md5(data).digest()).decode() == pub['md5']))

index = pd.read_parquet(CACHE / 'pinder_index.body')
subset = index[index.pinder_s]
paired = subset[subset.apo_R & subset.apo_L]
metadata = pd.read_parquet(CACHE / 'pinder_metadata.body', columns=['id'])
zip_file = zipfile.ZipFile(CACHE / 'pinder_testzip.body')
zip_info = dict(entries=len(zip_file.infolist()),
                regular_files=sum(not x.is_dir() for x in zip_file.infolist()),
                uncompressed_bytes=sum(x.file_size for x in zip_file.infolist()),
                crc_failure=zip_file.testzip())
structures = {}
for name in ['6IHB', '6JCQ', '6JCS']:
    data = (CACHE / (name + '.body')).read_bytes()
    block = gemmi.cif.read_string(data.decode()).sole_block()
    structures[name] = dict(bytes=len(data), sha256=digest(data), block=block.name,
                            atoms=len(block.find_values('_atom_site.id')))
summary = dict(verification_utc=now, index_rows=len(index), metadata_rows=len(metadata),
    pinder_s_cases=len(subset), paired_apo_cases=len(paired),
    missing_metadata_ids=sorted(set(subset.id) - set(metadata.id)),
    per_file_count=len(file_checks), per_file_failures=failures,
    fresh_manifest_entries=manifest_counts, root_files=root_checks,
    test_zip=zip_info, aav=structures,
    data_fetch_scope='Fresh root/archive/AAV/manifest GETs; prior individual-file GETs reused, bytes rehashed now.')
write('protein_verification.json', summary)
print('Protein verification:', len(file_checks), 'files;', len(failures), 'failures', flush=True)

data = (CACHE / 'gcp_mirror_package.body').read_bytes()
with gzip.open(CACHE / 'gcp_mirror_package.body', 'rb') as stream:
    while stream.read(1024 * 1024):
        pass
tar = tarfile.open(CACHE / 'gcp_mirror_package.body')
members = tar.getmembers()
names = {x.name for x in members}
files = []
for member in members:
    if member.isfile():
        contents = tar.extractfile(member).read()
        files.append(dict(path=member.name, bytes=len(contents), sha256=digest(contents)))
required = ['bin/frodock_mpi_gcc', 'bin/frodockgrid_mpi_gcc', 'bin/frodockcluster_gcc',
            'bin/frodockview_gcc', 'bin/soap.bin', 'compile_frodock.sh']
mirror = dict(verification_utc=now, provenance='unverified_mirror',
    url='https://storage.googleapis.com/gke-dja-demo_static_assets/frodock3_linux64.tgz',
    bytes=len(data), sha256=digest(data), sha1=digest(data, 'sha1'), md5=digest(data, 'md5'),
    gzip_crc_valid=True, tar_members=len(members), regular_files=len(files),
    uncompressed_regular_bytes=sum(x['bytes'] for x in files),
    missing_required=[x for x in required if 'frodock3_linux64/' + x not in names],
    licence_named_members=[x for x in names if any(w in x.lower() for w in ['license', 'licence', 'copying'])],
    files=files, authoritative_identity_proof=None, code_executed=False)
write('mirror_verification.json', mirror)

pypi = json.loads((CACHE / 'pinder_pypi.body').read_text())
package_checks = []
for number, package in enumerate(pypi['urls']):
    data = (CACHE / ('pinder_package_' + str(number) + '.body')).read_bytes()
    package_checks.append(dict(filename=package['filename'], url=package['url'], bytes=len(data),
        sha256=digest(data), published_sha256=package['digests']['sha256'],
        sha256_match=digest(data) == package['digests']['sha256']))
write('pinder_package_verification.json', package_checks)
assert not failures
assert all(x['size_match'] and x['md5_match'] for x in root_checks)
assert len(subset) == 250 and len(paired) == 93
assert not summary['missing_metadata_ids']
assert zip_info['crc_failure'] is None and zip_info['regular_files'] == 3914
assert all(x['sha256_match'] for x in package_checks)
print('Acquisition inspection passed. FroDock identity still unverified.', flush=True)
