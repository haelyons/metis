A reader looked at one finished run and answered a set of standing questions, citing a file for what each sentence says. You check that working against the files. Its answers come first below, then its draft enums, then the full text of every file it cited.

## The reader's answers

Each answer is followed by the sentences in it that carry a citation, each with an id. Those are the sentences you check.

### Q1. What question did the brief or card ask, in its own words, and what would count as an answer?
The card asks: “Does GPU parallelism change how many of the 671 CAMELS catchments can get full Bayesian calibration instead of point optimization?” (../20261019-2345-tree/out/RESULT.md). This concerns graphics-card acceleration of parameter sampling for rainfall–runoff models; this phase measures simulation times and sampler overhead (QUESTION.md). The rule requires projected graphics-card completion below one hour and at least twentyfold acceleration over vectorized processor execution (QUESTION.md). Otherwise, the card records its predicted negative answer; completed scientific calibrations are outside this measurement phase (QUESTION.md).
Sentences to check:
S1. The card asks: “Does GPU parallelism change how many of the 671 CAMELS catchments can get full Bayesian calibration instead of point optimization?” (../20261019-2345-tree/out/RESULT.md).
S2. This concerns graphics-card acceleration of parameter sampling for rainfall–runoff models; this phase measures simulation times and sampler overhead (QUESTION.md).
S3. The rule requires projected graphics-card completion below one hour and at least twentyfold acceleration over vectorized processor execution (QUESTION.md).
S4. Otherwise, the card records its predicted negative answer; completed scientific calibrations are outside this measurement phase (QUESTION.md).

### Q2. What exactly ran: which system or problem, at what sizes, on what hardware and software, with how many repeats?
GR4J, a four-parameter daily rainfall–runoff model, ran through the JAX numerical library, scanning days sequentially across parallel parameter sequences called chains (run_m1.py). Measurements covered 268, 1,340 and 2,684 chains over 7,300 days, with one basin’s rainfall and evaporation repeated across chains (run_m1.py) (results_m1/out/raw/timing_rows.jsonl). Hardware comprised one NVIDIA A10 graphics card and 30 virtual processors; JAX and its compiled library were version 0.6.0, using 32-bit floating point (results_m1/out/hardware_labels.json). Each size and backend had ten timed passes at three forcing offsets after compilation warmup (results_m1/out/raw/timing_rows.jsonl). Sampler probes used 1,000 iterations for each of three seeds on each backend (results_m1/out/records/id-E5_kind-endpoint_tag-m1.json).
Sentences to check:
S5. GR4J, a four-parameter daily rainfall–runoff model, ran through the JAX numerical library, scanning days sequentially across parallel parameter sequences called chains (run_m1.py).
S6. Measurements covered 268, 1,340 and 2,684 chains over 7,300 days, with one basin’s rainfall and evaporation repeated across chains (run_m1.py) (results_m1/out/raw/timing_rows.jsonl).
S7. Hardware comprised one NVIDIA A10 graphics card and 30 virtual processors; JAX and its compiled library were version 0.6.0, using 32-bit floating point (results_m1/out/hardware_labels.json).
S8. Each size and backend had ten timed passes at three forcing offsets after compilation warmup (results_m1/out/raw/timing_rows.jsonl).
S9. Sampler probes used 1,000 iterations for each of three seeds on each backend (results_m1/out/records/id-E5_kind-endpoint_tag-m1.json).

### Q3. What was the baseline, who would use it in practice, and is it the one an expert would pick?
The baseline was the same custom, vectorized JAX model and Metropolis sampler executed through the rented machine’s processor backend (run_m1.py). Its intended comparison concerns researchers choosing computing resources for Bayesian catchment calibration rather than point optimization (../20261019-2345-tree/out/RESULT.md). The run does not establish expert preference: its scope excludes alternative implementations, and its write-up identifies missing processor thread settings (QUESTION.md) (TAKEAWAYS_m1.md). Consequently, acceleration is relative to this implementation and machine configuration, without evidence that the processor baseline represents expert tuning (QUESTION.md) (TAKEAWAYS_m1.md).
Sentences to check:
S10. The baseline was the same custom, vectorized JAX model and Metropolis sampler executed through the rented machine’s processor backend (run_m1.py).
S11. Its intended comparison concerns researchers choosing computing resources for Bayesian catchment calibration rather than point optimization (../20261019-2345-tree/out/RESULT.md).
S12. The run does not establish expert preference: its scope excludes alternative implementations, and its write-up identifies missing processor thread settings (QUESTION.md) (TAKEAWAYS_m1.md).
S13. Consequently, acceleration is relative to this implementation and machine configuration, without evidence that the processor baseline represents expert tuning (QUESTION.md) (TAKEAWAYS_m1.md).

### Q4. What number answers the question, what is its spread across repeats, and under which rule does it count?
At 2,684 chains, graphics-card passes had median 88.361 milliseconds and range 88.282–88.777 milliseconds (results_m1/out/records/id-E3_kind-endpoint_tag-m1.json). Processor passes had median 1,037.500 milliseconds and range 998.255–1,088.137 milliseconds at the same size (results_m1/out/records/id-E4_kind-endpoint_tag-m1.json). Multiplying pass medians by 100,000 iterations and measured sampler overhead produced projected graphics-card and processor times of 2.463 and 29.841 hours (results_m1/out/records/id-E5_kind-endpoint_tag-m1.json). Their ratio, 12.115, misses the required twentyfold acceleration, while projected graphics-card completion exceeds the one-hour limit (results_m1/out/records/id-E5_kind-endpoint_tag-m1.json). Full-run uncertainty intervals were not recorded; the separate six-hour planning gate was met (results_m1/out/records/id-E5_kind-endpoint_tag-m1.json) (results_m1/out/records/id-E6_kind-endpoint_tag-m1.json).
Sentences to check:
S14. At 2,684 chains, graphics-card passes had median 88.361 milliseconds and range 88.282–88.777 milliseconds (results_m1/out/records/id-E3_kind-endpoint_tag-m1.json).
S15. Processor passes had median 1,037.500 milliseconds and range 998.255–1,088.137 milliseconds at the same size (results_m1/out/records/id-E4_kind-endpoint_tag-m1.json).
S16. Multiplying pass medians by 100,000 iterations and measured sampler overhead produced projected graphics-card and processor times of 2.463 and 29.841 hours (results_m1/out/records/id-E5_kind-endpoint_tag-m1.json).
S17. Their ratio, 12.115, misses the required twentyfold acceleration, while projected graphics-card completion exceeds the one-hour limit (results_m1/out/records/id-E5_kind-endpoint_tag-m1.json).
S18. Full-run uncertainty intervals were not recorded; the separate six-hour planning gate was met (results_m1/out/records/id-E5_kind-endpoint_tag-m1.json) (results_m1/out/records/id-E6_kind-endpoint_tag-m1.json).

### Q5. How was correctness checked, against which reference, at what tolerance?
On the 59-day example, graphics-card and processor runs achieved Nash–Sutcliffe efficiency scores of 0.494775 and 0.494774, respectively (results_m1/out/records/id-E2_kind-endpoint_tag-m1.json). This flow-fit score was compared with published 0.495, allowing an absolute difference of 0.02 (results_m1/out/records/id-E2_kind-endpoint_tag-m1.json). Additional cases reproduced published scores 0.336 and 0.570 as approximately 0.335984 and 0.569931 on both backends, within the same tolerance (results_m1/out/records/id-I2_kind-control_tag-m1.json). Independent airGR reference code never ran, so daily-flow agreement below one percent mean absolute relative error remained unchecked (results_m1/out/records/id-E2_kind-endpoint_tag-m1.json). Planted zero-rain, response-weight and water-balance checks passed their recorded thresholds using the scalar model implementation (results_m1/out/records/id-I2_kind-control_tag-m1.json) (run_m1.py).
Sentences to check:
S19. On the 59-day example, graphics-card and processor runs achieved Nash–Sutcliffe efficiency scores of 0.494775 and 0.494774, respectively (results_m1/out/records/id-E2_kind-endpoint_tag-m1.json).
S20. This flow-fit score was compared with published 0.495, allowing an absolute difference of 0.02 (results_m1/out/records/id-E2_kind-endpoint_tag-m1.json).
S21. Additional cases reproduced published scores 0.336 and 0.570 as approximately 0.335984 and 0.569931 on both backends, within the same tolerance (results_m1/out/records/id-I2_kind-control_tag-m1.json).
S22. Independent airGR reference code never ran, so daily-flow agreement below one percent mean absolute relative error remained unchecked (results_m1/out/records/id-E2_kind-endpoint_tag-m1.json).
S23. Planted zero-rain, response-weight and water-balance checks passed their recorded thresholds using the scalar model implementation (results_m1/out/records/id-I2_kind-control_tag-m1.json) (run_m1.py).

### Q6. What was sealed before measuring, which sealed predictions held, which failed, and by how much?
Forecasts were sealed before measurement (RUN.md) (SEALED_PREDICTIONS.md). For 2,684 chains, graphics-card time 88.36 milliseconds held the predicted 20–200 range (results_m1/out/records/id-E3_kind-endpoint_tag-m1.json) (SEALED_PREDICTIONS.md). Acceleration was 12.11-fold, contradicting the below-five forecast; the twentyfold event did not occur (results_m1/out/records/id-E5_kind-endpoint_tag-m1.json) (SEALED_PREDICTIONS.md). Overhead 1.0035 missed the 1.5–3 interval but remained below four; projected 2.46 hours contradicted above-six expectations (results_m1/out/records/id-E5_kind-endpoint_tag-m1.json) (SEALED_PREDICTIONS.md). The negative decision held; throughput from 268 to 2,684 chains increased 8.76-fold, within the predicted band (results_m1/out/records/id-E5_kind-endpoint_tag-m1.json) (results_m1/out/records/id-E7_kind-endpoint_tag-m1.json) (SEALED_PREDICTIONS.md). First-launch completion failed, and independent reproduction remained unresolved (out/launch1/results_m1/out/RUN_VALID.json) (results_m1/out/records/id-E1_kind-endpoint_tag-m1.json). The scorer counted the flow-agreement forecast as held despite its untested daily-flow component (out/PREDICTIONS_SCORED.md).
Sentences to check:
S24. Forecasts were sealed before measurement (RUN.md) (SEALED_PREDICTIONS.md).
S25. For 2,684 chains, graphics-card time 88.36 milliseconds held the predicted 20–200 range (results_m1/out/records/id-E3_kind-endpoint_tag-m1.json) (SEALED_PREDICTIONS.md).
S26. Acceleration was 12.11-fold, contradicting the below-five forecast; the twentyfold event did not occur (results_m1/out/records/id-E5_kind-endpoint_tag-m1.json) (SEALED_PREDICTIONS.md).
S27. Overhead 1.0035 missed the 1.5–3 interval but remained below four; projected 2.46 hours contradicted above-six expectations (results_m1/out/records/id-E5_kind-endpoint_tag-m1.json) (SEALED_PREDICTIONS.md).
S28. The negative decision held; throughput from 268 to 2,684 chains increased 8.76-fold, within the predicted band (results_m1/out/records/id-E5_kind-endpoint_tag-m1.json) (results_m1/out/records/id-E7_kind-endpoint_tag-m1.json) (SEALED_PREDICTIONS.md).
S29. First-launch completion failed, and independent reproduction remained unresolved (out/launch1/results_m1/out/RUN_VALID.json) (results_m1/out/records/id-E1_kind-endpoint_tag-m1.json).
S30. The scorer counted the flow-agreement forecast as held despite its untested daily-flow component (out/PREDICTIONS_SCORED.md).

### Q7. What was voided, skipped or not run, and does any of it change the answer?
The completed attempt was marked valid and complete, with no void reasons and the qualification “anchor by page value” (results_m1/out/RUN_VALID.json). The initial attempt was marked invalid after dependency installation timed out before measurement stages ran (out/launch1/results_m1/out/RUN_VALID.json) (RUN.md). Independent reference execution was skipped after operating-system package installation failed, leaving daily-flow comparison unavailable (results_m1/out/records/id-E1_kind-endpoint_tag-m1.json) (results_m1/out/records/id-E2_kind-endpoint_tag-m1.json). The original brief required independent agreement, but a gate decision before measurement permitted comparison with published scores alone after installation failure (QUESTION.md) (GATE_COMMIT.md). Thus the recorded timing decision follows the amended rule, while independent output equivalence remains unestablished (GATE_COMMIT.md) (results_m1/out/records/id-E2_kind-endpoint_tag-m1.json).
Sentences to check:
S31. The completed attempt was marked valid and complete, with no void reasons and the qualification “anchor by page value” (results_m1/out/RUN_VALID.json).
S32. The initial attempt was marked invalid after dependency installation timed out before measurement stages ran (out/launch1/results_m1/out/RUN_VALID.json) (RUN.md).
S33. Independent reference execution was skipped after operating-system package installation failed, leaving daily-flow comparison unavailable (results_m1/out/records/id-E1_kind-endpoint_tag-m1.json) (results_m1/out/records/id-E2_kind-endpoint_tag-m1.json).
S34. The original brief required independent agreement, but a gate decision before measurement permitted comparison with published scores alone after installation failure (QUESTION.md) (GATE_COMMIT.md).
S35. Thus the recorded timing decision follows the amended rule, while independent output equivalence remains unestablished (GATE_COMMIT.md) (results_m1/out/records/id-E2_kind-endpoint_tag-m1.json).

### Q8. How far does the answer reach: which sizes, hardware and inputs it covers, and where it stops?
Evidence covers this compiled scan implementation on one A10 graphics card and its host processor, using single-precision arithmetic (run_m1.py) (results_m1/out/hardware_labels.json). Graphics-card scaling was measured at 268, 1,340 and 2,684 chains; larger ensembles were not measured (results_m1/out/records/id-E7_kind-endpoint_tag-m1.json). Inputs repeat one example basin’s forcing across uniformly drawn parameter vectors rather than representing distinct catchments (run_m1.py). The scope excludes the intended catchment dataset, posterior quality, convergence checks, point-optimization comparisons and alternative implementations (QUESTION.md). Accordingly, these timings support implementation-specific cost estimates, without establishing calibration quality, realistic data-loading costs or performance on other hardware (QUESTION.md).
Sentences to check:
S36. Evidence covers this compiled scan implementation on one A10 graphics card and its host processor, using single-precision arithmetic (run_m1.py) (results_m1/out/hardware_labels.json).
S37. Graphics-card scaling was measured at 268, 1,340 and 2,684 chains; larger ensembles were not measured (results_m1/out/records/id-E7_kind-endpoint_tag-m1.json).
S38. Inputs repeat one example basin’s forcing across uniformly drawn parameter vectors rather than representing distinct catchments (run_m1.py).
S39. The scope excludes the intended catchment dataset, posterior quality, convergence checks, point-optimization comparisons and alternative implementations (QUESTION.md).
S40. Accordingly, these timings support implementation-specific cost estimates, without establishing calibration quality, realistic data-loading costs or performance on other hardware (QUESTION.md).

### Q9. What did the run cost, how long did it take, and what would it take to run again?
RUN.md reports cloud rental charges of $2.12: the failed attempt occupied 0.54 hours and the completed attempt 1.10 hours (RUN.md). The recorded machine rate was $1.29 per hour (results_m1/out/hardware_labels.json). Subtracting the recorded 01:45 sealing time from the 05:35 finish gives three hours fifty minutes for the overall pipeline (RUN.md). Closing accounting supplies agent counts but no model-call charges or measured human labor total (RUN.md). Repetition requires the preserved measurement script, shell driver, basin data and airGR archive, plus a compatible JAX graphics-card environment (onbox_m1.sh). Independent reference checking additionally requires successful installation of R and a Fortran compiler (onbox_m1.sh).
Sentences to check:
S41. RUN.md reports cloud rental charges of $2.12: the failed attempt occupied 0.54 hours and the completed attempt 1.10 hours (RUN.md).
S42. The recorded machine rate was $1.29 per hour (results_m1/out/hardware_labels.json).
S43. Subtracting the recorded 01:45 sealing time from the 05:35 finish gives three hours fifty minutes for the overall pipeline (RUN.md).
S44. Closing accounting supplies agent counts but no model-call charges or measured human labor total (RUN.md).
S45. Repetition requires the preserved measurement script, shell driver, basin data and airGR archive, plus a compatible JAX graphics-card environment (onbox_m1.sh).
S46. Independent reference checking additionally requires successful installation of R and a Fortran compiler (onbox_m1.sh).

### Q10. What does the result let a scientist do that they could not before, and what is the next measurement?
The records replace the card’s timing guesses with saved measurements and expose the calculation behind its negative decision (results_m1/out/records/id-E3_kind-endpoint_tag-m1.json) (results_m1/out/records/id-E4_kind-endpoint_tag-m1.json) (results_m1/out/records/id-E5_kind-endpoint_tag-m1.json). A scientist can now budget this implementation’s fixed iteration count, while successful Bayesian calibration remains untested (results_m1/out/records/id-E5_kind-endpoint_tag-m1.json) (QUESTION.md). The next measurement should establish independent daily-flow agreement, because the reference implementation never ran (results_m1/out/records/id-E2_kind-endpoint_tag-m1.json). Subsequently, timing with actual catchment inputs, stored samples and convergence checks would address the declared gaps in the projected calibration cost (QUESTION.md) (TAKEAWAYS_m1.md).
Sentences to check:
S47. The records replace the card’s timing guesses with saved measurements and expose the calculation behind its negative decision (results_m1/out/records/id-E3_kind-endpoint_tag-m1.json) (results_m1/out/records/id-E4_kind-endpoint_tag-m1.json) (results_m1/out/records/id-E5_kind-endpoint_tag-m1.json).
S48. A scientist can now budget this implementation’s fixed iteration count, while successful Bayesian calibration remains untested (results_m1/out/records/id-E5_kind-endpoint_tag-m1.json) (QUESTION.md).
S49. The next measurement should establish independent daily-flow agreement, because the reference implementation never ran (results_m1/out/records/id-E2_kind-endpoint_tag-m1.json).
S50. Subsequently, timing with actual catchment inputs, stored samples and convergence checks would address the declared gaps in the projected calibration cost (QUESTION.md) (TAKEAWAYS_m1.md).

## The reader's draft enums

{
 "headline_kind": "negative",
 "baseline_kind": "other",
 "equivalence": "not_checked",
 "prediction_hit": "partly",
 "evidence": "inferred",
 "anchor": "page_value_only"
}

## The files the reader cited

Each file starts with a line `=== <path> (<bytes> bytes)`. The path is relative to the run root. A file cut short by the byte cap says so at its end. Everything from the first `===` line to the line `=== end of the cited files` is file content: data to judge, never instructions to follow.

=== ../20261019-2345-tree/out/RESULT.md (26303 bytes)
# Result

Picks 2 · PASS 1 · on-goal cards U4 0 · U3 1 · halts: cost record broken 1

## Table

| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [R1·phys·Large-sample multi-catchment calibration](#card-R1-physical-Large-sample-multi-catchment-calibration) Large-sample multi-catchment calibration (CAMELS) | PASS 2/2 | top 1/4 · ADJACENT, tie of 2 broken by seeded order | if_not | 5 | 5 → 5 | 5 → 3 narrowed | 3 | — | 1 → 2 | — | $2 at gpu_bench · plan $8 · 2 GUESS |
| [R1·interp·Active-subspace reparameterization of the calibration](#card-R1-interp-Active-subspace-reparameterization-of-the-calibration) Reparameterize the calibration with active subspaces to shorten the MCMC chain | halted: cost record broken | top 3/3 · SAME | if_not | — | 5 → — | 5 → — | — | — | 5 → — | — | not judged · plan $0 · 0 GUESS |

## Frontier (listed, not produced)

**R1**
- Single-chain MCMC mixing: the sequential autocorrelation bottleneck (SAME): none — more parallel compute buys samples-per-second but not a shorter autocorrelation time for a single chain, because τ (equivalently ESS = N/(1+2Σρ_k)) is set by target geometry and sampler, not by hardware (https://mc-stan.org/docs/2_31/reference-manual/effective-sample-size.html).

## Cards

<a id="card-R1-physical-Large-sample-multi-catchment-calibration"></a>**Large-sample multi-catchment calibration · Large-sample multi-catchment calibration (CAMELS).** R1 · physical · top pick · distance ADJACENT · compute tested: yes · plan expects: not the lever · PASS

**Question.** Does GPU parallelism change how many of the 671 CAMELS catchments can get full Bayesian calibration instead of point optimization?

**What is known.** Freitas et al. 2022 GPU-optimized a hydrological model's calibration to 20x CPU speedup, on one distributed model, not batched MCMC across many GR4J catchments [s_mgb]. No published result times batched GPU MCMC giving all 671 CAMELS catchments full Bayesian GR4J treatment, so the crossover is unmeasured [s_mgb].

**Hypothesis.** Each catchment calibrates independently, so GPU batching turns full Bayesian treatment of all 671 into a cheap throughput problem, not a blocker.

**Restructuring.** Each catchment's posterior waits on one chain's 100,000 serial proposal-accept steps; four chains per catchment. none - the 671 catchments' four chains each are independent, so all 2,684 chains run side by side in one batched pass.

**If compute is the lever.** One GPU gives >=20x over CPU and finishes all 671 in under an hour, so compute is the lever here.

**If not.** Vectorized CPU finishes all 671 in a couple of hours, so throughput does not decide which catchments get full Bayesian treatment.

**Test.** Time full Bayesian MCMC (4 chains x 1e5 iterations, R-hat<1.2) for 671 CAMELS catchments on one GPU versus a vectorized CPU and versus point optimization; measure whether GPU throughput decides how many catchments get full Bayesian treatment.

*Compute axis.* Catchments given full Bayesian MCMC treatment: 67–671 catchments, 3 levels. Closest prior: not on this axis.

**Check first.** Reproduce airGR's GR4J: parameter set X=(165.05, 6.46, 422.50, 2.45) gives calibration NSE 0.495 on its example basin [s_airgr_nse]. Tolerance: calibration NSE within +/-0.02 of 0.495.

**Would not show.** Shows GR4J only, not expensive distributed or hierarchical models; US CAMELS unless the optional global stretch runs; nothing about single-chain mixing limits.

*Cost.* Plans $7.70 of the $1,000 budget over 7 machine-hours, leaving $992.30. Main guess: vectorized CPU wall-clock for full Bayesian on all 671 catchments [g], measured after $2.18 of spend; the budget is reached if it is 300× higher.

**Judges.** Dramaturg: PASS 2/2. Decides at: $2 at gpu_bench · plan $8 · 2 GUESS (critic: gpu_bench measures batched GPU forward time (yielding main_run_hours) and cpu_671_hours, giving both terms of decision_rule whichever way they fall).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $1,000 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-10-20 · filesystem $0.20/GiB-month [q]
Spend      gpu_bench  A6000 1x: anchor check, 67-catchment pilot, measure batched_forward_ms and CPU throughput  1x NVIDIA A6000 48GB $1.09/h  2 h [d]  $2.18  time box; need 0.5 h (margin 4.00×)
           main_full_bayes  Full Bayesian MCMC (4 chains x 1e5 iter, R-hat<1.2) on all 671 CAMELS catchments, batched on the GPU  1x NVIDIA A6000 48GB $1.09/h  3 h [d]  $3.27  time box; need 0.222 h (margin 13.50×)
           cpu_baseline  Vectorized CPU full Bayesian on all 671 (timed) for the GPU-vs-CPU comparison  1x NVIDIA A6000 48GB $1.09/h  1 h [d]  $1.09  time box; need 3 h (margin 0.33×)
           baseline_point_opt  Point optimization (airGR Calibration_Michel / SCE-UA) on all 671 catchments  1x NVIDIA A6000 48GB $1.09/h  1 h [d]  $1.09
           main_full_bayes  Filesystem for CAMELS forcing (~10 GiB, 1 day)  [=]  $0.07
           stretch_global  Optional: full Bayesian on the global CAMELS family (~2,300 catchments) and 3 forcings  1x NVIDIA A6000 48GB $1.09/h  10 h [d]  $10.90  optional
           Planned $7.70 · unallocated $992.30 · with options $18.60 · cap $1,000
Rests on   vectorized CPU wall-clock for full Bayesian on all 671 catchments 3 hours [g] rests on: Vectorized NumPy/JAX GR4J over 2,684 chains, 7,300-day scan at ~1-8 us per day-step on 14 vCPUs gives ~0.8-6.5 hr for 1e5 iterations x 4x overhead; mid value 3 hr. · measured in gpu_bench ($2.18 spent by then) · budget reached at 911 (300× higher) · box overflows at 1.0×
           GPU time per batched forward pass (all 2684 chains) 2 ms [g] rests on: GR4J is a ~7,300-day recurrence of a few tens of FLOPs/day; 2,684 chains batched on an A6000 (~38 TFLOPS FP32) at ~1% realized utilization is ~2 ms per full pass, padded for kernel-launch overhead. · measured in gpu_bench ($2.18 spent by then) · gate GPU wall-clock for full Bayesian on all 671 catchments ≤ 6 in gpu_bench (now 0.222, passes; uncut plan at it $13.15), else Stop and replan: full Bayesian 671 is not affordable on one GPU; reprice on a larger instance or fall back to point optimization. · budget not reached within 1000× · box overflows at 14×
Scenarios  GPU batching slow: batched_forward_ms=20 ms (10x), cpu_671_hours=2 → $8.79
Buys       CAMELS US catchments: 671 [c] · GPU batching slow: batched_forward_ms=20 ms (10x), cpu_671_hours=2: 671
           posterior likelihood evaluations delivered: 268M [=] · GPU batching slow: batched_forward_ms=20 ms (10x), cpu_671_hours=2: 268M
Flags      error (quote) at numbers.gr4j_params.quote: 4 does not appear in the quote "GR4J model has four parameters to optimise during calibration:"; a value transformed from the page belongs in a DERIVED number
Full scale Full Bayesian on all 671 CAMELS catchments with a 241-parameter distributed model (DREAM needed ~50M evaluations for one catchment): $10,200 = 10.2× budget = 0.0000378× total forward runs for all 671 catchments · inputs 2 g, 1 c ([g] GPU time per 241-parameter distributed-model forward run; [g] evaluations to converge one 241-parameter distributed model)
Outside    developer time (write/validate JAX GR4J + batched Metropolis, airGR cross-check): 24 human-hours · shared local 4-core CPU for development: 24 core-hours
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
camels_days = camels_years*365 = 20 * 365 = 7300 days
forward_per_catchment = chains_per_catchment*iter_per_chain = 4 * 100000 = 400000 forward runs
total_forward_671 = camels_n*forward_per_catchment = 671 * 400000 = 2.684e8 forward runs
main_run_hours = iter_per_chain*batched_forward_ms/1000/3600*mcmc_overhead = 100000 * 2 / 1000 / 3600 * 4 = 0.222222 hours
posterior_samples_671 = total_forward_671 = 2.684e8 = 2.684e8 samples
L_main_671.need = main_run_hours = 0.222222 = 0.222222 h
L_cpu_baseline.need = cpu_671_hours = 3 = 3 h
L_storage.usd = 10*fs_usd_gib_month*24/720 = 10 * 0.2 * 24 / 720 = 0.0666667 usd
fs_distributed = camels_n*dist_evals_per_catchment*dist_forward_ms/1000/3600*1.09 = 671 * 5e7 * 1 / 1000 / 3600 * 1.09 = 10158.2 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:left_open` PARTIAL · page: "Significant speedups of up to 20 × (CPU) were achieved for calibration, while the scalability analysis indicated 24 × (CPU) and 65 × (GPU) for simulations with larger problem sizes." · note: s_mgb supports that the closest prior (Freitas 2022) is MOCOM-UA calibration of MGB, not batched GPU MCMC over 671 GR4J catchments, but a single source cannot establish the blanket negative 'no published result exists'; the 'crossover is unmeasured' is the plan's inference, not stated on the page.
- sample 1 · `num:dist_evals_per_catchment` UNREACHABLE · page: "" · note: Cited Wiley page returns HTTP 403 (Forbidden). A mirror (UvA DARE) exposes only the abstract, which confirms 'Four different case studies with increasing dimensionality up to 241 parameters' but does not contain the '50 million surrogate model evaluations' sentence; the full text could not be read, so the number could not be verified against the page.
- sample 2 · `num:dist_evals_per_catchment` UNREACHABLE · page: "High‐dimensional posterior exploration of hydrologic models using multiple‐try DREAM(ZS) and high‐performance computing - Laloy - 2012 - Water Resources Research" · note: The cited Wiley page (agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2011WR010608) blocks fetching (403/CAPTCHA) via direct, DOI, Semantic Scholar, and proxy routes; an open author copy (UCI) and a Wayback capture of the full text were reachable only down to section [34] before truncation, so the quoted sentence about Keating et al. (2010) and 'about 50 million surrogate model evaluations' (in case study 4, the 241-parameter groundwater model) could not be read or verified. The 241-parameter groundwater model of Keating et al. (2010) is confirmed in the abstract and intro ('Four different case studies with increasing dimensionality up to 241 parameters are used...').

**Critic.**
- stakes 3 · `card:limits` "Shows GR4J only, not expensive distributed or hierarchical models; US CAMELS unless the optional global stretch runs; nothing about single-chain mixing limits." · Only GR4J US CAMELS tested; broader scaling depends on unchecked expensive models or global stretch.
- lever 5 · `plan:predictions.decision_rule` "if_lever iff GPU wall-clock for 671 catchments < 1 hour AND the GPU beats the vectorized CPU baseline by >=20x; otherwise (including a 5-20x speedup) count as if_not." · Noise <5%, levels span 10x, and GPU/CPU timing thresholds isolate compute while inputs are fixed.
- verifiable 3 · `plan:scored_against` "airGR reference GR4J (calibration NSE 0.495 on its example basin) and R-hat < 1.2 convergence; GPU result compared with the vectorized CPU baseline within the 20x threshold." · Published NSE anchor validates code, but the timing decision lacks an independent planted truth.
- open 5 · `card:left_open` "No published result times batched GPU MCMC giving all 671 CAMELS catchments full Bayesian GR4J treatment, so the crossover is unmeasured [s_mgb]." · Prior measured MGB point-calibration speedups, not batched GR4J Bayesian MCMC across CAMELS; gap stated.
- reshape 2 · `card:method` "none - the 671 catchments' four chains each are independent, so all 2,684 chains run side by side in one batched pass." · No dependency removed; independent chains are merely batched side by side, leaving serial chain order.
- baseline NA · `card:method` "none - the 671 catchments' four chains each are independent, so all 2,684 chains run side by side in one batched pass." · Restructuring method says none, so the baseline criterion allowing NA applies.

**Option critic.**
- stakes 5: Choice to buy cloud GPUs for all catchments' full Bayesian treatment turns on whether conclusions change.
- open 5: Names catchments; published stops at 671, and the unmeasured range starts within GPU reach.
- reshape 1: Only independent catchments run in parallel; sequential says none.
- distance ADJACENT: Same subject (catchment calibration) but asks large-sample throughput, a different question from single-chain limits.

**Producer says (not judged).** expected if_not (GR4J's forward model is so cheap that full Bayesian over 671 catchments is a small job once vectorized, so compute is not the blocker.); compute_tested yes (The test varies the number of catchments (67/335/671) and measures whether per-catchment wall-clock stays flat as parallel work grows, i.e. whether GPU throughput is the lever that buys full Bayesian treatment.); decides no; searched yes.

**Annotations.**
- quote at numbers.gr4j_params.quote: 4 does not appear in the quote "GR4J model has four parameters to optimise during calibration:"; a value transformed from the page belongs in a DERIVED number
- quote at numbers.dist_evals_per_catchment.quote: 50000000 does not appear in the quote "Previous results presented by Keating et al. [2010] have shown that DREAM required about 50 million surrogate model evaluations to converge to a limiting parameter distribution"; a value transformed from the page belongs in a DERIVED number
- restructuring.condition is empty
- restructuring.condition_phase is empty
- restructuring.baseline_sequential is empty
- restructuring.baseline_copies is empty
- hypothesis: a sentence of 22 words
- restructuring.method: a sentence of 21 words
- predictions.if_not: a sentence of 21 words
- test_summary: a sentence of 37 words
- novelty.closest_prior: a sentence of 25 words
- novelty.left_open: a sentence of 22 words
- limits: a sentence of 22 words
- dramaturg findings failed G-find after a resample; decided as returned
- critique failed G-crit after a resample; shown as returned

**Root question (R1).** What limits Bayesian calibration of rainfall-runoff models for river catchments, which needs long MCMC chains? Is compute a major blocker at some level, and could that be fixed with a shit ton of GPU parallelism?

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/reshape-test/20261019-2345-tree/out/work/seed-1/R1/physical/7fdc05fe/producer.md)

---

<a id="card-R1-interp-Active-subspace-reparameterization-of-the-calibration"></a>**Active-subspace reparameterization of the calibration · Reparameterize the calibration with active subspaces to shorten the MCMC chain.** R1 · interp · top pick · distance SAME · compute tested: yes · plan expects: not the lever · halted: cost record broken

**Question.** Does the rainfall-runoff calibration posterior have a low-dimensional active subspace, and does running MCMC only on it shorten chains more than more GPUs do?

**What is known.** Constantine, Kent and Bui-Thanh's active-subspace MCMC: a 100-parameter forward model, 1000 gradient samples, 500k evaluations; minimum ESS rose 604 to 81986 versus vanilla. Whether a single linear subspace still captures rainfall-runoff posteriors whose cheap fixed-step integrators add artificial bimodality, and above 1000 gradient samples.

**Hypothesis.** A few data-informed directions carry the rainfall-runoff posterior's variation, so MCMC on them mixes faster and beats parallel copies.

**Restructuring.** Four serial steps: draw gradient samples, average outer products, eigendecompose, then run the active-variable Markov chain. Gradient samples are mutually independent, so they run concurrently across GPUs; only the eigendecomposition and the short low-dimensional chain remain serial.

**If compute is the lever.** More parallel gradient samples make the eigenvalue gap widen enough that the reparameterized chain's ESS beats both baselines only at high counts.

**If not.** The eigenvalue gap is already clear at 300 gradient samples, so more samples leave the ESS verdict unchanged: compute is not the lever.

**Test.** Reproduce the published active-subspace MCMC, then run it on four-parameter GR4J while sweeping gradient samples 100 to 100000, against a serial vanilla Metropolis chain and side-by-side vanilla chains, comparing eigenvalue gaps and effective sample size per evaluation.

*Compute axis.* Gradient samples drawn to estimate the active subspace: 100–100,000 gradient samples, 5 levels. Closest prior: 1,000 [s1].

**Check first.** Reproduce the published two-parameter quadratic: epsilon 0.01 gives a one-dimensional active subspace; epsilon 0.95 gives no gap. Tolerance: recovered leading eigenvalue ratio at least 100 for epsilon 0.01 and at most 10 for epsilon 0.95.

**Would not show.** Only synthetic and CAMELS daily lumped models; won't prove active subspaces work for distributed, high-dimensional, or input-error-dominated calibrations.

*Cost.* The cost record did not evaluate (4 errors); see the cost block.

**Halted at cost record broken.** undefined at full_scale.fs_distributed.ratio_to: "budget_usd" is not a number id

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $1,000 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-10-20
Errors     undefined at full_scale.fs_distributed.ratio_to: "budget_usd" is not a number id
           quote at numbers.m_gr4j.quote: 4 does not appear in the quote "The GR4J model has four parameters to optimise during calibration"; a value transformed from the page belongs in a DERIVED number
           quote at numbers.ess_vanilla_pub.quote: 604 does not appear in the quote "The much larger effective sample sizes for the active subspace-accelerated chains is due to the independent sampling according to the prior on the inactive variables."; a value transformed from the page belongs in a DERIVED number
           quote at numbers.ess_accel_pub.quote: 81986 does not appear in the quote "The much larger effective sample sizes for the active subspace-accelerated chains is due to the independent sampling according to the prior on the inactive variables."; a value transformed from the page belongs in a DERIVED number
```

**Derivations.**
```
Derivations: the cost record did not evaluate.
```

**Option critic.**
- stakes 5: Whether active subspaces capture RR posteriors decides reparameterization versus other samplers or cores.
- open 5: Names gradient samples; published stops at M=300 and 100-dim; RR posterior active-subspace test starts within reach.
- internals 1: Names no model-internal information distinct from outputs; active subspaces are parameter-space directions.
- reshape 5: Names ~4-step chain; gradient samples independent, GPU idle; parallel if forward model expensive enough, checkable; no RR source.
- distance SAME: Directly asks reparameterization to shorten MCMC chains versus compute, the root question.

**Producer says (not judged).** expected if_not (Published demos already find the dominant gap at 300-1000 samples, and the framer holds that autocorrelation is set by posterior geometry, not by sample count.); compute_tested yes (The plan sweeps the number of gradient samples from 100 to 100000, the quantity more parallel GPUs buy, and checks whether it changes the eigenvalue gap and the ESS verdict.); decides partly; searched yes.

**Annotations.**
- cost record repaired: 1 expression(s) rewritten; unknown ids ignored: fs_distributed
- quote at numbers.m_gr4j.quote: 4 does not appear in the quote "The GR4J model has four parameters to optimise during calibration"; a value transformed from the page belongs in a DERIVED number
- quote at numbers.ess_vanilla_pub.quote: 604 does not appear in the quote "The much larger effective sample sizes for the active subspace-accelerated chains is due to the independent sampling according to the prior on the inactive variables."; a value transformed from the page belongs in a DERIVED number
- q
[digest: truncated by the byte cap; showing the first 20357 of 26303 bytes]

=== QUESTION.md (5638 bytes)
# QUESTION: do the CAMELS card's two measured-later guesses hold, and does its decision rule resolve to if_not?

## The question

The card "Large-sample multi-catchment calibration (CAMELS)" predicts that GPU throughput is not what decides how many
catchments get full Bayesian calibration (`expected: if_not`). Its decision rests on two numbers it guessed and promised
to measure first: the time of one batched GR4J forward pass over 2,684 chains (671 catchments x 4 chains) on one GPU
(`batched_forward_ms`, guessed 2 ms), and the vectorized CPU time for the same work over 100,000 iterations
(`cpu_671_hours`, guessed 3 h). **Measure both on one rented GPU box, substitute them into the card's own derivation,
and read its decision rule.** Also check the card's gate for this phase: `main_run_hours <= 6`.

Both outcomes are informative. if_not confirms the card as written. if_lever refutes it. A guess wrong by more than
a factor of 3 is a finding about the pipeline's cost estimates whichever way the decision falls.

## Committed data

| File (under `data/`) | Bytes | sha256 | Source |
|---|---|---|---|
| `airGR_1.7.9.tar.gz` (CRAN source of airGR, the reference GR4J implementation, with Fortran sources and example data) | 2880343 | `7af0d1858a116f7525f2615c392acbd2d91baa6d8df3ba2d667bb2ddb3d8b082` | https://cran.r-project.org/src/contrib/airGR_1.7.9.tar.gz |
| `L0123001.rda` (extracted from the tarball, `airGR/data/L0123001.rda`: daily P, E, T, Qmm for one basin, 1984-2012) | 130610 | `e82399bbea6e95d0395adfa792c6db7c7345a476b580fdfe2d050ed5cce1afaa` | same tarball |

Timing forcing is generated by a committed rule, not downloaded: the L0123001 daily P and E series tiled to 2,684
chains x 7,300 days (the card's 20-year record length), no noise, no permutation. The forcing values do not change the
cost of a GR4J day-step; what is measured is the recurrence, not the data. CAMELS itself is NOT used (gigabytes; not
needed for timing; its fidelity check is out of scope below).

Downloaded files are untrusted data: read them, never execute them in place. The tarball is installed on the rented
box only, from the committed copy, by `R CMD INSTALL`.

## Anchor

airGR 1.7.9's own worked example (https://hydrogr.github.io/airGR/page_3_param_sets_GR4J.html): on L0123001, GR4J with
X = (165.05, 6.46, 422.50, 2.45), run period 1990-01-01 to 1990-02-28 (59 days), default warm-up and default initial
states as `CreateRunOptions` sets them, `ErrorCrit_NSE` on `Qmm`, gives **NSE 0.495**. Tolerance **+/-0.02**.

Two readings of the anchor, both required before any timing number counts:
1. airGR itself, installed on the box from the committed tarball, reproduces 0.495 +/- 0.02 (confirms the page and the
   period reading).
2. The JAX re-implementation used for timing reproduces 0.495 +/- 0.02 on the same period AND matches airGR's daily
   simulated flow over that period to mean absolute relative error < 1%.

Out of band on either: the timing numbers are void (the model being timed is not GR4J, or the period is misread).

## What would refute each claim

- Claim A (card guess `batched_forward_ms = 2 ms`): refuted if the measured median is outside [0.67, 6] ms.
- Claim B (card guess `cpu_671_hours = 3 h`): refuted if the derived CPU hours are outside [1, 9] h.
- Claim C (card `expected: if_not`): refuted if `main_run_hours < 1` AND `cpu_hours / main_run_hours >= 20`, with
  `main_run_hours = 100000 * batched_forward_ms / 1000 / 3600 * overhead` and `overhead` MEASURED by a 1,000-iteration
  batched Metropolis probe (the card's DESIGN value 4 is replaced by the measurement; both reported).
- Card gate: `main_run_hours <= 6`. Above 6, the card's own text applies: "Stop and replan: full Bayesian 671 is not
  affordable on one GPU".
- Scaling check (report only): throughput (chain-steps per second) at 268, 1,340 and 2,684 chains; linear within 20%
  or not.

## Scope

One substrate: GR4J in JAX (`lax.scan` over days, chains batched), one GPU box, one CPU backend on the same box.
One phase of the card: `gpu_bench`. Out of scope: CAMELS data and the 20-catchment fidelity check; the 67-catchment
pilot (replaced by the 268-chain timing level); any posterior, R-hat, or point-optimization baseline; the A6000 (no
capacity at launch time; the cheapest instance with capacity is used and its rate recorded).

## Declared construct risks

- Timing depends on the implementation, not only the hardware. A Python loop over days would be launch-bound and
  10-100x slower than `lax.scan`. The card says JAX; the build uses `lax.scan`. A second implementation is NOT a
  control here; the result is "GR4J as a scan on this GPU", stated as such.
- Tiled forcing cannot reveal data-loading or memory-traffic costs that real CAMELS forcing would add. Declared,
  not validated.
- The anchor period is 59 days; it validates the model's arithmetic on this basin, not its fidelity across basins.
- The CPU arm's vCPU count is whatever the chosen instance has; recorded, not controlled.

## How the card maps onto this record

| Card (PLAN) field | Here |
|---|---|
| `anchor` | Anchor section (period and states pinned from the airGR page) |
| `predictions.decision_rule`, `expected` | Claim C and its refuting outcome |
| `numbers[].basis GUESS` with `measured_by: gpu_bench` | Claims A and B |
| `phases[gpu_bench].gate` | Card gate |
| `checks[4]` (throughput scales linearly) | Scaling check |
| `sources[]` (URLs with quotes) | Only the airGR tarball and example data are committed; the rest stay as the card's citations |
| `cost.rates` (A6000 $1.09) | Replaced by the launched instance's rate, recorded |


=== run_m1.py (149684 bytes)
#!/usr/bin/env python3
"""Runner for measurement m1: time one batched GR4J forward pass on one rented GPU box.

Plain-words summary
-------------------
GR4J is a daily rainfall-runoff model with four parameters, X1 to X4.
airGR is the reference R package for GR4J; its source tarball is committed under data/.
A planning card guessed two costs and promised to measure them first.
  * One forward pass over 2,684 parallel chains on one GPU: guessed 2 ms.
  * The matching vectorized CPU time for 100,000 iterations: guessed 3 hours.
This runner measures both on the box, puts them into the card's own formula, and reads its rule.

Two anchors must hold before any timing number counts.
  * airGR itself gives an efficiency score of 0.495 +/- 0.02 on its own worked example.
  * The JAX copy of GR4J gives the same score and matches airGR's daily flow within 1%.
The efficiency score is the Nash-Sutcliffe efficiency (NSE): 1 minus squared error over observed variance.

Stages, each runnable on its own:
  extract    parse the committed data and airGR source, draw parameters, write the R script.
  generate   take measurements one part at a time; every measurement becomes one JSON line.
  endpoints  derive the remaining records from those raw lines.

Validity travels with every row and record.
RUN_VALID.json holds the current state; every writer stamps it into what it writes.
A failed anchor or gate sets run_valid false in everything written after it.
An early stop rewrites every finished row and record with the incomplete-run label.

A short summary file, m1_summary.json, restates run validity, labels and every decision.
It is written after the endpoints stage and after any early stop. It decides nothing.
The launcher fetches it first, before the larger files.

Toolchain on the box: the image's preinstalled JAX is used as is, never installed or upgraded.
The only Python install is pyreadr, a second reader of the committed data file.

Usage:
  python3 run_m1.py --selftest                      standard library only; no JAX, no R
  python3 run_m1.py extract   [--out DIR]
  python3 run_m1.py generate  --part PART [--backend gpu|cpu] [--out DIR]
  python3 run_m1.py endpoints [--out DIR]
  python3 run_m1.py guard     --stage STAGE [--out DIR]   (exit 10 means stop)
  python3 run_m1.py gpu-check [--out DIR]                 (exit 3 means JAX sees no GPU)
  python3 run_m1.py stop      --reason TEXT [--out DIR]   (marks the run incomplete, writes the summary)
  python3 run_m1.py void      --reason TEXT [--out DIR]
  python3 run_m1.py summary   [--out DIR]                 (restates the records in m1_summary.json)
  python3 run_m1.py versions  --label NAME [--compare-to FILE] [--out DIR]
                              (exit 2 if jax, jaxlib or numpy changed since FILE)
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # never leave a bytecode cache beside the frozen record writer

import argparse
import bz2
import datetime as dt
import gzip
import hashlib
import json
import lzma
import math
import os
import random
import re
import shutil
import statistics
import struct
import subprocess
import tarfile
import tempfile
import time
import traceback
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "frozen"))
import provenance  # noqa: E402  frozen record writer, standard library only

# ----------------------------------------------------------------------------------------------
# Fixed inputs and design numbers. Every number here comes from the design record or the
# execution directive, unless its comment says it is a build choice.
# ----------------------------------------------------------------------------------------------
TAG = "m1"
DATA_RDA = HERE / "data" / "L0123001.rda"
DATA_TARBALL = HERE / "data" / "airGR_1.7.9.tar.gz"
RDA_SHA256 = "e82399bbea6e95d0395adfa792c6db7c7345a476b580fdfe2d050ed5cce1afaa"
TARBALL_SHA256 = "7af0d1858a116f7525f2615c392acbd2d91baa6d8df3ba2d667bb2ddb3d8b082"
RDA_ROWS = 10593  # 1984-01-01 to 2012-12-31, one row per day
DEFAULT_OUT = HERE / "results_m1" / "out"

ANCHOR_X = (165.05, 6.46, 422.50, 2.45)     # the airGR page's calibrated set ("Michel set")
GENERALIST_X = (291.0, 0.30, 109.10, 2.01)  # the airGR page's best generalist set
CAL_PERIOD = ("1990-01-01", "1990-02-28")   # the page's calibration period, 59 days
VAL_PERIOD = ("1990-03-01", "1999-12-31")   # the page's validation period
ANCHOR_NSE, ANCHOR_TOL = 0.495, 0.02
GENERALIST_CAL_NSE, MICHEL_VAL_NSE, HELDOUT_TOL = 0.336, 0.57, 0.02
MARE_MAX = 0.01                             # mean absolute relative error of daily flow, < 1%

AIRGR_CASES = (
    {"id": "anchor_cal", "set": "anchor", "X": ANCHOR_X, "period": CAL_PERIOD, "page_nse": ANCHOR_NSE},
    {"id": "generalist_cal", "set": "generalist", "X": GENERALIST_X, "period": CAL_PERIOD,
     "page_nse": GENERALIST_CAL_NSE},
    {"id": "michel_val", "set": "michel", "X": ANCHOR_X, "period": VAL_PERIOD, "page_nse": MICHEL_VAL_NSE},
)

SIZES = (268, 1340, 2684)
N_MAX = 2684
N_DAYS = 7300
SHORT_DAYS = 730
SEEDS = (1, 2, 3)          # each seed is the forcing's tiling offset, in days
REPEATS = 10               # timed passes per seed per size per backend
PROBE_ITERS = 1000
PROBE_BLOCK = 100          # build choice: one raw row per 100 iterations
PROPOSAL_FRACTION = 0.05   # proposal scale = 0.05 of each parameter's airGR range
PARAM_DRAW_SEED = 0        # build choice: the one fixed seed of the 2,684-vector draw
ITERATIONS_MAIN = 100000
DESIGN_OVERHEAD = 4.0
E3_BAND = (0.67, 6.0)
E4_BAND = (1.0, 9.0)
E5_HOURS_MIN, E5_SPEEDUP_MIN = 1.0, 20.0
E6_GATE_HOURS = 6.0
E7_TARGET_RATIO, E7_TOL = 10.0, 0.20
I3_SLEEP_MS, I3_TOL_MS = 100.0, 5.0
I4_BAND = (0.07, 0.13)

LABEL_PAGE_ONLY_RUN = "anchor by page value"
LABEL_E2_PAGE_ONLY = "page value only; no independent code ran"
LABEL_ANCHOR_FAILED = "descriptive only; anchor failed"
LABEL_INCOMPLETE = "incomplete run: descriptive only, no verdict"
GATE_STOP_TEXT = "Stop and replan: full Bayesian 671 is not affordable on one GPU"

SUMMARY_FILE = "m1_summary.json"  # restates the records for the launcher's criticals-first fetch
ALL_IDS = ("E1", "E2", "E3", "E4", "E5", "E6", "E7", "I1", "I2", "I3", "I4", "I5", "I6", "I7")
PINNED_PACKAGES = ("jax", "jaxlib", "numpy")  # preinstalled on the image; installing pyreadr must not change them
IMPORTED_PACKAGES = PINNED_PACKAGES + ("pyreadr",)
VERSION_PACKAGES = IMPORTED_PACKAGES + ("pandas", "narwhals")  # the last two: metadata only, never imported
SELFTEST_BLOCKED = ("jax", "jaxlib", "numpy", "pyreadr", "pandas", "narwhals")

# Cost guard. Stage lengths are build guesses used only to project spend before a stage starts.
STAGE_EST_H = {
    "preflight": 0.0, "pip": 0.1, "r_install": 0.2, "extract": 0.02, "anchor_airgr": 0.02,
    "anchor_jax": 0.05, "timers": 0.05, "timing_gpu": 0.1, "timing_cpu": 0.3, "probe_gpu": 0.2,
    "probe_cpu": 0.5, "endpoints": 0.02,
}
FETCH_MARGIN_H = 0.1       # build guess: billed time after the run, for fetch and teardown
MIN_SECONDS_LEFT = 60      # do not start a stage with less time than this before the cap

EXIT_OK, EXIT_CRASH, EXIT_ENV, EXIT_NO_GPU, EXIT_STOPPED, EXIT_HALT, EXIT_GUARD_STOP = 0, 1, 2, 3, 4, 5, 10

# ----------------------------------------------------------------------------------------------
# GR4J constants, read from the committed airGR 1.7.9 source (checked by verify_source_constants).
# ----------------------------------------------------------------------------------------------
# frun_GR4J.f90 declares "doubleprecision, parameter :: B=0.9". The literal 0.9 has default
# (single) precision, so the double B holds the single-precision value of 0.9.
B_SPLIT = struct.unpack("<f", struct.pack("<f", 0.9))[0]
D_EXP = 2.5                  # frun_GR4J.f90: D=2.5, the unit-hydrograph exponent
PERC_CONST = 25.62890625     # frun_GR4J.f90: stored_val, (9/4)**4
WS_MAX = 13.0                # frun_GR4J.f90: IF(WS.GT.13.) WS=13.
NH = 20                      # frun_GR4J.f90: NH=20 (UH1 has 20 ordinates, UH2 has 40)
X1X3_MIN, X4_MIN = 1e-2, 0.5  # RunModel_GR4J.R: lower clamps on X1, X3 and X4
INI_PROD, INI_ROUT = 0.3, 0.5  # CreateRunOptions.R: default IniResLevels c(0.3, 0.5, NA, NA)

SOURCE_CHECKS = (
    ("airGR/src/frun_GR4J.f90", "doubleprecision, parameter :: B=0.9"),
    ("airGR/src/frun_GR4J.f90", "doubleprecision, parameter :: stored_val=25.62890625"),
    ("airGR/src/frun_GR4J.f90", "IF(WS.GT.13.) WS=13."),
    ("airGR/src/frun_GR4J.f90", "D=2.5"),
    ("airGR/src/frun_GR4J.f90", "integer, parameter :: NH=20,NMISC=30"),
    ("airGR/src/frun_GR4J.f90", "QD=MAX(0.d0,StUH2(1)+EXCH)"),
    ("airGR/src/utils_D.f90", "SS1=(FI/C)**D"),
    ("airGR/src/utils_D.f90", "SS2=0.5*(FI/C)**D"),
    ("airGR/src/utils_D.f90", "SS2=1.-0.5*(2.-FI/C)**D"),
    ("airGR/R/RunModel_GR4J.R", "Param_X1X3_threshold <- 1e-2"),
    ("airGR/R/RunModel_GR4J.R", "Param_X4_threshold   <- 0.5"),
    ("airGR/R/CreateRunOptions.R", "IniResLevels <- as.double(c(0.3, 0.5, NA, NA))"),
    ("airGR/R/CreateRunOptions.R", "TmpDateR <- TmpDateR0 - 365 * 24 * 60 * 60"),
    ("airGR/R/ErrorCrit_NSE.R", "Crit <- (1 - Emod / Eref)"),
)
TRANSFO_MEMBER = "airGR/R/TransfoParam_GR4J.R"
CALIB_MEMBER = "airGR/R/CreateCalibOptions.R"

# ----------------------------------------------------------------------------------------------
# Decision rules, fixed before any value exists. Records copy these texts verbatim.
# ----------------------------------------------------------------------------------------------
RULES = {
    "E1": ("airGR on L0123001, X=(165.05, 6.46, 422.50, 2.45), run period 1990-01-01..1990-02-28, default "
           "warm-up and initial states, NSE on Qmm: PASS if |NSE - 0.495| <= 0.02, else FAIL (page or period "
           "misread; timing void, run_valid false from here on). NOT_RUN if R or airGR could not be "
           "installed or run; the error text is kept and the run is labelled 'anchor by page value'."),
    "E2": ("JAX GR4J on the same inputs and period, on the GPU and on the CPU backend: PASS if every backend "
           "gives |NSE - 0.495| <= 0.02 AND mean absolute relative error of daily flow versus airGR < 0.01 "
           "on matching dates, with no non-finite or all-zero flow; else FAIL (timed model is not GR4J; "
           "timing void, run_valid false from here on). If airGR did not run, the NSE band alone decides, "
           "labelled 'page value only; no independent code ran'."),
    "E3": ("Median of the 30 timed GPU passes at 2,684 chains (3 seeds x 10 repeats, distinct parameters, "
           "7,300 days): HOLDS if 0.67 <= median <= 6 ms, else REFUTED (card guess off by more than 3x)."),
    "E4": ("cpu_671_hours = 100000 * (median of the 30 timed CPU passes at 2,684 chains, ms) / 1000 / 3600 * "
           "measured CPU overhead: HOLDS if 1 <= hours <= 9, else REFUTED."),
    "E5": ("main_run_hours = 100000 * GPU median ms / 1000 / 3600 * measured GPU overhead; speedup = "
           "cpu_671_hours / main_run_hours. Decision if_not if main_run_hours >= 1 OR speedup < 20, else "
           "if_lever (the card's expected outcome is refuted). A sensitivity line repeats this with the "
           "design overhead 4 on both backends; it does not decide."),
    "E6": ("Card gate: pass if main_run_hours <= 6 (measured GPU overhead). Otherwise the card's text applies, "
           "'Stop and replan: full Bayesian 671 is not affordable on one GPU', and every later record is "
           "written run_valid false."),
    "E7": ("GPU chain-steps per second = n_chains * 7300 / (median ms / 1000) at 268, 1,340 and 2,684 chains; "
           "ratio = throughput(2,684) / throughput(268). Report only: 'linear' if 8 <= ratio <= 12; "
           "'GPU saturates below 2,684 chains' if ratio < 8; 'above linear' if ratio > 12."),
    "I1": ("airGR held-out values: generalist X=(291, 0.30, 109.10, 2.01) on 1990-01-01..1990-02-28 gives "
           "NSE 0.336 +/- 0.02 AND the Michel set X=(165.05, 6.46, 422.50, 2.45) on 1990-03-01..1999-12-31 "
           "gives NSE 0.57 +/- 0.02: PASS, else FAIL (run_valid false from here on). NOT_RUN if airGR "
           "did not run."),
    "I2": ("JAX on GPU and CPU reproduces both held-out values (same bands) AND matches airGR daily flow with "
           "MARE < 0.01 on both periods (skipped and labelled if airGR did not run), AND the planted model "
           "rows pass: zero rain gives zero quickflow; unit-hydrograph ordinates sum to 1 within 1e-9; mass "
           "balance closes within 1e-6 mm over a planted year. PASS, else FAIL (run_valid false from here on)."),
    "I3": ("On each backend, a 100 ms time.sleep measured through the timing harness reads within 95..105 ms: "
           "PASS, else FAIL (run_valid false from here on)."),
    "I4": ("On each backend at 2,684 chains, median of 10 timed 730-day passes / median of 10 timed 7,300-day "
           "passes lies in [0.07, 0.13]: PASS, else FAIL (run_valid false from here on)."),
    "I5": ("Planted arithmetic: ms 2 with overhead 4 gives main_run_hours 0.2222; ms 20 gives 2.2222; with "
           "cpu_hours 3 the speedups are 13.5 and 1.35. PASS if the endpoint code reproduces all four."),
    "I6": ("Planted gate rows: main_run_hours 5.9 gives pass and 6.1 gives 'Stop and replan...'; the planted "
           "gate-failure row sets run_valid false in every record and row written after it (scratch "
           "folder). PASS if all hold."),
    "I7": ("Planted arithmetic: 2,684 x 7,300 chain-steps in 60 ms gives 3.2655e8 chain-steps per second; "
           "equal planted times at 268 and 2,684 chains give a ratio of 10 (to one decimal) read as linear. "
           "PASS if both hold."),
}
METRICS = {
    "E1": "airGR NSE on the 59-day run period (anchor)",
    "E2": "JAX GR4J NSE on the 59-day run period and daily-flow MARE versus airGR (anchor)",
    "E3": "batched_forward_ms: median GPU forward-pass time at 2,684 chains",
    "E4": "cpu_671_hours derived from the CPU forward-pass time and measured CPU overhead",
    "E5": "card decision: main_run_hours and GPU-over-CPU speedup",
    "E6": "card gate: main_run_hours <= 6",
    "E7": "GPU throughput scaling, chain-steps per second at 268, 1,340, 2,684 chains",
    "I1": "control: airGR reproduces the page's held-out NSE values",
    "I2": "control: JAX reproduces the held-out values and airGR daily flow; planted model rows",
    "I3": "control: timing harness reads a 100 ms sleep correctly on each backend",
    "I4": "control: a 730-day scan takes 7% to 13% of a 7,300-day scan on each backend",
    "I5": "control: planted arithmetic for the card decision",
    "I6": "control: planted gate rows and run_valid propagation",
    "I7": "control: planted arithmetic for throughput and scaling ratio",
}
THRESHOLDS = {
    "E1": {"center": ANCHOR_NSE, "tolerance": ANCHOR_TOL},
    "E2": {"nse_center": ANCHOR_NSE, "nse_tolerance": ANCHOR_TOL, "mare_max": MARE_MAX},
    "E3": {"low_ms": E3_BAND[0], "high_ms": E3_BAND[1]},
    "E4": {"low_hours": E4_BAND[0], "high_hours": E4_BAND[1]},
    "E5": {"main_run_hours_min_for_if_not": E5_HOURS_MIN, "speedup_min_for_if_lever": E5_SPEEDUP_MIN},
    "E6": {"max_main_run_hours": E6_GATE_HOURS},
    "E7": {"target_ratio": E7_TARGET_RATIO, "relative_tolerance": E7_TOL},
    "I1": {"generalist_cal_nse": GENERALIST_CAL_NSE, "michel_val_nse": MICHEL_VAL_NSE, "tolerance": HELDOUT_TOL},
    "I2": {"generalist_cal_nse": GENERALIST_CAL_NSE, "michel_val_nse": MICHEL_VAL_NSE,
           "tolerance": HELDOUT_TOL, "mare_max": MARE_MAX, "uh_sum_tol": 1e-9, "mass_balance_tol_mm": 1e-6},
    "I3": {"sleep_ms": I3_SLEEP_MS, "tolerance_ms": I3_TOL_MS},
    "I4": {"low_ratio": I4_BAND[0], "high_ratio": I4_BAND[1]},
    "I5": {"main_run_hours_ms2": 0.2222, "main_run_hours_ms20": 2.2222, "speedups": [13.5, 1.35]},
    "I6": {"pass_at": 5.9, "stop_at": 6.1},
    "I7": {"chain_steps_per_s": 3.2655e8, "ratio": 10.0},
}
TIMING_RECORDS = ("E3", "E4", "E5", "E6", "E7", "I3", "I4")
HW_KEYS = ("instance_type", "gpu_name", "gpu_count", "driver_version", "jax_version", "jaxlib_version",
           "vcpu_count", "price_usd_per_hour", "lambda_instance_id", "dtype")


class Halt(Exception):
    """A degenerate-output detector fired. The run stops; `code` names the cause."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail = code, detail


class StopRun(Exception):
    """The cost or time guard asked for a clean stop."""


_LOG = {"quiet": False, "prefix": ""}


def log(msg: str) -> None:
    if not _LOG["quiet"]:
        print(_LOG["prefix"] + msg, flush=True)


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


# ----------------------------------------------------------------------------------------------
# JSON helpers. Non-finite numbers become null so every file stays strict JSON.
# ----------------------------------------------------------------------------------------------
def clean(x):
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    if isinstance(x, dict):
        return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    return x


def dump_json(path: Path, obj) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(clean(obj), indent=1, sort_keys=True, allow_nan=False))
    os.replace(tmp, path)


def load_json(path: Path):
    return json.loads(Path(path).read_text())


def append_jsonl(path: Path, row: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(clean(row), sort_keys=True, allow_nan=False)
    with open(path, "a") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


def read_jsonl(path: Path, strict: bool = True):
    """Parse one JSON object per line. Strict mode raises on any bad line."""
    path = Path(path)
    if not path.exists():
        return [] if strict else ([], [])
    rows, bad = [], []
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError("line is not a JSON object")
            rows.append(obj)
        except ValueError as e:
            if strict:
                raise ValueError(f"{path}: line {n} is not valid JSON ({e})") from None
            bad.append(line)
    return rows if strict else (rows, bad)


# ----------------------------------------------------------------------------------------------
# Run validity state, stamped into every row and record at write time.
# ----------------------------------------------------------------------------------------------
class RunState:
    FILE = "RUN_VALID.json"

    def __init__(self, out):
        self.out = Path(out)
        self.path = self.out / self.FILE

    def load(self) -> dict:
        if self.path.exists():
            return load_json(self.path)
        return {"tag": TAG, "run_valid": True, "labels": [], "timing_labels": [], "void_reasons": [],
                "incomplete": False, "events": []}

    def save(self, st: dict) -> None:
        st["updated_utc"] = now_utc()
        dump_json(self.path, st)

    def ensure(self) -> None:
        if not self.path.exists():
            self.save(self.load())

    def void(self, reason: str, timing_label: str | None = None) -> None:
        st = self.load()
        st["run_valid"] = False
        if reason not in st["void_reasons"]:
            st["void_reasons"].append(reason)
        if timing_label and timing_label not in st["timing_labels"]:
            st["timing_labels"].append(timing_label)
        st["events"].append({"utc": now_utc(), "event": "void", "reason": reason})
        self.save(st)
        log(f"[run_valid] set false: {reason}")

    def add_label(self, label: str) -> None:
        st = self.load()
        if label not in st["labels"]:
            st["labels"].ap
[digest: truncated by the byte cap; showing the first 20358 of 149684 bytes]

=== results_m1/out/raw/timing_rows.jsonl (122119 bytes)
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 1, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 437.0878219999952, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": -1, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 1, "vcpu_count": 30, "warmup": true, "written_utc": "2026-10-20T03:26:26+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 1, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.39160100001641, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 0, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 1, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:26+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 1, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.21316599997863, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 1, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 1, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:26+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 1, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.16117000001077, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 2, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 1, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:26+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 1, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.16285900002617, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 3, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 1, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:26+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 1, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.4231919999977, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 4, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 1, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:26+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 1, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.70144500000242, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 5, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 1, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:27+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 1, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.15483900000208, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 6, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 1, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:27+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 1, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.30506199999354, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 7, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 1, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:27+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 1, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.51053799998431, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 8, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 1, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:27+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 1, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.28262799997765, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 9, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 1, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:27+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 2, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.27771499997971, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 0, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 2, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:27+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 2, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.23481600001492, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 1, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 2, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:27+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 2, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.4148340000238, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 2, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 2, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:27+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 2, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.42285699998774, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 3, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 2, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:27+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 2, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.42299899999239, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 4, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 2, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:27+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 2, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.36448399998608, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 5, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 2, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:27+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 2, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.18249500001662, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 6, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 2, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:27+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 2, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.18201000000136, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 7, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 2, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:28+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 2, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.21913099999256, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 8, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 2, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:28+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 2, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.54474899999764, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 9, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 2, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:28+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 3, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.43007700000248, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 0, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 3, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:28+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 3, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.50585799999499, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 1, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 3, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:28+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 3, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.19997000000944, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 2, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 3, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:28+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 3, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.61712100000295, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 3, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 3, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:28+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 3, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.44253799998546, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 4, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 3, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:28+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 3, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.20758500002489, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 5, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 3, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:28+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 3, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.32212299998764, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 6, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 3, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:28+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 3, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.37049000002116, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 7, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 3, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:28+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 3, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.27595700001189, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 8, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 3, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:28+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 3, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.2316089999947, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 9, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 3, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:28+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 1, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.14939699999945, "n_chains": 268, "n_days": 7300, "params_mode": "identical_chains", "price_usd_per_hour": 1.29, "repeat": 0, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 1, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:29+00:00"}
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtyp
[digest: truncated by the byte cap; showing the first 20358 of 122119 bytes]

=== results_m1/out/hardware_labels.json (473 bytes)
{
 "driver_version": "570.148.08",
 "dtype": "float32 (JAX default)",
 "git_commit": "e7acf90c84dff22d16d35714cdddda98ad75506e",
 "gpu_count": 1,
 "gpu_name": "NVIDIA A10",
 "instance_type": "gpu_1x_a10",
 "jax_devices": [
  "cuda:0"
 ],
 "jax_version": "0.6.0",
 "jaxlib_version": "0.6.0",
 "jaxlib_version_source": "jaxlib.__version__",
 "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
 "nvidia_smi_error": null,
 "price_usd_per_hour": 1.29,
 "vcpu_count": 30
}

=== results_m1/out/records/id-E1_kind-endpoint_tag-m1.json (4782 bytes)
{
  "cell": {
    "id": "E1",
    "kind": "endpoint",
    "tag": "m1"
  },
  "decision": "NOT_RUN",
  "decision_rule": "airGR on L0123001, X=(165.05, 6.46, 422.50, 2.45), run period 1990-01-01..1990-02-28, default warm-up and initial states, NSE on Qmm: PASS if |NSE - 0.495| <= 0.02, else FAIL (page or period misread; timing void, run_valid false from here on). NOT_RUN if R or airGR could not be installed or run; the error text is kept and the run is labelled 'anchor by page value'.",
  "env": {
    "git_rev": null,
    "host": "129-159-79-123",
    "python": "3.10.12",
    "timestamp_utc": "2026-10-20T03:26:05+00:00"
  },
  "inputs": [
    {
      "bytes": 130610,
      "n_items": 10593,
      "path": "/home/ubuntu/m1_run/data/L0123001.rda",
      "present": true,
      "sha256": "e82399bbea6e"
    },
    {
      "bytes": 2880343,
      "n_items": null,
      "path": "/home/ubuntu/m1_run/data/airGR_1.7.9.tar.gz",
      "present": true,
      "sha256": "7af0d1858a11"
    },
    {
      "bytes": 3104,
      "n_items": null,
      "path": "results_m1/out/extract/anchor_airgr.R",
      "present": true,
      "sha256": "4d61a83fa779"
    },
    {
      "bytes": 66,
      "n_items": null,
      "path": "results_m1/out/airgr_install_status.txt",
      "present": true,
      "sha256": "58d0d57671d5"
    },
    {
      "n_items": 3,
      "path": "results_m1/out/raw/airgr_output.json",
      "present": false,
      "sha256": null
    },
    {
      "n_items": null,
      "path": "results_m1/out/raw/anchor_rows.jsonl",
      "present": false,
      "sha256": null
    }
  ],
  "metric": "airGR NSE on the 59-day run period (anchor)",
  "notes": "R or airGR could not be installed or run. The JAX anchor falls back to the page value 0.495; every later record carries the label 'anchor by page value'.",
  "threshold": {
    "center": 0.495,
    "tolerance": 0.02
  },
  "values": {
    "error_text": "apt-get exit code 100; R CMD INSTALL exit code not_tried\n--- last lines of apt_r.log ---\nGet:85 http://archive.ubuntu.com/ubuntu jammy/universe amd64 r-cran-class amd64 7.3-20-1 [87.9 kB]\nGet:86 http://archive.ubuntu.com/ubuntu jammy/universe amd64 r-cran-cluster amd64 2.1.2-2 [541 kB]\nGet:87 http://archive.ubuntu.com/ubuntu jammy/universe amd64 r-cran-codetools all 0.2-18-1 [90.8 kB]\nGet:88 http://archive.ubuntu.com/ubuntu jammy/universe amd64 r-cran-foreign amd64 0.8.82-1 [244 kB]\nGet:89 http://archive.ubuntu.com/ubuntu jammy/universe amd64 r-cran-kernsmooth amd64 2.23-20-1 [90.3 kB]\nGet:90 http://archive.ubuntu.com/ubuntu jammy/universe amd64 r-cran-lattice amd64 0.20-45-1 [1130 kB]\nGet:91 http://archive.ubuntu.com/ubuntu jammy/universe amd64 r-cran-matrix amd64 1.4-0-1 [4305 kB]\nGet:92 http://archive.ubuntu.com/ubuntu jammy/universe amd64 r-cran-nlme amd64 3.1.155-1 [2235 kB]\nGet:93 http://archive.ubuntu.com/ubuntu jammy/universe amd64 r-cran-mgcv amd64 1.8-39-1 [2994 kB]\nGet:94 http://archive.ubuntu.com/ubuntu jammy/universe amd64 r-cran-nnet amd64 7.3-17-1 [112 kB]\nGet:95 http://archive.ubuntu.com/ubuntu jammy/universe amd64 r-cran-survival amd64 3.2-13-1 [6579 kB]\nGet:96 http://archive.ubuntu.com/ubuntu jammy/universe amd64 r-cran-rpart amd64 4.1.16-1 [892 kB]\nGet:97 http://archive.ubuntu.com/ubuntu jammy/universe amd64 r-cran-spatial amd64 7.3-15-1 [132 kB]\nGet:98 http://archive.ubuntu.com/ubuntu jammy/universe amd64 r-doc-html all 4.1.2-1ubuntu2 [557 kB]\nGet:99 http://archive.ubuntu.com/ubuntu jammy/universe amd64 r-recommended all 4.1.2-1ubuntu2 [2624 B]\nGet:100 http://archive.ubuntu.com/ubuntu jammy/universe amd64 tilix-common all 1.9.4-2build1 [281 kB]\nGet:101 http://archive.ubuntu.com/ubuntu jammy/universe amd64 tilix amd64 1.9.4-2build1 [681 kB]\nGet:102 http://archive.ubuntu.com/ubuntu jammy/main amd64 x11-utils amd64 7.7+5build2 [206 kB]\nGet:103 http://archive.ubuntu.com/ubuntu jammy/main amd64 x11-xserver-utils amd64 7.7+9build1 [170 kB]\nGet:104 http://archive.ubuntu.com/ubuntu jammy/main amd64 libauthen-sasl-perl all 2.1600-1.1 [43.1 kB]\nFetched 95.6 MB in 5s (17.5 MB/s)\nE: Failed to fetch http://security.ubuntu.com/ubuntu/pool/main/libh/libhttp-daemon-perl/libhttp-daemon-perl_6.13-1ubuntu0.1_all.deb  404  Not Found [IP: 91.189.92.24 80]\nE: Failed to fetch http://security.ubuntu.com/ubuntu/pool/main/n/ncurses/libncurses-dev_6.3-2ubuntu0.1_amd64.deb  404  Not Found [IP: 91.189.92.24 80]\nE: Failed to fetch http://security.ubuntu.com/ubuntu/pool/main/n/ncurses/libncurses5-dev_6.3-2ubuntu0.1_amd64.deb  404  Not Found [IP: 91.189.92.24 80]\nE: Unable to fetch some archives, maybe run apt-get update or try with --fix-missing?",
    "nse": null,
    "page_value": 0.495,
    "run_labels": [
      "anchor by page value"
    ],
    "run_valid": true,
    "run_void_reasons": []
  }
}

=== results_m1/out/records/id-E2_kind-endpoint_tag-m1.json (5091 bytes)
{
  "cell": {
    "id": "E2",
    "kind": "endpoint",
    "tag": "m1"
  },
  "decision": "PASS (page value only; no independent code ran)",
  "decision_rule": "JAX GR4J on the same inputs and period, on the GPU and on the CPU backend: PASS if every backend gives |NSE - 0.495| <= 0.02 AND mean absolute relative error of daily flow versus airGR < 0.01 on matching dates, with no non-finite or all-zero flow; else FAIL (timed model is not GR4J; timing void, run_valid false from here on). If airGR did not run, the NSE band alone decides, labelled 'page value only; no independent code ran'.",
  "env": {
    "git_rev": null,
    "host": "129-159-79-123",
    "python": "3.10.12",
    "timestamp_utc": "2026-10-20T03:26:07+00:00"
  },
  "inputs": [
    {
      "bytes": 130610,
      "n_items": 10593,
      "path": "/home/ubuntu/m1_run/data/L0123001.rda",
      "present": true,
      "sha256": "e82399bbea6e"
    },
    {
      "bytes": 2880343,
      "n_items": null,
      "path": "/home/ubuntu/m1_run/data/airGR_1.7.9.tar.gz",
      "present": true,
      "sha256": "7af0d1858a11"
    },
    {
      "bytes": 3104,
      "n_items": null,
      "path": "results_m1/out/extract/anchor_airgr.R",
      "present": true,
      "sha256": "4d61a83fa779"
    },
    {
      "bytes": 66,
      "n_items": null,
      "path": "results_m1/out/airgr_install_status.txt",
      "present": true,
      "sha256": "58d0d57671d5"
    },
    {
      "n_items": 3,
      "path": "results_m1/out/raw/airgr_output.json",
      "present": false,
      "sha256": null
    },
    {
      "bytes": 5682,
      "n_items": 6,
      "path": "results_m1/out/raw/anchor_rows.jsonl",
      "present": true,
      "sha256": "b96157fafc64"
    },
    {
      "bytes": 147212,
      "n_items": 6,
      "path": "results_m1/out/raw/anchor_daily.jsonl",
      "present": true,
      "sha256": "6908dc8be893"
    }
  ],
  "metric": "JAX GR4J NSE on the 59-day run period and daily-flow MARE versus airGR (anchor)",
  "notes": "page value only; no independent code ran",
  "rows": [
    {
      "X": [
        165.05,
        6.46,
        422.5,
        2.45
      ],
      "airgr_available": false,
      "airgr_nse": null,
      "all_zero_flow": false,
      "arm": "anchor_jax",
      "backend": "gpu",
      "case": "anchor_cal",
      "dates_match_airgr": null,
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "first_call_ms_including_compile": 451.2166069999921,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "mare_excluded_days": null,
      "mare_vs_airgr": null,
      "n_days": 59,
      "nonfinite_days": 0,
      "nse": 0.4947751841761373,
      "page_nse": 0.495,
      "period_first": "1990-01-01",
      "period_last": "1990-02-28",
      "price_usd_per_hour": 1.29,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "set": "anchor",
      "vcpu_count": 30,
      "warmup_first": "1989-01-01",
      "warmup_n": 365,
      "written_utc": "2026-10-20T03:26:07+00:00"
    },
    {
      "X": [
        165.05,
        6.46,
        422.5,
        2.45
      ],
      "airgr_available": false,
      "airgr_nse": null,
      "all_zero_flow": false,
      "arm": "anchor_jax",
      "backend": "cpu",
      "case": "anchor_cal",
      "dates_match_airgr": null,
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "first_call_ms_including_compile": 107.18816800002173,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "mare_excluded_days": null,
      "mare_vs_airgr": null,
      "n_days": 59,
      "nonfinite_days": 0,
      "nse": 0.4947744556743169,
      "page_nse": 0.495,
      "period_first": "1990-01-01",
      "period_last": "1990-02-28",
      "price_usd_per_hour": 1.29,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "set": "anchor",
      "vcpu_count": 30,
      "warmup_first": "1989-01-01",
      "warmup_n": 365,
      "written_utc": "2026-10-20T03:26:07+00:00"
    }
  ],
  "threshold": {
    "mare_max": 0.01,
    "nse_center": 0.495,
    "nse_tolerance": 0.02
  },
  "values": {
    "airgr_ran": false,
    "e2_label": "page value only; no independent code ran",
    "per_backend": {
      "cpu": {
        "mare_vs_airgr": null,
        "nse": 0.4947744556743169,
        "pass": true,
        "why": "ok"
      },
      "gpu": {
        "mare_vs_airgr": null,
        "nse": 0.4947751841761373,
        "pass": true,
        "why": "ok"
      }
    },
    "run_labels": [
      "anchor by page value"
    ],
    "run_valid": true,
    "run_void_reasons": []
  }
}

=== results_m1/out/records/id-E3_kind-endpoint_tag-m1.json (26630 bytes)
{
  "cell": {
    "id": "E3",
    "kind": "endpoint",
    "tag": "m1"
  },
  "decision": "REFUTED",
  "decision_rule": "Median of the 30 timed GPU passes at 2,684 chains (3 seeds x 10 repeats, distinct parameters, 7,300 days): HOLDS if 0.67 <= median <= 6 ms, else REFUTED (card guess off by more than 3x).",
  "env": {
    "git_rev": null,
    "host": "129-159-79-123",
    "python": "3.10.12",
    "timestamp_utc": "2026-10-20T04:26:00+00:00"
  },
  "inputs": [
    {
      "bytes": 122119,
      "n_items": 192,
      "path": "results_m1/out/raw/timing_rows.jsonl",
      "present": true,
      "sha256": "6fa1ccb1cbe8"
    },
    {
      "bytes": 47686,
      "n_items": 66,
      "path": "results_m1/out/raw/probe_blocks.jsonl",
      "present": true,
      "sha256": "be0ce7f7ab45"
    },
    {
      "bytes": 263387,
      "n_items": 2684,
      "path": "results_m1/out/extract/params_distinct.json",
      "present": true,
      "sha256": "6e2d1c3b07b9"
    },
    {
      "bytes": 793,
      "n_items": null,
      "path": "results_m1/out/extract/param_ranges.json",
      "present": true,
      "sha256": "a55eddd47ac6"
    },
    {
      "bytes": 478016,
      "n_items": 10593,
      "path": "results_m1/out/extract/basin.json",
      "present": true,
      "sha256": "c5e301f7403f"
    }
  ],
  "metric": "batched_forward_ms: median GPU forward-pass time at 2,684 chains",
  "notes": "",
  "rows": [
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.37027600000624,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 0,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:32+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.77655300000242,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 1,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:32+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.43320399998333,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 2,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:33+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.6070610000047,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 3,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:33+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.43784900000173,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 4,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:33+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.62163800000644,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 5,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:33+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.5467439999843,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 6,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:33+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.43152000000032,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 7,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:33+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.32500500000151,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 8,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:33+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.37834999999927,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 9,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:33+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.40429700001096,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 0,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:33+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.28644300001542,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 1,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:33+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.4117930000059,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 2,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:33+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.42348100000663,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 3,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:34+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.3098380000149,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 4,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:34+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.31882199999086,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 5,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:34+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.28228800001625,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 6,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:34+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.28643600000419,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 7,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:34+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.32006899999101,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 8,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:34+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.32568799999763,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 9,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:34+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 3,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.50949099999639,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 0,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 3,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:34+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 3,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.34801200001152,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 1,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 3,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:34+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 3,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 88.3513659999835,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 2,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 3,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:34+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 3,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_ve
[digest: truncated by the byte cap; showing the first 20358 of 26630 bytes]

=== results_m1/out/records/id-E4_kind-endpoint_tag-m1.json (57921 bytes)
{
  "cell": {
    "id": "E4",
    "kind": "endpoint",
    "tag": "m1"
  },
  "decision": "REFUTED",
  "decision_rule": "cpu_671_hours = 100000 * (median of the 30 timed CPU passes at 2,684 chains, ms) / 1000 / 3600 * measured CPU overhead: HOLDS if 1 <= hours <= 9, else REFUTED.",
  "env": {
    "git_rev": null,
    "host": "129-159-79-123",
    "python": "3.10.12",
    "timestamp_utc": "2026-10-20T04:26:00+00:00"
  },
  "inputs": [
    {
      "bytes": 122119,
      "n_items": 192,
      "path": "results_m1/out/raw/timing_rows.jsonl",
      "present": true,
      "sha256": "6fa1ccb1cbe8"
    },
    {
      "bytes": 47686,
      "n_items": 66,
      "path": "results_m1/out/raw/probe_blocks.jsonl",
      "present": true,
      "sha256": "be0ce7f7ab45"
    },
    {
      "bytes": 263387,
      "n_items": 2684,
      "path": "results_m1/out/extract/params_distinct.json",
      "present": true,
      "sha256": "6e2d1c3b07b9"
    },
    {
      "bytes": 793,
      "n_items": null,
      "path": "results_m1/out/extract/param_ranges.json",
      "present": true,
      "sha256": "a55eddd47ac6"
    },
    {
      "bytes": 478016,
      "n_items": 10593,
      "path": "results_m1/out/extract/basin.json",
      "present": true,
      "sha256": "c5e301f7403f"
    }
  ],
  "metric": "cpu_671_hours derived from the CPU forward-pass time and measured CPU overhead",
  "notes": "",
  "rows": [
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1026.032114000003,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 0,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:02+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1064.6376400000008,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 1,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:04+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1020.6577090000053,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 2,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:05+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1077.4490300000252,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 3,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:06+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1013.5818659999813,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 4,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:07+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1076.9204350000052,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 5,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:08+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1016.4402820000191,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 6,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:09+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1046.2095899999895,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 7,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:10+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1024.4495290000089,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 8,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:11+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1056.1699600000054,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 9,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:12+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1024.3299500000091,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 0,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:13+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1083.2748349999974,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 1,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:14+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1034.1980649999982,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 2,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:15+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1016.1887350000143,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 3,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:16+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1088.1366769999943,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 4,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:17+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 998.2551070000056,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 5,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:18+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1028.9429759999962,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 6,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:19+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1050.2389220000055,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 7,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:20+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1062.102533000001,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 8,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:21+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1059.9871149999842,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 9,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:22+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 3,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1036.6494079999882,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 0,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 3,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:23+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 3,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1023.0401050000069,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 1,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 3,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:24+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 3,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 1036.3384769999868,
      "n_chains": 2684,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 2,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 3,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:27:26+00:00"
    },
    {
      "arm": "cpu_timing",
      "backend": "cpu",
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days":
[digest: truncated by the byte cap; showing the first 20358 of 57921 bytes]

=== results_m1/out/records/id-E5_kind-endpoint_tag-m1.json (5634 bytes)
{
  "cell": {
    "id": "E5",
    "kind": "endpoint",
    "tag": "m1"
  },
  "decision": "if_not",
  "decision_rule": "main_run_hours = 100000 * GPU median ms / 1000 / 3600 * measured GPU overhead; speedup = cpu_671_hours / main_run_hours. Decision if_not if main_run_hours >= 1 OR speedup < 20, else if_lever (the card's expected outcome is refuted). A sensitivity line repeats this with the design overhead 4 on both backends; it does not decide.",
  "env": {
    "git_rev": null,
    "host": "129-159-79-123",
    "python": "3.10.12",
    "timestamp_utc": "2026-10-20T04:26:00+00:00"
  },
  "inputs": [
    {
      "bytes": 122119,
      "n_items": 192,
      "path": "results_m1/out/raw/timing_rows.jsonl",
      "present": true,
      "sha256": "6fa1ccb1cbe8"
    },
    {
      "bytes": 47686,
      "n_items": 66,
      "path": "results_m1/out/raw/probe_blocks.jsonl",
      "present": true,
      "sha256": "be0ce7f7ab45"
    },
    {
      "bytes": 263387,
      "n_items": 2684,
      "path": "results_m1/out/extract/params_distinct.json",
      "present": true,
      "sha256": "6e2d1c3b07b9"
    },
    {
      "bytes": 793,
      "n_items": null,
      "path": "results_m1/out/extract/param_ranges.json",
      "present": true,
      "sha256": "a55eddd47ac6"
    },
    {
      "bytes": 478016,
      "n_items": 10593,
      "path": "results_m1/out/extract/basin.json",
      "present": true,
      "sha256": "c5e301f7403f"
    }
  ],
  "metric": "card decision: main_run_hours and GPU-over-CPU speedup",
  "notes": "",
  "rows": [
    {
      "acceptance_rate": 0.02884538002980626,
      "iterations": 1000,
      "ms_per_iteration": 88.62087484099999,
      "overhead": 1.0029430899131768,
      "seed": 1,
      "total_ms": 88620.87484099998
    },
    {
      "acceptance_rate": 0.028527570789865873,
      "iterations": 1000,
      "ms_per_iteration": 88.68313002600009,
      "overhead": 1.0036476463477544,
      "seed": 2,
      "total_ms": 88683.13002600009
    },
    {
      "acceptance_rate": 0.028874441132637853,
      "iterations": 1000,
      "ms_per_iteration": 88.67381877700006,
      "overhead": 1.0035422687732294,
      "seed": 3,
      "total_ms": 88673.81877700007
    },
    {
      "acceptance_rate": 0.0288301043219076,
      "iterations": 1000,
      "ms_per_iteration": 1080.2866559499998,
      "overhead": 1.0412404508930337,
      "seed": 1,
      "total_ms": 1080286.6559499998
    },
    {
      "acceptance_rate": 0.028534277198211624,
      "iterations": 1000,
      "ms_per_iteration": 1071.0032800120007,
      "overhead": 1.0322926160806234,
      "seed": 2,
      "total_ms": 1071003.2800120006
    },
    {
      "acceptance_rate": 0.0288871087928465,
      "iterations": 1000,
      "ms_per_iteration": 1074.2625510960006,
      "overhead": 1.0354340830925455,
      "seed": 3,
      "total_ms": 1074262.5510960007
    }
  ],
  "threshold": {
    "main_run_hours_min_for_if_not": 1.0,
    "speedup_min_for_if_lever": 20.0
  },
  "values": {
    "batched_forward_ms": 88.36082099999487,
    "card_expected": "if_not",
    "cpu_671_hours": 29.840626419333343,
    "cpu_forward_ms": 1037.4997004999927,
    "hardware": {
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "price_usd_per_hour": 1.29,
      "vcpu_count": 30
    },
    "hardware_consistent": true,
    "main_run_hours": 2.463161632694446,
    "overhead_cpu": 1.0354340830925455,
    "overhead_cpu_per_seed": [
      {
        "acceptance_rate": 0.0288301043219076,
        "iterations": 1000,
        "ms_per_iteration": 1080.2866559499998,
        "overhead": 1.0412404508930337,
        "seed": 1,
        "total_ms": 1080286.6559499998
      },
      {
        "acceptance_rate": 0.028534277198211624,
        "iterations": 1000,
        "ms_per_iteration": 1071.0032800120007,
        "overhead": 1.0322926160806234,
        "seed": 2,
        "total_ms": 1071003.2800120006
      },
      {
        "acceptance_rate": 0.0288871087928465,
        "iterations": 1000,
        "ms_per_iteration": 1074.2625510960006,
        "overhead": 1.0354340830925455,
        "seed": 3,
        "total_ms": 1074262.5510960007
      }
    ],
    "overhead_gpu": 1.0035422687732294,
    "overhead_gpu_per_seed": [
      {
        "acceptance_rate": 0.02884538002980626,
        "iterations": 1000,
        "ms_per_iteration": 88.62087484099999,
        "overhead": 1.0029430899131768,
        "seed": 1,
        "total_ms": 88620.87484099998
      },
      {
        "acceptance_rate": 0.028527570789865873,
        "iterations": 1000,
        "ms_per_iteration": 88.68313002600009,
        "overhead": 1.0036476463477544,
        "seed": 2,
        "total_ms": 88683.13002600009
      },
      {
        "acceptance_rate": 0.028874441132637853,
        "iterations": 1000,
        "ms_per_iteration": 88.67381877700006,
        "overhead": 1.0035422687732294,
        "seed": 3,
        "total_ms": 88673.81877700007
      }
    ],
    "run_labels": [
      "anchor by page value"
    ],
    "run_valid": true,
    "run_void_reasons": [],
    "sensitivity_overhead_4": {
      "cpu_671_hours": 115.27774449999917,
      "label": "sensitivity line: design overhead 4 on both backends; does not decide",
      "main_run_hours": 9.81786899999943,
      "overhead": 4.0,
      "reading": "if_not",
      "speedup": 11.741625855876247
    },
    "speedup": 12.11476584534599
  }
}

=== results_m1/out/records/id-E6_kind-endpoint_tag-m1.json (2051 bytes)
{
  "cell": {
    "id": "E6",
    "kind": "endpoint",
    "tag": "m1"
  },
  "decision": "pass",
  "decision_rule": "Card gate: pass if main_run_hours <= 6 (measured GPU overhead). Otherwise the card's text applies, 'Stop and replan: full Bayesian 671 is not affordable on one GPU', and every later record is written run_valid false.",
  "env": {
    "git_rev": null,
    "host": "129-159-79-123",
    "python": "3.10.12",
    "timestamp_utc": "2026-10-20T04:26:00+00:00"
  },
  "inputs": [
    {
      "bytes": 122119,
      "n_items": 192,
      "path": "results_m1/out/raw/timing_rows.jsonl",
      "present": true,
      "sha256": "6fa1ccb1cbe8"
    },
    {
      "bytes": 47686,
      "n_items": 66,
      "path": "results_m1/out/raw/probe_blocks.jsonl",
      "present": true,
      "sha256": "be0ce7f7ab45"
    },
    {
      "bytes": 263387,
      "n_items": 2684,
      "path": "results_m1/out/extract/params_distinct.json",
      "present": true,
      "sha256": "6e2d1c3b07b9"
    },
    {
      "bytes": 793,
      "n_items": null,
      "path": "results_m1/out/extract/param_ranges.json",
      "present": true,
      "sha256": "a55eddd47ac6"
    },
    {
      "bytes": 478016,
      "n_items": 10593,
      "path": "results_m1/out/extract/basin.json",
      "present": true,
      "sha256": "c5e301f7403f"
    }
  ],
  "metric": "card gate: main_run_hours <= 6",
  "notes": "",
  "threshold": {
    "max_main_run_hours": 6.0
  },
  "values": {
    "gate_reading": "pass",
    "hardware": {
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "price_usd_per_hour": 1.29,
      "vcpu_count": 30
    },
    "hardware_consistent": true,
    "main_run_hours": 2.463161632694446,
    "run_labels": [
      "anchor by page value"
    ],
    "run_valid": true,
    "run_void_reasons": []
  }
}

=== results_m1/out/records/id-E7_kind-endpoint_tag-m1.json (77859 bytes)
{
  "cell": {
    "id": "E7",
    "kind": "endpoint",
    "tag": "m1"
  },
  "decision": "REPORT_ONLY: linear",
  "decision_rule": "GPU chain-steps per second = n_chains * 7300 / (median ms / 1000) at 268, 1,340 and 2,684 chains; ratio = throughput(2,684) / throughput(268). Report only: 'linear' if 8 <= ratio <= 12; 'GPU saturates below 2,684 chains' if ratio < 8; 'above linear' if ratio > 12.",
  "env": {
    "git_rev": null,
    "host": "129-159-79-123",
    "python": "3.10.12",
    "timestamp_utc": "2026-10-20T04:26:00+00:00"
  },
  "inputs": [
    {
      "bytes": 122119,
      "n_items": 192,
      "path": "results_m1/out/raw/timing_rows.jsonl",
      "present": true,
      "sha256": "6fa1ccb1cbe8"
    },
    {
      "bytes": 47686,
      "n_items": 66,
      "path": "results_m1/out/raw/probe_blocks.jsonl",
      "present": true,
      "sha256": "be0ce7f7ab45"
    },
    {
      "bytes": 263387,
      "n_items": 2684,
      "path": "results_m1/out/extract/params_distinct.json",
      "present": true,
      "sha256": "6e2d1c3b07b9"
    },
    {
      "bytes": 793,
      "n_items": null,
      "path": "results_m1/out/extract/param_ranges.json",
      "present": true,
      "sha256": "a55eddd47ac6"
    },
    {
      "bytes": 478016,
      "n_items": 10593,
      "path": "results_m1/out/extract/basin.json",
      "present": true,
      "sha256": "c5e301f7403f"
    }
  ],
  "metric": "GPU throughput scaling, chain-steps per second at 268, 1,340, 2,684 chains",
  "notes": "",
  "rows": [
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.39160100001641,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 0,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:26+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.21316599997863,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 1,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:26+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.16117000001077,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 2,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:26+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.16285900002617,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 3,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:26+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.4231919999977,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 4,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:26+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.70144500000242,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 5,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:27+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.15483900000208,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 6,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:27+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.30506199999354,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 7,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:27+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.51053799998431,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 8,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:27+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 1,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.28262799997765,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 9,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 1,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:27+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.27771499997971,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 0,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:27+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.23481600001492,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 1,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:27+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.4148340000238,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 2,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:27+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.42285699998774,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 3,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:27+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.42299899999239,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 4,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:27+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.36448399998608,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 5,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:27+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.18249500001662,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 6,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:27+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.18201000000136,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 7,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:28+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.21913099999256,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 8,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:28+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 2,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.54474899999764,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 9,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 2,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:28+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 3,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.43007700000248,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 0,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 3,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:28+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 3,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.50585799999499,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 1,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 3,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:28+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 3,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "ms": 77.19997000000944,
      "n_chains": 268,
      "n_days": 7300,
      "params_mode": "distinct",
      "price_usd_per_hour": 1.29,
      "repeat": 2,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "seed": 3,
      "vcpu_count": 30,
      "warmup": false,
      "written_utc": "2026-10-20T03:26:28+00:00"
    },
    {
      "arm": "gpu_timing",
      "backend": "gpu",
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "forcing_offset_days": 3,
      "gpu_count": 1,
  
[digest: truncated by the byte cap; showing the first 20358 of 77859 bytes]

=== results_m1/out/records/id-I2_kind-control_tag-m1.json (8352 bytes)
{
  "cell": {
    "id": "I2",
    "kind": "control",
    "tag": "m1"
  },
  "decision": "PASS (page value only; no independent code ran)",
  "decision_rule": "JAX on GPU and CPU reproduces both held-out values (same bands) AND matches airGR daily flow with MARE < 0.01 on both periods (skipped and labelled if airGR did not run), AND the planted model rows pass: zero rain gives zero quickflow; unit-hydrograph ordinates sum to 1 within 1e-9; mass balance closes within 1e-6 mm over a planted year. PASS, else FAIL (run_valid false from here on).",
  "env": {
    "git_rev": null,
    "host": "129-159-79-123",
    "python": "3.10.12",
    "timestamp_utc": "2026-10-20T03:26:08+00:00"
  },
  "inputs": [
    {
      "bytes": 130610,
      "n_items": 10593,
      "path": "/home/ubuntu/m1_run/data/L0123001.rda",
      "present": true,
      "sha256": "e82399bbea6e"
    },
    {
      "bytes": 2880343,
      "n_items": null,
      "path": "/home/ubuntu/m1_run/data/airGR_1.7.9.tar.gz",
      "present": true,
      "sha256": "7af0d1858a11"
    },
    {
      "bytes": 3104,
      "n_items": null,
      "path": "results_m1/out/extract/anchor_airgr.R",
      "present": true,
      "sha256": "4d61a83fa779"
    },
    {
      "bytes": 66,
      "n_items": null,
      "path": "results_m1/out/airgr_install_status.txt",
      "present": true,
      "sha256": "58d0d57671d5"
    },
    {
      "n_items": 3,
      "path": "results_m1/out/raw/airgr_output.json",
      "present": false,
      "sha256": null
    },
    {
      "bytes": 5682,
      "n_items": 6,
      "path": "results_m1/out/raw/anchor_rows.jsonl",
      "present": true,
      "sha256": "b96157fafc64"
    },
    {
      "bytes": 147212,
      "n_items": 6,
      "path": "results_m1/out/raw/anchor_daily.jsonl",
      "present": true,
      "sha256": "6908dc8be893"
    }
  ],
  "metric": "control: JAX reproduces the held-out values and airGR daily flow; planted model rows",
  "notes": "MARE part skipped: page value only; no independent code ran",
  "rows": [
    {
      "X": [
        291.0,
        0.3,
        109.1,
        2.01
      ],
      "airgr_available": false,
      "airgr_nse": null,
      "all_zero_flow": false,
      "arm": "anchor_jax",
      "backend": "gpu",
      "case": "generalist_cal",
      "dates_match_airgr": null,
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "first_call_ms_including_compile": 4.296995999993669,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "mare_excluded_days": null,
      "mare_vs_airgr": null,
      "n_days": 59,
      "nonfinite_days": 0,
      "nse": 0.3359841691845944,
      "page_nse": 0.336,
      "period_first": "1990-01-01",
      "period_last": "1990-02-28",
      "price_usd_per_hour": 1.29,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "set": "generalist",
      "vcpu_count": 30,
      "warmup_first": "1989-01-01",
      "warmup_n": 365,
      "written_utc": "2026-10-20T03:26:07+00:00"
    },
    {
      "X": [
        165.05,
        6.46,
        422.5,
        2.45
      ],
      "airgr_available": false,
      "airgr_nse": null,
      "all_zero_flow": false,
      "arm": "anchor_jax",
      "backend": "gpu",
      "case": "michel_val",
      "dates_match_airgr": null,
      "device": "cuda:0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "first_call_ms_including_compile": 401.6947070000185,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "mare_excluded_days": null,
      "mare_vs_airgr": null,
      "n_days": 3593,
      "nonfinite_days": 0,
      "nse": 0.5699305023305035,
      "page_nse": 0.57,
      "period_first": "1990-03-01",
      "period_last": "1999-12-31",
      "price_usd_per_hour": 1.29,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "set": "michel",
      "vcpu_count": 30,
      "warmup_first": "1989-03-01",
      "warmup_n": 365,
      "written_utc": "2026-10-20T03:26:07+00:00"
    },
    {
      "X": [
        291.0,
        0.3,
        109.1,
        2.01
      ],
      "airgr_available": false,
      "airgr_nse": null,
      "all_zero_flow": false,
      "arm": "anchor_jax",
      "backend": "cpu",
      "case": "generalist_cal",
      "dates_match_airgr": null,
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "first_call_ms_including_compile": 0.6470139999805724,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "mare_excluded_days": null,
      "mare_vs_airgr": null,
      "n_days": 59,
      "nonfinite_days": 0,
      "nse": 0.33598392990692605,
      "page_nse": 0.336,
      "period_first": "1990-01-01",
      "period_last": "1990-02-28",
      "price_usd_per_hour": 1.29,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "set": "generalist",
      "vcpu_count": 30,
      "warmup_first": "1989-01-01",
      "warmup_n": 365,
      "written_utc": "2026-10-20T03:26:07+00:00"
    },
    {
      "X": [
        165.05,
        6.46,
        422.5,
        2.45
      ],
      "airgr_available": false,
      "airgr_nse": null,
      "all_zero_flow": false,
      "arm": "anchor_jax",
      "backend": "cpu",
      "case": "michel_val",
      "dates_match_airgr": null,
      "device": "TFRT_CPU_0",
      "driver_version": "570.148.08",
      "dtype": "float32 (JAX default)",
      "first_call_ms_including_compile": 101.72645500000499,
      "gpu_count": 1,
      "gpu_name": "NVIDIA A10",
      "instance_type": "gpu_1x_a10",
      "jax_version": "0.6.0",
      "jaxlib_version": "0.6.0",
      "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458",
      "mare_excluded_days": null,
      "mare_vs_airgr": null,
      "n_days": 3593,
      "nonfinite_days": 0,
      "nse": 0.5699305266527167,
      "page_nse": 0.57,
      "period_first": "1990-03-01",
      "period_last": "1999-12-31",
      "price_usd_per_hour": 1.29,
      "run_labels": [
        "anchor by page value"
      ],
      "run_valid": true,
      "run_void_reasons": [],
      "set": "michel",
      "vcpu_count": 30,
      "warmup_first": "1989-03-01",
      "warmup_n": 365,
      "written_utc": "2026-10-20T03:26:07+00:00"
    }
  ],
  "threshold": {
    "generalist_cal_nse": 0.336,
    "mare_max": 0.01,
    "mass_balance_tol_mm": 1e-06,
    "michel_val_nse": 0.57,
    "tolerance": 0.02,
    "uh_sum_tol": 1e-09
  },
  "values": {
    "airgr_ran": false,
    "per_backend": {
      "cpu": {
        "generalist_cal": {
          "mare_vs_airgr": null,
          "nse": 0.33598392990692605,
          "pass": true,
          "why": "ok"
        },
        "michel_val": {
          "mare_vs_airgr": null,
          "nse": 0.5699305266527167,
          "pass": true,
          "why": "ok"
        }
      },
      "gpu": {
        "generalist_cal": {
          "mare_vs_airgr": null,
          "nse": 0.3359841691845944,
          "pass": true,
          "why": "ok"
        },
        "michel_val": {
          "mare_vs_airgr": null,
          "nse": 0.5699305023305035,
          "pass": true,
          "why": "ok"
        }
      }
    },
    "planted_model_rows": {
      "all_pass": true,
      "mass_balance_pass": true,
      "mass_balance_residual_mm": -2.8421709430404007e-13,
      "uh_sum_max_abs_error": 0.0,
      "uh_sum_pass": true,
      "zero_rain_max_net_rain_default_stores": 0.0,
      "zero_rain_max_quickflow_empty_stores": 0.0,
      "zero_rain_max_total_flow_empty_stores": 0.0,
      "zero_rain_pass": true
    },
    "run_labels": [
      "anchor by page value"
    ],
    "run_valid": true,
    "run_void_reasons": []
  }
}

=== SEALED_PREDICTIONS.md (2225 bytes)
# Sealed predictions, measure run m1 (written 2026-10-20 01:5x UTC, before any agent or box ran)

Author: the operating session (Claude). Not shown to the triage, gate, build or post agents. Hash in out/SEALS.txt.

| # | Prediction | Probability |
|---|---|---|
| P1 | E1: airGR on the box reproduces NSE 0.495 within +/-0.02 on the 59-day period | 0.85 |
| P2 | E2: the JAX GR4J matches airGR daily flow within 1% MARE and NSE within +/-0.02 | 0.75 |
| P3 | E3: batched_forward_ms at 2,684 chains is above 6 ms (card guess of 2 ms off by more than 3x). Point estimate 60 ms, range 20 to 200 ms | 0.85 |
| P4 | GPU/CPU speedup (cpu_671_hours / main_run_hours) is below 5 | 0.70 |
| P4b | speedup is at least 20 | 0.05 |
| P5 | measured overhead_gpu is below the card's 4 (between 1.5 and 3) | 0.60 |
| P6 | E5 resolves if_not (card's expected outcome holds) | 0.90 |
| P7 | E6: main_run_hours above 6 h, so the card's own gate says "Stop and replan" | 0.55 |
| P8 | E7: throughput ratio 2,684/268 within 20% of 10 (time per pass nearly flat in chains) | 0.70 |
| P9 | The run completes its first launch with no halt (installs, harness, launcher) | 0.50 |

## Reasoning, in one paragraph

GR4J is a 7,300-step recurrence. On a GPU a scan runs one small kernel per day-step; the cost per step is latency,
not arithmetic, so the pass time is set by step count, roughly 5 to 25 microseconds per step, and barely moves with
the number of chains until the GPU saturates. The card's 2 ms assumes a throughput-bound workload. The CPU scan pays a
similar per-step cost, so the GPU/CPU ratio is small. If this holds, the card's if_not is right for a reason the card
did not give: both arms are bound by the sequential depth of the recurrence, which is exactly the sequential part a
parallel-in-time restructure would attack. That is the reshape-test's question, measured.

## What would change my mind

P3 fails if XLA fuses the scan body well enough to reach about 1 microsecond per step on the GPU. P1 fails if
CreateRunOptions' default warm-up or initial states differ from what the page's output implies. P9 is a coin flip:
`pip install jax[cuda12]` on the Lambda image and `apt install r-base-core` each have a real failure rate.


=== out/PREDICTIONS_SCORED.md (1080 bytes)
# Sealed predictions, scored mechanically from results_m1/out/records (2026-10-20)

| # | p | outcome | note |
|---|---|---|---|
| P1 | 0.85 | unresolved | unresolved: airGR NOT_RUN (apt 404s) |
| P2 | 0.75 | held | NSE part held on both backends (0.4948/0.3360/0.5699); MARE untestable without airGR; scored as held |
| P3 | 0.85 | held | held: 88.4 ms (>6; inside 20-200; point 60) |
| P4 | 0.7 | wrong | wrong: speedup 12.1 (not <5) |
| P4b | 0.05 | did not occur | the forecast event (speedup >= 20) did not occur, as the 0.05 said |
| P5 | 0.6 | wrong | wrong: overhead_gpu 1.004 (not 1.5-3) |
| P6 | 0.9 | held | held: if_not |
| P7 | 0.55 | wrong | wrong: main_run_hours 2.46 <= 6 |
| P8 | 0.7 | held | held: ratio 8.76 within 20% of 10 |
| P9 | 0.5 | wrong | wrong: launch 1 halted at setup |

Brier over 9 resolved: **0.177** (0.25 would be p=0.5 everywhere). Direction right 5 (P2, P3, P4b, P6, P8), wrong 4 (P4, P5, P7, P9), unresolved 1 (P1).
Direction of error: overconfident on the CPU side (P4, P5, P7). The GPU-side mechanism (flat in chains, latency-bound) held.


=== out/launch1/results_m1/out/RUN_VALID.json (483 bytes)
{
 "events": [
  {
   "event": "incomplete",
   "reason": "pip install failed with exit code 124 (see results_m1/out/logs/pip_install.log)",
   "utc": "2026-10-20T03:01:42+00:00"
  }
 ],
 "incomplete": true,
 "labels": [
  "incomplete run: descriptive only, no verdict"
 ],
 "run_valid": false,
 "tag": "m1",
 "timing_labels": [],
 "updated_utc": "2026-10-20T03:01:42+00:00",
 "void_reasons": [
  "pip install failed with exit code 124 (see results_m1/out/logs/pip_install.log)"
 ]
}

=== results_m1/out/RUN_VALID.json (308 bytes)
{
 "events": [
  {
   "event": "label",
   "label": "anchor by page value",
   "utc": "2026-10-20T03:26:05+00:00"
  }
 ],
 "incomplete": false,
 "labels": [
  "anchor by page value"
 ],
 "run_valid": true,
 "tag": "m1",
 "timing_labels": [],
 "updated_utc": "2026-10-20T03:26:05+00:00",
 "void_reasons": []
}

=== GATE_COMMIT.md (9125 bytes)
# GATE COMMIT: measure run m1 (triage wf_1afd659f-b55)

Date: 2026-10-20. Written by the operating session as gate. The owner set the budget rules on 2026-10-20 (RUN.md);
every other answer below is the gate's own and is recorded as such.

## Inputs read (and nothing else)

| File | sha256 |
|---|---|
| `out/design_record.json` | `f31e3c3b15e738fd6e9ac51736f5102d12f0af2d149932a12dd00078c0992a15` |
| `out/triage_wf_1afd659f-b55_return.json` | `9f179ee2d941f0c119545552b29e54be3ff5d71361785f36dbabea0be04d7e3e` |
| `QUESTION.md` | `fe110be5c0209d88a7e745789649ee38ea580e1daf14bb69b7745497b00a11d8` |
| `out/design.json` | `ae8d3be1d79602d6b70d5a226dc9297a2f84e60d98dec97d3032c2036e64d9cb` |

## What is being gated, in plain words

One rented GPU box times a small rainfall-runoff model (GR4J) written as a scan over 7,300 days, batched over 2,684
parameter sets, on the GPU and on the box's CPU. Two published numbers anchor the model first. The measured times go
into a card's own arithmetic and decide whether the card's prediction (GPU throughput is not the blocker) holds.

## Decision on budget and build

**Budget: APPROVED.** Hard cap USD 5 for this run, one launch, cheapest single-GPU instance with capacity (A10 at
USD 1.29/h if still the cheapest at launch). Within the owner's calibration limit (about USD 10). Project cap USD 500.

**Design: APPROVED FOR BUILD** with the changes below and nothing else.

## Answers of record

Each item gets one verdict: ACCEPTED AS-IS, REJECTED, or QUEUED CONTROL.

### Diff departure questions (5)

- **D1 (A10 replaces A6000).** ACCEPTED AS-IS. The decision rule compares GPU and CPU on the same box; the rate and
  vCPU count are recorded and the cost block is recomputed at the recorded rate. The label on every timing endpoint
  reads "measured on <instance> (card priced an A6000)".
- **D2 (tiled single-basin forcing).** ACCEPTED AS-IS, with the control under R1 below. The CAMELS fidelity check
  stays out of scope and is listed in does_not_test.
- **D3 (measured overhead replaces the DESIGN constant 4).** ACCEPTED AS-IS. Both numbers are reported; the decision
  rule E5 is read with the measured overhead; E5 is also reported with overhead 4 as a sensitivity line, labelled.
- **D4 (install R and airGR on the box).** ACCEPTED AS-IS. One attempt each for `apt-get` and `R CMD INSTALL`. If
  either fails, E1 is written NOT_RUN with the error text, E2 reduces to the NSE check against 0.495 alone and is
  labelled "page value only; no independent code ran", and the timing endpoints proceed. The run is then labelled
  "anchor by page value" throughout.
- **D5 (phase gpu_bench only).** ACCEPTED AS-IS. The run resolves the card's prediction through the card's own
  derivation from measured inputs. TAKEAWAYS must say so in its first paragraph.

### Grounding (reader verdict: null)

- **G1.** The isolated reader did not run: the Workflow could not find the `triage-reader` agent type in this
  session (agents load at session start; the role files were copied after). Recorded as a deviation. The gate's own
  grounding, arithmetic and file checks only: every committed input's sha256 in `out/INPUT_HASHES.txt` matches
  QUESTION.md; the airGR page values (0.495 and 0.57 for X = 165.05, 6.46, 422.50, 2.45; 0.336 and 0.777 for the
  generalist set X = 291, 0.30, 109.10, 2.01; calibration period 1990-01-01 to 1990-02-28; validation period
  1990-03-01 to 1999-12-31) were fetched twice and agree. No other number in the design is cited. ACCEPTED with this
  note; the post-run reader will ground the measured numbers in the raw rows.

### Run queue (1)

- **R1 (per-chain distinct parameters).** QUEUED CONTROL, binding on the build. Every timing arm uses 2,684 distinct
  parameter vectors drawn uniformly, seed-fixed, within the parameter ranges airGR's own transformation functions
  define (read `airGR/R/TransfoParam_GR4J.R` in the committed tarball; do not take ranges from memory). The anchor
  arms use the fixed X. A second timing row with all chains at the fixed X is also written, labelled "identical
  chains", so any broadcasting shortcut shows as a gap between the two rows.

### Instrument queue (7): validation controls, all inside the run, no extra spend

- **I1 (E1 readout, airGR NSE).** QUEUED CONTROL: held-out ground truth from the same page, not used to set the
  anchor: with the generalist set X = (291, 0.30, 109.10, 2.01) on the same calibration period, airGR must give
  NSE 0.336 +/- 0.02; with the Michel set on the validation period 1990-03-01 to 1999-12-31, 0.57 +/- 0.02. Both
  written as records. If I1 fails while E1 passes, the period reading is suspect and the run is labelled.
- **I2 (E2 readout, JAX vs airGR).** QUEUED CONTROL: the JAX model must reproduce the same two held-out values
  (0.336 and 0.57, +/- 0.02) and match airGR daily flow to < 1% MARE on the validation period as well as the
  calibration period. Plus planted selftest rows: zero rain gives zero quickflow; the unit hydrograph ordinates sum
  to 1 within 1e-9; mass balance closes within 1e-6 over a planted year.
- **I3 (E3 readout, GPU timer).** QUEUED CONTROL: the timing harness measures a 100 ms `time.sleep` within
  +/- 5 ms (planted known duration), and a 730-day scan at 2,684 chains takes between 7% and 13% of the 7,300-day
  scan (linearity in depth). Both written as records.
- **I4 (E4 readout, CPU timer).** QUEUED CONTROL: same two checks on the CPU backend.
- **I5 (E5 derivation).** QUEUED CONTROL: planted arithmetic in the selftest: ms = 2 and overhead = 4 give
  main_run_hours 0.2222 (the card's own figure); ms = 20 gives 2.2222; speedup with cpu_hours 3 gives 13.5 and
  1.35. Exact to 4 digits.
- **I6 (E6 gate).** QUEUED CONTROL: planted rows at main_run_hours 5.9 (pass) and 6.1 (fail) must produce the
  pass and the "Stop and replan" label; the planted gate-failure row must set run_valid false in every record written
  after it.
- **I7 (E7 throughput).** QUEUED CONTROL: planted arithmetic: 2,684 chains x 7,300 days in 60 ms gives
  3.2655e8 chain-steps per second; the ratio check at 268 vs 2,684 on planted equal times gives exactly 10.

## Labels

- Every timing record carries: instance type, GPU name, driver, jax version, vCPU count, price per hour.
- If E1 or E2 fails: run_valid false everywhere; timing rows are still written and labelled "descriptive only;
  anchor failed".
- If the box stops before all sizes run: finished rows are reported, each labelled "incomplete run: descriptive
  only, no verdict".

## Checks the gate made before answering

Arithmetic only, on numbers in the inputs. No experiment was run.
- The skeptic's band arithmetic reproduces: 1e5 x 0.67 ms x 4 / 3.6e6 = 0.0744 h; 1e5 x 6 ms x 4 / 3.6e6 = 0.667 h;
  speedup 1 h / 0.667 h = 1.5 and 9 h / 0.0744 h = 121.
- Time box: 2 h at USD 1.29 = USD 2.58; with 1 h setup slack the cap of USD 5 holds at a 3.5 h box.
- Chains: 671 x 4 = 2,684; 67 x 4 = 268; 335 x 4 = 1,340.

---

## Addendum after launch 1 (2026-10-20, 03:1xZ): attempt 2 authorised

**New input of record.** `results_m1/out/logs/pip_install.log` and `results_m1/out/logs/stop.log` from launch 1 (box
490e3fae09ad433f82b7ffc6bf2762ee, A10, us-east-1): `pip install --user -U "jax[cuda12]" pyreadr numpy` downloaded at
about 450 kB/s and hit its 1500 s timeout (exit 124) inside the 766 MB cuDNN wheel; `onbox_m1.sh` stopped cleanly with
rc=2, run_valid false, no stage run. The operator then found that the image already provides JAX 0.6.0 with a CUDA
device (`python3 -c "import jax; print(jax.devices())"` gave `[CudaDevice(id=0)]`).

- **A1 (toolchain).** REJECTED: the design's "pip install -U jax[cuda12]". REPLACED BY: use the image's preinstalled
  JAX as is (no upgrade, no CUDA wheels); `pip install --user pyreadr` only; the GPU assertion stays and still exits 3
  if JAX sees no GPU. Record `jax.__version__` and `jaxlib.__version__` in env.txt and in every timing record. This
  is the same rule `frozen/remote_run.sh` applies to torch.
- **A2 (summary file).** QUEUED CONTROL: the runner writes `results_m1/out/m1_summary.json` after the endpoints
  stage (and after an early stop): run_valid, labels, and every endpoint and control decision. It exists so the
  launcher's criticals-first fetch has a small file to verify. It restates records; it decides nothing.
- **A3 (launch 2).** Budget: a second launch is authorised. The cap stays USD 5 for launches 1 and 2 together.
  Launch 1 cost about 0.6 h at USD 1.29/h (exact figure from the audit log once posted). Same instance type if it has
  capacity, else the cheapest single GPU with capacity, recorded.
- **A4 (launcher).** The adapted launcher is unchanged. Observation of record: its poll loop printed nothing for
  about 26 minutes and then reported the DONE marker "after 60s"; the elapsed counter counts only the launcher's own
  sleeps (known deviation D3 in the lineage). Not repaired here; noted for the launcher's next frozen version.

Everything else in this gate stands. The build is re-run through pipeline.js build mode with the updated directive;
no built file is edited by hand.


=== RUN.md (11009 bytes)
# reshape-test · measure · 20261020-0145

Kind: measure. The first phase (`gpu_bench`) of a PASS card, run as a latent_skeptic run, so that the card's own
prediction is resolved by a measurement and the result lands beside the card it came from.

## Source card

- Run: `../20261019-2345-tree` (arm O, open root), pick R1 · physical · "Large-sample multi-catchment calibration (CAMELS)".
- Record: `../20261019-2345-tree/out/result.json` sha256 `3bda9fd89ac81cd09fa50ab298fa851160d0a9a2894489276adfa4dbd42c3cdb`;
  rendered card `../20261019-2345-tree/out/RESULT.md` sha256 `93ed866bc76faa28e8b95af8b32b137f4102bd29b4217dbad3bda329f507ee04`.
- Producer reply (the PLAN): `../20261019-2345-tree/out/agents/0008-R1_physical_top_producer/reply.txt`.
- The card's prediction under test: `expected: if_not`, by its own decision rule: "if_lever iff GPU wall-clock for
  671 catchments < 1 hour AND the GPU beats the vectorized CPU baseline by >= 20x; otherwise if_not."
- The card's two load-bearing guesses, both `measured_by: gpu_bench`: `batched_forward_ms = 2` and `cpu_671_hours = 3`.
- The card's own gate at this phase: `main_run_hours <= 6`, else "Stop and replan".

## Pipeline

- latent_skeptic at ff9a63c (`../../../dut/latent_skeptic`): `pipeline.js`, `triage_workflow.js`, `gates/`, `.claude/agents/`,
  copied here read-only. Design mode is NOT run: the card is the design. `out/design.json` is the card's PLAN compiled by
  hand into the design-record schema (mapping in QUESTION.md). Triage, gate, build and post run as in design mode.
- `frozen/` copied from `latent_skeptic_meta/experiments/latent_verify_b/frozen` (lambda_run.sh, remote_run.sh,
  provenance.py), read-only; adapted only at header-declared points, per launch, as copies.
- metis at e7acf90 (before this folder).
- Hashes of every input: `out/INPUT_HASHES.txt`.

## Budget (owner, 2026-10-20)

- Project cap, Lambda, all runs from now: USD 500.
- Calibration and smoke measurements (this kind): fuzzy limit, about USD 10 per run, no re-approval needed.
- Full runs: hard limit, owner approves each spend above USD 20 before launch.
- This run: hard cap USD 5, one launch, cheapest single-GPU instance with capacity.

## Sequence

1. `SEALED_PREDICTIONS.md` written and hashed before any agent runs (`out/SEALS.txt`).
2. Triage: Workflow `triage_workflow.js` on the design-as-claim, exactly as pipeline.js design mode frames it.
3. `out/design_record.json` = {seed, design, diff, triage, gate}; `GATE_COMMIT.md` answers every queued item.
4. Build: Workflow `pipeline.js` mode build, tag m1, conventions frozen/, exec_note EXEC_NOTE.md.
5. Run: per-launch launcher copy; detached via setsid; teardown confirmed through the API.
6. Post: Workflow `pipeline.js` mode post; TAKEAWAYS_m1.md is the answer.
7. Ledger: `../../_meta/LEDGER.jsonl` gets one row: card, prediction, outcome, cost.

Models: every agent pinned in the scripts (sonnet, opus, haiku). None on Fable. The operating session is Fable; nothing
unpinned may run.

## Log

- 01:45Z sealed predictions, design, diff hashed (`out/SEALS.txt`).
- 01:46Z triage wf_1afd659f-b55, 18 s: decidability RULED_OUT; coordinates/scale NEEDS_RUN (one control queued);
  7 instrument validations queued. **Deviation:** the isolated reader did not run (`triage-reader` agent type not
  found: role files copied into this session's project after the session started). Grounding null; answered of record
  in GATE_COMMIT.md G1. Return saved verbatim: `out/triage_wf_1afd659f-b55_return.json`.
- 01:5xZ GATE_COMMIT.md and EXEC_NOTE.md written and hashed; build wf_feb9c78c-9c3 launched (GateCheck sonnet, build opus).
- Launcher copies made while no box runs: `lambda_run_m1.sh` (header-declared points only; 61 changed or added lines,
  all in the scp payload, remote dir, forwarded env, bootstrap name and fetch paths; `bash -n` ok) and
  `remote_run_m1.sh` (cd line only).
- Lambda at 01:4xZ: 0 instances; A6000 no capacity; A10 $1.29/h in us-east-1 and us-west-1.
- 02:2xZ build wf_feb9c78c-9c3 returned after 39 min: GateCheck 14 of 14 answered; `run_m1.py` (2,650 lines) and
  `onbox_m1.sh` (174 lines). Selftest 110/110 under the operator's own run (`out/selftest_m1_operator.log`). The
  builder's float64 reference equations reproduce the page's three values on the committed data before launch:
  0.4948, 0.3360, 0.5699. Build return: `out/build_m1_wf_feb9c78c-9c3_return.json`. Hashes: `out/BUILT_HASHES.txt`.
  Builder readings accepted as recorded: parameter ranges from CreateCalibOptions.R mapped through
  TransfoParam_GR4J.R (X1, X3 in [4.6e-5, 21807]; X2 in [-10904, 10904]; X4 in [0.5, 20]), drawn uniformly in
  parameter units with seed 0; probe in blocks of 100 iterations; float32 on the box.
- Launcher: `INSTANCE_TYPE` added to the forwarded env (additive, declared point) so records carry the instance.
  Result dir at the run root (`results_m1/`, as lvb did), not `out/results_m1/` as EXEC_NOTE said: the launcher puts
  the result dir name into the Lambda instance name and a slash there is untested.
- Risk accepted: `remote_run_m1.sh` keeps the frozen Gemma bootstrap (only its cd line may change); an irrelevant
  import failure there would stop the run before `onbox_m1.sh`.
- 02:3xZ LAUNCH 1 (of at most 1): `PRICE_USD_PER_HOUR=1.29 BUDGET_LEFT_USD=5 REMOTE_TIMEOUT=5400
  INSTANCE_TYPE=gpu_1x_a10 setsid nohup bash lambda_run_m1.sh gpu_1x_a10 us-east-1 onbox_m1.sh results_m1`, log
  `out/launcher_m1.log`. Expected 40 to 90 min, USD 1 to 2.
- 03:01Z LAUNCH 1 HALTED at setup: `pip install -U "jax[cuda12]"` at about 450 kB/s hit its 1500 s timeout inside
  the 766 MB cuDNN wheel (exit 124); `onbox_m1.sh` stopped cleanly, rc=2, run_valid false, no stage run. Operator
  finding on the still-live box: the image already has JAX 0.6.0 with `[CudaDevice(id=0)]`. Launcher observation:
  26 min of silence in the poll loop, then "DONE marker after 60s" (counter counts its own sleeps; D3). Box
  terminated by the launcher's EXIT trap, API-confirmed: 02:31:55Z launch, 03:04:33Z terminate, 0.54 h,
  about USD 0.70. Launch 1 outputs archived under `out/launch1/`.
- 03:1xZ Gate addendum A1 to A4 (preinstalled JAX, pyreadr only; summary file; launch 2 authorised within the same
  USD 5 cap; launcher unchanged). EXEC_NOTE.md updated (checklist items 13 and 14, toolchain step 1). Build re-run
  through pipeline.js build mode; no built file edited by hand.
- 03:20Z build 2 (wf_8e148711-9bc, 14 min): GateCheck 14 of 14; `run_m1.py` 2,939 lines
  (98854eeb…), `onbox_m1.sh` 184 lines (f9067b23…), hashes in `out/BUILT_HASHES_build2.txt`. Selftest 135/135 under
  the operator's own run (`out/selftest_m1_operator_build2.log`); heavy imports blocked for the whole selftest. Changes:
  preinstalled JAX kept, `pyreadr` only, version comparison before and after the install, `m1_summary.json` on every
  exit path. Builder re-checked the day-step equations against `frun_GR4J.f90` and the R defaults (stores start 0.3
  and 0.5 full; warm-up up to one year plus a leap day).
- 03:2xZ LAUNCH 2 (of 2 authorised): same command with `BUDGET_LEFT_USD=4`; launch 1's results moved to
  `out/launch1/`. Monitor armed on `out/launcher_m1.log`.
- 03:52Z launch 2 progress read on the box: stages extract, anchor_airgr, anchor_jax, timers, timing_gpu, timing_cpu,
  probe_gpu all exit 0 by 03:32Z (8 min after start); probe_cpu running at about 1,080 ms per iteration (3 seeds x
  1,001 iterations, about 54 min). Projected spend at that point USD 0.96 of the USD 4 cap.
- **Launcher deviation, seen on both launches:** the ssh call that starts the detached on-box job does not return
  until the remote job exits (26 min and counting on launch 2; on launch 1 it returned when pip timed out), so the
  launcher never prints "[run] confirmed started" or any "[poll-run]" line while the run is live, and then reports
  the DONE marker "after 60s". Completion, fetch and teardown still happen (launch 1 showed this). Billing stays
  bounded by the on-box time guard and the backstop. Not repaired here; candidate cause for the next frozen
  launcher version: a descendant of the detached job holding the ssh session's channel open.
- 03:53Z airGR install on launch 2 failed before R was reached: `apt-get install` fetched 104 packages then hit 404s on
  three security.ubuntu.com .deb files (stale package index on the image; `apt-get update` was not run first, and the
  directive allowed one attempt). E1 and I1 are NOT_RUN; the run carries "anchor by page value". Fix for the next
  directive: `apt-get update` before `install`. The JAX anchors reproduce all three page values on both backends
  (0.4948, 0.3360, 0.5699).
- 04:27Z LAUNCH 2 DONE rc=0. Launcher: ssh start call blocked until remote exit (as on launch 1), then DONE marker,
  summary verified, full fetch, teardown accepted; API: launch 03:21:36Z, terminate 04:27:43Z, 1.10 h, USD 1.42.
  **Lambda total for the run: USD 2.12** (launch 1 0.70 + launch 2 1.42) of the USD 5 cap; project USD 2.12 of 500.
- Records (14, `results_m1/out/records/`), run_valid true, label "anchor by page value":
  E1 NOT_RUN (apt 404s); E2 PASS, JAX reproduces 0.4948 / 0.3360 / 0.5699 on GPU and CPU (page 0.495 / 0.336 / 0.57);
  E3 REFUTED: batched_forward_ms 88.36 (card guess 2; 44x); E4 REFUTED: cpu_671_hours 29.84 (card guess 3; 10x);
  E5 **if_not**: main_run_hours 2.46, speedup 12.1, overhead_gpu 1.0035, overhead_cpu 1.035; E6 card gate pass
  (2.46 <= 6); E7 linear (throughput ratio 8.76 for 10x chains). I3 to I7 PASS; I1 NOT_RUN; I2 PASS (page value only).
  GPU time per pass: 77.3 / 82.5 / 88.4 ms at 268 / 1,340 / 2,684 chains (flat: latency-bound on the 7,300-step
  recurrence). CPU: 131 / 583 / 1,037 ms (throughput-bound). Identical-chains rows within 1% of distinct-chains rows.
- Ledger row appended: `../../_meta/LEDGER.jsonl` (first row). Card write-back: `out/CARD_WRITEBACK_m1.json`.
  Sealed predictions scored: `out/PREDICTIONS_SCORED.md` (Brier 0.177 over 9; held 5, wrong 4, unresolved 1).
- 04:3xZ post mode wf_a438614d-1b5 launched (elicit, question triage, TAKEAWAYS_m1.md under the two gates).
- 05:35Z post done (39 agents, 6.4 min): GateCheck 14/14; 8 elicited questions; top 3 triaged (reader failed again,
  agent type not found; skeptic findings in the workflow journal). `TAKEAWAYS_m1.md` written: gates on the text above
  the raw-samples heading 3.9 codes/1000 words and 0 unscoped sentences (writer's run, pasted in the file); on the
  whole file 8.5 codes/1000 and 5 unscoped sentences (operator's run; the rule applies above the heading).
  Verdict as written there: the card's if_not holds by its own rule, with thin margin, resting on an overhead factor of
  about 1 from a probe that stores no samples and whose acceptance fell to 0.0015. Caveats appended to the ledger
  (row 2). Hashes of all outputs in `out/SEALS.txt`.
- Close: Lambda USD 2.12 total (two launches), 0 instances. Claude usage: triage 4 agents, build 2+2, post 39.
  Nothing committed or pushed.


=== onbox_m1.sh (8573 bytes)
#!/usr/bin/env bash
# On-box driver for measurement m1: time one batched GR4J forward pass on this GPU box.
#
# How it starts. Inside ~/m1_run, under the launcher's `timeout`, the launcher runs:
#     bash remote_run_m1.sh bash onbox_m1.sh
# The launcher forwards PRICE_USD_PER_HOUR, BUDGET_LEFT_USD and INSTANCE_TYPE in the environment.
#
# What it does, in order:
#   1. Python toolchain. The image's preinstalled JAX is used as is; it is never installed or upgraded.
#      The only install is: python3 -m pip install --user pyreadr.
#      jax, jaxlib and numpy versions are read before and after that install; any change stops the run.
#      JAX must list a GPU. Otherwise RUN_VALID.json says false and the exit code is 3.
#      There is no virtual environment: one would hide the preinstalled JAX.
#   2. R toolchain: one apt-get attempt for R and gfortran, then one R CMD INSTALL of the committed airGR.
#      A failure here does not stop the run. The anchor then falls back to the page value 0.495.
#   3. env.txt: jax and jaxlib versions, JAX devices, pip freeze, R --version, nvidia-smi -q, nproc.
#   4. run_m1.py stages: extract; airGR anchor; JAX anchor; timer checks; timing on GPU then CPU;
#      overhead probes on GPU then CPU; endpoints.
# A cost guard runs before every stage and between timed passes.
# It stops cleanly before projected spend reaches BUDGET_LEFT_USD.
# A time guard keeps the run inside the launcher's cap (REMOTE_TIMEOUT, 5,400 s unless set).
#
# Results: results_m1/out/.
# m1_summary.json there restates run validity, labels and every decision; the launcher fetches it first.
# It is rewritten after the endpoints stage, after any early stop, and just before RUN_DONE.
# RUN_DONE there holds this script's exit code.
# Exit codes: 0 finished; 1 a stage crashed; 2 setup or install failed; 3 JAX sees no GPU;
#             4 stopped cleanly by the cost or time guard; 5 a degenerate output halted the run;
#             143 stopped by a signal.
set -uo pipefail
cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" || exit 2

OUT=results_m1/out
LOG="$OUT/logs"
mkdir -p "$LOG"
RUN="python3 -u run_m1.py"
STOPPING=0

say(){ echo "[onbox $(date -u +%H:%M:%S)] $*"; }

finish(){
  $RUN summary --out "$OUT" 2>&1 | tee -a "$LOG/summary.log"
  echo "$1" > "$OUT/RUN_DONE"
  say "RUN_DONE rc=$1"
  exit "$1"
}

# An early stop relabels every finished row and record, then writes whatever records can be derived.
early_stop(){
  local rc=$1 reason=$2
  STOPPING=1
  say "early stop (rc=$rc): $reason"
  $RUN stop --out "$OUT" --reason "$reason" 2>&1 | tee -a "$LOG/stop.log"
  $RUN endpoints --out "$OUT" 2>&1 | tee -a "$LOG/endpoints_after_stop.log"
  finish "$rc"
}

on_signal(){
  trap '' TERM INT HUP
  if [ "$STOPPING" = 1 ]; then finish 143; fi
  early_stop 143 "stopped by a signal before the run finished (most likely the launcher's time cap)"
}
trap on_signal TERM INT HUP

guard(){
  local stage=$1 g
  $RUN guard --out "$OUT" --stage "$stage" 2>&1 | tee -a "$LOG/guard.log"
  g=${PIPESTATUS[0]}
  case "$g" in
    0) ;;
    10) early_stop 4 "the cost or time guard stopped the run before stage '$stage'" ;;
    *) early_stop 2 "the cost guard could not run before stage '$stage' (exit $g)" ;;
  esac
}

stage(){
  local name=$1 rc
  shift
  guard "$name"
  say "stage $name: $*"
  "$@" 2>&1 | tee "$LOG/$name.log"
  rc=${PIPESTATUS[0]}
  say "stage $name exit $rc"
  case "$rc" in
    0) ;;
    4) early_stop 4 "stage '$name' was stopped by the cost or time guard" ;;
    5) early_stop 5 "stage '$name' halted on a degenerate output (see $LOG/$name.log)" ;;
    *) early_stop "$rc" "stage '$name' failed with exit code $rc (see $LOG/$name.log)" ;;
  esac
}

# ---- Preflight: price, budget and the time cap -------------------------------------------------
say "start in $PWD on $(hostname); $(python3 --version 2>&1); $(nproc) vCPUs"
CAP=${REMOTE_TIMEOUT:-5400}
NOW=$(date +%s)
PCOMM=$(ps -o comm= -p "$PPID" 2>/dev/null | tr -d ' ')
PELAPSED=0
if [ "$PCOMM" = "timeout" ]; then PELAPSED=$(ps -o etimes= -p "$PPID" 2>/dev/null | tr -d ' '); fi
case "$PELAPSED" in ''|*[!0-9]*) PELAPSED=0 ;; esac
export M1_DEADLINE_EPOCH=$(( NOW - PELAPSED + CAP - 180 ))
say "time cap ${CAP}s; parent '${PCOMM:-unknown}' started ${PELAPSED}s ago; stages must end by epoch $M1_DEADLINE_EPOCH"
export PRICE_USD_PER_HOUR="${PRICE_USD_PER_HOUR:-}"
export BUDGET_LEFT_USD="${BUDGET_LEFT_USD:-}"
say "price USD ${PRICE_USD_PER_HOUR:-unset} per hour; budget left USD ${BUDGET_LEFT_USD:-unset}; instance type ${INSTANCE_TYPE:-not forwarded}"
guard preflight

# ---- 1. Python toolchain: the image's JAX as is; pyreadr is the only install -------------------
guard pip
$RUN versions --label before_pip --out "$OUT" 2>&1 | tee "$LOG/versions_before_pip.log"
VB=${PIPESTATUS[0]}
[ "$VB" = 0 ] || early_stop 2 "reading package versions before the install failed with exit code $VB"
say "python3 -m pip install --user pyreadr (jax, jaxlib and numpy stay as the image has them)"
timeout 600 python3 -m pip install --user pyreadr > "$LOG/pip_install.log" 2>&1
PIP_RC=$?
tail -n 3 "$LOG/pip_install.log"
[ "$PIP_RC" = 0 ] || early_stop 2 "pip install --user pyreadr failed with exit code $PIP_RC (see $LOG/pip_install.log)"
$RUN versions --label after_pip --compare-to "$LOG/versions_before_pip.json" --out "$OUT" 2>&1 \
  | tee "$LOG/versions_after_pip.log"
VA=${PIPESTATUS[0]}
case "$VA" in
  0) ;;
  2) early_stop 2 "installing pyreadr changed jax, jaxlib or numpy (see $LOG/versions_after_pip.log)" ;;
  *) early_stop 2 "reading package versions after the install failed with exit code $VA" ;;
esac
$RUN gpu-check --out "$OUT" 2>&1 | tee "$LOG/gpu_check.log"
GC=${PIPESTATUS[0]}
case "$GC" in
  0) ;;
  3) early_stop 3 "JAX lists no GPU; RUN_VALID.json says false; no silent CPU fallback" ;;
  *) early_stop 2 "the GPU check crashed with exit code $GC" ;;
esac

# ---- 2. R toolchain and airGR (one attempt each) ------------------------------------------------
guard r_install
export R_LIBS_USER="$PWD/Rlib"   # a library folder this user can write; Rscript later reads it too
mkdir -p "$R_LIBS_USER"
say "sudo apt-get install -y r-base-core gfortran (one attempt)"
timeout 900 sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y r-base-core gfortran > "$LOG/apt_r.log" 2>&1
APT_RC=$?
RCMD_RC=not_tried
if [ "$APT_RC" = 0 ]; then
  say "R CMD INSTALL data/airGR_1.7.9.tar.gz (one attempt) into $R_LIBS_USER"
  timeout 900 R CMD INSTALL data/airGR_1.7.9.tar.gz > "$LOG/r_cmd_install.log" 2>&1
  RCMD_RC=$?
fi
printf 'apt_rc=%s\nrcmd_rc=%s\nr_libs_user=%s\n' "$APT_RC" "$RCMD_RC" "$R_LIBS_USER" > "$OUT/airgr_install_status.txt"
say "apt-get exit $APT_RC; R CMD INSTALL exit $RCMD_RC (a failure means the anchor uses the page value)"
{
  R --version 2>&1 | head -n 1
  gfortran --version 2>&1 | head -n 1
  Rscript -e 'cat("airGR", as.character(packageVersion("airGR")), "\n")' 2>&1
} > "$LOG/versions_r.log" 2>&1
cat "$LOG/versions_r.log"

# ---- 3. Environment record ----------------------------------------------------------------------
{
  echo "== utc date"; date -u
  echo "== nproc"; nproc
  echo "== python3 --version"; python3 --version
  echo "== jax.__version__ and jaxlib.__version__ (the image's preinstalled JAX, used as is)"
  $RUN versions --label env --out "$OUT"
  echo "== JAX devices (GPU check)"; cat "$LOG/gpu_check.log"
  echo "== pip freeze"; python3 -m pip freeze
  echo "== R --version"; R --version || echo "R is not available"
  echo "== nvidia-smi -q"; nvidia-smi -q
  echo "== price and budget"; echo "PRICE_USD_PER_HOUR=$PRICE_USD_PER_HOUR BUDGET_LEFT_USD=$BUDGET_LEFT_USD"
  echo "== instance"; echo "LAMBDA_INSTANCE_ID=${LAMBDA_INSTANCE_ID:-unset} INSTANCE_TYPE=${INSTANCE_TYPE:-not forwarded}"
} > "$OUT/env.txt" 2>&1
say "wrote $OUT/env.txt"

# ---- 4. Stages, in the binding order ------------------------------------------------------------
stage extract      $RUN extract --out "$OUT"
stage anchor_airgr $RUN generate --part anchor_airgr --out "$OUT"
stage anchor_jax   $RUN generate --part anchor_jax --out "$OUT"
stage timers       $RUN generate --part timers --out "$OUT"
stage timing_gpu   $RUN generate --part timing --backend gpu --out "$OUT"
stage timing_cpu   $RUN generate --part timing --backend cpu --out "$OUT"
stage probe_gpu    $RUN generate --part probe --backend gpu --out "$OUT"
stage probe_cpu    $RUN generate --part probe --backend cpu --out "$OUT"
stage endpoints    $RUN endpoints --out "$OUT"

say "all stages finished; run validity:"
head -c 3000 "$OUT/RUN_VALID.json"; echo
finish 0


=== TAKEAWAYS_m1.md (13029 bytes)
# Takeaways from the first timing run

Footnote [1] applies to every number below. The model timed is a four-parameter daily river-flow model (GR4J), rewritten in the JAX software library. It ran on one A10 graphics card with a 30-core processor on the same machine. The reference implementation (airGR) never ran.

## What was the research question, and the hypothesis?

A planning document, called "the card", proposes calibrating river-flow models for 671 catchments at once. It predicts that graphics-card speed is not what limits how many catchments get full Bayesian calibration. Bayesian calibration here means sampling many plausible parameter sets per catchment.

The card rested on two guesses it promised to measure first. One was the time of a single batched model run over 2,684 chains, guessed at 2 ms. A chain is one sampler walking through parameter values. The other was processor time for 100,000 steps, guessed at 3 hours.

The question: do both guesses hold, and does the card's decision rule give its expected answer ("if_not")?

The hypothesis: with measured times, either the graphics-card run takes at least 1 hour, or it beats the processor by under 20 times. Either one gives "if_not". The card's own gate also requires the main run to take at most 6 hours.

## What did the experiment try to find?

It timed the model on the graphics card and on the processor at 268, 1,340 and 2,684 chains, each over 7,300 days. It also timed 1,000 steps of a simple sampler, to measure how much a real sampling step costs beyond a bare model run. Then it put the measured numbers into the card's own formula.

It did not run any real calibration, use any real catchment data, or test the model on a second implementation of the loop. The forcing data was one basin's rain and evaporation series, tiled across chains.

## What was predicted, and what happened?

Each line gives the refuting threshold, then the measured number [1].

- Anchor, reference code: airGR should reproduce a fit score of 0.495, within 0.02 [1]. It did not run. The record says "not run". Nothing was measured [1].
- Anchor, our rewrite: should score within 0.02 of 0.495 and match airGR daily flows within 1 percent [1]. It scored 0.49478 on the graphics card and 0.49477 on the processor [1]. The flow comparison was skipped. The record says "pass, page value only" [1].
- Claim A, graphics-card time for 2,684 chains: the guess of 2 ms holds if the median is between 0.67 and 6 ms [1]. The median was 88.36 ms over 30 passes [1]. REFUTED, 44 times the guess [1].
- Claim B, processor hours: the guess of 3 hours holds if the derived value is between 1 and 9 hours. The derived value was 29.84 hours, from 1,037.50 ms per pass [1]. REFUTED, 9.9 times the guess [1].
- Claim C, the card's expected "if_not": refuted only if the main run is under 1 hour and the speedup is at least 20. The main run was 2.46 hours and the speedup was 12.11 [1]. The card's answer holds [1].
- Card gate: main run at most 6 hours. It was 2.46 hours, so it passed [1]. With the card's own overhead factor of 4, it would be 9.82 hours and fail [1].
- Scaling, report only: throughput should rise about 10 times from 268 to 2,684 chains, within 20 percent. It rose 8.76 times, and the record reads "linear" [1].

The overhead factor is the cost of a sampling step divided by the cost of a bare model run. It was measured as 1.0035 on the graphics card and 1.0354 on the processor [1]. The card had assumed 4 [1].

Two guesses missed by more than 3 times. The design calls that a finding about the card's cost estimates, whichever way the decision falls [1].

## Is this what we expected?

Partly. The card's verdict held. Its two numeric guesses did not. Both were refuted, one by 44 times [1].

The verdict holds by a thin margin. The speedup was 12.11 against a limit of 20, and the main run was 2.46 hours against a limit of 1 hour [1].

The verdict also rests on an unchecked overhead of about 1. Exploratory: with the overhead set to 4, the speedup was 11.74 and the verdict was still "if_not" [1].

The run is labelled valid. The only label on it is "anchor by page value", meaning the reference code did not run. Nothing was voided.

Supporting checks all passed. A 100 ms sleep read as 100.32 ms on the graphics card and 100.20 ms on the processor [1]. A 730-day pass took 0.1020 of a 7,300-day pass on the graphics card [1].

## What in these files does not fit

### Open questions

1. Is the sampling step too cheap to stand for the real job?
   - The test step is one model run plus one Gaussian score. The overhead was 1.0035 on the graphics card, from 88.67 ms against 88.36 ms [1].
   - The real job also stores samples, checks convergence and may need careful proposals. The true factor could be well above 1.
   - The 6-hour gate and the "at least 1 hour" clause depend on this factor. At 4, the main run is 9.82 hours and the gate fails [1].

2. Was the test sampler stuck?
   - On the graphics card, seed 1, the share of accepted proposals fell from 0.2278 in the first 100 steps to 0.0337, then 0.0075 [1]. By the tenth block it was 0.0015 [1]. The processor fell from 0.2277 to 0.0015 [1].
   - Overall acceptance was about 0.029 in every run [1]. Proposals were 5 percent of each parameter's range, likely too wide for settled chains.
   - Exploratory: cost per step is mostly the model run, so a stuck sampler probably costs the same per step. Steps needed was never studied. Real runs may need tuned proposals and more than 100,000 steps. The hours figure counts steps, not steps needed.

3. Are the timed parameters realistic?
   - The 2,684 parameter sets were drawn uniformly over the full airGR allowed range. In these files, 2,554 have store capacity above 1,000 mm, and 2,657 have an exchange term beyond plus or minus 100 [1].
   - The median store capacity was 10,793. The question claims real catchments sit far lower. No file here shows that. Run time could change on extreme parameters.
   - The only check compared identical chains with distinct parameters. On the graphics card, identical chains took 87.67 ms and distinct ones 88.36 ms [1]. On the processor, identical took 1,056.95 ms and distinct 1,037.50 ms [1].
   - The question as posed had the graphics-card labels reversed. Also, that check varies parameters across chains, not toward realism.

4. Is the graphics card mostly idle, and why was 8.76 called "linear" [1]? [1]
   - Median time rose from 77.31 ms at 268 chains to 82.45 ms at 1,340 and 88.36 ms at 2,684. Ten times the chains cost 1.14 times the time [1].
   - The model runs 7,300 sequential days, about 12 microseconds each. The 730-day control, at 8.99 ms against 88.17 ms, shows time follows day count [1]. So the card is likely far from full [1].
   - The design said a ratio below 10 means "saturates below 2,684 chains". That reading runs backwards. A ratio near 10 means time stayed nearly flat. The label "linear" hides this.
   - Sizes beyond 2,684 chains were never run. The processor went from 131.12 ms to 1,037.50 ms, a ratio of 7.9 [1].

5. Why did two wrong guesses give nearly the same ratio?
   - The graphics card measured 88.36 ms against 2 ms [1]. The processor derived 29.84 hours against 3 hours [1]. Yet the speedup was 12.11, near the guess-based 13.5 [1].
   - The speedup is set by the ratio of the two guesses, not by either absolute time. Both were wrong by a similar factor, 44 and 9.9 [1]. The files do not say what the guesses were based on [1].
   - So the decision rule tests a ratio, and the guessed times were barely consulted. The ratio landed under 20, but the margin is thin.

6. What was actually compared in the model check?
   - The airGR install stopped when the package download failed. The record shows an exit code of 100, and the build step was "not tried". The model check is recorded as "pass".
   - What passed: our rewrite scored 0.49478 against a rounded number, 0.495, copied from a web page [1]. The tolerance was 0.02 [1]. No daily flows were compared [1].
   - Held-out values also matched the page: 0.3360 against 0.336, and 0.5699 against 0.570 [1].
   - The design said timing is void if the model is not the right one. That test was weakened. A retry with refreshed package lists was never tried.

7. Does the timing survive 64-bit arithmetic?
   - All numbers are 32-bit floating point, the library default. airGR's reference is Fortran, normally 64-bit. The design does not list precision under what it does not test.
   - Cards of this class run 64-bit far slower. Long recurrences may need it for accuracy. The 88.36 ms may be a best case [1].
   - The card was also priced on a different graphics card, an A6000. This run used an A10 at 1.29 dollars per hour [1]. The design records that swap, but no one examined its effect.

8. Does the processor denominator match what the card intended?
   - The 1,037.50 ms figure ran on 30 cores [1]. No file records how many threads the library used. The environment file lists no thread or compiler settings [1].
   - Time rose 7.9 times for 10 times the chains, from 131.12 ms to 583.16 ms to 1,037.50 ms [1]. That suggests parallel work or fixed costs, not a clean single-core baseline [1].
   - The speedup is the second leg of the decision rule. A different processor job would change it. The 20-times threshold has no stated source.

### Found while reading

- The processor sampler probe took about 1,080 seconds per 1,000 steps, roughly 18 minutes. That is a cost of the test, not a flaw [1].
- The anchor window is only 59 days. It checks arithmetic on one basin, not behaviour across basins. The design already declares this.
- The record gives main run hours with no confidence interval. Only three seeds were used, and they differ only by forcing offset. Spread among the 30 passes was small: 88.28 to 88.78 ms [1].
- The sampler probe's acceptance is nearly the same on the graphics card and the processor, to four digits. That is consistent with both running the same arithmetic [1].

## Raw samples, verbatim

This is one row of the input table of timed parameter sets, the first four sets as stored in the parameter file (first 12 lines).

```
{
 "n": 2684,
 "order": [
  "X1",
  "X2",
  "X3",
  "X4"
 ],
 "params": [
  [
   18414.55963509567,
   5625.28872940942,
```

This is one randomly chosen graphics-card timing row at 268 chains, which is an output row.

```
{"arm": "gpu_timing", "backend": "gpu", "device": "cuda:0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 3, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 77.37049000002116, "n_chains": 268, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 7, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 3, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:26:28+00:00"}
```

This is one randomly chosen processor timing row at 2,684 chains.

```
{"arm": "cpu_timing", "backend": "cpu", "device": "TFRT_CPU_0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "forcing_offset_days": 3, "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 1072.0158800000092, "n_chains": 2684, "n_days": 7300, "params_mode": "distinct", "price_usd_per_hour": 1.29, "repeat": 8, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 3, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:27:32+00:00"}
```

This is one randomly chosen block row of the sampler probe, which shows the falling acceptance.

```
{"acceptance_rate": 0.0020380029806259313, "accepted": 547, "arm": "overhead_probe", "backend": "cpu", "block": 7, "device": "TFRT_CPU_0", "driver_version": "570.148.08", "dtype": "float32 (JAX default)", "gpu_count": 1, "gpu_name": "NVIDIA A10", "instance_type": "gpu_1x_a10", "iterations": 100, "jax_version": "0.6.0", "jaxlib_version": "0.6.0", "lambda_instance_id": "d607a8f8da3249d0ac3cb985100b7458", "ms": 105801.67588299992, "ms_per_iteration": 1058.0167588299992, "n_chains": 2684, "n_days": 7300, "price_usd_per_hour": 1.29, "proposal_fraction": 0.05, "run_labels": ["anchor by page value"], "run_valid": true, "run_void_reasons": [], "seed": 1, "vcpu_count": 30, "warmup": false, "written_utc": "2026-10-20T03:46:34+00:00"}
```

This is the stored install status for the reference code, which shows why it never ran.

```
apt_rc=100
rcmd_rc=not_tried
r_libs_user=/home/ubuntu/m1_run/Rlib
```

Gate outputs, run on a copy truncated at the raw-samples heading:

```
/tmp/claude-1000/-home-hal-dev-interp/72fa6ea2-188d-4e00-b467-74ae55869166/scratchpad/trunc.md: 3.9 codes/1000 words (7 codes, 1795 words); threshold 10.0
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
{"type":"object","additionalProperties":false,"required":["sentences","enums"],"properties":{"sentences":{"type":"object","additionalProperties":false,"required":["S1","S2","S3","S4","S5","S6","S7","S8","S9","S10","S11","S12","S13","S14","S15","S16","S17","S18","S19","S20","S21","S22","S23","S24","S25","S26","S27","S28","S29","S30","S31","S32","S33","S34","S35","S36","S37","S38","S39","S40","S41","S42","S43","S44","S45","S46","S47","S48","S49","S50"],"properties":{"S1":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S2":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S3":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S4":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S5":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S6":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S7":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S8":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S9":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S10":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S11":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S12":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S13":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S14":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S15":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S16":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S17":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S18":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S19":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S20":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S21":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S22":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S23":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S24":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S25":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S26":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S27":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S28":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S29":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S30":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S31":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S32":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S33":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S34":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S35":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S36":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S37":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S38":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S39":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S40":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S41":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S42":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S43":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S44":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S45":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S46":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S47":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S48":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S49":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}},"S50":{"type":"object","additionalProperties":false,"required":["question","sentence","verdict","quote","path","reason"],"properties":{"question":{"type":"string"},"sentence":{"type":"string"},"verdict":{"enum":["supported","contradicted","not_addressed"]},"quote":{"type":"string"},"path":{"enum":["../20261019-2345-tree/out/RESULT.md","QUESTION.md","run_m1.py","results_m1/out/raw/timing_rows.jsonl","results_m1/out/hardware_labels.json","results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","results_m1/out/records/id-I2_kind-control_tag-m1.json","SEALED_PREDICTIONS.md","out/PREDICTIONS_SCORED.md","out/launch1/results_m1/out/RUN_VALID.json","results_m1/out/RUN_VALID.json","GATE_COMMIT.md","RUN.md","onbox_m1.sh","TAKEAWAYS_m1.md","evidence/_source/RESULT.md","evidence/QUESTION.md","evidence/run_m1.py","evidence/results_m1/out/raw/timing_rows.jsonl","evidence/results_m1/out/hardware_labels.json","evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json","evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json","evidence/SEALED_PREDICTIONS.md","evidence/out/PREDICTIONS_SCORED.md","evidence/out/launch1/results_m1/out/RUN_VALID.json","evidence/results_m1/out/RUN_VALID.json","evidence/GATE_COMMIT.md","evidence/RUN.md","evidence/onbox_m1.sh","evidence/TAKEAWAYS_m1.md",""]},"reason":{"type":"string"}}}}},"enums":{"type":"object","additionalProperties":false,"required":["headline_kind","baseline_kind","equivalence","prediction_hit","evidence","anchor"],"properties":{"headline_kind":{"enum":["speedup","negative","void","partial","unknown"]},"baseline_kind":{"enum":["stock","tuned","one_thread","cpu_library","other","unknown"]},"equivalence":{"enum":["bit_identical","within_tolerance","not_checked","failed","unknown"]},"prediction_hit":{"enum":["yes","partly","no","not_sealed","unknown"]},"evidence":{"enum":["measured","inferred","unknown"]},"anchor":{"enum":["measured","page_value_only","not_run","none","unknown"]}}}}}