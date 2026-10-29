#!/usr/bin/env bash
set -euo pipefail
select_cuda() {
    local root
    CUDA_NVCC=
    for root in /usr/local/cuda /usr/lib/cuda; do
        if [[ -x "$root/bin/nvcc" && -f "$root/include/cuda_runtime.h" && -f "$root/lib64/libcudart.so" ]]; then
            CUDA_NVCC="$root/bin/nvcc"
            CUDA_INCLUDE="$root/include"
            CUDA_LIBRARY="$root/lib64"
            export CUDAToolkit_ROOT="$root"
            break
        fi
    done
    if [[ -z "${CUDA_NVCC:-}" ]]; then
        CUDA_NVCC=/usr/bin/nvcc
        CUDA_INCLUDE=/usr/include
        CUDA_LIBRARY=/usr/lib/x86_64-linux-gnu
    fi
    ls "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIBRARY/libcudart.so"
    export PATH="${CUDA_NVCC%/*}:$PATH"
    export LD_LIBRARY_PATH="$CUDA_LIBRARY${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
    export OPENMM_CUDA_COMPILER="$CUDA_NVCC"
}
select_cuda

export PYTHONNOUSERSITE=1
export PYTHONUNBUFFERED=1
if [[ "${EVAL_MODE:-equivalence}" == anchors ]]; then
    cd "$(dirname "$(readlink -f "$0")")/.."
    exec bash harness/run_anchors.sh
fi
/usr/bin/python3 - <<'EVALUATE'
import ctypes
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import sys
import threading
import time

# Watchdogs terminate incomplete work rather than emit partial outcomes.
def watchdog(seconds):
    def expire():
        os.write(2, b'Evaluation time or GPU-second budget exhausted\n')
        os.kill(os.getpid(), signal.SIGKILL)
    timer = threading.Timer(seconds, expire)
    timer.daemon = True
    timer.start()
    return timer

stage_timer = watchdog(1100)
mode = os.environ.get('EVAL_MODE', 'equivalence')
if mode not in ('equivalence', 'warmup', 'performance', 'curve'):
    raise ValueError('Unknown EVAL_MODE: ' + mode)
arm = os.environ['EVAL_ARM']
if arm not in ('baseline', 'method'):
    raise ValueError('Unknown EVAL_ARM: ' + arm)
# This is the sequential baseline adapter. Method implementations have their own adapter.
if arm != 'baseline':
    raise ValueError('Baseline adapter requires EVAL_ARM=baseline')
protocol = json.loads(Path(os.environ['EVAL_PROTOCOL']).read_text())
inputs = json.loads(os.environ['EVAL_INPUTS'])
seed_spec = json.loads(os.environ['EVAL_SEEDS'])
ids = inputs['ids']
if ids != protocol['evaluation_inputs']['ids'] or not ids:
    raise ValueError('Input identities differ from sealed protocol')
if seed_spec['kind'] == 'paired_median':
    seeds = seed_spec['seeds']
elif seed_spec['kind'] == 'deterministic':
    seeds = [None]
else:
    raise ValueError('Unknown seed protocol')
configuration = protocol['evaluation_inputs']['configuration']
# The eight seeds identify the eight replicas, not eight shifted ensembles.
execution_seeds = configuration['seeds'] if seeds == [None] else seeds
if execution_seeds != configuration['seeds'] or any(type(s) is not int for s in execution_seeds):
    raise ValueError('Execution seeds differ from fixed published ensemble')
if (configuration['replicas'], configuration['steps_per_replica'],
        configuration['energy_interval_steps']) != (8, 25000, 250):
    raise ValueError('Unsupported published scale')
metric_names = [m['name'] for m in protocol['equivalence_metrics']]
if set(metric_names) != {'mean_potential_kj_mol', 'final_potential_kj_mol'}:
    raise ValueError('Unsupported scientific metrics')
gpu_count = protocol['hardware_cost_basis'][arm + '_gpus']
if gpu_count != 1:
    raise ValueError('Published baseline uses one GPU')
raw_budget = os.environ.get('EVAL_COMPUTE_BUDGET', '')
budget = json.loads(raw_budget) if raw_budget else None
limit = None
if mode == 'curve':
    limit = budget
    if isinstance(budget, dict):
        limit = next((budget[k] for k in ('gpu_seconds', 'gpu_s', 'budget_gpu_s',
                     'compute_budget_gpu_s', 'value') if k in budget), None)
    if type(limit) not in (int, float) or not math.isfinite(limit) or limit <= 0:
        raise ValueError('Curve requires a finite positive GPU-second budget')

