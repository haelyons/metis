#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
bash harness/run_command.sh
python3 - <<'PY'
import json,math,shlex
from pathlib import Path
log=Path('out/baseline.log').read_text()
commands=[shlex.split(line[2:]) for line in log.splitlines() if line.startswith('+ baseline-published/megadock/megadock ')]
if not commands: raise RuntimeError('Missing published command output')
args=commands[-1];opts=dict(zip(args[1::2],args[2::2]))
for k,v in {'-N':'50','-t':'1','-v':'1.2','-e':'1.0','-d':'1.0','-a':'-45.0','-b':'1.0','-f':'3','-r':'3600'}.items():
 if opts.get(k)!=v: raise RuntimeError('Invalid printed configuration: '+k)
for key,val in {'OMP_NUM_THREADS':'26','OMP_DYNAMIC':'FALSE','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1','LC_ALL':'C','LANG':'C','CUDA_VISIBLE_DEVICES':'0'}.items():
 if f'{key}={val}' not in log: raise RuntimeError('Missing environment: '+key)
rows=[]
for line in Path('out/docking.out').read_text().splitlines():
 fields=line.split()
 if len(fields)!=7: continue
 try: nums=[float(x) for x in fields]
 except ValueError: continue
 if not all(math.isfinite(x) for x in nums): raise RuntimeError('Invalid docking output')
 rows.append(nums)
if len(rows)!=50: raise RuntimeError('Missing ranked docking output')
for r in range(1,51):
 p=Path(f'out/model_{r}.pdb')
 lines=p.read_text().splitlines()
 if not lines or lines[-1]!='END': raise RuntimeError('Invalid model output')
 atoms=[line for line in lines if line.startswith(('ATOM  ','HETATM'))]
 if not atoms: raise RuntimeError('Missing model atoms')
 for line in atoms:
  if not all(math.isfinite(float(line[a:b])) for a,b in [(30,38),(38,46),(46,54)]): raise RuntimeError('Invalid model coordinates')
Path('out/anchors_measured.json').write_text('{}\n')
PY
