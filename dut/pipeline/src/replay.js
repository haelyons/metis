export const meta = {
  name: 'question-tree-v2-replay',
  description: 'Stage-2 replay bound to the last run\'s stored outputs (no research re-run). Phase A: price sheet, qt-extract on each stored producer.md, G-plan, one repair, card, writer side cell. Phase B: dramaturg on every card and the planted set, critic, option critic x3 per branch, dedup and overlap judges, pick rules',
  phases: [
    { title: 'Price', detail: 'Lambda price sheet, unless args.price_sheet is given (A)' },
    { title: 'Extract', detail: 'qt-extract on each stored producer.md, G-plan, one cost repair (A)' },
    { title: 'Card', detail: 'card fields with one repair, cost block, menu, card; WRITER side cell on 10 picks (A)' },
    { title: 'Check', detail: 'DRAMATURG on every card and the planted cards; CRITIC on every card (B)' },
    { title: 'Options', detail: 'OPTION CRITIC x3 per stored branch; dedup and overlap judges; pick rules (B)' },
  ],
}
// @@MODULES@@

// ---------- args (CONTRACT §3 replay.js): the script cannot read files, so every stored input comes in args ----------
let A = args || {}
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { return { error: `args is not JSON: ${e.message}` } } }
const NEED = { A: ['seed', 'given', 'picks', 'options_by_branch', 'roots', 'old_scores'], B: ['seed', 'given', 'picks', 'options_by_branch', 'roots', 'old_scores', 'price_sheet', 'records', 'planted_cards'] }
if (!NEED[A.phase]) return { error: 'args.phase must be "A" or "B"' }
const missing = NEED[A.phase].filter(k => A[k] === undefined || A[k] === null)
if (missing.length) return { error: `phase ${A.phase} needs args: ${missing.join(', ')}` }
const SEED = Number(A.seed)
// the run's own args as main builds them (gate_plan reads require_compute_lever and the budget)
const ARGS = {
  require_compute_lever: { physical: true, interp: true }, deepen_on_signal: false, pool_k: 3, picks_per_branch: 2,
  budget_usd: A.given.budget_usd, budget_covers_storage: A.given.budget_covers_storage, budget_covers_tax: A.given.budget_covers_tax,
}
const LOG = []
// role names: the five qt-* agent files; overridable by args.agent_types, because a session that started
// before the files existed cannot resolve them (registry is read at session start)
const ROLE = Object.assign({ 'qt-bare': 'qt-bare', 'qt-research': 'qt-research', 'qt-producer': 'qt-producer', 'qt-web': 'qt-web', 'qt-extract': 'qt-extract' }, A.agent_types || {})
const note = m => { LOG.push(m); log(m) }

// ---------- S0: model-free self-tests, before any agent ----------
const failures = Object.entries({ cost: cost_selftest(), pick: pick_selftest(), gates: gate_selftest(), render: render_selftest() })
  .flatMap(([m, r]) => (r.ok ? [] : (r.failures.length ? r.failures : ['not ok']).map(f => `${m}: ${f}`)))
if (failures.length) return { error: `S0 self-test failed (${failures.length})`, failures }

