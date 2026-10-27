#!/usr/bin/env python3
"""Black-box checks derived from m5/DESIGN.md and the public v1 schema.

Run from any directory with Python's standard library. The implementation is
executed only through its CLIs; no implementation source is imported or read.
"""

import concurrent.futures
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from measure.signature import FIELDS, validate  # noqa: E402


SENTINEL = "PRIVATE_SENTINEL_7c9e24"
COMMON = dict(tokens_known=True, gpu_busy_known=True)
FACTS = {
    "intake": dict(found=True, anchors_count=2, data="available",
                   licence="permitted", stock_environment=True, size="small"),
    "reproduce": dict(anchors_passed=2, anchors_total=2, stock_verified=True,
                      tuned_control_valid=True),
    "profile": dict(profile_complete=True, timed_fraction=0.95, gpu_telemetry=True),
    "seal": dict(seal_present=True, seal_verified=True, prediction_count=3),
    "propose": dict(method="batching", expected_speedup=1.5, votes_approve=4,
                    votes_total=5, vote_share=0.8, gate_pass=True),
    "implement": dict(patch_applies=True, tests_pass=True, blind_tests=True,
                      launch_review_pass=True),
    "evaluate": dict(validity_pass=True, equivalence_pass=True,
                     performance_pass=True, equal_cost=True,
                     speedup_published=1.5, speedup_tuned=1.2, cost_ratio=0.8,
                     prediction_ratio=1.0, curve_points=3),
    "takeaways": dict(operator_written=True, research_written=True,
                      teardown_confirmed=True),
}
FACTS = {stage: dict(facts, **COMMON) for stage, facts in FACTS.items()}
OMITTED = object()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def run(script, *args):
    return subprocess.run([sys.executable, str(ROOT / script), *map(str, args)],
                          cwd=ROOT, capture_output=True, text=True, timeout=30)


def emit(directory, stage="intake", status="PASS", facts=OMITTED, v1=OMITTED):
    args = ["emit", "--dir", directory, "--stage", stage, "--status", status]
    if facts is not OMITTED:
        args += ["--facts", json.dumps(facts)]
    if v1 is not OMITTED:
        args += ["--v1", json.dumps(v1)]
    return run("m5/signatures.py", *args)


def snapshot(directory):
    path = directory / "signatures.jsonl"
    return path.read_bytes() if path.exists() else None


def records(directory):
    raw = snapshot(directory)
    require(raw is not None and raw.endswith(b"\n"), "missing JSONL or final newline")
    def reject_constant(value):
        raise AssertionError("non-finite JSON constant: " + value)
    return [json.loads(line, parse_constant=reject_constant)
            for line in raw.splitlines()]


def envelope(record, stage, status, facts):
    require(set(record) == {"schema_version", "signature", "facts"},
            "envelope keys differ")
    require(type(record["schema_version"]) is int and record["schema_version"] == 2,
            "schema version differs")
    signature = record["signature"]
    require(not validate(signature), "invalid v1: " + repr(validate(signature)))
    require(signature["stage"] == stage, "stage differs")
    require(signature["status"] == status, "status differs")
    require(record["facts"] == facts, "facts differ")
    for key, value in facts.items():
        require(type(record["facts"][key]) is type(value), "fact type differs: " + key)


def accepted(directory, stage, status="PASS", facts=OMITTED, v1=OMITTED):
    before = snapshot(directory) or b""
    result = emit(directory, stage, status, facts, v1)
    require(result.returncode == 0, "emit exit " + str(result.returncode))
    after = snapshot(directory)
    require(after is not None and after.startswith(before), "previous records changed")
    require(len(after[len(before):].splitlines()) == 1, "emit did not append one line")
    expected = ({key: None for key in FACTS[stage]} if facts is OMITTED else facts)
    record = records(directory)[-1]
    envelope(record, stage, status, expected)
    return record


def rejected(directory, **kwargs):
    before = snapshot(directory)
    result = emit(directory, **kwargs)
    require(snapshot(directory) == before, "rejected input changed signatures.jsonl")
    require(SENTINEL.encode() not in (snapshot(directory) or b""), "sentinel written")
    require(result.returncode == 1, "expected exit 1, got " + str(result.returncode))


def concurrent_emits(directory):
    barrier = threading.Barrier(20)
    def worker(index):
        facts = dict(FACTS["intake"], anchors_count=index)
        barrier.wait(timeout=30)
        return emit(directory, facts=facts)
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(worker, range(20)))
    require(all(result.returncode == 0 for result in results), "concurrent emit failed")
    rows = records(directory)
    require(len(rows) == 20, "concurrent records lost or duplicated")
    require(sorted(row["facts"]["anchors_count"] for row in rows) == list(range(20)),
            "concurrent payloads lost or duplicated")
    for row in rows:
        envelope(row, "intake", "PASS",
                 dict(FACTS["intake"], anchors_count=row["facts"]["anchors_count"]))


