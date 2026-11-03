export const meta = {
  name: 'question-tree-v2',
  description: 'Five root questions -> framer -> physical/interp branches -> option critic -> dedup and seeded picks -> producer PLAN -> rendered card -> dramaturg and critic; returns {table, cards, inventory, frontier, log, result_md, price_sheet}',
  phases: [
    { title: 'Roots', detail: 'PLAYWRIGHT and GUEST, overlap judge, one re-ask' },
    { title: 'Frame', detail: 'FRAMER per root; Lambda price sheet in parallel' },
    { title: 'Branch', detail: 'DEEPENER or WIDENER, plus INTERP' },
    { title: 'Score', detail: 'OPTION CRITIC per branch as it returns' },
    { title: 'Pick', detail: 'dedup judge at the barrier, then the seeded pick rule' },
    { title: 'Produce', detail: 'PRODUCER per pick, extract fallback, G-plan, one cost repair' },
    { title: 'Card', detail: 'render from the card fields, one repair of failing fields' },
    { title: 'Check', detail: 'DRAMATURG and CRITIC; second DRAMATURG on each PASS and 2 seeded REJECTs' },
  ],
}
// @@MODULES@@

// ---------- args (CONTRACT §3 main.js) ----------
let A = args || {}
if (typeof A === 'string') { try { A = JSON.parse(A) } catch (e) { return { error: `args is not JSON: ${e.message}` } } }
if (A.seed === undefined || A.seed === null || !Number.isFinite(Number(A.seed)) || !A.base) return { error: 'args.seed (a number) and args.base are required' }
const SEED = Number(A.seed)
const RUN = `${A.base}/seed-${SEED}`
const ARGS = {
  require_compute_lever: { physical: true, interp: true, ...A.require_compute_lever },
  deepen_on_signal: A.deepen_on_signal ?? false,
  pool_k: A.pool_k ?? 3,
  picks_per_branch: A.picks_per_branch ?? 2,
  budget_usd: A.budget_usd ?? 1000,
  budget_covers_storage: A.budget_covers_storage ?? true,
  budget_covers_tax: A.budget_covers_tax ?? false,
}
const LOG = []   // every exclusion, resample, fallback and annotation
// role names: the five qt-* agent files; overridable by args.agent_types, because a session that started
// before the files existed cannot resolve them (registry is read at session start)
const ROLE = Object.assign({ 'qt-bare': 'qt-bare', 'qt-research': 'qt-research', 'qt-producer': 'qt-producer', 'qt-web': 'qt-web', 'qt-extract': 'qt-extract' }, A.agent_types || {})
const note = m => { LOG.push(m); log(m) }

// ---------- S0: model-free self-tests, before any agent ----------
const failures = Object.entries({ cost: cost_selftest(), pick: pick_selftest(), gates: gate_selftest(), render: render_selftest() })
  .flatMap(([m, r]) => (r.ok ? [] : (r.failures.length ? r.failures : ['not ok']).map(f => `${m}: ${f}`)))
if (failures.length) return { error: `S0 self-test failed (${failures.length})`, failures }

// ---------- fixed vocabularies (CONTRACT §2.3, §2.5, §2.6) ----------
const OC_CRIT = { physical: ['stakes', 'open', 'reshape'], interp: ['stakes', 'open', 'internals', 'reshape'] }
const CARD_CRIT = { physical: ['stakes', 'lever', 'verifiable', 'open', 'reshape', 'baseline'], interp: ['stakes', 'lever', 'verifiable', 'open', 'internals', 'reshape', 'baseline'] }
// card fields: [name in "card:<name>" refs, PLAN path, word cap]; the restructuring pair is shown, checked and sent
// to the dramaturg only on a restructured plan (gates.js)
const CARD = [
  ['question', 'question', 25], ['hypothesis', 'hypothesis', 22],
  ['sequential_part', 'restructuring.sequential_part', 18], ['method', 'restructuring.method', 22],
  ['if_lever', 'predictions.if_lever', 22], ['if_not', 'predictions.if_not', 25],
  ['test_summary', 'test_summary', 45], ['closest_prior', 'novelty.closest_prior', 30],
  ['left_open', 'novelty.left_open', 30], ['anchor', 'anchor.what', 24], ['limits', 'limits', 30],
]
const CAPS = Object.fromEntries(CARD.map(f => [f[1], f[2]]))

