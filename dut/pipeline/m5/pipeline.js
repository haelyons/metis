// wf.js script. Stages are placeholders; PASS does not assert scientific success yet.
const meta = { name: 'm5', description: 'Explicit-run-root scientific pipeline skeleton' }

return (async () => {
  const { default: path } = await import('node:path')
  const { mkdirSync } = await import('node:fs')
  const { execFile } = await import('node:child_process')
  const { promisify } = await import('node:util')
  const exec = promisify(execFile)
  const input = (typeof args === 'string' ? JSON.parse(args) : args) || {}
  if (!input.run_root || !input.tag) throw new Error('m5 needs run_root and tag')
  const root = path.resolve(input.run_root)
  const A = path.join(root, 'agent'), S = path.join(root, 'operator'), C = path.join(root, 'control')
  for (const dir of [A, S, C]) mkdirSync(dir, { recursive: true })

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

  function intake() { return stub('intake') }
  function reproduce() { return stub('reproduce') }
  function profile() { return stub('profile') }
  function seal() { return stub('seal') }
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
