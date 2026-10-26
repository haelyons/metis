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
  for candidate in /opt/nvidia/nsight-systems*/bin/nsys /opt/nvidia/nsight-systems*/*/bin/nsys \
                   /opt/nvidia/nsight-systems*/*/target-linux-x64/nsys; do
    if [[ -x $candidate ]]; then printf '%s\n' "$candidate"; return; fi
  done
  return 1
}
nsys_bin=$(find_nsys) || {
  python3 - "$script_dir/probe.json" "$out_dir" <<'PY'
import hashlib
import json
from pathlib import Path
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

    # Official Ubuntu 22.04 amd64 CLI package. Keep the version and SHA-256
    # pinned together; never trust a downloaded package without checking it.
    # Hash source: NVIDIA's devtools ubuntu2204/amd64/Packages index.
    base = "https://developer.download.nvidia.com/devtools/repos/ubuntu2204/amd64/"
    filename = "NsightSystems-linux-cli-public-2025.3.1.90-3582212.deb"
    sha256 = "d2484ad0faf6831b11fa0bf73c54232d9ea8beafb50414019e6ba299c4ed5718"
    destination = Path(sys.argv[2]).resolve() / filename
    with urllib.request.urlopen(base + filename, timeout=60) as response:
        destination.write_bytes(response.read())
    if hashlib.sha256(destination.read_bytes()).hexdigest() != sha256:
        raise RuntimeError("package checksum mismatch")
    # dpkg may leave the package unconfigured until apt installs dependencies
    # from the image's existing sources. No repositories are added.
    subprocess.run(["sudo", "-n", "dpkg", "-i", str(destination)], check=False)
    subprocess.run(["sudo", "-n", "apt-get", "-f", "install", "-y"], check=True)
PY
  [[ $? == 0 ]] || infra
  nsys_bin=$(find_nsys) || infra
}
export PATH="${nsys_bin%/*}:$PATH"
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
