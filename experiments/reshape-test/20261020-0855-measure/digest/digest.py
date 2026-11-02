import marimo

app = marimo.App(width="medium")

with app.setup:
    DIGEST_DIR = ""  # empty: this notebook's own directory
    import json
    from pathlib import Path
    import marimo as mo
    ROOT = Path(DIGEST_DIR) if DIGEST_DIR else mo.notebook_dir()


@app.cell
def _():
    evidence_dir = ROOT / "evidence"
    record_dir = evidence_dir / "results_m2" / "out" / "records"
    e1_file = "evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json"
    e3_file = "evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json"
    e7_file = "evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json"
    e9_file = "evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json"
    e10_file = "evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json"
    e1 = json.loads((record_dir / "id-E1_kind-endpoint_run-m2.json").read_text())
    e3 = json.loads((record_dir / "id-E3_kind-endpoint_run-m2.json").read_text())
    e7 = json.loads((record_dir / "id-E7_kind-endpoint_run-m2.json").read_text())
    e9 = json.loads((record_dir / "id-E9_kind-endpoint_run-m2.json").read_text())
    e10 = json.loads((record_dir / "id-E10_kind-endpoint_run-m2.json").read_text())
    summary = json.loads((evidence_dir / "results_m2" / "out" / "m2_summary.json").read_text())
    sweep = e3["values"]["table"]
    top = sweep[-1]
    return evidence_dir, e1_file, e3_file, e7_file, e9_file, e10_file, e1, e3, e7, e9, e10, summary, sweep, top


@app.cell
def _(top):
    mo.md(f"# 20261020-0855-measure\n\nThis run measured a {top['speedup']:.3f}-fold speedup for parallel cyclic reduction over one-thread GPU Thomas elimination, with correctness within tolerance at the checked sizes and only partial agreement with the sealed predictions.")
    return


@app.cell
def _():
    mo.md("""## Question

The source card asks, “Does feeding many GPUs to the block-tridiagonal Newton solve shorten its depth from T ordered steps to log2(T)?” (evidence/_source/reply.txt). This run narrows that question to scalar tridiagonal solves, comparing Thomas elimination with parallel cyclic reduction on a single graphics processor (evidence/QUESTION.md). Its declared answer requires at least twofold median speedup at 16,777,216 equations, improvement over smallest-size speedup, and positive logarithmic regression slope (evidence/QUESTION.md). Correctness checks must pass before interpreting that decision.

## Answer

At 16,777,216 equations, median Thomas and parallel cyclic reduction times were 7,598.50 and 21.8156 milliseconds, yielding 348.305-fold speedup (evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json). Paired-seed speedup ratios had interquartile width 1.089 and lower quartile 348.289 (evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json). The declared rule passed, including positive logarithmic regression slope of 0.25565, although speedup decreased across largest sizes (evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json). The headline baseline used a single graphics-processor thread per system, without unrolling or variant search (evidence/run_m2.py). The question document challenges its practical relevance and identifies processor-library Thomas as the practical sequential alternative; expert preference was not established. Correctness comparisons passed within tolerance at the checked sizes. The result answers the narrower comparison, while block-system depth and multiple-device acceleration remain untested.

## Problem and constraints

Measurements covered 1,024, 16,384, 262,144, 4,194,304, and 16,777,216 equations, with five seeded systems per implementation and size (evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json). Hardware was one NVIDIA A100 SXM4 graphics processor with 40 gigabytes; processor-library threading was restricted to one thread (evidence/results_m2/out/env.json). Inputs had diagonal entries of three, random unit-magnitude off-diagonals, standard-normal right-hand sides, and 64-bit floating-point arithmetic (evidence/QUESTION.md). Coverage used a single right-hand side and excluded ill-conditioned matrices, other precisions, block systems, multiple graphics processors, and surrounding Newton iteration (evidence/QUESTION.md). Forecasts were sealed before agents or rented hardware ran. Repeats varied generated systems on the same machine, providing no measurement of variation across machines.

## Method and assumptions

Measured implementations included hand-written Thomas and parallel cyclic reduction, batched Thomas, NVIDIA cuSPARSE, and the processor library's tridiagonal solver. Recorded software included CUDA 12.8, Python 3.10.12, NumPy 1.26.4, SciPy 1.8.0, and OpenBLAS 0.3.20 (evidence/results_m2/out/env.json). Each system received two warmups followed by a timed block of repeated solves (evidence/run_m2.py). Transfers, allocation, and required input copies occurred outside timed blocks, so timings describe data already on device. At 1,024 and 16,384 equations, seed zero, hand-written solvers were compared with cuSPARSE and SciPy's banded solver (evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json). Required relative equation residual was at most 1e-10; solution differences against references had to remain below 1e-8 (evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json). All comparisons passed, and residual instrumentation passed checks using an exact solution and a deliberately perturbed solution.

## Analysis

Ten forecast events occurred, covering compilation, correctness, smaller residuals, favorable decision, minimum speedup, earliest crossover, processor comparison, scaling, short duration, and completion (evidence/out/PREDICTIONS_SCORED.md). Two forecast events did not occur (evidence/out/PREDICTIONS_SCORED.md). Supported statements supply no numerical margins for those misses. The summary records no voids, missing records, or failed scheduled measurement stages. Some timing blocks fell below planned duration, although the summary retained its valid verdict. Optional block-system and multiple-graphics-processor phases were omitted, and isolated document-reader agents failed to run. Rental cost was $0.48 for 0.239 hours, with no total model or human cost reported (evidence/RUN.md). Measurement duration was 0.119105 hours (evidence/results_m2/out/records/id-E10_kind-endpoint_run-m2.json). At 16,777,216 equations, cuSPARSE took 2.943 milliseconds versus 21.816 for hand-written parallel cyclic reduction, informing solver selection within this input family (evidence/results_m2/out/records/id-E9_kind-endpoint_run-m2.json). Repetition requires saved runner, provenance helper, batch script, compatible software, and configured price, budget, and timeout variables. The proposed next measurement compares resident solves with transfer-inclusive solves; application-level acceleration remains unmeasured.""")
    return


