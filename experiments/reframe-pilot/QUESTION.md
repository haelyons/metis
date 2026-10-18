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
