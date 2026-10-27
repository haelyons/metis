#!/usr/bin/env node
'use strict'

// Black-box tests of m5/concurrency_probe.py from m5/SCHEMAS.md "Concurrency probe".
// The probe is copied and executed locally (python3 -I), never read.
// Usage: node tools/test_m5_concurrency.js
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const assert = require('node:assert/strict')
const { spawn, spawnSync } = require('node:child_process')
const { assertConcurrencyShape } = require('./m5_profile_fixture.js')
const ROOT = path.resolve(__dirname, '..')
const LABELS = ['single-1', 'single-2', 'single-3', 'n2-1', 'n2-2', 'n4-1', 'n4-2', 'n4-3', 'n4-4']
const BATCH_LABELS = { 2: ['n2-1', 'n2-2'], 4: ['n4-1', 'n4-2', 'n4-3', 'n4-4'] }
// Top-level entries each invocation must see as symlinks (out, profiler, concurrency-work, evaluation-work excluded).
const LINKED = ['.hidden', 'baseline-published', 'data', 'harness', 'top.txt']
const scratch = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_concurrency_')))
let checks = 0, failures = 0
function check(name, run) {
  checks++
  try { run(); console.log(`ok ${name}`) }
  catch (error) { failures++; console.log(`FAIL ${name}: ${error.message}`) }
}
function script(file, body) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, '#!/usr/bin/env bash\n' + body + '\n', { mode: 0o755 })
}
const median = values => [...values].sort((a, b) => a - b)[Math.floor(values.length / 2)]

// Restricted PATH: no host nvidia-cuda-mps-control unless a test adds a fake.
const tools = path.join(scratch, 'tools')
fs.mkdirSync(tools)
for (const tool of ['bash', 'sh', 'env', 'python3', 'sleep', 'cat', 'ls', 'date', 'readlink', 'basename', 'dirname',
  'mkdir', 'rm', 'rmdir', 'chmod', 'cp', 'mv', 'ln', 'touch', 'true', 'false', 'mktemp', 'uname', 'id', 'tee', 'head', 'tail', 'grep', 'sed', 'awk']) {
  const found = spawnSync('/bin/bash', ['-c', 'command -v "$1"', 'locate', tool], { encoding: 'utf8' })
  if (found.status === 0 && found.stdout.trim().startsWith('/')) fs.symlinkSync(found.stdout.trim(), path.join(tools, tool))
}

