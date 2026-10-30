Can increased parallelism in protein–protein docking improve the recovery of experimentally observed binding poses, particularly for AAV capsid–receptor interactions? We want to investigate whether additional parallel computation improves scientific results, rather than simply accelerating an existing search.

Use PINDER-S as the primary benchmark: https://github.com/pinder-org/pinder

It contains 250 protein–protein test complexes, including 93 with paired unbound structures. Prioritise those 93 cases for realistic docking evaluation. Use the published AAV–AAVR structures 6IHB, 6JCQ and 6JCS as a separate, biologically motivated challenge.

These represent AAV2–PKD2, AAV1–PKD2 and AAV5–PKD1 interactions. The AAV challenge should initially evaluate redocking from separated components. Do not treat these as independently determined unbound structures.

Investigate the following questions:
- Can existing docking methods recover known protein–protein interfaces from the benchmark inputs?
- What limits the number of independent candidate poses that can be evaluated or searched concurrently?
- Could restructuring the search exploit massively parallel GPU hardware rather than merely distributing independent runs?
- Does additional search improve the probability of recovering experimentally observed interfaces within a fixed time or compute budget?

Evaluate scientific correctness using DockQ, interface RMSD and native-contact recovery. DockQ ≥ 0.23 defines an acceptable-quality prediction under the standard benchmark convention. Compare the top-ranked predicted pose and the best pose among a fixed number of generated candidates. Do not conflate search coverage with ranking quality.

Compare wall-clock time, cost, search throughput and time to an acceptable pose against an optimised existing implementation.

Use independent random seeds and a fixed, preregistered selection of benchmark cases.

Begin with small calibration experiments to establish scientific validity, input sizes and actual performance.

Use those measurements to formulate a larger experimental proposal within a $1,000 compute budget.

Do not infer BBB transcytosis, binding affinity or therapeutic relevance from docking accuracy alone.

Explicitly report when the benchmarks or available structures cannot support a scientific conclusion.
