// Tests for src/pick.js. Wrapped in a block: every test file runs in one shared context.
// Seed 7 orders used below: R1:physical f < e < a < d < c < b; R2:physical a < b < c (a .05, b .94, c .98);
// R3:physical:a .55; ELSEWHERE j .17 < k .22 < w .40 < h .41 < g .73 < i .73; R1:interp q .25 < r .73 < p .99.
// Options default to sequential_status none with no reshape score: the rule as it was before the reshape route, which
// the older tests below pin; reshape-route tests pass 'named'.
{
  const ARGS = { pool_k: 3, picks_per_branch: 2, require_compute_lever: { physical: true, interp: true } }
  const opt = (key, scores, distance = 'SAME', status = 'open', seq = 'none') => ({ key, id: key.split(':')[2], title: `title of ${key}`, scores, distance,
    total: Object.entries(scores).reduce((a, [c, v]) => a + (c === 'reshape' ? 0 : v), 0), compute_open_status: status, compute_open: `${status}: claim`, sequential_status: seq })
  const run = (opts, { clusters = [], seed_ideas = [], args = {} } = {}) => {
    const branches = []
    for (const x of opts) {
      const [root, branch] = x.key.split(':')
      let b = branches.find(b => b.root === root && b.branch === branch)
      if (!b) branches.push(b = { root, branch, options: [] })
      b.options.push(x)
    }
    return pick_run({ seed: 7, args: { ...ARGS, ...args }, branches, clusters, seed_ideas })
  }
  const kinds = r => r.picks.map(p => `${p.kind} ${p.key}`)
  const inv = (r, key) => r.inventory.find(x => x.key === key)

  test('pick: selftest planted cases pass (P18 i-iv, §8.4 cases 15-16, reshape cases 19-23, determinism)', () => {
    const r = pick_selftest()
    assert.deepEqual(r.failures, [])
    assert.equal(r.ok, true)
  })

  test('pick: hashStr, u and the legacy index equal the Python port that replayed the run', () => {
    const v = fixture('pick/seedlib_values.json')
    for (const [s, h] of v.hashStr) assert.equal(pick_hashStr(s), h, s)
    for (const [seed, key, u] of v.u) assert.equal(pick_u(seed, key), u, key)
    for (const [seed, key, n, i] of v.pickIndex) assert.equal(pick_legacy_index(seed, key, n), i, key)
  })

  test("pick: pick_legacy_index equals the first script's pickIndex", () => {
    // Verbatim from question-tree-wf_670c1d45-049.js:21-34, with SEED made a parameter.
    function hashStr(s) {
      let h = 2166136261
      for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) }
      return h >>> 0
    }
    function mulberry32(a) {
      return function () {
        a |= 0; a = (a + 0x6D2B79F5) | 0
        let t = Math.imul(a ^ (a >>> 15), 1 | a)
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296
      }
    }
    const pickIndex = (SEED, key, n) => Math.floor(mulberry32(hashStr(`${SEED}:${key}`))() * n)
    for (const seed of [0, 1, 2, 42, 1000000])
      for (const key of ['R1:physical:random', 'R5:interp:random', 'order:R2:interp:opt-10-physics-extraction', ''])
        for (const n of [1, 2, 7, 18, 1000]) assert.equal(pick_legacy_index(seed, key, n), pickIndex(seed, key, n))
  })

  test("pick: the old rule on the stored option-critic scores gives the run's 20 picks", () => {
    const fx = fixture('pick/run_seed1.json')
    const branches = fx.branches.map(b => ({ root: b.root, branch: b.branch, options: b.options.map(o => {
      // Old totals: "cannot assess" counts 0, which is how the old option critic summed them.
      const total = Object.values(o.scores).reduce((s, v) => s + (typeof v === 'number' ? v : 0), 0)
      assert.equal(total, o.total, `${b.root}:${b.branch}:${o.id}`)
      return { key: `${b.root}:${b.branch}:${o.id}`, id: o.id, title: o.title, total }
    }) }))
    assert.equal(branches.reduce((n, b) => n + b.options.length, 0), 119)
    const got = pick_run_legacy({ seed: fx.seed, branches }).picks.map(p => ({ root: p.root, branch: p.branch, kind: p.kind, id: p.id }))
    assert.deepEqual(got, JSON.parse(JSON.stringify(fx.picks))) // fixture() parses in the runner's realm
  })

  test('pick: ELSEWHERE and settled/none options are not eligible; the gate follows require_compute_lever', () => {
    const opts = [opt('R1:physical:a', { open: 5, stakes: 5 }, 'ELSEWHERE'), opt('R1:physical:b', { open: 5, stakes: 4 }, 'SAME', 'settled'),
      opt('R1:physical:c', { open: 3, stakes: 3 }, 'ADJACENT'), opt('R1:physical:d', { open: 3, stakes: 1 }, 'SAME', 'none')]
    let r = run(opts)
    assert.deepEqual(kinds(r), ['top R1:physical:c', 'pool R1:physical:a'])
    assert.equal(r.picks[0].rank, 3) // a (10) and b (9) rank above c by total
    // changed contract: the reason names both closed fields
    assert.deepEqual([inv(r, 'R1:physical:b').status, inv(r, 'R1:physical:b').reason], ['not_eligible', 'compute_open settled, sequential none'])
    assert.deepEqual([inv(r, 'R1:physical:d').status, inv(r, 'R1:physical:d').reason], ['not_eligible', 'compute_open none, sequential none'])
    assert.ok(r.log.includes('R1:physical: 1 eligible option(s); picking 1'))
    // Gate off: b and d become eligible; b's open is floored to 1, so it cannot be top while c is open; random is d (u .70 < .82).
    r = run(opts, { args: { require_compute_lever: { physical: false, interp: true } } })
    assert.deepEqual(kinds(r), ['top R1:physical:c', 'random R1:physical:d', 'pool R1:physical:a'])
  })

  test('pick: a branch with fewer than two eligible options picks what it has and logs', () => {
    const r = run([opt('R1:physical:a', { open: 3, stakes: 3 }), opt('R1:interp:a', { open: 3, internals: 3, stakes: 3 }, 'ELSEWHERE')], { args: { pool_k: 0 } })
    assert.deepEqual(kinds(r), ['top R1:physical:a'])
    assert.ok(r.log.includes('R1:physical: 1 eligible option(s); picking 1'))
    assert.ok(r.log.includes('R1:interp: 0 eligible option(s); picking 0'))
  })

  test('pick: picks_per_branch n gives n - 1 randoms in seeded order', () => {
    const six = ['a', 'b', 'c', 'd', 'e', 'f'].map(id => opt(`R1:physical:${id}`, { open: 3, stakes: id === 'b' ? 5 : 1 }))
    assert.deepEqual(kinds(run(six, { args: { picks_per_branch: 3 } })), ['top R1:physical:b', 'random R1:physical:f', 'random R1:physical:e'])
    assert.deepEqual(kinds(run(six, { args: { picks_per_branch: 1 } })), ['top R1:physical:b'])
  })

  test('pick: picks in one root never collide, even in one cluster', () => {
    const r = run([opt('R1:physical:a', { open: 3, stakes: 3 }), opt('R1:physical:b', { open: 1, stakes: 1 }),
      opt('R1:interp:p', { open: 3, internals: 3, stakes: 3 }), opt('R1:interp:q', { open: 1, internals: 1, stakes: 1 })],
    { clusters: [{ topic: 'same root topic', members: ['R1:physical:a', 'R1:physical:b', 'R1:interp:p'] }] })
    assert.deepEqual(kinds(r), ['top R1:physical:a', 'random R1:physical:b', 'top R1:interp:p', 'random R1:interp:q'])
    assert.ok(!r.log.some(l => l.includes('collided')))
  })

  test('pick: a three-root collision keeps one pick, replaces or drops the losers, and logs each', () => {
    const r = run([opt('R1:physical:a', { open: 3, stakes: 3 }), opt('R1:physical:b', { open: 1, stakes: 1 }),
      opt('R2:physical:a', { open: 4, stakes: 4 }, 'ADJACENT'), opt('R2:physical:b', { open: 3, stakes: 1 }), opt('R2:physical:c', { open: 3, stakes: 2 }),
      opt('R3:physical:a', { open: 3, stakes: 4 })],
    { clusters: [{ topic: 'topic X', members: ['R1:physical:a', 'R2:physical:a', 'R3:physical:a'] }] })
    // R2:a is ADJACENT (and first in seeded order); R3:a is SAME but later than R1:a in seeded order.
    assert.deepEqual(kinds(r), ['top R1:physical:a', 'random R1:physical:b', 'top R2:physical:c', 'random R2:physical:b'])
    assert.deepEqual(r.picks[2].replaced, [{ key: 'R2:physical:a', reason: 'collided with R1:physical:a in topic X' }])
    assert.ok(r.log.includes('R2:physical:top: R2:physical:a collided with R1:physical:a in topic X; replaced by R2:physical:c'))
    assert.ok(r.log.includes('R3:physical:top: R3:physical:a collided with R1:physical:a in topic X; no replacement'))
    assert.deepEqual(['R2:physical:a', 'R3:physical:a'].map(k => inv(r, k).status), ['collided', 'collided'])
    assert.equal(inv(r, 'R3:physical:a').reason, 'collided with R1:physical:a in topic X')
  })

  test('pick: pool is one ELSEWHERE option per unpicked cluster, the first pool_k in seeded order, not by total', () => {
    const E = 'ELSEWHERE'
    const r = run([opt('R1:interp:w', { open: 3, internals: 3, stakes: 3 }, E), opt('R2:physical:h', { open: 3, stakes: 3 }, E),
      opt('R1:physical:g', { open: 3, stakes: 3 }, E), opt('R3:interp:i', { open: 5, internals: 5, stakes: 5 }, E),
      opt('R4:physical:j', { open: 3, stakes: 3 }, E), opt('R4:physical:s', { open: 3, stakes: 3 }), opt('R5:interp:k', { open: 3, internals: 3, stakes: 3 }, E, 'none')],
    { args: { pool_k: 2 }, clusters: [{ topic: 'pool pair topic', members: ['R2:physical:h', 'R1:physical:g'] }, { topic: 'taken topic', members: ['R4:physical:j', 'R4:physical:s'] }] })
    assert.deepEqual(kinds(r), ['top R4:physical:s', 'pool R1:interp:w', 'pool R2:physical:h'])
    assert.equal(inv(r, 'R1:physical:g').reason, 'ELSEWHERE; its cluster is represented by R2:physical:h')
    assert.equal(inv(r, 'R4:physical:j').reason, 'ELSEWHERE; its cluster has a pick')
    assert.equal(inv(r, 'R3:interp:i').reason, 'ELSEWHERE; not drawn for the pool')
    assert.deepEqual([inv(r, 'R5:interp:k').status, inv(r, 'R5:interp:k').reason], ['not_eligible', 'compute_open none, sequential none'])
    assert.equal(inv(r, 'R2:physical:h').status, 'picked_pool')
  })

  test('pick: a named sequential chain keeps a settled/none option eligible (top, random and pool), with its open still floored', () => {
    const N = 'named'
    const r = run([opt('R1:physical:b', { open: 5, stakes: 4 }, 'SAME', 'settled', N), opt('R1:physical:c', { open: 3, stakes: 3 }, 'ADJACENT'),
      opt('R1:physical:d', { open: 3, stakes: 1 }, 'SAME', 'none'), opt('R5:interp:k', { open: 3, internals: 3, stakes: 3 }, 'ELSEWHERE', 'none', N)])
    assert.deepEqual(kinds(r), ['top R1:physical:c', 'random R1:physical:b', 'pool R5:interp:k'])
    assert.equal(inv(r, 'R1:physical:d').status, 'not_eligible')
  })

  test('pick: reshape route ties go by reshape, stakes, then open (interp: internals before open), then seeded order; logged per branch', () => {
    const N = 'named'
    // physical: a and b tie on reshape + stakes (8); a has the higher reshape
    let r = run([opt('R1:physical:a', { open: 1, stakes: 3, reshape: 5 }, 'SAME', 'open', N), opt('R1:physical:b', { open: 5, stakes: 4, reshape: 4 }, 'SAME', 'open', N)])
    assert.equal(r.picks[0].key, 'R1:physical:a')
    assert.equal(r.picks[0].tie_note, 'tie of 2 broken by reshape')
    assert.equal(r.picks[0].rank, 2)   // rank stays by total
    assert.ok(r.log.includes('R1:physical: reshape route'))
    // interp: p, q, r tie on reshape (4) and stakes (4); internals decides before open
    r = run([opt('R1:interp:p', { open: 5, internals: 2, stakes: 4, reshape: 4 }, 'SAME', 'open', N), opt('R1:interp:q', { open: 1, internals: 3, stakes: 4, reshape: 4 }, 'SAME', 'open', N),
      opt('R1:interp:r', { open: 1, internals: 3, stakes: 4, reshape: 4 }, 'SAME', 'open', N)])
    assert.deepEqual([r.picks[0].key, r.picks[0].tie_note], ['R1:interp:q', 'tie of 3 broken by seeded order'])
    assert.equal(inv(r, 'R1:interp:q').reason, 'reshape route: highest reshape + stakes, tie of 3 broken by seeded order')
    // stakes 2 does not route, and an ELSEWHERE reshape 5 never takes a branch's top
    r = run([opt('R1:physical:a', { open: 3, stakes: 2, reshape: 5 }, 'SAME', 'open', N), opt('R1:physical:b', { open: 3, stakes: 3, reshape: 5 }, 'ELSEWHERE', 'open', N),
      opt('R1:physical:c', { open: 3, stakes: 3, reshape: 3 }, 'SAME', 'open', N)])
    assert.deepEqual(kinds(r), ['top R1:physical:c', 'random R1:physical:a', 'pool R1:physical:b'])
    assert.ok(r.log.includes('R1:physical: no reshape option'))
  })

  test('pick: the pool orders reshape >= 4 first, then the rest, each in seeded order, never by total', () => {
    const E = 'ELSEWHERE', N = 'named'
    const r = run([opt('R4:physical:j', { open: 3, stakes: 3 }, E, 'open', N), opt('R5:interp:k', { open: 3, internals: 3, stakes: 3, reshape: 2 }, E, 'open', N),
      opt('R1:interp:w', { open: 3, internals: 3, stakes: 3, reshape: 4 }, E, 'open', N), opt('R1:physical:g', { open: 5, stakes: 5, reshape: 5 }, E, 'open', N),
      opt('R3:interp:i', { open: 5, internals: 5, stakes: 5, reshape: 1 }, E, 'open', N)], { args: { pool_k: 3 } })
    assert.deepEqual(kinds(r), ['pool R1:interp:w', 'pool R1:physical:g', 'pool R4:physical:j'])
    // a reshape score on a sequential-none option is floored and does not jump the queue
    const f = run([opt('R4:physical:j', { open: 3, stakes: 3 }, E, 'open', N), opt('R1:physical:g', { open: 3, stakes: 3, reshape: 5 }, E)], { args: { pool_k: 1 } })
    assert.deepEqual(kinds(f), ['pool R4:physical:j'])
  })

  test('pick: seed ideas all become seed picks', () => {
    const r = run([opt('R1:physical:a', { open: 3, stakes: 3 })], { seed_ideas: [{ key: 'seed:1', title: 'one', text: 'idea one' }, { key: 'seed:2', title: 'two', text: 'idea two' }] })
    assert.deepEqual(kinds(r), ['top R1:physical:a', 'seed seed:1', 'seed seed:2'])
    assert.equal(r.inventory.length, 1)
  })

  // integration fix 10: a picked option (here a, the top pick) is left off the frontier
  test('pick: frontier lists open <= 2 (after the settled floor), a named quantity, stakes >= 4, and not picked', () => {
    const r = run([opt('R1:physical:a', { open: 2, stakes: 4 }), opt('R1:physical:b', { open: 5, stakes: 5 }, 'SAME', 'settled'),
      opt('R1:physical:c', { open: 1, stakes: 5 }, 'SAME', 'none'), opt('R1:physical:d', { open: 2, stakes: 3 }), opt('R1:physical:e', { open: 3, stakes: 5 }, 'ELSEWHERE')])
    assert.ok(r.picks.some(p => p.key === 'R1:physical:a'))
    assert.deepEqual(r.frontier, [
      { root: 'R1', key: 'R1:physical:b', title: 'title of R1:physical:b', compute_open: 'settled: claim', distance: 'SAME' }])
  })

  test('pick: output records carry exactly the contract fields; one inventory row per option', () => {
    const r = run([opt('R1:physical:a', { open: 3, stakes: 3 }), opt('R1:physical:b', { open: 2, stakes: 4 }), opt('R2:physical:a', { open: 3, stakes: 3 }, 'ADJACENT'),
      opt('R2:physical:b', { open: 3, stakes: 1 }), opt('R2:physical:c', { open: 3, stakes: 1 }, 'ELSEWHERE')],
    { clusters: [{ topic: 'shared', members: ['R1:physical:a', 'R2:physical:a'] }], seed_ideas: [{ key: 'seed:1', title: 't', text: 'x' }] })
    for (const p of r.picks) assert.deepEqual(Object.keys(p).sort(), ['branch', 'key', 'kind', 'rank', 'replaced', 'root', 'tie_note', 'total'])
    for (const f of r.frontier) assert.deepEqual(Object.keys(f).sort(), ['compute_open', 'distance', 'key', 'root', 'title'])
    for (const x of r.inventory) {
      assert.deepEqual(Object.keys(x).sort(), ['branch', 'cluster_topic', 'distance', 'key', 'reason', 'root', 'status', 'title', 'total'])
      assert.ok(['picked_top', 'picked_random', 'picked_pool', 'collided', 'not_eligible', 'not_picked'].includes(x.status), x.status)
      assert.ok(x.reason)
    }
    assert.deepEqual(r.inventory.map(x => x.key), ['R1:physical:a', 'R1:physical:b', 'R2:physical:a', 'R2:physical:b', 'R2:physical:c'])
    assert.deepEqual(r.inventory.map(x => x.status), ['picked_top', 'picked_random', 'collided', 'picked_random', 'picked_pool'])
    assert.equal(inv(r, 'R2:physical:a').cluster_topic, 'shared')
  })

  test('pick: module code has no forbidden constructs', () => {
    const src = [pick_hashStr, pick_mulberry32, pick_u, pick_legacy_index, pick_run_legacy, pick_run, pick_selftest].map(String).join('\n')
    for (const re of [/\bimport\s/, /\bexport\s/, /\brequire\(/, /module\.exports/, /Math\.random\(/, /Date\.now\(/, /new Date\(\s*\)/, /console\./])
      assert.doesNotMatch(src, re)
  })
}