// Fake published command: records what it saw, sleeps a known time per label.
const RUN_COMMAND = `set -u
label=$(basename "$PWD")
record="$RECORDS/$label.$$"
{
  printf 'label=%s\\npwd=%s\\nstart=%s\\n' "$label" "$(pwd -P)" "$(date +%s.%N)"
  printf 'pipe=%s\\nlog=%s\\nenv=%s\\n' "\${CUDA_MPS_PIPE_DIRECTORY-<unset>}" "\${CUDA_MPS_LOG_DIRECTORY-<unset>}" "\${FIXTURE_ENV-<unset>}"
  if [ -d out ] && [ ! -L out ] && [ -z "$(ls -A out)" ]; then printf 'outempty=yes\\n'; else printf 'outempty=no\\n'; fi
  shopt -s dotglob nullglob
  for entry in *; do
    if [ -L "$entry" ]; then printf 'link=%s=%s\\n' "$entry" "$(readlink -f "$entry")"
    elif [ -d "$entry" ]; then printf 'dir=%s\\n' "$entry"
    else printf 'file=%s\\n' "$entry"; fi
  done
} > "$record"
echo "stdout $label"
echo "stderr $label" >&2
printf '%s\\n' "$label" > out/result.txt
case "$label" in
  single-*) seconds=$SINGLE_S ;;
  n2-1) seconds=0.3 ;; n2-2) seconds=0.6 ;;
  n4-1) seconds=0.2 ;; n4-2) seconds=0.4 ;; n4-3) seconds=0.6 ;; n4-4) seconds=0.8 ;;
  *) seconds=0 ;;
esac
sleep "$seconds"
rc=0
for failing in \${FAIL_LABELS-}; do [ "$failing" = "$label" ] && rc=3; done
if [ "\${FAIL_UNDER_MPS-}" = "$label" ] && [ -n "\${CUDA_MPS_PIPE_DIRECTORY-}" ]; then rc=4; fi
printf 'end=%s\\nrc=%s\\n' "$(date +%s.%N)" "$rc" >> "$record"
exit "$rc"`
// Fake CUDA client, run at the start of every copy (after the record of inherited variables).
// MPS_PIPE_OVERRIDE models harness commands that unset, override or clear CUDA_MPS_* variables.
// A copy connects only through the daemon's pipe directory; a connection appends one
// `NEW CLIENT <pid> from user <uid>` line (plus CLIENT_EXTRA lines) to the daemon's control.log.
const CLIENT = `case "\${MPS_PIPE_OVERRIDE-}" in
  unset) unset CUDA_MPS_PIPE_DIRECTORY ;;
  other) mkdir -p out/other-pipe; export CUDA_MPS_PIPE_DIRECTORY="$PWD/out/other-pipe" ;;
  clear-all) for name in $(compgen -e); do case "$name" in CUDA_MPS_*) unset "$name" ;; esac; done ;;
esac
connected=none
if [ -n "\${CUDA_MPS_PIPE_DIRECTORY-}" ] && [ -f "$CUDA_MPS_PIPE_DIRECTORY/control" ]; then
  daemon_log="$(cat "$CUDA_MPS_PIPE_DIRECTORY/control")/control.log"
  skip=no
  for skipped in \${CLIENT_SKIP-}; do [ "$skipped" = "$label" ] && skip=yes; done
  if [ "$skip" = no ] && [ -f "$daemon_log" ] && [ -w "$daemon_log" ]; then
    uid=$(id -u)
    case "\${CLIENT_FORM-ok}" in
      lower) line="new client $$ from user $uid" ;;
      nopid) line="NEW CLIENT unknown from user $uid" ;;
      nofrom) line="NEW CLIENT $$ by user $uid" ;;
      *) line="NEW CLIENT $$ from user $uid" ;;
    esac
    extra=0
    for item in \${CLIENT_EXTRA-}; do [ "\${item%%:*}" = "$label" ] && extra="\${item#*:}"; done
    for ((i = 0; i <= extra; i++)); do
      printf '[2026-10-27 12:00:00.000 Control 4242] %s: Server already exists %s\\n' "$line" "$LOG_MARKER" >> "$daemon_log"
    done
    connected=yes
  fi
fi
printf 'client=%s\\n' "$connected" >> "$record"
`
const RUN_COMMAND_WITH_CLIENT = RUN_COMMAND.replace('echo "stdout $label"', match => CLIENT + match)
// Fake daemon: -d writes control.log in CUDA_MPS_LOG_DIRECTORY and a control endpoint in
// CUDA_MPS_PIPE_DIRECTORY naming that log directory; quit removes the endpoint.
// Modes: ok, fail-start, no-log (control.log never written), unreadable-log.
const MPS_CONTROL = `state="\${CUDA_MPS_PIPE_DIRECTORY-<unset>} \${CUDA_MPS_LOG_DIRECTORY-<unset>}"
if [ "$#" -gt 0 ]; then
  printf 'start %s %s %s\\n' "$(date +%s.%N)" "$*" "$state" >> "$MPS_LOG"
  [ "$MPS_MODE" = fail-start ] && exit 1
  if [ -n "\${CUDA_MPS_PIPE_DIRECTORY-}" ] && [ -n "\${CUDA_MPS_LOG_DIRECTORY-}" ]; then
    mkdir -p "$CUDA_MPS_PIPE_DIRECTORY" "$CUDA_MPS_LOG_DIRECTORY"
    case "$MPS_MODE" in
      no-log) ;;
      unreadable-log)
        if [ "$(id -u)" = 0 ]; then mkdir -p "$CUDA_MPS_LOG_DIRECTORY/control.log"
        else : > "$CUDA_MPS_LOG_DIRECTORY/control.log"; chmod 000 "$CUDA_MPS_LOG_DIRECTORY/control.log"; fi ;;
      *) printf '[2026-10-27 12:00:00.000 Control 4242] Starting control daemon %s\\n' "$LOG_MARKER" >> "$CUDA_MPS_LOG_DIRECTORY/control.log" ;;
    esac
    printf '%s\\n' "$CUDA_MPS_LOG_DIRECTORY" > "$CUDA_MPS_PIPE_DIRECTORY/control"
  fi
  exit 0
fi
input=$(cat)
printf 'stdin %s %s %s\\n' "$(date +%s.%N)" "$input" "$state" >> "$MPS_LOG"
if [ "$input" = quit ] && [ -n "\${CUDA_MPS_PIPE_DIRECTORY-}" ]; then rm -f "$CUDA_MPS_PIPE_DIRECTORY/control"; fi`
// Distinctive text in every control.log line; it must never reach concurrency.json.
const LOG_MARKER = 'MPS_LOG_PRIVATE_MARKER_550912'

