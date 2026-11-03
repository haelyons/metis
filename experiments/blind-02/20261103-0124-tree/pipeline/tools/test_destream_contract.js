#!/usr/bin/env node
'use strict';

const assert = require('node:assert/strict');
const http = require('node:http');
const { once } = require('node:events');

const usage = { prompt_tokens: 17, completion_tokens: 9, total_tokens: 26 };
const content = 'Hello, world!\nUnicode survives: café 👋';
const toolCalls = [
  { id: 'call_weather', type: 'function', function: { name: 'weather', arguments: '{"city":"London","units":"°C"}' } },
  { id: 'call_search', type: 'function', function: { name: 'search', arguments: '{"query":"a\\nb","limit":2}' } },
];
const requestBody = {
  model: 'plain',
  messages: [{ role: 'user', content: 'Hello 👋' }],
  tools: [{ type: 'function', function: { name: 'weather', parameters: { type: 'object' } } }],
  temperature: 0.37,
  stream: true,
  stream_options: { include_usage: true },
  user: 'contract-test',
};
const passthroughBody = '{ "model": "passthrough", "stream": false, "messages": [], "temperature": 0 }';
const passthroughReply = '{ "id": "unchanged", "choices": [], "extra": true }\n';
const modelsReply = '{ "object": "list", "data": [{ "id": "fake-model" }] }\n';
const errorReply = JSON.stringify({ error: { message: 'Invalid test request', type: 'invalid_request_error' } });
const received = [];
let failures = 0;

function request(baseURL, path, method = 'GET', body) {
  return new Promise((resolve, reject) => {
    const outgoing = http.request(new URL(path, baseURL), {
      method,
      agent: false,
      headers: body === undefined ? {} : {
        'content-type': 'application/json',
        'content-length': Buffer.byteLength(body),
      },
    }, response => {
      const chunks = [];
      response.on('data', chunk => chunks.push(chunk));
      response.on('error', reject);
      response.on('end', () => resolve({
        status: response.statusCode,
        headers: response.headers,
        body: Buffer.concat(chunks).toString('utf8'),
      }));
    });
    outgoing.setTimeout(5000, () => outgoing.destroy(new Error('Request timed out')));
    outgoing.on('error', reject);
    outgoing.end(body);
  });
}

function parseSSE(response) {
  assert.equal(response.status, 200);
  assert.match(response.headers['content-type'] || '', /^text\/event-stream(?:\s*;|$)/i);
  const normalized = response.body.replace(/\r\n/g, '\n');
  assert.ok(normalized.endsWith('\n\n'), 'SSE events must end with a blank line');
  const events = normalized.split('\n\n').filter(block => block.trim()).flatMap(block => {
    const lines = block.split('\n');
    const data = lines.filter(line => line.startsWith('data:'))
      .map(line => line.slice(5).replace(/^ /, ''));
    return data.length ? [data.join('\n')] : [];
  });
  assert.ok(events.length >= 3, 'Expected message, final chunk, and DONE');
  assert.equal(events.at(-1), '[DONE]', 'DONE must be the last data event');
  assert.equal(events.filter(event => event === '[DONE]').length, 1);
  const chunks = events.slice(0, -1).map(event => JSON.parse(event));
  for (const chunk of chunks) {
    assert.ok(Array.isArray(chunk.choices), 'SSE chunk must have choices');
  }
  return chunks;
}

async function check(name, run) {
  try {
    await run();
    console.log(`ok - ${name}`);
  } catch (error) {
    failures++;
    console.error(`FAIL - ${name}: ${error.message}`);
  }
}

