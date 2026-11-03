#!/usr/bin/env node
'use strict'

// Black-box contract tests for U52, the standalone unit probe in reproduce (m5/SCHEMAS.md "Standalone
// unit probe (U52)", "Unit equivalence check (U51)" for validation, unit-file requirements and the sample,
// the Concurrency probe bullets "Unit mode (U50b)" to "The standalone unit probe (U52) validates",
// "A/results/reproduce/" and "C/receipts/"). Never inspect pipeline.js, signatures.py, concurrency_probe.py
// or git history.
//
// The fake box and harness follow tools/test_m5_units_check.js (whose fake agents this file re-exports).
// The fake box really executes every box command in a temporary shared run directory, so the written
// remote probe script and reference file run for real. A `python3` wrapper on the fake box's PATH
// records each probe invocation (arguments, working directory, stale entries, snapshots of the remote
// probe script and reference file), runs the real probe with a fast fake `harness/run_units.sh`, and,
// for validator cases, rewrites the probe's genuine concurrency.json (MUTATIONS below) or its exit status.
// Usage: node tools/test_m5_units_probe_pipeline.js [case-name regex]
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const crypto = require('node:crypto')
const assert = require('node:assert/strict')
const { spawn } = require('node:child_process')

// ---- Mutations of a genuine unit-mode concurrency.json (applied on the fake box) ------------------
// Each returns a new value, { __text } (raw file content) or { __remove: true }.
const clone = value => JSON.parse(JSON.stringify(value))
const ranArm = arm => arm.wall_s !== null
const meanOf = values => values.reduce((sum, value) => sum + value, 0) / values.length
// Recompute every derived top-level value from the arms (SCHEMAS.md unit-mode concurrency.json bullets),
// keeping `outcome`.
function recompute(v) {
  const counted = prefix => v.arms.filter(arm => arm.label.startsWith(prefix) && ranArm(arm) && arm.all_ok)
  const a = counted('a-'), b = counted('b-')
  v.serial_wall_s = a.length ? meanOf(a.map(arm => arm.wall_s)) : null
  v.separate_wall_s = b.length ? meanOf(b.map(arm => arm.wall_s)) : null
  v.batches = [2, 4].map(n => {
    const executed = v.arms.filter(arm => arm.label.startsWith(`c${n}-`) && ranArm(arm))
    const wall_s = executed.length ? meanOf(executed.map(arm => arm.wall_s)) : null
    const all_ok = executed.length > 0 && executed.every(arm => arm.all_ok)
    return { n, wall_s, all_ok, skipped: executed.length === 0,
      factor: all_ok && v.outcome === 'measured' && v.serial_wall_s !== null ? v.serial_wall_s / wall_s : null }
  })
  const factors = v.batches.map(batch => batch.factor).filter(factor => factor !== null)
  v.factor = factors.length ? Math.max(...factors) : null
  return v
}
const notRun = label => ({ label, wall_s: null, all_ok: false, skipped: true, cpu_s: null, effective_cores: null,
  busy_fraction: null, mem_available_min_kb: null, threads_max: null, shared_changes: null, invocations: [] })
const MUTATIONS = {
  // Valid variants (still exactly the unit-mode shape).
  'valid-late-skip': v => {
    // Budget skip from c4-1 on: n=2 counted, n=4 skipped; only b-1 saw shared changes.
    v = clone(v)
    v.arms = v.arms.map((arm, i) => i >= 3 ? notRun(arm.label) : { ...arm, shared_changes: arm.label === 'b-1' ? 2 : 0 })
    return recompute(v)
  },
  'valid-shared-zero': v => {
    v = clone(v)
    for (const arm of v.arms) if (ranArm(arm)) arm.shared_changes = 0
    return v
  },
  'valid-shared-one-arm': v => {
    v = clone(v)
    for (const arm of v.arms) if (ranArm(arm)) arm.shared_changes = arm.label === 'c4-2' ? 1 : 0
    return v
  },
  // Invalid files.
  'missing-file': () => ({ __remove: true }),
  'nonzero-exit': v => v,
  'not-object': () => ({ __text: '[]\n' }),
  'not-json': () => ({ __text: '{"mode": "units",\n' }),
  'missing-key': v => { v = clone(v); delete v.nproc; return v },
  'renamed-key': v => { v = clone(v); v.separate_wall = v.separate_wall_s; delete v.separate_wall_s; return v },
  'extra-top-key': v => ({ ...clone(v), note: 'x' }),
  'extra-arm-key': v => { v = clone(v); v.arms[2].note = 1; return v },
  'missing-arm-key': v => { v = clone(v); delete v.arms[5].threads_max; return v },
  'extra-batch-key': v => { v = clone(v); v.batches[1].note = 1; return v },
  'extra-invocation-key': v => { v = clone(v); v.arms[1].invocations[0].note = 1; return v },
  'extra-sample-key': v => { v = clone(v); v.sample[0].id = 'x'; return v },
  'mode-command': v => ({ ...clone(v), mode: 'command' }),
  'outcome-unknown': v => ({ ...clone(v), outcome: 'great' }),
  'mps-true': v => ({ ...clone(v), mps: true }),
  'command-mode-shape': () => ({ mps: false, mps_failed: false, single_wall_s: [1, 1, 1],
    batches: [{ n: 2, wall_s: 1, all_ok: true, skipped: false, factor: 2 }, { n: 4, wall_s: 2, all_ok: true, skipped: false, factor: 2 }], factor: 2 }),
  'batch-factor-wrong': v => {
    v = clone(v)
    v.batches[0].factor *= 1.5
    v.factor = Math.max(v.batches[0].factor, v.batches[1].factor)
    return v
  },
  'batch4-factor-wrong': v => {
    v = clone(v)
    v.batches[1].factor *= 0.5
    v.factor = Math.max(v.batches[0].factor, v.batches[1].factor)
    return v
  },
  'factor-not-largest': v => {
    v = clone(v)
    const [low, high] = v.batches.map(batch => batch.factor).sort((x, y) => x - y)
    v.factor = low < high ? low : low * 0.9
    return v
  },
  'factor-above-largest': v => { v = clone(v); v.factor = v.factor * 1.25; return v },
  'factor-null-when-measured': v => ({ ...clone(v), factor: null }),
  'batch-factor-null-when-measured': v => {
    v = clone(v)
    v.batches[0].factor = null
    v.factor = v.batches[1].factor
    return v
  },
  // Applied to an outputs_mismatch file whose c arms all counted: factors present without `measured`.
  'factor-when-not-measured': v => {
    v = clone(v)
    for (const batch of v.batches) batch.factor = v.serial_wall_s / batch.wall_s
    v.factor = Math.max(...v.batches.map(batch => batch.factor))
    return v
  },
  'top-factor-when-not-measured': v => ({ ...clone(v), factor: 1.5 }),
  'nan-number': v => { v = clone(v); v.arms[0].busy_fraction = '__NAN__'; return v },
  'infinite-number': v => { v = clone(v); v.mem_total_kb = '__INF__'; return v },
  'infinite-factor': v => { v = clone(v); v.batches[0].factor = '__INF__'; return v },
  'negative-number': v => { v = clone(v); v.arms[2].mem_available_min_kb = -1; return v },
  'negative-shared-changes': v => { v = clone(v); v.arms[3].shared_changes = -1; return v },
  'negative-invocation-number': v => { v = clone(v); v.arms[0].invocations[0].nivcsw = -3; return v },
  'string-number': v => { v = clone(v); v.serial_wall_s = String(v.serial_wall_s); return v },
  'arm-order': v => { v = clone(v); [v.arms[1], v.arms[2]] = [v.arms[2], v.arms[1]]; return v },
  'arm-order-reversed': v => { v = clone(v); v.arms.reverse(); return v },
  'arm-count-7': v => { v = clone(v); v.arms.pop(); return v },
  'arm-count-9': v => { v = clone(v); v.arms.push(clone(v.arms[7])); return v },
  'arm-label-wrong': v => { v = clone(v); v.arms[4].label = 'c4-3'; return v },
  'batch-order': v => { v = clone(v); v.batches.reverse(); return v },
  'batch-count-1': v => { v = clone(v); v.batches.pop(); return v },
}
const NONFINITE = { '"__NAN__"': 'NaN', '"__INF__"': 'Infinity' }

