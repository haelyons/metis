#!/usr/bin/env bash
# On-box batch for the throughput measurement (tag m3). It runs on the rented GPU box, inside the
# launcher's REMOTE_TIMEOUT window, through the bootstrap:   bash remote_run_m3.sh bash onbox_m3.sh
#
# WHAT IT DOES, IN THE ORDER THE EXECUTION NOTE SETS (EXEC_NOTE.md, checklist item 13)
#   1. download and compile the engine (checklist item 11; gate addendum A7). No micromamba, no conda.
#      - Downloads the official LAMMPS source tarball stable_29Aug2024 from GitHub (the LAMMPS mirror if
#        that fails), records its sha256 and size, and unpacks it under engine_src/.
#      - cmake comes from the image if `command -v cmake` finds it; else `python3 -m pip install --user
#        cmake`, the one allowed install. Which one is recorded.
#      - FFT library: FFTW3 if /usr/include/fftw3.h exists, else LAMMPS's built-in KISS FFT.
#      - Configures with the note's cmake command (GPU package for CUDA, sm_80; KSPACE, MOLECULE, RIGID,
#        EXTRA-COMPUTE, OPENMP; no MPI), builds with every processor, installs into engine/.
#      - This stage has its own guard and a 1,800 s cap (gate addendum A8). Every step, its exit code
#        and its date stamps go to results_m3/out/compile_record.txt; each step's log sits beside it.
#   2. lmp -h and GPU check (run_m3.py extract): GPU, KSPACE, MOLECULE, RIGID and EXTRA-COMPUTE must
#      all be listed, else the run is void and stops with code 2.
#   3. timed dry run   4. copy of the box   5. equilibration   6-8. runs a, b, c   9. endpoints.
#   A cost and time guard runs before every stage: `run_m3.py guard` here, and inside each stage.
#   Step 5 (checklist item 3b): if the committed equilibrate.in stops with an error naming comm_style,
#   balance, tiled or rcb, run_m3.py deletes exactly those three lines in a copy
#   (results_m3/decks/equilibrate_noballance.in), records the error line and the diff, and runs the
#   equilibration once more from the copy, after a fresh guard. Any other error stops the run (code 12).
#
# WHAT MUST SIT BESIDE THIS SCRIPT: run_m3.py, frozen/provenance.py and data/ (the launcher ships them).
# RESULTS: results_m3/out/ (records, logs, raw rows, RUN_VALID.json, m3_summary.json, RUN_DONE).
# The engine is ./engine; its source and build folder ./engine_src; the writable box copy is
# results_m3/system/; restart files stay on the box.
#
# ENVIRONMENT: PRICE_USD_PER_HOUR, BUDGET_LEFT_USD and INSTANCE_TYPE (forwarded by the launcher);
# REMOTE_TIMEOUT (7200 s unless set; gate addendum A8). The run stops cleanly before projected spend
# reaches BUDGET_LEFT_USD and before REMOTE_TIMEOUT, cutting run c first, then run b.
#
# After a nonzero code, m3_summary.json labels every finished run "incomplete run: descriptive only,
# no verdict". After a failed compile it also restates the last 40 lines of the failing step's log.
# EXIT CODES (also written to results_m3/out/RUN_DONE)
#   0 finished   2 compile failed or a required package missing   3 stopped by the cost or time guard
#   4 pre-launch build gate failed   10 dry run  11 box copy  12 equilibration  13 run a  14 run b
#   15 run c   16 endpoints   17 extract   1 any other failure
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE" || exit 1
OUT="$HERE/results_m3/out"
mkdir -p "$OUT"
rm -f "$OUT/RUN_DONE"
exec > >(tee -a "$OUT/onbox_m3.log") 2>&1

# This process was started by the launcher's `timeout` (remote_run_m3.sh execs this script in the same
# process); run_m3.py reads its start time from /proc to know how much of the REMOTE_TIMEOUT window is left.
export M3_WINDOW_PID=$$
export REMOTE_TIMEOUT="${REMOTE_TIMEOUT:-7200}"
export PYTHONUNBUFFERED=1   # live progress lines for the launcher's poll
PY=python3
RUNNER="$HERE/run_m3.py"
FINISHED=0

stamp() { echo "[$1] $(date -u +%FT%TZ) uptime $(cut -d' ' -f1 /proc/uptime) s"; }

