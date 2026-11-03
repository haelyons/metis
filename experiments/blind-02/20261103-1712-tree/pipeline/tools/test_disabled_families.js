// Black-box runtime-guard tests. This file also supplies the WF_STUB runner.
// Usage: node tools/test_disabled_families.js
'use strict'
const fs = require('node:fs'), path = require('node:path'), os = require('node:os')
const { spawnSync } = require('node:child_process')
const ROOT = path.join(__dirname, '..')
const family = model => model.startsWith('codex/') ? 'codex' : model.startsWith('cursor/') ? 'cursor' : model.split('/')[0] === 'claude' ? 'claude' : 'opencode'
module.exports = {
  async run({ model, title, prompt }) {
    const f = family(model)
    fs.appendFileSync(process.env.DISABLED_FAMILIES_LOG, JSON.stringify({ model, label: title, prompt, repair: /could not be used/.test(prompt) }) + '\n')
    const errors = title === 'exhausted' && f !== 'claude' ? ['$: missing "v"']
      : title === 'usage-limit' && f === 'opencode' ? ['runner error: usage limit: test quota exhausted'] : []
    const json = errors.length ? null : { v: `${title} by ${f}` }
    return { text: json ? JSON.stringify(json) : '', json, jsonError: null, sessionID: 'stub',
      tokens: { input: 10, output: json ? 5 : 0, reasoning: 0 }, cost: 0, tools: 0, ms: 1, errors, refusal: false }
  },
  async exportSession(id, file) { fs.writeFileSync(file, '{}') },
}
if (require.main !== module) return

const DEFAULT_CONFIG = path.join(ROOT, 'idea', 'config.json')
const schema = { type: 'object', required: ['v'], properties: { v: { type: 'string' } } }
let failures = 0
const check = (condition, message) => {
  console.log(`${condition ? 'ok' : 'FAIL'} ${message}`)
  if (!condition) failures++
}
function run(name, { labels = ['answer'], flags = [], configure } = {}, verify) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'test_disabled_families_'))
  try {
    const script = path.join(dir, 'main.js'), log = path.join(dir, 'stub.jsonl'), out = path.join(dir, 'run')
    fs.writeFileSync(script, `export const meta = { name: 'disabled-families-test', description: 'Runtime guard test' }
const result = {}
for (const label of ${JSON.stringify(labels)}) {
  result[label] = await agent(label, { label, schema: ${JSON.stringify(schema)} })
}
return result
`)
    fs.writeFileSync(path.join(dir, 'args.json'), '{}')
    let config = DEFAULT_CONFIG
    if (configure) {
      const cfg = JSON.parse(fs.readFileSync(DEFAULT_CONFIG, 'utf8'))
      configure(cfg)
      config = path.join(dir, 'config.json')
      fs.writeFileSync(config, JSON.stringify(cfg))
    }
    // File descriptors also work in sandboxes that disallow child-process pipes.
    const stdoutFile = path.join(dir, 'stdout'), stderrFile = path.join(dir, 'stderr')
    const stdoutFd = fs.openSync(stdoutFile, 'w'), stderrFd = fs.openSync(stderrFile, 'w')
    let child
    try {
      child = spawnSync(process.execPath, [path.join(ROOT, 'idea', 'wf.js'),
        '--script', script, '--args', path.join(dir, 'args.json'), '--out', out,
        '--config', config, '--profile', 'latent_skeptic', ...flags], {
        stdio: ['ignore', stdoutFd, stderrFd], timeout: 30000,
        env: { ...process.env, WF_STUB: __filename, DISABLED_FAMILIES_LOG: log },
      })
    } finally {
      fs.closeSync(stdoutFd)
      fs.closeSync(stderrFd)
    }
    const output = fs.readFileSync(stdoutFile, 'utf8') + fs.readFileSync(stderrFile, 'utf8')
    const calls = fs.existsSync(log) ? fs.readFileSync(log, 'utf8').trim().split('\n').filter(Boolean).map(JSON.parse) : []
    const resultFile = path.join(out, 'result.json')
    const result = fs.existsSync(resultFile) ? JSON.parse(fs.readFileSync(resultFile, 'utf8')) : null
    const before = failures
    check(!child.error, `${name}: process completed${child.error ? ` (${child.error.message})` : ''}`)
    verify({ child, calls, result, output })
    if (failures > before) console.log(output.slice(-2000))
  } catch (error) {
    check(false, `${name}: ${error.stack}`)
  } finally {
    fs.rmSync(dir, { recursive: true, force: true })
  }
}
function exhausted(name, options) {
  run(name, { labels: ['exhausted'], ...options }, ({ child, calls, result }) => {
    check(child.status === 0, `${name}: workflow completed`)
    check(result && result.exhausted === null, `${name}: enabled chain exhausted without an answer`)
    check(['opencode', 'codex', 'cursor'].every(f => calls.some(c => family(c.model) === f)), `${name}: all enabled families attempted`)
    check(['opencode', 'codex', 'cursor'].every(f => calls.some(c => family(c.model) === f && c.repair)), `${name}: schema failures exercised repair turns`)
    check(calls.length > 0 && calls.every(c => !c.model.startsWith('claude/')), `${name}: no claude dispatch, including repairs and fallback`)
  })
}

