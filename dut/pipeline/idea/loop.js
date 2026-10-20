#!/usr/bin/env node
'use strict'
// One idea, one improvement round. A one-line seed (compute_open "not given", or expand: true) is first turned into
// option records by the pipeline's own FRAMER and WIDENER, and the screen picks one. Then: card for the idea (wf.js) -> frame check (frame.js) -> three close variants written
// from the card and the frame check -> option-critic panel scores the idea and the variants -> if a variant scores
// higher, card and frame check for it. Every model call is an OpenCode call, logged like the others.
//
// usage: node loop.js --seed seed.json [--name label] [--dir <earlier loop dir>]
//   --dir reuses a round's card and frame check when its result.json / frame.json are already there
//   seed.json: {id, title, text, root_question, kind: "physical"|"interp", root_link, compute_open, sequential, source_urls}
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const { spawnSync } = require('node:child_process')
const oc = process.env.LOOP_STUB ? require(path.resolve(process.env.LOOP_STUB)) : require('./oc.js')   // LOOP_STUB: tools/e2e_loop.js
const { validate, promptSuffix } = require('./schema.js')

const SRC = path.join(__dirname, '..', 'src')
const ctx = vm.createContext({ console })
for (const m of ['text', 'schemas', 'cost', 'pick', 'gates', 'render', 'prompts', 'screen']) vm.runInContext(fs.readFileSync(path.join(SRC, `${m}.js`), 'utf8'), ctx, { filename: `${m}.js` })
const { P_OPTION_CRITIC, CRIT_OPTION, gate_oc, gate_opt, SCHEMA_OPTION_SCORES, P_FRAMER, P_WIDENER, P_DEEPENER, SCHEMA_VERDICT, SCHEMA_OPTIONS, screen_rank } =
  vm.runInContext('({ P_OPTION_CRITIC, CRIT_OPTION, gate_oc, gate_opt, SCHEMA_OPTION_SCORES, P_FRAMER, P_WIDENER, P_DEEPENER, SCHEMA_VERDICT, SCHEMA_OPTIONS, screen_rank })', ctx)

const argv = process.argv.slice(2)
const opt = (k, d) => { const i = argv.indexOf(`--${k}`); return i >= 0 ? argv[i + 1] : d }
const CFG = JSON.parse(fs.readFileSync(path.join(__dirname, 'config.json'), 'utf8'))
const SEED = JSON.parse(fs.readFileSync(opt('seed'), 'utf8'))
const NAME = opt('name', path.basename(opt('seed')).replace(/\.json$/, ''))
const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\..*/, '').replace('T', '-')
const LOOP = opt('dir', path.join(CFG.loop.runs_dir, NAME, stamp))
fs.mkdirSync(path.join(LOOP, 'calls'), { recursive: true })
const KIND = SEED.kind === 'interp' ? 'interp' : 'physical'
const CRIT = KIND === 'interp' ? ['stakes', 'open', 'internals'] : ['stakes', 'open']   // the pick totals: reshape is reported, not summed

// ---------- one OpenCode call with a check and one repair turn, fully logged under calls/ ----------
let nCalls = 0, spend = 0
async function call(name, model, prompt, check, agent = 'qt-bare', cwd = path.join(LOOP, 'calls')) {
  const base = path.join(LOOP, 'calls', `${String(++nCalls).padStart(2, '0')}-${name}`)
  fs.writeFileSync(`${base}.prompt.md`, prompt)
  let session = null, res = null, errors = []
  for (let attempt = 1; attempt <= 2; attempt++) {
    const p = attempt === 1 ? prompt : `Your reply could not be used: ${errors.slice(0, 15).join('; ')}. Reply again with only the JSON asked for.`
    res = await oc.run({ model, agent, prompt: p, cwd, session, timeoutMs: 10 * 60000, rawPath: `${base}.events.jsonl`, httpLogDir: `${base}.http`, title: name })
    session = res.sessionID; spend += res.cost
    fs.appendFileSync(path.join(LOOP, 'ledger.jsonl'), JSON.stringify({ ts: new Date().toISOString(), name, model, attempt, tokens: res.tokens, cost_usd: res.cost, ms: res.ms, errors: res.errors }) + '\n')
    errors = res.errors.length ? res.errors : res.json == null ? [res.jsonError || 'no JSON found in the reply'] : check(res.json)
    fs.appendFileSync(path.join(LOOP, 'ledger.jsonl'), JSON.stringify({ name, attempt, check_errors: errors.slice(0, 10) }) + '\n')
    if (!errors.length) break
  }
  await oc.exportSession(session, `${base}.export.json`)
  return errors.length ? null : res.json
}

