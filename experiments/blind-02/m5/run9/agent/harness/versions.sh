#!/usr/bin/env bash
set -euo pipefail
baseline-published/pinder-venv/bin/python - <<'PY'
import json,importlib.metadata
from pathlib import Path
pin='9575280c875732553266e26adc607dd892b02616'
x={a:{'version':pin,'executable':'baseline-published/megadock/'+('megadock-gpu' if a in ('A1','A3') else 'megadock')} for a in ['A0','A1','A2','A3']}
x['evaluator']={'version':importlib.metadata.version('pinder'),'executable':'baseline-published/pinder-venv/bin/python'}
for r in x.values():
 if not Path(r['executable']).is_file(): raise FileNotFoundError(r['executable'])
print(json.dumps(x))
PY
