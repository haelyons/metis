#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PY'
import hashlib,urllib.request
from pathlib import Path
items=[{'access': 'evaluator private data only', 'name': 'pdbs/1a19__A1_P11540--1a19__B1_P11540.pdb', 'url': 'https://pinderdata.org/2024-02/pdbs/1a19__A1_P11540--1a19__B1_P11540.pdb', 'bytes': 116559, 'sha256': '9b112ee5082081cb9c111a3015449c72161332819251d200f6971e3f3336c7f2'}, {'access': 'evaluator private data only', 'name': 'pdbs/1dtd__A1_P48052--1dtd__B1_P81511.pdb', 'url': 'https://pinderdata.org/2024-02/pdbs/1dtd__A1_P48052--1dtd__B1_P81511.pdb', 'bytes': 230364, 'sha256': '95c095234280fb888c3ef9441f3393fc816223a960131f7dcddab2c0dbae9706'}, {'access': 'evaluator private data only', 'name': 'pdbs/1glj__A1_P0A6F3--1glj__B1_P0A6F3.pdb', 'url': 'https://pinderdata.org/2024-02/pdbs/1glj__A1_P0A6F3--1glj__B1_P0A6F3.pdb', 'bytes': 633501, 'sha256': 'b9650bb0452f3f6def3954f96a30be7e2fa5f246bf308385dcd0b6ea7756903c'}, {'access': 'evaluator private data only', 'name': 'pdbs/1ht8__A1_P05979--1ht8__B1_P05979.pdb', 'url': 'https://pinderdata.org/2024-02/pdbs/1ht8__A1_P05979--1ht8__B1_P05979.pdb', 'bytes': 725355, 'sha256': 'db9192a30142d9d8f364ff13b4191841af7f4aa0ecd85b688fb8b9cef70fffd9'}]
for s in items:
 p=Path(s['name']);p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():
  with urllib.request.urlopen(s['url'],timeout=120) as r: blob=r.read()
  t=p.with_suffix('.download');t.write_bytes(blob);t.replace(p)
 b=p.read_bytes()
 if len(b)!=s['bytes'] or hashlib.sha256(b).hexdigest()!=s['sha256']: raise RuntimeError('Reference integrity failure: '+str(p))
PY
