#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
python3 - <<'PY'
import json,math,os,pathlib,shutil,subprocess,time
mode=os.environ.get('EVAL_MODE','equivalence')
if mode not in ('equivalence','warmup','performance','curve'): raise SystemExit('Unsupported EVAL_MODE')
protocol=json.load(open(os.environ['EVAL_PROTOCOL']))
inputs=json.loads(os.environ['EVAL_INPUTS'])
seedspec=json.loads(os.environ['EVAL_SEEDS'])
ids=inputs.get('ids')
if not isinstance(ids,list) or not ids or any(not isinstance(i,str) for i in ids) or len(set(ids))!=len(ids):
    raise SystemExit('EVAL_INPUTS.ids must contain distinct sealed input identities')
if seedspec.get('kind')=='deterministic': seeds=[None]
elif seedspec.get('kind')=='paired_median':
    # Published executable has no explicit seed interface. Do not label generated
    # velocities as a replay of a supplied seed or silently modify the benchmark.
    raise SystemExit('Published benchmark has no explicit seed interface; paired seed replay is unsupported')
else: raise SystemExit('Unsupported sealed seed protocol')
scope=protocol.get('timing_scope')
if scope is None: raise SystemExit('Seal missing timing_scope')
budget_raw=os.environ.get('EVAL_COMPUTE_BUDGET','')
budget=None
if mode=='curve':
    try: budget=float(budget_raw)
    except ValueError: raise SystemExit('Curve requires numeric GPU-second budget')
    if not math.isfinite(budget) or budget<=0: raise SystemExit('Invalid GPU-second budget')
out=pathlib.Path(os.environ['EVAL_OUT']); out.mkdir(parents=True,exist_ok=True)
records=[]; started=time.monotonic()
for seed in seeds:
    for input_id in ids:
        index=len(records)
        logs=out/('run-%04d-%d'%(index,time.time_ns())); logs.mkdir()
        remaining=None if budget is None else budget-(time.monotonic()-started)
        if remaining is not None and remaining<=0: raise SystemExit('Curve GPU-second budget exhausted')
        # One exposed GPU, so process wall seconds bound GPU seconds. Include
        # imports, launch, transfer, synchronized energy reads, process teardown,
        # parsing and merge overhead. No warmup or shortened trajectories.
        proc=subprocess.Popen(['bash','harness/run_anchors.sh'],start_new_session=True,
                              stdout=(logs/'adapter.stdout.log').open('w'),
                              stderr=(logs/'adapter.stderr.log').open('w'))
        try: status=proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            import signal
            os.killpg(proc.pid,signal.SIGKILL)
            proc.wait()
            # CUDA driver releases the terminated process's contexts before
            # subsequent work can be considered complete. No partial curve result.
            raise SystemExit('Full published workload exceeds curve GPU-second budget')
        for name in ('baseline.stdout.log','baseline.stderr.log','baseline_summary.json','anchors_measured.json'):
            path=pathlib.Path('out')/name
            if path.exists(): shutil.copyfile(path,logs/name)
        if status: raise SystemExit('Evaluation workload failed; logs: '+str(logs))
        summary=json.load(open('out/baseline_summary.json'))
        metrics=json.load(open('out/anchors_measured.json'))
        for precision,values in summary['precision'].items():
            metrics[precision+'_mean']=values['mean']
            metrics[precision+'_standard_error']=values['standard_error']
        metrics['wall_s']=summary['wall_s']
        if any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in metrics.values()):
            raise SystemExit('Invalid measured evaluation metric')
        records.append({'input_id':input_id,'seed':seed,'metrics':metrics})
wall=time.monotonic()-started
if budget is not None and wall>budget: raise SystemExit('Curve GPU-second budget exceeded')
result={'records':records,'timing_scope':scope,'gpu_count':1,'wall_s':wall,'compute_budget':budget}
tmp=out/'evaluation.json.tmp'; tmp.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n'); tmp.replace(out/'evaluation.json')
PY
