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
# SCHEMAS.md "Propose, independent votes, and the one-shot gate": optional propose facts.
PROPOSE_OPTIONAL = ("votes_reject", "votes_abstain", "outcome")
OUTCOMES = ("approved", "rejected", "conditions_unmet")
BALLOT_LABELS = {
    "approve": r"(?:votes_)?approv(?:e|es|ed|als?)",
    "reject": r"(?:votes_)?reject(?:s|ed|ions?)?",
    "abstain": r"(?:votes_)?abstain(?:s|ed)?|abstentions?",
    "null": r"(?:votes_)?nulls?(?: ballots?)?|missing",
}


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
    # SCHEMAS.md A/intake/: `anchored` is shown among the intake gate flags.
    allowed.add("anchored")
    # SCHEMAS.md propose facts: the propose row shows `outcome` and the four ballot counts.
    allowed.update(PROPOSE_OPTIONAL)
    allowed.update(OUTCOMES)
    allowed.update(("votes_null", "approve", "reject", "abstain", "approvals", "rejections",
                    "abstentions", "nulls", "votes", "ballots", "outcome"))
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


def takeaway_anchored(text):
    """Value shown for `anchored` among the intake gate flags (table column or inline)."""
    blocks, block = [], []
    for line in text.splitlines():
        if line.strip().startswith("|"):
            block.append(line)
        elif block:
            blocks.append(block)
            block = []
    if block:
        blocks.append(block)
    def cells(line):
        return [cell.strip().strip("`*") for cell in line.strip().strip("|").split("|")]
    for table in blocks:
        header = cells(table[0])
        if "anchored" not in header:
            continue
        column = header.index("anchored")
        for row in map(cells, table[1:]):
            if "intake" in row and column < len(row):
                return row[column]
    match = re.search(r"\banchored\b\W{0,4}(true|false|null)\b", text)
    return match.group(1) if match else None


def anchored_takeaway(directory, value):
    # SCHEMAS.md A/intake/: OPERATOR_TAKEAWAY.md shows `anchored` among the intake gate flags.
    directory.mkdir()
    for stage, facts in FACTS.items():
        if stage == "intake":
            facts = dict(facts, anchored=value)
        accepted(directory, stage, facts=facts)
    output = directory / "OPERATOR_TAKEAWAY.md"
    result = run("m5/operator_takeaway.py", directory, "--out", output)
    require(result.returncode == 0, "takeaway exit " + str(result.returncode))
    shown = takeaway_anchored(output.read_text())
    require(shown == json.dumps(value), "anchored shown as " + repr(shown))


def propose_rows(text):
    """Propose table rows as header->cell maps, plus every text line mentioning propose."""
    def cells(line):
        return [cell.strip().strip("`*") for cell in line.strip().strip("|").split("|")]
    mapped, block, blocks = [], [], []
    for line in text.splitlines() + [""]:
        if line.strip().startswith("|"):
            block.append(line)
        elif block:
            blocks.append(block)
            block = []
    for table in blocks:
        header = cells(table[0])
        for row in map(cells, table[1:]):
            if "propose" in row:
                mapped.append(dict(zip(header, row)))
    lines = [line for line in text.splitlines() if re.search(r"\bpropose\b", line)]
    return mapped, " ".join(lines)


def takeaway_ballots(text):
    """Ballot counts and outcome shown for propose, accepting any unambiguous format:
    a column per count, labelled counts (`reject 1`, `reject=1`, `1 reject`), or
    slash-joined labels with slash-joined counts."""
    mapped, line = propose_rows(text)
    found = {name: set() for name in BALLOT_LABELS}
    for row in mapped:
        for header, cell in row.items():
            for name, label in BALLOT_LABELS.items():
                if re.fullmatch(label, header.strip().lower()) and re.fullmatch(r"\d+", cell):
                    found[name].add(int(cell))
    lowered = line.lower()
    for name, label in BALLOT_LABELS.items():
        for match in re.finditer(r"\b(?:%s)\b[\s:=]{0,3}(\d+)\b" % label, lowered):
            found[name].add(int(match.group(1)))
        for match in re.finditer(r"\b(\d+)[\s]{0,2}(?:%s)\b" % label, lowered):
            found[name].add(int(match.group(1)))
    slashed = [(words, numbers) for words, numbers in
               re.findall(r"([a-z_]+(?:/[a-z_]+){3})\W{0,6}(\d+(?:/\d+){3})", lowered)]
    slashed += [(words, numbers) for numbers, words in
                re.findall(r"(\d+(?:/\d+){3})\W{0,6}([a-z_]+(?:/[a-z_]+){3})", lowered)]
    for words, numbers in slashed:
        for word, count in zip(words.split("/"), numbers.split("/")):
            for name, label in BALLOT_LABELS.items():
                if re.fullmatch(label, word):
                    found[name].add(int(count))
    counts = {name: (next(iter(values)) if len(values) == 1 else sorted(values) or None)
              for name, values in found.items()}
    # An outcome shown as a value, not used as a count label (`rejected 2`, `2 rejected`).
    haystack = " ".join(" ".join(row.values()) for row in mapped) + " " + line
    shown = [outcome for outcome in OUTCOMES
             if re.search(r"(?<!\d)(?<!\d )\b%s\b(?![\s:=]{0,3}\d)" % outcome, haystack)]
    return counts, shown


