"""Replay saved profile inputs without executing any workload."""
import difflib
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
base = Path(__file__).resolve().parent
cwd = base.parent
repo = cwd.parents[2]
source = cwd / "run9/agent/results/profile/out/profile"
module_path = repo / "dut/pipeline/m5/profile_summarise.py"
names = ["stats_cuda_gpu_kern_sum.csv", "stats_cuda_gpu_mem_time_sum.csv",
         "stats_cuda_api_sum.csv", "stats.log", "raw_wall_s.json", "gpu_util_raw.jsonl"]

def digest(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()

manifest = {}
for name in names:
    manifest[name] = {"bytes": (source / name).stat().st_size,
                      "sha256": digest(source / name)}
for target in ("u48", "patched"):
    directory = base / target
    directory.mkdir(exist_ok=True)
    for name in names:
        shutil.copyfile(source / name, directory / name)
        assert digest(directory / name) == manifest[name]["sha256"]
(base / "input_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

original = module_path.read_text()
original_hash = digest(module_path)
driver = base / "u48_direct.py"
driver.write_text('''import importlib.util
from pathlib import Path
import sys
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location("u48_summarise", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.summarise(Path(sys.argv[2]))
''')

executions = {}
def run(label, command):
    result = subprocess.run(command, capture_output=True, text=True, cwd=cwd)
    (base / (label + ".stdout.txt")).write_text(result.stdout)
    (base / (label + ".stderr.txt")).write_text(result.stderr)
    executions[label] = {"argv": command, "exit_code": result.returncode,
                         "stdout": result.stdout, "stderr": result.stderr}
    print(label, "exit:", result.returncode)
    print(result.stderr, end="")
    return result.returncode

run("u48_direct", [sys.executable, "-I", str(driver), str(module_path), str(base / "u48")])
spec = importlib.util.spec_from_file_location("u48_diagnostics", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
diagnostics = {}
for name in names[:3]:
    try:
        diagnostics[name] = {"rows": list(module.report_rows(base / "u48" / name))}
    except Exception as error:
        diagnostics[name] = {"exception": type(error).__name__, "message": str(error)}
(base / "report_diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n")

skip_lines = [line for line in (base / "u48/stats.log").read_text().splitlines()
              if line.startswith("SKIPPED:")]
assert len(skip_lines) == 3
old_phrases = ["CUDA kernel data", "CUDA memory data", "CUDA API data"]
actual_phrases = [line.split(" does not contain ", 1)[1].removesuffix(".") for line in skip_lines]
patched = original
for old, actual in zip(old_phrases, actual_phrases):
    assert original.count('"' + old + '"') == 1
    patched = patched.replace('"' + old + '"', '"' + actual + '"')
(base / "patched_summarise.py").write_text(patched)
(base / "phrase_patch.diff").write_text("".join(difflib.unified_diff(
    original.splitlines(keepends=True), patched.splitlines(keepends=True),
    fromfile="dut/pipeline/m5/profile_summarise.py", tofile="run9_replay2/patched_summarise.py")))
run("patched", [sys.executable, "-I", str(base / "patched_summarise.py"), str(base / "patched")])
assert digest(module_path) == original_hash
for name in names:
    assert digest(source / name) == manifest[name]["sha256"]
(base / "execution.json").write_text(json.dumps({
    "executions": executions, "skip_lines": skip_lines,
    "original_module_sha256": original_hash,
    "original_module_unchanged": True,
    "actual_activity_phrases": actual_phrases}, indent=2) + "\n")
