#!/usr/bin/env node
'use strict'

// Black-box contract tests for the sealed comparison, pipeline side up to reproduce (U57a): m5/SCHEMAS.md
// "Sealed comparison (U57, U58)" up to and including "In comparison mode reproduce runs exactly as usual for
// `A0`" (args.comparison and the design, the three control files, isolation of every agent call and its
// copy-back, comparison prompts, the harness comparison files and C/arms_seal.json, the sudo_nopasswd rule,
// profile/seal/propose/implement SKIPPED), plus "A/harness/" (harness_from). Evaluate's comparison mode (U57b)
// and scoring (U58) are out of scope. Never inspect pipeline.js, score_comparison.py, idea/wf.js or git history.
//
// The fake box follows tools/test_m5_card_pipeline.js: it really executes every command in a temporary shared
// run directory. This file is also the stub agent module (WF_STUB): it records every call (prompt, isolation
// descriptor, a listing of its view and of A/intake/ and A/harness/ at that time), snapshots the control files
// at the first call, and writes its files into the isolation view when it has one (into A/ otherwise), plus
// stray files that must not be copied back.
// Usage: node tools/test_m5_comparison_pipeline.js [case-name regex] [keep]
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const crypto = require('node:crypto')
const assert = require('node:assert/strict')
const { spawn } = require('node:child_process')

const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex')
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const rows = file => fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : []
const b64 = file => fs.existsSync(file) ? fs.readFileSync(file).toString('base64') : null
const clone = value => JSON.parse(JSON.stringify(value))
function writeFile(file, text, mode) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, text, mode ? { mode } : undefined)
}
// Recursive listing: relative path -> SHA-256 (file), 'dir' (directory, key ends in '/'), 'link' (symlink).
function listing(directory) {
  if (!fs.existsSync(directory)) return null
  const result = {}
  ;(function visit(parent) {
    for (const entry of fs.readdirSync(parent, { withFileTypes: true })) {
      const file = path.join(parent, entry.name), relative = path.relative(directory, file)
      if (entry.isSymbolicLink()) result[relative] = 'link'
      else if (entry.isDirectory()) { result[relative + '/'] = 'dir'; visit(file) }
      else if (entry.isFile()) result[relative] = sha(fs.readFileSync(file))
      else result[relative] = 'other'
    }
  })(directory)
  return result
}
function treeText(directory) {
  let text = ''
  for (const [relative, kind] of Object.entries(listing(directory) ?? {}))
    if (kind !== 'dir' && kind !== 'link' && kind !== 'other') text += fs.readFileSync(path.join(directory, relative)).toString('latin1') + '\n'
  return text
}

// ---- Hidden design values (SCHEMAS.md: the view holds no comparison, criterion, margin, threshold, reference
// value, timeout, part, seed or budget). Each is distinctive so it can be searched for.
const HIDDEN_TEXT = ['REFERENCE_PRIVATE_SENTINEL', 'PART_PRIVATE_SENTINEL', 'PART2_PRIVATE_SENTINEL']
const HIDDEN_NUMBERS = ['0.03125', '0.0078125', '1.4375', '0.0625', '271.8281', '314.1593', '918273', '564738', '31337', '4321', '1357', '0.8125']
const numberRe = number => new RegExp(`(?<![0-9.])${number.replace(/\./g, '\\.')}(?![0-9])`)
const hiddenIn = text => [...HIDDEN_TEXT.filter(word => text.includes(word)), ...HIDDEN_NUMBERS.filter(number => numberRe(number).test(text))]

// ---- Harness scripts the stub agents and the "previous run" write ------------------------------------------
const SETUP_OK = 'mkdir -p out baseline-published data\nprintf \'published\\n\' > baseline-published/pin\nprintf \'input\\n\' > data/input'
const SETUP_FAILING = 'printf \'setup failing on purpose\\n\'\nexit 7\n' + SETUP_OK
const COMMAND_OK = 'test -f baseline-published/pin\nmkdir -p out\nprintf \'command ran\\n\' >> out/command-calls.log'
const ANCHORS_OK = 'bash harness/run_command.sh\nprintf \'%s\\n\' \'{"first":100,"second":0}\' > out/anchors_measured.json'
const ANCHORS_FAILING = 'printf \'anchors failing on purpose\\n\'\nexit 7\n' + ANCHORS_OK
const STRAY = name => `printf '%s\\n' stray > out/stray-${name}\nexit 9`
const sh = body => '#!/usr/bin/env bash\nset -eu\n' + body + '\n'
const ANCHORS = [{ id: 'first', published_value: 100, tolerance: 1, quantity: 'fixture', source: 'fixture' },
  { id: 'second', published_value: 0, tolerance: 0, quantity: 'fixture', source: 'fixture' }]

// The comparison files (SCHEMAS.md "Harness prompt, comparison mode only") for a view: relative name -> text.
function comparisonFiles(view) {
  const files = {}
  for (const arm of view.arms) files[`arms/${arm.id}.sh`] = sh(`# adapter for one arm: stages the input only\nmkdir -p "$CMP_OUT"\nprintf '%s\\n' "$CMP_INPUT" > "$CMP_OUT/input.txt"`)
  const location = name => name === 'score' && view.evaluator ? 'eval/score.json' : name === 'raw' ? { glob: 'out/raw/part-*.bin' }
    : name === 'energy' ? 'log/cmd1.stdout' : `out/${name}.txt`
  files['cmp_files.json'] = JSON.stringify({ files: Object.fromEntries(view.arms.map(arm => [arm.id,
    Object.fromEntries(view.outputs.map(output => [output.name, location(output.name)]))])) }, null, 1) + '\n'
  const rules = []
  view.arms.forEach((arm, i) => {
    for (const metric of view.metrics.filter(item => item.source === 'sealed_extraction')) {
      if (metric.reduce === 'value_at_max_key') rules.push({ arm: arm.id, metric: metric.name, file: 'log/cmd1.stdout', kind: 'regex', expr: 'step=(\\d+) loss=([0-9.eE+-]+)' })
      else if (i % 2 === 0) rules.push({ arm: arm.id, metric: metric.name, file: 'out/metrics.json', kind: 'json', expr: `/${metric.name}` })
      else rules.push({ arm: arm.id, metric: metric.name, file: 'out/run.log', kind: 'regex', expr: `${metric.name}=([0-9.]+)` })
    }
  })
  files['cmp_extract.json'] = JSON.stringify({ rules }, null, 1) + '\n'
  const versions = Object.fromEntries([...view.arms.map(arm => [arm.id, { version: '1.0', executable: 'bin/solver' }]),
    ...(view.evaluator ? [['evaluator', { version: '2.0', executable: 'bin/scorer' }]] : [])])
  files['versions.sh'] = sh(`printf '%s\\n' '${JSON.stringify(versions)}'`)
  if (view.evaluator) {
    files['fetch_private.sh'] = sh('printf private > private.dat')
    files['evaluate.sh'] = sh('mkdir -p "$CMP_EVAL_OUT"\nprintf \'{"score": 1}\\n\' > "$CMP_EVAL_OUT/score.json"')
  }
  return files
}

// Symbolic-link tricks of an agent (SCHEMAS.md "Isolation of agent calls": nothing is copied from a view's intake/,
// harness/ or harness/arms/ that is not a directory, and no copy follows a symbolic link). The decoy lies outside
// the view and holds exactly the valid-looking files the agent wrote.
let decoys = 0
const decoy = (root, title) => path.join(path.dirname(root), `decoy-${title}-${process.pid}-${++decoys}`)
function linkDirectory(directory, target) {
  fs.cpSync(directory, target, { recursive: true, verbatimSymlinks: true })
  fs.rmSync(directory, { recursive: true, force: true })
  fs.symlinkSync(target, directory)
}
function linkFile(file, target) {
  fs.copyFileSync(file, target)
  fs.chmodSync(target, 0o700)
  fs.rmSync(file)
  fs.symlinkSync(target, file)
}

