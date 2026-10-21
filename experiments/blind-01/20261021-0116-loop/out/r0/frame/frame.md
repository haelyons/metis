# Frame check: card

Root question: Can molecular mapping of AAV capsid-receptor interactions on brain microvascular endothelial cells determine which AAV variants transcytose across the blood-brain barrier versus remain intracellular, and for which capsid-receptor binding signatures?

Models: research opencode-go/mimo-v2.6-pro; dramaturgs opencode-go/deepseek-v4.1-flash, opencode-go/glm-5.3-flash; critics opencode-go/qwen3.8-flash, opencode-go/mimo-v2.6-flash, opencode-go/minimax-m3.
Cost $0.1775 · 597,867 tokens · 21.7 min wall time.

**Best fit:** Gradinaru Lab (Caltech) / APPRAISE-AAV — receptor-directed AAV engineering and the open-source APPRAISE package, at "The computational step the card scales: ranking engineered capsid insertion peptides against BBB receptors by AlphaFold-Multimer pairwise competition modeling, scored with atom-counting energy plus binding-angle and pocket-depth geometry, used to classify receptor-dependent vs receptor-independent capsids and to pick candidates before in vivo selection. Today this runs at ten models per competition on single-GPU Colab sessions; the card asks whether 144–2,880 pose models per pair change the transcytosis call.". Fit 5, change 5, new 5: 15 of 15.

## 1. Voyager Therapeutics — TRACER capsid discovery and ALPL NeuroShuttle (VCAP-102 / VY1706)

https://www.voyagertherapeutics.com/pipeline-overview/

**Step:** Mechanism-of-action step of the TRACER pipeline the card targets: after RNA-guided in vivo capsid evolution, Voyager identifies the vascular receptor each capsid uses to cross the BBB and demonstrates that binding of that receptor initiates transcytosis rather than mere uptake — i.e., the transcytose-versus-retain call per capsid–receptor pair. In practice this is done with human surface-protein binding/transduction screens, SPR, and a polarized cell-barrier Transwell assay, not with exhaustive structural enumeration.

