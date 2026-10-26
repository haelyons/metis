#!/usr/bin/env bash
set -euo pipefail
mkdir -p out/anchors
log="out/anchors/driver-$(date -u +%Y%m%dT%H%M%S)-$$.log"
exec > >(tee -a "$log") 2>&1
python3 - anchors <<'PY'

import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

PIN = 'db3eea23946bca2e90a75eca2b5b3e07158a9e11'
SAMPLE = Path('Samples/5_Domain_Specific/MonteCarloMultiGPU')
ROOT = Path.cwd()
PUBLISHED = ROOT / 'baseline-published'
MODE = sys.argv[1]
SESSION = str(time.time_ns()) + '-' + str(os.getpid())
LOGDIR = ROOT / 'out' / ('anchors' if MODE == 'anchors' else 'profile') / SESSION
LOGDIR.mkdir(parents=True, exist_ok=True)
ENV = dict(os.environ, CUDA_VISIBLE_DEVICES='0')
ENV['PATH'] = str(Path.home()/'.local/bin') + os.pathsep + ENV.get('PATH','')


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp-' + SESSION)
    temp.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')
    temp.replace(path)


def command(args, logfile, cwd=ROOT, timeout=3600):
    start = time.perf_counter()
    with open(logfile, 'w') as stream:
        stream.write('argv: ' + repr(list(map(str,args))) + '\n')
        stream.flush()
        proc = subprocess.Popen(list(map(str,args)), cwd=cwd, env=ENV,
                                stdout=stream, stderr=subprocess.STDOUT,
                                start_new_session=True)
        try:
            status = proc.wait(timeout=timeout)
        except BaseException:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.wait()
            raise
    elapsed = time.perf_counter() - start
    write_json(str(logfile)+'.status.json', {'exit_status': status, 'wall_s': elapsed})
    if status:
        raise RuntimeError(f'Command failed ({status}); see {logfile}')
    return elapsed


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def check_published():
    actual = subprocess.check_output(['git','-C',str(PUBLISHED),'rev-parse','HEAD'], text=True).strip()
    if actual != PIN:
        raise RuntimeError('Published checkout pin mismatch; run setup.sh')
    subprocess.run(['git','-C',str(PUBLISHED),'diff','--exit-code','HEAD'], check=True)
    host = (PUBLISHED/SAMPLE/'MonteCarloMultiGPU.cpp').read_text()
    for name, value in [('nOptions',8192),('PATH_N',262144)]:
        match = re.search(r'\b'+name+r'\s*=\s*([^;]+);', host)
        if not match or not re.fullmatch(r'[\d\s*()+-]+',match[1]) or eval(match[1], {'__builtins__':{}}, {}) != value:
            raise RuntimeError(f'Unexpected published {name} declaration')
    return host


def parse(logfile, options, paths):
    text = Path(logfile).read_text(errors='replace')
    def number(label):
        matches = re.findall(label + r'\s*[:=]\s*([+\-\d.eE]+)', text, re.I)
        if len(matches) != 1:
            raise RuntimeError(f'Missing or ambiguous {label}; see {logfile}')
        value = float(matches[0])
        if not math.isfinite(value):
            raise RuntimeError('Nonfinite sample output')
        return value
    for label, expected in [(r'GPU count',1),(r'Option count',options),(r'Paths per option',paths)]:
        if number(label) != expected:
            raise RuntimeError(f'Configuration mismatch: {label}')
    ms = number(r'Total time\s*\(ms\.\)')
    reserve = number(r'Average reserve')
    l1 = number(r'L1 norm')
    verdicts = re.findall(r'Test passed|Test failed!',text)
    if len(verdicts) != 1:
        raise RuntimeError('Missing or ambiguous final verdict')
    passed = int(verdicts[0] == 'Test passed')
    # Preserve the actual printed reserve. At rounded 1.000000 use upstream verdict.
    if ms <= 0 or passed != 1 or reserve < 1.0:
        raise RuntimeError('Published correctness or timing check failed')
    return {'total_ms':ms, 'reserve':reserve, 'sample_pass':passed,
            'l1_norm':l1, 'options':options, 'paths_per_option':paths,
            'gpu_count':1, 'method':'streamed', 'scaling':'strong', 'precision':'float',
            'reserve_boundary_accepted_by_verdict':reserve == 1.0}