def takeaway(directory):
    directory.mkdir()
    # Use the public emitter's fixed IDs instead of guessing their spelling.
    rows = []
    for index, (stage, facts) in enumerate(FACTS.items()):
        status = ("PASS", "FAIL", "SKIPPED")[index % 3]
        v1 = dict(exit_code=4 if status == "FAIL" else 0,
                  exit_kind="anchor" if status == "FAIL" else "ok",
                  error_class="anchor" if status == "FAIL" else "none",
                  wall_s=11, gpu_s=7, usd=3, tokens_in=13, tokens_out=17,
                  blockers=["data_unavailable"] if status == "FAIL" else ["none"])
        rows.append(accepted(directory, stage, status,
                             OMITTED if status == "SKIPPED" else facts, v1))
    source = directory / "signatures.jsonl"
    before = source.read_bytes()
    # A recursive scanner would leak these unrelated operator-directory inputs.
    (directory / "private.json").write_text(json.dumps({"note": SENTINEL}))
    (directory / "private.md").write_text(SENTINEL)
    output = directory / "OPERATOR_TAKEAWAY.md"
    result = run("m5/operator_takeaway.py", directory, "--out", output)
    require(result.returncode == 0, "takeaway exit " + str(result.returncode))
    require(output.is_file(), "takeaway missing")
    text = output.read_text()
    require(SENTINEL not in text, "takeaway leaked unrelated content")
    require(source.read_bytes() == before, "takeaway mutated signatures")
    table = [[cell.strip().strip("`*") for cell in line.strip().strip("|").split("|")]
             for line in text.splitlines() if "|" in line]
    allowed = {"true", "false", "null", "none", "unknown", "-", "—", "n/a"}
    allowed.update(FIELDS)
    for spec in FIELDS.values():
        allowed.update(spec.get("enum", []))
        allowed.update(spec.get("items", {}).get("enum", []))
    for row in rows:
        allowed.update(row["facts"])
        allowed.update(str(value) for value in row["signature"].values()
                       if isinstance(value, str))
        allowed.update(str(value) for value in row["facts"].values()
                       if isinstance(value, str))
    for stage in FACTS:
        matches = [cells for cells in table if stage in cells]
        require(len(matches) == 1, "expected one table row for " + stage)
        expected_status = next(row["signature"]["status"] for row in rows
                               if row["signature"]["stage"] == stage)
        require(expected_status in matches[0], "stage status missing: " + stage)
        for cell in matches[0]:
            for token in re.findall(r"[A-Za-z_][A-Za-z_0-9.-]*", cell):
                require(token in allowed or token.lower() in allowed,
                        "unexpected text in stage row: " + token)
    def check_totals(report, expected, case):
        require(re.search(r"total", report, re.I), "totals missing: " + case)
        totals_table = [
            [cell.strip().strip("`*") for cell in line.strip().strip("|").split("|")]
            for line in report.splitlines() if "|" in line]
        totals_header = ["wall_s", "gpu_s", "usd", "tokens_in", "tokens_out"]
        require(totals_header in totals_table, "totals columns missing: " + case)
        total_index = totals_table.index(totals_header)
        require(total_index + 2 < len(totals_table), "totals values missing: " + case)
        require([float(cell) for cell in totals_table[total_index + 2]] == expected,
                "incorrect totals: " + case)

    check_totals(text, [88, 56, 24, 104, 136], "stage records only")
    signature = dict(rows[0]["signature"], kind="launch", id="launch-0")
    require(not validate(signature), "invalid launch fixture")
    with source.open("a") as stream:
        stream.write(json.dumps(dict(rows[0], signature=signature)) + "\n")
    totals_before = source.read_bytes()
    result = run("m5/operator_takeaway.py", directory, "--out", output)
    require(result.returncode != 0, "takeaway accepted launch record")
    require(source.read_bytes() == totals_before, "takeaway mutated signatures")
    require(re.search(r"blocker", text, re.I), "blockers missing")
    require("data_unavailable" in text, "failure blocker missing")


