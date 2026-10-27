#!/usr/bin/env bash
set -euo pipefail
# This is also the sealed evaluation adapter for non-anchor EVAL_MODE.
mkdir -p out
source baseline-published/harness-environment.sh
ls -l "$HARNESS_CUDA_COMPILER" "$HARNESS_CUDA_INCLUDE/cuda_runtime.h" "$HARNESS_CUDA_LIBRARY"
python3 - <<'PY'
import ctypes, json, math, os, pathlib, re, signal, subprocess, time

root = pathlib.Path.cwd()
out = root / 'out'
mode = os.environ.get('EVAL_MODE', 'anchors') or 'anchors'
start = time.monotonic()

def synchronize():
    # CUDA_VISIBLE_DEVICES=0 is pinned by the canonical command environment.
    cuda = ctypes.CDLL(os.environ['HARNESS_CUDA_LIBRARY'])
    count = ctypes.c_int()
    if cuda.cudaGetDeviceCount(ctypes.byref(count)) != 0 or count.value != 1:
        raise RuntimeError('Expected exactly one visible CUDA device')
    if cuda.cudaSetDevice(0) != 0 or cuda.cudaDeviceSynchronize() != 0:
        raise RuntimeError('CUDA synchronization failed')

def extract(text):
    def number(pattern, label):
        found = re.findall(pattern, text, re.I | re.M)
        if len(found) != 1:
            raise ValueError('Missing or ambiguous output: ' + label)
        value = float(found[0])
        if not math.isfinite(value):
            raise ValueError('Nonfinite output: ' + label)
        return value
    numeric = r'([-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)'
    # These are binary output checks, never source checks.
    # Match the configuration summary, not the repeated per-device statistics.
    gpu = number(r'^[ \t]*Number of GPUs[ \t]*=[ \t]*(\d+)[ \t]*$', 'GPU count')
    options = number(r'^[ \t]*Total number of options[ \t]*=[ \t]*(\d+)[ \t]*$', 'option count')
    paths = number(r'^[ \t]*Number of paths[ \t]*=[ \t]*(\d+)[ \t]*$', 'path count')
    if (gpu, options, paths) != (1, 1048576, 262144):
        raise ValueError(f'Printed configuration differs from command: {gpu}, {options}, {paths}')
    for label, expected in (('Parallelization method', 'streamed'), ('Problem scaling', 'strong')):
        values = re.findall(r'^[ \t]*' + label + r'[ \t]*=[ \t]*(\S+)[ \t]*$', text, re.I | re.M)
        if values != [expected]:
            raise ValueError('Missing, ambiguous or invalid printed configuration: ' + label)
    for label, expected in (('Options', options), ('Simulation paths', paths)):
        values = re.findall(r'^[ \t]*' + label + r'[ \t]*:[ \t]*(\d+)[ \t]*$', text, re.I | re.M)
        if any(int(value) != expected for value in values):
            raise ValueError('Inconsistent per-device configuration: ' + label)
    reserve = number(r'^[ \t]*Average reserve[ \t]*:[ \t]*' + numeric + r'[ \t]*$', 'Average reserve')
    l1 = number(r'^[ \t]*L1 norm[ \t]*:[ \t]*' + numeric + r'[ \t]*$', 'L1 norm')
    ms = number(r'^[ \t]*Total time[ \t]*\(ms\.?\)[ \t]*:[ \t]*' + numeric + r'[ \t]*$', 'Total time (ms.)')
    if reserve < 0 or l1 < 0 or ms <= 0:
        raise ValueError('Invalid numerical output')
    verdicts = re.findall(r'^[ \t]*Test (passed|failed!)[ \t]*$', text, re.M)
    if len(verdicts) != 1:
        raise ValueError('Missing or ambiguous final verdict')
    passed = int(verdicts[0] == 'passed')
    return {'mc-bs-reserve': reserve, 'sample-pass': passed,
            'average_reserve': reserve, 'sample_pass': passed,
            'l1_norm': l1, 'total_time_ms': ms}

