// ---------- render: card, table, inventory, frontier, RESULT.md ----------
// Zero-token output the human reads (options-and-card §4, §6; criteria §8.5; cost §8.4). Nothing is dropped
// silently (substrate S10): every pick, halts included, gets a card and a table row.
//
// ctx, one per pick, is also a table row: the contract's {pick, option, root_question, plan, eval, given,
//   findings: [FINDINGS, FINDINGS|null], decision, critique|null, beyond_prior, annotations, halted: {gate, reasons}|null}
// plus three fields (CONTRACT, changes after build):
//   decision2      gate_decision on findings[1], or null; gives "PASS 2/2" or "PASS 1/2"
//   producer_path  producer.md, linked from the card (main.js and replay.js both set it)
//   n_options      options in the pick's branch, optional; gives the "/11" of "random 8/11"
// option = the OPTIONS item merged with its OPTION_SCORES item: {id, title, distance, distance_reason, scores: [{criterion, value, reason}]}.
// Card text holds no em-dash: the card is quoted inside the critic's prompt.

const render_get = (o, path) => path.split(/[.[\]]+/).filter(Boolean).reduce((x, k) => (x == null ? undefined : x[k]), o)
const render_num = n => (Number.isInteger(n) ? String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ',') : String(n))
const render_usd = x => `$${render_num(Math.round(x))}`
const render_cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0)
const render_cell = s => (s == null ? '' : String(s)).replace(/\|/g, '\\|').replace(/\s*\n\s*/g, ' ')
const render_score = (scores, c) => { const s = (scores || []).find(x => x.criterion === c); return s ? s.value : undefined }
const render_label = pick => pick.key.split(':').map(s => (s === 'physical' ? 'phys' : s)).join('·')
const render_anchor_id = pick => `card-${pick.key.replace(/[^A-Za-z0-9_-]+/g, '-')}`
// as gate_restructured: restructuring.method, trimmed and lowercased, is not "none" (missing or empty counts as none)
const render_restructured = plan => !['', 'none'].includes(String(render_get(plan || {}, 'restructuring.method') ?? '').trim().toLowerCase())

// The tolerance is printed by construction: it was lost or misstated in 3 of 3 PASS write-ups (options-and-card N5).
function render_anchor(a) {
  if (!a) return undefined
  if (!a.what) return a.absent_reason && `None: ${a.absent_reason}`
  return a.tolerance && !a.what.includes(a.tolerance) ? `${a.what} Tolerance: ${a.tolerance}.` : a.what
}

// Card fields by the name a critique ref uses ("card:<name>").
const render_fields = {
  question: p => p.question,
  closest_prior: p => render_get(p, 'novelty.closest_prior'),
  left_open: p => render_get(p, 'novelty.left_open'),
  hypothesis: p => p.hypothesis,
  if_lever: p => render_get(p, 'predictions.if_lever'),
  if_not: p => render_get(p, 'predictions.if_not'),
  test_summary: p => p.test_summary,
  anchor: p => render_anchor(p.anchor),
  limits: p => (p.limits || []).join(' '),
  sequential_part: p => render_get(p, 'restructuring.sequential_part'),
  method: p => render_get(p, 'restructuring.method'),
}

// The text a critique ref points at: a card field, else a plan field path. The script prints it next to the score (criteria §8.3).
function render_ref(plan, ref) {
  const path = String(ref).replace(/^(card|plan):/, '')
  const v = render_fields[path] ? render_fields[path](plan) : render_get(plan, path)
  const s = v === undefined ? 'not found' : typeof v === 'string' ? v : JSON.stringify(v)
  return s.length > 240 ? `${s.slice(0, 240)}…` : s
}

