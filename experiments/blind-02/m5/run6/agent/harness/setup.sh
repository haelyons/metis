#!/usr/bin/env bash
# setup.sh - build and check the published MEGADOCK baseline (commit 9575280c) and
# prepare the four PINDER 2024-02 apo cases for the timing-only calibration (s04).
# Invoked from the shared working directory as: bash harness/setup.sh
# Scope: build + checks of the published baseline only. No profiling tools, no
# workload runs, no CUDA_MPS_* handling (inherited unchanged).
set -euo pipefail

if [[ ! -f harness/setup.sh ]]; then
    echo "setup.sh: must be invoked from the working directory as 'bash harness/setup.sh'" >&2
    exit 2
fi
WORK=$(pwd)
mkdir -p out/setup baseline-published data/sources/pdbs data/inputs data/prepared
SLOG=out/setup/setup.log
if [[ -f "$SLOG" ]]; then
    mv "$SLOG" "out/setup/setup.$(date -u +%Y%m%dT%H%M%SZ).prev.log"
fi
exec > >(tee -a "$SLOG") 2>&1
SETUP_T0=$(date +%s.%N)
echo "== setup start $(date -u +%FT%TZ) in $WORK"

MEGADOCK_REPO=https://github.com/akiyamalab/MEGADOCK
MEGADOCK_COMMIT=9575280c875732553266e26adc607dd892b02616
SAMPLES_REPO=https://github.com/NVIDIA/cuda-samples
SAMPLES_TAG=v12.8
MD=baseline-published/megadock
SAMPLES_DIR=baseline-published/cuda-samples

fail() { echo "SETUP FAILED: $*" >&2; exit 1; }

# ---------------------------------------------------------------- tools / apt
APT_UPDATED=0
INSTALLED_PKGS=()
apt_install() {
    local pkg=$1
    if [[ $APT_UPDATED == 0 ]]; then
        sudo apt-get update
        APT_UPDATED=1
    fi
    local cand
    cand=$(apt-cache policy "$pkg" | awk '/Candidate:/ {print $2}')
    if [[ -z "$cand" || "$cand" == "(none)" ]]; then
        fail "package $pkg is required by the published build but has no install candidate in the enabled apt sources"
    fi
    echo "installing $pkg (candidate $cand)"
    sudo apt-get install -y "$pkg"
    echo "INSTALLED: $(dpkg-query -W "$pkg")"
    INSTALLED_PKGS+=("$(dpkg-query -W -f='${Package}=${Version}' "$pkg")")
}

for tool in git make /usr/bin/g++ python3 sha256sum ldd nvidia-smi; do
    command -v "$tool" >/dev/null 2>&1 || fail "required tool $tool not found in the stock image"
done
echo "git: $(git --version)"; echo "make: $(make --version | head -1)"; echo "g++: $(/usr/bin/g++ --version | head -1)"

# FFTW single precision (published Makefile links -lfftw3f)
if ! ls -l /usr/include/fftw3.h /usr/lib/x86_64-linux-gnu/libfftw3f.so; then
    echo "FFTW3 single-precision development files missing; installing libfftw3-dev via apt"
    apt_install libfftw3-dev
    ls -l /usr/include/fftw3.h /usr/lib/x86_64-linux-gnu/libfftw3f.so \
        || fail "libfftw3-dev installed but /usr/include/fftw3.h or libfftw3f.so still missing"
fi
dpkg-query -W libfftw3-dev 2>/dev/null || true

# ---------------------------------------------------------------- CUDA selection
# Prefer a complete toolkit root (bin/nvcc, include/cuda_runtime.h, lib64/libcudart.so)
# among the roots the probe found; else the complete distro layout.
CUDA_LAYOUT=""; CUDA_ROOT=""; CUDA_NVCC=""; CUDA_INCLUDE=""; CUDA_LIB=""
for root in /usr/local/cuda /usr/lib/cuda; do
    if ls -l "$root/bin/nvcc" "$root/include/cuda_runtime.h" "$root/lib64/libcudart.so" 2>/dev/null; then
        CUDA_LAYOUT=root; CUDA_ROOT=$root
        CUDA_NVCC=$root/bin/nvcc; CUDA_INCLUDE=$root/include; CUDA_LIB=$root/lib64
        break
    fi
