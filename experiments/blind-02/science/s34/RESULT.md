# blind-02 result: MEGADOCK GPU, dense search, four PINDER cases

**The seed's question:** "Can MEGADOCK's GPU implementation make denser docking search affordable, and does that improve pose recovery within a fixed budget?" The study is limited to four unbound PINDER cases (1aua, 1ax2, 1dv1, 1nr5). It compares three configurations: CPU standard sampling, GPU standard sampling, and GPU dense sampling with 54,000 rotations.

## The answer this route reached

The main comparison is run10: one A100 box, 7 timed replicates plus 1 warm-up for each configuration and case, and all 96 runs succeeded. Its rules were sealed before the run.

1. **The GPU gives the same science as the CPU at the same settings: yes, on all four cases.** The ranked poses, rebuilt models and DockQ values are identical. Only the printed scores differ, in the fifth significant digit.
2. **The GPU is faster: yes.** The complete workflow, including model building and scoring, is **2.35×** faster (95% interval 2.30–2.40). The docking step alone is about 4× faster.
3. **Dense search is not affordable at the CPU-derived budgets (1.5× and 2× the CPU run).**
   - Dense GPU search missed both budgets on every case and fitted only the loosest budget, which is built from dense's own run time.
   - On this box, dense costs about 1.7–2.1× the CPU-standard run.
   - The budgets were measured on an H100 box, where dense had fitted the 2× budget everywhere. **So whether dense fits a 2× budget depends on the hardware, and this route has not settled it on one box.**
4. **Does dense search improve pose recovery? Partly.**
   - The **best of the 50 retained poses** improves on all four cases: 1aua 0.76 → 0.90, 1ax2 0.04 → 0.92, 1dv1 0.77 → 0.87, 1nr5 0.46 → 0.57 DockQ.
   - The **top-ranked pose** does not improve consistently:
     - it is better on 1dv1 (0.74 → 0.82);
     - it is formally better but still wrong on 1ax2 (0.007 → 0.023);
     - it is unchanged on 1aua (both near 0);
     - **it is much worse on 1nr5 (0.46 → 0.02).**
   - Dense search finds better poses but does not reliably rank them first.

## How strong the evidence is, and why

**Strong for these four cases on this box.**
- The predictions and rules were sealed before the run, and the scorer's outcomes recompute by hand.
- Every output except timing and the printed scores was identical across replicates. The quality differences are therefore exact, but each case gives only one value.

**Limited in four ways.**
- **Four cases.** Nothing generalizes beyond them, and no biological conclusion is drawn.
- **One box type, and not the one the budgets came from.** The budgets came from an H100 box, and this run was on an A100.
- **Margins not validated for this GPU binary.** The agreement tolerances were derived on test fixtures with a GPU binary that differs from run10's. By the sealed rule, they are labelled "not applicable" to this run. The agreement result barely depends on them: the transforms, models and DockQ values are exactly identical, and the score differences are 65× inside the tolerance.
- **No independent DockQ check.** DockQ came from PINDER's published implementation, which no independent checker verified.

## What it cost

- **run10:** USD 2.74 of box time, 1.38 h of run wall (1.47 h allocated).
- **run9**, the fixture run that set the tolerances: about USD 2.66, 1.27 h.
- **blind-02 ledger:** USD 14.06 spent of the USD 100 ceiling, with USD 85.94 left.
- **Pilot:** about USD 126 of box time spent against the USD 2,000 cap.
- The hours of every earlier run are not totalled in the files this step read.

## What remains open

- **Whether dense search fits a 2× CPU budget on the same hardware.** This needs a calibration and a comparison on one known box type. The launch arguments cannot pin a box type, so this needs an owner-approved launcher change, not another test on this route.
- **Whether the agreement tolerances hold for run10's GPU binary.** A rerun cannot change the agreement answer, because the observed differences are zero or tiny.
- **Absolute DockQ accuracy**, and anything beyond these four cases.

This step stops with `no_justified_test`: the question is answered as far as this route can answer it.