function setupRun(name) {
  const run = path.join(scratch, name)
  script(path.join(run, 'harness', 'run_command.sh'), RUN_COMMAND_WITH_CLIENT)
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
  // Invocation records live outside the run directory so they are not linked.
  fs.mkdirSync(path.join(scratch, `${name}-records`))
  return run
}
function parseRecord(file) {
  const record = { links: {}, dirs: [], files: [] }
  for (const line of fs.readFileSync(file, 'utf8').split('\n').filter(Boolean)) {
    const [key, ...rest] = line.split('='), value = rest.join('=')
    if (key === 'link') { const [entry, ...target] = value.split('='); record.links[entry] = target.join('=') }
    else if (key === 'dir') record.dirs.push(value)
    else if (key === 'file') record.files.push(value)
    else record[key] = ['start', 'end', 'rc'].includes(key) ? Number(value) : value
  }
  return record
}
async function probe(name, { budget = 100, env = {}, mps = null, outDir = 'out/concurrency', prepare, terminateOnFirstRecord = false } = {}) {
  const run = setupRun(name)
  if (prepare) prepare(run)
  let PATH = tools
  const mpsLog = path.join(scratch, `${name}-mps.log`)
  if (mps) {
    const bin = path.join(scratch, `${name}-mps-bin`)
    script(path.join(bin, 'nvidia-cuda-mps-control'), MPS_CONTROL)
    PATH = `${bin}:${tools}`
  }
  const records = path.join(scratch, `${name}-records`)
  const result = await new Promise(resolve => {
    const child = spawn(path.join(tools, 'python3'), ['-I', 'profiler/concurrency_probe.py', 'harness/run_command.sh', outDir, String(budget)], {
      cwd: run, timeout: 60000, killSignal: 'SIGKILL',
      env: { PATH, HOME: scratch, TMPDIR: scratch, LANG: 'C.UTF-8', RECORDS: records, FIXTURE_ENV: 'preserved',
        SINGLE_S: '0.4', MPS_LOG: mpsLog, MPS_MODE: mps || '', LOG_MARKER, ...env },
    })
    let stdout = '', stderr = '', error
    child.stdout.on('data', data => { stdout += data })
    child.stderr.on('data', data => { stderr += data })
    child.on('error', value => { error = value })
    child.on('close', (status, signal) => resolve({ status, signal, stdout, stderr, error }))
    if (terminateOnFirstRecord) {
      const poll = setInterval(() => {
        if (fs.readdirSync(records).length) { clearInterval(poll); setTimeout(() => child.kill('SIGTERM'), 300) }
      }, 50)
      child.on('close', () => clearInterval(poll))
    }
  })
  assert.ifError(result.error)
  // Allow stray fake commands to finish recording before inspection.
  await new Promise(resolve => setTimeout(resolve, terminateOnFirstRecord ? 6000 : 100))
  const invocations = fs.readdirSync(records).map(file => parseRecord(path.join(records, file))).sort((a, b) => a.start - b.start)
  const output = path.join(run, 'out', 'concurrency', 'concurrency.json')
  return { ...result, run, invocations, output, value: fs.existsSync(output) ? JSON.parse(fs.readFileSync(output, 'utf8')) : undefined,
    mpsLog: fs.existsSync(mpsLog) ? fs.readFileSync(mpsLog, 'utf8').split('\n').filter(Boolean).map(line => {
      const [kind, time, ...rest] = line.split(' ')
      return { kind, time: Number(time), words: rest }
    }) : [] }
}
const diagnostics = result => `exit ${result.status}/${result.signal}; ${result.stderr.slice(-800)}`
// Fake daemon state left under concurrency-work/ (control.log contents), for failure messages.
function daemonState(result) {
  const found = []
  const visit = directory => {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const file = path.join(directory, entry.name)
      if (entry.isDirectory() && !['out', 'baseline-published', 'data', 'harness'].includes(entry.name)) visit(file)
      else if (entry.name === 'control.log' || entry.name === 'control') found.push(`${path.relative(result.run, file)}: ${fs.readFileSync(file, 'utf8').trim()}`)
    }
  }
  try { visit(path.join(result.run, 'concurrency-work')) } catch (error) { found.push(error.message) }
  return found.join(' | ') || 'no daemon files'
}
function written(result) {
  assert.equal(result.status, 0, diagnostics(result))
  assert.ok(result.value !== undefined, 'concurrency.json missing')
  assertConcurrencyShape(result.value)
}
// factor_n = n * T1 / wall_n for every counted batch; overall factor is the largest.
function arithmetic(value) {
  const singles = value.single_wall_s
  const counted = value.batches.filter(batch => batch.factor !== null)
  for (const batch of counted) {
    assert.ok(singles.every(wall => wall !== null), 'counted batch with failed single')
    assert.equal(batch.all_ok, true)
    assert.equal(batch.skipped, false)
    const expected = batch.n * median(singles) / batch.wall_s
    assert.ok(Math.abs(batch.factor - expected) <= 1e-6 * expected, `factor_${batch.n}: ${batch.factor} != ${expected}`)
  }
  for (const batch of value.batches) if (!batch.all_ok || batch.skipped) assert.equal(batch.factor, null, `uncounted batch ${batch.n} has factor`)
  assert.equal(value.factor, counted.length ? Math.max(...counted.map(batch => batch.factor)) : null)
}
function labelsOf(invocations) { return invocations.map(row => row.label) }
function workspace(result, invocations) {
  const base = path.join(result.run, 'concurrency-work')
  for (const row of invocations) {
    assert.equal(row.pwd, path.join(base, row.label), `${row.label}: working directory`)
    assert.equal(row.outempty, 'yes', `${row.label}: out/ must start empty`)
    assert.deepEqual(row.dirs, ['out'], `${row.label}: only out/ is a real directory`)
    assert.deepEqual(row.files, [], `${row.label}: unexpected regular files`)
    assert.deepEqual(Object.keys(row.links).sort(), LINKED, `${row.label}: symlinked entries`)
    for (const entry of LINKED) assert.equal(row.links[entry], path.join(result.run, entry), `${row.label}: ${entry} target`)
    assert.equal(row.env, 'preserved', `${row.label}: environment not inherited`)
  }
}
// Unverified MPS: treated like an invocation failure under MPS. Every MPS-phase copy exited 0, so
// the fallback can only come from verification. failsAt is the label (or batch) left unverified.
function fellBack(result, failsAt) {
  written(result)
  assert.equal(result.value.mps, false, 'mps recorded true without verified connections')
  assert.equal(result.value.mps_failed, true)
  const starts = result.mpsLog.filter(row => row.kind === 'start')
  const quits = result.mpsLog.filter(row => row.kind === 'stdin' && row.words[0] === 'quit')
  assert.equal(starts.length, 1, 'one daemon start (the rerun runs without MPS)')
  assert.ok(quits.length >= 1, 'daemon never stopped')
  assert.ok(quits.at(-1).time >= starts[0].time, 'daemon left running')
  const underMps = result.invocations.filter(row => row.pipe !== '<unset>')
  const plain = result.invocations.filter(row => row.pipe === '<unset>')
  const expected = BATCH_LABELS[{ n2: 2, n4: 4 }[failsAt]] ?? [failsAt]
  for (const label of expected) assert.ok(underMps.some(row => row.label === label), `${label} did not run under MPS`)
  assert.ok(underMps.every(row => row.rc === 0), 'an MPS-phase copy failed; fallback not due to verification')
  assert.deepEqual([...labelsOf(plain)].sort(), [...LABELS].sort(), 'exactly one complete rerun without MPS')
  assert.ok(plain.every(row => row.client === 'none' && row.log === '<unset>'), 'rerun copies saw MPS')
  const quit = quits.find(row => row.time >= Math.max(...underMps.map(row => row.end)))
  assert.ok(quit, 'daemon not stopped after the unverified run')
  assert.ok(quit.time <= Math.min(...plain.map(row => row.start)), 'daemon stopped after the rerun began')
  workspace(result, plain)
  assert.ok(result.value.single_wall_s.every(wall => wall > 0))
  assert.ok(result.value.batches.every(batch => batch.all_ok && !batch.skipped))
  assert.ok(result.value.factor > 0)
  arithmetic(result.value)
}
// No log content (pids, uids, paths, line text) enters concurrency.json; its key set is exact.
function noLogContent(result) {
  written(result)
  const text = fs.readFileSync(result.output, 'utf8')
  for (const fragment of [LOG_MARKER, 'NEW CLIENT', 'new client', 'from user', 'control', 'Control', 'Server', scratch, 'concurrency-work'])
    assert.ok(!text.includes(fragment), `log content in concurrency.json: ${fragment}`)
}

