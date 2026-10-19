// ---------- cost: PLAN.numbers / cost / full_scale -> computed spend, headroom, gates, block, menu ----------
// Pure functions; the script computes every cost figure, the producer only supplies typed inputs.
// Reference behaviour: the design round's cost-sim/gplan.js and its six encodings (tests/fixtures/cost/).

const cost_LITERALS = [0, 0.5, 1, 2, 3, 4, 7, 8, 10, 12, 24, 30, 60, 100, 1000, 1024, 3600, 1e3, 1e6, 1e9, 1e12]
const cost_ARITY = { ceil: [1, 1], floor: [1, 1], min: [1, 99], max: [1, 99], pow: [2, 2] }
const cost_TAG = { CITED: 'c', PROXY: 'p', MEASURED: 'm', DERIVED: '=', DESIGN: 'd', GUESS: 'g' }
const cost_PREC = { '+': 1, '-': 1, '*': 2, '/': 2, neg: 3, '^': 4 }
const cost_OP = { '>=': '≥', '<=': '≤' }
// GIVEN ids, set by the question: a plan refers to them and may not define them (both tagged [q])
const cost_GIVEN = ['budget_usd', 'fs_usd_gib_month']
const cost_LEGEND = 'Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan\'s choice [g] guess [=] computed'
// a number in quoted page text: not inside a word ("H100", "v4"), optional k/K/M/B/T multiplier ("20k steps")
const cost_NUM_IN_TEXT = /(?<![A-Za-z0-9_.])[-−]?\d[\d,]*(?:\.\d+)?(?:[eE][-+]?\d+)?(?:\s?[kKMBT](?![A-Za-z0-9]))?/g
const cost_SUFFIX = { k: 1e3, K: 1e3, M: 1e6, B: 1e9, T: 1e12 }

// ---------- expressions ----------
// Grammar: numbers; ids; + - * / ^ ( ); ceil floor min max pow. ^ is right-associative; unary minus binds looser than ^.
function cost_parse(src) {
  const s = String(src == null ? '' : src)
  const fail = (msg) => { throw { kind: 'parse', msg: `${msg} in "${s}"` } }
  if (!s.trim()) fail('empty expression')
  const re = /\s*(?:(\d+\.?\d*(?:[eE][-+]?\d+)?|\.\d+(?:[eE][-+]?\d+)?)|([A-Za-z_][A-Za-z0-9_]*)|([-+*/^(),]))\s*/y
  const t = []
  while (re.lastIndex < s.length) {
    const at = re.lastIndex, m = re.exec(s)
    if (!m) fail(`unexpected "${s.slice(at).trim()[0]}"`)
    t.push(m[1] !== undefined ? { num: m[1] } : m[2] !== undefined ? { id: m[2] } : { op: m[3] })
  }
  let i = 0
  const peek = () => t[i] && t[i].op
  const expect = (op) => { if (peek() !== op) fail(`expected "${op}"`); i++ }
  const show = (x) => x.op || x.id || x.num
  function add() { let a = mul(); while (peek() === '+' || peek() === '-') { const op = t[i++].op; a = { op, a, b: mul() } } return a }
  function mul() { let a = unary(); while (peek() === '*' || peek() === '/') { const op = t[i++].op; a = { op, a, b: unary() } } return a }
  function unary() { if (peek() === '-') { i++; return { op: 'neg', a: unary() } } return power() }
  function power() { const a = atom(); if (peek() === '^') { i++; return { op: '^', a, b: unary() } } return a }
  function atom() {
    const x = t[i++]
    if (!x) fail('unexpected end')
    if (x.num !== undefined) return { num: Number(x.num), lit: x.num }
    if (x.op === '(') { const e = add(); expect(')'); return e }
    if (x.id === undefined) fail(`unexpected "${x.op}"`)
    if (peek() !== '(') return { id: x.id }
    if (!Object.prototype.hasOwnProperty.call(cost_ARITY, x.id)) fail(`unknown function "${x.id}"`)
    i++
    const args = [add()]
    while (peek() === ',') { i++; args.push(add()) }
    expect(')')
    const [lo, hi] = cost_ARITY[x.id]
    if (args.length < lo || args.length > hi) fail(`${x.id} takes ${lo === hi ? lo : `at least ${lo}`} argument(s)`)
    return { fn: x.id, args }
  }
  const e = add()
  if (i < t.length) fail(`unexpected "${show(t[i])}"`)
  return e
}

function cost_ev(a, val) {
  if (a.num !== undefined) return a.num
  if (a.id !== undefined) return val(a.id)
  if (a.fn) return Math[a.fn](...a.args.map((x) => cost_ev(x, val)))
  if (a.op === 'neg') return -cost_ev(a.a, val)
  const x = cost_ev(a.a, val), y = cost_ev(a.b, val)
  return a.op === '+' ? x + y : a.op === '-' ? x - y : a.op === '*' ? x * y : a.op === '/' ? x / y : Math.pow(x, y)
}

function cost_walk(a, f) { f(a); if (a.a) cost_walk(a.a, f); if (a.b) cost_walk(a.b, f); if (a.args) a.args.forEach((x) => cost_walk(x, f)) }
function cost_ids(a) { const s = new Set(); if (a) cost_walk(a, (n) => { if (n.id !== undefined) s.add(n.id) }); return s }

// Print an AST, substituting ids through sub(id); parentheses only where precedence needs them.
function cost_ast_str(a, sub, parentOp, right) {
  if (a.num !== undefined) return a.lit
  if (a.id !== undefined) return sub(a.id)
  if (a.fn) return `${a.fn}(${a.args.map((x) => cost_ast_str(x, sub)).join(', ')})`
  const p = cost_PREC[a.op]
  const s = a.op === 'neg' ? `-${cost_ast_str(a.a, sub, 'neg', true)}` : `${cost_ast_str(a.a, sub, a.op, false)} ${a.op} ${cost_ast_str(a.b, sub, a.op, true)}`
  const q = parentOp ? cost_PREC[parentOp] : 0
  const wrap = p < q || (p === q && parentOp !== 'neg' && (right ? parentOp !== '^' : parentOp === '^'))
  return wrap ? `(${s})` : s
}

