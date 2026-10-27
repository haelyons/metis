// wf.js script. Intake through evaluate are real; takeaways remains a placeholder.
const meta = { name: 'm5', description: 'Explicit-run-root scientific pipeline skeleton' }

return (async () => {
  const { default: path } = await import('node:path')
  const { mkdirSync, existsSync, readFileSync, writeFileSync, readdirSync, rmSync } = await import('node:fs')
  const { createHash, randomUUID } = await import('node:crypto')
  const { execFile } = await import('node:child_process')
  const { promisify } = await import('node:util')
  const { homedir } = await import('node:os')
  const runStarted = Date.now()
  const exec = promisify(execFile)
  const input = (typeof args === 'string' ? JSON.parse(args) : args) || {}
  if (!input.run_root || !input.tag) throw new Error('m5 needs run_root and tag')
  const root = path.resolve(input.run_root)
  const A = path.join(root, 'agent'), S = path.join(root, 'operator'), C = path.join(root, 'control')
  for (const dir of [A, S, C]) mkdirSync(dir, { recursive: true })
  const { default: raids } = await import(path.resolve('m5/raids.js'))
  const { raid } = await raids.reserve(input)
  input.chat_prefix = `x-${raid}`
  // wf.js gives ls-writer this cwd and its write sandbox; control/operator stay script-owned.
  input.cwd = A

  const fields = {
    intake: ['found', 'anchors_count', 'data', 'licence', 'stock_environment', 'size'],
    reproduce: ['anchors_passed', 'anchors_total', 'stock_verified', 'tuned_control_valid'],
    profile: ['profile_complete', 'timed_fraction', 'gpu_telemetry'],
    seal: ['seal_present', 'seal_verified', 'prediction_count'],
    propose: ['method', 'expected_speedup', 'votes_approve', 'votes_total', 'vote_share', 'gate_pass'],
    implement: ['patch_applies', 'tests_pass', 'blind_tests', 'launch_review_pass'],
    evaluate: ['validity_pass', 'equivalence_pass', 'performance_pass', 'equal_cost', 'speedup_published', 'speedup_tuned', 'cost_ratio', 'prediction_ratio', 'curve_points'],
    takeaways: ['operator_written', 'research_written', 'teardown_confirmed'],
  }
  const nullFacts = stage => Object.fromEntries([...fields[stage], 'tokens_known', 'gpu_busy_known'].map(key => [key, null]))
  const stub = stage => ({ status: input.stub?.[stage] ?? 'PASS', facts: nullFacts(stage) })

  const intakeSchema = {
    type: 'object', additionalProperties: false,
    required: fields.intake,
    properties: {
      found: { type: 'boolean' }, anchors_count: { type: 'integer', minimum: 0 },
      data: { enum: ['available', 'partial', 'unavailable', 'unknown'] },
      licence: { enum: ['permitted', 'restricted', 'unknown'] },
      stock_environment: { type: ['boolean', 'null'] },
      size: { enum: ['tiny', 'small', 'medium', 'large', 'unknown'] },
    },
  }
  const readJSON = file => JSON.parse(readFileSync(file, 'utf8'))
  const boxPath = path.join(homedir(), '.cache', 'metis-serve', 'box.json')
  let box = null, stageReceipts = []
  const nonnegative = value => typeof value === 'number' && Number.isFinite(value) && value >= 0
  const journalText = () => agent.journal && existsSync(agent.journal) ? readFileSync(agent.journal, 'utf8') : ''
  function answeringFamilies(offset) {
    return journalText().slice(offset).split('\n').filter(Boolean).map(line => JSON.parse(line))
      .filter(row => ['result', 'cached'].includes(row.type) && typeof row.model === 'string')
      .map(row => /^(codex|cursor|lambda|claude)\//.exec(row.model)?.[1] ?? 'opencode')
  }
  function runBoxUSD(fallback) {
    if (!box || !nonnegative(box.price_usd_h)) return fallback
    const start = Date.parse(box.started_utc)
    const end = box.ended_utc == null ? Date.now() : Date.parse(box.ended_utc)
    if (!Number.isFinite(start) || !Number.isFinite(end) || end < start) return fallback
    return Math.max(0, Math.min(Date.now(), end) - Math.max(runStarted, start)) / 3600000 * box.price_usd_h
  }
  const hasValue = value => value != null && (typeof value !== 'string' || value.trim() !== '')
    && (typeof value !== 'object' || Object.keys(value).length > 0)
  const menu = ['data-parallel over inputs', 'batching', 'multi-GPU', 'ensembles', 'pipelining']

  async function intake() {
    if (input.stub?.intake != null) return stub('intake')
    const facts = { ...nullFacts('intake'), tokens_known: false, gpu_busy_known: false }
    const directory = path.join(A, 'intake')
    mkdirSync(directory, { recursive: true })
    const brief = typeof input.brief === 'string' && input.brief.trim() ? input.brief : null
    const briefPath = brief && (existsSync(path.resolve(brief)) || path.isAbsolute(brief)
      || /[/\\]|\.(md|txt|json|ya?ml|pdf)$/i.test(brief)) ? path.resolve(brief) : null
    const prompt = `Perform scientific benchmark intake in one bounded pass.
${briefPath
  ? `Read the brief file ${JSON.stringify(briefPath)}. Extract its benchmark; if unreadable or unsupported, report found=false. Do not substitute another benchmark. Copy the brief to intake/brief.md when readable.`
  : `Search for a public benchmark, inspecting at most three candidates and using at most two search calls. ${brief ? `Search hint: ${JSON.stringify(brief)}.` : ''} If none qualifies, report found=false. Never invent a benchmark, citation, published number, tolerance, pin, or command.`}
Write only under ${JSON.stringify(directory)}. Never read experiments/, operator/, or control/.
Never invent a benchmark, citation, published number, tolerance, pin, or command.
Write all five JSON files, including explicit null/unavailable values and reasons when evidence is missing:
- benchmark.json: identity, outcome definition, citations, source licences and intended-use permissions, stock CUDA image feasibility and evidence, data plus peak working-set GiB, scoring and repeatability rules; record search candidates if searched.
- anchors.json: an array of credible independently published reference anchors, each with a unique non-empty string id, quantity, finite numeric published_value, tolerance, source (citation). Tolerance must be a nonnegative finite number (absolute), {"abs": x}, or {"rel": x}; relative tolerance means x * abs(published_value). Optional comparison is one of "==" (default), ">", ">=", "<", "<=". When the published criterion is a threshold, supply comparison so measured_value comparison published_value expresses that criterion; tolerance is ignored for inequalities and may be 0. Do not count self-generated checks or unsupported references.
- data.json: required inputs, availability, access instructions, licences, pins/hashes, splits and seeds; distinguish generated inputs from missing data.
- baseline.json: repo, commit or immutable pin, build_commands, run_commands, published_configuration; cite their sources. Do not run builds or workloads.
- EXECUTION.json: representative_scale, inputs, outputs, timing_scope; specify the real representative workload and scoring interface, not a toy extrapolation. Optional stage_budgets_s overrides per-script seconds with keys setup, anchors, profile, method_setup, method_run, tests, evaluate. Defaults are 1200 except tests=900 and evaluate=2400; supplied args budgets are ${JSON.stringify(input.stage_budgets_s || {})}. All budgets must be positive integers <=999999999. Choose one fixed scale; no scale search or doubling loops. Scripts must finish well within their budgets.
Return only the facts matching the supplied schema. anchors_count must equal the credible anchors written.
data=available only when all required data is accessible. licence=permitted only when intended use is allowed.
stock_environment=true means provisionally feasible on the stock image, false means incompatible, null means unknown pending reproduction.
size is data plus peak working set: tiny <=1 GiB, small <=10 GiB, medium <=100 GiB, large >100 GiB, otherwise unknown.
Gate: found, at least one independent anchor, available required data, permitted licence, and stock_environment is not false. Missing evidence must stay unknown.`
    try {
      const reply = await agent(prompt, { label: 'intake', agentType: 'ls-writer', model: 'sonnet', schema: intakeSchema })
      if (reply == null) return { status: 'FAIL', facts }
      // Whitelist facts: no benchmark content or arbitrary reply keys can reach S.
      for (const key of fields.intake) facts[key] = reply[key]
      const documents = {}
      for (const name of ['benchmark', 'data', 'baseline', 'EXECUTION']) {
        const value = readJSON(path.join(directory, `${name}.json`))
        if (!hasValue(value) || typeof value !== 'object' || Array.isArray(value)) return { status: 'FAIL', facts }
        documents[name] = value
      }
      const anchors = readJSON(path.join(directory, 'anchors.json'))
      const validAnchors = Array.isArray(anchors) && new Set(anchors.map(anchor => anchor?.id)).size === anchors.length
        && anchors.every(anchor => anchor && typeof anchor.id === 'string' && anchor.id.trim()
          && ['quantity', 'source'].every(key => hasValue(anchor[key]))
          && Number.isFinite(anchor.published_value) && validTolerance(anchor.tolerance))
      const complete = validAnchors && anchors.length === facts.anchors_count
        && ['repo', 'build_commands', 'run_commands', 'published_configuration'].every(key => hasValue(documents.baseline[key]))
        && hasValue(documents.baseline.commit ?? documents.baseline.pin)
        && ['representative_scale', 'inputs', 'outputs', 'timing_scope'].every(key => hasValue(documents.EXECUTION[key]))
      const pass = complete && facts.found && facts.anchors_count >= 1 && facts.data === 'available'
        && facts.licence === 'permitted' && facts.stock_environment !== false
      return { status: pass ? 'PASS' : 'FAIL', facts }
    } catch {
      return { status: 'FAIL', facts }
    }
  }
  function validTolerance(value) {
    if (Number.isFinite(value)) return value >= 0
    return value && typeof value === 'object' && !Array.isArray(value)
      && Object.keys(value).length === 1 && ['abs', 'rel'].some(key => Number.isFinite(value[key]) && value[key] >= 0)
  }
  const quote = value => `'${String(value).replace(/'/g, "'\\''")}'`
  const remoteDirectory = `/tmp/m5-${randomUUID()}`
  const harnessDirectory = path.join(A, 'harness')
  const receiptsDirectory = path.join(C, 'receipts')
  const failure = (facts, error_class) => ({ status: 'FAIL', facts, v1: {
    error_class, exit_code: error_class === 'anchor' ? 4 : error_class === 'timeout' ? 3 : 2,
  } })
  const defaultBudgets = { setup: 1200, anchors: 1200, profile: 1200, method_setup: 1200,
    method_run: 1200, tests: 900, evaluate: 2400 }
  function executionTimeout(name) {
    const key = ({ run_anchors: 'anchors', setup_method: 'method_setup', run_method: 'method_run', run_tests: 'tests' })[name] || name
    const execution = readJSON(path.join(A, 'intake', 'EXECUTION.json'))
    const seconds = execution.stage_budgets_s?.[key] ?? input.stage_budgets_s?.[key] ?? defaultBudgets[key]
    if (!Number.isInteger(seconds) || seconds <= 0 || seconds > 999999999) throw new Error('invalid budget')
    return seconds
  }
  const budgetPrompt = () => `Script budgets in seconds: setup.sh=${executionTimeout('setup')}, run_anchors.sh=${executionTimeout('anchors')}, fixed profiler=${executionTimeout('profile')}, run_evaluation.sh=${executionTimeout('method_run')} per invocation (also run_anchors.sh when used as the evaluation adapter); complete evaluation scorer=${executionTimeout('evaluate')}. Use one fixed scale from EXECUTION.json, no scale search or doubling loops, and finish well within the budget.`
  async function boxCommand(name, command, destination, timeout, retry = false) {
    mkdirSync(receiptsDirectory, { recursive: true })
    const number = Math.max(0, ...readdirSync(receiptsDirectory)
      .filter(file => /^\d+-/.test(file)).map(file => Number(file.split('-')[0]))) + 1
    const id = `${String(number).padStart(4, '0')}-${name}`
    const receiptPath = path.join(receiptsDirectory, `${id}.json`)
    // Never score files left by an earlier invocation using the same run root.
    rmSync(path.join(destination, 'out'), { recursive: true, force: true })
    let commandFailed = false
    try {
      await exec('bash', ['m5/boxrun.sh', '--name', id, '--cmd', command,
        '--remote-dir', remoteDirectory, '--timeout', String(timeout), '--fetch', 'out',
        '--to', destination, '--receipt', receiptPath])
    } catch {
      commandFailed = true
      // boxrun's receipt, never command output, determines the public failure class.
    }
    let receipt
    try { receipt = readJSON(receiptPath) } catch { return { error: 'infra' } }
    receipt.budget_s = timeout
    receipt.overrun = receipt.rc === 124 || receipt.timed_out === true || receipt.wall_s > timeout
    stageReceipts.push(receipt)
    // Transport and integrity commands have no authored script to change. Repair by one identical retry.
    const authored = ['setup', 'anchors', 'profile', 'setup-method', 'run-method', 'run-tests']
    if (!retry && !authored.includes(name) && (receipt.rc === 124 || receipt.timed_out === true)) {
      return boxCommand(name, command, destination, timeout, true)
    }
    if (receipt.rc === 124 || receipt.timed_out === true) return { ...receipt, error: 'timeout', log: path.join(destination, `${id}.log`) }
    if (!Number.isInteger(receipt.rc)) return { error: 'infra' }
    if (commandFailed && receipt.rc === 0) return { error: 'infra', rc: receipt.rc }
    if (receipt.rc === 0 && receipt.fetched !== true) return { error: 'infra', rc: receipt.rc }
    return { ...receipt, log: path.join(destination, `${id}.log`) }
  }
  async function uploadHarness(names, destination, timeout) {
    const commands = ['mkdir -p harness out']
    for (const name of names) {
      const bytes = readFileSync(path.join(harnessDirectory, name)).toString('base64')
      commands.push(`printf %s ${quote(bytes)} | base64 -d > ${quote(`harness/${name}`)}`)
    }
    return boxCommand('upload', `set -e\n${commands.join('\n')}`, destination, timeout)
  }
  const harnessRules = 'Scope: setup.sh builds and checks only the baseline. The pipeline owns profiling and profiler installation; do not write profile.sh or install profiling tools. A repair must change only the failing script and stay within its scope. Run the published build and binary and read measurements from its OUTPUT. run_command.sh is the canonical measured command and complete environment, including working directory, arguments, CUDA_VISIBLE_DEVICES and GPU count. run_anchors.sh must invoke bash harness/run_command.sh without overriding its environment or duplicating the workload command; parse its saved output for anchor measurements. The fixed profiler invokes that identical file with bash from the same working directory. Keep output paths stable and preserve logs. Every later run script must preserve the published configuration. Validate printed configuration against the actual command and environment. Preserve consistency in repairs; read the other harness scripts while editing only the failing script. Never parse or assert on source text. Measurement checks must fail only on missing or invalid output; the pipeline scores measured values against anchors.'
  let boxProbe
  let harnessSource
  const writeHarnessSource = () => writeFileSync(path.join(C, 'harness_source.json'), JSON.stringify(harnessSource, null, 2) + '\n')
  const boxProbePrompt = () => `Box probe (collected by the pipeline before harness generation):
${JSON.stringify(boxProbe, null, 2)}
Use the probe's discovered paths and versions. Accept either a complete CUDA toolkit root containing bin/nvcc, include/cuda_runtime.h and lib64/libcudart.so, or the distro layout with /usr/bin/nvcc, /usr/include/cuda_runtime.h and libcudart.so under /usr/lib/x86_64-linux-gnu. Have the scripts check all three selected paths with ls on the box. Prefer a complete toolkit root when both layouts exist; otherwise accept the complete distro layout without requiring /usr/lib64/libcudart.so. Use the same selected compiler, include and library paths in every script, including repairs. For a complete root, pass it explicitly via CUDAToolkit_ROOT or -DCMAKE_CUDA_COMPILER=<root>/bin/nvcc and prepend <root>/bin to PATH. For the distro layout, use /usr/bin/nvcc with its distro include and library paths explicitly; do not treat /usr as a toolkit root requiring lib64. Never rely on /usr/bin/nvcc when a complete toolkit root exists. Never hard-code a toolkit path the probe did not find, even if the brief suggests one. If a required tool is missing, install it with apt only from sources the probe lists; do not add repositories or assume a package exists. Commented source lines are not enabled repositories. If apt cannot supply it, use pip for cmake only; otherwise fail with a clear message.`
  async function collectBoxProbe(timeout) {
    const destination = path.join(A, 'results', 'probe')
    const probePath = path.join(destination, 'probe.json')
    rmSync(probePath, { force: true })
    const bytes = readFileSync('m5/box_probe.sh').toString('base64')
    const uploaded = await boxCommand('upload', `set -e\nmkdir -p harness out\nprintf %s ${quote(bytes)} | base64 -d > harness/box_probe.sh`, destination, timeout)
    if (uploaded.error || uploaded.rc !== 0) throw Object.assign(new Error('probe upload failed'), { error_class: uploaded.error || 'infra' })
    const result = await boxCommand('probe', 'set -e\nrm -f out/probe.json\nbash harness/box_probe.sh', destination, timeout)
    if (result.error || result.rc !== 0) throw Object.assign(new Error('probe failed'), { error_class: result.error || 'infra' })
    const content = readFileSync(path.join(destination, 'out', 'probe.json'), 'utf8')
    const probe = JSON.parse(content)
    if (!probe || typeof probe !== 'object' || Array.isArray(probe)) throw new Error('invalid probe')
    writeFileSync(probePath, content)
    boxProbe = probe
  }
  async function runHarness(name, operation, destination, timeout) {
    const command = `bash harness/${name}`
    const result = await boxCommand(operation, command, destination, timeout)
    if (result.error === 'infra' || (result.rc === 0 && !result.error)) return result
    let tail
    try {
      const lines = readFileSync(result.log, 'utf8').trimEnd().split('\n')
      tail = lines.slice(-200).join('\n')
    } catch {
      if (!result.error) return result
      tail = ''
    }
    const repair = await agent(`${name} failed (rc ${result.rc}${result.error ? `, output gate: ${result.error}` : ''}). Repair only ${JSON.stringify(path.join(harnessDirectory, name))} using intake evidence. Preserve the published pin, configuration and stock image; sudo only for apt. ${harnessRules} Never read experiments/, operator/, or control/. Do not run workloads locally or access the box. This is the only repair attempt for this script.
Budget: ${timeout}s; measured elapsed: ${result.wall_s ?? 'unavailable'}s; measured overrun: ${Number.isFinite(result.wall_s) ? Math.max(0, result.wall_s - timeout) : 'unavailable'}s. ${budgetPrompt()}
${boxProbePrompt()}
Log tail (at most 200 lines):\n${tail}`,
      { label: name === 'setup.sh' ? 'harness-repair' : `${operation}-repair`, agentType: 'ls-writer', model: 'sonnet', retry: 1 })
    if (repair == null) return result
    if (harnessSource) {
      harnessSource.files[name].modified = true
      writeHarnessSource()
    }
    const uploaded = await uploadHarness([name], destination, executionTimeout('setup'))
    if (uploaded.error || uploaded.rc !== 0) return { ...uploaded, error: uploaded.error || 'infra' }
    return boxCommand(operation, command, destination, timeout)
  }
  async function reproduce() {
    // Snapshot only the current allocation; never reuse a prior run's box record.
    rmSync(path.join(C, 'box.json'), { force: true })
    if (existsSync(boxPath)) {
      writeFileSync(path.join(C, 'box.json'), readFileSync(boxPath))
      try { box = readJSON(path.join(C, 'box.json')) } catch { box = null }
    }
    if (input.stub?.reproduce != null) return stub('reproduce')
    const facts = { ...nullFacts('reproduce'), stock_verified: false, tokens_known: false, gpu_busy_known: false }
    const destination = path.join(A, 'results', 'reproduce')
    let setupTimeout, anchorsTimeout
    try {
      setupTimeout = executionTimeout('setup')
      anchorsTimeout = executionTimeout('run_anchors')
    } catch { return failure(facts, 'parse') }
    try {
      await collectBoxProbe(setupTimeout)
    } catch (error) { return failure(facts, error.error_class || 'infra') }
    const prompt = `Write a baseline harness from ${JSON.stringify(path.join(A, 'intake'))}/*.
Never read experiments/, operator/, or control/. Write only under ${JSON.stringify(harnessDirectory)}.
The operator already started the dev box. Do not start, stop, or access it; the pipeline runs your scripts.
${harnessRules}
${budgetPrompt()}
${boxProbePrompt()}
Write three self-contained bash scripts, invoked from a shared remote working directory with bash harness/<name>:
- setup.sh: build/install the published baseline at its exact intake pin in the stock image. Use sudo only for apt. Preserve stock torch and published source/configuration. Stage source in baseline-published/ and inputs in data/. Do not silently substitute or tune the baseline. Make setup safe to retry once in this directory.
- run_anchors.sh: run the published anchor protocol at the real representative scale declared in EXECUTION.json. Write out/anchors_measured.json as {anchor_id: measured_number}, one finite number per intake anchor. Never copy published values as measurements.
- run_command.sh: only the exact measured baseline run command and its complete environment at the fixed representative scale. Run the published binary, save its stdout/stderr for run_anchors.sh to parse, and propagate its exit status. Do not measure stages, sample telemetry, install tools, or write profiling outputs. run_anchors.sh invokes this file; the pipeline profiles this same file.
Also provide run_evaluation.sh for the published baseline evaluation interface, or make run_anchors.sh handle non-anchor EVAL_MODE. Evaluation uses fresh working directories with baseline-published/, method/, data/, harness/ and payload/ links and absolute BASELINE_DIR, METHOD_DIR, BASELINE_OUT, METHOD_OUT and EVAL_OUT paths. EVAL_PROTOCOL points to the sealed JSON; EVAL_INPUTS and EVAL_SEEDS contain its JSON input and seed specifications; EVAL_COMPUTE_BUDGET is empty except in curve mode. Modes are equivalence, warmup, performance and curve. Run the published configuration on every sealed input/seed, seeds first then input IDs, and write EVAL_OUT/evaluation.json: {records:[{input_id,seed,metrics:{metric_name:finite_number}}],timing_scope,gpu_count,wall_s,compute_budget}. Use null seed for deterministic protocols; timing_scope must equal the seal; wall_s is required for reported_wall scopes; compute_budget is required for curves. Synchronize every used GPU before returning or stopping reported timers; include launch, transfer and merge overhead. Enforce curve budgets in GPU seconds. Always measure actual outputs; never reuse baseline outputs.
Create output directories, preserve logs, and exit nonzero on failure. Read all intake files for pins, commands, data, scale and protocol. Do not run builds or workloads locally.
Return a short completion acknowledgement; the pipeline reads the scripts itself.`
    try {
      mkdirSync(harnessDirectory, { recursive: true })
      if (input.harness_from != null) {
        if (typeof input.harness_from !== 'string' || !input.harness_from.trim()) return failure(facts, 'parse')
        const source = path.resolve(input.harness_from)
        const names = ['setup.sh', 'run_anchors.sh', 'run_command.sh',
          ...(existsSync(path.join(source, 'run_evaluation.sh')) ? ['run_evaluation.sh'] : [])]
        const scripts = names.map(name => [name, readFileSync(path.join(source, name))])
        harnessSource = { source, files: {} }
        for (const [name, bytes] of scripts) {
          writeFileSync(path.join(harnessDirectory, name), bytes)
          harnessSource.files[name] = { sha256: createHash('sha256').update(bytes).digest('hex'), modified: false }
        }
        writeHarnessSource()
      } else {
        const reply = await agent(prompt, { label: 'harness', agentType: 'ls-writer', model: 'sonnet' })
        if (reply == null) return failure(facts, 'parse')
      }
      const uploaded = await uploadHarness(['setup.sh', 'run_anchors.sh', 'run_command.sh',
        ...(existsSync(path.join(harnessDirectory, 'run_evaluation.sh')) ? ['run_evaluation.sh'] : [])], destination, setupTimeout)
      if (uploaded.error || uploaded.rc !== 0) return failure(facts, uploaded.error || 'infra')
      const setup = await runHarness('setup.sh', 'setup', destination, setupTimeout)
      if (setup.error) {
        facts.stock_verified = setup.rc === 0 && setup.error !== 'timeout'
        return failure(facts, setup.error)
      }
      facts.stock_verified = setup.rc === 0
      if (!facts.stock_verified) return failure(facts, 'install')
      const anchors = await runHarness('run_anchors.sh', 'anchors', destination, anchorsTimeout)
      if (anchors.error) return failure(facts, anchors.error)
      if (anchors.rc !== 0) return failure(facts, 'anchor')
      const scorePath = path.join(destination, 'anchors_scored.json')
      try {
        await exec('python3', ['m5/score_anchors.py', path.join(A, 'intake', 'anchors.json'),
          path.join(destination, 'out', 'anchors_measured.json'), scorePath])
      } catch (error) {
        if (error.code !== 4) return failure(facts, 'parse')
      }
      const score = readJSON(scorePath)
      facts.anchors_passed = score.anchors_passed
      facts.anchors_total = score.anchors_total
      const passed = score.all_passed && facts.stock_verified
      return passed ? { status: 'PASS', facts, v1: { run_valid: true } }
        : { ...failure(facts, 'anchor'), v1: { error_class: 'anchor', exit_code: 4, run_valid: false } }
    } catch {
      return failure(facts, 'parse')
    }
  }
  async function profile() {
    if (input.stub?.profile != null) return stub('profile')
    const facts = { ...nullFacts('profile'), profile_complete: false, tokens_known: false, gpu_busy_known: false }
    const destination = path.join(A, 'results', 'profile')
    function validateProfile() {
      facts.profile_complete = false
      facts.timed_fraction = null
      facts.gpu_telemetry = null
      rmSync(path.join(A, 'profile-packet.json'), { force: true })
      try {
        const directory = path.join(destination, 'out', 'profile')
        const stages = readJSON(path.join(directory, 'stages.json'))
        const { total_wall_s } = readJSON(path.join(directory, 'total_wall_s.json'))
        const gpuUtil = readJSON(path.join(directory, 'gpu_util.json'))
        if (!Number.isFinite(total_wall_s) || total_wall_s <= 0 || !Array.isArray(stages)
          || !stages.every(item => item && typeof item.stage === 'string' && item.stage.trim()
            && (item.kind === undefined || ['compute', 'transfer', 'other'].includes(item.kind))
            && Number.isFinite(item.wall_s) && item.wall_s >= 0
            && (item.gpu_s === null || (Number.isFinite(item.gpu_s) && item.gpu_s >= 0)))
          || !Array.isArray(gpuUtil) || !gpuUtil.every(item => item && nonnegative(item.t)
            && nonnegative(item.util) && item.util <= 100)) return 'parse'
        const timedWall = stages.reduce((sum, item) => sum + item.wall_s, 0)
        if (!Number.isFinite(timedWall)) return 'parse'
        const measuredStages = stages.map(({ stage, kind, wall_s, gpu_s, start_s }) => {
          if (start_s !== undefined && (!nonnegative(start_s) || !Number.isFinite(start_s + wall_s))) {
            throw new Error('invalid stage window')
          }
          const samples = start_s === undefined ? [] : gpuUtil.filter(item => item.t >= start_s && item.t < start_s + wall_s)
          return { stage, ...(kind === undefined ? {} : { kind }), wall_s, gpu_s,
            start_s: start_s ?? null, wall_fraction: Math.min(1, wall_s / total_wall_s),
            mean_gpu_util: samples.length ? samples.reduce((sum, item) => sum + item.util / 100, 0) / samples.length : null }
        })
        let allocation
        try { allocation = readJSON(path.join(C, 'box.json')) } catch { /* Probe supplies inventory. */ }
        const allocationCount = Number.isInteger(allocation?.gpu_count) && allocation.gpu_count >= 0
          ? allocation.gpu_count : Number(/^gpu_(\d+)x_/.exec(allocation?.type)?.[1])
        facts.profile_complete = true
        facts.timed_fraction = Math.min(1, timedWall / total_wall_s)
        facts.gpu_telemetry = gpuUtil.length > 0
        writeFileSync(path.join(A, 'profile-packet.json'), JSON.stringify({
          stages: measuredStages, total_wall_s,
          timed_fraction: facts.timed_fraction, gpu_telemetry: facts.gpu_telemetry,
          gpu_count: Number.isInteger(allocationCount) && allocationCount >= 0 ? allocationCount
            : Array.isArray(boxProbe?.nvidia?.gpus) ? boxProbe.nvidia.gpus.length : 1,
        }, null, 2) + '\n')
        const processWrapper = stages.some(item => /(?:^|[\s_-])(?:process|wrapper|telemetry|total|overall)(?:$|[\s_-])/i.test(item.stage)
          || (item.wall_s >= total_wall_s * 0.98 && item.wall_s <= total_wall_s * 1.02))
        return stages.length >= 3 && !processWrapper && facts.timed_fraction >= 0.9 && facts.gpu_telemetry
          ? null : 'numeric'
      } catch {
        return 'parse'
      }
    }
    try {
      rmSync(path.join(A, 'profile-packet.json'), { force: true })
      const timeout = executionTimeout('profile')
      const commands = ['set -e', 'mkdir -p profiler', 'rm -rf out/profile']
      for (const name of ['profile_nsys.sh', 'profile_summarise.py']) {
        const bytes = readFileSync(path.join('m5', name)).toString('base64')
        commands.push(`printf %s ${quote(bytes)} | base64 -d > ${quote(`profiler/${name}`)}`)
      }
      const probeBytes = Buffer.from(JSON.stringify(boxProbe)).toString('base64')
      commands.push(`printf %s ${quote(probeBytes)} | base64 -d > profiler/probe.json`)
      const uploaded = await boxCommand('upload', commands.join('\n'), destination, timeout)
      if (uploaded.error || uploaded.rc !== 0) return failure(facts, uploaded.error || 'infra')
      const result = await boxCommand('profile',
        `bash profiler/profile_nsys.sh harness/run_command.sh out/profile ${timeout}`, destination, timeout)
      if (result.error) return failure(facts, result.error)
      if (existsSync(path.join(destination, 'out', 'profile', 'infra.json'))) return failure(facts, 'infra')
      if (result.rc !== 0) return failure(facts, 'parse')
      const invalid = validateProfile()
      if (invalid) return failure(facts, invalid)
      return { status: 'PASS', facts }
    } catch {
      return failure(facts, 'parse')
    }
  }
  async function seal() {
    if (input.stub?.seal != null) return stub('seal')
    const facts = { ...nullFacts('seal'), seal_present: false, seal_verified: false,
      prediction_count: 0, tokens_known: false, gpu_busy_known: false }
    const predictionPath = path.join(A, 'PREDICTIONS.json')
    const profilePath = path.join(A, 'profile-packet.json')
    const boundsPath = path.join(A, 'bounds.json')
    const reject = code => ({ ...failure(facts, 'numeric'), reason_codes: [code] })
    let check = 'bounds_generation_failed'
    let bounds
    try {
      rmSync(boundsPath, { force: true })
      await exec('python3', ['m5/bounds.py', profilePath, boundsPath])
      bounds = readJSON(boundsPath)
    } catch { return reject(check) }
    const prompt = `Seal a prospective scientific evaluation protocol in one narrow pass.
Read ${JSON.stringify(path.join(A, 'intake'))}/*, ${JSON.stringify(profilePath)}, and ${JSON.stringify(boundsPath)} only.
Never read experiments/, operator/, or control/. Do not search, build, run workloads, or write method code.
Write only ${JSON.stringify(predictionPath)}. Use intake evidence and the profile when present. Do not invent measurements; label assumptions and unavailable evidence explicitly.
The method menu is exactly ${JSON.stringify(menu)}. Deterministic bounds (p is the actionable timed fraction; k is the maximum factor): ${JSON.stringify(bounds)}.
Include every feasible entry once; list every entry with bound <1.05 exactly once as {method, reason} in infeasible_methods, never in predictions. With no feasible entry, write predictions=[] as a negative result.
For each interval require finite low >0, low <= high <= its method's bound, and high-low <= bound-1. When at least two methods are feasible, their intervals must not all be identical. Base each interval on its method's profile evidence and overheads.
Amdahl bound is 1/((1-p)+p/k). The supplied bounds are ceilings, not measured gains; intervals without measurements are prospective assumptions. Include launch/transfer/merge overhead.
Write an object with these fields:
- outputs_stochastic: boolean; true for Monte Carlo, sampling, or outputs affected by random seeds, even when fixed seeds make a run reproducible.
- predictions: array of {method, expected_speedup_interval: {low, high}, outcome_vs_compute_points}. Each point is {compute_budget, predicted_outcome, uncertainty}. Include all sealed compute budgets for each method. Both predicted_outcome and uncertainty must be non-null, nonempty values at every budget. If no numeric outcome forecast is scientifically supported, use an explicit nonempty declaration such as predicted_outcome={not_applicable:true,reason:"fixed-work benchmark; no calibrated outcome curve"} and explain assumptions or unavailable evidence in uncertainty. Never invent a numeric forecast or use null; equal_outcome_target.not_applicable does not waive these point fields.
- equivalence_metrics: quantities, scientific tolerances, and sources from requirements or baseline variability, never method outputs. Lack of significance is not equivalence.
For stochastic outputs, equivalence_metrics must be statistical: use paired seeds and positive absolute scientific margins derived from baseline variability (for example Monte Carlo standard error), with a sealed significance level alpha = 1 - confidence_rule.equivalence.confidence. Require the confidence interval for paired differences to lie within those margins. Never demand exact, zero-tolerance, or bitwise equivalence for stochastic outputs. Exact or bitwise equivalence is required only for deterministic outputs.
- paired_seed_tests: stochastic paired-seed test and fixed seeds, or an explicit scientifically justified deterministic/not-applicable declaration.
- sample_sizes and confidence_rule: powered equivalence sample sizes and the confidence decision rule.
- hardware_cost_basis, timing_scope, minimum_worthwhile_gain (a speedup ratio >1).
- evaluation_inputs and splits: fixed input identities/pins, held-out splits and seeds, or explicit generated-input specifications.
- compute_budgets: at least three distinct positive numeric budgets, with units in hardware_cost_basis.
- repetitions: integer >=5 timing pairs; warmup: fixed warmup protocol; scheduling_order: paired randomisation protocol; equal_outcome_target: the fixed scientific target.
Use executable v1 evaluation fields: evaluation_inputs={ids:[unique string IDs], ...input pins/specification}; sample_sizes={inputs:IDs.length,seeds:seed count}; equivalence_metrics=[{name,tolerance,source}], tolerance a nonnegative absolute number, {abs:number}, or {rel:number}. paired_seed_tests={kind:"deterministic",justification:"scientific reason"} or {kind:"paired_median",seeds:[unique integers]}; stochastic metrics require absolute margins. confidence_rule={performance:{kind:"paired_median",confidence:0.95},equivalence:{kind:"paired_median",confidence:0.95}} uses exact binomial order-statistic bounds (one-sided performance, two-sided equivalence with Bonferroni across metrics). Choose enough repetitions/seeds for finite bounds; 95% needs at least 5 timing pairs and 6 seed pairs for one metric. warmup is a nonnegative integer per arm. scheduling_order={kind:"randomized_pairs",seed:integer}. timing_scope={kind:"process_wall" or "reported_wall",gpu_synchronization:"adapter",description:"scope including launch/transfer/merge"}. hardware_cost_basis={baseline_gpus:positive integer,method_gpus:positive integer,budget_unit:"gpu_s"}. equal_outcome_target={metric:"outcome metric name",comparison:">=",target:finite number} or {not_applicable:true,reason:"why benchmark has no outcome curve"}. Unsupported prose-only protocols produce VOID at evaluation.
Define the complete protocol now, before method code exists. Scope/tolerance changes require a new sealed run.
Return a short completion acknowledgement; the script reads and seals the file itself.`
    try {
      check = 'agent_failed'
      const reply = await agent(prompt, { label: 'seal', agentType: 'ls-writer', model: 'sonnet' })
      if (reply == null) return reject(check)
      check = 'predictions_read_failed'
      const predictions = readJSON(predictionPath)
      if (!predictions || !Array.isArray(predictions.predictions)) return reject('predictions_invalid')
      facts.prediction_count = predictions.predictions.length
      check = 'protocol_incomplete'
      const required = ['equivalence_metrics', 'paired_seed_tests', 'sample_sizes', 'confidence_rule',
        'hardware_cost_basis', 'timing_scope', 'minimum_worthwhile_gain', 'evaluation_inputs', 'splits',
        'compute_budgets', 'repetitions', 'warmup', 'scheduling_order', 'equal_outcome_target']
      const complete = typeof predictions.outputs_stochastic === 'boolean'
        && required.every(key => hasValue(predictions[key]))
        && Array.isArray(predictions.compute_budgets) && new Set(predictions.compute_budgets).size >= 3
        && predictions.compute_budgets.every(value => Number.isFinite(value) && value > 0)
        && Number.isInteger(predictions.repetitions) && predictions.repetitions >= 5
        && Number.isFinite(predictions.minimum_worthwhile_gain) && predictions.minimum_worthwhile_gain > 1
        && new Set(predictions.predictions.map(item => item?.method)).size === facts.prediction_count
        && predictions.predictions.every(item => item && menu.includes(item.method)
          && Number.isFinite(item.expected_speedup_interval?.low) && item.expected_speedup_interval.low > 0
          && Number.isFinite(item.expected_speedup_interval?.high)
          && item.expected_speedup_interval.high >= item.expected_speedup_interval.low)
      if (!complete) return reject(check)
      check = 'compute_points_incomplete'
      const completePoints = predictions.predictions.every(item => Array.isArray(item.outcome_vs_compute_points)
        && predictions.compute_budgets.every(budget => item.outcome_vs_compute_points.some(point => point
          && point.compute_budget === budget && hasValue(point.predicted_outcome) && hasValue(point.uncertainty))))
      if (!completePoints) return reject(check)
      if (predictions.outputs_stochastic) {
        check = 'stochastic_equivalence_invalid'
        const seeds = predictions.paired_seed_tests
        const rule = predictions.confidence_rule?.equivalence
        const metrics = predictions.equivalence_metrics
        if (seeds?.kind !== 'paired_median' || !Array.isArray(seeds.seeds) || seeds.seeds.length < 2
          || !seeds.seeds.every(Number.isInteger) || new Set(seeds.seeds).size !== seeds.seeds.length
          || rule?.kind !== 'paired_median' || !Number.isFinite(rule.confidence) || rule.confidence < 0.5 || rule.confidence >= 1
          || !Array.isArray(metrics) || !metrics.length || !metrics.every(metric => {
            const tolerance = typeof metric?.tolerance === 'number' ? metric.tolerance : metric?.tolerance?.abs
            return typeof metric?.name === 'string' && metric.name.trim()
              && typeof metric.source === 'string' && metric.source.trim()
              && Number.isFinite(tolerance) && tolerance > 0
              && (typeof metric.tolerance === 'number' || Object.keys(metric.tolerance).length === 1)
              && !/\b(?:exact|bitwise)\b/i.test(JSON.stringify({ name: metric.name, kind: metric.kind,
                rule: metric.rule, comparison: metric.comparison }))
          })) return reject(check)
      }
      check = 'bounds_coverage_invalid'
      const feasible = menu.filter(method => bounds[method].feasible)
      const infeasible = menu.filter(method => !bounds[method].feasible)
      const excluded = predictions.infeasible_methods
      const validCoverage = facts.prediction_count === feasible.length
        && feasible.every(method => predictions.predictions.some(item => item?.method === method))
        && Array.isArray(excluded) && excluded.length === infeasible.length
        && new Set(excluded.map(item => item?.method)).size === excluded.length
        && excluded.every(item => item && infeasible.includes(item.method)
          && typeof item.reason === 'string' && item.reason.trim())
      if (!validCoverage) return reject(check)
      check = 'interval_bounds_invalid'
      const validIntervals = predictions.predictions.every(item => {
        const { low, high } = item.expected_speedup_interval
        const bound = bounds[item.method].bound
        return high <= bound && high - low <= bound - 1
      })
      if (!validIntervals) return reject(check)
      if (!(feasible.length < 2 || new Set(predictions.predictions.map(item =>
          JSON.stringify([item.expected_speedup_interval.low, item.expected_speedup_interval.high]))).size > 1)) return reject('intervals_identical')

      check = 'seal_write_failed'
      // Sort recursively, preserving array order. Hash the exact UTF-8 bytes, with no spaces/newline.
      const canonical = value => value === null || typeof value !== 'object' ? JSON.stringify(value)
        : Array.isArray(value) ? `[${value.map(canonical).join(',')}]`
          : `{${Object.keys(value).sort().map(key => `${JSON.stringify(key)}:${canonical(value[key])}`).join(',')}}`
      const bytes = canonical(predictions)
      const hash = value => createHash('sha256').update(value).digest('hex')
      writeFileSync(predictionPath, bytes)
      const seals = path.join(C, 'seals')
      mkdirSync(seals, { recursive: true })
      let number = Math.max(0, ...readdirSync(seals).filter(name => /^\d{4,}\.json$/.test(name)).map(name => Number(name.slice(0, -5)))) + 1
      let receiptPath
      for (;;) {
        const id = String(number++).padStart(4, '0')
        receiptPath = path.join(seals, `${id}.json`)
        const frozenPath = path.join(seals, `${id}.predictions.json`)
        try {
          // Exclusive creation also handles concurrent writers and interrupted prior seals.
          writeFileSync(frozenPath, bytes, { flag: 'wx', mode: 0o444 })
          writeFileSync(receiptPath, JSON.stringify({ sha256: hash(bytes), path: frozenPath, utc: new Date().toISOString() }), { flag: 'wx', mode: 0o444 })
          break
        } catch (error) {
          if (error.code !== 'EEXIST') throw error
        }
      }
      check = 'seal_verification_failed'
      facts.seal_present = existsSync(receiptPath)
      const receipt = readJSON(receiptPath)
      facts.seal_verified = hash(readFileSync(receipt.path)) === receipt.sha256
        && hash(readFileSync(predictionPath)) === receipt.sha256
      if (!facts.seal_verified) return reject(check)
      return facts.prediction_count > 0 ? { status: 'PASS', facts, reason_codes: [] }
        : reject('no_feasible_methods')
    } catch {
      return reject(check)
    }
  }
  async function propose() {
    if (input.stub?.propose != null) return stub('propose')
    const facts = { ...nullFacts('propose'), method: 'none', votes_approve: 0,
      votes_total: 5, vote_share: 0, gate_pass: false, tokens_known: false, gpu_busy_known: false }
    const predictionPath = path.join(A, 'PREDICTIONS.json')
    const proposalPath = path.join(A, 'proposal.json')
    const gatePath = path.join(A, 'GATE.json')
    const hash = bytes => createHash('sha256').update(bytes).digest('hex')
    let predictions
    // Verify both copies against the latest immutable receipt before reading scientific inputs.
    try {
      const seals = path.join(C, 'seals')
      const latest = readdirSync(seals).filter(name => /^\d{4,}\.json$/.test(name))
        .sort((a, b) => Number(a.slice(0, -5)) - Number(b.slice(0, -5))).at(-1)
      if (!latest) return failure(facts, 'other')
      const receipt = readJSON(path.join(seals, latest))
      const bytes = readFileSync(predictionPath)
      if (hash(bytes) !== receipt.sha256 || hash(readFileSync(receipt.path)) !== receipt.sha256) {
        return failure(facts, 'other')
      }
      predictions = JSON.parse(bytes.toString('utf8'))
    } catch { return failure(facts, 'other') }
    // A completed decision cannot be voted on again within this run.
    if (existsSync(gatePath)) return failure(facts, 'other')
    const finish = error_class => {
      writeFileSync(gatePath, JSON.stringify(facts, null, 2) + '\n')
      return facts.gate_pass ? { status: 'PASS', facts } : failure(facts, error_class)
    }
    try {
      const profile = readJSON(path.join(A, 'profile-packet.json'))
      const bounds = readJSON(path.join(A, 'bounds.json'))
      let allocation, probe
      try { allocation = readJSON(path.join(C, 'box.json')) } catch { /* Unknown inventory fails guards. */ }
      try { probe = readJSON(path.join(A, 'results', 'probe', 'probe.json')) } catch { /* Same. */ }
      const count = value => Number.isInteger(value) && value >= 0 ? value : null
      const allocationCount = count(allocation?.gpu_count)
        ?? count(Number(/^gpu_(\d+)x_/.exec(allocation?.type)?.[1]))
      const probeCount = Array.isArray(probe?.nvidia?.gpus) ? probe.nvidia.gpus.length : null
      const available = allocationCount === null || probeCount === null ? 0 : Math.min(allocationCount, probeCount)
      if (!Array.isArray(predictions.predictions)
        || !Number.isFinite(predictions.minimum_worthwhile_gain) || predictions.minimum_worthwhile_gain <= 1
        || new Set(predictions.predictions.map(item => item?.method)).size !== predictions.predictions.length) {
        return finish('parse')
      }
      const ranked = []
      for (const prediction of predictions.predictions) {
        const method = prediction?.method, limit = bounds[method]
        const { low, high } = prediction?.expected_speedup_interval || {}
        if (!menu.includes(method) || !limit || !Number.isFinite(limit.bound)
          || !Number.isFinite(low) || low <= 0 || !Number.isFinite(high) || high < low) return finish('parse')
        if (!limit.feasible || limit.bound < 1.05) continue
        const midpoint = low / 2 + high / 2
        const gpus_required = method === 'multi-GPU' ? Math.max(2, limit.k) : 1
        ranked.push({ method, bounds: limit, prediction, expected_speedup: midpoint,
          rank_score: Math.min(midpoint, limit.bound), gpus_required,
          resource_guard_pass: Number.isInteger(gpus_required) && gpus_required <= available })
      }
      ranked.sort((a, b) => b.rank_score - a.rank_score || menu.indexOf(a.method) - menu.indexOf(b.method))
      const methods = ranked.filter(item => item.resource_guard_pass)
      const packet = {
        ranked_methods: methods.map(({ method, bounds }) => ({ method, bounds })),
        stage_to_method: profile.stages.map(stage => {
          const mapped = Object.values(bounds).flatMap(limit => limit.stages || []).find(row => row.stage === stage.stage)
          return { stage: stage.stage, wall_fraction: Math.min(1, stage.wall_s / profile.total_wall_s),
            mean_gpu_util: stage.mean_gpu_util ?? null, methods: mapped?.methods || [] }
        }),
        bounds,
        sealed_equivalence_rule: Object.fromEntries(['outputs_stochastic', 'equivalence_metrics',
          'paired_seed_tests', 'sample_sizes'].map(key => [key, predictions[key]])),
      }
      packet.sealed_equivalence_rule.confidence_rule = predictions.confidence_rule?.equivalence ?? predictions.confidence_rule
      writeFileSync(path.join(A, 'propose-packet.json'), JSON.stringify(packet, null, 2) + '\n')
      if (!methods.length) return finish('numeric')
      const { validate } = await import(path.resolve('idea/schema.js'))
      const strings = { type: 'array', items: { type: 'string' } }
      const proposalSchema = { type: 'object', additionalProperties: false,
        required: ['method', 'rationale', 'plan_steps', 'files_expected', 'risks'],
        properties: { method: { enum: methods.map(item => item.method) }, rationale: { type: 'string' },
          plan_steps: strings, files_expected: strings, risks: strings } }
      rmSync(proposalPath, { force: true })
      const evidence = JSON.stringify(packet)
      const reply = await agent(`Choose one feasible method from ranked_methods in this prepared packet.
Read only the packet embedded below. Never read other files, search, access the box, run workloads, or implement code.
ranked_methods are ordered by sealed predicted speedup capped by the supplied bounds and have already passed deterministic GPU resource guards.
Write only ${JSON.stringify(proposalPath)}, matching this schema: ${JSON.stringify(proposalSchema)}.
Explain profile evidence, overheads, scientific equivalence risks, and a concrete implementation plan. Keep the sealed method and protocol unchanged.
Prepared packet:\n${evidence}
Return a short completion acknowledgement.`,
        { label: 'propose', agentType: 'ls-writer', model: 'sonnet', repairable: false, fresh: true })
      if (reply == null) return finish('parse')
      const proposal = readJSON(proposalPath)
      if (validate(proposalSchema, proposal).length || !proposal.rationale.trim()
        || !proposal.plan_steps.length || !proposal.files_expected.length
        || ['plan_steps', 'files_expected', 'risks'].some(key => proposal[key].some(item => !item.trim()))) return finish('parse')
      const chosen = methods.find(item => item.method === proposal.method)
      facts.method = chosen.method
      facts.expected_speedup = chosen.expected_speedup
      const reasons = ['exceeds_bound', 'not_parallelisable', 'changes_method', 'equivalence_risk',
        'resource_mismatch', 'weak_profile_evidence', 'other']
      const voteSchema = { type: 'object', additionalProperties: false, required: ['vote', 'reason_codes'],
        properties: { vote: { enum: ['approve', 'reject', 'abstain'] },
          reason_codes: { type: 'array', items: { enum: reasons } } } }
      const votesDirectory = path.join(A, 'votes')
      mkdirSync(votesDirectory, { recursive: true })
      // Queue all five siblings together for x-<raid>-skeptic-<i>of5 names and fresh runner sessions.
      const votes = await Promise.all(Array.from({ length: 5 }, async (_, index) => {
        const votePath = path.join(votesDirectory, `${index + 1}.json`)
        rmSync(votePath, { force: true })
        let vote = null
        try {
          vote = await agent(`Independent ballot ${index + 1} of 5. Review this proposal once.
Use only the embedded prepared packet and proposal. Never read files, other votes, or other sessions; do not search or use tools.
ranked_methods have already passed deterministic GPU resource guards. Approve only if the method stays within its bound, is parallelisable as planned, preserves the sealed scientific equivalence rule, and has adequate stage evidence.
Return only vote and reason_codes using the supplied schema. Missing evidence warrants reject or abstain. Vote share is not a calibrated probability.
Prepared packet:\n${evidence}\nProposal:\n${JSON.stringify(proposal)}`,
            { label: 'skeptic', agentType: 'qt-bare', model: 'haiku', schema: voteSchema, repairable: false, fresh: true })
        } catch { /* A failed call counts against approval; never replace it. */ }
        if (validate(voteSchema, vote).length) vote = null
        writeFileSync(votePath, JSON.stringify(vote, null, 2) + '\n')
        return vote
      }))
      facts.votes_approve = votes.filter(vote => vote?.vote === 'approve').length
      facts.vote_share = facts.votes_approve / 5
      facts.gate_pass = facts.votes_approve >= 4 && chosen.prediction.expected_speedup_interval.high >= predictions.minimum_worthwhile_gain
        && chosen.prediction.expected_speedup_interval.high <= chosen.bounds.bound && chosen.resource_guard_pass
      return finish('numeric')
    } catch { return finish('parse') }
  }
  async function implement() {
    if (input.stub?.implement != null) return stub('implement')
    const { default: run } = await import(path.resolve('m5/implement.js'))
    return run({ A, C, root, agent, exec, boxCommand, remoteDirectory, executionTimeout, failure, nullFacts })
  }
  async function evaluate() {
    if (input.stub?.evaluate != null) return stub('evaluate')
    const { default: run } = await import(path.resolve('m5/evaluate.js'))
    return run({ A, C, exec, boxCommand, remoteDirectory, executionTimeout, nullFacts })
  }
  function takeaways() { return stub('takeaways') }

  const stages = []
  let stageUSD = 0
  let stopped_at = null
  for (const run of [intake, reproduce, profile, seal, propose, implement, evaluate, takeaways]) {
    const stage = run.name
    phase(stage)
    stageReceipts = []
    const journalOffset = journalText().length
    const started = performance.now(), before = agent.usage?.()
    const result = stopped_at && stage !== 'takeaways'
      ? { status: 'SKIPPED', facts: nullFacts(stage) }
      : await run()
    const timeouts = stageReceipts.filter(receipt => receipt.rc === 124 || receipt.timed_out === true)
    if (timeouts.length) {
      result.facts.timed_out = true
      result.facts.budget_s = timeouts.at(-1).budget_s
      result.facts.overrun = timeouts.some(receipt => receipt.overrun === true)
    }
    const v1 = { ...result.v1, wall_s: (performance.now() - started) / 1000 }
    const families = answeringFamilies(journalOffset)
    v1.model_family = families.at(-1) ?? 'none'
    v1.gpu_s = stageReceipts.reduce((sum, receipt) => sum + (nonnegative(receipt.gpu_busy_s) ? receipt.gpu_busy_s : 0), 0)
    v1.usd = box && nonnegative(box.price_usd_h)
      ? stageReceipts.reduce((sum, receipt) => sum + (nonnegative(receipt.wall_s) ? receipt.wall_s : 0), 0) / 3600 * box.price_usd_h : 0
    stageUSD += v1.usd
    if (stageReceipts.length) result.facts.gpu_busy_known = stageReceipts.every(receipt => receipt.gpu_busy_known === true)
    if (stage === 'takeaways') {
      // A down during the run may have completed the allocation since the snapshot.
      try {
        const current = readJSON(boxPath)
        if (current && typeof current === 'object' && (!box || (current.started_utc === box.started_utc
          && current.type === box.type && current.region === box.region && current.price_usd_h === box.price_usd_h))) {
          box = current
          writeFileSync(path.join(C, 'box.json'), JSON.stringify(box) + '\n')
        }
      } catch { /* The initial snapshot remains sufficient for an active allocation. */ }
      result.facts.run_box_usd = result.status === 'SKIPPED' ? null : runBoxUSD(stageUSD)
    }
    const after = agent.usage?.()
    if (before && after && after.calls > before.calls) {
      v1.tokens_in = after.tokens_in - before.tokens_in
      v1.tokens_out = after.tokens_out - before.tokens_out
      result.facts.tokens_known = after.unknown === before.unknown
    }
    mkdirSync(path.join(C, 'stages'), { recursive: true })
    writeFileSync(path.join(C, 'stages', `${stage}.json`), JSON.stringify({ stage, status: result.status,
      ...v1, ...(stage === 'seal' ? { reason_codes: result.reason_codes ?? [] } : {}),
      notes: new Set(families).size > 1 ? ['multiple_model_families'] : [] }) + '\n')
    await exec('python3', ['m5/signatures.py', 'emit', '--dir', S, '--stage', stage, '--status', result.status,
      '--facts', JSON.stringify(result.facts), '--v1', JSON.stringify(v1)])
    stages.push({ stage, status: result.status })
    log(`${stage}: ${result.status}`)
    if (!stopped_at && result.status !== 'PASS') stopped_at = stage
  }
  await exec('python3', ['m5/operator_takeaway.py', S, '--raid', raid])
  return { stages, stopped_at }
})()
