#!/usr/bin/env node
'use strict'

// Black-box contract tests for card calibration in the m5 pipeline (U54): m5/SCHEMAS.md "Card calibration
// (U54)" (args.card, the three card files, prompts, harness/card_extract.json and its seal, scoring and the four
// reproduce facts), "A/harness/" (harness_from) and "A/results/reproduce/"; plus `pipeline_commit` in the
// args.json of a dry m5 launch. Never inspect pipeline.js, score_card.py, launch.js or git history.
//
// The fake box and agents follow tools/test_m5_units_check.js: the box really executes every command in a
// temporary shared run directory; intake and the generated harness come from tools/test_m5_reproduce.js. This
// file is also the stub agent module (WF_STUB): it records every call with its prompt (through the reproduce
// fixture), snapshots the card files at the first agent call, writes harness/card_extract.json for a generated
// harness, and declines every repair unless a case asks for the fixture's repairs.
// Usage: node tools/test_m5_card_pipeline.js [case-name regex] [keep]
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const crypto = require('node:crypto')
const assert = require('node:assert/strict')
const { spawn } = require('node:child_process')
const fixture = require('./test_m5_reproduce.js')

const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex')
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const rows = file => fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : []
const b64 = file => fs.existsSync(file) ? fs.readFileSync(file).toString('base64') : null

// Card outputs the representative run writes (read by the extraction rules below).
const METRICS = { throughput: { steps_per_h: 6100 }, mem: { gb: 200 }, anchor: { rate: 0.425 } }
const CARD_OUTPUT_SH = `mkdir -p out/card\nprintf '%s\\n' '${JSON.stringify(METRICS)}' > out/card/metrics.json\nprintf 'warmup_s=11\\nwarmup_s=13\\n' > out/card/run.log`

// ---- Stub agents ------------------------------------------------------------------------------------------
module.exports = {
  async run(options) {
    const root = process.env.M5_REPRODUCE_ROOT
    const cfg = JSON.parse(process.env.M5_CARD_CONFIG)
    const first = path.join(root, 'first-call.json')
    if (!fs.existsSync(first)) {
      const receipts = path.join(root, 'control', 'receipts')
      fs.writeFileSync(first, JSON.stringify({ label: options.title,
        card: b64(path.join(root, 'control', 'card.json')), seal: b64(path.join(root, 'control', 'card_seal.json')),
        inputs: b64(path.join(root, 'agent', 'card_inputs.json')),
        receipts: fs.existsSync(receipts) ? fs.readdirSync(receipts).length : 0 }))
    }
    // "Every later read of the card uses C/card.json, never result": the tree result disappears once intake runs.
    if (options.title === 'intake' && cfg.clobberResult) fs.writeFileSync(cfg.clobberResult, '{"calibration": "gone"}\n')
    if (['harness-repair', 'anchors-repair'].includes(options.title) && !cfg.fixtureRepairs) {
      fs.appendFileSync(process.env.M5_REPRODUCE_CALLS, JSON.stringify({ label: options.title, name: options.name, prompt: options.prompt, declined: true, ms: Date.now() }) + '\n')
      return null
    }
    const reply = await fixture.run(options)
    const harness = path.join(root, 'agent', 'harness')
    if (options.title === 'harness') {
      fs.appendFileSync(path.join(harness, 'run_command.sh'), '\n' + CARD_OUTPUT_SH + '\n')
      if (cfg.extract !== null) fs.writeFileSync(path.join(harness, 'card_extract.json'), typeof cfg.extract === 'string' ? cfg.extract : JSON.stringify(cfg.extract, null, 1) + '\n')
    }
    // A repair that also rewrites card_extract.json ("No repair changes card_extract.json").
    if (options.title === 'anchors-repair' && cfg.repairTamper) {
      fs.writeFileSync(path.join(harness, 'card_extract.json'), JSON.stringify(cfg.repairTamper, null, 1) + '\n')
      fs.appendFileSync(path.join(harness, 'run_command.sh'), '\n' + CARD_OUTPUT_SH + '\n')
    }
    return reply
  },
  exportSession: fixture.exportSession,
}
if (require.main !== module) return

const ROOT = path.resolve(__dirname, '..')
const STAGES = ['intake', 'reproduce', 'profile', 'seal', 'propose', 'implement', 'evaluate', 'takeaways']
const FOUR = ['card_inputs', 'card_measured', 'card_holds', 'card_refuted']
const PROBE = 'card-pipeline-probe-77031'
const ANCHORS = [{ id: 'first', published_value: 100, tolerance: 1, quantity: 'fixture', source: 'fixture' },
  { id: 'second', published_value: 0, tolerance: 0, quantity: 'fixture', source: 'fixture' }]
const PASSING = { first: 100, second: 0 }
const clone = value => JSON.parse(JSON.stringify(value))
function json(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, typeof value === 'string' ? value : JSON.stringify(value, null, 1) + '\n')
}
function script(file, body) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, '#!/usr/bin/env bash\nset -eu\n' + body + '\n', { mode: 0o700 })
}

// ---- The tree result and its card record ------------------------------------------------------------------
// Hidden values (SCHEMAS.md: card_inputs.json and agents never see values, bases, bands, gates, cost lines,
// budgets, predictions or published values): each is distinctive so it can be searched for.
const HIDDEN_NUMBERS = ['4817.25', '2963', '12.75', '2.375', '41.5', '0.2575', '0.4219', '0.0137', '777.31', '1.0473', '63.8417', '0.0419']
const HIDDEN_TEXT = ['PREDICTION_PRIVATE_SENTINEL', 'RESTS_PRIVATE_SENTINEL', 'COSTLINE_PRIVATE_SENTINEL', 'DIFFERS_PRIVATE_SENTINEL',
  'ELSE_PRIVATE_SENTINEL', 'JUDGED_PRIVATE_SENTINEL', 'OTHER_RECORD_PRIVATE_SENTINEL', 'STOP_RULE_PRIVATE_SENTINEL']
const P1 = { id: 'P1', what: 'pilot throughput run', stop_rule: 'STOP_RULE_PRIVATE_SENTINEL',
  gate: { on: 'steps_per_h', op: '>=', value: 2963, else: 'ELSE_PRIVATE_SENTINEL' } }
const req = (id, basis, value, extra) => ({ id, basis, value, differs_in: ['DIFFERS_PRIVATE_SENTINEL'], measured_by: 'P1',
  cum_spend_through_measured_by: 63.8417, k_budget: 1.0473, line: { id: 'pilot', what: 'COSTLINE_PRIVATE_SENTINEL', usd: 777.31 },
  rests_on: 'RESTS_PRIVATE_SENTINEL', ...extra })
