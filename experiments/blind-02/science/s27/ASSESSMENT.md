# s27 assessment: fixture analysis for the agreement margins (2026-11-04)

**Scope.** This was an offline step. I used no network, contacted no box, ran no git commands and read no credentials. The Bash tool was denied in this session, so I wrote every file with the file tool and hashed nothing. I wrote only into `science/s27/`.

**What I read.**
- s13 (`FINAL.json`, assessment), s15 (`SHAPES.json`, assessment), s26 (assessment, prompt) and s07 §A–§D; for s16–s25 I worked from their assessments' K1–K3 passages.
- The run6 calibration brief (`science/s06/CALIBRATION_BRIEF.md`), the physical card's plan (`20261103-0124-tree/out/work/seed-20261103/R1/physical/1fffee1a/producer.md`, called PC below) and `dut/pipeline/m5/SCHEMAS.md:115–203`, whole.
- The scorer's error code `dut/pipeline/m5/score_comparison.py:469–504`.
- The blind-01 run11 unit manifest and intake inventory (`experiments/blind-01/m5/run11/agent/harness/units.json`, `.../intake/data.json`).

**Verdict.** A fixture run is justified and fits the limits.
- I sealed a tolerance rule for every margin the main comparison needs (`TOLERANCE_RULE.md`, `tolerance_rule.json`).
- The fixture run (`fixture_design.json`, `FIXTURE_BRIEF.md`) only records values. All 12 of its comparisons are `exact`.
- The error budget is **partly** feasible. Analysis bounds serialization, determinism and the FFT roundoff (loosely). Two sources can only be measured, not bounded: GPU nondeterminism and the effect of `-use_fast_math` on voxel assignment.
- Next: **m5**, projected about USD 7, worst case USD 14.5, 1–3 h expected.

## A. The main inputs, and the fixtures

**Main comparison (s13, s15).**
- **Arms** (`s13/FINAL.json:2–4`; `s13/ASSESSMENT.md:13–17`):
  - A0: CPU MEGADOCK at 3600 rotations;
  - A1: GPU MEGADOCK, identical settings;
  - A2: GPU at 54000 rotations (`-D`).
- **Margin comparisons:**
  - K1, K2 and K3 are A1 against A0 (`FINAL.json:7–9`). Each is `per_input_all`, `paired_replicate`, `all_pairs` (`s15/SHAPES.json:2–4`).
  - K6 and K7 carry `0.01 + 2·eps_eval` (`s13/ASSESSMENT.md:51–57`).
- **Inputs** (`s13/ASSESSMENT.md:66`; `m5/BRIEF.md:3`): the four seed cases, each the apo pairing of PINDER `2024-02` (`m5/b01_materials/BRIEF_run1.md:56–158`):
  - `1aua__A1_P24280--1aua__A2_P24280:apo`
  - `1ax2__A1_P16404--1ax2__A2_P16404:apo`
  - `1dv1__A1_P24182--1dv1__B1_P24182:apo`
  - `1nr5__A1_P07547--1nr5__A2_P07547:apo`
- **Prepared hashes and settings.** The prepared hashes are at `s06/CALIBRATION_BRIEF.md:340–343`. The shared settings are `-N 50 -t 1 -v 1.2 -e 1.0 -d 1.0 -a -45.0 -b 1.0 -f 3` (`:387–391`).

**Fixtures chosen.** These are the holo test-set monomer pairs of four PINDER `2024-02` systems. They are the non-seed systems of the same blind-01 unit manifest that held the seed cases: run11 `units.json` lists 16 units, with ids at lines 4–844, and the seed cases sit at its indices 3, 5, 9 and 15 (`BRIEF_run1.md:48`). URLs, bytes and SHA-256 come from blind-01 run11 `intake/data.json`.

| input id | PINDER system | receptor / ligand source (bytes) | native (bytes) | data.json lines |
|---|---|---|---|---|
| f1a19 | `1a19__A1_P11540--1a19__B1_P11540` | 58320 / 58320 | 116559 | 14662–14667, 28000–28014 |
| f1dtd | `1dtd__A1_P48052--1dtd__B1_P81511` | 192132 / 38313 | 230364 | 15184–15189, 28090–28104 |
| f1glj | `1glj__A1_P0A6F3--1glj__B1_P0A6F3` | 316791 / 316791 | 633501 | 15598–15603, 28180–28194 |
| f1ht8 | `1ht8__A1_P05979--1ht8__B1_P05979` | 362718 / 362718 | 725355 | 15760–15765, 28252–28266 |

