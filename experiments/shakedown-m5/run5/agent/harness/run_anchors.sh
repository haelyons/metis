#!/usr/bin/env bash
set -euo pipefail
harness_mode=anchors
if [[ ${EVAL_MODE:-anchors} != anchors ]]; then
  harness_mode=evaluation
fi
exec python3 - "$harness_mode" <<'HARNESS_DRIVER_PY'
import ctypes
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import threading
import time

ROOT = Path.cwd()
BASE = Path(os.environ.get('BASELINE_DIR', ROOT / 'baseline-published')).resolve()
OUT = ROOT / 'out'
SAMPLE = Path('Samples/5_Domain_Specific/MonteCarloMultiGPU')
TIMEOUT = 3600
NUM = r'([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)'
os.environ['CUDA_VISIBLE_DEVICES'] = '0'


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def command(args, log, **kwargs):
    log = Path(log)
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('a') as f:
        subprocess.run(args, stdout=f, stderr=subprocess.STDOUT, check=True, **kwargs)


def synchronize():
    # Retain the primary context of every visible device and synchronize it.
    # The child sample also waits for completion events before printing timing;
    # process exit destroys its contexts before this parent returns.
    cuda = ctypes.CDLL('libcuda.so.1')
    def check(code):
        if code:
            raise RuntimeError('CUDA synchronization failed: ' + str(code))
    check(cuda.cuInit(0))
    count = ctypes.c_int()
    check(cuda.cuDeviceGetCount(ctypes.byref(count)))
    if count.value != 1:
        raise RuntimeError('Expected exactly one visible GPU')
    for i in range(count.value):
        device = ctypes.c_int()
        context = ctypes.c_void_p()
        check(cuda.cuDeviceGet(ctypes.byref(device), i))
        check(cuda.cuDevicePrimaryCtxRetain(ctypes.byref(context), device))
        try:
            check(cuda.cuCtxSetCurrent(context))
            check(cuda.cuCtxSynchronize())
        finally:
            check(cuda.cuDevicePrimaryCtxRelease(device))


def parse(text):
    def number(label):
        matches = re.findall(label + r'\s*[:=]\s*' + NUM, text, re.I)
        if not matches:
            raise RuntimeError('Missing/invalid binary output: ' + label)
        v = float(matches[-1])
        if not math.isfinite(v):
            raise RuntimeError('Nonfinite binary output: ' + label)
        return v
    result = {
        'average_reserve': number(r'Average reserve'),
        'l1_norm': number(r'L1 norm'),
        'total_time_ms': number(r'Total time\s*\(ms\.?\)'),
        'gpu_count': number(r'(?:Number of GPUs|GPU count)'),
        'options': number(r'(?:Total number of options|Option count)'),
        'paths_per_option': number(r'(?:Number of paths|Path count|Paths per option|PathN)'),
    }
    verdicts = re.findall(r'Test (passed|failed!?)', text, re.I)
    if not verdicts:
        raise RuntimeError('Missing sample verdict')
    result['sample_pass'] = int(verdicts[-1].lower() == 'passed')
    if result['total_time_ms'] <= 0 or result['gpu_count'] != 1:
        raise RuntimeError('Invalid timing or GPU configuration output')
    for key in ('options', 'paths_per_option'):
        if result[key] <= 0 or not result[key].is_integer():
            raise RuntimeError('Invalid workload configuration output: ' + key)
    return result


def binary(options=8192, paths=262144):
    if options == 8192 and paths == 262144:
        exe = BASE / 'build-mc/MonteCarloMultiGPU'
        if not exe.is_file():
            raise RuntimeError('Published binary missing; run setup.sh first')
        return exe
    # Only the two scale changes explicitly authorized by EXECUTION.json.
    # patch applies fixed published declarations; no source-derived measurements.
    directory = OUT / 'scale-builds' / f'{options}-{paths}'
    exe = directory / 'build-mc/MonteCarloMultiGPU'
    if exe.is_file():
        return exe.resolve()
    if directory.exists():
        shutil.rmtree(directory)
    shutil.copytree(BASE, directory, ignore=shutil.ignore_patterns('.git', 'build-mc'))
    source = directory / SAMPLE / 'MonteCarloMultiGPU.cpp'
    def change(name, old_values, value, line):
        for declaration in ('const int', 'int'):
            for old in old_values:
                patch = f'--- {source}\n+++ {source}\n@@ -{line} +{line} @@\n-  {declaration} {name} = {old};\n+  {declaration} {name} = {value};\n'
                with (directory / 'scale-patch.log').open('a') as log:
                    p = subprocess.run(['patch', '--batch', '--forward', '--ignore-whitespace', '--no-backup-if-mismatch', str(source)], input=patch, text=True, stdout=log, stderr=subprocess.STDOUT)
                if p.returncode == 0:
                    return
        raise RuntimeError('Published scale patch could not be applied: ' + name)
    if options != 8192:
        change('nOptions', ['8 * 1024'], options, 272)
    if paths != 262144:
        change('PATH_N', ['262144', '1 << 18'], paths, 279)
    command(['/usr/bin/cmake', '-S', str(directory / SAMPLE), '-B', str(directory / 'build-mc'), '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_CUDA_COMPILER=/usr/bin/nvcc'], directory / 'build.log')
    command(['/usr/bin/cmake', '--build', str(directory / 'build-mc'), '--target', 'MonteCarloMultiGPU', '--parallel', '30'], directory / 'build.log')
    return exe.resolve()


