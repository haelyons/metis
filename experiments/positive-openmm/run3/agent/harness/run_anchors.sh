#!/usr/bin/env bash
set -euo pipefail
mkdir -p out
# The published OpenMM pins leave NVIDIA runtime dependencies unpinned.  Setup's
# log resolved NVRTC 12.9.86, whose PTX cannot load on the probed 570 driver.
# Repair only that dependency in the isolated baseline, never the stock image.
# Keep this persistent: profiling and sibling work directories use the same
# baseline and the exact same run_command.sh without environment overrides.
python3 - <<'PY_NVRTC'
import importlib.metadata as md
import pathlib
import shutil
import subprocess
import tempfile

target = pathlib.Path('baseline-published/python')
def distributions():
    return {d.metadata['Name'].lower().replace('_', '-'): d
            for d in md.distributions(path=[str(target)])}

installed = distributions()
for name in ('openmm', 'openmm-cuda-12'):
    if name not in installed or installed[name].version != '8.2.0':
        raise RuntimeError('Missing published baseline pin: ' + name + '==8.2.0')
name = 'nvidia-cuda-nvrtc-cu12'
if name not in installed:
    raise RuntimeError('Baseline NVRTC dependency missing; setup must complete first')
version = installed[name].version
if tuple(map(int, version.split('.')[:2])) > (12, 8):
    repair = pathlib.Path(tempfile.mkdtemp(prefix='nvrtc-compat.', dir='out'))
    requirement = repair / 'requirements.txt'
    requirement.write_text('nvidia-cuda-nvrtc-cu12==12.8.93 '
                           '--hash=sha256:a7756528852ef889772a84c6cd89d41dfa74667e24cca16bb31f8f061e3e9994\n')
    staged = repair / 'python'
    with (repair / 'install.log').open('w') as log:
        subprocess.run(['python3', '-m', 'pip', 'install', '--no-deps',
                        '--only-binary=:all:', '--require-hashes',
                        '--target', str(staged), '-r', str(requirement)],
                       stdout=log, stderr=subprocess.STDOUT, check=True, timeout=180)
    replacement = staged / 'nvidia/cuda_nvrtc'
    if not (replacement / 'lib/libnvrtc.so.12').is_file():
        raise RuntimeError('Compatible NVRTC wheel has no libnvrtc.so.12')
    # Do not replace the shared nvidia namespace: it also contains cuFFT,
    # cudart, and other dependencies used by the unchanged canonical command.
    old = target / 'nvidia/cuda_nvrtc'
    backup = repair / 'previous'
    backup.mkdir()
    if old.exists():
        shutil.move(str(old), str(backup / old.name))
    shutil.move(str(replacement), str(old))
    for info in target.glob('nvidia_cuda_nvrtc_cu12-*.dist-info'):
        shutil.move(str(info), str(backup / info.name))
    for info in staged.glob('nvidia_cuda_nvrtc_cu12-*.dist-info'):
        shutil.move(str(info), str(target / info.name))
    # Compiled artifacts can contain the incompatible PTX. Preserve rather
    # than delete them; run_command.sh creates fresh per-workdir caches.
    for cache in ('cuda-cache', 'tmp'):
        path = pathlib.Path('out') / cache
        if path.exists():
            shutil.move(str(path), str(backup / cache))
    if distributions()[name].version != '12.8.93':
        raise RuntimeError('NVRTC compatibility repair did not install 12.8.93')
    print('Isolated baseline NVRTC: ' + version + ' -> 12.8.93; logs: ' + str(repair), flush=True)
PY_NVRTC
launch_dir=$(mktemp -d out/anchors.XXXXXXXX)
bash harness/run_command.sh 2>&1 | tee "$launch_dir/launch.log"
# Resolve intake through the harness link, while measurements stay relative to
# the caller's working directory (including sibling evaluation workdirs).
harness_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
intake_dir="$harness_dir/../intake"
python3 - "$intake_dir" <<'PY_ANCHORS'
import json, math, os, pathlib, re, sys

