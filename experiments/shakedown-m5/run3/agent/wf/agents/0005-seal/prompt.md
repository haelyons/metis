Seal a prospective scientific evaluation protocol in one narrow pass.
Read "/home/hal/dev/interp/metis/experiments/shakedown-m5/run3/agent/intake"/* only, plus "/home/hal/dev/interp/metis/experiments/shakedown-m5/run3/agent/profile-packet.json".
Never read experiments/, operator/, or control/. Do not search, build, run workloads, or write method code.
Write only "/home/hal/dev/interp/metis/experiments/shakedown-m5/run3/agent/PREDICTIONS.json". Use intake evidence and the profile when present. Do not invent measurements; label assumptions and unavailable evidence explicitly.
The method menu is exactly ["data-parallel over inputs","batching","multi-GPU","ensembles","pipelining"]. Include every feasible entry once; exclude infeasible entries with reasons in infeasible_methods. With no feasible entry, write predictions=[] as a negative result.
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
Return a short completion acknowledgement; the script reads and seals the file itself.