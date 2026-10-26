#!/usr/bin/env node
'use strict'
// Runs a Workflow-tool script (../dist/question_tree_v2.js, ../dist/replay_v2.js, or latent_skeptic's pipeline.js and
// triage_workflow.js) outside Claude Code: agent() calls use OpenCode Go (oc.js), Claude headless (claude_cli.js),
// Codex CLI (codex_cli.js), or Cursor Agent (cursor_cli.js), with an ordered understudy chain (understudy.js).
//
// usage: node wf.js --args args.json [--script ../dist/question_tree_v2.js] [--name label] [--out dir]
//                   [--resume <earlier run dir>] [--main provider/model] [--cheap provider/model]
//                   [--family opencode|claude|codex|cursor] [--mode fallback|shadow|swap|primary-only] [--on-refusal halt|understudy]
//                   [--disable-family opencode|claude|codex|cursor] (repeatable; adds to config exclusions for this run)
//                   [--chat-prefix x-raid] (or args.chat_prefix; opt-in agent chat names)
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
UCFG.disabled_families = [...new Set([...UCFG.disabled_families, ...argv.flatMap((a, i) => a === '--disable-family' ? [argv[i + 1]] : [])])]
UCFG.families.opencode.models = { strong: MAIN, main: MAIN, cheap: CHEAP, ...(UCFG.families.opencode.models || {}) }
if (opt('main')) UCFG.families.opencode.models.strong = UCFG.families.opencode.models.main = MAIN
if (opt('cheap')) UCFG.families.opencode.models.cheap = CHEAP
UCFG.families.opencode.by_role = { ...(CFG.by_role || {}), ...(UCFG.families.opencode.by_role || {}) }
const FAMILY = opt('family', null), MODE = opt('mode', null), PROFILE = opt('profile', 'metis')
for (const [k, v, ok] of [['family', FAMILY, ['opencode', 'claude', 'codex', 'cursor', null]], ['mode', MODE, ['fallback', 'shadow', 'swap', 'primary-only', null]], ['on-refusal', UCFG.on_refusal, ['halt', 'understudy']], ...UCFG.disabled_families.map(f => ['disable-family', f, ['opencode', 'claude', 'codex', 'cursor']])])
  if (!ok.includes(v)) { console.error(`--${k} must be one of ${ok.filter(Boolean).join(', ')}`); process.exit(2) }
try { U.resolve({ ...UCFG, routes: [] }, { familyOverride: FAMILY, modeOverride: MODE }) }
catch (e) { console.error(e.message); process.exit(2) }
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
const version = family => UCFG.disabled_families.includes(family) ? null : sh(family === 'cursor' ? 'cursor-agent' : family, ['--version'])
const runInfo = {
  name: NAME, run_dir: RUN, script: SCRIPT, script_sha256: sha(src), args: ARGS,
  models: { main: MAIN, cheap: CHEAP, by_role: UCFG.families.opencode.by_role },
  understudy: { primary_family: FAMILY || UCFG.primary_family, disabled_families: UCFG.disabled_families, mode: MODE || UCFG.mode, on_refusal: UCFG.on_refusal, retry_on: UCFG.retry_on, profile: PROFILE, families: UCFG.families, chain: UCFG.chain, routes: UCFG.routes },
  opencode_version: version('opencode'), claude_version: version('claude'), codex_version: version('codex'), cursor_version: version('cursor'), node: process.version,
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
const cacheModels = new Map()
const resumeDir = opt('resume')
if (resumeDir) for (const l of fs.readFileSync(path.join(resumeDir, 'journal.jsonl'), 'utf8').split('\n')) {
  if (!l.trim()) continue
  const r = JSON.parse(l)
  if (r.type === 'result' && r.key && !UCFG.disabled_families.includes(U.familyOf(r.model))) {
    cache.set(r.key, r.value); cacheModels.set(r.key, r.model)
  }
}

// ---------- concurrency ----------
let active = 0
const waiting = []
const acquire = () => new Promise(res => { if (active < CFG.max_concurrency) { active++; res() } else waiting.push(res) })
const release = () => { const next = waiting.shift(); if (next) next(); else active-- }

const FILE_ROLES = new Set(['qt-research', 'qt-producer', 'qt-extract'])
const WRITING_ROLES = new Set(['qt-research', 'qt-producer', 'triage-author', 'ls-builder', 'ls-writer'])   // roles that write files where the script says
// before an understudy runs for a writing role: copy every existing file the primary's reply names into <dir>/primary-files/
function snapshot(value, cwd, dir) {
  const kept = []
  for (const t of U.fileTokens(value || {})) {
    const p = path.isAbsolute(t) ? t : path.join(cwd, t)
    if (fs.existsSync(p) && fs.statSync(p).isFile()) { fs.mkdirSync(path.join(dir, 'primary-files'), { recursive: true }); fs.copyFileSync(p, path.join(dir, 'primary-files', path.basename(p))); kept.push(p) }
  }
  return kept
}
let counter = 0
const chatGroups = new Map()
const usage = { calls: 0, tokens_in: 0, tokens_out: 0, unknown: 0 }
agent.usage = () => ({ ...usage })
agent.journal = J
const slug = value => String(value).toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '') || 'agent'

