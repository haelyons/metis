# FRAMER — AAV capsid–receptor molecular mapping as a determinant of BBB transcytosis vs. intracellular retention

**Status:** framing only. The scientific question is deliberately left open; what follows is a definition of the problem, a relay of current understanding, pre-registered predictions, a causal decomposition, and an analysis of where more compute would and would not move the answer.

---

## 0. Restating the question in falsifiable form

> Can molecular mapping of AAV capsid–receptor interactions on brain microvascular endothelial cells (BMECs) determine which AAV variants transcytose across the blood–brain barrier versus remain intracellular, and for which capsid–receptor binding signatures?

There are three nested claims hiding in one sentence, and they must not be conflated:

- **(Q1) Measurability.** Can capsid–receptor interactions on BMECs actually be resolved at molecular resolution (which capsid surface, which receptor ectodomain, which affinity, which stoichiometry, which membrane domain)?
- **(Q2) Causal sufficiency.** Given a complete interaction map, is that map *sufficient* to classify each variant as transcytosing vs. intracellularly retained, or does the phenotype depend on layers that binding does not encode (post-endocytic sorting, polarity, uncoating, degradation)?
- **(Q3) Transportability.** For which *signatures* does the mapping rule transfer — across capsid families, across mouse strains, across rodent→primate→human, and across in vitro model systems?

"Answering" therefore means producing (a) a defined feature space for *binding signature*, (b) a validated decision rule with calibrated accuracy over that space, and (c) an explicit statement of where the rule fails. Anything less is an anecdote catalogue.

---

## 1. Current understanding (relayed)

### 1.1 The physical system

