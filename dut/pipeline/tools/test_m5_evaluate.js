#!/usr/bin/env node
'use strict'

// Black-box stage-7 contracts from m5/SCHEMAS.md. Never inspect evaluator source.
// Usage: node tools/test_m5_evaluate.js
// All generated workloads, fake GPU tools, ledgers and workflow outputs use /tmp.
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const assert = require('node:assert/strict')
const { spawn } = require('node:child_process')
const { createHash, randomUUID } = require('node:crypto')
const ROOT = process.env.M5_TEST_SOURCE_ROOT || path.resolve(__dirname, '..')
const SECRET = 'EVALUATE_PRIVATE_SENTINEL_486201'
const IDS = ['dropped_inputs', 'duplicated_inputs', 'ordering', 'tail_handling', 'seeds', 'equivalence']
const FACTS = ['validity_pass', 'equivalence_pass', 'performance_pass', 'equal_cost', 'speedup_published',
  'speedup_tuned', 'cost_ratio', 'prediction_ratio', 'curve_points', 'tokens_known', 'gpu_busy_known']
const SMOKE_PIN = path.join(__dirname, 'm5_smoke_pin.js')
const { pinned } = require('./m5_smoke_pin.js')
const quote = word => `'${word.replaceAll("'", "'\\''")}'`
const readJSON = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const rows = file => fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : []
const sha = value => createHash('sha256').update(value).digest('hex')
function writeJSON(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, JSON.stringify(value) + '\n')
}
function script(file, text) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, '#!/usr/bin/env bash\nset -eu\n' + text + '\n', { mode: 0o700 })
}
function files(directory) {
  if (!fs.existsSync(directory)) return []
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    const file = path.join(directory, entry.name)
    assert.ok(!entry.isSymbolicLink(), 'unexpected evidence symlink')
    return entry.isDirectory() ? files(file) : [file]
  })
}
const anchors = [{ id: 'first', quantity: 'fixture', source: 'published fixture', published_value: 1, tolerance: 0 },
  { id: 'zero', quantity: 'fixture', source: 'published fixture', published_value: 0, tolerance: { abs: 0 } }]
