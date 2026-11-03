#!/usr/bin/env node
'use strict'

// Black-box contract tests for U55 (CONTRACT.md main.js bullet "`calibration` in the return (2026-10-21)" and the
// PLAN field `band?`): each calibration record's `required` item carries `name`, `unit` and `band` from the plan's
// `numbers` entry (null when absent; a band that is not {abs: x} with finite x > 0 counts as absent), the record
// carries `judged` = {plan, pick, given, gate_args}, and a rerun with `--resume` answers every agent call from the
// cache and reproduces the table, cards and calibration states.
//
// The built tree (dist/question_tree_v2.js) runs under idea/wf.js with a stub runner (this file, through
// WF_STUB), as tools/e2e_main.js runs it with a stub agent: the replies are e2e_main's, and the stub recognises
// each call's schema by the prompt suffix idea/schema.js appends, using the schemas evaluated from the bundle's
// module section as e2e_main does. Never inspect src/, dist/ or git history.
// Usage: node tools/test_tree_calibration_u55.js
const fs = require('node:fs'), path = require('node:path'), os = require('node:os')
const assert = require('node:assert/strict')
const { spawn } = require('node:child_process')
const ROOT = path.join(__dirname, '..')
const BUNDLE = path.join(ROOT, 'dist/question_tree_v2.js')
const FX = f => JSON.parse(fs.readFileSync(path.join(ROOT, 'tests/fixtures', f), 'utf8'))
const { validate, promptSuffix } = require(path.join(ROOT, 'idea/schema.js'))
const PLAN = FX('gates/plan.json')
// The cost fixture's price sheet with gpu_memory_gb on every instance: wf.js validates replies against the
// schema (tools/e2e_main.js calls the bundle directly and does not), and the schema requires it.
const MEMORY_GB = { A6000: 48, V100: 32, B200: 192, 'H100 PCIe': 80, A10: 24 }
const SHEET = FX('cost/price_sheet.json')
for (const instance of SHEET.instances) if (instance.gpu_memory_gb === undefined) instance.gpu_memory_gb = MEMORY_GB[instance.gpu]
const clone = value => JSON.parse(JSON.stringify(value))

// The tree bundle as built before U55 (copied by the operator from the commit before U54-U56; never edited).
const PRE_U55_BUNDLE = path.join(ROOT, 'tools/fixtures/pre_u55_question_tree_v2.js')

// ---- Schemas, from the bundle's module section (as tools/e2e_main.js obtains them) -----------------------
// The stub reads the schemas of the bundle the run executes (U55_BUNDLE), so a pre-U55 run is recognised too.
const schemasPromises = {}
function schemas(bundle = process.env.U55_BUNDLE || BUNDLE) {
  if (!schemasPromises[bundle]) {
    const dist = fs.readFileSync(bundle, 'utf8')
    const mods = dist.slice(dist.indexOf('// ---- src/text.js ----'), dist.indexOf('\n// ---------- args (CONTRACT'))
    const AsyncFunction = (async () => {}).constructor
    schemasPromises[bundle] = new AsyncFunction(mods + '\nreturn {VERDICT: SCHEMA_VERDICT, OPTIONS: SCHEMA_OPTIONS, OPTION_SCORES: SCHEMA_OPTION_SCORES, PRICE_SHEET: SCHEMA_PRICE_SHEET, DEDUP: SCHEMA_DEDUP, PLAN: SCHEMA_PLAN, FINDINGS: SCHEMA_FINDINGS, CRITIQUE: SCHEMA_CRITIQUE, REPAIR_FIELDS: SCHEMA_REPAIR_FIELDS, REPAIR_EXPR: SCHEMA_REPAIR_EXPR}')()
  }
  return schemasPromises[bundle]
}

