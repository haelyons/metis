# Frame check: card

Root question: Can molecular mapping of AAV capsid-receptor interactions on brain microvascular endothelial cells determine which AAV variants transcytose across the blood-brain barrier versus remain intracellular, and for which capsid-receptor binding signatures?

Models: research opencode-go/mimo-v2.6-pro; dramaturgs opencode-go/deepseek-v4.1-flash, opencode-go/glm-5.3-flash; critics opencode-go/qwen3.8-flash, opencode-go/mimo-v2.6-flash, opencode-go/minimax-m3.
Cost $0.1717 · 424,892 tokens · 22.9 min wall time.

**Best fit:** Lir Therapeutics — Starfish™ / nAAVigator®, at "Starfish™ capsid-surface structure generation feeding receptor docking on symmetry-axis patches inside the nAAVigator® pipeline — in Lir's words, surface portions 'at the 2, 3 and 5-fold axes are the minimum subunit for useful docking or structural assessment of capsid stability in silico'. Docking receptors onto those Starfish-built variant capsid surfaces produces the binding-screen hits and 'explainability' that drive Lir's lab-in-the-loop variant selection. The card scores exactly this docking/binding-call step and its threefold-axis interface geometry.". Fit 5, change 3, new 4: 12 of 15.

## 1. Capsida Biotherapeutics

https://capsida.com/

**Step:** In vitro capsid–receptor binding detection in their integrated platform: plate-based and bead-based receptor binding assays ('In Vitro Binding Platform Demonstrates Reproducible Capsid/Receptor Binding Data Consistent with Expression Profiles') that emit bind/no-bind readouts for engineered capsids against the NR001–NR005 blood-brain-barrier receptor panel, with in vitro binding predictive power confirmed by transduction in receptor-expressing cell lines. The card emits computed capsid–receptor binding calls in exactly this readout's format, so its result would sit directly upstream of this step as an in silico pre-filter.

