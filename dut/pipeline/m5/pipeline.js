// wf.js script. Intake, reproduce, profile and seal are real; later stages are placeholders.
const meta = { name: 'm5', description: 'Explicit-run-root scientific pipeline skeleton' }

return (async () => {
  const { default: path } = await import('node:path')
  const { mkdirSync, existsSync, readFileSync, writeFileSync, readdirSync, rmSync } = await import('node:fs')
  const { createHash, randomUUID } = await import('node:crypto')
  const { execFile } = await import('node:child_process')
  const { promisify } = await import('node:util')
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
- EXECUTION.json: representative_scale, inputs, outputs, timing_scope; specify the real representative workload and scoring interface, not a toy extrapolation. Optional timeout_s defaults to 3600 seconds; optional timeouts {setup, run_anchors, profile} override it per script. All timeouts must be positive integers <=999999999.
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
    error_class, exit_code: error_class === 'anchor' ? 4 : 2,
  } })
  function executionTimeout(name) {
    const execution = readJSON(path.join(A, 'intake', 'EXECUTION.json'))
    const seconds = execution.timeouts?.[name] ?? execution.timeout_s ?? 3600
    if (!Number.isInteger(seconds) || seconds <= 0 || seconds > 999999999) throw new Error('invalid timeout')
    return seconds
  }
  async function boxCommand(name, command, destination, timeout) {
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
  const harnessRules = 'Run the published build and binary and read measurements from its OUTPUT. Never parse or assert on source text. Measurement checks must fail only on missing or invalid output; the pipeline scores measured values against anchors.'
  let boxProbe
  const boxProbePrompt = () => `Box probe (collected by the pipeline before harness generation):
${JSON.stringify(boxProbe, null, 2)}
Use the probe's discovered paths and versions. Never hard-code a toolkit path the probe did not find, even if the brief suggests one. If a required tool is missing, install it with apt only from sources the probe lists; do not add repositories or assume a package exists. Commented source lines are not enabled repositories. If apt cannot supply it, use pip for cmake only; otherwise fail with a clear message.`
  async function collectBoxProbe(timeout) {
    const destination = path.join(A, 'results', 'probe')
    const probePath = path.join(destination, 'probe.json')
    rmSync(probePath, { force: true })
    const bytes = readFileSync('m5/box_probe.sh').toString('base64')
    const uploaded = await boxCommand('upload', `set -e\nmkdir -p harness out\nprintf %s ${quote(bytes)} | base64 -d > harness/box_probe.sh`, destination, timeout)
    if (uploaded.error || uploaded.rc !== 0) throw new Error('probe upload failed')
    const result = await boxCommand('probe', 'set -e\nrm -f out/probe.json\nbash harness/box_probe.sh', destination, timeout)
    if (result.error || result.rc !== 0) throw new Error('probe failed')
    const content = readFileSync(path.join(destination, 'out', 'probe.json'), 'utf8')
    const probe = JSON.parse(content)
    if (!probe || typeof probe !== 'object' || Array.isArray(probe)) throw new Error('invalid probe')
    writeFileSync(probePath, content)
    boxProbe = probe
  }
  async function runHarness(name, operation, destination, timeout) {
    const command = `bash harness/${name}`
    const result = await boxCommand(operation, command, destination, timeout)
    if (result.error || result.rc === 0) return result
    let tail
    try {
      const lines = readFileSync(result.log, 'utf8').trimEnd().split('\n')
      tail = lines.slice(-200).join('\n')
    } catch { return result }
    const repair = await agent(`${name} failed (rc ${result.rc}). Repair only ${JSON.stringify(path.join(harnessDirectory, name))} using intake evidence. Preserve the published pin, configuration and stock image; sudo only for apt. ${harnessRules} Never read experiments/, operator/, or control/. Do not run workloads locally or access the box. This is the only repair attempt for this script.
${boxProbePrompt()}
Log tail (at most 200 lines):\n${tail}`,
      { label: name === 'setup.sh' ? 'harness-repair' : `${operation}-repair`, agentType: 'ls-writer', model: 'sonnet', retry: 1 })
    if (repair == null) return result
    const uploaded = await uploadHarness([name], destination, executionTimeout('setup'))
    if (uploaded.error || uploaded.rc !== 0) return { error: 'infra' }
    return boxCommand(operation, command, destination, timeout)
  }
  async function reproduce() {
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
    } catch { return failure(facts, 'infra') }
    const prompt = `Write a baseline harness from ${JSON.stringify(path.join(A, 'intake'))}/*.
Never read experiments/, operator/, or control/. Write only under ${JSON.stringify(harnessDirectory)}.
The operator already started the dev box. Do not start, stop, or access it; the pipeline runs your scripts.
${harnessRules}
${boxProbePrompt()}
Write three self-contained bash scripts, invoked from a shared remote working directory with bash harness/<name>:
- setup.sh: build/install the published baseline at its exact intake pin in the stock image. Use sudo only for apt. Preserve stock torch and published source/configuration. Stage source in baseline-published/ and inputs in data/. Do not silently substitute or tune the baseline. Make setup safe to retry once in this directory.
- run_anchors.sh: run the published anchor protocol at the real representative scale declared in EXECUTION.json. Write out/anchors_measured.json as {anchor_id: measured_number}, one finite number per intake anchor. Never copy published values as measurements.
- profile.sh: run that same baseline once at representative scale, with stage wall timers and nvidia-smi sampling. Write out/profile/stages.json as [{stage, wall_s, gpu_s}] (finite nonnegative seconds, gpu_s null when unavailable), and out/profile/total_wall_s.json as {total_wall_s} (finite positive seconds). Save raw telemetry under out/profile/. Use critical-path stage wall times without double-counting overlap. Do not invent GPU timings or replace unavailable GPU timings with allocated time.
Create output directories, preserve logs, and exit nonzero on failure. Read all intake files for pins, commands, data, scale and protocol. Do not run builds or workloads locally.
Return a short completion acknowledgement; the pipeline reads the scripts itself.`
    try {
      mkdirSync(harnessDirectory, { recursive: true })
      const reply = await agent(prompt, { label: 'harness', agentType: 'ls-writer', model: 'sonnet' })
      if (reply == null) return failure(facts, 'parse')
      const uploaded = await uploadHarness(['setup.sh', 'run_anchors.sh', 'profile.sh'], destination, setupTimeout)
      if (uploaded.error || uploaded.rc !== 0) return failure(facts, 'infra')
      const setup = await runHarness('setup.sh', 'setup', destination, setupTimeout)
      if (setup.error) {
        facts.stock_verified = setup.rc === 0
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
    try {
      rmSync(path.join(A, 'profile-packet.json'), { force: true })
      const destination = path.join(A, 'results', 'profile')
      const result = await runHarness('profile.sh', 'profile', destination, executionTimeout('profile'))
      if (result.error) return failure(facts, result.error)
      if (result.rc !== 0) return failure(facts, 'parse')
      const directory = path.join(destination, 'out', 'profile')
      const stages = readJSON(path.join(directory, 'stages.json'))
      const { total_wall_s } = readJSON(path.join(directory, 'total_wall_s.json'))
      if (!Number.isFinite(total_wall_s) || total_wall_s <= 0 || !Array.isArray(stages) || !stages.length
        || !stages.every(item => item && typeof item.stage === 'string' && item.stage.trim()
          && Number.isFinite(item.wall_s) && item.wall_s >= 0
          && (item.gpu_s === null || (Number.isFinite(item.gpu_s) && item.gpu_s >= 0)))) return failure(facts, 'parse')
      const timedWall = stages.reduce((sum, item) => sum + item.wall_s, 0)
      if (!Number.isFinite(timedWall)) return failure(facts, 'parse')
      facts.profile_complete = true
      facts.timed_fraction = Math.min(1, timedWall / total_wall_s)
      facts.gpu_telemetry = stages.some(item => item.gpu_s !== null)
      writeFileSync(path.join(A, 'profile-packet.json'), JSON.stringify({
        stages: stages.map(({ stage, wall_s, gpu_s }) => ({ stage, wall_s, gpu_s,
          wall_fraction: Math.min(1, wall_s / total_wall_s) })), total_wall_s,
        timed_fraction: facts.timed_fraction, gpu_telemetry: facts.gpu_telemetry,
      }, null, 2) + '\n')
      return facts.timed_fraction >= 0.9 ? { status: 'PASS', facts } : failure(facts, 'parse')
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
    const prompt = `Seal a prospective scientific evaluation protocol in one narrow pass.
Read ${JSON.stringify(path.join(A, 'intake'))}/* only${existsSync(profilePath) ? `, plus ${JSON.stringify(profilePath)}` : '. No profile packet is available'}.
Never read experiments/, operator/, or control/. Do not search, build, run workloads, or write method code.
Write only ${JSON.stringify(predictionPath)}. Use intake evidence and the profile when present. Do not invent measurements; label assumptions and unavailable evidence explicitly.
The method menu is exactly ${JSON.stringify(menu)}. Include every feasible entry once; exclude infeasible entries with reasons in infeasible_methods. With no feasible entry, write predictions=[] as a negative result.
Amdahl speedup bound for parallel fraction p and worker count n is 1/((1-p)+p/n). Apply it only to recorded timed fractions, include launch/transfer/merge overhead, and declare bounds unavailable if profile evidence is missing. Intervals without measurements are prospective assumptions, not measured gains.
Write an object with these fields:
- predictions: array of {method, expected_speedup_interval: {low, high}, outcome_vs_compute_points}. Each point is {compute_budget, predicted_outcome, uncertainty}. Include all sealed compute budgets for each method.
- equivalence_metrics: quantities, scientific tolerances, and sources from requirements or baseline variability, never method outputs. Lack of significance is not equivalence.
- paired_seed_tests: stochastic paired-seed test and fixed seeds, or an explicit scientifically justified deterministic/not-applicable declaration.
- sample_sizes and confidence_rule: powered equivalence sample sizes and the confidence decision rule.
- hardware_cost_basis, timing_scope, minimum_worthwhile_gain (a speedup ratio >1).
- evaluation_inputs and splits: fixed input identities/pins, held-out splits and seeds, or explicit generated-input specifications.
- compute_budgets: at least three distinct positive numeric budgets, with units in hardware_cost_basis.
- repetitions: integer >=5 timing pairs; warmup: fixed warmup protocol; scheduling_order: paired randomisation protocol; equal_outcome_target: the fixed scientific target.
Define the complete protocol now, before method code exists. Scope/tolerance changes require a new sealed run.
Return a short completion acknowledgement; the script reads and seals the file itself.`
    try {
      const reply = await agent(prompt, { label: 'seal', agentType: 'ls-writer', model: 'sonnet' })
      if (reply == null) return { status: 'FAIL', facts }
      const predictions = readJSON(predictionPath)
      if (!predictions || !Array.isArray(predictions.predictions)) return { status: 'FAIL', facts }
      facts.prediction_count = predictions.predictions.length
      const required = ['equivalence_metrics', 'paired_seed_tests', 'sample_sizes', 'confidence_rule',
        'hardware_cost_basis', 'timing_scope', 'minimum_worthwhile_gain', 'evaluation_inputs', 'splits',
        'compute_budgets', 'repetitions', 'warmup', 'scheduling_order', 'equal_outcome_target']
      const complete = required.every(key => hasValue(predictions[key]))
        && Array.isArray(predictions.compute_budgets) && new Set(predictions.compute_budgets).size >= 3
        && predictions.compute_budgets.every(value => Number.isFinite(value) && value > 0)
        && Number.isInteger(predictions.repetitions) && predictions.repetitions >= 5
        && Number.isFinite(predictions.minimum_worthwhile_gain) && predictions.minimum_worthwhile_gain > 1
        && new Set(predictions.predictions.map(item => item.method)).size === facts.prediction_count
        && predictions.predictions.every(item => menu.includes(item.method)
          && Number.isFinite(item.expected_speedup_interval?.low) && item.expected_speedup_interval.low > 0
          && Number.isFinite(item.expected_speedup_interval?.high)
          && item.expected_speedup_interval.high >= item.expected_speedup_interval.low
          && Array.isArray(item.outcome_vs_compute_points)
          && predictions.compute_budgets.every(budget => item.outcome_vs_compute_points.some(point => point
            && point.compute_budget === budget && hasValue(point.predicted_outcome) && hasValue(point.uncertainty))))
      if (!complete) return { status: 'FAIL', facts }

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
      facts.seal_present = existsSync(receiptPath)
      const receipt = readJSON(receiptPath)
      facts.seal_verified = hash(readFileSync(receipt.path)) === receipt.sha256
        && hash(readFileSync(predictionPath)) === receipt.sha256
      return { status: facts.seal_verified && facts.prediction_count > 0 ? 'PASS' : 'FAIL', facts }
    } catch {
      return { status: 'FAIL', facts }
    }
  }
  function propose() { return stub('propose') }
  function implement() { return stub('implement') }
  function evaluate() { return stub('evaluate') }
  function takeaways() { return stub('takeaways') }

  const stages = []
  let stopped_at = null
  for (const run of [intake, reproduce, profile, seal, propose, implement, evaluate, takeaways]) {
    const stage = run.name
    phase(stage)
    const started = performance.now(), before = agent.usage?.()
    const result = stopped_at && stage !== 'takeaways'
      ? { status: 'SKIPPED', facts: nullFacts(stage) }
      : await run()
    const v1 = { ...result.v1, wall_s: (performance.now() - started) / 1000 }
    const after = agent.usage?.()
    if (before && after && after.calls > before.calls) {
      v1.tokens_in = after.tokens_in - before.tokens_in
      v1.tokens_out = after.tokens_out - before.tokens_out
      result.facts.tokens_known = after.unknown === before.unknown
    }
    await exec('python3', ['m5/signatures.py', 'emit', '--dir', S, '--stage', stage, '--status', result.status,
      '--facts', JSON.stringify(result.facts), '--v1', JSON.stringify(v1)])
    stages.push({ stage, status: result.status })
    log(`${stage}: ${result.status}`)
    if (!stopped_at && result.status !== 'PASS') stopped_at = stage
  }
  await exec('python3', ['m5/operator_takeaway.py', S, '--raid', raid])
  return { stages, stopped_at }
})()
