# P1

**Angular-search saturation at fixed output count**

Proposed question: does wider rotational search improve rank1 and best50 DockQ on each frozen apo pair when retained count stays 50 and complete-workflow budgets match? MEGADOCK documents 3,600 versus 54,000 rotations; these establish available search sizes, not a quality scaling law (https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md).

- **root_link:** Bears directly on additional-search recovery and affordability, extending documented D/G comparison into a search-saturation study (file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-1649-tree/out/work/seed-20261103/R1/framer.md#problem-definition).
- **compute_open:** More parallel compute buys search width: largest rotation count documented by cited MEGADOCK guide is 54,000, with no measured quality-versus-width curve there; whether larger or differently distributed angular sets improve rank1 or best50 on these four cases remains unknown and would require an explicit sampler extension (https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md).
- **sequential:** none: rotations already split across CPU threads and GPUs, so 54,000 rotations are independent search tasks, not 54,000 dependent timesteps; per-angle voxelization/FFT/solution stages retain local dependencies (https://doi.org/10.1093/bioinformatics/btu532). Proposed minimum comparison needs four cases × two widths = eight docking runs per execution block; single-run GPU busy fraction is unreported for these inputs, and splitting angles pays only if work exceeds dispatch/merge overhead—MEGADOCK's existing rotation distribution is nearest demonstrated implementation (https://doi.org/10.1093/bioinformatics/btu532).
- **narrowing:** Leaves missing agreement margins, provenance and controller contracts to offline repair; angular coverage stands in for rigid-body sampling sufficiency, while signed rank1/best50 effects answer whether added search helps under sealed budgets.
- **source_urls:** <https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md>, <https://doi.org/10.1093/bioinformatics/btu532>

# P2

**Candidate-pool width and native-blind reranking**

Proposed question: does rescoring a wider candidate pool rescue rank1 while retaining only 50 final poses? MEGADOCK exposes output count and predictions per rotation and names ZRANK compatibility; ZRANK evaluated all 54,000 ZDOCK predictions per case, so transfer to MEGADOCK requires testing (https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md; https://zlab.wenglab.org/zlab/publications/ZRANKpaper.pdf).

- **root_link:** Bears on rank1/best50 divergence and reported 1nr5 ranking loss, while deliberately changing root's prohibition on reranking (file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-1649-tree/out/work/seed-20261103/R1/framer.md#problem-definition).
- **compute_open:** More parallel compute buys independently rescored samples: largest pool evaluated in cited ZRANK study is 54,000 poses per case, whereas MEGADOCK guide's explicit PPI example retains 10,800; above those respective evidence points, whether more candidates improve final native-blind top1/top50 or mainly add scoring distractors remains unknown for these four apo cases (https://zlab.wenglab.org/zlab/publications/ZRANKpaper.pdf; https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md).
- **sequential:** none: with pretrained scoring weights fixed, each pose's energy score can be computed independently before one global sort; ZRANK scores input structures without iterative minimization (https://zlab.wenglab.org/zlab/publications/ZRANKpaper.pdf). Proposed paired study needs four cases × two docking widths = eight upstream docking runs, then one rescoring evaluation per candidate per pool condition; cited implementation reports no GPU occupancy, and batching is an implementation proposal whose benefit requires scoring work to exceed transfer and sorting costs (https://zlab.wenglab.org/zlab/publications/ZRANKpaper.pdf).
- **narrowing:** Leaves original three-arm equivalence experiment intact as a separate prerequisite; rescored rank1/top50 quality tests whether selection, rather than lack of sampled near-native poses, limits useful recovery.
- **source_urls:** <https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md>, <https://zlab.wenglab.org/zlab/publications/ZRANKpaper.pdf>

# P3

**Apo-panel scaling and case-dependent benefit**

Proposed question: do dense-search gains and ranking losses persist across a sealed broader apo panel? PINDER-XL lists 1,955 holo test pairs and 342 apo pairs; published PINDER evaluation explicitly compares holo and apo performance (https://github.com/pinder-org/pinder; https://www.pinder.sh/blog/background).

- **root_link:** Bears on whether signed four-case quality effects reflect broader apo behavior, extending root's expressly four-case evidence boundary (file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-1649-tree/out/work/seed-20261103/R1/framer.md#gated-prospective-design).
- **compute_open:** More parallel compute buys model runs across independent cases: cited PINDER evaluation reaches 342 apo test pairs within a 1,955-pair holo panel, but does not measure MEGADOCK C/G/D effects, so their distribution even over those 342 cases—and stability on additional independently curated apo cases beyond that panel—remains unknown (https://www.pinder.sh/blog/background; https://github.com/pinder-org/pinder).
- **sequential:** none: cases and frozen arms split into independent docking jobs, as MEGADOCK's MPI master/worker execution demonstrates (https://doi.org/10.1093/bioinformatics/btu532). Proposed full listed apo panel requires 342 × three arms = 1,026 docking runs per execution block, before preparation and pose evaluation; actual eligible count needs input validation, single-run GPU busy fraction is unreported for this panel, and concurrent execution must use matched resource accounting to preserve proposed budget estimand (https://github.com/pinder-org/pinder).
- **narrowing:** Leaves exact-four-case replication as its own result; panel distribution of per-case signed DockQ differences stands in for generality of dense-search benefit, without treating deterministic repeats as new biological cases.
- **source_urls:** <https://github.com/pinder-org/pinder>, <https://www.pinder.sh/blog/background>, <https://doi.org/10.1093/bioinformatics/btu532>

# P4

**Sequential atomistic binding and conformational-path sampling**

Proposed adjacent question: do flexible pathways reveal rearrangements missed by frozen-monomer docking? Weighted-ensemble barnase–barstar study generated 203 independent binding pathways; applicability to requested four cases requires testing (https://pubs.rsc.org/en/content/articlepdf/2019/sc/c8sc04811h).

- **root_link:** Bears on apo-input and rigid-transform search limitations, extending root's frozen-input comparison to physical rearrangement pathways (file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-1649-tree/out/work/seed-20261103/R1/framer.md#identity-and-provenance-contract).
- **compute_open:** More parallel compute buys trajectory samples and ensemble members: cited association study reached 1,600 concurrent trajectories and 18 microseconds aggregate simulation; whether larger ensembles change pathway coverage or kinetic estimates, especially for these four untested systems, remains unknown (https://pubs.rsc.org/en/content/articlepdf/2019/sc/c8sc04811h).
- **sequential:** MD updates wait for prior coordinates/velocities: reported 2-fs timestep and 650 successive 20-ps WE intervals imply up to 6.5 million integration steps per lineage plus inter-interval resampling; one campaign started from 100 configurations × 16 trajectories, independent-campaign count needed for a new system remains undetermined, and reported CPU execution supplies no single-trajectory GPU busy fraction (https://pubs.rsc.org/en/content/articlepdf/2019/sc/c8sc04811h). Direct integration stays ordered; Parareal computes fine time slices concurrently with iterative boundary correction, paying only with cheap accurate coarse dynamics and few corrections—nearest cited trial used two simpler MD examples, not protein binding (https://doi.org/10.1103/PhysRevE.66.057701).
- **narrowing:** Leaves original execution-equivalence and fixed-budget three-arm claim aside; pathway coverage and kinetics probe whether physical flexibility creates a limit that denser rigid rotations alone cannot diagnose.
- **source_urls:** <https://pubs.rsc.org/en/content/articlepdf/2019/sc/c8sc04811h>, <https://doi.org/10.1103/PhysRevE.66.057701>

# P5

**Fixed-batch docking latency through parallel execution**

Settled execution example: MEGADOCK reported 98% strong-scaling efficiency at 420 nodes relative to 35 nodes for 30,976 docking jobs, and separately completed one million docking jobs in 11.51 hours; this supports large-batch execution acceleration within measured regime (https://doi.org/10.1093/bioinformatics/btu532).

- **root_link:** Bears on execution acceleration, while root's complete-workflow timing and allocation-dollar estimands still require their own measurements (file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-1649-tree/out/work/seed-20261103/R1/framer.md#problem-definition).
- **compute_open:** settled: more parallel hardware reduces completion time for a fixed docking batch within tested regime—30,976 jobs scaled from 35 to 420 nodes with 98% efficiency at largest node count; separate largest workload reported was one million jobs, not evidence that extra hardware improves biological ranking or lowers allocation cost (https://doi.org/10.1093/bioinformatics/btu532).
- **sequential:** none: fixed protein-pair jobs distribute through MPI master/worker scheduling, while rotations distribute across CPU cores and GPUs within each worker; nearest tested implementation is MEGADOCK itself (https://doi.org/10.1093/bioinformatics/btu532). Published scaling batch contains 30,976 docking jobs with five timing measurements, each worker node using 12 CPU cores and three K20X GPUs; neither job count nor three-GPU allocation establishes one run's fraction of a single GPU, which source does not report (https://doi.org/10.1093/bioinformatics/btu532).
- **narrowing:** Leaves search breadth and scientific answer fixed; time to finish a predeclared batch stands in for execution latency only, so established throughput scaling cannot establish dense-search recovery or fixed-cap affordability.
- **source_urls:** <https://doi.org/10.1093/bioinformatics/btu532>

