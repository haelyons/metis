#!/usr/bin/env node
'use strict'
// Runs a Workflow-tool script (../dist/question_tree_v2.js, ../dist/replay_v2.js) outside Claude Code: every agent()
// call is served by an OpenCode model under the isolated config in ./ocx. Same script, same prompts, same gates.
//
// usage: node wf.js --args args.json [--script ../dist/question_tree_v2.js] [--name label] [--out dir]
//                   [--resume <earlier run dir>] [--main provider/model] [--cheap provider/model]
// args.base "auto" (or missing) puts the pipeline's own files under <run dir>/work.
//
// Run directory (full record of the run):
//   run.json       script and its sha256, args, models, opencode and node versions, git commit of this repo, totals
//   journal.jsonl  every agent call (started / result with its returned value / failed / cached) and every log line
//   status.json    live progress (node status.js reads it)
//   agents/NNNN-<label>/  prompt.md (exact text sent, schema included), events.jsonl (OpenCode event stream),
//                  export.json (full session: messages, reasoning, tool calls with input and output, tokens, cost),
//                  reply.txt (final text), meta.json (role, model, cwd, attempts, errors, tokens, cost),
//                  http/NNN.request.json + .response.txt (exact provider requests: system prompt, tools, messages; key redacted)
//   result.json, RESULT.md   the script's return value and its result_md
const fs = require('node:fs')
const path = require('node:path')
const crypto = require('node:crypto')
const { execFileSync } = require('node:child_process')
const oc = require('./oc.js')
const { validate, promptSuffix } = require('./schema.js')
const { mergeCritique } = require('./panel.js')
const MERGE = { critique: mergeCritique }

const argv = process.argv.slice(2)
const opt = (k, d) => { const i = argv.indexOf(`--${k}`); return i >= 0 ? argv[i + 1] : d }
const CFG_ALL = JSON.parse(fs.readFileSync(opt('config', path.join(__dirname, 'config.json')), 'utf8'))
const CFG = CFG_ALL.workflow
const MAIN = opt('main', CFG.main_model), CHEAP = opt('cheap', CFG.cheap_model)
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
const runInfo = {
  name: NAME, run_dir: RUN, script: SCRIPT, script_sha256: sha(src), args: ARGS, models: { main: MAIN, cheap: CHEAP, by_role: CFG.by_role },
  opencode_version: sh('opencode', ['--version']), node: process.version,
  git: repo && { repo, commit: sh('git', ['-C', repo, 'rev-parse', 'HEAD']), dirty: !!sh('git', ['-C', repo, 'status', '--porcelain']) },
  ocx_config: JSON.parse(fs.readFileSync(path.join(oc.OCX, 'opencode', 'opencode.json'), 'utf8')), started: new Date().toISOString(),
}
fs.writeFileSync(path.join(RUN, 'run.json'), JSON.stringify(runInfo, null, 1))

// ---------- journal, status, totals ----------
const J = path.join(RUN, 'journal.jsonl')
const journal = o => fs.appendFileSync(J, JSON.stringify({ ts: new Date().toISOString(), ...o }) + '\n')
const status = { card: NAME, kind: 'workflow', run_dir: RUN, stage: 'start', started: runInfo.started, calls: [], cost_usd: 0, tokens: 0, by_model: {}, done: false }
const saveStatus = () => { status.updated = new Date().toISOString(); fs.writeFileSync(path.join(RUN, 'status.json.tmp'), JSON.stringify(status, null, 1)); fs.renameSync(path.join(RUN, 'status.json.tmp'), path.join(RUN, 'status.json')) }
saveStatus()

// ---------- resume cache: same prompt, role and model -> the stored value ----------
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