base = Path(os.environ['BASELINE_DIR']).resolve(strict=True)
output = Path(os.environ['EVAL_OUT']).resolve()
output.mkdir(parents=True, exist_ok=True)
# Setup installs the pinned package under BASELINE_DIR/python and the pinned
# data beside BASELINE_DIR. These paths remain valid from fresh working dirs.
sys.path.insert(0, str(base / 'python'))
import openmm as mm
from openmm import app, unit

data = base.parent / 'data'
for pin in protocol['evaluation_inputs']['pins']['files']:
    path = data / pin['name']
    if hashlib.sha256(path.read_bytes()).hexdigest() != pin['sha256']:
        raise ValueError('Pinned input hash mismatch: ' + str(path))
pdb = app.PDBFile(str(data / '5dfr_solv-cube_equil.pdb'))
forcefield = app.ForceField(str(data / 'amber99sb.xml'), str(data / 'tip3p.xml'))
system = forcefield.createSystem(pdb.topology, nonbondedMethod=app.PME,
    nonbondedCutoff=0.9, constraints=app.HBonds, hydrogenMass=1.5 * unit.amu)
platform = mm.Platform.getPlatformByName('CUDA')
properties = {'Precision': 'single', 'DeterministicForces': 'true'}
cudart = ctypes.CDLL('libcudart.so')
cudart.cudaSetDevice.argtypes = [ctypes.c_int]
cudart.cudaSetDevice.restype = ctypes.c_int
cudart.cudaDeviceSynchronize.argtypes = []
cudart.cudaDeviceSynchronize.restype = ctypes.c_int

def synchronize():
    # One allocated device; respect the pipeline's CUDA visibility and MPS env.
    for fn, args in ((cudart.cudaSetDevice, (0,)),
                     (cudart.cudaDeviceSynchronize, ())):
        status = fn(*args)
        if status:
            raise RuntimeError('CUDA synchronization failed: ' + str(status))

# Imports, input loading and System construction precede the sealed timer.
# Context creation, transfers, integration, queries, destruction and merge are
# all inside it. Energy getState also synchronizes each OpenMM context.
replicas = []
records = []
start = time.perf_counter()
budget_timer = watchdog(limit / gpu_count) if limit is not None else None
for index, seed in enumerate(execution_seeds):
    for input_id in ids:
        integrator = mm.LangevinMiddleIntegrator(300 * unit.kelvin,
            1 / unit.picosecond, 0.004 * unit.picoseconds)
        integrator.setConstraintTolerance(1e-5)
        integrator.setRandomNumberSeed(seed)
        context = mm.Context(system, integrator, platform, properties)
        context.setPositions(pdb.positions)
        context.setVelocitiesToTemperature(300 * unit.kelvin, seed)
        began = time.perf_counter()
        energies = []
        for _ in range(25000 // 250):
            integrator.step(250)
            energies.append(context.getState(getEnergy=True).getPotentialEnergy()
                            .value_in_unit(unit.kilojoule_per_mole))
        synchronize()
        metrics = {'mean_potential_kj_mol': sum(energies) / len(energies),
                   'final_potential_kj_mol': energies[-1]}
        if any(not math.isfinite(v) for v in energies + list(metrics.values())):
            raise ValueError('Nonfinite measured potential energy')
        replicas.append(dict(replica=index, seed=seed, steps=25000,
            wall_s=time.perf_counter() - began, **metrics))
        records.append(dict(input_id=input_id, seed=seed, metrics=metrics))
        del context, integrator
synchronize()
if seeds == [None]:
    # Deterministic protocols have one record per input; the scientific metrics
    # are ensemble means when there is no per-replica execution-seed identity.
    records = [dict(input_id=input_id, seed=None, metrics={
        name: sum(r['metrics'][name] for r in records if r['input_id'] == input_id)
              / len(execution_seeds) for name in metric_names}) for input_id in ids]
wall = time.perf_counter() - start
if not math.isfinite(wall) or wall <= 0:
    raise ValueError('Invalid measured ensemble wall time')
if limit is not None and wall * gpu_count >= limit:
    raise RuntimeError('Evaluation exceeded GPU-second budget')
result = dict(records=records, timing_scope=protocol['timing_scope'],
              gpu_count=gpu_count, wall_s=wall)
if mode == 'curve':
    result['compute_budget'] = budget
# Only newly measured outcomes are serialized; no baseline output is read.
(output / 'ensemble.json').write_text(json.dumps(dict(platform='CUDA',
    properties=properties, simulated_ns=0.8 * len(ids), total_wall_s=wall,
    replicas=replicas), indent=2, allow_nan=False) + '\n')
(output / 'evaluation.json').write_text(json.dumps(result, indent=2,
                                                allow_nan=False) + '\n')
if budget_timer is not None:
    budget_timer.cancel()
stage_timer.cancel()
EVALUATE