// ---------- helpers ----------
const hash8 = id => pick_hashStr(String(id)).toString(16).padStart(8, '0')
const str = v => (typeof v === 'string' ? v : JSON.stringify(v))
const fieldText = (plan, p) => { const v = p.split('.').reduce((x, k) => (x == null ? x : x[k]), plan); return Array.isArray(v) ? v.join(' ') : v == null ? '' : String(v) }
function setField(plan, p, text) {
  const ks = p.split('.'), last = ks.pop(), obj = ks.reduce((x, k) => x[k], plan)
  obj[last] = Array.isArray(obj[last]) ? [text] : text
}
// "settled: ..." and "none"/"none known" are read from the text; anything else is open (CONTRACT §2.2)
const openStatus = s => { const t = String(s ?? '').trim().toLowerCase(); return t.startsWith('settled') ? 'settled' : t === 'none' || t === 'none known' ? 'none' : 'open' }
// "none: <why the work already splits>" is none; any other text names a chain (CONTRACT §2.2)
const seqStatus = s => (String(s ?? '').trim().toLowerCase().startsWith('none') ? 'none' : 'named')
// what a generator or judge may see of an option: the branch agent's fields, never scores or distance
const optionRecord = o => ({ id: o.id, title: o.title, summary: o.summary, root_link: o.root_link, compute_open: o.compute_open, sequential: o.sequential, source_urls: o.source_urls })
const ann = (c, m) => { c.annotations.push(m); note(`${c.tag}: ${m}`) }
const halt = (c, gate, reasons) => { c.halted = { gate, reasons }; note(`${c.tag}: halted at ${gate}: ${reasons.join('; ')}`); return c }
// parallel() turns a throw into null; log it so a script error is never silent
const guard = (what, f) => async () => { try { return await f() } catch (e) { note(`${what}: script error: ${(e && e.message) || e}`); return null } }

// one sample, and one resample when the record fails its check; returns the last non-null record and whether it passed
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

// ---------- price sheet: once per run, in parallel with the roots and framers (cost §8.3) ----------
async function priceSheet() {
  const r = await twice('price sheet',
    s => agent(P_PRICE_SHEET(), { label: `run:price-sheet${s}`, phase: 'Frame', schema: SCHEMA_PRICE_SHEET, agentType: ROLE['qt-web'], model: 'sonnet', effort: 'low' }),
    gate_price_sheet)
  if (r.ok) return r.rec
  note('price sheet failed twice: producers get no sheet; the dramaturg checks each plan\'s rates (rate: items)')
  return null
}

// ---------- S1, S1b: roots ----------
const ROOTS = {}   // id -> {id, source, question, verdict, compute_signals}

async function allRoots() {
  const chain = r => guard(r.id, () => runRoot(r))
  if (A.fixed_roots) return (await parallel(A.fixed_roots.map((q, i) => chain({ id: `R${i + 1}`, source: 'fixed', question: q })))).filter(Boolean).flat()
  // R1 is fixed and starts at once; the generated roots start after the overlap judge and any re-ask
  const r1 = { id: 'R1', source: 'EX2', question: EX2_TEXT }
  const out = await parallel([
    chain(r1),
    guard('roots', async () => (await parallel((await generatedRoots(r1)).map(chain))).filter(Boolean).flat()),
  ])
  return out.filter(Boolean).flat()
}

async function generatedRoots(r1) {
  const GEN = [['PLAYWRIGHT', P_PLAYWRIGHT, 2], ['GUEST', P_GUEST, 4]]
  const ask = (source, fn, extra, stage) => agent(fn(EX1_TEXT, EX2_TEXT) + extra, { label: `roots:${source.toLowerCase()}${stage}`, phase: 'Roots', schema: SCHEMA_QUESTIONS, agentType: ROLE['qt-bare'] })
  const got = await parallel(GEN.map(([source, fn]) => () => ask(source, fn, '', '')))
  const roots = []
  GEN.forEach(([source, , first], g) => {
    const items = (got[g] && got[g].items) || []
    if (!items.length) return note(`${source} failed: R${first}, R${first + 1} dropped`)
    if (items.length !== 2) note(`${source} returned ${items.length} question(s); using the first ${Math.min(2, items.length)}`)
    items.slice(0, 2).forEach((q, i) => roots.push({ id: `R${first + i}`, source, question: q.question }))
  })
  // S1b: overlap judge on all roots; each flagged pair re-asks the later root's generator once,
  // and that generator's new questions replace its flagged roots in order (flow §2.5)
  const all = [r1, ...roots], ids = all.map(r => r.id)
  const ov = await agent(P_OVERLAP(all.map(r => ({ id: r.id, question: r.question }))), { label: 'roots:overlap', phase: 'Roots', schema: SCHEMA_OVERLAP, agentType: ROLE['qt-bare'], model: 'sonnet', effort: 'low' })
  const g = ov ? gate_overlap(ov.pairs, ids) : { ok: false, errors: ['agent returned null'] }
  if (!g.ok) { note(`overlap judge: ${g.errors.join('; ')}; no re-ask`); return roots }
  const later = new Map()
  for (const p of ov.pairs) {
    const [a, b] = [p.a, p.b].sort((x, y) => ids.indexOf(x) - ids.indexOf(y))
    note(`roots ${a} and ${b} overlap: ${p.shared_subject}`)
    later.set(b, a)
  }
  await parallel(GEN.map(([source, fn]) => guard(`${source} re-ask`, async () => {
    const flagged = roots.filter(r => r.source === source && later.has(r.id))
    if (!flagged.length) return
    const keep = all.filter(r => !flagged.includes(r)).map(r => ({ id: r.id, question: r.question }))
    const res = await ask(source, fn, ` ${P_REASK(keep)}`, ':reask')
    flagged.forEach((r, i) => {
      const q = res && res.items && res.items[i]
      if (!q) return note(`${r.id}: ${source} re-ask returned no question; kept despite overlap with ${later.get(r.id)}`)
      note(`${r.id}: replaced by the ${source} re-ask (overlapped ${later.get(r.id)})`)
      r.question = q.question
    })
  })))
  return roots
}

