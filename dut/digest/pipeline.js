export const meta = { name: 'digest', description: 'One finished run into <run>/digest/: four model calls, everything else deterministic' }
// wf.js script; the spec is README.txt beside this file. args: { run_root, out?, force?, max_evidence_mb?, file_bytes? }
// Questions produce the working (reader), verification checks the working (verify), trimming produces the write-up
// (writer); a notebook call (with one repair) shows the evidence. The models only return JSON; this script resolves
// and copies the evidence and writes every file.
const { default: path } = await import('node:path')
const fs = await import('node:fs')
const { createHash } = await import('node:crypto')
const { spawnSync } = await import('node:child_process')

const t0 = Date.now()
const A = (typeof args === 'string' ? JSON.parse(args) : args) || {}
if (!A.run_root) return { error: 'digest needs args.run_root' }
const WF = path.dirname(agent.journal)
const wfRun = JSON.parse(fs.readFileSync(path.join(WF, 'run.json'), 'utf8'))
const HOME = path.dirname(wfRun.script), CHECK = path.join(HOME, 'check.py')
const ROOT = fs.realpathSync(path.resolve(A.run_root))
const OUT = path.resolve(A.out || path.join(ROOT, 'digest'))
const MAX = (A.max_evidence_mb || 20) * 1e6, FILE_BYTES = A.file_bytes || 200000
if (!fs.existsSync(path.join(OUT, 'wf')) || fs.realpathSync(path.join(OUT, 'wf')) !== WF) return { error: `run wf.js with --out ${path.join(OUT, 'wf')}` }
// wf.js takes a Workflow model name and maps it to a tier (understudy.js TIER): opus -> strong, sonnet -> main
const STRONG = 'opus', MAIN = 'sonnet'
const ENUMS = {   // keep in step with check.py
  headline_kind: ['speedup', 'negative', 'void', 'partial', 'unknown'],
  baseline_kind: ['stock', 'tuned', 'one_thread', 'cpu_library', 'other', 'unknown'],
  equivalence: ['bit_identical', 'within_tolerance', 'not_checked', 'failed', 'unknown'],
  prediction_hit: ['yes', 'partly', 'no', 'not_sealed', 'unknown'],
  evidence: ['measured', 'inferred', 'unknown'],
  anchor: ['measured', 'page_value_only', 'not_run', 'none', 'unknown'],
}
const VERDICTS = ['supported', 'contradicted', 'not_addressed']
const SECTIONS = [['question', 'Question'], ['answer', 'Answer'], ['constraints', 'Problem and constraints'], ['method', 'Method and assumptions'], ['analysis', 'Analysis']]
const read = f => fs.readFileSync(f, 'utf8')
const write = (name, text) => fs.writeFileSync(path.join(OUT, name), text)
const sha256 = buf => createHash('sha256').update(buf).digest('hex')
const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
const inRepo = p => wfRun.git && !path.relative(wfRun.git.repo, p).startsWith('..') ? path.relative(wfRun.git.repo, p) : p
const rows = () => read(agent.journal).split('\n').filter(Boolean).map(l => JSON.parse(l))
const modelOf = label => (rows().filter(r => r.type === 'result' && r.label === label).pop() || {}).model || null
// paragraphs joined into lines, split into sentences the way check.py and gate_scope.py split them
const sentencesOf = text => String(text).split(/\n\s*\n/).map(p => p.split('\n').map(l => l.trim()).filter(Boolean).join(' '))
  .filter(Boolean).flatMap(p => p.split(/(?<=[.!?])\s+/)).filter(s => s.trim())

// ---------- refuse an existing digest; this run's wf/ is already there ----------
const old = fs.readdirSync(OUT).filter(n => n !== 'wf')
const oldWf = ['journal.jsonl', 'result.json', 'RESULT.md', 'UNDERSTUDY.md', 'shadow.jsonl'].filter(n => fs.existsSync(path.join(WF, n)))
  .concat(fs.readdirSync(path.join(WF, 'agents')).length ? ['agents'] : [])
