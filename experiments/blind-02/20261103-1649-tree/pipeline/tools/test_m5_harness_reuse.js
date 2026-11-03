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
// Failure kind -> source scripts that fail, and the fixture's anchors repair target (SCHEMAS.md "A/harness/").
const FAILING = { setup: ['setup.sh'], anchors: ['run_anchors.sh'], command: ['run_command.sh'], both: ['run_anchors.sh', 'run_command.sh'] }
const REPAIR_TARGET = { anchors: 'run_anchors.sh', command: 'run_command.sh', both: 'both' }
const operationOf = failure => failure === 'setup' ? 'setup' : 'anchors'
const REPAIR_LIMITS = { setup: 4, anchors: 2 }
const REPAIR_LABEL = { setup: 'harness-repair', anchors: 'anchors-repair' }
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
    if (process.env.M5_RUN5_ROOT) return run5Agent(options)
    if (['harness-repair', 'anchors-repair'].includes(options.title)) {
      const root = process.env.M5_REPRODUCE_ROOT
      // Capture the copied scripts before the first fake repair changes anything.
      const harness = path.join(root, 'agent/harness')
      if (!fs.existsSync(path.join(root, 'before-repair.json'))) json(path.join(root, 'before-repair.json'), {
        files: Object.fromEntries(fs.readdirSync(harness).map(name => [name, sha(fs.readFileSync(path.join(harness, name)))])),
        source: read(path.join(root, 'control/harness_source.json')),
      })
    }
    const result = await fixture.run(options)
    // A repair that rewrites run_anchors.sh with its exact original bytes changes nothing.
    const config = JSON.parse(process.env.M5_REPRODUCE_CONFIG)
    if (result && config.unitRepair && ['harness-repair', 'anchors-repair'].includes(options.title)) unitRepair(options.title, config.unitRepair)
    if (options.title === 'anchors-repair' && config.rewriteAnchorsUnchanged) {
      const harness = path.join(process.env.M5_REPRODUCE_ROOT, 'agent/harness')
      fs.writeFileSync(path.join(harness, 'run_anchors.sh'), fs.readFileSync(path.join(process.env.M5_REPRODUCE_ROOT, 'pre-anchors-repair/run_anchors.sh')))
    }
    return result
  },
  exportSession: fixture.exportSession,
}
// SCHEMAS.md "A/harness/", "Optional unit files (U50)": no repair changes run_units.sh or units.json;
// after every setup or anchors repair the pipeline restores their bytes (or their absence), and they are
// uploaded with the initial harness upload, never later. `actions` maps a unit file to rewrite/delete/create.
const UNIT_FILES = ['run_units.sh', 'units.json']
const OLD_MTIME = new Date('2001-02-03T04:05:06Z')
function unitRepair(title, actions) {
  const root = process.env.M5_REPRODUCE_ROOT
  const harness = path.join(root, 'agent/harness')
  // Tripwire: date the remote unit files back; any later upload of them sets a current mtime.
  const box = path.join(root, 'box')
  for (const entry of fs.readdirSync(box).filter(entry => entry.startsWith('m5-')))
    for (const file of UNIT_FILES) {
      const remote = path.join(box, entry, 'harness', file)
      if (fs.existsSync(remote)) fs.utimesSync(remote, OLD_MTIME, OLD_MTIME)
    }
  const n = rows(path.join(root, 'unit-repairs.jsonl')).length + 1
  for (const [file, action] of Object.entries(actions)) {
    const target = path.join(harness, file)
    if (action === 'delete') fs.rmSync(target, { force: true })
    else fs.writeFileSync(target, file === 'units.json' ? `{"units":[{"id":"${title}-${n}","outputs":["x"],"cost_s":1}]}\n` : `#!/usr/bin/env bash\n# ${action} by ${title} ${n}\nexit 9\n`)
  }
  const state = Object.fromEntries(UNIT_FILES.map(file => [file, fs.existsSync(path.join(harness, file)) ? sha(fs.readFileSync(path.join(harness, file))) : null]))
  fs.appendFileSync(path.join(root, 'unit-repairs.jsonl'), JSON.stringify({ title, n, state }) + '\n')
  // From now on every box command must see the local unit files restored (checked by bin/box).
  fs.writeFileSync(path.join(root, 'unit-armed'), '')
}
// Large run_units.sh with UTF-8 text and raw non-ASCII bytes after `exit 0`; a large valid units.json.
function unitBytes(file) {
  if (file === 'units.json') return Buffer.from(JSON.stringify({ units: Array.from({ length: 3000 }, (_, i) => ({
    id: `unit-${i}.v1:a+b=c`, outputs: [`units/${i}/result.txt`, `units/${i}/log.txt`], cost_s: 1 + (i % 97) / 7 })) }, null, 2) + '\n')
  const parts = [Buffer.from('#!/usr/bin/env bash\nset -eu\n# λ ü 日本 — 🙂 "quoted" $HOME `tick` \\\nexit 0\n')]
  let state = 99, size = 0
  while (size < 200000) {
    const text = Buffer.from(`# ${size} 'single' "double" \${PATH} λ ü 日本 — 🙂\n`)
    const raw = Buffer.alloc(80)
    for (let i = 0; i < raw.length; i++) raw[i] = (state = (Math.imul(state, 1664525) + 1013904223) >>> 0) & 0xff
    parts.push(text, raw, Buffer.from('\n'))
    size += text.length + raw.length + 1
  }
  return Buffer.concat(parts)
}
// Fake agents for the recorded positive-openmm run5 regression: intake copies the recorded intake;
// the anchors repair removes the openmm version assertion from run_command.sh and nothing else.
const VERSION_ASSERTION = 'openmm.__version__'
async function run5Agent(options) {
  const root = process.env.M5_RUN5_ROOT
  const agent = path.join(root, 'agent')
  fs.appendFileSync(path.join(root, 'calls.jsonl'), JSON.stringify({ label: options.title, prompt: options.prompt, name: options.name, ms: Date.now() }) + '\n')
  let facts = { v: `${options.title} stub` }
  if (options.title === 'intake') {
    const intake = path.join(root, 'fixture', 'intake')
    fs.cpSync(intake, path.join(agent, 'intake'), { recursive: true })
    // DESIGN.md intake facts: `size` is an enum tiny/small/medium/large/unknown.
    facts = { found: true, anchors_count: read(path.join(intake, 'anchors.json')).length, data: 'available',
      licence: 'permitted', stock_environment: true, size: 'small' }
  } else if (options.title === 'anchors-repair') {
    const file = path.join(agent, 'harness', 'run_command.sh')
    const lines = fs.readFileSync(file, 'utf8').split('\n')
    fs.writeFileSync(file, lines.filter(line => !line.includes(VERSION_ASSERTION)).join('\n'))
  }
  return { text: JSON.stringify(facts), json: facts, jsonError: null, sessionID: 'stub',
    tokens: { input: 10, output: 5, reasoning: 0 }, cost: 0.001, tools: 0, ms: 5, errors: [], refusal: false }
}
if (require.main !== module) return

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
// SCHEMAS.md reproduce bullet: when reproduce passes, one `reproduce-freeze` under the setup budget
// copies the anchor run's out/ to remote reproduce-out/, and its fetch replaces A/results/reproduce/out/.
// The reused-harness path freezes too; a failed reproduce never does.
// U47: no case sets args.stage_budgets_s, so the freeze budget is the time left before the run ceiling
// (checked with every reproduce receipt by assertReceiptsTimeLeft); `budget` pins an exact value if given.
function assertFreeze(root, passed, measured, budget = null) {
  const operations = fs.readdirSync(path.join(root, 'control/receipts')).sort().filter(file => file.endsWith('.json')).map(file => file.slice(5, -5))
  const freezes = operations.flatMap((operation, i) => operation === 'reproduce-freeze' ? [i] : [])
  const box = path.join(root, 'box')
  const remote = fs.readdirSync(box).filter(entry => entry.startsWith('m5-')).map(entry => path.join(box, entry))
    .filter(directory => fs.existsSync(path.join(directory, 'harness')))
  if (!passed) {
    assert.deepEqual(freezes, [], 'freeze after a failed reproduce')
    for (const directory of remote) assert.equal(fs.existsSync(path.join(directory, 'reproduce-out')), false)
    return
  }
  assert.equal(freezes.length, 1, operations.join(','))
  const anchors = operations.lastIndexOf('anchors')
  assert.ok(anchors >= 0 && anchors < freezes[0], 'freeze must follow the anchor run')
  assert.ok(operations.slice(anchors + 1, freezes[0]).every(operation => operation === 'upload'), operations.join(','))
  const receipt = read(path.join(root, 'control/receipts', fs.readdirSync(path.join(root, 'control/receipts')).sort()
    .filter(file => file.endsWith('.json'))[freezes[0]]))
  assert.deepEqual([receipt.rc, receipt.fetched], [0, true])
  if (budget !== null) assert.equal(receipt.budget_s, budget)
  assert.equal(remote.length, 1, 'expected one remote run directory')
  const frozen = path.join(remote[0], 'reproduce-out')
  assert.ok(fs.existsSync(frozen) && !fs.lstatSync(frozen).isSymbolicLink(), 'remote reproduce-out missing or a symlink')
  assert.deepEqual(contents(frozen), contents(path.join(root, 'agent/results/reproduce/out')), 'local reproduce out/ differs from reproduce-out')
  assert.deepEqual(read(path.join(frozen, 'anchors_measured.json')), measured)
}

