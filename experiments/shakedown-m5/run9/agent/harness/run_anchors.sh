#!/usr/bin/env bash
set -Eeuo pipefail
if [[ ${MC_RUN_BUDGET:-0} != 1 ]]; then
  exec env MC_RUN_BUDGET=1 timeout --signal=TERM --kill-after=10s 1180s bash "$0" "$@"
fi
root=$PWD
baseline=${BASELINE_DIR:-$root/baseline-published}
[[ -d $baseline/build-mc ]] || { echo "Missing baseline build: $baseline" >&2; exit 1; }
mkdir -p "$root/out"
exec > >(tee -a "$root/out/run_anchors.log") 2>&1
source "$baseline/.harness_cuda.env"
ls -l "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIB/libcudart.so"
export PATH="$(dirname "$CUDA_NVCC"):$PATH"
export LD_LIBRARY_PATH="$CUDA_LIB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export CUDA_VISIBLE_DEVICES=0
# The exact representative command is shared by profiling and evaluation:
# CUDA_VISIBLE_DEVICES=0 ./build-mc/MonteCarloMultiGPU --method=streamed --scaling=strong
cat > "$root/out/mc_output.py" <<'PY'
import json, math, pathlib, re, sys

def parse(path, options, status):
    text = pathlib.Path(path).read_text(errors='replace')
    def number(label):
        matches = re.findall(r'^\s*' + label + r'\s*[:=]\s*([-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)\s*$', text, re.I | re.M)
        if len(matches) != 1:
            raise RuntimeError('Missing, invalid or ambiguous output field: ' + label)
        v = float(matches[0])
        if not math.isfinite(v):
            raise RuntimeError('Nonfinite output field: ' + label)
        return v
    for label, expected in [(r'Number of GPUs', 1), (r'Total number of options', options), (r'Number of paths', 262144)]:
        if number(label) != expected:
            raise RuntimeError('Printed configuration differs from command/environment: '+label)
    for label, expected in [('Parallelization method', 'streamed'), ('Problem scaling', 'strong')]:
        values = re.findall(r'^\s*' + label + r'\s*=\s*(\S+)\s*$', text, re.M)
        if values != [expected]:
            raise RuntimeError('Printed configuration differs from command/environment: '+label)
    reserve = number(r'Average reserve')
    l1 = number(r'L1 norm')
    ms = number(r'Total time\s*\(ms\.\)')
    if ms <= 0 or reserve < 0 or l1 < 0:
        raise RuntimeError('Invalid measured output')
    verdict = re.findall(r'Test (passed|failed!)', text)
    if len(verdict) != 1:
        raise RuntimeError('Missing or ambiguous sample verdict')
    passed = int(verdict[0] == 'passed')
    if (status == 0) != bool(passed):
        raise RuntimeError('Exit status disagrees with printed verdict')
    # The verdict retains the strict predicate at the six-decimal boundary.
    if reserve == 1.0:
        reserve = math.nextafter(reserve, math.inf if passed else -math.inf)
    return {'mc-bs-reserve':reserve,'sample-pass':passed,'average_reserve':reserve,
            'l1_norm':l1,'total_time_ms':ms,'time_s':ms/1000,'exit_status':status}

if __name__ == '__main__':
    result = parse(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]))
    pathlib.Path(sys.argv[4]).write_text(json.dumps(result, allow_nan=False)+'\n')
PY
if [[ -n ${EVAL_MODE:-} && ${EVAL_MODE} != anchors && ${EVAL_MODE} != anchor ]]; then
  export MC_BASELINE="$baseline" MC_ROOT="$root"
  python3 - <<'PY'
import ctypes, importlib.util, json, math, os, pathlib, subprocess, time
root=pathlib.Path(os.environ['MC_ROOT'])
base=pathlib.Path(os.environ['MC_BASELINE']).resolve()
spec=importlib.util.spec_from_file_location('mc_output', root/'out/mc_output.py')
parser=importlib.util.module_from_spec(spec); spec.loader.exec_module(parser)
protocol=json.loads(pathlib.Path(os.environ['EVAL_PROTOCOL']).read_text())
inputs=json.loads(os.environ['EVAL_INPUTS'])
seeds=json.loads(os.environ['EVAL_SEEDS'])
mode=os.environ['EVAL_MODE']
if mode not in ('equivalence','warmup','performance','curve'):
    raise RuntimeError('Unsupported evaluation mode: '+mode)
if isinstance(inputs,dict):
    inputs=inputs.get('inputs',inputs)
    if isinstance(inputs,dict): inputs=[dict(v,input_id=k) if isinstance(v,dict) else {'input_id':k,'value':v} for k,v in inputs.items()]
