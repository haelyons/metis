'use strict'
// One ephemeral Codex CLI call, shaped like claude_cli.run. JSONL carries usage/errors; -o carries the final reply.
const { spawn } = require('node:child_process')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const { parseReply } = require('./claude_cli.js')

function run({ model, prompt, cwd, timeoutMs, rawPath, tools, systemPrompt, env, addDirs }) {
  return new Promise(resolve => {
    const t0 = Date.now(), limit = timeoutMs || 20 * 60000
    const tokens = { input: 0, output: 0, reasoning: 0, cache_read: 0, cache_write: 0 }
    const result = { text: '', json: null, jsonError: null, sessionID: null, tokens, cost: 0, tools: 0, ms: 0, errors: [], refusal: false }
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
      const args = ['exec', '--json', '--skip-git-repo-check', '--ephemeral', '-C', cwd, '-s', sandbox, '-o', path.join(tmp, 'last.txt')]
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
      child.stdin.end(systemPrompt ? `Role instructions:\n${systemPrompt}\n\nTask:\n${prompt}` : prompt)
    } catch (e) { finish(e) }
  })
}

module.exports = { run }