if (old.length + oldWf.length && !A.force) return { error: `${OUT} already holds a digest (${[...old, ...oldWf.map(n => `wf/${n}`)].join(', ')}); set force: true in args to replace it` }
for (const n of old) fs.rmSync(path.join(OUT, n), { recursive: true, force: true })
if (oldWf.length) { const prev = path.join(WF, `prev-${new Date().toISOString().replace(/[-:]|\..*/g, '')}`); fs.mkdirSync(prev); for (const n of oldWf) fs.renameSync(path.join(WF, n), path.join(prev, n)) }

// ---------- schemas (schema.js subset); keyed objects make the validator demand one entry per question or sentence ----------
const standing = read(path.join(HOME, 'questions.md')).split('\n').map(l => /^(Q\d+)\.\s+(.+)$/.exec(l)).filter(Boolean).map(m => [m[1], m[2].trim()])
const S = { type: 'string' }, list = { type: 'array', items: S }
const obj = props => ({ type: 'object', additionalProperties: false, required: Object.keys(props), properties: props })
const keyed = (keys, item) => obj(Object.fromEntries(keys.map(k => [k, item])))
const enumSchema = obj(Object.fromEntries(Object.entries(ENUMS).map(([k, v]) => [k, { enum: v }])))
const readerSchema = obj({ answers: keyed(standing.map(q => q[0]), obj({ answer: S, citations: list })),
  citations: { type: 'array', items: obj({ path: S, supports: S }) }, enums: enumSchema })
const fill = (name, vars) => {
  const text = read(path.join(HOME, 'prompts', `${name}.md`)).replace(/\{\{(\w+)\}\}/g, (m, k) => (k in vars ? String(vars[k]) : m))
  if (/\{\{\w+\}\}/.test(text)) throw new Error(`prompt ${name}: unfilled placeholder`)
  return text
}

// ---------- RUN.md on every exit path ----------
const runMd = (state, extra = []) => {
  const st = JSON.parse(read(path.join(WF, 'status.json')))
  const calls = (st.calls || []).map(c => `  ${c.id}: primary ${c.model}, answered by ${c.by || 'none'}${c.substituted ? ' (understudy)' : ''}, understudies ${(c.chain || []).join(', ') || 'none'}, ${c.state}, ${c.attempts} attempt(s), ${c.tokens} tokens, ${(c.ms / 1000).toFixed(0)} s, USD ${c.cost_usd.toFixed(3)}`)
  const text = ['# Digest run', '', `Status: ${state}.`, `Run digested: ${inRepo(ROOT)}`, `Digest directory: ${inRepo(OUT)}`,
    `Command, from ${process.cwd()}: \`node ${process.argv.slice(1).join(' ')}\``,
    `Pipeline commit: ${wfRun.git ? `${wfRun.git.commit}${wfRun.git.dirty ? ' (working tree dirty)' : ''}` : 'unknown'}; pipeline.js sha256 ${wfRun.script_sha256}`,
    `Wall time: ${((Date.now() - t0) / 1000).toFixed(1)} s (${new Date(t0).toISOString()} to ${new Date().toISOString()})`,
    `Spend, as the runners report it (Codex reports tokens, not dollars): USD ${st.cost_usd.toFixed(3)}, ${st.tokens} tokens`, 'Calls:', ...calls,
    ...extra, 'Every prompt and reply: wf/agents/; every call: wf/journal.jsonl.', ''].join('\n')
  write('RUN.md', text)
  return text
}
const fail = msg => { log(`digest: ${msg}`); return { error: msg, result_md: runMd(`failed: ${msg}`) } }

// ---------- 1. reader: answers the standing questions, claim-blind; runs in the run root, read-only ----------
phase('reader')
A.cwd = ROOT   // wf.js gives ls- roles args.cwd as their working directory
const reader = await agent(fill('reader', { run_root: ROOT, max_mb: MAX / 1e6, questions: standing.map(([id, q]) => `${id}. ${q}`).join('\n') }),
  { label: 'reader', agentType: 'ls-general', model: STRONG, schema: readerSchema })
