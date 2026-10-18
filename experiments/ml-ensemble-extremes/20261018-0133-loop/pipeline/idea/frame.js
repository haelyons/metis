#!/usr/bin/env node
'use strict'
// Frame check for one card: which existing research or industrial programmes would its result feed, is that practice
// cited and checked, and how well does the card fit. Stages: researcher (web) -> two dramaturgs on different models
// -> three critics on different models -> medians. Every model call goes through OpenCode (oc.js), metered in ledger.jsonl.
//
// usage: node frame.js --card R4:interp:I1            (a card from run F's RESULT.md)
//        node frame.js --card-file idea.md --root "…"  (any card or idea written as text)
//        options: --config config.json  --out <dir>  --research-model m  --dramaturgs m1,m2  --critics m1,m2,m3
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const oc = require('./oc.js')
const { programmeFlags, applyCaps } = require('./frame_rules.js')

// ---------- shared pipeline modules (prompts, gates) loaded as in tests/run.js ----------
const SRC = path.join(__dirname, '..', 'src')
const ctx = vm.createContext({ console })
for (const m of ['text', 'schemas', 'cost', 'pick', 'gates', 'render', 'prompts']) vm.runInContext(fs.readFileSync(path.join(SRC, `${m}.js`), 'utf8'), ctx, { filename: `${m}.js` })
const { P_DRAMATURG, P_lines, gate_findings } = vm.runInContext('({ P_DRAMATURG, P_lines, gate_findings })', ctx)

// ---------- args ----------
const argv = process.argv.slice(2)
const opt = (k, d) => { const i = argv.indexOf(`--${k}`); return i >= 0 ? argv[i + 1] : d }
const CFG = JSON.parse(fs.readFileSync(opt('config', path.join(__dirname, 'config.json')), 'utf8'))
const M = {
  research: opt('research-model', CFG.models.research),
  dramaturg: (opt('dramaturgs') || '').split(',').filter(Boolean).length ? opt('dramaturgs').split(',') : CFG.models.dramaturg,
  critic: (opt('critics') || '').split(',').filter(Boolean).length ? opt('critics').split(',') : CFG.models.critic,
}
const MIN = 60000

// ---------- the card ----------
function loadCard() {
  const key = opt('card')
  if (key) {
    const md = fs.readFileSync(CFG.result_md, 'utf8')
    const anchor = `<a id="card-${key.replace(/:/g, '-')}"></a>`
    const at = md.indexOf(anchor)
    if (at < 0) throw new Error(`card ${key} not found in ${CFG.result_md}`)
    const body = md.slice(at + anchor.length).split('\n**Judges.**')[0].split('\n<a id="card-')[0].trim()
    const roots = JSON.parse(fs.readFileSync(CFG.roots_args, 'utf8')).fixed_roots
    return { key, text: body, root: roots[Number(key.slice(1).split(':')[0]) - 1] }
  }
  const file = opt('card-file')
  if (!file) throw new Error('give --card <key> or --card-file <path> --root "<question>"')
  return { key: path.basename(file).replace(/\.[^.]+$/, ''), text: fs.readFileSync(file, 'utf8').trim(), root: opt('root', 'not given') }
}

// ---------- prompts (new for this stage) ----------
const P_FRAME_RESEARCH = (root, card) =>
  `Here is a research card, written to answer this root question: ${root}\n\n${card}\n\n` +
  `Find the existing research or industrial programmes this card's result would feed: named labs, companies, open-source projects or consortia doing this work now. Pick one to three. ` +
  `For each, use its own pages, papers or repositories to describe the step of its pipeline the card targets, and how it handles that step today: at what scale, with which tools or people. ` +
  `Describe that step in the programme's own words, and copy the sentence from its own page that describes it (step_url, step_quote). ` +
  `Say whether the programme is active now: cite its most recent release, commit, paper or announcement, or a statement that it was archived or stopped (activity). ` +
  `Say what each of the card's two predicted outcomes would change in that programme's practice, or that it would change nothing. ` +
  `Check whether that programme, or work it relies on, has already run this experiment. ` +
  `Cite a URL for every factual claim and copy the sentence from that page that supports it. If no programme would use the result, return no programmes and say why. ` +
  `Write your working notes to notes.md in your working directory.\n` +
  `Return only JSON: {"programmes": [{"name": "", "url": "", "step": "", "step_url": "", "step_quote": "", "activity": {"state": "active | inactive | unknown", "claim": "", "url": "", "quote": ""}, "practice": [{"claim": "", "url": "", "quote": ""}], "if_lever_changes": "", "if_not_changes": "", "already_done": {"status": "yes | partly | no | unknown", "claim": "", "url": "", "quote": ""}}], "gaps": [""], "no_programme_reason": ""}`