// Regression with the recorded public run positive-openmm/run1: its run_command.sh clears
// CUDA_MPS_* before running its command, yet its concurrency.json recorded mps true. The recorded
// files are copied into scratch (never written in experiments/); the probe runs a command with the
// same behaviour (all CUDA_MPS_* cleared) and a fake workload in place of the real one.
const RECORDED = path.resolve(ROOT, '..', '..', 'experiments', 'positive-openmm', 'run1', 'agent')
async function recordedHarnessRegression() {
  const copy = path.join(scratch, 'recorded-positive-openmm-run1')
  fs.mkdirSync(copy)
  let recorded
  check('recorded positive-openmm run1: copied harness clears CUDA_MPS_*; recorded concurrency mps=true', () => {
    fs.copyFileSync(path.join(RECORDED, 'harness', 'run_command.sh'), path.join(copy, 'run_command.sh'))
    fs.copyFileSync(path.join(RECORDED, 'results', 'profile', 'out', 'concurrency', 'concurrency.json'), path.join(copy, 'concurrency.json'))
    assert.match(fs.readFileSync(path.join(copy, 'run_command.sh'), 'utf8'), /CUDA_MPS_/, 'recorded harness does not touch CUDA_MPS_*')
    recorded = JSON.parse(fs.readFileSync(path.join(copy, 'concurrency.json'), 'utf8'))
    assertConcurrencyShape(recorded)
    assert.equal(recorded.mps, true)
  })
  const result = await probe('recorded-harness-behaviour', { mps: 'ok', env: { MPS_PIPE_OVERRIDE: 'clear-all' } })
  check('recorded harness behaviour: probe records mps=false, mps_failed=true (recorded run said mps=true)', () => {
    fellBack(result, 'single-1')
    assert.ok(recorded, 'recorded concurrency.json unavailable')
    assert.notEqual(result.value.mps, recorded.mps)
  })
}

