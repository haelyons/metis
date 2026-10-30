#!/usr/bin/env bash
set -euo pipefail
mkdir -p "${EVAL_OUT:?EVAL_OUT required}" out
exec > >(tee -a "$EVAL_OUT/evaluation.log") 2>&1
baseline-published/venv/bin/python - <<'PY'
import json, math, os, pathlib, subprocess, time
import pandas as pd
mode=os.environ.get('EVAL_MODE')
if mode not in {'equivalence','warmup','performance','curve'}:
    raise RuntimeError('Unknown evaluation mode')
seal=json.loads(pathlib.Path(os.environ['EVAL_PROTOCOL']).read_text())
inputs=json.loads(os.environ['EVAL_INPUTS'])
seed_protocol=json.loads(os.environ['EVAL_SEEDS'])
ids=inputs.get('ids')
if not isinstance(ids,list) or not ids or any(not isinstance(v,str) for v in ids) or len(set(ids))!=len(ids):
    raise RuntimeError('EVAL_INPUTS.ids must contain unique sealed input identities')
kind=seed_protocol.get('kind')
if kind=='deterministic':
    seeds=[None]
elif kind=='paired_median':
    seeds=seed_protocol.get('seeds')
    if not isinstance(seeds,list) or not seeds or any(type(s) is not int for s in seeds):
        raise RuntimeError('Invalid paired execution seeds')
else:
    raise RuntimeError('Unsupported sealed seed protocol')
scope=seal.get('timing_scope')
if scope is None:
    raise RuntimeError('Seal lacks timing_scope')
# Intake only supplies a deterministic scoring CLI, not a docking/search executable.
if 'search' in json.dumps(scope).lower() or mode=='curve':
    raise RuntimeError('Sealed search/curve protocol cannot run: intake lacks immutable docking executable, published parameters and seed interface. Evaluator cannot substitute for search.')
manifest=json.loads(pathlib.Path('data/manifest.json').read_text())
known=set(manifest['ids'])
if any(identity not in known and identity!='PINDER-S' for identity in ids):
    raise RuntimeError('Sealed input identity has no materialized mapping in published manifest; refusing to treat descriptive input keys as inputs')
output=pathlib.Path(os.environ['EVAL_OUT'])
# Remove stale success report before attempting fresh executions.
(output/'evaluation.json').unlink(missing_ok=True)
records=[]
start=time.monotonic()
for number,seed in enumerate(seeds):
    remaining=1100-(time.monotonic()-start)
    if remaining<=0:
        raise RuntimeError('Evaluation invocation budget exhausted')
    env=os.environ.copy()
    env['EVAL_MODE']='anchors'
    # The scoring binary is deterministic. Seed labels select repeats, not invented search randomness.
    subprocess.run(['bash','harness/run_anchors.sh'],env=env,check=True,timeout=remaining)
    archive=output/f'repeat_{number:03d}'
    archive.mkdir(parents=True,exist_ok=True)
    import shutil
    shutil.copy2('out/pinder_eval.log',archive/'pinder_eval.log')
    shutil.copy2('out/eval_dir/eval_dir_metrics.csv',archive/'metrics.csv')
    shutil.copy2('out/eval_dir/eval_dir_leaderboard.csv',archive/'leaderboard.csv')
    metrics=pd.read_csv(archive/'metrics.csv')
    metrics=metrics[(metrics.monomer_name=='apo') & (metrics.pinder_set=='pinder_s')]
    # Full fixed-scale scoring run covers each sealed case before the next seed.
    for identity in ids:
        rows=metrics if identity=='PINDER-S' else metrics[metrics.id==identity]
        top1=rows[rows['rank']==1]
        best=rows.groupby('id').DockQ.max()
        if top1.empty or best.empty:
            raise RuntimeError(f'Missing evaluator output for {identity}')
        values={key:float(top1[key].median()) for key in ['DockQ','iRMS','Fnat']}
        values.update(rank1_acceptable_fraction=float((top1.DockQ>=0.23).mean()),
                      best5_acceptable_fraction=float((best>=0.23).mean()),
                      best5_DockQ=float(best.median()))
        if not all(math.isfinite(value) for value in values.values()):
            raise RuntimeError('Nonfinite evaluation output')
        records.append({'input_id':identity,'seed':seed,'metrics':values})
# CPU-only scorer: no GPU used and therefore no GPU synchronization required.
result={'records':records,'timing_scope':scope,'gpu_count':0,
        'wall_s':time.monotonic()-start,'compute_budget':None}
(output/'evaluation.json').write_text(json.dumps(result,allow_nan=False,indent=2)+'\n')
PY
