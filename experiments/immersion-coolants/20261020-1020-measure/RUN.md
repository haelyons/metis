# immersion-coolants · measure · 20261020-1020

Kind: measure. The throughput number of the V1 card's `p_bench` phase, run as a latent_skeptic run, so the card's
load-bearing proxy is resolved by a measurement on the card's own protocol and lands beside the card. Third measure run
in metis (m1, m2 in `../../reshape-test/`). Tag: m3.

## Why this card (operator's pick, 2026-10-20)

The owner asked to carry the immersion-coolant work to experiment if it passed, or to take up a possible collaborator's
molecular pose estimation. Both coolant cards passed 2/2 (V3 at `../20261018-0342-card`, V1 at `../20261018-0342-card-2`).
V1 is picked: its engine (LAMMPS), force field, builder and decks are committed public files already in this repo
(`../../coolant-proxy/data/MD-ML-thermophysical`, Zenodo 10.5281/zenodo.21824121), and the coolant pilot (`../../coolant-proxy`)
halted exactly at this card's first step (box packing), so the measure also closes that halt. V3 holds GROMACS fixed
and needs LOPLS-AA ester topologies the repo does not have. Molecular pose estimation has no card yet; the phrase has
two readings (ligand binding-pose prediction; cryo-EM particle pose) and the collaborator's question is not in hand, so a
card run on a guessed seed would measure the wrong thing. Proposed next step for it in the closing report.

## Source card

- Run: `../20261018-0342-card-2`, seed `../seeds/V1.json`, producer MiMo v2.6 Pro. Dramaturg PASS 2/2; critic lever 4,
  verifiable 5, open 5, reshape 1, stakes 3. Plan USD 941, decides at `p_score`.
- Record: `../20261018-0342-card-2/out/result.json` sha256 `1b461dfd41deda92aa7a9a439f1d21ec51aa784eab1dc463f2e7195fd4153e29`;
  producer reply sha256 `9c880117e8899aeff6d1999da3fe7e81309317a76dc367b07ee445d6dcb71812`.
- Number under test: `throughput_ns_day`, PROXY 250 ns/day per GPU (source: Amber pmemd.cuda JAC benchmark, 23,558
  atoms, one A100, 611.08 ns/day; the card applies "a safety factor of about 2.4"), `measured_by: p_bench`.
- Card gate at `p_bench`: `throughput_ns_day >= 150`, else "drop the extension tier and re-plan with 48 molecules at 3
  replicas". Every cost line divides by this number.
- Card anchor (first part, cheap here): density within 4% of the reference at 40 C.
- Not measured here: `eta_se_frac` (needs 3 replicas x 8 ns), `eta_anchor_err` (8 molecules), everything in p_core and
  beyond.

## Adjustments decided by the operator before any agent ran (departures of record; see out/diff.json)

1. One molecule, not the pilot's four: nonylcyclohexane (`mol_00557`, C15H30, 45 atoms, reference density 0.805 g/cm3
   at 40 C, Experimental, from the committed `dataset.csv`). 250 molecules (the card's held_fixed) = 11,250 atoms.
2. Packing density 0.3 g/cm3 (the dataset README's own value; the pilot's gate chose 0.75 and Packmol could not pack).
   Box built locally before launch with the committed builder, in a fresh micromamba env matching `environment.yml`
   (rdkit 2025.09.5, packmol), then read with a zero-step `read_data` in LAMMPS 2024.08.29 (CPU). The built files are
   committed inputs with hashes.
3. Equilibration shortened from the deck's 1 ns NPT to 0.5 ns at 2 fs (the paper says density plateaus within about
   0.2 ns; the card holds 2 fs fixed; the deck default is 1 fs). Deck structure unchanged; only `-var` values.
4. Three production variants of 200 ps each: (a) the deck as written (pressure tensor and heat flux every 5 steps),
   (b) pressure tensor only, (c) no per-step sampling. (a) is the card's protocol and decides E3; (b) and (c) price the
   sampling and stand in for (a) if the GPU pair style refuses the centroid stress compute.
