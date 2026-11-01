// wf.js script. Intake through evaluate are real; takeaways remains a placeholder.
const meta = { name: 'm5', description: 'Explicit-run-root scientific pipeline skeleton' }

return (async () => {
  const runStarted = Date.now()
  const { default: path } = await import('node:path')
  const { mkdirSync, existsSync, readFileSync, writeFileSync, readdirSync, rmSync } = await import('node:fs')
  const { createHash, randomUUID } = await import('node:crypto')
  const { execFile } = await import('node:child_process')
  const { promisify } = await import('node:util')
  const { homedir } = await import('node:os')
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
    intake: ['found', 'anchors_count', 'data', 'licence', 'stock_environment', 'size', 'anchored', 'licence_basis'],
    reproduce: ['anchors_passed', 'anchors_total', 'stock_verified', 'tuned_control_valid'],
    profile: ['profile_complete', 'timed_fraction', 'gpu_telemetry', 'headroom'],
    seal: ['seal_present', 'seal_verified', 'prediction_count'],
    propose: ['method', 'expected_speedup', 'votes_approve', 'votes_total', 'vote_share', 'gate_pass',
      'votes_reject', 'votes_abstain', 'outcome'],
    implement: ['patch_applies', 'tests_pass', 'blind_tests', 'launch_review_pass'],
    evaluate: ['validity_pass', 'equivalence_pass', 'performance_pass', 'equal_cost', 'speedup_published', 'speedup_tuned', 'cost_ratio', 'prediction_ratio', 'curve_points'],
    takeaways: ['operator_written', 'research_written', 'teardown_confirmed'],
  }
  const nullFacts = stage => Object.fromEntries([...fields[stage], 'tokens_known', 'gpu_busy_known'].map(key => [key, null]))
  const stub = stage => ({ status: input.stub?.[stage] ?? 'PASS', facts: nullFacts(stage) })

  const intakeSchema = {
    type: 'object', additionalProperties: false,
    required: fields.intake.filter(key => key !== 'anchored' && key !== 'licence_basis'),
    properties: {
      found: { type: 'boolean' }, anchors_count: { type: 'integer', minimum: 0 },
      anchored: { type: 'boolean' },
      data: { enum: ['available', 'partial', 'unavailable', 'unknown'] },
      licence: { enum: ['permitted', 'restricted', 'unknown'] },
      licence_basis: { enum: ['unreachable', 'none', 'owner', 'distribution', 'explicit'] },
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
    const fail = () => {
      const blockers = []
      if (facts.licence === 'restricted') blockers.push('licence')
      if (['partial', 'unavailable', 'unknown'].includes(facts.data)) blockers.push('data_unavailable')
      if (facts.stock_environment === false) blockers.push('env_irreproducible')
      return { status: 'FAIL', facts, v1: { blockers: blockers.length ? blockers : ['none'] } }
    }
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
- anchors.json: an array, possibly empty, of independently published anchors and references, each with a unique non-empty string id, non-empty quantity and source (citation), finite numeric published_value, and tolerance. Tolerance must be a nonnegative finite number (absolute), {"abs": x}, or {"rel": x}; relative tolerance means x * abs(published_value). Optional comparison is one of "==" (default), ">", ">=", "<", "<=". When the published criterion is a threshold, supply comparison so measured_value comparison published_value expresses that criterion; tolerance is ignored for inequalities and may be 0 or null. Without a published acceptance criterion, record the published value as a reference with comparison "==" and tolerance null; never invent tolerances or convert published uncertainty into tolerance. Optional uncertainty is null or exactly {kind, value}, with kind standard_error, standard_deviation or interval_halfwidth and finite nonnegative value. Uncertainty never affects scoring. Do not count self-generated checks or unsupported references.
- data.json: required inputs, availability, access instructions, licences, pins/hashes, splits and seeds; distinguish generated inputs from missing data.
- baseline.json: non-empty values for JSON keys "repo", "build_commands", "run_commands", "published_configuration", and "commit" or "pin"; cite their sources. "pin" is any non-empty immutable identifier, such as a release, tag or content hash, when no commit exists. build_commands lists every command that builds or installs the baseline, including package-manager installs of released binaries, and is never empty. Do not run builds or workloads.
- EXECUTION.json: non-empty values for JSON keys "representative_scale", "inputs", "outputs", "timing_scope"; specify the real representative workload and scoring interface, not a toy extrapolation. Optional stage_budgets_s records estimates for setup, anchors and profile, and overrides per-script seconds for method_setup, method_run, tests and evaluate. Those overrides precede args budgets; defaults are method_setup=1200, method_run=1200, tests=900 and evaluate=2400. Setup, anchors and profile use args budgets when present, otherwise the time left before the run ceiling, not a target (args.run_ceiling_s, default 43200 seconds). Supplied args budgets are ${JSON.stringify(input.stage_budgets_s || {})}. All supplied budgets must be positive integers <=999999999. Choose one fixed scale; no scale search or doubling loops. Scripts must finish well within their budgets.
The completeness check reads only these JSON key names in baseline.json and EXECUTION.json, so an equivalent value under another key does not count.
Return only the facts matching the supplied schema. anchors_count must equal the number of items written, including references. Optional anchored is true exactly when at least one item is an anchor rather than a reference; the pipeline derives it from anchors.json.
found means a public benchmark with executable published code, command and inputs. A benchmark without published tolerances qualifies; record its published values as references without inventing tolerances.
data=available only when all required data is accessible. licence=permitted only when intended use is allowed.
When permission is not established, licence="unknown" stays "unknown" and does not stop the run; licence="restricted" does stop the run. Record licence and licence_basis as the evidence shows; never relabel ambiguous coverage as permission.
Report optional licence_basis for the least-covered item among the benchmark code and its required inputs. Use the first value that applies to any item, in this fixed order: "unreachable" (the licence evidence for the item could not be fetched), "none" (no licence, terms of use or owner statement found for the item), "owner" (the item's only basis is a permission stated by the run's owner in the brief), "distribution" (the item's only basis is a licence of the repository, package or archive that distributes it, and that licence does not state that it covers the item), "explicit" (a licence or terms of use states that it covers the item, by name, by path, or as the whole repository, package or archive). This fact records the basis only; it never changes the gate, licence, blockers or any other fact.
stock_environment=true means provisionally feasible on the stock image, false means incompatible, null means unknown pending reproduction.
size is data plus peak working set: tiny <=1 GiB, small <=10 GiB, medium <=100 GiB, large >100 GiB, otherwise unknown.
Gate: complete files, found, available required data, licence is not "restricted", and stock_environment is not false. Missing published tolerances do not block. Missing evidence must stay unknown.`
    try {
      const reply = await agent(prompt, { label: 'intake', agentType: 'ls-writer', model: 'sonnet', schema: intakeSchema })
      // Whitelist facts: no benchmark content or arbitrary reply keys can reach S.
      if (reply != null) {
        for (const key of intakeSchema.required) facts[key] = reply[key]
        facts.licence_basis = reply.licence_basis ?? null
      }
      const anchors = readJSON(path.join(directory, 'anchors.json'))
      const validAnchors = Array.isArray(anchors) && new Set(anchors.map(anchor => anchor?.id)).size === anchors.length
        && anchors.every(anchor => anchor && typeof anchor.id === 'string' && anchor.id.trim()
          && ['quantity', 'source'].every(key => hasValue(anchor[key]))
          && Number.isFinite(anchor.published_value)
          && ['==', '>', '>=', '<', '<='].includes(anchor.comparison === undefined ? '==' : anchor.comparison)
          && (validTolerance(anchor.tolerance) || anchor.tolerance === null)
          && (anchor.uncertainty === undefined || anchor.uncertainty === null
            || (typeof anchor.uncertainty === 'object' && !Array.isArray(anchor.uncertainty)
              && Object.keys(anchor.uncertainty).length === 2
              && ['standard_error', 'standard_deviation', 'interval_halfwidth'].includes(anchor.uncertainty.kind)
              && nonnegative(anchor.uncertainty.value))))
      facts.anchored = validAnchors && anchors.length === facts.anchors_count ? anchors.some(anchor => !isReference(anchor)) : null
      if (reply == null) return fail()
      const documents = {}
      for (const name of ['benchmark', 'data', 'baseline', 'EXECUTION']) {
        const value = readJSON(path.join(directory, `${name}.json`))
        if (!hasValue(value) || typeof value !== 'object' || Array.isArray(value)) return fail()
        documents[name] = value
      }
      const complete = validAnchors && anchors.length === facts.anchors_count
        && ['repo', 'build_commands', 'run_commands', 'published_configuration'].every(key => hasValue(documents.baseline[key]))
        && hasValue(documents.baseline.commit ?? documents.baseline.pin)
        && ['representative_scale', 'inputs', 'outputs', 'timing_scope'].every(key => hasValue(documents.EXECUTION[key]))
      const pass = complete && facts.found && facts.data === 'available'
        && facts.licence !== 'restricted' && facts.stock_environment !== false
      return pass ? { status: 'PASS', facts } : fail()
    } catch {
      return fail()
    }
  }
  const isReference = anchor => (anchor.comparison === undefined ? '==' : anchor.comparison) === '==' && anchor.tolerance === null
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
  const defaultBudgets = { method_setup: 1200, method_run: 1200, tests: 900, evaluate: 2400 }
  function executionTimeout(name) {
    const key = ({ run_anchors: 'anchors', setup_method: 'method_setup', run_method: 'method_run', run_tests: 'tests' })[name] || name
    if (['setup', 'anchors', 'profile'].includes(key)) {
      const ceiling = Object.hasOwn(input, 'run_ceiling_s') ? input.run_ceiling_s : 43200
      if (!Number.isInteger(ceiling) || ceiling <= 0 || ceiling > 999999999) throw new Error('invalid budget')
      if (!Object.hasOwn(input.stage_budgets_s || {}, key)) return Math.max(0, ceiling - Math.floor((Date.now() - runStarted) / 1000))
      const seconds = input.stage_budgets_s[key]
      if (!Number.isInteger(seconds) || seconds <= 0 || seconds > 999999999) throw new Error('invalid budget')
      return seconds
    }
    const execution = readJSON(path.join(A, 'intake', 'EXECUTION.json'))
    const seconds = execution.stage_budgets_s?.[key] ?? input.stage_budgets_s?.[key] ?? defaultBudgets[key]
    if (!Number.isInteger(seconds) || seconds <= 0 || seconds > 999999999) throw new Error('invalid budget')
    return seconds
  }
  const budgetPrompt = () => `Script budgets in seconds: setup.sh=${executionTimeout('setup')}, run_anchors.sh=${executionTimeout('anchors')}, fixed profiler=${executionTimeout('profile')} (resolved now: time left before the run ceiling, not a target; explicit args budgets override); run_evaluation.sh=${executionTimeout('method_run')} per invocation (also run_anchors.sh when used as the evaluation adapter); complete evaluation scorer=${executionTimeout('evaluate')}. Use one fixed scale from EXECUTION.json, no scale search or doubling loops, and finish well within the budget.`
  async function boxCommand(name, command, destination, timeout, retry = false) {
    const seconds = typeof timeout === 'string' ? executionTimeout(timeout) : timeout
    if (seconds < 1) {
      const result = { error: 'timeout', rc: 124, timed_out: true, budget_s: 0, wall_s: 0, overrun: true }
      stageReceipts.push(result)
      return result
    }
    if (typeof command === 'function') command = command(seconds)
    mkdirSync(receiptsDirectory, { recursive: true })
    const number = Math.max(0, ...readdirSync(receiptsDirectory)
      .filter(file => /^\d+-/.test(file)).map(file => Number(file.split('-')[0]))) + 1
    const id = `${String(number).padStart(4, '0')}-${name}`
    const receiptPath = path.join(receiptsDirectory, `${id}.json`)
    // Never score files left by an earlier invocation using the same run root.
    rmSync(path.join(destination, 'out', name === 'concurrency' ? 'concurrency' : ''), { recursive: true, force: true })
    let commandFailed = false
    try {
      await exec('bash', ['m5/boxrun.sh', '--name', id, '--cmd', command,
        '--remote-dir', remoteDirectory, '--timeout', String(seconds), '--fetch', 'out',
        '--to', destination, '--receipt', receiptPath])
    } catch {
      commandFailed = true
      // boxrun's receipt, never command output, determines the public failure class.
    }
    let receipt
    try { receipt = readJSON(receiptPath) } catch { return { error: 'infra' } }
    receipt.budget_s = seconds
    receipt.overrun = receipt.rc === 124 || receipt.timed_out === true || receipt.wall_s > seconds
    stageReceipts.push(receipt)
    // Transport and integrity commands have no authored script to change. Repair by one identical retry.
    const authored = ['setup', 'anchors', 'profile', 'concurrency', 'adapter-smoke', 'setup-method', 'run-method', 'run-tests']
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
    const commands = []
    for (const name of names) {
      const remote = `harness/${name}`
      commands.push(`: > ${quote(remote)}`)
      const bytes = readFileSync(path.join(harnessDirectory, name)).toString('base64')
      for (let offset = 0; offset < bytes.length; offset += 24576) {
        commands.push(`printf %s ${quote(bytes.slice(offset, offset + 24576))} | base64 -d >> ${quote(remote)}`)
      }
    }
    const prefix = 'set -e\nmkdir -p harness out'
    let batch = prefix
    for (const line of commands) {
      if (batch.length + line.length + 1 >= 32768) {
        const result = await boxCommand('upload', batch, destination, timeout)
        if (result.error || result.rc !== 0) return result
        batch = prefix
      }
      batch += `\n${line}`
    }
    return boxCommand('upload', batch, destination, timeout)
  }
  const harnessRules = 'Scope: setup.sh builds and checks only the baseline. The pipeline owns profiling and profiler installation; do not write profile.sh or install profiling tools. A setup repair may change only setup.sh; an anchors repair may change run_anchors.sh, run_command.sh, or both, and nothing else. Stay within each script\'s scope. Run the published build and binary and read measurements from its OUTPUT. run_command.sh contains only the exact measured baseline command and complete environment at the representative scale. run_command.sh is the canonical measured command and complete environment, including working directory, arguments, CUDA_VISIBLE_DEVICES and GPU count. run_command.sh must use paths relative to its working directory, never absolute paths into the run directory, and write only under out/ or temporary files. Concurrency and evaluation run it from sibling work directories linking the same trees. The pipeline owns CUDA MPS. No harness script (setup.sh, run_anchors.sh, run_command.sh, run_evaluation.sh) may set, unset or override any CUDA_MPS_* environment variable, or start or stop an MPS daemon; inherit these variables unchanged. run_anchors.sh must invoke bash harness/run_command.sh without overriding its environment or duplicating the workload command; parse its saved output for every intake item ID, anchors and references. With an empty anchors.json, still run the published command and write out/anchors_measured.json as {}. The fixed profiler invokes that identical file with bash from the same working directory. Keep output paths stable and preserve logs. Every later run script must preserve the published configuration. Validate printed configuration against the actual command and environment. Preserve consistency in repairs; read the other harness scripts while editing only the permitted scripts. Never parse or assert on source text. Measurement checks must fail only on missing or invalid output; the pipeline scores measured values against anchors.'
  let boxProbe
  let harnessSource
  const writeHarnessSource = () => writeFileSync(path.join(C, 'harness_source.json'), JSON.stringify(harnessSource, null, 2) + '\n')
  const boxProbePrompt = () => `Box probe (collected by the pipeline before harness generation):
${JSON.stringify(boxProbe, null, 2)}
Use the probe's discovered paths and versions. Accept either a complete CUDA toolkit root containing bin/nvcc, include/cuda_runtime.h and lib64/libcudart.so, or the distro layout with /usr/bin/nvcc, /usr/include/cuda_runtime.h and libcudart.so under /usr/lib/x86_64-linux-gnu. Have the scripts check all three selected paths with ls on the box. Prefer a complete toolkit root when both layouts exist; otherwise accept the complete distro layout without requiring /usr/lib64/libcudart.so. Use the same selected compiler, include and library paths in every script, including repairs. For a complete root, pass it explicitly via CUDAToolkit_ROOT or -DCMAKE_CUDA_COMPILER=<root>/bin/nvcc and prepend <root>/bin to PATH. For the distro layout, use /usr/bin/nvcc with its distro include and library paths explicitly; do not treat /usr as a toolkit root requiring lib64. Never rely on /usr/bin/nvcc when a complete toolkit root exists. Never hard-code a toolkit path the probe did not find, even if the brief suggests one. A tool or system library the published baseline needs but the stock image lacks may be installed with sudo apt-get install -y from any source the probe reports in apt_enabled_sources (after sudo apt-get update), once apt-cache policy <package> shows an install candidate. Never add repositories, keys or source lines, and never enable a commented or disabled source. Setup prints each package it installs and its installed version (dpkg-query -W <package>). Otherwise only cmake may fall back to pip. If neither route applies, scripts must fail with a clear message.`
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
    const repairLimit = name === 'setup.sh' ? 4 : 2
    let result = await boxCommand(operation, command, destination, timeout)
    for (let retry = 1; retry <= repairLimit; retry++) {
      if (result.error === 'infra' || result.budget_s === 0 || result.fetched === false || (result.rc === 0 && !result.error)) return result
      let tail
      try {
        const lines = readFileSync(result.log, 'utf8').trimEnd().split('\n')
        tail = lines.slice(-200).join('\n')
      } catch {
        if (!result.error) return result
        tail = ''
      }
      const names = name === 'setup.sh' ? [name] : ['run_anchors.sh', 'run_command.sh']
      const before = new Map(name === 'setup.sh' ? [] : names.map(file => [file, readFileSync(path.join(harnessDirectory, file))]))
      const protectedScripts = new Map(name === 'setup.sh' ? [] : ['setup.sh', 'run_evaluation.sh'].map(file =>
        [file, existsSync(path.join(harnessDirectory, file)) ? readFileSync(path.join(harnessDirectory, file)) : null]))
      const scope = name === 'setup.sh' ? `Repair only ${JSON.stringify(path.join(harnessDirectory, name))}`
        : `Repair run_anchors.sh, run_command.sh, or both under ${JSON.stringify(harnessDirectory)}, and nothing else. A rewritten run_command.sh must still obey every run_command.sh rule`
      const repair = await agent(`${name} failed (rc ${result.rc}${result.error ? `, output gate: ${result.error}` : ''}). ${scope} using intake evidence. Preserve the published pin, configuration and stock image; sudo only for apt. ${harnessRules} Never read experiments/, operator/, or control/. Do not run workloads locally or access the box. This is repair attempt ${retry} of ${repairLimit} for this ${name === 'setup.sh' ? 'script' : 'step'}.
Budget: ${executionTimeout(timeout)}s resolved now, the time left before the run ceiling, not a target (explicit args budget overrides); failed attempt budget: ${result.budget_s}s; measured elapsed: ${result.wall_s ?? 'unavailable'}s; measured overrun: ${Number.isFinite(result.wall_s) ? Math.max(0, result.wall_s - result.budget_s) : 'unavailable'}s. ${budgetPrompt()}
${boxProbePrompt()}
Log tail (at most 200 lines):\n${tail}`,
        { label: name === 'setup.sh' ? 'harness-repair' : `${operation}-repair`, agentType: 'ls-writer', model: 'sonnet', retry })
      for (const [file, bytes] of protectedScripts) {
        if (bytes === null) rmSync(path.join(harnessDirectory, file), { force: true })
        else writeFileSync(path.join(harnessDirectory, file), bytes)
      }
      if (repair == null) return result
      if (harnessSource) {
        for (const file of names) {
          if (!before.has(file) || !before.get(file).equals(readFileSync(path.join(harnessDirectory, file)))) harnessSource.files[file].modified = true
        }
        writeHarnessSource()
      }
      const uploaded = await uploadHarness(names, destination, 'setup')
      if (uploaded.error || uploaded.rc !== 0) return { ...uploaded, error: uploaded.error || 'infra' }
      result = await boxCommand(operation, command, destination, timeout)
    }
    return result
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
    try {
      executionTimeout('setup')
      executionTimeout('anchors')
    } catch { return failure(facts, 'parse') }
    try {
      await collectBoxProbe('setup')
    } catch (error) { return failure(facts, error.error_class || 'infra') }
    try {
      const prompt = `Write a baseline harness from ${JSON.stringify(path.join(A, 'intake'))}/*.
Never read experiments/, operator/, or control/. Write only under ${JSON.stringify(harnessDirectory)}.
The operator already started the dev box. Do not start, stop, or access it; the pipeline runs your scripts.
${harnessRules}
${budgetPrompt()}
${boxProbePrompt()}
Write three self-contained bash scripts, invoked from a shared remote working directory with bash harness/<name>:
- setup.sh: build/install the published baseline at its exact intake pin in the stock image. Use sudo only for apt. Preserve stock torch and published source/configuration. Stage source in baseline-published/ and inputs in data/. Do not silently substitute or tune the baseline. Make setup safe to retry once in this directory.
- run_anchors.sh: run the published protocol at the real representative scale declared in EXECUTION.json. Write out/anchors_measured.json as {item_id: measured_number}, one finite number per intake item ID (anchors and references). With an empty anchors.json, still run the published command and write {}. Never copy published values as measurements.
- run_command.sh: only the exact measured baseline run command and its complete environment at the fixed representative scale. Run the published binary, save its stdout/stderr for run_anchors.sh to parse, and propagate its exit status. Do not measure stages, sample telemetry, install tools, or write profiling outputs. run_anchors.sh invokes this file; the pipeline profiles this same file.
Also provide run_evaluation.sh for the published baseline evaluation interface, or make run_anchors.sh handle non-anchor EVAL_MODE. Evaluation uses fresh working directories with baseline-published/, method/, data/, harness/ and payload/ links and absolute BASELINE_DIR, METHOD_DIR, BASELINE_OUT, METHOD_OUT and EVAL_OUT paths. EVAL_PROTOCOL points to the sealed JSON; EVAL_INPUTS and EVAL_SEEDS are JSON encodings of evaluation_inputs and paired_seed_tests. EVAL_INPUTS is an object whose ids array lists the sealed input identities in order; each record's input_id is one of those strings, and every other key (pins, configuration, generated-input descriptions) describes inputs and is never itself an input. EVAL_SEEDS is either {kind:"paired_median",seeds:[integer,...]}, whose seeds are the execution seeds in order, or {kind:"deterministic",...}, whose single execution seed is null; other keys are descriptive. EVAL_COMPUTE_BUDGET is empty except in curve mode. Modes are equivalence, warmup, performance and curve. Run the published configuration on every sealed input/seed, seeds first then input IDs, and write EVAL_OUT/evaluation.json: {records:[{input_id,seed,metrics:{metric_name:finite_number}}],timing_scope,gpu_count,wall_s,compute_budget}. Use null seed for deterministic protocols; timing_scope must equal the seal; wall_s is required for reported_wall scopes; compute_budget is required for curves. Synchronize every used GPU before returning or stopping reported timers; include launch, transfer and merge overhead. Enforce curve budgets in GPU seconds. Always measure actual outputs; never reuse baseline outputs.
Create output directories, preserve logs, and exit nonzero on failure. Read all intake files for pins, commands, data, scale and protocol. Do not run builds or workloads locally.
Return a short completion acknowledgement; the pipeline reads the scripts itself.`
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
        ...(existsSync(path.join(harnessDirectory, 'run_evaluation.sh')) ? ['run_evaluation.sh'] : [])], destination, 'setup')
      if (uploaded.error || uploaded.rc !== 0) return failure(facts, uploaded.error || 'infra')
      const setup = await runHarness('setup.sh', 'setup', destination, 'setup')
      if (setup.error) {
        facts.stock_verified = setup.rc === 0 && setup.error !== 'timeout'
        return failure(facts, setup.error)
      }
      facts.stock_verified = setup.rc === 0
      if (!facts.stock_verified) return failure(facts, 'install')
      const anchors = await runHarness('run_anchors.sh', 'anchors', destination, 'anchors')
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
      const run_valid = score.anchors_total === 0 ? null : score.all_passed
      if (passed) {
        // A timeout may leave a partial snapshot; fail without retrying the freeze.
        const frozen = await boxCommand('reproduce-freeze', 'set -e\ntest ! -e reproduce-out\ncp -a out reproduce-out',
          destination, 'setup', true)
        if (frozen.error || frozen.rc !== 0) return failure(facts, frozen.error || 'infra')
      }
      return passed ? { status: 'PASS', facts, v1: { run_valid } }
        : { ...failure(facts, 'anchor'), v1: { error_class: 'anchor', exit_code: 4, run_valid } }
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
          stages: measuredStages, total_wall_s, concurrency: null,
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
      const commands = ['set -e', 'mkdir -p profiler', 'rm -rf out/profile']
      for (const name of ['profile_nsys.sh', 'profile_summarise.py']) {
        const bytes = readFileSync(path.join('m5', name)).toString('base64')
        commands.push(`printf %s ${quote(bytes)} | base64 -d > ${quote(`profiler/${name}`)}`)
      }
      const probeBytes = Buffer.from(JSON.stringify(boxProbe)).toString('base64')
      commands.push(`printf %s ${quote(probeBytes)} | base64 -d > profiler/probe.json`)
      const uploaded = await boxCommand('upload', commands.join('\n'), destination, 'profile')
      if (uploaded.error || uploaded.rc !== 0) return failure(facts, uploaded.error || 'infra')
      const result = await boxCommand('profile',
        seconds => `bash profiler/profile_nsys.sh harness/run_command.sh out/profile ${seconds}`, destination, 'profile')
      if (result.error) return failure(facts, result.error)
      if (existsSync(path.join(destination, 'out', 'profile', 'infra.json'))) return failure(facts, 'infra')
      if (result.rc !== 0) return failure(facts, 'parse')
      const invalid = validateProfile()
      if (invalid) return failure(facts, invalid)
      let concurrency = null
      try {
        const bytes = readFileSync('m5/concurrency_probe.py').toString('base64')
        const probe = await boxCommand('concurrency', seconds => `set -e
mkdir -p profiler
printf %s ${quote(bytes)} | base64 -d > profiler/concurrency_probe.py
rm -rf out/concurrency
python3 -I profiler/concurrency_probe.py harness/run_command.sh out/concurrency ${seconds}`, destination, 'profile')
        if (probe.budget_s === 0) return failure(facts, 'timeout')
        if (!probe.error && probe.rc === 0) {
          const value = readJSON(path.join(destination, 'out', 'concurrency', 'concurrency.json'))
          if (validConcurrency(value)) concurrency = value
        }
      } catch { /* Calibration is optional evidence and never changes the profile gate. */ }
      const packet = readJSON(path.join(A, 'profile-packet.json'))
      packet.concurrency = concurrency
      facts.headroom = concurrency?.factor ?? null
      writeFileSync(path.join(A, 'profile-packet.json'), JSON.stringify(packet, null, 2) + '\n')
      return { status: 'PASS', facts }
    } catch {
      return failure(facts, 'parse')
    }
  }
  function validConcurrency(value) {
    const keys = (item, expected) => item && typeof item === 'object' && !Array.isArray(item)
      && Object.keys(item).length === expected.length && expected.every(key => Object.hasOwn(item, key))
    const positive = item => Number.isFinite(item) && item > 0
    const nullable = item => item === null || positive(item)
    if (!keys(value, ['mps', 'mps_failed', 'single_wall_s', 'batches', 'factor'])
      || typeof value.mps !== 'boolean' || typeof value.mps_failed !== 'boolean'
      || !Array.isArray(value.single_wall_s) || value.single_wall_s.length !== 3
      || !value.single_wall_s.every(nullable) || !nullable(value.factor)
      || !Array.isArray(value.batches) || value.batches.length !== 2) return false
    const singlesOK = value.single_wall_s.every(positive)
    const t1 = [...value.single_wall_s].sort((a, b) => a - b)[1]
    if (!value.batches.every((batch, index) => {
      if (!keys(batch, ['n', 'wall_s', 'all_ok', 'skipped', 'factor'])
        || batch.n !== [2, 4][index] || typeof batch.all_ok !== 'boolean' || typeof batch.skipped !== 'boolean'
        || !nullable(batch.wall_s) || !nullable(batch.factor)) return false
      if (batch.skipped || !batch.all_ok || !singlesOK) return batch.factor === null
      return positive(batch.wall_s) && batch.factor === batch.n * t1 / batch.wall_s
    })) return false
    const factors = value.batches.filter(batch => batch.factor !== null).map(batch => batch.factor)
    return value.factor === (singlesOK && factors.length ? Math.max(...factors) : null)
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
    const { default: sealProtocol } = await import(path.resolve('m5/seal_protocol.js'))
    const evaluate_budget_s = executionTimeout('evaluate')
    const costPrompt = `Resolved evaluate budget: ${evaluate_budget_s} seconds. Project one complete performance scorer: projected_s = (warmup + repetitions) * 2 * baseline_invocation_s.seconds, plus b / baseline_gpus + b / method_gpus for each compute budget b unless equal_outcome_target.not_applicable is true; GPU counts come from hardware_cost_basis. With at least one feasible method, projected_s must not exceed 0.9 * the resolved evaluate budget; otherwise the seal fails protocol_cost. With no feasible method this cost check is skipped. baseline_invocation_s.seconds comes from the measurements and is never lowered to fit; fit the protocol through seeds, inputs, warmup, repetitions and compute budgets. The adapter smoke still measures the real cost.`
    const prompt = `Seal a prospective scientific evaluation protocol in one narrow pass.
Read ${JSON.stringify(path.join(A, 'intake'))}/*, ${JSON.stringify(profilePath)}, ${JSON.stringify(boundsPath)}, and the baseline's measured outputs under ${JSON.stringify(path.join(A, 'results', 'reproduce'))}/ (the fetched out/, logs and anchors_scored.json) only.
Never read experiments/, operator/, or control/. Do not search, build, run workloads, or write method code.
Write only ${JSON.stringify(predictionPath)}. Use intake evidence and the profile when present. Do not invent measurements; label assumptions and unavailable evidence explicitly.
The method menu is exactly ${JSON.stringify(menu)}. Deterministic bounds (p is the actionable timed fraction; k is the maximum factor): ${JSON.stringify(bounds)}.
Include every feasible entry once; list every entry with bound <1.05 exactly once as {method, reason} in infeasible_methods, never in predictions. With no feasible entry, write predictions=[] as a negative result.
For each interval require finite low >0, low <= high <= its method's bound, and high-low <= bound-1. When at least two methods are feasible, their intervals must not all be identical. Base each interval on its method's profile evidence and overheads.
Whole-workload bounds are measured concurrent throughput on one GPU (p=1, capped at 8 for data-parallel over inputs and ensembles, 4 for batching); missing headroom gives bound 1. Pipelining is Amdahl over transfer time with k=2. Multi-GPU bounds are per GPU-second at equal cost: Amdahl/k with k=max(1,gpu_count). Amdahl is 1/((1-p)+p/k). The supplied bounds are ceilings, not measured method gains; intervals without measurements are prospective assumptions. Include launch/transfer/merge overhead.
Write an object with these fields:
- outputs_stochastic: boolean; true for Monte Carlo, sampling, or outputs affected by random seeds, even when fixed seeds make a run reproducible.
- predictions: array of {method, expected_speedup_interval: {low, high}, outcome_vs_compute_points}. Each point is {compute_budget, predicted_outcome, uncertainty}. Include all sealed compute budgets for each method. Both predicted_outcome and uncertainty must be non-null, nonempty values at every budget. If no numeric outcome forecast is scientifically supported, use an explicit nonempty declaration such as predicted_outcome={not_applicable:true,reason:"fixed-work benchmark; no calibrated outcome curve"} and explain assumptions or unavailable evidence in uncertainty. Never invent a numeric forecast or use null; equal_outcome_target.not_applicable does not waive these point fields.
- equivalence_metrics: quantities, scientific tolerances, and sources from requirements or baseline variability, never method outputs. A margin derived from baseline variability names, in its source, the measured file and the statistic used (for example the standard deviation of a per-seed outcome across the baseline's seeds). Lack of significance is not equivalence.
For stochastic outputs, equivalence_metrics must be statistical: use paired seeds and positive absolute scientific margins supported by scientific requirements or measured baseline variability (for example Monte Carlo standard error), with a sealed significance level alpha = 1 - confidence_rule.equivalence.confidence. When neither a scientific requirement nor measured baseline variability supports a positive margin, never invent one; the seal fails stochastic_equivalence_invalid as before. Require the confidence interval for paired differences to lie within those margins. Never demand exact, zero-tolerance, or bitwise equivalence for stochastic outputs. Exact or bitwise equivalence is required only for deterministic outputs.
- paired_seed_tests: stochastic paired-seed test and fixed seeds, or an explicit scientifically justified deterministic/not-applicable declaration.
- sample_sizes and confidence_rule: powered equivalence sample sizes and the confidence decision rule.
- hardware_cost_basis, timing_scope, minimum_worthwhile_gain (a speedup ratio >1).
- evaluation_inputs and splits: fixed input identities/pins, held-out splits and seeds, or explicit generated-input specifications.
- compute_budgets: at least three distinct positive numeric budgets, with units in hardware_cost_basis.
- repetitions: integer >=5 timing pairs; warmup: fixed warmup protocol; scheduling_order: paired randomisation protocol; equal_outcome_target: the fixed scientific target.
- baseline_invocation_s: {seconds, source}; seconds is a finite positive number estimating process wall from launch to exit of one complete baseline equivalence invocation over all sealed seeds and inputs, derived from reproduce measurements. source is a nonempty string naming the measured file, measured value and arithmetic.
${costPrompt}
Executable v1 evaluation uses exact binomial order-statistic bounds (one-sided performance, two-sided equivalence with Bonferroni across metrics). warmup is a nonnegative integer per arm. scheduling_order={kind:"randomized_pairs",seed:integer}. timing_scope={kind:"process_wall" or "reported_wall",gpu_synchronization:"adapter",description:"scope including launch/transfer/merge"}. hardware_cost_basis={baseline_gpus:positive integer,method_gpus:positive integer,budget_unit:"gpu_s"}. equal_outcome_target={metric:"outcome metric name",comparison:">=",target:finite number} or {not_applicable:true,reason:"why benchmark has no outcome curve"}. Unsupported prose-only protocols produce VOID at evaluation.
Exact JSON skeletons, generated from the deterministic seal check's constants. Choose the matching output type; expand to your fixed inputs, metrics and seeds. Keep these field types and nesting, especially name/source as nonempty STRINGS, never objects. Example tolerances, invocation seconds and citations are placeholders: replace them with justified scientific choices. sample_sizes.inputs must equal evaluation_inputs.ids.length; sample_sizes.seeds must equal paired seed count (1 for deterministic, whose execution seed is null). More metrics or higher confidence can require more seeds for finite Bonferroni bounds.
Stochastic: ${JSON.stringify(sealProtocol.skeleton(true))}
Deterministic: ${JSON.stringify(sealProtocol.skeleton(false))}
Define the complete protocol now, before method code exists. Scope/tolerance changes require a new sealed run.
Return a short completion acknowledgement; the script reads and seals the file itself.`
    try {
      check = 'agent_failed'
      const reply = await agent(prompt, { label: 'seal', agentType: 'ls-writer', model: 'sonnet', repairable: false, fresh: true })
      if (reply == null) return reject(check)
      let predictions, invalid
      for (let attempt = 0; attempt < 2; attempt++) {
        check = 'predictions_read_failed'
        try {
          predictions = readJSON(predictionPath)
          facts.prediction_count = Array.isArray(predictions?.predictions) ? predictions.predictions.length : 0
          invalid = sealProtocol.validate(predictions, bounds, menu, evaluate_budget_s)
        } catch {
          invalid = { reason_codes: ['predictions_read_failed'], field_paths: ['$'] }
        }
        if (!invalid) break
        if (attempt === 1) return reject(invalid.reason_codes[0])
        check = 'agent_failed'
        const repaired = await agent(`Rewrite only ${JSON.stringify(predictionPath)} to repair the failed seal. Read only that file; do not read any other files, search, build, run workloads, or write method code. Preserve scientific intent; never invent evidence or loosen tolerances to obtain a pass. Return a short acknowledgement. This is the only repair attempt.
Validation feedback (codes and field paths only): ${JSON.stringify(invalid)}${invalid.reason_codes.includes('protocol_cost') ? `\n${costPrompt}` : ''}`,
          { label: 'seal-repair', agentType: 'ls-writer', model: 'sonnet', repairable: false, fresh: true })
        if (repaired == null) return reject(check)
      }

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
      return { status: 'PASS', facts, reason_codes: [] }
    } catch {
      return reject(check)
    }
  }
  async function propose() {
    if (input.stub?.propose != null) return stub('propose')
    const facts = { ...nullFacts('propose'), method: 'none', votes_approve: 0, votes_reject: 0, votes_abstain: 0,
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
      return facts.gate_pass || facts.outcome === 'no_feasible_method'
        ? { status: 'PASS', facts } : failure(facts, error_class)
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
      if (!methods.length) {
        if (Number.isFinite(profile.concurrency?.factor)
          && (profile.concurrency.mps === true
            || (profile.concurrency.mps === false && profile.concurrency.mps_failed === false))
          && available > 0) {
          facts.outcome = 'no_feasible_method'
        }
        return finish('numeric')
      }
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
Whole-workload bounds are measured concurrent throughput on one GPU; pipelining is Amdahl over transfer time with k=2; multi-GPU bounds are Amdahl/k per GPU-second at equal cost.
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
      // Queue all five ballots together with distinct labels and fresh runner sessions.
      const votes = await Promise.all(Array.from({ length: 5 }, async (_, index) => {
        const votePath = path.join(votesDirectory, `${index + 1}.json`)
        rmSync(votePath, { force: true })
        let vote = null
        try {
          vote = await agent(`Independent ballot ${index + 1} of 5. Review this proposal once.
Use only the embedded prepared packet and proposal. Never read files, other votes, or other sessions; do not search or use tools.
ranked_methods have already passed deterministic GPU resource guards.
reject = a named defect that would make the method fail as planned: exceeds its bound, cannot be parallelised as planned, changes the sealed method, risks breaking the sealed equivalence rule, or mismatches resources.
abstain = the packet is insufficient to judge. approve = no defect is found and the evidence is adequate.
Return only vote and reason_codes using the supplied schema. Missing or weak evidence warrants abstain, not reject. Vote share is not a calibrated probability.
Prepared packet:\n${evidence}\nProposal:\n${JSON.stringify(proposal)}`,
            { label: `skeptic-${index + 1}`, agentType: 'qt-bare', model: 'haiku', schema: voteSchema, repairable: false, fresh: true })
        } catch { /* A failed call is a null ballot; never replace it. */ }
        if (validate(voteSchema, vote).length) vote = null
        writeFileSync(votePath, JSON.stringify(vote, null, 2) + '\n')
        return vote
      }))
      facts.votes_approve = votes.filter(vote => vote?.vote === 'approve').length
      facts.votes_reject = votes.filter(vote => vote?.vote === 'reject').length
      facts.votes_abstain = votes.filter(vote => vote?.vote === 'abstain').length
      facts.vote_share = facts.votes_approve / 5
      const votesNull = 5 - facts.votes_approve - facts.votes_reject - facts.votes_abstain
      const ballotPass = facts.votes_reject + votesNull <= 1
      facts.gate_pass = ballotPass && chosen.prediction.expected_speedup_interval.high >= predictions.minimum_worthwhile_gain
        && chosen.prediction.expected_speedup_interval.high <= chosen.bounds.bound && chosen.resource_guard_pass
      facts.outcome = facts.gate_pass ? 'approved' : ballotPass ? 'conditions_unmet' : 'rejected'
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
    if (!stopped_at && (result.status !== 'PASS' || result.facts.outcome === 'no_feasible_method')) stopped_at = stage
  }
  await exec('python3', ['m5/operator_takeaway.py', S, '--raid', raid])
  return { stages, stopped_at }
})()
