"""Write a mechanical operator takeaway from validated m5 signatures only."""
import argparse
import json
import math
from pathlib import Path

if __package__:
    from .signatures import FACTS, signatures, validate
else:
    from signatures import FACTS, signatures, validate


BOX_TYPES = {
    "gpu_1x_a10", "gpu_1x_a100", "gpu_1x_a100_sxm4", "gpu_1x_a100_sxm4_80gb",
    "gpu_8x_a100", "gpu_8x_a100_80gb_sxm4", "gpu_1x_h100_pcie", "gpu_1x_h100_sxm5",
    "gpu_8x_h100_sxm5", "gpu_1x_gh200", "gpu_1x_h200", "gpu_8x_h200_sxm5",
    "gpu_1x_b200", "gpu_8x_b200",
}


def takeaway(records, raid=None, box=None):
    records = list(records)
    if any(validate(record) for record in records):
        raise ValueError("invalid signature")
    stages = {r["signature"]["stage"]: r for r in records if r["signature"]["kind"] == "stage"}
    compute = ("wall_s", "gpu_s", "usd", "tokens_in", "tokens_out", "model_family")
    lines = ["# Operator takeaway" + (f" — raid: {raid}" if raid is not None else ""), "", "## Compute", "",
             "| Stage | Status | Gate flags | Vote share | Speedup published | Speedup tuned | Expected speedup | Cost ratio | Prediction ratio | " + " | ".join(compute) + " |",
             "|" + "---|" * (9 + len(compute))]
    columns = ("vote_share", "speedup_published", "speedup_tuned", "expected_speedup",
               "cost_ratio", "prediction_ratio")
    for stage, schema in FACTS.items():
        entry = stages.get(stage)
        facts = entry["facts"] if entry else dict.fromkeys(schema)
        status = entry["signature"]["status"] if entry else "SKIPPED"
        flags = {key: facts[key] for key, spec in schema.items()
                 if spec is bool and key not in ("tokens_known", "gpu_busy_known")}
        if stage == "intake":
            flags["anchored"] = facts.get("anchored")
        flags.update({key: entry["signature"][key] if entry else None
                      for key in ("run_valid", "calibration_valid")})
        rendered = ", ".join(f"{key}={str(value).lower() if value is not None else 'null'}"
                             for key, value in flags.items())
        if stage == "propose":
            ballots = {key: facts.get(key) for key in ("votes_approve", "votes_reject", "votes_abstain")}
            ballots["votes_null"] = (5 - sum(ballots.values())
                                     if facts.get("outcome") in ("approved", "rejected", "conditions_unmet")
                                     and all(value is not None for value in ballots.values()) else None)
            rendered += ", outcome=" + (facts.get("outcome") or "null")
            rendered += ", " + ", ".join(f"{key}={value if value is not None else 'null'}"
                                        for key, value in ballots.items())
        values = [str(facts[key]) if facts.get(key) is not None else "null" for key in columns]
        values += [str(entry["signature"][key]) if entry else ("none" if key == "model_family" else "0")
                   for key in compute]
        lines.append("| " + " | ".join([stage, status, rendered, *values]) + " |")
    if stages.get("propose", {}).get("facts", {}).get("outcome") == "no_feasible_method":
        lines += ["", "Finding: negative. No menu method has measured headroom of at least 1.05 on this hardware."]
    rows = [r["signature"] for r in records]
    launches = [r for r in rows if r["kind"] == "launch"]
    stage_rows = [r for r in rows if r["kind"] == "stage"]
    calls = [r for r in rows if r["kind"] == "model_call"]
    # Costs use launch records when present; tokens use model_call records when present.
    # Each falls back to stage records only when its preferred kind is absent; never mix kinds.
    costs, tokens = launches or stage_rows, calls or stage_rows
    totals = {key: sum(r[key] for r in costs) for key in ("wall_s", "gpu_s", "usd")}
    totals.update({key: sum(r[key] for r in tokens) for key in ("tokens_in", "tokens_out")})
    run_usd = stages.get("takeaways", {}).get("facts", {}).get("run_box_usd")
    if run_usd is not None:
        totals["usd"] = run_usd
    # No arbitrary strings from control state enter the operator view.
    box = box if type(box) is dict else {}
    kind = box.get("type")
    kind = kind if type(kind) is str and kind in BOX_TYPES else "unknown"
    price = box.get("price_usd_h")
    price = price if type(price) in (int, float) and math.isfinite(price) and price >= 0 else None
    lines += ["", "| box_type | price_usd_h |", "|---|---|", f"| {kind} | {price if price is not None else 'null'} |"]
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
        try:
            box = json.loads((Path(args.S_dir).parent / "control" / "box.json").read_text())
        except (OSError, ValueError):
            box = None
        page = takeaway(signatures(args.S_dir), args.raid, box)
        output = args.out if args.out is not None else Path(args.S_dir) / "OPERATOR_TAKEAWAY.md"
        output.write_text(page)
    except (OSError, ValueError):
        parser.exit(1, "invalid signatures or output unavailable\n")
