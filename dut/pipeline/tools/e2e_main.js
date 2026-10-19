// End-to-end run of the built dist/question_tree_v2.js with a stub agent (no network, no model).
// Usage: node tools/e2e_main.js [mode] [outdir]     mode: ok | reject | nosheet | annot (default ok); outdir default os.tmpdir()
//   reject   the dramaturg contradicts card:question everywhere
//   nosheet  the price sheet agent returns null
//   annot    every num: item UNREACHABLE, critic decides_by none at lever 4, framer signals with deepen_on_signal
// Adapted from the main agent's scratch harness; it runs the bundle itself, so a build bug shows here.
'use strict'
const fs = require('node:fs'), path = require('node:path'), os = require('node:os')
const ROOT = path.join(__dirname, '..')
const DIST = fs.readFileSync(path.join(ROOT, 'dist/question_tree_v2.js'), 'utf8')
const FX = f => JSON.parse(fs.readFileSync(path.join(ROOT, 'tests/fixtures', f), 'utf8'))
const AsyncFunction = (async () => {}).constructor
// the bundle's module section (text ... prompts), to read its schemas and run its selftests outside the body
const MODS = DIST.slice(DIST.indexOf('// ---- src/text.js ----'), DIST.indexOf('\n// ---------- args (CONTRACT'))
const fn = new AsyncFunction('args', 'agent', 'parallel', 'pipeline', 'log', DIST.replace(/^export const meta/, 'const meta'))

const PLAN = FX('gates/plan.json'), SHEET = FX('cost/price_sheet.json')
const reason = 'a reason that is long enough to pass'
const crit = { physical: ['stakes', 'open', 'reshape'], interp: ['stakes', 'open', 'internals', 'reshape'] }
const card = { physical: ['stakes', 'lever', 'verifiable', 'open', 'reshape', 'baseline'], interp: ['stakes', 'lever', 'verifiable', 'open', 'internals', 'reshape', 'baseline'] }
// option W2 of each branch gets a restructured plan (compute_tested no, which must not halt it)
const RESTRUCTURED = { sequential_part: 'Each fine-tuning step waits on the weights the step before produced, 32,000 steps.', method: 'Steps are grouped into rounds whose updates are combined at once.',
  condition: 'Updates within a round nearly commute; the pilot measures the drift.', condition_phase: 'P1', baseline_sequential: 'the tuned reference trainer', baseline_copies: 'eight runs side by side' }