if (!reader) return fail('the reader call returned nothing (wf/journal.jsonl)')

// ---------- 2. resolve every cited path, copy the evidence ----------
phase('evidence')
// a citation: a parenthesis holding only a path token with a file extension, or with a slash naming something that exists
const EXT = /\.(md|txt|json|jsonl|log|py|sh|js|R|r|cu|c|h|cpp|patch|diff|csv|tsv|toml|ya?ml|html)$/
const pathLike = t => /^[A-Za-z_.][\w.\-/]*$/.test(t) && (EXT.test(t) || (t.includes('/') && fs.existsSync(path.resolve(ROOT, t))))
const inline = text => [...String(text).matchAll(/\(([^()\s]+)\)/g)].map(m => m[1]).filter(pathLike)
const runText = fs.existsSync(path.join(ROOT, 'RUN.md')) ? read(path.join(ROOT, 'RUN.md')) : ''
const named = p => new RegExp(`(?<![\\w./-])${esc(p)}(?![\\w/-])`).test(runText)   // RUN.md names p as a whole path
const hops = ['BRIEF.md', 'QUESTION.md'].map(n => path.join(path.dirname(ROOT), n))
const files = new Map(), map = new Map()   // dest -> entry; cited string -> dest
function resolve(p, supports) {
  if (path.isAbsolute(p)) throw new Error(`citation ${p}: absolute; cite relative to the run root`)
  const abs = path.resolve(ROOT, p)
  if (!fs.existsSync(abs) || !fs.statSync(abs).isFile()) throw new Error(`citation ${p}: no such file`)
  const real = fs.realpathSync(abs), rel = path.relative(ROOT, real), inside = !rel.startsWith('..')
  if (!inside && !named(p) && !hops.includes(real)) throw new Error(`citation ${p}: outside the run and not named in its RUN.md (one hop only)`)
  if (real.startsWith(OUT + path.sep)) throw new Error(`citation ${p}: inside the digest itself`)
  const parts = inside ? rel.split(path.sep) : [path.basename(real)]
  if (parts.some(c => c.startsWith('.')) || /credential|secret|\.pem$|\.key$/i.test(parts.join('/'))) throw new Error(`citation ${p}: hidden or credential file`)
  const bytes = fs.statSync(real).size
  if (bytes > MAX) throw new Error(`citation ${p}: ${bytes} bytes, over the ${MAX / 1e6} MB cap`)
  const dest = inside ? `evidence/${parts.join('/')}` : `evidence/_source/${parts[0]}`
  const seen = files.get(dest)
  if (seen && seen.abs !== real) throw new Error(`citation ${p}: ${dest} is already taken by ${seen.original}`)
  if (!seen) files.set(dest, { original: rel.split(path.sep).join('/'), copied: dest, abs: real, bytes, supports: supports || '' })
  else if (supports && !seen.supports) seen.supports = supports
  map.set(p, dest); map.set(files.get(dest).original, dest)
}
try {
  for (const c of reader.citations) resolve(c.path, c.supports)
  for (const a of Object.values(reader.answers)) for (const p of [...a.citations, ...inline(a.answer)]) resolve(p)
} catch (e) { return fail(e.message) }
for (const f of files.values()) {
  const to = path.join(OUT, f.copied)
  fs.mkdirSync(path.dirname(to), { recursive: true }); fs.copyFileSync(f.abs, to)
  f.sha256 = sha256(fs.readFileSync(to))
}
for (const dest of files.keys()) map.set(dest, dest)   // a path given as its evidence/ copy also resolves
const pattern = new RegExp(`(?<![\\w./-])(?:${[...map.keys()].sort((a, b) => b.length - a.length).map(esc).join('|')})(?![\\w/-])`, 'g')
const rewrite = text => map.size ? String(text).trim().replace(pattern, m => map.get(m)) : String(text).trim()   // cited paths now point into evidence/
const entries = [...files.values()]

