#!/usr/bin/env node
'use strict'

// Black-box contract tests. Do not import the pipeline or launcher implementation.
// Usage: node tools/test_m5_pipeline.js
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const assert = require('node:assert/strict')
const { createHash } = require('node:crypto')
const { spawn } = require('node:child_process')

const ROOT = path.resolve(__dirname, '..')
const STAGES = ['intake', 'reproduce', 'profile', 'seal', 'propose', 'implement', 'evaluate', 'takeaways']
const parent = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_pipeline_'))
let failures = 0
let checks = 0

function check(label, run) {
  checks++
  try {
    run()
    console.log(`ok ${label}`)
  } catch (error) {
    failures++
    console.log(`FAIL ${label}: ${error.message}`)
  }
}

// Compare paths, types, modes, file bytes, and symlink targets outside this run.
// Directory timestamps are omitted because creating children changes them.
function snapshot(excludedRoot) {
  const entries = []
  function visit(dir) {
    for (const name of fs.readdirSync(dir).sort()) {
      const file = path.join(dir, name)
      if (file === excludedRoot) continue
      const stat = fs.lstatSync(file)
      const entry = [path.relative(parent, file), stat.mode]
      if (stat.isSymbolicLink()) entry.push('symlink', fs.readlinkSync(file))
      else if (stat.isDirectory()) entry.push('directory')
      else entry.push('file', createHash('sha256').update(fs.readFileSync(file)).digest('hex'))
      entries.push(entry)
      if (stat.isDirectory()) visit(file)
    }
  }
  visit(parent)
  return entries
}

function readJSON(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'))
}

