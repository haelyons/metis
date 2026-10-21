'use strict'
// The substitution report of one wf.js run: which model answered each call, which family stood in and why, and in
// shadow mode whether the two families agreed. Reads journal.jsonl, shadow.jsonl and run.json; writes nothing.
// usage: node understudy_report.js <run dir>     (wf.js writes <run dir>/UNDERSTUDY.md with the same text)
const fs = require('node:fs')
const path = require('node:path')

function rows(file) { return fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(l => JSON.parse(l)) : [] }

function report(run) {
  const J = rows(path.join(run, 'journal.jsonl')), S = rows(path.join(run, 'shadow.jsonl'))
  const info = fs.existsSync(path.join(run, 'run.json')) ? JSON.parse(fs.readFileSync(path.join(run, 'run.json'), 'utf8')) : {}
  const started = J.filter(r => r.type === 'started'), by = {}
  for (const r of J) if (r.type === 'result' || r.type === 'failed' || r.type === 'cached' || r.type === 'understudy' || r.type === 'shadow') (by[r.n] = by[r.n] || {})[r.type] = r
  const u = info.understudy || {}
  const L = [`# Understudy report: ${info.name || path.basename(run)}`, '',
    `Primary family ${u.primary_family || '?'}, mode ${u.mode || '?'}, on refusal ${u.on_refusal || '?'}, hands over on ${(u.retry_on || []).join(', ') || '-'}; profile ${u.profile || '?'}; routes ${(u.routes || []).length}.`, '',
    '| # | label | role | tier | primary | kind | understudy | used? | by | ms | USD |', '|---|---|---|---|---|---|---|---|---|---|---|']
  const tally = { calls: 0, ok: 0, failed: 0, cached: 0, substituted: 0, refusals: 0, by_kind: {}, by_role: {} }
  for (const s of started) {
    const d = by[s.n] || {}, res = d.result, fail = d.failed, und = d.understudy
    const kind = (fail && fail.kind) || (und && und.kind) || (res ? 'none' : d.cached ? 'cached' : 'running')
    const used = und ? (und.ok ? 'yes' : 'tried, failed') : (d.shadow ? 'shadow' : '-')
    const prod = res ? res.model : fail ? '-' : d.cached ? 'cache' : '…'
    const meta = (() => { try { return JSON.parse(fs.readFileSync(path.join(run, 'agents', `${String(s.n).padStart(4, '0')}-${s.label.replace(/[^A-Za-z0-9._-]+/g, '_').slice(0, 80)}`, 'meta.json'), 'utf8')) } catch { return {} } })()
    L.push(`| ${s.n} | ${s.label} | ${s.role} | ${s.tier || ''} | ${s.model} | ${kind} | ${s.understudy || '-'} | ${used} | ${prod} | ${meta.ms != null ? Math.round(meta.ms / 1000) + ' s' : ''} | ${meta.cost_usd != null ? meta.cost_usd.toFixed(3) : ''} |`)
    tally.calls++
    if (res) tally.ok++; if (fail) tally.failed++; if (d.cached) tally.cached++
    if (res && res.substituted) tally.substituted++
    if (kind === 'refusal') tally.refusals++
    if (kind !== 'none' && kind !== 'cached' && kind !== 'running') tally.by_kind[kind] = (tally.by_kind[kind] || 0) + 1
    const br = tally.by_role[s.role] = tally.by_role[s.role] || { calls: 0, substituted: 0, failed: 0 }
    br.calls++; if (res && res.substituted) br.substituted++; if (fail) br.failed++
  }
  L.push('', `Calls ${tally.calls}: ${tally.ok} returned (${tally.substituted} by the understudy), ${tally.failed} failed, ${tally.cached} cached; refusals ${tally.refusals}; primary failure kinds ${JSON.stringify(tally.by_kind)}.`, '',
    '## By role', '', '| role | calls | substituted | failed |', '|---|---|---|---|', ...Object.entries(tally.by_role).map(([r, v]) => `| ${r} | ${v.calls} | ${v.substituted} | ${v.failed} |`))
  const fam = (info.totals || {}).by_family || {}
  if (Object.keys(fam).length) L.push('', '## By family', '', '| family | calls | failed | refusals | tokens | USD |', '|---|---|---|---|---|---|', ...Object.entries(fam).map(([f, v]) => `| ${f} | ${v.calls} | ${v.failed} | ${v.refusals} | ${v.tokens.toLocaleString()} | ${v.cost_usd.toFixed(3)} |`))
  if (S.length) {
    const agree = S.filter(r => r.agree).length, both = S.filter(r => r.primary.kind === 'none' && r.understudy.kind === 'none').length
    L.push('', `## Shadow: ${S.length} call(s) run by both families; both returned ${both}; identical values ${agree}`, '', '| # | label | primary kind | understudy kind | agree | fields that differ | primary ms / USD | understudy ms / USD |', '|---|---|---|---|---|---|---|---|',
      ...S.map(r => `| ${r.n} | ${r.label} | ${r.primary.kind} | ${r.understudy.kind} | ${r.agree ? 'yes' : 'no'} | ${(r.fields_differ || []).join(', ') || '-'} | ${Math.round(r.primary.ms / 1000)} / ${r.primary.cost_usd.toFixed(3)} | ${Math.round(r.understudy.ms / 1000)} / ${r.understudy.cost_usd.toFixed(3)} |`))
  }
  return L.join('\n') + '\n'
}

module.exports = { report }
if (require.main === module) process.stdout.write(report(path.resolve(process.argv[2] || '.')))