// Script line: the axis span, the closest prior's level against it, and whether prior art was searched (options-and-card §3).
function render_axis(plan, beyond) {
  const ax = plan.compute_axis, nv = plan.novelty || {}, out = []
  if (ax && ax.levels && ax.levels.length) {
    const q = String(ax.quantity)
    out.push(`${q[0].toUpperCase()}${q.slice(1)}: ${render_num(Math.min(...ax.levels))}–${render_num(Math.max(...ax.levels))} ${ax.unit}, ${ax.levels.length} levels.`)
  } else out.push('None.')
  if (nv.prior_max_level == null) out.push('Closest prior: not on this axis.')
  else out.push(`Closest prior: ${render_num(nv.prior_max_level)}${nv.closest_source_id ? ` [${nv.closest_source_id}]` : ''}${beyond === true ? ', beyond it' : beyond === false ? ', not beyond it' : ''}.`)
  if (nv.searched === false) out.push('Prior art checked without web search.')
  return out.join(' ')
}

function render_verdict(r) {
  if (r.halted) return `halted: ${r.halted.gate}`
  if (!r.decision) return 'not judged'
  if (r.decision.result !== 'PASS') return `REJECT (${r.decision.blocking.length} blocking)`
  return `PASS ${r.decision2 && r.decision2.result === 'PASS' ? 2 : 1}/${r.decision2 ? 2 : 1}`
}

// Payoff as dollars at decides_by (criteria §5): spend through that phase counted as cost counts spend through a
// pilot (base lines only, storage out when the budget does not cover it), the plan total, and the load-bearing GUESS inputs.
function render_payoff(r) {
  const ev = r.eval
  if (!ev || !r.plan) return 'not computed'
  const tail = `plan ${render_usd(ev.planned)} · ${(ev.uncertain || []).filter(u => u.basis === 'GUESS').length} GUESS`
  const at = r.critique && r.critique.decides_by
  if (!at) return `not judged · ${tail}`
  if (at === 'none') return `none · ${tail}`
  const order = (r.plan.phases || []).map(p => p.id), idx = order.indexOf(at)
  const storageOut = r.given && r.given.budget_covers_storage === false
  const usd = ev.lines
    .filter(l => !l.optional && !(l.instead_of || []).length && !(storageOut && l.kind === 'storage'))
    .filter(l => order.indexOf(l.phase) >= 0 && order.indexOf(l.phase) <= idx)
    .reduce((s, l) => s + l.usd, 0)
  return `${render_usd(usd)} at ${at} · ${tail}`
}

