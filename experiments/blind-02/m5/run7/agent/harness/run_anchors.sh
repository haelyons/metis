#!/usr/bin/env bash
set -euo pipefail
if [[ -n "${EVAL_MODE:-}" && "${EVAL_MODE}" != anchors ]]; then
    exec bash harness/run_evaluation.sh
fi
mkdir -p out
bash harness/run_command.sh
python3 - <<'PY'
import pathlib,math,json,re,shlex
root=pathlib.Path('out/a0-smoke')
log=(root/'stdout.log').read_text()
if not log.strip():raise RuntimeError('Missing published binary output')
expected=['baseline-published/megadock/megadock','-R','data/fixtures/f1a19/R.pdb','-L','data/fixtures/f1a19/L.pdb','-o','out/docking.out','-N','50','-t','1','-v','1.2','-e','1.0','-d','1.0','-a','-45.0','-b','1.0','-f','3','-r','3600']
launches=[shlex.split(line[2:]) for line in log.splitlines() if line.startswith('+ baseline-published/megadock/megadock ')]
if not launches or any(args!=expected for args in launches):raise RuntimeError('Invalid executed baseline configuration')
configuration='environment: OMP_NUM_THREADS=26 OMP_DYNAMIC=FALSE OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 LC_ALL=C LANG=C CUDA_VISIBLE_DEVICES=0 gpu_count=0'
if configuration not in log.splitlines():raise RuntimeError('Invalid execution environment output')
for pattern,value in [(r'(?im)^\s*(?:number of rotations|rotation angles|rotations)\s*[:=]\s*(\d+)',3600), (r'(?im)^\s*(?:number of predictions|retained predictions)\s*[:=]\s*(\d+)',50)]:
    for printed in re.findall(pattern,log):
        if int(printed)!=value:raise RuntimeError('Published binary reported inconsistent configuration')
rows=[]
for line in (root/'out/docking.out').read_text().splitlines():
    fields=line.split()
    if len(fields)!=7:continue
    try:values=list(map(float,fields))
    except ValueError:continue
    if not all(math.isfinite(v) for v in values):raise RuntimeError('Nonfinite docking output')
    rows.append(values)
if len(rows)!=50:raise RuntimeError('Expected 50 ranked prediction rows')
for r in range(1,51):
    lines=(root/f'out/model_{r}.pdb').read_text().splitlines()
    atoms=[line for line in lines if line.startswith(('ATOM  ','HETATM'))]
    if not atoms or lines[-1]!='END':raise RuntimeError('Invalid assembled model')
    for line in atoms:
        if not all(math.isfinite(float(line[i:i+8])) for i in (30,38,46)):raise RuntimeError('Invalid model coordinates')
# No published anchors or reference measurements are declared in this intake.
pathlib.Path('out/anchors_measured.json').write_text(json.dumps({})+'\n')
PY
