#!/usr/bin/env node
'use strict'
// Arms Hd and Ho: one bare model (no tools) gets the hackathon brief, with or without the domain, and proposes five
// projects. Three samples per arm. Every call is logged as in reframe/reframe.js.
// usage: node experiments/reshape-test/arm_h.js --out <run dir> [--model opencode-go/deepseek-v4-pro] [--n 3]
const fs = require('node:fs')
const path = require('node:path')
const oc = require('../../dut/pipeline/idea/oc.js')
const { validate, promptSuffix } = require('../../dut/pipeline/idea/schema.js')

const argv = process.argv.slice(2)
const opt = (k, d) => { const i = argv.indexOf(`--${k}`); return i >= 0 ? argv[i + 1] : d }
const OUT = path.resolve(opt('out')), MODEL = opt('model', 'opencode-go/deepseek-v4-pro'), N = Number(opt('n', 3))
const BRIEF = fs.readFileSync(path.join(__dirname, 'brief.md'), 'utf8').trim()
const DOMAIN = 'Bayesian calibration of rainfall-runoff models for river catchments, which needs long MCMC chains.'
const FIELDS = ['title', 'field', 'sequential_part', 'restructure', 'condition', 'baselines', 'first_test']
const SCHEMA = { type: 'object', required: ['proposals'], properties: { proposals: { type: 'array', items: { type: 'object',
  required: FIELDS, properties: Object.fromEntries(FIELDS.map(k => [k, { type: 'string' }])) } } } }
const ASK = where => `${BRIEF}\n\nPropose five projects for this hackathon${where}. For each give: title; field; sequential_part, ` +
  `the part of the work that one answer waits on step after step, or "none"; restructure, how your project changes that ` +
  `(or what it runs in parallel); condition, what must hold for it to pay off; baselines, what the result is timed and ` +
  `checked against; first_test, the cheapest measurement to run first and its rough cost. Decide from what you know; ` +
  `do not use tools.` + promptSuffix(SCHEMA)
const ARMS = { Hd: ASK(` in this domain: ${DOMAIN}`), Ho: ASK(', from any field of science') }

fs.mkdirSync(path.join(OUT, 'calls'), { recursive: true })
let spend = 0
async function call(name, prompt) {
  const base = path.join(OUT, 'calls', name)
  fs.writeFileSync(`${base}.prompt.md`, prompt)
  let session = null, res = null, errors = []
  for (let attempt = 1; attempt <= 2; attempt++) {
    res = await oc.run({ model: MODEL, agent: 'qt-bare', prompt: attempt === 1 ? prompt : `Your reply could not be used: ${errors.slice(0, 10).join('; ')}. Reply again with only the JSON asked for.`,
      cwd: path.join(OUT, 'calls'), session, timeoutMs: 15 * 60000, rawPath: `${base}.events.jsonl`, httpLogDir: `${base}.http`, title: name })
    session = res.sessionID; spend += res.cost
    errors = res.errors.length ? res.errors : res.json == null ? [res.jsonError || 'no JSON found in the reply'] : validate(SCHEMA, res.json)
    fs.appendFileSync(path.join(OUT, 'ledger.jsonl'), JSON.stringify({ ts: new Date().toISOString(), name, model: MODEL, attempt, tokens: res.tokens, cost_usd: res.cost, ms: res.ms, errors }) + '\n')
    if (!errors.length) break
  }
  await oc.exportSession(session, `${base}.export.json`)
  return errors.length ? null : res.json.proposals
}

;(async () => {
  const jobs = Object.keys(ARMS).flatMap(arm => Array.from({ length: N }, (_, i) => ({ arm, i: i + 1 })))
  const got = await Promise.all(jobs.map(j => call(`${j.arm}-${j.i}`, ARMS[j.arm])))
  const lists = jobs.map((j, k) => ({ case: j.arm === 'Hd' ? 'rr' : 'open', label: `${j.arm}-${j.i}`, reframes: got[k] || [] }))
  fs.writeFileSync(path.join(OUT, 'proposals.json'), JSON.stringify(lists, null, 1))
  console.log(`done: $${spend.toFixed(3)}; ${lists.filter(l => l.reframes.length).length} of ${lists.length} lists\n${OUT}/proposals.json`)
})()
