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

The source card asks, “Does feeding many GPUs to the block-tridiagonal Newton solve shorten its depth from T ordered steps to log2(T)?” (evidence/_source/reply.txt). This run narrows that question to scalar tridiagonal solves, comparing Thomas elimination with parallel cyclic reduction on a single graphics processor (evidence/QUESTION.md). Its declared answer requires at least twofold median speedup at 16,777,216 equations, improvement over smallest-size speedup, and positive logarithmic regression slope (evidence/QUESTION.md). Correctness checks must pass before interpreting that decision.

## Answer

At 16,777,216 equations, median Thomas and parallel cyclic reduction times were 7,598.50 and 21.8156 milliseconds, yielding 348.305-fold speedup (evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json). Paired-seed speedup ratios had interquartile width 1.089 and lower quartile 348.289 (evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json). The declared rule passed, including positive logarithmic regression slope of 0.25565, although speedup decreased across largest sizes (evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json). The headline baseline used a single graphics-processor thread per system, without unrolling or variant search (evidence/run_m2.py). The question document challenges its practical relevance and identifies processor-library Thomas as the practical sequential alternative; expert preference was not established. Correctness comparisons passed within tolerance at the checked sizes. The result answers the narrower comparison, while block-system depth and multiple-device acceleration remain untested.

## Problem and constraints

Measurements covered 1,024, 16,384, 262,144, 4,194,304, and 16,777,216 equations, with five seeded systems per implementation and size (evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json). Hardware was one NVIDIA A100 SXM4 graphics processor with 40 gigabytes; processor-library threading was restricted to one thread (evidence/results_m2/out/env.json). Inputs had diagonal entries of three, random unit-magnitude off-diagonals, standard-normal right-hand sides, and 64-bit floating-point arithmetic (evidence/QUESTION.md). Coverage used a single right-hand side and excluded ill-conditioned matrices, other precisions, block systems, multiple graphics processors, and surrounding Newton iteration (evidence/QUESTION.md). Forecasts were sealed before agents or rented hardware ran. Repeats varied generated systems on the same machine, providing no measurement of variation across machines.

## Method and assumptions

Measured implementations included hand-written Thomas and parallel cyclic reduction, batched Thomas, NVIDIA cuSPARSE, and the processor library's tridiagonal solver. Recorded software included CUDA 12.8, Python 3.10.12, NumPy 1.26.4, SciPy 1.8.0, and OpenBLAS 0.3.20 (evidence/results_m2/out/env.json). Each system received two warmups followed by a timed block of repeated solves (evidence/run_m2.py). Transfers, allocation, and required input copies occurred outside timed blocks, so timings describe data already on device. At 1,024 and 16,384 equations, seed zero, hand-written solvers were compared with cuSPARSE and SciPy's banded solver (evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json). Required relative equation residual was at most 1e-10; solution differences against references had to remain below 1e-8 (evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json). All comparisons passed, and residual instrumentation passed checks using an exact solution and a deliberately perturbed solution.

## Analysis

Ten forecast events occurred, covering compilation, correctness, smaller residuals, favorable decision, minimum speedup, earliest crossover, processor comparison, scaling, short duration, and completion (evidence/out/PREDICTIONS_SCORED.md). Two forecast events did not occur (evidence/out/PREDICTIONS_SCORED.md). Supported statements supply no numerical margins for those misses. The summary records no voids, missing records, or failed scheduled measurement stages. Some timing blocks fell below planned duration, although the summary retained its valid verdict. Optional block-system and multiple-graphics-processor phases were omitted, and isolated document-reader agents failed to run. Rental cost was $0.48 for 0.239 hours, with no total model or human cost reported (evidence/RUN.md). Measurement duration was 0.119105 hours (evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json). At 16,777,216 equations, cuSPARSE took 2.943 milliseconds versus 21.816 for hand-written parallel cyclic reduction, informing solver selection within this input family (evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json). Repetition requires saved runner, provenance helper, batch script, compatible software, and configured price, budget, and timeout variables. The proposed next measurement compares resident solves with transfer-inclusive solves; application-level acceleration remains unmeasured.

=== QA.md
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

=== digest.json
{
 "headline_kind": "speedup",
 "baseline_kind": "one_thread",
 "equivalence": "within_tolerance",
 "prediction_hit": "partly",
 "evidence": "measured",
 "anchor": "page_value_only"
}