async function runCase(name, failedStage, launch = false) {
  const runRoot = path.join(parent, name)
  const control = path.join(runRoot, 'control')
  const out = path.join(runRoot, 'agent', 'wf')
  fs.mkdirSync(control, { recursive: true })
  const brief = path.join(parent, `${name}-brief.md`)
  fs.writeFileSync(brief, '# Test brief\nNo experiment directory or model is needed.\n')
  const argsFile = path.join(control, 'args.json')
  const stub = { intake: 'PASS', reproduce: 'PASS', profile: 'PASS', seal: 'PASS', propose: 'PASS', implement: 'PASS', evaluate: 'PASS', ...(failedStage ? { [failedStage]: 'FAIL' } : {}) }
  if (!launch) {
    fs.writeFileSync(argsFile, JSON.stringify({
      run_root: runRoot,
      brief,
      tag: name,
      stub,
    }))
  }
  const before = snapshot(runRoot)
  const command = launch
    ? [path.join(ROOT, 'launch.js'), 'stage', '--stage', 'm5', '--run-root', runRoot, '--brief', brief, '--dry-run']
    : [path.join(ROOT, 'idea', 'wf.js'), '--script', path.join(ROOT, 'm5', 'pipeline.js'),
      '--args', argsFile, '--out', out, '--disable-family', 'claude']
  // File-backed output also works in sandboxes that restrict synchronous pipes.
  const stdoutFile = path.join(runRoot, 'test-stdout.log')
  const stderrFile = path.join(runRoot, 'test-stderr.log')
  const stdout = fs.openSync(stdoutFile, 'w')
  const stderr = fs.openSync(stderrFile, 'w')
  async function execute(executable, command, cwd = ROOT, envExtra = {}) {
    return new Promise(resolve => {
      const childProcess = spawn(executable, command, {
        cwd,
        timeout: 30000,
        stdio: ['ignore', stdout, stderr],
        env: { ...process.env, M5_RAIDS_LEDGER: path.join(runRoot, 'test-raids_used.jsonl'), WF_STUB: path.join(ROOT, 'tools', 'e2e_wf.js'), ...envExtra },
      })
      let error
      childProcess.on('error', value => { error = value })
      childProcess.on('close', (status, signal) => resolve({ status, signal, error }))
    })
  }
  const realLedger = path.join(ROOT, 'm5', 'raids_used.jsonl')
  const realBefore = launch ? (fs.existsSync(realLedger) ? fs.readFileSync(realLedger) : null) : null
  if (launch) {
    check(`${name}: real m5/raids_used.jsonl readable before launch`, () => {
      assert.ok(realBefore === null || Buffer.isBuffer(realBefore))
    })
  }
  // launch.js reserves via the shared ledger for real runs; redirect to a temp file under R.
  const launchEnv = launch ? { M5_RAIDS_LEDGER: path.join(runRoot, 'test-raids_used.jsonl') } : {}
  let child = await execute(process.execPath, command, ROOT, launchEnv)
  if (launch && child.status === 0 && !child.error) {
    // The launcher has no stub option. Set overrides in its generated args,
    // then execute its recorded command against the frozen pipeline copy.
    const launchArgsFile = path.join(out, 'args.json')
    fs.writeFileSync(launchArgsFile, JSON.stringify({ ...readJSON(launchArgsFile), stub }))
    const recordedCommand = fs.readFileSync(path.join(out, 'RUN.md'), 'utf8').match(/^Command: (.+)$/m)
    assert.ok(recordedCommand, 'launcher must record its workflow command')
    child = await execute('/bin/sh', ['-c', recordedCommand[1]], path.join(out, 'pipeline'))
  }
  if (launch) {
    check(`${name}: real m5/raids_used.jsonl byte-identical after launch`, () => {
      assert.deepEqual(fs.existsSync(realLedger) ? fs.readFileSync(realLedger) : null, realBefore)
    })
  }
  fs.closeSync(stdout)
  fs.closeSync(stderr)
  check(`${name}: exits successfully`, () => {
    assert.equal(child.status, 0,
      `${child.error || ''}; exit ${child.status}, signal ${child.signal}\n${fs.readFileSync(stdoutFile, 'utf8').slice(-1200)}\n${fs.readFileSync(stderrFile, 'utf8').slice(-1200)}`)
    assert.ifError(child.error)
  })
  check(`${name}: no changes outside R within temporary parent`, () => {
    assert.deepEqual(snapshot(runRoot), before)
  })
  check(`${name}: workflow run folder under R/agent/wf/`, () => {
    assert.ok(fs.statSync(out).isDirectory())
    const realRoot = fs.realpathSync(runRoot) + path.sep
    assert.ok(fs.realpathSync(out).startsWith(realRoot), 'workflow folder escapes R')
    assert.ok(fs.statSync(path.join(out, 'result.json')).isFile())
    assert.ok(fs.statSync(path.join(out, 'journal.jsonl')).isFile())
  })

  const failedIndex = failedStage ? STAGES.indexOf(failedStage) : -1
  const expected = STAGES.map((stage, index) => ({
    stage,
    status: stage === failedStage ? 'FAIL'
      : failedIndex >= 0 && index > failedIndex && stage !== 'takeaways' ? 'SKIPPED' : 'PASS',
  }))
  const signaturesFile = path.join(runRoot, 'operator', 'signatures.jsonl')
  const signatures = () => fs.readFileSync(signaturesFile, 'utf8').trim().split('\n').map(line => {
    const row = JSON.parse(line)
    return row.signature || row
  })
  check(`${name}: exactly 8 signature lines in stage order`, () => {
    const rows = signatures()
    assert.equal(rows.length, 8)
    assert.deepEqual(rows.map(row => row.stage), STAGES, `signature sample: ${JSON.stringify(rows[0])}`)
  })
  check(`${name}: signature statuses and SKIPPED set`, () => {
    assert.deepEqual(signatures().map(({ stage, status }) => ({ stage, status })), expected)
  })
  check(`${name}: takeaways still runs`, () => {
    assert.deepEqual(signatures().filter(row => row.stage === 'takeaways').map(row => row.status), ['PASS'])
  })
  check(`${name}: returned stages match contract`, () => {
    const result = readJSON(path.join(out, 'result.json'))
    assert.ok(Array.isArray(result.stages), `result.stages must be an array: ${JSON.stringify(result)}`)
    assert.deepEqual(result.stages.map(({ stage, status }) => ({ stage, status })), expected)
  })
  check(`${name}: stopped_at is ${failedStage || 'null'}`, () => {
    assert.equal(readJSON(path.join(out, 'result.json')).stopped_at, failedStage || null)
  })
}

async function main() {
  try {
    await runCase('all-pass')
    // A failed seal or propose (including propose's unmeasured absence of a feasible method) skips
    // downstream stages as for any failure; the measured negative finding is covered in test_m5_propose.js.
    for (const stage of ['intake', 'profile', 'seal', 'propose', 'implement']) await runCase(`fail-${stage}`, stage)
    await runCase('launch-pass', null, true)
  } catch (error) {
    failures++
    console.log(`FAIL test harness: ${error.stack}`)
  } finally {
    fs.rmSync(parent, { recursive: true, force: true })
  }
  console.log(failures ? `${failures} check(s) FAILED (${checks} checks)` : 'all checks passed')
  process.exitCode = failures ? 1 : 0
}
main()