def executable(tree):
    binary = tree/'build-mc/MonteCarloMultiGPU'
    if not binary.is_file():
        raise RuntimeError(f'Missing {binary}; run setup.sh')
    return binary


def run_sample(tree, options, paths, tag):
    logfile = LOGDIR/(tag+'.log')
    elapsed = command([executable(tree),'--method=streamed','--scaling=strong'], logfile, cwd=tree)
    result = parse(logfile, options, paths)
    result.update(process_wall_s=elapsed, log=str(logfile.relative_to(ROOT)), exit_status=0)
    write_json(LOGDIR/(tag+'.json'),result)
    return result


def extended_tree(host, options, paths):
    tree = ROOT/'baseline-timing'
    if not tree.exists():
        command(['git','-C',PUBLISHED,'worktree','add','--detach',tree,PIN], LOGDIR/'worktree.log')
    actual = subprocess.check_output(['git','-C',str(tree),'rev-parse','HEAD'],text=True).strip()
    if actual != PIN:
        raise RuntimeError('Timing worktree pin mismatch')
    # Only the explicitly authorized timing constants change, in a separate worktree.
    updated = host
    for name, value in [('nOptions',options),('PATH_N',paths)]:
        updated, count = re.subn(r'(\b'+name+r'\s*=\s*)[^;]+;',lambda m:m[1]+str(value)+';',updated)
        if count != 1:
            raise RuntimeError(f'Cannot uniquely change {name}')
    (tree/SAMPLE/'MonteCarloMultiGPU.cpp').write_text(updated)
    command(['cmake','-S',tree/SAMPLE,'-B',tree/'build-mc','-DCMAKE_BUILD_TYPE=Release',
             '-DCMAKE_CUDA_COMPILER=/usr/local/cuda-12.8/bin/nvcc'], LOGDIR/f'configure-{paths}.log')
    command(['cmake','--build',tree/'build-mc','--target','MonteCarloMultiGPU','--parallel'], LOGDIR/f'build-{paths}.log')
    diff = subprocess.check_output(['git','-C',str(tree),'diff','HEAD'],text=True)
    (LOGDIR/f'timing-constants-{paths}.diff').write_text(diff)
    return tree


def select_scale(host):
    tree, options, paths = PUBLISHED, 8192, 262144
    result = run_sample(tree, options, paths, 'initial')
    while result['total_ms'] < 10000:
        if options == 8192:
            options = 1048576
        else:
            paths *= 2
        if paths > 2147483647:
            raise RuntimeError('Required timing extension exceeds signed int PATH_N')
        tree = extended_tree(host, options, paths)
        result = run_sample(tree, options, paths, f'extended-{options}-{paths}')
    result.update(tree=str(tree.relative_to(ROOT)), commit=PIN,
                  source_sha256=digest(tree/SAMPLE/'MonteCarloMultiGPU.cpp'),
                  binary_sha256=digest(executable(tree)),
                  timing_extension=options != 8192)
    write_json(ROOT/'out/representative.json',result)
    return tree, result


def record_environment():
    for name,args in [('gpu',['nvidia-smi','-q']),('toolkit',['/usr/local/cuda-12.8/bin/nvcc','--version']),
                      ('libc',['getconf','GNU_LIBC_VERSION'])]:
        command(args,LOGDIR/(name+'.log'))
    # Record real device geometry and source grid formulas; do not infer timings.
    cuda = ctypes.CDLL('/usr/local/cuda-12.8/lib64/libcudart.so')
    count = ctypes.c_int()
    if cuda.cudaGetDeviceCount(ctypes.byref(count)) != 0 or count.value != 1:
        raise RuntimeError('Expected exactly one visible CUDA device')
    attributes = {}
    for label, attr in [('multiprocessor_count',16),('max_threads_per_multiprocessor',39)]:
        value = ctypes.c_int()
        if cuda.cudaDeviceGetAttribute(ctypes.byref(value),attr,0) != 0:
            raise RuntimeError('Unable to record CUDA device geometry')
        attributes[label] = value.value
    write_json(LOGDIR/'device-geometry.json',attributes)
    lines = []
    for filename in ['MonteCarloMultiGPU.cpp','MonteCarlo_kernel.cu']:
        for n,line in enumerate((PUBLISHED/SAMPLE/filename).read_text().splitlines(),1):
            if re.search(r'grid|multiProcessorCount|srand|curand_init',line,re.I):
                lines.append(f'{filename}:{n}: {line}')
    (LOGDIR/'grid-and-rng-source.txt').write_text('\n'.join(lines)+'\n')