done
if [[ -z "$CUDA_LAYOUT" ]]; then
    if ls -l /usr/bin/nvcc /usr/include/cuda_runtime.h /usr/lib/x86_64-linux-gnu/libcudart.so; then
        CUDA_LAYOUT=distro
        CUDA_NVCC=/usr/bin/nvcc; CUDA_INCLUDE=/usr/include; CUDA_LIB=/usr/lib/x86_64-linux-gnu
    else
        fail "no complete CUDA toolkit root (/usr/local/cuda, /usr/lib/cuda) and no complete distro layout (/usr/bin/nvcc, /usr/include/cuda_runtime.h, /usr/lib/x86_64-linux-gnu/libcudart.so)"
    fi
fi
if [[ "$CUDA_LAYOUT" == root ]]; then
    export PATH="$CUDA_ROOT/bin:$PATH"
    export CUDAToolkit_ROOT="$CUDA_ROOT"
fi
ls -l "$CUDA_NVCC" "$CUDA_INCLUDE/cuda_runtime.h" "$CUDA_LIB/libcudart.so"
ls -l "$CUDA_LIB"/libcufft.so || fail "libcufft.so not found in selected CUDA library dir $CUDA_LIB"
ls -l "$CUDA_INCLUDE/cufft.h" || fail "cufft.h not found in selected CUDA include dir $CUDA_INCLUDE"
echo "CUDA layout=$CUDA_LAYOUT root=${CUDA_ROOT:-none} nvcc=$CUDA_NVCC include=$CUDA_INCLUDE lib=$CUDA_LIB"
"$CUDA_NVCC" --version
cat > out/setup/cuda_layout.env <<EOF
CUDA_LAYOUT=$CUDA_LAYOUT
CUDA_ROOT=$CUDA_ROOT
CUDA_NVCC=$CUDA_NVCC
CUDA_INCLUDE=$CUDA_INCLUDE
CUDA_LIB=$CUDA_LIB
EOF

# ---------------------------------------------------------------- sources
BUILD_MARK="$MD/.harness_build_complete"
if [[ -d "$MD/.git" ]] && [[ "$(git -C "$MD" rev-parse HEAD 2>/dev/null)" == "$MEGADOCK_COMMIT" ]] \
   && [[ -f "$BUILD_MARK" ]] && [[ -x "$MD/megadock" && -x "$MD/megadock-gpu" && -x "$MD/decoygen" ]] \
   && git -C "$MD" diff --quiet HEAD; then
    echo "MEGADOCK checkout at $MEGADOCK_COMMIT already built (retry); reusing"
    NEED_BUILD=0
else
    echo "fresh MEGADOCK checkout"
    rm -rf "$MD"
    git clone "$MEGADOCK_REPO" "$MD"
    git -C "$MD" checkout "$MEGADOCK_COMMIT"
    NEED_BUILD=1
fi
[[ "$(git -C "$MD" rev-parse HEAD)" == "$MEGADOCK_COMMIT" ]] || fail "MEGADOCK HEAD is not $MEGADOCK_COMMIT"

if [[ -d "$SAMPLES_DIR/.git" ]] && [[ "$(git -C "$SAMPLES_DIR" describe --tags --exact-match 2>/dev/null)" == "$SAMPLES_TAG" ]]; then
    echo "cuda-samples $SAMPLES_TAG present"
else
    rm -rf "$SAMPLES_DIR"
    git clone --depth 1 --branch "$SAMPLES_TAG" "$SAMPLES_REPO" "$SAMPLES_DIR"
fi
git -C "$SAMPLES_DIR" describe --tags --exact-match
[[ "$(git -C "$SAMPLES_DIR" describe --tags --exact-match)" == "$SAMPLES_TAG" ]] || fail "cuda-samples is not at $SAMPLES_TAG"
samples=$WORK/$SAMPLES_DIR
ls -l "$samples/Common/helper_cuda.h"

