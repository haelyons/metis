// replay.js is a workflow body, not a module, so the runner does not load it. As in main.test.js, it is read as text
// (fixture() resolves against tests/fixtures, so '../../' reaches the repo) for the build.js checks and the contract
// names it uses, and its control flow is run synchronously (async/await stripped) against stub modules and agent.
// replay/args_A.json is checked through its copy in fixtures/replay/ (refresh: cp replay/args_A.json tests/fixtures/replay/).
(() => {
  const SRC = fixture('../../src/replay.js')
  const CONTRACT = fixture('../../CONTRACT.md')
  const API = CONTRACT.slice(CONTRACT.indexOf('## 3. Module APIs'), CONTRACT.indexOf('## 4. '))
  // identifiers the body calls or reads (an object key such as `pick_run_by_sample:` is not one)
  const USED = [...new Set(SRC.match(/\b(?:P|SCHEMA|CRIT|ROLE|ORIG)_[A-Z0-9_]+\b(?!\s*:)|\b(?:gate|cost|pick|render|txt)_\w+\b(?!\s*:)|\bEX[12]_TEXT\b/g))].sort()
  // pick_selftest is required by CONTRACT §1; pick_run_legacy is exported by pick.js for this replay. Neither is named in §3.
  const OFF_CONTRACT = ['pick_selftest', 'pick_run_legacy']
  const META = Function(`return (${SRC.slice('export const meta = '.length, SRC.indexOf('\n// @@MODULES@@'))})`)()
  const PHASES = META.phases.map(p => p.title)
  const ROLES = ['qt-bare', 'qt-research', 'qt-producer', 'qt-web', 'qt-extract']
  const ARGS = fixture('replay/args_A.json')
  // fixture() parses in the runner's realm; compare across realms by value
  const same = (a, b, m) => assert.equal(JSON.stringify(a), JSON.stringify(b), m)

  test('replay: passes the build.js header and forbidden-construct checks', () => {
    assert.ok(SRC.startsWith('export const meta'))
    assert.ok(SRC.split('\n').includes('// @@MODULES@@'))
    const FORBIDDEN = [/\bimport\s/, /\bexport\s(?!const meta)/, /\brequire\(/, /module\.exports/, /Math\.random\(/, /Date\.now\(/, /new Date\(\s*\)/]
    for (const re of FORBIDDEN) assert.ok(!re.test(SRC.replace(/^export const meta/, '')), `violates ${re}`)
    const AsyncFunction = (async () => {}).constructor
    new AsyncFunction(SRC.replace(/^export const meta/, 'const meta'))   // syntax only
  })

  test('replay: meta is a pure literal and every phase used is declared', () => {
    assert.equal(typeof META.name, 'string')
    assert.equal(typeof META.description, 'string')
    for (const p of META.phases) assert.deepEqual(Object.keys(p), ['title', 'detail'])
    const used = [...SRC.matchAll(/phase: '([^']+)', (?:schema|agentType)/g)].map(m => m[1])
    assert.ok(used.length >= 10)
    assert.deepEqual([...new Set(used)].filter(p => !PHASES.includes(p)), [])
  })

  test('replay: every module identifier it uses is named in CONTRACT §3, and no top-level name takes a module prefix', () => {
    assert.ok(USED.length > 30)
    assert.deepEqual(USED.filter(id => !OFF_CONTRACT.includes(id) && !new RegExp(`\\b${id}\\b`).test(API)), [])
    const top = [...SRC.matchAll(/^(?:const|let|function|async function)\s+(\w+)/gm)].map(m => m[1])
    assert.deepEqual(top.filter(n => /^(txt_|SCHEMA_|cost_|pick_|gate_|render_|P_|CRIT_|ROLE_|ORIG_)/.test(n)), [])
  })

  test('replay: args_A.json holds 20 picks with existing producer.md files, 10 branches with options and scores, 5 roots', () => {
    same(fixture('../../../../experiments/question-tree/replay/args_A.json'), ARGS, 'the fixture copy is stale')
    assert.equal(ARGS.phase, 'A')
    same(ARGS.given, { budget_usd: 1000, budget_covers_storage: true, budget_covers_tax: false })
    assert.equal(ARGS.picks.length, 20)
    assert.equal(new Set(ARGS.picks.map(p => `${p.root}:${p.branch}:${p.id}`)).size, 20)
    for (const p of ARGS.picks) {
      assert.ok(['top', 'random'].includes(p.kind) && ['physical', 'interp'].includes(p.branch), p.id)
      assert.equal(p.producer_path, `${p.dir}/producer.md`)
      assert.ok(p.dir.startsWith('/home/hal/stage/runs-v3/seed-1/'), p.dir)
      assert.ok(fixture(p.producer_path).length > 1000, p.producer_path)   // exists, not empty
      const o = ARGS.options_by_branch[`${p.root}:${p.branch}`].find(x => x.id === p.id)
      assert.ok(o && o.title === p.title, p.id)
    }
    assert.equal(ARGS.picks.filter(p => p.kind === 'top').length, 10)
    const branches = Object.keys(ARGS.options_by_branch)
    assert.equal(branches.length, 10)
    same(Object.keys(ARGS.old_scores).sort(), branches.sort())
    for (const bk of branches) {
      const ids = ARGS.options_by_branch[bk].map(o => o.id)
      assert.ok(ids.length >= 3 && ARGS.options_by_branch[bk].every(o => o.title && o.summary), bk)
      same(ARGS.old_scores[bk].map(s => s.id).sort(), [...ids].sort(), bk)
      assert.ok(ARGS.old_scores[bk].every(s => typeof s.total === 'number' && s.scores), bk)
    }
    assert.equal(branches.reduce((n, bk) => n + ARGS.options_by_branch[bk].length, 0), 119)
    same(ARGS.roots.map(r => r.id), ['R1', 'R2', 'R3', 'R4', 'R5'])
    assert.ok(ARGS.roots.every(r => r.question.length > 40))
  })

  // ---------- synchronous run against stubs ----------
  const SYNC = SRC.replace(/^export const meta/, 'const meta').replace(/\bawait\s+/g, '').replace(/\basync\s+/g, '')
  const OC = { physical: ['stakes', 'open', 'reshape'], interp: ['stakes', 'open', 'internals', 'reshape'] }
  const ok = () => ({ ok: true, failures: [] })
  const plan = (title, n) => ({
    option_title: title, question: n === 2 ? 'Does W11 fall?' : 'Does it fall?', hypothesis: 'It falls.',
    compute_axis: { quantity: 'samples', unit: 'n', levels: [1, 64] }, predictions: { if_lever: 'falls 2x', if_not: 'flat', decision_rule: 'ratio >= 2', expected: 'if_lever' },
    compute_tested: 'yes', anchor: { what: 'reproduce 3.1', tolerance: '5%', source_id: 's2' }, test_summary: 'Run it.',
    novelty: { closest_prior: 'p', closest_source_id: 's1', prior_max_level: n === 3 ? 128 : 8, left_open: 'l', decides: 'no', searched: true },
    limits: ['one model'], phases: [{ id: 'P1', what: 'x' }], numbers: [{ id: 'n1', basis: 'CITED', value: 6, source_id: 's1', quote: '6' }],
    cost: { rates: [], lines: [], total_stated: 144 }, full_scale: [], sources: [{ id: 's1', url: 'https://a', quote: 'q1' }, { id: 's2', url: 'https://b', quote: 'q2' }],
  })
  const nOf = key => ARGS.picks.findIndex(p => `${p.root}:${p.branch}:${p.id}` === key)
  // option-critic sample i (0..2): open 2, 3, 4 (mean 3); stakes 5, 5, 1 (mean 3.67 -> 4); internals 1; reshape 5, 4, 5 (mean 4.67 -> 5);
  // distance SAME, ELSEWHERE, ELSEWHERE
  function reply(prompt, o) {
    const i = Number((o.label.match(/option-critic:(\d)$/) || [])[1]) - 1
    switch (o.schema) {
      case 'PRICE_SHEET': return { read_at: '2026-10-16', instances: [], filesystem: {} }
      case 'PLAN': return nOf(`${o.label.split(':')[0]}:${o.label.split(':')[1]}:${ARGS.picks.find(p => p.producer_path === prompt.a[0]).id}`) === 4 ? null : plan('t', ARGS.picks.findIndex(p => p.producer_path === prompt.a[0]))
      case 'REPAIR_EXPR': return { numbers: [{ id: 'n1', expr: '2*3' }], lines: [] }
      case 'REPAIR_FIELDS': return { fields: Object.fromEntries(Object.entries(prompt.a[0]).map(([k, v]) => [k, v.replace('W11', 'the ensemble')])) }
      case 'FINDINGS': return { items: prompt.a[0].map(x => ({ ref: x.ref, status: x.ref === 'card:text' && /defect/.test(x.text) ? 'CONTRADICTED' : 'SUPPORTED', page_quote: 'a page quote', note: '' })) }
      case 'CRITIQUE': return { scores: [], decides_by: 'P1', decides_by_reason: 'r' }
      case 'OPTION_SCORES': return { items: prompt.a[2].map(x => ({ id: x.id, distance: ['SAME', 'ELSEWHERE', 'ELSEWHERE'][i], distance_reason: 'r',
        scores: OC[prompt.a[1]].map(c => ({ criterion: c, value: { open: [2, 3, 4], stakes: [5, 5, 1], internals: [1, 1, 1], reshape: [5, 4, 5] }[c][i], reason: 'a reason long enough' })) })) }
      case 'DEDUP': return { clusters: prompt.a[0].map(l => ({ topic: 'a topic here', members: [l.split(': ')[0]] })) }
      case 'OVERLAP': return { pairs: [{ a: 'R2', b: 'R5', shared_subject: 'robot hands and manipulation' }] }
      case undefined: return 'Plan costs {planned_usd}; also {not_in_menu}.'   // WRITER: text, no schema
    }
    throw new Error(`no reply for ${o.schema}`)
  }
  function world(over = {}) {
    const calls = [], logs = [], ctxs = [], runs = []
    const s = {
      calls, logs, ctxs, runs,
      log: m => logs.push(m), parallel: thunks => thunks.map(t => t()),
      agent: (prompt, o) => { calls.push({ prompt, o }); const r = over.agent && over.agent(prompt, o); return r !== undefined ? r : reply(prompt, o) },
      CRIT_OPTION: b => b, CRIT_CARD: b => b,
      cost_selftest: ok, pick_selftest: ok, gate_selftest: ok, render_selftest: ok,
      cost_eval_plan: p => ({ ok: true, errors: p.numbers[0].expr ? [] : [{ kind: 'parse', where: 'n1', msg: 'bad' }], planned: 144, flags: [] }),
      cost_load_bearing: () => ({ ids: ['n1'], uncertain: [] }),
      cost_render_block: () => 'block line 1\nblock line 2', cost_menu: () => [{ id: 'planned_usd', name: 'planned spend', value: '$144.00', tag: '=' }],
      // pick 1 needs a cost repair; pick 2 halts at G-plan (compute_tested no) and must still be carded and judged
      gate_plan: (p, ev, pick) => (ev.errors.length && nOf(pick.key) === 0 ? { action: 'repair', reasons: ['parse at n1: bad'], annotations: [] }
        : nOf(pick.key) === 1 ? { action: 'halt', reasons: ['compute_tested is no: w'], annotations: ['a'] } : { action: 'ok', reasons: [], annotations: [] }),
      gate_cardfields: p => { const failing = /W11/.test(p.question) ? [{ field: 'question', reasons: ['record ids: W11'] }] : []; return { ok: !failing.length, failing, annotations: [] } },
      gate_number_preservation: (a, b) => (a.match(/(?<![A-Za-z\d])\d+/g) || []).every(n => b.includes(n)),   // digits in codes (W11) are not numbers
      gate_price_sheet: () => ({ ok: true, errors: [] }),
      gate_findings: () => ({ ok: true, errors: [], degenerate: [] }),
      gate_core_refs: () => ['card:question', 'src:s1'],
      gate_decision: (items, core) => { const blocking = items.filter(i => core.includes(i.ref) && i.status !== 'SUPPORTED'); return { result: blocking.length ? 'REJECT' : 'PASS', blocking, listed: [] } },
      gate_critique: () => ({ ok: true, errors: [] }),
      gate_dramaturg_items,   // the real shared builder (integration fix 8); it reads the real cost and gates helpers
      gate_restructured,
      gate_totals: scored => Object.fromEntries(scored.map(x => [x.id, x.scores.reduce((t, c) => t + (c.criterion === 'reshape' ? 0 : c.value), 0)])),
      gate_dedup: () => ({ ok: true, errors: [], soft: [] }),
      gate_dedup_jaccard: (opts, clusters) => ({ ok: true, violations: clusters.length === opts.length ? [{ a: 'x', b: 'y' }] : [] }),
      dedup_best: () => null,
      dedup_handles: opts => ({ lines: opts.map(o => ({ handle: o.key, option: o })), toKey: new Map() }), dedup_unhandle: c => c,
      gate_overlap: () => ({ ok: true, errors: [] }),
      pick_u: (seed, key) => { let h = 2166136261; for (const ch of `${seed}:${key}`) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619) } return (h >>> 0) / 4294967296 },
      pick_run: input => { runs.push(input); return { picks: [], frontier: [], inventory: [], log: [] } },
      pick_run_legacy: input => ({ legacy: input }),
      render_card: c => { ctxs.push(c); return `card ${c.pick.key}` },
    }
    for (const n of USED) if (n.startsWith('P_') && !(n in s)) s[n] = (...a) => ({ p: n, a })
    for (const n of USED) if (n.startsWith('SCHEMA_')) s[n] = n.slice(7)
    return Object.assign(s, over.stubs)
  }
  function run(args, w) {
    const names = ['agent', 'parallel', 'log', ...USED]
    assert.deepEqual(names.filter(n => !(n in w)), [], 'stubs missing')
    return Function('args', ...names, SYNC)(args, ...names.map(n => w[n]))
  }
  const byLabel = (w, re) => w.calls.filter(c => re.test(c.o.label))
  const SONNET = /price-sheet|extract|repair|writer|critic$|dedup|overlap/   // extract: replay.js passes model sonnet as well as the role's pin
  const checkCalls = w => {
    for (const { o } of w.calls) {
      assert.ok(o.label && PHASES.includes(o.phase) && ROLES.includes(o.agentType), JSON.stringify(o))
      assert.equal(o.model, SONNET.test(o.label) ? 'sonnet' : undefined, o.label)
    }
  }

  test('replay: missing args, a bad phase or a failing self-test return {error} before any agent', () => {
    for (const a of [{ ...ARGS, phase: 'C' }, { ...ARGS, picks: undefined }, { ...ARGS, phase: 'B' }, 'not json']) {
      const w = world()
      assert.ok(run(a, w).error)
      assert.equal(w.calls.length, 0)
    }
    const w = world({ stubs: { render_selftest: () => ({ ok: false, failures: ['case 2'] }) } })
    assert.deepEqual(run(ARGS, w).failures, ['render: case 2'])
    assert.equal(w.calls.length, 0)
  })

  const wA = world()
  const outA = run(JSON.stringify(ARGS), wA)
  const recs = outA.records

  test('replay A: price sheet, 20 extracts, one repair, halts carried on, cards, 10 writer cells', () => {
    checkCalls(wA)
    assert.deepEqual(Object.keys(outA), ['phase', 'price_sheet', 'records', 'log'])
    assert.equal(byLabel(wA, /price-sheet/).length, 1)
    const ex = byLabel(wA, /:extract$/)
    same(ex.map(c => c.prompt.a), ARGS.picks.map(p => [p.producer_path, p.dir]))
    assert.equal(recs.length, 20)
    same(recs.map(r => r.pick.key), ARGS.picks.map(p => `${p.root}:${p.branch}:${p.id}`))
    // pick 5's extract returned null: a schema halt with no plan and no card
    assert.equal(recs[4].plan, null)
    assert.equal(recs[4].halted.gate, 'schema')
    assert.equal(recs[4].card, null)
    // pick 1: one cost repair, applied, re-evaluated
    assert.equal(byLabel(wA, /repair-expr$/).length, 1)
    assert.equal(recs[0].plan.numbers[0].expr, '2*3')
    assert.equal(recs[0].gate.action, 'ok')
    assert.equal(recs[0].repairs[0].kind, 'expr')
    // pick 2: halted at G-plan, still rendered with the halt
    assert.deepEqual(recs[1].halted, { gate: 'G-plan', reasons: ['compute_tested is no: w'] })
    assert.ok(recs[1].card && wA.ctxs.find(c => c.pick.key === recs[1].pick.key).halted)
    // pick 3: a failing card field repaired, number kept; beyond_prior from the axis (64 < 128)
    assert.equal(recs[2].plan.question, "Does the ensemble fall?")
    assert.equal(recs[2].cardfields.ok, false)
    assert.deepEqual(recs[2].np_failures, [])
    assert.equal(recs[3].beyond_prior, false)
    assert.equal(recs[5].beyond_prior, true)
    assert.equal(recs[3].block, 'block line 1\nblock line 2')
    for (const c of wA.ctxs) for (const k of ['pick', 'option', 'root_question', 'plan', 'eval', 'given', 'findings', 'decision', 'critique', 'beyond_prior', 'annotations', 'halted', 'producer_path']) assert.ok(k in c, `ctx lacks ${k}`)
    // writer on the 10 picks lowest in pick_u(seed, 'replaywriter:' + key), among those with a plan
    const keys = ARGS.picks.map(p => `${p.root}:${p.branch}:${p.id}`)
    const want = [...keys].sort((a, b) => wA.pick_u(1, `replaywriter:${a}`) - wA.pick_u(1, `replaywriter:${b}`)).slice(0, 10).filter(k => k !== keys[4])
    same(byLabel(wA, /:writer$/).map(c => keys.find(k => c.o.label.startsWith(tagOf(k)))).sort(), want.sort())
    const w = recs.filter(r => r.writer_raw)
    assert.equal(w.length, want.length)
    assert.equal(w[0].writer_text, 'Plan costs $144.00; also {not_in_menu}.')
    assert.ok(byLabel(wA, /:writer$/).every(c => !('cost' in c.prompt.a[2]) && c.prompt.a[1].compute_open === 'not recorded'))
  })
  function tagOf(key) { const p = ARGS.picks.find(x => `${x.root}:${x.branch}:${x.id}` === key); return `${p.root}:${p.branch}:${p.kind}:` }

  test('replay A: a given price sheet is used without an agent', () => {
    const w = world()
    const out = run({ ...ARGS, price_sheet: { read_at: 'x' } }, w)
    assert.equal(byLabel(w, /price-sheet/).length, 0)
    assert.deepEqual(out.price_sheet, { read_at: 'x' })
    assert.ok(w.ctxs.every(c => c.given.price_sheet.read_at === 'x' && c.given.budget_usd === 1000))
  })

  test('replay B: dramaturg on every card and the planted set, critic, 3 option-critic samples, judges, pick rules', () => {
    const planted = [{ id: 'clean', card_text: 'all fine', sources: [{ id: 's1', url: 'u', quote: 'q', supports: 'x' }], expected: 'PASS' },
      { id: 'bad', card_text: 'a defect here', sources: [], expected: 'REJECT' }]
    const w = world()
    const out = run({ ...ARGS, phase: 'B', price_sheet: outA.price_sheet, records: recs, planted_cards: planted }, w)
    checkCalls(w)
    assert.equal(byLabel(w, /^R\d:\w+:\w+:dramaturg$/).length, 19)
    assert.equal(byLabel(w, /:critic$/).length, 19)
    assert.equal(out.dramaturg.length, 19)
    assert.ok(out.dramaturg.every(d => d.decision.result === 'PASS' && d.items.length))
    assert.deepEqual(out.planted.map(p => [p.id, p.decision.result]), [['clean', 'PASS'], ['bad', 'REJECT']])
    // the critic never sees cost, full_scale or the producer's self-grades; a record from before PLAN.restructuring reads as method none
    for (const c of byLabel(w, /:critic$/)) { const v = c.prompt.a[3]; assert.ok(!('cost' in v) && !('full_scale' in v) && !('expected' in v.predictions) && !('decides' in v.novelty)) }
    for (const c of byLabel(w, /:critic$/)) {
      same(c.prompt.a[3].restructuring, { sequential_part: '', method: 'none' })
      assert.ok(c.prompt.a[2].includes('\ncard:method: none\n'))
    }
    assert.ok(out.dramaturg.every(d => !d.items.some(i => /^card:(sequential_part|method)$/.test(i.ref))))
    assert.ok(recs.filter(r => r.plan).every(r => !('restructuring' in r.plan)), 'phase-A records are not modified')
    const oc = byLabel(w, /option-critic:\d$/)
    assert.equal(oc.length, 30)
    assert.ok(oc.every(c => c.prompt.a[2].every(x => x.compute_open === 'not recorded' && x.root_link === 'not recorded' && x.sequential === 'not given (stored run)')))
    same(Object.keys(out.option_critic).sort(), Object.keys(ARGS.options_by_branch).sort())
    // pick_run on the means (rounded) and median distance; then one run per sample
    assert.equal(w.runs.length, 4)
    const o = w.runs[0].branches.find(b => b.root === 'R3' && b.branch === 'interp').options[0]
    assert.deepEqual(o.scores, { stakes: 4, open: 3, internals: 1, reshape: 5 })
    assert.equal(o.total, 8)   // reshape is not part of the total
    assert.equal(o.distance, 'ELSEWHERE')
    assert.equal(o.compute_open_status, 'open')
    assert.equal(o.sequential_status, 'named')   // "not given (stored run)": no floor
    assert.deepEqual(w.runs[0].args, { pool_k: 3, picks_per_branch: 2, require_compute_lever: { physical: true, interp: true } })
    assert.deepEqual(w.runs.slice(1).map(r => r.branches[0].options[0].scores.open), [2, 3, 4])
    assert.deepEqual(w.runs.slice(1).map(r => r.branches[0].options[0].distance), ['SAME', 'ELSEWHERE', 'ELSEWHERE'])
    assert.equal(out.pick_run_by_sample.length, 3)
    const leg = out.pick_run_legacy.legacy.branches.find(b => b.root === 'R1' && b.branch === 'physical')
    same(leg.options.map(x => x.total), ARGS.old_scores['R1:physical'].map(s => s.total))
    assert.equal(out.dedup.jaccard_pairs_n, 1)
    assert.equal(out.dedup.jaccard_violations_n, 1)   // the stub judge returns singletons
    assert.equal(out.overlap.raw.pairs[0].b, 'R5')
    assert.equal(byLabel(w, /dedup|overlap/).length, 2)
  })

  test('replay B: a branch with no sample back is left out of the pick rule and logged', () => {
    const w = world({ agent: (p, o) => (/^R4:physical:option-critic/.test(o.label) ? null : undefined) })
    run({ ...ARGS, phase: 'B', price_sheet: {}, records: [], planted_cards: [] }, w)
    assert.ok(w.runs.every(r => !r.branches.some(b => b.root === 'R4' && b.branch === 'physical') && r.branches.length === 9))
    assert.ok(w.logs.some(l => /R4:physical: no option-critic samples; branch left out/.test(l)))
  })
})()