// ---------- 3. verify: every cited sentence of the answers against the full text of the cited files ----------
phase('verify')
const checks = standing.flatMap(([qid]) => sentencesOf(reader.answers[qid].answer).filter(s => inline(s).length).map(s => ({ question: qid, sentence: s })))
checks.forEach((c, i) => { c.id = `S${i + 1}` })
const share = new Map()   // fair share of the byte cap: small files whole, the rest split what is left
let left = FILE_BYTES
entries.slice().sort((a, b) => a.bytes - b.bytes).forEach((e, i, all) => { const n = Math.min(e.bytes, Math.floor(left / (all.length - i))); share.set(e.copied, n); left -= n })
const shown = entries.map(e => {
  const buf = fs.readFileSync(path.join(OUT, e.copied)), n = share.get(e.copied)
  if (buf.subarray(0, 4096).includes(0)) return `=== ${e.original} (${e.bytes} bytes)\n[digest: binary file, not shown]`
  return `=== ${e.original} (${e.bytes} bytes)\n${buf.subarray(0, n).toString('utf8')}${n < buf.length ? `\n[digest: truncated by the byte cap; showing the first ${n} of ${buf.length} bytes]` : ''}`
}).join('\n\n')
const verifySchema = obj({ sentences: keyed(checks.map(c => c.id), obj({ question: S, sentence: S, verdict: { enum: VERDICTS }, quote: S, path: { enum: [...map.keys(), ''] }, reason: S })), enums: enumSchema })
const verify = await agent(fill('verify', {
  answers: standing.map(([qid, q]) => [`### ${qid}. ${q}`, reader.answers[qid].answer.trim(), 'Sentences to check:',
    ...checks.filter(c => c.question === qid).map(c => `${c.id}. ${c.sentence}`)].join('\n')).join('\n\n'),
  enums: JSON.stringify(reader.enums, null, 1), files: shown,
}), { label: 'verify', agentType: 'qt-bare', model: STRONG, schema: verifySchema })
if (!verify) return fail('the verify call returned nothing (wf/journal.jsonl)')
const verdictOf = c => verify.sentences[c.id]

// ---------- 4. writer: the five sections from the checked answers ----------
phase('writer')
const mark = { supported: '[supported]', contradicted: '[contradicted]', not_addressed: '[not addressed]' }
const annotated = standing.map(([qid, q]) => [`### ${qid}. ${q}`, ...sentencesOf(reader.answers[qid].answer).map(s => {
  const c = checks.find(x => x.question === qid && x.sentence === s)
  return `${c ? mark[verdictOf(c).verdict] : '[uncited]'} ${s}`
})].join('\n')).join('\n\n')
const writer = await agent(fill('writer', { answers: annotated, enums: JSON.stringify(verify.enums, null, 1) }),
  { label: 'writer', agentType: 'qt-bare', model: STRONG, schema: obj(Object.fromEntries(SECTIONS.map(([k]) => [k, S]))) })
if (!writer) return fail('the writer call returned nothing (wf/journal.jsonl)')

// ---------- write DIGEST.md, QA.md, VERIFY.json, digest.json, MANIFEST.json ----------
phase('write')
write('DIGEST.md', ['# Digest', '', ...SECTIONS.flatMap(([k, h]) => [`## ${h}`, '', rewrite(writer[k]), ''])].join('\n'))
const checked = checks.map(c => { const v = verdictOf(c); return { id: c.id, question: c.question, sentence: rewrite(c.sentence), verdict: v.verdict,
  quote: v.quote.replace(/\s+/g, ' ').trim(), path: v.path ? map.get(v.path) : '', reason: v.reason } })
