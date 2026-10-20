# Working plan — Structural coverage of capsid–receptor–glycan complexes

Option: "Structural coverage of capsid–receptor–glycan complexes".
Root question: Can molecular mapping of AAV capsid–receptor interactions on brain microvascular
endothelial cells determine which AAV variants transcytose across the BBB versus remain intracellular,
and for which capsid–receptor binding signatures?

## What this run can and cannot do here

- The environment exposes web fetch/search and file read/write only; no shell, so no local code run
  and no MEASURED numbers. Every throughput figure is CITED or PROXY and is re-measured on Lambda
  in phase `p_pilot` (threshold `md_ns_gpu_day`), or guessed and re-measured in `p_af`.
- budget_usd = 1,000 of Lambda on-demand credit. spend_cap_usd = 1,000.
- fs_usd_gib_month = 0.2 (price sheet filesystem rate).

## What to build (concrete)

1. Panel. Six capsid variable-region peptides: AAV9 VR-I/VR-V loop set (negative), AAV9-X1.1 X1
   VR-VIII peptide, CAP-Mac VR-VIII insertion, MaCPNS2 VR-VIII insertion, AAV-BI30 peptide,
   VCAP-102 VR-VIII peptide. Four receptor domains: LRP6 E1E2, LRP6 E3E4, AAVR PKD2, human ALPL
   ectodomain. 6 x 4 = 24 AlphaFold-Multimer complexes, 5 models each, up to 20 recycles
   (the exact method precedent of PMC11381518 Fig. 4c).
2. MD systems. Six labelled pairs x two pH values (7.4, 5.5) = 12 conditions. Each: predicted
   peptide–domain complex + key glycan (galactose or the ALPL N-glycan) + explicit water,
   150 mM NaCl, ~80,000 atoms (benchMEM is 81,743 atoms at 2 fs), protonation states set per pH.
   Labelled pairs: X1–LRP6E1 (transcytoses), CAP-Mac–LRP6E1 (transcytoses), VCAP-102–ALPL
   (transcytoses, pH switch), AAV9 peptide–LRP6E1 (no binding), AAV9 peptide–ALPL (no binding),
   X1–LRP6E3E4 (negative domain control).
3. Ensemble. 32 independent 10-ns GROMACS replicas per condition (384 replicas, 3.84 us aggregate),
   one replica per V100 GPU, random velocities. Nested subsets N = 8, 16, 32 give the compute axis.
4. Baselines (both timed). (a) Sequential: one 320-ns trajectory per anchored condition on one V100
   (same aggregate simulated time as 32 x 10 ns), GROMACS GPU-resident (`-pme gpu -update gpu
   -bonded gpu`), 2 fs, h-bonds constrained, one MPI rank, 8 OpenMP threads. (b) Copies: the 32
   independent 10-ns replicas run side by side on the same GPUs, timed with and without reseeding.
5. Score. Per pair: epitope contact set + buried surface area from AlphaFold; per condition: contact
   survival over the 10-ns replicas at each pH; pH ratio = survival(7.4)/survival(5.5). One
   classification score per pair; AUC over the six labelled pairs at N = 8, 16, 32.

## Check it is right

- Anchor (before MD): AlphaFold-Multimer must reproduce the published result that X1 and CAP-Mac
  peptides bind LRP6 E1 and not E3E4 (PMC11381518 Fig. 4c–d; SPR confirmed E1E2 not E3E4).
  Tolerance: top-ranked of 5 models docks E1 not E3E4 for both peptides.
- pH benchmark: ALPL–VCAP-102 is the only measured pH-resolved pair (K_D ≈ 20 nM at pH 7.4, rapid
  dissociation at pH 5.5; Moyer et al. bioRxiv 2024.03.12.584703). The computed pH ratio must be
  > 2 and in the same direction (release at low pH).
- Sequential anchor: ensemble contact occupancy within ±0.15 of the 320-ns trajectory.
- Noise: split-half AUCs over disjoint 16-replica halves must differ by < 0.10.
- Throughput: pilot-measured ns/day must be within 2x of the Kutzner-derived proxy before the
  main spend, else the ensemble is rescaled (scenarios scen_slow_md / scen_fast_md).

## Restructuring

- Sequential part: one MD trajectory is 10^9–10^12 ordered 2-fs steps, each frame waiting on the
  previous coordinates (Jones et al., PMC9281402).
- Method: many short independent trajectories at once; within-state contacts decorrelate far faster
  than inter-state transitions, so weak scaling of replicas beats strong scaling of one run
  (Kasson, PMC9476681; Kutzner 2019 arXiv:1903.05918; adaptive sampling scaled linearly to 5,000
  parallel simulations per iteration, Bowman et al., PMC3637129).