// ---------- vocabularies and helpers, as in main.js ----------
const OC_CRIT = { physical: ['stakes', 'open', 'reshape'], interp: ['stakes', 'open', 'internals', 'reshape'] }
const CARD_CRIT = { physical: ['stakes', 'lever', 'verifiable', 'open', 'reshape', 'baseline'], interp: ['stakes', 'lever', 'verifiable', 'open', 'internals', 'reshape', 'baseline'] }
const CARD = [
  ['question', 'question', 25], ['hypothesis', 'hypothesis', 22],
  ['sequential_part', 'restructuring.sequential_part', 18], ['method', 'restructuring.method', 22],
  ['if_lever', 'predictions.if_lever', 22], ['if_not', 'predictions.if_not', 25],
  ['test_summary', 'test_summary', 45], ['closest_prior', 'novelty.closest_prior', 30],
  ['left_open', 'novelty.left_open', 30], ['anchor', 'anchor.what', 24], ['limits', 'limits', 30],
]
const CAPS = Object.fromEntries(CARD.map(f => [f[1], f[2]]))
const str = v => (typeof v === 'string' ? v : JSON.stringify(v))
const getPath = (o, p) => p.split('.').reduce((x, k) => (x == null ? x : x[k]), o)
const fieldText = (plan, p) => { const v = getPath(plan, p); return Array.isArray(v) ? v.join(' ') : v == null ? '' : String(v) }
function setField(plan, p, text) {
  const ks = p.split('.'), last = ks.pop(), obj = ks.reduce((x, k) => x[k], plan)
  obj[last] = Array.isArray(obj[last]) ? [text] : text
}
const optionRecord = o => ({ id: o.id, title: o.title, summary: o.summary, root_link: o.root_link, compute_open: o.compute_open, sequential: o.sequential, source_urls: o.source_urls })
// as main.js: "none: ..." is none, any other text names a chain
const seqStatus = s => (String(s ?? '').trim().toLowerCase().startsWith('none') ? 'none' : 'named')
const GIVEN = { ...A.given, price_sheet: A.price_sheet || null }
const ROOTQ = Object.fromEntries(A.roots.map(r => [r.id, r.question]))
// stored options predate root_link, compute_open, sequential and source_urls; the judges are told so. "not given" names
// no "none", so no reshape floor applies and the option critic reads the summary.
const OPTS = Object.entries(A.options_by_branch).flatMap(([bk, items]) => {
  const [root, branch] = bk.split(':')
  return items.map(o => ({ ...o, root_link: 'not recorded', compute_open: 'not recorded', sequential: 'not given (stored run)', source_urls: [], key: `${bk}:${o.id}`, root, branch }))
})
const OPT = Object.fromEntries(OPTS.map(o => [o.key, o]))
const keyOf = p => `${p.root}:${p.branch}:${p.id}`
// parallel() turns a throw into null; log it so a script error is never silent (as in main.js)
const guard = (what, f) => async () => { try { return await f() } catch (e) { note(`${what}: script error: ${(e && e.message) || e}`); return null } }
const tagOf = p => `${p.root}:${p.branch}:${p.kind}`

async function twice(what, ask, check) {
  let rec = null
  for (const s of ['', '-resample']) {
    const r = await ask(s)
    if (r) rec = r
    const c = r ? check(r) : { ok: false, errors: ['agent returned null'] }
    if (c.ok) return { rec: r, ok: true }
    note(`${what}${s ? ' (resample)' : ''}: ${c.errors.join('; ')}`)
  }
  return { rec, ok: false }
}

// ================= phase A =================
async function priceSheet() {
  const r = await twice('price sheet',
    s => agent(P_PRICE_SHEET(), { label: `run:price-sheet${s}`, phase: 'Price', schema: SCHEMA_PRICE_SHEET, agentType: ROLE['qt-web'], model: 'sonnet', effort: 'low' }),
    gate_price_sheet)
  return r.ok ? r.rec : null
}

// REPAIR_EXPR applied to a copy of the plan, as main.js does
function repairedPlan(plan, fix, annotations) {
  const p = JSON.parse(JSON.stringify(plan)), missed = []
  for (const n of fix.numbers || []) { const t = (p.numbers || []).find(x => x.id === n.id); if (t) t.expr = n.expr; else missed.push(n.id) }
  for (const l of fix.lines || []) {
    const t = ((p.cost && p.cost.lines) || []).find(x => x.id === l.id)
    if (!t) { missed.push(l.id); continue }
    for (const k of ['hours', 'usd', 'need']) if (l[k] !== undefined) t[k] = l[k]
  }
  annotations.push(`cost record repaired: ${(fix.numbers || []).length + (fix.lines || []).length} expression(s) rewritten${missed.length ? `; unknown ids ignored: ${missed.join(', ')}` : ''}`)
  return p
}

// {menu_id} -> the computed value; an unknown id stays as written (C9 counts it)
const fillMenu = (text, menu) => text.replace(/\{([a-z][a-z0-9_]*)\}/g, (m, id) => {
  const e = menu.find(x => x.id === id)
  return e ? String(e.value) : m
})

// The writer side cell (P2'): 10 picks, the lowest in a seeded order of their own keys.
const WRITER_KEYS = new Set(A.picks.map(keyOf).sort((a, b) => pick_u(SEED, `replaywriter:${a}`) - pick_u(SEED, `replaywriter:${b}`)).slice(0, 10))

