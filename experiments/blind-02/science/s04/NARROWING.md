# Root and calibration scope

No narrowing. The root question is unchanged from the seed and from s01–s03:

> Can MEGADOCK’s GPU implementation make denser docking search affordable, and does that improve pose recovery within a fixed budget?

**Kept: every seed obligation** (`experiments/blind-02/m5/BRIEF.md:3–23`):

- the four original unbound PINDER 2024-02 cases;
- the three existing MEGADOCK configurations: CPU standard, GPU standard and documented GPU dense;
- fixed scoring and 50 retained predictions;
- correct execution and independently justified same-settings CPU/GPU agreement before any quality comparison;
- per-case rank1 and best50 DockQ, reported separately;
- runtime-calibrated common budgets and sealed rules;
- complete workflow time, GPU activity and billed allocation cost;
- preserved negatives, unavailable arms and overruns;
- a four-case pilot only, with no biological efficacy inference;
- native references used for evaluation only.

**Dropped: nothing.**

**Scope of the next test.** The next test is the seed's own runtime calibration step. It times all three configurations and defines budget tiers. By design it reads no native references and computes no comparison between arms, because the seed requires tolerances to be justified before comparative results are examined. Agreement, acceleration verdicts, affordability verdicts and quality effects remain open, not dropped.

**Run4.** Run4's CPU-standard evaluator screen passed (maximum 2.573 s against a 60 s allowance). It does not resolve the full card input for GPU-standard and dense evaluation.

**Candidates.** Both remain under consideration: seed:idea:2 provisionally, and R1:physical:P1. The rejected and halted cards keep their states.

**Changes to the question.** None. Neither CPU-only timing nor timing-only calibration replaces the question.
