// ---------- pick.js: seeded draws and the pick rule (S5) ----------

// Ported unchanged from the first script (keyed, so async completion order cannot change draws).
function pick_hashStr(s) {
  let h = 2166136261
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) }
  return h >>> 0
}
function pick_mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
const pick_u = (seed, key) => pick_mulberry32(pick_hashStr(`${seed}:${key}`))()
// The old pickIndex(key, n), with SEED passed in. Used only to replay the first run.
const pick_legacy_index = (seed, key, n) => Math.floor(pick_u(seed, key) * n)

// The first run's rule, for the replay: top = first listed among the highest totals (strict >);
// random = an index draw over every other option in list order.
function pick_run_legacy(input) {
  const picks = []
  for (const b of input.branches) {
    if (!b.options.length) continue
    let top = b.options[0]
    for (const o of b.options) if (o.total > top.total) top = o
    const rest = b.options.filter(o => o.id !== top.id)
    const row = (o, kind) => ({ key: o.key, root: b.root, branch: b.branch, kind, id: o.id, title: o.title, total: o.total })
    picks.push(row(top, 'top'))
    if (rest.length) picks.push(row(rest[pick_legacy_index(input.seed, `${b.root}:${b.branch}:random`, rest.length)], 'random'))
  }
  return { picks }
}

const pick_DIST = { SAME: 0, ADJACENT: 1, ELSEWHERE: 2 }
// Tie order after total (criteria §8.4); the seeded order u_k breaks what is left.
const pick_TIE = { physical: ['open', 'stakes'], interp: ['open', 'internals', 'stakes'] }
// Reshape route: tie order after reshape + stakes.
const pick_RESHAPE_TIE = { physical: ['reshape', 'stakes', 'open'], interp: ['reshape', 'stakes', 'internals', 'open'] }

