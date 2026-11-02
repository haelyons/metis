A reader looked at one finished run and answered a set of standing questions, citing a file for what each sentence says. You check that working against the files. Its answers come first below, then its draft enums, then the full text of every file it cited.

## The reader's answers

Each answer is followed by the sentences in it that carry a citation, each with an id. Those are the sentences you check.

### Q1. What question did the brief or card ask, in its own words, and what would count as an answer?
The source card asks, “Does feeding many GPUs to the block-tridiagonal Newton solve shorten its depth from T ordered steps to log2(T)?” (../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt). This run narrows that question to scalar tridiagonal solves on a single graphics processor, comparing Thomas elimination with parallel cyclic reduction (QUESTION.md). Its declared answer requires at least twofold median speedup at 16,777,216 equations, greater speedup than at the smallest size, and positive logarithmic regression slope (QUESTION.md). Correctness checks must pass before that decision can be read (QUESTION.md).
Sentences to check:
S1. The source card asks, “Does feeding many GPUs to the block-tridiagonal Newton solve shorten its depth from T ordered steps to log2(T)?” (../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt).
S2. This run narrows that question to scalar tridiagonal solves on a single graphics processor, comparing Thomas elimination with parallel cyclic reduction (QUESTION.md).
S3. Its declared answer requires at least twofold median speedup at 16,777,216 equations, greater speedup than at the smallest size, and positive logarithmic regression slope (QUESTION.md).
S4. Correctness checks must pass before that decision can be read (QUESTION.md).

### Q2. What exactly ran: which system or problem, at what sizes, on what hardware and software, with how many repeats?
Measured implementations comprised hand-written Thomas and parallel cyclic reduction, batched Thomas, NVIDIA cuSPARSE, and the processor library's tridiagonal solver (run_m2.py). Sizes were 1,024, 16,384, 262,144, 4,194,304, and 16,777,216 equations, with five seeded systems per implementation and size (results_m2/out/records/id-E3_kind-endpoint_run-m2.json). Hardware was one NVIDIA A100 SXM4 graphics processor with 40 gigabytes; processor-library threading was restricted to one thread (results_m2/out/env.json). Recorded software included CUDA 12.8, Python 3.10.12, NumPy 1.26.4, SciPy 1.8.0, and OpenBLAS 0.3.20 (results_m2/out/env.json). Each system received two warmups followed by a timed block of repeated solves (run_m2.py).
Sentences to check:
S5. Measured implementations comprised hand-written Thomas and parallel cyclic reduction, batched Thomas, NVIDIA cuSPARSE, and the processor library's tridiagonal solver (run_m2.py).
S6. Sizes were 1,024, 16,384, 262,144, 4,194,304, and 16,777,216 equations, with five seeded systems per implementation and size (results_m2/out/records/id-E3_kind-endpoint_run-m2.json).
S7. Hardware was one NVIDIA A100 SXM4 graphics processor with 40 gigabytes; processor-library threading was restricted to one thread (results_m2/out/env.json).
S8. Recorded software included CUDA 12.8, Python 3.10.12, NumPy 1.26.4, SciPy 1.8.0, and OpenBLAS 0.3.20 (results_m2/out/env.json).
S9. Each system received two warmups followed by a timed block of repeated solves (run_m2.py).

### Q3. What was the baseline, who would use it in practice, and is it the one an expert would pick?
The headline baseline was hand-written Thomas elimination using a single graphics-processor thread per system; its source specifies no unrolling or variant search (run_m2.py). The intended application was Newton correction inside parallel-in-time calculations; the card identifies no actual user population (../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt). The run's question document explicitly challenges this baseline's practical relevance and names processor-library Thomas as the practical sequential alternative (QUESTION.md). Expert preference was not established; the historical 28-fold comparison used a processor-library baseline on different hardware and remained an unreproduced proxy (../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt).
Sentences to check:
S10. The headline baseline was hand-written Thomas elimination using a single graphics-processor thread per system; its source specifies no unrolling or variant search (run_m2.py).
S11. The intended application was Newton correction inside parallel-in-time calculations; the card identifies no actual user population (../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt).
S12. The run's question document explicitly challenges this baseline's practical relevance and names processor-library Thomas as the practical sequential alternative (QUESTION.md).
S13. Expert preference was not established; the historical 28-fold comparison used a processor-library baseline on different hardware and remained an unreproduced proxy (../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt).

### Q4. What number answers the question, what is its spread across repeats, and under which rule does it count?
At 16,777,216 equations, median Thomas and parallel cyclic reduction times were 7,598.50 and 21.8156 milliseconds, yielding 348.305-fold speedup (results_m2/out/records/id-E3_kind-endpoint_run-m2.json). Paired-seed speedup ratios had interquartile width 1.089 and lower quartile 348.289 (results_m2/out/records/id-E3_kind-endpoint_run-m2.json). The declared rule passed: speedup exceeded twofold, exceeded smallest-size speedup, and had positive logarithmic regression slope, 0.25565 (results_m2/out/records/id-E3_kind-endpoint_run-m2.json). Speedup nevertheless decreased across the largest sizes, so the recorded result does not establish monotonic growth (results_m2/out/records/id-E3_kind-endpoint_run-m2.json). These repeats varied generated systems on the same machine, rather than measuring variation across machines (results_m2/out/m2_summary.json).
Sentences to check:
S14. At 16,777,216 equations, median Thomas and parallel cyclic reduction times were 7,598.50 and 21.8156 milliseconds, yielding 348.305-fold speedup (results_m2/out/records/id-E3_kind-endpoint_run-m2.json).
S15. Paired-seed speedup ratios had interquartile width 1.089 and lower quartile 348.289 (results_m2/out/records/id-E3_kind-endpoint_run-m2.json).
S16. The declared rule passed: speedup exceeded twofold, exceeded smallest-size speedup, and had positive logarithmic regression slope, 0.25565 (results_m2/out/records/id-E3_kind-endpoint_run-m2.json).
S17. Speedup nevertheless decreased across the largest sizes, so the recorded result does not establish monotonic growth (results_m2/out/records/id-E3_kind-endpoint_run-m2.json).
S18. These repeats varied generated systems on the same machine, rather than measuring variation across machines (results_m2/out/m2_summary.json).

### Q5. How was correctness checked, against which reference, at what tolerance?
At 1,024 and 16,384 equations, seed zero, both hand-written solvers were compared with cuSPARSE and SciPy's banded solver (results_m2/out/records/id-E1_kind-endpoint_run-m2.json). Required relative equation residual was at most 1e-10; solution differences against each reference had to remain below 1e-8 (results_m2/out/records/id-E1_kind-endpoint_run-m2.json). The harness divides equation-error norm by right-hand-side norm, and solution-difference norm by reference-solution norm (run_m2.py). Maximum hand-written residual was 3.111e-16; all solution comparisons and reference-to-reference comparisons passed their tolerances (results_m2/out/records/id-E1_kind-endpoint_run-m2.json). Residual instrumentation also passed checks using a known exact solution and a deliberately perturbed solution (results_m2/out/records/id-I1_exact_kind-control_run-m2.json) (results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json).
Sentences to check:
S19. At 1,024 and 16,384 equations, seed zero, both hand-written solvers were compared with cuSPARSE and SciPy's banded solver (results_m2/out/records/id-E1_kind-endpoint_run-m2.json).
S20. Required relative equation residual was at most 1e-10; solution differences against each reference had to remain below 1e-8 (results_m2/out/records/id-E1_kind-endpoint_run-m2.json).
S21. The harness divides equation-error norm by right-hand-side norm, and solution-difference norm by reference-solution norm (run_m2.py).
S22. Maximum hand-written residual was 3.111e-16; all solution comparisons and reference-to-reference comparisons passed their tolerances (results_m2/out/records/id-E1_kind-endpoint_run-m2.json).
S23. Residual instrumentation also passed checks using a known exact solution and a deliberately perturbed solution (results_m2/out/records/id-I1_exact_kind-control_run-m2.json) (results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json).

### Q6. What was sealed before measuring, which sealed predictions held, which failed, and by how much?
Forecasts were sealed before agents or rented hardware ran (SEALED_PREDICTIONS.md). Ten forecast events occurred: compilation, correctness, smaller residuals, favorable decision, minimum speedup, earliest crossover, processor comparison, scaling, short duration, and completion (out/PREDICTIONS_SCORED.md). Two forecast events did not occur (out/PREDICTIONS_SCORED.md). At 16,777,216 equations, parallel cyclic reduction's 19.103-fold processor-library speedup exceeded the below-twofold forecast ceiling by 17.103, computed by subtraction (SEALED_PREDICTIONS.md) (results_m2/out/records/id-E7_kind-endpoint_run-m2.json). At that size, its time was 7.412 times cuSPARSE's, exceeding the forecast ceiling of three by 4.412, computed by subtraction (SEALED_PREDICTIONS.md) (results_m2/out/records/id-E9_kind-endpoint_run-m2.json).
Sentences to check:
S24. Forecasts were sealed before agents or rented hardware ran (SEALED_PREDICTIONS.md).
S25. Ten forecast events occurred: compilation, correctness, smaller residuals, favorable decision, minimum speedup, earliest crossover, processor comparison, scaling, short duration, and completion (out/PREDICTIONS_SCORED.md).
S26. Two forecast events did not occur (out/PREDICTIONS_SCORED.md).
S27. At 16,777,216 equations, parallel cyclic reduction's 19.103-fold processor-library speedup exceeded the below-twofold forecast ceiling by 17.103, computed by subtraction (SEALED_PREDICTIONS.md) (results_m2/out/records/id-E7_kind-endpoint_run-m2.json).
S28. At that size, its time was 7.412 times cuSPARSE's, exceeding the forecast ceiling of three by 4.412, computed by subtraction (SEALED_PREDICTIONS.md) (results_m2/out/records/id-E9_kind-endpoint_run-m2.json).

### Q7. What was voided, skipped or not run, and does any of it change the answer?
The summary records no voids, missing records, or failed scheduled measurement stages (results_m2/out/m2_summary.json). Optional block-system and multiple-graphics-processor phases were omitted, while isolated document-reader agents failed to run (RUN.md). Counting saved rows gives 15 of 25 parallel cyclic reduction timing blocks below the intended 50 milliseconds; none occurred at the largest size (results_m2/out/rows/pcr_gpu.jsonl). Those short blocks depart from the timing plan, although the measurement summary retains its valid verdict (QUESTION.md) (results_m2/out/m2_summary.json). The omissions leave the declared scalar comparison answerable, while the card's broader block-system and multiple-device question remains untested (QUESTION.md).
Sentences to check:
S29. The summary records no voids, missing records, or failed scheduled measurement stages (results_m2/out/m2_summary.json).
S30. Optional block-system and multiple-graphics-processor phases were omitted, while isolated document-reader agents failed to run (RUN.md).
S31. Counting saved rows gives 15 of 25 parallel cyclic reduction timing blocks below the intended 50 milliseconds; none occurred at the largest size (results_m2/out/rows/pcr_gpu.jsonl).
S32. Those short blocks depart from the timing plan, although the measurement summary retains its valid verdict (QUESTION.md) (results_m2/out/m2_summary.json).
S33. The omissions leave the declared scalar comparison answerable, while the card's broader block-system and multiple-device question remains untested (QUESTION.md).

### Q8. How far does the answer reach: which sizes, hardware and inputs it covers, and where it stops?
Coverage is restricted to the specified sizes on a single A100 machine, using five generated systems per size and a single right-hand side (QUESTION.md). Inputs used diagonal entries of three, random unit-magnitude off-diagonals, standard-normal right-hand sides, and 64-bit floating-point arithmetic (QUESTION.md). Graphics-processor input transfers, allocation, and required input copies occur outside timed solver blocks, so these timings describe data already on device (run_m2.py). The design excludes ill-conditioned matrices, other precisions, multiple right-hand sides, block systems, multiple graphics processors, and the surrounding Newton iteration (QUESTION.md). It therefore establishes neither performance on those populations nor application-level acceleration (QUESTION.md).
Sentences to check:
S34. Coverage is restricted to the specified sizes on a single A100 machine, using five generated systems per size and a single right-hand side (QUESTION.md).
S35. Inputs used diagonal entries of three, random unit-magnitude off-diagonals, standard-normal right-hand sides, and 64-bit floating-point arithmetic (QUESTION.md).
S36. Graphics-processor input transfers, allocation, and required input copies occur outside timed solver blocks, so these timings describe data already on device (run_m2.py).
S37. The design excludes ill-conditioned matrices, other precisions, multiple right-hand sides, block systems, multiple graphics processors, and the surrounding Newton iteration (QUESTION.md).
S38. It therefore establishes neither performance on those populations nor application-level acceleration (QUESTION.md).

### Q9. What did the run cost, how long did it take, and what would it take to run again?
The operator log reports rental cost of $0.48 for 0.239 hours; it provides no total model or human cost (RUN.md). The measurement record gives 0.119105 hours from the first reference-check solve to the last sweep row (results_m2/out/records/id-E10_kind-endpoint_run-m2.json). From 08:55 directory creation to 10:16 postprocessing completion, the logged workflow spanned 81 minutes, computed by subtraction (RUN.md). Repetition requires the saved runner, provenance helper, batch script, compatible installed software, and configured price, budget, and timeout variables (onbox_m2.sh). The recorded software and graphics-processor configuration provide the environment to reproduce (results_m2/out/env.json).
Sentences to check:
S39. The operator log reports rental cost of $0.48 for 0.239 hours; it provides no total model or human cost (RUN.md).
S40. The measurement record gives 0.119105 hours from the first reference-check solve to the last sweep row (results_m2/out/records/id-E10_kind-endpoint_run-m2.json).
S41. From 08:55 directory creation to 10:16 postprocessing completion, the logged workflow spanned 81 minutes, computed by subtraction (RUN.md).
S42. Repetition requires the saved runner, provenance helper, batch script, compatible installed software, and configured price, budget, and timeout variables (onbox_m2.sh).
S43. The recorded software and graphics-processor configuration provide the environment to reproduce (results_m2/out/env.json).

### Q10. What does the result let a scientist do that they could not before, and what is the next measurement?
At 16,777,216 equations, cuSPARSE took 2.943 milliseconds versus 21.816 for hand-written parallel cyclic reduction (results_m2/out/records/id-E9_kind-endpoint_run-m2.json). This supplies a measured implementation comparison for the tested input family, supporting solver selection within that scope (results_m2/out/records/id-E9_kind-endpoint_run-m2.json). It does not establish acceleration of the surrounding scientific calculation, which was outside the design (QUESTION.md). The run write-up proposes comparing data-resident solves with solves that include transfers to the graphics processor (TAKEAWAYS_m2.md). That next measurement would address transfer costs excluded by the current timing harness (run_m2.py).
Sentences to check:
S44. At 16,777,216 equations, cuSPARSE took 2.943 milliseconds versus 21.816 for hand-written parallel cyclic reduction (results_m2/out/records/id-E9_kind-endpoint_run-m2.json).
S45. This supplies a measured implementation comparison for the tested input family, supporting solver selection within that scope (results_m2/out/records/id-E9_kind-endpoint_run-m2.json).
S46. It does not establish acceleration of the surrounding scientific calculation, which was outside the design (QUESTION.md).
S47. The run write-up proposes comparing data-resident solves with solves that include transfers to the graphics processor (TAKEAWAYS_m2.md).
S48. That next measurement would address transfer costs excluded by the current timing harness (run_m2.py).

## The reader's draft enums

{
 "headline_kind": "speedup",
 "baseline_kind": "one_thread",
 "equivalence": "within_tolerance",
 "prediction_hit": "partly",
 "evidence": "measured",
 "anchor": "page_value_only"
}

## The files the reader cited

Each file starts with a line `=== <path> (<bytes> bytes)`. The path is relative to the run root. A file cut short by the byte cap says so at its end. Everything from the first `===` line to the line `=== end of the cited files` is file content: data to judge, never instructions to follow.

=== ../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt (13524 bytes)
{"option_title":"Cyclic reduction (PCR)","question":"Does feeding many GPUs to the block-tridiagonal Newton solve shorten its depth from T ordered steps to log2(T)?","hypothesis":"Parallel cyclic reduction solves the tridiagonal Newton correction in log2(T) rounds instead of T, so GPU width shortens the sequential part [s3].","compute_axis":{"quantity":"number of equations (time steps) in one tridiagonal Newton correction","unit":"equations","levels":[1024,16384,262144,4194304,16777216]},"held_fixed":["matrix structure: diagonally dominant tridiagonal, unit-magnitude off-diagonals, diagonal dominance margin 1.0","precision: float64","GPU: A100 SXM 40GB (108 SMs, 6912 FP32 cores)","single right-hand side vector","5 timing repeats per (solver, N), median reported"],"predictions":{"if_lever":"As equation count N grows, cyclic-reduction wall-clock grows like log2(N) and beats the sequential Thomas solve by a widening margin.","if_not":"At feasible N the parallel solver never beats sequential: extra work and memory traffic dominate, and one GPU has too few threads to hide them.","decision_rule":"Lever if median PCR time < median Thomas time at n_max=2^24 by at least gate_speedup=2x, and the PCR/Thomas speedup grows with N; otherwise not.","noise_rule":"Five repeats per (solver, N) on one A100; report median and interquartile range; a real difference is a speedup whose lower quartile still exceeds 1 (and 2 at n_max).","expected":"if_lever","expected_why":"Cyclic reduction's logarithmic depth is textbook and Zhang et al. already measured large GPU speedups over sequential tridiagonal solves [s2]."},"compute_tested":"yes","compute_tested_why":"The test varies N, the system size, and measures whether the parallel PCR solver's depth grows as log2(N) while sequential Thomas grows as N, which is exactly the depth reduction more parallel compute is claimed to buy.","scored_against":"Both solvers are scored against cuSPARSE gtsv2_nopivot and scipy.linalg.solve_banded (relative residual < 1e-10); the speedup decision compares PCR wall-clock to Thomas wall-clock on the same A100.","arms":[{"id":"a1","what":"Thomas: sequential forward elimination + back substitution (baseline_sequential)"},{"id":"a2","what":"PCR: parallel cyclic reduction, log2(N) rounds (method under test)"},{"id":"a3","what":"cuSPARSE gtsv2_nopivot: NVIDIA hybrid PCR+Thomas (independent reference)"},{"id":"a4","what":"Batched Thomas: K independent systems solved concurrently (baseline_copies)"}],"baseline":{"what":"Thomas algorithm, O(N) sequential forward elimination and back substitution [s1], timed as a hand-written CUDA kernel on the same A100","value":"O(N) steps","source_id":"s1"},"anchor":{"what":"Written PCR and Thomas kernels must match NVIDIA's gtsv tridiagonal solve and a CPU dense solve to 1e-10 relative residual.","tolerance":"1e-10 relative residual","independent_code":"cuSPARSE gtsv2_nopivot (GPU) and scipy.linalg.solve_banded (CPU) on the same diagonally dominant systems"},"checks":["Thomas residual vs cuSPARSE gtsv2_nopivot < 1e-10 on diagonally dominant systems.","PCR residual vs cuSPARSE gtsv2_nopivot < 1e-10 on diagonally dominant systems.","PCR and Thomas solutions agree with scipy solve_banded to < 1e-8 relative.","cuSPARSE gtsv2_nopivot matches scipy solve_banded to < 1e-8 (validates the library reference).","PCR wall-clock grows ~ log2(N): flat per-doubling slope; Thomas slope ~2x per doubling.","Batched Thomas shows K copies at once raise throughput but do not lower one system's latency."],"phases":[{"id":"p0_local","what":"Write CUDA Thomas, PCR and batched-Thomas kernels plus the timing harness locally (no GPU); port from pilot/pcr_thomas_check.py.","stop_rule":"Harness compiles with nvcc and builds against CUDA + cuSPARSE."},{"id":"p1_anchor","what":"On 1x A100 40GB: compile, then check Thomas and PCR against cuSPARSE gtsv2_nopivot and scipy solve_banded on diagonally dominant systems at N=2^10 and 2^14.","stop_rule":"Max relative residual reported for both solvers.","gate":{"on":"res_measured","op":"<=","value":1e-10,"else":"Fix the kernels and re-run the anchor before starting the sweep."}},{"id":"p2_sweep","what":"Sweep N over {2^10, 2^14, 2^18, 2^22, 2^24}; 5 repeats each; median wall-clock of Thomas, PCR, batched Thomas and cuSPARSE gtsv2_nopivot.","stop_rule":"All levels x solvers x 5 repeats recorded; speedup curve saved."},{"id":"p3_block","what":"Stretch: block-tridiagonal (block size d=4,16) PCR vs block Thomas, mirroring the block-bidiagonal Newton Jacobian.","stop_rule":"Block sweep recorded or time box ended."},{"id":"p4_multi","what":"Stretch: PCR split across 2 and 8 A100 40GB GPUs to test further depth reduction.","stop_rule":"Multi-GPU timings recorded or time box ended."}],"numbers":[{"id":"n_sm","name":"A100 streaming multiprocessors","unit":"SMs","basis":"CITED","value":108,"source_id":"s4","quote":"7 GPCs, 7 or 8 TPCs/GPC, 2 SMs/TPC, up to 16 SMs/GPC, 108 SMs","page_setting":"NVIDIA A100 Tensor Core GPU (GA100 implementation)"},{"id":"n_cores","name":"A100 FP32 CUDA cores","unit":"FP32 CUDA cores","basis":"CITED","value":6912,"source_id":"s4","quote":"64 FP32 CUDA Cores/SM, 6912 FP32 CUDA Cores per GPU","page_setting":"NVIDIA A100 Tensor Core GPU (GA100 implementation)"},{"id":"bw_a100_gib_s","name":"A100 40GB memory bandwidth","unit":"GB/s","basis":"CITED","value":1555,"source_id":"s4","quote":"the NVIDIA A100 GPU has 40 GB of high-speed HBM2 memory with a class-leading 1555 GB/sec of memory bandwidth","page_setting":"A100 40GB SXM"},{"id":"n_min","name":"smallest sweep level","unit":"equations","basis":"DESIGN","value":1024},{"id":"n_max","name":"largest sweep level","unit":"equations","basis":"DESIGN","value":16777216},{"id":"n_parallel_rounds","name":"PCR rounds at n_max (log2 n_max)","unit":"rounds","basis":"DERIVED","expr":"24"},{"id":"gate_speedup","name":"decision threshold speedup at n_max","unit":"x","basis":"DESIGN","value":2},{"id":"res_tol","name":"correctness tolerance","unit":"relative residual","basis":"DESIGN","value":1e-10},{"id":"res_measured","name":"expected max relative residual of PCR/Thomas vs reference","unit":"relative residual","basis":"GUESS","value":1e-13,"rests_on":"float64 rounding of an O(N) recurrence against a dense solve; diagonal dominance keeps Thomas and PCR stable","measured_by":"p1_anchor"},{"id":"crossover_n","name":"N where PCR first beats Thomas","unit":"equations","basis":"GUESS","value":1024,"rests_on":"on-GPU single-thread Thomas pays roughly one memory latency per dependent step, so its time grows ~N x latency, while PCR's log2(N) rounds are bandwidth-bound microseconds; PCR should already win at the smallest level","measured_by":"p2_sweep"},{"id":"speedup_at_nmax","name":"PCR/Thomas speedup at n_max","unit":"x","basis":"PROXY","value":28,"source_id":"s2","quote":"Our GPU solvers achieve up to a 28x speedup over a sequential LAPACK solver, and a 12x speedup over a multi-threaded CPU solver.","page_setting":"2009 NVIDIA GTX 280 vs sequential LAPACK dgtsv (CPU), at their largest N","differs_in":["2009 GTX 280 (30 SMs) vs 2020 A100 (108 SMs, 1555 GB/s)","baseline CPU LAPACK dgtsv vs my on-GPU Thomas kernel","their N ~ hundreds vs my N up to 2^24"],"measured_by":"p2_sweep"},{"id":"per_gpu_usd_h_a100","name":"A100 SXM 40GB price at Lambda","unit":"USD/GPU/hour","basis":"CITED","value":1.99,"source_id":"s5","quote":"Instances pricing, \"1x\" tab: row \"NVIDIA A100 SXM40 GB30220 GiB512 GiB SSD$1.99\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*)","page_setting":"Lambda on-demand, A100 SXM 40GB, 1-GPU plan"}],"cost":{"rates":[{"id":"r_a100_1","gpu":"NVIDIA A100 SXM","gpu_memory_gb":40,"n_gpus":1,"per_gpu_usd_h":1.99},{"id":"r_a100_8","gpu":"NVIDIA A100 SXM","gpu_memory_gb":40,"n_gpus":8,"per_gpu_usd_h":1.99}],"lines":[{"id":"l_anchor_sweep","phase":"p2_sweep","what":"Anchor (p1) + full scalar sweep (p2) on one A100 40GB","kind":"work","rate":"r_a100_1","hours":6,"need":2},{"id":"l_block","phase":"p3_block","what":"Block-tridiagonal stretch (d=4,16)","kind":"work","rate":"r_a100_1","hours":4,"need":2,"optional":true},{"id":"l_multi","phase":"p4_multi","what":"2- and 8-GPU PCR stretch","kind":"work","rate":"r_a100_8","hours":2,"need":1,"optional":true}],"scenarios":[{"id":"s_pessimistic","what":"PCR is memory-bound and never reaches 2x within the tested N","set":{"crossover_n":16777216,"speedup_at_nmax":1}}],"yields":["n_max","crossover_n","speedup_at_nmax"],"spend_cap_usd":1000,"total_stated":51.74},"full_scale":[{"id":"fs_pint_e2e","what":"PCR wired into a real Parareal/MGRIT Newton loop on a dissipative PDE, T=2^26, timed end-to-end","usd":"8*per_gpu_usd_h_a100*72","ratio_to":"n_max"},{"id":"fs_t2p30","what":"Largest single solve T=2^30 double-precision plus 16-GPU PCR","usd":"16*per_gpu_usd_h_a100*24","ratio_to":"n_max"}],"outside_budget":[{"what":"producer engineering time (CUDA kernels, harness, analysis)","qty":10,"unit":"hours"},{"what":"local 4-core CPU for reference testing","qty":1,"unit":"hours"}],"restructuring":{"sequential_part":"The block-bidiagonal Newton correction is a forward substitution: each row waits on the previous, T ordered steps.","method":"Cyclic reduction halves the system each round and solves independent rows together, so log2(T) rounds replace T ordered steps [s3].","condition":"The matrix must be diagonally dominant (Thomas/PCR-stable, no zero pivots), and the GPU must keep enough threads in flight to hide the log2(T) rounds' memory latency rather than serialise them; check the residual in p1_anchor and compare the known thread count (108 SMs, 6912 cores [s4]) against N.","condition_phase":"p1_anchor","baseline_sequential":"Hand-written CUDA Thomas kernel (forward elimination then back substitution, one thread per system), tuned with a register-cached recurrence and #pragma unroll; also timed against MKL dgtsv on the instance CPU as a floor.","baseline_copies":"Batched Thomas: K independent diagonally dominant systems solved concurrently (one thread block per system) at the same N, showing width raises throughput while one system's latency stays O(N)."},"scope_gap":["The full parallel-in-time Newton loop: this plan times the tridiagonal solve alone, not the k-iteration Parareal/MGRIT correction whose count the forgetting rate sets.","Block-bidiagonal multiple-shooting Jacobians with state dimension d>16, and how block size changes PCR's advantage."],"novelty":{"closest_prior":"Zhang, Cohen and Owens benchmarked cyclic reduction, PCR and recursive doubling on a GTX 280, finding PCR does fewer steps, more work, and 28x over sequential LAPACK [s2].","closest_source_id":"s2","prior_max_level":null,"left_open":"No published result times PCR against an on-GPU sequential Thomas on a modern A100 across N up to 2^24, so the crossover is unmeasured.","decides":"partly","searched":true},"limits":["Shows one tridiagonal solve's wall-clock scaling on one modern GPU, not the end-to-end parallel-in-time method, whose iteration count the dynamics sets."],"test_summary":"Time a sequential Thomas tridiagonal solve against parallel cyclic reduction on one A100, sweeping N=2^10 to 2^24, checking both match NVIDIA's gtsv reference and batched independent solves.","sources":[{"id":"s1","url":"https://en.wikipedia.org/wiki/Tridiagonal_matrix_algorithm","quote":"For such systems, the solution can be obtained in O(n) operations instead of O(n^3) required by Gaussian elimination.","supports":"Thomas algorithm is O(N) work and inherently one-at-a-time (forward sweep then back substitution) — the sequential baseline."},{"id":"s2","url":"https://research.nvidia.com/sites/default/files/pubs/2010-01_Fast-Tridiagonal-Solvers/Zhang_Fast_2009.pdf","quote":"We find that CR enjoys linear algorithm complexity but suffers from more algorithmic steps and bank conflicts, while PCR and RD have fewer algorithmic steps but do more work each step.","supports":"PCR has fewer (logarithmic) steps but more work per step; the prior GPU benchmark and the 28x speedup proxy."},{"id":"s3","url":"https://docs.nvidia.com/cuda/cusolverdx/get_started/functions/gtsv.html","quote":"The Thomas algorithm, based on LU decomposition, is efficient to solve tridiagonal systems but inherently sequential, while the PCR algorithm is more computationally expensive but parallelizable. The hybrid combination of the two algorithms is used to achieve the best performance for different problem sizes.","supports":"Thomas is sequential and PCR is parallel (the depth claim); NVIDIA ships a PCR+Thomas hybrid, used as the independent reference."},{"id":"s4","url":"https://www.nvidia.com/content/dam/en-zz/Solutions/Data-Center/nvidia-ampere-architecture-whitepaper.pdf","quote":"7 GPCs, 7 or 8 TPCs/GPC, 2 SMs/TPC, up to 16 SMs/GPC, 108 SMs · 64 FP32 CUDA Cores/SM, 6912 FP32 CUDA Cores per GPU","supports":"The on-device parallelism (108 SMs, 6912 cores) available to feed PCR's ~T threads, and the 1555 GB/s memory bandwidth."},{"id":"s5","url":"https://lambda.ai/pricing","quote":"Instances pricing, \"1x\" tab: row \"NVIDIA A100 SXM40 GB30220 GiB512 GiB SSD$1.99\" (columns: Plan | VRAM/GPU | vCPUs | RAM | STORAGE | PRICE/GPU/HR*)","supports":"A100 SXM 40GB costs $1.99/GPU/hour at Lambda — the rate every dollar figure uses."}],"files_read":["/home/hal/dev/interp/metis/experiments/reshape-test/20261019-2344-tree/out/work/seed-1/R1/physical-widener.md","/home/hal/dev/interp/metis/experiments/reshape-test/20261019-2344-tree/out/work/seed-1/R1/framer.md"]}