AAV is a non-enveloped icosahedral parvovirus whose capsid is assembled from three overlapping proteins (VP1, VP2, VP3) at roughly a 1:1:10 ratio; the VP1 unique region (VP1u) is internal until extruded during trafficking. The BBB is formed primarily by BMECs joined by tight junctions, with pericytes and astrocytic endfeet; BMECs have low vesicular density relative to peripheral endothelium, which is why transcytosis there is rate-limiting and tightly regulated ([PMC10975205](https://pmc.ncbi.nlm.nih.gov/articles/PMC10975205); [PMC6513804](https://pmc.ncbi.nlm.nih.gov/articles/PMC6513804)).

Systemic AAV reaching the CNS must therefore (i) survive blood clearance and the hepatic sink, (ii) bind the luminal BMEC surface, (iii) be internalized, (iv) escape or avoid the endo-lysosomal system, (v) be sorted into a basolaterally-directed transcytotic carrier rather than recycled or degraded, and (vi) exit intact enough to transduce parenchyma — a *separate* phenotype from crossing ([PMC6629499](https://pmc.ncbi.nlm.nih.gov/articles/PMC6629499/)).

### 1.2 The receptor layer currently known

**Attachment factors (glycans).** AAV2/3B/6/13 use heparan sulfate proteoglycan; AAV1/4/5/6 use terminal sialic acid; AAV9 uses terminal N-linked galactose ([PMC9950413](https://pmc.ncbi.nlm.nih.gov/articles/PMC9950413); galactose domain: [JVI 2012](https://journals.asm.org/doi/10.1128/jvi.00448-12)). Structural work has increasingly recharacterized these glycans as *attachment factors* rather than the protein receptor that dictates entry ([TICV 2022](https://www.sciencedirect.com/science/article/pii/S0966842X2100216X)).

**The protein receptor AAVR (KIAA0319L).** Identified by haploid genetic screen as essential for AAV2 and most tested serotypes (exceptions include AAV4 and AAVrh32.33); AAVR traffics from plasma membrane to trans-Golgi ([PMC4962915](https://pmc.ncbi.nlm.nih.gov/articles/PMC4962915)). Critically, AAVR is *not* required for AAV2 binding or uptake — it acts post-endocytosis, in trafficking/escape ([PMC8413391](https://pmc.ncbi.nlm.nih.gov/articles/PMC8413391/)). Different serotypes engage different AAVR PKD domains (AAV2→PKD2, AAV5→PKD1, AAV1/8→both), so even "the same receptor" hides distinct binding signatures ([JVI 2017](https://journals.asm.org/doi/10.1128/jvi.00391-17)). Cryo-EM of the AAV2–AAVR complex shows the AAVR footprint partially overlapping the heparan-sulfate site ([PMC6561701](https://pmc.ncbi.nlm.nih.gov/articles/PMC6561701)). Structures also exist for AAV1–sialic acid (PDB 5EGC: [RCSB](https://www.rcsb.org/structure/5EGC)) and AAV9–galactose.

**Engineered-capsid BBB receptors (the informative natural experiment).**
- **LY6A (Sca-1)**, a GPI-anchored protein on brain endothelium, is the receptor for AAV-PHP.B/PHP.eB. Disrupting *Ly6a* (CRISPR or blocking antibody) reduces transduction of mouse BMECs; ectopic *Ly6a* raises transduction ≥30-fold in HEK293T/CHO, and this can occur independently of other AAV receptors ([PLOS One 2019](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0225206); [Mol Ther 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6520463)). The phenotype is strain-restricted ([Hum Gene Ther 2020](https://pubmed.ncbi.nlm.nih.gov/31696742)) and fails in NHPs ([Mol Ther 2018](https://pubmed.ncbi.nlm.nih.gov/29428298)).
- **LY6C1 (murine-restricted)** and **carbonic anhydrase IV (CA4, primate-conserved)** were identified by receptor-screens; AlphaFold-based capsid–receptor models were used to predict affinity, enabling AAV-PHP.eC ([Sci Adv 2023](https://pubmed.ncbi.nlm.nih.gov/37075114)).
- **ALPL (tissue-nonspecific alkaline phosphatase)** is the receptor for VCAP-102, an AAV9 variant from RNA-guided TRACER evolution; direct binding to human ALPL initiates receptor-mediated transcytosis in a cell-barrier model, and VCAP-102 gives 20–400× gene transfer over AAV9 across brain regions in rodents and primates ([PubMed 40340250](https://pubmed.ncbi.nlm.nih.gov/40340250)). A reconstituted MDCK-ALPL transwell transcytosed VCAP-102 but not parental AAV9, and ALPL inhibition blocked it ([ASGCT 2024 poster](https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf)).
- **LRP6** was recovered by human cell-surface AAV interactome screening as the transcytosis receptor for NHP-enhanced capsids AAV9-X1.1 and CAP-Mac; galactose and AAVR interactions are largely retained in those capsids, suggesting *synergy of engineered and natural receptors* ([Nat Commun 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518)).

Note the pattern: of the mapped BBB-crossing receptors so far — LY6A, LY6C1, CA4, ALPL — all are GPI-anchored or GPI-AP-family membrane proteins ([ASGCT 2024 poster](https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf)).

### 1.3 The phenotype layer: crossing is not transduction

- AAV9 crosses primary human BMEC monolayers by an active, cell-mediated process without disrupting TEER, tight junctions or inflammatory status, and with *minimal* transduction of the BMECs themselves ([J Neurochem 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5298820)).
- Conversely, AAV2/AAV-BR1 traffic to the nucleus of BMECs with little passage. A single Q→N substitution at position 587 (BR1N) flips BR1 from endothelium-retained to BBB-penetrant, with >90% of transduced cells parenchymal neurons — but BR1N did not improve brain transduction in a primate model ([JCI Insight 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10036519); commentary: [PMC10199398](https://pmc.ncbi.nlm.nih.gov/articles/PMC10199398)).
- AAV-BI30 is a high-efficiency CNS *endothelial* vector (282–2261× AAV9 in mouse BMVECs) that stays in the vasculature ([Nat Commun 2022](https://pmc.ncbi.nlm.nih.gov/articles/PMC9103166)); galactose-binding-deficient AAV9 (W503A) derivatives lose liver targeting and lose non-endothelial brain transduction while retaining brain-endothelial infectivity ([iScience 2024](https://iris.cnr.it/retrieve/2bf93910-4a4b-4d40-8da1-f893f86ad3e8/1-s2.0-S2589004224009994-main.pdf)).
- One AAV9-derived variant reported a ~60-fold CNS transduction increase yet "failed to penetrate the BBB and was retained in the microvascular endothelial cells" ([PMC10975205](https://pmc.ncbi.nlm.nih.gov/articles/PMC10975205)) — i.e., the readout most often used as a proxy for crossing (brain transgene expression) can be dominated by endothelium.

So *binding to BMECs*, *transduction of BMECs*, and *transcytosis across BMECs* are three separable phenotypes, and the literature contains all three dissociation directions.

### 1.4 The mapping technologies that exist

- **Structural:** cryo-EM/X-ray of capsid–receptor and capsid–glycan complexes (AAV2–AAVR: [PMC6561701](https://pmc.ncbi.nlm.nih.gov/articles/PMC6561701); AAV1–SIA: [RCSB 5EGC](https://www.rcsb.org/structure/5EGC)); AlphaFold-based capsid–receptor models used to infer affinity ([Sci Adv 2023](https://pubmed.ncbi.nlm.nih.gov/37075114)).
- **Interactomics:** human cell-surface protein microarrays probed with capsids recovered LRP6 and IL3 as AAV binders ([Nat Commun 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518)).
- **Deep mutational scanning / fitness landscapes:** the complete first-order AAV2 capsid landscape (all single-codon substitutions, insertions, deletions across 735 positions) is measured, with most mutations impairing assembly and with mutational tolerance concentrated in variable regions ([Science 2019](https://www.science.org/doi/10.1126/science.aaw2900); ML-guided design from it: [Nat Biotechnol 2021](https://pubmed.ncbi.nlm.nih.gov/33574611/)).
- **Pooled in vivo screens:** barcoded libraries (e.g. 183 variants side-by-side in one animal: [Nat Commun 2020](https://www.nature.com/articles/s41467-020-19230-w)), CREATE (Cre-recombination in transgenic mice), and TRACER (cell-type-specific RNA recovery in non-transgenic animals, up to 400× brain transduction over AAV9: [PMC7841218](https://pmc.ncbi.nlm.nih.gov/articles/PMC7841218)).
- **Barrier assays:** primary human BMEC transwells, hCMEC/D3 transwells used for capsid selection ([MTMCD 2022](https://www.cell.com/molecular-therapy-family/methods/fulltext/S2329-0501(22)00127-9)), and receptor-reconstituted MDCK transwells ([ASGCT 2024 poster](https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf)).

### 1.5 The two findings that make the question hard rather than routine

**(a) Monolayer binding does not predict in vivo transport.** In a 330-variant screen, capsids with high mouse-BMEC binding almost exclusively belonged to the LY6A-binding PHP-like cluster, while another cluster sharing the same C57BL/6-specific in vivo phenotype *did not* bind mouse BMECs; the authors conclude "monolayer cultures of BMVECs are a poor predictor of in vivo transport across the BBB" ([PMC7841218](https://pmc.ncbi.nlm.nih.gov/articles/PMC7841218)).

**(b) Species and strain lock-in.** PHP.B/PHP.eB depend on LY6A, which is polymorphic among mouse strains and has no primate ortholog; PHP.B is no better than AAV9 in BALB/cJ or NHPs ([PubMed 29428298](https://pubmed.ncbi.nlm.nih.gov/29428298)). The reverse also exists: VCAP-103 improves brain transduction ~40× in cynomolgus macaque and works in marmoset/AGM but *not* in C57BL/6 or BALB/c mice ([Voyager ASGCT 2023](https://www.voyagertherapeutics.com/wp-content/uploads/2023/12/6_FINAL-Voyager_ASGCT_2023_Lin_05-05-23.pdf)). A species-barrier review catalogs these as differences in capsid–receptor interaction, intracellular trafficking, immunity and microanatomy ([PMC13061871](https://pmc.ncbi.nlm.nih.gov/articles/PMC13061871)).

### 1.6 What is known about the sorting decision *after* binding

For antibody shuttles at the BBB, affinity and valency are decisive: high-affinity and bivalent anti-TfR binding *prevents* transcytosis and drives lysosomal delivery, while monovalent/lower-affinity engagement transcytoses ([PMC6513804](https://pmc.ncbi.nlm.nih.gov/articles/PMC6513804)). Endosomal sorting tubules (Rab17-positive) regulate the transcytosis-vs-degradation decision ([Cell Rep 2017](https://www.sciencedirect.com/science/article/pii/S2211124717317072)); Mfsd2a suppresses caveolae-mediated transcytosis cell-autonomously ([PMC6629499](https://pmc.ncbi.nlm.nih.gov/articles/PMC6629499/)); GPI-anchored proteins enter clathrin-independent CLIC/GEEC pathways ([PMC6513804](https://pmc.ncbi.nlm.nih.gov/articles/PMC6513804)). This is machinery that a pure binding map does not contain.

### 1.7 A methodological landmine in the model system itself

Commonly used iPSC-derived BMEC ("iBMEC") protocols produce a homogeneous **neuroectodermal epithelial** population (Epi-iBMEC) that lacks vascular-lineage genes and brain-EC-specific transporters (SLCO1A2, SLCO1C1, MFSD2A, ABCG2, ABCB1) and expresses an epithelial claudin repertoire; ETS-factor reprogramming is required to obtain true endothelial identity ([PNAS 2021](https://www.pnas.org/doi/10.1073/pnas.2016950118)). Any "molecular mapping on BMECs" done on iBMECs maps the wrong cell unless identity is verified. This alone can invert conclusions about receptor repertoire and transcytotic capacity.

---

## 2. Predictions (registered before answering)

These are stated so that each is falsifiable and so that later evaluation is not retrofitted.

- **P1 (Sufficiency is partial).** A classifier built only from binding features (receptor identity, epitope footprint, KD/kon/koff, valency/stoichiometry, membrane microdomain of receptor) will be substantially better than chance at predicting transcytosis vs. retention, but will leave a large residual that is explained by post-binding features (receptor cytoplasmic-tail/GPI status, endosomal pH-dependent dissociation, ubiquitination/degradation susceptibility, uncoating kinetics).
- **P2 (GPI enrichment).** Transcytosis-competent capsid receptors will be statistically overrepresented among GPI-anchored / lipid-raft-resident proteins relative to receptors with endocytic motifs that route to lysosomes. All four mapped BBB-crossing receptors to date (LY6A, LY6C1, CA4, ALPL) are in this class ([ASGCT 2024 poster](https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf)), which is the prior this prediction generalizes.
- **P3 (Non-monotone affinity).** Capsid–receptor affinity will relate to transcytosis as an inverted U: below a threshold there is no uptake; above a threshold the complex is retained/degraded at the luminal surface or in endosomes (the "binding-site barrier" phenomenon already documented for TfR antibodies: [PMC6513804](https://pmc.ncbi.nlm.nih.gov/articles/PMC6513804)). Optimal transcytosis will correspond to *tunable off-rate under endosomal pH*, not maximal serum-phase affinity.
- **P4 (Epitope matters more than affinity).** Two capsids with matched KD for the same receptor but non-overlapping footprints will differ in fate, because footprint determines clustering geometry, receptor orientation in the membrane, and whether the receptor co-partition into transcytotic vs. degradative domains.
- **P5 (In vitro–in vivo mismatch persists).** BMEC monolayer binding/transduction assays will systematically misrank some variants relative to in vivo BBB crossing in both directions, consistent with the reported failure of monolayer binding to predict transport ([PMC7841218](https://pmc.ncbi.nlm.nih.gov/articles/PMC7841218)); a reconstituted receptor-transwell (e.g. MDCK-ALPL) will be *more* specific but will overstate sufficiency of the single receptor by stripping away native sorting context.
- **P6 (Species generalization failure).** Any binding signature derived in mouse will fail out-of-sample in primates whenever the receptor is strain- or species-restricted (LY6A/LY6C1); signatures anchored on conserved receptors (ALPL, CA4, LRP6, AAVR/galactose) will transfer better. VCAP-103's primate-only phenotype ([Voyager ASGCT 2023](https://www.voyagertherapeutics.com/wp-content/uploads/2023/12/6_FINAL-Voyager_ASGCT_2023_Lin_05-05-23.pdf)) is the mirror case to PHP.B.
- **P7 (Synergy, not single receptor).** Where a capsid retains natural attachment-factor usage (galactose, HSPG) plus an engineered protein-receptor interaction, fate will be joint: galactose loss detargets liver and abolishes parenchymal transduction while sparing endothelial infectivity ([iScience 2024](https://iris.cnr.it/retrieve/2bf93910-4a4b-4d40-8da1-f893f86ad3e8/1-s2.0-S2589004224009994-main.pdf)); LRP6-binding engineered capsids retain galactose and AAVR interactions ([Nat Commun 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518)). "The signature" will therefore be a *pair or set*, not a single interaction.
- **P8 (Perturbation is required).** No purely observational mapping will be accepted as "determining" fate; the field will require loss-of-function (receptor knockout/blocking) and gain-of-function (ectopic receptor conferring transcytosis) tests, as done for LY6A ([PLOS One 2019](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0225206)) and ALPL ([ASGCT 2024 poster](https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf)). Predictive correlation alone will be treated as hypothesis generation.

---

## 3. Problem definition and decomposition

### 3.1 Operational definitions (needed before any measurement)

| Term | Must mean | Must not be confused with |
|---|---|---|
| "Molecular mapping" | A per-(capsid variant × receptor) record containing: binding site on capsid (residues, e.g. VR-IV insert vs. 3-fold galactose pocket), receptor domain engaged (e.g. AAVR PKD1 vs PKD2: [JVI 2017](https://journals.asm.org/doi/10.1128/jvi.00391-17)), affinity/kinetics, stoichiometry, and receptor membrane compartment | Co-immunoprecipitation "hits"; RNA co-expression |
| "Transcytosis" | Intact vector genome (and ideally capsid) appearing abluminally in a barrier assay with preserved TEER and minimal endothelial transduction ([J Neurochem 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5298820)) | Brain transgene expression (dominated by parenchymal transduction efficiency and promoter) |
| "Remain intracellular" | Retained in BMEC endosomes/lysosomes or trafficked to nucleus for endothelial transduction (AAV2/BR1/BI30 phenotype: [PMC10036519](https://pmc.ncbi.nlm.nih.gov/articles/PMC10036519), [PMC9103166](https://pmc.ncbi.nlm.nih.gov/articles/PMC9103166)) | "Low brain signal" (could be liver sink or clearance) |
| "Binding signature" | A structured feature set over capsid surface + receptor ectodomain + glycan context | A single receptor name |

### 3.2 Causal chain / decision points

```
IV dose → blood survival & liver sink (capsid; ~15% ID/cc liver accumulation for
         AAV9 and engineered capsids alike: PMC9621732)
  → luminal encounter: glycan attachment (HSPG/SIA/galactose)
  → protein-receptor engagement (AAVR / LY6A / LY6C1 / CA4 / ALPL / LRP6 / unknown)
  → clustering geometry & membrane domain (GPI/lipid-raft vs clathrin pit)
  → endocytic route (CME / CLIC-GEEC / caveolae / macropinocytosis)
  → endosomal sorting node  ← Mfsd2a, Rab5→Rab7, Rab17 tubules, pH-dependent
       dissociation, ubiquitination
      ├─► recycling to lumen (loss)
      ├─► lysosome / proteasome (retention) ← "remain intracellular"
      ├─► nuclear import in BMEC (endothelial transduction, no crossing)
      └─► basolateral exocytosis (transcytosis) → intact? → parenchymal transduction
```

The mapping in the question covers only the first two boxed nodes. The phenotype labels are produced at the last node. Everything in between is where sufficiency will be won or lost.

### 3.3 Hypothesis space for the answer (stated without selecting)

- **H_suff:** binding signature is sufficient; sorting is a deterministic function of receptor identity/geometry.
- **H_cond:** binding is necessary and *conditionally* sufficient given a small number of additional trafficking features (GPI status, pH off-rate, ubiquitination motifs) — i.e., an augmented signature works.
- **H_insuff:** binding is necessary but not determinative; fate is set by stochastic/contextual sorting, so mapping yields enrichment statistics, not classification.
- **H_context:** any of the above holds only within a species/strain/model system; the general question is ill-posed as stated and must be re-asked per context.

### 3.4 What would count as a decisive answer

1. A pre-registered feature set for "binding signature."
2. A panel of ≥50–100 capsids spanning matched-affinity/different-footprint, matched-footprint/different-affinity, and receptor-null mutants.
3. Orthogonal fate readouts on authentic (identity-verified) BMECs: basolateral intact genomes, endothelial nuclear entry, lysosomal co-localization, TEER integrity.
4. Perturbations: receptor KO/CRISPR, blocking antibodies, GPI-anchor disruption, Mfsd2a manipulation, Rab17/tubule disruption.
5. Out-of-sample validation in a second species and in a reconstituted receptor system.
6. Reported explained variance and calibration of the binding-only model vs. binding+trafficking model.

### 3.5 Boundary conditions and confounds to hold fixed

- Dose dependence and the hepatic sink (engineered capsids show similar liver accumulation to AAV9 (~15% ID/cc) but reduced hepatocyte transduction: [PMC9621732](https://pmc.ncbi.nlm.nih.gov/articles/PMC9621732)).
- Pre-existing neutralizing antibodies overlapping receptor footprints ([PMC9950413](https://pmc.ncbi.nlm.nih.gov/articles/PMC9950413)).
- Capsid fitness/assembly constraints: most single mutations impair assembly, so "binding mutants" are often just broken capsids ([Science 2019](https://www.science.org/doi/10.1126/science.aaw2900)).
- Model-system identity: verify endothelial (not epithelial) identity of the BMEC substrate ([PNAS 2021](https://www.pnas.org/doi/10.1073/pnas.2016950118)).
- Readout choice: RNA/barcode enrichment ≠ genome crossing ≠ protein expression ([TRACER](https://pmc.ncbi.nlm.nih.gov/articles/PMC7841218)).
- Developmental/age state (AAV9 BBB crossing is much higher in neonates) and route (i.v. vs intra-CSF; PHP.eB works in NHP only by intrathecal/i.c.v.: [PubMed 34869273](https://pubmed.ncbi.nlm.nih.gov/34869273)).

---

## 4. Why the question is interesting rather than settled

The field has produced, in five years, an *unusual* situation: several engineered capsids with strong BBB-crossing phenotypes, and several mapped receptors, but the mapping was performed *after* the phenotype was selected by mechanism-agnostic directed evolution. That inverts the usual causal direction. The question asks whether the map can be run *forward* — from interaction to fate — and that is exactly the step that has not been demonstrated. The pieces exist (structure, interactomes, fitness landscapes, pooled screens, reconstituted transwells), but no study has fit and validated a binding-signature→fate classifier across variants and species. Whether that gap is because the answer is "no" or because nobody has assembled the right paired dataset is the live scientific issue.

---

## 5. Failure modes of the question itself (to keep visible)

- **"Determine"** may smuggle in sufficiency where the honest claim is enrichment/prioritization.
- **"Binding signature"** is undefined; a signature that includes receptor identity + GPI status + pH off-rate is a different question from a signature that is only epitope+KD.
- **"BBB transcytosis"** in vivo includes post-endothelial events (basement membrane, pericyte coverage, glymphatic clearance: [PubMed 27699236](https://pubmed.ncbi.nlm.nih.gov/27699236)) that no BMEC mapping captures.
- **Selection bias in the evidence base:** receptor-mapping studies exist mainly for capsids that already crossed well; the negative class (retained capsids with mapped binding) is under-sampled, so any classifier trained on the literature will be biased.
- **Species as a hidden variable:** a "signature" may be a mouse-strain fact wearing a general name.

---

## 6. Compute analysis

**Where the bottleneck sits.** Producing the decisive answer requires paired (binding map, fate readout) data on authentic BMECs, with receptor perturbations, and cross-species validation. Each of those is a wet-lab and animal-study bottleneck: transwell assays with identity-verified endothelium ([PNAS 2021](https://www.pnas.org/doi/10.1073/pnas.2016950118)), NHP screening costs, and the fact that pooled screens return enrichment rather than mechanism ([Nat Commun 2020](https://www.nature.com/articles/s41467-020-19230-w)). Additional FLOPs cannot manufacture missing transcytosis phenotypes.

**Where compute genuinely changes things.**
1. *Enumeration of binding signatures* over capsid sequence space × receptor ectodomains is combinatorially large (AAV2 single-mutant landscape alone is ~10^4 measured mutants; deep-learned diversification has produced >10^5 viable variants in one 28-aa segment: [Science 2019](https://www.science.org/doi/10.1126/science.aaw2900), [PubMed 33574611](https://pubmed.ncbi.nlm.nih.gov/33574611/)). Structure prediction/docking at that scale is compute-hungry and determines whether a compact signature class exists.
2. *Sorting-decision simulation* (pH-dependent dissociation, clustering, vesicle fate) is the layer where sufficiency is decided; compute buys in-silico sufficiency tests.
3. *Cross-species model fitting* on pooled screens quantifies how much variance binding alone explains and whether signatures transfer — a question of statistical power over thousands of capsid×species×assay cells.

But these operate on data that must be generated experimentally, and the central question — whether a map is *causally determinative* of a trafficking phenotype — is a logic-and-perturbation question, not a throughput question. The literature already contains the decisive dissociations (binding ≠ crossing: [PMC7841218](https://pmc.ncbi.nlm.nih.gov/articles/PMC7841218); crossing ≠ transduction: [PMC5298820](https://pmc.ncbi.nlm.nih.gov/articles/PMC5298820); conserved-receptor crossing with receptor-sufficient reconstitution: [ASGCT 2024 poster](https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf)). No increase in parallel compute reverses those facts.

**Compute signals where more parallel compute would change the answer.**

- Exhaustive in-silico capsid–receptor complex enumeration (AlphaFold-class modeling + docking + free-energy refinement) across variant libraries × AAVR/glycan/LY6A/CA4/ALPL/LRP6 ectodomains: buys coverage of sequence space no wet lab can assay, and tests whether a compact, transferable binding-signature class exists or the map is irreducibly sparse.
- Physics-based simulation of the post-binding sorting node (endosomal pH dissociation, receptor clustering, ubiquitination, vesicle fate: recycling/transcytosis/lysosome): buys an in-silico sufficiency test of whether binding energetics plus trafficking kinetics jointly determine fate, prioritizing the few perturbations that discriminate H_suff / H_cond / H_insuff.
- Large-scale hierarchical model fitting on pooled barcoded/TRACER/CREATE/transwell datasets with species and model-system random effects: buys a quantified answer to how much variance binding signatures alone explain and whether they transfer from mouse strains to NHP/human, or are species-locked.

---

## 7. Standing

The problem is well-posed once "binding signature", "transcytosis", and "determination" are operationalized; the causal gap between a binding map and a vesicular-sorting phenotype is the crux; the existing evidence already shows dissociations that constrain any answer; and the decisive missing asset is paired, perturbation-validated, cross-species fate data — not additional simulation throughput.

VERDICT: NOT COMPUTE-BOUND
