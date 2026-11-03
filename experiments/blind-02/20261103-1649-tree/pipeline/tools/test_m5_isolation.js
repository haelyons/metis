#!/usr/bin/env node
'use strict'

// Black-box U28 isolation contracts (m5/SCHEMAS.md, wf agent setting `isolation`).
// Do not inspect implementation files or git diffs.
// Usage: node tools/test_m5_isolation.js
// Every case runs real workflow dispatch (idea/wf.js, family codex) with a local fake
// `codex` on PATH; no model or network. Requires a host where top-level bubblewrap works.
// The fake models this host: inside any user namespace other than the host's, a Codex
// sandbox other than danger-full-access must create a nested namespace, which Ubuntu's
// AppArmor bwrap-userns-restrict denies, so every command fails exactly as recorded in
// experiments/positive-openmm/run6/agent/wf/agents/0010-tests/codex-1.jsonl.
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const assert = require('node:assert/strict')
const { spawn } = require('node:child_process')
const { randomUUID } = require('node:crypto')
const ROOT = path.resolve(__dirname, '..')
const REAL_HOME = os.homedir()
const HOST_USERNS = fs.readlinkSync('/proc/self/ns/user')
const BWRAP = '/usr/bin/bwrap'
const readJSON = file => JSON.parse(fs.readFileSync(file, 'utf8'))

function snapshot(directory) {
  const result = {}
  ;(function visit(parent) {
    for (const entry of fs.readdirSync(parent, { withFileTypes: true })) {
      const file = path.join(parent, entry.name), relative = path.relative(directory, file)
      const stat = fs.lstatSync(file)
      if (entry.isDirectory()) { result[relative + '/'] = stat.mode & 0o7777; visit(file) }
      else result[relative] = [stat.mode & 0o7777, entry.isFile() ? fs.readFileSync(file, 'base64') : fs.readlinkSync(file)]
    }
  })(directory)
  return result
}

