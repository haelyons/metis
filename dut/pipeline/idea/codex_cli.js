'use strict'
// Persistent Codex app-server sessions, with an exec fallback, shaped like claude_cli.run.
const { spawn } = require('node:child_process')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const { parseReply } = require('./claude_cli.js')

// Agents never inherit the operator's personal MCP servers, skills, apps or network-proxy allowlist; auth stays in CODEX_HOME.
function isolation(env) {
  const home = ({ ...process.env, ...env }).CODEX_HOME || path.join(os.homedir(), '.codex')
  let servers = []
  try { servers = [...fs.readFileSync(path.join(home, 'config.toml'), 'utf8').matchAll(/^\[mcp_servers\.([A-Za-z0-9_-]+)\]/gm)].map(match => match[1]) } catch {}
  return ['--disable', 'network_proxy', '--disable', 'apps', '--disable', 'plugins', '-c', 'skills.include_instructions=false',
    ...servers.flatMap(server => ['-c', `mcp_servers.${server}.enabled=false`])]
}

function runExec({ model, prompt, cwd, timeoutMs, rawPath, tools, systemPrompt, env, addDirs, name: chatName }) {
  return new Promise(resolve => {
    const t0 = Date.now(), limit = timeoutMs || 20 * 60000
    const tokens = { input: 0, output: 0, reasoning: 0, cache_read: 0, cache_write: 0 }
    const result = { text: '', json: null, jsonError: null, sessionID: null, tokens, tokens_known: false, cost: 0, tools: 0, ms: 0, errors: [], refusal: false }
    let tmp, child, timer, killTimer, out = '', err = '', timedOut = false, finished = false
    const finish = spawnError => {
      if (finished) return
      finished = true; clearTimeout(timer); clearTimeout(killTimer)
      const errors = result.errors
      try {
        if (rawPath) fs.writeFileSync(rawPath, out || err)
        if (spawnError) errors.push(`runner error: ${spawnError.message}`)
        for (const line of out.split('\n')) {
          let e
          try { e = JSON.parse(line) } catch { continue }
          if (e.type === 'thread.started') result.sessionID = e.thread_id || null
          if (e.type === 'turn.completed') {
            const u = e.usage || {}, detail = u.output_tokens_details || {}
            result.tokens_known ||= Number.isInteger(u.input_tokens) && Number.isInteger(u.output_tokens)
            tokens.input += u.input_tokens || 0; tokens.output += u.output_tokens || 0
            tokens.reasoning += u.reasoning_output_tokens || u.reasoning_tokens || detail.reasoning_tokens || detail.thinking_tokens || 0
            tokens.cache_read += u.cached_input_tokens || 0
          }
          const item = e.item || {}
          if (e.type === 'item.completed' && ['command_execution', 'file_change', 'mcp_tool_call', 'web_search'].includes(item.type)) result.tools++
          if (e.type === 'refusal' || e.stop_reason === 'refusal' || e.refusal === true || item.type === 'refusal' || item.refusal === true) result.refusal = true
          if (e.type === 'error' || e.type === 'turn.failed' || item.type === 'error') {
            const error = e.error || item.message || e.message || e
            errors.push(`exit: ${typeof error === 'string' ? error : JSON.stringify(error)}`)
          }
        }
        if (tmp && fs.existsSync(path.join(tmp, 'last.txt'))) result.text = fs.readFileSync(path.join(tmp, 'last.txt'), 'utf8')
        Object.assign(result, parseReply(result.text))
        if (/usage[_ -]?limit|rate[_ -]?limit|quota[^\n]*(?:exceed|exhaust)|too many requests|\b429\b/i.test(errors.join(' ') + '\n' + err)) errors.unshift('runner error: usage limit')
        if (result.refusal) errors.push('refusal')
        if (timedOut) errors.unshift(`timeout after ${Math.round(limit / 60000)} min`)
        else if (child && child.exitCode !== 0 && !errors.length) errors.push(`exit ${child.exitCode}: ${err.trim().split('\n').slice(-3).join(' | ').slice(0, 400)}`)
      } catch (e) { errors.push(`runner error: ${e.message}`) }
      finally {
        if (tmp) fs.rmSync(tmp, { recursive: true, force: true })
        result.ms = Date.now() - t0
        resolve(result)
      }
    }
    try {
      tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'wf-codex-'))
      const [name, effort] = String(model).replace(/^codex\//, '').split('@')
      const sandbox = /(?:^|,)\s*(?:Write|Edit|Bash)(?:\([^)]*\))?\s*(?:,|$)/.test(tools || '') ? 'workspace-write' : 'read-only'
      // sessions persist so they can be monitored (Codex remote control); writers get network (ssh to the dev box)
      const args = ['exec', ...isolation(env), '--json', '--skip-git-repo-check',...(sandbox === 'workspace-write' ? ['-c', 'sandbox_workspace_write.network_access=true'] : []), '-C', cwd, '-s', sandbox, '-o', path.join(tmp, 'last.txt')]
      if (({ ...process.env, ...env }).CODEX_EPHEMERAL === '1') args.push('--ephemeral')
      if (name !== 'default') args.push('-m', name)
      if (effort) args.push('-c', `model_reasoning_effort=${effort}`)
      for (const d of addDirs || []) args.push('--add-dir', d)
      args.push('-')   // An explicit '-' reads the prompt from stdin.
      child = spawn('codex', args, { cwd, env: { ...process.env, ...env }, stdio: ['pipe', 'pipe', 'pipe'] })
      child.stdout.on('data', d => { out += d })
      child.stderr.on('data', d => { err += d; if (err.length > 20000) err = err.slice(-20000) })
      timer = setTimeout(() => { timedOut = true; child.kill('SIGTERM'); killTimer = setTimeout(() => child.kill('SIGKILL'), 5000) }, limit)
      child.on('error', finish)
      child.on('close', () => finish())
      child.stdin.on('error', () => {})
      // The CLI help has no system/developer instruction flag; the prompt carries the role instructions instead.
      child.stdin.end((chatName ? `[${chatName}]\n` : '') + (systemPrompt ? `Role instructions:\n${systemPrompt}\n\nTask:\n${prompt}` : prompt))
    } catch (e) { finish(e) }
  })
}

