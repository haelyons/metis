# Producer working file — option V3

Option title: Motif calls emitted for Capsida NR001–NR005 and Lir Starfish binding-assay readouts

Working file. The deliverable is the JSON record in the run output; this file holds the plan,
the source quotes, the cost arithmetic, and the word counts for the card fields.

Note on this session: no local shell tool was available, so no code was executed here. The pilot
script that measures the throughputs is saved at `pilot/measure_throughput.py` and runs in phase
`p1_pilot` on Lambda. Every throughput input is therefore PROXY or GUESS, with `measured_by`
naming `p1_pilot`. No number in the record is MEASURED.

## What the option asks, in plain terms

Enumerate binding modes of AAV capsid libraries against a human BBB-receptor set (ALPL, AAVR,
LRP6 and panel partners), emit calls in the format of plate- and bead-based capsid–receptor
binding assays, score whether 3-fold-axis engagement geometry agrees with measured bind/no-bind
receptor by receptor, and rank binding-positive pairs as the only transcytosis candidates.
Transcytosis and all post-binding fate are out of scope.

## The concrete build

Public stand-ins for the proprietary capsids and assays. Capsida's NR001–NR005 receptor/capsid
identities and Lir's Starfish outputs are not public; both companies do publish the assay formats
and the receptor classes. The plan therefore builds the same computation on a public panel with
published bind/no-bind labels, and scores exactly as the option specifies.

Grid: 6 capsids x 6 receptors = 36 pairs, 6 model runs per pair = 216 runs at the main level.

Capsids (public sequences/structures):
1. AAV2 — AAVR-PKD2 binder, heparan-sulfate binder.
2. AAV5 — AAVR-PKD1 binder (distinct site).
3. AAV9 — parent of the engineered BBB capsids; AAVR-PKD2 and galactose.
4. AAV9-X1.1 — VR-IV DGAATKN / VR-VIII AQGNNTRSVAQ (Shay 2024 Table 1); LRP6 binder.
5. AAV.CAP-Mac — VR-VIII AQLNTTKPIAQ (Shay 2024 Table 1); LRP6 binder.
6. AAV-PHP.eB — 7-mer TLAVPFK insertion; LY6A binder, weaker AAVR-PKD2.

Receptors: ALPL; AAVR-PKD2; AAVR-PKD1; LRP6-E1E2; LRP6-E3E4 and LRP5 (specificity controls);
LY6A. (Six receptor constructs: ALPL, AAVR-PKD2, AAVR-PKD1, LRP6-E1E2, LRP5, LY6A. LRP6-E3E4
is scored inside the LRP6 column as a domain check.)

Per pair, 6 model runs: 1 rigid-body docking job (200 poses, keep top 10), 3 AlphaFold-Multimer/
ColabFold seeds (up to 20 recycles), 2 short MD relaxations (5 ns each) of the top 2 poses.

Emitted calls: one row per capsid x receptor in plate layout (rows capsids, columns receptors)
plus a bead-panel CSV (bead id = receptor construct, MFI-like score = consensus score), fields
bind/no-bind, consensus score, interface residues, distance of interface centroid to nearest
3-fold axis, site class (3-fold-adjacent / 5-fold / 2-fold / insert-loop), and rank.

Scoring: balanced accuracy of bind/no-bind calls against published labels on the 13 labeled pairs
(6 positives, 7 negatives), plus fraction of positives whose top pose sits at the published site
(contact overlap >= 50% at the published 4.5 A contact cutoff, or interface RMSD <= 5 A).

Reference labels (published):
- AAV2 x AAVR-PKD2 bind; AAV5 x AAVR-PKD1 bind; AAV9 x AAVR-PKD2 bind; PHP.eB x AAVR-PKD2 bind
  (weaker).
- AAV9-X1.1 x LRP6 bind, x LRP5 no bind; CAP-Mac x LRP6 bind, x LRP5 no bind; AAV9 x LRP6 no
  bind; AAV9 x LY6A no bind; PHP.eB x LY6A bind; AAV9 x ALPL no bind; VCAP-102 x ALPL bind
  (VCAP-102 sequence taken from supplement if deposited, else AAV9 column kept as parent
  negative and the ALPL column is exploratory).

## Why 3-fold geometry is the right observable

