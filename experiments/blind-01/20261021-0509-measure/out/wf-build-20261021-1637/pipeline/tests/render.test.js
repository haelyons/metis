// render.js tests. Fixture: tests/fixtures/render/w11.json, the W11 card of options-and-card §4.2 as a PLAN.
// Wrapped in a function: every test file shares one vm global scope.
(() => {
  const W11 = fixture('render/w11.json')
  // the W11 card's cost line, options-and-card §4.2 (43 words)
  const W11_COST = '$684 planned of $1,000: 6 h on 1× H100 ($25.74), 20 h on 8× H100 at $31.92/h ($638.40), storage up to $20 (GUESS). Two GPU timings are GUESS; the $25.74 phase measures them. Not bought: the same runs without regrouping unfinished members, $6,120.'

  // Local stubs, only where the owning module is absent (CONTRACT §4).
  if (typeof txt_words === 'undefined') globalThis.txt_words = s => String(s).split(/\s+/).filter(w => /[A-Za-z0-9]/.test(w)).length
  if (typeof cost_render_short === 'undefined') globalThis.cost_render_short = () => W11_COST
  if (typeof cost_render_block === 'undefined') globalThis.cost_render_block = (ev, plan, given) => `COST\nPlanned $${ev.planned.toFixed(2)} of $${given.budget_usd} · unallocated $${ev.unallocated.toFixed(2)}`
  if (typeof cost_render_derivations === 'undefined') globalThis.cost_render_derivations = (ev, plan) =>
    plan.numbers.filter(n => n.basis === 'DERIVED').map(n => `${n.id} = ${n.expr} = ${ev.numbers[n.id]}`).join('\n')

  const ctx = (patch = {}) => Object.assign(JSON.parse(JSON.stringify(W11)), patch)
  const withPlan = (patch) => { const c = ctx(); Object.assign(c.plan, patch); return c }
  // words before the judged part, counted as options-and-card §4.1 counts them: markup and · separators are not words
  const bodyWords = card => txt_words(card.split('\n\n**Judges.**')[0].replace(/<[^>]*>|·/g, ' '))
  const inOrder = (s, labels) => labels.every((l, k) => s.indexOf(l) >= 0 && (k === 0 || s.indexOf(l) > s.indexOf(labels[k - 1])))
  const BODY = ['**Question.**', '**What is known.**', '**Hypothesis.**', '**If compute is the lever.**', '**If not.**', '**Test.**',
    '*Compute axis.*', '**Check first.**', '**Would not show.**', '*Cost.*', '**Judges.**']
  const APPENDIX = ['**Cost block.**', '**Derivations.**', '**Dramaturg, not SUPPORTED.**', '**Critic.**', '**Option critic.**',
    '**Producer says (not judged).**', '**Producer file.**']
  const rowsOf = t => t.split('\n').filter(l => l.startsWith('| ['))
  const cellsOf = l => l.slice(2, -2).split(' | ')

  test('render_card: header, sections and appendix in contract order with contract labels', () => {
    const card = render_card(ctx())
    assert.ok(card.startsWith('<a id="card-R3-physical-W11"></a>**W11 · Ensemble data assimilation of fault stress.** R3 · physical · random pick · distance SAME · compute tested: yes · plan expects: not the lever · PASS\n'), card.split('\n')[0])
    assert.ok(inOrder(card, [...BODY, ...APPENDIX]), 'section order')
    for (const l of [...BODY, ...APPENDIX]) assert.equal(card.split(l).length, 2, `${l} appears once`)
    assert.ok(card.includes('**Question.** On a simulated fault with known physics, does earthquake-forecast skill keep rising as the ensemble grows, or level off early?'))
    assert.ok(card.includes('**What is known.** The one perfect-model study used 150 ensemble members and found 20 captured most of the spread. No source reviewed reports'))
    assert.ok(card.includes(`*Cost.* ${cost_render_short(W11.eval, W11.plan)}`))
    assert.ok(card.includes('**Producer file.** [producer.md](run/R3/physical/37e545fc/producer.md)'))
    assert.ok(render_card(ctx({ producer_path: 'x/producer.md' })).includes('**Producer file.** [producer.md](x/producer.md)'), 'main.js and replay.js pass producer_path')
    assert.ok(card.includes('**Root question (R3).** Why can\'t we predict earthquakes'))
    assert.ok(!card.includes('—'), 'no em-dash in card text (it is quoted in prompts)')
  })

  // changed contract: PLAN.speedup and its script line are gone; a restructured plan gets a prose section after Hypothesis
  test('render_card: Restructuring section after Hypothesis on a restructured plan; otherwise the script line "none." after Compute axis', () => {
    const none = render_card(ctx())   // the fixture predates restructuring: read as method none
    assert.ok(inOrder(none, ['*Compute axis.*', '*Restructuring.* none.', '**Check first.**']) && !none.includes('**Restructuring.**'))
    assert.equal(render_card(withPlan({ restructuring: { sequential_part: 'Each member steps in order.', method: ' None ' } })), none)
    const rs = { sequential_part: 'Each member steps through 20,000 time steps in order.', method: 'Steps are combined in rounds of a parallel prefix computation.' }
    const card = render_card(withPlan({ restructuring: rs }))
    assert.ok(inOrder(card, ['**Hypothesis.**', `**Restructuring.** ${rs.sequential_part} ${rs.method}`, '**If compute is the lever.**', '*Compute axis.*', '**Check first.**']))
    assert.ok(!card.includes('*Restructuring.* none.'))
    assert.ok(bodyWords(card) - bodyWords(none) <= 40, 'the section adds at most its two capped fields')
    // a critic ref to a restructuring card field prints its text
    const c = withPlan({ restructuring: rs })
    c.critique.scores.push({ criterion: 'reshape', value: 4, ref: 'card:method', reason: 'removes the chain' })
    assert.ok(render_card(c).includes(`- reshape 4 · \`card:method\` "${rs.method}" · removes the chain`))
  })

  test('render_card: outcome labels and expected follow compute_tested', () => {
    for (const ct of ['yes', 'partly']) {
      const card = render_card(withPlan({ compute_tested: ct }))
      assert.ok(card.includes('**If compute is the lever.** With model error') && card.includes('**If not.** Skill plateaus'), ct)
      assert.ok(card.includes(`compute tested: ${ct} · plan expects: not the lever`), ct)
    }
    const no = render_card(withPlan({ compute_tested: 'no' }))
    assert.ok(no.includes('**If the hypothesis holds.** With model error') && no.includes('**If not.** Skill plateaus'))
    const rs = render_card(withPlan({ compute_tested: 'no', restructuring: { sequential_part: 'Each step waits on the last.', method: 'Steps are combined in rounds.' } }))
    assert.ok(rs.includes('**If compute is the lever.** With model error') && rs.includes('compute tested: no'))
    assert.ok(!no.includes('If compute is the lever'))
    assert.ok(no.includes('compute tested: no · plan expects: the hypothesis fails'))
    const c = ctx(); c.plan.predictions.expected = 'if_lever'
    assert.ok(render_card(c).includes('plan expects: the lever ·'))
  })

  test('render_card: compute axis line shows levels, closest prior level, beyond_prior and the search note', () => {
    assert.ok(render_card(ctx()).includes('*Compute axis.* Ensemble size: 16–16,384 members, 10 levels. Closest prior: 150 [s3], beyond it. Prior art checked without web search.\n'))
    const c = ctx({ beyond_prior: false }); c.plan.novelty.searched = true
    const line = render_card(c).split('\n').find(l => l.startsWith('*Compute axis.*'))
    assert.equal(line, '*Compute axis.* Ensemble size: 16–16,384 members, 10 levels. Closest prior: 150 [s3], not beyond it.')
    const d = ctx({ beyond_prior: null }); d.plan.novelty.prior_max_level = null
    assert.ok(render_card(d).includes('Closest prior: not on this axis. Prior art checked without web search.'))
  })

  test('render_card: W11 body before "Judges" is at most 320 words', () => {
    const card = render_card(ctx())
    const n = bodyWords(card)
    assert.ok(n <= 320, `${n} words`)
    // with the stub's 43-word cost line the body is 318: room for a cost line at its 45-word cap
    if (cost_render_short(W11.eval, W11.plan) === W11_COST) assert.equal(n, 318)
  })

  test('render_card: check-first prints the anchor tolerance by construction', () => {
    assert.ok(render_card(ctx()).includes('**Check first.** The simulator must match the independent QDYN code\'s recurrence interval within 1%. The filter must match an exact Kalman filter on a linear toy.\n'))
    const c = ctx(); c.plan.anchor = { what: 'The simulator must match QDYN\'s recurrence interval.', tolerance: '1%' }
    assert.ok(render_card(c).includes('**Check first.** The simulator must match QDYN\'s recurrence interval. Tolerance: 1%.'))
    const d = ctx(); d.plan.anchor = { absent_reason: 'no published run at this size' }
    assert.ok(render_card(d).includes('**Check first.** None: no published run at this size'))
  })

  test('render_card: Judges line, critique ref text and payoff dollars at decides_by', () => {
    const card = render_card(ctx())
    // P0b $25.74 + P1 $383.04; the optional chaos arm and later phases do not count
    assert.ok(card.includes('**Judges.** Dramaturg: PASS 2/2. Decides at: $409 at P1 · plan $684 · 2 GUESS (critic: Production gives skill'))
    assert.ok(card.includes('- stakes 3 · `card:if_not` "Skill plateaus by 256 members in every Kalman-filter arm. Model error or a deep sensor moves skill more than ensemble size does." · Either outcome'))
    assert.ok(card.includes('- verifiable 5 · `card:anchor` "The simulator must match the independent QDYN'))
    assert.ok(card.includes('- lever 5 · `plan:compute_axis` "{"quantity":"ensemble size","unit":"members"'))
    assert.ok(card.includes('**Option critic.**\n- stakes 3: Refines whether to buy ensemble members or sensors, but only in a synthetic world.\n- open 5: Skill beyond 150 members'))
    assert.ok(card.includes('- distance SAME: Forecasting earthquakes is the root question\'s object of study.'))
    assert.ok(card.includes('**Producer says (not judged).** expected if_not (Both prior studies found 20 to 30 members resolve the significant spread.); compute_tested yes (Only ensemble size varies within each arm.); decides partly; searched no.'))
    assert.ok(card.includes('**Annotations.**\n- time box p2 (8 h, 37% of plan): need not estimated'))
    const none = ctx(); none.critique.decides_by = 'none'
    assert.ok(render_card(none).includes('Decides at: none · plan $684 · 2 GUESS'))
  })

  test('render_card: both dramaturg samples\' non-SUPPORTED items appear verbatim in the appendix; SUPPORTED do not', () => {
    const card = render_card(ctx())
    const sect = card.slice(card.indexOf('**Dramaturg, not SUPPORTED.**'), card.indexOf('**Critic.**'))
    assert.ok(sect.includes('- sample 1 · `num:fs_rate` PARTIAL · page: "for example, $0.20 per GiB per month" · note: The page gives this as a worked example, not a list price.'))
    assert.ok(sect.includes('- sample 2 · `card:left_open` UNSUPPORTED · page: "" · note: No page checked states that no study goes beyond 150 members.'))
    assert.ok(!sect.includes('card:closest_prior') && !sect.includes('src:s3'))
    const one = ctx({ findings: [W11.findings[0], null], decision2: null })
    assert.ok(!render_card(one).includes('sample 2') && render_card(one).includes('Dramaturg: PASS 1/1.'))
  })

  test('render_card: a halted card shows the gate and reasons in place of the judged sections', () => {
    const c = ctx({ halted: { gate: 'G-plan', reasons: ['compute_tested is no where required', 'decision_rule has no digit'] }, findings: [null, null], decision: null, decision2: null, critique: null })
    const card = render_card(c)
    assert.ok(card.split('\n')[0].endsWith('· plan expects: not the lever · halted: G-plan'))
    assert.ok(inOrder(card, ['**Question.**', '*Cost.*', '**Halted at G-plan.** compute_tested is no where required; decision_rule has no digit', '**Cost block.**', '**Option critic.**', '**Producer file.**']))
    for (const l of ['**Judges.**', '**Dramaturg, not SUPPORTED.**', '**Critic.**']) assert.ok(!card.includes(l), l)
    // a schema halt has no plan and no eval: header, the halt, what is known of the option, the link
    const bare = render_card(ctx({ halted: { gate: 'schema', reasons: ['no valid PLAN'] }, plan: null, eval: null, findings: [null, null], decision: null, decision2: null, critique: null }))
    assert.ok(bare.startsWith('<a id="card-R3-physical-W11"></a>**W11 · Ensemble data assimilation of fault stress.** R3 · physical · random pick · distance SAME · halted: schema\n'))
    assert.ok(inOrder(bare, ['**Halted at schema.** no valid PLAN', '**Option critic.**', '**Producer file.**']) && !bare.includes('**Question.**') && !bare.includes('Cost'))
  })

  // table rows: the W11 ctx under other keys, results and scores
  const row = (key, o = {}) => {
    const c = ctx({ pick: { ...W11.pick, key, root: key.split(':')[0], branch: key.split(':')[1], rank: o.rank ?? 2 } })
    if (o.result === 'halt') Object.assign(c, { halted: { gate: o.gate || 'G-plan', reasons: ['x'] }, decision: null, decision2: null, critique: null, findings: [null, null] })
    if (o.result === 'REJECT') Object.assign(c, { decision: { result: 'REJECT', blocking: [{ ref: 'card:anchor' }, { ref: 'card:question' }], listed: [] }, decision2: null })
    if (o.d2) c.decision2 = { result: o.d2, blocking: [], listed: [] }
    if (o.card && c.critique) c.critique.scores = Object.entries(o.card).map(([criterion, value]) => ({ criterion, value, ref: 'card:question', reason: 'r' }))
    if (o.opt) c.option.scores = Object.entries(o.opt).map(([criterion, value]) => ({ criterion, value, reason: 'r' }))
    if (o.scope_gap) c.plan.scope_gap = o.scope_gap
    if (o.n_options === null) delete c.n_options
    return c
  }

  // changed contract: two columns added, Reshape (option → card) and Baseline
  test('render_table: twelve columns, one row per pick, result strings', () => {
    const rows = [row('R3:physical:W11'), row('R3:interp:I1', { d2: 'REJECT' }), row('R3:physical:W2', { result: 'REJECT' }), row('R3:physical:W5', { result: 'halt', gate: 'compute_tested' })]
    const t = render_table(rows)
    const lines = t.split('\n')
    assert.equal(lines[0], '| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |')
    assert.equal(lines[1], '|---|---|---|---|---|---|---|---|---|---|---|---|')
    assert.equal(rowsOf(t).length, 4)
    for (const l of rowsOf(t)) assert.equal(cellsOf(l).length, 12, l)
    const byPick = Object.fromEntries(rowsOf(t).map(l => [cellsOf(l)[0].slice(1, cellsOf(l)[0].indexOf(']')), cellsOf(l)]))
    assert.deepEqual(byPick['R3·phys·W11'], ['[R3·phys·W11](#card-R3-physical-W11) Ensemble data assimilation of fault stress', 'PASS 2/2', 'random 2/11 · SAME',
      'if_not', '5', '5 → 5', '3 → 3', '5', '—', '— → —', '—', '$409 at P1 · plan $684 · 2 GUESS'])
    assert.equal(byPick['R3·interp·I1'][1], 'PASS 1/2')
    assert.equal(byPick['R3·interp·I1'][8], '—', 'interp row without an internals score')
    assert.equal(byPick['R3·phys·W2'][1], 'REJECT (2 blocking)')
    assert.deepEqual(byPick['R3·phys·W5'].slice(1, 12), ['halted: compute_tested', 'random 2/11 · SAME', 'if_not', '—', '5 → —', '3 → —', '—', '—', '— → —', '—', 'not judged · plan $684 · 2 GUESS'])
    const interp = render_table([row('R3:interp:I1', { card: { stakes: 4, lever: 'NA', verifiable: 3, open: 4, internals: 4 } })])
    assert.deepEqual(cellsOf(rowsOf(interp)[0]).slice(4, 9), ['—', '5 → 4', '3 → 4', '3', '4'])
    const pool = row('R3:physical:W9', { n_options: null }); pool.pick.kind = 'pool'; pool.pick.tie_note = 'tie of 3 broken by open'
    assert.equal(cellsOf(rowsOf(render_table([pool]))[0])[2], 'pool 2 · SAME, tie of 3 broken by open')
    assert.ok(render_table([]).endsWith('| no picks | | | | | | | | | | | |'))
  })

  test('render_table: Reshape pairs option and card scores with no drop label; Baseline shows the card score, "—" for NA', () => {
    const cells = o => cellsOf(rowsOf(render_table([row('R3:physical:W11', o)]))[0]).slice(9, 11)
    assert.deepEqual(cells({ opt: { stakes: 3, open: 5, reshape: 5 }, card: { stakes: 3, open: 4, reshape: 1, baseline: 'NA' } }), ['5 → 1', '—'])
    assert.deepEqual(cells({ opt: { stakes: 3, open: 5, reshape: 4 }, card: { stakes: 3, open: 4, reshape: 5, baseline: 3 } }), ['4 → 5', '3'])
  })

  test('render_table: paired columns label drops of 2 or more', () => {
    const cases = [
      [{ opt: { stakes: 3, open: 5 }, card: { stakes: 3, open: 4 } }, '5 → 4', '3 → 3'],
      [{ opt: { stakes: 4, open: 5 }, card: { stakes: 2, open: 1 } }, '5 → 1 prior found', '4 → 2 narrowed'],
      [{ opt: { stakes: 4, open: 4 }, card: { stakes: 2, open: 2 }, scope_gap: [] }, '4 → 2 prior found', '4 → 2 unexplained'],
      [{ opt: { stakes: 2, open: 2 }, card: { stakes: 5, open: 5 } }, '2 → 5', '2 → 5'],
    ]
    for (const [o, open, stakes] of cases) {
      const cells = cellsOf(rowsOf(render_table([row('R3:physical:W11', o)]))[0])
      assert.deepEqual([cells[5], cells[6]], [open, stakes], JSON.stringify(o))
    }
  })

  test('render_table: within root PASS, REJECT, halted; then lever, open, stakes, key', () => {
    const rows = [
      row('R2:physical:Z', { card: { lever: 1, open: 1, stakes: 1 } }),
      row('R1:physical:H', { result: 'halt' }),
      row('R1:physical:R', { result: 'REJECT', card: { lever: 5, open: 5, stakes: 5 } }),
      row('R1:physical:B', { card: { lever: 5, open: 4, stakes: 3 } }),
      row('R1:interp:C', { card: { lever: 5, open: 4, stakes: 4 } }),
      row('R1:physical:A', { card: { lever: 4, open: 5, stakes: 5 } }),
      row('R1:physical:D', { card: { lever: 5, open: 5, stakes: 1 } }),
      row('R1:interp:B', { card: { lever: 5, open: 4, stakes: 3 } }),
      row('R1:physical:N', { card: { lever: 'NA', open: 5, stakes: 5 } }),
    ]
    const order = t => rowsOf(t).map(l => l.slice(3, l.indexOf(']')))
    const want = ['R1·phys·D', 'R1·interp·C', 'R1·interp·B', 'R1·phys·B', 'R1·phys·A', 'R1·phys·N', 'R1·phys·R', 'R1·phys·H', 'R2·phys·Z']
    assert.deepEqual(order(render_table(rows)), want)
    assert.deepEqual(order(render_table([...rows].reverse())), want, 'independent of input order')
  })

  const INV = [
    { key: 'R1:physical:W2', root: 'R1', branch: 'physical', title: 'Checking machine-unlearning claims', distance: 'ADJACENT', cluster_topic: 'machine unlearning audits', total: 8, status: 'picked_top', reason: '' },
    { key: 'R1:interp:I3', root: 'R1', branch: 'interp', title: 'Probe | for unlearned facts', distance: 'SAME', cluster_topic: 'unlearning probes', total: 9, status: 'not_picked', reason: 'not drawn' },
    { key: 'R1:physical:W1', root: 'R1', branch: 'physical', title: 'Turbulence DNS', distance: 'ELSEWHERE', cluster_topic: 'turbulence simulation', total: 6, status: 'not_eligible', reason: 'ELSEWHERE' },
  ]
  const FRONT = [
    { root: 'R3', key: 'R3:physical:W4', title: 'Full-waveform inversion', compute_open: 'settled: resolution limits measured to 1 km https://example.org/a', distance: 'SAME' },
    { root: 'R1', key: 'R1:physical:W7', title: 'Climate km-scale runs', compute_open: 'Grid spacing measured to 1.4 km https://example.org/b', distance: 'ELSEWHERE' },
    { root: 'R1', key: 'R1:physical:W3', title: 'Lattice QCD', compute_open: 'Lattice spacing measured https://example.org/c', distance: 'ELSEWHERE' },
  ]

  test('render_inventory: one row per option, sorted by key, cells escaped', () => {
    const t = render_inventory(INV)
    assert.equal(t, render_inventory([...INV].reverse()))
    const lines = t.split('\n')
    assert.equal(lines[0], '| Option | Title | Distance | Cluster | Total | Status | Reason |')
    assert.deepEqual(lines.slice(2).map(l => l.split(' | ')[0]), ['| R1:interp:I3', '| R1:physical:W1', '| R1:physical:W2'])
    assert.equal(lines[2], '| R1:interp:I3 | Probe \\| for unlearned facts | SAME | unlearning probes | 9 | not_picked | not drawn |')
  })

  test('render_frontier: grouped per root, sorted, listed with compute_open and distance', () => {
    const f = render_frontier(FRONT)
    assert.equal(f, render_frontier([...FRONT].reverse()))
    assert.equal(f, '**R1**\n- Lattice QCD (ELSEWHERE): Lattice spacing measured https://example.org/c\n- Climate km-scale runs (ELSEWHERE): Grid spacing measured to 1.4 km https://example.org/b\n\n**R3**\n- Full-waveform inversion (SAME): settled: resolution limits measured to 1 km https://example.org/a')
    assert.equal(render_frontier([]), 'None.')
  })

  test('render_result: header counts, then table, frontier, cards, inventory, log; deterministic', () => {
    const rows = [row('R3:physical:W11'), row('R3:physical:W5', { result: 'halt', gate: 'G-plan' })]
    const input = {
      header_counts: { picks: 2, pass: 1, reject: 0, not_judged: 0, halted: { 'G-plan': 1, schema: 2 }, u3: 1, u4: 0 },
      table: render_table(rows), frontier: render_frontier(FRONT), cards: rows.map(render_card), inventory: render_inventory(INV), log: ['S5: picked 2', 'R3: note'],
    }
    const md = render_result(input)
    assert.equal(md, render_result(JSON.parse(JSON.stringify(input))))
    assert.ok(md.startsWith('# Result\n\nPicks 2 · PASS 1 · on-goal cards U4 0 · U3 1 · halts: G-plan 1, schema 2\n\n## Table\n\n| Pick |'))
    assert.ok(inOrder(md, ['## Table', '| [R3·phys·W11]', '## Frontier', '**R1**', '## Cards', '**W11 · ', '\n\n---\n\n', '**Halted at G-plan.**', '## Inventory', '| R1:interp:I3', '## Log', '```\nS5: picked 2\nR3: note\n```']))
    assert.ok(render_result({ ...input, header_counts: { picks: 0, pass: 0, u3: 0, u4: 0, halted: {} }, cards: [] }).includes('halts: none'))
  })

  test('render_selftest passes', () => {
    const r = render_selftest()
    assert.deepEqual(r, { ok: true, failures: [] })
  })

  test('src/render.js: no forbidden constructs; every top-level name has the render_ prefix', () => {
    const src = fixture('../../src/render.js')
    for (const re of [/\bimport\s/, /\bexport\s/, /\brequire\(/, /module\.exports/, /Math\.random\(/, /Date\.now\(/, /new Date\(\s*\)/, /console\.log/]) assert.ok(!re.test(src), String(re))
    const names = [...src.matchAll(/^(?:const|let|var|function|class)\s+(\w+)/gm)].map(m => m[1])
    assert.ok(names.length > 10)
    assert.deepEqual(names.filter(n => !n.startsWith('render_')), [])
  })
})()
