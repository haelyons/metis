'use strict'
// vLLM can lose tool calls while streaming gpt-oss. Request complete JSON and emit OpenAI SSE chunks locally.
const http = require('node:http')
const https = require('node:https')

function start(baseURL) {
  const upstream = new URL(baseURL)
  const server = http.createServer((req, res) => {
    const chunks = []
    req.on('data', c => chunks.push(c))
    req.on('error', () => res.destroy())
    req.on('end', () => {
      let body = Buffer.concat(chunks), convert = false
      if (req.method === 'POST' && new URL(req.url, upstream).pathname.endsWith('/chat/completions')) {
        let parsed
        try { parsed = JSON.parse(body) } catch {}
        if (parsed?.stream === true) {
          convert = true
          parsed.stream = false
          delete parsed.stream_options   // vLLM rejects streaming options with stream:false
          body = Buffer.from(JSON.stringify(parsed))
        }
      }
      const headers = { ...req.headers, host: upstream.host }
      if (convert) {
        delete headers['accept-encoding']
        delete headers['transfer-encoding']
        headers['content-length'] = body.length
      }
      const fail = e => {
        if (res.destroyed || res.writableEnded) return
        if (res.headersSent) { res.destroy(); return }
        res.writeHead(502, { 'content-type': 'application/json' })
        res.end(JSON.stringify({ error: { message: e.message, type: 'proxy_error' } }))
      }
      const up = (upstream.protocol === 'https:' ? https : http).request(new URL(req.url, upstream), { method: req.method, headers }, r => {
        r.on('error', fail)
        if (!convert || r.statusCode < 200 || r.statusCode >= 300) {
          res.writeHead(r.statusCode, r.headers)
          r.pipe(res)
          return
        }
        const reply = []
        r.on('data', c => reply.push(c))
        r.on('end', () => {
          let result
          try {
            result = JSON.parse(Buffer.concat(reply))
            if (!Array.isArray(result.choices)) throw new Error('upstream response has no choices')
          } catch (e) { fail(e); return }
          res.writeHead(r.statusCode, { 'content-type': 'text/event-stream', 'cache-control': 'no-cache' })
          const { id, created, model, system_fingerprint } = result
          const emit = (choices, extra = {}) => res.write(`data: ${JSON.stringify({ id, object: 'chat.completion.chunk', created, model, system_fingerprint, choices, ...extra })}\n\n`)
          for (const choice of result.choices) {
            const { index, message } = choice
            const delta = { role: message.role || 'assistant' }
            if (message.content != null) delta.content = message.content
            emit([{ index, delta, finish_reason: null }])
            for (const [i, call] of (message.tool_calls || []).entries()) {
              emit([{ index, delta: { tool_calls: [{ index: i, id: call.id, type: call.type, function: call.function }] }, finish_reason: null }])
            }
          }
          emit(result.choices.map(c => ({ index: c.index, delta: {}, finish_reason: c.finish_reason })), result.usage ? { usage: result.usage } : {})
          res.end('data: [DONE]\n\n')
        })
      })
      up.on('error', fail)
      res.on('close', () => up.destroy())
      up.end(body)
    })
  })
  return new Promise((resolve, reject) => {
    server.once('error', reject)
    server.listen(0, '127.0.0.1', () => resolve({
      baseURL: `http://127.0.0.1:${server.address().port}${upstream.pathname.replace(/\/$/, '')}`,
      close: () => new Promise(r => { server.close(r); server.closeAllConnections() }),
    }))
  })
}

module.exports = { start }
