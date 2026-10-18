#!/usr/bin/env node
'use strict'
// reframe: a separate stage, outside the pipeline. For each case (a problem as first written down, with its root
// question) and each lens (a short brief in lenses/), one model proposes up to three reframings, each ending in a
// question someone could investigate. A judge on another model then classifies every question as reframe, copies or
// other, and checks it against the case's criterion when the case has one. Every call is logged as in the pipeline.
//
// usage: node reframe/reframe.js --cases <cases.json> --out <run dir> [--model m] [--judge m] [--lenses harry,independent]
//        node reframe/reframe.js --cases <cases.json> --judge-only <proposals.json> --out <run dir> [--judge m]
//          proposals.json: [{case, label, reframes: [...]}]; judges each list as given (planted tests, other judges' input)
const fs = require('node:fs')
const path = require('node:path')
const crypto = require('node:crypto')
const { execFileSync } = require('node:child_process')
const oc = require('../pipeline/idea/oc.js')
const { validate, promptSuffix } = require('../pipeline/idea/schema.js')

const argv = process.argv.slice(2)
const opt = (k, d) => { const i = argv.indexOf(`--${k}`); return i >= 0 ? argv[i + 1] : d }
const CASES = JSON.parse(fs.readFileSync(opt('cases'), 'utf8'))
const OUT = path.resolve(opt('out'))
const MODEL = opt('model', 'opencode-go/kimi-k3'), JUDGE = opt('judge', 'opencode-go/glm-5.3')
const LENSES = Object.fromEntries(opt('lenses', 'harry,independent').split(',').map(n => [n, fs.readFileSync(path.join(__dirname, 'lenses', `${n}.md`), 'utf8').trim()]))
fs.mkdirSync(path.join(OUT, 'calls'), { recursive: true })

const SCHEMA_REFRAMES = { type: 'object', required: ['reframes'], properties: { reframes: { type: 'array', items: { type: 'object',
  required: ['bottleneck', 'assumption', 'reframe', 'question', 'measure', 'compute_after', 'exact', 'expected', 'fails_if', 'closest_prior'],
  properties: Object.fromEntries(['bottleneck', 'assumption', 'reframe', 'question', 'measure', 'compute_after', 'exact', 'expected', 'fails_if', 'closest_prior'].map(k => [k, { type: 'string' }])) } } } }
const SCHEMA_JUDGE = { type: 'object', required: ['items'], properties: { items: { type: 'array', items: { type: 'object',
  required: ['index', 'kind', 'meets_criterion', 'quote', 'reason'],
  properties: { index: { type: 'integer' }, kind: { type: 'string', enum: ['reframe', 'copies', 'other'] }, meets_criterion: { type: 'string', enum: ['yes', 'no', 'NA'] }, quote: { type: 'string' }, reason: { type: 'string' } } } } } }

const P_REFRAME = (lens, c) => `${lens}\n\nHere is a research problem as it was first written down, with the question it belongs to.\n` +
  `Root question: ${c.root_question}\nProblem:\n${c.input}\n\n` +
  `Find where this problem stops more compute from helping, or where more compute only buys more of the same. Then look for reframings: changes to what is measured, the unit of work, the objective or the order of steps that would let more compute change the answer. Give up to three. ` +
  `End each with one question someone could investigate: specific, answerable by a measurement, and naming what is measured. For each, give the cheapest measurement that would answer it or show it is not worth pursuing, with a rough cost. ` +
  `Decide from the text above and what you know; do not use tools.` + promptSuffix(SCHEMA_REFRAMES)
const P_JUDGE = (c, proposals) => `Below are questions proposed for a research problem, each with the reframing behind it. Classify each one.\n` +
  `kind: "reframe" if it changes what is computed, measured or ordered so that more compute buys something it did not before; "copies" if it only runs the same computation more times, on more items, or side by side; "other" otherwise.\n` +
  `meets_criterion: "yes" or "no" for this criterion: ${c.criterion || 'none given; answer NA'}\n` +
  `Give for each a quote from the proposal and a reason of at most 25 words. Decide only from the text below; do not use tools.\n` +
  `Problem:\n${c.input}\nProposals: ${JSON.stringify(proposals.map((p, i) => ({ index: i + 1, ...p })))}` + promptSuffix(SCHEMA_JUDGE)