// The rule (flow §2.10 step 7, criteria §8.4). Each option's place in the seeded order depends only on its own key,
// so removing or excluding one option never re-rolls the draw for the others.
function pick_run(input) {
  const { seed, args, branches } = input
  const clusters = input.clusters || [], seedIdeas = input.seed_ideas || []
  const log = []
  const topic = {}, cid = {}
  clusters.forEach((c, i) => c.members.forEach(k => { topic[k] = c.topic; cid[k] = i }))
  const clusterOf = k => (k in cid ? cid[k] : k) // an option no cluster names is its own cluster
  const all = branches.flatMap(b => b.options.map(o => ({ ...o, root: b.root, branch: b.branch, u: pick_u(seed, `order:${o.key}`) })))
  const inBranch = (root, branch) => all.filter(o => o.root === root && o.branch === branch)
  const closed = o => o.compute_open_status === 'settled' || o.compute_open_status === 'none'
  // The floors (open: settled/none -> 1; reshape: sequential none -> 1) are applied here too, so the scores agree with
  // main's whatever the caller passed. A missing reshape score counts 0 (a run scored without the criterion).
  const val = (o, c) => (c === 'open' && closed(o) ? 1 : c === 'reshape' ? (o.sequential_status === 'none' ? 1 : o.scores.reshape ?? 0) : o.scores[c])
  // Gated only when both questions are closed: no open compute quantity and no step-after-step chain named.
  const gated = o => !!args.require_compute_lever[o.branch] && closed(o) && o.sequential_status === 'none'
  const eligible = o => o.distance !== 'ELSEWHERE' && !gated(o)
  const byU = (a, b) => a.u - b.u
  const byTotal = (a, b) => b.total - a.total || pick_TIE[a.branch].reduce((d, c) => d || val(b, c) - val(a, c), 0) || a.u - b.u
  const reshapeSum = o => val(o, 'reshape') + val(o, 'stakes')
  const byReshape = (a, b) => reshapeSum(b) - reshapeSum(a) || pick_RESHAPE_TIE[a.branch].reduce((d, c) => d || val(b, c) - val(a, c), 0) || a.u - b.u
  const routes = o => val(o, 'reshape') >= 4

  // Top: the reshape route first (reshape >= 4 and stakes >= 3, highest reshape + stakes); else the open route
  // (highest total among options with open >= 3; if none qualifies, highest total). Each route is logged.
  const chooseTop = (cands, tag) => {
    if (!cands.length) return null
    const rs = cands.filter(o => routes(o) && val(o, 'stakes') >= 3)
    let qual, why, sum, order, ties
    if (rs.length) { qual = rs; why = 'reshape route: highest reshape + stakes'; sum = reshapeSum; order = byReshape; ties = pick_RESHAPE_TIE; log.push(`${tag}: reshape route`) }
    else {
      log.push(`${tag}: no reshape option`)
      qual = cands.filter(o => val(o, 'open') >= 3); why = 'highest total with open >= 3'; sum = o => o.total; order = byTotal; ties = pick_TIE
      if (!qual.length) { qual = cands; why = 'no open option; highest total'; log.push(`${tag}: no open option; top taken by total`) }
    }
    const top = qual.slice().sort(order)[0]
    let tied = qual.filter(o => sum(o) === sum(top)), note = ''
    const n = tied.length
    if (n > 1) {
      note = `tie of ${n} broken by seeded order`
      for (const c of ties[top.branch]) {
        tied = tied.filter(o => val(o, c) === val(top, c))
        if (tied.length === 1) { note = `tie of ${n} broken by ${c}`; break }
      }
    }
    return { opt: top, note, why: note ? `${why}, ${note}` : why }
  }
  const choose = (kind, cands, tag) => (kind === 'top' ? chooseTop(cands, tag)
    : cands.length ? { opt: cands.slice().sort(byU)[0], note: '', why: 'next eligible in seeded order' } : null)

  // Provisional picks per branch: top, then the first picks_per_branch - 1 other eligible options in u-order.
  const slots = []
  for (const b of branches) {
    const tag = `${b.root}:${b.branch}`
    const el = inBranch(b.root, b.branch).filter(eligible)
    if (el.length < args.picks_per_branch) log.push(`${tag}: ${el.length} eligible option(s); picking ${el.length}`)
    const top = chooseTop(el, tag)
    if (!top) continue
    slots.push({ kind: 'top', ...top, replaced: [] })
    for (const o of el.filter(o => o !== top.opt).sort(byU).slice(0, args.picks_per_branch - 1))
      slots.push({ kind: 'random', opt: o, note: '', why: 'next eligible in seeded order', replaced: [] })
  }

  // Collisions: picks in different roots that share a cluster. Keep the better distance, then top before random,
  // then lower u_k; never totals, which come from different criteria sets (flow §2.8 item 4). The loser takes the
  // next eligible option in its branch whose cluster has no pick, so a replacement never collides again.
  const better = (a, b) => pick_DIST[a.opt.distance] - pick_DIST[b.opt.distance]
    || (a.kind === 'top' ? 0 : 1) - (b.kind === 'top' ? 0 : 1) || a.opt.u - b.opt.u
  const lost = {}
  for (;;) {
    const hit = slots.map(s => slots.filter(t => clusterOf(t.opt.key) === clusterOf(s.opt.key)))
      .find(g => new Set(g.map(t => t.opt.root)).size > 1)
    if (!hit) break
    const win = hit.slice().sort(better)[0]
    for (const s of hit) {
      if (s.opt.root === win.opt.root) continue
      const reason = `collided with ${win.opt.key} in ${topic[win.opt.key]}`
      const tag = `${s.opt.root}:${s.opt.branch}:${s.kind}`
      const taken = new Set(slots.map(t => clusterOf(t.opt.key)))
      const next = choose(s.kind, inBranch(s.opt.root, s.opt.branch).filter(o => eligible(o) && !taken.has(clusterOf(o.key))), tag)
      lost[s.opt.key] = reason
      log.push(`${tag}: ${s.opt.key} ${reason}; ${next ? `replaced by ${next.opt.key}` : 'no replacement'}`)
      if (next) { s.replaced.push({ key: s.opt.key, reason }); Object.assign(s, next) }
      else slots.splice(slots.indexOf(s), 1)
    }
  }

  // Pool: ELSEWHERE options whose cluster has no pick, one per cluster (lowest u_k); those with reshape >= 4 first, then
  // the rest, each in u-order; the first pool_k. Drawn, not taken by total: the top ELSEWHERE total was the same famous
  // field in every seed (flow §2.8 item 2). The compute-lever gate applies here too.
  const taken = new Set(slots.map(s => clusterOf(s.opt.key)))
  const rep = new Map()
  for (const o of all.slice().sort(byU))
    if (o.distance === 'ELSEWHERE' && !gated(o) && !taken.has(clusterOf(o.key)) && !rep.has(clusterOf(o.key))) rep.set(clusterOf(o.key), o)
  const pool = [...rep.values()].sort((a, b) => routes(b) - routes(a) || a.u - b.u).slice(0, args.pool_k)
  log.push(`pool: ${rep.size} candidate cluster(s); picked ${pool.length}`)

  const rank = {}
  for (const b of branches) inBranch(b.root, b.branch).sort(byTotal).forEach((o, i) => { rank[o.key] = i + 1 })
  const row = (o, kind, note, replaced) => ({ key: o.key, root: o.root, branch: o.branch, kind, rank: rank[o.key], total: o.total, tie_note: note, replaced })
  const picks = [
    ...slots.map(s => row(s.opt, s.kind, s.note, s.replaced)),
    ...pool.map(o => row(o, 'pool', '', [])),
    ...seedIdeas.map(s => ({ key: s.key, root: null, branch: null, kind: 'seed', rank: null, total: null, tie_note: '', replaced: [] })),
  ]

  const picked = {}
  for (const s of slots) picked[s.opt.key] = { status: `picked_${s.kind}`, reason: s.why + (s.replaced.length ? `; replaced ${s.replaced.map(r => r.key).join(', ')}` : '') }
  for (const o of pool) picked[o.key] = { status: 'picked_pool', reason: 'ELSEWHERE; drawn for the pool' }
  const inventory = all.map(o => {
    const c = clusterOf(o.key)
    const { status, reason } = picked[o.key]
      || (lost[o.key] && { status: 'collided', reason: lost[o.key] })
      || (gated(o) && { status: 'not_eligible', reason: `compute_open ${o.compute_open_status}, sequential none` })
      || (o.distance === 'ELSEWHERE' && { status: 'not_eligible', reason: taken.has(c) ? 'ELSEWHERE; its cluster has a pick'
        : rep.get(c) !== o ? `ELSEWHERE; its cluster is represented by ${rep.get(c).key}` : 'ELSEWHERE; not drawn for the pool' })
      || { status: 'not_picked', reason: 'not drawn' }
    return { key: o.key, root: o.root, branch: o.branch, title: o.title, distance: o.distance, cluster_topic: topic[o.key] || null, total: o.total, status, reason }
  })

  // Frontier: high-stakes options whose open range lies beyond the budget, not picked; listed for the human, not produced here.
  const frontier = all.filter(o => !picked[o.key] && val(o, 'open') <= 2 && o.compute_open_status !== 'none' && o.scores.stakes >= 4)
    .map(o => ({ root: o.root, key: o.key, title: o.title, compute_open: o.compute_open, distance: o.distance }))

  return { picks, frontier, inventory, log }
}

