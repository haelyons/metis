#!/usr/bin/env python3
"""Black-box, stdlib-only CLI contract tests; never import the tested tools."""

import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
KINDS = {"launch", "envbuild", "stage", "record", "model_call"}
STATUSES = {"PASS", "FAIL", "VOID", "ERROR", "RUNNING", "SKIPPED"}
EXITS = {"ok", "infra", "guard", "anchor", "later_stage", "unknown"}
SAFE_ID = re.compile(r"[a-z0-9_.-]{1,64}\Z")
CLEAR_ID = re.compile(
    r"(?:endpoint-(?:C[0-9]+|anchor)(?:_tag-[a-z0-9]+)?|RUN_VALID|[a-z0-9]+_summary)\Z"
)
HASH_ID = re.compile(r"rec-[0-9a-f]{8}\Z")
FORBIDDEN = ("SENTINEL_TEXT_42", "secretword", "recordinternaltext42")


class Checks:
    def __init__(self):
        self.failures = 0

    def check(self, name, condition, detail=""):
        if condition:
            print("ok:", name)
        else:
            self.failures += 1
            print("FAIL:", name, ("-- " + detail) if detail else "")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def invoke(tool, directory, *arguments):
    return subprocess.run(
        ["python3", str(ROOT / "measure" / tool), str(directory), *arguments],
        capture_output=True, text=True, timeout=30, cwd=ROOT,
    )


def signatures(checks, result, label):
    rows = []
    lines = result.stdout.splitlines()
    invalid_lines = []
    for number, line in enumerate(lines, 1):
        try:
            row = json.loads(line, parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError("non-finite JSON number: " + value)
            ))
            valid = isinstance(row, dict)
        except ValueError:
            row, valid = None, False
        if not valid:
            invalid_lines.append(number)
        if valid:
            rows.append(row)
    checks.check(label + " emits one JSON object per line", bool(lines) and not invalid_lines,
                 f"invalid lines: {invalid_lines}" if invalid_lines else "")
    valid_output = bool(lines) and not invalid_lines and all(
        safe_values(row) and row.get("kind") in KINDS and row.get("status") in STATUSES
        and row.get("exit_kind") in EXITS
        and all(row.get(key) is None or type(row[key]) is bool
                for key in ("run_valid", "calibration_valid"))
        and (row.get("kind") != "record" or
             bool(CLEAR_ID.fullmatch(str(row.get("id"))) or HASH_ID.fullmatch(str(row.get("id")))))
        for row in rows
    )
    # The contract concerns validation of emitted signatures. It does not specify
    # behavior for malformed input JSON, so do not invent an input-error policy.
    checks.check(label + " exit code agrees with signature validation",
                 result.returncode == (0 if valid_output else 1), f"exit {result.returncode}")
    return rows


def safe_values(value):
    if value is None or isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return isinstance(value, int) or math.isfinite(value)
    if isinstance(value, str):
        return bool(value in STATUSES or SAFE_ID.fullmatch(value) or CLEAR_ID.fullmatch(value))
    if isinstance(value, list):
        return all(safe_values(item) for item in value)
    if isinstance(value, dict):
        return all(safe_values(item) for item in value.values())
    return False