- Condition (checked in `p_pilot`): contact-set autocorrelation time tau_contact_ns <= 2 ns, i.e.
  replicas decorrelate inside a 10-ns window. Else switch to 8 replicas x 40 ns and 6 conditions.

## Cost (Lambda on-demand, 8-GPU instances)

Rates: r_v100_8 = 8 x Tesla V100 16 GB at $0.79/GPU-h = $6.32/h; r_a100_8 = 8 x A100 SXM 40 GB at
$1.99/GPU-h = $15.92/h.

| line | phase | hours (instance wall-clock) | rate | usd |
|---|---|---|---|---|
| l_setup | p_setup | 2 (time box) | r_v100_8 | 12.64 |
| l_af | p_af | 4 (time box; need 3) | r_a100_8 | 63.68 |
| l_pilot | p_pilot | 2 (time box; need 1.6) | r_v100_8 | 12.64 |
| l_ensemble | p_ensemble | 80 (time box; need 76.6) | r_v100_8 | 505.60 |
| l_baselines | p_baselines | 52 (time box; need 51.1) | r_v100_8 | 328.64 |
| l_score | p_score | 2 (time box) | r_v100_8 | 12.64 |
| l_storage | p_score | 50 GiB x fs_usd_gib_month | storage | 10.00 |
| total_stated | | | | 945.84 |

Optional: l_baseline_short (13 h, $82) instead of l_baselines if throughput is slow; l_replicas_extra
(26 h, $165) for 32 extra replicas on the four binder conditions if the AUC at N=32 lands between
0.75 and 0.9. spend_cap_usd = 1,000 stops all lines.

Throughput arithmetic (all DERIVED): mem_bench_aggr_ns_day = 300.76 (Kutzner 2019, Table 3:
2 x V100 node, aggregate of 2 independent MEM simulations, 81,743 atoms, 2 fs); md_ns_gpu_day =
300.76/2 = 150.38; replica_h = 10*24/150.38 = 1.596; ensemble_gpu_h = 32*12*1.596 = 612.9;
ensemble_inst_h = 76.6; baseline_agg_ns = 320; baseline_seq_h = 320*24/150.38 = 51.1.

## Predictions (same measured quantity)

Measured quantity: AUC of the computed score over the six labelled pairs, at N = 8, 16, 32
replicas, plus the ALPL–VCAP-102 pH contact-survival ratio.

- if_lever: at N = 32 the AUC is >= 0.9 and the pH ratio > 2, and the estimate matches the 320-ns
  sequential run; the answer is reached in ~51 instance-hours instead of 320 ns of serial waiting.
- if_not: at every N in {8, 16, 32} the AUC stays <= 0.75 and the pH ratio is ~1; the 320-ns run
  agrees, so more replicas do not change the answer — short replica ensembles cannot recover the
  signature at this system size.
- expected: unsure. Epitope geometry alone separates binders (PMC11381518), but 10-ns contact
  survival may be too short to recover the measured pH-5.5 release.

## Sources (exact sentences relied on)

- s_lrp6 (https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518/): "Representative AlphaFold models,
  from 5 structural models each of X1 and CAP-Mac peptides with up to 20 recycles, predict selective
  interaction with human LRP6 domain E1 (E1 and E2: teal, E3 and E4: yellow, AAV peptides: purple)."
- s_lrp6_spr (same URL): "SPR of mouse LRP6 extracellular domain fragments was consistent with the
  model predictions, with interaction observed for LRP6-E1E2 but not LRP6-E3E4 (Fig. 4d)."
- s_lrp6_pbmec (same URL): "AAV9-X1.1 was markedly more potent than its parent, AAV9, in the PBMECs
  from both species, and the LRP6 inhibitor Mesd selectively reduced AAV9-X1.1 potency back to AAV9
  levels."
- s_lrp6_cryo (same URL): "46 3D tomograms, composed of 41 such images each, yielded 85,135
  symmetry-expanded particles for sub-tomogram averaging."