AAV2–AAVR: PKD2 binds the spike region adjacent to the icosahedral three-fold axis (Zhang 2019).
Most AAV serotypes bind PKD2 with the domain C-terminus near the viral 3-fold axis (review). Lir
states the 2-, 3- and 5-fold surface patches are the minimum subunit for useful docking. Lir also
reports the 3-fold axes of AAV9 are generated with RMSD < 1 A by all methods tried, but the
5-fold axis OOMs Boltz2 on an 80 GB H100 and AlphaFold2-Multimer returns the wrong pentamer.
So: score the 3-fold patch, treat 5-fold-only poses as failures, and keep complexes to
trimer-patch + ectodomain size.

## Compute axis, baselines, predictions

Compute axis: model runs (docking/AF2/MD) the answer needs. Nested levels 54 (pilot 3x3),
216 (main 6x6), 432 (stretch: 6 AF2 seeds + 4 MD poses per pair).

Measured quantity: balanced accuracy of bind/no-bind calls on the 13 published labeled pairs,
and positives recovered within site tolerance. Measured at each nested run level.

- if_lever: balanced accuracy 0.80 at 432 runs versus 0.55 at 54, with 5 of 6 known binders
  within 5 A of published sites.
- if_not: accuracy moves < 0.05 between 54 and 432 runs and at most 3 of 6 binders reach
  published sites; extra runs resample the wrong pose basin.
- decision rule: if_lever iff bal_acc(432) - bal_acc(54) >= 0.10 AND >= 5 of 6 positives inside
  site tolerance; else if_not.
- noise rule: 3 independent seed sets per level, mean +/- SD; a gap counts only if it exceeds
  2x the SD across seed sets and a paired permutation test over the 13 labels gives p < 0.05.
- expected: if_not. Binding calls hinge on insert loops already visible in sequence space, so
  pose depth saturates; receptor flexibility, not run count, limits site agreement.

Baselines:
- scientific baseline: rigid-body docking score ranking alone, no multimer model, no 3-fold
  geometry filter, on the same 36-pair grid (scored on the same 13 labels).
- baseline_sequential: one A100 runs the 54-run pilot back-to-back (serial queue, batch 1, same
  seeds). Timed for wall-clock and for result equivalence.
- baseline_copies: 8 independent one-GPU copies of the same jobs on one 8-GPU node; identical
  per-run settings; timed for wall-clock.

Anchor: redock AAVR-PKD2 onto AAV2; the best pose must land beside the 3-fold spike matching
PDB 6IHB contacts (>= 50% contact overlap at 4.5 A). Second check: X1 and CAP-Mac VR-VIII
peptides must select LRP6 E1E2 over E3E4. Serial and parallel pilot results must match: identical
bind/no-bind calls and top-pose interface RMSD <= 2 A.

Restructuring: method = none. No answer waits on another; 216 independent runs queue across
8 GPUs. (Within a run, its three stages run back to back, one run deep.)

Novelty: closest prior is Shay et al. 2024 — AlphaFold-Multimer models (5 models per peptide, up
to 20 recycles) plus SPR and cryo-ET for LRP6 and IL3 sites on about six engineered capsids,
largest compute quantity = 10 model runs on our axis. It does not decide the outcome at 216–432
runs over a 36-pair grid.

## Cost arithmetic (Lambda on-demand, read 2026-10-21)

Rates: A100 SXM 40 GB 8x at $1.99/GPU-h = $15.92/instance-h; A100 SXM 1x at $1.99/GPU-h;
H100 SXM 8x at $3.99/GPU-h = $31.92/instance-h (fallback if AF2 OOMs at 40 GB); A6000 4x at
$1.09/GPU-h (optional deep MD). Filesystem $0.20/GiB-month.

Throughput inputs:
- af2_h_per_run = 0.5 h per AF2-Multimer run on one A100 (PROXY: Wynton ColabFold page gives
  (N/30)^2 seconds on an A40 for N residues; ours are 750–1000-residue multimers with up to 20
  recycles). measured_by p1_pilot.
- md_ns_per_day_a100 = 129 ns/day (PROXY: GROMACS 2024.1 on one A100, 170,320-atom protein in
  water). measured_by p1_pilot.