const RECORD = { key: 'R1:physical:W1', title: 'alpha quartz flow', state: 'calibration_required', plan_usd: 777.31,
  required: [
    req('steps_per_h', 'PROXY', 4817.25, { name: 'training steps per instance-hour', unit: 'steps/h', band: null, phase: P1 }),
    req('warmup_s', 'GUESS', 12.75, { name: 'warm-up seconds', unit: 's', band: { abs: 2.375 }, phase: { id: 'P1', what: 'pilot throughput run' } }),
    req('mem_gb', 'GUESS', 41.5, { measured_by: 'P2', phase: null }),
    req('idle_frac', 'PROXY', 0.2575, { name: 'idle fraction', unit: '1', band: null, measured_by: 'P2', phase: { id: 'P2', what: 'sweep at the published scale' } }),
  ],
  resolved: [], anchor: { what: 'reproduce the released success rate', published_value: 0.4219, tolerance: { abs: 0.0137 }, source_id: 's2' },
  predictions: { if_lever: 'PREDICTION_PRIVATE_SENTINEL more than 5 points', if_not: 'within 2 points', expected: 'if_not' },
  judged: { plan: { note: 'JUDGED_PRIVATE_SENTINEL' }, pick: {}, given: { budget_usd: 1000 }, gate_args: {} } }
const OTHER = { key: 'R2:interp:W2', title: 'other', state: 'calibration_required', plan_usd: 5,
  required: [req('other_x', 'GUESS', 3, { name: 'OTHER_RECORD_PRIVATE_SENTINEL', unit: 'x', band: null, phase: null })],
  resolved: [], anchor: null, predictions: null, judged: null }
const RESULT = { table: '| t |', cards: [], calibration: [OTHER, RECORD,
  { key: 'R3:physical:W3', title: 'halted', state: 'not_judged', plan_usd: null, required: [], resolved: [], anchor: null, predictions: null, judged: null }] }
const RULES = [
  { id: 'steps_per_h', file: 'card/metrics.json', kind: 'json', expr: '/throughput/steps_per_h' },
  { id: 'warmup_s', file: 'card/run.log', kind: 'regex', expr: 'warmup_s=([0-9.]+)' },
  { id: 'mem_gb', file: 'card/metrics.json', kind: 'json', expr: '/mem/gb' },
  { id: 'idle_frac', file: 'card/absent.json', kind: 'json', expr: '/x' },
  { id: 'anchor', file: 'card/metrics.json', kind: 'json', expr: '/anchor/rate' },
]
const EXTRACT = { rules: RULES }
const withRecord = (change, value = RESULT) => { const result = clone(value); result.calibration[1] = change(clone(RECORD)); return result }
const expectedInputs = record => ({ inputs: record.required.map(item => ({ id: item.id, name: item.name ?? null, unit: item.unit ?? null,
  measured_by: item.measured_by ?? null, phase: item.phase && typeof item.phase === 'object' ? item.phase.what ?? null : null })),
anchor: record.anchor && typeof record.anchor.published_value === 'number' ? { what: record.anchor.what } : null })

