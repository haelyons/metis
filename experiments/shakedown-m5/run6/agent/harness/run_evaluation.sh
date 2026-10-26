#!/usr/bin/env bash
set -euo pipefail
: "${EVAL_OUT:?EVAL_OUT is required}"
: "${EVAL_PROTOCOL:?EVAL_PROTOCOL is required}"
mkdir -p "$EVAL_OUT"
export HARNESS_BASELINE=${BASELINE_DIR:-$PWD/baseline-published}
python3 - <<'PY'
import json, math, os, pathlib, re, subprocess, time
out=pathlib.Path(os.environ['EVAL_OUT'])
(out/'evaluation.json').unlink(missing_ok=True)
protocol=json.load(open(os.environ['EVAL_PROTOCOL']))
def specification(name, fallback):
    text=os.environ.get(name,'')
    if not text: return fallback
    try: return json.loads(text)
    except json.JSONDecodeError: return json.load(open(text))
inputs=specification('EVAL_INPUTS',protocol.get('inputs',[{'input_id':'representative'}]))
seeds=specification('EVAL_SEEDS',protocol.get('seeds',[None]))
if isinstance(inputs,dict):
    if 'inputs' in inputs: inputs=inputs['inputs']
    elif 'input_ids' in inputs: inputs=inputs['input_ids']
    else: inputs=[dict(v,input_id=k) if isinstance(v,dict) else {'input_id':k,'value':v} for k,v in inputs.items()]
if isinstance(seeds,dict): seeds=seeds.get('seeds',seeds.get('values',[None]))
if seeds is None: seeds=[None]
if not isinstance(seeds,list): seeds=[seeds]
if not isinstance(inputs,list) or not inputs or not seeds: raise SystemExit('Invalid sealed input/seed specifications')
scope=protocol.get('timing_scope')
if scope is None and isinstance(protocol.get('evaluation'),dict): scope=protocol['evaluation'].get('timing_scope')
if scope is None: raise SystemExit('Sealed timing_scope missing')
mode=os.environ.get('EVAL_MODE','performance')
if mode not in ('equivalence','warmup','performance','curve'): raise SystemExit('Unknown EVAL_MODE')
budget_text=os.environ.get('EVAL_COMPUTE_BUDGET','')
budget=None
if mode=='curve':
    try: budget=float(budget_text)
    except ValueError: raise SystemExit('Curve GPU-second budget missing or invalid')
    if not math.isfinite(budget) or budget<=0: raise SystemExit('Invalid curve budget')
records=[]
wall_total=0.
start=time.monotonic()
# There is no seed CLI in the published deterministic sample. Its one host
# seed is 123; CUDA streams follow the published geometry-dependent formula.
for seed in seeds:
    if isinstance(seed,dict): seed=seed.get('seed',seed.get('value'))
    if seed not in (None,123): raise SystemExit('Unsupported seed: published sample has no seed CLI')
    for index,item in enumerate(inputs):
        if isinstance(item,str): input_id=item; spec={}
        elif isinstance(item,dict):
            input_id=item.get('input_id',item.get('id',item.get('name'))); spec=item
        else: raise SystemExit('Invalid input specification')
        if input_id is None: raise SystemExit('Sealed input_id missing')
        config=spec.get('configuration',spec.get('parameters',spec))
        if not isinstance(config,dict): raise SystemExit('Invalid sealed configuration')
        # Both published anchor and fixed representative cases are built once.
        options=config.get('options',config.get('n_options',1048576))
        if options not in (8192,1048576): raise SystemExit('Unsupported sealed option count')
        for key,expected in [('paths_per_option',262144),('gpu_count',1),('method','streamed'),('scaling','strong')]:
            if key in config and config[key]!=expected: raise SystemExit('Unsupported sealed '+key)
        binary='build-anchor' if options==8192 else 'build-mc'
        logfile=out/f'run-{len(records):04d}.log'
        remaining=1100-(time.monotonic()-start)
        if budget is not None: remaining=min(remaining,budget-wall_total)
        if remaining<=0: raise SystemExit('Evaluation budget exhausted')
        env=os.environ.copy(); env['CUDA_VISIBLE_DEVICES']='0'
        t=time.monotonic()
        try:
            with open(logfile,'w') as log:
                p=subprocess.run([os.environ['HARNESS_BASELINE']+'/'+binary+'/MonteCarloMultiGPU','--method=streamed','--scaling=strong'],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=remaining)
        except subprocess.TimeoutExpired: raise SystemExit('Fixed-scale baseline exceeded invocation/curve budget')
        # The streamed baseline waits for completion events and resets its CUDA
        # devices before exit. Process completion includes launch, transfer,
        # validation and teardown; no GPU work survives this timer. With one
        # GPU, process wall time conservatively bounds consumed GPU seconds.
        wall=time.monotonic()-t; wall_total+=wall
        (out/f'run-{len(records):04d}.exit_status').write_text(str(p.returncode)+'\n')
        s=logfile.read_text()
        def number(pattern):
            m=re.search(pattern,s,re.I)
            if not m: raise SystemExit('Missing baseline output: '+pattern)
            value=float(m[1])
            if not math.isfinite(value): raise SystemExit('Nonfinite baseline output')
            return value
        for pattern,expected in [(r'GPU count\s*:\s*(\d+)',1),(r'Option(?:s)? count\s*:\s*(\d+)',options),(r'Path(?:s)?(?: count| per option)?\s*:\s*(\d+)',262144)]:
            if number(pattern)!=expected: raise SystemExit('Invalid baseline scale')
        reserve=number(r'Average reserve\s*:\s*(\S+)')
        l1=number(r'L1 norm\s*:\s*(\S+)')
        ms=number(r'Total time\s*\(ms\.?\)\s*:\s*(\S+)')
        if ms<=0: raise SystemExit('Invalid baseline timing')
        verdict=re.findall(r'Test (passed|failed!)',s)
        if len(verdict)!=1 or p.returncode not in (0,1) or (p.returncode==0)!=(verdict[0]=='passed'):
            raise SystemExit('Invalid baseline verdict/exit status')
        passed=int(verdict[0]=='passed')
        # Metrics are all derived from this run's output. Aliases retain the
        # published names as well as common machine-readable spellings.
        metrics={'total_time_ms':ms,'streamed_total_time_ms':ms,'time_ms':ms,
                 'average_reserve':reserve,'reserve':reserve,'mc-bs-reserve':reserve,
                 'l1_norm':l1,'sample-pass':passed,'sample_pass':passed,
                 'wall_s':wall,'gpu_count':1,'option_count':options,'paths_per_option':262144}
        records.append({'input_id':input_id,'seed':None,'metrics':metrics})
if budget is not None and wall_total>budget: raise SystemExit('Curve GPU-second budget exceeded')
result={'records':records,'timing_scope':scope,'gpu_count':1,'wall_s':wall_total,'compute_budget':budget}
json.dump(result,open(out/'evaluation.json','w'),allow_nan=False,indent=2)
PY
