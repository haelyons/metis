# reshape-test

The asker's question: can language models find restructures of sequential work that benefit from parallel computing
hardware, aimed at the SoTA Scientific Parallelism Hackathon (21 November)?

The narrower question tested here: does our question-tree pipeline find such restructures, and if not, where does it
lose them? Run F's critic already scores the hackathon's criteria (reshape, baseline, verifiable, stakes); reshape was
1 on 15 of its 19 judged cards. But none of run F's roots named a problem with a long sequential chain, so the low
score may come from the roots rather than the pipeline. This experiment separates the two.

A restructure, for every arm and the judge: it removes a step-after-step dependency that one answer waits on (time
steps, chain iterations, solver iterations), so those steps are computed at the same time. Running independent copies
side by side, or splitting each single step across GPUs, does not count.

## Arms

All on one domain, chosen from the good fits in the asker's harry.md: Bayesian calibration of rainfall-runoff models,
which waits on a time-stepped model inside a long MCMC chain.

| Arm | Designer | Input |
|---|---|---|
| P | question-tree pipeline, run F's args, one pick per branch | planted root: names the known restructure (guess the whole trajectory, correct every step at once with Newton iterations) |
| O | same | open root: the domain only, no method |
| R | reframe stage, both lenses (harry, independent), Kimi K3 | the open root as the case |
| Hd | one bare model (DeepSeek V4 Pro, no tools), 3 samples | the hackathon brief (`brief.md`) and the domain |
| Ho | same | the hackathon brief only, any field |

The hackathon brief goes only to Hd and Ho; the pipeline arms never see it (the director's goal stays hidden from them,
as in every run). `brief.md` is harry.md's account of the rubric and sponsors, without harry's own pick or method.

