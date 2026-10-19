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
  if (/Find the existing research or industrial programmes/.test(p)) return { programmes: [{ name: 'Stub Lab', url: 'https://example.org', step: 'their screening step',
    step_url: 'https://example.org/step', step_quote: 'We screen candidates.', activity: { state: 'inactive', claim: 'archived in 2024', url: 'https://example.org/a', quote: 'This repository is archived.' },
    practice: [{ claim: 'they screen 100 candidates', url: 'https://example.org/p', quote: 'We screen 100 candidates.' }], if_lever_changes: 'more screening', if_not_changes: 'nothing',
    already_done: { status: 'no', claim: 'not done', url: 'https://example.org/d', quote: 'Not studied.' } }], gaps: ['stub gap'], no_programme_reason: '' }
  if (/^For each item below, fetch its source/.test(p)) return { items: [...p.matchAll(/^(p\d+:[a-z]+\d*): /gm)].map(m => ({ ref: m[1], status: m[1].endsWith(':done') ? 'CONTRADICTED' : 'SUPPORTED', page_quote: 'stub page sentence long enough', note: 'stub note text' })) }
  if (/^Score how well this research card fits/.test(p)) return { scores: ['fit', 'change', 'new'].map(c => ({ programme: 1, criterion: c, value: 5, reason: `stub ${c}` })) }
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
