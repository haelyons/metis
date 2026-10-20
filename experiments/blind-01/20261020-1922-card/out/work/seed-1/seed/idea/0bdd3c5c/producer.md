# Producer working file — option B1

Title: Mapping AAV capsid-receptor interactions to explain barrier transcytosis versus intracellular retention

Root question: Can molecular mapping of AAV capsid-receptor interactions on brain microvascular endothelial cells determine which AAV variants transcytose across the blood-brain barrier versus remain intracellular, and for which capsid-receptor binding signatures?

## What we build (concrete)

1. `labels.csv` — matched table: (capsid, receptor, phenotype transcytosis=1 / retention=0, assay type, source). Extracted
   by hand from open-access papers. Pilot seed of 15 rows already written at `pilot/labels_pilot.csv` (9 transcytosis, 6
   retention, 12 distinct capsids).
2. `signatures` — for each capsid–receptor pair: a complex model (OpenFold2/AlphaFold-style prediction of the capsid
   variable-region construct against the receptor ectodomain domain), then a 5 Å inter-chain contact fingerprint,
   buried-area and contact-potential features. Receptor panel: AAVR PKD1–5, LY6A, LY6C1, CA-IV, TfR1, ALPL, LRP6 (7).
3. Classifier: regularized logistic model predicting transcytosis vs retention from binding-signature features,
   evaluated leave-one-capsid-family-out (LOCO), 5 CV seeds, 1000 paired bootstraps.
4. Arms: (A) full binding signatures; (B) sequence-only; (C) receptor-affinity-rank only; (D) row-shuffled signatures.
5. Compute axis: number of capsid–receptor pair signature evaluations in the scored panel — 250 / 1,000 / 4,000.
   Accuracy is measured at each level. This directly tests whether the gap is compute or labels.

## Why this is the gap

- Merkel et al. show the phenotype pair the question names, in primary human brain endothelium: "Results of our in vitro
  studies indicate that AAV9 penetrates BMVEC barriers more effectively than AAV2, but has reduced transduction
  efficiency." https://pmc.ncbi.nlm.nih.gov/articles/PMC5298820
- Huang et al. give matched receptor-binding + transwell transport for a few capsids: "Significantly more BI-hTFR1 was
  actively transported to the bottom chamber than AAV9 or AAV2 (Fig. 3B)."
  https://pmc.ncbi.nlm.nih.gov/articles/PMC10769326
- Lin et al. show binding is not transcytosis: "Transcytosis is a necessary third step for BBB crossing (Figure 1B,
  step 3). Importantly, not all internalized AAVs complete this process."
  https://pmc.ncbi.nlm.nih.gov/articles/PMC12942408 — and top in-vitro binders (Alpha 48/49/62) failed in vivo while
  lower-ranked IV68/IV77 transcytosed.
- AAV1-PHP.B binds LY6A but does not cross: "However, unlike AAV9-PHP.B, this AAV1-based vector does not penetrate the
  blood-brain barrier." https://pubmed.ncbi.nlm.nih.gov/34346767
- Structural contacts are known and citable (anchor): "Residues in strands F/G and the CD loop of PKD1 interact directly
  with AAV5, whereas residues in strands B/C/E and the BC loop of PKD2 make contact with AAV1."
  https://pmc.ncbi.nlm.nih.gov/articles/PMC6704107 and "Wt AAVR binds to AAV1 with a KD value of 13.9 nM (Fig. 3f,
  Supplementary Fig. 6k–x), which is higher than the binding affinities of AAVR with AAV2 and AAV5." (same page)
- Receptor-dependent transwell recapitulation exists but for 2 capsids: "we generated a transwell model using
  Madin-Darby Canine Kidney (MDCK) cells overexpressing VCAP-102 receptor and showed that this cell line allowed very
  efficient transcytosis of VCAP-102 capsids, but not the parental AAV9."
  https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf

So: labels exist in the tens, in scattered panels; nobody has matched binding signatures + transcytosis/retention labels
at scale. The compute plan spends money on densifying the *signature* panel while the *label* table is what limits the
answer — which is exactly what the compute-axis test measures.

## Prior work nearest the decision (novelty)

ALICE (bioRxiv 2024/2026) is the nearest in-silico mapping of capsid-receptor engagement to CNS outcome:
"A total of 6,387 capsid sequences were compiled to train and test the evaluation model of ALICE-X, which predicts both
production fitness and hTfR1 binding capability (see Source data for full list of sequences)."
https://www.biorxiv.org/content/10.1101/2024.10.11.617764v2
It does not classify transcytosis vs endothelial retention, and does not report accuracy vs number of scored pairs.
Also relevant: AlphaFold-based capsid–receptor ranking precedent in the Caltech thesis
https://thesis.caltech.edu/15153/01/Xiaozhe_Ding_Caltech_Thesis_final.pdf ("applying AlphaFold-enabled in silico methods
to rank capsids against identified receptors and generate capsid-receptor binding models").

## Anchor (how we know the pipeline is right)

1. Contact recovery: predicted AAV1–PKD2 interface must recover the published cryo-EM contact residue sets
   (PKD2 strands B/C/E + BC loop; capsid loops listed in Zhang 2019) at ≥ 0.80 recall within 5 Å.
2. Affinity order: predicted interface score must rank AAV1–AAVR tighter than AAV2–AAVR (published KD 13.9 nM vs 57 nM,
   Zhang 2019).
3. Parallel-vs-sequential agreement: batch 4,000-pair answer vs four-round sequential answer within 0.03 balanced
   accuracy.
Independent code: a second 5 Å neighbor-search contact script (Biopython) over the same PDB files.

## Restructuring

