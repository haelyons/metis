#!/usr/bin/env bash
set -euo pipefail
# Working directory: shared remote work directory containing baseline-published/, data/, harness/.
# CPU/MPI baseline: no GPU used. Inherit pipeline-owned MPS environment unchanged.
export CUDA_VISIBLE_DEVICES=''
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
export PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
export PINDER_DATA_DIR=data PINDER_RELEASE=2024-02
export PATH=/usr/local/bin:/usr/bin:/bin
export TMPDIR=/tmp
mkdir -p out
# Reuse precisely the compiler/include/library selection verified during setup.
readarray -t cuda_paths < data/cuda-paths.txt
ls "${cuda_paths[0]}" "${cuda_paths[1]}/cuda_runtime.h" "${cuda_paths[2]}"
export CMAKE_CUDA_COMPILER="${cuda_paths[0]}"
if [[ ${cuda_paths[0]} != /usr/bin/nvcc ]]; then
  export CUDAToolkit_ROOT="${cuda_paths[0]%/bin/nvcc}"
  export PATH="${CUDAToolkit_ROOT}/bin:$PATH"
fi
export CPLUS_INCLUDE_PATH="${cuda_paths[1]}"
export LD_LIBRARY_PATH="${cuda_paths[2]%/*}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
timeout --foreground --signal=TERM --kill-after=10s 1150s baseline-published/venv/bin/python - <<'PY' 2>&1 | tee -a out/baseline.log
import json,math,os,pathlib,shutil,subprocess,tempfile,time
import pandas as pd
import biotite.structure.io as strucio
from pinder.eval.dockq.method import get_eval_metrics

root=pathlib.Path.cwd()
work=pathlib.Path(tempfile.mkdtemp(prefix='run-',dir='out'))
index=pd.read_parquet('data/index.parquet')
configs=json.load(open('data/prepared.json'))
expected=sorted(index.loc[index.pinder_s & index.apo_R & index.apo_L,'id'])
if [c['id'] for c in configs]!=expected:raise RuntimeError('Prepared input identities differ from fixed paired-apo selection')
configuration={'cases':len(configs),'pairs':'apo','n_solutions':5,'mpi_np':8,
               'interaction_type':'A','docking_th':10,'gpu_count':0,
               'CUDA_VISIBLE_DEVICES':os.environ['CUDA_VISIBLE_DEVICES'],
               'working_directory':'.','pinder_commit':'ebeb28a2f8411363cef722b7d293c978f7442672'}