// App-server uses JSON lines without a jsonrpc field. Keep one overall deadline
// across startup and fallback so transport negotiation cannot extend a call.
async function run(options) {
  const started = Date.now(), limit = options.timeoutMs || 20 * 60000
  const name = options.name || options.label
  if (({ ...process.env, ...options.env }).CODEX_EPHEMERAL === '1') return runExec({ ...options, name, timeoutMs: limit })
  let result
  try {
    result = await runAppServer({ ...options, name, timeoutMs: limit })
  } catch (error) {
    const remaining = Math.max(1, limit - (Date.now() - started))
    result = await runExec({ ...options, name, timeoutMs: remaining })
    result.errors.push(`app-server fallback to codex exec: ${error.message}`)
  }
  result.ms = Date.now() - started
  return result
}

function runAppServer({ model, prompt, cwd, timeoutMs, rawPath, tools, systemPrompt, env, addDirs, name }) {
  return new Promise((resolve, reject) => {
    const tokens = { input: 0, output: 0, reasoning: 0, cache_read: 0, cache_write: 0 }
    const result = { text: '', json: null, jsonError: null, sessionID: null, tokens, tokens_known: false, cost: 0, tools: 0, ms: 0, errors: [], refusal: false }
    const [modelName, effort] = String(model).replace(/^codex\//, '').split('@')
    const writer = /(?:^|,)\s*(?:Write|Edit|Bash)(?:\([^)]*\))?\s*(?:,|$)/.test(tools || '')
    const messages = new Map(), completedItems = new Set(), pending = new Map()
    let child, timer, startupTimer, killTimer, buffer = '', out = '', err = '', nextId = 0
    let settled = false, closed = false, failure = null
    const finish = error => {
      if (settled) return
      settled = true; failure = error
      clearTimeout(timer); clearTimeout(startupTimer)
      for (const request of pending.values()) request.reject(error || new Error('app-server closed'))
      pending.clear()
      try {
        result.text = [...messages.values()].join('\n')
        Object.assign(result, parseReply(result.text))
        if (/usage[_ -]?limit|rate[_ -]?limit|quota[^\n]*(?:exceed|exhaust)|too many requests|\b429\b/i.test(result.errors.join(' ') + '\n' + err)) result.errors.unshift('runner error: usage limit')
        if (result.refusal) result.errors.push('refusal')
        if (rawPath) fs.writeFileSync(rawPath, out || err)
      } catch (e) { result.errors.push(`runner error: ${e.message}`) }
      // Closing stdin lets the server flush persistent thread state before exit.
      if (child && !closed) {
        child.stdin.end()
        child.kill('SIGTERM')
        killTimer = setTimeout(() => child.kill('SIGKILL'), 5000)
      } else deliver()
    }
    const deliver = () => {
      clearTimeout(killTimer)
      if (failure) reject(failure)
      else resolve(result)
    }
    const send = message => child.stdin.write(JSON.stringify(message) + '\n')
    const request = (method, params) => new Promise((resolve, reject) => {
      const id = ++nextId
      pending.set(id, { resolve, reject, method })
      send({ id, method, params })
    })
    const collect = item => {
      if (item.type === 'agentMessage') messages.set(item.id, item.text)
      if (!completedItems.has(item.id) && ['commandExecution', 'fileChange', 'mcpToolCall', 'webSearch'].includes(item.type)) result.tools++
      completedItems.add(item.id)
      if (item.type === 'refusal' || item.refusal === true) result.refusal = true
    }
    const receive = line => {
      if (!line.trim() || settled) return
      try {
        const event = JSON.parse(line)
        if (event.id != null) {
          const call = pending.get(event.id)
          if (!call || event.method) throw new Error(`unexpected app-server request/response: ${event.method || event.id}`)
          pending.delete(event.id)
          if (event.error) call.reject(new Error(`${call.method}: ${JSON.stringify(event.error)}`))
          else if ('result' in event) call.resolve(event.result)
          else throw new Error('app-server response missing result')
          return
        }
        const p = event.params || {}
        if (event.method === 'item/completed') collect(p.item)
        if (event.method === 'thread/tokenUsage/updated') {
          // Notifications contain cumulative totals, not increments.
          const u = p.tokenUsage.total
          result.tokens_known = Number.isInteger(u.inputTokens) && Number.isInteger(u.outputTokens)
          Object.assign(tokens, { input: u.inputTokens || 0, output: u.outputTokens || 0,
            reasoning: u.reasoningOutputTokens || 0, cache_read: u.cachedInputTokens || 0, cache_write: u.cacheWriteInputTokens || 0 })
        }
        if (event.method === 'error') {
          if (!p.willRetry) result.errors.push(`exit: ${JSON.stringify(p.error || p)}`)
        }
        if (event.method === 'turn/completed') {
          for (const item of p.turn.items || []) collect(item)
          if (p.turn.status !== 'completed') result.errors.push(`exit: ${JSON.stringify(p.turn.error || p.turn.status)}`)
          finish()
        }
      } catch (error) { finish(error) }
    }
    try {
      child = spawn('codex', ['app-server', ...isolation(env)], { cwd, env: { ...process.env, ...env }, stdio: ['pipe', 'pipe', 'pipe'] })
      child.stdout.setEncoding('utf8')
      child.stdout.on('data', data => {
        out += data; buffer += data
        let end
        while ((end = buffer.indexOf('\n')) >= 0) {
          const line = buffer.slice(0, end); buffer = buffer.slice(end + 1)
          receive(line)
        }
      })
      child.stderr.on('data', data => { err = (err + data).slice(-20000) })
      child.stdin.on('error', error => finish(error))
      child.on('error', error => { closed = true; finish(error) })
      child.on('close', code => {
        closed = true
        if (!settled && buffer) receive(buffer)
        if (!settled) finish(new Error(`app-server exited ${code}: ${err.trim().slice(-400)}`))
        else deliver()
      })
      timer = setTimeout(() => {
        result.errors.unshift(`timeout after ${Math.round(timeoutMs / 60000)} min`)
        finish()
      }, timeoutMs)
      startupTimer = setTimeout(() => finish(new Error('initialize timed out')), Math.min(5000, timeoutMs / 2))
      ;(async () => {
        await request('initialize', { clientInfo: { name: 'wf_codex_cli', title: 'Workflow Codex runner', version: '1.0.0' } })
        clearTimeout(startupTimer)
        send({ method: 'initialized' })
        const config = {}
        if (effort) config.model_reasoning_effort = effort
        if (writer) config['sandbox_workspace_write.network_access'] = true
        if (addDirs?.length) config['sandbox_workspace_write.writable_roots'] = addDirs.map(d => path.resolve(cwd, d))
        const started = await request('thread/start', { cwd, sandbox: writer ? 'workspace-write' : 'read-only',
          ephemeral: false, approvalPolicy: 'never', config,
          ...(modelName !== 'default' ? { model: modelName } : {}),
          ...(systemPrompt ? { developerInstructions: systemPrompt } : {}) })
        result.sessionID = started.thread.id
        if (!result.sessionID) throw new Error('thread/start missing thread id')
        if (name) await request('thread/name/set', { threadId: result.sessionID, name })
        await request('turn/start', { threadId: result.sessionID,
          input: [{ type: 'text', text: (name ? `[${name}]\n` : '') + prompt }],
          ...(effort ? { effort } : {}) })
      })().catch(error => finish(error))
    } catch (error) { finish(error) }
  })
}

module.exports = { run }