async function replayPick(p) {
  const key = keyOf(p), tag = tagOf(p), o = OPT[key]
  const rec = { pick: { key, root: p.root, branch: p.branch, kind: p.kind, id: p.id, title: p.title }, plan: null, eval: null, gate: null, card: null,
    writer_text: null, writer_raw: null, menu: null, block: null, repairs: [], cardfields: null, np_failures: [], beyond_prior: null, annotations: [], halted: null }
  let plan = await agent(P_EXTRACT(p.producer_path, p.dir), { label: `${tag}:extract`, phase: 'Extract', schema: SCHEMA_PLAN, agentType: ROLE['qt-extract'], model: 'sonnet', effort: 'low' })
  if (!plan) { rec.halted = { gate: 'schema', reasons: ['no valid PLAN from the extract'] }; note(`${tag}: extract returned no valid PLAN`); return rec }
  try {
    let ev = cost_eval_plan(plan, GIVEN), g = gate_plan(plan, ev, rec.pick, ARGS)
    if (g.action === 'repair') {
      note(`${tag}: G-plan repair: ${g.reasons.join('; ')}`)
      const errs = ev.errors.length ? ev.errors.map(e => `${e.kind} at ${e.where}: ${e.msg}`) : g.reasons
      const fix = await agent(P_REPAIR_EXPR(errs, plan), { label: `${tag}:repair-expr`, phase: 'Extract', schema: SCHEMA_REPAIR_EXPR, agentType: ROLE['qt-bare'], model: 'sonnet', effort: 'low' })
      rec.repairs.push({ kind: 'expr', reasons: g.reasons, fix })
      if (fix) { plan = repairedPlan(plan, fix, rec.annotations); ev = cost_eval_plan(plan, GIVEN); g = gate_plan(plan, ev, rec.pick, ARGS) }
      else note(`${tag}: cost repair returned null`)
    }
    rec.plan = plan
    rec.eval = ev
    rec.gate = g
    rec.annotations.push(...g.annotations)
    // A halt is recorded and the chain continues: the replay judges every card ("PASS before the compute halt", substrate P1).
    if (g.action !== 'ok') { rec.halted = { gate: g.action === 'repair' ? 'cost record broken' : 'G-plan', reasons: g.reasons }; note(`${tag}: ${rec.halted.gate}: ${g.reasons.join('; ')}`) }

    // S7 as in main: failing card fields get one repair, kept only if every number survives
    const cf = gate_cardfields(plan, CAPS)
    rec.cardfields = cf
    rec.annotations.push(...cf.annotations)
    if (!cf.ok) {
      const orig = Object.fromEntries(cf.failing.map(f => [f.field, fieldText(plan, f.field)]))
      const caps = Object.fromEntries(cf.failing.map(f => [f.field, CAPS[f.field]]))
      const fix = await agent(P_REPAIR_FIELDS(orig, caps, plan), { label: `${tag}:repair-fields`, phase: 'Card', schema: SCHEMA_REPAIR_FIELDS, agentType: ROLE['qt-bare'], model: 'sonnet', effort: 'low' })
      rec.repairs.push({ kind: 'fields', fields: Object.keys(orig), fix })
      for (const f of Object.keys(orig)) {
        const t = fix && fix.fields && fix.fields[f]
        if (typeof t !== 'string') continue
        if (gate_number_preservation(orig[f], t)) { setField(plan, f, t); rec.annotations.push(`${f}: rewritten by the field repair`) }
        else { rec.np_failures.push(f); rec.annotations.push(`${f}: the field repair dropped a number; original kept`) }
      }
      gate_cardfields(plan, CAPS).failing.forEach(f => rec.annotations.push(`card field ${f.field} still fails: ${f.reasons.join(', ')}`))
    }
    const lv = (plan.compute_axis && plan.compute_axis.levels) || [], pm = plan.novelty && plan.novelty.prior_max_level
    rec.beyond_prior = typeof pm === 'number' && lv.length ? Math.max(...lv) > pm : null
    rec.block = cost_render_block(ev, plan, GIVEN)
    rec.menu = cost_menu(ev, plan)
    rec.card = render_card({ pick: rec.pick, option: o, root_question: ROOTQ[p.root], plan, eval: ev, given: GIVEN, findings: [null, null],
      decision: null, decision2: null, critique: null, beyond_prior: rec.beyond_prior, annotations: rec.annotations, halted: rec.halted, producer_path: p.producer_path })

    if (WRITER_KEYS.has(key)) {
      const { cost, ...planNoCost } = plan
      const w = await agent(P_WRITER(ROOTQ[p.root], optionRecord(o), planNoCost, rec.menu), { label: `${tag}:writer`, phase: 'Card', agentType: ROLE['qt-bare'], model: 'sonnet' })
      if (typeof w === 'string') { rec.writer_raw = w; rec.writer_text = fillMenu(w, rec.menu) }
      else note(`${tag}: writer returned no text`)
    }
  } catch (e) { rec.error = String((e && e.message) || e); note(`${tag}: script error: ${rec.error}`) }
  return rec
}

