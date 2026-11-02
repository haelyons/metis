export const meta = { name: 'digest', description: 'One finished run into <run>/digest/: three model calls, everything else deterministic' }
// wf.js script; the spec is README.txt beside this file. args: { run_root, out?, force?, max_evidence_mb?, verdict_bytes? }
// The models only return JSON; this script resolves and copies the evidence and writes every file.
const { default: path } = await import('node:path')
const fs = await import('node:fs')
const { createHash } = await import('node:crypto')
const { spawnSync } = await import('node:child_process')

const t0 = Date.now()
const A = (typeof args === 'string' ? JSON.parse(args) : args) || {}
if (!A.run_root) return { error: 'digest needs args.run_root' }
const WF = path.dirname(agent.journal)
const wfRun = JSON.parse(fs.readFileSync(path.join(WF, 'run.json'), 'utf8'))
const HOME = path.dirname(wfRun.script)
const ROOT = fs.realpathSync(path.resolve(A.run_root))
const OUT = path.resolve(A.out || path.join(ROOT, 'digest'))
const MAX = (A.max_evidence_mb || 20) * 1e6, VERDICT_BYTES = A.verdict_bytes || 200000
if (!fs.existsSync(path.join(OUT, 'wf')) || fs.realpathSync(path.join(OUT, 'wf')) !== WF) return { error: `run wf.js with --out ${path.join(OUT, 'wf')}` }
const ENUMS = {   // keep in step with check.py
  headline_kind: ['speedup', 'negative', 'void', 'partial', 'unknown'],
  baseline_kind: ['stock', 'tuned', 'one_thread', 'cpu_library', 'other', 'unknown'],
  equivalence: ['bit_identical', 'within_tolerance', 'not_checked', 'failed', 'unknown'],
  prediction_hit: ['yes', 'partly', 'no', 'not_sealed', 'unknown'],
  evidence: ['measured', 'inferred', 'unknown'],
  anchor: ['measured', 'page_value_only', 'not_run', 'none', 'unknown'],
}
const SECTIONS = [['question', 'Question'], ['answer', 'Answer'], ['constraints', 'Problem and constraints'], ['method', 'Method and assumptions'], ['analysis', 'Analysis']]
const read = f => fs.readFileSync(f, 'utf8')
const write = (name, text) => fs.writeFileSync(path.join(OUT, name), text)
const sha256 = buf => createHash('sha256').update(buf).digest('hex')
const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
const inRepo = p => wfRun.git && !path.relative(wfRun.git.repo, p).startsWith('..') ? path.relative(wfRun.git.repo, p) : p
const rows = () => read(agent.journal).split('\n').filter(Boolean).map(l => JSON.parse(l))
const modelOf = label => (rows().filter(r => r.type === 'result' && r.label === label).pop() || {}).model || null
const chainOf = label => ((rows().filter(r => r.type === 'started' && r.label === label).pop() || {}).chain || []).join(', ') || 'none'

// ---------- refuse an existing digest; questions.md (the owner's) and this run's wf/ may already be there ----------
const OWNER = path.join(OUT, 'questions.md')
const old = fs.readdirSync(OUT).filter(n => !['wf', 'questions.md'].includes(n))
const oldWf = ['journal.jsonl', 'result.json', 'RESULT.md', 'UNDERSTUDY.md', 'shadow.jsonl'].filter(n => fs.existsSync(path.join(WF, n)))
  .concat(fs.readdirSync(path.join(WF, 'agents')).length ? ['agents'] : [])
if (old.length + oldWf.length && !A.force) return { error: `${OUT} already holds a digest (${[...old, ...oldWf.map(n => `wf/${n}`)].join(', ')}); set force: true in args to replace it` }
for (const n of old) fs.rmSync(path.join(OUT, n), { recursive: true, force: true })
if (oldWf.length) { const prev = path.join(WF, `prev-${new Date().toISOString().replace(/[-:]|\..*/g, '')}`); fs.mkdirSync(prev); for (const n of oldWf) fs.renameSync(path.join(WF, n), path.join(prev, n)) }