# ---------------------------------------------------------------- build (published Makefile, make variables only)
if [[ $NEED_BUILD == 1 ]]; then
    B0=$(date +%s.%N)
    make -C "$MD" -j 8 USE_GPU=0 USE_MPI=0 \
        CPPCOMPILER=/usr/bin/g++ FFTW_INSTALL_PATH=/usr \
        FFTW_CFLAGS=-I/usr/include FFTW_LDFLAGS='-lm -L/usr/lib/x86_64-linux-gnu -lfftw3f' \
        2>&1 | tee out/setup/build_cpu.log
    B1=$(date +%s.%N)
    make -C "$MD" -j 8 USE_GPU=1 USE_MPI=0 \
        CPPCOMPILER=/usr/bin/g++ SM_VERSIONS=sm_90 \
        "NVCC=$CUDA_NVCC -Xcompiler -fopenmp -arch=sm_90 -use_fast_math" \
        "INCLUDES=-Isrc -I$CUDA_INCLUDE -I$samples/Common" \
        FFTW_CFLAGS=-I/usr/include \
        "LIB=-lm -L/usr/lib/x86_64-linux-gnu -lfftw3f -L$CUDA_LIB -Wl,-rpath,$CUDA_LIB -lcudart -lcufft" \
        2>&1 | tee out/setup/build_gpu.log
    B2=$(date +%s.%N)
    python3 -I -c "import sys; print('build walls cpu=%.3f gpu=%.3f' % (float(sys.argv[2])-float(sys.argv[1]), float(sys.argv[3])-float(sys.argv[2])))" "$B0" "$B1" "$B2" | tee out/setup/build_walls.txt
fi
for binary in megadock megadock-gpu decoygen; do
    test -x "$MD/$binary" || fail "$MD/$binary was not built"
    ldd "$MD/$binary" | tee "out/setup/$binary-ldd.log"
    if grep -q 'not found' "out/setup/$binary-ldd.log"; then fail "$binary has unresolved shared libraries"; fi
done
grep -q libcudart "out/setup/megadock-gpu-ldd.log" || fail "megadock-gpu is not linked against libcudart"
grep -q libcufft "out/setup/megadock-gpu-ldd.log" || fail "megadock-gpu is not linked against libcufft"
git -C "$MD" status --porcelain --untracked-files=no | tee out/setup/megadock_tracked_changes.txt
[[ ! -s out/setup/megadock_tracked_changes.txt ]] || fail "published MEGADOCK tracked sources were modified"
touch "$BUILD_MARK"

# Help exits 255 in this published release; require the actual usage text.
for binary in megadock megadock-gpu; do
    rc=0
    OMP_NUM_THREADS=26 CUDA_VISIBLE_DEVICES=0 "$MD/$binary" -h > "out/setup/$binary-help.log" 2>&1 || rc=$?
    echo "$binary -h exit status $rc"
    [[ "$rc" == 0 || "$rc" == 255 ]] || fail "$binary -h exited $rc"
    grep -q 'Usage: megadock' "out/setup/$binary-help.log" || fail "$binary -h did not print 'Usage: megadock'"
done

# ---------------------------------------------------------------- data (download, verify, prepare)
python3 -I - <<'PY'
import hashlib, json, os, shutil, sys, urllib.request

