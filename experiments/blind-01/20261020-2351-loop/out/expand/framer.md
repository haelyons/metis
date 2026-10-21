# Framer: Can molecular mapping of AAV capsid–receptor interactions on brain microvascular endothelial cells determine which AAV variants transcytose across the BBB versus remain intracellular, and for which capsid–receptor binding signatures?

---

## 0. How I am reading the question

Two nested questions are being asked:

1. **Determinacy:** Would a molecular map of capsid–receptor interactions *on BMECs* (brain microvascular endothelial cells) be *sufficient* to classify each AAV variant as (a) transcytosed across the blood–brain barrier (BBB) into parenchyma, (b) retained intracellularly in the endothelium (endosomal/lysosomal sequestration or nuclear trafficking that transduces the BMEC itself), or (c) neither?
2. **Signature scope:** If some mapping *does* work, *for which* capsid–receptor binding signatures does it work — i.e., which receptor engagement classes behave like a deterministic switch, and which do not?

"Determining" here must mean: from binding data alone (receptor identity, epitope, affinity/avidity, stoichiometry, capsid-loop topology), one could correctly assign transcytosis-vs-retention fate for a new variant without running a transwell or animal experiment. A weaker reading — "mapping gives useful priors" — is almost trivially true and not what is being asked. I will test the strong reading and then state precisely where the weaker reading holds.

---

## 1. My prior understanding, before checking the literature

(Corrected in §5–§7 against sources; URLs from here on.)

- **Prior belief P1 — two-stage problem.** Crossing the BBB is a two-stage process: luminal receptor engagement/uptake into the BMEC, then intracellular sorting that either routes the particle abluminally (transcytosis) or into degradative/retrograde/nuclear routes (retention). A "binding signature" map covers stage 1 only. My prior: stage 2 is where fate is decided for many variants, so binding mapping will be *necessary but not sufficient*.
- **Prior belief P2 — binding is not flux.** High-affinity binding can trap particles at the surface or in early compartments ("binding trap"); moderate-affinity or transient engagement may favor transcytosis. So the relationship between binding strength and transcytosis should be non-monotonic, which already breaks a naive "map binding → predict crossing" program.
- **Prior belief P3 — there exist clean positive signatures.** Engineered capsids with de novo peptide inserts that engage defined BMEC surface proteins (I expected GPI-anchored proteins and a few RMT receptors) should form a class where binding signature *does* predict transcytosis propensity well, because the inserts were selected for the whole phenotype.
- **Prior belief P4 — there exist clean counterexamples.** I expected to find at least one pair of capsids that share receptor usage but differ in fate (one transcytoses, one is retained), and at least one case where a small capsid mutation flips fate without changing receptor usage. Such cases would falsify the determinacy claim.
- **Prior belief P5 — species and model conditioning.** Mouse-derived signatures will not transfer to human BMECs (expected receptor ortholog gaps), and in vitro BBB models (primary human BMEC transwells, iPSC-BMEC, receptor-overexpression lines) will rank variants differently from in vivo. So any "determination" is conditional on species and model.
- **Prior belief P6 — structural/computational maps exist but are validated functionally.** Cryo-EM and AlphaFold models of capsid–receptor complexes will exist for a handful of pairs; they will explain binding but will not by themselves predict transcytosis.

### Predictions (stated before verification)

- **P-a.** The published record will contain an explicit statement that receptor binding alone does not determine in vivo outcome. *(Checked: yes — see BR1/BR1N, §6.1.)*
- **P-b.** A binding-signature class that predicts transcytosis will exist for mouse (LY6-class) and, more weakly, for cross-species receptors (I guessed a GPI-anchored panel plus one LDLR-family member). *(Checked: yes — LY6A, LY6C1, CA-IV, ALPL, LRP6; §4.)*
- **P-c.** In vitro binding rank will fail to fully predict in vivo transcytosis rank for at least one engineered family. *(Checked: yes — human CA-IV family, §6.3.)*
- **P-d.** A capsid engineered to bind a transcytosis receptor on a *non-BBB* scaffold will bind but not cross, showing the capsid scaffold contributes trafficking information beyond the binding epitope. *(Checked: yes — AAV1-PHP.B transplant, §6.2.)*
- **P-e.** The dominant limiting factor for a complete answer will be missing trafficking/fate data (and species-valid human BMEC systems), not missing compute. *(This drives the verdict; §9.)*

---

## 2. Operationalizing "molecular mapping"

