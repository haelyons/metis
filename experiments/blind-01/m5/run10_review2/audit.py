"""Static, local review only. Never imports or executes the reviewed program."""
import ast
import csv
import difflib
import hashlib
import json
import math
import re
import stat
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "run10_review2"
ORIGINAL = ROOT / "run9/agent/harness"
CANDIDATE = ROOT / "run10_harness2"
REPRO = ROOT / "run9/agent/results/reproduce/out"
PROFILE = ROOT / "run9/agent/results/profile/out"


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path):
    def unique(pairs):
        d = {}
        for k, v in pairs:
            assert k not in d, (path, k)
            d[k] = v
        return d
    return json.loads(path.read_text(), object_pairs_hook=unique)


copies = []
for p in sorted(ORIGINAL.iterdir()):
    assert p.is_file()
    q = CANDIDATE / p.name
    a, b = p.stat(), q.stat()
    copies.append(dict(name=p.name, bytes=a.st_size, sha256=digest(p),
                       bytes_equal=p.read_bytes() == q.read_bytes(),
                       mode_equal=stat.S_IMODE(a.st_mode) == stat.S_IMODE(b.st_mode),
                       mtime_ns_equal=a.st_mtime_ns == b.st_mtime_ns))
assert all(x["bytes_equal"] and x["mode_equal"] and x["mtime_ns_equal"] for x in copies)
o = (ORIGINAL / "run_command.sh").read_text()
u = (CANDIDATE / "run_units.sh").read_text()
(DEST / "run_units.diff").write_text("".join(difflib.unified_diff(
    o.splitlines(True), u.splitlines(True),
    fromfile="run9/agent/harness/run_command.sh", tofile="run10_harness2/run_units.sh")))
ol, ul = o.split("\n"), u.split("\n")
assert ol[20:48] == ul[22:50]
assert ol[116:] == ul[131:]
assert ol[49:81] == ul[51:83]

syntax = []
for name in ("setup.sh", "run_command.sh", "run_anchors.sh", "run_evaluation.sh", "run_units.sh"):
    result = subprocess.run(["bash", "-n", str(CANDIDATE / name)], capture_output=True, text=True)
    syntax.append(dict(name=name, returncode=result.returncode, stderr=result.stderr))
    assert result.returncode == 0
python_blocks = []
for i, line in enumerate(ul):
    if line.endswith("<<'PY'"):
        end = ul.index("PY", i + 1)
        ast.parse("\n".join(ul[i + 1:end]))
        python_blocks.append(dict(first_line=i + 2, last_line=end, parses=True))

units_path = CANDIDATE / "units.json"
manifest_text = units_path.read_text()
manifest_lines = manifest_text.split("\n")
manifest = load_json(units_path)
assert set(manifest) == {"units"}
units = manifest["units"]
assert isinstance(units, list) and len(units) >= 4
assert all(set(x) == {"id", "outputs", "cost_s"} for x in units)
ids = [x["id"] for x in units]
assert len(ids) == len(set(ids))
assert all(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:+=-]{0,127}", x) for x in ids)
rows = list(csv.DictReader((REPRO / "results/frodock_setup.csv").open()))
assert [x["id"] + ":" + x["kind"] for x in rows] == ids
assert all(set(r) == {"id", "kind", "receptor", "ligand"} and all(r.values()) for r in rows)
details_path = REPRO / "anchors_details.json"
details = load_json(details_path)
details_lines = details_path.read_text().split("\n")
assert [x["id"] + ":" + x["kind"] for x in details["jobs"]] == ids
log = (REPRO / "run_command/run_command.log").read_bytes().decode()
# LF numbering deliberately retains embedded CR progress updates on their LF line.
log_lines = log.split("\n")
starts, ends = {}, {}
for n, line in enumerate(log_lines, 1):
    m = re.search(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3}) \|.*Running FroDock \(50 solutions\) on complex (\S+) (\S+) ", line)
    if m:
        starts[m[2] + ":" + m[3]] = (n, m[1], datetime.strptime(m[1], "%Y-%m-%d %H:%M:%S,%f").timestamp())
    m = re.search(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d{3}) \|.*Copying the results to \S*/frodock/([^/\s]+)/(\w+)_decoys", line)
    if m:
        ends[m[2] + ":" + m[3]] = (n, m[1], datetime.strptime(m[1], "%Y-%m-%d %H:%M:%S,%f").timestamp())
