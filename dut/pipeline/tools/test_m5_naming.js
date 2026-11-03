#!/usr/bin/env node
'use strict'

// Black-box naming and raid contracts; WF_STUB prevents model/network calls.
// Usage: node tools/test_m5_naming.js
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const assert = require('node:assert/strict')
const { spawnSync } = require('node:child_process')
const ROOT = path.resolve(__dirname, '..')
const readJSON = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const rows = file => fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : []
const family = model => model.startsWith('codex/') ? 'codex' : model.startsWith('claude/') ? 'claude' : 'opencode'
module.exports = {
  async run(options) {
    const { title, model, prompt, name } = options
    fs.appendFileSync(process.env.M5_NAMING_CAPTURE, JSON.stringify({ title, model, name, prompt }) + '\n')
    let json = { v: 'ok' }, errors = []
    if (title === 'repair' && !/could not be used/.test(prompt)) json = {}
    if (title === 'fallback' && family(model) === 'opencode') errors = ['runner error: usage limit']
    if (['repair-fallback', 'combo'].includes(title) && family(model) === 'opencode') json = {}
    if (process.env.M5_NAMING_RAID) json = title === 'intake'
      ? { found: false, anchors_count: 0, data: 'unavailable', licence: 'unknown', stock_environment: false, size: 'unknown' }
      : { v: 'fixture' }
    return { text: JSON.stringify(json), json, jsonError: null, sessionID: 'stub',
      tokens: { input: 10, output: 5 }, tokens_known: true, cost: 0, tools: 0, ms: 1, errors, refusal: false }
  },
  async exportSession(id, file) { fs.writeFileSync(file, '{}') },
}
if (require.main !== module) return

