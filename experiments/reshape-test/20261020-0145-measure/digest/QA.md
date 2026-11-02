# Questions and answers

## Q1. What question did the brief or card ask, in its own words, and what would count as an answer?

The card asks: “Does GPU parallelism change how many of the 671 CAMELS catchments can get full Bayesian calibration instead of point optimization?” (evidence/_source/RESULT.md). This concerns graphics-card acceleration of parameter sampling for rainfall–runoff models; this phase measures simulation times and sampler overhead (evidence/QUESTION.md). The rule requires projected graphics-card completion below one hour and at least twentyfold acceleration over vectorized processor execution (evidence/QUESTION.md). Otherwise, the card records its predicted negative answer; completed scientific calibrations are outside this measurement phase (evidence/QUESTION.md).

Sources: (evidence/_source/RESULT.md), (evidence/QUESTION.md).

Checked: 4 sentences supported, 0 contradicted, 0 not addressed.

## Q2. What exactly ran: which system or problem, at what sizes, on what hardware and software, with how many repeats?

GR4J, a four-parameter daily rainfall–runoff model, ran through the JAX numerical library, scanning days sequentially across parallel parameter sequences called chains (evidence/run_m1.py). Measurements covered 268, 1,340 and 2,684 chains over 7,300 days, with one basin’s rainfall and evaporation repeated across chains (evidence/run_m1.py) (evidence/results_m1/out/raw/timing_rows.jsonl). Hardware comprised one NVIDIA A10 graphics card and 30 virtual processors; JAX and its compiled library were version 0.6.0, using 32-bit floating point (evidence/results_m1/out/hardware_labels.json). Each size and backend had ten timed passes at three forcing offsets after compilation warmup (evidence/results_m1/out/raw/timing_rows.jsonl). Sampler probes used 1,000 iterations for each of three seeds on each backend (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json).

Sources: (evidence/run_m1.py), (evidence/results_m1/out/raw/timing_rows.jsonl), (evidence/results_m1/out/hardware_labels.json), (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json).

Checked: 2 sentences supported, 0 contradicted, 3 not addressed.

Not addressed: GR4J, a four-parameter daily rainfall–runoff model, ran through the JAX numerical library, scanning days sequentially across parallel parameter sequences called chains (evidence/run_m1.py).

Quote: none; the cited file (evidence/run_m1.py) does not bear on it.

Not addressed: Measurements covered 268, 1,340 and 2,684 chains over 7,300 days, with one basin’s rainfall and evaporation repeated across chains (evidence/run_m1.py) (evidence/results_m1/out/raw/timing_rows.jsonl).

Quote: none; the cited file (evidence/run_m1.py) does not bear on it.

Not addressed: Each size and backend had ten timed passes at three forcing offsets after compilation warmup (evidence/results_m1/out/raw/timing_rows.jsonl).

Quote: none; the cited file (evidence/results_m1/out/raw/timing_rows.jsonl) does not bear on it.

## Q3. What was the baseline, who would use it in practice, and is it the one an expert would pick?

The baseline was the same custom, vectorized JAX model and Metropolis sampler executed through the rented machine’s processor backend (evidence/run_m1.py). Its intended comparison concerns researchers choosing computing resources for Bayesian catchment calibration rather than point optimization (evidence/_source/RESULT.md). The run does not establish expert preference: its scope excludes alternative implementations, and its write-up identifies missing processor thread settings (evidence/QUESTION.md) (evidence/TAKEAWAYS_m1.md). Consequently, acceleration is relative to this implementation and machine configuration, without evidence that the processor baseline represents expert tuning (evidence/QUESTION.md) (evidence/TAKEAWAYS_m1.md).

Sources: (evidence/run_m1.py), (evidence/_source/RESULT.md), (evidence/QUESTION.md), (evidence/TAKEAWAYS_m1.md).

Checked: 3 sentences supported, 0 contradicted, 1 not addressed.

Not addressed: The baseline was the same custom, vectorized JAX model and Metropolis sampler executed through the rented machine’s processor backend (evidence/run_m1.py).

Quote: none; the cited file (evidence/run_m1.py) does not bear on it.

## Q4. What number answers the question, what is its spread across repeats, and under which rule does it count?

