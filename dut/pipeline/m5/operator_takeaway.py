"""Write a mechanical operator takeaway from validated m5 signatures only."""
import argparse
from pathlib import Path

if __package__:
    from .signatures import FACTS, signatures, validate
else:
    from signatures import FACTS, signatures, validate


def takeaway(records, raid=None):
    records = list(records)
    if any(validate(record) for record in records):
        raise ValueError("invalid signature")
    stages = {r["signature"]["stage"]: r for r in records if r["signature"]["kind"] == "stage"}
    lines = ["# Operator takeaway" + (f" — raid: {raid}" if raid is not None else ""), "",
             "| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio |",
             "|---|---|---|---|---|---|---|---|---|"]
    columns = ("vote_share", "speedup_published", "speedup_tuned", "expected_speedup",
               "cost_ratio", "prediction_ratio")
    for stage, schema in FACTS.items():
        entry = stages.get(stage)
        facts = entry["facts"] if entry else dict.fromkeys(schema)
        status = entry["signature"]["status"] if entry else "SKIPPED"
        flags = {key: facts[key] for key, spec in schema.items()
                 if spec is bool and key not in ("tokens_known", "gpu_busy_known")}
        flags.update({key: entry["signature"][key] if entry else None
                      for key in ("run_valid", "calibration_valid")})
        rendered = ", ".join(f"{key}={str(value).lower() if value is not None else 'null'}"
                             for key, value in flags.items())
        values = [str(facts[key]) if facts.get(key) is not None else "null" for key in columns]
        lines.append("| " + " | ".join([stage, status, rendered, *values]) + " |")
    rows = [r["signature"] for r in records]
    launches = [r for r in rows if r["kind"] == "launch"]
    stage_rows = [r for r in rows if r["kind"] == "stage"]
    calls = [r for r in rows if r["kind"] == "model_call"]
    # Costs use launch records when present; tokens use model_call records when present.
    # Each falls back to stage records only when its preferred kind is absent; never mix kinds.
    costs, tokens = launches or stage_rows, calls or stage_rows
    totals = {key: sum(r[key] for r in costs) for key in ("wall_s", "gpu_s", "usd")}
    totals.update({key: sum(r[key] for r in tokens) for key in ("tokens_in", "tokens_out")})
    lines += ["", "## Totals", "", "| " + " | ".join(totals) + " |",
              "|" + "---|" * len(totals),
              "| " + " | ".join(str(value) for value in totals.values()) + " |",
              "", "Unknown token counts and GPU-busy telemetry remain unavailable; numeric totals cover recorded values only."]
    blockers = sorted({b for r in rows for b in r["blockers"]} - {"none"}) or ["none"]
    lines += ["", "## Blockers", ""] + [f"- {blocker}" for blocker in blockers]
    return "\n".join(lines + ["", "This page is mechanical and holds no domain content.", ""])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("S_dir")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--raid")
    args = parser.parse_args()
    try:
        page = takeaway(signatures(args.S_dir), args.raid)
        output = args.out if args.out is not None else Path(args.S_dir) / "OPERATOR_TAKEAWAY.md"
        output.write_text(page)
    except (OSError, ValueError):
        parser.exit(1, "invalid signatures or output unavailable\n")
