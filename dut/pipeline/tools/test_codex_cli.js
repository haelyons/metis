'use strict'
// Independent black-box contract tests. Never inspect the runner's implementation.
// Run: node tools/test_codex_cli.js. No network, dependencies, or real Codex runs.
const assert = require('node:assert/strict')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const { performance } = require('node:perf_hooks')
const { run } = require('../idea/codex_cli.js')
const { classify } = require('../idea/understudy.js')

const root = fs.mkdtempSync(path.join(os.tmpdir(), 'test-codex-cli-'))
const bin = path.join(root, 'bin')
fs.mkdirSync(bin)
fs.writeFileSync(path.join(bin, 'codex'), `#!${process.execPath}
'use strict'
const fs = require('node:fs')
const args = process.argv.slice(2)
const stdin = fs.readFileSync(0, 'utf8')
fs.writeFileSync(process.env.TEST_CODEX_CAPTURE, JSON.stringify({ args, stdin, pid: process.pid }))
const finish = () => {
  const output = args.indexOf('-o')
  if (output < 0 || !args[output + 1]) {
    process.stderr.write('fake codex: missing -o path')
    process.exit(98)
  }
  fs.writeFileSync(args[output + 1], process.env.TEST_CODEX_REPLY)
  const events = JSON.parse(process.env.TEST_CODEX_EVENTS)
  for (let i = 0; i < events.length; i++) {
    // Deliberately leave the last event unterminated, as a stream may end there.
    fs.writeSync(1, JSON.stringify(events[i]) + (i + 1 < events.length ? '\\n' : ''))
  }
  fs.writeSync(2, process.env.TEST_CODEX_STDERR)
  process.exit(Number(process.env.TEST_CODEX_EXIT))
}
setTimeout(finish, Number(process.env.TEST_CODEX_SLEEP))
`, { mode: 0o755 })