if configuration['CUDA_VISIBLE_DEVICES']!='':raise RuntimeError('Invalid CPU baseline environment')
print('CONFIGURATION '+json.dumps(configuration),flush=True)
mpi=shutil.which('mpirun')
if not mpi:raise RuntimeError('Published MPI launcher unavailable')
bindir=pathlib.Path('baseline-published/frodock/bin')
results=work/'results'
started=time.monotonic()
for item in configs:
    case=work/'stages'/item['id'];case.mkdir(parents=True)
    receptor=pathlib.Path(item['receptor']);ligand=pathlib.Path(item['ligand'])
    shutil.copyfile(receptor,case/'receptor.pdb');shutil.copyfile(ligand,case/'ligand.pdb')
    pre=os.path.relpath(bindir,case)+'/'
    launch=[mpi,'-np',str(configuration['mpi_np']),'--use-hwthread-cpus']
    stages=[
      launch+[pre+'frodockgrid_mpi_gcc','receptor.pdb','-o','receptor_W.mrc'],
      launch+[pre+'frodockgrid_mpi_gcc','receptor.pdb','-o','receptor_E.mrc','-m','1','-t',configuration['interaction_type']],
      launch+[pre+'frodockgrid_mpi_gcc','receptor.pdb','-o','receptor_DS.mrc','-m','3'],
      launch+[pre+'frodockgrid_mpi_gcc','ligand.pdb','-o','ligand_DS.mrc','-m','3'],
      launch+[pre+'frodock_mpi_gcc','receptor_ASA.pdb','ligand_ASA.pdb',
              '-w','receptor_W.mrc','-e','receptor_E.mrc','--th',str(configuration['docking_th']),
              '-d','receptor_DS.mrc,ligand_DS.mrc','-t',configuration['interaction_type'],
              '-o','dock.dat','-s',pre+'soap.bin'],
      [pre+'frodockcluster_gcc','dock.dat','ligand.pdb','--nc',str(configuration['n_solutions']),'-o','clust_dock.dat'],
      [pre+'frodockview_gcc','clust_dock.dat','-r','1-'+str(configuration['n_solutions'])],
      [pre+'frodockview_gcc','clust_dock.dat','-r','1-'+str(configuration['n_solutions']),'-p','ligand.pdb']]
    if any(cmd[:len(launch)]!=launch for cmd in stages[:5]):raise RuntimeError('Invalid MPI launch configuration')
    print('CASE '+item['id'],flush=True)
    for cmd in stages:
        print('COMMAND '+json.dumps(cmd),flush=True)
        subprocess.run(cmd,cwd=case,check=True)
    target=results/'frodock'/item['id']/'apo_decoys';target.mkdir(parents=True)
    r=strucio.load_structure(str(case/'receptor.pdb'));r.chain_id[:]='R'
    for rank in range(1,configuration['n_solutions']+1):
        l=strucio.load_structure(str(case/f'ligand_{rank}.pdb'));l.chain_id[:]='L'
        strucio.save_structure(str(target/f'model_{rank}.pdb'),r+l)
# Synchronous CPU subprocesses complete before timer stops. GPU count is zero.
wall=time.monotonic()-started
scoring_started=time.monotonic()
frames=[]
for item in configs:
    frame=get_eval_metrics({'system':results/'frodock'/item['id'],'method_name':'frodock'},parallel_io=False)
    if len(frame)!=5:raise RuntimeError('Incomplete per-pose evaluator output for '+item['id'])
    for metric in ['DockQ','iRMS','LRMS','Fnat']:
        if not all(math.isfinite(float(v)) for v in frame[metric]):raise RuntimeError('Invalid '+metric+' output')
    frame['input_id']=item['id'];frames.append(frame)
metrics=pd.concat(frames,ignore_index=True)
metrics.to_csv(work/'pose_metrics.csv',index=False)
case_metrics={}
for input_id,frame in metrics.groupby('input_id',sort=False):
    best=frame.loc[frame.DockQ.idxmax()]
    first=frame.loc[frame.model_name.map(lambda s:pathlib.Path(str(s)).stem=='model_1')]
    if len(first)!=1:raise RuntimeError('Missing or duplicate rank-one output')
    top=first.iloc[0]
    case_metrics[input_id]={k:float(top[k]) for k in ['DockQ','iRMS','LRMS','Fnat']}
    case_metrics[input_id].update({'top1_DockQ':float(top.DockQ),'best_of_5_DockQ':float(best.DockQ),
                                'acceptable_top1':float(top.DockQ>=0.23),
                                'acceptable_best_of_5':float(best.DockQ>=0.23)})
aggregate={k:sum(v[k] for v in case_metrics.values())/len(case_metrics) for k in next(iter(case_metrics.values()))}
measurements={'pinder_s_complex_count':int(index.pinder_s.sum()),
              'pinder_s_paired_apo_count':len(expected),
              'dockq_acceptable_pose':float(metrics.DockQ.max())}
aggregate.update(measurements)
aggregate.update({'wall_s':wall,'candidate_throughput':len(metrics)/wall})
summary={'configuration':configuration,'measurements':measurements,'metrics':aggregate,
         'case_metrics':case_metrics,'wall_s':wall,'scoring_wall_s':time.monotonic()-scoring_started,
         'gpu_count':0,'output_dir':str(work)}
(work/'summary.json').write_text(json.dumps(summary,allow_nan=False))
print('BASELINE_OUTPUT '+json.dumps(summary,allow_nan=False),flush=True)
PY
