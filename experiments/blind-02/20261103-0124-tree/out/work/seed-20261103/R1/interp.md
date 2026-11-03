# Interpretability routes

Partial fit. Goodfire extracts SAE features from neural activations; its Evo 2 report describes biological feature alignment and preliminary steering, not docking replication or numerical certification. MEGADOCK instead exposes an explicit grid-correlation score. Inference: inspect that computation directly; introduce neural interpretability only as separate research branch. [Goodfire](https://www.goodfire.com/research/interpreting-evo-2), [MEGADOCK equations](https://www.bi.cs.titech.ac.jp/megadock/perform.html).

Root task separates complete-workflow acceleration, same-settings CPU/GPU agreement, and dense-search quality under sealed budgets; it prohibits scoring changes and reranking inside proposed replication. Recommendations below are diagnostic proposals, not executed results or replacements for those gates. [Root plan](file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md).

## I1 — Exact score attribution and controlled ablation

MEGADOCK combines shape, electrostatics and desolvation through packed complex grids; command guide exposes scoring variants and electrostatic/hydrophobic weights. Proposal: instrument pinned implementation, reconstruct contributions at each frozen retained transform, verify their sum against original score, then compare contributions for rank1 and best50 winners. Respect packed-grid algebra; do not assume three independent off-the-shelf energy outputs. [Equations](https://www.bi.cs.titech.ac.jp/megadock/perform.html), [command guide](https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md).

Proposed causal test: at fixed transforms, remove one contribution at a time and measure score/rank changes; distinguish this from rerunning search, where candidate support changes too. Keep counterfactual ranks diagnostic only. Inference: this can separate candidate recovery from scoring preference, but cannot establish biological correctness or authorize new ranking within frozen arms. Native-derived evaluation remains evaluation-only under root protocol. [Root plan](file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md).

Root link: addresses why denser search might improve best50 while worsening rank1, alongside root's existing quality comparison. [Root plan](file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md).

Compute open: none. Proposed audit exhausts frozen retained poses; more poses would change diagnostic scope, not resolve missing acceptance criteria.

Sequential: proposed analysis needs one baseline plus three fixed-transform ablations per case/arm, independently across four cases and three arms; after frozen outputs, each pose's contribution calculation and comparison are independent, with CPU implementation requiring zero GPU capacity. If full search is repeated, rotate/voxelize → forward FFT → multiply → inverse FFT → select creates roughly five dependent stages per rotation, repeated 3,600 or 54,000 times; rotations can run concurrently, already supported through OpenMP, while GPU fraction for this instrumented audit remains unmeasured. [Command guide](https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md), [correlation equation](https://www.bi.cs.titech.ac.jp/megadock/perform.html).

Narrowing: score contributions stand in for algorithmic preference; leave timing, tolerance justification and generalization beyond exposed cases to original protocol.

## I2 — Differential tracing of CPU/GPU numerical disagreement

Floating-point reassociation and fused multiply-add can change results despite IEEE 754 compliance. Proposal: compare matched CPU/GPU checkpoints at voxel grids, forward transforms, products, inverse transforms, peak selection and serialization; locate earliest divergent stage, then test synthetic fixtures with independently computed reference values. [NVIDIA numerical guide](https://docs.nvidia.com/cuda/floating-point/index.html), [MEGADOCK correlation equation](https://www.bi.cs.titech.ac.jp/megadock/perform.html).

Proposed diagnosis: distinguish score rounding from changed selected transforms and reconstructed coordinates. Root requires separately justified score/pose/evaluator criteria and rejects deriving tolerance from observed disagreement; tracing supplies error evidence, not automatic scientific acceptance. Keep instrumentation outside timing samples. [Root plan](file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md).

Root link: directly supports same-settings agreement gate; cannot establish speedup or dense-search quality. [Root plan](file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md).

Compute open: none. Extra replicas cannot choose scientifically meaningful tolerances; fixture design and numerical analysis remain required.

Sequential: proposed minimum is eight instrumented executions, CPU/GPU pair for each case, each with about six ordered checkpoints depending on preceding arrays; proposed single-GPU backend reserves one device during acquisition, but busy fraction is unknown, and stored-trace comparisons require zero GPU. Different rotations/cases can run concurrently if memory, transfer and host capacity suffice, while within-rotation data dependencies remain; nearest demonstrated implementation distributes rotations and docking jobs, rather than removing FFT dependencies. [MEGADOCK implementation/performance](https://www.bi.cs.titech.ac.jp/megadock/perform.html).

Narrowing: first divergent intermediate stands in for implementation cause; this does not prove an acceptable error bound.

## I3 — Protein-language-model SAE hypothesis audit

Closest Goodfire-style route: use pretrained protein-model SAEs to propose residue-level biological hypotheses, then intervene on feature activations to check effects on model predictions. Goodfire reports Evo 2 analysis focused on layer 26 and describes steering as preliminary; protein-specific precedent InterPLM demonstrates localized feature interventions and glycine-pattern prediction changes. Neither cited experiment tests this four-case MEGADOCK replication. [Goodfire](https://www.goodfire.com/research/interpreting-evo-2), [InterPLM v1, sections 3.7 and 5.5](https://arxiv.org/html/2412.12101v1).

Proposal: apply released ESM-2-8M dictionaries to sequences extracted from prepared monomers; map selected activations onto structures, test feature interventions with reconstruction-only and matched random-feature controls. Treat interface overlap as hypothesis, not proof of binding mechanism. Any later use for ranking requires separately authorized study; current protocol excludes reranking. [InterPLM methodology](https://arxiv.org/html/2412.12101v1), [root constraint](file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md).

Root link: bears only on biological hypotheses behind pose preference; does not directly answer original acceleration, agreement or same-budget quality estimands. [Root plan](file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md).

Compute open: features/layers analysed could increase; cited InterPLM v1 studies six ESM-2-8M layers with 10,420 dictionary features each, but above that scope neither docking benefit nor stability of proposed interface hypotheses is established. [InterPLM v1, section 3.1](https://arxiv.org/html/2412.12101v1).

Sequential: proposed frozen-checkpoint audit uses six dependent transformer layers per baseline, then SAE encode/intervene/decode and remaining downstream layers per intervention, at most roughly fourteen stages per uncached intervention; for F prespecified features per input, plan eight monomer-input slots × (baseline + reconstruction control + F interventions + F random controls), with no SAE retraining and unknown fraction of one GPU busy per run. Layers remain ordered, but interventions can fork from cached activations and batch across features/inputs if device memory and batch throughput amortize overhead; nearest causal precedent is InterPLM's localized feature steering, which does not report this branching optimization or its GPU occupancy. [InterPLM v1, sections 3.1, 3.7 and 5.5](https://arxiv.org/html/2412.12101v1).

Narrowing: neural feature effects stand in for learned biological representations, not mechanisms of MEGADOCK; useful only for generating independently testable follow-up hypotheses.