At 2,684 chains, graphics-card passes had median 88.361 milliseconds and range 88.282–88.777 milliseconds (evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json). Processor passes had median 1,037.500 milliseconds and range 998.255–1,088.137 milliseconds at the same size (evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json). Multiplying pass medians by 100,000 iterations and measured sampler overhead produced projected graphics-card and processor times of 2.463 and 29.841 hours (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json). Their ratio, 12.115, misses the required twentyfold acceleration, while projected graphics-card completion exceeds the one-hour limit (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json). Full-run uncertainty intervals were not recorded; the separate six-hour planning gate was met (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json) (evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json).

Sources: (evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json), (evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json), (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json), (evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json).

Checked: 3 sentences supported, 0 contradicted, 2 not addressed.

Not addressed: At 2,684 chains, graphics-card passes had median 88.361 milliseconds and range 88.282–88.777 milliseconds (evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json).

Quote: none; the cited file (evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json) does not bear on it.

Not addressed: Processor passes had median 1,037.500 milliseconds and range 998.255–1,088.137 milliseconds at the same size (evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json).

Quote: none; the cited file (evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json) does not bear on it.

## Q5. How was correctness checked, against which reference, at what tolerance?

On the 59-day example, graphics-card and processor runs achieved Nash–Sutcliffe efficiency scores of 0.494775 and 0.494774, respectively (evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json). This flow-fit score was compared with published 0.495, allowing an absolute difference of 0.02 (evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json). Additional cases reproduced published scores 0.336 and 0.570 as approximately 0.335984 and 0.569931 on both backends, within the same tolerance (evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json). Independent airGR reference code never ran, so daily-flow agreement below one percent mean absolute relative error remained unchecked (evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json). Planted zero-rain, response-weight and water-balance checks passed their recorded thresholds using the scalar model implementation (evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json) (evidence/run_m1.py).

Sources: (evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json), (evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json), (evidence/run_m1.py).

Checked: 4 sentences supported, 0 contradicted, 1 not addressed.

Not addressed: Planted zero-rain, response-weight and water-balance checks passed their recorded thresholds using the scalar model implementation (evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json) (evidence/run_m1.py).

Quote: none; the cited file (evidence/run_m1.py) does not bear on it.

## Q6. What was sealed before measuring, which sealed predictions held, which failed, and by how much?

Forecasts were sealed before measurement (evidence/RUN.md) (evidence/SEALED_PREDICTIONS.md). For 2,684 chains, graphics-card time 88.36 milliseconds held the predicted 20–200 range (evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json) (evidence/SEALED_PREDICTIONS.md). Acceleration was 12.11-fold, contradicting the below-five forecast; the twentyfold event did not occur (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json) (evidence/SEALED_PREDICTIONS.md). Overhead 1.0035 missed the 1.5–3 interval but remained below four; projected 2.46 hours contradicted above-six expectations (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json) (evidence/SEALED_PREDICTIONS.md). The negative decision held; throughput from 268 to 2,684 chains increased 8.76-fold, within the predicted band (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json) (evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json) (evidence/SEALED_PREDICTIONS.md). First-launch completion failed, and independent reproduction remained unresolved (evidence/out/launch1/results_m1/out/RUN_VALID.json) (evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json). The scorer counted the flow-agreement forecast as held despite its untested daily-flow component (evidence/out/PREDICTIONS_SCORED.md).

Sources: (evidence/RUN.md), (evidence/SEALED_PREDICTIONS.md), (evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json), (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json), (evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json), (evidence/out/launch1/results_m1/out/RUN_VALID.json), (evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json), (evidence/out/PREDICTIONS_SCORED.md).

Checked: 5 sentences supported, 0 contradicted, 2 not addressed.

Not addressed: For 2,684 chains, graphics-card time 88.36 milliseconds held the predicted 20–200 range (evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json) (evidence/SEALED_PREDICTIONS.md).

Quote: none; the cited file (evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json) does not bear on it.

Not addressed: The negative decision held; throughput from 268 to 2,684 chains increased 8.76-fold, within the predicted band (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json) (evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json) (evidence/SEALED_PREDICTIONS.md).

Quote: none; the cited file (evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json) does not bear on it.

## Q7. What was voided, skipped or not run, and does any of it change the answer?

The completed attempt was marked valid and complete, with no void reasons and the qualification “anchor by page value” (evidence/results_m1/out/RUN_VALID.json). The initial attempt was marked invalid after dependency installation timed out before measurement stages ran (evidence/out/launch1/results_m1/out/RUN_VALID.json) (evidence/RUN.md). Independent reference execution was skipped after operating-system package installation failed, leaving daily-flow comparison unavailable (evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json) (evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json). The original brief required independent agreement, but a gate decision before measurement permitted comparison with published scores alone after installation failure (evidence/QUESTION.md) (evidence/GATE_COMMIT.md). Thus the recorded timing decision follows the amended rule, while independent output equivalence remains unestablished (evidence/GATE_COMMIT.md) (evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json).

