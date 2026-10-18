// ---------- gates (deterministic checks on returned records; S0 runs gate_selftest) ----------
// Record arguments are the arrays inside {items} / {clusters} / {pairs}; whole records otherwise.

// Plan field lookup: "predictions.if_lever", "phases.0.id", "phases[0].id", or an array element by id ("phases.P1").
function gate_get(obj, path) {
  let cur = obj
  for (const k of String(path).replace(/\[([^\]]+)\]/g, '.$1').split('.').filter(Boolean)) {
    if (cur === null || cur === undefined) return undefined
    cur = Array.isArray(cur) && !/^\d+$/.test(k) ? cur.find(x => x && x.id === k) : cur[k]
  }
  return cur
}
const gate_text = (plan, path) => {
  const v = gate_get(plan, path)
  return Array.isArray(v) ? v.join(' ') : String(v ?? '')
}

// Card fields: plan path -> word cap (CONTRACT §2.5). limits is capped joined. The restructuring fields are card
// fields only on a restructured plan (the card shows them only there).
const gate_card_caps = {
  question: 25, hypothesis: 22, 'predictions.if_lever': 22, 'predictions.if_not': 25, test_summary: 45,
  'novelty.closest_prior': 30, 'novelty.left_open': 30, 'anchor.what': 24, limits: 30,
  'restructuring.sequential_part': 18, 'restructuring.method': 22,
}
// Core card fields (the dramaturg's blocking set): ref name -> plan path.
const gate_CORE = {
  question: 'question', hypothesis: 'hypothesis', test_summary: 'test_summary', if_lever: 'predictions.if_lever',
  if_not: 'predictions.if_not', anchor: 'anchor.what', closest_prior: 'novelty.closest_prior',
}
const gate_STATUS = ['SUPPORTED', 'PARTIAL', 'UNSUPPORTED', 'CONTRADICTED', 'UNREACHABLE']
// A plan is restructured when restructuring.method, trimmed and lowercased, is not "none". A missing restructuring
// (a record from before the field existed) or an empty method counts as none.
const gate_restructured = plan => !['', 'none'].includes(String(((plan && plan.restructuring) || {}).method ?? '').trim().toLowerCase())
const gate_restructuring_field = path => String(path).startsWith('restructuring.')

// Source ids cited in a card field as [s1] or [s1, s3]; bracketed text with spaces is not a citation.
function gate_cited_ids(s) {
  const out = []
  for (const m of String(s ?? '').matchAll(/\[([^[\]]+)\]/g))
    for (const id of m[1].split(/[,;]/).map(x => x.trim())) if (/^[\w.:-]+$/.test(id)) out.push(id)
  return out
}

// Required fields that are absent (undefined or null), by walking the schema; anyOf passes if one branch does.
function gate_missing(schema, v, path) {
  if (schema.anyOf) {
    const tries = schema.anyOf.map(s => gate_missing(s, v, path))
    return tries.find(t => !t.length) || tries[0]
  }
  if (schema.type === 'array' && Array.isArray(v)) return v.flatMap((x, i) => gate_missing(schema.items, x, `${path}${i}.`))
  if (schema.type !== 'object' || v === null || typeof v !== 'object') return []
  const out = (schema.required || []).filter(k => v[k] === undefined || v[k] === null).map(k => path + k)
  for (const [k, s] of Object.entries(schema.properties || {}))
    if (v[k] !== undefined && v[k] !== null) out.push(...gate_missing(s, v[k], `${path}${k}.`))
  return out
}

// Cost figures belong to the script's cost line, which computes them: a dollar figure (the budget "$1,000" excepted),
// a multiple of the budget, compute-hours (substrate G-card regexes; cost.md §5).
function gate_cost_text(s) {
  const t = String(s ?? '').replace(/\$\s?1,000(?![\d,.])/g, '')
  if (/\$\s?\d/.test(t)) return 'dollar figure'
  if (/\d[\d,.]*\s*(\u00d7|x|times)\s+(the|this|a|our)?\s*budget/i.test(t)) return 'multiple of the budget'
  if (/\d[\d,.]*\s*(GPU|machine|node|instance)[- ]?hours?/i.test(t)) return 'compute-hours'
  return ''
}

function gate_opt(options) {
  const errors = []
  if (options.length < 3 || options.length > 25) errors.push(`${options.length} options (want 3 to 25)`)
  const seen = new Set()
  for (const o of options) {
    if (seen.has(o.id)) errors.push(`duplicate id ${o.id}`)
    seen.add(o.id)
    for (const f of ['id', 'title', 'summary', 'root_link', 'compute_open', 'sequential']) if (!String(o[f] ?? '').trim()) errors.push(`${o.id}: empty ${f}`)
  }
  return { ok: !errors.length, errors }
}

// Option critic. No NA (criteria.md §6). A reason under 15 characters or equal to the criterion name is degenerate
// (latent_skeptic's rule: schema-valid but content-free); degenerate makes ok false so the caller can resample.
function gate_oc(scores, options, criteria) {
  const errors = [], degenerate = new Set(), seen = new Set()
  const ids = new Set(options.map(o => o.id))
  for (const it of scores) {
    if (!ids.has(it.id)) errors.push(`unknown id ${it.id}`)
    if (seen.has(it.id)) errors.push(`duplicate id ${it.id}`)
    seen.add(it.id)
    if (!['SAME', 'ADJACENT', 'ELSEWHERE'].includes(it.distance)) errors.push(`${it.id}: distance ${it.distance}`)
    for (const c of criteria) {
      const s = (it.scores || []).find(x => x.criterion === c)
      if (!s) { errors.push(`${it.id}: missing ${c}`); continue }
      if (!Number.isInteger(s.value) || s.value < 1 || s.value > 5) errors.push(`${it.id}: ${c} = ${JSON.stringify(s.value)}`)
      const r = String(s.reason ?? '').trim()
      if (r.length < 15 || r.toLowerCase() === c.toLowerCase()) degenerate.add(it.id)
    }
  }
  for (const id of ids) if (!seen.has(id)) errors.push(`missing id ${id}`)
  return { ok: !errors.length && !degenerate.size, errors, degenerate: [...degenerate] }
}

