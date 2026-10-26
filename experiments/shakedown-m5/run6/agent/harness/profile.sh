#!/usr/bin/env bash
set -euo pipefail
mkdir -p out/profile
export HARNESS_BASELINE=${BASELINE_DIR:-$PWD/baseline-published}
# Reuse the fixed representative configuration prepared by setup.sh. Build with
# the published commands and the compiler path discovered by the box probe.
/usr/bin/cmake -S "$HARNESS_BASELINE/Samples/5_Domain_Specific/MonteCarloMultiGPU" -B "$HARNESS_BASELINE/build-mc" -DCMAKE_BUILD_TYPE=Release -DCMAKE_CUDA_COMPILER=/usr/bin/nvcc > out/profile/build.log 2>&1
/usr/bin/cmake --build "$HARNESS_BASELINE/build-mc" --target MonteCarloMultiGPU --parallel 8 >> out/profile/build.log 2>&1
python3 - <<'PY'
import errno, json, math, os, pathlib, pty, re, select, signal
import subprocess, threading, time

out = pathlib.Path('out/profile').resolve()
for name in ('stages.json', 'total_wall_s.json', 'gpu_util.json', 'baseline_metrics.json'):
    (out / name).unlink(missing_ok=True)
samples = []
markers = []
stop = threading.Event()

def sample():
    with open(out / 'nvidia-smi.csv', 'w') as raw:
        while not stop.is_set():
            try:
                query = subprocess.run(
                    ['nvidia-smi', '--id=0', '--query-gpu=utilization.gpu',
                     '--format=csv,noheader,nounits'],
                    capture_output=True, text=True, timeout=5)
                t = time.monotonic() - begin
                raw.write(f'{t:.9f},{query.stdout.strip()},{query.stderr.strip()}\n')
                raw.flush()
                if query.returncode == 0:
                    util = float(query.stdout.strip())
                    if math.isfinite(util) and 0 <= util <= 100:
                        samples.append({'t': t, 'util': util})
            except (ValueError, OSError, subprocess.TimeoutExpired) as error:
                raw.write(f'query error: {error}\n')
                raw.flush()
            stop.wait(.1)

# A terminal makes libc flush each output line at the program's own phase
# boundaries. No source instrumentation or CUDA preload changes the binary.
# These are host wall measurements; they do not claim device execution times.
phases = [
    (r'main\(\): generating input data', 'option input generation', 'other'),
    (r'main\(\): starting \d+ host threads', 'GPU setup and streamed pricing', 'compute'),
    (r'Total time\s*\(ms\.?\)\s*:', 'host result finalization', 'other'),
    (r'main\(\): comparing Monte Carlo and Black-Scholes results', 'Black-Scholes validation', 'compute'),
    (r'Shutting down', 'CUDA teardown and result reporting', 'other'),
]
master, slave = pty.openpty()
env = os.environ.copy()
env['CUDA_VISIBLE_DEVICES'] = '0'
# Do not use setup.sh's broken CUPTI activity preload.
env.pop('HARNESS_ACTIVITY', None)
thread = threading.Thread(target=sample)
p = None
begin = time.monotonic()
try:
    p = subprocess.Popen(
        [os.environ['HARNESS_BASELINE'] + '/build-mc/MonteCarloMultiGPU',
         '--method=streamed', '--scaling=strong'],
        stdout=slave, stderr=subprocess.STDOUT, env=env, start_new_session=True)
    os.close(slave)
    slave = None
    thread.start()
    pending = b''
    next_phase = 0
    with open(out / 'baseline.log', 'wb') as log:
        while True:
            remaining = 1100 - (time.monotonic() - begin)
            if remaining <= 0:
                raise subprocess.TimeoutExpired(p.args, 1100)
            if not select.select([master], [], [], min(.2, remaining))[0]:
                continue
            try:
                chunk = os.read(master, 4096)
            except OSError as error:
                if error.errno != errno.EIO:
                    raise
                chunk = b''
            if not chunk:
                break
            stamp = time.monotonic() - begin
            log.write(chunk)
            log.flush()
            pending += chunk
            while b'\n' in pending:
                line, pending = pending.split(b'\n', 1)
                text = line.decode(errors='replace')
                if next_phase < len(phases) and re.search(phases[next_phase][0], text):
                    _, stage, kind = phases[next_phase]
                    markers.append({'t': stamp, 'stage': stage, 'kind': kind, 'output': text.strip()})
                    next_phase += 1
    p.wait(timeout=max(.001, 1100 - (time.monotonic() - begin)))
    elapsed = time.monotonic() - begin
