// The idea loop's option gate and ranking (2026-10-21). Kept apart from main.js so it can be tested. First the hard
// eligibility gate: an option enters the ranking only if it bears on the root question (distance not ELSEWHERE), names
// an open compute quantity (compute_open not settled/none), and, when the framer found the question NOT COMPUTE-BOUND,
// states what it narrows the question to and why. Then the main pipeline's own pick rule (pick_run: open and reshape
// floors, reshape route, tie order) chooses among the options that pass. Status readers mirror main.js (CONTRACT §2.2).
const screen_open_status = s => { const t = String(s ?? '').trim().toLowerCase(); return t.startsWith('settled') ? 'settled' : t === 'none' || t === 'none known' ? 'none' : 'open' }
const screen_seq_status = s => (String(s ?? '').trim().toLowerCase().startsWith('none') ? 'none' : 'named')
// a narrowing is stated when the text says more than none / n/a
const screen_narrowed = s => { const t = String(s ?? '').trim().toLowerCase(); return !!t && t !== 'none' && t !== 'n/a' && !/^none\b/.test(t) }

// options: [{id, title, root_link, compute_open, sequential, narrowing?, distance, stakes, open, reshape, internals?}]
// opts: {kind: 'physical'|'interp', verdict: 'COMPUTE-BOUND'|'NOT COMPUTE-BOUND'|null, seed?: number}
// -> {ranked: [{...option, compute_open_status, sequential_status, scores, total, eligible, reasons}], top: id|null, why, log}
function screen_rank(options, opts) {
  const kind = opts.kind === 'interp' ? 'interp' : 'physical'
  const crit = kind === 'interp' ? ['stakes', 'open', 'internals'] : ['stakes', 'open']
  const log = []
  const ranked = options.map(o => {
    const status = screen_open_status(o.compute_open), seq = screen_seq_status(o.sequential)
    const reasons = []
    if (o.distance === 'ELSEWHERE') reasons.push('ELSEWHERE: does not bear on the root question')
    if (status !== 'open') reasons.push(status === 'settled' ? 'compute effect settled: no open compute quantity' : 'no compute effect named')
    if (opts.verdict === 'NOT COMPUTE-BOUND' && !screen_narrowed(o.narrowing)) reasons.push('no narrowing stated for a question the framer found not compute-bound')
    const scores = { stakes: o.stakes ?? 1, open: status === 'open' ? (o.open ?? 1) : 1, reshape: seq === 'none' ? 1 : (o.reshape ?? 1) }
    if (kind === 'interp') scores.internals = o.internals ?? 1
    const total = crit.reduce((t, c) => t + (scores[c] || 0), 0)
    return { ...o, compute_open_status: status, sequential_status: seq, scores, total, eligible: !reasons.length, reasons }
  })
  for (const r of ranked) if (!r.eligible) log.push(`${r.id}: not ranked (${r.reasons.join('; ')})`)
  const el = ranked.filter(r => r.eligible)
  if (!el.length) return { ranked, top: null, why: 'no option passed the gate', log }
  const keyOf = r => `seed:${kind}:${r.id}`
  const pr = pick_run({
    seed: opts.seed ?? 1, args: { pool_k: 0, picks_per_branch: 1, require_compute_lever: { physical: true, interp: true } },
    branches: [{ root: 'seed', branch: kind, options: el.map(r => ({ key: keyOf(r), id: r.id, title: r.title, total: r.total, scores: r.scores, distance: r.distance, compute_open_status: r.compute_open_status, sequential_status: r.sequential_status, compute_open: r.compute_open })) }],
    clusters: [], seed_ideas: [],
  })
  log.push(...(pr.log || []))
  const top = (pr.picks || []).find(p => p.kind === 'top')
  const topOpt = top && el.find(r => keyOf(r) === top.key)
  return { ranked, top: topOpt ? topOpt.id : null, why: top ? (top.why || top.tie_note || 'top pick') : 'pick rule returned no top', log }
}

function screen_selftest() {
  const failures = []
  const base = { root_link: 'bears on it', sequential: 'a chain of 100 steps', distance: 'SAME', stakes: 3, open: 5, reshape: 5 }
  const r = screen_rank([{ ...base, id: 'A', title: 'a', compute_open: 'samples, 10 to 1000' }], { kind: 'physical', verdict: 'COMPUTE-BOUND' })
  if (r.top !== 'A') failures.push('one eligible option is the top')
  const g = screen_rank([{ ...base, id: 'B', title: 'b', compute_open: 'none' }], { kind: 'physical', verdict: 'COMPUTE-BOUND' })
  if (g.top !== null || g.ranked[0].eligible) failures.push('compute_open none is gated')
  return { ok: !failures.length, failures }
}
