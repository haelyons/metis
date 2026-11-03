'use strict'
const fs = require('node:fs')
const path = require('node:path')

// Reserve before launch snapshots are made, or directly from pipeline.js.
async function reserve(args) {
  const root = path.resolve(args.run_root), control = path.join(root, 'control')
  // the shared ledger is opt-in (record_raid: true, set by launch.js for real runs); otherwise a run-local one, so tests never touch it
  const file = path.join(control, 'raid.json'), ledger = process.env.M5_RAIDS_LEDGER || (args.record_raid === true ? path.join(__dirname, 'raids_used.jsonl') : path.join(control, 'raids_used.jsonl'))
  const blind = args.blind ?? false
  if (typeof blind !== 'boolean') throw new Error('blind must be a boolean')
  if (args.raid != null && (typeof args.raid !== 'string' || !args.raid.trim() || /[\r\n]/.test(args.raid)))
    throw new Error('raid must be a non-empty single-line string')
  fs.mkdirSync(control, { recursive: true })
  // Serialise selection and append across simultaneous runs.
  for (;;) {
    try { fs.mkdirSync(ledger + '.lock'); break }
    catch (e) { if (e.code !== 'EEXIST') throw e; await new Promise(resolve => setTimeout(resolve, 25)) }
  }
  try {
    if (fs.existsSync(file)) {
      const saved = JSON.parse(fs.readFileSync(file, 'utf8'))
      if (saved.blind !== blind || (args.raid != null && args.raid !== saved.raid)) throw new Error('run raid already reserved')
      return saved
    }
    const used = new Set(fs.existsSync(ledger) ? fs.readFileSync(ledger, 'utf8').split('\n').filter(Boolean).map(line => JSON.parse(line).raid) : [])
    const theme = JSON.parse(fs.readFileSync(path.join(__dirname, 'raids.json'), 'utf8'))
    const names = theme[blind ? 'blind' : 'public']
    let raid = args.raid
    for (let i = 0; raid == null; i++) {
      const cycle = Math.floor(i / names.length) + 1
      const candidate = names[i % names.length] + (cycle === 1 ? '' : cycle)
      if (!used.has(candidate)) raid = candidate
    }
    const record = { raid, blind, run_root: root, utc: new Date().toISOString() }
    fs.appendFileSync(ledger, JSON.stringify(record) + '\n')
    fs.writeFileSync(file, JSON.stringify(record, null, 2) + '\n', { flag: 'wx' })
    return record
  } finally { fs.rmdirSync(ledger + '.lock') }
}

module.exports = { reserve }
if (require.main === module) {
  const [run_root, ...rest] = process.argv.slice(2)
  reserve({ run_root, raid: rest.find(value => value !== '--blind'), blind: rest.includes('--blind'), record_raid: true })
    .catch(error => { console.error(error.message); process.exitCode = 1 })
}