// SCHEMAS.md A/intake/: "==" items with null tolerance are references (never pass or fail).
const references = anchors.map(item => ({ ...item, tolerance: null }))
const ANCHOR_SETS = { anchors, references, empty: [], mixed: [anchors[1], references[0]] }
const anchorsFor = config => ANCHOR_SETS[config.anchorSet || 'anchors']
// Public evidence from positive-openmm run7: its harness run_evaluation.sh treated every key of the sealed
// evaluation_inputs as an input and crashed, so evaluate was VOID after implement passed.
const RUN7 = path.resolve(__dirname, '../../../experiments/positive-openmm/run7')
const run7Protocol = () => readJSON(path.join(RUN7, 'agent/PREDICTIONS.json'))
function protocol(config = {}) {
  if (config.run7) return run7Protocol()
  const budgets = [2, 4, 8]
  return {
    predictions: [{ method: 'batching', expected_speedup_interval: { low: 1.5, high: 2.5 },
      outcome_vs_compute_points: budgets.map(compute_budget => ({ compute_budget, predicted_outcome: 1, uncertainty: 'fixture' })) }],
    infeasible_methods: [], evaluation_inputs: { ids: ['first', 'middle', 'tail'], pin: 'fixture-v1' },
    sample_sizes: { inputs: 3, seeds: config.stochastic ? (config.seedCount || 6) : 1 },
    equivalence_metrics: [{ name: 'accuracy', tolerance: { abs: 0.01 }, source: 'fixture scientific requirement' }],
    paired_seed_tests: config.stochastic ? { kind: 'paired_median', seeds: Array.from({ length: config.seedCount || 6 }, (_, i) => 17 + i) }
      : { kind: 'deterministic', justification: 'Fixed arithmetic fixture.' },
    confidence_rule: { equivalence: { kind: 'paired_median', confidence: 0.95 }, performance: { kind: 'paired_median', confidence: 0.95 } },
    timing_scope: { kind: 'reported_wall', gpu_synchronization: 'adapter', description: 'Complete fixture workload.' },
    hardware_cost_basis: { baseline_gpus: 1, method_gpus: config.moreGPUs ? 4 : 1, budget_unit: 'gpu_s' },
    warmup: 1, repetitions: 5, scheduling_order: { kind: 'randomized_pairs', seed: 42 },
    minimum_worthwhile_gain: 1.1, compute_budgets: budgets, splits: { evaluation: ['first', 'middle', 'tail'] },
    equal_outcome_target: config.curves ? { metric: 'accuracy', target: config.unachieved ? 2 : 0.9, comparison: '>=' }
      : { not_applicable: true, reason: 'Fixture has no scientific outcome curve.' },
    baseline_invocation_s: { seconds: 0.01, source: 'fixture: one baseline equivalence invocation, 0.01 s' },
  }
}
// Synthetic adapter reports exercise the scorer; no real GPU, model or network.
// Different times by repetition distinguish median(pair ratios) from ratio(medians).
function adapter(config = {}, baseline = false) {
  if (config.run7) return run7Adapter(config, baseline)
  return `printf '%s\\n' '${SECRET}:adapter'
python3 - <<'FIXTURE_PY'
import json, os, pathlib
c = json.loads(${JSON.stringify(JSON.stringify(config))})
p = json.loads(pathlib.Path(os.environ['EVAL_PROTOCOL']).read_text()) if 'EVAL_PROTOCOL' in os.environ else None
out = pathlib.Path(os.environ.get('EVAL_OUT', 'out'))
out.mkdir(parents=True, exist_ok=True)
arm = os.environ.get('EVAL_ARM', '${baseline ? 'baseline' : 'method'}')
mode = os.environ.get('EVAL_MODE', 'implement')
if mode in ('implement', 'anchors'):
    if not (mode == 'anchors' and c.get('missingAnchor')):
        measured = {'first': 1, 'zero': 0}
        if mode == 'anchors' and arm == 'method' and c.get('badAnchor'): measured['first'] = 2
        if mode == 'anchors' and c.get('partialAnchor'): del measured['zero']
        (out / 'anchors_measured.json').write_text(json.dumps(measured))
    (out / 'values.json').write_text('[0,1,2]')
else:
    seeds = p['paired_seed_tests'].get('seeds', [None])
    records = [dict(input_id=i, seed=s, metrics={'accuracy': 1.0 + (c.get('delta', 0) if arm == 'method' else 0)})
               for s in seeds for i in p['evaluation_inputs']['ids']]
    if c.get('stochastic'):
        for row in records:
            row['metrics']['accuracy'] += row['seed'] / 10
            if arm == 'method':
                row['metrics']['accuracy'] += {'first': -0.02, 'middle': 0.02, 'tail': 0}[row['input_id']]
    if arm == 'method':
        if c.get('alignment') == 'order': records[0], records[1] = records[1], records[0]
        if c.get('alignment') == 'drop': records.pop()
        if c.get('alignment') == 'duplicate': records[-1] = records[0].copy()
        if c.get('alignment') == 'seed': records[0]['seed'] = 999
        if c.get('missingMetric'): records[0]['metrics'] = {}
    # Fresh work directories make repetition index observable without shared counters.
    index = int(pathlib.Path.cwd().parent.name) if pathlib.Path.cwd().parent.name.isdigit() else 0
    times = c.get('baselineTimes', [10]*5) if arm == 'baseline' else c.get('methodTimes', [5]*5)
    wall = times[index % len(times)]
    if mode == 'warmup': wall = 100 if arm == 'method' else 1
    report = dict(records=records, timing_scope=p['timing_scope'],
                  gpu_count=p['hardware_cost_basis'][arm + '_gpus'], wall_s=wall, private='${SECRET}')
    if mode == 'curve': report['compute_budget'] = float(os.environ['EVAL_COMPUTE_BUDGET'])
    if c.get('missingScope'): del report['timing_scope']
    # Implement's baseline adapter smoke (SCHEMAS.md "Baseline adapter smoke") runs in
    # evaluation-work/smoke/; missing outputs model an adapter that fails only in evaluate.
    smoke = '/evaluation-work/smoke/' in str(pathlib.Path.cwd())
    if not ((c.get('missingOutput') and not smoke) or (mode == 'curve' and c.get('missingCurve'))):
        (out / 'evaluation.json').write_text(json.dumps(report))
FIXTURE_PY`
}
// SCHEMAS.md EVAL_PROTOCOL bullet. `contract` reads only EVAL_INPUTS.ids and the EVAL_SEEDS seeds (or one
// null seed) and emits seed-major records. `every-key` reproduces run7's harness: each key of EVAL_INPUTS
// becomes an input. Every invocation's environment and emitted (input_id, seed) pairs go to the capture file.
function run7Adapter(config, baseline) {
  return `printf '%s\\n' '${SECRET}:adapter'
python3 - <<'RUN7_FIXTURE_PY'
import json, os, pathlib
c = json.loads(${JSON.stringify(JSON.stringify(config))})['run7']
arm = os.environ.get('EVAL_ARM', '${baseline ? 'baseline' : 'method'}')
mode = os.environ.get('EVAL_MODE', 'implement')
out = pathlib.Path(os.environ.get('EVAL_OUT', 'out'))
out.mkdir(parents=True, exist_ok=True)
row = dict(arm=arm, mode=mode, cwd=os.getcwd(), inputs=os.environ.get('EVAL_INPUTS'), seeds=os.environ.get('EVAL_SEEDS'),
           protocol=pathlib.Path(os.environ['EVAL_PROTOCOL']).read_text() if os.environ.get('EVAL_PROTOCOL') else None)
def capture():
    with open(c['capture'], 'a') as f: f.write(json.dumps(row) + '\\n')
if mode in ('implement', 'anchors'):
    capture()
    (out / 'anchors_measured.json').write_text(json.dumps({'first': 1, 'zero': 0}))
    (out / 'values.json').write_text('[0,1,2]')
else:
    capture()
    inputs, spec = json.loads(row['inputs']), json.loads(row['seeds'])
    seeds = spec['seeds'] if spec['kind'] == 'paired_median' else [None]
    ids = inputs['ids'] if c[arm] == 'contract' else list(inputs)
    records = [dict(input_id=i, seed=s, metrics={'final_potential_kj_mol': -30000.0 - (s or 0), 'mean_potential_kj_mol': -31000.0 + (s or 0) / 2})
               for s in seeds for i in ids]
    p = json.loads(row['protocol'])
    report = dict(records=records, timing_scope=p['timing_scope'], gpu_count=p['hardware_cost_basis'][arm + '_gpus'])
    if mode == 'curve': report['compute_budget'] = float(os.environ['EVAL_COMPUTE_BUDGET'])
    (out / 'evaluation.json').write_text(json.dumps(report))
    row['records'] = [[r['input_id'], r['seed']] for r in records]
    capture()
RUN7_FIXTURE_PY`
}
module.exports = {
  async run(options) {
    const root = process.env.M5_EVALUATE_ROOT, config = JSON.parse(process.env.M5_EVALUATE_CONFIG)
    const { title } = options
    fs.appendFileSync(path.join(root, 'calls.jsonl'), JSON.stringify({ title }) + '\n')
    const agent = path.join(root, 'agent')
    let json = { v: SECRET }
    if (title === 'harness') {
      script(path.join(agent, 'harness', 'setup.sh'), `mkdir -p baseline-published data out
git init -q --separate-git-dir published-git baseline-published
printf 'published\\n' > baseline-published/pin
printf 'input\\n' > data/input`)
      // Reproduction must pass before the method's intentionally bad anchor is tested.
      script(path.join(agent, 'harness', 'run_anchors.sh'), 'mkdir -p out\nprintf \'{"first":1,"zero":0}\\n\' > out/anchors_measured.json\nprintf \'[0,1,2]\\n\' > out/values.json')
      script(path.join(agent, 'harness', 'run_evaluation.sh'), adapter(config, true))
      script(path.join(agent, 'harness', 'run_command.sh'), 'true')
    }
    const view = options.isolation?.directory || options.cwd
    if (title === 'tests') {
      const report = { passed: IDS.length, failed: 0, cases: IDS.map(id => ({ id, pass: true, reason_code: null })) }
      script(path.join(view, 'tests', 'run_tests.sh'), `mkdir -p out\nprintf '%s\\n' '${JSON.stringify(report)}' > out/tests.json`)
    }
    if (title === 'implement') {
      const directory = path.join(view, 'method')
      fs.mkdirSync(directory, { recursive: true })
      fs.writeFileSync(path.join(directory, 'method.patch'), 'diff --git a/pin b/pin\n--- a/pin\n+++ b/pin\n@@ -1 +1 @@\n-published\n+changed\n')
      script(path.join(directory, 'setup_method.sh'), 'true')
      script(path.join(directory, 'run_method.sh'), adapter(config))
    }
    if (title === 'review') json = { pass: true, reason_codes: [] }
    return { text: JSON.stringify(json), json, jsonError: null, sessionID: randomUUID(),
      tokens: { input: 0, output: 0 }, tokens_known: true, cost: 0, tools: 0, ms: 1, errors: [], refusal: false }
  },
  async exportSession(id, file) { fs.writeFileSync(file, '{}') },
}
if (require.main !== module) return

