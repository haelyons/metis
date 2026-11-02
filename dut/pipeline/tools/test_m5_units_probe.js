#!/usr/bin/env node
'use strict'

// Black-box tests of the concurrency probe's unit mode (U50b), from m5/SCHEMAS.md "Concurrency probe"
// (bullets "Unit mode (U50b)" to "The standalone unit probe (U52) validates", the command-mode bullet
// "Each invocation runs ..." for the work-directory layout) and "A/harness/" bullet "Optional unit files (U50)".
// The probe is copied into a temporary shared run directory and executed (python3 -I), never read.
// Usage: node tools/test_m5_units_probe.js
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const crypto = require('node:crypto')
const assert = require('node:assert/strict')
const { spawn, spawnSync } = require('node:child_process')
const { assertConcurrencyShape } = require('./m5_profile_fixture.js')
const ROOT = path.resolve(__dirname, '..')
const scratch = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_units_probe_')))
let checks = 0, failures = 0
function check(name, run) {
  checks++
  try { run(); console.log(`ok ${name}`) }
  catch (error) { failures++; console.log(`FAIL ${name}: ${error.message.replace(/\s*\n\s*/g, ' ')}`) }
}
function script(file, body) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, '#!/usr/bin/env bash\n' + body + '\n', { mode: 0o755 })
}

const ARMS = ['a-1', 'b-1', 'c2-1', 'c4-1', 'c4-2', 'c2-2', 'b-2', 'a-2']
const dirsOf = label => label.startsWith('a') ? [label] : [1, 2, 3, 4].map(j => `${label}-${j}`)
const OUTCOMES = ['invalid_units', 'failed', 'baseline_mismatch', 'outputs_mismatch', 'skipped', 'measured']
const UNIT_KEYS = ['mode', 'mps', 'mps_failed', 'outcome', 'units_total', 'sample', 'baseline_match', 'outputs_match',
  'serial_wall_s', 'separate_wall_s', 'batches', 'arms', 'nproc', 'mem_total_kb', 'factor']
const ARM_KEYS = ['label', 'wall_s', 'all_ok', 'skipped', 'cpu_s', 'effective_cores', 'busy_fraction',
  'mem_available_min_kb', 'threads_max', 'shared_changes', 'invocations']
const ARM_NUMBERS = ['wall_s', 'cpu_s', 'effective_cores', 'busy_fraction', 'mem_available_min_kb', 'threads_max', 'shared_changes']
const INV_KEYS = ['units', 'rc', 'wall_s', 'cpu_s', 'max_rss_kb', 'nivcsw', 'inblock', 'oublock']
// Top-level entries every work directory must link (out, profiler, concurrency-work, evaluation-work excluded).
const LINKED = ['.hidden', 'baseline-published', 'data', 'harness', 'top.txt']

// Restricted PATH: no host nvidia-cuda-mps-control unless a test adds a fake.
const tools = path.join(scratch, 'tools')
fs.mkdirSync(tools)
for (const tool of ['bash', 'sh', 'env', 'python3', 'sleep', 'cat', 'ls', 'date', 'readlink', 'basename', 'dirname',
  'mkdir', 'rm', 'rmdir', 'chmod', 'cp', 'mv', 'ln', 'touch', 'true', 'false', 'mktemp', 'uname', 'id', 'tee', 'head', 'tail', 'grep', 'sed', 'awk']) {
  const found = spawnSync('/bin/bash', ['-c', 'command -v "$1"', 'locate', tool], { encoding: 'utf8' })
  if (found.status === 0 && found.stdout.trim().startsWith('/')) fs.symlinkSync(found.stdout.trim(), path.join(tools, tool))
}

// Fake run_units.sh. Records (outside the run directory) its work directory, arguments, session,
// environment, work-directory listing and start/end times; writes each listed unit's outputs under out/
// with content `unit <id> path <path>`; sleeps UNIT_SLEEP per unit plus EXTRA_SLEEP (`<name pattern>:<s>`).
// Controls by work directory name: FAIL (exit 3), OMIT (skip one output), CORRUPT (one byte differs).
// SHARED_WRITES=1 writes through the links into the shared run directory and to excluded places.
const RUN_UNITS = `set -u
name=$(basename "$PWD")
record="$RECORDS/$name"
ids=("$@")
stat=$(cat "/proc/$$/stat")
read -r _state _ppid pgrp sid _rest <<< "\${stat##*) }"
{
  printf 'name=%s\\npwd=%s\\npid=%s\\npgrp=%s\\nsid=%s\\nnargs=%s\\nargs=%s\\n' "$name" "$(pwd -P)" "$$" "$pgrp" "$sid" "$#" "$*"
  printf 'env=%s\\n' "\${FIXTURE_ENV-<unset>}"
  for var in $(compgen -e); do case "$var" in CUDA_MPS_*) printf 'mpsvar=%s\\n' "$var" ;; esac; done
  if [ -d out ] && [ ! -L out ] && [ -z "$(ls -A out)" ]; then printf 'outempty=yes\\n'; else printf 'outempty=no\\n'; fi
  shopt -s dotglob nullglob
  for entry in *; do
    if [ -L "$entry" ]; then printf 'link=%s=%s\\n' "$entry" "$(readlink -f "$entry")"
    elif [ -d "$entry" ]; then printf 'dir=%s\\n' "$entry"
    else printf 'file=%s\\n' "$entry"; fi
  done
  shopt -u dotglob nullglob
  printf 'start=%s\\n' "$(date +%s.%N)"
} > "$record"
set -f
echo "stdout $name"
echo "stderr $name" >&2
listed() { local item; for item in $1; do [ "$item" = "$name" ] && return 0; done; return 1; }
omit=no; listed "\${OMIT-}" && omit=yes
corrupt=no; listed "\${CORRUPT-}" && corrupt=yes
for id in "\${ids[@]}"; do
  while IFS=$'\\t' read -r uid upath; do
    [ "$uid" = "$id" ] || continue
    if [ "$omit" = yes ]; then omit=done; continue; fi
    content="unit $uid path $upath"
    if [ "$corrupt" = yes ]; then content="Unit $uid path $upath"; corrupt=done; fi
    mkdir -p "out/$(dirname "$upath")"
    printf '%s\\n' "$content" > "out/$upath"
  done < "$OUTPUTS_FILE"
  sleep "\${UNIT_SLEEP-0.2}"
done
for item in \${EXTRA_SLEEP-}; do case "$name" in \${item%%:*}) sleep "\${item#*:}" ;; esac; done
if [ -n "\${BURN-}" ]; then python3 -I -c 'import sys, time
t = time.process_time()
while time.process_time() - t < float(sys.argv[1]): pass' "$BURN"; fi
if [ "\${SHARED_WRITES-}" = 1 ]; then
  printf x > "data/created-$name"
  mkdir -p "data/sub-$name"; printf x > "data/sub-$name/f"
  printf x >> top.txt
  case "$name" in a-1) rm -f data/doomed.txt ;; a-2) printf x >> .hidden ;; b-2-*) touch -m data/stamp.txt ;; esac
  printf x > "stray-$name"
  printf x > "extlink/f-$name"
  printf x > "$SHARED/profiler/extra-$name"
  printf x > "$SHARED/out/extra-$name"
fi
rc=0
listed "\${FAIL-}" && rc=3
printf 'end=%s\\nrc=%s\\n' "$(date +%s.%N)" "$rc" >> "$record"
exit "$rc"`
const RUN_COMMAND = `mkdir -p out; printf '%s\\n' "$(basename "$PWD")" > out/result.txt; sleep 0.05`