// ---------- record index ----------
// Index ids, parse every expression once, and collect structural errors. Maps are prototype-free so any id string is safe.
function cost_prepare(plan) {
  const errors = [], log = []
  const err = (kind, where, msg) => errors.push({ kind, where, msg })
  const c = plan.cost || {}
  const N = Object.create(null), R = Object.create(null), L = Object.create(null), kinds = Object.create(null), ast = Object.create(null)
  const lists = [[plan.numbers || [], N, 'numbers'], [c.rates || [], R, 'rates'], [c.lines || [], L, 'lines']]
  for (const [list, map, what] of lists) for (const x of list) {
    if (cost_GIVEN.includes(x.id)) err('reserved', `${what}.${x.id}`, `${x.id} is set by the question; refer to it, do not define it`)
    else if (x.id in kinds) err('reserved', `${what}.${x.id}`, `id "${x.id}" is already used in ${kinds[x.id]}`)
    else { map[x.id] = x; kinds[x.id] = what }
  }
  const parse = (where, src) => {
    let a
    try { a = cost_parse(src) } catch (e) { if (e && e.kind === 'parse') return err('parse', where, e.msg); throw e }
    ast[where] = a
    cost_walk(a, (n) => {
      if (n.num !== undefined && !cost_LITERALS.includes(n.num)) log.push(`unlabelled constant ${n.lit} in ${where}`)
      if (n.id !== undefined && !cost_GIVEN.includes(n.id) && !(n.id in kinds)) err('undefined', where, `"${n.id}" is not a number, rate or line id`)
    })
  }
  const given = (x) => x !== undefined && x !== null && x !== ''
  for (const n of plan.numbers || []) {
    if (n.basis === 'DERIVED') parse(`numbers.${n.id}.expr`, n.expr)
    else if (typeof n.value !== 'number' || !Number.isFinite(n.value)) err('undefined', `numbers.${n.id}.value`, `${n.basis} number has no numeric value`)
  }
  for (const l of c.lines || []) {
    for (const k of ['hours', 'need', 'usd']) if (given(l[k])) parse(`lines.${l.id}.${k}`, l[k])
    if (l.rate) {
      if (!(l.rate in R)) err('undefined', `lines.${l.id}.rate`, `rate "${l.rate}" is not defined`)
      if (!given(l.hours)) err('undefined', `lines.${l.id}.hours`, 'a line with a rate needs hours')
    } else if (!given(l.usd)) err('undefined', `lines.${l.id}`, 'a line needs a rate and hours, or usd')
    for (const x of l.instead_of || []) if (!(x in L)) err('undefined', `lines.${l.id}.instead_of`, `line "${x}" is not defined`)
  }
  for (const f of plan.full_scale || []) {
    parse(`full_scale.${f.id}.usd`, f.usd)
    if (f.ratio_to && !(f.ratio_to in N)) err('undefined', `full_scale.${f.id}.ratio_to`, `"${f.ratio_to}" is not a number id`)
  }
  for (const s of c.scenarios || []) for (const k of Object.keys(s.set || {})) if (!(k in N)) err('undefined', `scenarios.${s.id}.set`, `"${k}" is not a number id`)
  for (const y of c.yields || []) if (!(y in N)) err('undefined', 'cost.yields', `"${y}" is not a number id`)
  for (const p of plan.phases || []) if (p.gate && !(p.gate.on in N)) err('gate_ref', `phases.${p.id}.gate.on`, `"${p.gate.on}" is not a number id`)
  // cycles through DERIVED numbers and line expressions
  const deps = (id) => [...cost_ids(ast[`numbers.${id}.expr`]), ...['hours', 'need', 'usd'].flatMap((k) => [...cost_ids(ast[`lines.${id}.${k}`])])]
  const state = Object.create(null)
  const visit = (id, path) => {
    if (state[id] === 2) return
    if (state[id] === 1) return err('cycle', id, `cycle: ${path.slice(path.indexOf(id)).concat(id).join(' -> ')}`)
    state[id] = 1
    for (const d of deps(id)) visit(d, path.concat(id))
    state[id] = 2
  }
  Object.keys(kinds).forEach((id) => visit(id, []))
  const P = { N, R, L, ast, lines: c.lines || [], phases: (plan.phases || []).map((p) => p.id) }
  return { P, errors, log }
}

// Ids reachable from roots through DERIVED expressions and line expressions (roots included).
function cost_ancestors(P, roots) {
  const seen = new Set(), todo = [...roots]
  while (todo.length) {
    const x = todo.pop()
    if (seen.has(x)) continue
    seen.add(x)
    for (const k of [`numbers.${x}.expr`, `lines.${x}.hours`, `lines.${x}.need`, `lines.${x}.usd`]) cost_ids(P.ast[k]).forEach((y) => todo.push(y))
  }
  return seen
}

const cost_is_alt = (l) => !!(l.instead_of && l.instead_of.length)
const cost_counts = (l, storageOut) => !cost_is_alt(l) && !l.optional && !(storageOut && l.kind === 'storage')
const cost_uncertain_basis = (n) => n.basis === 'GUESS' || n.basis === 'PROXY' || (n.basis === 'MEASURED' && (n.differs_in || []).length > 0)

function cost_load_bearing(plan) {
  const { P } = cost_prepare(plan)
  const c = plan.cost || {}
  const roots = P.lines.filter((l) => !cost_is_alt(l) && !l.optional).map((l) => l.id)
    .concat(c.yields || [], (plan.phases || []).filter((p) => p.gate).map((p) => p.gate.on))
  const anc = cost_ancestors(P, roots)
  const nums = (plan.numbers || []).filter((n) => anc.has(n.id))
  return { ids: nums.map((n) => n.id), uncertain: nums.filter(cost_uncertain_basis).map((n) => n.id) }
}

// ---------- prices ----------
const cost_gpu_norm = (s) => String(s || '').toLowerCase().replace(/nvidia/g, '').replace(/[^a-z0-9]/g, '')
const cost_rate_label = (r) => `${r.n_gpus}x ${r.gpu}${r.gpu_memory_gb ? ` ${r.gpu_memory_gb}GB` : ''}`

// 'ok' (stated price is on the sheet), 'corrected' (one sheet entry, other price), 'off' (no or ambiguous entry), 'unchecked' (no sheet)
function cost_sheet_match(r, sheet) {
  if (!sheet || !sheet.instances) return { status: 'unchecked', per: r.per_gpu_usd_h }
  const cands = sheet.instances.filter((x) => cost_gpu_norm(x.gpu) === cost_gpu_norm(r.gpu) && x.n_gpus === r.n_gpus &&
    (!r.gpu_memory_gb || x.gpu_memory_gb === r.gpu_memory_gb))
  if (cands.some((x) => Math.abs(x.per_gpu_usd_h - r.per_gpu_usd_h) < 0.005)) return { status: 'ok', per: r.per_gpu_usd_h }
  if (cands.length === 1) return { status: 'corrected', per: cands[0].per_gpu_usd_h }
  return { status: 'off', per: r.per_gpu_usd_h, n: cands.length }
}