- md_h_per_run = 5*24/129 = 0.930 h.
- aux_h_per_pair = 1.0 h (GUESS: docking job, MSAs, scoring, I/O). measured_by p1_pilot.
- gpu_h_per_pair = 3*0.5 + 2*0.930 + 1.0 = 4.360 h.
- gpu_h_pilot = 9*4.360 = 39.24 h -> /8 GPUs = 4.91 instance-h.
- gpu_h_main = 36*4.360 = 156.98 h -> /8 = 19.62 instance-h.
- gpu_h_per_job = 4.360/6 = 0.727 h; stretch extra 216 jobs = 156.98 GPU-h -> 19.62 instance-h.

Lines (instance hours are wall-clock of the whole instance):
- l_setup (p0, A100 1x, 6 h box, need 4): 6*1*1.99 = $11.94
- l_pilot (p1, A100 8x, 6 h box, need 4.91): 6*8*1.99 = $95.52
- l_main (p2, A100 8x, 24 h box, need 19.62): 24*8*1.99 = $382.08
- l_score (p3, A100 1x, 4 h box, need 2): 4*1*1.99 = $7.96
- l_storage: 0.2*200 GiB*7/30 = $9.33
Core total_stated = $506.83. spend_cap_usd = 1000.
Optional: l_stretch (p4, A100 8x, 24 h box, need 19.62) = $382.08 -> $888.91 with stretch.
Fallbacks instead of l_main: l_fallback_dock_md (16 h box, $254.08) if af2_h_per_run > 1.0;
l_h100_oom (12 h box on H100 8x, $383.04) if any AF2 run OOMs at 40 GB.

Full scale the budget cannot buy: 100-ns MD on both poses of all 36 pairs (~$2,666);
12x12 grid at stretch depth (~$2,501).

Outside budget: scientist time (40 h) to define the panel, run the pipeline and adjudicate
calls; optional commercial plate/bead binding assays (~$15k) to replace proxy labels; the shared
4-core local machine used for planning; public structure and sequence downloads (free).

## Scope gaps and limits

- The computation cannot test transcytosis or any post-binding fate (option leaves it aside).
- It cannot test Capsida's or Lir's proprietary capsid sequences or their actual plate/bead
  readouts; public labels cover 13 of 36 pairs.
- 5-ns MD relaxes local geometry only; it does not yield affinities or equilibrium occupancy.
- NR001–NR005 receptors other than ALPL/AAVR/LRP6 are unnamed publicly, so the receptor set is
  the published BBB panel plus controls.

## Card field word counts

question 23; hypothesis 19; if_lever 22; if_not 25; anchor.what 22; closest_prior 27;
left_open 21; limits 23 (across two strings); test_summary 28; sequential_part 17;
method = "none".

## Sources (exact sentences relied on)

s_lambda https://lambda.ai/pricing — "Plan NVIDIA A100 SXM | VRAM/GPU: 40 GB | vCPUs: 124 |
RAM: 1800 GiB | STORAGE: 5.8 TiB SSD | PRICE/GPU/HR*: $1.99 (* plus applicable sales tax/VAT/GST)"
and "For example, at a rate of $0.20 per GiB per month: If you use 1,000 GiB continuously for a
full month (720 hours), you'll be billed $200.00."

s_capsida_deck https://capsida.com/wp-content/uploads/Nick_Goeden_1445_May-14_Theater-C_Identification-of-Multiple-BBB-Receptors.pdf
— "Plate-Based Receptor Binding Detection Bead-Based Receptor Binding Detection" and "The
predictive power of in vitro receptor binding is confirmed by AAV transduction in cell lines with
receptor expression" and "Binding also confirmed for NR002-5" and "Human and NHP ortholog binding
confirmed".

s_capsida_science https://capsida.com/science-innovation/ — "We have identified novel human
blood-brain barrier receptors that bind our engineered capsids and are conserved between primates
and humans."

s_lir_starfish https://www.lirtx.com/post/starfish-fast-capsid-structure-generation — "portions
of the surface such as at the 2, 3 and 5-fold axes are the minimum subunit for useful docking or
structural assessment of capsid stability in silico." / "Alphafold2/Openfold scales poorly as the
complexity of the surface portion increases, requiring over an hour to generate the 5-fold axis .
Boltz2 is able to generate structures of the 3-fold axis in reasonable time but fails to generate
a 5-fold axis, running out of memory (OOM) on a H100 80GB GPU." / "We first showcased an
application of this technology at ESGCT 2025 in Seville, demonstrating that screening of the LY6A
receptor was possible by performing docking to variant capsid surfaces constructed using
Starfish™." / "All approaches generate the 3-fold axes of AAV9 wild-type with an RMSD <1Å".

