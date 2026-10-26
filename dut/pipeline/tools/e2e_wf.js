// End-to-end run of idea/wf.js with a stub runner for all model families (no network, no model): checks the understudy
// policy on a small script with a nested workflow. The same file is the stub module (wf.js loads it through WF_STUB).
// Usage: node tools/e2e_wf.js [mode]   default: all; modes are listed in flags below
//   fallback      opencode primary; 'beta' times out on opencode -> codex answers; 'eta' needs claude; 'gamma' is refused
//                 by opencode and on_refusal halt leaves it null; 'delta' (triage-reader, text) and the nested script run
//   refusal       --on-refusal understudy: 'gamma' is answered by the understudy
//   shadow        --mode shadow: every call runs in the primary and first understudy families; shadow.jsonl compares them
//   claude        --family claude: claude answers everything; no understudy rows
//   primary-only  --mode primary-only: no understudy; 'beta' and 'gamma' are null
'use strict'
const fs = require('node:fs'), path = require('node:path'), os = require('node:os'), { spawnSync } = require('node:child_process')
const ROOT = path.join(__dirname, '..')

// ---- the stub runner: outcome by family and label ----
const fam = m => (/^codex\//.test(m) ? 'codex' : /^cursor\//.test(m) ? 'cursor' : /^claude\//.test(m) ? 'claude' : 'opencode')
const ok = (json, text) => ({ text: text || JSON.stringify(json), json, jsonError: null, sessionID: 'stub', tokens: { input: 10, output: 5, reasoning: 0 }, cost: 0.001, tools: 0, ms: 5, errors: [], refusal: false })
const bad = (errors, refusal) => ({ text: '', json: null, jsonError: null, sessionID: 'stub', tokens: { input: 10, output: 0, reasoning: 0 }, cost: 0.001, tools: 0, ms: 5, errors, refusal: !!refusal })
const stub = {
  calls: [],
  async run({ model, title, prompt, agent, tools, systemPrompt, cwd }) {
    stub.calls.push({ model, title, agent, tools, systemPrompt: !!systemPrompt, repair: /could not be used/.test(prompt) })
    const f = fam(model), label = title
    if (label === 'alpha') return ok({ v: `alpha by ${f}` })
    if (label === 'beta') return f === 'opencode' ? bad(['timeout after 1 min']) : ok({ v: `beta by ${f}` })
    if (label === 'eta') {
      if (f === 'opencode') return bad(['timeout after 1 min'])
      if (f === 'codex') return process.env.E2E_CHAIN_REFUSAL ? bad(['refusal'], true) : bad(['runner error: usage limit'])
      return process.env.E2E_CHAIN_EXHAUSTED ? bad(['exit 1: unavailable']) : ok({ v: `eta by ${f}` })
    }
    if (label === 'writer') {
      const file = path.join(cwd, 'writer.py')
      fs.writeFileSync(file, f)
      if (f !== 'claude') return { ...bad(['$: missing "v"']), json: { runner_py: file } }
      return ok({ v: `writer by ${f}` })
    }
    if (label === 'gamma') return f === 'opencode' ? bad(['refusal'], true) : ok({ v: `gamma by ${f}` })
    if (label === 'delta') return ok(null, `delta text by ${f} as ${agent}`)
    if (label === 'eps') return f === 'opencode' ? bad(['$: missing "v"']) : ok({ v: `eps by ${f}` })   // schema failure -> repair turn -> understudy
    if (label === 'zeta') return f === 'opencode' ? ok({ runner_py: 'STOP: the directive contradicts itself; run_zeta.py was not written', onbox_sh: 'STOP: onbox_zeta.sh not written' }) : ok({ runner_py: `Wrote ${process.env.E2E_EXISTING_FILE} (12 lines).`, onbox_sh: process.env.E2E_EXISTING_FILE })
    if (label.startsWith('nested')) return ok({ v: `${label} by ${f}` })
    return ok({ v: `${label} by ${f}` })
  },
  async exportSession(id, file) { fs.writeFileSync(file, '{}') },
}
module.exports = stub
if (require.main !== module) return

// ---- the driver ----
const S = `{"type":"object","required":["v"],"properties":{"v":{"type":"string"}}}`
const MAIN_SCRIPT = `export const meta = { name: 'understudy-test', description: 'test' }
const S = ${S}
const a = await agent('alpha', { label: 'alpha', schema: S })
const b = await agent('beta', { label: 'beta', schema: S, model: 'sonnet' })
const c = await agent('gamma', { label: 'gamma', schema: S, model: 'opus' })
const d = await agent('delta', { label: 'delta', agentType: 'triage-reader' })
const e = await agent('eps', { label: 'eps', schema: S })
const z = await agent('zeta', { label: 'zeta', schema: { type: 'object', required: ['runner_py', 'onbox_sh'], properties: { runner_py: { type: 'string' }, onbox_sh: { type: 'string' } } } })
const h = await agent('eta', { label: 'eta', schema: S })
if (args.writing) await agent('writer', { label: 'writer', agentType: 'ls-builder', schema: S })
const n = await workflow({ scriptPath: './nested.js' }, { k: 2 })
return { a, b, c, d, e, z, h, n }
`
const NESTED = `export const meta = { name: 'nested', description: 'nested test' }
const x = await agent('n1', { label: 'nested-1', schema: ${S} })
let threw = false
try { await workflow({ scriptPath: './nested.js' }, {}) } catch (e) { threw = true }
return { x, k: args.k, nested_nesting_threw: threw }
`
const want = process.argv[2] || 'all'
const flags = { fallback: [], refusal: ['--on-refusal', 'understudy'], shadow: ['--mode', 'shadow'], claude: ['--family', 'claude'], 'primary-only': ['--mode', 'primary-only'], codex: ['--family', 'codex'], swap: ['--mode', 'swap'],
  exhausted: [], 'chain-refusal': [], writing: ['--mode', 'shadow'] }
const modes = want === 'all' ? Object.keys(flags) : [want]
let failures = 0
const check = (cond, msg) => { if (!cond) { failures++; console.log(`  FAIL ${msg}`) } else console.log(`  ok   ${msg}`) }
const rows = f => fs.readFileSync(f, 'utf8').split('\n').filter(Boolean).map(l => JSON.parse(l))
for (const mode of modes) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `e2e_wf_${mode}_`))
  fs.writeFileSync(path.join(dir, 'main.js'), MAIN_SCRIPT); fs.writeFileSync(path.join(dir, 'nested.js'), NESTED)
  fs.writeFileSync(path.join(dir, 'args.json'), JSON.stringify({ base: 'auto', writing: mode === 'writing' }))
  const cfg = JSON.parse(fs.readFileSync(path.join(ROOT, 'idea', 'config.json'), 'utf8'))
  cfg.understudy.families.opencode.models = { strong: 'opencode-go/stub-pro', main: 'opencode-go/stub-pro', cheap: 'opencode-go/stub-flash' }
  cfg.workflow.main_model = 'opencode-go/stub-pro'; cfg.workflow.cheap_model = 'opencode-go/stub-flash'; cfg.workflow.label_rules = []
  cfg.understudy.routes = [{ match: '^zeta$', declined_if: 'no_files' }]
  fs.writeFileSync(path.join(dir, 'config.json'), JSON.stringify(cfg))
  const out = path.join(dir, 'run')
  const r = spawnSync('node', [path.join(ROOT, 'idea', 'wf.js'), '--script', path.join(dir, 'main.js'), '--args', path.join(dir, 'args.json'), '--out', out, '--config', path.join(dir, 'config.json'), '--profile', 'latent_skeptic', ...flags[mode]],
    { encoding: 'utf8', env: { ...process.env, WF_STUB: __filename, E2E_EXISTING_FILE: path.join(dir, 'main.js'), E2E_CHAIN_REFUSAL: mode === 'chain-refusal' ? '1' : '', E2E_CHAIN_EXHAUSTED: mode === 'exhausted' ? '1' : '' } })
  console.log(`== ${mode} (exit ${r.status})`)
  if (r.status !== 0) { console.log(r.stdout.slice(-800), r.stderr.slice(-1200)); failures++; continue }
  const res = JSON.parse(fs.readFileSync(path.join(out, 'result.json'), 'utf8')), J = rows(path.join(out, 'journal.jsonl'))
  const started = J.filter(x => x.type === 'started'), und = J.filter(x => x.type === 'understudy'), shadow = J.filter(x => x.type === 'shadow')
  const byLabel = Object.fromEntries(started.map(s => [s.label, s]))
  check(started.length === (mode === 'writing' ? 9 : 8), `agent calls started (${started.length})`)
  check(J.some(x => x.type === 'workflow' && x.depth === 1), 'nested workflow journaled at depth 1')
  check(res.n && res.n.k === 2 && res.n.nested_nesting_threw === true, 'nested script ran with its args and a second nesting level threw')
  check(res.a && /alpha by/.test(res.a.v), 'alpha returned')
  check(typeof res.d === 'string' && /as triage-reader/.test(res.d), `delta ran as triage-reader (${JSON.stringify(res.d)})`)
  check(byLabel.gamma.tier === 'strong' && byLabel.beta.tier === 'main', 'pinned opus -> strong tier, sonnet -> main tier')
  if (mode === 'fallback') {
    check(byLabel.alpha.model.startsWith('opencode-go/') && byLabel.alpha.understudy === 'codex/default@medium', `opencode primary, codex understudy (${byLabel.alpha.model} / ${byLabel.alpha.understudy})`)
    check(byLabel.gamma.understudy === 'codex/default@high', `strong tier understudy is codex/default@high (${byLabel.gamma.understudy})`)
    check(res.b && /beta by codex/.test(res.b.v), 'beta answered by the codex understudy after the opencode timeout')
    check(res.c === null, 'gamma refused by opencode and halted (on_refusal halt)')
    check(res.e && /eps by codex/.test(res.e.v), 'eps answered by the understudy after a schema failure and a repair turn')
    check(und.length === 5 && und.filter(x => x.ok).length === 4 && und.map(x => x.label).sort().join() === 'beta,eps,eta,eta,zeta', `5 handovers, 4 succeeded (${und.map(x => x.label).join()})`)
    check(res.z && /main\.js/.test(res.z.runner_py) && und.some(x => x.label === 'zeta' && x.kind === 'declined'), 'zeta: a schema-valid stop report naming unwritten files is kind declined and hands over; a description naming an existing file is accepted')
    const epsMeta = JSON.parse(fs.readFileSync(path.join(out, 'agents', '0005-eps', 'meta.json'), 'utf8'))
    check(epsMeta.attempts === 2, 'schema failure received a repair turn')
    check(res.h && res.h.v === 'eta by cursor', 'eta answered by cursor after opencode and codex failed')
    check(res.h && /eta by cursor/.test(res.h.v) && und.filter(x => x.label === 'eta').some(x => x.to === 'cursor' && x.ok), 'label failing on opencode and codex is answered by cursor')
    const etaRows = und.filter(x => x.label === 'eta')
    check(etaRows.length === 2 && etaRows[0].from === 'opencode' && etaRows[0].to === 'codex' && !etaRows[0].ok && etaRows[1].from === 'codex' && etaRows[1].to === 'cursor' && etaRows[1].ok && etaRows[1].kind === 'runner', 'ordered family handovers journaled separately')
    const totals = JSON.parse(fs.readFileSync(path.join(out, 'status.json'), 'utf8'))
    check(totals.by_family.opencode.calls === 8 && totals.by_family.codex.calls === 4 && totals.by_family.cursor.calls === 1 && totals.substitutions === 4, 'totals include all three families; substitutions count answered calls')
    check(totals.calls.find(x => / eta$/.test(x.id)).attempts === 4, 'attempt count includes all three families (no repair turn after a usage-limit error)')
    const failed = J.filter(x => x.type === 'failed'); check(failed.length === 1 && failed[0].kind === 'refusal', 'one failed row of kind refusal')
    const md = fs.readFileSync(path.join(out, 'UNDERSTUDY.md'), 'utf8'); check(/refusals 1/.test(md) && /\| beta \|/.test(md), 'UNDERSTUDY.md written with the refusal count and the beta row')
    check(md.split('\n').some(l => /\| eta \|/.test(l) && /codex\/default@medium \(runner\), cursor\/default \(ok\)/.test(l)), 'report preserves both handovers')
  }
  if (mode === 'refusal') check(res.c && /gamma by codex/.test(res.c.v) && und.some(x => x.label === 'gamma' && x.kind === 'refusal'), 'gamma handed to the understudy when on_refusal is understudy')
  if (mode === 'shadow' || mode === 'writing') {
    check(shadow.length === 8 && fs.existsSync(path.join(out, 'shadow.jsonl')), `8 shadow rows (${shadow.length})`)
    check(shadow.find(x => x.label === 'alpha').agree === false && shadow.find(x => x.label === 'alpha').fields_differ.join() === 'v', 'alpha: both families returned, values differ in field v')
    check(res.b && /beta by codex/.test(res.b.v) && und.some(x => x.label === 'beta' && x.shadow), 'beta: primary failed, the shadow understudy value was used')
    check(res.c === null, 'gamma: refusal still halts in shadow mode')
    check(res.h === null && !und.some(x => x.label === 'eta'), 'shadow stops after first understudy fails')
  }
  if (mode === 'claude') {
    check(started.every(s => s.model.startsWith('claude/')), 'every primary is a claude model')
    check(byLabel.alpha.understudy === 'codex/default@medium', 'first understudy is codex')
    check(und.length === 0 && res.b && res.c && res.e, 'no understudy needed; all answered')
    const status = JSON.parse(fs.readFileSync(path.join(out, 'status.json'), 'utf8')); check(status.by_family.claude && status.by_family.claude.calls === 8, 'by_family totals on claude')
  }
  if (mode === 'primary-only') check(und.length === 0 && res.b === null && res.c === null && res.e === null && res.z === null && res.h === null, 'no understudy: failed calls are null')
  if (mode === 'codex' || mode === 'swap') {
    check(started.every(s => s.model.startsWith('codex/')), 'every primary is codex')
    check(res.h && res.h.v === 'eta by cursor', 'codex failure reaches cursor')
    check(und.filter(x => x.label === 'eta').map(x => x.to).join() === (mode === 'swap' ? 'opencode,cursor' : 'cursor'), 'swap retains original primary before remaining chain')
  }
  if (mode === 'exhausted' || mode === 'chain-refusal') {
    const etaRows = und.filter(x => x.label === 'eta')
    check(res.h === null && etaRows.length === (mode === 'exhausted' ? 3 : 1), 'chain stops when exhausted or refused')
    const status = JSON.parse(fs.readFileSync(path.join(out, 'status.json'), 'utf8'))
    check(status.calls.find(x => / eta$/.test(x.id)).state === (mode === 'exhausted' ? 'failed' : 'refused'), 'final failure state reflects last family')
  }
  if (mode === 'writing') {
    const writerDir = path.join(out, 'agents', '0008-writer')
    check(fs.readFileSync(path.join(writerDir, 'primary-files', 'writer.py'), 'utf8') === 'opencode' && fs.readFileSync(path.join(writerDir, 'understudy', 'primary-files', 'writer.py'), 'utf8') === 'codex', 'files snapshotted before each writing handover')
    check(fs.readFileSync(path.join(out, 'work', 'writer.py'), 'utf8') === 'claude' && byLabel.writer.mode === 'fallback', 'writing shadow downgrades to fallback and reaches claude')
  }
}
// Exercise the real CLI adapter against a local executable, without network or models.
async function codexChecks() {
  console.log('== codex runner')
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'e2e_codex_'))
  fs.writeFileSync(path.join(dir, 'codex'), `#!${process.execPath}
const fs = require('node:fs')
const args = process.argv.slice(2), prompt = fs.readFileSync(0, 'utf8')
fs.writeFileSync(process.env.E2E_CAPTURE, JSON.stringify({ args, prompt }))
if (process.env.E2E_CODEX_CASE === 'timeout') { setInterval(() => {}, 1000); return }
fs.writeFileSync(args[args.indexOf('-o') + 1], process.env.E2E_REPLY || '{"ok":true}')
const events = [{ type: 'thread.started', thread_id: 'thread-test' },
  { type: 'item.completed', item: { type: 'command_execution' } },
  { type: 'turn.completed', usage: { input_tokens: 13, output_tokens: 7, cached_input_tokens: 3, output_tokens_details: { reasoning_tokens: 2 } } }]
if (process.env.E2E_CODEX_CASE === 'limit') events.push({ type: 'turn.failed', error: { message: 'Rate limit exceeded' } })
if (process.env.E2E_CODEX_CASE === 'refusal') events.push({ type: 'item.completed', item: { type: 'refusal' } })
fs.writeSync(1, events.map(e => JSON.stringify(e)).join('\\n'))
`, { mode: 0o755 })
  const capture = path.join(dir, 'capture.json'), rawPath = path.join(dir, 'raw.jsonl')
  const env = { PATH: `${dir}:${process.env.PATH}`, E2E_CAPTURE: capture, E2E_CODEX_CASE: '', E2E_REPLY: '' }
  const base = { model: 'codex/default@low', prompt: 'reply ok', cwd: dir, tools: '', timeoutMs: 5000, rawPath, env }
  const run = o => require('../idea/codex_cli.js').run({ ...base, ...o })
  try {
    let r = await run({ systemPrompt: 'Role text', addDirs: [ROOT] })
    let sent = JSON.parse(fs.readFileSync(capture, 'utf8')), args = sent.args
    check(args[0] === 'exec' && ['--json', '--skip-git-repo-check'].every(a => args.includes(a)) && !args.includes('--ephemeral') && args.at(-1) === '-' && args[args.indexOf('-C') + 1] === dir, 'codex exec flags and stdin selected')
    check(!args.includes('-m') && args.includes('model_reasoning_effort=low') && args[args.indexOf('-s') + 1] === 'read-only', 'default model omitted; low effort and read-only sandbox')
    check(args[args.indexOf('--add-dir') + 1] === ROOT && sent.prompt.includes('Role text') && sent.prompt.includes('reply ok'), 'additional directory and role prompt forwarded')
    check(r.text === '{"ok":true}' && r.json.ok && !r.jsonError && r.sessionID === 'thread-test' && r.errors.length === 0 && !r.refusal, 'last-message file supplies parsed reply and event supplies session')
    check(r.tokens.input === 13 && r.tokens.output === 7 && r.tokens.reasoning === 2 && r.tokens.cache_read === 3 && r.tools === 1, 'JSONL usage and tool count parsed, including final unterminated line')
    check(rows(rawPath).length === 3 && !fs.existsSync(path.dirname(args[args.indexOf('-o') + 1])), 'raw events saved and temporary reply directory removed')
    r = await run({ model: 'codex/custom@high', tools: 'Read,Edit', env: { ...env, E2E_REPLY: '{"nested":{},}' } })
    args = JSON.parse(fs.readFileSync(capture, 'utf8')).args
    check(args[args.indexOf('-m') + 1] === 'custom' && args.includes('model_reasoning_effort=high') && args[args.indexOf('-s') + 1] === 'workspace-write', 'named model, high effort and writing sandbox')
    check(r.json === null && /the JSON does not parse/.test(r.jsonError), 'malformed whole JSON does not return inner fragment')
    for (const tools of ['Write', 'Bash', 'Read,Glob,Grep']) {
      await run({ tools })
      args = JSON.parse(fs.readFileSync(capture, 'utf8')).args
      check(args[args.indexOf('-s') + 1] === (tools === 'Read,Glob,Grep' ? 'read-only' : 'workspace-write'), `sandbox for ${tools}`)
    }
    r = await run({ env: { ...env, E2E_CODEX_CASE: 'limit' } })
    check(r.errors[0].startsWith('runner error: usage limit') && require('../idea/understudy.js').classify(r, r.errors) === 'runner', 'rate limit classified as runner failure')
    r = await run({ env: { ...env, E2E_CODEX_CASE: 'refusal' } })
    check(r.refusal && r.errors.includes('refusal'), 'explicit refusal event honored')
    r = await run({ timeoutMs: 300, env: { ...env, E2E_CODEX_CASE: 'timeout' } })
    check(r.errors[0].startsWith('timeout after ') && r.ms < 5000, 'timeout kills process and reports error')
    r = await run({ env: { ...env, PATH: dir + '/missing' } })
    check(r.errors[0].startsWith('runner error:') && r.tokens.input === 0, 'missing executable returns runner error')
  } finally { fs.rmSync(dir, { recursive: true, force: true }) }
}

;(async () => {
  if (want === 'all') await codexChecks()
  console.log(failures ? `\n${failures} check(s) FAILED` : '\nall checks passed')
  process.exit(failures ? 1 : 0)
})().catch(e => { console.error(e); process.exit(1) })
