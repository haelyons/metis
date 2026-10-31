import argparse, json, math, os, shutil, subprocess, time
from pathlib import Path
import pandas as pd
import biotite.structure.io as strucio
p=argparse.ArgumentParser()
p.add_argument('--cases',required=True)
p.add_argument('--out',required=True)
p.add_argument('--mpi-np',type=int,required=True)
p.add_argument('--n-solutions',type=int,required=True)
p.add_argument('--gpu-count',type=int,required=True)
p.add_argument('--input-id')
a=p.parse_args()
if (a.mpi_np,a.n_solutions,a.gpu_count)!=(8,100,0) or os.environ.get('CUDA_VISIBLE_DEVICES')!='':
    raise ValueError('Published configuration mismatch')
root=Path.cwd()
cases=json.loads(Path(a.cases).read_text())
if len(cases)!=93: raise ValueError('Missing fixed cases')
if a.input_id and a.input_id in {x['id'] for x in cases}:
    cases=[x for x in cases if x['id']==a.input_id]
out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
run=out / ('run-'+str(time.time_ns())); run.mkdir()
print('CONFIG '+json.dumps({'mpi_np':a.mpi_np,'n_solutions':a.n_solutions,'gpu_count':a.gpu_count,'CUDA_VISIBLE_DEVICES':os.environ['CUDA_VISIBLE_DEVICES'],'cases':len(cases),'cwd':str(root),'OMP_NUM_THREADS':os.environ.get('OMP_NUM_THREADS')}),flush=True)
bindir=root/'baseline-published/frodock3_linux64/bin'
mpi=['/usr/bin/mpirun','-np',str(a.mpi_np),'--use-hwthread-cpus']
all_metrics=[]; total_wall=0.0
for case in cases:
    cid=case['id']; work=run/'scratch'/cid; work.mkdir(parents=True)
    dst=run/'results/frodock'/cid/'apo_decoys'; dst.mkdir(parents=True)
    start=time.perf_counter()
    shutil.copyfile(case['receptor'],work/'receptor.pdb')
    shutil.copyfile(case['ligand'],work/'ligand.pdb')
    grid=mpi+[str(bindir/'frodockgrid_mpi_gcc')]
    commands=[
      grid+['receptor.pdb','-o','receptor_W.mrc'],
      grid+['receptor.pdb','-o','receptor_E.mrc','-m','1','-t','A'],
      grid+['receptor.pdb','-o','receptor_DS.mrc','-m','3'],
      grid+['ligand.pdb','-o','ligand_DS.mrc','-m','3'],
      mpi+[str(bindir/'frodock_mpi_gcc'),'receptor_ASA.pdb','ligand_ASA.pdb','-w','receptor_W.mrc','-e','receptor_E.mrc','--th','10','-d','receptor_DS.mrc,ligand_DS.mrc','-t','A','-o','dock.dat','-s',str(bindir/'soap.bin')],
      [str(bindir/'frodockcluster_gcc'),'dock.dat','ligand.pdb','--nc',str(a.n_solutions),'-o','clust_dock.dat'],
      [str(bindir/'frodockview_gcc'),'clust_dock.dat','-r',f'1-{a.n_solutions}'],
      [str(bindir/'frodockview_gcc'),'clust_dock.dat','-r',f'1-{a.n_solutions}','-p','ligand.pdb']]
    for command in commands:
        print('COMMAND '+json.dumps(command),flush=True)
        subprocess.run(command,cwd=work,check=True)
    receptor=strucio.load_structure(str(work/'receptor.pdb'))
    for i in range(1,a.n_solutions+1):
        ligand=strucio.load_structure(str(work/f'ligand_{i}.pdb'))
        strucio.save_structure(str(dst/f'model_{i}.pdb'),receptor+ligand)
    # CPU/MPI processes have exited; no GPU work was launched.
    elapsed=time.perf_counter()-start; total_wall+=elapsed
    print('CASE_WALL '+json.dumps({'id':cid,'wall_s':elapsed}),flush=True)
# Invoke the published evaluator API, avoiding its interactive CLI confirmation.
from pinder.eval.dockq.method import MethodMetrics
mm=MethodMetrics(run/'results',parallel=True,allow_missing_systems=True,max_workers=8)
metrics=mm.metrics
metrics.to_csv(run/'frodock_metrics.csv',index=False)
mm.get_leaderboard_entry().to_csv(run/'frodock_leaderboard.csv',index=False)
selected=metrics[metrics.id.isin([c['id'] for c in cases]) & (metrics.monomer_name=='apo')].drop_duplicates(['id','rank'])
if len(selected)!=len(cases)*a.n_solutions: raise ValueError('Missing measured poses')
cols=['DockQ','iRMS','LRMS','Fnat']
if not all(math.isfinite(float(v)) for col in cols for v in selected[col]): raise ValueError('Invalid measured metric')
top=selected[selected['rank']==1].sort_values('id')
best=selected.groupby('id').DockQ.max()
counts=json.loads(Path('data/counts.json').read_text())
summary={'wall_s':total_wall,'gpu_count':0,'case_count':len(cases),'pose_count':len(selected),
 'DockQ':float(top.DockQ.mean()),'top1_DockQ':float(top.DockQ.mean()),'best100_DockQ':float(best.mean()),
 'iRMSD':float(top.iRMS.mean()),'LRMSD':float(top.LRMS.mean()),'fnat':float(top.Fnat.mean()),
 'acceptable_fraction':float((best>=0.23).sum()/len(cases)),
 'poses_per_s':len(selected)/total_wall,
 'anchors':dict(counts,**{'dockq-acceptable':float(top.iloc[0].DockQ)}),
 'run_dir':str(run)}
print('MEASUREMENT '+json.dumps(summary,allow_nan=False),flush=True)