// Totals = sum over the branch's criteria; `open` counts 1 when compute_open is settled or none. `reshape` routes the
// top pick and the pool and is left out, so the open route and the legacy reproduction keep their totals.
function gate_totals(scores, criteria, statusById) {
  const out = {}
  for (const it of scores) {
    const floor = ['settled', 'none'].includes(statusById[it.id])
    out[it.id] = criteria.filter(c => c !== 'reshape').reduce((t, c) => t + (c === 'open' && floor ? 1 : Number((it.scores.find(x => x.criterion === c) || {}).value)), 0)
  }
  return out
}

// ok covers the partition only (every key in exactly one cluster, no unknown key); a topic under 3 words is a soft
// fault: it triggers the resample with the Jaccard check but never costs the run a valid partition.
function gate_dedup(clusters, keys) {
  const errors = [], soft = []
  const count = new Map(keys.map(k => [k, 0]))
  for (const c of clusters) {
    if (txt_words(c.topic) < 3) soft.push(`topic "${c.topic}" has fewer than 3 words`)
    for (const m of c.members) {
      if (count.has(m)) count.set(m, count.get(m) + 1)
      else errors.push(`unknown key ${m}`)
    }
  }
  for (const [k, n] of count) if (n !== 1) errors.push(`${k} is in ${n} clusters`)
  return { ok: !errors.length, errors, soft }
}

// The dedup judge sees short handles, root:branch:K<n> (n = position in its branch), not option ids: long ids such as
// "A. Inference-time steering of VLA internals" came back shortened to keys that did not exist (run F, both samples).
function dedup_handles(options) {
  const seen = new Map(), toKey = new Map()
  const lines = options.map(o => {
    const rb = String(o.key).split(':').slice(0, 2).join(':')
    const n = (seen.get(rb) || 0) + 1
    seen.set(rb, n)
    const handle = `${rb}:K${n}`
    toKey.set(handle, o.key)
    return { handle, option: o }
  })
  return { lines, toKey }
}

// Maps a judge's clusters back to option keys; an unknown handle passes through, so gate_dedup reports it.
function dedup_unhandle(clusters, toKey) {
  return (Array.isArray(clusters) ? clusters : []).map(c => ({ ...c, members: (c.members || []).map(m => toKey.get(m) || m) }))
}

// After both dedup samples fail: the sample whose partition is valid with the fewest soft faults (short topics plus
// unmerged cross-root Jaccard pairs), ties to the earlier sample; null when no sample partitions the keys.
function dedup_best(samples, options, keys, threshold) {
  let best = null
  for (const r of samples) {
    if (!r || !Array.isArray(r.clusters)) continue
    const g = gate_dedup(r.clusters, keys)
    if (!g.ok) continue
    const faults = g.soft.length + gate_dedup_jaccard(options, r.clusters, threshold).violations.length
    if (!best || faults < best.faults) best = { clusters: r.clusters, faults }
  }
  return best
}

// options: [{key, title}], key = `${root}:${branch}:${id}`. Cross-root pairs whose title Jaccard reaches the threshold
// must share a cluster (flow.md §2.5: at 0.4, 9 pairs flagged on the stored run, 0 false positives).
function gate_dedup_jaccard(options, clusters, threshold) {
  const clusterOf = new Map()
  clusters.forEach((c, i) => c.members.forEach(m => clusterOf.set(m, i)))
  const root = k => String(k).split(':')[0]
  const violations = []
  for (let i = 0; i < options.length; i++) {
    for (let j = i + 1; j < options.length; j++) {
      const a = options[i], b = options[j]
      if (root(a.key) === root(b.key)) continue
      const jaccard = txt_jaccard(a.title, b.title)
      if (jaccard >= threshold && (!clusterOf.has(a.key) || clusterOf.get(a.key) !== clusterOf.get(b.key))) violations.push({ a: a.key, b: b.key, jaccard })
    }
  }
  return { ok: !violations.length, violations }
}

function gate_overlap(pairs, rootIds) {
  const errors = []
  for (const p of pairs) {
    if (!rootIds.includes(p.a) || !rootIds.includes(p.b) || p.a === p.b) errors.push(`bad pair ${p.a}/${p.b}`)
    if (txt_words(p.shared_subject) < 3) errors.push(`${p.a}/${p.b}: shared_subject has fewer than 3 words`)
  }
  return { ok: !errors.length, errors }
}

function gate_price_sheet(sheet) {
  const errors = []
  const inst = sheet.instances
  const price = p => typeof p === 'number' && p > 0 && p < 20
  if (inst.length < 5) errors.push(`${inst.length} instances (want at least 5)`)
  if (!inst.some(i => /H100/i.test(i.gpu) && i.n_gpus === 8)) errors.push('no 8x H100 instance')
  for (const i of inst) if (!price(i.per_gpu_usd_h)) errors.push(`${i.n_gpus}x ${i.gpu}: price ${i.per_gpu_usd_h} outside (0, 20)`)
  if (!price(sheet.filesystem.usd_gib_month)) errors.push(`filesystem price ${sheet.filesystem.usd_gib_month} outside (0, 20)`)
  return { ok: !errors.length, errors }
}