// ---------- S2 framer, S3 branches, S4' option critic as each branch returns ----------
async function runRoot(root) {
  ROOTS[root.id] = root
  const framerPath = `${RUN}/${root.id}/framer.md`
  const fr = await agent(P_FRAMER(root.question, framerPath), { label: `${root.id}:framer`, phase: 'Frame', schema: SCHEMA_VERDICT, agentType: ROLE['qt-research'] })
  if (!fr) { note(`${root.id}: FRAMER failed; root dropped`); return [] }
  root.verdict = fr.verdict
  root.compute_signals = fr.compute_signals || []
  let role = fr.verdict === 'COMPUTE-BOUND' ? 'deepener' : 'widener'
  if (role === 'widener' && ARGS.deepen_on_signal && root.compute_signals.length) role = 'deepener'
  note(`${root.id}: ${fr.verdict}, ${root.compute_signals.length} compute signal(s) -> ${role.toUpperCase()} + INTERP`)
  const branches = [
    { name: 'physical', role, path: `${RUN}/${root.id}/physical-${role}.md` },
    { name: 'interp', role: 'interp', path: `${RUN}/${root.id}/interp.md` },
  ]
  return (await parallel(branches.map(b => guard(`${root.id}:${b.name}`, () => runBranch(root, b, framerPath))))).filter(Boolean)
}

async function runBranch(root, b, framerPath) {
  const tag = `${root.id}:${b.name}`
  let prompt = { widener: P_WIDENER, deepener: P_DEEPENER, interp: P_INTERP }[b.role](framerPath, b.path)
  // deepen_on_signal: the DEEPENER also gets the framer's signals, one line (substrate §10)
  if (b.role === 'deepener' && ARGS.deepen_on_signal && root.compute_signals.length)
    prompt += `\nSignals from the framer: ${root.compute_signals.map(x => `${x.subproblem}: ${x.what_compute_buys}`).join('; ')}`
  const res = await agent(prompt, { label: `${tag}:${b.role}`, phase: 'Branch', schema: SCHEMA_OPTIONS, agentType: ROLE['qt-research'] })
  if (!res || !(res.items || []).length) { note(`${tag}: ${b.role.toUpperCase()} returned no options; branch dropped`); return null }
  const go = gate_opt(res.items)
  if (!go.ok) note(`${tag}: G-opt (annotate only): ${go.errors.join('; ')}`)
  const crit = OC_CRIT[b.name]
  const oc = await twice(`${tag}: option critic`,
    s => agent(P_OPTION_CRITIC(root.question, CRIT_OPTION(b.name), res.items), { label: `${tag}:option-critic${s}`, phase: 'Score', schema: SCHEMA_OPTION_SCORES, agentType: ROLE['qt-bare'] }),
    r => gate_oc(r.items, res.items, crit))
  // after two failures every option is ADJACENT and keeps whatever valid scores came back; a missing score is 1
  if (!oc.ok) note(`${tag}: option critic failed twice: every option labelled ADJACENT; missing scores set to 1`)
  const byId = Object.fromEntries(((oc.rec && oc.rec.items) || []).map(it => [it.id, it]))
  const status = {}, seq = {}
  const scored = res.items.map(o => {
    const it = byId[o.id] || {}
    status[o.id] = openStatus(o.compute_open)
    seq[o.id] = seqStatus(o.sequential)
    const scores = crit.map(c => {
      const s = (it.scores || []).find(x => x.criterion === c)
      return s && Number.isInteger(s.value) && s.value >= 1 && s.value <= 5 ? s : { criterion: c, value: 1, reason: 'missing from the option critic; set to 1' }
    })
    // script floor: a settled or absent compute effect scores open = 1 (CONTRACT §2.3)
    for (const s of scores) if (s.criterion === 'open' && status[o.id] !== 'open' && s.value !== 1) { note(`${tag}:${o.id}: compute_open ${status[o.id]}; open ${s.value} -> 1`); s.value = 1 }
    // and no step-after-step chain named scores reshape = 1, before routing (CONTRACT §2.3)
    for (const s of scores) if (s.criterion === 'reshape' && seq[o.id] === 'none' && s.value !== 1) { note(`${tag}:${o.id}: sequential none; reshape ${s.value} -> 1`); s.value = 1 }
    return { id: o.id, distance: oc.ok ? it.distance : 'ADJACENT', distance_reason: oc.ok ? it.distance_reason : 'option critic failed twice', scores }
  })
  const totals = gate_totals(scored, crit, status)
  const options = res.items.map((o, i) => ({ ...o, ...scored[i], key: `${tag}:${o.id}`, root: root.id, branch: b.name, compute_open_status: status[o.id], sequential_status: seq[o.id], total: totals[o.id] }))
  return { root: root.id, branch: b.name, role: b.role, path: b.path, options }
}

