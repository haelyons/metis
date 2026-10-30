#!/usr/bin/env bash
set -euo pipefail
adapter_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
export BASELINE_DIR="${BASELINE_DIR:-$(dirname -- "$adapter_dir")}"
if [[ -f "$BASELINE_DIR/baseline-published/cuda-env.sh" ]]; then
    published_dir="$BASELINE_DIR/baseline-published"
else
    published_dir="$BASELINE_DIR"
fi
source "$published_dir/cuda-env.sh"
export EVAL_PUBLISHED_DIR="$published_dir"
export CUDA_VISIBLE_DEVICES=0
export PYTHONHASHSEED=0
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="$published_dir/python"
: "${EVAL_OUT:?EVAL_OUT required}"
: "${EVAL_PROTOCOL:?EVAL_PROTOCOL required}"
: "${EVAL_INPUTS:?EVAL_INPUTS required}"
: "${EVAL_SEEDS:?EVAL_SEEDS required}"
mkdir -p "$EVAL_OUT"
/usr/bin/python3 - <<'EVALUATE'
import ctypes, json, math, os, pathlib, re, subprocess, time
def validate(result, seed0):
    def number(x, positive=False):
        if isinstance(x, bool) or not isinstance(x, (float, int)) or not math.isfinite(x) or (positive and x <= 0):
            raise ValueError('Missing or invalid numerical output')
        return x
    if result['platform'] != 'CUDA' or result['properties'] != {'Precision':'single', 'DeterministicForces':'true'}:
        raise ValueError('Output platform/properties disagree with published command')
    if not math.isclose(number(result['simulated_ns'], True), 0.8, abs_tol=1e-12):
        raise ValueError('Invalid simulated work')
    number(result['total_wall_s'], True)
    if len(result['replicas']) != 8:
        raise ValueError('Missing replica output')
    for i, replica in enumerate(result['replicas']):
        if (replica['replica'], replica['seed'], replica['steps']) != (i, seed0+i, 25000):
            raise ValueError('Output work/seeds disagree with command')
        number(replica['wall_s'], True)
        number(replica['final_potential_kj_mol'])
        number(replica['mean_potential_kj_mol'])
    return result['simulated_ns']/result['total_wall_s']*86400

root = pathlib.Path(os.environ['BASELINE_DIR']).resolve()
published = pathlib.Path(os.environ['EVAL_PUBLISHED_DIR']).resolve()
data = root/'data'
if not data.is_dir():
    data = published.parent/'data'
output = pathlib.Path(os.environ['EVAL_OUT'])
(output/'evaluation.json').unlink(missing_ok=True)
protocol = json.loads(pathlib.Path(os.environ['EVAL_PROTOCOL']).read_text())
inputs = json.loads(os.environ['EVAL_INPUTS'])
seed_spec = json.loads(os.environ['EVAL_SEEDS'])
mode = os.environ['EVAL_MODE']
if mode not in ('anchors', 'equivalence', 'warmup', 'performance', 'curve'):
    raise ValueError('Unknown evaluation mode')
ids = inputs['ids']
if not isinstance(ids, list) or not ids or any(not isinstance(i, str) for i in ids):
    raise ValueError('Invalid sealed input IDs')
if seed_spec['kind'] == 'paired_median':
    seeds = seed_spec['seeds']
    if not seeds or any(type(s) is not int for s in seeds):
        raise ValueError('Invalid paired execution seeds')
elif seed_spec['kind'] == 'deterministic':
    seeds = [None]
else:
    raise ValueError('Unsupported sealed seed protocol')
scope = protocol.get('timing_scope')
if scope is None:
    raise ValueError('Seal missing timing_scope')
budget_text = os.environ.get('EVAL_COMPUTE_BUDGET', '')
budget = None
if mode == 'curve':
    budget = json.loads(budget_text)
    if isinstance(budget, dict):
        limit = next((budget[k] for k in ('gpu_seconds', 'gpu_s', 'seconds', 'value') if k in budget), None)
    else:
        limit = budget
    if isinstance(limit, bool) or not isinstance(limit, (float, int)) or not math.isfinite(limit) or limit <= 0:
        raise ValueError('Curve budget must specify positive GPU seconds')
else:
    limit = None
# One visible GPU; context energy queries and destruction also block in driver.
runtime = ctypes.CDLL(str(pathlib.Path(os.environ['CUDA_LIBRARY_DIR'])/'libcudart.so'))
for name in ('cudaSetDevice', 'cudaDeviceSynchronize'):
    getattr(runtime, name).restype = ctypes.c_int
