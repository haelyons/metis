#!/usr/bin/env bash
# Faithful pre-launch resolve (gate addendum 8): pip's dry-run of the runner's PIP_PINS in a real CPython 3.10 (uv-managed),
# sdists allowed (their metadata is built locally), report written beside the runner. Prints counts only.
#   usage: bash pip_resolve_310.sh <measure dir> <build number>
set -u
# scratch on disk, never on the quota-limited tmpfs (a metadata build there failed on quota, 2026-10-21)
export TMPDIR=${TMPDIR_DISK:-$HOME/.cache/blind01/tmp} UV_CACHE_DIR=${UV_CACHE_DIR:-$HOME/.cache/blind01/uv} PIP_CACHE_DIR=${PIP_CACHE_DIR:-$HOME/.cache/blind01/pip}
mkdir -p "$TMPDIR" "$UV_CACHE_DIR" "$PIP_CACHE_DIR"
M=$(realpath "$1"); N=$2; S=$TMPDIR/pip_resolve_310_$$; mkdir -p "$S"
python3 - "$M/run_m4.py" > "$S/pins.txt" <<'PY'
import ast, sys
for node in ast.walk(ast.parse(open(sys.argv[1]).read())):
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id.lower() == "pip_pins" for t in node.targets):
        v = ast.literal_eval(node.value); print("\n".join([f"{k}=={x}" for k, x in v.items()] if isinstance(v, dict) else [str(x) for x in v]))
PY
uv venv --quiet --seed --python 3.10 "$S/venv" || { echo "uv venv failed"; exit 2; }
timeout 900 "$S/venv/bin/python" -m pip install --dry-run --quiet --report "$M/out/pip_pins_resolve_build$N.json" --target "$S/target" -r "$S/pins.txt" > "$M/out/pip_pins_resolve_build$N.txt" 2>&1; rc=$?
echo "pip dry-run resolve of build $N's $(wc -l < "$S/pins.txt") pins in CPython 3.10 (sdists allowed): exit $rc; ResolutionImpossible $(grep -c ResolutionImpossible "$M/out/pip_pins_resolve_build$N.txt"); 'No matching distribution' $(grep -c 'No matching distribution' "$M/out/pip_pins_resolve_build$N.txt"); error lines $(grep -ci '^error' "$M/out/pip_pins_resolve_build$N.txt"); packages in the report $(python3 -c "import json; print(len(json.load(open('$M/out/pip_pins_resolve_build$N.json')).get('install', [])))" 2>/dev/null || echo 0)"
rm -rf "$S"; exit $rc