const [SHEET, found] = await parallel([guard('price sheet', priceSheet), guard('roots', allRoots)])
const BRANCHES = found || []

// ---------- barrier; S4 dedup over every option, checked by title Jaccard ----------
const OPTS = BRANCHES.flatMap(b => b.options)
const keys = OPTS.map(o => o.key)
let clusters = []
if (OPTS.length) {
  const samples = [], H = dedup_handles(OPTS)
  const dd = await twice('dedup judge',
    async s => {
      const r = await agent(P_DEDUP(H.lines.map(({ handle, option: o }) => `${handle}: ${o.title}. ${o.summary}`)), { label: `run:dedup${s}`, phase: 'Pick', schema: SCHEMA_DEDUP, agentType: ROLE['qt-bare'], model: 'sonnet', effort: 'low' })
      const t = r && { ...r, clusters: dedup_unhandle(r.clusters, H.toKey) }
      samples.push(t)
      return t
    },
    r => {
      const g = gate_dedup(r.clusters, keys), j = gate_dedup_jaccard(OPTS, r.clusters, 0.4)
      return { ok: g.ok && !g.soft.length && j.ok, errors: [...g.errors, ...g.soft, ...j.violations.map(v => `title Jaccard >= 0.4 not merged: ${str(v)}`)] }
    })
  if (dd.ok) clusters = dd.rec.clusters
  else {
    // soft faults alone never cost the run the judge's partition
    const best = dedup_best(samples, OPTS, keys, 0.4)
    if (best) { note(`dedup judge failed twice: kept the valid sample with ${best.faults} soft fault(s)`); clusters = best.clusters }
    else { note('dedup judge failed twice: one cluster per option'); clusters = OPTS.map(o => ({ topic: o.title, members: [o.key] })) }
  }
}

// ---------- S5 pick (script) ----------
// a seed idea is a string, or an option record {title, text, root_question, kind: 'interp'|'physical', root_link, compute_open,
// sequential, source_urls}; the record form carries its root question to the producer and critic and picks the card criteria
const SEEDS = (A.seed_ideas || []).map((s, i) => typeof s === 'string'
  ? { key: `seed:idea:${i + 1}`, id: String(i + 1), root: 'seed', branch: 'idea', title: s, summary: s }
  : { key: `seed:idea:${i + 1}`, id: String(s.id || i + 1), root: 'seed', branch: 'idea', title: s.title || s.text, summary: s.text || s.summary,
      root_question: s.root_question || null, kind: s.kind === 'interp' ? 'interp' : 'physical',
      root_link: s.root_link, compute_open: s.compute_open, sequential: s.sequential, source_urls: s.source_urls })
const picked = pick_run({
  seed: SEED,
  args: { pool_k: ARGS.pool_k, picks_per_branch: ARGS.picks_per_branch, require_compute_lever: ARGS.require_compute_lever },
  branches: BRANCHES.map(b => ({
    root: b.root, branch: b.branch,
    options: b.options.map(o => ({ key: o.key, id: o.id, title: o.title, total: o.total, scores: Object.fromEntries(o.scores.map(s => [s.criterion, s.value])), distance: o.distance, compute_open_status: o.compute_open_status, sequential_status: o.sequential_status, compute_open: o.compute_open })),
  })),
  clusters,
  seed_ideas: SEEDS.map(s => ({ key: s.key, title: s.title, text: s.summary })),
})
picked.log.forEach(note)