// ---- The plan every producer returns: three load-bearing inputs with three band forms ---------------------
// steps_per_h (PROXY) has a valid band {abs: 250}; slow_f (GUESS) an invalid band; fudge_f (GUESS) none, and no
// `unit` when the plan schema allows that. All three scale the sweep, the plan's dominant spend.
const INVALID_BANDS = [{ abs: 0 }, { abs: -5 }, { rel: 0.5 }, { abs: 'wide' }, { abs: 2, rel: 1 }, 'wide', 5]
function variant(S) {
  const base = clone(PLAN)
  const [steps, total] = [base.numbers[0], base.numbers[1]]
  const make = (slowBand, dropUnit) => {
    const p = clone(base)
    const fudge = { id: 'fudge_f', name: 'restart overhead factor', unit: 'x', basis: 'GUESS', value: 1,
      rests_on: 'restarts are rare on runs this short', measured_by: 'P1' }
    if (dropUnit) delete fudge.unit
    const slow = { id: 'slow_f', name: 'slowdown factor of the fixed dataset', unit: 'x', basis: 'GUESS', value: 1,
      rests_on: 'a smaller dataset runs at about the same speed', measured_by: 'P1' }
    if (slowBand !== undefined) slow.band = slowBand
    p.numbers = [{ ...steps, band: { abs: 250 } }, total, slow, fudge,
      { id: 't_main', name: 'sweep hours', unit: 'h', basis: 'DERIVED', expr: 'steps / steps_per_h * slow_f * fudge_f' }]
    return p
  }
  const invalid = INVALID_BANDS.find(band => validate(S.PLAN, make(band, false)).length === 0)
  const dropUnit = validate(S.PLAN, make(invalid, true)).length === 0
  return { plan: make(invalid, dropUnit), invalid, dropUnit, baseValid: validate(S.PLAN, make(undefined, false)) }
}

// Every band form that is not {abs: x} with finite x > 0 (U55: counts as absent, so `band` is null). The band-forms
// run (U55_BAND_FORMS) gives each form the schema accepts its own load-bearing GUESS number `bf_<i>`.
const BAND_FORMS = [...INVALID_BANDS, { abs: null }, { abs: true }, { abs: '5' }, { abs: [1] }, {}, [], [{ abs: 1 }], { ABS: 1 },
  { abs: 1, note: 'x' }, null, true, 'abs 5', { rel: 2 }]
const bandNumber = (i, band) => ({ id: `bf_${i}`, name: `band form ${i}`, unit: 'x', basis: 'GUESS', value: 1, band,
  rests_on: 'a factor near one on runs this short', measured_by: 'P1' })
function bandForms(S) {
  const base = variant(S).plan
  const withForms = forms => {
    const p = clone(base)
    const t = p.numbers.pop()
    for (const [i, band] of forms) p.numbers.push(bandNumber(i, band))
    p.numbers.push({ ...t, expr: [t.expr, ...forms.map(([i]) => `bf_${i}`)].join(' * ') })
    return p
  }
  const accepted = BAND_FORMS.map((band, i) => [i, band]).filter(form => validate(S.PLAN, withForms([form])).length === 0)
  return { plan: withForms(accepted), accepted, rejected: BAND_FORMS.filter((_, i) => !accepted.some(([j]) => j === i)) }
}

// The producer reply for one option title. `steps` (DESIGN) differs per option, so every pick's plan, and so its
// plan_usd, is its own: 126000 less 250 per place of the title's first word (at most 2,000 steps, under the
// stated-versus-computed flag). Two titles get restructured plans.
const WORDS = ['alpha', 'bravo', 'charlie', 'delta', 'echo', 'foxtrot', 'golf', 'hotel']
function producerPlan(S, title) {
  const p = clone(process.env.U55_BAND_FORMS ? bandForms(S).plan : variant(S).plan)
  p.option_title = title ?? PLAN.option_title
  p.numbers.find(number => number.id === 'steps').value = 126000 - 250 * (WORDS.indexOf(String(title).split(' ')[0]) + 1)
  return title && /^(bravo|foxtrot) /.test(title) ? { ...p, restructuring: RESTRUCTURED, compute_tested: 'no' } : p
}
// The planned spend the cost rules give such a plan: pilot 2 h plus sweep hours, both at 8 x 3.99 $/h.
function plannedOf(plan) {
  const value = id => plan.numbers.find(number => number.id === id).value
  const factors = plan.numbers.filter(number => /^(slow_f|fudge_f|bf_\d+)$/.test(number.id)).reduce((a, n) => a * n.value, 1)
  return 8 * 3.99 * (2 + value('steps') / value('steps_per_h') * factors)
}

