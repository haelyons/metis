#!/usr/bin/env bash
# On-box batch for run cp1: a viscosity stand-in from short LAMMPS simulations of eight liquids.
#
# WHAT IT DOES, IN THE ORDER THE EXECUTION DIRECTIVE SETS (GATE_COMMIT.md, last addendum, part b)
#   1. Reads the hourly price and the budget left, before anything else. It stops at once if
#      either is missing, not a number, or not above zero. It works out the time limit T.
#   2. Sets up the engine: a Python environment for the runner, the runner's own checks, then
#      LAMMPS 29 Aug 2024 from conda-forge (CUDA 12.6 build). A short trial of the edited deck
#      picks the path: the graphics card (GPU) first, then the processor (CPU) fallback.
#   3. Checks every shipped box file against the hash recorded before launch.
#   4. Runs the simulations, tier by tier, under the clock rule and the speed probe.
#   5. Runs the analysis pass: the twelve endpoints and the report-only readouts.
#   6. Results are written under out/results_cp1/ as each becomes known.
#   It never runs the box builder, Packmol or RDKit. The 24 boxes arrive built and checked.
#
# USAGE (from the launcher, inside the one working folder):
#   PRICE_USD_PER_HOUR=1.29 BUDGET_LEFT_USD=19.0 bash onbox_cp1.sh
#
# WHAT MUST SIT BESIDE THIS SCRIPT (the launcher copy ships it)
#   run_cp1.py, frozen/provenance.py (or provenance.py here), and boxes_cp1/ exactly as the
#   pre-launch step wrote it (24 boxes, decks, reference table, status, manifest).
#
# WHERE RESULTS GO
#   out/results_cp1/ : one self-describing record per run and per endpoint, the summary
#   (stage-summary.json), raw engine output under raw/, and this script's log (onbox_cp1.log).
#   The finish marker RUN_DONE holds the exit code, beside this script and in out/results_cp1/.
#   Nothing is written into a folder named prelaunch.
#
# EXIT CODES
#   0  every stage finished (tiers after tier 1 may still have been cut by the clock rule)
#   3  price or budget variable missing or invalid       4  tier 1 did not finish, or T < 6.29 h
#   5  no engine path passed its trial                   6  a shipped file failed its hash check
#   8  the engine could not be installed                 9  the analysis pass failed
#   1  any other setup failure
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
RES="out/results_cp1"
mkdir -p "$RES"
rm -f "$HERE/RUN_DONE" "$HERE/$RES/RUN_DONE"
exec > >(tee -a "$HERE/$RES/onbox_cp1.log") 2>&1

FINAL_RC=0
on_exit() {
  local rc=$?
  [ "$rc" = 0 ] && rc=$FINAL_RC
  printf '%s\n' "$rc" > "$HERE/$RES/RUN_DONE"
  printf '%s\n' "$rc" > "$HERE/RUN_DONE"
  echo "[finish] exit code $rc written to RUN_DONE at $(date -u +%FT%TZ)"
  exit "$rc"
}
trap on_exit EXIT
trap 'echo "[signal] stopped by a signal"; exit 143' TERM INT HUP

die() { local code=$1; shift; echo "[FATAL] $*" >&2; exit "$code"; }
stamp() { echo "[$1] $(date -u +%FT%TZ) uptime $(cut -d' ' -f1 /proc/uptime) s"; }

# --- 1. Price and budget, before anything else (system Python, standard library only) ----------
stamp "stage 1: price and budget"
python3 "$HERE/run_cp1.py" budget --outdir "$HERE/$RES"
rc=$?
[ "$rc" = 0 ] || die "$rc" "the price and budget check failed (code $rc); nothing else runs"

# --- 2. The engine ------------------------------------------------------------------------------
stamp "stage 2: engine setup"
[ -f "$HERE/run_cp1.py" ] || die 1 "run_cp1.py is not beside this script"
if [ ! -f "$HERE/frozen/provenance.py" ] && [ ! -f "$HERE/provenance.py" ]; then
  die 1 "the frozen record writer provenance.py is in neither frozen/ nor this folder"
fi
[ -d "$HERE/boxes_cp1" ] || die 1 "the shipped bundle boxes_cp1/ is not beside this script"

# 2a. A Python environment for the runner, with the analysis library pinned.
VENV="$HERE/.venv_cp1"
PY="$VENV/bin/python"
if [ ! -x "$PY" ]; then
  python3 -m venv "$VENV" || die 1 "could not create the Python environment"
fi
"$PY" -m pip install -q --upgrade pip || echo "[setup] pip self-upgrade skipped"
"$PY" -m pip install -q "numpy==1.26.4" || die 1 "could not install numpy 1.26.4"
"$PY" -c "import numpy, sys; print('[setup] python', sys.version.split()[0], 'numpy', numpy.__version__)" \
  || die 1 "numpy does not import"

# 2b. The runner's own checks: standard library only, no engine, no network.
"$PY" "$HERE/run_cp1.py" --selftest || die 1 "the runner's selftest failed; nothing runs"

