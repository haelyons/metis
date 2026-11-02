# Questions and answers

## Q1. What question did the brief or card ask, in its own words, and what would count as an answer?

The source card asks, “Does feeding many GPUs to the block-tridiagonal Newton solve shorten its depth from T ordered steps to log2(T)?” (evidence/_source/reply.txt). This run narrows that question to scalar tridiagonal solves on a single graphics processor, comparing Thomas elimination with parallel cyclic reduction (evidence/QUESTION.md). Its declared answer requires at least twofold median speedup at 16,777,216 equations, greater speedup than at the smallest size, and positive logarithmic regression slope (evidence/QUESTION.md). Correctness checks must pass before that decision can be read (evidence/QUESTION.md).

Sources: (evidence/_source/reply.txt), (evidence/QUESTION.md).

Checked: 4 sentences supported, 0 contradicted, 0 not addressed.

## Q2. What exactly ran: which system or problem, at what sizes, on what hardware and software, with how many repeats?

Measured implementations comprised hand-written Thomas and parallel cyclic reduction, batched Thomas, NVIDIA cuSPARSE, and the processor library's tridiagonal solver (evidence/run_m2.py). Sizes were 1,024, 16,384, 262,144, 4,194,304, and 16,777,216 equations, with five seeded systems per implementation and size (evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json). Hardware was one NVIDIA A100 SXM4 graphics processor with 40 gigabytes; processor-library threading was restricted to one thread (evidence/results_m2/out/env.json). Recorded software included CUDA 12.8, Python 3.10.12, NumPy 1.26.4, SciPy 1.8.0, and OpenBLAS 0.3.20 (evidence/results_m2/out/env.json). Each system received two warmups followed by a timed block of repeated solves (evidence/run_m2.py).

Sources: (evidence/run_m2.py), (evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json), (evidence/results_m2/out/env.json).

Checked: 5 sentences supported, 0 contradicted, 0 not addressed.

## Q3. What was the baseline, who would use it in practice, and is it the one an expert would pick?

The headline baseline was hand-written Thomas elimination using a single graphics-processor thread per system; its source specifies no unrolling or variant search (evidence/run_m2.py). The intended application was Newton correction inside parallel-in-time calculations; the card identifies no actual user population (evidence/_source/reply.txt). The run's question document explicitly challenges this baseline's practical relevance and names processor-library Thomas as the practical sequential alternative (evidence/QUESTION.md). Expert preference was not established; the historical 28-fold comparison used a processor-library baseline on different hardware and remained an unreproduced proxy (evidence/_source/reply.txt).

Sources: (evidence/run_m2.py), (evidence/_source/reply.txt), (evidence/QUESTION.md).

Checked: 4 sentences supported, 0 contradicted, 0 not addressed.

## Q4. What number answers the question, what is its spread across repeats, and under which rule does it count?

At 16,777,216 equations, median Thomas and parallel cyclic reduction times were 7,598.50 and 21.8156 milliseconds, yielding 348.305-fold speedup (evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json). Paired-seed speedup ratios had interquartile width 1.089 and lower quartile 348.289 (evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json). The declared rule passed: speedup exceeded twofold, exceeded smallest-size speedup, and had positive logarithmic regression slope, 0.25565 (evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json). Speedup nevertheless decreased across the largest sizes, so the recorded result does not establish monotonic growth (evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json). These repeats varied generated systems on the same machine, rather than measuring variation across machines (evidence/results_m2/out/m2_summary.json).

Sources: (evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json), (evidence/results_m2/out/m2_summary.json).

Checked: 5 sentences supported, 0 contradicted, 0 not addressed.

## Q5. How was correctness checked, against which reference, at what tolerance?

At 1,024 and 16,384 equations, seed zero, both hand-written solvers were compared with cuSPARSE and SciPy's banded solver (evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json). Required relative equation residual was at most 1e-10; solution differences against each reference had to remain below 1e-8 (evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json). The harness divides equation-error norm by right-hand-side norm, and solution-difference norm by reference-solution norm (evidence/run_m2.py). Maximum hand-written residual was 3.111e-16; all solution comparisons and reference-to-reference comparisons passed their tolerances (evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json). Residual instrumentation also passed checks using a known exact solution and a deliberately perturbed solution (evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json) (evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json).

Sources: (evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json), (evidence/run_m2.py), (evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json), (evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json).

Checked: 4 sentences supported, 0 contradicted, 1 not addressed.

Not addressed: The harness divides equation-error norm by right-hand-side norm, and solution-difference norm by reference-solution norm (evidence/run_m2.py).

Quote: none; the cited file (evidence/run_m2.py) does not bear on it.

## Q6. What was sealed before measuring, which sealed predictions held, which failed, and by how much?

Forecasts were sealed before agents or rented hardware ran (evidence/SEALED_PREDICTIONS.md). Ten forecast events occurred: compilation, correctness, smaller residuals, favorable decision, minimum speedup, earliest crossover, processor comparison, scaling, short duration, and completion (evidence/out/PREDICTIONS_SCORED.md). Two forecast events did not occur (evidence/out/PREDICTIONS_SCORED.md). At 16,777,216 equations, parallel cyclic reduction's 19.103-fold processor-library speedup exceeded the below-twofold forecast ceiling by 17.103, computed by subtraction (evidence/SEALED_PREDICTIONS.md) (evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json). At that size, its time was 7.412 times cuSPARSE's, exceeding the forecast ceiling of three by 4.412, computed by subtraction (evidence/SEALED_PREDICTIONS.md) (evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json).

