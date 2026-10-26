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
const { spawn } = require('node:child_process')
const { createHash, randomUUID } = require('node:crypto')
const ROOT = path.resolve(__dirname, '..')
const PRIVATE = 'IMPLEMENT_PRIVATE_SENTINEL_593771'
const TEST_SECRET = 'TEST_SOURCE_SENTINEL_174839'
const METHOD_SECRET = 'METHOD_SOURCE_SENTINEL_284950'
const CREDENTIAL = 'FAKE_AUTH_SENTINEL_395061'
const IDS = ['dropped_inputs', 'duplicated_inputs', 'ordering', 'tail_handling', 'seeds', 'equivalence']
const readJSON = file => JSON.parse(fs.readFileSync(file, 'utf8'))
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
return await agent('Run the local isolation probe.', {label:'probe', role:'ls-writer', model:'sonnet',
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
    if (title === 'harness') {
      const harness = path.join(agent, 'harness')
      script(path.join(harness, 'setup.sh'), `mkdir -p baseline-published data out
git init -q --separate-git-dir published-git baseline-published
printf 'published\\n' > baseline-published/pin
printf 'inputs\\n' > data/input`)
      script(path.join(harness, 'run_anchors.sh'), emit('out/anchors_measured.json', { anchor: 1 }) +
        emit('out/values.json', [0, 1, 2, 3, 4]) + emit('out/seeds.json', [0, 1, 2, 3, 4]))
      script(path.join(harness, 'profile.sh'), 'true')
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
      event.freeze = fs.existsSync(path.join(root, 'control', 'implement', 'tests.json'))
        ? readJSON(path.join(root, 'control', 'implement', 'tests.json')) : null
      event.frozenHash = event.freeze ? treeHash(path.join(agent, 'tests')) : null
      event.testBytesInPrompt = prompt.includes(TEST_SECRET)
      event.methodBytesInPrompt = prompt.includes(METHOD_SECRET)
      const prior = rows(path.join(root, 'calls.jsonl')).filter(call => call.title === title)
      if (title === 'tests') {
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
if (require.main !== module) return

const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_implement_'))
let checks = 0, failures = 0
function check(label, fn) {
  checks++
  try { fn(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${error.message}`) }
}
function fixture(root, config) {
  const agent = path.join(root, 'agent')
  writeJSON(path.join(agent, 'intake', 'anchors.json'), [{ id: 'anchor', quantity: 'sum', source: 'fixture', published_value: 1, tolerance: 0 }])
  for (const [name, value] of Object.entries({
    benchmark: { name: PRIVATE }, data: { available: true },
    baseline: { repo: 'fixture', pin: 'v1', build_commands: ['true'], run_commands: ['true'], published_configuration: { n: 5 } },
    EXECUTION: { representative_scale: { n: 5 }, inputs: ['data/input'], outputs: ['values.json'], timing_scope: 'whole run',
      timeout_s: 10, timeouts: { setup_method: 11, run_method: 12, run_tests: 13 } },
  })) writeJSON(path.join(agent, 'intake', name + '.json'), value)
  const predictions = { predictions: [{ method: 'batching', expected_speedup_interval: { low: 1.1, high: 1.2 },
    outcome_vs_compute_points: [1, 2, 4].map(compute_budget => ({ compute_budget, predicted_outcome: 1, uncertainty: 'exact' })) }],
    infeasible_methods: [], equivalence_metrics: ['exact equality'], paired_seed_tests: [0, 1, 2, 3, 4],
    sample_sizes: { n: 5 }, confidence_rule: 'paired 95% interval', hardware_cost_basis: 'same box', timing_scope: 'whole run',
    minimum_worthwhile_gain: 1.1, evaluation_inputs: ['fixture'], splits: { evaluation: [0, 5] }, compute_budgets: [1, 2, 4],
    repetitions: 5, warmup: 'one run', scheduling_order: 'alternate', equal_outcome_target: 1 }
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
async function execute(name, config = {}) {
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
  script(path.join(bin, 'box'), `command=\${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}
export PATH="$M5_IMPLEMENT_BIN:$PATH"
cd "$BOX_ROOT"
printf '%s\\n' "$command" >> "$M5_BOX_COMMANDS"
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
  script(path.join(bin, 'fetch'), 'source=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\n' +
    (config.fetchFailure ? '[[ $source != *-run-method.log ]] || exit 7\n' : '') + 'exec cp -r -- "$source" "$2"')
  const args = path.join(root, 'control', 'args.json')
  writeJSON(args, { run_root: root, raid: 'implement-test', tag: 'implement-test', stub: {
    intake: 'PASS', profile: 'PASS', seal: 'PASS', propose: 'PASS', evaluate: 'PASS', takeaways: 'PASS',
  } })
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
          M5_BOX_COMMANDS: path.join(root, 'box-commands'), BOX: path.join(bin, 'box'), FETCH: path.join(bin, 'fetch') } })
      let error
      proc.on('error', value => { error = value })
      proc.on('close', (status, signal) => resolve({ status, signal, error }))
    })
  } finally { fs.closeSync(stdout); fs.closeSync(stderr) }
  const records = rows(path.join(root, 'operator', 'signatures.jsonl'))
  const record = records.find(row => row.signature?.stage === 'implement')
  const calls = rows(path.join(root, 'calls.jsonl')).filter(call => ['tests', 'implement', 'review'].includes(call.title))
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
  check('payload hashes match final source, frozen tests, seal and script timeouts', () => {
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
    assert.deepEqual(payload.timeouts, { setup_method: 11, run_method: 12, run_tests: 13 })
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
async function main() {
  try {
    const happy = await execute('happy')
    verdict('happy', happy, null, { patch_applies: true, tests_pass: true, blind_tests: true, launch_review_pass: true })
    authorChecks(happy)
    receiptChecks(happy)
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
  finally {
    // Frozen trees require owner write permission before recursive cleanup.
    function writable(directory) {
      for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
        if (entry.isDirectory()) { const child = path.join(directory, entry.name); fs.chmodSync(child, 0o700); writable(child) }
      }
    }
    writable(scratch)
    fs.rmSync(scratch, { recursive: true, force: true })
  }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : 'all checks passed')
  process.exitCode = failures ? 1 : 0
}
main()
