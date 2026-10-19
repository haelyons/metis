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

Cost cap: $8 of OpenCode Go in total.