// ---------- evaluation ----------
// One evaluation context: overrides (number id -> value) and whether time boxes stretch to their need.
function cost_ctx(P, ov, stretch) {
  const memo = Object.create(null), lm = Object.create(null)
  const ex = (l, k) => (`lines.${l.id}.${k}` in P.ast ? cost_ev(P.ast[`lines.${l.id}.${k}`], val) : null)
  const line = (l) => {
    if (l.id in lm) return lm[l.id]
    const box = ex(l, 'hours'), need = ex(l, 'need')
    const hours = stretch && box !== null && need !== null ? Math.max(box, need) : box
    const usd = l.rate ? hours * val(l.rate) : ex(l, 'usd')
    return (lm[l.id] = { box, need, hours, usd })
  }
  function val(id) {
    if (id in memo) return memo[id]
    let v
    if (id in ov) v = ov[id]
    else if (id === 'budget_usd') v = P.budget
    else if (id === 'fs_usd_gib_month') v = P.fs_rate
    else if (id in P.N) v = P.N[id].basis === 'DERIVED' ? cost_ev(P.ast[`numbers.${id}.expr`], val) : P.N[id].value
    else if (id in P.R) v = P.rate_usd[id]
    else v = line(P.L[id]).usd
    return (memo[id] = v)
  }
  return { val, line }
}

function cost_run(P, ov, stretch) {
  const c = cost_ctx(P, ov, stretch)
  const rows = P.lines.map((l) => ({ l, ...c.line(l) }))
  const planned = rows.filter((r) => cost_counts(r.l, P.storage_out)).reduce((s, r) => s + r.usd, 0)
  return { c, rows, planned }
}

// Smallest k in [1, 1000] with hit(k), by bisection in log space; null if hit(1000) is false.
function cost_bisect(hit) {
  if (!hit(1000)) return null
  if (hit(1)) return 1
  let lo = 1, hi = 1000
  for (let i = 0; i < 60; i++) { const m = Math.sqrt(lo * hi); if (hit(m)) hi = m; else lo = m }
  return hi
}

function cost_eval_plan(plan, given, opts) {
  opts = opts || {}
  const c = plan.cost || {}
  const { P, errors, log } = cost_prepare(plan)
  const flags = []
  const budget = given.budget_usd
  const name = (id) => { const n = P.N[id]; return n && n.name ? n.name : id }
  const label = (n) => `${n.name || n.id} [${cost_TAG[n.basis] || '?'}]`
  // rates, checked against the price sheet
  const rates = {}, rate_corrections = []
  if (!given.price_sheet) log.push('no price sheet given; rates not checked')
  for (const r of c.rates || []) {
    const m = cost_sheet_match(r, given.price_sheet)
    if (m.status === 'corrected') {
      rate_corrections.push({ id: r.id, stated: r.per_gpu_usd_h, sheet: m.per })
      flags.push(`rate ${cost_rate_label(r)}: plan says $${r.per_gpu_usd_h}/GPU-h, price sheet $${m.per}/GPU-h; sheet price used`)
    }
    if (m.status === 'off') flags.push(`rate ${cost_rate_label(r)} at $${r.per_gpu_usd_h}/GPU-h is not on the price sheet${m.n ? ` (${m.n} entries at other prices)` : ''}; kept as a guess`)
    rates[r.id] = r.n_gpus * m.per
  }
  for (const q of cost_check_quotes(plan)) {
    if (!q.ok) errors.push({ kind: 'quote', where: `numbers.${q.id}.quote`, msg: q.msg })
    else if (q.msg) log.push(`${q.id}: ${q.msg}`)
  }
  // fs_usd_gib_month is the price sheet's filesystem rate; without a sheet a plan that uses it cannot evaluate
  const fsRate = given.price_sheet && given.price_sheet.filesystem ? given.price_sheet.filesystem.usd_gib_month : undefined
  const fsUsed = Object.keys(P.ast).filter((w) => cost_ids(P.ast[w]).has('fs_usd_gib_month'))
  if (typeof fsRate !== 'number') for (const w of fsUsed) errors.push({ kind: 'undefined', where: w, msg: '"fs_usd_gib_month" is read from the price sheet, and none was given' })
  const ov = Object.assign(Object.create(null), opts.overrides || {})
  for (const k of Object.keys(ov)) if (!(k in P.N)) errors.push({ kind: 'undefined', where: 'opts.overrides', msg: `"${k}" is not a number id` })
  if (opts.scenario) {
    const s = (c.scenarios || []).find((x) => x.id === opts.scenario)
    if (s) Object.assign(ov, s.set)
    else errors.push({ kind: 'undefined', where: 'opts.scenario', msg: `scenario "${opts.scenario}" is not defined` })
  }
  // Under overrides or a scenario the plan is evaluated as a scenario is: time boxes stretch to their need.
  const stretch = !!opts.scenario || Object.keys(ov).length > 0
  const out = {
    ok: false, errors, numbers: {}, rates, rate_corrections, lines: [], planned: null, planned_with_options: null,
    alternatives: [], unallocated: null, scenarios: [], yields: [], gates: [], uncertain: [], full_scale: [], flags, log,
  }
  if (errors.some((e) => e.kind !== 'quote' && e.kind !== 'gate_ref')) return out
  Object.assign(P, { rate_usd: rates, budget, fs_rate: fsRate, storage_out: given.budget_covers_storage === false })

  const base = cost_run(P, ov, stretch)
  const counted = base.rows.filter((r) => cost_counts(r.l, P.storage_out))
  for (const n of plan.numbers || []) out.numbers[n.id] = base.c.val(n.id)
  if (fsUsed.length) out.numbers.fs_usd_gib_month = fsRate
  out.lines = base.rows.map((r) => ({
    id: r.l.id, phase: r.l.phase, kind: r.l.kind || 'work', hours: r.hours, usd: r.usd, optional: !!r.l.optional,
    instead_of: r.l.instead_of || [], time_box: !!r.l.rate && (r.need !== null || cost_ids(P.ast[`lines.${r.l.id}.hours`]).size === 0),
    need_h: r.need, margin: r.need ? r.box / r.need : null,
  }))
  out.planned = base.planned
  out.planned_with_options = base.rows.filter((r) => !cost_is_alt(r.l) && !(P.storage_out && r.l.kind === 'storage')).reduce((s, r) => s + r.usd, 0)
  out.alternatives = base.rows.filter((r) => cost_is_alt(r.l)).map((r) => ({
    line_id: r.l.id,
    total: base.planned - counted.filter((x) => r.l.instead_of.includes(x.l.id)).reduce((s, x) => s + x.usd, 0) + r.usd,
  }))
  out.unallocated = budget - base.planned
  const limit = Math.min(c.spend_cap_usd ?? Infinity, budget)
  const withOv = (set) => Object.assign(Object.create(null), ov, set)

  out.scenarios = (c.scenarios || []).map((s) => ({ id: s.id, what: s.what, total: cost_run(P, withOv(s.set), true).planned }))
  out.yields = (c.yields || []).map((y) => ({
    id: y, base: base.c.val(y),
    by_scenario: Object.fromEntries((c.scenarios || []).map((s) => [s.id, cost_ctx(P, withOv(s.set), true).val(y)])),
  }))

  for (const p of plan.phases || []) {
    const g = p.gate
    if (!g || !(g.on in P.N)) continue
    const base_value = base.c.val(g.on)
    const passes = g.op === '<=' ? base_value <= g.value : base_value >= g.value
    const uncut = cost_run(P, withOv({ [g.on]: g.value }), true).planned
    out.gates.push({ phase: p.id, on: g.on, op: g.op, value: g.value, base_value, passes, uncut_total_at_threshold: uncut, else: g.else })
    if (!passes) flags.push(`gate in ${p.id} fails at the plan's own value: ${name(g.on)} is ${cost_fmt_num(base_value)}, needs ${cost_OP[g.op]} ${cost_fmt_num(g.value)}; expected path: ${g.else || 'not stated'}`)
    if (uncut > budget) flags.push(`uncut plan at the ${p.id} gate threshold costs ${cost_fmt_usd(uncut)}, over budget; the plan relies on: ${g.else || 'not stated'}`)
  }

  // uncertain load-bearing inputs: measuring phase, spend so far, headroom
  const order = P.phases, idx = (ph) => order.indexOf(ph)
  const cum = (ph) => (idx(ph) < 0 ? null : counted.filter((r) => idx(r.l.phase) >= 0 && idx(r.l.phase) <= idx(ph)).reduce((s, r) => s + r.usd, 0))
  const anc = (l, k) => cost_ancestors(P, cost_ids(P.ast[`lines.${l.id}.${k}`]))
  const lb = new Set(cost_load_bearing(plan).uncertain)
  for (const n of (plan.numbers || []).filter((x) => lb.has(x.id))) {
    const v0 = base.c.val(n.id)
    const at = (k, d) => withOv({ [n.id]: d > 0 ? v0 * k : v0 / k })
    const spend = (k, d) => cost_run(P, at(k, d), true).planned
    const needSum = (k, d) => cost_run(P, at(k, d), false).rows.reduce((s, r) => s + (r.need || 0), 0)
    const up = spend(10, 1), dn = spend(10, -1)
    const dir = up > dn || (up === dn && needSum(10, 1) >= needSum(10, -1)) ? 1 : -1
    const k_budget = cost_bisect((k) => spend(k, dir) >= limit)
    const boxed = counted.filter((r) => r.need !== null && anc(r.l, 'need').has(n.id)).map((r) => r.l.id)
    const k_box = boxed.length ? cost_bisect((k) => cost_run(P, at(k, dir), false).rows.some((r) => boxed.includes(r.l.id) && r.need > r.box + 1e-9)) : null
    out.uncertain.push({
      id: n.id, basis: n.basis, value: v0, differs_in: n.differs_in || [], measured_by: n.measured_by || null,
      cum_spend_through_measured_by: n.measured_by ? cum(n.measured_by) : null, k_budget, k_box, dir: dir > 0 ? 'higher' : 'lower',
    })
    const dependent = counted.filter((r) => ['hours', 'usd', 'need'].some((k) => anc(r.l, k).has(n.id)) && idx(r.l.phase) >= 0)
    const first = dependent.reduce((m, r) => Math.min(m, idx(r.l.phase)), Infinity)
    if (!n.measured_by) flags.push(`${label(n)} is load-bearing and no phase measures it`)
    else if (idx(n.measured_by) < 0) flags.push(`${label(n)}: measuring phase ${n.measured_by} is not in the plan`)
    else if (idx(n.measured_by) > first) flags.push(`${label(n)} is measured in ${n.measured_by}, after spend that depends on it starts in ${order[first]}`)
    if (k_budget !== null && k_budget < 1.5) flags.push(`thin headroom: the budget is reached if ${name(n.id)} is ${cost_fmt_k(k_budget)}× ${dir > 0 ? 'higher' : 'lower'}`)
  }

  const stated = c.total_stated
  if (typeof stated === 'number') {
    const d = Math.min(Math.abs(base.planned - stated), Math.abs(out.planned_with_options - stated))
    if (d > Math.max(1, 0.02 * stated)) flags.push(`stated total ${cost_fmt_usd(stated)} differs from computed ${cost_fmt_usd(base.planned)}${Math.abs(out.planned_with_options - base.planned) > 0.005 ? ` (with options ${cost_fmt_usd(out.planned_with_options)})` : ''}`)
  }
  if (base.planned > budget) flags.push(`planned spend ${cost_fmt_usd(base.planned)} is over the ${cost_fmt_usd(budget)} budget (stated ${typeof stated === 'number' ? cost_fmt_usd(stated) : 'none'})`)
  // Constant-hours boxes are the default encoding (minimal estimates), so a big box without `need` is logged, not flagged.
  for (const r of counted) {
    const l = r.l, ph = (plan.phases || []).find((p) => p.id === l.phase)
    if (l.rate && r.need === null && cost_ids(P.ast[`lines.${l.id}.hours`]).size === 0 && !(ph && ph.stop_rule) && r.usd >= 0.1 * base.planned) {
      log.push(`time box ${l.id} (${cost_fmt_num(r.hours)} h, ${Math.round(100 * r.usd / base.planned)}% of plan): work not estimated`)
    }
  }

  out.full_scale = (plan.full_scale || []).map((f) => {
    const usd = cost_ev(P.ast[`full_scale.${f.id}.usd`], base.c.val)
    return { id: f.id, what: f.what, usd, multiple_of_budget: usd / budget, ratio_to_value: f.ratio_to ? usd / base.c.val(f.ratio_to) : null }
  })
  out.ok = errors.length === 0
  return out
}

