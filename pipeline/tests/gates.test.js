// gates.js tests. Wrapped to keep names local. gate_decision calls cost_eval_plan; when src/cost.js is absent,
// withCost installs a stub for the duration of one test that evaluates this fixture's arithmetic
// (planned = 8 x 3.99 x (2 + steps / steps_per_h)) and returns the CONTRACT §3 EVAL shape.
;(() => {
  const PLAN = () => fixture('gates/plan.json')
  const EV = (o = {}) => ({ ok: true, errors: [], planned: 868.22, flags: [], ...o })
  const PICK = { title: 'Fine-tuning steps against policy success in simulation', branch: 'physical' }
  const ARGS = { budget_usd: 1000, require_compute_lever: { physical: true, interp: true } }
  const GIVEN = { budget_usd: 1000, price_sheet: fixture('gates/records.json').PRICE_SHEET, budget_covers_storage: true, budget_covers_tax: false }
  // a complete restructuring record for the fixture plan (P1 is its gated pilot, before the P2 sweep)
  const RESTRUCTURED = { sequential_part: 'Each fine-tuning step waits on the weights the step before produced, 32,000 steps.',
    method: 'Steps are grouped into rounds whose updates are combined at once.', condition: 'Updates within a round must nearly commute; the pilot measures the drift.',
    condition_phase: 'P1', baseline_sequential: 'the tuned reference trainer', baseline_copies: 'eight independent fine-tuning runs side by side' }

  const costStub = (plan, given, opts = {}) => {
    const v = id => (opts.overrides && id in opts.overrides ? opts.overrides[id] : plan.numbers.find(n => n.id === id).value)
    const rate = 8 * 3.99
    const planned = rate * (2 + v('steps') / v('steps_per_h'))
    return {
      ok: true, errors: [], numbers: {}, rates: { h100x8: rate }, rate_corrections: [], lines: [], planned, planned_with_options: planned,
      alternatives: [], unallocated: given.budget_usd - planned, scenarios: [], yields: [], gates: [], uncertain: [], full_scale: [], flags: [], log: [],
    }
  }
  const withCost = fn => () => {
    if (typeof cost_eval_plan !== 'undefined') return fn()
    globalThis.cost_eval_plan = costStub
    try { return fn() } finally { delete globalThis.cost_eval_plan }
  }

  test('gate_selftest passes', () => {
    const r = gate_selftest()
    assert.deepEqual(r.failures, [])
    assert.equal(r.ok, true)
  })

  // ---- gate_plan ----
  test('gate_plan: valid fixture is ok with no annotations', () => {
    assert.deepEqual(gate_plan(PLAN(), EV(), PICK, ARGS), { action: 'ok', reasons: [], annotations: [] })
  })

  test('gate_plan: missing required fields halt (nested, arrays, anyOf anchor)', () => {
    const p = PLAN()
    delete p.predictions.noise_rule
    delete p.phases[1].id
    p.anchor = { what: 'no tolerance given' }
    const r = gate_plan(p, EV(), PICK, ARGS)
    assert.equal(r.action, 'halt')
    assert.ok(r.reasons.includes('missing predictions.noise_rule'))
    assert.ok(r.reasons.includes('missing phases.1.id'))
    assert.ok(r.reasons.includes('missing anchor.tolerance'))
    const q = PLAN()
    q.anchor = { absent_reason: 'no published number for this setting' }
    assert.equal(gate_plan(q, EV(), PICK, ARGS).action, 'ok')
  })

  test('gate_plan: if_lever equal to if_not after normalising halts', () => {
    const p = PLAN()
    p.predictions.if_not = `"${p.predictions.if_lever.toUpperCase().replace(/\.$/, '')}"`
    const r = gate_plan(p, EV(), PICK, ARGS)
    assert.equal(r.action, 'halt')
    assert.deepEqual(r.reasons, ['if_lever equals if_not'])
  })

  test('gate_plan: decision_rule without a digit halts', () => {
    const p = PLAN()
    p.predictions.decision_rule = 'Compute is the lever if success keeps rising by a clear margin.'
    assert.deepEqual(gate_plan(p, EV(), PICK, ARGS).reasons, ['decision_rule has no number'])
  })

  // changed contract: the speedup.extends_range exemption is gone with PLAN.speedup; a restructured plan is not exempt either
  test('gate_plan: compute_axis levels (fewer than 2, span under 2x) halt, restructured or not', () => {
    for (const levels of [[32000], [20000, 32000]]) {
      const p = PLAN()
      p.compute_axis.levels = levels
      assert.equal(gate_plan(p, EV(), PICK, ARGS).action, 'halt', JSON.stringify(levels))
      p.restructuring = { ...RESTRUCTURED }
      assert.equal(gate_plan(p, EV(), PICK, ARGS).action, 'halt', `${JSON.stringify(levels)} restructured`)
    }
  })

  test('gate_plan: no phase, no source halt', () => {
    const p = PLAN()
    p.phases = []
    p.sources = []
    const r = gate_plan(p, EV(), PICK, ARGS)
    assert.ok(r.reasons.includes('no phase') && r.reasons.includes('no source'))
  })

  test('gate_plan: compute_tested no on a restructured plan does not halt; method none, None or a missing record does', () => {
    const p = PLAN()
    p.compute_tested = 'no'
    p.restructuring = { ...RESTRUCTURED }
    assert.equal(gate_plan(p, EV(), PICK, ARGS).action, 'ok')
    for (const method of ['none', ' None ', '']) {
      p.restructuring = { ...RESTRUCTURED, method }
      assert.equal(gate_plan(p, EV(), PICK, ARGS).action, 'halt', JSON.stringify(method))
    }
    delete p.restructuring
    assert.deepEqual(gate_plan(p, EV(), PICK, ARGS).reasons, ['missing restructuring'])
  })

  test('gate_plan: restructured plans annotate (never halt) empty fields, a condition phase that is unknown, ungated or not before the main spend, an anchor with neither code nor tolerance', () => {
    const lines = [{ id: 'pilot', phase: 'P1', kind: 'work', usd: 64, optional: false, instead_of: [] }, { id: 'sweep', phase: 'P2', kind: 'work', usd: 804, optional: false, instead_of: [] },
      { id: 'extra', phase: 'P1', kind: 'work', usd: 5000, optional: true, instead_of: [] }]
    const p = PLAN()
    p.restructuring = { ...RESTRUCTURED }
    assert.deepEqual(gate_plan(p, EV({ lines }), PICK, ARGS), { action: 'ok', reasons: [], annotations: [] })   // P1 is gated and before P2
    p.restructuring = { sequential_part: 'x', method: 'steps combined in rounds', condition: ' ', condition_phase: 'P2' }
    p.anchor = { absent_reason: 'none' }
    const r = gate_plan(p, EV({ lines }), PICK, ARGS)
    assert.equal(r.action, 'ok')
    assert.deepEqual(r.annotations, ['restructuring.condition is empty', 'restructuring.baseline_sequential is empty', 'restructuring.baseline_copies is empty',
      'restructuring.condition_phase P2 has no gate', 'restructuring.condition_phase P2 is not before the phase with the largest planned spend (P2)',
      'anchor has neither an independent code nor a tolerance'])
    p.restructuring.condition_phase = 'P7'
    assert.ok(gate_plan(p, EV({ lines }), PICK, ARGS).annotations.includes('restructuring.condition_phase P7 is not a phase id'))
    // not restructured: none of these
    p.restructuring.method = 'none'
    assert.deepEqual(gate_plan(p, EV({ lines }), PICK, ARGS).annotations, [])
  })

  test('gate_plan: compute_tested no halts only where the branch requires the compute lever', () => {
    const p = PLAN()
    p.compute_tested = 'no'
    assert.equal(gate_plan(p, EV(), PICK, ARGS).action, 'halt')
    assert.equal(gate_plan(p, EV(), { ...PICK, branch: 'interp' }, ARGS).action, 'halt')
    assert.equal(gate_plan(p, EV(), { ...PICK, branch: 'interp' }, { ...ARGS, require_compute_lever: { physical: true, interp: false } }).action, 'ok')
    p.compute_tested = 'partly'
    assert.equal(gate_plan(p, EV(), PICK, ARGS).action, 'ok')
  })

  test('gate_plan: budget halt, budget repair, eval errors repair, halt wins', () => {
    const over = PLAN()
    over.cost.total_stated = 1040
    assert.equal(gate_plan(over, EV({ planned: 1040 }), PICK, ARGS).action, 'halt')
    const r = gate_plan(PLAN(), EV({ planned: 1040 }), PICK, ARGS)
    assert.equal(r.action, 'repair')
    assert.match(r.reasons[0], /planned \$1040\.00 over \$1000\.00 while stated \$868\.22 is not/)
    // errors that stop evaluation route to repair; quote and gate_ref errors only annotate (the dramaturg checks those numbers)
    for (const kind of ['parse', 'undefined', 'cycle', 'reserved']) {
      const e = gate_plan(PLAN(), EV({ ok: false, errors: [{ kind, where: 'lines.sweep.hours', msg: 'bad' }] }), PICK, ARGS)
      assert.equal(e.action, 'repair', kind)
    }
    for (const kind of ['quote', 'gate_ref']) {
      const e = gate_plan(PLAN(), EV({ ok: false, errors: [{ kind, where: 'numbers.x.quote', msg: 'bad' }] }), PICK, ARGS)
      assert.equal(e.action, 'ok', kind)
      assert.ok(e.annotations.some(a => a.startsWith(`${kind} at numbers.x.quote`)), kind)
    }
    const both = PLAN()
    both.compute_tested = 'no'
    assert.equal(gate_plan(both, EV({ ok: false, errors: [{ kind: 'parse', where: 'x', msg: 'y' }] }), PICK, ARGS).action, 'halt')
  })

  test('gate_plan: annotations (title mismatch, eval flags, unknown sources, prior level, empty novelty)', () => {
    const same = gate_plan(PLAN(), EV(), { ...PICK, title: ' "fine-tuning steps against policy success, in simulation" ' }, ARGS)
    assert.deepEqual(same.annotations, [])
    const p = PLAN()
    p.hypothesis += ' [s9]'
    p.novelty.closest_source_id = 's8'
    p.novelty.left_open = ' '
    const r = gate_plan(p, EV({ flags: ['k_budget 1.3 below 1.5'] }), { ...PICK, title: 'Another option entirely' }, ARGS)
    assert.equal(r.action, 'ok')
    const a = r.annotations.join('\n')
    assert.match(a, /option_title mismatch: .*re-key/)
    assert.match(a, /k_budget 1\.3 below 1\.5/)
    assert.match(a, /hypothesis cites unknown source s9/)
    assert.match(a, /novelty\.closest_source_id s8 is not in sources/)
    assert.match(a, /prior_max_level 20000 is not in the quote of s8/)
    assert.match(a, /novelty\.left_open is empty/)
    const q = PLAN()
    q.novelty.prior_max_level = 30000
    assert.match(gate_plan(q, EV(), PICK, ARGS).annotations.join('\n'), /prior_max_level 30000 is not in the quote of s3/)
    q.novelty.prior_max_level = null
    assert.deepEqual(gate_plan(q, EV(), PICK, ARGS).annotations, [])
  })

  // ---- gate_cardfields, gate_number_preservation ----
  test('gate_cardfields: valid fixture passes (plain-word arm id "A" is not matched)', () => {
    assert.deepEqual(gate_cardfields(PLAN(), gate_card_caps), { ok: true, failing: [], annotations: [] })
  })

  test('gate_cardfields: each check fails its field', () => {
    const p = PLAN()
    p.question = 'word '.repeat(26).trim() + '?'
    p.hypothesis = 'The full fine-tune E2 levels off near 8,000 steps.'
    p.limits = ['Says nothing about the W11 claim.']
    p.test_summary = 'That costs about $600.'
    p.novelty.left_open = 'Whether 69 times the budget would help.'
    p.anchor.what = 'Reproduce 31% within 3 points using 250 GPU-hours [s9].'
    const r = gate_cardfields(p, gate_card_caps)
    const why = f => (r.failing.find(x => x.field === f) || { reasons: [] }).reasons.join('; ')
    assert.equal(r.ok, false)
    assert.match(why('question'), /26 words \(cap 25\)/)
    assert.equal(why('hypothesis'), 'record ids: E2')
    assert.equal(why('limits'), 'coined codes: W11')
    assert.equal(why('test_summary'), 'dollar figure')
    assert.equal(why('novelty.left_open'), 'multiple of the budget')
    assert.match(why('anchor.what'), /compute-hours/)
    assert.match(why('anchor.what'), /unknown sources: s9/)
  })

  test('gate_cardfields: "$1,000", hardware names and record ids inside words pass; no digit in either outcome fails', () => {
    const p = PLAN()
    p.question = 'Within the $1,000 budget, does success keep rising from 2,000 to 32,000 steps on 8x H100?'
    p.hypothesis = 'Success levels off; pE2 and E2x hold an arm id only inside words.'
    assert.equal(gate_cardfields(p, gate_card_caps).ok, true)
    p.predictions.if_lever = 'Success keeps rising.'
    p.predictions.if_not = 'Success levels off.'
    const r = gate_cardfields(p, gate_card_caps)
    assert.deepEqual(r.failing, [{ field: 'predictions.if_lever', reasons: ['neither if_lever nor if_not contains a number'] }])
  })

  test('gate_cardfields: the restructuring fields are checked only on a restructured plan', () => {
    const p = PLAN()
    p.restructuring.sequential_part = 'word '.repeat(19).trim()
    assert.equal(gate_cardfields(p, gate_card_caps).ok, true)
    p.restructuring.method = 'Steps run in rounds as in E2, ' + 'word '.repeat(18).trim()
    const r = gate_cardfields(p, gate_card_caps)
    assert.deepEqual(r.failing.map(f => [f.field, f.reasons]), [['restructuring.sequential_part', ['19 words (cap 18)']], ['restructuring.method', ['25 words (cap 22)', 'record ids: E2']]])
  })

  test('gate_cardfields: long sentences annotate only', () => {
    const p = PLAN()
    p.test_summary = 'Fine-tune the same policy for 2,000, 8,000 and 32,000 steps with three seeds each and then compare the simulated success at each of the levels. Done.'
    const r = gate_cardfields(p, gate_card_caps)
    assert.equal(r.ok, true)
    assert.deepEqual(r.annotations, ['test_summary: a sentence of 25 words'])
  })

  test('gate_number_preservation', () => {
    assert.equal(gate_number_preservation('Above 1,979 at 20k steps, 5.0 points.', 'Above 1979 at 20,000 steps, 5 points.'), true)
    assert.equal(gate_number_preservation('Arm E2 beats 32,000 steps.', 'The full fine-tune beats 32000 steps.'), true)
    assert.equal(gate_number_preservation('Rises by 0.05 beyond 1,024 members.', 'Keeps rising beyond 1024 members.'), false)
  })

  // ---- findings, core refs, decision ----
  const item = (ref, status, o = {}) => ({ ref, status, page_quote: 'a sentence quoted from the page', note: 'what the page says about it', ...o })

  test('gate_findings: coverage, status, degenerate quotes and notes', () => {
    const sent = ['card:question', 'src:s1', 'num:steps_per_h']
    assert.deepEqual(gate_findings([item('card:question', 'SUPPORTED'), item('src:s1', 'UNREACHABLE'), item('num:steps_per_h', 'PARTIAL')], sent), { ok: true, errors: [], degenerate: [] })
    const r = gate_findings([item('card:question', 'SUPPORTED'), item('card:question', 'PARTIAL'), item('rate:x', 'MAYBE'),
      item('src:s1', 'SUPPORTED', { page_quote: 'short' }), item('num:steps_per_h', 'UNSUPPORTED', { note: 'no' })], sent)
    assert.equal(r.ok, false)
    assert.ok(r.errors.includes('card:question: 2 findings'))
    assert.ok(r.errors.includes('rate:x: not sent') && r.errors.includes('rate:x: status MAYBE'))
    assert.deepEqual(r.degenerate, ['src:s1', 'num:steps_per_h'])
    assert.ok(gate_findings([item('card:question', 'SUPPORTED')], sent).errors.includes('src:s1: 0 findings'))
  })

  test('gate_core_refs: core card fields plus sources cited by them', () => {
    const refs = gate_core_refs(PLAN())
    assert.deepEqual(refs, ['card:question', 'card:hypothesis', 'card:test_summary', 'card:if_lever', 'card:if_not', 'card:anchor', 'card:closest_prior', 'src:s2', 'src:s3'])
    const p = PLAN()
    p.limits.push('Transfer to hardware is poor [s4].')
    p.hypothesis += ' [s1]'
    assert.deepEqual(gate_core_refs(p).filter(r => r.startsWith('src:')), ['src:s1', 'src:s2', 'src:s3'])
    // a restructured plan adds sequential_part and the sources it cites; a plan with no restructuring record does not
    const q = PLAN()
    q.restructuring = { ...RESTRUCTURED, sequential_part: 'Each step waits on the last, 32,000 steps [s4].' }
    assert.deepEqual(gate_core_refs(q), ['card:question', 'card:hypothesis', 'card:test_summary', 'card:if_lever', 'card:if_not', 'card:anchor', 'card:closest_prior', 'card:sequential_part', 'src:s2', 'src:s3', 'src:s4'])
    delete q.restructuring
    assert.ok(!gate_core_refs(q).includes('card:sequential_part'))
  })

  test('gate_restructured: method trimmed and lowercased is not "none"; missing or empty counts as none', () => {
    const p = PLAN()
    assert.equal(gate_restructured(p), false)
    for (const [method, want] of [['none', false], [' NONE ', false], ['', false], ['steps combined in rounds', true], ['none: copies only', true]]) {
      p.restructuring.method = method
      assert.equal(gate_restructured(p), want, JSON.stringify(method))
    }
    delete p.restructuring
    assert.equal(gate_restructured(p), false)
    assert.equal(gate_restructured(null), false)
  })

  // integration fix 8: the item builder main.js and replay.js share
  test('gate_dramaturg_items: card fields with their [s1, s2] sources, core sources, load-bearing or full-scale CITED/PROXY numbers, rates on request', () => {
    const plan = {
      question: 'Does error fall with samples [s1, s2]?', hypothesis: 'It falls.', predictions: { if_lever: 'falls 2x', if_not: 'flat' },
      test_summary: 'Run it.', limits: ['one model'], anchor: { what: 'reproduce 3.1', published_value: 3.1, tolerance: '5%', source_id: 's2' },
      novelty: { closest_prior: 'p', closest_source_id: 's1', prior_max_level: 8, left_open: '' }, phases: [{ id: 'P1', what: 'x' }],
      numbers: [{ id: 'n1', name: 'n', unit: 'h', basis: 'CITED', value: 6, source_id: 's1', quote: '6' }, { id: 'g1', name: 'g', unit: 'x', basis: 'GUESS', value: 2 },
        { id: 'f1', name: 'f', unit: 'x', basis: 'PROXY', value: 9, source_id: 's3' }, { id: 'u1', name: 'u', unit: 'x', basis: 'CITED', value: 1 }],
      cost: { rates: [{ id: 'r1', gpu: 'H100', n_gpus: 8, per_gpu_usd_h: 3 }], lines: [{ id: 'l1', phase: 'P1', what: 'w', kind: 'work', rate: 'r1', hours: 'n1 * g1' }], total_stated: 288 },
      full_scale: [{ id: 'fs', what: 'all', usd: 'f1 * 1e6' }],
      sources: [{ id: 's1', url: 'https://a', quote: 'q1', supports: 'prior' }, { id: 's2', url: 'https://b', quote: 'q2', supports: 'anchor' }, { id: 's3', url: 'https://c', quote: 'q3', supports: 'proxy' }],
    }
    const FIELDS = [['question', 'question'], ['hypothesis', 'hypothesis'], ['if_lever', 'predictions.if_lever'], ['if_not', 'predictions.if_not'], ['test_summary', 'test_summary'],
      ['closest_prior', 'novelty.closest_prior'], ['left_open', 'novelty.left_open'], ['anchor', 'anchor.what'], ['limits', 'limits']]
    const items = gate_dramaturg_items(plan, FIELDS)
    const by = ref => items.find(i => i.ref === ref)
    assert.deepEqual(items.map(i => i.ref), ['card:question', 'card:hypothesis', 'card:if_lever', 'card:if_not', 'card:test_summary', 'card:closest_prior', 'card:anchor', 'card:limits',
      'src:s1', 'src:s2', 'num:n1', 'num:f1'])
    assert.deepEqual(by('card:question').sources.map(x => x.id), ['s1', 's2'])
    assert.deepEqual([by('card:anchor').value, by('card:anchor').sources.map(x => x.id)], [3.1, ['s2']])
    assert.deepEqual([by('card:closest_prior').value, by('card:closest_prior').sources.map(x => x.id)], [8, ['s1']])
    assert.equal(by('num:f1').url, 'https://c')
    assert.deepEqual(gate_dramaturg_items(plan, FIELDS, { rates: true }).filter(i => i.ref.startsWith('rate:')).map(i => i.ref), ['rate:r1'])
    // the restructuring card fields go only on a restructured plan; sequential_part is then core, with its source
    const R = [['sequential_part', 'restructuring.sequential_part'], ['method', 'restructuring.method'], ...FIELDS]
    plan.restructuring = { sequential_part: 'Each step waits on the last [s3].', method: 'none' }
    assert.ok(!gate_dramaturg_items(plan, R).some(i => /^card:(sequential_part|method)$/.test(i.ref)))
    plan.restructuring.method = 'steps combined in rounds'
    const rs = gate_dramaturg_items(plan, R)
    assert.deepEqual(rs.slice(0, 2).map(i => [i.ref, i.sources.map(x => x.id)]), [['card:sequential_part', ['s3']], ['card:method', []]])
    assert.ok(rs.some(i => i.ref === 'src:s3'))
  })

  test('gate_decision: core blocking statuses REJECT; PARTIAL and non-core failures PASS and are listed', () => {
    const core = gate_core_refs(PLAN())
    for (const status of ['UNSUPPORTED', 'CONTRADICTED', 'UNREACHABLE']) {
      const r = gate_decision([item('src:s2', status), item('card:question', 'SUPPORTED')], core, PLAN(), EV(), GIVEN)
      assert.equal(r.result, 'REJECT', status)
      assert.deepEqual(r.blocking.map(i => i.ref), ['src:s2'])
    }
    const r = gate_decision([item('card:test_summary', 'PARTIAL'), item('card:limits', 'CONTRADICTED'), item('src:s4', 'UNREACHABLE'),
      item('rate:h100x8', 'CONTRADICTED', { page_value: 4.99 }), item('card:question', 'SUPPORTED')], core, PLAN(), EV(), GIVEN)
    assert.equal(r.result, 'PASS')
    assert.deepEqual(r.blocking, [])
    assert.deepEqual(r.listed.map(i => i.ref), ['card:test_summary', 'card:limits', 'src:s4', 'rate:h100x8'])
  })

  test('gate_decision: CONTRADICTED num: re-evaluated at page_value blocks only over budget', withCost(() => {
    const core = gate_core_refs(PLAN())
    const run = (status, page_value) => gate_decision([item('num:steps_per_h', status, page_value === undefined ? {} : { page_value })], core, PLAN(), EV(), GIVEN)
    const over = run('CONTRADICTED', 2000)          // 63 h of sweep: about $2,075 planned
    assert.equal(over.result, 'REJECT')
    assert.deepEqual(over.blocking.map(i => i.ref), ['num:steps_per_h'])
    const under = run('CONTRADICTED', 4500)         // 28 h: about $958 planned
    assert.equal(under.result, 'PASS')
    assert.deepEqual(under.listed.map(i => i.ref), ['num:steps_per_h'])
    assert.equal(run('CONTRADICTED').result, 'PASS')          // no page_value: never blocks
    assert.equal(run('UNSUPPORTED', 2000).result, 'PASS')     // only CONTRADICTED is re-evaluated
    assert.equal(run('UNREACHABLE').result, 'PASS')
    // planted cards come without a plan: nothing to re-evaluate, so the item is listed
    assert.deepEqual(gate_decision([item('num:steps_per_h', 'CONTRADICTED', { page_value: 2000 })], [], null, null, GIVEN).listed.length, 1)
  }))

  // ---- critique ----
  const CARD_FIELDS = ['question', 'hypothesis', 'if_lever', 'if_not', 'test_summary', 'closest_prior', 'left_open', 'anchor', 'limits']
  const CRIT = ['stakes', 'lever', 'verifiable', 'open']
  const crit = (o = {}) => ({
    scores: [
      { criterion: 'stakes', value: 4, ref: 'card:if_lever', reason: 'a lab would buy more training on it' },
      { criterion: 'lever', value: 5, ref: 'plan:predictions.decision_rule', reason: 'numeric rule with a noise margin' },
      { criterion: 'verifiable', value: 3, ref: 'plan:phases.P1.stop_rule', reason: 'exact success flag, reproduction first' },
      { criterion: 'open', value: 4, ref: 'plan:phases[0].what', reason: 'prior stops at a smaller step count' },
    ],
    decides_by: 'P2', decides_by_reason: 'the sweep gives both outcomes', ...o,
  })

  test('gate_critique: valid; refs resolve by path, index and id', () => {
    assert.deepEqual(gate_critique(crit(), CARD_FIELDS, PLAN(), CRIT), { ok: true, errors: [] })
    assert.equal(gate_critique(crit({ decides_by: 'none' }), CARD_FIELDS, PLAN(), CRIT).ok, true)
  })

  test('gate_critique: missing criterion, bad value, NA rule, unresolved ref, short reason, unknown phase', () => {
    const c = crit({ decides_by: 'P9' })
    c.scores[0].ref = 'card:summary'
    c.scores[1].value = 'NA'
    c.scores[2].reason = 'fine'
    c.scores[3].ref = 'plan:predictions.nothing'
    c.scores.push({ criterion: 'novelty', value: 3, ref: 'card:question', reason: 'not a criterion in this set' })
    const e = gate_critique(c, CARD_FIELDS, PLAN(), CRIT).errors.join('\n')
    assert.match(e, /stakes: ref "card:summary" does not resolve/)
    assert.match(e, /lever: value "NA"/)
    assert.match(e, /verifiable: reason under 15 characters/)
    assert.match(e, /open: ref "plan:predictions.nothing" does not resolve/)
    assert.match(e, /unknown criterion novelty/)
    assert.match(e, /decides_by P9 is not a phase id/)
    const d = crit()
    d.scores.pop()
    assert.match(gate_critique(d, CARD_FIELDS, PLAN(), CRIT).errors.join('\n'), /open: 0 scores/)
    const noAxis = PLAN()
    delete noAxis.compute_axis
    const na = crit()
    na.scores[1] = { criterion: 'lever', value: 'NA', ref: 'plan:compute_axis', reason: 'no compute axis in this exempt branch' }
    assert.equal(gate_critique(na, CARD_FIELDS, noAxis, CRIT).ok, true)
  })

  test('gate_critique: reshape and baseline; baseline NA only when the plan is not restructured', () => {
    const C6 = [...CRIT, 'reshape', 'baseline']
    const c = (baseline) => crit({ scores: [...crit().scores, { criterion: 'reshape', value: 1, ref: 'card:method', reason: 'independent copies side by side only' },
      { criterion: 'baseline', value: baseline, ref: 'plan:restructuring.method', reason: 'no restructuring, so no baselines timed' }] })
    const F = [...CARD_FIELDS, 'sequential_part', 'method']
    assert.equal(gate_critique(c('NA'), F, PLAN(), C6).ok, true)
    assert.equal(gate_critique(c(2), F, PLAN(), C6).ok, true)
    const old = PLAN()
    delete old.restructuring   // a record from before the field: method counts as none
    assert.equal(gate_critique(c('NA'), F, old, C6).ok, true)
    const rp = PLAN()
    rp.restructuring = { ...RESTRUCTURED }
    assert.match(gate_critique(c('NA'), F, rp, C6).errors.join('\n'), /baseline: value "NA"/)
    assert.equal(gate_critique(c(4), F, rp, C6).ok, true)
    assert.match(gate_critique(crit(), F, rp, C6).errors.join('\n'), /reshape: 0 scores[\s\S]*baseline: 0 scores/)
  })

  // ---- options, option critic, totals ----
  const opt = (id, o = {}) => ({ id, title: `Option ${id}`, summary: 'a summary', root_link: 'none', compute_open: 'none', sequential: 'none: independent runs', source_urls: [], ...o })

  test('gate_opt: count, unique ids, non-empty fields (sequential included)', () => {
    assert.deepEqual(gate_opt([opt('W1'), opt('W2'), opt('W3')]), { ok: true, errors: [] })
    assert.equal(gate_opt([opt('W1'), opt('W2')]).ok, false)
    assert.equal(gate_opt(Array.from({ length: 26 }, (_, i) => opt(`W${i}`))).ok, false)
    const r = gate_opt([opt('W1'), opt('W1'), opt('W3', { compute_open: ' ' })])
    assert.deepEqual(r.errors, ['duplicate id W1', 'W3: empty compute_open'])
    assert.deepEqual(gate_opt([opt('W1', { sequential: undefined }), opt('W2', { sequential: '  ' }), opt('W3')]).errors, ['W1: empty sequential', 'W2: empty sequential'])
  })

  const sc = (id, values, o = {}) => ({
    id, distance: 'ADJACENT', distance_reason: 'nearby field',
    scores: Object.entries(values).map(([criterion, value]) => ({ criterion, value, reason: `${criterion} reason long enough here` })), ...o,
  })

  test('gate_oc: ids, distance, criteria, integer values, degenerate reasons', () => {
    const opts = [opt('I1'), opt('I2')]
    const C = ['stakes', 'open', 'internals']
    assert.deepEqual(gate_oc([sc('I1', { stakes: 4, open: 3, internals: 5 }), sc('I2', { stakes: 1, open: 1, internals: 1 })], opts, C), { ok: true, errors: [], degenerate: [] })
    const r = gate_oc([sc('I1', { stakes: 6, open: 2.5 }, { distance: 'FAR' }), sc('I9', { stakes: 1, open: 1, internals: 1 })], opts, C)
    assert.deepEqual(r.errors, ['I1: distance FAR', 'I1: stakes = 6', 'I1: open = 2.5', 'I1: missing internals', 'unknown id I9', 'missing id I2'])
    const d = sc('I1', { stakes: 4, open: 3, internals: 5 })
    d.scores[2].reason = 'Internals '
    assert.deepEqual(gate_oc([d, sc('I2', { stakes: 1, open: 1, internals: 1 })], opts, C).degenerate, ['I1'])
  })

  test('gate_totals: sum, with the open floor for settled and none; reshape is not part of the total', () => {
    const s = [sc('W1', { stakes: 4, open: 5 }), sc('W2', { stakes: 3, open: 4 }), sc('W3', { stakes: 2, open: 3 })]
    assert.deepEqual(gate_totals(s, ['stakes', 'open'], { W1: 'open', W2: 'settled', W3: 'none' }), { W1: 9, W2: 4, W3: 3 })
    const r = [sc('W1', { stakes: 4, open: 5, reshape: 5 }), sc('W2', { stakes: 3, open: 4, reshape: 1 })]
    assert.deepEqual(gate_totals(r, ['stakes', 'open', 'reshape'], { W1: 'open', W2: 'none' }), { W1: 9, W2: 4 })
  })

  // ---- dedup, Jaccard, overlap, price sheet ----
  test('gate_dedup: partition and topic length', () => {
    const keys = ['R1:physical:W1', 'R2:physical:W4', 'R3:interp:I2']
    assert.equal(gate_dedup([{ topic: 'privacy audits by retraining', members: keys }], keys).ok, true)
    const r = gate_dedup([{ topic: 'privacy audits', members: keys.slice(0, 2) }, { topic: 'probe based audits', members: ['R1:physical:W1', 'R9:x:y'] }], keys)
    assert.deepEqual(r.errors, ['unknown key R9:x:y', 'R1:physical:W1 is in 2 clusters', 'R3:interp:I2 is in 0 clusters'])
    assert.deepEqual(r.soft, ['topic "privacy audits" has fewer than 3 words'])
    const short = gate_dedup([{ topic: 'privacy audits', members: keys }], keys)
    assert.equal(short.ok, true)
    assert.deepEqual(short.soft, ['topic "privacy audits" has fewer than 3 words'])
  })

  test('dedup_handles / dedup_unhandle: short handles per branch, round trip', () => {
    const o = [{ key: 'R2:interp:A. Inference-time steering of VLA internals ' }, { key: 'R2:interp:B. Internal-feature failure detection' }, { key: 'R5:physical:W1' }]
    const h = dedup_handles(o)
    assert.deepEqual(h.lines.map(l => l.handle), ['R2:interp:K1', 'R2:interp:K2', 'R5:physical:K1'])
    const back = dedup_unhandle([{ topic: 'monitoring of robot policies', members: ['R2:interp:K2', 'R5:physical:K1'] }, { topic: 'steering of VLA internals', members: ['R2:interp:K1'] }], h.toKey)
    assert.deepEqual(back.map(c => c.members), [[o[1].key, o[2].key], [o[0].key]])
    assert.equal(gate_dedup(back, o.map(x => x.key)).ok, true)
    assert.deepEqual(dedup_unhandle(null, h.toKey), [])
    assert.deepEqual(gate_dedup(dedup_unhandle([{ topic: 'a b c', members: ['R2:interp:A'] }], h.toKey), o.map(x => x.key)).errors[0], 'unknown key R2:interp:A')
  })

  test('dedup_best: valid partition with the fewest soft faults; null without one', () => {
    const keys = ['R1:physical:W1', 'R2:physical:W4', 'R3:interp:I2']
    const opts = [{ key: keys[0], title: 'privacy audits by retraining' }, { key: keys[1], title: 'privacy audits by retraining models' }, { key: keys[2], title: 'probes on reviewer models' }]
    const broken = { clusters: [{ topic: 'privacy audits by retraining', members: keys.slice(0, 2) }] }
    const split = { clusters: [{ topic: 'privacy audits', members: [keys[0]] }, { topic: 'retraining audits', members: [keys[1]] }, { topic: 'probes on reviewer models', members: [keys[2]] }] }
    const merged = { clusters: [{ topic: 'privacy audits', members: keys.slice(0, 2) }, { topic: 'probes on reviewer models', members: [keys[2]] }] }
    assert.equal(dedup_best([broken], opts, keys, 0.4), null)
    assert.equal(dedup_best([null, broken, split], opts, keys, 0.4).clusters, split.clusters)
    assert.equal(dedup_best([split], opts, keys, 0.4).faults, 3)
    const b = dedup_best([split, merged], opts, keys, 0.4)
    assert.equal(b.clusters, merged.clusters)
    assert.equal(b.faults, 1)
  })

  test('gate_dedup_jaccard on the stored 119 titles: 9 cross-root pairs at 0.4 (flow.md M7); merged clusters pass', () => {
    const opts = fixture('gates/titles.json')
    const singletons = opts.map(o => ({ topic: `only ${o.key} here`, members: [o.key] }))
    const r = gate_dedup_jaccard(opts, singletons, 0.4)
    assert.equal(r.violations.length, 9)
    assert.ok(r.violations.every(v => v.a.split(':')[0] !== v.b.split(':')[0] && v.jaccard >= 0.4))
    // union the violating pairs into clusters: the check then passes
    const parent = new Map(opts.map(o => [o.key, o.key]))
    const find = k => (parent.get(k) === k ? k : find(parent.get(k)))
    for (const v of r.violations) parent.set(find(v.a), find(v.b))
    const groups = new Map()
    for (const o of opts) groups.set(find(o.key), [...(groups.get(find(o.key)) || []), o.key])
    const merged = [...groups.values()].map(members => ({ topic: 'merged near duplicate titles', members }))
    assert.equal(gate_dedup_jaccard(opts, merged, 0.4).ok, true)
    assert.equal(gate_dedup(merged, opts.map(o => o.key)).ok, true)
  })

  test('gate_dedup_jaccard: same-root pairs are not checked', () => {
    const opts = [{ key: 'R1:physical:W1', title: 'Proof search for formal mathematics' }, { key: 'R1:interp:I1', title: 'Proof search for formal mathematics' }]
    assert.equal(gate_dedup_jaccard(opts, [{ topic: 'a b c', members: ['R1:physical:W1'] }, { topic: 'd e f', members: ['R1:interp:I1'] }], 0.4).ok, true)
  })

  test('gate_overlap', () => {
    const roots = ['R1', 'R2', 'R3', 'R4', 'R5']
    assert.equal(gate_overlap([{ a: 'R2', b: 'R5', shared_subject: 'kilometre-scale weather simulation' }], roots).ok, true)
    const r = gate_overlap([{ a: 'R2', b: 'R2', shared_subject: 'weather' }, { a: 'R6', b: 'R1', shared_subject: 'three word subject' }], roots)
    assert.deepEqual(r.errors, ['bad pair R2/R2', 'R2/R2: shared_subject has fewer than 3 words', 'bad pair R6/R1'])
  })

  test('gate_price_sheet: count, 8x H100, prices in (0, 20)', () => {
    const sheet = () => fixture('gates/records.json').PRICE_SHEET
    assert.deepEqual(gate_price_sheet(sheet()), { ok: true, errors: [] })
    const s = sheet()
    s.instances = s.instances.filter(i => !(i.gpu === 'H100' && i.n_gpus === 8))
    s.instances[0].per_gpu_usd_h = 0
    s.instances[1].per_gpu_usd_h = 25
    s.filesystem.usd_gib_month = -1
    const e = gate_price_sheet(s).errors
    assert.deepEqual(e, ['4 instances (want at least 5)', 'no 8x H100 instance', '1x A100: price 0 outside (0, 20)', '8x A100: price 25 outside (0, 20)', 'filesystem price -1 outside (0, 20)'])
  })
})()
