"""Classify saved profiler artifacts without running a workload."""

import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
root = Path(__file__).resolve().parent
source = root.parent / "run9_diag2" / "work"
work = root / "work"
work.mkdir(exist_ok=True)
names = [
    "stats_cuda_gpu_kern_sum.csv",
    "stats_cuda_gpu_mem_time_sum.csv",
    "stats_cuda_api_sum.csv",
    "stats.log",
    "nsys-version.txt",
    "raw_wall_s.json",
    "gpu_util_raw.jsonl",
]
evidence = {"copies": {}}
for name in names:
    original = source / name
    copied = work / name
    shutil.copyfile(original, copied)
    original_bytes = original.read_bytes()
    copied_bytes = copied.read_bytes()
    assert original_bytes == copied_bytes
    evidence["copies"][name] = {
        "bytes": len(copied_bytes),
        "sha256": hashlib.sha256(copied_bytes).hexdigest(),
    }

# Import only the explicitly permitted summariser functions. Do not modify
# pipeline files or create bytecode beside them.
module_path = root.parents[3] / "dut" / "pipeline" / "m5" / "profile_summarise.py"
spec = importlib.util.spec_from_file_location("saved_profile_summarise", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
evidence["summariser_path"] = str(module_path)


def attempt(function, *args):
    try:
        result = function(*args)
        # report_rows may return an iterator; consume it to exercise parsing.
        if function is module.report_rows:
            result = list(result)
        return {"ok": True, "result": result}
    except Exception as error:
        return {"ok": False, "exception": type(error).__name__, "message": str(error)}


evidence["report_rows"] = {
    name: attempt(module.report_rows, work / name) for name in names[:3]
}
evidence["summarise_original"] = attempt(module.summarise, work)

original_report_rows = module.report_rows
bypass_calls = []


def kernel_has_no_rows(path):
    bypass_calls.append(path.name)
    if path.name == "stats_cuda_gpu_kern_sum.csv":
        return []
    return original_report_rows(path)


module.report_rows = kernel_has_no_rows
try:
    evidence["summarise_kernel_no_rows"] = attempt(module.summarise, work)
    evidence["kernel_no_rows_report_calls"] = bypass_calls
finally:
    module.report_rows = original_report_rows

samples = [json.loads(line) for line in (work / "gpu_util_raw.jsonl").read_text().splitlines() if line.strip()]
wall = json.loads((work / "raw_wall_s.json").read_text())
inside = [sample for sample in samples if wall["start_monotonic_s"] <= sample["t"] <= wall["start_monotonic_s"] + wall["total_wall_s"]]
evidence["telemetry"] = {
    "samples": len(samples),
    "samples_inside_wall": len(inside),
    "util_min": min(sample["util"] for sample in samples),
    "util_max": max(sample["util"] for sample in samples),
    "nonzero_samples": sum(sample["util"] != 0 for sample in samples),
}
evidence["raw_wall"] = wall
(root / "validation.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(json.dumps(evidence, indent=2))