// Planted cases: flow P18 (i)-(iv), criteria §8.4 cases 15-16, reshape cases 19-23, determinism. Seed 7 gives these seeded orders:
// R1:physical f < e < a < d < c < b; R2:physical d < x < c; R2:physical:d < R1:physical:b; R1:physical q < p; R1:interp q < r < p;
// R4:physical k < j; R5:physical n < m.
// In each collision case the winner has the lower total, and the key under test is the only one that favours it.
// Options default to sequential_status none with no reshape score, which is the rule before the reshape route.
function pick_selftest() {
  const failures = []
  const check = (name, ok) => { if (!ok) failures.push(name) }
  const args = { pool_k: 3, picks_per_branch: 2, require_compute_lever: { physical: true, interp: true } }
  const o = (key, scores, distance = 'SAME', status = 'open', seq = 'none') => ({ key, id: key.split(':')[2], title: key, scores, distance,
    total: Object.entries(scores).reduce((a, [c, v]) => a + (c === 'reshape' ? 0 : v), 0), compute_open_status: status, compute_open: status, sequential_status: seq })
  const input = (opts, clusters = []) => {
    const branches = []
    for (const x of opts) {
      const [root, branch] = x.key.split(':')
      let b = branches.find(b => b.root === root && b.branch === branch)
      if (!b) branches.push(b = { root, branch, options: [] })
      b.options.push(x)
    }
    return { seed: 7, args, branches, clusters, seed_ideas: [] }
  }
  const run = (opts, clusters) => pick_run(input(opts, clusters))
  const picks = r => r.picks.map(p => `${p.kind} ${p.key}`).join(', ')
  const status = (r, key) => r.inventory.find(x => x.key === key).status

  // P18 (i), (ii): top b by total; random f, the first other eligible option in seeded order.
  const six = [o('R1:physical:a', { open: 3, stakes: 3 }), o('R1:physical:b', { open: 4, stakes: 5 }), o('R1:physical:c', { open: 3, stakes: 4 }),
    o('R1:physical:d', { open: 2, stakes: 2 }), o('R1:physical:e', { open: 3, stakes: 2 }), o('R1:physical:f', { open: 1, stakes: 3 })]
  const base = 'top R1:physical:b, random R1:physical:f'
  check('six options: top b, random f', picks(run(six)) === base)
  for (const id of ['a', 'c', 'd', 'e'])
    check(`P18(i): removing non-picked ${id} leaves both picks unchanged`, picks(run(six.filter(x => x.id !== id))) === base)
  check('P18(ii): excluding the random pick f yields e, the next in seeded order',
    picks(run(six.map(x => (x.id === 'f' ? { ...x, compute_open_status: 'none' } : x)))) === 'top R1:physical:b, random R1:physical:e')

  // P18 (iii): collisions resolve by distance, then kind, then order; never by total.
  let r = run([o('R1:physical:a', { open: 5, stakes: 5 }, 'ADJACENT'), o('R1:physical:b', { open: 3, stakes: 1 }), o('R1:physical:e', { open: 1, stakes: 1 }),
    o('R2:physical:c', { open: 3, stakes: 3 }), o('R2:physical:d', { open: 3, stakes: 1 }), o('R2:physical:x', { open: 3, stakes: 2 })],
  [{ topic: 'shared topic one', members: ['R1:physical:a', 'R2:physical:c'] }])
  check('P18(iii) distance: SAME c (total 6, later u) beats ADJACENT a (total 10); R1 top takes b',
    picks(r) === 'top R1:physical:b, random R1:physical:e, top R2:physical:c, random R2:physical:d'
    && JSON.stringify(r.picks[0].replaced) === JSON.stringify([{ key: 'R1:physical:a', reason: 'collided with R2:physical:c in shared topic one' }])
    && status(r, 'R1:physical:a') === 'collided')
  r = run([o('R1:physical:a', { open: 1, stakes: 1 }), o('R1:physical:b', { open: 3, stakes: 2 }),
    o('R2:physical:c', { open: 4, stakes: 5 }), o('R2:physical:d', { open: 4, stakes: 4 }), o('R2:physical:x', { open: 3, stakes: 2 })],
  [{ topic: 'shared topic two', members: ['R1:physical:b', 'R2:physical:d'] }])
  check('P18(iii) kind: top b (total 5, later u) beats random d (total 8); R2 random takes x',
    picks(r) === 'top R1:physical:b, random R1:physical:a, top R2:physical:c, random R2:physical:x' && status(r, 'R2:physical:d') === 'collided')
  const twoRoots = [o('R1:physical:a', { open: 3, stakes: 2 }), o('R1:physical:b', { open: 1, stakes: 1 }),
    o('R2:physical:c', { open: 4, stakes: 5 }), o('R2:physical:d', { open: 3, stakes: 1 }), o('R2:physical:x', { open: 3, stakes: 2 })]
  r = run(twoRoots, [{ topic: 'shared topic three', members: ['R1:physical:a', 'R2:physical:c'] }])
  check('P18(iii) order: top a (total 5, lower u) beats top c (total 9); R2 top takes x',
    picks(r) === 'top R1:physical:a, random R1:physical:b, top R2:physical:x, random R2:physical:d' && status(r, 'R2:physical:c') === 'collided')

  // P18 (iv): a cluster picked in one root only (a in R1; x is not picked in R2) excludes nothing.
  r = run(twoRoots, [{ topic: 'shared topic four', members: ['R1:physical:a', 'R2:physical:x'] }])
  check('P18(iv): a cluster picked in one root excludes nothing',
    picks(r) === picks(run(twoRoots)) && picks(r) === 'top R1:physical:a, random R1:physical:b, top R2:physical:c, random R2:physical:d'
    && status(r, 'R2:physical:x') === 'not_picked')

  // §8.4 case 15: ties by open (interp: open, internals, stakes) before the seeded order, which favours q.
  r = run([o('R1:physical:p', { open: 4, stakes: 3 }), o('R1:physical:q', { open: 3, stakes: 4 }),
    o('R1:interp:p', { open: 4, internals: 3, stakes: 2 }), o('R1:interp:q', { open: 4, internals: 2, stakes: 3 }), o('R1:interp:r', { open: 3, internals: 3, stakes: 3 })])
  const tops = r.picks.filter(p => p.kind === 'top')
  check('§8.4(15): a tie broken by open', tops[0].key === 'R1:physical:p' && tops[0].tie_note === 'tie of 2 broken by open')
  check('§8.4(15): interp tie of 3 broken by internals', tops[1].key === 'R1:interp:p' && tops[1].tie_note === 'tie of 3 broken by internals')

  // §8.4 case 16: open <= 2 cannot be top while an open option exists; with none, highest total and a log line.
  r = run([o('R1:physical:a', { open: 2, stakes: 5 }), o('R1:physical:b', { open: 3, stakes: 2 })])
  check('§8.4(16): open <= 2 is not top', r.picks[0].key === 'R1:physical:b' && !r.log.some(l => l.includes('no open option')))
  r = run([o('R1:physical:a', { open: 2, stakes: 5 }), o('R1:physical:b', { open: 1, stakes: 4 })])
  check('§8.4(16): fallback when no option is open', r.picks[0].key === 'R1:physical:a' && r.log.includes('R1:physical: no open option; top taken by total'))

  // 19: a reshape-route top (reshape 4, stakes 3, total 6) beats a higher total (10) on the open route; reshape 5 with stakes 2 does not route.
  const N = 'named'
  r = run([o('R1:physical:a', { open: 3, stakes: 3, reshape: 4 }, 'SAME', 'open', N), o('R1:physical:b', { open: 5, stakes: 5, reshape: 2 }, 'SAME', 'open', N),
    o('R1:physical:c', { open: 3, stakes: 2, reshape: 5 }, 'SAME', 'open', N)])
  check('19: the reshape route beats a higher total on the open route', picks(r) === 'top R1:physical:a, random R1:physical:c'
    && r.log.includes('R1:physical: reshape route') && r.inventory[0].reason === 'reshape route: highest reshape + stakes')
  // 20: compute_open none with a named chain is eligible (its open is still floored, so e is top); both none is not.
  r = run([o('R1:physical:a', { open: 3, stakes: 3 }, 'SAME', 'none', N), o('R1:physical:b', { open: 3, stakes: 5 }, 'SAME', 'none'), o('R1:physical:e', { open: 3, stakes: 2 })])
  check('20: compute_open none with sequential named is eligible; both none is not_eligible', picks(r) === 'top R1:physical:e, random R1:physical:a'
    && status(r, 'R1:physical:b') === 'not_eligible' && r.inventory.find(x => x.key === 'R1:physical:b').reason === 'compute_open none, sequential none')
  // 21: pool_k 1 takes j (reshape 4) over k (lower u, no reshape score); without the score, k.
  const pool1 = opts => pick_run({ ...input(opts), args: { ...args, pool_k: 1 } }).picks.map(p => `${p.kind} ${p.key}`).join(', ')
  check('21: the pool takes reshape >= 4 first, then u-order', pool1([o('R4:physical:k', { open: 3, stakes: 3 }, 'ELSEWHERE', 'open', N),
    o('R4:physical:j', { open: 3, stakes: 3, reshape: 4 }, 'ELSEWHERE', 'open', N)]) === 'pool R4:physical:j'
    && pool1([o('R4:physical:k', { open: 3, stakes: 3 }, 'ELSEWHERE', 'open', N), o('R4:physical:j', { open: 3, stakes: 3 }, 'ELSEWHERE', 'open', N)]) === 'pool R4:physical:k')
  // 22: sequential "none: independent runs" (status none, as main derives it) floors reshape 5 to 1: m leaves the
  // reshape route and n wins on the open route.
  r = run([o('R5:physical:m', { open: 3, stakes: 3, reshape: 5 }), o('R5:physical:n', { open: 4, stakes: 4, reshape: 2 }, 'SAME', 'open', N)])
  check('22: sequential none floors reshape to 1', r.picks[0].key === 'R5:physical:n' && r.log.includes('R5:physical: no reshape option') && !r.log.some(l => l.includes('reshape route')))
  // 23: no option at reshape >= 4 reproduces the open-route picks of P18.
  check('23: a branch with no option at reshape >= 4 keeps the current top pick',
    picks(run(six.map(x => ({ ...x, scores: { ...x.scores, reshape: 3 }, sequential_status: N })))) === base)

  // Same seed, same input: identical output, input untouched. R3 m and n tie on every score (m is first in seeded order).
  const inp = input([...twoRoots, o('R3:physical:n', { open: 3, stakes: 3 }), o('R3:physical:m', { open: 3, stakes: 3 }),
    o('R3:interp:z', { open: 4, internals: 4, stakes: 4 }, 'ELSEWHERE')], [{ topic: 'shared topic three', members: ['R1:physical:a', 'R2:physical:c'] }])
  inp.seed_ideas = [{ key: 'seed:1', title: 'an idea', text: 'an idea from the human' }]
  const before = JSON.stringify(inp), once = pick_run(inp)
  check('a full tie goes to the seeded order', once.picks.some(p => p.key === 'R3:physical:m' && p.kind === 'top' && p.tie_note === 'tie of 2 broken by seeded order'))
  check('determinism: same seed gives identical output, input unchanged', JSON.stringify(once) === JSON.stringify(pick_run(inp)) && JSON.stringify(inp) === before)

  return { ok: failures.length === 0, failures }
}
