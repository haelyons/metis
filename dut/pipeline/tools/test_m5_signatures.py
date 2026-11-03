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
MISSING = "<not shown>"
# SCHEMAS.md "Propose, independent votes, and the one-shot gate": optional propose facts.
PROPOSE_OPTIONAL = ("votes_reject", "votes_abstain", "outcome")
OUTCOMES = ("approved", "rejected", "conditions_unmet", "no_feasible_method")
# Outcomes for which ballots were counted; otherwise the null-ballot count shows null.
COUNTED = ("approved", "rejected", "conditions_unmet")
FINDING = ("Finding: negative. No menu method has measured headroom of at least 1.05 "
           "on this hardware.")
# SCHEMAS.md A/intake/ (U40): optional intake enum fact `licence_basis`, null when omitted.
LICENCE_BASES = ("unreachable", "none", "owner", "distribution", "explicit")
# SCHEMAS.md Concurrency probe, unit mode: the six `outcome` values (U52 `units_outcome`).
UNITS_OUTCOMES = ("invalid_units", "failed", "baseline_mismatch", "outputs_mismatch", "skipped",
                  "measured")
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
    # SCHEMAS.md A/intake/: `anchored` and `licence_basis` are shown among the intake gate flags.
    allowed.add("anchored")
    allowed.add("licence_basis")
    allowed.update(LICENCE_BASES)
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


def takeaway_licence_basis(text):
    """Value shown for `licence_basis` among the intake gate flags (table column or inline)."""
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
        return [cell.strip().strip("`*\"") for cell in line.strip().strip("|").split("|")]
    for table in blocks:
        header = cells(table[0])
        if "licence_basis" not in header:
            continue
        column = header.index("licence_basis")
        for row in map(cells, table[1:]):
            if "intake" in row and column < len(row):
                return row[column]
    match = re.search(r"\blicence_basis\b\W{0,4}(%s|null)\b" % "|".join(LICENCE_BASES), text)
    return match.group(1) if match else None


def licence_basis_takeaway(directory, value):
    # SCHEMAS.md A/intake/: OPERATOR_TAKEAWAY.md shows `licence_basis` among the intake gate flags.
    directory.mkdir()
    for stage, facts in FACTS.items():
        if stage == "intake":
            facts = dict(facts, anchored=True, licence_basis=value)
        accepted(directory, stage, facts=facts)
    output = directory / "OPERATOR_TAKEAWAY.md"
    result = run("m5/operator_takeaway.py", directory, "--out", output)
    require(result.returncode == 0, "takeaway exit " + str(result.returncode))
    text = output.read_text()
    shown = takeaway_licence_basis(text)
    expected = "null" if value is None else value
    require(shown == expected, "licence_basis shown as " + repr(shown))
    # Shown alongside the other intake gate flag.
    require(takeaway_anchored(text) == "true", "anchored no longer shown as true")


AUTHORITY_LINE = ("Execution authority: owner's standing instruction (2026-10-30), "
                  "not licence evidence.")
LICENCES = ("permitted", "unknown", "restricted")


def takeaway_licence(text):
    """Value shown for `licence` among the intake gate flags, and whether it sits next to
    `licence_basis` (adjacent table columns, or the same line)."""
    def cells(line):
        return [cell.strip().strip("`*\"") for cell in line.strip().strip("|").split("|")]
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        header = cells(line)
        if "licence" not in header:
            continue
        column = header.index("licence")
        adjacent = "licence_basis" in header and abs(header.index("licence_basis") - column) == 1
        for following in lines[index + 1:]:
            if not following.strip().startswith("|"):
                break
            row = cells(following)
            if "intake" in row and column < len(row):
                return row[column], adjacent
    for line in lines:
        match = re.search(r"\blicence\b(?!_)\W{0,4}(%s|null)\b" % "|".join(LICENCES), line)
        if match:
            return match.group(1), bool(re.search(r"\blicence_basis\b", line))
    return None, False