**Practice claims and checks:**
- VERIFIED [SUPPORTED, SUPPORTED] Scale of the discovery funnel feeding the receptor step: TRACER-NHP libraries start at ~4E7 individual capsid variants, narrowed by two in vivo macaque passages to ~1,500 variants of interest before receptor work. (https://www.cell.com/molecular-therapy-family/molecular-therapy/fulltext/S1525-0016(25)00373-9)
- VERIFIED [SUPPORTED, SUPPORTED] Receptor identification is done experimentally with two orthogonal screens (human surface-protein binding microarray and ORFeome transduction screen), not by complex modeling. (https://www.cell.com/molecular-therapy-family/molecular-therapy/fulltext/S1525-0016(25)00373-9)
- VERIFIED [SUPPORTED, SUPPORTED] The transcytose-versus-retain call is made in a polarized cell-barrier (MDCK Transwell) model: human ALPL expression raises VCAP-102 transcytosis >100-fold while AAV9 is unaffected. (https://www.cell.com/molecular-therapy-family/molecular-therapy/fulltext/S1525-0016(25)00373-9)
- VERIFIED [SUPPORTED, SUPPORTED] Voyager already works with predicted capsid–receptor interface residues and treats cross-species conservation of the contact set as its translatability argument, so interface-signature outputs are directly consumable. (https://www.voyagertherapeutics.com/wp-content/uploads/2026/05/PRESENTATION_Voyager_IntravenousDeliveryofVY1706_May_2026_Final.pdf)

**Activity:** active [SUPPORTED, SUPPORTED] Active as of 2026: the lead program VY1706 is a TRACER-derived capsid gene therapy with AAIC 2026 NHP GLP toxicology data and dosing in early Alzheimer's disease expected in Q4 2026; ALPL-VYGR-NeuroShuttle sits in the wholly-owned research pipeline.

**Flag:** the step is put in the card's terms, or no checker found it on the programme's page.

**If the lever:** If exhaustive pose enumeration shows that transcytosis-competent pairs share a 3-fold-axis GPI-anchor engagement geometry (competent-minus-retained gap ≥0.50 at 2,880 models), Voyager gains a structural signature for ALPL-engaging capsids — including the VCAP-102 SPH-family insert at VR-IV on the 3-fold spike — that can gate TRACER hits and Gen2 capsids before SPR/Transwell/NHP work, prioritize variants predicted to trigger transcytosis rather than intracellular retention, and inform ALPL-NeuroShuttle binder design; the mechanism story behind VY1706 and partnered programs would gain a predictive interface biomarker.

**If not:** If deeper pose sampling leaves the gap within 0.15 of its 144-model value (insert location already fixes the 3-fold engagement site), nothing changes: Voyager keeps receptor ID via cell-microarray/ORFeome screens and the MDCK Transwell transcytosis model, and capsid–receptor complex enumeration would not enter its Go/No-Go decisions.

**Already done:** partly [SUPPORTED, SUPPORTED] Voyager has run the closest analogue — receptor ID plus a cell-barrier transcytosis demonstration for one capsid family (VCAP-102/ALPL), SPR affinity, cryo-EM showing the insert at the 3-fold apex, and predicted capsid–ALPL contact residues — but has not published exhaustive pose-depth sampling across a capsid panel with transcytose-versus-retain labels.

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 3 | 3, 3, 3 | 0 |
| change | 3 | 3, 3, 4 | 1 |
| new | 4 | 3, 4, 4 | 1 |

- fit, opencode-go/qwen3.8-flash: Measures a structural interface signature, while the program uses experimental receptor ID and Transwell assays for mechanism-of-action steps.
- fit, opencode-go/mimo-v2.6-flash: Card's structural pose-gap is a stand-in; Voyager makes the transcytose-retain call with binding screens, SPR and Transwell assays, requiring a bridge.
- fit, opencode-go/minimax-m3: Card's interface signature feeds Voyager's transcytose-vs-retain step, but only as a computational stand-in versus their experimental microarray/Transwell pipeline.
- change, opencode-go/qwen3.8-flash: Positive finding would add a gate to their Go/No-Go decisions, but they already rely on cryo-EM and predicted interface residues, making the change incremental.
- change, opencode-go/mimo-v2.6-flash: Positive outcome could gate TRACER/Gen2 hits before SPR/Transwell; the negative explicitly changes nothing, so only one outcome alters current practice.
- change, opencode-go/minimax-m3: If motif found, Voyager gains a predictive signature to gate TRACER hits and prioritize variants; if not, practice unchanged — one outcome drives a concrete change.
- new, opencode-go/qwen3.8-flash: The program has done interface predictions and cryo-EM, but lacks exhaustive pose-depth sweeps across a capsid panel.
- new, opencode-go/mimo-v2.6-flash: Voyager already links receptor contacts to a demonstrated transcytosis call for ALPL/VCAP-102, but has not run pose-depth sampling across a panel.
- new, opencode-go/minimax-m3: Voyager has receptor ID, Transwell transcytosis, predicted contacts for one family, but no exhaustive pose-depth sweep across a panel with transcytose/retain labels.

## 2. Gradinaru Lab (Caltech) / APPRAISE-AAV — receptor-directed AAV engineering and the open-source APPRAISE package

https://github.com/GradinaruLab/APPRAISE

**Step:** The computational step the card scales: ranking engineered capsid insertion peptides against BBB receptors by AlphaFold-Multimer pairwise competition modeling, scored with atom-counting energy plus binding-angle and pocket-depth geometry, used to classify receptor-dependent vs receptor-independent capsids and to pick candidates before in vivo selection. Today this runs at ten models per competition on single-GPU Colab sessions; the card asks whether 144–2,880 pose models per pair change the transcytosis call.

**Practice claims and checks:**
- VERIFIED [SUPPORTED, SUPPORTED] Standard depth of pose sampling is ten AF-Multimer models per pairwise competition (five predictions per input order, two orders), averaged into a round-robin ranking matrix. (https://www.cell.com/molecular-therapy-family/molecular-therapy/fulltext/S1525-0016(24)00219-3)
- VERIFIED [SUPPORTED, SUPPORTED] Scale and cost of the step today: a 100-capsid HT-APPRAISE screen completed in 24 h on three parallel Colab GPU sessions, with ~0.1–1 GPU minute per peptide–receptor model and sub-second CPU scoring. (https://www.cell.com/molecular-therapy-family/molecular-therapy/fulltext/S1525-0016(24)00219-3)
- VERIFIED [SUPPORTED, SUPPORTED] Applied to LY6A, LY6C1 and CA4, the 10-model ranking recovered validated binders but produced documented false negatives — the exact failure mode deeper pose sampling is meant to fix. (https://pmc.ncbi.nlm.nih.gov/articles/PMC10115422/)
- VERIFIED [SUPPORTED, SUPPORTED] Where full complex modeling has been run (LRP6–capsid VR-VIII), the lab used only five AF-Multimer models with up to 20 recycles on a single A100, and validated poses experimentally and on macaque/human primary brain microvascular endothelial cells. (https://doi.org/10.1038/s41467-024-52149-0)

**Activity:** active [PARTIAL, PARTIAL] Active: the APPRAISE repository received commits on Apr 9, 2026 (1.3.0 package and Boltz-1/Chai-1/OpenFold3 compatibility), and the lab published human CA-IV-targeted capsid AAV-hCA4-IV77 in Cell Reports on Oct 31, 2025.

**Flag:** the step is put in the card's terms, or no checker found it on the programme's page.

**If the lever:** If the competent-minus-retained engagement gap grows to ≥0.50 only at 2,880 models, the lab would raise APPRAISE's default replicate depth (and could add rigid-docking poses), and a shared 3-fold GPI-anchor motif would become an explicit interface feature alongside its angle/depth geometry terms — letting it triage capsid–receptor pairs and rescue false negatives (e.g., 9P08–LY6A, 9P36–CA4) before humanized-mouse selections for PHP.eC- and hCA4-type vectors.

**If not:** If the gap stays within 0.15 of the 144-model value, nothing changes: the lab keeps ten-model pairwise competitions and its assumption that insert location (VR-VIII AA587–594 at the 3-fold spike) already fixes the engagement site, and the deeper enumeration compute is not justified.

**Already done:** partly [PARTIAL, SUPPORTED] This lab produced the closest prior work: APPRAISE matrices at ten AF-Multimer models per competition across LY6A/LY6C1/CA4 pairings, a validated PHP.eB–LY6A pose used as the reference anchor, five-model LRP6 complex models with cryo-ET, and observed false negatives — but it has not run pose-depth sweeps (144–2,880) or tested a shared 3-fold GPI motif against transcytosis-versus-retention phenotype labels.

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 5 | 5, 5, 5 | 0 |
| change | 5 | 5, 3, 5 | 2 |
| new | 5 | 5, 5, 4 | 1 |

- fit, opencode-go/qwen3.8-flash: Directly targets their computational step of modeling capsid-receptor complexes to classify transcytosis competence.
- fit, opencode-go/mimo-v2.6-flash: Card scales APPRAISE's own ten-model AF-Multimer competition depth on the same receptors and PHP.eB anchor, measuring exactly that step's parameter.
- fit, opencode-go/minimax-m3: Card directly tests APPRAISE's AF-Multimer pairwise competition step on the same receptors (LY6A, LY6C1, CA4) and same PHP.eB anchor — measures the quantity that step depends on.
- change, opencode-go/qwen3.8-flash: A high-depth gap would alter their default APPRAISE depth and scoring parameters, directly modifying current software workflows.
- change, opencode-go/mimo-v2.6-flash: Deeper-sampling success would raise APPRAISE's default replicate depth and add a motif feature; the null outcome explicitly leaves ten-model practice unchanged.
- change, opencode-go/minimax-m3: Both outcomes change a current choice: raise default replicate depth if lever, or confirm 10-model assumption if not; explicit Go/No-Go on depth.
- new, opencode-go/qwen3.8-flash: They have 10-model baselines but lack exhaustive enumeration and testing against transcytosis-vs-retention phenotype labels.
- new, opencode-go/mimo-v2.6-flash: Ten-model matrices with documented false negatives exist; no pose-depth sweep against transcytose-versus-retain labels has been run, so the question is open.
- new, opencode-go/minimax-m3: Closest prior exists: 10-model APPRAISE matrices, validated PHP.eB–LY6A pose, observed false negatives — but no 144–2,880 sweeps or transcytose-vs-retain label testing.

## 3. Dyno Therapeutics — multi-mechanism BBB-crossing capsid portfolio (ALPL, TfR1, Dyno-discovered receptors)

https://www.dynotx.com/gene-delivery

**Step:** The step the card targets is Dyno's mechanism assignment and structure-aware design for its CNS portfolio: deciding which BBB receptor each engineered capsid engages and whether that engagement crosses the BBB, then engineering capsids for several BBB-crossing mechanisms in parallel (ALPL, hTfR1, and Dyno-discovered receptors) rather than one pathway. Dyno states it integrates sequence- and structure-based approaches in its generative design, with receptor mechanism confirmed by head-to-head in vivo comparisons.

**Practice claims and checks:**
- VERIFIED [SUPPORTED, SUPPORTED] Dyno deliberately portfolios multiple BBB-crossing mechanisms and treats receptor mechanism as a translatability lever, so a cross-capsid binding signature for transcytosis would sit directly on its decision path. (https://www.dynotx.com/news/dyno-therapeutics-launches-dyno-yp2-a-top-performing-tfr1-mediated-aav-capsid-to-further-diversify-cns-delivery-portfolio)
- VERIFIED [PARTIAL, SUPPORTED] Its ALPL mechanism (the same GPI-anchored receptor class as the card's motif hypothesis) is validated phenotypically by head-to-head in vivo comparisons of ALPL-targeting capsids in mouse and NHP. (https://www.dynotx.com/gene-delivery)
- VERIFIED [SUPPORTED, SUPPORTED] Scale of the experimental funnel that any in silico signature would filter: LEAP with billions of in vivo sequence–function measurements per month, aimed at CNS partners such as Roche ($50M upfront, Oct 2024). (https://www.dynotx.com/news/dyno-therapeutics-forms-new-strategic-partnership-with-roche-to-advance-aav-gene-therapy-vectors-for-neurological-diseases)

**Activity:** active [PARTIAL, PARTIAL] Active: Dyno launched the ALPL-targeting Dyno-9zh capsid in 2026 and the TfR1-targeting Dyno-yp2 on Jan 12, 2026, with further capsid launches at ASGCT 2026, and runs active Roche/Novartis/Sarepta/Astellas partnerships.

**Flag:** the step is put in the card's terms, or no checker found it on the programme's page.

**If the lever:** If exhaustive enumeration yields a shared 3-fold GPI-engagement signature separating transcytosing from retained pairs (and the gap only appears at high model counts), Dyno could adopt the signature as a design/filter feature in its sequence+structure generative pipeline for ALPL and its discovered-receptor capsids, rank generated capsids by predicted transcytosis-competent geometry to cut in vivo screening, and strengthen the receptor-mechanism translation package its Roche/Novartis partners need.

**If not:** If pose depth does not change the call, Dyno's practice is unchanged: capsid selection remains driven by in vivo phenotype at LEAP scale plus receptor-engagement validation, and capsid–receptor complex enumeration would not affect which mechanisms or capsids it advances.

**Already done:** unknown [PARTIAL, SUPPORTED] No public record shows Dyno has run exhaustive capsid–receptor pose enumeration: its published practice validates receptor mechanisms in vivo (head-to-head ALPL-targeting capsids in mouse and NHP) and folds structure-based approaches into generative design, but any pose-depth studies remain proprietary and unverifiable.

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 3 | 3, 3, 3 | 0 |
| change | 3 | 3, 3, 3 | 0 |
| new | 3 | 3, 3, 3 | 0 |

- fit, opencode-go/qwen3.8-flash: The signature would feed their structure-aware design pipeline, but they rely heavily on massive in vivo phenotypic screening rather than computational modeling for this step.
- fit, opencode-go/mimo-v2.6-flash: Signature is a stand-in: Dyno confirms receptor mechanism by in vivo phenotype at LEAP scale, so structural geometry must be bridged to that readout.
- fit, opencode-go/minimax-m3: Dyno uses structure-based generative design but validates by in vivo phenotype at LEAP scale; card's pose-depth output feeds only through a design filter stand-in.
- change, opencode-go/qwen3.8-flash: Positive finding would add a design filter to their generative pipeline, though in vivo phenotype data remains dominant for their final selection.
- change, opencode-go/mimo-v2.6-flash: A positive signature becomes a generative filter feature; the null result leaves LEAP-driven in vivo selection untouched, so only one outcome changes practice.
- change, opencode-go/minimax-m3: Only the if_lever outcome would add a generative-pipeline filter feature; if_not leaves practice unchanged. Adoption requires further integration work.
- new, opencode-go/qwen3.8-flash: They use structure-based design but no evidence of exhaustive pose enumeration for their specific receptor mechanisms or transcytosis predictions.
- new, opencode-go/mimo-v2.6-flash: No public record of pose enumeration, but proprietary studies remain unverifiable, leaving it unclear whether Dyno has already answered this.
- new, opencode-go/minimax-m3: No public record of exhaustive pose enumeration; Dyno validates mechanisms in vivo head-to-head, but any pose-depth work is proprietary and unverifiable.

## Gaps named by the researcher

- No published pose-depth (model-count) scaling study for AAV capsid–receptor complexes exists; the closest comparators are 10 AF-Multimer models per competition (Ding et al. 2024) and 5 models with up to 20 recycles for LRP6 complexes (Shay et al. 2024), so the card's 144–2,880 arms have no prior baseline beyond the ten-model published one.
- Per-pair transcytose-versus-retain phenotype labels are scarce: Voyager's MDCK Transwell result covers VCAP-102±ALPL vs AAV9 only, and most programs (Dyno, Capsida, Gradinaru) score in vivo brain transduction rather than transcytosis rate, so the card's training labels may rest on few direct measurements.
- APPRAISE-style modeling uses isolated VR-VIII peptides (AA587–594), not the full 60-mer capsid at the 3-fold spike with GPI anchor and membrane; a 'shared 3-fold motif' may partly reflect the peptide-competition setup, and weak avidity-dependent contacts can evade prediction (the card's own caveat).
- Species gaps limit motif generality: LY6A/LY6C1 are mouse-restricted (absent in primates), 9P31/9P36 bind mouse but not primate CA4, while ALPL is conserved — a motif validated on mouse GPI receptors may not transfer to human-relevant pairs.
- Dyno's and Capsida's structural pipelines are proprietary, so 'already done' cannot be settled for them; Capsida's NR001–NR005 human BBB-receptor platform with plate-/bead-based capsid/receptor binding assays (capsida.com) and Lir's Starfish capsid-structure/docking pipeline (lirtx.com) are additional consumers of this result that were not assessed in depth here.
