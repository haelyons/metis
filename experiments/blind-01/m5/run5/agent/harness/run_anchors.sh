#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p out
bash harness/run_command.sh
# Score newly generated poses through the pinned published evaluation API.
PINDER_DATA_DIR=./data PINDER_RELEASE=2024-02 PYTHONDONTWRITEBYTECODE=1 baseline-published/venv/bin/python -u - <<'PYSCORE' 2>&1 | tee -a out/scoring.log
import json,math,re
from pathlib import Path
import pandas as pd
from pinder.core import get_index
from pinder.eval.dockq.method import get_eval_metrics,MethodMetrics
lines=Path('out/baseline.log').read_text().splitlines()
outputs=[json.loads(line[7:]) for line in lines if line.startswith('OUTPUT ')]
if not outputs: raise RuntimeError('Missing successful baseline OUTPUT')
result=outputs[-1]; cfg=result['configuration']
if cfg['mpi_np']!=8 or cfg['n_solutions']!=5 or cfg['gpu_count']!=0 or cfg['CUDA_VISIBLE_DEVICES']!='':
    raise RuntimeError('Printed workload configuration differs from fixed protocol')
commands=cfg['commands']
if len(commands)!=8 or any(cmd[:4]!=['mpirun','-np','8','--use-hwthread-cpus'] for cmd in commands[:5]):
    raise RuntimeError('Invalid printed MPI commands')
if commands[5][3:5]!=['--nc','5'] or commands[6][-2:]!=['-r','1-5'] or commands[7][2:4]!=['-r','1-5']:
    raise RuntimeError('Invalid printed candidate configuration')
case=cfg['case']; root=Path(result['results_dir'])
if result['pose_count']!=5: raise RuntimeError('Invalid pose output count')
frame=get_eval_metrics({'system':root/'frodock'/case,'method_name':'frodock'},parallel_io=False)
if frame is None or frame.empty: raise RuntimeError('Published evaluator returned no metrics')
frame=MethodMetrics.add_rank_column(frame,r'\d+(?=\D*$)')
frame=frame.drop_duplicates(['model_name']).sort_values('rank')
if set(frame['rank'])!=set(range(1,6)): raise RuntimeError('Missing scored candidates')
for key in ('DockQ','iRMS','LRMS','Fnat'):
    if not all(math.isfinite(float(v)) for v in frame[key]): raise RuntimeError('Invalid measured '+key)
frame.to_csv(root/'frodock_metrics.csv',index=False)
# Keep raw CAPRI and direct DockQ success separate.
top=frame[frame['rank']==1].iloc[0]
metrics={k:float(top[k]) for k in ('DockQ','iRMS','LRMS','Fnat')}
metrics.update(best_DockQ=float(frame.DockQ.max()),evaluated_candidates=float(len(frame)),
               acceptable_pose_count=float((frame.DockQ>=0.23).sum()))
index=get_index(); test=index[index.pinder_s.astype(bool)]
observations={'pinder_s_case_count':float(len(test)),
 'pinder_s_paired_apo_count':float((test.apo_R.astype(bool)&test.apo_L.astype(bool)).sum()),
 'dockq_acceptable_pose':float(frame.DockQ.max())}
print('MEASUREMENTS '+json.dumps({'anchors':observations,'metrics':metrics,'results_dir':str(root)}),flush=True)
PYSCORE
python3 - <<'PYPARSE'
import json,math
from pathlib import Path
lines=Path('out/scoring.log').read_text().splitlines()
rows=[json.loads(x[len('MEASUREMENTS '):]) for x in lines if x.startswith('MEASUREMENTS ')]
if not rows: raise RuntimeError('Missing measurement OUTPUT')
measured=rows[-1]
ids=['pinder_s_case_count', 'pinder_s_paired_apo_count', 'dockq_acceptable_pose']
anchors={key:measured['anchors'][key] for key in ids}
if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in anchors.values()):
    raise RuntimeError('Missing or invalid anchor measurement')
Path('out/anchors_measured.json').write_text(json.dumps(anchors,allow_nan=False)+'\n')
Path('out/metrics_measured.json').write_text(json.dumps(measured['metrics'],allow_nan=False)+'\n')
PYPARSE
