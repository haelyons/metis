#!/usr/bin/env bash
# Deterministic stock-image facts for harness/repair prompts. No model, no sudo.
# Writes out/probe.json. Missing tools become null; never fails the stage for absence.
set +e
set -u
umask 077
mkdir -p out || exit 1

tmp=$(mktemp -d) || exit 1
trap 'rm -rf -- "$tmp"' EXIT

# --- os ---
os_json='null'
if [[ -r /etc/os-release ]]; then
  # shellcheck disable=SC1091
  . /etc/os-release
  os_json=$(ID="${ID-}" VERSION_ID="${VERSION_ID-}" PRETTY_NAME="${PRETTY_NAME-}" \
    VERSION="${VERSION-}" NAME="${NAME-}" python3 -c '
import json, os
print(json.dumps({
  "id": os.environ.get("ID") or None,
  "version_id": os.environ.get("VERSION_ID") or None,
  "pretty_name": os.environ.get("PRETTY_NAME") or None,
  "version": os.environ.get("VERSION") or None,
  "name": os.environ.get("NAME") or None,
}))' 2>/dev/null) || os_json='null'
fi

# --- kernel ---
kernel=$(uname -r 2>/dev/null) || kernel=

# --- nproc ---
nproc_n=$(nproc 2>/dev/null) || nproc_n=

# --- memory (KiB from MemTotal) ---
memory_kb=
if [[ -r /proc/meminfo ]]; then
  memory_kb=$(awk '/^MemTotal:/ {print $2; exit}' /proc/meminfo 2>/dev/null) || memory_kb=
fi

# --- free disk of $HOME (bytes available) ---
disk_home_bytes=
disk_home_bytes=$(df -B1 --output=avail "$HOME" 2>/dev/null | awk 'NR==2 {print $1; exit}') || disk_home_bytes=

# --- nvidia-smi ---
nvidia_json='null'
if command -v nvidia-smi >/dev/null 2>&1; then
  gpu_names=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null) || gpu_names=
  driver=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -n1) || driver=
  cuda_ver=$(nvidia-smi --query-gpu=cuda_version --format=csv,noheader 2>/dev/null | head -n1) || cuda_ver=
  # Older drivers expose CUDA via the summary line instead.
  if [[ -z ${cuda_ver:-} ]]; then
    cuda_ver=$(nvidia-smi 2>/dev/null | awk -F'CUDA Version: ' 'NF>1 {split($2,a," "); print a[1]; exit}') || cuda_ver=
  fi
  nvidia_json=$(GPU_NAMES="$gpu_names" DRIVER="$driver" CUDA_VER="$cuda_ver" python3 -c '
import json, os
names = [line.strip() for line in os.environ.get("GPU_NAMES", "").splitlines() if line.strip()]
driver = os.environ.get("DRIVER") or None
cuda = os.environ.get("CUDA_VER") or None
print(json.dumps({"gpus": names, "driver_version": driver, "cuda_version": cuda}))
' 2>/dev/null) || nvidia_json='null'
fi

# --- nvcc paths ---
: >"$tmp/nvcc_paths"
if command -v nvcc >/dev/null 2>&1; then
  command -v nvcc >>"$tmp/nvcc_paths" 2>/dev/null
fi
for pattern in /usr/local/cuda*/bin/nvcc /usr/lib/cuda*/bin/nvcc; do
  for path in $pattern; do
    [[ -x $path ]] && printf '%s\n' "$path" >>"$tmp/nvcc_paths"
  done
done
# Deduplicate while preserving order.
nvcc_json=$(python3 -c '
import json, os, subprocess, sys
paths = []
seen = set()
for line in open(sys.argv[1]):
    p = line.strip()
    if not p or p in seen:
        continue
    seen.add(p)
    paths.append(p)
out = []
for p in paths:
    version = None
    try:
        r = subprocess.run([p, "--version"], capture_output=True, text=True, timeout=30)
        text = (r.stdout or "") + (r.stderr or "")
        version = text.strip() or None
    except Exception:
        version = None
    out.append({"path": p, "version": version})
print(json.dumps(out))
' "$tmp/nvcc_paths" 2>/dev/null) || nvcc_json='[]'

# --- toolchain helpers ---
tool_json() {
  local name=$1
  local bin path version
  path=
  version=
  if command -v "$name" >/dev/null 2>&1; then
    path=$(command -v "$name" 2>/dev/null) || path=
    case $name in
      python3) version=$("$path" --version 2>&1 | head -n1) || version= ;;
      pip) version=$("$path" --version 2>&1 | head -n1) || version= ;;
      g++) version=$("$path" --version 2>&1 | head -n1) || version= ;;
      *) version=$("$path" --version 2>&1 | head -n1) || version= ;;
    esac
  fi
  PATH_VAL="$path" VER_VAL="$version" python3 -c '
