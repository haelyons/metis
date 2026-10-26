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
const readline = require('node:readline')
const args = process.argv.slice(2)
const capture = { args, stdin: '', pid: process.pid, requests: [] }
const save = () => fs.appendFileSync(process.env.TEST_CODEX_CAPTURE, JSON.stringify(capture) + '\\n')
const events = JSON.parse(process.env.TEST_CODEX_EVENTS)
const send = message => fs.writeSync(1, JSON.stringify(message) + '\\n')
if (args[0] === 'app-server') {
  save()
  if (process.env.TEST_CODEX_APP_FAIL === '1') {
    fs.writeSync(2, 'Synthetic app-server failure\\n')
    process.exit(23)
  }
  const input = readline.createInterface({ input: process.stdin })
  input.on('line', line => {
    capture.stdin += line + '\\n'
    const request = JSON.parse(line)
    capture.requests.push(request)
    save()
    const respond = result => send({ id: request.id, result })
    switch (request.method) {
      case 'initialize': respond({ userAgent: 'fake-codex' }); break
      case 'thread/start': respond({ thread: { id: 'black-box-thread' } }); break
      case 'thread/name/set': respond({}); break
      case 'turn/start': {
        respond({ turn: { id: 'turn-1', status: 'inProgress', items: [] } })
        setTimeout(() => {
          const threadId = 'black-box-thread', turnId = 'turn-1'
          fs.writeSync(2, process.env.TEST_CODEX_STDERR)
          for (const event of events) {
            if (event.type === 'turn.completed') {
              const usage = event.usage
              send({ method: 'thread/tokenUsage/updated', params: { threadId, turnId,
                tokenUsage: { total: { inputTokens: usage.input_tokens,
                  cachedInputTokens: usage.cached_input_tokens, outputTokens: usage.output_tokens,
                  reasoningOutputTokens: 0, totalTokens: usage.input_tokens + usage.output_tokens },
                  last: { inputTokens: usage.input_tokens, cachedInputTokens: usage.cached_input_tokens,
                    outputTokens: usage.output_tokens, reasoningOutputTokens: 0,
                    totalTokens: usage.input_tokens + usage.output_tokens } } } })
            }
            if (event.type === 'turn.failed') {
              send({ method: 'error', params: { threadId, turnId, error: event.error, willRetry: false } })
            }
          }
          const text = process.env.TEST_CODEX_REPLY
          const split = Math.floor(text.length / 2)
          for (const delta of [text.slice(0, split), text.slice(split)]) {
            send({ method: 'item/agentMessage/delta', params: { threadId, turnId, itemId: 'message-1', delta } })
          }
          send({ method: 'item/completed', params: { threadId, turnId,
            item: { id: 'message-1', type: 'agentMessage', text } } })
          const error = events.find(event => event.type === 'turn.failed')?.error
          send({ method: 'turn/completed', params: { threadId,
            turn: { id: turnId, status: error ? 'failed' : 'completed', items: [], error } } })
        }, Number(process.env.TEST_CODEX_SLEEP))
        break
      }
      default:
        if (request.id !== undefined) {
          send({ id: request.id, error: { code: -32601, message: 'Unsupported fake method: ' + request.method } })
        }
    }
  })
} else if (args[0] === 'exec') {
  capture.stdin = fs.readFileSync(0, 'utf8')
  save()
  setTimeout(() => {
    const output = args.indexOf('-o')
    if (output < 0 || !args[output + 1]) process.exit(98)
    fs.writeFileSync(args[output + 1], process.env.TEST_CODEX_REPLY)
    for (let i = 0; i < events.length; i++) {
      // Exec may end with an unterminated JSONL event.
      fs.writeSync(1, JSON.stringify(events[i]) + (i + 1 < events.length ? '\\n' : ''))
    }
    fs.writeSync(2, process.env.TEST_CODEX_STDERR)
    process.exit(Number(process.env.TEST_CODEX_EXIT))
  }, Number(process.env.TEST_CODEX_SLEEP))
} else {
  fs.writeSync(2, 'Unexpected codex command: ' + args[0])
  process.exit(97)
}
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
    ...fake.env,
    TEST_CODEX_CAPTURE: capture,
    TEST_CODEX_APP_FAIL: fake.appFail ? '1' : '0',
    TEST_CODEX_REPLY: fake.reply ?? 'file reply\n',
    TEST_CODEX_EVENTS: JSON.stringify(fake.events ?? usageEvents),
    TEST_CODEX_STDERR: fake.stderr ?? '',
    TEST_CODEX_EXIT: String(fake.exit ?? 0),
    TEST_CODEX_SLEEP: String(fake.sleep ?? 0),
  }
  let watchdog
  const originalEphemeral = process.env.CODEX_EPHEMERAL
  if (fake.env?.CODEX_EPHEMERAL === undefined) delete process.env.CODEX_EPHEMERAL
  else process.env.CODEX_EPHEMERAL = fake.env.CODEX_EPHEMERAL
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
    const captures = fs.readFileSync(capture, 'utf8').trim().split('\n').map(line => JSON.parse(line))
    for (const item of captures) pids.add(item.pid)
    const sent = captures[captures.length - 1]
    if (!fake.appFail && !fake.sleep) {
      assert.equal(sent.args[0], 'app-server', `unexpected fallback: ${JSON.stringify(res.errors)}`)
      assert.ok(sent.requests.some(request => request.method === 'turn/start'), 'app-server never received turn/start')
    }
    return { res, sent, captures, elapsed, dir }
  } finally {
    if (originalEphemeral === undefined) delete process.env.CODEX_EPHEMERAL
    else process.env.CODEX_EPHEMERAL = originalEphemeral
    clearTimeout(watchdog)
    if (fs.existsSync(capture)) {
      for (const line of fs.readFileSync(capture, 'utf8').trim().split('\n')) pids.add(JSON.parse(line).pid)
    }
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
  await check('app-server initializes, starts and names thread before turn', async () => {
    const { res, sent, captures, dir } = await invoke({ name: 'Black-box named conversation' })
    assert.equal(sent.args[0], 'app-server')
    assert.ok(captures.every(item => item.args[0] === 'app-server'), 'successful app-server must not fall back')
    const requests = sent.requests.filter(request => request.id !== undefined)
    assert.deepEqual(requests.map(request => request.method), ['initialize', 'thread/start', 'thread/name/set', 'turn/start'])
    assert.equal(requests[1].params.cwd, dir)
    assert.equal(requests[2].params.threadId, 'black-box-thread')
    assert.equal(requests[2].params.name, 'Black-box named conversation')
    assert.equal(requests[3].params.threadId, 'black-box-thread')
    assert.ok(JSON.stringify(requests[3].params.input).includes('User prompt marker'))
    assert.equal(res.text, 'file reply\n')
    assert.deepEqual(res.errors, [])
  })
  await check('app-server usage notification maps token fields', async () => {
    const { res } = await invoke({}, { events: [usageEvents[2]] })
    assert.equal(res.tokens.input, 13)
    assert.equal(res.tokens.output, 7)
    assert.equal(res.tokens.cache_read, 3)
  })
  await check('app-server failure falls back to exec and records error', async () => {
    const { res, captures } = await invoke({}, { appFail: true, reply: '{"fallback":true}' })
    assert.deepEqual([...new Set(captures.map(item => item.args[0]))], ['app-server', 'exec'])
    assert.equal(res.text, '{"fallback":true}')
    assert.deepEqual(res.json, { fallback: true })
    assert.equal(res.tokens.input, 30)
    assert.ok(res.errors.some(error => /app.?server|fallback/i.test(error)), JSON.stringify(res.errors))
  })
  await check('exec flags, cwd, and output file', async () => {
    const { res, sent, dir } = await invoke({}, { appFail: true })
    assert.equal(sent.args[0], 'exec')
    for (const name of ['--json', '--skip-git-repo-check']) assert.ok(sent.args.includes(name), `missing ${name}`)
    assert.ok(!sent.args.includes('--ephemeral'), 'default must omit --ephemeral')
    assert.equal(flag(sent.args, '-C'), dir)
    assert.ok(flag(sent.args, '-o'))
    assert.equal(res.text, 'file reply\n', 'text must come from -o, preserving whitespace')
    assert.ok(res.errors.some(error => /app.?server|fallback/i.test(error)), JSON.stringify(res.errors))
  })
  for (const value of ['1', '0']) {
    await check(`ephemeral flag with CODEX_EPHEMERAL=${value}`, async () => {
      const { sent } = await invoke({}, { appFail: true, env: { CODEX_EPHEMERAL: value } })
      assert.equal(sent.args.includes('--ephemeral'), value === '1')
    })
  }
  for (const tools of ['', 'Read,Glob,Grep', 'Bash', 'Read,Write', 'Read,Edit']) {
    await check(`1 sandbox for ${tools || 'no tools'}`, async () => {
      const { sent } = await invoke({ tools }, { appFail: true })
      assert.equal(flag(sent.args, '-s'), /Bash|Write|Edit/.test(tools) ? 'workspace-write' : 'read-only')
      assert.equal(sent.args.some((arg, index) => arg === '-c' && sent.args[index + 1] === 'sandbox_workspace_write.network_access=true'), /Bash|Write|Edit/.test(tools), 'network access config must appear only for workspace-write')
    })
  }
  for (const [model, name, effort] of [['codex/default@low', null, 'low'], ['codex/gpt-x@high', 'gpt-x', 'high']]) {
    await check(`2 model and effort for ${model}`, async () => {
      const { sent } = await invoke({ model }, { appFail: true })
      if (name) assert.equal(flag(sent.args, '-m'), name)
      else assert.ok(!sent.args.includes('-m'), 'default must omit -m')
      assert.ok(sent.args.some((arg, index) => arg === '-c' && sent.args[index + 1] === `model_reasoning_effort=${effort}`), 'missing effort config')
    })
  }
  await check('3 prompt on stdin and system prompt forwarded', async () => {
    const prompt = 'User prompt marker\nSecond line'
    const systemPrompt = 'System role marker: preserve this instruction.'
    const { sent } = await invoke({ prompt, systemPrompt }, { appFail: true })
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
  await check('5 exec usage events summed, including final unterminated event', async () => {
    const { res } = await invoke({}, { appFail: true })
    assert.equal(res.tokens.input, 30)
    assert.equal(res.tokens.output, 18)
    assert.equal(res.tokens.cache_read, 8)
  })
  await check('6 timeout terminates sleeping process promptly', async () => {
    const { res, sent, captures, elapsed } = await invoke({ timeoutMs: 350 }, { sleep: 10000 })
    assert.ok(captures.some(item => item.requests.some(request => request.method === 'turn/start')),
      'timeout must exercise an app-server turn')
    assert.ok(res.errors.some(error => error.startsWith('timeout after')), JSON.stringify(res.errors))
    // Allow process startup and CI scheduling; still far below the fake's 10-second sleep.
    assert.ok(elapsed < 2000, `timeout took ${Math.round(elapsed)} ms (limit 2000 ms)`)
    assert.ok(!alive(sent.pid), 'fake process remains alive after timeout resolution')
  })
  await check('7 app-server usage limit classified as runner', async () => {
    const message = 'Usage limit reached. Rate limit exceeded; try again later.'
    const { res } = await invoke({}, { events: [{ type: 'turn.failed', error: { message } }] })
    assert.ok(res.errors.some(error => error.startsWith('runner error: usage limit')), JSON.stringify(res.errors))
    assert.equal(classify(res, res.errors), 'runner')
  })
  for (const source of ['stderr', 'event']) {
    await check(`7 exec usage limit via ${source} classified as runner`, async () => {
      const message = 'Usage limit reached. Rate limit exceeded; try again later.'
      const fake = source === 'stderr' ? { stderr: message, exit: 1 }
        : { events: [{ type: 'turn.failed', error: { message } }], exit: 1 }
      const { res } = await invoke({}, { ...fake, appFail: true })
      assert.ok(res.errors.some(error => error.startsWith('runner error: usage limit')), JSON.stringify(res.errors))
      assert.equal(classify(res, res.errors), 'runner')
    })
  }
  await check('8 non-zero exit reports exit error', async () => {
    const { res } = await invoke({}, { appFail: true, exit: 23, stderr: 'Synthetic process failure' })
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
