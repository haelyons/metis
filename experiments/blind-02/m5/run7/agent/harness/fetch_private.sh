#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PYPRIVATE'
import pathlib,urllib.request,hashlib
items=[{'id': 'f1a19', 'access': 'evaluator private data only', 'name': 'pdbs/1a19__A1_P11540--1a19__B1_P11540.pdb', 'url': 'https://pinderdata.org/2024-02/pdbs/1a19__A1_P11540--1a19__B1_P11540.pdb', 'bytes': 116559, 'sha256': '9b112ee5082081cb9c111a3015449c72161332819251d200f6971e3f3336c7f2'}, {'id': 'f1dtd', 'access': 'evaluator private data only', 'name': 'pdbs/1dtd__A1_P48052--1dtd__B1_P81511.pdb', 'url': 'https://pinderdata.org/2024-02/pdbs/1dtd__A1_P48052--1dtd__B1_P81511.pdb', 'bytes': 230364, 'sha256': '95c095234280fb888c3ef9441f3393fc816223a960131f7dcddab2c0dbae9706'}, {'id': 'f1glj', 'access': 'evaluator private data only', 'name': 'pdbs/1glj__A1_P0A6F3--1glj__B1_P0A6F3.pdb', 'url': 'https://pinderdata.org/2024-02/pdbs/1glj__A1_P0A6F3--1glj__B1_P0A6F3.pdb', 'bytes': 633501, 'sha256': 'b9650bb0452f3f6def3954f96a30be7e2fa5f246bf308385dcd0b6ea7756903c'}, {'id': 'f1ht8', 'access': 'evaluator private data only', 'name': 'pdbs/1ht8__A1_P05979--1ht8__B1_P05979.pdb', 'url': 'https://pinderdata.org/2024-02/pdbs/1ht8__A1_P05979--1ht8__B1_P05979.pdb', 'bytes': 725355, 'sha256': 'db9192a30142d9d8f364ff13b4191841af7f4aa0ecd85b688fb8b9cef70fffd9'}]
for spec in items:
    p=pathlib.Path(spec['name']);p.parent.mkdir(parents=True,exist_ok=True)
    if not p.exists():
        b=urllib.request.urlopen(spec['url'],timeout=180).read()
        if len(b)!=spec['bytes'] or hashlib.sha256(b).hexdigest()!=spec['sha256']:raise RuntimeError('Private input checksum mismatch: '+spec['id'])
        p.write_bytes(b)
    b=p.read_bytes()
    if len(b)!=spec['bytes'] or hashlib.sha256(b).hexdigest()!=spec['sha256']:raise RuntimeError('Private input checksum mismatch: '+spec['id'])
PYPRIVATE