import json, os
p = os.environ.get("PATH_VAL") or None
v = os.environ.get("VER_VAL") or None
print(json.dumps(None if not p else {"path": p, "version": v}))
' 2>/dev/null || printf 'null'
}

cmake_j=$(tool_json cmake)
gcc_j=$(tool_json gcc)
gxx_j=$(tool_json 'g++')
make_j=$(tool_json make)
git_j=$(tool_json git)
python3_j=$(tool_json python3)
pip_name=
command -v pip >/dev/null 2>&1 && pip_name=pip
[[ -z $pip_name ]] && command -v pip3 >/dev/null 2>&1 && pip_name=pip3
pip_j='null'
[[ -n $pip_name ]] && pip_j=$(tool_json "$pip_name")

# --- apt sources mentioning cuda or nvidia ---
apt_json='[]'
{
  [[ -f /etc/apt/sources.list ]] && printf '%s\n' /etc/apt/sources.list
  shopt -s nullglob
  for f in /etc/apt/sources.list.d/*; do printf '%s\n' "$f"; done
  shopt -u nullglob
} >"$tmp/apt_files"
apt_json=$(python3 -c '
import json, re, sys
pat = re.compile(r"cuda|nvidia", re.I)
out = []
for path in open(sys.argv[1]):
    path = path.strip()
    if not path:
        continue
    try:
        lines = open(path, errors="replace").read().splitlines()
    except OSError:
        continue
    matched = [line for line in lines if pat.search(line) and not line.lstrip().startswith("#")]
    # Keep commented repo lines that still name the vendor; agents need available sources.
    if not matched:
        matched = [line for line in lines if pat.search(line)]
    if matched:
        out.append({"file": path, "lines": matched})
print(json.dumps(out))
' "$tmp/apt_files" 2>/dev/null) || apt_json='[]'

# --- sudo -n ---
sudo_ok=false
if command -v sudo >/dev/null 2>&1; then
  if sudo -n true >/dev/null 2>&1; then
    sudo_ok=true
  fi
fi

# Assemble probe.json
OS_JSON="$os_json" KERNEL="${kernel-}" NPROC="${nproc_n-}" MEM="${memory_kb-}" DISK="${disk_home_bytes-}" \
NVIDIA_JSON="$nvidia_json" NVCC_JSON="$nvcc_json" \
CMAKE_J="$cmake_j" GCC_J="$gcc_j" GXX_J="$gxx_j" MAKE_J="$make_j" GIT_J="$git_j" \
PY_J="$python3_j" PIP_J="$pip_j" APT_JSON="$apt_json" SUDO_OK="$sudo_ok" \
python3 -c '
import json, os, sys

def parse(name, default):
    raw = os.environ.get(name, "")
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        return default

def int_or_none(name):
    raw = os.environ.get(name, "")
    if not raw:
        return None
    try:
        return int(raw)
    except Exception:
        return None

probe = {
    "os": parse("OS_JSON", None),
    "kernel": os.environ.get("KERNEL") or None,
    "nproc": int_or_none("NPROC"),
    "memory_kb": int_or_none("MEM"),
    "disk_home_avail_bytes": int_or_none("DISK"),
    "nvidia": parse("NVIDIA_JSON", None),
    "nvcc": parse("NVCC_JSON", []),
    "cmake": parse("CMAKE_J", None),
    "gcc": parse("GCC_J", None),
    "g++": parse("GXX_J", None),
    "make": parse("MAKE_J", None),
    "git": parse("GIT_J", None),
    "python3": parse("PY_J", None),
    "pip": parse("PIP_J", None),
    "apt_sources": parse("APT_JSON", []),
    "sudo_nopasswd": os.environ.get("SUDO_OK") == "true",
}
path = "out/probe.json"
with open(path + ".tmp", "w") as f:
    json.dump(probe, f, indent=2, sort_keys=True)
    f.write("\n")
os.replace(path + ".tmp", path)
' || exit 1

exit 0
