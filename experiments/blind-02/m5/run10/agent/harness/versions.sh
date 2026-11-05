#!/usr/bin/env bash
set -euo pipefail
baseline-published/evaluator-venv/bin/python - <<'PYVERSIONS'
import json,importlib.metadata
pin='9575280c875732553266e26adc607dd892b02616'
print(json.dumps({
 'A0':{'version':pin,'executable':'baseline-published/megadock/megadock'},
 'A1':{'version':pin,'executable':'baseline-published/megadock/megadock-gpu'},
 'A2':{'version':pin,'executable':'baseline-published/megadock/megadock-gpu'},
 'evaluator':{'version':importlib.metadata.version('pinder'),'executable':'baseline-published/evaluator-venv/bin/python'}}))
PYVERSIONS
