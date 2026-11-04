#!/usr/bin/env bash
set -euo pipefail
baseline-published/evaluator-venv/bin/python - <<'PY'
import importlib.metadata,json
pin='9575280c875732553266e26adc607dd892b02616'
d={a:{'version':pin,'executable':'baseline-published/megadock/'+('megadock-gpu' if a in ('A1','A3') else 'megadock')} for a in ('A0','A1','A2','A3')}
d['evaluator']={'version':importlib.metadata.version('pinder'),'executable':'baseline-published/evaluator-venv/bin/python'}
print(json.dumps(d))
PY