// ================= phase B =================
function criticView(plan) {
  const { cost, full_scale, compute_tested, compute_tested_why, files_read, ...rest } = plan
  const { expected, expected_why, ...predictions } = plan.predictions || {}
  const { decides, searched, ...novelty } = plan.novelty || {}
  return { ...rest, predictions, novelty }
}
const criticCard = plan => CARD.map(([name, p]) => `card:${name}: ${fieldText(plan, p)}`).join('\n')

// one dramaturg sample with one resample on a degenerate return, decided by the script's rule
async function dramaturg(label, items, decide) {
  const refs = items.map(i => i.ref)
  const r = await twice(`${label}: dramaturg`,
    s => agent(P_DRAMATURG(items), { label: `${label}:dramaturg${s}`, phase: 'Check', schema: SCHEMA_FINDINGS, agentType: ROLE['qt-web'] }),
    f => { const g = gate_findings(f.items, refs); return { ok: g.ok && !g.degenerate.length, errors: [...g.errors, ...g.degenerate.map(d => `degenerate: ${str(d)}`)] } })
  return { items, findings: r.rec, findings_ok: r.ok, decision: r.rec ? decide(r.rec.items) : null }
}

async function judgeRecord(r) {
  // the same items main builds (gate_dramaturg_items); the replay always has a price sheet, so rates are never items
  const d = await dramaturg(tagOf(r.pick), gate_dramaturg_items(r.plan, CARD), f => gate_decision(f, gate_core_refs(r.plan), r.plan, r.eval, GIVEN))
  return { key: r.pick.key, ...d }
}

// a planted card is one card item plus its sources, every item core
async function judgePlanted(c) {
  const items = [{ ref: 'card:text', text: c.card_text, sources: c.sources.map(s => ({ id: s.id, url: s.url, quote: s.quote })) },
    ...c.sources.map(s => ({ ref: `src:${s.id}`, url: s.url, quote: s.quote, supports: s.supports }))]
  const d = await dramaturg(`planted:${c.id}`, items, f => gate_decision(f, items.map(i => i.ref), null, null, GIVEN))
  return { id: c.id, expected: c.expected, ...d }
}

async function critic(r) {
  const tag = tagOf(r.pick), cb = r.pick.branch, plan = r.plan
  const cr = await twice(`${tag}: critic`,
    s => agent(P_CRITIC(ROOTQ[r.pick.root], optionRecord(OPT[r.pick.key]), criticCard(plan), criticView(plan), CRIT_CARD(cb)), { label: `${tag}:critic${s}`, phase: 'Check', schema: SCHEMA_CRITIQUE, agentType: ROLE['qt-bare'], model: 'sonnet' }),
    x => gate_critique(x, CARD.map(f => f[0]), plan, CARD_CRIT[cb]))
  return { key: r.pick.key, critique: cr.rec, critique_ok: cr.ok }
}

// three independent option-critic samples per stored branch; no resample, so the samples stay independent draws (K3)
const BRANCH_KEYS = Object.keys(A.options_by_branch)
const branchOpts = bk => OPTS.filter(o => `${o.root}:${o.branch}` === bk)
const optionCritic = (bk, i) => agent(P_OPTION_CRITIC(ROOTQ[bk.split(':')[0]], CRIT_OPTION(bk.split(':')[1]), branchOpts(bk).map(optionRecord)),
  { label: `${bk}:option-critic:${i + 1}`, phase: 'Options', schema: SCHEMA_OPTION_SCORES, agentType: ROLE['qt-bare'] })

