# Working notes — programmes that would consume the capsid–receptor enumeration card

Card: exhaustive capsid–receptor complex enumeration (docking + AF-Multimer), 72 pairs ×
144/720/2,880 pose models, to find a shared 3-fold-axis GPI-receptor engagement motif that
marks BBB transcytosis vs intracellular retention. Phenotype labels cited as [s_alpl].

## Key facts found (with URLs)

### Origin of the method the card scales
- APPRAISE-AAV = Gradinaru Lab (Caltech), Xiaozhe Ding et al. "Automated Pairwise Peptide
  Receptor Analysis for Screening Engineered AAVs". Repo: https://github.com/GradinaruLab/APPRAISE
  (fork of xz-ding/APPRAISE). README: "APPRAISE ... predicts the receptor binding propensity of
  engineered proteins based on high-precision protein structure prediction tools, such as
  AlphaFold2-multimer." Commits page shows Apr 9, 2026 commits ("1.3.0 package",
  "Updating Colab notebook for compatibility to Boltz-1, Chai-1, and Openfold3",
  "Colab instruction update", "distribution 1.2.6"). ACTIVE.
- Ding et al., Mol Ther 2024 (10.1016/j.ymthe.2024.04.003),
  https://www.cell.com/molecular-therapy-family/molecular-therapy/fulltext/S1525-0016(24)00219-3:
  "when AlphaFold-Multimer was used, 10 independent models were generated for each competition
  because AlphaFold-Multimer gives five different predictions for each input"; HT-APPRAISE
  screen of 100 capsid variants "took 24 h using three parallel Google Colaboratory GPU
  sessions"; ~"0.1–1 GPU minute per peptide-LY6A model". Trained/evaluated on 22 AAV9-based
  variants vs LY6A (ROC AUC 0.838 APPRAISE 1.2).
- Shay et al., Sci Adv 2023 (10.1126/sciadv.adg6618), PMC10115422: applied APPRAISE-AAV to
  LY6A, LY6C1, CA4; "Each model was recycled three times, and 10 models were generated from each
  competition"; "Some false negatives were also observed, however, as in 9P08 with LY6A or 9P36
  with CA-IV." Created AAV-PHP.eC (LY6C1-binding) and identified CA4 (primate-conserved).
- Shay et al., Nat Commun 2024 (10.1038/s41467-024-52149-0): human cell-surface AAV interactome;
  LRP6 = BBB transcytosis receptor; "Five structure models were produced using a protocol with up
  to 20 recycles" (AF-Multimer v3, A100) for LRP6–VR-VIII complexes; validated on macaque and
  human primary brain microvascular endothelial cells (PBMECs).
- Lin et al., Cell Rep 2025 (10.1016/j.celrep.2025.116419), published 2025-10-31: AAV-hCA4-IV77
  (100x brain transduction vs AAV9 in humanized mice); receptor-directed on-column selection +
  humanized-mouse in vivo; notes transcytosis mechanics "poorly understood".

### [s_alpl] source = Voyager Therapeutics (TRACER / VCAP-102 / ALPL)
- Moyer et al., Mol Ther 2025 (10.1016/j.ymthe.2025.04.046),
  https://www.cell.com/molecular-therapy-family/molecular-therapy/fulltext/S1525-0016(25)00373-9:
  TRACER RNA-guided capsid evolution → VCAP-102 (AAV9 + 6-mer insert in VR-IV, 3-fold spike);
  "We identify alkaline phosphatase (ALPL) as the primary receptor used by VCAP-102 to cross the
  BBB and demonstrate that direct binding of VCAP-102 to human ALPL can initiate receptor-mediated
  transcytosis in a cell barrier model." ALPL = GPI-anchored. Receptor ID via Retrogenix cell
  microarray + lentiviral ORFeome transduction screen. SPR KD ~20 nM. MDCK Transwell: "Ectopic
  expression of human ALPL induced a dramatic >100-fold increase in the transcytosis of VCAP-102
  while it had no measurable impact on AAV9 migration". Library scale: "the naive library
  contained approximately 4E7 individual capsid variants". Cryo-EM: insert density at apex of
  VR-IV at 3-fold axis. High-performance variants share SPH motif at 456–458 (VR-IV).
- Voyager 10-K (FY2025): "We subsequently utilized these BBB-penetrant capsids to identify the
  receptors by which the capsids enter the BBB. We have identified multiple receptors, including
  alkaline phosphatase, or ALPL, that are capable of transporting a large biologic molecule, such
  as a capsid, across the BBB." NeuroShuttle platform: first shuttle leverages ALPL.
  https://www.sec.gov/Archives/edgar/data/1640266/000110465926025197/vygr-20251231x10k.htm
- Voyager pipeline page (fetched 2026-10): VY1706 (TRACER capsid + anti-tau siRNA) — "At AAIC
  2026, Voyager presented 6-month good laboratory practice (GLP) toxicology non-human primate
  (NHP) data showing VY1706 was well tolerated and resulted in sustained tau protein reduction by
  up to 75% in key AD brain regions following a single intravenous (IV) dose." "Status: Expected
  to begin dosing in adults with early AD in Q4 2026." ALPL-VYGR-NeuroShuttle in wholly-owned
  pipeline. https://www.voyagertherapeutics.com/pipeline-overview/ — ACTIVE.