@app.cell
def _(evidence_dir):
    def prediction_rows(text):
        _rows = {}
        for _line in text.splitlines():
            if _line.startswith("|"):
                _parts = [_part.strip() for _part in _line.strip().strip("|").split("|")]
                if _parts[0].startswith("P") and _parts[0][1:2].isdigit():
                    _rows[_parts[0]] = _parts
        return _rows

    sealed_predictions = prediction_rows((evidence_dir / "SEALED_PREDICTIONS.md").read_text())
    scored_predictions = prediction_rows((evidence_dir / "out" / "PREDICTIONS_SCORED.md").read_text())
    return sealed_predictions, scored_predictions


@app.cell
def _(e1, e3, e7, e9, e10, top, sweep, e1_file, e3_file, e7_file, e9_file, e10_file, scored_predictions):
    _levels = e1["values"]["levels"]
    max_residual = max(_lv[_solver]["res"] for _lv in _levels for _solver in ("thomas", "pcr"))
    _max_diff = max(_lv[_solver][_ref] for _lv in _levels for _solver in ("thomas", "pcr") for _ref in ("diff_cusparse", "diff_scipy"))
    _held = sum(_row[3].startswith("held") for _row in scored_predictions.values())
    _rows = [
        {"Quantity": "Headline speedup at the largest size", "Value": f"{top['speedup']:.9g} times", "Evidence file": e3_file},
        {"Quantity": "Equations at the headline size", "Value": str(top["N"]), "Evidence file": e3_file},
        {"Quantity": "Baseline median time", "Value": f"{top['median_numerator_ms']:.9g} ms", "Evidence file": e3_file},
        {"Quantity": "Parallel cyclic reduction median time", "Value": f"{top['median_denominator_ms']:.9g} ms", "Evidence file": e3_file},
        {"Quantity": "Baseline implementation", "Value": e3["values"]["labels"]["baseline"], "Evidence file": "evidence/run_m2.py; " + e3_file},
        {"Quantity": "Paired-seed speedup interquartile width", "Value": f"{top['iqr_ratio']:.9g}", "Evidence file": e3_file},
        {"Quantity": "Paired-seed speedup lower quartile", "Value": f"{top['lower_quartile_ratio']:.9g}", "Evidence file": e3_file},
        {"Quantity": "Decision", "Value": e3["decision"], "Evidence file": e3_file},
        {"Quantity": "Decision rule", "Value": e3["decision_rule"], "Evidence file": e3_file},
        {"Quantity": "Slope of ln(speedup) against log2(N)", "Value": str(e3["values"]["slope_ln_speedup_per_log2N"]), "Evidence file": e3_file},
        {"Quantity": "Smallest-size speedup", "Value": str(sweep[0]["speedup"]), "Evidence file": e3_file},
        {"Quantity": "Correctness decision", "Value": e1["decision"], "Evidence file": e1_file},
        {"Quantity": "Correctness sizes", "Value": ", ".join(str(_lv["N"]) for _lv in _levels), "Evidence file": e1_file},
        {"Quantity": "Maximum hand-written solver relative residual", "Value": str(max_residual), "Evidence file": e1_file},
        {"Quantity": "Residual tolerance (inclusive)", "Value": str(e1["threshold"]["residual_max"]), "Evidence file": e1_file},
        {"Quantity": "Maximum hand-written solution difference against either reference", "Value": str(_max_diff), "Evidence file": e1_file},
        {"Quantity": "Solution difference tolerance (exclusive)", "Value": str(e1["threshold"]["difference_max_exclusive"]), "Evidence file": e1_file},
        {"Quantity": "References agree", "Value": str(e1["values"]["references_agree"]), "Evidence file": e1_file},
        {"Quantity": "CPU-library baseline speedup at the largest size", "Value": str(e7["values"]["table"][-1]["speedup"]), "Evidence file": e7_file},
        {"Quantity": "cuSPARSE median time at the largest size", "Value": f"{e9['values']['median_cusparse_ms'][-1]:.9g} ms", "Evidence file": e9_file},
        {"Quantity": "Measurement duration", "Value": f"{e10['values']['hours']:.9g} hours", "Evidence file": e10_file},
        {"Quantity": "digest.json: headline_kind", "Value": "speedup", "Evidence file": e3_file},
        {"Quantity": "digest.json: baseline_kind", "Value": "one_thread", "Evidence file": "evidence/run_m2.py; " + e3_file},
        {"Quantity": "digest.json: equivalence", "Value": "within_tolerance", "Evidence file": e1_file},
        {"Quantity": "digest.json: prediction_hit", "Value": f"partly ({_held} of {len(scored_predictions)} predicted events occurred)", "Evidence file": "evidence/SEALED_PREDICTIONS.md; evidence/out/PREDICTIONS_SCORED.md"},
        {"Quantity": "digest.json: evidence", "Value": "measured", "Evidence file": e3_file},
        {"Quantity": "digest.json: anchor", "Value": "page_value_only", "Evidence file": "evidence/_source/reply.txt; " + e1_file + "; " + e3_file},
    ]
    mo.vstack([
        mo.md("## Headline and its evidence\n\nThe numerical rows below are loaded from the saved measurement records. The six rows labelled `digest.json` reproduce the supplied digest categories and name the evidence used to interpret them. The `page_value_only` category describes the source card's quoted proxy; the run's separate correctness anchor compares actual computed solutions.\n\nSpeedup is a ratio of median times, while its interquartile width describes the five paired-seed ratios. Correctness was checked against both cuSPARSE and SciPy at the two recorded anchor sizes; these checks do not establish equivalence at every size or for block systems."),
        mo.ui.table(_rows, selection=None, pagination=False),
    ])
    return max_residual,