def ballot_takeaway(directory, approve, reject, abstain, outcome):
    # SCHEMAS.md: OPERATOR_TAKEAWAY.md shows `outcome` and the four ballot counts
    # (approve, reject, abstain, null) in the propose row.
    directory.mkdir()
    nulls = 5 - approve - reject - abstain
    for stage, facts in FACTS.items():
        if stage == "propose":
            facts = dict(facts, votes_approve=approve, vote_share=approve / 5,
                         gate_pass=outcome == "approved", votes_reject=reject,
                         votes_abstain=abstain, outcome=outcome)
        accepted(directory, stage, facts=facts)
    output = directory / "OPERATOR_TAKEAWAY.md"
    result = run("m5/operator_takeaway.py", directory, "--out", output)
    require(result.returncode == 0, "takeaway exit " + str(result.returncode))
    counts, shown = takeaway_ballots(output.read_text())
    expected = dict(approve=approve, reject=reject, abstain=abstain, null=nulls)
    require(counts == expected, "propose ballots shown as %r, expected %r" % (counts, expected))
    require(outcome in shown, "propose outcome %s not shown (found %r)" % (outcome, shown))


def main():
    failures = 0
    checks = 0
    def check(name, operation):
        nonlocal failures, checks
        checks += 1
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
        # SCHEMAS.md A/intake/: optional intake `anchored` (boolean); null on stub records.
        anchored = root / "anchored"
        for value in (True, False, None):
            check("accept intake anchored=" + repr(value),
                  lambda v=value: accepted(anchored, "intake",
                                           facts=dict(FACTS["intake"], anchored=v)))
        check("accept intake without optional anchored",
              lambda: accepted(anchored, "intake", facts=FACTS["intake"]))
        check("accept intake anchored=false with zero anchors_count",
              lambda: accepted(anchored, "intake",
                               facts=dict(FACTS["intake"], anchors_count=0, anchored=False)))
        for value in (1, 0, 1.0, "true", "false", "", [], [True], {"anchored": True},
                      math.nan, SENTINEL):
            check("reject intake anchored=" + repr(value),
                  lambda v=value: rejected(invalid, stage="intake",
                                           facts=dict(FACTS["intake"], anchored=v)))
        check("reject anchored on a non-intake stage",
              lambda: rejected(invalid, stage="reproduce",
                               facts=dict(FACTS["reproduce"], anchored=True)))
        for value in (True, False):
            check("takeaway shows intake anchored=" + repr(value),
                  lambda v=value: anchored_takeaway(root / ("takeaway-anchored-" + str(v)), v))
        # SCHEMAS.md propose facts: optional votes_reject, votes_abstain (nonnegative
        # integers) and outcome (approved, rejected, conditions_unmet or null).
        ballots = root / "ballots"
        for extra in (dict(votes_reject=1, votes_abstain=0, outcome="conditions_unmet"),
                      dict(votes_reject=0, votes_abstain=5, outcome="approved"),
                      dict(votes_reject=5, votes_abstain=0, outcome="rejected"),
                      dict(votes_reject=0, votes_abstain=0, outcome=None),
                      dict(votes_reject=None, votes_abstain=None, outcome=None),
                      dict(outcome="approved"), dict(votes_reject=2), dict(votes_abstain=3)):
            check("accept propose " + repr(extra),
                  lambda e=extra: accepted(ballots, "propose", facts=dict(FACTS["propose"], **e)))
        check("accept propose without optional ballot facts (older records)",
              lambda: accepted(ballots, "propose", facts=FACTS["propose"]))
        check("accept SKIPPED propose with null ballot facts",
              lambda: accepted(ballots, "propose", "SKIPPED",
                               facts=dict.fromkeys(list(FACTS["propose"]) + list(PROPOSE_OPTIONAL))))
        for key in ("votes_reject", "votes_abstain"):
            for value in (-1, 1.5, 2.0, True, False, "2", [2], {"n": 2}, math.nan, math.inf):
                check("reject propose %s=%r" % (key, value),
                      lambda k=key, v=value: rejected(invalid, stage="propose",
                                                      facts=dict(FACTS["propose"], **{k: v})))
        for value in ("Approved", "APPROVED", "approve", "reject", "abstain", "passed",
                      "conditions-unmet", "", SENTINEL, True, 1, [], {"outcome": "approved"}):
            check("reject propose outcome=%r" % (value,),
                  lambda v=value: rejected(invalid, stage="propose",
                                           facts=dict(FACTS["propose"], outcome=v)))
        for key, value in (("votes_reject", 1), ("votes_abstain", 1), ("outcome", "approved")):
            check("reject %s on a non-propose stage" % key,
                  lambda k=key, v=value: rejected(invalid, stage="seal",
                                                  facts=dict(FACTS["seal"], **{k: v})))
        for approve, reject, abstain, outcome in ((2, 1, 1, "conditions_unmet"),
                                                  (0, 3, 0, "rejected"),
                                                  (1, 0, 4, "approved")):
            check("takeaway propose row shows outcome %s and ballots %d/%d/%d/%d"
                  % (outcome, approve, reject, abstain, 5 - approve - reject - abstain),
                  lambda a=approve, r=reject, b=abstain, o=outcome: ballot_takeaway(
                      root / ("takeaway-ballots-" + o), a, r, b, o))
        check("reject unknown stage", lambda: rejected(
            invalid, stage=SENTINEL, facts=FACTS["intake"]))
        check("reject unknown status", lambda: rejected(
            invalid, status=SENTINEL, facts=FACTS["intake"]))
        check("reject sentinel without creating file", lambda: rejected(
            root / "absent", facts=dict(FACTS["intake"], data=SENTINEL)))
        check("20 concurrent emits", lambda: concurrent_emits(root / "concurrent"))
        check("mixed takeaway rows, totals, blockers, no sentinel",
              lambda: takeaway(root / "takeaway"))

    print("%d failures (%d checks)" % (failures, checks) if failures
          else "all checks passed (%d checks)" % checks)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