// A CITED/PROXY value must appear as printed in its quote (commas, minus sign and k/M/B multipliers normalised).
// A missing quote is allowed by the schema; it is reported as not checked.
function cost_check_quotes(plan) {
  const out = []
  for (const n of plan.numbers || []) {
    if (n.basis !== 'CITED' && n.basis !== 'PROXY') continue
    if (!n.quote) { out.push({ id: n.id, ok: true, msg: 'no quote given; value not checked against page text' }); continue }
    const found = (String(n.quote).match(cost_NUM_IN_TEXT) || []).map((tok) => {
      const m = /^(.*?)\s?([kKMBT])$/.exec(tok)
      return Number(txt_norm_number(m ? m[1] : tok)) * (m ? cost_SUFFIX[m[2]] : 1)
    })
    const ok = found.some((x) => Math.abs(x - n.value) <= 1e-9 * Math.max(1, Math.abs(n.value)))
    out.push(ok ? { id: n.id, ok, msg: '' } : { id: n.id, ok, msg: `${n.value} does not appear in the quote "${n.quote}"; a value transformed from the page belongs in a DERIVED number` })
  }
  return out
}

// ---------- formatting ----------
function cost_commas(s) { const [i, f] = s.split('.'); return i.replace(/\B(?=(\d{3})+(?!\d))/g, ',') + (f !== undefined ? `.${f}` : '') }
// 3 significant figures; commas below a million, M/B/T above
function cost_fmt_num(x) {
  if (typeof x !== 'number' || !Number.isFinite(x)) return String(x)
  const a = Math.abs(x), sign = x < 0 ? '-' : ''
  for (const [d, s] of [[1e12, 'T'], [1e9, 'B'], [1e6, 'M']]) if (a >= d) return `${sign}${Number((a / d).toPrecision(3))}${s}`
  const r = Number(a.toPrecision(3))
  return sign + (r >= 1000 ? cost_commas(String(r)) : String(r))
}
// dollars to cents below $10,000 (whole dollars without ".00"), 3 significant figures above
function cost_fmt_usd(x) {
  if (typeof x !== 'number' || !Number.isFinite(x)) return '$?'
  const a = Math.abs(x), sign = x < 0 ? '-' : ''
  return `${sign}$${a < 1e4 ? cost_commas(a.toFixed(2)).replace(/\.00$/, '') : cost_fmt_num(a)}`
}
// headroom factors to 2 significant figures
function cost_fmt_k(k) { return k < 10 ? k.toFixed(1) : k < 100 ? k.toFixed(0) : String(Number(k.toPrecision(2))) }
// 6 significant figures for shown working; exponent form from 1e7
function cost_fmt_exact(x) {
  if (typeof x !== 'number' || !Number.isFinite(x)) return String(x)
  const r = Number(x.toPrecision(6))
  return Math.abs(r) >= 1e7 ? r.toExponential().replace('+', '') : String(r)
}
const cost_index = (list) => Object.fromEntries((list || []).map((x) => [x.id, x]))
const cost_words = (s) => s.split(/\s+/).filter(Boolean).length

