#!/usr/bin/env node
'use strict'

// Black-box stage-6 contracts. Do not inspect implementation files or git diffs.
// Usage: node tools/test_m5_implement.js
// WF_STUB bypasses provider execution. Sentinel probes therefore also invoke the
// real workflow dispatch with a local fake Codex executable and descriptor.
// These checks require a host with working unprivileged bubblewrap.
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const assert = require('node:assert/strict')
const { spawn, spawnSync } = require('node:child_process')
const { createHash, randomUUID } = require('node:crypto')
const ROOT = path.resolve(__dirname, '..')
const { assertEvalShapes } = require('./test_m5_reproduce.js')
const PRIVATE = 'IMPLEMENT_PRIVATE_SENTINEL_593771'
const TEST_SECRET = 'TEST_SOURCE_SENTINEL_174839'
const METHOD_SECRET = 'METHOD_SOURCE_SENTINEL_284950'
const CREDENTIAL = 'FAKE_AUTH_SENTINEL_395061'
const IDS = ['dropped_inputs', 'duplicated_inputs', 'ordering', 'tail_handling', 'seeds', 'equivalence']
const readJSON = file => JSON.parse(fs.readFileSync(file, 'utf8'))
// Recorded public evidence: positive-openmm run8 (sealed protocol, frozen tests,
// representative baseline/method outputs paired by seeds 1000..1007).
const RUN8 = path.resolve(ROOT, '..', '..', 'experiments', 'positive-openmm', 'run8', 'agent')
const RUN8_ENSEMBLE = {
  baseline: path.join(RUN8, 'results', 'implement', 'baseline', 'out', 'run', 'ensemble.json'),
  method: [1, 2].map(n => path.join(RUN8, 'results', 'implement', `attempt-${n}`, 'run', 'out', 'run', 'ensemble.json')),
}
// Recorded public evidence: positive-openmm run9 (sealed protocol, pre-seal harness
// run_evaluation.sh, and evaluate's equivalence records for each arm).
const RUN9 = path.resolve(ROOT, '..', '..', 'experiments', 'positive-openmm', 'run9', 'agent')
const RUN9_RECORDS = {
  baseline: path.join(RUN9, 'results', 'evaluate', 'equivalence-0-baseline.json'),
  method: path.join(RUN9, 'results', 'evaluate', 'equivalence-0-method.json'),
}
// Sentinels that let the adapter-repair prompt be checked for its documented inputs.
const SEAL_SOURCE = 'SEALED_SOURCE_SENTINEL_610274'
const INTAKE_NOTE = 'INTAKE_SENTINEL_610275'
const HARNESS_NOTE = 'HARNESS_SENTINEL_610276'
// Baseline evaluation adapter fixture (SCHEMAS.md "Baseline and method adapter interface").
// It records its working directory, environment and links to `obs`, then writes
// EVAL_OUT/evaluation.json from EVAL_INPUTS, EVAL_SEEDS and the sealed protocol. `fault`
// injects one smoke failure; `run9-*` faults replay run9's recorded report for the given seeds.
const ADAPTER_PY = String.raw`import json, os, sys, time
obs, sequence, label, fault, recorded = sys.argv[1:6]
cwd, env = os.getcwd(), os.environ
out = env.get('EVAL_OUT')
def kind(p):
    return 'link' if os.path.islink(p) else 'dir' if os.path.isdir(p) else 'file'
names = ['EVAL_ARM', 'EVAL_MODE', 'EVAL_PROTOCOL', 'EVAL_INPUTS', 'EVAL_SEEDS', 'EVAL_COMPUTE_BUDGET', 'EVAL_OUT',
         'BASELINE_DIR', 'METHOD_DIR', 'BASELINE_OUT', 'METHOD_OUT']
row = {'label': label, 'fault': fault, 'cwd': cwd, 'env': {k: env.get(k) for k in names},
       'entries': {n: kind(os.path.join(cwd, n)) for n in sorted(os.listdir(cwd))},
       'out': sorted(os.listdir(out)) if out and os.path.isdir(out) else None}
try:
    with open(env['EVAL_PROTOCOL']) as f: protocol = json.load(f)
except Exception:
    protocol = None
row['protocol'] = protocol
with open(obs, 'a') as f: f.write(json.dumps(row) + '\n')
with open(sequence, 'a') as f: f.write('smoke ' + label + '\n')
with open(os.path.join(cwd, 'stale-marker'), 'w') as f: f.write(label)
for i in range(1, 241): print('SMOKELOG:%d:end' % i)
sys.stdout.flush()
# A known run time for the smoke's process_wall_s (then a normal report; sleep_exit exits 3).
if fault in ('sleep', 'sleep_exit'): time.sleep(2.0)
if fault == 'broken': sys.exit(9)
if fault == 'timeout':
    time.sleep(60)
    sys.exit(0)
inputs, spec = json.loads(env['EVAL_INPUTS']), json.loads(env['EVAL_SEEDS'])
seeds = spec['seeds'] if spec.get('kind') == 'paired_median' else [None]
# Seed-set faults: a single-seed subset (the former one-seed cut), a dropped or an extra seed.
if fault == 'first_seed': seeds = seeds[:1]
if fault == 'missing_seed': seeds = seeds[:-1]
if fault == 'extra_seed': seeds = seeds + [max(s or 0 for s in seeds) + 1]
ids = inputs['ids']
if fault.startswith('run9-'):
    with open(recorded) as f: report = json.load(f)
    report['records'] = [r for r in report['records'] if r['seed'] in seeds]
else:
    metric_names = [m['name'] for m in protocol['equivalence_metrics']]
    records = [{'input_id': i, 'seed': s, 'metrics': {n: 1.0 + k for k, n in enumerate(metric_names)}} for s in seeds for i in ids]
    first = metric_names[0]
    if fault == 'inputs_first':
        records = [{'input_id': i, 'seed': s, 'metrics': {n: 1.0 + k for k, n in enumerate(metric_names)}} for i in ids for s in seeds]
    if fault == 'order': records.reverse()
    if fault == 'missing_input': records.pop()
    if fault == 'wrong_seed': records[0]['seed'] = (records[0]['seed'] or 0) + 1000
    if fault == 'missing_metric': del records[-1]['metrics'][first]
    if fault == 'renamed_metric':
        for r in records: r['metrics']['replica_0_' + first] = r['metrics'].pop(first)
    if fault == 'null_metric': records[0]['metrics'][first] = None
    if fault == 'bool_metric': records[0]['metrics'][first] = True
    if fault == 'string_metric': records[0]['metrics'][first] = '1.0'
    report = {'records': records, 'timing_scope': protocol['timing_scope'],
              'gpu_count': protocol['hardware_cost_basis']['baseline_gpus'], 'wall_s': 1.5}
    if fault == 'scope': report['timing_scope'] = dict(protocol['timing_scope'], description='changed scope')
    if fault == 'gpus': report['gpu_count'] += 1
    if fault == 'wall': report['wall_s'] = 0
    if fault == 'no_wall': del report['wall_s']
if fault != 'missing_output':
    with open(os.path.join(out, 'evaluation.json'), 'w') as f: json.dump(report, f)
if fault in ('exit', 'sleep_exit'): sys.exit(3)
`
function adapterScript(root, label, fault, recorded = '') {
  return `python3 -I - ${[path.join(root, 'smoke.jsonl'), path.join(root, 'sequence.log'), label, fault || 'none', recorded].map(quote).join(' ')} <<'SMOKE_ADAPTER'
${ADAPTER_PY}SMOKE_ADAPTER`
}
// Stand-in for run9's published driver: replays the recorded replicas for one seed so that
// run9's own run_evaluation.sh runs unchanged without a GPU.
const RUN9_DRIVER = String.raw`import argparse, json
p = argparse.ArgumentParser()
for a in ('--replicas', '--steps', '--seed0', '--platform', '--out'): p.add_argument(a)
a = p.parse_args()
seed0 = int(a.seed0)
with open(RECORDED) as f: recorded = json.load(f)
m = next(r for r in recorded['records'] if r['seed'] == seed0)['metrics']
reps = [{'replica': i, 'seed': seed0 + i, 'steps': int(a.steps), 'wall_s': m['replica_%d_wall_s' % i],
         'final_potential_kj_mol': m['replica_%d_final_potential_kj_mol' % i],
         'mean_potential_kj_mol': m['replica_%d_mean_potential_kj_mol' % i]} for i in range(int(a.replicas))]
d = {'platform': a.platform, 'properties': {'Precision': 'single', 'DeterministicForces': 'true'},
     'total_wall_s': m['total_wall_s'], 'simulated_ns': m['simulated_ns'], 'replicas': reps}
with open(a.out, 'w') as f: json.dump(d, f)
print('total_wall_s: %r' % d['total_wall_s'])
print('aggregate_ns_per_day: %r' % (d['simulated_ns'] / d['total_wall_s'] * 86400))
`
// Recorded public evidence: positive-openmm run10. Its repaired run_evaluation.sh sources
// $base/cuda-env.sh, lists CUDACXX, CUDA_INCLUDE_DIR/cuda_runtime.h and
// CUDA_LIBRARY_DIR/libcudart.so, then runs `$base/venv/bin/python3 $base/dhfr_ensemble.py
// --replicas 8 --steps 25000 --seed0 1000` once per input id with HARNESS_DATA/<pdb> linked into
// its working directory, and validates the ensemble.json and stdout lines it writes.
const RUN10 = path.resolve(ROOT, '..', '..', 'experiments', 'positive-openmm', 'run10', 'agent')
const RUN10_ENSEMBLE = path.join(RUN10, 'results', 'implement', 'baseline', 'out', 'command', 'ensemble.json')
// Recorded public evidence: positive-openmm run12 (sealed warmup 1, repetitions 8, no outcome
// curve, one GPU per arm; its baseline adapter measured about 488 s per invocation in evaluate).
const RUN12 = path.resolve(ROOT, '..', '..', 'experiments', 'positive-openmm', 'run12', 'agent')
// Recorded public evidence: positive-openmm run13. The test author's view held one baseline run
// (results/reproduce/out/). BASELINE_OUT was copied from remote out/ at the start of implement, after
// profiling (results/implement/baseline/out/: a second baseline.* run, profile/ and concurrency/ outputs,
// latest-baseline-run.txt rewritten), and the frozen tests reject more than one ensemble.json.
const RUN13 = path.resolve(ROOT, '..', '..', 'experiments', 'positive-openmm', 'run13', 'agent')
const RUN13_IDS = ['dropped_inputs', 'duplicated_inputs', 'ordering', 'tail_handling', 'seeds', 'equivalence',
  'output_schema', 'fixed_work', 'upstream_output']