function fakeCodex(config) {
  return `#!${process.execPath}
'use strict'
const fs = require('node:fs'), path = require('node:path'), os = require('node:os')
const { spawnSync } = require('node:child_process')
const C = ${JSON.stringify(config)}
const args = process.argv.slice(2)
if (args.includes('--version')) { console.log('codex 0.0.0-test'); process.exit(0) }
if (args[0] !== 'exec' && args[0] !== 'app-server') process.exit(0)
// Host-visible only outside the isolation namespace (outer-wrapper cases).
try { fs.appendFileSync(C.marker, JSON.stringify({ args, pid: process.pid, ephemeral: process.env.CODEX_EPHEMERAL ?? null }) + '\\n') } catch {}
const DENIED = 'bwrap: No permissions to create a new namespace, likely because the kernel does not allow non-privileged user namespaces. See <https://deb.li/bubblewrap> or <file:///usr/share/doc/bubblewrap/README.Debian.gz>.\\n'
const POLICY = { dangerFullAccess: 'danger-full-access', workspaceWrite: 'workspace-write', readOnly: 'read-only', externalSandbox: 'external-sandbox' }
const unquote = value => String(value).trim().replace(/^["']|["']$/g, '')
function cliMode() {
  let flag = null, config = null
  for (let i = 0; i < args.length; i++) {
    const arg = args[i]
    if (arg === '-s' || arg === '--sandbox') flag = args[++i]
    else if (arg.startsWith('--sandbox=')) flag = arg.slice('--sandbox='.length)
    else if (arg === '--dangerously-bypass-approvals-and-sandbox' || arg === '--yolo') flag = 'danger-full-access'
    else if (arg === '--full-auto') flag = 'workspace-write'
    else if ((arg === '-c' || arg === '--config') && /^sandbox_mode\\s*=/.test(args[i + 1] || '')) config = unquote(args[++i].replace(/^sandbox_mode\\s*=/, ''))
  }
  return flag ?? config
}
let userns = null
try { userns = fs.readlinkSync('/proc/self/ns/user') } catch {}
const inside = userns !== C.hostUserns
function attempt(fn) {
  try { return { ok: true, detail: fn() ?? null } } catch (error) { return { ok: false, error: String(error.code || error.message) } }
}
function shell(command, ...rest) {
  const result = spawnSync('/bin/sh', ['-c', command, 'sh', ...rest], { encoding: 'utf8' })
  if (result.error) throw result.error
  if (result.status !== 0) throw new Error('exit ' + result.status + ': ' + result.stderr.trim())
  return result.stdout
}
function probes() {
  const p = C.paths
  return {
    command: attempt(() => shell('printf ran > "$1" && cat "$1"', p.viewCommand)),
    commandTmp: attempt(() => shell('f="\${TMPDIR:-/tmp}/$1"; printf ran > "$f" && cat "$f"', C.id + '-cmd')),
    viewRead: attempt(() => fs.readFileSync(p.viewInput, 'utf8')),
    viewWrite: attempt(() => fs.writeFileSync(p.viewDirect, 'direct')),
    viewMkdir: attempt(() => fs.mkdirSync(p.viewDir)),
    viewChange: attempt(() => fs.appendFileSync(p.viewInput, 'changed')),
    repoWrite: attempt(() => fs.writeFileSync(p.repo, 'escape')),
    realHomeWrite: attempt(() => fs.writeFileSync(p.realHome, 'escape')),
    privateHome: attempt(() => {
      if (!process.env.HOME || path.resolve(process.env.HOME) === path.resolve(C.realHome)) throw new Error('HOME is the real HOME')
      fs.writeFileSync(path.join(process.env.HOME, C.id), 'home')
      return process.env.HOME
    }),
    tmpdir: attempt(() => { const file = path.join(os.tmpdir(), C.id); fs.writeFileSync(file, 'tmp'); return file }),
    slashTmp: attempt(() => fs.writeFileSync(path.join('/tmp', C.id + '-slash'), 'tmp')),
  }
}
// Observations travel in the reply: a read-only role has no host path to write to.
function observe(mode) {
  const blocked = inside && mode !== 'danger-full-access'
  const commands = blocked ? ['ls -la ' + C.paths.view] : []
  const p = blocked ? null : probes()
  return { commands, reply: JSON.stringify({ v: blocked ? 'blocked' : 'ok', sandbox: mode, inside, blocked,
    probes: p, error: blocked ? 'Blocked: the execution sandbox fails with ' + DENIED.split(',')[0] : null }) }
}
if (args[0] === 'exec') {
  fs.readFileSync(0, 'utf8')
  const mode = cliMode()
  const { commands, reply } = observe(mode)
  const output = args.indexOf('-o')
  if (output !== -1 && args[output + 1]) fs.writeFileSync(args[output + 1], reply)
  const events = [{ type: 'thread.started', thread_id: 'u28-' + C.id }]
  commands.forEach((command, i) => events.push({ type: 'item.completed', item: { id: 'item_' + i, type: 'command_execution',
    command: "/bin/bash -c '" + command + "'", aggregated_output: DENIED, exit_code: 1, status: 'failed' } }))
  events.push({ type: 'item.completed', item: { id: 'reply', type: 'agent_message', text: reply } })
  events.push({ type: 'turn.completed', usage: { input_tokens: 0, cached_input_tokens: 0, output_tokens: 0 } })
  for (const event of events) fs.writeSync(1, JSON.stringify(event) + '\\n')
  process.exit(0)
}
// app-server: newline-delimited JSON-RPC on stdin/stdout.
const send = message => fs.writeSync(1, JSON.stringify(message) + '\\n')
let threadMode = null, buffer = ''
const threadId = 'u28-' + C.id, turnId = 'turn-1'
process.stdin.on('data', chunk => {
  buffer += chunk
  let index
  while ((index = buffer.indexOf('\\n')) !== -1) {
    const line = buffer.slice(0, index); buffer = buffer.slice(index + 1)
    if (!line.trim()) continue
    const request = JSON.parse(line)
    const respond = result => { if (request.id !== undefined) send({ id: request.id, result }) }
    const params = request.params || {}
    try { fs.appendFileSync(C.marker, JSON.stringify({ method: request.method, params, pid: process.pid }) + '\\n') } catch {}
    switch (request.method) {
      case 'initialize': respond({ userAgent: 'fake-codex' }); break
      case 'thread/start': case 'thread/resume':
        if (params.sandbox) threadMode = params.sandbox
        respond({ thread: { id: threadId } }); break
      case 'turn/start': {
        let mode = threadMode ?? cliMode()
        if (params.sandboxPolicy?.type) mode = POLICY[params.sandboxPolicy.type] || params.sandboxPolicy.type
        respond({ turn: { id: turnId, status: 'inProgress', items: [] } })
        const { commands, reply } = observe(mode)
        commands.forEach((command, i) => send({ method: 'item/completed', params: { threadId, turnId, item: { id: 'item_' + i,
          type: 'commandExecution', command: "/bin/bash -c '" + command + "'", aggregatedOutput: DENIED, exitCode: 1, status: 'failed' } } }))
        send({ method: 'item/completed', params: { threadId, turnId, item: { id: 'reply', type: 'agentMessage', text: reply } } })
        send({ method: 'thread/tokenUsage/updated', params: { threadId, turnId, tokenUsage: {
          total: { inputTokens: 0, cachedInputTokens: 0, outputTokens: 0, reasoningOutputTokens: 0, totalTokens: 0 },
          last: { inputTokens: 0, cachedInputTokens: 0, outputTokens: 0, reasoningOutputTokens: 0, totalTokens: 0 } } } })
        send({ method: 'turn/completed', params: { threadId, turn: { id: turnId, status: 'completed', items: [] } } })
        break
      }
      default: respond({})
    }
  }
})
process.stdin.on('end', () => process.exit(0))
`
}