// ---- One workflow run -------------------------------------------------------------------------------------
// spec: { card (args value, or function of {result, root, reference}), result (value or raw text), resultKind
// ('file' | 'directory' | 'missing'), generated (no harness_from), extract (object, raw string, null = absent),
// anchorsRc, measured, setupTamper, stub (args.stub additions), commit (args.pipeline_commit), unitsCheck,
// unitsProbe, clobberResult, fixtureRepairs, anchorsFailures, repairTamper }
const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_card_pipeline_'))
const pipeline = path.join(scratch, 'pipeline')
const ONLY = process.argv[2] ? new RegExp(process.argv[2]) : null
let checks = 0, failures = 0
function check(label, test) {
  if (ONLY && !ONLY.test(label)) return
  checks++
  try { test(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${String(error.message).replace(/\s*\n\s*/g, ' ').slice(0, 1500)}`) }
}
async function execute(name, spec) {
  if (ONLY && !ONLY.test(name)) return null
  const root = path.join(scratch, name)
  const agent = path.join(root, 'agent')
  const source = path.join(root, 'previous run', 'A', 'harness')
  const reference = path.join(root, 'previous run', 'A', 'results', 'reproduce', 'out')
  const resultFile = path.join(root, 'tree run', 'result-CARDRESULT.json')
  const box = path.join(root, 'box')
  for (const directory of [box, reference, path.join(root, 'home')]) fs.mkdirSync(directory, { recursive: true })
  const kind = spec.resultKind ?? 'file'
  if (kind === 'file') json(resultFile, spec.result ?? RESULT)
  if (kind === 'directory') fs.mkdirSync(resultFile, { recursive: true })
  const extract = spec.extract === undefined ? EXTRACT : spec.extract
  const extractText = extract === null ? null : typeof extract === 'string' ? extract : JSON.stringify(extract, null, 1) + '\n'
  if (!spec.generated) {
    // Harness of a "previous run", copied by args.harness_from. setupTamper edits the sealed card record on
    // the (local) box after the seal, so scoring must fail its seal check.
    script(path.join(source, 'setup.sh'), `mkdir -p out baseline-published data\nprintf 'published\\n' > baseline-published/pin\nprintf 'input\\n' > data/input` +
      (spec.setupTamper ? `\nprintf ' ' >> ${JSON.stringify(path.join(root, 'control', 'card.json'))}` : ''))
    script(path.join(source, 'run_command.sh'), `test -f baseline-published/pin\nmkdir -p out\nprintf 'command ran\\n' >> out/command-calls.log\n${CARD_OUTPUT_SH}`)
    script(path.join(source, 'run_anchors.sh'), `bash harness/run_command.sh\nprintf '%s\\n' '${JSON.stringify(spec.measured ?? PASSING)}' > out/anchors_measured.json\nexit ${spec.anchorsRc ?? 0}`)
    if (extractText !== null) fs.writeFileSync(path.join(source, 'card_extract.json'), extractText)
  }
  const args = { run_root: root, tag: name, stub: { profile: 'PASS', seal: 'PASS', propose: 'PASS', implement: 'PASS', evaluate: 'PASS', ...(spec.stub ?? {}) } }
  if (!spec.generated) args.harness_from = source
  if (spec.card !== undefined) args.card = typeof spec.card === 'function' ? spec.card({ result: resultFile, root, reference }) : spec.card
  if (spec.commit !== undefined) args.pipeline_commit = spec.commit
  if (spec.unitsCheck) args.units_check = { reference }
  if (spec.unitsProbe) args.units_probe = { reference }
  json(path.join(root, 'control/args.json'), args)

  const callsFile = path.join(root, 'calls.jsonl')
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
  // Before each box command: which card files exist, and whether a harness script is already on the box.
  const cardState = 'c="$BOX_ROOT/../control"\nh=0\nfor f in "$BOX_ROOT"/m5-*/harness/setup.sh; do [[ ! -f $f ]] || h=1; done\n' +
    'printf \'{"card":%s,"seal":%s,"inputs":%s,"extract_seal":%s,"harness":%s}\\n\' "$([[ -f $c/card.json ]] && echo true || echo false)" ' +
    '"$([[ -f $c/card_seal.json ]] && echo true || echo false)" "$([[ -f $BOX_ROOT/../agent/card_inputs.json ]] && echo true || echo false)" ' +
    '"$([[ -f $c/card_extract_seal.json ]] && echo true || echo false)" "$([[ $h == 1 ]] && echo true || echo false)" >> "$BOX_ROOT/../card-box.jsonl"\n'
  script(path.join(root, 'bin/box'), 'command=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\nexport PATH="$BOX_ROOT/../box-bin:$PATH"\ncd -- "$BOX_ROOT"\n' + cardState +
    'bash -c "$command"\n"$M5_TEST_NODE" "$M5_REPLACE_PROBE"\nif [[ $command == *timeout* ]]; then\n  for ((end=SECONDS+1800; SECONDS<end; )); do\n    pending=false\n    for file in "$BOX_ROOT"/m5-*/*.sh; do\n      [[ -f $file ]] || continue\n      [[ -f ${file%.sh}.rc ]] || pending=true\n    done\n    [[ $pending == true ]] || break\n    sleep 0.01\n  done\nfi\nexit 0')
  script(path.join(root, 'bin/fetch'), 'source=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\ncd -- "$BOX_ROOT"\nexec cp -r -- "$source" "$2"')
  const fixtureConfig = { anchors: ANCHORS, measured: spec.measured ?? PASSING, setupFailures: 0, anchorsFailures: spec.anchorsFailures ?? 0 }
  const cardConfig = { extract: spec.generated ? (extractText ?? null) : null, clobberResult: spec.clobberResult ? resultFile : null,
    fixtureRepairs: Boolean(spec.fixtureRepairs), repairTamper: spec.repairTamper ?? null }
  const stderrFile = path.join(root, 'stderr.log')
  const stdout = fs.openSync(path.join(root, 'stdout.log'), 'w'), stderr = fs.openSync(stderrFile, 'w')
  let child
  try {
    child = await new Promise(resolve => {
      const proc = spawn(process.execPath, [path.join(pipeline, 'idea/wf.js'), '--script', path.join(pipeline, 'm5/pipeline.js'),
        '--args', path.join(root, 'control/args.json'), '--out', path.join(agent, 'wf'), '--disable-family', 'claude'], {
        cwd: pipeline, timeout: 1800000, killSignal: 'SIGKILL', stdio: ['ignore', stdout, stderr],
        env: { ...process.env, HOME: path.join(root, 'home'), M5_RAIDS_LEDGER: path.join(scratch, 'raids.jsonl'),
          WF_STUB: __filename, M5_REPRODUCE_ROOT: root, M5_REPRODUCE_CONFIG: JSON.stringify(fixtureConfig), M5_CARD_CONFIG: JSON.stringify(cardConfig),
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
  const records = rows(path.join(root, 'operator/signatures.jsonl')).map(row => ({ ...row.signature, facts: row.facts }))
  const receiptDir = path.join(root, 'control/receipts')
  const receipts = fs.existsSync(receiptDir) ? fs.readdirSync(receiptDir).sort().filter(file => file.endsWith('.json'))
    .map(file => ({ operation: file.slice(5, -5), ...read(path.join(receiptDir, file)) })) : []
  const firstFile = path.join(root, 'first-call.json')
  return { name, spec, root, agent, control: path.join(root, 'control'), source, resultFile, records, receipts, extractText,
    calls: rows(callsFile).filter(call => !['probe', 'probe-upload'].includes(call.label)), allCalls: rows(callsFile),
    boxLog: rows(path.join(root, 'card-box.jsonl')), first: fs.existsSync(firstFile) ? read(firstFile) : null,
    stage: label => records.find(row => row.stage === label) }
}

// ---- Shared checks ----------------------------------------------------------------------------------------
function statuses(r, wanted) {
  check(`${r.name}: stage statuses ${wanted.map(([stage, status]) => `${stage}=${status}`).join(' ')}`, () => {
    const got = r.records.filter(row => STAGES.includes(row.stage)).map(row => [row.stage, row.status])
    assert.deepEqual(got, wanted, JSON.stringify({ reproduce: r.stage('reproduce')?.error_class, intake: r.stage('intake')?.error_class }))
  })
}
const failedAt = (stage, ok = []) => STAGES.map((label, i) => [label, label === stage ? 'FAIL'
  : i < STAGES.indexOf(stage) ? 'PASS' : label === 'takeaways' ? 'PASS' : ok.includes(label) ? 'PASS' : 'SKIPPED'])
const ALL_PASS = STAGES.map(label => [label, 'PASS'])
function errorClass(r, stage, errorClass) {
  check(`${r.name}: ${stage} error_class ${errorClass}, exit_code ${errorClass === 'anchor' ? 4 : 2}`, () => {
    const signature = r.stage(stage)
    assert.equal(signature?.error_class, errorClass)
    assert.equal(signature.exit_code, errorClass === 'anchor' ? 4 : 2)
  })
}
// The four facts: null outside card mode, on SKIPPED/stub records and without card_scored.json.
function nullFacts(r, label) {
  check(`${r.name}: card facts null (${label})`, () => {
    const record = r.stage('reproduce')
    assert.ok(record, 'no reproduce record')
    const executed = record.status !== 'SKIPPED' && label !== 'stub'
    for (const key of FOUR) {
      if (executed) assert.ok(Object.hasOwn(record.facts, key), `${key} missing from an executed reproduce record`)
      assert.equal(record.facts?.[key] ?? null, null, key)
    }
  })
}
const afterProbe = r => {
  const at = r.receipts.findIndex(receipt => receipt.operation === 'probe')
  return at < 0 ? [] : r.receipts.slice(at + 1)
}
// Invalid args.card: intake fails with parse before any agent call and any box command.
function intakeParse(r) {
  if (!r) return
  statuses(r, failedAt('intake'))
  errorClass(r, 'intake', 'parse')
  check(`${r.name}: no agent call and no box command`, () => {
    assert.deepEqual(r.allCalls.map(call => call.label), [], 'agent or probe call')
    assert.deepEqual(r.receipts.map(receipt => receipt.operation), [], 'box receipt')
    assert.deepEqual(r.boxLog, [], 'box command')
  })
  nullFacts(r, 'SKIPPED reproduce')
}
// card_extract.json missing or invalid: reproduce fails with parse before the harness upload.
function extractParse(r, generated = false) {
  if (!r) return
  statuses(r, failedAt('reproduce'))
  errorClass(r, 'reproduce', 'parse')
  check(`${r.name}: the box probe only; no harness upload, setup or anchors; no repair`, () => {
    assert.deepEqual(r.receipts.map(receipt => receipt.operation), ['upload', 'probe'])
    assert.ok(r.boxLog.every(entry => !entry.harness), 'a harness script reached the box')
    assert.ok(!r.calls.some(call => /repair/.test(call.label)), 'repair call')
    assert.deepEqual(r.calls.map(call => call.label), generated ? ['intake', 'harness'] : ['intake'])
  })
  check(`${r.name}: no extract seal and no card_scored.json`, () => {
    assert.equal(fs.existsSync(path.join(r.control, 'card_extract_seal.json')), false, 'card_extract_seal.json written for an invalid file')
    assert.equal(fs.existsSync(path.join(r.control, 'card_scored.json')), false)
  })
  nullFacts(r, 'no card_scored.json')
}
// The three card files, written exactly and before any agent call or box command.
function cardFileChecks(r, { record = RECORD, bands = {}, result = r.resultFile, noBox = false } = {}) {
  const cardFile = path.join(r.control, 'card.json'), sealFile = path.join(r.control, 'card_seal.json')
  const inputsFile = path.join(r.agent, 'card_inputs.json')
  check(`${r.name}: control/card.json exactly {source, source_sha256, record, bands}`, () => {
    const card = read(cardFile)
    assert.deepEqual(Object.keys(card).sort(), ['bands', 'record', 'source', 'source_sha256'])
    assert.equal(card.source, result, 'source is not the absolute path of result')
    assert.equal(card.source_sha256, r.resultSha ?? sha(fs.readFileSync(result)))
    assert.deepEqual(card.record, record)
    assert.deepEqual(card.bands, bands)
  })
  check(`${r.name}: control/card_seal.json exactly {card_sha256, sealed_utc}`, () => {
    const seal = read(sealFile)
    assert.deepEqual(Object.keys(seal).sort(), ['card_sha256', 'sealed_utc'])
    assert.equal(seal.card_sha256, sha(fs.readFileSync(cardFile)))
    assert.match(seal.sealed_utc, /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?(Z|\+00:00)$/)
  })
  check(`${r.name}: agent/card_inputs.json exactly {inputs, anchor} as specified`, () => {
    assert.deepEqual(read(inputsFile), expectedInputs(record))
  })
  check(`${r.name}: agent/card_inputs.json holds no value, basis, band, gate, cost line, budget, prediction or published value`, () => {
    const text = fs.readFileSync(inputsFile, 'utf8')
    for (const word of [...HIDDEN_TEXT, 'PROXY', 'GUESS']) assert.ok(!text.includes(word), `${word} in card_inputs.json`)
    for (const number of HIDDEN_NUMBERS) assert.ok(!new RegExp(`(?<![0-9.])${number.replace('.', '\\.')}(?![0-9])`).test(text), `${number} in card_inputs.json`)
  })
  check(`${r.name}: the three card files exist, final, at the first agent call and the first box command`, () => {
    assert.ok(r.first, 'no agent call')
    assert.deepEqual([r.first.card, r.first.seal, r.first.inputs], [b64(cardFile), b64(sealFile), b64(inputsFile)])
    assert.equal(r.first.receipts, 0, 'a box command ran before the first agent call')
    if (noBox && r.boxLog.length === 0) return
    assert.ok(r.boxLog.length > 0, 'no box command')
    assert.deepEqual([r.boxLog[0].card, r.boxLog[0].seal, r.boxLog[0].inputs], [true, true, true])
  })
  check(`${r.name}: written in order card.json, card_seal.json, card_inputs.json`, () => {
    const times = [cardFile, sealFile, inputsFile].map(file => fs.statSync(file).mtimeMs)
    assert.ok(times[0] <= times[1] && times[1] <= times[2], `mtimes ${times}`)
  })
}
// Review of U54: no file an agent can read (everything under the run's agent/, the workflow run record
// agent/wf/run.json included) holds args.card or anything of control/card.json.
function* objectsIn(value) {
  if (value && typeof value === 'object') {
    if (!Array.isArray(value)) yield value
    for (const child of Object.values(value)) yield* objectsIn(child)
  }
}
// run.json holds the run's arguments: some object in it carries every key of `args` with the same value.
function holdsArgs(record, args) {
  for (const object of objectsIn(record)) {
    try { for (const key of Object.keys(args)) assert.deepEqual(object[key], args[key]); return true } catch { /* next */ }
  }
  return false
}
function agentFiles(directory, prefix = '') {
  const list = []
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const file = path.join(directory, entry.name)
    if (entry.isDirectory()) list.push(...agentFiles(file, prefix + entry.name + '/'))
    else if (entry.isFile()) list.push([prefix + entry.name, file])
  }
  return list
}
function noCardInAgentFiles(r, launchBands = null) {
  const args = read(path.join(r.control, 'args.json'))
  const runFile = path.join(r.agent, 'wf', 'run.json')
  check(`${r.name}: agent/wf/run.json omits card and still records the other run arguments`, () => {
    assert.ok(fs.existsSync(runFile), 'no agent/wf/run.json')
    const record = read(runFile)
    for (const object of objectsIn(record)) assert.ok(!Object.hasOwn(object, 'card'), 'run.json has a `card` key')
    const { card: _card, ...rest } = args
    assert.ok(holdsArgs(record, rest), 'run.json does not record the run arguments other than card')
  })
  check(`${r.name}: no file under agent/ holds the result path, the record or the launch bands`, () => {
    const found = []
    for (const [name, file] of agentFiles(r.agent)) {
      const text = fs.readFileSync(file).toString('latin1')
      if (name === 'card_inputs.json') continue   // checked exactly by cardFileChecks
      if (text.includes('CARDRESULT')) found.push(`${name}: result path`)
      if (text.includes(r.resultFile) || text.includes(path.dirname(r.resultFile))) found.push(`${name}: result directory`)
      for (const hidden of hiddenIn(text)) found.push(`${name}: ${hidden}`)
      if (/"(source_sha256|card_sha256)"/.test(text)) found.push(`${name}: card.json or seal fields`)
      if (launchBands) for (const [id, band] of Object.entries(launchBands))
        if (new RegExp(`"?abs"?\\s*:\\s*${String(band.abs).replace('.', '\\.')}(?![0-9])`).test(text)) found.push(`${name}: launch band of ${id}`)
    }
    assert.deepEqual(found, [])
  })
}
// Outside card mode the workflow run record is unchanged: it records every run argument.
function plainRunRecord(r) {
  check(`${r.name}: agent/wf/run.json records every run argument (outside card mode)`, () => {
    const runFile = path.join(r.agent, 'wf', 'run.json')
    assert.ok(fs.existsSync(runFile), 'no agent/wf/run.json')
    assert.ok(holdsArgs(read(runFile), read(path.join(r.control, 'args.json'))), 'run.json does not record the run arguments')
  })
}
const hiddenIn = text => [...HIDDEN_TEXT.filter(word => text.includes(word)),
  ...HIDDEN_NUMBERS.filter(number => new RegExp(`(?<![0-9.])${number.replace('.', '\\.')}(?![0-9])`).test(text))]
const count = (text, needle) => text.split(needle).length - 1
// Card-mode prompts: name card_inputs.json, never control/ card files or the result; no hidden value.
function promptChecks(r, baseline) {
  for (const call of r.calls) check(`${r.name}: ${call.label} prompt carries no hidden card value and never names the result or the card's control/ files`, () => {
    assert.deepEqual(hiddenIn(call.prompt), [])
    assert.ok(!call.prompt.includes('result-CARDRESULT') && !call.prompt.includes(path.dirname(r.resultFile)), 'prompt names result')
    for (const file of ['card.json', 'card_seal.json', 'card_extract_seal.json', 'card_scored.json'])
      assert.ok(!new RegExp(`(^|[^_a-z])${file.replace('.', '\\.')}`).test(call.prompt.replaceAll('card_inputs.json', '').replaceAll('card_extract.json', '')), `prompt names ${file}`)
    // The existing "agents never read control/" wording may stay; card mode adds no other mention of control/.
    const plain = baseline?.calls.find(other => other.label === call.label)
    if (plain) {
      assert.ok(count(call.prompt, 'control/') <= count(plain.prompt, 'control/'), `control/ named ${count(call.prompt, 'control/')} times (without args.card: ${count(plain.prompt, 'control/')})`)
      assert.ok(count(call.prompt, r.control) <= count(plain.prompt, baseline.control), 'card mode adds a mention of the control directory path')
    } else assert.fail(`no ${call.label} prompt without args.card to compare with`)
  })
  const intake = r.calls.find(call => call.label === 'intake')
  check(`${r.name}: intake prompt names card_inputs.json, the listed inputs, and the phases' protocol as EXECUTION.json's workload`, () => {
    assert.ok(intake, 'no intake call')
    assert.match(intake.prompt, /card_inputs\.json/)
    assert.match(intake.prompt, /calibrat/i)
    assert.match(intake.prompt, /EXECUTION\.json/)
    assert.match(intake.prompt, /representative/i)
    assert.match(intake.prompt, /\bphases?\b/)
  })
}
const SCORED_KEYS = ['key', 'run', 'pipeline_commit', 'box_type', 'box_started_utc', 'card_sha256', 'extract_sha256', 'predictions',
  'anchor', 'rows', 'inputs_total', 'measured_total', 'holds_total', 'refuted_total']
