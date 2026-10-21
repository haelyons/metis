// screen.js: the idea loop's gate and ranking (2026-10-21)
(() => {
  const opt = (id, over) => ({ id, title: id, root_link: 'bears on the root', compute_open: 'samples, 10 to 10,000', sequential: 'a chain of 1,000 steps', distance: 'SAME', stakes: 3, open: 5, reshape: 1, ...over })

  test('screen: ELSEWHERE, settled and absent compute effects never enter the ranking', () => {
    const r = screen_rank([
      opt('E', { distance: 'ELSEWHERE' }), opt('S', { compute_open: 'settled: published up to 10^6' }), opt('N', { compute_open: 'none' }), opt('K', { compute_open: 'none known' }), opt('G'),
    ], { kind: 'physical', verdict: 'COMPUTE-BOUND' })
    const by = Object.fromEntries(r.ranked.map(x => [x.id, x]))
    assert.equal(by.E.eligible, false); assert.match(by.E.reasons[0], /ELSEWHERE/)
    assert.equal(by.S.eligible, false); assert.equal(by.S.compute_open_status, 'settled'); assert.equal(by.S.scores.open, 1)
    assert.equal(by.N.eligible, false); assert.equal(by.N.compute_open_status, 'none')
    assert.equal(by.K.eligible, false)
    assert.equal(by.G.eligible, true)
    assert.equal(r.top, 'G')
    assert.equal(r.log.filter(l => /not ranked/.test(l)).length, 4)
  })

  test('screen: a question the framer found not compute-bound needs a stated narrowing; a compute-bound one does not', () => {
    const noNarrow = [opt('A'), opt('B', { narrowing: 'none' }), opt('C', { narrowing: 'drops the field trial; the computed observable stands in for the measured yield because both rank cultivars the same way' })]
    const r = screen_rank(noNarrow, { kind: 'physical', verdict: 'NOT COMPUTE-BOUND' })
    const by = Object.fromEntries(r.ranked.map(x => [x.id, x]))
    assert.equal(by.A.eligible, false); assert.match(by.A.reasons[0], /narrowing/)
    assert.equal(by.B.eligible, false)
    assert.equal(by.C.eligible, true)
    assert.equal(r.top, 'C')
    const c = screen_rank(noNarrow, { kind: 'physical', verdict: 'COMPUTE-BOUND' })
    assert.ok(c.ranked.every(x => x.eligible))
    const n = screen_rank(noNarrow, { kind: 'physical', verdict: null })
    assert.ok(n.ranked.every(x => x.eligible), 'no verdict (seed given with compute_open): narrowing not required')
  })

  test('screen: reshape route first, then highest total with open >= 3; reshape floors to 1 without a chain', () => {
    const r = screen_rank([opt('T', { stakes: 5, open: 5, reshape: 1 }), opt('R', { stakes: 3, open: 4, reshape: 5 })], { kind: 'physical', verdict: 'COMPUTE-BOUND' })
    assert.equal(r.top, 'R', 'reshape 5 with stakes 3 wins the reshape route over a higher total')
    const f = screen_rank([opt('T', { stakes: 5, open: 5, reshape: 1 }), opt('R', { stakes: 3, open: 4, reshape: 5, sequential: 'none: the runs are independent' })], { kind: 'physical', verdict: 'COMPUTE-BOUND' })
    assert.equal(f.ranked.find(x => x.id === 'R').scores.reshape, 1, 'sequential none floors reshape')
    assert.equal(f.top, 'T', 'without a reshape option the highest total wins')
  })

  test('screen: no eligible option gives top null and says why; same input gives the same top', () => {
    const r = screen_rank([opt('A', { compute_open: 'none' }), opt('B', { distance: 'ELSEWHERE' })], { kind: 'physical', verdict: 'COMPUTE-BOUND' })
    assert.equal(r.top, null); assert.match(r.why, /no option passed/)
    const a = screen_rank([opt('X'), opt('Y')], { kind: 'physical', verdict: 'COMPUTE-BOUND' })
    const b = screen_rank([opt('X'), opt('Y')], { kind: 'physical', verdict: 'COMPUTE-BOUND' })
    assert.equal(a.top, b.top)
    assert.ok(['X', 'Y'].includes(a.top))
  })

  test('screen: interp kind sums internals and ranks on it', () => {
    const r = screen_rank([opt('A', { internals: 5 }), opt('B', { internals: 1 })], { kind: 'interp', verdict: 'COMPUTE-BOUND' })
    assert.equal(r.ranked.find(x => x.id === 'A').total, 13)
    assert.equal(r.top, 'A')
  })

  test('screen: selftest passes', () => { assert.deepEqual(screen_selftest(), { ok: true, failures: [] }) })
})()
