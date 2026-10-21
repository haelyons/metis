// End-to-end run of idea/loop.js with stubbed model calls and stubbed card and frame scripts (no network, no model).
// Usage: node tools/e2e_loop.js [mode]   mode: ok (default) | gate | bound
//   ok     NOT COMPUTE-BOUND; one widener option passes the gate; a variant outscores it and gets a second card
//   gate   NOT COMPUTE-BOUND; every option fails the gate (settled, none, ELSEWHERE); loop ends with no card
//   bound  COMPUTE-BOUND; the deepener runs and no narrowing is required
// The same file is the stub module: loop.js loads it through LOOP_STUB.
'use strict'
const fs = require('node:fs'), path = require('node:path'), os = require('node:os'), { spawnSync } = require('node:child_process')
const MODE = process.env.LOOP_STUB_MODE || process.argv[2] || 'ok'

const option = (id, over) => ({ id, title: `option ${id}`, summary: `a summary for ${id}`, root_link: 'bears on the root question', compute_open: 'samples, 10 to 10,000', sequential: 'a chain of 500 steps', source_urls: [], narrowing: `leaves the field trial aside; the computed ${id} stands in for the measured yield; it moves the root question because both rank candidates`, ...over })
const scores = (id, distance, v) => ({ id, distance, distance_reason: 'a reason long enough to pass the gate', scores: ['stakes', 'open', 'reshape', 'internals'].map(c => ({ criterion: c, value: v[c] ?? 3, reason: 'a reason of more than fifteen characters' })) })
const stub = {
  calls: [],
  async run({ title, prompt }) {
    stub.calls.push(title)
    let json
    if (title === 'framer') json = { verdict: MODE === 'bound' ? 'COMPUTE-BOUND' : 'NOT COMPUTE-BOUND', compute_signals: [] }
    else if (title === 'widener' || title === 'deepener') json = { items: MODE === 'gate'
      ? [option('W1', { compute_open: 'settled: published up to 10^6 samples' }), option('W2', { compute_open: 'none' }), option('W3')]
      : [option('W1'), option('W2', { compute_open: 'none' }), option('W3', { narrowing: MODE === 'bound' ? '' : 'none' })] }
    else if (title.startsWith('screen-')) {
      const ids = [...prompt.matchAll(/"id":"([A-Za-z0-9]+)"/g)].map(m => m[1])
      json = { items: ids.map(id => scores(id, MODE === 'gate' && id === 'W3' ? 'ELSEWHERE' : 'SAME', id === 'V3' ? { stakes: 5, open: 5, reshape: 5 } : id === 'W1' ? { stakes: 3, open: 5, reshape: 4 } : { stakes: 3, open: 3, reshape: 1 })) }
    } else if (title === 'neighbours') json = { variants: ['V1', 'V2', 'V3'].map(id => ({ id, title: `variant ${id}`, text: `text of ${id}`, root_link: 'bears on it', compute_open: 'samples, 10 to 10,000', sequential: 'a chain of 500 steps', changes: 'one thing', narrowing: id === 'V2' ? '' : `narrowing of ${id}: leaves aside x, stands in for y, moves the question because z` })) }
    else json = {}
    return { json, errors: [], cost: 0.001, tokens: { input: 1, output: 1 }, ms: 1, sessionID: 'stub', jsonError: null }
  },
  async exportSession(id, file) { fs.writeFileSync(file, '{}') },
  runNode(script, args) {
    const out = args[args.indexOf('--out') + 1]
    fs.mkdirSync(out, { recursive: true })
    if (script === 'wf.js') {
      const a = JSON.parse(fs.readFileSync(args[args.indexOf('--args') + 1], 'utf8')), seed = a.seed_ideas[0]
      const card = `<a id="card-seed-idea-1"></a>**${seed.id} · ${seed.title}.** seed pick\n\n**Question.** ${seed.text}\n\n**Judges.** Dramaturg: PASS 2/2.`
      fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify({
        table: `| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |\n|---|\n| [seed·idea·1](#card-seed-idea-1) ${seed.title} | PASS 2/2 | seed | if_not | 4 | — → 5 | — → 3 | 5 | — | — → 5 | 5 | $946 at p_score · plan $946 · 1 GUESS |`,
        cards: [card], inventory: '', frontier: '', log: [], result_md: '# Result\n\nPicks 1 · PASS 1 · on-goal cards U4 1 · U3 1 · halts: none\n', price_sheet: {},
        calibration: [{ key: 'seed:idea:1', state: 'calibration_required', plan_usd: 946, required: [{ id: 'throughput', basis: 'PROXY', value: 250, measured_by: 'p_bench', cum_spend_through_measured_by: 36.2, k_budget: 1.1 }] }],
      }))
    } else fs.writeFileSync(path.join(out, 'frame.json'), JSON.stringify({ best: { name: 'a programme', fit: 3, change: 3, new: 5, sum: 11 }, programmes: [{ name: 'a programme', step: 's', sum: 11 }], gaps: [], cost_usd: 0 }))
  },
}
if (require.main !== module) { module.exports = stub } else {
  const ROOT = path.join(__dirname, '..'), T = fs.mkdtempSync(path.join(os.tmpdir(), 'e2e-loop-'))
  const seed = { id: 'T1', title: 'a test seed', text: 'a test problem', root_question: 'a test question', kind: 'physical', root_link: 'not given', compute_open: 'not given', sequential: 'not given', source_urls: [] }
  fs.writeFileSync(path.join(T, 'seed.json'), JSON.stringify(seed))
  const r = spawnSync('node', [path.join(ROOT, 'idea', 'loop.js'), '--seed', path.join(T, 'seed.json'), '--name', 'e2e', '--dir', path.join(T, 'out')], { env: { ...process.env, LOOP_STUB: __filename, LOOP_STUB_MODE: MODE }, encoding: 'utf8' })
  const md = fs.existsSync(path.join(T, 'out', 'loop.md')) ? fs.readFileSync(path.join(T, 'out', 'loop.md'), 'utf8') : ''
  const js = fs.existsSync(path.join(T, 'out', 'loop.json')) ? JSON.parse(fs.readFileSync(path.join(T, 'out', 'loop.json'), 'utf8')) : null
  const CHECKS = {
    ok: () => ({
      'exit 0': r.status === 0,
      'framer then widener (not deepener)': fs.existsSync(path.join(T, 'out', 'expand', 'physical-widener.md')) || /widener/.test(md),
      'W1 chosen (W2 none, W3 no narrowing)': js && js.expanded && js.expanded.chosen && js.expanded.chosen.id === 'W1',
      'gate reasons shown': /no compute effect named/.test(md) && /no narrowing stated/.test(md),
      'record text carries the narrowing': js && /Narrowing:/.test(js.expanded.chosen.text),
      'r0 card PASS': js && js.rounds[0] && js.rounds[0].verdict === 'PASS 2/2',
      'calibration line in loop.md': /Calibration: calibration_required; unmeasured load-bearing input\(s\): throughput \(PROXY 250, measured in p_bench after \$36\.2\)/.test(md),
      'V2 (no narrowing) not ranked; V3 displaces O; r1 ran': js && js.chosen === 'V3' && js.rounds.length === 2 && /V2: not ranked/.test(md),
    }),
    gate: () => ({
      'exit 0': r.status === 0,
      'no card produced': js && js.rounds.length === 0 && !fs.existsSync(path.join(T, 'out', 'r0')),
      'loop.md says none passed': /none passed the gate/.test(md),
      'three reasons logged': (md.match(/not ranked/g) || []).length === 3,
    }),
    bound: () => ({
      'exit 0': r.status === 0,
      'deepener ran': stubCalls(T).includes('deepener'),
      'no narrowing required: W3 eligible': js && js.expanded && js.expanded.screen.find(x => x.id === 'W3').eligible === true,
      'r0 card PASS': js && js.rounds[0] && js.rounds[0].verdict === 'PASS 2/2',
    }),
  }
  const checks = CHECKS[MODE]()
  let ok = true
  for (const [k, v] of Object.entries(checks)) { console.log(`  ${v ? 'ok  ' : 'FAIL'} ${k}`); ok = ok && !!v }
  if (!ok) { console.log(r.stdout.slice(-1500)); console.log(r.stderr.slice(-1500)) }
  console.log(`${MODE}: ${ok ? 'pass' : 'FAIL'} (${T})`)
  process.exit(ok ? 0 : 1)
  function stubCalls(dir) { return fs.readdirSync(path.join(dir, 'out', 'calls')).map(f => f.replace(/^\d+-/, '').replace(/\..*$/, '')) }
}