def run(exe, directory, profile=False, budget=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    if profile:
        library = ROOT / 'out/setup/libharness_trace.so'
        if not library.is_file():
            raise RuntimeError('CUPTI observer missing; run setup.sh first')
        env.update(CUDA_INJECTION64_PATH=str(library.resolve()), HARNESS_TRACE=str((directory / 'activities.tsv').resolve()))
    synchronize()
    samples = []
    stop = threading.Event()
    # Monitor belongs outside measured workload, with raw values preserved.
    raw = (directory / 'nvidia-smi.csv').open('w') if profile else None
    start = time.perf_counter()
    def sample_gpu():
        while not stop.is_set():
            q = subprocess.run(['nvidia-smi', '--id=0', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'], capture_output=True, text=True)
            elapsed = time.perf_counter() - start
            raw.write(f'{elapsed:.9f},{q.returncode},{q.stdout.strip()},{q.stderr.strip()}\n')
            raw.flush()
            if q.returncode == 0:
                try:
                    util = float(q.stdout.strip())
                    if math.isfinite(util) and 0 <= util <= 100:
                        samples.append({'t': elapsed, 'util': util})
                except ValueError:
                    pass
            stop.wait(0.1)
    thread = threading.Thread(target=sample_gpu) if profile else None
    if thread:
        thread.start()
    status = None
    try:
        with (directory / 'stdout.log').open('w') as log:
            process = subprocess.Popen([str(exe), '--method=streamed', '--scaling=strong'], stdout=log, stderr=subprocess.STDOUT, env=env, start_new_session=True)
            try:
                # Single GPU: wall deadline conservatively enforces GPU-second
                # budget, including host/launch/transfer overhead, never extrapolates.
                deadline = TIMEOUT if budget is None else min(TIMEOUT, budget)
                status = process.wait(timeout=deadline)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                synchronize()
                raise RuntimeError('Baseline exceeded timeout or GPU-second budget')
        synchronize()
        wall = time.perf_counter() - start
    finally:
        stop.set()
        if thread:
            thread.join()
            raw.close()
            if 'wall' in locals():
                samples[:] = [sample for sample in samples if sample['t'] <= wall]
            write(directory / 'gpu_util.json', samples)
    write(directory / 'process.json', {'exit_status': status, 'total_wall_s': wall})
    metrics = parse((directory / 'stdout.log').read_text())
    # The published failure verdict is a valid measured anchor (zero).
    # Other failures, or inconsistent exit/verdict pairs, are execution errors.
    if status != (0 if metrics['sample_pass'] else 1):
        raise RuntimeError('Baseline exit status inconsistent with valid verdict')
    if profile and not samples:
        raise RuntimeError('No valid GPU utilization samples')
    return metrics, wall


def representative():
    state = OUT / 'representative.json'
    if state.exists():
        constants = json.loads(state.read_text())
        return int(constants['options']), int(constants['paths_per_option'])
    options, paths = 8192, 262144
    while True:
        metrics, wall = run(binary(options, paths), OUT / 'scale-probes' / f'{options}-{paths}')
        if metrics['options'] != options or metrics['paths_per_option'] != paths:
            raise RuntimeError('Binary printed unexpected workload scale')
        if metrics['total_time_ms'] >= 10000:
            write(state, {'options': options, 'paths_per_option': paths, 'gpu_count': 1, 'total_time_ms': metrics['total_time_ms']})
            return options, paths
        if options == 8192:
            options = 1048576
        else:
            paths *= 2
            if paths > 1073741824:
                raise RuntimeError('Cannot reach representative interval within safe integer path range')


def anchors():
    options, paths = representative()
    metrics, wall = run(binary(options, paths), OUT / 'anchors')
    write(OUT / 'anchors_measured.json', {'mc-bs-reserve': metrics['average_reserve'], 'sample-pass': metrics['sample_pass']})
    write(OUT / 'anchors/metrics.json', metrics)


def profile():
    options, paths = representative()
    directory = OUT / 'profile'
    metrics, total = run(binary(options, paths), directory, profile=True)
    trace = directory / 'activities.tsv'
    if not trace.exists():
        raise RuntimeError('CUDA injection did not produce CUPTI activity records')
    events, origin, finish = [], None, None
    for line in trace.read_text().splitlines():
        kind, a, b, name = line.split('\t', 3)
        a, b = int(a), int(b)
        if kind == 'origin':
            origin = a
        elif kind == 'finish':
            finish = a
        elif b > a:
            events.append((kind, a, b, name))
    if origin is None or finish is None or not any(e[0] == 'compute' for e in events):
        raise RuntimeError('Incomplete CUPTI activity trace')
    # Partition the critical path. Device activity takes precedence over host
    # API spans, which takes precedence over host-only work. Overlap counted once.
    boundaries = {origin, finish}
    intervals = []
    for kind, a, b, name in events:
        a, b = max(a, origin), min(b, finish)
        if b <= a:
            continue
        if kind == 'api':
            if any(s in name for s in ('Malloc', 'Free', 'HostAlloc')):
                label = 'host allocation and release'
            elif any(s in name for s in ('Synchronize', 'Event', 'Stream')):
                label = 'host CUDA event and stream handling'
            else:
                label = 'host CUDA runtime calls'
            group, priority, gpu = 'other', 1, False
        else:
            label = ('kernel ' + name) if kind == 'compute' else ('device ' + name)
            group, priority, gpu = kind, 2, True
        intervals.append((a, b, label, group, priority, gpu))
        boundaries.update((a, b))
    totals = {}
    points = sorted(boundaries)
    for a, b in zip(points, points[1:]):
        active = [e for e in intervals if e[0] <= a and e[1] >= b]
        if active:
            chosen = max(active, key=lambda e: e[4])
            label, kind, gpu = chosen[2], chosen[3], chosen[5]
        else:
            label, kind, gpu = 'host work outside CUDA APIs', 'other', False
        key = (label, kind)
        value = totals.setdefault(key, [0.0, 0.0, gpu])
        seconds = (b-a) * 1e-9
        value[0] += seconds
        if gpu:
            value[1] += seconds
    stages = [{'stage': label, 'kind': kind, 'wall_s': v[0], 'gpu_s': v[1] if v[2] else None} for (label, kind), v in totals.items() if v[0] > 0]
    write(directory / 'stages.json', stages)
    write(directory / 'total_wall_s.json', {'total_wall_s': total})
    write(directory / 'metrics.json', metrics)
    if len(stages) < 3 or sum(s['wall_s'] for s in stages) / total < 0.9:
        raise RuntimeError('Insufficient measured internal stage coverage')
    if any(abs(s['wall_s'] - total) / total <= 0.02 for s in stages):
        raise RuntimeError('Single stage indistinguishable from total process duration')


def evaluation():
    mode = os.environ.get('EVAL_MODE', 'equivalence')
    if mode not in ('equivalence', 'warmup', 'performance', 'curve'):
        raise RuntimeError('Unsupported EVAL_MODE: ' + mode)
    seal = json.loads(Path(os.environ['EVAL_PROTOCOL']).read_text())
    directory = Path(os.environ['EVAL_OUT']).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    scope = seal['timing_scope']
    inputs = json.loads(os.environ['EVAL_INPUTS'])
    seeds = json.loads(os.environ['EVAL_SEEDS'])
    if isinstance(inputs, dict) and 'inputs' in inputs:
        inputs = inputs['inputs']
    if isinstance(inputs, dict):
        inputs = [dict(value, input_id=key) if isinstance(value, dict) else {'input_id': key, 'value': value} for key, value in inputs.items()]
    if not isinstance(inputs, list) or not inputs:
        raise RuntimeError('EVAL_INPUTS must specify a nonempty input list')
    if isinstance(seeds, dict):
        if seeds.get('deterministic') or seeds.get('kind') == 'deterministic':
            seeds = [None]
        else:
            seeds = seeds.get('seeds', seeds.get('values'))
    if seeds is None or seeds == []:
        seeds = [None]
    if not isinstance(seeds, list):
        seeds = [seeds]
    if seal.get('deterministic') or seal.get('seed_policy') == 'deterministic':
        seeds = [None]
    budget_text = os.environ.get('EVAL_COMPUTE_BUDGET', '')
    budget = json.loads(budget_text) if budget_text else None
    remaining = None
    if mode == 'curve':
        if isinstance(budget, dict):
            remaining = budget.get('gpu_seconds', budget.get('gpu_s', budget.get('seconds')))
        else:
            remaining = budget
        if not isinstance(remaining, (int, float)) or not math.isfinite(remaining) or remaining <= 0:
            raise RuntimeError('Curve requires a finite positive GPU-second budget')
    records, elapsed = [], 0.0
    metric_aliases = {
        'mc-bs-reserve': 'average_reserve', 'reserve': 'average_reserve',
        'Average reserve': 'average_reserve', 'sample-pass': 'sample_pass',
        'pass': 'sample_pass', 'verdict': 'sample_pass', 'L1 norm': 'l1_norm',
        'l1': 'l1_norm', 'Total time (ms.)': 'total_time_ms',
        'streamed_ms': 'total_time_ms', 'time_ms': 'total_time_ms',
    }
    # Seeds first, then inputs, exactly as supplied by the sealed interface.
    for seed in seeds:
        if seed is not None and seed != 123:
            raise RuntimeError('Published deterministic sample has fixed seed 123 and no seed CLI')
        for index, item in enumerate(inputs):
            spec = item if isinstance(item, dict) else {'input_id': item}
            sealed_inputs = seal.get('inputs', [])
            if isinstance(sealed_inputs, dict):
                sealed_inputs = [dict(v, input_id=k) if isinstance(v, dict) else {'input_id': k} for k, v in sealed_inputs.items()]
            for candidate in sealed_inputs:
                if isinstance(candidate, dict) and candidate.get('input_id', candidate.get('id')) == spec.get('input_id', spec.get('id')):
                    spec = dict(candidate, **spec)
                    break
            input_id = spec.get('input_id', spec.get('id', spec.get('name')))
            if input_id is None:
                raise RuntimeError('Sealed input lacks input_id')
            configuration = spec.get('configuration', spec.get('parameters', spec.get('config', spec)))
            options = int(configuration.get('options', configuration.get('nOptions', 8192)))
            paths = int(configuration.get('paths_per_option', configuration.get('PATH_N', 262144)))
            if configuration.get('gpu_count', 1) != 1 or configuration.get('method', 'streamed') != 'streamed' or configuration.get('scaling', 'strong') != 'strong':
                raise RuntimeError('Sealed input conflicts with published one-GPU streamed strong configuration')
            if options not in (8192, 1048576) or paths < 262144 or paths % 262144 or (paths // 262144) & ((paths // 262144)-1):
                raise RuntimeError('Sealed scale outside published conditional scale policy')
            exe = binary(options, paths)
            run_dir = directory / 'runs' / f'{len(records):06d}'
            metrics, wall = run(exe, run_dir, budget=remaining)
            if metrics['options'] != options or metrics['paths_per_option'] != paths:
                raise RuntimeError('Sealed configuration differs from printed binary configuration')
            elapsed += wall
            if remaining is not None:
                remaining -= wall
                if remaining < 0:
                    raise RuntimeError('Curve GPU-second budget exceeded including launch/transfer/synchronization overhead')
            measured = dict(metrics)
            for alias, source in metric_aliases.items():
                measured[alias] = metrics[source]
            measured['wall_s'] = wall
            requested = seal.get('metrics', seal.get('metric_names', []))
            if isinstance(requested, dict):
                requested = list(requested)
            for metric in requested:
                key = metric.get('name', metric.get('id')) if isinstance(metric, dict) else metric
                if key not in measured:
                    raise RuntimeError('Published binary does not report sealed metric: ' + str(key))
            records.append({'input_id': input_id, 'seed': None, 'metrics': measured})
    synchronize()
    write(directory / 'evaluation.json', {'records': records, 'timing_scope': scope, 'gpu_count': 1, 'wall_s': elapsed, 'compute_budget': budget})


if __name__ == '__main__':
    try:
        OUT.mkdir(parents=True, exist_ok=True)
        {'anchors': anchors, 'profile': profile, 'evaluation': evaluation}[sys.argv[1]]()
    except Exception as error:
        print('HARNESS FAILURE:', error, file=sys.stderr)
        sys.exit(1)
HARNESS_DRIVER_PY