// U47: without args.stage_budgets_s every reproduce command (probe and harness uploads, probe, setup and
// anchors attempts and reruns, freeze) gets the time left before the run ceiling, resolved at its start.
function assertReceiptsTimeLeft(root, ceiling, spawnedMs) {
  const directory = path.join(root, 'control/receipts')
  const receipts = fs.readdirSync(directory).sort().filter(file => file.endsWith('.json')).map(file => read(path.join(directory, file)))
  assert.ok(receipts.length > 0, 'no receipts')
  fixture.assertTimeLeft(receipts, ceiling, spawnedMs)
}

const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_harness_reuse_'))
const pipeline = path.join(scratch, 'pipeline')
let checks = 0, failures = 0
function check(label, test) {
  checks++
  try { test(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${error.message}`) }
}

async function execute(name, config = {}) {
  // SCHEMAS.md "A/harness/" (U46): up to four setup repairs and two anchors repairs, the same under reuse.
  const limit = config.failure ? REPAIR_LIMITS[operationOf(config.failure)] : 0
  // Failing runs of the failing step: k (repair k passes) or limit + 1 (exhausted: repair limit + 1 would pass).
  const failures = !config.failure ? 0 : config.exhausted ? limit + 1 : config.failures ?? 1
  const repairCount = Math.min(failures, limit)
  const root = path.join(scratch, name)
  const source = path.join(root, 'previous run', 'A', 'harness')
  const agent = path.join(root, 'agent')
  script(path.join(source, 'setup.sh'), 'mkdir -p out baseline-published data\nprintf "published\\n" > baseline-published/pin\nprintf "input\\n" > data/input')
  script(path.join(source, 'run_command.sh'), 'test -f baseline-published/pin\ntest -f data/input\nprintf "command ran\\n" >> out/command-calls.log')
  script(path.join(source, 'run_anchors.sh'), 'bash harness/run_command.sh\nprintf \'{"first":100,"second":0}\\n\' > out/anchors_measured.json')
  if (config.optional !== false) script(path.join(source, 'run_evaluation.sh'), '# Optional adapter: preserve exact UTF-8 bytes: λ\ntrue')
  for (const file of config.failure ? FAILING[config.failure] : [])
    script(path.join(source, file), `mkdir -p out\nprintf 'reused ${file} failed\\n'\nexit 7`)
  // Unrelated files must not enter the copy or provenance manifest.
  fs.writeFileSync(path.join(source, 'unrelated.txt'), 'do not copy\n')
  if (config.missing) fs.unlinkSync(path.join(source, config.missing))
  for (const file of config.units ?? []) fs.writeFileSync(path.join(source, file), unitBytes(file))
  const originals = Object.fromEntries(fs.readdirSync(source).map(file => [file, fs.readFileSync(path.join(source, file))]))
  const args = { run_root: root, tag: name, stub: { profile: 'PASS', seal: 'PASS', propose: 'PASS', implement: 'PASS', evaluate: 'PASS' } }
  if (!config.generated) args.harness_from = config.relative ? path.relative(pipeline, source) : source
  if (config.ceiling) args.run_ceiling_s = config.ceiling
  const ceiling = config.ceiling ?? fixture.CEILING_DEFAULT
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
  // U50: once a fake repair has touched the unit files, every box command (re-upload, rerun, freeze)
  // records whether the local A/harness/ unit files are back to their source bytes or absence.
  const unitCheck = path.join(root, 'check-units.js')
  fs.writeFileSync(unitCheck, `
const fs = require('node:fs'), path = require('node:path')
const root = ${JSON.stringify(root)}, source = ${JSON.stringify(source)}
if (fs.existsSync(path.join(root, 'unit-armed'))) {
  const bad = []
  for (const file of ${JSON.stringify(UNIT_FILES)}) {
    const local = path.join(root, 'agent/harness', file), original = path.join(source, file)
    const want = fs.existsSync(original) ? fs.readFileSync(original) : null
    const have = fs.existsSync(local) ? fs.readFileSync(local) : null
    if (want === null ? have !== null : have === null || !want.equals(have)) bad.push(file)
  }
  fs.appendFileSync(path.join(root, 'unit-checks.jsonl'), JSON.stringify({ bad }) + '\\n')
}
`)
  script(path.join(root, 'bin/box'), `"$M5_TEST_NODE" ${JSON.stringify(unitCheck)}\n` + 'command=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\nexport PATH="$BOX_ROOT/../box-bin:$PATH"\ncd -- "$BOX_ROOT"\nbash -c "$command"\n"$M5_TEST_NODE" "$M5_REPLACE_PROBE"\nif [[ $command == *timeout* ]]; then\n  for ((i=0; i<1000; i++)); do\n    pending=false\n    for file in "$BOX_ROOT"/m5-*/*.sh; do\n      [[ -f $file ]] || continue\n      [[ -f ${file%.sh}.rc ]] || pending=true\n    done\n    [[ $pending == true ]] || break\n    sleep 0.01\n  done\nfi')
  script(path.join(root, 'bin/fetch'), 'source=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\ncd -- "$BOX_ROOT"\nexec cp -r -- "$source" "$2"')
  const fixtureConfig = {
    ...(config.unitRepair ? { unitRepair: config.unitRepair } : {}),
    anchors: [{ id: 'first', published_value: 100, tolerance: 1, quantity: 'fixture', source: 'fixture' },
      { id: 'second', published_value: 0, tolerance: 0, quantity: 'fixture', source: 'fixture' }],
    measured: { first: 100, second: 0 },
    // The reused script fails, then each fake repair passes after `failures - 1` failing rewrites
    // (tools/test_m5_reproduce.js): exhausted = every permitted repair fails too.
    setupFailures: config.failure === 'setup' ? failures : 0,
    anchorsFailures: config.failure && config.failure !== 'setup' ? failures : 0,
    anchorsRepairTarget: REPAIR_TARGET[config.failure],
    anchorsRepairStray: Boolean(config.stray), rewriteAnchorsUnchanged: Boolean(config.unchangedAnchors),
    ...(config.agentDelayMs ? { agentDelayMs: config.agentDelayMs } : {}),
  }
  const stdoutFile = path.join(root, 'stdout.log'), stderrFile = path.join(root, 'stderr.log')
  const stdout = fs.openSync(stdoutFile, 'w'), stderr = fs.openSync(stderrFile, 'w')
  let child
  const spawnedMs = Date.now()
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
    if (config.exhausted) assert.equal(reproduce.error_class, operationOf(config.failure) === 'setup' ? 'install' : 'anchor')
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
      assert.equal(repairs.length, config.failure && label === (operationOf(config.failure) === 'setup' ? 'harness-repair' : 'anchors-repair') ? repairCount : 0)
      if (repairs.length) assert.match(repairs[0].name, /-retry1$/)
      // Every repair receives the fresh probe (checked above) and the run_command.sh rules (below).
    }
  })
  // SCHEMAS.md "A/harness/" (U46): each repair prompt states `repair attempt <n> of <limit>`, under reuse too.
  if (config.failure) check(`${name}: repair prompts state attempt n of ${limit}`, () => {
    const repairs = calls.filter(call => call.label === REPAIR_LABEL[operationOf(config.failure)])
    repairs.forEach((call, i) => {
      const stated = [...call.prompt.matchAll(/repair attempt (\d+) of (\d+)/g)].map(match => `${match[1]} of ${match[2]}`)
      assert.ok(stated.length >= 1, `repair ${i + 1}: prompt lacks "repair attempt ${i + 1} of ${limit}"`)
      assert.deepEqual([...new Set(stated)], [`${i + 1} of ${limit}`], `repair ${i + 1}: prompt states ${stated.join(', ')}`)
    })
  })
  // SCHEMAS.md "The pipeline owns CUDA MPS": reused harnesses get the same rule in every repair prompt.
  check(`${name}: harness and repair prompts state the pipeline-owned CUDA MPS rule`, () => {
    for (const call of calls.filter(call => ['harness', 'harness-repair', 'anchors-repair'].includes(call.label)))
      fixture.assertMpsRule(call.prompt, call.label)
  })
  if (calls.some(call => ['harness', 'harness-repair', 'anchors-repair'].includes(call.label))) check(`${name}: harness and repair prompts state setup/anchors budgets as time left before the run ceiling`, () => {
    for (const call of calls.filter(call => ['harness', 'harness-repair', 'anchors-repair'].includes(call.label)))
      fixture.assertCeilingPrompt(call, ceiling, spawnedMs)
  })
  if (calls.some(call => call.label === 'anchors-repair')) check(`${name}: anchors repair prompt states the run_command.sh rules`, () => {
    for (const call of calls.filter(call => call.label === 'anchors-repair')) fixture.assertRunCommandRules(call.prompt, call.label)
  })
  // SCHEMAS.md: "Under reuse, an accepted anchors repair marks `modified` true for each of the two scripts
  // whose bytes it changed"; sha256 "remains unchanged after repair". Never setup.sh/run_evaluation.sh.
  const rewritten = (config.failure ? FAILING[config.failure] : []).filter(file => !(config.unchangedAnchors && file === 'run_anchors.sh'))
  if (!config.generated && !config.missing) check(`${name}: exact copies and immutable source hashes`, () => {
    const manifest = read(path.join(root, 'control/harness_source.json'))
    const expected = Object.fromEntries(Object.entries(originals).filter(([file]) => file !== 'unrelated.txt')
      .map(([file, bytes]) => [file, { sha256: sha(bytes), modified: rewritten.includes(file) }]))
    assert.deepEqual(manifest, { source: path.resolve(source), files: expected })
    assert.deepEqual(fs.readdirSync(path.join(agent, 'harness')).sort(), Object.keys(expected).sort())
    for (const [file, bytes] of Object.entries(originals)) {
      assert.deepEqual(fs.readFileSync(path.join(source, file)), bytes, 'source was mutated')
      // A stray anchors-repair edit to setup.sh/run_evaluation.sh may stay in the local view; the box copy is checked below.
      const strayEdited = config.stray && ['setup.sh', 'run_evaluation.sh'].includes(file)
      if (file !== 'unrelated.txt' && !expected[file].modified && !strayEdited) assert.deepEqual(fs.readFileSync(path.join(agent, 'harness', file)), bytes)
    }
    if (config.failure) {
      const before = read(path.join(root, 'before-repair.json'))
      assert.deepEqual(before.files, Object.fromEntries(Object.entries(expected).map(([file, value]) => [file, value.sha256])))
      assert.ok(Object.values(before.source.files).every(value => value.modified === false))
      for (const repaired of rewritten)
        assert.notEqual(sha(fs.readFileSync(path.join(agent, 'harness', repaired))), expected[repaired].sha256, repaired)
    }
  })
  if (config.generated) check(`${name}: generation creates no reuse manifest`, () => {
    assert.equal(fs.existsSync(path.join(root, 'control/harness_source.json')), false)
    for (const file of REQUIRED) assert.ok(fs.statSync(path.join(agent, 'harness', file)).isFile())
  })
  check(`${name}: scripts execute with exactly one rerun after each repair`, () => {
    const receipts = fs.readdirSync(path.join(root, 'control/receipts')).sort().map(file => ({ file, ...read(path.join(root, 'control/receipts', file)) }))
    for (const operation of ['setup', 'anchors']) {
      const attempts = receipts.filter(row => new RegExp(`^\\d{4}-${operation}\\.json$`).test(row.file))
      const expected = config.missing || (operation === 'anchors' && config.exhausted && config.failure === 'setup') ? []
        : config.failure && operationOf(config.failure) === operation
          ? Array.from({ length: repairCount + 1 }, (_, attempt) => attempt < failures ? 7 : 0) : [0]
      assert.deepEqual(attempts.map(row => row.rc), expected, operation)
      for (const receipt of attempts) assert.equal(receipt.fetched, true)
    }
    // One rerun after each repair, "with its budget resolved at the rerun's start (U47)" (SCHEMAS.md "A/harness/").
    assertReceiptsTimeLeft(root, ceiling, spawnedMs)
    if (config.failure && !config.missing) {
      const remote = fs.readdirSync(box).filter(entry => entry.startsWith('m5-')).map(entry => path.join(box, entry, 'harness'))
        .filter(directory => fs.existsSync(directory))
      assert.equal(remote.length, 1, 'expected one remote run directory')
      for (const file of rewritten) assert.deepEqual(fs.readFileSync(path.join(remote[0], file)), fs.readFileSync(path.join(agent, 'harness', file)), `${file}: repair not uploaded`)
      if (config.stray) {
        assert.deepEqual(fs.readFileSync(path.join(remote[0], 'setup.sh')), originals['setup.sh'], 'setup.sh: anchors repair changed it on the box')
        // run_evaluation.sh need not reach the box during reproduce; if it did, it must be the original.
        const evaluation = path.join(remote[0], 'run_evaluation.sh')
        if (fs.existsSync(evaluation)) assert.deepEqual(fs.readFileSync(evaluation), originals['run_evaluation.sh'], 'run_evaluation.sh: anchors repair changed it on the box')
      }
      if (operationOf(config.failure) === 'anchors') for (const file of ['run_anchors.sh', 'run_command.sh'].filter(file => !rewritten.includes(file)))
        assert.deepEqual(fs.readFileSync(path.join(remote[0], file)), originals[file], `${file}: unrewritten script changed on the box`)
    }
    if (!failed) {
      assert.equal(read(path.join(agent, 'results/reproduce/anchors_scored.json')).all_passed, true)
      assert.equal(reproduce.facts.stock_verified, true)
      assert.match(fs.readFileSync(path.join(agent, 'results/reproduce/out/command-calls.log'), 'utf8'), /command/)
    }
  })
  check(`${name}: ${failed ? 'no freeze after a failed reproduce' : 'reproduce-freeze copies the anchor outputs to reproduce-out'}`, () => {
    assertFreeze(root, !failed, fixtureConfig.measured)
  })
  if (config.units) unitChecks(name, { root, agent, box, source, originals, present: config.units, unitRepair: config.unitRepair, repairCount })
}

// SCHEMAS.md "A/harness/", "Optional unit files (U50)", pipeline obligations under args.harness_from.
function unitChecks(name, { root, agent, box, source, originals, present, unitRepair, repairCount }) {
  const absent = UNIT_FILES.filter(file => !present.includes(file))
  check(`${name}: unit files ${present.join(', ') || 'none'} copied byte for byte and recorded unmodified; ${absent.join(', ') || 'none'} not created`, () => {
    const manifest = read(path.join(root, 'control/harness_source.json'))
    assert.equal(manifest.source, path.resolve(source))
    for (const file of present) {
      assert.deepEqual(manifest.files[file], { sha256: sha(originals[file]), modified: false }, `${file}: manifest entry`)
      const local = path.join(agent, 'harness', file)
      assert.ok(fs.existsSync(local), `${file}: not copied`)
      assert.ok(fs.readFileSync(local).equals(originals[file]), `${file}: copy differs from source bytes`)
      assert.ok(fs.readFileSync(path.join(source, file)).equals(originals[file]), `${file}: source mutated`)
    }
    for (const file of absent) {
      assert.equal(file in manifest.files, false, `${file}: recorded though absent from the source`)
      assert.equal(fs.existsSync(path.join(agent, 'harness', file)), false, `${file}: created though absent from the source`)
    }
  })
  const remotes = () => fs.readdirSync(box).filter(entry => entry.startsWith('m5-')).map(entry => path.join(box, entry, 'harness'))
    .filter(directory => fs.existsSync(directory))
  check(`${name}: unit files reach the box with the initial upload, byte-identical`, () => {
    const remote = remotes()
    assert.equal(remote.length, 1, 'expected one remote run directory')
    for (const file of present) {
      const uploaded = path.join(remote[0], file)
      assert.ok(fs.existsSync(uploaded), `${file}: not uploaded`)
      assert.ok(fs.readFileSync(uploaded).equals(originals[file]), `${file}: box copy differs (${fs.statSync(uploaded).size} vs ${originals[file].length} bytes)`)
    }
    for (const file of absent) assert.equal(fs.existsSync(path.join(remote[0], file)), false, `${file}: on the box though absent from the source`)
  })
  if (!unitRepair) return
  check(`${name}: every repair's unit-file changes are undone before the next box command, and never uploaded`, () => {
    const repairs = rows(path.join(root, 'unit-repairs.jsonl'))
    assert.equal(repairs.length, repairCount, 'fake repairs that touched unit files')
    // The fixture really changed the unit files each time.
    for (const repair of repairs) for (const [file, action] of Object.entries(unitRepair))
      assert.notEqual(repair.state[file], originals[file] ? sha(originals[file]) : null, `${file}: fake ${action} by ${repair.title} ${repair.n} changed nothing`)
    const seen = rows(path.join(root, 'unit-checks.jsonl'))
    assert.ok(seen.length >= repairCount, `${seen.length} box command(s) after the first repair`)
    seen.forEach((row, i) => assert.deepEqual(row.bad, [], `box command ${i + 1} after a repair ran with unrestored unit files`))
    // Restored bytes (or absence) in A/harness/ at the end, and modified false.
    const manifest = read(path.join(root, 'control/harness_source.json'))
    for (const file of UNIT_FILES) {
      const local = path.join(agent, 'harness', file)
      if (present.includes(file)) {
        assert.ok(fs.existsSync(local) && fs.readFileSync(local).equals(originals[file]), `${file}: bytes not restored`)
        assert.equal(manifest.files[file]?.modified, false, `${file}: modified flag`)
      } else assert.equal(fs.existsSync(local), false, `${file}: absence not restored`)
    }
    // Not re-uploaded: the remote copies keep the original bytes and the mtime set when the repair ran.
    const remote = remotes()
    assert.equal(remote.length, 1, 'expected one remote run directory')
    for (const file of UNIT_FILES) {
      const uploaded = path.join(remote[0], file)
      if (!present.includes(file)) { assert.equal(fs.existsSync(uploaded), false, `${file}: uploaded after a repair created it`); continue }
      assert.ok(fs.readFileSync(uploaded).equals(originals[file]), `${file}: box copy changed`)
      assert.equal(fs.statSync(uploaded).mtimeMs, OLD_MTIME.getTime(), `${file}: re-uploaded after a repair`)
    }
  })
}