// Fake agents: the U51 suite's (intake from the reproduce fixture; repairs recorded and declined).
const stub = require('./test_m5_units_check.js')
module.exports = { run: stub.run, exportSession: stub.exportSession, MUTATIONS, NONFINITE }
if (require.main !== module) return

const fixture = require('./test_m5_reproduce.js')
const ROOT = path.resolve(__dirname, '..')
const STAGES = ['intake', 'reproduce', 'profile', 'seal', 'propose', 'implement', 'evaluate', 'takeaways']
const PROBE = 'units-probe-pipeline-61204'
const FOUR = ['units_outcome', 'units_factor_2', 'units_factor_4', 'units_shared_writes']
const OUTCOMES = ['invalid_units', 'failed', 'baseline_mismatch', 'outputs_mismatch', 'skipped', 'measured']
const ANCHORS = [{ id: 'first', published_value: 100, tolerance: 1, quantity: 'fixture', source: 'fixture' },
  { id: 'second', published_value: 0, tolerance: 0, quantity: 'fixture', source: 'fixture' }]
const PASSING = { first: 100, second: 0 }
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const rows = file => fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : []
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex')
function json(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, JSON.stringify(value) + '\n')
}
function script(file, body, header = '#!/usr/bin/env bash\nset -eu\n') {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, header + body + '\n', { mode: 0o700 })
}
function contents(directory) {
  const result = {}
  const visit = (parent, prefix) => {
    for (const entry of fs.readdirSync(parent, { withFileTypes: true })) {
      const file = path.join(parent, entry.name)
      if (entry.isDirectory()) visit(file, prefix + entry.name + '/')
      else if (entry.isFile()) result[prefix + entry.name] = fs.readFileSync(file).toString('base64')
    }
  }
  if (fs.existsSync(directory)) visit(directory, '')
  return result
}
const realPython = (() => {
  for (const directory of (process.env.PATH || '').split(':')) {
    const file = path.join(directory, 'python3')
    try { fs.accessSync(file, fs.constants.X_OK); return file } catch {}
  }
  throw new Error('python3 not found on PATH')
})()

