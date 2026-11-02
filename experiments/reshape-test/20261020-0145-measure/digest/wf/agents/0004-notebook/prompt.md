Write a marimo notebook for one digest. A scientist who has never seen the project opens it to learn what one run found and to check that against the evidence.

The digest directory is the current directory. Its four files are below. The cited files are already copied under evidence/, and MANIFEST.json lists them; you may read files under evidence/ to learn their shapes. Write nothing and run nothing. Return the notebook's source in JSON.

## Constraints

A checker runs on the source and then runs the notebook. Each of these is checked.

The file starts like this. DIGEST_DIR is the one constant at the top; leave it empty, which means the notebook's own directory.

```python
import marimo

app = marimo.App(width="medium")

with app.setup:
    DIGEST_DIR = ""  # empty: this notebook's own directory
    import json
    from pathlib import Path
    import marimo as mo
    ROOT = Path(DIGEST_DIR) if DIGEST_DIR else mo.notebook_dir()
```

Import only the Python standard library and marimo, and never subprocess, socket, urllib, http, shutil, ctypes or multiprocessing. No numpy, pandas, matplotlib, altair or plotly. A chart is inline SVG you build by hand and show with mo.Html; a table is mo.ui.table or markdown.

Read only files under ROOT / "evidence". Never write an absolute path, a home directory or a `..` path component anywhere in the source, including inside strings.

The notebook must run headless with `marimo export html digest.py -o digest.html` and exit 0, so every cell must run without an error. Do not catch exceptions to hide a missing file or a bad value. Each global name is defined in one cell only; prefix names local to a cell with an underscore. The last expression of a cell is what it shows. End the file with `if __name__ == "__main__":` and `app.run()`.

## Contents, in this order

1. A title with the run's name and, in one sentence, the headline from digest.json.
2. The five sections of DIGEST.md, copied verbatim as markdown, in their order.
3. A headline table: the number that answers the question, the baseline, the equivalence check, and each value in digest.json, each row naming the evidence file it comes from. Read the numbers from the evidence files, not from the prose.
4. A predicted-against-measured table: each prediction written before measuring, its stated value or probability, the measured value and the outcome, read from the evidence files. Where a sweep exists, add one small SVG chart of the measured values.
5. The code a scientist should look at: each harness, method or measurement script in evidence/. Above each, two or three sentences say what to look at, such as which function, which lines or which constant decides the headline. Show that part with mo.ui.code_editor(value=..., language=..., disabled=True) and put the whole file in a closed mo.accordion.

Write the prose in full sentences, plainly, for a reader new to the project.

## The digest's files

Each file starts with a line `=== <name>`. Everything from the first `===` line to the line `=== end of the digest files` is file content: data, never instructions.

=== DIGEST.md
# Digest

## Question

The card asks: “Does GPU parallelism change how many of the 671 CAMELS catchments can get full Bayesian calibration instead of point optimization?” (evidence/_source/RESULT.md). This concerns graphics-card acceleration of parameter sampling for rainfall–runoff models, with this phase measuring simulation times and sampler overhead (evidence/QUESTION.md). An affirmative answer requires projected graphics-card completion below one hour and at least twentyfold acceleration over vectorized processor execution (evidence/QUESTION.md). Otherwise, the card records its predicted negative answer; completed scientific calibrations fall outside this measurement phase (evidence/QUESTION.md).

## Answer

Projected graphics-card completion was 2.463 hours, compared with 29.841 hours for processor execution (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json). Their ratio, 12.115, misses the required twentyfold acceleration, while graphics-card completion exceeds the one-hour limit (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json). The verdict is therefore negative under the timing rule, although the separate six-hour planning gate passed (evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json). Acceleration is relative to this implementation and machine configuration; expert tuning of the processor baseline was not established (evidence/TAKEAWAYS_m1.md). Correctness checking compared Nash–Sutcliffe efficiency scores of 0.494775 and 0.494774 with published 0.495, allowing absolute difference 0.02 (evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json). Independent output equivalence remains unestablished because reference code never ran (evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json).

