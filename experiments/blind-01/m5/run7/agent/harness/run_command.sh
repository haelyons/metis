#!/usr/bin/env bash
set -euo pipefail
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# Invoke from the shared working directory; every workload path is relative.
source baseline-published/cuda.env
ls "$CUDACXX" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_RUNTIME_LIBRARY"
export CUDA_VISIBLE_DEVICES=''
export GPU_COUNT=0
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OMPI_ALLOW_RUN_AS_ROOT=1
export OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
export PINDER_DATA_DIR=data
export PINDER_RELEASE=2024-02
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
export TMPDIR=out/tmp
mkdir -p out/tmp out/logs
# A fresh directory prevents reuse while stable latest paths retain all prior logs.
run_dir=$(mktemp -d out/run.XXXXXXXX)
ln -sfn "${run_dir#out/}" out/latest
set +e
baseline-published/venv/bin/python - "$run_dir" <<'PY' 2>&1 | tee "$run_dir/stdout.log" out/command.log
import json, os, shlex, subprocess, sys
from pathlib import Path
import biotite.structure.io as strucio
from pinder.core import get_index

out=Path(sys.argv[1]); cases=json.load(open('data/cases.json'))
scale=json.load(open('harness/EXECUTION.json'))['representative_scale']
mpi_np=8; n_solutions=5
if len(cases)!=scale['primary_cases'] or mpi_np!=scale['mpi_processes'] or n_solutions!=scale['candidate_poses_per_case']:
    raise RuntimeError('Prepared workload does not match fixed execution scale')
index=get_index()
ids=sorted(index.loc[index.pinder_s & index.apo_R & index.apo_L,'id'])
if [c['id'] for c in cases]!=ids: raise RuntimeError('Prepared IDs differ from full paired-primary-apo subset')
config=dict(primary_cases=len(cases),mpi_np=mpi_np,n_solutions=n_solutions,gpu_count=int(os.environ['GPU_COUNT']),CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'],OMP_NUM_THREADS=os.environ['OMP_NUM_THREADS'],release=os.environ['PINDER_RELEASE'],docking_flags='--th 10 -t A',compiler=os.environ['CUDACXX'],include=os.environ['CUDA_INCLUDE_DIR'],library=os.environ['CUDA_RUNTIME_LIBRARY'])
if config['gpu_count']!=0 or config['CUDA_VISIBLE_DEVICES']!='': raise RuntimeError('CPU baseline environment mismatch')
print('CONFIG '+json.dumps(config),flush=True)
print('INPUT_IDS '+json.dumps(ids),flush=True)
bin_dir=Path('baseline-published/frodock3_linux64/bin')
poses=0
for c in cases:
    cid=c['id']
    if Path(cid).name!=cid: raise RuntimeError('Invalid case identity')
    work=out/'work'/cid; work.mkdir(parents=True)
    for key,name in [('receptor','receptor'),('ligand','ligand')]:
        atoms=strucio.load_structure(c[key]); atoms.chain_id[:]='R' if key=='receptor' else 'L'
        strucio.save_structure(str(work/(name+'.pdb')),atoms)
    # relpath keeps subprocess arguments portable across sibling working dirs.
    pre=os.path.relpath(bin_dir,work)
    def binary(name): return pre+'/'+name
    run=['mpirun','-np',str(mpi_np),'--use-hwthread-cpus']
    stages=[
        run+[binary('frodockgrid_mpi_gcc'),'receptor.pdb','-o','receptor_W.mrc'],
        run+[binary('frodockgrid_mpi_gcc'),'receptor.pdb','-o','receptor_E.mrc','-m','1','-t','A'],
        run+[binary('frodockgrid_mpi_gcc'),'receptor.pdb','-o','receptor_DS.mrc','-m','3'],
        run+[binary('frodockgrid_mpi_gcc'),'ligand.pdb','-o','ligand_DS.mrc','-m','3'],
        run+[binary('frodock_mpi_gcc'),'receptor_ASA.pdb','ligand_ASA.pdb','-w','receptor_W.mrc','-e','receptor_E.mrc','--th','10','-d','receptor_DS.mrc,ligand_DS.mrc','-t','A','-o','dock.dat','-s',binary('soap.bin')],
        [binary('frodockcluster_gcc'),'dock.dat','ligand.pdb','--nc',str(n_solutions),'-o','clust_dock.dat'],
        [binary('frodockview_gcc'),'clust_dock.dat','-r',f'1-{n_solutions}'],
        [binary('frodockview_gcc'),'clust_dock.dat','-r',f'1-{n_solutions}','-p','ligand.pdb'],
    ]
    with (work/'binary.log').open('w') as log:
        for command in stages:
            print('COMMAND '+json.dumps({'input_id':cid,'cwd':str(work),'argv':command}),flush=True)
            log.write('$ '+shlex.join(command)+'\n'); log.flush()
            result=subprocess.run(command,cwd=work,stdout=log,stderr=subprocess.STDOUT)
            if result.returncode:
                print((work/'binary.log').read_text(),flush=True)
                sys.exit(result.returncode if result.returncode>0 else 128-result.returncode)
    target=out/'eval_dir'/'frodock'/cid/'apo_decoys'; target.mkdir(parents=True)
    receptor=strucio.load_structure(str(work/'receptor.pdb')); receptor.chain_id[:]='R'
    for rank in range(1,n_solutions+1):
        ligand=strucio.load_structure(str(work/f'ligand_{rank}.pdb')); ligand.chain_id[:]='L'
        pose=receptor+ligand
        if set(pose.chain_id)!={'R','L'} or len(pose)==0: raise RuntimeError('Invalid generated pose')
        strucio.save_structure(str(target/f'model_{rank}.pdb'),pose); poses+=1
    print('CASE_OUTPUT '+json.dumps({'input_id':cid,'poses':n_solutions,'log':str(work/'binary.log')}),flush=True)
print('RESULT '+json.dumps({'pinder_s_total_reference':int(index.pinder_s.sum()),'pinder_s_paired_apo_reference':len(ids),'poses':poses,'eval_dir':str(out/'eval_dir')}),flush=True)
PY
status=${PIPESTATUS[0]}
set -e
exit "$status"
