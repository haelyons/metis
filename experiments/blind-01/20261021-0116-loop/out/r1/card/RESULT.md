# Result

Picks 1 · PASS 1 · on-goal cards U4 0 · U3 1 · halts: none

## Table

| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [seed·idea·1](#card-seed-idea-1) Motif calls emitted for Capsida NR001–NR005 and Lir Starfish binding-assay readouts | PASS 2/2 | seed | if_not | 3 | — → 5 | — → 3 | 5 | — | — → 1 | — | $507 at p3_score · plan $507 · 2 GUESS |

## Frontier (listed, not produced)

None.

## Cards

<a id="card-seed-idea-1"></a>**V3 · Motif calls emitted for Capsida NR001–NR005 and Lir Starfish binding-assay readouts.** seed pick · compute tested: yes · plan expects: not the lever · PASS

**Question.** Can computed capsid–receptor binding calls for ALPL, AAVR and LRP6 reproduce published bind/no-bind readouts with interfaces at the threefold axis?

**What is known.** Shay and colleagues in 2024 ran five AlphaFold-Multimer models per peptide and used cryo-ET to map where LRP6 and IL3 bind engineered capsids, with SPR binding labels [s_shay_af]. Whether hundreds of pose and seed runs improve bind/no-bind agreement with threefold-axis geometry across a full capsid-by-receptor grid remains untested [s_shay_af].

**Hypothesis.** Pairs that bind in plate- and bead-based assays share threefold-axis or insert-loop engagement geometry, so pose enumeration recovers published bind/no-bind labels [s_aavr_struct].

**If compute is the lever.** Balanced accuracy 0.80 at 432 runs versus 0.55 at 54, with five of six known binders within 5 Å of published sites.

**If not.** Accuracy moves under 0.05 between 54 and 432 runs and at most three of six binders reach published sites; extra runs resample the wrong basin.

**Test.** Thirty-six capsid–receptor pairs run docking, three AlphaFold-Multimer seeds, two 5-ns MD relaxations; calls and threefold-site geometry scored on published labels; parallel wall-clock versus serial one-GPU and independent-copy baselines.

*Compute axis.* Independent capsid–receptor model runs (docking, AlphaFold-Multimer, MD relaxation) the answer needs: 54–432 model runs, 3 levels. Closest prior: 10 [s_shay_af], beyond it.

*Restructuring.* none.

**Check first.** Redocking AAVR-PKD2 onto AAV2 must place it beside the threefold spike matching PDB 6IHB contacts; serial and parallel pilots must match calls. Tolerance: >=50% contact overlap at the published 4.5 Å cutoff or interface backbone RMSD <=5 Å; serial versus parallel top-pose RMSD <=2 Å with identical bind/no-bind calls.

**Would not show.** Binding-call agreement and interface geometry only; no transcytosis or affinity. Public labels cover 13 of 36 pairs; NR001–NR005 and Starfish assays are proprietary.

*Cost.* Plans $506.83 of the $1,000 budget over 40 machine-hours, leaving $493.17. Main guess: GROMACS throughput on one A100 [p], measured after $107.46 of spend; the budget is reached if it is 4.5× lower.

**Judges.** Dramaturg: PASS 2/2. Decides at: $507 at p3_score · plan $507 · 2 GUESS (critic: p3 scores 54/216/432 balanced accuracy and site recovery, enabling the 432-versus-54 decision rule).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $1,000 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-10-21 · filesystem $0.20/GiB-month [q]
Spend      p0_setup  Install ColabFold, GROMACS and LightDock; fetch capsid and receptor structures and sequences (PDB 6IHB, 1LP3, AAV9 and PHP.eB capsids, ALPL, AAVR PKD1/PKD2, LRP6 E1E2/E3E4, LRP5, LY6A); assemble AAV9-X1.1 and CAP-Mac from Shay 2024 Table 1; run the anchor redock and the LRP6 domain check.  1x NVIDIA A100 SXM 40GB $1.99/h  6 h  $11.94  l_setup need 4 h in a 6 h box
           p1_pilot  Run the 54-run pilot (3 capsids x 3 receptors) on 8x A100 and measure af2_h_per_run, md_ns_per_day_a100, aux_h_per_pair and seed-to-seed SD of calls.  8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h  6 h  $95.52  l_pilot need 4.91 h in a 6 h box
           p2_main  Run the 216-run main grid on 8x A100; emit the plate-layout call table and bead-panel CSV with bind/no-bind, score, interface residues, distance to nearest threefold axis and site class.  8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h  24 h  $391.41  l_main need 19.6 h in a 24 h box
           p3_score  Score balanced accuracy and site recovery at nested run levels 54/216/432 by subsampling runs; rank binding-positive pairs; write the ranked candidate list and the serial-versus-parallel comparison.  1x NVIDIA A100 SXM 40GB $1.99/h  4 h  $7.96  l_score need 2 h in a 4 h box
           p4_stretch  Optional expansion to 432 model runs and re-scoring  8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h  24 h [d]  $382.08  time box; need 19.6 h (margin 1.22×)  optional
           Planned $506.83 · unallocated $493.17 · with options $888.91 · cap $1,000
           Instead of l_main: Fallback main grid with one AlphaFold-Multimer seed per pair and docking poses filling the rest, 8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h, 16 h, $254.72 → plan $379.47
           Instead of l_main: Fallback main grid on 80 GB H100 GPUs if AlphaFold-Multimer OOMs at 40 GB, 8x NVIDIA H100 SXM 80GB 8×$3.99=$31.92/h, 12 h, $383.04 → plan $507.79
Rests on   GROMACS throughput on one A100 129 ns_per_day [p] "a protein in explicit water (170,320 atoms) ... | A100 | 267.5 | 691.7 | 265.8 | 129.1 | 38.8 | 23.2 |" · differs: our system is a docked capsid–receptor complex in explicit solvent, roughly 120k–180k atoms, Lambda A100 SXM 40 GB · measured in p1_pilot ($107.46 spent by then) · budget reached at 28.8 (4.5× lower) · box overflows at 1.5×
           Wall-clock hours for one AlphaFold-Multimer run on one A100 0.5 GPU_h_per_run [p] "Prediction time for a structure of N residues is roughly (N/30)*(N/30) seconds for an Nvidia A40 GPU." · differs: monomer timing formula, not a 750–1000-residue hetero-multimer with 5 models and up to 20 recycles, Lambda A100 SXM 40 GB instead of an A40 · measured in p1_pilot ($107.46 spent by then) · gate Wall-clock hours for one AlphaFold-Multimer run on one A100 ≤ 1 in p1_pilot (now 0.5, passes; uncut plan at it $554.04), else take the docking-plus-MD fallback line with one AlphaFold-Multimer seed per pair, or move the grid to 12 pairs · budget reached at 2.66 (5.3× higher) · box overflows at 1.6×
           Docking job, MSAs, scoring and I/O per pair 1 GPU_h_per_pair [g] rests on: one rigid-body docking run of a capsid patch plus ectodomain, MSA generation and scoring typically fills about an hour of instance time per pair; no benchmark was run in this session · measured in p1_pilot ($107.46 spent by then) · budget reached at 7.48 (7.5× higher) · box overflows at 2.0×
           Shared filesystem footprint 200 GiB [g] rests on: structures, MSAs, AlphaFold models and 72 short explicit-solvent trajectories of about 170k-atom systems; each 5-ns trajectory with 10-ps frames is a few GiB · measured in p2_main ($498.87 spent by then) · budget reached at 10,800 (54× higher)
           gate Contact overlap required on the anchor redock ≥ 0.5 in p0_setup (now 0.5, passes; uncut plan at it $506.83), else retune the docking box or switch pose generation to AlphaFold-Multimer only before the main spend
Scenarios  AlphaFold-Multimer runs twice as slow as proxied → $554.04 · MD at H100-class throughput instead of the A100 proxy → $506.83
Buys       Model runs at the main level: 216 [=] · AlphaFold-Multimer runs twice as slow as proxied: 216 · MD at H100-class throughput instead of the A100 proxy: 216
           Capsid–receptor pairs: 36 [=] · AlphaFold-Multimer runs twice as slow as proxied: 36 · MD at H100-class throughput instead of the A100 proxy: 36
           Reference pairs with published bind/no-bind labels: 13 [d] · AlphaFold-Multimer runs twice as slow as proxied: 13 · MD at H100-class throughput instead of the A100 proxy: 13
           Reference binding-positive pairs: 6 [d] · AlphaFold-Multimer runs twice as slow as proxied: 6 · MD at H100-class throughput instead of the A100 proxy: 6
Flags      error (gate_ref) at phases.p4_stretch.gate.on: "seed_sd_calls" is not a number id
           error (quote) at numbers.af2_h_per_run.quote: 0.5 does not appear in the quote "Prediction time for a structure of N residues is roughly (N/30)*(N/30) seconds for an Nvidia A40 GPU."; a value transformed from the page belongs in a DERIVED number
           error (quote) at numbers.md_ns_per_day_a100.quote: 129 does not appear in the quote "a protein in explicit water (170,320 atoms) ... | A100 | 267.5 | 691.7 | 265.8 | 129.1 | 38.8 | 23.2 |"; a value transformed from the page belongs in a DERIVED number
Full scale 100-ns MD on both top poses of all 36 pairs (7,200 ns total) for converged interface geometry: $2,665.67 = 2.67× budget · inputs 1 d, 1 p ([p] GROMACS throughput on one A100)
           12 capsids by 12 receptors at stretch depth (144 pairs x 12 model runs): $2,499.07 = 2.5× budget · inputs 6 d, 1 g, 2 p ([g] Docking job, MSAs, scoring and I/O per pair; [p] GROMACS throughput on one A100; [p] Wall-clock hours for one AlphaFold-Multimer run on one A100)
Outside    Scientist time to define the capsid and receptor panel, run the pipeline and adjudicate calls: 40 hours · Optional commercial plate- and bead-based binding assays to replace the public proxy labels: 15000 USD · Shared 4-core local machine used for planning (no GPU runs executed there): 1 machine · Public structure and sequence downloads (PDB, UniProt, Shay 2024 Table 1): 0 USD
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
n_pairs = n_capsids*n_receptors = 6 * 6 = 36 pairs
runs_main = n_pairs*jobs_per_pair = 36 * 6 = 216 model runs
runs_stretch = n_pairs*n_stretch_jobs_per_pair = 36 * 12 = 432 model runs
n_pilot_pairs = n_pilot_capsids*n_pilot_receptors = 3 * 3 = 9 pairs
runs_pilot = n_pilot_pairs*jobs_per_pair = 9 * 6 = 54 model runs
md_h_per_run = md_ns_per_run*24/md_ns_per_day_a100 = 5 * 24 / 129 = 0.930233 GPU_h_per_run
gpu_h_per_pair = af2_seeds_per_pair*af2_h_per_run+md_runs_per_pair*md_h_per_run+aux_h_per_pair = 3 * 0.5 + 2 * 0.930233 + 1 = 4.36047 GPU_h_per_pair
gpu_h_per_job = gpu_h_per_pair/jobs_per_pair = 4.36047 / 6 = 0.726744 GPU_h_per_run
gpu_h_pilot = n_pilot_pairs*gpu_h_per_pair = 9 * 4.36047 = 39.2442 GPU_h
gpu_h_main = n_pairs*gpu_h_per_pair = 36 * 4.36047 = 156.977 GPU_h
gpu_h_stretch_extra = (runs_stretch-runs_main)*gpu_h_per_job = (432 - 216) * 0.726744 = 156.977 GPU_h
n_ref_negatives = n_labeled_pairs-n_ref_positives = 13 - 6 = 7 pairs
l_pilot.need = gpu_h_pilot/n_main_gpus = 39.2442 / 8 = 4.90552 h
l_main.need = gpu_h_main/n_main_gpus = 156.977 / 8 = 19.6221 h
l_storage.usd = fs_usd_gib_month*n_storage_gib*n_days/30 = 0.2 * 200 * 7 / 30 = 9.33333 usd
l_stretch.need = gpu_h_stretch_extra/n_main_gpus = 156.977 / 8 = 19.6221 h
l_fallback_dock_md.need = gpu_h_main/n_main_gpus = 156.977 / 8 = 19.6221 h
l_h100_oom.need = gpu_h_main/n_main_gpus = 156.977 / 8 = 19.6221 h
fs_md_100ns = 7200/md_ns_per_day_a100*24/n_main_gpus*8*1.99 = 7200 / 129 * 24 / 8 * 8 * 1.99 = 2665.67 usd
fs_grid_12x12 = 144*n_stretch_jobs_per_pair*gpu_h_per_job/n_main_gpus*8*1.99 = 144 * 12 * 0.726744 / 8 * 8 * 1.99 = 2499.07 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:hypothesis` PARTIAL · page: "This structure reveals that of the five Ig-like polycystic kidney disease (PKD) domains in AAVR, PKD2 binds directly to the spike region of the AAV2 capsid adjacent to the icosahedral three-fold axis." · note: Quote appears verbatim in the abstract and supports the threefold-axis engagement premise (for AAVR-PKD2 on AAV2). The source says nothing about insert-loop engagement geometry or about plate- and bead-based assay pairs; the 'pose enumeration recovers labels' clause is the plan's prediction and needs no source. So the cited source supports only part of the premise.
- sample 1 · `card:closest_prior` PARTIAL · page: "c Representative AlphaFold models, from 5 structural models each of X1 and CAP-Mac peptides with up to 20 recycles, predict selective interaction with human LRP6 domain E1 (E1 and E2: teal, E3 and E4: yellow, AAV peptides: purple). b SPR confirms that the engineered capsids AAV9-X1.1 and CAP-Mac gained direct binding interactions with human LRP6. v.g.: viral genomes." · note: The quote appears verbatim and supports five AlphaFold models per peptide and SPR binding labels (panels b and d). The figure page does not mention cryo-ET or mapping of IL3 binding sites (IL3 appears only in the article title), and authorship ('Shay and colleagues') is not shown. The carried value 10 is not stated anywhere on the page; the page gives 5 structural models each and up to 20 recycles.
- sample 1 · `card:left_open` PARTIAL · page: "c Representative AlphaFold models, from 5 structural models each of X1 and CAP-Mac peptides with up to 20 recycles, predict selective interaction with human LRP6 domain E1 (E1 and E2: teal, E3 and E4: yellow, AAV peptides: purple)." · note: The quote supports that the closest prior used only 5 models per peptide with up to 20 recycles (modest compute), which is consistent with large-scale pose/seed runs being left open. The page gives no evidence about threefold-axis geometry, bind/no-bind agreement across a full capsid-by-receptor grid, or that this gap is untested in the wider literature.
- sample 1 · `card:limits` UNSUPPORTED · page: "" · note: The scope restriction (binding calls and interface geometry only) is a plan choice needing no source, but the factual claims that public labels cover 13 of 36 pairs and that NR001–NR005 and Starfish assays are proprietary carry no source at all.
- sample 1 · `num:af2_h_per_run` PARTIAL · page: "This job took 2.5 minutes to complete (296 residues). Prediction time for a structure of N residues is roughly (N/30)*(N/30) seconds for an Nvidia A40 GPU." · note: The quoted formula appears verbatim and is a legitimate proxy basis, but the page never states 0.5 GPU_h per run; its only concrete per-run wall-clock is 2.5 minutes (0.0417 h) for a 296-residue heterodimer on an Nvidia A40 (ColabFold output includes the 5 model PDBs). The item's own differs_in notes the monomer formula and A40-vs-A100 mismatch, but the recorded number is not stated on the page for the given setting. · page value 0.0417
- sample 2 · `card:question` PARTIAL · page: "This structure reveals that of the five Ig-like polycystic kidney disease (PKD) domains in AAVR, PKD2 binds directly to the spike region of the AAV2 capsid adjacent to the icosahedral three-fold axis. | SPR confirms that the engineered capsids AAV9-X1.1 and CAP-Mac gained direct binding interactions with human LRP6." · note: The card cites no sources. The fetched pages corroborate published bind/no-bind readouts for AAVR (Zhang et al. abstract: PKD2 binds the AAV2 spike; Fig. 4 is 'Mutagenesis study of AAVR for AAV2 binding assays') and for LRP6 (Shay et al. Fig. 4b/d: SPR shows engineered capsids bind human LRP6/LRP6-E1E2 while parent AAV9 does not), and the AAVR interface is at the threefold axis. No fetched page mentions ALPL or any published ALPL bind/no-bind readout, so that part of the premise is unsupported.
- sample 2 · `card:closest_prior` PARTIAL · page: "Representative AlphaFold models, from 5 structural models each of X1 and CAP-Mac peptides with up to 20 recycles, predict selective interaction with human LRP6 domain E1 (E1 and E2: teal, E3 and E4: yellow, AAV peptides: purple). | we identify a naturally-evolved and serotype-specific interaction between the AAV9 capsid and human interleukin 3 (IL3) ... as well as lab-evolved low-density lipoprotein receptor-related protein 6 (LRP6) interactions specific to engineered capsids" · note: Quote appears verbatim in the Fig. 4 caption (panel c). The article page confirms first author Timothy F. Shay, published 08 September 2024; 'We applied AlphaFold-Multimer to build models of LRP6-AAV interaction complexes' with 5 structural models per peptide and up to 20 recycles; SPR panels b/d give bind/no-bind labels. But the page describes IL3 binding as a naturally-evolved interaction of the AAV9 capsid (cryo-ET mapped IL3 on AAV9, Fig. 3d), with only the LRP6 interactions 'specific to engineered capsids', so 'where LRP6 and IL3 bind engineered capsids' is inaccurate for the IL3 part. The value 10 is a plan-assigned number with no counterpart on the page.
- sample 2 · `card:limits` PARTIAL · page: "SPR confirms that the engineered capsids AAV9-X1.1 and CAP-Mac gained direct binding interactions with human LRP6." · note: The scope statement (binding-call agreement and interface geometry only; no transcytosis or affinity) is what the plan will measure and needs no source. The factual claims that public labels cover 13 of 36 pairs and that NR001–NR005 and Starfish assays are proprietary have no cited source and appear on no fetched page (the fetched pages cover only AAVR, LRP6 and IL3 bind/no-bind readouts); the quoted SPR sentence merely shows public labels exist for some pairs.

**Critic.**
- stakes 3 · `card:limits` "Binding-call agreement and interface geometry only; no transcytosis or affinity. Public labels cover 13 of 36 pairs; NR001–NR005 and Starfish assays are proprietary." · Binding agreement and geometry only; transcytosis choice needs untested post-binding fate and proprietary assay validation.
- lever 3 · `plan:compute_axis.levels` "[54,216,432]" · Levels 54,216,432 span only 8x, below required 10x; other lever conditions can hold.
- verifiable 5 · `plan:anchor` "Redocking AAVR-PKD2 onto AAV2 must place it beside the threefold spike matching PDB 6IHB contacts; serial and parallel pilots must match calls. Tolerance: >=50% contact overlap at the published 4.5 Å cutoff or interface backbone RMSD <=5 Å;…" · Published experimental labels score outputs; p0 anchor reproduces PDB 6IHB within stated contact or RMSD tolerance.
- open 5 · `card:left_open` "Whether hundreds of pose and seed runs improve bind/no-bind agreement with threefold-axis geometry across a full capsid-by-receptor grid remains untested [s_shay_af]." · Prior used five models per peptide; full grid and hundreds-run agreement gap is explicitly untested.
- reshape 1 · `card:sequential_part` "No answer waits on another: 216 independent runs; three stages follow one another only within each run." · No answer waits on another; independent capsid-receptor runs are only side-by-side parallelism.
- baseline NA · `card:method` "none" · Restructuring method is none, so baseline condition makes this criterion NA.

**Producer says (not judged).** expected if_not (Binding calls hinge on insert loops already visible in sequence space, so pose depth saturates quickly; receptor flexibility, not run count, limits site agreement.); compute_tested yes (Levels 54, 216 and 432 vary exactly the pose-and-seed model runs that more parallel GPUs buy across the capsid by receptor grid; sequences, labels and protocols stay fixed.); decides no; searched yes.

**Annotations.**
- dropped the producer's definition of budget_usd, fs_usd_gib_month: set by the question
- full_scale.fs_md_100ns.ratio_to dropped: "budget_usd" is not a number id
- full_scale.fs_grid_12x12.ratio_to dropped: "budget_usd" is not a number id
- gate_ref at phases.p4_stretch.gate.on: "seed_sd_calls" is not a number id
- quote at numbers.af2_h_per_run.quote: 0.5 does not appear in the quote "Prediction time for a structure of N residues is roughly (N/30)*(N/30) seconds for an Nvidia A40 GPU."; a value transformed from the page belongs in a DERIVED number
- quote at numbers.md_ns_per_day_a100.quote: 129 does not appear in the quote "a protein in explicit water (170,320 atoms) ... | A100 | 267.5 | 691.7 | 265.8 | 129.1 | 38.8 | 23.2 |"; a value transformed from the page belongs in a DERIVED number
- prior_max_level 10 is not in the quote of s_shay_af
- hypothesis: a sentence of 22 words
- predictions.if_lever: a sentence of 22 words
- predictions.if_not: a sentence of 25 words
- test_summary: a sentence of 28 words
- novelty.closest_prior: a sentence of 25 words
- novelty.left_open: a sentence of 21 words
- anchor.what: a sentence of 22 words
- novelty.closest_prior: rewritten by the field repair
- card field novelty.closest_prior still fails: coined codes: IL3
- dramaturg findings failed G-find after a resample; decided as returned
- prose over 240 words (256)

**Root question (null).** Can molecular mapping of AAV capsid-receptor interactions on brain microvascular endothelial cells determine which AAV variants transcytose across the blood-brain barrier versus remain intracellular, and for which capsid-receptor binding signatures?

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/blind-01/20261021-0116-loop/out/r1/card/work/seed-1/seed/idea/95fa97ae/producer.md)

## Inventory

| Option | Title | Distance | Cluster | Total | Status | Reason |
|---|---|---|---|---|---|---|

## Log

```
pool: 0 candidate cluster(s); picked 0
seed:idea:seed: dropped the producer's definition of budget_usd, fs_usd_gib_month: set by the question
seed:idea:seed: full_scale.fs_md_100ns.ratio_to dropped: "budget_usd" is not a number id
seed:idea:seed: full_scale.fs_grid_12x12.ratio_to dropped: "budget_usd" is not a number id
seed:idea:seed: gate_ref at phases.p4_stretch.gate.on: "seed_sd_calls" is not a number id
seed:idea:seed: quote at numbers.af2_h_per_run.quote: 0.5 does not appear in the quote "Prediction time for a structure of N residues is roughly (N/30)*(N/30) seconds for an Nvidia A40 GPU."; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: quote at numbers.md_ns_per_day_a100.quote: 129 does not appear in the quote "a protein in explicit water (170,320 atoms) ... | A100 | 267.5 | 691.7 | 265.8 | 129.1 | 38.8 | 23.2 |"; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: prior_max_level 10 is not in the quote of s_shay_af
seed:idea:seed: hypothesis: a sentence of 22 words
seed:idea:seed: predictions.if_lever: a sentence of 22 words
seed:idea:seed: predictions.if_not: a sentence of 25 words
seed:idea:seed: test_summary: a sentence of 28 words
seed:idea:seed: novelty.closest_prior: a sentence of 25 words
seed:idea:seed: novelty.left_open: a sentence of 21 words
seed:idea:seed: anchor.what: a sentence of 22 words
seed:idea:seed: card fields failing: novelty.closest_prior (coined codes: IL3)
seed:idea:seed: novelty.closest_prior: rewritten by the field repair
seed:idea:seed: card field novelty.closest_prior still fails: coined codes: IL3
seed:idea:seed: dramaturg: degenerate: card:question; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary
seed:idea:seed: dramaturg (resample): degenerate: card:question; degenerate: card:if_lever; degenerate: card:if_not; degenerate: card:test_summary
seed:idea:seed: dramaturg findings failed G-find after a resample; decided as returned
seed:idea:seed: dramaturg-2: card:limits: 0 findings
seed:idea:seed: prose over 240 words (256)
```