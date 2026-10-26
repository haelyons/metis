#!/usr/bin/env bash
set -Eeuo pipefail
mkdir -p out/anchors
exec > >(tee -a out/anchors/driver.log) 2>&1
trap 'echo "anchor run failed at line $LINENO" >&2' ERR
python3 - <<'PY'
import json,math,os,pathlib,re,subprocess,time
root=pathlib.Path.cwd()
scale_path=root/'data/scale.json'
scale=json.loads(scale_path.read_text())
cmake=(root/'data/cmake-command').read_text().strip()
repo=root/'baseline-published'
host='Samples/5_Domain_Specific/MonteCarloMultiGPU/MonteCarloMultiGPU.cpp'
env=dict(os.environ,CUDA_VISIBLE_DEVICES='0')
num=r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?'
def scalar(text,label):
    m=re.search(label+r'\s*[:=]\s*('+num+r')',text,re.I)
    if not m: raise RuntimeError('Missing or invalid output: '+label)
    x=float(m.group(1))
    if not math.isfinite(x): raise RuntimeError('Nonfinite output: '+label)
    return x

def measure(index):
    path=root/f'out/anchors/run-{time.time_ns()}-{index}.log'
    with path.open('w') as f:
        p=subprocess.run([str(repo/'build-mc/MonteCarloMultiGPU'),'--method=streamed','--scaling=strong'],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=3600)
    text=path.read_text()
    print(text,flush=True)
    (path.with_suffix('.status.json')).write_text(json.dumps({'exit_status':p.returncode}))
    # A failed baseline process is an execution failure, never a fabricated score.
    if p.returncode: raise RuntimeError(f'Baseline exited {p.returncode}; see {path}')
    elapsed=scalar(text,r'Total time\s*\(ms\.\)')
    reserve=scalar(text,r'Average reserve')
    l1=scalar(text,r'L1 norm')
    verdicts=re.findall(r'Test (passed|failed!)',text)
    if not verdicts: raise RuntimeError('Missing sample verdict')
    # Configuration is checked exclusively against the program's printed output.
    fields={
      'gpu_count':r'(?:Number of GPUs|GPU_N|GPUs?\s*(?:count)?)',
      'nOptions':r'(?:Number of options|Option count|Options? count|OPT_N)',
      'PATH_N':r'(?:Number of paths|Path count|Paths? count|PATH_N)'}
    for key,pattern in fields.items():
        actual=scalar(text,pattern)
        if actual!=scale[key]: raise RuntimeError(f'Invalid runtime configuration: {key}={actual}, expected {scale[key]}')
    if elapsed<=0 or reserve<0 or l1<0: raise RuntimeError('Invalid numeric output')
    return {'elapsed_ms':elapsed,'mc-bs-reserve':reserve,'sample-pass':int(verdicts[-1]=='passed'),'l1':l1,'log':str(path)}

def change_constant(name,old,new):
    # Apply only intake-authorized scale edits. No source parsing or source-derived
    # measurements; git applies a literal patch to the pinned host declaration.
    before = '8 * 1024' if name=='nOptions' and old==8192 else str(old)
    patch=f'diff --git a/{host} b/{host}\n--- a/{host}\n+++ b/{host}\n@@ -272 +272 @@\n-  int {name} = {before};\n+  int {name} = {new};\n'
    subprocess.run(['/usr/bin/git','apply','--unidiff-zero','--ignore-whitespace','-'],cwd=repo,input=patch,text=True,check=True)
    with (root/f'out/anchors/build-{time.time_ns()}.log').open('w') as f:
        subprocess.run([cmake,'--build',str(repo/'build-mc'),'--target','MonteCarloMultiGPU','--parallel'],stdout=f,stderr=subprocess.STDOUT,check=True)
    scale[name]=new
    scale_path.write_text(json.dumps(scale,indent=2)+'\n')

index=0
while True:
    result=measure(index)
    if result['elapsed_ms']>=10000: break
    if scale['nOptions']==8192:
        change_constant('nOptions',8192,1048576)
    else:
        old=scale['PATH_N']
        if old*2>2147483647: raise RuntimeError('PATH_N escalation exceeds published signed integer range')
        change_constant('PATH_N',old,old*2)
    index+=1
(root/'out/anchors_measured.json').write_text(json.dumps({k:result[k] for k in ('mc-bs-reserve','sample-pass')},allow_nan=False,indent=2)+'\n')
(root/'out/anchors/final-run.json').write_text(json.dumps(dict(result,configuration=scale),allow_nan=False,indent=2)+'\n')
subprocess.run(['/usr/bin/git','diff','--',host],cwd=repo,stdout=(root/'out/anchors/scale.patch').open('w'),check=True)
PY
