#!/usr/bin/env node
'use strict'

// Runs a test suite and prints only its FAIL lines and summary; exits with the suite's status.
// Usage: node tools/run_failures_only.js tools/<suite>.js
const path = require('node:path')
const { spawnSync } = require('node:child_process')

const suite = process.argv[2]
if (!suite) { console.error('usage: node tools/run_failures_only.js tools/<suite>.js'); process.exit(2) }
const result = spawnSync(process.execPath, [path.resolve(suite)], { encoding: 'utf8', maxBuffer: 1 << 28 })
const lines = (result.stdout || '').split('\n')
for (const line of lines) if (/^FAIL\b/.test(line) || /checks passed|check\(s\) FAILED/.test(line)) console.log(line)
console.log(`ok lines: ${lines.filter(line => line.startsWith('ok ')).length}`)
if (result.stderr) console.log(`stderr tail: ${result.stderr.slice(-2000)}`)
process.exit(result.status ?? 1)
