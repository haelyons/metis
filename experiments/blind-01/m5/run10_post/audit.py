"""Read-only audit of retained records; writes evidence only under run10_post."""
from pathlib import Path
import hashlib
import json
import tarfile

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "run10_post"
manifest_path = ROOT / "run10/agent/harness/units.json"
check_path = ROOT / "run10/agent/results/reproduce/units_check.json"
manifest = json.loads(manifest_path.read_text())["units"]
check = json.loads(check_path.read_text())
subset = ROOT / "run10/agent/results/reproduce/units-check/files"
reference = ROOT / "run9/agent/results/reproduce/out"
rows = []
for sample in check["sample"]:
    unit = manifest[sample["index"]]
    for name in unit["outputs"]:
        actual = (subset / name).read_bytes()
        expected = (reference / name).read_bytes()
        rows.append({"index": sample["index"], "path": name,
                     "subset_bytes": len(actual), "reference_bytes": len(expected),
                     "byte_equal": actual == expected,
                     "sha256": hashlib.sha256(actual).hexdigest()})
log = (ROOT / "run10/agent/results/reproduce/units-check/run.log").read_bytes().split(b"\n")
markers = ("--- Logging error ---", "non-zero exit code", "WARNING!!", "UserWarning", "| ERROR :")
archives = [
    ("pinder", Path("/home/hal/.cache/blind01/intake_check_dl/codex/pinder_code.1.body"),
     "b577532820ebbe5c16432b78c5e9c197690e863cb70a0a35a8ebcbe5277b76dd"),
    ("frodock", Path("/home/hal/.cache/blind01/intake_check_dl/acquire/gcp_mirror_package.body"),
     "91b9aeff747346046c7f8c4c92fa5749c9f082d8122ee9d2d4769855d35368f4"),
]
source_records = []
evidence = DEST / "evidence"
evidence.mkdir(exist_ok=True)
for label, archive, expected in archives:
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    assert digest == expected
    source_records.append({"label": label, "archive": str(archive), "sha256": digest})
    if label == "pinder":
        wanted = {
            "/core/index/system.py": "core_index_system.py.txt",
            "/core/utils/dataset.py": "core_utils_dataset.py.txt",
            "/core/utils/log.py": "core_utils_log.py.txt",
        }
        with tarfile.open(archive) as bundle:
            for member in bundle.getmembers():
                for suffix, filename in wanted.items():
                    if member.isfile() and member.name.endswith(suffix):
                        data = bundle.extractfile(member).read()
                        (evidence / filename).write_bytes(data)
                        source_records.append({"member": member.name, "evidence": filename,
                                               "sha256": hashlib.sha256(data).hexdigest()})
result = {
    "files_total": len(rows), "files_matched": sum(r["byte_equal"] for r in rows),
    "subset_nonempty": sum(r["subset_bytes"] > 0 for r in rows),
    "reference_nonempty": sum(r["reference_bytes"] > 0 for r in rows),
    "bytes_per_side": sum(r["subset_bytes"] for r in rows),
    "minimum_bytes": min(r["subset_bytes"] for r in rows),
    "maximum_bytes": max(r["subset_bytes"] for r in rows),
    "log_marker_lines": {m: [i for i, line in enumerate(log, 1) if m.encode() in line] for m in markers},
    "ratio_recomputed": check["subset_wall_s"] / check["cost_sum_s"],
    "harness_matches_harness3": {name: (ROOT / "run10/agent/harness" / name).read_bytes() ==
                                 (ROOT / "run10_harness3" / name).read_bytes()
                                 for name in ("run_units.sh", "run_command.sh", "setup.sh", "units.json")},
    "sources": source_records, "files": rows,
}
assert len(rows) == 200 and all(r["byte_equal"] and r["subset_bytes"] > 0 for r in rows)
assert all(result["harness_matches_harness3"].values())
(DEST / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
print("Record audit passed.")
