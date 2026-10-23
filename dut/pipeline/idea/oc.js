'use strict'
// One OpenCode call: `opencode run` under the isolated config in ./ocx (no MCP servers, deny-by-default permissions,
// agents qt-bare / qt-web / qt-research). Returns the final text, the parsed JSON, tokens and cost.
const { spawn } = require('node:child_process')
const fs = require('node:fs')
const path = require('node:path')

const OCX = path.join(__dirname, 'ocx')

// httpLogDir: route OpenCode Go traffic through a logging proxy for this call (httplog.js)
async function run(o) {
  if (!o.httpLogDir || !o.model.startsWith('opencode-go/')) return runOnce(o)
  // a spent usage limit (HTTP 429) stops the call at once instead of letting OpenCode retry until the timeout
  let stop = null
  const proxy = await require('./httplog.js').start(o.httpLogDir, msg => { if (stop) { stop(msg); stop = null } })
  const extra = JSON.stringify({ provider: { 'opencode-go': { options: { baseURL: proxy.baseURL } } } })
  try { return await runOnce({ ...o, env: { OPENCODE_CONFIG_CONTENT: extra }, onStop: f => { stop = f } }) } finally { await proxy.close() }
}

function runOnce({ model, agent, prompt, cwd, session, timeoutMs, rawPath, env, title, onStop }) {
  return new Promise(resolve => {
    const args = ['run', '--pure', '--format', 'json', '-m', model, '--agent', agent]
    if (session) args.push('--session', session)
    // a given title skips OpenCode's extra title-generation call (seen in the proxy logs)
    args.push('--title', title || 'qt')
    // argv strings stop at 128 KiB on Linux: a long prompt goes in an attached file
    if (Buffer.byteLength(prompt) > 100000) {
      const f = path.join(cwd, `.prompt-${process.pid}-${Date.now()}.md`)
      fs.writeFileSync(f, prompt)
      args.push('-f', f, 'Your whole task is in the attached file. Follow it exactly.')
    } else args.push(prompt)
    const t0 = Date.now()
    // OpenCode takes its project directory from --dir and PWD, not only the process cwd
    args.splice(1, 0, '--dir', cwd)
    const child = spawn('opencode', args, { cwd, env: { ...process.env, ...env, PWD: cwd, XDG_CONFIG_HOME: OCX }, stdio: ['ignore', 'pipe', 'pipe'] })
    const raw = rawPath ? fs.createWriteStream(rawPath, { flags: 'a' }) : null
    let buf = '', err = '', sessionID = session || null, steps = [], cur = [], tools = 0, errors = []
    const tokens = { input: 0, output: 0, reasoning: 0, cache_read: 0, cache_write: 0 }
    let cost = 0
    const onLine = line => {
      if (!line.trim()) return
      raw && raw.write(line + '\n')
      let o
      try { o = JSON.parse(line) } catch { return }
      sessionID = o.sessionID || sessionID
      const p = o.part || {}
      if (o.type === 'step_start') cur = []
      else if (o.type === 'text' && p.text) cur.push(p.text)
      else if (o.type === 'tool_use' || p.type === 'tool') tools++
      else if (o.type === 'step_finish') {
        if (cur.length) steps.push(cur.join(''))
        const t = p.tokens || {}
        tokens.input += t.input || 0; tokens.output += t.output || 0; tokens.reasoning += t.reasoning || 0
        tokens.cache_read += (t.cache || {}).read || 0; tokens.cache_write += (t.cache || {}).write || 0
        cost += p.cost || 0
      } else if (o.type === 'error') errors.push(JSON.stringify(o.error || o).slice(0, 500))
    }
    child.stdout.on('data', d => { buf += d; let i; while ((i = buf.indexOf('\n')) >= 0) { onLine(buf.slice(0, i)); buf = buf.slice(i + 1) } })
    child.stderr.on('data', d => { err += d; if (err.length > 20000) err = err.slice(-20000) })
    const timer = setTimeout(() => { errors.push(`timeout after ${Math.round(timeoutMs / 60000)} min`); child.kill('SIGTERM'); setTimeout(() => child.kill('SIGKILL'), 5000) }, timeoutMs)
    onStop && onStop(msg => { errors.unshift(msg); child.kill('SIGTERM'); setTimeout(() => child.kill('SIGKILL'), 5000) })
    child.on('close', code => {
      clearTimeout(timer)
      onLine(buf)
      if (cur.length) steps.push(cur.join(''))
      raw && raw.end()
      if (code && !errors.length) errors.push(`exit ${code}: ${err.trim().split('\n').slice(-3).join(' | ').slice(0, 400)}`)
      const text = steps.length ? steps[steps.length - 1] : ''
      // a reply that is meant to be one JSON value but does not parse reports the syntax error, never an inner fragment
      const whole = text.trim(), meant = /^[[{]/.test(whole) && /[\]}]$/.test(whole)
      let json = null, jsonError = null
      if (meant) { try { json = JSON.parse(whole) } catch (e) { jsonError = parseError(e, whole) } }
      else json = extractJSON(text)
      resolve({ text, json, jsonError, sessionID, tokens, cost, tools, ms: Date.now() - t0, errors })
    })
  })
}

// "the JSON does not parse: <message>; near: <the text around the error>", so a repair turn can fix the exact spot
function parseError(e, text) {
  const at = Number((String(e.message).match(/position (\d+)/) || [])[1])
  const near = Number.isFinite(at) ? ` near: ${JSON.stringify(text.slice(Math.max(0, at - 80), at + 40))}` : ''
  return `the JSON does not parse: ${e.message};${near}`
}

// The last fenced ```json block, else the last balanced {...} or [...] that parses.
function extractJSON(text) {
  if (!text) return null
  const fences = [...text.matchAll(/```(?:json)?\s*([\s\S]*?)```/g)].map(m => m[1])
  for (const f of fences.reverse()) { try { return JSON.parse(f) } catch {} }
  for (let end = text.length - 1; end >= 0; end--) {
    const c = text[end]
    if (c !== '}' && c !== ']') continue
    const open = c === '}' ? '{' : '['
    let depth = 0, inStr = false
    for (let i = end; i >= 0; i--) {
      const ch = text[i]
      if (ch === '"' && text[i - 1] !== '\\') inStr = !inStr
      if (inStr) continue
      if (ch === c) depth++
      else if (ch === open && --depth === 0) { try { return JSON.parse(text.slice(i, end + 1)) } catch { break } }
    }
  }
  return null
}

// Full session record (user prompt, every assistant message, reasoning, tool calls with input and output, tokens, cost).
function exportSession(sessionID, outPath) {
  return new Promise(resolve => {
    if (!sessionID) return resolve(false)
    const out = fs.createWriteStream(outPath)
    const child = spawn('opencode', ['export', sessionID], { env: { ...process.env, XDG_CONFIG_HOME: OCX }, stdio: ['ignore', 'pipe', 'ignore'] })
    child.stdout.pipe(out)
    child.on('close', code => resolve(code === 0))
  })
}

module.exports = { run, extractJSON, exportSession, OCX }
