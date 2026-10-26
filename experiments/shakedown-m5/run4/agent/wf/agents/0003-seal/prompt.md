Seal a prospective scientific evaluation protocol in one narrow pass.
Read "/home/hal/dev/interp/metis/experiments/shakedown-m5/run4/agent/intake"/*, "/home/hal/dev/interp/metis/experiments/shakedown-m5/run4/agent/profile-packet.json", and "/home/hal/dev/interp/metis/experiments/shakedown-m5/run4/agent/bounds.json" only.
Never read experiments/, operator/, or control/. Do not search, build, run workloads, or write method code.
Write only "/home/hal/dev/interp/metis/experiments/shakedown-m5/run4/agent/PREDICTIONS.json". Use intake evidence and the profile when present. Do not invent measurements; label assumptions and unavailable evidence explicitly.
The method menu is exactly ["data-parallel over inputs","batching","multi-GPU","ensembles","pipelining"]. Deterministic bounds (p is the actionable timed fraction; k is the maximum factor): {"data-parallel over inputs":{"p":0.9631075222251976,"k":8,"bound":6.358050374956024,"feasible":true},"batching":{"p":0.00009258799823128444,"k":4,"bound":1.0000694458210606,"feasible":false},"multi-GPU":{"p":0.9631075222251976,"k":1,"bound":1,"feasible":false},"ensembles":{"p":0.9631075222251976,"k":8,"bound":6.358050374956024,"feasible":true},"pipelining":{"p":0.00009258799823128444,"k":2,"bound":1.0000462961423493,"feasible":false}}.
Include every feasible entry once; list every entry with bound <1.05 exactly once as {method, reason} in infeasible_methods, never in predictions. With no feasible entry, write predictions=[] as a negative result.
For each interval require finite low >0, low <= high <= its method's bound, and high-low <= bound-1. When at least two methods are feasible, their intervals must not all be identical. Base each interval on its method's profile evidence and overheads.
Amdahl bound is 1/((1-p)+p/k). The supplied bounds are ceilings, not measured gains; intervals without measurements are prospective assumptions. Include launch/transfer/merge overhead.
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
Return a short completion acknowledgement; the script reads and seals the file itself.