# RUN SUMMARY — coolant_proxy, attempt 2 (run cp1)

**Outcome: halted before launch. No answer to the question.** No simulation ran, so nothing was measured against any
refutation condition. Lambda spend: $0.00.

## The question (QUESTION.md)

For the eight benchmark lubricant molecules of Ogbomo, Carman, Dini and Ewen, compute a viscosity proxy from about
1 ns of LOPLS-AA molecular dynamics at 40 °C (self-diffusion combined with density and molecular size). Does the
proxy's ordering match the reference viscosities with Spearman rho ≥ 0.8?

What would refute it (QUESTION.md, "What would refute each claim"):
1. Spearman rho < 0.8 against the reference viscosities at 40 °C. The abandon line is rho < 0.6.
2. The 1-ns ordering is not stable across independent replicas, or disagrees with a longer trajectory.
3. Total MD cost per molecule is not well below the paper's Green-Kubo cost (about 1.5 × 10⁴ CPU-hours per molecule
   per temperature).
4. The rho ≥ 0.8 rests on an ordering already fixed by chemical family; within-family order is wrong.

## What was run

| Step | Outcome | Record |
|---|---|---|
| 1 Seed | Not re-run (QUESTION.md and data/ stand from attempt 1) | QUESTION.md |
| 2 Design | First launch halted: the Workflow tool was not enabled. After the owner's "configure" instruction, `.claude/settings.json` turned it on. The second launch returned a design at $19 against the $20 cap. It used an Amber GPU benchmark (PROXY) × a guessed 0.15. The OpenMM benchmarks page returned 404. | out/design_attempt2_wf_1e76375d-cc7_return.json, out/design_record_attempt2.json, out/gate_text_attempt2.md, HALT_attempt2_noworkflow.md |
| 2b Calibration | Not triggered (design did not halt on budget) | — |
| 3 Gate | Budget approved up to $19, cap not raised; design approved for build with changes; later addendum with execution directives after build halt 1 | GATE_COMMIT.md |
| 4 Build | Try 1 halted: no execution note, and no local toolchain. Try 2, after the gate addendum and a local micromamba toolchain, succeeded once resumed after an account session limit. The runner's selftest passed: 217 checks. | out/build_cp1_try*_return.json, run_cp1.py, onbox_cp1.sh |
| 5 Run | Launcher copy made with header-listed edits only. The local pre-launch stage **failed**: 0 of 24 boxes built, Packmol exit 173 at 0.75 g/cm³. The summary reads DO_NOT_LAUNCH. Per the gate, stop before launch. **No launch.** | out/results_cp1/prelaunch/, out/prelaunch_extract_cp1.log, HALT.md |
| 6 Post | Not run (no results) | — |

## Measured numbers against the refutation conditions

- **Claims 1, 2 and 4:** nothing measured. No trajectory exists.
- **Claim 3 (cost):** nothing measured on a GPU. One incidental number: packing one box with the committed builder took
  20 to 41 min of one CPU core (1188 to 2447 s, mean 1828 s), and it failed in every case.
- **Endpoint 1 (data pre-check, before any simulation):** PASS. Both committed reference files give the same order of
  the eight molecules at 40 °C (`endpoint-1_stage-prelaunch_step-data-precheck.json`). This checks the reference
  data only, not the proxy.

## Spend

Lambda: $0.00 in attempt 2 (0 launches), $0.00 in attempt 1. GET /instances at 2026-10-18T20:43:37Z: 0 instances.
Local workstation: about 3 h 08 min of 4 cores for the failed box builds, plus one 34-min diagnostic build.

## What halted, and why

1. **Design, first launch (11:54Z):** halted because the Workflow tool was not available. Fixed by configuration on
   the owner's instruction, then rerun.
2. **Build try 1:** halted with blockers. Fixed by a gate addendum (execution directives) and a local toolchain.
   Try 2 completed.
3. **Run, pre-launch (20:43Z): final halt.** The committed builder could not pack any box at the gate's density of
   0.75 g/cm³ (Packmol "ENDED WITHOUT PERFECT PACKING", exit 173, 24 of 24). The gate had ruled on this case in
   advance: "If Packmol cannot pack any box at 0.75, stop before launch and report. Do not lower the density for some
   boxes only." The likely cause: the builder packs inside a box shrunk by its 2.0 Å tolerance on every face, so
   0.75 g/cm³ becomes about 0.93 g/cm³ in the packing region. The dataset README packs at 0.3 g/cm³. Details, and
   what a next attempt would have to decide, are in HALT.md.

Nothing was committed or pushed. The transcript of this session is in this folder:
`a6c94dfb-fed7-47bd-b10c-731a7357443f.jsonl`.
