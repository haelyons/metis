#!/usr/bin/env bash
set -euo pipefail
: "${EVAL_MODE:?Missing EVAL_MODE}"
: "${EVAL_PROTOCOL:?Missing EVAL_PROTOCOL}"
: "${EVAL_INPUTS:?Missing EVAL_INPUTS}"
: "${EVAL_SEEDS:?Missing EVAL_SEEDS}"
: "${EVAL_OUT:?Missing EVAL_OUT}"
mkdir -p "$EVAL_OUT" out/tmp
export PYTHONDONTWRITEBYTECODE=1
python3 - <<'PYEVAL'
import os,json,pathlib,subprocess,time,signal,csv,math,shutil
P=pathlib.Path
mode=os.environ['EVAL_MODE']; assert mode in ['equivalence','warmup','performance','curve']
seal=json.loads(P(os.environ['EVAL_PROTOCOL']).read_text())
inputs=json.loads(os.environ['EVAL_INPUTS']); ids=inputs['ids']; assert isinstance(ids,list) and ids and len(set(ids))==len(ids)
seed_spec=json.loads(os.environ['EVAL_SEEDS'])
if seed_spec['kind']=='deterministic': seeds=[None]
elif seed_spec['kind']=='paired_median':
    seeds=seed_spec['seeds']; assert seeds and all(isinstance(s,int) and not isinstance(s,bool) for s in seeds)
else: raise ValueError('Unsupported seed kind')
manifest=json.loads(P('data/manifest.json').read_text())
cases={c['id']:c for c in manifest['data']['cases']}
assert all(i in cases for i in ids),'Unknown sealed input identity'
scope=seal.get('timing_scope')
assert scope is not None,'Missing sealed timing_scope'
budget=os.environ.get('EVAL_COMPUTE_BUDGET','')
if mode=='curve':
    assert budget, 'Curve requires GPU-second budget'
    budget=float(budget); assert math.isfinite(budget) and budget>=0
else: budget=None
# Published CPU baseline uses zero GPUs, including evaluation. GPU-seconds are zero.
# Full canonical configuration is fixed; integer execution seeds are recorded but
# do not alter deterministic rotational enumeration.
output=P(os.environ['EVAL_OUT']); output.mkdir(parents=True,exist_ok=True)
start=time.monotonic(); deadline=start+1190
records=[]
result={'records':records,'timing_scope':scope,'gpu_count':0,'wall_s':None,'compute_budget':budget}
def save():
    result['wall_s']=time.monotonic()-start
    (output/'evaluation.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
def run(argv,log,limit):
    remaining=deadline-time.monotonic()
    assert remaining>0,'Evaluation invocation budget exhausted'
    with log.open('a') as stream:
        t=time.monotonic()
        p=subprocess.Popen(argv,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        try: rc=p.wait(timeout=min(limit,remaining))
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGKILL); p.wait(); raise RuntimeError('Evaluation process timeout; partial logs retained')
        assert rc==0,'Published execution failed: '+str(argv)
        return t
try:
    for seed_index,seed in enumerate(seeds):
        seed_dir=output/f'seed_{seed_index}'; seed_dir.mkdir(exist_ok=True)
        run(['bash','harness/run_command.sh'],seed_dir/'run_command.log',1190)
        values={i:[] for i in ids}
        # Preserve four serial blocks and fresh children for each sealed input.
        for block in range(1,5):
            for input_id in ids:
                c=cases[input_id]; job=seed_dir/c['system_id'][:4]/f'block_{block}'; job.mkdir(parents=True,exist_ok=True)
                t=run(['bash','harness/run_anchors.sh','--child',input_id,str(job),'score'],job/'child.log',180)
                csv_path=job/'dockq.csv'; assert csv_path.is_file() and csv_path.stat().st_size>0,'Missing evaluation CSV'
                wall=time.monotonic()-t
                rows=list(csv.DictReader(csv_path.open()))
                assert len(rows)==50 and {r['model_name'] for r in rows}=={f'model_{i}' for i in range(1,51)}
                dockq={r['model_name']:float(r['DockQ']) for r in rows}
                assert all(math.isfinite(v) for v in dockq.values())
                values[input_id].append((wall,dockq))
        for input_id in ids:
            samples=values[input_id]; primary=max(v[0] for v in samples)
            metrics={'eval_runtime_s':primary,'wall_s':primary,'DockQ_top1':samples[-1][1]['model_1'],'DockQ_best50':max(samples[-1][1].values())}
            assert all(math.isfinite(v) for v in metrics.values())
            records.append({'input_id':input_id,'seed':seed,'metrics':metrics})
            save()
        # Preserve each seed's fresh docking outputs before next invocation.
        for c in manifest['data']['cases']:
            src=P('out')/c['system_id'][:4]
            shutil.copytree(src,seed_dir/c['system_id'][:4]/'docking',dirs_exist_ok=True)
except BaseException as e:
    result['failure']=str(e); save(); raise
save()
PYEVAL