Roots (the asker's voice, as EX1 and EX2):
- P: `seeds/P.json`
- O: `seeds/O.json`

## Measures

- Pipeline arms, from the returned records: framer verdict; per option, the `sequential` status and the option
  critic's reshape score; which options were picked; per card, `restructuring.method` (none or not), the critic's
  reshape score and the verdict.
- Every arm: a judge (GLM 5.3, via `reframe/reframe.js --judge-only`) marks each option or proposal against the
  restructure criterion above. A planted list (`planted.json`, key in `planted-key.json`, not shown to the judge)
  checks the judge: two restructures, two non-restructures.

## Predictions (written before any run)

- P: framer says NOT COMPUTE-BOUND (0.6). At least one physical option meets the criterion (0.9). The physical pick
  meets it (0.7). The physical card's method is not none (0.6) and its critic reshape is 4 or 5 (0.5).
- O: at least one physical option meets the criterion (0.35). The physical pick meets it (0.2). A card with reshape 4
  or 5 (0.15).
- R: the harry lens proposes at least one restructure (0.7); the independent lens (0.3).
- Hd: at least one of five proposals meets the criterion in at least two of three samples (0.8).
- Ho: the same (0.9); a parallel-in-time method (Parareal, DEER or parallel Newton, parallel scan, waveform
  relaxation) is named in at least two of three samples (0.6).
- Planted: the judge labels all four as keyed (0.9).

## What the outcomes tell

- O carries no restructure to a card, P does, and Hd finds one: the loss is in generation (root, framer, branch
  prompts), not in the critic. A bare model told the objective does better on the same domain. This is the
  hypothesis.
- O carries a restructure to a card with reshape 4 or 5: the hypothesis is wrong. The pipeline finds restructures
  when the domain has a chain; run F's low reshape came from its roots.
- P fails too (no card with a method): the loss is downstream, in the producer's compute lever or the critic.
- Hd and Ho fail as well: on this evidence, these models do not find restructures without being told one.

One run per pipeline arm: cheap-model verdicts have flipped between reruns before (immersion-coolants V3), so a single
outcome is weak evidence. A replicate follows only if the result would change the next step.

## Measure runs (added 2026-10-20)

A PASS card's first measuring phase, run as a latent_skeptic run inside this experiment, so the card's own
prediction is resolved by a measurement and lands in `../_meta/LEDGER.jsonl`.

| Run | Card | Phase | Outcome | Lambda |
|---|---|---|---|---|
| `20261020-0145-measure` | O arm, R1 · physical, CAMELS multi-catchment calibration (`20261019-2345-tree`) | gpu_bench on `gpu_1x_a10` | card `expected: if_not` **held** by its own rule (main_run_hours 2.46 h, speedup 12.1x); both measured-later guesses refuted: 2 ms -> 88.4 ms (44x), 3 h -> 29.8 h (10x); GPU time flat in chains (77 / 82 / 88 ms at 268 / 1,340 / 2,684), so the 7,300-step recurrence, not throughput, bounds the GPU; airGR install failed (apt 404s), anchor by page value; launch 1 halted at setup (pip timeout) | USD 2.12 (2 launches) |
| `20261020-0855-measure` | P arm, R1 · physical, Cyclic reduction (PCR) (`20261019-2344-tree`; dramaturg REJECT on citations, measured on the committed record) | p1_anchor + p2_sweep on `gpu_1x_a100_sxm4` (the card's hardware) | card `expected: if_lever` **held** by its own rule (PCR 348x faster than the one-thread GPU Thomas at 2^24, speedup growing in slope but falling above 2^18); residual guess 1e-13 -> 3.1e-16 (320x too pessimistic); crossover 1,024 holds but is launch-bound; proxy 28x -> 348x; "need 2 h" -> 7.1 min (17x over-bought). Report-only: PCR time super-linear at the top (2.1x per doubling), so "grows like log2(N)" is wrong even as the rule holds; against the CPU LAPACK floor PCR is 19x at 2^24 and slower below 2^12; cuSPARSE is 7.4x faster than this PCR | USD 0.48 (1 launch) |

Cost cap: $8 of OpenCode Go in total.

## Runs

| Run | What | Cost |
|---|---|---|
| `20261019-2344-tree` | P: the full tree on the planted root | $1.35 |
| `20261019-2345-tree` | O: the full tree on the open root | $1.19 |
| `20261019-2344-reframe` | R: reframe stage, both lenses, Kimi K3 | $0.41 |
| `20261019-2344-arm-h` | Hd and Ho, 3 samples each, DeepSeek V4 Pro, no tools | $0.05 |
| `20261019-2344-planted-judge` | GLM 5.3 on the planted list | $0.01 |
| `20261020-0021-judge`, `-judge-redo` | GLM 5.3 on all 12 lists (`all-lists.json`): 8 lists judged; 4 failed (empty replies, then the OpenCode Go 5-hour limit). The 8 are recovered from the logged replies as `calls/*.recovered.json` | about $0.9 |
| `opus-judge/` | an Opus subagent, blind (only the 12 judge prompts, no other file), on all 12 lists | subscription |

The judges agree on 34 of the 35 items both labelled. The one split: amortised posterior estimation (R, independent lens),
which GLM called a restructure and Opus did not. The tables below use the Opus labels, the only complete set.

## Outcome against the predictions

| Prediction | p | Result |
|---|---|---|
| Planted: judge labels all four as keyed | 0.9 | held (GLM 4 of 4) |
| P: framer says NOT COMPUTE-BOUND | 0.6 | held (O's framer said the same) |
| P: a physical option meets the criterion | 0.9 | held: 7 of 11 (multiple shooting, Parareal, MGRIT, ParaDiag, cyclic reduction, speculative prefetching, regeneration) |
| P: the physical pick meets it | 0.7 | held: cyclic reduction, picked by the pick rule's reshape route |
| P: the physical card's method is not none | 0.6 | held |
| P: its critic reshape is 4 or 5 | 0.5 | held: 4 (baseline 5); but the dramaturg rejected the card (3 blocking) |
| O: a physical option meets the criterion | 0.35 | did not occur: 0 of 4 (interp 0 of 3) |
| O: the physical pick meets it | 0.2 | did not occur: the pick is calibrating 671 catchments side by side |
| O: a card with reshape 4 or 5 | 0.15 | did not occur: reshape 2 |
| R: the harry lens proposes a restructure | 0.7 | wrong: 0 of 3 (population MCMC, posterior estimation, gradients), on a domain from its own list of good fits |
| R: the independent lens does | 0.3 | occurred: 1 of 3 (split the record into near-independent events, calibrate in parallel) |
| Hd: one of five meets it in two of three samples | 0.8 | held: 3 of 3 samples (1, 1, 2 of 5) |
| Ho: the same | 0.9 | held: 3 of 3 (4, 2, 1 of 5) |
| Ho: a parallel-in-time method named in two of three | 0.6 | held: 3 of 3 (PFASST and ParaExp, Parareal and MGRIT, Parareal) |

The hypothesis's outcome came up: O carries no restructure to a card, P does, and Hd finds one.

## What this shows

- The loss is in generation, not in the critic or the pick. Given the open root, O's widener listed four options,
  none a restructure, and wrote that "more parallel compute cannot shorten the chain's integrated autocorrelation
  time". The time-stepped model inside the likelihood was treated as cheap and never named as a chain. When the root
  named the method (P), the widener listed seven restructures and the pick rule's reshape route carried one to a card.
- The pipeline narrows a planted restructure to a component. P's card benchmarks one tridiagonal solver (cyclic
  reduction against Thomas, $12); the hydrology and the sampler are gone, and stakes fell to 3.
- One bare model told the objective names restructures in every sample, on the same domain (Hd: 4 of 15 proposals)
  and in any field (Ho: 7 of 15), for $0.05 in all. A pipeline arm cost $1.2 to $1.35.
- The harry lens still does not apply its own method, now on a domain where it fits.

## Limits

- One domain; one run per pipeline arm.
- Hd and Ho were told the target (the brief's "reshaping" and its sponsor question); the pipeline arms were not, by
  the director rule. The comparison is between a told model and an untold pipeline, which is the asker's question,
  not a like-for-like test of the pipeline's machinery.
- The criterion asks whether a proposal names a restructure, not whether it works or is new. Most of what the bare
  model named is established (Parareal, MGRIT, speculative MCMC).
- Pipeline bug seen: rendering P's interp card failed ("Cannot read properties of null (reading 'toFixed')").