**Same numerical path.** Each fixture runs exactly the main arms' code path:
- **Binaries and flags.** The same two MEGADOCK binaries are built from the same commit with the same flags (single-precision FFTW `-lfftw3f` on the CPU; cuFFT with `-use_fast_math` on the GPU; `s06/CALIBRATION_BRIEF.md:361–369`). The same command lines and environment are used (`OMP_NUM_THREADS=26`, `CUDA_VISIBLE_DEVICES=0`; `:387–391`), as are the same 3600-rotation set, voxel size and scoring settings.
- **FFT path.** It is the same FFT correlation, translational reductions and ranking to 50 rows.
- **Reconstruction and evaluation.** The same `decoygen` and model assembly are used (`:393`), and the same PINDER BiotiteDockQ evaluator (`:330`) with R/L mapping.
- **Inputs.** The preparation rule is the same (chain field to R/L; `:336`), and the inputs are the same kind of file: PINDER monomer PDBs.
- **Size range.** Monomer sizes span 38–363 KB, against 150–277 KB for the main prepared sources (`BRIEF_run1.md:75, 102, 129–130, 156`). The grid sizes therefore bracket the main cases.
- **Chain mapping.** Three fixtures are homodimers, like all four seed cases. f1dtd adds a heterodimer.

**The one difference: holo, not apo.** These are bound conformations. In holo inputs the identity rotation is near-native, so the fixtures' DockQ values will sit higher than the seed cases'. This changes which poses are evaluated, not the arithmetic. I chose holo because blind-01's records pin these files by hash, while the apo files of the four disjoint systems cannot be identified from the records without the index.

**Disjointness rule.** A fixture is admissible iff all three hold:
1. its PINDER system id differs from each seed id;
2. none of its UniProt accessions is among the seed accessions {P24280, P16404, P24182, P07547};
3. none of its source, prepared or native files has the SHA-256 of any file recorded for a seed case. That covers the sources, prepared files, natives, holo test-set members and alternates in `BRIEF_run1.md:72–273`, and `s06:340–343`.

Rule (2) excludes every structure of a seed protein, including the seed systems' own holo and AlphaFold files. The fixtures' accessions are P11540, P48052, P81511, P0A6F3 and P05979, so (1) and (2) hold. I checked (3) by comparing the listed hashes by eye; no Bash was available. The prepared fixture hashes do not exist yet, and the run's setup records them.

The fixture run also never fetches or reads any seed file. Its brief tells setup not to (`FIXTURE_BRIEF.md`, comparison request).

## B. Analytic error budget

Notation: u = 2^-24 ≈ 5.96e-8 (binary32).

**Outputs the margins concern:**
- `transforms`: main K1 identity;
- `coords`: main K1 eps_xyz;
- `scores`: main K2;
- `dockq`: main K3, and through eps_eval, K6/K7.

