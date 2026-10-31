#!/usr/bin/env bash
set -Eeuo pipefail
# Invoked from the shared work directory. CPU FroDock uses zero GPUs.
mkdir -p out
select_cuda() {
    local root
    for root in /usr/local/cuda /usr/lib/cuda; do
        if [[ -x "$root/bin/nvcc" && -f "$root/include/cuda_runtime.h" && -f "$root/lib64/libcudart.so" ]]; then
            export CUDACXX="$root/bin/nvcc" CUDA_INCLUDE_DIR="$root/include" CUDA_LIBRARY="$root/lib64/libcudart.so" CUDAToolkit_ROOT="$root"
            export PATH="$root/bin:$PATH"
            ls -l "$CUDACXX" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY"
            return
        fi
    done
    if [[ -x /usr/bin/nvcc && -f /usr/include/cuda_runtime.h && -f /usr/lib/x86_64-linux-gnu/libcudart.so ]]; then
        export CUDACXX=/usr/bin/nvcc CUDA_INCLUDE_DIR=/usr/include CUDA_LIBRARY=/usr/lib/x86_64-linux-gnu/libcudart.so
        ls -l "$CUDACXX" "$CUDA_INCLUDE_DIR/cuda_runtime.h" "$CUDA_LIBRARY"
    else
        echo 'No complete CUDA layout among probe-discovered locations.' >&2; exit 1
    fi
}
select_cuda
export CUDA_VISIBLE_DEVICES="" GPU_COUNT=0
export CC=/usr/bin/gcc CXX=/usr/bin/g++
export OMPI_ALLOW_RUN_AS_ROOT=1 OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
export PINDER_DATA_DIR=./data PINDER_RELEASE=2024-02
export PYTHONDONTWRITEBYTECODE=1
# Orchestration reproduces predict.py stages verbatim in argv form. Repairs are
# explicit: copy input PDBs, join bin paths, check subprocess status, copy poses
# individually. Published source remains untouched. No search parameter changes.
baseline-published/venv/bin/python -u - <<'PYRUN' 2>&1 | tee -a out/baseline.log
import json,os,shutil,subprocess,tempfile
from pathlib import Path
import biotite.structure.io as strucio
case='7zj1__B1_P55265--7zj1__A1_P55265'
config=json.loads(Path('data/prepared/config.json').read_text())
if config['id']!=case or config['kind']!='apo': raise RuntimeError('Prepared input configuration mismatch')
work=Path(tempfile.mkdtemp(prefix='frodock-',dir='out'))
receptor=Path(config['receptor']).stem
ligand=Path(config['ligand']).stem
for key in ('receptor','ligand'):
    source=Path(config[key]); shutil.copy2(source,work/source.name)
pre=Path(os.path.relpath('baseline-published/frodock/bin',work))
mpi=['mpirun','-np','8','--use-hwthread-cpus']
stages=[
 mpi+[str(pre/'frodockgrid_mpi_gcc'),receptor+'.pdb','-o',receptor+'_W.mrc'],
 mpi+[str(pre/'frodockgrid_mpi_gcc'),receptor+'.pdb','-o',receptor+'_E.mrc','-m','1','-t','A'],
 mpi+[str(pre/'frodockgrid_mpi_gcc'),receptor+'.pdb','-o',receptor+'_DS.mrc','-m','3'],
 mpi+[str(pre/'frodockgrid_mpi_gcc'),ligand+'.pdb','-o',ligand+'_DS.mrc','-m','3'],
 mpi+[str(pre/'frodock_mpi_gcc'),receptor+'_ASA.pdb',ligand+'_ASA.pdb','-w',receptor+'_W.mrc','-e',receptor+'_E.mrc','--th','10','-d',receptor+'_DS.mrc,'+ligand+'_DS.mrc','-t','A','-o','dock.dat','-s',str(pre/'soap.bin')],
 [str(pre/'frodockcluster_gcc'),'dock.dat',ligand+'.pdb','--nc','5','-o','clust_dock.dat'],
 [str(pre/'frodockview_gcc'),'clust_dock.dat','-r','1-5'],
 [str(pre/'frodockview_gcc'),'clust_dock.dat','-r','1-5','-p',ligand+'.pdb'],
]
configuration={'case':case,'kind':'apo','force':False,'mpi_np':int(stages[0][2]),
 'n_solutions':int(stages[5][4]),'gpu_count':int(os.environ['GPU_COUNT']),
 'CUDA_VISIBLE_DEVICES':os.environ['CUDA_VISIBLE_DEVICES'],'cwd':str(work),
 'commands':stages,'environment':{k:os.environ[k] for k in (
 'CC','CXX','CUDACXX','CUDA_INCLUDE_DIR','CUDA_LIBRARY','PATH','PINDER_DATA_DIR',
 'PINDER_RELEASE','OMPI_ALLOW_RUN_AS_ROOT','OMPI_ALLOW_RUN_AS_ROOT_CONFIRM')}}
print('CONFIGURATION '+json.dumps(configuration),flush=True)
for argv in stages:
    print('COMMAND '+json.dumps({'cwd':str(work),'argv':argv}),flush=True)
    try:
        subprocess.run(argv,cwd=work,check=True)
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode)
# Published receptor+ligand merge and rank normalization, with all five required.
poses=work/'results'/'frodock'/case/'apo_decoys'
poses.mkdir(parents=True,exist_ok=True)
receptor_array=strucio.load_structure(str(work/(receptor+'.pdb')))
for rank in range(1,6):
    ligand_path=work/(ligand+'_'+str(rank)+'.pdb')
    if not ligand_path.is_file(): raise RuntimeError('Missing generated pose: '+str(ligand_path))
    ligand_array=strucio.load_structure(str(ligand_path))
    strucio.save_structure(str(poses/('model_'+str(rank)+'.pdb')),receptor_array+ligand_array)
result={'configuration':configuration,'results_dir':str(work/'results'),'pose_count':len(list(poses.glob('model_*.pdb')))}
Path('out/latest-results.json').write_text(json.dumps(result))
print('OUTPUT '+json.dumps(result),flush=True)
PYRUN
