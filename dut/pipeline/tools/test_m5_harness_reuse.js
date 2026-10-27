#!/usr/bin/env node
'use strict'

// Black-box contracts from m5/SCHEMAS.md. Never inspect pipeline.js or git diff.
// Usage: node tools/test_m5_harness_reuse.js
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const assert = require('node:assert/strict')
const { createHash } = require('node:crypto')
const { spawn } = require('node:child_process')
const fixture = require('./test_m5_reproduce.js')
const ROOT = path.resolve(__dirname, '..')
const PROBE = 'fresh-reuse-probe-72193'
const REQUIRED = ['setup.sh', 'run_anchors.sh', 'run_command.sh']
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const rows = file => fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : []
const sha = bytes => createHash('sha256').update(bytes).digest('hex')
function json(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, JSON.stringify(value) + '\n')
}
function script(file, body) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, '#!/usr/bin/env bash\nset -eu\n' + body + '\n', { mode: 0o700 })
}

module.exports = {
  async run(options) {
    if (['harness-repair', 'anchors-repair'].includes(options.title)) {
      const root = process.env.M5_REPRODUCE_ROOT
      // Capture the copied scripts before the fake repair changes anything.
      const harness = path.join(root, 'agent/harness')
      json(path.join(root, 'before-repair.json'), {
        files: Object.fromEntries(fs.readdirSync(harness).map(name => [name, sha(fs.readFileSync(path.join(harness, name)))])),
        source: read(path.join(root, 'control/harness_source.json')),
      })
    }
    return fixture.run(options)
  },
  exportSession: fixture.exportSession,
}
if (require.main !== module) return

