#!/usr/bin/env bash
set -euo pipefail
: "${CMP_INPUT:?}" "${CMP_INPUT_SPEC:?}"
python3 - <<'PYADAPTER'
import json, os
from pathlib import Path
spec=json.loads(os.environ['CMP_INPUT_SPEC'])
for name in ['receptor','ligand']:
    path=Path(spec['prepared'][name])
    if not path.is_file(): raise FileNotFoundError(path)
PYADAPTER