async function main() {
  const basic = await probe('basic')
  check('basic: exits 0 and writes the exact shape', () => written(basic))
  check('basic: no MPS binary means mps=false, mps_failed=false, no MPS variables', () => {
    assert.equal(basic.value.mps, false)
    assert.equal(basic.value.mps_failed, false)
    for (const row of basic.invocations) assert.deepEqual([row.pipe, row.log], ['<unset>', '<unset>'], row.label)
  })
  check('basic: three singles then n=2 then n=4, each label once', () => {
    assert.deepEqual([...labelsOf(basic.invocations)].sort(), [...LABELS].sort())
    const at = label => basic.invocations.find(row => row.label === label)
    for (const [before, after] of [['single-1', 'single-2'], ['single-2', 'single-3']])
      assert.ok(at(before).end <= at(after).start, `${before} must finish before ${after} starts`)
    for (const label of BATCH_LABELS[2]) assert.ok(at('single-3').end <= at(label).start, `${label} before singles finished`)
    for (const label of BATCH_LABELS[4]) for (const prior of BATCH_LABELS[2]) assert.ok(at(prior).end <= at(label).start, `${label} overlapped n=2`)
    for (const n of [2, 4]) {
      const rows = BATCH_LABELS[n].map(at)
      assert.ok(Math.max(...rows.map(row => row.start)) < Math.min(...rows.map(row => row.end)), `n=${n} copies not started together`)
    }
    assert.deepEqual(basic.value.batches.map(batch => batch.n), [2, 4])
  })
  check('basic: walls, batch wall to last exit, factor arithmetic', () => {
    const { single_wall_s: singles, batches } = basic.value
    for (const wall of singles) assert.ok(wall >= 0.4 && wall < 1.5, `single wall ${wall}`)
    assert.ok(batches[0].wall_s >= 0.6 && batches[0].wall_s < 0.85, `n=2 wall ${batches[0].wall_s} (serial would be 0.9)`)
    assert.ok(batches[1].wall_s >= 0.8 && batches[1].wall_s < 1.5, `n=4 wall ${batches[1].wall_s} (serial would be 2.0)`)
    for (const batch of batches) { assert.equal(batch.all_ok, true); assert.equal(batch.skipped, false) }
    arithmetic(basic.value)
    // Independent estimate from the commands' own clocks, within tolerance.
    const at = label => basic.invocations.find(row => row.label === label)
    const t1 = median(['single-1', 'single-2', 'single-3'].map(label => at(label).end - at(label).start))
    for (const batch of batches) {
      const rows = BATCH_LABELS[batch.n].map(at)
      const estimate = batch.n * t1 / (Math.max(...rows.map(row => row.end)) - Math.min(...rows.map(row => row.start)))
      assert.ok(Math.abs(batch.factor - estimate) <= 0.3 * estimate, `factor_${batch.n} ${batch.factor} vs measured ${estimate}`)
    }
  })
  check('basic: fresh concurrency-work/<label>/ with empty out/ and links to top-level entries', () => workspace(basic, basic.invocations))
  check('basic: per-label logs capture stdout and stderr; shared out/ untouched by invocations', () => {
    for (const label of LABELS) {
      const log = fs.readFileSync(path.join(basic.run, 'out', 'concurrency', 'logs', `${label}.log`), 'utf8')
      assert.match(log, new RegExp(`stdout ${label}`))
      assert.match(log, new RegExp(`stderr ${label}`))
    }
    assert.equal(fs.readFileSync(path.join(basic.run, 'out', 'keep.txt'), 'utf8'), 'shared\n')
    assert.ok(!fs.existsSync(path.join(basic.run, 'out', 'result.txt')), 'invocation wrote into shared out/')
  })

  const singleFails = await probe('single-fails', { env: { FAIL_LABELS: 'single-2' } })
  check('single-fails: stops after the failing single with null factor, exit 0', () => {
    written(singleFails)
    assert.deepEqual(labelsOf(singleFails.invocations), ['single-1', 'single-2'])
    const { single_wall_s: singles, batches } = singleFails.value
    assert.ok(singles[0] > 0)
    assert.deepEqual(singles.slice(1), [null, null])
    for (const batch of batches) { assert.equal(batch.wall_s, null); assert.equal(batch.factor, null) }
    assert.equal(singleFails.value.factor, null)
  })
  const firstFails = await probe('first-single-fails', { env: { FAIL_LABELS: 'single-1' } })
  check('first-single-fails: all singles null, factor null', () => {
    written(firstFails)
    assert.deepEqual(labelsOf(firstFails.invocations), ['single-1'])
    assert.deepEqual(firstFails.value.single_wall_s, [null, null, null])
    assert.equal(firstFails.value.factor, null)
  })
  const copyFails = await probe('batch-copy-fails', { env: { FAIL_LABELS: 'n4-2' } })
  check('batch-copy-fails: n=4 does not count; factor is factor_2', () => {
    written(copyFails)
    const [two, four] = copyFails.value.batches
    assert.equal(two.all_ok, true)
    assert.ok(two.factor > 0)
    assert.equal(four.all_ok, false)
    assert.equal(four.skipped, false)
    assert.equal(four.factor, null)
    assert.equal(copyFails.value.factor, two.factor)
    arithmetic(copyFails.value)
  })
  const bothFail = await probe('both-batches-fail', { env: { FAIL_LABELS: 'n2-1 n4-4' } })
  check('both-batches-fail: no counted batch gives null factor', () => {
    written(bothFail)
    assert.ok(bothFail.value.single_wall_s.every(wall => wall > 0))
    assert.deepEqual(bothFail.value.batches.map(batch => [batch.all_ok, batch.factor]), [[false, null], [false, null]])
    assert.equal(bothFail.value.factor, null)
  })
  // Skip when n * T1 > 0.9 * budget - elapsed. Singles 0.5 s: elapsed ~1.6 s before n=2, ~2.2 s before n=4.
  const skipFour = await probe('budget-skips-n4', { budget: 4, env: { SINGLE_S: '0.5' } })
  check('budget-skips-n4: n=2 runs (1.0 <= 3.6-1.6), n=4 skipped (2.0 > 3.6-2.2)', () => {
    written(skipFour)
    const [two, four] = skipFour.value.batches
    assert.equal(two.skipped, false)
    assert.equal(two.all_ok, true)
    assert.equal(four.skipped, true)
    assert.equal(four.wall_s, null)
    assert.equal(four.factor, null)
    assert.ok(!labelsOf(skipFour.invocations).some(label => label.startsWith('n4-')), 'skipped batch ran')
    assert.equal(skipFour.value.factor, two.factor)
    arithmetic(skipFour.value)
  })
  const skipBoth = await probe('budget-skips-both', { budget: 2, env: { SINGLE_S: '0.5' } })
  check('budget-skips-both: both batches skipped, factor null, exit 0', () => {
    written(skipBoth)
    assert.deepEqual(labelsOf(skipBoth.invocations), ['single-1', 'single-2', 'single-3'])
    assert.deepEqual(skipBoth.value.batches.map(batch => [batch.skipped, batch.wall_s, batch.factor]), [[true, null, null], [true, null, null]])
    assert.equal(skipBoth.value.factor, null)
  })

  const mps = await probe('mps', { mps: 'ok' })
  check('mps: daemon started before, stopped after, variables passed to every invocation', () => {
    written(mps)
    assert.equal(mps.value.mps, true, `MPS not recorded although every copy connected; ${diagnostics(mps)}; ${daemonState(mps)}`)
    assert.equal(mps.value.mps_failed, false)
    noLogContent(mps)
    const starts = mps.mpsLog.filter(row => row.kind === 'start'), quits = mps.mpsLog.filter(row => row.kind === 'stdin')
    assert.equal(starts.length, 1, 'one daemon start')
    const [flag, pipe, log] = starts[0].words
    assert.equal(flag, '-d')
    const work = path.join(mps.run, 'concurrency-work') + path.sep
    assert.ok(path.resolve(mps.run, pipe).startsWith(work), `pipe directory ${pipe} not under concurrency-work/`)
    assert.ok(path.resolve(mps.run, log).startsWith(work), `log directory ${log} not under concurrency-work/`)
    assert.notEqual(pipe, log)
    assert.ok(starts[0].time <= mps.invocations[0].start, 'daemon started after first invocation')
    assert.equal(mps.invocations.length, 9)
    for (const row of mps.invocations) assert.deepEqual([row.pipe, row.log], [pipe, log], row.label)
    assert.ok(quits.length >= 1, 'daemon never stopped')
    const last = quits.at(-1)
    assert.deepEqual(last.words, ['quit', pipe, log], 'quit must use the same variables')
    assert.ok(last.time >= Math.max(...mps.invocations.map(row => row.end)), 'daemon stopped before the last invocation ended')
    workspace(mps, mps.invocations)
    arithmetic(mps.value)
  })
  check('mps verified: every copy connected, no rerun, factor from the MPS measurements', () => {
    written(mps)
    assert.deepEqual(mps.invocations.map(row => [row.label, row.client]).sort(), LABELS.map(label => [label, 'yes']).sort())
    assert.ok(mps.invocations.every(row => row.pipe !== '<unset>'), 'rerun without MPS after verified runs')
    assert.ok(mps.value.single_wall_s.every(wall => wall > 0))
    assert.ok(mps.value.batches.every(batch => batch.all_ok && !batch.skipped && batch.factor > 0))
    assert.ok(mps.value.factor > 0)
    arithmetic(mps.value)
  })

  // SCHEMAS.md "MPS use is verified, not assumed": each case below runs every copy successfully
  // but leaves too few valid `NEW CLIENT <pid> from user <uid>` lines, so it must fall back.
  for (const [name, options, failsAt] of [
    ['unverified-command-unsets-pipe', { env: { MPS_PIPE_OVERRIDE: 'unset' } }, 'single-1'],
    ['unverified-command-overrides-pipe', { env: { MPS_PIPE_OVERRIDE: 'other' } }, 'single-1'],
    ['unverified-command-clears-all-mps', { env: { MPS_PIPE_OVERRIDE: 'clear-all' } }, 'single-1'],
    ['unverified-single-short', { env: { CLIENT_SKIP: 'single-2' } }, 'single-2'],
    // Growth is per run: earlier extra lines cannot cover a later copy that did not connect.
    ['unverified-single-short-after-extra', { env: { CLIENT_EXTRA: 'single-1:3', CLIENT_SKIP: 'single-2' } }, 'single-2'],
    ['unverified-n2-short', { env: { CLIENT_SKIP: 'n2-2' } }, 'n2'],
    ['unverified-n4-short', { env: { CLIENT_SKIP: 'n4-3' } }, 'n4'],
    ['unverified-log-missing', { mps: 'no-log' }, 'single-1'],
    ['unverified-log-unreadable', { mps: 'unreadable-log' }, 'single-1'],
    ['unverified-lowercase-lines', { env: { CLIENT_FORM: 'lower' } }, 'single-1'],
    ['unverified-no-integer-pid', { env: { CLIENT_FORM: 'nopid' } }, 'single-1'],
    ['unverified-no-from-user', { env: { CLIENT_FORM: 'nofrom' } }, 'single-1'],
  ]) {
    const result = await probe(name, { mps: 'ok', ...options })
    check(`${name}: mps=false, mps_failed=true, daemon stopped, one complete rerun without MPS`, () => fellBack(result, failsAt))
    check(`${name}: no log content in concurrency.json`, () => noLogContent(result))
  }
  const extra = await probe('verified-extra-lines', { mps: 'ok', env: { CLIENT_EXTRA: 'single-2:2 n2-1:1 n4-1:3 n4-4:1' } })
  check('verified-extra-lines: more than n new lines still verifies; no rerun', () => {
    written(extra)
    assert.equal(extra.value.mps, true, diagnostics(extra))
    assert.equal(extra.value.mps_failed, false)
    assert.deepEqual([...labelsOf(extra.invocations)].sort(), [...LABELS].sort())
    assert.ok(extra.invocations.every(row => row.pipe !== '<unset>' && row.client === 'yes'))
    assert.ok(extra.value.factor > 0)
    arithmetic(extra.value)
  })
  check('verified-extra-lines: no log content in concurrency.json', () => noLogContent(extra))
  await recordedHarnessRegression()
  const startFails = await probe('mps-start-fails', { mps: 'fail-start' })
  check('mps-start-fails: daemon stopped, probe repeated once without MPS, mps_failed=true', () => {
    written(startFails)
    assert.equal(startFails.value.mps, false)
    assert.equal(startFails.value.mps_failed, true)
    assert.ok(startFails.mpsLog.some(row => row.kind === 'stdin' && row.words[0] === 'quit'), 'failed daemon not stopped')
    assert.deepEqual([...labelsOf(startFails.invocations)].sort(), [...LABELS].sort())
    for (const row of startFails.invocations) assert.deepEqual([row.pipe, row.log], ['<unset>', '<unset>'], row.label)
    assert.ok(startFails.value.factor > 0)
    arithmetic(startFails.value)
  })
  const mpsInvocationFails = await probe('mps-invocation-fails', { mps: 'ok', env: { FAIL_UNDER_MPS: 'n2-1' } })
  check('mps-invocation-fails: stop daemon, one complete rerun without MPS in fresh directories', () => {
    written(mpsInvocationFails)
    assert.equal(mpsInvocationFails.value.mps, false)
    assert.equal(mpsInvocationFails.value.mps_failed, true)
    const underMps = mpsInvocationFails.invocations.filter(row => row.pipe !== '<unset>')
    const plain = mpsInvocationFails.invocations.filter(row => row.pipe === '<unset>')
    assert.ok(underMps.some(row => row.label === 'n2-1' && row.rc === 4), 'failing MPS invocation missing')
    assert.deepEqual([...labelsOf(plain)].sort(), [...LABELS].sort(), 'exactly one complete rerun without MPS')
    const quit = mpsInvocationFails.mpsLog.find(row => row.kind === 'stdin' && row.words[0] === 'quit')
    assert.ok(quit, 'daemon not stopped')
    assert.ok(quit.time <= Math.min(...plain.map(row => row.start)), 'daemon stopped after the rerun began')
    for (const row of plain) assert.equal(row.outempty, 'yes', `${row.label}: rerun reused a work directory`)
    assert.ok(mpsInvocationFails.value.single_wall_s.every(wall => wall > 0))
    assert.ok(mpsInvocationFails.value.batches.every(batch => batch.all_ok))
    arithmetic(mpsInvocationFails.value)
  })
  const terminated = await probe('sigterm', { mps: 'ok', env: { SINGLE_S: '3' }, terminateOnFirstRecord: true })
  check('sigterm: daemon stopped on SIGTERM', () => {
    assert.ok(terminated.mpsLog.some(row => row.kind === 'start'), 'daemon never started')
    assert.ok(terminated.mpsLog.some(row => row.kind === 'stdin' && row.words[0] === 'quit'), 'daemon left running after SIGTERM')
    assert.ok(terminated.invocations.length < 9, 'probe completed before SIGTERM')
  })
  const unwritable = await probe('unwritable', { outDir: 'out/blocker/concurrency',
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
