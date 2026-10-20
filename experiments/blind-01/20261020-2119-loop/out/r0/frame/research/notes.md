# Working notes — programmes that would consume the card's result

Root question: can molecular mapping of AAV capsid–receptor interactions on brain microvascular
endothelial cells (BMECs) determine which AAV variants transcytose across the BBB versus remain
intracellular, and for which binding signatures?

Card's deliverable: computed capsid–receptor structures (AlphaFold-Multimer epitope geometry) plus
pH-resolved MD contact lifetimes from many short replicas, classified against transcytosis vs
retention. Compute axis: 8–32 independent 10-ns replicas per (peptide, receptor, pH) condition.
Predicted outcomes: (i) lever — 32 replicas reach AUC ≥ 0.9 and pH ratio > 2, matching a 320-ns run;
(ii) not a lever — AUC ≤ 0.75, no pH difference, more replicas do not help.

## The paper the card is built on (root sources)

- Shay TF, Jang S, Brittain TJ, ... Gradinaru V. "Human cell surface-AAV interactomes identify LRP6
  as blood-brain barrier transcytosis receptor and immune cytokine IL3 as AAV9 binder."
  Nat Commun 15:7853 (8 Sep 2024). https://www.nature.com/articles/s41467-024-52149-0
  - Six-capsid Retrogenix cell-microarray screen of >6400 proteins (>90% of human membrane proteome
    and secretome). Hits: LRP6 (AAV9-X1.1, CAP-Mac), IL3 (AAV9 family), GP2, FAM234A.
  - "We applied AlphaFold-Multimer to build models of LRP6-AAV interaction complexes, which predicted
    that the X1 and CAP-Mac VR-VIII peptides bind LRP6 YWTD domain 1 (Fig. 4c)."
  - Fig. 4c caption: "Representative AlphaFold models, from 5 structural models each of X1 and CAP-Mac
    peptides with up to 20 recycles, predict selective interaction with human LRP6 domain E1".
  - SPR: LRP6-E1E2 bound, LRP6-E3E4 not. This is the card's "check first" reproduction target.
  - In vivo: Lrp6 conditional KO abolishes AAV9-X1.1 brain endothelial tropism; human/macaque PBMEC
    assays with Mesd inhibitor; hPSC-derived neurons.
- Moyer TC, Hoffman BA, Chen W, Shah I, Ren XQ, et al. "Highly conserved brain vascular receptor ALPL
  mediates transport of engineered AAV vectors across the blood-brain barrier." Mol Ther (2025).
  https://www.cell.com/molecular-therapy-family/molecular-therapy/fulltext/S1525-0016(25)00373-9
  (Voyager Therapeutics; TRACER platform; VCAP-102).
  - SPR: VCAP-102 binds ALPL KD ~20 nM at pH 7.4; "Rapid dissociation of the ALPL-VCAP-102 complex was
    observed at pH 5.5 ... mechanism of capsid release ... triggered by the acidification of endosomes".
    This is the only measured pH-kinetics pair the card cites [s_moyer].
  - MDCK-Transwell transcytosis model: human ALPL ectopic expression gives >100-fold increase in
    VCAP-102 transcytosis, no effect on AAV9.
  - Library scale: ~4E7 naive capsid variants; 1,500 variants of interest after two NHP passages.

## Candidate programmes (1–3)

### 1. Voyager Therapeutics (TRACER capsid discovery / NeuroShuttle) — SELECTED
- Step: identify the receptor each BBB-penetrant TRACER capsid engages on brain vasculature and
  whether binding triggers receptor-mediated transcytosis, so cross-species/human-conserved capsids
  can be nominated for IV CNS gene therapies (VY1706 tau silencing, ALPL-VYGR-NeuroShuttle).
- Step quote (own page): pipeline-overview — "To address this problem, Voyager has discovered novel
  capsids and identified associated receptors that potentially enable exceptional delivery across the
  blood-brain barrier following intravenous dosing."
- How handled today: RNA-guided in vivo biopanning in cynomolgus macaques (TRACER), ~4E7-variant
  libraries → 1,500 variants of interest → focused library; SPR binding + pH 7.4/5.5 dissociation;
  MDCK-Transwell transcytosis; potency-assay cell lines overexpressing the capsid-specific receptor
  (ASGCT 2026 poster #3148). People: Capsid Discovery team (Tyler Moyer, Mathieu Nonnenmacher,
  Todd Carter CSO).
- Activity: active. Q2 2026 results 6 Aug 2026 — FDA cleared VY1706 IND (TRACER capsid), dosing
  expected Q4 2026; eight ASGCT 2026 presentations (Apr–May 2026).
- Already done: PARTLY — Voyager already measured the one pH-resolved kinetics pair (VCAP-102–ALPL)
  and a transwell transcytosis readout, but no computed pH-resolved MD contact-lifetime classifier.

