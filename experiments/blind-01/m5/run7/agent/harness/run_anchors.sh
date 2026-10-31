#!/usr/bin/env bash
set -euo pipefail
if [[ -n "${EVAL_MODE:-}" && "${EVAL_MODE}" != anchor && "${EVAL_MODE}" != anchors ]]; then
    exec bash harness/run_evaluation.sh
fi
mkdir -p out
# No environment overrides here: profiler invokes this identical canonical file.
bash harness/run_command.sh
source baseline-published/cuda.env
ls "$CUDACXX" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_RUNTIME_LIBRARY"
# Scoring is separate from the docking command and uses the published evaluator.
PINDER_DATA_DIR=data PINDER_RELEASE=2024-02 PYTHONDONTWRITEBYTECODE=1 baseline-published/venv/bin/python - <<'PY' 2>&1 | tee out/latest/scoring.log out/scoring.log
import json, math
from pathlib import Path
import pandas as pd
from pinder.eval.dockq.biotite_dockq import BiotiteDockQ

lines=Path('out/command.log').read_text().splitlines()
def get(prefix):
    found=[json.loads(x[len(prefix):]) for x in lines if x.startswith(prefix)]
    if len(found)!=1: raise RuntimeError('Missing or duplicated '+prefix)
    return found[0]
config=get('CONFIG '); result=get('RESULT '); ids=get('INPUT_IDS ')
scale=json.load(open('harness/EXECUTION.json'))['representative_scale']
expected={'primary_cases':scale['primary_cases'],'mpi_np':scale['mpi_processes'],'n_solutions':scale['candidate_poses_per_case'],'gpu_count':0,'CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'1','release':'2024-02','docking_flags':'--th 10 -t A'}
for k,v in expected.items():
    if config.get(k)!=v: raise RuntimeError('Printed configuration mismatch: '+k)
commands=[json.loads(x[len('COMMAND '):]) for x in lines if x.startswith('COMMAND ')]
if len(commands)!=len(ids)*8: raise RuntimeError('Incomplete command output')
for i,cid in enumerate(ids):
    stages=commands[i*8:(i+1)*8]
    for stage in stages:
        if stage['input_id']!=cid: raise RuntimeError('Command identity mismatch')
    for stage in stages[:5]:
        if stage['argv'][:4]!=['mpirun','-np',str(config['mpi_np']),'--use-hwthread-cpus']: raise RuntimeError('MPI arguments mismatch')
    dock=stages[4]['argv']
    if dock[dock.index('--th')+1]!='10' or dock[dock.index('-t')+1]!='A': raise RuntimeError('Docking flags mismatch')
    if stages[5]['argv'][stages[5]['argv'].index('--nc')+1]!=str(config['n_solutions']): raise RuntimeError('Pose count mismatch')
frames=[]
for cid in ids:
    paths=[Path(result['eval_dir'])/'frodock'/cid/'apo_decoys'/f'model_{rank}.pdb' for rank in range(1,config['n_solutions']+1)]
    if not all(p.is_file() and p.stat().st_size for p in paths): raise RuntimeError('Missing pose output '+cid)
    df=BiotiteDockQ(native=Path('data/pdbs')/(cid+'.pdb'),decoys=paths,native_receptor_chain=['R'],native_ligand_chain=['L'],decoy_receptor_chain=['R'],decoy_ligand_chain=['L'],parallel_io=False).calculate()
    if len(df)!=len(paths): raise RuntimeError('Incomplete metrics '+cid)
    for key in ['DockQ','iRMS','LRMS','Fnat']:
        if not all(math.isfinite(float(x)) for x in df[key]): raise RuntimeError('Invalid '+key+' '+cid)
    df['input_id']=cid
    frames.append(df)
    print('CASE_METRICS '+json.dumps({'input_id':cid,'DockQ':float(df.DockQ.max()),'iRMS':float(df.iRMS.min()),'LRMS':float(df.LRMS.min()),'Fnat':float(df.Fnat.max())},allow_nan=False),flush=True)
metrics=pd.concat(frames,ignore_index=True)
metrics.to_csv(Path(result['eval_dir'])/'frodock_metrics.csv',index=False)
rank1=metrics[metrics.model_name=='model_1']
summary={'DockQ':float(metrics.groupby('input_id').DockQ.max().mean()),'iRMS':float(metrics.groupby('input_id').iRMS.min().mean()),'LRMS':float(metrics.groupby('input_id').LRMS.min().mean()),'Fnat':float(metrics.groupby('input_id').Fnat.max().mean()),'rank1_success_rate':float((rank1.DockQ>=0.23).sum()/len(ids)),'top5_success_rate':float((metrics.groupby('input_id').DockQ.max()>=0.23).sum()/len(ids))}
print('SUMMARY '+json.dumps(summary,allow_nan=False),flush=True)
measured={k:result[k] for k in ['pinder_s_total_reference','pinder_s_paired_apo_reference']}
measured['dockq_acceptable_pose']=float(metrics.DockQ.max())
print('MEASURED '+json.dumps(measured,allow_nan=False),flush=True)
PY
python3 - <<'PY'
import json,math
from pathlib import Path
items=json.load(open('harness/anchors.json'))
if isinstance(items,dict): items=items.get('anchors',[])+items.get('references',[])
lines=Path('out/scoring.log').read_text().splitlines()
rows=[json.loads(l[9:]) for l in lines if l.startswith('MEASURED ')]
if len(rows)!=1: raise RuntimeError('Missing measured output')
measured=rows[0]; answer={}
for item in items:
    key=item['id']; value=measured.get(key)
    if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value): raise RuntimeError('Missing or invalid measured output '+key)
    answer[key]=value
Path('out/anchors_measured.json').write_text(json.dumps(answer,indent=2,allow_nan=False)+'\n')
PY
