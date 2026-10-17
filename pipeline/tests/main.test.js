// main.js is a workflow body, not a module, so the runner does not load it. These tests read it as text
// (fixture() resolves against tests/fixtures, so '../../' reaches the repo): the build.js checks, the contract
// names it uses, and its control flow, run synchronously (async/await stripped) against stub modules and agent.
(() => {
  const SRC = fixture('../../src/main.js')
  const CONTRACT = fixture('../../CONTRACT.md')
  const API = CONTRACT.slice(CONTRACT.indexOf('## 3. Module APIs'), CONTRACT.indexOf('## 4. '))
  const USED = [...new Set(SRC.match(/\b(?:P|SCHEMA|CRIT|ROLE|ORIG)_[A-Z0-9_]+\b|\b(?:gate|cost|pick|render|txt)_\w+|\bEX[12]_TEXT\b/g))].sort()
  const META = Function(`return (${SRC.slice('export const meta = '.length, SRC.indexOf('\n// @@MODULES@@'))})`)()
  const PHASES = META.phases.map(p => p.title)
  const ROLES = ['qt-bare', 'qt-research', 'qt-producer', 'qt-web', 'qt-extract']

  test('main: passes the build.js header and forbidden-construct checks', () => {
    assert.ok(SRC.startsWith('export const meta'))
    assert.ok(SRC.split('\n').includes('// @@MODULES@@'))
    const FORBIDDEN = [/\bimport\s/, /\bexport\s(?!const meta)/, /\brequire\(/, /module\.exports/, /Math\.random\(/, /Date\.now\(/, /new Date\(\s*\)/]
    for (const re of FORBIDDEN) assert.ok(!re.test(SRC.replace(/^export const meta/, '')), `violates ${re}`)
    const AsyncFunction = (async () => {}).constructor
    new AsyncFunction(SRC.replace(/^export const meta/, 'const meta'))   // syntax only
  })

  test('main: meta is a pure literal and every phase used is declared', () => {
    assert.equal(typeof META.name, 'string')
    assert.equal(typeof META.description, 'string')
    for (const p of META.phases) assert.deepEqual(Object.keys(p), ['title', 'detail'])
    const used = [...SRC.matchAll(/phase: '([^']+)'/g)].map(m => m[1])
    assert.deepEqual([...new Set(used)].filter(p => !PHASES.includes(p)), [])
  })

  test('main: every module identifier it uses is named in CONTRACT §3', () => {
    assert.ok(USED.length > 40)
    const named = `${API} cost_selftest pick_selftest gate_selftest render_selftest`   // §1: <prefix>selftest() for cost, pick, gates, render
    assert.deepEqual(USED.filter(id => !new RegExp(`\\b${id}\\b`).test(named)), [])
  })

  // ---------- synchronous run against stubs ----------
  const SYNC = SRC.replace(/^export const meta/, 'const meta').replace(/\bawait\s+/g, '').replace(/\basync\s+/g, '')
  const OC = { physical: ['stakes', 'open', 'reshape'], interp: ['stakes', 'open', 'internals', 'reshape'] }
  const ok = () => ({ ok: true, failures: [] })
  const outcome = c => (c.halted ? `halted: ${c.halted.gate}` : !c.decision ? 'not judged' : `${c.decision.result}${c.decision2 ? ` / ${c.decision2.result}` : ''}`)
  const plan = title => ({
    option_title: title, question: 'Does the error fall with more samples [s1, s2]?', hypothesis: 'Error falls as samples grow.',
    compute_axis: { quantity: 'samples', unit: 'n', levels: [1, 64] }, held_fixed: ['model'],
    predictions: { if_lever: 'error falls 2x by 64', if_not: 'flat', decision_rule: 'ratio >= 2', noise_rule: 'seeds', expected: 'if_lever', expected_why: 'w' },
    compute_tested: 'yes', compute_tested_why: 'w', scored_against: 'truth', arms: [], baseline: { what: 'b' },
    anchor: { what: 'reproduce 3.1', published_value: 3.1, tolerance: '5%', source_id: 's2' }, checks: [], test_summary: 'Run it.',
    novelty: { closest_prior: 'p', closest_source_id: 's1', prior_max_level: 8, left_open: 'l', decides: 'no', searched: true },
    limits: ['one model'], phases: [{ id: 'P1', what: 'x' }], restructuring: { sequential_part: 'Each step waits on the last.', method: 'none' },
    numbers: [{ id: 'n1', basis: 'CITED', value: 6, source_id: 's1', quote: '6' }, { id: 'g1', basis: 'GUESS', value: 2 }, { id: 'f1', basis: 'PROXY', value: 9, source_id: 's2' }, { id: 'u1', basis: 'CITED', value: 1 }],
    cost: { rates: [{ id: 'r1', gpu: 'H100', n_gpus: 8, per_gpu_usd_h: 3 }], lines: [{ id: 'l1', phase: 'P1', what: 'w', kind: 'work', rate: 'r1', hours: 'n1' }], scenarios: [], yields: [], total_stated: 144 },
    full_scale: [{ id: 'fs', what: 'all', usd: 'f1 * 1e6' }], outside_budget: [], scope_gap: [],
    sources: [{ id: 's1', url: 'https://a', quote: 'q1' }, { id: 's2', url: 'https://b', quote: 'q2' }], files_read: ['f'],
  })
  function reply(prompt, o) {
    switch (o.schema) {
      case 'QUESTIONS': return { items: [{ question: `${o.label} q1` }, { question: `${o.label} q2` }] }
      case 'OVERLAP': return { pairs: [] }
      case 'PRICE_SHEET': return { read_at: '2026-10-16', instances: [], filesystem: {} }
      case 'VERDICT': return { verdict: 'COMPUTE-BOUND', compute_signals: [] }
      case 'OPTIONS': return { items: [1, 2, 3].map(i => ({ id: `O${i}`, title: `${o.label} option ${i}`, summary: 's', root_link: 'none', compute_open: i === 3 ? 'settled: known https://x' : 'samples https://x',
        sequential: i === 2 ? ' None: independent runs' : 'each step waits on the last', source_urls: [] })) }
      case 'OPTION_SCORES': return { items: prompt.a[2].map(x => ({ id: x.id, distance: 'SAME', distance_reason: 'same subject here', scores: OC[prompt.a[1]].map(c => ({ criterion: c, value: x.id === 'O1' ? 5 : 3, reason: 'a reason long enough' })) })) }
      case 'DEDUP': return { clusters: prompt.a[0].map(l => ({ topic: 'a topic here', members: [l.split(': ')[0]] })) }
      case 'PLAN': return plan(prompt.a[0].optionRecord.title)
      case 'REPAIR_EXPR': return { numbers: [{ id: 'n1', expr: '2*3' }], lines: [] }
      case 'REPAIR_FIELDS': return { fields: Object.fromEntries(Object.entries(prompt.a[0]).map(([k, v]) => [k, v.replace(/W11( at \d+)?/, 'the ensemble')])) }
      case 'FINDINGS': return { items: prompt.a[0].map(i => ({ ref: i.ref, status: 'SUPPORTED', page_quote: 'a page quote', note: '' })) }
      case 'CRITIQUE': return { scores: [], decides_by: 'P1', decides_by_reason: 'r' }
    }
    throw new Error(`no reply for ${o.schema}`)
  }
  function world(over = {}) {
    const calls = [], logs = [], ctxs = [], picks = []
    const s = {
      calls, logs, ctxs, picks,
      log: m => logs.push(m), parallel: thunks => thunks.map(t => t()), pipeline: () => { throw new Error('unused') },
      agent: (prompt, o) => { calls.push({ prompt, o }); const r = over.agent && over.agent(prompt, o); return r !== undefined ? r : reply(prompt, o) },
      EX1_TEXT: 'ex1', EX2_TEXT: 'ex2', P_PLAYWRIGHT: () => 'playwright', P_GUEST: () => 'guest', P_REASK: roots => `reask ${roots.map(r => r.id)}`,
      CRIT_OPTION: b => b, CRIT_CARD: b => b,
      cost_selftest: ok, pick_selftest: ok, gate_selftest: ok, render_selftest: ok,
      gate_opt: () => ({ ok: true, errors: [] }),
      gate_oc: (items, options) => ({ ok: options.every(x => items.some(i => i.id === x.id)), errors: ['missing id'], degenerate: [] }),
      gate_totals: scored => Object.fromEntries(scored.map(x => [x.id, x.scores.reduce((t, c) => t + (c.criterion === 'reshape' ? 0 : c.value), 0)])),
      gate_dedup: () => ({ ok: true, errors: [], soft: [] }), gate_dedup_jaccard: () => ({ ok: true, violations: [] }), dedup_best: () => null, dedup_handles: opts => ({ lines: opts.map(o => ({ handle: o.key, option: o })), toKey: new Map() }), dedup_unhandle: c => c,
      gate_overlap: () => ({ ok: true, errors: [] }), gate_price_sheet: () => ({ ok: true, errors: [] }),
      cost_eval_plan: () => ({ ok: true, errors: [], planned: 144, flags: [] }),
      cost_load_bearing: () => ({ ids: ['n1', 'g1'], uncertain: ['g1'] }),
      gate_plan: () => ({ action: 'ok', reasons: [], annotations: ['an annotation'] }),
      gate_cardfields: p => { const failing = ['question', 'hypothesis'].filter(f => /W11/.test(p[f])).map(field => ({ field, reasons: ['record id'] })); return { ok: !failing.length, failing, annotations: [] } },
      gate_number_preservation: (a, b) => (a.match(/\b\d+/g) || []).every(n => b.includes(n)),
      gate_findings: () => ({ ok: true, errors: [], degenerate: [] }),
      gate_core_refs: () => ['card:question', 'card:hypothesis', 'card:anchor', 'src:s1'],
      gate_decision: items => { const blocking = items.filter(i => i.status !== 'SUPPORTED'); return { result: blocking.length ? 'REJECT' : 'PASS', blocking, listed: [] } },
      gate_critique: () => ({ ok: true, errors: [] }),
      gate_dramaturg_items,   // the real shared builder (integration fix 8); it reads the real cost and gates helpers
      gate_restructured,
      txt_words: t => String(t).split(/\s+/).filter(Boolean).length,
      txt_normalize_title: t => t.toLowerCase().replace(/[^a-z0-9 ]/g, '').trim(),
      pick_hashStr: x => { let h = 2166136261; for (const ch of x) { h ^= ch.charCodeAt(0); h = Math.imul(h, 16777619) } return h >>> 0 },
      pick_u: (seed, key) => s.pick_hashStr(`${seed}:${key}`) / 4294967296,
      pick_run: input => {
        for (const b of input.branches) for (const x of b.options) assert.deepEqual(Object.keys(x), ['key', 'id', 'title', 'total', 'scores', 'distance', 'compute_open_status', 'sequential_status', 'compute_open'])
        for (const b of input.branches) {
          const [top, rnd] = [...b.options].sort((x, y) => y.total - x.total)
          picks.push({ key: top.key, root: b.root, branch: b.branch, kind: 'top', rank: 1, total: top.total }, { key: rnd.key, root: b.root, branch: b.branch, kind: 'random', rank: 2, total: rnd.total })
        }
        for (const x of input.seed_ideas) picks.push({ key: x.key, root: 'seed', branch: 'idea', kind: 'seed' })
        return { picks, frontier: [], inventory: [], log: ['pick: stub'] }
      },
      render_card: c => {
        for (const k of ['pick', 'option', 'root_question', 'plan', 'eval', 'given', 'findings', 'decision', 'critique', 'beyond_prior', 'annotations', 'halted']) assert.ok(k in c, `ctx lacks ${k}`)
        ctxs.push(c)
        return `card ${c.pick.key}: ${outcome(c)}`
      },
      render_table: rows => rows.map(r => `${r.pick.key} ${outcome(r)}`).join('\n'),
      render_inventory: () => 'inventory', render_frontier: () => 'frontier', render_result: x => `RESULT ${JSON.stringify(x.header_counts)}`,
    }
    for (const n of USED) if (n.startsWith('P_') && !(n in s)) s[n] = (...a) => ({ p: n, a })
    for (const n of USED) if (n.startsWith('SCHEMA_')) s[n] = n.slice(7)
    return Object.assign(s, over.stubs)
  }
  function run(args, w) {
    const names = ['agent', 'parallel', 'pipeline', 'log', ...USED]
    assert.deepEqual(names.filter(n => !(n in w)), [], 'stubs missing')
    return Function('args', ...names, SYNC)(args, ...names.map(n => w[n]))
  }
  const byLabel = (w, re) => w.calls.filter(c => re.test(c.o.label))
  const ctx = (w, key) => w.ctxs.find(c => c.pick.key === key)

  test('main: missing seed or base, or a failing self-test, returns {error} before any agent', () => {
    for (const a of [{ base: '/b' }, { seed: 1 }, { seed: 'x', base: '/b' }, 'not json']) {
      const w = world()
      assert.ok(run(a, w).error)
      assert.equal(w.calls.length, 0)
    }
    const w = world({ stubs: { gate_selftest: () => ({ ok: false, failures: ['case 3'] }) } })
    const r = run({ seed: 1, base: '/b' }, w)
    assert.deepEqual(r.failures, ['gates: case 3'])
    assert.equal(w.calls.length, 0)
  })

  test('main: fixed roots, every pick a row, call options, paths, what the critic and dramaturg see', () => {
    const w = world()
    const r = run(JSON.stringify({ seed: 7, base: '/b', fixed_roots: ['root a', 'root b'], seed_ideas: ['idea one'] }), w)
    assert.deepEqual(Object.keys(r), ['table', 'cards', 'inventory', 'frontier', 'log', 'result_md', 'price_sheet'])   // price_sheet: integration fix 4
    assert.equal(byLabel(w, /^roots:/).length, 0)
    assert.equal(r.cards.length, 9)
    assert.equal(w.picks.length, 9)
    for (const c of w.ctxs) assert.equal(outcome(c), 'PASS / PASS')
    assert.equal(ctx(w, 'R1:physical:O1').n_options, 3)
    const SONNET = /price-sheet|dedup|overlap|repair|critic$/
    for (const { o } of w.calls) {
      assert.ok(o.label && PHASES.includes(o.phase) && ROLES.includes(o.agentType) && o.schema, JSON.stringify(o))
      assert.equal(o.model, SONNET.test(o.label) && !/option-critic/.test(o.label) ? 'sonnet' : undefined, o.label)
    }
    for (const c of byLabel(w, /^(R\d|seed):/)) if (/:(producer|dramaturg|critic)/.test(c.o.label)) assert.equal(c.o.label.split(':').length, 4, c.o.label)
    const hash8 = id => w.pick_hashStr(id).toString(16).padStart(8, '0')
    const prod = byLabel(w, /^R1:physical:top:producer$/)[0].prompt.a[0]
    assert.equal(prod.path, `/b/seed-7/R1/physical/${hash8('O1')}/producer.md`)
    assert.equal(prod.branchPath, '/b/seed-7/R1/physical-deepener.md')
    assert.equal(prod.framerPath, '/b/seed-7/R1/framer.md')
    assert.deepEqual(Object.keys(prod.optionRecord), ['id', 'title', 'summary', 'root_link', 'compute_open', 'sequential', 'source_urls'])
    assert.equal(byLabel(w, /^seed:idea:seed:producer$/)[0].prompt.a[0].path, `/b/seed-7/seed/idea/${hash8('1')}/producer.md`)
    // settled O3: open floored to 1; O2's sequential " None: ..." floors reshape to 1, after which pick_run gets status none
    assert.ok(r.log.some(l => /R1:physical:O3: compute_open settled; open 3 -> 1/.test(l)))
    assert.ok(r.log.some(l => /R1:physical:O2: sequential none; reshape 3 -> 1/.test(l)) && !r.log.some(l => /O[13]: sequential none/.test(l)))
    // the option critic gets every option's sequential text; totals leave reshape out (O1: stakes 5 + open 5)
    assert.ok(byLabel(w, /^R1:physical:option-critic$/)[0].prompt.a[2].every(x => typeof x.sequential === 'string'))
    assert.equal(ctx(w, 'R1:physical:O1').option.total, 10)
    const [root, option, card, fields] = byLabel(w, /^R1:physical:top:critic$/)[0].prompt.a
    assert.equal(root, 'root a')
    assert.ok(!('distance' in option) && !('scores' in option))
    assert.ok(card.startsWith('card:question: Does the error'))
    assert.ok(card.includes('\ncard:method: none\n'), 'the critic reads method none (baseline NA)')
    for (const k of ['cost', 'full_scale', 'compute_tested', 'compute_tested_why', 'files_read']) assert.ok(!(k in fields), k)
    assert.ok(!('expected' in fields.predictions) && !('decides' in fields.novelty) && !('searched' in fields.novelty))
    const items = byLabel(w, /^R1:physical:top:dramaturg$/)[0].prompt.a[0]
    const refs = items.map(i => i.ref)
    // integration fix 8: items come from the shared gate_dramaturg_items, which reads the real gate_core_refs (not this
    // world's stub), so src:s2 (cited by card:question and the anchor) is a core source item too
    assert.deepEqual(refs.filter(x => !x.startsWith('card:')), ['src:s1', 'src:s2', 'num:n1', 'num:f1'])
    assert.ok(!refs.includes('card:sequential_part') && !refs.includes('card:method'), 'not restructured: no restructuring items')
    assert.deepEqual(items.find(i => i.ref === 'card:question').sources.map(x => x.id), ['s1', 's2'])
    assert.equal(items.find(i => i.ref === 'card:anchor').value, 3.1)
    assert.equal(byLabel(w, /dramaturg-2$/).length, 9)
    assert.equal(ctx(w, 'R1:physical:O1').beyond_prior, true)
  })

  test('main: halts, repairs, fallbacks and re-keys each leave a row and a log line', () => {
    const tagOf = o => o.label.split(':').slice(0, 3).join(':')
    const w = world({
      agent: (prompt, o) => {
        const t = tagOf(o)
        if (o.schema === 'PRICE_SHEET') return null
        if (/^R1:physical:option-critic/.test(o.label)) return null
        if (t === 'R1:physical:top' && o.schema === 'PLAN') return null
        if (t === 'R2:interp:random' && /producer/.test(o.label)) return null
        if (t === 'R2:interp:random' && /extract/.test(o.label)) return plan('R2:interp:interp option 2')
        if (t === 'R1:physical:random' && o.label.endsWith(':dramaturg')) return { items: prompt.a[0].map(i => ({ ref: i.ref, status: i.ref === 'card:question' ? 'CONTRADICTED' : 'SUPPORTED', page_quote: 'a page quote', note: 'the page says otherwise' })) }
        if (o.schema !== 'PLAN') return undefined
        const p = reply(prompt, o)
        if (t === 'R1:interp:random') p.novelty.decides = 'yes'
        if (t === 'R2:physical:top') p.option_title = 'R2:physical:deepener option 3'
        if (t === 'R2:physical:random') p.option_title = 'R2:physical:deepener option 1'
        if (t === 'R2:interp:top') Object.assign(p, { question: 'Does W11 have 64 members?', hypothesis: 'W11 at 8 wins.' })
        return p
      },
      stubs: { gate_plan: (p, ev, pick) => ({ action: pick.key === 'R1:interp:O1' ? 'repair' : 'ok', reasons: ['undefined id x'], annotations: [] }) },
    })
    const r = run({ seed: 3, base: '/b', fixed_roots: ['a', 'b'] }, w)
    assert.equal(r.cards.length, 8)
    const res = Object.fromEntries(w.ctxs.map(c => [c.pick.key, outcome(c)]))
    assert.deepEqual(res, {
      'R1:physical:O1': 'halted: schema', 'R1:physical:O2': 'REJECT / PASS',
      'R1:interp:O1': 'halted: cost record broken', 'R1:interp:O2': 'not judged',
      'R2:physical:O3': 'PASS / PASS', 'R2:physical:O2': 'halted: handoff mismatch',
      'R2:interp:O1': 'PASS / PASS', 'R2:interp:O2': 'PASS / PASS',
    })
    // option critic null twice: ADJACENT, scores 1
    assert.equal(byLabel(w, /^R1:physical:option-critic/).length, 2)
    assert.equal(ctx(w, 'R1:physical:O2').option.distance, 'ADJACENT')
    assert.ok(r.log.some(l => /R1:physical: option critic failed twice/.test(l)))
    // price sheet failed: no sheet for producers, rates go to the dramaturg
    assert.equal(byLabel(w, /^run:price-sheet/).length, 2)
    assert.equal(byLabel(w, /^R2:interp:top:producer$/)[0].prompt.a[0].priceSheetText, null)
    assert.ok(byLabel(w, /^R2:interp:top:dramaturg$/)[0].prompt.a[0].some(i => i.ref === 'rate:r1'))
    // extract fallback, one repair call, no judges on halts or decides = yes
    assert.equal(byLabel(w, /extract$/).length, 2)
    assert.equal(byLabel(w, /^R1:interp:top:repair-expr$/).length, 1)
    for (const t of ['R1:physical:top', 'R1:interp:top', 'R1:interp:random', 'R2:physical:random']) assert.equal(byLabel(w, new RegExp(`^${t}:(dramaturg|critic)`)).length, 0, t)
    assert.ok(ctx(w, 'R1:interp:O2').annotations.some(a => /prior already decides/.test(a)))
    // re-key: annotated, and the option record follows the plan
    assert.equal(ctx(w, 'R2:physical:O3').option.id, 'O3')
    assert.ok(r.log.some(l => /re-keyed from R2:physical:O1 to R2:physical:O3/.test(l)))
    // field repair: kept when every number survives, original kept otherwise
    const fixed = ctx(w, 'R2:interp:O1')
    assert.equal(fixed.plan.question, 'Does the ensemble have 64 members?')
    assert.equal(fixed.plan.hypothesis, 'W11 at 8 wins.')
    assert.ok(fixed.annotations.some(a => /hypothesis: the field repair dropped a number/.test(a)))
    assert.ok(fixed.annotations.some(a => /card field hypothesis still fails/.test(a)))
    for (const c of w.ctxs) if (c.halted) assert.ok(r.log.some(l => l.includes(`halted at ${c.halted.gate}`)))
  })

  test('main: integration fixes: producer_path, framer signals to the DEEPENER, case-17 and prose annotations, unconfirmed num: shown as GUESS, u3, price_sheet', () => {
    const tagOf = o => o.label.split(':').slice(0, 3).join(':')
    const rendered = {}, plans = {}
    const LONG = `head\n\n**Question.** ${'word '.repeat(241)}\n\n*Cost.* ${'x '.repeat(50)}\n\n**Judges.** j`
    const w = world({
      agent: (prompt, o) => {
        const t = tagOf(o)
        if (o.schema === 'VERDICT') return { verdict: 'NOT COMPUTE-BOUND', compute_signals: [{ subproblem: 'ensemble size', what_compute_buys: 'more members' }] }
        if (o.schema === 'PLAN') { const p = plans[t] = reply(prompt, o); if (t === 'R1:interp:top') p.compute_tested = 'no'; return p }
        if (o.schema === 'FINDINGS' && t === 'R1:physical:random') return { items: prompt.a[0].map(i => ({ ref: i.ref, status: i.ref === 'num:n1' ? 'UNREACHABLE' : 'SUPPORTED', page_quote: 'a page quote', note: 'did not load' })) }
        if (o.schema === 'CRITIQUE' && t === 'R1:physical:top') return { scores: [{ criterion: 'lever', value: 4, ref: 'card:question', reason: 'r' }], decides_by: 'none', decides_by_reason: 'r' }
        return undefined
      },
      stubs: { render_card: c => { rendered[c.pick.key] = c; return c.pick.key === 'R1:interp:O2' ? LONG : `card ${c.pick.key}` } },
    })
    const r = run({ seed: 7, base: '/b', fixed_roots: ['root a'], deepen_on_signal: true }, w)
    const hash8 = id => w.pick_hashStr(id).toString(16).padStart(8, '0')
    // 1: the producer link is producer_path, the one name render reads
    assert.equal(rendered['R1:physical:O1'].producer_path, `/b/seed-7/R1/physical/${hash8('O1')}/producer.md`)
    assert.ok(!('path' in rendered['R1:physical:O1']))
    // 9: NOT COMPUTE-BOUND with signals and deepen_on_signal -> DEEPENER, with the signals on one line
    assert.ok(String(byLabel(w, /^R1:physical:deepener$/)[0].prompt).endsWith('\nSignals from the framer: ensemble size: more members'))
    // 5: case 17, and prose over 240 words (header and script lines not counted)
    assert.ok(rendered['R1:physical:O1'].annotations.includes('inconsistent: decides_by none with lever ≥ 4'))
    assert.ok(rendered['R1:interp:O2'].annotations.includes('prose over 240 words (242)'))
    assert.ok(!rendered['R1:physical:O2'].annotations.some(a => /prose over/.test(a)))
    // 7: render gets a copy with the unconfirmed num: as a GUESS; the record keeps the producer's CITED number
    assert.deepEqual(rendered['R1:physical:O2'].plan.numbers.find(n => n.id === 'n1'), { id: 'n1', basis: 'GUESS', value: 6, rests_on: 'citation not confirmed: UNREACHABLE' })
    assert.equal(plans['R1:physical:random'].numbers.find(n => n.id === 'n1').basis, 'CITED')
    assert.equal(rendered['R1:physical:O1'].plan, plans['R1:physical:top'])
    // 3, 4: u3 counts PASS cards whose test varies compute (R1:interp:O1 says compute_tested no); price_sheet returned
    assert.ok(r.result_md.includes('"pass":3') && r.result_md.includes('"u3":2'), r.result_md)
    assert.deepEqual(r.price_sheet, { read_at: '2026-10-16', instances: [], filesystem: {} })
  })

  test('main: a restructured plan sends sequential_part (core) and method to the dramaturg, gets 40 more prose words, and counts toward u4', () => {
    const tagOf = o => o.label.split(':').slice(0, 3).join(':')
    const rendered = {}
    const LONG = n => `head\n\n**Question.** ${'word '.repeat(n)}\n\n*Cost.* x\n\n**Judges.** j`
    const w = world({
      agent: (prompt, o) => {
        const t = tagOf(o)
        if (o.schema === 'PLAN') { const p = reply(prompt, o); if (t.startsWith('R1:physical')) p.restructuring = { sequential_part: 'Each of 64 steps waits on the last [s1].', method: 'Steps combine in rounds.' }; return p }
        if (o.schema === 'CRITIQUE') return { scores: [{ criterion: 'reshape', value: t === 'R1:interp:top' ? 3 : 4, ref: 'card:method', reason: 'r' }, { criterion: 'baseline', value: t === 'R1:physical:random' ? 'NA' : 3, ref: 'card:test_summary', reason: 'r' }], decides_by: 'P1', decides_by_reason: 'r' }
        return undefined
      },
      stubs: { render_card: c => { rendered[c.pick.key] = c; return c.pick.root === 'R1' ? LONG(c.pick.branch === 'physical' ? 270 : 250) : `card ${c.pick.key}` } },
    })
    const r = run({ seed: 7, base: '/b', fixed_roots: ['root a'] }, w)
    const items = byLabel(w, /^R1:physical:top:dramaturg$/)[0].prompt.a[0]
    assert.deepEqual(items.slice(0, 4).map(i => i.ref), ['card:question', 'card:hypothesis', 'card:sequential_part', 'card:method'])
    assert.ok(byLabel(w, /^R1:interp:top:dramaturg$/)[0].prompt.a[0].every(i => !/sequential_part|method/.test(i.ref)))
    // prose: 270 words pass on a restructured card (max 280), 250 do not on another (max 240)
    assert.ok(!rendered['R1:physical:O1'].annotations.some(a => /prose over/.test(a)))
    assert.ok(rendered['R1:interp:O1'].annotations.includes('prose over 240 words (251)'))
    // u4: PASS cards with critic reshape >= 4 and baseline >= 3, one per cluster: R1:physical:O1 and R1:interp:O2
    assert.ok(r.result_md.includes('"u4":2'), r.result_md)
  })

  test('main: only the 2 REJECTs lowest in recheck order get a second dramaturg', () => {
    const w = world({ agent: (prompt, o) => (o.schema === 'FINDINGS' ? { items: prompt.a[0].map(i => ({ ref: i.ref, status: 'UNSUPPORTED', page_quote: '', note: 'not on the page' })) } : undefined) })
    run({ seed: 5, base: '/b', fixed_roots: ['a', 'b', 'c'] }, w)
    const second = byLabel(w, /dramaturg-2$/).map(c => c.o.label.split(':').slice(0, 3).join(':'))
    const order = w.ctxs.map(c => c.pick.key).sort((x, y) => w.pick_u(5, `recheck:${x}`) - w.pick_u(5, `recheck:${y}`)).slice(0, 2)
    assert.deepEqual(second.sort(), order.map(k => w.ctxs.find(c => c.pick.key === k).tag).sort())
  })

  test('main: generated roots; overlap re-asks the later root\'s generator and its first question replaces it', () => {
    const w = world({ agent: (prompt, o) => (o.schema === 'OVERLAP' ? { pairs: [{ a: 'R5', b: 'R2', shared_subject: 'same subject matter' }] } : undefined) })
    run({ seed: 1, base: '/b' }, w)
    assert.deepEqual(byLabel(w, /^roots:/).map(c => c.o.label).sort(), ['roots:guest', 'roots:guest:reask', 'roots:overlap', 'roots:playwright'])
    assert.equal(byLabel(w, /^roots:guest:reask$/)[0].prompt, 'guest reask R1,R2,R3,R4')
    const framed = Object.fromEntries(byLabel(w, /:framer$/).map(c => [c.o.label.split(':')[0], c.prompt.a[0]]))
    assert.deepEqual(framed, { R1: 'ex2', R2: 'roots:playwright q1', R3: 'roots:playwright q2', R4: 'roots:guest q1', R5: 'roots:guest:reask q1' })
  })
})()