@app.cell
def _(sealed_predictions, scored_predictions, e1, e3, e7, e9, e10, summary, sweep, top, max_residual, e1_file, e3_file, e7_file, e9_file, e10_file):
    _growth = (sweep[-1]["median_denominator_ms"] / sweep[-2]["median_denominator_ms"]) ** (1 / (sweep[-1]["log2_N"] - sweep[-2]["log2_N"]))
    _measured = {
        "P2": (f"{e1['decision']}; maximum residual {max_residual:.9g}; references agree: {e1['values']['references_agree']}", e1_file),
        "P3": (f"Maximum residual {max_residual:.9g}; {1e-13 / max_residual:.6g} times below the sealed guess", e1_file),
        "P4": (f"{e3['decision']}; top speedup {top['speedup']:.9g}; slope {e3['values']['slope_ln_speedup_per_log2N']:.9g}", e3_file),
        "P5": (f"{top['speedup']:.9g} times", e3_file),
        "P6": (f"First measured size with speedup above one: {next(_r['N'] for _r in sweep if _r['speedup'] > 1)}; launch fraction {e3['values']['launch_fraction_2e10']:.9g}", e3_file),
        "P7": (f"{e7['values']['table'][-1]['speedup']:.9g} times", e7_file),
        "P7b": (f"{e7['values']['table'][-1]['speedup']:.9g} times; exceeds two by {e7['values']['table'][-1]['speedup'] - 2:.9g}", e7_file),
        "P8": (f"Per-doubling growth {_growth:.9g}, calculated from the two largest-size PCR medians", e3_file),
        "P9": (f"{e10['values']['hours'] * 60:.9g} minutes; sealed two-hour estimate divided by measured duration: {e10['values']['card_need_hours'] / e10['values']['hours']:.9g}", e10_file),
        "P10": (f"PCR/cuSPARSE time ratio {e9['values']['pcr_over_cusparse'][-1]:.9g}; exceeds three by {e9['values']['pcr_over_cusparse'][-1] - 3:.9g}", e9_file),
        "P11": (f"{scored_predictions['P11'][4]}; saved E3 decision: {summary['decisions']['E3']['decision']}", "evidence/out/PREDICTIONS_SCORED.md; evidence/results_m2/out/m2_summary.json"),
    }
    _rows = []
    for _key, _sealed in sealed_predictions.items():
        _score = scored_predictions[_key]
        _value, _file = _measured.get(_key, (_score[4], "evidence/out/PREDICTIONS_SCORED.md"))
        _rows.append({
            "ID": _key,
            "Prediction sealed before measuring": _sealed[1],
            "Probability": float(_sealed[2]),
            "Measured value": _value,
            "Recorded outcome": _score[3],
            "Prediction evidence": "evidence/SEALED_PREDICTIONS.md",
            "Measurement evidence": _file,
            "Scoring evidence": "evidence/out/PREDICTIONS_SCORED.md",
        })
    mo.vstack([
        mo.md("## Predictions against measurements\n\nThe prediction text and probabilities come from the sealed forecast file. Outcomes come from its scoring file, and numerical measurements come from the corresponding saved records where available. Compilation and first-launch completion use the scored account because their original logs are outside this evidence set.\n\nAn event marked ‘did not occur’ is a failed event prediction, regardless of its probability. The two numerical margins below are calculated directly from the saved ratios. The earliest crossover is the first tested size, so the run does not locate a crossover between untested sizes."),
        mo.ui.table(_rows, selection=None, pagination=False),
    ])
    return


