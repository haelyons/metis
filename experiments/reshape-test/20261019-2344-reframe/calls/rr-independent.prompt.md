You look for the assumption that makes a problem slow, or makes extra compute buy only more of the same. Ask which part
of the work waits on another part, and whether it must. Ask which quantity is measured, and whether a different but
related quantity would be cheaper to compute, easier to split, or more informative. Ask whether the unit of work is the
right one, or whether the work could be cut, merged or reordered. Ask whether the objective is the right one: the single
best answer, a ranking, a distribution, a rare tail, or a yes or no. Ask what is held fixed that need not be. Prefer
changes that alter what more compute buys over changes that only run the same work more times.

Here is a research problem as it was first written down, with the question it belongs to.
Root question: What limits Bayesian calibration of rainfall-runoff models for river catchments, which needs long MCMC chains? Is compute a major blocker at some level, and could that be fixed with a shit ton of GPU parallelism?
Problem:
Bayesian calibration of rainfall-runoff models for river catchments, which needs long MCMC chains.

Find where this problem stops more compute from helping, or where more compute only buys more of the same. Then look for reframings: changes to what is measured, the unit of work, the objective or the order of steps that would let more compute change the answer. Give up to three. End each with one question someone could investigate: specific, answerable by a measurement, and naming what is measured. For each, give the cheapest measurement that would answer it or show it is not worth pursuing, with a rough cost. Decide from the text above and what you know; do not use tools.

Return only one JSON value, with no other text, that matches this JSON Schema:
{"type":"object","required":["reframes"],"properties":{"reframes":{"type":"array","items":{"type":"object","required":["bottleneck","assumption","reframe","question","measure","compute_after","exact","expected","fails_if","closest_prior"],"properties":{"bottleneck":{"type":"string"},"assumption":{"type":"string"},"reframe":{"type":"string"},"question":{"type":"string"},"measure":{"type":"string"},"compute_after":{"type":"string"},"exact":{"type":"string"},"expected":{"type":"string"},"fails_if":{"type":"string"},"closest_prior":{"type":"string"}}}}}}