**Practice claims and checks:**
- DISPUTED [SUPPORTED, UNREACHABLE] The binding step is run as wet-lab detection in plate- and bead-based formats across patented BBB receptors NR001–NR005, whose identities are not public. (https://capsida.com/wp-content/uploads/Nick_Goeden_1445_May-14_Theater-C_Identification-of-Multiple-BBB-Receptors.pdf)
- VERIFIED [SUPPORTED, SUPPORTED] Scale and people: large engineered capsid libraries screened by automated, high-throughput biological screening by Capsida scientists, at a scale the company calls unrivaled. (https://capsida.com/science-innovation/)
- VERIFIED [SUPPORTED, SUPPORTED] Today the receptor step is treated as the key design variable: the company is investigating its CAP-002 capsid's interaction with receptor ADAM15 and advancing a new capsid using receptor RECK. (https://capsida.com/capsida-to-present-preclinical-data-of-new-next-generation-high-performing-ocular-capsids-at-asgct-annual-meeting/)

**Activity:** active [SUPPORTED, SUPPORTED] Active: Capsida issued a corporate and pipeline update on May 12, 2026 with ASGCT 2026 presentations and CNS-program work, including ongoing receptor-interaction studies of its clinical capsid and a next-generation capsid using receptor RECK.

**Flag:** the step is put in the card's terms, or no checker found it on the programme's page.

**If the lever:** If balanced accuracy reaches 0.80 at 432 runs with five of six binders at published sites, Capsida would gain a computed bind/no-bind gate ahead of its plate- and bead-based assays: capsid–receptor pairs could be pre-selected in silico before wet-lab binding detection, and the threefold-axis site-recovery result would become an interface-geometry quality check for calls on its NR001–NR005 (and ADAM15/RECK) panel; hundreds of pose/seed/MD runs would be budgeted as validation compute for the patented receptor program.

**If not:** Nothing changes: plate- and bead-based receptor binding detection remains the binding gate, computed calls stay hypothesis-generating only, and no extra pose-enumeration compute is added to the platform, since accuracy moves under 0.05 between 54 and 432 runs and at most three of six binders reach published sites.

**Already done:** unknown [PARTIAL, UNREACHABLE] No public record shows Capsida running exhaustive computed capsid–receptor pose enumeration scored against its plate/bead binding labels; its public platform material validates binding experimentally (transduction in receptor-expressing cell lines), and the NR001–NR005 receptors and assay labels are proprietary, so internal work of this kind cannot be ruled out.

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 3 | 3, 3, 3 | 0 |
| change | 3 | 3, 3, 3 | 0 |
| new | 3 | 3, 3, 3 | 0 |

- fit, opencode-go/qwen3.8-flash: Card tests ALPL/AAVR/LRP6 published pairs, not supported NR001–NR005/ADAM15/RECK systems, so only stand-in prefilter.
- fit, opencode-go/mimo-v2.6-flash: Card scores public capsid–receptor pairs and published labels, not Capsida's proprietary NR001–NR005 panel, so it's a stand-in the programme must bridge.
- fit, opencode-go/minimax-m3: The card measures capsid–receptor bind/no-bind calls and threefold geometry, but public ALPL, AAVR and LRP6 benchmarks only stand in for proprietary NR001–NR005 labels.
- change, opencode-go/qwen3.8-flash: Supported wet-lab binding could gain computed prescreen only if accurate; non-lever leaves binding detection unchanged.
- change, opencode-go/mimo-v2.6-flash: Only the lever-holds outcome adds an in silico pre-filter, and bridging to proprietary receptors requires work the card does not do.
- change, opencode-go/minimax-m3: A positive result could add an in-silico prefilter, but operational use requires proprietary NR-panel calibration and wet-lab validation; failure leaves current screening unchanged.
- new, opencode-go/qwen3.8-flash: Supported wet-lab binding lacks public computed pose enumeration, but proprietary internal work remains unknown, so unclear.
- new, opencode-go/mimo-v2.6-flash: No-record claim is only PARTIAL with one UNREACHABLE check, leaving unclear whether Capsida has internally run this pose-enumeration validation.
- new, opencode-go/minimax-m3: Public evidence supports experimental binding assays, not this exhaustive computational benchmark; proprietary labels leave possible prior internal pose enumeration unresolved.

## 2. Lir Therapeutics — Starfish™ / nAAVigator®

https://www.lirtx.com/

**Step:** Starfish™ capsid-surface structure generation feeding receptor docking on symmetry-axis patches inside the nAAVigator® pipeline — in Lir's words, surface portions 'at the 2, 3 and 5-fold axes are the minimum subunit for useful docking or structural assessment of capsid stability in silico'. Docking receptors onto those Starfish-built variant capsid surfaces produces the binding-screen hits and 'explainability' that drive Lir's lab-in-the-loop variant selection. The card scores exactly this docking/binding-call step and its threefold-axis interface geometry.

**Practice claims and checks:**
- VERIFIED [SUPPORTED, SUPPORTED] Scale and tools: Starfish builds capsid surfaces by folding monomers then physics-based assembly and refinement, fast enough for screening tens of thousands of variants on cost-efficient hardware. (https://www.lirtx.com/post/starfish-fast-capsid-structure-generation)
- VERIFIED [SUPPORTED, SUPPORTED] The binding-call use today is receptor docking screens on Starfish-built variant surfaces (LY6A first, then other receptors), with computed hits compared against language-model hits. (https://www.lirtx.com/post/starfish-fast-capsid-structure-generation)
- VERIFIED [SUPPORTED, SUPPORTED] Current tuning of the docking step is by surface size rather than run count, and the threefold axis is their benchmarked reference surface (AAV9 3-fold axes within RMSD <1 Å). (https://www.lirtx.com/post/starfish-fast-capsid-structure-generation)

**Activity:** active [SUPPORTED, UNREACHABLE] Active: Lir's blog ran through July 15, 2026, and on August 18, 2026 VectorBuilder announced a strategic collaboration with Lir to develop AI-designed AAV capsids.

**Flag:** the step is put in the card's terms, or no checker found it on the programme's page.

**If the lever:** If 432 runs give balanced accuracy 0.80 and five of six binders within 5 Å of published sites, Lir would promote its docking stage from a hit-ranking heuristic to a validated bind/no-bind call at the threefold patch: nAAVigator would budget hundreds of pose/seed/MD runs per capsid–receptor pair, use threefold-site contact overlap as interface QC, and drop no-bind pairs before lab-in-the-loop validation.

**If not:** Nothing in the call stage changes: docking stays a ranking signal additive to their language-model hits, lab-in-the-loop assays remain the binding gate, surface-size tuning remains their only docking knob, and extra pose sampling is not justified because accuracy is flat between 54 and 432 runs.

**Already done:** partly [SUPPORTED, SUPPORTED] Lir has already run receptor docking screens on Starfish-built variant capsid surfaces (LY6A at ESGCT 2025, and the same approach 'for other receptors'), but has not published bind/no-bind accuracy of computed calls against a labelled capsid-by-receptor grid, nor a 54-to-432 run-count scaling test — the assessment the card performs.

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 5 | 5, 5, 3 | 2 |
| change | 3 | 3, 5, 3 | 2 |
| new | 4 | 5, 4, 3 | 2 |

- fit, opencode-go/qwen3.8-flash: Card directly measures AAV capsid docking calls and threefold-axis geometry, the quantity Lir's supported docking step depends on.
- fit, opencode-go/mimo-v2.6-flash: The card measures balanced accuracy and threefold-site recovery — the exact docking-call quantities Lir's nAAVigator step depends on, including its AAV9 threefold benchmark.
- fit, opencode-go/minimax-m3: The outcome matches Lir’s docking calls and threefold QC, but public ALPL, AAVR and LRP6 results do not validate Starfish variants or proprietary assay labels.
- change, opencode-go/qwen3.8-flash: Current docking is tuned by surface size, not run count; only lever outcome would change validation and scaling.
- change, opencode-go/mimo-v2.6-flash: Both outcomes alter docking-stage practice now: promote ranking to validated calls, budget hundreds of pose/seed runs, add contact-overlap QC, drop no-bind pairs.
- change, opencode-go/minimax-m3: Success could add extensive pose sampling and a pre-assay binding gate; failure preserves today’s surface-size tuning and laboratory gate.
- new, opencode-go/qwen3.8-flash: Supported claims show docking exists, but labelled accuracy and 54-to-432 run-count scaling remain absent from practice.
- new, opencode-go/mimo-v2.6-flash: Lir has run docking screens but supported claims confirm no published bind/no-bind accuracy or 54-to-432 run-count scaling test exists.
- new, opencode-go/minimax-m3: Lir already performs receptor docking on Starfish surfaces, but lacks published bind/no-bind accuracy and the proposed 54-to-432-run scaling test.

## 3. CLOVER Center / Gradinaru Laboratory, Caltech — APPRAISE

https://clover.caltech.edu/

**Step:** Computed capsid–receptor binding models and bind/no-bind calls: the APPRAISE pipeline ranks engineered capsid peptides by receptor-binding propensity from AlphaFold-Multimer competitions ('a method that predicts the receptor binding propensity of engineered proteins based on high-precision protein structure prediction tools, such as AlphaFold2-multimer'), extended to integrative trimer–receptor models on the AAV threefold spike, and validated against cell-microarray/SPR/pull-down labels and cryo-ET binding sites. This is the programme the card's closest prior (Shay et al. 2024) belongs to, and its computed-call step is the one the card scales from a handful of models to 54–432 runs.

**Practice claims and checks:**
- VERIFIED [SUPPORTED, SUPPORTED] Binding-call generation today: APPRAISE scores pairwise peptide–receptor structure models with physics- and geometry-informed analysis in under one CPU-second per model. (https://authors.library.caltech.edu/records/nyxge-gz849)
- VERIFIED [SUPPORTED, PARTIAL] Modeling scale in their own capsid–receptor work is small: five AlphaFold-Multimer models per peptide with up to 20 recycles on one A100 GPU, checked against SPR domain labels (LRP6 E1E2 vs E3E4). (https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518/)
- VERIFIED [SUPPORTED, SUPPORTED] Their interface-geometry observable is the threefold spike: binding sites are placed by cryo-ET sub-tomogram averaging with symmetry expansion, next to the twofold valley, and integrated with the computed models. (https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518/)

**Activity:** active [PARTIAL, PARTIAL] Active: the CLOVER Center's most recent announcement (August 27, 2026) reports a Nature Chemical Biology paper on a CA-IV-targeting BBB shuttle by Gradinaru-lab alumni and staff, following a March 30, 2026 Molecular Therapy paper structurally characterizing AAV9-X1.1 and CAP-B10 capsids.

**Flag:** the step is put in the card's terms, or no checker found it on the programme's page.

**If the lever:** If the lever holds (0.80 balanced accuracy at 432 runs, five of six binders within 5 Å of published sites), the lab would scale APPRAISE/AlphaFold-Multimer from 5–10 models per competition to hundreds of pose/seed/MD runs per pair as the standard for bind/no-bind calls across a capsid-by-receptor grid, use the threefold-site tolerance as the interface criterion, and let computed calls decide which pairs consume SPR/pull-down and cryo-ET time.

**If not:** Computed models stay illustrative: bind/no-bind calls continue to come from SPR, pull-down and cryo-ET, AlphaFold-Multimer runs remain at a handful of representative models per peptide, and APPRAISE rankings remain rank-order hints rather than calls; no compute scaling would be adopted.

**Already done:** partly [PARTIAL, PARTIAL] The card's experiment exists in miniature in this programme: APPRAISE's proof-of-concept already classifies receptor-dependent vs receptor-independent AAV vectors from computed models, and Shay et al. 2024 scored 5-model AlphaFold-Multimer LRP6-domain predictions against SPR bind/no-bind labels and cryo-ET sites for about six capsids; what is missing is the full 36-pair grid at 54–432 runs with balanced-accuracy and site-recovery scoring.

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 5 | 5, 5, 5 | 0 |
| change | 3 | 3, 5, 3 | 2 |
| new | 3 | 3, 3, 3 | 0 |

- fit, opencode-go/qwen3.8-flash: Card scales the APPRAISE quantity itself: computed capsid-receptor calls with threefold-site geometry, on supported AAV systems.
- fit, opencode-go/mimo-v2.6-flash: The card scales the lab's own APPRAISE AlphaFold-Multimer step on the same LRP6/threefold-spike systems and SPR/cryo-ET labels it already uses.
- fit, opencode-go/minimax-m3: It directly scales the programme’s five-model AlphaFold-Multimer/SPR workflow with cryo-ET threefold-site scoring on capsid–receptor pairs.
- change, opencode-go/qwen3.8-flash: Supported practice uses small models and experimental calls; only lever outcome would scale models and gate SPR/cryo-ET use.
- change, opencode-go/mimo-v2.6-flash: Lever-holds outcome changes compute directly: hundreds of runs per pair become standard for bind/no-bind calls, deciding which pairs consume SPR and cryo-ET time.
- change, opencode-go/minimax-m3: Success could standardize hundreds of runs and let computed calls prioritize SPR and cryo-ET; failure leaves the current small-scale, assay-gated practice.
- new, opencode-go/qwen3.8-flash: Supported mini-scale already tests AlphaFold-Multimer against labels; the full 54-to-432 grid remains partly answered.
- new, opencode-go/mimo-v2.6-flash: Shay 2024 already ran a miniature version here — five-model predictions against SPR and cryo-ET labels — but both checkers mark this only PARTIAL.
- new, opencode-go/minimax-m3: The proof-of-concept and Shay experiment already cover miniature classification and five-model site checks; only broader grid accuracy and compute scaling remain unanswered.

## Gaps named by the researcher

- Public bind/no-bind labels cover only 13 of the card's 36 pairs, and Capsida's NR001–NR005 receptor identities are patented and unnamed publicly, so the full grid can never be scored against Capsida's own plate/bead labels.
- None of the three programmes has published a run-count scaling curve (54→432 model runs) for binding-call accuracy, so the card's lever question is open for all of them.
- Lir's Starfish benchmarks and receptor-docking screens live in blog posts and an ESGCT 2025 poster, not a peer-reviewed bind/no-bind accuracy dataset, so its call accuracy is not externally checkable before the card's test.
- The card yields binding-call agreement and interface geometry only; all three programmes ultimately gate on transduction, transcytosis or in vivo data that the card does not supply.
- Capsida's current priority receptors (ADAM15 for CAP-002, RECK for its next-generation capsid) are absent from the card's reference labels and from public interface structures, so even a positive lever result would not validate calls for the pairs Capsida is now prioritizing.
