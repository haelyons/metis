"""Read-only source/manifest audit. No imports or execution of experiment code."""

import csv
import hashlib
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "run10_inputs"
CACHE = Path("/home/hal/.cache/blind01/intake_check_dl")
PIN = "ebeb28a2f8411363cef722b7d293c978f7442672"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def preserve(archive, expected, prefix, members):
    actual = digest(archive.read_bytes())
    assert actual == expected, (archive, actual)
    result = {"archive": str(archive), "sha256": actual, "members": {}}
    with tarfile.open(archive, "r:gz") as tf:
        for member, target in members.items():
            data = tf.extractfile(prefix + member).read()
            (DEST / "evidence" / target).write_bytes(data)
            result["members"][member] = {
                "copy": "evidence/" + target,
                "sha256": digest(data),
                "lines": len(data.splitlines()),
            }
    return result


(DEST / "evidence").mkdir(exist_ok=True)
pinder = preserve(
    CACHE / "codex/pinder_code.1.body",
    "b577532820ebbe5c16432b78c5e9c197690e863cb70a0a35a8ebcbe5277b76dd",
    "pinder-" + PIN + "/",
    {
        "src/pinder-methods/pinder/methods/__init__.py": "methods_init.py.txt",
        "src/pinder-methods/pinder/methods/main.py": "main.py.txt",
        "src/pinder-methods/pinder/methods/run/frodock/predict.py": "predict.py.txt",
        "src/pinder-eval/pinder/eval/dockq/method.py": "eval_method.py.txt",
    },
)
native = preserve(
    CACHE / "acquire/gcp_mirror_package.body",
    "91b9aeff747346046c7f8c4c92fa5749c9f082d8122ee9d2d4769855d35368f4",
    "frodock3_linux64/",
    {
        "src/frodockgrid/frodockgrid.cpp": "frodockgrid.cpp.txt",
        "src/libsas/sas.cpp": "sas.cpp.txt",
        "src/libsas/include/mersenne.h": "mersenne.h.txt",
        "src/frodockgrid/Release_MPI_GCC/makefile": "grid_MPI_GCC_makefile.txt",
        "src/frodockgrid/Release_MPI_GCC/objects.mk": "grid_MPI_GCC_objects.mk.txt",
        "src/frodockgrid/Release_MPI_GCC/subdir.mk": "grid_MPI_GCC_subdir.mk.txt",
        "src/libsas/Release_gcc/makefile": "sas_gcc_makefile.txt",
        "src/libsas/Release_gcc/subdir.mk": "sas_gcc_subdir.mk.txt",
        "compile_frodock.sh": "compile_frodock.sh.txt",
    },
)
for name in ("main.py.txt", "predict.py.txt"):
    assert (DEST / "evidence" / name).read_bytes() == (
        ROOT / "run10_why/evidence" / name
    ).read_bytes()

baseline = (ROOT / "run9/agent/harness/run_command.sh").read_bytes()
candidate = (ROOT / "run10_harness2/run_units.sh").read_bytes()
blines, clines = baseline.splitlines(keepends=True), candidate.splitlines(keepends=True)
parity = {}
for label, blo, bhi, clo, chi in (
    ("environment", 21, 48, 23, 50),
    ("output_setup", 50, 81, 52, 83),
    ("prediction_repair_evaluation", 117, 185, 132, 200),
):
    parity[label] = blines[blo - 1 : bhi] == clines[clo - 1 : chi]
    assert parity[label]

manifest_path = ROOT / "run9/agent/results/reproduce/out/results/frodock_setup.csv"
raw = manifest_path.read_bytes()
lines = raw.splitlines(keepends=True)
rows = list(csv.DictReader(io.StringIO(raw.decode())))
assert len(rows) == 16 and len(lines) == 17
assert list(rows[0]) == ["id", "kind", "receptor", "ligand"]
assert all(all(row.values()) for row in rows)
keys = [row["id"] + ":" + row["kind"] for row in rows]
assert len(set(keys)) == len(keys)
units = json.loads((ROOT / "run10_harness2/units.json").read_text())["units"]
assert keys == [unit["id"] for unit in units]
for unit, row in zip(units, rows):
    expected = {
        f'results/frodock/{row["id"]}/{row["kind"]}_decoys/model_{rank}.pdb'
        for rank in range(1, 51)
    }
    assert set(unit["outputs"]) == expected

# Exercise only CSV selection in memory, never prediction or other workload code.
# Every individual row and one reversed four-row selection retain exact fields.
requests = [[key] for key in keys] + [[keys[i] for i in (15, 9, 5, 3)]]
for requested in requests:
    chosen = lines[0] + b"".join(lines[keys.index(key) + 1] for key in requested)
    parsed = list(csv.DictReader(io.StringIO(chosen.decode())))
    assert parsed == [rows[keys.index(key)] for key in requested]

result = {
    "pinder": pinder,
    "native": native,
    "run_command_sha256": digest(baseline),
    "candidate_parity": parity,
    "applied_patch_matches": (
        ROOT / "run9/agent/harness/pinder_frodock_fixes.patch"
    ).read_bytes() == (
        ROOT / "run9/agent/results/reproduce/out/setup/pinder_frodock_fixes.applied.patch"
    ).read_bytes(),
    "manifest": {
        "path": str(manifest_path.relative_to(ROOT)),
        "sha256": digest(raw),
        "units": len(rows),
        "fields": list(rows[0]),
        "unit_order_and_all_800_path_formulas_match": True,
        "in_memory_selection_cases": len(requests),
        "selected_fields_and_original_line_bytes_retained": True,
    },
}
assert result["applied_patch_matches"]
(DEST / "audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"source_archives_verified": 2, "manifest_units": len(rows),
                  "selection_cases": len(requests), "candidate_parity": parity}))
