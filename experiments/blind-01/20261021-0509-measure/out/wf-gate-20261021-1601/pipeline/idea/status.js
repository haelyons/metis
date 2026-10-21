#!/usr/bin/env node
'use strict'
// Progress of frame runs. usage: node status.js [run dir | --latest] [--watch]
const fs = require('node:fs')
const path = require('node:path')
const CFG = JSON.parse(fs.readFileSync(path.join(__dirname, 'config.json'), 'utf8'))
const argv = process.argv.slice(2)

function latest() {
  const runs = []
  const walk = (d, depth) => { for (const e of fs.readdirSync(d, { withFileTypes: true })) if (e.isDirectory()) { const p = path.join(d, e.name); if (fs.existsSync(path.join(p, 'status.json'))) runs.push(p); else if (depth < 7) walk(p, depth + 1) } }
  if (fs.existsSync(CFG.experiments_dir)) walk(CFG.experiments_dir, 0)
  return runs.sort((a, b) => fs.statSync(path.join(b, 'status.json')).mtimeMs - fs.statSync(path.join(a, 'status.json')).mtimeMs)[0]
}
function show(dir) {
  const s = JSON.parse(fs.readFileSync(path.join(dir, 'status.json'), 'utf8'))
  const age = Math.round((Date.now() - Date.parse(s.started)) / 60000)
  const lines = [`${s.card} · stage ${s.stage}${s.done ? ' (done)' : ''} · ${age} min · $${s.cost_usd.toFixed(4)} · ${s.tokens.toLocaleString()} tokens`, `run: ${s.run_dir}`]
  const calls = s.calls.length > 25 ? s.calls.filter(c => c.state !== 'ok' && c.state !== 'cached').concat(s.calls.filter(c => c.state === 'ok' || c.state === 'cached').slice(-10)) : s.calls
  if (s.calls.length > 25) lines.push(`  ${s.calls.length} calls: ${['ok', 'running', 'queued', 'failed', 'cached'].map(k => `${s.calls.filter(c => c.state === k).length} ${k}`).join(', ')}; showing open ones and the last 10 finished`)
  for (const c of calls) lines.push(`  ${c.state.padEnd(7)} ${c.id.padEnd(40)} ${c.model.padEnd(28)} ${(c.ms / 60000).toFixed(1).padStart(5)} min  $${c.cost_usd.toFixed(4)}${c.attempts > 1 ? `  (${c.attempts} attempts)` : ''}${c.errors && c.errors.length ? `  ${c.errors.join('; ').slice(0, 120)}` : ''}`)
  if (s.by_model) for (const [m, v] of Object.entries(s.by_model)) { const cap = (CFG.go_monthly_caps_usd || {})[m.split('/').pop()]; lines.push(`  spend ${m}: $${v.cost_usd.toFixed(3)}${cap ? ` (${(100 * v.cost_usd / cap).toFixed(1)}% of monthly cap, ${(500 * v.cost_usd / cap).toFixed(1)}% of a 5-hour window)` : ''}`) }
  if (s.best) lines.push(`best: ${s.best.name} · fit ${s.best.fit} · change ${s.best.change} · new ${s.best.new} · ${s.best.sum}/15`)
  if (s.error) lines.push(`error: ${s.error.split('\n')[0]}`)
  return { text: lines.join('\n'), done: s.done }
}
const dir = argv.find(a => !a.startsWith('--')) || latest()
if (!dir) { console.log(`no runs under ${CFG.runs_dir}`); process.exit(0) }
if (!argv.includes('--watch')) console.log(show(dir).text)
else { const tick = () => { const r = show(dir); console.clear(); console.log(r.text); if (r.done) process.exit(0) }; tick(); setInterval(tick, 10000) }
