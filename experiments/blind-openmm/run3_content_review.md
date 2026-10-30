# blind-openmm run3: content review (after the sealed blind diagnosis, d65f3a8)

## What intake did
- Two search calls, two candidates. It selected a different study from runs 1 and 2: NVIDIA's technical blog "Maximizing OpenMM Molecular Dynamics Throughput with NVIDIA Multi-Process Service" (2025-06-04). The workload is OpenMM's `examples/benchmark.py`, DHFR explicit-solvent PME, with two independent simulations running concurrently on one GPU at `--seconds=60` each. The score is aggregate ns/day.
- This matches the hint better than the energy-drift study did: a throughput benchmark of independent simulations on one GPU, with distinct seeds coming from OpenMM's default per-Context seeding.
- Pinned to OpenMM 8.2.0 at commit 5377094 (`commit` and `pin` both present). The files are complete under the check: U39 worked.
- Budgets: none supplied, so defaults apply. Run2's 7-day budgets belonged to the drift study.
- Anchors: one reference, the DHFR atom count (23,558). The agent did not record the blog's published per-GPU throughputs, judging them hardware-dependent.

## Cause of the FAIL
`licence` "unknown". The agent established MIT (API, Reference and CPU platforms) and LGPL (CUDA platform) for the software from `docs-source/licenses/Licenses.txt`. It then found no file-specific grant for the required inputs: the example PDB (`examples/5dfr_solv-cube_equil.pdb`) and two bundled force-field XMLs. Its reason: "Public availability does not establish a distinct licence grant for benchmark PDB and all benchmark materials."

The reading is defensible. Licences.txt says "several licenses which cover different parts of OpenMM" and lists the API and the platforms; it never names the examples or the bundled data.

The fact is not stable on the same evidence, though:
- Run16 (positive control), on the same repository's `benchmark.py` inputs, recorded `licence` "permitted".
- Run2 recorded "permitted" for a paper's supplementary archive with no software licence of its own.

## Blind hypotheses scored
- H1 0.45, a different study whose inputs carry no licence statement the agent could cite: **true**.
- H2 0.3, the same drift study judged unlicensed: false.
- H3 0.15, licence evidence unreachable: false. The licence files were fetched and quoted.
- H4 0.1: false.

## What this says about the licence gate
The gate thresholds a judgement whose criterion the contract leaves open: what counts as "intended use allowed" for inputs bundled in a project whose licence does not name them. Three intake agents applied three standards. Under the stopping principle, the measurement has to be fixed before the gate is trusted.

Two parts, and only the first is mine to write:
1. **Measurement (no policy change).** Intake records a closed licence-basis fact for the required inputs, as an enum a blind operator may read: covered by a file's own licence, by a licence for the repository or archive that distributes them, by terms of use, or by an owner statement; or none found, or the source unreachable. This makes "unknown" diagnosable without reading content, which blind-01 needs too.
2. **Policy (owner).** Does a project licence count as permission for the example inputs that the project itself distributes, when the intended use is local execution with no redistribution? A yes is ordinary open-source practice and would have passed this run. A no keeps such runs blocked, as now.

## Bearing on blind-01
Blind-01 run1's `licence` "unknown" may be this same strict reading rather than an absent or restrictive licence. Its H1 (0.5) should fall, and H3 (a conservative reading, 0.2) should rise. The licence-basis fact would separate them blind.
