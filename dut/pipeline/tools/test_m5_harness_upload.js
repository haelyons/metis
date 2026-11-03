#!/usr/bin/env node
'use strict'

// Black-box contract tests (U44). Do not inspect the pipeline or git diff.
// Contract: m5/SCHEMAS.md "A/harness/", the bullet beginning "Harness uploads (the initial upload of every
// harness script": each script is truncated (`: > harness/<name>`) and then appended in independently
// decodable base64 chunks of at most 24,576 characters; the lines are batched in order into boxrun commands
// below 32,768 characters, each beginning with `set -e` and `mkdir -p harness out`, each an `upload` with its
// own receipt under the setup budget. A failed batch ends the upload (later batches are not sent, no
// harness script runs) and fails like a failed upload (`infra`). Afterwards the uploaded files are
// byte-identical to the local ones; a harness small enough for one batch uploads in exactly one command.
// Usage: node tools/test_m5_harness_upload.js
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const assert = require('node:assert/strict')
const { spawn, spawnSync } = require('node:child_process')
const fixture = require('./test_m5_reproduce.js')
const ROOT = path.resolve(__dirname, '..')
const PROBE = 'harness-upload-probe-50317'
const LIMIT = 32768
const CHUNK = 24576
const LARGE = 300000
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
// At least LARGE bytes of varied content after an `exit 0`, so the script still runs: quotes, `$`,
// backslashes, backticks, newlines, UTF-8 text and raw non-ASCII (including invalid UTF-8 and NUL) bytes.
function payload(seed) {
  const parts = [Buffer.from('exit 0\n')]
  let state = seed >>> 0, size = 0
  const random = () => (state = (Math.imul(state, 1664525) + 1013904223) >>> 0)
  for (let line = 0; size < LARGE + 4096; line++) {
    const text = Buffer.from(`# ${line} 'single' "double" $HOME \${PATH} $(id) \`date\` \\ \\\\n %s %% λ ü 日本 — 🙂\n`)
    const raw = Buffer.alloc(64 + (random() % 96))
    for (let i = 0; i < raw.length; i++) raw[i] = random() & 0xff
    parts.push(text, raw, Buffer.from('\n'))
    size += text.length + raw.length + 1
  }
  return Buffer.concat(parts)
}
// SCHEMAS.md "A/harness/", "Optional unit files (U50)": run_units.sh and units.json. `large` gives a
// run_units.sh of over LARGE bytes (non-ASCII, NUL, invalid UTF-8) and a units.json over one chunk.
const UNIT_FILES = ['run_units.sh', 'units.json']
function unitFiles(size) {
  const units = Array.from({ length: size === 'large' ? 1500 : 4 }, (_, i) => ({ id: `u${i}`, outputs: [`units/u${i}.txt`], cost_s: 1 + i / 3 }))
  return {
    'run_units.sh': size === 'large' ? Buffer.concat([Buffer.from('#!/usr/bin/env bash\n# λ ü 日本 — 🙂\n'), payload(777)])
      : Buffer.from('#!/usr/bin/env bash\nset -eu\n# λ ü 日本 — 🙂\nfor id in "$@"; do mkdir -p out/units; printf "%s\\n" "$id" > "out/units/$id.txt"; done\n'),
    'units.json': Buffer.from(JSON.stringify({ units }, null, size === 'large' ? 2 : 0) + '\n'),
  }
}

// Fake agents: the reproduce suite's agents, then optionally a large setup.sh or an empty run_command.sh.
module.exports = {
  async run(options) {
    const result = await fixture.run(options)
    const config = JSON.parse(process.env.M5_REPRODUCE_CONFIG)
    const harness = path.join(process.env.M5_REPRODUCE_ROOT, 'agent', 'harness')
    if (result && (config.largeSetup ?? []).includes(options.title))
      fs.appendFileSync(path.join(harness, 'setup.sh'), payload(options.title === 'harness' ? 17 : 4242))
    if (result && options.title === 'harness' && config.emptyCommand) fs.writeFileSync(path.join(harness, 'run_command.sh'), '')
    // U50: optional unit files present in A/harness/ before the initial upload.
    if (result && options.title === 'harness' && config.units) for (const [file, bytes] of Object.entries(unitFiles(config.units)))
      fs.writeFileSync(path.join(harness, file), bytes)
    return result
  },
  exportSession: fixture.exportSession,
}
if (require.main !== module) return