const FORMAT_FINDINGS = `\nReturn only JSON: {"items": [{"ref": "", "status": "SUPPORTED | PARTIAL | UNSUPPORTED | CONTRADICTED | UNREACHABLE", "page_quote": "", "note": ""}]}`

const CRIT_FRAME = [
  `fit: Does the card's measured outcome feed a named step of this programme? 5 = it measures the quantity that step's current practice depends on, on systems the programme uses; 3 = it feeds that step only through a stand-in (another model, system or scale) the programme would have to bridge; 1 = no step of the programme would use the outcome. A step given only in the card's terms, not the programme's own, scores 3 at most.`,
  `change: What would the card's outcomes change in this programme's practice? 5 = either outcome changes a choice the programme makes now (what to build, buy, label, check or scale), as its supported practice shows; 3 = only one outcome would change practice, or the change needs further work the card does not do; 1 = neither outcome would change what the programme does. An inactive or archived programme scores 1.`,
  `new: Has this programme, or work it relies on, already answered the card's question? 5 = supported claims show its current practice lacks this measurement; 3 = unclear, or partly answered; 1 = already answered. If a checker contradicted the claim that it has not been done, score 3 at most.`,
]
const P_FRAME_CRITIC = (root, card, progs) =>
  `Score how well this research card fits each existing programme below. Each programme lists claims about its current practice; two checkers fetched each source and marked each claim SUPPORTED, PARTIAL, UNSUPPORTED, CONTRADICTED or UNREACHABLE. ` +
  `Rely only on claims that at least one checker marked SUPPORTED or PARTIAL. Score each programme 1-5 on each criterion, with a reason of at most 25 words. Decide only from the text below; do not use tools.\n` +
  `Root question: ${root}\nCard:\n${card}\nProgrammes:\n${P_lines(progs)}\nCriteria:\n${CRIT_FRAME.join('\n')}\n` +
  `Return only JSON: {"scores": [{"programme": 1, "criterion": "fit | change | new", "value": 1, "reason": ""}]}`

// ---------- checks on each reply ----------
const str = v => typeof v === 'string' && v.trim().length > 0
function checkResearch(r) {
  const e = []
  if (!r || !Array.isArray(r.programmes)) return ['no programmes array']
  if (r.programmes.length > 3) e.push(`${r.programmes.length} programmes (at most 3)`)
  if (!r.programmes.length && !str(r.no_programme_reason)) e.push('no programmes and no no_programme_reason')
  r.programmes.forEach((p, i) => {
    for (const k of ['name', 'step', 'step_url', 'step_quote', 'if_lever_changes', 'if_not_changes']) if (!str(p[k])) e.push(`programme ${i + 1}: ${k} missing`)
    const a = p.activity || {}
    if (!['active', 'inactive', 'unknown'].includes(a.state)) e.push(`programme ${i + 1}: activity.state must be active, inactive or unknown`)
    else if (a.state !== 'unknown') for (const k of ['claim', 'url', 'quote']) if (!str(a[k])) e.push(`programme ${i + 1}: activity.${k} missing`)
    if (!Array.isArray(p.practice) || !p.practice.length) e.push(`programme ${i + 1}: no practice claims`)
    else p.practice.forEach((c, j) => { for (const k of ['claim', 'url', 'quote']) if (!str(c[k])) e.push(`programme ${i + 1} claim ${j + 1}: ${k} missing`) })
    if (!p.already_done || !['yes', 'partly', 'no', 'unknown'].includes(p.already_done.status)) e.push(`programme ${i + 1}: already_done.status must be yes, partly, no or unknown`)
  })
  return e
}
function checkCritique(r, n) {
  const e = []
  if (!r || !Array.isArray(r.scores)) return ['no scores array']
  for (let p = 1; p <= n; p++) for (const c of ['fit', 'change', 'new']) {
    const s = r.scores.filter(x => Number(x.programme) === p && x.criterion === c)
    if (s.length !== 1) e.push(`programme ${p} ${c}: ${s.length} scores`)
    else if (!Number.isInteger(s[0].value) || s[0].value < 1 || s[0].value > 5) e.push(`programme ${p} ${c}: value ${s[0].value} (need an integer 1-5)`)
  }
  return e
}