const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_units_probe_pipeline_'))
const pipeline = path.join(scratch, 'pipeline')
const ONLY = process.argv[2] ? new RegExp(process.argv[2]) : null
let checks = 0, failures = 0
function check(label, test) {
  if (ONLY && !ONLY.test(label)) return
  checks++
  try { test(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${error.message.replace(/\s*\n\s*/g, ' ')}`) }
}

// ---- Units and reference bytes --------------------------------------------------------------------
const unitId = i => `zq${i}.unit:${i}+k=v`
const unitOutputs = i => i % 2 ? [`res-${i}/zq${i}.out.bin`, `res-${i}/nested/zq${i}.log`] : [`res-${i}/zq${i}.out.bin`]
const makeUnits = costs => costs.map((cost_s, i) => ({ id: unitId(i), outputs: unitOutputs(i), cost_s }))
function sampleOf(units) {
  const sorted = units.map((unit, index) => ({ index, cost: unit.cost_s })).sort((a, b) => a.cost - b.cost || a.index - b.index)
  const start = Math.floor((units.length - 4) / 2)
  return sorted.slice(start, start + 4).map(row => row.index)
}
const refBytes = (i, j) => Buffer.concat([Buffer.from(`reference unit ${i} output ${j}\n`), Buffer.from([0, 255, i & 0xff, j, 10, 13, 0])])
const UNITS_8 = makeUnits([30, 5, 12.5, 70, 2, 44, 18, 9])
const valid = units => ({ units })

// ---- One workflow run -----------------------------------------------------------------------------
// spec: { units (object, raw string or null), runUnits (false = absent), unitsProbe / unitsCheck ('ref',
// 'ref-relative', function of {reference, root}, raw value, undefined = absent), refMissing ['pos:j'],
// refDirectory ['pos:j'], refOmitNonSample, sleepS (per run_units.sh invocation), fail / corrupt [work dir
// names], sharedWrites, remoteUnits (raw content setup.sh writes over remote harness/units.json),
// mutation, mutationRc, anchorsBudget, fetchFailProbe, setupRc }
async function execute(name, spec) {
  if (ONLY && !ONLY.test(name)) return null
  const root = path.join(scratch, name)
  const agent = path.join(root, 'agent')
  const source = path.join(root, 'previous run', 'A', 'harness')
  const reference = path.join(root, 'previous run', 'A', 'results', 'reproduce', 'out')
  const box = path.join(root, 'box')
  const configFile = path.join(root, 'units-config.json')
  const unitsCalls = path.join(root, 'units-calls.jsonl')
  const commandCalls = path.join(root, 'command-calls.log')
  const probeCalls = path.join(root, 'probe-calls')
  const helper = path.join(root, 'fake-units.js')
  for (const directory of [box, probeCalls, path.join(root, 'home')]) fs.mkdirSync(directory, { recursive: true })

  const units = spec.units && typeof spec.units === 'object' ? spec.units.units : null
  const sample = units ? sampleOf(units) : []
  const outputs = {}
  fs.mkdirSync(reference, { recursive: true })
  for (const [i, unit] of (units ?? []).entries()) {
    outputs[unit.id] = {}
    unit.outputs.forEach((rel, j) => {
      outputs[unit.id][rel] = refBytes(i, j).toString('base64')
      const key = `${sample.indexOf(i)}:${j}`
      const file = path.join(reference, rel)
      if (!sample.includes(i) && spec.refOmitNonSample) return
      if (sample.includes(i) && spec.refMissing?.includes(key)) return
      fs.mkdirSync(path.dirname(file), { recursive: true })
      if (sample.includes(i) && spec.refDirectory?.includes(key)) fs.mkdirSync(file)
      else fs.writeFileSync(file, refBytes(i, j))
    })
  }
  fs.writeFileSync(path.join(reference, 'anchors_measured.json'), '{"first":-1}\n')
  json(configFile, { outputs, sleep_s: spec.sleepS ?? 0.05, fail: spec.fail ?? [], corrupt: spec.corrupt ?? [],
    sharedWrites: Boolean(spec.sharedWrites) })

  // Fake unit runner (harness/run_units.sh): writes the listed units' reference bytes under out/, in its
  // working directory; `corrupt` flips one byte, `fail` exits 3, `sharedWrites` writes through data/.
  fs.writeFileSync(helper, `'use strict'
const fs = require('node:fs'), path = require('node:path')
const cfg = JSON.parse(fs.readFileSync(${JSON.stringify(configFile)}, 'utf8'))
const ids = process.argv.slice(2)
const name = path.basename(process.cwd())
fs.appendFileSync(${JSON.stringify(unitsCalls)}, JSON.stringify({ name, ids, ms: Date.now() }) + '\\n')
let corrupt = cfg.corrupt.includes(name)
for (const id of ids) for (const [rel, data] of Object.entries(cfg.outputs[id] ?? {})) {
  const bytes = Buffer.from(data, 'base64')
  if (corrupt) { bytes[bytes.length >> 1] ^= 1; corrupt = false }
  const file = path.join('out', rel)
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, bytes)
}
if (cfg.sharedWrites) fs.writeFileSync(path.join('data', 'created-' + name), 'x')
process.stdout.write('UNITS_STDOUT ' + name + '\\n')
const until = Date.now() + cfg.sleep_s * 1000
const cell = new Int32Array(new SharedArrayBuffer(4))
while (Date.now() < until) Atomics.wait(cell, 0, 0, 10)
process.exit(cfg.fail.includes(name) ? 3 : 0)
`)
  const node = JSON.stringify(process.execPath), helperArg = JSON.stringify(helper)
  // Harness of a "previous run", copied by args.harness_from. Setup leaves stale probe state behind.
  script(path.join(source, 'setup.sh'), `mkdir -p out baseline-published data profiler evaluation-work concurrency-work/stale-dir out/concurrency
printf 'published\\n' > baseline-published/pin
printf 'input\\n' > data/input
printf 'stale\\n' > concurrency-work/stale-dir/x
printf 'stale\\n' > out/concurrency/stale.txt
printf 'stale probe\\n' > profiler/concurrency_probe.py
printf '{"sha256": {}}\\n' > profiler/units_reference.json
printf 'note\\n' > top-file.txt
${spec.remoteUnits !== undefined ? `printf '%s' ${JSON.stringify(spec.remoteUnits)} > harness/units.json` : ''}
exit ${spec.setupRc ?? 0}`)
  script(path.join(source, 'run_command.sh'), `test -f baseline-published/pin\nmkdir -p out\nprintf 'full\\n' >> ${JSON.stringify(commandCalls)}\nprintf 'command ran\\n' > out/command.log`)
  script(path.join(source, 'run_anchors.sh'), `bash harness/run_command.sh\nprintf '%s\\n' '${JSON.stringify(PASSING)}' > out/anchors_measured.json`)
  if (spec.runUnits !== false) script(path.join(source, 'run_units.sh'), `exec ${node} ${helperArg} "$@"`)
  if (spec.units !== null && spec.units !== undefined)
    fs.writeFileSync(path.join(source, 'units.json'), typeof spec.units === 'string' ? spec.units : JSON.stringify(spec.units, null, 2) + '\n')

  const args = { run_root: root, tag: name, harness_from: source,
    stub: { profile: 'PASS', seal: 'PASS', propose: 'PASS', implement: 'PASS', evaluate: 'PASS' } }
  const argValue = value => value === 'ref' ? { reference } : value === 'ref-relative' ? { reference: path.relative(pipeline, reference) }
    : typeof value === 'function' ? value({ reference, root }) : value
  if (spec.unitsProbe !== undefined) args.units_probe = argValue(spec.unitsProbe)
  if (spec.unitsCheck !== undefined) args.units_check = argValue(spec.unitsCheck)
  if (spec.anchorsBudget) args.stage_budgets_s = { anchors: spec.anchorsBudget }
  json(path.join(root, 'control/args.json'), args)

  // python3 on the fake box: records and runs the real probe; optionally rewrites its output.
  const mutationFile = path.join(root, 'mutation.json')
  if (spec.mutation) json(mutationFile, { name: spec.mutation, rc: spec.mutationRc ?? null })
  const mutate = path.join(root, 'mutate.js')
  fs.writeFileSync(mutate, `'use strict'
const fs = require('node:fs')
const { MUTATIONS, NONFINITE } = require(${JSON.stringify(__filename)})
const cfg = JSON.parse(fs.readFileSync(${JSON.stringify(mutationFile)}, 'utf8'))
const file = 'out/concurrency/concurrency.json'
const before = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : undefined
fs.writeFileSync(${JSON.stringify(path.join(root, 'genuine.json'))}, JSON.stringify(before ?? null))
const after = MUTATIONS[cfg.name](before)
if (after && after.__remove) fs.rmSync(file, { force: true })
else {
  let text = after && after.__text !== undefined ? after.__text : JSON.stringify(after, null, 1) + '\\n'
  for (const [from, to] of Object.entries(NONFINITE)) text = text.split(from).join(to)
  fs.writeFileSync(file, text)
}
process.exit(cfg.rc ?? Number(process.argv[2]))
`)
  script(path.join(root, 'box-bin/python3'), `probe=no
for arg in "$@"; do [[ $arg != profiler/concurrency_probe.py ]] || probe=yes; done
[[ $probe == yes ]] || exec ${JSON.stringify(realPython)} "$@"
call=${JSON.stringify(probeCalls)}/$(date +%s%N)
mkdir -p "$call"
printf '%s\\n' "$@" > "$call/argv"
pwd -P > "$call/cwd"
[[ ! -e out/concurrency/stale.txt ]] || : > "$call/stale-out"
[[ ! -e concurrency-work/stale-dir ]] || : > "$call/stale-work"
cp profiler/concurrency_probe.py "$call/probe.py" 2>/dev/null
cp profiler/units_reference.json "$call/units_reference.json" 2>/dev/null
${JSON.stringify(realPython)} "$@"
rc=$?
[[ ! -f ${JSON.stringify(mutationFile)} ]] || exec ${node} ${JSON.stringify(mutate)} "$rc"
exit "$rc"`, '#!/usr/bin/env bash\n')
  script(path.join(root, 'box-bin/nvidia-smi'), 'exit 1')

  const callsFile = path.join(root, 'calls.jsonl')
  const replaceProbe = path.join(root, 'replace-probe.js')
  const originalProbe = fs.readFileSync(path.join(ROOT, 'm5/box_probe.sh'), 'utf8')
  const fakeProbe = '#!/usr/bin/env bash\nset -eu\nmkdir -p out\nprintf \'{"label":"probe"}\\n\' >> "$M5_REPRODUCE_CALLS"\nprintf \'{"kernel":"' + PROBE + '","nvcc":[],"cmake":null}\\n\' > out/probe.json\n'
  fs.writeFileSync(replaceProbe, `
const fs = require('node:fs'), path = require('node:path')
function visit(directory) {
  let entries
  try { entries = fs.readdirSync(directory, { withFileTypes: true }) } catch { return }
  for (const entry of entries) {
    const file = path.join(directory, entry.name)
    if (entry.isDirectory()) { if (entry.name !== 'concurrency-work') visit(file) }
    else if (entry.isFile() && entry.name.endsWith('.sh')) {
      let text
      try { text = fs.readFileSync(file, 'utf8') } catch { continue }
      if (text !== ${JSON.stringify(originalProbe)}) continue
      fs.appendFileSync(process.env.M5_REPRODUCE_CALLS, '{"label":"probe-upload"}\\n')
      fs.writeFileSync(file, ${JSON.stringify(fakeProbe)})
    }
  }
}
visit(process.env.BOX_ROOT)
`)
  // As in the U51 fixture, a boxrun command waits for every remote .sh to have its .rc (here up to 30 s).
  // replace-probe.js tolerates entries that vanish while it walks the box: the probe runs detached and
  // creates and removes concurrency-work/ entries meanwhile; a crash there (set -e) returned the box
  // before the probe ended, and boxrun recorded rc null, fetched false. Box calls go to box-calls.log.
  script(path.join(root, 'bin/box'), 'command=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\nexport PATH="$BOX_ROOT/../box-bin:$PATH"\ncd -- "$BOX_ROOT"\n' +
    'printf "start %s %s timeout=%s\\n" "$(date +%s.%N)" "${#command}" "$([[ $command == *timeout* ]] && echo yes || echo no)" >> "$BOX_ROOT/../box-calls.log"\n' +
    'trap \'printf "end %s rc-files=%s\\n" "$(date +%s.%N)" "$(cd "$BOX_ROOT" && echo m5-*/*.rc)" >> "$BOX_ROOT/../box-calls.log"\' EXIT\n' +
    'bash -c "$command"\n"$M5_TEST_NODE" "$M5_REPLACE_PROBE"\nif [[ $command == *timeout* ]]; then\n  for ((i=0; i<3000; i++)); do\n    pending=false\n    for file in "$BOX_ROOT"/m5-*/*.sh; do\n      [[ -f $file ]] || continue\n      [[ -f ${file%.sh}.rc ]] || pending=true\n    done\n    [[ $pending == true ]] || break\n    sleep 0.01\n  done\nfi\nexit 0')
  // fetchFailProbe: every fetch of the concurrency log fails, so its receipt has fetched=false (infra).
  script(path.join(root, 'bin/fetch'), 'source=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\ncd -- "$BOX_ROOT"\n' +
    (spec.fetchFailProbe ? "[[ $source != *-concurrency.log ]] || { echo 'simulated failed fetch' >&2; exit 1; }\n" : '') + 'exec cp -r -- "$source" "$2"')
  const fixtureConfig = { anchors: ANCHORS, measured: PASSING }
  const stderrFile = path.join(root, 'stderr.log')
  const stdout = fs.openSync(path.join(root, 'stdout.log'), 'w'), stderr = fs.openSync(stderrFile, 'w')
  let child
  const spawnedMs = Date.now()
  try {
    child = await new Promise(resolve => {
      const proc = spawn(process.execPath, [path.join(pipeline, 'idea/wf.js'), '--script', path.join(pipeline, 'm5/pipeline.js'),
        '--args', path.join(root, 'control/args.json'), '--out', path.join(agent, 'wf'), '--disable-family', 'claude'], {
        cwd: pipeline, timeout: 150000, killSignal: 'SIGKILL', stdio: ['ignore', stdout, stderr],
        env: { ...process.env, HOME: path.join(root, 'home'), M5_RAIDS_LEDGER: path.join(scratch, 'raids.jsonl'),
          WF_STUB: __filename, M5_REPRODUCE_ROOT: root, M5_REPRODUCE_CONFIG: JSON.stringify(fixtureConfig),
          M5_REPRODUCE_CALLS: callsFile, M5_TEST_NODE: process.execPath, M5_REPLACE_PROBE: replaceProbe,
          BOX_ROOT: box, BOX: path.join(root, 'bin/box'), FETCH: path.join(root, 'bin/fetch'),
          ...(spec.fetchFailProbe ? { BOXRUN_FETCH_WAIT_S: '0' } : {}) },
      })
      let error
      proc.on('error', value => { error = value })
      proc.on('close', (status, signal) => resolve({ status, signal, error }))
    })
  } finally { fs.closeSync(stdout); fs.closeSync(stderr) }
  check(`${name}: workflow completes`, () => {
    assert.ifError(child.error)
    assert.equal(child.status, 0, `signal ${child.signal}; ${fs.readFileSync(stderrFile, 'utf8').slice(-1000)}`)
  })
  const records = rows(path.join(root, 'operator/signatures.jsonl')).map(row => ({ ...row.signature, facts: row.facts }))
  const receiptDir = path.join(root, 'control/receipts')
  const receipts = fs.existsSync(receiptDir) ? fs.readdirSync(receiptDir).sort().filter(file => file.endsWith('.json'))
    .map(file => ({ operation: file.slice(5, -5), ...read(path.join(receiptDir, file)) })) : []
  const runDir = () => {
    const remote = fs.readdirSync(box).filter(entry => entry.startsWith('m5-')).map(entry => path.join(box, entry))
      .filter(directory => fs.existsSync(path.join(directory, 'harness')))
    assert.equal(remote.length, 1, 'expected one remote run directory')
    return remote[0]
  }
  const probeRuns = fs.readdirSync(probeCalls).sort().map(entry => {
    const directory = path.join(probeCalls, entry)
    const file = name => path.join(directory, name)
    return { argv: fs.readFileSync(file('argv'), 'utf8').split('\n').slice(0, -1), cwd: fs.readFileSync(file('cwd'), 'utf8').trim(),
      staleOut: fs.existsSync(file('stale-out')), staleWork: fs.existsSync(file('stale-work')),
      probe: fs.existsSync(file('probe.py')) ? fs.readFileSync(file('probe.py')) : null,
      reference: fs.existsSync(file('units_reference.json')) ? fs.readFileSync(file('units_reference.json')) : null }
  })
  const genuineFile = path.join(root, 'genuine.json')
  return { name, spec, root, agent, reference, records, receipts, runDir, spawnedMs, units, sample, probeRuns,
    genuine: fs.existsSync(genuineFile) ? read(genuineFile) : undefined,
    calls: rows(callsFile), unitsCalls: rows(unitsCalls), commandRan: fs.existsSync(commandCalls),
    stage: label => records.find(row => row.stage === label) }
}

// ---- Shared checks --------------------------------------------------------------------------------
function statusChecks(r, status, errorClass = null, mode = 'unit-probe') {
  if (!r) return
  check(`${r.name}: reproduce ${status}${errorClass ? ` (${errorClass})` : ''}; later stages SKIPPED except takeaways`, () => {
    const signature = r.stage('reproduce')
    const summary = JSON.stringify({ status: signature?.status, error_class: signature?.error_class, facts: signature?.facts,
      receipts: r.receipts.map(receipt => `${receipt.operation}:${receipt.rc}:${receipt.timed_out}:${receipt.fetched}`) })
    assert.deepEqual(r.records.filter(row => STAGES.includes(row.stage)).map(row => [row.stage, row.status]),
      STAGES.map(label => [label, label === 'intake' || label === 'takeaways' ? 'PASS' : label === 'reproduce' ? status : 'SKIPPED']), summary)
    if (errorClass) {
      assert.equal(signature.error_class, errorClass)
      assert.equal(signature.exit_code, { anchor: 4, timeout: 3 }[errorClass] ?? 2)
    }
    assert.ok(!r.calls.some(call => ['seal', 'propose', 'implement', 'evaluate'].includes(call.label)), `scientific call in ${mode} mode`)
  })
}
function nullFacts(r, label = 'the four unit-probe facts null') {
  if (!r) return
  check(`${r.name}: ${label}`, () => {
    const facts = r.stage('reproduce')?.facts
    assert.ok(facts, 'no reproduce record')
    for (const key of FOUR) {
      assert.ok(Object.hasOwn(facts, key), `${key} missing from executed reproduce facts`)
      assert.equal(facts[key], null, key)
    }
  })
}
const afterProbe = r => {
  const at = r.receipts.findIndex(receipt => receipt.operation === 'probe')
  assert.ok(at >= 1, `no probe receipt: ${r.receipts.map(x => x.operation)}`)
  return r.receipts.slice(at + 1)
}
function earlyParseChecks(r, receiptsWanted) {
  if (!r) return
  statusChecks(r, 'FAIL', 'parse')
  nullFacts(r)
  check(`${r.name}: ${receiptsWanted.length ? 'probe only, no harness upload' : 'no box receipt'}; nothing ran`, () => {
    assert.deepEqual(r.receipts.map(receipt => receipt.operation), receiptsWanted)
    assert.deepEqual(r.unitsCalls, [], 'a unit command ran')
    assert.deepEqual(r.probeRuns, [], 'the concurrency probe ran')
    assert.equal(r.commandRan, false, 'the baseline command ran')
    assert.ok(!r.calls.some(call => /repair/.test(call.label)), 'repair call')
    if (!receiptsWanted.length) assert.ok(!r.calls.some(call => ['probe', 'probe-upload'].includes(call.label)), 'box probe ran')
  })
}
const expectedShared = file => {
  const ran = file.arms.filter(ranArm)
  return ran.length === 0 ? null : ran.some(arm => arm.shared_changes > 0)
}

// A run whose probe command completed (exit and fetch): command, receipts, reference file, fetched files.
function commandChecks(r, { budget = null } = {}) {
  if (!r) return
  const results = path.join(r.agent, 'results/reproduce')
  check(`${r.name}: receipts: setup, then exactly one concurrency command; no anchors, no reproduce-freeze`, () => {
    const ops = afterProbe(r).map(receipt => receipt.operation)
    assert.ok(ops.slice(0, ops.indexOf('setup')).every(op => op === 'upload'), ops.join(','))
    assert.deepEqual(ops.filter(op => op !== 'upload'), ['setup', 'concurrency'], ops.join(','))
    assert.equal(ops.at(-1), 'concurrency', ops.join(','))
    assert.equal(ops[ops.length - 2], 'setup', `between setup and concurrency: ${ops.join(',')}`)
    assert.equal(r.commandRan, false, 'run_command.sh (anchors step) ran in unit-probe mode')
  })
  check(`${r.name}: concurrency receipt under the resolved anchors budget; log in A/results/reproduce/`, () => {
    const receipt = afterProbe(r).at(-1)
    assert.equal(receipt.operation, 'concurrency')
    assert.equal(receipt.fetched, true)
    assert.equal(receipt.timed_out, false)
    if (budget === null) fixture.assertTimeLeft([receipt], fixture.CEILING_DEFAULT, r.spawnedMs, 'concurrency')
    else assert.equal(receipt.budget_s, budget, 'budget_s is the args anchors budget')
    assert.ok(fs.statSync(path.join(results, `${receipt.name}.log`)).isFile(), 'concurrency log not in A/results/reproduce/')
  })
  check(`${r.name}: probe invoked once from the shared run directory with the stated arguments`, () => {
    assert.equal(r.probeRuns.length, 1, `probe invocations: ${r.probeRuns.length}`)
    const [run] = r.probeRuns
    const receipt = afterProbe(r).at(-1)
    assert.equal(run.cwd, fs.realpathSync(r.runDir()))
    assert.deepEqual(run.argv, ['-I', 'profiler/concurrency_probe.py', '--units', 'harness/run_units.sh', 'harness/units.json',
      'out/concurrency', String(receipt.budget_s), 'profiler/units_reference.json'])
  })
  check(`${r.name}: earlier out/concurrency/ and concurrency-work/ removed before the probe ran`, () => {
    const [run] = r.probeRuns
    assert.equal(run.staleOut, false, 'out/concurrency/stale.txt present when the probe started')
    assert.equal(run.staleWork, false, 'concurrency-work/stale-dir present when the probe started')
    assert.equal(fs.existsSync(path.join(results, 'out/concurrency/stale.txt')), false, 'stale file fetched')
  })
  check(`${r.name}: remote profiler/concurrency_probe.py equals m5/concurrency_probe.py when the probe ran`, () => {
    const [run] = r.probeRuns
    assert.ok(run.probe, 'no remote probe script')
    assert.ok(run.probe.equals(fs.readFileSync(path.join(ROOT, 'm5/concurrency_probe.py'))), 'remote probe script differs')
  })
  check(`${r.name}: units_reference.json exact shape, sample output paths, SHA-256 of the reference files`, () => {
    const value = read(path.join(results, 'units_reference.json'))
    assert.deepEqual(Object.keys(value), ['sha256'])
    const want = {}
    for (const i of r.sample) for (const rel of r.units[i].outputs) want[rel] = sha(fs.readFileSync(path.join(r.reference, rel)))
    assert.deepEqual(Object.keys(value.sha256).sort(), Object.keys(want).sort(), 'keys must be exactly the sample output paths')
    for (const [rel, digest] of Object.entries(want)) assert.equal(value.sha256[rel], digest, rel)
    for (const digest of Object.values(value.sha256)) assert.match(digest, /^[0-9a-f]{64}$/)
  })
  check(`${r.name}: the same bytes reach remote profiler/units_reference.json`, () => {
    const [run] = r.probeRuns
    assert.ok(run.reference, 'no remote reference file')
    assert.ok(run.reference.equals(fs.readFileSync(path.join(results, 'units_reference.json'))), 'remote reference bytes differ')
  })
  check(`${r.name}: fetched files under A/results/reproduce/out/concurrency/ equal remote out/concurrency/`, () => {
    const local = contents(path.join(results, 'out/concurrency'))
    assert.deepEqual(local, contents(path.join(r.runDir(), 'out/concurrency')))
    assert.ok(Object.keys(local).some(file => file.startsWith('logs/')) || r.spec.expectNoLogs, `no probe logs fetched: ${Object.keys(local)}`)
  })
  check(`${r.name}: no agent repair or harness call`, () => {
    assert.deepEqual(r.calls.filter(call => /harness|repair/.test(call.label)).map(call => call.label), [])
  })
}

// Valid file: PASS and the four facts from the file.
function validChecks(r, outcome, extra = {}) {
  if (!r) return
  statusChecks(r, 'PASS')
  commandChecks(r, extra)
  const file = path.join(r.agent, 'results/reproduce/out/concurrency/concurrency.json')
  check(`${r.name}: fetched concurrency.json has outcome ${outcome} (fixture sanity)`, () => {
    const value = read(file)
    assert.equal(value.mode, 'units')
    assert.equal(value.outcome, outcome)
    if (extra.shared !== undefined) assert.equal(expectedShared(value), extra.shared, 'fixture shared_changes')
    if (extra.factors) assert.deepEqual(extra.factors(value.batches.map(batch => batch.factor)), true, `factors ${JSON.stringify(value.batches)}`)
  })
  check(`${r.name}: facts units_outcome=${outcome}, batch factors and units_shared_writes from the file`, () => {
    const value = read(file)
    const facts = r.stage('reproduce').facts
    assert.equal(facts.units_outcome, outcome)
    assert.equal(facts.units_factor_2, value.batches[0].factor)
    assert.equal(facts.units_factor_4, value.batches[1].factor)
    assert.equal(facts.units_shared_writes, expectedShared(value))
    if (extra.shared !== undefined) assert.equal(facts.units_shared_writes, extra.shared)
    assert.equal(facts.stock_verified, true)
    assert.equal(facts.units_match ?? null, null, 'units_match outside units-check mode')
    assert.equal(facts.units_full_match ?? null, null, 'units_full_match outside units-check mode')
  })
}

// Diagnostics for a failed check (no assertion): the concurrency receipt, probe calls, remote state.
function diagnose(r) {
  try {
    const receipt = r.receipts.filter(row => row.operation === 'concurrency').at(-1)
    const run = r.runDir()
    const tail = file => fs.existsSync(file) ? fs.readFileSync(file, 'utf8').slice(-600) : '<absent>'
    return JSON.stringify({ receipt, probeRuns: r.probeRuns.length, remoteOut: Object.keys(contents(path.join(run, 'out/concurrency'))),
      remoteRunDir: fs.readdirSync(run), log: receipt && tail(path.join(run, `${receipt.name}.log`)),
      localLog: receipt && tail(path.join(r.agent, 'results/reproduce', `${receipt.name}.log`)),
      stderr: tail(path.join(r.root, 'stderr.log')).slice(-300), boxCalls: tail(path.join(r.root, 'box-calls.log')).slice(-900) })
  } catch (error) { return `diagnose failed: ${error.message}` }
}

// Invalid file: parse, four facts null.
function invalidChecks(r) {
  if (!r) return
  check(`${r.name}: diagnostics when the probe command did not fetch`, () => {
    const receipt = r.receipts.filter(row => row.operation === 'concurrency').at(-1)
    if (!receipt || receipt.fetched !== true) console.log(`FAIL-DIAGNOSTIC (not counted) ${r.name}: ${diagnose(r)}`)
  })
  statusChecks(r, 'FAIL', 'parse')
  nullFacts(r)
  check(`${r.name}: one concurrency command after setup, no retry, no anchors, no repair`, () => {
    const ops = afterProbe(r).map(receipt => receipt.operation)
    assert.deepEqual(ops.filter(op => op !== 'upload'), ['setup', 'concurrency'], ops.join(','))
    assert.equal(ops.at(-1), 'concurrency')
    assert.equal(r.probeRuns.length, 1)
    assert.equal(r.commandRan, false, 'anchors step ran')
    assert.ok(!r.calls.some(call => /harness|repair/.test(call.label)), 'repair call')
    assert.equal(afterProbe(r).at(-1).fetched, true)
  })
}

async function inParallel(jobs, width = 4) {
  const results = new Array(jobs.length)
  let next = 0
  await Promise.all(Array.from({ length: width }, async () => {
    while (next < jobs.length) { const i = next++; results[i] = await jobs[i]() }
  }))
  return results
}

async function main() {
  try {
    for (const directory of ['m5', 'idea', 'measure']) fs.cpSync(path.join(ROOT, directory), path.join(pipeline, directory), {
      recursive: true, filter: source => !['experiments', 'raids_used.jsonl'].includes(path.basename(source)),
    })
    check('fixture: test sample rule on UNITS_8', () => assert.deepEqual(sampleOf(UNITS_8), [7, 2, 6, 0]))

    // 1a. Invalid args.units_probe, or both modes: parse before any box command.
    const badArgs = [
      ['args-string', { unitsProbe: () => 'units' }], ['args-array', { unitsProbe: ({ reference }) => [reference] }],
      ['args-number', { unitsProbe: () => 7 }], ['args-null', { unitsProbe: () => null }],
      ['args-extra-key', { unitsProbe: ({ reference }) => ({ reference, extra: true }) }],
      ['args-empty-reference', { unitsProbe: () => ({ reference: '' }) }],
      ['args-missing-reference', { unitsProbe: () => ({}) }],
      ['args-reference-not-string', { unitsProbe: () => ({ reference: 7 }) }],
      ['args-missing-directory', { unitsProbe: ({ root }) => ({ reference: path.join(root, 'no such directory') }) }],
      ['args-reference-is-file', { unitsProbe: ({ root }) => ({ reference: path.join(root, 'previous run', 'A', 'harness', 'units.json') }) }],
      ['args-both-modes', { unitsProbe: 'ref', unitsCheck: 'ref' }],
    ]
    for (const r of await inParallel(badArgs.map(([name, spec]) => () => execute(name, { units: valid(UNITS_8), ...spec }))))
      earlyParseChecks(r, [])

    // 1b. Unit files missing or invalid, or a sample output missing under the reference: parse before
    // the harness upload.
    const base = makeUnits([3, 1, 4, 1.5, 9])
    const tweak = (i, change) => valid(base.map((unit, k) => k === i ? change({ ...unit }) : unit))
    const badFiles = [
      ['files-missing-run-units', { units: valid(base), runUnits: false }],
      ['files-missing-units-json', { units: null }],
      ['files-three-units', { units: valid(base.slice(0, 3)) }],
      ['files-not-json', { units: '{"units": [' }],
      ['files-top-extra-key', { units: JSON.stringify({ units: base, version: 1 }) }],
      ['files-unit-extra-key', { units: JSON.stringify(tweak(2, unit => ({ ...unit, note: 'x' }))) }],
      ['files-duplicate-id', { units: JSON.stringify(tweak(3, unit => ({ ...unit, id: base[0].id }))) }],
      ['files-output-dotdot', { units: JSON.stringify(tweak(0, unit => ({ ...unit, outputs: ['a/../x'] }))) }],
      ['files-cost-zero', { units: JSON.stringify(tweak(4, unit => ({ ...unit, cost_s: 0 }))) }],
      ['reference-sample-output-missing', { units: valid(UNITS_8), refMissing: ['2:0'] }],
      ['reference-sample-nested-output-missing', { units: valid(UNITS_8), refMissing: ['0:1'] }],
      ['reference-sample-output-directory', { units: valid(UNITS_8), refDirectory: ['3:0'] }],
    ]
    for (const r of await inParallel(badFiles.map(([name, spec]) => () => execute(name, { unitsProbe: 'ref', ...spec }))))
      earlyParseChecks(r, ['upload', 'probe'])
    check('fixture: sample position 0 has a nested second output', () => assert.equal(UNITS_8[sampleOf(UNITS_8)[0]].outputs.length, 2))

    // 2-4. Valid files from the real probe, one per outcome.
    const fast = { units: valid(UNITS_8), unitsProbe: 'ref' }
    const validCases = [
      ['measured', 'measured', { ...fast, refOmitNonSample: true }, { factors: ([f2, f4]) => f2 > 0 && f4 > 0 }],
      ['measured-relative-reference', 'measured', { ...fast, unitsProbe: 'ref-relative' }, {}],
      ['measured-shared-writes', 'measured', { ...fast, sharedWrites: true, anchorsBudget: 3000 }, { shared: true, budget: 3000 }],
      // Sample cost sum 30+12.5+18+9 > 0.9 * 50: every arm skipped by the budget; no arm ran.
      ['skipped', 'skipped', { ...fast, anchorsBudget: 50, expectNoLogs: true },{ shared: null, budget: 50, factors: f => f.every(x => x === null) }],
      ['failed', 'failed', { ...fast, fail: ['a-1'] }, { factors: f => f.every(x => x === null) }],
      ['failed-later', 'failed', { ...fast, fail: ['c2-1-2'] }, { factors: f => f.every(x => x === null) }],
      ['baseline-mismatch', 'baseline_mismatch', { ...fast, corrupt: ['a-1'] }, { factors: f => f.every(x => x === null) }],
      ['outputs-mismatch', 'outputs_mismatch', { ...fast, corrupt: ['b-1-2'] }, { factors: f => f.every(x => x === null) }],
      // The remote manifest becomes unreadable after the upload (setup overwrites it on the box).
      ['invalid-units', 'invalid_units', { ...fast, remoteUnits: '{"units": [', expectNoLogs: true },{ shared: null, factors: f => f.every(x => x === null) }],
      // Valid crafted variants of a genuine measured file.
      ['valid-late-skip', 'measured', { ...fast, mutation: 'valid-late-skip' }, { shared: true, factors: ([f2, f4]) => f2 > 0 && f4 === null }],
      ['valid-shared-zero', 'measured', { ...fast, mutation: 'valid-shared-zero' }, { shared: false }],
      ['valid-shared-one-arm', 'measured', { ...fast, mutation: 'valid-shared-one-arm' }, { shared: true }],
    ]
    const validRuns = await inParallel(validCases.map(([name, , spec]) => () => execute(name, spec)))
    validCases.forEach(([, outcome, , extra], i) => validChecks(validRuns[i], outcome, extra))
    check('fixture: every unit-mode outcome is covered by a valid case', () =>
      assert.deepEqual([...new Set(validCases.map(entry => entry[1]))].sort(), [...OUTCOMES].sort()))
    const measured = validRuns[0]
    if (measured) check('measured: run_units.sh ran in concurrency-work/ with the sample ids (fixture sanity)', () => {
      const a1 = measured.unitsCalls.find(call => call.name === 'a-1')
      assert.ok(a1, `no a-1 invocation: ${measured.unitsCalls.map(call => call.name)}`)
      assert.deepEqual(a1.ids, measured.sample.map(i => measured.units[i].id))
      assert.ok(!measured.unitsCalls.some(call => call.name === 'units-check'), 'units-check ran in unit-probe mode')
    })

    // 5. Invalid files: parse, the four facts null.
    const invalidCases = [
      ['missing-file'], ['nonzero-exit', 2], ['not-object'], ['not-json'], ['missing-key'], ['renamed-key'], ['extra-top-key'],
      ['extra-arm-key'], ['missing-arm-key'], ['extra-batch-key'], ['extra-invocation-key'], ['extra-sample-key'], ['mode-command'],
      ['outcome-unknown'], ['mps-true'], ['command-mode-shape'], ['batch-factor-wrong'], ['batch4-factor-wrong'], ['factor-not-largest'],
      ['factor-above-largest'], ['factor-null-when-measured'], ['batch-factor-null-when-measured'],
      ['factor-when-not-measured', null, { corrupt: ['b-1-2'] }], ['top-factor-when-not-measured', null, { corrupt: ['b-1-2'] }],
      ['nan-number'], ['infinite-number'], ['infinite-factor'], ['negative-number'], ['negative-shared-changes'],
      ['negative-invocation-number'], ['string-number'], ['arm-order'], ['arm-order-reversed'], ['arm-count-7'], ['arm-count-9'],
      ['arm-label-wrong'], ['batch-order'], ['batch-count-1'],
    ]
    const invalidRuns = await inParallel(invalidCases.map(([mutation, rc, extra]) => () =>
      execute(`invalid-${mutation}`, { ...fast, mutation, mutationRc: rc ?? null, ...(extra ?? {}) })))
    invalidCases.forEach(([mutation, , extra], i) => {
      const r = invalidRuns[i]
      invalidChecks(r)
      if (!r) return
      check(`${r.name}: genuine probe file before the mutation was valid (fixture sanity)`, () => {
        assert.ok(r.genuine && r.genuine.mode === 'units', 'no genuine unit-mode file')
        assert.equal(r.genuine.outcome, extra?.corrupt ? 'outputs_mismatch' : 'measured')
        if (extra?.corrupt) {
          assert.ok(r.genuine.batches.every(batch => batch.all_ok && batch.factor === null), 'c arms must all count')
          assert.notEqual(r.genuine.serial_wall_s, null)
        } else assert.ok(r.genuine.batches.every(batch => batch.factor > 0), 'measured file without both factors')
      })
      if (mutation === 'nonzero-exit') check(`${r.name}: receipt rc 2 although the file is valid`, () => {
        assert.equal(afterProbe(r).at(-1).rc, 2)
        assert.equal(read(path.join(r.agent, 'results/reproduce/out/concurrency/concurrency.json')).outcome, 'measured')
      })
    })

    // 6. Timeout and failed fetch of the probe command: no identical retry, no repair.
    const failureCases = [
      // Sample cost sum 0.9 s <= 0.9 * 3 s, so a-1 starts; it sleeps 8 s, beyond the 3 s budget.
      ['probe-timeout', { units: valid(makeUnits([0.1, 0.2, 0.3, 0.4, 0.5])), unitsProbe: 'ref', anchorsBudget: 3, sleepS: 8 }, 'timeout'],
      ['probe-fetch-failed', { ...fast, fetchFailProbe: true }, 'infra'],
    ]
    const failureRuns = await inParallel(failureCases.map(([name, spec]) => () => execute(name, spec)))
    failureCases.forEach(([name, , errorClass], i) => {
      const r = failureRuns[i]
      statusChecks(r, 'FAIL', errorClass)
      nullFacts(r)
      if (!r) return
      check(`${name}: one concurrency command, no identical retry, no anchors, no repair`, () => {
        const ops = afterProbe(r).map(receipt => receipt.operation)
        assert.deepEqual(ops.filter(op => op !== 'upload'), ['setup', 'concurrency'], ops.join(','))
        assert.equal(ops.at(-1), 'concurrency', 'box command after the failed probe')
        assert.equal(r.probeRuns.length, 1, 'probe invoked again')
        assert.equal(r.commandRan, false, 'anchors step ran')
        assert.ok(!r.calls.some(call => /harness|repair/.test(call.label)), 'agent call after a probe failure')
        const receipt = afterProbe(r).at(-1)
        if (errorClass === 'timeout') {
          assert.equal(receipt.timed_out, true)
          assert.equal(receipt.budget_s, 3, 'probe must use the resolved anchors budget')
          const facts = r.stage('reproduce').facts
          assert.deepEqual([facts.timed_out, facts.budget_s], [true, 3])
          assert.equal(r.unitsCalls.filter(call => call.name === 'a-1').length, 1, 'a-1 started once')
        } else assert.deepEqual([receipt.rc, receipt.fetched], [0, false])
      })
    })

    // 3 (gate). Setup failing: no concurrency command.
    const setupFails = await execute('setup-fails', { ...fast, setupRc: 1 })
    if (setupFails) {
      statusChecks(setupFails, 'FAIL', 'install')
      nullFacts(setupFails)
      check('setup-fails: the probe never runs when setup fails', () => {
        assert.ok(!setupFails.receipts.some(receipt => receipt.operation === 'concurrency'), 'concurrency receipt')
        assert.deepEqual(setupFails.probeRuns, [])
      })
    }

    // 7. Without args.units_probe: unchanged; units-check mode unchanged.
    const [plain, unitsCheck] = await inParallel([
      () => execute('no-units-probe', { units: valid(UNITS_8) }),
      () => execute('units-check-mode', { units: valid(UNITS_8), unitsCheck: 'ref' }),
    ])
    if (plain) {
      check('no-units-probe: every stage PASS; anchors run and freeze; no probe', () => {
        assert.deepEqual(plain.records.filter(row => STAGES.includes(row.stage)).map(row => [row.stage, row.status]), STAGES.map(label => [label, 'PASS']))
        const ops = afterProbe(plain).map(receipt => receipt.operation)
        assert.deepEqual(ops.filter(op => op !== 'upload'), ['setup', 'anchors', 'reproduce-freeze'], ops.join(','))
        assert.deepEqual(plain.probeRuns, [], 'probe ran without args.units_probe')
        assert.deepEqual(plain.unitsCalls, [], 'run_units.sh ran without args.units_probe')
        assert.equal(plain.commandRan, true)
        assert.equal(fs.existsSync(path.join(plain.agent, 'results/reproduce/units_reference.json')), false)
        assert.equal(fs.existsSync(path.join(plain.runDir(), 'concurrency-work/stale-dir')), true, 'concurrency-work/ touched without args.units_probe')
      })
      check('no-units-probe: reproduce facts as before, units-check and unit-probe facts null', () => {
        const { tokens_known, ...facts } = plain.stage('reproduce').facts
        assert.equal(typeof tokens_known === 'boolean' || tokens_known === null, true)
        // U54: the four card facts are null outside card mode (SCHEMAS.md "Card calibration (U54)").
        assert.deepEqual(facts, { anchors_passed: 2, anchors_total: 2, stock_verified: true, tuned_control_valid: null,
          gpu_busy_known: false, units_match: null, units_full_match: null,
          units_outcome: null, units_factor_2: null, units_factor_4: null, units_shared_writes: null,
          card_inputs: null, card_measured: null, card_holds: null, card_refuted: null })
        assert.equal(plain.stage('reproduce').run_valid, true)
      })
    }
    if (unitsCheck) {
      statusChecks(unitsCheck, 'PASS', null, 'units-check')
      nullFacts(unitsCheck, 'units-check mode: the four unit-probe facts null')
      check('units-check-mode: units-check command as in U51, no probe, units_match true', () => {
        const ops = afterProbe(unitsCheck).map(receipt => receipt.operation)
        assert.deepEqual(ops.filter(op => op !== 'upload'), ['setup', 'units-check'], ops.join(','))
        assert.deepEqual(unitsCheck.probeRuns, [])
        assert.deepEqual(unitsCheck.unitsCalls.map(call => call.name), ['units-check'])
        assert.equal(unitsCheck.stage('reproduce').facts.units_match, true)
        assert.equal(fs.existsSync(path.join(unitsCheck.agent, 'results/reproduce/units_check.json')), true)
        assert.equal(fs.existsSync(path.join(unitsCheck.agent, 'results/reproduce/units_reference.json')), false)
      })
    }
  } catch (error) { failures++; console.log(`FAIL test harness: ${error.stack}`) }
  finally {
    // Optional second argument `keep`: leave the scratch directory for debugging (printed).
    if (process.argv[3] === 'keep') console.log(`scratch kept: ${scratch}`)
    else fs.rmSync(scratch, { recursive: true, force: true })
  }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : 'all checks passed')
  process.exitCode = failures ? 1 : 0
}
main()