// Unit k: unusual but valid id and output paths, so leaks into concurrency.json are recognisable.
function makeUnits(costs) {
  return costs.map((cost_s, k) => ({
    id: `Uq7.${k}:a+b=c-z`,
    outputs: k % 3 === 0 ? [`rq7=${k}/a+b.out`, `rq7=${k}/d.d/e_${k}.txt`] : [`rq7_${k}.txt`],
    cost_s,
  }))
}
function sampleOf(units) {
  const order = units.map((_, i) => i).sort((a, b) => units[a].cost_s - units[b].cost_s || a - b)
  const start = Math.floor((units.length - 4) / 2)
  return order.slice(start, start + 4)
}
const contentOf = (id, file) => `unit ${id} path ${file}\n`
const sha = text => crypto.createHash('sha256').update(text).digest('hex')
function referenceOf(units) {
  const sha256 = {}
  for (const index of sampleOf(units)) for (const file of units[index].outputs) sha256[file] = sha(contentOf(units[index].id, file))
  return { sha256 }
}
const DEFAULT_COSTS = [4, 1, 3, 2]

function setupRun(name) {
  const run = path.join(scratch, name)
  script(path.join(run, 'harness', 'run_units.sh'), RUN_UNITS)
  script(path.join(run, 'harness', 'run_command.sh'), RUN_COMMAND)
  fs.mkdirSync(path.join(run, 'baseline-published'))
  fs.writeFileSync(path.join(run, 'baseline-published', 'pin'), 'pinned\n')
  fs.mkdirSync(path.join(run, 'data'))
  fs.writeFileSync(path.join(run, 'data', 'input'), 'input\n')
  fs.writeFileSync(path.join(run, 'top.txt'), 'top\n')
  fs.writeFileSync(path.join(run, '.hidden'), 'hidden\n')
  fs.mkdirSync(path.join(run, 'out'))
  fs.writeFileSync(path.join(run, 'out', 'keep.txt'), 'shared\n')
  fs.mkdirSync(path.join(run, 'profiler'))
  fs.copyFileSync(path.join(ROOT, 'm5', 'concurrency_probe.py'), path.join(run, 'profiler', 'concurrency_probe.py'))
  fs.mkdirSync(path.join(run, 'evaluation-work'))
  fs.mkdirSync(path.join(scratch, `${name}-records`))
  return run
}
function parseRecord(file) {
  const record = { links: {}, dirs: [], files: [], mpsvars: [] }
  for (const line of fs.readFileSync(file, 'utf8').split('\n').filter(Boolean)) {
    const [key, ...rest] = line.split('='), value = rest.join('=')
    if (key === 'link') { const [entry, ...target] = value.split('='); record.links[entry] = target.join('=') }
    else if (key === 'dir') record.dirs.push(value)
    else if (key === 'file') record.files.push(value)
    else if (key === 'mpsvar') record.mpsvars.push(value)
    else record[key] = ['start', 'end', 'rc', 'pid', 'pgrp', 'sid', 'nargs'].includes(key) ? Number(value) : value
  }
  return record
}

// Runs `python3 -I profiler/concurrency_probe.py --units harness/run_units.sh harness/units.json out/concurrency <budget> profiler/units_reference.json`.
// manifest: undefined (write {units}), a string (raw content), null (absent) or 'dir' (a directory).
// ref: 'ok', null (absent), a string (raw content) or a function of the correct reference object.
async function probeUnits(name, { costs = DEFAULT_COSTS, units, manifest, ref = 'ok', budget = 1000, env = {}, prepare,
  args, path: PATH = tools } = {}) {
  units = units ?? makeUnits(costs)
  const run = setupRun(name)
  const records = path.join(scratch, `${name}-records`)
  const outputsFile = path.join(scratch, `${name}-outputs.tsv`)
  fs.writeFileSync(outputsFile, units.flatMap(unit => unit.outputs.map(file => `${unit.id}\t${file}\n`)).join(''))
  const manifestFile = path.join(run, 'harness', 'units.json')
  if (manifest === undefined) fs.writeFileSync(manifestFile, JSON.stringify({ units }))
  else if (manifest === 'dir') fs.mkdirSync(manifestFile)
  else if (typeof manifest === 'string') fs.writeFileSync(manifestFile, manifest)
  const refFile = path.join(run, 'profiler', 'units_reference.json')
  if (ref === 'ok') fs.writeFileSync(refFile, JSON.stringify(referenceOf(units)))
  else if (typeof ref === 'string') fs.writeFileSync(refFile, ref)
  else if (typeof ref === 'function') {
    const value = ref(referenceOf(units))
    fs.writeFileSync(refFile, typeof value === 'string' ? value : JSON.stringify(value))
  }
  if (prepare) prepare(run)
  const argv = args ?? ['--units', 'harness/run_units.sh', 'harness/units.json', 'out/concurrency', String(budget), 'profiler/units_reference.json']
  const result = await new Promise(resolve => {
    const child = spawn(path.join(tools, 'python3'), ['-I', 'profiler/concurrency_probe.py', ...argv], {
      cwd: run, timeout: 150000, killSignal: 'SIGKILL',
      env: { PATH, HOME: scratch, TMPDIR: scratch, LANG: 'C.UTF-8', RECORDS: records, OUTPUTS_FILE: outputsFile,
        FIXTURE_ENV: 'preserved', SHARED: run, UNIT_SLEEP: '0.2', ...env },
    })
    let stdout = '', stderr = '', error
    child.stdout.on('data', data => { stdout += data })
    child.stderr.on('data', data => { stderr += data })
    child.on('error', value => { error = value })
    child.on('close', (status, signal) => resolve({ status, signal, stdout, stderr, error }))
  })
  assert.ifError(result.error)
  await new Promise(resolve => setTimeout(resolve, 100))
  const byName = {}
  for (const file of fs.readdirSync(records)) byName[file] = parseRecord(path.join(records, file))
  const output = path.join(run, 'out', 'concurrency', 'concurrency.json')
  const text = fs.existsSync(output) ? fs.readFileSync(output, 'utf8') : undefined
  let value
  try { value = text === undefined ? undefined : JSON.parse(text) } catch { value = undefined }
  return { ...result, name, run, units, sample: sampleOf(units), byName, output, text, value }
}
const diagnostics = result => `exit ${result.status}/${result.signal}; ${result.stderr.slice(-800)}`
const close = (actual, expected, label, tolerance = 1e-5) =>
  assert.ok(typeof actual === 'number' && Math.abs(actual - expected) <= tolerance + 1e-6 * Math.abs(expected), `${label}: ${actual} != ${expected}`)
