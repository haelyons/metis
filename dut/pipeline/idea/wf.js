#!/usr/bin/env node
'use strict'
// Runs a Workflow-tool script (../dist/question_tree_v2.js, ../dist/replay_v2.js, or latent_skeptic's pipeline.js and
// triage_workflow.js) outside Claude Code: every agent() call is served by a model of one of two families, OpenCode Go
// models (oc.js, isolated config in ./ocx) or Claude models headless (claude_cli.js), with the other family as its
// understudy (understudy.js). Same script, same prompts, same gates in either family.
//
// usage: node wf.js --args args.json [--script ../dist/question_tree_v2.js] [--name label] [--out dir]
//                   [--resume <earlier run dir>] [--main provider/model] [--cheap provider/model]
//                   [--family opencode|claude] [--mode fallback|shadow|swap|primary-only] [--on-refusal halt|understudy]
//                   [--profile metis|latent_skeptic]
// args.base "auto" (or missing) puts the pipeline's own files under <run dir>/work; args.cwd is the working directory
// of file-writing roles when the script writes into an existing folder (latent_skeptic stages).
//
// Run directory (full record of the run):
//   run.json       script and its sha256, args, models, understudy policy, versions, git commit, totals by model and family
//   journal.jsonl  every agent call (started / result with its returned value / failed / cached / understudy / shadow),
//                  every nested workflow, every log line
//   shadow.jsonl   in shadow mode: primary and understudy outcomes of each call side by side
//   status.json    live progress (node status.js reads it)
//   agents/NNNN-<label>/  prompt.md (exact text sent, schema included), events.jsonl or claude-N.json (raw runner
//                  output), export.json (OpenCode session), reply.txt, meta.json (role, models, attempts, errors,
//                  tokens, cost, kind), http/ (OpenCode provider requests, key redacted), understudy/ (same for the
//                  understudy when it ran)
//   result.json, RESULT.md, UNDERSTUDY.md   the script's return value, its result_md, the substitution report
const fs = require('node:fs')
const path = require('node:path')
const crypto = require('node:crypto')
const { execFileSync } = require('node:child_process')
const runner = require('./runner.js')
const U = require('./understudy.js')
const { validate, promptSuffix } = require('./schema.js')
const { mergeCritique } = require('./panel.js')
const MERGE = { critique: mergeCritique }

const argv = process.argv.slice(2)
const opt = (k, d) => { const i = argv.indexOf(`--${k}`); return i >= 0 ? argv[i + 1] : d }
const CFG_ALL = JSON.parse(fs.readFileSync(opt('config', path.join(__dirname, 'config.json')), 'utf8'))
const CFG = CFG_ALL.workflow
const MAIN = opt('main', CFG.main_model), CHEAP = opt('cheap', CFG.cheap_model)
const UCFG = U.withDefaults({ ...(CFG_ALL.understudy || {}), ...(opt('on-refusal') ? { on_refusal: opt('on-refusal') } : {}) })
UCFG.families.opencode.models = { strong: MAIN, main: MAIN, cheap: CHEAP, ...(UCFG.families.opencode.models || {}) }
if (opt('main')) UCFG.families.opencode.models.strong = UCFG.families.opencode.models.main = MAIN
if (opt('cheap')) UCFG.families.opencode.models.cheap = CHEAP
UCFG.families.opencode.by_role = { ...(CFG.by_role || {}), ...(UCFG.families.opencode.by_role || {}) }
const FAMILY = opt('family', null), MODE = opt('mode', null), PROFILE = opt('profile', 'metis')
for (const [k, v, ok] of [['family', FAMILY, ['opencode', 'claude', null]], ['mode', MODE, ['fallback', 'shadow', 'swap', 'primary-only', null]], ['on-refusal', UCFG.on_refusal, ['halt', 'understudy']]])
  if (!ok.includes(v)) { console.error(`--${k} must be one of ${ok.filter(Boolean).join(', ')}`); process.exit(2) }
