#!/usr/bin/env node
'use strict'

// Black-box contract tests for U51, the unit equivalence check (m5/SCHEMAS.md "Unit equivalence check
// (U51)", "A/harness/" bullet "Optional unit files (U50)", the Concurrency probe "Sample:" rule,
// "A/results/reproduce/" and "C/receipts/"). Never inspect pipeline.js, signatures.py or git history.
// Usage: node tools/test_m5_units_check.js
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const assert = require('node:assert/strict')
const { spawn } = require('node:child_process')
const fixture = require('./test_m5_reproduce.js')
const ROOT = path.resolve(__dirname, '..')
const STAGES = ['intake', 'reproduce', 'profile', 'seal', 'propose', 'implement', 'evaluate', 'takeaways']
const PROBE = 'units-check-probe-50713'
// SCHEMAS.md U51 step 2: the work directory links every top-level entry of the shared run directory except these.
const EXCLUDED = ['out', 'profiler', 'concurrency-work', 'evaluation-work', 'units-check']
const ANCHORS = [{ id: 'first', published_value: 100, tolerance: 1, quantity: 'fixture', source: 'fixture' },
  { id: 'second', published_value: 0, tolerance: 0, quantity: 'fixture', source: 'fixture' }]
const PASSING = { first: 100, second: 0 }
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const rows = file => fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : []
function json(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, JSON.stringify(value) + '\n')
}
function script(file, body) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, '#!/usr/bin/env bash\nset -eu\n' + body + '\n', { mode: 0o700 })
}

// Fake agents: intake comes from the reproduce fixture; any repair call is recorded and declined (null),
// so a failed anchors run ends its step as recorded. No harness call happens under args.harness_from.
module.exports = {
  async run(options) {
    if (['harness-repair', 'anchors-repair'].includes(options.title)) {
      fs.appendFileSync(process.env.M5_REPRODUCE_CALLS, JSON.stringify({ label: options.title, name: options.name, ms: Date.now() }) + '\n')
      return null
    }
    return fixture.run(options)
  },
  exportSession: fixture.exportSession,
}
if (require.main !== module) return