finish() {   # finish <code> <reason...>: summary, then the RUN_DONE marker, then exit
  local rc=$1; shift
  if [ "$rc" != 0 ]; then "$PY" "$RUNNER" void --reason "the run stopped with code $rc: $*" || true; fi
  "$PY" "$RUNNER" summary --exit-code "$rc" --note "$*" || echo "[finish] the summary could not be written"
  printf '%s\n' "$rc" > "$OUT/RUN_DONE"
  FINISHED=1
  echo "[finish] code $rc: $* ($(date -u +%FT%TZ))"
  exit "$rc"
}

on_exit() {
  local rc=$?
  if [ "$FINISHED" != 1 ]; then
    [ "$rc" = 0 ] && rc=1
    "$PY" "$RUNNER" void --reason "the on-box script ended without finishing (code $rc)" || true
    "$PY" "$RUNNER" summary --exit-code "$rc" --note "ended without finishing" || true
    printf '%s\n' "$rc" > "$OUT/RUN_DONE"
    echo "[finish] code $rc: ended without finishing"
  fi
}
trap on_exit EXIT
trap 'echo "[signal] stopped by a signal"; exit 143' TERM INT HUP

[ -f "$RUNNER" ] || finish 1 "run_m3.py is not beside this script"
[ -f "$HERE/frozen/provenance.py" ] || finish 1 "frozen/provenance.py is not beside this script"
[ -d "$HERE/data" ] || finish 1 "data/ is not beside this script"

# ---- 1. download and compile the engine ------------------------------------------------------
stamp "compile: guard"
GUARD_TXT="$("$PY" "$RUNNER" guard --stage compile)"
rc=$?
echo "$GUARD_TXT"
[ "$rc" = 0 ] || finish "$rc" "the cost or time guard stopped the run before the compile"
ALLOW=$(printf '%s\n' "$GUARD_TXT" | sed -n 's/^allowed_seconds=\([0-9][0-9]*\)$/\1/p' | tail -1)
[ -n "$ALLOW" ] || finish 1 "the guard printed no allowed time for the compile"
[ "$ALLOW" -le 1800 ] || ALLOW=1800          # the compile stage's own cap (run_m3.py applies it too)
DEADLINE=$(( $(date +%s) + ALLOW ))
left() { echo $(( DEADLINE - $(date +%s) )); }

URL_MAIN="https://github.com/lammps/lammps/archive/refs/tags/stable_29Aug2024.tar.gz"
URL_MIRROR="https://download.lammps.org/tars/lammps-29Aug2024.tar.gz"
SRC_ROOT="$HERE/engine_src"
BUILD="$SRC_ROOT/build"
ENGINE="$HERE/engine"
TARBALL="$SRC_ROOT/lammps-stable_29Aug2024.tar.gz"
CREC="$OUT/compile_record.txt"
TC="$OUT/toolchain_versions.txt"
: > "$CREC"
: > "$TC"
kv() { printf '%s=%s\n' "$1" "$2" >> "$CREC"; }
compile_fail() {   # compile_fail <reason> [<log file name under results_m3/out/>]
  kv end_epoch "$(date +%s.%N)"
  kv compile_ok 0
  kv failure "$1"
  kv failure_log "${2:-}"
  "$PY" "$RUNNER" void --reason "the engine compile failed: $1"
  finish 2 "the engine compile failed: $1"
}
step_fail() {      # step_fail <step> <exit code> <log>: a step's nonzero exit, naming the time limit if hit
  local why="$1 exited $2"
  [ "$2" = 124 ] && why="$1 reached the compile stage's time limit (exit 124)"
  compile_fail "$why" "$3"
}

stamp "compile: start (allowed ${ALLOW} s)"
kv start_epoch "$(date +%s.%N)"
kv allowed_seconds "$ALLOW"
kv cap_seconds 1800

# Toolchain from the image (gate addendum A7): nvcc, g++, make; their versions are recorded.
nvidia-smi > "$OUT/nvidia_smi.txt" 2>&1 || echo "[compile] nvidia-smi exited nonzero"
nvidia-smi --query-gpu=name,driver_version --format=csv,noheader > "$OUT/nvidia_smi_query.txt" 2>&1 || true
NVCC="$(command -v nvcc || true)"
[ -n "$NVCC" ] || { [ -x /usr/bin/nvcc ] && NVCC=/usr/bin/nvcc; }
kv nvcc_path "${NVCC:-not found}"
command -v g++ > /dev/null || compile_fail "g++ is not on the image"
command -v make > /dev/null || compile_fail "make is not on the image"
[ -n "$NVCC" ] || compile_fail "nvcc is not on the image"
{ echo "## g++ --version"; g++ --version; echo "## nvcc --version"; "$NVCC" --version
  echo "## make --version"; make --version | head -1; } >> "$TC" 2>&1
