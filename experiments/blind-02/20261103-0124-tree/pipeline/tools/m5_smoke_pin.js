#!/usr/bin/env node
'use strict'

// Fetch-side pin for implement's baseline adapter smoke (m5/SCHEMAS.md "Baseline adapter smoke"),
// for pipeline fixtures with evaluate budgets small enough that the host's speed could decide the
// smoke's `cost` gate. Run by a fixture's fetch after the copy:
//   node tools/m5_smoke_pin.js <fetched destination> <log.jsonl>
// Every fetched smoke.json holding a well-formed measurement, exactly {"process_wall_s": x} with x
// finite and nonnegative, is rewritten to {"process_wall_s": PINNED_WALL_S}. Anything else is left
// as fetched, so implement still sees a malformed or missing file. Each rewrite is logged so the
// fixture can confirm the pin happened. tools/test_m5_adapter_smoke.js checks the real measurement.
const fs = require('node:fs')
const path = require('node:path')
const PINNED_WALL_S = 0.01
module.exports = { PINNED_WALL_S, pinned }
// Logged rewrites, for the fixture's checks.
function pinned(log) {
  return fs.existsSync(log) ? fs.readFileSync(log, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : []
}
function measurement(text) {
  try {
    const value = JSON.parse(text)
    return value && typeof value === 'object' && !Array.isArray(value) && Object.keys(value).join() === 'process_wall_s' &&
      Number.isFinite(value.process_wall_s) && value.process_wall_s >= 0
  } catch { return false }
}
function visit(file, log) {
  const stat = fs.lstatSync(file, { throwIfNoEntry: false })
  if (!stat) return
  if (stat.isDirectory()) {
    for (const entry of fs.readdirSync(file)) visit(path.join(file, entry), log)
    return
  }
  if (!stat.isFile() || path.basename(file) !== 'smoke.json') return
  const measured = fs.readFileSync(file, 'utf8')
  if (!measurement(measured)) return
  fs.writeFileSync(file, JSON.stringify({ process_wall_s: PINNED_WALL_S }) + '\n')
  fs.appendFileSync(log, JSON.stringify({ file, measured, value: PINNED_WALL_S }) + '\n')
}
if (require.main === module) {
  const [destination, log] = process.argv.slice(2)
  if (!destination || !log) { console.error('usage: m5_smoke_pin.js <destination> <log.jsonl>'); process.exit(2) }
  visit(destination, log)
}