async function main() {
  const upstream = http.createServer(async (incoming, response) => {
    try {
      const parts = [];
      for await (const part of incoming) parts.push(part);
      const rawBody = Buffer.concat(parts).toString('utf8');
      const body = rawBody ? JSON.parse(rawBody) : undefined;
      received.push({ method: incoming.method, path: incoming.url, rawBody, body });
      response.setHeader('content-type', 'application/json');
      if (incoming.method === 'GET' && incoming.url === '/models') {
        response.writeHead(203);
        response.end(modelsReply);
      } else if (incoming.url !== '/chat/completions' || incoming.method !== 'POST') {
        response.writeHead(404);
        response.end('{}');
      } else if (body.model === 'passthrough') {
        response.writeHead(201);
        response.end(passthroughReply);
      } else if (body.model === 'error') {
        response.writeHead(400);
        response.end(errorReply);
      } else {
        const tools = body.model === 'tools';
        response.end(JSON.stringify({
          id: tools ? 'chatcmpl-tools' : 'chatcmpl-plain',
          object: 'chat.completion',
          created: 1700000000,
          model: body.model,
          choices: [{
            index: 0,
            message: tools ? { role: 'assistant', content: null, tool_calls: toolCalls }
              : { role: 'assistant', content },
            finish_reason: tools ? 'tool_calls' : 'stop',
          }],
          ...(tools ? {} : { usage }),
        }));
      }
    } catch (error) {
      response.writeHead(500);
      response.end(JSON.stringify({ error: error.message }));
    }
  });
  let proxy;
  let plainChunks;
  try {
    upstream.listen(0, '127.0.0.1');
    await once(upstream, 'listening');
    const { start } = require('../idea/destream.js');
    proxy = await start(`http://127.0.0.1:${upstream.address().port}`);
    assert.equal(typeof proxy.baseURL, 'string');
    assert.equal(typeof proxy.close, 'function');

    await check('1. Plain text streams with role, stop, and DONE last', async () => {
      plainChunks = parseSSE(await request(proxy.baseURL, '/chat/completions', 'POST', JSON.stringify(requestBody)));
      assert.equal(plainChunks[0].choices[0].delta.role, 'assistant');
      assert.equal(plainChunks.map(chunk => chunk.choices[0]?.delta?.content || '').join(''), content);
      assert.equal(plainChunks.at(-1).choices[0].finish_reason, 'stop');
    });

    await check('2. Two complete tool-call chunks preserve indexes, IDs, names, and arguments', async () => {
      const chunks = parseSSE(await request(proxy.baseURL, '/chat/completions', 'POST',
        JSON.stringify({ ...requestBody, model: 'tools' })));
      assert.equal(chunks[0].choices[0].delta.role, 'assistant');
      const toolChunks = chunks.filter(chunk => chunk.choices[0]?.delta?.tool_calls?.length);
      assert.equal(toolChunks.length, 2);
      toolChunks.forEach((chunk, index) => {
        assert.deepEqual(chunk.choices[0].delta.tool_calls, [{ index, ...toolCalls[index] }]);
      });
      assert.equal(chunks.at(-1).choices[0].finish_reason, 'tool_calls');
    });

    await check('3. Streaming requests change only stream and stream_options upstream', () => {
      assert.equal(received.length, 2);
      received.forEach((entry, index) => {
        assert.equal(entry.method, 'POST');
        assert.equal(entry.path, '/chat/completions');
        const expected = { ...requestBody, model: index === 0 ? 'plain' : 'tools', stream: false };
        delete expected.stream_options;
        assert.deepEqual(entry.body, expected);
        assert.equal(Object.hasOwn(entry.body, 'stream_options'), false);
      });
    });

    await check('4. Non-streaming POST and GET /models preserve requests, responses, and statuses', async () => {
      const before = received.length;
      const post = await request(proxy.baseURL, '/chat/completions', 'POST', passthroughBody);
      assert.equal(post.status, 201);
      assert.equal(post.body, passthroughReply);
      assert.deepEqual(received[before], {
        method: 'POST', path: '/chat/completions', rawBody: passthroughBody, body: JSON.parse(passthroughBody),
      });
      const models = await request(proxy.baseURL, '/models');
      assert.equal(models.status, 203);
      assert.equal(models.body, modelsReply);
      assert.deepEqual(received[before + 1], {
        method: 'GET', path: '/models', rawBody: '', body: undefined,
      });
    });

    await check('5. Upstream 400 reaches the streaming client as 400', async () => {
      const response = await request(proxy.baseURL, '/chat/completions', 'POST',
        JSON.stringify({ ...requestBody, model: 'error' }));
      assert.equal(response.status, 400);
    });

    await check('6. Usage is forwarded on the final chunk', () => {
      assert.ok(plainChunks, 'Plain response must parse successfully');
      assert.deepEqual(plainChunks.at(-1).usage, usage);
    });
  } finally {
    try {
      if (proxy) await proxy.close();
    } finally {
      if (upstream.listening) {
        upstream.closeAllConnections();
        await new Promise((resolve, reject) => upstream.close(error => error ? reject(error) : resolve()));
      }
    }
  }
}

const watchdog = setTimeout(() => {
  console.error('FAIL - Test process timed out');
  console.error(`${failures + 1} failure(s)`);
  process.exit(1);
}, 20000);

main().catch(error => {
  failures++;
  console.error(`FAIL - Setup or cleanup: ${error.message}`);
}).finally(() => {
  clearTimeout(watchdog);
  console.log(failures ? `${failures} failure(s)` : 'all checks passed');
  process.exitCode = failures ? 1 : 0;
});