assert list(starts) == ids == list(ends)
all_outputs, evidence = set(), []
for n, (unit, row, job) in enumerate(zip(units, rows, details["jobs"]), 1):
    cost = unit["cost_s"]
    assert type(cost) in (float, int) and math.isfinite(cost) and cost > 0
    assert cost == job["docking_wall_s"] == ends[unit["id"]][2] - starts[unit["id"]][2]
    outputs = unit["outputs"]
    assert isinstance(outputs, list) and outputs and len(outputs) == len(set(outputs))
    for output in outputs:
        assert all(re.fullmatch(r"[A-Za-z0-9._+=-]+", part) and part not in (".", "..") for part in output.split("/"))
    directory = f"results/frodock/{row['id']}/{row['kind']}_decoys"
    expected = [f"{directory}/model_{rank}.pdb" for rank in range(1, 51)]
    assert outputs == expected
    assert set(p.name for p in (REPRO / directory).iterdir()) == {Path(p).name for p in outputs}
    assert not all_outputs.intersection(outputs)
    all_outputs.update(outputs)
    assert all((REPRO / p).is_file() for p in outputs)
    id_line = next(i for i, l in enumerate(manifest_lines, 1) if json.dumps(unit["id"]) in l)
    cost_line = id_line + next(i for i, l in enumerate(manifest_lines[id_line:]) if '"cost_s"' in l) + 1
    evidence.append(dict(position=n, id=unit["id"], csv_line=n + 1,
                         manifest_id_line=id_line, manifest_cost_line=cost_line,
                         details_cost_line=[i for i, l in enumerate(details_lines, 1) if re.search(r'"docking_wall_s": [0-9]', l)][n - 1],
                         cost_s=cost, outputs=len(outputs),
                         log_start_line=starts[unit["id"]][0], log_copy_line=ends[unit["id"]][0],
                         start=starts[unit["id"]][1], copy=ends[unit["id"]][1]))
assert {str(p.relative_to(REPRO)) for p in (REPRO / "results/frodock").rglob("*") if p.is_file()} == all_outputs
assert {str(p.relative_to(PROFILE)) for p in (PROFILE / "results/frodock").rglob("*") if p.is_file()} == all_outputs
matches, total_bytes = 0, 0
for output in sorted(all_outputs):
    a, b = REPRO / output, PROFILE / output
    equal = a.read_bytes() == b.read_bytes()
    assert equal, output
    matches += equal
    total_bytes += a.stat().st_size
assert (REPRO / "results/frodock_setup.csv").read_bytes() == (PROFILE / "results/frodock_setup.csv").read_bytes()
applied_patch_matches = (ORIGINAL / "pinder_frodock_fixes.patch").read_bytes() == (REPRO / "setup/pinder_frodock_fixes.applied.patch").read_bytes()
assert applied_patch_matches

# Decode only named source-bearing completed events. Never execute recorded commands.
record = ROOT / "run9/agent/wf/agents/0006-anchors-repair/codex-1.jsonl"
sources = []
for n, line in enumerate(record.open(), 1):
    if n not in (103, 129):
        continue
    item = json.loads(line)["params"]["item"]
    assert item["status"] == "completed" and item["exitCode"] == 0
    out = item["aggregatedOutput"]
    if n == 103:
        for part in out.split("\nFILE ")[1:]:
            name, src = part.split("\n", 1)
            local = {"src/pinder-methods/pinder/methods/run/frodock/predict.py": "saved_predict.py.txt",
                     "src/pinder-eval/pinder/eval/dockq/method.py": "saved_eval_method_81_260.py.txt",
                     "src/pinder-eval/pinder/eval/run.py": "saved_eval_run.py.txt"}[name]
            (DEST / local).write_text(src)
            sources.append(dict(record=str(record.relative_to(ROOT)), record_line=n, upstream_path=name,
                                local=local, sha256=digest(DEST / local)))
    else:
        local = "saved_core_utils_excerpt.py.txt"
        (DEST / local).write_text(out)
        sources.append(dict(record=str(record.relative_to(ROOT)), record_line=n,
                            local=local, sha256=digest(DEST / local)))

audit = dict(copies=copies, syntax=syntax, python_blocks=python_blocks,
             environment_block_equal=True, output_setup_equal=True, predict_repair_score_suffix_equal=True,
             units=evidence, unit_count=len(units), output_count=len(all_outputs),
             costs_sum_s=sum(x["cost_s"] for x in units),
             saved_full_runs_pdb_matches=matches, saved_full_run_pdb_bytes_each=total_bytes,
             saved_full_run_csv_bytes_equal=True, applied_patch_matches=applied_patch_matches,
             sources=sources, native_compound_id_acceptance="unknown",
             isolated_reordered_concurrent_output_equality="unknown")
(DEST / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
table = ["| # | Unit | CSV line | Manifest id/cost lines | Details cost line | cost_s | Log start/copy lines |",
         "| ---: | --- | ---: | --- | ---: | ---: | --- |"]
for e in evidence:
    table.append(f"| {e['position']} | `{e['id']}` | {e['csv_line']} | {e['manifest_id_line']}/{e['manifest_cost_line']} | {e['details_cost_line']} | {e['cost_s']} | {e['log_start_line']}/{e['log_copy_line']} |")
(DEST / "unit_evidence.md").write_text("\n".join(table) + "\n")
print(json.dumps(dict(copies_verified=len(copies), shell_parses=len(syntax), python_blocks=len(python_blocks),
                      units=len(units), outputs=len(all_outputs), costs_sum_s=audit["costs_sum_s"],
                      full_run_pdb_matches=matches, bytes_each=total_bytes, sources=len(sources))))