- s_moyer (https://www.biorxiv.org/content/10.1101/2024.03.12.584703v1): "We observed direct
  capsid-receptor interaction in a cell-free assay using Surface Plasmon Resonance (SPR) analysis
  with recombinant ALPL, showing that VCAP-102 directly interacts with ALPL with an affinity (KD) of
  ∼20nm at pH7.4 (Fig. 4c). Rapid dissociation of the ALPL-VCAP-102 complex was observed at pH 5.5."
  (open bioRxiv preprint; the peer-reviewed Molecular Therapy version is paywalled, so the numbers
  are taken from the preprint.)
- s_moyer_abs (same URL): "VCAP-102 demonstrates a similar CNS tropism in cynomolgus macaque,
  african green monkey, marmoset and mouse, showing 20- to 400-fold increased transgene expression
  across multiple brain regions relative to AAV9." and "ectopic expression of ALPL is sufficient to
  initiate receptor-mediated transcytosis of VCAP-102 in an in vitro transwell model."
- s_jones (https://pmc.ncbi.nlm.nih.gov/articles/PMC9281402/): "The number of sequential operations
  needed to achieve these time scales can grow to be at least 10^9–10^12."
- s_kasson (https://pmc.ncbi.nlm.nih.gov/articles/PMC9476681/): "In a system with multiple
  metastable states and good separation of timescales, individual trajectories will decorrelate
  within a metastable state much faster than they transition between states."
- s_bowman (https://pmc.ncbi.nlm.nih.gov/articles/PMC3637129/): "Figure 1A shows that the wall-clock
  time efficiency of adaptive sampling scales linearly up to 5,000 simulations per iteration."
- s_kutzner (https://arxiv.org/html/1903.05918v1): "2 | Gold6148F × 2 ‡ | 2 × 20 | 2.4 | V100×2 |
  300.76 | 19.95 | 23 200" and "A benchmark protocol matching both requirements is: running N
  simulations on nodes with N GPUs in parallel, each using 1/N of the available CPU cores or hardware
  threads, and reporting the aggregate performance, i.e. the sum of the performances of the
  individual simulations."
- s_kutzner_ens (same URL): "problems that previously required the generation of a few long
  trajectories are nowadays often addressed by ensemble methods that instead need a large number of
  shorter trajectories."
- s_colabfold (https://pmc.ncbi.nlm.nih.gov/articles/PMC9184281/): "ColabFold's 40−60-fold faster
  search and optimized model utilization enables prediction of close to 1,000 structures per day on
  a server with one graphics processing unit."
- s_chimerax (https://www.rbvi.ucsf.edu/chimerax/data/alphafold-jan2022/afspeed.html): "1 minute to
  install ColabFold on Google Colab and 4 minutes to run 5 models." and "The table shows ColabFold
  1.5.5 is about 2 to 10 times faster than AlphaFold 2.3.2."
- s_lambda (https://lambda.ai/pricing): "NVIDIA Tesla V100 | VRAM/GPU: 16 GB | vCPUs: 88 | RAM:
  448 GiB | STORAGE: 5.8 TiB SSD | PRICE/GPU/HR: $0.79"
- s_lambda_a100 (https://lambda.ai/pricing): "NVIDIA A100 SXM | VRAM/GPU: 40 GB | vCPUs: 124 | RAM:
  1800 GiB | STORAGE: 5.8 TiB SSD | PRICE/GPU/HR: $1.99"
- s_lambda_fs (https://lambda.ai/pricing): "Filesystems are billed per GiB used per month in
  one-hour increments. For example, at a rate of $0.20 per GiB per month ..."
- s_bench (https://www.mpinat.mpg.de/grubmueller/bench): "benchMEM (82k atoms, protein in membrane
  surrounded by water, 2 fs time step)"

Pages fetched while planning (files_read): PMC11381518, PMC3637129, PMC9281402, PMC9476681,
mpinat.mpg.de/grubmueller/bench, lambda.ai/pricing, biorxiv.org/content/10.1101/2024.03.12.584703v1
(abstract page; the .full-text endpoint returned HTTP 429, so full-text sentences are quoted as
returned by web search over the same open URL), rbvi.ucsf.edu/chimerax/data/alphafold-jan2022/
afspeed.html, arxiv.org/html/1903.05918v1.

## Novelty

- closest_prior: adaptive-sampling MSMs matched one long villin run with up to 5,000 parallel
  simulations per iteration [s_bowman]; the capsid work used 5 AlphaFold models per peptide
  [s_lrp6]. prior_max_level = 5000 parallel simulations (same axis: independent parallel runs),
  decides: partly — parallel replicas are the efficient way to buy sampling below saturation,
  but nothing published decides whether the computed signature classifies transcytosis.
- left_open: whether computed pH-resolved contact lifetimes classify transcytosis versus retention
  at all; only ALPL–VCAP-102 has measured pH kinetics [s_moyer].

## Scope gap (what this budget cannot test)

Full glycosylated 60-mer capsids in water/membrane (fs_full_capsid, ~$7.3k at the proxied
throughput), true millisecond k_off per condition (fs_us_per_cond, ~$1.5k), and coverage of
hundreds of variants x many receptors (fs_many_variants, ~$65k) are outside budget_usd.