// ---- Stub runner (loaded by wf.js through WF_STUB) ------------------------------------------------------------
const reason = 'a reason that is long enough to pass'
const crit = { physical: ['stakes', 'open', 'reshape'], interp: ['stakes', 'open', 'internals', 'reshape'] }
const card = { physical: ['stakes', 'lever', 'verifiable', 'open', 'reshape', 'baseline'], interp: ['stakes', 'lever', 'verifiable', 'open', 'internals', 'reshape', 'baseline'] }
const RESTRUCTURED = { sequential_part: 'Each fine-tuning step waits on the weights the step before produced, 32,000 steps.', method: 'Steps are grouped into rounds whose updates are combined at once.',
  condition: 'Updates within a round nearly commute; the pilot measures the drift.', condition_phase: 'P1', baseline_sequential: 'the tuned reference trainer', baseline_copies: 'eight runs side by side' }
const ok = json => ({ text: JSON.stringify(json), json, jsonError: null, sessionID: 'stub', tokens: { input: 10, output: 5, reasoning: 0 }, cost: 0, tools: 0, ms: 1, errors: [], refusal: false })
const unavailable = () => ({ text: '', json: null, jsonError: null, sessionID: 'stub', tokens: { input: 0, output: 0, reasoning: 0 }, cost: 0, tools: 0, ms: 1, errors: ['exit 1: unavailable'], refusal: false })
function reply(kind, tag, prompt, S) {
  switch (kind) {
    case 'VERDICT': return { verdict: tag.startsWith('R1') ? 'COMPUTE-BOUND' : 'NOT COMPUTE-BOUND', compute_signals: [] }
    case 'OPTIONS': return { items: [1, 2, 3, 4].map(i => ({ id: `W${i}`, title: `${(tag.startsWith('R1') ? ['alpha', 'bravo', 'charlie', 'delta'] : ['echo', 'foxtrot', 'golf', 'hotel'])[i - 1]} ${tag.startsWith('R1') ? 'quartz' : 'basalt'} ${tag.includes('interp') ? 'probe' : 'flow'}`, summary: 'a summary', root_link: 'none', compute_open: i === 4 ? 'none' : 'samples; measured to 256 https://x.org; unknown above', sequential: i === 4 ? 'none: independent runs' : 'each step waits on the last; https://x.org', source_urls: ['https://x.org'] })) }
    case 'OPTION_SCORES': {
      const b = tag.split(':')[1]
      return { items: [1, 2, 3, 4].map(i => ({ id: `W${i}`, distance: i === 3 ? 'ELSEWHERE' : 'SAME', distance_reason: reason, scores: crit[b].map(c => ({ criterion: c, value: 1 + ((i + c.length) % 5), reason })) })) }
    }
    case 'PRICE_SHEET': return SHEET
    case 'DEDUP': {
      const keys = [...new Set([...prompt.matchAll(/(R\d:(?:physical|interp):W\d):/g)].map(m => m[1]))]
      return { clusters: keys.map(k => ({ topic: `the topic of ${k}`, members: [k] })) }
    }
    case 'PLAN': {
      const t = /^Read option \S+ "([^"]*)"/.exec(prompt)
      // U55_NULL_PLANS: no plan for one branch's picks (labels `R2:interp:<kind>:<stage>`): no evaluated plan.
      if (process.env.U55_NULL_PLANS && tag.startsWith('R2:interp:')) return null
      return producerPlan(S, t ? t[1] : null)
    }
    case 'FINDINGS': {
      const refs = [...prompt.matchAll(/"ref":"([^"]+)"/g)].map(m => m[1])
      return { items: [...new Set(refs)].map(ref => ({ ref, status: 'SUPPORTED', page_quote: 'the page states exactly this', note: 'checked on the page' })) }
    }
    case 'CRITIQUE': {
      const b = tag.split(':')[1] === 'interp' ? 'interp' : 'physical'
      const restructured = !prompt.includes('\ncard:method: none\n')
      return { scores: card[b].map(c => ({ criterion: c, value: c === 'baseline' && !restructured ? 'NA' : 4, ref: 'card:question', reason })), decides_by: PLAN.phases[0].id, decides_by_reason: reason }
    }
    case 'REPAIR_FIELDS': return { fields: {} }
    case 'REPAIR_EXPR': return { numbers: [], lines: [] }
  }
  return undefined
}
module.exports = {
  async run({ title, prompt }) {
    const S = await schemas()
    const kind = Object.keys(S).find(k => prompt.endsWith(promptSuffix(S[k])))
    fs.appendFileSync(process.env.U55_CALLS, JSON.stringify({ title, kind: kind ?? null }) + '\n')
    if (!kind) return unavailable()
    const body = prompt.slice(0, prompt.length - promptSuffix(S[kind]).length)
    const value = reply(kind, String(title).replace(/@.*$/, ''), body, S)
    return value === null || value === undefined ? unavailable() : ok(value)
  },
  async exportSession(id, file) { fs.writeFileSync(file, '{}') },
}
if (require.main !== module) return

