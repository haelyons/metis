#!/usr/bin/env bash
set -euo pipefail
python3 - <<'PYADAPTER'
import os,json,pathlib
known=['f1a19', 'f1dtd', 'f1glj', 'f1ht8']
ident=os.environ['CMP_INPUT'];spec=json.loads(os.environ['CMP_INPUT_SPEC'])
if ident not in known:raise RuntimeError('Unknown input: '+ident)
for role in ('receptor','ligand'):
    path=pathlib.Path(spec['prepared'][role])
    if not path.is_file():raise RuntimeError('Missing prepared input: '+str(path))
pathlib.Path(os.environ['CMP_OUT']).mkdir(parents=True,exist_ok=True)
PYADAPTER