// G-plan. pick: {title, branch} (the picked option's title and the branch);
// args: {budget_usd, require_compute_lever: {physical, interp}}. Halt wins over repair; annotations always returned.
function gate_plan(plan, ev, pick, args) {
  const missing = gate_missing(SCHEMA_PLAN, plan, '')
  if (missing.length) return { action: 'halt', reasons: missing.map(p => `missing ${p}`), annotations: [] }
  const budget = args.budget_usd, stated = plan.cost.total_stated
  const usd = x => `$${Number(x).toFixed(2)}`
  const halt = [], repair = [], annotations = []
  const pr = plan.predictions, lv = plan.compute_axis.levels
  if (txt_normalize_title(pr.if_lever) === txt_normalize_title(pr.if_not)) halt.push('if_lever equals if_not')
  if (!txt_has_digit(pr.decision_rule)) halt.push('decision_rule has no number')
  if (lv.length < 2 || Math.max(...lv) / Math.min(...lv) < 2) halt.push(`compute_axis levels ${JSON.stringify(lv)}: need at least 2 levels spanning 2x`)
  if (!plan.phases.length) halt.push('no phase')
  if (!plan.sources.length) halt.push('no source')
  // a restructured plan reaches the same answer sooner: its axis may buy no new answer, so compute_tested "no" does not halt it
  const restructured = gate_restructured(plan)
  if (plan.compute_tested === 'no' && args.require_compute_lever[pick.branch] && !restructured) halt.push(`compute_tested is no: ${plan.compute_tested_why}`)
  if (ev.planned > budget && stated > budget) halt.push(`planned ${usd(ev.planned)} and stated ${usd(stated)} both over ${usd(budget)}`)
  // only errors that stop evaluation route to repair; a value not found in its quote, or a gate naming a non-number,
  // is annotated and left to the dramaturg (an unconfirmed citation is shown as GUESS on the card)
  for (const e of ev.errors) (['quote', 'gate_ref'].includes(e.kind) ? annotations : repair).push(`${e.kind} at ${e.where}: ${e.msg}`)
  if (ev.planned > budget && stated <= budget) repair.push(`planned ${usd(ev.planned)} over ${usd(budget)} while stated ${usd(stated)} is not`)

  if (txt_normalize_title(plan.option_title) !== txt_normalize_title(pick.title))
    annotations.push(`option_title mismatch: plan "${plan.option_title}", pick "${pick.title}" (re-key if it is another option in this branch)`)
  annotations.push(...ev.flags)
  const sourceIds = new Set(plan.sources.map(s => s.id))
  for (const path of Object.keys(gate_card_caps)) {
    const bad = gate_cited_ids(gate_text(plan, path)).filter(id => !sourceIds.has(id))
    if (bad.length) annotations.push(`${path} cites unknown source ${bad.join(', ')}`)
  }
  for (const path of ['anchor.source_id', 'novelty.closest_source_id']) {
    const id = gate_get(plan, path)
    if (id && !sourceIds.has(id)) annotations.push(`${path} ${id} is not in sources`)
  }
  const nv = plan.novelty
  if (typeof nv.prior_max_level === 'number') {
    const src = plan.sources.find(s => s.id === nv.closest_source_id)
    if (!src || !txt_numbers(src.quote).includes(txt_norm_number(String(nv.prior_max_level))))
      annotations.push(`prior_max_level ${nv.prior_max_level} is not in the quote of ${nv.closest_source_id || 'a named source'}`)
  }
  for (const f of ['closest_prior', 'left_open']) if (!String(nv[f] ?? '').trim()) annotations.push(`novelty.${f} is empty`)
  if (restructured) annotations.push(...gate_restructuring_notes(plan, ev))

  if (halt.length) return { action: 'halt', reasons: halt, annotations }
  if (repair.length) return { action: 'repair', reasons: repair, annotations }
  return { action: 'ok', reasons: [], annotations }
}

// Restructured plans: what the method needs to be tested is annotated, never halted (a missing condition or baseline
// lowers the critic's reshape and baseline instead). "Main spend" is the phase with the most core planned dollars.
function gate_restructuring_notes(plan, ev) {
  const r = plan.restructuring, out = []
  for (const f of ['condition', 'condition_phase', 'baseline_sequential', 'baseline_copies']) if (!String(r[f] ?? '').trim()) out.push(`restructuring.${f} is empty`)
  const order = plan.phases.map(p => p.id), cp = String(r.condition_phase ?? '').trim()
  if (cp && !order.includes(cp)) out.push(`restructuring.condition_phase ${cp} is not a phase id`)
  else if (cp) {
    if (!plan.phases.find(p => p.id === cp).gate) out.push(`restructuring.condition_phase ${cp} has no gate`)
    const spend = {}
    for (const l of (ev && ev.lines) || []) if (!l.optional && !(l.instead_of || []).length && typeof l.usd === 'number') spend[l.phase] = (spend[l.phase] || 0) + l.usd
    const main = order.filter(id => id in spend).sort((a, b) => spend[b] - spend[a] || order.indexOf(a) - order.indexOf(b))[0]
    if (main && order.indexOf(cp) >= order.indexOf(main)) out.push(`restructuring.condition_phase ${cp} is not before the phase with the largest planned spend (${main})`)
  }
  const a = plan.anchor || {}
  if (!String(a.independent_code ?? '').trim() && !String(a.tolerance ?? '').trim()) out.push('anchor has neither an independent code nor a tolerance')
  return out
}