// Wraps the scratch m5/boxrun.sh: records each call's argv, then runs the original unchanged. With
// M5_FAIL_HARNESS_UPLOAD=N, the Nth harness upload (an `upload` after the probe receipt) runs its command
// and then exits 7 on the fake box, so its receipt has a nonzero rc. The log keeps the original command.
const SHIM = `
const fs = require('node:fs'), path = require('node:path'), { spawnSync } = require('node:child_process')
const [self, ...args] = process.argv.slice(2)
const value = flag => { const i = args.indexOf(flag); return i >= 0 ? args[i + 1] : undefined }
const receipt = value('--receipt') ?? ''
const receipts = path.dirname(receipt)
const afterProbe = fs.existsSync(receipts) && fs.readdirSync(receipts).some(file => /^\\d{4}-probe\\.json$/.test(file))
const upload = /^\\d{4}-upload\\.json$/.test(path.basename(receipt))
fs.appendFileSync(process.env.M5_BOXRUN_LOG, JSON.stringify({ args, receipt: path.basename(receipt), harnessUpload: upload && afterProbe }) + '\\n')
const run = [...args]
if (upload && afterProbe && process.env.M5_FAIL_HARNESS_UPLOAD) {
  const counter = process.env.M5_BOXRUN_LOG + '.harness-uploads'
  const count = (fs.existsSync(counter) ? Number(fs.readFileSync(counter, 'utf8')) : 0) + 1
  fs.writeFileSync(counter, String(count))
  if (count === Number(process.env.M5_FAIL_HARNESS_UPLOAD)) run[run.indexOf('--cmd') + 1] += '\\nexit 7'
}
const result = spawnSync('bash', [path.join(path.dirname(self), 'boxrun.orig.sh'), ...run], { stdio: 'inherit' })
process.exit(result.status ?? 1)
`