| # | Source | Affects | Expected size for a correct arm | Evidence | Fixtures measure? |
|---|---|---|---|---|---|
| 1 | Floating-point precision. Both FFT paths are binary32. | scores | Worst case, per correlation peak: A_rel(N) = (3·log2 N³ + 1)·5u·N^1.5 relative, about 0.02–0.06 for N = 100–200. The typical normwise size is about (log2 n)·u ≈ 1e-6 to 1e-5. | `-lfftw3f` and `-lcufft` (`s06:363, 369`). The bound form follows the FFT normwise error result of Higham, *Accuracy and Stability of Numerical Algorithms*, 2nd ed., §24.1. **This is recalled, not a repository file, and was not re-read (no network).** The √n factor converts a normwise bound into a per-element bound and is my derivation. | Yes, as the combined score difference (F-K4, F-K6). Analysis gives only the loose ceiling the rule checks against. |
| 2 | Reduction and summation order (FFTW vs cuFFT plans; GPU translational max reductions). | scores; transforms at near-ties | Scores: the same order as #1. Transforms change only where two candidates' scores are within that error, at rank ties or cutoff membership. The size cannot be bounded without the score landscape. | No file states the plans. "Tie mismatch fails this strict gate" (PC:58). | Yes (F-K1, F-K3). |
| 3 | Nondeterministic GPU kernels. | all GPU outputs | Unknown in magnitude. Only file hashes exist. | GPU `docking.out`: 39 distinct SHA-256 in 40 files. CPU: one hash per case in 20/20 (`s07/ASSESSMENT.md:116–118`). | Yes, GPU self-agreement (F-K3, F-K6, F-K9, F-K12). |
| 4 | Compiler flags (`-use_fast_math` on the GPU build only). | scores; transforms | Approximate trig and flush-to-zero perturb rotated ligand coordinates by roughly 1e-6 relative (about 3e-5 Å at 30 Å). A grid assignment flips when an atom lies within that distance of a voxel boundary (`-v 1.2`): roughly 5e-5 per atom per rotation. This is my estimate, not a measurement. Each flip moves one atom's score contribution. That cannot be bounded without MEGADOCK's scoring source, which is not in the repository. | `s06:360, 366` ("retain published -O3 and -use_fast_math") | Only in cross-arm agreement (F-K4, F-K1). The effect is deterministic, so GPU self-agreement does not show it. |
| 5 | Library and driver versions. | all | Controlled, not measured. CUDA 12.8, driver 570.148.08, H100 PCIe (`s07:74–75`). FFTW is the distro package; its version is not in the files I read. | Rebuilding on this box type reproduced the CPU binary hash `4b85db6e…` in run4 and run6 (`s07:94`). The pipeline records executables and library hashes (`SCHEMAS.md:171`). | No. The rule (§3 step 4) requires identity between the fixture run and the main run. |
| 6 | Seeds. | none | 0. The FFT search is exhaustive and deterministic, with no random sampling. `order_seed` only orders invocations (`SCHEMAS.md:172`). | "deterministic repeats do not increase biological sample size" (PC:30). CPU byte-reproducible (`s07:116`). | Confirmed by CPU self-agreement (F-K2, F-K5). |
| 7 | CPU threading (26 OpenMP threads). | CPU outputs | 0 observed. | CPU 20/20 identical in run6 under the same environment (`s07:116`; `s06:387`). | Yes (F-K2, F-K5, F-K8). |
| 8 | Text serialization. | scores; coords | Scores: one unit of the last printed digit (atol = 10^-d, d read from the files by the rule). Coordinates: PDB `%8.3f` gives 0.001 Å. `decoygen` is one CPU binary for every arm (`fixture_design.json` commands), so identical transform rows give identical coordinates. | `s06:393`; run6 validation reads 7-field rows (`m5/run6/agent/harness/run_command.sh:125–141`) | Coordinates: yes (F-K7–F-K9, on pairs with identical transforms). Score print resolution: read from the files. |
| 9 | Evaluator. | dockq | 0 for byte-identical models (deterministic CPU code). If coordinates differ by at most 0.002 Å, the continuous DockQ terms move by at most about 0.0005. Each flipped native contact moves Fnat by 1/N_c, which is 1/(3·N_c) in DockQ. This uses DockQ = (Fnat + 1/(1+(iRMS/1.5)²) + 1/(1+(LRMS/8.5)²))/3 (Basu & Wallner 2016, **recalled, not a repository file**). The absolute accuracy against an independent implementation (PC:59) is not measurable on this route and stays an uncertainty. | Run4 evaluator: 16 walls, max 2.573 s (`s26/ASSESSMENT.md:38`) | Repeatability: yes (F-K11 on identical CPU models; F-K10 and F-K12 on pairs with identical transforms). Accuracy: no. |
| 10 | Shared hardware state between parts | all | None expected for deterministic code. | Declared residual (`SCHEMAS.md:116`) | Covered by the self-agreement pairs. |

**Summary.**
- **Measured by the fixtures:** #2, #3, #4 and #7, together with the realised size of #1.
- **Bounded only by analysis:** #1 (as the loose ceiling A_rel), #6 and #8 (resolution units).
- **Controlled by identity checks:** #5.
- **Unbounded and kept as uncertainty:** #9's absolute accuracy.

So the budget is `partly` feasible on `fixtures_and_analysis`.

