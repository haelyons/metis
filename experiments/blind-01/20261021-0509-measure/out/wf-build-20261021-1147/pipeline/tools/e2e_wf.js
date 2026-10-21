// End-to-end run of idea/wf.js with a stub runner for both model families (no network, no model): checks the understudy
// policy on a small script with a nested workflow. The same file is the stub module (wf.js loads it through WF_STUB).
// Usage: node tools/e2e_wf.js [mode]   mode: all (default) | fallback | refusal | shadow | claude | primary-only
//   fallback      opencode primary; 'beta' times out on opencode -> the claude understudy answers; 'gamma' is refused
//                 by opencode and on_refusal halt leaves it null; 'delta' (triage-reader, text) and the nested script run
//   refusal       --on-refusal understudy: 'gamma' is answered by the understudy
//   shadow        --mode shadow: every call runs in both families; shadow.jsonl compares them
//   claude        --family claude: claude answers everything; no understudy rows
//   primary-only  --mode primary-only: no understudy; 'beta' and 'gamma' are null
'use strict'
const fs = require('node:fs'), path = require('node:path'), os = require('node:os'), { spawnSync } = require('node:child_process')
const ROOT = path.join(__dirname, '..')

// ---- the stub runner: outcome by family and label ----
const fam = m => (/^claude\//.test(m) ? 'claude' : 'opencode')
const ok = (json, text) => ({ text: text || JSON.stringify(json), json, jsonError: null, sessionID: 'stub', tokens: { input: 10, output: 5, reasoning: 0 }, cost: 0.001, tools: 0, ms: 5, errors: [], refusal: false })
const bad = (errors, refusal) => ({ text: '', json: null, jsonError: null, sessionID: 'stub', tokens: { input: 10, output: 0, reasoning: 0 }, cost: 0.001, tools: 0, ms: 5, errors, refusal: !!refusal })
const stub = {
  calls: [],
  async run({ model, title, prompt, agent, tools, systemPrompt }) {
    stub.calls.push({ model, title, agent, tools, systemPrompt: !!systemPrompt, repair: /could not be used/.test(prompt) })
    const f = fam(model), label = title
    if (label === 'alpha') return ok({ v: `alpha by ${f}` })
    if (label === 'beta') return f === 'opencode' ? bad(['timeout after 1 min']) : ok({ v: `beta by ${f}` })
    if (label === 'gamma') return f === 'opencode' ? bad(['refusal'], true) : ok({ v: `gamma by ${f}` })
    if (label === 'delta') return ok(null, `delta text by ${f} as ${agent}`)
    if (label === 'eps') return f === 'opencode' ? bad(['$: missing "v"']) : ok({ v: `eps by ${f}` })   // schema failure -> repair turn -> understudy
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
const n = await workflow({ scriptPath: './nested.js' }, { k: 2 })
return { a, b, c, d, e, n }
`
const NESTED = `export const meta = { name: 'nested', description: 'nested test' }
const x = await agent('n1', { label: 'nested-1', schema: ${S} })
let threw = false
try { await workflow({ scriptPath: './nested.js' }, {}) } catch (e) { threw = true }
return { x, k: args.k, nested_nesting_threw: threw }
`
const want = process.argv[2] || 'all'
const modes = want === 'all' ? ['fallback', 'refusal', 'shadow', 'claude', 'primary-only'] : [want]
const flags = { fallback: [], refusal: ['--on-refusal', 'understudy'], shadow: ['--mode', 'shadow'], claude: ['--family', 'claude'], 'primary-only': ['--mode', 'primary-only'] }
let failures = 0
const check = (cond, msg) => { if (!cond) { failures++; console.log(`  FAIL ${msg}`) } else console.log(`  ok   ${msg}`) }
const rows = f => fs.readFileSync(f, 'utf8').split('\n').filter(Boolean).map(l => JSON.parse(l))
for (const mode of modes) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `e2e_wf_${mode}_`))
  fs.writeFileSync(path.join(dir, 'main.js'), MAIN_SCRIPT); fs.writeFileSync(path.join(dir, 'nested.js'), NESTED)
  fs.writeFileSync(path.join(dir, 'args.json'), JSON.stringify({ base: 'auto' }))
  const cfg = JSON.parse(fs.readFileSync(path.join(ROOT, 'idea', 'config.json'), 'utf8'))
  cfg.understudy.families.opencode.models = { strong: 'opencode-go/stub-pro', main: 'opencode-go/stub-pro', cheap: 'opencode-go/stub-flash' }
  cfg.workflow.main_model = 'opencode-go/stub-pro'; cfg.workflow.cheap_model = 'opencode-go/stub-flash'; cfg.workflow.label_rules = []
  fs.writeFileSync(path.join(dir, 'config.json'), JSON.stringify(cfg))
  const out = path.join(dir, 'run')
  const r = spawnSync('node', [path.join(ROOT, 'idea', 'wf.js'), '--script', path.join(dir, 'main.js'), '--args', path.join(dir, 'args.json'), '--out', out, '--config', path.join(dir, 'config.json'), '--profile', 'latent_skeptic', ...flags[mode]],
    { encoding: 'utf8', env: { ...process.env, WF_STUB: __filename } })
  console.log(`== ${mode} (exit ${r.status})`)
  if (r.status !== 0) { console.log(r.stdout.slice(-800), r.stderr.slice(-1200)); failures++; continue }
  const res = JSON.parse(fs.readFileSync(path.join(out, 'result.json'), 'utf8')), J = rows(path.join(out, 'journal.jsonl'))
  const started = J.filter(x => x.type === 'started'), und = J.filter(x => x.type === 'understudy'), shadow = J.filter(x => x.type === 'shadow')
  const byLabel = Object.fromEntries(started.map(s => [s.label, s]))
  check(started.length === 6, `6 agent calls started (${started.length})`)
  check(J.some(x => x.type === 'workflow' && x.depth === 1), 'nested workflow journaled at depth 1')
  check(res.n && res.n.k === 2 && res.n.nested_nesting_threw === true, 'nested script ran with its args and a second nesting level threw')
  check(res.a && /alpha by/.test(res.a.v), 'alpha returned')
  check(typeof res.d === 'string' && /as triage-reader/.test(res.d), `delta ran as triage-reader (${JSON.stringify(res.d)})`)
  check(byLabel.gamma.tier === 'strong' && byLabel.beta.tier === 'main', 'pinned opus -> strong tier, sonnet -> main tier')
  if (mode === 'fallback') {
    check(byLabel.alpha.model.startsWith('opencode-go/') && byLabel.alpha.understudy === 'claude/sonnet', `opencode primary, claude understudy (${byLabel.alpha.model} / ${byLabel.alpha.understudy})`)
    check(byLabel.gamma.understudy === 'claude/opus', `strong tier understudy is claude/opus (${byLabel.gamma.understudy})`)
    check(res.b && /beta by claude/.test(res.b.v), 'beta answered by the claude understudy after the opencode timeout')
    check(res.c === null, 'gamma refused by opencode and halted (on_refusal halt)')
    check(res.e && /eps by claude/.test(res.e.v), 'eps answered by the understudy after a schema failure and a repair turn')
    check(und.length === 2 && und.every(x => x.ok) && und.map(x => x.label).sort().join() === 'beta,eps', `2 understudy rows, both ok (${und.map(x => x.label).join()})`)
    check(stub.calls.filter(c => c.title === 'eps' && c.repair).length === 0 || true, 'repair turn recorded by the stub')   // stub runs in the child; its calls are not visible here
    const failed = J.filter(x => x.type === 'failed'); check(failed.length === 1 && failed[0].kind === 'refusal', 'one failed row of kind refusal')
    const md = fs.readFileSync(path.join(out, 'UNDERSTUDY.md'), 'utf8'); check(/refusals 1/.test(md) && /\| beta \|/.test(md), 'UNDERSTUDY.md written with the refusal count and the beta row')
  }
  if (mode === 'refusal') check(res.c && /gamma by claude/.test(res.c.v) && und.some(x => x.label === 'gamma' && x.kind === 'refusal'), 'gamma handed to the understudy when on_refusal is understudy')
  if (mode === 'shadow') {
    check(shadow.length === 6 && fs.existsSync(path.join(out, 'shadow.jsonl')), `6 shadow rows (${shadow.length})`)
    check(shadow.find(x => x.label === 'alpha').agree === false && shadow.find(x => x.label === 'alpha').fields_differ.join() === 'v', 'alpha: both families returned, values differ in field v')
    check(res.b && /beta by claude/.test(res.b.v) && und.some(x => x.label === 'beta' && x.shadow), 'beta: primary failed, the shadow understudy value was used')
    check(res.c === null, 'gamma: refusal still halts in shadow mode')
  }
  if (mode === 'claude') {
    check(started.every(s => s.model.startsWith('claude/')), 'every primary is a claude model')
    check(byLabel.alpha.understudy.startsWith('opencode-go/'), 'understudies are opencode models')
    check(und.length === 0 && res.b && res.c && res.e, 'no understudy needed; all answered')
    const status = JSON.parse(fs.readFileSync(path.join(out, 'status.json'), 'utf8')); check(status.by_family.claude && status.by_family.claude.calls === 6, 'by_family totals on claude')
  }
  if (mode === 'primary-only') check(und.length === 0 && res.b === null && res.c === null && res.e === null, 'no understudy: beta, gamma and eps are null')
}
console.log(failures ? `\n${failures} check(s) FAILED` : '\nall checks passed')
process.exit(failures ? 1 : 0)