// G-cardfields (render path). Every failing reason routes the field to the one repair call; nothing here blocks.
// Record ids are matched only when they hold a digit or "_": plain-word ids ("A", "pilot") would flag ordinary words.
function gate_cardfields(plan, caps) {
  const sourceIds = new Set(plan.sources.map(s => s.id))
  const ids = [...plan.arms, ...plan.phases, ...plan.numbers, ...plan.cost.rates, ...plan.cost.lines, ...(plan.cost.scenarios || []), ...plan.full_scale]
    .map(x => String(x.id)).filter(id => /[\d_]/.test(id))
  const failing = [], annotations = []
  const fail = (field, reason) => {
    const f = failing.find(x => x.field === field)
    if (f) f.reasons.push(reason)
    else failing.push({ field, reasons: [reason] })
  }
  for (const [field, cap] of Object.entries(caps)) {
    if (gate_restructuring_field(field) && !gate_restructured(plan)) continue
    const t = gate_text(plan, field)
    const n = txt_words(t)
    if (n > cap) fail(field, `${n} words (cap ${cap})`)
    const rid = txt_contains_record_id(t, ids)
    if (rid.length) fail(field, `record ids: ${rid.join(', ')}`)
    const codes = [...new Set(txt_coined_codes(t))].filter(c => !rid.includes(c))
    if (codes.length) fail(field, `coined codes: ${codes.join(', ')}`)
    const cost = gate_cost_text(t)
    if (cost) fail(field, cost)
    const bad = gate_cited_ids(t).filter(id => !sourceIds.has(id))
    if (bad.length) fail(field, `unknown sources: ${bad.join(', ')}`)
    for (const s of txt_sentences(t)) if (txt_words(s) > 20) annotations.push(`${field}: a sentence of ${txt_words(s)} words`)
  }
  if (!txt_has_digit(plan.predictions.if_lever) && !txt_has_digit(plan.predictions.if_not))
    fail('predictions.if_lever', 'neither if_lever nor if_not contains a number')
  return { ok: !failing.length, failing, annotations }
}

// Every number in the original field must survive the rewrite (after txt_norm_number).
function gate_number_preservation(orig, rewritten) {
  const kept = new Set(txt_numbers(rewritten))
  return txt_numbers(orig).every(n => kept.has(n))
}

// G-find: each sent ref exactly once; SUPPORTED/PARTIAL carry a page_quote of 15+ characters, other statuses a note of 10+.
function gate_findings(items, sentRefs) {
  const errors = [], degenerate = []
  const sent = new Set(sentRefs)
  for (const ref of sent) {
    const n = items.filter(i => i.ref === ref).length
    if (n !== 1) errors.push(`${ref}: ${n} findings`)
  }
  for (const i of items) {
    if (!sent.has(i.ref)) errors.push(`${i.ref}: not sent`)
    if (!gate_STATUS.includes(i.status)) errors.push(`${i.ref}: status ${i.status}`)
    const quoted = i.status === 'SUPPORTED' || i.status === 'PARTIAL'
    if (String((quoted ? i.page_quote : i.note) ?? '').trim().length < (quoted ? 15 : 10)) degenerate.push(i.ref)
  }
  return { ok: !errors.length && !degenerate.length, errors, degenerate }
}

// Core refs: the core card fields, plus every source a core field cites (its [id]s, the anchor's and the prior's source).
// A restructured plan adds sequential_part: it carries facts such as step counts.
function gate_core_refs(plan) {
  const core = gate_restructured(plan) ? { ...gate_CORE, sequential_part: 'restructuring.sequential_part' } : gate_CORE
  const src = []
  for (const path of Object.values(core)) src.push(...gate_cited_ids(gate_text(plan, path)))
  src.push(gate_get(plan, 'anchor.source_id'), gate_get(plan, 'novelty.closest_source_id'))
  return [...Object.keys(core).map(f => `card:${f}`), ...[...new Set(src.filter(Boolean))].map(id => `src:${id}`)]
}

// Dramaturg items (CONTRACT §2.6), built once for main and replay: every card field with the sources it cites (the anchor
// and the prior also with their own source and value); the sources core fields cite; CITED/PROXY numbers that are
// load-bearing or reach full_scale; and the rates only when no price sheet checked them (opts.rates).
// cardFields: [[ref name, plan path], ...] in card order.
function gate_dramaturg_items(plan, cardFields, opts) {
  const src = Object.fromEntries((plan.sources || []).map(s => [s.id, s]))
  const anchor = plan.anchor || {}, novelty = plan.novelty || {}
  const implicit = { anchor: [anchor.source_id, anchor.published_value], closest_prior: [novelty.closest_source_id, novelty.prior_max_level] }
  const items = []
  for (const [name, path] of cardFields) {
    const text = gate_text(plan, path)
    if (!text || (gate_restructuring_field(path) && !gate_restructured(plan))) continue
    const [sid, value] = implicit[name] || []
    const sources = [...new Set([sid, ...gate_cited_ids(text)])].filter(id => src[id]).map(id => ({ id, url: src[id].url, quote: src[id].quote }))
    items.push({ ref: `card:${name}`, text, sources, ...(value != null ? { value } : {}) })
  }
  for (const ref of gate_core_refs(plan)) {
    const s = ref.startsWith('src:') && src[ref.slice(4)]
    if (s) items.push({ ref, url: s.url, quote: s.quote, supports: s.supports })
  }
  // numbers a full-scale figure reaches, through DERIVED expressions and line expressions (cost's own index)
  const { P } = cost_prepare(plan)
  const lb = new Set(cost_load_bearing(plan).ids)
  const fs = cost_ancestors(P, (plan.full_scale || []).flatMap(f => [...cost_ids(P.ast[`full_scale.${f.id}.usd`]), f.ratio_to]).filter(Boolean))
  for (const x of plan.numbers || []) {
    if ((x.basis === 'CITED' || x.basis === 'PROXY') && (lb.has(x.id) || fs.has(x.id))) {
      items.push({ ref: `num:${x.id}`, name: x.name, value: x.value, unit: x.unit, basis: x.basis, quote: x.quote, page_setting: x.page_setting, differs_in: x.differs_in, url: src[x.source_id] ? src[x.source_id].url : null })
    }
  }
  if (opts && opts.rates) for (const r of (plan.cost && plan.cost.rates) || []) items.push({ ref: `rate:${r.id}`, gpu: r.gpu, gpu_memory_gb: r.gpu_memory_gb, n_gpus: r.n_gpus, per_gpu_usd_h: r.per_gpu_usd_h, url: 'https://lambda.ai/pricing' })
  return items
}