const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_naming_'))
let failures = 0, checks = 0, sequence = 0
function check(label, test) {
  checks++
  try { test(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${error.message}`) }
}
function writeJSON(file, value) { fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, JSON.stringify(value) + '\n') }
const schema = { type: 'object', required: ['v'], properties: { v: { type: 'string' } } }
const script = `export const meta = { name: 'naming-contract', description: 'black-box fixture' }
const schema = ${JSON.stringify(schema)}
await agent('single', { label: ' !! MiXeD__ Label!! ', schema })
await agent('empty', { label: '!!!', schema })
await Promise.all([1, 2, 3].map(i => agent('sibling ' + i, { label: 'same', schema })))
await agent('repair', { label: 'repair', schema })
await agent('fallback', { label: 'fallback', schema })
await agent('repair fallback', { label: 'repair-fallback', schema })
await Promise.all([1, 2].map(i => agent('combined ' + i, { label: 'combo', schema })))
await agent('harness repair', { label: 'harness-repair', retry: 1, schema })
return { ok: true }
`
function workflow(label, args, options = {}) {
  const dir = path.join(scratch, `${++sequence}-${label}`)
  fs.mkdirSync(dir, { recursive: true })
  const scriptFile = path.join(dir, 'script.js'), argsFile = path.join(dir, 'args.json')
  fs.writeFileSync(scriptFile, options.script || script)
  writeJSON(argsFile, args)
  const capture = path.join(dir, 'calls.jsonl'), out = path.join(dir, 'wf')
  const config = readJSON(path.join(ROOT, 'idea', 'config.json'))
  config.workflow.label_rules = []
  config.workflow.main_model = 'opencode-go/stub'
  config.workflow.cheap_model = 'opencode-go/stub'
  config.understudy.routes = []
  config.understudy.disabled_families = []
  config.understudy.chain = { opencode: ['codex'], codex: ['claude'], claude: ['codex'] }
  writeJSON(path.join(dir, 'config.json'), config)
  const stdout = fs.openSync(path.join(dir, 'stdout.log'), 'w'), stderr = fs.openSync(path.join(dir, 'stderr.log'), 'w')
  const env = { ...process.env, WF_STUB: __filename, M5_NAMING_CAPTURE: capture,
    M5_NAMING_RAID: options.raid ? '1' : '', ...(options.env || {}) }
  // raidsLedger: path string sets M5_RAIDS_LEDGER; null clears it (run-local default).
  if (options.raidsLedger !== undefined) {
    if (options.raidsLedger === null) delete env.M5_RAIDS_LEDGER
    else env.M5_RAIDS_LEDGER = options.raidsLedger
  }
  const result = spawnSync(process.execPath, [path.join(options.pipeline || ROOT, 'idea', 'wf.js'), '--script', options.scriptFile || scriptFile,
    '--args', argsFile, '--out', out, '--config', path.join(dir, 'config.json'), ...(options.flags || [])], {
    cwd: options.cwd || ROOT, stdio: ['ignore', stdout, stderr], timeout: 600000, env,
  })
  fs.closeSync(stdout); fs.closeSync(stderr)
  check(`${label}: workflow exits cleanly`, () => {
    assert.ifError(result.error)
    assert.equal(result.status, 0, fs.readFileSync(path.join(dir, 'stderr.log'), 'utf8').slice(-800))
    const value = readJSON(path.join(out, 'result.json'))
    assert.ok(!value?.error, value?.error)
  })
  return { calls: rows(capture), dir, out, result }
}
function namingChecks() {
  for (const [label, args, flags] of [
    ['args-prefix', { chat_prefix: 'x-crowbar' }, []],
    ['flag-prefix', {}, ['--chat-prefix', 'x-crowbar']],
  ]) {
    const run = workflow(label, args, { flags })
    const named = title => run.calls.filter(call => call.title === title).map(call => call.name)
    check(`${label}: every runner attempt gets prefix and sanitized label`, () => {
      assert.ok(run.calls.length >= 12)
      for (const call of run.calls) assert.match(call.name, /^x-crowbar-[a-z0-9-]+$/)
      assert.deepEqual(named(' !! MiXeD__ Label!! '), ['x-crowbar-mixed-label'])
      assert.deepEqual(named('!!!'), ['x-crowbar-agent'])
    })
    check(`${label}: siblings get ordered iofn suffixes`, () => {
      assert.deepEqual(named('same'), ['x-crowbar-same-1of3', 'x-crowbar-same-2of3', 'x-crowbar-same-3of3'])
    })
    check(`${label}: repair and fallback descriptors`, () => {
      assert.deepEqual(named('repair'), ['x-crowbar-repair', 'x-crowbar-repair-retry1'])
      assert.deepEqual(named('fallback'), ['x-crowbar-fallback', 'x-crowbar-fallback-fb'])
      assert.deepEqual(named('repair-fallback'), ['x-crowbar-repair-fallback', 'x-crowbar-repair-fallback-retry1', 'x-crowbar-repair-fallback-fb'])
      assert.deepEqual(named('combo').sort(), [1, 2].flatMap(i => [
        `x-crowbar-combo-${i}of2`, `x-crowbar-combo-${i}of2-retry1`, `x-crowbar-combo-${i}of2-fb`,
      ]).sort())
      assert.deepEqual(named('harness-repair'), ['x-crowbar-harness-repair-retry1'])
    })
  }
  const legacy = workflow('no-prefix', {})
  check('no prefix preserves runner naming', () => {
    assert.ok(legacy.calls.length >= 12)
    assert.ok(legacy.calls.every(call => call.name == null || call.name === ''))
    assert.ok(legacy.calls.some(call => call.title === ' !! MiXeD__ Label!! '))
  })
  const option = workflow('agent-option', {}, { script: `export const meta = { name: 'option', description: 'fixture' }
return await agent('hello', { label: 'Own Label', chat_prefix: 'x-shadow' })` })
  check('agent option opts into naming', () => assert.deepEqual(option.calls.map(call => call.name), ['x-shadow-own-label']))
}
async function runnerChecks() {
  const dir = path.join(scratch, 'runners')
  fs.mkdirSync(dir)
  const capture = path.join(dir, 'capture.json')
  const executable = `#!${process.execPath}
const fs = require('node:fs')
const args = process.argv.slice(2), prompt = fs.readFileSync(0, 'utf8')
fs.writeFileSync(process.env.M5_RUNNER_CAPTURE, JSON.stringify({ args, prompt }))
const executable = require('node:path').basename(process.argv[1])
if (executable === 'codex') {
  fs.writeFileSync(args[args.indexOf('-o') + 1], '{"v":"ok"}')
  fs.writeSync(1, JSON.stringify({ type: 'thread.started', thread_id: 'stub' }) + '\\n')
  fs.writeSync(1, JSON.stringify({ type: 'turn.completed', usage: { input_tokens: 0, output_tokens: 0 } }) + '\\n')
} else if (executable === 'claude') {
  fs.writeSync(1, JSON.stringify({ type: 'result', subtype: 'success', result: '{"v":"ok"}', session_id: 'stub', usage: { input_tokens: 0, output_tokens: 0 }, total_cost_usd: 0 }) + '\\n')
} else {
  fs.writeSync(1, JSON.stringify({ type: 'text', sessionID: 'stub', part: { type: 'text', text: '{"v":"ok"}' } }) + '\\n')
  fs.writeSync(1, JSON.stringify({ type: 'step_finish', sessionID: 'stub', part: { type: 'step-finish', tokens: { input: 0, output: 0, reasoning: 0, cache: { read: 0, write: 0 } }, cost: 0 } }) + '\\n')
}
`
  for (const name of ['opencode', 'claude', 'codex']) fs.writeFileSync(path.join(dir, name), executable, { mode: 0o700 })
  const adapters = [['opencode', 'oc.js', 'opencode-go/stub'], ['claude', 'claude_cli.js', 'claude/sonnet'], ['codex', 'codex_cli.js', 'codex/default@low']]
  for (const [family, file, model] of adapters) {
    for (const name of ['x-crowbar-agent', undefined]) {
      // Keep adapter failures local so all three family contracts still run.
      try {
        fs.rmSync(capture, { force: true })
        const result = await require(path.join(ROOT, 'idea', file)).run({ model, name, title: 'original title', prompt: 'hello',
          systemPrompt: 'Role instructions', cwd: dir, tools: '', timeoutMs: 5000,
          env: { PATH: `${dir}:${process.env.PATH}`, M5_RUNNER_CAPTURE: capture } })
        check(`${family}: ${name || 'legacy'} transport`, () => {
          const sent = readJSON(capture)
          if (family === 'codex') {
            if (name) assert.equal(sent.prompt.split('\n')[0], `[${name}]`)
            else assert.ok(!sent.prompt.startsWith('['))
            assert.ok(sent.prompt.includes('Role instructions') && sent.prompt.includes('hello'))
          } else {
            const flag = family === 'claude' ? '--name' : '--title'
            if (name || family === 'opencode') assert.equal(sent.args[sent.args.indexOf(flag) + 1], name || 'original title')
            else assert.equal(sent.args.includes(flag), false)
          }
          assert.equal(result.tokens_known, true, 'reported zero usage must be known')
        })
      } catch (error) { check(`${family}: adapter invocation`, () => { throw error }) }
    }
  }
}
function raidChecks() {
  // Isolate both source-relative and cwd-relative resolution via a scratch pipeline copy.
  const pipeline = path.join(scratch, 'pipeline')
  for (const directory of ['m5', 'idea', 'measure']) fs.cpSync(path.join(ROOT, directory), path.join(pipeline, directory), {
    recursive: true, filter: source => path.basename(source) !== 'experiments',
  })
  const sharedCopy = path.join(pipeline, 'm5', 'raids_used.jsonl')
  const sharedCopyBefore = fs.existsSync(sharedCopy) ? fs.readFileSync(sharedCopy) : null
  // Sequence tests opt into a temp ledger via M5_RAIDS_LEDGER (never the shared file).
  const ledger = path.join(scratch, 'raids_used_sequence.jsonl')
  const names = readJSON(path.join(ROOT, 'm5', 'raids.json'))
  const entry = (raid, blind = false, run_root = '/tmp/prior-run') => ({ raid, blind, run_root, utc: '2026-01-01T00:00:00.000Z' })
  const seed = entries => fs.writeFileSync(ledger, entries.map(row => JSON.stringify(row) + '\n').join(''))
  function reserve(label, args, expected, prior, options = {}) {
    const root = args.run_root || path.join(scratch, `raid-${label}`)
    const activeLedger = options.local
      ? path.join(root, 'control', 'raids_used.jsonl')
      : (options.raidsLedger || ledger)
    const run = workflow(label, { tag: 'naming-test', ...args, run_root: root }, {
      raid: true, pipeline, cwd: pipeline, flags: ['--disable-family', 'claude'],
      scriptFile: path.join(pipeline, 'm5', 'pipeline.js'),
      raidsLedger: options.local ? null : (options.raidsLedger || ledger),
    })
    check(`${label}: reservation and append-only ledger`, () => {
      const reservation = readJSON(path.join(root, 'control', 'raid.json'))
      assert.deepEqual(Object.keys(reservation).sort(), ['blind', 'raid', 'run_root', 'utc'])
      assert.equal(reservation.raid, expected)
      assert.equal(reservation.blind, !!args.blind)
      assert.equal(reservation.run_root, path.resolve(root))
      assert.match(reservation.utc, /^\d{4}-\d\d-\d\dT.*Z$/)
      assert.ok(Number.isFinite(Date.parse(reservation.utc)))
      const after = rows(activeLedger)
      assert.deepEqual(after.slice(0, prior.length), prior)
      assert.equal(after.length, prior.length + 1)
      assert.deepEqual(after.at(-1), reservation)
    })
    check(`${label}: every pipeline call carries raid`, () => {
      assert.ok(run.calls.length >= 1, fs.readFileSync(path.join(run.out, 'result.json'), 'utf8'))
      for (const call of run.calls) assert.equal(call.name, `x-${expected}-${call.title.toLowerCase().replace(/[^a-z0-9-]+/g, '-').replace(/^-+|-+$/g, '') || 'agent'}`)
    })
    check(`${label}: operator takeaway header carries raid`, () => {
      const takeaway = fs.readFileSync(path.join(root, 'operator', 'OPERATOR_TAKEAWAY.md'), 'utf8')
      assert.ok(takeaway.split('\n')[0].includes(expected))
      assert.ok(!takeaway.split('\n').slice(1).join('\n').includes(expected), 'raid outside header')
      for (const row of rows(path.join(root, 'operator', 'signatures.jsonl'))) {
        assert.ok(!JSON.stringify(row.facts).includes(expected), 'raid leaked into facts')
        assert.ok(!row.signature.id.includes(expected), 'raid leaked into signature ID')
      }
    })
    return root
  }
  seed([])
  reserve('first-public', {}, names.public[0], [])
  reserve('next-public', {}, names.public[1], rows(ledger))
  reserve('first-blind', { blind: true }, names.blind[0], rows(ledger))
  const prior = [entry(names.public[0]), entry(names.public[2]), entry(names.blind[0], true)]
  seed(prior)
  reserve('first-unused', {}, names.public[1], prior)
  reserve('explicit', { raid: 'operator-chosen', blind: true }, 'operator-chosen', rows(ledger))
  for (const blind of [false, true]) {
    const list = names[blind ? 'blind' : 'public']
    seed(list.map(name => entry(name, blind)))
    reserve(`exhausted-${blind}`, { blind }, `${list[0]}2`, rows(ledger))
    reserve(`next-cycle-${blind}`, { blind }, `${list[1]}2`, rows(ledger))
    seed([1, 2].flatMap(cycle => list.map(name => entry(name + (cycle === 1 ? '' : cycle), blind))))
    reserve(`third-cycle-${blind}`, { blind }, `${list[0]}3`, rows(ledger))
  }
  // No record_raid, no M5_RAIDS_LEDGER → run-local ledger only; shared files untouched.
  const sequenceBytes = fs.existsSync(ledger) ? fs.readFileSync(ledger) : null
  const localRoot = reserve('run-local', {}, names.public[0], [], { local: true })
  check('no opt-in writes only run-local ledger', () => {
    const localLedger = path.join(localRoot, 'control', 'raids_used.jsonl')
    assert.ok(fs.existsSync(localLedger), 'missing run-local ledger')
    assert.equal(rows(localLedger).length, 1)
    assert.equal(rows(localLedger)[0].raid, names.public[0])
    assert.deepEqual(fs.existsSync(ledger) ? fs.readFileSync(ledger) : null, sequenceBytes, 'sequence temp ledger mutated')
    assert.deepEqual(fs.existsSync(sharedCopy) ? fs.readFileSync(sharedCopy) : null, sharedCopyBefore, 'copied shared ledger mutated')
    assert.ok(!fs.existsSync(path.join(localRoot, 'm5', 'raids_used.jsonl')))
  })
}
async function main() {
  const realLedger = path.join(ROOT, 'm5', 'raids_used.jsonl')
  const realBefore = fs.existsSync(realLedger) ? fs.readFileSync(realLedger) : null
  check('real m5/raids_used.jsonl readable before suite', () => {
    assert.ok(realBefore === null || Buffer.isBuffer(realBefore))
  })
  try {
    namingChecks()
    await runnerChecks()
    raidChecks()
  } catch (error) { check('test harness', () => { throw error }) }
  finally {
    check('real m5/raids_used.jsonl byte-identical after suite', () => {
      assert.deepEqual(fs.existsSync(realLedger) ? fs.readFileSync(realLedger) : null, realBefore)
    })
    fs.rmSync(scratch, { recursive: true, force: true })
  }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : 'all checks passed')
  process.exitCode = failures ? 1 : 0
}
main()
