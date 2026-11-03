'use strict'
// One ephemeral Cursor Agent CLI call (`cursor-agent -p`), shaped like codex_cli.run.
const { spawn } = require('node:child_process')
const fs = require('node:fs')
const { parseReply } = require('./claude_cli.js')

function run({ model, prompt, cwd, timeoutMs, rawPath, tools, systemPrompt, env, addDirs, name: chatName }) {
  return new Promise(resolve => {
    const t0 = Date.now(), limit = timeoutMs || 20 * 60000
    const tokens = { input: 0, output: 0, reasoning: 0, cache_read: 0, cache_write: 0 }
    const result = { text: '', json: null, jsonError: null, sessionID: null, tokens, tokens_known: false, cost: 0, tools: 0, ms: 0, errors: [], refusal: false }
    let child, timer, killTimer, out = '', err = '', timedOut = false, finished = false
    const finish = spawnError => {
      if (finished) return
      finished = true; clearTimeout(timer); clearTimeout(killTimer)
      const errors = result.errors
      try {
        if (rawPath) fs.writeFileSync(rawPath, out || err)
        if (spawnError) errors.push(`runner error: ${spawnError.message}`)
        let d = null
        try { d = JSON.parse(out) } catch { /* not JSON: an error or a kill */ }
        if (d) {
          result.text = String(d.result == null ? '' : d.result)
          result.sessionID = d.session_id || null
          const u = d.usage || {}
          const input = u.inputTokens ?? u.input_tokens
          const output = u.outputTokens ?? u.output_tokens
          result.tokens_known = Number.isInteger(input) && Number.isInteger(output)
          tokens.input = input || 0
          tokens.output = output || 0
          tokens.reasoning = u.reasoningTokens || u.reasoning_tokens || ((u.output_tokens_details || {}).thinking_tokens) || 0
          tokens.cache_read = u.cacheReadTokens || u.cache_read_input_tokens || u.cached_input_tokens || 0
          tokens.cache_write = u.cacheWriteTokens || u.cache_creation_input_tokens || 0
          result.cost = d.total_cost_usd || 0
          result.tools = Math.max(0, (d.num_turns || 1) - 1)
          result.refusal = !!(d.stop_reason === 'refusal' || d.refusal === true || /refusal/i.test(String(d.subtype || '')))
          if (d.is_error && d.subtype !== 'success') errors.push(`exit: ${d.subtype}: ${result.text.slice(0, 300)}`)
        }
        Object.assign(result, parseReply(result.text))
        if (/usage[_ -]?limit|rate[_ -]?limit|quota[^\n]*(?:exceed|exhaust)|too many requests|\b429\b/i.test(errors.join(' ') + '\n' + err + '\n' + out)) errors.unshift('runner error: usage limit')
        if (result.refusal) errors.push('refusal')
        if (timedOut) errors.unshift(`timeout after ${Math.round(limit / 60000)} min`)
        else if (child && child.exitCode !== 0 && !errors.length) errors.push(`exit ${child.exitCode}: ${err.trim().split('\n').slice(-3).join(' | ').slice(0, 400) || out.trim().slice(0, 400)}`)
      } catch (e) { errors.push(`runner error: ${e.message}`) }
      finally {
        result.ms = Date.now() - t0
        resolve(result)
      }
    }
    try {
      const name = String(model).replace(/^cursor\//, '')
      const writing = /(?:^|,)\s*(?:Write|Edit|Bash)(?:\([^)]*\))?\s*(?:,|$)/.test(tools || '')
      const args = ['-p', '--output-format', 'json', '--trust', '--workspace', cwd]
      if (name !== 'default') args.push('--model', name)
      if (writing) args.push('--force')
      for (const d of addDirs || []) args.push('--add-dir', d)
      child = spawn('cursor-agent', args, { cwd, env: { ...process.env, ...env }, stdio: ['pipe', 'pipe', 'pipe'] })
      child.stdout.on('data', d => { out += d })
      child.stderr.on('data', d => { err += d; if (err.length > 20000) err = err.slice(-20000) })
      timer = setTimeout(() => { timedOut = true; child.kill('SIGTERM'); killTimer = setTimeout(() => child.kill('SIGKILL'), 5000) }, limit)
      child.on('error', finish)
      child.on('close', () => finish())
      child.stdin.on('error', () => {})
      const body = (systemPrompt ? `Role instructions:\n${systemPrompt}\n\nTask:\n${prompt}` : prompt)
        + (writing ? '' : '\n\nDo not modify any files.')
      child.stdin.end((chatName ? `[${chatName}]\n` : '') + body)
    } catch (e) { finish(e) }
  })
}

module.exports = { run }