// The uncertain input whose measurement prices the plan: measured somewhere, tightest headroom first.
function cost_main_guess(ev) {
  const key = (u) => (u.k_budget === null ? Infinity : u.k_budget)
  return ev.uncertain.filter((u) => u.measured_by).reduce((m, u) => (!m || key(u) < key(m) ? u : m), null)
}
const cost_machine_hours = (ev, plan) => {
  const L = cost_index((plan.cost || {}).lines)
  return ev.lines.filter((r) => L[r.id].rate && !r.optional && !r.instead_of.length).reduce((s, r) => s + r.hours, 0)
}

// ---------- rendering ----------
function cost_render_block(ev, plan, given) {
  const c = plan.cost || {}, N = cost_index(plan.numbers), R = cost_index(c.rates), L = cost_index(c.lines), PH = cost_index(plan.phases)
  const usd = cost_fmt_usd, num = cost_fmt_num, budget = given.budget_usd
  const out = ['COST: computed by the pipeline from the plan\'s inputs', cost_LEGEND]
  const sec = (label, items) => (items.length ? items : ['none']).forEach((s, i) => out.push((i ? '' : label).padEnd(11) + s))
  const sheet = given.price_sheet
  const fs = ev.numbers.fs_usd_gib_month !== undefined ? ` · filesystem ${usd(ev.numbers.fs_usd_gib_month)}/GiB-month [q]` : ''
  sec('Budget', [`[q] ${usd(budget)} Lambda on-demand credit · storage ${given.budget_covers_storage === false ? 'not covered' : 'covered'} · tax ${given.budget_covers_tax ? 'covered' : 'not covered'} · ${sheet ? `prices read ${sheet.read_at}` : 'no price sheet'}${fs}`])
  if (ev.planned === null) { sec('Errors', ev.errors.map((e) => `${e.kind} at ${e.where}: ${e.msg}`)); return out.join('\n') }
  const { P } = cost_prepare(plan)
  const exprTag = (src) => (cost_ids(cost_parse(src)).size ? '=' : 'd')
  const rateTxt = (rid) => {
    const r = R[rid], m = cost_sheet_match(r, sheet), per = ev.rates[rid] / r.n_gpus
    return `${cost_rate_label(r)} ${r.n_gpus > 1 ? `${r.n_gpus}×${usd(per)}=` : ''}${usd(ev.rates[rid])}/h${m.status === 'off' ? ' [g]' : ''}`
  }
  const storageOut = given.budget_covers_storage === false
  const lineItem = (r) => {
    const l = L[r.id], what = l.what || (PH[l.phase] && PH[l.phase].what) || ''
    const notes = []
    if (r.need_h !== null) notes.push(`time box; need ${num(r.need_h)} h (margin ${r.margin.toFixed(2)}×)`)
    if (r.optional) notes.push('optional')
    if (storageOut && l.kind === 'storage') notes.push('outside the budget')
    const cost = l.rate ? `${rateTxt(l.rate)}  ${num(r.hours)} h [${exprTag(l.hours)}]` : `[${exprTag(l.usd)}]`
    return [l.phase, what, cost, usd(r.usd)].concat(notes).join('  ')
  }
  // Spend: one row per line, or per phase when the plan has more than 6 lines
  const spend = []
  const main = ev.lines.filter((r) => !r.instead_of.length)
  if (ev.lines.length <= 6) main.forEach((r) => spend.push(lineItem(r)))
  else {
    const counted = main.filter((r) => !r.optional && !(storageOut && L[r.id].kind === 'storage'))
    const phaseIds = [...new Set([...(plan.phases || []).map((p) => p.id), ...counted.map((r) => r.phase)])]
    for (const ph of phaseIds) {
      const rows = counted.filter((r) => r.phase === ph)
      if (!rows.length) continue
      const machines = [...new Set(rows.filter((r) => L[r.id].rate).map((r) => rateTxt(L[r.id].rate)))]
      const h = rows.filter((r) => L[r.id].rate).reduce((s, r) => s + r.hours, 0)
      const boxes = rows.filter((r) => r.need_h !== null).map((r) => `${r.id} need ${num(r.need_h)} h in a ${num(r.hours)} h box`)
      spend.push([ph, (PH[ph] && PH[ph].what) || '', machines.join('; '), h ? `${num(h)} h` : '', usd(rows.reduce((s, r) => s + r.usd, 0)), ...boxes].filter(Boolean).join('  '))
    }
    main.filter((r) => r.optional || (storageOut && L[r.id].kind === 'storage')).forEach((r) => spend.push(lineItem(r)))
  }
  const withOpt = Math.abs(ev.planned_with_options - ev.planned) > 0.005 ? ` · with options ${usd(ev.planned_with_options)}` : ''
  spend.push(`Planned ${usd(ev.planned)} · unallocated ${usd(ev.unallocated)}${withOpt}${c.spend_cap_usd != null ? ` · cap ${usd(c.spend_cap_usd)}` : ''}`)
  for (const a of ev.alternatives) {
    const l = L[a.line_id], r = ev.lines.find((x) => x.id === a.line_id)
    spend.push(`Instead of ${l.instead_of.join(', ')}: ${l.what || a.line_id}, ${l.rate ? `${rateTxt(l.rate)}, ${num(r.hours)} h, ` : ''}${usd(r.usd)} → plan ${usd(a.total)}`)
  }
  sec('Spend', spend)
  // Rests on: at most 4 uncertain inputs, tightest headroom first; each gate goes with the input it depends on
  const key = (u) => (u.k_budget === null ? 1e9 : u.k_budget)
  const unc = ev.uncertain.slice().sort((a, b) => key(a) - key(b))
  const shown = unc.slice(0, 4), gateAnc = ev.gates.map((g) => cost_ancestors(P, [g.on]))
  const gateTxt = (g) => `gate ${N[g.on].name || g.on} ${cost_OP[g.op]} ${num(g.value)} in ${g.phase} (now ${num(g.base_value)}, ${g.passes ? 'passes' : 'fails'}; uncut plan at it ${usd(g.uncut_total_at_threshold)})${g.else ? `, else ${g.else}` : ''}`
  const used = new Set()
  const rests = shown.map((u) => {
    const n = N[u.id]
    const parts = [`${n.name || u.id} ${num(u.value)}${n.unit && n.unit !== '1' ? ` ${n.unit}` : ''} [${cost_TAG[n.basis]}]${n.quote ? ` "${n.quote}"` : n.rests_on ? ` rests on: ${n.rests_on}` : ''}`]
    if (u.differs_in.length) parts.push(`differs: ${u.differs_in.join(', ')}`)
    parts.push(u.measured_by ? `measured in ${u.measured_by}${u.cum_spend_through_measured_by !== null ? ` (${usd(u.cum_spend_through_measured_by)} spent by then)` : ''}` : 'no phase measures it')
    ev.gates.forEach((g, i) => { if (!used.has(i) && gateAnc[i].has(u.id)) { used.add(i); parts.push(gateTxt(g)) } })
    const atK = u.dir === 'higher' ? u.value * u.k_budget : u.value / u.k_budget
    parts.push(u.k_budget !== null ? `budget reached at ${num(atK)} (${cost_fmt_k(u.k_budget)}× ${u.dir})` : 'budget not reached within 1000×')
    if (u.k_box !== null) parts.push(`box overflows at ${cost_fmt_k(u.k_box)}×`)
    return parts.join(' · ')
  })
  ev.gates.forEach((g, i) => { if (!used.has(i)) rests.push(gateTxt(g)) })
  if (unc.length > shown.length) rests.push(`+${unc.length - shown.length} more: ${unc.slice(4).map((u) => N[u.id].name || u.id).join(', ')}`)
  sec('Rests on', rests)
  sec('Scenarios', ev.scenarios.length ? [ev.scenarios.map((s) => `${s.what || s.id} → ${usd(s.total)}${s.total > budget ? ' (over budget)' : ''}`).join(' · ')] : [])
  const S = cost_index(c.scenarios)
  sec('Buys', ev.yields.map((y) => `${N[y.id].name || y.id}: ${num(y.base)} [${cost_TAG[N[y.id].basis]}]${Object.entries(y.by_scenario).map(([sid, v]) => ` · ${S[sid].what || sid}: ${num(v)}`).join('')}`))
  sec('Flags', ev.errors.map((e) => `error (${e.kind}) at ${e.where}: ${e.msg}`).concat(ev.flags))
  const F = cost_index(plan.full_scale)
  sec('Full scale', ev.full_scale.map((f) => {
    const leaves = [...cost_ancestors(P, cost_ids(P.ast[`full_scale.${f.id}.usd`]))].filter((id) => N[id] && N[id].basis !== 'DERIVED').map((id) => N[id])
    const tags = Object.entries(leaves.reduce((m, n) => ({ ...m, [cost_TAG[n.basis]]: (m[cost_TAG[n.basis]] || 0) + 1 }), {})).map(([t, k]) => `${k} ${t}`)
    const unsure = leaves.filter((n) => n.basis === 'GUESS' || n.basis === 'PROXY').map((n) => `[${cost_TAG[n.basis]}] ${n.name || n.id}`)
    const ratio = f.ratio_to_value !== null ? ` = ${num(f.ratio_to_value)}× ${N[F[f.id].ratio_to].name || F[f.id].ratio_to}` : ''
    return `${f.what}: ${usd(f.usd)} = ${num(f.multiple_of_budget)}× budget${ratio}${tags.length ? ` · inputs ${tags.join(', ')}` : ''}${unsure.length ? ` (${unsure.join('; ')})` : ''}`
  }))
  sec('Outside', (plan.outside_budget || []).length ? [plan.outside_budget.map((o) => `${o.what}: ${o.qty} ${o.unit}`).join(' · ')] : [])
  return out.join('\n')
}