Sources: (evidence/results_m1/out/RUN_VALID.json), (evidence/out/launch1/results_m1/out/RUN_VALID.json), (evidence/RUN.md), (evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json), (evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json), (evidence/QUESTION.md), (evidence/GATE_COMMIT.md).

Checked: 5 sentences supported, 0 contradicted, 0 not addressed.

## Q8. How far does the answer reach: which sizes, hardware and inputs it covers, and where it stops?

Evidence covers this compiled scan implementation on one A10 graphics card and its host processor, using single-precision arithmetic (evidence/run_m1.py) (evidence/results_m1/out/hardware_labels.json). Graphics-card scaling was measured at 268, 1,340 and 2,684 chains; larger ensembles were not measured (evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json). Inputs repeat one example basin’s forcing across uniformly drawn parameter vectors rather than representing distinct catchments (evidence/run_m1.py). The scope excludes the intended catchment dataset, posterior quality, convergence checks, point-optimization comparisons and alternative implementations (evidence/QUESTION.md). Accordingly, these timings support implementation-specific cost estimates, without establishing calibration quality, realistic data-loading costs or performance on other hardware (evidence/QUESTION.md).

Sources: (evidence/run_m1.py), (evidence/results_m1/out/hardware_labels.json), (evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json), (evidence/QUESTION.md).

Checked: 2 sentences supported, 0 contradicted, 3 not addressed.

Not addressed: Evidence covers this compiled scan implementation on one A10 graphics card and its host processor, using single-precision arithmetic (evidence/run_m1.py) (evidence/results_m1/out/hardware_labels.json).

Quote: none; the cited file (evidence/run_m1.py) does not bear on it.

Not addressed: Graphics-card scaling was measured at 268, 1,340 and 2,684 chains; larger ensembles were not measured (evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json).

Quote: none; the cited file (evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json) does not bear on it.

Not addressed: Inputs repeat one example basin’s forcing across uniformly drawn parameter vectors rather than representing distinct catchments (evidence/run_m1.py).

Quote: none; the cited file (evidence/run_m1.py) does not bear on it.

## Q9. What did the run cost, how long did it take, and what would it take to run again?

evidence/RUN.md reports cloud rental charges of $2.12: the failed attempt occupied 0.54 hours and the completed attempt 1.10 hours (evidence/RUN.md). The recorded machine rate was $1.29 per hour (evidence/results_m1/out/hardware_labels.json). Subtracting the recorded 01:45 sealing time from the 05:35 finish gives three hours fifty minutes for the overall pipeline (evidence/RUN.md). Closing accounting supplies agent counts but no model-call charges or measured human labor total (evidence/RUN.md). Repetition requires the preserved measurement script, shell driver, basin data and airGR archive, plus a compatible JAX graphics-card environment (evidence/onbox_m1.sh). Independent reference checking additionally requires successful installation of R and a Fortran compiler (evidence/onbox_m1.sh).

Sources: (evidence/RUN.md), (evidence/results_m1/out/hardware_labels.json), (evidence/onbox_m1.sh).

Checked: 6 sentences supported, 0 contradicted, 0 not addressed.

## Q10. What does the result let a scientist do that they could not before, and what is the next measurement?

The records replace the card’s timing guesses with saved measurements and expose the calculation behind its negative decision (evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json) (evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json) (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json). A scientist can now budget this implementation’s fixed iteration count, while successful Bayesian calibration remains untested (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json) (evidence/QUESTION.md). The next measurement should establish independent daily-flow agreement, because the reference implementation never ran (evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json). Subsequently, timing with actual catchment inputs, stored samples and convergence checks would address the declared gaps in the projected calibration cost (evidence/QUESTION.md) (evidence/TAKEAWAYS_m1.md).

Sources: (evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json), (evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json), (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json), (evidence/QUESTION.md), (evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json), (evidence/TAKEAWAYS_m1.md).

Checked: 3 sentences supported, 0 contradicted, 1 not addressed.

Not addressed: The next measurement should establish independent daily-flow agreement, because the reference implementation never ran (evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json).

Quote: none; the cited file (evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json) does not bear on it.
