#!/usr/bin/env bash
set -euo pipefail

mkdir -p out
bash harness/run_command.sh
python3 - <<'PYANCHORS'
import pathlib,math,json,shlex
log=pathlib.Path('out/baseline.log').read_text()
expected=['baseline-published/megadock/megadock','-R','data/inputs/1aua_R.pdb','-L','data/inputs/1aua_L.pdb','-o','out/docking.out','-N','50','-t','1','-v','1.2','-e','1','-d','1','-a','-45.0','-b','1','-f','3','-r','3600']
commands=[shlex.split(line[2:]) for line in log.splitlines() if line.startswith('+ baseline-published/megadock/megadock ')]
if not commands or any(command!=expected for command in commands):raise ValueError('Invalid printed invocation configuration')
for setting in ['OMP_NUM_THREADS=26','OMP_DYNAMIC=FALSE','OPENBLAS_NUM_THREADS=1','MKL_NUM_THREADS=1','NUMEXPR_NUM_THREADS=1','LC_ALL=C','LANG=C','CUDA_VISIBLE_DEVICES=0']:
 if '+ '+setting not in log:raise ValueError('Missing printed environment: '+setting)
p=pathlib.Path('out/docking.out')
rows=[]
for line in p.read_text().splitlines():
 fields=line.split()
 if len(fields)!=7: continue
 try: values=list(map(float,fields))
 except ValueError: continue
 if not all(map(math.isfinite,values)): raise ValueError('Invalid docking output')
 rows.append(values)
if len(rows)!=50: raise ValueError('Missing ranked prediction output')
for r in range(1,51):
 p=pathlib.Path(f'out/model_{r}.pdb')
 if not p.is_file() or not p.stat().st_size: raise ValueError('Missing reconstructed model')
if not pathlib.Path('out/baseline.log').stat().st_size:raise ValueError('Missing published stdout/stderr')
# Intake anchors.json is empty; no published values are used as measurements.
pathlib.Path('out/anchors_measured.json').write_text('{}\n')
PYANCHORS