// ---------- run state, ledger, status ----------
const card = loadCard()
const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\..*/, '').replace('T', '-')
const RUN = opt('out', path.join(CFG.runs_dir, card.key.replace(/[^A-Za-z0-9._-]/g, '_'), stamp))
for (const d of ['raw', 'research']) fs.mkdirSync(path.join(RUN, d), { recursive: true })
const status = { run_dir: RUN, card: card.key, models: M, stage: 'start', started: new Date().toISOString(), calls: [], cost_usd: 0, tokens: 0, by_model: {}, done: false }
const saveStatus = () => { status.updated = new Date().toISOString(); fs.writeFileSync(path.join(RUN, 'status.json.tmp'), JSON.stringify(status, null, 1)); fs.renameSync(path.join(RUN, 'status.json.tmp'), path.join(RUN, 'status.json')) }
fs.writeFileSync(path.join(RUN, 'card.md'), `Root question: ${card.root}\n\n${card.text}\n`)
saveStatus()

// One role call with one repair turn; every attempt is metered.
async function call(stage, model, agent, prompt, check, timeoutMin, cwd) {
  const id = `${stage}#${status.calls.length + 1}`
  const rec = { id, stage, model, state: 'running', attempts: 0, ms: 0, cost_usd: 0, tokens: 0 }
  status.calls.push(rec); saveStatus()
  let session = null, res = null, errors = []
  const base = path.join(RUN, 'raw', id.replace('#', '-'))
  fs.writeFileSync(`${base}.prompt.md`, prompt)
  for (let attempt = 1; attempt <= 2; attempt++) {
    rec.attempts = attempt
    const p = attempt === 1 ? prompt : `Your reply could not be used: ${errors.join('; ')}. Reply again with only the JSON asked for.`
    res = await oc.run({ model, agent, prompt: p, cwd: cwd || RUN, session, timeoutMs: timeoutMin * MIN, rawPath: path.join(RUN, 'raw', `${id.replace('#', '-')}.jsonl`), httpLogDir: `${base}.http`, title: id })
    const tok = res.tokens.input + res.tokens.output + res.tokens.reasoning
    rec.ms += res.ms; rec.cost_usd += res.cost; rec.tokens += tok; status.cost_usd += res.cost; status.tokens += tok
    fs.appendFileSync(path.join(RUN, 'ledger.jsonl'), JSON.stringify({ ts: new Date().toISOString(), id, stage, model, agent, attempt, session: res.sessionID, ms: res.ms, tokens: res.tokens, cost_usd: res.cost, tools: res.tools, errors: res.errors }) + '\n')
    session = res.sessionID
    errors = res.errors.length ? res.errors : res.json == null ? ['no JSON found in the reply'] : check(res.json)
    if (!errors.length) break
  }
  rec.state = errors.length ? 'failed' : 'ok'
  rec.errors = errors
  await oc.exportSession(session, `${base}.export.json`)
  const bm = status.by_model[model] = status.by_model[model] || { calls: 0, cost_usd: 0, tokens: 0 }
  bm.calls++; bm.cost_usd += rec.cost_usd; bm.tokens += rec.tokens
  saveStatus()
  return { json: res && res.json, ok: !errors.length, errors, model, raw_text: res && res.text }
}

const median = xs => { const s = xs.filter(Number.isFinite).sort((a, b) => a - b); return s.length ? (s.length % 2 ? s[(s.length - 1) / 2] : (s[s.length / 2 - 1] + s[s.length / 2]) / 2) : null }
const OKS = ['SUPPORTED', 'PARTIAL']