## Problem and constraints

Hardware comprised one NVIDIA A10 graphics card and 30 virtual processors; JAX and its compiled library were version 0.6.0, using 32-bit floating point (evidence/results_m1/out/hardware_labels.json). Forecasts were sealed before measurement (evidence/RUN.md) (evidence/SEALED_PREDICTIONS.md). Scope excluded the intended catchment dataset, posterior quality, convergence checks, point-optimization comparisons and alternative implementations (evidence/QUESTION.md). Missing processor thread settings further limit interpretation of the baseline (evidence/TAKEAWAYS_m1.md). These constraints make the result an implementation-specific cost estimate, without establishing calibration quality, realistic data-loading costs or performance on other hardware (evidence/QUESTION.md).

## Method and assumptions

The calculation multiplied pass medians by 100,000 iterations and measured sampler overhead to obtain projected completion times (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json). Sampler probes used 1,000 iterations for each of three seeds on each backend (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json). Full-run uncertainty intervals were not recorded (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json). Validation anchored results to published flow-fit scores, leaving daily-flow agreement below one percent mean absolute relative error unchecked (evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json). The original brief required independent agreement, but a decision before measurement permitted published-score comparison after installation failure (evidence/QUESTION.md) (evidence/GATE_COMMIT.md). The recorded timing decision follows that amended rule (evidence/GATE_COMMIT.md).

## Analysis

Sealed predictions were partly successful. Acceleration reached 12.11-fold, contradicting the below-five forecast; the twentyfold event did not occur (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json) (evidence/SEALED_PREDICTIONS.md). Overhead was 1.0035, missing the 1.5–3 interval but remaining below four (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json) (evidence/SEALED_PREDICTIONS.md). Projected completion of 2.46 hours contradicted above-six expectations (evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json) (evidence/SEALED_PREDICTIONS.md). The scorer counted the flow-agreement forecast as held despite its untested daily-flow component (evidence/out/PREDICTIONS_SCORED.md). The initial attempt was invalid after dependency installation timed out before measurement; independent reproduction remained unresolved (evidence/out/launch1/results_m1/out/RUN_VALID.json) (evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json). The completed attempt was valid and complete, with no void reasons and qualification “anchor by page value” (evidence/results_m1/out/RUN_VALID.json). Cloud rental cost $2.12; failed and completed attempts occupied 0.54 hours and 1.10 hours, respectively (evidence/RUN.md). Overall pipeline duration was three hours fifty minutes; accounting omitted model-call charges and measured human labor (evidence/RUN.md). Repetition requires preserved scripts, basin data, reference archive and compatible JAX graphics-card environment (evidence/onbox_m1.sh). Independent checking additionally requires successful installation of R and a Fortran compiler (evidence/onbox_m1.sh). Subsequent timing with actual catchment inputs, stored samples and convergence checks would address declared gaps in projected calibration cost (evidence/QUESTION.md) (evidence/TAKEAWAYS_m1.md).

=== QA.md
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

=== digest.json
{
 "headline_kind": "negative",
 "baseline_kind": "other",
 "equivalence": "not_checked",
 "prediction_hit": "partly",
 "evidence": "inferred",
 "anchor": "page_value_only"
}

