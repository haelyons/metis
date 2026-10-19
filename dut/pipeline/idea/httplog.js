'use strict'
// Logging proxy for one OpenCode call. The call's provider baseURL points here; each request goes on to opencode.ai
// unchanged (an Anthropic-style call, which arrives on the OpenAI path, is sent to the Anthropic path) and is written
// to disk with its streamed reply: the exact system prompt, tool definitions and messages the model received.
const http = require('node:http')
const https = require('node:https')
const fs = require('node:fs')
const path = require('node:path')

const UPSTREAM = 'opencode.ai'
const SECRET = /^(authorization|x-api-key|x-opencode-org-id|cookie|set-cookie)$/i
const ORG = /org_[A-Z0-9]{20,}/g   // account workspace ids appear in error bodies
const redact = h => Object.fromEntries(Object.entries(h).map(([k, v]) => [k, SECRET.test(k) ? '[redacted]' : v]))

function start(dir) {
  fs.mkdirSync(dir, { recursive: true })
  let n = 0
  const server = http.createServer((req, res) => {
    const id = String(++n).padStart(3, '0')
    const chunks = []
    req.on('data', c => chunks.push(c))
    req.on('end', () => {
      const body = Buffer.concat(chunks)
      const p = req.url.replace(/\/openai\/v1\/messages/, '/anthropic/v1/messages')
      let parsed
      try { parsed = JSON.parse(body) } catch { parsed = body.toString() }
      fs.writeFileSync(path.join(dir, `${id}.request.json`), JSON.stringify({ ts: new Date().toISOString(), method: req.method, path: p, headers: redact(req.headers), body: parsed }, null, 1))
      const headers = { ...req.headers, host: UPSTREAM }
      delete headers['accept-encoding']   // plain-text replies, so the log is readable
      const out = fs.createWriteStream(path.join(dir, `${id}.response.txt`))
      const up = https.request({ host: UPSTREAM, method: req.method, path: p, headers }, r => {
        out.write(`HTTP ${r.statusCode}\n${JSON.stringify(redact(r.headers))}\n\n`)
        res.writeHead(r.statusCode, r.headers)
        r.on('data', c => { out.write(String(c).replace(ORG, 'org_[redacted]')); res.write(c) })
        r.on('end', () => { out.end(); res.end() })
      })
      up.on('error', e => { out.end(`proxy error: ${e.message}\n`); if (!res.headersSent) res.writeHead(502); res.end() })
      up.end(body)
    })
  })
  return new Promise(resolve => server.listen(0, '127.0.0.1', () =>
    resolve({ baseURL: `http://127.0.0.1:${server.address().port}/inference/go/openai/v1`, close: () => new Promise(r => server.close(r)) })))
}

module.exports = { start }