async function main() {
  const t0 = Date.now()
  // 1. researcher
  status.stage = 'research'; saveStatus()
  const rs = await call('research', M.research, 'qt-research', P_FRAME_RESEARCH(card.root, card.text), checkResearch, CFG.timeouts_min.research, path.join(RUN, 'research'))
  const progs = (rs.json && Array.isArray(rs.json.programmes) ? rs.json.programmes : []).slice(0, 3)

  // 2. dramaturgs: the step, the activity claim, every practice claim and every already_done claim with a source
  const items = []
  progs.forEach((p, i) => {
    if (str(p.step_url)) items.push({ ref: `p${i + 1}:step`, line: `p${i + 1}:step: ${p.name} has this step in its pipeline: ${p.step} | source: ${p.step_url} | recorded quote: "${p.step_quote || ''}"` })
    const a = p.activity || {}
    if (str(a.url)) items.push({ ref: `p${i + 1}:activity`, line: `p${i + 1}:activity: ${a.claim} | source: ${a.url} | recorded quote: "${a.quote || ''}"` })
    ;(p.practice || []).forEach((c, j) => items.push({ ref: `p${i + 1}:c${j + 1}`, line: `p${i + 1}:c${j + 1}: ${c.claim} | source: ${c.url} | recorded quote: "${c.quote}"` }))
    const d = p.already_done || {}
    if (str(d.url)) items.push({ ref: `p${i + 1}:done`, line: `p${i + 1}:done: ${d.claim || `already done: ${d.status}`} | source: ${d.url} | recorded quote: "${d.quote || ''}"` })
  })
  status.stage = 'dramaturg'; saveStatus()
  const refs = items.map(x => x.ref)
  const drams = items.length ? await Promise.all(M.dramaturg.map(m => call('dramaturg', m, 'qt-web', P_DRAMATURG(items.map(x => x.line)) + FORMAT_FINDINGS,
    r => { const g = gate_findings((r && r.items) || [], refs); return g.errors.concat(g.degenerate.map(x => `${x}: page_quote or note too short`)) }, CFG.timeouts_min.dramaturg))) : []
  const marks = Object.fromEntries(refs.map(ref => [ref, drams.map(d => ((d.json && d.json.items) || []).find(x => x.ref === ref) || null)]))
  const verdict = ref => { const n = (marks[ref] || []).filter(x => x && OKS.includes(x.status)).length; return n === drams.length && n ? 'verified' : n ? 'disputed' : 'failed' }

  // 3. critics on every programme with at least one claim not failed
  const view = progs.map((p, i) => {
    const claims = (p.practice || []).map((c, j) => ({ claim: c.claim, url: c.url, checks: (marks[`p${i + 1}:c${j + 1}`] || []).map(x => x ? x.status : 'NO ANSWER'), verdict: verdict(`p${i + 1}:c${j + 1}`) }))
    const d = p.already_done || {}
    const a = p.activity || {}, checks = ref => (marks[ref] || []).map(x => x ? x.status : 'NO ANSWER')
    return { n: i + 1, name: p.name, url: p.url, step: p.step, step_url: p.step_url, step_checks: checks(`p${i + 1}:step`),
      activity: { state: a.state, claim: a.claim, url: a.url, checks: checks(`p${i + 1}:activity`) }, flags: programmeFlags(p, i + 1, marks),
      claims, if_lever_changes: p.if_lever_changes, if_not_changes: p.if_not_changes,
      already_done: { status: d.status, claim: d.claim, checks: (marks[`p${i + 1}:done`] || []).map(x => x ? x.status : 'NO ANSWER') },
      grounded: claims.some(c => c.verdict !== 'failed') }
  })
  const grounded = view.filter(v => v.grounded)
  const shown = grounded.map((v, k) => ({ programme: k + 1, name: v.name, step: v.step,
    practice: v.claims.filter(c => c.verdict !== 'failed').map(c => `${c.claim} [${c.checks.join(', ')}]`),
    if_lever_changes: v.if_lever_changes, if_not_changes: v.if_not_changes, already_done: v.already_done,
    activity: `${v.activity.state || 'unknown'}${v.activity.claim ? `: ${v.activity.claim}` : ''} [${v.activity.checks.join(', ') || 'no source'}]`,
    step_in_card_terms: v.flags.step_restates_card ? 'yes: the step is put in the card\'s terms, or no checker found it on the programme\'s page' : 'no' }))
  status.stage = 'critic'; saveStatus()
  const crits = shown.length ? await Promise.all(M.critic.map(m => call('critic', m, 'qt-bare', P_FRAME_CRITIC(card.root, card.text, shown), r => checkCritique(r, shown.length), CFG.timeouts_min.critic))) : []

  // 4. medians per programme and criterion
  const scored = grounded.map((v, k) => {
    const per = {}
    for (const c of ['fit', 'change', 'new']) {
      const vals = crits.map(cr => ((cr.json && cr.json.scores) || []).find(s => Number(s.programme) === k + 1 && s.criterion === c)).map(s => s ? s.value : null)
      const reasons = crits.map((cr, i) => { const s = ((cr.json && cr.json.scores) || []).find(s => Number(s.programme) === k + 1 && s.criterion === c); return s ? `${M.critic[i]}: ${s.reason}` : null }).filter(Boolean)
      per[c] = { median: median(vals), values: vals, spread: vals.filter(Number.isFinite).length ? Math.max(...vals.filter(Number.isFinite)) - Math.min(...vals.filter(Number.isFinite)) : null, reasons }
    }
    const caps = applyCaps(per, v.flags)   // frame_rules.js: evidence in the record caps what the critics gave
    const sum = ['fit', 'change', 'new'].reduce((t, c) => t + (per[c].median || 0), 0)
    return { ...v, scores: per, sum, caps }
  })
  // ties: higher fit, then lower total spread across critics
  const spread = s => ['fit', 'change', 'new'].reduce((t, c) => t + (s.scores[c].spread || 0), 0)
  const best = scored.slice().sort((a, b) => b.sum - a.sum || (b.scores.fit.median || 0) - (a.scores.fit.median || 0) || spread(a) - spread(b))[0] || null
  const result = {
    card: card.key, root: card.root, models: M, run_dir: RUN, wall_min: +((Date.now() - t0) / MIN).toFixed(1),
    cost_usd: +status.cost_usd.toFixed(4), tokens: status.tokens,
    research_ok: rs.ok, research_errors: rs.errors, no_programme_reason: rs.json && rs.json.no_programme_reason, gaps: (rs.json && rs.json.gaps) || [],
    programmes: view.map(v => scored.find(s => s.n === v.n) || v),
    best: best && { name: best.name, step: best.step, sum: best.sum, fit: best.scores.fit.median, change: best.scores.change.median, new: best.scores.new.median },
    failed_calls: status.calls.filter(c => c.state === 'failed').map(c => ({ id: c.id, model: c.model, errors: c.errors })),
  }
  fs.writeFileSync(path.join(RUN, 'frame.json'), JSON.stringify(result, null, 1))
  fs.writeFileSync(path.join(RUN, 'frame.md'), renderMd(result))
  status.stage = 'done'; status.done = true; status.best = result.best; saveStatus()
  console.log(`${card.key}: ${result.best ? `best ${result.best.name} (fit ${result.best.fit}, change ${result.best.change}, new ${result.best.new}; sum ${result.best.sum}/15)` : 'no grounded programme'} · $${result.cost_usd} · ${result.tokens.toLocaleString()} tokens · ${result.wall_min} min\n${RUN}/frame.md`)
}