intake=pathlib.Path(sys.argv[1])
# Intake is not one of the trees staged into remote evaluation workdirs.
# Embed the supplied fixed configuration and item IDs so this script remains
# self-contained; use intake JSON when available, including an empty item list.
configuration={
    'atoms':23558, 'force_fields':['amber99sb.xml','tip3p.xml'],
    'nonbonded_method':'PME', 'cutoff_nm':0.9, 'constraints':'HBonds',
    'hydrogen_mass_amu':1.5, 'integrator':'LangevinMiddleIntegrator',
    'temperature_K':300, 'friction_per_ps':1, 'step_fs':4,
    'constraint_tolerance':1e-5, 'platform':'CUDA',
    'properties':{'Precision':'single','DeterministicForces':'true'},
    'gpu_count':1, 'replicas':8, 'steps_per_replica':25000,
    'seeds':list(range(1000,1008)), 'energy_interval_steps':250,
}
if (intake/'EXECUTION.json').is_file():
    configuration=json.loads((intake/'EXECUTION.json').read_text())['inputs']['configuration']
items=[{'id':'nvidia_2025_dhfr_8replicas_tuned_throughput_reference'}]
if (intake/'anchors.json').is_file():
    items=json.loads((intake/'anchors.json').read_text())

def finite(x, positive=False):
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) or (positive and x<=0):
        raise RuntimeError('Missing/invalid numeric output: '+repr(x))
    return x

def read_run(root,seed):
    run=root/(root/'out/last_run.txt').read_text().strip()
    result=json.loads((run/'ensemble.json').read_text())
    c=json.loads((run/'configuration.json').read_text())
    expected_seeds=list(range(seed,seed+8))
    expected_config=dict(configuration)
    expected_config['seeds']=expected_seeds
    if any(c.get(key)!=value for key,value in expected_config.items()):
        raise RuntimeError('Printed published configuration mismatch')
    if c['command']!=['python3','dhfr_ensemble.py','--replicas','8','--steps','25000','--seed0',str(seed)]:
        raise RuntimeError('Printed command mismatch')
    if c['CUDA_VISIBLE_DEVICES']!='0' or c['gpu_count']!=1 or c['seeds']!=expected_seeds:
        raise RuntimeError('Printed environment/configuration mismatch')
    if result['platform']!='CUDA' or result['properties']!={'Precision':'single','DeterministicForces':'true'}:
        raise RuntimeError('Invalid platform/properties output')
    if result['simulated_ns']!=0.8 or len(result['replicas'])!=8:
        raise RuntimeError('Invalid ensemble scale output')
    wall=finite(result['total_wall_s'],True)
    throughput=0.8/wall*86400
    metrics={'total_wall_s':wall,'aggregate_ns_per_day':throughput,'aggregate_us_per_day':throughput/1000}
    for i,r in enumerate(result['replicas']):
        if (r['replica'],r['seed'],r['steps'])!=(i,seed+i,25000): raise RuntimeError('Replica configuration mismatch')
        finite(r['wall_s'],True)
        for name in ('final_potential_kj_mol','mean_potential_kj_mol'):
            metrics[f'replica_{i}_{name}']=finite(r[name])
    stdout=(run/'stdout.log').read_text()
    for name,target,tol in [('total_wall_s',wall,0.00051),('aggregate_ns_per_day',throughput,0.051)]:
        matches=re.findall(r'^'+name+r':\s*(\S+)\s*$',stdout,re.M)
        if len(matches)!=1 or abs(finite(float(matches[0]),True)-target)>tol:
            raise RuntimeError('Missing/invalid printed measurement: '+name)
    return metrics

metrics=read_run(pathlib.Path('.'),int(os.environ.get('DHFR_SEED0','1000')))
metric_by_id={'nvidia_2025_dhfr_8replicas_tuned_throughput_reference':'aggregate_us_per_day'}
measured={item['id']:metrics[metric_by_id[item['id']]] for item in items}
pathlib.Path('out/anchors_measured.json').write_text(json.dumps(measured,allow_nan=False,indent=2)+'\n')
PY_ANCHORS
