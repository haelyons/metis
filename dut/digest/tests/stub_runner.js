'use strict'
// WF_STUB module for dry runs of dut/digest: no model is called. wf.js loads it in place of every model family
// (WF_STUB=<this file>); each call gets a canned reply from DIGEST_STUB_DIR, chosen by the call's label:
//   reader.json, verdict.json   the JSON reply
//   notebook.py                 the notebook source; __SECTIONS__ becomes the five DIGEST.md sections found in the
//                               notebook prompt, as a JSON object (a model copies them from the prompt the same way)
// A label with no file fails like a dead model (exit 1). DIGEST_STUB_LOG, if set, gets one JSON line per call.
const fs = require('node:fs'), path = require('node:path')
const DIR = process.env.DIGEST_STUB_DIR
const result = (json, errors = []) => ({ text: json ? JSON.stringify(json) : '', json, jsonError: null, sessionID: 'stub',
  tokens: { input: 0, output: 0, reasoning: 0, cache_read: 0, cache_write: 0 }, tokens_known: false, cost: 0, tools: 0, ms: 1, errors, refusal: false })

function sections(prompt) {
  const digest = (/=== DIGEST\.md\n([\s\S]*?)\n=== QA\.md\n/.exec(prompt) || [])[1] || ''
  return Object.fromEntries(digest.split(/^## /m).slice(1).map(block => {
    const [head, ...body] = block.split('\n')
    return [head.trim(), body.join('\n').trim()]
  }))
}

module.exports = {
  async run({ model, title, prompt, cwd, tools }) {
    if (process.env.DIGEST_STUB_LOG) fs.appendFileSync(process.env.DIGEST_STUB_LOG, JSON.stringify({ label: title, model, cwd, tools, prompt_bytes: Buffer.byteLength(prompt) }) + '\n')
    const file = name => path.join(DIR, name)
    if (title === 'notebook' && fs.existsSync(file('notebook.py')))
      return result({ source: fs.readFileSync(file('notebook.py'), 'utf8').replace('__SECTIONS__', JSON.stringify(sections(prompt), null, 1)) })
    if (fs.existsSync(file(`${title}.json`))) return result(JSON.parse(fs.readFileSync(file(`${title}.json`), 'utf8')))
    return result(null, [`exit 1: no stub reply for ${title} in ${DIR}`])
  },
  async exportSession(id, file) { fs.writeFileSync(file, '{}') },
}