// one model's attempt at a call: up to two turns (the second repairs a reply that could not be used); the accounting
// lands on the call's status record and on the model's and family's totals
async function callModel({ model, role, label, full, opts, dir, cwd, rec, repairable, declinedIf, chat, fallback = false }) {
  const fam = U.familyOf(model)
  const sub = fam !== 'opencode' ? { tools: U.claudeTools(UCFG, role), systemPrompt: rolePrompt(role), addDirs: [ARGS.base, ...(ARGS.cwd ? [ARGS.cwd] : []), ...(ARGS.add_dirs || [])] } : {}
  const timeoutMs = (CFG.timeouts_min[role] || UCFG.timeouts_min[role] || 20) * 60000
  let res = null, errors = [], session = null, value = null, attempts = 0
  try {
    for (let attempt = 1; attempt <= 2; attempt++) {
      if (UCFG.disabled_families.includes(fam)) throw new Error(`family disabled: ${fam}`)
      attempts = attempt
      const repair = `Your reply could not be used: ${errors.slice(0, 15).join('; ')}. Reply again with only the JSON value asked for, complete.`
      const p = attempt === 1 ? full : (session && fam === 'opencode' ? repair : `${full}\n\n${repair}`)
      const raw = fam === 'claude' ? `claude-${attempt}.json` : fam === 'codex' ? `codex-${attempt}.jsonl` : 'events.jsonl'
      const retry = (opts.retry || 0) + attempt - 1
      const name = chat && [chat.base, ...(chat.group.count > 1 ? [`${chat.index}of${chat.group.count}`] : []), ...(retry ? [`retry${retry}`] : []), ...(fallback ? ['fb'] : [])].join('-')
      usage.calls++; usage.unknown++
      res = await runner.run({ model, agent: role, role, prompt: p, cwd, session, timeoutMs, rawPath: path.join(dir, raw), httpLogDir: path.join(dir, 'http'), title: label, ...(name ? { name } : {}), ...sub })
      const known = res.tokens_known !== false && Number.isInteger(res.tokens?.input) && Number.isInteger(res.tokens?.output)
      if (known) { usage.unknown--; usage.tokens_in += res.tokens.input; usage.tokens_out += res.tokens.output }
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
      if (res.refusal || !repairable || errors.some(e => e.startsWith('runner error: usage limit'))) break   // no repair after refusal or quota exhaustion
    }
  } catch (e) { errors = [`runner error: ${e.message}`] }
  let kind = U.classify(res, errors)
  if (kind === 'none' && declinedIf && U.declined(declinedIf, value, p => fs.existsSync(path.isAbsolute(p) ? p : path.join(cwd, p)))) {
    kind = 'declined'; errors = ['declined: the reply names no existing file (declined_if no_files)']; value = null
  }
  if (kind !== 'none') { const bm = status.by_model[model]; if (bm) { bm.failed++; if (kind === 'refusal') bm.refusals++ } const bf = status.by_family[fam]; if (bf) { bf.failed++; if (kind === 'refusal') bf.refusals++ } }
  if (kind === 'refusal') status.refusals++
  if (!UCFG.disabled_families.includes(fam)) await runner.exportSession(model, session, path.join(dir, 'export.json'))
  fs.writeFileSync(path.join(dir, 'reply.txt'), (res && res.text) || '')
  fs.writeFileSync(path.join(dir, 'meta.json'), JSON.stringify({ label, role, model, family: fam, attempts, ms: rec.ms, cost_usd: rec.cost_usd, tokens: res && res.tokens, tools: res && res.tools, errors, kind, session }, null, 1))
  return { res, errors, value, attempts, kind, model }
}

