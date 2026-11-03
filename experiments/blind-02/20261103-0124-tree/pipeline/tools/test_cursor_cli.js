'use strict'
// Independent black-box contract tests. Never inspect the runner's implementation.
// Run: node tools/test_cursor_cli.js. No network, dependencies, or real Cursor runs.
const assert = require('node:assert/strict')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const { performance } = require('node:perf_hooks')
const { run } = require('../idea/cursor_cli.js')
const { classify } = require('../idea/understudy.js')

const root = fs.mkdtempSync(path.join(os.tmpdir(), 'test-cursor-cli-'))
const bin = path.join(root, 'bin')
fs.mkdirSync(bin)
fs.writeFileSync(path.join(bin, 'cursor-agent'), `#!${process.execPath}
'use strict'
const fs = require('node:fs')
const args = process.argv.slice(2)
const stdin = fs.readFileSync(0, 'utf8')
fs.writeFileSync(process.env.TEST_CURSOR_CAPTURE, JSON.stringify({ args, stdin, pid: process.pid }))
const finish = () => {
  const reply = process.env.TEST_CURSOR_REPLY
  const payload = {
    result: reply,
    session_id: 'black-box-session',
    subtype: 'success',
    usage: { input_tokens: 13, output_tokens: 7, cache_read_input_tokens: 3 },
    total_cost_usd: 0.01,
    num_turns: 1,
  }
  if (process.env.TEST_CURSOR_PAYLOAD) Object.assign(payload, JSON.parse(process.env.TEST_CURSOR_PAYLOAD))
  fs.writeSync(1, JSON.stringify(payload))
  fs.writeSync(2, process.env.TEST_CURSOR_STDERR)
  process.exit(Number(process.env.TEST_CURSOR_EXIT))
}
setTimeout(finish, Number(process.env.TEST_CURSOR_SLEEP))
`, { mode: 0o755 })

const originalPath = process.env.PATH
process.env.PATH = bin
let sequence = 0, failures = 0, checks = 0
const pids = new Set()

function alive(pid) {
  try { process.kill(pid, 0); return true } catch (error) {
    if (error.code === 'ESRCH') return false
    throw error
  }
}

async function invoke(options = {}, fake = {}) {
  const dir = path.join(root, String(++sequence))
  fs.mkdirSync(dir)
  const capture = path.join(dir, 'capture.json')
  const env = {
    PATH: bin,
    ...fake.env,
    TEST_CURSOR_CAPTURE: capture,
    TEST_CURSOR_REPLY: fake.reply ?? 'file reply\n',
    TEST_CURSOR_STDERR: fake.stderr ?? '',
    TEST_CURSOR_EXIT: String(fake.exit ?? 0),
    TEST_CURSOR_SLEEP: String(fake.sleep ?? 0),
  }
  if (fake.payload) env.TEST_CURSOR_PAYLOAD = JSON.stringify(fake.payload)
  let watchdog
  const started = performance.now()
  try {
    const res = await Promise.race([
      run({ model: 'cursor/default', prompt: 'User prompt marker\nSecond line', cwd: dir,
        timeoutMs: 3000, rawPath: path.join(dir, 'raw.jsonl'), tools: 'Read,Glob,Grep',
        ...options, env }),
      new Promise((_, reject) => {
        watchdog = setTimeout(() => reject(new Error('runner did not settle within 6000 ms')), 6000)
      }),
    ])
    const elapsed = performance.now() - started
    assert.ok(fs.existsSync(capture), 'fake cursor-agent was not invoked through PATH')
    const sent = JSON.parse(fs.readFileSync(capture, 'utf8'))
    pids.add(sent.pid)
    return { res, sent, elapsed, dir }
  } finally {
    clearTimeout(watchdog)
    if (fs.existsSync(capture)) pids.add(JSON.parse(fs.readFileSync(capture, 'utf8')).pid)
  }
}

async function check(name, test) {
  checks++
  try { await test(); console.log(`ok ${name}`) } catch (error) {
    failures++
    console.log(`FAIL ${name}: ${error.message}`)
  }
}

function flag(args, name) {
  const index = args.indexOf(name)
  assert.ok(index >= 0, `missing ${name}`)
  assert.ok(index + 1 < args.length, `missing value for ${name}`)
  return args[index + 1]
}