- May 2026 VY1706 deck: "100% conservation of predicted capsid-ALPL interacting residues";
  "IND process on track for Q2 2026; clinical entry expected H2 2026".
  (search-extracted from PDF at voyagertherapeutics.com)

### Dyno Therapeutics (multi-mechanism BBB capsid portfolio)
- https://www.dynotx.com/gene-delivery: Dyno-9zh (2026) "Engages human Alkaline Phosphatase
  (ALPL) receptor for BBB-crossing, supporting translation to humans"; "Best capsid when compared
  head-to-head with other ALPL-targeting capsids in mouse and NHP"; Dyno-yp2 (2026) hTfR1;
  Dyno-ahq (2025) "Highly conserved candidate receptor"; Dyno-hc9 (2023, bCap 1).
- Dyno-yp2 launch (2026-01-12): "Dyno's novel generative AI models, trained on billions of in vivo
  measurements, most recently accelerated with NVIDIA hardware and software, using Hopper GPUs on
  DGX Cloud and libraries such as TransformerEngine, integrate sequence- and structure-based
  approaches to engineer functional capsids for new and promising BBB-crossing mechanisms with
  exceptional efficiency." Also: "Dyno is advancing capsids that engage additional BBB transport
  pathways, including several BBB-receptors discovered by Dyno, as well as approaches involving
  alkaline phosphatase (ALPL)".
  https://www.dynotx.com/news/dyno-therapeutics-launches-dyno-yp2-a-top-performing-tfr1-mediated-aav-capsid-to-further-diversify-cns-delivery-portfolio
- Roche partnership (2024-10-24): "LEAP ... paired with the capability to make billions of in vivo
  sequence-function measurements each month".
  https://www.dynotx.com/news/dyno-therapeutics-forms-new-strategic-partnership-with-roche-to-advance-aav-gene-therapy-vectors-for-neurological-diseases
- ACTIVE (Dyno-9zh/Dyno-n96 "Launched at ASGCT 2026"; "© Dyno 2026").

### Also noted but not selected (or for gaps)
- Capsida Biotherapeutics: "We have identified novel human blood-brain barrier receptors that bind
  our engineered capsids and are conserved between primates and humans" (capsida.com/science-innovation);
  ASGCT 2025 deck: NR001–NR005 receptors, plate-/bead-based receptor binding platform, "NR004:
  endothelial-specific", predicted binding sites; IND clearances CAP-002/CAP-003 (June 2025).
  Same consumer class as Dyno; kept as gap/footnote because Dyno's ALPL portfolio matches [s_alpl].
- Lir "Starfish" capsid-structure/docking pipeline (lirtx.com): full-capsid structure gen +
  "downstream tasks such as molecular docking" at library scale — a tools consumer; footnote only.

## Programme selection (1–3)
1. Voyager Therapeutics — step: identify the receptor used by a TRACER capsid and show
   receptor-mediated transcytosis (cell barrier model) = exactly transcytose-vs-retain call.
2. Gradinaru Lab / APPRAISE-AAV — step: AF-Multimer pairwise peptide–receptor pose competition
   ranking (the computation the card scales from 10 to 2,880 models).
3. Dyno Therapeutics — step: structure+sequence-based engineering and mechanism assignment for
   multi-mechanism BBB portfolio (ALPL, TfR1, discovered receptors).

## already_done checks
- Voyager: PARTLY — receptor ID + Transwell transcytosis for VCAP-102/ALPL, cryo-EM 3-fold insert
  density, "predicted capsid-ALPL interacting residues" cited (May 2026 deck), but no exhaustive
  pose-depth enumeration across a capsid panel with retention labels.
- Gradinaru/APPRAISE: PARTLY — 10-model competitions on LY6A/LY6C1/CA4 matrices, PHP.eB–LY6A
  pose work, 5-model LRP6 complexes + cryo-ET; false negatives documented; NO 144–2,880 depth
  sweep and NO shared-motif-vs-transcytosis test.
- Dyno: UNKNOWN — proprietary; public record shows mechanism validation in vivo (head-to-head
  ALPL capsids) and structure-based generative design, no public exhaustive pose enumeration.

## Gaps to report
1. No published pose-depth scaling for capsid–receptor models (closest: 10/competition, 5×20
   recycles); the card's 144–2,880 arms have no comparator.
2. Transcytosis-vs-retention labels per pair are scarce (MDCK Transwell for VCAP-102±ALPL only;
   most programs use in vivo brain transduction as readout).
3. APPRAISE models isolated VR-VIII peptides, not full capsid/3-fold spike with GPI anchor and
   membrane; avidity-dependent weak contacts evade prediction (card's own caveat).
4. Species gaps: LY6A/LY6C1 mouse-restricted; 9P31/9P36 bind mouse not primate CA4; ALPL
   conserved — motif generality across GPI receptors unproven.
5. Dyno's and Capsida's structural pipelines proprietary; Capsida NR001–005 and Lir Starfish are
   additional consumers not fully assessed here.