if not isinstance(inputs,list) or not inputs: raise RuntimeError('EVAL_INPUTS must specify at least one input')
if isinstance(seeds,dict): seeds=seeds.get('seeds',[None] if seeds.get('deterministic') else [])
if seeds is None or seeds==[]: seeds=[None]
if not isinstance(seeds,list): raise RuntimeError('Invalid seed specification')
# Published protocol is deterministic and exposes no seed argument.
if any(seed not in (None,123) for seed in seeds): raise RuntimeError('Published sample supports only fixed seed 123')
seeds=[None]
inputs=sorted(inputs,key=lambda x:str(x.get('input_id',x.get('id','')) if isinstance(x,dict) else x))
out=pathlib.Path(os.environ['EVAL_OUT']); out.mkdir(parents=True,exist_ok=True)
scope=protocol.get('timing_scope')
if scope is None: raise RuntimeError('Sealed timing_scope is required')
budget_text=os.environ.get('EVAL_COMPUTE_BUDGET','')
budget=float(budget_text) if budget_text else None
if mode=='curve' and (budget is None or not math.isfinite(budget) or budget<=0): raise RuntimeError('Curve requires positive GPU-second budget')
# CUDA_VISIBLE_DEVICES=0 means synchronizing this context synchronizes the one used device.
# The child exits after its event wait and device cleanup; synchronization also brackets reporting.
cuda=ctypes.CDLL(os.environ['CUDA_LIB']+'/libcudart.so')
def sync():
    if cuda.cudaSetDevice(0)!=0 or cuda.cudaDeviceSynchronize()!=0: raise RuntimeError('GPU synchronization failed')
records=[]; elapsed=0.0; started=time.monotonic()
for seed in seeds:
    for item in inputs:
        item=item if isinstance(item,dict) else {'input_id':item}
        ident=item.get('input_id',item.get('id'))
        if ident is None: raise RuntimeError('Missing sealed input ID')
        conf=item.get('configuration',item.get('parameters',item))
        for key,expected in [('options',1048576),('paths_per_option',262144),('gpus',1)]:
            if key in conf and conf[key]!=expected: raise RuntimeError('Unsupported sealed configuration: '+key)
        index=len(records); log=out/f'run-{index:04d}.log'
        sync(); begin=time.monotonic()
        remaining=1140-(begin-started)
        if budget is not None: remaining=min(remaining,budget-elapsed)
        if remaining<=0: raise RuntimeError('Evaluation GPU-second budget exhausted')
        with log.open('w') as stream:
            run=subprocess.Popen(['./build-mc/MonteCarloMultiGPU','--method=streamed','--scaling=strong'],cwd=base,stdout=stream,stderr=subprocess.STDOUT)
            try: status=run.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                run.kill(); run.wait(); sync()
                raise RuntimeError('Fixed-scale run timed out; scale is never reduced')
        sync(); wall=time.monotonic()-begin; elapsed+=wall
        measured=parser.parse(log,1048576,status)
        measured['wall_s']=wall
        records.append({'input_id':ident,'seed':None,'metrics':measured})
if budget is not None and elapsed>budget: raise RuntimeError('Curve GPU-second budget exceeded')
result={'records':records,'timing_scope':scope,'gpu_count':1,'wall_s':elapsed,'compute_budget':budget}
(out/'evaluation.json').write_text(json.dumps(result,allow_nan=False)+'\n')
PY
else
  cd "$baseline"
  set +e
  CUDA_VISIBLE_DEVICES=0 ./build-anchor/MonteCarloMultiGPU --method=streamed --scaling=strong > "$root/out/anchor-output.log" 2>&1
  status=$?
  set -e
  cat "$root/out/anchor-output.log"
  python3 "$root/out/mc_output.py" "$root/out/anchor-output.log" 8192 "$status" "$root/out/anchor-statistics.json"
  python3 - "$root/out" <<'PY'
import json,pathlib,sys
out=pathlib.Path(sys.argv[1]); m=json.loads((out/'anchor-statistics.json').read_text())
(out/'anchors_measured.json').write_text(json.dumps({k:m[k] for k in ('mc-bs-reserve','sample-pass')},allow_nan=False)+'\n')
PY
  set +e
  CUDA_VISIBLE_DEVICES=0 ./build-mc/MonteCarloMultiGPU --method=streamed --scaling=strong > "$root/out/representative-output.log" 2>&1
  status=$?
  set -e
  cat "$root/out/representative-output.log"
  python3 "$root/out/mc_output.py" "$root/out/representative-output.log" 1048576 "$status" "$root/out/representative_measured.json"
fi