BASE = "https://pinderdata.org/2024-02/pdbs/"
SOURCES = {
    "6f0e__A1_P24280.pdb": (192456, "622eacb7b46e1a4c25d16aa1c56a0546d1b23d31a41aad5c275886159f6d98cd"),
    "3n35__A1_P16404.pdb": (151794, "b39b7288e39983302280e4f83a69a3afbeee879fe2c0db13a8072c5c0e06090e"),
    "3g8c__A1_P24182.pdb": (277182, "48aa5f4b2ac1e57d855b85d56a9c4a74c4b16f7d165b0fce03535815e26bdb60"),
    "3g8d__A1_P24182.pdb": (234657, "1f5320894a6ca42ffd58a164620e159cc6d95d21f978246b3f73f7620885f20c"),
    "1sg6__A1_P07547.pdb": (234171, "4a7227a5777521835f4dcb9af450bf5f8be13ebbe10144ab4fdfa7eeb7900da5"),
}
CASES = [
    ("1aua", "1aua__A1_P24280--1aua__A2_P24280", "6f0e__A1_P24280.pdb", "6f0e__A1_P24280.pdb"),
    ("1ax2", "1ax2__A1_P16404--1ax2__A2_P16404", "3n35__A1_P16404.pdb", "3n35__A1_P16404.pdb"),
    ("1dv1", "1dv1__A1_P24182--1dv1__B1_P24182", "3g8c__A1_P24182.pdb", "3g8d__A1_P24182.pdb"),
    ("1nr5", "1nr5__A1_P07547--1nr5__A2_P07547", "1sg6__A1_P07547.pdb", "1sg6__A1_P07547.pdb"),
]
EXPECTED = {
    "1aua": {"receptor": "162aad227fdbdb6a0600a5b6a4f5b461663ee7ce419798061ea0cd8ae9be6f35", "ligand": "f5158ee7030ce712cc5fb419d1e7532d4db2d4b4ddb64b50a5d0d9e45a973600"},
    "1ax2": {"receptor": "a9be54841e5e92e301558c198a7188b6765ab34cf30cb5d939b46f99db103d35", "ligand": "8d3948ddc69f493dfeea785aefc09f3de7b191ab7f8250dc102f63dc1d35810e"},
    "1dv1": {"receptor": "880a12d8a36e84fc8bea31cb4105284827ce1a985128413e4e8f70582fe52ea2", "ligand": "f9c72e23a1f2afe893c672da0412e82fa8345be23902d1d5cc7c17971193f623"},
    "1nr5": {"receptor": "ec52d962eacf8e92518ead142a51f6feb18e8d74590ea7048fffc461f52cacf2", "ligand": "83ad5cf3938c63172fea2254e31e6fe05d5751d072323ff7ed3463d92af0d1a2"},
}

def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()

src_ok = {}
for name, (nbytes, digest) in SOURCES.items():
    dst = os.path.join("data/sources/pdbs", name)
    if not (os.path.isfile(dst) and sha(dst) == digest):
        tmp = dst + ".part"
        print("downloading", BASE + name, flush=True)
        req = urllib.request.Request(BASE + name, headers={"User-Agent": "megadock-calibration-harness"})
        with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as fh:
            shutil.copyfileobj(r, fh)
        os.replace(tmp, dst)
    got, size = sha(dst), os.path.getsize(dst)
    print(f"source {name} bytes={size} sha256={got}")
    if got != digest or size != nbytes:
        sys.exit(f"SETUP FAILED: source {name} hash/size mismatch (got {size} {got}, expected {nbytes} {digest})")
    src_ok[name] = got

def relabel(src_bytes, chain):
    out = []
    for line in src_bytes.splitlines(keepends=True):
        rec = line[:6].rstrip()
        if rec in (b"ATOM", b"HETATM", b"ANISOU", b"TER"):
            body = line.rstrip(b"\r\n")
            if len(body) >= 22:
                line = line[:21] + chain + line[22:]
        out.append(line)
    return b"".join(out)

prepared = {}
ok = True
for prefix, system, rsrc, lsrc in CASES:
    d = os.path.join("data/prepared", system, "inputs", "apo")
    os.makedirs(d, exist_ok=True)
    prepared[prefix] = {}
    for role, src, chain, tag in (("receptor", rsrc, b"R", "R"), ("ligand", lsrc, b"L", "L")):
        with open(os.path.join("data/sources/pdbs", src), "rb") as fh:
            data = relabel(fh.read(), chain)
        full = os.path.join(d, f"{prefix}_apo_{tag}.pdb")
        with open(full, "wb") as fh:
            fh.write(data)
        alias = os.path.join("data/inputs", f"{prefix}_{tag}.pdb")
        shutil.copyfile(full, alias)
        h_full, h_alias = sha(full), sha(alias)
        good = h_full == h_alias == EXPECTED[prefix][role]
        ok = ok and good
        prepared[prefix][role] = {"path": alias, "sha256": h_alias, "expected": EXPECTED[prefix][role], "valid": good}
        print(f"prepared {alias} sha256={h_alias} expected={EXPECTED[prefix][role]} {'OK' if good else 'MISMATCH'}")
with open("out/setup/prepared_inputs.json", "w") as fh:
    json.dump({"sources": src_ok, "prepared": prepared, "prepared_hashes_valid": ok}, fh, indent=2)