const OPT = Object.fromEntries([...OPTS, ...SEEDS].map(o => [o.key, o]))
const BRANCH_PATH = Object.fromEntries(BRANCHES.map(b => [`${b.root}:${b.branch}`, b.path]))
const CLUSTER = {}
clusters.forEach((c, i) => c.members.forEach(k => { CLUSTER[k] = i }))
const PICKED_IN = {}   // cluster index -> picked keys
for (const p of picked.picks) (PICKED_IN[CLUSTER[p.key]] = PICKED_IN[CLUSTER[p.key]] || []).push(p.key)
const GIVEN = { budget_usd: ARGS.budget_usd, price_sheet: SHEET, budget_covers_storage: ARGS.budget_covers_storage, budget_covers_tax: ARGS.budget_covers_tax }
// U55: per card, copies of what cost_eval_plan and gate_plan received, taken then (a later field repair never reaches them)
const JUDGED = new WeakMap()

// ---------- S6-S9 per pick: producer -> G-plan -> card fields -> dramaturg || critic ----------
async function runPick(p) {
  const o = OPT[p.key]
  const dir = `${RUN}/${o.root}/${o.branch}/${hash8(o.id)}`
  const c = {
    pick: { ...p, id: o.id, title: o.title }, option: o, root_question: ROOTS[o.root] ? ROOTS[o.root].question : (o.root_question || null),
    plan: null, eval: null, given: GIVEN, findings: [null, null], decision: null, decision2: null, critique: null,
    beyond_prior: null, annotations: [], halted: null, producer_path: `${dir}/producer.md`, tag: `${o.root}:${o.branch}:${p.kind}`,
    n_options: OPTS.filter(x => x.root === o.root && x.branch === o.branch).length || null,
  }
  try { await producePick(c, dir) } catch (e) { halt(c, 'script error', [String((e && e.message) || e)]) }
  return c
}