const mean = values => values.reduce((sum, value) => sum + value, 0) / values.length
const armOf = (value, label) => value.arms.find(arm => arm.label === label)
const ran = arm => arm.wall_s !== null

// Exact unit-mode shape and the arithmetic the contract fixes.
function assertUnitShape(value) {
  const finiteNonneg = (x, label) => assert.ok(typeof x === 'number' && Number.isFinite(x) && x >= 0, `${label}: ${x}`)
  const positive = (x, label) => assert.ok(typeof x === 'number' && Number.isFinite(x) && x > 0, `${label}: ${x}`)
  const nullablePositive = (x, label) => { if (x !== null) positive(x, label) }
  const nullableBool = (x, label) => assert.ok(x === null || typeof x === 'boolean', `${label}: ${x}`)
  assert.ok(value && typeof value === 'object' && !Array.isArray(value), 'concurrency.json must be an object')
  assert.deepEqual(Object.keys(value).sort(), [...UNIT_KEYS].sort(), 'top-level keys')
  assert.equal(value.mode, 'units')
  assert.equal(value.mps, false)
  assert.equal(value.mps_failed, false)
  assert.ok(OUTCOMES.includes(value.outcome), `outcome ${value.outcome}`)
  if (value.outcome === 'invalid_units') {
    assert.equal(value.units_total, null)
    assert.deepEqual(value.sample, [])
  } else {
    assert.ok(Number.isInteger(value.units_total) && value.units_total >= 4, `units_total ${value.units_total}`)
    assert.equal(value.sample.length, 4, 'sample rows')
    for (const row of value.sample) {
      assert.deepEqual(Object.keys(row).sort(), ['cost_s', 'index'])
      assert.ok(Number.isInteger(row.index) && row.index >= 0 && row.index < value.units_total, `sample index ${row.index}`)
      positive(row.cost_s, 'sample cost_s')
    }
    assert.equal(new Set(value.sample.map(row => row.index)).size, 4, 'sample indices distinct')
  }
  nullableBool(value.baseline_match, 'baseline_match')
  nullableBool(value.outputs_match, 'outputs_match')
  nullablePositive(value.serial_wall_s, 'serial_wall_s')
  nullablePositive(value.separate_wall_s, 'separate_wall_s')
  assert.ok(Array.isArray(value.arms) && value.arms.length === 8, 'eight arms')
  assert.deepEqual(value.arms.map(arm => arm.label), ARMS, 'arm order')
  for (const arm of value.arms) {
    assert.deepEqual(Object.keys(arm).sort(), [...ARM_KEYS].sort(), `${arm.label}: keys`)
    assert.equal(typeof arm.all_ok, 'boolean', `${arm.label}: all_ok`)
    assert.equal(typeof arm.skipped, 'boolean', `${arm.label}: skipped`)
    assert.ok(Array.isArray(arm.invocations), `${arm.label}: invocations`)
    if (!ran(arm)) {
      for (const key of ARM_NUMBERS) assert.equal(arm[key], null, `${arm.label}: ${key} must be null when the arm did not run`)
      assert.deepEqual(arm.invocations, [], `${arm.label}: invocations of an arm that did not run`)
      continue
    }
    for (const key of ARM_NUMBERS) finiteNonneg(arm[key], `${arm.label}: ${key}`)
    assert.ok(Number.isInteger(arm.shared_changes), `${arm.label}: shared_changes integer`)
    assert.ok(arm.busy_fraction <= 1 + 1e-9, `${arm.label}: busy_fraction ${arm.busy_fraction}`)
    assert.ok(arm.mem_available_min_kb <= value.mem_total_kb, `${arm.label}: mem_available_min_kb above MemTotal`)
    assert.equal(arm.skipped, false, `${arm.label}: ran but skipped`)
    assert.ok(arm.invocations.length >= 1, `${arm.label}: ran without invocations`)
    for (const row of arm.invocations) {
      assert.deepEqual(Object.keys(row).sort(), [...INV_KEYS].sort(), `${arm.label}: invocation keys`)
      assert.ok(Array.isArray(row.units) && row.units.length >= 1 && row.units.every(unit => Number.isInteger(unit) && unit >= 0 && unit <= 3), `${arm.label}: units ${JSON.stringify(row.units)}`)
      assert.ok(Number.isInteger(row.rc), `${arm.label}: rc ${row.rc}`)
      for (const key of INV_KEYS.slice(2)) finiteNonneg(row[key], `${arm.label}: invocation ${key}`)
    }
    close(arm.cpu_s, arm.invocations.reduce((sum, row) => sum + row.cpu_s, 0), `${arm.label}: cpu_s is the sum over invocations`, 1e-3)
    if (arm.wall_s > 0) close(arm.effective_cores, arm.cpu_s / arm.wall_s, `${arm.label}: effective_cores = cpu_s / wall_s`, 1e-3)
  }
  assert.ok(Array.isArray(value.batches) && value.batches.length === 2, 'two batches')
  for (const [index, n] of [2, 4].entries()) {
    const batch = value.batches[index]
    assert.deepEqual(Object.keys(batch).sort(), ['all_ok', 'factor', 'n', 'skipped', 'wall_s'], `n=${n}: keys`)
    assert.equal(batch.n, n)
    assert.equal(typeof batch.all_ok, 'boolean')
    assert.equal(typeof batch.skipped, 'boolean')
    nullablePositive(batch.wall_s, `n=${n}: wall_s`)
    nullablePositive(batch.factor, `n=${n}: factor`)
    const executed = value.arms.filter(arm => arm.label.startsWith(`c${n}-`) && ran(arm))
    assert.equal(batch.skipped, executed.length === 0, `n=${n}: skipped iff no c${n} arm ran`)
    if (executed.length) close(batch.wall_s, mean(executed.map(arm => arm.wall_s)), `n=${n}: wall_s is the mean of executed c${n} arms`)
    else { assert.equal(batch.wall_s, null); assert.equal(batch.all_ok, false, `n=${n}: all_ok without a run`) }
    if (batch.all_ok && value.outcome === 'measured') close(batch.factor, value.serial_wall_s / batch.wall_s, `n=${n}: factor = serial_wall_s / wall_s`)
    else assert.equal(batch.factor, null, `n=${n}: factor must be null (all_ok ${batch.all_ok}, outcome ${value.outcome})`)
  }
  const factors = value.batches.map(batch => batch.factor).filter(factor => factor !== null)
  assert.equal(value.factor, factors.length ? Math.max(...factors) : null, 'factor is the largest batch factor')
  assert.ok(Number.isInteger(value.nproc) && value.nproc > 0, `nproc ${value.nproc}`)
  positive(value.mem_total_kb, 'mem_total_kb')
}
function written(result) {
  assert.equal(result.status, 0, diagnostics(result))
  assert.ok(result.text !== undefined, `concurrency.json missing; ${diagnostics(result)}`)
  assert.ok(result.value !== undefined, 'concurrency.json is not JSON')
  assertUnitShape(result.value)
}
function noIdentifiers(result) {
  for (const unit of result.units) {
    assert.ok(!result.text.includes(unit.id), `unit id ${unit.id} in concurrency.json`)
    for (const file of unit.outputs) assert.ok(!result.text.includes(file), `output path ${file} in concurrency.json`)
  }
}
const ownSid = Number(fs.readFileSync('/proc/self/stat', 'utf8').split(') ')[1].split(' ')[3])

