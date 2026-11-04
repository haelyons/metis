// wf.js script. Intake through evaluate are real; takeaways remains a placeholder.
const meta = { name: 'm5', description: 'Explicit-run-root scientific pipeline skeleton' }

return (async () => {
  const runStarted = Date.now()
  const { default: path } = await import('node:path')
  const { mkdirSync, existsSync, readFileSync, writeFileSync, readdirSync, rmSync, statSync, cpSync, renameSync,
    mkdtempSync, lstatSync, chmodSync } = await import('node:fs')
  const { createHash, randomUUID } = await import('node:crypto')
  const { execFile } = await import('node:child_process')
  const { promisify } = await import('node:util')
  const { homedir, tmpdir } = await import('node:os')
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
    reproduce: ['anchors_passed', 'anchors_total', 'stock_verified', 'tuned_control_valid', 'units_match', 'units_full_match',
      'units_outcome', 'units_factor_2', 'units_factor_4', 'units_shared_writes',
      'card_inputs', 'card_measured', 'card_holds', 'card_refuted'],
    profile: ['profile_complete', 'timed_fraction', 'gpu_telemetry', 'headroom', 'host_only'],
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
  // A comparison's bill of the whole box allocation (G6), which may include work outside this run.
  function allocation() {
    const field = key => box && box[key] !== undefined ? box[key] : null
    const price = box && nonnegative(box.price_usd_h) ? box.price_usd_h : null
    const final = box?.ended_utc != null && box?.hours != null
    const start = Date.parse(box?.started_utc)
    const hours = final ? box.hours : Number.isFinite(start) ? (Date.now() - start) / 3600000 : null
    return { type: field('type'), price_usd_h: price, started_utc: field('started_utc'), ended_utc: final ? box.ended_utc : null,
      hours, usd: Number.isFinite(hours) && price !== null ? hours * price : null, final }
  }
  const hasValue = value => value != null && (typeof value !== 'string' || value.trim() !== '')
    && (typeof value !== 'object' || Object.keys(value).length > 0)
  const menu = ['data-parallel over inputs', 'batching', 'multi-GPU', 'ensembles', 'pipelining']
  const sha256 = bytes => createHash('sha256').update(bytes).digest('hex')
  function writeAtomic(file, text) {
    const temporary = `${file}.${randomUUID()}.tmp`
    writeFileSync(temporary, text)
    renameSync(temporary, file)
  }

  // Card calibration (U54): agents see only A/card_inputs.json; the record, its values and bands stay in control/.
  const cardMode = Object.hasOwn(input, 'card')
  const cardArg = input.card
  if (cardMode) {
    // No agent-readable copy of the arguments holds args.card: wf.js records this same object in agent/wf/run.json
    // before the script starts (rewritten here, before any agent call) and again when it ends (hence the delete).
    delete input.card
    const runRecord = agent.journal ? path.join(path.dirname(agent.journal), 'run.json') : null
    if (runRecord && existsSync(runRecord)) {
      const info = readJSON(runRecord)
      if (info?.args && typeof info.args === 'object') delete info.args.card
      writeAtomic(runRecord, JSON.stringify(info, null, 1))
    }
  }
  const cardInputsPath = path.join(A, 'card_inputs.json')
  let cardInputs = null
  function prepareCard() {
    const card = cardArg
    const plain = value => value && typeof value === 'object' && !Array.isArray(value)
    if (!plain(card) || !Object.keys(card).every(key => ['result', 'key', 'bands'].includes(key))
      || typeof card.result !== 'string' || !card.result.trim() || typeof card.key !== 'string' || !card.key.trim()
      || Object.hasOwn(input, 'units_check') || Object.hasOwn(input, 'units_probe')) throw new Error('invalid card')
    const source = path.resolve(card.result)
    const bytes = readFileSync(source)
    const calibration = JSON.parse(bytes.toString('utf8'))?.calibration
    const record = Array.isArray(calibration) ? calibration.find(item => item?.key === card.key) : null
    if (!plain(record) || record.state !== 'calibration_required' || !Array.isArray(record.required) || !record.required.length
      || new Set(record.required.map(item => item?.id)).size !== record.required.length
      || !record.required.every(item => plain(item) && typeof item.id === 'string' && /^[a-z][a-z0-9_]{0,30}$/.test(item.id)
        && ['GUESS', 'PROXY'].includes(item.basis))) throw new Error('invalid card')
    const bands = Object.hasOwn(card, 'bands') ? card.bands : {}
    if (!plain(bands) || !Object.entries(bands).every(([id, band]) => record.required.some(item => item.id === id)
      && plain(band) && Object.keys(band).length === 1 && Number.isFinite(band.abs) && band.abs > 0)) throw new Error('invalid card')
    const cardText = JSON.stringify({ source, source_sha256: sha256(bytes), record, bands }, null, 2) + '\n'
    writeAtomic(path.join(C, 'card.json'), cardText)
    writeAtomic(path.join(C, 'card_seal.json'), JSON.stringify({ card_sha256: sha256(cardText), sealed_utc: new Date().toISOString() }, null, 2) + '\n')
    cardInputs = {
      inputs: record.required.map(item => ({ id: item.id, name: item.name ?? null, unit: item.unit ?? null,
        measured_by: item.measured_by ?? null, phase: item.phase?.what ?? null })),
      anchor: Number.isFinite(record.anchor?.published_value) ? { what: record.anchor.what ?? null } : null,
    }
    writeAtomic(cardInputsPath, JSON.stringify(cardInputs, null, 2) + '\n')
  }

  // Sealed comparison (U57): the design stays in control/; agents see only A/comparison_view.json, from private views.
  const comparisonMode = Object.hasOwn(input, 'comparison')
  const comparisonViewPath = path.join(A, 'comparison_view.json')
  let design = null, hiddenPaths = null
  const exactObject = (value, keys) => value && typeof value === 'object' && !Array.isArray(value)
    && Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key))
  const pointerPattern = /^(?:\/(?:[^~/]|~[01])*)*$/
  async function pythonGroups(pairs) {
    // Python's re decides what a pattern is and how many groups it has: [groups test, pattern] pairs.
    if (!pairs.length) return true
    try {
      await exec('python3', ['-I', '-c', `import re, sys
a = sys.argv[1:]
sys.exit(0 if all(re.compile(p).groups >= 1 if t == "some" else re.compile(p).groups == int(t) for t, p in zip(a[0::2], a[1::2])) else 1)`,
      ...pairs.flat()])
    } catch { return false }
    return true
  }
  async function validDesign(value) {
    const text = item => typeof item === 'string' && item.length > 0
    const sized = (list, low, high) => Array.isArray(list) && list.length >= low && list.length <= high
    const unique = list => new Set(list).size === list.length
    const integer = (item, low = -Infinity, high = Infinity) => Number.isInteger(item) && item >= low && item <= high
    const named = item => typeof item === 'string' && /^[a-z][a-z0-9_]{0,30}$/.test(item)
    if (!exactObject(value, ['arms', 'inputs', 'outputs', 'metrics', 'evaluator', 'replicates', 'warmup', 'order_seed',
      'timeout_s', 'budget_s', 'bootstrap_seed', 'bootstrap_resamples', 'comparisons'])) return false
    const { arms, inputs, outputs, metrics, evaluator, comparisons } = value
    if (!sized(inputs, 1, 10) || !inputs.every(item => exactObject(item, ['id', 'spec']) && typeof item.id === 'string'
      && /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/.test(item.id)) || !unique(inputs.map(item => item.id))) return false
    const resolves = pointer => inputs.every(item => {
      let node = item.spec
      for (const raw of pointer.split('/').slice(1)) {
        const key = raw.replace(/~1/g, '/').replace(/~0/g, '~')
        if (Array.isArray(node)) {
          if (!/^(?:0|[1-9][0-9]*)$/.test(key) || Number(key) >= node.length) return false
          node = node[Number(key)]
        } else if (node && typeof node === 'object' && Object.hasOwn(node, key)) node = node[key]
        else return false
      }
      return typeof node === 'string' || Number.isFinite(node)
    })
    // {input}, {run}, {out}, {spec:<pointer>}; {{ and }} are literal braces; any other brace is invalid.
    const placeholders = item => {
      for (let i = 0; i < item.length; i++) {
        if (item[i] === '}') {
          if (item[i + 1] !== '}') return false
          i++
        } else if (item[i] === '{') {
          if (item[i + 1] === '{') { i++; continue }
          const end = item.indexOf('}', i)
          if (end < 0) return false
          const token = item.slice(i + 1, end)
          if (!['input', 'run', 'out'].includes(token) && !(token.startsWith('spec:')
            && pointerPattern.test(token.slice(5)) && resolves(token.slice(5)))) return false
          i = end
        }
      }
      return true
    }
    if (!sized(arms, 2, 5) || !arms.every((arm, index) => exactObject(arm, ['id', 'what', 'commands', 'env'])
      && arm.id === `A${index}` && text(arm.what) && sized(arm.commands, 1, 8)
      && arm.commands.every(command => sized(command, 1, Infinity) && command.every(part => text(part) && placeholders(part)))
      && (arm.env === null || (exactObject(arm.env, Object.keys(arm.env)) && Object.entries(arm.env).every(([key, item]) =>
        /^[A-Z_][A-Z0-9_]{0,63}$/.test(key) && !key.startsWith('CMP_') && typeof item === 'string' && placeholders(item)))))) return false
    if (!sized(outputs, 0, 10) || !unique(outputs.map(item => item?.name))
      || !outputs.every(item => exactObject(item, ['name', 'what', 'format', 'select']) && named(item.name) && text(item.what)
        && ['bytes', 'text_numbers', 'json_numbers'].includes(item.format)
        && (item.select === null || (item.format !== 'json_numbers' && typeof item.select === 'string')))) return false
    if (!sized(metrics, 1, 10) || !unique(metrics.map(item => item?.name))
      || !metrics.every(item => exactObject(item, ['name', 'unit', 'what', 'source', 'reduce', 'expect_count'])
        && named(item.name) && text(item.unit) && text(item.what)
        && (item.source === 'trusted_wall' ? item.reduce === null && item.expect_count === null
          : item.source === 'sealed_extraction' && ['first', 'max', 'value_at_max_key'].includes(item.reduce)
            && (item.expect_count === null || integer(item.expect_count, 1))))) return false
    if (!(evaluator === null || (exactObject(evaluator, ['what', 'spec', 'timeout_s']) && text(evaluator.what)
      && (evaluator.timeout_s === null || integer(evaluator.timeout_s, 1))))) return false
    if (!integer(value.replicates, 1, 30) || !integer(value.warmup, 0, 3) || !integer(value.order_seed)
      || !integer(value.bootstrap_seed) || !integer(value.bootstrap_resamples, 1000, 1000000) || !integer(value.budget_s, 1)
      || (Object.hasOwn(input, 'run_ceiling_s') && !(value.budget_s < input.run_ceiling_s))) return false
    const armIds = arms.map(arm => arm.id), inputIds = inputs.map(item => item.id)
    const timeout = value.timeout_s
    if (!(timeout === null || integer(timeout, 1) || (exactObject(timeout, armIds) && armIds.every(id => integer(timeout[id], 1)
      || (exactObject(timeout[id], inputIds) && inputIds.every(key => integer(timeout[id][key], 1))))))) return false
    if (!sized(comparisons, 0, 12)) return false
    const tolerances = { exact: null, elementwise_abs: ['abs'], elementwise_abs_plus_rel_max: ['abs', 'rel'] }
    const earlier = []
    for (const item of comparisons) {
      if (!exactObject(item, ['id', 'arm', 'against', 'measure', 'criterion', 'direction', 'unit', 'pairing', 'rule',
        'confidence', 'margin', 'threshold', 'strict', 'reference', 'missing', 'given', 'parts'])) return false
      const output = exactObject(item.measure, ['output', 'comparator'])
      const perInput = ['per_input_all', 'per_input_each'].includes(item.unit)
      const ratio = item.criterion === 'ratio_at_least'
      if (output && !Object.hasOwn(tolerances, item.measure.comparator)) return false
      const keys = output ? tolerances[item.measure.comparator]
        : ['non_inferiority', 'superiority'].includes(item.criterion) && item.margin !== null ? ['abs'] : null
      if (!(typeof item.id === 'string' && /^K[0-9]{1,2}$/.test(item.id) && !earlier.includes(item.id)
        && armIds.includes(item.arm) && item.against !== item.arm && (armIds.includes(item.against) || item.against === 'reference')
        && sized(item.parts, 1, Infinity) && item.parts.every(text) && unique(item.parts)
        && (output ? outputs.some(entry => entry.name === item.measure.output) && armIds.includes(item.against)
          : exactObject(item.measure, ['metric']) && metrics.some(entry => entry.name === item.measure.metric))
        && ['agreement', 'non_inferiority', 'superiority', 'ratio_at_least'].includes(item.criterion)
        && (item.criterion === 'agreement') === output
        && (['agreement', 'superiority'].includes(item.criterion) ? item.direction === 'two_sided'
          : ['higher_better', 'lower_better'].includes(item.direction))
        && (ratio ? item.unit === 'pooled_mean' && item.pairing === 'paired_replicate' && item.rule === 'bootstrap'
          : item.rule === 'all_pairs' && perInput && ['paired_replicate', 'unpaired'].includes(item.pairing)
            && (item.criterion !== 'agreement' || item.pairing === 'paired_replicate'))
        && (item.rule === 'bootstrap' ? Number.isFinite(item.confidence) && item.confidence >= 0.5 && item.confidence < 1
          : item.confidence === null)
        && (keys === null ? item.margin === null
          : exactObject(item.margin, keys) && keys.every(key => Number.isFinite(item.margin[key]) && item.margin[key] >= 0))
        && (ratio ? Number.isFinite(item.threshold) && item.threshold > 0 && typeof item.strict === 'boolean'
          : item.threshold === null && item.strict === null)
        && (item.against === 'reference'
          ? exactObject(item.reference, ['source', 'values']) && text(item.reference.source)
            && exactObject(item.reference.values, inputIds) && inputIds.every(id => Number.isFinite(item.reference.values[id]))
            && perInput && item.pairing === 'unpaired'
          : item.reference === null)
        && ['void', 'fail'].includes(item.missing)
        && Array.isArray(item.given) && unique(item.given) && item.given.every(id => earlier.includes(id)))) return false
      earlier.push(item.id)
    }
    return pythonGroups(outputs.filter(item => item.select !== null).map(item => ['some', item.select]))
  }
  async function prepareComparison() {
    const value = input.comparison
    if (!exactObject(value, ['design']) || typeof value.design !== 'string' || !value.design.trim() || cardMode
      || Object.hasOwn(input, 'units_check') || Object.hasOwn(input, 'units_probe')) throw new Error('invalid comparison')
    const source = path.resolve(value.design)
    const bytes = readFileSync(source)
    const parsed = JSON.parse(bytes.toString('utf8'))
    if (!await validDesign(parsed)) throw new Error('invalid comparison')
    design = parsed
    const comparisonText = JSON.stringify({ source, source_sha256: sha256(bytes), design }, null, 2) + '\n'
    writeAtomic(path.join(C, 'comparison.json'), comparisonText)
    writeAtomic(path.join(C, 'comparison_seal.json'), JSON.stringify({
      comparison_sha256: sha256(comparisonText), sealed_utc: new Date().toISOString() }, null, 2) + '\n')
    const { arms, inputs, outputs, metrics, evaluator, replicates, warmup } = design
    writeAtomic(comparisonViewPath, JSON.stringify({ arms, inputs, outputs, metrics,
      evaluator: evaluator === null ? null : { what: evaluator.what, spec: evaluator.spec }, replicates, warmup }, null, 2) + '\n')
    // Hidden from every agent call: the run, the journal, the design's directory and its git work tree.
    const parent = path.dirname(source)
    let top = parent
    while (!existsSync(path.join(top, '.git')) && path.dirname(top) !== top) top = path.dirname(top)
    hiddenPaths = [root, path.dirname(agent.journal || path.join(A, 'wf', 'journal.jsonl')), parent,
      ...(existsSync(path.join(top, '.git')) ? [top] : [])]
  }
  const views = []
  function privateView(label, entries) {
    const view = mkdtempSync(path.join(tmpdir(), `m5-${label}-`))
    views.push(view)
    writeFileSync(path.join(view, 'comparison_view.json'), readFileSync(comparisonViewPath))
    for (const [name, source] of entries) {
      if (source) cpSync(source, path.join(view, name), { recursive: true })
      else mkdirSync(path.join(view, name), { recursive: true })
    }
    return view
  }
  const isolation = view => ({ isolation: { directory: view, box_access: false, hidden: hiddenPaths } })
  function copyRegular(from, to, names) {
    // Only regular files directly under `from`: no links, no subdirectories.
    let listed
    try { listed = names ?? readdirSync(from) } catch { return }
    mkdirSync(to, { recursive: true })
    for (const name of listed) {
      try {
        if (lstatSync(path.join(from, name)).isFile()) writeFileSync(path.join(to, name), readFileSync(path.join(from, name)))
      } catch { /* A missing file is not copied. */ }
    }
  }
  function removeView(directory) {
    try {
      chmodSync(directory, 0o700)
      for (const name of readdirSync(directory)) {
        if (lstatSync(path.join(directory, name)).isDirectory()) removeView(path.join(directory, name))
      }
    } catch { /* rmSync removes what it can. */ }
    rmSync(directory, { recursive: true, force: true })
  }
  const comparisonFiles = () => [...design.arms.map(arm => `arms/${arm.id}.sh`), 'cmp_files.json', 'cmp_extract.json',
    'versions.sh', ...(design.evaluator === null ? [] : ['fetch_private.sh', 'evaluate.sh'])]
  async function validComparisonHarness() {
    const evaluator = design.evaluator !== null
    const regular = name => { try { return lstatSync(path.join(harnessDirectory, name)).isFile() } catch { return false } }
    const adapters = design.arms.map(arm => `${arm.id}.sh`)
    let listed
    try { listed = readdirSync(path.join(harnessDirectory, 'arms')) } catch { return false }
    if (listed.length !== adapters.length || !adapters.every(name => listed.includes(name) && regular(`arms/${name}`)
      && statSync(path.join(harnessDirectory, 'arms', name)).size > 0)) return false
    if (!regular('versions.sh') || ['fetch_private.sh', 'evaluate.sh'].some(name =>
      evaluator ? !regular(name) : existsSync(path.join(harnessDirectory, name)))) return false
    const relative = (item, part, first) => typeof item === 'string' && first.includes(item.split('/')[0])
      && item.split('/').every(component => part.test(component) && component !== '.' && component !== '..')
    const plainPart = /^[A-Za-z0-9._+=-]+$/, globPart = /^[A-Za-z0-9._+=*?[\]-]+$/
    const first = evaluator ? ['out', 'log', 'eval'] : ['out', 'log']
    const armIds = design.arms.map(arm => arm.id), names = design.outputs.map(item => item.name)
    let files, extract
    try {
      files = readJSON(path.join(harnessDirectory, 'cmp_files.json'))
      extract = readJSON(path.join(harnessDirectory, 'cmp_extract.json'))
    } catch { return false }
    if (!exactObject(files, ['files']) || !exactObject(files.files, armIds)
      || !armIds.every(id => exactObject(files.files[id], names) && names.every(name => {
        const location = files.files[id][name]
        return relative(location, plainPart, first) || (exactObject(location, ['glob']) && relative(location.glob, globPart, first))
      }))) return false
    const reduce = Object.fromEntries(design.metrics.filter(item => item.source === 'sealed_extraction').map(item => [item.name, item.reduce]))
    const expected = armIds.flatMap(id => Object.keys(reduce).map(name => `${id}/${name}`))
    if (!exactObject(extract, ['rules']) || !Array.isArray(extract.rules) || extract.rules.length !== expected.length) return false
    const seen = new Set()
    for (const rule of extract.rules) {
      if (!exactObject(rule, ['arm', 'metric', 'file', 'kind', 'expr']) || typeof rule.arm !== 'string'
        || typeof rule.metric !== 'string') return false
      const key = `${rule.arm}/${rule.metric}`
      if (!expected.includes(key) || seen.has(key) || !relative(rule.file, plainPart, ['out', 'log', 'eval'])
        || typeof rule.expr !== 'string' || !(rule.kind === 'regex' || (rule.kind === 'json' && pointerPattern.test(rule.expr)))) return false
      seen.add(key)
    }
    return pythonGroups(extract.rules.filter(rule => rule.kind === 'regex')
      .map(rule => [reduce[rule.metric] === 'value_at_max_key' ? '2' : '1', rule.expr]))
  }

  async function intake() {
    if (comparisonMode) {
      try { await prepareComparison() } catch { return failure({ ...nullFacts('intake'), tokens_known: false, gpu_busy_known: false }, 'parse') }
    }
    if (cardMode) {
      try { prepareCard() } catch { return failure({ ...nullFacts('intake'), tokens_known: false, gpu_busy_known: false }, 'parse') }
    }
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
    // Comparison mode: the agent reads and writes only its private view; the pipeline copies intake/ back.
    let view = null, shownBrief = briefPath, written = directory
    if (comparisonMode) {
      try {
        view = privateView('intake', [['intake', null]])
        written = path.join(view, 'intake')
        if (briefPath) {
          shownBrief = path.join(view, 'brief', path.basename(briefPath))
          mkdirSync(path.dirname(shownBrief))
          try {
            if (statSync(briefPath).isFile()) writeFileSync(shownBrief, readFileSync(briefPath))
          } catch { /* An unreadable brief stays absent; the agent reports found=false. */ }
        }
      } catch { return fail() }
    }
    const prompt = `Perform scientific benchmark intake in one bounded pass.
${briefPath
  ? `Read the brief file ${JSON.stringify(shownBrief)}. Extract its benchmark; if unreadable or unsupported, report found=false. Do not substitute another benchmark. Copy the brief to intake/brief.md when readable.`
  : `Search for a public benchmark, inspecting at most three candidates and using at most two search calls. ${brief ? `Search hint: ${JSON.stringify(brief)}.` : ''} If none qualifies, report found=false. Never invent a benchmark, citation, published number, tolerance, pin, or command.`}
Write only under ${JSON.stringify(written)}. Never read experiments/, operator/, or control/.
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
Gate: complete files, found, available required data, licence is not "restricted", and stock_environment is not false. Missing published tolerances do not block. Missing evidence must stay unknown.${cardMode ? `
This run calibrates the inputs listed in ${JSON.stringify(cardInputsPath)}. EXECUTION.json's representative workload is the protocol of the phases those inputs name (their measured_by and phase), not another workload.` : ''}${view ? `
This run compares the arms listed in ${JSON.stringify(path.join(view, 'comparison_view.json'))} on the inputs listed there. Arm A0 is the benchmark: record it in the five files as usual. Also record, in benchmark.json under the JSON key "arms", each other arm's published source, pin and commands, keyed by arm id${design.evaluator === null ? '' : `; in benchmark.json under the JSON key "evaluator", the evaluator's published source, pin and command`}; and in data.json every input any arm${design.evaluator === null ? '' : ' or the evaluator'} needs${design.evaluator === null ? '' : `, marking the evaluator's private data and stating where each private item is published`}.` : ''}`
    try {
      const reply = await agent(prompt, { label: 'intake', agentType: 'ls-writer', model: 'sonnet', schema: intakeSchema,
        ...(view ? isolation(view) : {}) })
      if (view) copyRegular(written, directory)
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
  const extractPath = path.join(harnessDirectory, 'card_extract.json')
  async function validCardExtract() {
    const value = readJSON(extractPath)
    const ids = [...cardInputs.inputs.map(item => item.id), ...(cardInputs.anchor ? ['anchor'] : [])]
    const exactKeys = (item, keys) => item && typeof item === 'object' && !Array.isArray(item)
      && Object.keys(item).length === keys.length && keys.every(key => Object.hasOwn(item, key))
    if (!exactKeys(value, ['rules']) || !Array.isArray(value.rules) || value.rules.length !== ids.length
      || !value.rules.every((rule, index) => exactKeys(rule, ['id', 'file', 'kind', 'expr']) && rule.id === ids[index]
        && typeof rule.file === 'string' && rule.file.split('/').every(part => /^[A-Za-z0-9._+=-]+$/.test(part) && part !== '.' && part !== '..')
        && typeof rule.expr === 'string' && (rule.kind === 'regex'
          || (rule.kind === 'json' && /^(?:\/(?:[^~/]|~[01])*)*$/.test(rule.expr))))) return false
    // Python's re decides what a pattern is; exactly one capturing group each.
    const patterns = value.rules.filter(rule => rule.kind === 'regex').map(rule => rule.expr)
    if (patterns.length) {
      try {
        await exec('python3', ['-I', '-c', 'import re, sys\nsys.exit(0 if all(re.compile(p).groups == 1 for p in sys.argv[1:]) else 1)', ...patterns])
      } catch { return false }
    }
    return true
  }
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
    const authored = ['setup', 'anchors', 'units-check', 'profile', 'concurrency', 'adapter-smoke', 'setup-method', 'run-method', 'run-tests']
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
      if (name.includes('/')) commands.push(`mkdir -p ${quote(path.posix.dirname(remote))}`)
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
      const protectedScripts = new Map([...(name === 'setup.sh' ? [] : ['setup.sh', 'run_evaluation.sh']),
        'run_units.sh', 'units.json', ...(cardMode ? ['card_extract.json'] : [])].map(file =>
        [file, existsSync(path.join(harnessDirectory, file)) ? readFileSync(path.join(harnessDirectory, file)) : null]))
      // Comparison mode: the repair works on copies in its private view; only its permitted scripts come back.
      const view = comparisonMode ? privateView(name === 'setup.sh' ? 'harness-repair' : `${operation}-repair`,
        [['intake', path.join(A, 'intake')], ['harness', harnessDirectory]]) : null
      const shown = view ? path.join(view, 'harness') : harnessDirectory
      const scope = name === 'setup.sh' ? `Repair only ${JSON.stringify(path.join(shown, name))}`
        : `Repair run_anchors.sh, run_command.sh, or both under ${JSON.stringify(shown)}, and nothing else. A rewritten run_command.sh must still obey every run_command.sh rule`
      const viewPrompt = view ? ` The intake files are under ${JSON.stringify(path.join(view, 'intake'))} and the compared arms and inputs are listed in ${JSON.stringify(path.join(view, 'comparison_view.json'))}.` : ''
      const repair = await agent(`${name} failed (rc ${result.rc}${result.error ? `, output gate: ${result.error}` : ''}). ${scope} using intake evidence.${viewPrompt} Preserve the published pin, configuration and stock image; sudo only for apt. ${harnessRules} Never read experiments/, operator/, or control/. Do not run workloads locally or access the box. This is repair attempt ${retry} of ${repairLimit} for this ${name === 'setup.sh' ? 'script' : 'step'}.
Budget: ${executionTimeout(timeout)}s resolved now, the time left before the run ceiling, not a target (explicit args budget overrides); failed attempt budget: ${result.budget_s}s; measured elapsed: ${result.wall_s ?? 'unavailable'}s; measured overrun: ${Number.isFinite(result.wall_s) ? Math.max(0, result.wall_s - result.budget_s) : 'unavailable'}s. ${budgetPrompt()}
${boxProbePrompt()}
Log tail (at most 200 lines):\n${tail}`,
        { label: name === 'setup.sh' ? 'harness-repair' : `${operation}-repair`, agentType: 'ls-writer', model: 'sonnet', retry,
          ...(view ? isolation(view) : {}) })
      if (view) copyRegular(shown, harnessDirectory, names)
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
  function unitSample() {
    readFileSync(path.join(harnessDirectory, 'run_units.sh'))
    const manifest = readJSON(path.join(harnessDirectory, 'units.json'))
    const exactKeys = (value, keys) => value && typeof value === 'object' && !Array.isArray(value)
      && Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key))
    if (!exactKeys(manifest, ['units']) || !Array.isArray(manifest.units) || manifest.units.length < 4
      || new Set(manifest.units.map(unit => unit?.id)).size !== manifest.units.length
      || !manifest.units.every(unit => exactKeys(unit, ['id', 'outputs', 'cost_s'])
        && typeof unit.id === 'string' && /^[A-Za-z0-9][A-Za-z0-9._:+=-]{0,127}$/.test(unit.id) && !unit.id.includes('\n')
        && Number.isFinite(unit.cost_s) && unit.cost_s > 0
        && Array.isArray(unit.outputs) && unit.outputs.length > 0 && new Set(unit.outputs).size === unit.outputs.length
        && unit.outputs.every(file => typeof file === 'string' && file.split('/').every(part => part.length > 0
          && !/[^A-Za-z0-9._+=-]/.test(part) && part !== '.' && part !== '..')))) throw new Error('invalid units')
    const sorted = manifest.units.map((unit, index) => ({ ...unit, index }))
      .sort((a, b) => a.cost_s - b.cost_s || a.index - b.index)
    const start = Math.floor((sorted.length - 4) / 2)
    return sorted.slice(start, start + 4)
  }
  function unitsCheckCommand(sample) {
    return `python3 - <<'PY'
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

root = Path.cwd()
work = root / "units-check"
output = root / "out" / "units-check"
for directory in (work, output):
    if directory.exists():
        shutil.rmtree(directory)
work.mkdir()
output.mkdir(parents=True)
for entry in root.iterdir():
    if entry.name not in ("out", "profiler", "concurrency-work", "evaluation-work", "units-check"):
        (work / entry.name).symlink_to(entry)
(work / "out").mkdir()
with (output / "run.log").open("wb") as log:
    start = time.monotonic()
    result = subprocess.run(["bash", "harness/run_units.sh", ${sample.map(unit => quote(unit.id)).join(', ')}],
                            cwd=work, stdout=log, stderr=subprocess.STDOUT)
    wall = time.monotonic() - start
(output / "wall.json").write_text(json.dumps({"wall_s": wall}) + "\\n")
shutil.copytree(work / "out", output / "files")
sys.exit(result.returncode if result.returncode >= 0 else 128 - result.returncode)
PY`
  }
  function matchedUnitFiles(sample, left, right) {
    let total = 0, matched = 0
    for (const unit of sample) {
      for (const file of unit.outputs) {
        total++
        try {
          if (readFileSync(path.join(left, file)).equals(readFileSync(path.join(right, file)))) matched++
        } catch { /* Missing or unreadable files are mismatches. */ }
      }
    }
    return { total, matched, match: matched === total }
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
    const unitsMode = Object.hasOwn(input, 'units_check')
    const unitsProbe = Object.hasOwn(input, 'units_probe')
    let reference
    try {
      if (unitsMode && unitsProbe) return failure(facts, 'parse')
      if (unitsMode || unitsProbe) {
        const value = unitsProbe ? input.units_probe : input.units_check
        if (!value || typeof value !== 'object' || Array.isArray(value) || Object.keys(value).length !== 1
          || !Object.hasOwn(value, 'reference') || typeof value.reference !== 'string' || !value.reference.trim()) return failure(facts, 'parse')
        reference = path.resolve(value.reference)
        if (!statSync(reference).isDirectory()) return failure(facts, 'parse')
      }
      executionTimeout('setup')
      executionTimeout('anchors')
    } catch { return failure(facts, 'parse') }
    try {
      await collectBoxProbe('setup')
    } catch (error) { return failure(facts, error.error_class || 'infra') }
    // The separated users of a comparison with an evaluator need passwordless sudo.
    if (comparisonMode && design.evaluator !== null && boxProbe.sudo_nopasswd !== true) return failure(facts, 'infra')
    try {
      // Comparison mode: the harness agent writes into its private view; the pipeline copies harness/ back.
      const view = comparisonMode && input.harness_from == null
        ? privateView('harness', [['intake', path.join(A, 'intake')], ['harness', null]]) : null
      const shown = view ? path.join(view, 'harness') : harnessDirectory
      const evaluator = comparisonMode && design.evaluator !== null
      const prompt = `Write a baseline harness from ${JSON.stringify(view ? path.join(view, 'intake') : path.join(A, 'intake'))}/*.
Never read experiments/, operator/, or control/. Write only under ${JSON.stringify(shown)}.
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
Return a short completion acknowledgement; the pipeline reads the scripts itself.${cardMode ? `
This run calibrates the inputs listed in ${JSON.stringify(cardInputsPath)}. The representative run must write outputs under out/ from which each listed input${cardInputs?.anchor ? ', and the anchor quantity that file names,' : ''} can be read. Declare how each one is read in ${JSON.stringify(extractPath)}, exactly {"rules": [...]}: one rule per listed input, in the listed order, with that input's id${cardInputs?.anchor ? ', then one rule with id "anchor"' : ''}. Each rule is exactly {"id", "file", "kind", "expr"}. file is a path relative to out/, made of /-separated components of A-Za-z0-9._+=- characters, none of them "." or "..". kind "json": expr is a JSON Pointer (RFC 6901) into that file, and the value there must be a finite JSON number. kind "regex": expr is a Python re pattern with exactly one capturing group; the file is read as UTF-8 and the last match's group must parse with float() as a finite number. The pipeline reads the values with these rules; no harness script computes, writes or asserts a value for these inputs.` : ''}${view ? `
This run compares the arms listed in ${JSON.stringify(path.join(view, 'comparison_view.json'))} on the inputs listed there. A0 is the published baseline: run_anchors.sh and run_command.sh keep their meaning for A0. setup.sh also builds or installs every arm's published program and configuration${evaluator ? ', and the evaluator,' : ''} as published, under the shared run directory or with apt, never under the home directory.${evaluator ? ` setup.sh never fetches, copies or writes the evaluator's private data; only fetch_private.sh does.` : ''} Besides the usual scripts, write under ${JSON.stringify(shown)}:
- arms/<arm id>.sh, one adapter per arm, A0 included. It only prepares the invocation: it stages the input named by CMP_INPUT (its spec is the JSON in CMP_INPUT_SPEC) under run/, its working directory, or under CMP_OUT. It never runs the arm's program, writes or patches source, or computes, writes or asserts a metric; the pipeline runs the arm's commands itself.${evaluator ? `
- fetch_private.sh: fetches every input data.json marks as the evaluator's private data from where it is published, writing only under its working directory.
- evaluate.sh: runs the published, pinned evaluator on the arm output in CMP_ARM_OUT for the input named by CMP_INPUT, reads private data only under CMP_PRIVATE, writes its results under CMP_EVAL_OUT, and never writes elsewhere.` : ''}
- cmp_files.json, exactly {"files": {...}}, mapping each arm id to an object that maps every output name to a location: a relative path, or exactly {"glob": pattern} with a pattern of relative-path components that may also use *, ?, [ and ]. Locations are relative to the invocation directory, and their first component is out (the arm's files), log (the standard output and error of the arm's adapter and commands)${evaluator ? ' or eval (the evaluator\'s files)' : ''}.
- cmp_extract.json, exactly {"rules": [...]}, one rule per arm and sealed_extraction metric, each exactly {"arm", "metric", "file", "kind", "expr"}, with file a relative path whose first component is out or log${evaluator ? ' or eval' : ''}. kind "json": expr is a JSON Pointer (RFC 6901) to a finite number, to an array of finite numbers, or (for reduce value_at_max_key) to an array of two-element [key, value] arrays of finite numbers. kind "regex": expr is a Python re pattern with exactly one capturing group, or exactly two (key, then value) for value_at_max_key; matches are parsed with float().
- versions.sh, which prints one JSON object mapping each arm id${evaluator ? ' and "evaluator"' : ''} to exactly {"version", "executable"}: the program's version string and the path, absolute or relative to the shared run directory, of its main executable file.
Relative paths are one or more /-separated components made of A-Za-z0-9._+=- characters, none of them "." or "..". The pipeline checks and seals these files before any run; no repair changes them.` : ''}`
      mkdirSync(harnessDirectory, { recursive: true })
      if (comparisonMode) mkdirSync(path.join(harnessDirectory, 'arms'), { recursive: true })
      if (input.harness_from != null) {
        if (typeof input.harness_from !== 'string' || !input.harness_from.trim()) return failure(facts, 'parse')
        const source = path.resolve(input.harness_from)
        const names = ['setup.sh', 'run_anchors.sh', 'run_command.sh', ...(cardMode ? ['card_extract.json'] : []),
          ...['run_evaluation.sh', 'run_units.sh', 'units.json'].filter(name => existsSync(path.join(source, name))),
          ...(comparisonMode ? comparisonFiles() : [])]
        const scripts = names.map(name => [name, readFileSync(path.join(source, name))])
        harnessSource = { source, files: {} }
        for (const [name, bytes] of scripts) {
          writeFileSync(path.join(harnessDirectory, name), bytes)
          harnessSource.files[name] = { sha256: createHash('sha256').update(bytes).digest('hex'), modified: false }
        }
        writeHarnessSource()
      } else {
        const reply = await agent(prompt, { label: 'harness', agentType: 'ls-writer', model: 'sonnet', ...(view ? isolation(view) : {}) })
        if (view) {
          copyRegular(shown, harnessDirectory)
          copyRegular(path.join(shown, 'arms'), path.join(harnessDirectory, 'arms'), design.arms.map(arm => `${arm.id}.sh`))
        }
        if (reply == null) return failure(facts, 'parse')
      }
      if (comparisonMode) {
        // The comparison files are fixed before any run, sealed, uploaded with the harness, and never repaired.
        if (!await validComparisonHarness()) return failure(facts, 'parse')
        writeAtomic(path.join(C, 'arms_seal.json'), JSON.stringify({
          files: Object.fromEntries(comparisonFiles().map(name => [name, sha256(readFileSync(path.join(harnessDirectory, name)))])),
          sealed_utc: new Date().toISOString() }, null, 2) + '\n')
      }
      if (cardMode) {
        // The extraction rules are fixed before the workload runs; no repair changes them.
        if (!await validCardExtract()) return failure(facts, 'parse')
        writeAtomic(path.join(C, 'card_extract_seal.json'), JSON.stringify({
          extract_sha256: sha256(readFileSync(extractPath)), sealed_utc: new Date().toISOString() }, null, 2) + '\n')
      }
      const sample = unitsMode || unitsProbe ? unitSample() : null
      const referenceFile = path.join(destination, 'units_reference.json')
      if (unitsProbe) {
        const sha256 = Object.fromEntries(sample.flatMap(unit => unit.outputs.map(file =>
          [file, createHash('sha256').update(readFileSync(path.join(reference, file))).digest('hex')])))
        mkdirSync(destination, { recursive: true })
        writeFileSync(referenceFile, JSON.stringify({ sha256 }, null, 2) + '\n')
      }
      const uploaded = await uploadHarness(['setup.sh', 'run_anchors.sh', 'run_command.sh',
        ...['run_evaluation.sh', 'run_units.sh', 'units.json'].filter(name => existsSync(path.join(harnessDirectory, name))),
        ...(comparisonMode ? comparisonFiles() : [])], destination, 'setup')
      if (uploaded.error || uploaded.rc !== 0) return failure(facts, uploaded.error || 'infra')
      const setup = await runHarness('setup.sh', 'setup', destination, 'setup')
      if (setup.error) {
        facts.stock_verified = setup.rc === 0 && setup.error !== 'timeout'
        return failure(facts, setup.error)
      }
      facts.stock_verified = setup.rc === 0
      if (!facts.stock_verified) return failure(facts, 'install')
      if (unitsProbe) {
        const bytes = readFileSync('m5/concurrency_probe.py').toString('base64')
        const referenceBytes = readFileSync(referenceFile).toString('base64')
        const probe = await boxCommand('concurrency', seconds => `set -e
mkdir -p profiler
printf %s ${quote(bytes)} | base64 -d > profiler/concurrency_probe.py
printf %s ${quote(referenceBytes)} | base64 -d > profiler/units_reference.json
rm -rf out/concurrency concurrency-work
python3 -I profiler/concurrency_probe.py --units harness/run_units.sh harness/units.json out/concurrency ${seconds} profiler/units_reference.json`, destination, 'anchors')
        if (probe.error) return failure(facts, probe.error)
        if (probe.fetched !== true) return failure(facts, 'infra')
        if (probe.rc !== 0) return failure(facts, 'parse')
        const value = readJSON(path.join(destination, 'out', 'concurrency', 'concurrency.json'))
        if (!validUnitConcurrency(value)) return failure(facts, 'parse')
        facts.units_outcome = value.outcome
        facts.units_factor_2 = value.batches[0].factor
        facts.units_factor_4 = value.batches[1].factor
        const ran = value.arms.filter(arm => !arm.skipped)
        facts.units_shared_writes = ran.length ? ran.some(arm => arm.shared_changes > 0) : null
        return { status: 'PASS', facts }
      }
      let unitsCheck
      const subsetDirectory = path.join(destination, 'units-check')
      const writeUnitsCheck = () => {
        const file = path.join(destination, 'units_check.json')
        const temporary = `${file}.${randomUUID()}.tmp`
        writeFileSync(temporary, JSON.stringify(unitsCheck, null, 2) + '\n')
        renameSync(temporary, file)
        facts.units_match = unitsCheck.subset_match
        facts.units_full_match = unitsCheck.full_match
      }
      if (unitsMode) {
        const subset = await boxCommand('units-check', unitsCheckCommand(sample), destination, 'anchors')
        if (subset.error) return failure(facts, subset.error)
        if (subset.fetched !== true) return failure(facts, 'infra')
        rmSync(subsetDirectory, { recursive: true, force: true })
        cpSync(path.join(destination, 'out', 'units-check'), subsetDirectory, { recursive: true })
        const files = matchedUnitFiles(sample, path.join(subsetDirectory, 'files'), reference)
        let wall = null
        try {
          const value = readJSON(path.join(subsetDirectory, 'wall.json')).wall_s
          if (Number.isFinite(value) && value > 0) wall = value
        } catch { /* Timing is optional evidence. */ }
        const cost = sample.reduce((sum, unit) => sum + unit.cost_s, 0)
        unitsCheck = { sample: sample.map(({ index, cost_s }) => ({ index, cost_s })), subset_rc: subset.rc,
          subset_wall_s: wall, cost_sum_s: cost, cost_ratio: wall === null ? null : wall / cost,
          files_total: files.total, files_matched: files.matched, subset_match: subset.rc === 0 && files.match,
          full_ran: false, full_match: null, subset_vs_full_match: null }
        writeUnitsCheck()
        if (subset.rc !== 0 || unitsCheck.subset_match) return { status: 'PASS', facts }
      }
      const anchors = await runHarness('run_anchors.sh', 'anchors', destination, 'anchors')
      if (unitsMode) {
        unitsCheck.full_ran = anchors.budget_s !== 0
        if (anchors.rc === 0 && !anchors.error) {
          const full = path.join(destination, 'out')
          unitsCheck.full_match = matchedUnitFiles(sample, full, reference).match
          unitsCheck.subset_vs_full_match = matchedUnitFiles(sample, path.join(subsetDirectory, 'files'), full).match
        }
        writeUnitsCheck()
      }
      if (anchors.error) return failure(facts, anchors.error)
      if (anchors.rc !== 0) return failure(facts, 'anchor')
      if (cardMode) {
        // Card rows are measured and reported, as references are; they never change status, gate or run_valid.
        const scored = path.join(C, 'card_scored.json')
        rmSync(scored, { force: true })
        try {
          await exec('python3', ['-I', 'm5/score_card.py', C, extractPath, path.join(destination, 'out'),
            '--run', String(input.tag), '--commit', typeof input.pipeline_commit === 'string' ? input.pipeline_commit : '-'])
        } catch { return failure(facts, 'parse') }
        const card = readJSON(scored)
        facts.card_inputs = card.inputs_total
        facts.card_measured = card.measured_total
        facts.card_holds = card.holds_total
        facts.card_refuted = card.refuted_total
      }
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
      if (passed && !unitsMode) {
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
      facts.host_only = null
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
        const hostOnly = gpuUtil.length > 0 && gpuUtil.every(item => item.util === 0)
          && ['kernels', 'memcpy H2D', 'memcpy D2H', 'CUDA API host time'].every(name => {
            const rows = stages.filter(item => item.stage === name)
            return rows.length > 0 && rows.every(item => item.wall_s === 0 && (item.gpu_s === 0 || item.gpu_s === null))
          })
        writeFileSync(path.join(A, 'profile-packet.json'), JSON.stringify({
          stages: measuredStages, total_wall_s, concurrency: null, host_only: hostOnly,
          timed_fraction: facts.timed_fraction, gpu_telemetry: facts.gpu_telemetry,
          gpu_count: Number.isInteger(allocationCount) && allocationCount >= 0 ? allocationCount
            : Array.isArray(boxProbe?.nvidia?.gpus) ? boxProbe.nvidia.gpus.length : 1,
        }, null, 2) + '\n')
        facts.host_only = hostOnly
        const processWrapper = stages.some(item => /(?:^|[\s_-])(?:process|wrapper|telemetry|total|overall)(?:$|[\s_-])/i.test(item.stage)
          || (!(hostOnly && item.stage === 'other host time')
            && item.wall_s >= total_wall_s * 0.98 && item.wall_s <= total_wall_s * 1.02))
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
  function validUnitConcurrency(value) {
    const keys = (item, expected) => item && typeof item === 'object' && !Array.isArray(item)
      && Object.keys(item).length === expected.length && expected.every(key => Object.hasOwn(item, key))
    const positive = item => Number.isFinite(item) && item > 0
    const nullable = item => item === null || positive(item)
    const nonnegative = item => Number.isFinite(item) && item >= 0
    const boolean = item => item === null || typeof item === 'boolean'
    if (!keys(value, ['mode', 'mps', 'mps_failed', 'outcome', 'units_total', 'sample', 'baseline_match',
      'outputs_match', 'serial_wall_s', 'separate_wall_s', 'batches', 'arms', 'nproc', 'mem_total_kb', 'factor'])
      || value.mode !== 'units' || value.mps !== false || value.mps_failed !== false
      || !['invalid_units', 'failed', 'baseline_mismatch', 'outputs_mismatch', 'skipped', 'measured'].includes(value.outcome)
      || !boolean(value.baseline_match) || !boolean(value.outputs_match)
      || !nullable(value.serial_wall_s) || !nullable(value.separate_wall_s) || !nullable(value.factor)
      || !(value.nproc === null || Number.isInteger(value.nproc) && value.nproc > 0)
      || !(value.mem_total_kb === null || Number.isInteger(value.mem_total_kb) && value.mem_total_kb >= 0)
      || !Array.isArray(value.sample) || !Array.isArray(value.batches) || value.batches.length !== 2
      || !Array.isArray(value.arms) || value.arms.length !== 8) return false
    const invalid = value.outcome === 'invalid_units'
    if (invalid ? value.units_total !== null || value.sample.length !== 0
      : !Number.isInteger(value.units_total) || value.units_total < 4 || value.sample.length !== 4) return false
    if (!value.sample.every((unit, index) => keys(unit, ['index', 'cost_s'])
      && Number.isInteger(unit.index) && unit.index >= 0 && unit.index < value.units_total && positive(unit.cost_s)
      && (index === 0 || value.sample[index - 1].cost_s < unit.cost_s
        || value.sample[index - 1].cost_s === unit.cost_s && value.sample[index - 1].index < unit.index))
      || new Set(value.sample.map(unit => unit.index)).size !== value.sample.length) return false
    const labels = ['a-1', 'b-1', 'c2-1', 'c4-1', 'c4-2', 'c2-2', 'b-2', 'a-2']
    const numbers = ['wall_s', 'cpu_s', 'effective_cores', 'busy_fraction', 'mem_available_min_kb', 'threads_max', 'shared_changes']
    if (!value.arms.every((arm, index) => {
      if (!keys(arm, ['label', 'all_ok', 'skipped', ...numbers, 'invocations']) || arm.label !== labels[index]
        || typeof arm.all_ok !== 'boolean' || typeof arm.skipped !== 'boolean'
        || !numbers.every(key => arm[key] === null || nonnegative(arm[key]))
        || !(arm.shared_changes === null || Number.isInteger(arm.shared_changes))
        || !Array.isArray(arm.invocations)) return false
      if (arm.skipped) return !arm.all_ok && numbers.every(key => arm[key] === null) && arm.invocations.length === 0
      if (invalid || (index > 0 && value.arms[index - 1].skipped)
        || !positive(arm.wall_s) || !numbers.every(key => nonnegative(arm[key]))) return false
      const serial = arm.label.startsWith('a')
      return arm.invocations.length === (serial ? 1 : 4) && arm.invocations.every((row, position) =>
        keys(row, ['units', 'rc', 'wall_s', 'cpu_s', 'max_rss_kb', 'nivcsw', 'inblock', 'oublock'])
        && Array.isArray(row.units) && row.units.length === (serial ? 4 : 1)
        && row.units.every((unit, i) => unit === (serial ? i : position)) && Number.isInteger(row.rc)
        && ['wall_s', 'cpu_s', 'max_rss_kb', 'nivcsw', 'inblock', 'oublock'].every(key => nonnegative(row[key]))
        && (!arm.all_ok || row.rc === 0))
    })) return false
    const ran = value.arms.filter(arm => !arm.skipped)
    if ((value.baseline_match === null) !== (ran.length === 0)
      || (value.outputs_match === null) !== (ran.length < 2)
      || ran.length > 1 && !ran[0].all_ok
      || ran.length > 0 && ran[0].all_ok !== (value.baseline_match === true
        && ran[0].invocations.every(row => row.rc === 0))) return false
    const outcome = invalid ? 'invalid_units' : ran.some(arm => arm.invocations.some(row => row.rc !== 0)) ? 'failed'
      : value.baseline_match === false ? 'baseline_mismatch' : value.outputs_match === false ? 'outputs_mismatch'
        : ran.some(arm => arm.label.startsWith('c') && arm.all_ok) ? 'measured' : 'skipped'
    if (value.outcome !== outcome) return false
    const mean = arms => arms.length ? arms.reduce((sum, arm) => sum + arm.wall_s / arms.length, 0) : null
    for (const [prefix, key] of [['a', 'serial_wall_s'], ['b', 'separate_wall_s']]) {
      if (value[key] !== mean(ran.filter(arm => arm.label.startsWith(prefix) && arm.all_ok))) return false
    }
    if (!value.batches.every((batch, index) => {
      if (!keys(batch, ['n', 'wall_s', 'all_ok', 'skipped', 'factor']) || batch.n !== [2, 4][index]
        || typeof batch.all_ok !== 'boolean' || typeof batch.skipped !== 'boolean'
        || !nullable(batch.wall_s) || !nullable(batch.factor)) return false
      const arms = ran.filter(arm => arm.label.startsWith(`c${batch.n}`))
      if (batch.skipped !== (arms.length === 0) || batch.all_ok !== (arms.length > 0 && arms.every(arm => arm.all_ok))
        || batch.wall_s !== mean(arms)) return false
      return batch.factor === (batch.all_ok && value.outcome === 'measured'
        ? value.serial_wall_s / batch.wall_s : null)
    })) return false
    const factors = value.batches.filter(batch => batch.factor !== null).map(batch => batch.factor)
    return value.factor === (factors.length ? Math.max(...factors) : null)
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
    if (comparisonMode) {
      const { default: run } = await import(path.resolve('m5/comparison.js'))
      return run({ A, C, exec, boxCommand, quote, failure, nullFacts, design, runStarted, allocation,
        ceiling_s: Object.hasOwn(input, 'run_ceiling_s') ? input.run_ceiling_s : 43200,
        price: box && nonnegative(box.price_usd_h) ? box.price_usd_h : null })
    }
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
    // A comparison runs reproduce for A0, then evaluate; the method stages never run.
    const comparisonSkip = comparisonMode && ['profile', 'seal', 'propose', 'implement'].includes(stage)
    const result = (stopped_at && stage !== 'takeaways') || comparisonSkip
      ? { status: 'SKIPPED', facts: nullFacts(stage) }
      : await run()
    for (const view of views.splice(0)) {
      try { removeView(view) } catch { /* A view left behind never changes the stage. */ }
    }
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
          // A comparison's compute record: only its allocation is recomputed.
          const compute = path.join(A, 'results', 'evaluate', 'comparison_compute.json')
          if (comparisonMode && existsSync(compute)) {
            writeAtomic(compute, JSON.stringify({ ...readJSON(compute), allocation: allocation() }, null, 2) + '\n')
          }
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
      notes: [...(result.notes ?? []), ...(new Set(families).size > 1 ? ['multiple_model_families'] : [])] }) + '\n')
    await exec('python3', ['m5/signatures.py', 'emit', '--dir', S, '--stage', stage, '--status', result.status,
      '--facts', JSON.stringify(result.facts), '--v1', JSON.stringify(v1)])
    stages.push({ stage, status: result.status })
    log(`${stage}: ${result.status}`)
    if (!stopped_at && !comparisonSkip && (result.status !== 'PASS' || result.facts.outcome === 'no_feasible_method'
      || (stage === 'reproduce' && (Object.hasOwn(input, 'units_check') || Object.hasOwn(input, 'units_probe'))))) stopped_at = stage
  }
  await exec('python3', ['m5/operator_takeaway.py', S, '--raid', raid])
  return { stages, stopped_at }
})()