// Card body line, at most 45 words: sentences are added in priority order while they fit.
function cost_render_short(ev, plan) {
  if (ev.planned === null) return `The cost record did not evaluate (${ev.errors.length} error${ev.errors.length === 1 ? '' : 's'}); see the cost block.`
  const N = cost_index(plan.numbers), usd = cost_fmt_usd, budget = ev.planned + ev.unallocated, h = cost_machine_hours(ev, plan)
  const s = [ev.planned > budget
    ? `Over budget: plans ${usd(ev.planned)} against the ${usd(budget)} budget.`
    : `Plans ${usd(ev.planned)} of the ${usd(budget)} budget${h ? ` over ${cost_fmt_num(h)} machine-hours` : ''}, leaving ${usd(ev.unallocated)}.`]
  const m = cost_main_guess(ev)
  if (m) {
    const n = N[m.id]
    s.push(`Main guess: ${n.name || m.id} [${cost_TAG[n.basis]}], measured${m.cum_spend_through_measured_by !== null ? ` after ${usd(m.cum_spend_through_measured_by)} of spend` : ' first'}${m.k_budget !== null ? `; the budget is reached if it is ${cost_fmt_k(m.k_budget)}× ${m.dir}` : ''}.`)
  }
  const big = ev.full_scale.reduce((b, f) => (!b || f.multiple_of_budget > b.multiple_of_budget ? f : b), null)
  if (big) s.push(`Full scale: ${big.what}, ${usd(big.usd)}, ${cost_fmt_num(big.multiple_of_budget)}× the budget.`)
  const g = ev.gates[0]
  if (g) s.push(`Pilot gate: ${N[g.on].name || g.on} ${cost_OP[g.op]} ${cost_fmt_num(g.value)}${g.passes ? '' : ' (fails at the plan\'s own value)'}${g.else ? `, else ${g.else}` : ''}.`)
  if (ev.flags.length) s.push(`${ev.flags.length} cost flag${ev.flags.length === 1 ? '' : 's'} in the block.`)
  const out = []
  let w = 0
  for (const x of s) { const k = cost_words(x); if (w + k <= 45) { out.push(x); w += k } }
  return out.join(' ')
}