except subprocess.TimeoutExpired:
    raise SystemExit('Fixed representative scale exceeded 1100-second run budget')
finally:
    if p is not None and p.poll() is None:
        os.killpg(p.pid, signal.SIGKILL)
        p.wait()
    if slave is not None:
        os.close(slave)
    os.close(master)
    stop.set()
    if thread.ident is not None:
        thread.join()

(out / 'exit_status').write_text(str(p.returncode) + '\n')
json.dump(markers, open(out / 'phase_markers.json', 'w'), allow_nan=False, indent=2)
samples = [s for s in samples if 0 <= s['t'] <= elapsed]
json.dump(samples, open(out / 'gpu_util.json', 'w'), allow_nan=False)
if not samples:
    raise SystemExit('No valid GPU utilisation samples during measured run')
s = (out / 'baseline.log').read_text()
for label, expected in [('Number of GPUs', 1), ('Total number of options', 1048576), ('Number of paths', 262144)]:
    m = re.search(re.escape(label) + r'\s*=\s*(\d+)\s*(?:\n|$)', s, re.I)
    if not m or int(m[1]) != expected:
        raise SystemExit('Missing/invalid representative configuration: ' + label)
verdict = re.findall(r'Test (passed|failed!)', s)
if len(verdict) != 1 or p.returncode not in (0, 1) or (p.returncode == 0) != (verdict[0] == 'passed'):
    raise SystemExit('Invalid baseline verdict/exit status')
metrics = {}
for key, pattern in [
    ('total_time_ms', r'Total time\s*\(ms\.?\)\s*:\s*(\S+)'),
    ('average_reserve', r'Average reserve\s*:\s*(\S+)'),
    ('l1_norm', r'L1 norm\s*:\s*(\S+)'),
]:
    m = re.search(pattern, s, re.I)
    if not m:
        raise SystemExit('Missing baseline metric: ' + key)
    value = float(m[1])
    if not math.isfinite(value):
        raise SystemExit('Nonfinite baseline metric: ' + key)
    metrics[key] = value
if metrics['total_time_ms'] <= 0:
    raise SystemExit('Invalid baseline timing')
# A failed published correctness criterion remains a measured outcome.
metrics['sample_pass'] = int(verdict[0] == 'passed')
json.dump(metrics, open(out / 'baseline_metrics.json', 'w'), allow_nan=False)
if len(markers) != len(phases):
    raise SystemExit('Missing internal phase output; cannot measure stage boundaries')
if not math.isfinite(elapsed) or elapsed <= 0:
    raise SystemExit('Invalid total wall time')
stages = []
previous = 0.
name, kind = 'CUDA discovery and host initialization', 'other'
for marker in markers + [{'t': elapsed}]:
    duration = marker['t'] - previous
    if not math.isfinite(duration) or duration < 0:
        raise SystemExit('Invalid internal phase timing')
    stages.append({'stage': name, 'kind': kind, 'wall_s': duration, 'gpu_s': None})
    previous = marker['t']
    name, kind = marker.get('stage'), marker.get('kind')
if len([stage for stage in stages if stage['wall_s'] > 0]) < 3:
    raise SystemExit('Fewer than three timed internal stages')
if any(abs(stage['wall_s'] - elapsed) <= .02 * elapsed for stage in stages):
    raise SystemExit('Insufficient internal stage resolution: stage spans process duration')
# Consecutive output boundaries partition the critical path without overlap.
if min(1., sum(stage['wall_s'] for stage in stages) / elapsed) < .9:
    raise SystemExit('Internal stages cover less than 90% of measured run')
json.dump(stages, open(out / 'stages.json', 'w'), allow_nan=False, indent=2)
json.dump({'total_wall_s': elapsed}, open(out / 'total_wall_s.json', 'w'), allow_nan=False)
PY
