'use strict'

// These constants drive both the executable seal checks and their prompt examples.
const CONTRACT = Object.freeze({
  pairedKind: 'paired_median', deterministicKind: 'deterministic',
  minimumConfidence: 0.5, maximumConfidence: 1, exampleConfidence: 0.95,
  minimumSeeds: 2, minimumRepetitions: 5,
  metricStringFields: Object.freeze(['name', 'source']),
})
const required = ['equivalence_metrics', 'paired_seed_tests', 'sample_sizes', 'confidence_rule',
  'hardware_cost_basis', 'timing_scope', 'minimum_worthwhile_gain', 'evaluation_inputs', 'splits',
  'compute_budgets', 'repetitions', 'warmup', 'scheduling_order', 'equal_outcome_target', 'baseline_invocation_s']

function projectPerformanceSeconds(predictions, seconds) {
  const { warmup, repetitions, hardware_cost_basis: basis } = predictions
  let projected_s = (warmup + repetitions) * 2 * seconds
  if (predictions.equal_outcome_target.not_applicable !== true) {
    for (const b of predictions.compute_budgets) projected_s += b / basis.baseline_gpus + b / basis.method_gpus
  }
  return projected_s
}

function stochasticFailures(predictions) {
  const paths = []
  const seeds = predictions.paired_seed_tests
  const rule = predictions.confidence_rule?.equivalence
  const metrics = predictions.equivalence_metrics
  if (seeds?.kind !== CONTRACT.pairedKind) paths.push('paired_seed_tests.kind')
  if (!Array.isArray(seeds?.seeds) || seeds.seeds.length < CONTRACT.minimumSeeds
    || !seeds.seeds.every(Number.isInteger) || new Set(seeds.seeds).size !== seeds.seeds.length)
    paths.push('paired_seed_tests.seeds')
  if (rule?.kind !== CONTRACT.pairedKind) paths.push('confidence_rule.equivalence.kind')
  if (!Number.isFinite(rule?.confidence) || rule.confidence < CONTRACT.minimumConfidence
    || rule.confidence >= CONTRACT.maximumConfidence) paths.push('confidence_rule.equivalence.confidence')
  if (!Array.isArray(metrics) || !metrics.length) paths.push('equivalence_metrics')
  else metrics.forEach((metric, index) => {
    const prefix = `equivalence_metrics[${index}]`
    for (const field of CONTRACT.metricStringFields) {
      if (typeof metric?.[field] !== 'string' || !metric[field].trim()) paths.push(`${prefix}.${field}`)
    }
    const tolerance = typeof metric?.tolerance === 'number' ? metric.tolerance : metric?.tolerance?.abs
    if (!Number.isFinite(tolerance) || tolerance <= 0
      || (typeof metric.tolerance !== 'number' && Object.keys(metric.tolerance).length !== 1))
      paths.push(`${prefix}.tolerance`)
  })
  return paths
}

function skeleton(stochastic) {
  const confidence = CONTRACT.exampleConfidence
  // Finite exact median interval for one metric (Bonferroni needs more seeds for multiple metrics).
  const count = Math.max(CONTRACT.minimumSeeds, Math.ceil(Math.log2(2 / (1 - confidence))))
  const seeds = Array.from({ length: count }, (_, index) => index)
  const metric = Object.fromEntries(CONTRACT.metricStringFields.map(field => [field,
    field === 'name' ? 'outcome_metric' : 'REPLACE with scientific requirement citation or baseline variability evidence']))
  metric.tolerance = { abs: stochastic ? 0.001 : 0 }
  return {
    outputs_stochastic: stochastic,
    evaluation_inputs: { ids: ['held-out-1'] },
    equivalence_metrics: [metric],
    paired_seed_tests: stochastic ? { kind: CONTRACT.pairedKind, seeds }
      : { kind: CONTRACT.deterministicKind, justification: 'REPLACE with scientific reason outputs are deterministic' },
    sample_sizes: { inputs: 1, seeds: stochastic ? seeds.length : 1 },
    confidence_rule: Object.fromEntries(['performance', 'equivalence'].map(key =>
      [key, { kind: CONTRACT.pairedKind, confidence }])),
    repetitions: CONTRACT.minimumRepetitions,
    baseline_invocation_s: { seconds: 1, source: 'REPLACE with measured file, measured value and arithmetic for one complete baseline equivalence invocation' },
  }
}