// Appendix: every DERIVED number, id-bearing line expression and full-scale figure with values substituted.
function cost_render_derivations(ev, plan) {
  if (ev.planned === null) return 'Derivations: the cost record did not evaluate.'
  const lineById = cost_index(ev.lines)
  const value = (id) => (id === 'budget_usd' ? ev.planned + ev.unallocated : id in ev.numbers ? ev.numbers[id] : id in ev.rates ? ev.rates[id] : lineById[id].usd)
  const show = (src, v, unit) => {
    const a = cost_parse(src), subst = cost_ids(a).size ? ` = ${cost_ast_str(a, (id) => cost_fmt_exact(value(id)))}` : ''
    return `${src}${subst} = ${cost_fmt_exact(v)}${unit ? ` ${unit}` : ''}`
  }
  const out = ['Derivations: each computed number with its inputs substituted']
  for (const n of plan.numbers || []) if (n.basis === 'DERIVED') out.push(`${n.id} = ${show(n.expr, ev.numbers[n.id], n.unit)}`)
  for (const l of (plan.cost || {}).lines || []) {
    const r = lineById[l.id]
    for (const [k, v, unit] of [['hours', r.hours, 'h'], ['need', r.need_h, 'h'], ['usd', r.usd, 'usd']]) {
      if (l[k] !== undefined && l[k] !== null && l[k] !== '' && cost_ids(cost_parse(l[k])).size) out.push(`${l.id}.${k} = ${show(l[k], v, unit)}`)
    }
  }
  for (const f of ev.full_scale) out.push(`${f.id} = ${show(cost_index(plan.full_scale)[f.id].usd, f.usd, 'usd')}`)
  return out.join('\n')
}

// Placeholder menu for the writer side cell: rendered values only, so prose never retypes a computed number.
function cost_menu(ev, plan) {
  if (ev.planned === null) return []
  const N = cost_index(plan.numbers), usd = cost_fmt_usd, num = cost_fmt_num, out = []
  const add = (id, name, value, tag) => { if (!out.some((x) => x.id === id)) out.push({ id, name, value, tag }) }
  add('planned_usd', 'planned spend', usd(ev.planned), '=')
  add('planned_h', 'planned machine-hours', num(cost_machine_hours(ev, plan)), '=')
  add('unallocated_usd', 'budget left unallocated', usd(ev.unallocated), '=')
  if (Math.abs(ev.planned_with_options - ev.planned) > 0.005) add('planned_with_options_usd', 'planned spend including optional lines', usd(ev.planned_with_options), '=')
  const m = cost_main_guess(ev)
  if (m && m.cum_spend_through_measured_by !== null) add('pilot_cum_usd', `spend through the phase that measures ${N[m.id].name || m.id}`, usd(m.cum_spend_through_measured_by), '=')
  if (m && m.k_budget !== null) add('headroom', `how many times ${m.dir} ${N[m.id].name || m.id} can be before the budget is reached`, cost_fmt_k(m.k_budget), '=')
  ev.gates.forEach((g, i) => add(i ? `gate_value_${i + 1}` : 'gate_value', `pilot gate threshold on ${N[g.on].name || g.on}`, num(g.value), 'd'))
  for (const f of ev.full_scale) {
    const id = f.id.startsWith('fs_') ? f.id : `fs_${f.id}`, F = cost_index(plan.full_scale)[f.id]
    add(id, f.what, usd(f.usd), '=')
    add(`${id}_x`, `${f.what}, as a multiple of the budget`, num(f.multiple_of_budget), '=')
    if (f.ratio_to_value !== null) add(`${id}_ratio`, `${f.what}, as a multiple of ${N[F.ratio_to].name || F.ratio_to}`, num(f.ratio_to_value), '=')
  }
  const ax = plan.compute_axis
  if (ax && (ax.levels || []).length >= 2 && Math.min(...ax.levels) > 0) add('axis_span', `span of the compute axis (${ax.quantity}), largest level over smallest`, num(Math.max(...ax.levels) / Math.min(...ax.levels)), 'd')
  for (const y of ev.yields) add(y.id, `${N[y.id].name || y.id}${N[y.id].unit ? ` (${N[y.id].unit})` : ''}`, num(y.base), cost_TAG[N[y.id].basis])
  for (const n of plan.numbers || []) if (n.basis === 'DERIVED') add(n.id, `${n.name || n.id}${n.unit ? ` (${n.unit})` : ''}`, num(ev.numbers[n.id]), '=')
  return out
}

