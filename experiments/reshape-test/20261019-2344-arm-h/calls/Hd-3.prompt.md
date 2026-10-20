A weekend hackathon on scientific parallelism, about 30 hours, on 21 November. GPUs are provided; their type is not yet
known. Teams may bring their own problem, and the thinking, data and baseline can be prepared beforehand.

Judges score reshaping, a credible baseline, correctness and scientific value. A carefully explained failure to get a
speedup can still win, if its failure modes were predicted in advance.

The sponsors build systems that split workloads into subtasks and route each to the best chip, and low-latency
inference chips. The question they care about: which parts of a workload are sequential, and must they be?

Propose five projects for this hackathon in this domain: Bayesian calibration of rainfall-runoff models for river catchments, which needs long MCMC chains.. For each give: title; field; sequential_part, the part of the work that one answer waits on step after step, or "none"; restructure, how your project changes that (or what it runs in parallel); condition, what must hold for it to pay off; baselines, what the result is timed and checked against; first_test, the cheapest measurement to run first and its rough cost. Decide from what you know; do not use tools.

Return only one JSON value, with no other text, that matches this JSON Schema:
{"type":"object","required":["proposals"],"properties":{"proposals":{"type":"array","items":{"type":"object","required":["title","field","sequential_part","restructure","condition","baselines","first_test"],"properties":{"title":{"type":"string"},"field":{"type":"string"},"sequential_part":{"type":"string"},"restructure":{"type":"string"},"condition":{"type":"string"},"baselines":{"type":"string"},"first_test":{"type":"string"}}}}}}