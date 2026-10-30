'use strict'
const path = require('node:path')
const os = require('node:os')
const fs = require('node:fs')
const { isDeepStrictEqual } = require('node:util')
const { createHash } = require('node:crypto')
const { projectPerformanceSeconds } = require('./seal_protocol.js')
const hash = bytes => createHash('sha256').update(bytes).digest('hex')
const readJSON = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const writeJSON = (file, value) => fs.writeFileSync(file, JSON.stringify(value, null, 2) + '\n')
const quote = value => `'${String(value).replace(/'/g, "'\\''")}'`
const methodNames = ['method.patch', 'setup_method.sh', 'run_method.sh']
const optionalMethodNames = ['run_anchors.sh']
const testReasons = ['dropped_inputs', 'duplicated_inputs', 'ordering', 'tail_handling', 'seeds',
  'equivalence', 'missing_output', 'invalid_output', 'upstream', 'other']
const reviewReasons = ['changes_method', 'equivalence_risk', 'resource_mismatch', 'changes_baseline',
  'changes_protocol', 'invalid_payload', 'cost_guard', 'other']
const evaluationInterface = `
Evaluation runs in fresh working directories with the same absolute source/data paths. Honor EVAL_ARM, EVAL_MODE, EVAL_PROTOCOL (sealed JSON path), EVAL_INPUTS, EVAL_SEEDS and EVAL_COMPUTE_BUDGET. BASELINE_DIR, METHOD_DIR and BASELINE_OUT are absolute fixed paths; METHOD_OUT and EVAL_OUT are this invocation's empty output directory. EVAL_COMPUTE_BUDGET is empty outside curves. EVAL_INPUTS and EVAL_SEEDS are JSON encodings of evaluation_inputs and paired_seed_tests. EVAL_INPUTS is an object whose ids array lists the sealed input identities in order; each record's input_id is one of those strings, and every other key (pins, configuration, generated-input descriptions) describes inputs and is never itself an input. EVAL_SEEDS is either {kind:"paired_median",seeds:[integer,...]}, whose seeds are the execution seeds in order, or {kind:"deterministic",...}, whose single execution seed is null; other keys are descriptive. Modes are anchors, equivalence, warmup, performance, curve. Non-anchor modes write EVAL_OUT/evaluation.json with records [{input_id,seed,metrics}], timing_scope, gpu_count, wall_s for reported timing, and compute_budget for curves. Iterate seeds first, then sealed input IDs; preserve exact counts/order. Each record's metrics holds every sealed equivalence_metrics name as a finite number for that input and seed, keyed by exactly that name. The method adapter's records mean the same as the baseline adapter's: for each input and seed, the same workload execution and the same metric definitions. timing_scope must equal the sealed scope; gpu_count must equal the arm's sealed hardware_cost_basis count; reported wall_s must be finite positive. Synchronize all used GPUs before returning or stopping reported timers. Include launch, transfer and merge within the sealed scope. Compute budgets are hard GPU-second limits; report outcomes only from computation within the budget.`

// Copy declared evidence only, rejecting links and special files at role boundaries.
function files(directory, relative = '', includeDirectories = false) {
  return fs.readdirSync(path.join(directory, relative)).sort().flatMap(name => {
    const label = path.join(relative, name), stat = fs.lstatSync(path.join(directory, label))
    if (stat.isSymbolicLink() || (!stat.isFile() && !stat.isDirectory())) throw new Error('invalid payload')
    return stat.isDirectory() ? [...(includeDirectories ? [label] : []), ...files(directory, label, includeDirectories)] : [label]
  })
}
function copy(source, target) {
  const stat = fs.lstatSync(source)
  if (stat.isSymbolicLink()) throw new Error('invalid input')
  if (stat.isDirectory()) {
    fs.mkdirSync(target, { recursive: true })
    for (const name of fs.readdirSync(source)) copy(path.join(source, name), path.join(target, name))
  } else if (stat.isFile()) {
    fs.mkdirSync(path.dirname(target), { recursive: true })
    fs.copyFileSync(source, target)
  } else throw new Error('invalid input')
}
function freeze(directory) {
  for (const name of fs.readdirSync(directory)) {
    const file = path.join(directory, name)
    if (fs.lstatSync(file).isDirectory()) freeze(file)
    else fs.chmodSync(file, 0o444)
  }
  fs.chmodSync(directory, 0o555)
}
function removeView(directory) {
  if (!fs.existsSync(directory)) return
  fs.chmodSync(directory, 0o700)
  for (const name of fs.readdirSync(directory)) {
    const file = path.join(directory, name)
    if (fs.lstatSync(file).isDirectory()) removeView(file)
  }
  fs.rmSync(directory, { recursive: true, force: true })
}