=== MANIFEST.json
{
 "run_root": "experiments/reshape-test/20261020-0855-measure",
 "run_name": "20261020-0855-measure",
 "created_utc": "2026-11-02T15:02:43.908Z",
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
   "original": "../20261019-2344-tree/out/agents/0008-R1_physical_top_producer/reply.txt",
   "copied": "evidence/_source/reply.txt",
   "sha256": "5edcb633490ee446d7a77a8f32cf246efae31aab79919fe6b21ac4f6aa411b33",
   "bytes": 13524,
   "supports": "Original question, decision rule, baseline, historical proxy, and intended application"
  },
  {
   "original": "QUESTION.md",
   "copied": "evidence/QUESTION.md",
   "sha256": "ea54a9182df53f3e3fe6e7f5844a4e36d72a6b103d0c0f3d99425bfc79ec4810",
   "bytes": 9043,
   "supports": "Operational question, declared rules, inputs, timing plan, and scope"
  },
  {
   "original": "run_m2.py",
   "copied": "evidence/run_m2.py",
   "sha256": "46faee5d4265b7cabb92166ae3da9e88d18b5a2f084ce4146aae7a671c661af1",
   "bytes": 138132,
   "supports": "Solver implementations, correctness calculations, timing harness, and excluded transfers"
  },
  {
   "original": "results_m2/out/records/id-E3_kind-endpoint_run-m2.json",
   "copied": "evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json",
   "sha256": "10455a00abfd2fced26df3ab07b879678ade9f07986cb1f7aab20728b2130c1c",
   "bytes": 7586,
   "supports": "Measured sizes, median times, speedup spread, growth rule, and decision"
  },
  {
   "original": "results_m2/out/env.json",
   "copied": "evidence/results_m2/out/env.json",
   "sha256": "904741ef0261c0d69f0bd76e717210a9d6568468071d2bf1e946832be00b81fd",
   "bytes": 1960,
   "supports": "Recorded hardware, software versions, threading, and library linkage"
  },
  {
   "original": "results_m2/out/m2_summary.json",
   "copied": "evidence/results_m2/out/m2_summary.json",
   "sha256": "2ce06d98b7fc147a7dc24f0a291f8e42a77a76b918a7b80543bed900676c575f",
   "bytes": 10927,
   "supports": "Completion, validity, missing records, voids, and repeat interpretation"
  },
  {
   "original": "results_m2/out/records/id-E1_kind-endpoint_run-m2.json",
   "copied": "evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json",
   "sha256": "6caefc8106d8d239fc38db4025cd4f5282a348faaab2ce6b7420c75e861e3b7c",
   "bytes": 10390,
   "supports": "Correctness references, tolerances, residuals, and solution comparisons"
  },
  {
   "original": "results_m2/out/records/id-I1_exact_kind-control_run-m2.json",
   "copied": "evidence/results_m2/out/records/id-I1_exact_kind-control_run-m2.json",
   "sha256": "9cfb35718c0e69659c35b2bbec6b893b23c894d9b409cd854e4636fd7f6ee88f",
   "bytes": 3183,
   "supports": "Known exact-solution residual instrumentation check"
  },
  {
   "original": "results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json",
   "copied": "evidence/results_m2/out/records/id-I1_perturbed_kind-control_run-m2.json",
   "sha256": "b1440c79273ae7c493185584e713bc2a20cb0e368d909864b561b06a5d7e3a9a",
   "bytes": 3228,
   "supports": "Deliberately perturbed-solution residual instrumentation check"
  },
  {
   "original": "SEALED_PREDICTIONS.md",
   "copied": "evidence/SEALED_PREDICTIONS.md",
   "sha256": "169bb51e31dc9c25d2ae76a6c21e153f8c2522b9b46edceb8dde4df15c58032e",
   "bytes": 3207,
   "supports": "Forecasts recorded before measurement"
  },
  {
   "original": "out/PREDICTIONS_SCORED.md",
   "copied": "evidence/out/PREDICTIONS_SCORED.md",
   "sha256": "82741fdb26752e5eb614b0d1412338bc11ec7cee9e83538e2ad391663ccb15cb",
   "bytes": 2716,
   "supports": "Scoring of sealed forecast events"
  },
  {
   "original": "results_m2/out/records/id-E7_kind-endpoint_run-m2.json",
   "copied": "evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json",
   "sha256": "044600bfb4aed31dd2e3e8d7326c1d5967bfa6cbdb02bab6a56a3c2df1a92e6e",
   "bytes": 7279,
   "supports": "Measured comparison against processor-library tridiagonal solver"
  },
  {
   "original": "results_m2/out/records/id-E9_kind-endpoint_run-m2.json",
   "copied": "evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json",
   "sha256": "af01f12cf6dfb7ad089f16047ff7be8deb9c6ba0865f98c75a86f9e2049ff526",
   "bytes": 4733,
   "supports": "Measured cuSPARSE times and comparison against hand-written parallel solver"
  },
  {
   "original": "RUN.md",
   "copied": "evidence/RUN.md",
   "sha256": "fc44a6305dcff96e8a2ac7eaf22355d9926b5a24e8d19d9fe5b2289a8eb7fde8",
   "bytes": 10627,
   "supports": "Operator timeline, rental accounting, omitted phases, and reader failures"
  },
  {
   "original": "results_m2/out/rows/pcr_gpu.jsonl",
   "copied": "evidence/results_m2/out/rows/pcr_gpu.jsonl",
   "sha256": "f73af1752f6073f9d187026a202bfb8a69e8971b93acb92065704eb53fd44c7a",
   "bytes": 70936,
   "supports": "Saved parallel-solver timing blocks and short-block count"
  },
  {
   "original": "results_m2/out/records/id-E10_kind-endpoint_run-m2.json",
   "copied": "evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json",
   "sha256": "190693c1474d10e921a878d9d007cb0f9ab392ed8bdf362edc36e102d033ffcb",
   "bytes": 4834,
   "supports": "Measured first-anchor-to-last-sweep duration"
  },
  {
   "original": "onbox_m2.sh",
   "copied": "evidence/onbox_m2.sh",
   "sha256": "3cfe0f6da24a0ba1ed46b4b17dec4ea8b91f34db27b7d2bdd20ce5ee408f5453",
   "bytes": 3710,
   "supports": "Batch execution sequence, required files, and runtime configuration"
  },
  {
   "original": "TAKEAWAYS_m2.md",
   "copied": "evidence/TAKEAWAYS_m2.md",
   "sha256": "9efcbde683d596d1b7a4d4f75b2ceed9e494fe5c303c865e834938d43ea5ce96",
   "bytes": 28264,
   "supports": "Proposed measurement including graphics-processor transfers"
  }
 ]
}


=== end of the digest files


Return only one JSON value, with no other text, that matches this JSON Schema:
{"type":"object","additionalProperties":false,"required":["source"],"properties":{"source":{"type":"string"}}}