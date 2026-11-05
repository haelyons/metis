#!/usr/bin/env bash
set -euo pipefail
: "${EVAL_OUT:?}" "${EVAL_PROTOCOL:?}" "${EVAL_INPUTS:?}" "${EVAL_SEEDS:?}" "${EVAL_MODE:?}"
mkdir -p "$EVAL_OUT"
source baseline-published/cuda-env.sh
export OMP_NUM_THREADS=26 OMP_DYNAMIC=FALSE OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 LC_ALL=C LANG=C CUDA_VISIBLE_DEVICES=0
python3 - <<'PY'
import os,json,time,subprocess,math
from pathlib import Path
protocol=json.loads(Path(os.environ['EVAL_PROTOCOL']).read_text())
inputs=json.loads(os.environ['EVAL_INPUTS'])
seed_spec=json.loads(os.environ['EVAL_SEEDS'])
seeds=seed_spec['seeds'] if seed_spec['kind']=='paired_median' else [None]
if seed_spec['kind'] not in ('paired_median','deterministic'): raise ValueError('Unknown seed protocol')
if os.environ['EVAL_MODE'] not in ('equivalence','warmup','performance','curve'): raise ValueError('Unknown evaluation mode')
if os.environ['EVAL_MODE']=='curve':
 raise RuntimeError('The published comparison has no curve arm or GPU-second budget protocol')
# The sealed fixture program is deterministic and has no seed argument.
known={'f1a19','f1dtd','f1glj','f1ht8'}
root=Path.cwd();out=Path(os.environ['EVAL_OUT']).resolve()
exe=root/'baseline-published/megadock/megadock';decoy=root/'baseline-published/megadock/decoygen'
records=[];total_start=time.monotonic()
for si,seed in enumerate(seeds):
 for ii,input_id in enumerate(inputs['ids']):
  if input_id not in known: raise ValueError('Unpublished fixture: '+input_id)
  dest=out/f'seed_{si}'/input_id;dest.mkdir(parents=True,exist_ok=True)
  rec=root/'data/fixtures'/input_id/'R.pdb';lig=root/'data/fixtures'/input_id/'L.pdb'
  command=[str(exe),'-R',str(rec),'-L',str(lig),'-o',str(dest/'docking.out'),'-N','50','-t','1','-v','1.2','-e','1.0','-d','1.0','-a','-45.0','-b','1.0','-f','3','-r','3600']
  start=time.monotonic()
  with (dest/'command.log').open('a') as log:
   log.write(json.dumps({'argv':command,'gpu_count':0,'environment':{k:os.environ[k] for k in ['OMP_NUM_THREADS','OMP_DYNAMIC','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','LC_ALL','LANG','CUDA_VISIBLE_DEVICES']}})+'\n');log.flush()
   subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,cwd=root)
  for rank in range(1,51):
   ligand=dest/f'lig_{rank}.pdb'
   with (dest/f'decoygen_{rank}.log').open('a') as log:
    subprocess.run([str(decoy),str(ligand),str(lig),str(dest/'docking.out'),str(rank)],stdout=log,stderr=subprocess.STDOUT,check=True,cwd=root)
   rec_lines=[l for l in rec.read_bytes().splitlines(keepends=True) if not l.startswith(b'END')]
   lig_lines=[l for l in ligand.read_bytes().splitlines(keepends=True) if not l.startswith((b'END',b'ENDMDL'))]
   model=dest/f'model_{rank}.pdb';model.write_bytes(b''.join(rec_lines+lig_lines)+b'END\n')
   atoms=[l for l in model.read_text().splitlines() if l.startswith(('ATOM  ','HETATM'))]
   if not atoms or not all(math.isfinite(float(l[a:b])) for l in atoms for a,b in [(30,38),(38,46),(46,54)]): raise RuntimeError('Invalid model output')
  wall=time.monotonic()-start
  records.append({'input_id':input_id,'seed':seed,'metrics':{'wall':wall}})
# A0 uses the CPU implementation: there are no used GPUs to synchronize.
result={'records':records,'timing_scope':protocol['timing_scope'],'gpu_count':0,'wall_s':time.monotonic()-total_start,'compute_budget':None}
(out/'evaluation.json').write_text(json.dumps(result,allow_nan=False)+'\n')
PY