def table_rows(markdown, heading):
    """Read a generated Markdown table without requiring exact whitespace."""
    section = markdown.split(heading, 1)
    if len(section) != 2:
        return []
    section = section[1].split("\n## ", 1)[0]
    return [
        [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        for line in section.splitlines() if line.strip().startswith("|")
    ]


def number_equal(text, expected):
    try:
        return math.isclose(float(text.replace("$", "").replace(",", "")), expected,
                            rel_tol=1e-6, abs_tol=1e-6)
    except ValueError:
        return False


def main():
    checks = Checks()
    with tempfile.TemporaryDirectory(prefix="signature-contract-") as temporary:
        directory = Path(temporary)
        # Deliberately create these out of numeric order. Costs use wall_s / 3600.
        launches = [(10, "0", 10800, 7.25), (2, 4, 7200, 3.5), (1, "2", 3600, 1.25)]
        for number, rc, wall_s, usd in launches:
            write_json(directory / f"out/launch{number}.json",
                       {"rc": rc, "wall_s": wall_s, "usd": usd})
        write_json(directory / "out/envbuild3.json",
                   {"rc": 0, "wall_s": 1800, "usd": 2.75})

        # Unique measured/card pairs identify records without assuming a hash algorithm.
        cases = [
            ("out/launch1/results_a/out", "endpoint-C1", "PASS", 6, 3, True, True),
            ("out/launch2/results_b/out", "endpoint-anchor_tag-abc", "FAIL", 9, 3, False, False),
            ("out/launch10/results_c/out", "RUN_VALID", "VOID", 12, 3, None, None),
            ("results_root/out", "abc_summary", "PASS", 15, 3, True, None),
            ("results_root/out", "secretword_parse_log", "FAIL", 18, 3, False, True),
            ("results_other/out", "ordinaryrecord", "VOID", 21, 3, None, False),
            ("results_other/out", "endpoint-C2_tag-x1", "PASS", "42", 3, True, True),
            ("out/launch2/results_b/out", "endpoint-C3", "FAIL", 24, "3", False, None),
            ("results_other/out", "endpoint-C4", "VOID", None, 3, None, None),
            ("results_other/out/nested", "endpoint-C5", "PASS", 30, 3, True, False),
            ("results_other/out", "endpoint-C1_tag-UPPER", "VOID", 33, 3, False, None),
        ]
        for folder, name, decision, measured, card, run_valid, calibration_valid in cases:
            record = {
                "decision": decision,
                "values": {"measured": measured, "card_value": card},
                "note": "SENTINEL_TEXT_42",
                "description": "recordinternaltext42",
                "nested": {"note": "SENTINEL_TEXT_42", "items": ["SENTINEL_TEXT_42"]},
            }
            if measured is None:
                record.pop("values")
            if run_valid is not None:
                record["run_valid"] = run_valid
            if calibration_valid is not None:
                record["calibration_valid"] = calibration_valid
            write_json(directory / folder / (name + ".json"), record)

        result = invoke("signature.py", directory)
        checks.check("signature exits 0 for valid input", result.returncode == 0,
                     f"exit {result.returncode}")
        rows = signatures(checks, result, "signature")
        checks.check("all output values satisfy the restricted vocabulary", all(map(safe_values, rows)))
        checks.check("kind always uses its enum", all(row.get("kind") in KINDS for row in rows))
        checks.check("status always uses its enum", all(row.get("status") in STATUSES for row in rows))
        checks.check("exit_kind always uses its enum", all(row.get("exit_kind") in EXITS for row in rows))
        launch_rows = [row for row in rows if row.get("kind") == "launch"]
        builds = [row for row in rows if row.get("kind") == "envbuild"]
        records = [row for row in rows if row.get("kind") == "record"]
        checks.check("every launch is covered once", sorted(row.get("n", -1) for row in launch_rows) == [1, 2, 10])
        checks.check("environment build is covered once", len(builds) == 1 and builds[0].get("id") == "envbuild3")
        checks.check("every nested and root result record is covered once", len(records) == len(cases),
                     f"expected {len(cases)}, got {len(records)}")
        for number, expected in [(1, "infra"), (2, "anchor"), (10, "ok")]:
            matches = [row for row in launch_rows if row.get("n") == number]
            checks.check(f"launch{number} rc maps to {expected}",
                         len(matches) == 1 and matches[0].get("exit_kind") == expected)

        for folder, name, decision, measured, card, run_valid, calibration_valid in cases:
            numeric = isinstance(measured, (int, float)) and isinstance(card, (int, float))
            expected_ratio = measured / card if numeric else None
            if CLEAR_ID.fullmatch(name):
                matches = [row for row in records if row.get("id") == name]
            else:
                matches = [row for row in records if row.get("ratio_to_card") == expected_ratio]
            checks.check(f"record {name} is identifiable exactly once", len(matches) == 1)
            if len(matches) != 1:
                continue
            row = matches[0]
            checks.check(f"record {name} id follows disclosure rule",
                         row.get("id") == name if CLEAR_ID.fullmatch(name)
                         else bool(HASH_ID.fullmatch(str(row.get("id")))))
            checks.check(f"record {name} preserves decision", row.get("status") == decision)
            checks.check(f"record {name} ratio_to_card", "ratio_to_card" in row and
                         row["ratio_to_card"] == expected_ratio)
            for key, expected in [("run_valid", run_valid), ("calibration_valid", calibration_valid)]:
                checks.check(f"record {name} {key}", key in row and row[key] is expected)

        output = directory / "takeaway.md"
        takeaway = invoke("operator_takeaway.py", directory, "--out", str(output))
        checks.check("takeaway exits 0", takeaway.returncode == 0, f"exit {takeaway.returncode}")
        checks.check("--out writes Markdown", output.is_file())
        markdown = output.read_text(encoding="utf-8") if output.is_file() else ""
        checks.check("takeaway has a Markdown heading", bool(re.search(r"(?m)^# .+", markdown)))
        launch_table = table_rows(markdown, "## Launches")
        order = [int(row[0]) for row in launch_table if row and row[0].isdigit()]
        checks.check("takeaway launches sorted numerically", order == [1, 2, 10], str(order))
        totals = {row[0].lower(): row[1:] for row in table_rows(markdown, "## Totals") if row}
        for scope, hours, usd in [("launches", 6, 12), ("environment builds", .5, 2.75), ("combined", 6.5, 14.75)]:
            values = totals.get(scope, [])
            checks.check(f"takeaway {scope} box hours and USD", len(values) >= 2 and
                         number_equal(values[0], hours) and number_equal(values[1], usd), str(values))
        counts_section = markdown.split("Counts by status:", 1)
        counts = dict(re.findall(r"(?m)^\s*[-*]\s+(PASS|FAIL|VOID|ERROR|RUNNING|SKIPPED):\s*(\d+)\s*$",
                                 counts_section[1] if len(counts_section) == 2 else ""))
        for status in ("PASS", "FAIL", "VOID"):
            expected = sum(case[2] == status for case in cases)
            checks.check(f"takeaway counts {status}", counts.get(status) == str(expected),
                         f"expected {expected}, got {counts.get(status)}")
        record_table = table_rows(markdown, "## Records")
        displayed_ids = [row[1] for row in record_table if len(row) >= 2 and
                         row[0] not in {"run", "---"} and not set(row[0]) <= {"-", ":"}]
        checks.check("takeaway only displays allowed clear or hashed record ids",
                     bool(displayed_ids) and all(CLEAR_ID.fullmatch(value) or HASH_ID.fullmatch(value)
                                                 for value in displayed_ids))
        for name in (case[1] for case in cases if not CLEAR_ID.fullmatch(case[1])):
            checks.check(f"unsafe id {name} never appears in either output",
                         name not in result.stdout + result.stderr + markdown + takeaway.stdout + takeaway.stderr)
        for label, text in [("signature", result.stdout + result.stderr),
                            ("takeaway", markdown + takeaway.stdout + takeaway.stderr)]:
            for forbidden in FORBIDDEN:
                checks.check(f"{label} never discloses {forbidden}", forbidden not in text)

        # Probe the remaining rc branches through the CLI, retaining three launches.
        for rc, expected in [(2, "infra"), ("3", "guard"), (5, "later_stage"),
                             ("4", "anchor"), (0, "ok"), ("7", "unknown"), (-1, "unknown")]:
            write_json(directory / "out/launch1.json", {"rc": rc})
            probe = invoke("signature.py", directory)
            probe_rows = signatures(checks, probe, f"rc {rc!r}")
            matches = [row for row in probe_rows if row.get("kind") == "launch" and row.get("n") == 1]
            checks.check(f"rc {rc!r} maps to {expected}", probe.returncode == 0 and len(matches) == 1
                         and matches[0].get("exit_kind") == expected)

    print(f"{checks.failures} failures" if checks.failures else "all checks passed")
    return int(bool(checks.failures))


if __name__ == "__main__":
    sys.exit(main())
