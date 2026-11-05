#!/usr/bin/env bash
set -euo pipefail
: "${CMP_INPUT:?}" "${CMP_INPUT_SPEC:?}" "${CMP_OUT:?}"
python3 - <<'PY'
import os,json
from pathlib import Path
spec=json.loads(os.environ['CMP_INPUT_SPEC'])
for role in ('receptor','ligand'):
 p=Path(spec['prepared'][role])
 if not p.is_file(): raise FileNotFoundError(p)
PY