const mode = process.argv[2] || 'ok', OUT = process.argv[3] || os.tmpdir()
const calls = []
let SCHEMA, KEYS = []
async function agent(prompt, o) {
  calls.push({ label: o.label, prompt })
  const tag = o.label
  switch (o.schema) {
    case SCHEMA.VERDICT: return mode === 'annot' ? { verdict: 'NOT COMPUTE-BOUND', compute_signals: [{ subproblem: 'ensemble size', what_compute_buys: 'more members' }] }
      : { verdict: tag.startsWith('R1') ? 'COMPUTE-BOUND' : 'NOT COMPUTE-BOUND', compute_signals: [] }
    case SCHEMA.OPTIONS: return { items: [1, 2, 3, 4].map(i => ({ id: `W${i}`, title: `${(tag.startsWith("R1") ? ["alpha", "bravo", "charlie", "delta"] : ["echo", "foxtrot", "golf", "hotel"])[i - 1]} ${tag.startsWith("R1") ? "quartz" : "basalt"} ${tag.includes("interp") ? "probe" : "flow"}`, summary: 'a summary', root_link: 'none', compute_open: i === 4 ? 'none' : 'samples; measured to 256 https://x.org; unknown above', sequential: i === 4 ? 'none: independent runs' : 'each step waits on the last; https://x.org', source_urls: ['https://x.org'] })) }
    case SCHEMA.OPTION_SCORES: {
      const b = tag.split(':')[1]
      return { items: [1, 2, 3, 4].map(i => ({ id: `W${i}`, distance: i === 3 ? 'ELSEWHERE' : 'SAME', distance_reason: reason, scores: crit[b].map(c => ({ criterion: c, value: 1 + ((i + c.length) % 5), reason })) })) }
    }
    case SCHEMA.PRICE_SHEET: return mode === 'nosheet' ? null : SHEET
    case SCHEMA.DEDUP: return { clusters: KEYS.map(k => ({ topic: `the topic of ${k}`, members: [k] })) }
    case SCHEMA.PLAN: {
      const t = /^Read option \S+ "([^"]*)"/.exec(String(prompt))
      const p = { ...JSON.parse(JSON.stringify(PLAN)), option_title: t ? t[1] : PLAN.option_title }
      return t && /^(bravo|foxtrot) /.test(t[1]) ? { ...p, restructuring: RESTRUCTURED, compute_tested: 'no' } : p
    }
    case SCHEMA.FINDINGS: {
      const refs = [...String(prompt).matchAll(/"ref":"([^"]+)"/g)].map(m => m[1])
      const status = ref => (mode === 'reject' && ref === 'card:question' ? 'CONTRADICTED' : mode === 'annot' && ref.startsWith('num:') ? 'UNREACHABLE' : 'SUPPORTED')
      return { items: [...new Set(refs)].map(ref => ({ ref, status: status(ref), page_quote: 'the page states exactly this', note: 'checked on the page' })) }
    }
    case SCHEMA.CRITIQUE: {
      const b = tag.split(':')[1] === 'interp' ? 'interp' : 'physical'
      const restructured = !String(prompt).includes('\ncard:method: none\n')
      return { scores: card[b].map(c => ({ criterion: c, value: c === 'baseline' && !restructured ? 'NA' : 4, ref: 'card:question', reason })), decides_by: mode === 'annot' ? 'none' : PLAN.phases[0].id, decides_by_reason: reason }
    }
    case SCHEMA.REPAIR_FIELDS: return { fields: {} }
    case SCHEMA.REPAIR_EXPR: return { numbers: [], lines: [] }
  }
  throw new Error('no reply for ' + tag)
}
let threw = 0
const parallel = thunks => Promise.all(thunks.map(t => Promise.resolve().then(t).catch(e => { threw++; console.log('THUNK THREW', e); return null })))

