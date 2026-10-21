# Producer plan — Option 1: Exhaustive capsid–receptor complex enumeration (docking and AlphaFold-Multimer)

Working file. The machine-readable record is returned separately in the session output. Every factual claim below carries a URL.

## 1. What is being tested

Root question: can molecular mapping of AAV capsid–receptor interactions on brain microvascular endothelial
cells determine which AAV variants transcytose across the BBB versus remain intracellular, and for which
capsid–receptor binding signatures?

This option tests the binding step only: enumerate binding modes of an engineered capsid library against the
BBB receptor panel (LY6A, LY6C1, ALPL, LRP6, CA4, AAVR) with docking + AlphaFold-Multimer + short MD, and ask
whether transcytosis-competent pairs share a geometric motif — 3-fold-axis engagement of GPI-anchored
receptors.

Why this motif is plausible and open:
- AAV variable regions VR-IV, VR-V and VR-VIII form the 3-fold protrusions; the engineered insertions that
  create BBB-penetrant capsids sit in exactly these loops
  (https://pmc.ncbi.nlm.nih.gov/articles/PMC12682079: "VR-IV, -V, and -VIII interact with each other to form
  the 3-fold protrusions; and VR-VI and -VII are located at the base of the 3-fold protrusions.").
- A GPI-anchored BBB receptor has been seen at the 3-fold protrusion experimentally: CA4 on AAV9-P31, at 1.8 Å
  (https://pmc.ncbi.nlm.nih.gov/articles/PMC12682079: "Recombinant Car4 was found to bind to the 3-fold
  protrusions of AAV9-P31. Due to its size, similar to antibodies bound close to the symmetry axis, a localized
  cryo-EM reconstruction approach was needed to resolve the complex at 1.8 Å resolution.").
- AAVR PKD2 binds "along the side of the 3-fold protrusions and on top of the 2/5-fold wall"
  (https://pmc.ncbi.nlm.nih.gov/articles/PMC12682079).
- The BBB-crossing receptors LY6A, LY6C1 and CA4 are all GPI-anchored, and ALPL (the VCAP-102 receptor) is
  GPI-anchored too (https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/BioCentury_Voyagers-journey-to-identify-a-new-shuttle-for-bringing-gene-therapies-into-the-brain.pdf:
  "This really fits with the other receptors that have been identified for novel capsids that have brain
  tropism,\" said Hoffman, as LY6A, LY6C1 and CAIV are all GPI-anchored.").
- Prior modeling placed the PHP.eB peptide–LY6A complex "within the context of the AAV capsid threefold symmetry
  spike" and found one LY6A per trimer
  (https://pmc.ncbi.nlm.nih.gov/articles/PMC10115422).

Why it is still open: published modeling covers single-digit complexes. APPRAISE-AAV ran AlphaFold-Multimer
peptide competitions "over 10 replicate conditions for LY6A, LY6C1, and mouse CA-IV"
(https://pmc.ncbi.nlm.nih.gov/articles/PMC10115422) and the LRP6 study modeled two VR-VIII peptides with 5
models each (https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518: "Representative AlphaFold models, from 5
structural models each of X1 and CAP-Mac peptides with up to 20 recycles, predict selective interaction with
human LRP6 domain E1"). Nobody has enumerated the capsid × receptor × pose grid.

## 2. What to build

A pipeline (Python + ColabFold + GROMACS + an in-house pose-binning script) that, for each of 72
capsid–receptor pairs:

1. Builds constructs: capsid receptor-binding fragment = VR-IV + VR-VIII surface loops (the insertion site,
   residues ~445–600 of VP1; published libraries insert 7-mers between residues 588–589 of VP1,
   https://journals.plos.org/plosbiology/article?id=10.1371%2Fjournal.pbio.3002112). Receptor ectodomains:
   LY6A and LY6C1 mature domains, ALPL catalytic domain, LRP6 E1E2 (the SPR-validated binding fragment,
   https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518), CA4 ectodomain, AAVR PKD2.
2. Global rigid-body docking of receptor ectodomain onto the VP trimer (insertion loop as anchor), 20 poses per
   pair at deep level; CPU work on the instance's vCPUs.
3. AlphaFold-Multimer (ColabFold v2.3.5, AlphaFold-Multimer-v3, 5 models, up to 20 recycles, MMseqs2 MSAs —
   the same stack as https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518) on fragment × receptor, 20 seeds per
   pair at deep level.
4. Integrative placement on the capsid trimer (as in https://pmc.ncbi.nlm.nih.gov/articles/PMC10115422), then
   20 ns explicit-solvent MD (GROMACS) on 20 top cluster representatives.
5. Analysis: bin every pose by nearest icosahedral axis (2-fold, 3-fold, 5-fold, 2/5-fold wall) and by
   GPI-anchor geometry (angle of the receptor C-terminal attachment vector to the membrane normal). Motif =
   3-fold class (contact centroid within 15 Å of the 3-fold axis) AND GPI-compatible anchor (≤30°) AND
   one-receptor-per-trimer steric consistency.

Capsid library (12, chosen because each has a published receptor/BBB phenotype): AAV9, AAV2, PHP.B, PHP.eB,
PHP.eC, 9P31, 9P36, VCAP-102, AAV9-X1.1, CAP-Mac, CAP-B22, AAV-BI30.

Phenotype labels (scored_against), all from open sources:
- PHP.B/PHP.eB bind LY6A and cross the mouse BBB; LY6A disruption reduces transduction
  (https://pmc.ncbi.nlm.nih.gov/articles/PMC6855452: "Interfering with LY6A by CRISPR/Cas9-mediated Ly6a
  disruption or with blocking antibodies reduced transduction of mouse brain endothelial cells by AAV-PHP.eB,
  while ectopic expression of Ly6a increased AAV-PHP.eB transduction of HEK293T and CHO cells by 30-fold or
  more.").
- 9P31/9P36 use CA4; PHP.eC uses LY6C1; nearly all mouse-BBB-selected capsids use LY6A or LY6C1
  (https://pmc.ncbi.nlm.nih.gov/articles/PMC10115422; https://journals.plos.org/plosbiology/article?id=10.1371%2Fjournal.pbio.3002112:
  "nearly all published AAV capsids that were selected for their ability to cross the BBB in mice leverage
  either the LY6A or LY6C1 protein, which are not present in primates.").
- VCAP-102 uses ALPL and transcytoses
  (https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_Spring_2024_03_Hoffman_FRIDAY_4-26.pdf:
  "ALPL ectopic expression increased transcytosis of VCAP-102 >100-fold in a transwell model."; and
  https://ir.voyagertherapeutics.com/news-releases/news-release-details/voyager-therapeutics-presents-data-second-generation-tracertm:
  "Voyager developed a transcytosis model expressing the VCAP-102 receptor in cultured cells and demonstrated
  that VCAP-102 and second-generation capsids, but not the AAV9 capsid, exhibited efficient transcytosis.").
- AAV9-X1.1 and CAP-Mac use LRP6 for BBB entry
  (https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518: "confirming the necessity of LRP6 for BBB capsid entry in
  vivo").
- AAV9 and AAV2 are the retained/intracellular-class controls (AAV9 does not bind LY6A;
  https://pmc.ncbi.nlm.nih.gov/articles/PMC10115422: "As expected, AAV9 showed no evidence of binding at any
  concentration").

## 3. Baselines and anchor

Baseline (published state of the art on the same axis): ten AlphaFold-Multimer models per receptor competition
matrix in APPRAISE-AAV (https://pmc.ncbi.nlm.nih.gov/articles/PMC10115422: "Matrices ranking AAV peptides by
their average competition metric over 10 replicate conditions for LY6A, LY6C1, and mouse CA-IV."), plus two
LRP6 peptide complexes (5 models each) in
https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518. Our shallow arm (144 models) is the minimal-compute
baseline.

Anchor (reproduced before library spend): rebuild the published PHP.eB peptide–LY6A complex. Published numbers:
capsid-model RMSD 0.36 Å to PDB 7WQO, 1.36 Å in the engineered loop
(https://pmc.ncbi.nlm.nih.gov/articles/PMC10115422: "RMSD (root mean square deviation) between the
computational PHP.eB model and a cryo–electron microscopy (cryo-EM)–based model [Protein Data Bank (PDB) ID:
7WQO] is 0.36 Å. RMSD increases in PHP.eB's engineered loop to 1.36 Å."), and the validated contacts: peptide
Pro5′/Phe6′ and LY6A Ala58 (mutation A58R disrupts infectivity; same source). Tolerance: capsid-fragment RMSD
≤ 1.5 Å and ≥2 of the 3 named contacts within 5 Å. Independent code: the RosettaRemodel integrative pipeline of
Shay et al. 2023.

## 4. Compute axis, arms, predictions

- Axis quantity: capsid–receptor pose models computed per panel sweep (docked or AlphaFold-Multimer).
- Levels: 144 (2 per pair), 720 (10 per pair), 2,880 (40 per pair = 20 docking poses + 20 AlphaFold seeds).
- Held fixed: 12 capsids, 6 receptors, constructs, ColabFold settings, docking search space, motif definition
  (15 Å / 30°), phenotype labels, 8×A100 hardware.

Measured quantity: motif_gap = (share of cognate/transcytosis-competent pairs whose dominant pose cluster is
GPI-engaging at the 3-fold) minus (share of non-cognate pairs so classified), computed at each level.

- if_lever: at 2,880 models the gap ≥ 0.50 while at 144 models it is < 0.25 (compute changed the answer).
- if_not: the gap stays within 0.15 of its 144-model value at all depths.
- Decision: paired on the same 72 pairs; if_lever if gap rises ≥ 0.25 with disjoint bootstrap 95% intervals;
  if_not if it moves < 0.15 and per-pair κ ≥ 0.8; else unsure.
- Noise rule: 5 seeds vote per pair; κ < 0.8 marks a pair unresolved; paired bootstrap over 72 pairs; a
  fresh-seed medium rerun must reproduce the gap within ±0.10 (noise floor).
- Expected: if_not. Why: insert location already fixes the 3-fold site
  (https://pmc.ncbi.nlm.nih.gov/articles/PMC12682079) and AlphaFold-Multimer poses for these weak interfaces
  vary by software version (https://pmc.ncbi.nlm.nih.gov/articles/PMC10115422: "the predicted binding pose for
  PHP.C2 peptide with LY6C1 was found to vary with the version of AlphaFold-Multimer used"), so extra poses add
  noise rather than a converged signature.

Why not expect the lever: AlphaFold-Multimer "failed to capture direct contact between fLY6A and PHP.eB capsid
in either monomer or trimer configurations" and integrative modeling was needed
(https://pmc.ncbi.nlm.nih.gov/articles/PMC10115422) — sampling depth is not the bottleneck; interface fidelity
is.

## 5. Numbers (basis in brackets)

- n_capsids = 12 [DESIGN], n_receptors = 6 [DESIGN], n_pairs = 72 [DERIVED]
- poses per pair: 2 / 10 / 40 [DESIGN] → n_pose_shallow = 144, n_pose_med = 720, n_pose_deep = 2,880 [DERIVED]
- af_seeds_deep = 20, dock_poses_deep = 20, af_jobs_deep = 1,440 [DERIVED: n_pairs * af_seeds_deep]
- af_job_min = 12 min [PROXY: "~1 to 2 min on A100-40GB" for no-MSA ≤600 aa at
  https://tools.ranomics.com/help/tools/colabfold; our jobs add MMseqs2 MSAs, 5 models, up to 20 recycles,
  ~250–400 residues] — measured_by p1_pilot, gate ≤ 20 min
- anchor_job_min = 30 min [GUESS: published anchor complex is ~1,370 residues
  (https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518 uses LRP6 20–1370), longer than library jobs]
- dock_job_min = 30 min CPU [GUESS: global rigid-body search of a ~250-residue ectodomain on a VP trimer]
- md_ns_per_gpu_day = 240 [PROXY: GROMACS 2024 on A100, system 3 (protein in membrane, 80,289 atoms) =
  265.8 ns/day at https://hpc.fau.de/2024/08/13/gromacs-2024-1-on-brand-new-gpgpus/; ours is ~50k atoms of
  receptor+loop in water without a membrane]
- md_runs = 20, md_ns = 20, md_atoms = 50,000 [DESIGN]
- usd_per_gpu_h_a1008 = 1.99 [CITED: https://lambda.ai/pricing 8x tab "NVIDIA A100 SXM | VRAM/GPU 40 GB | vCPUs
  124 | RAM 1800 GiB | STORAGE 5.8 TiB SSD | PRICE/GPU/HR* $1.99"]
- prior_models_per_peptide = 5, prior_peptides = 2, prior_models = 10 [CITED/DERIVED:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518]
- Decision numbers: axis_cutoff_a = 15 Å, gpi_angle_deg = 30, gap_threshold = 0.25, kappa_min = 0.8,
  noise_gap = 0.10, anchor_rmsd_a = 1.5 [DESIGN]

## 6. Cost (Lambda on-demand; budget_usd = 1,000; fs_usd_gib_month = 0.2)

Rates: 8×A100 SXM 40GB = $1.99/GPU-h → $15.92/instance-h; 1×A100 SXM 40GB = $1.99/instance-h.

| line | hours (time box) | need | rate | $ |
|---|---|---|---|---|
| l_p0_setup | 2 | 1.5 | 1×A100 | 3.98 |
| l_p1_pilot | 3 | 2.5 | 8×A100 | 47.76 |
| l_p2_shallow | 4 | n_pairs*af_job_min/60/8+1 = 2.8 | 8×A100 | 63.68 |
| l_p3_deep | 36 | (af_jobs_deep−n_pairs)*af_job_min/60/8 = 34.2 | 8×A100 | 573.12 |
| l_p4_md | 8 | md_runs*md_ns/md_ns_per_gpu_day*24/8 = 5.0 | 8×A100 | 127.36 |
| l_p5_analysis | 6 | 4 | 1×A100 | 11.94 |
| l_storage | — | storage_gib*fs_usd_gib_month*0.5 = 8 | storage | 8.00 |
| l_contingency | — | 120 | allotment | 120.00 |
| **total_stated** | | | | **955.84** |

spend_cap_usd = 1,000. Full-scale work the budget cannot buy: 100-capsid sweep (24,000 models, ~$4,776), 1 μs
whole-capsid–receptor–membrane MD (~$12,736), 200 seeds/pair with Amber relaxation (~$2,866).

## 7. Phases (execution order)

1. p0_inputs — fetch structures/sequences, build 72 pair FASTAs, axis precheck. Gate: n_capsids_ready ≥ 9.
2. p1_pilot — on 8×A100: reproduce the PHP.eB–LY6A anchor, time 6 representative pair jobs, 1 docking job,
   2 ns MD; write pilot/pilot_metrics.txt (script in pilot/run_pilot.py). Gate: af_job_min ≤ 20 min, else halve
   deep seeds. Stop rule: no library spend until the anchor contacts reproduce.
3. p2_shallow — 144 pose models (1 AF seed + 1 docking pose per pair); first motif gap. Timer 4 h.
4. p3_deep — deepen to 2,880 models (20 AF seeds + 20 docking poses per pair); the 720-model snapshot is the
   first 10 per pair. Timer 36 h or spend guard.
5. p4_md — 20 × 20 ns MD on top cluster reps. Timer 8 h.
6. p5_analysis — axis binning, motif_gap at 144/720/2,880 with paired bootstrap, report. Timer 6 h.

Restructuring: sequential part = none (each pair is an independent docking/folding job; only short refinements
chain within one pair). Method = none. Baselines timed anyway: baseline_sequential = one GPU running the 2,880
jobs back-to-back in one sorted colabfold_batch queue with the JAX compile cache on (≈ 576 GPU-h ≈ 24 days);
baseline_copies = 8 independent single-GPU workers on the same 8-GPU instance (the plan's actual mode).

## 8. Scope gaps and limits

- Nothing after binding is tested: endosomal sorting, lysosomal degradation, nuclear import (the option's
  narrowing).
- Whole-capsid dynamics, glycans, and the GPI lipid anchor are approximated, not simulated.
- Only 12 capsids and 6 receptors; hundreds of published capsids remain unsampled
  (https://journals.plos.org/plosbiology/article?id=10.1371%2Fjournal.pbio.3002112 reports "hundreds of
  capsids").
- No new wet-lab transcytosis data; labels come from published work.
- Ishan ASGCT poster (the option's cited URL) was fetched but its PDF text could not be extracted in this
  session; its transcytosis-model claim is instead cited from Voyager's open press release and the Hoffman
  poster PDF.

## 9. Local runs

No shell tool is available in this session, so no code was executed locally and no number is MEASURED. The
pilot script that phase p1_pilot runs on the Lambda instance is saved at pilot/run_pilot.py and will write
pilot/pilot_metrics.txt. All runtime inputs are PROXY or GUESS with measured_by pointing at p1_pilot or
p0_inputs.

## 10. Record field checks

question 23 words; hypothesis 20; if_lever 19; if_not 25; anchor.what 19; test_summary 34; closest_prior 22;
left_open 23; limits 21; sequential_part 18; method "none". Budget referenced as budget_usd; filesystem price
as fs_usd_gib_month. total_stated 955.84 USD under spend_cap_usd 1,000.