const RUN13_RUN = 'baseline.wdnWYQIH'
// Written into the fixture's frozen run_tests.sh: records what the tests see as BASELINE_OUT
// (relative path -> SHA-256 of contents), one JSON line per test run.
const BASELINE_SEEN_PY = String.raw`import hashlib, json, os, sys
root, log = sys.argv[1:3]
seen = {}
for directory, _, names in os.walk(root):
    for name in names:
        file = os.path.join(directory, name)
        with open(file, 'rb') as f: seen[os.path.relpath(file, root)] = hashlib.sha256(f.read()).hexdigest()
with open(log, 'a') as f: f.write(json.dumps(seen) + '\n')
`
// Fetch-side stand-in for the smoke's measurement: after a fetch, rewrites a fetched smoke.json
// according to the plan for the most recently started smoke adapter label (sequence.log). A number
// becomes {"process_wall_s": n}; 'missing' deletes the file; any other string is written verbatim.
// Each action is logged to smoke-inject.jsonl so tests can confirm the injection happened.
const SMOKE_INJECT_PY = String.raw`import json, os, sys
root, dest = sys.argv[1:3]
with open(os.path.join(root, 'smoke-inject.json')) as f: plan = json.load(f)
try:
    with open(os.path.join(root, 'sequence.log')) as f:
        labels = [line[6:].strip() for line in f if line.startswith('smoke ')]
except OSError:
    labels = []
if not labels or labels[-1] not in plan: sys.exit(0)
label, value = labels[-1], plan[labels[-1]]
candidates = [dest] if os.path.basename(dest) == 'smoke.json' else []
candidates += [os.path.join(dest, 'smoke.json'), os.path.join(dest, 'out', 'smoke.json')]
for file in candidates:
    if not os.path.isfile(file): continue
    with open(file) as f: measured = f.read()
    if value == 'missing': os.remove(file)
    else:
        with open(file, 'w') as f: f.write(value if isinstance(value, str) else json.dumps({'process_wall_s': value}))
    with open(os.path.join(root, 'smoke-inject.jsonl'), 'a') as f:
        f.write(json.dumps({'label': label, 'file': file, 'measured': measured, 'value': value}) + '\n')
`
// Stand-in for run10's published driver: replays run10's recorded baseline ensemble without a GPU
// and logs each invocation (argv, cwd, EVAL_SEEDS, EVAL_INPUTS) to CAPTURE.
const RUN10_DRIVER = String.raw`import json, os, sys
argv = sys.argv[1:]
with open(CAPTURE, 'a') as f:
    f.write(json.dumps({'argv': argv, 'cwd': os.getcwd(), 'EVAL_SEEDS': os.environ.get('EVAL_SEEDS'),
                        'EVAL_INPUTS': os.environ.get('EVAL_INPUTS')}) + '\n')
if dict(zip(argv[::2], argv[1::2])) != {'--replicas': '8', '--steps': '25000', '--seed0': '1000'}:
    sys.exit('unexpected driver arguments: %r' % argv)
with open(RECORDED) as f: d = json.load(f)
with open('ensemble.json', 'w') as f: json.dump(d, f)
print('total_wall_s: %r' % d['total_wall_s'])
print('aggregate_ns_per_day: %r' % (d['simulated_ns'] / d['total_wall_s'] * 86400))
`
// Shell that builds run10's baseline fakes in the current directory: baseline-published/ with
// cuda-env.sh, fake CUDA files, venv/bin/python3 and the driver stand-in, plus data/<pdb>.
function run10Fakes(capture) {
  return `mkdir -p baseline-published/fake-cuda/bin baseline-published/fake-cuda/include baseline-published/fake-cuda/lib baseline-published/venv/bin data
: > baseline-published/fake-cuda/bin/nvcc
: > baseline-published/fake-cuda/include/cuda_runtime.h
: > baseline-published/fake-cuda/lib/libcudart.so
: > data/5dfr_solv-cube_equil.pdb
cat > baseline-published/cuda-env.sh <<'RUN10_CUDA'
fake="$(cd "$(dirname "\${BASH_SOURCE[0]}")" && pwd)/fake-cuda"
export CUDACXX="$fake/bin/nvcc" CUDA_INCLUDE_DIR="$fake/include" CUDA_LIBRARY_DIR="$fake/lib"
RUN10_CUDA
printf '#!/usr/bin/env bash\\nexec /usr/bin/python3 -I "$@"\\n' > baseline-published/venv/bin/python3
chmod +x baseline-published/venv/bin/python3
cat > baseline-published/dhfr_ensemble.py <<'RUN10_DRIVER'
CAPTURE = ${JSON.stringify(capture)}
RECORDED = ${JSON.stringify(RUN10_ENSEMBLE)}
${RUN10_DRIVER}RUN10_DRIVER`
}
// Reference equivalence rule for the tests' `equivalence` case, written from
// SCHEMAS.md only: exact sign-test interval (largest k >= 1 with
// P(Binomial(n,0.5) < k) <= alpha/2, bounds x[k-1], x[n-k]); reject only when
// the interval is disjoint from (-margin, +margin), or under a deterministic
// seal when some paired difference exceeds the tolerance. No interval: no reject.
function orderStatisticInterval(diffs, confidence, metrics = 1) {
  const n = diffs.length, alpha = (1 - confidence) / metrics
  let k = 0, below = 0, binomial = 1
  for (let j = 1; j <= n; j++) {
    below += binomial // C(n, j-1)
    binomial = binomial * (n - j + 1) / j
    if (below / 2 ** n <= alpha / 2) k = j; else break
  }
  if (k === 0 || k - 1 > n - k) return null
  const sorted = [...diffs].sort((a, b) => a - b)
  return [sorted[k - 1], sorted[n - k]]
}
function pairedDiffs(baseline, method, name) {
  const bySeed = new Map(baseline.map(row => [row.seed, row]))
  return method.filter(row => bySeed.has(row.seed)).map(row => row[name] - bySeed.get(row.seed)[name])
}
function rejectsEquivalence(baseline, method, seal) {
  const metrics = seal.equivalence_metrics
  for (const { name, tolerance: { abs: margin } } of metrics) {
    const diffs = pairedDiffs(baseline, method, name)
    if (seal.paired_seed_tests.kind === 'deterministic') {
      if (diffs.some(d => Math.abs(d) > margin)) return true
      continue
    }
    const bounds = orderStatisticInterval(diffs, seal.confidence_rule.equivalence.confidence, metrics.length)
    if (bounds && (bounds[0] >= margin || bounds[1] <= -margin)) return true
  }
  return false
}
// A contract-following test author's checker: reads only BASELINE_OUT,
// METHOD_OUT and its sealed-protocol fixture, never evaluation records.
const CONTRACT_TESTS_PY = `import json, math, os, sys
from pathlib import Path
here = Path(__file__).resolve().parent
seal = json.loads((here / 'protocol.json').read_text())
baseline, method = Path(os.environ['BASELINE_OUT']), Path(os.environ['METHOD_OUT'])
cases = []
def case(name, ok, reason):
    cases.append({'id': name, 'pass': bool(ok), 'reason_code': None if ok else reason})
def replicas(root):
    return json.loads((root / 'run' / 'ensemble.json').read_text())['replicas']
def interval(diffs, confidence, metrics):
    n, alpha, k, below = len(diffs), (1 - confidence) / metrics, 0, 0
    for j in range(1, n + 1):
        below += math.comb(n, j - 1)
        if below / 2 ** n <= alpha / 2: k = j
        else: break
    if k == 0 or k - 1 > n - k: return None
    d = sorted(diffs)
    return d[k - 1], d[n - k]
def rejects(b, m):
    by_seed = {r['seed']: r for r in b}
    pairs = [(by_seed[r['seed']], r) for r in m if r['seed'] in by_seed]
    metrics = seal['equivalence_metrics']
    for metric in metrics:
        name, margin = metric['name'], metric['tolerance']['abs']
        diffs = [mr[name] - br[name] for br, mr in pairs]
        if seal['paired_seed_tests'].get('kind') == 'deterministic':
            if any(abs(d) > margin for d in diffs): return True
            continue
        bounds = interval(diffs, seal['confidence_rule']['equivalence']['confidence'], len(metrics))
        if bounds and (bounds[0] >= margin or bounds[1] <= -margin): return True
    return False
try:
    b, m = replicas(baseline), replicas(method)
except (OSError, ValueError, KeyError):
    for name in ('dropped_inputs', 'duplicated_inputs', 'ordering', 'tail_handling', 'seeds', 'equivalence'):
        case(name, False, 'missing_output')
else:
    bs, ms = [r['seed'] for r in b], [r['seed'] for r in m]
    case('dropped_inputs', set(bs) <= set(ms), 'dropped_inputs')
    case('duplicated_inputs', len(ms) == len(set(ms)), 'duplicated_inputs')
    case('ordering', ms == bs, 'ordering')
    case('tail_handling', bool(ms) and ms[-1] == bs[-1], 'tail_handling')
    case('seeds', ms == bs, 'seeds')
    case('equivalence', not rejects(b, m), 'equivalence')
failed = sum(not c['pass'] for c in cases)
(method / 'tests.json').write_text(json.dumps({'passed': len(cases) - failed, 'failed': failed, 'cases': cases}))
sys.exit(1 if failed else 0)
`
const rows = file => fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : []
const sha = bytes => createHash('sha256').update(bytes).digest('hex')
const quote = value => "'" + value.replace(/'/g, "'\\''") + "'"
function writeJSON(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, JSON.stringify(value) + '\n')
}
function script(file, body) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, '#!/usr/bin/env bash\nset -eu\n' + body + '\n', { mode: 0o700 })
}
const emit = (file, value) => `cat > ${quote(file)} <<'IMPLEMENT_FIXTURE'\n${JSON.stringify(value)}\nIMPLEMENT_FIXTURE\n`
function files(directory) {
  if (!fs.existsSync(directory)) return []
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    const file = path.join(directory, entry.name)
    return entry.isDirectory() ? files(file) : entry.isFile() ? [file] : []
  })
}
// Independent implementation of the documented tree digest, including modes.
function treeHash(directory) {
  const result = []
  function visit(parent, prefix) {
    for (const name of fs.readdirSync(parent).sort((a, b) => {
      const left = Array.from(a, c => c.codePointAt(0)), right = Array.from(b, c => c.codePointAt(0))
      for (let i = 0; i < Math.min(left.length, right.length); i++) if (left[i] !== right[i]) return left[i] - right[i]
      return left.length - right.length
    })) {
      const file = path.join(parent, name), relative = prefix + name
      const stat = fs.lstatSync(file), mode = stat.mode & 0o7777
      if (stat.isDirectory()) { result.push([relative, 'directory', mode]); visit(file, relative + '/') }
      else if (stat.isFile()) result.push([relative, 'file', mode, sha(fs.readFileSync(file))])
      else if (stat.isSymbolicLink()) result.push([relative, 'link', mode, fs.readlinkSync(file)])
      else throw new Error('special file in fixture tree')
    }
  }
  visit(directory, '')
  return sha(JSON.stringify(result).replace(/[\u007f-\uffff]/g, c => '\\u' + c.charCodeAt(0).toString(16).padStart(4, '0')))
}
// Relative path -> SHA-256 of contents for every regular file under a directory; null when absent.
function manifest(directory) {
  if (!fs.existsSync(directory)) return null
  return Object.fromEntries(files(directory).map(file => [path.relative(directory, file).split(path.sep).join('/'), sha(fs.readFileSync(file))]))
}
function credentialsGone(root) {
  // The original fixture credentials remain; no copied credentials may survive.
  return files(root).filter(file => !file.startsWith(path.join(root, 'fixture-home') + path.sep))
    .filter(file => fs.readFileSync(file).includes(Buffer.from(CREDENTIAL)))
}
async function isolationProbe(options, root) {
  const isolation = options.isolation
  if (!isolation || !path.isAbsolute(isolation.directory) || !Array.isArray(isolation.hidden)) {
    return { status: -1, diagnostic: 'missing isolation descriptor' }
  }
  const opposite = options.title === 'tests' ? 'method' : 'tests'
  const target = path.join(root, 'agent', opposite, 'isolation-sentinel')
  if (!fs.existsSync(target)) return { status: -1, diagnostic: 'sentinel was not planted' }
  const view = isolation.directory, bin = path.join(view, '.probe-bin')
  const capture = path.join(view, 'probe-capture.json')
  fs.mkdirSync(bin)
  // Exercise real workflow dispatch with a hermetic provider executable. No model or
  // network access. The executable is the adversarial stub agent, and reads the
  // known absolute sentinel path inside the actual provider sandbox.
  fs.writeFileSync(path.join(bin, 'codex'), `#!${process.execPath}
const fs = require('node:fs'), path = require('node:path')
const args = process.argv.slice(2)
if (args.includes('--version')) {
  console.log('codex 0.0.0-test')
  process.exit(0)
}
fs.readFileSync(0, 'utf8')
let readable = false
try { fs.readFileSync(${JSON.stringify(target)}); readable = true } catch (e) {
  if (!['ENOENT', 'EACCES', 'EPERM', 'ENOTDIR'].includes(e.code)) throw e
}
const home = process.env.HOME
const credential = path.join(home, '.codex', 'auth.json')
const authPresent = fs.existsSync(credential) && fs.readFileSync(credential, 'utf8').includes(${JSON.stringify(CREDENTIAL)})
let boxReadable = false
try { fs.readFileSync(path.join(home, '.cache', 'metis-serve', 'box.sh')); boxReadable = true } catch {}
fs.writeFileSync(${JSON.stringify(capture)}, JSON.stringify({ readable, home, authPresent, boxReadable }))
const outputIndex = args.indexOf('-o')
if (outputIndex !== -1 && args[outputIndex + 1]) {
  fs.writeFileSync(args[outputIndex + 1], '{"v":"ok"}')
}
for (const event of [{type:'thread.started',thread_id:'isolated-stub'}, {type:'turn.completed',usage:{input_tokens:0,output_tokens:0}}]) {
  fs.writeSync(1, JSON.stringify(event) + '\\n')
}
`, { mode: 0o700 })
  const work = path.join(root, 'provider-probe-' + randomUUID())
  fs.mkdirSync(work)
  const workflow = path.join(work, 'main.js'), argsFile = path.join(work, 'args.json')
  fs.writeFileSync(workflow, `export const meta = {name:'isolation-probe',description:'Hermetic sandbox probe'}
return await agent('Run the local isolation probe.', {label:'probe', agentType:'ls-writer', model:'sonnet',
  fresh:true, repairable:false, isolation:${JSON.stringify(isolation)}, schema:{type:'object',required:['v'],properties:{v:{type:'string'}}}})
`)
  writeJSON(argsFile, {})
  const errorFile = path.join(work, 'stderr')
  const errorFd = fs.openSync(errorFile, 'w')
  try {
    const env = { ...process.env, PATH: bin + path.delimiter + process.env.PATH }
    delete env.WF_STUB
    const result = await new Promise(resolve => {
      const proc = spawn(process.execPath, [path.join(ROOT, 'idea', 'wf.js'), '--script', workflow,
        '--args', argsFile, '--out', path.join(work, 'wf'), '--family', 'codex', '--mode', 'primary-only',
        '--disable-family', 'claude', '--disable-family', 'opencode', '--disable-family', 'cursor'], {
        cwd: work, env, stdio: ['ignore', 'ignore', errorFd], timeout: 15000,
      })
      let error
      proc.on('error', value => { error = value })
      proc.on('close', status => resolve({status, error}))
    })
    if (!fs.existsSync(capture)) return { status: -1, diagnostic: result.error?.message ||
      fs.readFileSync(errorFile, 'utf8').trim().slice(-300) || 'provider sandbox did not invoke fake codex [requires bubblewrap]' }
    const observed = readJSON(capture)
    return { status: observed.readable ? 9 : 0, ...observed,
      credentialsRemoved: observed.home !== process.env.HOME && !fs.existsSync(observed.home),
      diagnostic: observed.readable ? 'opposing sentinel readable via real workflow dispatch' : fs.readFileSync(errorFile, 'utf8').trim().slice(-300) }
  } catch (error) { return { status: -1, diagnostic: error.message.slice(-300) } }
  finally {
    fs.closeSync(errorFd)
    fs.rmSync(work, { recursive: true, force: true })
    fs.rmSync(bin, { recursive: true, force: true })
    fs.rmSync(capture, { force: true })
    fs.rmSync(path.join(view, 'probe-events.jsonl'), { force: true })
  }
}