// pick_run input from a set of samples: each criterion is the mean over the samples that returned the branch,
// rounded (a missing or invalid score counts 1, as in main); distance is the median label (main's fallback ADJACENT)
const DIST = ['SAME', 'ADJACENT', 'ELSEWHERE']
function scoreBranch(bk, samples) {
  const [root, branch] = bk.split(':'), crit = OC_CRIT[branch], got = samples.filter(Boolean)
  const scored = branchOpts(bk).map(o => {
    const its = got.map(s => (s.items || []).find(it => it.id === o.id) || {})
    const scores = crit.map(c => {
      const vs = its.map(it => { const s = (it.scores || []).find(x => x.criterion === c); return s && Number.isInteger(s.value) && s.value >= 1 && s.value <= 5 ? s.value : 1 })
      return { criterion: c, value: vs.length ? Math.round(vs.reduce((a, b) => a + b, 0) / vs.length) : 1 }
    })
    const ds = its.map(it => DIST.indexOf(it.distance)).filter(d => d >= 0).sort((x, y) => x - y)
    return { id: o.id, distance: ds.length ? DIST[ds[Math.floor((ds.length - 1) / 2)]] : 'ADJACENT', scores }
  })
  // "not recorded" is neither settled nor none, so every stored option is open (CONTRACT §2.2)
  const status = Object.fromEntries(scored.map(s => [s.id, 'open']))
  const totals = gate_totals(scored, crit, status)
  return { root, branch, options: scored.map(s => ({ key: `${bk}:${s.id}`, id: s.id, title: OPT[`${bk}:${s.id}`].title, total: totals[s.id],
    scores: Object.fromEntries(s.scores.map(x => [x.criterion, x.value])), distance: s.distance, compute_open_status: 'open',
    sequential_status: seqStatus(OPT[`${bk}:${s.id}`].sequential), compute_open: 'not recorded' })) }
}
const runPicks = (branches, clusters) => pick_run({ seed: SEED, args: { pool_k: ARGS.pool_k, picks_per_branch: ARGS.picks_per_branch, require_compute_lever: ARGS.require_compute_lever }, branches, clusters, seed_ideas: [] })

async function dedupJudge() {
  const keys = OPTS.map(o => o.key), samples = [], H = dedup_handles(OPTS)
  const dd = await twice('dedup judge',
    async s => {
      const r = await agent(P_DEDUP(H.lines.map(({ handle, option: o }) => `${handle}: ${o.title}. ${o.summary}`)), { label: `run:dedup${s}`, phase: 'Options', schema: SCHEMA_DEDUP, agentType: ROLE['qt-bare'], model: 'sonnet', effort: 'low' })
      const t = r && { ...r, clusters: dedup_unhandle(r.clusters, H.toKey) }
      samples.push(t)
      return t
    },
    r => {
      const g = gate_dedup(r.clusters, keys), j = gate_dedup_jaccard(OPTS, r.clusters, 0.4)
      return { ok: g.ok && !g.soft.length && j.ok, errors: [...g.errors, ...g.soft, ...j.violations.map(v => `title Jaccard >= 0.4 not merged: ${str(v)}`)] }
    })
  const single = OPTS.map(o => ({ topic: o.title, members: [o.key] }))
  const best = dd.ok ? null : dedup_best(samples, OPTS, keys, 0.4)
  if (!dd.ok) note(best ? `dedup judge failed twice: kept the valid sample with ${best.faults} soft fault(s)` : 'dedup judge failed twice: one cluster per option')
  const clusters = dd.ok ? dd.rec.clusters : best ? best.clusters : single
  // P9'(b): the cross-root pairs at title Jaccard >= 0.4 are the violations of the all-singleton clustering
  return { samples, ok: dd.ok, clusters, jaccard_pairs_n: gate_dedup_jaccard(OPTS, single, 0.4).violations.length,
    jaccard_violations_n: gate_dedup_jaccard(OPTS, clusters, 0.4).violations.length }
}