// ---------- S0 self-test: planted cases (cost.md §8.2 plus the contract's cases) ----------
function cost_selftest() {
  const failures = []
  const near = (x, y, tol) => typeof x === 'number' && Math.abs(x - y) <= tol
  const given = {
    budget_usd: 1000, budget_covers_storage: true, budget_covers_tax: false,
    price_sheet: {
      read_at: 'selftest', filesystem: { usd_gib_month: 0.2, page_text: 'selftest', example: true },
      instances: [
        { gpu: 'A100 SXM', gpu_memory_gb: 40, n_gpus: 8, per_gpu_usd_h: 1.99, page_text: 'selftest' },
        { gpu: 'H100 SXM', gpu_memory_gb: 80, n_gpus: 1, per_gpu_usd_h: 4.29, page_text: 'selftest' },
        { gpu: 'H100 SXM', gpu_memory_gb: 80, n_gpus: 8, per_gpu_usd_h: 3.99, page_text: 'selftest' },
      ],
    },
  }
  const r1 = { id: 'r1', gpu: 'H100 SXM', gpu_memory_gb: 80, n_gpus: 1, per_gpu_usd_h: 4.29 }
  const r8 = { id: 'r8', gpu: 'H100 SXM', gpu_memory_gb: 80, n_gpus: 8, per_gpu_usd_h: 3.99 }
  const ra = { id: 'ra', gpu: 'A100 SXM', gpu_memory_gb: 40, n_gpus: 8, per_gpu_usd_h: 1.99 }
  const plan = (numbers, rates, lines, total, phases, scenarios) => ({
    phases: phases || [{ id: 'P0', what: 'pilot' }, { id: 'P1', what: 'main runs' }], numbers,
    cost: { rates, lines, scenarios: scenarios || [], total_stated: total }, full_scale: [], outside_budget: [],
  })
  const work = (id, phase, hours, extra) => ({ id, phase, what: id, kind: 'work', rate: 'r1', hours, ...extra })
  const cases = {
    // pick 6 (W13): scenarios $676.60 / $761.89 / $875.60; budget reached at 1.93x slower training
    p06: [plan([
      { id: 'lr_steps', name: 'steps in LeRobot SmolVLA timing', unit: 'steps', basis: 'PROXY', value: 20000, source_id: 's_lerobot', quote: '20k steps will roughly take ~4 hrs on a single A100 GPU', page_setting: 'SmolVLA fine-tune, 1x A100', differs_in: ['dataset'], measured_by: 'P0' },
      { id: 'lr_hours', name: 'hours for those steps', unit: 'h', basis: 'PROXY', value: 4, source_id: 's_lerobot', page_setting: 'same', differs_in: ['dataset'], measured_by: 'P0' },
      { id: 'sph', name: 'training steps per A100-hour', unit: 'steps/GPU-h', basis: 'DERIVED', expr: 'lr_steps / lr_hours' },
      { id: 's_a', name: 'steps, arm A', unit: 'steps', basis: 'DESIGN', value: 200000 },
      { id: 's_c', name: 'step-equivalents, arm C', unit: 'steps', basis: 'DERIVED', expr: '2 * 50000 * c_full' },
      { id: 'c_full', name: 'full fine-tune step cost vs expert-only', unit: 'x', basis: 'GUESS', value: 2, rests_on: 'producer assumption', measured_by: 'P0' },
      { id: 's_b50', name: 'steps, arm B 50k', unit: 'steps', basis: 'DESIGN', value: 200000 },
      { id: 's_bp', name: "steps, arm B'", unit: 'steps', basis: 'DESIGN', value: 200000 },
      { id: 's_w2', name: 'steps in wave 2', unit: 'steps', basis: 'DESIGN', value: 250000 },
      { id: 'gpus_w1', name: 'GPUs in wave 1', unit: 'GPUs', basis: 'DESIGN', value: 8 },
      { id: 'gpus_w2', name: 'GPUs in wave 2', unit: 'GPUs', basis: 'DESIGN', value: 5 },
      { id: 'gpuh_w1', name: 'A100-hours, wave 1', unit: 'GPU-h', basis: 'DERIVED', expr: '(s_a + s_c + s_b50 + s_bp) / sph' },
      { id: 'gpuh_w2', name: 'A100-hours, wave 2', unit: 'GPU-h', basis: 'DERIVED', expr: 's_w2 / sph' },
    ], [ra], [
      { id: 'pilot', phase: 'P0', what: 'pilot', kind: 'work', rate: 'ra', hours: '2' },
      { id: 'wave1', phase: 'W1', what: 'wave 1', kind: 'work', rate: 'ra', hours: 'gpuh_w1 / gpus_w1' },
      { id: 'wave2', phase: 'W2', what: 'wave 2', kind: 'work', rate: 'ra', hours: 'gpuh_w2 / gpus_w2' },
      { id: 'evtail', phase: 'EV', what: 'evaluation tail', kind: 'work', rate: 'ra', hours: '3' },
    ], 557, [{ id: 'P0', what: 'pilot' }, { id: 'W1', what: 'wave 1' }, { id: 'W2', what: 'wave 2' }, { id: 'EV', what: 'evaluation' }],
    [{ id: 's4000', what: '4,000 steps/A100-h', set: { sph: 4000 } }, { id: 's3500', what: '3,500', set: { sph: 3500 } }, { id: 's3000', what: '3,000', set: { sph: 3000 } }]), (ev) => {
      const t = ev.scenarios.map((s) => s.total), u = ev.uncertain.find((x) => x.id === 'lr_steps')
      return near(ev.planned, 557.2, 0.005) && near(t[0], 676.6, 0.005) && near(t[1], 761.89, 0.005) && near(t[2], 875.6, 0.005) && u && near(u.k_budget, 1.93, 0.005)
    }],
    // a GUESS reachable only through a time box's need must be load-bearing, and flagged when nothing measures it
    need_only: [plan([
      { id: 'tok', name: 'tokens to generate', unit: 'tokens', basis: 'DESIGN', value: 2e6 },
      { id: 'tps', name: 'generation speed', unit: 'tok/s', basis: 'GUESS', value: 100, rests_on: 'producer estimate' },
    ], [r1], [work('a', 'P0', '2'), work('b', 'P1', '8', { need: 'tok / tps / 3600' })], 42.9), (ev, p) =>
      cost_load_bearing(p).uncertain.includes('tps') && ev.uncertain.some((u) => u.id === 'tps' && u.k_box !== null) &&
      ev.flags.some((f) => f.startsWith('generation speed [g] is load-bearing and no phase measures it'))],
    // a pilot gate the plan's own value fails (pick 18's shape)
    gate_fails: [{ ...plan([{ id: 'thr', name: 'pilot throughput', unit: 'samples/s', basis: 'GUESS', value: 5, rests_on: 'estimate', measured_by: 'P0' }],
      [r1], [work('a', 'P0', '2'), work('b', 'P1', '10')], 51.48), phases: [{ id: 'P0', what: 'pilot', gate: { on: 'thr', op: '>=', value: 13, else: 'config B' } }, { id: 'P1', what: 'main' }] },
    (ev) => ev.gates.length === 1 && ev.gates[0].passes === false && ev.flags.some((f) => f.startsWith('gate in P0 fails'))],
    // a GUESS with 1.02x headroom: 61.58 h x $15.92 = $980.35, budget reached at 1.02x
    thin: [plan([
      { id: 'steps', name: 'steps', unit: 'steps', basis: 'DESIGN', value: 61580 },
      { id: 'sph', name: 'steps per hour', unit: 'steps/h', basis: 'GUESS', value: 1000, rests_on: 'estimate', measured_by: 'P1' },
    ], [ra], [{ id: 'run', phase: 'P1', what: 'run', kind: 'work', rate: 'ra', hours: 'steps / sph' }], 980.35), (ev) =>
      ev.uncertain.some((u) => u.id === 'sph' && near(u.k_budget, 1.02, 0.001)) && ev.flags.some((f) => f.startsWith('thin headroom'))],
    // computed $1,040 with $1,040 stated: the halt condition must be visible as planned > budget
    over: [plan([], [r8], [{ id: 'a', phase: 'P1', what: 'runs', kind: 'work', rate: 'r8', hours: '30' }, { id: 'b', phase: 'P1', what: 'reruns', kind: 'allotment', usd: '82.4' }], 1040),
      (ev, p) => near(ev.planned, 1040, 0.005) && ev.planned > 1000 && p.cost.total_stated > 1000 && ev.flags.some((f) => f.startsWith('planned spend $1,040 is over'))],
    undefined_id: [plan([{ id: 'steps', name: 'steps', unit: 'steps', basis: 'DESIGN', value: 100 }], [r1], [work('a', 'P1', 'steps / speed')], 10),
      (ev) => !ev.ok && ev.errors.some((e) => e.kind === 'undefined' && e.where === 'lines.a.hours')],
    quote: [plan([{ id: 'bw', name: 'HBM bandwidth', unit: 'TB/s', basis: 'CITED', value: 3.35, source_id: 's1', quote: 'up to 4.8TB/s of memory bandwidth' }], [r1], [work('a', 'P1', '2')], 8.58),
      (ev) => !ev.ok && ev.errors.some((e) => e.kind === 'quote' && e.where === 'numbers.bw.quote')],
    // the default minimal encoding: two lines, constant hours, one rate, a total; nothing to flag
    minimal: [plan([], [r1], [work('a', 'P0', '2'), work('b', 'P1', '10')], 51.48),
      (ev) => ev.ok && near(ev.planned, 51.48, 0.005) && ev.flags.length === 0],
  }
  for (const [name, [p, check]] of Object.entries(cases)) {
    try { if (!check(cost_eval_plan(p, given), p)) failures.push(`cost selftest ${name}: check failed`) }
    catch (e) { failures.push(`cost selftest ${name}: threw ${e && e.msg ? e.msg : e}`) }
  }
  return { ok: failures.length === 0, failures }
}