const count = (xs, v) => xs.filter(x => x.verdict === v).length
const qa = ['# Questions and answers', '']
for (const [qid, q] of standing) {
  const a = reader.answers[qid], src = [...new Set(a.citations.map(c => map.get(c)))], mine = checked.filter(c => c.question === qid)
  qa.push(`## ${qid}. ${q}`, '', rewrite(a.answer), '', ...(src.length ? [`Sources: ${src.map(d => `(${d})`).join(', ')}.`, ''] : []),
    `Checked: ${count(mine, 'supported')} sentences supported, ${count(mine, 'contradicted')} contradicted, ${count(mine, 'not_addressed')} not addressed.`, '')
  for (const c of mine.filter(x => x.verdict !== 'supported'))
    qa.push(`${c.verdict === 'contradicted' ? 'Contradicted' : 'Not addressed'}: ${c.sentence}`, '',
      c.quote ? `Quote (${c.path}): "${c.quote}"` : `Quote: none${c.path ? `; the cited file (${c.path}) does not bear on it` : ''}.`, '')
}
write('QA.md', qa.join('\n'))
write('VERIFY.json', JSON.stringify({ summary: Object.fromEntries([['sentences', checked.length], ...VERDICTS.map(v => [v, count(checked, v)])]), sentences: checked }, null, 1) + '\n')
write('digest.json', JSON.stringify(verify.enums, null, 1) + '\n')
const manifest = () => ({ run_root: inRepo(ROOT), run_name: path.basename(ROOT), created_utc: new Date().toISOString(),
  pipeline: { commit: wfRun.git && wfRun.git.commit, dirty: wfRun.git && wfRun.git.dirty, script_sha256: wfRun.script_sha256 },
  models: Object.fromEntries(['reader', 'verify', 'writer', 'notebook', 'notebook-repair'].map(l => [l, modelOf(l)])),
  files: entries.map(({ original, copied, sha256, bytes, supports }) => ({ original, copied, sha256, bytes, supports })) })
write('MANIFEST.json', JSON.stringify(manifest(), null, 1) + '\n')

// ---------- 5. notebook, and one repair if the export fails ----------
phase('notebook')
A.cwd = OUT
const nbSchema = obj({ source: S })
const nb = await agent(fill('notebook', { files: ['DIGEST.md', 'QA.md', 'digest.json', 'MANIFEST.json'].map(n => `=== ${n}\n${read(path.join(OUT, n))}`).join('\n') }),
  { label: 'notebook', agentType: 'ls-general', model: MAIN, schema: nbSchema })
if (!nb) return fail('the notebook call returned nothing (wf/journal.jsonl)')
const source = s => s.endsWith('\n') ? s : `${s}\n`
write('digest.py', source(nb.source))
const exported = spawnSync('python3', ['-I', CHECK, '--export', OUT], { encoding: 'utf8', timeout: 900000 })
let repaired = 'not needed'
if (exported.status !== 0) {
  const fixed = await agent(fill('repair', { stderr: `${exported.stdout}${exported.stderr}`.trim().split('\n').slice(-60).join('\n'), source: nb.source }),
    { label: 'notebook-repair', agentType: 'ls-general', model: MAIN, schema: nbSchema })
  repaired = fixed ? 'repaired once' : 'repair call returned nothing'
  if (fixed) write('digest.py', source(fixed.source))
}
write('MANIFEST.json', JSON.stringify(manifest(), null, 1) + '\n')

// ---------- 6. check.py (it runs the export again, sandboxed), then RUN.md ----------
phase('check')
const chk = spawnSync('python3', ['-I', CHECK, OUT], { encoding: 'utf8', timeout: 900000 })
const check = fs.existsSync(path.join(OUT, 'CHECK.json')) ? JSON.parse(read(path.join(OUT, 'CHECK.json'))) : { pass: false, failed: [`check.py did not run: ${chk.error || chk.stderr}`] }
const state = check.pass ? 'done, all checks pass' : `done, checks failed: ${check.failed.join(', ')}`
const v = JSON.parse(read(path.join(OUT, 'VERIFY.json'))).summary
const md = runMd(state, [`Verify: ${v.sentences} cited sentences, ${v.supported} supported, ${v.contradicted} contradicted, ${v.not_addressed} not addressed`,
  `Notebook export: ${repaired}`, `Check: ${check.pass ? 'pass' : `fail (${check.failed.join(', ')})`}; details in CHECK.json`])
log(`digest: ${state}`)
return { ...(check.pass ? {} : { error: `checks failed: ${check.failed.join(', ')}` }), digest: OUT, enums: verify.enums, verify: v, files: entries.length, result_md: md }
