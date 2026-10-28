#!/usr/bin/env bash
set -euo pipefail
: "${METHOD_DIR:?}"
source "$METHOD_DIR/toolkit.env"
export CUDA_VISIBLE_DEVICES=0
export PYTHONDONTWRITEBYTECODE=1
mkdir -p "${METHOD_OUT:-out}"
exec "$METHOD_DIR/venv/bin/python3" "$METHOD_DIR/method_adapter.py"
