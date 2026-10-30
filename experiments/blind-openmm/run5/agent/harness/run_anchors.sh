#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
python3 - <<'PY'
import json,math,pathlib,re,statistics,subprocess,time
out=pathlib.Path('out')
start=time.monotonic()
# Canonical workload, with exactly its own environment and configuration.
result=subprocess.run(['bash','harness/run_command.sh'])
wall=time.monotonic()-start
if result.returncode:
    raise SystemExit('Published workload failed; see out/baseline.stderr.log (exit %d)'%result.returncode)
lines=(out/'baseline.stdout.log').read_text().splitlines()
layout=json.load(open('baseline-published/cuda-layout.json'))
expected=('HARNESS_CONFIGURATION CUDA_VISIBLE_DEVICES=0 gpu_count=1 working_directory=SI/Benchmarks '
          'command=python3_energyBenchmarks.py modes=single,mixed,double trials_per_precision=10 '
          'steps_per_trial=500000 samples_per_trial=1000 timestep_fs=2 compiler=%s include=%s library=%s'
          %(layout['compiler'],layout['include'],layout['library']))
if not lines or lines[0]!=expected: raise SystemExit('Missing or invalid printed run configuration')
values={p:[] for p in ('single','mixed','double')}
precision=None; trial=None; order=[]
for line in lines[1:]:
    line=line.strip()
    if not line: continue
    m=re.fullmatch(r'Precision:\s+(single|mixed|double)',line)
    if m:
        if trial is not None: raise SystemExit('Trial missing slope')
        precision=m[1]; order.append(precision)
        continue
    m=re.fullmatch(r'trial\s+(\d+)',line)
    if m:
        if precision is None or trial is not None: raise SystemExit('Invalid trial sequence')
        trial=int(m[1])
        if trial!=len(values[precision])+1 or trial>10: raise SystemExit('Invalid trial label')
        continue
    m=re.fullmatch(r'slope:\s+(\S+)\s+kJ/mol/ps',line)
    if m:
        if precision is None or trial is None: raise SystemExit('Slope lacks precision/trial')
        try: slope=float(m[1])
        except ValueError: raise SystemExit('Invalid slope')
        if not math.isfinite(slope): raise SystemExit('Nonfinite slope')
        values[precision].append(slope); trial=None
        continue
    raise SystemExit('Unexpected published output: '+line)
if order!=['single','mixed','double'] or trial is not None or any(len(v)!=10 for v in values.values()):
    raise SystemExit('Incomplete fixed workload output')
summary={p:{'mean':statistics.mean(v),'standard_error':statistics.stdev(v)/math.sqrt(10),'slopes':v} for p,v in values.items()}
# Intake anchors and references, including reference-only items; never substitute paper values.
ids=['dhfr-energy-drift-single','dhfr-energy-drift-mixed','dhfr-energy-drift-double']
measured={i:summary[i.rsplit('-',1)[1]]['mean'] for i in ids}
for name,content in [('anchors_measured.json',measured),('baseline_summary.json',{'precision':summary,'wall_s':wall,'gpu_count':1})]:
    tmp=out/(name+'.tmp'); tmp.write_text(json.dumps(content,indent=2,allow_nan=False)+'\n'); tmp.replace(out/name)
print(json.dumps(measured,allow_nan=False))
PY
