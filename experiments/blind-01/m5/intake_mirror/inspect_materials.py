"""Read-only material inspection; FroDock provenance remains unverified_mirror."""
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import os
import tarfile
import zipfile

import gemmi
import pandas as pd

OUT = Path(__file__).resolve().parent
CACHE = Path('/home/hal/.cache/blind01/intake_check_dl')
PIN = 'ebeb28a2f8411363cef722b7d293c978f7442672'

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')

def git_hash(kind, data):
    return hashlib.sha1(kind.encode() + b' ' + str(len(data)).encode() + b'\0' + data).digest()

def tree_hash(tree):
    def key(pair):
        name, item = pair
        return name.encode() + (b'/' if isinstance(item, dict) else b'')
    data = b''
    for name, item in sorted(tree.items(), key=key):
        mode, oid = ('40000', tree_hash(item)) if isinstance(item, dict) else item
        data += mode.encode() + b' ' + name.encode() + b'\0' + oid
    return git_hash('tree', data)

def main():
    summary = {'inspected_utc': now()}
    index = pd.read_parquet(CACHE / 'acquire/pinder_index.body')
    subset = index[index.pinder_s]
    paired = subset[subset.apo_R & subset.apo_L]
    metadata = pd.read_parquet(CACHE / 'acquire/pinder_metadata.body', columns=['id'])
    summary.update(index_rows=len(index), metadata_rows=len(metadata), pinder_s_cases=len(subset),
                   paired_apo_cases=len(paired), missing_metadata_ids=sorted(set(subset.id)-set(metadata.id)))
    # Case IDs document coverage, without preregistering a new selection.
    summary['published_subset_ids'] = sorted(subset.id)
    summary['paired_primary_apo_ids'] = sorted(paired.id)
    with zipfile.ZipFile(CACHE / 'acquire/pinder_testzip.body') as archive:
        summary['test_zip'] = dict(entries=len(archive.infolist()),
            regular_files=sum(not m.is_dir() for m in archive.infolist()),
            directory_entries=sum(m.is_dir() for m in archive.infolist()),
            uncompressed_bytes=sum(m.file_size for m in archive.infolist()),
            crc_failure=archive.testzip())
    summary['aav'] = {}
    for name in ['6IHB', '6JCQ', '6JCS']:
        block = gemmi.cif.read(str(CACHE / 'acquire' / (name + '.body'))).sole_block()
        summary['aav'][name] = dict(entry_id=block.name, atoms=len(block.find_values('_atom_site.id')),
            revision_dates=list(block.find_values('_pdbx_audit_revision_history.revision_date')))
    summary['manifest_entries'] = {}
    for name in ['root', 'pdbs', 'mappings', 'test_set_pdbs']:
        with gzip.open(CACHE / 'acquire' / ('manifest_' + name + '.body'), 'rt') as stream:
            summary['manifest_entries'][name] = sum(1 for line in stream)
    mirror = dict(provenance='unverified_mirror', inspected_utc=now(), files=[])
    with gzip.open(CACHE / 'acquire/gcp_mirror_package.body', 'rb') as stream:
        while stream.read(1024 * 1024):
            pass
    mirror['gzip_crc_valid'] = True
    with tarfile.open(CACHE / 'acquire/gcp_mirror_package.body') as archive:
        mirror['tar_members'] = len(archive.getmembers())
        for member in archive.getmembers():
            if member.isfile():
                data = archive.extractfile(member).read()
                mirror['files'].append(dict(path=member.name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
        mirror['regular_files'] = len(mirror['files'])
        mirror['regular_bytes'] = sum(r['bytes'] for r in mirror['files'])
        mirror['licence_named_members'] = [m.name for m in archive.getmembers()
            if any(word in Path(m.name).name.lower() for word in ['license', 'licence', 'copying'])]
    write('mirror_inspection.json', mirror)
    tree = {}
    with tarfile.open(CACHE / 'codex/pinder_code.1.body') as archive:
        for member in archive.getmembers():
            if member.isdir():
                continue
            parts = member.name.split('/')[1:]
            node = tree
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            if member.issym():
                mode, data = '120000', member.linkname.encode()
            elif member.isfile():
                mode = '100755' if member.mode & 0o111 else '100644'
                data = archive.extractfile(member).read()
            else:
                raise ValueError('Unexpected archive member: ' + member.name)
            node[parts[-1]] = (mode, git_hash('blob', data))
    computed_tree = tree_hash(tree).hex()
    # Read-only public git check. Disable credential helpers, prompts and global config.
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GIT_CONFIG_GLOBAL='/dev/null',
               GIT_CONFIG_SYSTEM='/dev/null', GIT_ASKPASS='/bin/false', SSH_ASKPASS='/bin/false')
    command = ['git', '-c', 'credential.helper=', '-c', 'http.extraHeader=',
               'ls-remote', 'https://github.com/pinder-org/pinder.git', 'refs/heads/main', PIN]
    start = now()
    result = subprocess.run(command, cwd=OUT, env=env, capture_output=True, text=True, timeout=90)
    git = dict(url='https://github.com/pinder-org/pinder.git', commit=PIN,
               source_archive_computed_tree=computed_tree, ls_remote_started_utc=start,
               ls_remote_ended_utc=now(), ls_remote_exit=result.returncode,
               ls_remote_stdout=result.stdout, ls_remote_stderr=result.stderr,
               ls_remote_contains_pin=any(line.split()[0] == PIN for line in result.stdout.splitlines()))
    command = ['curl', '-q', '-fsSL', '--connect-timeout', '20', '--max-time', '60',
               f'https://api.github.com/repos/pinder-org/pinder/git/commits/{PIN}']
    start = now()
    result = subprocess.run(command, capture_output=True, text=True, timeout=75)
    git.update(commit_metadata_started_utc=start, commit_metadata_ended_utc=now(),
               commit_metadata_curl_exit=result.returncode, commit_metadata_error=result.stderr)
    if result.returncode == 0:
        obj = json.loads(result.stdout)
        git.update(commit_metadata_url=command[-1], official_commit=obj['sha'], official_tree=obj['tree']['sha'],
                   tree_match=computed_tree == obj['tree']['sha'], commit_match=obj['sha'] == PIN)
    write('git_verification.json', git)
    summary['complete'] = (len(subset) == 250 and len(paired) == 93 and not summary['missing_metadata_ids']
                           and summary['test_zip']['regular_files'] == 3914 and summary['test_zip']['crc_failure'] is None)
    write('scientific_input_inspection.json', summary)
    print(json.dumps({'scientific_complete': summary['complete'], 'git': git,
                      'mirror_members': mirror['tar_members'], 'mirror_files': mirror['regular_files']}), flush=True)

if __name__ == '__main__':
    main()
