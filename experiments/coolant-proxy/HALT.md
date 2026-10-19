# HALT — coolant_proxy attempt 2, run cp1, step 5 (run), pre-launch box build

Time: 2026-10-18T20:45Z. Lambda spend: $0.00. Instances running at halt: 0 (GET /instances at 20:43:37Z).
No GPU box was ever launched in attempt 2.

## What halted

The built runner's pre-launch stage (`run_cp1.py extract`, run on this workstation as the build directs) could not
build any of the 24 simulation boxes (8 molecules × packing seeds 61453, 61454, 61455). Every build ran the committed
builder (`data/MD-ML-thermophysical/MD/builder/smiles2loplsaa.py`, sha256 `91cac1d5…7008`) at the gate's packing
density of 0.75 g/cm³. Each one ended with:

    ERROR: Packmol failed with exit code 173:
    STOP 173

Packmol 21.2.1 uses exit code 173 for "ENDED WITHOUT PERFECT PACKING". The builder then exits 2 and writes no files.
Builds took 1188 to 2447 s each (mean 1828 s); the stage ran 3 h 08 min with 4 builds at a time.

The runner recorded it as:
- `out/results_cp1/prelaunch/stage-prelaunch-summary.json`: decision `DO_NOT_LAUNCH`, failed step `build`
  (inputs PASS, endpoint 1 data pre-check PASS). sha256 `e7b2cc83…e494`.
- 24 per-box records `out/results_cp1/prelaunch/molecule-*_step-build.json`, all `FAIL`, all with stderr "STOP 173".
- `out/results_cp1/prelaunch/RUN_VALID.json`: `run_valid: false`.
- Log: `out/prelaunch_extract_cp1.log` (ends `exit=3`).

A separate identical build of mol_00105 / seed 61453, run while the stage was still going, gave the same result
after 2018 s (`out/diag_build_mol00105_seed61453_cp1.json`).

## Why it stops here

GATE_COMMIT.md, addendum part (c), set the packing density and decided this case in advance:

> If Packmol cannot pack any box at 0.75, stop before launch and report. Do not lower the density for some boxes only.

The build's own directive is to launch only if the pre-launch summary reads `LAUNCH_ALLOWED`. It reads
`DO_NOT_LAUNCH`.

## Why no retry

- Rerunning the same stage would repeat the same failure: the packing seeds are fixed, and the builder, density and
  Packmol version are pinned.
- Every way to pack the boxes changes something the gate decided: the density (0.75), or the builder's Packmol
  tolerance (2.0 Å, its default). The operator may not edit GATE_COMMIT.md or the built runner. The gate's written
  answer to exactly this case is "stop before launch and report". Asking a new gate agent for a different density
  would be asking until a more convenient answer came back.

## Likely cause (operator's reading, not checked by a gate)

The builder packs molecules inside a box shrunk by its 2.0 Å tolerance on every face. For mol_00426 the box side is
56.81 Å and the packing region 52.81 Å, so 0.75 g/cm³ over the whole box is about 0.93 g/cm³ in the packing
region ((56.81/52.81)³ = 1.245), with at least 2 Å between atoms of different molecules. That is at or above the
liquids' real densities (0.80 to 0.96 g/cm³ in the paper's MD). The dataset's own README packs at 0.3 g/cm³ "dilute
on purpose; equilibration compresses them to the real density". The gate chose 0.75 so that density would level off
before the 0.2 ns diffusion window opened. It noted that it "did not check which packing density the paper itself
used".

## What a next attempt would have to decide (for its design and gate, not decided here)

- A packing density that Packmol can reach with this builder for all 8 molecules (the README's 0.3, or something in
  between), applied to all 24 boxes.
- With a dilute start, whether 0.2 ns of constant-pressure run still reaches a steady density before the diffusion
  window. Either the window moves later, which costs box time, or the gate's density-levelling readout becomes a
  binding check rather than report-only.
- Packing all 24 boxes takes about 3 h on this 4-core workstation at 0.75 g/cm³, and failed runs cost the same. A
  short pack-test of the largest molecule at the chosen density before committing all 24 would surface this early.

## State at halt

- Lambda: 0 instances; spend $0.00 for attempt 2 (and $0.00 for attempt 1).
- `boxes_cp1/` holds the decks and reference table, and 24 empty `pack<seed>` folders. No box file exists to ship.
- `lambda_run_cp1.sh` and `remote_run_cp1.sh` were prepared and never run.
- Post (step 6) was not run: there are no results to post on.