// After a passing anchors run: card_scored.json and the four facts.
function scoredChecks(r, { decisions, measured, totals, commit = null, record = RECORD, anchor = 'default', status = 'PASS' }) {
  const file = path.join(r.control, 'card_scored.json')
  check(`${r.name}: control/card_scored.json written with the card's identity and seals`, () => {
    assert.ok(fs.existsSync(file), 'no card_scored.json')
    const scored = read(file)
    assert.deepEqual(Object.keys(scored).sort(), [...SCORED_KEYS].sort())
    assert.equal(scored.key, record.key)
    assert.equal(scored.run, r.name, 'run is the run tag')
    assert.equal(scored.pipeline_commit, commit)
    const boxFile = path.join(r.control, 'box.json')
    const box = fs.existsSync(boxFile) ? (() => { try { return read(boxFile) } catch { return {} } })() : {}
    assert.equal(scored.box_type, box?.type ?? null)
    assert.equal(scored.box_started_utc, box?.started_utc ?? null)
    assert.equal(scored.card_sha256, sha(fs.readFileSync(path.join(r.control, 'card.json'))))
    assert.equal(scored.extract_sha256, read(path.join(r.control, 'card_extract_seal.json')).extract_sha256)
    assert.deepEqual(scored.predictions, record.predictions ?? null)
  })
  check(`${r.name}: card_scored.json rows: measured ${JSON.stringify(measured)}, decisions ${decisions.join(',')}`, () => {
    const scored = read(file)
    assert.deepEqual(scored.rows.map(row => row.id), record.required.map(item => item.id))
    assert.deepEqual(scored.rows.map(row => row.measured_value), measured)
    assert.deepEqual(scored.rows.map(row => row.decision), decisions)
    assert.deepEqual([scored.inputs_total, scored.measured_total, scored.holds_total, scored.refuted_total], totals)
    if (anchor === 'default') {
      assert.deepEqual(Object.keys(scored.anchor ?? {}).sort(), ['difference', 'measured_value', 'passed', 'published_value', 'tolerance'])
      assert.equal(scored.anchor.published_value, 0.4219)
      assert.deepEqual(scored.anchor.tolerance, { abs: 0.0137 })
      assert.equal(scored.anchor.measured_value, 0.425)
      assert.equal(scored.anchor.passed, true)
    } else assert.equal(scored.anchor, anchor)
  })
  check(`${r.name}: reproduce facts card_inputs..card_refuted = ${totals.join(',')}`, () => {
    const facts = r.stage('reproduce').facts
    assert.deepEqual(FOUR.map(key => facts[key]), totals)
  })
  if (status === 'PASS') check(`${r.name}: card rows never change reproduce: PASS, run_valid true`, () => {
    assert.equal(r.stage('reproduce').status, 'PASS')
    assert.equal(r.stage('reproduce').run_valid, true)
    assert.deepEqual([r.stage('reproduce').facts.anchors_passed, r.stage('reproduce').facts.anchors_total], [2, 2])
  })
}
// The extract seal: exactly {extract_sha256, sealed_utc} of the harness copy, written before the harness upload.
function extractSealChecks(r, wantBytes) {
  check(`${r.name}: control/card_extract_seal.json exactly {extract_sha256, sealed_utc} of agent/harness/card_extract.json`, () => {
    const seal = read(path.join(r.control, 'card_extract_seal.json'))
    assert.deepEqual(Object.keys(seal).sort(), ['extract_sha256', 'sealed_utc'])
    const bytes = fs.readFileSync(path.join(r.agent, 'harness', 'card_extract.json'))
    assert.ok(bytes.equals(Buffer.from(wantBytes)), 'agent/harness/card_extract.json bytes differ from the written/copied file')
    assert.equal(seal.extract_sha256, sha(bytes))
    assert.ok(Number.isFinite(Date.parse(seal.sealed_utc)), 'sealed_utc')
  })
  check(`${r.name}: the extract seal exists before the harness upload`, () => {
    const at = r.boxLog.findIndex(entry => entry.harness)
    assert.ok(at > 0, `no harness on the box: ${JSON.stringify(r.boxLog)}`)
    assert.equal(r.boxLog[at - 1].extract_seal, true, 'the command that uploaded the harness ran before the seal')
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

// ---- launch.js: pipeline_commit in a dry m5 launch's args.json --------------------------------------------
async function launchChecks() {
  if (ONLY && !ONLY.test('launch')) return
  const runRoot = path.join(scratch, 'launch')
  fs.mkdirSync(runRoot, { recursive: true })
  const brief = path.join(scratch, 'launch-brief.md')
  fs.writeFileSync(brief, '# Card test brief\nNo experiment directory or model is needed.\n')
  const realLedger = path.join(ROOT, 'm5', 'raids_used.jsonl')
  const realBefore = fs.existsSync(realLedger) ? fs.readFileSync(realLedger) : null
  const stderrFile = path.join(scratch, 'launch-stderr.log')
  const stdout = fs.openSync(path.join(scratch, 'launch-stdout.log'), 'w'), stderr = fs.openSync(stderrFile, 'w')
  let child
  try {
    child = await new Promise(resolve => {
      const proc = spawn(process.execPath, [path.join(ROOT, 'launch.js'), 'stage', '--stage', 'm5', '--run-root', runRoot,
        '--brief', brief, '--raid', 'card-test', '--dry-run'], { cwd: ROOT, timeout: 600000, stdio: ['ignore', stdout, stderr],
        env: { ...process.env, M5_RAIDS_LEDGER: path.join(scratch, 'launch-raids.jsonl'), WF_STUB: path.join(ROOT, 'tools', 'e2e_wf.js') } })
      let error
      proc.on('error', value => { error = value })
      proc.on('close', (status, signal) => resolve({ status, signal, error }))
    })
  } finally { fs.closeSync(stdout); fs.closeSync(stderr) }
  check('launch: launch.js stage --stage m5 --dry-run exits 0; the real raid ledger unchanged', () => {
    assert.ifError(child.error)
    assert.equal(child.status, 0, fs.readFileSync(stderrFile, 'utf8').slice(-800))
    assert.deepEqual(fs.existsSync(realLedger) ? fs.readFileSync(realLedger) : null, realBefore)
  })
  check('launch: args.json carries pipeline_commit, the short commit RUN.md records, or null', () => {
    const out = path.join(runRoot, 'agent', 'wf')
    const args = read(path.join(out, 'args.json'))
    assert.ok(Object.hasOwn(args, 'pipeline_commit'), 'args.json lacks pipeline_commit')
    const commit = args.pipeline_commit
    assert.ok(commit === null || (typeof commit === 'string' && /^[0-9a-f]{4,40}$/.test(commit)), `pipeline_commit ${JSON.stringify(commit)}`)
    if (commit !== null) assert.ok(fs.readFileSync(path.join(out, 'RUN.md'), 'utf8').includes(commit), 'RUN.md does not record that commit')
  })
}

async function main() {
  try {
    for (const directory of ['m5', 'idea', 'measure']) fs.cpSync(path.join(ROOT, directory), path.join(pipeline, directory), {
      recursive: true, filter: source => !['experiments', 'raids_used.jsonl'].includes(path.basename(source)),
    })
    const card = ({ result }) => ({ result, key: RECORD.key })

    // 1. Invalid args.card: intake fails with parse before any agent call.
    const badRecord = (change) => ({ result: withRecord(change), card })
    const invalid = [
      ['args-card-string', { card: () => 'R1:physical:W1' }],
      ['args-card-array', { card: ({ result }) => [result, RECORD.key] }],
      ['args-card-number', { card: () => 3 }],
      ['args-missing-result', { card: () => ({ key: RECORD.key }) }],
      ['args-missing-key', { card: ({ result }) => ({ result }) }],
      ['args-extra-key', { card: ({ result }) => ({ result, key: RECORD.key, note: 'x' }) }],
      ['args-empty-result', { card: () => ({ result: '', key: RECORD.key }) }],
      ['args-empty-key', { card: ({ result }) => ({ result, key: '' }) }],
      ['args-key-not-string', { card: ({ result }) => ({ result, key: 7 }) }],
      ['args-result-not-string', { card: () => ({ result: 7, key: RECORD.key }) }],
      ['result-missing', { resultKind: 'missing', card }],
      ['result-directory', { resultKind: 'directory', card }],
      ['result-not-json', { result: '{"calibration": [', card }],
      ['result-no-calibration', { result: { table: '' }, card }],
      ['no-matching-record', { card: ({ result }) => ({ result, key: 'R9:none:W9' }) }],
      ['state-calibrated', badRecord(record => ({ ...record, state: 'calibrated' }))],
      ['state-not-judged', badRecord(record => ({ ...record, state: 'not_judged' }))],
      ['state-no-unmeasured-input', badRecord(record => ({ ...record, state: 'no_unmeasured_input' }))],
      ['required-empty', badRecord(record => ({ ...record, required: [] }))],
      ['required-missing', badRecord(record => { delete record.required; return record })],
      ['required-not-array', badRecord(record => ({ ...record, required: { steps_per_h: 1 } }))],
      ['id-uppercase', badRecord(record => { record.required[1].id = 'Warmup_s'; return record })],
      ['id-too-long', badRecord(record => { record.required[1].id = 'w' + 'x'.repeat(31); return record })],
      ['id-leading-digit', badRecord(record => { record.required[1].id = '1warmup'; return record })],
      ['id-duplicate', badRecord(record => { record.required[1].id = 'steps_per_h'; return record })],
      ['id-not-string', badRecord(record => { record.required[1].id = 5; return record })],
      ['basis-cited', badRecord(record => { record.required[0].basis = 'CITED'; return record })],
      ['basis-measured', badRecord(record => { record.required[0].basis = 'MEASURED'; return record })],
      ['basis-missing', badRecord(record => { delete record.required[0].basis; return record })],
      ['bands-array', { card: ({ result }) => ({ result, key: RECORD.key, bands: [] }) }],
      ['bands-unknown-id', { card: ({ result }) => ({ result, key: RECORD.key, bands: { other_x: { abs: 1 } } }) }],
      ['bands-zero', { card: ({ result }) => ({ result, key: RECORD.key, bands: { warmup_s: { abs: 0 } } }) }],
      ['bands-negative', { card: ({ result }) => ({ result, key: RECORD.key, bands: { warmup_s: { abs: -1 } } }) }],
      ['bands-string', { card: ({ result }) => ({ result, key: RECORD.key, bands: { warmup_s: { abs: '1' } } }) }],
      ['bands-rel', { card: ({ result }) => ({ result, key: RECORD.key, bands: { warmup_s: { rel: 0.5 } } }) }],
      ['bands-extra-key', { card: ({ result }) => ({ result, key: RECORD.key, bands: { warmup_s: { abs: 1, rel: 1 } } }) }],
      ['bands-null-value', { card: ({ result }) => ({ result, key: RECORD.key, bands: { warmup_s: null } }) }],
      ['with-units-check', { card, unitsCheck: true }],
      ['with-units-probe', { card, unitsProbe: true }],
    ]
    for (const r of await inParallel(invalid.map(([name, spec]) => () => execute(`invalid-${name}`, spec)))) intakeParse(r)

    // 2. Baselines without args.card, then the main card run (harness_from) and a generated-harness card run.
    const [plain, plainGenerated] = await inParallel([
      () => execute('no-card', {}),
      () => execute('no-card-generated', { generated: true }),
    ])
    for (const r of [plain, plainGenerated].filter(Boolean)) {
      statuses(r, ALL_PASS)
      nullFacts(r, 'outside card mode')
      check(`${r.name}: no card file; no prompt names card_inputs.json or card_extract.json`, () => {
        for (const file of ['control/card.json', 'control/card_seal.json', 'agent/card_inputs.json', 'control/card_extract_seal.json', 'control/card_scored.json'])
          assert.equal(fs.existsSync(path.join(r.root, file)), false, file)
        for (const call of r.calls) assert.ok(!/card_inputs|card_extract/.test(call.prompt), `${call.label} prompt mentions card files`)
      })
      plainRunRecord(r)
    }

    const [main, generated, launchBands, noAnchor] = await inParallel([
      () => execute('card-reuse', { card, clobberResult: true }),
      () => execute('card-generated', { card, generated: true }),
      () => execute('card-launch-bands', { card: ({ result }) => ({ result: path.relative(pipeline, result), key: RECORD.key,
        bands: { mem_gb: { abs: 500 }, idle_frac: { abs: 0.0419 } } }), commit: 'c0ffee1' }),
      () => execute('card-no-anchor', { result: withRecord(record => ({ ...record, anchor: { absent_reason: 'nothing published' },
        required: [...record.required, { id: 'z' + 'q'.repeat(30), basis: 'GUESS', value: 3, measured_by: 'P1', phase: { id: 'P1' } }] })),
      card, extract: { rules: [...RULES.slice(0, 4), { id: 'z' + 'q'.repeat(30), file: 'card/metrics.json', kind: 'json', expr: '/mem/gb' }] } }),
    ])
    if (main) {
      // clobberResult: the stub replaced result.json during intake; the card was read before, from the original bytes.
      main.resultSha = sha(Buffer.from(JSON.stringify(RESULT, null, 1) + '\n'))
      statuses(main, ALL_PASS)
      cardFileChecks(main)
      promptChecks(main, plain)
      extractSealChecks(main, main.extractText)
      check('card-reuse: harness_from copies card_extract.json with its exact bytes', () => {
        assert.ok(fs.readFileSync(path.join(main.agent, 'harness', 'card_extract.json')).equals(fs.readFileSync(path.join(main.source, 'card_extract.json'))))
      })
      // After the intake call result.json no longer holds the record: scoring read control/card.json.
      scoredChecks(main, { decisions: ['holds', 'holds', 'refuted', 'not_measured'], measured: [6100, 13, 200, null], totals: [4, 3, 2, 1] })
      noCardInAgentFiles(main)
      check('card-reuse: the refuted mem_gb row was decided by its band, steps_per_h by its gate', () => {
        const scored = read(path.join(main.control, 'card_scored.json'))
        assert.deepEqual(scored.rows.map(row => [row.decided_by, row.band_source]),
          [['gate', 'multiplicative'], ['band', 'card'], ['band', 'multiplicative'], [null, 'multiplicative']])
      })
    }
    if (generated) {
      statuses(generated, ALL_PASS)
      cardFileChecks(generated)
      promptChecks(generated, plainGenerated)
      extractSealChecks(generated, generated.extractText)
      scoredChecks(generated, { decisions: ['holds', 'holds', 'refuted', 'not_measured'], measured: [6100, 13, 200, null], totals: [4, 3, 2, 1] })
      noCardInAgentFiles(generated)
      check('card-generated: harness prompt names card_inputs.json and harness/card_extract.json and forbids scripts computing card values', () => {
        const harness = generated.calls.find(call => call.label === 'harness')
        assert.ok(harness, 'no harness call')
        assert.match(harness.prompt, /card_inputs\.json/)
        assert.match(harness.prompt, /card_extract\.json/)
        assert.match(harness.prompt, /\banchor\b/)
        const at = harness.prompt.indexOf('card_extract.json')
        // Meaning, not wording: e.g. "no harness script computes, writes or asserts a value for these inputs".
        assert.match(harness.prompt, /(never|not|no)\b[^.\n]{0,120}\b(comput|writ|assert)\w*[^.\n]{0,80}\b(card|inputs?)\b/i,
          `card wording: ${harness.prompt.slice(at, at + 1400)}`)
      })
    }
    if (launchBands) {
      statuses(launchBands, ALL_PASS)
      cardFileChecks(launchBands, { bands: { mem_gb: { abs: 500 }, idle_frac: { abs: 0.0419 } } })
      promptChecks(launchBands, plain)
      scoredChecks(launchBands, { decisions: ['holds', 'holds', 'holds', 'not_measured'], measured: [6100, 13, 200, null], totals: [4, 3, 3, 0], commit: 'c0ffee1' })
      noCardInAgentFiles(launchBands, { mem_gb: { abs: 500 }, idle_frac: { abs: 0.0419 } })
      check('card-launch-bands: launch bands decide (band_source launch)', () => {
        const scored = read(path.join(launchBands.control, 'card_scored.json'))
        assert.deepEqual(scored.rows.map(row => row.band_source), ['multiplicative', 'card', 'launch', 'launch'])
      })
    }
    if (noAnchor) {
      const record = withRecord(record => ({ ...record, anchor: { absent_reason: 'nothing published' },
        required: [...record.required, { id: 'z' + 'q'.repeat(30), basis: 'GUESS', value: 3, measured_by: 'P1', phase: { id: 'P1' } }] })).calibration[1]
      statuses(noAnchor, ALL_PASS)
      cardFileChecks(noAnchor, { record })
      scoredChecks(noAnchor, { record, decisions: ['holds', 'holds', 'refuted', 'not_measured', 'refuted'], measured: [6100, 13, 200, null, 200],
        totals: [5, 4, 2, 2], anchor: null })
      noCardInAgentFiles(noAnchor)
    }

    // 3. card_extract.json missing or invalid: reproduce fails with parse before the harness upload.
    const rules = (...list) => ({ rules: list })
    const badExtract = [
      ['extract-missing', null],
      ['extract-not-json', '{"rules": ['],
      ['extract-extra-top-key', { rules: RULES, note: 'x' }],
      ['extract-too-few-rules', rules(...RULES.slice(0, 3), RULES[4])],
      ['extract-wrong-order', rules(RULES[1], RULES[0], ...RULES.slice(2))],
      ['extract-no-anchor-rule', rules(...RULES.slice(0, 4))],
      ['extract-extra-rule-key', rules({ ...RULES[0], note: 'x' }, ...RULES.slice(1))],
      ['extract-dotdot', rules({ ...RULES[0], file: 'card/../metrics.json' }, ...RULES.slice(1))],
      ['extract-absolute', rules({ ...RULES[0], file: '/tmp/metrics.json' }, ...RULES.slice(1))],
      ['extract-unknown-kind', rules({ ...RULES[0], kind: 'jq' }, ...RULES.slice(1))],
      ['extract-two-groups', rules(RULES[0], { ...RULES[1], expr: '(warmup)_s=([0-9.]+)' }, ...RULES.slice(2))],
      ['extract-bad-regex', rules(RULES[0], { ...RULES[1], expr: 'warmup_s=([0-9.]+' }, ...RULES.slice(2))],
      ['extract-bad-pointer', rules({ ...RULES[0], expr: 'throughput/steps_per_h' }, ...RULES.slice(1))],
    ]
    for (const r of await inParallel(badExtract.map(([name, extract]) => () => execute(name, { card, extract }))))
      if (r) { extractParse(r); check(`${r.name}: card files still written before intake`, () => assert.ok(fs.existsSync(path.join(r.control, 'card_seal.json')))) }
    extractParse(await execute('extract-missing-generated', { card, generated: true, extract: null }), true)

    // 4. Scoring around the anchors step.
    const [anchorsFail, anchorsNonzero, scoreFails, repairTamper, stubReproduce] = await inParallel([
      // Scoring runs before anchor scoring and whatever the anchors score.
      () => execute('card-anchors-out-of-tolerance', { card, measured: { first: 150, second: 0 } }),
      // run_anchors.sh exits nonzero: no scoring.
      () => execute('card-anchors-nonzero', { card, anchorsRc: 3 }),
      // The sealed card changes on the box before scoring: the seal check fails scoring (parse).
      () => execute('card-score-seal-mismatch', { card, setupTamper: true }),
      // Generated harness; anchors fail once; the anchors repair also rewrites card_extract.json.
      () => execute('card-repair-rewrites-extract', { card, generated: true, anchorsFailures: 1, fixtureRepairs: true,
        repairTamper: rules({ ...RULES[0], expr: '/mem/gb' }, ...RULES.slice(1)) }),
      // A stub reproduce record in card mode.
      () => execute('card-stub-reproduce', { card, stub: { reproduce: 'PASS' } }),
    ])
    if (anchorsFail) {
      statuses(anchorsFail, failedAt('reproduce'))
      errorClass(anchorsFail, 'reproduce', 'anchor')
      scoredChecks(anchorsFail, { decisions: ['holds', 'holds', 'refuted', 'not_measured'], measured: [6100, 13, 200, null], totals: [4, 3, 2, 1], status: 'FAIL' })
    }
    if (anchorsNonzero) {
      statuses(anchorsNonzero, failedAt('reproduce'))
      check('card-anchors-nonzero: no card_scored.json when run_anchors.sh exits nonzero', () =>
        assert.equal(fs.existsSync(path.join(anchorsNonzero.control, 'card_scored.json')), false))
      nullFacts(anchorsNonzero, 'no card_scored.json')
    }
    if (scoreFails) {
      statuses(scoreFails, failedAt('reproduce'))
      errorClass(scoreFails, 'reproduce', 'parse')
      check('card-score-seal-mismatch: no card_scored.json', () => assert.equal(fs.existsSync(path.join(scoreFails.control, 'card_scored.json')), false))
      nullFacts(scoreFails, 'scoring failed')
    }
    if (repairTamper) {
      statuses(repairTamper, ALL_PASS)
      check('card-repair-rewrites-extract: an anchors repair ran (fixture sanity)', () =>
        assert.equal(repairTamper.calls.filter(call => call.label === 'anchors-repair').length, 1))
      extractSealChecks(repairTamper, repairTamper.extractText)
      // The original mem_gb rule held: no repair changes card_extract.json.
      scoredChecks(repairTamper, { decisions: ['holds', 'holds', 'refuted', 'not_measured'], measured: [6100, 13, 200, null], totals: [4, 3, 2, 1] })
    }
    if (stubReproduce) {
      cardFileChecks(stubReproduce, { noBox: true })
      noCardInAgentFiles(stubReproduce)
      nullFacts(stubReproduce, 'stub')
    }

    await launchChecks()
  } catch (error) { failures++; console.log(`FAIL test harness: ${error.stack}`) }
  finally {
    if (process.argv[3] === 'keep') console.log(`scratch kept: ${scratch}`)
    else fs.rmSync(scratch, { recursive: true, force: true })
  }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : `all ${checks} checks passed`)
  process.exitCode = failures ? 1 : 0
}
main()
