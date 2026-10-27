#!/usr/bin/env node
'use strict'

// m5 model policy contracts (SCHEMAS.md "m5 model policy"). Black box: m5/wf_config.json is loaded at run time
// and resolved through the unchanged idea/understudy.js; launch.js is exercised only through its --dry-run.
// Usage: node tools/test_m5_policy.js
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const assert = require('node:assert/strict')
const { spawn } = require('node:child_process')
const U = require('../idea/understudy.js')

const ROOT = path.resolve(__dirname, '..')
const readJSON = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_policy_'))
let failures = 0, checks = 0
function check(label, test) {
  checks++
  try { test(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${error.message}`) }
}

// Expected values come from SCHEMAS.md, not from the config under test.
const CHAIN = { codex: ['opencode'], opencode: ['codex'], claude: ['codex'], cursor: ['codex'] }
const ROUTES = [{ match: '^skeptic-[45]$', primary: 'claude/sonnet' }, { match: '^review$', primary: 'claude/sonnet' }]
const CLAUDE_LABELS = ['skeptic-4', 'skeptic-5', 'review']
const CODEX_LABELS = ['intake', 'harness', 'harness-repair', 'anchors-repair', 'seal', 'seal-repair', 'propose',
  'skeptic-1', 'skeptic-2', 'skeptic-3', 'tests', 'implement']
const ROLES = [undefined, 'qt-bare', 'ls-writer']
const PINNED = [undefined, 'haiku', 'sonnet', 'opus']
const withoutDocs = value => Object.fromEntries(Object.entries(value).filter(([key]) => !key.startsWith('_')))

// The understudy policy exactly as idea/wf.js builds it from a --config file (wf.js lines 42-47).
function policy(all) {
  const cfg = U.withDefaults({ ...(all.understudy || {}) })
  const wf = all.workflow
  cfg.families.opencode.models = { strong: wf.main_model, main: wf.main_model, cheap: wf.cheap_model, ...(cfg.families.opencode.models || {}) }
  cfg.families.opencode.by_role = { ...(wf.by_role || {}), ...(cfg.families.opencode.by_role || {}) }
  return cfg
}

function configChecks() {
  const file = path.join(ROOT, 'm5', 'wf_config.json')
  let all = null
  check('m5/wf_config.json is readable JSON with workflow and understudy sections', () => {
    all = readJSON(file)
    assert.equal(typeof all.workflow, 'object')
    assert.equal(typeof all.understudy, 'object')
  })
  if (!all) return
  check('workflow section is identical to idea/config.json\'s', () => {
    assert.deepEqual(all.workflow, readJSON(path.join(ROOT, 'idea', 'config.json')).workflow)
  })
  check('understudy section: primary codex, fallback, halt on refusal, no disabled families, contract chain', () => {
    const u = all.understudy
    assert.equal(u.primary_family, 'codex')
    assert.equal(u.mode, 'fallback')
    assert.equal(u.on_refusal, 'halt')
    assert.deepEqual(u.disabled_families, [])
    assert.deepEqual(u.chain, CHAIN)
  })
  check('understudy routes are exactly skeptic-4/5 and review to claude/sonnet', () => {
    assert.deepEqual(all.understudy.routes.map(withoutDocs), ROUTES)
  })
  check('no route or family model names Fable', () => assert.ok(!/fable/i.test(JSON.stringify(all.understudy))))

  const cfg = policy(all)
  for (const label of CLAUDE_LABELS) {
    check(`${label}: claude/sonnet primary with codex as the only understudy (--family codex)`, () => {
      for (const agentType of ROLES) for (const pinned of PINNED) {
        const role = U.roleFor(cfg, 'latent_skeptic', { label, agentType })
        const r = U.resolve(cfg, { label, role, pinned, familyOverride: 'codex' })
        const where = `role ${role}, pinned ${pinned}`
        assert.equal(r.primary, 'claude/sonnet', where)
        assert.equal(r.chain.length, 1, `${where}: chain ${JSON.stringify(r.chain)}`)
        assert.equal(U.familyOf(r.chain[0]), 'codex', where)
        assert.equal(r.understudy, r.chain[0], where)
        assert.equal(r.mode, 'fallback', where)
      }
    })
  }
  for (const label of CODEX_LABELS) {
    check(`${label}: codex primary with opencode as the only understudy, no claude (--family codex)`, () => {
      for (const agentType of ROLES) for (const pinned of PINNED) {
        const role = U.roleFor(cfg, 'latent_skeptic', { label, agentType })
        const r = U.resolve(cfg, { label, role, pinned, familyOverride: 'codex' })
        const where = `role ${role}, pinned ${pinned}`
        assert.equal(U.familyOf(r.primary), 'codex', `${where}: primary ${r.primary}`)
        assert.equal(r.chain.length, 1, `${where}: chain ${JSON.stringify(r.chain)}`)
        assert.equal(U.familyOf(r.chain[0]), 'opencode', `${where}: chain ${JSON.stringify(r.chain)}`)
        assert.ok([r.primary, ...r.chain].every(m => U.familyOf(m) !== 'claude'), `${where}: claude model present`)
        assert.equal(r.mode, 'fallback', where)
      }
    })
  }
  check('claude refusal halts; transport failures hand over', () => {
    assert.equal(U.handover(cfg, 'fallback', 'refusal'), false)
    for (const kind of ['timeout', 'exit', 'runner']) assert.equal(U.handover(cfg, 'fallback', kind), true, kind)
  })
}

// Minimal POSIX shell word splitting for the recorded command: quotes and backslashes, no expansion.
function words(command) {
  const out = []
  let word = null, quote = null
  for (let i = 0; i < command.length; i++) {
    const c = command[i]
    if (quote === "'") { if (c === "'") quote = null; else word += c; continue }
    if (quote === '"') {
      if (c === '"') quote = null
      else if (c === '\\' && '"\\$`'.includes(command[i + 1])) word += command[++i]
      else word += c
      continue
    }
    if (/\s/.test(c)) { if (word !== null) out.push(word); word = null; continue }
    word = word ?? ''
    if (c === "'" || c === '"') quote = c
    else if (c === '\\') word += command[++i]
    else word += c
  }
  if (word !== null) out.push(word)
  return out
}

