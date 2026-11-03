# Related compute-constrained problems

Scope: research options, no execution. Root frames separate acceleration, scientific-agreement and added-search questions; current protocol gaps remain outside these computational extensions ([root](file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md)). “Open” below means extra compute's effect on specified answer remains unestablished; “settled” marks demonstrated compute sensitivity on a stated workload. GPU allocation is not measured GPU utilization; missing utilization values remain explicit.

## P1

**Title:** Denser rigid-body search: recovery versus ranking

**Summary:** Question: does added angular search improve rank1 and best50 DockQ under common complete-workflow budgets? Root separates these outcomes; MEGADOCK documents 3,600 standard rotations and 54,000 dense rotations, without establishing their quality difference (file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md; https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md). Proposed extension: measure quality versus search width while holding scoring and retention fixed.

**Root link:** Directly bears on GPU-dense minus GPU-standard rank1 and best50 DockQ, conditional on both complete workflows fitting sealed budgets (file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md).

**Compute open:** More parallel compute buys search width: largest documented angular search in cited guide is 54,000 rotations, versus 3,600 standard; guide supplies settings, not a quality-scaling experiment, so whether still denser coverage improves either DockQ outcome remains unknown here (https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md).

**Sequential:** none: rotation calculations already parallelize through OpenMP and docking jobs distribute through MPI; angles need no preceding angle's result, although ranking and decoy reconstruction wait for docking output (https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md).

**Narrowing:** Leaves protocol repair and numerical acceptance criteria aside; search-width response stands in for added-search value, while preserving root's separate rank1/best50 outcomes (file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md).

**Sources:**

- [Source 1](https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md)
- [Source 2](file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md)

## P2

**Title:** Fixed-search docking throughput