kv gxx_version "$(g++ --version 2>/dev/null | head -1)"
kv nvcc_version "$("$NVCC" --version 2>/dev/null | grep -i 'release' | head -1)"
kv make_version "$(make --version 2>/dev/null | head -1)"

# cmake: from the image if present, else the one allowed install.
CMAKE="$(command -v cmake || true)"
if [ -n "$CMAKE" ]; then
  kv cmake_source image
else
  kv cmake_source "pip_user (python3 -m pip install --user cmake)"
  L=$(left); [ "$L" -gt 0 ] || compile_fail "no time left to install cmake"
  kv cmake_pip_start_epoch "$(date +%s.%N)"
  timeout "$L" python3 -m pip install --user cmake > "$OUT/cmake_pip.log" 2>&1
  RC=$?
  kv cmake_pip_end_epoch "$(date +%s.%N)"
  kv cmake_pip_exit "$RC"
  [ "$RC" = 0 ] || step_fail "python3 -m pip install --user cmake" "$RC" cmake_pip.log
  CMAKE="$(python3 -m site --user-base)/bin/cmake"
  [ -x "$CMAKE" ] || compile_fail "no cmake binary after the pip install" cmake_pip.log
fi
kv cmake_path "$CMAKE"
kv cmake_version "$("$CMAKE" --version 2>/dev/null | head -1)"
{ echo "## cmake --version"; "$CMAKE" --version; } >> "$TC" 2>&1

# The source tarball: GitHub first, the LAMMPS mirror on failure; sha256 and size recorded.
rm -rf "${SRC_ROOT:?}" "${ENGINE:?}"
mkdir -p "$SRC_ROOT"
kv url_primary "$URL_MAIN"
kv url_mirror "$URL_MIRROR"
kv download_start_epoch "$(date +%s.%N)"
URL_USED=""
L=$(left)
if [ "$L" -gt 0 ] && timeout "$L" curl -fsSL --retry 5 -o "$TARBALL" "$URL_MAIN" >> "$OUT/download.log" 2>&1; then
  URL_USED="$URL_MAIN"
else
  kv primary_download_exit "$?"
  rm -f "$TARBALL"
  L=$(left)
  if [ "$L" -gt 0 ] && timeout "$L" curl -fsSL --retry 5 -o "$TARBALL" "$URL_MIRROR" >> "$OUT/download.log" 2>&1; then
    URL_USED="$URL_MIRROR"
  else
    compile_fail "neither the source tarball nor its mirror downloaded" download.log
  fi
fi
kv download_end_epoch "$(date +%s.%N)"
kv url_used "$URL_USED"
kv tarball_sha256 "$(sha256sum "$TARBALL" | cut -d' ' -f1)"
kv tarball_bytes "$(stat -c %s "$TARBALL")"

kv unpack_start_epoch "$(date +%s.%N)"
L=$(left); [ "$L" -gt 0 ] || compile_fail "no time left to unpack the source tarball"
timeout "$L" tar -xzf "$TARBALL" -C "$SRC_ROOT" >> "$OUT/download.log" 2>&1 \
  || compile_fail "could not unpack the source tarball" download.log
kv unpack_end_epoch "$(date +%s.%N)"
SRC="$(find "$SRC_ROOT" -mindepth 1 -maxdepth 1 -type d -name 'lammps-*' | head -1)"
{ [ -n "$SRC" ] && [ -f "$SRC/cmake/CMakeLists.txt" ]; } || compile_fail "the unpacked source has no cmake/CMakeLists.txt" download.log
kv src_dir "$SRC"
kv src_version_h "$(grep -m1 'LAMMPS_VERSION' "$SRC/src/version.h" 2>/dev/null)"