**What the fixtures cannot do.** They cannot make the card's exact transform-identity criterion achievable. If GPU self-agreement fails on the transforms, a correct GPU arm will fail the exact gate with no CPU involvement. The rule reports that as flag G_T and does not relax the criterion (PC:66).

## C. Tolerance rule (sealed now)

The full rule is in `TOLERANCE_RULE.md`. `tolerance_rule.json` has one item per margin: M1 to M6.
- **M1, K1 transform identity:** stays `exact` (no margin). The fixtures only set the flags X_T, C_T and G_T.
- **M2, K1 coordinates:**
  - `eps_xyz = up2(max(0.001 Å, 2·Mxyz))`, where Mxyz is the maximum coordinate error over pairs whose transforms are byte-identical.
  - Defensible iff Mxyz ≤ 0.001 Å and every fixture has at least 4 CPU-self pairs.
- **M3, K2 scores:**
  - `atol = 10^-d` (the printed resolution) and `rtol = up2(max(2·MR, 1e-6))`. MR is the maximum relative score error over the cross, CPU-self and GPU-self pairs.
  - Defensible iff no count mismatch and, per fixture, every maximum ≤ A_rel(N_f).
- **M4, K3 DockQ:**
  - `eps_eval = up2(max(0.001, 2·Me))`, where Me is the maximum DockQ error over pairs with identical transforms.
  - Defensible iff eps_eval ≤ 0.01 and every fixture has at least 4 CPU-self pairs.
- **M5 and M6, K6/K7:** `0.01 + 2·eps_eval`. Defensible iff M4 is.
- **Run-level conditions:**
  - If the run fails (V0), every derived margin is indefensible.
  - If any fixture comparison has fewer than 4 present pairs on any fixture (Z), every derived margin is indefensible.
  - An indefensible margin keeps its uncertainty: the main run records that output with `exact` (errors recorded) and claims no tolerance.
- **Applying it without judgment:** a later step reads `C/comparison_scored.json` (agrees, missing, max_abs_error, max_rel_error per pair) and A0's fetched `docking.out` (d, N_f), evaluates the formulas, and copies the margins into the main design. After the main run it checks binary, library, driver and GPU identity against the fixture run's `comparison_compute.json` (§3).

Every constant is in the rule's table. k = 2, 0.001 and 0.01 are DESIGN choices, each stated with its reason. Nothing in the rule reads a seed case's output.

## D. The fixture run

- **Design:** `fixture_design.json`, in the exact schema of `SCHEMAS.md:117–141`.
- **Arms:**
  - A0 is the published baseline: CPU standard plus reconstruction.
  - A1 is the GPU standard arm whose outputs K1–K3 compare.
  - A2 and A3 duplicate A0 and A1 with identical commands. This gives two self-agreement arms: CPU, and GPU, which matters because the GPU is the nondeterministic one.
  - The dense arm is not included. No fixture margin concerns it; eps_eval for K6/K7 is an evaluator property measured on A0–A3.
  - The commands are `megadock`/`megadock-gpu` with the run6 flags. Reconstruction is one `bash -c` loop over `decoygen` plus model assembly, because 50 `decoygen` calls exceed the 8-command limit.
- **Inputs:** the four fixtures only.
- **Outputs:** `transforms` and `scores` (regex selections of the 7-field rows of `docking.out`), `coords` (PDB columns 31–54 of `out/model_*.pdb`, natural order) and `dockq` (`eval/dockq.json`, a JSON array).
- **Metric:** the trusted wall, which is required (at least 1 metric) and is not compared.
- **Evaluator:** yes. K3, and through it K6/K7, need it. The native complexes are the evaluator's private data.
- **Comparisons:** 12, all `exact`: four outputs × {cross, CPU self, GPU self}.
  - They decide nothing used by the rule except byte identity, which is itself a recorded fact.
  - The scorer records max_abs_error and max_rel_error for `exact` comparisons too (`score_comparison.py:492–504`), so the rule gets its numbers from the trusted scorer and no agent computes one.
  - Exact checks have no margin, so they cannot bias the rule.
