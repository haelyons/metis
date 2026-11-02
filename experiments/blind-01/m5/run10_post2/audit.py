"""Inspect retained records and source bytes; never import or execute workload code."""
from pathlib import Path
import csv
import hashlib
import io
import json
import re
import stat
import struct
import tarfile

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "run10_post2"
EVIDENCE = DEST / "evidence"
EVIDENCE.mkdir(exist_ok=True)

def sha(data):
    return hashlib.sha256(data).hexdigest()

record = json.loads((ROOT / "run10/agent/results/reproduce/out/setup/setup_record.json").read_text())
sources = []
archives = [
    (Path("/home/hal/.cache/blind01/intake_check_dl/codex/pinder_code.1.body"), record["pinder_archive_sha256"], {
        "pinder/core/__init__.py": "core_init.py.txt",
        "pinder/core/_version.py": "core_version.py.txt",
        "pinder/core/structure/atoms.py": "core_atoms.py.txt",
        "pinder/core/utils/process.py": "core_process.py.txt",
        "pinder/eval/dockq/biotite_dockq.py": "biotite_dockq.py.txt",
        "pinder/methods/run/frodock/predict.py": "predict_upstream.py.txt",
        "pinder/methods/main.py": "main_upstream.py.txt",
    }),
    (Path("/home/hal/.cache/blind01/intake_check_dl/acquire/gcp_mirror_package.body"), record["frodock_archive_sha256"], {
        "src/frodockgrid/frodockgrid.cpp": "frodockgrid.cpp.txt",
        "src/libfrodock/frodock.cpp": "libfrodock.cpp.txt",
        "src/frodock/frodock.cpp": "frodock.cpp.txt",
        "src/frodockcluster/frodockcluster.cpp": "frodockcluster.cpp.txt",
        "src/frodockview/frodockview.cpp": "frodockview.cpp.txt",
        "src/libvolume/fwr.cpp": "volume_fwr.cpp.txt",
    }),
]
for path, expected, wanted in archives:
    digest = sha(path.read_bytes())
    assert digest == expected
    sources.append({"archive": str(path), "sha256": digest})
    found = set()
    with tarfile.open(path) as bundle:
        for member in bundle.getmembers():
            if not member.isfile():
                continue
            for suffix, filename in wanted.items():
                if member.name.endswith("/" + suffix):
                    assert suffix not in found
                    found.add(suffix)
                    data = bundle.extractfile(member).read()
                    (EVIDENCE / filename).write_bytes(data)
                    sources.append({"member": member.name, "saved": filename, "sha256": sha(data)})
    assert found == set(wanted)

# Apply retained textual diff in memory, verifying every context/deleted line.
# This reconstructs inspected installed source; it does not execute that source.
patch = (ROOT / "run10/agent/results/reproduce/out/setup/pinder_frodock_fixes.applied.patch").read_text()
assert patch == (ROOT / "run9/agent/harness/pinder_frodock_fixes.patch").read_text()
parts = re.split(r"(?=^--- a/)", patch, flags=re.M)
for suffix, raw, target in [
    ("/main.py", "main_upstream.py.txt", "main_patched.py.txt"),
    ("/frodock/predict.py", "predict_upstream.py.txt", "predict_patched.py.txt"),
]:
    part = next(p for p in parts if p.startswith("--- a/") and p.splitlines()[0].endswith(suffix))
    lines = (EVIDENCE / raw).read_text().splitlines(keepends=True)
    result = []
    position = 0
    in_hunk = False
    for line in part.splitlines(keepends=True)[2:]:
        match = re.match(r"@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@", line)
        if match:
            start = int(match[1]) - 1
            assert start >= position
            result.extend(lines[position:start])
            position = start
            in_hunk = True
        elif in_hunk and line[:1] in (" ", "-", "+"):
            if line[:1] in (" ", "-"):
                assert line[1:] == lines[position], (target, position)
                position += 1
            if line[:1] in (" ", "+"):
                result.append(line[1:])
    result.extend(lines[position:])
    (EVIDENCE / target).write_text("".join(result))

markers = ["--- Logging error ---", "TypeError:", "non-zero exit code", "WARNING!!", "UserWarning", "| ERROR :", "Skipping "]
logs = {}
for label, name in [
    ("subset", "run10/agent/results/reproduce/units-check/run.log"),
    ("run9", "run9/agent/results/reproduce/out/run_command/run_command.log"),
]:
    lines = (ROOT / name).read_bytes().split(b"\n")
    decoded = [line.decode(errors="replace") for line in lines]
    starts = [(i, re.search(r"on complex (\S+) (\S+)", line)) for i, line in enumerate(decoded) if "Running FroDock" in line]
    jobs = []
    for j, (start, match) in enumerate(starts):
        end = starts[j + 1][0] if j + 1 < len(starts) else next(i for i in range(start, len(lines)) if b"PREDICT_EXIT=" in lines[i])
        segment = decoded[start:end]
        temp = next(re.search(r"PosixPath\('([^']+)'\)", line)[1] for line in segment if line.startswith("Arguments: "))
        jobs.append({"id": match[1] + ":" + match[2], "start_line": start + 1, "end_line": end,
                     "temp": temp, "markers": {m: [start + i + 1 for i, line in enumerate(segment) if m in line] for m in markers},
                     "map_lines": [start + i + 1 for i, line in enumerate(segment) if "Written " in line and "map:" in line],
                     "copy_line": next(start + i + 1 for i, line in enumerate(segment) if "Copying the results" in line),
                     "generated_ligand_lines": [start + i + 1 for i, line in enumerate(segment) if re.search(r"=> \S+_\d+\.pdb", line)],
                     })
    logs[label] = {"path": name, "sha256": sha(b"\n".join(lines)), "jobs": jobs,
                   "markers": {m: [i + 1 for i, line in enumerate(decoded) if m in line] for m in markers},
                   "error_records": [{"line": i + 1, "text": line} for i, line in enumerate(decoded) if "| ERROR :" in line]}

