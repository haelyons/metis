# HALT — coolant_proxy run, step 2 (design)

Time: 2026-10-18T11:34:17Z. Lambda spend: $0.00. Instances running at halt: 0 (checked via GET /instances).

## What halted

The design step of the pipeline (pipeline.js, design mode, run wf_b06f2a6a-35f) returned
`{"halt": "budget_over_cap"}`. The design agent priced its own minimal experiment at $200.
The cap passed to it, and the run's cap, is $20. The pipeline stops at that check by construction.
It never reached the departure-question or triage stages, so no gate text was produced.

Verbatim return: `out/design_wf_b06f2a6a-35f_return.json` (and its result field alone in
`out/design_attempt1_halt.json`).

## Why the design costs $200 (its own stated guesses)

- About 92 ns of simulated time: 8 molecules × 3 replicas × (1 ns equilibration + 1 ns production),
  plus a 5 ns longer run per molecule for the stability check, plus 2 calibration molecules.
- GUESS: 25 ns/day for a 15,000-atom box on one GPU, so about 88 GPU-hours, plus 50% for setup and reruns.
- GUESS: $1.5 per GPU-hour.
- The design itself notes the cost could fall between $100 and $400 if the price guess is wrong by 2×.

The longer runs (40 ns of the 92) exist to test the question's second refutation condition
(does the 1-ns ordering agree with a longer trajectory). Dropping them would remove a test the
question requires. That is a design choice a gate could make, but the pipeline halts before any gate
exists, and the operator may not rewrite the design or raise the cap.

## Why no retry

The design step was not re-run. Re-running the same prompt until a cheaper estimate came back would
turn the budget check into a sampling loop and defeat it. The operator's instructions also forbid
editing the design and the gate agent may not raise the $20 cap. A halt is a valid outcome.

## What would unblock it (for the human owner, not done here)

Either raise the cap to roughly the design's estimate, or measure the real throughput first.
The $200 rests on an unmeasured 25 ns/day guess; a short paid benchmark on one box would show
whether the true figure is several times higher, which would bring the same design under $20.
Or narrow the question (for example, drop the longer-trajectory check) and re-seed.

## Booked deviation

A first design launch (wf_90b1785e-680) was sent with a placeholder seed string by operator error.
It was stopped within seconds, returned nothing, and nothing from it was used. The second launch's
prompt was checked against QUESTION.md: same text, differing only in line indentation.

Steps 3–7 (gate, build, run, post, close) were not run. No Lambda instance was ever launched.
