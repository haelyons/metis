// Dry run of the built dist/replay_v2.js, phases A and B on replay/args_A.json, with a stub agent (no network, no model).
// Usage: node tools/e2e_replay.js [outdir] [planted_cards.json]     outdir default os.tmpdir(); writes A.json and B.json there.
// Without a planted file, phase B gets one clean planted card. Stub plans are the six cost encodings under card fields.
// Adapted from the replay agent's scratch dry run; it runs the bundle itself, so a build bug shows here.
'use strict'
const fs = require('node:fs'), path = require('node:path'), os = require('node:os'), vm = require('node:vm')
const Q = path.join(__dirname, '..'), OUT = process.argv[2] || os.tmpdir(), PLANTED = process.argv[3]
const P_NAMES = ['P_PRICE_SHEET', 'P_EXTRACT', 'P_REPAIR_EXPR', 'P_REPAIR_FIELDS', 'P_WRITER', 'P_DRAMATURG', 'P_CRITIC', 'P_OPTION_CRITIC', 'P_DEDUP', 'P_OVERLAP', 'CRIT_OPTION', 'CRIT_CARD']
// prompt functions return {p, a, text} so the stub agent can read the arguments
const wrap = P_NAMES.map(n => `${n} = ((f) => (...a) => ({ p: '${n}', a, text: f(...a) }))(${n})`).join('\n')
const dist = fs.readFileSync(path.join(Q, 'dist/replay_v2.js'), 'utf8').replace(/^export const meta/, 'const meta')
const cut = dist.indexOf('// ---------- args (CONTRACT')
const body = dist.slice(0, cut) + wrap + '\n' + dist.slice(cut)
const MODS = dist.slice(dist.indexOf('// ---- src/text.js ----'), cut)
const ARGS = JSON.parse(fs.readFileSync(path.join(Q, 'replay/args_A.json'), 'utf8'))
const sheet = JSON.parse(fs.readFileSync(path.join(Q, 'tests/fixtures/cost/price_sheet.json'), 'utf8'))
const enc = ['p03', 'p05', 'p06', 'p10', 'p16', 'p18'].map(n => JSON.parse(fs.readFileSync(path.join(Q, `tests/fixtures/cost/${n}.json`), 'utf8')))
const card = (i, title) => ({
  option_title: title, question: `Does skill keep rising with ensemble size beyond 150 members on fault ${i} [s1]?`, hypothesis: 'Skill levels off at tens to hundreds of members.',
  compute_axis: { quantity: 'ensemble members', unit: 'members', levels: [16, 256, 16384] }, held_fixed: ['truth regime'],
  predictions: { if_lever: 'Skill still rising beyond 1,024 members.', if_not: 'Skill flat by 256 members in every arm.', decision_rule: 'M* <= 256 decides if_not; rising beyond 1,024 decides if_lever', noise_rule: '5 truths, SE', expected: i % 3 ? 'if_not' : 'if_lever', expected_why: 'w' },
  compute_tested: i % 4 === 1 ? 'no' : 'yes', compute_tested_why: 'w', scored_against: 'hidden truth', arms: [{ id: 'E1', what: 'EnKF' }], baseline: { what: 'pattern repeat' },
  anchor: { what: 'Recurrence interval within 1% of the published benchmark code.', tolerance: '1%', source_id: 's1' }, checks: ['c'], scope_gap: [], outside_budget: [], full_scale: [],
  novelty: { closest_prior: 'A 150-member study forecast 70% of events [s1].', closest_source_id: 's1', prior_max_level: i % 2 ? 150 : null, left_open: 'Skill beyond 150 members.', decides: ['no', 'partly', 'yes'][i % 3], searched: false },
  limits: ['Synthetic faults only.'], test_summary: 'Simulate a fault, assimilate synthetic data with growing ensembles, score forecasts against the hidden truth.',
  restructuring: i === 0 ? { sequential_part: 'Each ensemble member steps through 20,000 time steps in order.', method: 'Time steps are combined in rounds of a parallel prefix computation.',
    condition: 'The state stays small; the pilot times one pass.', condition_phase: 'P1', baseline_sequential: 'compiled sequential code', baseline_copies: '64 copies side by side' }
    : { sequential_part: 'Each ensemble member steps through time in order.', method: 'none' },
  sources: [{ id: 's1', url: 'https://example.org/a', quote: 'as little as 20 ensemble members 150', supports: 'prior' }], files_read: ['producer.md'],
})
const plans = ARGS.picks.map((p, i) => { const e = JSON.parse(JSON.stringify(enc[i % 6])); const c = card(i, p.title); return { ...c, ...e, ...Object.fromEntries(Object.entries(c).filter(([k]) => !(k in e))), option_title: p.title, sources: [...c.sources, ...(e.sources || [])] } })
const OC = { physical: ['stakes', 'open', 'reshape'], interp: ['stakes', 'open', 'internals', 'reshape'] }
let n = 0, BYSIG = {}
function agent(prompt, o) {
  n++
  const name = o.schema === undefined ? 'WRITER' : BYSIG[JSON.stringify(o.schema)]
  const a = prompt && prompt.a
  return Promise.resolve((() => {
    switch (name) {
      case 'SCHEMA_PRICE_SHEET': return sheet
      // pick 5's extract returns null: a schema halt
      case 'SCHEMA_PLAN': { const i = ARGS.picks.findIndex(p => p.dir && o.label.startsWith(`${p.root}:${p.branch}:${p.kind}`)); return i === 4 ? null : plans[i] }
      case 'SCHEMA_REPAIR_EXPR': return { numbers: [], lines: [] }
      case 'SCHEMA_REPAIR_FIELDS': return { fields: Object.fromEntries(Object.entries(a ? a[0] : {}).map(([k, v]) => [k, String(v).split(' ').slice(0, 20).join(' ')])) }
      case 'WRITER': return 'Planned spend is {planned_usd}, budget $1,000; it typed 684.14 once and {nope}.'
      case 'SCHEMA_FINDINGS': return { items: (a ? a[0] : []).map((x, j) => ({ ref: x.ref, status: x.ref.startsWith('num:') && j % 2 ? 'UNSUPPORTED' : 'SUPPORTED', page_quote: 'a page quote that is long enough', note: 'a note of some length' })) }
      case 'SCHEMA_CRITIQUE': return { scores: [], decides_by: 'P1', decides_by_reason: 'r' }
      case 'SCHEMA_OPTION_SCORES': { const i = Number(o.label.slice(-1)); const br = o.label.split(':')[1]
        return { items: a[2].map((x, k) => ({ id: x.id, distance: ['SAME', 'ADJACENT', 'ELSEWHERE'][(k + i) % 3], distance_reason: 'a reason here', scores: OC[br].map((c, m) => ({ criterion: c, value: 1 + ((k * 7 + m * 3 + i) % 5), reason: 'a reason long enough' })) })) } }
      case 'SCHEMA_DEDUP': return { clusters: a[0].map(l => ({ topic: 'a topic of three', members: [l.split(': ')[0]] })) }
      case 'SCHEMA_OVERLAP': return { pairs: [{ a: 'R2', b: 'R5', shared_subject: 'robot manipulation limits today' }] }
    }
    throw new Error(`no stub for ${name} (${o.label})`)
  })())
}
let threw = 0
const parallel = thunks => Promise.all(thunks.map(t => Promise.resolve().then(t).catch(e => { threw++; console.error('thunk threw', e); return null })))
const AsyncFunction = (async () => {}).constructor
const go = args => new AsyncFunction('agent', 'parallel', 'log', 'args', body)(agent, parallel, () => {}, args)