async function producePick(c, dir) {
  let o = c.option
  const at = (stage, phase, extra) => ({ label: `${c.tag}:${stage}`, phase, ...extra })
  // S6: producer; on a schema failure, one extract from producer.md
  let plan = await agent(P_PRODUCER({
    idTitle: `${o.id} "${o.title}"`, branchPath: BRANCH_PATH[`${o.root}:${o.branch}`] || null, path: c.producer_path, dir,
    optionRecord: optionRecord(o), rootQuestion: c.root_question, framerPath: ROOTS[o.root] ? `${RUN}/${o.root}/framer.md` : null,
    priceSheetText: SHEET ? JSON.stringify(SHEET) : null,
  }), at('producer', 'Produce', { schema: SCHEMA_PLAN, agentType: ROLE['qt-producer'] }))
  if (!plan) {
    note(`${c.tag}: PRODUCER returned no valid PLAN; extracting from producer.md`)
    plan = await agent(P_EXTRACT(c.producer_path, dir), at('extract', 'Produce', { schema: SCHEMA_PLAN, agentType: ROLE['qt-extract'], model: 'sonnet', effort: 'low' }))
  }
  if (!plan) return halt(c, 'schema', ['no valid PLAN from the producer or the extract fallback'])
  if (typeof plan.limits === 'string') plan.limits = [plan.limits]   // the schema admits a string; the record keeps a list
  // handoff: a plan for another option of this branch is re-keyed to it; halt only if that option's cluster already has a pick (flow §2.3)
  const norm = t => txt_normalize_title(t || '')
  if (plan.option_title && norm(plan.option_title) !== norm(o.title)) {
    const other = OPTS.find(x => x.root === o.root && x.branch === o.branch && x.key !== o.key && norm(x.title) === norm(plan.option_title))
    if (other) {
      c.plan = plan
      if ((PICKED_IN[CLUSTER[other.key]] || []).some(k => k !== c.pick.key)) return halt(c, 'handoff mismatch', [`the plan is for ${other.key}, whose cluster already has a pick`])
      ann(c, `re-keyed from ${o.key} to ${other.key}: the producer planned "${plan.option_title}"`)
      o = c.option = other
      c.pick = { ...c.pick, key: other.key, id: other.id, title: other.title }
    }
  }
  // two cost-record errors REPAIR_EXPR cannot reach (it rewrites expressions only): a number defined under a question-set id,
  // and a full_scale ratio_to that is not a number id; both are dropped with an annotation before the gate (blind-01, 2026-10-20)
  plan = sanitizePlan(c, plan)
  // G-plan on the script's own evaluation; one repair call for a broken cost record, then halt
  let ev = cost_eval_plan(plan, GIVEN), g = gate_plan(plan, ev, c.pick, ARGS)
  if (g.action === 'repair') {
    note(`${c.tag}: G-plan repair: ${g.reasons.join('; ')}`)
    const fix = await agent(P_REPAIR_EXPR(g.reasons, plan), at('repair-expr', 'Produce', { schema: SCHEMA_REPAIR_EXPR, agentType: ROLE['qt-bare'], model: 'sonnet', effort: 'low' }))
    if (fix) {
      plan = repairedPlan(c, plan, fix)
      ev = cost_eval_plan(plan, GIVEN)
      g = gate_plan(plan, ev, c.pick, ARGS)
    } else note(`${c.tag}: cost repair returned null`)
  }
  c.plan = plan
  c.eval = ev
  JUDGED.set(c, JSON.parse(JSON.stringify({ plan, pick: c.pick, given: GIVEN, gate_args: ARGS })))
  g.annotations.forEach(m => ann(c, m))
  if (g.action === 'repair') return halt(c, 'cost record broken', g.reasons)
  if (g.action === 'halt') return halt(c, 'G-plan', g.reasons)

  // S7: the card renders from the producer's fields; failing fields get one repair, kept only if every number survives
  const cf = gate_cardfields(plan, CAPS)
  cf.annotations.forEach(m => ann(c, m))
  if (!cf.ok) {
    note(`${c.tag}: card fields failing: ${cf.failing.map(f => `${f.field} (${f.reasons.join(', ')})`).join('; ')}`)
    const orig = Object.fromEntries(cf.failing.map(f => [f.field, fieldText(plan, f.field)]))
    const caps = Object.fromEntries(cf.failing.map(f => [f.field, CAPS[f.field]]))
    const fix = await agent(P_REPAIR_FIELDS(orig, caps, plan), at('repair-fields', 'Card', { schema: SCHEMA_REPAIR_FIELDS, agentType: ROLE['qt-bare'], model: 'sonnet', effort: 'low' }))
    if (!fix) note(`${c.tag}: field repair returned null`)
    for (const f of Object.keys(orig)) {
      const t = fix && fix.fields && fix.fields[f]
      if (typeof t !== 'string') continue
      if (gate_number_preservation(orig[f], t)) { setField(plan, f, t); ann(c, `${f}: rewritten by the field repair`) }
      else ann(c, `${f}: the field repair dropped a number; original kept`)
    }
    gate_cardfields(plan, CAPS).failing.forEach(f => ann(c, `card field ${f.field} still fails: ${f.reasons.join(', ')}`))
  }
  const lv = (plan.compute_axis && plan.compute_axis.levels) || [], pm = plan.novelty && plan.novelty.prior_max_level
  c.beyond_prior = typeof pm === 'number' && lv.length ? Math.max(...lv) > pm : null

  // the producer says the closest prior already decides the outcome: rendered and flagged, not judged (options-and-card §3.3)
  if (plan.novelty && plan.novelty.decides === 'yes') return ann(c, 'not judged: the producer says the closest prior already decides this at these levels')

  // S8 dramaturg (second sample on PASS) in parallel with S9 critic, which sees no cost, self-grades or option-critic output
  const cb = o.branch === 'interp' || o.kind === 'interp' ? 'interp' : 'physical'
  const [, cr] = await parallel([
    guard(`${c.tag}: dramaturg`, async () => { await judge(c, 0); if (c.decision && c.decision.result === 'PASS') await judge(c, 1) }),
    guard(`${c.tag}: critic`, () => twice(`${c.tag}: critic`,
      s => agent(P_CRITIC(c.root_question, optionRecord(o), criticCard(plan), criticView(plan), CRIT_CARD(cb)), at(`critic${s}`, 'Check', { schema: SCHEMA_CRITIQUE, agentType: ROLE['qt-bare'], model: 'sonnet' })),
      r => gate_critique(r, CARD.map(f => f[0]), plan, CARD_CRIT[cb]))),
  ])
  c.critique = cr ? cr.rec : null
  if (!c.critique) return ann(c, 'critic returned nothing after a resample')
  if (!cr.ok) ann(c, 'critique failed G-crit after a resample; shown as returned')
  // criteria case 17: a lever this strong should decide in some phase
  const lever = (c.critique.scores || []).find(x => x.criterion === 'lever')
  if (c.critique.decides_by === 'none' && lever && typeof lever.value === 'number' && lever.value >= 4) ann(c, 'inconsistent: decides_by none with lever ≥ 4')
}

// drop what the repair call cannot fix, reading the errors cost_eval_plan reports: a producer number under a question-set
// id ("reserved … is set by the question") and a full_scale[].ratio_to that names no number ("undefined" at that path)
function sanitizePlan(c, plan) {
  const errs = cost_eval_plan(plan, GIVEN).errors || []
  const given = errs.filter(e => e.kind === 'reserved' && /^numbers\./.test(e.where) && /set by the question/.test(e.msg)).map(e => e.where.slice('numbers.'.length))
  const bad = errs.filter(e => e.kind === 'undefined' && /^full_scale\.[^.]+\.ratio_to$/.test(e.where)).map(e => e.where.split('.')[1])
  if (!given.length && !bad.length) return plan   // untouched: the record keeps the producer's own object
  const p = JSON.parse(JSON.stringify(plan))
  if (given.length) { p.numbers = (p.numbers || []).filter(n => !given.includes(n.id)); ann(c, `dropped the producer's definition of ${given.join(', ')}: set by the question`) }
  for (const f of p.full_scale || []) if (bad.includes(f.id) && f.ratio_to) { ann(c, `full_scale.${f.id}.ratio_to dropped: "${f.ratio_to}" is not a number id`); delete f.ratio_to }
  return p
}

