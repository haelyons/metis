#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PYPRIVATE'
import json,pathlib,urllib.request,hashlib
items=json.loads('[{"access": "evaluator private data only", "name": "pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb", "url": "https://pinderdata.org/2024-02/pdbs/1aua__A1_P24280--1aua__A2_P24280.pdb", "bytes": 388881, "sha256": ["a12fd5f7506b927c1d435464cabbb9cd59299fdc4a826b63302052b0fef4", "1a48"]}, {"access": "evaluator private data only", "name": "pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb", "url": "https://pinderdata.org/2024-02/pdbs/1ax2__A1_P16404--1ax2__A2_P16404.pdb", "bytes": 300591, "sha256": ["111ed0e1daea9ff8575bb61a2184b5f58fedd5437846e0f8026bebb53ef77a10"]}, {"access": "evaluator private data only", "name": "pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb", "url": "https://pinderdata.org/2024-02/pdbs/1dv1__A1_P24182--1dv1__B1_P24182.pdb", "bytes": 536625, "sha256": ["a159da5b6b145570b4d03ac9e17eb7b4315f7a8afd0497a93ad1f77a55debf3e"]}, {"access": "evaluator private data only", "name": "pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb", "url": "https://pinderdata.org/2024-02/pdbs/1nr5__A1_P07547--1nr5__A2_P07547.pdb", "bytes": 484785, "sha256": ["ee2fc4", "9ec38f2", "6a216154fd7ce0a93086f2ba60dde6997d86deb196bac96f861"]}]')

for s in items:
 p=pathlib.Path(s['name']); p.parent.mkdir(parents=True,exist_ok=True)
 with urllib.request.urlopen(s['url'],timeout=120) as r: raw=r.read()
 if len(raw)!=s['bytes'] or hashlib.sha256(raw).hexdigest()!=''.join(s['sha256']): raise ValueError('Private data size/checksum mismatch: '+s['name'])
 p.write_bytes(raw)
PYPRIVATE
