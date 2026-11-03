#!/usr/bin/env node
'use strict'
// Card write-back and re-judging (U56): node m5/card_resolve.js <result.json> <run root> [<run root> ...] --out <file>
// Returns each run's measurements to the card's calibration record as MEASURED plan numbers, sets the state from every
// run that measured it, and re-judges the plan with the tree's own cost_eval_plan and gate_plan. No model is called.
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const crypto = require('node:crypto')

const sha256 = bytes => crypto.createHash('sha256').update(bytes).digest('hex')
const fail = message => { process.stderr.write(`${message}\n`); process.exit(1) }
const plain = value => value && typeof value === 'object' && !Array.isArray(value)
const exactly = (value, keys) => Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key))
// U54's card_scored.json and its rows (m5/SCHEMAS.md "Card calibration (U54)")
const SCORED_KEYS = ['key', 'run', 'pipeline_commit', 'box_type', 'box_started_utc', 'card_sha256', 'extract_sha256',
  'predictions', 'anchor', 'rows', 'inputs_total', 'measured_total', 'holds_total', 'refuted_total']
const ROW_KEYS = ['id', 'name', 'unit', 'basis', 'value', 'band_source', 'band_lo', 'band_hi', 'measured_value', 'verdict',
  'gate_passed', 'decided_by', 'decision', 'rule']

// the tree modules, concatenated in build.js's order, in one context (they are plain scripts with no Node APIs)
function treeModules() {
  const src = ['text', 'schemas', 'cost', 'pick', 'gates', 'render', 'prompts']
    .map(m => fs.readFileSync(path.join(__dirname, '..', 'src', `${m}.js`), 'utf8')).join('\n')
  return vm.runInNewContext(`${src}\n;({ cost_eval_plan, gate_plan })`, {}, { filename: 'src(concat).js' })
}

const median = values => {
  const s = [...values].sort((a, b) => a - b), m = Math.floor(s.length / 2)
  if (s.length % 2) return s[m]
  const sum = s[m - 1] + s[m]   // halved first only when the sum overflows (then both halves are exact)
  return Number.isFinite(sum) ? sum / 2 : s[m - 1] / 2 + s[m] / 2
}

// a scored row holds values U54 allows and agrees with U54's rules for its record item (m5/SCHEMAS.md "Card calibration (U54)")
const VERDICTS = ['not_measured', 'no_band', 'within_band', 'below_band', 'above_band']
const BANDED = ['within_band', 'below_band', 'above_band']
const count = n => Number.isInteger(n) && n >= 0
function rowValid(row, item) {
  const m = row.measured_value, lo = row.band_lo, hi = row.band_hi
  const bound = v => v === null || Number.isFinite(v)
  if (!['GUESS', 'PROXY'].includes(row.basis) || row.basis !== item.basis || !VERDICTS.includes(row.verdict)
    || ![null, 'launch', 'card', 'multiplicative'].includes(row.band_source) || !bound(lo) || !bound(hi)
    || !(row.gate_passed === null || typeof row.gate_passed === 'boolean')
    || !exactly(row.rule, ['file', 'kind', 'expr']) || !['json', 'regex'].includes(row.rule.kind)) return false
  if (row.band_source === null && (lo !== null || hi !== null)) return false
  // the verdict: bounds are written rounded to the nearest double, which keeps each exact comparison non-strict
  if (m === null ? row.verdict !== 'not_measured'
    : row.band_source === null ? row.verdict !== 'no_band'
      : !BANDED.includes(row.verdict)
        || (row.verdict === 'within_band' && ((lo !== null && m < lo) || (hi !== null && m > hi)))
        || (row.verdict === 'below_band' && (lo === null || m > lo))
        || (row.verdict === 'above_band' && (hi === null || m < hi))) return false
  // the gate: the item's phase gate on its own id with >= or <= and a finite value, decided by the measurement
  const gate = plain(item.phase) && plain(item.phase.gate) ? item.phase.gate : null
  const gated = gate && gate.on === item.id && ['>=', '<='].includes(gate.op) && Number.isFinite(gate.value) && m !== null
  if (row.gate_passed !== (gated ? (gate.op === '>=' ? m >= gate.value : m <= gate.value) : null)) return false
  const decided_by = row.gate_passed !== null ? 'gate' : BANDED.includes(row.verdict) ? 'band' : null
  const decision = decided_by === 'gate' ? (row.gate_passed ? 'holds' : 'refuted')
    : decided_by === 'band' ? (row.verdict === 'within_band' ? 'holds' : 'refuted')
      : m === null ? 'not_measured' : 'undecidable'
  return row.decided_by === decided_by && row.decision === decision
}