// apply REPAIR_EXPR to a copy of the plan: new exprs for numbers, new hours/usd/need for lines
function repairedPlan(c, plan, fix) {
  const p = JSON.parse(JSON.stringify(plan)), missed = []
  for (const n of fix.numbers || []) { const t = (p.numbers || []).find(x => x.id === n.id); if (t) t.expr = n.expr; else missed.push(n.id) }
  for (const l of fix.lines || []) {
    const t = ((p.cost && p.cost.lines) || []).find(x => x.id === l.id)
    if (!t) { missed.push(l.id); continue }
    for (const k of ['hours', 'usd', 'need']) if (l[k] !== undefined) t[k] = l[k]
  }
  ann(c, `cost record repaired: ${(fix.numbers || []).length + (fix.lines || []).length} expression(s) rewritten${missed.length ? `; unknown ids ignored: ${missed.join(', ')}` : ''}`)
  return p
}

// S8: one dramaturg sample (n = 0 first, 1 second) with one resample on a degenerate return; the script's rule decides
async function judge(c, n) {
  const items = gate_dramaturg_items(c.plan, CARD, { rates: !SHEET }), refs = items.map(i => i.ref), stage = n ? 'dramaturg-2' : 'dramaturg'
  const r = await twice(`${c.tag}: ${stage}`,
    s => agent(P_DRAMATURG(items), { label: `${c.tag}:${stage}${s}`, phase: 'Check', schema: SCHEMA_FINDINGS, agentType: ROLE['qt-web'] }),
    f => { const g = gate_findings(f.items, refs); return { ok: g.ok, errors: [...g.errors, ...g.degenerate.map(d => `degenerate: ${str(d)}`)] } })
  if (!r.rec) return ann(c, `${stage} returned nothing after a resample`)
  if (!r.ok) ann(c, `${stage} findings failed G-find after a resample; decided as returned`)
  c.findings[n] = r.rec
  c[n ? 'decision2' : 'decision'] = gate_decision(r.rec.items, gate_core_refs(c.plan), c.plan, c.eval, GIVEN)
}

// what the critic sees (criteria §8.2): plan without cost, full_scale, files_read and the producer's self-grades
function criticView(plan) {
  const { cost, full_scale, compute_tested, compute_tested_why, files_read, ...rest } = plan
  const { expected, expected_why, ...predictions } = plan.predictions || {}
  const { decides, searched, ...novelty } = plan.novelty || {}
  return { ...rest, predictions, novelty }
}
const criticCard = plan => CARD.map(([name, p]) => `card:${name}: ${fieldText(plan, p)}`).join('\n')

const CTX = (await parallel(picked.picks.map(p => guard(p.key, () => runPick(p))))).filter(Boolean)

// two REJECTs lowest in seeded order get a second dramaturg (flow §2.6): it measures REJECT flipping to PASS
const recheck = CTX.filter(c => c.decision && c.decision.result === 'REJECT')
  .sort((x, y) => pick_u(SEED, `recheck:${x.pick.key}`) - pick_u(SEED, `recheck:${y.pick.key}`)).slice(0, 2)
await parallel(recheck.map(c => guard(`${c.tag}: dramaturg-2`, () => judge(c, 1))))