// Invocations of the arms that ran: names, units, ids, order, timing, work directories, logs, sessions.
function assertInvocations(result, { workspace = true } = {}) {
  const { value, byName, run, sample, units } = result
  const ids = sample.map(index => units[index].id)
  const expectedNames = []
  const arms = []
  for (const arm of value.arms) {
    if (!ran(arm)) continue
    const names = dirsOf(arm.label).slice(0, arm.invocations.length)
    assert.equal(arm.invocations.length, dirsOf(arm.label).length, `${arm.label}: invocation count`)
    expectedNames.push(...names)
    const rows = names.map((name, j) => ({ name, row: arm.invocations[j], record: byName[name] }))
    for (const { name, row, record } of rows) {
      assert.ok(record, `${name}: no invocation ran in concurrency-work/${name}/ (ran: ${Object.keys(byName).sort().join(' ')})`)
      assert.equal(record.args, row.units.map(unit => ids[unit]).join(' '), `${name}: ids passed`)
      assert.equal(record.nargs, row.units.length, `${name}: argument count`)
      assert.equal(row.rc, record.rc, `${name}: rc`)
      assert.ok(record.end >= record.start, `${name}: no end record`)
      assert.ok(row.wall_s >= record.end - record.start - 0.05, `${name}: wall ${row.wall_s} shorter than the command`)
      assert.ok(row.wall_s <= record.end - record.start + 1.5, `${name}: wall ${row.wall_s} far longer than the command`)
    }
    const kind = arm.label.split('-')[0]
    const unitsOf = arm.invocations.map(row => row.units)
    if (kind === 'a') assert.deepEqual(unitsOf, [[0, 1, 2, 3]], `${arm.label}: units`)
    if (kind === 'b') assert.deepEqual(unitsOf, [[0], [1], [2], [3]], `${arm.label}: units in sample order`)
    if (kind === 'c2') {
      assert.deepEqual(unitsOf.slice(0, 2).flat().sort(), [0, 1], `${arm.label}: first pair`)
      assert.deepEqual(unitsOf.slice(2).flat().sort(), [2, 3], `${arm.label}: second pair`)
      assert.ok(unitsOf.every(units => units.length === 1), `${arm.label}: one unit per invocation`)
    }
    if (kind === 'c4') {
      assert.deepEqual(unitsOf.flat().sort(), [0, 1, 2, 3], `${arm.label}: units`)
      assert.ok(unitsOf.every(units => units.length === 1), `${arm.label}: one unit per invocation`)
    }
    const recs = rows.map(entry => entry.record)
    const overlap = group => assert.ok(Math.max(...group.map(r => r.start)) < Math.min(...group.map(r => r.end)),
      `${arm.label}: ${group.map(r => r.name).join(',')} did not run at once`)
    const after = (first, second) => assert.ok(Math.max(...first.map(r => r.end)) <= Math.min(...second.map(r => r.start)),
      `${arm.label}: ${second.map(r => r.name).join(',')} started before ${first.map(r => r.name).join(',')} ended`)
    if (kind === 'b') for (let j = 1; j < 4; j++) after([recs[j - 1]], [recs[j]])
    if (kind === 'c2') { overlap(recs.slice(0, 2)); overlap(recs.slice(2)); after(recs.slice(0, 2), recs.slice(2)) }
    if (kind === 'c4') overlap(recs)
    const span = Math.max(...recs.map(r => r.end)) - Math.min(...recs.map(r => r.start))
    assert.ok(arm.wall_s >= span - 0.05, `${arm.label}: wall ${arm.wall_s} shorter than its invocations' span ${span}`)
    assert.ok(arm.wall_s <= span + 2.5, `${arm.label}: wall ${arm.wall_s} far longer than span ${span}`)
    arms.push(recs)
  }
  for (let i = 1; i < arms.length; i++)
    assert.ok(Math.max(...arms[i - 1].map(r => r.end)) <= Math.min(...arms[i].map(r => r.start)), `arm ${i} overlapped the arm before it`)
  assert.deepEqual(Object.keys(byName).sort(), [...expectedNames].sort(), 'invocations that ran')
  const sids = Object.values(byName).map(r => r.sid)
  assert.equal(new Set(sids).size, sids.length, 'each invocation starts its own session')
  for (const record of Object.values(byName)) {
    assert.equal(record.pgrp, record.sid, `${record.name}: own process group`)
    assert.notEqual(record.sid, ownSid, `${record.name}: shares the probe's session`)
    assert.deepEqual(record.mpsvars, [], `${record.name}: CUDA_MPS_* set in unit mode`)
    assert.equal(record.env, 'preserved', `${record.name}: environment not inherited`)
    const log = fs.readFileSync(path.join(run, 'out', 'concurrency', 'logs', `${record.name}.log`), 'utf8')
    assert.match(log, new RegExp(`stdout ${record.name}\n`), `${record.name}: stdout not in its log`)
    assert.match(log, new RegExp(`stderr ${record.name}\n`), `${record.name}: stderr not in its log`)
    if (!workspace) continue
    assert.equal(record.pwd, path.join(run, 'concurrency-work', record.name), `${record.name}: working directory`)
    assert.equal(record.outempty, 'yes', `${record.name}: out/ must start empty`)
    assert.deepEqual(record.dirs, ['out'], `${record.name}: only out/ is a real directory`)
    assert.deepEqual(record.files, [], `${record.name}: unexpected regular files`)
    assert.deepEqual(Object.keys(record.links).sort(), LINKED, `${record.name}: linked entries`)
    for (const entry of LINKED) assert.equal(record.links[entry], path.join(run, entry), `${record.name}: ${entry} target`)
  }
}
function sampleRows(result) {
  assert.deepEqual(result.value.sample, result.sample.map(index => ({ index, cost_s: result.units[index].cost_s })))
  assert.equal(result.value.units_total, result.units.length)
}
const noneRan = result => assert.deepEqual(Object.keys(result.byName), [], 'an invocation ran')
function onlyFirstArm(result) {
  assert.deepEqual(Object.keys(result.byName), ['a-1'], 'only a-1 may run')
  for (const arm of result.value.arms.slice(1)) assert.ok(!ran(arm), `${arm.label} ran after a-1`)
}