- sequential_part: adaptive selection rounds — each of 4 rounds waits on the previous model before scoring its 250 pairs.
- method: pair signatures do not depend on the model, so all four rounds' pairs are scored in one batch instead of
  sequentially.
- condition: batching pays only if stratified-random panels cover signature space about as well as uncertainty-picked
  panels. Cheap check in p3_pilot: |accuracy_random − accuracy_uncertainty| ≤ 0.05 on the labeled set.
- baseline_sequential: 4-round active-learning loop (score the 250 most-uncertain pool members per round, retrain),
  timed on 2×H100.
- baseline_copies: two independent 250-pair scoring copies, one per GPU on the same 2×H100 instance, timed and
  hash-checked.

## Cost (Lambda on-demand, read 2026-10-20)

Rates (from https://lambda.ai/pricing):
- r_h100x2: 2× NVIDIA H100 SXM 80 GB @ $4.19/GPU-h → $8.38/h
- r_h100x8: 8× NVIDIA H100 SXM 80 GB @ $3.99/GPU-h → $31.92/h
- r_a100x1: 1× NVIDIA A100 SXM 40 GB @ $1.99/h
- r_a6000x1: 1× NVIDIA A6000 48 GB @ $1.09/h
- fs_usd_gib_month = $0.20/GiB-month (price sheet; example text: "at a rate of $0.20 per GiB per month")

Work estimate per pair-seed = 20 s (PROXY: OpenFold2 v2.4.0 H100 TensorRT pipeline_time 20.03 s for a 304-residue chain,
https://docs.nvidia.com/nim/bionemo/openfold2/2.4.0/performance.html; differs: NIM 5-model/2-trial pipeline vs our
single-model single-seed, single chain vs capsid–receptor complex).

Wall-hour needs (4 seeds/pair):
- 250 pairs on 2 GPUs: 250*4*20/3600/2 = 2.78 h
- 1,000 pairs on 2 GPUs: 11.11 h
- 4,000 pairs on 8 GPUs: 11.11 h

Time boxes (timer ended):
| line | phase | rate | hours | need | usd |
| l_smoke | p_setup | r_a6000x1 | 2 | 0.5 | 2.18 |
| l_extract | p1_data | r_a6000x1 | 6 | 3 | 6.54 |
| l_anchor | p2_anchor | r_a100x1 | 4 | 2 | 7.96 |
| l_panel250 | p3_pilot | r_h100x2 | 6 | 2.78 | 50.28 |
| l_panel1000 | p4_mid | r_h100x2 | 12 | 11.11 | 100.56 |
| l_seq | p4_mid | r_h100x2 | 14 | 11.11 | 117.32 |
| l_copies | p4_mid | r_h100x2 | 4 | 2.78 | 33.52 |
| l_panel4000 | p5_large | r_h100x8 | 16 | 11.11 | 510.72 |
| l_train | p6_model | r_a100x1 | 8 | 1 | 15.92 |
| l_ablation | p6_model | r_h100x2 | 4 | 1 | 33.52 |
| l_storage | p5_large | storage 40 GiB × 0.2 × 0.5 mo | | | 4.00 |
| l_contingency | p5_large | allotment | | | 60.00 |
Total: **$942.52**. spend_cap_usd = 1000.

Fallback line: l_panel1000_only (12 h on r_h100x2 = $100.56) instead_of l_panel4000 if the p3_pilot gate fails.
Stretch: l_extra_seeds (2 h on r_h100x2 = $16.76) if accuracy at 4,000 pairs lands between 0.65 and 0.80.

## Pilot (local)

`pilot/pilot_pipeline.py` + `pilot/labels_pilot.csv` are written. This session has no shell tool, so the pilot was NOT
executed; every pilot-dependent number is basis GUESS with measured_by naming the phase that runs the script. The script
prints: n_labels_pilot, fingerprint_sec_per_pair, cv_loco_sec, acc_synthetic_{signatures,seqonly,shuffled},
panel_{random,uncertainty}_acc, machine.

## Gates

- p1_data: n_labels_extracted ≥ 12, else drop the classifier claim and deliver the dataset + descriptive signature map.
- p2_anchor: contact_recovery_min ≥ 0.80, else stop (pipeline wrong).
- p3_pilot: sec_pair_seed ≤ 60 s measured, else cut seeds to 2 and run only the 1,000-pair level.
- p3_pilot condition: |random − uncertainty panel accuracy| ≤ 0.05, else fall back to the sequential baseline strategy.

## Predictions

- measured quantity: LOCO balanced accuracy of the transcytosis-vs-retention classifier at each panel size.
- if_lever: at 4,000 pairs accuracy ≥ 0.80, ≥ 0.10 above the 1,000-pair level and ≥ 0.15 above sequence-only; batching
  reaches it in 16 h vs 64 h for four sequential rounds.
- if_not: accuracy ≤ 0.65 at 250, 1,000 and 4,000 pairs; sequential selection hits the same ceiling at 1,000 pairs.
- expected: if_not — matched labels number in the tens, so more scored pairs densify features without adding label
  information.
- noise: 5 CV seeds × 1,000 paired bootstraps; real only if 95% CI of paired accuracy difference excludes zero and the
  sign holds in ≥ 4/5 seeds.

## Outside budget

- ~60 h researcher time (label extraction, coding, reading).
- Optional wet-lab: hBMVEC Transwell panel for ~12 predicted variants (~$8,000) — this is what would actually close the
  gap; not Lambda, not paid here.
- 1 h on the shared 4-core local host for the pilot.

## Scope gap

- No new wet-lab binding or transcytosis measurements; labels stay as published.
- Species-specific receptor differences (mouse LY6A vs human CA-IV) only as far as published panels go.
- Retention kinetics are not measured; only binary transcytosis-vs-retention labels.