// PASS iff no core item is UNSUPPORTED, CONTRADICTED or UNREACHABLE. num:/rate: items never block on status:
// a CONTRADICTED num: with page_value is re-evaluated at that value and blocks only if the plan is then over budget
// (with no plan, as for planted cards, there is nothing to re-evaluate). Every non-SUPPORTED item that does not block is listed.
function gate_decision(items, coreRefs, plan, ev, given) {
  const core = new Set(coreRefs)
  const blocking = [], listed = []
  for (const it of items) {
    const costItem = it.ref.startsWith('num:') || it.ref.startsWith('rate:')
    const blocks = costItem
      ? plan && it.ref.startsWith('num:') && it.status === 'CONTRADICTED' && typeof it.page_value === 'number' &&
        cost_eval_plan(plan, given, { overrides: { [it.ref.slice(4)]: it.page_value } }).planned > given.budget_usd
      : core.has(it.ref) && ['UNSUPPORTED', 'CONTRADICTED', 'UNREACHABLE'].includes(it.status)
    if (blocks) blocking.push(it)
    else if (it.status !== 'SUPPORTED') listed.push(it)
  }
  return { result: blocking.length ? 'REJECT' : 'PASS', blocking, listed }
}

// G-crit. NA only for lever when compute_axis is absent (never under the current SCHEMA_PLAN, which requires it; the rule is kept),
// and for baseline when the plan is not restructured.
function gate_critique(critique, cardFieldNames, plan, criteria) {
  const errors = []
  for (const c of criteria) {
    const n = critique.scores.filter(s => s.criterion === c).length
    if (n !== 1) errors.push(`${c}: ${n} scores`)
  }
  for (const s of critique.scores) {
    if (!criteria.includes(s.criterion)) { errors.push(`unknown criterion ${s.criterion}`); continue }
    const na = s.value === 'NA'
    const naAllowed = (s.criterion === 'lever' && !plan.compute_axis) || (s.criterion === 'baseline' && !gate_restructured(plan))
    if (na ? !naAllowed : !(Number.isInteger(s.value) && s.value >= 1 && s.value <= 5))
      errors.push(`${s.criterion}: value ${JSON.stringify(s.value)}`)
    const ref = String(s.ref ?? '')
    const resolves = ref.startsWith('card:') ? cardFieldNames.includes(ref.slice(5)) : ref.startsWith('plan:') && gate_get(plan, ref.slice(5)) !== undefined
    if (!na && !resolves) errors.push(`${s.criterion}: ref "${ref}" does not resolve`)
    if (String(s.reason ?? '').trim().length < 15) errors.push(`${s.criterion}: reason under 15 characters`)
  }
  if (critique.decides_by !== 'none' && !plan.phases.some(p => p.id === critique.decides_by)) errors.push(`decides_by ${critique.decides_by} is not a phase id`)
  return { ok: !errors.length, errors }
}