// Recorded public regression: positive-openmm run5's harness asserts openmm.__version__ == '8.2.0' in
// run_command.sh. The fake box fails that assertion until run_command.sh no longer contains it; the fake
// anchors repair removes it from run_command.sh (SCHEMAS.md: "the anchors repair may rewrite either or both").
// Fixtures are copied into scratch first; nothing is written into experiments/.
const RUN5 = path.resolve(ROOT, '..', '..', 'experiments', 'positive-openmm', 'run5', 'agent')
async function recordedRun5() {
  const name = 'recorded-positive-openmm-run5'
  const root = path.join(scratch, name), agent = path.join(root, 'agent'), box = path.join(root, 'box')
  const source = path.join(root, 'fixture', 'harness')
  fs.mkdirSync(path.join(root, 'fixture'), { recursive: true })
  for (const directory of ['harness', 'intake']) fs.cpSync(path.join(RUN5, directory), path.join(root, 'fixture', directory), { recursive: true })
  const originals = Object.fromEntries(fs.readdirSync(source).map(file => [file, fs.readFileSync(path.join(source, file))]))
  const command = originals['run_command.sh']?.toString('utf8') ?? ''
  check(`${name}: recorded run_command.sh asserts openmm 8.2.0`, () => {
    assert.ok(command.includes(VERSION_ASSERTION) && command.includes('8.2.0'), 'recorded fixture lacks the version assertion')
  })
  const anchors = read(path.join(root, 'fixture', 'intake', 'anchors.json'))
  const execution = read(path.join(root, 'fixture', 'intake', 'EXECUTION.json'))
  // Passing measurements for every intake item, derived only from the scoring contract.
  const passing = item => {
    const step = Math.max(1, Math.abs(item.published_value))
    return { '>': item.published_value + step, '<': item.published_value - step }[item.comparison] ?? item.published_value
  }
  json(path.join(root, 'measured.json'), Object.fromEntries(anchors.map(item => [item.id, passing(item)])))
  json(path.join(root, 'control/args.json'), { run_root: root, tag: name, harness_from: source,
    stub: { profile: 'PASS', seal: 'PASS', propose: 'PASS', implement: 'PASS', evaluate: 'PASS' } })
  fs.mkdirSync(box, { recursive: true })
  fs.mkdirSync(path.join(root, 'home'), { recursive: true })
  const callsFile = path.join(root, 'calls.jsonl'), shimLog = path.join(root, 'shim.jsonl')
  const originalProbe = fs.readFileSync(path.join(ROOT, 'm5/box_probe.sh'), 'utf8')
  const fakeProbe = '#!/usr/bin/env bash\nset -eu\nmkdir -p out\nprintf \'{"kernel":"' + PROBE + '","nvcc":[],"cmake":null}\\n\' > out/probe.json\n'
  fs.writeFileSync(path.join(root, 'replace-probe.js'), `
const fs = require('node:fs'), path = require('node:path')
function visit(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const file = path.join(directory, entry.name)
    if (entry.isDirectory()) visit(file)
    else if (entry.isFile() && entry.name.endsWith('.sh') && fs.readFileSync(file, 'utf8') === ${JSON.stringify(originalProbe)}) fs.writeFileSync(file, ${JSON.stringify(fakeProbe)})
  }
}
visit(process.env.BOX_ROOT)
`)
  // The box has no GPU or OpenMM: this bash shim stands in for the recorded scripts at their documented
  // invocations (`bash harness/<name>`), reading the uploaded remote run_command.sh. Everything else runs real bash.
  const shim = path.join(root, 'box-bin', 'bash')
  fs.mkdirSync(path.dirname(shim), { recursive: true })
  fs.writeFileSync(shim, `#!/bin/bash
log=${JSON.stringify(shimLog)}
if [[ $# -ge 1 && ( $1 == harness/setup.sh || $1 == harness/run_anchors.sh || $1 == harness/run_command.sh ) ]]; then
  asserted=false
  ! grep -qF '${VERSION_ASSERTION}' harness/run_command.sh || asserted=true
  printf '{"script":"%s","asserted":%s,"command_sha256":"%s"}\\n' "$1" "$asserted" "$(sha256sum harness/run_command.sh | cut -d' ' -f1)" >> "$log"
  mkdir -p out
  if [[ $1 == harness/setup.sh ]]; then mkdir -p baseline-published data; echo 'fake recorded setup'; exit 0; fi
  if [[ $asserted == true ]]; then
    echo 'Traceback (most recent call last):'
    echo "AssertionError: openmm.__version__ == '8.2.0' failed (fake box has 8.3.1)"
    exit 1
  fi
  [[ $1 == harness/run_command.sh ]] || cp ${JSON.stringify(path.join(root, 'measured.json'))} out/anchors_measured.json
  exit 0
fi
exec /bin/bash "$@"
`, { mode: 0o700 })
  script(path.join(root, 'box-bin/nvidia-smi'), 'exit 1')
  script(path.join(root, 'bin/box'), 'command=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\nexport PATH="$BOX_ROOT/../box-bin:$PATH"\ncd -- "$BOX_ROOT"\nbash -c "$command"\n"$M5_TEST_NODE" "$M5_REPLACE_PROBE"\nif [[ $command == *timeout* ]]; then\n  for ((i=0; i<1000; i++)); do\n    pending=false\n    for file in "$BOX_ROOT"/m5-*/*.sh; do\n      [[ -f $file ]] || continue\n      [[ -f ${file%.sh}.rc ]] || pending=true\n    done\n    [[ $pending == true ]] || break\n    sleep 0.01\n  done\nfi')
  script(path.join(root, 'bin/fetch'), 'source=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\ncd -- "$BOX_ROOT"\nexec cp -r -- "$source" "$2"')
  const stderrFile = path.join(root, 'stderr.log')
  const stdout = fs.openSync(path.join(root, 'stdout.log'), 'w'), stderr = fs.openSync(stderrFile, 'w')
  let child
  const spawnedMs = Date.now()
  try {
    child = await new Promise(resolve => {
      const proc = spawn(process.execPath, [path.join(pipeline, 'idea/wf.js'), '--script', path.join(pipeline, 'm5/pipeline.js'),
        '--args', path.join(root, 'control/args.json'), '--out', path.join(agent, 'wf'), '--disable-family', 'claude'], {
        cwd: pipeline, timeout: 60000, stdio: ['ignore', stdout, stderr],
        env: { ...process.env, HOME: path.join(root, 'home'), M5_RAIDS_LEDGER: path.join(scratch, 'raids.jsonl'),
          WF_STUB: __filename, M5_RUN5_ROOT: root, M5_REPRODUCE_ROOT: root, M5_REPRODUCE_CALLS: callsFile,
          M5_REPRODUCE_CONFIG: JSON.stringify({ anchors, measured: {} }), M5_TEST_NODE: process.execPath,
          M5_REPLACE_PROBE: path.join(root, 'replace-probe.js'), BOX_ROOT: box, BOX: path.join(root, 'bin/box'), FETCH: path.join(root, 'bin/fetch') },
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
  const signatures = rows(path.join(root, 'operator/signatures.jsonl'))
  const reproduce = signatures.find(row => row.signature.stage === 'reproduce')
  const anchorTotal = anchors.filter(item => !((item.comparison ?? '==') === '==' && item.tolerance === null)).length
  // Where the run stopped, for failure messages (scratch is removed afterwards).
  const progress = JSON.stringify({ calls: calls.map(call => call.label),
    stages: signatures.map(({ signature: { stage, status, error_class, blockers }, facts }) => ({ stage, status, error_class, blockers, facts })) })
  check(`${name}: exactly one anchors repair, of run_command.sh, with the run_command.sh rules`, () => {
    assert.deepEqual(calls.filter(call => /harness|repair/.test(call.label)).map(call => call.label), ['anchors-repair'], progress)
    const prompt = calls.find(call => call.label === 'anchors-repair').prompt
    assert.ok(prompt.includes('AssertionError'), 'failure log missing from repair prompt')
    assert.ok(prompt.includes(PROBE), 'fresh probe missing from repair prompt')
    fixture.assertRunCommandRules(prompt, 'anchors-repair')
  })
  check(`${name}: rewritten run_command.sh uploaded before the single rerun with the budget resolved at its start`, () => {
    const receipts = fs.readdirSync(path.join(root, 'control/receipts')).sort().filter(file => /^\d{4}-anchors\.json$/.test(file))
      .map(file => read(path.join(root, 'control/receipts', file)))
    assert.deepEqual(receipts.map(row => row.rc), [1, 0])
    // U47: the recorded intake's EXECUTION.json budgets are estimates; every reproduce command gets the
    // time left before the default 12 h ceiling instead.
    assertReceiptsTimeLeft(root, fixture.CEILING_DEFAULT, spawnedMs)
    for (const key of ['setup', 'anchors']) if (Number.isInteger(execution.stage_budgets_s?.[key]))
      assert.ok(fs.readdirSync(path.join(root, 'control/receipts')).filter(file => file.endsWith('.json'))
        .every(file => read(path.join(root, 'control/receipts', file)).budget_s !== execution.stage_budgets_s[key]), `intake ${key} budget used as a timeout`)
    assert.deepEqual(fs.readFileSync(path.join(agent, 'intake', 'EXECUTION.json')), fs.readFileSync(path.join(root, 'fixture', 'intake', 'EXECUTION.json')), 'EXECUTION.json changed')
    fixture.assertCeilingPrompt(rows(callsFile).find(call => call.label === 'anchors-repair'), fixture.CEILING_DEFAULT, spawnedMs)
    const runs = rows(shimLog).filter(row => row.script === 'harness/run_anchors.sh')
    assert.deepEqual(runs.map(row => row.asserted), [true, false], 'fake box did not see the rewritten run_command.sh')
    assert.equal(runs[1].command_sha256, sha(fs.readFileSync(path.join(agent, 'harness/run_command.sh'))))
  })
  check(`${name}: reproduce reaches anchor scoring`, () => {
    const scored = read(path.join(agent, 'results/reproduce/anchors_scored.json'))
    assert.equal(scored.anchors.length, anchors.length)
    assert.equal(scored.anchors_total, anchorTotal)
    assert.equal(scored.all_passed, true)
    assert.equal(reproduce?.facts.anchors_total, anchorTotal)
    assert.equal(reproduce?.facts.anchors_passed, anchorTotal)
    assert.equal(reproduce?.facts.stock_verified, true)
    assert.equal(reproduce?.signature.status, 'PASS')
  })
  check(`${name}: reproduce-freeze copies the repaired anchor run's outputs to reproduce-out`, () => {
    assertFreeze(root, true, read(path.join(root, 'measured.json')))
  })
  check(`${name}: provenance marks only run_command.sh modified, source hashes unchanged`, () => {
    const manifest = read(path.join(root, 'control/harness_source.json'))
    assert.equal(manifest.source, path.resolve(source))
    assert.deepEqual(manifest.files, Object.fromEntries(Object.entries(originals).filter(([file]) => REQUIRED.includes(file) || file === 'run_evaluation.sh')
      .map(([file, bytes]) => [file, { sha256: sha(bytes), modified: file === 'run_command.sh' }])))
    for (const [file, bytes] of Object.entries(originals)) assert.deepEqual(fs.readFileSync(path.join(source, file)), bytes, `${file}: source mutated`)
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
    for (const failure of ['setup', 'anchors', 'command', 'both']) {
      await execute(`${failure}-repair`, { failure })
      await execute(`${failure}-repaired-twice`, { failure, failures: 2 })
      await execute(`${failure}-exhausted`, { failure, exhausted: true })
    }
    // U46: a reused setup.sh passes after the third or fourth repair; modified marks setup.sh only.
    await execute('setup-repaired-thrice', { failure: 'setup', failures: 3 })
    await execute('setup-repaired-four-times', { failure: 'setup', failures: 4 })
    // U47: under a small run ceiling, a reused setup.sh repaired twice reruns with non-increasing
    // time-left budgets (each repair call takes over a second).
    await execute('ceiling-setup-repaired-twice', { failure: 'setup', failures: 2, ceiling: 240, agentDelayMs: 1100 })
    // An anchors repair that also edits setup.sh and run_evaluation.sh marks neither modified.
    await execute('both-repair-stray', { failure: 'both', stray: true })
    // Rewriting run_anchors.sh with identical bytes is not a change.
    await execute('command-repair-anchors-unchanged', { failure: 'command', unchangedAnchors: true })
    // U50a: optional unit files under args.harness_from (copy, initial upload, restore after repairs).
    await execute('units-both', { units: UNIT_FILES })
    await execute('units-only-run-units', { units: ['run_units.sh'], relative: true })
    await execute('units-only-units-json', { units: ['units.json'], optional: false })
    await execute('units-none', { units: [] })
    await execute('units-setup-repair-rewrite-delete', { units: UNIT_FILES, failure: 'setup', failures: 2, unitRepair: { 'run_units.sh': 'rewrite', 'units.json': 'delete' } })
    await execute('units-setup-repair-create', { units: [], failure: 'setup', unitRepair: { 'run_units.sh': 'create', 'units.json': 'create' } })
    await execute('units-anchors-repair-rewrite-delete', { units: UNIT_FILES, failure: 'both', failures: 2, unitRepair: { 'units.json': 'rewrite', 'run_units.sh': 'delete' } })
    await execute('units-anchors-repair-create-rewrite', { units: ['units.json'], failure: 'command', unitRepair: { 'run_units.sh': 'create', 'units.json': 'rewrite' } })
    await recordedRun5()
    for (const missing of REQUIRED) await execute(`missing-${missing}`, { missing })
    await execute('generated', { generated: true })
  } catch (error) { failures++; console.log(`FAIL test harness: ${error.stack}`) }
  finally { fs.rmSync(scratch, { recursive: true, force: true }) }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : 'all checks passed')
  process.exitCode = failures ? 1 : 0
}
main()