# FFT library, then the note's cmake command (EXEC_NOTE.md item 11), recorded verbatim.
if [ -f /usr/include/fftw3.h ]; then FFT=FFTW3; else FFT=KISS; fi
kv fft "$FFT"
kv fftw3_header "$([ -f /usr/include/fftw3.h ] && echo present || echo absent)"
CMAKE_ARGS=(-S "$SRC/cmake" -B "$BUILD" -D CMAKE_BUILD_TYPE=Release -D BUILD_MPI=no -D BUILD_OMP=yes
            -D PKG_KSPACE=on -D PKG_MOLECULE=on -D PKG_RIGID=on -D PKG_EXTRA-COMPUTE=on -D PKG_OPENMP=on
            -D PKG_GPU=on -D GPU_API=cuda -D GPU_ARCH=sm_80 -D FFT="$FFT" -D CMAKE_INSTALL_PREFIX="$ENGINE")
kv cmake_command "$CMAKE ${CMAKE_ARGS[*]}"
stamp "compile: configure"
kv configure_start_epoch "$(date +%s.%N)"
L=$(left); [ "$L" -gt 0 ] || compile_fail "no time left to configure"
timeout "$L" "$CMAKE" "${CMAKE_ARGS[@]}" > "$OUT/cmake_configure.log" 2>&1
RC=$?
kv configure_end_epoch "$(date +%s.%N)"
kv configure_exit "$RC"
[ "$RC" = 0 ] || step_fail "cmake configure" "$RC" cmake_configure.log

JOBS="$(nproc)"
kv build_jobs "$JOBS"
kv build_command "$CMAKE --build $BUILD -j $JOBS"
stamp "compile: build with $JOBS jobs"
kv build_start_epoch "$(date +%s.%N)"
L=$(left); [ "$L" -gt 0 ] || compile_fail "no time left to build"
timeout "$L" "$CMAKE" --build "$BUILD" -j "$JOBS" > "$OUT/cmake_build.log" 2>&1
RC=$?
kv build_end_epoch "$(date +%s.%N)"
kv build_exit "$RC"
[ "$RC" = 0 ] || step_fail "cmake --build" "$RC" cmake_build.log

kv install_command "$CMAKE --install $BUILD"
kv install_start_epoch "$(date +%s.%N)"
L=$(left); [ "$L" -gt 0 ] || compile_fail "no time left to install"
timeout "$L" "$CMAKE" --install "$BUILD" > "$OUT/cmake_install.log" 2>&1
RC=$?
kv install_end_epoch "$(date +%s.%N)"
kv install_exit "$RC"
[ "$RC" = 0 ] || step_fail "cmake --install" "$RC" cmake_install.log
[ -x "$ENGINE/bin/lmp" ] || compile_fail "the install left no engine/bin/lmp" cmake_install.log
kv lmp_path "$ENGINE/bin/lmp"
kv end_epoch "$(date +%s.%N)"
kv compile_ok 1
ldd "$ENGINE/bin/lmp" > "$OUT/lmp_ldd.txt" 2>&1 || true
timeout 120 "$ENGINE/bin/lmp" -h > "$OUT/lmp_help.txt" 2>&1
kv lmp_help_exit "$?"
stamp "compile: done ($FFT FFT, cmake from $(sed -n 's/^cmake_source=//p' "$CREC"))"

# ---- 2 to 9: the stages; each runs its own guard first ------------------------------------------
stage() {   # stage <label> <command...>: run it, print its code, return the code
  local label=$1; shift
  stamp "$label: start"
  "$@"
  local rc=$?
  stamp "$label: code $rc"
  return "$rc"
}

stage "lmp -h and GPU check" "$PY" "$RUNNER" extract                    || finish $? "the lmp -h and GPU check stage stopped the run"
stage "timed dry run"        "$PY" "$RUNNER" generate --stage dryrun      || finish $? "the dry run stage stopped the run"
stage "copy of the box"      "$PY" "$RUNNER" generate --stage copy        || finish $? "the box copy stage stopped the run"
stage "equilibration"        "$PY" "$RUNNER" generate --stage equilibrate || finish $? "the equilibration stage stopped the run"
stage "run a"                "$PY" "$RUNNER" generate --stage prod_a      || finish $? "the run a stage stopped the run"
stage "run b"                "$PY" "$RUNNER" generate --stage prod_b      || finish $? "the run b stage stopped the run"
stage "run c"                "$PY" "$RUNNER" generate --stage prod_c      || finish $? "the run c stage stopped the run"
stage "endpoints"            "$PY" "$RUNNER" endpoints                    || finish $? "the endpoints stage failed"

echo "[result] files in results_m3/out/:"
ls -1 "$OUT" | sed 's/^/    /'
finish 0 "every stage finished"