5. LAMMPS from conda-forge (CUDA build, the pilot's pinned spec or the nearest available) through micromamba on the
   box; nothing else installed. If the install fails: RUN_VALID false, exit 2, no fallback.
6. Two launches pre-authorised within one USD 10 cap (fuzzy calibration limit).

## Pipeline

As m2: latent_skeptic ff9a63c files copied read-only and verified identical; design mode not run (the card is the
design; `out/design.json` compiled by hand); triage, gate, build, post run as workflows; `frozen/` launcher adapted at
declared points per launch. Every action by actor in `INTERVENTIONS.md`. Hashes in `out/INPUT_HASHES.txt`.

## Budget (owner rules of 2026-10-20)

Project cap USD 500 (spent USD 2.60). Calibration runs fuzzy about USD 10. This run: hard cap USD 10, at most two
launches, `gpu_1x_a100_sxm4` at USD 1.99/h if it has capacity (the card's GPU), else the cheapest single GPU with
capacity, recorded. Expected 0.5 to 0.8 h per launch.

## Sequence

1. `SEALED_PREDICTIONS.md` hashed before anything runs. 2. Local box build (E1) and its hashes. 3. QUESTION.md,
design.json, diff.json. 4. Triage workflow. 5. design_record.json, GATE_COMMIT.md, EXEC_NOTE.md. 6. Build workflow.
7. Launch. 8. Post workflow. 9. Ledger row.

Models: every agent pinned sonnet or opus. None on Fable.

## Log

- 10:20Z run dir made; pipeline files identical to m2's (dut ff9a63c); committed data copied from the pilot and verified
  against its hash table (8 files). Local micromamba env creation started.
- 10:27Z pre-launch build (E1 part 1): the committed builder at 0.3 g/cm3, seed 61453, 250 molecules: exit 0 in 12 s;
  11,250 atoms; box 66.28 A; net charge per molecule 0.0; parameter source "L-OPLS hydrocarbons"; 4 atom types, 13
  dihedral types (hybrid opls multi/harmonic). Files and hashes under `data/box_mol00557_n250_d0.30_s61453/`,
  appended to `out/INPUT_HASHES.txt`. Builder log `out/prelaunch_build_mol00557.log`. (The pilot's packs at 0.75
  g/cm3 took 20 to 41 min each and all failed; the density, not the builder, was the halt.)
- Launcher copies made: `lambda_run_m3.sh` (declared points: remote dir m3_run, payload incl. `scp -r data`, bootstrap
  name, fetch paths; `bash -n` ok), `remote_run_m3.sh` (cd line only).
- 10:29Z E1 part 2: zero-step `read_data` of the built box in LAMMPS 2024.08.29 (CPU build, conda-forge, pilot's pin) with
  SHAKE at 2 fs: exit 0, 11,250 atoms, density 0.29999997 g/cm3, no ERROR lines (`out/prelaunch_read0_mol00557.out`).
  E1 PASS. conda-forge still carries the pilot's pinned CUDA build `lammps=2024.08.29=cuda126_py310_h894d002_nompi_2`
  (and builds _3, _5, _6 of the same string). Triage launched.
- 10:31Z triage wf_fb02fd5d-a4e FAILED: login expired on every model agent (reader also absent); its empty return is kept as a failure record and not used. Owner re-logged in; triage relaunched.
- 10:33Z triage wf_0cc4d978-d33 (35 s): reader ran, grounding unauditable (pre-launch artifacts confirmed; builder exit code in no artifact, now written as out/prelaunch_build_mol00557.json); skeptics NEEDS_RUN x2; run-queue: timed GPU dry run with a Performance-vs-wall-clock check. 
- 10:40Z GATE_COMMIT.md and EXEC_NOTE.md written and hashed; build launched.
- 11:22Z build 1 (wf_2975691d-aa9, 44 min) STOPPED by design: GateCheck 19/19; run_m3.py 3,072 lines, onbox_m3.sh 172 lines; selftest 282/283, the one failure being the directive's own contradiction (I7 planted 1.3021e10 vs formula 1.3021e7; the gate's arithmetic was wrong by 1,000x). Return: out/build1_m3_wf_2975691d-aa9_STOPPED_return.json; files archived under out/build1_stopped/.
- 11:24Z gate addendum A2 to A5 (formula binds, planted 1.3021e7; builder readings accepted); EXEC_NOTE item 9 corrected; build 2 launched.
- 11:45Z build 2 (wf_4df87803-b95, 15 min) STOPPED by design: the pinned conda-forge CUDA build has the GPU package off (KOKKOS instead; feedstock recipe read for 2024-2026); selftest 313/313; no spend. The pilot's RUN_LOG step 4d had reported this; the gate missed it (operator error, booked).
- 11:48Z gate addendum A7 to A9: LAMMPS stable_29Aug2024 compiled from source on the box with the GPU package (sm_80), mixed precision labelled; REMOTE_TIMEOUT 7,200 s; EXEC_NOTE item 11 rewritten; build 3 launched.
- 11:57Z build 3 (wf_881fe8ab-bfb, 21 min): ready, selftest 365/365; flagged the directive's stale engine label. Addendum A10/A11; build 4 launched for the label constant.
- 12:01Z build 4 (wf_5b14e871-632, 3.5 min): ready; run_m3.py 3,781 lines (40d7e909…), onbox_m3.sh 266 lines (b6689ce4…, identical to build 3); selftest 367/367 under the operator's run (out/selftest_m3_operator.log). Four builds in all; builds 1 to 3 archived under out/.
- 12:05Z LAUNCH 1 (of at most 2): `REMOTE_TIMEOUT=7200 PRICE_USD_PER_HOUR=1.99 BUDGET_LEFT_USD=5 INSTANCE_TYPE=gpu_1x_a100_sxm4 setsid nohup bash lambda_run_m3.sh gpu_1x_a100_sxm4 us-east-1 onbox_m3.sh results_m3`, log `out/launcher_m3.log`; backstop 9,000 s. Expected: compile 10 to 25 min, MD 15 to 40 min, USD 1.5 to 3.
- 12:14Z LAUNCH 1 ended by the guard, as designed. Box 7fd3a46cdc944565ad8bb8617ce6e206 (A100 SXM4, us-east-1):
  compile 113 s (cmake 3.22.1 from the image, g++ 11.4, nvcc 12.8, KISS FFT since fftw3.h is absent; `lmp -h`: GPU
  package, CUDA, mixed precision; KSPACE, MOLECULE, RIGID, EXTRA-COMPUTE, OPENMP); engine check pass; timed dry run of
  the deck as written on the dilute box: RUNS_AGREE, Performance 13.52 / 13.38 ns/day on two 1,000-step runs (78
  steps/s, 880 katom-steps/s), wall-clock within 5%. The cost/time guard then stopped before the box copy: 875,000
  remaining steps at 78 steps/s need 10,558 s against 7,009 s left. Exit 3, run_valid false. API: launch 12:05:10Z,
  terminate 12:14:09Z, 0.15 h, USD 0.30. Outputs archived under `out/launch1/`.
  **Finding of record (not E3):** 13.5 ns/day on the deck as written is 18.5x below the card's 250 ns/day proxy and
  11x below its own gate, on a dilute box; the dense liquid will not be faster.
- 12:15Z gate addenda A12 to A14: protocol shortened to 450,000 steps (10 ps relax, 100 ps NVT, 300 ps NPT with the
  density mean over its last 100 ps, 100 ps deform; 20 ps + 100 ps per production variant), window 9,000 s, launch 2
  authorised; EXEC_NOTE item 2 and caps revised; build 5 launched.
- 12:27Z build 5 (wf_4759c384-967, 12 min): run_m3.py 3,866 lines (f395a4e9…), onbox_m3.sh 266 lines (8a2af63d…); selftest 383/383 under the operator's run. Five builds in all (two stopped on gate errors, one on an engine fact, one for a label, one for lengths); archives under out/build*/.
- 12:28Z LAUNCH 2 (of 2 authorised): same command with REMOTE_TIMEOUT=9000; log out/launcher_m3.log (launch 1's log moved to out/launch1/). Backstop 10,800 s. Expected compile 2 min, MD 450,000 steps at 78 to 300 steps/s: 25 to 95 min; USD 1 to 4.
- 12:41Z launch 2 progress (ssh, operator): box 3ecfff8ae8444d51aecdbbb8d8b0bf01, ip 129.213.82.194; compile 2 min
  (KISS FFT, image cmake); engine check pass; dry run RUNS; box copy ok; equilibration attempt 1 stopped on
  "ERROR: Cannot currently use pppm/gpu with fix balance. (src/GPU/pppm_gpu.cpp:118)"; the A6 fallback applied listed
  edit 3 (the deck's comm_style tiled / balance rcb / fix load_balance lines deleted in a recorded copy) and attempt 2
  is running; guard "go" with 6,844 s allowed. Finding of record: the dataset's equilibration deck cannot run under
  pppm/gpu as written; its MPI load balancing must be removed for the GPU package.
- 13:01Z launch 2 progress (ssh): equilibration attempt 2 running; push-off 20,000 steps at 0.5 fs: 104.9 steps/s
  (4.53 ns/day at that step); NVT settle 50,000 steps: 110.3 steps/s = 19.05 ns/day at 2 fs, 1.24 Matom-steps/s, with
  no per-step sampling. NPT at step 35,000: density 0.7915 g/cm3 (reference 0.805), temperature 312 K. The pure-MD rate
  of this GPU-package build on one process is itself about 13x below the card's 250 ns/day; the production variants
  will show the sampling cost on top. Projected DONE about 13:55Z, about 1.4 h billed.
- 13:35Z launch 2 progress (ssh): equilibration attempt 2 finished 13:24:00Z (2,816 s for 280,000 steps incl.
  minimisation): NPT 150,000 steps at 91.3 steps/s (15.78 ns/day at liquid density), deform at 101 steps/s; NPT
  mean density over the last 100 ps **0.79503 g/cm3** (reference 0.805: -1.24%, inside the 4% band); final density
  0.795028 after deform. Run a (deck as written) started 13:24:00Z; guard go, 5,074 s allowed.
- 13:58Z LAUNCH 2 DONE rc=0, every stage finished; fetch (try 1); teardown accepted. API: launch 12:28:32Z, terminate
  13:57:47Z, 1.487 h, USD 2.96. **Lambda total for the run USD 3.26** (launch 1 USD 0.30 + launch 2 USD 2.96);
  project USD 5.86 of 500.
- Records (36, `results_m3/out/`), run_valid true. E1 PASS (parts on box; full record local); E2 WITHIN_BAND: density
  0.79503 g/cm3 vs 0.805 (-1.24%), drift 0.0047 per 100 ps (not drifting); **E3 REFUTED_BELOW: 12.600 ns/day** on the
  deck as written (72.9 steps/s, 820 katom-steps/s; card proxy 250, 19.8x); E3b gate FAIL (12.6 < 150): the card's own
  text applies, "drop the extension tier and re-plan with 48 molecules at 3 replicas"; E3c plan re-priced USD
  18,670.63 (card USD 941; cap USD 1,000); E4 pressure-only 18.185 ns/day (1.443x); E5 no-sampling 18.426 ns/day
  (1.462x, 1.20 Matom-steps/s); E6 RUNS; E7 compile about 115 s; E8 PASS (313.6 / 313.6 / 311.7 K, no error lines).
  R1 RUNS_AGREE (Performance line vs wall-clock 0.02%); I1 to I10 PASS; edit 3 APPLIED (pppm/gpu refuses fix balance).
- Ledger row appended (`../../_meta/LEDGER.jsonl`, row 5). Card write-back `out/CARD_WRITEBACK_m3.json`. Sealed
  predictions scored `out/PREDICTIONS_SCORED.md` (Brier 0.174 over 9; held 6, did not occur 3).
- 14:05Z post mode launched.
- 14:16Z post done (wf_890f436a-e4f, 39 agents, 10 min, no failures): GateCheck 19/19; 8 elicited questions; top 3
  triaged with the isolated reader running (grounding "reproduces" on all three). TAKEAWAYS_m3.md written in the run
  dir; gates on the text above the raw-samples heading: 1.1 codes/1000 words, 0 unscoped sentences (writer's run;
  operator's run agrees). Central caveat from the post: the timed run is CPU-bound (bonded forces and SHAKE 63% of
  wall time on one thread; GPU pair work 5%), so 12.6 ns/day is this build's rate, not an upper bound for an A100.
- Caveats appended to the ledger (row 6). Hashes of all outputs in `out/SEALS.txt`.
- Close: Lambda USD 3.26 (two launches, 1.64 h), 0 instances; project total USD 5.86 of 500. Claude usage: triage 4+6
  (one failed on login) agents, build 2 x 5, post 39. Operator actions vs pipeline actions: `INTERVENTIONS.md`.