At least four distinct things could be meant, with very different power:

| Map type | What it measures | Covers stage 1? | Covers stage 2 (sorting)? |
|---|---|---|---|
| Static interactome (cell-microarray of human membrane proteome/secretome, SPR/pulldown panels, glycan arrays) | Which host molecules a capsid binds | Yes | No |
| Structural map (cryo-EM of capsid–receptor complexes, AlphaFold/docking models, mutational epitope scans) | Geometry, epitope, affinity drivers | Yes | No |
| Perturbational genetics on BMECs (CRISPR KO/knockdown, blocking antibodies, receptor overexpression) | Which receptor is necessary for uptake/transduction | Mostly | Partially (only if coupled to transcytosis readout) |
| Functional fate map (transwell transcytosis + intracellular trafficking imaging + in vivo brain-parenchyma labeling) | Actual transcytosed-vs-retained outcome | Yes | Yes |

The question asks whether *mapping of capsid–receptor interactions* — i.e., rows 1–2, possibly row 3 — determines fate. Row 4 is not a "binding map"; it is the fate assay itself. The determinacy question is precisely: **can rows 1–3 substitute for row 4?**

A "binding signature" I will take to mean a tuple: {receptor identity and species, receptor class (GPI-anchored vs type-I transmembrane vs glycan), capsid epitope (VR-loop insert sequence and scaffold context), affinity/avidity, stoichiometry/valency, pH-dependent binding behavior}.

---

## 3. The causal chain, and what a binding map can and cannot see

Blood → (i) luminal encounter with BMEC glycocalyx/receptors → (ii) attachment → (iii) endocytosis → (iv) endosomal sorting (recycling / early-endosome escape / late endosome–lysosome degradation / transcytotic tubule or vesicle) → (v) basolateral exocytosis → (vi) penetration of basement membrane/parenchyma → (vii) secondary receptor engagement on neurons/glia.

A binding signature map observes (i)–(ii). Uptake assays extend to (iii). Fate is decided at (iv)–(v). Two structural facts in the literature make this concrete:

- Endosomal sorting, not attachment, governs transcytosis efficiency for RMT cargos: sorting away from late endosome/lysosome and into early endosomes/MVB subsets increases abluminal delivery (reviewed in https://pmc.ncbi.nlm.nih.gov/articles/PMC6513804; quantitative antibody example: https://www.ovid.com/journals/jcbfm/abstract/10.1177/0271678x17740031).
- Transcytosis and intracellular transduction are *competing* fates for AAV: blocking transcytosis dramatically increases intracellular vector and transduction of the barrier cell (https://pubmed.ncbi.nlm.nih.gov/16368273).

Also, the BBB cell actively suppresses bulk vesicular transport: brain endothelial Mfsd2a-driven lipid transport suppresses caveolae-mediated transcytosis, making low transcytosis a *cell-biological default* that capsids must actively subvert (https://pubmed.ncbi.nlm.nih.gov/28416077). Any prediction of "transcytoses" is a prediction of a rare exception to the BMEC default, which is a high bar for a binding-only model.

---

## 4. The current capsid–receptor landscape on BMECs (what is actually mapped)

**Attachment factors and entry receptors:**
- AAV9 engages terminal galactose; five capsid residues (N470, D271, N272, Y446, W503) form the glycan-binding pocket (https://pubmed.ncbi.nlm.nih.gov/22514350). AAV9 remains galactose-bound at late-endosomal pH 5.5, which alters VP variable-region dynamics (https://journals.asm.org/doi/10.1128/jvi.00843-21).
- AAVR (KIAA0319L) is an essential entry receptor for most serotypes (AAV1, 2, 3B, 5, 6, 8, 9): https://pmc.ncbi.nlm.nih.gov/articles/PMC4962915. Serotypes engage different AAVR PKD domains — AAV2 mainly PKD2, AAV5 mainly PKD1, AAV1/AAV8 need PKD1+PKD2 (https://journals.asm.org/doi/10.1128/jvi.00391-17). An AAV4/rh32.33 lineage is AAVR-independent (http://www.broad.mit.edu/publications/broad627661), and AAVR sequence origin itself dominates species-tropism differences (https://pmc.ncbi.nlm.nih.gov/articles/PMC12687847).
- AAV2 attaches via heparan sulfate proteoglycan before AAVR engagement (https://pmc.ncbi.nlm.nih.gov/articles/PMC4962915).

**BBB-transcytosis receptors identified from engineered capsids:**
- **LY6A (Sca-1):** GPI-anchored protein on brain endothelium; the receptor for AAV-PHP.B/PHP.eB; BBB transport is mouse-strain-specific via the Ly6a haplotype (https://pmc.ncbi.nlm.nih.gov/articles/PMC6520463). Ly6a CRISPR disruption or blocking antibodies reduce PHP.eB transduction of mouse BMVECs; ectopic Ly6a raises transduction ≥30-fold; this binding mode can occur independently of other known AAV receptors (https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0225206).
- **LY6C1:** mouse-restricted second RMT target; de novo LY6A- or LY6C1-binding 7-mer inserts produced hundreds of BBB-crossing capsids with tropisms predictable from target expression (https://journals.plos.org/plosbiology/article?id=10.1371%2Fjournal.pbio.3002112). Of 26 previously reported mouse BBB-crossing capsids tested, 24 engaged LY6A or LY6C1 (https://www.broadinstitute.org/news/researchers-find-gene-therapy-viral-vectors-bind-specific-protein-targets).
- **CA-IV (CA4/Car4):** primate-conserved GPI-linked enzyme; receptor for engineered variants 9P31/9P36 (https://pmc.ncbi.nlm.nih.gov/articles/PMC10115422). Capsid–Car4 complex structures are solved at atomic resolution (https://pmc.ncbi.nlm.nih.gov/articles/PMC10868842). Rhesus/marmoset CA-IV share ~85% identity with human vs ~55% for mouse; 9P31/9P36 bind mouse but not primate CA-IV (https://pmc.ncbi.nlm.nih.gov/articles/PMC12942408). AAV-hCA4-IV77, selected against human CA-IV, gives ~100-fold greater brain transduction than AAV9 in humanized mice (https://pubmed.ncbi.nlm.nih.gov/41175373).
- **ALPL (tissue-nonspecific alkaline phosphatase):** primary receptor for VCAP-102 (an AAV9 VR-4-loop 6-aa-insert variant), which gives 20–400× increased brain gene transfer vs AAV9 in rodents and NHP; direct capsid–human ALPL binding initiates receptor-mediated transcytosis in a cell-barrier model (https://pubmed.ncbi.nlm.nih.gov/40340250). An MDCK-ALPL transwell transcytoses VCAP-102 but not parental AAV9; ALPL inhibitor blocks transport; the model is used for library screening (https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf).
- **LRP6:** identified by human membrane-proteome/secretome cell-microarray screening as the BBB transcytosis receptor engaged by primate brain-enhanced engineered capsids AAV9-X1.1 and AAV.CAP-Mac; the same screen found AAV9 binding to IL3 (https://www.nature.com/articles/s41467-024-52149-0). AlphaFold models predict the engineered inserts contacting LRP6 domain E1 (https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518).
- **Retained-in-endothelium class:** AAV2 and its BMVEC-tropic variant BR1 (NRGTEWD insert) transduce brain microvascular endothelial cells with little transcytosis (https://pmc.ncbi.nlm.nih.gov/articles/PMC10036519). AAV-BR1 itself shows strong capillary endothelial expression with only sporadic neuronal transduction (https://pmc.ncbi.nlm.nih.gov/articles/PMC4888850). Another engineered variant showed a 60-fold CNS transduction increase yet failed to penetrate the BBB and was retained in microvascular endothelium (https://pmc.ncbi.nlm.nih.gov/articles/PMC10975205).

**Signature pattern worth noting up front:** four of the five validated BBB-transcytosis receptors (LY6A, LY6C1, CA-IV, ALPL) are GPI-anchored surface proteins of the BMEC luminal membrane (https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf), with LRP6 as the transmembrane (LDLR-family) exception. That clustering is the strongest "binding signature" regularity currently available — but note it is a correlation among *successes*, not a validated causal rule for sorting.

---

## 5. What the question gets right: where mapping genuinely determines fate

Within a validated receptor class, binding signatures *do* carry substantial determinative power:

- Target-focused screening for de novo LY6A/LY6C1 binding yielded BBB-crossing capsids en masse, with in vivo tropism predictable from strain-specific target expression (https://journals.plos.org/plosbiology/article?id=10.1371%2Fjournal.pbio.3002112).
- For VCAP-102, receptor identity (ALPL) plus direct binding *is* the mechanism of transcytosis, and receptor presence alone (MDCK-ALPL vs parental MDCK) is sufficient to flip the transcytosis phenotype of the same capsid (https://pubmed.ncbi.nlm.nih.gov/40340250; https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf).
- Ly6a expression is sufficient to convert non-permissive cells to PHP.eB-permissive (https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0225206).
- Receptor-focused on-column selection against human CA-IV, followed by in vivo validation, produced a human-relevant BBB-penetrant capsid (https://pubmed.ncbi.nlm.nih.gov/41175373).

So the answer to "for which signatures" has a concrete core: **insert-mediated engagement of a validated luminal RMT receptor (LY6A and LY6C1 in mouse; CA-IV, ALPL, LRP6 for translational work), on an otherwise transcytosis-competent capsid scaffold.** For these, a binding map predicts transcytosis propensity reasonably well — well enough to design capsids (https://journals.plos.org/plosbiology/article?id=10.1371%2Fjournal.pbio.3002112).

---

## 6. Where mapping fails to determine fate (the decisive counterexamples)

### 6.1 Same receptor, different fate: BR1 vs BR1N
AAV2-BR1 enters BMVECs and transduces them with minimal transcytosis; a single Q→N substitution at position 587 (BR1N) confers high BBB penetration, and the authors state that BR1 and BR1N "likely use the same receptor" and conclude that "receptor binding alone does not determine the final outcome in vivo" (https://pmc.ncbi.nlm.nih.gov/articles/PMC10036519). The same paper notes that PHP.B/PHP.eB inserts enhance BMVEC endocytosis yet the capsids then follow parental AAV9 trafficking, while BR1 follows parental AAV2 trafficking with minimal transcytosis (https://pmc.ncbi.nlm.nih.gov/articles/PMC10036519). The intracellular sorting mechanism is explicitly called unknown (https://pmc.ncbi.nlm.nih.gov/articles/PMC10036519). **This alone falsifies strong determinacy of binding signatures.**

### 6.2 Same receptor-binding epitope, different scaffold, no crossing
Transferring the PHP.B 7-mer plus adjacent AAV9 HVR-VIII residues onto AAV1 yields a capsid that binds LY6A and localizes to brain tissue yet does **not** penetrate the BBB, unlike AAV9-PHP.B (https://pubmed.ncbi.nlm.nih.gov/34346767). LY6A binding requires both the engineered peptide and specific AAV9 HVR-VIII residues (https://pubmed.ncbi.nlm.nih.gov/34346767). The scaffold encodes trafficking behavior beyond the receptor-binding epitope. Additionally, the PHP.eB 7-mer partially *destabilizes* AAVR-PKD2 engagement, and altered tropism is attributed to the combination of added LY6A interaction and weakened AAVR interaction (https://pmc.ncbi.nlm.nih.gov/articles/PMC9382559) — i.e., the *ratio* of two receptor interactions, not one binding event, tracks fate.

### 6.3 Binding rank ≠ transcytosis rank
In the human CA-IV program, two of the top in vivo performers in humanized mice were relatively low-ranked in the in vitro binding selection and outperformed several top-ranked in vitro candidates (https://pubmed.ncbi.nlm.nih.gov/41175373). Binding-selection enrichment is informative but not determinative.

### 6.4 Attaching ≠ crossing ≠ transducing
- AAV9 penetrates primary human BMVEC barriers better than AAV2 yet transduces those cells *less* well (https://pubmed.ncbi.nlm.nih.gov/27718541); AAV9 crossing is an active, cell-mediated process that does not disrupt TEER or tight junctions (https://pmc.ncbi.nlm.nih.gov/articles/PMC5298820).
- Galactose-binding-deficient AAV9 variants lose liver targeting and still transduce brain vasculature, but galactose binding is required to infect non-endothelial brain cells after crossing (https://pubmed.ncbi.nlm.nih.gov/38711458) — so "crosses" and "transduces parenchyma" are separable phenotypes with different signatures.
- AAVR itself is not fate-decisive: human AAVR missense variants can leave initial binding unchanged while altering nuclear trafficking and transduction efficiency (Ser1031Phe), or alter serotypes differentially (https://geneticmedicine.weill.cornell.edu/publications/consequences-human-genetic-variations-kiaa0319l-encoding-adeno-associated-virus-receptor-aav).
- Transcytosis and transduction compete as sinks; inhibiting transcytosis increases intracellular accumulation and transduction (https://pubmed.ncbi.nlm.nih.gov/16368273).

### 6.5 Species and model conditioning
- LY6A and LY6C1 have no primate orthologs; nearly all mouse-selected BBB-crossing capsids rely on them (https://journals.plos.org/plosbiology/article?id=10.1371%2Fjournal.pbio.3002112).
- AAVR species origin dominates species-tropism differences (https://pmc.ncbi.nlm.nih.gov/articles/PMC12687847), and 9P31/9P36 are mouse-C-IV-specific despite CA4 conservation (https://pmc.ncbi.nlm.nih.gov/articles/PMC12942408).
- Primary human BMECs are scarce, heterogeneous, and dedifferentiate in culture; iPSC-derived BMECs incompletely recapitulate the brain endothelial transcriptome (https://pmc.ncbi.nlm.nih.gov/articles/PMC12721698), though perfused iPSC-BMEC chips can model TfR-mediated transcytosis with useful dynamic range (https://pubmed.ncbi.nlm.nih.gov/37698826). A transwell selection of a shuffled AAV library identified capsids with enhanced human BBB penetration and an siRNA screen implicated host genes in transcytosis (https://pubmed.ncbi.nlm.nih.gov/36186955) — useful, but ranked outcomes remain model-dependent.

---

## 7. Synthesis: the determinacy claim, precisely

**Strong claim (binding map determines fate for all variants): falsified.** Counterexamples BR1/BR1N (same receptor, opposite fate; https://pmc.ncbi.nlm.nih.gov/articles/PMC10036519), AAV1-PHP.B (binds LY6A, does not cross; https://pubmed.ncbi.nlm.nih.gov/34346767), and in vitro/in vivo rank discordance (https://pubmed.ncbi.nlm.nih.gov/41175373) are decisive. Fate is substantially decided post-uptake by endosomal sorting (https://pmc.ncbi.nlm.nih.gov/articles/PMC6513804), against a cell-biological default of suppressed transcytosis (https://pubmed.ncbi.nlm.nih.gov/28416077).

**Moderate claim (mapping stratifies variants into propensity classes for specific signatures): supported.**
- **Predictive signatures (transcytosis-favoring):** engineered VR-loop inserts engaging GPI-anchored RMT receptors LY6A (mouse), LY6C1 (mouse), CA-IV (cross-species, human-targeted variants exist), ALPL (cross-species), or transmembrane LRP6 — with the caveat that the capsid scaffold must retain its native transcytosis-competent trafficking (AAV9-like rather than AAV2-like) and that AAVR engagement strength modulates the outcome (https://journals.plos.org/plosbiology/article?id=10.1371%2Fjournal.pbio.3002112; https://pmc.ncbi.nlm.nih.gov/articles/PMC9382559; https://pubmed.ncbi.nlm.nih.gov/40340250; https://www.nature.com/articles/s41467-024-52149-0; https://pmc.ncbi.nlm.nih.gov/articles/PMC10115422).
- **Retention-favoring signatures:** AAV2-scaffold capsids (HSPG-attachment + AAVR-PKD2) including BMVEC-tropic BR1, which transduce the endothelium with little transcytosis (https://pmc.ncbi.nlm.nih.gov/articles/PMC10036519), and variants selected purely for endothelial entry that stay in the microvasculature (https://pmc.ncbi.nlm.nih.gov/articles/PMC10975205).
- **Non-signatures:** galactose/HSPG glycan attachment predicts tissue binding and secondary transduction, not transcytosis per se (https://pubmed.ncbi.nlm.nih.gov/38711458; https://pubmed.ncbi.nlm.nih.gov/22514350).
- **Ambiguous middle:** most single capsids fall in a regime where receptor identity gives a prior but endosomal sorting decides; the sorting determinants are currently unmapped mechanistically (https://pmc.ncbi.nlm.nih.gov/articles/PMC10036519; https://pmc.ncbi.nlm.nih.gov/articles/PMC6513804).

**Therefore:** molecular mapping of capsid–receptor interactions can *determine* fate only for variants that fall inside a validated RMT-signature class, and even then it determines *propensity* (class membership), not the individual particle's fate. For variants outside those classes — and for any variant sharing receptor usage but differing in scaffold or local capsid chemistry — binding signatures cannot distinguish transcytosed from intracellularly retained. A complete determination requires adding the post-binding layer: endosomal sorting/trafficking data (live-cell or biochemical fractionation of early endosome vs late endosome/lysosome routing, pH-dependent capsid conformational behavior, and abluminal release assays) in a species-matched BMEC system.

---

## 8. What a decisive research program would require (and why it is mostly wet-lab)

1. Paired binding + transcytosis labels for a large variant panel on species-matched primary or well-validated iPSC-BMEC barriers (transwell/organ-chip with TEER control), plus intracellular fate imaging (recycling vs lysosomal colocalization) — precedent assays exist (https://pubmed.ncbi.nlm.nih.gov/27718541; https://pubmed.ncbi.nlm.nih.gov/36186955; https://pubmed.ncbi.nlm.nih.gov/37698826).
2. Receptor perturbation on both sides (KO/blocking on BMEC; ectopic expression in non-permissive cells) to separate attachment- from sorting-competence (https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0225206).
3. Structural/energetic annotation of each variant–receptor pair (cryo-EM + AlphaFold/docking as in https://pmc.ncbi.nlm.nih.gov/articles/PMC10868842; https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518; https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf).
4. In vivo parenchymal readout to confirm crossing, since in vitro rank can invert in vivo (https://pubmed.ncbi.nlm.nih.gov/41175373).

The binding map (item 3, plus interactomes) is the cheap layer. Items 1, 2, 4 are experiments; their absence — not a lack of compute — is why the determinacy question cannot currently be answered "yes."

---

## 9. Is this problem compute-bound?

The question as posed is an **epistemic/mechanistic judgment**: what can a class of measurement determine, and for which signatures? The answer is settled by published counterexamples and causal reasoning (§6–§7), which additional parallel compute does not overturn. Even a maximal mapping campaign — AlphaFold-multimer over every capsid variant × every BMEC surface protein, MD free energies, ML over library NGS — still cannot *supply* the transcytosis-vs-retention labels; those come from transwells, trafficking assays, and animals. Compute refines the map and can test whether fate is derivable from physics; it does not convert a binding map into a fate map.

Where more parallel compute *would* move the needle on sub-questions (listed in the JSON as compute_signals):
1. **Structure/energetics of capsid–receptor interfaces at scale** (AlphaFold/MD over variant × receptor matrices, including GPI-anchored vs transmembrane geometry and AAVR PKD-domain engagement): buys a quantitative, continuous "binding signature" descriptor space, and tests whether receptor class geometry predicts sorting.
2. **Endosomal-fate biophysics** (pH-dependent capsid conformational change, membrane interaction, exposure of sorting/degradation determinants — e.g., AAV9 stays galactose-bound at pH 5.5, https://journals.asm.org/doi/10.1128/jvi.00843-21): buys a test of whether post-binding fate is computable from structure — the one computational result that could upgrade "not determinable from binding" to "determinable from binding + physics."
3. **Variant-effect ML over capsid-library NGS with transcytosis labels** (deep-mutational-scanning style; precedent production/transduction models screened ~25M in silico sequences before a 100k library, https://www.voyagertherapeutics.com/wp-content/uploads/2025/05/Cox_ASGCT2025_VoyagerTherapeutics.pdf; ML viability diversification of AAV2 capsids, https://arep.med.harvard.edu/pdf/Bryant_Kelsic_ML_2021.pdf): buys generalization within a receptor class and an empirical test of whether binding-signature features suffice to predict fate labels at scale.

None of these flips the top-line answer: more compute improves the *map*; the *determination* still requires fate assays and species-matched BMEC biology.

---

## 10. Final answer (stated only now, after framing)

**No — not fully, and not in general.** Molecular mapping of capsid–receptor interactions on BMECs determines transcytosis-vs-retention only for variants inside validated receptor-mediated-transcytosis signature classes, and even there predicts *propensity* rather than per-variant fate. The signatures where mapping works are: engineered VR-loop inserts that engage luminal RMT receptors — GPI-anchored LY6A (mouse), LY6C1 (mouse), CA-IV (primate-conserved; human-targeted variants exist), ALPL (cross-species) — and transmembrane LRP6, on an AAV9-like scaffold with modulated AAVR engagement. The signatures where mapping fails are: AAV2-scaffold/HSPG-plus-AAVR engagement (retained in endothelium, e.g., BR1), any case of shared receptor usage with divergent post-binding sorting (BR1 vs BR1N), scaffold-transplanted binding epitopes (AAV1-PHP.B), and glycan-attachment signatures (galactose/HSPG) which track binding and secondary transduction, not transcytosis. The missing determinants are post-uptake endosomal sorting, which is currently unmapped and species/model-conditional. Determining fate for arbitrary variants additionally requires trafficking/assay data that no binding map — however computationally elaborated — can substitute for.

VERDICT: NOT COMPUTE-BOUND