module.exports = {
  async run(options) {
    const root = process.env.M5_IMPLEMENT_ROOT
    const config = JSON.parse(process.env.M5_IMPLEMENT_CONFIG)
    const { title, prompt } = options
    let json = { v: PRIVATE }
    const event = { ...options, returnedSession: randomUUID(), credentialsBefore: credentialsGone(root) }
    const agent = path.join(root, 'agent')
    fs.appendFileSync(path.join(root, 'sequence.log'), `agent ${title}\n`)
    const harnessHashes = directory => Object.fromEntries(files(directory).map(file => [path.relative(directory, file), sha(fs.readFileSync(file))]))
    if (title === 'harness') {
      const harness = path.join(agent, 'harness')
      script(path.join(harness, 'setup.sh'), `mkdir -p baseline-published data out
git init -q --separate-git-dir published-git baseline-published
printf 'published\\n' > baseline-published/pin
printf 'inputs\\n' > data/input` + (config.run9Script ? `
: > baseline-published/cuda.env
: > data/5dfr_solv-cube_equil.pdb
cat > baseline-published/dhfr_ensemble.py <<'RUN9_DRIVER'
RECORDED = ${JSON.stringify(RUN9_RECORDS.baseline)}
${RUN9_DRIVER}RUN9_DRIVER` : '') + (config.run10Script ? '\n' + run10Fakes(path.join(root, 'run10-driver.jsonl')) : ''))
      // run_anchors.sh doubles as the baseline adapter when EVAL_MODE is set (the documented
      // fallback when run_evaluation.sh is absent).
      const anchorsFault = config.anchorsFault ?? (config.evaluation || config.run9Script || config.run10Script ? 'broken' : config.fault)
      script(path.join(harness, 'run_anchors.sh'), `# ${HARNESS_NOTE}
if [[ -n \${EVAL_MODE:-} ]]; then
${adapterScript(root, 'run_anchors', anchorsFault, config.fault === 'run9-baseline' ? RUN9_RECORDS.baseline : '')}
exit 0
fi
` + emit('out/anchors_measured.json', { anchor: 1 }) +
        emit('out/values.json', [0, 1, 2, 3, 4]) + emit('out/seeds.json', [0, 1, 2, 3, 4]) +
        (config.run8 ? 'mkdir -p out/run\n' + emit('out/run/ensemble.json', readJSON(RUN8_ENSEMBLE.baseline)) : '') +
        // run13's anchor run: one baseline.* run directory and latest-baseline-run.txt.
        (config.run13Data ? `cp -R ${quote(path.join(config.run13Data, 'reproduce'))}/. out/\n` : ''))
      script(path.join(harness, 'run_command.sh'), 'true')
      if (config.evaluation) script(path.join(harness, 'run_evaluation.sh'), `# ${HARNESS_NOTE}\n` +
        adapterScript(root, 'run_evaluation', config.fault, config.fault === 'run9-baseline' ? RUN9_RECORDS.baseline : ''))
      // run9's pre-seal adapter, byte for byte.
      if (config.run9Script) fs.copyFileSync(path.join(RUN9, 'harness', 'run_evaluation.sh'), path.join(harness, 'run_evaluation.sh'))
      // run10's repaired adapter, byte for byte.
      if (config.run10Script) fs.copyFileSync(path.join(RUN10, 'harness', 'run_evaluation.sh'), path.join(harness, 'run_evaluation.sh'))
    }
    if (title === 'adapter-repair') {
      // Writes where the harness agent writes; an isolated view, if supplied, takes precedence.
      const harness = options.isolation?.directory ? path.join(options.isolation.directory, 'harness') : path.join(agent, 'harness')
      event.repairDirectory = harness
      event.harnessBefore = harnessHashes(path.join(agent, 'harness'))
      // What the repair view supplies, before this agent writes: file hashes and parsed JSON.
      const view = options.isolation?.directory
      event.repairView = view ? harnessHashes(view) : null
      event.repairViewJSON = view ? Object.fromEntries(files(view).filter(file => file.endsWith('.json'))
        .map(file => { try { return [path.relative(view, file), readJSON(file)] } catch { return [path.relative(view, file), null] } })) : null
      const recorded = { 'run9-method': RUN9_RECORDS.method, 'run9-baseline': RUN9_RECORDS.baseline }[config.repairFault] || ''
      script(path.join(harness, 'run_evaluation.sh'), '# rewritten by adapter-repair\n' + adapterScript(root, 'repaired', config.repairFault, recorded))
      event.repairedSha = sha(fs.readFileSync(path.join(harness, 'run_evaluation.sh')))
      // Other rewritten scripts must never be accepted, uploaded or run.
      if (config.stray) for (const name of ['setup.sh', 'run_anchors.sh', 'run_command.sh']) {
        script(path.join(harness, name), `printf '%s\\n' stray > out/stray-${name}\nexit 9`)
      }
    }
    if (['tests', 'implement', 'review'].includes(title)) {
      const view = options.isolation?.directory || options.cwd
      assert.ok(view && path.isAbsolute(view), 'author has no absolute private view')
      event.view = view
      if (title === 'tests') {
        const planted = path.join(agent, 'method')
        fs.mkdirSync(planted)
        fs.writeFileSync(path.join(planted, 'isolation-sentinel'), METHOD_SECRET)
        try { event.probe = await isolationProbe(options, root) }
        finally { fs.rmSync(planted, { recursive: true }) }
      } else event.probe = await isolationProbe(options, root)
      event.viewFiles = files(view).map(file => path.relative(view, file))
      event.viewHarness = harnessHashes(path.join(view, 'harness'))
      event.freeze = fs.existsSync(path.join(root, 'control', 'implement', 'tests.json'))
        ? readJSON(path.join(root, 'control', 'implement', 'tests.json')) : null
      event.frozenHash = event.freeze ? treeHash(path.join(agent, 'tests')) : null
      event.testBytesInPrompt = prompt.includes(TEST_SECRET)
      event.methodBytesInPrompt = prompt.includes(METHOD_SECRET)
      const prior = rows(path.join(root, 'calls.jsonl')).filter(call => call.title === title)
      if (title === 'tests') {
        event.viewBaselineOut = manifest(path.join(view, 'baseline-out'))
        const tests = path.join(view, 'tests')
        fs.mkdirSync(tests, { recursive: true })
        fs.writeFileSync(path.join(tests, 'fixture.txt'), TEST_SECRET)
        // Source sentinel becomes part of the frozen tree. No method assertions.
        fs.writeFileSync(path.join(tests, 'isolation-sentinel'), TEST_SECRET)
        let report = { passed: 6, failed: 0, cases: IDS.map(id => ({ id, pass: true, reason_code: null })) }
        if (config.report === 'missing-id') { report.cases.pop(); report.passed-- }
        if (config.report === 'duplicate') report.cases[5].id = report.cases[0].id
        if (config.report === 'extra') report.extra = PRIVATE
        if (config.report === 'counts') report.passed = 7
        if (config.report === 'reason') { report.cases[0].pass = false; report.cases[0].reason_code = 'secret-reason'; report.failed = 1; report.passed = 5 }
        script(path.join(tests, 'run_tests.sh'), `# ${TEST_SECRET}
for key in BASELINE_DIR METHOD_DIR BASELINE_OUT METHOD_OUT; do [[ \${!key} == /* ]]; done
test -f "$BASELINE_OUT/values.json"
test -f "$METHOD_OUT/values.json"
test ! -f "$METHOD_OUT/tests.json"
test -f "$(dirname "$0")/fixture.txt"
python3 -I -c ${quote(BASELINE_SEEN_PY)} "$BASELINE_OUT" ${quote(path.join(root, 'baseline-seen.jsonl'))}
printf '%s\\n' '${PRIVATE}:tests'
python3 - "$BASELINE_OUT" "$METHOD_OUT" <<'OUTPUT_CHECKS'
import json, pathlib, sys
baseline, method = map(pathlib.Path, sys.argv[1:])
expected = json.loads((baseline / 'values.json').read_text())
actual = json.loads((method / 'values.json').read_text())
checks = {
    'dropped_inputs': set(expected) <= set(actual),
    'duplicated_inputs': len(actual) == len(set(actual)),
    'ordering': actual == expected,
    'tail_handling': bool(actual) and actual[-1] == expected[-1],
    'seeds': json.loads((baseline / 'seeds.json').read_text()) == json.loads((method / 'seeds.json').read_text()),
    'equivalence': actual == expected and not (method / 'fail-equivalence').exists(),
}
cases = [dict(id=k, pass_=v, reason_code=None if v else k) for k, v in checks.items()]
for row in cases:
    row['pass'] = row.pop('pass_')
failed = sum(not row['pass'] for row in cases)
(method / 'tests.json').write_text(json.dumps(dict(passed=len(cases)-failed, failed=failed, cases=cases)))
sys.exit(1 if failed else 0)
OUTPUT_CHECKS
${config.report === 'missing' ? 'rm -f out/tests.json' : config.report ? emit('out/tests.json', report) : 'true'}
exit ${config.testExit || 0}`)
        if (config.testSymlink) fs.symlinkSync('fixture.txt', path.join(tests, 'forbidden-link'))
        if (config.run8 === 'contract') {
          // Sealed protocol fixture comes from the test view's PREDICTIONS.json.
          fs.copyFileSync(path.join(view, 'PREDICTIONS.json'), path.join(tests, 'protocol.json'))
          fs.writeFileSync(path.join(tests, 'check_equivalence.py'), CONTRACT_TESTS_PY)
          script(path.join(tests, 'run_tests.sh'), `# ${TEST_SECRET}\nexec python3 -I "$(dirname "$0")/check_equivalence.py"`)
        }
        if (config.run8 === 'frozen') {
          // run8's frozen tests, byte for byte: they require evaluation.json records.
          fs.rmSync(path.join(tests, 'run_tests.sh'))
          for (const name of ['run_tests.sh', 'check_outputs.py', 'protocol.json']) fs.copyFileSync(path.join(RUN8, 'tests', name), path.join(tests, name))
        }
        // run13's frozen tests, byte for byte: they reject more than one baseline ensemble.json.
        if (config.run13Data) for (const name of ['run_tests.sh', 'check_outputs.py']) fs.copyFileSync(path.join(RUN13, 'tests', name), path.join(tests, name))
      }
      if (title === 'implement') {
        const retry = prior.length > 0
        const method = path.join(view, 'method')
        fs.mkdirSync(method, { recursive: true })
        fs.writeFileSync(path.join(method, 'method.patch'), `diff --git a/pin b/pin\n--- a/pin\n+++ b/pin\n@@ -1 +1 @@\n-published\n+changed\n`)
        script(path.join(method, 'setup_method.sh'), `# ${METHOD_SECRET}
for key in BASELINE_DIR METHOD_DIR BASELINE_OUT METHOD_OUT; do [[ \${!key} == /* ]]; done
test "$(cat "$BASELINE_DIR/pin")" = published
test "$(cat "$METHOD_DIR/pin")" = changed
test ! -f "$METHOD_OUT/values.json"
printf '%s\\n' '${PRIVATE}:setup'
${config.setupFailure ? 'exit 7' : 'true'}`)
        script(path.join(method, 'run_method.sh'), `# ${METHOD_SECRET}
test ! -f "$METHOD_OUT/values.json"
printf '%s\\n' '${PRIVATE}:run'
${emit('out/values.json', [0, 1, 2, 3, 4])}
${emit('out/seeds.json', [0, 1, 2, 3, 4])}
${config.run8 ? 'mkdir -p out/run\n' + emit('out/run/ensemble.json', readJSON(RUN8_ENSEMBLE.method[retry ? 1 : 0])) : 'true'}
${config.run13Data ? ['ensemble.json', 'stdout.log'].map(file => `cp ${quote(path.join(config.run13Data, 'reproduce', RUN13_RUN, file))} out/${file}`).join('\n') : 'true'}
${(config.repair || config.failTwice) && (!retry || config.failTwice) ? 'touch out/fail-equivalence' : 'true'}
${config.tamperBaseline ? 'printf modified > "$BASELINE_DIR/pin"' : 'true'}
${config.tamperTests ? 'chmod u+w payload/tests/run_tests.sh; printf "# tampered\\n" >> payload/tests/run_tests.sh' : 'true'}
${config.tamperPayload ? 'printf "# tampered\\n" >> payload/method/run_method.sh' : 'true'}
${config.runFailure ? 'exit 7' : 'true'}`)
        if (config.badPatch) fs.writeFileSync(path.join(method, 'method.patch'), 'invalid patch\n')
        if (config.tamperSeal === 'author') fs.appendFileSync(path.join(agent, 'PREDICTIONS.json'), ' ')
      }
      if (title === 'review') {
        event.reviewPayload = readJSON(path.join(view, 'implement-payload.json'))
        event.reviewSeal = readJSON(path.join(view, 'seal.json'))
        json = config.badReview ? { pass: true, reason_codes: ['other'] }
          : { pass: !config.rejectReview, reason_codes: config.rejectReview ? ['changes_protocol'] : [] }
        if (config.tamperSeal === 'review') fs.appendFileSync(path.join(agent, 'PREDICTIONS.json'), ' ')
        if (config.newSeal) {
          const seals = path.join(root, 'control', 'seals')
          writeJSON(path.join(seals, '0002.json'), readJSON(path.join(seals, '0001.json')))
        }
      }
    }
    fs.appendFileSync(path.join(root, 'calls.jsonl'), JSON.stringify(event) + '\n')
    return { text: JSON.stringify(json), json, jsonError: null, sessionID: event.returnedSession,
      tokens: { input: 10, output: 5 }, tokens_known: true, cost: 0, tools: 0, ms: 1, errors: [], refusal: false }
  },
  async exportSession(id, file) { fs.writeFileSync(file, '{}') },
}
function fixture(root, config) {
  const agent = path.join(root, 'agent')
  writeJSON(path.join(agent, 'intake', 'anchors.json'), [{ id: 'anchor', quantity: 'sum', source: 'fixture', published_value: 1, tolerance: 0 }])
  for (const [name, value] of Object.entries({
    benchmark: { name: PRIVATE }, data: { available: true, note: INTAKE_NOTE },
    baseline: { repo: 'fixture', pin: 'v1', build_commands: ['true'], run_commands: ['true'], published_configuration: { n: 5 } },
    EXECUTION: { representative_scale: { n: 5 }, inputs: ['data/input'], outputs: ['values.json'], timing_scope: 'whole run',
      timeout_s: 10, timeouts: { setup_method: 11, run_method: 12, run_tests: 13 },
      stage_budgets_s: { method_setup: 21, method_run: config.methodRun || 22, tests: 23,
        ...(config.evaluateBudget ? { evaluate: config.evaluateBudget } : {}) } },
  })) writeJSON(path.join(agent, 'intake', name + '.json'), value)
  // An executable sealed protocol (SCHEMAS.md "Evaluate: executable sealed protocol"), so the
  // baseline adapter smoke has sealed input ids, seeds, metric names, scope and GPU count.
  // Seeds and ids are deliberately unsorted so order is observable.
  const stochastic = config.seal !== 'deterministic'
  const predictions = { predictions: [{ method: 'batching', expected_speedup_interval: { low: 1.1, high: 1.2 },
    outcome_vs_compute_points: [1, 2, 4].map(compute_budget => ({ compute_budget, predicted_outcome: 1, uncertainty: 'exact' })) }],
    infeasible_methods: [], outputs_stochastic: stochastic,
    equivalence_metrics: [{ name: 'value_sum', source: SEAL_SOURCE, tolerance: { abs: stochastic ? 0.5 : 0 } },
      { name: 'value_max', source: 'fixture requirement', tolerance: { abs: stochastic ? 0.5 : 0 } }],
    paired_seed_tests: stochastic ? { kind: 'paired_median', seeds: [7, 3, 5, 1, 9, 11] } : { kind: 'deterministic', justification: 'fixture is deterministic' },
    sample_sizes: { inputs: 2, seeds: stochastic ? 6 : 1 },
    confidence_rule: { equivalence: { kind: 'paired_median', confidence: 0.95 }, performance: { kind: 'paired_median', confidence: 0.95 } },
    hardware_cost_basis: { baseline_gpus: 1, method_gpus: 1, budget_unit: 'gpu_s' },
    timing_scope: { kind: 'reported_wall', gpu_synchronization: 'adapter', description: 'whole run' },
    minimum_worthwhile_gain: 1.1, evaluation_inputs: { ids: ['input-b', 'input-a'], pin: 'fixture inputs' },
    splits: { evaluation: [0, 5] }, compute_budgets: [1, 2, 4], repetitions: 5, warmup: 1,
    scheduling_order: { kind: 'randomized_pairs', seed: 42 }, equal_outcome_target: { not_applicable: true, reason: 'fixed-work fixture' },
    baseline_invocation_s: { seconds: 0.01, source: 'fixture: one baseline equivalence invocation, 0.01 s' } }
  if (config.run8) Object.assign(predictions, readJSON(path.join(RUN8, 'PREDICTIONS.json')))
  if (config.run9 || config.run9Script) Object.assign(predictions, readJSON(path.join(RUN9, 'PREDICTIONS.json')))
  if (config.run10Script) Object.assign(predictions, readJSON(path.join(RUN10, 'PREDICTIONS.json')))
  if (config.run12) Object.assign(predictions, readJSON(path.join(RUN12, 'PREDICTIONS.json')))
  // Cost-projection fields (warmup, repetitions, compute_budgets, hardware_cost_basis,
  // equal_outcome_target); prediction points follow any changed compute budgets.
  if (config.sealPatch) {
    Object.assign(predictions, config.sealPatch)
    predictions.predictions = predictions.predictions.map(row => ({ ...row,
      outcome_vs_compute_points: predictions.compute_budgets.map(compute_budget => ({ compute_budget, predicted_outcome: 1, uncertainty: 'exact' })) }))
  }
  writeJSON(path.join(agent, 'PREDICTIONS.json'), predictions)
  const frozen = path.join(root, 'control', 'seals', 'frozen.json')
  writeJSON(frozen, predictions)
  fs.chmodSync(frozen, 0o444)
  writeJSON(path.join(root, 'control', 'seals', '0001.json'), { sha256: sha(fs.readFileSync(frozen)), path: frozen, utc: new Date().toISOString() })
  writeJSON(path.join(agent, 'proposal.json'), { method: 'batching', rationale: PRIVATE,
    plan_steps: ['Preserve paired seeds and input order.'], files_expected: ['pin'], risks: [] })
  writeJSON(path.join(agent, 'profile-packet.json'), { stages: [
    { stage: 'prepare', wall_s: 3, gpu_s: null }, { stage: 'transfer', wall_s: 4, gpu_s: null }, { stage: 'compute', wall_s: 3, gpu_s: null },
  ], total_wall_s: 10, timed_fraction: 1, gpu_telemetry: true, gpu_count: 1 })
  // Plant each sentinel only while its opposing role runs. Remove it before the
  // harness copies author outputs; otherwise the stage's restart guard fires.
  if (config.tamperSeal === 'initial') fs.appendFileSync(path.join(agent, 'PREDICTIONS.json'), ' ')
}
// Runs the real pipeline against the fake box and this file's WF_STUB; shared with
// tools/test_m5_adapter_smoke.js.
async function launch(scratch, name, config = {}) {
  const root = path.join(scratch, name)
  fs.mkdirSync(root, { recursive: true })
  fs.symlinkSync(path.join(ROOT, 'm5'), path.join(root, 'm5'), 'dir')
  fixture(root, config)
  const home = path.join(root, 'fixture-home'), box = path.join(root, 'box')
  fs.mkdirSync(box, { recursive: true })
  writeJSON(path.join(home, '.codex', 'auth.json'), { access_token: CREDENTIAL })
  script(path.join(home, '.cache', 'metis-serve', 'box.sh'), 'exit 99')
  const bin = path.join(root, 'bin')
  // Both local receipt telemetry and remote scripts see only this fake GPU tool.
  script(path.join(bin, 'nvidia-smi'), 'exit 1')
  // Stands in for profiling and later baseline runs (SCHEMAS.md reproduce bullet): once the
  // `reproduce-freeze` receipt exists, before the next box command, copy `pollute/` over remote out/
  // (adding files and rewriting some) and apply any reproduce-out tamper ('missing' or 'symlink').
  if (config.pollute) fs.cpSync(config.pollute, path.join(root, 'pollute'), { recursive: true })
  script(path.join(bin, 'box'), `command=\${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}
export PATH="$M5_IMPLEMENT_BIN:$PATH"
cd "$BOX_ROOT"
printf '%s\\n' "$command" >> "$M5_BOX_COMMANDS"
frozen=false
for receipt in "$M5_IMPLEMENT_ROOT"/control/receipts/*-reproduce-freeze.json; do [[ ! -e $receipt ]] || frozen=true; done
if [[ $frozen == true && ! -e $M5_IMPLEMENT_ROOT/after-freeze ]]; then
  : > "$M5_IMPLEMENT_ROOT/after-freeze"
  for remote in "$BOX_ROOT"/m5-*; do
    [[ -d $remote/out ]] || continue
    [[ ! -d $M5_IMPLEMENT_ROOT/pollute ]] || cp -R "$M5_IMPLEMENT_ROOT/pollute/." "$remote/out/"
    case ${quote(config.freezeTamper || 'none')} in
      missing) rm -rf "$remote/reproduce-out" ;;
      symlink) rm -rf "$remote/reproduce-out"; ln -s out "$remote/reproduce-out" ;;
    esac
  done
fi
bash -c "$command"
if [[ $command == *timeout* ]]; then
  for ((i=0; i<1000; i++)); do
    pending=false
    for file in "$BOX_ROOT"/m5-*/*.sh; do
      [[ -f $file ]] || continue
      [[ -f \${file%.sh}.rc ]] || pending=true
    done
    [[ $pending == true ]] || break
    sleep 0.01
  done
fi`)
  if (config.smokeJson) {
    writeJSON(path.join(root, 'smoke-inject.json'), config.smokeJson)
    fs.writeFileSync(path.join(root, 'smoke-inject.py'), SMOKE_INJECT_PY)
  }
  script(path.join(bin, 'fetch'), 'source=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\n' +
    (config.fetchFailure ? '[[ $source != *-run-method.log ]] || exit 7\n' : '') +
    (config.smokeJson ? `cp -r -- "$source" "$2"\nexec python3 -I ${quote(path.join(root, 'smoke-inject.py'))} ${quote(root)} "$2"` : 'exec cp -r -- "$source" "$2"'))
  const args = path.join(root, 'control', 'args.json')
  writeJSON(args, { run_root: root, raid: 'implement-test', tag: 'implement-test', stub: {
    intake: 'PASS', profile: 'PASS', seal: 'PASS', propose: 'PASS', evaluate: 'PASS', takeaways: 'PASS',
  }, ...(config.argsBudgets ? { stage_budgets_s: config.argsBudgets } : {}) })
  const output = path.join(root, 'agent', 'wf')
  const stdout = fs.openSync(path.join(root, 'stdout'), 'w'), stderr = fs.openSync(path.join(root, 'stderr'), 'w')
  let child
  try {
    child = await new Promise(resolve => {
      const proc = spawn(process.execPath, [path.join(ROOT, 'idea', 'wf.js'), '--script', path.join(ROOT, 'm5', 'pipeline.js'),
        '--args', args, '--out', output, '--disable-family', 'claude'], { cwd: root, timeout: 180000,
        stdio: ['ignore', stdout, stderr], env: { ...process.env, HOME: home, PATH: bin + path.delimiter + process.env.PATH,
          WF_STUB: __filename, M5_IMPLEMENT_ROOT: root, M5_IMPLEMENT_CONFIG: JSON.stringify(config),
          M5_RAIDS_LEDGER: path.join(scratch, 'ledger.jsonl'), BOX_ROOT: box, M5_IMPLEMENT_BIN: bin,
          M5_BOX_COMMANDS: path.join(root, 'box-commands'), BOX: path.join(bin, 'box'), FETCH: path.join(bin, 'fetch'),
          // A failing fetch is retried after BOXRUN_FETCH_WAIT_S; keep the fixture fast.
          ...(config.fetchFailure ? { BOXRUN_FETCH_WAIT_S: '0' } : {}) } })
      let error
      proc.on('error', value => { error = value })
      proc.on('close', (status, signal) => resolve({ status, signal, error }))
    })
  } finally { fs.closeSync(stdout); fs.closeSync(stderr) }
  const records = rows(path.join(root, 'operator', 'signatures.jsonl'))
  const record = records.find(row => row.signature?.stage === 'implement')
  const allCalls = rows(path.join(root, 'calls.jsonl'))
  const calls = allCalls.filter(call => ['tests', 'implement', 'review'].includes(call.title))
  return { root, child, output, records, record, calls, allCalls, config }
}
// Frozen trees require owner write permission before recursive cleanup.
function removeScratch(scratch) {
  function writable(directory) {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      if (entry.isDirectory()) { const child = path.join(directory, entry.name); fs.chmodSync(child, 0o700); writable(child) }
    }
  }
  writable(scratch)
  fs.rmSync(scratch, { recursive: true, force: true })
}
Object.assign(module.exports, { fixtures: { launch, removeScratch, rows, files, sha, readJSON, writeJSON, treeHash,
  RUN9, RUN9_RECORDS, RUN10, RUN12, run10Fakes, SEAL_SOURCE, INTAKE_NOTE, HARNESS_NOTE, PRIVATE } })
