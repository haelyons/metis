#!/usr/bin/env bash
set -euo pipefail
if [[ -n "${EVAL_MODE:-}" && "${EVAL_MODE}" != anchors ]]; then
    exec bash harness/run_evaluation.sh
fi
mkdir -p out
exec > >(tee -a out/anchors.log) 2>&1
bash harness/run_command.sh
source baseline-published/cuda.env
ls -l "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIB/libcudart.so"
export LC_ALL=C LANG=C
export OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
baseline-published/venv/bin/python - <<'PY'
import json, math, pathlib, re
from pinder.eval.dockq import BiotiteDockQ
manifest=json.loads(pathlib.Path('baseline-published/intake.json').read_text())
run=pathlib.Path('out/latest-run').resolve()
summary={}; measurements={}; grids={}
for config in ['cpu_standard','gpu_standard','gpu_dense']:
    for case in manifest['data']['cases']:
        job=run/config/case['system_id']; log=(job/'docking.log').read_text()
        def require(pattern):
            match=re.search(pattern,log)
            if not match: raise RuntimeError('Missing/invalid printed configuration '+pattern+' in '+str(job))
            return match
        require(r'Using\s+26 CPU cores, '+('0' if config=='cpu_standard' else '1')+r' GPUs')
        require(r'Using OpenMP parallelization:\s+26 threads')
        require(r'Number of output = 50\b')
        require(r'Set number of scores per one angle = 1\b')
        require(r'Set voxel size\s*= 1\.2\b')
        require(r'Set electric term ratio = 1\b')
        require(r'Set ACE term ratio = 1\b')
        require(r'Set score Function = 3\b')
        if config=='gpu_dense': require(r'Set 54,000 rotational angles')
        elif 'Set 54,000 rotational angles' in log: raise RuntimeError('Unexpected dense sampling')
        elapsed=float(require(r'Elapsed time\s*=\s*([0-9.eE+-]+) sec').group(1))
        if not math.isfinite(elapsed) or elapsed<0: raise RuntimeError('Invalid elapsed time')
        lines=(job/'docking.out').read_text().strip().splitlines()
        if len(lines)!=54: raise RuntimeError('Expected four header lines and 50 predictions')
        grid,spacing=lines[0].split()
        if int(grid)<=0 or not math.isclose(float(spacing),1.2,abs_tol=1e-6): raise RuntimeError('Invalid output grid/spacing')
        ranked=[[float(v) for v in line.split()] for line in lines[4:]]
        if any(len(row)!=7 or not all(math.isfinite(v) for v in row) for row in ranked): raise RuntimeError('Invalid transform/score output')
        if config=='cpu_standard': grids[case['id']]=int(grid)
        elif grids[case['id']]!=int(grid): raise RuntimeError('CPU/GPU FFT configuration differs')
        poses=[job/'apo_decoys'/f'model_{rank}.pdb' for rank in range(1,51)]
        for pose in poses:
            chains={line[21] for line in pose.read_text().splitlines() if line.startswith(('ATOM  ','HETATM'))}
            if chains!={'R','L'}: raise RuntimeError('Invalid decoy chain identities: '+str(pose))
        df=BiotiteDockQ(native=pathlib.Path('data/2024-02')/case['reference'],decoys=poses,
                       native_receptor_chain=['R'],native_ligand_chain=['L'],
                       decoy_receptor_chain=['R'],decoy_ligand_chain=['L'],parallel_io=False).calculate()
        if len(df)!=50 or set(df.model_name)!={f'model_{i}' for i in range(1,51)}: raise RuntimeError('Missing scored pose')
        values=[float(x) for x in df.DockQ]
        if not all(math.isfinite(v) for v in values): raise RuntimeError('Invalid DockQ output')
        df.to_csv(job/'dockq.csv',index=False)
        metrics={'dockq_rank1':float(df.loc[df.model_name=='model_1','DockQ'].iloc[0]),
                 'dockq_best50':max(values),'docking_elapsed_s':elapsed,
                 'rank1_score':ranked[0][-1]}
        summary.setdefault(case['id'],{})[config]=metrics
        for name,value in metrics.items(): measurements[f"{case['id']}/{config}/{name}"]=value
        print(case['id'],config,json.dumps(metrics))
# Preserve paired scientific outcomes separately; no invented acceptance threshold.
for item,configs in summary.items():
    configs['dense_minus_standard']={name:configs['gpu_dense'][name]-configs['gpu_standard'][name]
                                    for name in ['dockq_rank1','dockq_best50']}
    cpu=run/'cpu_standard'/item.split(':')[0]/'docking.out'
    gpu=run/'gpu_standard'/item.split(':')[0]/'docking.out'
    a=[[float(x) for x in line.split()] for line in cpu.read_text().splitlines()[4:]]
    b=[[float(x) for x in line.split()] for line in gpu.read_text().splitlines()[4:]]
    configs['agreement']={'ranked_score_max_abs_delta':max(abs(x[-1]-y[-1]) for x,y in zip(a,b)),
                         'ranked_transform_max_abs_delta':max(abs(x[i]-y[i]) for x,y in zip(a,b) for i in range(6)),
                         'acceptance_tolerance':None}
(run/'protocol_limitations.json').write_text(json.dumps(manifest['EXECUTION']['limitations'],indent=2)+'\n')
(run/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
# Intake has zero scalar items. Still validate actual outputs above before writing {}.
items=manifest['anchors']
if isinstance(items,dict): items=items.get('anchors',[])+items.get('references',[])
measured={}
for item in items:
    key=item.get('id',item.get('item_id'))
    if key not in measurements: raise RuntimeError('No actual output mapping for intake item '+str(key))
    measured[key]=measurements[key]
pathlib.Path('out/anchors_measured.json').write_text(json.dumps(measured,allow_nan=False)+'\n')
PY
