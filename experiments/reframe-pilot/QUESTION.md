# reframe-pilot

Can a separate reframing stage find where a change of metric, unit of work, objective or order would let more compute
change an answer, rather than buy more of the same? Its output is a question someone could investigate.

Design (written before the run):
- Tool: `reframe/reframe.js`, outside `pipeline/`. Two lenses on the same model (Kimi K3): `harry` (a loop computed
  all at once by guess-and-correct, its forgetfulness test, its five-feature filter) and `independent` (which
  assumption makes the work slow or more of the same). A judge on another model (GLM 5.3) classifies each question as
  reframe, copies or other, and checks the case's criterion where there is one. No tools for any agent.
- Cases (`cases.json`):
  - `vla`: run F's option R2·interp·A exactly as the branch wrote it. It already proposes batching rollouts (copies).
    The producer later found a reframe the option does not contain: score steering on recorded frames instead of
    closed-loop episodes, then confirm the top features closed-loop. That is this case's criterion: a known positive.
  - `weather`: the passing ensemble-size card. No criterion.
  - `coolant`: the passing V1 card (molecular dynamics against measured data). No criterion.

Predictions (written before the run):
- `vla`: the independent lens meets the criterion; the harry lens proposes computing the 56-call rollout all at once
  and does not.
- `weather`: the harry lens predicts its method fails on chaotic dynamics; the independent lens proposes spending
  compute on the tail (rare-event sampling or splitting) instead of more members.
- `coolant`: the harry lens predicts failure for chaotic molecular dynamics; the independent lens changes the metric
  (ranking or triage) rather than the number of molecules.
- Batching more rollouts, members or molecules is judged copies wherever it appears.

What it tells us: whether a separate stage finds a known-good reframe from the bare option; whether the harry lens adds
anything beyond its own method; whether the judge separates reframes from copies; the cost of one pass. It does not
tell us whether any reframe works: that needs a measurement.

| Run | Result |
|---|---|
| `20261018-1021-reframe` | 18 questions (3 cases x 2 lenses x 3), all first-attempt valid, $0.76. Known positive found by the independent lens (question 1) and, more loosely, by the harry lens (question 3). The judge called all 18 "reframe" and none "copies". |

## Outcome against the predictions

- `vla`, independent lens meets the criterion: **held.** Its first question scores steered action-chunk divergence on
  recorded states and checks the ranking against closed-loop success (Spearman over about 30 features).
- `vla`, harry lens proposes computing the 56-call rollout all at once and misses: **wrong.** It never proposed its own
  method. It turned the forgetfulness test into short steered-versus-unsteered branches from checkpoints, and its third
  question (rank features by activation gaps in the 420,000 logged rollouts, confirm the top ones closed-loop) was
  judged to meet the criterion. That is correlational mining rather than steering on recorded frames: a loose match.
- `weather`, harry lens predicts failure on chaotic dynamics: **wrong.** It did not mention its method; it proposed
  extrapolating skill to infinite members, fitted "virtual members", and pooling model families.
- `weather`, independent lens proposes rare-event sampling: **wrong.** It proposed separating Monte Carlo error from
  shared model error by resampling the existing 7,424-member HENS archive, scoring return levels instead of fixed
  percentiles, and a power analysis showing whether 7 dates can resolve a slope at all.
- `coolant`, harry lens predicts failure for molecular dynamics: **wrong.** It proposed pairwise ordering on the
  published 8-molecule table, a force-field parameter sweep, and simulating blends directly.
- `coolant`, independent lens changes the metric: **held.** A 1-ns diffusion proxy for viscosity ranking, a learned
  residual correction, and a variance decomposition that steers the remaining budget.
- Batching judged copies wherever it appears: **not tested.** No proposal batched anything, so the judge never had a
  copies case; it needs a planted one.

Most questions are answerable by reanalysing data that already exists (the HENS archive, the published 8-molecule
table, the logged rollouts) for $0 to $25. The harry brief behaved as a second general reframer with a convergence
flavour, not as its namesake method.
| `20261018-1057-planted-glm` | GLM judge on the VLA list with three planted proposals mixed in (`planted.json`; key in `planted-key.json`, not shown to the judge): 3 of 3 planted judged as expected (two copies, one near-miss that fails the criterion) |
| `20261018-1057-reframe-a`, `-b` | two reruns of all cases; all 12 reframer calls completed; 7 of 12 GLM judge calls blocked by the OpenCode Go weekly limit (`all-lists.json` gathers every proposal) |
| `20261018-opus-judge` | an Opus subagent judged all 63 proposals (19 lists) from `judge_input.json`, without the GLM labels |

## Judges and stability (2026-10-18)

- Planted proposals: both judges 3 of 3. Each can say "copies", and both separate a near-miss from the criterion.
- GLM against Opus on the 45 proposals both judged: kind 45 of 45, criterion 44 of 45. The one disagreement is the
  first run's loose harry match: GLM said yes when judging that list alone and no inside the mixed list; Opus said no.
- Opus called 60 of 63 proposals reframes and 3 copies: the two planted ones and one real proposal (a rerun's harry
  coolant question that only resized replicas).
- The VLA known positive (score steering on recorded observations, confirm the top features closed-loop), by run:
  first run, independent lens only; rerun a, harry lens only; rerun b, both. At least one lens found it in all three
  runs; each lens alone found it in two of three.

