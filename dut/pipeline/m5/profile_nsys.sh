#!/usr/bin/env bash
# Fixed box-side profiler. The pipeline uploads probe.json beside this script.
# Usage: profile_nsys.sh <run_command_file> <out_dir> <budget_s>
set -euo pipefail
[[ $# == 3 && $3 =~ ^[1-9][0-9]*$ ]] || exit 2
command_file=$1
out_dir=$2
budget_s=$3
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
mkdir -p -- "$out_dir"
infra() {
  printf '%s\n' 'M5_PROFILER_INFRA' >&2
  printf '%s\n' '{"error_class":"infra","marker":"M5_PROFILER_INFRA"}' > "$out_dir/infra.json"
  exit 2
}
trap infra ERR
rm -f -- "$out_dir/infra.json" "$out_dir/stages.json" "$out_dir/total_wall_s.json" "$out_dir/gpu_util.json"
[[ -s $command_file ]]

# Reuse installed nsys, including NVIDIA packages without a PATH symlink.
find_nsys() {
  command -v nsys && return
  local candidate
  for candidate in /opt/nvidia/nsight-systems*/bin/nsys /opt/nvidia/nsight-systems/*/bin/nsys; do
    if [[ -x $candidate ]]; then printf '%s\n' "$candidate"; return; fi
  done
  return 1
}
nsys_bin=$(find_nsys) || {
  python3 - "$script_dir/probe.json" "$out_dir" <<'PY'
import gzip
import hashlib
import json
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

probe = json.loads(Path(sys.argv[1]).read_text())
root = [] if subprocess.run(["id", "-u"], capture_output=True, text=True).stdout.strip() == "0" else ["sudo", "-n"]

with tempfile.TemporaryDirectory(prefix="m5-nsys-") as temporary:
    sources = Path(temporary) / "sources.list.d"
    sources.mkdir()
    sources.chmod(0o755)
    for source in probe.get("apt_sources", []):
        if any(line.strip() and not line.lstrip().startswith("#") for line in source["lines"]):
            file = Path(source["file"])
            if file.suffix in (".list", ".sources"):
                copied = sources / file.name
                shutil.copyfile(file, copied)
                copied.chmod(0o644)
    options = ["-o", "Dir::Etc::sourcelist=/dev/null", "-o", f"Dir::Etc::sourceparts={sources}"]
    # apt must be able to read the temporary source directory after dropping privileges.
    Path(temporary).chmod(0o755)
    if list(sources.iterdir()):
        subprocess.run(root + ["apt-get", *options, "update"], check=False)
        result = subprocess.run(root + ["apt-get", *options, "install", "-y", "--no-install-recommends", "nsight-systems-cli"])
        if result.returncode == 0:
            sys.exit(0)

    # Resolve the Nsight package selected by the probed CUDA toolkit, rather than
    # guessing a .deb filename or installing a newer, incompatible profiler.
    cuda = None
    for compiler in probe.get("nvcc", []):
        match = re.search(r"release (\d+)\.(\d+)", compiler.get("version") or "")
        if match:
            cuda = match.groups()
            break
    if cuda is None:
        match = re.fullmatch(r"(\d+)\.(\d+)", (probe.get("nvidia") or {}).get("cuda_version") or "")
        if match:
            cuda = match.groups()
    os_info = probe.get("os") or {}
    distro = os_info.get("id")
    version = os_info.get("version_id", "")
    architecture = {"x86_64": "x86_64", "aarch64": "sbsa"}.get(platform.machine())
    if not cuda or distro not in ("ubuntu", "debian") or not re.fullmatch(r"\d+(?:\.\d+)?", version) or not architecture:
        raise RuntimeError("no public package for probed platform")
    base = f"https://developer.download.nvidia.com/compute/cuda/repos/{distro}{version.replace('.', '')}/{architecture}/"
    with urllib.request.urlopen(base + "Packages.gz", timeout=60) as response:
        contents = gzip.decompress(response.read()).decode()
    packages = {}
    for stanza in contents.split("\n\n"):
        fields = dict(line.split(": ", 1) for line in stanza.splitlines() if ": " in line and not line.startswith(" "))
        if "Package" in fields:
            packages.setdefault(fields["Package"], []).append(fields)
    selectors = packages.get("cuda-nsight-systems-" + "-".join(cuda), [])
    if not selectors:
        raise RuntimeError("CUDA Nsight package unavailable")
    selector = selectors[-1]
    names = re.findall(r"(?:^|,\s*)(nsight-systems(?:-cli)?(?:-[\d.]+)?)\b", selector.get("Depends", ""))
    if not names or names[0] not in packages:
        raise RuntimeError("Nsight dependency unavailable")
    package = packages[names[0]][-1]
    filename = package["Filename"]
    if filename.startswith("./"):
        filename = filename[2:]
    if not re.fullmatch(r"[\w.+/-]+\.deb", filename) or ".." in filename:
        raise RuntimeError("invalid package filename")
    destination = Path(sys.argv[2]).resolve() / "nsight-systems.deb"
    with urllib.request.urlopen(base + filename, timeout=60) as response:
        destination.write_bytes(response.read())
    if hashlib.sha256(destination.read_bytes()).hexdigest() != package["SHA256"]:
        raise RuntimeError("package checksum mismatch")
    subprocess.run(root + ["apt-get", *options, "install", "-y", "--no-install-recommends", str(destination)], check=True)
PY
  [[ $? == 0 ]] || infra
  nsys_bin=$(find_nsys) || infra
}
"$nsys_bin" --version > "$out_dir/nsys-version.txt"

python3 - "$nsys_bin" "$command_file" "$out_dir" "$budget_s" <<'PY'
import json
import math
from pathlib import Path
import subprocess
import sys
import threading
import time

nsys, command, output, budget = sys.argv[1:]
directory = Path(output).resolve()
stop = threading.Event()

def sample():
    with (directory / "gpu_util_raw.jsonl").open("w") as log:
        while not stop.is_set():
            stamp = time.monotonic()
            try:
                result = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                                        capture_output=True, text=True, timeout=2, check=True)
                values = [float(line.strip()) for line in result.stdout.splitlines()]
                if values and all(math.isfinite(value) and 0 <= value <= 100 for value in values):
                    log.write(json.dumps(dict(t=stamp, util=sum(values) / len(values))) + "\n")
                    log.flush()
            except (OSError, ValueError, subprocess.SubprocessError):
                pass
            stop.wait(0.1)

# Time only the shared command. Installation, collection finalization and CSV
# export are outside the baseline wall clock. No command/environment rewriting.
launcher = '''import json, pathlib, subprocess, sys, time
start = time.monotonic()
result = subprocess.run(["bash", sys.argv[1]])
wall = time.monotonic() - start
pathlib.Path(sys.argv[2]).write_text(json.dumps(dict(total_wall_s=wall, start_monotonic_s=start)))
sys.exit(result.returncode)
'''
sampler = threading.Thread(target=sample)
sampler.start()
try:
    with (directory / "baseline.log").open("w") as log:
        result = subprocess.run([nsys, "profile", "--trace=cuda,nvtx,osrt", "--sample=none",
                                 "--force-overwrite=true", "--output=" + str(directory / "baseline"),
                                 "python3", "-c", launcher, command, str(directory / "raw_wall_s.json")],
                                stdout=log, stderr=subprocess.STDOUT, timeout=int(budget))
finally:
    stop.set()
    sampler.join()
sys.exit(result.returncode)
PY
"$nsys_bin" stats --report cuda_gpu_kern_sum,cuda_gpu_mem_time_sum,cuda_api_sum --format csv \
  --force-export=true --force-overwrite=true --output "$out_dir/stats" "$out_dir/baseline.nsys-rep" \
  > "$out_dir/stats.log" 2>&1
# Summarization errors remain parse failures, distinct from profiler infrastructure.
trap - ERR
python3 "$script_dir/profile_summarise.py" "$out_dir"