// ---------- S10: each ctx is a card and a table row (render.js reads decision2, producer_path, n_options too) ----------
// a renderer bug must not lose the run: fall back to the raw record and log it
const safe = (what, f, raw) => { try { return f() } catch (e) { note(`render ${what} failed: ${e.message}`); return '```json\n' + JSON.stringify(raw, null, 1) + '\n```' } }
// a num: citation the dramaturg could not confirm (either sample) renders as a GUESS, so the cost block tags it [g] and
// recomputes headroom (cost.md §6); c.plan and c.eval keep the producer's record
function shown(c) {
  const bad = {}
  for (const f of c.findings) for (const it of (f && f.items) || [])
    if (it.ref.startsWith('num:') && ['UNSUPPORTED', 'CONTRADICTED', 'UNREACHABLE'].includes(it.status)) bad[it.ref.slice(4)] = bad[it.ref.slice(4)] || it.status
  if (!c.plan || !Object.keys(bad).length) return c
  const numbers = c.plan.numbers.map(n => {
    if (!bad[n.id]) return n
    const { source_id, quote, page_setting, differs_in, ...rest } = n
    return { ...rest, basis: 'GUESS', rests_on: `citation not confirmed: ${bad[n.id]}` }
  })
  const plan = { ...c.plan, numbers }
  return { ...c, plan, eval: cost_eval_plan(plan, GIVEN) }
}
const SHOWN = CTX.map(shown)
// the producer's prose: the card body before Judges (or the halt), without the header and the script lines (italic labels)
const prose = card => card.split(/\n\n\*\*(?:Judges|Halted at)/)[0].split('\n\n').slice(1).filter(x => !/^\*[^*]/.test(x)).join('\n\n')
const cards = SHOWN.map(c => safe(`card ${c.pick.key}`, () => {
  // a restructured card may run longer by its Restructuring section (caps 18 + 22 words)
  const card = render_card(c), n = txt_words(prose(card)), max = 240 + (gate_restructured(c.plan) ? 40 : 0)
  if (n <= max) return card
  ann(c, `prose over ${max} words (${n})`)
  return render_card(c)   // again, so the card lists the annotation
}, c))
const table = safe('table', () => render_table(SHOWN), CTX.map(c => [c.pick.key, c.halted || (c.decision && c.decision.result)]))
const inventory = safe('inventory', () => render_inventory(picked.inventory), picked.inventory)
const frontier = safe('frontier', () => render_frontier(picked.frontier), picked.frontier)
const isPass = c => c.decision && c.decision.result === 'PASS'
const halts = {}
for (const c of CTX) if (c.halted) halts[c.halted.gate] = (halts[c.halted.gate] || 0) + 1
const header_counts = {
  picks: CTX.length,
  pass: CTX.filter(isPass).length,
  halted: halts,
  // on-goal (flow U3): distinct clusters among first-sample PASS cards whose test varies compute
  u3: new Set(CTX.filter(c => isPass(c) && ['yes', 'partly'].includes(c.plan.compute_tested)).map(c => CLUSTER[c.pick.key] ?? c.pick.key)).size,
  // on-goal (U4): distinct clusters among first-sample PASS cards the critic scores reshape >= 4 and baseline >= 3
  u4: new Set(CTX.filter(c => isPass(c) && [['reshape', 4], ['baseline', 3]].every(([k, min]) => {
    const s = ((c.critique && c.critique.scores) || []).find(x => x.criterion === k)
    return s && typeof s.value === 'number' && s.value >= min
  })).map(c => CLUSTER[c.pick.key] ?? c.pick.key)).size,
}
const result_md = safe('result', () => render_result({ header_counts, table, frontier, cards, inventory, log: LOG }), header_counts)
// calibration state per card (2026-10-21): a judged card whose cost rests on a load-bearing GUESS or PROXY is
// calibration_required until a measure run resolves each input (ledger kind card_number_resolved); the record carries
// what the measure run needs: the inputs, their measuring phase and its line, the anchor and the predictions;
// U55 (2026-11-03): each input's name, unit and band from the plan, and `judged`, what m5/card_resolve.js re-judges with
const calibration = CTX.map(c => {
  const ev = c.eval || {}, plan = c.plan || {}
  const required = (ev.uncertain || []).map(u => {
    const line = (ev.lines || []).find(l => l.phase === u.measured_by) || null
    const phase = (plan.phases || []).find(p => p.id === u.measured_by) || null
    const n = (plan.numbers || []).find(x => x.id === u.id) || {}
    // a band other than {abs: x} with a finite x > 0 counts as absent
    const band = n.band && typeof n.band === 'object' && Object.keys(n.band).length === 1 && Number.isFinite(n.band.abs) && n.band.abs > 0 ? n.band : null
    return { id: u.id, name: n.name ?? null, unit: n.unit ?? null, band, basis: u.basis, value: u.value, differs_in: u.differs_in || [], measured_by: u.measured_by || null, cum_spend_through_measured_by: u.cum_spend_through_measured_by ?? null, k_budget: u.k_budget ?? null,
      phase: phase && { id: phase.id, what: phase.what, gate: phase.gate || null, stop_rule: phase.stop_rule || null }, line: line && { id: line.id, hours: line.hours, usd: line.usd } }
  })
  const state = c.halted ? 'not_judged' : !(c.decision && c.decision.result === 'PASS') ? 'rejected' : required.length ? 'calibration_required' : 'no_unmeasured_input'
  return { key: c.pick.key, title: c.pick.title, state, plan_usd: ev.planned ?? null, required, resolved: [],
    anchor: plan.anchor || null, predictions: plan.predictions ? { if_lever: plan.predictions.if_lever, if_not: plan.predictions.if_not, noise_rule: plan.predictions.noise_rule, expected: plan.predictions.expected } : null,
    judged: c.eval ? JUDGED.get(c) ?? null : null }
})
return { table, cards, inventory, frontier, log: LOG, result_md, price_sheet: SHEET, calibration }