let spend = 0
async function call(name, model, prompt, schema) {
  const base = path.join(OUT, 'calls', name)
  fs.writeFileSync(`${base}.prompt.md`, prompt)
  let session = null, res = null, errors = []
  for (let attempt = 1; attempt <= 2; attempt++) {
    res = await oc.run({ model, agent: 'qt-bare', prompt: attempt === 1 ? prompt : `Your reply could not be used: ${errors.slice(0, 10).join('; ')}. Reply again with only the JSON asked for.`,
      cwd: path.join(OUT, 'calls'), session, timeoutMs: 15 * 60000, rawPath: `${base}.events.jsonl`, httpLogDir: `${base}.http`, title: name })
    session = res.sessionID; spend += res.cost
    errors = res.errors.length ? res.errors : res.json == null ? [res.jsonError || 'no JSON found in the reply'] : validate(schema, res.json)
    fs.appendFileSync(path.join(OUT, 'ledger.jsonl'), JSON.stringify({ ts: new Date().toISOString(), name, model, attempt, tokens: res.tokens, cost_usd: res.cost, ms: res.ms, errors }) + '\n')
    if (!errors.length) break
  }
  await oc.exportSession(session, `${base}.export.json`)
  return errors.length ? null : res.json
}

;(async () => {
  const sha = s => crypto.createHash('sha256').update(s).digest('hex').slice(0, 12)
  const commit = (() => { try { return execFileSync('git', ['-C', __dirname, 'rev-parse', '--short', 'HEAD'], { encoding: 'utf8' }).trim() } catch { return '?' } })()
  fs.writeFileSync(path.join(OUT, 'RUN.md'), [`# reframe run`, '', `Code: reframe/ at commit ${commit}. Reframer ${MODEL}; judge ${JUDGE}.`,
    `Lenses: ${Object.entries(LENSES).map(([n, t]) => `${n} (sha ${sha(t)})`).join(', ')}; copies in ./lenses.`, `Cases: ./cases.json.`, ''].join('\n'))
  fs.mkdirSync(path.join(OUT, 'lenses'), { recursive: true })
  for (const [n, t] of Object.entries(LENSES)) fs.writeFileSync(path.join(OUT, 'lenses', `${n}.md`), t + '\n')
  fs.writeFileSync(path.join(OUT, 'cases.json'), JSON.stringify(CASES, null, 1))

  const judgeOnly = opt('judge-only')
  if (judgeOnly) {
    const lists = JSON.parse(fs.readFileSync(judgeOnly, 'utf8'))
    const out = await Promise.all(lists.map(async x => {
      const c = CASES.find(k => k.id === x.case)
      const j = await call(`${x.case}-${x.label}-judge`, JUDGE, P_JUDGE(c, x.reframes), SCHEMA_JUDGE)
      return { case: x.case, label: x.label, judged: ((j && j.items) || []) }
    }))
    fs.writeFileSync(path.join(OUT, 'judged.json'), JSON.stringify({ judge: JUDGE, cost_usd: +spend.toFixed(4), lists: out }, null, 1))
    console.log(`judge-only done: $${spend.toFixed(3)}\n${OUT}/judged.json`)
    return
  }
  const jobs = CASES.flatMap(c => Object.keys(LENSES).map(l => ({ c, l })))
  const results = await Promise.all(jobs.map(async ({ c, l }) => {
    const r = await call(`${c.id}-${l}`, MODEL, P_REFRAME(LENSES[l], c), SCHEMA_REFRAMES)
    const props = (r && r.reframes) || []
    const j = props.length ? await call(`${c.id}-${l}-judge`, JUDGE, P_JUDGE(c, props), SCHEMA_JUDGE) : null
    return { case: c.id, lens: l, reframes: props.map((p, i) => ({ ...p, judge: ((j && j.items) || []).find(x => x.index === i + 1) || null })), ok: !!r, judged: !!j }
  }))
  fs.writeFileSync(path.join(OUT, 'results.json'), JSON.stringify({ model: MODEL, judge: JUDGE, cost_usd: +spend.toFixed(4), results }, null, 1))
  const L = [`# Reframe results`, '', `Reframer ${MODEL}, judge ${JUDGE}, cost $${spend.toFixed(3)}.`, '']
  for (const c of CASES) {
    L.push(`## ${c.id}`, '', `Criterion: ${c.criterion || 'none (classification only)'}`, '')
    for (const r of results.filter(x => x.case === c.id)) {
      L.push(`### lens: ${r.lens}${r.ok ? '' : ' (no valid reply)'}`, '')
      r.reframes.forEach((p, i) => {
        const j = p.judge || {}
        L.push(`${i + 1}. **${p.question}**`, `   - kind: ${j.kind || '?'} · criterion: ${j.meets_criterion || '?'} · ${j.reason || ''}`,
          `   - reframe: ${p.reframe}`, `   - measure: ${p.measure}`, `   - compute after: ${p.compute_after} · ${p.exact}`, `   - expected: ${p.expected} · fails if: ${p.fails_if}`, `   - closest prior: ${p.closest_prior}`, '')
      })
    }
  }
  fs.writeFileSync(path.join(OUT, 'results.md'), L.join('\n'))
  console.log(`done: $${spend.toFixed(3)}\n${OUT}/results.md`)
})().catch(e => { console.error(e); process.exit(1) })
