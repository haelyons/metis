# Root question and scope (s05)

No narrowing. The root question is unchanged from the seed and from s01–s04:

> Can MEGADOCK’s GPU implementation make denser docking search affordable, and does that improve pose recovery within a fixed budget?

**Kept: every seed obligation** (`experiments/blind-02/m5/BRIEF.md:3–23`), as listed in `science/s04/NARROWING.md:7–18`:

- the four original unbound PINDER 2024-02 cases;
- the three configurations (CPU standard, GPU standard, documented GPU dense);
- fixed scoring and 50 retained predictions;
- correct execution, and independently justified same-settings CPU/GPU agreement before any quality comparison;
- per-case rank1 and best50 DockQ, reported separately;
- runtime-calibrated common budgets and sealed rules;
- complete workflow time, GPU activity and billed allocation cost;
- preserved negatives, unavailable arms and overruns;
- a four-case pilot only;
- native references used for evaluation only.

**Dropped: nothing.**

**Why there is no change.** Run5 measured nothing: its intake agent could not open the brief, so no stage after intake ran. A failure caused by the pipeline gives no reason to drop or change any part of the question. The s04 timing calibration (all three configurations, timing only) stays the pending prerequisite, unchanged. Agreement, acceleration, affordability and quality all remain open.
