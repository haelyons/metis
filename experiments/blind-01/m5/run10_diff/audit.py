"""Local record/byte audit only; never imports or executes experiment code."""
import csv
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "run10_diff"
REPRO = ROOT / "run9/agent/results/reproduce/out"
PROFILE = ROOT / "run9/agent/results/profile/out"


def sha(data):
    return hashlib.sha256(data).hexdigest()


baseline = (ROOT / "run9/agent/harness/run_command.sh").read_bytes()
candidate = (ROOT / "run10_harness2/run_units.sh").read_bytes()
bl, cl = baseline.splitlines(True), candidate.splitlines(True)
parity = {}
for label, a, b, c, d in [
    ("environment", 21, 48, 23, 50),
    ("output_setup", 50, 81, 52, 83),
    ("predict_repair_evaluation", 117, 185, 132, 200),
]:
    parity[label] = bl[a - 1:b] == cl[c - 1:d]
    assert parity[label]
patch = (ROOT / "run9/agent/harness/pinder_frodock_fixes.patch").read_bytes()
assert patch == (REPRO / "setup/pinder_frodock_fixes.applied.patch").read_bytes()
assert baseline == (ROOT / "run10_harness2/run_command.sh").read_bytes()

raw = (REPRO / "results/frodock_setup.csv").read_bytes()
lines = raw.splitlines(True)
rows = list(csv.DictReader(io.StringIO(raw.decode())))
assert len(rows) == 16 and len(lines) == 17
assert list(rows[0]) == ["id", "kind", "receptor", "ligand"]
keys = [r["id"] + ":" + r["kind"] for r in rows]
assert len(set(keys)) == 16
requests = [[k] for k in keys] + [[keys[i] for i in [15, 9, 5, 3]]]
for request in requests:
    restricted = lines[0] + b"".join(lines[keys.index(k) + 1] for k in request)
    assert list(csv.DictReader(io.StringIO(restricted.decode()))) == [rows[keys.index(k)] for k in request]

units = json.loads((ROOT / "run10_harness2/units.json").read_text())["units"]
assert [u["id"] for u in units] == keys
files = []
for u, row in zip(units, rows):
    expected = [f'results/frodock/{row["id"]}/{row["kind"]}_decoys/model_{i}.pdb' for i in range(1, 51)]
    assert u["outputs"] == expected
    for relative in expected:
        a = (REPRO / relative).read_bytes()
        b = (PROFILE / relative).read_bytes()
        assert a == b, relative
        files.append({"path": relative, "bytes": len(a), "sha256": sha(a), "byte_equal": True})
assert raw == (PROFILE / "results/frodock_setup.csv").read_bytes()

# Read only designated source-bearing records; do not execute their commands.
record = ROOT / "run9/agent/wf/agents/0006-anchors-repair/codex-1.jsonl"
source_checks = []
for n, line in enumerate(record.open(), 1):
    if n != 103:
        continue
    item = json.loads(line)["params"]["item"]
    assert item["status"] == "completed" and item["exitCode"] == 0
    for part in item["aggregatedOutput"].split("\nFILE ")[1:]:
        name, content = part.split("\n", 1)
        if name.endswith("/frodock/predict.py"):
            saved = (ROOT / "run10_inputs/evidence/predict.py.txt").read_text()
            assert content.rstrip() == saved.rstrip()
            source_checks.append({"record": str(record.relative_to(ROOT)), "line": n,
                                  "member": name, "matches_saved_source_ignoring_trailing_whitespace": True})
assert len(source_checks) == 1

log_records = {}
for label, directory in [("reproduce", REPRO), ("profile", PROFILE)]:
    ll = (directory / "run_command/run_command.log").read_bytes().decode().split("\n")
    selected = [{"line": i, "text": line} for i, line in enumerate(ll, 1)
                if line.startswith("CONFIG ") or "Running FroDock (50 solutions)" in line
                or "Success! Finished docking" in line or line.startswith(("PREDICT_EXIT=", "EVAL_EXIT=", "CHAIN_LABELS_RESTORED"))]
    assert sum("Running FroDock (50 solutions)" in r["text"] for r in selected) == 16
    log_records[label] = selected

changes = json.loads((REPRO / "run_command/chain_labels_restored.json").read_text())
result = {
    "run_command_sha256": sha(baseline), "candidate_parity": parity,
    "applied_patch_sha256": sha(patch), "applied_patch_equal": True,
    "prepared_manifest_sha256": sha(raw), "prepared_records": len(rows),
    "original_record_byte_selection_checks": len(requests),
    "source_checks": source_checks,
    "baseline_chain_repair": {"models": len(changes), "atoms": sum(len(c["line_numbers"]) for c in changes)},
    "full_run_comparison": {"left": str(REPRO.relative_to(ROOT)), "right": str(PROFILE.relative_to(ROOT)),
                            "files_equal": len(files), "bytes_per_run": sum(f["bytes"] for f in files),
                            "files": files},
    "logs": log_records,
}
(DEST / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"parity": parity, "records": len(rows), "byte_equal_files": len(files),
                  "bytes_per_run": result["full_run_comparison"]["bytes_per_run"],
                  "chain_repair": result["baseline_chain_repair"]}))