async function main() {
  await check('print flags, trust, workspace, and output format', async () => {
    const { res, sent, dir } = await invoke()
    assert.ok(sent.args.includes('-p'), 'missing -p')
    assert.ok(sent.args.includes('--trust'), 'missing --trust')
    assert.equal(flag(sent.args, '--workspace'), dir)
    const format = flag(sent.args, '--output-format')
    assert.ok(format === 'json' || format === 'stream-json', `unexpected --output-format ${format}`)
    assert.ok(!sent.args.includes('--model'), 'cursor/default must omit --model')
    assert.ok(!sent.args.includes('--force'), 'read-only tools must omit --force')
    assert.deepEqual(res.errors, [])
  })
  for (const [model, name] of [['cursor/default', null], ['cursor/composer-2', 'composer-2']]) {
    await check(`model flag for ${model}`, async () => {
      const { sent } = await invoke({ model })
      if (name) assert.equal(flag(sent.args, '--model'), name)
      else assert.ok(!sent.args.includes('--model'), 'default must omit --model')
    })
  }
  for (const tools of ['', 'Read,Glob,Grep', 'Bash', 'Read,Write', 'Read,Edit']) {
    await check(`force for ${tools || 'no tools'}`, async () => {
      const { sent } = await invoke({ tools })
      assert.equal(sent.args.includes('--force'), /Bash|Write|Edit/.test(tools))
    })
  }
  await check('name becomes first prompt line', async () => {
    const { sent } = await invoke({ name: 'agent-label', prompt: 'User prompt marker\nSecond line' })
    assert.equal(sent.stdin.split('\n')[0], '[agent-label]')
    assert.ok(sent.stdin.includes('User prompt marker\nSecond line'), 'user prompt missing from stdin')
  })
  await check('plain text reply', async () => {
    const { res } = await invoke({}, { reply: 'Plain reply.\n' })
    assert.equal(res.text, 'Plain reply.\n')
    assert.equal(res.json, null)
    assert.ok(!res.jsonError)
  })
  for (const value of [{ answer: 42, nested: { ok: true } }, [1, 'two'], 42, true, 'hello', null]) {
    await check(`JSON value ${JSON.stringify(value)}`, async () => {
      const reply = JSON.stringify(value)
      const { res } = await invoke({}, { reply })
      assert.equal(res.text, reply)
      assert.deepEqual(res.json, value !== null && typeof value === 'object' ? value : null)
      assert.ok(!res.jsonError)
    })
  }
  await check('JSON extracted from reply', async () => {
    const { res } = await invoke({}, { reply: 'Result:\n```json\n{"answer":42}\n```' })
    assert.deepEqual(res.json, { answer: 42 })
    assert.ok(!res.jsonError)
  })
  await check('malformed JSON reports jsonError without inner JSON fallback', async () => {
    const { res } = await invoke({}, { reply: '{"nested":{},}' })
    assert.ok(res.jsonError, 'malformed JSON must produce jsonError')
    assert.ok(res.json == null, 'malformed JSON must not produce json')
  })
  await check('timeout terminates sleeping process promptly', async () => {
    const { res, sent, elapsed } = await invoke({ timeoutMs: 350 }, { sleep: 10000 })
    assert.ok(res.errors.some(error => error.startsWith('timeout after')), JSON.stringify(res.errors))
    assert.ok(elapsed < 2000, `timeout took ${Math.round(elapsed)} ms (limit 2000 ms)`)
    assert.ok(!alive(sent.pid), 'fake process remains alive after timeout resolution')
  })
  for (const source of ['stderr', 'result']) {
    await check(`usage limit via ${source} classified as runner`, async () => {
      const message = 'Usage limit reached. Rate limit exceeded; try again later.'
      const fake = source === 'stderr'
        ? { stderr: message, exit: 1, reply: '' }
        : { reply: message, exit: 1 }
      const { res } = await invoke({}, fake)
      assert.ok(res.errors.some(error => error.startsWith('runner error: usage limit')), JSON.stringify(res.errors))
      assert.equal(classify(res, res.errors), 'runner')
    })
  }
  await check('non-zero exit reports exit error', async () => {
    const { res } = await invoke({}, { exit: 23, stderr: 'Synthetic process failure', reply: '' })
    assert.ok(res.errors.some(error => error.startsWith('exit')), JSON.stringify(res.errors))
  })
}

main().catch(error => { failures++; console.log(`FAIL test harness: ${error.message}`) }).finally(() => {
  for (const pid of pids) {
    try { if (alive(pid)) process.kill(pid, 'SIGKILL') } catch (error) {
      failures++; console.log(`FAIL cleanup: ${error.message}`)
    }
  }
  if (originalPath === undefined) delete process.env.PATH
  else process.env.PATH = originalPath
  fs.rmSync(root, { recursive: true, force: true })
  console.log(failures ? `${failures} failure(s) across ${checks} checks` : 'all checks passed')
  process.exit(failures ? 1 : 0)
})
