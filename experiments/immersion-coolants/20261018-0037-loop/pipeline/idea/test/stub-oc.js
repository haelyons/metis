'use strict'
// Smoke test with no model calls: preload with NODE_OPTIONS="--require <this file>". Every require of idea/oc.js
// (also in the wf.js and frame.js processes the loop starts) gets canned replies for the framer, widener, option
// critic and neighbour prompts; every other call fails at once, like a blocked provider.
const Module = require('node:module')
const resolve = Module._resolveFilename
Module._resolveFilename = function (req, parent, ...rest) {
  const r = resolve.call(this, req, parent, ...rest)
  return /[\\/]idea[\\/]oc\.js$/.test(r) ? __filename : r
}
const opt = id => ({ id, title: `option ${id}`, summary: `summary of ${id}`, root_link: 'bears on the root', compute_open: 'samples; largest reported 10', sequential: 'none', source_urls: [] })
function reply(p) {
  if (/VERDICT: COMPUTE-BOUND or VERDICT: NOT COMPUTE-BOUND/.test(p)) return { verdict: 'NOT COMPUTE-BOUND', compute_signals: [] }
  if (/What sorts of related problems are compute constrained/.test(p)) return { items: ['W1', 'W2', 'W3'].map(opt) }
  if (/^Score each option 1-5/.test(p)) {
    const ids = [...p.matchAll(/^\{"id":"([^"]+)"/gm)].map(m => m[1])
    return { items: ids.map(id => ({ id, distance: id === 'W2' ? 'SAME' : 'ADJACENT', distance_reason: `stub label reason for ${id}`,
      scores: ['stakes', 'open', 'reshape'].map(c => ({ criterion: c, value: ['W1', 'V1'].includes(id) ? 5 : id === 'W2' ? 3 : 2, reason: `stub reason on ${c} for ${id}` })) })) }
  }
  if (/Propose three close variants/.test(p)) return { variants: ['V1', 'V2', 'V3'].map(id => ({ id, title: `variant ${id}`, text: 't', root_link: 'r', compute_open: 'c', sequential: 's', changes: `changes ${id}` })) }
  return null
}
const zero = { input: 0, output: 0, reasoning: 0, cache_read: 0, cache_write: 0 }
module.exports = {
  run: async o => { const j = reply(o.prompt); return { text: j ? JSON.stringify(j) : '', json: j, sessionID: null, tokens: zero, cost: 0, tools: 0, ms: 1, errors: j ? [] : ['stub: no reply'] } },
  exportSession: async () => false,
  extractJSON: () => null,
  OCX: require('node:path').join(__dirname, '..', 'ocx'),
}