def run(timeout):
    if timeout <= 0:
        raise TimeoutError('Stage or GPU-seconds budget exhausted')
    # No environment overrides and no copy of the workload command.
    process = subprocess.Popen(['bash', 'harness/run_command.sh'], cwd=root, start_new_session=True)
    try:
        status = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass
        # Kill the entire pipeline, including the workload and tee.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
        synchronize()
        raise TimeoutError('Published workload exceeded fixed budget; logs preserved')
    synchronize()
    text = (out / 'baseline.stdout.log').read_text()
    metrics = extract(text)
    # The pipeline scores the verdict; a failed verdict is still a measurement.
    metrics['exit_status'] = status
    return metrics

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temp.replace(path)

if mode == 'anchors':
    measured = run(1150)
    write(out / 'anchors_measured.json', {k: measured[k] for k in ('mc-bs-reserve','sample-pass')})
else:
    if mode not in ('equivalence','warmup','performance','curve'):
        raise ValueError('Unsupported EVAL_MODE: ' + mode)
    protocol = json.loads(pathlib.Path(os.environ['EVAL_PROTOCOL']).read_text())
    def spec(name, default):
        raw = os.environ.get(name, '')
        return json.loads(raw) if raw else default
    inputs = spec('EVAL_INPUTS', protocol.get('inputs', [{'input_id':'representative'}]))
    if isinstance(inputs, dict):
        inputs = inputs.get('inputs', [{'input_id':k, **(v if isinstance(v,dict) else {})} for k,v in inputs.items()])
    if not isinstance(inputs, list) or not inputs:
        raise ValueError('Empty or invalid sealed inputs')
    seeds = spec('EVAL_SEEDS', protocol.get('seeds', [None]))
    if isinstance(seeds, dict):
        seeds = seeds.get('seeds', [None] if seeds.get('deterministic') else None)
    if seeds is None or seeds == []:
        seeds = [None]
    if not isinstance(seeds, list):
        raise ValueError('Invalid seed specification')
    # Published program has a fixed host seed and no seed CLI.
    if any(s not in (None, 123) for s in seeds):
        raise ValueError('Published deterministic generator supports only fixed seed 123')
    timing_scope = protocol['timing_scope']
    budget_raw = os.environ.get('EVAL_COMPUTE_BUDGET', '')
    budget = float(budget_raw) if budget_raw else None
    if mode == 'curve' and (budget is None or not math.isfinite(budget) or budget <= 0):
        raise ValueError('Curve requires positive finite GPU-seconds budget')
    records = []
    for seed in seeds:
        for item in inputs:
            item = {'input_id':item} if not isinstance(item,dict) else item
            input_id = item.get('input_id', item.get('id'))
            if input_id is None:
                raise ValueError('Sealed input lacks input_id')
            configuration = item.get('configuration', item.get('parameters', item))
            expected = {'options':1048576, 'paths_per_option':262144, 'gpus':1,
                        'method':'streamed', 'scaling':'strong', 'precision':'float'}
            for key,value in expected.items():
                if key in configuration and configuration[key] != value:
                    raise ValueError('Sealed input changes published fixed configuration: ' + key)
            elapsed = time.monotonic() - start
            remaining = min(1150-elapsed, budget-elapsed if budget is not None else 1150)
            metrics = run(remaining)
            # Fixed seeds are deterministic; records use null as required by this protocol.
            records.append({'input_id':input_id,'seed':None,'metrics':metrics})
    synchronize()
    wall = time.monotonic() - start
    if budget is not None and wall > budget:
        raise TimeoutError('Curve GPU-seconds budget exceeded')
    write(pathlib.Path(os.environ['EVAL_OUT']) / 'evaluation.json',
          {'records':records,'timing_scope':timing_scope,'gpu_count':1,
           'wall_s':wall,'compute_budget':budget})
PY