try:
    # Remove only current summary artifacts; all timestamped raw logs survive retries.
    if MODE == 'anchors':
        (ROOT/'out/anchors_measured.json').unlink(missing_ok=True)
        (ROOT/'out/representative.json').unlink(missing_ok=True)
    else:
        for name in ['stages.json','total_wall_s.json']:
            (ROOT/'out/profile'/name).unlink(missing_ok=True)
    host = check_published()
    record_environment()
    if MODE == 'anchors':
        tree, selected = select_scale(host)
        write_json(ROOT/'out/anchors_measured.json', {
            'mc-bs-reserve':selected['reserve'], 'sample-pass':selected['sample_pass']})
    else:
        profile = ROOT/'out/profile'
        for name in ['stages.json','total_wall_s.json']:
            (profile/name).unlink(missing_ok=True)
        config = ROOT/'out/representative.json'
        if config.exists():
            selected = json.loads(config.read_text())
            if selected['commit'] != PIN or selected['total_ms'] < 10000:
                raise RuntimeError('Invalid selected configuration')
            tree = ROOT/selected['tree']
            if tree not in (PUBLISHED, ROOT/'baseline-timing'):
                raise RuntimeError('Unexpected baseline directory')
            if digest(tree/SAMPLE/'MonteCarloMultiGPU.cpp') != selected['source_sha256'] or digest(executable(tree)) != selected['binary_sha256']:
                raise RuntimeError('Selected source or executable changed; rerun anchors')
        else:
            tree, selected = select_scale(host)
        # Calibration/builds above are excluded. This interval runs the selected baseline once.
        start = time.perf_counter()
        telemetry_file = open(LOGDIR/'nvidia-smi.csv','w')
        sampler = None
        telemetry_status = None
        try:
            sampler = subprocess.Popen(['nvidia-smi','--id=0',
                '--query-gpu=timestamp,index,uuid,name,utilization.gpu,utilization.memory,memory.used,power.draw,clocks.sm',
                '--format=csv','--loop-ms=100'],stdout=telemetry_file,stderr=subprocess.STDOUT)
            workload_start = time.perf_counter()
            logfile = LOGDIR/'baseline.log'
            wall = command([executable(tree),'--method=streamed','--scaling=strong'],logfile,cwd=tree)
            workload_end = time.perf_counter()
            measured = parse(logfile,selected['options'],selected['paths_per_option'])
            write_json(LOGDIR/'measured.json',measured)
            validated = time.perf_counter()
        finally:
            if sampler is not None:
                if sampler.poll() is None:
                    sampler.terminate()
                try:
                    telemetry_status = sampler.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    sampler.kill()
                    telemetry_status = sampler.wait()
            telemetry_file.close()
        end = time.perf_counter()
        write_json(LOGDIR/'telemetry-status.json',{'exit_status':telemetry_status,
            'gpu_s':None,'reason':'Utilization samples do not measure GPU elapsed seconds.'})
        # One process stage includes overlapping preprocessing, transfers and GPU work.
        # The upstream interval is nested inside this stage and is not added again.
        stages = [
            {'stage':'telemetry_startup','wall_s':workload_start-start,'gpu_s':None},
            {'stage':'baseline_process','wall_s':workload_end-workload_start,'gpu_s':None},
            {'stage':'result_validation','wall_s':validated-workload_end,'gpu_s':None},
            {'stage':'telemetry_shutdown','wall_s':end-validated,'gpu_s':None}]
        write_json(LOGDIR/'scope.json',{'selected_configuration':selected,
            'upstream_total_ms':measured['total_ms'],
            'note':'Process wall includes allocation, RNG initialization, streamed pricing, CPU finalization and Black-Scholes validation. Nested streamed timer is saved separately; no phase timing is inferred from utilization.'})
        write_json(profile/'stages.json',stages)
        write_json(profile/'total_wall_s.json',{'total_wall_s':end-start})
except BaseException as exc:
    (LOGDIR/'failure.txt').write_text(repr(exc)+'\n')
    raise

PY
