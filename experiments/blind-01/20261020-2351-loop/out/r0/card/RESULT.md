# Result

Picks 1 · PASS 0 · on-goal cards U4 0 · U3 0 · halts: G-plan 1

## Table

| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [seed·idea·1](#card-seed-idea-1) pH-resolved capsid and glycan dynamics from molecular simulation | halted: G-plan | seed | unsure | — | — → — | — → — | — | — | — → — | — | not judged · plan $0 · 0 GUESS |

## Frontier (listed, not produced)

None.

## Cards

<a id="card-seed-idea-1"></a>**endosome-md · pH-resolved capsid and glycan dynamics from molecular simulation.** seed pick · compute tested: yes · plan expects: unsure · halted: G-plan

**Question.** Can all-atom simulation at endosomal pH detect the one-residue difference that flips AAV brain entry and show galactose binding?

**What is known.** Minzoni 2026 ran pH-resolved AAV capsid MD: 500 ns x 2 serotypes x 3 pHs = 3 us aggregate, no glycans, no fate labels [minzoni_2026]. Prior work ran no glycans and no fate-labeled capsids, leaving whether simulation resolves BR1 vs BR1N and galactose binding across pH untested.

**Hypothesis.** pH-resolved trajectories of four capsid trimers separate fate-linked signatures because the three-fold unit holds both the glycan pocket and the fate-flipping site.

**Restructuring.** Each 150 ns trajectory integrates forward step by step; all 28 replicas must finish. Independent replicas run concurrently, two per GPU via CUDA MPS interleaving steps, sixteen lanes on the 8-GPU instance.

**If compute is the lever.** At 28 trajectories the pH 5.5 separation ratio exceeds 3.0; packed GPUs reach it in 56 vs 70 copy-hours, 560 sequential hours.

**If not.** At 28 trajectories the ratio stays below 1.5 or sign-flips across replica halves; packing then buys only more noisy replicas, no earlier conclusion.

**Test.** Simulate VP3 trimers of AAV9, AAV2, BR1 and BR1N at pH 7.4, 5.5 and 4.0, plus AAV9 with galactose, 150 ns x 2 replicas each. Pre-registered loop, contact and exposure descriptors test whether the one-residue BR1/BR1N difference leaves a detectable signature.

*Compute axis.* Independent 150-ns replica trajectories whose aggregate simulation the answer needs: 28–36 trajectories, 2 levels. Closest prior: 6 [minzoni_2026].

**Check first.** Published cryo-EM capsid structures differ by 0.5 A C-alpha RMSD between pH 4.0 and 7.4 Tolerance: Averaged simulated structures must differ by <= 1.0 A over the VP3 core.

**Would not show.** Results are 150-ns descriptor proxies for one capsid pair and a glycan pocket; they cannot establish BBB transport or the 5-fold pore mechanism.

*Cost.* The cost record did not evaluate (5 errors); see the cost block.

**Halted at G-plan.** compute_axis levels [28,36]: need at least 2 levels spanning 2x

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $1,000 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-10-21
Errors     parse at full_scale.fs_full_replicas.usd: unexpected "priced" in "not priced in the plan"
           parse at full_scale.fs_pentamer.usd: unexpected "priced" in "not priced in the plan"
           quote at numbers.ns_day_a100.quote: 180 does not appear in the quote "ApoA1 92,224 atoms = 445.35 ns/day; Cellulose 408,609 atoms = 126.69 ns/day"; a value transformed from the page belongs in a DERIVED number
           quote at numbers.packing_gain.quote: 1.25 does not appear in the quote "ApoA1 on A100, 203.198 ns/day single vs 256.53 ns/day with 2 MPS processes = 1.26x"; a value transformed from the page belongs in a DERIVED number
           quote at numbers.baseline_agg_ns.quote: 3000 does not appear in the quote "500 ns x 2 serotypes x 3 pHs = 3 us aggregate on AAV8/AAV9 5-fold assemblies, no glycans, no fate labels"; a value transformed from the page belongs in a DERIVED number
```

**Derivations.**
```
Derivations: the cost record did not evaluate.
```

**Producer says (not judged).** expected unsure (BR1 and BR1N differ by one residue, so any capsid-intrinsic signature is small and 150-ns replicas may be too short to resolve it.); compute_tested yes (The plan varies the replica count (28, optional 36) and times packed, copies and sequential execution of the same 4200 ns on the 8-GPU instance.); decides no; searched yes.

**Annotations.**
- quote at numbers.ns_day_a100.quote: 180 does not appear in the quote "ApoA1 92,224 atoms = 445.35 ns/day; Cellulose 408,609 atoms = 126.69 ns/day"; a value transformed from the page belongs in a DERIVED number
- quote at numbers.packing_gain.quote: 1.25 does not appear in the quote "ApoA1 on A100, 203.198 ns/day single vs 256.53 ns/day with 2 MPS processes = 1.26x"; a value transformed from the page belongs in a DERIVED number
- quote at numbers.baseline_agg_ns.quote: 3000 does not appear in the quote "500 ns x 2 serotypes x 3 pHs = 3 us aggregate on AAV8/AAV9 5-fold assemblies, no glycans, no fate labels"; a value transformed from the page belongs in a DERIVED number
- rate 1x A100 SXM 40GB 40GB at $1.99/GPU-h is not on the price sheet; kept as a guess
- rate 8x A100 SXM 40GB 40GB at $1.99/GPU-h is not on the price sheet; kept as a guess
- prior_max_level 6 is not in the quote of minzoni_2026

**Root question (null).** Can molecular mapping of AAV capsid-receptor interactions on brain microvascular endothelial cells determine which AAV variants transcytose across the blood-brain barrier versus remain intracellular, and for which capsid-receptor binding signatures?

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/blind-01/20261020-2351-loop/out/r0/card/work/seed-1/seed/idea/fa3e0c93/producer.md)

## Inventory

| Option | Title | Distance | Cluster | Total | Status | Reason |
|---|---|---|---|---|---|---|

## Log

```
pool: 0 candidate cluster(s); picked 0
seed:idea:seed: PRODUCER returned no valid PLAN; extracting from producer.md
seed:idea:seed: quote at numbers.ns_day_a100.quote: 180 does not appear in the quote "ApoA1 92,224 atoms = 445.35 ns/day; Cellulose 408,609 atoms = 126.69 ns/day"; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: quote at numbers.packing_gain.quote: 1.25 does not appear in the quote "ApoA1 on A100, 203.198 ns/day single vs 256.53 ns/day with 2 MPS processes = 1.26x"; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: quote at numbers.baseline_agg_ns.quote: 3000 does not appear in the quote "500 ns x 2 serotypes x 3 pHs = 3 us aggregate on AAV8/AAV9 5-fold assemblies, no glycans, no fate labels"; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: rate 1x A100 SXM 40GB 40GB at $1.99/GPU-h is not on the price sheet; kept as a guess
seed:idea:seed: rate 8x A100 SXM 40GB 40GB at $1.99/GPU-h is not on the price sheet; kept as a guess
seed:idea:seed: prior_max_level 6 is not in the quote of minzoni_2026
seed:idea:seed: halted at G-plan: compute_axis levels [28,36]: need at least 2 levels spanning 2x
```