# 2c. LAMMPS 29 Aug 2024 from conda-forge, CUDA 12.6 build, through a pinned micromamba.
MM_URL="https://conda.anaconda.org/conda-forge/linux-64/micromamba-2.9.0-0.tar.bz2"
MM_SHA="8761c382127e6363bd9e0a2451aa3ef90d071a79133f736e2f759a3bf13040dd"
GPU_SPEC="lammps==2024.08.29=cuda126_py310_h894d002_nompi_2"
CPU_SPEC="lammps==2024.08.29=cpu_py310_h956f9f1_mpi_openmpi_2"   # the same build as the workstation's
MMDIR="$HERE/.mm_cp1"
MM="$MMDIR/bin/micromamba"
ENGINE="$HERE/.engine_cp1"
if [ ! -x "$MM" ]; then
  mkdir -p "$MMDIR"
  curl -fsSL --retry 5 -o "$MMDIR/micromamba.tar.bz2" "$MM_URL" || die 8 "could not download micromamba"
  echo "$MM_SHA  $MMDIR/micromamba.tar.bz2" | sha256sum -c - || die 8 "micromamba download has the wrong hash"
  tar -xjf "$MMDIR/micromamba.tar.bz2" -C "$MMDIR" bin/micromamba || die 8 "could not unpack micromamba"
fi
export MAMBA_ROOT_PREFIX="$MMDIR/root"
nvidia-smi || echo "[setup] nvidia-smi is not available"
CUDA_VER="$(nvidia-smi 2>/dev/null | sed -n 's/.*CUDA Version: *\([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -1)"
if [ -n "$CUDA_VER" ]; then export CONDA_OVERRIDE_CUDA="$CUDA_VER"; fi
INSTALL_NOTE=""
if [ ! -x "$ENGINE/bin/lmp" ]; then
  if "$MM" create -y -q -p "$ENGINE" -c conda-forge --override-channels "$GPU_SPEC"; then
    INSTALL_NOTE="installed $GPU_SPEC"
  else
    echo "[setup] the CUDA 12.6 build did not install; installing the processor build instead"
    rm -rf "$ENGINE"
    "$MM" create -y -q -p "$ENGINE" -c conda-forge --override-channels "$CPU_SPEC" \
      || die 8 "neither LAMMPS build could be installed"
    INSTALL_NOTE="CUDA build failed to install; installed $CPU_SPEC"
  fi
else
  INSTALL_NOTE="engine already present"
fi
"$MM" list -p "$ENGINE" lammps || true

# 2d. Pick the path by a short trial of the edited deck: GPU switches first, then the processor.
export OMPI_MCA_plm=isolated OMPI_MCA_rmaps_base_oversubscribe=yes OMPI_MCA_btl_vader_single_copy_mechanism=none
export CUDA_CACHE_MAXSIZE=4294967296 CUDA_CACHE_PATH="$HERE/.nv_cache_cp1"
"$PY" "$HERE/run_cp1.py" engine --outdir "$HERE/$RES" --bundle "$HERE/boxes_cp1" --lmp "$ENGINE/bin/lmp" \
  --work "$HERE/work_cp1" --install-note "$INSTALL_NOTE"
rc=$?
[ "$rc" = 0 ] || die "$rc" "no engine path passed its trial (code $rc); no simulation runs"

# --- 3. Every shipped box file against its pre-launch hash ---------------------------------------
stamp "stage 3: hash check"
python3 "$HERE/run_cp1.py" verify --outdir "$HERE/$RES" --bundle "$HERE/boxes_cp1"
rc=$?
[ "$rc" = 0 ] || die "$rc" "a shipped file failed its hash check (code $rc); no simulation runs"

# --- 4. The simulations, tier by tier, under the clock rule and the speed probe ------------------
stamp "stage 4: simulations"
"$PY" "$HERE/run_cp1.py" generate --outdir "$HERE/$RES" --bundle "$HERE/boxes_cp1" --work "$HERE/work_cp1"
GEN_RC=$?
echo "[stage 4] finished with code $GEN_RC"

# --- 5. The analysis pass, always, so finished cells are reported even after an early stop -------
stamp "stage 5: analysis"
"$PY" "$HERE/run_cp1.py" endpoints --outdir "$HERE/$RES" --bundle "$HERE/boxes_cp1"
END_RC=$?

# --- 6. What a reader should look at first --------------------------------------------------------
stamp "stage 6: results"
echo "[result] files in $RES:"
ls -1 "$HERE/$RES" | sed 's/^/    /'
echo "[result] run validity:"
sed 's/^/    /' "$HERE/$RES/RUN_VALID.json" 2>/dev/null || echo "    (no validity file)"
if [ "$GEN_RC" != 0 ]; then
  FINAL_RC=$GEN_RC
elif [ "$END_RC" != 0 ]; then
  FINAL_RC=9
fi
exit "$FINAL_RC"
