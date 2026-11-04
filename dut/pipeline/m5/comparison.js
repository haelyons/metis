'use strict'
// Evaluate, comparison mode (U57): separated users, versions, interleaved invocations, compute (G6), then the U58 scorer.
const fs = require('node:fs')
const path = require('node:path')
const { randomUUID } = require('node:crypto')
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const plain = value => value !== null && typeof value === 'object' && !Array.isArray(value)
const sum = values => values.reduce((total, value) => total + (Number.isFinite(value) ? value : 0), 0)
function writeAtomic(file, value) {
  const temporary = `${file}.${randomUUID()}.tmp`
  fs.writeFileSync(temporary, JSON.stringify(value, null, 2) + '\n')
  fs.renameSync(temporary, file)
}

module.exports = async function comparison(context) {
  const { A, C, exec, boxCommand, quote, failure, nullFacts, design, runStarted, ceiling_s, price, allocation } = context
  const started = Date.now()
  const facts = nullFacts('evaluate')
  const results = path.join(A, 'results', 'evaluate', 'comparison')
  const staging = path.join(A, 'results', 'evaluate', 'comparison-box')
  const budgetLeft = () => design.budget_s - (Date.now() - started) / 1000
  const ceilingLeft = () => ceiling_s - (Date.now() - runStarted) / 1000
  const left = () => Math.floor(Math.min(budgetLeft(), ceilingLeft()))
  const evaluator = design.evaluator !== null
  const encode = value => Buffer.from(typeof value === 'string' ? value : JSON.stringify(value)).toString('base64')
  fs.rmSync(results, { recursive: true, force: true })
  fs.rmSync(staging, { recursive: true, force: true })
  fs.mkdirSync(results, { recursive: true })

  // The trusted scripts are written inline, as the profile stage writes its probe; cmp_users.sh gets whether the design
  // has an evaluator and the SHA-256 of each sealed harness file, which it checks on the box.
  let sealed
  try {
    sealed = Object.entries(read(path.join(C, 'arms_seal.json')).files).flat()
  } catch { return failure(facts, 'infra') }
  const users = fs.readFileSync(path.join(__dirname, 'cmp_users.sh'), 'utf8')
    .replace(/^EVALUATOR=0$/m, `EVALUATOR=${evaluator ? 1 : 0}`)
    .replace(/^SEALED=\(\)$/m, () => `SEALED=(${sealed.map(quote).join(' ')})`)
  const uploads = ['set -e', 'mkdir -p profiler']
  for (const [name, text] of [['cmp_users.sh', users], ...['cmp_system.py', 'cmp_wrap.py'].map(name =>
    [name, fs.readFileSync(path.join(__dirname, name), 'utf8')])]) {
    uploads.push(`printf %s ${quote(encode(text))} | base64 -d > ${quote(`profiler/${name}`)}`)
  }
  const uploaded = await boxCommand('upload', uploads.join('\n'), staging, left())
  if (uploaded.error || uploaded.rc !== 0) return failure(facts, uploaded.error || 'infra')
  // Separated users for every comparison.
  const separated = await boxCommand('comparison-users', seconds => `bash profiler/cmp_users.sh ${seconds}`, staging, left())
  if (separated.error || separated.rc !== 0) return failure(facts, 'infra')
  const versions = await boxCommand('versions', `mkdir -p out/comparison
bash harness/versions.sh > out/comparison/versions.json
python3 profiler/cmp_system.py`, staging, left())
  const fetched = name => {
    try {
      const value = read(path.join(staging, 'out', 'comparison', name))
      return versions.error || !plain(value) ? null : value
    } catch { return null }
  }
  const system = fetched('system.json'), armVersions = fetched('versions.json')
  for (const [name, value] of [['system.json', system], ['versions.json', armVersions]]) {
    if (value !== null) writeAtomic(path.join(results, name), value)
  }

  // Rounds: warmups, then replicates; one random.Random(order_seed) stream shuffles each round's (arm, input) pairs.
  const { stdout } = await exec('python3', ['-I', '-c', `import json, random, sys
design = json.load(open(sys.argv[1]))["design"]
pairs = [[arm["id"], item["id"]] for arm in design["arms"] for item in design["inputs"]]
stream, rounds = random.Random(design["order_seed"]), []
for _ in range(design["warmup"] + design["replicates"]):
    order = list(pairs)
    stream.shuffle(order)
    rounds.append(order)
print(json.dumps(rounds))`, path.join(C, 'comparison.json')])
  const schedule = JSON.parse(stdout).flatMap((order, index) => order.map(([arm, input]) => ({
    arm, input, mode: index < design.warmup ? 'warmup' : 'replicate',
    round: index < design.warmup ? index + 1 : index - design.warmup + 1 })))
  const armTimeout = (arm, input) => {
    const value = design.timeout_s
    return value === null ? Infinity : Number.isInteger(value) ? value
      : Number.isInteger(value[arm]) ? value[arm] : value[arm][input]
  }
  const wrapKeys = ['status', 'adapter_rc', 'adapter_wall_s', 'commands', 'gpu_busy_s', 'gpu_busy_known',
    'eval_status', 'eval_rc', 'eval_wall_s', 'eval_gpu_busy_s', 'eval_gpu_busy_known']
  // Keys and types; status ok exactly when every exit status is 0 and every command has a row; eval_status ok only
  // when eval_rc is 0.
  const exact = (value, keys) => plain(value) && Object.keys(value).length === keys.length
    && keys.every(key => Object.hasOwn(value, key))
  const seconds = (item, nullable = false) => (nullable && item === null) || (Number.isFinite(item) && item >= 0)
  const rc = item => item === null || Number.isInteger(item)
  const nullableText = item => item === null || typeof item === 'string'
  const validWrap = (value, count) => exact(value, wrapKeys) && Array.isArray(value.commands)
    && ['ok', 'failed', 'timeout', 'invalid'].includes(value.status)
    && ['ok', 'failed', 'timeout', 'skipped'].includes(value.eval_status)
    && rc(value.adapter_rc) && seconds(value.adapter_wall_s) && seconds(value.gpu_busy_s)
    && typeof value.gpu_busy_known === 'boolean' && rc(value.eval_rc) && seconds(value.eval_wall_s, true)
    && seconds(value.eval_gpu_busy_s, true) && typeof value.eval_gpu_busy_known === 'boolean'
    && value.commands.every(row => exact(row, ['argv', 'rc', 'wall_s', 'executable', 'sha256'])
      && Array.isArray(row.argv) && row.argv.every(part => typeof part === 'string') && rc(row.rc) && seconds(row.wall_s)
      && nullableText(row.executable) && nullableText(row.sha256))
    && (value.status === 'ok') === (value.adapter_rc === 0 && value.commands.length === count
      && value.commands.every(row => row.rc === 0))
    && (value.eval_status !== 'ok' || value.eval_rc === 0)
  const invocations = []
  for (const [index, job] of schedule.entries()) {
    const token = `i${index + 1}`
    if (budgetLeft() < 1) {
      invocations.push({ job, wrap: null, status: 'not_run' })
      continue
    }
    const bound = Math.min(budgetLeft(), ceilingLeft())
    const record = { arm: job.arm, input: job.input, mode: job.mode, round: job.round,
      arm_timeout_s: Math.max(0, Math.floor(Math.min(armTimeout(job.arm, job.input), bound))),
      eval_timeout_s: evaluator ? Math.max(0, Math.floor(Math.min(design.evaluator.timeout_s ?? Infinity, bound))) : null,
      left_s: Math.max(0, Math.floor(bound)) }
    const arm = design.arms.find(item => item.id === job.arm)
    const plan = { commands: arm.commands, env: arm.env, spec: design.inputs.find(item => item.id === job.input).spec,
      evaluator, budget_left_s: Math.max(0, Math.floor(budgetLeft())) }
    const written = await boxCommand('comparison-job', `set -e
mkdir -p comparison-jobs comparison-work
chmod 700 comparison-jobs
chmod 711 comparison-work
umask 077
printf %s ${quote(encode(record))} | base64 -d > comparison-jobs/${token}.json
printf %s ${quote(encode(plan))} | base64 -d > comparison-jobs/${token}.run.json
chmod 600 comparison-jobs/${token}.json comparison-jobs/${token}.run.json`, staging, Math.max(1, Math.floor(ceilingLeft())))
    const target = path.join(results, `${job.mode === 'warmup' ? 'w' : 'r'}${job.round}`, job.arm, job.input)
    fs.mkdirSync(target, { recursive: true })
    let wrap = null
    if (!written.error && written.rc === 0) {
      // Only regular files and directories of the invocation are fetched.
      const ran = await boxCommand('comparison', `python3 profiler/cmp_wrap.py ${token}
rm -rf out/cmp-fetch
mkdir -m 700 out/cmp-fetch
for name in out log eval wrap.json; do
  if [ -e comparison-work/${token}/$name ]; then cp -a comparison-work/${token}/$name out/cmp-fetch/ 2>/dev/null || true; fi
done
find out/cmp-fetch -mindepth 1 ! -type f ! -type d -delete
exit 0`, staging, Math.max(1, Math.floor(ceilingLeft())), true)
      const source = path.join(staging, 'out', 'cmp-fetch')
      if (!ran.error && fs.existsSync(source)) fs.cpSync(source, target, { recursive: true })
      try {
        const value = read(path.join(target, 'wrap.json'))
        if (validWrap(value, arm.commands.length)) wrap = value
      } catch { /* A missing or invalid wrap.json gives status invalid. */ }
    }
    invocations.push({ job, wrap, status: wrap ? wrap.status : 'invalid' })
  }
  if (evaluator) {
    // Its outcome is recorded in the stage's receipts and changes no value or outcome.
    await boxCommand('comparison-private-remove', 'sudo -n rm -rf cmp-private', staging, Math.max(1, Math.floor(ceilingLeft())))
  }

  // Compute (G6): attribution per invocation, and the bill of the whole box allocation; never mixed.
  const rows = invocations.map(({ job, wrap, status }) => {
    const wall = wrap ? sum([wrap.adapter_wall_s, ...wrap.commands.map(row => row.wall_s)]) : null
    return { round: job.round, arm: job.arm, input: job.input, status, wall_s: wall,
      gpu_busy_s: wrap ? wrap.gpu_busy_s : null, gpu_busy_known: wrap ? wrap.gpu_busy_known === true : false,
      eval_status: wrap ? wrap.eval_status : null, eval_wall_s: wrap ? wrap.eval_wall_s : null,
      eval_gpu_busy_s: wrap ? wrap.eval_gpu_busy_s : null,
      attributed_usd: status === 'not_run' || price === null ? null : sum([wall, wrap?.eval_wall_s]) / 3600 * price, mode: job.mode }
  })
  const compute = {
    invocations: rows.map(({ mode, ...row }) => row),
    arms: design.arms.map(({ id }) => {
      const own = rows.filter(row => row.arm === id && row.mode === 'replicate')
      return { arm: id, invocations: own.length, wall_s: sum(own.map(row => row.wall_s)),
        gpu_busy_s: sum(own.map(row => row.gpu_busy_s)), gpu_busy_known: own.every(row => row.gpu_busy_known),
        eval_wall_s: sum(own.map(row => row.eval_wall_s)), eval_gpu_busy_s: sum(own.map(row => row.eval_gpu_busy_s)),
        attributed_usd: sum(own.map(row => row.attributed_usd)) }
    }),
    all_invocations: { invocations: rows.length, wall_s: sum(rows.map(row => row.wall_s)),
      eval_wall_s: sum(rows.map(row => row.eval_wall_s)), attributed_usd: sum(rows.map(row => row.attributed_usd)) },
    system, versions: armVersions, allocation: allocation(),
  }
  writeAtomic(path.join(A, 'results', 'evaluate', 'comparison_compute.json'), compute)

  try {
    await exec('python3', ['-I', 'm5/score_comparison.py', C, results, path.join(A, 'harness'), path.join(C, 'comparison_scored.json')])
  } catch { return failure(facts, 'parse') }
  return { status: 'PASS', facts }
}