async function main() {
  // 1. Usage.
  const runUsage = async (name, args) => probeUnits(name, { args })
  for (const [name, args] of [
    ['usage-units-0', ['--units']],
    ['usage-units-3', ['--units', 'harness/run_units.sh', 'harness/units.json', 'out/concurrency']],
    ['usage-units-4', ['--units', 'harness/run_units.sh', 'harness/units.json', 'out/concurrency', '1000']],
    ['usage-units-6', ['--units', 'harness/run_units.sh', 'harness/units.json', 'out/concurrency', '1000', 'profiler/units_reference.json', 'extra']],
    ['usage-command-0', []],
    ['usage-command-2', ['harness/run_command.sh', 'out/concurrency']],
    ['usage-command-4', ['harness/run_command.sh', 'out/concurrency', '100', 'extra']],
  ]) {
    const result = await runUsage(name, args)
    check(`${name}: wrong argument count exits nonzero without running anything`, () => {
      assert.notEqual(result.status, 0, 'exit 0 on wrong argument count')
      assert.equal(result.signal, null, `killed by ${result.signal}`)
      noneRan(result)
      assert.equal(result.text, undefined, 'concurrency.json written')
    })
  }
  const command = await probeUnits('command-mode', { args: ['harness/run_command.sh', 'out/concurrency', '100'] })
  check('command mode still works: exit 0, command-mode shape (no mode key), no unit invocations', () => {
    assert.equal(command.status, 0, diagnostics(command))
    assert.ok(command.value, 'concurrency.json missing')
    assertConcurrencyShape(command.value)
    assert.ok(!('mode' in command.value), 'command mode wrote a mode key')
    noneRan(command)
    assert.ok(command.value.factor > 0, `factor ${command.value.factor}`)
  })

  // 2. invalid_units.
  const good = makeUnits(DEFAULT_COSTS)
  const withUnit = (k, change) => JSON.stringify({ units: good.map((unit, i) => i === k ? change({ ...unit }) : unit) })
  for (const [name, manifest] of [
    ['invalid-missing', null],
    ['invalid-directory', 'dir'],
    ['invalid-not-json', '{"units": ['],
    ['invalid-empty-file', ''],
    ['invalid-array', JSON.stringify(good)],
    ['invalid-extra-top-key', JSON.stringify({ units: good, note: 'x' })],
    ['invalid-units-not-array', JSON.stringify({ units: { a: good[0] } })],
    ['invalid-three-units', JSON.stringify({ units: good.slice(0, 3) })],
    ['invalid-zero-units', JSON.stringify({ units: [] })],
    ['invalid-unit-extra-key', withUnit(1, unit => ({ ...unit, extra: 1 }))],
    ['invalid-unit-missing-cost', withUnit(1, ({ cost_s, ...unit }) => unit)],
    ['invalid-unit-not-object', JSON.stringify({ units: [...good.slice(0, 3), 'u3'] })],
    ['invalid-duplicate-id', withUnit(2, unit => ({ ...unit, id: good[1].id }))],
    ['invalid-id-number', withUnit(1, unit => ({ ...unit, id: 7 }))],
    ['invalid-id-leading-dash', withUnit(1, unit => ({ ...unit, id: '-u1' }))],
    ['invalid-id-space', withUnit(1, unit => ({ ...unit, id: 'u 1' }))],
    ['invalid-id-slash', withUnit(1, unit => ({ ...unit, id: 'u/1' }))],
    ['invalid-id-empty', withUnit(1, unit => ({ ...unit, id: '' }))],
    ['invalid-id-129-chars', withUnit(1, unit => ({ ...unit, id: 'u'.repeat(129) }))],
    ['invalid-outputs-empty', withUnit(1, unit => ({ ...unit, outputs: [] }))],
    ['invalid-outputs-string', withUnit(1, unit => ({ ...unit, outputs: 'rq7_1.txt' }))],
    ['invalid-outputs-duplicate', withUnit(1, unit => ({ ...unit, outputs: ['rq7_1.txt', 'rq7_1.txt'] }))],
    ['invalid-output-dotdot', withUnit(1, unit => ({ ...unit, outputs: ['../rq7_1.txt'] }))],
    ['invalid-output-dot', withUnit(1, unit => ({ ...unit, outputs: ['./rq7_1.txt'] }))],
    ['invalid-output-absolute', withUnit(1, unit => ({ ...unit, outputs: ['/rq7_1.txt'] }))],
    ['invalid-output-trailing-slash', withUnit(1, unit => ({ ...unit, outputs: ['rq7_1/'] }))],
    ['invalid-output-bad-char', withUnit(1, unit => ({ ...unit, outputs: ['rq7 1.txt'] }))],
    ['invalid-output-empty', withUnit(1, unit => ({ ...unit, outputs: [''] }))],
    ['invalid-cost-zero', withUnit(1, unit => ({ ...unit, cost_s: 0 }))],
    ['invalid-cost-negative', withUnit(1, unit => ({ ...unit, cost_s: -1 }))],
    ['invalid-cost-string', withUnit(1, unit => ({ ...unit, cost_s: '1' }))],
    ['invalid-cost-boolean', withUnit(1, unit => ({ ...unit, cost_s: true }))],
    ['invalid-cost-null', withUnit(1, unit => ({ ...unit, cost_s: null }))],
    ['invalid-cost-infinite', withUnit(1, unit => ({ ...unit, cost_s: 1 })).replace('"cost_s":1,', '"cost_s":1e999,').replace('"cost_s":1}', '"cost_s":1e999}')],
  ]) {
    const result = await probeUnits(name, { manifest })
    check(`${name}: outcome invalid_units, units_total null, sample [], no arm runs, exit 0`, () => {
      written(result)
      assert.equal(result.value.outcome, 'invalid_units')
      assert.equal(result.value.units_total, null)
      assert.deepEqual(result.value.sample, [])
      noneRan(result)
      for (const arm of result.value.arms) assert.ok(!ran(arm), `${arm.label} ran`)
      assert.equal(result.value.baseline_match, null)
      assert.equal(result.value.outputs_match, null)
      assert.equal(result.value.serial_wall_s, null)
      assert.equal(result.value.separate_wall_s, null)
      assert.equal(result.value.factor, null)
    })
  }

  // 3/4. Sample rule, ids per invocation, arm order, work directories, logs, overlap. Run in parallel.
  const sampleCases = [
    ['sample-n4-distinct', [4, 1, 3, 2], [1, 3, 2, 0]],
    ['sample-n4-ties', [2, 1, 2, 1], [1, 3, 0, 2]],
    ['sample-n5-distinct', [5, 3, 1, 4, 2], [2, 4, 1, 3]],
    ['sample-n5-ties', [2, 2, 1, 2, 1], [2, 4, 0, 1]],
    ['sample-n8-distinct', [8, 1, 7, 2, 6, 3, 5, 4], [5, 7, 6, 4]],
    ['sample-n8-ties', [3, 1, 3, 2, 3, 2, 1, 3], [3, 5, 0, 2]],
    ['sample-n9-distinct', [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1], [6, 5, 4, 3]],
    ['sample-n9-ties', [2, 2, 2, 2, 1, 2, 2, 2, 3], [1, 2, 3, 5]],
  ]
  const sampleResults = await Promise.all(sampleCases.map(([name, costs]) => probeUnits(name, { costs })))
  for (const [[name, costs, expected], result] of sampleCases.map((entry, i) => [entry, sampleResults[i]])) {
    check(`${name}: fixture sample rule gives ${expected.join(',')}`, () => assert.deepEqual(sampleOf(makeUnits(costs)), expected))
    check(`${name}: measured, sample rows carry manifest positions and costs in sample order`, () => {
      written(result)
      assert.equal(result.value.outcome, 'measured', `outcome ${result.value.outcome}`)
      sampleRows(result)
    })
    check(`${name}: ids per invocation, arm order, work directories, logs, sessions, concurrency`, () => {
      written(result)
      assert.ok(result.value.arms.every(ran), 'every arm runs with a large budget')
      assertInvocations(result)
    })
    check(`${name}: no unit id or output path in concurrency.json`, () => { written(result); noIdentifiers(result) })
    check(`${name}: no shared writes counted when invocations write only under their own out/`, () => {
      written(result)
      assert.deepEqual(result.value.arms.map(arm => arm.shared_changes), ARMS.map(() => 0))
    })
  }

  // 9. measured: exact keys, means, factors, resources, atomic write, no MPS lookup.
  const mpsCalls = path.join(scratch, 'mps-calls.log')
  const mpsBin = path.join(scratch, 'mps-bin')
  script(path.join(mpsBin, 'nvidia-cuda-mps-control'), `printf 'called %s\\n' "$*" >> "${mpsCalls}"; exit 0`)
  const sentinel = path.join(scratch, 'sentinel.json')
  const measured = await probeUnits('measured', {
    env: { BURN: '0.2', UNIT_SLEEP: '0.15' }, path: `${mpsBin}:${tools}`,
    prepare: run => {
      fs.writeFileSync(sentinel, 'sentinel\n')
      fs.mkdirSync(path.join(run, 'out', 'concurrency'))
      fs.linkSync(sentinel, path.join(run, 'out', 'concurrency', 'concurrency.json'))
    },
  })
  check('measured: exit 0, exact shape, outcome measured, both matches true', () => {
    written(measured)
    assert.equal(measured.value.outcome, 'measured')
    assert.equal(measured.value.baseline_match, true)
    assert.equal(measured.value.outputs_match, true)
    sampleRows(measured)
    for (const arm of measured.value.arms) { assert.equal(arm.all_ok, true, arm.label); assert.equal(arm.skipped, false, arm.label) }
    for (const batch of measured.value.batches) { assert.equal(batch.all_ok, true); assert.equal(batch.skipped, false) }
  })
  check('measured: serial/separate walls are means of a and b arms; batch walls means of c arms; factors', () => {
    written(measured)
    const v = measured.value, wall = label => armOf(v, label).wall_s
    close(v.serial_wall_s, mean([wall('a-1'), wall('a-2')]), 'serial_wall_s')
    close(v.separate_wall_s, mean([wall('b-1'), wall('b-2')]), 'separate_wall_s')
    close(v.batches[0].wall_s, mean([wall('c2-1'), wall('c2-2')]), 'n=2 wall_s')
    close(v.batches[1].wall_s, mean([wall('c4-1'), wall('c4-2')]), 'n=4 wall_s')
    for (const batch of v.batches) close(batch.factor, v.serial_wall_s / batch.wall_s, `n=${batch.n} factor`, 1e-4)
    close(v.factor, Math.max(...v.batches.map(batch => batch.factor)), 'factor', 1e-9)
    // Fake: 4 x 0.15 s sleep + 0.2 s CPU per invocation; c4 runs everything at once.
    assert.ok(v.serial_wall_s >= 0.75, `serial_wall_s ${v.serial_wall_s}`)
    assert.ok(v.batches[1].wall_s < v.serial_wall_s, 'n=4 not faster than serial although units sleep')
  })
  check('measured: invocations, ids, order, work directories, logs, sessions', () => { written(measured); assertInvocations(measured) })
  check('measured: per-invocation resources from wait4 include descendants (cpu_s >= child CPU burn), rss > 0', () => {
    written(measured)
    for (const arm of measured.value.arms) for (const row of arm.invocations) {
      assert.ok(row.cpu_s >= 0.15, `${arm.label}: cpu_s ${row.cpu_s} misses the child's 0.2 s CPU`)
      assert.ok(row.max_rss_kb > 0, `${arm.label}: max_rss_kb ${row.max_rss_kb}`)
    }
  })
  check('measured: nproc is os.cpu_count(), mem_total_kb is MemTotal', () => {
    written(measured)
    assert.equal(measured.value.nproc, os.cpus().length)
    const total = Number(/^MemTotal:\s+(\d+)\s+kB/m.exec(fs.readFileSync('/proc/meminfo', 'utf8'))[1])
    assert.equal(measured.value.mem_total_kb, total)
  })
  check('measured: unit mode never invokes the MPS binary on PATH and passes no CUDA_MPS_* variables', () => {
    assert.ok(!fs.existsSync(mpsCalls), `MPS binary invoked: ${fs.existsSync(mpsCalls) ? fs.readFileSync(mpsCalls, 'utf8') : ''}`)
    for (const record of Object.values(measured.byName)) assert.deepEqual(record.mpsvars, [], record.name)
  })
  check('measured: concurrency.json replaced atomically (a hard link to the old file keeps its content)', () => {
    written(measured)
    assert.equal(fs.readFileSync(sentinel, 'utf8'), 'sentinel\n', 'old file rewritten in place')
  })
  check('measured: no unit id or output path in concurrency.json', () => { written(measured); noIdentifiers(measured) })

  // 10. Shared writes.
  const external = path.join(scratch, 'external')
  fs.mkdirSync(external)
  const shared = await probeUnits('shared-writes', {
    env: { SHARED_WRITES: '1', UNIT_SLEEP: '0.1' },
    prepare: run => {
      fs.writeFileSync(path.join(run, 'data', 'doomed.txt'), 'doomed\n')
      fs.writeFileSync(path.join(run, 'data', 'stamp.txt'), 'stamp\n')
      fs.utimesSync(path.join(run, 'data', 'stamp.txt'), new Date(2020, 0, 1), new Date(2020, 0, 1))
      fs.symlinkSync(external, path.join(run, 'extlink'))
    },
  })
  check('shared-writes: counts appeared, disappeared, resized and retimed non-directory entries per arm', () => {
    written(shared)
    // Per invocation: 2 new files (one in a new directory) + top.txt grows once per arm.
    // a-1 also deletes data/doomed.txt; a-2 grows .hidden; b-2 touches data/stamp.txt (mtime only).
    // Not counted: directories, files in the invocation's own work directory (concurrency-work/),
    // profiler/, the shared out/, and the external directory behind the extlink symlink.
    assert.deepEqual(shared.value.arms.map(arm => [arm.label, arm.shared_changes]),
      [['a-1', 4], ['b-1', 9], ['c2-1', 9], ['c4-1', 9], ['c4-2', 9], ['c2-2', 9], ['b-2', 10], ['a-2', 4]])
  })
  check('shared-writes: the writes happened (fixture sanity)', () => {
    assert.ok(!fs.existsSync(path.join(shared.run, 'data', 'doomed.txt')))
    assert.ok(fs.existsSync(path.join(shared.run, 'profiler', 'extra-a-1')))
    assert.ok(fs.existsSync(path.join(shared.run, 'out', 'extra-c4-2-3')))
    assert.ok(fs.existsSync(path.join(external, 'f-b-1-2')))
    assert.ok(fs.existsSync(path.join(shared.run, 'concurrency-work', 'c2-1-1', 'stray-c2-1-1')))
  })
  check('shared-writes: shared_changes never changes the outcome (measured, factor set)', () => {
    written(shared)
    assert.equal(shared.value.outcome, 'measured')
    assert.equal(shared.value.baseline_match, true)
    assert.equal(shared.value.outputs_match, true)
    assert.ok(shared.value.factor > 0)
    assertInvocations(shared, { workspace: false })
  })

  // 5. baseline_match.
  const firstPath = reference => Object.keys(reference.sha256)[0]
  for (const [name, ref, options] of [
    ['baseline-wrong-digest', reference => { const key = firstPath(reference); const digest = reference.sha256[key]; reference.sha256[key] = (digest[0] === '0' ? '1' : '0') + digest.slice(1); return reference }],
    ['baseline-missing-output', 'ok', { env: { OMIT: 'a-1' } }],
    ['baseline-path-missing-from-reference', reference => { delete reference.sha256[firstPath(reference)]; return reference }],
    ['baseline-reference-extra-path', reference => { reference.sha256['zz_extra.txt'] = sha('x'); return reference }],
    ['baseline-reference-absent', null],
    ['baseline-reference-not-json', 'not json'],
    ['baseline-reference-array', reference => [reference]],
    ['baseline-reference-wrong-key', reference => ({ digests: reference.sha256 })],
    ['baseline-reference-extra-top-key', reference => ({ ...reference, note: 'x' })],
    ['baseline-reference-uppercase-hex', reference => { const key = firstPath(reference); reference.sha256[key] = reference.sha256[key].toUpperCase(); return reference }],
    ['baseline-reference-short-hex', reference => { const key = firstPath(reference); reference.sha256[key] = reference.sha256[key].slice(1); return reference }],
    ['baseline-reference-digest-number', reference => { reference.sha256[firstPath(reference)] = 1; return reference }],
  ]) {
    const result = await probeUnits(name, { ref, ...(options || {}), env: { UNIT_SLEEP: '0.05', ...(options?.env || {}) } })
    check(`${name}: baseline_match false, outcome baseline_mismatch, no later arm`, () => {
      written(result)
      assert.equal(result.value.baseline_match, false)
      assert.equal(result.value.outcome, 'baseline_mismatch')
      assert.equal(armOf(result.value, 'a-1').invocations[0].rc, 0)
      onlyFirstArm(result)
      assert.equal(result.value.outputs_match, null, 'outputs_match evaluated without a later invocation')
      assert.equal(result.value.factor, null)
      sampleRows(result)
      noIdentifiers(result)
    })
  }
  const aFails = await probeUnits('a1-fails', { env: { FAIL: 'a-1', UNIT_SLEEP: '0.05' } })
  check('a1-fails: outcome failed, rc recorded, no later arm', () => {
    written(aFails)
    assert.equal(aFails.value.outcome, 'failed')
    assert.equal(armOf(aFails.value, 'a-1').invocations[0].rc, 3)
    assert.equal(armOf(aFails.value, 'a-1').all_ok, false)
    onlyFirstArm(aFails)
    assert.equal(aFails.value.serial_wall_s, null, 'a failed a-1 counted')
    assert.equal(aFails.value.factor, null)
  })
  const aFailsBadRef = await probeUnits('a1-fails-bad-reference', { ref: 'not json', env: { FAIL: 'a-1', UNIT_SLEEP: '0.05' } })
  check('a1-fails-bad-reference: failed precedes baseline_mismatch', () => {
    written(aFailsBadRef)
    assert.equal(aFailsBadRef.value.outcome, 'failed')
    onlyFirstArm(aFailsBadRef)
  })

  // 6. outputs_match.
  const corrupt = await probeUnits('outputs-corrupt', { env: { CORRUPT: 'b-1-2 a-2', UNIT_SLEEP: '0.1' } })
  check('outputs-corrupt: one different byte in b-1-2 and a-2 gives outputs_mismatch; those arms do not count', () => {
    written(corrupt)
    const v = corrupt.value
    assert.equal(v.outcome, 'outputs_mismatch')
    assert.equal(v.baseline_match, true)
    assert.equal(v.outputs_match, false)
    assert.equal(armOf(v, 'b-1').all_ok, false)
    assert.equal(armOf(v, 'a-2').all_ok, false)
    for (const label of ['a-1', 'c2-1', 'c4-1', 'c4-2', 'c2-2', 'b-2']) assert.equal(armOf(v, label).all_ok, true, label)
    close(v.serial_wall_s, armOf(v, 'a-1').wall_s, 'serial_wall_s counts only a-1')
    close(v.separate_wall_s, armOf(v, 'b-2').wall_s, 'separate_wall_s counts only b-2')
    assert.equal(v.factor, null)
    assertInvocations(corrupt)
  })
  const missing = await probeUnits('outputs-missing', { env: { OMIT: 'c4-2-3', UNIT_SLEEP: '0.1' } })
  check('outputs-missing: a file missing in c4-2-3 gives outputs_mismatch; c4-2 does not count', () => {
    written(missing)
    const v = missing.value
    assert.equal(v.outcome, 'outputs_mismatch')
    assert.equal(v.outputs_match, false)
    assert.equal(armOf(v, 'c4-2').all_ok, false)
    assert.equal(v.batches[1].all_ok, false)
    assert.equal(v.batches[1].skipped, false)
    assert.equal(v.batches[0].all_ok, true)
    assert.ok(v.batches.every(batch => batch.factor === null))
    assertInvocations(missing)
  })

  // 7. Later invocation exits nonzero.
  const laterFails = await probeUnits('later-fails', { env: { FAIL: 'c2-2-3', UNIT_SLEEP: '0.1' } })
  check('later-fails: c2-2-3 exits nonzero: outcome failed, c2-2 does not count', () => {
    written(laterFails)
    const v = laterFails.value
    assert.equal(v.outcome, 'failed')
    assert.equal(v.baseline_match, true)
    const arm = armOf(v, 'c2-2')
    assert.equal(arm.all_ok, false)
    assert.equal(arm.invocations[2].rc, 3)
    assert.equal(v.batches[0].all_ok, false)
    assert.equal(v.batches[0].skipped, false)
    assert.equal(v.batches[1].all_ok, true)
    assert.equal(v.factor, null)
  })
  const failedFirst = await probeUnits('failed-precedes-mismatch', { env: { FAIL: 'c4-1-2', CORRUPT: 'b-1-1', UNIT_SLEEP: '0.1' } })
  check('failed-precedes-mismatch: a failing invocation and a corrupt output give outcome failed', () => {
    written(failedFirst)
    assert.equal(failedFirst.value.outcome, 'failed')
    assert.equal(failedFirst.value.outputs_match, false)
    assert.equal(armOf(failedFirst.value, 'c4-1').all_ok, false)
    assert.equal(armOf(failedFirst.value, 'b-1').all_ok, false)
  })

  // 8. Budget. Estimate: sum of sample cost_s for a-1, a-1's measured wall for later arms; skip when
  // estimate > 0.9 * budget - elapsed, and then skip every later arm too.
  const skipAll = await probeUnits('budget-skips-all', { costs: [50, 50, 50, 50], budget: 100, env: { UNIT_SLEEP: '0.05' } })
  check('budget-skips-all: cost sum 200 > 90: every arm skipped with nulls, outcome skipped', () => {
    written(skipAll)
    const v = skipAll.value
    noneRan(skipAll)
    assert.equal(v.outcome, 'skipped')
    for (const arm of v.arms) assert.equal(arm.skipped, true, `${arm.label} not skipped`)
    assert.deepEqual([v.baseline_match, v.outputs_match, v.serial_wall_s, v.separate_wall_s, v.factor], [null, null, null, null, null])
    assert.deepEqual(v.batches.map(batch => [batch.skipped, batch.wall_s, batch.factor]), [[true, null, null], [true, null, null]])
    sampleRows(skipAll)
  })
  // a-1 ~2 s (4 x 0.5 s), b-1 ~4 s (4 x (0.5 + 0.5) s), 0.9 * 6 = 5.4:
  // b-1 fits (2 <= 5.4 - ~2.1), c2-1 does not (2 > 5.4 - ~6.1).
  const skipC = await probeUnits('budget-skips-c', { costs: [0.1, 0.2, 0.3, 0.4], budget: 6,
    env: { UNIT_SLEEP: '0.5', EXTRA_SLEEP: 'b-1-*:0.5' } })
  check('budget-skips-c: a-1 and b-1 run; c2-1 and every later arm skipped; outcome skipped', () => {
    written(skipC)
    const v = skipC.value
    assert.deepEqual(v.arms.map(arm => [arm.label, arm.skipped, ran(arm)]),
      ARMS.map((label, i) => [label, i >= 2, i < 2]))
    assert.equal(v.outcome, 'skipped')
    assert.equal(v.baseline_match, true)
    assert.equal(v.outputs_match, true)
    close(v.serial_wall_s, armOf(v, 'a-1').wall_s, 'serial_wall_s')
    close(v.separate_wall_s, armOf(v, 'b-1').wall_s, 'separate_wall_s')
    assert.deepEqual(v.batches.map(batch => [batch.skipped, batch.all_ok, batch.wall_s, batch.factor]), [[true, false, null, null], [true, false, null, null]])
    assert.equal(v.factor, null)
    assertInvocations(skipC)
  })
  // a-1 ~1.6 s, c4-1 invocations sleep 6 s, 0.9 * 9 = 8.1: c4-1 fits (~2.1 s elapsed), c4-2 does not (~8.1 s elapsed).
  const skipLate = await probeUnits('budget-skips-late', { costs: [0.1, 0.2, 0.3, 0.4], budget: 9,
    env: { UNIT_SLEEP: '0.02', EXTRA_SLEEP: 'a-1:1.5 c4-1-*:6' } })
  check('budget-skips-late: c4-2 and later skipped; measured with factors from a-1, c2-1 and c4-1', () => {
    written(skipLate)
    const v = skipLate.value
    assert.deepEqual(v.arms.map(arm => [arm.label, arm.skipped, ran(arm)]),
      ARMS.map((label, i) => [label, i >= 4, i < 4]))
    assert.equal(v.outcome, 'measured')
    close(v.serial_wall_s, armOf(v, 'a-1').wall_s, 'serial_wall_s')
    close(v.separate_wall_s, armOf(v, 'b-1').wall_s, 'separate_wall_s')
    close(v.batches[0].wall_s, armOf(v, 'c2-1').wall_s, 'n=2 wall_s')
    close(v.batches[1].wall_s, armOf(v, 'c4-1').wall_s, 'n=4 wall_s')
    for (const batch of v.batches) { assert.equal(batch.all_ok, true); close(batch.factor, v.serial_wall_s / batch.wall_s, `n=${batch.n} factor`, 1e-4) }
    assert.ok(v.batches[1].factor < 1, 'n=4 slower than serial by construction')
    close(v.factor, v.batches[0].factor, 'factor is the larger (n=2)', 1e-9)
    assertInvocations(skipLate)
  })

  // Exit 2 when the file cannot be written.
  const unwritable = await probeUnits('unwritable', { manifest: '{', args: ['--units', 'harness/run_units.sh', 'harness/units.json',
    'out/blocker/concurrency', '1000', 'profiler/units_reference.json'],
  prepare: run => fs.writeFileSync(path.join(run, 'out', 'blocker'), 'not a directory\n') })
  check('unwritable: exit 2 when concurrency.json cannot be written', () => {
    assert.equal(unwritable.status, 2, diagnostics(unwritable))
    assert.equal(fs.readFileSync(path.join(unwritable.run, 'out', 'blocker'), 'utf8'), 'not a directory\n')
  })
}

main().catch(error => { failures++; console.log(`FAIL test harness: ${error.stack}`) }).finally(() => {
  fs.rmSync(scratch, { recursive: true, force: true })
  console.log(`${checks} checks, ${failures} failures`)
  if (!failures) console.log('all checks passed')
  process.exitCode = failures ? 1 : 0
})