function main(argv) {
  const at = argv.indexOf('--out')
  if (at < 0 || !argv[at + 1]) fail('usage: card_resolve.js <result.json> <run root> [<run root> ...] --out <file>')
  const out = path.resolve(argv[at + 1])
  const [resultArg, ...roots] = argv.filter((_, i) => i !== at && i !== at + 1)
  if (!resultArg || !roots.length) fail('usage: card_resolve.js <result.json> <run root> [<run root> ...] --out <file>')
  const source = path.resolve(resultArg)
  let bytes, result
  try { bytes = fs.readFileSync(source); result = JSON.parse(bytes.toString('utf8')) } catch { fail('result unreadable or invalid') }
  const source_sha256 = sha256(bytes)
  if (!plain(result) || !Array.isArray(result.calibration)) fail('result has no calibration array')
  const inputs = [source]
  const named = new Map()   // key -> new entries, runs in argument order
  for (const root of roots.map(r => path.resolve(r))) {
    const control = path.join(root, 'control')
    const files = ['card.json', 'card_seal.json', 'card_scored.json'].map(f => path.join(control, f))
    inputs.push(...files)
    let card, seal, scored, cardBytes
    try {
      cardBytes = fs.readFileSync(files[0])
      card = JSON.parse(cardBytes.toString('utf8'))
      seal = JSON.parse(fs.readFileSync(files[1], 'utf8'))
      scored = JSON.parse(fs.readFileSync(files[2], 'utf8'))
    } catch { fail('run files unreadable or invalid') }
    if (!plain(seal) || seal.card_sha256 !== sha256(cardBytes)) fail('card does not match its seal')
    if (!plain(card) || card.source_sha256 !== source_sha256) fail('card was taken from another result')
    // card_scored.json: exactly U54's keys and row keys, scored from this run's sealed card, rows in `required` order
    const required = plain(card.record) && Array.isArray(card.record.required) ? card.record.required : null
    if (!plain(card.record) || typeof card.record.key !== 'string' || !required || !plain(scored) || !Array.isArray(scored.rows)
      || !exactly(scored, SCORED_KEYS) || scored.key !== card.record.key || scored.card_sha256 !== sha256(cardBytes)
      || scored.rows.length !== required.length || !scored.rows.every((row, i) => plain(required[i]) && row?.id === required[i].id)
      || !scored.rows.every(row => plain(row) && exactly(row, ROW_KEYS) && typeof row.id === 'string' && plain(row.rule)
        && typeof row.rule.file === 'string' && typeof row.rule.kind === 'string' && typeof row.rule.expr === 'string'
        && (row.measured_value === null || Number.isFinite(row.measured_value)))
      || !scored.rows.every((row, i) => rowValid(row, required[i]))
      || ![scored.inputs_total, scored.measured_total, scored.holds_total, scored.refuted_total].every(count)
      || scored.inputs_total !== scored.rows.length
      || scored.measured_total !== scored.rows.filter(row => row.measured_value !== null).length
      || scored.holds_total !== scored.rows.filter(row => row.decision === 'holds').length
      || scored.refuted_total !== scored.rows.filter(row => row.decision === 'refuted').length) fail('run files invalid')
    const key = card.record.key
    if (!result.calibration.some(rec => plain(rec) && rec.key === key)) fail('no calibration record for the card key')
    const box_type = scored.box_type ?? null
    const entries = scored.rows.map(row => ({
      run: scored.run ?? null, pipeline_commit: scored.pipeline_commit ?? null, box_type, box_started_utc: scored.box_started_utc ?? null,
      id: row.id, measured_value: row.measured_value, verdict: row.verdict ?? null, decided_by: row.decided_by ?? null, decision: row.decision ?? null,
      number: row.measured_value === null ? null : {
        id: row.id, name: row.name ?? null, unit: row.unit ?? null, basis: 'MEASURED', value: row.measured_value, differs_in: [],
        command: 'bash harness/run_command.sh', output: `${path.basename(root)}/agent/results/reproduce/out/${row.rule.file}`,
        output_line: `${row.rule.kind}: ${row.rule.expr}`, machine: box_type },
    }))
    named.set(key, [...(named.get(key) || []), ...entries])
  }
  const real = file => { try { return fs.realpathSync(file) } catch { return path.resolve(file) } }
  if (inputs.some(file => real(file) === real(out))) fail('--out names one of the inputs')

  let tree = null
  const calibration = result.calibration.map(rec => {
    if (!plain(rec) || !named.has(rec.key)) return rec
    const resolved = [...(Array.isArray(rec.resolved) ? rec.resolved : []), ...named.get(rec.key)]
    const ids = (Array.isArray(rec.required) ? rec.required : []).map(item => item && item.id)
    const mine = resolved.filter(e => plain(e) && ids.includes(e.id))
    const state = mine.some(e => e.decision === 'refuted') ? 'refuted'
      : ids.length && ids.every(id => mine.some(e => e.id === id && e.decision === 'holds')) ? 'calibrated' : rec.state
    let rejudged = null
    if (rec.judged) {
      // MEASURED numbers replace the plan's entries: the median of every measured value, provenance from the latest
      const plan = JSON.parse(JSON.stringify(rec.judged.plan)), measured_ids = []
      for (const id of ids) {
        const runs = mine.filter(e => e.id === id && plain(e.number) && Number.isFinite(e.measured_value))
        const index = (plan.numbers || []).findIndex(n => n && n.id === id)
        if (!runs.length || index < 0) continue
        const { rests_on, source_id, quote, page_setting, ...kept } = plan.numbers[index]
        plan.numbers[index] = { ...kept, ...runs[runs.length - 1].number, value: median(runs.map(e => e.measured_value)) }
        measured_ids.push(id)
      }
      tree = tree || treeModules()
      const ev = tree.cost_eval_plan(plan, rec.judged.given)
      const g = tree.gate_plan(plan, ev, rec.judged.pick, rec.judged.gate_args)
      rejudged = { measured_ids, plan_usd_before: rec.plan_usd ?? null, plan_usd_after: ev.planned ?? null,
        gate_action: g.action, gate_reasons: g.reasons, uncertain_after: (ev.uncertain || []).map(u => u.id) }
    }
    return { ...rec, state, resolved, rejudged }
  })

  const text = JSON.stringify({ source, source_sha256, calibration }, null, 1) + '\n'
  const temporary = `${out}.${process.pid}.tmp`
  try {
    fs.writeFileSync(temporary, text)
    fs.renameSync(temporary, out)
  } catch {
    try { fs.rmSync(temporary, { force: true }) } catch { /* nothing to clean */ }
    fail('output unavailable')
  }
}

try { main(process.argv.slice(2)) } catch { fail('re-judging failed') }