Sources: (evidence/SEALED_PREDICTIONS.md), (evidence/out/PREDICTIONS_SCORED.md), (evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json), (evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json).

Checked: 3 sentences supported, 0 contradicted, 2 not addressed.

Not addressed: At 16,777,216 equations, parallel cyclic reduction's 19.103-fold processor-library speedup exceeded the below-twofold forecast ceiling by 17.103, computed by subtraction (evidence/SEALED_PREDICTIONS.md) (evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json).

Quote: none; the cited file (evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json) does not bear on it.

Not addressed: At that size, its time was 7.412 times cuSPARSE's, exceeding the forecast ceiling of three by 4.412, computed by subtraction (evidence/SEALED_PREDICTIONS.md) (evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json).

Quote: none; the cited file (evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json) does not bear on it.

## Q7. What was voided, skipped or not run, and does any of it change the answer?

The summary records no voids, missing records, or failed scheduled measurement stages (evidence/results_m2/out/m2_summary.json). Optional block-system and multiple-graphics-processor phases were omitted, while isolated document-reader agents failed to run (evidence/RUN.md). Counting saved rows gives 15 of 25 parallel cyclic reduction timing blocks below the intended 50 milliseconds; none occurred at the largest size (evidence/results_m2/out/rows/pcr_gpu.jsonl). Those short blocks depart from the timing plan, although the measurement summary retains its valid verdict (evidence/QUESTION.md) (evidence/results_m2/out/m2_summary.json). The omissions leave the declared scalar comparison answerable, while the card's broader block-system and multiple-device question remains untested (evidence/QUESTION.md).

Sources: (evidence/results_m2/out/m2_summary.json), (evidence/RUN.md), (evidence/results_m2/out/rows/pcr_gpu.jsonl), (evidence/QUESTION.md).

Checked: 4 sentences supported, 0 contradicted, 1 not addressed.

Not addressed: Counting saved rows gives 15 of 25 parallel cyclic reduction timing blocks below the intended 50 milliseconds; none occurred at the largest size (evidence/results_m2/out/rows/pcr_gpu.jsonl).

Quote: none; the cited file (evidence/results_m2/out/rows/pcr_gpu.jsonl) does not bear on it.

## Q8. How far does the answer reach: which sizes, hardware and inputs it covers, and where it stops?

Coverage is restricted to the specified sizes on a single A100 machine, using five generated systems per size and a single right-hand side (evidence/QUESTION.md). Inputs used diagonal entries of three, random unit-magnitude off-diagonals, standard-normal right-hand sides, and 64-bit floating-point arithmetic (evidence/QUESTION.md). Graphics-processor input transfers, allocation, and required input copies occur outside timed solver blocks, so these timings describe data already on device (evidence/run_m2.py). The design excludes ill-conditioned matrices, other precisions, multiple right-hand sides, block systems, multiple graphics processors, and the surrounding Newton iteration (evidence/QUESTION.md). It therefore establishes neither performance on those populations nor application-level acceleration (evidence/QUESTION.md).

Sources: (evidence/QUESTION.md), (evidence/run_m2.py).

Checked: 5 sentences supported, 0 contradicted, 0 not addressed.

## Q9. What did the run cost, how long did it take, and what would it take to run again?

The operator log reports rental cost of $0.48 for 0.239 hours; it provides no total model or human cost (evidence/RUN.md). The measurement record gives 0.119105 hours from the first reference-check solve to the last sweep row (evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json). From 08:55 directory creation to 10:16 postprocessing completion, the logged workflow spanned 81 minutes, computed by subtraction (evidence/RUN.md). Repetition requires the saved runner, provenance helper, batch script, compatible installed software, and configured price, budget, and timeout variables (evidence/onbox_m2.sh). The recorded software and graphics-processor configuration provide the environment to reproduce (evidence/results_m2/out/env.json).

Sources: (evidence/RUN.md), (evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json), (evidence/onbox_m2.sh), (evidence/results_m2/out/env.json).

Checked: 4 sentences supported, 0 contradicted, 1 not addressed.

Not addressed: From 08:55 directory creation to 10:16 postprocessing completion, the logged workflow spanned 81 minutes, computed by subtraction (evidence/RUN.md).

Quote: none; the cited file (evidence/RUN.md) does not bear on it.

## Q10. What does the result let a scientist do that they could not before, and what is the next measurement?

At 16,777,216 equations, cuSPARSE took 2.943 milliseconds versus 21.816 for hand-written parallel cyclic reduction (evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json). This supplies a measured implementation comparison for the tested input family, supporting solver selection within that scope (evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json). It does not establish acceleration of the surrounding scientific calculation, which was outside the design (evidence/QUESTION.md). The run write-up proposes comparing data-resident solves with solves that include transfers to the graphics processor (evidence/TAKEAWAYS_m2.md). That next measurement would address transfer costs excluded by the current timing harness (evidence/run_m2.py).

Sources: (evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json), (evidence/QUESTION.md), (evidence/TAKEAWAYS_m2.md), (evidence/run_m2.py).

Checked: 5 sentences supported, 0 contradicted, 0 not addressed.
