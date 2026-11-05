# Narrowing (s34)

No narrowing. This is unchanged from s31–s33 (`science/s33/NARROWING.md`).

**The root question held fixed** is the seed's own, verbatim (`experiments/blind-02/m5/BRIEF.md:1`): "Can MEGADOCK’s GPU implementation make denser docking search affordable, and does that improve pose recovery within a fixed budget?" It applies to the four pinned apo PINDER cases (1aua, 1ax2, 1dv1, 1nr5) and to the seed's three configurations.

**Kept:** every part of the question. run10 tested all of them in one sealed design:
- CPU/GPU agreement at identical settings (K1, K8, K2, K3);
- execution acceleration (K4);
- affordability of dense sampling at the three budget tiers (K5, K9, K10);
- rank-1 and best-of-50 recovery, reported separately (K6, K7).

**Dropped:** nothing.

**How strongly two parts can be claimed.** Two reporting rules were sealed before the run (s27 §3 step 4; s31 §B4) and are now applied:
- the derived margins are "not applicable to this main run", because the megadock-gpu binary differs from run9's;
- the tier comparisons are cross-hardware, because the H100 tiers were applied to an A100 run.

These rules limit how strongly agreement-by-margin, quality-by-margin and affordability can be claimed. They do not change which question is asked. Same-hardware affordability stays open, and is reported as open rather than replaced by another question (`ASSESSMENT.md` §D, §E).