// ---- Stub agents ------------------------------------------------------------------------------------------
module.exports = {
  async run(options) {
    const root = process.env.M5_CMP_ROOT
    const cfg = JSON.parse(process.env.M5_CMP_CONFIG)
    const title = options.title
    const isolation = options.isolation ?? null
    const view = isolation && typeof isolation.directory === 'string' ? isolation.directory : null
    const agent = path.join(root, 'agent'), control = path.join(root, 'control')
    const receiptDir = path.join(control, 'receipts')
    const firstFile = path.join(path.dirname(root), 'first-call.json')
    if (!fs.existsSync(firstFile)) fs.writeFileSync(firstFile, JSON.stringify({ label: title,
      comparison: b64(path.join(control, 'comparison.json')), seal: b64(path.join(control, 'comparison_seal.json')),
      view: b64(path.join(agent, 'comparison_view.json')),
      receipts: fs.existsSync(receiptDir) ? fs.readdirSync(receiptDir).length : 0,
      box: rows(path.join(path.dirname(root), 'box-state.jsonl')).length }))
    const viewText = view ? treeText(view) : ''
    fs.appendFileSync(process.env.M5_CMP_CALLS, JSON.stringify({ label: title, name: options.name, prompt: options.prompt,
      isolation, cwd: options.cwd ?? null, ms: Date.now(), view: view ? listing(view) : null, viewHidden: hiddenIn(viewText),
      viewDesignPath: Boolean(cfg.designPath && viewText.includes(cfg.designPath)),
      agentIntake: listing(path.join(agent, 'intake')), agentHarness: listing(path.join(agent, 'harness')) }) + '\n')
    if (/repair/.test(title) && cfg.declineRepairs) return null
    const base = view ?? agent
    const record = (label, files) => fs.writeFileSync(path.join(path.dirname(root), `written-${label}.json`), JSON.stringify(files))
    let facts = { v: `${title} stub` }
    if (title === 'intake') {
      facts = { found: true, anchors_count: ANCHORS.length, data: 'available', licence: 'permitted', stock_environment: true, size: 'tiny' }
      const intake = {
        'benchmark.json': { identity: 'contract fixture', arms: [{ id: 'A1', source: 'https://example.org/a1', pin: 'v1', commands: [['true']] }] },
        'data.json': { availability: 'available', licences: ['MIT'], required_inputs: ['fixture'] },
        'anchors.json': ANCHORS,
        'baseline.json': { repo: 'https://example.org/fixture', pin: 'fixture-v1', build_commands: ['true'], run_commands: ['true'], published_configuration: { n: 10 } },
        'EXECUTION.json': { representative_scale: { n: 10 }, inputs: ['fixture'], outputs: ['quantity'], timing_scope: 'whole process' },
      }
      const written = {}
      for (const [name, value] of Object.entries(intake)) {
        const text = JSON.stringify(value) + '\n'
        writeFile(path.join(base, 'intake', name), text)
        written[name] = sha(Buffer.from(text))
      }
      if (view) {
        // Not regular files directly under intake/: never copied back.
        writeFile(path.join(view, 'intake', 'sub', 'extra.json'), '{"stray": true}\n')
        fs.symlinkSync('benchmark.json', path.join(view, 'intake', 'link.json'))
        if (cfg.intakeLink === 'dir') linkDirectory(path.join(view, 'intake'), decoy(root, title))
        if (cfg.intakeLink === 'file') linkFile(path.join(view, 'intake', 'anchors.json'), decoy(root, title))
      }
      record('intake', written)
    }
    if (title === 'harness') {
      const files = { 'setup.sh': sh(cfg.setupFailures ? SETUP_FAILING : SETUP_OK), 'run_anchors.sh': sh(cfg.anchorsFailures ? ANCHORS_FAILING : ANCHORS_OK),
        'run_command.sh': sh(COMMAND_OK), ...(cfg.cmpFiles ?? {}) }
      const written = {}
      for (const [name, text] of Object.entries(files)) {
        if (text === null) continue
        writeFile(path.join(base, 'harness', name), text, 0o700)
        written[name] = sha(Buffer.from(text))
      }
      if (view) {
        // Not copied back: an adapter for no arm of the design, a non-adapter under arms/, a subdirectory.
        writeFile(path.join(view, 'harness', 'arms', 'A9.sh'), sh('echo stray adapter'))
        writeFile(path.join(view, 'harness', 'arms', 'notes.txt'), 'stray notes\n')
        writeFile(path.join(view, 'harness', 'sub', 'helper.sh'), sh('echo stray helper'))
        if (cfg.harnessLink === 'dir') linkDirectory(path.join(view, 'harness'), decoy(root, title))
        if (cfg.harnessLink === 'arms') linkDirectory(path.join(view, 'harness', 'arms'), decoy(root, title))
        if (cfg.harnessLink === 'file') linkFile(path.join(view, 'harness', 'arms', 'A1.sh'), decoy(root, title))
      }
      record('harness', written)
    }
    if (title === 'harness-repair') {
      const text = sh('# repaired by harness-repair\n' + SETUP_OK)
      writeFile(path.join(base, 'harness', 'setup.sh'), text, 0o700)
      if (view && cfg.repairLink === 'dir') linkDirectory(path.join(view, 'harness'), decoy(root, title))
      if (view && cfg.repairLink === 'file') linkFile(path.join(view, 'harness', 'setup.sh'), decoy(root, title))
      if (view && cfg.repairTamper) {
        // Changes the setup repair may not make: all discarded.
        writeFile(path.join(view, 'harness', 'run_anchors.sh'), sh(STRAY('anchors')))
        writeFile(path.join(view, 'harness', 'run_command.sh'), sh(STRAY('command')))
        writeFile(path.join(view, 'harness', 'arms', 'A0.sh'), sh('echo tampered adapter'))
        writeFile(path.join(view, 'harness', 'cmp_files.json'), '{"files": {}}\n')
        writeFile(path.join(view, 'harness', 'evil.sh'), sh('echo evil'))
        writeFile(path.join(view, 'intake', 'anchors.json'), '[]\n')
      }
      record('harness-repair', { 'setup.sh': sha(Buffer.from(text)) })
    }
    if (title === 'anchors-repair') {
      const anchors = sh('# repaired by anchors-repair\n' + ANCHORS_OK), command = sh('# repaired by anchors-repair\n' + COMMAND_OK)
      writeFile(path.join(base, 'harness', 'run_anchors.sh'), anchors, 0o700)
      writeFile(path.join(base, 'harness', 'run_command.sh'), command, 0o700)
      if (view && cfg.repairTamper) {
        writeFile(path.join(view, 'harness', 'setup.sh'), sh(STRAY('setup')))
        writeFile(path.join(view, 'harness', 'arms', 'A1.sh'), sh('echo tampered adapter'))
        writeFile(path.join(view, 'harness', 'cmp_extract.json'), '{"rules": []}\n')
        writeFile(path.join(view, 'harness', 'versions.sh'), sh('echo {}'))
        writeFile(path.join(view, 'harness', 'evil2.sh'), sh('echo evil'))
      }
      record('anchors-repair', { 'run_anchors.sh': sha(Buffer.from(anchors)), 'run_command.sh': sha(Buffer.from(command)) })
    }
    return { text: JSON.stringify(facts), json: facts, jsonError: null, sessionID: 'stub',
      tokens: { input: 10, output: 5, reasoning: 0 }, cost: 0.001, tools: 0, ms: 5, errors: [], refusal: false }
  },
  async exportSession(id, file) { fs.writeFileSync(file, '{}') },
}
if (require.main !== module) return

const ROOT = path.resolve(__dirname, '..')
const STAGES = ['intake', 'reproduce', 'profile', 'seal', 'propose', 'implement', 'evaluate', 'takeaways']
const PROBE = 'comparison-pipeline-probe-50417'
const CMP_FILES = ['comparison.json', 'comparison_seal.json', 'arms_seal.json', 'comparison_scored.json']

// ---- The design ---------------------------------------------------------------------------------------------
const K = (id, extra) => ({ id, arm: 'A1', against: 'A0', measure: { metric: 'wall' }, criterion: 'non_inferiority', direction: 'lower_better',
  unit: 'per_input_all', pairing: 'unpaired', rule: 'all_pairs', confidence: null, margin: null, threshold: null, strict: null,
  reference: null, missing: 'void', given: [], parts: ['main'], ...extra })
const BASE = {
  arms: [
    { id: 'A0', what: 'published baseline program', commands: [['bin/solver', '--case', '{spec:/case}', '--out', '{out}/result.txt']], env: null },
    { id: 'A1', what: 'published alternative configuration', commands: [
      ['bin/solver', '--fast', '--case', '{spec:/case}', '--n', '{spec:/n}', '--tag', '{spec:/a~1b}', '--second', '{spec:/list/1}'],
      ['python3', '-c', 'print("{{done}}")', '{input}', '{run}']],
    env: { OMP_NUM_THREADS: '4', CASE_DIR: '{run}/cases/{input}', N_STR: 'n={spec:/n}', ['A' + 'B'.repeat(63)]: 'x' } },
  ],
  inputs: [
    { id: 'case-1', spec: { case: 'alpha', n: 10, 'a/b': 'x', list: [1, 2], extra: { deep: true }, flag: true, nil: null, only: 'z' } },
    { id: 'case_2.b', spec: { case: 'beta', n: 2.5, 'a/b': 'y', list: [3, 4.5], flag: false, nil: null } },
  ],
  outputs: [
    { name: 'energy', what: 'final energies', format: 'text_numbers', select: 'E=(\\S+)' },
    { name: 'raw', what: 'raw result bytes', format: 'bytes', select: null },
    { name: 'score', what: 'evaluator score', format: 'json_numbers', select: null },
  ],
  metrics: [
    { name: 'wall', unit: 's', what: 'invocation wall', source: 'trusted_wall', reduce: null, expect_count: null },
    { name: 'steps_per_s', unit: '1/s', what: 'reported throughput', source: 'sealed_extraction', reduce: 'max', expect_count: null },
    { name: 'final_loss', unit: '1', what: 'loss at the last step', source: 'sealed_extraction', reduce: 'value_at_max_key', expect_count: 3 },
  ],
  evaluator: { what: 'published scorer', spec: { program: 'scorer', pin: 'v1.2', private: 'held-out labels' }, timeout_s: 1357 },
  replicates: 3, warmup: 1, order_seed: 918273, timeout_s: 4321, budget_s: 31337, bootstrap_seed: 564738, bootstrap_resamples: 2000,
  comparisons: [
    K('K1', { measure: { output: 'energy', comparator: 'elementwise_abs_plus_rel_max' }, criterion: 'agreement', direction: 'two_sided',
      pairing: 'paired_replicate', margin: { abs: 0.03125, rel: 0.0078125 }, missing: 'fail', parts: ['PART_PRIVATE_SENTINEL'] }),
    K('K2', { criterion: 'ratio_at_least', unit: 'pooled_mean', pairing: 'paired_replicate', rule: 'bootstrap', confidence: 0.8125,
      threshold: 1.4375, strict: true, given: ['K1'], parts: ['speed', 'PART2_PRIVATE_SENTINEL'] }),
    K('K3', { against: 'reference', measure: { metric: 'steps_per_s' }, direction: 'higher_better', unit: 'per_input_each', margin: { abs: 0.0625 },
      reference: { source: 'REFERENCE_PRIVATE_SENTINEL run 7, median rule', values: { 'case-1': 271.8281, 'case_2.b': 314.1593 } }, missing: 'fail' }),
    K('K4', { arm: 'A0', against: 'A1', measure: { metric: 'final_loss' }, criterion: 'superiority', direction: 'two_sided', given: ['K1', 'K3'] }),
    K('K5', { measure: { output: 'raw', comparator: 'exact' }, criterion: 'agreement', direction: 'two_sided', unit: 'per_input_each', pairing: 'paired_replicate' }),
    K('K6', { measure: { output: 'score', comparator: 'elementwise_abs' }, criterion: 'agreement', direction: 'two_sided', pairing: 'paired_replicate', margin: { abs: 0 } }),
  ],
}
const design = change => { const value = clone(BASE); const out = change(value); return out === undefined ? value : out }
const cmp = (i, patch) => design(value => { Object.assign(value.comparisons[i], typeof patch === 'function' ? patch(value.comparisons[i]) : patch) })
const viewOf = value => ({ arms: value.arms, inputs: value.inputs, outputs: value.outputs, metrics: value.metrics,
  evaluator: value.evaluator === null ? null : { what: value.evaluator.what, spec: value.evaluator.spec }, replicates: value.replicates, warmup: value.warmup })
// No evaluator: the score output and its comparison go.
const NOEVAL = design(value => {
  value.evaluator = null
  value.outputs = value.outputs.filter(output => output.name !== 'score')
  value.comparisons = value.comparisons.filter(item => item.id !== 'K6')
  value.timeout_s = { A0: 600, A1: { 'case-1': 300, 'case_2.b': 450 } }
})
const REUSE = design(value => { value.budget_s = 20000 })
// Smallest design: 5 arms, one input, no output, no evaluator, no comparison, no timeout.
const MINIMAL = {
  arms: ['A0', 'A1', 'A2', 'A3', 'A4'].map(id => ({ id, what: `arm ${id}`, commands: [['bin/run', `--arm=${id}`, '{input}']], env: null })),
  inputs: [{ id: 'only', spec: null }], outputs: [],
  metrics: [{ name: 'wall', unit: 's', what: 'invocation wall', source: 'trusted_wall', reduce: null, expect_count: null }],
  evaluator: null, replicates: 1, warmup: 0, order_seed: -3, timeout_s: null, budget_s: 31337, bootstrap_seed: 0, bootstrap_resamples: 1000, comparisons: [],
}

