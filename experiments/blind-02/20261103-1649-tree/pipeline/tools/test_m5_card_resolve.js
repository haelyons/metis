#!/usr/bin/env node
'use strict'

// Black-box contract tests for `node m5/card_resolve.js` (U56): m5/SCHEMAS.md "Card write-back and re-judging
// (U56)", with the card records of "Card calibration (U54)" and the `calibration` record of CONTRACT.md (U55).
// Never inspect m5/card_resolve.js, src/ or git history. Every run root is built by hand (control/card.json,
// card_seal.json and card_scored.json in their contract shapes); the tool is run as a program and only its exit
// status, its output file and the files around it are read.
// Usage: node tools/test_m5_card_resolve.js
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const crypto = require('node:crypto')
const assert = require('node:assert/strict')
const { spawnSync } = require('node:child_process')

const ROOT = path.resolve(__dirname, '..')
const TOOL = path.join(ROOT, 'm5', 'card_resolve.js')
const PLAN = JSON.parse(fs.readFileSync(path.join(ROOT, 'tests/fixtures/gates/plan.json'), 'utf8'))
const SHEET = JSON.parse(fs.readFileSync(path.join(ROOT, 'tests/fixtures/cost/price_sheet.json'), 'utf8'))
const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_card_resolve_'))
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex')
const clone = value => JSON.parse(JSON.stringify(value))
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'))
let checks = 0, failures = 0
function check(label, test) {
  checks++
  try { test(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${String(error.message).replace(/\s*\n\s*/g, ' ').slice(0, 1500)}`) }
}
function writeJSON(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  const bytes = Buffer.from(JSON.stringify(value, null, 1) + '\n')
  fs.writeFileSync(file, bytes)
  return bytes
}
// Relative path -> base64 bytes of every regular file under a directory.
function contents(directory) {
  const result = {}
  const visit = (parent, prefix) => {
    for (const entry of fs.readdirSync(parent, { withFileTypes: true })) {
      const file = path.join(parent, entry.name)
      if (entry.isDirectory()) visit(file, prefix + entry.name + '/')
      else result[prefix + entry.name] = fs.readFileSync(file).toString('base64')
    }
  }
  if (fs.existsSync(directory)) visit(directory, '')
  return result
}
function near(actual, expected, label) {
  assert.ok(typeof actual === 'number' && Math.abs(actual - expected) <= 1e-6 * Math.max(1, Math.abs(expected)),
    `${label}: ${actual} != ${expected}`)
}

// ---- The tree result (CONTRACT.md `calibration` in the return) --------------------------------------------
// A: the fixture plan's load-bearing PROXY `steps_per_h`, with a hand-built `judged` for re-judging.
// Its cost: pilot 2 h + sweep 126000 / steps_per_h h, both at 8 x 3.99 $/h (the price sheet's 8x H100 rate).
const RATE = 8 * 3.99
const planned = stepsPerHour => RATE * 2 + RATE * 126000 / stepsPerHour
const required = (id, basis, value, extra = {}) => ({ id, name: `name of ${id}`, unit: `unit of ${id}`, band: null, basis, value,
  differs_in: basis === 'PROXY' ? ['model size'] : [], measured_by: 'P1', cum_spend_through_measured_by: 63.84, k_budget: 1.04,
  phase: { id: 'P1', what: 'pilot: throughput and reproduction' }, line: 'pilot', ...extra })
const JUDGED = {
  plan: clone(PLAN),
  pick: { key: 'R1:physical:W1', root: 'R1', branch: 'physical', kind: 'top', rank: 1, total: 24, tie_note: null, replaced: [],
    title: PLAN.option_title },
  given: { budget_usd: 1000, price_sheet: SHEET, budget_covers_storage: true, budget_covers_tax: true },
  gate_args: { budget_usd: 1000, require_compute_lever: { physical: true, interp: true }, picks_per_branch: 2, pool_k: 2 },
}
const REC_A = { key: 'R1:physical:W1', title: PLAN.option_title, state: 'calibration_required', plan_usd: planned(5000),
  required: [required('steps_per_h', 'PROXY', 5000, { phase: clone(PLAN.phases[0]) })], resolved: [],
  anchor: clone(PLAN.anchor), predictions: clone(PLAN.predictions), judged: JUDGED }
// B: two required ids, judged null (rejudged null).
const REC_B = { key: 'R2:interp:W3', title: 'bravo basalt probe', state: 'calibration_required', plan_usd: 412.5,
  required: [required('a_rate', 'PROXY', 40), required('b_lat', 'GUESS', 2.5, { measured_by: 'P2' })], resolved: [],
  anchor: { absent_reason: 'no published value' }, predictions: { if_lever: 'x 5', if_not: 'y 2' }, judged: null }
// D: a record without the `judged` key at all.
const REC_D = { key: 'R3:physical:W2', title: 'delta quartz flow', state: 'calibration_required', plan_usd: 99,
  required: [required('c_frac', 'GUESS', 0.3)], resolved: [], anchor: null, predictions: null }
// C and E: records no run names.
const REC_C = { key: 'seed:idea:seed', title: 'an idea from the human', state: 'no_unmeasured_input', plan_usd: 10, required: [],
  resolved: [], anchor: null, predictions: null, judged: null }
const REC_E = { key: 'R1:interp:W4', title: 'rejected one', state: 'rejected', plan_usd: null, required: [], resolved: [],
  anchor: null, predictions: null, judged: null }
const RESULT = { table: '| Pick | Result |', cards: ['card one', 'card two'], inventory: [], frontier: '', log: ['x'],
  result_md: '# r', price_sheet: SHEET, calibration: [REC_A, REC_B, REC_C, REC_D, REC_E] }

// ---- Hand-built run roots ---------------------------------------------------------------------------------
// rows: [{ id, measured, verdict, decision, decided_by?, rule? }] for the record's `required` ids.
function scoredRow(record, spec) {
  const item = record.required.find(entry => entry.id === spec.id) ?? { id: spec.id, name: null, unit: null, basis: 'GUESS', value: 1 }
  const decidedBy = spec.decided_by !== undefined ? spec.decided_by
    : ['holds', 'refuted'].includes(spec.decision) ? 'band' : null
  return { id: spec.id, name: item.name ?? null, unit: item.unit ?? null, basis: item.basis, value: item.value,
    band_source: 'multiplicative', band_lo: 1, band_hi: 100000, measured_value: spec.measured, verdict: spec.verdict,
    gate_passed: decidedBy === 'gate' ? spec.decision === 'holds' : null, decided_by: decidedBy, decision: spec.decision,
    rule: spec.rule ?? { file: `card/${spec.id}.json`, kind: 'json', expr: `/value/${spec.id}` } }
}
// opts: { record, rows, run, commit, box: {type, started_utc} | null, result (file), bands }
function makeRun(dir, opts) {
  const control = path.join(dir, 'control')
  const resultBytes = fs.readFileSync(opts.result)
  const card = { source: opts.result, source_sha256: sha(resultBytes), record: opts.record, bands: opts.bands ?? {} }
  const cardBytes = writeJSON(path.join(control, 'card.json'), card)
  writeJSON(path.join(control, 'card_seal.json'), { card_sha256: sha(cardBytes), sealed_utc: '2026-11-03T10:00:00Z' })
  const rows = opts.rows.map(spec => scoredRow(opts.record, spec))
  const box = opts.box === undefined ? { type: 'gpu_1x_a10', started_utc: '2026-11-03T09:00:00Z' } : opts.box
  writeJSON(path.join(control, 'card_scored.json'), { key: opts.record.key, run: opts.run, pipeline_commit: opts.commit ?? null,
    box_type: box?.type ?? null, box_started_utc: box?.started_utc ?? null, card_sha256: sha(cardBytes),
    extract_sha256: 'e'.repeat(64), predictions: opts.record.predictions ?? null, anchor: null, rows,
    inputs_total: rows.length, measured_total: rows.filter(row => typeof row.measured_value === 'number').length,
    holds_total: rows.filter(row => row.decision === 'holds').length, refuted_total: rows.filter(row => row.decision === 'refuted').length })
  // Box and agent files a real run also holds; the tool reads only control/.
  writeJSON(path.join(control, 'box.json'), box ?? {})
  writeJSON(path.join(dir, 'agent', 'card_inputs.json'), { inputs: [], anchor: null })
  return { dir, rows, run: opts.run, commit: opts.commit ?? null, box, record: opts.record }
}
// The entry the contract writes for one scored row of one run.
function entryFor(run, row) {
  const box = run.box
  return { run: run.run, pipeline_commit: run.commit, box_type: box?.type ?? null, box_started_utc: box?.started_utc ?? null,
    id: row.id, measured_value: row.measured_value, verdict: row.verdict, decided_by: row.decided_by, decision: row.decision,
    number: row.measured_value === null ? null : { id: row.id, name: row.name, unit: row.unit, basis: 'MEASURED',
      value: row.measured_value, differs_in: [], command: 'bash harness/run_command.sh',
      output: `${path.basename(run.dir)}/agent/results/reproduce/out/${row.rule.file}`,
      output_line: `${row.rule.kind}: ${row.rule.expr}`, machine: box?.type ?? null } }
}

// ---- Running the tool -------------------------------------------------------------------------------------
let caseNumber = 0
function setup(name, resultValue = RESULT) {
  const dir = path.join(scratch, `${String(++caseNumber).padStart(2, '0')}-${name}`)
  fs.mkdirSync(dir, { recursive: true })
  const result = path.join(dir, 'tree run', 'result.json')
  const resultBytes = writeJSON(result, resultValue)
  return { dir, result, resultBytes, outDir: path.join(dir, 'resolved'), out: path.join(dir, 'resolved', 'calibration.json') }
}
function resolve(argv, cwd = ROOT) {
  const proc = spawnSync(process.execPath, [TOOL, ...argv], { cwd, encoding: 'utf8', timeout: 60000 })
  return { status: proc.status, stdout: proc.stdout ?? '', stderr: proc.stderr ?? '', error: proc.error }
}
const why = r => `exit ${r.status}; ${(r.stderr || '').slice(-800)}${r.error ? ` ${r.error.message}` : ''}`
// A successful run: exit 0, exact top level, result.json and every input unchanged, only the output written.
function okRun(name, c, runs, argv = null, cwd = ROOT) {
  const inputs = Object.fromEntries(runs.map(run => [run.dir, contents(run.dir)]))
  fs.mkdirSync(c.outDir, { recursive: true })
  const r = resolve(argv ?? [c.result, ...runs.map(run => run.dir), '--out', c.out], cwd)
  check(`${name}: exit 0 and the output written`, () => {
    assert.ifError(r.error)
    assert.equal(r.status, 0, why(r))
    assert.ok(fs.existsSync(c.out), 'no output file')
  })
  check(`${name}: result.json bytes and every run root unchanged; only the output file written`, () => {
    assert.ok(fs.readFileSync(c.result).equals(c.resultBytes), 'result.json changed')
    for (const run of runs) assert.deepEqual(contents(run.dir), inputs[run.dir], `${run.dir} changed`)
    assert.deepEqual(fs.readdirSync(c.outDir), ['calibration.json'], 'stray file next to the output')
  })
  const value = fs.existsSync(c.out) ? read(c.out) : null
  if (value) check(`${name}: exactly {source, source_sha256, calibration}; source absolute, SHA-256 of result.json`, () => {
    assert.deepEqual(Object.keys(value).sort(), ['calibration', 'source', 'source_sha256'])
    assert.equal(value.source, c.result, 'source is not the absolute path of result.json')
    assert.equal(value.source_sha256, sha(c.resultBytes))
    assert.ok(Array.isArray(value.calibration) && value.calibration.length === RESULT.calibration.length, 'calibration length')
  })
  return value
}
// Records no run names stay exactly as in result.json.
function unchangedOthers(name, value, named) {
  if (!value) return
  check(`${name}: records no run names are unchanged (${RESULT.calibration.filter(rec => !named.includes(rec.key)).map(rec => rec.key).join(', ')})`, () => {
    RESULT.calibration.forEach((record, i) => {
      if (!named.includes(record.key)) assert.deepEqual(value.calibration[i], record, record.key)
    })
  })
}
// A named record: every original field unchanged except `state` and `resolved`, plus `rejudged`.
function namedRecord(name, value, original, { entries, state, judged = true }) {
  if (!value) return null
  const record = value.calibration[RESULT.calibration.findIndex(rec => rec.key === original.key)]
  check(`${name}: ${original.key}: resolved entries (existing first, then runs in argument order)`, () => {
    assert.deepEqual(record.resolved, entries)
  })
  check(`${name}: ${original.key}: state ${state}`, () => assert.equal(record.state, state))
  check(`${name}: ${original.key}: other fields unchanged; ${judged ? 'rejudged present' : 'rejudged null'}`, () => {
    const { resolved, state: _s, rejudged, ...rest } = record
    const { resolved: _r, state: _o, ...want } = original
    assert.deepEqual(rest, want)
    assert.ok(Object.hasOwn(record, 'rejudged'), 'named record lacks rejudged')
    if (!judged) assert.equal(rejudged, null)
  })
  return record
}
// An exit-1 case: nothing written (no output, no stray file), inputs unchanged.
function refused(name, c, runs, argv, { outIsInput = null } = {}) {
  const inputs = Object.fromEntries(runs.map(run => [run.dir, contents(run.dir)]))
  fs.mkdirSync(c.outDir, { recursive: true })
  const before = contents(c.outDir)
  const r = resolve(argv)
  check(`${name}: exit 1 and nothing written`, () => {
    assert.ifError(r.error)
    assert.equal(r.status, 1, why(r))
    if (!outIsInput) assert.equal(fs.existsSync(c.out), false, 'output written')
    assert.deepEqual(contents(c.outDir), before, 'files written next to the output')
    assert.ok(fs.readFileSync(c.result).equals(c.resultBytes), 'result.json changed')
    for (const run of runs) assert.deepEqual(contents(run.dir), inputs[run.dir], `${run.dir} changed`)
  })
}

function main() {
  try {
    assert.ok(fs.existsSync(TOOL), 'm5/card_resolve.js missing')

    // 1. One run naming B: one entry per scored row; a measured and an unmeasured row; state unchanged.
    {
      const c = setup('one-run')
      const run = makeRun(path.join(c.dir, 'run-one'), { result: c.result, record: REC_B, run: 'blind-02-run1', commit: 'abc1234',
        rows: [{ id: 'a_rate', measured: 44.5, verdict: 'within_band', decision: 'holds' },
          { id: 'b_lat', measured: null, verdict: 'not_measured', decision: 'not_measured' }] })
      const value = okRun('one-run', c, [run])
      namedRecord('one-run', value, REC_B, { entries: run.rows.map(row => entryFor(run, row)), state: 'calibration_required', judged: false })
      unchangedOthers('one-run', value, [REC_B.key])
      if (value) check('one-run: MEASURED number fields (literal)', () => {
        const [measured, unmeasured] = value.calibration[1].resolved
        assert.deepEqual(measured.number, { id: 'a_rate', name: 'name of a_rate', unit: 'unit of a_rate', basis: 'MEASURED', value: 44.5,
          differs_in: [], command: 'bash harness/run_command.sh', output: 'run-one/agent/results/reproduce/out/card/a_rate.json',
          output_line: 'json: /value/a_rate', machine: 'gpu_1x_a10' })
        assert.equal(unmeasured.number, null)
        assert.deepEqual(Object.keys(measured).sort(), ['box_started_utc', 'box_type', 'decided_by', 'decision', 'id', 'measured_value',
          'number', 'pipeline_commit', 'run', 'verdict'])
      })
    }

    // 2. Several runs, argument order; regex rule; null box and commit; run root basename with a space.
    {
      const c = setup('several-runs')
      const second = makeRun(path.join(c.dir, 'run two'), { result: c.result, record: REC_B, run: 'r2', commit: null, box: null,
        rows: [{ id: 'a_rate', measured: 41, verdict: 'within_band', decision: 'holds' },
          { id: 'b_lat', measured: 2.75, verdict: 'within_band', decision: 'holds',
            rule: { file: 'logs/run.log', kind: 'regex', expr: 'latency=([0-9.]+)' } }] })
      const first = makeRun(path.join(c.dir, 'run-one'), { result: c.result, record: REC_B, run: 'r1', commit: 'abc',
        rows: [{ id: 'a_rate', measured: 39, verdict: 'within_band', decision: 'holds' },
          { id: 'b_lat', measured: 9, verdict: 'not_measured', decision: 'undecidable', decided_by: null }] })
      // Argument order: the second-built run first.
      const value = okRun('several-runs', c, [second, first])
      namedRecord('several-runs', value, REC_B, {
        entries: [...second.rows.map(row => entryFor(second, row)), ...first.rows.map(row => entryFor(first, row))],
        state: 'calibrated', judged: false })
      unchangedOthers('several-runs', value, [REC_B.key])
      if (value) check('several-runs: regex output_line, null machine, basename with a space (literal)', () => {
        const number = value.calibration[1].resolved[1].number
        assert.equal(number.output_line, 'regex: latency=([0-9.]+)')
        assert.equal(number.output, 'run two/agent/results/reproduce/out/logs/run.log')
        assert.equal(number.machine, null)
        assert.equal(value.calibration[1].resolved[1].pipeline_commit, null)
      })
    }

    // 3. State rules, from every entry of every run (existing entries count; ids outside `required` do not).
    const existing = (id, decision, measured = null) => ({ run: 'earlier', pipeline_commit: null, box_type: null, box_started_utc: null,
      id, measured_value: measured, verdict: decision === 'holds' ? 'within_band' : decision === 'refuted' ? 'above_band' : 'not_measured',
      decided_by: ['holds', 'refuted'].includes(decision) ? 'band' : null, decision,
      // As card_resolve.js writes entries: a MEASURED number exactly when measured_value is a number.
      number: measured === null ? null : { id, name: `name of ${id}`, unit: `unit of ${id}`, basis: 'MEASURED', value: measured,
        differs_in: [], command: 'bash harness/run_command.sh', output: 'earlier/agent/results/reproduce/out/card/x.json',
        output_line: 'json: /x', machine: null } })
    const stateCases = [
      // [name, existing entries of B, runs: [[a decision, b decision], ...], expected state]
      ['state-any-refuted', [], [['holds', 'holds'], ['refuted', 'not_measured']], 'refuted'],
      ['state-refuted-over-all-holds', [], [['holds', 'refuted'], ['holds', 'holds']], 'refuted'],
      ['state-all-hold-across-runs', [], [['holds', 'not_measured'], ['undecidable', 'holds']], 'calibrated'],
      ['state-one-unheld-unchanged', [], [['holds', 'undecidable'], ['holds', 'not_measured']], 'calibration_required'],
      ['state-existing-refuted', [existing('b_lat', 'refuted', 9)], [['holds', 'holds']], 'refuted'],
      ['state-existing-holds', [existing('b_lat', 'holds', 2.5)], [['holds', 'not_measured']], 'calibrated'],
      ['state-existing-other-id-refuted', [existing('old_id', 'refuted', 1)], [['holds', 'holds']], 'calibrated'],
    ]
    const measuredFor = decision => decision === 'not_measured' ? null : decision === 'refuted' ? 999 : 3
    const verdictFor = decision => ({ holds: 'within_band', refuted: 'above_band', not_measured: 'not_measured', undecidable: 'no_band' })[decision]
    for (const [name, prior, decisions, state] of stateCases) {
      const result = clone(RESULT)
      result.calibration[1].resolved = prior
      const c = setup(name, result)
      const runs = decisions.map(([a, b], i) => makeRun(path.join(c.dir, `run-${i + 1}`), { result: c.result, record: result.calibration[1],
        run: `run-${i + 1}`, commit: `c${i}`, rows: [{ id: 'a_rate', measured: measuredFor(a), verdict: verdictFor(a), decision: a },
          { id: 'b_lat', measured: measuredFor(b), verdict: verdictFor(b), decision: b }] }))
      fs.mkdirSync(c.outDir, { recursive: true })
      const r = resolve([c.result, ...runs.map(run => run.dir), '--out', c.out])
      check(`${name}: exit 0`, () => assert.equal(r.status, 0, why(r)))
      if (!fs.existsSync(c.out)) continue
      const record = read(c.out).calibration[1]
      check(`${name}: state ${state}`, () => assert.equal(record.state, state))
      check(`${name}: existing entries kept first, then each run's rows`, () => assert.deepEqual(record.resolved,
        [...prior, ...runs.flatMap(run => run.rows.map(row => entryFor(run, row)))]))
    }

    // 4. Two runs naming different records in one call; D has no `judged` key: rejudged null.
    {
      const c = setup('two-records')
      const runB = makeRun(path.join(c.dir, 'run-b'), { result: c.result, record: REC_B, run: 'rb', commit: 'x',
        rows: [{ id: 'a_rate', measured: 120, verdict: 'above_band', decision: 'refuted' },
          { id: 'b_lat', measured: 2, verdict: 'within_band', decision: 'holds' }] })
      const runD = makeRun(path.join(c.dir, 'run-d'), { result: c.result, record: REC_D, run: 'rd', commit: 'y',
        rows: [{ id: 'c_frac', measured: 0.31, verdict: 'within_band', decision: 'holds' }] })
      const value = okRun('two-records', c, [runB, runD])
      namedRecord('two-records', value, REC_B, { entries: runB.rows.map(row => entryFor(runB, row)), state: 'refuted', judged: false })
      namedRecord('two-records', value, REC_D, { entries: runD.rows.map(row => entryFor(runD, row)), state: 'calibrated', judged: false })
      unchangedOthers('two-records', value, [REC_B.key, REC_D.key])
    }

    // 5. Re-judging A with its hand-built `judged`.
    // Expected gate outcomes, derived from CONTRACT.md (gates.js `gate_plan`, cost.js, §5 integration) rather than
    // from the implementation. The fixture plan passes every schema-level halt (both predictions differ, the decision
    // rule has a digit, levels 2000..32000, phases and sources present, compute_tested "yes") and has no expression
    // error, so the action is forced by the budget rule alone, with budget 1000 (judged.gate_args.budget_usd):
    //   planned <= 1000                              -> "ok", and then no reason (reasons explain a halt or a repair)
    //   planned > 1000 and total_stated (868.22) <= 1000 -> "repair"
    //   planned > 1000 and total_stated > 1000       -> "halt"
    // Reason strings are not stated in the contract, so for "repair"/"halt" only a non-empty list of strings is
    // required. `uncertain_after` is forced: the plan's only GUESS/PROXY input is steps_per_h (DESIGN and DERIVED
    // are never uncertain), so it is [] once steps_per_h is MEASURED and ["steps_per_h"] while it is not. A merge
    // that kept the PROXY basis would also keep the quote check ("about 5,000 ...") and fail it: "repair", not "ok".
    const gateFor = (median, totalStated = PLAN.cost.total_stated) => planned(median) <= 1000 ? 'ok'
      : totalStated <= 1000 ? 'repair' : 'halt'
    const rejudge = (name, measuredRuns, { prior = [], wantMedian, wantIds, mutate = null, wantAction = null }) => {
      const result = clone(RESULT)
      result.calibration[0].resolved = prior
      if (mutate) mutate(result.calibration[0])
      const c = setup(name, result)
      const runs = measuredRuns.map((measured, i) => makeRun(path.join(c.dir, `run-${i + 1}`), { result: c.result, record: result.calibration[0],
        run: `run-${i + 1}`, commit: `k${i}`, box: { type: `gpu_8x_h100_${i}`, started_utc: `2026-11-0${i + 1}T00:00:00Z` },
        rows: [{ id: 'steps_per_h', measured, verdict: measured === null ? 'not_measured' : 'within_band',
          decision: measured === null ? 'not_measured' : measured >= 3000 ? 'holds' : 'refuted', decided_by: measured === null ? null : 'gate' }] }))
      const value = okRun(name, c, runs)
      if (!value) return null
      const record = value.calibration[0]
      check(`${name}: rejudged has exactly {measured_ids, plan_usd_before, plan_usd_after, gate_action, gate_reasons, uncertain_after}`, () => {
        assert.ok(record.rejudged && typeof record.rejudged === 'object', `rejudged ${JSON.stringify(record.rejudged)}`)
        assert.deepEqual(Object.keys(record.rejudged).sort(), ['gate_action', 'gate_reasons', 'measured_ids', 'plan_usd_after',
          'plan_usd_before', 'uncertain_after'])
      })
      if (!record.rejudged) return record
      check(`${name}: measured_ids ${JSON.stringify(wantIds)}; plan_usd_before is the record's plan_usd`, () => {
        assert.deepEqual(record.rejudged.measured_ids, wantIds)
        assert.equal(record.rejudged.plan_usd_before, REC_A.plan_usd)
      })
      check(`${name}: plan_usd_after is the evaluation with steps_per_h = ${wantMedian}`, () => {
        near(record.rejudged.plan_usd_after, planned(wantMedian), 'plan_usd_after')
      })
      check(`${name}: gate_action and gate_reasons from gate_plan; uncertain_after a list of ids without a measured id`, () => {
        assert.ok(['halt', 'repair', 'ok'].includes(record.rejudged.gate_action), `gate_action ${record.rejudged.gate_action}`)
        assert.ok(Array.isArray(record.rejudged.gate_reasons), 'gate_reasons not an array')
        assert.ok(Array.isArray(record.rejudged.uncertain_after) && record.rejudged.uncertain_after.every(id => typeof id === 'string'),
          `uncertain_after ${JSON.stringify(record.rejudged.uncertain_after)}`)
        for (const id of wantIds) assert.ok(!record.rejudged.uncertain_after.includes(id), `${id} still uncertain after measurement`)
      })
      const action = wantAction ?? gateFor(wantMedian)
      check(`${name}: gate_action "${action}", gate_reasons and uncertain_after exactly as the contract forces them`, () => {
        assert.equal(record.rejudged.gate_action, action)
        if (action === 'ok') assert.deepEqual(record.rejudged.gate_reasons, [])
        else assert.ok(record.rejudged.gate_reasons.length > 0 && record.rejudged.gate_reasons.every(x => typeof x === 'string'),
          `gate_reasons ${JSON.stringify(record.rejudged.gate_reasons)}`)
        assert.deepEqual(record.rejudged.uncertain_after, wantIds.includes('steps_per_h') ? [] : ['steps_per_h'])
      })
      check(`${name}: entries for every run in argument order`, () => assert.deepEqual(record.resolved,
        [...prior, ...runs.flatMap(run => run.rows.map(row => entryFor(run, row)))]))
      return record
    }
    const one = rejudge('rejudge-one-run', [6300], { wantMedian: 6300, wantIds: ['steps_per_h'] })
    if (one) check('rejudge-one-run: a measured value that changes the cost changes plan_usd_after (literal 63.84 + 638.4)', () => {
      assert.notEqual(one.rejudged.plan_usd_after, one.rejudged.plan_usd_before)
      near(one.rejudged.plan_usd_after, 702.24, 'plan_usd_after (63.84 + 638.4)')
    })
    rejudge('rejudge-median-odd', [6000, 9000, 7000], { wantMedian: 7000, wantIds: ['steps_per_h'] })
    rejudge('rejudge-median-even', [6000, 7000], { wantMedian: 6500, wantIds: ['steps_per_h'] })
    rejudge('rejudge-median-with-existing-entry', [6000, 7000], { prior: [existing('steps_per_h', 'holds', 100000)], wantMedian: 7000,
      wantIds: ['steps_per_h'] })
    rejudge('rejudge-refuted-measurement', [2000], { wantMedian: 2000, wantIds: ['steps_per_h'] })
    const none = rejudge('rejudge-unmeasured', [null], { wantMedian: 5000, wantIds: [] })
    if (none) check('rejudge-unmeasured: nothing measured: the plan is evaluated unchanged', () => {
      near(none.rejudged.plan_usd_after, REC_A.plan_usd, 'plan_usd_after')
    })
    // judged.plan states a total over the budget: a measured cost over the budget halts; one within it does not.
    const statedOver = record => { record.judged.plan.cost.total_stated = 2500 }
    rejudge('rejudge-stated-over-measured-over', [2000], { wantMedian: 2000, wantIds: ['steps_per_h'], mutate: statedOver,
      wantAction: 'halt' })
    rejudge('rejudge-stated-over-measured-within', [6300], { wantMedian: 6300, wantIds: ['steps_per_h'], mutate: statedOver,
      wantAction: 'ok' })

    // 5b. Merging with two required ids whose `required` order (steps_per_h, eff) is not alphabetical order.
    // The judged plan's sweep hours are steps / steps_per_h / eff, so the evaluation shows which value each id took.
    // What the merged numbers look like inside the copied plan is not part of `rejudged`; the observable parts are the
    // medians (through plan_usd_after), measured_ids, and the MEASURED basis replacing PROXY/GUESS (uncertain_after,
    // and gate_action "ok": a kept PROXY basis with its quote "about 5,000 ..." would fail the quote check and repair).
    {
      const plan2 = clone(PLAN)
      plan2.numbers.splice(1, 0, { id: 'eff', name: 'step efficiency', unit: 'ratio', basis: 'GUESS', value: 2,
        rests_on: 'a guess from the pilot of a similar policy', measured_by: 'P1' })
      plan2.numbers.find(n => n.id === 't_main').expr = 'steps / steps_per_h / eff'
      const planned2 = (s, e) => RATE * 2 + RATE * 126000 / (s * e)
      const REC_F = { key: 'R4:physical:W5', title: plan2.option_title, state: 'calibration_required', plan_usd: planned2(5000, 2),
        required: [required('steps_per_h', 'PROXY', 5000, { phase: clone(PLAN.phases[0]) }),
          required('eff', 'GUESS', 2, { name: 'step efficiency', unit: 'ratio' })], resolved: [],
        anchor: clone(PLAN.anchor), predictions: clone(PLAN.predictions), judged: { ...clone(JUDGED), plan: plan2 } }
      const result = clone(RESULT)
      result.calibration[3] = REC_F   // D's slot: D is not named here
      const merge = (name, perRun, { wantIds, steps, eff, uncertain }) => {
        const c = setup(name, result)
        const runs = perRun.map(([s, e], i) => makeRun(path.join(c.dir, `run-${i + 1}`), { result: c.result, record: REC_F,
          run: `run-${i + 1}`, commit: `m${i}`, box: { type: `box_${i}`, started_utc: `2026-11-0${i + 1}T00:00:00Z` },
          rows: [{ id: 'steps_per_h', measured: s, verdict: s === null ? 'not_measured' : 'within_band', decision: s === null ? 'not_measured' : 'holds' },
            { id: 'eff', measured: e, verdict: e === null ? 'not_measured' : 'within_band', decision: e === null ? 'not_measured' : 'holds' }] }))
        fs.mkdirSync(c.outDir, { recursive: true })
        const r = resolve([c.result, ...runs.map(run => run.dir), '--out', c.out])
        check(`${name}: exit 0`, () => assert.equal(r.status, 0, why(r)))
        if (!fs.existsSync(c.out)) return
        const record = read(c.out).calibration[3]
        check(`${name}: entries for both ids of every run, in argument order`, () => assert.deepEqual(record.resolved,
          runs.flatMap(run => run.rows.map(row => entryFor(run, row)))))
        check(`${name}: rejudged present`, () => assert.ok(record.rejudged && typeof record.rejudged === 'object'))
        if (!record.rejudged) return
        check(`${name}: measured_ids ${JSON.stringify(wantIds)} in required order (not alphabetical)`, () =>
          assert.deepEqual(record.rejudged.measured_ids, wantIds))
        check(`${name}: plan_usd_before ${REC_F.plan_usd.toFixed(3)}; plan_usd_after uses the medians steps_per_h=${steps}, eff=${eff}`, () => {
          assert.equal(record.rejudged.plan_usd_before, REC_F.plan_usd)
          near(record.rejudged.plan_usd_after, planned2(steps, eff), 'plan_usd_after')
        })
        check(`${name}: gate_action "ok", no reasons, uncertain_after ${JSON.stringify(uncertain)}`, () => {
          assert.equal(record.rejudged.gate_action, 'ok')
          assert.deepEqual(record.rejudged.gate_reasons, [])
          assert.deepEqual(record.rejudged.uncertain_after, uncertain)
        })
      }
      // The latest run never holds the median: steps_per_h 9000, 7000, 6000 (median 7000, latest 6000); eff 3, 1.5, 4
      // (median 3, latest 4). planned = 63.84 + 31.92 * 126000 / 21000 = 255.36.
      merge('merge-two-ids-three-runs', [[9000, 3], [7000, 1.5], [6000, 4]], { wantIds: ['steps_per_h', 'eff'], steps: 7000, eff: 3,
        uncertain: [] })
      // Even count, with an unmeasured row in one run: steps_per_h 6000 and 8000 (median 7000), eff 2.5 alone.
      merge('merge-two-ids-even-and-unmeasured', [[6000, null], [8000, 2.5]], { wantIds: ['steps_per_h', 'eff'], steps: 7000, eff: 2.5,
        uncertain: [] })
      // Only eff measured: steps_per_h keeps its PROXY value and stays uncertain.
      merge('merge-only-second-id', [[null, 4], [null, 2]], { wantIds: ['eff'], steps: 5000, eff: 3, uncertain: ['steps_per_h'] })
      // Only steps_per_h measured: eff keeps its GUESS value and stays uncertain.
      merge('merge-only-first-id', [[6300, null]], { wantIds: ['steps_per_h'], steps: 6300, eff: 2, uncertain: ['eff'] })
    }

    // 6. A relative result path from another working directory: `source` is absolute.
    {
      const c = setup('relative-result')
      const run = makeRun(path.join(c.dir, 'run-one'), { result: c.result, record: REC_B, run: 'r', commit: null,
        rows: [{ id: 'a_rate', measured: 40, verdict: 'within_band', decision: 'holds' },
          { id: 'b_lat', measured: null, verdict: 'not_measured', decision: 'not_measured' }] })
      const value = okRun('relative-result', c, [run], [path.relative(c.dir, c.result), 'run-one', '--out', path.relative(c.dir, c.out)], c.dir)
      if (value) check('relative-result: source is the absolute path of result.json', () => assert.equal(value.source, c.result))
    }

    // 7. Exit 1: nothing written.
    const base = (name, mutate = () => {}) => {
      const c = setup(name)
      const run = makeRun(path.join(c.dir, 'run-one'), { result: c.result, record: REC_B, run: 'r', commit: null,
        rows: [{ id: 'a_rate', measured: 40, verdict: 'within_band', decision: 'holds' },
          { id: 'b_lat', measured: null, verdict: 'not_measured', decision: 'not_measured' }] })
      const good = makeRun(path.join(c.dir, 'run-good'), { result: c.result, record: REC_B, run: 'g', commit: null,
        rows: [{ id: 'a_rate', measured: 41, verdict: 'within_band', decision: 'holds' },
          { id: 'b_lat', measured: 2, verdict: 'within_band', decision: 'holds' }] })
      mutate(c, run)
      return { c, run, good, runs: [good, run], argv: [c.result, good.dir, run.dir, '--out', c.out] }
    }
    const control = (run, file) => path.join(run.dir, 'control', file)
    const failing = [
      ['seal-mismatch', (c, run) => fs.appendFileSync(control(run, 'card.json'), ' ')],
      ['seal-digest-wrong', (c, run) => writeJSON(control(run, 'card_seal.json'), { card_sha256: '0'.repeat(64), sealed_utc: 'x' })],
      ['source-sha-differs', (c, run) => {
        const card = read(control(run, 'card.json'))
        card.source_sha256 = 'b'.repeat(64)
        const bytes = writeJSON(control(run, 'card.json'), card)
        writeJSON(control(run, 'card_seal.json'), { card_sha256: sha(bytes), sealed_utc: 'x' })
      }],
      ['missing-card', (c, run) => fs.rmSync(control(run, 'card.json'))],
      ['missing-seal', (c, run) => fs.rmSync(control(run, 'card_seal.json'))],
      ['missing-scored', (c, run) => fs.rmSync(control(run, 'card_scored.json'))],
      ['scored-not-json', (c, run) => fs.writeFileSync(control(run, 'card_scored.json'), '{"rows": [')],
      ['seal-not-json', (c, run) => fs.writeFileSync(control(run, 'card_seal.json'), '{')],
      ['run-root-missing', (c, run) => fs.rmSync(run.dir, { recursive: true })],
      ['key-without-record', (c, run) => {
        const card = read(control(run, 'card.json'))
        card.record = { ...card.record, key: 'R9:nowhere:W9' }
        const bytes = writeJSON(control(run, 'card.json'), card)
        writeJSON(control(run, 'card_seal.json'), { card_sha256: sha(bytes), sealed_utc: 'x' })
        const scored = read(control(run, 'card_scored.json'))
        writeJSON(control(run, 'card_scored.json'), { ...scored, key: 'R9:nowhere:W9', card_sha256: sha(bytes) })
      }],
    ]
    // card_scored.json must have exactly U54's keys and row keys, the run's record key, the run's card.json digest,
    // and rows for the record's `required` ids in order (review of U56).
    const scored = fn => (c, run) => {
      const value = read(control(run, 'card_scored.json'))
      fn(value, run)
      writeJSON(control(run, 'card_scored.json'), value)
    }
    failing.push(
      ['scored-missing-key', scored(v => { delete v.extract_sha256 })],
      ['scored-missing-predictions', scored(v => { delete v.predictions })],
      ['scored-extra-key', scored(v => { v.note = 'extra' })],
      ['scored-row-missing-key', scored(v => { delete v.rows[0].rule })],
      ['scored-row-missing-gate-passed', scored(v => { delete v.rows[1].gate_passed })],
      ['scored-row-extra-key', scored(v => { v.rows[1].note = 'extra' })],
      ['scored-other-record-key', scored(v => { v.key = REC_A.key })],
      ['scored-card-sha-other', scored(v => { v.card_sha256 = 'c'.repeat(64) })],
      ['scored-card-sha-of-seal', scored((v, run) => { v.card_sha256 = sha(fs.readFileSync(control(run, 'card_seal.json'))) })],
      ['scored-rows-reordered', scored(v => { v.rows.reverse() })],
      ['scored-rows-missing-one', scored(v => { v.rows.pop() })],
      ['scored-rows-extra-id', scored(v => { v.rows.push({ ...v.rows[0], id: 'z_extra' }) })],
      ['scored-rows-duplicate-id', scored(v => { v.rows[1] = { ...v.rows[0] } })],
      ['scored-rows-empty', scored(v => { v.rows = [] })],
    )
    for (const [name, mutate] of failing) {
      const { c, runs, argv } = base(name, mutate)
      refused(name, c, runs.filter(run => fs.existsSync(run.dir)), argv)
    }
    {
      const { c, runs } = base('result-missing')
      const missing = path.join(c.dir, 'no-such-result.json')
      refused('result-missing', c, runs, [missing, ...runs.map(run => run.dir), '--out', c.out])
    }
    {
      // result.json changed after the runs: its SHA-256 no longer matches the runs' source_sha256.
      const { c, runs, argv } = base('result-changed')
      const changed = Buffer.concat([c.resultBytes, Buffer.from(' ')])
      fs.writeFileSync(c.result, changed)
      c.resultBytes = changed
      refused('result-changed', c, runs, argv)
    }
    {
      const { c, runs } = base('result-not-json')
      const bad = path.join(c.dir, 'bad.json')
      fs.writeFileSync(bad, '{"calibration": [')
      refused('result-not-json', c, runs, [bad, ...runs.map(run => run.dir), '--out', c.out])
    }
    {
      const { c } = base('no-run-root')
      refused('no-run-root', c, [], [c.result, '--out', c.out])
    }
    {
      const { c, runs } = base('missing-out')
      refused('missing-out', c, runs, [c.result, ...runs.map(run => run.dir)])
      refused('missing-out-value', c, runs, [c.result, ...runs.map(run => run.dir), '--out'])
    }
    // Refusal to write over an input: result.json, a run's card_scored.json or card.json.
    for (const [name, target] of [['out-is-result', c => c.result], ['out-is-scored', (c, run) => control(run, 'card_scored.json')],
      ['out-is-card', (c, run) => control(run, 'card.json')], ['out-is-seal', (c, run) => control(run, 'card_seal.json')]]) {
      const { c, run, runs } = base(name)
      refused(name, c, runs, [c.result, ...runs.map(r => r.dir), '--out', target(c, run)], { outIsInput: true })
    }
  } catch (error) { failures++; console.log(`FAIL test harness: ${error.stack}`) }
  finally { fs.rmSync(scratch, { recursive: true, force: true }) }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : `all ${checks} checks passed`)
  process.exitCode = failures ? 1 : 0
}
main()
