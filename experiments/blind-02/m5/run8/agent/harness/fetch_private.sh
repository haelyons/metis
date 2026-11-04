#!/usr/bin/env bash
set -euo pipefail
# The pipeline invokes this script with the private directory as its cwd.
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
python3 - "$script_dir/inputs.json" <<'PY'
import hashlib, json, sys, urllib.request
from pathlib import Path
root=Path.cwd()
for item in json.loads(Path(sys.argv[1]).read_text()):
    spec=item['spec']['reference']
    path=root/spec['name']
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        data=path.read_bytes()
    else:
        with urllib.request.urlopen(spec['url'],timeout=120) as response:
            data=response.read()
    if len(data)!=spec['bytes'] or hashlib.sha256(data).hexdigest()!=spec['sha256']:
        raise ValueError('Private source bytes/hash mismatch: '+spec['name'])
    path.write_bytes(data)
    print(item['id'],spec['name'],len(data),hashlib.sha256(data).hexdigest())
PY