function validate(predictions, bounds, menu, evaluate_budget_s) {
  let check = 'predictions_invalid'
  const hasValue = value => value != null && (typeof value !== 'string' || value.trim() !== '')
    && (typeof value !== 'object' || Object.keys(value).length > 0)
  const paths = {
    predictions_invalid: ['predictions'],
    protocol_cost: ['warmup', 'repetitions', 'paired_seed_tests.seeds', 'evaluation_inputs.ids',
      'compute_budgets', 'baseline_invocation_s'],
    bounds_coverage_invalid: ['predictions[].method', 'infeasible_methods'],
    interval_bounds_invalid: ['predictions[].expected_speedup_interval'],
    intervals_identical: ['predictions[].expected_speedup_interval'],
  }
  const reject = (code, fieldPaths = paths[code]) => ({ reason_codes: [code], field_paths: fieldPaths })
  if (!predictions || !Array.isArray(predictions.predictions)) return reject('predictions_invalid')
  const predictionCount = predictions.predictions.length
  check = 'protocol_incomplete'
  const incomplete = required.filter(key => !hasValue(predictions[key]))
  const invocation = predictions.baseline_invocation_s
  if (!invocation || typeof invocation !== 'object' || Array.isArray(invocation)
    || !Number.isFinite(invocation.seconds) || invocation.seconds <= 0
    || typeof invocation.source !== 'string' || !invocation.source.trim()) incomplete.push('baseline_invocation_s')
  if (typeof predictions.outputs_stochastic !== 'boolean') incomplete.push('outputs_stochastic')
  if (!Array.isArray(predictions.compute_budgets) || new Set(predictions.compute_budgets).size < 3
    || !predictions.compute_budgets.every(value => Number.isFinite(value) && value > 0)) incomplete.push('compute_budgets')
  if (!Number.isInteger(predictions.repetitions) || predictions.repetitions < CONTRACT.minimumRepetitions)
    incomplete.push('repetitions')
  if (!Number.isFinite(predictions.minimum_worthwhile_gain) || predictions.minimum_worthwhile_gain <= 1)
    incomplete.push('minimum_worthwhile_gain')
  if (new Set(predictions.predictions.map(item => item?.method)).size !== predictionCount)
    incomplete.push('predictions[].method')
  predictions.predictions.forEach((item, index) => {
    if (!item || !menu.includes(item.method)) incomplete.push(`predictions[${index}].method`)
    const interval = item?.expected_speedup_interval
    if (!Number.isFinite(interval?.low) || interval.low <= 0 || !Number.isFinite(interval?.high)
      || interval.high < interval.low) incomplete.push(`predictions[${index}].expected_speedup_interval`)
  })
  if (incomplete.length) return reject(check, [...new Set(incomplete)])
  check = 'compute_points_incomplete'
  const missingPoints = []
  predictions.predictions.forEach((item, index) => {
    if (!Array.isArray(item.outcome_vs_compute_points)
      || !predictions.compute_budgets.every(budget => item.outcome_vs_compute_points.some(point => point
        && point.compute_budget === budget && hasValue(point.predicted_outcome) && hasValue(point.uncertainty))))
      missingPoints.push(`predictions[${index}].outcome_vs_compute_points`)
  })
  if (missingPoints.length) return reject(check, missingPoints)
  if (predictions.outputs_stochastic) {
    check = 'stochastic_equivalence_invalid'
    const paths = stochasticFailures(predictions)
    if (paths.length) return reject(check, paths)
  }
  const feasible = menu.filter(method => bounds[method].feasible)
  check = 'protocol_cost'
  if (feasible.length && projectPerformanceSeconds(predictions, invocation.seconds) > 0.9 * evaluate_budget_s)
    return reject(check)
  check = 'bounds_coverage_invalid'
  const infeasible = menu.filter(method => !bounds[method].feasible)
  const excluded = predictions.infeasible_methods
  const validCoverage = predictionCount === feasible.length
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

  return null
}

module.exports = { validate, skeleton, projectPerformanceSeconds }
