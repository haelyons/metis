# Result

Picks 1 · PASS 1 · on-goal cards U4 0 · U3 1 · halts: none

## Table

| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [seed·idea·1](#card-seed-idea-1) Force-field error floor for coolant MD: an enlarged C10–C50 benchmark scored against measurement | PASS 2/2 | seed | if_not | 4 | — → 5 | — → 3 | 5 | — | — → 1 | — | $941 at p_score · plan $941 · 3 GUESS |

## Frontier (listed, not produced)

None.

## Cards

<a id="card-seed-idea-1"></a>**IC-V1 · Force-field error floor for coolant MD: an enlarged C10–C50 benchmark scored against measurement.** seed pick · compute tested: yes · plan expects: not the lever · PASS

**Question.** Will graphics-card molecular simulations using Green–Kubo on C10–C50 hydrocarbons and esters rank immersion coolants' viscosity and thermal conductivity the same way measurements do?

**What is known.** Ogbomo and colleagues, in 2026, used Green–Kubo molecular dynamics to compute viscosity and thermal conductivity for eight C10–C50 molecules at 40 °C and compared with measurements [s_ogbomo_md]. Whether the error is a correctable bias or a random floor that caps ranking, and how rank agreement holds over hundreds of molecules [s_ogbomo_db].

**Hypothesis.** Green–Kubo MD with one fixed force field has a chemistry-dependent error floor near 25 percent that more molecules cannot remove [s_ogbomo_res].

**If compute is the lever.** At 120 molecules, held-out viscosity error after bias correction falls below 15 percent and rank correlation with measurement exceeds 0.9 [s_ogbomo_res].

**If not.** Held-out viscosity error stays above 25 percent and rank correlation below 0.7 at every set size, capping candidate ranking [s_ogbomo_res].

**Test.** One LAMMPS LOPLS-AA Green–Kubo protocol at 40 °C, six five-nanosecond replicas per molecule, run on 8, 24, 48 then 120 molecules from the public 835-molecule reference set, scored only against measured viscosity and thermal conductivity [s_ogbomo_db].

*Compute axis.* Benchmark molecules scored against measured viscosity and thermal conductivity: 8–120 molecules, 4 levels. Closest prior: 8 [s_ogbomo_md], beyond it.

*Restructuring.* none.

**Check first.** Repeat the published eight-molecule Green–Kubo run first: density within 4% for seven molecules and thermal conductivity over-predicted for all eight [s_ogbomo_res]. Tolerance: same bias signs for viscosity and thermal conductivity; density error within 4 percentage points of the published error; per-molecule viscosity within 20% of the reference value.

**Would not show.** Shows transport-property error only at 40 °C for pure liquids between 1 and 50 mPa·s, not blends or sold coolants. Cannot show ranking behaviour beyond 120 molecules.

*Cost.* Plans $940.98 of the $1,000 budget over 59 machine-hours, leaving $59.02. Main guess: assumed MD throughput per GPU [p], measured after $36.20 of spend; the budget is reached if it is 1.1× lower. 3 cost flags in the block.

**Judges.** Dramaturg: PASS 2/2. Decides at: $941 at p_score · plan $941 · 3 GUESS (critic: p_score computes MAPE and rank correlation over set sizes, needed to apply decision_rule).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $1,000 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-10-18 · filesystem $0.20/GiB-month [q]
Spend      p_local  Assemble the LOPLS-AA LAMMPS protocol from the public decks and validate the scoring and noise rules on synthetic Green–Kubo data using pilot/cost_and_noise_check.py  1x NVIDIA A6000 48GB $1.09/h  4 h  $4.36  l_dry need 4 h in a 4 h box
           p_bench  GPU pilot: 4 molecules with 3 replicas of 8 ns; measure throughput, Green–Kubo plateau time and replica spread  8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h  2 h  $31.84
           p_core  Benchmark 48 molecules, including the anchor eight, at the fixed protocol  8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h  19 h  $302.48
           p_ext  Extend the benchmark to 120 molecules  8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h  28 h  $445.76
           p_score  Score error distributions, held-out bias correction and rank correlation at 8, 24, 48 and 120 molecules; write the report  1x NVIDIA A6000 48GB $1.09/h  6 h  $156.54  l_score need 6 h in a 6 h box
           Planned $940.98 · unallocated $59.02 · cap $1,000
           Instead of l_ext: Stretch: 12 molecules re-run with six 15 ns replicas to separate trajectory length from set size, 8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h, 14 h, $222.88 → plan $718.10
Rests on   assumed MD throughput per GPU 250 ns/day [p] "1 x A100 GPU:      |         ns/day =    611.08" · differs: Amber pmemd.cuda rather than LAMMPS, protein in water rather than neat organic liquid, no per-step stress-tensor autocorrelation accumulation, we take 250 ns/day as a safety factor of about 2.4 under the 611 ns/day figure · measured in p_bench ($36.20 spent by then) · gate assumed MD throughput per GPU ≥ 150 in p_bench (now 250, passes; uncut plan at it $1,450.42), else drop the extension tier and re-plan with 48 molecules at 3 replicas · budget reached at 230 (1.1× lower)
           expected worst anchor viscosity error 0.25 fraction [g] rests on: the prior reports small LOPLS-AA viscosity errors for hydrocarbons and consistent under-prediction for oxygenates, so 25 percent sits mid-range of published per-molecule force-field errors · measured in p_anchor ($36.20 spent by then) · gate expected worst anchor viscosity error ≤ 0.2 in p_anchor (now 0.25, fails; uncut plan at it $940.98), else stop and report that the protocol is not trustworthy; make no ranking claim · budget not reached within 1000×
           expected replica standard error of viscosity 0.15 fraction [g] rests on: published practice that five to ten Green–Kubo replicas of a few nanoseconds give a standard error of order ten to twenty percent · measured in p_bench ($36.20 spent by then) · gate expected replica standard error of viscosity ≤ 0.2 in p_ext (now 0.15, passes; uncut plan at it $940.98), else spend the extension money on longer trajectories for the 48 core molecules instead of new molecules · budget not reached within 1000×
           false-positive rate of the rank rule 0.05 fraction [g] rests on: bootstrap rank tests at this sample size usually reject a true null about five times in a hundred · measured in p_local ($4.36 spent by then) · gate false-positive rate of the rank rule ≤ 0.08 in p_local (now 0.05, passes; uncut plan at it $940.98), else fix the scoring code before any GPU spend · budget not reached within 1000×
Scenarios  Measured throughput is half the proxy: shrink the benchmark rather than overspend → $944.66 · Replica spread too wide: buy longer runs on fewer molecules → $1,147.94 (over budget)
Buys       molecules in the full benchmark: 120 [d] · Measured throughput is half the proxy: shrink the benchmark rather than overspend: 60 · Replica spread too wide: buy longer runs on fewer molecules: 60
           trajectory nanoseconds bought: 3,840 [=] · Measured throughput is half the proxy: shrink the benchmark rather than overspend: 1,920 · Replica spread too wide: buy longer runs on fewer molecules: 4,920
           independent replica runs bought: 720 [=] · Measured throughput is half the proxy: shrink the benchmark rather than overspend: 360 · Replica spread too wide: buy longer runs on fewer molecules: 600
Flags      error (quote) at numbers.throughput_ns_day.quote: 250 does not appear in the quote "1 x A100 GPU:      |         ns/day =    611.08"; a value transformed from the page belongs in a DERIVED number
           uncut plan at the p_bench gate threshold costs $1,450.42, over budget; the plan relies on: drop the extension tier and re-plan with 48 molecules at 3 replicas
           gate in p_anchor fails at the plan's own value: expected worst anchor viscosity error is 0.25, needs ≤ 0.2; expected path: stop and report that the protocol is not trustworthy; make no ranking claim
           thin headroom: the budget is reached if assumed MD throughput per GPU is 1.1× lower
Full scale Score all 835 reference molecules at 40 °C with the same protocol: $5,104.59 = 5.1× budget = 42.5× molecules in the full benchmark · inputs 2 c, 1 p, 3 d ([p] assumed MD throughput per GPU)
           Repeat the 120-molecule benchmark at 100 °C as well: $1,467.19 = 1.47× budget = 12.2× molecules in the full benchmark · inputs 1 c, 1 p, 4 d ([p] assumed MD throughput per GPU)
Outside    local shared-machine CPU time for protocol assembly and scoring code: 20 hours · human time for setup, curation and writing: 10 hours · public reference dataset and prior's LAMMPS decks, downloaded free of charge [s_zenodo]: 1 download
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
atoms_per_mol_avg = (32 + 152) / 2 = 92 atoms
atoms_per_box = n_mol_per_box * atoms_per_mol_avg = 250 * 92 = 23000 atoms
ns_per_mol = t_eq_ns + n_replicas * t_prod_ns = 2 + 6 * 5 = 32 ns
gpu_h_per_mol = 24 * ns_per_mol / throughput_ns_day = 24 * 32 / 250 = 3.072 GPU-hour
mol_usd = gpu_h_per_mol * a100x8_usd_gpu_h = 3.072 * 1.99 = 6.11328 USD
n_mol_ext = n_mol_total - n_mol_core = 120 - 48 = 72 molecules
store_usd = gib_store * fs_usd_gib_month = 150 * 0.2 = 30 USD
ns_total = n_mol_total * ns_per_mol = 120 * 32 = 3840 ns
replica_runs = n_mol_total * n_replicas = 120 * 6 = 720 runs
l_bench.hours = ceil(24 * pilot_ns / (throughput_ns_day * n_gpus)) = ceil(24 * 150 / (250 * 8)) = 2 h
l_core.hours = ceil(24 * n_mol_core * ns_per_mol / (throughput_ns_day * n_gpus)) = ceil(24 * 48 * 32 / (250 * 8)) = 19 h
l_ext.hours = ceil(24 * n_mol_ext * ns_per_mol / (throughput_ns_day * n_gpus)) = ceil(24 * 72 * 32 / (250 * 8)) = 28 h
l_store.usd = gib_store * fs_usd_gib_month = 150 * 0.2 = 30 usd
l_rerun.usd = rerun_usd = 120 = 120 usd
l_long_traj.hours = ceil(24 * 12 * (t_eq_ns + n_replicas * 15) / (throughput_ns_day * n_gpus)) = ceil(24 * 12 * (2 + 6 * 15) / (250 * 8)) = 14 h
fs_all835 = n_ref_molecules * mol_usd = 835 * 6.11328 = 5104.59 usd
fs_two_temp = n_mol_total * mol_usd * 2 = 120 * 6.11328 * 2 = 1467.19 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:hypothesis` PARTIAL · page: "Viscosity errors are small for the pure hydrocarbons with LOPLS, but this property is consistently under-predicted for the oxygen-containing molecules; the reference ranking of the fluids is nonetheless largely preserved. Thermal conductivity is over-predicted for every molecule, by amounts that correlate with the density of aliphatic C–H bonds, compressing the reference range and misordering the fluids." · note: The source supports the qualitative claim of chemistry-dependent force-field errors in viscosity and thermal conductivity. It does not state a ~25% error floor (it reports viscosity errors from small up to 137% at 40 °C, with only four of eight molecules within 25%) and says nothing about more molecules being unable to remove the error; those parts are unsupported.
- sample 1 · `card:left_open` PARTIAL · page: "We compile a database of approximately 4,700 critically evaluated reference values for the density, viscosity, and thermal conductivity of 835 unique organic molecules in the C10–C50 range." · note: The page supports only the scale claim ('hundreds of molecules', 835-molecule reference set). It does not state that whether the error is a correctable bias or a random floor, or rank agreement at that scale, is left open; the work reports that viscosity ranking is largely preserved among eight molecules, so the 'left open' framing is the plan's gap claim, not a finding on the page.
- sample 1 · `card:limits` UNSUPPORTED · page: "Only molecules with a dynamic viscosity of approximately 1–50 mPa s at 40 °C were included, because this is the range accessible to equilibrium molecular dynamics (EMD) simulations." · note: The applicability claims ('only at 40 °C for pure liquids between 1 and 50 mPa·s, not blends or sold coolants') are factual claims about the evidence domain and the item cites no source, so they are UNSUPPORTED by the rule. (They do match the work's inclusion criteria on the page I fetched, but no source is cited here.) 'Cannot show ranking behaviour beyond 120 molecules' is plan scope and needs no source.
- sample 1 · `src:s_ogbomo_res` PARTIAL · page: "Density is reproduced to within 4% for seven of the eight molecules at 40 °C. Viscosity errors are small for the pure hydrocarbons with LOPLS, but this property is consistently under-predicted for the oxygen-containing molecules; the reference ranking of the fluids is nonetheless largely preserved. Thermal conductivity is over-predicted for every molecule, by amounts that correlate with the density of aliphatic C–H bonds, compressing the reference range and misordering the fluids." · note: The cited Spiral bitstream is the same article PDF (d6dd00260a.pdf) but returns unparseable PDF bytes; the identical text was confirmed in the published version of the same article. The quote supports the anchor tolerances and the qualitative error pattern, but not 'the predicted error floor' (no error floor is quantified) and only loosely the if_not expectation (it says viscosity ranking was largely preserved, and reports no 25%/0.7 thresholds).
- sample 1 · `num:throughput_ns_day` PARTIAL · page: "JAC_PRODUCTION_NVE - 23,558 atoms PME 2fs ... 1 x A100 GPU: | ns/day = 611.08" · note: The quoted benchmark line appears on the Amber page for the stated setting (JAC_PRODUCTION_NVE, 23,558 atoms, PME, 2 fs, one A100), but the page states 611.08 ns/day, not 250. The 250 ns/day is a disclosed proxy (safety factor ~2.4 under the page figure, Amber pmemd.cuda protein-in-water rather than LAMMPS with stress-tensor accumulation), so the assumption is not contradicted, just not the page's number. · page value 611.08
- sample 2 · `card:hypothesis` PARTIAL · page: "The MD benchmark, using a Green–Kubo protocol with quantified trajectory-length convergence, shows that the accuracy of the LOPLS-AA force field is property- and chemistry dependent." · note: The page confirms Green–Kubo MD with one fixed force field (LOPLS-AA) and chemistry-dependent transport errors that persist at convergence (viscosity under-predicted 17–38% for esters and 26–57% for ethers; thermal conductivity over-predicted +7 to +96%). But no ~25% floor is stated anywhere, and the paper explicitly says that with only eight molecules these observations 'can only be used to identify plausible explanations, rather than establish firm conclusions' — so the 'near 25 percent' figure and 'more molecules cannot remove' are the plan's own extrapolation, not page content.
- sample 2 · `card:limits` PARTIAL · page: "Only molecules with a dynamic viscosity of approximately 1–50 mPa·s at 40 °C were included, because this is the range accessible to equilibrium molecular dynamics (EMD) simulations." · note: The plan-scope limits (40 °C-only protocol; no ranking behaviour beyond 120 molecules) are the plan's own and need no source. The dataset-scope factual claims (pure liquids only, ~1–50 mPa·s, no blends) are correct per the Ogbomo paper but carry no source on this item; also note the published benchmark reported errors at both 40 °C and 100 °C, so 'only at 40 °C' holds for the plan's protocol (per test_summary), not for the prior paper.
- sample 2 · `src:s_ogbomo_res` PARTIAL · page: "Density is reproduced to within 4% for seven of the eight molecules at 40 °C. Viscosity errors are small for the pure hydrocarbons with LOPLS, but this property is consistently under-predicted for the oxygen-containing molecules; the reference ranking of the fluids is nonetheless largely preserved. Thermal conductivity is over-predicted for every molecule, by amounts that correlate with the density of aliphatic C–H bonds, compressing the reference range and misordering the fluids." · note: The quote appears verbatim in the PDF served at this bitstream URL (conclusion section; confirmed via the indexed full text of this exact URL — a direct fetch returns a binary PDF that could not be text-extracted). It fully backs the anchor tolerances and qualitatively backs a chemistry-dependent, force-field-limited error floor, but the page nowhere states the ~25% floor or the if_not thresholds (>25% error, rank correlation <0.7), and for viscosity it reports the ranking 'largely preserved' while only thermal-conductivity ranking is misordered — so 'the predicted error floor and the if_not expectation' are only partly backed.

**Critic.**
- stakes 3 · `card:limits` "Shows transport-property error only at 40 °C for pure liquids between 1 and 50 mPa·s, not blends or sold coolants. Cannot show ranking behaviour beyond 120 molecules." · Tests only pure-liquid transport; full coolant choices still depend on blends, dielectric, flash point and candidates.
- lever 4 · `plan:predictions.decision_rule` "At 120 molecules, if_lever when held-out viscosity MAPE is at most 0.15 and Spearman rank correlation is at least 0.90 for both viscosity and thermal conductivity; if_not when MAPE is at least 0.25 or rank correlation at most 0.70 at every …" · Set size 8–120 is 15x compute with force field, temperature and protocol held fixed; per-molecule SE of 0.20 vs 0.15/0.25 thresholds makes separation not fully assured.
- verifiable 5 · `card:test_summary` "One LAMMPS LOPLS-AA Green–Kubo protocol at 40 °C, six five-nanosecond replicas per molecule, run on 8, 24, 48 then 120 molecules from the public 835-molecule reference set, scored only against measured viscosity and thermal conductivity [s_…" · Measured reference values are independent; anchor reproduces published eight-molecule run within tolerance.
- open 5 · `card:left_open` "Whether the error is a correctable bias or a random floor that caps ranking, and how rank agreement holds over hundreds of molecules [s_ogbomo_db]." · Prior covers eight molecules; gap over rank agreement through 120 and beyond is explicitly stated.
- reshape 1 · `card:sequential_part` "One molecule needs equilibration, then six runs, then averaging — three steps; different molecules never wait on each other." · Only independent molecules run side by side; no sequential dependency is removed.
- baseline NA · `card:method` "none" · Restructuring.method is none, so baseline comparison is not applicable.

**Producer says (not judged).** expected if_not (Published LOPLS-AA Green–Kubo runs already show chemistry-dependent errors of tens of percent that more sampling cannot remove [s_ogbomo_res].); compute_tested yes (The test varies the number of benchmark molecules from 8 to 120, which is exactly the work more parallel GPUs buy; per-molecule trajectory length is held fixed.); decides partly; searched yes.

**Annotations.**
- cost record repaired: 2 expression(s) rewritten
- quote at numbers.throughput_ns_day.quote: 250 does not appear in the quote "1 x A100 GPU:      |         ns/day =    611.08"; a value transformed from the page belongs in a DERIVED number
- uncut plan at the p_bench gate threshold costs $1,450.42, over budget; the plan relies on: drop the extension tier and re-plan with 48 molecules at 3 replicas
- gate in p_anchor fails at the plan's own value: expected worst anchor viscosity error is 0.25, needs ≤ 0.2; expected path: stop and report that the protocol is not trustworthy; make no ranking claim
- thin headroom: the budget is reached if assumed MD throughput per GPU is 1.1× lower
- prior_max_level 8 is not in the quote of s_ogbomo_md
- hypothesis: a sentence of 21 words
- predictions.if_lever: a sentence of 21 words
- test_summary: a sentence of 36 words
- novelty.closest_prior: a sentence of 22 words
- novelty.left_open: a sentence of 24 words
- anchor.what: a sentence of 21 words
- question: rewritten by the field repair
- novelty.closest_prior: rewritten by the field repair
- card field question still fails: coined codes: C10, C50
- card field novelty.closest_prior still fails: coined codes: C10, C50
- dramaturg findings failed G-find after a resample; decided as returned
- prose over 240 words (265)

**Root question (null).** generative pipeline for discovery of single phase immersion coolants

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/immersion-coolants/20261018-0342-card-2/out/work/seed-1/seed/idea/506d69e1/producer.md)

## Inventory

| Option | Title | Distance | Cluster | Total | Status | Reason |
|---|---|---|---|---|---|---|

## Log

```
pool: 0 candidate cluster(s); picked 0
seed:idea:seed: G-plan repair: parse at lines.l_dry.need: unexpected ";" in "time box; work inside not estimated"; parse at lines.l_score.need: unexpected ";" in "time box; analysis work not estimated"
seed:idea:seed: cost record repaired: 2 expression(s) rewritten
seed:idea:seed: quote at numbers.throughput_ns_day.quote: 250 does not appear in the quote "1 x A100 GPU:      |         ns/day =    611.08"; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: uncut plan at the p_bench gate threshold costs $1,450.42, over budget; the plan relies on: drop the extension tier and re-plan with 48 molecules at 3 replicas
seed:idea:seed: gate in p_anchor fails at the plan's own value: expected worst anchor viscosity error is 0.25, needs ≤ 0.2; expected path: stop and report that the protocol is not trustworthy; make no ranking claim
seed:idea:seed: thin headroom: the budget is reached if assumed MD throughput per GPU is 1.1× lower
seed:idea:seed: prior_max_level 8 is not in the quote of s_ogbomo_md
seed:idea:seed: hypothesis: a sentence of 21 words
seed:idea:seed: predictions.if_lever: a sentence of 21 words
seed:idea:seed: test_summary: a sentence of 36 words
seed:idea:seed: novelty.closest_prior: a sentence of 22 words
seed:idea:seed: novelty.left_open: a sentence of 24 words
seed:idea:seed: anchor.what: a sentence of 21 words
seed:idea:seed: card fields failing: question (coined codes: C10, C50); novelty.closest_prior (coined codes: C10, C50)
seed:idea:seed: question: rewritten by the field repair
seed:idea:seed: novelty.closest_prior: rewritten by the field repair
seed:idea:seed: card field question still fails: coined codes: C10, C50
seed:idea:seed: card field novelty.closest_prior still fails: coined codes: C10, C50
seed:idea:seed: dramaturg: degenerate: card:question
seed:idea:seed: dramaturg (resample): agent returned null
seed:idea:seed: dramaturg findings failed G-find after a resample; decided as returned
seed:idea:seed: prose over 240 words (265)
```
## Measured (added 2026-10-20 by the operator; not pipeline output)

The card's load-bearing number, assumed MD throughput per GPU (250 ns/day, PROXY from the Amber JAC benchmark under a 2.4 safety factor), was measured on 2026-10-20 in `../20261020-1020-measure` (latent_skeptic run m3). The card record is untouched: `result.json` sha256 1b461dfd…; ledger rows 5 and 6 in `experiments/_meta/LEDGER.jsonl`; machine form in `../20261020-1020-measure/out/CARD_WRITEBACK_m3.json`.

**What was run.** The card's own p_bench protocol on one molecule: LOPLS-AA, 250 nonylcyclohexane molecules (11,250 atoms), 313.15 K, 2 fs, PPPM, SHAKE, pressure tensor and heat flux every 5 steps. One A100 SXM4 40 GB (the card's GPU), LAMMPS 29Aug2024 compiled on the box with the GPU package (CUDA sm_80, mixed precision), one process, no MPI, no OpenMP threads. Lambda cost USD 3.26 over two launches.

**Result.**

| Card value | Measured | Record |
|---|---|---|
| throughput 250 ns/day [p], band 100 to 625 | 12.6 ns/day as written; 18.2 pressure tensor only; 18.4 no sampling | E3 |
| p_bench gate: throughput ≥ 150 | FAIL (11.9× below) | E3b |
| plan $940.98; headroom "budget reached if 1.1× lower" | 19.8× lower; plan at the measured rate about $18,700 (the storage line was scaled too, so slightly overstated); cap $1,000 | E3c |
| scenario "throughput half the proxy" (125 ns/day) → $944.66 | the measured rate is 10× below that scenario | |
| anchor: density within 4% of 0.805 g/cm3 | 0.795 g/cm3 (−1.2%), within band; 300 ps NPT, last 100 ps averaged | E2 |
| anchor: eight-molecule Green–Kubo repeat (bias signs, viscosity within 20%) | not measured: one molecule, no viscosity or thermal conductivity computed | |
| l_dry 4 h to build LAMMPS and dry-run | engine compiled on the box in about 2 min; box packed in 12 s | E7 |

**The card's own fallback does not rescue it at this rate.** The gate's else-branch is "drop the extension tier and re-plan with 48 molecules at 3 replicas". By the card's derivations (ns_per_mol = 2 + 3 × 5 = 17; gpu_h_per_mol = 24 × 17 / throughput; $1.99 per GPU-hour), the 48 core molecules alone cost about $3,100 at 12.6 ns/day and about $2,100 at 18.4 ns/day, before the anchor and scoring phases. Operator arithmetic on the card's formulas, not a pipeline evaluation.

**Caveat that bounds the reading.** The 12.6 ns/day is CPU-bound, not GPU-bound: bonded forces and SHAKE took 63% of wall time on one CPU thread while the GPU's pair work took 5% (post triage, reader: reproduces). On a multi-rank or KOKKOS build the same protocol could run several times faster; that was not measured. The number therefore refutes the card's figure for the engine the card named (LAMMPS, GPU package, a per-GPU rate) and sets a floor, not a ceiling, for this hardware. In atom-steps per second the gap to the Amber proxy is 50 to 100×, far beyond the 2.4 safety factor. Two further engine facts: the equilibration deck does not run under pppm/gpu as written (fix balance refused; its three load-balancing lines were removed), and the per-step sampling costs 32% of throughput (the pressure tensor alone about 1%, the heat flux the rest).

**Pipeline verdict.** The dramaturg PASS 2/2 and the critic scores (lever 4, verifiable 5, open 5, reshape 1, stakes 3) judged citations and design; they stand as made and said nothing about whether 250 was right. The pipeline's own flags pointed the right way and were under-weighted: "thin headroom: the budget is reached if assumed MD throughput per GPU is 1.1× lower"; "uncut plan at the p_bench gate threshold costs $1,450.42, over budget"; the dramaturg's PARTIAL on num:throughput_ns_day (the page says 611.08, not 250). As a plan, the card fails at p_bench by its own rule, and its fallback is over the cap. The scientific question (an error floor near 25%, expected if_not) is untouched: no viscosity or thermal conductivity was computed. Status: PASS as a citation-checked design, FAIL as a priced plan. The re-plan branch is postponed by the owner (2026-10-20).