async function launchChecks() {
  const runRoot = path.join(scratch, 'launch')
  fs.mkdirSync(runRoot, { recursive: true })
  const brief = path.join(scratch, 'brief.md')
  fs.writeFileSync(brief, '# Policy test brief\nNo experiment directory or model is needed.\n')
  const stdoutFile = path.join(scratch, 'launch-stdout.log'), stderrFile = path.join(scratch, 'launch-stderr.log')
  const stdout = fs.openSync(stdoutFile, 'w'), stderr = fs.openSync(stderrFile, 'w')
  const realLedger = path.join(ROOT, 'm5', 'raids_used.jsonl')
  const realBefore = fs.existsSync(realLedger) ? fs.readFileSync(realLedger) : null
  let child
  try {
    child = await new Promise(resolve => {
      const proc = spawn(process.execPath, [path.join(ROOT, 'launch.js'), 'stage', '--stage', 'm5', '--run-root', runRoot,
        '--brief', brief, '--raid', 'policy-test', '--dry-run'], { cwd: ROOT, timeout: 30000, stdio: ['ignore', stdout, stderr],
        env: { ...process.env, M5_RAIDS_LEDGER: path.join(scratch, 'raids_used.jsonl'), WF_STUB: path.join(ROOT, 'tools', 'e2e_wf.js') } })
      let error
      proc.on('error', value => { error = value })
      proc.on('close', (status, signal) => resolve({ status, signal, error }))
    })
  } finally { fs.closeSync(stdout); fs.closeSync(stderr) }
  check('launch.js stage --stage m5 --dry-run exits 0', () => {
    assert.ifError(child.error)
    assert.equal(child.status, 0, fs.readFileSync(stderrFile, 'utf8').slice(-800))
  })
  check('dry run leaves the real raid ledger byte-identical', () => {
    assert.deepEqual(fs.existsSync(realLedger) ? fs.readFileSync(realLedger) : null, realBefore)
  })
  const out = path.join(runRoot, 'agent', 'wf')
  let argv = null
  check('dry run records its workflow command in RUN.md', () => {
    const line = fs.readFileSync(path.join(out, 'RUN.md'), 'utf8').match(/^Command: (.+)$/m)
    assert.ok(line, 'no "Command:" line')
    argv = words(line[1])
  })
  if (!argv) return
  const value = flag => { const i = argv.indexOf(flag); return i >= 0 ? argv[i + 1] : undefined }
  const cwd = path.join(out, 'pipeline')   // the recorded command runs from the frozen pipeline copy
  check('m5 command runs idea/wf.js on m5/pipeline.js with --profile latent_skeptic', () => {
    assert.ok(argv.some(word => /(^|\/)idea\/wf\.js$/.test(word)), argv.join(' '))
    assert.match(String(value('--script')), /(^|\/)m5\/pipeline\.js$/)
    assert.equal(value('--profile'), 'latent_skeptic')
  })
  check('m5 command uses --config m5/wf_config.json', () => {
    const config = value('--config')
    assert.match(String(config), /(^|\/)m5\/wf_config\.json$/, argv.join(' '))
    const file = path.resolve(cwd, config)
    assert.ok(fs.existsSync(file), `${file} missing`)
    const u = readJSON(file).understudy
    assert.equal(u.primary_family, 'codex')
    assert.deepEqual(u.routes.map(withoutDocs), ROUTES)
  })
  check('m5 command uses --family codex', () => {
    assert.equal(argv.filter(word => word === '--family').length, 1, argv.join(' '))
    assert.equal(value('--family'), 'codex')
  })
  check('m5 command does not pass --disable-family claude', () => {
    argv.forEach((word, i) => {
      if (word === '--disable-family') assert.notEqual(argv[i + 1], 'claude', argv.join(' '))
      assert.ok(!/^--disable-family=claude$/.test(word), argv.join(' '))
    })
  })
}

async function main() {
  try {
    configChecks()
    await launchChecks()
  } catch (error) {
    failures++
    console.log(`FAIL test harness: ${error.stack}`)
  } finally { fs.rmSync(scratch, { recursive: true, force: true }) }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : 'all checks passed')
  process.exitCode = failures ? 1 : 0
}
main()
