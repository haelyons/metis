# blind-openmm run4: content review (after the sealed blind diagnosis, e10599c)

## What intake did
- Two search calls, one candidate. It selected OpenMM's own `examples/benchmark.py` DHFR explicit-solvent PME test, pinned to OpenMM 8.0.0 at commit a780005. It cited the OpenMM 7 paper and a Salad blog benchmark as context, not the NVIDIA MPS study that run3 chose. Blind H2 (0.3) was true; H1 (0.6) was false.
- One reference: the DHFR atom count, 23,558. Default budgets.
- Files complete; intake PASS.

## The licence judgement against run3
The required input is byte-identical in both runs: `examples/5dfr_solv-cube_equil.pdb`, sha256 fc975976…2fdf. Both agents found the same evidence: MIT and LGPL component licences in `docs-source/licenses/Licenses.txt`, and no statement that names the PDB or grants a licence to the whole repository.
- Run3: basis distribution, `licence` "unknown". "Public availability does not establish a distinct licence grant."
- Run4: basis distribution, `licence` "permitted". "Distributed in OpenMM repository; component licences permit scientific use."

With the same evidence and the same basis, the verdicts are opposite. U40 makes the split visible: the disagreement lies entirely in whether a distribution-basis licence permits the intended use. That is the policy question already put to the owner. Until it is answered in the contract, intake's licence verdict on a distribution basis is a coin flip, not a measurement. The record so far on this basis is 3 permitted (run2 judged a paper archive, run4, and run16, before U40) against 1 unknown (run3).

## The box failure
Lambda allocated an H100 PCIe in us-west-3 that never received an IP. The launcher terminated it and exited 1, and the chain ran the pipeline anyway. Reproduce then failed in 15 s as infra (exit 2), which is the correct classification. The fix belongs in the chain: retry the launch a bounded number of times, and do not start the pipeline without a box.
