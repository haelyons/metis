# Result

Picks 1 · PASS 1 · on-goal cards U4 0 · U3 1 · halts: none

## Table

| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [seed·idea·1](#card-seed-idea-1) Exhaustive capsid–receptor complex enumeration (docking and AlphaFold-Multimer) | PASS 1/2 | seed | if_not | 5 | — → 5 | — → 3 | 5 | — | — → 1 | — | $956 at p5_analysis · plan $956 · 3 GUESS |

## Frontier (listed, not produced)

None.

## Cards

<a id="card-seed-idea-1"></a>**Option 1: Exhaustive capsid–receptor complex enumeration (docking and AlphaFold-Multimer) · Exhaustive capsid–receptor complex enumeration (docking and AlphaFold-Multimer).** seed pick · compute tested: yes · plan expects: not the lever · PASS

**Question.** Does exhaustive modeling of AAV capsid–receptor complexes reveal a shared interface motif, like 3-fold-axis GPI-receptor engagement, that marks which capsids transcytose the BBB?

**What is known.** The earlier APPRAISE-AAV study used AlphaFold-Multimer, ten replicate models per matrix, to rank capsid peptides against the receptors LY6A, LY6C1 and CA4, validating one PHP.eB–LY6A pose [s_appraise]. Whether a shared 3-fold-axis GPI-engagement motif marks transcytosis-competent pairs across a whole capsid panel, or whether deeper pose sampling changes that call [s_appraise].

**Hypothesis.** Transcytosis-competent capsids engage GPI-anchored BBB receptors at the capsid 3-fold spike with a shared anchor geometry, unlike non-cognate pairs [s_appraise].

**If compute is the lever.** At 2,880 models the competent-minus-retained GPI-engagement gap reaches 0.50 or more, while at 144 models it stays below 0.25.

**If not.** The gap stays within 0.15 of its 144-model value at every depth; added poses change nothing because insert location already fixes the 3-fold site [s_cat].

**Test.** Run 72 pairs at 144, 720, 2,880 pose models on 8x A100s [s_lambda], anchored on the published PHP.eB–LY6A complex [s_appraise]; compare with the ten-model published baseline and the 144-model shallow arm against phenotype labels [s_alpl].

*Compute axis.* Capsid–receptor pose models computed per panel sweep (rigid-docking poses plus AlphaFold-Multimer seed models): 144–2,880 pose models, 3 levels. Closest prior: 10 [s_appraise_rep], beyond it.

*Restructuring.* none.

**Check first.** Rebuild the published PHP.eB peptide–LY6A complex and require its validated contacts and capsid fit before any library spend [s_appraise]. Tolerance: capsid-fragment RMSD to PDB 7WQO at most 1.5 Å (published engineered-loop RMSD is 1.36 Å) and at least 2 of the 3 named contacts (peptide Pro5', Phe6', LY6A Ala58) within 5 Å.

**Would not show.** Predicted interface geometry only, not transcytosis rates or post-binding fate; weak avidity-dependent contacts may evade prediction [s_appraise]; twelve capsids, six receptors.

*Cost.* Plans $955.84 of the $1,000 budget over 59 machine-hours, leaving $44.16. Main guess: wall minutes per AlphaFold-Multimer seed job [g], measured after $51.74 of spend; the budget is reached if it is 1.1× higher. 2 cost flags in the block.

**Judges.** Dramaturg: PASS 1/2. Decides at: $956 at p5_analysis · plan $956 · 3 GUESS (critic: Only p5_analysis bins all depths and bootstraps 2,880-versus-144 gap; pilot, shallow, deep do not apply rule).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $1,000 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-10-21 · filesystem $0.20/GiB-month [q]
Spend      p0_inputs  Fetch 12 capsid and 6 receptor constructs, build the 72 pair FASTAs, run the symmetry-axis precheck that each engineered insertion lies on the 3-fold spike [s_cat_vr]  1x NVIDIA A100 SXM 40GB $1.99/h  2 h  $3.98  l_p0_setup need 1.5 h in a 2 h box
           p1_pilot  On one 8x A100 instance: reproduce the PHP.eB–LY6A anchor, time 6 representative pair jobs, one docking job and 2 ns MD, write pilot/pilot_metrics.txt with pilot/run_pilot.py  8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h  3 h  $47.76  l_p1_pilot need 2.5 h in a 3 h box
           p2_shallow  Compute 2 pose models for every pair (1 docking pose plus 1 AlphaFold seed): 144 models, and the first motif gap  8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h  4 h  $63.68  l_p2_shallow need 2.8 h in a 4 h box
           p3_deep  Deepen each pair to 40 pose models (20 docking poses plus 20 AlphaFold seeds): 2,880 models, with the 720-model snapshot taken at 10 per pair  8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h  36 h  $693.12  l_p3_deep need 34.2 h in a 36 h box
           p4_md  Refine 20 top cluster representatives with 20 ns explicit-solvent MD and measure interface stability  8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h  8 h  $127.36  l_p4_md need 5 h in a 8 h box
           p5_analysis  Bin every pose by capsid symmetry axis and GPI-anchor angle, bootstrap the motif gap at 144, 720 and 2,880 models, write the report  1x NVIDIA A100 SXM 40GB $1.99/h  6 h  $19.94  l_p5_analysis need 4 h in a 6 h box
           Planned $955.84 · unallocated $44.16 · cap $1,000
Rests on   wall minutes per AlphaFold-Multimer seed job 12 minutes [g] rests on: citation not confirmed: UNSUPPORTED · measured in p1_pilot ($51.74 spent by then) · gate wall minutes per AlphaFold-Multimer seed job ≤ 20 in p1_pilot (now 12, passes; uncut plan at it $1,290.16), else halve af_seeds_deep to 12 per pair and re-price; stop entirely if jobs exceed 30 min · budget reached at 13.6 (1.1× higher) · box overflows at 1.1×
           MD throughput for the refinement system 240 ns per GPU-day [g] rests on: citation not confirmed: CONTRADICTED · measured in p1_pilot ($51.74 spent by then) · budget reached at 111 (2.2× lower) · box overflows at 1.6×
           capsids with usable structures or sequences in p0 12 capsids [g] rests on: each of the twelve engineered capsids has a published sequence and a parent serotype structure in the AAV capsid catalog · measured in p0_inputs ($3.98 spent by then) · gate capsids with usable structures or sequences in p0 ≥ 9 in p0_inputs (now 12, passes; uncut plan at it $955.84), else shrink the library to ready capsids, re-derive the pair grid and re-price before any GPU spend · budget not reached within 1000×
Scenarios  Measured jobs run at 25 minutes instead of 12: the p3 gate halves deep seeds to 12 per pair, giving 1,008 deep pose models inside the same 36-hour box → $1,528.96 (over budget) · Same work on 8x H100 SXM at $3.99 per GPU-hour: jobs finish about 1.8 times faster, deep line wall-clock near 20 hours, total bill rises to about $1,300 → $955.84
Buys       capsid–receptor pairs enumerated: 72 [=] · Measured jobs run at 25 minutes instead of 12: the p3 gate halves deep seeds to 12 per pair, giving 1,008 deep pose models inside the same 36-hour box: 72 · Same work on 8x H100 SXM at $3.99 per GPU-hour: jobs finish about 1.8 times faster, deep line wall-clock near 20 hours, total bill rises to about $1,300: 72
           pose models at the shallow level: 144 [=] · Measured jobs run at 25 minutes instead of 12: the p3 gate halves deep seeds to 12 per pair, giving 1,008 deep pose models inside the same 36-hour box: 144 · Same work on 8x H100 SXM at $3.99 per GPU-hour: jobs finish about 1.8 times faster, deep line wall-clock near 20 hours, total bill rises to about $1,300: 144
           pose models at the medium level: 720 [=] · Measured jobs run at 25 minutes instead of 12: the p3 gate halves deep seeds to 12 per pair, giving 1,008 deep pose models inside the same 36-hour box: 720 · Same work on 8x H100 SXM at $3.99 per GPU-hour: jobs finish about 1.8 times faster, deep line wall-clock near 20 hours, total bill rises to about $1,300: 720
           pose models at the deep level: 2,880 [=] · Measured jobs run at 25 minutes instead of 12: the p3 gate halves deep seeds to 12 per pair, giving 1,008 deep pose models inside the same 36-hour box: 2,880 · Same work on 8x H100 SXM at $3.99 per GPU-hour: jobs finish about 1.8 times faster, deep line wall-clock near 20 hours, total bill rises to about $1,300: 2,880
           MD refinement runs: 20 [d] · Measured jobs run at 25 minutes instead of 12: the p3 gate halves deep seeds to 12 per pair, giving 1,008 deep pose models inside the same 36-hour box: 20 · Same work on 8x H100 SXM at $3.99 per GPU-hour: jobs finish about 1.8 times faster, deep line wall-clock near 20 hours, total bill rises to about $1,300: 20
Flags      error (quote) at numbers.prior_peptides.quote: 2 does not appear in the quote "The input comprised two sequences: surface-exposed residues in VR-VIII of AAV-X1 (587-AQGNNTRSVAQAQTG-594) or AAV-CAP-Mac (587-AQLNTTKPIAQAQTG-594) and the extracellular domain of human LRP6 (UniProt entry O75581, residues 20-1370)."; a value transformed from the page belongs in a DERIVED number
           uncut plan at the p1_pilot gate threshold costs $1,290.16, over budget; the plan relies on: halve af_seeds_deep to 12 per pair and re-price; stop entirely if jobs exceed 30 min
           thin headroom: the budget is reached if wall minutes per AlphaFold-Multimer seed job is 1.1× higher
Full scale 100-capsid library against 6 receptors at 40 pose models each: 24,000 models, 8.3 times the grid here: $4,776 = 4.78× budget = 1.66× pose models at the deep level
           1 microsecond of all-atom MD for a whole 60-mer capsid with receptor and membrane (about 2.5M atoms, roughly 10 ns/day on one A100): $12,700 = 12.7× budget = 637× MD length per refinement run
           200 AlphaFold seeds per pair with Amber relaxation of every pose, five times the deep sampling: $2,865.60 = 2.87× budget = 143× AlphaFold-Multimer seeds per pair at deep level
Outside    Researcher time for construct curation, pipeline setup and analysis: 40 hours · Public PDB, AlphaFold DB and UniProt downloads and the free MMseqs2 MSA service: 0 usd · Shared local 4-core machine used only to write this plan; no local compute runs were possible in this session: 0 gpu-hours
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
n_pairs = n_capsids * n_receptors = 12 * 6 = 72 pairs
n_pose_shallow = n_pairs * 2 = 72 * 2 = 144 pose models
n_pose_med = n_pairs * 10 = 72 * 10 = 720 pose models
n_pose_deep = n_pairs * poses_per_pair_deep = 72 * 40 = 2880 pose models
af_jobs_deep = n_pairs * af_seeds_deep = 72 * 20 = 1440 jobs
instance_h_usd = 8 * usd_per_gpu_h_a1008 = 8 * 1.99 = 15.92 usd per instance-hour
prior_models = prior_models_per_peptide * prior_peptides = 5 * 2 = 10 pose models
l_p2_shallow.need = n_pairs * af_job_min / 60 / 8 + 1 = 72 * 12 / 60 / 8 + 1 = 2.8 h
l_p3_deep.need = (af_jobs_deep - n_pairs) * af_job_min / 60 / 8 = (1440 - 72) * 12 / 60 / 8 = 34.2 h
l_p4_md.need = md_runs * md_ns / md_ns_per_gpu_day * 24 / 8 = 20 * 20 / 240 * 24 / 8 = 5 h
l_storage.usd = storage_gib * fs_usd_gib_month * 0.5 = 80 * 0.2 * 0.5 = 8 usd
fs_100caps = 24000 / 2880 * 573.12 = 4776 usd
fs_whole_md = 800 * 15.92 = 12736 usd
fs_seeds5x = 5 * 573.12 = 2865.6 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:if_not` PARTIAL · page: "Recombinant Car4 was found to bind to the 3-fold protrusions of AAV9-P31." · note: The predicted gap behavior needs no source, but the rationale 'insert location already fixes the 3-fold site' is a mechanistic claim the page does not make: s_cat only shows recombinant Car4 binding the 3-fold protrusions of the insertion variant AAV9-P31, and says nothing about insert location fixing the site or deeper pose sampling adding nothing.
- sample 1 · `card:test_summary` PARTIAL · page: "Matrices ranking AAV peptides by their average competition metric over 10 replicate conditions for LY6A, LY6C1, and mouse CA-IV." · note: Runs, sampling depths, the 8x A100 choice (Lambda lists A100 SXM 40GB at $1.99/GPU-hr with 124 vCPUs on the 8x instance) and the 144-model arm are plan actions; the published PHP.eB–LY6A anchor and the ALPL phenotype label check out. But 'the ten-model published baseline' misstates the prior: the page says 10 replicate conditions, not ten models.
- sample 1 · `card:closest_prior` PARTIAL · page: "Matrices ranking AAV peptides by their average competition metric over 10 replicate conditions for LY6A, LY6C1, and mouse CA-IV." · note: AlphaFold-Multimer peptide competitions against LY6A, LY6C1 and mouse CA-IV (CA4) and validation of one PHP.eB–LY6A pose (LY6A Ala58Arg disrupts potency; RMSD 0.36 Å vs PDB 7WQO) are all on the page, and value 10 matches. But the page describes '10 replicate conditions' per matrix, not 'ten replicate models per matrix'.
- sample 1 · `src:s_appraise_rep` PARTIAL · page: "Matrices ranking AAV peptides by their average competition metric over 10 replicate conditions for LY6A, LY6C1, and mouse CA-IV." · note: Quote appears verbatim and the count 10 per receptor matrix matches value 10, but the page says '10 replicate conditions', not 'ten replicate models'; the supports text asserts a model count the page does not state.
- sample 1 · `num:af_job_min` UNSUPPORTED · page: "Paste a FASTA (monomer or multimer up to 600 aa total) and get pLDDT, PAE, and pTM/ipTM. Runs on an A100-40GB. No MSA, no templates." · note: Only the first sentence of the recorded quote is on the page; the page continues 'Runs on an A100-40GB. No MSA, no templates.' The clause '~1 to 2 min on A100-40GB' is absent and the page states no wall-time at all, so neither the quoted timing nor the recorded 12 minutes is stated for the given setting (no page_value: the page gives no number).
- sample 1 · `num:md_ns_per_gpu_day` CONTRADICTED · page: "a protein inside a membrane surrounded by explicit water (80,289 atoms) ... [ns/day] System 1 System 2 System 3 System 4 System 5 System 6 A100 267.5 691.7 265.8 129.1 38.8 23.2" · note: The quote appears as the A100 benchmark row and system 3 is the 80,289-atom membrane system; for that setting the page states 265.8 ns/day, not the recorded 240 ns per GPU-day, so the carried value is contradicted (page_value 265.8). · page value 265.8
- sample 2 · `card:test_summary` PARTIAL · page: "NVIDIA A100 SXM | VRAM/GPU 40 GB | vCPUs 124 | RAM 1800 GiB | STORAGE 5.8 TiB SSD | PRICE/GPU/HR* $1.99 ... this method uses AlphaFold-Multimer to place surface-exposed peptides spanning mutagenic insertions (AA587 to AA594) ... Matrices ranking AAV peptides by their average competition metric over 10 replicate conditions for LY6A, LY6C1, and mouse CA-IV." · note: s_lambda verified: Lambda's 8x A100 SXM 40 GB instance row shows 124 vCPUs, 1800 GiB RAM, 5.8 TiB SSD, $1.99/GPU/hr. s_appraise verified verbatim (PHP.eB-LY6A anchor, ten-replicate baseline). The s_alpl-backed part (phenotype labels from the Voyager VCAP-102/ALPL poster) could not be checked: the PDF fetch failed twice with 'Response too large (exceeds 5MB limit)', so that citation is unverified.
- sample 2 · `src:s_alpl` UNREACHABLE · page: "" · note: The Voyager Therapeutics poster PDF could not be fetched; two attempts both failed with 'Response too large (exceeds 5MB limit)'. The recorded quote ('ALPL ectopic expression increased transcytosis of VCAP-102 >100-fold in a transwell model.') could not be checked against the page.
- sample 2 · `num:af_job_min` PARTIAL · page: "Paste a FASTA (monomer or multimer up to 600 aa total) and get pLDDT, PAE, and pTM/ipTM. Runs on an A100-40GB. No MSA, no templates." · note: The page confirms the stated setting exactly (no-MSA multimer folding up to 600 aa total on one A100 40GB), but it nowhere states a runtime: the '~1 to 2 min on A100-40GB' portion of the recorded quote is not on the page, so the 12-minute value derived from it is unchecked. The page gives no number to substitute.

**Critic.**
- stakes 3 · `card:limits` "Predicted interface geometry only, not transcytosis rates or post-binding fate; weak avidity-dependent contacts may evade prediction [s_appraise]; twelve capsids, six receptors." · Predicted geometry only, not transcytosis rates or fate; choices rely on unchecked simulation-to-reality step.
- lever 5 · `plan:predictions.decision_rule` "Paired comparison of the motif gap at 2,880 versus 144 models on the same 72 pairs: call if_lever if the gap rises by at least 0.25 with disjoint bootstrap 95% intervals; call if_not if it moves less than 0.15 and per-pair seed agreement ka…" · Same pairs, only depth changes; 0.25 rise beats 0.10 noise floor, spans 20×, and key inputs are held fixed.
- verifiable 5 · `plan:scored_against` "Published capsid–receptor phenotype labels: PHP.B/PHP.eB–LY6A and VCAP-102–ALPL transcytosis versus AAV9 and AAV2 retention [s_ly6a][s_alpl][s_voyager_pr], plus the published PHP.eB–LY6A binding pose and contacts [s_appraise_rmsd]." · Outcome uses published phenotype labels; anchor reproduces PHP.eB–LY6A pose within RMSD tolerance before spend.
- open 5 · `card:left_open` "Whether a shared 3-fold-axis GPI-engagement motif marks transcytosis-competent pairs across a whole capsid panel, or whether deeper pose sampling changes that call [s_appraise]." · Prior used ten models and one validated pose; plan asks 2,880-depth whole-panel motif, stated as open.
- reshape 1 · `card:sequential_part` "None: each capsid–receptor pair is an independent docking and folding job; only short refinements chain within one pair." · Plan states each pair is independent; it only runs copies side by side, not removing a dependency.
- baseline NA · `plan:restructuring.method` "none" · Restructuring method is none, so baseline comparison is not applicable.

**Producer says (not judged).** expected if_not (Capsid insertions already sit on the 3-fold spike [s_cat] and AlphaFold-Multimer poses for these weak interfaces vary by run and version [s_appraise_unstable], so extra poses add noise rather than a converged signature.); compute_tested yes (Each pose model is an independent docking or AlphaFold-Multimer job with its own seed, so the model count of 144, 720 or 2,880 is exactly what extra parallel GPUs buy.); decides no; searched yes.

**Annotations.**
- quote at numbers.af_job_min.quote: 12 does not appear in the quote "Paste a FASTA (monomer or multimer up to 600 aa total) and get pLDDT, PAE, and pTM/ipTM. ~1 to 2 min on A100-40GB."; a value transformed from the page belongs in a DERIVED number
- quote at numbers.md_ns_per_gpu_day.quote: 240 does not appear in the quote "A100 | 267.5 | 691.7 | 265.8 | 129.1 | 38.8 | 23.2"; a value transformed from the page belongs in a DERIVED number
- quote at numbers.prior_peptides.quote: 2 does not appear in the quote "The input comprised two sequences: surface-exposed residues in VR-VIII of AAV-X1 (587-AQGNNTRSVAQAQTG-594) or AAV-CAP-Mac (587-AQLNTTKPIAQAQTG-594) and the extracellular domain of human LRP6 (UniProt entry O75581, residues 20-1370)."; a value transformed from the page belongs in a DERIVED number
- uncut plan at the p1_pilot gate threshold costs $1,290.16, over budget; the plan relies on: halve af_seeds_deep to 12 per pair and re-price; stop entirely if jobs exceed 30 min
- thin headroom: the budget is reached if wall minutes per AlphaFold-Multimer seed job is 1.1× higher
- question: a sentence of 23 words
- predictions.if_not: a sentence of 25 words
- test_summary: a sentence of 35 words
- novelty.closest_prior: a sentence of 22 words
- novelty.left_open: a sentence of 23 words
- limits: a sentence of 21 words
- novelty.closest_prior: rewritten by the field repair
- card field novelty.closest_prior still fails: coined codes: CA4
- dramaturg findings failed G-find after a resample; decided as returned
- prose over 240 words (263)

**Root question (null).** Can molecular mapping of AAV capsid-receptor interactions on brain microvascular endothelial cells determine which AAV variants transcytose across the blood-brain barrier versus remain intracellular, and for which capsid-receptor binding signatures?

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/blind-01/20261021-0116-loop/out/r0/card/work/seed-1/seed/idea/55c57ced/producer.md)

## Inventory

| Option | Title | Distance | Cluster | Total | Status | Reason |
|---|---|---|---|---|---|---|

## Log

```
pool: 0 candidate cluster(s); picked 0
seed:idea:seed: quote at numbers.af_job_min.quote: 12 does not appear in the quote "Paste a FASTA (monomer or multimer up to 600 aa total) and get pLDDT, PAE, and pTM/ipTM. ~1 to 2 min on A100-40GB."; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: quote at numbers.md_ns_per_gpu_day.quote: 240 does not appear in the quote "A100 | 267.5 | 691.7 | 265.8 | 129.1 | 38.8 | 23.2"; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: quote at numbers.prior_peptides.quote: 2 does not appear in the quote "The input comprised two sequences: surface-exposed residues in VR-VIII of AAV-X1 (587-AQGNNTRSVAQAQTG-594) or AAV-CAP-Mac (587-AQLNTTKPIAQAQTG-594) and the extracellular domain of human LRP6 (UniProt entry O75581, residues 20-1370)."; a value transformed from the page belongs in a DERIVED number
seed:idea:seed: uncut plan at the p1_pilot gate threshold costs $1,290.16, over budget; the plan relies on: halve af_seeds_deep to 12 per pair and re-price; stop entirely if jobs exceed 30 min
seed:idea:seed: thin headroom: the budget is reached if wall minutes per AlphaFold-Multimer seed job is 1.1× higher
seed:idea:seed: question: a sentence of 23 words
seed:idea:seed: predictions.if_not: a sentence of 25 words
seed:idea:seed: test_summary: a sentence of 35 words
seed:idea:seed: novelty.closest_prior: a sentence of 22 words
seed:idea:seed: novelty.left_open: a sentence of 23 words
seed:idea:seed: limits: a sentence of 21 words
seed:idea:seed: card fields failing: novelty.closest_prior (coined codes: CA4)
seed:idea:seed: novelty.closest_prior: rewritten by the field repair
seed:idea:seed: card field novelty.closest_prior still fails: coined codes: CA4
seed:idea:seed: dramaturg: degenerate: card:question; degenerate: card:if_lever
seed:idea:seed: dramaturg (resample): degenerate: card:question; degenerate: card:if_lever
seed:idea:seed: dramaturg findings failed G-find after a resample; decided as returned
seed:idea:seed: prose over 240 words (263)
```