@app.cell
def _(sweep, e3_file):
    _parts = [
        '<svg viewBox="0 0 640 300" role="img" aria-label="Measured Thomas to PCR speedup by log2 equation count" style="width:100%;background:white;color:black">',
        '<text x="60" y="20" font-size="15">Measured Thomas / PCR speedup</text>',
        '<path d="M60 40 V240 H600" fill="none" stroke="black"/>',
    ]
    for _tick in (0, 100, 200, 300, 400, 500, 600):
        _y = 240 - _tick / 600 * 200
        _parts.append(f'<path d="M60 {_y} H600" stroke="#ddd"/><text x="50" y="{_y + 4}" text-anchor="end" font-size="11">{_tick}</text>')
    _points = []
    for _row in sweep:
        _x = 60 + (_row["log2_N"] - 10) / 14 * 540
        _y = 240 - _row["speedup"] / 600 * 200
        _points.append(f"{_x},{_y}")
        _parts.append(f'<circle cx="{_x}" cy="{_y}" r="4" fill="#1261a0"><title>N={_row["N"]}; speedup={_row["speedup"]:.6g}</title></circle>')
        _parts.append(f'<text x="{_x}" y="260" text-anchor="middle" font-size="11">{_row["log2_N"]}</text>')
        _parts.append(f'<text x="{_x}" y="{_y - 10}" text-anchor="middle" font-size="11">{_row["speedup"]:.1f}</text>')
    _parts.append('<polyline points="' + ' '.join(_points) + '" fill="none" stroke="#1261a0" stroke-width="2"/>')
    _parts.append('<text x="330" y="288" text-anchor="middle" font-size="12">log2(number of equations)</text></svg>')
    mo.vstack([
        mo.Html("".join(_parts)),
        mo.md(f"The horizontal axis is logarithmic in equation count; the vertical axis is a linear speedup ratio. Points are ratios of medians over five seeds on one machine, read from `{e3_file}`. Connecting lines guide the eye. The decrease at the largest sizes shows why a positive fitted slope does not establish monotonic growth."),
        mo.ui.table([
            {"Equations": _r["N"], "Thomas median ms": _r["median_numerator_ms"], "PCR median ms": _r["median_denominator_ms"], "Speedup": _r["speedup"], "Paired ratio IQR": _r["iqr_ratio"], "Evidence file": e3_file}
            for _r in sweep
        ], selection=None, pagination=False),
    ])
    return


