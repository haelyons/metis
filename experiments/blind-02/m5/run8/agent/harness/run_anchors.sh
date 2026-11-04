#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
bash harness/run_command.sh
python3 - <<'PY'
import json, math, re
from pathlib import Path
s=Path('out/stdout.log').read_text()
checks={r'# Number of output\s*=\s*(\S+)':50,r'# Set number of scores per one angle\s*=\s*(\S+)':1,r'# Set voxel size\s*=\s*(\S+)':1.2,r'# Set electric term ratio\s*=\s*(\S+)':1,r'# Set ACE term ratio\s*=\s*(\S+)':1,r'#Set score Function\s*=\s*(\S+)':3}
for pattern, expected in checks.items():
    matches=re.findall(pattern,s)
    if not matches or any(float(v)!=expected for v in matches):
        raise ValueError('Missing or invalid printed configuration: '+pattern)
if not re.search(r'# Using\s+26 CPU cores, 0 GPUs',s):
    raise ValueError('Missing or invalid CPU/GPU configuration')
rows=[]
for line in Path('out/docking.out').read_text().splitlines():
    parts=line.split()
    if len(parts)==7:
        try: values=list(map(float,parts))
        except ValueError: continue
        if not all(map(math.isfinite,values)): raise ValueError('Nonfinite docking output')
        rows.append(values)
if len(rows)!=50: raise ValueError('Missing ranked docking output')
for rank in range(1,51):
    p=Path(f'out/model_{rank}.pdb')
    if not p.is_file() or not any(l.startswith(('ATOM  ','HETATM')) for l in p.read_text().splitlines()):
        raise ValueError('Missing model '+str(p))
Path('out/anchors_measured.json').write_text('{}\n')
PY
