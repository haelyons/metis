// wf.js script. Only intake and seal are real; other stages remain placeholders.
const meta = { name: 'm5', description: 'Explicit-run-root scientific pipeline skeleton' }

return (async () => {
  const { default: path } = await import('node:path')
  const { mkdirSync, existsSync, readFileSync, writeFileSync, readdirSync } = await import('node:fs')
  const { createHash } = await import('node:crypto')
  const { execFile } = await import('node:child_process')
  const { promisify } = await import('node:util')
  const exec = promisify(execFile)
  const input = (typeof args === 'string' ? JSON.parse(args) : args) || {}
  if (!input.run_root || !input.tag) throw new Error('m5 needs run_root and tag')
  const root = path.resolve(input.run_root)
  const A = path.join(root, 'agent'), S = path.join(root, 'operator'), C = path.join(root, 'control')
  for (const dir of [A, S, C]) mkdirSync(dir, { recursive: true })
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
- anchors.json: an array of credible independently published reference anchors, each with id, quantity, published_value, tolerance, source (citation). Do not count self-generated checks or unsupported references.
- data.json: required inputs, availability, access instructions, licences, pins/hashes, splits and seeds; distinguish generated inputs from missing data.
- baseline.json: repo, commit or immutable pin, build_commands, run_commands, published_configuration; cite their sources. Do not run builds or workloads.
- EXECUTION.json: representative_scale, inputs, outputs, timing_scope; specify the real representative workload and scoring interface, not a toy extrapolation.
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
      const validAnchors = Array.isArray(anchors) && anchors.every(anchor => anchor &&
        ['id', 'quantity', 'published_value', 'tolerance', 'source'].every(key => hasValue(anchor[key])))
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
  function reproduce() { return stub('reproduce') }
  function profile() { return stub('profile') }
  async function seal() {
    if (input.stub?.seal != null) return stub('seal')
    const facts = { ...nullFacts('seal'), seal_present: false, seal_verified: false,
      prediction_count: 0, tokens_known: false, gpu_busy_known: false }
    const predictionPath = path.join(A, 'PREDICTIONS.json')
    const profilePath = path.join(A, 'profile-packet.json')
    const prompt = `Seal a prospective scientific evaluation protocol in one narrow pass.
Read ${JSON.stringify(path.join(A, 'intake'))}/* only${existsSync(profilePath) ? `, plus ${JSON.stringify(profilePath)}` : '. No profile packet exists; profiling is currently a stub'}.
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
    const result = stopped_at && stage !== 'takeaways'
      ? { status: 'SKIPPED', facts: nullFacts(stage) }
      : await run()
    await exec('python3', ['m5/signatures.py', 'emit', '--dir', S, '--stage', stage, '--status', result.status, '--facts', JSON.stringify(result.facts)])
    stages.push({ stage, status: result.status })
    log(`${stage}: ${result.status}`)
    if (!stopped_at && result.status !== 'PASS') stopped_at = stage
  }
  return { stages, stopped_at }
})()
