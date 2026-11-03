"""Write an operator takeaway using only validated signatures."""
import argparse
import re
from collections import Counter
from pathlib import Path

try:
    from .signature import NAMED_RECORD_ID, signatures
except ImportError:
    from signature import NAMED_RECORD_ID, signatures


def takeaway(records):
    launches = sorted((r for r in records if r["kind"] == "launch"), key=lambda r: r["n"])
    builds = [r for r in records if r["kind"] == "envbuild"]
    endpoints = [r for r in records if r["kind"] == "record"]
    wall = sum(r["wall_s"] for r in launches)
    successful = [r for r in launches if r["status"] == "PASS" and r["depth"] == 8]
    lines = ["# Operator takeaway", "", "## Launches", "",
             "| n | type | hours | usd | exit kind | depth |", "|---|---|---|---|---|---|"]
    for r in launches:
        lines.append(f'| {r["n"]} | {r["type"]} | {r["wall_s"] / 3600:.4f} | {r["usd"]:.4f} | {r["exit_kind"]} | {r["depth"] if r["depth"] is not None else "null"} |')
    lines += ["", "## Totals", "", "| scope | box hours | USD |", "|---|---|---|"]
    for scope, group in (("Launches", launches), ("Environment builds", builds),
                         ("Combined", launches + builds)):
        lines.append(f'| {scope} | {sum(r["wall_s"] for r in group) / 3600:.4f} | '
                     f'{sum(r["usd"] for r in group):.4f} |')
    lines += ["", "Launches by exit kind:"]
    lines += [f"- {kind}: {count}" for kind, count in sorted(Counter(r["exit_kind"] for r in launches).items())]
    share = f'{successful[0]["wall_s"] / wall:.2%}' if len(successful) == 1 and wall else "unavailable"
    lines += [f"Successful end-to-end run share of wall clock: {share}.", "", "## Records", "", "Counts by status:"]
    lines += [f"- {status}: {count}" for status, count in sorted(Counter(r["status"] for r in endpoints).items())]
    lines += ["", "| run | id | run_valid | calibration_valid |", "|---|---|---|---|"]
    for r in endpoints:
        if not re.fullmatch(NAMED_RECORD_ID, r["id"]):
            continue
        flags = ["null" if r[k] is None else str(r[k]).lower() for k in ("run_valid", "calibration_valid")]
        lines.append(f'| {r["run"]} | {r["id"]} | {flags[0]} | {flags[1]} |')
    lines += ["", "Unnamed records by launch:"]
    runs = list(dict.fromkeys([r["run"] for r in launches] + [r["run"] for r in endpoints]))
    for run in runs:
        counts = Counter(r["status"] for r in endpoints
                         if r["run"] == run and not re.fullmatch(NAMED_RECORD_ID, r["id"]))
        statuses = ", ".join(f"{status}: {count}" for status, count in sorted(counts.items()))
        lines.append(f"- {run}: {statuses or 'none (0)'}.")
    blockers = sorted({b for r in records for b in r["blockers"]} - {"none"}) or ["none"]
    lines += ["", "## Blockers to reproduction", ""] + [f"- {b}" for b in blockers]
    return "\n".join(lines + ["", "This page contains no domain content and is generated mechanically.", ""])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("measure_dir")
    parser.add_argument("--out", default="OPERATOR_TAKEAWAY.md")
    args = parser.parse_args()
    try:
        page = takeaway(list(signatures(args.measure_dir)))
    except ValueError:
        parser.exit(1, "invalid signature\n")
    Path(args.out).write_text(page)