units = json.loads((ROOT / "run10/agent/harness/units.json").read_text())["units"]
check = json.loads((ROOT / "run10/agent/results/reproduce/units_check.json").read_text())
subset = ROOT / "run10/agent/results/reproduce/units-check/files"
reference = ROOT / "run9/agent/results/reproduce/out"
outputs = []
stages = []
for sample in check["sample"]:
    unit = units[sample["index"]]
    job = next(j for j in logs["subset"]["jobs"] if j["id"] == unit["id"])
    stage = subset / "tmp" / Path(job["temp"]).name
    old_job = next(j for j in logs["run9"]["jobs"] if j["id"] == unit["id"])
    old_stage = reference / "tmp" / Path(old_job["temp"]).name
    intermediate_comparisons = []
    for p in sorted(stage.iterdir()):
        if p.name.startswith("model_"):
            continue
        old = old_stage / p.name
        intermediate_comparisons.append({"file": p.name, "bytes": p.stat().st_size,
                                         "run9_file": str(old.relative_to(ROOT)),
                                         "equals_run9": p.read_bytes() == old.read_bytes()})
    maps = []
    for p in sorted(stage.glob("*.mrc")):
        with p.open("rb") as f:
            header = f.read(1024)
        nx, ny, nz, mode = struct.unpack_from("<4i", header)
        expected = 1024 + nx * ny * nz * 4
        assert mode == 2 and min(nx, ny, nz) > 0 and p.stat().st_size == expected
        maps.append({"file": p.name, "shape": [nx, ny, nz], "mode": mode, "bytes": expected})
    stages.append({"id": unit["id"], "directory": str(stage.relative_to(ROOT)), "map_headers": maps,
                   "intermediate_comparisons": intermediate_comparisons,
                   "files": [{"name": p.name, "bytes": p.stat().st_size, "symlink": p.is_symlink()} for p in sorted(stage.iterdir())]})
    for name in unit["outputs"]:
        actual = subset / name
        frozen = reference / name
        staged = stage / actual.name
        a, b, c = actual.read_bytes(), frozen.read_bytes(), staged.read_bytes()
        links = [str(p.relative_to(ROOT)) for p in [actual, *actual.parents] if p != ROOT and ROOT in p.parents and p.is_symlink()]
        assert not links
        assert stat.S_ISREG(actual.lstat().st_mode) and actual.stat().st_nlink == 1
        assert stat.S_ISREG(staged.lstat().st_mode) and staged.stat().st_nlink == 1
        assert actual.stat().st_ino != staged.stat().st_ino or actual.stat().st_dev != staged.stat().st_dev
        assert a and a == b == c
        outputs.append({"index": sample["index"], "path": name, "bytes": len(a), "sha256": sha(a),
                        "equals_run9": a == b, "equals_subset_stage": a == c, "local_links": links,
                        "local_nlink": actual.stat().st_nlink})

prepared = (reference / "results/frodock_setup.csv").read_bytes().splitlines(keepends=True)
restricted = (subset / "results/frodock_setup.csv").read_bytes()
assert restricted == prepared[0] + b"".join(prepared[s["index"] + 1] for s in check["sample"])
assert (subset / "run_command/chain_labels_restored.json").read_text() == "[]"
assert len(outputs) == 200
assert all(len(j["generated_ligand_lines"]) == 50 for j in logs["subset"]["jobs"])
assert len(stages) == 4
assert all(len(s["map_headers"]) == 4 and len(s["files"]) == 56 for s in stages)
assert all(r["equals_run9"] for s in stages for r in s["intermediate_comparisons"])
audit = {"sources": sources, "logs": logs, "stages": stages, "outputs": outputs,
         "summary": {"files": len(outputs), "bytes": sum(r["bytes"] for r in outputs),
                     "all_equal_run9_and_private_stage": True, "all_local_result_paths_regular_without_symlink_or_hardlink": True,
                     "restricted_list_original_records": True,
                     "chain_repairs": 0, "subset_rc": check["subset_rc"]}}
# Independently authenticate earlier saved sources cited in REPORT.md.
prior_sources = {
    "pinder/core/index/utils.py": "run10_review3/evidence/core_index_utils.py.txt",
    "pinder/core/index/system.py": "run10_post/evidence/core_index_system.py.txt",
    "pinder/core/utils/dataset.py": "run10_post/evidence/core_utils_dataset.py.txt",
    "pinder/core/utils/log.py": "run10_post/evidence/core_utils_log.py.txt",
    "pinder/eval/dockq/method.py": "run10_review3/evidence/eval_method.py.txt",
    "pinder/eval/run.py": "run10_review3/evidence/eval_run.py.txt",
}
found = set()
with tarfile.open(archives[0][0]) as bundle:
    for member in bundle.getmembers():
        if not member.isfile():
            continue
        for suffix, saved in prior_sources.items():
            if member.name.endswith("/" + suffix):
                data = bundle.extractfile(member).read()
                assert data == (ROOT / saved).read_bytes()
                found.add(suffix)
                sources.append({"member": member.name, "verified_prior_copy": saved, "sha256": sha(data)})
assert found == set(prior_sources)
(DEST / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
print("Retained-record audit passed.")
