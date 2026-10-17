// cost.js against the design round's six hand encodings (expected figures: cost.md §2) and CONTRACT.md §2.5 / §3.
//
// Fixture conversions: tests/fixtures/cost/pNN.json were made from
// scratchpad/meta/synthesis/cost-sim/pNN.json (the encodings predate the contract):
//  1. all six: numbers[].source -> numbers[].source_id.
//  2. all six: top-level "pick" -> option_title (label text kept).
//  3. all six: rates[].instance dropped; GPU memory moved into gpu_memory_gb and stripped from gpu
//     ("8x H100 SXM 80GB" -> gpu "H100 SXM", 80; "A100 SXM 40GB" -> "A100 SXM", 40; "A100 SXM 80GB" -> "A100 SXM", 80).
//  4. all six: lines[].kind mapped to the contract enum: "lambda_other" storage lines (p03 st, p05 fs, p10 st, p18 fs) -> "storage";
//     "lambda_other" dollar lines (p05 p4s, p10 chaos) and "contingency" (p16 cont) -> "allotment"; missing kind -> "work".
//  5. p18: the producer's stop_rule "config A only if >= 13 samples/s per H100" written as phases[G23].gate
//     {on: samples_per_s, op: '>=', value: 13, else: 'use config B'}, with a new DERIVED number
//     samples_per_s = h100_dense * util / flop_sample (gates did not exist when the encoding was written).
//  6. p06: stop_rule "if < 3,500 steps/A100-h: ..." written as phases[P0].gate {on: sph, op: '>=', value: 3500, else: ...}.
//  7. p05: full_scale "record" gets ratio_to: 'usd_per_tl' (cost.md §2.3 states that multiple against the 1024^3 cost per T_L).
//  8. p03, p05, p18 (integration): the PROXY number fs_rate (Lambda's example filesystem price, no measuring phase) is removed
//     and its uses read the reserved GIVEN id fs_usd_gib_month from the price sheet (CONTRACT §2.5), so the
//     "no phase measures it" flag on the example price is gone. p10 keeps its fs_rate, which names a measuring phase.
//  Kept as written: p03 dense_frac is CITED 0.5 with quote "With sparsity"; cost.js reports it as a quote error (a transform is DERIVED).
//  price_sheet.json lists exactly the instances the encodings use, at the encodings' prices (a fixture, not a page read).
// The converter is scratchpad/costwork/convert.js (not part of the build).
;(() => {
  // text.js is owned by another agent and may be absent here; cost_check_quotes needs txt_norm_number
  if (typeof txt_norm_number !== 'function') globalThis.txt_norm_number = (s) => String(s).replace(/,/g, '').replace(/−/g, '-').trim()

  // fixture() parses in the runner's realm; re-parse here so arrays compare by deepEqual with literals in this file
  const local = (x) => JSON.parse(JSON.stringify(x))
  const SHEET = local(fixture('cost/price_sheet.json'))
  const GIVEN = { budget_usd: 1000, price_sheet: SHEET, budget_covers_storage: true, budget_covers_tax: false }
  const load = (f) => local(fixture(`cost/${f}.json`))
  const ev = (f, opts, given) => cost_eval_plan(typeof f === 'string' ? load(f) : f, given || GIVEN, opts)
  const near = (x, y, tol, what) => assert.ok(typeof x === 'number' && Math.abs(x - y) <= tol, `${what}: ${x} not within ${tol} of ${y}`)
  const unc = (e, id) => e.uncertain.find((u) => u.id === id)
  const line = (e, id) => e.lines.find((l) => l.id === id)
  const SIX = ['p03', 'p05', 'p06', 'p10', 'p16', 'p18']
  const R1 = { id: 'r1', gpu: 'H100 SXM', gpu_memory_gb: 80, n_gpus: 1, per_gpu_usd_h: 4.29 }
  const minimal = () => ({
    phases: [{ id: 'P0', what: 'setup' }, { id: 'P1', what: 'runs' }],
    cost: { rates: [R1], lines: [{ id: 'a', phase: 'P0', what: 'setup', kind: 'work', rate: 'r1', hours: '2' }, { id: 'b', phase: 'P1', what: 'runs', kind: 'work', rate: 'r1', hours: '10' }], total_stated: 51.48 },
  })

  // ---------- grammar ----------
  test('cost: grammar evaluates operators, precedence and the five functions', () => {
    const v = (s) => cost_ev(cost_parse(s), (id) => ({ a: 2, B_1: 3 })[id])
    assert.equal(v('2 + 3 * 4'), 14)
    assert.equal(v('2 ^ 3 ^ 2'), 512) // right-associative
    assert.equal(v('-2 ^ 2'), -4)
    assert.equal(v('(1 + 2) * 3 - 4 / 2'), 7)
    assert.equal(v('ceil(2.5) + floor(2.5) + min(3, 1, 2) + max(1, 4) + pow(2, 10)'), 1034)
    assert.equal(v('1e3 / 4 + .5 * 4 + 2.5e-1'), 252.25)
    assert.equal(v('a * B_1 - -1'), 7)
    assert.equal(v(' 7 '), 7)
  })

  test('cost: grammar rejects anything outside the contract with kind parse', () => {
    for (const s of ['2 ** 3', 'sqrt(4)', 'pow(2)', 'ceil(1, 2)', 'a +', '', '   ', '3 $ 4', 'a b', '(1 + 2', '1 + 2)', 'min()', '2 % 3', 'a.b']) {
      assert.throws(() => cost_parse(s), (e) => e.kind === 'parse' && typeof e.msg === 'string', s)
    }
  })

  test('cost: expression ids resolve to numbers, rates ($/h), lines ($) and budget_usd', () => {
    const p = minimal()
    p.numbers = [{ id: 'x', name: 'x', unit: '1', basis: 'DESIGN', value: 2 }, { id: 'd', name: 'd', unit: 'usd', basis: 'DERIVED', expr: 'x * r1 + a + budget_usd' }]
    near(ev(p).numbers.d, 2 * 4.29 + 2 * 4.29 + 1000, 1e-9, 'd')
  })

  test('cost: literals outside the contract list are logged as unlabelled constants', () => {
    const p = minimal()
    p.numbers = [{ id: 'd', name: 'd', unit: '1', basis: 'DERIVED', expr: '3600 * 1024 * 0.5 * 1e9 * 37 / 2.5' }]
    const log = ev(p).log.filter((x) => x.startsWith('unlabelled constant'))
    assert.deepEqual(log, ['unlabelled constant 37 in numbers.d.expr', 'unlabelled constant 2.5 in numbers.d.expr'])
  })

  // ---------- the six encodings (cost.md §2) ----------
  test('cost: p10 reproduces planned $684.14, no-compaction $6,119, model wall 10.72 h', () => {
    const e = ev('p10')
    assert.ok(e.ok, JSON.stringify(e.errors))
    near(e.planned, 684.14, 0.005, 'planned')
    near(e.numbers.model_wall, 10.72, 0.005, 'model wall')
    assert.equal(Math.round(e.full_scale.find((f) => f.id === 'nocomp').usd), 6119)
    near(e.scenarios[0].total, 1327.83, 0.005, '3x scenario, nothing cut')
    near(line(e, 'p1').margin, 1.12, 0.005, 'P1 box margin')
    near(unc(e, 't_m').k_box, 1.21, 0.005, 't_m box')
    near(unc(e, 't_m').k_budget, 2.61, 0.005, 't_m cap')
    near(unc(e, 't_0').k_box, 1.27, 0.005, 't_0 box')
    near(unc(e, 't_0').k_budget, 3.02, 0.005, 't_0 cap')
    near(unc(e, 't_m').cum_spend_through_measured_by, 25.74, 0.005, 'P0b spend')
    assert.deepEqual(e.flags, [])
  })

  test('cost: p03 reproduces core $440.23 and with options $599.83; its GUESSes reach spend only through need', () => {
    const e = ev('p03')
    near(e.planned, 440.23, 0.005, 'core')
    near(e.planned_with_options, 599.83, 0.005, 'with options')
    near(line(e, 'B2').need_h, 1.13, 0.005, '70B generation need')
    near(line(e, 'B2').margin, 1.76, 0.005, 'B2 margin')
    near(unc(e, 'eff_prefill').k_box, 2.3, 0.005, 'prefill efficiency box')
    assert.deepEqual(e.alternatives.map((a) => [a.line_id, Math.round(a.total * 100) / 100]), [['alt_A_on_8x', 616.48]])
    assert.deepEqual(cost_load_bearing(load('p03')).uncertain.sort(), ['eff_prefill', 'hbm_frac', 'tok_in'])   // fs_rate became fs_usd_gib_month (conversion 8)
    // the encoding's CITED 0.5 "With sparsity" is a transform of the page, so it is a quote error; evaluation still runs
    assert.deepEqual(e.errors.map((x) => [x.kind, x.where]), [['quote', 'numbers.dense_frac.quote']])
    assert.equal(e.ok, false)
  })

  test('cost: p05 reproduces planned $318.80, pessimistic $510.43, record turnover 51,545x the 1024^3 cost', () => {
    const e = ev('p05')
    near(e.planned, 318.8, 0.005, 'planned')
    near(e.scenarios.find((s) => s.id === 'pess').total, 510.43, 0.005, 'pessimistic')
    const rec = e.full_scale.find((f) => f.id === 'record')
    assert.equal(Math.round(rec.ratio_to_value), 51545)
    assert.equal(Math.round(rec.multiple_of_budget), 909)
    near(e.numbers.s_step_model, 0.134, 0.0005, 'modelled step')
    near(e.numbers.usd_per_tl, 17.64, 0.005, '$ per T_L')
    near(unc(e, 's_step').k_budget, 8.11, 0.005, 'step-time headroom')
    near(unc(e, 's_step').cum_spend_through_measured_by, 135.4, 0.005, 'spend through P2')
    assert.ok(!cost_load_bearing(load('p05')).ids.includes('cost_exp'), 'a GUESS used only in full_scale is not load-bearing')
  })

  test('cost: p06 reproduces planned $557.20, scenarios $676.60 / $761.89 / $875.60, k_budget 1.93', () => {
    const e = ev('p06')
    assert.ok(e.ok, JSON.stringify(e.errors))
    near(e.planned, 557.2, 0.005, 'planned')
    assert.deepEqual(e.scenarios.map((s) => Math.round(s.total * 100) / 100), [676.6, 761.89, 875.6])
    near(unc(e, 'lr_steps').k_budget, 1.93, 0.005, 'k_budget')
    assert.equal(unc(e, 'lr_steps').dir, 'lower')
    near(unc(e, 'c_full').k_budget, 6.56, 0.005, 'full fine-tune headroom')
    const g = e.gates[0]
    assert.equal(g.passes, true)
    near(g.uncut_total_at_threshold, 761.89, 0.005, 'uncut plan at the gate')
    assert.equal(Math.round(e.full_scale.find((f) => f.id === 'fs_wm_arm').usd), 3942)
    assert.equal(Math.round(e.full_scale.find((f) => f.id === 'fs_cosmos').multiple_of_budget), 86184)
    assert.deepEqual(e.flags, [])
  })

  test('cost: p16 reproduces core $276.08, ceiling $612.70, P2 margin 0.99', () => {
    const e = ev('p16')
    near(e.planned, 276.08, 0.005, 'core')
    near(e.planned_with_options, 612.7, 0.005, 'ceiling')
    assert.equal(line(e, 'p2').margin.toFixed(2), '0.99')
    assert.equal(unc(e, 'tps_gpu').k_box, 1) // the box is already short of its need
  })

  test('cost: p18 reproduces planned $834.46, GraphCast $69,243 = 69.2x, yields 274K / 822K, gate failing at base', () => {
    const e = ev('p18')
    near(e.planned, 834.46, 0.005, 'planned')
    const gc = e.full_scale.find((f) => f.id === 'graphcast')
    assert.equal(Math.round(gc.usd), 69243)
    assert.equal(gc.multiple_of_budget.toFixed(1), '69.2')
    const y = e.yields.find((x) => x.id === 'samples_per_run')
    assert.equal(Math.round(y.base / 1000), 274)
    assert.equal(Math.round(y.by_scenario.u15 / 1000), 822)
    const g = e.gates[0]
    assert.deepEqual([g.phase, g.on, g.op, g.value, g.passes], ['G23', 'samples_per_s', '>=', 13, false])
    assert.ok(e.flags.some((f) => f.startsWith('gate in G23 fails')))
    assert.equal(ev('p18', { scenario: 'u15' }).gates[0].passes, false) // fails across the producer's whole range
    near(unc(e, 'util').cum_spend_through_measured_by, 38.05, 0.005, 'spend through G23')
    assert.equal(unc(e, 'util').k_budget, null)
    near(e.alternatives[0].total, 827.26, 0.005, '8x A100 fallback')
    const lb = cost_load_bearing(load('p18'))
    assert.ok(lb.uncertain.includes('util') && !lb.ids.includes('device_is_chip'))
  })

  // ---------- errors and flags ----------
  test('cost: structural errors carry the contract kinds and stop evaluation', () => {
    const kinds = (p) => ev(p).errors.map((x) => x.kind)
    let p = minimal(); p.numbers = [{ id: 'a1', name: 'a', unit: '1', basis: 'DERIVED', expr: 'b1 + 1' }, { id: 'b1', name: 'b', unit: '1', basis: 'DERIVED', expr: 'a1 * 2' }]
    assert.deepEqual(kinds(p), ['cycle'])
    p = minimal(); p.numbers = [{ id: 'budget_usd', name: 'b', unit: 'usd', basis: 'DESIGN', value: 5 }]
    assert.deepEqual(kinds(p), ['reserved'])
    p = minimal(); p.numbers = [{ id: 'a', name: 'dup', unit: '1', basis: 'DESIGN', value: 5 }]
    assert.deepEqual(kinds(p), ['reserved']) // number and line share an id
    p = minimal(); p.cost.lines[0].hours = '2 +'
    assert.deepEqual(kinds(p), ['parse'])
    p = minimal(); p.cost.lines[0].rate = 'r9'
    assert.deepEqual(kinds(p), ['undefined'])
    p = minimal(); p.numbers = [{ id: 'g', name: 'g', unit: '1', basis: 'GUESS' }]
    assert.deepEqual(kinds(p), ['undefined'])
    p = minimal(); p.cost.scenarios = [{ id: 's', what: 's', set: { nope: 1 } }]
    assert.deepEqual(kinds(p), ['undefined'])
    const broken = ev(p)
    assert.equal(broken.ok, false)
    assert.equal(broken.planned, null)
  })

  test('cost: fs_usd_gib_month is a GIVEN id read from the price sheet, tagged [q]; a plan may not define it', () => {
    for (const f of ['p03', 'p05', 'p18']) assert.ok(!ev(f).flags.some((x) => /filesystem price.*no phase measures it/.test(x)), f)
    const p = minimal()
    p.cost.lines.push({ id: 'st', phase: 'P1', what: 'filesystem', kind: 'storage', usd: '100 * fs_usd_gib_month' })
    const e = ev(p)
    assert.ok(e.ok, JSON.stringify(e.errors))
    near(e.planned, 51.48 + 20, 0.005, 'planned with storage at the sheet rate')
    assert.ok(cost_render_block(e, p, GIVEN).split('\n')[2].endsWith('· filesystem $0.20/GiB-month [q]'))
    assert.ok(cost_render_derivations(e, p).includes('st.usd = 100 * fs_usd_gib_month = 100 * 0.2 = 20 usd'))
    assert.deepEqual(ev(p, {}, { ...GIVEN, price_sheet: null }).errors.map((x) => [x.kind, x.where]), [['undefined', 'lines.st.usd']])
    p.numbers = [{ id: 'fs_usd_gib_month', name: 'filesystem price', unit: 'usd/GiB-month', basis: 'GUESS', value: 0.3 }]
    assert.deepEqual(ev(p).errors.map((x) => x.kind), ['reserved'])
  })

  test('cost: a bare number where an expression is expected is read as its string', () => {
    const p = minimal()
    p.cost.lines[1].hours = 10
    p.numbers = [{ id: 'd', name: 'd', unit: 'h', basis: 'DERIVED', expr: 3 }]
    p.full_scale = [{ id: 'big', what: 'everything', usd: 5000 }]
    const e = ev(p)
    assert.ok(e.ok, JSON.stringify(e.errors))
    near(e.planned, 51.48, 0.005, 'planned')
    assert.equal(e.numbers.d, 3)
    assert.equal(e.full_scale[0].usd, 5000)
    assert.ok(cost_render_block(e, p, GIVEN).includes('Planned $51.48'))
  })

  test('cost: a gate on an undefined number is a gate_ref error; the rest still evaluates', () => {
    const p = minimal()
    p.phases[0].gate = { on: 'nope', op: '>=', value: 1, else: 'x' }
    const e = ev(p)
    assert.deepEqual(e.errors.map((x) => x.kind), ['gate_ref'])
    near(e.planned, 51.48, 0.005, 'planned')
  })

  test('cost: flags for measuring order, stated vs computed, and uncut plan over budget at a gate', () => {
    let p = load('p06'); p.numbers.find((n) => n.id === 'lr_steps').measured_by = 'EV'
    assert.ok(ev(p).flags.some((f) => f.includes('is measured in EV, after spend that depends on it starts in W1')))
    p = load('p06'); p.numbers.find((n) => n.id === 'lr_steps').measured_by = 'P9'
    assert.ok(ev(p).flags.some((f) => f.includes('measuring phase P9 is not in the plan')))
    p = load('p06'); p.cost.total_stated = 600
    assert.ok(ev(p).flags.some((f) => f.startsWith('stated total $600 differs from computed $557.20')))
    p.cost.total_stated = 560 // within max($1, 2%)
    assert.deepEqual(ev(p).flags, [])
    p = load('p06'); p.phases[0].gate.value = 2000
    assert.ok(ev(p).flags.some((f) => f.startsWith('uncut plan at the P0 gate threshold costs $1,273.60, over budget')))
  })

  test('cost: computed and stated $1,040 surfaces planned > budget (the halt condition)', () => {
    const p = minimal()
    p.cost.rates.push({ id: 'r8', gpu: 'H100 SXM', gpu_memory_gb: 80, n_gpus: 8, per_gpu_usd_h: 3.99 })
    p.cost.lines = [{ id: 'a', phase: 'P1', what: 'runs', kind: 'work', rate: 'r8', hours: '30' }, { id: 'b', phase: 'P1', what: 'reruns', kind: 'allotment', usd: '82.4' }]
    p.cost.total_stated = 1040
    const e = ev(p)
    near(e.planned, 1040, 0.005, 'planned')
    assert.ok(e.planned > GIVEN.budget_usd && p.cost.total_stated > GIVEN.budget_usd)
    assert.ok(e.flags.includes('planned spend $1,040 is over the $1,000 budget (stated $1,040)'))
    near(e.unallocated, -40, 0.005, 'unallocated')
  })

  test('cost: rates are checked against the price sheet', () => {
    let p = load('p06'); p.cost.rates[0].per_gpu_usd_h = 2.1
    let e = ev(p)
    assert.deepEqual(e.rate_corrections, [{ id: 'r_a100x8', stated: 2.1, sheet: 1.99 }])
    near(e.rates.r_a100x8, 15.92, 1e-9, 'sheet rate used')
    near(e.planned, 557.2, 0.005, 'planned at sheet price')
    assert.ok(e.flags.some((f) => f.includes('sheet price used')))
    p = load('p06'); p.cost.rates[0].gpu = 'GH200'
    e = ev(p)
    assert.ok(e.flags.some((f) => f.startsWith('rate 8x GH200 40GB at $1.99/GPU-h is not on the price sheet')))
    near(e.rates.r_a100x8, 15.92, 1e-9, 'stated price kept')
    e = ev('p06', {}, { ...GIVEN, price_sheet: null })
    assert.deepEqual(e.flags, [])
    assert.ok(e.log.includes('no price sheet given; rates not checked'))
  })

  test('cost: quotes are matched as printed, with commas and k/M multipliers normalised', () => {
    const q = (value, quote) => cost_check_quotes({ numbers: [{ id: 'x', basis: 'CITED', value, quote }] })[0]
    assert.equal(q(10000, '10,000 NVIDIA H100 GPUs').ok, true)
    assert.equal(q(20000, '20k steps will roughly take ~4 hrs').ok, true)
    assert.equal(q(4, '20k steps will roughly take ~4 hrs').ok, true)
    assert.equal(q(78, '78ms with 8 GPUs (1 node)').ok, true)
    assert.equal(q(1.3e6, 'about 1.3M tokens').ok, true)
    assert.equal(q(100, 'one H100 SXM').ok, false) // not inside a model name
    assert.equal(q(4, 'a B200 run').ok, false)
    assert.equal(q(989.5, '1,979 teraFLOPS with sparsity').ok, false) // a halved figure is DERIVED
    assert.deepEqual(q(3, undefined), { id: 'x', ok: true, msg: 'no quote given; value not checked against page text' })
    assert.deepEqual(cost_check_quotes({ numbers: [{ id: 'g', basis: 'GUESS', value: 1, quote: 'nothing' }] }), [])
  })

  test('cost: overrides and scenarios evaluate as a scenario (boxes stretch to need)', () => {
    near(ev('p06', { overrides: { sph: 3500 } }).planned, 761.89, 0.005, 'override')
    near(ev('p06', { scenario: 's3000' }).planned, 875.6, 0.005, 'scenario')
    assert.deepEqual(ev('p06', { scenario: 'nope' }).errors.map((x) => x.kind), ['undefined'])
    assert.deepEqual(ev('p06', { overrides: { wave1: 3 } }).errors.map((x) => x.kind), ['undefined']) // only number ids
    near(ev('p16', { overrides: { tps_gpu: 95 } }).planned, 276.08 + (8.114035087719298 - 4) * 31.92, 0.005, 'stretched box')
    near(ev('p16').planned, 276.08, 0.005, 'base keeps the box')
  })

  test('cost: storage lines leave the planned total when the credit does not cover storage', () => {
    near(ev('p18', {}, { ...GIVEN, budget_covers_storage: false }).planned, 834.46 - 30.33, 0.005, 'planned without storage')
  })

  test('cost: a minimal plan (rates, constant-hour lines, a total) evaluates with no flags', () => {
    const p = minimal()
    const e = ev(p)
    assert.ok(e.ok, JSON.stringify(e.errors))
    near(e.planned, 51.48, 0.005, 'planned')
    assert.deepEqual(e.flags, [])
    assert.deepEqual(e.uncertain, [])
    assert.deepEqual(e.lines.map((l) => l.time_box), [true, true])
    assert.ok(cost_render_block(e, p, GIVEN).includes('Planned $51.48 · unallocated $948.52'))
    assert.ok(cost_words(cost_render_short(e, p)) <= 45)
    assert.ok(cost_menu(e, p).some((m) => m.id === 'planned_usd' && m.value === '$51.48'))
    assert.equal(cost_render_derivations(e, p), 'Derivations: each computed number with its inputs substituted')
  })

  // ---------- rendering ----------
  const LABELS = ['Budget', 'Spend', 'Rests on', 'Scenarios', 'Buys', 'Flags', 'Full scale', 'Outside']
  test('cost: the block has the fixed section order and stays short', () => {
    for (const f of SIX) {
      const p = load(f), b = cost_render_block(ev(p), p, GIVEN), rows = b.split('\n')
      assert.ok(rows[0].startsWith('COST: computed by the pipeline'), f)
      assert.equal(rows[1], cost_LEGEND)
      const at = LABELS.map((l) => rows.findIndex((r) => r.startsWith(l.padEnd(11))))
      assert.ok(at.every((i, k) => i > 1 && (k === 0 || i > at[k - 1])), `${f}: section order ${at}`)
      assert.ok(rows.length <= 20, `${f}: ${rows.length} lines`)
      assert.ok(!/one machine|8 GPUs|max_gpus|—/.test(b), `${f}: no machine cap, no em-dash`)
    }
  })

  test('cost: block content for p06 and p18', () => {
    let p = load('p06'), b = cost_render_block(ev(p), p, GIVEN)
    for (const s of ['[q] $1,000 Lambda on-demand credit', 'prices read 2026-10-16', '8x A100 SXM 40GB 8×$1.99=$15.92/h  20 h [=]  $318.40',
      'Planned $557.20 · unallocated $442.80', 'measured in P0 ($31.84 spent by then)', '≥ 3,500', 'uncut plan at it $761.89',
      'budget reached at 10,400 (1.9× lower)', '4,000 steps/A100-h → $676.60 · 3,500 → $761.89 · 3,000 → $875.60', '$86.2M = 86,200× budget']) {
      assert.ok(b.includes(s), `p06 block lacks: ${s}`)
    }
    p = load('p18'); b = cost_render_block(ev(p), p, GIVEN)
    for (const s of ['Instead of main:', '→ plan $827.26', 'measured in G23 ($38.05 spent by then)', 'fails; uncut plan at it $834.46',
      'samples seen per GPU run in the time box: 274,000 [=] · 15% utilization: 822,000', 'Flags      gate in G23 fails',
      '$69,200 = 69.2× budget', '([g] a \'device\' is one chip)', 'write prepare/train/rollout code: 2 to 4 person-days']) {
      assert.ok(b.includes(s), `p18 block lacks: ${s}`)
    }
    p = load('p16'); b = cost_render_block(ev(p), p, GIVEN)
    assert.ok(b.includes('time box; need 4.06 h (margin 0.99×)'))
    p = load('p03'); b = cost_render_block(ev(p), p, GIVEN)
    assert.ok(b.includes('Flags      error (quote) at numbers.dense_frac.quote: 0.5 does not appear in the quote "With sparsity"'))
  })

  test('cost: Rests on shows at most 4 uncertain inputs, tightest headroom first', () => {
    const p = load('p10')
    p.numbers.find((n) => n.id === 'acc_steps').differs_in = ['workload']
    const e = ev(p), rows = cost_render_block(e, p, GIVEN).split('\n')
    const i = rows.findIndex((r) => r.startsWith('Rests on')), j = rows.findIndex((r) => r.startsWith('Scenarios'))
    assert.equal(e.uncertain.length, 5)
    assert.equal(j - i, 5)
    assert.ok(rows[i].includes('accepted steps, same run') && rows[i].includes('(2.0× higher)'), rows[i])
    assert.ok(rows[i + 1].includes('GPU s per member per RHS') && rows[i + 1].includes('(2.6× higher)'), rows[i + 1])
    assert.ok(rows[j - 1].trim().startsWith('+1 more:'))
  })

  test('cost: short form is at most 45 words', () => {
    for (const f of SIX) {
      const p = load(f), s = cost_render_short(ev(p), p)
      assert.ok(cost_words(s) <= 45, `${f}: ${cost_words(s)} words`)
      assert.ok(s.startsWith('Plans $'), f)
    }
    const p = load('p06')
    assert.equal(cost_render_short(ev(p), p), 'Plans $557.20 of the $1,000 budget over 35 machine-hours, leaving $442.80. Main guess: steps in LeRobot SmolVLA timing [p], measured after $31.84 of spend; the budget is reached if it is 1.9× lower.')
    const bad = minimal(); bad.cost.lines[0].hours = '2 +'
    assert.equal(cost_render_short(ev(bad), bad), 'The cost record did not evaluate (1 error); see the cost block.')
  })

  test('cost: menu carries the contract ids, each full-scale figure with its multiple, and axis_span', () => {
    const p = load('p06'), e = ev(p), m = cost_menu(e, p), val = (id) => (m.find((x) => x.id === id) || {}).value
    for (const x of m) assert.deepEqual(Object.keys(x), ['id', 'name', 'value', 'tag'])
    assert.equal(val('planned_usd'), '$557.20')
    assert.equal(val('planned_h'), '35')
    assert.equal(val('unallocated_usd'), '$442.80')
    assert.equal(val('pilot_cum_usd'), '$31.84')
    assert.equal(val('gate_value'), '3,500')
    assert.equal(val('headroom'), '1.9')
    assert.equal(val('fs_cosmos'), '$86.2M')
    assert.equal(val('fs_cosmos_x'), '86,200')
    assert.equal(val('fs_wm_arm'), '$3,941.58')
    assert.equal(val('fs_wm_arm_x'), '3.94')
    assert.equal(val('sph'), '5,000')
    assert.equal(val('axis_span'), undefined)
    p.compute_axis = { quantity: 'training steps', unit: 'steps', levels: [5000, 15000, 50000] }
    assert.equal(cost_menu(e, p).find((x) => x.id === 'axis_span').value, '10')
    const p5 = load('p05'), m5 = cost_menu(ev(p5), p5)
    assert.equal(m5.find((x) => x.id === 'fs_record_ratio').value, '51,500')
    const p18 = load('p18'), m18 = cost_menu(ev(p18), p18)
    assert.equal(m18.find((x) => x.id === 'samples_per_run').value, '274,000')
  })

  test('cost: derivations substitute values into every DERIVED number, id-bearing line and full-scale expression', () => {
    const p = load('p06'), d = cost_render_derivations(ev(p), p).split('\n')
    assert.ok(d.includes('sph = lr_steps / lr_hours = 20000 / 4 = 5000 steps/GPU-h'))
    assert.ok(d.includes('wave1.hours = gpuh_w1 / gpus_w1 = 160 / 8 = 20 h'))
    assert.ok(d.includes('fs_cosmos = fs_cosmos_gpus * fs_cosmos_months * 30 * 24 * h100_rate = 10000 * 3 * 30 * 24 * 3.99 = 8.6184e7 usd'))
    assert.ok(d.includes('gpuh_w1 = (s_A + s_C + s_B50 + s_Bp) / sph = (200000 + 200000 + 200000 + 200000) / 5000 = 160 GPU-h'))
  })

  // ---------- selftest, determinism, module rules ----------
  test('cost: selftest passes, and each planted case fails when its behaviour is broken', () => {
    assert.deepEqual(cost_selftest(), { ok: true, failures: [] })
    const breakFn = (name, fake, expect) => {
      const real = globalThis[name]
      globalThis[name] = fake
      try { const r = cost_selftest(); assert.ok(!r.ok && expect.every((x) => r.failures.some((f) => f.includes(x))), `${name}: ${JSON.stringify(r.failures)}`) }
      finally { globalThis[name] = real }
    }
    breakFn('cost_check_quotes', () => [], ['selftest quote:'])
    breakFn('cost_load_bearing', () => ({ ids: [], uncertain: [] }), ['selftest p06:', 'selftest need_only:', 'selftest thin:'])
    breakFn('cost_bisect', () => null, ['selftest p06:', 'selftest thin:', 'selftest need_only:'])
    breakFn('cost_parse', () => { throw { kind: 'parse', msg: 'x' } }, ['selftest minimal:', 'selftest undefined_id:'])
  })

  test('cost: evaluation is deterministic', () => {
    for (const f of SIX) assert.equal(JSON.stringify(ev(f)), JSON.stringify(ev(f)), f)
  })

  test('cost: module uses only cost_ top-level names and no forbidden constructs', () => {
    const src = fixture('../../src/cost.js')
    const FORBIDDEN = [/\bimport\s/, /\bexport\s(?!const meta)/, /\brequire\(/, /module\.exports/, /Math\.random\(/, /Date\.now\(/, /new Date\(\s*\)/, /console\.log/]
    for (const re of FORBIDDEN) assert.ok(!re.test(src), String(re))
    const names = [...src.matchAll(/^(?:function|const|let|var|class)\s+([A-Za-z_$][\w$]*)/gm)].map((m) => m[1])
    assert.ok(names.length > 10 && names.every((n) => n.startsWith('cost_')), names.filter((n) => !n.startsWith('cost_')).join(', '))
  })
})()
