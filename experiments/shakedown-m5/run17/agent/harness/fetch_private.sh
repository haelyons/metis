#!/usr/bin/env bash
# Shakedown stand-in for the evaluator's private data: one published file at a pinned commit, checked by digest.
# Runs as cmp-eval with working directory cmp-private; writes only there.
set -euo pipefail
url=https://raw.githubusercontent.com/karpathy/nanoGPT/3adf61e154c3fe3fca428ad6bc3818b27a3b8291/README.md
curl -sfL --retry 3 -o reference.md "$url"
echo "8d969370683849a2cc4e46c81bf2449717f2daff657586888151933c3590f85f  reference.md" | sha256sum -c --quiet -
