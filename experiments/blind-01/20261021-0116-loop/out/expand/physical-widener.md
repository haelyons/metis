# Physical widener: related problems that are compute constrained

The root question (framer.md) is judged not compute-bound in its central claim: molecular mapping of capsid–receptor binding is necessary but not sufficient for transcytosis fate, because the decision point is post-binding endosomal sorting. This file widens to *related* problems that do count as compute constrained under three tests: (i) it is still open whether more parallel compute would change the answer; (ii) compute is already known to bind; (iii) the answer is slow because its steps run one after another, even where more hardware would change only how soon it arrives, not the answer itself.

---

## Option 1: Exhaustive capsid–receptor complex enumeration (docking and AlphaFold-Multimer)

**Summary.** Enumerate binding modes of engineered capsid libraries against the BBB receptor panel (LY6A, LY6C1, ALPL, LRP6, CA4, AAVR) with docking, MD refinement, and AlphaFold-Multimer, then ask whether transcytosis-competent pairs share a geometric or energetic motif — for example 3-fold-axis engagement of GPI-anchored receptors (https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf). Published modeling covers only a handful of complexes: AlphaFold-Multimer models of LRP6 YWTD domain 1 with the AAV-X1 and AAV.CAP-Mac VR-VIII peptides, built with AlphaFold-Multimer-v3 via ColabFold v2.3.5 (https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518), and an AlphaFold model of the VCAP-102 capsid with ALPL (https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf) — against an experimental catalog of ~150 high-resolution AAV capsid structures, more than 50% determined in the last 5 years (https://pmc.ncbi.nlm.nih.gov/articles/PMC12682079).

**Root link.** Bears on Q3 — for which capsid–receptor binding signatures transcytosis occurs — specifically whether a shared interface motif marks transcytosis-competent complexes.

**Compute_open (open kind).** More parallel compute would buy model runs (capsid × receptor × pose); published measurements of its effect stop at single-digit numbers of AAV–receptor complexes modeled per study — two LRP6 peptide complexes in https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518 — and above that it is unknown whether exhaustive enumeration would surface a shared transcytosis-competent motif or demonstrate that no such motif exists.

**Sequential.** none: every capsid–receptor pair is an independent docking or AlphaFold-Multimer job with its own random seeds, so the work already splits into independent pieces.

**Narrowing.** This leaves aside everything after binding — endosomal sorting, lysosomal degradation, nuclear import — so the computed interface geometry stands in for the binding step alone, not for fate. Its answer still moves the root question because it either widens or closes the catalog of candidate signatures (Q3) against which the sufficiency claim (Q1) has to be tested.

**Sources.** https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518; https://www.voyagertherapeutics.com/wp-content/uploads/2024/05/POSTER-Voyager_ASGCT_2024_FINAL_Ishan.pdf; https://pmc.ncbi.nlm.nih.gov/articles/PMC12682079

---

## Option 2: Microsecond molecular dynamics of capsid–receptor–membrane assemblies

**Summary.** Run long MD of a capsid plus receptor in a membrane at endosomal pH to watch binding poses, pH-triggered release, and raft/curvature effects: VCAP-102 binds ALPL at Kd ~20 nM at pH 7.4 but dissociates rapidly at pH 5.5 (https://www.biorxiv.org/content/10.1101/2024.03.12.584703v1.full.pdf), and AAV9 remains galactose-attached at pH 5.5 (https://journals.asm.org/doi/abs/10.1128/jvi.00843-21). Coarse-grained Martini3 simulations of AAV2 with AAVR in a model plasma membrane reached microsecond frames and observed AAVR PKD1/PKD2 contacts lasting only ~1 µs at a time (https://pmc.ncbi.nlm.nih.gov/articles/PMC11492248).

**Root link.** Bears on Q1/Q3 — whether fate-relevant physics (pH-dependent release, membrane-domain partitioning) is already visible at the binding step, and so whether "molecular mapping" can be pushed toward a trafficking signature.

**Compute_open (settled kind).** settled: longer trajectories are already known to reveal more of the binding configurational space — the AAV2–AAVR coarse-grained study reports that once the capsid is membrane-bound its translational and rotational motion is restricted and "much longer simulation times" would be required to observe how the capsid moves on the membrane (https://pmc.ncbi.nlm.nih.gov/articles/PMC11492248).

**Sequential.** One answer waits on a chain of ~2 fs integration steps (the timestep used in the AAV2–AAVR protocol, https://pmc.ncbi.nlm.nih.gov/articles/PMC11492248), each step consuming the previous step's forces and coordinates, so one 100 ns run is ~5×10^7 sequential steps and a 1 µs run ~5×10^8; the answer needs several independent replicas (the AAV2–AAVR study reports multiple, its Figures S17–S25 and S28), and a single replica is a one-GPU job that keeps that GPU essentially fully busy (GPU offloading in gmx mdrun, https://manual.gromacs.org/documentation/current/user-guide/mdrun-performance.html). The steps must run in order inside one trajectory, but independent replicas can run at once, and recasting the answer as an ensemble of many short trajectories combined by Markov-state analysis would let them run simultaneously — a payoff only if the capsid–receptor dynamics is metastable so short runs recombine; the nearest source that has tried this is virus-capsid self-assembly MSMs built from many relatively short unbiased trajectories run in parallel (https://arxiv.org/pdf/1402.1784).

**Narrowing.** This leaves aside the cell's sorting machinery — retromer/SNX tubule engagement, lysosomal routing — and treats simulated binding/unbinding and membrane partitioning as a stand-in for the trafficking decision. Its answer still moves the root question by testing whether any fate-relevant physics is recoverable from the binding step at all, which is exactly the sufficiency issue Q1 raises.

**Sources.** https://pmc.ncbi.nlm.nih.gov/articles/PMC11492248; https://arxiv.org/pdf/1402.1784; https://www.biorxiv.org/content/10.1101/2024.03.12.584703v1.full.pdf

---

## Option 3: Supervised sequence-to-transcytosis phenotype models

**Summary.** Train sequence-to-function models on paired (capsid features, transcytosis phenotype) data to rank variants for validation. Precedents: deep models predicting AAV2 packaging viability trained on 201,426 assayed variants yielding 110,689 viable capsids (https://www.nature.com/articles/s41587-020-00793-4), and Fit4Function's six sequence-to-function models trained on libraries sized at 240K variants or less, which predicted macaque biodistribution from mouse in vivo and human in vitro data (https://pmc.ncbi.nlm.nih.gov/articles/PMC11297966).

**Root link.** Bears on Q2 — assigning each variant a fate — and on whether the binding-to-fate gap in Q1 can be closed statistically instead of mechanistically.

**Compute_open (open kind).** More parallel compute would buy model runs (seeds and architectures) and model size; published measurements of its effect stop at ensembles of three architectures (logistic regression, CNN, RNN) over ~2×10^5 labeled variants (https://www.nature.com/articles/s41587-020-00793-4) and six Fit4Function models over ≤240K-variant libraries (https://pmc.ncbi.nlm.nih.gov/articles/PMC11297966), and above that it is unknown whether more parameters, seeds, or training compute improve transcytosis prediction or whether labeled transcytosis data, not FLOPs, is the binding constraint.

**Sequential.** One training run is a chain of roughly 10^4–10^5 gradient updates, each update waiting on the previous weights' loss, so a converged answer needs multiple independent seeds and, for multi-trait prediction, one model per trait (Fit4Function trained six, https://pmc.ncbi.nlm.nih.gov/articles/PMC11297966); a single run is small enough to keep one GPU busy throughout. Within a run the updates must run in order, but different seeds and per-trait models can train at the same time — which pays off when each model fits one GPU and the labeled set is fully visible to every run, the arrangement used by Fit4Function's RNN/LSTM sequence models (https://pmc.ncbi.nlm.nih.gov/articles/PMC11297966).

**Narrowing.** This leaves aside the mechanism of the sorting decision and treats a predicted transcytosis score as a stand-in for measured transwell/in vivo fate. Its answer still moves the root question because a predictor that generalizes would show which feature set carries fate information — i.e., how far Q3's signatures can be pushed toward Q1's sufficiency claim.

**Sources.** https://www.nature.com/articles/s41587-020-00793-4; https://pmc.ncbi.nlm.nih.gov/articles/PMC11297966

---

## Option 4: Cryo-EM reconstruction of capsid–receptor complexes

**Summary.** Determine single-particle cryo-EM structures of capsid–receptor complexes — as done for AAV2–AAVR (PKD2) at 2.4 Å (https://pmc.ncbi.nlm.nih.gov/articles/PMC6561701) — to extend the ~150-structure AAV capsid library (https://pmc.ncbi.nlm.nih.gov/articles/PMC12682079) with receptor-bound interfaces; all high-resolution cryo-EM structures of capsid complexes are single-particle reconstructions averaging large numbers of homogeneous particles (https://pmc.ncbi.nlm.nih.gov/articles/PMC12682079).

**Root link.** Bears on the interface-mapping component of Q1 (which capsid residues and receptor domains contact) that feeds Q3's signatures.

**Compute_open (settled kind).** settled: map resolution is already known to improve as more particles contribute — in the AAV structural atlas, genome-containing AAV7/11/12/13 reconstructions reached slightly lower resolution than the empty capsids specifically because fewer capsids were used in those reconstructions (https://pmc.ncbi.nlm.nih.gov/articles/PMC7828300).

**Sequential.** One map waits on a chain of processing stages — motion correction, CTF estimation, particle picking, 2D classification, 3D refinement — roughly a dozen sequential stages, each consuming the previous stage's particle stack; the answer needs one reconstruction per complex plus re-runs for empty/full or symmetry-broken states (the AAV2 Rep–capsid work produced separate pentameric and hexameric maps, https://pmc.ncbi.nlm.nih.gov/articles/PMC12713660), and a single refinement keeps one GPU busy for hours to days. The stages must run in order, but the per-particle work inside a stage can run simultaneously — as in the AAV2 Rep–capsid study, where local refinements of 45,150 and 75,559 symmetry-expanded particles ran on GPU computing resources (https://pmc.ncbi.nlm.nih.gov/articles/PMC12713660) — which pays off when a dataset holds tens of thousands of independent particles.

**Narrowing.** This leaves aside affinity, kinetics, and post-binding sorting, so the static interface stands in for the whole binding event. Its answer still moves the root question because residue-level contact maps are the raw material from which any binding signature (Q3) is defined.

**Sources.** https://pmc.ncbi.nlm.nih.gov/articles/PMC7828300; https://pmc.ncbi.nlm.nih.gov/articles/PMC12713660; https://pmc.ncbi.nlm.nih.gov/articles/PMC12682079

---

## Option 5: Cross-species receptor–capsid compatibility scoring

**Summary.** Score capsid interfaces against receptor orthologs (ALPL, LRP6, AAVR, and the mouse-restricted LY6A/LY6C1) to predict which signatures translate to humans. Precedents: AlphaFold modeling of VCAP-102–ALPL predicted capsid-contacting ALPL residues conserved across human, cynomolgus macaque, and mouse (https://www.biorxiv.org/content/10.1101/2024.03.12.584703v1.full.pdf); LRP6 was picked out as a highly conserved BBB transcytosis receptor via interactome mapping plus AlphaFold-Multimer of capsid–LRP6 complexes (https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518); and LY6A/LY6C1 lack primate orthologs (https://journals.plos.org/plosbiology/article?id=10.1371%2Fjournal.pbio.3002112).

**Root link.** Bears on the species-conditionality caveat of Q3 — whether a binding signature learned in mouse survives in human.

**Compute_open (open kind).** More parallel compute would buy model runs (receptor-ortholog × capsid pairs scored); published measurements of its effect stop at a handful of isoforms — ALPL contact residues compared for one capsid across human, cynomolgus macaque, and mouse (https://www.biorxiv.org/content/10.1101/2024.03.12.584703v1.full.pdf) — and above that it is unknown whether exhaustive ortholog scoring would keep, drop, or reorder the GPI-anchored-protein and LRP6 signatures as candidates for human BBB crossing.

**Sequential.** none: each receptor-ortholog × capsid pair is an independent alignment and modeling job, so the work already splits into independent pieces.

**Narrowing.** This leaves aside mouse-only biology (Ly6a polymorphism underlies strain-specific PHP.B tropism, https://pubmed.ncbi.nlm.nih.gov/31696742) and treats interface conservation as a stand-in for actual human transcytosis. Its answer still moves the root question because translatability is a necessary filter on any signature Q3 proposes for human use.

**Sources.** https://www.biorxiv.org/content/10.1101/2024.03.12.584703v1.full.pdf; https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518; https://journals.plos.org/plosbiology/article?id=10.1371%2Fjournal.pbio.3002112
