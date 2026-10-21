# Framing: Can molecular mapping of AAV capsid–receptor interactions on brain microvascular endothelial cells determine transcytosis fate and its binding signatures?

---

## 1. Current understanding (relayed before analysis)

### 1.1 The system

AAV (adeno-associated virus) is the leading in vivo gene-therapy vector; systemic delivery to the CNS requires crossing the blood-brain barrier (BBB), whose wall is formed by brain microvascular endothelial cells (BMECs/BMVECs) with tight junctions and low vesicular density (https://pmc.ncbi.nlm.nih.gov/articles/PMC7765129; https://pmc.ncbi.nlm.nih.gov/articles/PMC6513804). The BBB is not absolutely impermeable to large molecules: multiple proteins cross it by receptor-mediated transcytosis (RMT), classically via the transferrin receptor (TfR), insulin receptor, and LDL receptor family (https://pmc.ncbi.nlm.nih.gov/articles/PMC6513804). In brain endothelium, caveolae-mediated transcytosis is actively suppressed by Mfsd2a-dependent lipid transport, which keeps BBB transcytosis tightly regulated and low relative to peripheral endothelia (https://pmc.ncbi.nlm.nih.gov/articles/PMC7765129; https://www.mdpi.com/2218-273X/15/4/456).

### 1.2 AAV variants that cross the BBB vs. those that stay in the endothelium

- **AAV9** crosses the BBB after intravenous administration in rodents, cats, pigs, and non-human primates (https://pubmed.ncbi.nlm.nih.gov/27718541). In primary human BMVEC transwell models, AAV9 penetrates the barrier by an active, cell-mediated process without disrupting TEER or tight-junction markers, and with minimal transduction of the BMVECs themselves (https://pmc.ncbi.nlm.nih.gov/articles/PMC5298820). Two-photon imaging shows AAV9 traffics through tubular transport vesicles and accumulates at the basolateral aspect, consistent with transcytosis rather than nuclear import (https://pmc.ncbi.nlm.nih.gov/articles/PMC5298820).
- **AAV2** does not appreciably cross the BBB; it is endocytosed by BMVECs and trafficked to the nucleus, transducing the endothelium with little transcytosis (https://pmc.ncbi.nlm.nih.gov/articles/PMC5298820; https://pmc.ncbi.nlm.nih.gov/articles/PMC10036519).
- **AAV-PHP.B / PHP.eB** (AAV9-derived, 7-mer insert in VR-VIII) cross the mouse BBB with ~40–60-fold greater brain transduction than AAV9, but this is restricted to mouse strains expressing membrane-localized **LY6A (SCA-1)** and does not translate to primates (https://pmc.ncbi.nlm.nih.gov/articles/PMC6520463; https://pubmed.ncbi.nlm.nih.gov/31725765; https://neuroscience.caltech.edu/documents/21479/Sullivan_Abstract_r2022.pdf). LY6A is a GPI-anchored protein; no primate ortholog exists (https://journals.plos.org/plosbiology/article?id=10.1371%2Fjournal.pbio.3002112; https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf).
- **LY6C1**, a related GPI-anchored protein, was identified as a second BBB receptor for engineered AAV capsids; de novo capsid–receptor targeting to LY6A or LY6C1 yields potent vectors with predictable tropisms (https://journals.plos.org/plosbiology/article?id=10.1371%2Fjournal.pbio.3002112).
- **VCAP-102** (an AAV9 variant with a 6-aa insert in VR-IV, selected by TRACER) shows 20–400-fold increased brain gene transfer in rodents and primates and uses **ALPL** (tissue-nonspecific alkaline phosphatase) as its primary receptor; direct binding of VCAP-102 to human ALPL initiates receptor-mediated transcytosis in a cell-barrier model (https://pubmed.ncbi.nlm.nih.gov/40340250; https://www.globenewswire.com/news-release/2025/05/15/3082003/36461/en/voyager-demonstrates-alpl-receptor-mediated-blood-brain-barrier-transport-of-novel-aav-capsids-in-molecular-therapy-publication.html). ALPL is a GPI-anchored protein, as are LY6A, LY6C1, and CA4 (https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf).
- **AAV9-X1.1 / AAV-X1 family** shows endothelial-specific tropism in mice that shifts to enhanced neuronal tropism (i.e., transcytosis) in macaque; **LRP6** was identified as a BBB transcytosis receptor for these capsids, a highly conserved target with human-relevant binding sites (https://www.nature.com/articles/s41467-024-52149-0; https://www.nature.com/articles/s41467-023-38582-7). AAV-BI30 also binds LRP6-E1E2 (https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518).
- **BR1** (an AAV2 variant with an NRGTEWD insert) transduces BMVECs with little transcytosis, whereas a single Q→N substitution at position 587 (BR1N) confers strong BBB penetration; BR1 and BR1N likely use the same receptor, yet one residue profoundly changes fate (https://pmc.ncbi.nlm.nih.gov/articles/PMC10036519).

### 1.3 Receptor and entry biology

- **AAVR (KIAA0319L)** is the universal proteinaceous AAV entry receptor for most serotypes; it rapidly endocytoses from the plasma membrane and traffics to the trans-Golgi network (TGN) (https://pmc.ncbi.nlm.nih.gov/articles/PMC4962915; https://pubmed.ncbi.nlm.nih.gov/26814968). Glycans (heparan sulfate for AAV2; sialic acid for AAV1/4/5; terminal galactose for AAV9) act as attachment factors rather than entry receptors (https://www.sciencedirect.com/science/article/pii/S0966842X2100216X; https://pubmed.ncbi.nlm.nih.gov/21330365; https://journals.asm.org/doi/10.1128/jvi.00448-12).
- AAV9 binds terminal N-linked galactose via a pocket (N470, D271, N272, Y446, W503) at the base of the 3-fold protrusions (https://journals.asm.org/doi/10.1128/jvi.00448-12). Cryo-EM at endosomal pHs shows AAV9 remains galactose-attached at pH 5.5, which may matter for sorting during trafficking (https://journals.asm.org/doi/abs/10.1128/jvi.00843-21).
- AAVR itself is not a simple plasma-membrane receptor: cell-surface attachment is AAVR-independent in some contexts, and AAVR acts as a retromer cargo driving endosome-to-TGN transport (https://pmc.ncbi.nlm.nih.gov/articles/PMC13483459; https://pmc.ncbi.nlm.nih.gov/articles/PMC8413391). Even in AAVR-knockout cells, AAV genomes can be detected, indicating a post-attachment trafficking role (https://pmc.ncbi.nlm.nih.gov/articles/PMC10975205). An alternate receptor AAVR2 (carboxypeptidase D) enables AAVR-independent transduction of clade E AAVs (https://www.rcsb.org/structure/9J6Z).
- Cryo-EM and crosslinking-MS have solved AAV2–AAVR (PKD2) at 2.4 Å (https://pmc.ncbi.nlm.nih.gov/articles/PMC6561701), AAV1–AAVR and AAV5–AAVR complexes showing divergent binding modes (https://pmc.ncbi.nlm.nih.gov/articles/PMC6704107), and the PHP.eB capsid structure at 2.24 Å showing that the engineered 7-mer loop conformation dictates AAVR (PKD2) binding strength and LY6A-binding availability (https://pmc.ncbi.nlm.nih.gov/articles/PMC9382559). A library of ~150 high-resolution AAV cryo-EM structures now exists (https://www.sciencedirect.com/science/article/pii/S2329050125002244).

### 1.4 Post-binding steps determine fate

Transcytosis across BBB endothelium requires: (1) luminal binding, (2) endocytosis (clathrin, caveolae, or macropinocytosis), (3) sorting away from late endosome/lysosome degradation toward a transcytotic route, (4) trafficking to the abluminal membrane, and (5) exocytosis (https://pmc.ncbi.nlm.nih.gov/articles/PMC6337067). Classic RMT biology shows that binding alone does not set the itinerary: high-affinity or bivalent anti-TfR antibodies are sorted to lysosomes, whereas monovalent or low-affinity binders are sorted to transcytosis (https://pmc.ncbi.nlm.nih.gov/articles/PMC6513804; https://pubmed.ncbi.nlm.nih.gov/29877588). For AAV specifically, AAV5 transcytosis uses an entry pathway independent of its transduction pathway (https://pubmed.ncbi.nlm.nih.gov/16368273), and inhibiting transcytosis increases intracellular vector and transduction, demonstrating that transcytosis and transduction are competing fates (https://pubmed.ncbi.nlm.nih.gov/16368273; https://pmc.ncbi.nlm.nih.gov/articles/PMC10975205). The BR1/BR1N comparison is the cleanest AAV demonstration that receptor binding alone does not determine the in vivo outcome (https://pmc.ncbi.nlm.nih.gov/articles/PMC10036519). More generally, "receptor binding alone does not fully explain AAV tissue tropism in vivo" (https://pmc.ncbi.nlm.nih.gov/articles/PMC12926770).

### 1.5 Computational tools in play

Machine learning has been applied to AAV capsid design for viability/packaging and tropism (https://arep.med.harvard.edu/pdf/Bryant_Kelsic_ML_2021.pdf; https://pubmed.ncbi.nlm.nih.gov/40176349), including multi-objective models predicting liver tropism and manufacturability across species (https://www.news-medical.net/news/20240809/Machine-learning-revolutionizes-gene-delivery.aspx) and prescreening of production-fitness for library design (https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Cox.pdf). AlphaFold-Multimer has been used to model capsid–receptor complexes (e.g., VCAP-102–ALPL; LRP6–X1/CAP-Mac) (https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf; https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518).

---

## 2. Predictions (made before deep analysis)

**P1.** Molecular mapping of capsid–receptor binding on BMECs will be **necessary but not sufficient** to classify variants as transcytosing vs. intracellularly retained. Binding identity and interface structure constrain fate but do not determine it, because the decision point is intracellular sorting, not surface engagement.

**P2.** A **receptor-class signature** will correlate with transcytosis: engagement of GPI-anchored proteins (LY6A, LY6C1, ALPL, CA4) will associate with BBB crossing more strongly than engagement of AAVR or HSPG/glycan attachment factors, because GPI-APs reside in lipid-raft/caveolar domains implicated in transcytotic transport.

**P3.** That correlation will have **known exceptions** (BR1 vs. BR1N with the same receptor; AAV2 vs. BR1 both BMVEC-tropic with different fates), proving that binding signatures underdetermine outcome.

**P4.** No purely structural/biophysical signature (contact residues, Kd, stoichiometry) will be found that is both necessary and sufficient for transcytosis across species; the missing variable is the capsid/receptor's post-endocytic sorting behavior.

**P5.** The problem as posed will therefore **not be compute-bound**: the decisive evidence is mechanistic and empirical (trafficking assays, single-amino-acid counterexamples), not a matter of insufficient computation. Compute can expand the catalog of binding signatures but cannot close the causal gap from binding to transcytosis.

---

## 3. Problem definition (before answering)

### 3.1 What exactly is being asked

The question contains three nested sub-questions:

- **Q1 (sufficiency):** Can *molecular mapping* of capsid–receptor interactions on BMECs *determine* (i.e., predict/classify) which AAV variants transcytose the BBB vs. remain intracellular?
- **Q2 (phenotype assignment):** For each variant, which fate does it have?
- **Q3 (signature identification):** For which *capsid–receptor binding signatures* does transcytosis occur?

"Molecular mapping" is ambiguous and must be decomposed. It could mean any of:
(a) **Interaction discovery**: which receptor does a capsid bind (affinity proteomics, CRISPR screens, SPR/BLI panels);
(b) **Interface mapping**: which capsid residues and receptor domains contact (cryo-EM, crosslinking-MS, mutagenesis);
(c) **Energetics**: Kd, kon/koff, stoichiometry, pH dependence;
(d) **Structural signatures**: loop conformations, insert topologies, glycan-binding pockets.

Each of these characterizes the **binding step only**. Transcytosis fate is an emergent property of the entire pathway: binding → internalization → endosomal sorting → transcytotic trafficking → abluminal exocytosis, competing with lysosomal degradation and nuclear import/transduction of the endothelium (https://pmc.ncbi.nlm.nih.gov/articles/PMC6337067; https://pmc.ncbi.nlm.nih.gov/articles/PMC10975205).

### 3.2 The causal chain and where information is lost

```
Capsid + Receptor on BMEC
        │  ← molecular mapping lives HERE (Kd, contacts, structure)
        ▼
   Endocytosis (clathrin / caveolae / macropinocytosis)
        ▼
   Early endosome sorting station                    ← fate decision lives HERE
        ├──► transcytotic tubule/vesicle ──► abluminal exocytosis  = BBB crossing
        ├──► late endosome / lysosome                                = degradation
        └──► TGN / nucleus (endothelial transduction)                = intracellular retention
```

The mapping information is generated upstream of the sorting decision. Two capsids with identical receptor binding can be sorted differently; conversely, two capsids with different binding modes can converge on the same transcytotic route. Therefore **there is a many-to-one and one-to-many relationship between binding signature and fate**, and no function f(binding_signature) → {transcytose, retain} can be exact without additional variables.

### 3.3 The decisive empirical counterexample

**BR1 vs. BR1N**: same receptor on BMVECs, one amino acid (Q587N) changes the outcome from endothelial transduction with little transcytosis to robust BBB penetration and neuronal transduction. The authors conclude: "receptor binding alone does not determine the final outcome in vivo" (https://pmc.ncbi.nlm.nih.gov/articles/PMC10036519). This single result falsifies the strong form of Q1 ("mapping determines fate") unless "molecular mapping" is expanded to include features that encode post-binding behavior (e.g., receptor oligomerization state, membrane-domain partitioning, endocytic motif engagement) — but those are no longer purely "capsid–receptor binding" signatures; they are trafficking signatures.

### 3.4 The second independent line of evidence: RMT affinity/valency

For TfR-directed antibodies at the BBB, monovalent or lower-affinity binders are sorted to transcytosis while bivalent/high-affinity binders are sorted to lysosomes (https://pmc.ncbi.nlm.nih.gov/articles/PMC6513804; https://pubmed.ncbi.nlm.nih.gov/29877588). Here the *same receptor* yields opposite fates depending on binding mode (valency, affinity) — i.e., even the binding signature's quantitative parameters are not sufficient; the cell's sorting machinery reads avidity/cluster size. Transcytosis rates were directly proportional to partition into early endosome fractions (https://pmc.ncbi.nlm.nih.gov/articles/PMC5888858).

### 3.5 What mapping *can* contribute (the partial answer)

1. **Receptor identity** is strongly informative at the family level:
   - GPI-anchored receptor engagement (LY6A, LY6C1, ALPL) associates with BBB transcytosis in mouse and, for ALPL, in cross-species/human cell-barrier models (https://pmc.ncbi.nlm.nih.gov/articles/PMC6520463; https://journals.plos.org/plosbiology/article?id=10.1371%2Fjournal.pbio.3002112; https://pubmed.ncbi.nlm.nih.gov/40340250).
   - LRP6 engagement associates with primate-relevant BBB transcytosis for X1.1-family capsids (https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518).
   - AAVR/galactose engagement is compatible with both fates (AAV9 crosses; AAV2 does not; PHP.eB weakens AAVR while gaining LY6A) (https://pmc.ncbi.nlm.nih.gov/articles/PMC9382559; https://pmc.ncbi.nlm.nih.gov/articles/PMC5298820).
2. **Interface geometry/topology**: the PHP.eB 7-mer bent-loop conformation tunes AAVR affinity and LY6A availability (https://pmc.ncbi.nlm.nih.gov/articles/PMC9382559); VCAP-102's 6-aa VR-IV insert mediates ALPL binding at the 3-fold axis (https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf); AAV9's galactose pocket sits at the base of 3-fold protrusions (https://journals.asm.org/doi/10.1128/jvi.00448-12).
3. **Species conservation of the receptor** is a necessary translatability filter: LY6A/LY6C1 are mouse-specific; ALPL and LRP6 are conserved (https://journals.plos.org/plosbiology/article?id=10.1371%2Fjournal.pbio.3002112; https://pubmed.ncbi.nlm.nih.gov/40340250; https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518).

### 3.6 What mapping cannot determine without functional assays

- Whether a bound complex is internalized via a transcytosis-competent route (caveolar/lipid-raft vs. clathrin-to-lysosome) (https://pmc.ncbi.nlm.nih.gov/articles/PMC6337067; https://pmc.ncbi.nlm.nih.gov/articles/PMC7765129).
- Whether the capsid escapes endosomes (PLA2-dependent) toward nuclear import instead of crossing (https://pmc.ncbi.nlm.nih.gov/articles/PMC8413391).
- Quantitative partition between early-endosome transcytotic tubules and late-endosome/lysosome degradation (https://pmc.ncbi.nlm.nih.gov/articles/PMC5888858).
- Species- and strain-specific receptor expression (Ly6a polymorphism underlies strain-specific PHP.B tropism) (https://pubmed.ncbi.nlm.nih.gov/31696742).

### 3.7 Reformulation of the question

Q1 is best answered as: *partially — mapping identifies the receptor-class and interface correlates of transcytosis, but cannot alone determine fate; fate requires a trafficking readout.* Q3 is best answered as: *the strongest available signature is engagement of a GPI-anchored luminal receptor (LY6A/LY6C1/ALPL, and by extension CA4) or of conserved RMT receptors like LRP6, with caveats (same-receptor different-fate cases; species-restricted receptors).*

---

## 4. Deep analysis

### 4.1 Is there a "binding signature" that is predictive?

The literature supports a **probabilistic, class-level signature** rather than a deterministic residue-level one:

- **Signature S1 (GPI-AP engagement):** PHP.B/PHP.eB (LY6A), engineered LY6C1-targeting capsids, VCAP-102 (ALPL). Mechanistic plausibility: GPI-APs partition into lipid rafts and undergo apical-to-basolateral transcytotic delivery in polarized cells (https://www.cell.com/molecular-therapy-family/molecular-therapy/fulltext/S1525-0016(19)30054-1), and the Voyager model explicitly groups LY6A, LY6C1, CA4, ALPL as a GPI-AP receptor family for BBB transport (https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf).
- **Signature S2 (conserved RMT receptor engagement):** LRP6 for AAV9-X1.1/BI30 family (https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518).
- **Signature S3 (AAVR engagement strength):** PHP.eB's altered tropism arises from *weakening* AAVR/PKD2 interaction while gaining LY6A — suggesting that reduced AAVR-driven TGN/nuclear routing plus a transcytotic receptor is favorable for crossing (https://pmc.ncbi.nlm.nih.gov/articles/PMC9382559).
- **Non-signatures:** glycan attachment (galactose for AAV9, HS for AAV2) is compatible with both fates and is not predictive (https://pmc.ncbi.nlm.nih.gov/articles/PMC5298820; https://pubmed.ncbi.nlm.nih.gov/21330365).

**Counterexample pressure on all signatures:** BR1/BR1N shows one residue flips fate within a fixed receptor usage (https://pmc.ncbi.nlm.nih.gov/articles/PMC10036519); AAV2 and BR1 share BMVEC transduction with little crossing while AAV9 and BR1N cross (https://pmc.ncbi.nlm.nih.gov/articles/PMC10036519; https://pmc.ncbi.nlm.nih.gov/articles/PMC5298820). Hence no residue-level binding signature is sufficient.

### 4.2 The species problem

Any signature learned in mouse (LY6A/LY6C1) is not automatically valid in human: LY6A/LY6C1 lack primate orthologs (https://journals.plos.org/plosbiology/article?id=10.1371%2Fjournal.pbio.3002112), and PHP.eB failed in NHPs (https://neuroscience.caltech.edu/documents/21479/Sullivan_Abstract_r2022.pdf). Human-relevant signatures must involve conserved receptors (ALPL, LRP6) or conserved expression patterns (https://pubmed.ncbi.nlm.nih.gov/40340250; https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518). This is a biological constraint on the signature space, not a computational one.

### 4.3 Could compute change this?

Compute enters at:
- **(a) Structural enumeration:** docking/MD/AlphaFold-Multimer across capsid libraries × receptor panels to classify binding modes (in the spirit of https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518 and https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf). This expands the *catalog* of S1–S3-like signatures but cannot validate fate.
- **(b) ML on paired (binding features, transcytosis phenotype) data:** sequence→function models are feasible for capsid properties (https://arep.med.harvard.edu/pdf/Bryant_Kelsic_ML_2021.pdf; https://pubmed.ncbi.nlm.nih.gov/40176349), but the label "transcytoses across human BBB" requires experimental transwell/in vivo measurements; the bottleneck is labeled data, not FLOPs.
- **(c) Simulating post-binding trafficking** (endosomal sorting, retromer/SNX tubule engagement, GPI-AP raft partitioning) — currently beyond tractable whole-system simulation, and in any case the decisive variables are cell-biological (https://pmc.ncbi.nlm.nih.gov/articles/PMC6513804).

**The core answer to Q1 is fixed by mechanistic logic and existing counterexamples (BR1/BR1N; TfR affinity/valency; AAV5 transcytosis independent of transduction pathway).** More parallel compute cannot overturn these; it can only refine the signature catalog (Q3) and prioritize experiments. Therefore the problem is **not compute-bound** in its central claim.

### 4.4 Where parallel compute *would* materially help (candidate compute signals)

1. **Exhaustive binding-signature enumeration** across engineered capsid libraries vs. the BBB receptor panel (LY6A, LY6C1, ALPL, LRP6, CA4, AAVR) via docking/MD/AF-Multimer — could reveal whether transcytosis-competent complexes share a geometric/energetic motif (e.g., 3-fold-axis engagement of GPI-APs) beyond the handful of published structures.
2. **Supervised learning of transcytosis phenotype from (sequence, receptor, structural, biophysical) features**, once paired transwell/in vivo labels exist — could convert class-level correlations into quantitative predictors and rank variants for validation.
3. **Cross-species receptor–capsid compatibility scoring** (comparative structural genomics of receptor orthologs + capsid interface conservation) — could predict translatability of a binding signature from mouse to human, addressing the LY6A-to-ALPL/LRP6 gap.

None of these change the qualitative answer to Q1 ("mapping alone is insufficient"); they change the completeness and precision of Q3 ("for which signatures") and the experimental prioritization. Since the question's headline claim is decided by biology rather than compute, the verdict stands.

---

## 5. Synthesis

- **Q1:** No — molecular mapping of capsid–receptor binding on BMECs is necessary but not sufficient to determine transcytosis vs. intracellular retention. The fate decision is made by post-binding endosomal sorting, and the same binding signature can yield either fate (BR1 vs. BR1N; TfR affinity/valency; AAV5 transcytosis independent of transduction pathway).
- **Q2:** Phenotype assignment requires functional readouts (transwell transcytosis, in vivo CNS transduction vs. endothelial transduction, endosomal colocalization).
- **Q3:** The best-supported binding signatures associated with transcytosis are: (i) engagement of GPI-anchored luminal receptors (LY6A, LY6C1, ALPL; CA4 by family extension), (ii) engagement of conserved RMT receptors (LRP6), and (iii) weakened AAVR/TGN-routing combined with a transcytotic receptor. Glycan attachment signatures (galactose, HS) are not predictive. All signatures are probabilistic and species-conditional.

The problem is **NOT COMPUTE-BOUND**: the decisive reasoning is causal/mechanistic and rests on published counterexamples and cell-biological sorting logic; parallel compute refines signature catalogs and prioritizes experiments but cannot establish sufficiency of binding for transcytosis.

---

VERDICT: NOT COMPUTE-BOUND