### 2. Dyno Therapeutics — SELECTED
- Step: the BBB-mechanism layer of AI capsid design — which BBB transport receptor a designed capsid
  engages (hTfR1 for Dyno-yp2; ALPL for Dyno-9zh; other Dyno-discovered receptors) and whether
  binding is conserved to human, before licensing to CNS programs.
- Step quote (own page): Dyno-yp2 launch — "In parallel with its work on TfR1-mediated delivery, Dyno
  is advancing capsids that engage additional BBB transport pathways, including several BBB-receptors
  discovered by Dyno, as well as approaches involving alkaline phosphatase (ALPL), a compelling and
  distinct mechanism with translational relevance across species."
- How handled today: in vivo pooled screens of 10,000–10 million barcoded capsid sequences in mice/NHP;
  LEAP mixture-of-models design (19 designs replaced one high-throughput round); generative AI models
  trained on "billions of in vivo non-human primate measurements"; sequence- and structure-based
  approaches; receptor mechanism confirmed by binding to human/NHP orthologues and NHP biodistribution;
  Dyno Phi open agentic platform runs open-weight protein structure models.
- Activity: active. Launch of Dyno-9zh (ALPL) and Dyno-n96 plus platform updates at ASGCT 13 May 2026;
  further multi-mechanism muscle data announced 5 Oct 2026.
- Already done: UNKNOWN — no public evidence of pH-resolved MD contact-lifetime classification of
  transcytosis vs retention; their mechanism step is empirical binding + in vivo phenotype.

### 3. Gradinaru laboratory, Caltech (AAV receptor-mapping program) — SELECTED
- Step: unbiased capsid–receptor interactome mapping on human cell-surface/secreted proteome plus
  structural/computational epitope mapping, to explain which engineered capsids cross the BBB and
  which binding signature they use (LRP6, CA-IV, AAVR, LY6A...).
- Step quote (own paper): Nat Commun 2024 — "Here, we adapt an unbiased human cell microarray platform
  to determine the extracellular and cell surface interactomes of natural and engineered AAVs."
- How handled today: Retrogenix microarray of >6400 proteins (6019 plasma-membrane/secreted +
  397 heterodimers) for six-capsid pools; SPR domain fragments; AlphaFold-Multimer of peptide–domain
  complexes (5 models each); cryo-ET subtomogram averaging; cryo-EM of capsid–AAVR PKD2 complexes
  (2.2–3.1 Å, Brittain et al. 2026); in vivo Lrp6 conditional KO; human/macaque PBMEC and hPSC-neuron
  assays. Tools: AlphaFold-Multimer, cryo-EM (Caltech CLOVER), SPR/BLI (Protein Expression Center).
- Activity: active. Brittain et al., Mol Ther, 28 Mar 2026 (structural basis of liver de-targeting /
  neuronal tropism); Lin et al., Cell Reports, 31 Oct 2025 (human CA-IV-targeted AAVs); lab list has
  2026 bioRxiv/Science entries.
- Already done: PARTLY — the lab already ran the card's "check first" computation (AlphaFold-Multimer
  X1/CAP-Mac → LRP6 E1; SPR E1E2 vs E3E4). No pH-resolved MD contact lifetimes published.

## Cross-cutting facts for "practice" and "already done"
- Voyager = the card's [s_moyer] source; Gradinaru lab = the card's [s_lrp6] source. Both already run
  adjacent experiments; the novel part of the card is the MD contact-lifetime classifier and the
  transcytosis-vs-retention label across many pairs.
- Nobody has published a compute classifier validated against cell-level transcytosis for many
  capsid–receptor pairs. Structural pipelines (AlphaFold-Multimer, cryo-EM) are descriptive, not
  predictive of transcytosis vs retention.
- Species divergence is central to all three programmes (LRP6 98% human/mouse identity; ALPL >92%;
  CA-IV 55% mouse/human) — the card tests human peptide–domain fragments only.

## Gaps
1. Card's labels are proxies (10-ns contact survival), not cell-level transcytosis; programmes decide
   with Transwell assays and NHP in vivo screens, so AUC against the card's own labels is uncalibrated
   to their endpoints.
2. Peptide–domain fragments in water; no full glycosylated capsid, no glycans (GPI-anchored ALPL,
   glycosylated LRP6/CA-IV), despite the card title promising "capsid–receptor–glycan complexes".
3. Only one measured pH-kinetics pair exists (VCAP-102–ALPL) to anchor the pH-ratio criterion.
4. Compute axis (8–32 replicas × 10 ns) is many orders below screening scale (4E7 library variants;
   6400-protein interactome; 10^4–10^7 pooled in vivo designs at Dyno).
5. Millisecond off-rates and endosomal pH lability may not be separable from 10-ns contact survival;
   if not, the "if not" outcome is the expected one.
6. Species-context: human-only fragments; programmes need orthologue binding and humanized models.
