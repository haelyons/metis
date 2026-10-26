#!/usr/bin/env bash
set -euo pipefail
base=${BASELINE_DIR:-$PWD/baseline-published}
source "$base/cuda-env.sh"
ls -l "$CUDA_COMPILER" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIB/libcudart.so"
export CUDA_VISIBLE_DEVICES=0
mkdir -p "${EVAL_OUT:?EVAL_OUT required}"
exec > >(tee "$EVAL_OUT/adapter.log") 2>&1
export BASELINE_DIR="$base"
export CANONICAL_RUN="$(cd "$(dirname "$0")"; pwd)/run_anchors.sh"
python3 - <<'PY'
import json, math, os, pathlib, subprocess, time
out=pathlib.Path(os.environ['EVAL_OUT']); protocol=json.loads(pathlib.Path(os.environ['EVAL_PROTOCOL']).read_text())
def specification(name, default):
    text=os.environ.get(name,'')
    return json.loads(text) if text else default
inputs=specification('EVAL_INPUTS',protocol.get('inputs',[{'input_id':'representative'}]))
seeds=specification('EVAL_SEEDS',protocol.get('seeds',[None]))
if isinstance(inputs,dict):
    if 'inputs' in inputs:inputs=inputs['inputs']
    elif 'input_id' in inputs or 'id' in inputs:inputs=[inputs]
    else:inputs=[dict(v,input_id=k) if isinstance(v,dict) else {'input_id':k,'value':v} for k,v in inputs.items()]
if isinstance(seeds,dict):seeds=seeds.get('values',seeds.get('seeds',[None]))
if seeds is None:seeds=[None]
if not isinstance(seeds,list):seeds=[seeds]
if not inputs or not seeds:raise SystemExit('Empty evaluation input/seed specification')
mode=os.environ.get('EVAL_MODE','equivalence')
if mode not in ('equivalence','warmup','performance','curve'):raise SystemExit('Unknown evaluation mode')
budget_text=os.environ.get('EVAL_COMPUTE_BUDGET','')
budget=float(budget_text) if budget_text else None
if mode=='curve' and (budget is None or not math.isfinite(budget) or budget<=0):raise SystemExit('Curve requires positive GPU-second budget')
scope=protocol.get('timing_scope')
if scope is None:raise SystemExit('Seal lacks timing_scope')
start=time.monotonic();records=[]
for seed in seeds:
    # This published protocol has no seed CLI. Its only host seed is 123.
    if seed not in (None,123):raise SystemExit('Unsupported seed: published generator fixes srand(123)')
    for item in inputs:
        if isinstance(item,str):item={'input_id':item}
        input_id=item.get('input_id',item.get('id',item.get('name')))
        if input_id is None:raise SystemExit('Missing input ID')
        config=item.get('configuration',item.get('parameters',item.get('params',item)))
        options=config.get('options',config.get('nOptions',1048576))
        if options not in (8192,1048576):raise SystemExit('Input requests unsupported fixed option count')
        for key,want in [('paths_per_option',262144),('gpus',1),('gpu_count',1),('method','streamed'),('scaling','strong'),('precision','float')]:
            if key in config and config[key]!=want:raise SystemExit('Unsupported published configuration: '+key)
        elapsed=time.monotonic()-start
        remaining=min(1100.,2350.-elapsed)
        if budget is not None:remaining=min(remaining,budget-elapsed) # One GPU, conservative wall-time bound on GPU seconds.
        if remaining<=0:raise SystemExit('Evaluation compute/time budget exhausted')
        index=len(records);log=out/f'run-{index:04d}.log'
        env=os.environ.copy();env.update(RUN_LOG=str(log),RUN_TIMEOUT=str(remaining),CUDA_VISIBLE_DEVICES='0')
        # Run the canonical adapter for both published scales. Each invocation is fresh.
        args=['bash',os.environ['CANONICAL_RUN']]
        if options==1048576:args+=['--representative']
        before=time.monotonic()
        with (out/f'adapter-{index:04d}.log').open('w') as stream:
            result=subprocess.run(args,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=remaining+15)
        wall=time.monotonic()-before
        if options==8192:
            # Anchor mode preserves its canonical log path.
            import shutil
            src=pathlib.Path('out/anchors.log')
            shutil.copyfile(src,log)
            shutil.copyfile(str(src)+'.metrics.json',str(log)+'.metrics.json')
        if result.returncode:raise SystemExit('Published evaluation run failed; see '+str(log))
        m=json.loads(pathlib.Path(str(log)+'.metrics.json').read_text())
        metrics=dict(m)
        metrics.update({'mc-bs-reserve':m['average_reserve'],'sample-pass':m['sample_pass'],
                        'Total time (ms.)':m['total_time_ms'],'Average reserve':m['average_reserve'],
                        'L1 norm':m['l1_norm'],'runtime_ms':m['total_time_ms'],
                        'total_time_s':m['total_time_ms']/1000.,'wall_s':wall})
        if any(not math.isfinite(v) for v in metrics.values()):raise SystemExit('Nonfinite evaluation measurement')
        records.append({'input_id':input_id,'seed':seed,'metrics':metrics})
        report={'records':records,'timing_scope':scope,'gpu_count':1,'wall_s':time.monotonic()-start,'compute_budget':budget}
        (out/'evaluation.partial.json').write_text(json.dumps(report,allow_nan=False))
report['wall_s']=time.monotonic()-start
if budget is not None and report['wall_s']>budget:raise SystemExit('Curve GPU-second budget exceeded')
(out/'evaluation.json').write_text(json.dumps(report,allow_nan=False))
PY