// `codex exec --help` confirms --json emits JSONL but does not specify usage fields.
// Assumed real exec shape: {type:'turn.completed', usage:{input_tokens,
// cached_input_tokens, output_tokens}}. Cached tokens are a subset of input tokens.
const usageEvents = [
  { type: 'thread.started', thread_id: 'black-box-thread' },
  { type: 'item.completed', item: { id: 'message-1', type: 'agent_message', text: 'stdout is not the reply file' } },
  { type: 'turn.completed', usage: { input_tokens: 13, cached_input_tokens: 3, output_tokens: 7 } },
  { type: 'turn.completed', usage: { input_tokens: 17, cached_input_tokens: 5, output_tokens: 11 } },
]
const originalPath = process.env.PATH
// Also guard runners that inherit PATH without merging the supplied env.
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
    TEST_CODEX_CAPTURE: capture,
    TEST_CODEX_REPLY: fake.reply ?? 'file reply\n',
    TEST_CODEX_EVENTS: JSON.stringify(fake.events ?? usageEvents),
    TEST_CODEX_STDERR: fake.stderr ?? '',
    TEST_CODEX_EXIT: String(fake.exit ?? 0),
    TEST_CODEX_SLEEP: String(fake.sleep ?? 0),
  }
  let watchdog
  const started = performance.now()
  try {
    const res = await Promise.race([
      run({ model: 'codex/default@low', prompt: 'User prompt marker\nSecond line', cwd: dir,
        timeoutMs: 3000, rawPath: path.join(dir, 'raw.jsonl'), tools: 'Read,Glob,Grep',
        ...options, env }),
      new Promise((_, reject) => {
        watchdog = setTimeout(() => reject(new Error('runner did not settle within 6000 ms')), 6000)
      }),
    ])
    const elapsed = performance.now() - started
    assert.ok(fs.existsSync(capture), 'fake codex was not invoked through PATH')
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
  await check('exec flags, cwd, and output file', async () => {
    const { res, sent, dir } = await invoke()
    assert.equal(sent.args[0], 'exec')
    for (const name of ['--json', '--skip-git-repo-check', '--ephemeral']) assert.ok(sent.args.includes(name), `missing ${name}`)
    assert.equal(flag(sent.args, '-C'), dir)
    assert.ok(flag(sent.args, '-o'))
    assert.equal(res.text, 'file reply\n', 'text must come from -o, preserving whitespace')
    assert.deepEqual(res.errors, [])
  })
  for (const tools of ['', 'Read,Glob,Grep', 'Bash', 'Read,Write', 'Read,Edit']) {
    await check(`1 sandbox for ${tools || 'no tools'}`, async () => {
      const { sent } = await invoke({ tools })
      assert.equal(flag(sent.args, '-s'), /Bash|Write|Edit/.test(tools) ? 'workspace-write' : 'read-only')
    })
  }
  for (const [model, name, effort] of [['codex/default@low', null, 'low'], ['codex/gpt-x@high', 'gpt-x', 'high']]) {
    await check(`2 model and effort for ${model}`, async () => {
      const { sent } = await invoke({ model })
      if (name) assert.equal(flag(sent.args, '-m'), name)
      else assert.ok(!sent.args.includes('-m'), 'default must omit -m')
      assert.ok(sent.args.some((arg, index) => arg === '-c' && sent.args[index + 1] === `model_reasoning_effort=${effort}`), 'missing effort config')
    })
  }
  await check('3 prompt on stdin and system prompt forwarded', async () => {
    const prompt = 'User prompt marker\nSecond line'
    const systemPrompt = 'System role marker: preserve this instruction.'
    const { sent } = await invoke({ prompt, systemPrompt })
    assert.ok(sent.stdin.includes(prompt), 'user prompt missing from stdin')
    const inStdin = sent.stdin.includes(systemPrompt)
    const inConfig = sent.args.some((arg, index) => ['-c', '--config'].includes(arg) && (sent.args[index + 1] || '').includes(systemPrompt))
    assert.ok(inStdin || inConfig, 'system prompt missing from stdin and config')
    // Accept both contract-permitted transports; print the observed one for reviewers.
    console.log(`observed system prompt transport: ${inStdin ? 'stdin' : 'config option'}`)
  })
  await check('4 plain text reply', async () => {
    const { res } = await invoke({}, { reply: 'Plain reply.\n' })
    assert.equal(res.text, 'Plain reply.\n')
    assert.equal(res.json, null)
    assert.ok(!res.jsonError)
  })
  for (const value of [{ answer: 42, nested: { ok: true } }, [1, 'two'], 42, true, 'hello', null]) {
    await check(`4 JSON value ${JSON.stringify(value)}`, async () => {
      const reply = JSON.stringify(value)
      const { res } = await invoke({}, { reply })
      assert.equal(res.text, reply)
      assert.deepEqual(res.json, value !== null && typeof value === 'object' ? value : null)
      assert.ok(!res.jsonError)
    })
  }
  await check('4 JSON extracted from reply', async () => {
    const { res } = await invoke({}, { reply: 'Result:\n```json\n{"answer":42}\n```' })
    assert.deepEqual(res.json, { answer: 42 })
    assert.ok(!res.jsonError)
  })
  await check('4 malformed JSON reports jsonError without inner JSON fallback', async () => {
    const { res } = await invoke({}, { reply: '{"nested":{},}' })
    assert.ok(res.jsonError, 'malformed JSON must produce jsonError')
    assert.ok(res.json == null, 'malformed JSON must not produce json')
  })
  await check('5 usage events summed, including final unterminated event', async () => {
    const { res } = await invoke()
    assert.equal(res.tokens.input, 30)
    assert.equal(res.tokens.output, 18)
    assert.equal(res.tokens.cache_read, 8)
  })
  await check('6 timeout terminates sleeping process promptly', async () => {
    const { res, sent, elapsed } = await invoke({ timeoutMs: 350 }, { sleep: 10000 })
    assert.ok(res.errors.some(error => error.startsWith('timeout after')), JSON.stringify(res.errors))
    // Allow process startup and CI scheduling; still far below the fake's 10-second sleep.
    assert.ok(elapsed < 2000, `timeout took ${Math.round(elapsed)} ms (limit 2000 ms)`)
    assert.ok(!alive(sent.pid), 'fake process remains alive after timeout resolution')
  })
  for (const source of ['stderr', 'event']) {
    await check(`7 usage limit via ${source} classified as runner`, async () => {
      const message = 'Usage limit reached. Rate limit exceeded; try again later.'
      const fake = source === 'stderr' ? { stderr: message, exit: 1 }
        : { events: [{ type: 'turn.failed', error: { message } }], exit: 1 }
      const { res } = await invoke({}, fake)
      assert.ok(res.errors.some(error => error.startsWith('runner error: usage limit')), JSON.stringify(res.errors))
      assert.equal(classify(res, res.errors), 'runner')
    })
  }
  await check('8 non-zero exit reports exit error', async () => {
    const { res } = await invoke({}, { exit: 23, stderr: 'Synthetic process failure' })
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