**Summary:** Question: how soon can unchanged docking searches finish? Developer benchmark reports 352 dockings taking 67.1 hours on one CPU core, 2.26 hours with 12 CPU cores plus one GPU, and 1.02 hours with 12 CPU cores plus three GPUs; hardware was Tesla K20X (https://www.bi.cs.titech.ac.jp/megadock/perform.html). This establishes acceleration for that benchmark.

**Root link:** Bears on root's CPU-standard/GPU-standard acceleration estimand, whose complete-workflow timing boundary is broader than published docking timings (file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md; https://www.bi.cs.titech.ac.jp/megadock/perform.html).

**Compute open:** settled: parallel hardware reduced fixed docking workload time in reported benchmark, from 67.1 hours on one CPU core to 1.02 hours on 12 CPU cores plus three GPUs; this establishes compute sensitivity there, while root's complete-workflow ratio still requires measurement (https://www.bi.cs.titech.ac.jp/megadock/perform.html; file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md).

**Sequential:** none: independent docking jobs distribute through MPI and rotations parallelize through OpenMP; fixed predictions still require downstream decoy generation after docking output exists (https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md).

**Narrowing:** Leaves additional-search quality and scientific agreement gates aside; docking time is a component of root's complete-workflow time, not a substitute for its measured ratio (file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md).

**Sources:**

- [Source 1](https://www.bi.cs.titech.ac.jp/megadock/perform.html)
- [Source 2](https://raw.githubusercontent.com/akiyamalab/MEGADOCK/master/doc/README.md)
- [Source 3](file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md)

## P3

**Title:** Massive multimer sampling and long recycling

**Summary:** Question: can many independently initialized complex predictions recover good poses and rank them reliably? AFsample generated about 6,000 models per target and increased mean DockQ from 0.41 to 0.55 relative to its AlphaFold-Multimer baseline; T1187o still included confidently wrong orientations (https://pmc.ncbi.nlm.nih.gov/articles/PMC10534052/). MassiveFold distributes prediction batches across GPUs (https://pmc.ncbi.nlm.nih.gov/articles/PMC11578886/).

**Root link:** Bears on root's distinction between finding a good pose among candidates and placing it first, through an alternative complex-prediction method outside its frozen MEGADOCK arms (file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md).

**Compute open:** More parallel compute buys model runs/seeds: largest per-target sample count reported across these cited studies is approximately 6,000, with measured DockQ gains but remaining ranking errors; whether larger samples improve selected rank1 or best50 rather than merely generating more good candidates remains unestablished by them (https://pmc.ncbi.nlm.nih.gov/articles/PMC10534052/; https://pmc.ncbi.nlm.nih.gov/articles/PMC11578886/).

**Sequential:** One prediction waits on successive recycles of its preceding state: MassiveFold reports an example stopping at recycle 164 under a 1,000-recycle cap, while AFsample's sampled answer used about 6,000 separate predictions; MassiveFold schedules down to one prediction per GPU, but reports no fraction of GPU utilization for that run (https://pmc.ncbi.nlm.nih.gov/articles/PMC11578886/; https://pmc.ncbi.nlm.nih.gov/articles/PMC10534052/). Recycles remain ordered under this recurrence; independent seeds can run concurrently when GPU memory/resources suffice, as MassiveFold demonstrated, but that change shortens ensemble completion rather than removing one seed's dependency chain (https://pmc.ncbi.nlm.nih.gov/articles/PMC11578886/).

**Narrowing:** Leaves identical monomer-only docking inputs and CPU/GPU equivalence aside; ranked complex-prediction DockQ probes whether more search fixes candidate coverage or candidate selection, root's central quality distinction (file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md).

**Sources:**

- [Source 1](https://pmc.ncbi.nlm.nih.gov/articles/PMC10534052/)
- [Source 2](https://pmc.ncbi.nlm.nih.gov/articles/PMC11578886/)
- [Source 3](file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md)

## P4

**Title:** GPU molecular dynamics for native-interface recovery

**Summary:** Question: can greater trajectory sampling find native interfaces missed through trapping? Protein-association study compared 16 ordinary MD runs with one coupled 16-replica repulsive-scaling exchange simulation per complex; exchange sampled near-native binding arrangements in five of six cases, with 1gcq unresolved after 640 ns per replica (https://onlinelibrary.wiley.com/doi/full/10.1002/jcc.26187). Proposed extension: test additional independent seeds at fixed trajectory length.

**Root link:** Bears on root's added-search pose-recovery question through a flexible molecular simulation alternative outside its rigid-body docking arms (file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md).

**Compute open:** More parallel compute buys independent association seeds/ensemble members: cited association experiment used 16 ordinary trajectories or 16 coupled exchange replicas, with longest trajectories 899 ns ordinary and 845 ns per exchange replica; whether additional independent ensembles resolve failures such as 1gcq or preserve force-field-favored wrong orientations remains unknown (https://onlinelibrary.wiley.com/doi/full/10.1002/jcc.26187).

**Sequential:** Each integration update waits for preceding positions/velocities and resulting forces; proposed 2-fs steps imply roughly 154–450 million updates for reported 308–899-ns ordinary runs, with benchmark using 16 independent ordinary runs or one coupled 16-replica exchange run per pair, not establishing a sufficient run count for convergence; GPU engine was pmemd.cuda, but per-run GPU busy fraction and original integration timestep are unreported in cited main text (https://onlinelibrary.wiley.com/doi/full/10.1002/jcc.26187). Updates are ordered in ordinary integration; parallel-in-time coarse prediction plus concurrent fine corrections could overlap trajectory segments if a cheap accurate coarse force field preserves relevant dynamics and converges cheaply—nearest cited physical demonstration used adaptive Parareal on tungsten defects, not protein association (https://arxiv.org/abs/2212.10508).

**Narrowing:** Leaves fixed MEGADOCK scoring, numerical agreement and exact DockQ endpoints aside; near-native interface recovery is a geometric proxy for root's pose recovery, requiring separate validation on its four cases (file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md; https://onlinelibrary.wiley.com/doi/full/10.1002/jcc.26187).

**Sources:**

- [Source 1](https://onlinelibrary.wiley.com/doi/full/10.1002/jcc.26187)
- [Source 2](https://arxiv.org/abs/2212.10508)
- [Source 3](file:///home/hal/dev/interp/metis/experiments/blind-02/20261103-0124-tree/out/work/seed-20261103/R1/framer.md)