const SCRIPT = path.resolve(opt('script', path.join(__dirname, '..', 'dist', 'question_tree_v2.js')))
const ARGS = JSON.parse(fs.readFileSync(opt('args'), 'utf8'))
const NAME = opt('name', path.basename(opt('args')).replace(/\.json$/, ''))
const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\..*/, '').replace('T', '-')
fs.mkdirSync(path.join(path.resolve(opt('out', path.join(CFG.runs_dir, NAME, stamp))), 'agents'), { recursive: true })
// real path: OpenCode compares file paths with its working directory, so no symlinks in either
const RUN = fs.realpathSync(path.resolve(opt('out', path.join(CFG.runs_dir, NAME, stamp))))
if (!ARGS.base || ARGS.base === 'auto') ARGS.base = path.join(RUN, 'work')
fs.mkdirSync(ARGS.base, { recursive: true })

const src = fs.readFileSync(SCRIPT, 'utf8')
const sha = s => crypto.createHash('sha256').update(s).digest('hex')
const sh = (cmd, a) => { try { return execFileSync(cmd, a, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'] }).trim() } catch { return null } }
const repo = sh('git', ['-C', __dirname, 'rev-parse', '--show-toplevel'])
const OCX_CFG = (() => { try { return JSON.parse(fs.readFileSync(path.join(__dirname, 'ocx', 'opencode', 'opencode.json'), 'utf8')) } catch { return {} } })()
const rolePrompt = role => ((OCX_CFG.agent || {})[role] || {}).prompt || null
const runInfo = {
  name: NAME, run_dir: RUN, script: SCRIPT, script_sha256: sha(src), args: ARGS,
  models: { main: MAIN, cheap: CHEAP, by_role: UCFG.families.opencode.by_role },
  understudy: { primary_family: FAMILY || UCFG.primary_family, mode: MODE || UCFG.mode, on_refusal: UCFG.on_refusal, retry_on: UCFG.retry_on, profile: PROFILE, families: UCFG.families, routes: UCFG.routes },
  opencode_version: sh('opencode', ['--version']), claude_version: sh('claude', ['--version']), node: process.version,
  git: repo && { repo, commit: sh('git', ['-C', repo, 'rev-parse', 'HEAD']), dirty: !!sh('git', ['-C', repo, 'status', '--porcelain']) },
  ocx_config: OCX_CFG, started: new Date().toISOString(),
}
fs.writeFileSync(path.join(RUN, 'run.json'), JSON.stringify(runInfo, null, 1))

// ---------- journal, status, totals ----------
const J = path.join(RUN, 'journal.jsonl')
const journal = o => fs.appendFileSync(J, JSON.stringify({ ts: new Date().toISOString(), ...o }) + '\n')
const shadowLog = o => fs.appendFileSync(path.join(RUN, 'shadow.jsonl'), JSON.stringify({ ts: new Date().toISOString(), ...o }) + '\n')
const status = { card: NAME, kind: 'workflow', run_dir: RUN, stage: 'start', started: runInfo.started, calls: [], cost_usd: 0, tokens: 0, by_model: {}, by_family: {}, substitutions: 0, refusals: 0, done: false }
const saveStatus = () => { status.updated = new Date().toISOString(); fs.writeFileSync(path.join(RUN, 'status.json.tmp'), JSON.stringify(status, null, 1)); fs.renameSync(path.join(RUN, 'status.json.tmp'), path.join(RUN, 'status.json')) }
saveStatus()

// ---------- resume cache: same prompt, role and primary model -> the stored value ----------
const cache = new Map()
const resumeDir = opt('resume')
if (resumeDir) for (const l of fs.readFileSync(path.join(resumeDir, 'journal.jsonl'), 'utf8').split('\n')) {
  if (!l.trim()) continue
  const r = JSON.parse(l)
  if (r.type === 'result' && r.key) cache.set(r.key, r.value)
}

// ---------- concurrency ----------
let active = 0
const waiting = []
const acquire = () => new Promise(res => { if (active < CFG.max_concurrency) { active++; res() } else waiting.push(res) })
const release = () => { const next = waiting.shift(); if (next) next(); else active-- }

const FILE_ROLES = new Set(['qt-research', 'qt-producer', 'qt-extract'])
let counter = 0

// one model's attempt at a call: up to two turns (the second repairs a reply that could not be used); the accounting
// lands on the call's status record and on the model's and family's totals
async function callModel({ model, role, label, full, opts, dir, cwd, rec, repairable, declinedIf }) {
  const fam = U.familyOf(model)
  const sub = fam === 'claude' ? { tools: U.claudeTools(UCFG, role), systemPrompt: rolePrompt(role), addDirs: [ARGS.base, ...(ARGS.cwd ? [ARGS.cwd] : []), ...(ARGS.add_dirs || [])] } : {}
  const timeoutMs = (CFG.timeouts_min[role] || UCFG.timeouts_min[role] || 20) * 60000
  let res = null, errors = [], session = null, value = null, attempts = 0
  try {
    for (let attempt = 1; attempt <= 2; attempt++) {
      attempts = attempt
      const repair = `Your reply could not be used: ${errors.slice(0, 15).join('; ')}. Reply again with only the JSON value asked for, complete.`
      const p = attempt === 1 ? full : (session && fam !== 'claude' ? repair : `${full}\n\n${repair}`)
      res = await runner.run({ model, agent: role, role, prompt: p, cwd, session, timeoutMs, rawPath: path.join(dir, fam === 'claude' ? `claude-${attempt}.json` : 'events.jsonl'), httpLogDir: path.join(dir, 'http'), title: label, ...sub })
      session = res.sessionID
      const tok = res.tokens.input + res.tokens.output + res.tokens.reasoning
      rec.ms += res.ms; rec.cost_usd += res.cost; rec.tokens += tok
      status.cost_usd += res.cost; status.tokens += tok
      const bm = status.by_model[model] = status.by_model[model] || { calls: 0, cost_usd: 0, tokens: 0, failed: 0, refusals: 0 }
      bm.calls += attempt === 1 ? 1 : 0; bm.cost_usd += res.cost; bm.tokens += tok
      const bf = status.by_family[fam] = status.by_family[fam] || { calls: 0, cost_usd: 0, tokens: 0, failed: 0, refusals: 0 }
      bf.calls += attempt === 1 ? 1 : 0; bf.cost_usd += res.cost; bf.tokens += tok
      if (res.errors.length) errors = res.errors
      else if (opts.schema) errors = res.json == null ? [res.jsonError || 'no JSON value found in the reply'] : validate(opts.schema, res.json)
      else errors = []
      if (!errors.length) { value = opts.schema ? res.json : res.text; break }
      if (res.refusal || !repairable) break   // no repair turn after a refusal
    }
  } catch (e) { errors = [`runner error: ${e.message}`] }
  let kind = U.classify(res, errors)
  if (kind === 'none' && declinedIf && U.declined(declinedIf, value, p => fs.existsSync(path.isAbsolute(p) ? p : path.join(cwd, p)))) {
    kind = 'declined'; errors = ['declined: the reply names no existing file (declined_if no_files)']; value = null
  }
  if (kind !== 'none') { const bm = status.by_model[model]; if (bm) { bm.failed++; if (kind === 'refusal') bm.refusals++ } const bf = status.by_family[fam]; if (bf) { bf.failed++; if (kind === 'refusal') bf.refusals++ } }
  if (kind === 'refusal') status.refusals++
  await runner.exportSession(model, session, path.join(dir, 'export.json'))
  fs.writeFileSync(path.join(dir, 'reply.txt'), (res && res.text) || '')
  fs.writeFileSync(path.join(dir, 'meta.json'), JSON.stringify({ label, role, model, family: fam, attempts, ms: rec.ms, cost_usd: rec.cost_usd, tokens: res && res.tokens, tools: res && res.tools, errors, kind, session }, null, 1))
  return { res, errors, value, attempts, kind, model }
}

async function agent(prompt, opts = {}) {
  const label = opts.label || `agent-${counter + 1}`
  // label rules (config.workflow.label_rules): a panel runs the call on several models and merges the replies;
  // a model rule sends that call to another model (e.g. the second dramaturg to another family)
  const rule = (CFG.label_rules || []).find(r => new RegExp(r.match).test(label))
  if (rule && rule.panel) {
    const replies = await Promise.all(rule.panel.map(m => agent(prompt, { ...opts, label: `${label}@${m.split('/').pop()}`, _model: m })))
    const merged = MERGE[rule.merge](replies)
    journal({ type: 'panel', label, members: rule.panel, ok: replies.map(Boolean), value: merged })
    return merged
  }
  const n = ++counter
  const role = U.roleFor(UCFG, PROFILE, { label, agentType: opts.agentType })
  const r = U.resolve(UCFG, { label, role, pinned: opts.model, familyOverride: FAMILY, modeOverride: MODE })
  const primary = opts._model || (rule && rule.model) || r.primary
  const understudy = U.familyOf(primary) === U.familyOf(r.understudy) ? U.resolve(UCFG, { label, role, pinned: opts.model, familyOverride: U.otherFamily(U.familyOf(primary)) }).primary : r.understudy
  const mode = r.mode
  const full = opts.schema ? prompt + promptSuffix(opts.schema) : String(prompt)
  const key = sha(JSON.stringify({ full, role, model: primary }))
  const rec = { id: `${String(n).padStart(4, '0')} ${label}`, stage: opts.phase || '', model: primary, understudy, mode, state: 'queued', attempts: 0, ms: 0, cost_usd: 0, tokens: 0 }
  status.calls.push(rec)
  journal({ type: 'started', n, label, phase: opts.phase, role, model: primary, understudy, mode, tier: r.tier, route: r.route, key })
  if (cache.has(key)) {
    rec.state = 'cached'; saveStatus(); journal({ type: 'cached', n, label, key })
    return cache.get(key)
  }
  await acquire()
  rec.state = 'running'; saveStatus()
  const dir = path.join(RUN, 'agents', `${String(n).padStart(4, '0')}-${label.replace(/[^A-Za-z0-9._-]+/g, '_').slice(0, 80)}`)
  fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(path.join(dir, 'prompt.md'), full)
  const cwd = (FILE_ROLES.has(role) || /^(ls-|triage-)/.test(role)) ? (ARGS.cwd || ARGS.base) : path.join(dir, 'cwd')
  fs.mkdirSync(cwd, { recursive: true })
  const common = { role, label, full, opts, cwd, rec, repairable: true, declinedIf: r.declined_if }
  let first, second = null, producer = null, value = null, errors = []
  if (mode === 'shadow' && understudy) {
    const udir = path.join(dir, 'understudy'); fs.mkdirSync(udir, { recursive: true })
    const urec = { ms: 0, cost_usd: 0, tokens: 0 }
    ;[first, second] = await Promise.all([callModel({ ...common, model: primary, dir }), callModel({ ...common, model: understudy, dir: udir, rec: urec })])
    const agree = first.kind === 'none' && second.kind === 'none' && JSON.stringify(first.value) === JSON.stringify(second.value)
    const differ = (first.kind === 'none' && second.kind === 'none' && first.value && typeof first.value === 'object' && second.value && typeof second.value === 'object')
      ? [...new Set([...Object.keys(first.value), ...Object.keys(second.value)])].filter(k => JSON.stringify(first.value[k]) !== JSON.stringify(second.value[k])) : null
    const row = { n, label, role, primary: { model: primary, kind: first.kind, attempts: first.attempts, ms: rec.ms, cost_usd: rec.cost_usd, len: JSON.stringify(first.value || '').length }, understudy: { model: understudy, kind: second.kind, attempts: second.attempts, ms: urec.ms, cost_usd: urec.cost_usd, len: JSON.stringify(second.value || '').length }, agree, fields_differ: differ }
    shadowLog({ ...row, primary_value: first.value, understudy_value: second.value })
    journal({ type: 'shadow', ...row })
    rec.shadow = { understudy_kind: second.kind, agree }
    if (first.kind === 'none') { producer = primary; value = first.value }
    else if (second.kind === 'none' && U.handover(UCFG, mode, first.kind)) { producer = understudy; value = second.value; errors = []; rec.substituted = true; status.substitutions++; journal({ type: 'understudy', n, label, from: primary, kind: first.kind, errors: first.errors, to: understudy, ok: true, shadow: true }) }
    else errors = first.errors
  } else {
    first = await callModel({ ...common, model: primary, dir })
    if (first.kind === 'none') { producer = primary; value = first.value }
    else if (understudy && U.handover(UCFG, mode, first.kind)) {
      const udir = path.join(dir, 'understudy'); fs.mkdirSync(udir, { recursive: true })
      rec.state = 'understudy'; saveStatus()
      second = await callModel({ ...common, model: understudy, dir: udir })
      journal({ type: 'understudy', n, label, from: primary, kind: first.kind, errors: first.errors, to: understudy, ok: second.kind === 'none', understudy_kind: second.kind })
      if (second.kind === 'none') { producer = understudy; value = second.value; rec.substituted = true; status.substitutions++ }
      else errors = second.errors
    } else errors = first.errors
  }
  rec.kind = first.kind; rec.by = producer; rec.attempts = first.attempts + (second ? second.attempts : 0)
  if (first.kind === 'refusal' && !producer) rec.state = 'refused'
  rec.state = errors.length ? (first.kind === 'refusal' && !producer ? 'refused' : 'failed') : 'ok'; rec.errors = errors
  journal(errors.length ? { type: 'failed', n, label, key, model: primary, kind: first.kind, understudy_kind: second ? second.kind : null, errors } : { type: 'result', n, label, key, model: producer, substituted: !!rec.substituted, value })
  saveStatus()
  release()
  return errors.length ? null : value
}

const parallel = xs => Promise.all(xs.map(x => Promise.resolve().then(() => (typeof x === 'function' ? x() : x)).catch(e => { log(`parallel: ${e && e.message || e}`); return null })))
const pipeline = (items, ...stages) => parallel(items.map(it => async () => { let v = it; for (const s of stages) v = await s(v); return v }))
const log = m => { console.log(`[${NAME}] ${m}`); journal({ type: 'log', m: String(m) }) }
const phase = t => { status.stage = t; saveStatus(); journal({ type: 'phase', t }) }
const budget = { total: null, spent: () => status.tokens, remaining: () => Infinity }

// a script body with the Workflow tool's globals; workflow() runs another script file one level deep
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
async function runScript(file, args, depth) {
  const body = fs.readFileSync(file, 'utf8').replace(/^export const meta\s*=/m, 'const meta =')
  const workflow = depth > 0
    ? () => { throw new Error('workflow() nesting is one level only') }
    : async (ref, a) => {
      const f = path.resolve(path.dirname(file), typeof ref === 'string' ? ref : ref.scriptPath)
      journal({ type: 'workflow', file: f, sha256: sha(fs.readFileSync(f, 'utf8')), depth: depth + 1 })
      return runScript(f, a, depth + 1)
    }
  return new AsyncFunction('args', 'agent', 'parallel', 'log', 'phase', 'pipeline', 'workflow', 'budget', body)(args, agent, parallel, log, phase, pipeline, workflow, budget)
}

function goReport() {
  const caps = CFG_ALL.go_monthly_caps_usd || {}
  return Object.entries(status.by_model).map(([m, v]) => {
    const cap = caps[m.split('/').pop()]
    return `${m}: $${v.cost_usd.toFixed(3)} over ${v.calls} calls${v.failed ? `, ${v.failed} failed` : ''}${v.refusals ? `, ${v.refusals} refused` : ''}${cap ? ` = ${(100 * v.cost_usd / cap).toFixed(1)}% of its $${cap} monthly cap, ${(100 * v.cost_usd / (cap * 0.2)).toFixed(1)}% of a 5-hour window` : ''}`
  })
}

;(async () => {
  let result
  try { result = await runScript(SCRIPT, ARGS, 0) }
  catch (e) { result = { error: `script threw: ${e && e.stack || e}` } }
  fs.writeFileSync(path.join(RUN, 'result.json'), JSON.stringify(result, null, 1))
  if (result && typeof result.result_md === 'string') fs.writeFileSync(path.join(RUN, 'RESULT.md'), result.result_md)
  status.stage = 'done'; status.done = true; status.error = result && result.error; status.go = goReport(); saveStatus()
  runInfo.finished = new Date().toISOString(); runInfo.totals = { cost_usd: status.cost_usd, tokens: status.tokens, calls: counter, by_model: status.by_model, by_family: status.by_family, substitutions: status.substitutions, refusals: status.refusals }
  fs.writeFileSync(path.join(RUN, 'run.json'), JSON.stringify(runInfo, null, 1))
  try { fs.writeFileSync(path.join(RUN, 'UNDERSTUDY.md'), require('./understudy_report.js').report(RUN)) } catch (e) { console.error(`understudy report: ${e.message}`) }
  console.log(`${NAME}: ${result && result.error ? `error: ${result.error}` : 'done'} · $${status.cost_usd.toFixed(3)} · ${status.tokens.toLocaleString()} tokens · ${counter} agent calls · ${status.substitutions} understudy substitution(s) · ${status.refusals} refusal(s)\n${goReport().join('\n')}\n${RUN}`)
})()