// ---------- questions: standing (questions.md here) and the owner's (## Beliefs, ## Questions, one "- " item each) ----------
const standing = read(path.join(HOME, 'questions.md')).split('\n').map(l => /^(Q\d+)\.\s+(.+)$/.exec(l)).filter(Boolean).map(m => [m[1], m[2].trim()])
const owner = { beliefs: [], questions: [] }
if (fs.existsSync(OWNER)) {
  let at = null
  for (const line of read(OWNER).split('\n')) {
    const h = /^#+\s*(beliefs|questions)\b/i.exec(line)
    if (h) { at = h[1].toLowerCase(); continue }
    if (/^#/.test(line)) { at = null; continue }
    const item = /^\s*[-*]\s+(.*)$/.exec(line), list = at && owner[at]
    if (list && item) list.push(item[1].trim())
    else if (list && list.length && line.trim()) list[list.length - 1] += ` ${line.trim()}`
  }
}
const ids = (prefix, xs) => xs.map((_, i) => `${prefix}${i + 1}`)

// ---------- schemas (schema.js subset); keyed objects make the validator demand one entry per question or belief ----------
const S = { type: 'string' }, list = { type: 'array', items: S }
const obj = props => ({ type: 'object', additionalProperties: false, required: Object.keys(props), properties: props })
const keyed = (keys, item) => obj(Object.fromEntries(keys.map(k => [k, item])))
const enumSchema = obj(Object.fromEntries(Object.entries(ENUMS).map(([k, v]) => [k, { enum: v }])))
const readerSchema = obj({ observations: keyed(standing.map(q => q[0]), obj({ answer: S, citations: list })),
  ...Object.fromEntries(SECTIONS.map(([k]) => [k, S])), citations: { type: 'array', items: obj({ path: S, supports: S }) }, enums: enumSchema })
const verdictSchema = obj({ beliefs: keyed(ids('B', owner.beliefs), obj({ belief: S, verdict: { enum: ['supported', 'contradicted', 'not_addressed'] }, quote: S, path: S, reason: S })),
  answers: keyed(ids('O', owner.questions), obj({ answer: S })), enums: enumSchema })
const fill = (name, vars) => {
  const text = read(path.join(HOME, 'prompts', `${name}.md`)).replace(/\{\{(\w+)\}\}/g, (m, k) => (k in vars ? String(vars[k]) : m))
  if (/\{\{\w+\}\}/.test(text)) throw new Error(`prompt ${name}: unfilled placeholder`)
  return text
}

// ---------- RUN.md on every exit path ----------
const runMd = (state, extra = []) => {
  const st = JSON.parse(read(path.join(WF, 'status.json')))
  const by = Object.entries(st.by_model || {}).map(([m, v]) => `${m} ${v.calls} call(s), ${v.tokens} tokens, USD ${v.cost_usd.toFixed(3)}`).join('; ') || 'none'
  const text = ['# Digest run', '', `Status: ${state}.`, `Run digested: ${inRepo(ROOT)}`, `Digest directory: ${inRepo(OUT)}`,
    `Command, from ${process.cwd()}: \`node ${process.argv.slice(1).join(' ')}\``,
    `Pipeline commit: ${wfRun.git ? `${wfRun.git.commit}${wfRun.git.dirty ? ' (working tree dirty)' : ''}` : 'unknown'}; pipeline.js sha256 ${wfRun.script_sha256}`,
    `Models: ${['reader', 'verdict', 'notebook'].map(l => `${l} ${modelOf(l)} (understudies: ${chainOf(l)})`).join('; ')}`,
    `Wall time: ${((Date.now() - t0) / 1000).toFixed(1)} s (${new Date(t0).toISOString()} to ${new Date().toISOString()})`,
    `Spend, as the runners report it (Codex reports tokens, not dollars): USD ${st.cost_usd.toFixed(3)}, ${st.tokens} tokens; ${by}`,
    `Owner file: ${fs.existsSync(OWNER) ? `questions.md, ${owner.beliefs.length} belief(s), ${owner.questions.length} question(s)` : 'none'}`,
    ...extra, 'Every prompt and reply: wf/agents/; every call: wf/journal.jsonl.', ''].join('\n')
  write('RUN.md', text)
  return text
}
const fail = msg => { log(`digest: ${msg}`); return { error: msg, result_md: runMd(`failed: ${msg}`) } }

// ---------- 1. reader: claim-blind; runs in the run root, read-only ----------
phase('reader')
A.cwd = ROOT   // wf.js gives ls- roles args.cwd as their working directory
const reader = await agent(fill('reader', { run_root: ROOT, max_mb: MAX / 1e6, questions: standing.map(([id, q]) => `${id}. ${q}`).join('\n') }),
  { label: 'reader', agentType: 'ls-general', model: 'opus', schema: readerSchema })
if (!reader) return fail('the reader call returned nothing (wf/journal.jsonl)')
const readerDir = fs.readdirSync(path.join(WF, 'agents')).find(n => /-reader$/.test(n))
const ownerRel = path.relative(ROOT, OWNER)
const walk = d => fs.readdirSync(d, { withFileTypes: true }).flatMap(e => e.isDirectory() ? walk(path.join(d, e.name)) : [path.join(d, e.name)])
const touched = !!readerDir && fs.existsSync(OWNER) && !ownerRel.startsWith('..') && walk(path.join(WF, 'agents', readerDir))
  .some(f => path.basename(f) !== 'prompt.md' && read(f).includes(ownerRel))

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
  for (const [k] of SECTIONS) for (const p of inline(reader[k])) resolve(p)
  for (const o of Object.values(reader.observations)) for (const p of [...o.citations, ...inline(o.answer)]) resolve(p)
} catch (e) { return fail(e.message) }
for (const f of files.values()) {
  const to = path.join(OUT, f.copied)
  fs.mkdirSync(path.dirname(to), { recursive: true }); fs.copyFileSync(f.abs, to)
  f.sha256 = sha256(fs.readFileSync(to))
}
for (const dest of files.keys()) map.set(dest, dest)   // a verdict path given as its evidence/ copy also resolves
const pattern = new RegExp(`(?<![\\w./-])(?:${[...map.keys()].sort((a, b) => b.length - a.length).map(esc).join('|')})(?![\\w/-])`, 'g')
const rewrite = text => map.size ? String(text).trim().replace(pattern, m => map.get(m)) : String(text).trim()   // cited paths, inline or bare, now point into evidence/

