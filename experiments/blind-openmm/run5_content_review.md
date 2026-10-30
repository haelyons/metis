# blind-openmm run5: content review (after the sealed blind diagnosis, 6618adf)

## What intake chose
- The energy-drift study: Table 5 of the OpenMM 7 paper (PLOS Comput Biol 2017, doi 10.1371/journal.pcbi.1005659), `SI/Benchmarks/energyBenchmarks.py` from the supplementary archive (pinned by sha256), on DHFR in explicit solvent, 23,558 atoms. The licence evidence is CC BY 4.0 for the supplement; the basis is "distribution" for the least-covered item. Intake judged it "permitted".
- Three references, no anchors: mean total-energy drift over ten 1 ns trials in single (1.557 kJ/mol/ps), mixed (-0.0047) and double precision.
- Baseline: `pip install openmm[cuda12]` (OpenMM 8.6.1), not the 7.x the paper used. My sealed concern about an OpenMM 7.0.1 source build did not apply; setup took 29 s.
- Workload as published, one fixed scale: 30 sequential trials (10 per precision) of 500,000 steps at 2 fs, sampling energy every 1 ps. 15 million steps in one invocation, including 10 ns in double precision.
- `stage_budgets_s`: 604800 s for anchors, profile, method_run, tests and evaluate, described by intake as "conservative administrative caps ... including historically slow double precision". There was no `setup` key, so setup resolved to the 1200 s default. That answers the diagnosis's open question: my mid-run recollection that every key was 604800 was wrong for setup.

## Why the anchors run took over 5.7 h
H1 (0.55) holds: the run was the full published workload, on an A10. An A10 does double-precision arithmetic at a small fraction of its single-precision rate. 10 ns of DHFR in double precision is many hours on that card, after 20 ns in single and mixed. The published script runs all three precisions in one invocation, so H2's mechanism (several long parts in sequence) is part of the workload itself, not a harness choice. There is no sign of H3: GPU at 100%, and the harness parses output only after the workload exits. No partial output survives. The chain killed the pipeline and tore down the box before anything was fetched, so how far it got is unknown.

## What this means
- **This study does not fit the pipeline at its published scale on this box.** No runtime is published. The performance metric is optional ("full fixed-workload wall time"). The smallest sealed protocol needs at least 10 more invocations of the same 15-million-step workload. At over 5.7 h per invocation, evaluate alone is days.
- **Intake did what the contract asks:** one fixed scale, no scale search, budgets stated as caps rather than claims. The contract gives it no way to know the runtime before running. This is the "unknown runtime" case the owner named, and the right response is a bounded calibration whose measured lower bound decides fit.
- **The half-time-left cap in U42b would not have helped.** It would have allowed about 5.9 h, then timed out, at the same cost as the chain cut. Bounding the first workload run by ceiling divided by the smallest protocol's invocation count stops it at about 1 h with a measured lower bound and a `compute_cap` record. This is the same lower-bound rule as the smoke, applied at the first measurement.
- **Open for the owner:** the reproduction alone (drift on OpenMM 8.6.1 against the paper's three values) is an interpretable result even when the speedup protocol cannot fit. Finishing it here would have taken roughly 10 h or more on an A10.
- **Evidence loss on a cut:** an outer timeout loses the partial workload output and every stage record. The pipeline's own limits must fire first so boxrun fetches what exists.