if (require.main !== module) return

const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_implement_'))
let checks = 0, failures = 0
function check(label, fn) {
  checks++
  try { fn(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${error.message}`) }
}
async function execute(name, config = {}) {
  const { root, child, output, records, record, calls } = await launch(scratch, name, config)
  check(`${name}: workflow completes`, () => {
    assert.ifError(child.error)
    assert.equal(child.status, 0, `status=${child.status} signal=${child.signal}`)
    const result = readJSON(path.join(output, 'result.json'))
    assert.ok(!result.error, JSON.stringify(result.error))
    assert.ok(record, 'no implement signature (upstream fixture failed)')
    assert.equal(records.find(row => row.signature?.stage === 'reproduce')?.signature.status, 'PASS')
  })
  check(`${name}: operator contains no private source, credentials or feedback`, () => {
    const operator = path.join(root, 'operator')
    function inspect(directory) {
      for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
        assert.ok(!entry.isSymbolicLink(), 'operator contains a symlink')
        for (const secret of [PRIVATE, TEST_SECRET, METHOD_SECRET, CREDENTIAL]) assert.ok(!entry.name.includes(secret), 'sentinel in filename')
        if (entry.isDirectory()) inspect(path.join(directory, entry.name))
      }
    }
    inspect(operator)
    for (const file of files(operator)) {
      const text = fs.readFileSync(file, 'utf8')
      for (const secret of [PRIVATE, TEST_SECRET, METHOD_SECRET, CREDENTIAL, 'reason_code_counts']) assert.ok(!text.includes(secret), path.basename(file))
    }
  })
  check(`${name}: credentials removed after each isolated call`, () => {
    for (const call of calls) assert.deepEqual(call.credentialsBefore, [])
    assert.deepEqual(credentialsGone(root), [])
    for (const call of calls) assert.equal(fs.existsSync(call.view), false, 'private view retained')
  })
  if (name === 'happy' || config.repair) check(`${name}: provider credential copies removed after every probe [requires bubblewrap]`, () => {
    for (const call of calls) {
      assert.ok(call.probe && 'home' in call.probe, call.probe?.diagnostic || 'probe did not run')
      assert.equal(call.probe.authPresent, true, 'probe did not receive fixture authentication')
      assert.equal(call.probe.credentialsRemoved, true, 'provider HOME was not disposable or survives provider return')
      if (!call.isolation.box_access) assert.equal(call.probe.boxReadable, false, 'unprivileged role sees box credentials')
    }
  })
  return { root, calls, record, records, config }
}
function verdict(name, run, errorClass, expected) {
  check(`${name}: implement ${errorClass || 'PASS'} and downstream stop`, () => {
    assert.equal(run.record?.signature.status, errorClass ? 'FAIL' : 'PASS')
    if (errorClass) {
      assert.ok([].concat(errorClass).includes(run.record.signature.error_class), `unexpected error_class: ${run.record.signature.error_class}`)
      assert.equal(run.record.signature.exit_code, 2)
    }
    assert.equal(run.records.find(row => row.signature?.stage === 'evaluate')?.signature.status, errorClass ? 'SKIPPED' : 'PASS')
    assert.equal(run.records.find(row => row.signature?.stage === 'takeaways')?.signature.status, 'PASS')
    const facts = run.record.facts
    assert.deepEqual(Object.keys(facts).sort(), ['patch_applies', 'tests_pass', 'blind_tests', 'launch_review_pass', 'tokens_known', 'gpu_busy_known'].sort())
    if (expected) for (const [key, value] of Object.entries(expected)) assert.equal(facts[key], value, key)
  })
}
function authorChecks(run) {
  const { root, calls } = run
  check('independent authors use private fresh sessions and exact permissions', () => {
    assert.equal(calls.filter(call => call.title === 'tests').length, 1)
    assert.equal(calls[0].title, 'tests')
    assert.equal(new Set(calls.map(call => call.returnedSession)).size, calls.length)
    assert.equal(new Set(calls.map(call => call.view)).size, calls.length)
    for (const call of calls) {
      // Fresh/repairable are workflow options, not runner options. Observe their
      // effects: no resume, distinct views, and no extra provider repair calls.
      for (const key of ['session', 'sessionID', 'resume', 'resumeSession']) assert.ok(!call[key], `resumed via ${key}`)
      assert.equal(call.role, call.title === 'review' ? 'qt-bare' : 'ls-writer')
      assert.equal(call.isolation.box_access, call === calls.find(row => row.title === 'implement'))
      if (call.title === 'tests') {
        assert.equal(call.freeze, null)
        assert.equal(call.methodBytesInPrompt, false)
        assert.ok(!call.viewFiles.some(file => file.startsWith('method/')))
      } else if (call.title === 'implement') {
        assert.ok(call.freeze, 'method started before freeze')
        assert.equal(call.freeze.sha256, call.frozenHash)
        assert.equal(call.testBytesInPrompt, false)
        assert.ok(!call.viewFiles.some(file => file.startsWith('tests/')))
      }
    }
  })
  check('frozen tests receipt records exact file hashes and read-only modes', () => {
    const directory = path.join(root, 'agent', 'tests'), receiptFile = path.join(root, 'control', 'implement', 'tests.json')
    const receipt = readJSON(receiptFile)
    assert.deepEqual(Object.keys(receipt).sort(), ['sha256', 'files', 'seal_sha256', 'utc'].sort())
    assert.equal(receipt.sha256, treeHash(directory))
    assert.equal(fs.statSync(receiptFile).mode & 0o777, 0o444)
    assert.equal(fs.statSync(directory).mode & 0o777, 0o555)
    const expected = files(directory).map(file => ({ path: path.relative(directory, file).split(path.sep).join('/'), sha256: sha(fs.readFileSync(file)) }))
    assert.deepEqual(receipt.files, expected)
    for (const file of files(directory)) assert.equal(fs.statSync(file).mode & 0o777, 0o444)
    const seal = readJSON(path.join(root, 'control', 'seals', '0001.json'))
    assert.equal(receipt.seal_sha256, seal.sha256)
  })
}
function receiptChecks(run) {
  check('setup, method and tests run through boxrun with valid receipts', () => {
    const receipts = files(path.join(run.root, 'control', 'receipts')).filter(file => file.endsWith('.json')).map(file => ({ file, value: readJSON(file) }))
    for (const operation of ['implement-baseline', 'implement-state', 'implement-upload', 'implement-patch', 'setup-method', 'run-method', 'run-tests']) {
      assert.ok(receipts.some(({ file }) => new RegExp('^\\d{4}-' + operation + '\\.json$').test(path.basename(file))), operation)
    }
    for (const { file, value } of receipts) {
      assert.equal(value.name, path.basename(file, '.json'))
      assert.equal(value.rc, 0, path.basename(file))
      assert.equal(value.fetched, true)
      assert.equal(value.timed_out, false)
      assert.ok(Number.isInteger(value.wall_s) && value.wall_s >= 0)
      assert.equal(value.gpu_busy_known, false, 'host GPU tool escaped hermetic PATH')
      assert.ok(files(path.join(run.root, 'agent', 'results')).some(log => path.basename(log) === value.name + '.log'), 'missing fetched log')
    }
  })
  check('payload hashes match final source, frozen tests, seal and stage budgets', () => {
    const payload = readJSON(path.join(run.root, 'agent', 'implement-payload.json'))
    const review = run.calls.find(call => call.title === 'review')
    assert.deepEqual(review?.reviewPayload, payload)
    assert.equal(review.reviewSeal.receipt, '0001.json')
    assert.equal(review.reviewSeal.sha256, payload.seal_sha256)
    assert.equal(review.methodBytesInPrompt, true)
    assert.equal(review.testBytesInPrompt, false)
    assert.deepEqual(Object.keys(payload).sort(), ['attempt', 'remote_directory', 'baseline_directory', 'method_directory', 'baseline_outputs', 'method_outputs', 'tests_sha256', 'seal_sha256', 'method_files', 'timeouts'].sort())
    assert.equal(payload.attempt, 1)
    assert.ok(path.isAbsolute(payload.remote_directory))
    assert.deepEqual([payload.baseline_directory, payload.method_directory, payload.baseline_outputs, payload.method_outputs], ['baseline-published', 'method', 'baseline-out', 'out'])
    assert.deepEqual(payload.timeouts, { setup_method: 21, run_method: 22, run_tests: 23 })
    assert.equal(payload.tests_sha256, treeHash(path.join(run.root, 'agent', 'tests')))
    assert.equal(payload.seal_sha256, readJSON(path.join(run.root, 'control', 'seals', '0001.json')).sha256)
    assert.deepEqual(payload.method_files.map(row => row.path).sort(), ['method.patch', 'run_method.sh', 'setup_method.sh'])
    for (const row of payload.method_files) assert.equal(row.sha256, sha(fs.readFileSync(path.join(run.root, 'agent', 'method', row.path))))
    const remote = path.join(run.root, 'box', path.basename(payload.remote_directory))
    const baseline = readJSON(path.join(run.root, 'control', 'implement', 'baseline.json'))
    assert.deepEqual(baseline, { baseline_sha256: treeHash(path.join(remote, 'baseline-published')), data_sha256: treeHash(path.join(remote, 'data')), baseline_outputs_sha256: treeHash(path.join(remote, 'baseline-out')) })
    assert.equal(fs.readFileSync(path.join(remote, 'baseline-published', 'pin'), 'utf8'), 'published\n')
    assert.equal(fs.readFileSync(path.join(remote, 'method', 'pin'), 'utf8'), 'changed\n')
    assert.equal(treeHash(path.join(remote, 'payload', 'tests')), payload.tests_sha256)
    assert.equal(readJSON(path.join(run.root, 'agent', 'results', 'implement', 'out', 'tests.json')).failed, 0)
  })
}
// Meaning, not wording: each rule must appear within two adjacent sentences.
function assertTestAuthorRules(prompt) {
  const sentences = prompt.split(/(?<=[.!?;])\s+|\n+/).filter(Boolean)
  const windows = sentences.map((sentence, i) => sentence + ' ' + (sentences[i + 1] || ''))
  const rules = [
    ['tests see only BASELINE_OUT and METHOD_OUT', [/BASELINE_OUT/, /METHOD_OUT/, /\b(only|exactly two|two sets)\b/i]],
    ['one method run at the representative scale, inputs and seeds', [/\b(one|single)\b[^.]*\bmethod\b|\bmethod\b[^.]*\b(one|single)\b/i, /representative/i, /\binputs?\b/i, /\bseeds?\b/i]],
    ['evaluation records, held-out seeds, timing repetitions and compute budgets exist only in evaluate',
      [/evaluation\.json|evaluation records/i, /held-out seeds/i, /timing repetitions|repetitions/i, /compute budgets?/i, /\bevaluat(e|ion)\b[^.]*\bonly\b|\bonly\b[^.]*\bevaluate\b/i]],
    ['no case may require evaluation-only data', [/\b(no|never|must not|may not|cannot|do not)\b[^.]*\brequire/i, /evaluation\.json|evaluation records|held-out|compute budgets?|repetitions/i]],
    ['equivalence applies sealed margins and confidence rule to the representative pairs', [/equivalence/i, /equivalence_metrics|margins?/i, /confidence[ _]rule|sealed confidence/i, /pairs?/i]],
    ['confidence is for the number of pairs available', [/confidence/i, /number of pairs|pairs available|available pairs/i]],
    ['fails only when an interval is disjoint from (-margin, +margin)', [/\bfail/i, /\bonly\b/i, /disjoint|entirely outside|does not overlap|no overlap/i, /margin/i]],
    ['deterministic seal fails when a paired difference exceeds the tolerance', [/deterministic/i, /paired difference|difference/i, /exceed|greater than|larger than/i, /tolerance/i]],
    ['an overlapping interval passes', [/overlap/i, /\bpass|cannot reject|does not reject|not reject/i]],
    ['too few pairs for a finite interval passes', [/too few|insufficient|fewer|not enough/i, /pairs?/i, /finite|interval/i, /\bpass|cannot reject|does not reject|not reject/i]],
    ['evaluate decides acceptance', [/accept/i, /\bevaluate\b/i, /decide|determin/i]],
  ]
  const missing = rules.filter(([, patterns]) => !windows.some(text => patterns.every(pattern => pattern.test(text)))).map(([label]) => label)
  assert.deepEqual(missing, [], 'test author prompt omits: ' + missing.join('; '))
}
function run8RuleChecks() {
  // SCHEMAS.md: "It fails only when the pairs reject equivalence ... An interval that
  // overlaps (−margin, +margin), or pairs too few for a finite interval, cannot reject".
  const seal = readJSON(path.join(RUN8, 'PREDICTIONS.json'))
  const baseline = readJSON(RUN8_ENSEMBLE.baseline).replicas
  const methods = RUN8_ENSEMBLE.method.map(file => readJSON(file).replicas)
  check('run8 fixture: eight representative pairs per metric, paired by seeds 1000..1007', () => {
    assert.equal(seal.outputs_stochastic, true)
    assert.equal(seal.paired_seed_tests.kind, 'paired_median')
    assert.deepEqual(seal.confidence_rule.equivalence, { confidence: 0.95, kind: 'paired_median' })
    assert.equal(seal.equivalence_metrics.length, 2)
    for (const replicas of [baseline, ...methods]) assert.deepEqual(replicas.map(row => row.seed), [1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007])
    // At n=8, 95% gives k=1 with or without Bonferroni across the two metrics,
    // so the result below does not depend on that choice: the interval is [min, max].
    for (const metrics of [1, 2]) assert.deepEqual(orderStatisticInterval([1, 2, 3, 4, 5, 6, 7, 8], 0.95, metrics), [1, 8])
  })
  check('run8 reference rule: recorded pairs overlap (-margin, +margin) and are not rejected', () => {
    for (const method of methods) {
      for (const { name, tolerance: { abs: margin } } of seal.equivalence_metrics) {
        const [low, high] = orderStatisticInterval(pairedDiffs(baseline, method, name), 0.95, 2)
        assert.ok(low < margin && high > -margin, `${name} interval [${low}, ${high}] disjoint from ±${margin}`)
      }
      assert.equal(rejectsEquivalence(baseline, method, seal), false)
    }
  })
  check('run8 reference rule: pairs shifted twice the margin clear of zero are rejected', () => {
    const shifted = (method, direction) => method.map(row => {
      const out = { ...row }
      for (const { name, tolerance: { abs: margin } } of seal.equivalence_metrics) {
        const diffs = pairedDiffs(baseline, method, name)
        // Move every difference so the nearest one lies 2×margin from zero.
        const offset = direction > 0 ? 2 * margin - Math.min(...diffs) : -2 * margin - Math.max(...diffs)
        out[name] = row[name] + offset
      }
      return out
    })
    for (const method of methods) for (const direction of [1, -1]) {
      for (const metric of seal.equivalence_metrics) {
        const only = { ...seal, equivalence_metrics: [metric] }
        assert.equal(rejectsEquivalence(baseline, shifted(method, direction), only), true, `${metric.name} ${direction}`)
      }
    }
    // Documented on recorded data: a uniform +2×margin shift is not enough, because
    // the n=8 interval spans the full range of differences (here > 4×margin).
    const uniform = methods[0].map(row => ({ ...row, final_potential_kj_mol: row.final_potential_kj_mol + 2 * seal.equivalence_metrics[0].tolerance.abs }))
    assert.equal(rejectsEquivalence(baseline, uniform, { ...seal, equivalence_metrics: [seal.equivalence_metrics[0]] }), false)
  })
  check('run8 reference rule: deterministic zero tolerance rejects any nonzero difference, accepts identity', () => {
    const deterministic = { ...seal, paired_seed_tests: { kind: 'deterministic', justification: 'fixture' },
      equivalence_metrics: seal.equivalence_metrics.map(metric => ({ ...metric, tolerance: { abs: 0 } })) }
    for (const method of methods) assert.equal(rejectsEquivalence(baseline, method, deterministic), true)
    const nudged = baseline.map((row, i) => i === 3 ? { ...row, mean_potential_kj_mol: row.mean_potential_kj_mol + 1e-9 } : row)
    assert.equal(rejectsEquivalence(baseline, nudged, deterministic), true)
    assert.equal(rejectsEquivalence(baseline, baseline.map(row => ({ ...row })), deterministic), false)
  })
  check('run8 reference rule: three pairs at 95% give no finite interval and are not rejected', () => {
    const three = methods[0].slice(0, 3).map(row => ({ ...row, final_potential_kj_mol: row.final_potential_kj_mol + 1e6, mean_potential_kj_mol: row.mean_potential_kj_mol + 1e6 }))
    for (const metrics of [1, 2]) assert.equal(orderStatisticInterval(pairedDiffs(baseline, three, 'final_potential_kj_mol'), 0.95, metrics), null)
    assert.equal(rejectsEquivalence(baseline, three, seal), false)
  })
  check('run8 contract checker: python fixture agrees with the reference rule', () => {
    // The fixture test script used in the run8-contract scenario must discriminate,
    // otherwise its PASS through implement would be vacuous.
    const work = fs.mkdtempSync(path.join(scratch, 'run8-checker-'))
    fs.writeFileSync(path.join(work, 'check_equivalence.py'), CONTRACT_TESTS_PY)
    fs.copyFileSync(path.join(RUN8, 'PREDICTIONS.json'), path.join(work, 'protocol.json'))
    const shift = 3000 // beyond both margins plus the observed spread for both metrics
    for (const [label, replicas, expected] of [
      ['recorded', methods[0], 0],
      ['shifted', methods[0].map(row => ({ ...row, final_potential_kj_mol: row.final_potential_kj_mol + shift })), 1],
    ]) {
      const b = path.join(work, label, 'baseline'), m = path.join(work, label, 'method')
      writeJSON(path.join(b, 'run', 'ensemble.json'), { replicas: baseline })
      writeJSON(path.join(m, 'run', 'ensemble.json'), { replicas })
      assert.equal(rejectsEquivalence(baseline, replicas, seal), expected === 1, label)
      const result = spawnSync('python3', ['-I', path.join(work, 'check_equivalence.py')], { cwd: work, encoding: 'utf8',
        env: { ...process.env, BASELINE_OUT: b, METHOD_OUT: m } })
      assert.equal(result.status, expected, `${label}: ${result.stderr}`)
      const equivalence = readJSON(path.join(m, 'tests.json')).cases.find(row => row.id === 'equivalence')
      assert.deepEqual(equivalence, { id: 'equivalence', pass: !expected, reason_code: expected ? 'equivalence' : null })
    }
  })
}
function run8FrozenTestCheck() {
  // SCHEMAS.md: "Evaluation records (`evaluation.json`), held-out seeds, timing repetitions
  // and compute budgets exist only in evaluate, and no case may require them."
  check('run8 recorded implement outputs hold no evaluation.json; run8 frozen tests cannot pass on them', () => {
    const results = path.join(RUN8, 'results', 'implement')
    assert.ok(fs.existsSync(results), 'run8 evidence missing')
    assert.deepEqual(files(results).filter(file => path.basename(file) === 'evaluation.json'), [])
    const work = fs.mkdtempSync(path.join(scratch, 'run8-frozen-'))
    for (const name of ['check_outputs.py', 'protocol.json']) fs.copyFileSync(path.join(RUN8, 'tests', name), path.join(work, name))
    for (const method of RUN8_ENSEMBLE.method) {
      fs.rmSync(path.join(work, 'out'), { recursive: true, force: true })
      const result = spawnSync('python3', ['-I', path.join(work, 'check_outputs.py')], { cwd: work, encoding: 'utf8',
        env: { ...process.env, BASELINE_OUT: path.dirname(path.dirname(RUN8_ENSEMBLE.baseline)), METHOD_OUT: path.dirname(path.dirname(method)) } })
      assert.equal(result.status, 1, result.stderr)
      const report = readJSON(path.join(work, 'out', 'tests.json'))
      assert.deepEqual(report.cases.find(row => row.id === 'equivalence'), { id: 'equivalence', pass: false, reason_code: 'missing_output' })
      // Every failure is the evaluation-record requirement; the output-shape cases pass.
      assert.deepEqual(report.cases.filter(row => !row.pass).map(row => row.id), ['equivalence'])
    }
  })
}
// The shared remote /tmp/m5-<uuid> run directory, mapped into the case's fake box.
function remoteDirectory(root) {
  const box = path.join(root, 'box')
  const directories = fs.readdirSync(box).filter(entry => entry.startsWith('m5-') && fs.existsSync(path.join(box, entry, 'harness')))
  assert.equal(directories.length, 1, `expected one remote run directory: ${directories}`)
  return path.join(box, directories[0])
}
const receiptOperations = root => fs.readdirSync(path.join(root, 'control', 'receipts')).sort()
  .filter(file => file.endsWith('.json')).map(file => file.slice(5, -5))
// SCHEMAS.md reproduce bullet: on PASS, one `reproduce-freeze` under the setup budget copies the anchor
// run's out/ to reproduce-out/, and the local A/results/reproduce/out/ holds the same outputs. Implement
// snapshot bullet: baseline-out/ is a copy of reproduce-out/, never the current out/. Views bullet: the
// test view's baseline-out/ is a copy of A/results/reproduce/out/, so frozen tests run against the
// baseline outputs their author saw. `pollution` is the directory the fake box copied over out/ after
// the freeze (profiling, probes and further baseline runs), or null.
function frozenBaselineChecks(name, run, pollution) {
  const { root, calls, config } = run
  check(`${name}: reproduce freezes its outputs once, after the anchor run, under the setup budget`, () => {
    const operations = receiptOperations(root)
    assert.equal(operations.filter(operation => operation === 'reproduce-freeze').length, 1, operations.join(','))
    const freeze = operations.indexOf('reproduce-freeze'), anchors = operations.lastIndexOf('anchors')
    assert.ok(anchors >= 0 && anchors < freeze, 'freeze must follow the anchor run')
    assert.ok(operations.slice(anchors + 1, freeze).every(operation => operation === 'upload'), operations.slice(anchors + 1, freeze).join(','))
    assert.ok(freeze < operations.indexOf('implement-baseline'), 'implement snapshot before the freeze')
    const receipt = readJSON(path.join(root, 'control', 'receipts', fs.readdirSync(path.join(root, 'control', 'receipts'))
      .find(file => /^\d{4}-reproduce-freeze\.json$/.test(file))))
    assert.equal(receipt.budget_s, config.argsBudgets?.setup ?? 1200, 'freeze must use the setup budget')
    assert.equal(receipt.rc, 0)
    assert.equal(receipt.fetched, true)
  })
  check(`${name}: baseline-out, BASELINE_OUT and the test view hold exactly the frozen reproduce outputs`, () => {
    const remote = remoteDirectory(root)
    assert.ok(!fs.lstatSync(path.join(remote, 'reproduce-out')).isSymbolicLink(), 'reproduce-out is a symlink')
    const frozen = manifest(path.join(remote, 'reproduce-out'))
    assert.ok(frozen && Object.keys(frozen).length, 'remote reproduce-out missing or empty')
    assert.deepEqual(manifest(path.join(root, 'agent', 'results', 'reproduce', 'out')), frozen, 'local A/results/reproduce/out differs from remote reproduce-out')
    assert.deepEqual(manifest(path.join(remote, 'baseline-out')), frozen, 'remote baseline-out is not a copy of reproduce-out')
    const author = calls.filter(call => call.title === 'tests')
    assert.equal(author.length, 1)
    assert.deepEqual(author[0].viewBaselineOut, frozen, 'test view baseline-out differs from the frozen outputs')
    // run13's byte-for-byte tests do not record BASELINE_OUT; their own verdict is checked instead.
    if (!config.run13Data) {
      const seen = rows(path.join(root, 'baseline-seen.jsonl'))
      assert.ok(seen.length >= 1, 'frozen tests never recorded BASELINE_OUT')
      for (const row of seen) assert.deepEqual(row, author[0].viewBaselineOut, 'BASELINE_OUT seen by the tests differs from the test view')
    }
  })
  if (pollution) check(`${name}: files added or rewritten in out/ after reproduce never reach baseline-out`, () => {
    assert.ok(fs.existsSync(path.join(root, 'after-freeze')), 'fixture never changed out/ after the freeze')
    const remote = remoteDirectory(root)
    const added = manifest(pollution)
    for (const [label, tree] of [['baseline-out', manifest(path.join(remote, 'baseline-out'))],
      ['test view', calls.find(call => call.title === 'tests').viewBaselineOut]]) {
      for (const [relative, digest] of Object.entries(added)) assert.notEqual(tree[relative], digest, `${label}: ${relative} came from out/ after reproduce`)
      assert.ok(!Object.keys(tree).some(relative => /^(profile|concurrency)\//.test(relative)), `${label}: profiler outputs present`)
    }
  })
}
// SCHEMAS.md implement snapshot bullet: "A missing or symlinked `reproduce-out/` fails the snapshot".
function brokenFreezeCheck(name, run) {
  check(`${name}: snapshot fails before the adapter smoke and any author call`, () => {
    assert.ok(fs.existsSync(path.join(run.root, 'after-freeze')), 'fixture never tampered with reproduce-out')
    assert.equal(run.record?.signature.status, 'FAIL')
    const titles = rows(path.join(run.root, 'calls.jsonl')).map(call => call.title)
    for (const title of ['tests', 'implement', 'review', 'adapter-repair']) assert.ok(!titles.includes(title), `${title} called after a failed snapshot`)
    const operations = receiptOperations(run.root)
    for (const operation of ['adapter-smoke', 'setup-method', 'run-method', 'run-tests']) assert.ok(!operations.includes(operation), `${operation} ran after a failed snapshot`)
    assert.equal(run.records.find(row => row.signature?.stage === 'evaluate')?.signature.status, 'SKIPPED')
    assert.equal(fs.existsSync(path.join(run.root, 'control', 'implement', 'tests.json')), false, 'tests frozen after a failed snapshot')
  })
}
// Small copies of the run13 files the frozen tests read: `reproduce/` is the anchor run's out/;
// `profiled/` is what reached out/ afterwards (a second run, rewritten latest-baseline-run.txt,
// small profile/ and concurrency/ outputs; large profiler files are skipped).
function run13Data() {
  const data = path.join(scratch, 'run13-data')
  const copy = (from, to) => {
    fs.mkdirSync(path.dirname(path.join(data, to)), { recursive: true })
    fs.copyFileSync(path.join(RUN13, 'results', from), path.join(data, to))
  }
  for (const file of [`${RUN13_RUN}/ensemble.json`, `${RUN13_RUN}/stdout.log`, 'latest-baseline-run.txt']) copy(`reproduce/out/${file}`, `reproduce/${file}`)
  for (const file of ['baseline.xYR708Pq/ensemble.json', 'baseline.xYR708Pq/stdout.log', 'latest-baseline-run.txt',
    'profile/stages.json', 'profile/total_wall_s.json', 'concurrency/concurrency.json']) copy(`implement/baseline/out/${file}`, `profiled/${file}`)
  return data
}
// run13's check_outputs.py run directly, with a method output equal to the reproduce run.
function run13Direct(data, baselineOut) {
  const work = fs.mkdtempSync(path.join(scratch, 'run13-direct-')), method = path.join(work, 'method')
  fs.copyFileSync(path.join(RUN13, 'tests', 'check_outputs.py'), path.join(work, 'check_outputs.py'))
  fs.mkdirSync(method)
  for (const file of ['ensemble.json', 'stdout.log']) fs.copyFileSync(path.join(data, 'reproduce', RUN13_RUN, file), path.join(method, file))
  const result = spawnSync('python3', ['-I', path.join(work, 'check_outputs.py')], { cwd: work, encoding: 'utf8',
    env: { ...process.env, BASELINE_OUT: baselineOut, METHOD_OUT: method } })
  return { result, report: fs.existsSync(path.join(method, 'tests.json')) ? readJSON(path.join(method, 'tests.json')) : null }
}
function run13RecordedChecks(data) {
  const postProfiling = path.join(RUN13, 'results', 'implement', 'baseline', 'out')
  check('run13 recorded: the post-profiling out/ copy holds two baseline runs, the reproduce out/ one', () => {
    const runs = directory => fs.readdirSync(directory).filter(entry => fs.existsSync(path.join(directory, entry, 'ensemble.json'))).sort()
    assert.deepEqual(runs(postProfiling), [RUN13_RUN, 'baseline.xYR708Pq'].sort())
    assert.deepEqual(runs(path.join(RUN13, 'results', 'reproduce', 'out')), [RUN13_RUN])
  })
  check('run13 recorded (old failure mode): frozen tests on the post-profiling out/ copy report every case invalid_output', () => {
    const { result, report } = run13Direct(data, postProfiling)
    assert.equal(result.status, 1, result.stderr)
    const expected = { passed: 0, failed: 9, cases: RUN13_IDS.map(id => ({ id, pass: false, reason_code: 'invalid_output' })) }
    assert.deepEqual(report, expected)
    assert.deepEqual(readJSON(path.join(RUN13, 'results', 'implement', 'attempt-1', 'tests', 'out', 'tests.json')), expected, 'recorded attempt-1 report')
  })
  check('run13 recorded: the same tests pass all nine cases on the reproduce outputs their author saw', () => {
    const { result, report } = run13Direct(data, path.join(data, 'reproduce'))
    assert.equal(result.status, 0, result.stderr)
    assert.deepEqual(report, { passed: 9, failed: 0, cases: RUN13_IDS.map(id => ({ id, pass: true, reason_code: null })) })
  })
}
async function main() {
  try {
    const happy = await execute('happy')
    verdict('happy', happy, null, { patch_applies: true, tests_pass: true, blind_tests: true, launch_review_pass: true })
    authorChecks(happy)
    receiptChecks(happy)
    frozenBaselineChecks('happy', happy, null)
    // SCHEMAS.md EVAL_PROTOCOL bullet: "The harness prompt ... and the method author prompt both state these two shapes."
    check('method author prompt states the EVAL_INPUTS and EVAL_SEEDS shapes', () => {
      const author = happy.calls.find(call => call.title === 'implement')
      assert.ok(author, 'missing method author call')
      assertEvalShapes(author.prompt, 'implement')
    })
    // SCHEMAS.md "A/tests/ and out/tests.json": "Tests see exactly two sets of outputs ...
    // acceptance is decided in evaluate. The test author prompt states these rules."
    check('test author prompt states the representative-output equivalence rules', () => {
      const author = happy.calls.find(call => call.title === 'tests')
      assert.ok(author, 'missing test author call')
      assertTestAuthorRules(author.prompt)
      // Negative control: the matcher depends on the rule statements themselves.
      for (const word of [/overlap/i, /disjoint|entirely outside|does not overlap|no overlap/i, /held-out seeds/i, /too few|insufficient|not enough/i]) {
        const stripped = author.prompt.split('\n').filter(line => !word.test(line)).join('\n')
        assert.throws(() => assertTestAuthorRules(stripped), undefined, `matcher passes without ${word}`)
      }
    })
    run8RuleChecks()
    run8FrozenTestCheck()
    for (const role of ['tests', 'implement']) check(`${role}: opposing sentinel unreadable [requires bubblewrap]`, () => {
      const call = happy.calls.find(call => call.title === role)
      assert.ok(call, 'missing author call')
      assert.equal(call.probe?.status, 0, call.probe?.diagnostic || 'probe did not run')
    })
    const repaired = await execute('repair', { repair: true })
    verdict('repair', repaired, null, { patch_applies: true, tests_pass: true, blind_tests: true, launch_review_pass: true })
    check('one bounded repair receives only aggregated reason counts', () => {
      const authors = repaired.calls.filter(call => call.title === 'implement')
      assert.equal(authors.length, 2)
      assert.match(authors[1].name, /-retry1$/)
      const counts = authors[1].prompt.match(/reason_code(?:_counts| counts)\s*:\s*(\{[^\n]*?\})/)
      assert.ok(counts, 'repair prompt has no reason counts')
      assert.deepEqual(JSON.parse(counts[1]), { equivalence: 1 })
      for (const forbidden of [TEST_SECRET, `${PRIVATE}:tests`, 'fail-equivalence', '"cases"', '"failed"', 'run_tests.sh']) assert.ok(!authors[1].prompt.includes(forbidden), `repair feedback contains ${forbidden}`)
      assert.equal(repaired.calls.filter(call => call.title === 'tests').length, 1)
      assert.equal(repaired.calls.filter(call => call.title === 'review').length, 1)
      assert.deepEqual(readJSON(path.join(repaired.root, 'control', 'implement', 'attempt-1.json')), { attempt: 1, reason_code_counts: { equivalence: 1 } })
      assert.equal(readJSON(path.join(repaired.root, 'agent', 'implement-payload.json')).attempt, 2)
      assert.equal(authors[0].frozenHash, authors[1].frozenHash)
    })
    // run8 regression through the real implement stage: a contract-following
    // equivalence test passes on run8's representative pairs; run8's frozen tests,
    // which require evaluation records, fail with missing_output on both attempts.
    const contract = await execute('run8-contract', { run8: 'contract' })
    verdict('run8-contract', contract, null, { patch_applies: true, tests_pass: true, blind_tests: true, launch_review_pass: true })
    check('run8-contract: equivalence case passes on run8 pairs at the first attempt', () => {
      const report = readJSON(path.join(contract.root, 'agent', 'results', 'implement', 'out', 'tests.json'))
      assert.deepEqual(report.cases.find(row => row.id === 'equivalence'), { id: 'equivalence', pass: true, reason_code: null })
      assert.equal(report.failed, 0)
      assert.equal(contract.calls.filter(call => call.title === 'implement').length, 1)
      assert.equal(fs.existsSync(path.join(contract.root, 'control', 'implement', 'attempt-1.json')), false)
    })
    const frozen = await execute('run8-frozen', { run8: 'frozen' })
    verdict('run8-frozen', frozen, 'numeric', { tests_pass: false })
    check('run8-frozen: evaluation-record tests fail missing_output on both attempts', () => {
      for (const attempt of [1, 2]) {
        assert.deepEqual(readJSON(path.join(frozen.root, 'control', 'implement', `attempt-${attempt}.json`)),
          { attempt, reason_code_counts: { missing_output: 1 } })
      }
    })
    // After the freeze, out/ gains profiler and probe outputs and a second baseline-style run, and
    // values.json is rewritten: the fixture's tests compare BASELINE_OUT/values.json with the method's.
    const pollution = path.join(scratch, 'pollute-generic')
    writeJSON(path.join(pollution, 'values.json'), [9, 9, 9, 9, 9])
    writeJSON(path.join(pollution, 'baseline.second', 'values.json'), [0, 1, 2, 3, 4, 5])
    writeJSON(path.join(pollution, 'profile', 'stages.json'), [{ stage: 'kernels', wall_s: 1, gpu_s: 1 }])
    writeJSON(path.join(pollution, 'concurrency', 'concurrency.json'), { factor: null })
    const profiled = await execute('profiled-out', { pollute: pollution })
    verdict('profiled-out', profiled, null, { patch_applies: true, tests_pass: true, blind_tests: true, launch_review_pass: true })
    frozenBaselineChecks('profiled-out', profiled, pollution)
    for (const tamper of ['missing', 'symlink']) {
      const name = `reproduce-out-${tamper}`
      const run = await execute(name, { freezeTamper: tamper })
      brokenFreezeCheck(name, run)
    }
    // run13 regression: its frozen tests, its reproduce outputs as the anchor run's out/, and its
    // post-reproduce run, profile and concurrency outputs added to out/ before implement.
    const data = run13Data()
    run13RecordedChecks(data)
    const run13 = await execute('run13-profiled', { run13Data: data, pollute: path.join(data, 'profiled') })
    verdict('run13-profiled', run13, null, { patch_applies: true, tests_pass: true, blind_tests: true, launch_review_pass: true })
    check('run13-profiled: run13 frozen tests pass all nine cases at the first attempt', () => {
      const report = readJSON(path.join(run13.root, 'agent', 'results', 'implement', 'out', 'tests.json'))
      assert.deepEqual(report, { passed: 9, failed: 0, cases: RUN13_IDS.map(id => ({ id, pass: true, reason_code: null })) })
      assert.equal(run13.calls.filter(call => call.title === 'implement').length, 1)
      assert.equal(fs.existsSync(path.join(run13.root, 'control', 'implement', 'attempt-1.json')), false)
      const baselineOut = path.join(remoteDirectory(run13.root), 'baseline-out')
      assert.deepEqual(fs.readdirSync(baselineOut).filter(entry => fs.existsSync(path.join(baselineOut, entry, 'ensemble.json'))), [RUN13_RUN])
      assert.equal(fs.readFileSync(path.join(baselineOut, 'latest-baseline-run.txt'), 'utf8'), `out/${RUN13_RUN}\n`)
    })
    frozenBaselineChecks('run13-profiled', run13, path.join(data, 'profiled'))
    for (const [name, config, errorClass] of [
      ['repair-exhausted', { failTwice: true }, 'numeric'],
      ['review-rejected', { rejectReview: true }, 'other'],
      ['review-invalid', { badReview: true }, 'parse'],
      ['patch-invalid', { badPatch: true }, 'parse'],
      ['setup-failed', { setupFailure: true }, 'install'],
      ['run-failed', { runFailure: true }, 'numeric'],
      ['fetch-failed', { fetchFailure: true }, 'infra'],
      ['nonzero-tests', { testExit: 7 }, 'numeric'],
      ...['missing', 'missing-id', 'duplicate', 'extra', 'counts', 'reason'].map(report => ['report-' + report, { report }, 'parse']),
      ['baseline-tampered', { tamperBaseline: true }, 'other'],
      ['tests-tampered', { tamperTests: true }, 'other'],
      ['payload-tampered', { tamperPayload: true }, 'other'],
      ['tests-symlink', { testSymlink: true }, 'parse'],
      // Seal failure must stop work. The implement contract does not prescribe
      // one error class for this failure; parse and other are both valid here.
      ...['initial', 'author', 'review'].map(tamperSeal => ['seal-' + tamperSeal, { tamperSeal }, ['parse', 'other']]),
      ['new-latest-seal', { newSeal: true }, ['parse', 'other']],
    ]) {
      const run = await execute(name, config)
      verdict(name, run, errorClass)
      if (config.report || config.testExit || config.setupFailure || config.runFailure || config.failTwice) {
        check(`${name}: failed execution cannot set tests_pass`, () => assert.equal(run.record?.facts.tests_pass, false))
      }
      check(`${name}: no extra author, repair or review`, () => {
        assert.ok(run.calls.filter(call => call.title === 'tests').length <= 1)
        assert.ok(run.calls.filter(call => call.title === 'implement').length <= 2)
        assert.ok(run.calls.filter(call => call.title === 'review').length <= 1)
        if (config.fetchFailure || config.tamperBaseline || config.tamperTests || config.tamperPayload || config.tamperSeal || config.newSeal || config.rejectReview || config.badReview) {
          assert.ok(run.calls.filter(call => call.title === 'implement').length <= 1, 'integrity/review failure triggered repair')
        }
        if (config.failTwice) {
          assert.equal(run.calls.filter(call => call.title === 'implement').length, 2)
          assert.equal(run.calls.filter(call => call.title === 'review').length, 0)
          assert.deepEqual(readJSON(path.join(run.root, 'control', 'implement', 'attempt-2.json')), { attempt: 2, reason_code_counts: { equivalence: 1 } })
        }
        if (config.tamperSeal === 'initial') assert.equal(run.calls.length, 0, 'seal failure called an author')
        if (config.tamperSeal === 'author') assert.equal(run.calls.filter(call => call.title === 'review').length, 0)
      })
    }
  } catch (error) { failures++; console.log(`FAIL test harness: ${error.stack}`) }
  finally { removeScratch(scratch) }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : 'all checks passed')
  process.exitCode = failures ? 1 : 0
}
main()
