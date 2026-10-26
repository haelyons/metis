#!/usr/bin/env bash
set -Eeuo pipefail
: "${EVAL_MODE:?EVAL_MODE is required}"
: "${EVAL_PROTOCOL:?EVAL_PROTOCOL is required}"
: "${EVAL_INPUTS:?EVAL_INPUTS is required}"
: "${EVAL_SEEDS:?EVAL_SEEDS is required}"
: "${EVAL_OUT:?EVAL_OUT is required}"
exec bash "$(dirname "$(readlink -f "$0")")/run_anchors.sh" "$@"