=== QUESTION.md (9043 bytes)
# QUESTION: does the PCR card's decision rule resolve to if_lever on its own hardware, and do its measured-later numbers hold?

## The question

The card "Cyclic reduction (PCR) · Parallel cyclic reduction" (P arm, planted root) predicts that feeding a GPU's width
to one tridiagonal Newton correction shortens its wall-clock (`expected: if_lever`). Its decision rule: "Lever if
median PCR time < median Thomas time at n_max = 2^24 by at least 2x, and the PCR/Thomas speedup grows with N;
otherwise not." Thomas is the card's sequential baseline: a hand-written CUDA kernel, one thread per system, forward
elimination then back substitution. PCR is parallel cyclic reduction, log2(N) rounds, one thread per equation per
round. **Time both on one rented A100 SXM4 40 GB box at N in {2^10, 2^14, 2^18, 2^22, 2^24}, five seeds each, after
both match two independent references at N = 2^10 and 2^14, and read the card's rule.** Also read the card's three
measured-later numbers: `res_measured` (GUESS 1e-13), `crossover_n` (GUESS 1,024), `speedup_at_nmax` (PROXY 28), and its
cost line's "need 2 h".

Both outcomes are informative. if_lever confirms the card as written. if_not refutes it. A guess wrong by more than
10x (residual) or a crossover above the first level is a finding about the pipeline's estimates whichever way the
decision falls. Two further readings are reported beside the card's rule and do not decide it: the shape of PCR's
time against N (the card's if_lever sentence says "grows like log2(N)"), and the card's rule re-read against the CPU
floor the card itself names (LAPACK dgtsv on the instance CPU).

## Committed data

No file is downloaded. The systems are generated on the box by a committed rule:

| Item | Rule |
|---|---|
| Matrix | tridiagonal, N equations; off-diagonals a_i, c_i of unit magnitude with seed-fixed random signs; diagonal b_i = 3 (so |b| - |a| - |c| = 1, the card's "diagonal dominance margin 1.0"); float64 |
| Right-hand side | d_i standard normal, float64 |
| Generator | numpy `default_rng(seed)`, seeds 0, 1, 2, 3, 4 (one per timing repeat); the anchor uses seed 0 |
| Record | every generated system is reproducible from (N, seed); the first 8 values of a, b, c, d and the sha256 of each array are written per row |

The card record itself is the committed input: `../20261019-2344-tree/out/result.json`
sha256 `48ac464c98a73069aab7af8efbd53021ca5439a193af666a2e1ac6d0d32ac6ae` (PLAN in
`out/agents/0008-R1_physical_top_producer/reply.txt`, sha256 `5edcb633490ee446d7a77a8f32cf246efae31aab79919fe6b21ac4f6aa411b33`).

## Anchor

The card's own `p1_anchor`: at N = 2^10 and 2^14, the hand-written Thomas and PCR solutions must each have relative
residual ||A x - d||_2 / ||d||_2 **<= 1e-10** (the card's `res_tol`), computed in float64 on the CPU from the generated
arrays, and must agree with two independent references on the same systems: NVIDIA cuSPARSE `gtsv2_nopivot` on the GPU
and scipy `solve_banded` (LAPACK) on the CPU, each to **< 1e-8** relative difference in x (the card's `checks`). The two
references must also agree with each other to < 1e-8 (the card's fourth check; validates the references).

Out of band on either solver: that solver's timing rows are "descriptive only; anchor failed" and the card's rule is
not read (the card's own gate text applies: "Fix the kernels and re-run the anchor before starting the sweep"; no
kernel is fixed mid-run).

## What would refute each claim

- Claim A (card GUESS `res_measured = 1e-13`): the measured max relative residual over the anchor levels and both
  hand-written solvers. Holds if within [1e-14, 1e-12]; refuted outside (10x either way).
- Claim B (card GUESS `crossover_n = 1,024`, "PCR should already win at the smallest level"): the crossover is the
  smallest sweep level at which the lower quartile of the PCR/Thomas speedup over the five seeds exceeds 1 (the card's
  noise rule). Holds if the crossover is 2^10; refuted if it is higher or does not occur.
- Claim C (card `expected: if_lever`): refuted if, at N = 2^24, median Thomas ms / median PCR ms < 2, OR the speedup
  does not grow with N. "Grows with N" is read as: speedup at 2^24 > speedup at 2^10 AND the least-squares slope of
  log(speedup) against log2(N) over the five levels is positive. The noise rule: the lower quartile of the speedup at
  2^24 must also exceed 2 for the lever reading to be "a real difference" in the card's words; if the median passes and
  the lower quartile does not, the reading is if_lever with the label "within noise".
- Claim D (card PROXY `speedup_at_nmax = 28`, from a 2009 GTX 280 against CPU LAPACK): the measured speedup at 2^24.
  Holds if within [9.3, 84] (3x either way); refuted outside. A PROXY is cited for a different setting; this is a
  report on how far it travelled, not a card prediction.
- Claim E (card cost line: "6 h time box; need 2 h" for anchor plus sweep): the on-box wall-clock from the first anchor
  solve to the last sweep row. Holds if within [0.67, 6] h; refuted if below 0.67 h (the plan over-bought by more than
  3x) or above 6 h.
- Shape reading (report only; tests the card's if_lever sentence "wall-clock grows like log2(N)", not its rule): the
  per-doubling growth factor g = (median PCR ms at 2^24 / median PCR ms at 2^22)^(1/2). "log-like" if g <= 1.15,
  "linear-like" if g >= 1.7, "between" otherwise.
- CPU-floor reading (report only): the card's rule with median scipy `dgtsv` ms on the box's CPU in place of the
  one-thread GPU Thomas. Reported as if_lever or if_not under that baseline, with the speedup at each level.
- Copies reading (report only; the card's `baseline_copies` check): K independent systems solved at once by the
  Thomas kernel, one thread per system, K = min(256, 2^28 / N). The card's claim holds if the batched solve's time is
  within [0.9, 3] x the single-system time at every level (width raises throughput, one system's latency stays O(N)).
- cuSPARSE reading (report only): median cuSPARSE `gtsv2_nopivot` ms at each level and its ratio to the hand-written PCR.

## Scope

One GPU (A100 SXM4 40 GB, the card's hardware, at the card's rate of USD 1.99/h), one CPU core for the floor, float64,
one right-hand side, scalar tridiagonal systems with the generated structure. The card's phases `p1_anchor` and
`p2_sweep` only. Out of scope: block-tridiagonal systems (`p3_block`), multi-GPU PCR (`p4_multi`), the parallel-in-time
Newton loop the solve would sit inside, non-dominant or ill-conditioned matrices, float32, multiple right-hand sides,
any tuning of the Thomas kernel beyond the card's "one thread per system" with the recurrence kept in registers.

## Declared construct risks

- The card's sequential baseline is one GPU thread. Against it, any parallel method wins at large N by construction;
  the rule tests whether PCR is slower than the slowest arrangement of the sequential algorithm, not whether it is
  faster than the sequential algorithm as anyone would run it. The CPU-floor reading is added so the reader can see the
  difference; it does not change the card's verdict.
- The Thomas kernel's constant factor depends on how the builder writes it (register use, loads per step). The card
  says "tuned with a register-cached recurrence and #pragma unroll"; the build keeps the recurrence in registers and
  reads each input once per step. Stated as "the one-thread Thomas this build wrote", not "the fastest one-thread Thomas".
- Timing a sub-millisecond solve needs a block of back-to-back solves; the per-solve time then includes no host
  synchronisation but does include kernel-launch gaps. Blocks are sized so each timed block is at least 50 ms; the
  block size is recorded per row.
- PCR's per-round kernels are the builder's; a different PCR (shared-memory tiling, hybrid with Thomas below a cutoff,
  as cuSPARSE does) would be faster. The cuSPARSE reading bounds how far this PCR is from NVIDIA's.
- The CPU floor is one core running LAPACK through scipy 1.8.0 as the image ships it (OpenBLAS or MKL unknown until
  read on the box; recorded). It is a floor for "sequential on this box", not the best CPU.

## How the card maps onto this record

| Card (PLAN) field | Here |
|---|---|
| `anchor`, `checks` 1-4, `phases[p1_anchor].gate` | Anchor section; Claim A |
| `predictions.decision_rule`, `expected`, `noise_rule` | Claim C |
| `numbers[res_measured]` GUESS, `measured_by: p1_anchor` | Claim A |
| `numbers[crossover_n]` GUESS, `measured_by: p2_sweep` | Claim B |
| `numbers[speedup_at_nmax]` PROXY, `measured_by: p2_sweep` | Claim D |
| `cost.lines[l_anchor_sweep]` hours 6, need 2 | Claim E |
| `predictions.if_lever` sentence ("grows like log2(N)"), `checks` 5 | Shape reading |
| `restructuring.baseline_sequential` ("MKL dgtsv on the instance CPU as a floor") | CPU-floor reading |
| `restructuring.baseline_copies`, arm a4, `checks` 6 | Copies reading |
| arm a3 (cuSPARSE as independent reference) | Anchor; cuSPARSE reading |
| `held_fixed` | Scope |
| `phases[p3_block]`, `phases[p4_multi]` | not run |


=== run_m2.py (138132 bytes)
#!/usr/bin/env python3
"""Runner for measure run m2: a one-thread GPU Thomas solve against a parallel cyclic reduction solve.

What it measures. One rented GPU box times two hand-written CUDA solvers of a tridiagonal linear system.
A tridiagonal matrix has nonzeros only on its main diagonal and the two diagonals next to it.
The first solver is the Thomas algorithm (forward elimination, then back substitution) on one CUDA thread.
The second is parallel cyclic reduction (PCR): one thread per equation per round, log2(N) rounds.
Systems have N equations, N in 2^10, 2^14, 2^18, 2^22, 2^24, with five seeds each.
Two independent references check the answers first: NVIDIA cuSPARSE gtsv2_nopivot and scipy solve_banded.
The card's own decision rule is then read from the timings.

Stages, in the order onbox_m2.sh runs them. Each stage reads only files that earlier stages wrote.
So each stage can be run again on its own.
  build             check numpy, scipy.linalg and nvcc; write the CUDA source; compile it; record labels
  gpucheck          cudaGetDeviceCount >= 1 through ctypes
  anchor            planted arithmetic controls (I2..I10, gate propagation); readout control (I1); anchor (E1, E2)
  timers            CPU sleep clock; cudaEvent against the wall clock; a block of 2R solves against R
  residual_sweep    one Thomas and one PCR solve per level and seed, residuals recorded (report only)
  thomas_gpu pcr_gpu cusparse_gpu thomas_batched_gpu launch_probe cpu_dgtsv      the timing arms
  endpoints         E3..E10 from the timing rows
  summary           m2_summary.json: restates the records and decides nothing
  guard             time and cost guard arithmetic, used by onbox_m2.sh before every stage
The pipeline template's stage names map onto these groups.
extract = build + gpucheck; generate = anchor through cpu_dgtsv; endpoints = endpoints.

  python3 run_m2.py --selftest      stdlib only: no numpy, no scipy, no CUDA
"""
from __future__ import annotations

import argparse
import contextlib
import ctypes
import glob
import hashlib
import io
import json
import math
import os
import random
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "m2"

# ------------------------------------------------------------------------------------------------------------
# Fixed numbers. Each comes from the design record or the execution note. GUESS marks the design's guesses.
# ------------------------------------------------------------------------------------------------------------
LEVELS = [2 ** 10, 2 ** 14, 2 ** 18, 2 ** 22, 2 ** 24]   # sweep levels, the card's compute axis
SEEDS = [0, 1, 2, 3, 4]                                   # one generated system per seed
ANCHOR_LEVELS = [2 ** 10, 2 ** 14]
ANCHOR_SEED = 0
WARMUPS = 2                                               # warm-up solves before each timed block
BLOCK_MS = 50.0                                           # GUESS: R = max(1, ceil(50 ms / warm-up ms per solve))
K_CAP, K_TOTAL = 256, 2 ** 28                             # GUESS: batched copies K = min(256, 2^28 / N)
PCR_BLOCKDIM = 256
B_DIAG = 3.0                                              # diagonal value; off-diagonals are signs of size 1
RES_TOL = 1e-10                                           # the card's residual tolerance
DIFF_TOL = 1e-8                                           # the card's agreement tolerance (checks 1 to 4)
E2_GUESS, E2_BAND = 1e-13, (1e-14, 1e-12)
GATE_SPEEDUP = 2.0
E5_PROXY, E5_BAND = 28.0, (9.3, 84.0)
E6_LOG_MAX, E6_LIN_MIN = 1.15, 1.7                        # GUESS thresholds for the growth shape
E8_BAND = (0.9, 3.0)
E10_BAND = (0.67, 6.0)
E10_NEED_H = 2.0
LAUNCH_BOUND = 0.5
I1_EXACT_TOL, I1_PERTURB, I1_BAND = 1e-14, 1e-6, (1e-7, 1e-5)
TIMER_N = 2 ** 14
TIMER_SLEEP_MS, TIMER_SLEEP_TOL_MS = 100.0, 5.0
TIMER_EVENT_TOL, TIMER_2R_TOL = 0.05, 0.15

# Guard constants. They bound spend and wall-clock only; they decide nothing about the card.
GUARD_RESERVE_S = 90        # kept free at the end for the summary and the done marker
GUARD_TEARDOWN_S = 300      # billed time after the done marker: launcher poll, fetch, terminate
GUARD_MIN_STAGE_S = 30      # a stage is not started with less time than this

LABEL_DRAMATURG = "card dramaturg: REJECT (3 blocking, citations)"
LABEL_BASELINE = "baseline: one CUDA thread per system, this build's kernel"
LABEL_ANCHOR_FAILED = "descriptive only; anchor failed"
LABEL_ONE_REF = "one reference only"
ROLE_REPORT_ONLY = "report-only; does not decide the card"
SUMMARY_NOTE = ("Restates the records under records/ and decides nothing. The five seeds are five different "
                "generated systems timed on one box, not separate boxes.")

# Execution note item 2: an anchor failure labels that solver's rows and leaves the card unread.
# Only disagreeing references (and the other gates) make run_valid false. Set True to void on anchor failure.
ANCHOR_FAIL_VOIDS_RUN = False

EXIT_OK, EXIT_ERROR, EXIT_TOOLCHAIN, EXIT_GPU, EXIT_ENV, EXIT_GUARD_STOP, EXIT_WRONG_VARIANCE = 0, 1, 2, 3, 4, 5, 6
SPARSE_BASE = 100000        # status codes at or above this are cuSPARSE statuses plus this base

TIMING_ARMS = ["thomas_gpu", "pcr_gpu", "cusparse_gpu", "thomas_batched_gpu", "launch_probe", "cpu_dgtsv"]
SWEEP_ROW_FILES = ["residual_sweep"] + TIMING_ARMS
ARM_SOLVER = {"thomas_gpu": "thomas", "thomas_batched_gpu": "thomas", "pcr_gpu": "pcr"}
STAGE_ORDER = ["build", "gpucheck", "anchor", "timers", "residual_sweep"] + TIMING_ARMS + ["endpoints"]
STAGE_GROUPS = {"extract": ["build", "gpucheck"],
                "generate": ["anchor", "timers", "residual_sweep"] + TIMING_ARMS}

ARM_TEXT = {
    "thomas_gpu": "one system solved by the Thomas algorithm on one CUDA thread (thomas_gpu)",
    "pcr_gpu": "one system solved by parallel cyclic reduction, one thread per equation per round (pcr_gpu)",
    "cusparse_gpu": "one system solved by NVIDIA cuSPARSE gtsv2_nopivot (cusparse_gpu)",
    "thomas_batched_gpu": ("K copies of one system solved at once by the same one-thread Thomas kernel, "
                           "one block per copy (thomas_batched_gpu)"),
    "launch_probe": "an empty CUDA kernel launched with the level's PCR grid shape; ms per launch (launch_probe)",
    "cpu_dgtsv": "one system solved by LAPACK dgtsv through scipy on one CPU core (cpu_dgtsv)",
}

EXPECTED_RECORDS = (["toolchain", "gpu_check"] + [f"I{k}" for k in range(2, 11)] + ["gate_propagation"]
                    + ["I1_exact", "I1_perturbed", "I1_references", "E1", "E2", "timers", "residual_sweep"]
                    + TIMING_ARMS + ["timing_rows_check", "dispersion"] + [f"E{k}" for k in range(3, 11)])

# Decision rules, stated before any value is known (the record writer's convention).
RULES = {
    "toolchain": ("PASS iff numpy and scipy.linalg import, nvcc is found (PATH, then /usr/local/cuda/bin, then "
                  "/usr/local/cuda-*/bin), the CUDA source compiles with the fixed command, and the library "
                  "loads. Otherwise FAIL, run_valid false, exit 2. A missing cuSPARSE library alone does not "
                  "fail: its arm is NOT_RUN and the anchor reads against scipy alone."),
    "gpu_check": ("PASS iff cudaGetDeviceCount through ctypes returns success and at least 1 device. Otherwise "
                  "FAIL, run_valid false, exit 3, no CPU-only fallback."),
    "I1_exact": ("x* = ones at N = 2^10, seed 0, d = A x*. The residual readout of x* itself must be <= 1e-14. "
                 "Otherwise FAIL and run_valid false."),
    "I1_perturbed": ("x* perturbed by 1e-6 relative (alternating signs). The residual readout must lie in "
                     "[1e-7, 1e-5]. Otherwise FAIL and run_valid false."),
    "I1_references": ("On the same planted system, cuSPARSE and scipy solve_banded must agree to < 1e-8 relative "
                      "difference. Otherwise FAIL and run_valid false. NOT_RUN when cuSPARSE is missing."),
    "E1": ("Thomas and PCR at N = 2^10 and 2^14, seed 0: each relative residual <= 1e-10 AND each relative "
           "difference against cuSPARSE and against scipy < 1e-8. A solver out of band: its timing rows are "
           "labelled 'descriptive only; anchor failed' and E3, E4, E5 are NOT_READ; the box continues. "
           "cuSPARSE against scipy >= 1e-8: run_valid false in every record written after. cuSPARSE missing: "
           "read against scipy alone, label 'one reference only'."),
    "E2": ("Max relative residual over the anchor levels and both hand-written solvers. HOLDS if within "
           "[1e-14, 1e-12]. Below: REFUTED, the guess 1e-13 was too pessimistic. Above: REFUTED, too optimistic."),
    "E3": ("speedup(N) = median Thomas ms / median PCR ms over the five seeds. if_lever iff speedup(2^24) >= 2 "
           "AND speedup(2^24) > speedup(2^10) AND the least-squares slope of ln(speedup) against log2(N) over "
           "the five levels > 0. Otherwise if_not. Label 'within noise' when if_lever and the lower quartile of "
           "the per-seed ratio Thomas_ms / PCR_ms at 2^24 is <= 2. NOT_READ if the anchor failed for either."),
    "E4": ("Crossover = smallest level at which the lower quartile over seeds of Thomas_ms / PCR_ms exceeds 1. "
           "HOLDS iff the crossover is 2^10. Higher or none: REFUTED. Label 'crossover at 2^10 is launch-bound' "
           "when the PCR launch fraction at 2^10 is > 0.5. NOT_READ if the anchor failed for either solver."),
    "E5": ("Measured speedup(2^24) against the card's proxy 28. HOLDS if within [9.3, 84]. Outside: REFUTED, "
           "direction and ratio (measured / 28) reported. NOT_READ if the anchor failed for either solver."),
    "E6": ("g = (median PCR ms at 2^24 / median PCR ms at 2^22)^(1/2). log-like if g <= 1.15; linear-like if "
           "g >= 1.7; between otherwise. Report only."),
    "E7": ("E3's rule with median scipy dgtsv ms on one CPU core in place of the one-thread GPU Thomas ms. "
           "if_lever or if_not under that baseline, speedup at every level. Report only."),
    "E8": ("ratio(N) = median batched Thomas ms / median single Thomas ms; throughput factor K / ratio. The "
           "card's copies claim HOLDS if the ratio is within [0.9, 3] at every level. Otherwise FAILS, labelled "
           "'batched solve changes one system's latency'. Report only."),
    "E9": "Median cuSPARSE ms at each level and ratio = median PCR ms / median cuSPARSE ms. Report only.",
    "E10": ("Hours from the first anchor solve to the last sweep row. HOLDS if within [0.67, 6]. Below 0.67: "
            "REFUTED, the plan over-bought by more than 3x. Above 6: REFUTED, the plan under-bought."),
    "timers": ("A 100 ms time.sleep measures within +/- 5 ms; a cudaEvent-timed PCR block at N = 2^14 agrees "
               "with perf_counter around it within 5%; a block of 2R solves takes 2x the block of R within 15% "
               "for Thomas and for PCR at N = 2^14. All three PASS, otherwise FAIL and run_valid false."),
    "residual_sweep": "Report only: relative residual of one Thomas and one PCR solve per level and seed.",
    "arm": ("MEASURED iff every level has all five seeds with positive, finite ms per solve; otherwise "
            "INCOMPLETE. The anchor label of the solver is appended when it failed."),
    "timing_rows_check": ("PASS iff no timing row has non-positive or non-finite ms, a non-finite solution, or "
                          "a nonzero solver status. Otherwise FAIL and run_valid false."),
    "dispersion": ("The noise-rule quantity is the per-seed ratio over five generated systems. If its "
                   "interquartile range is exactly zero at any level, the wrong variance source was chosen: "
                   "WRONG_VARIANCE_SOURCE, run_valid false, the endpoints stage halts."),
    "planted": "PASS iff the endpoint arithmetic reproduces every planted known decision; otherwise FAIL, void.",
    "gate_propagation": ("PASS iff a planted Thomas anchor failure (residual 1e-9) labels Thomas rows and writes "
                         "E3, E4, E5 NOT_READ, and a planted reference disagreement (1e-7) writes run_valid "
                         "false into every record and row written after it. Otherwise FAIL and run_valid false."),
}


_LOG_TAG = [""]   # set while a planted control runs in a temporary directory, so its log lines say so


def log(msg: str) -> None:
    print(f"[m2 {time.strftime('%H:%M:%S')}] {_LOG_TAG[0]}{msg}", flush=True)


# ------------------------------------------------------------------------------------------------------------
# CUDA C source. Written to results_m2/build/m2_kernels.cu by the build stage, hashed, compiled with nvcc.
# ------------------------------------------------------------------------------------------------------------
CUDA_SOURCE = r"""// m2_kernels.cu: written by run_m2.py (build stage); its sha256 is recorded in env.json.
// Thomas: one CUDA thread per system, recurrence carried in registers; plain, no unroll, no variant search.
// PCR: one thread per equation per round, strides 1, 2, 4, ..., N/2, one launch per round, 256 threads a block.
// Thin C wrappers: device memory, cudaEvent timing of a block of R back-to-back solves, the cuSPARSE call.
#include <cuda_runtime.h>
#include <stddef.h>
#ifndef M2_NO_CUSPARSE
#include <cusparse.h>
#endif

#define M2_PCR_BLOCK 256
#define M2_SPARSE_BASE 100000

// Thomas, one thread per system. blockIdx.x picks the system; systems are laid out one after another.
// Forward: w = a_i / b'_{i-1}; b'_i = b_i - w c_{i-1}; d'_i = d_i - w d'_{i-1}. Back: x_i = (d'_i - c_i x_{i+1}) / b'_i.
__global__ void m2_thomas_kernel(const double* a, const double* b, const double* c, const double* d,
                                 double* bp, double* dp, double* x, int n)
{
    if (threadIdx.x != 0) return;
    const size_t off = (size_t)blockIdx.x * (size_t)n;
    a += off; b += off; c += off; d += off; bp += off; dp += off; x += off;
    double bprev = b[0];
    double dprev = d[0];
    double cprev = c[0];
    bp[0] = bprev;
    dp[0] = dprev;
    for (int i = 1; i < n; ++i) {
        const double w = a[i] / bprev;
        const double bi = b[i] - w * cprev;
        const double di = d[i] - w * dprev;
        bp[i] = bi;
        dp[i] = di;
        bprev = bi;
        dprev = di;
        cprev = c[i];
    }
    double xi = dprev / bprev;
    x[n - 1] = xi;
    for (int i = n - 2; i >= 0; --i) {
        xi = (dp[i] - c[i] * xi) / bp[i];
        x[i] = xi;
    }
}

// One PCR round at stride s. Coefficients outside [0, n) are zero. The last round writes x_i = d_i / b_i.
__global__ void m2_pcr_round(const double* a, const double* b, const double* c, const double* d,
                             double* a2, double* b2, double* c2, double* d2, double* x,
                             int n, int s, int last)
{
    const int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= n) return;
    double alpha = 0.0, gamma = 0.0;
    double am = 0.0, cm = 0.0, dm = 0.0;
    double ap = 0.0, cp = 0.0, dq = 0.0;
    const int im = i - s;
    const int ip = i + s;
    if (im >= 0) { alpha = -a[i] / b[im]; am = a[im]; cm = c[im]; dm = d[im]; }
    if (ip < n)  { gamma = -c[i] / b[ip]; ap = a[ip]; cp = c[ip]; dq = d[ip]; }
    const double nb = b[i] + alpha * cm + gamma * ap;
    const double nd = d[i] + alpha * dm + gamma * dq;
    if (last) { x[i] = nd / nb; return; }
    a2[i] = alpha * am;
    b2[i] = nb;
    c2[i] = gamma * cp;
    d2[i] = nd;
}

__global__ void m2_empty_kernel(void) {}

// log2(n) rounds; round 0 reads the inputs, later rounds ping-pong between the two buffer sets.
static void m2_pcr_launch(int n, const double* a, const double* b, const double* c, const double* d,
                          double* const* buf, double* x)
{
    const int grid = (n + M2_PCR_BLOCK - 1) / M2_PCR_BLOCK;
    const double* ia = a; const double* ib = b; const double* ic = c; const double* id = d;
    int r = 0;
    for (int s = 1; s < n; s <<= 1, ++r) {
        double* const* o = buf + 4 * (r & 1);
        const int last = (2 * s >= n) ? 1 : 0;
        m2_pcr_round<<<grid, M2_PCR_BLOCK>>>(ia, ib, ic, id, o[0], o[1], o[2], o[3], x, n, s, last);
        ia = o[0]; ib = o[1]; ic = o[2]; id = o[3];
    }
}

typedef struct { cudaEvent_t e0; cudaEvent_t e1; } m2_timer;

static int m2_timer_start(m2_timer* t)
{
    int err = (int)cudaEventCreate(&t->e0);
    if (!err) err = (int)cudaEventCreate(&t->e1);
    if (!err) err = (int)cudaDeviceSynchronize();
    if (!err) err = (int)cudaEventRecord(t->e0, 0);
    return err;
}

static int m2_timer_stop(m2_timer* t, float* ms)
{
    int err = (int)cudaGetLastError();
    if (!err) err = (int)cudaEventRecord(t->e1, 0);
    if (!err) err = (int)cudaEventSynchronize(t->e1);
    if (!err) err = (int)cudaDeviceSynchronize();
    if (!err) err = (int)cudaEventElapsedTime(ms, t->e0, t->e1);
    return err;
}

static void m2_timer_free(m2_timer* t)
{
    if (t->e0) cudaEventDestroy(t->e0);
    if (t->e1) cudaEventDestroy(t->e1);
}

extern "C" {

int m2_device_count(int* n) { return (int)cudaGetDeviceCount(n); }
int m2_runtime_version(int* v) { return (int)cudaRuntimeGetVersion(v); }
int m2_driver_version(int* v) { return (int)cudaDriverGetVersion(v); }
const char* m2_error_string(int e) { return cudaGetErrorString((cudaError_t)e); }

int m2_has_cusparse(void)
{
#ifdef M2_NO_CUSPARSE
    return 0;
#else
    return 1;
#endif
}

int m2_malloc(void** p, size_t bytes) { return (int)cudaMalloc(p, bytes); }
int m2_free(void* p) { return (int)cudaFree(p); }
int m2_h2d(void* dst, const void* src, size_t bytes) { return (int)cudaMemcpy(dst, src, bytes, cudaMemcpyHostToDevice); }
int m2_d2h(void* dst, const void* src, size_t bytes) { return (int)cudaMemcpy(dst, src, bytes, cudaMemcpyDeviceToHost); }
int m2_d2d(void* dst, const void* src, size_t bytes) { return (int)cudaMemcpy(dst, src, bytes, cudaMemcpyDeviceToDevice); }
int m2_sync(void) { return (int)cudaDeviceSynchronize(); }

int m2_solve_thomas(int K, int n, const double* a, const double* b, const double* c, const double* d,
                    double* bp, double* dp, double* x)
{
    m2_thomas_kernel<<<K, 1>>>(a, b, c, d, bp, dp, x, n);
    int err = (int)cudaGetLastError();
    if (!err) err = (int)cudaDeviceSynchronize();
    return err;
}

int m2_time_thomas(int R, int K, int n, const double* a, const double* b, const double* c, const double* d,
                   double* bp, double* dp, double* x, float* ms)
{
    m2_timer t = {0, 0};
    *ms = -1.0f;
    int err = m2_timer_start(&t);
    if (!err) {
        for (int r = 0; r < R; ++r) m2_thomas_kernel<<<K, 1>>>(a, b, c, d, bp, dp, x, n);
        err = m2_timer_stop(&t, ms);
    }
    m2_timer_free(&t);
    return err;
}

int m2_solve_pcr(int n, const double* a, const double* b, const double* c, const double* d,
                 double* p0, double* p1, double* p2, double* p3, double* p4, double* p5, double* p6, double* p7,
                 double* x)
{
    double* buf[8] = {p0, p1, p2, p3, p4, p5, p6, p7};
    m2_pcr_launch(n, a, b, c, d, buf, x);
    int err = (int)cudaGetLastError();
    if (!err) err = (int)cudaDeviceSynchronize();
    return err;
}

int m2_time_pcr(int R, int n, const double* a, const double* b, const double* c, const double* d,
                double* p0, double* p1, double* p2, double* p3, double* p4, double* p5, double* p6, double* p7,
                double* x, float* ms)
{
    double* buf[8] = {p0, p1, p2, p3, p4, p5, p6, p7};
    m2_timer t = {0, 0};
    *ms = -1.0f;
    int err = m2_timer_start(&t);
    if (!err) {
        for (int r = 0; r < R; ++r) m2_pcr_launch(n, a, b, c, d, buf, x);
        err = m2_timer_stop(&t, ms);
    }
    m2_timer_free(&t);
    return err;
}

int m2_time_empty(int R, int grid, int block, float* ms)
{
    m2_timer t = {0, 0};
    *ms = -1.0f;
    int err = m2_timer_start(&t);
    if (!err) {
        for (int r = 0; r < R; ++r) m2_empty_kernel<<<grid, block>>>();
        err = m2_timer_stop(&t, ms);
    }
    m2_timer_free(&t);
    return err;
}

#ifndef M2_NO_CUSPARSE
static cusparseHandle_t m2_sparse = 0;

int m2_cusparse_init(void)
{
    if (m2_sparse) return 0;
    int st = (int)cusparseCreate(&m2_sparse);
    return st ? M2_SPARSE_BASE + st : 0;
}

int m2_cusparse_bufsize(int m, const double* dl, const double* d, const double* du, const double* B, size_t* bytes)
{
    int st = (int)cusparseDgtsv2_nopivot_bufferSizeExt(m2_sparse, m, 1, dl, d, du, B, m, bytes);
    return st ? M2_SPARSE_BASE + st : 0;
}

int m2_cusparse_solve(int m, const double* dl, const double* d, const double* du, double* B, void* buf)
{
    int st = (int)cusparseDgtsv2_nopivot(m2_sparse, m, 1, dl, d, du, B, m, buf);
    if (st) return M2_SPARSE_BASE + st;
    return (int)cudaDeviceSynchronize();
}

// R solves, each on its own copy of the right-hand side (B_all holds R copies laid out one after another).
int m2_time_cusparse(int R, int m, const double* dl, const double* d, const double* du, double* B_all, void* buf,
                     float* ms)
{
    m2_timer t = {0, 0};
    int st = 0;
    *ms = -1.0f;
    int err = m2_timer_start(&t);
    if (!err) {
        for (int r = 0; r < R && !st; ++r)
            st = (int)cusparseDgtsv2_nopivot(m2_sparse, m, 1, dl, d, du, B_all + (size_t)r * (size_t)m, m, buf);
        err = m2_timer_stop(&t, ms);
    }
    m2_timer_free(&t);
    if (st) return M2_SPARSE_BASE + st;
    return err;
}
#endif

}  // extern "C"
"""

# Functions the Python side binds; the selftest checks each is defined in the source above.
CUDA_EXPORTS = ["m2_device_count", "m2_runtime_version", "m2_driver_version", "m2_error_string",
                "m2_has_cusparse", "m2_malloc", "m2_free", "m2_h2d", "m2_d2h", "m2_d2d", "m2_sync",
                "m2_solve_thomas", "m2_time_thomas", "m2_solve_pcr", "m2_time_pcr", "m2_time_empty"]
CUSPARSE_EXPORTS = ["m2_cusparse_init", "m2_cusparse_bufsize", "m2_cusparse_solve", "m2_time_cusparse"]


def nvcc_command(nvcc: str, cu: str, so: str, arch: str | None, cusparse: bool) -> list:
    """The execution note's command, verbatim; -arch=sm_80 only for an A100; no cuSPARSE when it is missing."""
    cmd = [nvcc, "-O3", "-shared", "-Xcompiler", "-fPIC"]
    if not cusparse:
        cmd.append("-DM2_NO_CUSPARSE")
    cmd += ["-o", so, cu]
    if cusparse:
        cmd.append("-lcusparse")
    cmd.append("-lcudart")
    if arch:
        cmd.append(f"-arch={arch}")
    return cmd


# ------------------------------------------------------------------------------------------------------------
# Parsers (each covered by the selftest)
# ------------------------------------------------------------------------------------------------------------
def parse_nvcc_version(text: str | None) -> str | None:
    m = re.search(r"release\s+([0-9]+\.[0-9]+),\s*V([0-9][0-9.]*)", text or "")
    return f"{m.group(1)} (V{m.group(2)})" if m else None


def parse_nvidia_smi_csv(text: str | None) -> dict:
    line = next((ln for ln in (text or "").splitlines() if ln.strip()), "")
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 2 or not parts[0]:
        return {"gpu_name": None, "gpu_driver": None, "gpu_memory": None}
    return {"gpu_name": parts[0], "gpu_driver": parts[1], "gpu_memory": parts[2] if len(parts) > 2 else None}


def format_cuda_version(v) -> str | None:
    if not isinstance(v, int) or isinstance(v, bool) or v <= 0:
        return None
    return f"{v // 1000}.{(v % 1000) // 10}"


def parse_blas_vendor(text: str | None) -> str:
    """Vendor from scipy.show_config text. New style names it ('blas: ... name: openblas'). Old style lists
    sections; sections marked NOT AVAILABLE are skipped and only their 'libraries = [...]' lists are read."""
    t = text or ""
    m = re.search(r"^[ \t]*blas:[ \t]*\n(?:[ \t]+.*\n)*?[ \t]+name:[ \t]*(\S+)", t, re.M)
    if m:
        return m.group(1).strip().lower()
    libs = []
    for _sec, body in re.findall(r"^(\S+):[ \t]*\n((?:[ \t]+.*(?:\n|$))*)", t, re.M):
        if "NOT AVAILABLE" in body:
            continue
        for lm in re.finditer(r"libraries\s*=\s*\[([^\]]*)\]", body):
            libs += [x.strip().strip("'\"").lower() for x in lm.group(1).split(",") if x.strip()]
    for key in ("mkl", "openblas", "blis", "flexiblas", "accelerate", "atlas"):
        if any(key in lib for lib in libs):
            return key
    if libs:
        return "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries"
    return "unknown"


def parse_ldd(text: str | None) -> dict:
    """ldd output -> {library name: resolved path, or None when 'not found'}."""
    libs = {}
    for line in (text or "").splitlines():
        m = re.match(r"\s*(\S+)\s+=>\s+(not found|\S+)", line)
        if m:
            libs[m.group(1)] = None if m.group(2) == "not found" else m.group(2)
    return libs


def parse_uptime(text: str | None) -> float | None:
    try:
        v = float((text or "").split()[0])
    except (IndexError, ValueError):
        return None
    return v if math.isfinite(v) and v >= 0 else None


def parse_positive_float(s) -> float | None:
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) and v > 0 else None


def parse_nonneg_float(s) -> float | None:
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) and v >= 0 else None


def detect_cusparse_missing(log_text: str | None) -> bool:
    t = (log_text or "").lower()
    keys = ("cannot find", "no such file", "not found", "undefined reference", "cannot open shared object")
    return "cusparse" in t and any(k in t for k in keys)


def cuda_dir_version_key(path: str) -> tuple:
    m = re.search(r"cuda-(\d+)\.(\d+)", path)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def read_jsonl(path) -> list:
    rows = []
    with open(path) as f:
        for k, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{path}:{k}: malformed row ({e})") from None
    return rows


# ------------------------------------------------------------------------------------------------------------
# Small statistics, stdlib only. Quartiles use linear interpolation (index (n-1) q, numpy's default).
# ------------------------------------------------------------------------------------------------------------
def is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def pos_finite(x) -> bool:
    return is_num(x) and math.isfinite(x) and x > 0


def le(x, t) -> bool:
    return is_num(x) and math.isfinite(x) and x <= t


def lt(x, t) -> bool:
    return is_num(x) and math.isfinite(x) and x < t


def median(xs) -> float:
    s = sorted(xs)
    n = len(s)
    if n == 0:
        raise ValueError("median of nothing")
    return float(s[n // 2]) if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def quantile(xs, q: float) -> float:
    s = sorted(xs)
    if not s:
        raise ValueError("quantile of nothing")
    pos = (len(s) - 1) * q
    lo, hi = int(math.floor(pos)), int(math.ceil(pos))
    return float(s[lo] + (s[hi] - s[lo]) * (pos - lo))


def iqr(xs) -> float:
    return quantile(xs, 0.75) - quantile(xs, 0.25)


def ls_slope(xs, ys) -> float:
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / sxx


def same4(a, b) -> bool:
    """Equal to 4 significant digits."""
    return ("%.4g" % a) == ("%.4g" % b)


def fmt(x) -> str:
    return "%.4g" % x if is_num(x) else str(x)


# ------------------------------------------------------------------------------------------------------------
# Rules for R, K and launch fraction
# ------------------------------------------------------------------------------------------------------------
def r_rule(warm_ms: float) -> int:
    """R = max(1, ceil(50 ms / warm-up ms per solve)); the second warm-up solve's ms is used."""
    return max(1, int(math.ceil(BLOCK_MS / warm_ms)))


def k_rule(N: int) -> int:
    return min(K_CAP, K_TOTAL // N)


def log2_int(N: int) -> int:
    return int(round(math.log2(N)))


def launch_fraction(N: int, ms_per_launch: float, ms_per_solve: float) -> float:
    return log2_int(N) * ms_per_launch / ms_per_solve


# ------------------------------------------------------------------------------------------------------------
# Degenerate-output detectors
# ------------------------------------------------------------------------------------------------------------
def detect_bad_vector(xs) -> str | None:
    """A solution that cannot be a solve: empty, non-finite values, or all zeros."""
    vals = [float(v) for v in xs]
    if not vals:
        return "empty"
    if any(not math.isfinite(v) for v in vals):
        return "non-finite values"
    if all(v == 0.0 for v in vals):
        return "all zeros"
    return None


def detect_bad_timing_row(r: dict) -> str | None:
    if r.get("kind") != "timing":
        return None
    for key in ("ms_per_solve", "block_ms"):
        if not pos_finite(r.get(key)):
            return f"{key} not positive and finite ({r.get(key)!r})"
    if not (isinstance(r.get("R"), int) and r["R"] >= 1):
        return f"R not a positive integer ({r.get('R')!r})"
    if r.get("x_finite") is False:
        return "solution not finite"
    if r.get("solver_status") not in (None, 0):
        return f"solver status {r.get('solver_status')!r}"
    if r.get("degenerate"):
        return str(r["degenerate"])
    return None


def ms_table(rows, key: str = "ms_per_solve") -> dict:
    """Timing rows -> {N: {seed: value}}."""
    t: dict = {}
    for r in rows:
        if r.get("kind") != "timing":
            continue
        t.setdefault(int(r["N"]), {})[int(r["seed"])] = r.get(key)
    return t


def table_complete(t: dict) -> bool:
    return all(N in t and all(pos_finite(t[N].get(s)) for s in SEEDS) for N in LEVELS)


def missing_cells(t: dict) -> list:
    return [[N, s] for N in LEVELS for s in SEEDS if not pos_finite(t.get(N, {}).get(s))]


# ------------------------------------------------------------------------------------------------------------
# Endpoint arithmetic (pure; the planted controls and the endpoints stage both call these)
# ------------------------------------------------------------------------------------------------------------
def decide_e1(levels: list) -> dict:
    """levels: [{"N", "thomas": {"res", "diff_cusparse", "diff_scipy"}, "pcr": {...}, "ref_diff"}]."""
    one_ref = any(lv.get("ref_diff") is None for lv in levels)
    ok, reasons = {}, []
    for s in ("thomas", "pcr"):
        good = True
        for lv in levels:
            r = lv[s].get("res")
            if not le(r, RES_TOL):
                good = False
                reasons.append(f"{s} residual {fmt(r)} not <= {RES_TOL:g} at N={lv['N']}")
            for ref in ("cusparse", "scipy"):
                dv = lv[s].get("diff_" + ref)
                if dv is None and (ref == "cusparse" and one_ref):
                    continue
                if not lt(dv, DIFF_TOL):
                    good = False
                    reasons.append(f"{s} differs from {ref} by {fmt(dv)}, not < {DIFF_TOL:g}, at N={lv['N']}")
        ok[s] = good
    agree = None
    if not one_ref:
        agree = all(lt(lv.get("ref_diff"), DIFF_TOL) for lv in levels)
        if not agree:
            reasons.append("the two references (cuSPARSE, scipy) disagree by >= 1e-8: "
                           + ", ".join(f"N={lv['N']}: {fmt(lv.get('ref_diff'))}" for lv in levels))
    passed = ok["thomas"] and ok["pcr"] and agree is not False
    decision = "PASS" if passed else "FAIL: " + "; ".join(reasons)
    if one_ref:
        decision += f"; {LABEL_ONE_REF}"
    return {"decision": decision, "solver_ok": ok, "references_agree": agree, "one_reference_only": one_ref,
            "reasons": reasons}


def decide_e2(max_res) -> dict:
    lo, hi = E2_BAND
    if not (is_num(max_res) and math.isfinite(max_res)):
        return {"decision": "NOT_READ: residual not finite", "direction": None, "max_residual": max_res}
    if lo <= max_res <= hi:
        return {"decision": "HOLDS", "direction": None, "max_residual": max_res}
    if max_res < lo:
        return {"decision": "REFUTED", "direction": "too pessimistic", "max_residual": max_res,
                "guess_over_measured": E2_GUESS / max_res if max_res > 0 else None}
    return {"decision": "REFUTED", "direction": "too optimistic", "max_residual": max_res,
            "measured_over_guess": max_res / E2_GUESS}


def speedup_table(num: dict, den: dict) -> list:
    """num, den: {N: {seed: ms}}. speedup = median num / median den; per-seed ratio for the noise rule."""
    out = []
    for N in LEVELS:
        seeds = [s for s in SEEDS if s in num.get(N, {}) and s in den.get(N, {})]
        mn, md = median([num[N][s] for s in seeds]), median([den[N][s] for s in seeds])
        ratios = [num[N][s] / den[N][s] for s in seeds]
        out.append({"N": N, "log2_N": log2_int(N), "median_numerator_ms": mn, "median_denominator_ms": md,
                    "speedup": mn / md, "per_seed_ratio": ratios, "lower_quartile_ratio": quantile(ratios, 0.25),
                    "iqr_ratio": iqr(ratios)})
    return out


def decide_lever(table: list) -> dict:
    s = [r["speedup"] for r in table]
    x = [r["log2_N"] for r in table]
    slope = ls_slope(x, [math.log(v) for v in s])
    top_ok = s[-1] >= GATE_SPEEDUP
    above = s[-1] > s[0]
    lever = top_ok and above and slope > 0
    lq_top = table[-1]["lower_quartile_ratio"]
    label = "within noise" if (lever and lq_top <= GATE_SPEEDUP) else None
    decreases = [{"from_N": table[k]["N"], "to_N": table[k + 1]["N"], "from_speedup": s[k], "to_speedup": s[k + 1]}
                 for k in range(len(s) - 1) if s[k + 1] < s[k]]
    return {"decision": "if_lever" if lever else "if_not", "label": label, "speedups": s,
            "slope_ln_speedup_per_log2N": slope, "speedup_top_at_least_2": top_ok,
            "speedup_top_above_bottom": above, "slope_positive": slope > 0, "lower_quartile_top": lq_top,
            "adjacent_decreases": decreases}


def lever_from_tables(num: dict, den: dict) -> dict:
    tab = speedup_table(num, den)
    r = decide_lever(tab)
    r["table"] = tab
    return r


def decide_e4(lqs: list) -> dict:
    cross = next((N for N, q in zip(LEVELS, lqs) if q > 1.0), None)
    return {"decision": "HOLDS" if cross == LEVELS[0] else "REFUTED", "crossover_N": cross,
            "lower_quartiles": list(lqs)}


def decide_e5(s_top: float) -> dict:
    lo, hi = E5_BAND
    ratio = s_top / E5_PROXY
    if lo <= s_top <= hi:
        return {"decision": "HOLDS", "direction": None, "speedup_top": s_top, "measured_over_proxy": ratio}
    return {"decision": "REFUTED", "direction": "above" if s_top > hi else "below", "speedup_top": s_top,
            "measured_over_proxy": ratio}


def decide_e6(m22: float, m24: float) -> dict:
    g = math.sqrt(m24 / m22)
    shape = "log-like" if g <= E6_LOG_MAX else ("linear-like" if g >= E6_LIN_MIN else "between")
    return {"decision": shape, "g": g, "median_pcr_ms_2e22": m22, "median_pcr_ms_2e24": m24}


def decide_e8(ratios: list, ks: list) -> dict:
    lo, hi = E8_BAND
    holds = all(lo <= r <= hi for r in ratios)
    return {"decision": "HOLDS" if holds else "FAILS",
            "label": None if holds else "batched solve changes one system's latency",
            "ratios": list(ratios), "K": list(ks), "throughput_factor": [k / r for k, r in zip(ks, ratios)]}


def decide_e9(cus: list, pcr: list) -> dict:
    return {"decision": "REPORTED", "median_cusparse_ms": list(cus), "median_pcr_ms": list(pcr),
            "pcr_over_cusparse": [p / c for p, c in zip(pcr, cus)]}


def decide_e10(hours: float) -> dict:
    lo, hi = E10_BAND
    if lo <= hours <= hi:
        return {"decision": "HOLDS", "direction": None, "hours": hours}
    if hours < lo:
        return {"decision": "REFUTED", "direction": "below: the plan over-bought by more than 3x", "hours": hours}
    return {"decision": "REFUTED", "direction": "above: the plan under-bought", "hours": hours}


def check_timers(sleep_ms: float, event_ms: float, wall_ms: float, blocks: dict) -> dict:
    """blocks: {solver: (R, block_R_ms, block_2R_ms)}."""
    sleep_ok = is_num(sleep_ms) and abs(sleep_ms - TIMER_SLEEP_MS) <= TIMER_SLEEP_TOL_MS
    rel = abs(event_ms - wall_ms) / wall_ms if pos_finite(wall_ms) and is_num(event_ms) else float("inf")
    event_ok = rel <= TIMER_EVENT_TOL
    per = {}
    for solver, (R, b1, b2) in blocks.items():
        ratio = b2 / b1 if pos_finite(b1) and is_num(b2) else float("inf")
        per[solver] = {"R": R, "block_R_ms": b1, "block_2R_ms": b2, "ratio": ratio,
                       "ok": abs(ratio / 2.0 - 1.0) <= TIMER_2R_TOL}
    ok = sleep_ok and event_ok and all(p["ok"] for p in per.values())
    return {"ok": ok, "sleep_ms": sleep_ms, "sleep_ok": sleep_ok, "event_ms": event_ms, "wall_ms": wall_ms,
           
[digest: truncated by the byte cap; showing the first 37395 of 138132 bytes]

=== results_m2/out/records/id-E3_kind-endpoint_run-m2.json (7586 bytes)
{
  "cell": {
    "id": "E3",
    "kind": "endpoint",
    "run": "m2"
  },
  "decision": "if_lever",
  "decision_rule": "speedup(N) = median Thomas ms / median PCR ms over the five seeds. if_lever iff speedup(2^24) >= 2 AND speedup(2^24) > speedup(2^10) AND the least-squares slope of ln(speedup) against log2(N) over the five levels > 0. Otherwise if_not. Label 'within noise' when if_lever and the lower quartile of the per-seed ratio Thomas_ms / PCR_ms at 2^24 is <= 2. NOT_READ if the anchor failed for either.",
  "env": {
    "git_rev": null,
    "host": "150-136-47-224",
    "python": "3.10.12",
    "timestamp_utc": "2026-10-20T09:58:53+00:00"
  },
  "inputs": [
    {
      "bytes": 65392,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/thomas_gpu.jsonl",
      "present": true,
      "sha256": "9d1b8fc1136d"
    },
    {
      "bytes": 70936,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/pcr_gpu.jsonl",
      "present": true,
      "sha256": "f73af1752f60"
    },
    {
      "bytes": 68537,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/cusparse_gpu.jsonl",
      "present": true,
      "sha256": "2ef01011a680"
    },
    {
      "bytes": 68177,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/thomas_batched_gpu.jsonl",
      "present": true,
      "sha256": "39e4178392db"
    },
    {
      "bytes": 62652,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/launch_probe.jsonl",
      "present": true,
      "sha256": "6f8826ec206a"
    },
    {
      "bytes": 70403,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/cpu_dgtsv.jsonl",
      "present": true,
      "sha256": "68cbcae8d816"
    }
  ],
  "metric": "card decision: median one-thread Thomas ms / median PCR ms against the card's rule",
  "notes": "",
  "threshold": {
    "speedup_top_min": 2.0
  },
  "values": {
    "adjacent_decreases": [
      {
        "from_N": 262144,
        "from_speedup": 517.527174941804,
        "to_N": 4194304,
        "to_speedup": 395.38457774438325
      },
      {
        "from_N": 4194304,
        "from_speedup": 395.38457774438325,
        "to_N": 16777216,
        "to_speedup": 348.3049877958905
      }
    ],
    "anchor_failed": [],
    "decision": "if_lever",
    "label": null,
    "labels": {
      "baseline": "baseline: one CUDA thread per system, this build's kernel",
      "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries",
      "budget_left_usd": 6.0,
      "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)",
      "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80",
      "cuda_driver_api_version": "12.8",
      "cuda_runtime_version": "12.8",
      "cuda_runtime_version_runner_library": "12.8",
      "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12",
      "cusparse_available": true,
      "cusparse_note": null,
      "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e",
      "gpu_device_count": 1,
      "gpu_driver": "570.148.08",
      "gpu_memory": "40960 MiB",
      "gpu_name": "NVIDIA A100-SXM4-40GB",
      "instance_type": "gpu_1x_a100_sxm4",
      "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354",
      "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409",
      "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12",
      "mkl_num_threads": "1",
      "numpy_version": "1.26.4",
      "nvcc_arch_flag": "-arch=sm_80",
      "nvcc_path": "/usr/bin/nvcc",
      "nvcc_version": "12.8 (V12.8.93)",
      "omp_num_threads": "1",
      "openblas_num_threads": "1",
      "price_usd_per_hour": 1.99,
      "python_version": "3.10.12",
      "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1",
      "scipy_lapack_libraries": {
        "libblas.so.3": {
          "path": "/lib/x86_64-linux-gnu/libblas.so.3",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"
        },
        "liblapack.so.3": {
          "path": "/lib/x86_64-linux-gnu/liblapack.so.3",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"
        },
        "libopenblas.so.0": {
          "path": "/lib/x86_64-linux-gnu/libopenblas.so.0",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"
        }
      },
      "scipy_version": "1.8.0",
      "vcpu_count": 30
    },
    "launch_fraction_2e10": 0.7751903391337839,
    "launch_fraction_2e24": 0.055114508939160756,
    "lower_quartile_top": 348.28862129983,
    "one_reference_only": false,
    "run_valid": true,
    "slope_ln_speedup_per_log2N": 0.255653691157889,
    "slope_positive": true,
    "speedup_top_above_bottom": true,
    "speedup_top_at_least_2": true,
    "speedups": [
      8.540986788840167,
      95.89943496015222,
      517.527174941804,
      395.38457774438325,
      348.3049877958905
    ],
    "table": [
      {
        "N": 1024,
        "iqr_ratio": 0.0003328336885388694,
        "log2_N": 10,
        "lower_quartile_ratio": 8.540829997336468,
        "median_denominator_ms": 0.03477456059437318,
        "median_numerator_ms": 0.2970090626242632,
        "per_seed_ratio": [
          8.540829997336468,
          8.539319363014531,
          8.541859914107615,
          8.541077064940353,
          8.541162831025007
        ],
        "speedup": 8.540986788840167
      },
      {
        "N": 16384,
        "iqr_ratio": 0.014579352837913007,
        "log2_N": 14,
        "lower_quartile_ratio": 95.8980333535302,
        "median_denominator_ms": 0.05360068278188094,
        "median_numerator_ms": 5.140275192260742,
        "per_seed_ratio": [
          95.92324966335401,
          95.89210640165413,
          95.8980333535302,
          95.90325672570692,
          95.91261270636811
        ],
        "speedup": 95.89943496015222
      },
      {
        "N": 262144,
        "iqr_ratio": 0.29516914560167606,
        "log2_N": 18,
        "lower_quartile_ratio": 517.49463009562,
        "median_denominator_ms": 0.16082188957615903,
        "median_numerator_ms": 83.22969818115234,
        "per_seed_ratio": [
          517.8352815082729,
          517.49463009562,
          517.7897992412217,
          517.527174941804,
          517.4496303648573
        ],
        "speedup": 517.527174941804
      },
      {
        "N": 4194304,
        "iqr_ratio": 0.03164152881277005,
        "log2_N": 22,
        "lower_quartile_ratio": 395.36832393024724,
        "median_denominator_ms": 4.785245028409091,
        "median_numerator_ms": 1892.0120849609375,
        "per_seed_ratio": [
          395.5916729674547,
          395.36832393024724,
          395.39996545906,
          395.3963377302833,
          394.29794894024315
        ],
        "speedup": 395.38457774438325
      },
      {
        "N": 16777216,
        "iqr_ratio": 1.0888978870281676,
        "log2_N": 24,
        "lower_quartile_ratio": 348.28862129983,
        "median_denominator_ms": 21.815638224283855,
        "median_numerator_ms": 7598.49560546875,
        "per_seed_ratio": [
          349.3775191868582,
          348.3142987772109,
          348.28862129983,
          349.63247367676456,
          348.2287110334019
        ],
        "speedup": 348.3049877958905
      }
    ]
  }
}

=== results_m2/out/env.json (1960 bytes)
{
  "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries",
  "budget_left_usd": 6.0,
  "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80",
  "cuda_driver_api_version": "12.8",
  "cuda_runtime_version": "12.8",
  "cuda_runtime_version_runner_library": "12.8",
  "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12",
  "cusparse_available": true,
  "cusparse_note": null,
  "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e",
  "gpu_device_count": 1,
  "gpu_driver": "570.148.08",
  "gpu_memory": "40960 MiB",
  "gpu_name": "NVIDIA A100-SXM4-40GB",
  "instance_type": "gpu_1x_a100_sxm4",
  "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354",
  "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409",
  "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12",
  "mkl_num_threads": "1",
  "numpy_version": "1.26.4",
  "nvcc_arch_flag": "-arch=sm_80",
  "nvcc_path": "/usr/bin/nvcc",
  "nvcc_version": "12.8 (V12.8.93)",
  "omp_num_threads": "1",
  "openblas_num_threads": "1",
  "price_usd_per_hour": 1.99,
  "python_version": "3.10.12",
  "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1",
  "scipy_lapack_libraries": {
    "libblas.so.3": {
      "path": "/lib/x86_64-linux-gnu/libblas.so.3",
      "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"
    },
    "liblapack.so.3": {
      "path": "/lib/x86_64-linux-gnu/liblapack.so.3",
      "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"
    },
    "libopenblas.so.0": {
      "path": "/lib/x86_64-linux-gnu/libopenblas.so.0",
      "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"
    }
  },
  "scipy_version": "1.8.0",
  "vcpu_count": 30
}

=== results_m2/out/m2_summary.json (10927 bytes)
{
  "anchor_failed": [],
  "cusparse_available": true,
  "decisions": {
    "E1": {
      "decision": "PASS",
      "file": "records/id-E1_kind-endpoint_run-m2.json",
      "kind": "endpoint",
      "role": null,
      "run_valid": true
    },
    "E10": {
      "decision": "REFUTED (below: the plan over-bought by more than 3x)",
      "file": "records/id-E10_kind-endpoint_run-m2.json",
      "kind": "endpoint",
      "role": null,
      "run_valid": true
    },
    "E2": {
      "decision": "REFUTED (too pessimistic)",
      "file": "records/id-E2_kind-endpoint_run-m2.json",
      "kind": "endpoint",
      "role": null,
      "run_valid": true
    },
    "E3": {
      "decision": "if_lever",
      "file": "records/id-E3_kind-endpoint_run-m2.json",
      "kind": "endpoint",
      "role": null,
      "run_valid": true
    },
    "E4": {
      "decision": "HOLDS (crossover at 2^10 is launch-bound)",
      "file": "records/id-E4_kind-endpoint_run-m2.json",
      "kind": "endpoint",
      "role": null,
      "run_valid": true
    },
    "E5": {
      "decision": "REFUTED (above, measured / 28 = 12.44)",
      "file": "records/id-E5_kind-endpoint_run-m2.json",
      "kind": "endpoint",
      "role": null,
      "run_valid": true
    },
    "E6": {
      "decision": "linear-like",
      "file": "records/id-E6_kind-endpoint_run-m2.json",
      "kind": "endpoint",
      "role": "report-only; does not decide the card",
      "run_valid": true
    },
    "E7": {
      "decision": "if_lever under the CPU baseline",
      "file": "records/id-E7_kind-endpoint_run-m2.json",
      "kind": "endpoint",
      "role": "report-only; does not decide the card",
      "run_valid": true
    },
    "E8": {
      "decision": "HOLDS",
      "file": "records/id-E8_kind-endpoint_run-m2.json",
      "kind": "endpoint",
      "role": "report-only; does not decide the card",
      "run_valid": true
    },
    "E9": {
      "decision": "REPORTED",
      "file": "records/id-E9_kind-endpoint_run-m2.json",
      "kind": "endpoint",
      "role": "report-only; does not decide the card",
      "run_valid": true
    },
    "I10": {
      "decision": "PASS",
      "file": "records/id-I10_kind-control_run-m2.json",
      "kind": "control",
      "role": null,
      "run_valid": true
    },
    "I1_exact": {
      "decision": "PASS",
      "file": "records/id-I1_exact_kind-control_run-m2.json",
      "kind": "control",
      "role": null,
      "run_valid": true
    },
    "I1_perturbed": {
      "decision": "PASS",
      "file": "records/id-I1_perturbed_kind-control_run-m2.json",
      "kind": "control",
      "role": null,
      "run_valid": true
    },
    "I1_references": {
      "decision": "PASS",
      "file": "records/id-I1_references_kind-control_run-m2.json",
      "kind": "control",
      "role": null,
      "run_valid": true
    },
    "I2": {
      "decision": "PASS",
      "file": "records/id-I2_kind-control_run-m2.json",
      "kind": "control",
      "role": null,
      "run_valid": true
    },
    "I3": {
      "decision": "PASS",
      "file": "records/id-I3_kind-control_run-m2.json",
      "kind": "control",
      "role": null,
      "run_valid": true
    },
    "I4": {
      "decision": "PASS",
      "file": "records/id-I4_kind-control_run-m2.json",
      "kind": "control",
      "role": null,
      "run_valid": true
    },
    "I5": {
      "decision": "PASS",
      "file": "records/id-I5_kind-control_run-m2.json",
      "kind": "control",
      "role": null,
      "run_valid": true
    },
    "I6": {
      "decision": "PASS",
      "file": "records/id-I6_kind-control_run-m2.json",
      "kind": "control",
      "role": null,
      "run_valid": true
    },
    "I7": {
      "decision": "PASS",
      "file": "records/id-I7_kind-control_run-m2.json",
      "kind": "control",
      "role": null,
      "run_valid": true
    },
    "I8": {
      "decision": "PASS",
      "file": "records/id-I8_kind-control_run-m2.json",
      "kind": "control",
      "role": null,
      "run_valid": true
    },
    "I9": {
      "decision": "PASS",
      "file": "records/id-I9_kind-control_run-m2.json",
      "kind": "control",
      "role": null,
      "run_valid": true
    },
    "cpu_dgtsv": {
      "decision": "MEASURED",
      "file": "records/id-cpu_dgtsv_kind-arm_run-m2.json",
      "kind": "arm",
      "role": null,
      "run_valid": true
    },
    "cusparse_gpu": {
      "decision": "MEASURED",
      "file": "records/id-cusparse_gpu_kind-arm_run-m2.json",
      "kind": "arm",
      "role": null,
      "run_valid": true
    },
    "dispersion": {
      "decision": "PASS",
      "file": "records/id-dispersion_kind-gate_run-m2.json",
      "kind": "gate",
      "role": null,
      "run_valid": true
    },
    "gate_propagation": {
      "decision": "PASS",
      "file": "records/id-gate_propagation_kind-control_run-m2.json",
      "kind": "control",
      "role": null,
      "run_valid": true
    },
    "gpu_check": {
      "decision": "PASS",
      "file": "records/id-gpu_check_kind-gate_run-m2.json",
      "kind": "gate",
      "role": null,
      "run_valid": true
    },
    "launch_probe": {
      "decision": "MEASURED",
      "file": "records/id-launch_probe_kind-arm_run-m2.json",
      "kind": "arm",
      "role": null,
      "run_valid": true
    },
    "pcr_gpu": {
      "decision": "MEASURED",
      "file": "records/id-pcr_gpu_kind-arm_run-m2.json",
      "kind": "arm",
      "role": null,
      "run_valid": true
    },
    "residual_sweep": {
      "decision": "REPORTED",
      "file": "records/id-residual_sweep_kind-report_run-m2.json",
      "kind": "report",
      "role": "report-only; does not decide the card",
      "run_valid": true
    },
    "thomas_batched_gpu": {
      "decision": "MEASURED",
      "file": "records/id-thomas_batched_gpu_kind-arm_run-m2.json",
      "kind": "arm",
      "role": null,
      "run_valid": true
    },
    "thomas_gpu": {
      "decision": "MEASURED",
      "file": "records/id-thomas_gpu_kind-arm_run-m2.json",
      "kind": "arm",
      "role": null,
      "run_valid": true
    },
    "timers": {
      "decision": "PASS",
      "file": "records/id-timers_kind-control_run-m2.json",
      "kind": "control",
      "role": null,
      "run_valid": true
    },
    "timing_rows_check": {
      "decision": "PASS",
      "file": "records/id-timing_rows_check_kind-detector_run-m2.json",
      "kind": "detector",
      "role": null,
      "run_valid": true
    },
    "toolchain": {
      "decision": "PASS",
      "file": "records/id-toolchain_kind-gate_run-m2.json",
      "kind": "gate",
      "role": null,
      "run_valid": true
    }
  },
  "exit_code": 0,
  "labels": {
    "baseline": "baseline: one CUDA thread per system, this build's kernel",
    "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries",
    "budget_left_usd": 6.0,
    "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)",
    "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80",
    "cuda_driver_api_version": "12.8",
    "cuda_runtime_version": "12.8",
    "cuda_runtime_version_runner_library": "12.8",
    "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12",
    "cusparse_available": true,
    "cusparse_note": null,
    "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e",
    "gpu_device_count": 1,
    "gpu_driver": "570.148.08",
    "gpu_memory": "40960 MiB",
    "gpu_name": "NVIDIA A100-SXM4-40GB",
    "instance_type": "gpu_1x_a100_sxm4",
    "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354",
    "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409",
    "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12",
    "mkl_num_threads": "1",
    "numpy_version": "1.26.4",
    "nvcc_arch_flag": "-arch=sm_80",
    "nvcc_path": "/usr/bin/nvcc",
    "nvcc_version": "12.8 (V12.8.93)",
    "omp_num_threads": "1",
    "openblas_num_threads": "1",
    "price_usd_per_hour": 1.99,
    "python_version": "3.10.12",
    "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1",
    "scipy_lapack_libraries": {
      "libblas.so.3": {
        "path": "/lib/x86_64-linux-gnu/libblas.so.3",
        "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"
      },
      "liblapack.so.3": {
        "path": "/lib/x86_64-linux-gnu/liblapack.so.3",
        "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"
      },
      "libopenblas.so.0": {
        "path": "/lib/x86_64-linux-gnu/libopenblas.so.0",
        "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"
      }
    },
    "scipy_version": "1.8.0",
    "vcpu_count": 30
  },
  "note": "Restates the records under records/ and decides nothing. The five seeds are five different generated systems timed on one box, not separate boxes.",
  "one_reference_only": false,
  "records_missing": [],
  "records_unreadable": [],
  "run": "m2",
  "run_valid": true,
  "stages": [
    {
      "cap_s": 3482,
      "end_utc": 1792489903,
      "rc": 0,
      "stage": "build",
      "start_utc": 1792489901
    },
    {
      "cap_s": 3480,
      "end_utc": 1792489903,
      "rc": 0,
      "stage": "gpucheck",
      "start_utc": 1792489903
    },
    {
      "cap_s": 3480,
      "end_utc": 1792489904,
      "rc": 0,
      "stage": "anchor",
      "start_utc": 1792489904
    },
    {
      "cap_s": 3479,
      "end_utc": 1792489905,
      "rc": 0,
      "stage": "timers",
      "start_utc": 1792489905
    },
    {
      "cap_s": 3477,
      "end_utc": 1792489969,
      "rc": 0,
      "stage": "residual_sweep",
      "start_utc": 1792489906
    },
    {
      "cap_s": 3414,
      "end_utc": 1792490124,
      "rc": 0,
      "stage": "thomas_gpu",
      "start_utc": 1792489969
    },
    {
      "cap_s": 3259,
      "end_utc": 1792490136,
      "rc": 0,
      "stage": "pcr_gpu",
      "start_utc": 1792490124
    },
    {
      "cap_s": 3247,
      "end_utc": 1792490148,
      "rc": 0,
      "stage": "cusparse_gpu",
      "start_utc": 1792490136
    },
    {
      "cap_s": 3235,
      "end_utc": 1792490311,
      "rc": 0,
      "stage": "thomas_batched_gpu",
      "start_utc": 1792490148
    },
    {
      "cap_s": 3072,
      "end_utc": 1792490313,
      "rc": 0,
      "stage": "launch_probe",
      "start_utc": 1792490311
    },
    {
      "cap_s": 3070,
      "end_utc": 1792490333,
      "rc": 0,
      "stage": "cpu_dgtsv",
      "start_utc": 1792490313
    },
    {
      "cap_s": 3050,
      "end_utc": 1792490333,
      "rc": 0,
      "stage": "endpoints",
      "start_utc": 1792490333
    }
  ],
  "stop_reason": "all stages ran",
  "voids": [],
  "written_utc": 1792490333.4952939
}

=== results_m2/out/records/id-E1_kind-endpoint_run-m2.json (10390 bytes)
{
  "cell": {
    "id": "E1",
    "kind": "endpoint",
    "run": "m2"
  },
  "decision": "PASS",
  "decision_rule": "Thomas and PCR at N = 2^10 and 2^14, seed 0: each relative residual <= 1e-10 AND each relative difference against cuSPARSE and against scipy < 1e-8. A solver out of band: its timing rows are labelled 'descriptive only; anchor failed' and E3, E4, E5 are NOT_READ; the box continues. cuSPARSE against scipy >= 1e-8: run_valid false in every record written after. cuSPARSE missing: read against scipy alone, label 'one reference only'.",
  "env": {
    "git_rev": null,
    "host": "150-136-47-224",
    "python": "3.10.12",
    "timestamp_utc": "2026-10-20T09:51:44+00:00"
  },
  "inputs": [
    {
      "bytes": 1520035,
      "n_items": 11,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/anchor.jsonl",
      "present": true,
      "sha256": "8c76cef1539a"
    }
  ],
  "metric": "anchor: relative residuals of Thomas and PCR at N = 2^10 and 2^14 (seed 0); relative differences against cuSPARSE gtsv2_nopivot and scipy solve_banded; difference between the two references",
  "notes": "",
  "rows": [
    {
      "N": 1024,
      "degenerate": null,
      "diff_vs_cusparse": 2.5657932166359355e-16,
      "diff_vs_scipy": 7.949111607269157e-17,
      "kind": "anchor",
      "rel_residual": 1.352419586054903e-16,
      "seed": 0,
      "solver": "thomas",
      "t_end_utc": 1792489904.6011431,
      "t_start_utc": 1792489904.6005583,
      "x_fingerprint": {
        "first8": [
          0.08522333088208299,
          0.048156852381544026,
          -0.03763953773685444,
          -0.3307052090052367,
          -0.4116817869620112,
          -0.5147866782426658,
          -0.1762325938842892,
          -0.21132475572451714
        ],
        "n": 1024,
        "sha256": "78a3d17958b95660b4c095b6b8f32a992806a31608be64c8256368b1d30e4e3a"
      }
    },
    {
      "N": 1024,
      "degenerate": null,
      "diff_vs_cusparse": 9.034444860840711e-17,
      "diff_vs_scipy": 2.5404249849633584e-16,
      "kind": "anchor",
      "rel_residual": 3.014787708299566e-16,
      "seed": 0,
      "solver": "pcr",
      "t_end_utc": 1792489904.601268,
      "t_start_utc": 1792489904.6011436,
      "x_fingerprint": {
        "first8": [
          0.085223330882083,
          0.048156852381544026,
          -0.037639537736854425,
          -0.33070520900523664,
          -0.4116817869620111,
          -0.5147866782426658,
          -0.17623259388428922,
          -0.21132475572451717
        ],
        "n": 1024,
        "sha256": "56720bab9104481a3f652ae3fe9cc520f336ae5decabe8836d9994b005a8da5a"
      }
    },
    {
      "N": 1024,
      "degenerate": null,
      "diff_vs_scipy": 2.572594775330545e-16,
      "kind": "anchor",
      "rel_residual": 3.1510667266027875e-16,
      "seed": 0,
      "solver": "cusparse",
      "t_end_utc": 1792489904.6013799,
      "t_start_utc": 1792489904.6012862,
      "x_fingerprint": {
        "first8": [
          0.085223330882083,
          0.048156852381544026,
          -0.037639537736854425,
          -0.33070520900523664,
          -0.41168178696201113,
          -0.5147866782426658,
          -0.17623259388428922,
          -0.2113247557245172
        ],
        "n": 1024,
        "sha256": "95de5715cf9c30525f9cbc420bb273e15e74bce9181975131f0627c279534a76"
      }
    },
    {
      "N": 1024,
      "degenerate": null,
      "kind": "anchor",
      "rel_residual": 1.3354207769300864e-16,
      "seed": 0,
      "solver": "scipy",
      "t_end_utc": 1792489904.6016684,
      "t_start_utc": 1792489904.6015193,
      "x_fingerprint": {
        "first8": [
          0.08522333088208299,
          0.048156852381544026,
          -0.03763953773685444,
          -0.3307052090052367,
          -0.4116817869620112,
          -0.5147866782426658,
          -0.1762325938842892,
          -0.21132475572451714
        ],
        "n": 1024,
        "sha256": "34cd0c56d991369e11966467a9d622933ab48d4a5ff13542be9713c6f74a0652"
      }
    },
    {
      "N": 16384,
      "degenerate": null,
      "diff_vs_cusparse": 1.7724666991054108e-16,
      "diff_vs_scipy": 6.870519549925801e-17,
      "kind": "anchor",
      "rel_residual": 1.3875747603982332e-16,
      "seed": 0,
      "solver": "thomas",
      "t_end_utc": 1792489904.6156049,
      "t_start_utc": 1792489904.6082485,
      "x_fingerprint": {
        "first8": [
          -0.08906676947669871,
          0.061783737108314835,
          -0.15546210319029938,
          0.0570803244437967,
          0.3566224074537998,
          0.24799314517492102,
          0.2122447247849357,
          -0.2026368313658215
        ],
        "n": 16384,
        "sha256": "84422db7deeeecc7117ddc1f834c116eb159cefc4fb3067e60da03a925c6efd1"
      }
    },
    {
      "N": 16384,
      "degenerate": null,
      "diff_vs_cusparse": 2.28888649357753e-16,
      "diff_vs_scipy": 2.5431470690674916e-16,
      "kind": "anchor",
      "rel_residual": 3.1109912540540033e-16,
      "seed": 0,
      "solver": "pcr",
      "t_end_utc": 1792489904.6158113,
      "t_start_utc": 1792489904.6156056,
      "x_fingerprint": {
        "first8": [
          -0.0890667694766987,
          0.06178373710831483,
          -0.15546210319029938,
          0.0570803244437967,
          0.35662240745379975,
          0.247993145174921,
          0.21224472478493578,
          -0.20263683136582147
        ],
        "n": 16384,
        "sha256": "1580cdd60b57d989a7d69f9264d153f08a44c25d6892ce8f7a384dd21cdd617c"
      }
    },
    {
      "N": 16384,
      "degenerate": null,
      "diff_vs_scipy": 1.7925627142002788e-16,
      "kind": "anchor",
      "rel_residual": 1.6170978296548225e-16,
      "seed": 0,
      "solver": "cusparse",
      "t_end_utc": 1792489904.6162431,
      "t_start_utc": 1792489904.6159394,
      "x_fingerprint": {
        "first8": [
          -0.08906676947669871,
          0.06178373710831483,
          -0.15546210319029938,
          0.057080324443796716,
          0.3566224074537998,
          0.24799314517492105,
          0.21224472478493572,
          -0.20263683136582147
        ],
        "n": 16384,
        "sha256": "24f049ac16f5523b832acc1ef7ca36907947445129a78a916d46668b24461287"
      }
    },
    {
      "N": 16384,
      "degenerate": null,
      "kind": "anchor",
      "rel_residual": 1.407813698395702e-16,
      "seed": 0,
      "solver": "scipy",
      "t_end_utc": 1792489904.6175349,
      "t_start_utc": 1792489904.6164596,
      "x_fingerprint": {
        "first8": [
          -0.08906676947669871,
          0.061783737108314835,
          -0.15546210319029938,
          0.0570803244437967,
          0.3566224074537998,
          0.24799314517492108,
          0.2122447247849357,
          -0.2026368313658215
        ],
        "n": 16384,
        "sha256": "34e0eb235b512e5b26b850bc5a628dff00fcb8299d18335e6bde6977383e2c32"
      }
    }
  ],
  "threshold": {
    "difference_max_exclusive": 1e-08,
    "residual_max": 1e-10
  },
  "values": {
    "anchor_failed": [],
    "labels": {
      "baseline": "baseline: one CUDA thread per system, this build's kernel",
      "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries",
      "budget_left_usd": 6.0,
      "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)",
      "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80",
      "cuda_driver_api_version": "12.8",
      "cuda_runtime_version": "12.8",
      "cuda_runtime_version_runner_library": "12.8",
      "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12",
      "cusparse_available": true,
      "cusparse_note": null,
      "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e",
      "gpu_device_count": 1,
      "gpu_driver": "570.148.08",
      "gpu_memory": "40960 MiB",
      "gpu_name": "NVIDIA A100-SXM4-40GB",
      "instance_type": "gpu_1x_a100_sxm4",
      "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354",
      "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409",
      "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12",
      "mkl_num_threads": "1",
      "numpy_version": "1.26.4",
      "nvcc_arch_flag": "-arch=sm_80",
      "nvcc_path": "/usr/bin/nvcc",
      "nvcc_version": "12.8 (V12.8.93)",
      "omp_num_threads": "1",
      "openblas_num_threads": "1",
      "price_usd_per_hour": 1.99,
      "python_version": "3.10.12",
      "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1",
      "scipy_lapack_libraries": {
        "libblas.so.3": {
          "path": "/lib/x86_64-linux-gnu/libblas.so.3",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"
        },
        "liblapack.so.3": {
          "path": "/lib/x86_64-linux-gnu/liblapack.so.3",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"
        },
        "libopenblas.so.0": {
          "path": "/lib/x86_64-linux-gnu/libopenblas.so.0",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"
        }
      },
      "scipy_version": "1.8.0",
      "vcpu_count": 30
    },
    "levels": [
      {
        "N": 1024,
        "pcr": {
          "diff_cusparse": 9.034444860840711e-17,
          "diff_scipy": 2.5404249849633584e-16,
          "res": 3.014787708299566e-16
        },
        "ref_diff": 2.572594775330545e-16,
        "thomas": {
          "diff_cusparse": 2.5657932166359355e-16,
          "diff_scipy": 7.949111607269157e-17,
          "res": 1.352419586054903e-16
        }
      },
      {
        "N": 16384,
        "pcr": {
          "diff_cusparse": 2.28888649357753e-16,
          "diff_scipy": 2.5431470690674916e-16,
          "res": 3.1109912540540033e-16
        },
        "ref_diff": 1.7925627142002788e-16,
        "thomas": {
          "diff_cusparse": 1.7724666991054108e-16,
          "diff_scipy": 6.870519549925801e-17,
          "res": 1.3875747603982332e-16
        }
      }
    ],
    "one_reference_only": false,
    "reasons": [],
    "references_agree": true,
    "run_valid": true,
    "solver_ok": {
      "pcr": true,
      "thomas": true
    }
  }
}

=== results_m2/out/records/id-I1_exact_kind-control_run-m2.json (3183 bytes)
{
  "cell": {
    "id": "I1_exact",
    "kind": "control",
    "run": "m2"
  },
  "decision": "PASS",
  "decision_rule": "x* = ones at N = 2^10, seed 0, d = A x*. The residual readout of x* itself must be <= 1e-14. Otherwise FAIL and run_valid false.",
  "env": {
    "git_rev": null,
    "host": "150-136-47-224",
    "python": "3.10.12",
    "timestamp_utc": "2026-10-20T09:51:44+00:00"
  },
  "inputs": [
    {
      "bytes": 32088,
      "n_items": 3,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/anchor.jsonl",
      "present": true,
      "sha256": "41ef4cba7b4f"
    }
  ],
  "metric": "residual readout of the exact solution x* = ones (d = A x*)",
  "notes": "",
  "threshold": {
    "max": 1e-14
  },
  "values": {
    "N": 1024,
    "anchor_failed": [],
    "labels": {
      "baseline": "baseline: one CUDA thread per system, this build's kernel",
      "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries",
      "budget_left_usd": 6.0,
      "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)",
      "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80",
      "cuda_driver_api_version": "12.8",
      "cuda_runtime_version": "12.8",
      "cuda_runtime_version_runner_library": "12.8",
      "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12",
      "cusparse_available": true,
      "cusparse_note": null,
      "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e",
      "gpu_device_count": 1,
      "gpu_driver": "570.148.08",
      "gpu_memory": "40960 MiB",
      "gpu_name": "NVIDIA A100-SXM4-40GB",
      "instance_type": "gpu_1x_a100_sxm4",
      "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354",
      "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409",
      "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12",
      "mkl_num_threads": "1",
      "numpy_version": "1.26.4",
      "nvcc_arch_flag": "-arch=sm_80",
      "nvcc_path": "/usr/bin/nvcc",
      "nvcc_version": "12.8 (V12.8.93)",
      "omp_num_threads": "1",
      "openblas_num_threads": "1",
      "price_usd_per_hour": 1.99,
      "python_version": "3.10.12",
      "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1",
      "scipy_lapack_libraries": {
        "libblas.so.3": {
          "path": "/lib/x86_64-linux-gnu/libblas.so.3",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"
        },
        "liblapack.so.3": {
          "path": "/lib/x86_64-linux-gnu/liblapack.so.3",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"
        },
        "libopenblas.so.0": {
          "path": "/lib/x86_64-linux-gnu/libopenblas.so.0",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"
        }
      },
      "scipy_version": "1.8.0",
      "vcpu_count": 30
    },
    "one_reference_only": false,
    "rel_residual": 0.0,
    "run_valid": true,
    "seed": 0
  }
}

=== results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json (3228 bytes)
{
  "cell": {
    "id": "I1_perturbed",
    "kind": "control",
    "run": "m2"
  },
  "decision": "PASS",
  "decision_rule": "x* perturbed by 1e-6 relative (alternating signs). The residual readout must lie in [1e-7, 1e-5]. Otherwise FAIL and run_valid false.",
  "env": {
    "git_rev": null,
    "host": "150-136-47-224",
    "python": "3.10.12",
    "timestamp_utc": "2026-10-20T09:51:44+00:00"
  },
  "inputs": [
    {
      "bytes": 32088,
      "n_items": 3,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/anchor.jsonl",
      "present": true,
      "sha256": "41ef4cba7b4f"
    }
  ],
  "metric": "residual readout of x* perturbed by 1e-6 relative",
  "notes": "",
  "threshold": {
    "band": [
      1e-07,
      1e-05
    ]
  },
  "values": {
    "N": 1024,
    "anchor_failed": [],
    "labels": {
      "baseline": "baseline: one CUDA thread per system, this build's kernel",
      "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries",
      "budget_left_usd": 6.0,
      "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)",
      "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80",
      "cuda_driver_api_version": "12.8",
      "cuda_runtime_version": "12.8",
      "cuda_runtime_version_runner_library": "12.8",
      "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12",
      "cusparse_available": true,
      "cusparse_note": null,
      "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e",
      "gpu_device_count": 1,
      "gpu_driver": "570.148.08",
      "gpu_memory": "40960 MiB",
      "gpu_name": "NVIDIA A100-SXM4-40GB",
      "instance_type": "gpu_1x_a100_sxm4",
      "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354",
      "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409",
      "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12",
      "mkl_num_threads": "1",
      "numpy_version": "1.26.4",
      "nvcc_arch_flag": "-arch=sm_80",
      "nvcc_path": "/usr/bin/nvcc",
      "nvcc_version": "12.8 (V12.8.93)",
      "omp_num_threads": "1",
      "openblas_num_threads": "1",
      "price_usd_per_hour": 1.99,
      "python_version": "3.10.12",
      "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1",
      "scipy_lapack_libraries": {
        "libblas.so.3": {
          "path": "/lib/x86_64-linux-gnu/libblas.so.3",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"
        },
        "liblapack.so.3": {
          "path": "/lib/x86_64-linux-gnu/liblapack.so.3",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"
        },
        "libopenblas.so.0": {
          "path": "/lib/x86_64-linux-gnu/libopenblas.so.0",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"
        }
      },
      "scipy_version": "1.8.0",
      "vcpu_count": 30
    },
    "one_reference_only": false,
    "rel_residual": 9.571824604348377e-07,
    "run_valid": true,
    "seed": 0
  }
}

=== SEALED_PREDICTIONS.md (3207 bytes)
# Sealed predictions, measure run m2 (written 2026-10-20 08:5x UTC, before any agent or box ran)

Author: the operating session (Claude). Not shown to the triage, gate, build or post agents. Hash in out/SEALS.txt.

Card under test: P arm, R1 · physical · "Cyclic reduction (PCR)", `expected: if_lever`, decision rule "lever if median
PCR time < median Thomas time at n_max = 2^24 by at least 2x, and the PCR/Thomas speedup grows with N".

| # | Prediction | Probability |
|---|---|---|
| P1 | The box has nvcc (CUDA toolkit) and the kernels compile on the first launch | 0.75 |
| P2 | E1 anchor passes: Thomas and PCR relative residuals <= 1e-10 at N = 2^10 and 2^14 against cuSPARSE and scipy | 0.80 |
| P3 | E2: the card's residual guess 1e-13 is too pessimistic by more than 10x (measured max relative residual below 1e-14) | 0.65 |
| P4 | E3: the card's decision rule resolves if_lever (PCR >= 2x faster than the one-thread GPU Thomas at 2^24, speedup growing with N) | 0.95 |
| P5 | E5: PCR/Thomas speedup at 2^24 is at least 28 (the card's proxy). Point estimate 150x, range 30 to 1,000x | 0.85 |
| P6 | E4: crossover at the first level: PCR already beats one-thread GPU Thomas at N = 1,024 (card guess holds) | 0.75 |
| P7 | E7: against the CPU LAPACK dgtsv floor at N = 2^24, PCR's speedup is below 20x | 0.70 |
| P7b | ... and below 2x (the card's own threshold would say if_not against that baseline) | 0.20 |
| P8 | E6: PCR wall-clock is not log-like at the top: per-doubling growth between 2^22 and 2^24 is at least 1.7x (work-bound, not depth-bound) | 0.80 |
| P9 | E10: the whole on-box sweep (anchor plus all levels) takes under 20 minutes; the card's "need 2 h" is high by more than 3x | 0.80 |
| P10 | E9: the hand-written PCR is within 3x of cuSPARSE gtsv2_nopivot at 2^24 | 0.55 |
| P11 | The run completes its first launch with no halt | 0.50 |

## Reasoning, in one paragraph

The card's baseline is one CUDA thread walking 2^24 dependent steps twice; at a few hundred cycles per step that is
seconds per solve. PCR touches all N equations in each of its 24 rounds, so on one GPU its time is bandwidth-bound:
tens of milliseconds at 2^24. The ratio is therefore large, and the card's rule is near-certain to say if_lever;
the rule cannot easily fail because its baseline is the slowest possible sequential arrangement, not the practical
one (a CPU core running LAPACK dgtsv, about 0.1 s at 2^24). The interesting measured facts are elsewhere: PCR's time
grows about linearly with N at the top (depth is log N but work is N log N and the GPU's width is finite), which
contradicts the card's if_lever prose "wall-clock grows like log2(N)" even while the decision rule holds; and the CPU
floor shows what the restructure buys against the sequential alternative anyone would use.

## What would change my mind

P4 fails only if the Thomas kernel is written as something other than one thread per system. P8 fails if the GPU is
far from saturated at 2^22 (it is not: 4 million threads per round). P7 fails if dgtsv on the box's CPU is slow (an
old MKL-less LAPACK at over 1 s for 2^24 would push PCR past 20x). P1 is the P9 analogue from m1: a toolchain
assumption about the Lambda image.


=== out/PREDICTIONS_SCORED.md (2716 bytes)
# Sealed predictions scored, measure run m2

Sealed before any agent ran: `SEALED_PREDICTIONS.md` sha256 169bb51e31dc9c25d2ae76a6c21e153f8c2522b9b46edceb8dde4df15c58032e
(out/SEALS.txt, first line). Scored against `results_m2/out/records/` and `results_m2/out/rows/` on 2026-10-20 10:05Z.
"Held" = the predicted event occurred; "did not occur" = it did not (a low forecast that did not occur is a good forecast).

| # | Prediction | p | Outcome | Measured | Brier term |
|---|---|---|---|---|---|
| P1 | nvcc present, kernels compile on launch 1 | 0.75 | held | /usr/bin/nvcc 12.8, compiled in 2 s with -arch=sm_80 | 0.0625 |
| P2 | E1 anchor passes (residuals <= 1e-10, references agree) | 0.80 | held | E1 PASS; I1 x3 PASS | 0.0400 |
| P3 | E2: card residual guess 1e-13 too pessimistic by > 10x | 0.65 | held | max relative residual 3.11e-16 (320x below the guess) | 0.1225 |
| P4 | E3 resolves if_lever by the card's rule | 0.95 | held | speedups 8.5 / 95.9 / 517.5 / 395.4 / 348.3; slope of ln(speedup) 0.256 > 0 | 0.0025 |
| P5 | E5: speedup at 2^24 >= 28 (point 150, range 30 to 1,000) | 0.85 | held | 348.3x (12.4x the card's proxy) | 0.0225 |
| P6 | E4: crossover at N = 1,024 | 0.75 | held | 1,024, labelled launch-bound (launch fraction 0.775 at 2^10) | 0.0625 |
| P7 | E7: PCR vs CPU dgtsv at 2^24 below 20x | 0.70 | held, thin | 416.7 ms / 21.8 ms = 19.1x | 0.0900 |
| P7b | ... below 2x | 0.20 | did not occur | 19.1x | 0.0400 |
| P8 | E6: PCR per-doubling growth 2^22 -> 2^24 at least 1.7x | 0.80 | held | g = 2.135 (4.79 ms -> 21.8 ms for 4x N): super-linear, "linear-like" | 0.0400 |
| P9 | E10: sweep under 20 min; "need 2 h" high by > 3x | 0.80 | held | 0.119 h = 7.1 min; 16.8x below the card's need | 0.0400 |
| P10 | E9: this PCR within 3x of cuSPARSE gtsv2_nopivot at 2^24 | 0.55 | did not occur | cuSPARSE 2.94 ms vs PCR 21.8 ms: 7.4x | 0.3025 |
| P11 | first launch completes with no halt | 0.50 | held | rc=0, 12 stages, 35 records, run_valid true | 0.2500 |

**Brier score: 1.075 / 12 = 0.090** (m1: 0.177). Twelve resolved, none unresolved.

## Where the forecast was weakest

- P10: the hand-written PCR is 7.4x slower than NVIDIA's hybrid at the top level and 2.4x at the bottom. The one-kernel-per-round
  PCR over global memory is far from the library's shared-memory hybrid; the card's E3 speedup is against the card's own
  baseline and would be about 2,580x with cuSPARSE as the parallel arm.
- P11 and P1: the toolchain risk did not materialise this time (nvcc, scipy, cuSPARSE all on the image).
- P7 held by 0.9x of margin: the practical sequential floor (one CPU core, OpenBLAS LAPACK dgtsv) is 19x slower than this PCR at
  2^24, 0.6x at 2^10 (the CPU wins below about 2^12).


=== results_m2/out/records/id-E7_kind-endpoint_run-m2.json (7279 bytes)
{
  "cell": {
    "id": "E7",
    "kind": "endpoint",
    "run": "m2"
  },
  "decision": "if_lever under the CPU baseline",
  "decision_rule": "E3's rule with median scipy dgtsv ms on one CPU core in place of the one-thread GPU Thomas ms. if_lever or if_not under that baseline, speedup at every level. Report only.",
  "env": {
    "git_rev": null,
    "host": "150-136-47-224",
    "python": "3.10.12",
    "timestamp_utc": "2026-10-20T09:58:53+00:00"
  },
  "inputs": [
    {
      "bytes": 65392,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/thomas_gpu.jsonl",
      "present": true,
      "sha256": "9d1b8fc1136d"
    },
    {
      "bytes": 70936,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/pcr_gpu.jsonl",
      "present": true,
      "sha256": "f73af1752f60"
    },
    {
      "bytes": 68537,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/cusparse_gpu.jsonl",
      "present": true,
      "sha256": "2ef01011a680"
    },
    {
      "bytes": 68177,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/thomas_batched_gpu.jsonl",
      "present": true,
      "sha256": "39e4178392db"
    },
    {
      "bytes": 62652,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/launch_probe.jsonl",
      "present": true,
      "sha256": "6f8826ec206a"
    },
    {
      "bytes": 70403,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/cpu_dgtsv.jsonl",
      "present": true,
      "sha256": "68cbcae8d816"
    }
  ],
  "metric": "CPU floor: the card's rule with median one-core scipy dgtsv ms in place of Thomas ms",
  "notes": "",
  "threshold": {
    "speedup_top_min": 2.0
  },
  "values": {
    "adjacent_decreases": [
      {
        "from_N": 262144,
        "from_speedup": 30.708453671787385,
        "to_N": 4194304,
        "to_speedup": 18.411710053908486
      }
    ],
    "anchor_failed": [],
    "decision": "if_lever",
    "label": null,
    "labels": {
      "baseline": "baseline: one CUDA thread per system, this build's kernel",
      "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries",
      "budget_left_usd": 6.0,
      "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)",
      "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80",
      "cuda_driver_api_version": "12.8",
      "cuda_runtime_version": "12.8",
      "cuda_runtime_version_runner_library": "12.8",
      "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12",
      "cusparse_available": true,
      "cusparse_note": null,
      "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e",
      "gpu_device_count": 1,
      "gpu_driver": "570.148.08",
      "gpu_memory": "40960 MiB",
      "gpu_name": "NVIDIA A100-SXM4-40GB",
      "instance_type": "gpu_1x_a100_sxm4",
      "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354",
      "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409",
      "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12",
      "mkl_num_threads": "1",
      "numpy_version": "1.26.4",
      "nvcc_arch_flag": "-arch=sm_80",
      "nvcc_path": "/usr/bin/nvcc",
      "nvcc_version": "12.8 (V12.8.93)",
      "omp_num_threads": "1",
      "openblas_num_threads": "1",
      "price_usd_per_hour": 1.99,
      "python_version": "3.10.12",
      "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1",
      "scipy_lapack_libraries": {
        "libblas.so.3": {
          "path": "/lib/x86_64-linux-gnu/libblas.so.3",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"
        },
        "liblapack.so.3": {
          "path": "/lib/x86_64-linux-gnu/liblapack.so.3",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"
        },
        "libopenblas.so.0": {
          "path": "/lib/x86_64-linux-gnu/libopenblas.so.0",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"
        }
      },
      "scipy_version": "1.8.0",
      "vcpu_count": 30
    },
    "lower_quartile_top": 17.152781190036713,
    "one_reference_only": false,
    "pcr_anchor_status": "anchor passed",
    "role": "report-only; does not decide the card",
    "run_valid": true,
    "slope_ln_speedup_per_log2N": 0.23437177893098576,
    "slope_positive": true,
    "speedup_top_above_bottom": true,
    "speedup_top_at_least_2": true,
    "speedups": [
      0.5907048648185403,
      5.782147180309478,
      30.708453671787385,
      18.411710053908486,
      19.102597490644076
    ],
    "table": [
      {
        "N": 1024,
        "iqr_ratio": 0.0008974235938574715,
        "log2_N": 10,
        "lower_quartile_ratio": 0.5903024254890288,
        "median_denominator_ms": 0.03477456059437318,
        "median_numerator_ms": 0.020541502115023348,
        "per_seed_ratio": [
          0.5924345157147046,
          0.5903024254890288,
          0.5911998490828863,
          0.5907228023954774,
          0.5901755907826257
        ],
        "speedup": 0.5907048648185403
      },
      {
        "N": 16384,
        "iqr_ratio": 0.002074014488173681,
        "log2_N": 14,
        "lower_quartile_ratio": 5.782941717505204,
        "median_denominator_ms": 0.05360068278188094,
        "median_numerator_ms": 0.3099270368099156,
        "per_seed_ratio": [
          5.783399710225969,
          5.834085208857459,
          5.7850157319933775,
          5.781277244249244,
          5.782941717505204
        ],
        "speedup": 5.782147180309478
      },
      {
        "N": 262144,
        "iqr_ratio": 0.017610273806958787,
        "log2_N": 18,
        "lower_quartile_ratio": 30.705671938280837,
        "median_denominator_ms": 0.16082188957615903,
        "median_numerator_ms": 4.938591545458786,
        "per_seed_ratio": [
          31.156825542946027,
          30.716092118011897,
          30.723282212087796,
          30.705671938280837,
          30.696690852162988
        ],
        "speedup": 30.708453671787385
      },
      {
        "N": 4194304,
        "iqr_ratio": 2.4453102624551484,
        "log2_N": 22,
        "lower_quartile_ratio": 17.41310421801345,
        "median_denominator_ms": 4.785245028409091,
        "median_numerator_ms": 88.10454399997525,
        "per_seed_ratio": [
          18.422461541792234,
          17.080793275367494,
          19.8584144804686,
          20.458618820726315,
          17.41310421801345
        ],
        "speedup": 18.411710053908486
      },
      {
        "N": 16777216,
        "iqr_ratio": 2.0088788109779827,
        "log2_N": 24,
        "lower_quartile_ratio": 17.152781190036713,
        "median_denominator_ms": 21.815638224283855,
        "median_numerator_ms": 416.7353560000038,
        "per_seed_ratio": [
          19.161660001014695,
          19.14123688278103,
          22.214444717473377,
          17.152781190036713,
          16.970509588819247
        ],
        "speedup": 19.102597490644076
      }
    ]
  }
}

=== results_m2/out/records/id-E9_kind-endpoint_run-m2.json (4733 bytes)
{
  "cell": {
    "id": "E9",
    "kind": "endpoint",
    "run": "m2"
  },
  "decision": "REPORTED",
  "decision_rule": "Median cuSPARSE ms at each level and ratio = median PCR ms / median cuSPARSE ms. Report only.",
  "env": {
    "git_rev": null,
    "host": "150-136-47-224",
    "python": "3.10.12",
    "timestamp_utc": "2026-10-20T09:58:53+00:00"
  },
  "inputs": [
    {
      "bytes": 65392,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/thomas_gpu.jsonl",
      "present": true,
      "sha256": "9d1b8fc1136d"
    },
    {
      "bytes": 70936,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/pcr_gpu.jsonl",
      "present": true,
      "sha256": "f73af1752f60"
    },
    {
      "bytes": 68537,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/cusparse_gpu.jsonl",
      "present": true,
      "sha256": "2ef01011a680"
    },
    {
      "bytes": 68177,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/thomas_batched_gpu.jsonl",
      "present": true,
      "sha256": "39e4178392db"
    },
    {
      "bytes": 62652,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/launch_probe.jsonl",
      "present": true,
      "sha256": "6f8826ec206a"
    },
    {
      "bytes": 70403,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/cpu_dgtsv.jsonl",
      "present": true,
      "sha256": "68cbcae8d816"
    }
  ],
  "metric": "cuSPARSE: median gtsv2_nopivot ms at each level and median PCR ms / median cuSPARSE ms",
  "notes": "",
  "threshold": {},
  "values": {
    "anchor_failed": [],
    "decision": "REPORTED",
    "labels": {
      "baseline": "baseline: one CUDA thread per system, this build's kernel",
      "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries",
      "budget_left_usd": 6.0,
      "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)",
      "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80",
      "cuda_driver_api_version": "12.8",
      "cuda_runtime_version": "12.8",
      "cuda_runtime_version_runner_library": "12.8",
      "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12",
      "cusparse_available": true,
      "cusparse_note": null,
      "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e",
      "gpu_device_count": 1,
      "gpu_driver": "570.148.08",
      "gpu_memory": "40960 MiB",
      "gpu_name": "NVIDIA A100-SXM4-40GB",
      "instance_type": "gpu_1x_a100_sxm4",
      "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354",
      "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409",
      "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12",
      "mkl_num_threads": "1",
      "numpy_version": "1.26.4",
      "nvcc_arch_flag": "-arch=sm_80",
      "nvcc_path": "/usr/bin/nvcc",
      "nvcc_version": "12.8 (V12.8.93)",
      "omp_num_threads": "1",
      "openblas_num_threads": "1",
      "price_usd_per_hour": 1.99,
      "python_version": "3.10.12",
      "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1",
      "scipy_lapack_libraries": {
        "libblas.so.3": {
          "path": "/lib/x86_64-linux-gnu/libblas.so.3",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"
        },
        "liblapack.so.3": {
          "path": "/lib/x86_64-linux-gnu/liblapack.so.3",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"
        },
        "libopenblas.so.0": {
          "path": "/lib/x86_64-linux-gnu/libopenblas.so.0",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"
        }
      },
      "scipy_version": "1.8.0",
      "vcpu_count": 30
    },
    "levels": [
      1024,
      16384,
      262144,
      4194304,
      16777216
    ],
    "median_cusparse_ms": [
      0.01477508544921875,
      0.04902480091580767,
      0.09943578619706003,
      0.7998100403816469,
      2.943216884837431
    ],
    "median_pcr_ms": [
      0.03477456059437318,
      0.05360068278188094,
      0.16082188957615903,
      4.785245028409091,
      21.815638224283855
    ],
    "one_reference_only": false,
    "pcr_anchor_status": "anchor passed",
    "pcr_over_cusparse": [
      2.353594550359228,
      1.093338101952349,
      1.6173441748370665,
      5.982976940531662,
      7.412174867802461
    ],
    "role": "report-only; does not decide the card",
    "run_valid": true
  }
}

=== RUN.md (10627 bytes)
# reshape-test · measure · 20261020-0855

Kind: measure. The decides-by phase (`p2_sweep`, with its anchor `p1_anchor`) of the P arm's physical card, run as a
latent_skeptic run, so the card's own prediction is resolved by a measurement and lands beside the card it came from.
Second measure run in this experiment (first: `../20261020-0145-measure`, m1). Tag: m2.

## Source card

- Run: `../20261019-2344-tree` (arm P, planted root), pick R1 · physical · "Cyclic reduction (PCR) · Parallel cyclic
  reduction". Dramaturg verdict on the card: **REJECT (3 blocking)**, all on citations (the plan's own predictions and
  one literature-gap claim cited to no source); critic reshape 4, baseline 5, lever 5, stakes 3.
- Record: `../20261019-2344-tree/out/result.json` sha256 `48ac464c98a73069aab7af8efbd53021ca5439a193af666a2e1ac6d0d32ac6ae`;
  rendered `../20261019-2344-tree/out/RESULT.md` sha256 `ac1ccd211ff8ebdff09116f2aaaf52063942463b1a0bda6e838bd8fd3ccc1a07`.
- Producer reply (the PLAN): `../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt`
  sha256 `5edcb633490ee446d7a77a8f32cf246efae31aab79919fe6b21ac4f6aa411b33`.
- Prediction under test: `expected: if_lever`, by its own decision rule: "Lever if median PCR time < median Thomas time
  at n_max=2^24 by at least gate_speedup=2x, and the PCR/Thomas speedup grows with N; otherwise not."
- Card numbers measured here: `res_measured` GUESS 1e-13 (`p1_anchor`); `crossover_n` GUESS 1,024 (`p2_sweep`);
  `speedup_at_nmax` PROXY 28 (`p2_sweep`); cost line `l_anchor_sweep` hours 6, need 2 on A100 SXM 40 GB at USD 1.99/h.
- Card gate at `p1_anchor`: `res_measured <= 1e-10`, else "Fix the kernels and re-run the anchor before starting the sweep".

## Adjustments decided by the operator before any agent ran (each is a departure of record; see out/diff.json)

1. **No producer resample before measuring.** The dramaturg's REJECT is about citations for the plan's own predictions
   and a literature-gap sentence. A resample rewrites the PLAN (new numbers, new rule), so the measurement would then
   resolve a card that is not the committed record. The measurement binds to the committed record and carries the label
   "card dramaturg: REJECT (citations)". The if_lever / if_not sentences the dramaturg called unsupported are what this run
   measures.
2. **Hardware as the card states.** `gpu_1x_a100_sxm4` has capacity in us-east-1 at USD 1.99/h (the card's rate and GPU),
   so no instance substitution this time. Rule if capacity vanishes at launch: cheapest single GPU with capacity,
   recorded as a departure.
3. **The CPU floor is measured, report-only.** The card's `baseline_sequential` names "MKL dgtsv on the instance CPU as a
   floor" but gives it no endpoint. It is timed here (scipy's LAPACK dgtsv, preinstalled scipy 1.8.0 on the image) and
   the card's rule is re-read against it as a labelled sensitivity line. The card's verdict is read against its own
   baseline only.
4. **Phases p3 (block) and p4 (multi-GPU) are not run** (optional in the card).
5. **Toolchain rule from m1:** nothing is installed on the box unless missing; preinstalled scipy and system CUDA
   libraries are used; nvcc is looked up on PATH and under /usr/local/cuda*/bin; if absent the run halts cleanly with
   RUN_VALID false (no fallback install).
6. **Two launches pre-authorised within one cap** (m1 needed a gate addendum for its second launch).

## Pipeline

- latent_skeptic at ff9a63c (`../../../dut/latent_skeptic`): `pipeline.js`, `triage_workflow.js`, `gates/` copied here
  read-only and verified byte-identical. Design mode is NOT run: the card is the design. `out/design.json` is the card's
  PLAN compiled by hand into the design-record schema (mapping in QUESTION.md). Triage, gate, build and post run as in
  design mode. `.claude/agents/` role files sit at `/home/hal/dev/interp/.claude/agents/` (present since m1; this
  session predates them, so the isolated reader is expected to fail again; see INTERVENTIONS.md).
- `frozen/` as in m1 (lambda_run.sh, remote_run.sh, provenance.py), adapted only at header-declared points, per launch.
- metis at e7acf90 (uncommitted: m1 folder, this folder, `_meta/LEDGER.jsonl`, `.gitignore`, `reshape-test/QUESTION.md`).
- Hashes of every input: `out/INPUT_HASHES.txt`. Every action by actor: `INTERVENTIONS.md`.

## Budget (owner rules of 2026-10-20)

- Project cap, Lambda: USD 500. Spent before this run: USD 2.12 (m1).
- Calibration and smoke measurements (this kind): fuzzy limit about USD 10 per run, no re-approval.
- Full runs: hard limit, owner approves each spend above USD 20 before launch.
- This run: hard cap USD 8, at most two launches, `gpu_1x_a100_sxm4` at USD 1.99/h; expected 0.3 to 0.6 h per launch.

## Sequence

1. `SEALED_PREDICTIONS.md` written and hashed before any agent runs (`out/SEALS.txt`).
2. Triage: Workflow `triage_workflow.js` on the design-as-claim, as pipeline.js design mode frames it.
3. `out/design_record.json` = {seed, design, diff, triage, gate}; `GATE_COMMIT.md` answers every queued item.
4. Build: Workflow `pipeline.js` mode build, tag m2, conventions frozen/, exec_note EXEC_NOTE.md.
5. Run: per-launch launcher copy; detached via setsid; teardown confirmed through the API.
6. Post: Workflow `pipeline.js` mode post; TAKEAWAYS_m2.md is the answer.
7. Ledger: `../../_meta/LEDGER.jsonl` gets one row: card, prediction, outcome, cost.

Models: every agent pinned in the scripts (sonnet, opus). None on Fable. The operating session is Fable; nothing
unpinned may run.

## Log

- 08:55Z run dir made; pipeline files verified identical to dut ff9a63c; inputs hashed.
- 09:00Z QUESTION.md, out/design.json (10 endpoints), out/diff.json (7 departures) written and hashed. Triage launched.
- 09:02Z triage wf_da9ff4cd-543, 23 s: decidability RULED_OUT (design structure); coordinates/scale NEEDS_RUN (one run-queue item); 10 instrument validations queued. **Deviation:** isolated reader did not run (agent type not found, as in m1). Return: out/triage_wf_da9ff4cd-543_return.json.
- 09:05Z GATE_COMMIT.md and EXEC_NOTE.md written and hashed; build launched.
- 09:45Z build wf_7bcc0b19-df0 returned after 39 min: GateCheck 19 of 19; `run_m2.py` 2,836 lines (46faee5d…), `onbox_m2.sh`
  76 lines (3cfe0f6d…), hashes in `out/BUILT_HASHES.txt`; selftest 115/115 under the operator's own run
  (`out/selftest_m2_operator.log`). Builder choices (a) to (l) in `out/build_m2_wf_7bcc0b19-df0_return.json`, all accepted:
  anchor failure labels rows but does not void the run; -arch=sm_80 on A100; batched arm = K copies of the same (N, seed)
  system laid out one after another; cuSPARSE RHS copies before the block; R from the second warm-up; planted controls
  also run on the box; a cuSPARSE run-time error stops the run (the directive covered only a missing library).
  Builder's wall-clock estimate: 8 to 15 min compute, 20 to 40 min billed, USD 0.7 to 1.3.
- 09:47Z LAUNCH 1 (of at most 2): `PRICE_USD_PER_HOUR=1.99 BUDGET_LEFT_USD=6 INSTANCE_TYPE=gpu_1x_a100_sxm4 REMOTE_TIMEOUT=3600
  setsid nohup bash lambda_run_m2.sh gpu_1x_a100_sxm4 us-east-1 onbox_m2.sh results_m2`, log `out/launcher_m2.log`.
  Known launcher deviation (m1): the start-ssh call blocks until the remote job exits; no poll lines while live.
- 09:54Z progress read on the box (ssh, operator): box 3be4cd7175024dcd8ffa23e50d300409, ip 150.136.47.224; nvcc found at
  /usr/bin/nvcc, compiled with -arch=sm_80 in 2 s; GPU check pass; anchor I1 x3 PASS, E1 PASS, E2 REFUTED (too
  pessimistic); timers pass; residual sweep 63 s; thomas_gpu one-thread: 5.14 ms at 2^14, 83.2 ms at 2^18, 1,892 ms
  at 2^22, 7,598 ms at 2^24 (about 0.45 microseconds per equation, linear). scipy warns NumPy 1.26.4 is newer than
  scipy 1.8.0 supports (image as shipped; recorded).
- 10:00Z LAUNCH 1 DONE rc=0. Launcher: start-ssh blocked until remote exit (as in m1), then DONE marker, summary verified,
  full fetch (try 1), teardown accepted; API: launch 09:46:22Z, terminate 10:00:43Z, 0.239 h, **USD 0.48**. 0 instances.
  Project Lambda total USD 2.60 of 500.
- Records (35, `results_m2/out/records/`), run_valid true, labels "card dramaturg: REJECT (3 blocking, citations)" and
  "baseline: one CUDA thread per system, this build's kernel". Compute on the box 7.1 min (E10 span 0.119 h).
  E1 PASS (max relative residual 3.1e-16; cuSPARSE and scipy agree); E2 REFUTED, too pessimistic (guess 1e-13, 320x);
  E3 **if_lever**: speedups 8.5 / 95.9 / 517.5 / 395.4 / 348.3 at 2^10..2^24, slope 0.256 > 0, lower quartile at the
  top 348; two adjacent decreases above 2^18 (strict reading would fail); E4 HOLDS, crossover 1,024, launch-bound
  (launch fraction 0.775); E5 REFUTED above (348x vs proxy 28, 12.4x); E6 linear-like (g 2.135: PCR 4.79 ms at 2^22,
  21.8 ms at 2^24); E7 if_lever under the CPU floor (dgtsv 416.7 ms at 2^24, 19.1x; CPU faster below about 2^12);
  E8 HOLDS (batched/single 1.05 to 1.81); E9 cuSPARSE 2.94 ms at 2^24, this PCR 7.4x slower; E10 REFUTED below
  (0.119 h vs need 2 h, 16.8x). I1 to I10, timers, gate propagation, dispersion, timing-rows check all PASS.
  One-thread Thomas: 0.297 / 5.14 / 83.2 / 1,892 / 7,598 ms (linear, about 0.45 microseconds per equation).
- Ledger row appended: `../../_meta/LEDGER.jsonl` (row 3). Card write-back: `out/CARD_WRITEBACK_m2.json`. Sealed
  predictions scored: `out/PREDICTIONS_SCORED.md` (Brier 0.090 over 12; held 10, did not occur 2).
- 10:08Z post mode wf_c1d43903-ecc launched (elicit, question triage, TAKEAWAYS_m2.md under the two gates).
- 10:16Z post done (wf_c1d43903-ecc, 39 agents, 7.8 min): GateCheck 19/19; 8 elicited questions; top 3 triaged (reader
  failed 3x, agent type not found; skeptics: q1 baseline artifact EXPLAINS the 12.4x proxy miss, q2 CPU faster at 2^10
  EXPLAINS, q3 host-to-device copy NEEDS_RUN). **Deviation:** the writer put `TAKEAWAYS_m2.md` in the experiment dir
  (`reshape-test/`), not the run dir; moved by the operator (mv, no edit). Gates on the text above the raw-samples
  heading: 1.3 codes/1000 words, 0 unscoped sentences (writer's run; operator's run agrees). The writer satisfied the
  scope gate with 23 `[^1]` footnote markers (its model-naming rule does not fit a solver study): a workaround, recorded.
  Hash in `out/SEALS.txt`.
- Caveats appended to the ledger (row 4). Hashes of all outputs in `out/SEALS.txt`.
- Close: Lambda USD 0.48 (one launch, 0.239 h), 0 instances; project total USD 2.60 of 500. Claude usage: triage 4 agents,
  build 2, post 39 (all sonnet/opus by pin). Operator actions vs pipeline actions: `INTERVENTIONS.md`. Nothing
  committed or pushed.


=== results_m2/out/rows/pcr_gpu.jsonl (70936 bytes)
{"K": 1, "N": 1024, "R": 1253, "anchor_failed": [], "anchor_status": "anchor passed", "arm": "pcr_gpu", "block_at_least_50ms": false, "block_dim": 256, "block_ms": 43.57427215576172, "degenerate": null, "grid": 4, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "launch_fraction": 0.7751592468371377, "launch_fraction_from": "median ms per launch over the launch probe's five rows at this level", "launches_per_solve": 10, "ms_per_launch": 0.002695690342038046, "ms_per_solve": 0.0347759554315736, "one_reference_only": false, "rounds": 10, "run_valid": true, "seed": 0, "t_written_utc": 1792490124.662866, "warmup_ms": [0.19148799777030945, 0.03993599861860275], "x_all_zero": false, "x_finite": true, "x_first8": [0.085223330882083, 0.048156852381544026, -0.037639537736854425, -0.33070520900523664, -0.4116817869620111, -0.5147866782426658, -0.17623259388428922, -0.21132475572451717]}
{"K": 1, "N": 1024, "R": 1221, "anchor_failed": [], "anchor_status": "anchor passed", "arm": "pcr_gpu", "block_at_least_50ms": false, "block_dim": 256, "block_ms": 42.466304779052734, "degenerate": null, "grid": 4, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "launch_fraction": 0.77507047640557, "launch_fraction_from": "median ms per launch over the launch probe's five rows at this level", "launches_per_solve": 10, "ms_per_launch": 0.002695690342038046, "ms_per_solve": 0.034779938393982586, "one_reference_only": false, "rounds": 10, "run_valid": true, "seed": 1, "t_written_utc": 1792490124.7062576, "warmup_ms": [0.04403200000524521, 0.04095999896526337], "x_all_zero": false, "x_finite": true, "x_first8": [0.16725593292084112, 0.5294170791951257, -0.9730753782293168, 0.185633965995893, 0.6995036043326974, -0.20143404993959987, 0.07028685643349918, 0.30273128838611457]}
{"K": 1, "N": 1024, "R": 1320, "anchor_failed": [], "anchor_status": "anchor passed", "arm": "pcr_gpu", "block_at_least_50ms": false, "block_dim": 256, "block_ms": 45.897727966308594, "degenerate": null, "grid": 4, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "launch_fraction": 0.7752695850439945, "launch_fraction_from": "median ms per launch over the launch probe's five rows at this level", "launches_per_solve": 10, "ms_per_launch": 0.002695690342038046, "ms_per_solve": 0.03477100603508227, "one_reference_only": false, "rounds": 10, "run_valid": true, "seed": 2, "t_written_utc": 1792490124.7529793, "warmup_ms": [0.043007999658584595, 0.03788800165057182], "x_all_zero": false, "x_finite": true, "x_first8": [-0.1318023877208004, -0.006686993672656713, -0.07066063549290416, -0.06660767559499439, -0.21553893487283146, -0.47257053182695763, -0.9383654550869579, -0.7381146581579195]}
{"K": 1, "N": 1024, "R": 1253, "anchor_failed": [], "anchor_status": "anchor passed", "arm": "pcr_gpu", "block_at_least_50ms": false, "block_dim": 256, "block_ms": 43.57120132446289, "degenerate": null, "grid": 4, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "launch_fraction": 0.775213878869407, "launch_fraction_from": "median ms per launch over the launch probe's five rows at this level", "launches_per_solve": 10, "ms_per_launch": 0.002695690342038046, "ms_per_solve": 0.03477350464841412, "one_reference_only": false, "rounds": 10, "run_valid": true, "seed": 3, "t_written_utc": 1792490124.7973728, "warmup_ms": [0.04403200000524521, 0.03993599861860275], "x_all_zero": false, "x_finite": true, "x_first8": [0.45956712173875064, 0.4654591067778007, -0.6352807208254428, -0.4797375135931368, 0.22548640041974657, -0.3411520443551451, 0.06928269687602967, -0.8700980725595525]}
{"K": 1, "N": 1024, "R": 1285, "anchor_failed": [], "anchor_status": "anchor passed", "arm": "pcr_gpu", "block_at_least_50ms": false, "block_dim": 256, "block_ms": 44.68531036376953, "degenerate": null, "grid": 4, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "launch_fraction": 0.7751903391337839, "launch_fraction_from": "median ms per launch over the launch probe's five rows at this level", "launches_per_solve": 10, "ms_per_launch": 0.002695690342038046, "ms_per_solve": 0.03477456059437318, "one_reference_only": false, "rounds": 10, "run_valid": true, "seed": 4, "t_written_utc": 1792490124.8433156, "warmup_ms": [0.043007999658584595, 0.03891199827194214], "x_all_zero": false, "x_finite": true, "x_first8": [-0.39861001567043813, 0.18070404700902695, 0.1919598508828549, 0.1625087592216491, 0.09827884939473122, 0.4473872548851103, 0.358048881183865, 1.0428330641219388]}
{"K": 1, "N": 16384, "R": 872, "anchor_failed": [], "anchor_status": "anchor passed", "arm": "pcr_gpu", "block_at_least_50ms": false, "block_dim": 256, "block_ms": 46.72819137573242, "degenerate": null, "grid": 64, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "launch_fraction": 0.7028836131933971, "launch_fraction_from": "median ms per launch over the launch probe's five rows at this level", "launches_per_solve": 14, "ms_per_launch": 0.0026904062903151493, "ms_per_solve": 0.053587375430885806, "one_reference_only": false, "rounds": 14, "run_valid": true, "seed": 0, "t_written_utc": 1792490124.892851, "warmup_ms": [0.07571200281381607, 0.05734400078654289], "x_all_zero": false, "x_finite": true, "x_first8": [-0.0890667694766987, 0.06178373710831483, -0.15546210319029938, 0.0570803244437967, 0.35662240745379975, 0.247993145174921, 0.21224472478493578, -0.20263683136582147]}
{"K": 1, "N": 16384, "R": 872, "anchor_failed": [], "anchor_status": "anchor passed", "arm": "pcr_gpu", "block_at_least_50ms": false, "block_dim": 256, "block_ms": 46.74150466918945, "degenerate": null, "grid": 64, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "launch_fraction": 0.7026834121969848, "launch_fraction_from": "median ms per launch over the launch probe's five rows at this level", "launches_per_solve": 14, "ms_per_launch": 0.0026904062903151493, "ms_per_solve": 0.05360264296925396, "one_reference_only": false, "rounds": 14, "run_valid": true, "seed": 1, "t_written_utc": 1792490124.9415526, "warmup_ms": [0.06441599875688553, 0.05734400078654289], "x_all_zero": false, "x_finite": true, "x_first8": [0.5184688164709682, 0.46007068033048454, 0.1801378383475259, 0.02520533157647122, -0.2429935921750874, -0.08327316175324348, 0.5072642881242397, -0.7720372965757979]}
{"K": 1, "N": 16384, "R": 872, "anchor_failed": [], "anchor_status": "anchor passed", "arm": "pcr_gpu", "block_at_least_50ms": false, "block_dim": 256, "block_ms": 46.740478515625, "degenerate": null, "grid": 64, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "launch_fraction": 0.7026988391055448, "launch_fraction_from": "median ms per launch over the launch probe's five rows at this level", "launches_per_solve": 14, "ms_per_launch": 0.0026904062903151493, "ms_per_solve": 0.053601466187643346, "one_reference_only": false, "rounds": 14, "run_valid": true, "seed": 2, "t_written_utc": 1792490124.9899511, "warmup_ms": [0.06431999802589417, 0.05734400078654289], "x_all_zero": false, "x_finite": true, "x_first8": [-0.3026607477859687, -0.08116988226978208, 0.2018231795187799, 0.3852636043739202, 0.5066750342956674, 0.19541844389768315, -0.1841335190912171, -0.25396601506714234]}
{"K": 1, "N": 16384, "R": 842, "anchor_failed": [], "anchor_status": "anchor passed", "arm": "pcr_gpu", "block_at_least_50ms": false, "block_dim": 256, "block_ms": 45.13177490234375, "degenerate": null, "grid": 64, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "launch_fraction": 0.702709109465757, "launch_fraction_from": "median ms per launch over the launch probe's five rows at this level", "launches_per_solve": 14, "ms_per_launch": 0.0026904062903151493, "ms_per_solve": 0.05360068278188094, "one_reference_only": false, "rounds": 14, "run_valid": true, "seed": 3, "t_written_utc": 1792490125.036747, "warmup_ms": [0.06441599875688553, 0.05939200147986412], "x_all_zero": false, "x_finite": true, "x_first8": [-0.07344050692079923, -0.46724208711153065, -0.36804201650364926, -0.2016722065813377, -0.11055142465649948, -0.12426465721473472, 0.44576936306803283, 0.18849459805264365]}
{"K": 1, "N": 16384, "R": 857, "anchor_failed": [], "anchor_status": "anchor passed", "arm": "pcr_gpu", "block_at_least_50ms": false, "block_dim": 256, "block_ms": 45.929473876953125, "degenerate": null, "grid": 64, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "launch_fraction": 0.7028056702255986, "launch_fraction_from": "median ms per launch over the launch probe's five rows at this level", "launches_per_solve": 14, "ms_per_launch": 0.0026904062903151493, "ms_per_solve": 0.05359331840951356, "one_reference_only": false, "rounds": 14, "run_valid": true, "seed": 4, "t_written_utc": 1792490125.0843537, "warmup_ms": [0.06435199826955795, 0.058368001133203506], "x_all_zero": false, "x_finite": true, "x_first8": [-0.21702004779385775, 0.520470155383871, 0.4920973399219945, 0.3080065029716126, 0.05795799204738174, -0.08910627115180048, -0.35175654353490665, -0.31413368258343]}
{"K": 1, "N": 262144, "R": 304, "anchor_failed": [], "anchor_status": "anchor passed", "arm": "pcr_gpu", "block_at_least_50ms": false, "block_dim": 256, "block_ms": 48.86016082763672, "degenerate": null, "grid": 1024, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "launch_fraction": 0.2995578702820996, "launch_fraction_from": "median ms per launch over the launch probe's five rows at this level", "launches_per_solve": 18, "ms_per_launch": 0.002674789056865447, "ms_per_solve": 0.160724213248805, "one_reference_only": false, "rounds": 18, "run_valid": true, "seed": 0, "t_written_utc": 1792490125.157943, "warmup_ms": [0.17235200107097626, 0.16486400365829468], "x_all_zero": false, "x_finite": true, "x_first8": [-0.08387418168427681, -0.22580580719882384, -0.10950277566928444, 0.32556062571111305, -0.15928725019531514, 0.21055459023441067, 0.029857717767751424, 0.6598599201515274]}
{"K": 1, "N": 262144, "R": 304, "anchor_failed": [], "anchor_status": "anchor passed", "arm": "pcr_gpu", "block_at_least_50ms": false, "block_dim": 256, "block_ms": 48.89292907714844, "degenerate": null, "grid": 1024, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "launch_fraction": 0.2993571053203377, "launch_fraction_from": "median ms per launch over the launch probe's five rows at this level", "launches_per_solve": 18, "ms_per_launch": 0.002674789056865447, "ms_per_solve": 0.16083200354325144, "one_reference_only": false, "rounds": 18, "run_valid": true, "seed": 1, "t_written_utc": 1792490125.225984, "warmup_ms": [0.1745920032262802, 0.16486400365829468], "x_all_zero": false, "x_finite": true, "x_first8": [0.2692408824723714, -0.791196107823321, 0.2076605191669208, -0.3107287186614362, 0.25843560416218475, -0.47035390050555087, 0.050426892505120675, -0.007908279625324576]}
{"K": 1, "N": 262144, "R": 302, "anchor_failed": [], "anchor_status": "anchor passed", "arm": "pcr_gpu", "block_at_least_50ms": false, "block_dim": 256, "block_ms": 48.544769287109375, "degenerate": null, "grid": 1024, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "launch_fraction": 0.29952049472365244, "launch_fraction_from": "median ms per launch over the launch probe's five rows at this level", "launches_per_solve": 18, "ms_per_launch": 0.002674789056865447, "ms_per_solve": 0.16074426916261383, "one_reference_only": false, "rounds": 18, "run_valid": true, "seed": 2, "t_written_utc": 1792490125.2923872, "warmup_ms": [0.1733119934797287, 0.1658879965543747], "x_all_zero": false, "x_finite": true, "x_first8": [-0.3940085165019745, 0.037392316482038786, -0.06113722992980534, 0.3396511864732271, 0.4133731360129172, 0.1931203061120717, 0.10097850167157056, -0.28637342394109117]}
{"K": 1, "N": 262144, "R": 304, "anchor_failed": [], "anchor_status": "anchor passed", "arm": "pcr_gpu", "block_at_least_50ms": false, "block_dim": 256, "block_ms": 48.889854431152344, "degenerate": null, "grid": 1024, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocki
[digest: truncated by the byte cap; showing the first 37394 of 70936 bytes]

=== results_m2/out/records/id-E10_kind-endpoint_run-m2.json (4834 bytes)
{
  "cell": {
    "id": "E10",
    "kind": "endpoint",
    "run": "m2"
  },
  "decision": "REFUTED (below: the plan over-bought by more than 3x)",
  "decision_rule": "Hours from the first anchor solve to the last sweep row. HOLDS if within [0.67, 6]. Below 0.67: REFUTED, the plan over-bought by more than 3x. Above 6: REFUTED, the plan under-bought.",
  "env": {
    "git_rev": null,
    "host": "150-136-47-224",
    "python": "3.10.12",
    "timestamp_utc": "2026-10-20T09:58:53+00:00"
  },
  "inputs": [
    {
      "bytes": 1520035,
      "n_items": 11,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/anchor.jsonl",
      "present": true,
      "sha256": "8c76cef1539a"
    },
    {
      "bytes": 137275,
      "n_items": 50,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/residual_sweep.jsonl",
      "present": true,
      "sha256": "d5ecf0c76679"
    },
    {
      "bytes": 65392,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/thomas_gpu.jsonl",
      "present": true,
      "sha256": "9d1b8fc1136d"
    },
    {
      "bytes": 70936,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/pcr_gpu.jsonl",
      "present": true,
      "sha256": "f73af1752f60"
    },
    {
      "bytes": 68537,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/cusparse_gpu.jsonl",
      "present": true,
      "sha256": "2ef01011a680"
    },
    {
      "bytes": 68177,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/thomas_batched_gpu.jsonl",
      "present": true,
      "sha256": "39e4178392db"
    },
    {
      "bytes": 62652,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/launch_probe.jsonl",
      "present": true,
      "sha256": "6f8826ec206a"
    },
    {
      "bytes": 70403,
      "n_items": 25,
      "path": "/home/ubuntu/m2_run/results_m2/out/rows/cpu_dgtsv.jsonl",
      "present": true,
      "sha256": "68cbcae8d816"
    }
  ],
  "metric": "card cost line 'need 2 h': hours from the first anchor solve to the last sweep row",
  "notes": "",
  "threshold": {
    "band_hours": [
      0.67,
      6.0
    ]
  },
  "values": {
    "anchor_failed": [],
    "card_need_hours": 2.0,
    "decision": "REFUTED",
    "direction": "below: the plan over-bought by more than 3x",
    "first_anchor_solve_utc": 1792489904.3220892,
    "hours": 0.11910545163684422,
    "labels": {
      "baseline": "baseline: one CUDA thread per system, this build's kernel",
      "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries",
      "budget_left_usd": 6.0,
      "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)",
      "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80",
      "cuda_driver_api_version": "12.8",
      "cuda_runtime_version": "12.8",
      "cuda_runtime_version_runner_library": "12.8",
      "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12",
      "cusparse_available": true,
      "cusparse_note": null,
      "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e",
      "gpu_device_count": 1,
      "gpu_driver": "570.148.08",
      "gpu_memory": "40960 MiB",
      "gpu_name": "NVIDIA A100-SXM4-40GB",
      "instance_type": "gpu_1x_a100_sxm4",
      "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354",
      "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409",
      "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12",
      "mkl_num_threads": "1",
      "numpy_version": "1.26.4",
      "nvcc_arch_flag": "-arch=sm_80",
      "nvcc_path": "/usr/bin/nvcc",
      "nvcc_version": "12.8 (V12.8.93)",
      "omp_num_threads": "1",
      "openblas_num_threads": "1",
      "price_usd_per_hour": 1.99,
      "python_version": "3.10.12",
      "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1",
      "scipy_lapack_libraries": {
        "libblas.so.3": {
          "path": "/lib/x86_64-linux-gnu/libblas.so.3",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"
        },
        "liblapack.so.3": {
          "path": "/lib/x86_64-linux-gnu/liblapack.so.3",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"
        },
        "libopenblas.so.0": {
          "path": "/lib/x86_64-linux-gnu/libopenblas.so.0",
          "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"
        }
      },
      "scipy_version": "1.8.0",
      "vcpu_count": 30
    },
    "last_sweep_row_utc": 1792490333.101715,
    "one_reference_only": false,
    "run_valid": true
  }
}

=== onbox_m2.sh (3710 bytes)
#!/usr/bin/env bash
# On-box batch for measure run m2: runs the runner's stages in order on the rented GPU box.
#
# The launcher runs it from ~/m2_run as:   bash remote_run_m2.sh bash onbox_m2.sh
# No venv and no pip install here. The execution note's toolchain rule uses the image's python3, numpy and
# scipy as they are, and nvcc from PATH or /usr/local/cuda*. The remote bootstrap's own installs are left alone.
#
# Results go under results_m2/out/; the compiled library goes under results_m2/build/.
# Before every stage a guard runs. It stops cleanly before projected spend reaches BUDGET_LEFT_USD.
# It also caps each stage so the run ends inside REMOTE_TIMEOUT (3600 s unless set).
# After the last stage, after any stop and after any failure, it writes m2_summary.json and then RUN_DONE.
# RUN_DONE holds the exit code: 0 all stages ran; 2 toolchain; 3 no GPU; 4 guard inputs missing;
# 5 guard stop; 6 zero-dispersion halt; 124 a stage hit its time cap; 1 any other stage failure.
set -uo pipefail
cd "$(dirname "$0")" || exit 1
OUT=results_m2/out
BUILD=results_m2/build
REMOTE_TIMEOUT=${REMOTE_TIMEOUT:-3600}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONUNBUFFERED=1
STAGES="build gpucheck anchor timers residual_sweep thomas_gpu pcr_gpu cusparse_gpu thomas_batched_gpu launch_probe cpu_dgtsv endpoints"

# A results directory left by an earlier run on this box is moved aside, never mixed in.
if [ -d "$OUT" ] && [ -n "$(ls -A "$OUT" 2>/dev/null)" ]; then
  PREV="results_m2/out_prev_$(date -u +%Y%m%dT%H%M%SZ)"
  mv "$OUT" "$PREV" && echo "[onbox] earlier results moved to $PREV"
fi
mkdir -p "$OUT/logs" "$BUILD"

# Seconds since this process started. remote_run_m2.sh execs into this script, so that is its start.
elapsed(){ local e; e=$(ps -o etimes= -p $$ 2>/dev/null | tr -d ' '); if [ -n "$e" ]; then echo "$e"; else echo "$SECONDS"; fi; }
# Box uptime in seconds: the spend clock for the cost guard.
uptime_s(){ cut -d' ' -f1 /proc/uptime 2>/dev/null || echo 0; }

finish(){
  local rc=$1 reason=$2
  if [ -f run_m2.py ]; then
    python3 run_m2.py summary --exit-code "$rc" --stop-reason "$reason" 2>&1 | tee -a "$OUT/logs/summary.log"
  fi
  echo "$rc" > "$OUT/RUN_DONE"
  echo "[onbox] RUN_DONE rc=$rc ($reason)"
  exit "$rc"
}

for f in run_m2.py frozen/provenance.py; do
  [ -f "$f" ] || finish 2 "payload file missing: $f"
done

echo "[onbox] start $(date -u +%FT%TZ) REMOTE_TIMEOUT=${REMOTE_TIMEOUT}s PRICE_USD_PER_HOUR=${PRICE_USD_PER_HOUR:-unset}" \
     "BUDGET_LEFT_USD=${BUDGET_LEFT_USD:-unset} INSTANCE_TYPE=${INSTANCE_TYPE:-unset} elapsed=$(elapsed)s"
echo "[onbox] stages: $STAGES"

for st in $STAGES; do
  G=$(python3 run_m2.py guard --remote-timeout "$REMOTE_TIMEOUT" --elapsed "$(elapsed)" --uptime "$(uptime_s)" \
        --price "${PRICE_USD_PER_HOUR:-}" --budget "${BUDGET_LEFT_USD:-}" 2>>"$OUT/logs/guard.log")
  case "$G" in
    "RUN "*)    ALLOW=${G#RUN } ;;
    "STOP "*)   finish 5 "${G#STOP } (before stage $st)" ;;
    "BADENV "*) finish 4 "${G#BADENV } (before stage $st)" ;;
    *)          finish 1 "guard gave no verdict before stage $st: $G" ;;
  esac
  echo "[onbox] stage $st: cap ${ALLOW}s"
  T0=$(date -u +%s)
  timeout -k 30 "$ALLOW" python3 run_m2.py "$st" 2>&1 | tee "$OUT/logs/$st.log"
  rc=${PIPESTATUS[0]}
  T1=$(date -u +%s)
  printf '{"stage": "%s", "rc": %d, "start_utc": %d, "end_utc": %d, "cap_s": %d}\n' \
         "$st" "$rc" "$T0" "$T1" "$ALLOW" >> "$OUT/stages.jsonl"
  if [ "$rc" -ne 0 ]; then
    if [ "$rc" -eq 124 ] || [ "$rc" -eq 137 ]; then
      finish 124 "time guard: stage $st stopped at its ${ALLOW}s cap"
    fi
    finish "$rc" "stage $st failed (rc=$rc)"
  fi
done
finish 0 "all stages ran"


=== TAKEAWAYS_m2.md (28264 bytes)
# Takeaways from the second measurement run

This note covers one speed test of three ways to solve a tridiagonal system of equations. It assumes you have never seen the project.

A tridiagonal system is a chain of N equations. Each equation links only its two neighbours. Each measured sentence below names its solver, which plays the role of the model [^1]. The numbers come from one rented 40 GB data-centre graphics card (GPU) and one CPU core.

Words used throughout:

- **One-thread solver**: the Thomas algorithm, written by hand, running on a single GPU thread per system. It sweeps forward, then back.
- **Parallel solver**: parallel cyclic reduction, written by hand. It uses one GPU thread per equation and about log2(N) rounds.
- **Vendor solver**: the graphics-card maker's own library routine for the same job.
- **CPU library solver**: the standard LAPACK tridiagonal routine, run on one CPU core through scipy.
- **Speedup**: slower solver's median time divided by faster solver's median time. The median is taken over five random systems.
- **Residual**: how badly a computed answer fails to satisfy the equations, as a relative size. Near 1e-16 is as good as double precision allows.


## 1. Research question and hypothesis

The project keeps "cards": written plans that predict an outcome before anything is measured. One card proposed using a GPU's width on a single tridiagonal correction step inside a larger calculation. Width means thousands of threads working at once.

The question was this. Does that card's own decision rule give its predicted outcome ("lever") on its own hardware? And do the card's four numbers still hold once measured?

The hypothesis the card stated is that feeding GPU width to one solve shortens its wall-clock time. The card's decision rule says "lever" only if two things are true. First, the parallel solver must beat the one-thread solver by at least 2 times at N = 2^24 (16,777,216 equations). Second, that speedup must grow as N grows.

The four numbers the card promised to be checked later were these:

- The worst residual, guessed at 1e-13.
- The smallest N where the parallel solver wins, guessed at 1,024.
- The speedup at 2^24, taken from a 2009 study on an older graphics card against a CPU library. That study gave 28.
- The time needed for the whole run, planned at 2 hours.

## 2. What the experiment tried to find

It timed the one-thread solver and the parallel solver at five sizes: 2^10, 2^14, 2^18, 2^22 and 2^24. Each size used five random systems (seeds 0 to 4). The matrices have a diagonal of 3 and off-diagonals of plus or minus 1, so they are safely well behaved.

Before any timing, both hand-written solvers had to pass a check at 2^10 and 2^14. Each had to reach a residual of 1e-10 or lower. Each also had to match two independent references to within 1e-8. The references were the vendor solver and the CPU library solver.

Four extra readings were declared in advance as report-only. They do not decide the card. They are exploratory, and I label them that way below.

- The shape of the parallel solver's time against N.
- The same rule re-read against the CPU library solver instead of the one-thread solver.
- A test solving many systems at once with the one-thread solver.
- The vendor solver's time, as a yardstick.

## 3. What was predicted, and what happened

The run was valid. No stage failed, and no result was voided. Every planted-case control passed. The anchor check passed for both hand-written solvers.

**Anchor check (passed).** The largest residual of the one-thread solver was 1.39e-16, measured on seed 0 at 2^14. The parallel solver's largest was 3.11e-16 at 2^14. The largest difference from either reference was 2.57e-16, for the parallel solver against the CPU library at 2^10. The vendor solver and CPU library solver differed from each other by at most 2.57e-16 [^1].

**Prediction 1: residual about 1e-13, holds if between 1e-14 and 1e-12. Refuted.** The worst residual of the two hand-written solvers was 3.11e-16 (parallel solver, 2^14). The parallel solver's worst residual is 321.4 times below the guess [^1]. The error is in the good direction, but the guess was still wrong by more than the allowed 10 times.

**Prediction 2: the parallel solver already wins at N = 1,024. Held, with a caveat.** Against the one-thread solver, the lower quartile of the speedup at 2^10 was 8.54, above 1. Lower quartile means the value a quarter of the way up the five seeds. The crossover was therefore 2^10. The run labelled it launch-bound, because 0.775 of the parallel solver's time at 2^10 was kernel-launch gaps. See section 5 for what changes with a CPU baseline.

**Prediction 3: the card's rule gives "lever". Held.** Against the one-thread solver, the median speedups at the five sizes were 8.54, 95.90, 517.53, 395.38 and 348.30 [^1]. The parallel solver's 2^24 speedup of 348.30 over the one-thread solver is far above 2. The lower quartile at 2^24 was 348.29, so the result is not within noise. The slope of log speedup against log2(N) was +0.256, so it is positive [^1]. The outcome is "lever". Two adjacent steps fell: 517.53 to 395.38, then 395.38 to 348.30 [^1].

**Prediction 4: speedup at 2^24 near 28, holds if between 9.3 and 84. Refuted.** The one-thread solver took a median 7598.5 ms and the parallel solver 21.8 ms at 2^24, giving 348.30. That is 12.44 times the old figure of 28, above the allowed band [^1].

**Prediction 5: the run needs 2 hours, holds if between 0.67 and 6 hours [^1]. Refuted.** The on-box time from first anchor solve to last sweep row was 0.119 hours, about 7.15 minutes [^1]. The plan over-bought by about 16.8 times [^1].

### Exploratory readings (report-only)

**Shape of the parallel solver's time.** The card says time "grows like log2(N)". The parallel solver took 4.785 ms at 2^22 and 21.816 ms at 2^24, a factor of 2.135 per doubling of N. That is labelled linear-like, since the cut-off is 1.7 [^1]. The card's sentence is wrong at large N.

**CPU library as the baseline.** The CPU library solver took a median 416.7 ms at 2^24. The parallel solver's speedup over it was 0.59, 5.78, 30.71, 18.41 and 19.10 at the five sizes [^1]. The rule still gives "lever" under that baseline. But at 2^10 the CPU is faster, since 0.59 is below 1.

**Many systems at once.** The one-thread solver was run on 256, 256, 256, 64 and 16 systems together at the five sizes. The time ratios to one system were 1.08, 1.76, 1.81, 1.08 and 1.05 [^1]. All sit inside the allowed 0.9 to 3, so the card's claim held [^1].

**Vendor solver.** The vendor solver took 0.0148, 0.0490, 0.0994, 0.800 and 2.943 ms at the five sizes [^1]. The hand-written parallel solver took 2.35, 1.09, 1.62, 5.98 and 7.41 times as long [^1].

## 4. Is this what we expected?

Partly. The headline outcome matched the card: the rule reads "lever". Three of the four numbers did not match. The residual guess, the 28 speedup and the 2-hour plan were all refuted. The crossover guess survived.

The "lever" verdict is weaker than it looks. Its baseline is a single GPU thread, which is the slowest sensible way to run the older method. Against the CPU library solver, the 2^24 speedup is 19.10, not 348.30. Against the vendor solver, the hand-written parallel solver is 7.41 times slower at 2^24. These are exploratory readings. They do not change the card's verdict.

## 5. What in these files does not fit

### Open questions

**1. Why was the 2^24 speedup measured against one GPU thread, not the CPU library?**

The old 28 came from a parallel solver against a CPU library. Against the one-thread solver the run got 348.30, which is 12.44 times too high [^1]. Against the CPU library it got 19.10, which is 0.68 of 28 and inside the band [^1]. Median times at 2^24 were 7598.5 ms (one thread), 416.7 ms (CPU library), 21.8 ms (parallel solver) and 2.94 ms (vendor solver). The one-thread solver is 18.2 times slower than the CPU library solver on one core [^1]. The vendor solver is 2582 times faster than that thread. If the card meant the CPU library, the miss comes from the baseline, not from the old figure travelling badly. The headline would shrink from 348 to 19. The files do not say which baseline the card meant.

**2. Does the CPU library beat the parallel solver at the smallest size?**

Yes, on the CPU baseline. The speedup at 2^10 was 0.59 and at 2^14 it was 5.78. Under that baseline the card's claim of winning at the smallest size fails. The crossover then sits between 2^10 and 2^14. The prediction was marked "holds" only because the one-thread baseline gave 8.54 [^1]. At 2^24 the five CPU library times ran from 370.3 to 484.6 ms. The five one-thread solver times at 2^24 differ by only about 0.004 percent, so the seeds add almost no noise information there.

**3. Do the timed solves include moving data to the GPU?**

The records never say. They show timed blocks of repeated solves on data already on the card. At 2^24 each of four input arrays is 134.2 MB, 536.9 MB in all. At an assumed 25 GB/s link, which is my assumption and not in the files, a copy would take about 21 ms. That is about the parallel solver's 21.8 ms [^1]. The speedup over the CPU library would roughly halve from 19.10, and 348 would fall much further [^1]. The design needs a case with data resident and a case with data copied.

**4. Does speedup really grow with size, when it peaks at 2^18?**

The one-thread solver speedups were 8.54, 95.90, 517.53, 395.38 and 348.30. The rule compares only 2^24 with 2^10, plus a slope of +0.256 over all five. So "grows" passes through its endpoints while the top three levels fall. The one-thread solver cost 317 ns per equation at 2^18 and 451 ns at 2^22. The parallel solver's time grew 29.8 times over that step while size grew 16 times [^1]. Something changes between 2^18 and 2^22. Cache size is one guess, and the files never test it. Any extrapolation to larger N is unsupported.

**5. How much small-size time is launch overhead, and were all blocks at least 50 ms?**

The design expected launch gaps to inflate small-size time by at most about 2 times. Measured launch share of parallel-solver time was 0.775 at 2^10 and 0.703 at 2^14. That would allow up to about 4.4 times [^1]. Timed blocks under 50 ms numbered 52 of 125 timing rows, so the design's rule was often missed. I counted 77 of 150 when the launch-probe rows are included. Examples are the parallel solver at 2^10, 2^14 and 2^18, and the vendor solver at four sizes. The 8.54 and 95.90 speedups mostly measure launch cost [^1]. The empty-kernel test cost 50 microseconds per launch at 2^24, which is block scheduling, not launch delay.

**6. Why was the many-systems test never compared with the parallel solver?**

The ratios were 1.08, 1.76, 1.81, 1.08 and 1.05, all inside the band [^1]. At 2^10, 256 systems took 0.3218 ms, which is 1.26 microseconds each. One parallel-solver solve took 34.8 microseconds [^1]. If the real calculation has many independent systems, plain Thomas is about 27 times faster per system at 2^10. At 2^24 it loses: 16 systems took 7965 ms. The ratios 1.76 and 1.81 at 2^14 and 2^18 are unexplained. Only 256 GPU threads were busy, a tiny part of the card.

**7. Does "linear-like" describe the parallel solver, with one factor of 2.135 from two levels?**

The factor of 2.135 uses only 2^22 and 2^24. Exactly linear would be 2.0, so the time is steeper than linear at the top [^1]. From 2^10 to 2^14 the factor is 1.11 per doubling, which would read as log-like. Neither label fits. The word "linear-like" hides a flat stretch followed by a superlinear one.

**8. Could the 2-hour estimate ever have been judged too low, and what did 0.119 hours cover [^1]?**

Every stage started with a time cap near 3482 s, about 0.97 hours. So the upper half of the band could never be seen [^1]. The 0.119 hours counts first anchor solve to last sweep row [^1]. It excludes setup and installs. The 16.8 times over-buy is therefore not like for like [^1]. The stage log shows a budget_left of 6.0 dollars throughout [^1]. Scipy 1.8.0 and numpy 1.26.4 are both recorded [^1]. The files I read do not state that this pair is unsupported, so I cannot confirm that part.

### Further things I found

- **The floor library differs from the card.** The card names MKL as the CPU floor. The run recorded OpenBLAS 0.3.20 behind scipy, on one thread [^1]. The vendor field reads as unnamed.
- **Installs happened despite the design.** The design planned no installs. The first lines of the run log show a setup step adding transformers, accelerate and scikit-learn.
- **The card was rejected by its own reviewer.** The run labels record "card dramaturg: REJECT (3 blocking, citations)". The run went ahead anyway.
- **The five seeds are not independent boxes.** The summary says the seeds are five generated systems on one machine. Tight spreads reflect one machine, not run-to-run variation across machines.
- **"Refuted" on the residual is symmetric by design.** The band is 10 times either way. A result 321.4 times better than guessed counts as refuted, though nothing went wrong [^1].
- **The growth rule is weak.** It passes with a fall of 32.7 percent from the 2^18 peak to 2^24.
- **The CPU side is the noisy side.** The CPU library times at 2^24 ran 370.3 to 484.6 ms, a spread of 31 percent. The one-thread solver spread was about 0.004 percent [^1].
- **Dates.** Files on disk are stamped 11:00, but the run's records say 09:51 to 09:58 UTC. They were evidently copied afterwards.

[^1]: This project has no language models. Each measured sentence names the solver or baseline it describes, which plays the role of the model.

## Raw samples, verbatim

Five rows were picked at random with a fixed seed. Each is one line, exactly as stored.

An input row: the generated system fingerprint used for one-thread solver timing.

```json
{"N": 16777216, "a": {"first8": [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, -1.0], "n": 16777216, "sha256": "e2b5410920d7d30d82dc31deed0379efba4a78c7aa8ff9c56fd04e84427fd379"}, "anchor_failed": [], "b": {"first8": [3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0], "n": 16777216, "sha256": "295948a1de46b54fe093d2551510ebae242f0f646074021e80916926a61b5080"}, "c": {"first8": [1.0, 1.0, 1.0, 1.0, -1.0, 1.0, -1.0, -1.0], "n": 16777216, "sha256": "0fb0a08dbb35aa22ab440bb3b11379747910fd2e15c8a0667576817a46846be3"}, "context": "thomas_gpu", "d": {"first8": [0.276472080635235, -0.5187778639281005, 0.814970759465404, 0.4022427886374344, -0.16567555068627843, -1.171986060213274, 0.9237282420657763, -0.01891539322137044], "n": 16777216, "sha256": "08bcb0906132a2770167fb1e6f00cef2af71e91ed9e970a294227b3d5363239b"}, "kind": "system", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "one_reference_only": false, "run_valid": true, "seed": 4, "t_written_utc": 1792490101.1019228}
```

An input row: the generated system fingerprint used for parallel solver timing.

```json
{"N": 262144, "a": {"first8": [0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, -1.0], "n": 262144, "sha256": "b62d08a5ecf27c3a273b0ba990ca5d057cb1064c60469a70ad4ffd650d0c569d"}, "anchor_failed": [], "b": {"first8": [3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0, 3.0], "n": 262144, "sha256": "fe5439c2b011ec45fd12206b6f36c36f4d5a0e433070dfba337e6369938ca237"}, "c": {"first8": [1.0, -1.0, 1.0, 1.0, 1.0, -1.0, 1.0, 1.0], "n": 262144, "sha256": "3deb6dd52cf42787975119736c02839ef3e39b7beca11dbcdd8afcec5c80737f"}, "context": "pcr_gpu", "d": {"first8": [-0.5289394796393546, -0.8021523777922626, 0.4092672367525235, 0.9808994085506736, -0.28371766505553736, 0.2126220765650628, -0.5122409840628848, -0.804789456234628], "n": 262144, "sha256": "1c9d4501a73fd365ccf3f56637b5007c3421719146122d5f37620d2a2c2d069b"}, "kind": "system", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "one_reference_only": false, "run_valid": true, "seed": 4, "t_written_utc": 1792490125.3763971}
```

An output row: one timing of the one-thread solver.

```json
{"K": 1, "N": 16777216, "R": 1, "anchor_failed": [], "anchor_status": "anchor passed", "arm": "thomas_gpu", "block_at_least_50ms": true, "block_dim": 1, "block_ms": 7598.57470703125, "degenerate": null, "grid": 1, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "ms_per_solve": 7598.57470703125, "one_reference_only": false, "run_valid": true, "seed": 3, "t_written_utc": 1792490099.6330864, "warmup_ms": [7613.25341796875, 7598.34033203125], "x_all_zero": false, "x_finite": true, "x_first8": [0.4858339846436915, 0.09004596052209478, -0.08469506984409962, -0.5191058190665746, -0.08251707041533349, -0.03677784537515155, -0.35350881187299743, -0.858629709765579]}
```

An output row: one timing of the vendor solver.

```json
{"K": 1, "N": 16777216, "R": 17, "anchor_failed": [], "anchor_status": null, "arm": "cusparse_gpu", "block_at_least_50ms": true, "block_ms": 51.316734313964844, "buffer_bytes": 537001984, "copies_in_timed_block": 17, "copies_made": 19, "copy_rule": "one right-hand-side copy per solve, made before the timed block", "degenerate": null, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "ms_per_solve": 3.018631430233226, "one_reference_only": false, "run_valid": true, "seed": 0, "t_written_utc": 1792490141.453078, "warmup_ms": [3.0402560234069824, 3.1037440299987793], "x_all_zero": false, "x_finite": true, "x_first8": [0.6075402993412365, 0.06100850417175658, 0.06456682918909255, 0.08331669779459235, -0.30744345506579757, 0.1155971595029857, -0.0024099841672812067, 0.6290760657074215]}
```

An output row: one timing of the CPU library solver.

```json
{"N": 262144, "R": 11, "anchor_failed": [], "anchor_status": null, "arm": "cpu_dgtsv", "block_at_least_50ms": true, "block_ms": 55.084218999922996, "copies_in_timed_block": 11, "copies_made": 13, "copy_rule": "dgtsv overwrites its inputs; one input copy per call, made before the timed block", "degenerate": null, "kind": "timing", "labels": {"baseline": "baseline: one CUDA thread per system, this build's kernel", "blas_lapack_vendor": "unnamed in scipy.show_config (generic blas/lapack names); see scipy_lapack_libraries", "budget_left_usd": 6.0, "card_dramaturg": "card dramaturg: REJECT (3 blocking, citations)", "compile_command": "/usr/bin/nvcc -O3 -shared -Xcompiler -fPIC -o results_m2/build/libm2.so results_m2/build/m2_kernels.cu -lcusparse -lcudart -arch=sm_80", "cuda_driver_api_version": "12.8", "cuda_runtime_version": "12.8", "cuda_runtime_version_runner_library": "12.8", "cuda_runtime_version_via": "cudaRuntimeGetVersion via ctypes on /lib/x86_64-linux-gnu/libcudart.so.12", "cusparse_available": true, "cusparse_note": null, "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e", "gpu_device_count": 1, "gpu_driver": "570.148.08", "gpu_memory": "40960 MiB", "gpu_name": "NVIDIA A100-SXM4-40GB", "instance_type": "gpu_1x_a100_sxm4", "kernel_source_sha256": "bb768a4721c5af56d50446cea6f5289af1ae25f8f339ded20fd7143c233d5354", "lambda_instance_id": "3be4cd7175024dcd8ffa23e50d300409", "libcudart_path": "/lib/x86_64-linux-gnu/libcudart.so.12", "mkl_num_threads": "1", "numpy_version": "1.26.4", "nvcc_arch_flag": "-arch=sm_80", "nvcc_path": "/usr/bin/nvcc", "nvcc_version": "12.8 (V12.8.93)", "omp_num_threads": "1", "openblas_num_threads": "1", "price_usd_per_hour": 1.99, "python_version": "3.10.12", "runner_sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1", "scipy_lapack_libraries": {"libblas.so.3": {"path": "/lib/x86_64-linux-gnu/libblas.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libblas.so.3"}, "liblapack.so.3": {"path": "/lib/x86_64-linux-gnu/liblapack.so.3", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/liblapack.so.3"}, "libopenblas.so.0": {"path": "/lib/x86_64-linux-gnu/libopenblas.so.0", "resolved": "/usr/lib/x86_64-linux-gnu/openblas-pthread/libopenblasp-r0.3.20.so"}}, "scipy_version": "1.8.0", "vcpu_count": 30}, "mkl_num_threads": "1", "ms_per_solve": 5.007656272720272, "omp_num_threads": "1", "one_reference_only": false, "openblas_num_threads": "1", "run_valid": true, "seed": 0, "solver_status": 0, "t_written_utc": 1792490314.3089788, "warmup_ms": [4.941432999999051, 4.947831000094993], "x_all_zero": false, "x_finite": true, "x_first8": [-0.08387418168427681, -0.22580580719882387, -0.10950277566928442, 0.32556062571111305, -0.1592872501953151, 0.21055459023441056, 0.0298577177677514, 0.6598599201515274]}
```

## Gate outputs

```
/tmp/claude-1000/s/trunc.md: 1.3 codes/1000 words (3 codes, 2383 words); threshold 10.0
0 unscoped result sentence(s)
```


=== end of the cited files

## What to return

For every sentence id, decide whether the files support the sentence, contradict it, or do not address it. Supported means a line in a cited file states it or computes it, numbers included. Contradicted means a line states otherwise, including a different number. Not addressed means the cited file does not bear on it; a sentence whose number appears in no file shown is not addressed. Judge each sentence on its own, and judge only what it claims.

For supported and contradicted, quote the line you relied on exactly, one sentence or less, copied character for character from one file, and give that file's path as its `===` line shows it. For not addressed, leave the quote empty and give the path the sentence cites. Copy the question id and the sentence as given. Give a reason of at most 40 words. When a truncated file might hold the answer, say so in the reason and do not guess.

Then give the final enums. Keep each of the reader's draft values unless the files show it is wrong. The meanings:
- headline_kind: speedup (the method beat the baseline under the run's own rule), negative (it did not), void (the run was voided or produced no valid headline), partial (only part of the rule could be applied), unknown.
- baseline_kind: stock (the published code as shipped), tuned (a baseline tuned for this hardware), one_thread (one thread, or one GPU thread, per problem), cpu_library (a CPU library routine), other, unknown.
- equivalence: bit_identical, within_tolerance (outputs compared with a reference and matched within a stated tolerance), not_checked, failed, unknown.
- prediction_hit: yes (every sealed prediction held), partly, no, not_sealed (nothing was sealed before measuring), unknown. Count only the predictions sealed before this run measured. The brief's or card's own guesses are context for the prose, not for this value.
- evidence: measured (the headline number was measured in this run), inferred (computed from other numbers or quoted, not measured here), unknown.
- anchor: measured (an independent reference implementation ran and reproduced its published value), page_value_only (the published value was compared, but the reference code did not run), not_run (an anchor was planned and did not run), none (the run had no anchor), unknown.

Decide only from the text above. Use no tools and read no files.


Return only one JSON value, with no other text, that matches this JSON Schema:
{"type":"object","additionalProperties":false,"required":["sentences","enums"],"properties":{"sentences":{"type":"object","additionalProperties":false,"required":["S1","S2","S3","S4","S5","S6","S7","S8","S9","S10","S11","S12","S13","S14","S15","S16","S17","S18","S19","S20","S21","S22","S23","S24","S25","S26","S27","S28","S29","S30","S31","S32","S33","S34","S35","S36","S37","S38","S39","S40","S41","S42","S43","S44","S45","S46","S47","S48"],"properties":{"S1":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S2":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S3":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S4":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S5":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S6":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S7":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S8":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S9":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S10":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S11":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S12":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S13":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S14":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S15":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S16":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S17":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S18":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S19":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S20":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S21":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S22":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S23":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S24":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S25":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S26":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S27":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S28":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S29":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S30":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S31":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S32":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S33":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S34":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S35":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S36":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S37":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S38":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S39":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S40":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S41":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S42":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S43":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S44":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S45":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S46":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S47":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}},"S48":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt","QUESTION.md","run_m2.py","results_m2/out/records/id-E3_kind-endpoint_run-m2.json","results_m2/out/env.json","results_m2/out/m2_summary.json","results_m2/out/records/id-E1_kind-endpoint_run-m2.json","results_m2/out/records/id-I1_exact_kind-control_run-m2.json","results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","results_m2/out/records/id-E7_kind-endpoint_run-m2.json","results_m2/out/records/id-E9_kind-endpoint_run-m2.json","RUN.md","results_m2/out/rows/pcr_gpu.jsonl","results_m2/out/records/id-E10_kind-endpoint_run-m2.json","onbox_m2.sh","TAKEAWAYS_m2.md","evidence/_source/reply.txt","evidence/QUESTION.md","evidence/run_m2.py","evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json","evidence/results_m2/out/env.json","evidence/results_m2/out/m2_summary.json","evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json","evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json","evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json","evidence/RUN.md","evidence/results_m2/out/rows/pcr_gpu.jsonl","evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json","evidence/onbox_m2.sh","evidence/TAKEAWAYS_m2.md",""]},"reason":{"type":"string"}}}}},"enums":{"type":"object","additionalProperties":false,"required":["headline_kind","baseline_kind","equivalence","prediction_hit","evidence","anchor"],"properties":{"headline_kind":{"enum":["speedup","negative","void","partial","unknown"]},"baseline_kind":{"enum":["stock","tuned","one_thread","cpu_library","other","unknown"]},"equivalence":{"enum":["bit_identical","within_tolerance","not_checked","failed","unknown"]},"prediction_hit":{"enum":["yes","partly","no","not_sealed","unknown"]},"evidence":{"enum":["measured","inferred","unknown"]},"anchor":{"enum":["measured","page_value_only","not_run","none","unknown"]}}}}}