const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_evaluate_'))
let checks = 0, failures = 0
function check(label, fn) {
  checks++
  try { fn(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${error.message}`) }
}
function near(actual, expected) { assert.ok(typeof actual === 'number' && Math.abs(actual - expected) < 1e-10, `${actual} != ${expected}`) }
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical)
  if (value && typeof value === 'object') return Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])]))
  return value
}
async function execute(command, args, directory, env = {}, cwd = directory) {
  const stdout = fs.openSync(path.join(directory, 'stdout.log'), 'w'), stderr = fs.openSync(path.join(directory, 'stderr.log'), 'w')
  try {
    return await new Promise(resolve => {
      const child = spawn(command, args, { cwd, timeout: 180000, stdio: ['ignore', stdout, stderr],
        env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1', M5_RAIDS_LEDGER: path.join(scratch, 'ledger.jsonl'), ...env } })
      let error
      child.on('error', value => { error = value })
      child.on('close', (status, signal) => resolve({ status, signal, error }))
    })
  } finally { fs.closeSync(stdout); fs.closeSync(stderr) }
}
function hermetic(root) {
  const bin = path.join(root, 'bin')
  script(path.join(bin, 'nvidia-smi'), `if [[ "$*" == *--query-gpu=name* ]]; then
  for ((i=0; i<8; i++)); do printf '%s\\n' 'Fixture GPU'; done
  exit 0
fi
exit 1`)
  return { PATH: bin + path.delimiter + process.env.PATH }
}
function provenance() {
  return Object.fromEntries(['seal_sha256', 'baseline_sha256', 'data_sha256', 'baseline_outputs_sha256', 'tests_sha256',
    'method_payload_sha256', 'anchors_sha256', 'harness_sha256'].map(key => [key, sha(key)]))
}
async function cli(name, stage, config = {}, explicit = true) {
  const root = path.join(scratch, 'cli-' + name), remote = path.join(root, 'remote'), out = path.join(remote, 'out', 'eval')
  for (const directory of ['baseline-published', 'method', 'data', 'baseline-out', 'harness', 'payload/method', 'payload/tests', 'out/eval']) {
    fs.mkdirSync(path.join(remote, directory), { recursive: true })
  }
  script(path.join(remote, 'harness', 'run_evaluation.sh'), adapter(config, true))
  script(path.join(remote, 'harness', 'run_anchors.sh'), adapter(config, true))
  script(path.join(remote, 'payload', 'method', 'run_method.sh'), adapter(config))
  const p = protocol(config), hashes = provenance()
  hashes.evaluators = Object.fromEntries(['eval_common.py', 'eval_validity.py', 'eval_equivalence.py', 'eval_performance.py', 'score_anchors.py'].map(file => [file, sha(file)]))
  const method_files = [{ path: 'run_method.sh', sha256: sha(fs.readFileSync(path.join(remote, 'payload/method/run_method.sh'))) }]
  const manifest = { remote_directory: remote, protocol: p, prediction: p.predictions[0],
    box: { price_usd_h: config.noPrice ? 0 : 4, type: 'gpu_8x_a100' }, gpu_count: 8, run_timeout_s: 10,
    method_files, anchors: anchorsFor(config), input_hashes: hashes }
  writeJSON(path.join(remote, 'evaluation-payload/predictions.json'), p)
  writeJSON(path.join(root, 'manifest.json'), manifest)
  fs.chmodSync(path.join(root, 'manifest.json'), 0o444)
  const child = await execute('python3', [path.join(ROOT, 'm5', `eval_${stage}.py`),
    ...(explicit ? ['--stage', stage] : []), '--in', path.join(root, 'manifest.json'), '--out', out], root, hermetic(root))
  return { root, remote, out, child, manifest,
    verdict: fs.existsSync(path.join(out, stage + '.json')) ? readJSON(path.join(out, stage + '.json')) : null }
}
function verdict(name, result, stage, status, code) {
  check(name, () => {
    assert.ifError(result.child.error)
    assert.equal(result.child.status, code, fs.readFileSync(path.join(result.root, 'stderr.log'), 'utf8').slice(-400))
    assert.equal(result.verdict?.status, status)
    assert.equal(result.verdict[stage + '_pass'], status === 'VOID' ? null : status === 'PASS')
    assert.deepEqual(result.verdict.input_hashes, result.manifest.input_hashes)
    if (status === 'VOID') assert.equal(result.verdict.reason_code, 'missing_or_invalid_measurements')
  })
}
async function pipeline(name, config = {}) {
  const root = path.join(scratch, 'pipeline-' + name), agent = path.join(root, 'agent'), home = path.join(root, 'home')
  fs.mkdirSync(root, { recursive: true })
  const p = protocol(config)
  for (const [name, value] of Object.entries({ benchmark: { name: SECRET }, data: { available: true }, anchors: anchorsFor(config),
    baseline: { repo: 'fixture', pin: 'v1', build_commands: ['true'], run_commands: ['true'], published_configuration: { n: 3 } },
    EXECUTION: { representative_scale: { n: 3 }, inputs: ['data/input'], outputs: ['values.json'], timing_scope: p.timing_scope,
      timeout_s: 60, timeouts: { setup_method: 30, run_method: 10, run_tests: 10, evaluate: 60 } },
  })) writeJSON(path.join(agent, 'intake', name + '.json'), value)
  const sealed = JSON.stringify(canonical(p))
  fs.mkdirSync(path.join(agent), { recursive: true })
  fs.writeFileSync(path.join(agent, 'PREDICTIONS.json'), sealed)
  const frozen = path.join(root, 'control', 'seals', 'frozen.json')
  fs.mkdirSync(path.dirname(frozen), { recursive: true })
  fs.writeFileSync(frozen, sealed, { mode: 0o444 })
  writeJSON(path.join(root, 'control/seals/0001.json'), { sha256: sha(sealed), path: frozen, utc: new Date().toISOString() })
  writeJSON(path.join(agent, 'proposal.json'), { method: 'batching', rationale: SECRET, plan_steps: ['Preserve paired inputs.'], files_expected: ['pin'], risks: [] })
  writeJSON(path.join(agent, 'profile-packet.json'), { stages: [], total_wall_s: 10, timed_fraction: 1, gpu_telemetry: true, gpu_count: 8 })
  writeJSON(path.join(home, '.cache/metis-serve/box.json'), { type: 'gpu_8x_a100', region: SECRET, price_usd_h: 4, started_utc: new Date().toISOString() })
  script(path.join(home, '.cache/metis-serve/box.sh'), 'exit 99')
  const box = path.join(root, 'box'), bin = path.join(root, 'bin')
  fs.mkdirSync(box)
  const env = hermetic(root)
  // Keep real /tmp/m5-<uuid> paths: the sealed manifest embeds absolute paths
  // consumed by adapter subprocesses, so shell-only path rewriting is invalid.
  script(path.join(bin, 'box'), `command=$1
remote_directory=
if [[ $command =~ /tmp/m5-[a-z0-9-]+ ]]; then
  remote_directory=\${BASH_REMATCH[0]}
  printf '%s\\n' "$remote_directory" >> "$M5_REMOTE_ROOTS"
fi
export PATH="$M5_EVALUATE_BIN:$PATH"
cd "$BOX_ROOT"
bash -c "$command"
if [[ $command == *timeout* && -n $remote_directory ]]; then
  for ((i=0; i<1000; i++)); do
    pending=false
    for file in "$remote_directory"/*.sh; do
      [[ -f $file ]] || continue
      [[ -f \${file%.sh}.rc ]] || pending=true
    done
    [[ $pending == true ]] || break
    sleep 0.01
  done
fi`)
  // Implement's smoke cost gate must not depend on the host's speed: pin each fetched smoke
  // measurement (tools/m5_smoke_pin.js). Malformed smoke.json files pass through unchanged.
  const pinLog = path.join(root, 'smoke-pin.jsonl')
  script(path.join(bin, 'fetch'), `cp -r -- "$1" "$2"\nexec ${quote(process.execPath)} ${quote(SMOKE_PIN)} "$2" ${quote(pinLog)}`)
  const args = path.join(root, 'control/args.json'), output = path.join(agent, 'wf')
  writeJSON(args, { run_root: root, tag: 'evaluate-' + name, raid: 'evaluate-' + name, stub: { intake: 'PASS', profile: 'PASS', seal: 'PASS', propose: 'PASS', takeaways: 'PASS' } })
  const child = await execute(process.execPath, [path.join(ROOT, 'idea/wf.js'), '--script', path.join(ROOT, 'm5/pipeline.js'),
    '--args', args, '--out', output, '--disable-family', 'claude'], root,
  { ...env, HOME: home, WF_STUB: __filename, M5_TEST_SOURCE_ROOT: ROOT, M5_EVALUATE_ROOT: root,
    M5_EVALUATE_CONFIG: JSON.stringify(config), M5_REMOTE_ROOTS: path.join(scratch, 'remote-roots'), BOX_ROOT: box, M5_EVALUATE_BIN: bin, BOX: path.join(bin, 'box'), FETCH: path.join(bin, 'fetch') }, ROOT)
  const records = rows(path.join(root, 'operator/signatures.jsonl')), record = records.find(row => row.signature?.stage === 'evaluate')
  // A baseline adapter failing implement's smoke (and its one repair) stops before evaluate.
  if (config.stopsAtImplement) {
    check(`${name}: implement's baseline adapter smoke stops the run before evaluate`, () => {
      assert.ifError(child.error)
      assert.equal(child.status, 0)
      assert.equal(records.find(row => row.signature?.stage === 'reproduce')?.signature.status, 'PASS', 'reproduce')
      const implement = records.find(row => row.signature?.stage === 'implement')?.signature
      assert.equal(implement?.status, 'VOID', 'implement')
      assert.equal(implement.error_class, 'parse')
      assert.equal(record?.signature.status, 'SKIPPED', 'evaluate')
      assert.ok(!rows(path.join(root, 'calls.jsonl')).some(row => ['tests', 'implement', 'review'].includes(row.title)), 'an author ran')
    })
    return { root, record, records, results: path.join(agent, 'results/evaluate') }
  }
  check(`${name}: evaluate reached through real reproduce and implement`, () => {
    assert.ifError(child.error)
    assert.equal(child.status, 0)
    assert.ok(!readJSON(path.join(output, 'result.json')).error, JSON.stringify(readJSON(path.join(output, 'result.json')).error))
    for (const stage of ['reproduce', 'implement']) assert.equal(records.find(row => row.signature?.stage === stage)?.signature.status, 'PASS', stage)
    assert.ok(record)
  })
  check(`${name}: the fixture pinned the fetched smoke measurement`, () => {
    assert.ok(pinned(pinLog).length > 0, 'implement passed but no fetched smoke.json was pinned')
  })
  check(`${name}: exact facts, no model calls, hermetic GPU telemetry`, () => {
    assert.deepEqual(Object.keys(record.facts).sort(), FACTS.slice().sort())
    assert.equal(record.facts.tokens_known, true)
    assert.equal(record.facts.gpu_busy_known, false)
    assert.equal(record.facts.speedup_tuned, null)
    assert.ok(rows(path.join(root, 'calls.jsonl')).every(row => ['harness', 'tests', 'implement', 'review'].includes(row.title)))
    assert.equal(records.find(row => row.signature?.stage === 'takeaways')?.signature.status, 'PASS')
  })
  check(`${name}: stubbed intake record has null anchored`, () => {
    const intake = records.find(row => row.signature?.stage === 'intake')
    assert.ok(intake, 'missing intake record')
    assert.equal(intake.facts.anchored ?? null, null)
  })
  check(`${name}: no scientific sentinel reaches R/operator`, () => {
    const operator = path.join(root, 'operator')
    assert.ok(files(operator).length > 0)
    for (const file of files(operator)) {
      assert.ok(!file.includes(SECRET))
      assert.ok(!fs.readFileSync(file, 'utf8').includes(SECRET), path.basename(file))
    }
    assert.ok(files(path.join(agent, 'results')).some(file => fs.readFileSync(file).includes(Buffer.from(SECRET))), 'sentinel never entered scientific results')
  })
  return { root, record, records, results: path.join(agent, 'results/evaluate') }
}
// SCHEMAS.md EVAL_PROTOCOL bullet: "`EVAL_INPUTS` and `EVAL_SEEDS` are JSON encodings of `evaluation_inputs`
// and `paired_seed_tests`." Each adapter invocation in an evaluate mode must receive run7's sealed objects.
// Implement's baseline adapter smoke runs in evaluation-work/smoke/ as one complete baseline
// equivalence invocation with the sealed paired_seed_tests unchanged (tools/test_m5_adapter_smoke.js),
// so its invocations are checked here alongside evaluate's.
const isSmoke = row => /\/evaluation-work\/smoke\//.test(row.cwd || '')
function run7Env(name, captureFile, arms, { smoke = false } = {}) {
  const sealed = run7Protocol(), captured = rows(captureFile).filter(row => row.mode !== 'implement')
  check(`${name}: every adapter receives run7's sealed evaluation_inputs and paired_seed_tests`, () => {
    for (const arm of arms) assert.ok(captured.some(row => row.arm === arm && row.mode === 'equivalence' && !isSmoke(row)), `${arm} adapter never ran equivalence`)
    if (smoke) assert.ok(captured.some(row => isSmoke(row) && row.arm === 'baseline' && row.mode === 'equivalence'), 'baseline adapter never smoked')
    for (const row of captured) {
      const where = `${row.arm}/${row.mode}`
      assert.equal(typeof row.inputs, 'string', `${where}: EVAL_INPUTS missing`)
      assert.equal(typeof row.seeds, 'string', `${where}: EVAL_SEEDS missing`)
      assert.deepEqual(JSON.parse(row.inputs), sealed.evaluation_inputs, `${where}: EVAL_INPUTS`)
      assert.deepEqual(JSON.parse(row.seeds), sealed.paired_seed_tests, `${where}: EVAL_SEEDS`)
      assert.deepEqual(JSON.parse(row.protocol), sealed, `${where}: EVAL_PROTOCOL`)
    }
  })
  return captured
}
// "Records must cover exactly the Cartesian product, in seed-major then input-ID order."
function run7Pairs(name, captured) {
  const sealed = run7Protocol()
  const expected = sealed.paired_seed_tests.seeds.flatMap(seed => sealed.evaluation_inputs.ids.map(id => [id, seed]))
  check(`${name}: contract adapters emit exactly ids x seeds in seed-major order`, () => {
    assert.deepEqual(expected.length, 8)
    const emitted = captured.filter(row => row.records)
    assert.ok(emitted.length >= 2, 'no adapter records captured')
    for (const row of emitted) assert.deepEqual(row.records, expected, `${row.arm}/${row.mode}`)
  })
}
async function run7Cases() {
  check('run7 fixture: recorded PREDICTIONS.json bytes match the run7 seal receipt', () => {
    const receipt = readJSON(path.join(RUN7, 'control/seals/0001.json'))
    assert.equal(sha(fs.readFileSync(path.join(RUN7, 'agent/PREDICTIONS.json'))), receipt.sha256)
    const sealed = run7Protocol()
    assert.ok(Object.keys(sealed.evaluation_inputs).length > 1, 'run7 evaluation_inputs has no non-ids keys')
    assert.equal(sealed.paired_seed_tests.kind, 'paired_median')
  })
  const capture = name => path.join(scratch, name + '.capture.jsonl')
  const accepted = await cli('run7-contract', 'equivalence', { run7: { baseline: 'contract', method: 'contract', capture: capture('cli-contract') } })
  verdict('run7 equivalence CLI: contract adapters accepted as valid measurements', accepted, 'equivalence', 'PASS', 0)
  run7Pairs('run7 equivalence CLI', run7Env('run7 equivalence CLI', capture('cli-contract'), ['baseline', 'method']))
  for (const [name, baseline, method] of [['every-key-both', 'every-key', 'every-key'], ['every-key-baseline', 'every-key', 'contract']]) {
    const r = await cli('run7-' + name, 'equivalence', { run7: { baseline, method, capture: capture('cli-' + name) } })
    run7Env(`run7 equivalence CLI ${name}`, capture('cli-' + name), ['baseline', 'method'])
    check(`run7 equivalence CLI ${name}: adapter treating every EVAL_INPUTS key as an input is not accepted`, () => {
      assert.ifError(r.child.error)
      const emitted = rows(capture('cli-' + name)).filter(row => row.arm === 'baseline' && row.records)
      assert.ok(emitted.some(row => row.records.some(([id]) => id === 'pins')), 'fixture did not emit every-key records')
      assert.notEqual(r.child.status, 0)
      assert.notEqual(r.verdict?.status, 'PASS')
      assert.notEqual(r.verdict?.equivalence_pass, true)
    })
  }
  // Through the real stages, as in run7: sealed PREDICTIONS.json, harness run_evaluation.sh, method run_method.sh.
  const good = await pipeline('run7-contract', { run7: { baseline: 'contract', method: 'contract', capture: capture('pipeline-contract') } })
  run7Pairs('run7 pipeline', run7Env('run7 pipeline', capture('pipeline-contract'), ['baseline', 'method'], { smoke: true }))
  check('run7 pipeline: contract adapters accepted as valid equivalence measurements', () => {
    const value = readJSON(path.join(good.results, 'equivalence.json'))
    assert.equal(value.status, 'PASS')
    assert.equal(good.record.facts.equivalence_pass, true)
  })
  // run7's harness now fails implement's baseline adapter smoke (records keyed by every EVAL_INPUTS key).
  const bad = await pipeline('run7-every-key', { stopsAtImplement: true, run7: { baseline: 'every-key', method: 'contract', capture: capture('pipeline-every-key') } })
  check('run7 pipeline every-key harness: the smoke ran it as baseline/equivalence and saw every-key records', () => {
    const smokes = rows(capture('pipeline-every-key')).filter(isSmoke)
    assert.ok(smokes.some(row => row.arm === 'baseline' && row.mode === 'equivalence'), 'baseline adapter never smoked')
    for (const row of smokes) assert.deepEqual(JSON.parse(row.seeds), run7Protocol().paired_seed_tests, 'smoke EVAL_SEEDS')
    assert.ok(smokes.some(row => row.records?.some(([id]) => id === 'pins')), 'fixture did not emit every-key records')
    assert.ok(!rows(capture('pipeline-every-key')).some(row => !isSmoke(row) && row.mode !== 'implement'), 'an evaluate invocation ran')
  })
  check('run7 pipeline: harness treating every EVAL_INPUTS key as an input is not accepted', () => {
    const value = fs.existsSync(path.join(bad.results, 'equivalence.json')) ? readJSON(path.join(bad.results, 'equivalence.json')) : null
    assert.notEqual(value?.status, 'PASS')
    assert.notEqual(bad.record.facts?.equivalence_pass, true)
    assert.notEqual(bad.record.signature.status, 'PASS')
  })
}
async function main() {
  try {
    await run7Cases()
    const valid = await cli('anchors-pass', 'validity', {}, false)
    verdict('validity CLI: every anchor passes; --stage optional', valid, 'validity', 'PASS', 0)
    check('validity preserves exact anchor score', () => {
      assert.deepEqual(valid.verdict.anchors.map(row => row.kind), ['anchor', 'anchor'])
      assert.equal(valid.verdict.anchors_passed, 2)
      assert.equal(valid.verdict.anchors_total, 2)
      assert.equal(valid.verdict.all_passed, true)
      assert.deepEqual(valid.verdict.anchors.map(row => row.id), anchors.map(row => row.id))
    })
    const invalid = await cli('anchors-fail', 'validity', { badAnchor: true })
    verdict('validity CLI: one failed anchor exits 4', invalid, 'validity', 'FAIL', 4)
    check('validity failure classified anchor', () => { assert.equal(invalid.verdict.anchors_passed, 1) })
    for (const config of [{ missingAnchor: true }, { partialAnchor: true }]) {
      const r = await cli('anchor-missing-' + Object.keys(config)[0], 'validity', config)
      verdict('missing anchor measurement is VOID', r, 'validity', 'VOID', 2)
    }
    // SCHEMAS.md validity: references never fail validity; with no anchors validity passes when
    // the method arm's anchor protocol exits 0 with a valid measurement file.
    for (const [name, config, status, code, total] of [
      ['no-anchors', { anchorSet: 'empty' }, 'PASS', 0, 0],
      ['no-anchors-no-file', { anchorSet: 'empty', missingAnchor: true }, 'VOID', 2],
      ['references-off', { anchorSet: 'references', badAnchor: true }, 'PASS', 0, 0],
      ['references-unmeasured', { anchorSet: 'references', partialAnchor: true }, 'PASS', 0, 0],
      ['references-no-file', { anchorSet: 'references', missingAnchor: true }, 'VOID', 2],
      ['mixed-reference-off', { anchorSet: 'mixed', badAnchor: true }, 'PASS', 0, 1],
      ['mixed-anchor-unmeasured', { anchorSet: 'mixed', partialAnchor: true }, 'VOID', 2],
    ]) {
      const r = await cli('validity-' + name, 'validity', config)
      verdict(`validity CLI: ${name}`, r, 'validity', status, code)
      if (status === 'PASS') check(`validity CLI: ${name} anchor score counts anchors only`, () => {
        assert.equal(r.verdict.anchors_total, total)
        assert.equal(r.verdict.anchors_passed, total)
        assert.equal(r.verdict.all_passed, true)
        assert.deepEqual(r.verdict.anchors.map(row => [row.id, row.kind, row.kind === 'reference' ? row.passed : true]),
          anchorsFor(config).map(item => [item.id, item.tolerance === null ? 'reference' : 'anchor', item.tolerance === null ? null : true]))
      })
    }
    for (const [name, config, status] of [
      ['exact', {}, 'PASS'], ['within-tolerance', { delta: 0.005 }, 'PASS'], ['outside-tolerance', { delta: 0.02 }, 'FAIL'],
      ...['order', 'drop', 'duplicate', 'seed'].map(alignment => [alignment, { alignment }, 'FAIL']),
      ['stochastic-paired', { stochastic: true, delta: 0.005 }, 'PASS'],
      ['stochastic-outside', { stochastic: true, delta: 0.02 }, 'FAIL'],
      ['stochastic-underpowered', { stochastic: true, seedCount: 5 }, 'VOID'],
      ['missing-output', { missingOutput: true }, 'VOID'], ['missing-metric', { missingMetric: true }, 'VOID'],
    ]) {
      const r = await cli(name, 'equivalence', config)
      verdict(`equivalence CLI: ${name}`, r, 'equivalence', status, status === 'PASS' ? 0 : status === 'FAIL' ? 5 : 2)
      if (config.alignment) check(`${name}: failed alignment row`, () => assert.ok(r.verdict.metrics.some(row => row.passed === false && row.reason_code === 'counts_or_alignment')))
      if (config.stochastic && status !== 'VOID') check(`${name}: paired effect interval`, () => {
        const metric = r.verdict.metrics[0]
        near(metric.difference_interval[0], config.delta); near(metric.difference_interval[1], config.delta)
        assert.equal(metric.confidence, 0.95)
      })
    }
    for (const [name, config, status] of [
      ['speedup', {}, 'PASS'],
      ['fast-but-invalid', { badAnchor: true }, 'PASS'],
      ['median-pairs', { baselineTimes: [2, 90, 30, 40, 50], methodTimes: [1, 10, 10, 20, 25] }, 'PASS'],
      ['noisy-confidence', { methodTimes: [20, 5, 5, 5, 5] }, 'FAIL'],
      ['equal-cost', { methodTimes: [10, 10, 10, 10, 10] }, 'FAIL'],
      ['higher-cost', { methodTimes: [20, 20, 20, 20, 20] }, 'FAIL'],
      ['more-gpus-higher-cost', { moreGPUs: true }, 'FAIL'],
      ['curve-points', { curves: true, unachieved: true }, 'PASS'],
      ['missing-curve', { curves: true, missingCurve: true }, 'PASS'],
      ['failed-performance-missing-curve', { curves: true, missingCurve: true, methodTimes: [20, 20, 20, 20, 20] }, 'FAIL'],
      ['missing-timing-output', { missingOutput: true }, 'VOID'], ['missing-scope', { missingScope: true }, 'VOID'],
      ['missing-price', { noPrice: true }, 'VOID'],
    ]) {
      const r = await cli(name, 'performance', config)
      verdict(`performance CLI: ${name}`, r, 'performance', status, status === 'FAIL' ? 5 : config.missingCurve ? 2 : status === 'PASS' ? 0 : 2)
      if (!config.missingOutput && !config.missingScope && !config.noPrice) check(`${name}: measured paired statistics and cost`, () => {
        const v = r.verdict
        assert.equal(v.pairs.length, 5)
        const expected = name === 'median-pairs' ? 2 : name === 'equal-cost' ? 1 : name === 'higher-cost' || name === 'failed-performance-missing-curve' ? 0.5 : 2
        near(v.speedup_published, expected)
        near(v.cost_ratio, (config.moreGPUs ? 4 : 1) / expected)
        assert.equal(v.equal_cost, v.cost_ratio <= 1)
        near(v.prediction_ratio, expected / 2)
        assert.equal(v.speedup_tuned, null)
        assert.equal(v.confidence, 0.95)
        assert.equal(v.speedup_interval[1], null)
        if (name === 'noisy-confidence') assert.ok(v.speedup_interval[0] < 1.1)
        for (const pair of v.pairs) {
          assert.deepEqual(pair.order.slice().sort(), ['baseline', 'method'])
          near(pair.speedup, pair.baseline_s / pair.method_s)
          near(pair.baseline_usd, pair.baseline_s * pair.baseline_gpus * (4 / 8) / 3600)
          near(pair.method_usd, pair.method_s * pair.method_gpus * (4 / 8) / 3600)
        }
      })
      if (status === 'PASS' || config.missingCurve) check(`${name}: curve measured or explicitly inapplicable`, () => {
        const curve = readJSON(path.join(r.out, 'curve.json'))
        assert.deepEqual(curve.input_hashes, r.manifest.input_hashes)
        if (config.missingCurve) { assert.equal(curve.status, 'VOID'); assert.notEqual(curve.curve_points, 3) }
        else if (!config.curves) { assert.equal(curve.status, 'PASS'); assert.equal(curve.not_applicable, true); assert.equal(curve.curve_points, 0) }
        else {
          assert.equal(curve.status, 'PASS'); assert.equal(curve.curve_points, 3)
          assert.deepEqual(curve.points.map(point => point.compute_budget), [2, 4, 8])
          for (const point of curve.points) for (const arm of ['baseline', 'method']) {
            assert.equal(point[arm].status, 'PASS'); near(point[arm].outcome, 1)
            assert.equal(point[arm].target_achieved, false)
            assert.deepEqual(point[arm].uncertainty, { min: 1, max: 1 })
            assert.ok(point[arm].allocated_gpu_hours > 0); assert.ok(point[arm].usd > 0)
          }
        }
      })
    }
    for (const [name, config, status, code, kind] of [
      ['pass', {}, 'PASS', 0, null],
      ['curves', { curves: true }, 'PASS', 0, null],
      ['missing-curves', { curves: true, missingCurve: true }, 'VOID', 2, 'parse'],
      ['failed-performance-missing-curves', { curves: true, missingCurve: true, methodTimes: [20, 20, 20, 20, 20] }, 'FAIL', 5, 'numeric'],
      ['anchor-fail-fast', { badAnchor: true }, 'FAIL', 4, 'anchor'],
      ['equivalence-fail', { delta: 0.02 }, 'FAIL', 5, 'numeric'],
      ['cost-fail', { moreGPUs: true }, 'FAIL', 5, 'numeric'],
      ['missing', { missingOutput: true }, 'VOID', 2, 'parse'],
      ['no-anchors', { anchorSet: 'empty' }, 'PASS', 0, null],
      ['references-only', { anchorSet: 'references', badAnchor: true }, 'PASS', 0, null],
    ]) {
      const r = await pipeline(name, config)
      const anchored = anchorsFor(config).some(item => item.tolerance !== null)
      check(`${name}: overall stage verdict`, () => {
        assert.equal(r.record.signature.status, status)
        assert.equal(r.record.signature.exit_code, code)
        if (kind) assert.equal(r.record.signature.error_class, kind)
        if (config.badAnchor && anchored) assert.equal(r.record.signature.exit_kind, 'anchor')
      })
      if (!anchored) check(`${name}: no anchors: reproduce passes on stock verification; run_valid null`, () => {
        const reproduce = r.records.find(row => row.signature?.stage === 'reproduce')
        assert.equal(reproduce.signature.status, 'PASS')
        assert.equal(reproduce.facts.stock_verified, true)
        assert.equal(reproduce.facts.anchors_total, 0)
        assert.equal(reproduce.signature.run_valid ?? null, null, 'reproduce run_valid')
        assert.equal(r.record.facts.validity_pass, true)
        assert.equal(r.record.signature.run_valid ?? null, null, 'evaluate run_valid')
      })
      if (config.badAnchor && anchored) check(`${name}: validity failure sets run_valid false`, () => {
        assert.equal(r.record.signature.run_valid, false)
      })
      check(`${name}: immutable manifest and scorer receipts`, () => {
        const file = path.join(r.root, 'control/evaluate/manifest.json')
        const manifest = readJSON(file)
        assert.equal(fs.statSync(file).mode & 0o777, 0o444)
        assert.deepEqual(Object.keys(manifest).sort(), ['remote_directory', 'protocol', 'prediction', 'box', 'gpu_count',
          'run_timeout_s', 'method_files', 'anchors', 'input_hashes'].sort())
        assert.deepEqual(manifest.protocol, protocol(config))
        for (const key of Object.keys(provenance())) assert.match(manifest.input_hashes[key], /^[0-9a-f]{64}$/)
        assert.ok(Object.keys(manifest.input_hashes.evaluators).includes('eval_performance.py'))
        const receipts = files(path.join(r.root, 'control/receipts')).filter(file => file.endsWith('.json'))
        assert.ok(receipts.some(file => /evaluate-upload/.test(file)))
        assert.ok(receipts.some(file => /evaluate-validity/.test(file)))
        for (const file of receipts) assert.equal(readJSON(file).gpu_busy_known, false)
      })
      check(`${name}: three independent verdicts`, () => {
        const values = Object.fromEntries(['validity', 'equivalence', 'performance'].map(stage => [stage, readJSON(path.join(r.results, stage + '.json'))]))
        for (const [stage, value] of Object.entries(values)) assert.equal(r.record.facts[stage + '_pass'], value[stage + '_pass'] ?? null, stage + ' fact disagrees with verdict')
        if (status === 'PASS') {
          for (const value of Object.values(values)) assert.equal(value.status, 'PASS')
          assert.equal(r.record.facts.equal_cost, true); near(r.record.facts.speedup_published, 2)
          near(r.record.facts.cost_ratio, 0.5); near(r.record.facts.prediction_ratio, 1)
          assert.equal(r.record.facts.curve_points, config.curves ? 3 : 0)
        }
        if (name === 'missing-curves') {
          assert.equal(values.performance.status, 'PASS')
          assert.equal(r.record.facts.curve_points, null)
        }
        if (name === 'failed-performance-missing-curves') assert.equal(values.performance.status, 'FAIL')
        if (config.delta) {
          assert.equal(values.validity.status, 'PASS')
          assert.equal(values.equivalence.status, 'FAIL')
          assert.equal(values.performance.status, 'VOID')
        }
        if (config.badAnchor && anchored) {
          assert.equal(values.validity.status, 'FAIL')
          assert.equal(values.equivalence.status, 'VOID'); assert.equal(values.performance.status, 'VOID')
          for (const key of ['equal_cost', 'speedup_published', 'cost_ratio', 'prediction_ratio', 'curve_points']) assert.equal(r.record.facts[key], null)
          // Separate performance CLI proved this same fast adapter passes performance.
          // Fail-fast validity must still stop overall PASS and leave later verdicts VOID.
        }
      })
    }
  } catch (error) { failures++; console.log(`FAIL test harness: ${error.stack}`) }
  finally {
    function writable(directory) {
      fs.chmodSync(directory, 0o700)
      for (const entry of fs.readdirSync(directory, { withFileTypes: true })) if (entry.isDirectory()) writable(path.join(directory, entry.name))
    }
    const registry = path.join(scratch, 'remote-roots')
    if (fs.existsSync(registry)) for (const directory of new Set(fs.readFileSync(registry, 'utf8').trim().split('\n'))) {
      assert.match(directory, /^\/tmp\/m5-[0-9a-f-]{36}$/)
      if (fs.existsSync(directory)) { writable(directory); fs.rmSync(directory, { recursive: true, force: true }) }
    }
    writable(scratch)
    fs.rmSync(scratch, { recursive: true, force: true })
  }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : 'all checks passed')
  process.exitCode = failures ? 1 : 0
}
main()