const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_harness_upload_'))
const pipeline = path.join(scratch, 'pipeline')
let checks = 0, failures = 0
function check(label, test) {
  checks++
  try { test(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${error.message}`) }
}

async function execute(name, config = {}) {
  const root = path.join(scratch, name)
  const agent = path.join(root, 'agent')
  const box = path.join(root, 'box')
  fs.mkdirSync(box, { recursive: true })
  fs.mkdirSync(path.join(root, 'home'), { recursive: true })
  json(path.join(root, 'control/args.json'), { run_root: root, tag: name,
    stub: { profile: 'PASS', seal: 'PASS', propose: 'PASS', implement: 'PASS', evaluate: 'PASS' } })
  const callsFile = path.join(root, 'calls.jsonl')
  const boxrunLog = path.join(root, 'boxrun.jsonl')
  const replaceProbe = path.join(root, 'replace-probe.js')
  const originalProbe = fs.readFileSync(path.join(ROOT, 'm5/box_probe.sh'), 'utf8')
  const fakeProbe = '#!/usr/bin/env bash\nset -eu\nmkdir -p out\nprintf \'{"label":"probe"}\\n\' >> "$M5_REPRODUCE_CALLS"\nprintf \'{"kernel":"' + PROBE + '","nvcc":[],"cmake":null}\\n\' > out/probe.json\n'
  fs.writeFileSync(replaceProbe, `
const fs = require('node:fs'), path = require('node:path')
// The job bin/box just started may remove entries meanwhile; vanished ones are skipped.
const boxWalk = require(${JSON.stringify(path.join(ROOT, 'tools/m5_box_walk.js'))})
function visit(directory) {
  for (const entry of boxWalk.entries(directory)) {
    const file = path.join(directory, entry.name)
    if (entry.isDirectory()) visit(file)
    else if (entry.isFile() && entry.name.endsWith('.sh') && boxWalk.text(file) === ${JSON.stringify(originalProbe)}) {
      fs.appendFileSync(process.env.M5_REPRODUCE_CALLS, '{"label":"probe-upload"}\\n')
      fs.writeFileSync(file, ${JSON.stringify(fakeProbe)})
    }
  }
}
visit(process.env.BOX_ROOT)
`)
  script(path.join(root, 'box-bin/nvidia-smi'), 'exit 1')
  script(path.join(root, 'bin/box'), 'command=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\nexport PATH="$BOX_ROOT/../box-bin:$PATH"\ncd -- "$BOX_ROOT"\nbash -c "$command"\n"$M5_TEST_NODE" "$M5_REPLACE_PROBE"\nif [[ $command == *timeout* ]]; then\n  for ((end=SECONDS+1800; SECONDS<end; )); do\n    pending=false\n    for file in "$BOX_ROOT"/m5-*/*.sh; do\n      [[ -f $file ]] || continue\n      [[ -f ${file%.sh}.rc ]] || pending=true\n    done\n    [[ $pending == true ]] || break\n    sleep 0.01\n  done\nfi')
  script(path.join(root, 'bin/fetch'), 'source=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\ncd -- "$BOX_ROOT"\nexec cp -r -- "$source" "$2"')
  const fixtureConfig = {
    anchors: [{ id: 'first', published_value: 100, tolerance: 1, quantity: 'fixture', source: 'fixture' },
      { id: 'second', published_value: 0, tolerance: 0, quantity: 'fixture', source: 'fixture' }],
    measured: { first: 100, second: 0 }, setupFailures: config.setupFailures ?? 0, anchorsFailures: 0,
    largeSetup: config.largeSetup ?? [], emptyCommand: Boolean(config.emptyCommand),
    ...(config.units ? { units: config.units } : {}),
  }
  const stderrFile = path.join(root, 'stderr.log')
  const stdout = fs.openSync(path.join(root, 'stdout.log'), 'w'), stderr = fs.openSync(stderrFile, 'w')
  let child
  const spawnedMs = Date.now()
  try {
    child = await new Promise(resolve => {
      const proc = spawn(process.execPath, [path.join(pipeline, 'idea/wf.js'), '--script', path.join(pipeline, 'm5/pipeline.js'),
        '--args', path.join(root, 'control/args.json'), '--out', path.join(agent, 'wf'), '--disable-family', 'claude'], {
        cwd: pipeline, timeout: 1800000, killSignal: 'SIGKILL', stdio: ['ignore', stdout, stderr],
        env: { ...process.env, HOME: path.join(root, 'home'), M5_RAIDS_LEDGER: path.join(scratch, 'raids.jsonl'),
          WF_STUB: __filename, M5_REPRODUCE_ROOT: root, M5_REPRODUCE_CONFIG: JSON.stringify(fixtureConfig),
          M5_REPRODUCE_CALLS: callsFile, M5_TEST_NODE: process.execPath, M5_REPLACE_PROBE: replaceProbe,
          M5_BOXRUN_LOG: boxrunLog, ...(config.failUpload ? { M5_FAIL_HARNESS_UPLOAD: String(config.failUpload) } : {}),
          BOX_ROOT: box, BOX: path.join(root, 'bin/box'), FETCH: path.join(root, 'bin/fetch') },
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
  const directory = path.join(root, 'control/receipts')
  const receipts = (fs.existsSync(directory) ? fs.readdirSync(directory) : []).filter(file => /^\d{4}-.*\.json$/.test(file)).sort()
    .map(file => ({ file, operation: file.slice(5, -5), ...read(path.join(directory, file)) }))
  const boxrun = rows(boxrunLog).map(row => ({ ...row, cmd: row.args[row.args.indexOf('--cmd') + 1] }))
  const signatures = rows(path.join(root, 'operator/signatures.jsonl'))
  const reproduce = signatures.find(row => row.signature.stage === 'reproduce')
  const remote = () => {
    const found = fs.readdirSync(box).filter(entry => entry.startsWith('m5-') && fs.existsSync(path.join(box, entry, 'harness')))
    assert.equal(found.length, 1, `expected one remote run directory: ${found}`)
    return path.join(box, found[0], 'harness')
  }
  // Where the run stopped, for failure messages (scratch is removed afterwards).
  const progress = () => JSON.stringify({ receipts: receipts.map(r => `${r.operation}:${r.rc}`),
    stages: signatures.map(({ signature: { stage, status, error_class } }) => `${stage}:${status}:${error_class ?? ''}`) })
  return { name, root, agent, receipts, boxrun, reproduce, remote, progress, spawnedMs }
}
// U47: no args.stage_budgets_s and no run_ceiling_s, so every (reproduce) command, harness uploads
// included, gets the time left before the default 12 h ceiling, resolved at its start.
const assertTimeLeft = run => fixture.assertTimeLeft(run.receipts, fixture.CEILING_DEFAULT, run.spawnedMs)

// Harness upload receipts between two indexes of the receipt list (after the probe run).
const probeAt = run => run.receipts.findIndex(receipt => receipt.operation === 'probe')
const setupAts = run => run.receipts.flatMap((receipt, i) => receipt.operation === 'setup' ? [i] : [])
// The boxrun calls whose receipt is one of `receipts`, in order.
function commandsFor(run, receipts) {
  const names = new Set(receipts.map(receipt => receipt.file))
  const calls = run.boxrun.filter(call => names.has(call.receipt))
  assert.equal(calls.length, receipts.length, `boxrun calls ${calls.map(c => c.receipt)} vs receipts ${[...names]}`)
  return calls.map(call => call.cmd)
}
// SCHEMAS.md: below 32,768 characters, beginning with `set -e` and then `mkdir -p harness out`;
// base64 chunks of at most 24,576 characters, each independently decodable.
function assertBatch(cmd, label) {
  assert.equal(typeof cmd, 'string', `${label}: no --cmd`)
  assert.ok(cmd.length < LIMIT, `${label}: --cmd has ${cmd.length} characters (limit ${LIMIT})`)
  assert.match(cmd, /^\s*set -e\s*(?:\n|;|&&)\s*mkdir -p harness out\s*(?:\n|;|&&|$)/, `${label}: begins ${JSON.stringify(cmd.slice(0, 80))}`)
  for (const chunk of cmd.match(/[A-Za-z0-9+/]{200,}={0,2}/g) ?? []) {
    assert.ok(chunk.length <= CHUNK, `${label}: base64 chunk of ${chunk.length} characters`)
    assert.equal(chunk.length % 4, 0, `${label}: base64 chunk not independently decodable`)
  }
}
// Executes the upload commands in order with bash in an empty temporary directory.
function replay(commands) {
  const directory = fs.mkdtempSync(path.join(scratch, 'replay-'))
  commands.forEach((cmd, i) => {
    const result = spawnSync('bash', ['-c', cmd], { cwd: directory, encoding: 'utf8', maxBuffer: 1 << 26 })
    assert.ifError(result.error)
    assert.equal(result.status, 0, `upload command ${i + 1} failed in replay: ${result.stderr.slice(-300)}`)
  })
  return path.join(directory, 'harness')
}
function assertSame(directory, local, files, label) {
  for (const file of files) {
    const expected = fs.readFileSync(path.join(local, file))
    const actual = path.join(directory, file)
    assert.ok(fs.existsSync(actual), `${label}: ${file} missing`)
    assert.ok(expected.equals(fs.readFileSync(actual)), `${label}: ${file} differs (${fs.statSync(actual).size} vs ${expected.length} bytes)`)
  }
}
const harnessFiles = run => fs.readdirSync(path.join(run.agent, 'harness')).filter(file => fs.statSync(path.join(run.agent, 'harness', file)).isFile()).sort()
const escape = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

// Checks 1-3: the initial upload reaches setup, chunked or in one command, byte-identical.
function initialUploadChecks(run, { large, empty }) {
  const { name } = run
  let uploads = []
  check(`${name}: reproduce PASS; ${large ? 'more than one' : 'exactly one'} upload receipt before the first setup`, () => {
    assert.equal(run.reproduce?.signature.status, 'PASS', run.progress())
    const probe = probeAt(run), setup = setupAts(run)[0]
    assert.ok(probe >= 0 && setup > probe, `probe ${probe}, first setup ${setup}: ${run.progress()}`)
    uploads = run.receipts.slice(probe + 1, setup)
    assert.ok(uploads.every(receipt => receipt.operation === 'upload'), run.progress())
    if (large) assert.ok(uploads.length > 1, `${uploads.length} upload receipt(s) for a setup.sh of over ${LARGE} bytes`)
    else assert.equal(uploads.length, 1, run.progress())
    for (const receipt of uploads) assert.deepEqual([receipt.rc, receipt.timed_out, receipt.fetched], [0, false, true], receipt.file)
    assertTimeLeft(run)
  })
  check(`${name}: every harness upload --cmd is below ${LIMIT} characters and begins with set -e, mkdir -p harness out`, () => {
    const commands = commandsFor(run, uploads)
    commands.forEach((cmd, i) => assertBatch(cmd, `${uploads[i].file}`))
    // Calls recorded as harness uploads equal those with receipts (no unreceipted batch).
    assert.equal(run.boxrun.filter(call => call.harnessUpload && call.receipt < run.receipts[setupAts(run)[0]].file).length, uploads.length)
    for (const file of harnessFiles(run)) assert.match(commands.join('\n'), new RegExp(`:\\s*>\\s*['"]?harness/${escape(file)}['"]?`), `${file}: never truncated`)
  })
  check(`${name}: replaying the upload commands with bash reproduces every harness file byte for byte`, () => {
    const local = path.join(run.agent, 'harness')
    if (large) assert.ok(fs.statSync(path.join(local, 'setup.sh')).size >= LARGE, 'fixture setup.sh is not large')
    if (empty) assert.equal(fs.statSync(path.join(local, 'run_command.sh')).size, 0, 'fixture run_command.sh is not empty')
    assertSame(replay(commandsFor(run, uploads)), local, harnessFiles(run), 'replay')
    assertSame(run.remote(), local, harnessFiles(run), 'box')
  })
  if (empty) check(`${name}: a zero-byte harness file uploads as an empty file`, () => {
    assert.equal(fs.statSync(path.join(run.remote(), 'run_command.sh')).size, 0)
    assert.equal(fs.statSync(path.join(replay(commandsFor(run, uploads)), 'run_command.sh')).size, 0)
  })
}

// Check 4: the second harness upload batch returns rc 7.
function failedBatchChecks(run) {
  const { name } = run
  check(`${name}: no upload or setup after the failed batch; reproduce FAIL infra, exit 2`, () => {
    const probe = probeAt(run)
    assert.ok(probe >= 0, run.progress())
    const after = run.receipts.slice(probe + 1)
    assert.deepEqual(after.map(receipt => `${receipt.operation}:${receipt.rc}`), ['upload:0', 'upload:7'], run.progress())
    assert.equal(run.boxrun.filter(call => call.harnessUpload).length, 2, 'harness upload batches sent after the failed one')
    assert.ok(!run.boxrun.some(call => /^\d{4}-(setup|anchors)\.json$/.test(call.receipt)), 'a harness script ran')
    assert.equal(run.reproduce?.signature.status, 'FAIL', run.progress())
    assert.equal(run.reproduce.signature.error_class, 'infra')
    assert.equal(run.reproduce.signature.exit_code, 2)
    assert.ok(!rows(path.join(run.root, 'calls.jsonl')).some(call => /repair/.test(call.label)), 'repair after a failed upload')
  })
  check(`${name}: the batches sent obey the batch rules`, () => {
    const probe = probeAt(run)
    const uploads = run.receipts.slice(probe + 1)
    commandsFor(run, uploads).forEach((cmd, i) => assertBatch(cmd, uploads[i].file))
  })
}

// Check 5: setup fails, the repair rewrites setup.sh to over LARGE bytes, the re-upload is chunked.
function repairUploadChecks(run) {
  const { name } = run
  let uploads = []
  check(`${name}: several upload receipts between the failed setup and its rerun; setup reruns and passes`, () => {
    assert.equal(run.reproduce?.signature.status, 'PASS', run.progress())
    const setups = setupAts(run)
    assert.deepEqual(setups.map(i => run.receipts[i].rc), [7, 0], run.progress())
    uploads = run.receipts.slice(setups[0] + 1, setups[1])
    assert.ok(uploads.length > 1 && uploads.every(receipt => receipt.operation === 'upload'), run.progress())
    for (const receipt of uploads) assert.deepEqual([receipt.rc, receipt.fetched], [0, true], receipt.file)
    // Setup attempts, the rerun and the re-upload batches: time left, non-increasing.
    assertTimeLeft(run)
  })
  check(`${name}: every re-upload --cmd is below ${LIMIT} characters and begins with set -e, mkdir -p harness out`, () => {
    const commands = commandsFor(run, uploads)
    commands.forEach((cmd, i) => assertBatch(cmd, uploads[i].file))
    assert.match(commands.join('\n'), /:\s*>\s*['"]?harness\/setup\.sh['"]?/, 'setup.sh never truncated')
  })
  check(`${name}: the re-uploaded setup.sh is byte-identical (replay and box)`, () => {
    const local = path.join(run.agent, 'harness')
    assert.ok(fs.statSync(path.join(local, 'setup.sh')).size >= LARGE, 'fixture repair did not write a large setup.sh')
    assertSame(replay(commandsFor(run, uploads)), local, ['setup.sh'], 'replay')
    assertSame(run.remote(), local, harnessFiles(run), 'box')
  })
}

// U50a: unit files are part of the initial upload (same encoding and batching) and never uploaded later;
// a harness without them uploads only the scripts. Run after initialUploadChecks / repairUploadChecks.
const mentions = (commands, file) => new RegExp(`harness/${escape(file)}\\b`).test(commands.join('\n'))
function unitUploadChecks(run, { units }) {
  const { name } = run
  const local = path.join(run.agent, 'harness')
  const setups = setupAts(run)
  const initial = () => run.receipts.slice(probeAt(run) + 1, setups[0])
  check(`${name}: initial upload ${units ? 'carries run_units.sh and units.json' : 'carries no unit files'}; replay yields exactly the local harness files`, () => {
    assert.ok(probeAt(run) >= 0 && setups.length > 0, run.progress())
    const commands = commandsFor(run, initial())
    if (units) {
      for (const [file, bytes] of Object.entries(unitFiles(units))) {
        assert.ok(bytes.equals(fs.readFileSync(path.join(local, file))), `${file}: fixture did not write it`)
        assert.match(commands.join('\n'), new RegExp(`:\\s*>\\s*['"]?harness/${escape(file)}['"]?`), `${file}: never truncated in the initial upload`)
      }
    } else for (const file of UNIT_FILES) {
      assert.equal(fs.existsSync(path.join(local, file)), false, `${file}: fixture wrote it`)
      assert.equal(mentions(commands, file), false, `${file}: named in an upload without unit files`)
    }
    initial().forEach((receipt, i) => {
      assert.deepEqual([receipt.operation, receipt.rc, receipt.fetched], ['upload', 0, true], receipt.file)
      assertBatch(commands[i], receipt.file)
    })
    // Large unit files alone need several batches; small ones fit the single batch (checked by initialUploadChecks).
    if (units === 'large') assert.ok(initial().length > 1, `${initial().length} upload receipt(s) for unit files over ${LARGE} bytes`)
    assertTimeLeft(run)
    const replayed = replay(commands)
    assert.deepEqual(fs.readdirSync(replayed).sort(), harnessFiles(run), 'replayed harness files')
    // After a setup repair the local setup.sh is the rewritten one; compare only files no repair changes.
    const unchanged = setups.length > 1 ? harnessFiles(run).filter(file => file !== 'setup.sh') : harnessFiles(run)
    assertSame(replayed, local, unchanged, 'replay')
    assertSame(run.remote(), local, harnessFiles(run), 'box')
    for (const file of units ? [] : UNIT_FILES) assert.equal(fs.existsSync(path.join(run.remote(), file)), false, `${file}: on the box`)
  })
  if (setups.length > 1) check(`${name}: no upload after the initial one names a unit file`, () => {
    const later = run.receipts.slice(setups[0] + 1).filter(receipt => receipt.operation === 'upload')
    assert.ok(later.length > 0, 'no re-upload after the repair')
    const commands = commandsFor(run, later)
    for (const file of UNIT_FILES) assert.equal(mentions(commands, file), false, `${file}: uploaded after the initial upload`)
  })
}

async function main() {
  try {
    // Copy the runtime without reading implementation text; all mutations stay in scratch.
    for (const directory of ['m5', 'idea', 'measure']) fs.cpSync(path.join(ROOT, directory), path.join(pipeline, directory), {
      recursive: true, filter: source => !['experiments', 'raids_used.jsonl'].includes(path.basename(source)),
    })
    const boxrun = path.join(pipeline, 'm5/boxrun.sh')
    fs.renameSync(boxrun, path.join(pipeline, 'm5/boxrun.orig.sh'))
    fs.writeFileSync(path.join(scratch, 'boxrun-shim.js'), SHIM)
    fs.writeFileSync(boxrun, `#!/usr/bin/env bash\nexec "$M5_TEST_NODE" ${JSON.stringify(path.join(scratch, 'boxrun-shim.js'))} "$0" "$@"\n`, { mode: 0o755 })
    const large = await execute('large', { largeSetup: ['harness'] })
    initialUploadChecks(large, { large: true })
    unitUploadChecks(large, { units: null })
    const small = await execute('small')
    initialUploadChecks(small, { large: false })
    unitUploadChecks(small, { units: null })
    // U50a: unit files in A/harness/ join the initial upload: one batch when small, chunked when large.
    const unitsSmall = await execute('units-small', { units: 'small' })
    initialUploadChecks(unitsSmall, { large: false })
    unitUploadChecks(unitsSmall, { units: 'small' })
    // (initialUploadChecks' large mode expects a large setup.sh; unitUploadChecks checks these batches.)
    unitUploadChecks(await execute('units-large', { units: 'large' }), { units: 'large' })
    const unitsRepair = await execute('units-repair-reupload', { units: 'small', setupFailures: 1, largeSetup: ['harness-repair'] })
    repairUploadChecks(unitsRepair)
    unitUploadChecks(unitsRepair, { units: 'small' })
    initialUploadChecks(await execute('empty-file', { emptyCommand: true }), { large: false, empty: true })
    failedBatchChecks(await execute('failed-middle-batch', { largeSetup: ['harness'], failUpload: 2 }))
    repairUploadChecks(await execute('repair-reupload', { setupFailures: 1, largeSetup: ['harness-repair'] }))
  } catch (error) { failures++; console.log(`FAIL test harness: ${error.stack}`) }
  finally { fs.rmSync(scratch, { recursive: true, force: true }) }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : 'all checks passed')
  process.exitCode = failures ? 1 : 0
}
main()