async function overlapJudge() {
  const raw = await agent(P_OVERLAP(A.roots.map(r => ({ id: r.id, question: r.question }))), { label: 'roots:overlap', phase: 'Options', schema: SCHEMA_OVERLAP, agentType: ROLE['qt-bare'], model: 'sonnet', effort: 'low' })
  return { raw, gate: raw ? gate_overlap(raw.pairs, A.roots.map(r => r.id)) : null }
}

// ================= run =================
if (A.phase === 'A') {
  const sheet = A.price_sheet || await priceSheet()
  if (!sheet) return { error: 'price sheet failed twice; pass args.price_sheet to replay', log: LOG }
  GIVEN.price_sheet = sheet
  const records = await parallel(A.picks.map(p => () => replayPick(p)))
  return { phase: 'A', price_sheet: sheet, records: records.map((r, i) => r || { pick: { key: keyOf(A.picks[i]) }, error: 'pick chain threw' }), log: LOG }
}

// phase-A records written before PLAN.restructuring existed have none: read as {sequential_part: '', method: 'none'},
// so gates, core refs, the critic's view and its baseline NA rule see a plan that is not restructured
const withRestructuring = plan => (plan.restructuring ? plan : { ...plan, restructuring: { sequential_part: '', method: 'none' } })
// phase B can be split so each launch carries small args: record slices (skip_branch_jobs) and one branch-level run (skip_records)
const judged = A.skip_records ? [] : A.records.filter(r => r.plan).map(r => ({ ...r, plan: withRestructuring(r.plan) }))
A.records.filter(r => !r.plan).forEach(r => note(`${r.pick.key}: no plan; not judged`))
const skipB = !!A.skip_branch_jobs
const [dram, planted, crit, oc, dd, overlap] = await parallel([
  () => parallel(judged.map(r => guard(`${r.pick.key}: dramaturg`, () => judgeRecord(r)))),
  () => parallel(A.planted_cards.map(c => guard(`planted:${c.id}`, () => judgePlanted(c)))),
  () => parallel(judged.map(r => guard(`${r.pick.key}: critic`, () => critic(r)))),
  () => parallel(skipB ? [] : BRANCH_KEYS.flatMap(bk => [0, 1, 2].map(i => () => optionCritic(bk, i)))),
  skipB ? () => Promise.resolve(null) : guard('dedup judge', dedupJudge),
  skipB ? () => Promise.resolve(null) : guard('overlap judge', overlapJudge),
])
if (skipB) return { phase: 'B', slice: A.slice ?? null, dramaturg: dram, planted, critic: crit, log: LOG }
const dedup = dd || { samples: [], ok: false, clusters: OPTS.map(o => ({ topic: o.title, members: [o.key] })), jaccard_pairs_n: null, jaccard_violations_n: null }
const option_critic = Object.fromEntries(BRANCH_KEYS.map((bk, b) => [bk, oc.slice(3 * b, 3 * b + 3)]))
// branches scored from all samples (i undefined) or from sample i alone; a branch with no sample back is left out, and logged
function scoredBranches(i) {
  const use = bk => (i === undefined ? option_critic[bk] : [option_critic[bk][i]])
  return BRANCH_KEYS.filter(bk => {
    const got = use(bk).some(Boolean)
    if (!got) note(`${bk}: no option-critic sample${i === undefined ? 's' : ` ${i + 1}`}; branch left out`)
    return got
  }).map(bk => scoreBranch(bk, use(bk)))
}
const branches = scoredBranches()
const legacy = BRANCH_KEYS.map(bk => {
  const [root, branch] = bk.split(':')
  return { root, branch, options: A.old_scores[bk].map(s => ({ key: `${bk}:${s.id}`, id: s.id, title: OPT[`${bk}:${s.id}`].title, total: s.total })) }
})
return {
  phase: 'B', dramaturg: dram, planted, critic: crit, option_critic,
  new_scores: Object.fromEntries(branches.map(b => [`${b.root}:${b.branch}`, b.options])),
  dedup, overlap,
  pick_run: runPicks(branches, dedup.clusters),
  pick_run_by_sample: [0, 1, 2].map(i => runPicks(scoredBranches(i), dedup.clusters)),
  pick_run_legacy: pick_run_legacy({ seed: SEED, branches: legacy }),
  log: LOG,
}