function render_card(ctx) {
  const { pick, plan, option: o } = ctx, ev = ctx.eval
  // Outcome labels follow compute_tested: a test that varies no compute quantity states a hypothesis, not a lever,
  // unless the plan is restructured (the restructuring is the lever; the gates halt only an unrestructured "no").
  const lever = !plan || plan.compute_tested !== 'no' || render_restructured(plan)
  const exp = plan && render_get(plan, 'predictions.expected')
  const expects = exp && { if_lever: lever ? 'the lever' : 'the hypothesis holds', if_not: lever ? 'not the lever' : 'the hypothesis fails', unsure: 'unsure' }[exp]
  const head = [
    pick.root, pick.branch, `${pick.kind} pick`,
    o.distance && `distance ${o.distance}`,
    plan && plan.compute_tested && `compute tested: ${plan.compute_tested}`,
    expects && `plan expects: ${expects}`,
    ctx.halted ? `halted: ${ctx.halted.gate}` : ctx.decision && ctx.decision.result,
  ].filter(Boolean).join(' · ')
  const out = [`<a id="${render_anchor_id(pick)}"></a>**${o.id} · ${String(o.title).replace(/[.?!]$/, '')}.** ${head}`]

  if (plan) {
    const f = k => render_fields[k](plan) || 'not given'
    out.push(
      `**Question.** ${f('question')}`,
      `**What is known.** ${[render_fields.closest_prior(plan), render_fields.left_open(plan)].filter(Boolean).join(' ') || 'not given'}`,
      `**Hypothesis.** ${f('hypothesis')}`)
    // A restructured plan says which chain it computes at the same time and how; any other plan gets a script line.
    const rs = render_restructured(plan)
    if (rs) out.push(`**Restructuring.** ${[f('sequential_part'), f('method')].join(' ')}`)
    out.push(
      `**${lever ? 'If compute is the lever' : 'If the hypothesis holds'}.** ${f('if_lever')}`,
      `**If not.** ${f('if_not')}`,
      `**Test.** ${f('test_summary')}`,
      `*Compute axis.* ${render_axis(plan, ctx.beyond_prior)}`)
    if (!rs) out.push('*Restructuring.* none.')
    out.push(
      `**Check first.** ${f('anchor')}`,
      `**Would not show.** ${f('limits')}`,
      `*Cost.* ${ev ? cost_render_short(ev, plan) : 'not computed'}`)
  }

  // A halt replaces the judged part: no dramaturg or critic ran.
  if (ctx.halted) out.push(`**Halted at ${ctx.halted.gate}.** ${ctx.halted.reasons.join('; ')}`)
  else {
    const why = ctx.critique && ctx.critique.decides_by_reason ? ` (critic: ${ctx.critique.decides_by_reason.replace(/\.$/, '')})` : ''
    out.push(`**Judges.** Dramaturg: ${render_verdict(ctx)}. Decides at: ${render_payoff(ctx)}${why}.`)
  }

  // Appendix, not counted in the word budget, in the contract's order.
  if (ev && plan) {
    out.push(`**Cost block.**\n\`\`\`\n${cost_render_block(ev, plan, ctx.given)}\n\`\`\``)
    out.push(`**Derivations.**\n\`\`\`\n${cost_render_derivations(ev, plan)}\n\`\`\``)
  }
  const samples = (ctx.findings || []).map((fs, i) => fs && fs.items.filter(it => it.status !== 'SUPPORTED').map(it =>
    `- sample ${i + 1} · \`${it.ref}\` ${it.status} · page: "${it.page_quote}" · note: ${it.note}${it.page_value != null ? ` · page value ${it.page_value}` : ''}`))
  if (samples.some(Boolean)) out.push(`**Dramaturg, not SUPPORTED.**\n${samples.filter(Boolean).flat().join('\n') || 'none'}`)
  if (ctx.critique) out.push(`**Critic.**\n${ctx.critique.scores.map(s => `- ${s.criterion} ${s.value} · \`${s.ref}\` "${render_ref(plan, s.ref)}" · ${s.reason}`).join('\n')}`)
  if (o.scores) out.push(`**Option critic.**\n${o.scores.map(s => `- ${s.criterion} ${s.value}: ${s.reason}`).concat(o.distance ? [`- distance ${o.distance}: ${o.distance_reason}`] : []).join('\n')}`)
  if (plan) {
    const g = path => render_get(plan, path) ?? 'not given', sr = render_get(plan, 'novelty.searched')
    out.push(`**Producer says (not judged).** expected ${g('predictions.expected')} (${g('predictions.expected_why')}); compute_tested ${g('compute_tested')} (${g('compute_tested_why')}); decides ${g('novelty.decides')}; searched ${sr === true ? 'yes' : sr === false ? 'no' : 'not given'}.`)
  }
  if ((ctx.annotations || []).length) out.push(`**Annotations.**\n${ctx.annotations.map(a => `- ${a}`).join('\n')}`)
  if (ctx.root_question) out.push(`**Root question (${pick.root}).** ${ctx.root_question}`)
  out.push(`**Producer file.** ${ctx.producer_path ? `[producer.md](${ctx.producer_path})` : 'path not given'}`)
  return out.join('\n\n')
}

// Option critic → critic on the shared constructs (criteria §4). Only a drop of 2 or more in open or stakes is labelled:
// an `open` drop means the critic found a prior; a `stakes` drop is "narrowed" when the plan lists a scope gap.
// reshape is never labelled: the option scores the potential, the card the design.
function render_pair(r, c) {
  const a = render_score(r.option && r.option.scores, c), b = render_score(r.critique && r.critique.scores, c)
  const show = v => (typeof v === 'number' ? v : '—')
  const drop = c !== 'reshape' && typeof a === 'number' && typeof b === 'number' && a - b >= 2
  const label = !drop ? '' : c === 'open' ? ' prior found' : (r.plan.scope_gap || []).length ? ' narrowed' : ' unexplained'
  return `${show(a)} → ${show(b)}${label}`
}

function render_picked(r) {
  const p = r.pick, d = r.option && r.option.distance
  const rank = typeof p.rank === 'number' ? ` ${p.rank}${r.n_options ? `/${r.n_options}` : ''}` : ''
  return `${p.kind}${rank}${d ? ` · ${d}` : ''}${p.tie_note ? `, ${p.tie_note}` : ''}`
}

// Index, one row per pick (criteria §8.5). Within each root: PASS, REJECT, halted; then card lever, open, stakes
// (higher first), then key. No totals.
function render_table(rows) {
  const group = r => (r.halted || !r.decision ? 2 : r.decision.result === 'PASS' ? 0 : 1)
  const card = (r, c) => render_score(r.critique && r.critique.scores, c)
  const sortv = (r, c) => (typeof card(r, c) === 'number' ? card(r, c) : -1)
  const shown = (r, c) => (typeof card(r, c) === 'number' ? card(r, c) : '—')
  const root = r => r.pick.root ?? 'seed'   // seed picks have no root; 'seed' sorts after R1..R5
  const sorted = [...rows].sort((x, y) => render_cmp(root(x), root(y)) || group(x) - group(y) ||
    sortv(y, 'lever') - sortv(x, 'lever') || sortv(y, 'open') - sortv(x, 'open') || sortv(y, 'stakes') - sortv(x, 'stakes') ||
    render_cmp(x.pick.key, y.pick.key))
  const lines = [
    '| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |',
    '|---|---|---|---|---|---|---|---|---|---|---|---|',
    ...sorted.map(r => `| ${[
      `[${render_label(r.pick)}](#${render_anchor_id(r.pick)}) ${r.option.title}`,
      render_verdict(r),
      render_picked(r),
      render_get(r.plan, 'predictions.expected') || '—',
      shown(r, 'lever'),
      render_pair(r, 'open'),
      render_pair(r, 'stakes'),
      shown(r, 'verifiable'),
      r.pick.branch === 'interp' ? shown(r, 'internals') : '—',
      render_pair(r, 'reshape'),
      shown(r, 'baseline'),
      render_payoff(r),
    ].map(render_cell).join(' | ')} |`),
  ]
  if (!rows.length) lines.push('| no picks | | | | | | | | | | | |')
  return lines.join('\n')
}

function render_inventory(inventory) {
  return [
    '| Option | Title | Distance | Cluster | Total | Status | Reason |',
    '|---|---|---|---|---|---|---|',
    ...[...inventory].sort((a, b) => render_cmp(a.key, b.key)).map(o =>
      `| ${[o.key, o.title, o.distance, o.cluster_topic, o.total, o.status, o.reason].map(render_cell).join(' | ')} |`),
  ].join('\n')
}

// Per root: options whose compute effect is measured beyond reach but whose stakes are high. Listed, never produced.
function render_frontier(frontier) {
  if (!frontier.length) return 'None.'
  const out = []
  let root = null
  for (const f of [...frontier].sort((a, b) => render_cmp(a.root, b.root) || render_cmp(a.key, b.key))) {
    if (f.root !== root) { root = f.root; out.push(`${out.length ? '\n' : ''}**${root}**`) }
    out.push(`- ${f.title} (${f.distance}): ${f.compute_open}`)
  }
  return out.join('\n')
}

// RESULT.md. header_counts as main.js builds it: {picks, pass, u4 and u3 (on-goal cards), halted: {gate: n}, ...};
// table, frontier and inventory are rendered strings, cards an array of rendered cards, log an array of lines.
function render_result({ header_counts: h, table, frontier, cards, inventory, log }) {
  const halts = Object.keys(h.halted || {}).sort().map(g => `${g} ${h.halted[g]}`).join(', ') || 'none'
  return [
    '# Result',
    `Picks ${h.picks} · PASS ${h.pass} · on-goal cards U4 ${h.u4} · U3 ${h.u3} · halts: ${halts}`,
    '## Table', table,
    '## Frontier (listed, not produced)', frontier,
    '## Cards', cards.join('\n\n---\n\n') || 'None.',
    '## Inventory', inventory,
    '## Log', `\`\`\`\n${log.join('\n')}\n\`\`\``,
  ].join('\n\n')
}