module.exports = async function implement(context) {
  const { A, C, root, agent, exec, boxCommand, remoteDirectory, executionTimeout, failure, nullFacts } = context
  const facts = { ...nullFacts('implement'), patch_applies: false, tests_pass: false,
    blind_tests: false, launch_review_pass: false, tokens_known: false, gpu_busy_known: false }
  const control = path.join(C, 'implement'), destination = path.join(A, 'results', 'implement')
  const tests = path.join(A, 'tests'), method = path.join(A, 'method')
  const stateScript = fs.readFileSync(path.join(__dirname, 'implement_state.py')).toString('base64')
  let seal, frozenTests, baselineState, methodPayloadHash, methodOutputs
  const views = []
  function verifySeal() {
    const seals = path.join(C, 'seals')
    const latest = fs.readdirSync(seals).filter(name => /^\d{4,}\.json$/.test(name))
      .sort((a, b) => Number(a.slice(0, -5)) - Number(b.slice(0, -5))).at(-1)
    if (!latest) throw new Error('missing seal')
    const receipt = readJSON(path.join(seals, latest))
    if (hash(fs.readFileSync(receipt.path)) !== receipt.sha256
      || hash(fs.readFileSync(path.join(A, 'PREDICTIONS.json'))) !== receipt.sha256
      || (seal && (seal.sha256 !== receipt.sha256 || seal.receipt !== latest))) throw new Error('changed seal')
    return { ...receipt, receipt: latest }
  }
  async function treeHash(directory) {
    return JSON.parse((await exec('python3', [path.join(__dirname, 'implement_state.py'), 'sha256', directory])).stdout).sha256
  }
  async function intact() {
    verifySeal()
    if (frozenTests && await treeHash(tests) !== frozenTests) {
      facts.blind_tests = false
      throw new Error('changed tests')
    }
  }
  async function author(label, output, repairCounts, timeoutFailure, missingPaths) {
    const view = fs.mkdtempSync(path.join(os.tmpdir(), `m5-${label}-`))
    views.push(view)
    for (const name of ['proposal.json', 'PREDICTIONS.json', 'intake', 'harness']) {
      copy(path.join(A, name), path.join(view, name))
    }
    if (label !== 'tests') copy(path.join(A, 'results', 'probe', 'probe.json'), path.join(view, 'probe.json'))
    if (label === 'tests') copy(path.join(A, 'results', 'reproduce', 'out'), path.join(view, 'baseline-out'))
    const outputPath = path.join(view, output)
    fs.mkdirSync(outputPath)
    if (repairCounts) copy(method, outputPath)
    const common = `Use only this private view: ${JSON.stringify(view)}. Proposal, intake, baseline harness and sealed PREDICTIONS.json are provided here.
Never read experiments/, operator/, control/, other role directories, transcripts or sessions. Do not change the sealed protocol, scale, inputs, seeds or tolerances.
${label === 'tests' ? `Script budget: run_tests.sh=${executionTimeout('run_tests')} seconds.` : `Script budgets in seconds: setup_method.sh=${executionTimeout('setup_method')}, run_method.sh=${executionTimeout('run_method')}, optional run_anchors.sh=${executionTimeout('run_method')}; complete evaluation scorer=${executionTimeout('evaluate')}.`} Use one fixed scale from EXECUTION.json, no scale search or doubling loops, and finish well within the budget.
${timeoutFailure ? `Timeout repair: budget ${timeoutFailure.budget_s}s; measured elapsed ${timeoutFailure.wall_s ?? 'unavailable'}s; measured overrun ${Number.isFinite(timeoutFailure.wall_s) ? Math.max(0, timeoutFailure.wall_s - timeoutFailure.budget_s) : 'unavailable'}s.` : ''}
Write only under ${JSON.stringify(outputPath)}. Return a short acknowledgement; the pipeline reads the files.`
    const prompt = label === 'tests' ? `Author independent output tests, before any method is authored or run.
${common}
You have no method code, patch, build logs or method results. Use only the proposal, baseline interface and baseline outputs, anchors, and sealed tolerances. No box access or workloads.
Write tests/run_tests.sh, tests/outputs.json and any fixtures. run_tests.sh is invoked as bash payload/tests/run_tests.sh from the remote run directory.
outputs.json must be exactly {"method_outputs": [path, ...]}: a nonempty array of unique relative POSIX paths naming every file the tests read under METHOD_OUT. No leading / or empty, . or .. path segments are allowed. Each path must name a regular file under this view's baseline-out/. Missing or invalid outputs.json fails author output like a missing run_tests.sh. It is frozen and hashed with the tests; only these paths are shared with the method author.
BASELINE_DIR points to the frozen published source, BASELINE_OUT to frozen baseline outputs, METHOD_DIR to the patched copy, and METHOD_OUT to out/. Fixtures are beside run_tests.sh; resolve them from its script directory.
Reuse upstream tests when available. Check actual method OUTPUTS, never source text, for dropped_inputs, duplicated_inputs, ordering, tail_handling, seeds, and equivalence within sealed tolerances. Include non-divisible tails and the final input; use fixed paired seeds or the sealed justified deterministic declaration. Tests see exactly two sets of outputs: BASELINE_OUT, the frozen baseline outputs, and METHOD_OUT, one method run at the same representative scale, inputs and seeds. Evaluation records (evaluation.json), held-out seeds, timing repetitions and compute budgets exist only in evaluate, and no case may require them. The equivalence case pairs baseline and method outputs by input and seed and applies the sealed equivalence_metrics margins and confidence rule to those representative pairs, at the sealed confidence for the number of pairs available. It fails only when for some metric the interval is disjoint from the open interval (-margin, +margin), or, under a deterministic seal, some paired difference exceeds the sealed tolerance. An interval that overlaps (-margin, +margin), or pairs too few for a finite interval, cannot reject, and the case passes; acceptance is decided in evaluate. Do not execute or read method source/scripts.
Write out/tests.json with exactly {passed, failed, cases: [{id, pass, reason_code}]}. Counts are nonnegative integers and must match cases. IDs are unique nonempty strings. Each pass is boolean; reason_code is null for passes, otherwise one of ${JSON.stringify(testReasons)}. Include case IDs dropped_inputs, duplicated_inputs, ordering, tail_handling, seeds, equivalence. A deterministic/not-applicable seed case must be justified by the seal. Always write the report, exit nonzero on failure. Never loosen a tolerance.`
      : `${repairCounts ? 'Repair the method once using only the failure category counts below.' : 'Implement the selected proposal in one author call.'}
${common}
Never read independent tests or test fixtures, even on the box. They are frozen and hidden from this session.
${repairCounts ? `No box access, test source, case IDs, output values, reports or logs are available for this repair. Failure reason_code counts: ${JSON.stringify(repairCounts)}.${missingPaths ? ` Layout feedback: ${JSON.stringify({ missing_paths: missingPaths })}.` : ''}`
  : `You may inspect the already-built baseline on the dev box using ~/.cache/metis-serve/box.sh. Remote run directory: ${JSON.stringify(remoteDirectory)}. Do not start/stop the box. No tests have been uploaded. Use probe.json for discovered tools. Never modify baseline-published/ or data/ or baseline-out/.`}
Write method.patch, setup_method.sh and run_method.sh under method/. You may additionally provide run_anchors.sh, the method variant of the baseline anchor protocol; no other files are allowed. Without it the pipeline invokes run_method.sh with EVAL_MODE=anchors, which must rerun every intake anchor and write out/anchors_measured.json. method.patch is a nonempty git-style patch relative to the published baseline root. The pipeline makes a fresh COPY at method/, checks/applies the patch there, and never patches baseline-published/.
The pipeline invokes bash payload/method/setup_method.sh, then bash payload/method/run_method.sh, from ${JSON.stringify(remoteDirectory)}. BASELINE_DIR, METHOD_DIR, BASELINE_OUT and METHOD_OUT are absolute paths supplied by the pipeline; METHOD_DIR is already patched. Setup builds only METHOD_DIR. Run the method at the same representative scale, seeds and input set as the baseline; write actual outputs in out/ with exactly the baseline format and relative location scheme. Frozen method_outputs: ${JSON.stringify(methodOutputs)}. run_method.sh must write each under METHOD_OUT at that relative path, as the baseline outputs do. Missing paths fail the attempt with category layout before tests run. Never copy baseline outputs as method results. Both scripts must fail nonzero on errors, create required output directories, and tolerate a fresh patched copy. Do not edit harness scripts, launchers or tests.`
    const reply = await agent(prompt + (label === 'implement' ? evaluationInterface : ''), { label, agentType: 'ls-writer', model: 'sonnet',
      repairable: false, fresh: true, ...(repairCounts ? { retry: 1 } : {}),
      isolation: { directory: view, hidden: [root, path.dirname(agent.journal || path.join(A, 'wf', 'journal.jsonl'))],
        box_access: label === 'implement' && !repairCounts } })
    if (reply == null) throw new Error('author failed')
    const names = files(outputPath)
    if (label === 'tests') {
      if (!names.includes('run_tests.sh') || fs.statSync(path.join(outputPath, 'run_tests.sh')).size === 0) throw new Error('missing tests')
      const outputs = readJSON(path.join(outputPath, 'outputs.json'))
      if (!outputs || Object.keys(outputs).join(',') !== 'method_outputs'
        || !Array.isArray(outputs.method_outputs) || !outputs.method_outputs.length
        || new Set(outputs.method_outputs).size !== outputs.method_outputs.length
        || !outputs.method_outputs.every(name => typeof name === 'string' && !name.startsWith('/')
          && name.split('/').every(segment => segment && segment !== '.' && segment !== '..')
          && fs.lstatSync(path.join(view, 'baseline-out', name)).isFile())) throw new Error('invalid outputs')
      methodOutputs = outputs.method_outputs
    } else if (!methodNames.every(name => names.includes(name)) || names.some(name => ![...methodNames, ...optionalMethodNames].includes(name)
      || fs.statSync(path.join(outputPath, name)).size === 0)) throw new Error('invalid method')
    for (const name of names.filter(name => name.endsWith('.sh'))) await exec('bash', ['-n', path.join(outputPath, name)])
    if (repairCounts) fs.rmSync(method, { recursive: true, force: true })
    copy(outputPath, path.join(A, output))
  }
  async function command(name, body, to, timeout) {
    const result = await boxCommand(name, `set -e\n${body}`, to, timeout)
    if (result.rc === 124 || result.timed_out === true) return { ...result, error: 'timeout', budget_s: timeout }
    if (result.error || !Number.isInteger(result.rc) || result.fetched !== true) return { ...result, error: 'infra' }
    return result
  }
  function adapterVoid(category) {
    for (const name of ['patch_applies', 'tests_pass', 'blind_tests', 'launch_review_pass']) facts[name] = null
    return { ...failure(facts, category === 'timeout' ? 'timeout' : 'parse'), status: 'VOID' }
  }
  async function smokeAdapter(predictions, attempt) {
    await intact()
    const to = path.join(destination, 'adapter', String(attempt))
    const result = await command('adapter-smoke', 'rm -rf out/adapter out/smoke.json\npython3 -B adapter-payload/adapter_smoke.py',
      to, executionTimeout('run_method'))
    let category = result.error === 'timeout' ? 'timeout' : result.error || result.rc !== 0 ? 'exit' : null
    const file = path.join(to, 'out', 'adapter', 'evaluation.json')
    if (!category && !fs.existsSync(file)) category = 'missing_output'
    if (!category) {
      try {
        const report = readJSON(file), rule = predictions.paired_seed_tests
        const seeds = rule.kind === 'deterministic' ? [null] : rule.seeds
        const ids = predictions.evaluation_inputs.ids
        const identities = seeds.flatMap(seed => ids.map(id => [id, seed]))
        if (!Array.isArray(report.records) || report.records.length !== identities.length
          || !report.records.every((row, index) => row && row.input_id === identities[index][0] && row.seed === identities[index][1])
          || !isDeepStrictEqual(report.timing_scope, predictions.timing_scope)
          || !Number.isInteger(report.gpu_count) || report.gpu_count !== predictions.hardware_cost_basis.baseline_gpus
          || (predictions.timing_scope.kind === 'reported_wall' && (!Number.isFinite(report.wall_s) || report.wall_s <= 0))) category = 'records'
        else if (!report.records.every(row => row.metrics && typeof row.metrics === 'object' && !Array.isArray(row.metrics)
          && Object.values(row.metrics).every(Number.isFinite)
          && predictions.equivalence_metrics.every(metric => Number.isFinite(row.metrics[metric.name])))) category = 'metrics'
      } catch { category = 'records' }
    }
    let cost
    if (!category) {
      try {
        const smoke = readJSON(path.join(to, 'out', 'smoke.json'))
        if (!smoke || Array.isArray(smoke) || Object.keys(smoke).length !== 1
          || !Number.isFinite(smoke.process_wall_s) || smoke.process_wall_s < 0) category = 'missing_output'
        else {
          const { warmup, repetitions } = predictions
          const projected_s = projectPerformanceSeconds(predictions, smoke.process_wall_s)
          const evaluate_budget_s = executionTimeout('evaluate')
          if (projected_s > 0.9 * evaluate_budget_s) {
            category = 'cost'
            cost = { process_wall_s: smoke.process_wall_s, warmup, repetitions, projected_s, evaluate_budget_s }
          }
        }
      } catch { category = 'missing_output' }
    }
    return { category, log: result.log, cost }
  }
  async function repairAdapter(smoke) {
    await intact()
    const view = fs.mkdtempSync(path.join(os.tmpdir(), 'm5-adapter-repair-'))
    views.push(view)
    for (const name of ['PREDICTIONS.json', 'intake', 'harness']) copy(path.join(A, name), path.join(view, name))
    const permitted = path.join('harness', 'run_evaluation.sh')
    const lines = smoke.log && fs.existsSync(smoke.log) ? fs.readFileSync(smoke.log, 'utf8').split('\n') : []
    if (lines.at(-1) === '') lines.pop()
    const log = lines.slice(-200).join('\n')
    const reply = await agent(`Repair the baseline evaluation adapter once. Use only this private view: ${JSON.stringify(view)}.
Sealed PREDICTIONS.json, intake files and current harness scripts are provided here. Failure category: ${smoke.category}.
${smoke.category === 'cost' ? `Cost projection: ${JSON.stringify(smoke.cost)}. The complete performance scorer must fit within 0.9 times evaluate_budget_s.` : ''}
Rewrite only harness/run_evaluation.sh, creating it when absent. Run the exact published configuration and measure actual outputs; never reuse baseline outputs. Do not change other scripts, source, data, scale, inputs, seeds or tolerances. Do not access the box or run workloads locally.
The pipeline owns CUDA MPS. No harness script may set, unset or override any CUDA_MPS_* environment variable, or start or stop an MPS daemon; inherit these variables unchanged.
Script budget: run_evaluation.sh=${executionTimeout('run_method')} seconds. Use one fixed scale from EXECUTION.json, no scale search or doubling loops, and finish well within the budget.
${evaluationInterface}
Last at most 200 log lines:\n${log}
Return a short acknowledgement; the pipeline reads the script.`,
      { label: 'adapter-repair', agentType: 'ls-writer', model: 'sonnet', retry: 1, repairable: false, fresh: true,
        isolation: { directory: view, hidden: [root, path.dirname(agent.journal || path.join(A, 'wf', 'journal.jsonl'))], box_access: false } })
    if (reply == null) throw new Error('invalid adapter repair')
    const script = path.join(view, permitted)
    if (!fs.lstatSync(script).isFile() || !fs.statSync(script).size) throw new Error('missing adapter')
    await exec('bash', ['-n', script])
    copy(script, path.join(A, permitted))
  }
  async function uploadAdapter(attempt) {
    const commands = ['mkdir -p adapter-payload out']
    const payload = attempt === 1 ? [
      ...['eval_common.py', 'adapter_smoke.py'].map(name => [path.join(__dirname, name), 'adapter-payload/' + name]),
      [path.join(A, 'PREDICTIONS.json'), 'adapter-payload/predictions.json'],
    ] : [[path.join(A, 'harness', 'run_evaluation.sh'), 'harness/run_evaluation.sh']]
    for (const [source, target] of payload) {
      commands.push(`: > ${quote(target)}`)
      const bytes = fs.readFileSync(source).toString('base64')
      for (let offset = 0; offset < bytes.length; offset += 24576) {
        commands.push(`printf %s ${quote(bytes.slice(offset, offset + 24576))} | base64 -d >> ${quote(target)}`)
      }
    }
    return uploadCommands(commands, path.join(destination, 'adapter', String(attempt)))
  }
  const stateCommand = includeTests => `printf %s ${quote(stateScript)} | base64 -d | python3 -I - baseline_sha256 baseline-published data_sha256 data baseline_outputs_sha256 baseline-out${includeTests ? ' tests_sha256 payload/tests method_payload_sha256 payload/method' : ''} > out/implement-state.json`
  async function checkState(attempt, phase, includeTests = true) {
    const to = path.join(destination, `attempt-${attempt}`, phase)
    const result = await command('implement-state', `mkdir -p out\n${stateCommand(includeTests)}`, to, executionTimeout('setup_method'))
    if (result.error || result.rc !== 0) return result.error || 'infra'
    const current = readJSON(path.join(to, 'out', 'implement-state.json'))
    if (!Object.values(current).every(value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value))) return 'parse'
    if (['baseline_sha256', 'data_sha256', 'baseline_outputs_sha256'].some(key => current[key] !== baselineState[key])) return 'other'
    if (includeTests && current.tests_sha256 !== frozenTests) { facts.blind_tests = false; return 'other' }
    if (includeTests) {
      if (phase === 'before') methodPayloadHash = current.method_payload_sha256
      if (typeof methodPayloadHash !== 'string' || current.method_payload_sha256 !== methodPayloadHash) return 'other'
    }
    return null
  }
  const environment = `export BASELINE_DIR=${quote(remoteDirectory + '/baseline-published')} METHOD_DIR=${quote(remoteDirectory + '/method')} BASELINE_OUT=${quote(remoteDirectory + '/baseline-out')} METHOD_OUT=${quote(remoteDirectory + '/out')}`
  async function upload(attempt) {
    const commands = ['test ! -L payload', 'test ! -L payload/tests', 'if test -d payload/tests; then chmod -R u+w payload/tests; fi',
      'rm -rf payload/method payload/tests', 'mkdir -p payload/method payload/tests out']
    for (const [source, target] of [[method, 'method'], [tests, 'tests']]) {
      for (const name of files(source, '', true)) {
        const remote = path.posix.join('payload', target, name.split(path.sep).join('/'))
        if (fs.lstatSync(path.join(source, name)).isDirectory()) {
          commands.push(`mkdir -p ${quote(remote)}`)
          continue
        }
        commands.push(`mkdir -p ${quote(path.posix.dirname(remote))}`, `: > ${quote(remote)}`)
        const bytes = fs.readFileSync(path.join(source, name)).toString('base64')
        for (let offset = 0; offset < bytes.length; offset += 24576) {
          commands.push(`printf %s ${quote(bytes.slice(offset, offset + 24576))} | base64 -d >> ${quote(remote)}`)
        }
      }
    }
    commands.push('find payload/tests -type d -exec chmod 555 {} +', 'find payload/tests -type f -exec chmod 444 {} +')
    return uploadCommands(commands, path.join(destination, `attempt-${attempt}`, 'upload'))
  }
  async function uploadCommands(commands, to) {
    let batch = [], size = 0, result
    for (const line of commands) {
      if (size + line.length > 32768) {
        result = await command('implement-upload', batch.join('\n'), to, executionTimeout('setup_method'))
        if (result.error || result.rc !== 0) return result
        batch = []; size = 0
      }
      batch.push(line); size += line.length + 1
    }
    return command('implement-upload', batch.join('\n'), to, executionTimeout('setup_method'))
  }
  async function reviewLaunch() {
    const view = fs.mkdtempSync(path.join(os.tmpdir(), 'm5-review-'))
    views.push(view)
    for (const name of ['method', 'proposal.json', 'PREDICTIONS.json', 'implement-payload.json', 'intake']) copy(path.join(A, name), path.join(view, name))
    writeJSON(path.join(view, 'seal.json'), seal)
    const schema = { type: 'object', additionalProperties: false, required: ['pass', 'reason_codes'],
      properties: { pass: { type: 'boolean' }, reason_codes: { type: 'array', items: { enum: reviewReasons } } } }
    const review = await agent(`Review the final launch payload once, after smoke tests and any bounded repair.
Read only this embedded payload: ${JSON.stringify({
      proposal: readJSON(path.join(view, 'proposal.json')),
      predictions: readJSON(path.join(view, 'PREDICTIONS.json')), seal,
      payload: readJSON(path.join(view, 'implement-payload.json')),
      method: Object.fromEntries(methodNames.map(name => [name, fs.readFileSync(path.join(view, 'method', name), 'utf8')])),
      intake: Object.fromEntries(files(path.join(view, 'intake')).map(name => [name, fs.readFileSync(path.join(view, 'intake', name), 'utf8')])),
    })}.
Check the selected method, unchanged scientific protocol and baseline, payload, equivalent output interface, representative scale, resource use and projected costs. Return {pass, reason_codes} matching the schema. Never read or change tests, call the box, or modify files.`,
      { label: 'review', agentType: 'qt-bare', model: 'sonnet', schema, repairable: false, fresh: true,
        isolation: { directory: view, hidden: [root, path.dirname(agent.journal || path.join(A, 'wf', 'journal.jsonl'))], box_access: false } })
    const { validate } = require('../idea/schema.js')
    if (validate(schema, review).length || (review.pass && review.reason_codes.length)) return 'parse'
    writeJSON(path.join(A, 'REVIEW.json'), review)
    facts.launch_review_pass = review.pass
    return review.pass ? null : 'other'
  }
  function scoreTests(file) {
    const report = readJSON(file), keys = object => Object.keys(object).sort().join(',')
    if (keys(report) !== 'cases,failed,passed' || !Number.isInteger(report.passed) || report.passed < 0
      || !Number.isInteger(report.failed) || report.failed < 0 || !Array.isArray(report.cases) || !report.cases.length
      || new Set(report.cases.map(row => row?.id)).size !== report.cases.length
      || !report.cases.every(row => row && keys(row) === 'id,pass,reason_code'
        && typeof row.id === 'string' && row.id.trim() && typeof row.pass === 'boolean'
        && (row.pass ? row.reason_code === null : testReasons.includes(row.reason_code)))
      || report.passed !== report.cases.filter(row => row.pass).length
      || report.failed !== report.cases.filter(row => !row.pass).length
      || !['dropped_inputs', 'duplicated_inputs', 'ordering', 'tail_handling', 'seeds', 'equivalence']
        .every(id => report.cases.some(row => row.id === id))) throw new Error('invalid report')
    return report
  }
  try {
    seal = verifySeal()
    // Refuse to replace an earlier test freeze or reset the repair budget on resume.
    if ([control, tests, method, path.join(A, 'REVIEW.json')].some(file => fs.existsSync(file))) return failure(facts, 'other')
    fs.mkdirSync(control)
    fs.mkdirSync(destination, { recursive: true })
    writeJSON(path.join(control, 'started.json'), { seal_sha256: seal.sha256, utc: new Date().toISOString() })
    const proposal = readJSON(path.join(A, 'proposal.json'))
    const predictions = readJSON(path.join(A, 'PREDICTIONS.json'))
    if (!predictions.predictions?.some(row => row.method === proposal.method)
      || !predictions.equivalence_metrics || !predictions.paired_seed_tests) return failure(facts, 'parse')
    for (const name of ['setup_method', 'run_method', 'run_tests']) executionTimeout(name)
    const initial = await command('implement-baseline', `test -d baseline-published\ntest ! -L baseline-published\ntest ! -L data\ntest ! -L out\ntest -d reproduce-out\ntest ! -L reproduce-out\nmkdir -p data out\ntest ! -e baseline-out\ncp -a reproduce-out baseline-out\n${stateCommand(false)}`,
      path.join(destination, 'baseline'), executionTimeout('setup_method'))
    if (initial.error || initial.rc !== 0) return failure(facts, initial.error || 'infra')
    baselineState = readJSON(path.join(destination, 'baseline', 'out', 'implement-state.json'))
    if (Object.keys(baselineState).sort().join(',') !== 'baseline_outputs_sha256,baseline_sha256,data_sha256'
      || !Object.values(baselineState).every(value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value))) return failure(facts, 'parse')
    writeJSON(path.join(control, 'baseline.json'), baselineState)
    let uploaded = await uploadAdapter(1)
    if (uploaded.error || uploaded.rc !== 0) return failure(facts, uploaded.error || 'infra')
    let smoke = await smokeAdapter(predictions, 1)
    if (smoke.category) {
      try { await repairAdapter(smoke) } catch { return adapterVoid('records') }
      uploaded = await uploadAdapter(2)
      if (uploaded.error || uploaded.rc !== 0) return failure(facts, uploaded.error || 'infra')
      smoke = await smokeAdapter(predictions, 2)
      if (smoke.category) return adapterVoid(smoke.category)
    }
    await intact()
    await author('tests', 'tests')
    freeze(tests)
    frozenTests = await treeHash(tests)
    fs.writeFileSync(path.join(control, 'tests.json'), JSON.stringify({ sha256: frozenTests,
      files: files(tests).map(name => ({ path: name.split(path.sep).join('/'), sha256: hash(fs.readFileSync(path.join(tests, name))) })),
      seal_sha256: seal.sha256, utc: new Date().toISOString() }) + '\n', { flag: 'wx', mode: 0o444 })
    facts.blind_tests = true
    await intact()
    await author('implement', 'method')
    await intact()
    const stateError = await checkState(0, 'after-author', false)
    if (stateError) return failure(facts, stateError)
    for (let attempt = 1; attempt <= 2; attempt++) {
      await intact()
      const payload = { attempt, remote_directory: remoteDirectory,
        baseline_directory: 'baseline-published', method_directory: 'method', baseline_outputs: 'baseline-out',
        method_outputs: 'out', tests_sha256: frozenTests, seal_sha256: seal.sha256,
        method_files: files(method).map(name => ({ path: name, sha256: hash(fs.readFileSync(path.join(method, name))) })),
        timeouts: Object.fromEntries(['setup_method', 'run_method', 'run_tests'].map(name => [name, executionTimeout(name)])) }
      writeJSON(path.join(A, 'implement-payload.json'), payload)
      const uploaded = await upload(attempt)
      if (uploaded.error || uploaded.rc !== 0) return failure(facts, uploaded.error || 'infra')
      let stateError = await checkState(attempt, 'before')
      if (stateError) return failure(facts, stateError)
      facts.patch_applies = false
      facts.tests_pass = false
      let counts, failedClass, timeoutFailure, missingPaths
      const to = phase => path.join(destination, `attempt-${attempt}`, phase)
      const apply = `git --git-dir=/dev/null --work-tree=${quote(remoteDirectory + '/method')} -C method apply`
      const patched = await command('implement-patch', `rm -rf method\ncp -a baseline-published method\n${apply} --check -- ${quote(remoteDirectory + '/payload/method/method.patch')}\n${apply} -- ${quote(remoteDirectory + '/payload/method/method.patch')}`,
        to('patch'), executionTimeout('setup_method'))
      if (patched.error) return failure(facts, patched.error)
      facts.patch_applies = patched.rc === 0
      if (!facts.patch_applies) { counts = { patch_applies: 1 }; failedClass = 'parse' }
      if (!counts) {
        const setup = await command('setup-method', `rm -rf out\nmkdir -p out\n${environment}\nbash payload/method/setup_method.sh`, to('setup'), executionTimeout('setup_method'))
        if (setup.error && setup.error !== 'timeout') return failure(facts, setup.error)
        if (setup.rc !== 0) { counts = { setup_failed: 1 }; failedClass = 'install' }
        if (setup.error === 'timeout') { counts = { timeout: 1 }; failedClass = 'timeout'; timeoutFailure = setup }
      }
      if (!counts) {
        const run = await command('run-method', `rm -rf out\nmkdir -p out\n${environment}\nbash payload/method/run_method.sh`, to('run'), executionTimeout('run_method'))
        if (run.error && run.error !== 'timeout') return failure(facts, run.error)
        if (run.rc !== 0) { counts = { run_failed: 1 }; failedClass = 'numeric' }
        if (run.error === 'timeout') { counts = { timeout: 1 }; failedClass = 'timeout'; timeoutFailure = run }
        if (!counts) {
          missingPaths = methodOutputs.filter(name => {
            try {
              const stat = fs.lstatSync(path.join(to('run'), 'out', name))
              return !stat.isFile() && !stat.isSymbolicLink()
            } catch { return true }
          }).sort()
          if (missingPaths.length) { counts = { layout: 1 }; failedClass = 'numeric' }
          else missingPaths = undefined
        }
      }
      stateError = await checkState(attempt, 'after-method')
      if (stateError) return failure(facts, stateError)
      if (!counts) {
        const result = await command('run-tests', `rm -f out/tests.json\n${environment}\nbash payload/tests/run_tests.sh`, to('tests'), executionTimeout('run_tests'))
        if (result.error && result.error !== 'timeout') return failure(facts, result.error)
        let report
        try { report = scoreTests(path.join(to('tests'), 'out', 'tests.json')) }
        catch { counts = { invalid_report: 1 }; failedClass = 'parse' }
        if (result.error === 'timeout') timeoutFailure = result
        if (report) {
          facts.tests_pass = result.rc === 0 && report.failed === 0
          if (!facts.tests_pass) {
            counts = report.cases.filter(row => !row.pass).reduce((out, row) => {
              out[row.reason_code] = (out[row.reason_code] || 0) + 1; return out
            }, {})
            if (!Object.keys(counts).length) counts.tests_failed = 1
            failedClass = 'numeric'
          }
        }
      }
      if (timeoutFailure) { counts = { timeout: 1 }; failedClass = 'timeout' }
      stateError = await checkState(attempt, 'after-tests')
      if (stateError) return failure(facts, stateError)
      fs.rmSync(path.join(destination, 'out'), { recursive: true, force: true })
      copy(path.join(to('after-tests'), 'out'), path.join(destination, 'out'))
      await intact()
      if (!counts) {
        const reviewError = await reviewLaunch()
        if (reviewError) return failure(facts, reviewError)
        await intact()
        return facts.patch_applies && facts.tests_pass && facts.blind_tests && facts.launch_review_pass
          ? { status: 'PASS', facts } : failure(facts, 'other')
      }
      writeJSON(path.join(control, `attempt-${attempt}.json`), { attempt, reason_code_counts: counts })
      if (attempt === 2) return failure(facts, failedClass)
      await author('implement', 'method', counts, timeoutFailure, missingPaths)
    }
  } catch {
    return failure(facts, 'parse')
  } finally {
    for (const view of views) removeView(view)
  }
}