const SMALL = new Set(['sonnet', 'haiku'])
const FILE_ROLES = new Set(['qt-research', 'qt-producer', 'qt-extract'])
let counter = 0

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
  const role = opts.agentType || 'qt-bare'
  const model = opts._model || (rule && rule.model) || CFG.by_role[role] || (opts.model && SMALL.has(opts.model) ? CHEAP : MAIN)
  const full = opts.schema ? prompt + promptSuffix(opts.schema) : String(prompt)
  const key = sha(JSON.stringify({ full, role, model }))
  const rec = { id: `${String(n).padStart(4, '0')} ${label}`, stage: opts.phase || '', model, state: 'queued', attempts: 0, ms: 0, cost_usd: 0, tokens: 0 }
  status.calls.push(rec)
  journal({ type: 'started', n, label, phase: opts.phase, role, model, key })
  if (cache.has(key)) {
    rec.state = 'cached'; saveStatus(); journal({ type: 'cached', n, label, key })
    return cache.get(key)
  }
  await acquire()
  rec.state = 'running'; saveStatus()
  const dir = path.join(RUN, 'agents', `${String(n).padStart(4, '0')}-${label.replace(/[^A-Za-z0-9._-]+/g, '_').slice(0, 80)}`)
  fs.mkdirSync(dir, { recursive: true })
  fs.writeFileSync(path.join(dir, 'prompt.md'), full)
  const cwd = FILE_ROLES.has(role) ? ARGS.base : path.join(dir, 'cwd')
  fs.mkdirSync(cwd, { recursive: true })
  let res = null, errors = [], session = null, value = null
  try {
    for (let attempt = 1; attempt <= 2; attempt++) {
      rec.attempts = attempt
      const p = attempt === 1 ? full : `Your reply could not be used: ${errors.slice(0, 15).join('; ')}. Reply again with only the JSON value asked for, complete.`
      res = await oc.run({ model, agent: role, prompt: p, cwd, session, timeoutMs: (CFG.timeouts_min[role] || 20) * 60000, rawPath: path.join(dir, 'events.jsonl'), httpLogDir: path.join(dir, 'http'), title: label })
      session = res.sessionID
      const tok = res.tokens.input + res.tokens.output + res.tokens.reasoning
      rec.ms += res.ms; rec.cost_usd += res.cost; rec.tokens += tok
      status.cost_usd += res.cost; status.tokens += tok
      const bm = status.by_model[model] = status.by_model[model] || { calls: 0, cost_usd: 0, tokens: 0 }
      bm.calls += attempt === 1 ? 1 : 0; bm.cost_usd += res.cost; bm.tokens += tok
      if (res.errors.length) errors = res.errors
      else if (opts.schema) errors = res.json == null ? [res.jsonError || 'no JSON value found in the reply'] : validate(opts.schema, res.json)
      else errors = []
      if (!errors.length) { value = opts.schema ? res.json : res.text; break }
    }
  } catch (e) { errors = [`runner error: ${e.message}`] }
  await oc.exportSession(session, path.join(dir, 'export.json'))
  fs.writeFileSync(path.join(dir, 'reply.txt'), (res && res.text) || '')
  fs.writeFileSync(path.join(dir, 'meta.json'), JSON.stringify({ n, label, phase: opts.phase, role, model, opts: { ...opts, schema: !!opts.schema }, cwd, session, attempts: rec.attempts, ms: rec.ms, cost_usd: rec.cost_usd, tokens: res && res.tokens, tools: res && res.tools, errors }, null, 1))
  rec.state = errors.length ? 'failed' : 'ok'; rec.errors = errors
  journal(errors.length ? { type: 'failed', n, label, key, errors } : { type: 'result', n, label, key, value })
  saveStatus()
  release()
  return errors.length ? null : value
}

const parallel = xs => Promise.all(xs.map(x => Promise.resolve().then(() => (typeof x === 'function' ? x() : x)).catch(e => { log(`parallel: ${e && e.message || e}`); return null })))
const pipeline = (items, ...stages) => parallel(items.map(it => async () => { let v = it; for (const s of stages) v = await s(v); return v }))
const log = m => { console.log(`[${NAME}] ${m}`); journal({ type: 'log', m: String(m) }) }
const phase = t => { status.stage = t; saveStatus(); journal({ type: 'phase', t }) }

function goReport() {
  const caps = CFG_ALL.go_monthly_caps_usd || {}
  return Object.entries(status.by_model).map(([m, v]) => {
    const cap = caps[m.split('/').pop()]
    return `${m}: $${v.cost_usd.toFixed(3)} over ${v.calls} calls${cap ? ` = ${(100 * v.cost_usd / cap).toFixed(1)}% of its $${cap} monthly cap, ${(100 * v.cost_usd / (cap * 0.2)).toFixed(1)}% of a 5-hour window` : ''}`
  })
}

;(async () => {
  const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
  const body = src.replace(/^export const meta\s*=/m, 'const meta =')
  let result
  try { result = await new AsyncFunction('args', 'agent', 'parallel', 'log', 'phase', 'pipeline', body)(ARGS, agent, parallel, log, phase, pipeline) }
  catch (e) { result = { error: `script threw: ${e && e.stack || e}` } }
  fs.writeFileSync(path.join(RUN, 'result.json'), JSON.stringify(result, null, 1))
  if (result && typeof result.result_md === 'string') fs.writeFileSync(path.join(RUN, 'RESULT.md'), result.result_md)
  status.stage = 'done'; status.done = true; status.error = result && result.error; status.go = goReport(); saveStatus()
  runInfo.finished = new Date().toISOString(); runInfo.totals = { cost_usd: status.cost_usd, tokens: status.tokens, calls: counter, by_model: status.by_model }
  fs.writeFileSync(path.join(RUN, 'run.json'), JSON.stringify(runInfo, null, 1))
  console.log(`${NAME}: ${result && result.error ? `error: ${result.error}` : 'done'} · $${status.cost_usd.toFixed(3)} · ${status.tokens.toLocaleString()} tokens · ${counter} agent calls\n${goReport().join('\n')}\n${RUN}`)
})()
