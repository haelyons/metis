'use strict'
const fs = require('node:fs')
const path = require('node:path')
const { createHash } = require('node:crypto')
const hash = bytes => createHash('sha256').update(bytes).digest('hex')
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const quote = value => `'${String(value).replace(/'/g, "'\\''")}'`
const write = (file, value) => fs.writeFileSync(file, JSON.stringify(value, null, 2) + '\n')

module.exports = async function evaluate(context) {
  const { A, C, exec, boxCommand, remoteDirectory, executionTimeout, nullFacts } = context
  const facts = { ...nullFacts('evaluate'), tokens_known: true, gpu_busy_known: false }
  const destination = path.join(A, 'results', 'evaluate'), control = path.join(C, 'evaluate')
  const helpers = ['eval_common.py', 'score_anchors.py', 'eval_validity.py', 'eval_equivalence.py', 'eval_performance.py']
  let seal, manifest, frozenState
  const finish = (status, error_class, exit_code) => ({ status, facts, v1: {
    error_class, exit_code, run_valid: facts.validity_pass,
  } })
  function verifySeal() {
    const seals = path.join(C, 'seals')
    const latest = fs.readdirSync(seals).filter(name => /^\d{4,}\.json$/.test(name))
      .sort((a, b) => Number(a.slice(0, -5)) - Number(b.slice(0, -5))).at(-1)
    const receipt = read(path.join(seals, latest || 'missing'))
    if (hash(fs.readFileSync(receipt.path)) !== receipt.sha256
      || hash(fs.readFileSync(path.join(A, 'PREDICTIONS.json'))) !== receipt.sha256
      || (seal && seal.receipt !== latest)) throw new Error('invalid seal')
    return { ...receipt, receipt: latest }
  }
  async function treeHash(directory) {
    return JSON.parse((await exec('python3', [path.join(__dirname, 'implement_state.py'), 'sha256', directory])).stdout).sha256
  }
  async function command(name, body, timeout) {
    const to = path.join(destination, name)
    const result = await boxCommand(name, `set -e\n${body}`, to, timeout)
    if (result.timed_out) return { error: 'timeout', rc: 124 }
    if (result.error || result.fetched !== true) return { error: 'infra' }
    return { ...result, to }
  }
  async function intact(phase) {
    verifySeal()
    if (await treeHash(path.join(A, 'tests')) !== frozenState.tests_sha256) throw new Error('changed tests')
    for (const row of manifest.method_files) {
      if (hash(fs.readFileSync(path.join(A, 'method', row.path))) !== row.sha256) throw new Error('changed method')
    }
    const helper = fs.readFileSync(path.join(__dirname, 'implement_state.py')).toString('base64')
    const keys = ['baseline_sha256 baseline-published', 'data_sha256 data', 'baseline_outputs_sha256 baseline-out',
      'tests_sha256 payload/tests', 'method_payload_sha256 payload/method', 'evaluation_payload_sha256 evaluation-payload',
      'method_source_sha256 method', 'harness_sha256 harness']
    const expectedFiles = Object.fromEntries([
      ...manifest.method_files.map(row => [`payload/method/${row.path}`, row.sha256]),
      ...fs.readdirSync(path.join(A, 'harness')).map(name => [`harness/${name}`, hash(fs.readFileSync(path.join(A, 'harness', name)))]),
      ...helpers.map(name => [`evaluation-payload/${name}`, manifest.input_hashes.evaluators[name]]),
      ['evaluation-payload/manifest.json', hash(Buffer.from(JSON.stringify(manifest)))],
      ['evaluation-payload/predictions.json', seal.sha256],
    ])
    const check = `import hashlib,json,pathlib; expected=json.loads(${JSON.stringify(JSON.stringify(expectedFiles))}); assert all(hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()==h for p,h in expected.items())`
    const result = await command(`evaluate-state-${phase}`, `mkdir -p out\npython3 -I -c ${quote(check)}\nprintf %s ${quote(helper)} | base64 -d | python3 -I - ${keys.join(' ')} > out/evaluate-state.json`, executionTimeout('setup_method'))
    if (result.error || result.rc !== 0) return 'infra'
    const state = read(path.join(result.to, 'out', 'evaluate-state.json'))
    if (!frozenState.evaluation_payload_sha256) frozenState.evaluation_payload_sha256 = state.evaluation_payload_sha256
    if (!frozenState.method_source_sha256) frozenState.method_source_sha256 = state.method_source_sha256
    if (!frozenState.harness_sha256) frozenState.harness_sha256 = state.harness_sha256
    return Object.keys(frozenState).every(key => /^[a-f0-9]{64}$/.test(state[key]) && state[key] === frozenState[key]) ? null : 'other'
  }
  function collect(result) {
    const source = path.join(result.to, 'out', 'eval')
    if (!fs.existsSync(source)) return
    for (const name of fs.readdirSync(source)) {
      const file = path.join(source, name)
      if (!fs.lstatSync(file).isFile()) throw new Error('invalid evaluation artifact')
      fs.copyFileSync(file, path.join(destination, name))
    }
  }
  try {
    fs.mkdirSync(destination, { recursive: true })
    if (fs.existsSync(control)) return finish('VOID', 'other', 2)
    for (const name of ['validity', 'equivalence', 'performance', 'curve']) {
      write(path.join(destination, `${name}.json`), { status: 'VOID', reason_code: 'not_run' })
    }
    seal = verifySeal()
    const protocol = read(path.join(A, 'PREDICTIONS.json'))
    const payload = read(path.join(A, 'implement-payload.json'))
    const tests = read(path.join(C, 'implement', 'tests.json'))
    const baseline = read(path.join(C, 'implement', 'baseline.json'))
    if (payload.remote_directory !== remoteDirectory || payload.seal_sha256 !== seal.sha256
      || tests.seal_sha256 !== seal.sha256 || tests.sha256 !== payload.tests_sha256
      || read(path.join(A, 'REVIEW.json')).pass !== true) return finish('VOID', 'other', 2)
    const method = read(path.join(A, 'proposal.json')).method
    const prediction = protocol.predictions.find(row => row.method === method)
    if (!prediction) return finish('VOID', 'parse', 2)
    const box = read(path.join(C, 'box.json'))
    const gpuCount = Number.isInteger(box.gpu_count) ? box.gpu_count : Number(/^gpu_(\d+)x_/.exec(box.type)?.[1])
    const probe = read(path.join(A, 'results', 'probe', 'probe.json'))
    const available = Math.min(gpuCount, probe.nvidia.gpus.length)
    if (!Number.isInteger(available) || available < 1) return finish('VOID', 'parse', 2)
    frozenState = { ...baseline, tests_sha256: tests.sha256,
      method_payload_sha256: read(path.join(A, 'results', 'implement', 'out', 'implement-state.json')).method_payload_sha256 }
    manifest = { remote_directory: remoteDirectory, protocol, prediction, box, gpu_count: available,
      run_timeout_s: executionTimeout('run_method'), method_files: payload.method_files,
      anchors: read(path.join(A, 'intake', 'anchors.json')),
      input_hashes: { seal_sha256: seal.sha256, ...frozenState,
        anchors_sha256: hash(fs.readFileSync(path.join(A, 'intake', 'anchors.json'))),
        harness_sha256: await treeHash(path.join(A, 'harness')),
        evaluators: Object.fromEntries(helpers.map(name => [name, hash(fs.readFileSync(path.join(__dirname, name)))])) } }
    fs.mkdirSync(control)
    fs.writeFileSync(path.join(control, 'manifest.json'), JSON.stringify(manifest) + '\n', { flag: 'wx', mode: 0o444 })
    const uploads = ['test ! -e evaluation-payload', 'test ! -e evaluation-work', 'mkdir -p evaluation-payload out', 'rm -rf out/eval', 'mkdir -p out/eval']
    for (const [name, bytes] of [...helpers.map(name => [name, fs.readFileSync(path.join(__dirname, name))]),
      ['manifest.json', Buffer.from(JSON.stringify(manifest))], ['predictions.json', fs.readFileSync(path.join(A, 'PREDICTIONS.json'))]]) {
      uploads.push(`: > ${quote('evaluation-payload/' + name)}`)
      const encoded = bytes.toString('base64')
      for (let offset = 0; offset < encoded.length; offset += 24576) {
        uploads.push(`printf %s ${quote(encoded.slice(offset, offset + 24576))} | base64 -d >> ${quote('evaluation-payload/' + name)}`)
      }
    }
    let batch = [], size = 0
    for (const line of uploads) {
      if (size + line.length > 32768) {
        const result = await command('evaluate-upload', batch.join('\n'), executionTimeout('setup_method'))
        if (result.error || result.rc !== 0) return finish('VOID', 'infra', 2)
        batch = []; size = 0
      }
      batch.push(line); size += line.length + 1
    }
    const uploaded = await command('evaluate-upload', batch.join('\n'), executionTimeout('setup_method'))
    if (uploaded.error || uploaded.rc !== 0) return finish('VOID', 'infra', 2)
    for (const stage of ['validity', 'equivalence', 'performance']) {
      let error = await intact(`before-${stage}`)
      if (error) return finish('VOID', error, 2)
      const result = await command(`evaluate-${stage}`, `python3 -B evaluation-payload/eval_${stage}.py --stage ${stage} --in evaluation-payload/manifest.json --out out/eval`, executionTimeout('evaluate'))
      if (result.error) return finish('VOID', result.error, result.error === 'timeout' ? 3 : 2)
      error = await intact(`after-${stage}`)
      if (error) return finish('VOID', error, 2)
      collect(result)
      const verdict = read(path.join(destination, `${stage}.json`))
      if (result.rc === 3) return finish('VOID', 'timeout', 3)
      const passed = verdict[`${stage}_pass`]
      if (JSON.stringify(verdict.input_hashes) !== JSON.stringify(manifest.input_hashes)
        || !['PASS', 'FAIL', 'VOID'].includes(verdict.status)
        || (verdict.status === 'PASS' && (passed !== true
          || (result.rc !== 0 && !(stage === 'performance' && result.rc === 2))))
        || (verdict.status === 'FAIL' && passed !== false)) return finish('VOID', 'parse', 2)
      facts[`${stage}_pass`] = typeof passed === 'boolean' ? passed : null
      if (stage === 'performance') {
        for (const key of ['equal_cost', 'speedup_published', 'speedup_tuned', 'cost_ratio', 'prediction_ratio']) facts[key] = verdict[key] ?? null
        const curve = read(path.join(destination, 'curve.json'))
        facts.curve_points = curve.curve_points === 0 && curve.not_applicable !== true ? null : curve.curve_points ?? null
        if (verdict.status === 'FAIL' && passed === false) return finish('FAIL', 'numeric', 5)
        if (curve.status !== 'PASS' || result.rc !== 0) return finish('VOID', 'parse', 2)
      }
      if (verdict.status === 'VOID') return finish('VOID', 'parse', 2)
      if (!passed) return finish('FAIL', stage === 'validity' ? 'anchor' : 'numeric', stage === 'validity' ? 4 : 5)
    }
    return finish('PASS', 'none', 0)
  } catch {
    return finish('VOID', 'parse', 2)
  }
}