;(async () => {
  const S = await new AsyncFunction(MODS + '\nreturn {VERDICT: SCHEMA_VERDICT, OPTIONS: SCHEMA_OPTIONS, OPTION_SCORES: SCHEMA_OPTION_SCORES, PRICE_SHEET: SCHEMA_PRICE_SHEET, DEDUP: SCHEMA_DEDUP, PLAN: SCHEMA_PLAN, FINDINGS: SCHEMA_FINDINGS, CRITIQUE: SCHEMA_CRITIQUE, REPAIR_FIELDS: SCHEMA_REPAIR_FIELDS, REPAIR_EXPR: SCHEMA_REPAIR_EXPR}')()
  // schema identity differs between the two evaluations, so match by JSON
  SCHEMA = Object.fromEntries(Object.entries(S).map(([k, v]) => [k, JSON.stringify(v)]))
  const selftests = await new AsyncFunction(MODS + '\nreturn {cost: cost_selftest(), pick: pick_selftest(), gates: gate_selftest(), render: render_selftest()}')()
  console.log('selftests inside the bundle:', Object.entries(selftests).map(([m, r]) => `${m} ${r.ok ? 'ok' : `FAIL ${r.failures.join('; ')}`}`).join(', '))
  const wrapped = (p, o) => {
    if (o.schema === undefined) throw new Error('no schema ' + o.label)
    const key = Object.keys(SCHEMA).find(k => SCHEMA[k] === JSON.stringify(o.schema))
    if (key === 'DEDUP') KEYS = [...String(p).matchAll(/(R\d:(?:physical|interp):W\d):/g)].map(m => m[1])
    return agent(p, { ...o, schema: SCHEMA[key] })
  }
  const args = { seed: 1, base: '/b', fixed_roots: ['root one', 'root two'], seed_ideas: ['an idea from the human'], ...(mode === 'annot' ? { deepen_on_signal: true } : {}) }
  const r = await fn(args, wrapped, parallel, null, () => {})
  if (r.error) { console.log('RUN ERROR', r); process.exit(1) }
  fs.writeFileSync(path.join(OUT, `RESULT-${mode}.md`), r.result_md)
  const errs = r.log.filter(l => /script error|render .* failed/.test(l))
  const checks = {
    'all four selftests pass': Object.values(selftests).every(x => x.ok),
    'no script errors': !errs.length && !threw,
    'return carries price_sheet (fix 4)': 'price_sheet' in r && (mode === 'nosheet' ? r.price_sheet === null : r.price_sheet.read_at === SHEET.read_at),
    'every card links its producer.md (fix 1)': r.cards.every(c => /\*\*Producer file\.\*\* \[producer\.md\]\(\/b\/seed-1\//.test(c)),
    'Picked column shows rank/n_options (fix 2)': /\| (top|random) \d+\/4 /.test(r.table),
    'seed row and header say seed (fix 6)': /^\| \[seed·idea·1\][^\n]*\| seed \|/m.test(r.table) && r.cards.some(c => c.includes('**1 · an idea from the human.** seed pick')),
    'frontier lists no picked option (fix 10)': !r.table.split('\n').filter(l => l.startsWith('| [')).some(l => r.frontier.includes(`- ${l.split('](')[1].split(') ')[1].split(' | ')[0]} (`)),
    'option critic reads sequential; sequential none floors reshape': calls.some(c => /option-critic$/.test(c.label) && String(c.prompt).includes('"sequential":"none: independent runs"'))
      && r.log.some(l => /:W4: sequential none; reshape \d -> 1/.test(l)),
    'restructured cards: section after Hypothesis, not halted on compute_tested no; others say none': r.cards.some(c => /\*\*Hypothesis\.\*\*[^\n]*\n\n\*\*Restructuring\.\*\* Each fine-tuning step/.test(c) && !c.includes('**Halted at'))
      && r.cards.some(c => c.includes('*Restructuring.* none.')),
    'restructured cards send sequential_part and method to the dramaturg': calls.some(c => /:dramaturg$/.test(c.label) && String(c.prompt).includes('"ref":"card:sequential_part"') && String(c.prompt).includes('"ref":"card:method"'))
      && calls.some(c => /:dramaturg$/.test(c.label) && !String(c.prompt).includes('"ref":"card:sequential_part"')),
    'table has Reshape and Baseline; header prints U4 and U3': r.table.startsWith('| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |')
      && /on-goal cards U4 \d+ · U3 \d+/.test(r.result_md),
  }
  if (mode === 'annot') Object.assign(checks, {
    'DEEPENER prompt carries the framer signals (fix 9)': calls.some(c => /:physical:deepener$/.test(c.label) && c.prompt.endsWith('\nSignals from the framer: ensemble size: more members')),
    'case-17 annotation on every critiqued card (fix 5)': r.cards.filter(c => c.includes('**Critic.**')).every(c => c.includes('- inconsistent: decides_by none with lever ≥ 4')) && r.cards.some(c => c.includes('**Critic.**')),
    'unconfirmed num: shows as [g] in the cost block (fix 7)': r.cards.some(c => /\[g\] rests on: citation not confirmed: UNREACHABLE/.test(c)),
  })
  console.log(`mode ${mode}: keys ${Object.keys(r).join(',')}; ${r.cards.length} cards; ${calls.length} agent calls; ${r.log.length} log lines; header: ${r.result_md.split('\n')[2]}`)
  for (const l of errs) console.log('  ', l)
  let bad = 0
  for (const [k, ok] of Object.entries(checks)) { console.log(`  ${ok ? 'ok  ' : 'FAIL'} ${k}`); bad += !ok }
  console.log(`wrote ${path.join(OUT, `RESULT-${mode}.md`)}`)
  process.exit(bad ? 1 : 0)
})().catch(e => { console.error(e); process.exit(1) })