if not ok:
    sys.exit("SETUP FAILED: prepared input hash mismatch; the run must stop")
PY

# ---------------------------------------------------------------- record identity
SETUP_T1=$(date +%s.%N)
nvidia-smi --query-gpu=index,name,uuid,driver_version,memory.total --format=csv > out/setup/gpu_identity.csv
lscpu > out/setup/lscpu.txt
free -b > out/setup/free.txt
INSTALLED_JSON=$(printf '%s\n' "${INSTALLED_PKGS[@]+"${INSTALLED_PKGS[@]}"}" | python3 -I -c "import json,sys; print(json.dumps([l for l in sys.stdin.read().split('\n') if l]))")
python3 -I - "$SETUP_T0" "$SETUP_T1" "$INSTALLED_JSON" <<'PY'
import hashlib, json, os, platform, subprocess, sys

def sh(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=False).stdout.strip()
    except OSError as e:
        return f"unavailable: {e}"

def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()

env = dict(l.split("=", 1) for l in open("out/setup/cuda_layout.env").read().splitlines() if "=" in l)
md = "baseline-published/megadock"
prep = json.load(open("out/setup/prepared_inputs.json"))
gpu_rows = [l for l in open("out/setup/gpu_identity.csv").read().splitlines()[1:] if l.strip()]
mem_kb = None
for l in open("/proc/meminfo"):
    if l.startswith("MemTotal:"):
        mem_kb = int(l.split()[1])
rec = {
    "pins": {
        "megadock_repo": "https://github.com/akiyamalab/MEGADOCK",
        "megadock_commit": sh(["git", "-C", md, "rev-parse", "HEAD"]),
        "megadock_commit_expected": "9575280c875732553266e26adc607dd892b02616",
        "cuda_samples_tag": sh(["git", "-C", "baseline-published/cuda-samples", "describe", "--tags", "--exact-match"]),
        "pinder_release": "2024-02",
        "pinder_source_commit": "ebeb28a2f8411363cef722b7d293c978f7442672",
    },
    "binary_sha256": {b: sha(os.path.join(md, b)) for b in ("megadock", "megadock-gpu", "decoygen")},
    "cuda": env,
    "versions": {
        "nvcc": sh([env["CUDA_NVCC"], "--version"]),
        "gxx": sh(["/usr/bin/g++", "--version"]).splitlines()[0],
        "driver": gpu_rows[0].split(",")[3].strip() if gpu_rows else None,
        "fftw": sh(["dpkg-query", "-W", "libfftw3-dev"]),
        "python": platform.python_version(),
    },
    "apt_installed": json.loads(sys.argv[3]),
    "host": {
        "gpus_csv": gpu_rows,
        "cpu_model": next((l.split(":", 1)[1].strip() for l in open("out/setup/lscpu.txt") if l.startswith("Model name")), None),
        "nproc": os.cpu_count(),
        "affinity": sorted(os.sched_getaffinity(0)),
        "mem_total_kb": mem_kb,
        "kernel": platform.release(),
    },
    "setup_checks": {
        "megadock_commit_valid": sh(["git", "-C", md, "rev-parse", "HEAD"]) == "9575280c875732553266e26adc607dd892b02616",
        "cuda_samples_tag_valid": sh(["git", "-C", "baseline-published/cuda-samples", "describe", "--tags", "--exact-match"]) == "v12.8",
        "help_usage_valid": {b: "Usage: megadock" in open(f"out/setup/{b}-help.log", errors="replace").read() for b in ("megadock", "megadock-gpu")},
        "prepared_hashes_valid": prep["prepared_hashes_valid"],
        "source_hashes": prep["sources"],
        "prepared": prep["prepared"],
    },
    "stage_walls_s": {"setup": float(sys.argv[2]) - float(sys.argv[1])},
}
for path in ("out/setup/setup_record.json", "data/setup_record.json"):
    with open(path, "w") as fh:
        json.dump(rec, fh, indent=2)
print(json.dumps(rec["setup_checks"]["help_usage_valid"]), json.dumps(rec["binary_sha256"], indent=1))
PY
echo "== setup complete $(date -u +%FT%TZ)"
