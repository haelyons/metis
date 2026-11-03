'use strict'
// Local HTTP contract checks for the de-streaming proxy. Run: node tools/test_destream.js.
const assert = require('node:assert/strict')
const http = require('node:http')
const { start } = require('../idea/destream.js')

async function main() {
  const requests = []
  const calls = [
    { id: 'call-1', type: 'function', function: { name: 'bash', arguments: '{"command":"echo héllo"}' } },
    { id: 'call-2', type: 'function', function: { name: 'read', arguments: '{"filePath":"/tmp/a.txt"}' } },
  ]
  let reply = {
    id: 'chatcmpl-test', object: 'chat.completion', created: 123, model: 'test', system_fingerprint: 'fp-test',
    choices: [{ index: 0, message: { role: 'assistant', content: 'héllo', tool_calls: calls }, finish_reason: 'tool_calls' }],
    usage: { prompt_tokens: 8, completion_tokens: 5, total_tokens: 13 },
  }
  let status = 200
  const upstream = http.createServer((req, res) => {
    const chunks = []
    req.on('data', c => chunks.push(c))
    req.on('end', () => {
      requests.push({ method: req.method, url: req.url, headers: req.headers, body: Buffer.concat(chunks).toString() })
      res.writeHead(status, { 'content-type': 'application/json', 'x-upstream': 'kept' })
      res.end(typeof reply === 'string' ? reply : JSON.stringify(reply))
    })
  })
  await new Promise(r => upstream.listen(0, '127.0.0.1', r))
  const proxy = await start(`http://127.0.0.1:${upstream.address().port}/v1`)
  const request = (body, route = '/chat/completions') => fetch(proxy.baseURL + route, {
    method: 'POST', headers: { 'content-type': 'application/json', authorization: 'Bearer local-test' }, body,
  })
  const parse = text => {
    const events = text.split('\n\n').filter(Boolean)
    assert.equal(events.pop(), 'data: [DONE]')
    return events.map(event => JSON.parse(event.slice('data: '.length)))
  }
  try {
    const input = { model: 'test', messages: [{ role: 'user', content: 'hello' }], stream: true,
      stream_options: { include_usage: true }, tools: [{ type: 'function', function: { name: 'bash' } }],
      temperature: 0.2, seed: 42, tools_md: 'Bash, Read' }
    let res = await request(JSON.stringify(input))
    assert.equal(res.status, 200)
    assert.equal(res.headers.get('content-type'), 'text/event-stream')
    const sent = requests.at(-1)
    const { stream_options, ...expected } = input
    assert.deepEqual(JSON.parse(sent.body), { ...expected, stream: false })
    assert.equal(sent.headers.authorization, 'Bearer local-test')
    assert.equal(Number(sent.headers['content-length']), Buffer.byteLength(sent.body))
    assert.equal(sent.url, '/v1/chat/completions')
    const events = parse(await res.text())
    assert.equal(events.length, 4)
    for (const event of events) {
      assert.equal(event.object, 'chat.completion.chunk')
      for (const field of ['id', 'created', 'model', 'system_fingerprint']) assert.equal(event[field], reply[field])
      assert.equal(event.choices[0].index, 0)
    }
    assert.deepEqual(events[0].choices[0].delta, { role: 'assistant', content: 'héllo' })
    for (let i = 0; i < calls.length; i++) {
      assert.deepEqual(events[i + 1].choices[0].delta.tool_calls, [{ index: i, ...calls[i] }])
      assert.equal(events[i + 1].choices[0].finish_reason, null)
    }
    assert.deepEqual(events.at(-1).usage, reply.usage)
    assert.deepEqual(events.at(-1).choices, [{ index: 0, delta: {}, finish_reason: 'tool_calls' }])
    console.log('ok stream conversion: fields, Unicode, parallel tool indexes, finish reason, usage, DONE')

    const raw = ' { "model": "test", "stream": false, "messages": [] }\n'
    res = await request(raw)
    assert.equal(await res.text(), JSON.stringify(reply))
    assert.equal(requests.at(-1).body, raw)
    assert.equal(res.headers.get('x-upstream'), 'kept')
    res = await fetch(proxy.baseURL + '/models?limit=2')
    assert.equal(await res.text(), JSON.stringify(reply))
    assert.equal(requests.at(-1).url, '/v1/models?limit=2')
    assert.equal(requests.at(-1).method, 'GET')
    res = await request(JSON.stringify(input), '/other')
    assert.equal(await res.text(), JSON.stringify(reply))
    assert.equal(requests.at(-1).body, JSON.stringify(input))
    console.log('ok passthrough: non-streaming bytes, models query, other POST paths, response headers')

    reply = { ...reply, choices: [{ index: 0, message: { role: 'assistant', content: null, tool_calls: [calls[0]] }, finish_reason: 'tool_calls' }] }
    delete reply.usage
    res = await request(JSON.stringify(input))
    let chunks = parse(await res.text())
    assert.deepEqual(chunks[0].choices[0].delta, { role: 'assistant' })
    assert.equal(chunks.at(-1).usage, undefined)
    reply.choices = [{ index: 0, message: { role: 'assistant', content: 'done' }, finish_reason: 'stop' }]
    res = await request(JSON.stringify(input))
    chunks = parse(await res.text())
    assert.equal(chunks.length, 2)
    assert.equal(chunks.at(-1).choices[0].finish_reason, 'stop')
    console.log('ok tool-only and text-only responses without usage')

    status = 429
    reply = '{"error":{"message":"busy"}}'
    res = await request(JSON.stringify(input))
    assert.equal(res.status, 429)
    assert.equal(await res.text(), reply)
    status = 200
    reply = 'invalid JSON'
    res = await request(JSON.stringify(input))
    assert.equal(res.status, 502)
    assert.equal((await res.json()).error.type, 'proxy_error')
    await new Promise(r => upstream.close(r))
    res = await request(JSON.stringify(input))
    assert.equal(res.status, 502)
    assert.equal((await res.json()).error.type, 'proxy_error')
    console.log('ok upstream errors: HTTP status/body, malformed JSON, connection refused')
  } finally {
    await proxy.close()
    await new Promise(r => upstream.close(r))
  }
}
main().catch(e => { console.error(e); process.exitCode = 1 })