// ---------- 3. verdict: observations first, then the cited files (bounded), then the owner's beliefs ----------
phase('verdict')
const entries = [...files.values()]
const share = new Map()   // fair share of the byte cap: small files whole, the rest split what is left
let left = VERDICT_BYTES
entries.slice().sort((a, b) => a.bytes - b.bytes).forEach((e, i, all) => { const n = Math.min(e.bytes, Math.floor(left / (all.length - i))); share.set(e.copied, n); left -= n })
const shown = entries.map(e => {
  const buf = fs.readFileSync(path.join(OUT, e.copied)), n = share.get(e.copied)
  if (buf.subarray(0, 4096).includes(0)) return `=== ${e.original} (${e.bytes} bytes)\n[digest: binary file, not shown]`
  return `=== ${e.original} (${e.bytes} bytes)\n${buf.subarray(0, n).toString('utf8')}${n < buf.length ? `\n[digest: truncated by the byte cap; showing the first ${n} of ${buf.length} bytes]` : ''}`
}).join('\n\n')
const numbered = (prefix, xs) => xs.length ? xs.map((x, i) => `${prefix}${i + 1}. ${x}`).join('\n') : 'None.'
const verdict = await agent(fill('verdict', {
  observations: standing.map(([id, q]) => { const o = reader.observations[id]; return `${id}. ${q}\n${o.answer.trim()}\nFiles: ${o.citations.join(', ') || 'none'}` }).join('\n\n'),
  enums: JSON.stringify(reader.enums, null, 1), files: shown, beliefs: numbered('B', owner.beliefs), questions: numbered('O', owner.questions),
}), { label: 'verdict', agentType: 'qt-bare', model: 'opus', schema: verdictSchema })
if (!verdict) return fail('the verdict call returned nothing (wf/journal.jsonl)')
for (const [id, v] of Object.entries(verdict.beliefs)) {
  if (v.verdict !== 'not_addressed' && !map.has(v.path)) return fail(`verdict ${id}: path ${JSON.stringify(v.path)} is not one of the files shown`)
  if (v.verdict !== 'not_addressed' && !v.quote.trim()) return fail(`verdict ${id}: ${v.verdict} with no quote`)
}
for (const t of [...Object.values(verdict.beliefs).map(v => v.reason), ...Object.values(verdict.answers).map(a => a.answer)])
  for (const p of inline(t)) if (!map.has(p)) return fail(`verdict cites ${p}, which is not one of the files shown`)

