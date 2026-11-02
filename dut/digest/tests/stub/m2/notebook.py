import marimo

app = marimo.App(width="medium")

with app.setup:
    DIGEST_DIR = ""  # empty: this notebook's own directory
    import json
    import math
    from pathlib import Path
    import marimo as mo
    ROOT = Path(DIGEST_DIR) if DIGEST_DIR else mo.notebook_dir()
    EV = ROOT / "evidence"


@app.cell
def _():
    # STUB notebook for the dry run of dut/digest, written by hand; the five sections are copied from the prompt.
    SECTIONS = __SECTIONS__
    ENUMS = {"headline_kind": "speedup", "baseline_kind": "one_thread", "equivalence": "within_tolerance",
             "prediction_hit": "partly", "evidence": "measured", "anchor": "measured"}
    mo.md("# Digest of 20261020-0855-measure\n\nThe card's own rule reads lever: the parallel solver beat one GPU thread "
          "running Thomas by a wide margin at every size, and one CPU core by a narrower one.")
    return ENUMS, SECTIONS


@app.cell
def _(SECTIONS):
    mo.md("\n\n".join(f"## {h}\n\n{SECTIONS[h]}" for h in SECTIONS))
    return


@app.cell
def _():
    def record(name):
        return json.loads((EV / "results_m2" / "out" / "records" / name).read_text())
    E1 = record("id-E1_kind-endpoint_run-m2.json")
    E3 = record("id-E3_kind-endpoint_run-m2.json")
    E7 = record("id-E7_kind-endpoint_run-m2.json")
    return E1, E3, E7


@app.cell
def _(E1, E3, E7, ENUMS):
    _top3, _top7 = E3["values"]["table"][-1], E7["values"]["table"][-1]
    _src3, _src7 = "evidence/results_m2/out/records/id-E3_kind-endpoint_run-m2.json", "evidence/results_m2/out/records/id-E7_kind-endpoint_run-m2.json"
    _rows = [
        {"item": "speedup at 2^24, one GPU thread", "value": round(_top3["speedup"], 2), "source": _src3},
        {"item": "speedup at 2^24, one CPU core", "value": round(_top7["speedup"], 2), "source": _src7},
        {"item": "parallel solver median ms at 2^24", "value": round(_top3["median_denominator_ms"], 3), "source": _src3},
        {"item": "CPU library median ms at 2^24", "value": round(_top7["median_numerator_ms"], 1), "source": _src7},
        {"item": "anchor decision", "value": E1["decision"], "source": "evidence/results_m2/out/records/id-E1_kind-endpoint_run-m2.json"},
        {"item": "card rule decision", "value": E3["decision"], "source": _src3},
    ] + [{"item": k, "value": v, "source": "digest.json"} for k, v in ENUMS.items()]
    mo.vstack([mo.md("## Headline"), mo.ui.table(_rows, selection=None)])
    return


@app.cell
def _():
    _lines = (EV / "out" / "PREDICTIONS_SCORED.md").read_text().splitlines()
    _rows = []
    for _l in _lines:
        _cells = [c.strip() for c in _l.strip().strip("|").split("|")]
        if _l.startswith("| P") and len(_cells) >= 6:
            _rows.append({"prediction": _cells[0], "stated": _cells[1], "probability": _cells[2], "outcome": _cells[3], "measured": _cells[4]})
    mo.vstack([mo.md("## Predicted against measured\n\nSealed before any agent ran; scored by the operator against the records."),
               mo.ui.table(_rows, selection=None)])
    return


@app.cell
def _(E3, E7):
    def chart(series, w=520, h=220, pad=40):
        _xs = [x for _, pts in series for x, _ in pts]
        _ys = [math.log10(y) for _, pts in series for _, y in pts]
        x0, x1, y0, y1 = min(_xs), max(_xs), math.floor(min(_ys)), math.ceil(max(_ys))
        sx = lambda x: pad + (x - x0) / (x1 - x0) * (w - 2 * pad)
        sy = lambda y: h - pad - (math.log10(y) - y0) / (y1 - y0) * (h - 2 * pad)
        parts = [f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg" font-size="11">']
        for e in range(y0, y1 + 1):
            yy = h - pad - (e - y0) / (y1 - y0) * (h - 2 * pad)
            parts.append(f'<line x1="{pad}" x2="{w - pad}" y1="{yy}" y2="{yy}" stroke="#ddd"/><text x="4" y="{yy + 4}">1e{e}</text>')
        for x in sorted(set(_xs)):
            parts.append(f'<text x="{sx(x) - 10}" y="{h - pad + 16}">2^{x}</text>')
        for (name, pts), color in zip(series, ["#2b6cb0", "#c05621"]):
            d = " ".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in pts)
            parts.append(f'<polyline points="{d}" fill="none" stroke="{color}" stroke-width="2"/>')
            parts.append(f'<text x="{sx(pts[-1][0]) - 120}" y="{sy(pts[-1][1]) - 6}" fill="{color}">{name}</text>')
        return "".join(parts) + "</svg>"
    _s3 = [(r["log2_N"], r["speedup"]) for r in E3["values"]["table"]]
    _s7 = [(r["log2_N"], r["speedup"]) for r in E7["values"]["table"]]
    mo.vstack([mo.md("Speedup of the parallel solver by size, log scale."),
               mo.Html(chart([("over one GPU thread", _s3), ("over one CPU core", _s7)]))])
    return


@app.cell
def _():
    _runner = (EV / "run_m2.py").read_text()
    _start, _end = _runner.index("def speedup_table"), _runner.index("def lever_from_tables")
    _onbox = (EV / "onbox_m2.sh").read_text()
    mo.vstack([
        mo.md("## Code to read\n\nIn the runner, `speedup_table` divides the median baseline time by the median parallel "
              "time per size, and `decide_lever` applies the card's rule. Check that both medians come from the same seeds."),
        mo.ui.code_editor(value=_runner[_start:_end], language="python", disabled=True),
        mo.accordion({"run_m2.py, whole file": mo.ui.code_editor(value=_runner, language="python", disabled=True)}),
        mo.md("The on-box script runs the runner's stages in order behind a spend guard. Check which stages ran and the time cap per stage."),
        mo.accordion({"onbox_m2.sh, whole file": mo.ui.code_editor(value=_onbox, language="shell", disabled=True)}),
    ])
    return


if __name__ == "__main__":
    app.run()
