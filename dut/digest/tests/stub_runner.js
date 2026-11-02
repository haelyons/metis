'use strict'
// WF_STUB module for dry runs of dut/digest: no model is called. wf.js loads it in place of every model family
// (WF_STUB=<this file>); each call gets a canned reply from DIGEST_STUB_DIR, chosen by the call's label:
//   reader.json, writer.json  the JSON reply
//   verify.json               {overrides: [{match, verdict, quote, path, reason}], drop: [id], enums}; every sentence the prompt
//                             lists is supported, quoting a verbatim line of a file it cites that holds one of its
//                             numbers, unless an override's match is in the sentence
//   notebook.py               the notebook source; __SECTIONS__ becomes the five DIGEST.md sections found in the
//                             notebook prompt, as a JSON object (a model copies them from the prompt the same way)
//   notebook-repair           the source from the repair prompt without its "planted export failure" lines
//                             (unchanged if the stub dir holds a file named repair_fails)
// A label with no reply fails like a dead model (exit 1). DIGEST_STUB_LOG, if set, gets one JSON line per call.
const fs = require('node:fs'), path = require('node:path')
const DIR = process.env.DIGEST_STUB_DIR
const file = name => path.join(DIR, name)
const result = (json, errors = []) => ({ text: json ? JSON.stringify(json) : '', json, jsonError: null, sessionID: 'stub',
  tokens: { input: 0, output: 0, reasoning: 0, cache_read: 0, cache_write: 0 }, tokens_known: false, cost: 0, tools: 0, ms: 1, errors, refusal: false })
const between = (text, a, b) => { const i = text.indexOf(a); return i < 0 ? '' : text.slice(i + a.length, text.indexOf(b, i + a.length)) }

function sections(prompt) {
  return Object.fromEntries(between(prompt, '=== DIGEST.md\n', '\n=== QA.md\n').split(/^## /m).slice(1).map(block => {
    const [head, ...body] = block.split('\n')
    return [head.trim(), body.join('\n').trim()]
  }))
}

function verify(prompt, cfg) {
  const files = {}
  between(prompt, '## The files the reader cited', '\n=== end of the cited files\n').split(/^=== (.+) \(\d+ bytes\)$/m).slice(1)
    .forEach((x, i, a) => { if (i % 2 === 0) files[x] = a[i + 1] })
  const sentences = {}
  let question = null
  for (const line of between(prompt, "## The reader's answers", "## The reader's draft enums").split('\n')) {
    const q = /^### (Q\d+)\./.exec(line), s = /^(S\d+)\. (.*)$/.exec(line)
    if (q) question = q[1]
    if (!s) continue
    const cited = [...s[2].matchAll(/\(([^()\s]+)\)/g)].map(m => m[1]).filter(p => p in files)
    const nums = (s[2].replace(/\([^()\s]+\)/g, ' ').match(/\d+(?:\.\d+)?/g) || [])
    const o = (cfg.overrides || []).find(x => s[2].includes(x.match))
    let hit = null
    for (const p of cited) for (const l of files[p].split('\n')) if (!hit && l.trim() && nums.some(n => l.includes(n))) hit = { path: p, quote: l.trim().slice(0, 200) }
    hit = hit || { path: cited[0], quote: files[cited[0]].split('\n').find(l => l.trim()).trim().slice(0, 200) }
    sentences[s[1]] = o ? { question, sentence: s[2], verdict: o.verdict, quote: o.quote, path: o.path, reason: o.reason }
      : { question, sentence: s[2], verdict: 'supported', quote: hit.quote, path: hit.path, reason: 'stub: a line of the cited file holds the number' }
  }
  for (const id of cfg.drop || []) delete sentences[id]   // a reply that skips sentences, for the schema test
  return { sentences, enums: cfg.enums }
}

module.exports = {
  async run({ model, title, prompt, cwd, tools }) {
    if (process.env.DIGEST_STUB_LOG) fs.appendFileSync(process.env.DIGEST_STUB_LOG, JSON.stringify({ label: title, model, cwd, tools, prompt_bytes: Buffer.byteLength(prompt) }) + '\n')
    const json = name => JSON.parse(fs.readFileSync(file(name), 'utf8'))
    if (title === 'verify' && fs.existsSync(file('verify.json'))) return result(verify(prompt, json('verify.json')))
    if (title === 'notebook' && fs.existsSync(file('notebook.py')))
      return result({ source: fs.readFileSync(file('notebook.py'), 'utf8').replace('__SECTIONS__', JSON.stringify(sections(prompt), null, 1)) })
    if (title === 'notebook-repair') {
      const src = between(prompt, '=== digest.py\n', '\n=== end of digest.py')
      return result({ source: fs.existsSync(file('repair_fails')) ? src : src.split('\n').filter(l => !l.includes('planted export failure')).join('\n') })
    }
    if (fs.existsSync(file(`${title}.json`))) return result(json(`${title}.json`))
    return result(null, [`exit 1: no stub reply for ${title} in ${DIR}`])
  },
  async exportSession(id, f) { fs.writeFileSync(f, '{}') },
}