;(async () => {
  // schemas are recreated inside the body; the stub matches them by JSON
  const ctx = {}
  vm.createContext(ctx)
  vm.runInContext(MODS + '\nthis.S = {' + ['SCHEMA_PRICE_SHEET', 'SCHEMA_PLAN', 'SCHEMA_REPAIR_EXPR', 'SCHEMA_REPAIR_FIELDS', 'SCHEMA_FINDINGS', 'SCHEMA_CRITIQUE', 'SCHEMA_OPTION_SCORES', 'SCHEMA_DEDUP', 'SCHEMA_OVERLAP'].join(',') + '}' +
    '\nthis.T = {cost: cost_selftest(), pick: pick_selftest(), gates: gate_selftest(), render: render_selftest()}', ctx)
  BYSIG = Object.fromEntries(Object.entries(ctx.S).map(([k, v]) => [JSON.stringify(v), k]))
  console.log('selftests inside the bundle:', Object.entries(ctx.T).map(([m, r]) => `${m} ${r.ok ? 'ok' : `FAIL ${r.failures.join('; ')}`}`).join(', '))
  const A = await go({ ...ARGS })
  fs.writeFileSync(path.join(OUT, 'A.json'), JSON.stringify(A, null, 1))
  if (A.error) { console.log('A: RUN ERROR', A); process.exit(1) }
  console.log(`A: ${A.records.length} records, ${A.records.filter(r => r.card).length} cards, ${A.records.filter(r => r.writer_text).length} writer cells, ${A.records.filter(r => r.halted).length} halted, agents ${n}`)
  const planted = PLANTED ? JSON.parse(fs.readFileSync(PLANTED, 'utf8')).planted_cards : [{ id: 'clean', card_text: 'fine', sources: [], expected: 'PASS' }]
  // every third record as the previous build wrote it: a plan with no restructuring record
  const OLD = new Set(A.records.filter((r, i) => r.plan && i % 3 === 2).map(r => r.pick.key))
  const records = A.records.map(r => (OLD.has(r.pick.key) ? { ...r, plan: (({ restructuring, ...p }) => p)(r.plan) } : r))
  const B = await go({ ...ARGS, phase: 'B', price_sheet: A.price_sheet, records, planted_cards: planted })
  fs.writeFileSync(path.join(OUT, 'B.json'), JSON.stringify(B, null, 1))
  if (B.error) { console.log('B: RUN ERROR', B); process.exit(1) }
  console.log(`B: dramaturg ${B.dramaturg.length}, planted ${B.planted.map(p => `${p.id} ${p.decision && p.decision.result}`).join(', ')}, critic ${B.critic.length}, picks ${B.pick_run.picks.length}, legacy picks ${B.pick_run_legacy.picks.length}, agents ${n}`)
  const errs = [...A.log, ...B.log].filter(l => /script error/.test(l)).concat(A.records.filter(r => r.error).map(r => `${r.pick.key}: ${r.error}`))
  const checks = {
    'all four selftests pass': Object.values(ctx.T).every(x => x.ok),
    'no script errors': !errs.length && !threw,
    'phase A: 20 records': A.records.length === 20,
    'phase B: every card with a plan dramaturged': B.dramaturg.length === A.records.filter(r => r.plan).length && B.dramaturg.every(d => d && d.items.length),
    'phase B: every planted card decided': B.planted.length === planted.length && B.planted.every(p => p && p.decision),
    'phase B: legacy rule reproduces 20 picks': B.pick_run_legacy.picks.length === 20,
    'phase B: plans without restructuring are dramaturged and critiqued as method none': OLD.size > 0 && [...OLD].every(k => B.dramaturg.some(d => d && d.key === k)
      && B.critic.some(c => c && c.key === k)),
    'phase B: option critic reads sequential "not given (stored run)"; reshape scored': B.pick_run.picks.length > 0
      && Object.values(B.new_scores).flat().every(o => typeof o.scores.reshape === 'number'),
  }
  for (const e of errs) console.log('  ', e)
  let bad = 0
  for (const [k, ok] of Object.entries(checks)) { console.log(`  ${ok ? 'ok  ' : 'FAIL'} ${k}`); bad += !ok }
  console.log(`wrote ${path.join(OUT, 'A.json')} and ${path.join(OUT, 'B.json')}`)
  process.exit(bad ? 1 : 0)
})().catch(e => { console.error(e); process.exit(1) })