def main():
    failures = 0
    def check(name, operation):
        nonlocal failures
        try:
            operation()
        except Exception as error:
            failures += 1
            print("FAIL " + name + ": " + str(error), flush=True)
        else:
            print("ok " + name, flush=True)

    with tempfile.TemporaryDirectory(prefix="m5-signatures-test-") as temporary:
        root = Path(temporary)
        valid = root / "valid"
        for stage, facts in FACTS.items():
            check("valid emit " + stage,
                  lambda s=stage, f=facts: accepted(valid, s, facts=f))
            check("SKIPPED null facts " + stage,
                  lambda s=stage: accepted(valid, s, "SKIPPED"))
            check("explicit null facts " + stage,
                  lambda s=stage, f=facts: accepted(valid, s,
                                                  facts=dict.fromkeys(f)))

        # Seed rejection files independently; byte-for-byte preservation is checked.
        invalid = root / "invalid"
        invalid.mkdir()
        (invalid / "signatures.jsonl").write_bytes(b'{"existing":true}\n')
        for stage, facts in FACTS.items():
            for key, value in facts.items():
                missing = dict(facts)
                del missing[key]
                check("reject missing " + stage + "." + key,
                      lambda s=stage, f=missing: rejected(invalid, stage=s, facts=f))
                wrong = "free text" if not isinstance(value, str) else 17
                check("reject wrong type " + stage + "." + key,
                      lambda s=stage, f=dict(facts, **{key: wrong}):
                      rejected(invalid, stage=s, facts=f))
                if type(value) is int:
                    for bad in (-1, 1.5, True):
                        check("reject count " + stage + "." + key + "=" + repr(bad),
                              lambda s=stage, f=dict(facts, **{key: bad}):
                              rejected(invalid, stage=s, facts=f))
                if type(value) in (int, float):
                    for bad in (math.nan, math.inf, -math.inf):
                        check("reject nonfinite " + stage + "." + key + "=" + str(bad),
                              lambda s=stage, f=dict(facts, **{key: bad}):
                              rejected(invalid, stage=s, facts=f))
                if type(value) is float:
                    check("reject boolean ratio " + stage + "." + key,
                          lambda s=stage, f=dict(facts, **{key: True}):
                          rejected(invalid, stage=s, facts=f))
                if type(value) is bool:
                    check("reject integer flag " + stage + "." + key,
                          lambda s=stage, f=dict(facts, **{key: 1}):
                          rejected(invalid, stage=s, facts=f))
                if isinstance(value, str):
                    check("reject enum sentinel " + stage + "." + key,
                          lambda s=stage, f=dict(facts, **{key: SENTINEL}):
                          rejected(invalid, stage=s, facts=f))
            check("reject unknown fact " + stage,
                  lambda s=stage, f=dict(facts, private_note=SENTINEL):
                  rejected(invalid, stage=s, facts=f))
            check("reject omitted PASS facts " + stage,
                  lambda s=stage: rejected(invalid, stage=s))

        for value in ([], "free text", 1, None):
            check("reject facts object " + repr(value),
                  lambda v=value: rejected(invalid, facts=v))
        for key in ("id", "run", "stage", "type", "error_class", "model_family",
                    "status", "blockers", "private_note"):
            value = [SENTINEL] if key == "blockers" else SENTINEL
            check("reject v1 sentinel " + key,
                  lambda k=key, v=value: rejected(invalid, facts=FACTS["intake"],
                                                 v1={k: v}))
        for key, value in (("usd", math.inf), ("wall_s", math.nan),
                           ("tokens_in", True), ("run_valid", "true")):
            check("reject malformed v1 " + key,
                  lambda k=key, v=value: rejected(invalid, facts=FACTS["intake"],
                                                 v1={k: v}))
        # SCHEMAS.md profile facts: optional `headroom`, a finite positive ratio or null.
        headroom = root / "headroom"
        for value in (2.2, 3, 1, None):
            check("accept profile headroom=" + repr(value),
                  lambda v=value: accepted(headroom, "profile",
                                           facts=dict(FACTS["profile"], headroom=v)))
        check("accept profile without optional headroom",
              lambda: accepted(headroom, "profile", facts=FACTS["profile"]))
        for value in (math.nan, math.inf, -math.inf, True, "2.2", [2.2], {"factor": 2.2}):
            check("reject profile headroom=" + repr(value),
                  lambda v=value: rejected(invalid, stage="profile",
                                           facts=dict(FACTS["profile"], headroom=v)))
        check("reject headroom on a non-profile stage",
              lambda: rejected(invalid, stage="reproduce",
                               facts=dict(FACTS["reproduce"], headroom=2.2)))
        check("reject unknown stage", lambda: rejected(
            invalid, stage=SENTINEL, facts=FACTS["intake"]))
        check("reject unknown status", lambda: rejected(
            invalid, status=SENTINEL, facts=FACTS["intake"]))
        check("reject sentinel without creating file", lambda: rejected(
            root / "absent", facts=dict(FACTS["intake"], data=SENTINEL)))
        check("20 concurrent emits", lambda: concurrent_emits(root / "concurrent"))
        check("mixed takeaway rows, totals, blockers, no sentinel",
              lambda: takeaway(root / "takeaway"))

    print(str(failures) + " failures" if failures else "all checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