def synchronize():
    if runtime.cudaSetDevice(0) != 0 or runtime.cudaDeviceSynchronize() != 0:
        raise RuntimeError('CUDA synchronization failed')
# The paired seeds identify replicas, not independent eight-replica ensembles.
# Run the published fixed scale once per molecular input and scatter by seed.
configuration = inputs['configuration']
replicas = configuration['replicas']
steps = configuration['steps_per_replica']
seed0 = configuration['seed0']
if (replicas, steps, seed0) != (8, 25000, 1000):
    raise ValueError('Configuration disagrees with fixed published scale')
if seeds != [None] and seeds != list(range(seed0, seed0+replicas)):
    raise ValueError('Paired seeds must match the eight published replica seeds')
arm = os.environ.get('EVAL_ARM', 'baseline')
gpu_count = protocol['hardware_cost_basis'][arm+'_gpus']
if gpu_count != 1:
    raise ValueError('Published workload requires one GPU')
metric_names = [m['name'] for m in protocol['equivalence_metrics']]
synchronize()
start = time.perf_counter()
results = {}
for input_index, input_id in enumerate(ids):
    run = output / ('input-%04d' % input_index)
    run.mkdir(parents=True, exist_ok=True)
    for name in ('5dfr_solv-cube_equil.pdb', 'amber99sb.xml', 'tip3p.xml'):
        target = run/name
        if not target.exists():
            target.symlink_to(data/name)
    env = os.environ.copy()
    env['TMPDIR'] = str(run)
    # Inherit normal CUDA cache policy across warmup and measured invocations.
    command = ['/usr/bin/python3', str(published/'dhfr_ensemble.py'),
               '--replicas', str(replicas), '--steps', str(steps),
               '--seed0', str(seed0), '--platform', 'CUDA', '--out', 'ensemble.json']
    deadline = min(1100, limit/gpu_count if limit is not None else 1100)
    remaining = deadline-(time.perf_counter()-start)
    if remaining <= 0:
        raise RuntimeError('Invocation GPU-second budget exhausted')
    (run/'ensemble.json').unlink(missing_ok=True)
    try:
        with (run/'stdout.log').open('w') as log:
            subprocess.run(command, cwd=run, env=env, stdout=log,
                           stderr=subprocess.STDOUT, check=True, timeout=remaining)
    finally:
        synchronize()
    result = json.loads((run/'ensemble.json').read_text())
    throughput = validate(result, seed0)
    log = (run/'stdout.log').read_text()
    for key, expected, tolerance in [('total_wall_s', result['total_wall_s'], 0.00051), ('aggregate_ns_per_day', throughput, 0.051)]:
        values = re.findall(r'^'+key+r':\s*(\S+)\s*$', log, re.M)
        if not values or not math.isfinite(float(values[-1])) or abs(float(values[-1])-expected) > tolerance:
            raise ValueError('Invalid printed '+key)
    results[input_id] = result
records = []
for seed in seeds:
    for input_id in ids:
        result = results[input_id]
        if seed is None:
            metrics = {name: sum(r[name] for r in result['replicas'])/replicas
                       for name in metric_names}
        else:
            replica = result['replicas'][seed-seed0]
            metrics = {name: replica[name] for name in metric_names}
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
               for v in metrics.values()):
            raise ValueError('Nonfinite equivalence metric')
        records.append({'input_id': input_id, 'seed': seed, 'metrics': metrics})
report = {'records': records, 'timing_scope': scope, 'gpu_count': gpu_count,
          'compute_budget': budget}
# Include the ordered merge and JSON serialization in the process-wall scope.
encoded = json.dumps(report, indent=2, allow_nan=False)
staged = output/'evaluation.pending.json'
staged.write_text(encoded+'\n')
staged.unlink()
synchronize()
wall = time.perf_counter()-start
if limit is not None and wall*gpu_count > limit:
    raise RuntimeError('Curve GPU-second budget exceeded')
report = {'records': records, 'timing_scope': scope, 'gpu_count': gpu_count,
          'wall_s': wall, 'compute_budget': budget}
if mode == 'anchors':
    anchor_ids = ['nvidia-2025-dhfr-eight-tuned-throughput']
    if len(ids) != 1:
        raise ValueError('Published anchor requires one input')
    result = results[ids[0]]
    measured = result['simulated_ns']/result['total_wall_s']*86400
    (output/'anchors_measured.json').write_text(json.dumps({k: measured for k in anchor_ids})+'\n')
(output/'evaluation.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
EVALUATE