// S0 planted cases (substrate §2.4 cases 6-13, criteria §8.4 case 18, plus Jaccard, number preservation, price sheet).
// Each case is built to make its gate fire; the controls show the same gate passes a valid record.
function gate_selftest() {
  const failures = []
  const check = (name, f) => {
    try { if (!f()) failures.push(name) } catch (e) { failures.push(`${name}: threw ${e && e.message}`) }
  }
  const PLAN = {
    option_title: 'Ensemble size and forecast skill on a synthetic fault',
    question: 'Does forecast skill on a synthetic fault keep rising as the ensemble grows from 32 to 1,024 members?',
    hypothesis: 'Skill levels off below 256 members because model error outweighs sampling error.',
    compute_axis: { quantity: 'ensemble members', unit: 'members', levels: [32, 128, 1024] },
    held_fixed: ['observation network', 'truth runs'],
    predictions: {
      if_lever: 'Skill still rises by more than 0.05 between 256 and 1,024 members.',
      if_not: 'Skill at 256 members is within one standard error of skill at 1,024 members.',
      decision_rule: 'Lever if skill at 1,024 minus skill at 256 exceeds 0.05 and two standard errors.',
      noise_rule: 'Standard error across 5 truth runs.',
      expected: 'if_not',
      expected_why: 'Published ensembles saturate early.',
    },
    compute_tested: 'yes',
    compute_tested_why: 'Ensemble size is bought with GPU time.',
    scored_against: 'Hidden truth runs of the same simulator.',
    arms: [{ id: 'E1', what: 'perfect model' }],
    baseline: { what: 'climatology forecast' },
    anchor: { what: 'Recurrence interval within 1% of the benchmark code [s2].', tolerance: '1%', source_id: 's2' },
    checks: ['reproduce the benchmark first'],
    phases: [{ id: 'P1', what: 'pilot and benchmark' }, { id: 'P2', what: 'ensemble sweep' }],
    numbers: [{ id: 't_sweep', name: 'sweep hours', unit: 'h', basis: 'DESIGN', value: 20 }],
    cost: {
      rates: [{ id: 'h100x8', gpu: 'H100', n_gpus: 8, per_gpu_usd_h: 3.99 }],
      lines: [{ id: 'sweep', phase: 'P2', what: 'ensemble sweep', kind: 'work', rate: 'h100x8', hours: 't_sweep' }],
      total_stated: 638.4,
    },
    full_scale: [],
    outside_budget: [],
    scope_gap: ['real faults'],
    novelty: {
      closest_prior: 'A 150-member ensemble on a lab-scale fault model captured most diversity with 20 members [s1].',
      closest_source_id: 's1', prior_max_level: 150,
      left_open: 'No source reports skill against ensemble size beyond 150 members.',
      decides: 'no', searched: true,
    },
    limits: ['Says nothing about observing stress on a real fault.'],
    test_summary: 'Run ensembles of 32 to 1,024 members on a synthetic fault with known truth, and compare forecast skill across sizes.',
    restructuring: { sequential_part: 'Each ensemble member steps through simulated time in order.', method: 'none' },
    sources: [
      { id: 's1', url: 'https://example.org/a', quote: 'We used a 150-member ensemble.', supports: 'closest prior' },
      { id: 's2', url: 'https://example.org/b', quote: 'The benchmark recurrence interval is 120 years.', supports: 'anchor' },
    ],
    files_read: [],
  }
  const plan = () => JSON.parse(JSON.stringify(PLAN))
  const EV = { ok: true, errors: [], planned: 638.4, flags: [] }
  const PICK = { title: PLAN.option_title, branch: 'physical' }
  const ARGS = { budget_usd: 1000, require_compute_lever: { physical: true, interp: true } }
  const GIVEN = { budget_usd: 1000 }

  check('valid plan: gate_plan ok', () => gate_plan(plan(), EV, PICK, ARGS).action === 'ok')
  check('6 if_lever equal to if_not: halt', () => {
    const p = plan()
    p.predictions.if_not = `  ${p.predictions.if_lever.toUpperCase()}`
    return gate_plan(p, EV, PICK, ARGS).action === 'halt'
  })
  check('7 card field "That costs about $600.": cardfields fails', () => {
    const p = plan()
    p.test_summary = 'That costs about $600.'
    const r = gate_cardfields(p, gate_card_caps)
    return !r.ok && r.failing.some(f => f.field === 'test_summary')
  })
  check('8 unknown source id: cardfields fails', () => {
    const p = plan()
    p.anchor.what = 'Recurrence interval within 1% of the benchmark code [s9].'
    const r = gate_cardfields(p, gate_card_caps)
    return !r.ok && r.failing.some(f => f.field === 'anchor.what')
  })
  check('9 valid card: cardfields passes', () => gate_cardfields(plan(), gate_card_caps).ok)

  const keys = ['R1:physical:W1', 'R2:physical:W1', 'R2:interp:I1']
  check('10 cluster list missing one key: dedup fails', () =>
    gate_dedup([{ topic: 'privacy audits of models', members: keys.slice(0, 2) }], keys).ok === false &&
    gate_dedup([{ topic: 'privacy audits of models', members: keys.slice(0, 2) }, { topic: 'probes on reviewer models', members: keys.slice(2) }], keys).ok)
  check('10c dedup handles: long ids get root:branch:K<n>, clusters map back, unknown handles pass through', () => {
    const o = [{ key: 'R2:interp:A. Inference-time steering' }, { key: 'R2:interp:B. Failure detection' }, { key: 'R3:physical:W1' }]
    const h = dedup_handles(o)
    const back = dedup_unhandle([{ topic: 'steering and failure detection', members: ['R2:interp:K1', 'R2:interp:K2'] }, { topic: 'one other option', members: ['R3:physical:K1', 'R2:interp:A'] }], h.toKey)
    return h.lines.map(l => l.handle).join() === 'R2:interp:K1,R2:interp:K2,R3:physical:K1'
      && back[0].members.join('|') === 'R2:interp:A. Inference-time steering|R2:interp:B. Failure detection'
      && back[1].members.join('|') === 'R3:physical:W1|R2:interp:A'
  })
  check('10b short topic: soft fault, partition still ok; dedup_best keeps the valid sample with fewer faults', () => {
    const short = [{ topic: 'privacy audits', members: keys.slice(0, 2) }, { topic: 'probes on reviewer models', members: keys.slice(2) }]
    const g = gate_dedup(short, keys)
    const opts = keys.map(k => ({ key: k, title: k }))
    const best = dedup_best([{ clusters: [{ topic: 'one cluster missing keys', members: keys.slice(0, 1) }] }, { clusters: short }], opts, keys, 0.4)
    return g.ok && g.soft.length === 1 && best && best.faults === 1 && best.clusters === short
      && dedup_best([{ clusters: [{ topic: 'one cluster missing keys', members: keys.slice(0, 1) }] }], opts, keys, 0.4) === null
  })

  const OPTS = [{ id: 'W1' }, { id: 'W2' }]
  const oc = (value, reason) => [
    { id: 'W1', distance: 'SAME', distance_reason: 'same object of study', scores: [{ criterion: 'stakes', value: 4, reason: 'a lab chooses what to buy on it' }, { criterion: 'open', value, reason }] },
    { id: 'W2', distance: 'ELSEWHERE', distance_reason: 'a different field', scores: [{ criterion: 'stakes', value: 2, reason: 'nobody changes course on it' }, { criterion: 'open', value: 3, reason: 'partly measured up to 64 runs' }] },
  ]
  check('option critic valid: gate_oc ok', () => gate_oc(oc(5, 'no published sweep above 150 members'), OPTS, ['stakes', 'open']).ok)
  check('11 option-critic reason equal to the criterion: degenerate', () => {
    const r = gate_oc(oc(5, 'open'), OPTS, ['stakes', 'open'])
    return !r.ok && r.degenerate.includes('W1')
  })
  check('18 option-critic value "NA": gate_oc fails', () => !gate_oc(oc('NA', 'no published sweep above 150 members'), OPTS, ['stakes', 'open']).ok)

  const core = gate_core_refs(PLAN)
  const item = (ref, status) => ({ ref, status, page_quote: 'a sentence quoted from the page', note: 'what the page says about it' })
  check('12 one CONTRADICTED core item: REJECT', () => {
    const r = gate_decision([item('card:test_summary', 'CONTRADICTED'), item('src:s1', 'SUPPORTED')], core, PLAN, EV, GIVEN)
    return r.result === 'REJECT' && r.blocking.length === 1
  })
  check('13a only PARTIAL: PASS, item listed', () => {
    const r = gate_decision([item('card:test_summary', 'PARTIAL'), item('src:s1', 'SUPPORTED')], core, PLAN, EV, GIVEN)
    return r.result === 'PASS' && r.listed.length === 1 && r.listed[0].ref === 'card:test_summary'
  })
  check('13b CONTRADICTED only in a non-core ref: PASS, item listed', () => {
    const r = gate_decision([item('card:limits', 'CONTRADICTED'), item('card:question', 'SUPPORTED')], core, PLAN, EV, GIVEN)
    return r.result === 'PASS' && r.listed.length === 1 && r.listed[0].ref === 'card:limits'
  })

  const TITLES = [{ key: 'R1:physical:W3', title: 'Training-data attribution and data valuation' }, { key: 'R4:interp:I2', title: 'Probe-based data attribution' }]
  check('Jaccard-0.4 title pair split across clusters: violation', () =>
    !gate_dedup_jaccard(TITLES, [{ topic: 'training data attribution', members: ['R1:physical:W3'] }, { topic: 'probe based attribution', members: ['R4:interp:I2'] }], 0.4).ok &&
    gate_dedup_jaccard(TITLES, [{ topic: 'training data attribution', members: ['R1:physical:W3', 'R4:interp:I2'] }], 0.4).ok)

  check('number preservation catches a dropped number', () =>
    !gate_number_preservation('Skill rises by 0.05 beyond 1,024 members.', 'Skill keeps rising beyond 1024 members.') &&
    gate_number_preservation('Skill rises by 0.05 beyond 1,024 members.', 'Skill rises by 0.05 past 1024 members.'))

  const inst = (gpu, n, p) => ({ gpu, gpu_memory_gb: 80, n_gpus: n, per_gpu_usd_h: p, page_text: `${n}x ${gpu} $${p}` })
  const sheet = extra => ({
    read_at: '2026-10-16',
    instances: [inst('A100', 1, 1.29), inst('A100', 8, 1.79), inst('H100', 1, 2.49), inst('H100', 2, 2.39), inst('B200', 8, 4.99), ...extra],
    filesystem: { usd_gib_month: 0.2, page_text: '$0.20 per GiB per month', example: false },
  })
  check('price sheet without 8x H100: rejected', () => !gate_price_sheet(sheet([])).ok && gate_price_sheet(sheet([inst('H100', 8, 2.99)])).ok)

  // Planted reshape/baseline set (criteria version check): two highs that remove a step-after-step dependency, two lows
  // that only run independent work side by side. Only the gates are tested here; the judges' calibration runs on the model.
  const why = 'a reason long enough to keep'
  const opt = (id, title, compute_open, sequential) => ({ id, title, summary: `${title}.`, root_link: 'none', compute_open, sequential, source_urls: [] })
  const OPT_SET = [
    opt('H1', 'Smoothing a long linear-Gaussian state series', 'none', 'One smoothing pass waits on 1,000,000 steps, each on the last state; few runs are needed and one run keeps under 5% of a GPU busy. The update is associative, so a parallel prefix computation could run all steps at once while the state stays small; nearest attempt https://example.org/prefix'),
    opt('H2', 'Aligning two long sequences by dynamic programming', 'settled: alignment accuracy does not change with compute https://example.org/dp', 'Filling one table waits cell by cell, 100,000,000 cells for two sequences of 10,000; one table leaves most of a GPU idle. Cells on one anti-diagonal do not depend on each other, so each anti-diagonal could run at once when the sequences are long; nearest attempt https://example.org/wavefront'),
    opt('L1', 'Eight independent fine-tuning jobs', 'Jobs: published sweeps stop at 4 https://example.org/sweep; unknown above.', 'none: the answer needs eight independent jobs, one per GPU, which already fill the hardware.'),
    opt('L2', 'Ensemble data assimilation of fault stress', 'Members: one study used 150 https://example.org/a; unknown above.', 'Each ensemble member steps through simulated time in order; the answer needs hundreds of members, so copies side by side already fill the GPUs.'),
  ]
  const OPT_SCORES = OPT_SET.map((o, i) => ({ id: o.id, distance: 'SAME', distance_reason: why,
    scores: [['stakes', 4], ['open', 3], ['reshape', [5, 5, 1, 2][i]]].map(([criterion, value]) => ({ criterion, value, reason: why })) }))
  const STATUS = { H1: 'none', H2: 'settled', L1: 'open', L2: 'open' }
  check('planted reshape set: options pass G-opt and G-oc; totals leave reshape out', () =>
    gate_opt(OPT_SET).ok && !gate_opt([...OPT_SET.slice(0, 3), { ...OPT_SET[3], sequential: ' ' }]).ok &&
    gate_oc(OPT_SCORES, OPT_SET, ['stakes', 'open', 'reshape']).ok &&
    JSON.stringify(gate_totals(OPT_SCORES, ['stakes', 'open', 'reshape'], STATUS)) === JSON.stringify({ H1: 5, H2: 5, L1: 7, L2: 7 }))

  const stub = (o, over) => Object.assign(plan(), { option_title: o.title, novelty: { ...PLAN.novelty, prior_max_level: null } }, over)
  const fast = (o, quantity, levels, sequential_part, method, condition) => stub(o, {
    question: `Can ${o.title.toLowerCase()} reach the sequential answer sooner on one GPU by computing dependent steps at the same time?`,
    hypothesis: 'The dependency can be combined in rounds, so the same answer arrives in far fewer sequential rounds.',
    compute_axis: { quantity, unit: 'steps', levels },
    predictions: { ...PLAN.predictions, if_lever: 'The parallel version beats both baselines beyond 100,000 steps at the same answer.',
      if_not: 'Below 100,000 steps the tuned sequential code stays faster, because rounds cost more than they save.',
      decision_rule: 'Lever if the parallel run is at least 2 times faster than both baselines at the longest chain.' },
    compute_tested: 'no', compute_tested_why: 'The same answer sooner; no new answer is bought.',
    anchor: { what: 'Match the tuned sequential result within a relative error of 1e-6.', tolerance: '1e-6 relative', independent_code: 'the tuned sequential code' },
    phases: [{ id: 'P0', what: 'time one parallel pass on a short chain', gate: { on: 't_sweep', op: '>=', value: 1, else: 'stop' } }, { id: 'P1', what: 'time every arm at three chain lengths' }],
    restructuring: { sequential_part, method, condition, condition_phase: 'P0', baseline_sequential: 'compiled, vectorised sequential code', baseline_copies: '64 independent sequential copies side by side on the same GPU' },
    test_summary: 'Time the parallel version, tuned sequential code and 64 copies side by side at three chain lengths, each to the same answer.',
  })
  const slow = (o, sequential_part) => stub(o, { restructuring: { sequential_part, method: 'none' } })
  const HIGH = [
    fast(OPT_SET[0], 'steps in the chain', [1e4, 1e5, 1e6], 'One smoothing pass updates a small state 1,000,000 times, each step waiting on the one before.',
      'The update is associative, so a parallel prefix computation combines all steps at once in about 20 rounds.', 'State dimension at most 16, checked by timing one pass at 10,000 steps.'),
    fast(OPT_SET[1], 'cells in the table', [1e6, 1e7, 1e8], 'Filling one alignment table visits 100,000,000 cells, each waiting on its left, upper and diagonal neighbours.',
      'Cells on one anti-diagonal depend only on earlier anti-diagonals, so each anti-diagonal is computed at once across threads.', 'Sequences of at least 10,000, checked by timing one table of that size.'),
  ]
  const LOW = [slow(OPT_SET[2], 'Each of eight jobs steps through its own data in order.'), slow(OPT_SET[3], 'Each ensemble member steps through about 20,000 time steps in order.')]
  const EV2 = { ...EV, lines: [{ id: 'pilot', phase: 'P0', kind: 'work', usd: 40, optional: false, instead_of: [] }, { id: 'sweep', phase: 'P2', kind: 'work', usd: 598.4, optional: false, instead_of: [] }] }
  const EVH = { ...EV, lines: [{ id: 'pilot', phase: 'P0', kind: 'work', usd: 40, optional: false, instead_of: [] }, { id: 'main', phase: 'P1', kind: 'work', usd: 598.4, optional: false, instead_of: [] }] }
  const crit = (p, baseline) => ({ scores: [['stakes', 4], ['reshape', 5], ['baseline', baseline]].map(([criterion, value]) => ({ criterion, value, ref: 'card:test_summary', reason: why })),
    decides_by: p.phases[p.phases.length - 1].id, decides_by_reason: why })
  const CRIT3 = ['stakes', 'reshape', 'baseline']
  const CF = [['question', 'question'], ['sequential_part', 'restructuring.sequential_part'], ['method', 'restructuring.method'], ['test_summary', 'test_summary']]
  check('planted highs: restructured; compute_tested no does not halt; no annotation; sequential_part is core and a card field within its cap', () => HIGH.every(p => {
    const g = gate_plan(p, EVH, { title: p.option_title, branch: 'physical' }, ARGS), cf = gate_cardfields(p, gate_card_caps)
    return gate_restructured(p) && g.action === 'ok' && !g.annotations.length && gate_core_refs(p).includes('card:sequential_part') && cf.ok &&
      gate_dramaturg_items(p, CF).some(i => i.ref === 'card:method')
  }))
  check('planted highs: baseline must be scored (NA fails G-crit)', () => HIGH.every(p =>
    gate_critique(crit(p, 4), CF.map(f => f[0]), p, CRIT3).ok && !gate_critique(crit(p, 'NA'), CF.map(f => f[0]), p, CRIT3).ok))
  check('planted lows: not restructured; restructuring fields neither core, nor checked, nor sent; baseline NA accepted', () => LOW.every(p => {
    const long = { ...p, restructuring: { ...p.restructuring, sequential_part: 'word '.repeat(30) } }
    return !gate_restructured(p) && gate_plan(p, EV2, { title: p.option_title, branch: 'physical' }, ARGS).action === 'ok' &&
      !gate_core_refs(p).includes('card:sequential_part') && gate_cardfields(long, gate_card_caps).ok &&
      !gate_dramaturg_items(p, CF).some(i => /^card:(sequential_part|method)$/.test(i.ref)) && gate_critique(crit(p, 'NA'), CF.map(f => f[0]), p, CRIT3).ok
  }))
  check('not restructured: compute_tested no halts where the lever is required; a missing restructuring counts as none', () => {
    const p = { ...LOW[1], compute_tested: 'no' }, q = plan()
    delete q.restructuring
    return gate_plan(p, EV2, { title: p.option_title, branch: 'physical' }, ARGS).action === 'halt' && !gate_restructured(q) && !gate_core_refs(q).includes('card:sequential_part')
  })
  check('restructured: empty condition and baselines, an ungated or late condition phase, an anchor with neither code nor tolerance annotate, never halt', () => {
    const p = JSON.parse(JSON.stringify(HIGH[0]))
    Object.assign(p.restructuring, { condition: '', baseline_sequential: ' ', baseline_copies: undefined })
    const a = gate_plan(p, EVH, { title: p.option_title, branch: 'physical' }, ARGS)
    const late = JSON.parse(JSON.stringify(HIGH[0]))
    late.restructuring.condition_phase = 'P1'
    delete late.phases[1].gate
    const b = gate_plan(late, EVH, { title: late.option_title, branch: 'physical' }, ARGS)
    const none = JSON.parse(JSON.stringify(HIGH[0]))
    none.restructuring.condition_phase = 'P9'
    none.anchor = { absent_reason: 'no reference code' }
    const c = gate_plan(none, EVH, { title: none.option_title, branch: 'physical' }, ARGS).annotations.join('\n')
    return a.action === 'ok' && ['condition', 'baseline_sequential', 'baseline_copies'].every(f => a.annotations.includes(`restructuring.${f} is empty`)) &&
      b.action === 'ok' && b.annotations.includes('restructuring.condition_phase P1 has no gate') && b.annotations.some(x => /P1 is not before the phase with the largest planned spend \(P1\)/.test(x)) &&
      /P9 is not a phase id/.test(c) && /neither an independent code nor a tolerance/.test(c)
  })

  return { ok: !failures.length, failures }
}
