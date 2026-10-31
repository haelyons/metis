"""Read saved records and archive data; never execute setup or archived code."""
import ast
import difflib
import hashlib
import json
from pathlib import Path
import posixpath
import re
import shlex
import shutil
import subprocess
import tarfile

BASE = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent / "evidence"
OUT.mkdir(exist_ok=True)
AGENTS = BASE / "run7/agent/wf/agents"


def records(folder):
    result = []
    for number, line in enumerate((AGENTS / folder / "codex-1.jsonl").read_text().splitlines(), 1):
        obj = json.loads(line)
        if obj.get("method") == "item/completed":
            result.append((number, obj.get("params", {}).get("item", {})))
    return result


def setup_changes(rows):
    return [(n, c["diff"]) for n, item in rows
            if item.get("type") == "fileChange" and item.get("status") == "completed"
            for c in item.get("changes", []) if c["path"].endswith("/harness/setup.sh")]


def reverse_patch(content, patch):
    lines = content.splitlines(keepends=True)
    hunks = []
    for line in patch.splitlines(keepends=True):
        match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
        if match:
            hunks.append((int(match[3]) - 1, [], []))
        elif hunks and line[:1] in (" ", "+", "-"):
            if line[0] in (" ", "+"):
                hunks[-1][1].append(line[1:])
            if line[0] in (" ", "-"):
                hunks[-1][2].append(line[1:])
    for start, new, old in reversed(hunks):
        assert lines[start:start + len(new)] == new
        lines[start:start + len(new)] = old
    return "".join(lines)


summary = {"reconstruction": [], "static_checks": [], "repair_tails": []}
versions = {3: (BASE / "run7/agent/harness/setup.sh").read_text()}
for attempt, folder in [(3, "0004-harness-repair"), (2, "0003-harness-repair")]:
    rows = records(folder)
    changes = setup_changes(rows)
    assert len(changes) == 1
    n, patch = changes[0]
    versions[attempt - 1] = reverse_patch(versions[attempt], patch)
    (OUT / f"repair-{attempt - 1}.recorded.diff").write_text(patch)
    snapshots = [n for n, item in rows if versions[attempt - 1] in (item.get("aggregatedOutput") or "")]
    assert snapshots
    summary["reconstruction"].append({"repair_record": folder, "completed_change_line": n,
                                       "pre_repair_full_snapshot_lines": snapshots})

# Independently connect attempt 1 to the original harness creation and final edit.
initial_rows = records("0002-harness")
original = versions[1]
initial_changes = setup_changes(initial_rows)
for n, patch in reversed(initial_changes):
    original = reverse_patch(original, patch)
creation_matches = []
for n, item in initial_rows:
    if item.get("type") != "commandExecution":
        continue
    argv = shlex.split(item.get("command", ""))
    if len(argv) == 3 and "cat > harness/setup.sh <<'BASH'\n" in argv[2]:
        body = argv[2].split("cat > harness/setup.sh <<'BASH'\n", 1)[1].split("\nBASH", 1)[0] + "\n"
        assert body == original
        creation_matches.append(n)
assert creation_matches
summary["original_harness"] = {"creation_command_lines": creation_matches,
                                "final_setup_change_lines": [n for n, _ in initial_changes],
                                "exact_creation_match": True}

for attempt, content in sorted(versions.items()):
    receipt = {1: "0004", 2: "0006", 3: "0008"}[attempt]
    target = OUT / f"setup-{receipt}.sh"
    target.write_text(content)
    assert content == (BASE / f"run7_diag/evidence/setup-{receipt}.sh").read_text()
    checked = subprocess.run(["bash", "--noprofile", "--norc", "-n", str(target)], capture_output=True, text=True)
    assert checked.returncode == 0
    blocks = re.findall(r"<<'PY'[^\n]*\n(.*?)\nPY(?:\n|$)", content, re.S)
    for block in blocks:
        ast.parse(block)
    row = {"attempt": attempt, "script": target.name,
           "sha256": hashlib.sha256(content.encode()).hexdigest(),
           "bash_n_rc": checked.returncode, "bash_n_stderr": checked.stderr,
           "python_blocks_parsed_without_execution": len(blocks)}
    if shutil.which("shellcheck"):
        checked = subprocess.run(["shellcheck", "--severity=error", "--norc", str(target)], capture_output=True, text=True)
        row["shellcheck"] = {"rc": checked.returncode, "stdout": checked.stdout, "stderr": checked.stderr}
    else:
        row["shellcheck"] = "not installed; not fetched"
    summary["static_checks"].append(row)

for repair in (1, 2):
    (OUT / f"repair-{repair}.diff").write_text("".join(difflib.unified_diff(
        versions[repair].splitlines(True), versions[repair + 1].splitlines(True),
        f"setup-attempt-{repair}.sh", f"setup-attempt-{repair + 1}.sh")))

for folder, receipt in [("0003-harness-repair", "0004"), ("0004-harness-repair", "0006")]:
    prompt = (AGENTS / folder / "prompt.md").read_bytes().decode()
    tail = prompt.split("Log tail (at most 200 lines):\n", 1)[1].rstrip()
    log = (BASE / f"run7/agent/results/reproduce/{receipt}-setup.log").read_bytes().decode()
    assert tail == "\n".join(log.rstrip().split("\n")[-200:])
    summary["repair_tails"].append({"folder": folder, "exact_last_200_line_match": True,
                                    "tail_lines": len(tail.split("\n"))})

script = versions[3]
targets = script.split("for target in \\\n", 1)[1].split("; do", 1)[0].replace("\\", "").split()
with tarfile.open(BASE / "run7/agent/harness/frodock.tar.gz") as archive:
    members = {m.name.rstrip("/"): m for m in archive.getmembers()}
    summary["frodock_archive_sha256"] = hashlib.sha256((BASE / "run7/agent/harness/frodock.tar.gz").read_bytes()).hexdigest()
    summary["frodock_links"] = [{"name": m.name, "target": m.linkname}
                                 for m in archive.getmembers() if m.issym() or m.islnk()]
    summary["build_targets"] = []
    for target in targets:
        prefix = "frodock3_linux64/src/" + target
        source_refs = re.findall(r"(?m)^\.\./[^\s\\]+", archive.extractfile(members[prefix + "/subdir.mk"]).read().decode())
        summary["build_targets"].append({"target": target, "makefile_exists": prefix + "/makefile" in members,
                                          "source_refs": len(source_refs),
                                          "missing_sources": [r for r in source_refs if posixpath.normpath(prefix + "/" + r) not in members]})
    summary["build_output_directories_exist"] = {name: "frodock3_linux64/" + name in members for name in ("bin", "lib")}

with tarfile.open(BASE / "run7/agent/harness/pinder-source.tar.gz") as archive:
    root = archive.getmembers()[0].name.split("/")[0]
    for relative, output in [("pyproject.toml", "pinder-pyproject.toml"),
                             ("src/pinder-methods/pinder/methods/preprocess/__init__.py", "pinder-preprocess.py.txt")]:
        (OUT / output).write_bytes(archive.extractfile(root + "/" + relative).read())

inventory = json.loads((BASE / "run7/agent/intake/data.json").read_text())["inventory"]
selected = [x for x in inventory if x["url"].startswith("https://pinderdata.org/2024-02/") and not x["name"].endswith(".zip")]
summary["release_inventory_selected_count"] = len(selected)
(OUT / "checks.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps({"reconstructed_attempts": 3, "bash_n": "all pass", "python_ast": "all pass",
                  "shellcheck": shutil.which("shellcheck"), "selected_release_files": len(selected),
                  "evidence": str(OUT.relative_to(BASE))}))