exhausted('(a) config exclusion', { configure: cfg => { cfg.understudy.disabled_families = ['claude'] } })
exhausted('(b) CLI exclusion with default config', { flags: ['--disable-family', 'claude'] })
run('(c) disabled primary', { configure: cfg => {
  cfg.understudy.primary_family = 'claude'
  cfg.understudy.disabled_families = ['claude']
} }, ({ child, calls, result }) => {
  check(child.status === 0 && result && result.answer && result.answer.v === 'answer by codex', '(c): first enabled fallback answers')
  check(calls.length === 1 && family(calls[0].model) === 'codex', '(c): disabled primary never dispatched')
})
run('(d) all disabled', { configure: cfg => {
  cfg.understudy.disabled_families = ['opencode', 'codex', 'claude', 'cursor']
} }, ({ child, calls, output }) => {
  check(child.status !== null && child.status !== 0, '(d): workflow fails when no family is enabled')
  check(/runner error: family disabled\b/.test(output), '(d): clear error has required family-disabled prefix')
  check(calls.length === 0, '(d): no disabled family dispatched')
})
run('(e) usage limit', { labels: ['usage-limit'] }, ({ child, calls, result }) => {
  check(child.status === 0 && result && result['usage-limit'] && result['usage-limit'].v === 'usage-limit by codex', '(e): next family answers after usage limit')
  check(calls.length === 2 && calls.map(c => family(c.model)).join() === 'opencode,codex', '(e): immediate ordered handover, no extra dispatch')
  check(calls.length > 0 && calls.every(c => c.label === 'usage-limit' && !c.repair), '(e): usage-limit label receives no repair prompt')
})
run('shadow exclusion', { flags: ['--family', 'codex', '--mode', 'shadow', '--disable-family', 'claude'] }, ({ child, calls, result }) => {
  check(child.status === 0 && result && result.answer && result.answer.v === 'answer by codex', 'shadow: primary answers')
  check(calls.length === 2 && calls.map(c => family(c.model)).sort().join() === 'codex,cursor', 'shadow: first enabled understudy shadows; no claude dispatch')
})
run('repeatable CLI exclusion', { flags: ['--family', 'claude', '--disable-family', 'claude', '--disable-family', 'codex'] }, ({ child, calls, result }) => {
  check(child.status === 0 && result && result.answer && result.answer.v === 'answer by opencode', 'repeatable CLI: skips disabled primary and disabled first fallback')
  check(calls.length === 1 && family(calls[0].model) === 'opencode', 'repeatable CLI: neither disabled family dispatched')
})
console.log(failures ? `${failures} check(s) FAILED` : 'all checks passed')
process.exitCode = failures ? 1 : 0
