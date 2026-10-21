# Physical widener: related problems that are compute constrained

The framer's root question — whether molecular mapping of AAV capsid–receptor interactions on BMECs determines transcytosis versus intracellular retention, and for which binding signatures (framer.md) — is itself not compute-bound (framer.md §9). Widening the definition as instructed (a related problem counts as compute constrained both where it is still open whether more parallel compute would change its answer, and where compute is already known to bind; and also where the answer is late only because its steps run one after another), four related problems qualify.

## structure-matrix

Structure/energetics of capsid–receptor interfaces at scale: AlphaFold-Multimer and docking over a capsid-variant × BMEC-receptor matrix (GPI-anchored LY6A/LY6C1/CA-IV/ALPL versus transmembrane LRP6 and AAVR PKD domains), yielding a continuous binding-signature descriptor space and a test of whether receptor-class geometry predicts sorting. Per pair, the largest published compute allocation is 5 AlphaFold models with up to 20 recycles (https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518); the field at large has run >200 million predictions (https://www.ebi.ac.uk/about/news/technology-and-innovation/alphafold-200-million/). Open whether more pairs/seeds change the answer: post-binding sorting determinants are unmapped (https://pmc.ncbi.nlm.nih.gov/articles/PMC10036519).

## endosome-md

pH-resolved capsid and glycan dynamics by simulation (extending the cryo-EM pH series where AAV9 stays galactose-bound at pH 5.5, https://pmc.ncbi.nlm.nih.gov/articles/PMC8428384): the one computational result that could upgrade "not determinable from binding" to "determinable from binding + physics". Sequential-latency-bound: each 2 fs step waits on the previous coordinates (~250 million steps per 500 ns run, one GPU per replica). Largest published sampling: 3 μs total (500 ns × 2 serotypes × 3 pHs, https://doi.org/10.3390/pharmaceutics18091053); open whether converged sampling exposes sorting determinants correlating with fate labels.

## library-ml

Variant-effect ML over capsid-library NGS with transcytosis-versus-retention labels (deep-mutational-scanning style). This is the kind where compute is already known to bind: in-silico prescreening of ~25 million candidates (https://www.voyagertherapeutics.com/wp-content/uploads/2025/05/Cox_ASGCT2025_VoyagerTherapeutics.pdf) and then 1.7 billion candidates (https://www.voyagertherapeutics.com/wp-content/uploads/2026/05/POSTER_Voyager_LeveragingArtificialIntelligencetoDesignAAVMutantCapsidsOptimizedforAntibodyEvasion_May_2026_FINAL.pdf) changed which mutants were built, in a region where >90% of random mutants are nonviable; ensembles of models helped all designs (https://www.nature.com/articles/s41587-020-00793-4).

## cryoet-refinement

Cryo-ET/cryo-EM averaging of capsid–receptor complexes to epitope-level resolution (interface maps for LRP6/CA-IV/ALPL/LY6A engagement). Compute buys particles averaged and hence resolution: 159,660 symmetry-expanded particles from 46 tomograms (https://pmc.ncbi.nlm.nih.gov/articles/PMC11381518); AAV capsid maps reach 1.56–1.86 Å with per-particle refinement (https://www.nature.com/articles/s41467-018-06076-6). Sequential: iterative classification/refinement rounds (GPU-parallelized in RELION-2, https://elifesciences.org/articles/18722). Open whether higher-resolution interfaces separate same-receptor different-fate capsids (https://pmc.ncbi.nlm.nih.gov/articles/PMC10036519).