// ---- One workflow run -------------------------------------------------------------------------------------
// spec: { comparison (args value, or function of {designFile, caseDir}), design (value or raw text; undefined =
// none written), designKind ('file'|'directory'|'missing'), git (design inside a git work tree), generated (no
// harness_from), cmpFiles (relative name -> text or null, overriding comparisonFiles), brief, sudo (true|false|
// 'absent'|other), setupFailures, anchorsFailures, repairTamper, declineRepairs, ceiling (args.run_ceiling_s),
// card, unitsCheck, unitsProbe, stub (args.stub), inside ('root'|'journal'|'design': that path inside the pipeline
// working directory), intakeLink ('dir'|'file'), harnessLink ('dir'|'arms'|'file'), repairLink ('dir'|'file') }
const scratch = fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_comparison_pipeline_'))
const pipeline = path.join(scratch, 'pipeline')
const ONLY = process.argv[2] ? new RegExp(process.argv[2]) : null
let checks = 0, failures = 0
function check(label, test) {
  if (ONLY && !ONLY.test(label)) return
  checks++
  try { test(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${String(error.message).replace(/\s*\n\s*/g, ' ').slice(0, 1500)}`) }
}
async function execute(name, spec) {
  if (ONLY && !ONLY.test(name)) return null
  const caseDir = path.join(scratch, name)
  // spec.inside: the run root, the journal directory or the design file inside the pipeline working directory.
  const root = spec.inside === 'root' ? path.join(pipeline, 'runs', name) : path.join(caseDir, 'run')
  const agent = path.join(root, 'agent'), control = path.join(root, 'control')
  const journal = spec.inside === 'journal' ? path.join(pipeline, 'journals', name) : path.join(agent, 'wf')
  const science = spec.inside === 'design' ? path.join(pipeline, 'designs', name) : path.join(caseDir, 'science')
  const designDir = path.join(science, 'plans')
  const designFile = path.join(designDir, 'design-CMPDESIGN.json')
  const source = path.join(caseDir, 'previous run', 'A', 'harness')
  const reference = path.join(caseDir, 'previous run', 'A', 'results', 'reproduce', 'out')
  const box = path.join(caseDir, 'box')
  for (const directory of [box, reference, path.join(root, 'home'), designDir]) fs.mkdirSync(directory, { recursive: true })
  if (spec.git) fs.mkdirSync(path.join(science, '.git'))
  const kind = spec.designKind ?? 'file'
  if (kind === 'file' && spec.design !== undefined) writeFile(designFile, typeof spec.design === 'string' ? spec.design : JSON.stringify(spec.design, null, 1) + '\n')
  if (kind === 'directory') fs.mkdirSync(designFile, { recursive: true })
  const designValue = spec.design && typeof spec.design === 'object' ? spec.design : null
  const cmpFiles = spec.cmpFiles !== undefined ? spec.cmpFiles : designValue && !Array.isArray(designValue) && Array.isArray(designValue.arms) ? (() => {
    try { return comparisonFiles(viewOf(designValue)) } catch { return {} }
  })() : {}
  if (!spec.generated) {
    writeFile(path.join(source, 'setup.sh'), sh(spec.setupFailures ? SETUP_FAILING : SETUP_OK), 0o700)
    writeFile(path.join(source, 'run_command.sh'), sh(COMMAND_OK), 0o700)
    writeFile(path.join(source, 'run_anchors.sh'), sh(spec.anchorsFailures ? ANCHORS_FAILING : ANCHORS_OK), 0o700)
    for (const [file, text] of Object.entries(cmpFiles)) if (text !== null) writeFile(path.join(source, file), text, 0o700)
  }
  let brief = null
  if (spec.brief) { brief = path.join(caseDir, 'briefs', 'brief-CMPBRIEF.md'); writeFile(brief, '# Comparison brief\nCompare the published arms.\n') }
  const args = { run_root: root, tag: name, stub: { evaluate: 'PASS', ...(spec.stub ?? {}) } }
  if (brief) args.brief = brief
  if (!spec.generated) args.harness_from = source
  if (spec.comparison !== undefined) args.comparison = typeof spec.comparison === 'function' ? spec.comparison({ designFile, caseDir }) : spec.comparison
  if (spec.ceiling !== undefined) args.run_ceiling_s = spec.ceiling
  if (spec.unitsCheck) args.units_check = { reference }
  if (spec.unitsProbe) args.units_probe = { reference }
  if (spec.card) {
    const result = path.join(caseDir, 'tree', 'result.json')
    writeFile(result, JSON.stringify({ calibration: [{ key: 'R1:x:W1', state: 'calibration_required', required: [{ id: 'steps_per_h', basis: 'GUESS', value: 3 }] }] }) + '\n')
    args.card = { result, key: 'R1:x:W1' }
  }
  writeFile(path.join(root, 'control/args.json'), JSON.stringify(args, null, 1) + '\n')

  const callsFile = path.join(caseDir, 'calls.jsonl')
  const replaceProbe = path.join(caseDir, 'replace-probe.js')
  const originalProbe = fs.readFileSync(path.join(ROOT, 'm5/box_probe.sh'), 'utf8')
  const sudo = spec.sudo === undefined ? true : spec.sudo
  const probeJSON = JSON.stringify({ kernel: PROBE, nvcc: [], cmake: null, ...(sudo === 'absent' ? {} : { sudo_nopasswd: sudo }) })
  const fakeProbe = `#!/usr/bin/env bash\nset -eu\nmkdir -p out\nprintf '%s\\n' '${probeJSON}' > out/probe.json\n`
  fs.writeFileSync(replaceProbe, `
const fs = require('node:fs'), path = require('node:path')
// The job bin/box just started may remove entries meanwhile; vanished ones are skipped.
const boxWalk = require(${JSON.stringify(path.join(ROOT, 'tools/m5_box_walk.js'))})
function visit(directory) {
  for (const entry of boxWalk.entries(directory)) {
    const file = path.join(directory, entry.name)
    if (entry.isDirectory()) visit(file)
    else if (entry.isFile() && entry.name.endsWith('.sh') && boxWalk.text(file) === ${JSON.stringify(originalProbe)}) fs.writeFileSync(file, ${JSON.stringify(fakeProbe)})
  }
}
visit(process.env.BOX_ROOT)
`)
  writeFile(path.join(caseDir, 'box-bin/nvidia-smi'), sh('exit 1'), 0o700)
  // Before each box command: which control files exist, and whether harness files are already on the box.
  const state = 'c="$BOX_ROOT/../run/control"\na="$BOX_ROOT/../run/agent"\nh=0\nm=0\n' +
    'for f in "$BOX_ROOT"/m5-*/harness/setup.sh; do [[ ! -f $f ]] || h=1; done\nfor f in "$BOX_ROOT"/m5-*/harness/cmp_files.json; do [[ ! -f $f ]] || m=1; done\n' +
    'b() { [[ -f $1 ]] && echo true || echo false; }\n' +
    'printf \'{"comparison":%s,"seal":%s,"view":%s,"arms_seal":%s,"harness":%s,"cmp_on_box":%s}\\n\' "$(b "$c/comparison.json")" "$(b "$c/comparison_seal.json")" ' +
    '"$(b "$a/comparison_view.json")" "$(b "$c/arms_seal.json")" "$([[ $h == 1 ]] && echo true || echo false)" "$([[ $m == 1 ]] && echo true || echo false)" >> "$BOX_ROOT/../box-state.jsonl"\n'
  writeFile(path.join(caseDir, 'bin/box'), sh('command=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\nexport PATH="$BOX_ROOT/../box-bin:$PATH"\ncd -- "$BOX_ROOT"\n' + state +
    'bash -c "$command"\n"$M5_TEST_NODE" "$M5_REPLACE_PROBE"\nif [[ $command == *timeout* ]]; then\n  for ((end=SECONDS+1800; SECONDS<end; )); do\n    pending=false\n    for file in "$BOX_ROOT"/m5-*/*.sh; do\n      [[ -f $file ]] || continue\n      [[ -f ${file%.sh}.rc ]] || pending=true\n    done\n    [[ $pending == true ]] || break\n    sleep 0.01\n  done\nfi\nexit 0'), 0o700)
  writeFile(path.join(caseDir, 'bin/fetch'), sh('source=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\ncd -- "$BOX_ROOT"\nexec cp -r -- "$source" "$2"'), 0o700)
  const designAbs = typeof args.comparison?.design === 'string' && args.comparison.design ? path.resolve(pipeline, args.comparison.design) : null
  const stubConfig = { setupFailures: spec.setupFailures ?? 0, anchorsFailures: spec.anchorsFailures ?? 0, repairTamper: Boolean(spec.repairTamper),
    declineRepairs: Boolean(spec.declineRepairs), cmpFiles: spec.generated && args.comparison ? cmpFiles : null, designPath: designAbs,
    intakeLink: spec.intakeLink ?? null, harnessLink: spec.harnessLink ?? null, repairLink: spec.repairLink ?? null }
  const stderrFile = path.join(caseDir, 'stderr.log')
  const stdout = fs.openSync(path.join(caseDir, 'stdout.log'), 'w'), stderr = fs.openSync(stderrFile, 'w')
  let child
  try {
    child = await new Promise(resolve => {
      const proc = spawn(process.execPath, [path.join(pipeline, 'idea/wf.js'), '--script', path.join(pipeline, 'm5/pipeline.js'),
        '--args', path.join(root, 'control/args.json'), '--out', journal, '--disable-family', 'claude'], {
        cwd: pipeline, timeout: 1800000, killSignal: 'SIGKILL', stdio: ['ignore', stdout, stderr],
        env: { ...process.env, HOME: path.join(root, 'home'), M5_RAIDS_LEDGER: path.join(scratch, 'raids.jsonl'),
          WF_STUB: __filename, M5_CMP_ROOT: root, M5_CMP_CONFIG: JSON.stringify(stubConfig), M5_CMP_CALLS: callsFile,
          M5_TEST_NODE: process.execPath, M5_REPLACE_PROBE: replaceProbe,
          BOX_ROOT: box, BOX: path.join(caseDir, 'bin/box'), FETCH: path.join(caseDir, 'bin/fetch') },
      })
      let error
      proc.on('error', value => { error = value })
      proc.on('close', (status, signal) => resolve({ status, signal, error }))
    })
  } finally { fs.closeSync(stdout); fs.closeSync(stderr) }
  check(`${name}: workflow completes`, () => {
    assert.ifError(child.error)
    assert.equal(child.status, 0, `signal ${child.signal}; ${fs.readFileSync(stderrFile, 'utf8').slice(-1000)}`)
  })
  const records = rows(path.join(root, 'operator/signatures.jsonl')).map(row => ({ ...row.signature, facts: row.facts }))
  const receiptDir = path.join(control, 'receipts')
  const receipts = fs.existsSync(receiptDir) ? fs.readdirSync(receiptDir).sort().filter(file => file.endsWith('.json'))
    .map(file => ({ operation: file.slice(5, -5), ...read(path.join(receiptDir, file)) })) : []
  const firstFile = path.join(caseDir, 'first-call.json')
  const written = label => { const file = path.join(caseDir, `written-${label}.json`); return fs.existsSync(file) ? read(file) : null }
  const remote = fs.readdirSync(box).filter(entry => entry.startsWith('m5-')).map(entry => path.join(box, entry, 'harness')).find(dir => fs.existsSync(dir)) ?? null
  return { name, spec, caseDir, root, agent, control, source, designFile, designAbs, designDir, science, brief, records, receipts, cmpFiles,
    calls: rows(callsFile), boxLog: rows(path.join(caseDir, 'box-state.jsonl')), first: fs.existsSync(firstFile) ? read(firstFile) : null,
    written, remote, stage: label => records.find(row => row.stage === label) }
}

// ---- Shared checks ----------------------------------------------------------------------------------------
function statuses(r, wanted, label = null) {
  check(`${r.name}: stage statuses ${label ?? wanted.map(([stage, status]) => `${stage}=${status}`).join(' ')}`, () => {
    const stages = wanted.map(([stage]) => stage)
    const got = r.records.filter(row => stages.includes(row.stage)).map(row => [row.stage, row.status])
    assert.deepEqual(got, wanted, JSON.stringify({ intake: r.stage('intake')?.error_class, reproduce: r.stage('reproduce')?.error_class }))
  })
}
const failedAt = stage => STAGES.map((label, i) => [label, label === stage ? 'FAIL' : i < STAGES.indexOf(stage) ? 'PASS' : label === 'takeaways' ? 'PASS' : 'SKIPPED'])
// Comparison mode with reproduce passed: profile, seal, propose and implement SKIPPED (evaluate is U57b).
const CMP_PASS = [['intake', 'PASS'], ['reproduce', 'PASS'], ['profile', 'SKIPPED'], ['seal', 'SKIPPED'], ['propose', 'SKIPPED'], ['implement', 'SKIPPED'], ['takeaways', 'PASS']]
function errorClass(r, stage, value) {
  check(`${r.name}: ${stage} error_class ${value}, exit_code 2`, () => {
    const signature = r.stage(stage)
    assert.equal(signature?.error_class, value)
    assert.equal(signature.exit_code, 2)
  })
}
// Invalid args.comparison or design: intake fails with parse before any agent call (and any box command).
function intakeParse(r) {
  if (!r) return
  statuses(r, failedAt('intake'))
  errorClass(r, 'intake', 'parse')
  check(`${r.name}: no agent call and no box command`, () => {
    assert.deepEqual(r.calls.map(call => call.label), [], 'agent call')
    assert.deepEqual(r.receipts.map(receipt => receipt.operation), [], 'box receipt')
    assert.deepEqual(r.boxLog, [], 'box command')
  })
}
// Harness comparison files missing or invalid: reproduce fails with parse before the harness upload.
function harnessParse(r, generated = false) {
  if (!r) return
  statuses(r, failedAt('reproduce'))
  errorClass(r, 'reproduce', 'parse')
  check(`${r.name}: the box probe only; no harness upload, setup or anchors; no repair`, () => {
    assert.deepEqual(r.receipts.map(receipt => receipt.operation), ['upload', 'probe'])
    assert.ok(r.boxLog.every(entry => !entry.harness && !entry.cmp_on_box), 'a harness file reached the box')
    assert.deepEqual(r.calls.map(call => call.label), generated ? ['intake', 'harness'] : ['intake'])
  })
  check(`${r.name}: no C/arms_seal.json`, () => assert.equal(fs.existsSync(path.join(r.control, 'arms_seal.json')), false))
}
// The three control files, exactly, before any agent call or box command.
function controlFileChecks(r, value, sourceFile = r.designFile) {
  const cmpFile = path.join(r.control, 'comparison.json'), sealFile = path.join(r.control, 'comparison_seal.json')
  const viewFile = path.join(r.agent, 'comparison_view.json')
  check(`${r.name}: C/comparison.json exactly {source, source_sha256, design}`, () => {
    const record = read(cmpFile)
    assert.deepEqual(Object.keys(record).sort(), ['design', 'source', 'source_sha256'])
    assert.equal(record.source, sourceFile, 'source is not the absolute design path')
    assert.equal(record.source_sha256, sha(fs.readFileSync(sourceFile)))
    assert.deepEqual(record.design, value)
  })
  check(`${r.name}: C/comparison_seal.json exactly {comparison_sha256, sealed_utc}`, () => {
    const seal = read(sealFile)
    assert.deepEqual(Object.keys(seal).sort(), ['comparison_sha256', 'sealed_utc'])
    assert.equal(seal.comparison_sha256, sha(fs.readFileSync(cmpFile)))
    assert.match(seal.sealed_utc, /^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?(Z|\+00:00)$/)
  })
  check(`${r.name}: A/comparison_view.json exactly {arms, inputs, outputs, metrics, evaluator, replicates, warmup} from the design`, () => {
    const view = read(viewFile)
    assert.deepEqual(Object.keys(view).sort(), ['arms', 'evaluator', 'inputs', 'metrics', 'outputs', 'replicates', 'warmup'])
    assert.deepEqual(view, viewOf(value))
  })
  check(`${r.name}: the view holds no comparison, criterion, margin, threshold, reference value, timeout, part, seed or budget`, () => {
    const text = fs.readFileSync(viewFile, 'utf8')
    assert.deepEqual(hiddenIn(text), [])
    for (const key of ['comparisons', 'criterion', 'margin', 'threshold', 'reference', 'timeout_s', 'parts', 'order_seed', 'bootstrap_seed', 'budget_s', 'bootstrap_resamples'])
      assert.ok(!text.includes(`"${key}"`), `key ${key} in the view`)
  })
  check(`${r.name}: the three files exist, final, at the first agent call, before any box command`, () => {
    assert.ok(r.first, 'no agent call')
    assert.deepEqual([r.first.comparison, r.first.seal, r.first.view], [b64(cmpFile), b64(sealFile), b64(viewFile)])
    assert.equal(r.first.receipts, 0, 'a box command ran before the first agent call')
    assert.equal(r.first.box, 0, 'a box command ran before the first agent call')
    assert.ok(r.boxLog.length > 0, 'no box command')
    assert.deepEqual([r.boxLog[0].comparison, r.boxLog[0].seal, r.boxLog[0].view], [true, true, true])
  })
  check(`${r.name}: written in order comparison.json, comparison_seal.json, comparison_view.json`, () => {
    const times = [cmpFile, sealFile, viewFile].map(file => fs.statSync(file).mtimeMs)
    assert.ok(times[0] <= times[1] && times[1] <= times[2], `mtimes ${times}`)
  })
}
// Isolation of every agent call: descriptor, view contents at the call, views removed afterwards.
const strip = (listingValue, prefix) => Object.fromEntries(Object.entries(listingValue ?? {}).map(([key, value]) => [prefix + key, value]))
function isolationChecks(r, { journal = path.join(r.agent, 'wf'), gitTop = null } = {}) {
  const viewSha = sha(fs.readFileSync(path.join(r.agent, 'comparison_view.json')))
  const hiddenWanted = [r.root, journal, path.dirname(r.designAbs), ...(gitTop ? [gitTop] : [])]
  check(`${r.name}: every agent call is dispatched with isolation (fresh view under the temporary directory, box_access false)`, () => {
    assert.ok(r.calls.length > 0, 'no agent call')
    const seen = new Set()
    for (const call of r.calls) {
      const iso = call.isolation
      assert.ok(iso && typeof iso === 'object', `${call.label}: no isolation`)
      assert.equal(iso.box_access, false, `${call.label}: box_access`)
      assert.ok(typeof iso.directory === 'string' && path.isAbsolute(iso.directory), `${call.label}: directory`)
      const tmp = path.resolve(os.tmpdir())
      assert.ok(path.resolve(iso.directory).startsWith(tmp + path.sep), `${call.label}: view ${iso.directory} not under ${tmp}`)
      for (const hidden of hiddenWanted) assert.ok(!(path.resolve(iso.directory) + path.sep).startsWith(path.resolve(hidden) + path.sep), `${call.label}: view inside hidden ${hidden}`)
      assert.ok(!seen.has(iso.directory), `${call.label}: view ${iso.directory} reused`)
      seen.add(iso.directory)
    }
  })
  check(`${r.name}: isolation hidden holds the run root, the journal directory, the design's folder${gitTop ? ' and its git work tree' : ''}`, () => {
    for (const call of r.calls) {
      const hidden = (call.isolation?.hidden ?? []).map(entry => path.resolve(entry))
      for (const wanted of hiddenWanted) assert.ok(hidden.includes(path.resolve(wanted)), `${call.label}: hidden ${JSON.stringify(hidden)} lacks ${wanted}`)
    }
  })
  for (const call of r.calls) check(`${r.name}: ${call.label} view holds exactly what the contract lists`, () => {
    assert.ok(call.view, 'no view at the call')
    const got = Object.fromEntries(Object.entries(call.view).filter(([key]) => !key.startsWith('.')))
    let want
    if (call.label === 'intake') {
      want = { 'comparison_view.json': viewSha, 'intake/': 'dir' }
      if (r.brief) Object.assign(want, { 'brief/': 'dir', [`brief/${path.basename(r.brief)}`]: sha(fs.readFileSync(r.brief)) })
    } else if (call.label === 'harness') {
      want = { 'comparison_view.json': viewSha, 'intake/': 'dir', ...strip(call.agentIntake, 'intake/'), 'harness/': 'dir' }
    } else {
      want = { 'comparison_view.json': viewSha, 'intake/': 'dir', ...strip(call.agentIntake, 'intake/'), 'harness/': 'dir', ...strip(call.agentHarness, 'harness/') }
    }
    assert.deepEqual(got, want)
    assert.deepEqual(call.viewHidden, [], 'hidden design values in the view')
    assert.equal(call.viewDesignPath, false, 'the design path appears in a view file')
  })
  check(`${r.name}: views are removed after the stage`, () => {
    for (const call of r.calls) assert.equal(fs.existsSync(call.isolation?.directory ?? '/nonexistent-view'), false, `${call.label}: ${call.isolation?.directory} left`)
  })
}
const count = (text, needle) => needle ? text.split(needle).length - 1 : 0
// Comparison prompts: name the view (and its paths) and never C/, the control files or the design path.
function promptChecks(r, plain) {
  for (const call of r.calls) check(`${r.name}: ${call.label} prompt names the view and never the control folder, the design path or a hidden value`, () => {
    const prompt = call.prompt
    const view = call.isolation?.directory
    assert.ok(view && prompt.includes(view), 'prompt does not name its view')
    assert.match(prompt, /comparison_view\.json/)
    assert.ok(!prompt.includes(path.join(r.agent, 'comparison_view.json')), 'prompt names A/comparison_view.json instead of the view copy')
    assert.deepEqual(hiddenIn(prompt), [])
    assert.ok(!prompt.includes(r.designAbs) && !prompt.includes(path.dirname(r.designAbs)) && !prompt.includes('CMPDESIGN'), 'prompt names the design path')
    for (const file of CMP_FILES) assert.ok(!new RegExp(`(^|[^_a-z])${file.replace('.', '\\.')}`).test(prompt), `prompt names ${file}`)
    for (const dir of ['intake', 'harness']) assert.ok(!prompt.includes(path.join(r.agent, dir)), `prompt names A/${dir}/ instead of the view's ${dir}/`)
    // The existing "agents never read control/" wording may stay; comparison mode adds no other mention of C/.
    const base = plain?.calls.find(other => other.label === call.label)
    assert.ok(base, `no ${call.label} prompt without args.comparison to compare with`)
    assert.ok(count(prompt, 'control/') <= count(base.prompt, 'control/'), `control/ named ${count(prompt, 'control/')} times (without args.comparison: ${count(base.prompt, 'control/')})`)
    assert.ok(count(prompt, r.control) <= count(base.prompt, plain.control), 'comparison mode adds a mention of the control directory path')
    if (call.label !== 'intake') assert.ok(prompt.includes(PROBE), 'the probe is not in the prompt')
  })
}
function intakePromptChecks(r, evaluator) {
  const call = r.calls.find(row => row.label === 'intake')
  check(`${r.name}: intake prompt: compare the view's arms, A0 as usual, benchmark.json arms, data.json${evaluator ? ', the evaluator and its private data' : ''}`, () => {
    assert.ok(call, 'no intake call')
    assert.match(call.prompt, /\bA0\b/)
    assert.match(call.prompt, /\barms\b/)
    assert.match(call.prompt, /benchmark\.json/)
    assert.match(call.prompt, /data\.json/)
    // The evaluator's private data exist only when the view has an evaluator.
    if (evaluator) { assert.match(call.prompt, /evaluator/); assert.match(call.prompt, /private/i) }
    const view = call.isolation?.directory
    if (r.brief) {
      assert.ok(view && call.prompt.includes(path.join(view, 'brief', path.basename(r.brief))), 'prompt does not name the brief copy in the view')
      assert.ok(!call.prompt.includes(path.dirname(r.brief)), 'prompt names the original brief path')
    }
  })
}
function harnessPromptChecks(r, evaluator) {
  const call = r.calls.find(row => row.label === 'harness')
  check(`${r.name}: harness prompt asks for adapters, cmp_files.json, cmp_extract.json, versions.sh${evaluator ? ', fetch_private.sh, evaluate.sh' : ''}`, () => {
    assert.ok(call, 'no harness call')
    for (const needle of ['arms/', 'cmp_files.json', 'cmp_extract.json', 'versions.sh', 'CMP_INPUT', 'CMP_OUT', 'setup.sh'])
      assert.ok(call.prompt.includes(needle), `harness prompt lacks ${needle}`)
    if (evaluator) for (const needle of ['fetch_private.sh', 'evaluate.sh', 'CMP_ARM_OUT', 'CMP_EVAL_OUT', 'CMP_PRIVATE'])
      assert.ok(call.prompt.includes(needle), `harness prompt lacks ${needle}`)
  })
}
const harnessNames = files => Object.keys(files).filter(name => files[name] !== null)
// C/arms_seal.json and the upload of the comparison files.
function armsSealChecks(r, files) {
  const names = harnessNames(files)
  check(`${r.name}: C/arms_seal.json exactly {files, sealed_utc}, SHA-256 of each comparison file in A/harness/`, () => {
    const seal = read(path.join(r.control, 'arms_seal.json'))
    assert.deepEqual(Object.keys(seal).sort(), ['files', 'sealed_utc'])
    assert.ok(Number.isFinite(Date.parse(seal.sealed_utc)), 'sealed_utc')
    assert.deepEqual(Object.keys(seal.files).sort(), [...names].sort())
    for (const name of names) {
      assert.equal(seal.files[name], sha(Buffer.from(files[name])), `${name}: sealed hash is not the written file's`)
      assert.equal(seal.files[name], sha(fs.readFileSync(path.join(r.agent, 'harness', name))), `${name}: A/harness copy differs from the seal (a repair changed it?)`)
    }
  })
  check(`${r.name}: the arms seal exists before the harness upload; the comparison files upload with the harness`, () => {
    const at = r.boxLog.findIndex(entry => entry.harness || entry.cmp_on_box)
    assert.ok(at > 0, `no harness on the box: ${JSON.stringify(r.boxLog)}`)
    assert.equal(r.boxLog[at - 1].arms_seal, true, 'the command that uploaded the harness ran before the arms seal')
    assert.equal(r.boxLog[at].harness && r.boxLog[at].cmp_on_box, true, 'the comparison files did not upload with the harness scripts')
    assert.ok(r.remote, 'no remote harness directory')
    for (const name of names) assert.ok(fs.readFileSync(path.join(r.remote, name)).equals(Buffer.from(files[name])), `${name} on the box differs`)
  })
}
const RECEIPTS_PASS = ['upload', 'probe', 'upload', 'setup', 'anchors', 'reproduce-freeze']

async function inParallel(jobs, width = 6) {
  const results = new Array(jobs.length)
  let next = 0
  await Promise.all(Array.from({ length: width }, async () => {
    while (next < jobs.length) { const i = next++; results[i] = await jobs[i]() }
  }))
  return results
}

async function main() {
  try {
    for (const directory of ['m5', 'idea', 'measure']) fs.cpSync(path.join(ROOT, directory), path.join(pipeline, directory), {
      recursive: true, filter: source => !['experiments', 'raids_used.jsonl'].includes(path.basename(source)),
    })
    const comparison = ({ designFile }) => ({ design: designFile })

    // 1. Invalid args.comparison or design: intake fails with parse before any agent call.
    const env = (value) => design(d => { d.arms[1].env = value })
    const cmd = (value) => design(d => { d.arms[1].commands[0][2] = value })
    const arm1 = patch => design(d => { Object.assign(d.arms[1], patch) })
    const del = (object, key) => { delete object[key]; return object }
    const thirteen = design(d => { d.comparisons = Array.from({ length: 13 }, (_, i) => ({ ...clone(d.comparisons[4]), id: `K${i + 1}` })) })
    const invalid = [
      // args.comparison itself
      ['args-string', { comparison: ({ designFile }) => designFile, design: BASE }],
      ['args-array', { comparison: ({ designFile }) => [designFile], design: BASE }],
      ['args-null', { comparison: null, design: BASE }],
      ['args-empty-object', { comparison: {}, design: BASE }],
      ['args-empty-design', { comparison: { design: '' }, design: BASE }],
      ['args-design-number', { comparison: { design: 7 }, design: BASE }],
      ['args-extra-key', { comparison: ({ designFile }) => ({ design: designFile, note: 'x' }), design: BASE }],
      ['design-missing', { comparison, designKind: 'missing' }],
      ['design-directory', { comparison, designKind: 'directory' }],
      ['design-not-json', { comparison, design: '{"arms": [' }],
      ['design-empty-file', { comparison, design: '' }],
      ['with-card', { comparison, design: BASE, card: true }],
      ['with-units-check', { comparison, design: BASE, unitsCheck: true }],
      ['with-units-probe', { comparison, design: BASE, unitsProbe: true }],
      // top level
      ['top-array', { design: [BASE] }],
      ['top-missing-warmup', { design: design(d => del(d, 'warmup')) }],
      ['top-missing-comparisons', { design: design(d => del(d, 'comparisons')) }],
      ['top-extra-key', { design: design(d => { d.notes = 'x' }) }],
      // arms
      ['arms-one', { design: design(d => { d.arms = [d.arms[0]]; d.comparisons = [] }) }],
      ['arms-six', { design: design(d => { d.arms = ['A0', 'A1', 'A2', 'A3', 'A4', 'A5'].map((id, i) => ({ ...clone(d.arms[i % 2]), id })) }) }],
      ['arms-order', { design: design(d => { d.arms[0].id = 'A1'; d.arms[1].id = 'A0' }) }],
      ['arms-id-b0', { design: design(d => { d.arms[1].id = 'B1' }) }],
      ['arms-id-gap', { design: design(d => { d.arms[1].id = 'A2' }) }],
      ['arm-extra-key', { design: arm1({ note: 'x' }) }],
      ['arm-missing-env', { design: design(d => { del(d.arms[1], 'env') }) }],
      ['arm-what-empty', { design: arm1({ what: '' }) }],
      ['arm-what-number', { design: arm1({ what: 3 }) }],
      ['arm-commands-empty', { design: arm1({ commands: [] }) }],
      ['arm-commands-nine', { design: arm1({ commands: Array.from({ length: 9 }, () => ['true']) }) }],
      ['arm-command-empty', { design: arm1({ commands: [[]] }) }],
      ['arm-command-empty-string', { design: arm1({ commands: [['bin/solver', '']] }) }],
      ['arm-command-number', { design: arm1({ commands: [['bin/solver', 3]] }) }],
      ['arm-command-string', { design: arm1({ commands: ['bin/solver --fast'] }) }],
      ['env-array', { design: env([['A', 'b']]) }],
      ['env-lowercase', { design: env({ omp_threads: '4' }) }],
      ['env-cmp-prefix', { design: env({ CMP_INPUT: 'x' }) }],
      ['env-leading-digit', { design: env({ '1X': 'x' }) }],
      ['env-too-long', { design: env({ ['A' + 'B'.repeat(64)]: 'x' }) }],
      ['env-value-number', { design: env({ OMP_NUM_THREADS: 4 }) }],
      ['env-value-null', { design: env({ OMP_NUM_THREADS: null }) }],
      // placeholders
      ['ph-unknown-name', { design: cmd('{inputs}') }],
      ['ph-spaced-name', { design: cmd('{ input }') }],
      ['ph-lone-open', { design: cmd('a{b') }],
      ['ph-lone-close', { design: cmd('a}b') }],
      ['ph-unterminated', { design: cmd('{input') }],
      ['ph-triple-close', { design: cmd('x}}}') }],
      ['ph-spec-missing', { design: cmd('{spec:/missing}') }],
      ['ph-spec-object', { design: cmd('{spec:/extra}') }],
      ['ph-spec-one-input-only', { design: cmd('{spec:/only}') }],
      ['ph-spec-boolean', { design: cmd('{spec:/flag}') }],
      ['ph-spec-null', { design: cmd('{spec:/nil}') }],
      ['ph-spec-array', { design: cmd('{spec:/list}') }],
      ['ph-spec-no-slash', { design: cmd('{spec:case}') }],
      ['ph-spec-bad-escape', { design: cmd('{spec:/a~2b}') }],
      ['ph-spec-index-out-of-range', { design: cmd('{spec:/list/2}') }],
      ['ph-env-value', { design: env({ CASE_DIR: '{bad}' }) }],
      ['ph-env-lone-brace', { design: env({ CASE_DIR: '{run' }) }],
      // inputs
      ['inputs-none', { design: design(d => { d.inputs = []; for (const c of d.comparisons) if (c.reference) c.reference.values = {} }) }],
      ['inputs-eleven', { design: design(d => { d.inputs = Array.from({ length: 11 }, (_, i) => ({ id: `c${i}`, spec: { case: 'a', n: 1, 'a/b': 'x', list: [1, 2] } })); d.comparisons = d.comparisons.filter(c => !c.reference).map(c => ({ ...c, given: c.given.filter(id => id !== 'K3') })) }) }],
      ['input-duplicate-id', { design: design(d => { d.inputs[1].id = 'case-1' }) }],
      ['input-id-leading-dash', { design: design(d => { d.inputs[1].id = '-case' }) }],
      ['input-id-space', { design: design(d => { d.inputs[1].id = 'case 2' }) }],
      ['input-id-too-long', { design: design(d => { d.inputs[1].id = 'c'.repeat(65) }) }],
      ['input-extra-key', { design: design(d => { d.inputs[1].note = 'x' }) }],
      ['input-missing-spec', { design: design(d => { del(d.inputs[1], 'spec') }) }],
      // outputs
      ['outputs-eleven', { design: design(d => { for (let i = 0; i < 8; i++) d.outputs.push({ name: `o${i}`, what: 'x', format: 'bytes', select: null }) }) }],
      ['output-duplicate-name', { design: design(d => { d.outputs[1].name = 'energy' }) }],
      ['output-name-uppercase', { design: design(d => { d.outputs.push({ name: 'Energy2', what: 'x', format: 'bytes', select: null }) }) }],
      ['output-name-too-long', { design: design(d => { d.outputs.push({ name: 'o' + 'x'.repeat(31), what: 'x', format: 'bytes', select: null }) }) }],
      ['output-what-empty', { design: design(d => { d.outputs[0].what = '' }) }],
      ['output-format-csv', { design: design(d => { d.outputs[1].format = 'csv' }) }],
      ['output-select-json', { design: design(d => { d.outputs[2].select = '(\\d+)' }) }],
      ['output-select-no-group', { design: design(d => { d.outputs[0].select = 'E=\\S+' }) }],
      ['output-select-noncapturing', { design: design(d => { d.outputs[0].select = 'E=(?:\\S+)' }) }],
      ['output-select-bad-regex', { design: design(d => { d.outputs[0].select = 'E=(\\S+' }) }],
      ['output-extra-key', { design: design(d => { d.outputs[0].note = 'x' }) }],
      // metrics
      ['metrics-none', { design: design(d => { d.metrics = []; d.comparisons = d.comparisons.filter(c => c.measure.output !== undefined).map(c => ({ ...c, given: c.given.filter(id => id === 'K1') })) }) }],
      ['metrics-eleven', { design: design(d => { for (let i = 0; i < 8; i++) d.metrics.push({ name: `m${i}`, unit: 's', what: 'x', source: 'trusted_wall', reduce: null, expect_count: null }) }) }],
      ['metric-duplicate-name', { design: design(d => { d.metrics[1].name = 'wall' }) }],
      ['metric-name-bad', { design: design(d => { d.metrics.push({ name: '9lives', unit: 's', what: 'x', source: 'trusted_wall', reduce: null, expect_count: null }) }) }],
      ['metric-unit-empty', { design: design(d => { d.metrics[0].unit = '' }) }],
      ['metric-source-other', { design: design(d => { d.metrics[0].source = 'agent_reported' }) }],
      ['metric-wall-reduce', { design: design(d => { d.metrics[0].reduce = 'max' }) }],
      ['metric-wall-expect', { design: design(d => { d.metrics[0].expect_count = 1 }) }],
      ['metric-extraction-reduce-null', { design: design(d => { d.metrics[1].reduce = null }) }],
      ['metric-extraction-reduce-min', { design: design(d => { d.metrics[1].reduce = 'min' }) }],
      ['metric-expect-zero', { design: design(d => { d.metrics[1].expect_count = 0 }) }],
      ['metric-expect-fraction', { design: design(d => { d.metrics[1].expect_count = 1.5 }) }],
      ['metric-extra-key', { design: design(d => { d.metrics[0].note = 'x' }) }],
      // evaluator
      ['evaluator-string', { design: design(d => { d.evaluator = 'scorer' }) }],
      ['evaluator-extra-key', { design: design(d => { d.evaluator.note = 'x' }) }],
      ['evaluator-missing-timeout', { design: design(d => { del(d.evaluator, 'timeout_s') }) }],
      ['evaluator-what-empty', { design: design(d => { d.evaluator.what = '' }) }],
      ['evaluator-timeout-zero', { design: design(d => { d.evaluator.timeout_s = 0 }) }],
      ['evaluator-timeout-fraction', { design: design(d => { d.evaluator.timeout_s = 1.5 }) }],
      // integers
      ['replicates-zero', { design: design(d => { d.replicates = 0 }) }],
      ['replicates-31', { design: design(d => { d.replicates = 31 }) }],
      ['replicates-fraction', { design: design(d => { d.replicates = 2.5 }) }],
      ['replicates-string', { design: design(d => { d.replicates = '3' }) }],
      ['warmup-negative', { design: design(d => { d.warmup = -1 }) }],
      ['warmup-four', { design: design(d => { d.warmup = 4 }) }],
      ['order-seed-fraction', { design: design(d => { d.order_seed = 1.5 }) }],
      ['order-seed-string', { design: design(d => { d.order_seed = '7' }) }],
      ['bootstrap-seed-null', { design: design(d => { d.bootstrap_seed = null }) }],
      ['bootstrap-seed-boolean', { design: design(d => { d.bootstrap_seed = true }) }],
      ['resamples-999', { design: design(d => { d.bootstrap_resamples = 999 }) }],
      ['resamples-1000001', { design: design(d => { d.bootstrap_resamples = 1000001 }) }],
      ['budget-zero', { design: design(d => { d.budget_s = 0 }) }],
      ['budget-negative', { design: design(d => { d.budget_s = -5 }) }],
      ['budget-fraction', { design: design(d => { d.budget_s = 1.5 }) }],
      ['budget-null', { design: design(d => { d.budget_s = null }) }],
      ['budget-equals-ceiling', { design: BASE, ceiling: BASE.budget_s }],
      ['budget-above-ceiling', { design: BASE, ceiling: BASE.budget_s - 1 }],
      // timeout_s forms
      ['timeout-zero', { design: design(d => { d.timeout_s = 0 }) }],
      ['timeout-negative', { design: design(d => { d.timeout_s = -1 }) }],
      ['timeout-fraction', { design: design(d => { d.timeout_s = 2.5 }) }],
      ['timeout-string', { design: design(d => { d.timeout_s = '60' }) }],
      ['timeout-boolean', { design: design(d => { d.timeout_s = true }) }],
      ['timeout-array', { design: design(d => { d.timeout_s = [60, 60] }) }],
      ['timeout-missing-arm', { design: design(d => { d.timeout_s = { A0: 60 } }) }],
      ['timeout-extra-arm', { design: design(d => { d.timeout_s = { A0: 60, A1: 60, A2: 60 } }) }],
      ['timeout-arm-zero', { design: design(d => { d.timeout_s = { A0: 0, A1: 60 } }) }],
      ['timeout-arm-null', { design: design(d => { d.timeout_s = { A0: null, A1: 60 } }) }],
      ['timeout-missing-input', { design: design(d => { d.timeout_s = { A0: 60, A1: { 'case-1': 5 } } }) }],
      ['timeout-extra-input', { design: design(d => { d.timeout_s = { A0: 60, A1: { 'case-1': 5, 'case_2.b': 5, other: 5 } } }) }],
      ['timeout-input-zero', { design: design(d => { d.timeout_s = { A0: 60, A1: { 'case-1': 0, 'case_2.b': 5 } } }) }],
      ['timeout-input-fraction', { design: design(d => { d.timeout_s = { A0: 60, A1: { 'case-1': 0.5, 'case_2.b': 5 } } }) }],
      // comparisons: list and identity
      ['comparisons-thirteen', { design: thirteen }],
      ['cmp-id-k100', { design: cmp(4, { id: 'K100' }) }],
      ['cmp-id-lower', { design: cmp(4, { id: 'k5' }) }],
      ['cmp-id-bare', { design: cmp(4, { id: 'K' }) }],
      ['cmp-id-duplicate', { design: cmp(4, { id: 'K1' }) }],
      ['cmp-arm-unknown', { design: cmp(4, { arm: 'A7' }) }],
      ['cmp-against-self', { design: cmp(4, { against: 'A1' }) }],
      ['cmp-against-unknown', { design: cmp(4, { against: 'A3' }) }],
      ['cmp-parts-empty', { design: cmp(4, { parts: [] }) }],
      ['cmp-parts-empty-string', { design: cmp(4, { parts: [''] }) }],
      ['cmp-parts-duplicate', { design: cmp(4, { parts: ['a', 'a'] }) }],
      ['cmp-parts-missing', { design: design(d => { del(d.comparisons[4], 'parts') }) }],
      ['cmp-extra-key', { design: cmp(4, { note: 'x' }) }],
      // measure
      ['measure-metric-unknown', { design: cmp(3, { measure: { metric: 'nope' } }) }],
      ['measure-output-unknown', { design: cmp(4, { measure: { output: 'nope', comparator: 'exact' } }) }],
      ['measure-both', { design: cmp(4, { measure: { metric: 'wall', output: 'raw', comparator: 'exact' } }) }],
      ['measure-output-no-comparator', { design: cmp(4, { measure: { output: 'raw' } }) }],
      ['measure-comparator-unknown', { design: cmp(4, { measure: { output: 'raw', comparator: 'relative' } }) }],
      ['measure-output-against-reference', { design: cmp(4, { against: 'reference', reference: { source: 'run 7', values: { 'case-1': 1, 'case_2.b': 2 } }, pairing: 'unpaired' }) }],
      // criterion and direction
      ['criterion-unknown', { design: cmp(3, { criterion: 'equivalence' }) }],
      ['criterion-agreement-metric', { design: cmp(3, { criterion: 'agreement', pairing: 'paired_replicate' }) }],
      ['criterion-noninf-output', { design: cmp(4, { criterion: 'non_inferiority', direction: 'higher_better', pairing: 'unpaired' }) }],
      ['direction-agreement-higher', { design: cmp(4, { direction: 'higher_better' }) }],
      ['direction-superiority-lower', { design: cmp(3, { direction: 'lower_better' }) }],
      ['direction-noninf-two-sided', { design: cmp(2, { direction: 'two_sided' }) }],
      ['direction-ratio-two-sided', { design: cmp(1, { direction: 'two_sided' }) }],
      ['direction-unknown', { design: cmp(2, { direction: 'up' }) }],
      // unit, pairing, rule, confidence
      ['unit-unknown', { design: cmp(3, { unit: 'mean' }) }],
      ['unit-ratio-per-input', { design: cmp(1, { unit: 'per_input_all' }) }],
      ['unit-noninf-pooled', { design: cmp(3, { criterion: 'non_inferiority', direction: 'lower_better', unit: 'pooled_mean' }) }],
      ['unit-agreement-pooled', { design: cmp(4, { unit: 'pooled_mean' }) }],
      ['pairing-ratio-unpaired', { design: cmp(1, { pairing: 'unpaired' }) }],
      ['pairing-agreement-unpaired', { design: cmp(4, { pairing: 'unpaired' }) }],
      ['pairing-unknown', { design: cmp(3, { pairing: 'matched' }) }],
      ['rule-ratio-all-pairs', { design: cmp(1, { rule: 'all_pairs', confidence: null }) }],
      ['rule-noninf-bootstrap', { design: cmp(3, { criterion: 'non_inferiority', direction: 'lower_better', rule: 'bootstrap', confidence: 0.9 }) }],
      ['confidence-bootstrap-null', { design: cmp(1, { confidence: null }) }],
      ['confidence-one', { design: cmp(1, { confidence: 1 }) }],
      ['confidence-below-half', { design: cmp(1, { confidence: 0.4 }) }],
      ['confidence-all-pairs', { design: cmp(3, { confidence: 0.9 }) }],
      // margin
      ['margin-exact-abs', { design: cmp(4, { margin: { abs: 0 } }) }],
      ['margin-abs-null', { design: cmp(5, { margin: null }) }],
      ['margin-abs-with-rel', { design: cmp(5, { margin: { abs: 0, rel: 0 } }) }],
      ['margin-rel-max-abs-only', { design: cmp(0, { margin: { abs: 0.03125 } }) }],
      ['margin-negative', { design: cmp(5, { margin: { abs: -0.1 } }) }],
      ['margin-rel-negative', { design: cmp(0, { margin: { abs: 0.03125, rel: -1 } }) }],
      ['margin-string', { design: cmp(5, { margin: { abs: '0.1' } }) }],
      ['margin-noninf-rel', { design: cmp(2, { margin: { rel: 0.1 } }) }],
      ['margin-superiority-abs-rel', { design: cmp(3, { margin: { abs: 0.1, rel: 0.1 } }) }],
      ['margin-ratio-abs', { design: cmp(1, { margin: { abs: 0.1 } }) }],
      ['margin-bare-number', { design: cmp(2, { margin: 0.1 }) }],
      // threshold and strict
      ['threshold-ratio-zero', { design: cmp(1, { threshold: 0 }) }],
      ['threshold-ratio-negative', { design: cmp(1, { threshold: -1 }) }],
      ['threshold-ratio-null', { design: cmp(1, { threshold: null }) }],
      ['threshold-other', { design: cmp(3, { threshold: 1 }) }],
      ['strict-ratio-null', { design: cmp(1, { strict: null }) }],
      ['strict-ratio-string', { design: cmp(1, { strict: 'yes' }) }],
      ['strict-other', { design: cmp(3, { strict: false }) }],
      // reference
      ['reference-null-against-reference', { design: cmp(2, { reference: null }) }],
      ['reference-against-arm', { design: cmp(3, { reference: { source: 'run 7', values: { 'case-1': 1, 'case_2.b': 2 } } }) }],
      ['reference-missing-input', { design: cmp(2, c => ({ reference: { ...c.reference, values: { 'case-1': 1 } } })) }],
      ['reference-extra-input', { design: cmp(2, c => ({ reference: { ...c.reference, values: { ...c.reference.values, other: 3 } } })) }],
      ['reference-value-string', { design: cmp(2, c => ({ reference: { ...c.reference, values: { 'case-1': '1', 'case_2.b': 2 } } })) }],
      ['reference-source-empty', { design: cmp(2, c => ({ reference: { ...c.reference, source: '' } })) }],
      ['reference-extra-key', { design: cmp(2, c => ({ reference: { ...c.reference, note: 'x' } })) }],
      ['reference-paired', { design: cmp(2, { pairing: 'paired_replicate' }) }],
      ['reference-pooled', { design: cmp(2, { unit: 'pooled_mean' }) }],
      // missing, given
      ['missing-unknown', { design: cmp(3, { missing: 'skip' }) }],
      ['given-forward', { design: cmp(0, { given: ['K2'] }) }],
      ['given-self', { design: cmp(3, { given: ['K4'] }) }],
      ['given-unknown', { design: cmp(3, { given: ['K9'] }) }],
      ['given-duplicate', { design: cmp(3, { given: ['K1', 'K1'] }) }],
      ['given-string', { design: cmp(3, { given: 'K1' }) }],
    ].map(([name, spec]) => [name, { comparison, ...spec }])
    for (const r of await inParallel(invalid.map(([name, spec]) => () => execute(`invalid-${name}`, spec)))) intakeParse(r)

    // 2. Without args.comparison (baseline for the prompts), and the main comparison runs.
    const MAIN_FILES = comparisonFiles(viewOf(BASE)), NOEVAL_FILES = comparisonFiles(viewOf(NOEVAL)), MINIMAL_FILES = comparisonFiles(viewOf(MINIMAL))
    const [plain, main, reuse, noeval, minimal] = await inParallel([
      () => execute('plain', { generated: true, brief: true, setupFailures: 1, anchorsFailures: 1,
        stub: { profile: 'PASS', seal: 'PASS', propose: 'PASS', implement: 'PASS', evaluate: 'PASS' } }),
      // Generated harness, evaluator, brief, design inside a git work tree, one setup and one anchors repair that
      // also change files they may not change.
      () => execute('cmp-main', { comparison, design: BASE, git: true, generated: true, brief: true, setupFailures: 1, anchorsFailures: 1, repairTamper: true }),
      // harness_from, evaluator, a design path relative to the pipeline working directory, budget_s just below run_ceiling_s.
      // (A budget other than the hidden 31337, so that time-left figures in prompts cannot match a hidden value.)
      () => execute('cmp-reuse', { comparison: ({ designFile }) => ({ design: path.relative(pipeline, designFile) }), design: REUSE, ceiling: REUSE.budget_s + 1 }),
      // No evaluator, timeout_s per arm and input, generated harness without a brief.
      () => execute('cmp-noeval', { comparison, design: NOEVAL, generated: true }),
      // 5 arms, no output, no comparison, timeout_s null, no evaluator.
      () => execute('cmp-minimal', { comparison, design: MINIMAL, generated: true }),
    ])
    if (plain) {
      statuses(plain, STAGES.map(label => [label, 'PASS']))
      check('plain: without args.comparison no comparison file is written', () => {
        for (const file of ['control/comparison.json', 'control/comparison_seal.json', 'agent/comparison_view.json', 'control/arms_seal.json', 'control/comparison_scored.json'])
          assert.equal(fs.existsSync(path.join(plain.root, file)), false, file)
      })
      check('plain: without args.comparison no agent call has isolation and the stub wrote into A/ directly', () => {
        assert.deepEqual(plain.calls.map(call => call.label), ['intake', 'harness', 'harness-repair', 'anchors-repair'])
        for (const call of plain.calls) assert.equal(call.isolation ?? null, null, `${call.label} has isolation`)
      })
      check('plain: without args.comparison no prompt mentions the comparison view or comparison harness files', () => {
        for (const call of plain.calls) for (const needle of ['comparison_view', 'cmp_files', 'cmp_extract', 'versions.sh', 'fetch_private', 'evaluate.sh', 'CMP_INPUT', 'arms/'])
          assert.ok(!call.prompt.includes(needle), `${call.label} prompt mentions ${needle}`)
      })
      check('plain: the intake prompt names args.brief itself', () => {
        assert.ok(plain.calls.find(call => call.label === 'intake')?.prompt.includes(plain.brief), 'brief path not in the intake prompt')
      })
      check('plain: A/harness/ holds only what the agents wrote (the repaired setup.sh and anchors scripts)', () => {
        assert.deepEqual(fs.readdirSync(path.join(plain.agent, 'harness')).sort(), ['run_anchors.sh', 'run_command.sh', 'setup.sh'])
        assert.equal(sha(fs.readFileSync(path.join(plain.agent, 'harness', 'setup.sh'))), plain.written('harness-repair')['setup.sh'])
      })
    }
    if (main) {
      statuses(main, CMP_PASS)
      controlFileChecks(main, BASE)
      isolationChecks(main, { gitTop: main.science })
      promptChecks(main, plain)
      intakePromptChecks(main, true)
      harnessPromptChecks(main, true)
      check('cmp-main: calls are intake, harness, one setup repair and one anchors repair', () =>
        assert.deepEqual(main.calls.map(call => call.label), ['intake', 'harness', 'harness-repair', 'anchors-repair']))
      check('cmp-main: receipts probe, harness upload, setup, rerun, anchors, rerun, freeze', () => {
        const ops = main.receipts.map(receipt => receipt.operation)
        assert.deepEqual(ops.slice(0, 3), ['upload', 'probe', 'upload'])
        assert.equal(ops.filter(op => op === 'setup').length, 2)
        assert.equal(ops.filter(op => op === 'anchors').length, 2)
        assert.equal(ops.at(-1), 'reproduce-freeze')
      })
      check('cmp-main: intake copy-back: each regular file directly under the view\'s intake/, no symlink, no subdirectory', () => {
        const intake = listing(path.join(main.agent, 'intake'))
        assert.deepEqual(intake, main.written('intake'))
      })
      check('cmp-main: harness copy-back: files directly under harness/ and harness/arms/<arm id>.sh only', () => {
        const harness = listing(path.join(main.agent, 'harness'))
        const want = { ...main.written('harness'), 'arms/': 'dir' }
        want['setup.sh'] = main.written('harness-repair')['setup.sh']
        Object.assign(want, main.written('anchors-repair'))
        assert.deepEqual(harness, want)
      })
      check('cmp-main: the setup repair\'s other changes (anchors scripts, adapter, cmp_files.json, new script, intake) are discarded', () => {
        const repairs = main.calls.filter(call => call.label === 'anchors-repair')
        assert.equal(repairs.length, 1, 'no anchors repair')
        // At the anchors repair, A/harness/ held the harness agent's files with only setup.sh replaced.
        const want = { ...main.written('harness'), 'arms/': 'dir', 'setup.sh': main.written('harness-repair')['setup.sh'] }
        assert.deepEqual(repairs[0].agentHarness, want)
        assert.deepEqual(repairs[0].agentIntake, main.written('intake'))
      })
      check('cmp-main: the anchors repair\'s other changes (setup.sh, adapter, cmp_extract.json, versions.sh, new script) are discarded', () => {
        assert.equal(sha(fs.readFileSync(path.join(main.agent, 'harness', 'setup.sh'))), main.written('harness-repair')['setup.sh'])
        for (const name of ['arms/A1.sh', 'cmp_extract.json', 'versions.sh'])
          assert.equal(sha(fs.readFileSync(path.join(main.agent, 'harness', name))), main.written('harness')[name], name)
        assert.equal(fs.existsSync(path.join(main.agent, 'harness', 'evil2.sh')), false)
      })
      armsSealChecks(main, MAIN_FILES)
      check('cmp-main: the adapters, evaluator scripts and comparison files are in A/harness/ with the harness agent\'s bytes', () => {
        assert.deepEqual(fs.readdirSync(path.join(main.agent, 'harness', 'arms')).sort(), ['A0.sh', 'A1.sh'])
        for (const name of harnessNames(MAIN_FILES)) assert.ok(fs.readFileSync(path.join(main.agent, 'harness', name)).equals(Buffer.from(MAIN_FILES[name])), name)
      })
    }
    if (reuse) {
      statuses(reuse, CMP_PASS)
      controlFileChecks(reuse, REUSE)
      isolationChecks(reuse)
      promptChecks(reuse, plain)
      intakePromptChecks(reuse, true)
      check('cmp-reuse: only the intake agent is called (harness_from)', () => assert.deepEqual(reuse.calls.map(call => call.label), ['intake']))
      check('cmp-reuse: receipts as usual for A0', () => assert.deepEqual(reuse.receipts.map(receipt => receipt.operation), RECEIPTS_PASS))
      check('cmp-reuse: harness_from copies arms/, cmp_files.json, cmp_extract.json, versions.sh, fetch_private.sh and evaluate.sh with their exact bytes', () => {
        for (const name of [...harnessNames(MAIN_FILES), 'setup.sh', 'run_anchors.sh', 'run_command.sh'])
          assert.ok(fs.readFileSync(path.join(reuse.agent, 'harness', name)).equals(fs.readFileSync(path.join(reuse.source, name))), name)
      })
      armsSealChecks(reuse, MAIN_FILES)
    }
    if (noeval) {
      statuses(noeval, CMP_PASS)
      controlFileChecks(noeval, NOEVAL)
      isolationChecks(noeval)
      promptChecks(noeval, plain)
      intakePromptChecks(noeval, false)
      harnessPromptChecks(noeval, false)
      check('cmp-noeval: calls intake and harness; receipts as usual for A0', () => {
        assert.deepEqual(noeval.calls.map(call => call.label), ['intake', 'harness'])
        assert.deepEqual(noeval.receipts.map(receipt => receipt.operation), RECEIPTS_PASS)
      })
      armsSealChecks(noeval, NOEVAL_FILES)
    }
    if (minimal) {
      statuses(minimal, CMP_PASS)
      controlFileChecks(minimal, MINIMAL)
      isolationChecks(minimal)
      armsSealChecks(minimal, MINIMAL_FILES)
      check('cmp-minimal: five adapters copied back', () =>
        assert.deepEqual(fs.readdirSync(path.join(minimal.agent, 'harness', 'arms')).sort(), ['A0.sh', 'A1.sh', 'A2.sh', 'A3.sh', 'A4.sh']))
    }

    // 3. Comparison runs that stop at the seal of A0's reproduce: declined repair, sudo rule.
    const [declined, sudoFalse, sudoAbsent, sudoString, sudoNoevalFalse, sudoMinimalAbsent] = await inParallel([
      () => execute('cmp-repair-declined', { comparison, design: BASE, generated: true, setupFailures: 1, declineRepairs: true }),
      () => execute('sudo-false', { comparison, design: BASE, generated: true, sudo: false }),
      () => execute('sudo-absent', { comparison, design: BASE, generated: true, sudo: 'absent' }),
      () => execute('sudo-string', { comparison, design: BASE, sudo: 'true' }),
      // Separated users run for every comparison, so the rule holds without an evaluator too.
      () => execute('sudo-noeval-false', { comparison, design: NOEVAL, generated: true, sudo: false }),
      () => execute('sudo-minimal-absent', { comparison, design: MINIMAL, generated: true, sudo: 'absent' }),
    ])
    if (declined) {
      statuses(declined, failedAt('reproduce'))
      check('cmp-repair-declined: the setup repair is dispatched with isolation too', () => {
        const repair = declined.calls.find(call => call.label === 'harness-repair')
        assert.ok(repair, 'no setup repair')
        assert.equal(repair.isolation?.box_access, false)
      })
    }
    for (const r of [sudoFalse, sudoAbsent, sudoString, sudoNoevalFalse, sudoMinimalAbsent].filter(Boolean)) {
      statuses(r, failedAt('reproduce'))
      errorClass(r, 'reproduce', 'infra')
      check(`${r.name}: ${r.spec.design.evaluator ? 'with' : 'without'} an evaluator, sudo_nopasswd not true fails right after the probe, before the harness call`, () => {
        assert.deepEqual(r.calls.map(call => call.label), ['intake'])
        assert.deepEqual(r.receipts.map(receipt => receipt.operation), ['upload', 'probe'])
        assert.ok(r.boxLog.every(entry => !entry.harness && !entry.cmp_on_box), 'a harness file reached the box')
      })
    }

    // 4. Harness comparison files missing or invalid: reproduce fails with parse before the upload.
    const files = (edit, base = MAIN_FILES) => { const value = { ...base }; edit(value); return value }
    const json = (name, change, base = MAIN_FILES) => files(value => { const parsed = JSON.parse(value[name]); const out = change(parsed); value[name] = typeof out === 'string' ? out : JSON.stringify(out ?? parsed) })
    const loc = (arm, output, location) => json('cmp_files.json', value => { value.files[arm][output] = location })
    const rule = (i, patch) => json('cmp_extract.json', value => { Object.assign(value.rules[i], patch) })
    const ruleIndex = (arm, metric) => JSON.parse(MAIN_FILES['cmp_extract.json']).rules.findIndex(item => item.arm === arm && item.metric === metric)
    const badHarness = [
      ['adapter-missing', files(value => { value['arms/A1.sh'] = null })],
      ['adapters-none', files(value => { value['arms/A0.sh'] = null; value['arms/A1.sh'] = null })],
      ['adapter-empty', files(value => { value['arms/A0.sh'] = '' })],
      ['versions-missing', files(value => { value['versions.sh'] = null })],
      ['fetch-private-missing', files(value => { value['fetch_private.sh'] = null })],
      ['evaluate-missing', files(value => { value['evaluate.sh'] = null })],
      ['cmp-files-missing', files(value => { value['cmp_files.json'] = null })],
      ['cmp-files-not-json', files(value => { value['cmp_files.json'] = '{"files": {' })],
      ['cmp-files-extra-top-key', json('cmp_files.json', value => { value.note = 'x' })],
      ['cmp-files-missing-arm', json('cmp_files.json', value => { delete value.files.A1 })],
      ['cmp-files-extra-arm', json('cmp_files.json', value => { value.files.A2 = value.files.A0 })],
      ['cmp-files-missing-output', json('cmp_files.json', value => { delete value.files.A1.raw })],
      ['cmp-files-extra-output', json('cmp_files.json', value => { value.files.A1.nope = 'out/nope.txt' })],
      ['location-dotdot', loc('A1', 'energy', 'out/../secret.txt')],
      ['location-absolute', loc('A1', 'energy', '/tmp/result.txt')],
      ['location-first-run', loc('A1', 'energy', 'run/result.txt')],
      ['location-first-other', loc('A1', 'energy', 'home/result.txt')],
      ['location-space', loc('A1', 'energy', 'out/my result.txt')],
      ['location-dot', loc('A1', 'energy', 'out/./result.txt')],
      ['location-number', loc('A1', 'energy', 7)],
      ['location-glob-extra-key', loc('A1', 'raw', { glob: 'out/raw/*.bin', sort: 'name' })],
      ['location-glob-dotdot', loc('A1', 'raw', { glob: '../*' })],
      ['location-glob-first-other', loc('A1', 'raw', { glob: 'tmp/*.bin' })],
      ['extract-missing', files(value => { value['cmp_extract.json'] = null })],
      ['extract-not-json', files(value => { value['cmp_extract.json'] = '{"rules": [' })],
      ['extract-extra-top-key', json('cmp_extract.json', value => { value.note = 'x' })],
      ['extract-missing-rule', json('cmp_extract.json', value => { value.rules.splice(ruleIndex('A1', 'final_loss'), 1) })],
      ['extract-duplicate-rule', json('cmp_extract.json', value => { value.rules.push(value.rules[0]) })],
      ['extract-trusted-wall-rule', json('cmp_extract.json', value => { value.rules.push({ arm: 'A0', metric: 'wall', file: 'out/run.log', kind: 'regex', expr: 'wall=([0-9.]+)' }) })],
      ['extract-unknown-arm', json('cmp_extract.json', value => { value.rules.push({ arm: 'A2', metric: 'steps_per_s', file: 'out/run.log', kind: 'regex', expr: 'x=([0-9.]+)' }) })],
      ['extract-two-groups-for-max', rule(ruleIndex('A1', 'steps_per_s'), { expr: '(steps)=([0-9.]+)' })],
      ['extract-one-group-for-value-at-max-key', rule(ruleIndex('A0', 'final_loss'), { expr: 'loss=([0-9.]+)' })],
      ['extract-bad-regex', rule(ruleIndex('A1', 'steps_per_s'), { expr: 'x=([0-9.]+' })],
      ['extract-unknown-kind', rule(ruleIndex('A0', 'steps_per_s'), { kind: 'jq' })],
      ['extract-bad-pointer', rule(ruleIndex('A0', 'steps_per_s'), { expr: 'steps_per_s' })],
      ['extract-file-first-run', rule(ruleIndex('A0', 'steps_per_s'), { file: 'run/metrics.json' })],
      ['extract-file-dotdot', rule(ruleIndex('A0', 'steps_per_s'), { file: 'out/../metrics.json' })],
      ['extract-extra-rule-key', rule(0, { note: 'x' })],
    ]
    for (const r of await inParallel(badHarness.map(([name, cmpFiles]) => () => execute(`harness-${name}`, { comparison, design: BASE, cmpFiles }))))
      if (r) { harnessParse(r); check(`${r.name}: the control files are still written before intake`, () => assert.ok(fs.existsSync(path.join(r.control, 'comparison_seal.json')))) }
    // Generated harness: the view's harness/ is copied back, so evaluator scripts without an evaluator, an eval location
    // without an evaluator, and a missing adapter are found after the copy.
    const generatedBad = [
      ['gen-fetch-private-without-evaluator', NOEVAL, files(value => { value['fetch_private.sh'] = sh('true') }, NOEVAL_FILES)],
      ['gen-evaluate-without-evaluator', NOEVAL, files(value => { value['evaluate.sh'] = sh('true') }, NOEVAL_FILES)],
      ['gen-eval-location-without-evaluator', NOEVAL, json('cmp_files.json', value => { value.files.A1.energy = 'eval/energy.txt' }, NOEVAL_FILES)],
      ['gen-adapter-missing', BASE, files(value => { value['arms/A0.sh'] = null })],
      ['gen-evaluate-missing', BASE, files(value => { value['evaluate.sh'] = null })],
    ]
    for (const r of await inParallel(generatedBad.map(([name, value, cmpFiles]) => () => execute(`harness-${name}`, { comparison, design: value, generated: true, cmpFiles }))))
      harnessParse(r, true)

    // 5. Symbolic links in a view: an agent replaces its view's intake/, harness/ or harness/arms/ with a link to
    // another directory holding valid-looking files, or puts a link to a file there. Nothing is copied from them.
    const [intakeDir, intakeFile, harnessDir, harnessArms, harnessFile, repairDir, repairFile] = await inParallel([
      () => execute('link-intake-dir', { comparison, design: BASE, generated: true, intakeLink: 'dir' }),
      () => execute('link-intake-file', { comparison, design: BASE, generated: true, intakeLink: 'file' }),
      () => execute('link-harness-dir', { comparison, design: BASE, generated: true, harnessLink: 'dir' }),
      () => execute('link-harness-arms', { comparison, design: BASE, generated: true, harnessLink: 'arms' }),
      () => execute('link-harness-file', { comparison, design: BASE, generated: true, harnessLink: 'file' }),
      () => execute('link-repair-dir', { comparison, design: BASE, generated: true, setupFailures: 1, repairLink: 'dir' }),
      () => execute('link-repair-file', { comparison, design: BASE, generated: true, setupFailures: 1, repairLink: 'file' }),
    ])
    const regularFiles = directory => Object.entries(listing(directory) ?? {}).filter(([, kind]) => !['dir', 'link', 'other'].includes(kind))
    if (intakeDir) {
      check('link-intake-dir: nothing is copied from a view intake/ that is a symbolic link to another directory; intake does not pass', () => {
        assert.deepEqual(regularFiles(path.join(intakeDir.agent, 'intake')), [])
        assert.notEqual(intakeDir.stage('intake')?.status, 'PASS')
        assert.ok(!intakeDir.calls.some(call => call.label === 'harness'), 'the harness agent was called')
      })
    }
    if (intakeFile) {
      check('link-intake-file: a symbolic link to a file in the view intake/ is not copied (anchors.json); the regular files are; intake does not pass', () => {
        const got = Object.fromEntries(regularFiles(path.join(intakeFile.agent, 'intake')))
        const want = { ...intakeFile.written('intake') }
        delete want['anchors.json']
        assert.deepEqual(got, want)
        assert.notEqual(intakeFile.stage('intake')?.status, 'PASS')
      })
    }
    if (harnessDir) {
      check('link-harness-dir: nothing is copied from a view harness/ that is a symbolic link to another directory; no harness file reaches the box', () => {
        assert.deepEqual(regularFiles(path.join(harnessDir.agent, 'harness')), [])
        assert.notEqual(harnessDir.stage('reproduce')?.status, 'PASS')
        assert.ok(harnessDir.boxLog.every(entry => !entry.harness && !entry.cmp_on_box), 'a harness file reached the box')
        assert.equal(fs.existsSync(path.join(harnessDir.control, 'arms_seal.json')), false)
      })
    }
    for (const r of [harnessArms, harnessFile].filter(Boolean)) {
      harnessParse(r, true)
      check(`${r.name}: no adapter is copied from ${r.spec.harnessLink === 'arms' ? 'a view harness/arms/ that is a symbolic link to another directory' : 'a symbolic link to a file in harness/arms/ (A1.sh)'}`, () => {
        const arms = path.join(r.agent, 'harness', 'arms')
        const names = fs.existsSync(arms) ? fs.readdirSync(arms).sort() : []
        assert.deepEqual(names, r.spec.harnessLink === 'arms' ? [] : ['A0.sh'])
        // The other harness files are copied as usual.
        assert.equal(sha(fs.readFileSync(path.join(r.agent, 'harness', 'cmp_files.json'))), r.written('harness')['cmp_files.json'])
      })
    }
    for (const r of [repairDir, repairFile].filter(Boolean)) {
      check(`${r.name}: the setup repair's setup.sh is not copied from ${r.spec.repairLink === 'dir' ? 'a view harness/ that is a symbolic link to another directory' : 'a symbolic link to a file'}: A/harness/setup.sh keeps the harness agent's bytes`, () => {
        assert.ok(r.calls.some(call => call.label === 'harness-repair'), 'no setup repair')
        assert.equal(sha(fs.readFileSync(path.join(r.agent, 'harness', 'setup.sh'))), r.written('harness')['setup.sh'])
        assert.notEqual(r.stage('reproduce')?.status, 'PASS')
        assert.equal(r.records.find(row => row.stage === 'intake')?.status, 'PASS')
      })
    }

    // 6. The run root, the journal directory or the design file inside the pipeline working directory (which the
    // isolation runner exposes to every agent call): intake fails with parse before any agent call.
    const inside = await inParallel(['root', 'journal', 'design'].map(where => () => execute(`inside-${where}`, { comparison, design: BASE, inside: where })))
    for (const r of inside) intakeParse(r)
  } catch (error) { failures++; console.log(`FAIL test harness: ${error.stack}`) }
  finally {
    if (process.argv[3] === 'keep') console.log(`scratch kept: ${scratch}`)
    else fs.rmSync(scratch, { recursive: true, force: true })
  }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : `all ${checks} checks passed`)
  process.exitCode = failures ? 1 : 0
}
main()
