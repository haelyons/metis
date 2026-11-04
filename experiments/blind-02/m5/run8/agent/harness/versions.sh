#!/usr/bin/env bash
set -euo pipefail
baseline-published/eval-venv/bin/python -B - <<'PY'
import importlib.metadata,json
from pathlib import Path
pin='9575280c875732553266e26adc607dd892b02616'
result={a:{'version':pin,'executable':'baseline-published/megadock/'+('megadock-gpu' if a in ['A1','A3'] else 'megadock')} for a in ['A0','A1','A2','A3']}
result['evaluator']={'version':importlib.metadata.version('pinder'),'executable':'baseline-published/eval-venv/bin/python'}
for rec in result.values():
    if not Path(rec['executable']).is_file(): raise FileNotFoundError(rec['executable'])
print(json.dumps(result))
PY
