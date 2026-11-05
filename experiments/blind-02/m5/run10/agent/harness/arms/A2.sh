#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PYADAPTER'
import os,json,pathlib
s=json.loads(os.environ['CMP_INPUT_SPEC'])
for role in ('receptor','ligand'):
 p=pathlib.Path(s['prepared'][role])
 if not p.is_file(): raise FileNotFoundError(p)
PYADAPTER