def licence_takeaway(directory, status, licence, extra, blockers, line):
    directory.mkdir()
    intake = dict(FACTS["intake"], anchored=True, licence=licence,
                  licence_basis="distribution", **extra)
    if status == "PASS":
        accepted(directory, "intake", facts=intake)
        for stage, facts in FACTS.items():
            if stage != "intake":
                accepted(directory, stage, facts=facts)
    else:
        accepted(directory, "intake", "FAIL", facts=intake,
                 v1=dict(exit_code=2, exit_kind="guard", error_class="numeric",
                         blockers=blockers))
        for stage in FACTS:
            if stage != "intake":
                accepted(directory, stage, "SKIPPED")
    source = directory / "signatures.jsonl"
    before = source.read_bytes()
    output = directory / "OPERATOR_TAKEAWAY.md"
    result = run("m5/operator_takeaway.py", directory, "--out", output)
    require(result.returncode == 0, "takeaway exit " + str(result.returncode))
    require(source.read_bytes() == before, "takeaway mutated signatures")
    require(b"standing instruction" not in before, "authorization carried by a signature record")
    text = output.read_text()
    shown, adjacent = takeaway_licence(text)
    require(shown == licence, "licence shown as " + repr(shown))
    require(adjacent, "licence not shown next to licence_basis")
    require(takeaway_licence_basis(text) == "distribution", "licence_basis no longer shown")
    count = sum(AUTHORITY_LINE in row for row in text.splitlines())
    if line:
        require(count == 1 and text.count(AUTHORITY_LINE) == 1,
                "expected exactly one authority line, found " + str(text.count(AUTHORITY_LINE)))
        require(len(re.findall(r"execution authority", text, re.I)) == 1,
                "more than one execution authority statement")
    else:
        require(not re.search(r"execution authority|standing instruction", text, re.I),
                "unexpected authority line")


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
    slash-joined labels with slash-joined counts. A count shown as `null` is None;
    a count not shown at all is MISSING."""
    mapped, line = propose_rows(text)
    found = {name: set() for name in BALLOT_LABELS}
    def parse(cell):
        return int(cell) if cell.isdigit() else None
    for row in mapped:
        for header, cell in row.items():
            for name, label in BALLOT_LABELS.items():
                if (re.fullmatch(label, header.strip().lower())
                        and re.fullmatch(r"\d+|null", cell.strip().lower())):
                    found[name].add(parse(cell.strip()))
    lowered = line.lower()
    for name, label in BALLOT_LABELS.items():
        for match in re.finditer(r"\b(?:%s)\b[\s:=]{0,3}(\d+|null)\b" % label, lowered):
            found[name].add(parse(match.group(1)))
        for match in re.finditer(r"\b(\d+)[\s]{0,2}(?:%s)\b" % label, lowered):
            found[name].add(int(match.group(1)))
    count = r"(?:\d+|null)"
    slashed = [(words, numbers) for words, numbers in
               re.findall(r"([a-z_]+(?:/[a-z_]+){3})\W{0,6}(%s(?:/%s){3})" % (count, count),
                          lowered)]
    slashed += [(words, numbers) for numbers, words in
                re.findall(r"(%s(?:/%s){3})\W{0,6}([a-z_]+(?:/[a-z_]+){3})" % (count, count),
                           lowered)]
    for words, numbers in slashed:
        for word, value in zip(words.split("/"), numbers.split("/")):
            for name, label in BALLOT_LABELS.items():
                if re.fullmatch(label, word):
                    found[name].add(parse(value))
    counts = {name: (next(iter(values)) if len(values) == 1
                     else sorted(values, key=repr) if values else MISSING)
              for name, values in found.items()}
    # An outcome shown as a value, not used as a count label (`rejected 2`, `2 rejected`).
    haystack = " ".join(" ".join(row.values()) for row in mapped) + " " + line
    shown = [outcome for outcome in OUTCOMES
             if re.search(r"(?<!\d)(?<!\d )\b%s\b(?![\s:=]{0,3}\d)" % outcome, haystack)]
    return counts, shown


def finding_lines(text):
    return [line for line in text.splitlines() if line.strip() == FINDING]


def anchored_text(directory):
    """Takeaway text for records without the optional propose facts."""
    directory.mkdir()
    for stage, facts in FACTS.items():
        accepted(directory, stage, facts=facts)
    output = directory / "OPERATOR_TAKEAWAY.md"
    result = run("m5/operator_takeaway.py", directory, "--out", output)
    require(result.returncode == 0, "takeaway exit " + str(result.returncode))
    return output.read_text()


def ballot_takeaway(directory, approve, reject, abstain, outcome):
    # SCHEMAS.md: OPERATOR_TAKEAWAY.md shows `outcome` and the four ballot counts
    # (approve, reject, abstain, null) in the propose row. "Its null-ballot count is
    # `5 - votes_approve - votes_reject - votes_abstain` only when ballots were counted
    # (outcome `approved`, `rejected` or `conditions_unmet`); otherwise it shows null,
    # because no ballot was requested." The fixed Finding line appears exactly when
    # outcome is no_feasible_method.
    directory.mkdir()
    counted = outcome in COUNTED
    nulls = 5 - approve - reject - abstain if counted else None
    for stage, facts in FACTS.items():
        status, v1 = "PASS", OMITTED
        if stage == "propose":
            facts = dict(facts, votes_approve=approve, vote_share=approve / 5,
                         gate_pass=outcome == "approved", votes_reject=reject,
                         votes_abstain=abstain, outcome=outcome)
            if not counted:
                facts.update(method="none", expected_speedup=None)
            if outcome in ("rejected", "conditions_unmet", None):
                status = "FAIL"
                v1 = dict(exit_code=2, exit_kind="guard", error_class="numeric")
        if outcome == "no_feasible_method" and stage in ("implement", "evaluate"):
            accepted(directory, stage, "SKIPPED")
            continue
        accepted(directory, stage, status, facts=facts, v1=v1)
    output = directory / "OPERATOR_TAKEAWAY.md"
    result = run("m5/operator_takeaway.py", directory, "--out", output)
    require(result.returncode == 0, "takeaway exit " + str(result.returncode))
    text = output.read_text()
    counts, shown = takeaway_ballots(text)
    expected = dict(approve=approve, reject=reject, abstain=abstain, null=nulls)
    require(counts == expected, "propose ballots shown as %r, expected %r; propose text: %r"
            % (counts, expected, propose_rows(text)))
    if outcome is not None:
        require(outcome in shown, "propose outcome %s not shown (found %r)" % (outcome, shown))
    else:
        require(not shown, "outcome null shown as %r" % (shown,))
    lines = finding_lines(text)
    require(len(lines) == (1 if outcome == "no_feasible_method" else 0),
            "Finding line shown %d times for outcome %r" % (len(lines), outcome))


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
        # SCHEMAS.md profile facts (U49): optional `host_only`, the packet's boolean or null
        # when no packet was written; optional so older records stay valid; null on SKIPPED/stub.
        host_only = root / "host-only"
        for value in (True, False, None):
            check("accept profile host_only=" + repr(value),
                  lambda v=value: accepted(host_only, "profile",
                                           facts=dict(FACTS["profile"], host_only=v)))
            check("accept profile host_only=%r with headroom" % (value,),
                  lambda v=value: accepted(host_only, "profile",
                                           facts=dict(FACTS["profile"], headroom=2.2, host_only=v)))
        check("accept profile without optional host_only",
              lambda: accepted(host_only, "profile", facts=FACTS["profile"]))
        check("accept FAIL profile with null host_only (parse, no packet)",
              lambda: accepted(host_only, "profile", "FAIL",
                               facts=dict(FACTS["profile"], profile_complete=False,
                                          headroom=None, host_only=None),
                               v1=dict(exit_code=2, exit_kind="guard", error_class="parse")))
        check("accept SKIPPED profile with null headroom and host_only",
              lambda: accepted(host_only, "profile", "SKIPPED",
                               facts=dict.fromkeys(list(FACTS["profile"]) + ["headroom", "host_only"])))
        for value in ("true", "false", "True", "", "null", SENTINEL, 1, 0, 1.0, 0.0,
                      math.nan, [], [True], {"host_only": True}):
            check("reject profile host_only=" + repr(value),
                  lambda v=value: rejected(invalid, stage="profile",
                                           facts=dict(FACTS["profile"], host_only=v)))
        check("reject host_only on a non-profile stage",
              lambda: rejected(invalid, stage="reproduce",
                               facts=dict(FACTS["reproduce"], host_only=True)))
        # SCHEMAS.md "Unit equivalence check (U51)": reproduce facts add optional `units_match`
        # and `units_full_match`, each a boolean or null; null outside units-check mode and on
        # SKIPPED/stub records; records without them stay valid.
        units = root / "units"
        for match in (True, False, None):
            for full in (True, False, None):
                check("accept reproduce units_match=%r units_full_match=%r" % (match, full),
                      lambda m=match, f=full: accepted(units, "reproduce",
                                                       facts=dict(FACTS["reproduce"], units_match=m,
                                                                  units_full_match=f)))
        for key, value in (("units_match", True), ("units_match", None),
                           ("units_full_match", False), ("units_full_match", None)):
            check("accept reproduce with only %s=%r" % (key, value),
                  lambda k=key, v=value: accepted(units, "reproduce",
                                                  facts=dict(FACTS["reproduce"], **{k: v})))
        check("accept reproduce without optional units facts",
              lambda: accepted(units, "reproduce", facts=FACTS["reproduce"]))
        check("accept FAIL reproduce with units_match=false and null counts",
              lambda: accepted(units, "reproduce", "FAIL",
                               facts=dict(FACTS["reproduce"], anchors_passed=None,
                                          anchors_total=None, units_match=False,
                                          units_full_match=None),
                               v1=dict(exit_code=4, exit_kind="guard", error_class="anchor")))
        check("accept SKIPPED reproduce with null units facts",
              lambda: accepted(units, "reproduce", "SKIPPED",
                               facts=dict.fromkeys(list(FACTS["reproduce"])
                                                   + ["units_match", "units_full_match"])))
        for key in ("units_match", "units_full_match"):
            for value in ("true", "false", "True", "", "null", SENTINEL, 1, 0, 1.0, 0.0,
                          math.nan, math.inf, [], [True], {key: True}):
                check("reject reproduce %s=%r" % (key, value),
                      lambda k=key, v=value: rejected(invalid, stage="reproduce",
                                                      facts=dict(FACTS["reproduce"], **{k: v})))
            check("reject %s on a non-reproduce stage" % key,
                  lambda k=key: rejected(invalid, stage="profile",
                                         facts=dict(FACTS["profile"], **{k: True})))
        # SCHEMAS.md "Standalone unit probe (U52)": reproduce facts add optional `units_outcome`
        # (one of the six unit-mode outcomes), `units_factor_2` and `units_factor_4` (finite
        # positive numbers or null) and `units_shared_writes` (boolean or null); all null outside
        # unit-probe mode and on SKIPPED/stub records; records without them stay valid.
        probe = root / "units-probe"
        for value in UNITS_OUTCOMES + (None,):
            check("accept reproduce units_outcome=%r" % (value,),
                  lambda v=value: accepted(probe, "reproduce",
                                           facts=dict(FACTS["reproduce"], units_outcome=v)))
        for key in ("units_factor_2", "units_factor_4"):
            # Numeric ratio facts accept integer spellings (SCHEMAS.md C/receipts/).
            for value in (2.5, 0.8, 1, 3, 1e-9, None):
                check("accept reproduce %s=%r" % (key, value),
                      lambda k=key, v=value: accepted(probe, "reproduce",
                                                      facts=dict(FACTS["reproduce"], **{k: v})))
        for value in (True, False, None):
            check("accept reproduce units_shared_writes=%r" % (value,),
                  lambda v=value: accepted(probe, "reproduce",
                                           facts=dict(FACTS["reproduce"], units_shared_writes=v)))
        check("accept reproduce with all four unit-probe facts (measured)",
              lambda: accepted(probe, "reproduce",
                               facts=dict(FACTS["reproduce"], anchors_passed=None, anchors_total=None,
                                          units_outcome="measured", units_factor_2=1.7,
                                          units_factor_4=2.4, units_shared_writes=True)))
        check("accept reproduce with all four unit-probe facts (skipped, nulls)",
              lambda: accepted(probe, "reproduce",
                               facts=dict(FACTS["reproduce"], units_outcome="skipped", units_factor_2=None,
                                          units_factor_4=None, units_shared_writes=None)))
        check("accept reproduce with unit-probe and units-check facts all null",
              lambda: accepted(probe, "reproduce",
                               facts=dict(FACTS["reproduce"], units_match=None, units_full_match=None,
                                          units_outcome=None, units_factor_2=None,
                                          units_factor_4=None, units_shared_writes=None)))
        check("accept reproduce without the unit-probe facts",
              lambda: accepted(probe, "reproduce", facts=FACTS["reproduce"]))
        check("accept FAIL reproduce (parse) with null unit-probe facts",
              lambda: accepted(probe, "reproduce", "FAIL",
                               facts=dict(FACTS["reproduce"], anchors_passed=None, anchors_total=None,
                                          units_outcome=None, units_factor_2=None,
                                          units_factor_4=None, units_shared_writes=None),
                               v1=dict(exit_code=2, exit_kind="guard", error_class="parse")))
        check("accept SKIPPED reproduce with null unit-probe facts",
              lambda: accepted(probe, "reproduce", "SKIPPED",
                               facts=dict.fromkeys(list(FACTS["reproduce"])
                                                   + ["units_outcome", "units_factor_2",
                                                      "units_factor_4", "units_shared_writes"])))
        for value in ("unknown", "", "MEASURED", "Measured", "measured ", "invalid-units",
                      SENTINEL, True, False, 0, 1, 1.0, [], ["measured"], {"outcome": "measured"}):
            check("reject reproduce units_outcome=%r" % (value,),
                  lambda v=value: rejected(invalid, stage="reproduce",
                                           facts=dict(FACTS["reproduce"], units_outcome=v)))
        for key in ("units_factor_2", "units_factor_4"):
            for value in (True, False, 0, 0.0, -0.0, -1, -2.5, math.nan, math.inf, -math.inf,
                          "2.5", "", SENTINEL, [2.5], {"factor": 2.5}):
                check("reject reproduce %s=%r" % (key, value),
                      lambda k=key, v=value: rejected(invalid, stage="reproduce",
                                                      facts=dict(FACTS["reproduce"], **{k: v})))
        for value in ("true", "false", "True", "", "null", SENTINEL, 1, 0, 1.0, 0.0,
                      math.nan, math.inf, [], [True], {"units_shared_writes": True}):
            check("reject reproduce units_shared_writes=%r" % (value,),
                  lambda v=value: rejected(invalid, stage="reproduce",
                                           facts=dict(FACTS["reproduce"], units_shared_writes=v)))
        for key, value in (("units_outcome", "measured"), ("units_factor_2", 2.0),
                           ("units_factor_4", 2.0), ("units_shared_writes", False)):
            check("reject %s on a non-reproduce stage" % key,
                  lambda k=key, v=value: rejected(invalid, stage="profile",
                                                  facts=dict(FACTS["profile"], **{k: v})))
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
        # SCHEMAS.md A/intake/ (U40): optional intake enum fact `licence_basis`, one of five
        # values or null; null on SKIPPED and stub records.
        basis = root / "licence-basis"
        for value in LICENCE_BASES + (None,):
            check("accept intake licence_basis=" + repr(value),
                  lambda v=value: accepted(basis, "intake",
                                           facts=dict(FACTS["intake"], licence_basis=v)))
            # U41: only licence "restricted" names the `licence` blocker.
            check("accept FAIL intake licence_basis=" + repr(value),
                  lambda v=value: accepted(basis, "intake", "FAIL",
                                           facts=dict(FACTS["intake"], licence="restricted",
                                                      anchored=False, licence_basis=v),
                                           v1=dict(exit_code=2, exit_kind="guard",
                                                   error_class="numeric",
                                                   blockers=["licence"])))
        check("accept intake without optional licence_basis",
              lambda: accepted(basis, "intake", facts=FACTS["intake"]))
        check("accept SKIPPED intake with null licence_basis",
              lambda: accepted(basis, "intake", "SKIPPED",
                               facts=dict.fromkeys(list(FACTS["intake"]) + ["anchored", "licence_basis"])))
        for value in ("Explicit", "EXPLICIT", "explicit ", "distributed", "permitted",
                      "unknown", "restricted", "null", "None", "", SENTINEL, True, False, 0, 1,
                      1.5, math.nan, [], ["explicit"], {"licence_basis": "explicit"}):
            check("reject intake licence_basis=" + repr(value),
                  lambda v=value: rejected(invalid, stage="intake",
                                           facts=dict(FACTS["intake"], licence_basis=v)))
        check("reject licence_basis on a non-intake stage",
              lambda: rejected(invalid, stage="reproduce",
                               facts=dict(FACTS["reproduce"], licence_basis="explicit")))
        for value in LICENCE_BASES + (None,):
            check("takeaway shows intake licence_basis=" + repr(value),
                  lambda v=value: licence_basis_takeaway(
                      root / ("takeaway-licence-basis-" + str(v)), v))
        # SCHEMAS.md A/intake/ (U41): the takeaway shows `licence` next to `licence_basis`;
        # a PASS intake with licence other than "permitted" adds exactly one authority line.
        for status, licence, extra, blockers, line in (
                ("PASS", "permitted", {}, ["none"], False),
                ("PASS", "unknown", {}, ["none"], True),
                ("FAIL", "restricted", {}, ["licence"], False),
                ("FAIL", "unknown", dict(data="unavailable"), ["data_unavailable"], False),
                ("FAIL", "unknown", dict(found=False), ["none"], False),
                ("FAIL", "permitted", dict(stock_environment=False), ["env_irreproducible"], False)):
            check("takeaway licence=%s on %s intake%s %s authority line"
                  % (licence, status, "".join(" " + k for k in sorted(extra)),
                     "with one" if line else "without"),
                  lambda s=status, l=licence, e=extra, b=blockers, w=line: licence_takeaway(
                      root / ("takeaway-licence-%s-%s-%s" % (s, l, "-".join(sorted(e)) or "alone")),
                      s, l, e, b, w))
        # SCHEMAS.md propose facts: optional votes_reject, votes_abstain (nonnegative
        # integers) and outcome (approved, rejected, conditions_unmet, no_feasible_method
        # or null).
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
        # SCHEMAS.md: "`no_feasible_method` is set only by the measured negative finding
        # above, with all ballot counts 0."
        check("accept propose measured negative finding",
              lambda: accepted(ballots, "propose", facts=dict(
                  FACTS["propose"], method="none", expected_speedup=None, votes_approve=0,
                  vote_share=0, gate_pass=False, votes_reject=0, votes_abstain=0,
                  outcome="no_feasible_method")))
        for value in ("no_feasible_methods", "No_feasible_method", "no-feasible-method"):
            check("reject propose outcome=%r" % (value,),
                  lambda v=value: rejected(invalid, stage="propose",
                                           facts=dict(FACTS["propose"], outcome=v)))
        for approve, reject, abstain, outcome in ((2, 1, 1, "conditions_unmet"),
                                                  (0, 3, 0, "rejected"),
                                                  (1, 0, 4, "approved"),
                                                  (0, 0, 5, "conditions_unmet"),
                                                  (0, 0, 0, "no_feasible_method"),
                                                  (0, 0, 0, None)):
            nulls = (5 - approve - reject - abstain) if outcome in COUNTED else None
            check("takeaway propose row shows outcome %s and ballots %d/%d/%d/%s"
                  % (outcome, approve, reject, abstain, nulls)
                  + ("; Finding line" if outcome == "no_feasible_method" else "; no Finding line"),
                  lambda a=approve, r=reject, b=abstain, o=outcome: ballot_takeaway(
                      root / ("takeaway-ballots-%s-%d%d%d" % (o, a, r, b)), a, r, b, o))
        check("takeaway without propose outcome has no Finding line",
              lambda: require(not finding_lines(anchored_text(root / "takeaway-plain")),
                              "Finding line without no_feasible_method"))
        # SCHEMAS.md "Card calibration (U54)": reproduce facts add optional `card_inputs`,
        # `card_measured`, `card_holds` and `card_refuted`, nonnegative integers; all four null
        # outside card mode, on SKIPPED/stub records and without card_scored.json; records
        # without them stay valid.
        card_keys = ("card_inputs", "card_measured", "card_holds", "card_refuted")
        cards = root / "card-totals"
        check("accept reproduce without the four card totals",
              lambda: accepted(cards, "reproduce", facts=FACTS["reproduce"]))
        check("accept reproduce with the four card totals null",
              lambda: accepted(cards, "reproduce",
                               facts=dict(FACTS["reproduce"], **dict.fromkeys(card_keys))))
        check("accept reproduce with the four card totals (3, 2, 1, 1)",
              lambda: accepted(cards, "reproduce", facts=dict(
                  FACTS["reproduce"], card_inputs=3, card_measured=2, card_holds=1, card_refuted=1)))
        check("accept reproduce with the four card totals zero",
              lambda: accepted(cards, "reproduce",
                               facts=dict(FACTS["reproduce"], **dict.fromkeys(card_keys, 0))))
        check("accept SKIPPED reproduce with null card totals",
              lambda: accepted(cards, "reproduce", "SKIPPED",
                               facts=dict.fromkeys(list(FACTS["reproduce"]) + list(card_keys))))
        for key in card_keys:
            for value in (0, 7, None):
                check("accept reproduce %s=%r" % (key, value),
                      lambda k=key, v=value: accepted(cards, "reproduce",
                                                      facts=dict(FACTS["reproduce"], **{k: v})))
            for value in (-1, -7, 1.5, 0.5, -0.5, True, False, math.nan, math.inf, "3", "",
                          SENTINEL, [3], {key: 3}):
                check("reject reproduce %s=%r" % (key, value),
                      lambda k=key, v=value: rejected(invalid, stage="reproduce",
                                                      facts=dict(FACTS["reproduce"], **{k: v})))
            check("reject reproduce %s negative alongside valid totals" % key,
                  lambda k=key: rejected(invalid, stage="reproduce", facts=dict(
                      FACTS["reproduce"], **dict(dict.fromkeys(card_keys, 1), **{k: -1}))))
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