const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_units_check_'))
const pipeline = path.join(scratch, 'pipeline')
let checks = 0, failures = 0
function check(label, test) {
  // Every label starts with its case name; a case filter (first argument) skips the other cases.
  if (ONLY && !ONLY.test(label)) return
  checks++
  try { test(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${error.message}`) }
}
// Relative path -> base64 contents for every regular file under a directory.
function contents(directory) {
  const result = {}
  const visit = (parent, prefix) => {
    for (const entry of fs.readdirSync(parent, { withFileTypes: true })) {
      const file = path.join(parent, entry.name)
      if (entry.isDirectory()) visit(file, prefix + entry.name + '/')
      else if (entry.isFile()) result[prefix + entry.name] = fs.readFileSync(file).toString('base64')
    }
  }
  visit(directory, '')
  return result
}

// ---- Unit manifests and output bytes ------------------------------------------------------------
// Distinctive ids and output paths, so units_check.json can be searched for them. Unit i has one
// output, or two (one nested) when i is odd.
const unitId = i => `zq${i}.unit:${i}+k=v`
const unitOutputs = i => i % 2 ? [`res-${i}/zq${i}.out.bin`, `res-${i}/nested/zq${i}.log`] : [`res-${i}/zq${i}.out.bin`]
const makeUnits = (costs, extra = {}) => costs.map((cost_s, i) => ({ id: extra.ids?.[i] ?? unitId(i), outputs: unitOutputs(i), cost_s }))
// SCHEMAS.md Concurrency probe "Sample:": sorted by cost_s ascending, ties by manifest order; four
// consecutive sorted units from position floor((N - 4) / 2), kept in that order.
function sampleOf(units) {
  const sorted = units.map((unit, index) => ({ index, cost: unit.cost_s })).sort((a, b) => a.cost - b.cost || a.index - b.index)
  const start = Math.floor((units.length - 4) / 2)
  return sorted.slice(start, start + 4).map(row => row.index)
}
const refBytes = (i, j) => Buffer.concat([Buffer.from(`reference unit ${i} output ${j}\n`), Buffer.from([0, 255, i & 0xff, j, 10, 13, 0])])
function flip(bytes) { const copy = Buffer.from(bytes); copy[copy.length >> 1] ^= 0x01; return copy }
const b64 = bytes => bytes === null ? null : bytes.toString('base64')
const sameBytes = (a, b) => a !== null && b !== null && a.equals(b)

// ---- One workflow run -----------------------------------------------------------------------------
// spec: { units (manifest object or raw string or null), runUnits (false = absent), unitsCheck (args value,
// 'ref' = absolute reference path, 'ref-relative' = relative to the pipeline cwd, undefined = absent),
// rc, sleepS, mutate: { subset|full|reference: { '<samplePos>:<outputIndex>': kind } }, measured,
// anchorsRc, anchorsBudget, fetchFailUnits, clobber }
// Optional first argument: a regular expression selecting case names (for debugging one case).
const ONLY = process.argv[2] ? new RegExp(process.argv[2]) : null
async function execute(name, spec) {
  if (ONLY && !ONLY.test(name)) return null
  const root = path.join(scratch, name)
  const agent = path.join(root, 'agent')
  const source = path.join(root, 'previous run', 'A', 'harness')
  const reference = path.join(root, 'previous run', 'A', 'results', 'reproduce', 'out')
  const box = path.join(root, 'box')
  const configFile = path.join(root, 'units-config.json')
  const unitsCalls = path.join(root, 'units-calls.jsonl')
  const helper = path.join(root, 'fake-units.js')
  fs.mkdirSync(box, { recursive: true })
  fs.mkdirSync(path.join(root, 'home'), { recursive: true })

  // Content maps: reference R, subset S (what run_units.sh writes), full F (what run_command.sh writes).
  const units = spec.units && typeof spec.units === 'object' ? spec.units.units : null
  const sample = units ? sampleOf(units) : []
  const maps = { reference: {}, subset: {}, full: {} }
  for (const [i, unit] of (units ?? []).entries()) {
    for (const kind of Object.keys(maps)) maps[kind][unit.id] = {}
    unit.outputs.forEach((rel, j) => {
      const key = `${sample.indexOf(i)}:${j}`
      const R = refBytes(i, j)
      const mutation = kind => sample.includes(i) ? spec.mutate?.[kind]?.[key] : undefined
      const pick = (table, kind) => Object.hasOwn(table, mutation(kind) ?? '') ? table[mutation(kind)] : R
      const S = pick({ flip: flip(R), missing: null }, 'subset')
      const F = pick({ flip: flip(R), missing: null, subset: S, other: Buffer.from(`full-only bytes ${i} ${j}\n`) }, 'full')
      const ref = mutation('reference') === 'missing' ? null : R
      maps.reference[unit.id][rel] = ref
      maps.subset[unit.id][rel] = S
      maps.full[unit.id][rel] = F
    })
  }
  for (const files of Object.values(maps.reference)) for (const [rel, bytes] of Object.entries(files)) if (bytes !== null) {
    fs.mkdirSync(path.dirname(path.join(reference, rel)), { recursive: true })
    fs.writeFileSync(path.join(reference, rel), bytes)
  }
  fs.mkdirSync(reference, { recursive: true })
  // A reference-only file outside every unit's outputs is never compared.
  fs.writeFileSync(path.join(reference, 'anchors_measured.json'), '{"first":-1}\n')
  const encode = map => Object.fromEntries(Object.entries(map).map(([id, files]) => [id, Object.fromEntries(Object.entries(files).map(([rel, bytes]) => [rel, b64(bytes)]))]))
  const samplePaths = sample.flatMap(i => units[i].outputs)
  json(configFile, { subset: encode(maps.subset), full: encode(maps.full), rc: spec.rc ?? 0, sleep_s: spec.sleepS ?? 1, clobber: Boolean(spec.clobber), samplePaths })

  // The fake unit runner, run by harness/run_units.sh (subset) and harness/run_command.sh (full).
  fs.writeFileSync(helper, `'use strict'
const fs = require('node:fs'), path = require('node:path')
const cfg = JSON.parse(fs.readFileSync(${JSON.stringify(configFile)}, 'utf8'))
const [mode, ...ids] = process.argv.slice(2)
const write = (rel, data) => { const file = path.join('out', rel); fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, Buffer.from(data, 'base64')) }
const record = { mode, ids, cwd: fs.realpathSync(process.cwd()), ms: Date.now() }
if (mode === 'subset') {
  record.parent = path.dirname(record.cwd)
  record.entries = fs.readdirSync('.').sort().map(name => {
    const stat = fs.lstatSync(name)
    let real = null
    try { real = stat.isSymbolicLink() ? fs.realpathSync(name) : null } catch { real = 'dangling' }
    return { name, symlink: stat.isSymbolicLink(), directory: stat.isDirectory(), real }
  })
  record.parentEntries = fs.readdirSync(record.parent).sort()
  record.parentReal = Object.fromEntries(record.parentEntries.map(name => [name, fs.realpathSync(path.join(record.parent, name))]))
  record.out = fs.existsSync('out') ? fs.readdirSync('out') : null
  record.written = {}
  for (const id of ids) for (const [rel, data] of Object.entries(cfg.subset[id] ?? {})) if (data !== null) { write(rel, data); record.written[rel] = data }
  const extra = Buffer.from('not a unit output\\n').toString('base64')
  write('extra-unlisted.txt', extra)
  record.written['extra-unlisted.txt'] = extra
  process.stdout.write('UNITS_STDOUT_MARK\\n')
  process.stderr.write('UNITS_STDERR_MARK\\n')
  fs.appendFileSync(${JSON.stringify(unitsCalls)}, JSON.stringify(record) + '\\n')
  const until = Date.now() + cfg.sleep_s * 1000
  const cell = new Int32Array(new SharedArrayBuffer(4))
  while (Date.now() < until) Atomics.wait(cell, 0, 0, 20)
  process.exit(cfg.rc)
}
for (const files of Object.values(cfg.full)) for (const [rel, data] of Object.entries(files)) if (data !== null) write(rel, data)
if (cfg.clobber) {
  // The full run replaces remote out/units-check/, so its fetch replaces the local out/ copy of it too.
  fs.rmSync('out/units-check', { recursive: true, force: true })
  for (const rel of cfg.samplePaths) write('units-check/files/' + rel, Buffer.from('clobbered by the full run\\n').toString('base64'))
  fs.writeFileSync('out/units-check/wall.json', '{"wall_s": 12345}\\n')
}
fs.appendFileSync(${JSON.stringify(unitsCalls)}, JSON.stringify(record) + '\\n')
`)
  const node = JSON.stringify(process.execPath), helperArg = JSON.stringify(helper)
  // Harness of a "previous run", copied by args.harness_from (SCHEMAS.md "A/harness/").
  script(path.join(source, 'setup.sh'), `mkdir -p out baseline-published data profiler concurrency-work evaluation-work units-check/stale-dir out/units-check/files
printf 'published\\n' > baseline-published/pin
printf 'input\\n' > data/input
printf 'stale\\n' > units-check/stale-work.txt
printf 'stale\\n' > out/units-check/files/stale-out.txt
printf 'stale\\n' > out/units-check/stale-run.log
printf 'hidden\\n' > .hidden-entry
printf 'note\\n' > top-file.txt`)
  script(path.join(source, 'run_command.sh'), `test -f baseline-published/pin\ntest -f data/input\nmkdir -p out\n${node} ${helperArg} full\nprintf 'command ran\\n' >> out/command-calls.log`)
  script(path.join(source, 'run_anchors.sh'), `bash harness/run_command.sh\nprintf '%s\\n' '${JSON.stringify(spec.measured ?? PASSING)}' > out/anchors_measured.json\nexit ${spec.anchorsRc ?? 0}`)
  if (spec.runUnits !== false) script(path.join(source, 'run_units.sh'), `exec ${node} ${helperArg} subset "$@"`)
  if (spec.units !== null && spec.units !== undefined)
    fs.writeFileSync(path.join(source, 'units.json'), typeof spec.units === 'string' ? spec.units : JSON.stringify(spec.units, null, 2) + '\n')

  const args = { run_root: root, tag: name, harness_from: source,
    stub: { profile: 'PASS', seal: 'PASS', propose: 'PASS', implement: 'PASS', evaluate: 'PASS' } }
  if (spec.unitsCheck === 'ref') args.units_check = { reference }
  else if (spec.unitsCheck === 'ref-relative') args.units_check = { reference: path.relative(pipeline, reference) }
  else if (typeof spec.unitsCheck === 'function') args.units_check = spec.unitsCheck({ reference, root })
  else if (spec.unitsCheck !== undefined) args.units_check = spec.unitsCheck
  if (spec.anchorsBudget) args.stage_budgets_s = { anchors: spec.anchorsBudget }
  json(path.join(root, 'control/args.json'), args)

  const callsFile = path.join(root, 'calls.jsonl')
  const replaceProbe = path.join(root, 'replace-probe.js')
  const originalProbe = fs.readFileSync(path.join(ROOT, 'm5/box_probe.sh'), 'utf8')
  const fakeProbe = '#!/usr/bin/env bash\nset -eu\nmkdir -p out\nprintf \'{"label":"probe"}\\n\' >> "$M5_REPRODUCE_CALLS"\nprintf \'{"kernel":"' + PROBE + '","nvcc":[],"cmake":null}\\n\' > out/probe.json\n'
  fs.writeFileSync(replaceProbe, `
const fs = require('node:fs'), path = require('node:path')
function visit(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const file = path.join(directory, entry.name)
    if (entry.isDirectory()) visit(file)
    else if (entry.isFile() && entry.name.endsWith('.sh') && fs.readFileSync(file, 'utf8') === ${JSON.stringify(originalProbe)}) {
      fs.appendFileSync(process.env.M5_REPRODUCE_CALLS, '{"label":"probe-upload"}\\n')
      fs.writeFileSync(file, ${JSON.stringify(fakeProbe)})
    }
  }
}
visit(process.env.BOX_ROOT)
`)
  script(path.join(root, 'box-bin/nvidia-smi'), 'exit 1')
  // Before the first box command after the units-check receipt, keep the remote out/units-check/ as
  // the units-check command left it (a later full run may replace it).
  const unitsSnapshot = `latest=
for receipt in "$BOX_ROOT"/../control/receipts/*.json; do [[ ! -e $receipt ]] || latest=$receipt; done
if [[ $latest == *-units-check.json && ! -e $BOX_ROOT/../units-check-remote ]]; then
  for remote in "$BOX_ROOT"/m5-*; do
    [[ ! -d $remote/out/units-check ]] || cp -a "$remote/out/units-check" "$BOX_ROOT/../units-check-remote"
  done
fi
`
  script(path.join(root, 'bin/box'), 'command=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\nexport PATH="$BOX_ROOT/../box-bin:$PATH"\ncd -- "$BOX_ROOT"\n' + unitsSnapshot +
    'bash -c "$command"\n"$M5_TEST_NODE" "$M5_REPLACE_PROBE"\nif [[ $command == *timeout* ]]; then\n  for ((i=0; i<1000; i++)); do\n    pending=false\n    for file in "$BOX_ROOT"/m5-*/*.sh; do\n      [[ -f $file ]] || continue\n      [[ -f ${file%.sh}.rc ]] || pending=true\n    done\n    [[ $pending == true ]] || break\n    sleep 0.01\n  done\nfi\nexit 0')
  // fetchFailUnits: every fetch of the units-check log fails, so its receipt has fetched=false (infra).
  script(path.join(root, 'bin/fetch'), 'source=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\ncd -- "$BOX_ROOT"\n' +
    (spec.fetchFailUnits ? "[[ $source != *-units-check.log ]] || { echo 'simulated failed fetch' >&2; exit 1; }\n" : '') + 'exec cp -r -- "$source" "$2"')
  const fixtureConfig = { anchors: ANCHORS, measured: spec.measured ?? PASSING }
  const stderrFile = path.join(root, 'stderr.log')
  const stdout = fs.openSync(path.join(root, 'stdout.log'), 'w'), stderr = fs.openSync(stderrFile, 'w')
  let child
  const spawnedMs = Date.now()
  try {
    child = await new Promise(resolve => {
      const proc = spawn(process.execPath, [path.join(pipeline, 'idea/wf.js'), '--script', path.join(pipeline, 'm5/pipeline.js'),
        '--args', path.join(root, 'control/args.json'), '--out', path.join(agent, 'wf'), '--disable-family', 'claude'], {
        cwd: pipeline, timeout: 120000, killSignal: 'SIGKILL', stdio: ['ignore', stdout, stderr],
        env: { ...process.env, HOME: path.join(root, 'home'), M5_RAIDS_LEDGER: path.join(scratch, 'raids.jsonl'),
          WF_STUB: __filename, M5_REPRODUCE_ROOT: root, M5_REPRODUCE_CONFIG: JSON.stringify(fixtureConfig),
          M5_REPRODUCE_CALLS: callsFile, M5_TEST_NODE: process.execPath, M5_REPLACE_PROBE: replaceProbe,
          BOX_ROOT: box, BOX: path.join(root, 'bin/box'), FETCH: path.join(root, 'bin/fetch'),
          ...(spec.fetchFailUnits ? { BOXRUN_FETCH_WAIT_S: '0' } : {}) },
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
  return { name, spec, root, agent, reference, records, receipts, runDir, spawnedMs, units, sample, maps,
    calls: rows(callsFile), unitsCalls: rows(unitsCalls), stage: label => records.find(row => row.stage === label) }
}

// ---- Shared checks --------------------------------------------------------------------------------
// Stage statuses: units-check mode skips every stage after reproduce except takeaways (SCHEMAS.md U51).
function statusChecks(r, status, errorClass = null) {
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
    assert.ok(!r.calls.some(call => ['seal', 'propose', 'implement', 'evaluate'].includes(call.label)), 'scientific call in units-check mode')
  })
}
const afterProbe = r => {
  const at = r.receipts.findIndex(receipt => receipt.operation === 'probe')
  assert.ok(at >= 1, `no probe receipt: ${r.receipts.map(x => x.operation)}`)
  return r.receipts.slice(at + 1)
}
// Expected comparison results, computed from the fixture's own bytes.
function expected(r) {
  const paths = r.sample.flatMap(i => r.units[i].outputs.map(rel => [r.units[i].id, rel]))
  const S = ([id, rel]) => r.maps.subset[id][rel], R = ([id, rel]) => r.maps.reference[id][rel], F = ([id, rel]) => r.maps.full[id][rel]
  const rc = r.spec.rc ?? 0
  const filesMatched = paths.filter(p => sameBytes(S(p), R(p))).length
  const subsetMatch = rc === 0 && filesMatched === paths.length
  const fullRan = rc === 0 && !subsetMatch
  const fullOk = fullRan && (r.spec.anchorsRc ?? 0) === 0
  return { rc, filesTotal: paths.length, filesMatched, subsetMatch, fullRan,
    fullMatch: fullOk ? paths.every(p => sameBytes(F(p), R(p))) : null,
    subsetVsFull: fullOk ? paths.every(p => sameBytes(S(p), F(p))) : null }
}
const UNITS_CHECK_KEYS = ['sample', 'subset_rc', 'subset_wall_s', 'cost_sum_s', 'cost_ratio', 'files_total', 'files_matched',
  'subset_match', 'full_ran', 'full_match', 'subset_vs_full_match']
const close = (a, b) => Math.abs(a - b) <= 1e-9 * Math.max(1, Math.abs(a), Math.abs(b))

// A units-check run whose command completed: receipts, invocation, layout, logs, wall.json, copies,
// units_check.json, facts and statuses (SCHEMAS.md U51 steps 1-4 and the units_check.json bullet).
function unitsCheckChecks(r, scoring = null) {
  if (!r) return
  const want = expected(r)
  const results = path.join(r.agent, 'results/reproduce')
  const sampleIds = r.sample.map(i => r.units[i].id)
  const declined = (r.spec.anchorsRc ?? 0) !== 0
  const anchorsFail = want.fullRan && !declined && scoring && scoring.passed < scoring.total
  const status = want.fullRan && (declined || anchorsFail) ? 'FAIL' : 'PASS'
  statusChecks(r, status, status === 'FAIL' ? 'anchor' : null)
  check(`${r.name}: receipts: setup, one units-check, ${want.fullRan ? 'one anchors run' : 'no anchors run'}, no reproduce-freeze`, () => {
    const ops = afterProbe(r).map(receipt => receipt.operation)
    const units = ops.flatMap((op, i) => op === 'units-check' ? [i] : [])
    assert.equal(units.length, 1, ops.join(','))
    const lastSetup = ops.lastIndexOf('setup')
    assert.ok(lastSetup >= 1 && lastSetup < units[0], ops.join(','))
    assert.ok(ops.slice(0, ops.indexOf('setup')).every(op => op === 'upload'), ops.join(','))
    assert.deepEqual(ops.slice(lastSetup + 1, units[0]), [], `between setup and units-check: ${ops.join(',')}`)
    assert.deepEqual(ops.slice(units[0] + 1), want.fullRan ? ['anchors'] : [], `after units-check: ${ops.join(',')}`)
    assert.ok(!ops.includes('reproduce-freeze'), 'reproduce-freeze in units-check mode')
    const receipt = afterProbe(r)[units[0]]
    assert.equal(receipt.rc, want.rc, 'units-check receipt rc is the invocation exit status')
    assert.equal(receipt.fetched, true)
    assert.equal(receipt.timed_out, false)
    // "under the resolved `anchors` budget": no args override, so the time left before the run ceiling.
    fixture.assertTimeLeft([receipt], fixture.CEILING_DEFAULT, r.spawnedMs, 'units-check')
    assert.ok(fs.statSync(path.join(results, `${receipt.name}.log`)).isFile(), 'units-check log not in A/results/reproduce/')
    if (want.fullRan) assert.equal(afterProbe(r).at(-1).rc, r.spec.anchorsRc ?? 0)
  })
  check(`${r.name}: no agent repair or harness call; run_units.sh invoked once`, () => {
    // A declined call may be retried on another family (`fb` descriptor, SCHEMAS.md naming): same turn.
    assert.deepEqual(r.calls.filter(call => /harness|repair/.test(call.label) && !/(^|-)fb(-|$)/.test(call.name || '')).map(call => call.label),
      declined ? ['anchors-repair'] : [])
    assert.equal(r.unitsCalls.filter(call => call.mode === 'subset').length, 1)
    assert.equal(r.unitsCalls.filter(call => call.mode === 'full').length, want.fullRan ? 1 : 0)
  })
  const invocation = r.unitsCalls.find(call => call.mode === 'subset')
  check(`${r.name}: run_units.sh gets the four sample ids in sample order`, () => {
    assert.ok(invocation, 'run_units.sh never ran')
    assert.deepEqual(invocation.ids, sampleIds)
  })
  check(`${r.name}: fresh units-check/ work directory: symlinks to every top-level entry except ${EXCLUDED.join(', ')}, plus an empty out/`, () => {
    const run = fs.realpathSync(r.runDir())
    assert.equal(invocation.cwd, path.join(run, 'units-check'), 'run_units.sh not run in <run>/units-check')
    assert.equal(invocation.parent, run)
    const out = invocation.entries.find(entry => entry.name === 'out')
    assert.ok(out && out.directory && !out.symlink, 'out/ must be a real directory')
    assert.deepEqual(invocation.out, [], 'out/ not empty at the start of the invocation')
    const linked = invocation.entries.filter(entry => entry.name !== 'out')
    const want = invocation.parentEntries.filter(name => !EXCLUDED.includes(name))
    // The fixture's setup made these, so the exclusions and "every entry" are both exercised.
    for (const name of ['profiler', 'concurrency-work', 'evaluation-work', 'units-check', '.hidden-entry', 'top-file.txt', 'data', 'harness'])
      assert.ok(invocation.parentEntries.includes(name), `fixture run directory lacks ${name}`)
    assert.deepEqual(linked.map(entry => entry.name).sort(), want.sort(), 'work directory entries')
    for (const entry of linked) {
      assert.equal(entry.symlink, true, `${entry.name} is not a symlink`)
      assert.equal(entry.real, invocation.parentReal[entry.name], `${entry.name} links elsewhere`)
    }
  })
  // Remote out/units-check/ as the units-check command left it.
  const remoteUnits = () => {
    const saved = path.join(r.root, 'units-check-remote')
    return fs.existsSync(saved) ? saved : path.join(r.runDir(), 'out/units-check')
  }
  check(`${r.name}: remote out/units-check/ holds run.log, wall.json and a copy of the work out/ (stale files removed)`, () => {
    const remote = contents(remoteUnits())
    const files = Object.fromEntries(Object.entries(invocation.written).map(([rel, data]) => [`files/${rel}`, data]))
    assert.deepEqual(Object.keys(remote).sort(), ['run.log', 'wall.json', ...Object.keys(files)].sort())
    for (const [file, data] of Object.entries(files)) assert.equal(remote[file], data, file)
    assert.deepEqual(contents(path.join(r.runDir(), 'units-check/out')), invocation.written, 'work out/ differs from what run_units.sh wrote')
    assert.equal(fs.existsSync(path.join(r.runDir(), 'units-check/stale-work.txt')), false, 'earlier units-check/ not removed')
    const log = Buffer.from(remote['run.log'], 'base64').toString('utf8')
    assert.ok(log.includes('UNITS_STDOUT_MARK') && log.includes('UNITS_STDERR_MARK'), 'run.log lacks stdout or stderr')
  })
  let wall = null
  check(`${r.name}: wall.json is {"wall_s"} with the invocation's own wall seconds`, () => {
    const value = JSON.parse(Buffer.from(contents(remoteUnits())['wall.json'], 'base64').toString('utf8'))
    assert.deepEqual(Object.keys(value), ['wall_s'])
    assert.ok(typeof value.wall_s === 'number' && Number.isFinite(value.wall_s) && value.wall_s > 0, `wall_s ${value.wall_s}`)
    const sleep = r.spec.sleepS ?? 1
    const receipt = afterProbe(r).find(row => row.operation === 'units-check')
    assert.ok(value.wall_s >= sleep - 0.05, `wall_s ${value.wall_s} shorter than the invocation (${sleep} s)`)
    assert.ok(value.wall_s <= receipt.wall_s + 1.5, `wall_s ${value.wall_s} longer than the command (${receipt.wall_s} s)`)
    wall = value.wall_s
  })
  check(`${r.name}: fetched out/units-check/ saved to A/results/reproduce/units-check/`, () => {
    assert.deepEqual(contents(path.join(results, 'units-check')), contents(remoteUnits()))
  })
  if (r.spec.clobber) check(`${r.name}: the anchors fetch replaced A/results/reproduce/out/ (fixture sanity)`, () => {
    assert.deepEqual(read(path.join(results, 'out/units-check/wall.json')), { wall_s: 12345 })
    for (const i of r.sample) for (const rel of r.units[i].outputs) {
      const local = path.join(results, 'out', rel), bytes = r.maps.full[r.units[i].id][rel]
      if (bytes === null) assert.equal(fs.existsSync(local), false, rel)
      else assert.ok(fs.readFileSync(local).equals(bytes), `${rel}: full-run bytes not fetched`)
    }
  })
  check(`${r.name}: units_check.json exact keys and values`, () => {
    const file = path.join(results, 'units_check.json')
    const value = read(file)
    assert.deepEqual(Object.keys(value).sort(), [...UNITS_CHECK_KEYS].sort())
    assert.deepEqual(value.sample, r.sample.map(index => ({ index, cost_s: r.units[index].cost_s })))
    for (const row of value.sample) assert.deepEqual(Object.keys(row).sort(), ['cost_s', 'index'])
    assert.equal(value.subset_rc, want.rc)
    assert.ok(Number.isInteger(value.subset_rc))
    if (wall !== null) assert.equal(value.subset_wall_s, wall, 'subset_wall_s differs from wall.json')
    const sum = r.sample.reduce((total, i) => total + r.units[i].cost_s, 0)
    assert.ok(close(value.cost_sum_s, sum), `cost_sum_s ${value.cost_sum_s}, expected ${sum}`)
    assert.ok(close(value.cost_ratio, value.subset_wall_s / sum), `cost_ratio ${value.cost_ratio}, expected ${value.subset_wall_s / sum}`)
    assert.equal(value.files_total, want.filesTotal)
    assert.equal(value.files_matched, want.filesMatched)
    assert.equal(value.subset_match, want.subsetMatch)
    assert.equal(value.full_ran, want.fullRan)
    assert.equal(value.full_match, want.fullMatch)
    assert.equal(value.subset_vs_full_match, want.subsetVsFull)
    // "No unit identifier or output path appears in the file."
    const text = fs.readFileSync(file, 'utf8')
    for (const unit of r.units) for (const needle of [unit.id, ...unit.outputs]) assert.ok(!text.includes(needle), `units_check.json contains ${needle}`)
  })
  check(`${r.name}: reproduce facts units_match=${want.subsetMatch} units_full_match=${want.fullMatch}`, () => {
    const facts = r.stage('reproduce').facts
    assert.equal(facts.units_match, want.subsetMatch)
    assert.equal(facts.units_full_match, want.fullMatch)
    assert.equal(facts.stock_verified, true)
    if (!want.fullRan || declined) assert.deepEqual([facts.anchors_passed, facts.anchors_total], [null, null], 'anchor counts without scoring')
    else assert.deepEqual([facts.anchors_passed, facts.anchors_total], [scoring.passed, scoring.total])
    if (r.stage('reproduce').status === 'PASS' && !want.fullRan) assert.equal(r.stage('reproduce').run_valid ?? null, null, 'run_valid without anchor scoring')
  })
  check(`${r.name}: anchors scoring ${want.fullRan && !declined ? 'written once' : 'absent'}`, () => {
    const scored = path.join(results, 'anchors_scored.json')
    if (!want.fullRan || declined) { assert.equal(fs.existsSync(scored), false); return }
    const value = read(scored)
    assert.equal(value.anchors_passed, scoring.passed)
    assert.equal(value.anchors_total, scoring.total)
    assert.equal(r.stage('reproduce').run_valid, scoring.passed === scoring.total)
  })
}

// Runs that stop before the units-check command ran.
function earlyParseChecks(r, receiptsWanted) {
  if (!r) return
  statusChecks(r, 'FAIL', 'parse')
  check(`${r.name}: ${receiptsWanted.length ? 'probe only, no harness upload' : 'no box receipt'}`, () => {
    assert.deepEqual(r.receipts.map(receipt => receipt.operation), receiptsWanted)
    assert.deepEqual(r.unitsCalls, [], 'a unit or baseline command ran')
    assert.ok(!r.calls.some(call => /repair/.test(call.label)), 'repair call')
    assert.equal(fs.existsSync(path.join(r.agent, 'results/reproduce/units_check.json')), false)
  })
}

const UNITS_8 = makeUnits([30, 5, 12.5, 70, 2, 44, 18, 9])

async function main() {
  try {
    for (const directory of ['m5', 'idea', 'measure']) fs.cpSync(path.join(ROOT, directory), path.join(pipeline, directory), {
      recursive: true, filter: source => !['experiments', 'raids_used.jsonl'].includes(path.basename(source)),
    })
    // 1a. Invalid args.units_check: parse before any box command.
    const badArgs = [
      ['args-string', () => 'units'], ['args-array', ({ reference }) => [reference]], ['args-number', () => 7],
      ['args-extra-key', ({ reference }) => ({ reference, extra: true })], ['args-empty-reference', () => ({ reference: '' })],
      ['args-missing-reference', () => ({})], ['args-reference-not-string', () => ({ reference: 7 })],
      ['args-missing-directory', ({ root }) => ({ reference: path.join(root, 'no such directory') })],
      ['args-reference-is-file', ({ root }) => ({ reference: path.join(root, 'previous run', 'A', 'harness', 'units.json') })],
    ]
    for (const [name, unitsCheck] of badArgs) {
      const r = await execute(name, { units: UNITS_8, unitsCheck })
      earlyParseChecks(r, [])
      check(`${name}: no probe and no harness upload`, () => {
        assert.ok(!r.calls.some(call => ['probe', 'probe-upload'].includes(call.label)), 'probe ran')
      })
    }
    // 1b. Unit files missing or invalid after the harness copy: parse before the harness upload.
    const valid = units => ({ units })
    const base = makeUnits([3, 1, 4, 1.5, 9])
    const tweak = (i, change) => valid(base.map((unit, k) => k === i ? change({ ...unit }) : unit))
    const badFiles = [
      ['files-missing-run-units', { units: valid(base), runUnits: false }],
      ['files-missing-units-json', { units: null }],
      ['files-three-units', { units: valid(base.slice(0, 3)) }],
      ['files-not-json', { units: '{"units": [' }],
      ['files-top-array', { units: JSON.stringify(base) }],
      ['files-top-extra-key', { units: JSON.stringify({ units: base, version: 1 }) }],
      ['files-units-not-array', { units: JSON.stringify({ units: { a: base[0] } }) }],
      ['files-unit-extra-key', { units: JSON.stringify(tweak(2, unit => ({ ...unit, note: 'x' }))) }],
      ['files-unit-missing-cost', { units: JSON.stringify(tweak(2, ({ cost_s, ...unit }) => unit)) }],
      ['files-duplicate-id', { units: JSON.stringify(tweak(3, unit => ({ ...unit, id: base[0].id }))) }],
      ['files-id-leading-dash', { units: JSON.stringify(tweak(1, unit => ({ ...unit, id: '-lead' }))) }],
      ['files-id-space', { units: JSON.stringify(tweak(1, unit => ({ ...unit, id: 'a b' }))) }],
      ['files-id-129-chars', { units: JSON.stringify(tweak(1, unit => ({ ...unit, id: 'a'.repeat(129) }))) }],
      ['files-id-number', { units: JSON.stringify(tweak(1, unit => ({ ...unit, id: 7 }))) }],
      ['files-outputs-empty', { units: JSON.stringify(tweak(0, unit => ({ ...unit, outputs: [] }))) }],
      ['files-outputs-duplicate', { units: JSON.stringify(tweak(0, unit => ({ ...unit, outputs: ['a/x', 'a/x'] }))) }],
      ['files-output-dotdot', { units: JSON.stringify(tweak(0, unit => ({ ...unit, outputs: ['a/../x'] }))) }],
      ['files-output-dot', { units: JSON.stringify(tweak(0, unit => ({ ...unit, outputs: ['./x'] }))) }],
      ['files-output-absolute', { units: JSON.stringify(tweak(0, unit => ({ ...unit, outputs: ['/x'] }))) }],
      ['files-output-empty-component', { units: JSON.stringify(tweak(0, unit => ({ ...unit, outputs: ['a//x'] }))) }],
      ['files-output-bad-char', { units: JSON.stringify(tweak(0, unit => ({ ...unit, outputs: ['a b'] }))) }],
      ['files-cost-zero', { units: JSON.stringify(tweak(4, unit => ({ ...unit, cost_s: 0 }))) }],
      ['files-cost-negative', { units: JSON.stringify(tweak(4, unit => ({ ...unit, cost_s: -1 }))) }],
      ['files-cost-string', { units: JSON.stringify(tweak(4, unit => ({ ...unit, cost_s: '1' }))) }],
      ['files-cost-boolean', { units: JSON.stringify(tweak(4, unit => ({ ...unit, cost_s: true }))) }],
    ]
    for (const [name, spec] of badFiles) earlyParseChecks(await execute(name, { ...spec, unitsCheck: 'ref' }), ['upload', 'probe'])

    // 2-3. Match: every sample file byte-identical to the reference. Sample rule over N = 4, 5, 8, 9,
    // distinct costs and ties; manifest order differs from cost order. N=5 includes a 128-character id.
    const id128 = 'Z' + 'y.:+=-'.repeat(21) + 'x'
    const matchCases = [
      ['match-n4-distinct', makeUnits([40, 10, 30, 20]), 'ref-relative'],
      ['match-n5-ties', makeUnits([7, 3, 7, 3, 7], { ids: [undefined, undefined, id128] }), 'ref'],
      ['match-n8-distinct', UNITS_8, 'ref'],
      ['match-n8-ties-at-boundary', makeUnits([5, 9, 5, 1, 5, 9, 5, 2]), 'ref'],
      ['match-n9-ties', makeUnits([6, 6, 1, 6, 8, 2, 6, 0.5, 6.5]), 'ref'],
    ]
    check('fixture: 128-character id is valid by the U50 pattern', () => assert.match(id128, /^[A-Za-z0-9][A-Za-z0-9._:+=-]{0,127}$/))
    for (const [name, units, unitsCheck] of matchCases) {
      const r = await execute(name, { units: valid(units), unitsCheck })
      unitsCheckChecks(r)
      check(`${name}: expected sample positions ${JSON.stringify(r?.sample)} (test's own rule)`, () => assert.equal(r.sample.length, 4))
    }
    // 4. Mismatch with exit 0: one anchors run, then full_match and subset_vs_full_match.
    const mismatch = [
      // [name, mutate, extra]: positions are sample positions.
      ['mismatch-byte-full-equals-reference', { subset: { '1:0': 'flip' } }],
      ['mismatch-byte-full-equals-subset', { subset: { '1:0': 'flip' }, full: { '1:0': 'subset' } }],
      ['mismatch-subset-missing-full-equals-reference', { subset: { '2:0': 'missing' } }],
      ['mismatch-subset-missing-full-missing', { subset: { '2:0': 'missing' }, full: { '2:0': 'missing' } }],
      ['mismatch-reference-missing-full-equals-subset', { reference: { '0:0': 'missing' } }],
      ['mismatch-reference-missing-full-differs', { reference: { '0:0': 'missing' }, full: { '0:0': 'other' } }],
      ['mismatch-byte-full-differs-from-both', { subset: { '3:0': 'flip' }, full: { '3:0': 'other' } }],
      ['mismatch-anchors-fail-scoring', { subset: { '0:1': 'flip' } },{ measured: { first: 102, second: 0 } }],
      ['mismatch-anchors-exit-nonzero', { subset: { '1:0': 'flip' } }, { anchorsRc: 7 }],
    ]
    for (const [name, mutate, extra = {}] of mismatch) {
      const units = valid(makeUnits([30, 5, 12.5, 70, 2, 44, 18, 9]))
      const r = await execute(name, { units, unitsCheck: 'ref', mutate, clobber: true, ...extra })
      const measured = extra.measured ?? PASSING
      const scoring = { total: 2, passed: ANCHORS.filter(item => Math.abs(measured[item.id] - item.published_value) <= item.tolerance).length }
      unitsCheckChecks(r, scoring)
      check(`${name}: fixture produces a subset mismatch with exit 0`, () => {
        const want = expected(r)
        assert.equal(want.subsetMatch, false)
        assert.equal(want.fullRan, true)
      })
    }
    // 5. Invocation exits nonzero: files still copied, no anchors run, status PASS.
    await (async () => {
      const r = await execute('nonzero-all-files-match', { units: valid(UNITS_8), unitsCheck: 'ref', rc: 3 })
      unitsCheckChecks(r)
      check('nonzero-all-files-match: every file matched, subset_match false', () => {
        const value = read(path.join(r.agent, 'results/reproduce/units_check.json'))
        assert.equal(value.files_matched, value.files_total)
        assert.equal(value.subset_match, false)
      })
      unitsCheckChecks(await execute('nonzero-file-missing', { units: valid(UNITS_8), unitsCheck: 'ref', rc: 1, mutate: { subset: { '0:0': 'missing' } } }))
    })()
    // 6. Timeout or infrastructure failure of the units-check command: no retry, no repair.
    for (const [name, extra, errorClass] of [['units-check-timeout', { anchorsBudget: 2, sleepS: 6 }, 'timeout'], ['units-check-fetch-failed', { fetchFailUnits: true }, 'infra']]) {
      const r = await execute(name, { units: valid(UNITS_8), unitsCheck: 'ref', ...extra })
      statusChecks(r, 'FAIL', errorClass)
      check(`${name}: one units-check command, no identical retry, no anchors, no repair`, () => {
        const ops = afterProbe(r).map(receipt => receipt.operation)
        assert.deepEqual(ops.filter(op => op !== 'upload'), ['setup', 'units-check'], ops.join(','))
        assert.equal(ops.at(-1), 'units-check', 'box command after the failed units-check')
        const receipt = afterProbe(r).at(-1)
        if (errorClass === 'timeout') {
          assert.equal(receipt.timed_out, true)
          assert.equal(receipt.budget_s, 2, 'units-check must use the resolved anchors budget')
          const facts = r.stage('reproduce').facts
          assert.deepEqual([facts.timed_out, facts.budget_s], [true, 2])
        } else assert.deepEqual([receipt.rc, receipt.fetched], [0, false])
        assert.equal(r.unitsCalls.filter(call => call.mode === 'subset').length, 1, 'run_units.sh invoked again')
        assert.equal(r.unitsCalls.filter(call => call.mode === 'full').length, 0, 'full run after a failed units-check')
        assert.ok(!r.calls.some(call => /harness|repair/.test(call.label)), 'agent repair after a units-check failure')
      })
    }
    // 7. Without args.units_check: reproduce and later stages as before, even with unit files present.
    const plain = await execute('no-units-check', { units: valid(UNITS_8) })
    check('no-units-check: every stage PASS; anchors run and freeze; no units-check command', () => {
      assert.deepEqual(plain.records.filter(row => STAGES.includes(row.stage)).map(row => [row.stage, row.status]), STAGES.map(label => [label, 'PASS']))
      const ops = afterProbe(plain).map(receipt => receipt.operation)
      assert.deepEqual(ops.filter(op => op !== 'upload'), ['setup', 'anchors', 'reproduce-freeze'], ops.join(','))
      assert.deepEqual(plain.unitsCalls.map(call => call.mode), ['full'], 'run_units.sh ran without args.units_check')
      assert.equal(fs.existsSync(path.join(plain.agent, 'results/reproduce/units_check.json')), false)
      assert.equal(fs.existsSync(path.join(plain.agent, 'results/reproduce/units-check')), false)
      assert.equal(fs.existsSync(path.join(plain.runDir(), 'units-check/stale-work.txt')), true, 'units-check/ touched without args.units_check')
    })
    check('no-units-check: reproduce facts as before, units_match and units_full_match null', () => {
      // tokens_known depends on runner attempts (none in reproduce under reuse); tools/test_m5_reproduce.js
      // checks the full facts of generated-harness runs.
      const { tokens_known, ...facts } = plain.stage('reproduce').facts
      assert.equal(typeof tokens_known === 'boolean' || tokens_known === null, true)
      assert.deepEqual(facts, { anchors_passed: 2, anchors_total: 2, stock_verified: true,
        tuned_control_valid: null, gpu_busy_known: false, units_match: null, units_full_match: null,
        // SCHEMAS.md U52: the four unit-probe facts are null outside unit-probe mode.
        units_outcome: null, units_factor_2: null, units_factor_4: null, units_shared_writes: null,
        // SCHEMAS.md "Card calibration (U54)": the four card facts are null outside card mode.
        card_inputs: null, card_measured: null, card_holds: null, card_refuted: null })
      assert.equal(plain.stage('reproduce').run_valid, true)
    })
  } catch (error) { failures++; console.log(`FAIL test harness: ${error.stack}`) }
  finally { fs.rmSync(scratch, { recursive: true, force: true }) }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : 'all checks passed')
  process.exitCode = failures ? 1 : 0
}
main()
