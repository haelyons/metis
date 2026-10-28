#!/usr/bin/env bash
set -euo pipefail
: "${METHOD_DIR:?METHOD_DIR must identify the patched copy}"
export PYTHONDONTWRITEBYTECODE=1
python3 - "$METHOD_DIR" <<'PY'
import ast, pathlib, sys
root=pathlib.Path(sys.argv[1])
for name in ('dhfr_ensemble.py','method_evaluate.py'):
    ast.parse((root/name).read_text(),filename=str(root/name))
PY
