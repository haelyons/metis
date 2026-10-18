# Result

Picks 1 · PASS 1 · on-goal cards U4 1 · U3 1 · halts: none

## Table

| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [seed·idea·1](#card-seed-idea-1) MD verification inserted into Org-Mol's ester shortlist before synthesis | PASS 2/2 | seed | if_lever | 5 | — → 5 | — → 3 | 5 | — | — → 5 | 5 | $984 at verify_300 · plan $984 · 2 GUESS |

## Frontier (listed, not produced)

None.

## Cards

<a id="card-seed-idea-1"></a>**IC-V3 · MD verification inserted into Org-Mol's ester shortlist before synthesis.** seed pick · compute tested: yes · plan expects: the lever · PASS

**Question.** Does molecular-dynamics verification of viscosity and thermal conductivity reorder a machine-learning ester shortlist, and does the best coolant keep improving?

**What is known.** A 2026 benchmark ran Green-Kubo molecular dynamics on eight organic liquids; viscosity ranking stayed, thermal conductivity did not [s9][s7][s8]. Only eight molecules had viscosity and thermal conductivity Green-Kubo verified against reference values [s9]; the 100-to-1000 shortlist answer is open.

**Hypothesis.** Molecular dynamics reorders the shortlist: machine-learning viscosity error (22.467% MAPE) exceeds molecular-dynamics error, so better esters appear after verification [s3].

**Restructuring.** Each candidate's viscosity waits on one long trajectory; the ranking waits on 100, 300, then 1000 candidates. Split each long trajectory into independent replicas on separate GPUs, block-average the Green-Kubo integrals, and run candidates side by side.

**If compute is the lever.** By 100 candidates the replica ranking matches the sequential baseline, diverges from machine-learning, and the best figure climbs through 1000.

**If not.** Replicas match the sequential ranking only by 300 candidates; then molecular dynamics confirms the machine-learning list from 100 through 1000.

**Test.** Run Green-Kubo molecular dynamics on the top 100 then 300 of 461 monoesters [s1]. Compare MD-vs-ML rank correlation and figure climb. Time single-trajectory against parallel replicas.

*Compute axis.* MD-verified ester candidates: 100–1,000 candidates, 3 levels. Closest prior: 8 [s6], beyond it.

**Check first.** Green-Kubo molecular dynamics reproduces the paper's measured Ester 1 viscosity 6.41 cSt and conductivity 0.141 W/m K. Tolerance: ±40% on viscosity and thermal conductivity (the documented LOPLS-AA error is about a factor of 1.4); parallel replicas within one standard error of the sequential run.

**Would not show.** Shows single-phase ranking under one force field and 15 ns sampling; no synthesis, dielectric, flammability, compatibility, or stability checks. The 1000-candidate run exceeds the budget.

*Cost.* Plans $984.16 of the $1,000 budget over 61.8 machine-hours, leaving $15.84. Main guess: A100 GROMACS throughput [p], measured after $20 of spend; the budget is reached if it is 1.0× lower. 1 cost flag in the block.

**Judges.** Dramaturg: PASS 2/2. Decides at: $984 at verify_300 · plan $984 · 2 GUESS (critic: Decision rule needs MD-versus-ML Spearman and figure climb at 300 candidates, first available after verify_300).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $1,000 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-10-18 · filesystem $0.20/GiB-month [q]
Spend      anchor  Green-Kubo runs of Ester 1 and Ester 2 (5 replicas x 8 ns each) plus one 24 ns sequential trajectory; throughput benchmark  8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h  1.26 h [=]  $20  time box; need 1.26 h (margin 1.00×)
           verify_100  top 100 candidates, 18 ns each, 8 at a time  8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h  20.2 h [=]  $321.38  time box; need 20.2 h (margin 1.00×)
           verify_300  candidates 101-300, same protocol  8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h  40.4 h [=]  $642.75  time box; need 40.4 h (margin 1.00×)
           verify_300  box files, Green-Kubo autocorrelations and logs, about 2 GiB kept about 60 h  [=]  $0.03
           Planned $984.16 · unallocated $15.84 · cap $1,000
Rests on   A100 GROMACS throughput 268 ns/day [p] "A100 | 267.5 | 691.7 | 265.8 | 129.1 | 38.8 | 23.2" · differs: system: R-143a in hexane, 20,248 atoms, versus a ~15,000-atom saturated monoester box, the benchmark writes energy output 333x more often and loses 2.6x; our Green-Kubo runs also write pressure and heat flux at high frequency · measured in anchor ($20 spent by then) · gate A100 GROMACS throughput ≥ 264 in verify_300 (now 268, passes; uncut plan at it $997.20), else throughput too low to afford 300 candidates in budget; stop at top 100 · budget reached at 263 (1.0× lower)
           MD viscosity MAPE on two esters 15 percent [g] rests on: LOPLS-AA reproduces organic-liquid viscosity to about a factor of 1.4 (one standard deviation), so two known esters should land near that · measured in anchor ($20 spent by then) · gate MD viscosity MAPE on two esters ≤ 22.5 in anchor (now 15, passes; uncut plan at it $984.16), else MD is no more accurate than the ML viscosity model; stop · budget not reached within 1000×
           best figure at 300 versus 100 1.08 ratio [g] rests on: the 461 pool spans 1-12 cSt and the ML 22.467% viscosity error hides better candidates that MD uncovers · measured in verify_300 ($984.16 spent by then) · gate best figure at 300 versus 100 ≥ 1.05 in verify_1000 (now 1.08, passes; uncut plan at it $984.16), else the best figure already plateaued at 300; the 1000-candidate run is not justified · budget not reached within 1000×
Scenarios  throughput halves to 150 ns/day → $1,755.05 (over budget) · MD viscosity MAPE equals ML's 22.467% → $984.16
Buys       top-100 tier: 100 [d] · throughput halves to 150 ns/day: 100 · MD viscosity MAPE equals ML's 22.467%: 100
           top-300 tier: 300 [d] · throughput halves to 150 ns/day: 300 · MD viscosity MAPE equals ML's 22.467%: 300
           production ns through 300: 5,400 [=] · throughput halves to 150 ns/day: 5,400 · MD viscosity MAPE equals ML's 22.467%: 5,400
           anchor simulation total: 112 [d] · throughput halves to 150 ns/day: 112 · MD viscosity MAPE equals ML's 22.467%: 112
Flags      thin headroom: the budget is reached if A100 GROMACS throughput is 1.0× lower
Full scale verify candidates 301-1000 (700 more) at 18 ns each: $2,249.63 = 2.25× budget = 7.5× top-300 tier · inputs 1 c, 1 p, 5 d ([p] A100 GROMACS throughput)
           top 1000 at 100 ns per candidate (5x longer sampling): $17,900 = 17.9× budget = 17.9× top-1000 tier · inputs 1 c, 1 p, 1 d ([p] A100 GROMACS throughput)
Outside    computational chemist time: pipeline build, LOPLS-AA parameter assignment, Green-Kubo analysis, result review: 60 person-hours
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
ns_per_candidate = equil_ns + reps * prod_ns_rep = 3 + 3 * 5 = 18 ns
usd_per_candidate = ns_per_candidate / a100_ns_day * 24 * a100_usd_gpu_h = 18 / 267.5 * 24 * 1.99 = 3.21376 USD
usd_anchor = anchor_ns / a100_ns_day * 24 * a100_usd_gpu_h = 112 / 267.5 * 24 * 1.99 = 19.9967 USD
usd_100 = n_100 * usd_per_candidate = 100 * 3.21376 = 321.376 USD
usd_300_extra = (n_300 - n_100) * usd_per_candidate = (300 - 100) * 3.21376 = 642.751 USD
usd_1000_extra = (n_1000 - n_300) * usd_per_candidate = (1000 - 300) * 3.21376 = 2249.63 USD
usd_1000_long = n_1000 * 100 / a100_ns_day * 24 * a100_usd_gpu_h = 1000 * 100 / 267.5 * 24 * 1.99 = 17854.2 USD
ns_simulated_300 = n_300 * ns_per_candidate = 300 * 18 = 5400 ns
l_anchor.hours = anchor_ns / a100_ns_day * 24 / node_gpus = 112 / 267.5 * 24 / 8 = 1.25607 h
l_anchor.need = anchor_ns / a100_ns_day * 24 / node_gpus = 112 / 267.5 * 24 / 8 = 1.25607 h
l_100.hours = n_100 * ns_per_candidate / a100_ns_day * 24 / node_gpus = 100 * 18 / 267.5 * 24 / 8 = 20.1869 h
l_100.need = n_100 * ns_per_candidate / a100_ns_day * 24 / node_gpus = 100 * 18 / 267.5 * 24 / 8 = 20.1869 h
l_300.hours = (n_300 - n_100) * ns_per_candidate / a100_ns_day * 24 / node_gpus = (300 - 100) * 18 / 267.5 * 24 / 8 = 40.3738 h
l_300.need = (n_300 - n_100) * ns_per_candidate / a100_ns_day * 24 / node_gpus = (300 - 100) * 18 / 267.5 * 24 / 8 = 40.3738 h
l_storage.usd = 2 * fs_usd_gib_month / 12 = 2 * 0.2 / 12 = 0.0333333 usd
fs_1000 = usd_1000_extra = 2249.63 = 2249.63 usd
fs_1000_long = usd_1000_long = 17854.2 = 17854.2 usd
```

**Dramaturg, not SUPPORTED.**
none

**Critic.**
- stakes 3 · `card:limits` "Shows single-phase ranking under one force field and 15 ns sampling; no synthesis, dielectric, flammability, compatibility, or stability checks. The 1000-candidate run exceeds the budget." · Choices need synthesis, dielectric, stability; outcomes change them only through unchecked simulation-to-reality and one force field.
- lever 5 · `plan:predictions.noise_rule` "Ten candidates rerun at 3x length with fresh seeds; the molecular-dynamics ranking must be stable (Spearman >= 0.95 between runs), and each candidate's figure carries a block-averaged standard error across replicas." · Noise rules and explicit thresholds separate reorder from confirmation; candidate axis and fixed protocol support the comparison.
- verifiable 5 · `card:anchor` "Green-Kubo molecular dynamics reproduces the paper's measured Ester 1 viscosity 6.41 cSt and conductivity 0.141 W/m K. Tolerance: ±40% on viscosity and thermal conductivity (the documented LOPLS-AA error is about a factor of 1.4); parallel …" · Anchor reproduces published measured ester viscosity and conductivity within stated tolerance; later scores use independent measured values.
- open 5 · `card:closest_prior` "A 2026 benchmark ran Green-Kubo molecular dynamics on eight organic liquids; viscosity ranking stayed, thermal conductivity did not [s9][s7][s8]." · Prior only Green-Kubo verifies eight molecules; plan explicitly states the 100–1000 ester shortlist remains open.
- reshape 5 · `plan:restructuring.condition_phase` "anchor" · Names the serial trajectory-and-tier dependency, runs replicas in parallel, conditions on replica/sequential agreement measured in the anchor phase before main spend.
- baseline 5 · `plan:restructuring.baseline_sequential` "One 24 ns single trajectory per candidate on one A100, GROMACS with -nb gpu -pme gpu -bonded gpu -update gpu -ntmpi 1, timed on the anchor esters." · Tuned GROMACS sequential baseline and replica copies timed on the same GPUs, checked in the anchor phase within one standard error.

**Producer says (not judged).** expected if_lever (The machine-learning viscosity error (22.467% MAPE across a 1-12 cSt range) is large enough that molecular dynamics' closer-to-truth ranking reshuffles the top and the best figure keeps climbing.); compute_tested yes (Verifying more candidates is bought directly with more GPU-hours; candidate count is the varied axis, and wall-clock is compressed by running replicas and candidates side by side on the 8-GPU node.); decides partly; searched yes.

**Annotations.**
- thin headroom: the budget is reached if A100 GROMACS throughput is 1.0× lower
- dramaturg findings failed G-find after a resample; decided as returned

**Root question (null).** generative pipeline for discovery of single phase immersion coolants

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/immersion-coolants/20261018-0342-card/out/work/seed-1/seed/idea/4e6d66bb/producer.md)

## Inventory

| Option | Title | Distance | Cluster | Total | Status | Reason |
|---|---|---|---|---|---|---|

## Log

```
pool: 0 candidate cluster(s); picked 0
seed:idea:seed: thin headroom: the budget is reached if A100 GROMACS throughput is 1.0× lower
seed:idea:seed: dramaturg: degenerate: card:question; degenerate: card:sequential_part; degenerate: card:method; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:limits
seed:idea:seed: dramaturg (resample): degenerate: card:question; degenerate: card:sequential_part; degenerate: card:method; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:limits
seed:idea:seed: dramaturg findings failed G-find after a resample; decided as returned
```