// ---------- 4. write DIGEST.md, QA.md, digest.json, MANIFEST.json ----------
phase('write')
write('DIGEST.md', ['# Digest', '', ...SECTIONS.flatMap(([k, h]) => [`## ${h}`, '', rewrite(reader[k]), ''])].join('\n'))
const qa = ['# Questions and answers', '', '## Standing questions', '']
for (const [id, q] of standing) {
  const o = reader.observations[id], src = [...new Set(o.citations.map(c => map.get(c)))]
  qa.push(`### ${id}. ${q}`, '', rewrite(o.answer), '', ...(src.length ? [`Sources: ${src.map(d => `(${d})`).join(', ')}.`, ''] : []))
}
if (owner.questions.length) qa.push('## Owner questions', '', ...owner.questions.flatMap((q, i) => [`### O${i + 1}. ${q}`, '', rewrite(verdict.answers[`O${i + 1}`].answer), '']))
if (owner.beliefs.length) qa.push('## Owner beliefs', '', ...owner.beliefs.flatMap((b, i) => {
  const v = verdict.beliefs[`B${i + 1}`]
  return [`### B${i + 1}. ${b}`, '', `Verdict: ${v.verdict.replace('_', ' ')}.`, '',
    v.verdict === 'not_addressed' ? 'Quote: none.' : `Quote (${map.get(v.path)}): "${v.quote.replace(/\s+/g, ' ').trim()}"`, '', `Reason: ${rewrite(v.reason)}`, '']
}))
write('QA.md', qa.join('\n'))
write('digest.json', JSON.stringify(verdict.enums, null, 1) + '\n')
const manifest = () => ({ run_root: inRepo(ROOT), run_name: path.basename(ROOT), created_utc: new Date().toISOString(),
  pipeline: { commit: wfRun.git && wfRun.git.commit, dirty: wfRun.git && wfRun.git.dirty, script_sha256: wfRun.script_sha256 },
  models: { reader: modelOf('reader'), verdict: modelOf('verdict'), notebook: modelOf('notebook') }, reader_read_owner_file: touched,
  files: entries.map(({ original, copied, sha256, bytes, supports }) => ({ original, copied, sha256, bytes, supports })) })
write('MANIFEST.json', JSON.stringify(manifest(), null, 1) + '\n')

// ---------- 5. notebook: reads the written files; may read evidence/ to learn its shapes ----------
phase('notebook')
A.cwd = OUT
const nb = await agent(fill('notebook', { files: ['DIGEST.md', 'QA.md', 'digest.json', 'MANIFEST.json'].map(n => `=== ${n}\n${read(path.join(OUT, n))}`).join('\n') }),
  { label: 'notebook', agentType: 'ls-general', model: 'sonnet', schema: obj({ source: S }) })
if (!nb) return fail('the notebook call returned nothing (wf/journal.jsonl)')
write('digest.py', nb.source.endsWith('\n') ? nb.source : `${nb.source}\n`)
write('MANIFEST.json', JSON.stringify(manifest(), null, 1) + '\n')

// ---------- 6. check.py (it also runs the marimo export), then RUN.md ----------
phase('check')
const chk = spawnSync('python3', ['-I', path.join(HOME, 'check.py'), OUT], { encoding: 'utf8', timeout: 900000 })
const check = fs.existsSync(path.join(OUT, 'CHECK.json')) ? JSON.parse(read(path.join(OUT, 'CHECK.json'))) : { pass: false, failed: [`check.py did not run: ${chk.error || chk.stderr}`] }
const state = check.pass ? 'done, all checks pass' : `done, checks failed: ${check.failed.join(', ')}`
const md = runMd(state, [`Check: ${check.pass ? 'pass' : `fail (${check.failed.join(', ')})`}; details in CHECK.json`, `Reader read the owner file: ${touched}`])
log(`digest: ${state}`)
return { ...(check.pass ? {} : { error: `checks failed: ${check.failed.join(', ')}` }), digest: OUT, enums: verdict.enums, files: entries.length, result_md: md }