function renderMd(r) {
  const L = [`# Frame check: ${r.card}`, '', `Root question: ${r.root}`, '',
    `Models: research ${r.models.research}; dramaturgs ${r.models.dramaturg.join(', ')}; critics ${r.models.critic.join(', ')}.`,
    `Cost $${r.cost_usd} · ${r.tokens.toLocaleString()} tokens · ${r.wall_min} min wall time.`, '']
  L.push(r.best ? `**Best fit:** ${r.best.name}, at "${r.best.step}". Fit ${r.best.fit}, change ${r.best.change}, new ${r.best.new}: ${r.best.sum} of 15.` : `**No grounded programme.** ${r.no_programme_reason || ''}`, '')
  for (const p of r.programmes) {
    L.push(`## ${p.n}. ${p.name}${p.grounded ? '' : ' (not grounded: every claim failed its check)'}`, '', `${p.url || ''}`, '', `**Step:** ${p.step}`, '')
    L.push('**Practice claims and checks:**')
    for (const c of p.claims) L.push(`- ${c.verdict.toUpperCase()} [${c.checks.join(', ')}] ${c.claim} (${c.url})`)
    L.push('', `**Activity:** ${(p.activity || {}).state || 'not given'} [${((p.activity || {}).checks || []).join(', ') || 'no source'}] ${(p.activity || {}).claim || ''}`)
    if (p.flags && p.flags.step_restates_card) L.push('', '**Flag:** the step is put in the card\'s terms, or no checker found it on the programme\'s page.')
    if (p.caps && p.caps.length) L.push('', `**Caps applied:** ${p.caps.join('; ')}`)
    L.push('', `**If the lever:** ${p.if_lever_changes}`, '', `**If not:** ${p.if_not_changes}`, '', `**Already done:** ${p.already_done.status} [${p.already_done.checks.join(', ') || 'no source'}] ${p.already_done.claim || ''}`, '')
    if (p.scores) {
      L.push('| Criterion | Median | Scores | Spread |', '|---|---|---|---|')
      for (const c of ['fit', 'change', 'new']) L.push(`| ${c} | ${p.scores[c].median} | ${p.scores[c].values.map(v => v ?? '—').join(', ')} | ${p.scores[c].spread ?? '—'} |`)
      L.push('')
      for (const c of ['fit', 'change', 'new']) for (const why of p.scores[c].reasons) L.push(`- ${c}, ${why}`)
      L.push('')
    }
  }
  if (r.gaps.length) L.push('## Gaps named by the researcher', '', ...r.gaps.map(g => `- ${g}`), '')
  if (r.failed_calls.length) L.push('## Failed calls', '', ...r.failed_calls.map(c => `- ${c.id} (${c.model}): ${c.errors.join('; ')}`), '')
  return L.join('\n')
}

main().catch(e => { status.stage = 'error'; status.error = String(e && e.stack || e); status.done = true; saveStatus(); console.error(e); process.exit(1) })