@app.cell
def _(evidence_dir):
    runner_source = (evidence_dir / "run_m2.py").read_text()
    batch_source = (evidence_dir / "onbox_m2.sh").read_text()
    mo.md("## Code to inspect\n\nThe evidence includes two executable scripts: the measurement runner and the batch harness. The following excerpts are displayed as text, and the complete files are available in closed accordions. The notebook never imports or executes these scripts.")
    return runner_source, batch_source


@app.cell
def _(runner_source):
    _lines = runner_source.splitlines()
    mo.vstack([
        mo.md("### Measurement runner: evidence/run_m2.py\n\nInspect `GATE_SPEEDUP` in lines 57–70 and `speedup_table` and `decide_lever` in lines 728–755: these define the ratio of medians, the twofold threshold, the comparison with the smallest size, and the regression test that decides the headline. Inspect `m2_thomas_kernel` and `m2_pcr_round` near lines 190–255 to see the single-thread recurrence and the parallel work performed in each reduction round."),
        mo.ui.code_editor(value="\n".join(_lines[56:70]), language="python", disabled=True),
        mo.ui.code_editor(value="\n".join(_lines[727:755]), language="python", disabled=True),
        mo.ui.code_editor(value="\n".join(_lines[189:255]), language="cpp", disabled=True),
        mo.md("Inspect `rel_residual_np` and `rel_diff_np` near lines 1130–1156 to check how equation residuals and reference differences are normalized. Inspect `time_cell` near lines 1342–1353 and `run_gpu_arm` near lines 1895–1945 to see how two warmups set the repeat count and which preparation steps occur outside each timed block. These details determine whether the correctness and timing claims match the intended experiment."),
        mo.ui.code_editor(value="\n".join(_lines[1129:1156]), language="python", disabled=True),
        mo.ui.code_editor(value="\n".join(_lines[1341:1353]), language="python", disabled=True),
        mo.ui.code_editor(value="\n".join(_lines[1894:1945]), language="python", disabled=True),
        mo.accordion({"Complete evidence/run_m2.py": mo.ui.code_editor(value=runner_source, language="python", disabled=True)}, lazy=False),
    ])
    return


@app.cell
def _(batch_source):
    _lines = batch_source.splitlines()
    mo.vstack([
        mo.md("### Batch harness: evidence/onbox_m2.sh\n\nInspect `STAGES` and the thread environment settings near lines 14–22 to see the order of measurement and the one-thread CPU-library constraint. Inspect the stage loop near the end to see how price, remaining budget, and timeout control execution, and how a failure reaches the final summary. The required-file loop also names the provenance helper needed to repeat the run; that helper is not included in this evidence set."),
        mo.ui.code_editor(value="\n".join(_lines[13:22]), language="shell", disabled=True),
        mo.ui.code_editor(value="\n".join(_lines[45:]), language="shell", disabled=True),
        mo.accordion({"Complete evidence/onbox_m2.sh": mo.ui.code_editor(value=batch_source, language="shell", disabled=True)}, lazy=False),
    ])
    return


if __name__ == "__main__":
    app.run()
