'use strict'
// One Claude call through the headless CLI (`claude -p`), shaped like oc.run so wf.js can serve an agent() call from
// either family. The prompt goes in on stdin (no argv limit); the role's prompt from ocx/opencode.json becomes an
// appended system prompt and the role's tool list limits the built-in tools; --restricted and --strict-mcp-config keep the
// user's hooks, plugins and MCP servers out of the call, so nothing outside the prompt reaches the model. No session persistence: a repair turn is a fresh call whose prompt
// carries the earlier errors. Returns { text, json, jsonError, sessionID, tokens, cost, tools, ms, errors, refusal }.
const { spawn } = require('node:child_process')
const fs = require('node:fs')
const { extractJSON } = require('./oc.js')
const { claudeModel } = require('./understudy.js')

function run({ model, prompt, cwd, timeoutMs, rawPath, tools, systemPrompt, env, addDirs, name: chatName }) {
  return new Promise(resolve => {
    const name = claudeModel(model)
    // --restricted: no user hooks, plugins or settings reach the call (the caveman hook did), file tools confined to the
    // working directories; --strict-mcp-config: no MCP servers (the full tool list cost ~170k prompt tokens per call);
    // --bare would do both but drops the login. Named tools are re-enabled under --restricted and pre-approved.
    const args = ['-p', '--model', name, '--output-format', 'json', '--no-session-persistence', '--restricted', '--strict-mcp-config', '--permission-mode', 'dontAsk', '--tools', tools == null ? '' : tools]
    if (chatName) args.push('--name', chatName)
    if (tools) args.push('--allowedTools', tools)
    for (const d of addDirs || []) args.push('--add-dir', d)
    if (systemPrompt) args.push('--append-system-prompt', systemPrompt)
    const t0 = Date.now()
    let child
    try {
      child = spawn('claude', args, { cwd, env: { ...process.env, ...env, CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS: '0' }, stdio: ['pipe', 'pipe', 'pipe'] })
    } catch (e) { return resolve(fail(`runner error: ${e.message}`, t0)) }
    let out = '', err = '', timedOut = false
    child.stdout.on('data', d => { out += d })
    child.stderr.on('data', d => { err += d; if (err.length > 20000) err = err.slice(-20000) })
    const timer = setTimeout(() => { timedOut = true; child.kill('SIGTERM'); setTimeout(() => child.kill('SIGKILL'), 5000) }, timeoutMs || 20 * 60000)
    child.on('error', e => { clearTimeout(timer); resolve(fail(`runner error: ${e.message}`, t0)) })
    child.on('close', code => {
      clearTimeout(timer)
      if (rawPath) fs.writeFileSync(rawPath, out || err)
      const errors = []
      let d = null
      try { d = JSON.parse(out) } catch { /* not JSON: an error or a kill */ }
      if (timedOut) errors.push(`timeout after ${Math.round((timeoutMs || 0) / 60000)} min`)
      else if (!d) errors.push(`exit ${code}: ${(err.trim() || out.trim()).split('\n').slice(-3).join(' | ').slice(0, 400)}`)
      const text = d ? String(d.result == null ? '' : d.result) : ''
      const refusal = !!(d && (d.stop_reason === 'refusal' || /refusal/i.test(String(d.subtype || ''))))
      if (refusal) errors.push('refusal')
      else if (d && d.is_error && d.subtype !== 'success') errors.push(`exit: ${d.subtype}: ${text.slice(0, 300)}`)
      const u = (d && d.usage) || {}
      const tokens = { input: u.input_tokens || 0, output: u.output_tokens || 0, reasoning: ((u.output_tokens_details || {}).thinking_tokens) || 0, cache_read: u.cache_read_input_tokens || 0, cache_write: u.cache_creation_input_tokens || 0 }
      const { json, jsonError } = parseReply(text)
      resolve({ text, json, jsonError, sessionID: d && d.session_id || null, tokens, tokens_known: Number.isInteger(u.input_tokens) && Number.isInteger(u.output_tokens), cost: (d && d.total_cost_usd) || 0, tools: Math.max(0, ((d && d.num_turns) || 1) - 1), ms: Date.now() - t0, errors, refusal, turns: d && d.num_turns })
    })
    child.stdin.on('error', () => {})
    child.stdin.end(prompt)
  })
  function fail(msg, t0) { return { text: '', json: null, jsonError: null, sessionID: null, tokens: { input: 0, output: 0, reasoning: 0, cache_read: 0, cache_write: 0 }, tokens_known: false, cost: 0, tools: 0, ms: Date.now() - t0, errors: [msg], refusal: false } }
}

function parseReply(text) {
  const whole = text.trim(), meant = /^[[{]/.test(whole) && /[\]}]$/.test(whole)
  let json = null, jsonError = null
  if (meant) { try { json = JSON.parse(whole) } catch (e) { jsonError = `the JSON does not parse: ${e.message}` } }
  else json = extractJSON(text)
  return { json, jsonError }
}

module.exports = { run, parseReply }