// ---- Driver -----------------------------------------------------------------------------------------------
const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_tree_calibration_u55_'))
let checks = 0, failures = 0
function check(label, test) {
  checks++
  try { test(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${String(error.message).replace(/\s*\n\s*/g, ' ').slice(0, 1500)}`) }
}
const rows = file => fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : []
// One tree run under wf.js; every run of this suite shares the same args (and so the same base directory).
async function treeRun(name, extraArgs = [], env = {}, bundle = BUNDLE) {
  const out = path.join(scratch, name), calls = path.join(scratch, `${name}-calls.jsonl`)
  const stdoutFile = path.join(scratch, `${name}-stdout.log`), stderrFile = path.join(scratch, `${name}-stderr.log`)
  const stdout = fs.openSync(stdoutFile, 'w'), stderr = fs.openSync(stderrFile, 'w')
  let child
  try {
    child = await new Promise(resolve => {
      const proc = spawn(process.execPath, [path.join(ROOT, 'idea/wf.js'), '--script', bundle, '--args', path.join(scratch, 'args.json'),
        '--out', out, '--disable-family', 'claude', ...extraArgs], { cwd: ROOT, timeout: 300000, killSignal: 'SIGKILL', stdio: ['ignore', stdout, stderr],
        env: { ...process.env, HOME: path.join(scratch, 'home'), WF_STUB: __filename, U55_CALLS: calls, U55_BUNDLE: bundle, ...env } })
      let error
      proc.on('error', value => { error = value })
      proc.on('close', (status, signal) => resolve({ status, signal, error }))
    })
  } finally { fs.closeSync(stdout); fs.closeSync(stderr) }
  const resultFile = path.join(out, 'result.json')
  const result = fs.existsSync(resultFile) ? JSON.parse(fs.readFileSync(resultFile, 'utf8')) : null
  check(`${name}: the tree run completes without a script error`, () => {
    assert.ifError(child.error)
    assert.equal(child.status, 0, `exit ${child.status} ${child.signal}; ${fs.readFileSync(stderrFile, 'utf8').slice(-600)}`)
    assert.ok(result && !result.error, `result error: ${result?.error}`)
    assert.ok(Array.isArray(result.calibration) && result.calibration.length === result.cards.length, 'one calibration record per card')
  })
  return { name, out, result, calls: rows(calls), journal: rows(path.join(out, 'journal.jsonl')) }
}

async function main() {
  try {
    fs.mkdirSync(path.join(scratch, 'home'), { recursive: true })
    fs.mkdirSync(path.join(scratch, 'base'), { recursive: true })
    // Budget arguments differ from the defaults (1000, true, false), so judged.given and judged.gate_args show
    // the run's own values; the gate arguments are given explicitly.
    const ARGS = { seed: 1, base: path.join(scratch, 'base'), fixed_roots: ['root one', 'root two'], seed_ideas: ['an idea from the human'],
      budget_usd: 1500, budget_covers_storage: false, budget_covers_tax: true, require_compute_lever: { physical: true, interp: true },
      pool_k: 3, picks_per_branch: 2 }
    fs.writeFileSync(path.join(scratch, 'args.json'), JSON.stringify(ARGS))
    const S = await schemas()
    const v = variant(S)
    check('fixture: the producer plan (no slow_f band) validates against the bundle plan schema', () => assert.deepEqual(v.baseValid, []))
    check('fixture: the price sheet reply validates against the bundle price sheet schema', () => assert.deepEqual(validate(S.PRICE_SHEET, SHEET), []))
    check(`fixture: an invalid band form passes the plan schema, so the tree can receive one (slow_f band ${JSON.stringify(v.invalid)})`, () =>
      assert.ok(v.invalid !== undefined, `the schema rejects every invalid band form tried: ${JSON.stringify(INVALID_BANDS)}`))
    if (!v.dropUnit) console.log('note: the plan schema requires `unit`; the "unit null when absent" case is not reachable through a valid plan (not counted)')
    const want = {
      steps_per_h: { name: PLAN.numbers[0].name, unit: PLAN.numbers[0].unit, band: { abs: 250 } },
      slow_f: { name: 'slowdown factor of the fixed dataset', unit: 'x', band: null },
      fudge_f: { name: 'restart overhead factor', unit: v.dropUnit ? null : 'x', band: null },
    }

    const first = await treeRun('run1')
    const records = first.result?.calibration ?? []
    const required = records.filter(record => record.state === 'calibration_required')
    check('run1: stub calls all recognised (fixture sanity)', () => assert.deepEqual(first.calls.filter(call => !call.kind).map(call => call.title), []))
    check('run1: calibration_required records name steps_per_h, slow_f and fudge_f (fixture sanity)', () => {
      assert.ok(required.length >= 1, `states: ${records.map(record => record.state)}`)
      for (const record of required) assert.deepEqual(record.required.map(item => item.id).sort(), Object.keys(want).sort(), record.key)
    })
    check('run1: every required item has name, unit and band from the plan numbers entry (band null when absent or invalid)', () => {
      for (const record of required) for (const item of record.required) {
        for (const key of ['name', 'unit', 'band']) assert.ok(Object.hasOwn(item, key), `${record.key} ${item.id} lacks ${key}`)
        if (want[item.id]) assert.deepEqual({ name: item.name, unit: item.unit, band: item.band }, want[item.id], `${record.key} ${item.id}`)
      }
    })
    check('run1: every record has judged; a judged pick has exactly {plan, pick, given, gate_args}', () => {
      for (const record of records) {
        assert.ok(Object.hasOwn(record, 'judged'), `${record.key} lacks judged`)
        if (record.state === 'calibration_required') assert.ok(record.judged, `${record.key}: judged null for an evaluated plan`)
        if (record.judged === null) continue
        assert.deepEqual(Object.keys(record.judged).sort(), ['gate_args', 'given', 'pick', 'plan'], record.key)
        for (const key of ['plan', 'pick', 'given', 'gate_args'])
          assert.ok(record.judged[key] && typeof record.judged[key] === 'object' && !Array.isArray(record.judged[key]), `${record.key} judged.${key}`)
      }
    })
    check('run1: judged.plan is the producer plan of the pick, judged.given carries the price sheet the run read', () => {
      for (const record of required) {
        assert.deepEqual(record.judged.plan.numbers.map(number => number.id), v.plan.numbers.map(number => number.id), record.key)
        assert.equal(record.judged.plan.option_title, record.title, `${record.key}: plan option_title`)
        assert.deepEqual(record.judged.given.price_sheet, SHEET, `${record.key}: given.price_sheet`)
        assert.equal(typeof record.judged.given.budget_usd, 'number', `${record.key}: given.budget_usd`)
      }
    })
    check('run1: the tree writes resolved: [] in every record', () => {
      for (const record of records) assert.deepEqual(record.resolved, [], record.key)
    })
    // judged holds the actual evaluation arguments (review of U55).
    const judgedRecords = records.filter(record => record.judged)
    check('run1: the producer plans differ per pick in their numbers (fixture sanity)', () => {
      const steps = judgedRecords.map(record => record.judged.plan.numbers.find(number => number.id === 'steps')?.value)
      assert.ok(judgedRecords.length >= 2 && new Set(steps).size >= 2, `steps values ${JSON.stringify(steps)}`)
    })
    for (const record of judgedRecords) {
      const want = producerPlan(S, record.title)
      check(`run1: ${record.key}: judged.plan is the producer plan of this pick, number values included`, () => {
        assert.deepEqual(record.judged.plan.numbers, want.numbers)
        assert.deepEqual(record.judged.plan, want)
      })
      check(`run1: ${record.key}: plan_usd is the planned spend of judged.plan's numbers (${plannedOf(want).toFixed(3)})`, () => {
        assert.ok(typeof record.plan_usd === 'number' && Math.abs(record.plan_usd - plannedOf(record.judged.plan)) <= 1e-6 * record.plan_usd,
          `plan_usd ${record.plan_usd} != ${plannedOf(record.judged.plan)}`)
      })
      check(`run1: ${record.key}: judged.pick is the record's pick`, () => {
        const pick = record.judged.pick
        assert.equal(pick.key, record.key)
        // The result's inventory is rendered text; a pick key is `<root>:<branch>:<option id>`, a seed key `seed:...`.
        if (record.key.startsWith('seed:')) {
          assert.equal(pick.kind, 'seed')
          for (const key of ['root', 'branch', 'rank', 'total']) assert.equal(pick[key], null, `seed pick ${key}`)
        } else {
          const [root, branch] = record.key.split(':')
          assert.ok(['top', 'random', 'pool'].includes(pick.kind), `pick kind ${pick.kind}`)
          assert.deepEqual([pick.root, pick.branch], [root, branch], 'pick root and branch')
          assert.equal(typeof pick.total, 'number', 'pick total')
        }
      })
      check(`run1: ${record.key}: judged.given is the run's {budget_usd, price_sheet, budget_covers_storage, budget_covers_tax}`, () => {
        assert.deepEqual(record.judged.given, { budget_usd: ARGS.budget_usd, price_sheet: SHEET,
          budget_covers_storage: ARGS.budget_covers_storage, budget_covers_tax: ARGS.budget_covers_tax })
      })
      check(`run1: ${record.key}: judged.gate_args carries the run's budget and gate arguments`, () => {
        for (const key of ['budget_usd', 'require_compute_lever', 'pool_k', 'picks_per_branch'])
          assert.deepEqual(record.judged.gate_args[key], ARGS[key], `gate_args.${key}`)
      })
    }

    // --resume: every agent call answered from the cache; table, cards and calibration states reproduced.
    const second = await treeRun('run2', ['--resume', first.out])
    check('run2 (--resume run1): no new agent call', () => {
      assert.deepEqual(second.calls, [], `stub called ${second.calls.length} times`)
      const started = second.journal.filter(row => row.type === 'started').length
      const cached = second.journal.filter(row => row.type === 'cached').length
      assert.ok(started > 0, 'no agent call started')
      assert.equal(cached, started, `${started} calls started, ${cached} answered from the cache`)
      assert.equal(second.journal.filter(row => ['result', 'failed', 'understudy'].includes(row.type)).length, 0, 'calls beyond the cache')
    })
    if (second.result && first.result) {
      check('run2 (--resume run1): the same table and cards', () => {
        assert.equal(second.result.table, first.result.table)
        assert.deepEqual(second.result.cards, first.result.cards)
      })
      check('run2 (--resume run1): the same calibration states, required items and judged', () => {
        assert.deepEqual(second.result.calibration.map(record => [record.key, record.state]), first.result.calibration.map(record => [record.key, record.state]))
        assert.deepEqual(second.result.calibration.map(record => record.required), first.result.calibration.map(record => record.required))
        assert.deepEqual(second.result.calibration.map(record => record.judged), first.result.calibration.map(record => record.judged))
      })
    }

    // A pick without an evaluated plan: judged null.
    const third = await treeRun('run3-null-plans', [], { U55_NULL_PLANS: '1' })
    check('run3-null-plans: picks of the branch without a plan have judged null; the others keep judged', () => {
      const records3 = third.result?.calibration ?? []
      const halted = records3.filter(record => String(record.key).startsWith('R2:interp:'))
      assert.ok(halted.length >= 1, `no pick of that branch: ${records3.map(record => record.title)}`)
      for (const record of halted) {
        assert.equal(record.state, 'not_judged', `${record.key} state`)
        assert.equal(record.judged, null, `${record.key} judged`)
      }
      assert.ok(records3.some(record => record.judged !== null), 'no judged record left')
    })

    // Every invalid band form the plan schema accepts reaches the output as band null, each in its own number.
    const forms = bandForms(S)
    check(`band-forms fixture: the plan with all ${forms.accepted.length} accepted forms validates; at least one form is accepted`, () => {
      assert.ok(forms.accepted.length >= 1, 'the plan schema rejects every invalid band form')
      assert.deepEqual(validate(S.PLAN, forms.plan), [])
    })
    for (const band of forms.rejected) console.log(`note: the plan schema rejects band ${JSON.stringify(band)}; it cannot reach the tree (not counted)`)
    const fourth = await treeRun('run4-band-forms', [], { U55_BAND_FORMS: '1' })
    const required4 = (fourth.result?.calibration ?? []).filter(record => record.state === 'calibration_required')
    check('run4-band-forms: calibration_required records name every bf_<i> number (fixture sanity)', () => {
      assert.ok(required4.length >= 1, 'no calibration_required record')
      for (const record of required4) for (const [i] of forms.accepted)
        assert.ok(record.required.some(item => item.id === `bf_${i}`), `${record.key} lacks bf_${i}`)
    })
    check('run4-band-forms: the valid band {abs: 250} still reaches the output', () => {
      for (const record of required4) assert.deepEqual(record.required.find(item => item.id === 'steps_per_h')?.band, { abs: 250 }, record.key)
    })
    for (const [i, band] of forms.accepted) {
      check(`run4-band-forms: band ${JSON.stringify(band)} (bf_${i}) is null in every record; name and unit copied`, () => {
        for (const record of required4) {
          const item = record.required.find(entry => entry.id === `bf_${i}`)
          assert.ok(item, `${record.key} lacks bf_${i}`)
          assert.ok(Object.hasOwn(item, 'band'), `${record.key} bf_${i} has no band key`)
          assert.deepEqual({ name: item.name, unit: item.unit, band: item.band }, { name: `band form ${i}`, unit: 'x', band: null }, record.key)
        }
      })
    }

    // Backward compatibility: a run of the pre-U55 bundle, then the current bundle resuming from it.
    const old = await treeRun('run5-pre-u55', [], {}, PRE_U55_BUNDLE)
    const resumed = await treeRun('run6-resume-pre-u55', ['--resume', old.out])
    check('run6-resume-pre-u55: no new agent call; every call answered from the pre-U55 cache', () => {
      assert.ok(old.calls.length > 0, 'the pre-U55 run made no agent call')
      assert.deepEqual(resumed.calls, [], `stub called ${resumed.calls.length} times: ${resumed.calls.slice(0, 5).map(call => call.title)}`)
      const started = resumed.journal.filter(row => row.type === 'started').length
      const cached = resumed.journal.filter(row => row.type === 'cached').length
      assert.ok(started > 0, 'no agent call started')
      assert.equal(cached, started, `${started} calls started, ${cached} answered from the cache`)
      assert.equal(resumed.journal.filter(row => ['result', 'failed', 'understudy'].includes(row.type)).length, 0, 'calls beyond the cache')
    })
    if (old.result && resumed.result) {
      for (const key of ['table', 'cards', 'inventory', 'frontier'])
        check(`run6-resume-pre-u55: the same ${key} as the pre-U55 run`, () => assert.deepEqual(resumed.result[key], old.result[key]))
      check('run6-resume-pre-u55: the same calibration keys and states', () => {
        assert.deepEqual(resumed.result.calibration.map(record => [record.key, record.state]),
          old.result.calibration.map(record => [record.key, record.state]))
        assert.ok(old.result.calibration.some(record => record.state === 'calibration_required'), 'no calibration_required record (fixture sanity)')
      })
      check('run6-resume-pre-u55: the records differ only by the added name, unit, band (required items) and judged', () => {
        assert.equal(resumed.result.calibration.length, old.result.calibration.length)
        resumed.result.calibration.forEach((record, i) => {
          const before = old.result.calibration[i]
          assert.ok(!Object.hasOwn(before, 'judged'), `${before.key}: the pre-U55 record already has judged`)
          assert.ok(Object.hasOwn(record, 'judged'), `${record.key}: judged not added`)
          const { judged, required, ...rest } = record
          const { required: requiredBefore, ...restBefore } = before
          assert.deepEqual(rest, restBefore, `${record.key}: record fields`)
          assert.equal(required.length, requiredBefore.length, `${record.key}: required length`)
          required.forEach((item, j) => {
            for (const key of ['name', 'unit', 'band']) {
              assert.ok(!Object.hasOwn(requiredBefore[j], key), `${record.key} ${item.id}: the pre-U55 item already has ${key}`)
              assert.ok(Object.hasOwn(item, key), `${record.key} ${item.id}: ${key} not added`)
            }
            const { name, unit, band, ...itemRest } = item
            assert.deepEqual(itemRest, requiredBefore[j], `${record.key} ${item.id}`)
          })
        })
      })
      check('run6-resume-pre-u55: the added fields hold the values a fresh current run gives', () => {
        assert.deepEqual(resumed.result.calibration.map(record => record.required), first.result.calibration.map(record => record.required))
        assert.deepEqual(resumed.result.calibration.map(record => record.judged), first.result.calibration.map(record => record.judged))
      })
    }
  } catch (error) { failures++; console.log(`FAIL test harness: ${error.stack}`) }
  finally { fs.rmSync(scratch, { recursive: true, force: true }) }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : `all ${checks} checks passed`)
  process.exitCode = failures ? 1 : 0
}
main()