async function agent(prompt, opts = {}) {
  const label = opts.label || `agent-${counter + 1}`
  // label rules (config.workflow.label_rules): a panel runs the call on several models and merges the replies;
  // a model rule sends that call to another model (e.g. the second dramaturg to another family)
  const rule = (CFG.label_rules || []).find(r => new RegExp(r.match).test(label))
  if (rule && rule.panel && opts.repairable !== false) {
    const replies = await Promise.all(rule.panel.map(m => agent(prompt, { ...opts, label: `${label}@${m.split('/').pop()}`, _model: m })))
    const merged = MERGE[rule.merge](replies)
    journal({ type: 'panel', label, members: rule.panel, ok: replies.map(Boolean), value: merged })
    return merged
  }
  const n = ++counter
  const prefix = opt('chat-prefix', opts.chat_prefix || ARGS.chat_prefix)
  let chat = null
  if (prefix) {
    const base = `${prefix}-${slug(label)}`, key = JSON.stringify([opts.phase || status.stage, base])
    const group = chatGroups.get(key) || { count: 0 }
    chatGroups.set(key, group)
    chat = { base, group, index: ++group.count }
  }
  const role = U.roleFor(UCFG, PROFILE, { label, agentType: opts.agentType })
  const r = U.resolve(UCFG, { label, role, pinned: opts.model, familyOverride: FAMILY, modeOverride: MODE, primaryOverride: opts._model || (rule && rule.model) })
  const { primary, understudy, chain } = r
  let mode = r.mode
  // Single-response calls may fail over on transport errors, but never solicit replacement ballots.
  if (opts.repairable === false && mode === 'shadow') mode = 'fallback'
  if (mode === 'shadow' && WRITING_ROLES.has(role)) { mode = 'fallback'; journal({ type: 'log', m: `${label}: shadow mode refused for writing role ${role} (both families would write the same files); fallback` }) }
  const full = opts.schema ? prompt + promptSuffix(opts.schema) : String(prompt)
  const key = sha(JSON.stringify({ full, role, model: primary }))
  const rec = { id: `${String(n).padStart(4, '0')} ${label}`, stage: opts.phase || '', model: primary, understudy, chain, mode, state: 'queued', attempts: 0, ms: 0, cost_usd: 0, tokens: 0 }
  status.calls.push(rec)
  journal({ type: 'started', n, label, phase: opts.phase, role, model: primary, understudy, chain, mode, tier: r.tier, route: r.route, key })
  if (!opts.fresh && cache.has(key)) {
    rec.state = 'cached'; saveStatus(); journal({ type: 'cached', n, label, key, model: cacheModels.get(key) })
    return cache.get(key)
  }
  await acquire()
  rec.state = 'running'; saveStatus()
  const dir = path.join(RUN, 'agents', `${String(n).padStart(4, '0')}-${label.replace(/[^A-Za-z0-9._-]+/g, '_').slice(0, 80)}`)
  fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(path.join(dir, 'prompt.md'), full)
  const cwd = (FILE_ROLES.has(role) || /^(ls-|triage-)/.test(role)) ? (ARGS.cwd || ARGS.base) : path.join(dir, 'cwd')
  fs.mkdirSync(cwd, { recursive: true })
  const common = { role, label, full, opts, cwd, rec, repairable: opts.repairable !== false, declinedIf: r.declined_if, chat }
  let first, second = null, producer = null, value = null, errors = [], attempts = 0
  if (mode === 'shadow' && understudy) {
    const udir = path.join(dir, 'understudy'); fs.mkdirSync(udir, { recursive: true })
    const urec = { ms: 0, cost_usd: 0, tokens: 0 }
    ;[first, second] = await Promise.all([callModel({ ...common, model: primary, dir }), callModel({ ...common, model: understudy, dir: udir, rec: urec, fallback: true })])
    const agree = first.kind === 'none' && second.kind === 'none' && JSON.stringify(first.value) === JSON.stringify(second.value)
    const differ = (first.kind === 'none' && second.kind === 'none' && first.value && typeof first.value === 'object' && second.value && typeof second.value === 'object')
      ? [...new Set([...Object.keys(first.value), ...Object.keys(second.value)])].filter(k => JSON.stringify(first.value[k]) !== JSON.stringify(second.value[k])) : null
    const row = { n, label, role, primary: { model: primary, kind: first.kind, attempts: first.attempts, ms: rec.ms, cost_usd: rec.cost_usd, len: JSON.stringify(first.value || '').length }, understudy: { model: understudy, kind: second.kind, attempts: second.attempts, ms: urec.ms, cost_usd: urec.cost_usd, len: JSON.stringify(second.value || '').length }, agree, fields_differ: differ }
    shadowLog({ ...row, primary_value: first.value, understudy_value: second.value })
    journal({ type: 'shadow', ...row })
    rec.ms += urec.ms; rec.cost_usd += urec.cost_usd; rec.tokens += urec.tokens
    attempts = first.attempts + second.attempts
    rec.shadow = { understudy_kind: second.kind, agree }
    if (first.kind === 'none') { producer = primary; value = first.value }
    else if (second.kind === 'none' && U.handover(UCFG, mode, first.kind)) { producer = understudy; value = second.value; errors = []; rec.substituted = true; status.substitutions++; journal({ type: 'understudy', n, label, from: U.familyOf(primary), from_model: primary, kind: first.kind, errors: first.errors, to: U.familyOf(understudy), to_model: understudy, ok: true, shadow: true }) }
    else errors = first.errors
  } else {
    first = await callModel({ ...common, model: primary, dir })
    attempts = first.attempts
    if (first.kind === 'none') { producer = primary; value = first.value }
    errors = first.errors
    let previous = first, previousDir = dir
    for (const [i, model] of chain.entries()) {
      if (!common.repairable && ['schema', 'nojson'].includes(previous.kind)) break
      if (!U.handover(UCFG, mode, previous.kind)) break
      const udir = path.join(dir, i === 0 ? 'understudy' : `understudy-${i + 1}`); fs.mkdirSync(udir, { recursive: true })
      const kept = WRITING_ROLES.has(role) ? snapshot(previous.res && (opts.schema ? previous.res.json : previous.res.text), cwd, previousDir) : []
      rec.state = 'understudy'; saveStatus()
      const urec = { ms: 0, cost_usd: 0, tokens: 0 }
      second = await callModel({ ...common, model, dir: udir, rec: urec, fallback: true })
      attempts += second.attempts
      rec.ms += urec.ms; rec.cost_usd += urec.cost_usd; rec.tokens += urec.tokens
      rec.understudy_cost_usd = (rec.understudy_cost_usd || 0) + urec.cost_usd; rec.understudy_ms = (rec.understudy_ms || 0) + urec.ms
      journal({ type: 'understudy', n, label, from: U.familyOf(previous.model), from_model: previous.model, kind: previous.kind, errors: previous.errors, to: U.familyOf(model), to_model: model, ok: second.kind === 'none', understudy_kind: second.kind, primary_files_kept: kept.length, understudy_ms: urec.ms, understudy_cost_usd: urec.cost_usd })
      errors = second.errors
      if (second.kind === 'none') { producer = model; value = second.value; rec.substituted = true; status.substitutions++; break }
      previous = second; previousDir = udir
    }
  }
  rec.kind = first.kind; rec.by = producer; rec.attempts = attempts
  const finalKind = mode === 'shadow' ? first.kind : (second || first).kind
  rec.state = errors.length ? (finalKind === 'refusal' && !producer ? 'refused' : 'failed') : 'ok'; rec.errors = errors
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