// ---------- card and frame check through the existing tools ----------
function runNode(script, args) {
  if (oc.runNode) return oc.runNode(script, args)   // stubbed card and frame outputs
  const r = spawnSync('node', [path.join(__dirname, script), ...args], { stdio: 'inherit' })
  if (r.status !== 0) throw new Error(`${script} exited ${r.status}`)
}
function cardAndFrame(record, tag) {
  const dir = path.join(LOOP, tag)
  fs.mkdirSync(dir, { recursive: true })
  const F = JSON.parse(fs.readFileSync(CFG.roots_args, 'utf8'))
  const args = { ...Object.fromEntries(Object.entries(F).filter(([k]) => !['fixed_roots', 'base'].includes(k))), base: 'auto', fixed_roots: [], seed_ideas: [{ ...record, root_question: SEED.root_question, kind: KIND }] }
  fs.writeFileSync(path.join(dir, 'args.json'), JSON.stringify(args, null, 1))
  if (!fs.existsSync(path.join(dir, 'card', 'result.json'))) runNode('wf.js', ['--args', path.join(dir, 'args.json'), '--name', `${NAME}-${tag}`, '--out', path.join(dir, 'card')])
  const result = JSON.parse(fs.readFileSync(path.join(dir, 'card', 'result.json'), 'utf8'))
  const card = (result.cards || [])[0] || ''
  fs.writeFileSync(path.join(dir, 'card.md'), card.split('\n**Judges.**')[0].replace(/^<a id="[^"]*"><\/a>/, ''))
  const row0 = (result.table || '').split('\n').find(l => l.startsWith('| ['))
  const judged = !!row0 && /^(PASS|REJECT)/.test(row0.split('|')[2].trim())
  if (!judged) return { tag, verdict: row0 ? row0.split('|')[2].trim() : 'no card', critic: {}, critic_sum: 0, plan: '', frame_best: null, frame_programmes: [], gaps: [], card, cost_usd: 0, judged }   // a halted card gets no frame check
  if (!fs.existsSync(path.join(dir, 'frame', 'frame.json'))) runNode('frame.js', ['--card-file', path.join(dir, 'card.md'), '--root', SEED.root_question, '--out', path.join(dir, 'frame')])
  const frame = JSON.parse(fs.readFileSync(path.join(dir, 'frame', 'frame.json'), 'utf8'))
  const row = (result.table || '').split('\n').find(l => l.startsWith('| ['))
  const cells = row ? row.split('|').slice(1, -1).map(s => s.trim()) : []
  const num = s => { const v = String(s || '').split('→').pop().trim(); return /^\d$/.test(v) ? Number(v) : null }
  const crit = { lever: num(cells[4]), open: num(cells[5]), stakes: num(cells[6]), verifiable: num(cells[7]), internals: num(cells[8]), reshape: num(cells[9]), baseline: num(cells[10]) }
  return { tag, judged, verdict: cells[1] || 'no card', critic: crit, critic_sum: ['stakes', 'lever', 'verifiable', 'open', 'reshape'].reduce((t, k) => t + (crit[k] || 0), 0),
    plan: cells[11] || '', calibration: (result.calibration || [])[0] || null, frame_best: frame.best, frame_programmes: frame.programmes.map(p => ({ name: p.name, step: p.step, sum: p.sum })), gaps: frame.gaps, card, cost_usd: frame.cost_usd }
}

// ---------- neighbours and screen ----------
const SCHEMA_VARIANTS = { type: 'object', required: ['variants'], properties: { variants: { type: 'array', items: { type: 'object',
  required: ['id', 'title', 'text', 'root_link', 'compute_open', 'sequential', 'changes'],
  properties: Object.fromEntries(['id', 'title', 'text', 'root_link', 'compute_open', 'sequential', 'changes', 'narrowing'].map(k => [k, { type: 'string' }])) } } } }
const P_NEIGHBOURS = (rec, r0) =>
  `Here is a research idea, the card a planner wrote for it, and a check of which existing research or industrial programmes would use its result, with the gaps that check found.\n\n` +
  `Root question: ${SEED.root_question}\nIdea: ${JSON.stringify({ title: rec.title, text: rec.text, root_link: rec.root_link, compute_open: rec.compute_open, sequential: rec.sequential })}\n` +
  `Card:\n${r0.card.split('\n**Judges.**')[0]}\nCard verdict: ${r0.verdict}\nProgramme check: ${JSON.stringify(r0.frame_programmes)}\nGaps found: ${JSON.stringify(r0.gaps)}\n\n` +
  `Propose three close variants of the idea. Each changes one thing (the system studied, the quantity more compute buys, the comparison it is judged against, or the programme it is aimed at) so that its result would matter more to a named programme or close a named gap. Keep the rest of the idea. ` +
  `Name only systems, tools and programmes that appear above or that you are sure exist. Decide only from the text above; do not use tools.\n` +
  `Return only JSON: {"variants": [{"id": "V1", "title": "", "text": "the idea in three to five sentences, in the form of the original", "root_link": "", "compute_open": "", "sequential": "", "changes": "what differs from the original and which gap or programme it answers", "narrowing": "${NARROWING_FIELD}"}]}`

// asked of every option when the framer found the root question not compute-bound (and of every variant): the gate
// (src/screen.js) refuses an option that leaves it empty or says none
const NARROWING_FIELD = 'what of the root question this leaves aside, what the computed observable stands in for, and why its answer still moves the root question; one to three sentences'
const NARROWING_SUFFIX = ` Add to each item a field "narrowing": ${NARROWING_FIELD}.`

const median = xs => { const s = xs.filter(Number.isFinite).sort((a, b) => a - b); return s.length ? s[Math.floor((s.length - 1) / 2)] : null }

// option-critic panel on a list of option records: per option the median of each criterion, the pick total and the
// majority distance label (SAME / ADJACENT / ELSEWHERE against the root question)
async function screenOptions(options) {
  const scored = await Promise.all(CFG.loop.screen.map(m => call(`screen-${m.split('/').pop()}`, m, P_OPTION_CRITIC(SEED.root_question, CRIT_OPTION(KIND), options) + promptSuffix(SCHEMA_OPTION_SCORES),
    r => {   // the gate assumes the schema's shape, so it runs only once the schema check passes
      const e = validate(SCHEMA_OPTION_SCORES, r)
      if (e.length) return e
      const g = gate_oc(r.items, options, [...CRIT, 'reshape'])
      return g.ok ? [] : g.errors.concat([...(g.degenerate || [])].map(d => `${d}: reason only restates the criterion`))
    })))
  if (!scored.some(Boolean)) throw new Error('every screen call failed its check; see ledger.jsonl')
  return options.map(o => {
    const items = scored.filter(Boolean).map(s => s.items.find(i => i.id === o.id)).filter(Boolean)
    const per = Object.fromEntries([...CRIT, 'reshape'].map(c => [c, median(items.map(it => (it.scores.find(x => x.criterion === c) || {}).value))]))
    const labels = items.map(it => it.distance)
    const distance = ['SAME', 'ADJACENT', 'ELSEWHERE'].sort((a, b) => labels.filter(x => x === b).length - labels.filter(x => x === a).length)[0]
    return { id: o.id, title: o.title, changes: o.changes || '', root_link: o.root_link, compute_open: o.compute_open, sequential: o.sequential, narrowing: o.narrowing || '', ...per, total: CRIT.reduce((t, c) => t + (per[c] || 0), 0), distance }
  })
}

// one-line seed -> FRAMER; its verdict routes: COMPUTE-BOUND -> DEEPENER, NOT COMPUTE-BOUND -> WIDENER with a narrowing per
// option -> option-critic screen -> the gate and pick rule in src/screen.js. Returns record null when nothing passes.
async function expand() {
  const dir = path.join(LOOP, 'expand')
  fs.mkdirSync(dir, { recursive: true })
  const fpath = path.join(dir, 'framer.md')
  const fr = await call('framer', CFG.loop.expand_model, P_FRAMER(SEED.root_question, fpath) + promptSuffix(SCHEMA_VERDICT), r => validate(SCHEMA_VERDICT, r), 'qt-research', dir)
  if (!fr) throw new Error('framer failed; see ledger.jsonl')
  const bound = fr.verdict === 'COMPUTE-BOUND'
  const role = bound ? 'deepener' : 'widener', bpath = path.join(dir, `${KIND}-${role}.md`)
  const prompt = (bound ? P_DEEPENER : P_WIDENER)(fpath, bpath) + (bound ? '' : NARROWING_SUFFIX)
  const check = r => {
    const e = validate(SCHEMA_OPTIONS, r)
    if (e.length) return e
    const g = gate_opt(r.items)
    return g.ok ? (bound ? [] : r.items.filter(o => !String(o.narrowing || '').trim()).map(o => `${o.id}: narrowing missing`)) : g.errors
  }
  const wd = await call(role, CFG.loop.expand_model, prompt + promptSuffix(SCHEMA_OPTIONS), check, 'qt-research', dir)
  if (!wd) throw new Error(`${role} failed; see ledger.jsonl`)
  const opts = wd.items.map(o => ({ id: String(o.id), title: o.title, summary: o.summary, root_link: o.root_link, compute_open: o.compute_open, sequential: o.sequential, source_urls: o.source_urls, narrowing: o.narrowing || '' }))
  const sc = await screenOptions(opts)
  const rk = screen_rank(sc, { kind: KIND, verdict: fr.verdict, seed: 1 })
  const o = rk.top && opts.find(x => x.id === rk.top)
  fs.writeFileSync(path.join(dir, 'expand.json'), JSON.stringify({ framer: fr, role, options: opts, screen: sc, ranked: rk.ranked, gate_log: rk.log, chosen: rk.top, why: rk.why }, null, 1))
  return { record: o ? { id: o.id, title: o.title, text: o.summary + (o.narrowing ? ` Narrowing: ${o.narrowing}` : ''), root_link: o.root_link, compute_open: o.compute_open, sequential: o.sequential, source_urls: o.source_urls || [], narrowing: o.narrowing } : null,
    screen: rk.ranked, verdict: fr.verdict, role, why: rk.why, gate_log: rk.log }
}

;(async () => {
  const log = []
  const thin = SEED.expand === true || /not given/i.test(SEED.compute_open || 'not given')
  const ex = thin ? await expand() : null
  const gateCols = s => `| ${s.id} ${s.title} | ${CRIT.map(c => s.scores ? s.scores[c] ?? '—' : s[c] ?? '—').join(' | ')} | ${s.scores ? s.scores.reshape : s.reshape ?? '—'} | ${s.total} | ${s.eligible === false ? s.reasons.join('; ') : 'ranked'} | ${s.narrowing || '—'} | ${s.changes || ''} |`
  const screenHead = [`| Option | ${CRIT.join(' | ')} | reshape | total | gate | narrowing | changes |`, `|---|${CRIT.map(() => '---|').join('')}---|---|---|---|---|`]
  if (ex && !ex.record) {   // nothing passed the gate: a legitimate end, no card
    const out = { name: NAME, seed: SEED, expanded: { verdict: ex.verdict, role: ex.role, chosen: null, screen: ex.screen, why: ex.why }, loop_dir: LOOP, screen: [], chosen: null, rounds: [], loop_calls_cost_usd: +spend.toFixed(4) }
    fs.writeFileSync(path.join(LOOP, 'loop.json'), JSON.stringify(out, null, 1))
    const L = [`# Idea loop: ${SEED.title}`, '', `Root question: ${SEED.root_question}`, '', `Framer: ${ex.verdict}; ${ex.role} listed ${ex.screen.length} option(s); none passed the gate (${ex.why}). No card.`, '',
      '## Screen (option-critic panel, medians; gate from src/screen.js)', '', ...screenHead, ...ex.screen.map(gateCols), '', '## Gate log', '', ...ex.gate_log.map(l => `- ${l}`), '']
    fs.writeFileSync(path.join(LOOP, 'loop.md'), L.join('\n'))
    console.log(L.join('\n') + `\n${LOOP}`)
    return
  }
  const REC = ex ? ex.record : SEED
  const r0 = cardAndFrame(REC, 'r0')
  log.push(r0)
  if (!r0.judged) throw new Error(`r0 card not judged (${r0.verdict}); no frame check or neighbours. See r0/card/RESULT.md`)
  const nb = await call('neighbours', CFG.loop.generator, P_NEIGHBOURS(REC, r0), r => validate(SCHEMA_VARIANTS, r).concat(r.variants && r.variants.length === 3 ? [] : ['give exactly three variants']))
  const options = [{ id: 'O', title: REC.title, summary: REC.text, root_link: REC.root_link, compute_open: REC.compute_open, sequential: REC.sequential, narrowing: REC.narrowing || '' }]
    .concat(((nb && nb.variants) || []).map(v => ({ id: v.id, title: v.title, summary: v.text, root_link: v.root_link, compute_open: v.compute_open, sequential: v.sequential, changes: v.changes, narrowing: v.narrowing || '' })))
  const sc2 = await screenOptions(options)
  // the same gate and pick rule as the expansion: a variant replaces the original only if it passes the gate and the rule picks it
  const rk2 = screen_rank(sc2, { kind: KIND, verdict: ex ? ex.verdict : null, seed: 1 })
  const screen = rk2.ranked
  const best = rk2.top && rk2.top !== 'O' ? screen.find(s => s.id === rk2.top) : null
  let r1 = null
  if (best) {   // r1 runs for the variant; a halted r1 card is reported as such
    const v = nb.variants.find(x => x.id === best.id)
    r1 = cardAndFrame({ id: v.id, title: v.title, text: v.text + (v.narrowing ? ` Narrowing: ${v.narrowing}` : ''), root_link: v.root_link, compute_open: v.compute_open, sequential: v.sequential, source_urls: [] }, 'r1')
    log.push(r1)
  }
  const out = { name: NAME, seed: SEED, expanded: ex && { verdict: ex.verdict, role: ex.role, chosen: REC, screen: ex.screen, why: ex.why }, loop_dir: LOOP, screen, pick_why: rk2.why, chosen: r1 ? best.id : null, rounds: log.map(({ card, ...rest }) => rest), loop_calls_cost_usd: +spend.toFixed(4) }
  fs.writeFileSync(path.join(LOOP, 'loop.json'), JSON.stringify(out, null, 1))
  const L = [`# Idea loop: ${SEED.title}`, '', `Root question: ${SEED.root_question}`, '',
    ...(ex ? [`Expanded from a one-line seed (framer: ${ex.verdict}, so the ${ex.role} listed the options): option ${REC.id} "${REC.title}" chosen by the gate and pick rule (${ex.why}) among ${ex.screen.length}, ${ex.screen.filter(s => s.eligible).length} of which passed the gate.`, '',
      '### Expansion screen', '', ...screenHead, ...ex.screen.map(gateCols), '', ...ex.gate_log.map(l => `- ${l}`), ''] : []), '## Screen (option-critic panel, medians; gate from src/screen.js)', '',
    ...screenHead, ...screen.map(gateCols), '', ...rk2.log.map(l => `- ${l}`), '',
    r1 ? `Variant ${best.id} passed the gate and the pick rule chose it over the original (${rk2.why}); it got its own card.` : `No variant displaced the original (${rk2.why}); no second card.`, '', '## Rounds', '']
  for (const r of log) L.push(`**${r.tag}:** card ${r.verdict}, critic sum ${r.critic_sum}/25 (${Object.entries(r.critic).map(([k, v]) => `${k} ${v ?? '—'}`).join(', ')}), ${r.plan}. ` +
    `Frame: ${r.frame_best ? `${r.frame_best.name}, fit ${r.frame_best.fit}, change ${r.frame_best.change}, new ${r.frame_best.new} (${r.frame_best.sum}/15)` : 'no grounded programme'}. ` +
    (r.calibration ? `Calibration: ${r.calibration.state}${r.calibration.required.length ? `; unmeasured load-bearing input(s): ${r.calibration.required.map(u => `${u.id} (${u.basis} ${u.value}, measured in ${u.measured_by || 'no phase'} after $${u.cum_spend_through_measured_by ?? '?'})`).join('; ')}` : ''}.` : ''), '')
  fs.writeFileSync(path.join(LOOP, 'loop.md'), L.join('\n'))
  console.log(L.join('\n') + `\n${LOOP}`)
})().catch(e => { console.error(e); process.exit(1) })