- **Schedule and limits:**
  - `replicates` 6 and `warmup` 1, so 7 rounds × 16 = 112 invocations.
  - `timeout_s` 1200 per arm part and evaluator `timeout_s` 900. Both are far above the expected walls and only cap a hang.
  - `budget_s` 12600, which is below 19800.
  - `order_seed` 27277, `bootstrap_seed` 27278 and `bootstrap_resamples` 1000 (unused, but required by the schema).
- **Projection.**
  - **Per invocation:** about 30 s of overhead (shakedown-m5 run20: job receipt median 8.0 s, comparison receipt median 29.5 s). On top of that come the arm walls:
    - CPU about 5–25 s, scaled by input size from run6's 9.0–14.5 s (`s07:38–41`);
    - GPU about 2–6 s;
    - the evaluator about 2–5 s (run4: 1.8–2.6 s).
  - **Evaluate stage:** about 112 × 30 s plus about 22 min of compute, roughly 78 min.
  - **Rest of the allocation:** intake, harness, the two builds plus the PINDER install, setup, anchors, the users step, fetches and scoring, about 35 min (run6's whole allocation was 2083 s, including about 10 min of jobs; `s07:214`).
  - **Expected:** about 1.9–2.2 h, or **USD 6.3–7.2** at USD 3.29/h.
  - **Worst case under the caps:** about 0.6 h + 3.5 h (`budget_s`) + 0.3 h ≈ 4.4 h, or **USD 14.5**. That is under USD 20 and inside the 6 h limit.
- **Main runs fit after:** USD 100 − 1.67 − 14.5 (worst) = USD 83.8 left. The physical card's whole plan is USD 49.48 (`s13/ASSESSMENT.md:86`), and an agreement run on four cases (about 1.5 h, about USD 5) fits before it. So the answer is yes.
- **Brief:** `FIXTURE_BRIEF.md`.
  - It holds the seed and materials addendum, written from the read text of `BRIEF_run1.md` with the file tool. No byte copy was possible, so the operator should confirm that its first 310 lines equal `BRIEF_run1.md` byte for byte.
  - It then has one section, `## Comparison request (science step s27)`.
  - That section and the view text state no margin, threshold, expected result or rule. I grepped both files for every sealed number of the design (900, 1200, 12600, 27277, 27278, 1000). The only hits outside the sealed fields are digit runs inside SHA-256 hex strings of the verbatim addendum.

## E. What each fixture result decides

- **All of M2–M4 defensible** (with M5 and M6):
  - The next step writes the main agreement design (s13 run 1: A0 and A1, the four seed cases, the same outputs) with K1 transforms `exact`, K1 coordinates `{abs: eps_xyz}`, K2 `{abs: atol, rel: rtol}` and K3 `{abs: eps_eval}`. It writes the main study design with K6/K7 `{abs: 0.01 + 2·eps_eval}`, gated by `given` on K1–K3.
  - The cost then follows s13 and the card.
- **G_T true (GPU transforms not self-reproducible on fixtures):**
  - The card's exact gate (PC:58) would very likely fail on the seed cases from GPU nondeterminism alone.
  - Relaxing it "requires new prospective plan" (PC:66). That is the owner's decision, so the next step stops with `needs_owner` before the main agreement run, rather than spending on a gate that the fixtures show a correct GPU arm cannot pass.
  - The margins M2–M4 still stand or fall by the rule.
- **Some of M2–M4 indefensible:** that comparison is recorded as `exact` with errors and reported as having no defensible tolerance, so agreement is unresolved for it.
  - Whether the acceleration and quality comparisons may still run ungated by it is the owner's decision. The card gates dense quality on agreement failure, and unresolved is not failure. So the next step returns `needs_owner` with the reasons the rule produced.
- **The fixture run fails (V0 or Z):**
  - On an infrastructure failure with no comparison data, one repeat of this exact design is justified within the remaining ceiling.
  - On a harness or evaluator defect, the next step reports it and identifies the contract or harness gap.
  - No margin is derived from a partial run.

## F. Narrowing

Unchanged: **no narrowing** (`NARROWING.md`). The fixtures are measuring instruments, not new cases. The seed's conclusions stay limited to its four cases.

## Predictions and outcomes

s26 sealed no predictions, so `outcomes.json` is `{"items": []}`. Sixteen predictions for the fixture run are sealed in `PREDICTIONS.md` and `predictions.json`.