s_shay_lrp6 https://www.nature.com/articles/s41467-024-52149-0 — "Both AAV9-X1.1 and CAP-Mac
strongly bind human LRP6-Fc, unlike their parent capsid, AAV9, with a sub-nM apparent affinity."

s_shay_af https://www.nature.com/articles/s41467-024-52149-0/figures/4 — "Representative
AlphaFold models, from 5 structural models each of X1 and CAP-Mac peptides with up to 20 recycles,
predict selective interaction with human LRP6 domain E1 (E1 and E2: teal, E3 and E4: yellow, AAV
peptides: purple)."

s_shay_lrp5 https://www.nature.com/articles/s41467-024-52149-0 — "A pull-down assay confirmed
that both AAV9-X1.1 and CAP-Mac bind to AAVR's PKD2 domain and the full length extracellular
domain of mouse LRP6 but not that of closely-related LRP5 (Supplementary Fig. 9a)."

s_shay_il3 https://www.nature.com/articles/s41467-024-52149-0 — "we were able to locate the
human IL3 binding site on the side of AAV9's threefold symmetry spike adjacent to the capsid's
twofold symmetry valley and generate an integrative binding model."

s_aavr_struct https://www.nature.com/articles/s41564-018-0356-7 — "This structure reveals that
of the five Ig-like polycystic kidney disease (PKD) domains in AAVR, PKD2 binds directly to the
spike region of the AAV2 capsid adjacent to the icosahedral three-fold axis."

s_aavr_review https://pmc.ncbi.nlm.nih.gov/articles/PMC9950413/ — "Several cryo-EM structures of
AAV-AAVR complexes are published using constructs containing either two domains (PKD12) or all
five PKD domains (PKD1-5) with similar results (Meyer et al., 2019; Zhang et al., 2019; Silveria
et al., 2020; Xu et al., 2022)." and "the contact footprints (4.5 Å cut-off) for all of the
binding surfaces that are related by the viral symmetry axes".

s_alpl https://doi.org/10.1101/2024.03.12.584703 — "We identify alkaline phosphatase (ALPL) as
the primary receptor used by VCAP-102 to cross the BBB and demonstrate that direct binding of
VCAP-102 to human ALPL can initiate receptor-mediated transcytosis in a cell barrier model." and
"VCAP-102 binds ALPL with an affinity of ∼20 nM at pH 7.4 and is rapidly released at pH 5."

s_ly6a https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0225206 — "Ly6a
expression resulted in a >50-fold increase in binding by each of the AAV-PHP.B capsids to HEK293T
cells, but did not increase binding by AAV9 (Fig 3A)."

s_phpeb https://pmc.ncbi.nlm.nih.gov/articles/PMC9382559/ — "We found that LY6A pulled down
PHP.eB even more efficiently than PKD2 did. By contrast, LY6A did not detectably capture any AAV9
capsids, revealing significantly different receptor selectivity for AAV9 and PHP.eB." and "AAV1,
AAV2, and AAV8 interact with the PKD2 domain, while AAV5 interacts with PKD1."

s_colabfold https://pmc.ncbi.nlm.nih.gov/articles/PMC9184281/ — "ColabFold's 40−60-fold faster
search and optimized model utilization enables prediction of close to 1,000 structures per day on
a server with one graphics processing unit."

s_wynton https://www.rbvi.ucsf.edu/chimerax/data/wynton-colabfold-feb2024/colabfold_wynton.html
— "Prediction time for a structure of N residues is roughly (N/30)*(N/30) seconds for an Nvidia
A40 GPU."

s_gromacs https://hpc.fau.de/2024/08/13/gromacs-2024-1-on-brand-new-gpgpus/ — "1. R-143a in
hexane (20,248 atoms) ... 4. a protein in explicit water (170,320 atoms) ... | A100 | 267.5 |
691.7 | 265.8 | 129.1 | 38.8 | 23.2 |" (ns/day, system 4 = 129.1).
