# Root question and scope (s06)

No narrowing. The root question is unchanged from the seed and from s01–s05:

> Can MEGADOCK’s GPU implementation make denser docking search affordable, and does that improve pose recovery within a fixed budget?

**Kept: every seed obligation** (`experiments/blind-02/m5/BRIEF.md:3–23`), as listed in `science/s05/NARROWING.md:7–18`:

- the four unbound PINDER 2024-02 cases;
- the three configurations;
- fixed scoring and 50 retained predictions;
- correct execution and justified same-settings CPU/GPU agreement before any quality comparison;
- per-case rank1 and best50 DockQ, reported separately;
- runtime-calibrated common budgets and sealed rules;
- complete workflow time, GPU activity and billed allocation cost;
- preserved negatives, unavailable arms and overruns;
- a four-case pilot only;
- references used for evaluation only.

**Dropped: nothing.**

**Why.** The new information is an infrastructure finding: why run5's intake could not read its brief, and how the launcher now provides read access. It gives no scientific reason to change the question. The next test is s04's timing-only calibration again, unchanged, and it drops nothing.