const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_isolation_'))
const escapes = []
let checks = 0, failures = 0
function check(label, fn) {
  checks++
  try { fn(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${error.message}`) }
}

// outer: null, 'no-bwrap' (bubblewrap binary unusable) or 'no-userns' (namespaces unavailable).
// extraEnv: variables added to wf's environment; CODEX_EPHEMERAL is unset unless given here.
async function dispatch(name, { role, isolated, outer = null, extraEnv = {} }) {
  const id = 'u28-' + name + '-' + randomUUID()
  const root = path.join(scratch, name)
  const view = path.join(root, 'view'), hidden = path.join(root, 'hidden'), out = path.join(root, 'wf')
  const bin = path.join(view, '.probe-bin')
  fs.mkdirSync(bin, { recursive: true })
  fs.mkdirSync(hidden)
  fs.writeFileSync(path.join(hidden, 'secret'), 'hidden')
  fs.writeFileSync(path.join(view, 'input.txt'), 'input')
  const paths = {
    view, viewInput: path.join(view, 'input.txt'), viewCommand: path.join(view, 'cmd-wrote.txt'),
    viewDirect: path.join(view, 'direct-wrote.txt'), viewDir: path.join(view, 'made-dir'),
    repo: path.join(ROOT, 'tools', '.' + id + '-escape'), realHome: path.join(REAL_HOME, '.' + id + '-escape'),
  }
  escapes.push(paths.repo, paths.realHome, path.join('/tmp', id + '-slash'), path.join('/tmp', id), path.join('/tmp', id + '-cmd'))
  const marker = path.join(root, 'fake-ran.jsonl')
  fs.writeFileSync(path.join(bin, 'codex'), fakeCodex({ id, hostUserns: HOST_USERNS, realHome: REAL_HOME, paths, marker }), { mode: 0o755 })
  const isolation = { directory: view, hidden: [hidden], box_access: false }
  const placement = isolated ? `isolation:${JSON.stringify(isolation)}` : `cwd:${JSON.stringify(view)}`
  const workflow = path.join(root, 'main.js'), argsFile = path.join(root, 'args.json')
  fs.writeFileSync(workflow, `export const meta = {name:'isolation-u28',description:'U28 isolation probe'}
let value = null, error = null
try {
  value = await agent('Run the local isolation probe.', {label:'probe', agentType:${JSON.stringify(role)}, model:'sonnet',
    fresh:true, repairable:false, ${placement}, schema:{type:'object',required:['v'],properties:{v:{type:'string'}}}})
} catch (e) { error = String(e?.message || e) }
return {value, error}
`)
  fs.writeFileSync(argsFile, '{}\n')
  const before = snapshot(view)
  const env = { ...process.env, PATH: bin + path.delimiter + process.env.PATH }
  delete env.WF_STUB
  delete env.CODEX_EPHEMERAL
  Object.assign(env, extraEnv)
  let command = [process.execPath, path.join(ROOT, 'idea', 'wf.js'), '--script', workflow, '--args', argsFile, '--out', out,
    '--family', 'codex', '--mode', 'primary-only', '--disable-family', 'claude', '--disable-family', 'opencode', '--disable-family', 'cursor']
  if (outer) {
    const wrapper = [BWRAP, '--die-with-parent', '--dev-bind', '/', '/']
    if (outer === 'no-userns') wrapper.push('--unshare-user', '--disable-userns')
    if (outer === 'no-bwrap') {
      // Mask every bubblewrap reachable by absolute path or PATH.
      const candidates = new Set([BWRAP, '/bin/bwrap', '/usr/local/bin/bwrap',
        ...process.env.PATH.split(path.delimiter).filter(Boolean).map(dir => path.join(dir, 'bwrap'))])
      for (const file of candidates) if (fs.existsSync(file)) wrapper.push('--ro-bind', '/dev/null', file)
    }
    command = [...wrapper, '--', ...command]
  }
  const errorFile = path.join(root, 'stderr'), errorFd = fs.openSync(errorFile, 'w')
  let child
  try {
    child = await new Promise(resolve => {
      const proc = spawn(command[0], command.slice(1), { cwd: root, env, stdio: ['ignore', 'ignore', errorFd], timeout: 60000 })
      let error
      proc.on('error', value => { error = value })
      proc.on('close', (status, signal) => resolve({ status, signal, error }))
    })
  } finally { fs.closeSync(errorFd) }
  const resultFile = path.join(out, 'result.json')
  const result = fs.existsSync(resultFile) ? readJSON(resultFile) : null
  // Locate the workflow's {value, error} return wherever wf records it.
  function find(node) {
    if (!node || typeof node !== 'object') return null
    if ('value' in node && 'error' in node && Object.keys(node).length === 2) return node
    for (const child of Object.values(node)) { const hit = find(child); if (hit) return hit }
    return null
  }
  const returned = find(result)
  const reply = returned?.value && typeof returned.value === 'object' ? returned.value : null
  const stderr = fs.readFileSync(errorFile, 'utf8').trim()
  const ran = fs.existsSync(marker) ? fs.readFileSync(marker, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : []
  const agents = path.join(out, 'agents')
  const metas = fs.existsSync(agents) ? fs.readdirSync(agents).map(name => path.join(agents, name, 'meta.json'))
    .filter(file => fs.existsSync(file)).map(readJSON) : []
  const diagnostic = `child=${JSON.stringify({ status: child.status, signal: child.signal, error: child.error?.message })} ` +
    `returned=${JSON.stringify(returned ?? result)?.slice(0, 600)} meta=${JSON.stringify(metas.map(m => ({ role: m.role, kind: m.kind, errors: m.errors })))?.slice(0, 600)} ` +
    `stderr=${stderr.slice(-400)}`
  return { id, root, view, paths, before, after: snapshot(view), child, result, returned, reply, ran, metas, diagnostic }
}

function sandboxIs(run, expected) {
  assert.ok(run.reply, 'fake codex reply not returned: ' + run.diagnostic)
  assert.equal(run.reply.sandbox, expected, `dispatched sandbox ${JSON.stringify(run.reply.sandbox)}` +
    (run.reply.blocked ? ` -> every command failed: ${run.reply.error}` : ''))
}
function probe(run, name) {
  assert.ok(run.reply, 'fake codex reply not returned: ' + run.diagnostic)
  assert.ok(run.reply.probes, `no probes ran (blocked=${run.reply.blocked}, sandbox=${run.reply.sandbox}): ${run.reply.error}`)
  return run.reply.probes[name]
}
// Every recorded invocation (CLI args, app-server thread/turn params) outside the namespace.
function noDangerRequested(run) {
  for (const entry of run.ran) {
    if (entry.args) {
      for (const arg of ['--dangerously-bypass-approvals-and-sandbox', '--yolo'])
        assert.ok(!entry.args.includes(arg), `codex ${entry.args[0]} passed ${arg}`)
      assert.ok(!entry.args.some(arg => /danger-full-access/.test(arg)), `codex ${entry.args[0]} args request danger-full-access: ${JSON.stringify(entry.args)}`)
    }
    if (entry.params) {
      assert.notEqual(entry.params.sandbox, 'danger-full-access', `${entry.method} params.sandbox`)
      assert.notEqual(entry.params.sandboxPolicy?.type, 'dangerFullAccess', `${entry.method} params.sandboxPolicy`)
      assert.notEqual(entry.params.sandboxPolicy?.type, 'danger-full-access', `${entry.method} params.sandboxPolicy`)
    }
  }
}
function noEscape(run) {
  for (const file of [run.paths.repo, run.paths.realHome]) assert.equal(fs.existsSync(file), false, `wrote outside its view: ${file}`)
  for (const name of ['repoWrite', 'realHomeWrite']) {
    const result = probe(run, name)
    assert.equal(result.ok, false, `${name} succeeded inside the namespace`)
  }
}

;(async () => {
  try {
    // 1-2. Writer roles: ls-writer has Write and Bash; ls-general has Bash but no Write or Edit.
    for (const role of ['ls-writer', 'ls-general']) {
      const run = await dispatch('iso-' + role, { role, isolated: true })
      check(`isolated ${role}: Codex dispatched with danger-full-access inside the namespace [requires bubblewrap]`, () => {
        sandboxIs(run, 'danger-full-access')
        assert.equal(run.reply.inside, true, 'provider did not run inside a separate user namespace')
      })
      check(`isolated ${role}: runs a command that writes a file in its view [requires bubblewrap]`, () => {
        const result = probe(run, 'command')
        assert.equal(result.ok, true, `command failed: ${result.error}`)
        assert.equal(fs.readFileSync(run.paths.viewCommand, 'utf8'), 'ran', 'command output not in host view')
      })
      check(`isolated ${role}: view writable directly [requires bubblewrap]`, () => {
        for (const name of ['viewWrite', 'viewMkdir']) assert.equal(probe(run, name).ok, true, `${name}: ${probe(run, name).error}`)
        assert.equal(fs.readFileSync(run.paths.viewDirect, 'utf8'), 'direct')
        assert.ok(fs.statSync(run.paths.viewDir).isDirectory())
      })
      check(`isolated ${role}: cannot write into the repository or the real HOME [requires bubblewrap]`, () => noEscape(run))
      check(`isolated ${role}: private HOME is not the real HOME [requires bubblewrap]`, () => {
        const result = probe(run, 'privateHome')
        assert.equal(result.ok, true, result.error)
        assert.equal(fs.existsSync(path.join(result.detail, run.id)), false, 'private HOME survives the call')
      })
    }

    // 3. Role without Write, Edit or Bash.
    const bare = await dispatch('iso-qt-bare', { role: 'qt-bare', isolated: true })
    check('isolated qt-bare: Codex dispatched with danger-full-access inside the namespace [requires bubblewrap]', () => {
      sandboxIs(bare, 'danger-full-access')
      assert.equal(bare.reply.inside, true, 'provider did not run inside a separate user namespace')
    })
    check('isolated qt-bare: view readable but not writable [requires bubblewrap]', () => {
      assert.equal(probe(bare, 'viewRead').detail, 'input')
      for (const name of ['viewWrite', 'viewMkdir', 'viewChange', 'command'])
        assert.equal(probe(bare, name).ok, false, `${name} succeeded in a read-only view`)
    })
    check('isolated qt-bare: private HOME and temporary directory writable, commands still run [requires bubblewrap]', () => {
      for (const name of ['privateHome', 'tmpdir', 'slashTmp', 'commandTmp'])
        assert.equal(probe(bare, name).ok, true, `${name}: ${probe(bare, name).error}`)
    })
    check('isolated qt-bare: nothing it wrote survives into the view [requires bubblewrap]', () => {
      assert.ok(bare.reply?.probes, 'probes did not run: ' + bare.diagnostic)
      assert.deepEqual(bare.after, bare.before)
    })
    check('isolated qt-bare: cannot write into the repository or the real HOME [requires bubblewrap]', () => noEscape(bare))

    // 4. Non-isolated Codex calls keep their sandbox arguments.
    for (const [role, expected] of [['ls-writer', 'workspace-write'], ['ls-general', 'workspace-write'], ['qt-bare', 'read-only']]) {
      const run = await dispatch('plain-' + role, { role, isolated: false })
      check(`non-isolated ${role}: Codex keeps sandbox ${expected}`, () => {
        sandboxIs(run, expected)
        assert.equal(run.reply.inside, false)
      })
    }

    // 4b. danger-full-access follows only from dispatch inside the namespace, never from CODEX_EPHEMERAL.
    for (const [role, expected] of [['ls-writer', 'workspace-write'], ['ls-general', 'workspace-write'], ['qt-bare', 'read-only']]) {
      const run = await dispatch('ephemeral-plain-' + role, { role, isolated: false, extraEnv: { CODEX_EPHEMERAL: '1' } })
      check(`non-isolated ${role} with CODEX_EPHEMERAL=1: Codex keeps sandbox ${expected}`, () => {
        sandboxIs(run, expected)
        assert.equal(run.reply.inside, false)
      })
      check(`non-isolated ${role} with CODEX_EPHEMERAL=1: no Codex invocation requests danger-full-access`, () => {
        assert.ok(run.ran.length > 0, 'fake codex never ran: ' + run.diagnostic)
        // Fixture: the variable must reach the provider, or this case would not exercise the contract.
        assert.ok(run.ran.some(entry => entry.ephemeral === '1' || entry.args?.includes('--ephemeral')),
          'CODEX_EPHEMERAL=1 never reached the Codex invocation')
        noDangerRequested(run)
      })
    }
    for (const role of ['ls-writer', 'qt-bare']) {
      const run = await dispatch('ephemeral-iso-' + role, { role, isolated: true, extraEnv: { CODEX_EPHEMERAL: '1' } })
      check(`isolated ${role} with CODEX_EPHEMERAL=1: still danger-full-access inside the namespace [requires bubblewrap]`, () => {
        sandboxIs(run, 'danger-full-access')
        assert.equal(run.reply.inside, true, 'provider did not run inside a separate user namespace')
      })
    }

    // 5. No fallback when bubblewrap is missing or namespaces are unavailable.
    const control = await dispatch('outer-control', { role: 'ls-writer', isolated: false, outer: 'no-userns' })
    check('outer wrapper control: non-isolated call still dispatches the fake [requires bubblewrap]', () => {
      assert.ok(control.ran.length > 0, 'fake codex never ran under the outer wrapper: ' + control.diagnostic)
    })
    // Fixture self-check: a provider sandbox inside a foreign namespace fails every command, as in run6.
    check('fixture: workspace-write inside a foreign namespace blocks every command [requires bubblewrap]', () => {
      sandboxIs(control, 'workspace-write')
      assert.equal(control.reply.inside, true)
      assert.equal(control.reply.blocked, true)
      assert.equal(control.reply.probes, null)
      assert.equal(fs.existsSync(control.paths.viewCommand), false)
    })
    for (const outer of ['no-bwrap', 'no-userns']) {
      const run = await dispatch('outer-' + outer, { role: 'ls-writer', isolated: true, outer })
      check(`isolated call with ${outer === 'no-bwrap' ? 'bubblewrap missing' : 'namespaces unavailable'} fails without fallback [requires bubblewrap]`, () => {
        assert.deepEqual(run.ran, [], 'provider executed without the isolation namespace')
        assert.notEqual(run.reply?.v, 'ok', 'call returned a provider value')
        // A failed call either throws/aborts or returns null with its failure recorded in meta.json.
        assert.ok(run.returned?.error || run.child.status !== 0 || run.result?.error ||
          (run.returned && run.returned.value == null && run.metas.length > 0 && run.metas.every(m => m.errors?.length > 0 && m.kind !== 'none')),
          'call did not fail: ' + run.diagnostic)
        assert.equal(fs.existsSync(run.paths.viewCommand), false, 'something wrote into the view')
      })
    }
  } catch (error) { failures++; console.log(`FAIL test harness: ${error.stack || error.message}`) }
  finally {
    for (const file of escapes) fs.rmSync(file, { force: true })
    fs.rmSync(scratch, { recursive: true, force: true })
  }
  console.log(failures ? `\n${failures} of ${checks} check(s) FAILED` : `\nall ${checks} checks passed`)
  process.exit(failures ? 1 : 0)
})()