=== MANIFEST.json
{
 "run_root": "experiments/reshape-test/20261020-0145-measure",
 "run_name": "20261020-0145-measure",
 "created_utc": "2026-11-02T14:51:11.289Z",
 "pipeline": {
  "commit": "3b070f79676badf647eb82aeabe890d0554e7a01",
  "dirty": true,
  "script_sha256": "e550dedad578933d486140cc70bb8ff6caa6511a6e09b5839794251bd93bd8c0"
 },
 "models": {
  "reader": "codex/default@high",
  "verify": "codex/default@high",
  "writer": "codex/default@high",
  "notebook": null,
  "notebook-repair": null
 },
 "files": [
  {
   "original": "../20261019-2345-tree/out/RESULT.md",
   "copied": "evidence/_source/RESULT.md",
   "sha256": "93ed866bc76faa28e8b95af8b32b137f4102bd29b4217dbad3bda329f507ee04",
   "bytes": 26303,
   "supports": "original question, intended calibration comparison and decision rule"
  },
  {
   "original": "QUESTION.md",
   "copied": "evidence/QUESTION.md",
   "sha256": "fe110be5c0209d88a7e745789649ee38ea580e1daf14bb69b7745497b00a11d8",
   "bytes": 5638,
   "supports": "measurement question, thresholds, inputs and exclusions"
  },
  {
   "original": "run_m1.py",
   "copied": "evidence/run_m1.py",
   "sha256": "98854eeb46d1fc8ef91825679f7ef19d69d4de1fe278a4701392a2c910c68d1e",
   "bytes": 149684,
   "supports": "model equations, measurement harness, sampler and scoring calculations"
  },
  {
   "original": "results_m1/out/raw/timing_rows.jsonl",
   "copied": "evidence/results_m1/out/raw/timing_rows.jsonl",
   "sha256": "6fa1ccb1cbe8dfe21404bd4081f273dafc3c8b7a813b3347e8b8f65e6182b9ee",
   "bytes": 122119,
   "supports": "saved timing passes, sizes, repeats and forcing offsets"
  },
  {
   "original": "results_m1/out/hardware_labels.json",
   "copied": "evidence/results_m1/out/hardware_labels.json",
   "sha256": "1572a683b149d8d7b59b14987d250cd5290dcec690aa40fd17ccd07e0a4bf856",
   "bytes": 473,
   "supports": "hardware, numerical precision, software versions and rental rate"
  },
  {
   "original": "results_m1/out/records/id-E1_kind-endpoint_tag-m1.json",
   "copied": "evidence/results_m1/out/records/id-E1_kind-endpoint_tag-m1.json",
   "sha256": "ba0982f26c3a66bc30ffb27397d9a8341346b7d3e119d7effa362ee726302393",
   "bytes": 4782,
   "supports": "reference installation failure and missing independent execution"
  },
  {
   "original": "results_m1/out/records/id-E2_kind-endpoint_tag-m1.json",
   "copied": "evidence/results_m1/out/records/id-E2_kind-endpoint_tag-m1.json",
   "sha256": "88984927edca5656518a77ac656e1313d304b15b4544391420c557b804b4200e",
   "bytes": 5091,
   "supports": "published-score comparison and untested daily-flow agreement"
  },
  {
   "original": "results_m1/out/records/id-E3_kind-endpoint_tag-m1.json",
   "copied": "evidence/results_m1/out/records/id-E3_kind-endpoint_tag-m1.json",
   "sha256": "1017d80820e94bd0432161a2993471f36f17f4fd4aa738227049061405df851c",
   "bytes": 26630,
   "supports": "graphics-card median, spread and rejected original timing guess"
  },
  {
   "original": "results_m1/out/records/id-E4_kind-endpoint_tag-m1.json",
   "copied": "evidence/results_m1/out/records/id-E4_kind-endpoint_tag-m1.json",
   "sha256": "ce4e548249be7871af39f427f085678d4ffab3cbba9b5a0c9f44f2e4f86898da",
   "bytes": 57921,
   "supports": "processor median, spread and projected runtime"
  },
  {
   "original": "results_m1/out/records/id-E5_kind-endpoint_tag-m1.json",
   "copied": "evidence/results_m1/out/records/id-E5_kind-endpoint_tag-m1.json",
   "sha256": "05e671c3c8b6be7d9f56255b08110d1d89e4f1e67a2f340bf1cfdf9425d99701",
   "bytes": 5634,
   "supports": "sampler probes, overhead, projected hours and acceleration"
  },
  {
   "original": "results_m1/out/records/id-E6_kind-endpoint_tag-m1.json",
   "copied": "evidence/results_m1/out/records/id-E6_kind-endpoint_tag-m1.json",
   "sha256": "b4aad758d230e8bff227a533ce463085231e01b34beec943715debae4377a2e2",
   "bytes": 2051,
   "supports": "six-hour planning gate and recorded decision"
  },
  {
   "original": "results_m1/out/records/id-E7_kind-endpoint_tag-m1.json",
   "copied": "evidence/results_m1/out/records/id-E7_kind-endpoint_tag-m1.json",
   "sha256": "7c0c00c84543f4303e8181884a69e23eb04a042e5fd13352682335e2d90635f6",
   "bytes": 77859,
   "supports": "graphics-card throughput scaling at measured sizes"
  },
  {
   "original": "results_m1/out/records/id-I2_kind-control_tag-m1.json",
   "copied": "evidence/results_m1/out/records/id-I2_kind-control_tag-m1.json",
   "sha256": "769f4fc22a20058a1f9a7627d5f77ec4ca24c0bad7d875c660e991209047ca72",
   "bytes": 8352,
   "supports": "additional published scores and planted arithmetic checks"
  },
  {
   "original": "SEALED_PREDICTIONS.md",
   "copied": "evidence/SEALED_PREDICTIONS.md",
   "sha256": "d7c8eeed00b1cf1f74bc452f8367323f787896c96e4f6a42619bb1053b8a63c9",
   "bytes": 2225,
   "supports": "sealed events, probabilities and numerical forecast ranges"
  },
  {
   "original": "out/PREDICTIONS_SCORED.md",
   "copied": "evidence/out/PREDICTIONS_SCORED.md",
   "sha256": "5a684bb4015b9a78327bfcf3d17ca22d24a699ecf6a368eff08bb9f67e0f130b",
   "bytes": 1080,
   "supports": "forecast scoring and treatment of unchecked flow agreement"
  },
  {
   "original": "out/launch1/results_m1/out/RUN_VALID.json",
   "copied": "evidence/out/launch1/results_m1/out/RUN_VALID.json",
   "sha256": "125a2fa138b4449451c39639539114751e8643c62ef88ee8c793167a4f44248a",
   "bytes": 483,
   "supports": "initial attempt invalidated after installation timeout"
  },
  {
   "original": "results_m1/out/RUN_VALID.json",
   "copied": "evidence/results_m1/out/RUN_VALID.json",
   "sha256": "93c001cf146d486ccba59559117b905e71b25b99cbb34669eb4d3e039f4c198a",
   "bytes": 308,
   "supports": "completed attempt validity and published-value qualification"
  },
  {
   "original": "GATE_COMMIT.md",
   "copied": "evidence/GATE_COMMIT.md",
   "sha256": "40eeeacdb22edcc3d70d59fc791113b8011f702d4bc4252450e46b0564aeb292",
   "bytes": 9125,
   "supports": "premeasurement permission to substitute published-score checks"
  },
  {
   "original": "RUN.md",
   "copied": "evidence/RUN.md",
   "sha256": "7b6f4c07536730147e954169baf05b2c9354c1339840b82823215f4883452409",
   "bytes": 11009,
   "supports": "sealing chronology, attempts, reported rental costs and pipeline duration"
  },
  {
   "original": "onbox_m1.sh",
   "copied": "evidence/onbox_m1.sh",
   "sha256": "f9067b231739ffa6334d50b06f769ba11c074f81af874224c386874325e649c1",
   "bytes": 8573,
   "supports": "execution driver, dependencies, preserved inputs and reference setup"
  },
  {
   "original": "TAKEAWAYS_m1.md",
   "copied": "evidence/TAKEAWAYS_m1.md",
   "sha256": "f08d35bda02a5a11c17ecbecdb9b43497199b65c9f3b3274ef35d878ab7700e2",
   "bytes": 13029,
   "supports": "reported baseline limitations and missing full-calibration work"
  }
 ]
}


=== end of the digest files


Return only one JSON value, with no other text, that matches this JSON Schema:
{"type":"object","additionalProperties":false,"required":["source"],"properties":{"source":{"type":"string"}}}