# Narrowing (s32)

No narrowing. Unchanged from s31 (`science/s31/NARROWING.md`); s32 changes only the visible form of the same run's design and brief.

The root question held fixed is the seed's own, verbatim (`experiments/blind-02/m5/BRIEF.md:1`): "Can MEGADOCK’s GPU implementation make denser docking search affordable, and does that improve pose recovery within a fixed budget?" It applies to the four pinned apo PINDER cases (1aua, 1ax2, 1dv1, 1nr5) and the seed's three configurations.

The main comparison (`main_design.json`) carries every part of that question:
- CPU/GPU agreement at identical settings under justified tolerances (s13 K1–K3; design K1, K8, K2, K3, with s30's margins from s27's sealed rule);
- execution acceleration (K4);
- affordability of dense sampling at the common budget tiers from the runtime calibration (K5 as K5, K9, K10);
- rank-1 and best-of-50 recovery, reported separately (K6, K7).

Negative results are kept, and the conclusions stay limited to the four cases.

Nothing is dropped. The box type cannot be pinned on this route. Its consequence is handled by reporting rules that were sealed before s31 (s27 §3 step 4) or are stated in `science/s31/ASSESSMENT.md` §B4 before the run:
- the margins are labelled "not applicable" on a box that differs from run9's;
- the tier comparisons are labelled cross-hardware off run6's box type.

These rules change how strongly a part may be claimed. They do not change which parts the question asks.