// Planted cases: section order, outcome labels, the Restructuring section or script line, a halted card, the word budget,
// and the table sort. The fixture is the W1 turbulence card of options-and-card §4.2 (REJECT, plan expects the lever).
function render_selftest() {
  const failures = []
  const check = (ok, msg) => { if (!ok) failures.push(msg) }
  const W1 = {
    pick: { key: 'R5:physical:W1', root: 'R5', branch: 'physical', kind: 'top', rank: 1, total: 9, tie_note: null, replaced: [] },
    n_options: 9,
    option: { id: 'W1', title: 'Turbulent fluid flow (direct numerical simulation)', distance: 'ELSEWHERE', distance_reason: 'Fluid turbulence is not the root question\'s system.',
      scores: [{ criterion: 'stakes', value: 4, reason: 'Turbulence-model choice for engineering flows turns on it.' }, { criterion: 'open', value: 1, reason: 'Settled: published runs reach far larger grids.' }] },
    root_question: 'What limits general-purpose robot manipulation? Is it compute-bound?',
    plan: {
      option_title: 'Turbulent fluid flow (direct numerical simulation)',
      question: 'On one rented machine, does turbulence-simulation cost grow as Reynolds number to the sixth? Does resolving every scale remove turbulence-model error?',
      hypothesis: 'Compute removes turbulence-model error by resolving the scales the model approximates. The plan expects this for small-scale statistics only.',
      compute_axis: { quantity: 'grid points per side', unit: 'points', levels: [128, 256, 512, 1024, 2048] },
      held_fixed: ['viscosity', 'forcing', 'time scheme'],
      predictions: { if_lever: 'Unmodelled error on velocity-gradient statistics falls toward zero at full resolution, while a Smagorinsky model keeps an error floor.',
        if_not: 'The plan states no outcome that would count against the claim. Its predictions confirm expected behaviour: the cost exponent nears six above 512³.',
        decision_rule: 'Lever if gradient error at 1024³ is below 5% while the model error stays above 20%.', noise_rule: 'three seeds per grid',
        expected: 'if_lever', expected_why: 'Resolution removes modelling error by construction.' },
      compute_tested: 'yes', compute_tested_why: 'Grid size is the only varied quantity.',
      scored_against: 'the published 1024³ run', arms: [{ id: 'A1', what: 'direct simulation' }, { id: 'A2', what: 'Smagorinsky model' }],
      baseline: { what: 'Smagorinsky model at three constants' },
      anchor: { what: 'The 1024³ run must reproduce the published Taylor Reynolds number 418 within 4%, energy within 3%, spectrum within 10%.', published_value: 418, tolerance: '4%', source_id: 's2' },
      checks: ['energy balance closes within 1%'],
      phases: [{ id: 'B', what: 'benchmark step times' }, { id: 'M', what: 'grid ladder and model runs' }],
      numbers: [{ id: 't_step', name: 'seconds per step at 1024³ on 8 GPUs', unit: 's', basis: 'GUESS', value: 0.8, rests_on: 'textbook operation count', measured_by: 'B' },
        { id: 'steps', name: 'steps in the ladder', unit: 'steps', basis: 'DESIGN', value: 21825 }],
      cost: { rates: [{ id: 'r8', gpu: 'H100 SXM', gpu_memory_gb: 80, n_gpus: 8, per_gpu_usd_h: 3.99 }],
        lines: [{ id: 'bench', phase: 'B', what: 'benchmark', kind: 'work', rate: 'r8', hours: '1.25' }, { id: 'main', phase: 'M', what: 'ladder', kind: 'work', rate: 'r8', hours: 't_step * steps / 3600' }],
        scenarios: [], yields: [], total_stated: 194.71 },
      full_scale: [], outside_budget: [], scope_gap: [],
      novelty: { closest_prior: 'Published simulations reach Taylor Reynolds number 1,200 to 1,300; the run this plan copies reached 418.', closest_source_id: 's4', prior_max_level: 8192,
        left_open: 'The cost law follows from the textbook operation count.', decides: 'partly', searched: false },
      limits: ['The plan cannot move the research frontier: it stays below published Reynolds numbers.', 'Small grids under-use the GPUs, which distorts the measured cost law.'],
      test_summary: 'A spectral solver copies the published 1024³ run\'s viscosity, forcing and time scheme on one to eight GPUs. Grids rise from 128³ to 1024³, and to 2048³ only if affordable. Turbulence-model runs at three constants compete at equal spend.',
      sources: [{ id: 's2', url: 'https://example.org/dns418', quote: 'Taylor Reynolds number 418', supports: 'anchor' }, { id: 's4', url: 'https://example.org/dns8192', quote: '8192³', supports: 'closest prior' }],
      files_read: [],
    },
    eval: { ok: true, errors: [], numbers: { t_step: 0.8, steps: 21825 }, rates: { r8: 31.92 }, rate_corrections: [],
      lines: [{ id: 'bench', phase: 'B', kind: 'work', hours: 1.25, usd: 39.9, optional: false, instead_of: [], time_box: false, need_h: null, margin: null },
        { id: 'main', phase: 'M', kind: 'work', hours: 4.85, usd: 154.81, optional: false, instead_of: [], time_box: false, need_h: null, margin: null }],
      planned: 194.71, planned_with_options: 194.71, alternatives: [], unallocated: 805.29, scenarios: [], yields: [], gates: [],
      uncertain: [{ id: 't_step', basis: 'GUESS', value: 0.8, differs_in: [], measured_by: 'B', cum_spend_through_measured_by: 39.9, k_budget: 5.1, k_box: null, dir: 'higher' }],
      full_scale: [], flags: [], log: [] },
    given: { budget_usd: 1000, budget_covers_storage: true, budget_covers_tax: false,
      price_sheet: { read_at: '2026-10-16', instances: [{ gpu: 'H100 SXM', gpu_memory_gb: 80, n_gpus: 8, per_gpu_usd_h: 3.99, page_text: '8x H100 SXM $3.99/GPU/hr' }], filesystem: { usd_gib_month: 0.2, page_text: '$0.20/GiB/month', example: true } } },
    findings: [{ items: [{ ref: 'card:closest_prior', status: 'CONTRADICTED', page_quote: 'Taylor Reynolds number 1,300', note: 'Largest run is 8,192 points per side.' },
      { ref: 'card:anchor', status: 'SUPPORTED', page_quote: 'Taylor Reynolds number 418', note: '' }] }, null],
    decision: { result: 'REJECT', blocking: [{ ref: 'card:closest_prior', status: 'CONTRADICTED' }], listed: [] },
    decision2: null,
    critique: { scores: [{ criterion: 'stakes', value: 2, ref: 'card:if_not', reason: 'No outcome would change a choice.' },
      { criterion: 'lever', value: 4, ref: 'plan:compute_axis', reason: 'Spans 16x in grid points.' },
      { criterion: 'verifiable', value: 4, ref: 'card:anchor', reason: 'Reproduces a published run.' },
      { criterion: 'open', value: 1, ref: 'card:closest_prior', reason: 'Published runs go far beyond.' }],
      decides_by: 'M', decides_by_reason: 'The ladder gives both outcomes.' },
    beyond_prior: false, annotations: [], halted: null, producer_path: 'run/R5/physical/8ff84fa5/producer.md',
  }
  const has = (card, labels) => labels.map(l => card.indexOf(l)).every((i, k, a) => i >= 0 && (k === 0 || i > a[k - 1]))
  const SECTIONS = ['**Question.**', '**What is known.**', '**Hypothesis.**', '**If compute is the lever.**', '**If not.**', '**Test.**',
    '*Compute axis.*', '**Check first.**', '**Would not show.**', '*Cost.*', '**Judges.**', '**Cost block.**', '**Derivations.**',
    '**Dramaturg, not SUPPORTED.**', '**Critic.**', '**Option critic.**', '**Producer says (not judged).**', '**Producer file.**']
  try {
    const card = render_card(W1)
    check(card.startsWith(`<a id="card-R5-physical-W1"></a>**W1 · `) && has(card, SECTIONS), 'card: sections out of contract order')
    check(card.includes('plan expects: the lever'), 'card: header lacks predictions.expected')
    check(has(card, ['*Compute axis.*', '*Restructuring.* none.', '**Check first.**']) && !card.includes('**Restructuring.**'), 'card: no restructuring, but no "none" script line')
    const rs = render_card({ ...W1, plan: { ...W1.plan, restructuring: { sequential_part: 'Each solver step waits on the last.', method: 'Steps are combined in rounds.' } } })
    check(has(rs, ['**Hypothesis.**', '**Restructuring.** Each solver step waits on the last. Steps are combined in rounds.', '**If compute is the lever.**'])
      && !rs.includes('*Restructuring.* none.'), 'card: Restructuring section missing or misplaced on a restructured plan')
    const no = render_card({ ...W1, plan: { ...W1.plan, compute_tested: 'no' } })
    check(no.includes('**If the hypothesis holds.**') && !no.includes('**If compute is the lever.**'), 'card: labels do not switch on compute_tested no')
    const rsno = render_card({ ...W1, plan: { ...W1.plan, compute_tested: 'no', restructuring: { sequential_part: 'Each solver step waits on the last.', method: 'Steps are combined in rounds.' } } })
    check(rsno.includes('**If compute is the lever.**') && rsno.includes('plan expects: the lever'), 'card: restructured plan with compute_tested no lost the lever labels')
    const body = card.split('\n\n**Judges.**')[0].replace(/<[^>]*>|·/g, ' ')
    check(txt_words(body) <= 320, `card: body ${txt_words(body)} words > 320`)
    const halt = render_card({ ...W1, decision: null, critique: null, findings: [null, null], halted: { gate: 'compute_tested', reasons: ['compute_tested is no'] } })
    check(halt.includes('**Halted at compute_tested.** compute_tested is no') && !halt.includes('**Judges.**') && !halt.includes('**Critic.**'), 'card: halt does not replace the judged part')
    // Table sort: root, then PASS / REJECT / halted, then lever, open, stakes (higher first), then key.
    const row = (key, result, lever, open) => ({ ...W1, pick: { ...W1.pick, key, root: key.split(':')[0], branch: key.split(':')[1] },
      decision: result === 'PASS' || result === 'REJECT' ? { result, blocking: [], listed: [] } : null,
      halted: result === 'halt' ? { gate: 'compute_tested', reasons: [] } : null,
      critique: result === 'halt' ? null : { ...W1.critique, scores: [{ criterion: 'lever', value: lever }, { criterion: 'open', value: open }, { criterion: 'stakes', value: 3 }] } })
    const rows = [row('R2:physical:F', 'REJECT', 5, 5), row('R1:physical:E', 'halt'), row('R1:physical:A', 'PASS', 4, 5), row('R1:physical:D', 'REJECT', 5, 5),
      row('R2:physical:G', 'PASS', 1, 1), row('R1:interp:B', 'PASS', 5, 3), row('R1:interp:A', 'PASS', 4, 5), row('R1:physical:C', 'PASS', 5, 4)]
    const got = render_table(rows).split('\n').filter(l => l.startsWith('| [')).map(l => l.slice(3, l.indexOf(']')))
    const want = ['R1·phys·C', 'R1·interp·B', 'R1·interp·A', 'R1·phys·A', 'R1·phys·D', 'R1·phys·E', 'R2·phys·G', 'R2·phys·F']
    check(got.join() === want.join(), `table: order ${got.join()} != ${want.join()}`)
  } catch (e) {
    failures.push(`render_selftest threw: ${e && e.message}`)
  }
  return { ok: failures.length === 0, failures }
}