const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_harness_reuse_'))
const pipeline = path.join(scratch, 'pipeline')
let checks = 0, failures = 0
function check(label, test) {
  checks++
  try { test(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${error.message}`) }
}

async function execute(name, config = {}) {
  const root = path.join(scratch, name)
  const source = path.join(root, 'previous run', 'A', 'harness')
  const agent = path.join(root, 'agent')
  script(path.join(source, 'setup.sh'), 'mkdir -p out baseline-published data\nprintf "published\\n" > baseline-published/pin\nprintf "input\\n" > data/input')
  script(path.join(source, 'run_command.sh'), 'test -f baseline-published/pin\ntest -f data/input\nprintf "command ran\\n" >> out/command-calls.log')
  script(path.join(source, 'run_anchors.sh'), 'bash harness/run_command.sh\nprintf \'{"first":100,"second":0}\\n\' > out/anchors_measured.json')
  if (config.optional !== false) script(path.join(source, 'run_evaluation.sh'), '# Optional adapter: preserve exact UTF-8 bytes: λ\ntrue')
  if (config.failure) script(path.join(source, config.failure === 'setup' ? 'setup.sh' : 'run_anchors.sh'),
    `mkdir -p out\nprintf 'reused ${config.failure} failed\\n'\nexit 7`)
  // Unrelated files must not enter the copy or provenance manifest.
  fs.writeFileSync(path.join(source, 'unrelated.txt'), 'do not copy\n')
  if (config.missing) fs.unlinkSync(path.join(source, config.missing))
  const originals = Object.fromEntries(fs.readdirSync(source).map(file => [file, fs.readFileSync(path.join(source, file))]))
  const args = { run_root: root, tag: name, stub: { profile: 'PASS', seal: 'PASS', propose: 'PASS', implement: 'PASS', evaluate: 'PASS' } }
  if (!config.generated) args.harness_from = config.relative ? path.relative(pipeline, source) : source
  json(path.join(root, 'control/args.json'), args)
  // A previous run's probe and measurements must not satisfy this run.
  json(path.join(root, 'previous run/A/results/probe/probe.json'), { kernel: 'stale-probe' })
  json(path.join(root, 'previous run/A/results/reproduce/out/anchors_measured.json'), { first: -999 })
  const box = path.join(root, 'box')
  fs.mkdirSync(box, { recursive: true })
  fs.mkdirSync(path.join(root, 'home'), { recursive: true })
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
  script(path.join(root, 'bin/box'), 'command=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\nexport PATH="$BOX_ROOT/../box-bin:$PATH"\ncd -- "$BOX_ROOT"\nbash -c "$command"\n"$M5_TEST_NODE" "$M5_REPLACE_PROBE"\nif [[ $command == *timeout* ]]; then\n  for ((i=0; i<1000; i++)); do\n    pending=false\n    for file in "$BOX_ROOT"/m5-*/*.sh; do\n      [[ -f $file ]] || continue\n      [[ -f ${file%.sh}.rc ]] || pending=true\n    done\n    [[ $pending == true ]] || break\n    sleep 0.01\n  done\nfi')
  script(path.join(root, 'bin/fetch'), 'source=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\ncd -- "$BOX_ROOT"\nexec cp -r -- "$source" "$2"')
  const fixtureConfig = {
    anchors: [{ id: 'first', published_value: 100, tolerance: 1, quantity: 'fixture', source: 'fixture' },
      { id: 'second', published_value: 0, tolerance: 0, quantity: 'fixture', source: 'fixture' }],
    measured: { first: 100, second: 0 },
    setupFailures: config.failure === 'setup' ? (config.exhausted ? 2 : 1) : 0,
    anchorsFailures: config.failure === 'anchors' ? (config.exhausted ? 2 : 1) : 0,
  }
  const stdoutFile = path.join(root, 'stdout.log'), stderrFile = path.join(root, 'stderr.log')
  const stdout = fs.openSync(stdoutFile, 'w'), stderr = fs.openSync(stderrFile, 'w')
  let child
  try {
    child = await new Promise(resolve => {
      const proc = spawn(process.execPath, [path.join(pipeline, 'idea/wf.js'), '--script', path.join(pipeline, 'm5/pipeline.js'),
        '--args', path.join(root, 'control/args.json'), '--out', path.join(agent, 'wf'), '--disable-family', 'claude'], {
        cwd: pipeline, timeout: 60000, stdio: ['ignore', stdout, stderr],
        env: { ...process.env, HOME: path.join(root, 'home'), M5_RAIDS_LEDGER: path.join(scratch, 'raids.jsonl'),
          WF_STUB: __filename, M5_REPRODUCE_ROOT: root, M5_REPRODUCE_CONFIG: JSON.stringify(fixtureConfig),
          M5_REPRODUCE_CALLS: callsFile, M5_TEST_NODE: process.execPath, M5_REPLACE_PROBE: replaceProbe,
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
  const calls = rows(callsFile)
  const records = rows(path.join(root, 'operator/signatures.jsonl')).map(row => ({ ...row.signature, facts: row.facts }))
  const reproduce = records.find(row => row.stage === 'reproduce')
  const failed = Boolean(config.missing || config.exhausted)
  check(`${name}: reproduce verdict and downstream gate`, () => {
    assert.equal(reproduce?.status, failed ? 'FAIL' : 'PASS')
    if (config.missing) assert.equal(reproduce.error_class, 'parse')
    if (config.exhausted) assert.equal(reproduce.error_class, config.failure === 'setup' ? 'install' : 'anchor')
    assert.equal(records.find(row => row.stage === 'profile')?.status, failed ? 'SKIPPED' : 'PASS')
    assert.equal(records.find(row => row.stage === 'takeaways')?.status, 'PASS')
  })
  check(`${name}: fresh probe runs once before authoring`, () => {
    assert.equal(calls.filter(call => call.label === 'probe-upload').length, 1)
    assert.equal(calls.filter(call => call.label === 'probe').length, 1)
    assert.equal(read(path.join(agent, 'results/probe/probe.json')).kernel, PROBE)
    for (const call of calls.filter(call => /harness|anchors-repair/.test(call.label))) {
      assert.ok(calls.indexOf(call) > calls.findIndex(row => row.label === 'probe'))
      assert.equal(call.probeFetched, true)
      assert.ok(call.prompt.includes(PROBE))
    }
  })
  check(`${name}: initial harness call and bounded repair`, () => {
    assert.equal(calls.filter(call => call.label === 'harness').length, config.generated ? 1 : 0)
    for (const label of ['harness-repair', 'anchors-repair']) {
      const repairs = calls.filter(call => call.label === label)
      assert.equal(repairs.length, config.failure && label === (config.failure === 'setup' ? 'harness-repair' : 'anchors-repair') ? 1 : 0)
      if (repairs.length) assert.match(repairs[0].name, /-retry1$/)
    }
  })
  // SCHEMAS.md "The pipeline owns CUDA MPS": reused harnesses get the same rule in every repair prompt.
  check(`${name}: harness and repair prompts state the pipeline-owned CUDA MPS rule`, () => {
    for (const call of calls.filter(call => ['harness', 'harness-repair', 'anchors-repair'].includes(call.label)))
      fixture.assertMpsRule(call.prompt, call.label)
  })
  if (!config.generated && !config.missing) check(`${name}: exact copies and immutable source hashes`, () => {
    const manifest = read(path.join(root, 'control/harness_source.json'))
    const expected = Object.fromEntries(Object.entries(originals).filter(([file]) => file !== 'unrelated.txt')
      .map(([file, bytes]) => [file, { sha256: sha(bytes), modified: Boolean(config.failure && file === (config.failure === 'setup' ? 'setup.sh' : 'run_anchors.sh')) }]))
    assert.deepEqual(manifest, { source: path.resolve(source), files: expected })
    assert.deepEqual(fs.readdirSync(path.join(agent, 'harness')).sort(), Object.keys(expected).sort())
    for (const [file, bytes] of Object.entries(originals)) {
      assert.deepEqual(fs.readFileSync(path.join(source, file)), bytes, 'source was mutated')
      if (file !== 'unrelated.txt' && !expected[file].modified) assert.deepEqual(fs.readFileSync(path.join(agent, 'harness', file)), bytes)
    }
    if (config.failure) {
      const before = read(path.join(root, 'before-repair.json'))
      assert.deepEqual(before.files, Object.fromEntries(Object.entries(expected).map(([file, value]) => [file, value.sha256])))
      assert.ok(Object.values(before.source.files).every(value => value.modified === false))
      const repaired = config.failure === 'setup' ? 'setup.sh' : 'run_anchors.sh'
      assert.notEqual(sha(fs.readFileSync(path.join(agent, 'harness', repaired))), expected[repaired].sha256)
    }
  })
  if (config.generated) check(`${name}: generation creates no reuse manifest`, () => {
    assert.equal(fs.existsSync(path.join(root, 'control/harness_source.json')), false)
    for (const file of REQUIRED) assert.ok(fs.statSync(path.join(agent, 'harness', file)).isFile())
  })
  check(`${name}: scripts execute with exactly one rerun after repair`, () => {
    const receipts = fs.readdirSync(path.join(root, 'control/receipts')).sort().map(file => ({ file, ...read(path.join(root, 'control/receipts', file)) }))
    for (const operation of ['setup', 'anchors']) {
      const attempts = receipts.filter(row => new RegExp(`^\\d{4}-${operation}\\.json$`).test(row.file))
      const expected = config.missing || (operation === 'anchors' && config.exhausted && config.failure === 'setup') ? []
        : config.failure === operation ? [7, config.exhausted ? 7 : 0] : [0]
      assert.deepEqual(attempts.map(row => row.rc), expected, operation)
      for (const receipt of attempts) assert.equal(receipt.fetched, true)
    }
    if (!failed) {
      assert.equal(read(path.join(agent, 'results/reproduce/anchors_scored.json')).all_passed, true)
      assert.equal(reproduce.facts.stock_verified, true)
      assert.match(fs.readFileSync(path.join(agent, 'results/reproduce/out/command-calls.log'), 'utf8'), /command/)
    }
  })
}

async function main() {
  try {
    // Copy the runtime without reading implementation text; all mutations stay in scratch.
    for (const directory of ['m5', 'idea', 'measure']) fs.cpSync(path.join(ROOT, directory), path.join(pipeline, directory), {
      recursive: true, filter: source => !['experiments', 'raids_used.jsonl'].includes(path.basename(source)),
    })
    await execute('reuse')
    await execute('relative-no-optional', { relative: true, optional: false })
    for (const failure of ['setup', 'anchors']) {
      await execute(`${failure}-repair`, { failure })
      await execute(`${failure}-exhausted`, { failure, exhausted: true })
    }
    for (const missing of REQUIRED) await execute(`missing-${missing}`, { missing })
    await execute('generated', { generated: true })
  } catch (error) { failures++; console.log(`FAIL test harness: ${error.stack}`) }
  finally { fs.rmSync(scratch, { recursive: true, force: true }) }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : 'all checks passed')
  process.exitCode = failures ? 1 : 0
}
main()
