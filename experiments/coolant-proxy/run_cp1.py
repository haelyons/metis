#!/usr/bin/env python3
"""Runner for one pre-registered experiment (tag cp1): does a viscosity stand-in,
read from a short simulation, put eight liquids in the order of their reference
viscosities?

WHAT IS MEASURED, IN PLAIN WORDS
  Eight liquids come from a published simulation study. Each one is simulated as
  a box of about 15,000 atoms at 40 degrees Celsius (313.15 K) and 1 atmosphere.
  The simulation program is LAMMPS. The interaction parameters are a published
  set for long-chain liquids (the LOPLS-AA force field).

  The runner records the centre of every molecule once per picosecond (ps). The
  mean-squared displacement (MSD) is the average squared distance a centre has
  moved after a given delay, called the lag. In ordinary diffusion it grows in
  proportion to the lag. One sixth of that slope is the self-diffusion
  coefficient, D.

  The stand-in for viscosity (the proxy) is kT/(6*pi*D*R). Here k is Boltzmann's
  constant and T the temperature. R is the radius of a sphere that holds the
  volume one molecule fills at the simulated density.

  The main question is whether the proxy ranks the eight liquids like their
  reference viscosities. Agreement is scored by Spearman's rank correlation
  (rho): the ordinary correlation of the two rank orders. Success is rho of at
  least 0.8.

WHICH TEXTS BIND THIS FILE, IN ORDER
  1. The execution directive: the addendum at the end of GATE_COMMIT.md.
  2. The gate's item answers above that addendum.
  3. The design record, out/design_record_attempt2.json.
  Where two differ, the earlier one wins. Numbers the design marks as guesses
  are binding. Nothing here re-chooses a number those texts fix.

WHERE EACH PART RUNS
  On this workstation, before any rented box is launched (no cost), with the
  local toolchain's Python (.toolchain/env/bin/python):
    python run_cp1.py extract      # every pre-launch step, in the directive's order
    python run_cp1.py decktrial    # optional: a few hundred steps of the edited
                                   # deck on one box, to catch deck errors for free
  Records go to out/results_cp1/prelaunch/. The shipped bundle goes to boxes_cp1/.

  On the rented box, in this order, started by onbox_cp1.sh:
    python3 run_cp1.py budget      # price and budget, then the time limit
    python  run_cp1.py engine      # a short trial picks the GPU or CPU path
    python3 run_cp1.py verify      # every shipped box file against its hash
    python  run_cp1.py generate    # the simulations, tier by tier, under the clock
    python  run_cp1.py endpoints   # the twelve endpoints and the summary
  Records go to out/results_cp1/. The box never writes into "prelaunch".

  Anywhere, standard library only:
    python run_cp1.py --selftest

THE SIMULATIONS
  A run is one liquid in one packed box. Each run has three parts: 50,000 steps
  of 0.5 femtosecond (fs) strain relaxation, 50,000 steps of 2 fs at constant
  volume, and 500,000 steps of 2 fs (1.0 nanosecond, ns) at constant pressure.
  The committed equilibration deck is used with the design's listed edits only:
  the final density-matching part is removed, and every molecule's unwrapped
  centre is written every 1 ps. Step counts and the timestep are set through
  the deck's own command-line variables.

  Three reruns per liquid, each with its own packed box and velocity seed. All
  reruns share one box session, so they measure rerun spread on one machine only.

  Work runs in priority tiers, four runs at a time (a wave):
    tier 1: reruns 1 and 2 of all eight liquids, 16 runs, 9.6 million steps
    tier 2: rerun 1 of each liquid continued 1 ns more, 8 runs, 4.0 million steps
    tier 3: rerun 3 of all eight liquids, 8 runs, 4.8 million steps
    tier 4: nonylcyclohexane rerun 1 at the deck's own 1 fs step, 1.15 million
  The time limit T, in hours from box boot, is min(18.0/P, B/P - 0.75). P is the
  hourly price and B the budget left. Before each wave, the runner projects its
  end from the mean length of finished waves. A wave starts only if that fits
  within T less 15 minutes, and only after every higher tier is done. In the
  first wave a speed probe reads the step rate once each run has done 50,000
  constant-pressure steps. If the rest of tier 1 (9.0 million steps) cannot fit,
  every run stops.

VALIDITY, AND HOW A VOID SPREADS
  Every record carries a top-level run_valid field. These void the run:
    - any pre-launch check failing (data pre-check, box checks, planted checks);
    - tier 1 not finishing (speed probe, clock rule, time limit, failed runs);
    - the density gate failing (endpoint 2).
  A void writes run_valid=false into every record written afterwards. It also
  rewrites every record already written, marked as voided after the fact. A void
  is never undone. Records then state the rule's outcome but give no verdict.

NUMBERS AND READINGS THIS FILE CHOSE (the binding texts fix none of them)
  - Net charge per molecule counts as near zero at 1e-6 elementary charges or
    less. The builder rounds it to 1e-10.
  - The diffusion window 0.2-1.0 ns holds 801 positions, 800 steps of 1 ps.
  - D is the least-squares slope, with intercept, of MSD against every
    whole-picosecond lag in the fit window, divided by 6.
  - The log-log slope is the same fit on the logarithms of lag and MSD.
  - Drift is removed by subtracting, frame by frame, the mean centre of all
    molecules in the box.
  - A planted "ensemble" in check (a) is one synthetic version of all eight
    cells, with each liquid's real molecule count. Checks (b) and (c) use 200
    single cells each, the eight counts taken in turn.
  - Planted walkers share a centre that does not wander, as in a box whose total
    momentum is zero. A known common drift is then added. Without this, drift
    removal would shrink the planted D by a factor (1 - 1/N), and the bias check
    would test that artefact instead of the code.
  - Every planted walk uses one D of 0.01 square angstroms per ps (1e-10 m2/s).
    Equal D values let rerun noise reorder liquids, so the margin check can test
    the margin code.
  - Planted bias is pooled as D_fit/D_true - 1 over all planted cells. Its
    standard error is the sample deviation divided by the square root of n.
  - The rerun margin is the population standard deviation over every pick. The
    timestep spread is the sample standard deviation of the three 2 fs reruns.
  - The non-diffusive count uses each liquid's MSD averaged over its finished
    reruns.
  - Each proxy takes R from the mean density of the same runs that give its D.
    The 2 ns run uses its own last 250 ps.
  - The short side of the longer-run comparison uses whichever of reruns 2 and
    3 finished.
  - A margin or spread of exactly zero halts that endpoint with the code
    WRONG_VARIANCE_SOURCE and no verdict. It does not void the other endpoints.
  - The speed probe's rate is all steps done by the wave's runs, as LAMMPS
    numbers them in its centre file, divided by wall time since the wave began.
  - "Time limit" also means running simulations are stopped when T is reached.
    The analysis then runs inside the 30-minute backstop margin.
  - A run that fails, or whose output fails a degeneracy check, is repeated once.
  - On the box, LAMMPS comes from conda-forge, CUDA 12.6 build, single process
    (no MPI). That build carries GPU support through the KOKKOS package, so the
    GPU path is tried with KOKKOS switches first.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import gzip
import hashlib
import importlib
import importlib.util
import io
import itertools
import json
import math
import os
import random
import re
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import time
import traceback
from array import array
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "cp1"
OUT_REL = Path("out") / "results_cp1"
PRELAUNCH_NAME = "prelaunch"
BUNDLE_REL = Path("boxes_cp1")
WORK_REL = Path("work_cp1")
TOOLCHAIN_BIN_REL = Path(".toolchain") / "env" / "bin"
STATE_NAME = "RUN_VALID.json"
ENGINE_NAME = "ENGINE.json"
PROGRESS_NAME = "PROGRESS.json"

# Committed inputs, by path relative to this folder, with their design-time hashes.
COMMITTED = {
    "dataset": ("data/MD-ML-thermophysical/ML/data/dataset.csv",
                "962d1c7e9517b04b97f73f7a016e102eb1cacbd13a190222c0f1e30aa33cded0"),
    "predictions": ("data/MD-ML-thermophysical/ML/results/predictions_viscosity.csv",
                    "bf0e17fc60c8ac816debb48ca497b75a4d459f810a123f7d9c76330d06ab420d"),
    "builder": ("data/MD-ML-thermophysical/MD/builder/smiles2loplsaa.py",
                "91cac1d5307eb3a0ab54be1cfd2fac3d01919bdd1cd35e7c75929bd016977008"),
    "deck": ("data/MD-ML-thermophysical/MD/lammps/equilibrate.in",
             "1e79c3f7669b8ae2e994caacc6f56dc4bfac19737f6f61a3b0f68a94269816cb"),
}
# The three texts that bind this runner.
BINDING = {
    "execution_directive": ("out/exec_note_cp1.txt",
                            "968be335ec19d72765471955296fcf7aa6b9e6d27230f34f941f34d3e6865285"),
    "gate_commit": ("GATE_COMMIT.md",
                    "ffe8be31860cae42238346797b2326ffb3d91a9e48b4347153384326524886cf"),
    "design_record": ("out/design_record_attempt2.json",
                      "9f320ef3d15f224a9bebeb30d7ff4dfe6eeab79230ec9785f2a977de0af6e641"),
}

# ---------------------------------------------------------------------------
# Physical constants (SI, exact by definition) and the design's fixed numbers
# ---------------------------------------------------------------------------
KB_J_PER_K = 1.380649e-23
NA_PER_MOL = 6.02214076e23
T_KELVIN = 313.15
T_STR = "313.15"
ATOMIC_MASS = {"C": 12.011, "H": 1.008, "O": 15.999}
AMU_PER_A3_TO_G_PER_CM3 = 1.0 / (NA_PER_MOL * 1e-24)

MOLECULES = [
    {"id": "mol_00105", "name": "squalane", "family": "hydrocarbon",
     "smiles": "CC(C)CCCC(C)CCCC(C)CCCCC(C)CCCC(C)CCCC(C)C", "formula": {"C": 30, "H": 62},
     "eta_ref": 15.06, "rho_ref": 0.796, "rho_paper": 0.804, "band": (0.788, 0.820), "n_mol": 163},
    {"id": "mol_00557", "name": "nonylcyclohexane", "family": "hydrocarbon",
     "smiles": "CCCCCCCCCC1CCCCC1", "formula": {"C": 15, "H": 30},
     "eta_ref": 2.68, "rho_ref": 0.805, "rho_paper": 0.797, "band": (0.781, 0.813), "n_mol": 333},
    {"id": "mol_00426", "name": "4-hexyl-1,7-diphenylheptane", "family": "hydrocarbon",
     "smiles": "CCCCCCC(CCCc1ccccc1)CCCc1ccccc1", "formula": {"C": 25, "H": 36},
     "eta_ref": 15.56688, "rho_ref": 0.904, "rho_paper": 0.904, "band": (0.886, 0.922), "n_mol": 246},
    {"id": "mol_00400", "name": "2-(1-propylheptyl)naphthalene", "family": "hydrocarbon",
     "smiles": "CCCCCCC(CCC)c1ccc2ccccc2c1", "formula": {"C": 20, "H": 28},
     "eta_ref": 13.3444, "rho_ref": 0.914, "rho_paper": 0.905, "band": (0.887, 0.923), "n_mol": 312},
    {"id": "mol_00764", "name": "decyl stearate", "family": "oxygenate",
     "smiles": "CCCCCCCCCCCCCCCCCC(=O)OCCCCCCCCCC", "formula": {"C": 28, "H": 56, "O": 2},
     "eta_ref": 11.17585, "rho_ref": 0.863, "rho_paper": 0.837, "band": (0.820, 0.854), "n_mol": 174},
    {"id": "mol_00305", "name": "bis(2-ethylhexyl) sebacate", "family": "oxygenate",
     "smiles": "CCCCC(CC)COC(=O)CCCCCCCCC(=O)OCC(CC)CCCC", "formula": {"C": 26, "H": 50, "O": 4},
     "eta_ref": 10.445688, "rho_ref": 0.89925, "rho_paper": 0.890, "band": (0.872, 0.908), "n_mol": 188},
    {"id": "mol_00942", "name": "7,10,13-trioxanonadecane", "family": "oxygenate",
     "smiles": "CCCCCCOCCOCCOCCCCCC", "formula": {"C": 16, "H": 34, "O": 3},
     "eta_ref": 6.4, "rho_ref": 0.859, "rho_paper": 0.850, "band": (0.833, 0.867), "n_mol": 283},
    {"id": "mol_01025", "name": "tetraethylene glycol diethyl ether", "family": "oxygenate",
     "smiles": "CCOCCOCCOCCOCCOCC", "formula": {"C": 12, "H": 26, "O": 5},
     "eta_ref": 5.5, "rho_ref": 1.069, "rho_paper": 0.962, "band": (0.943, 0.981), "n_mol": 349},
]
MOL_IDS = [m["id"] for m in MOLECULES]
MOL = {m["id"]: m for m in MOLECULES}
HYDROCARBONS = MOL_IDS[:4]
OXYGENATES = MOL_IDS[4:]
GLYCOL_ETHER = "mol_01025"
TIMESTEP_MOL = "mol_00557"
REFERENCE_ORDER = ["mol_00426", "mol_00105", "mol_00400", "mol_00764",
                   "mol_00305", "mol_00942", "mol_01025", "mol_00557"]

PACK_SEEDS = {1: 61453, 2: 61454, 3: 61455}
PACK_DENSITY = 0.75
RERUNS = (1, 2, 3)


def velocity_seed(rerun: int) -> int:
    """The deck's own formula: 4928459 + run_id * 10007."""
    return 4928459 + rerun * 10007


# Command-line variables per kind of run. Only step counts, the timestep and the
# centre-output spacing differ from the deck's defaults. The density window keeps
# the deck's own shape: 2,500 samples, 0.1 ps apart, over the last 250 ps.
RUN_KINDS = {
    "main": {"timestep_fs": 2.0, "relax_dt": 0.5, "pushoff_steps": 50000, "settle_steps": 50000,
             "npt_steps": 500000, "density_avg_start": 375000, "density_sample_every": 50,
             "density_sample_repeat": 2500, "density_sample_freq": 125000, "com_every": 500},
    "timestep_1fs": {"timestep_fs": 1.0, "relax_dt": 0.5, "pushoff_steps": 50000, "settle_steps": 100000,
                     "npt_steps": 1000000, "density_avg_start": 750000, "density_sample_every": 100,
                     "density_sample_repeat": 2500, "density_sample_freq": 250000, "com_every": 1000},
    "extension": {"timestep_fs": 2.0, "ext_steps": 500000, "density_avg_start": 875000,
                  "density_sample_every": 50, "density_sample_repeat": 2500,
                  "density_sample_freq": 125000, "com_every": 500},
}
PRE_STAGE3_STEPS = {"main": 100000, "timestep_1fs": 150000, "extension": 0}
STAGE3_END_STEP = {"main": 500000, "timestep_1fs": 1000000, "extension": 1000000}
STAGE3_END_PS = {"main": 1000.0, "timestep_1fs": 1000.0, "extension": 2000.0}
TOTAL_STEPS = {"main": 600000, "timestep_1fs": 1150000, "extension": 500000}

FRAME_PS = 1.0
WINDOW_MAIN_PS = (200.0, 1000.0)
WINDOW_EXT_PS = (200.0, 2000.0)
FITS_MAIN = {"main": (100.0, 400.0), "alt_short": (50.0, 200.0), "alt_late": (200.0, 400.0)}
FITS_EXT = {"long": (100.0, 900.0)}
DENSITY_LAST_PS = 250.0
READOUT_EARLY_PS = (200.0, 450.0)

RHO_PASS = 0.8
RHO_ABANDON = 0.6
NONDIFF_LABEL_MIN = 3
FAMILY_MIN = 10
COST_LIMIT_NS = 8.0
NS_PER_RUN = 1.125
PAPER_NS_PER_MOLECULE = 80.0
I2_TOL = 0.001
I3_TOL = 1e-6
CHARGE_TOL = 1e-6
WAVE_SIZE = 4
GUESSED_RATE = 530.0
PROBE_STAGE3_STEPS = 50000
PROBE_REMAINING_STEPS = 9_000_000
SPARE_H = 0.25
LAUNCH_MIN_T_H = Fraction("6.29")
TEMP_TOL_K = 30.0
TELEPORT_A = 10.0
POLL_S = 15.0
TRIAL_TIMEOUT_S = 1800
BUILD_TIMEOUT_S = 7200

PLANTED_SEED = 7
PLANTED_D = 0.01                      # square angstroms per ps, i.e. 1e-10 m2/s
PLANTED_DRIFT = (0.01, -0.02, 0.005)  # angstroms per ps, common to all walkers
N_ENS_A = 20
N_ENS_BC = 200
EXPONENT_C = 0.7
BAND_FRACTION = 0.95

# Labels fixed by the gate and the execution directive, word for word.
LABEL_D1_PASS = "yes, for the Stokes-Einstein-like form kT/(6π·D·R)"
LABEL_D1_REFUTED = ("refuted for the Stokes-Einstein-like form kT/(6π·D·R) only; "
                    "the excess-entropy-like form was not tested")
LABEL_ABANDON = ("below the abandon line of 0.6: this form is not worth pursuing; "
                 "refuted for the Stokes-Einstein-like form kT/(6π·D·R) only; "
                 "the excess-entropy-like form was not tested")
LABEL_NONDIFF = "apparent D: slope outside the planted band for {n} of 8 molecules"
LABEL_WINDOW = "passed in the pre-registered window (0.1–0.4 ns); window-dependent"
LABEL_ROBUST = "rho at least 0.8 in all three fit windows"
LABEL_E8_NOISE = "higher than free orderings, within rerun noise"
LABEL_SIZE = "size term adds nothing"
LABEL_DIFFUSION = "diffusion adds nothing over density"
LABEL_COST = "met by the plan's arithmetic: 3.375 ns per molecule, 4.2% of 80 ns; not an empirical test"
LABEL_CLAIM3_NOT_SHOWN = "not shown"
LABEL_E1 = "integrity check, not evidence"
LABEL_INCOMPLETE = "incomplete run: descriptive only, no verdict"
LABEL_UNTRUSTED = "untrusted: the density gate failed, so this ranking is neither passed nor refuted"
LABEL_RERUNS = ("reruns share one box session; they measure rerun spread on one machine, "
                "one box size and one software build only")
WRONG_VARIANCE_SOURCE = "WRONG_VARIANCE_SOURCE"


class StageError(RuntimeError):
    pass


class WrongVarianceSource(RuntimeError):
    pass


class ParseError(ValueError):
    pass


class BudgetError(ValueError):
    pass


class DeckEditError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rel(path) -> str:
    try:
        return str(Path(path).resolve().relative_to(HERE))
    except ValueError:
        return str(path)


def clean(obj):
    """JSON-safe copy: non-finite floats become None, fractions and paths become plain."""
    if isinstance(obj, bool) or obj is None:
        return obj
    if isinstance(obj, Fraction):
        return float(obj)
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, (int, str)):
        return obj
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, array)):
        return [clean(v) for v in obj]
    return str(obj)


def write_json_atomic(path, obj) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w") as fh:
        fh.write(json.dumps(clean(obj), indent=2, sort_keys=True))
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def read_json(path):
    return json.loads(Path(path).read_text())


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs) if xs else None


def is_finite_number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def r12(x):
    return None if x is None else round(x, 12)


# ---------------------------------------------------------------------------
# The frozen record writer and run validity
# ---------------------------------------------------------------------------
_PROV = None


def provenance():
    global _PROV
    if _PROV is not None:
        return _PROV
    for cand in (HERE / "frozen" / "provenance.py", HERE / "provenance.py"):
        if cand.exists():
            spec = importlib.util.spec_from_file_location("cp1_provenance", cand)
            mod = importlib.util.module_from_spec(spec)
            keep = sys.dont_write_bytecode
            sys.dont_write_bytecode = True  # leave no cache files beside the frozen writer
            try:
                spec.loader.exec_module(mod)
            finally:
                sys.dont_write_bytecode = keep
            _PROV = mod
            return mod
    raise SystemExit("cannot find the frozen record writer provenance.py in frozen/ or beside this file")


def read_state(outdir) -> dict:
    p = Path(outdir) / STATE_NAME
    if p.exists():
        st = json.loads(p.read_text())
        return {"run_valid": bool(st.get("run_valid", True)), "voided_by": list(st.get("voided_by", [])),
                "labels": list(st.get("labels", [])), "voided_at_utc": st.get("voided_at_utc")}
    return {"run_valid": True, "voided_by": [], "labels": [], "voided_at_utc": None}


def is_record(obj) -> bool:
    return isinstance(obj, dict) and "cell" in obj and "decision_rule" in obj


def void_run(outdir, reason: str, label: str | None = None) -> dict:
    """Set run_valid=false for good, and rewrite every record already in outdir."""
    outdir = Path(outdir)
    st = read_state(outdir)
    st["run_valid"] = False
    if reason not in st["voided_by"]:
        st["voided_by"].append(reason)
    if label and label not in st["labels"]:
        st["labels"].append(label)
    st["voided_at_utc"] = st.get("voided_at_utc") or utc_now()
    write_json_atomic(outdir / STATE_NAME, st)
    for p in sorted(outdir.glob("*.json")):
        if p.name in (STATE_NAME, ENGINE_NAME, PROGRESS_NAME):
            continue
        try:
            rec = json.loads(p.read_text())
        except Exception:
            continue
        if not is_record(rec):
            continue
        if rec.get("run_valid", True):
            rec["run_valid"] = False
            rec["run_valid_voided_retroactively"] = True
        rec["run_valid_voided_by"] = list(st["voided_by"])
        rec["run_labels"] = list(st["labels"])
        write_json_atomic(p, rec)
    print(f"[void] run_valid=false; reason: {reason}")
    return st


def write_record(outdir, *, cell, inputs, metric, values, threshold=None, decision_rule, decision,
                 notes="", rows=None) -> Path:
    """One self-describing record through the frozen writer, then the validity fields."""
    outdir = Path(outdir)
    prov = provenance()
    st = read_state(outdir)
    path = outdir / (prov.cell_slug(cell) + ".json")
    prov.write_result(path, cell=cell, inputs=list(inputs or []), metric=metric, values=clean(values),
                      threshold=clean(threshold or {}), decision_rule=decision_rule, decision=decision,
                      notes=notes, rows=clean(rows) if rows is not None else None)
    rec = json.loads(path.read_text())
    rec["run_valid"] = st["run_valid"]
    rec["run_valid_voided_by"] = list(st["voided_by"])
    rec["run_valid_voided_retroactively"] = False
    rec["run_labels"] = list(st["labels"])
    write_json_atomic(path, rec)
    return path


def describe(path, n_items=None) -> dict:
    return provenance().describe_input(path, n_items)


def guard_not_prelaunch(outdir) -> None:
    if PRELAUNCH_NAME in Path(outdir).resolve().parts:
        raise SystemExit("this stage runs on the box and never writes into a folder named prelaunch")


# ---------------------------------------------------------------------------
# Rank arithmetic
# ---------------------------------------------------------------------------
def average_ranks(xs):
    n = len(xs)
    order = sorted(range(n), key=lambda i: xs[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and xs[order[j + 1]] == xs[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def pearson(a, b):
    n = len(a)
    ma, mb = sum(a) / n, sum(b) / n
    sab = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    saa = sum((x - ma) ** 2 for x in a)
    sbb = sum((y - mb) ** 2 for y in b)
    if saa == 0 or sbb == 0:
        return None
    return sab / math.sqrt(saa * sbb)


def spearman(xs, ys):
    """Spearman's rho: Pearson correlation of average ranks (ties share a rank)."""
    xs, ys = list(xs), list(ys)
    if len(xs) != len(ys) or len(xs) < 2:
        return None
    if any((v is None) or (not math.isfinite(v)) for v in xs + ys):
        return None
    r = pearson(average_ranks(xs), average_ranks(ys))
    return None if r is None else r12(r)


_PERM_COUNTS = {}


def perm_sum_sq_counts(n: int = 8) -> Counter:
    if n not in _PERM_COUNTS:
        c = Counter()
        for p in itertools.permutations(range(n)):
            c[sum((i - pi) ** 2 for i, pi in enumerate(p))] += 1
        _PERM_COUNTS[n] = c
    return _PERM_COUNTS[n]


def chance_at_least(rho: float, n: int = 8):
    """Exact count of the n! orderings whose rho reaches the given value."""
    counts = perm_sum_sq_counts(n)
    total = math.factorial(n)
    k = sum(cnt for s, cnt in counts.items() if r12(1 - 6 * s / (n * (n * n - 1))) >= r12(rho))
    return k, total


def concordance(proxy: dict, ref: dict, group) -> list:
    out = []
    for a, b in itertools.combinations(group, 2):
        sp, sr = proxy[a] - proxy[b], ref[a] - ref[b]
        out.append({"pair": [a, b], "concordant": (sp > 0 and sr > 0) or (sp < 0 and sr < 0)})
    return out


def family_chance_counts():
    """All 24 x 24 pairs of within-family orders: how many reach 10 and 9 of 12."""
    perms = list(itertools.permutations(range(4)))

    def conc(p):
        return sum(1 for i, j in itertools.combinations(range(4), 2) if p[i] < p[j])

    cs = [conc(p) for p in perms]
    ge10 = sum(1 for a in cs for b in cs if a + b >= 10)
    ge9 = sum(1 for a in cs for b in cs if a + b >= 9)
    return {"ge10": ge10, "ge9": ge9, "total": len(cs) ** 2}


# ---------------------------------------------------------------------------
# Chemistry: formula from the molecule code (SMILES), mass, radius, proxy
# ---------------------------------------------------------------------------
def formula_from_smiles(smiles: str) -> dict:
    """Element counts for the plain SMILES used here (C, O, aromatic c, rings, branches)."""
    atoms, bonds = [], []
    prev, stack, ring, pending = None, [], {}, None
    i = 0

    def add_bond(a, b, order):
        if order is None:
            order = 1.5 if (atoms[a][1] and atoms[b][1]) else 1.0
        bonds.append((a, b, order))

    while i < len(smiles):
        c = smiles[i]
        if c == "(":
            stack.append(prev)
            i += 1
            continue
        if c == ")":
            if not stack:
                raise ValueError("unbalanced branch")
            prev = stack.pop()
            i += 1
            continue
        if c in "=#-":
            pending = {"=": 2.0, "#": 3.0, "-": 1.0}[c]
            i += 1
            continue
        if c.isdigit() or c == "%":
            if c == "%":
                num = smiles[i + 1:i + 3]
                i += 3
            else:
                num = c
                i += 1
            if prev is None:
                raise ValueError("ring digit before any atom")
            if num in ring:
                j, order0 = ring.pop(num)
                add_bond(prev, j, pending if pending is not None else order0)
            else:
                ring[num] = (prev, pending)
            pending = None
            continue
        if c == "[" or smiles.startswith("Cl", i) or smiles.startswith("Br", i):
            raise ValueError(f"unsupported SMILES feature at position {i}")
        if c in "CO":
            el, arom = c, False
        elif c == "c":
            el, arom = "C", True
        else:
            raise ValueError(f"unsupported SMILES character {c!r}")
        idx = len(atoms)
        atoms.append((el, arom))
        if prev is not None:
            add_bond(prev, idx, pending)
        prev, pending = idx, None
        i += 1
    if ring or stack:
        raise ValueError("unclosed ring or branch")
    nb = [0] * len(atoms)
    bo = [0.0] * len(atoms)
    for a, b, o in bonds:
        nb[a] += 1
        nb[b] += 1
        bo[a] += o
        bo[b] += o
    counts = Counter()
    for k, (el, arom) in enumerate(atoms):
        counts[el] += 1
        if arom:
            h = 3 - nb[k]
        else:
            h = {"C": 4, "O": 2}[el] - bo[k]
        if h < 0 or abs(h - round(h)) > 1e-9:
            raise ValueError(f"impossible valence at atom {k + 1}")
        counts["H"] += int(round(h))
    return dict(counts)


def formula_text(f: dict) -> str:
    return "".join(f"{el}{f[el]}" for el in ("C", "H", "O") if f.get(el))


def molar_mass(formula: dict) -> float:
    return sum(ATOMIC_MASS[el] * n for el, n in formula.items())


def sphere_radius_m(molar_mass_g: float, density_g_cm3: float) -> float:
    v_cm3 = molar_mass_g / (density_g_cm3 * NA_PER_MOL)
    return ((3.0 * v_cm3) / (4.0 * math.pi)) ** (1.0 / 3.0) * 1e-2


def proxy_mpas(d_a2ps: float, molar_mass_g: float, density_g_cm3: float) -> float:
    """kT/(6 pi D R) in mPa s, from D in square angstroms per ps."""
    d_m2s = d_a2ps * 1e-8
    return KB_J_PER_K * T_KELVIN / (6.0 * math.pi * d_m2s * sphere_radius_m(molar_mass_g, density_g_cm3)) * 1e3


def planted_d_a2ps(eta_mpas: float, molar_mass_g: float, density_g_cm3: float) -> float:
    r = sphere_radius_m(molar_mass_g, density_g_cm3)
    return KB_J_PER_K * T_KELVIN / (6.0 * math.pi * eta_mpas * 1e-3 * r) * 1e8


# ---------------------------------------------------------------------------
# Parsers (standard library only)
# ---------------------------------------------------------------------------
def _isnum(tok: str) -> bool:
    try:
        float(tok)
        return True
    except ValueError:
        return False


def parse_com_file(text: str) -> dict:
    """LAMMPS 'fix ave/time ... mode vector' output: a 'step nrows' line, then rows
    'index x y z'. Returns complete frames; a cut-off last frame is flagged, not kept."""
    frames = []
    n_rows_seen = set()
    cur_step, cur_n, cur_vals, cur_rows = None, 0, None, 0
    truncated = False
    for ln, raw in enumerate(text.splitlines(), 1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        if len(parts) == 2:
            if cur_step is not None:
                if cur_rows != cur_n:
                    raise ParseError(f"frame at step {cur_step} has {cur_rows} rows; its header says {cur_n}")
                frames.append((cur_step, cur_vals))
            try:
                cur_step, cur_n = int(parts[0]), int(parts[1])
            except ValueError:
                raise ParseError(f"line {ln}: a frame header must be two whole numbers")
            n_rows_seen.add(cur_n)
            cur_vals, cur_rows = array("d"), 0
        elif len(parts) == 4:
            if cur_step is None:
                raise ParseError(f"line {ln}: a data row comes before any frame header")
            try:
                idx = int(parts[0])
                xyz = (float(parts[1]), float(parts[2]), float(parts[3]))
            except ValueError:
                raise ParseError(f"line {ln}: a data row must be an index and three numbers")
            if idx != cur_rows + 1:
                raise ParseError(f"line {ln}: row index {idx} out of order")
            if cur_rows >= cur_n:
                raise ParseError(f"line {ln}: more rows than the frame header declares")
            cur_vals.extend(xyz)
            cur_rows += 1
        else:
            raise ParseError(f"line {ln}: expected 2 or 4 fields, found {len(parts)}")
    if cur_step is not None:
        if cur_rows == cur_n:
            frames.append((cur_step, cur_vals))
        else:
            truncated = True
    return {"frames": frames, "truncated_last_frame": truncated,
            "rows_per_frame": sorted(n_rows_seen)}


def format_com_text(steps, frames_xyz, n_mol: int) -> str:
    """Write frames the way LAMMPS writes the centre file (default ' %g' format)."""
    out = ["# Time-averaged data for fix cp1_com_out", "# TimeStep Number-of-rows",
           "# Row c_cp1_com[1] c_cp1_com[2] c_cp1_com[3]"]
    for step, vals in zip(steps, frames_xyz):
        out.append(f"{step} {n_mol}")
        for i in range(n_mol):
            out.append(f"{i + 1} {vals[3 * i]:g} {vals[3 * i + 1]:g} {vals[3 * i + 2]:g}")
    return "\n".join(out) + "\n"


def last_header_step_from_tail(tail: str, from_file_start: bool):
    """Last complete 'step nrows' header in the tail of a centre file."""
    lines = tail.split("\n")
    if not tail.endswith("\n"):
        lines = lines[:-1]
    if not from_file_start and lines:
        lines = lines[1:]
    for raw in reversed(lines):
        parts = raw.split()
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return int(parts[0])
    return None


def last_header_step(path, tail_bytes: int = 262144):
    try:
        size = os.path.getsize(path)
        with open(path, "rb") as fh:
            start = max(0, size - tail_bytes)
            fh.seek(start)
            tail = fh.read().decode("utf-8", errors="replace")
        return last_header_step_from_tail(tail, start == 0)
    except OSError:
        return None


_LOOP_RE = re.compile(r"Loop time of ([-+0-9.eE]+) on (\d+) procs for (\d+) steps with (\d+) atoms")
_PERF_RE = re.compile(r"([-+0-9.eE]+) timesteps/s")
_DENS_RE = re.compile(r"NPT average density target from final window:\s*([-+0-9.eE]+)")


def parse_lammps_log(text: str) -> dict:
    """Thermo blocks, loop-time lines, speed lines, error and warning lines, and the
    deck's printed final-window density, from a LAMMPS log or screen file."""
    blocks, loops, perf, errors, warnings, dens = [], [], [], [], [], []
    cur = None
    wall = None
    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            continue
        if s.startswith("ERROR"):
            errors.append(s)
        if s.startswith("WARNING"):
            warnings.append(s)
        if s.startswith("Total wall time:"):
            wall = s.split(":", 1)[1].strip()
        if s.startswith("Loop time of"):
            m = _LOOP_RE.match(s)
            if m:
                loops.append({"seconds": float(m.group(1)), "procs": int(m.group(2)),
                              "steps": int(m.group(3)), "atoms": int(m.group(4))})
            if cur is not None:
                cur["complete"] = True
                blocks.append(cur)
                cur = None
            continue
        if s.startswith("Performance:"):
            m = _PERF_RE.search(s)
            if m:
                perf.append(float(m.group(1)))
            continue
        m = _DENS_RE.search(s)
        if m and not s.startswith("print"):
            try:
                dens.append(float(m.group(1)))
            except ValueError:
                pass
            continue
        toks = s.split()
        if toks[0] == "Step" and len(toks) >= 2 and not any(_isnum(t) for t in toks):
            if cur is not None:
                cur["complete"] = False
                blocks.append(cur)
            cur = {"header": toks, "rows": [], "raw": [], "complete": False}
            continue
        if cur is not None and len(toks) == len(cur["header"]) and all(_isnum(t) for t in toks):
            cur["rows"].append([float(t) for t in toks])
            cur["raw"].append(raw)
    if cur is not None:
        blocks.append(cur)
    return {"blocks": blocks, "loops": loops, "performance": perf, "errors": errors,
            "warnings": warnings, "density_prints": dens, "total_wall_time": wall}


def parse_density_file(text: str) -> list:
    rows = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        if len(parts) != 2:
            raise ParseError("a density row must be a step and one value")
        rows.append((int(parts[0]), float(parts[1])))
    return rows


_SECTIONS = {"Masses", "Atoms", "Velocities", "Bonds", "Angles", "Dihedrals", "Impropers",
             "Pair Coeffs", "PairIJ Coeffs", "Bond Coeffs", "Angle Coeffs", "Dihedral Coeffs",
             "Improper Coeffs"}


def parse_lammps_data(text: str) -> dict:
    """Header counts, box, masses and per-atom types from a LAMMPS data file;
    then the density by hand: total mass over box volume, in g/cm3."""
    lines = text.splitlines()
    n_atoms = None
    box = {}
    masses, atom_types = {}, []
    section = None
    style_hint = None
    for raw in lines[1:]:
        s = raw.split("#", 1)[0].strip()
        hint = raw.split("#", 1)[1].strip() if "#" in raw else ""
        if not s:
            continue
        if s in _SECTIONS:
            section = s
            if s == "Atoms" and hint:
                style_hint = hint
            continue
        if section is None:
            m = re.match(r"^(\d+)\s+atoms$", s)
            if m:
                n_atoms = int(m.group(1))
                continue
            m = re.match(r"^([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+(xlo xhi|ylo yhi|zlo zhi)$", s)
            if m:
                box[m.group(3)] = (float(m.group(1)), float(m.group(2)))
                continue
            if s.endswith("xy xz yz"):
                raise ParseError("tilted boxes are not expected from this builder")
            continue
        parts = s.split()
        if section == "Masses":
            masses[int(parts[0])] = float(parts[1])
        elif section == "Atoms":
            if style_hint and style_hint != "full":
                raise ParseError(f"atom style {style_hint!r}, expected full")
            atom_types.append(int(parts[2]))
    if n_atoms is None or len(box) != 3:
        raise ParseError("the data file header lacks the atom count or the box")
    if len(atom_types) != n_atoms:
        raise ParseError(f"the Atoms section holds {len(atom_types)} rows; the header says {n_atoms}")
    missing = sorted(set(atom_types) - set(masses))
    if missing:
        raise ParseError(f"atom types without a mass: {missing}")
    total_mass = sum(masses[t] for t in atom_types)
    vol = 1.0
    for k in ("xlo xhi", "ylo yhi", "zlo zhi"):
        lo, hi = box[k]
        vol *= (hi - lo)
    return {"n_atoms": n_atoms, "box": box, "volume_A3": vol, "total_mass_amu": total_mass,
            "density_g_cm3": total_mass / vol * AMU_PER_A3_TO_G_PER_CM3, "n_atom_types": len(masses)}


def parse_builder_metadata(text: str) -> dict:
    d = json.loads(text)
    need = ("n_molecules", "atoms_per_molecule", "net_charge_per_molecule", "density_g_cm3", "smiles")
    missing = [k for k in need if k not in d]
    if missing:
        raise ParseError(f"builder metadata lacks {missing}")
    return d


def parse_lmp_help(text: str) -> dict:
    version = None
    packages, accel = [], []
    lines = text.splitlines()
    for i, raw in enumerate(lines):
        m = re.search(r"Large-scale Atomic/Molecular Massively Parallel Simulator - (.+)$", raw)
        if m and version is None:
            version = m.group(1).strip()
        if raw.strip() == "Installed packages:":
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            while j < len(lines) and lines[j].strip():
                packages.extend(lines[j].split())
                j += 1
        if raw.strip() == "Accelerator configuration:":
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            while j < len(lines) and lines[j].strip():
                accel.append(lines[j].strip())
                j += 1
    return {"version": version, "packages": packages, "accelerators": accel}


def parse_uptime(text: str) -> float:
    parts = text.split()
    if not parts:
        raise ParseError("empty uptime text")
    v = float(parts[0])
    if not math.isfinite(v) or v < 0:
        raise ParseError("uptime is not a finite non-negative number")
    return v


def read_uptime_s() -> float:
    return parse_uptime(Path("/proc/uptime").read_text())


def parse_positive_number(raw, name: str) -> Fraction:
    if raw is None or str(raw).strip() == "":
        raise BudgetError(f"{name} is missing")
    try:
        d = Decimal(str(raw).strip())
    except InvalidOperation:
        raise BudgetError(f"{name} is not a number: {raw!r}")
    if not d.is_finite():
        raise BudgetError(f"{name} is not a finite number: {raw!r}")
    if d <= 0:
        raise BudgetError(f"{name} is not above zero: {raw!r}")
    return Fraction(d)


# ---------------------------------------------------------------------------
# Budget and clock arithmetic (exact fractions)
# ---------------------------------------------------------------------------
def time_limit_h(price: Fraction, budget: Fraction) -> Fraction:
    return min(Fraction(18) / price, budget / price - Fraction(3, 4))


def remote_timeout_s(t_h: Fraction) -> int:
    return math.floor((t_h + Fraction(1, 2)) * 3600)


def worst_case_usd(price: Fraction, t_h: Fraction) -> Fraction:
    return price * (t_h + Fraction(1, 2) + Fraction(1, 4))


def clock_allows(uptime_h: float, mean_wave_h, t_h: float) -> bool:
    return mean_wave_h is None or (uptime_h + mean_wave_h) <= (t_h - SPARE_H)


# ---------------------------------------------------------------------------
# Trajectory analysis (plain Python and numpy, same arithmetic)
# ---------------------------------------------------------------------------
def frame_times_ps(frames, dt_fs: float):
    """Time of each frame from its step number times the run's own timestep."""
    return [step * dt_fs / 1000.0 for step, _ in frames]


def spacing_check(frames, dt_fs: float) -> dict:
    t = frame_times_ps(frames, dt_fs)
    d = [b - a for a, b in zip(t, t[1:])]
    ok = bool(d) and all(abs(x - FRAME_PS) <= 1e-9 for x in d)
    return {"passed": ok, "spacing_ps_min": min(d) if d else None, "spacing_ps_max": max(d) if d else None,
            "n_frames": len(t), "timestep_fs": dt_fs,
            "rule": "frame time = step number x this run's timestep; every spacing must be 1.000 ps"}


def ols(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx == 0:
        return None, None
    b = sxy / sxx
    return b, my - b * mx


def fit_msd(msd, lo_ps: float, hi_ps: float) -> dict:
    """D from the linear fit, and the log-log slope, over whole-ps lags lo..hi."""
    m_lo, m_hi = int(round(lo_ps / FRAME_PS)), int(round(hi_ps / FRAME_PS))
    lags = list(range(m_lo, m_hi + 1))
    xs = [m * FRAME_PS for m in lags]
    ys = [msd[m] for m in lags]
    slope, icpt = ols(xs, ys)
    out = {"lag_ps": [lo_ps, hi_ps], "n_lags": len(lags), "D_A2_per_ps": None, "intercept_A2": icpt,
           "loglog_slope": None}
    if slope is not None:
        out["D_A2_per_ps"] = slope / 6.0
    if all(y > 0 for y in ys):
        ls, _ = ols([math.log(x) for x in xs], [math.log(y) for y in ys])
        out["loglog_slope"] = ls
    return out


def remove_drift_plain(vals_list, n_mol: int):
    out = []
    for v in vals_list:
        cx = sum(v[3 * i] for i in range(n_mol)) / n_mol
        cy = sum(v[3 * i + 1] for i in range(n_mol)) / n_mol
        cz = sum(v[3 * i + 2] for i in range(n_mol)) / n_mol
        w = [0.0] * (3 * n_mol)
        for i in range(n_mol):
            w[3 * i], w[3 * i + 1], w[3 * i + 2] = v[3 * i] - cx, v[3 * i + 1] - cy, v[3 * i + 2] - cz
        out.append(w)
    return out


def msd_plain(vals_list, n_mol: int, max_lag: int):
    """Mean over molecules and all time origins of the squared 3-D displacement."""
    nf = len(vals_list)
    out = [0.0] * (max_lag + 1)
    for m in range(1, max_lag + 1):
        tot, cnt = 0.0, nf - m
        for t in range(cnt):
            a, b = vals_list[t], vals_list[t + m]
            tot += sum((b[k] - a[k]) ** 2 for k in range(3 * n_mol))
        out[m] = tot / (cnt * n_mol)
    return out


def max_jump_plain(vals_list, n_mol: int) -> float:
    best = 0.0
    for a, b in zip(vals_list, vals_list[1:]):
        for i in range(n_mol):
            d2 = (b[3 * i] - a[3 * i]) ** 2 + (b[3 * i + 1] - a[3 * i + 1]) ** 2 + (b[3 * i + 2] - a[3 * i + 2]) ** 2
            if d2 > best:
                best = d2
    return math.sqrt(best)


def frozen_count_plain(vals_list, n_mol: int) -> int:
    first = vals_list[0]
    frozen = 0
    for i in range(n_mol):
        if all(v[3 * i] == first[3 * i] and v[3 * i + 1] == first[3 * i + 1] and v[3 * i + 2] == first[3 * i + 2]
               for v in vals_list):
            frozen += 1
    return frozen


def msd_numpy(X, max_lag: int):
    """Same arithmetic as msd_plain, by fast Fourier transform. X: (frames, molecules, 3)."""
    import numpy as np
    nf, n_mol, _ = X.shape
    y = (X - X[0]).reshape(nf, n_mol * 3)
    nfft = 1 << int(2 * nf - 1).bit_length()
    fy = np.fft.rfft(y, n=nfft, axis=0)
    ac = np.fft.irfft(fy * np.conj(fy), n=nfft, axis=0)[:max_lag + 1]
    sq = y * y
    csum = np.concatenate([np.zeros((1, y.shape[1])), np.cumsum(sq, axis=0)], axis=0)
    m = np.arange(max_lag + 1)
    head = csum[nf - m]
    tail = csum[nf] - csum[m]
    s = head + tail - 2.0 * ac
    per_col = s / (nf - m)[:, None]
    msd = per_col.reshape(max_lag + 1, n_mol, 3).sum(axis=2).mean(axis=1)
    msd[0] = 0.0
    return [float(v) for v in msd]


def analyze_frames(frames, n_mol: int, dt_fs: float, window_ps, fits: dict, backend: str = "plain") -> dict:
    """Window selection, drift removal, MSD over all time origins, and the fits.
    Also the degeneracy checks that need the positions themselves."""
    issues = []
    res = {"issues": issues, "fits": {}, "msd": None, "n_frames_window": 0}
    if len(frames) < 2:
        issues.append("fewer than two centre frames")
        return res
    if any(len(v) != 3 * n_mol for _, v in frames):
        issues.append("a centre frame does not hold one row per molecule")
        return res
    steps = [s for s, _ in frames]
    if any(b <= a for a, b in zip(steps, steps[1:])):
        issues.append("frame step numbers do not increase")
        return res
    sc = spacing_check(frames, dt_fs)
    res["spacing"] = sc
    if not sc["passed"]:
        issues.append(f"frame spacing is not 1.000 ps (from {sc['spacing_ps_min']} to {sc['spacing_ps_max']} ps)")
        return res
    t = frame_times_ps(frames, dt_fs)
    lo, hi = window_ps
    idx = [i for i, x in enumerate(t) if lo - 1e-6 <= x <= hi + 1e-6]
    expected = int(round((hi - lo) / FRAME_PS)) + 1
    if len(idx) != expected or abs(t[idx[0]] - lo) > 1e-6 or abs(t[idx[-1]] - hi) > 1e-6:
        issues.append(f"the analysis window {lo:g}-{hi:g} ps is not fully covered")
        return res
    res["n_frames_window"] = len(idx)
    all_vals = [v for _, v in frames]
    if any(not math.isfinite(x) for v in all_vals for x in v):
        issues.append("a centre position is not a finite number")
        return res
    max_lag = max(int(round(h / FRAME_PS)) for _, h in fits.values())
    if backend == "numpy":
        import numpy as np
        X_all = np.asarray([np.frombuffer(v, dtype=float) if isinstance(v, array) else np.asarray(v, dtype=float)
                            for v in all_vals]).reshape(len(all_vals), n_mol, 3)
        jumps = np.linalg.norm(np.diff(X_all, axis=0), axis=2)
        res["max_one_frame_jump_A"] = float(jumps.max())
        X = X_all[idx[0]:idx[-1] + 1]
        rng = X.max(axis=0) - X.min(axis=0)
        res["frozen_molecules"] = int((rng.max(axis=1) == 0).sum())
        Xd = X - X.mean(axis=1, keepdims=True)
        msd = msd_numpy(Xd, max_lag)
    else:
        res["max_one_frame_jump_A"] = max_jump_plain(all_vals, n_mol)
        win = all_vals[idx[0]:idx[-1] + 1]
        res["frozen_molecules"] = frozen_count_plain(win, n_mol)
        msd = msd_plain(remove_drift_plain(win, n_mol), n_mol, max_lag)
    res["msd"] = msd
    if res["max_one_frame_jump_A"] > TELEPORT_A:
        issues.append(f"a molecule centre jumped {res['max_one_frame_jump_A']:.3f} angstroms in one frame "
                      f"(limit {TELEPORT_A:g}): lost periodic image or blow-up")
    if res["frozen_molecules"] > 0:
        issues.append(f"{res['frozen_molecules']} molecule centres never move in the window")
    for name, (a, b) in fits.items():
        f = fit_msd(msd, a, b)
        res["fits"][name] = f
        if f["D_A2_per_ps"] is None or not f["D_A2_per_ps"] > 0:
            issues.append(f"the {name} fit gives a D that is not positive")
        if f["loglog_slope"] is None:
            issues.append(f"the MSD is not positive at every lag of the {name} fit")
    return res


def join_check(frames1, frames2, n_mol: int) -> dict:
    """The largest one-frame jump across the 1.0 ns join must not exceed the
    largest one-frame jump inside either part (gate item I5, part 2)."""
    last_step, last_vals = frames1[-1]
    after = [(s, v) for s, v in frames2 if s > last_step]
    dup = [(s, v) for s, v in frames2 if s == last_step]
    if not after:
        return {"passed": False, "reason": "the second part has no frame after the join"}
    join = max_jump_plain([last_vals, after[0][1]], n_mol)
    inner1 = max_jump_plain([v for _, v in frames1], n_mol)
    inner2 = max_jump_plain([v for _, v in frames2], n_mol)
    out = {"join_jump_A": join, "inner_max_part1_A": inner1, "inner_max_part2_A": inner2,
           "passed": join <= max(inner1, inner2), "join_step": last_step}
    if dup:
        out["duplicate_frame_difference_A"] = max_jump_plain([last_vals, dup[0][1]], n_mol)
    return out


def merge_parts(frames1, frames2):
    last = frames1[-1][0]
    return list(frames1) + [(s, v) for s, v in frames2 if s > last]


def stage3_thermo(block, dt_fs: float, kind: str) -> dict:
    """Mean temperature, and the report-only density readout, from the last thermo block."""
    out = {"temperature_mean_K": None, "density_mean_0p20_0p45_ns": None,
           "density_mean_last_250_ps_thermo": None, "n_rows": 0}
    if not block or not block["rows"]:
        return out
    hdr = block["header"]
    try:
        i_s, i_t, i_d = hdr.index("Step"), hdr.index("Temp"), hdr.index("Density")
    except ValueError:
        return out
    rows = block["rows"]
    out["n_rows"] = len(rows)
    out["temperature_mean_K"] = mean(r[i_t] for r in rows)
    times = [(r[i_s] * dt_fs / 1000.0, r[i_d]) for r in rows]
    early = [d for t, d in times if READOUT_EARLY_PS[0] - 1e-6 <= t <= READOUT_EARLY_PS[1] + 1e-6]
    end = STAGE3_END_PS[kind]
    late = [d for t, d in times if end - DENSITY_LAST_PS - 1e-6 <= t <= end + 1e-6]
    if kind != "extension":
        out["density_mean_0p20_0p45_ns"] = mean(early)
    out["density_mean_last_250_ps_thermo"] = mean(late)
    return out


# ---------------------------------------------------------------------------
# Decks: the design's listed edits, the continuation deck, the zero-step deck
# ---------------------------------------------------------------------------
DECK_REMOVE_FIRST = "variable        rho_now equal density"
DECK_REMOVE_LAST = "unfix           eq_nvt"
DECK_RUN_NPT = "run             ${npt_steps}"
COM_BLOCK = [
    "# Edit listed in the design (run cp1): write the unwrapped centre of every molecule every 1 ps.",
    "variable        com_every             index 500",
    "compute         cp1_mol all chunk/atom molecule",
    "compute         cp1_com all com/chunk cp1_mol",
    "fix             cp1_com_out all ave/time ${com_every} 1 ${com_every} c_cp1_com[*] "
    "file ${system_dir}/com_npt_T${T}K_run${run_id}.dat mode vector",
]


def edit_main_deck(text: str) -> str:
    """Apply the two text edits the design lists. Step counts and the timestep are
    set on the command line through the deck's own variables, not here."""
    lines = text.split("\n")
    first = [i for i, ln in enumerate(lines) if ln.rstrip() == DECK_REMOVE_FIRST]
    last = [i for i, ln in enumerate(lines) if ln.rstrip() == DECK_REMOVE_LAST]
    run = [i for i, ln in enumerate(lines) if ln.rstrip() == DECK_RUN_NPT]
    if len(first) != 1 or len(last) != 1 or len(run) != 1:
        raise DeckEditError("the deck anchors are not each present exactly once")
    if not run[0] < first[0] < last[0]:
        raise DeckEditError("the deck anchors are out of the expected order")
    new = lines[:run[0]] + COM_BLOCK + lines[run[0]:first[0]] + lines[last[0] + 1:]
    return "\n".join(new)


EXTENSION_DECK = """# Continuation of the constant-pressure stage for 1 ns more (rerun 1 only), written for run cp1.
# Restart handling follows the committed tdm_continue.in. The stage repeats the committed
# equilibrate.in constant-pressure stage: same thermostat, barostat, constraints and density
# window, and the same centre output as the edited main deck. Step numbers continue.

variable        system_dir            index .
variable        restart_file          index equilibrated_T313.15K.restart
variable        T                     index 313.15
variable        P                     index 1.0
variable        run_id                index 1
variable        timestep_fs           index 2.0
variable        thermo_every          index 5000
variable        tdamp                 index 100.0
variable        pdamp                 index 1000.0
variable        ext_steps             index 500000
variable        density_avg_start     index 875000
variable        density_sample_every  index 50
variable        density_sample_repeat index 2500
variable        density_sample_freq   index 125000
variable        shake_tol             index 0.0001
variable        shake_iter            index 20
variable        shake_order           index 0
variable        com_every             index 500

log             ${system_dir}/log_extension_T${T}K_run${run_id}.out

read_restart    ${restart_file}
kspace_style    pppm 1.0e-5
include         ${system_dir}/in.settings
timestep        ${timestep_fs}

thermo          ${thermo_every}
thermo_style    custom step temp press density vol lx ly lz pe etotal

fix             constrain_h all shake ${shake_tol} ${shake_iter} ${shake_order} m 1.008

variable        rho equal density
fix             npt_density all ave/time ${density_sample_every} ${density_sample_repeat} ${density_sample_freq} v_rho &
                file ${system_dir}/density_npt_ext_T${T}K_run${run_id}.dat ave one start ${density_avg_start}
fix             eq_npt all npt temp ${T} ${T} ${tdamp} iso ${P} ${P} ${pdamp} nreset 1000
compute         cp1_mol all chunk/atom molecule
compute         cp1_com all com/chunk cp1_mol
fix             cp1_com_out all ave/time ${com_every} 1 ${com_every} c_cp1_com[*] file ${system_dir}/com_ext_T${T}K_run${run_id}.dat mode vector
run             ${ext_steps}
unfix           eq_npt

variable        rho_target equal $(f_npt_density:%.12g)
print           "NPT average density target from final window: ${rho_target} g/cm^3"
unfix           npt_density
unfix           constrain_h
print           "Extension done: steps=${ext_steps}"
"""

ZERO_STEP_DECK = """# Zero-step read of one built box (pre-launch check, written for run cp1). Nothing moves.
variable        system_dir index .
include         ${system_dir}/in.init
read_data       ${system_dir}/in.data
include         ${system_dir}/in.settings
thermo_style    custom step atoms density vol pe
run             0
"""

TRIAL_VARS = {"pushoff_steps": 100, "settle_steps": 100, "npt_steps": 1000, "density_avg_start": 500,
              "density_sample_every": 10, "density_sample_repeat": 50, "density_sample_freq": 500,
              "com_every": 250, "timestep_fs": 2.0, "relax_dt": 0.5}


def cell_file_names(kind: str, rerun: int) -> dict:
    if kind == "extension":
        return {"log": f"log_extension_T{T_STR}K_run{rerun}.out", "com": f"com_ext_T{T_STR}K_run{rerun}.dat",
                "density": f"density_npt_ext_T{T_STR}K_run{rerun}.dat"}
    return {"log": f"log_equilibrate_T{T_STR}K_run{rerun}.out", "com": f"com_npt_T{T_STR}K_run{rerun}.dat",
            "density": f"density_npt_T{T_STR}K_run{rerun}.dat", "restart": f"equilibrated_T{T_STR}K.restart"}


def _var_text(v) -> str:
    if isinstance(v, float):
        return repr(v)
    return str(v)


def engine_vars(kind: str, rerun: int, system_dir, restart_file=None, overrides=None) -> list:
    v = {"system_dir": str(system_dir), "T": T_STR, "run_id": str(rerun)}
    for k, val in RUN_KINDS[kind].items():
        v[k] = _var_text(val)
    for k, val in (overrides or {}).items():
        v[k] = _var_text(val)
    if restart_file is not None:
        v["restart_file"] = str(restart_file)
    out = []
    for k, val in v.items():
        out += ["-var", k, val]
    return out


# ---------------------------------------------------------------------------
# Degeneracy checks on one finished run's outputs
# ---------------------------------------------------------------------------
def degenerate_engine(rc, log: dict, kind: str, stopped: bool = False) -> list:
    issues = []
    if stopped:
        issues.append("the run was stopped before it finished")
    elif rc is None:
        issues.append("the run left no exit code")
    elif rc != 0:
        issues.append(f"the engine exited with code {rc}")
    if log["errors"]:
        issues.append("the engine log holds an error line: " + log["errors"][0][:200])
    want = 1 if kind == "extension" else 4
    if len(log["loops"]) != want:
        issues.append(f"the engine log shows {len(log['loops'])} finished loops; expected {want}")
    return issues


def degenerate_density(print_value, file_rows, end_step: int) -> tuple:
    issues = []
    file_final = next((v for s, v in file_rows if s == end_step), None)
    value = print_value
    if value is None or not math.isfinite(value) or value <= 0:
        issues.append("no final-window density was reported")
        value = None
    elif file_final is not None and abs(file_final / value - 1.0) > 1e-4:
        issues.append("the density file and the engine log disagree on the final-window density")
    elif file_final is None:
        issues.append(f"the density file has no row at step {end_step}")
    return value, issues


def degenerate_temperature(temp_mean) -> list:
    if temp_mean is None or not math.isfinite(temp_mean):
        return ["no constant-pressure temperature readings were found"]
    if abs(temp_mean - T_KELVIN) > TEMP_TOL_K:
        return [f"the mean temperature {temp_mean:.2f} K is more than {TEMP_TOL_K:g} K from {T_KELVIN} K"]
    return []


def degenerate_com(parsed: dict, n_mol: int, end_step: int) -> list:
    issues = []
    if parsed is None:
        return ["the centre file is missing or unreadable"]
    if parsed["truncated_last_frame"]:
        issues.append("the centre file ends in a cut-off frame")
    if parsed["rows_per_frame"] and parsed["rows_per_frame"] != [n_mol]:
        issues.append(f"centre frames hold {parsed['rows_per_frame']} rows; expected {n_mol}")
    if not parsed["frames"]:
        issues.append("the centre file holds no complete frame")
    elif parsed["frames"][-1][0] != end_step:
        issues.append(f"the last centre frame is at step {parsed['frames'][-1][0]}; expected {end_step}")
    return issues


# ---------------------------------------------------------------------------
# The scheduler: tiers, waves, the clock rule, the speed probe, the time limit
# ---------------------------------------------------------------------------
def run_spec(mol: str, rerun: int, kind: str, tier: int) -> dict:
    return {"mol": mol, "rerun": rerun, "kind": kind, "tier": tier, "attempt": 1}


def build_tiers():
    t1 = [run_spec(m, 1, "main", 1) for m in MOL_IDS] + [run_spec(m, 2, "main", 1) for m in MOL_IDS]
    t2 = [run_spec(m, 1, "extension", 2) for m in MOL_IDS]
    t3 = [run_spec(m, 3, "main", 3) for m in MOL_IDS]
    t4 = [run_spec(TIMESTEP_MOL, 1, "timestep_1fs", 4)]
    return [(1, t1), (2, t2), (3, t3), (4, t4)]


def run_key(run) -> tuple:
    return (run["mol"], run["rerun"], run["kind"])


def cell_of(run) -> dict:
    return {"stage": "cell", "molecule": run["mol"], "rerun": run["rerun"], "kind": run["kind"],
            "attempt": run["attempt"]}


def run_name(run) -> str:
    return f"{run['mol']} rerun {run['rerun']} {run['kind']} attempt {run['attempt']}"


def _probe_check(handles, done, engine, last_s3, elapsed_s, uptime_h, t_h):
    ready, steps, per_run = True, [], []
    for i, (run, h) in enumerate(handles):
        if run["kind"] != "main":
            continue
        k = run_key(run)
        s3 = engine.progress(h)
        if s3 is not None:
            last_s3[k] = max(last_s3.get(k, -1), s3)
        cur = last_s3.get(k, -1)
        if cur >= PROBE_STAGE3_STEPS:
            steps.append(PRE_STAGE3_STEPS["main"] + cur)
            per_run.append({"run": run_name(run), "steps_done": PRE_STAGE3_STEPS["main"] + cur})
        elif i in done:
            per_run.append({"run": run_name(run), "excluded": "ended before the probe point"})
        else:
            ready = False
    if not ready:
        return None
    if not steps or elapsed_s <= 0:
        return {"state": "deferred", "per_run": per_run,
                "note": "no run of this wave reached the probe point; the probe moves to the next tier-1 wave"}
    rate = sum(steps) / elapsed_s
    proj = uptime_h + PROBE_REMAINING_STEPS / rate / 3600.0
    fits = proj <= t_h - SPARE_H
    return {"state": "measured", "rate_steps_per_s": rate, "guessed_rate_steps_per_s": GUESSED_RATE,
            "ratio_to_guess": rate / GUESSED_RATE, "steps_counted": sum(steps), "elapsed_s": elapsed_s,
            "uptime_h_at_probe": uptime_h, "remaining_tier1_steps": PROBE_REMAINING_STEPS,
            "projected_tier1_end_h": proj, "limit_h": t_h, "spare_h": SPARE_H, "fits": fits,
            "per_run": per_run}


def run_schedule(tiers, engine, clock, t_h: float, *, poll_s: float, on_cell_done, on_probe=None,
                 on_wave_done=None, log=print) -> dict:
    """Run the tiers in waves under the clock rule, the speed probe and the time limit."""
    wave_hours, tiers_done, waves = [], [], []
    state = {"probe": {"state": "pending"}}
    last_s3 = {}

    def finish(reason, tier_no=None):
        return {"stop_reason": reason, "tiers_done": list(tiers_done), "tier1_complete": 1 in tiers_done,
                "waves": waves, "probe": state["probe"], "uptime_h_end": clock.uptime_h(),
                "stopped_in_tier": tier_no, "limit_h": t_h}

    for tier_no, runs in tiers:
        queue = [dict(r) for r in runs]
        retried, failed = set(), []
        while queue:
            wave = queue[:WAVE_SIZE]
            del queue[:WAVE_SIZE]
            up = clock.uptime_h()
            mean_h = (sum(wave_hours) / len(wave_hours)) if wave_hours else None
            if up >= t_h:
                return finish(f"time limit reached before a tier-{tier_no} wave could start "
                              f"(uptime {up:.3f} h, limit {t_h:.3f} h)", tier_no)
            if not clock_allows(up, mean_h, t_h):
                return finish(f"clock rule: the next tier-{tier_no} wave is projected to end at "
                              f"{up + mean_h:.3f} h, past the limit {t_h:.3f} h less 15 minutes", tier_no)
            t0 = clock.now()
            handles = [(run, engine.start(run)) for run in wave]
            log(f"[wave] tier {tier_no}: {', '.join(run_name(r) for r in wave)} (uptime {up:.3f} h)")
            done, stop_reason = {}, None
            while len(done) < len(handles):
                clock.sleep(poll_s)
                for i, (run, h) in enumerate(handles):
                    if i not in done:
                        rc = engine.poll(h)
                        if rc is not None:
                            done[i] = rc
                if (tier_no == 1 and state["probe"]["state"] in ("pending", "deferred")):
                    res = _probe_check(handles, done, engine, last_s3, clock.now() - t0, clock.uptime_h(), t_h)
                    if res is not None and not (res["state"] == "deferred" and len(done) < len(handles)):
                        state["probe"] = res
                        if on_probe:
                            on_probe(res)
                        if res["state"] == "measured" and not res["fits"]:
                            stop_reason = (f"speed probe: tier 1 is projected to end at "
                                           f"{res['projected_tier1_end_h']:.3f} h, past the limit "
                                           f"{t_h:.3f} h less 15 minutes; measured "
                                           f"{res['rate_steps_per_s']:.1f} steps/s against the guessed 530")
                            break
                if len(done) < len(handles) and clock.uptime_h() >= t_h:
                    stop_reason = f"time limit {t_h:.3f} h reached during a tier-{tier_no} wave"
                    break
            wave_rec = {"tier": tier_no, "runs": [run_name(r) for r in wave], "uptime_h_start": up,
                        "duration_h": (clock.now() - t0) / 3600.0}
            if stop_reason:
                for i, (run, h) in enumerate(handles):
                    if i in done:
                        on_cell_done(run, h, done[i], len(wave), False)
                    else:
                        engine.kill(h)
                        on_cell_done(run, h, None, len(wave), True)
                wave_rec["stopped"] = stop_reason
                waves.append(wave_rec)
                return finish(stop_reason, tier_no)
            wave_hours.append(wave_rec["duration_h"])
            for i, (run, h) in enumerate(handles):
                res = on_cell_done(run, h, done[i], len(wave), False)
                if not res.get("ok"):
                    k = run_key(run)
                    if k not in retried:
                        retried.add(k)
                        queue.append(dict(run, attempt=run["attempt"] + 1))
                    else:
                        failed.append(run_name(run))
            waves.append(wave_rec)
            if on_wave_done:
                on_wave_done(wave_rec, list(tiers_done))
        if failed:
            return finish(f"tier {tier_no} did not finish: {', '.join(failed)} failed twice", tier_no)
        tiers_done.append(tier_no)
    return finish(None)


class RealClock:
    def now(self):
        return time.monotonic()

    def uptime_h(self):
        return read_uptime_s() / 3600.0

    def sleep(self, s):
        time.sleep(s)


class RealEngine:
    """Starts LAMMPS runs as separate processes and watches them."""

    def __init__(self, lmp, switches, env_extra, bundle: Path, work: Path):
        self.lmp, self.switches, self.env_extra = str(lmp), list(switches), dict(env_extra)
        self.bundle, self.work = Path(bundle), Path(work)
        self.finished_dirs = {}

    def start(self, run):
        slug = provenance().cell_slug(cell_of(run))
        rundir = self.work / slug
        if rundir.exists():
            shutil.rmtree(rundir)
        rundir.mkdir(parents=True)
        box_rerun = run["rerun"] if run["kind"] == "main" else 1
        box = self.bundle / run["mol"] / f"pack{PACK_SEEDS[box_rerun]}"
        for f in ("in.init", "in.settings", "in.data"):
            shutil.copy2(box / f, rundir / f)
        restart = None
        if run["kind"] == "extension":
            part1 = self.finished_dirs.get((run["mol"], 1, "main"))
            restart = (part1 / cell_file_names("main", 1)["restart"]) if part1 else None
            if restart is None or not restart.exists():
                (rundir / "screen.out").write_text("ERROR: rerun 1 left no restart file to continue from\n")
                return {"run": run, "proc": None, "rc": 97, "rundir": rundir, "cmd": [], "t0": time.monotonic(),
                        "part1": part1}
            shutil.copy2(self.bundle / "deck_extension_cp1.in", rundir / "deck.in")
        else:
            shutil.copy2(self.bundle / "deck_main_cp1.in", rundir / "deck.in")
        cmd = [self.lmp] + self.switches + ["-in", "deck.in"] + \
            engine_vars(run["kind"], run["rerun"], rundir, restart) + ["-log", "log.lammps"]
        env = os.environ.copy()
        env.update(self.env_extra)
        fh = open(rundir / "screen.out", "wb")
        proc = subprocess.Popen(cmd, cwd=rundir, stdout=fh, stderr=subprocess.STDOUT, env=env,
                                start_new_session=True)
        return {"run": run, "proc": proc, "fh": fh, "rundir": rundir, "cmd": cmd, "t0": time.monotonic(),
                "part1": self.finished_dirs.get((run["mol"], 1, "main"))}

    def poll(self, h):
        if h["proc"] is None:
            return h["rc"]
        rc = h["proc"].poll()
        if rc is not None and "t_end" not in h:
            h["t_end"] = time.monotonic()
        if rc is not None and h.get("fh"):
            h["fh"].close()
            h["fh"] = None
        return rc

    def progress(self, h):
        if h["proc"] is None or h["run"]["kind"] != "main":
            return None
        return last_header_step(h["rundir"] / cell_file_names("main", h["run"]["rerun"])["com"])

    def kill(self, h):
        p = h.get("proc")
        if p is None or p.poll() is not None:
            return
        try:
            os.killpg(p.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        try:
            p.wait(timeout=20)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            p.wait()
        if h.get("fh"):
            h["fh"].close()
            h["fh"] = None


# ---------------------------------------------------------------------------
# Processing one finished run into its cell record
# ---------------------------------------------------------------------------
def copy_raw(rundir: Path, outdir: Path, slug: str, names: dict) -> dict:
    dest = outdir / "raw" / slug
    dest.mkdir(parents=True, exist_ok=True)
    out = {}
    for name in (names["log"], "log.lammps", "screen.out", names["density"], "deck.in"):
        src = rundir / name
        if src.exists():
            shutil.copy2(src, dest / name)
            out[name] = {"path": rel(dest / name), "sha256": sha256_file(dest / name)}
    src = rundir / names["com"]
    if src.exists():
        gz = dest / (names["com"] + ".gz")
        with open(src, "rb") as fi, gzip.open(gz, "wb", compresslevel=6) as fo:
            shutil.copyfileobj(fi, fo)
        out[names["com"]] = {"path": rel(gz), "sha256_uncompressed": sha256_file(src), "sha256_gz": sha256_file(gz)}
    return out


def process_cell(run, rc, *, handle, outdir: Path, wave_size: int, engine_info: dict, stopped: bool,
                 backend: str = "numpy") -> dict:
    kind, mol, rr = run["kind"], run["mol"], run["rerun"]
    spec = RUN_KINDS[kind]
    dt = spec["timestep_fs"]
    n_mol = MOL[mol]["n_mol"]
    rundir = handle["rundir"]
    names = cell_file_names(kind, rr)
    wall_s = handle.get("t_end", time.monotonic()) - handle["t0"]
    issues = []
    log_path = rundir / names["log"]
    log_text = log_path.read_text(errors="replace") if log_path.exists() else ""
    screen = (rundir / "screen.out").read_text(errors="replace") if (rundir / "screen.out").exists() else ""
    if not log_text:
        issues.append("the deck's log file is missing")
    pl = parse_lammps_log(log_text + "\n" + screen if not log_text else log_text)
    if not log_text:
        pl_screen = pl
    else:
        pl_screen = parse_lammps_log(screen)
    pl["errors"] = sorted(set(pl["errors"]) | set(pl_screen["errors"]))
    issues += degenerate_engine(rc, pl, kind, stopped)
    dens_rows = []
    try:
        if (rundir / names["density"]).exists():
            dens_rows = parse_density_file((rundir / names["density"]).read_text())
    except ParseError as e:
        issues.append(f"the density file is unreadable: {e}")
    density, d_issues = degenerate_density(pl["density_prints"][-1] if pl["density_prints"] else None,
                                           dens_rows, STAGE3_END_STEP[kind])
    issues += d_issues
    thermo = stage3_thermo(pl["blocks"][-1] if pl["blocks"] else None, dt, kind)
    issues += degenerate_temperature(thermo["temperature_mean_K"])
    parsed = None
    com_path = rundir / names["com"]
    try:
        if com_path.exists():
            parsed = parse_com_file(com_path.read_text())
    except ParseError as e:
        issues.append(f"the centre file is malformed: {e}")
    issues += degenerate_com(parsed, n_mol, STAGE3_END_STEP[kind])
    values = {"status": None, "kind": kind, "molecule": mol, "molecule_name": MOL[mol]["name"], "rerun": rr,
              "attempt": run["attempt"], "tier": run["tier"], "timestep_fs": dt,
              "pack_seed": PACK_SEEDS[rr if kind == "main" else 1],
              "velocity_seed": velocity_seed(rr if kind != "extension" else 1),
              "engine_variables": RUN_KINDS[kind], "total_steps_planned": TOTAL_STEPS[kind],
              "acceleration_path": engine_info.get("path"), "command": handle.get("cmd"),
              "exit_code": rc, "stopped": stopped, "wall_seconds": wall_s, "wave_size": wave_size,
              "box_hours_share": wall_s / 3600.0 / max(1, wave_size), "n_molecules": n_mol,
              "loops": pl["loops"], "performance_timesteps_per_s": pl["performance"],
              "warning_lines": pl["warnings"][:50], "n_warning_lines": len(pl["warnings"]),
              "error_lines": pl["errors"][:20], "density_final_window_g_cm3": density,
              "density_file_rows": dens_rows, "thermo_stage": thermo,
              "thermo_last_block_raw": (pl["blocks"][-1]["raw"] if pl["blocks"] else []),
              "rerun_note": LABEL_RERUNS}
    msd_rows = []
    if parsed and parsed["frames"] and not stopped:
        try:
            if kind == "extension":
                p1dir = handle.get("part1")
                p1 = parse_com_file((p1dir / cell_file_names("main", 1)["com"]).read_text()) if p1dir else None
                if not p1 or not p1["frames"]:
                    issues.append("the first part of the extended run is missing")
                else:
                    jc = join_check(p1["frames"], parsed["frames"], n_mol)
                    values["join_check"] = jc
                    values["part1_run_dir"] = rel(p1dir)
                    res = analyze_frames(merge_parts(p1["frames"], parsed["frames"]), n_mol, dt,
                                         WINDOW_EXT_PS, FITS_EXT, backend)
                    issues += res["issues"]
                    values["fits"] = res["fits"]
                    values["max_one_frame_jump_A"] = res.get("max_one_frame_jump_A")
                    values["frozen_molecules"] = res.get("frozen_molecules")
                    if res["msd"]:
                        msd_rows = [{"lag_ps": m * FRAME_PS, "msd_A2": v} for m, v in enumerate(res["msd"])]
            else:
                if kind == "timestep_1fs":
                    values["frame_spacing_check"] = spacing_check(parsed["frames"], dt)
                res = analyze_frames(parsed["frames"], n_mol, dt, WINDOW_MAIN_PS, FITS_MAIN, backend)
                issues += res["issues"]
                values["fits"] = res["fits"]
                values["max_one_frame_jump_A"] = res.get("max_one_frame_jump_A")
                values["frozen_molecules"] = res.get("frozen_molecules")
                values["n_frames_window"] = res.get("n_frames_window")
                if res["msd"]:
                    msd_rows = [{"lag_ps": m * FRAME_PS, "msd_A2": v} for m, v in enumerate(res["msd"])]
        except Exception as e:  # an analysis failure is a degenerate cell, not a crash
            issues.append(f"the analysis failed: {type(e).__name__}: {e}")
            values["analysis_traceback"] = traceback.format_exc()[-2000:]
    fits = values.get("fits") or {}
    values["D_A2_per_ps"] = {k: f.get("D_A2_per_ps") for k, f in fits.items()}
    values["loglog_slope"] = {k: f.get("loglog_slope") for k, f in fits.items()}
    status = "stopped" if stopped else ("finished" if not issues else "degenerate")
    values["status"] = status
    values["issues"] = issues
    slug = provenance().cell_slug(cell_of(run))
    values["raw_files"] = copy_raw(rundir, outdir, slug, names)
    values["run_dir"] = rel(rundir)
    inputs = [describe(rundir / f) for f in ("in.data", "in.init", "in.settings", "deck.in")]
    write_record(outdir, cell=cell_of(run), inputs=inputs, metric="one simulation run: centres, MSD, D, density",
                 values=values, threshold={"temperature_tolerance_K": TEMP_TOL_K, "teleport_limit_A": TELEPORT_A},
                 decision_rule=("finished when the engine exits cleanly, every output parses, the centre frames "
                                "are complete and 1.000 ps apart, no centre jumps more than 10 angstroms in one "
                                "frame or never moves, the mean temperature is within 30 K of 313.15 K, and D "
                                "is positive; otherwise degenerate (repeated once) or stopped"),
                 decision=status.upper(), notes="; ".join(issues), rows=msd_rows)
    return {"ok": status == "finished", "status": status}


# ---------------------------------------------------------------------------
# Endpoints: pure arithmetic over cell records (standard library only)
# ---------------------------------------------------------------------------
def collect_cells(outdir) -> dict:
    """Latest finished attempt per (molecule, rerun, kind); else the latest attempt."""
    best = {}
    for p in sorted(Path(outdir).glob("*.json")):
        try:
            rec = json.loads(p.read_text())
        except Exception:
            continue
        if not is_record(rec) or rec["cell"].get("stage") != "cell":
            continue
        c = rec["cell"]
        key = (c["molecule"], int(c["rerun"]), c["kind"])
        fin = rec["values"].get("status") == "finished"
        rank = (1 if fin else 0, int(c.get("attempt", 1)))
        if key not in best or rank > best[key][0]:
            best[key] = (rank, rec, p)
    return {k: {"rec": v[1], "path": v[2]} for k, v in best.items()}


def finished_rec(cells, mol, rerun, kind="main"):
    c = cells.get((mol, rerun, kind))
    if c and c["rec"]["values"].get("status") == "finished":
        return c["rec"]
    return None


def msd_curve(rec) -> list:
    rows = rec.get("rows") or []
    return [r["msd_A2"] for r in sorted(rows, key=lambda r: r["lag_ps"])]


def main_table(cells, ref: dict, window: str = "main", reruns=RERUNS) -> dict:
    out = {}
    for m in MOL_IDS:
        recs = [(r, finished_rec(cells, m, r)) for r in reruns]
        recs = [(r, x) for r, x in recs if x is not None]
        if not recs:
            out[m] = None
            continue
        ds = [x["values"]["D_A2_per_ps"][window] for _, x in recs]
        dens = [x["values"]["density_final_window_g_cm3"] for _, x in recs]
        if any(not is_finite_number(v) for v in ds + dens):
            out[m] = None
            continue
        d, rho = mean(ds), mean(dens)
        out[m] = {"reruns": [r for r, _ in recs], "D_each": ds, "D_mean": d, "density_each": dens,
                  "density_mean": rho, "proxy_mPa_s": proxy_mpas(d, ref[m]["molar_mass_g_mol"], rho)}
    return out


def rho_vs_ref(values_by_mol: dict, ref: dict):
    if any(values_by_mol.get(m) is None for m in MOL_IDS):
        return None
    return spearman([values_by_mol[m] for m in MOL_IDS], [ref[m]["eta_ref_mPa_s"] for m in MOL_IDS])


def tier_status(cells) -> dict:
    t1 = all(finished_rec(cells, m, r) for m in MOL_IDS for r in (1, 2))
    t2 = all(finished_rec(cells, m, 1, "extension") for m in MOL_IDS)
    t3 = all(finished_rec(cells, m, 3) for m in MOL_IDS)
    t4 = finished_rec(cells, TIMESTEP_MOL, 1, "timestep_1fs") is not None
    return {"tier1": t1, "tier2": t2, "tier3": t3, "tier4": t4}


def e2_density_gate(tab, ref) -> dict:
    rows, complete, inside_all = [], True, True
    for m in MOL_IDS:
        t = tab.get(m)
        lo, hi = ref[m]["density_band_g_cm3"]
        if t is None:
            complete = False
            rows.append({"molecule": m, "density_mean": None, "band": [lo, hi], "inside": None})
            continue
        d = t["density_mean"]
        inside = lo <= d <= hi
        inside_all = inside_all and inside
        rows.append({"molecule": m, "name": ref[m]["name"], "density_each": t["density_each"], "density_mean": d,
                     "band": [lo, hi], "inside": inside, "paper": ref[m]["rho_paper_g_cm3"],
                     "vs_paper_pct": 100 * (d / ref[m]["rho_paper_g_cm3"] - 1),
                     "vs_reference_pct": 100 * (d / ref[m]["rho_ref_g_cm3"] - 1)})
    impl = None
    if complete:
        ge = next(r for r in rows if r["molecule"] == GLYCOL_ETHER)
        others = [r for r in rows if r["molecule"] != GLYCOL_ETHER]
        impl = {"glycol_ether_vs_reference_pct": ge["vs_reference_pct"],
                "glycol_ether_8_to_12_pct_below_reference": -12.0 <= ge["vs_reference_pct"] <= -8.0,
                "others_within_5_pct_of_reference": all(abs(r["vs_reference_pct"]) <= 5.0 for r in others)}
    if not complete:
        decision = "NOT_JUDGED"
    else:
        decision = "PASS" if inside_all else "FAIL"
    return {"decision": decision, "rows": rows, "implications_report_only": impl, "complete": complete}


def e3_decide(rho):
    if rho is None:
        return "NOT_JUDGED", []
    if rho >= RHO_PASS:
        return "PASS", [LABEL_D1_PASS]
    if rho < RHO_ABANDON:
        return "REFUTED_BELOW_ABANDON_LINE", [LABEL_ABANDON]
    return "REFUTED", [LABEL_D1_REFUTED]


def e8_decide(main_rho, best_free, margin):
    if main_rho is None or best_free is None:
        return "NOT_JUDGED", []
    if main_rho <= best_free:
        return "REFUTED", []
    if margin is None:
        return "NOT_JUDGED", []
    if main_rho - best_free <= margin:
        return "DOWNGRADED", [LABEL_E8_NOISE]
    return "PASS", []


def e8_ablation_labels(main_rho, rho_inv_d, rho_simdens) -> list:
    out = []
    if main_rho is None:
        return out
    if rho_inv_d is not None and rho_inv_d >= main_rho:
        out.append(LABEL_SIZE)
    if rho_simdens is not None and rho_simdens >= main_rho:
        out.append(LABEL_DIFFUSION)
    return out


def rerun_margin(d_by_mol: dict, mm_by_mol: dict, dens_by_mol: dict, ref: dict) -> dict:
    """Population SD of rho over every pick of one rerun's D per molecule."""
    lists = [d_by_mol[m] for m in MOL_IDS]
    rhos = []
    for pick in itertools.product(*lists):
        prox = [proxy_mpas(d, mm_by_mol[m], dens_by_mol[m]) for d, m in zip(pick, MOL_IDS)]
        rhos.append(spearman(prox, [ref[m]["eta_ref_mPa_s"] for m in MOL_IDS]))
    if any(r is None for r in rhos):
        raise ValueError("a pick gave an undefined rho")
    sd = statistics.pstdev(rhos)
    out = {"n_picks": len(rhos), "margin_sd": sd, "rho_min": min(rhos), "rho_max": max(rhos),
           "rho_mean": statistics.fmean(rhos)}
    if sd == 0.0:
        raise WrongVarianceSource(f"the rerun margin over {len(rhos)} picks is exactly zero")
    return out


def nondiffusive_labels(count: int) -> list:
    return [LABEL_NONDIFF.format(n=count)] if count >= NONDIFF_LABEL_MIN else []


def e9_values(cells, band) -> dict:
    lo, hi = band
    rows, outside = [], []
    for m in MOL_IDS:
        recs = [finished_rec(cells, m, r) for r in RERUNS]
        recs = [x for x in recs if x is not None]
        curves = [msd_curve(x) for x in recs]
        curves = [c for c in curves if len(c) > int(FITS_MAIN["main"][1])]
        if not curves:
            rows.append({"molecule": m, "slope": None})
            continue
        n = min(len(c) for c in curves)
        avg = [mean(c[k] for c in curves) for k in range(n)]
        f = fit_msd(avg, *FITS_MAIN["main"])
        s = f["loglog_slope"]
        out_flag = s is None or not (lo <= s <= hi)
        if out_flag:
            outside.append(m)
        rows.append({"molecule": m, "name": MOL[m]["name"], "slope_of_rerun_mean_msd": s,
                     "per_rerun_slopes": [x["values"]["loglog_slope"].get("main") for x in recs],
                     "outside_band": out_flag})
    return {"rows": rows, "outside": outside, "count": len(outside), "band": [lo, hi]}


def e10_values(cells, ref) -> dict:
    out = {}
    for w in FITS_MAIN:
        tab = main_table(cells, ref, window=w)
        out[w] = rho_vs_ref({m: (tab[m]["proxy_mPa_s"] if tab[m] else None) for m in MOL_IDS}, ref)
    return out


def e10_labels(rhos: dict) -> list:
    main = rhos.get("main")
    if main is None or main < RHO_PASS:
        return []
    others = [rhos.get(k) for k in rhos if k != "main"]
    if all(r is not None and r >= RHO_PASS for r in others):
        return [LABEL_ROBUST]
    return [LABEL_WINDOW]


def compute_endpoints(cells, reference: dict, status: dict) -> dict:
    """Every endpoint's values and raw outcome. Writing and voiding happen elsewhere."""
    ref = reference["molecules"]
    band = status.get("slope_band")
    tiers = tier_status(cells)
    tab = main_table(cells, ref)
    E = {"tiers": tiers}

    # 1: data-only pre-check, restated from the pre-launch record.
    e1 = status.get("e1") or {}
    E[1] = {"decision": "PASS" if e1.get("passed") else "FAIL", "labels": [LABEL_E1] if e1.get("passed") else [],
            "values": e1, "metric": "data-only pre-check, recomputed from the committed files before launch"}

    # 2: density gate.
    g = e2_density_gate(tab, ref)
    E[2] = {"decision": g["decision"], "labels": [], "values": g, "gate_failed": g["decision"] == "FAIL",
            "metric": "mean simulated density, last 250 ps of the constant-pressure stage, against the paper's"}

    # 9 and 10 first: their labels attach to the main endpoint.
    e9 = e9_values(cells, band) if band else {"rows": [], "outside": [], "count": None, "band": None}
    e10 = e10_values(cells, ref)
    lab9 = nondiffusive_labels(e9["count"]) if e9["count"] is not None else []
    lab10 = e10_labels(e10)

    # 3: main rho.
    proxies = {m: (tab[m]["proxy_mPa_s"] if tab[m] else None) for m in MOL_IDS}
    rho = rho_vs_ref(proxies, ref)
    chance = chance_at_least(rho) if rho is not None else None
    dec3, lab3 = e3_decide(rho)
    E[3] = {"decision": dec3, "labels": lab3 + lab9 + lab10,
            "values": {"rho": rho, "chance_count": chance[0] if chance else None,
                       "chance_total": chance[1] if chance else None,
                       "chance_probability": (chance[0] / chance[1]) if chance else None,
                       "flagged_non_diffusive": e9["outside"], "table": tab},
            "metric": "Spearman rho, proxy against reference viscosity at 40 C, D averaged over finished reruns"}

    # 4: stability across reruns.
    complete_reruns = [r for r in RERUNS if all(finished_rec(cells, m, r) for m in MOL_IDS)]
    per_rerun = {}
    for r in complete_reruns:
        per_rerun[r] = {m: proxy_mpas(finished_rec(cells, m, r)["values"]["D_A2_per_ps"]["main"],
                                      ref[m]["molar_mass_g_mol"],
                                      finished_rec(cells, m, r)["values"]["density_final_window_g_cm3"])
                        for m in MOL_IDS}
    pairs = []
    for a, b in itertools.combinations(complete_reruns, 2):
        pairs.append({"reruns": [a, b], "rho": spearman([per_rerun[a][m] for m in MOL_IDS],
                                                         [per_rerun[b][m] for m in MOL_IDS])})
    own = {r: rho_vs_ref(per_rerun[r], ref) for r in complete_reruns}
    if not pairs:
        dec4 = "NOT_JUDGED"
    elif all(p["rho"] is not None and p["rho"] >= RHO_PASS for p in pairs):
        dec4 = "PASS"
    else:
        dec4 = "REFUTED"
    E[4] = {"decision": dec4, "labels": [], "values": {
        "complete_reruns": complete_reruns, "pairs": pairs, "each_rerun_rho_vs_reference": own,
        "min_rerun_rho": min(own.values()) if own and None not in own.values() else None,
        "max_rerun_rho": max(own.values()) if own and None not in own.values() else None,
        "per_rerun_proxy_mPa_s": per_rerun, "note": LABEL_RERUNS},
        "metric": "Spearman rho between the proxy orders of each pair of complete reruns"}

    # 5: agreement with the longer run.
    ext = {m: finished_rec(cells, m, 1, "extension") for m in MOL_IDS}
    v5 = {"long_proxy_mPa_s": None, "short_proxy_mPa_s": None, "rho": None}
    if not all(ext.values()):
        dec5, why5 = "NOT_JUDGED", "the longer runs (tier 2) did not all finish"
    else:
        joins = {m: ext[m]["values"].get("join_check", {}) for m in MOL_IDS}
        v5["join_checks"] = joins
        bad = [m for m in MOL_IDS if not joins[m].get("passed")]
        long_p = {m: proxy_mpas(ext[m]["values"]["D_A2_per_ps"]["long"], ref[m]["molar_mass_g_mol"],
                                ext[m]["values"]["density_final_window_g_cm3"]) for m in MOL_IDS}
        short_tab = main_table(cells, ref, reruns=(2, 3))
        short_p = {m: (short_tab[m]["proxy_mPa_s"] if short_tab[m] else None) for m in MOL_IDS}
        v5.update({"long_proxy_mPa_s": long_p, "short_proxy_mPa_s": short_p,
                   "short_side_reruns": {m: (short_tab[m]["reruns"] if short_tab[m] else []) for m in MOL_IDS}})
        if any(short_p[m] is None for m in MOL_IDS):
            dec5, why5 = "NOT_JUDGED", "reruns 2 and 3 are missing for some molecule"
        else:
            r5 = spearman([long_p[m] for m in MOL_IDS], [short_p[m] for m in MOL_IDS])
            v5["rho"] = r5
            if bad:
                dec5, why5 = "NOT_JUDGED", f"the join check failed for {', '.join(bad)}"
            else:
                dec5, why5 = ("PASS" if r5 is not None and r5 >= RHO_PASS else "REFUTED"), ""
    v5["why_not_judged"] = why5 if dec5 == "NOT_JUDGED" else None
    E[5] = {"decision": dec5, "labels": [], "values": v5,
            "metric": "Spearman rho, rerun 1 continued to 2 ns against the mean of reruns 2 and 3"}

    # 6: cost.
    rows6 = []
    for m in MOL_IDS:
        fin = [finished_rec(cells, m, r) for r in RERUNS]
        fin = [x for x in fin if x]
        ns = len(fin) * NS_PER_RUN
        val = [x for x in (finished_rec(cells, m, 1, "extension"), finished_rec(cells, m, 1, "timestep_1fs")) if x]
        rows6.append({"molecule": m, "finished_reruns": len(fin), "simulated_ns": ns,
                      "within_8_ns": ns <= COST_LIMIT_NS,
                      "box_hours_share_main": sum(x["values"].get("box_hours_share") or 0 for x in fin),
                      "validation_runs_box_hours_share": sum(x["values"].get("box_hours_share") or 0 for x in val)})
    E[6] = {"decision": "MET_BY_PLAN" if all(r["within_8_ns"] for r in rows6) else "EXCEEDED",
            "labels": [LABEL_COST] + ([f"claim 3: {LABEL_CLAIM3_NOT_SHOWN}"] if dec4 == "REFUTED" else []),
            "values": {"rows": rows6, "planned_ns_per_molecule": 3 * NS_PER_RUN,
                       "planned_fraction_of_80_ns": 3 * NS_PER_RUN / PAPER_NS_PER_MOLECULE},
            "metric": "simulated time per molecule: finished reruns x 1.125 ns; box hours reported beside it"}

    # 7: family test.
    v7 = {"concordant": None}
    if all(proxies[m] is not None for m in MOL_IDS):
        etas = {m: ref[m]["eta_ref_mPa_s"] for m in MOL_IDS}
        pairs7 = concordance(proxies, etas, HYDROCARBONS) + concordance(proxies, etas, OXYGENATES)
        n_conc = sum(1 for p in pairs7 if p["concordant"])
        lh = mean(math.log(proxies[m] / etas[m]) for m in HYDROCARBONS)
        lo_ = mean(math.log(proxies[m] / etas[m]) for m in OXYGENATES)
        fc = family_chance_counts()
        v7 = {"concordant": n_conc, "of": 12, "discordant_pairs": [p["pair"] for p in pairs7 if not p["concordant"]],
              "pairs": pairs7, "log_offset_hydrocarbon_minus_oxygenate": lh - lo_,
              "offset_factor": math.exp(lh - lo_), "chance_ge10": [fc["ge10"], fc["total"]],
              "chance_ge9": [fc["ge9"], fc["total"]]}
        dec7 = "PASS" if n_conc >= FAMILY_MIN else "REFUTED"
    else:
        dec7 = "NOT_JUDGED"
    lab7 = []
    if dec7 == "REFUTED" and rho is not None and rho >= RHO_PASS:
        lab7.append("the overall rho is carried by order between families, not inside them")
    E[7] = {"decision": dec7, "labels": lab7, "values": v7,
            "metric": "within-family pairs in the reference order, of 12"}

    # 8: added value over free orderings.
    free = reference.get("free_orderings") or {}
    best = max(free.values()) if free else None
    v8 = {"main_rho": rho, "free_orderings": free, "best_free": best,
          "main_minus_best_free": (rho - best) if (rho is not None and best is not None) else None}
    lab8 = []
    if rho is None:
        dec8 = "NOT_JUDGED"
    else:
        inv_d = {m: 1.0 / tab[m]["D_mean"] for m in MOL_IDS}
        simd = {m: tab[m]["density_mean"] for m in MOL_IDS}
        v8["rho_inverse_D_ablation"] = rho_vs_ref(inv_d, ref)
        v8["rho_simulated_density_ablation"] = rho_vs_ref(simd, ref)
        lab8 += e8_ablation_labels(rho, v8["rho_inverse_D_ablation"], v8["rho_simulated_density_ablation"])
        try:
            mg = rerun_margin({m: tab[m]["D_each"] for m in MOL_IDS},
                              {m: ref[m]["molar_mass_g_mol"] for m in MOL_IDS},
                              {m: tab[m]["density_mean"] for m in MOL_IDS}, ref)
            v8["margin"] = mg
            dec8, extra = e8_decide(rho, best, mg["margin_sd"])
            lab8 = extra + lab8
        except WrongVarianceSource as e:
            dec8 = WRONG_VARIANCE_SOURCE
            v8["halt"] = str(e)
    E[8] = {"decision": dec8, "labels": lab8, "values": v8,
            "metric": "main rho against the best of molar mass, reference density and XGBoost, with a rerun margin"}

    # 9: diffusive-regime label (never refutes).
    E[9] = {"decision": "LABEL" if lab9 else ("NO_LABEL" if e9["count"] is not None else "NOT_JUDGED"),
            "labels": lab9, "values": e9,
            "metric": "molecules whose log-log MSD slope, 0.1-0.4 ns, lies outside the planted band"}

    # 10: fit-window sensitivity (never refutes).
    E[10] = {"decision": ("ROBUST" if LABEL_ROBUST in lab10 else ("WINDOW_DEPENDENT" if LABEL_WINDOW in lab10
                                                                   else "NO_LABEL")),
             "labels": lab10, "values": {"rho_by_window": e10, "windows_ps": FITS_MAIN},
             "metric": "main rho with lag windows 0.1-0.4 (main), 0.05-0.2 and 0.2-0.4 ns"}

    # 11: planted known truth, restated from the pre-launch record.
    pl = status.get("planted") or {}
    E[11] = {"decision": "PASS" if pl.get("all_passed") else "FAIL", "labels": [], "values": pl,
             "metric": "planted known-truth checks (a) to (d), run before launch"}

    # 12: timestep control.
    v12 = {}
    one = finished_rec(cells, TIMESTEP_MOL, 1, "timestep_1fs")
    twos = [finished_rec(cells, TIMESTEP_MOL, r) for r in RERUNS]
    if one is None:
        dec12 = "NOT_JUDGED"
        v12["why_not_judged"] = "the 1 fs run (tier 4) did not finish"
    elif any(x is None for x in twos):
        dec12 = "NOT_JUDGED"
        v12["why_not_judged"] = "the three 2 fs reruns are not all finished"
    else:
        sc = one["values"].get("frame_spacing_check") or {}
        v12["frame_spacing_check"] = sc
        d1 = one["values"]["D_A2_per_ps"]["main"]
        d2 = [x["values"]["D_A2_per_ps"]["main"] for x in twos]
        v12.update({"D_1fs": d1, "D_2fs_each": d2, "D_2fs_mean": mean(d2)})
        if not sc.get("passed"):
            dec12 = "NOT_JUDGED"
            v12["why_not_judged"] = "the 1 fs frame spacing is not 1.000 ps"
        else:
            sd = statistics.stdev(d2)
            v12["spread_sd"] = sd
            if sd == 0.0:
                dec12 = WRONG_VARIANCE_SOURCE
                v12["halt"] = "the spread of D over the three 2 fs reruns is exactly zero"
            else:
                v12["difference_in_sd"] = abs(d1 - mean(d2)) / sd
                dec12 = "PASS" if abs(d1 - mean(d2)) <= 2 * sd else "CONDITIONAL_ON_TIMESTEP"
    E[12] = {"decision": dec12, "labels": (["the main result is conditional on the timestep"]
                                           if dec12 == "CONDITIONAL_ON_TIMESTEP" else []), "values": v12,
             "metric": "D of nonylcyclohexane at 1 fs against the mean of its three 2 fs reruns"}

    # Report-only readouts.
    f2 = []
    for m in MOL_IDS:
        x = ext.get(m)
        f2.append({"molecule": m, "name": MOL[m]["name"],
                   "loglog_slope_0p1_0p9_ns": x["values"]["loglog_slope"].get("long") if x else None,
                   "status": "measured" if x else "not run"})
    E["F2"] = {"decision": "REPORT_ONLY", "labels": [], "values": {"rows": f2},
               "metric": "log-log MSD slope of each molecule in the 2 ns run, lags 0.1-0.9 ns"}
    dr = []
    for m in MOL_IDS:
        recs = [x for x in (finished_rec(cells, m, r) for r in RERUNS) if x]
        dr.append({"molecule": m, "name": MOL[m]["name"],
                   "mean_0p20_0p45_ns": mean(x["values"]["thermo_stage"]["density_mean_0p20_0p45_ns"] for x in recs)
                   if recs else None,
                   "mean_last_250_ps_deck_window": mean(x["values"]["density_final_window_g_cm3"] for x in recs)
                   if recs else None,
                   "per_rerun": [{"rerun": x["cell"]["rerun"],
                                  "mean_0p20_0p45_ns": x["values"]["thermo_stage"]["density_mean_0p20_0p45_ns"],
                                  "mean_last_250_ps_deck_window": x["values"]["density_final_window_g_cm3"]}
                                 for x in recs]})
    E["DENS"] = {"decision": "REPORT_ONLY", "labels": [], "values": {"rows": dr},
                 "metric": "mean density over 0.20-0.45 ns of the constant-pressure stage, beside its last 250 ps"}
    E["proxy"] = proxies
    E["rho"] = rho
    return E


RULES = {
    1: ("rho = 1.0 between the two committed files, and the stated reference order. A failure stops the run "
        "before any spend. A pass is an integrity check, not evidence."),
    2: ("every molecule's density, averaged over finished reruns, inside its band (paper value plus or minus 2%); "
        "any molecule outside fails the gate, voids the run, and leaves the main claim neither passed nor refuted"),
    3: ("rho at least 0.8 answers yes for this form; below 0.8 refutes this form only; below 0.6 also meets the "
        "abandon line for this form"),
    4: "every pair of complete reruns has rho at least 0.8; any pair below 0.8 refutes stability",
    5: ("rho at least 0.8 passes; below 0.8 refutes; not judged if the longer runs did not all finish or any join "
        "check failed; never counted as passed when not judged"),
    6: ("at most 8 ns of simulated time per molecule; reported as met by the plan's arithmetic, not an empirical "
        "test; claim 3 is not shown if the stability endpoint fails"),
    7: "at least 10 of 12 within-family pairs in the reference order; fewer refutes the family claim only",
    8: ("judged against molar mass, reference density and XGBoost only: at or below the best refutes; above it "
        "but within the rerun margin downgrades; above it by more than the margin passes; a margin of exactly "
        "zero halts with WRONG_VARIANCE_SOURCE and gives no verdict"),
    9: "three or more of eight molecules outside the planted slope band adds a label; it never refutes",
    10: ("a main-window pass with another window below 0.8 is labelled window-dependent; it never refutes"),
    11: "planted checks (a) to (d) and the queued planted controls all pass before launch",
    12: ("|D at 1 fs minus mean D at 2 fs| at most 2 standard deviations passes; more makes the main result "
         "conditional on the timestep; a spread of exactly zero halts with WRONG_VARIANCE_SOURCE; not judged if "
         "the 1 fs run did not finish or its frame spacing is not 1.000 ps"),
    "F2": "report only; no verdict depends on it",
    "DENS": "report only; no verdict depends on it",
}

CLAIM_TEXT = {
    1: "the proxy ranks the eight liquids with rho of at least 0.8",
    2: "the ordering converges in about 1 ns (stable across reruns, and agrees with a 2 ns run)",
    3: "the proxy costs well under the paper's 80 ns per molecule",
    4: "the ordering holds inside each chemical family",
    5: "the proxy adds over orderings that cost nothing",
}


def claims_from(E: dict) -> dict:
    c = {}
    c[1] = E[3]["decision"]
    d4, d5 = E[4]["decision"], E[5]["decision"]
    if "REFUTED" in (d4, d5):
        c[2] = "REFUTED"
    elif d4 == "PASS" and d5 == "PASS":
        c[2] = "PASS"
    elif d4 == "PASS":
        c[2] = "PARTLY_JUDGED: rerun stability passed; agreement with the longer run not judged"
    else:
        c[2] = "NOT_JUDGED"
    c[3] = LABEL_CLAIM3_NOT_SHOWN if d4 == "REFUTED" else LABEL_COST
    c[4] = E[7]["decision"]
    c[5] = E[8]["decision"]
    return c


def run_endpoints(outdir, reference: dict, status: dict, inputs=None) -> dict:
    """Write every endpoint record in order, voiding when a gate fails, then the summary."""
    outdir = Path(outdir)
    cells = collect_cells(outdir)
    E = compute_endpoints(cells, reference, status)
    if not E["tiers"]["tier1"]:
        st = read_state(outdir)
        if not any(v.startswith("incomplete run") for v in st["voided_by"]):
            void_run(outdir, "incomplete run: tier 1 did not finish", LABEL_INCOMPLETE)
    decisions = {}
    order = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, "F2", "DENS"]
    for n in order:
        e = E[n]
        if n == 2 and e.get("gate_failed"):
            void_run(outdir, "the density gate (endpoint 2) failed", LABEL_UNTRUSTED)
        st = read_state(outdir)
        raw = e["decision"]
        labels = list(e["labels"])
        verdict_bearing = n in (2, 3, 4, 5, 7, 8, 12)
        decision = raw
        values = dict(e["values"])
        if not st["run_valid"] and verdict_bearing:
            decision = "NO_VERDICT"
            values["rule_outcome_untrusted"] = raw
            labels = labels + st["labels"]
        cell = {"stage": "endpoints", "endpoint": n} if isinstance(n, int) else \
            {"stage": "endpoints", "readout": {"F2": "extension-slope", "DENS": "density-settling"}[n]}
        write_record(outdir, cell=cell, inputs=inputs or [], metric=e["metric"],
                     values=dict(values, labels=labels), threshold={"rule": RULES[n]},
                     decision_rule=RULES[n], decision=decision, notes="; ".join(labels),
                     rows=e["values"].get("rows") if isinstance(e["values"].get("rows"), list) else None)
        decisions[n] = {"decision": decision, "rule_outcome": raw, "labels": labels}
    st = read_state(outdir)
    claims = claims_from(E)
    if not st["run_valid"]:
        claims = {k: f"NO_VERDICT ({'; '.join(st['voided_by'])}); rule outcome: {v}" for k, v in claims.items()}
    summary_values = {"run_valid": st["run_valid"], "voided_by": st["voided_by"], "run_labels": st["labels"],
                      "tiers_finished": E["tiers"], "claims": {k: {"claim": CLAIM_TEXT[k], "outcome": v}
                                                               for k, v in claims.items()},
                      "endpoints": decisions, "main_rho": E["rho"], "proxy_mPa_s": E["proxy"],
                      "rerun_note": LABEL_RERUNS}
    write_record(outdir, cell={"stage": "summary"}, inputs=inputs or [], metric="run summary",
                 values=summary_values, threshold={},
                 decision_rule=("RUN_VALID when no gate failed and tier 1 finished; RUN_VOID otherwise. "
                                "Each claim's outcome is its endpoint's decision."),
                 decision="RUN_VALID" if st["run_valid"] else "RUN_VOID",
                 notes="; ".join(st["voided_by"]))
    return {"E": E, "decisions": decisions, "claims": claims, "run_valid": st["run_valid"]}


# ---------------------------------------------------------------------------
# Data-only pre-check (endpoint 1) and the reference table
# ---------------------------------------------------------------------------
def data_precheck(dataset_text: str, predictions_text: str) -> dict:
    problems, rows = [], {}

    def index(text, name):
        out = {}
        for r in csv.DictReader(io.StringIO(text)):
            mid = r.get("molecule_id")
            if mid in MOL:
                if mid in out:
                    problems.append(f"{name}: {mid} appears more than once")
                out[mid] = r
        return out

    ds, pr = index(dataset_text, "dataset"), index(predictions_text, "predictions")
    for m in MOLECULES:
        d, p = ds.get(m["id"]), pr.get(m["id"])
        if d is None or p is None:
            problems.append(f"{m['id']} is missing from a committed file")
            continue
        try:
            row = {"eta_dataset": float(d["viscosity_40c"]), "eta_predictions": float(p["experimental_40C_mPa_s"]),
                   "xgboost": float(p["xgboost_descriptors_40C"]), "rho_ref": float(d["density_40c"])}
        except (KeyError, ValueError) as e:
            problems.append(f"{m['id']}: unreadable value ({e})")
            continue
        for src, s in (("dataset", d.get("canonical_smiles")), ("predictions", p.get("canonical_smiles"))):
            if s != m["smiles"]:
                problems.append(f"{m['id']}: the {src} molecule code differs from the question's")
        if abs(row["eta_dataset"] - m["eta_ref"]) > 1e-9:
            problems.append(f"{m['id']}: dataset viscosity {row['eta_dataset']} differs from the design's {m['eta_ref']}")
        if abs(row["rho_ref"] - m["rho_ref"]) > 1e-9:
            problems.append(f"{m['id']}: dataset density {row['rho_ref']} differs from the design's {m['rho_ref']}")
        f = formula_from_smiles(m["smiles"])
        if f != m["formula"]:
            problems.append(f"{m['id']}: formula from the molecule code is {formula_text(f)}")
        row.update({"formula": formula_text(f), "atoms_per_molecule": sum(f.values()), "molar_mass": molar_mass(f)})
        rows[m["id"]] = row
    out = {"problems": problems, "rows_by_id": rows, "passed": False}
    if len(rows) != len(MOLECULES):
        return out
    eta_d = [rows[m]["eta_dataset"] for m in MOL_IDS]
    eta_p = [rows[m]["eta_predictions"] for m in MOL_IDS]
    rho_files = spearman(eta_d, eta_p)
    order_d = sorted(MOL_IDS, key=lambda m: -rows[m]["eta_dataset"])
    order_p = sorted(MOL_IDS, key=lambda m: -rows[m]["eta_predictions"])
    free = {"molar_mass": spearman([rows[m]["molar_mass"] for m in MOL_IDS], eta_d),
            "reference_density": spearman([rows[m]["rho_ref"] for m in MOL_IDS], eta_d),
            "xgboost": spearman([rows[m]["xgboost"] for m in MOL_IDS], eta_d)}
    out.update({"rho_between_files": rho_files, "order_dataset": order_d, "order_predictions": order_p,
                "order_expected": REFERENCE_ORDER, "free_orderings": free,
                "free_orderings_at_design_time": {"molar_mass": 0.524, "reference_density": 0.048, "xgboost": 0.738}})
    out["passed"] = (not problems and rho_files is not None and abs(rho_files - 1.0) < 1e-12
                     and order_d == REFERENCE_ORDER and order_p == REFERENCE_ORDER)
    return out


def build_reference(e1: dict) -> dict:
    mols = {}
    for m in MOLECULES:
        r = e1["rows_by_id"][m["id"]]
        mols[m["id"]] = {"name": m["name"], "family": m["family"], "smiles": m["smiles"], "formula": r["formula"],
                         "atoms_per_molecule": r["atoms_per_molecule"], "molar_mass_g_mol": r["molar_mass"],
                         "eta_ref_mPa_s": r["eta_dataset"], "eta_experimental_column": r["eta_predictions"],
                         "xgboost_40C": r["xgboost"], "rho_ref_g_cm3": r["rho_ref"],
                         "rho_paper_g_cm3": m["rho_paper"], "density_band_g_cm3": list(m["band"]),
                         "n_molecules": m["n_mol"]}
    return {"molecules": mols, "free_orderings": e1["free_orderings"], "reference_order": e1["order_dataset"]}


def reference_from_constants(xgb=None) -> dict:
    """For planted checks only: the same table built from the constants above."""
    mols = {}
    for m in MOLECULES:
        mm = molar_mass(m["formula"])
        mols[m["id"]] = {"name": m["name"], "family": m["family"], "smiles": m["smiles"],
                         "formula": formula_text(m["formula"]), "atoms_per_molecule": sum(m["formula"].values()),
                         "molar_mass_g_mol": mm, "eta_ref_mPa_s": m["eta_ref"], "rho_ref_g_cm3": m["rho_ref"],
                         "rho_paper_g_cm3": m["rho_paper"], "density_band_g_cm3": list(m["band"]),
                         "n_molecules": m["n_mol"], "xgboost_40C": (xgb or {}).get(m["id"])}
    etas = [m["eta_ref"] for m in MOLECULES]
    free = {"molar_mass": spearman([mols[i]["molar_mass_g_mol"] for i in MOL_IDS], etas),
            "reference_density": spearman([m["rho_ref"] for m in MOLECULES], etas)}
    if xgb:
        free["xgboost"] = spearman([xgb[i] for i in MOL_IDS], etas)
    return {"molecules": mols, "free_orderings": free, "reference_order": REFERENCE_ORDER}


# ---------------------------------------------------------------------------
# Planted known-truth checks
# ---------------------------------------------------------------------------
def bias_check(d_rec, d_true) -> dict:
    rel_ = [r / t - 1.0 for r, t in zip(d_rec, d_true)]
    n = len(rel_)
    mb = statistics.fmean(rel_)
    sd = statistics.stdev(rel_) if n > 1 else 0.0
    se = sd / math.sqrt(n) if n else 0.0
    return {"n": n, "mean_relative_bias": mb, "sd": sd, "standard_error": se,
            "bias_in_standard_errors": (mb / se) if se > 0 else None, "passed": abs(mb) <= 2 * se}


def slope_band(slopes, fraction: float = BAND_FRACTION):
    devs = sorted(abs(s - 1.0) for s in slopes)
    k = math.ceil(fraction * len(devs)) - 1
    h = devs[k]
    return (1.0 - h, 1.0 + h), h


def planted_proxy_check() -> dict:
    """Gate item I3: made-up viscosities 1..8 mPa s, shuffled with seed 7."""
    etas = list(range(1, 9))
    random.Random(PLANTED_SEED).shuffle(etas)
    planted = {m: float(e) for m, e in zip(MOL_IDS, etas)}
    rows, worst = [], 0.0
    rec = {}
    for m in MOL_IDS:
        mm = molar_mass(MOL[m]["formula"])
        d = planted_d_a2ps(planted[m], mm, MOL[m]["rho_paper"])
        back = proxy_mpas(d, mm, MOL[m]["rho_paper"])
        rec[m] = back
        err = abs(back / planted[m] - 1.0)
        worst = max(worst, err)
        rows.append({"molecule": m, "planted_eta": planted[m], "planted_D_A2_per_ps": d, "recovered_eta": back,
                     "relative_error": err})
    rho_fwd = spearman([rec[m] for m in MOL_IDS], [planted[m] for m in MOL_IDS])
    rho_rev = spearman([rec[m] for m in MOL_IDS], [9.0 - planted[m] for m in MOL_IDS])
    passed = worst <= I3_TOL and rho_fwd == 1.0 and rho_rev == -1.0
    return {"passed": passed, "worst_relative_error": worst, "rho_forward": rho_fwd, "rho_reversed": rho_rev,
            "rows": rows, "seed": PLANTED_SEED}


def planted_family_check() -> dict:
    """Gate item I7."""
    etas = {m: MOL[m]["eta_ref"] for m in MOL_IDS}
    known = sum(p["concordant"] for p in concordance(etas, etas, HYDROCARBONS) + concordance(etas, etas, OXYGENATES))
    rev = {m: 1.0 / etas[m] for m in MOL_IDS}
    reversed_ = sum(p["concordant"] for p in concordance(rev, etas, HYDROCARBONS) + concordance(rev, etas, OXYGENATES))
    off = {m: etas[m] * (2.0 if m in HYDROCARBONS else 0.5) for m in MOL_IDS}
    off_c = sum(p["concordant"] for p in concordance(off, etas, HYDROCARBONS) + concordance(off, etas, OXYGENATES))
    lh = mean(math.log(off[m] / etas[m]) for m in HYDROCARBONS)
    lo_ = mean(math.log(off[m] / etas[m]) for m in OXYGENATES)
    fc = family_chance_counts()
    passed = (known == 12 and reversed_ == 0 and off_c == 12 and abs((lh - lo_) - math.log(4.0)) < 1e-12
              and fc["ge10"] == 26 and fc["ge9"] == 68 and fc["total"] == 576)
    return {"passed": passed, "known_order": known, "reversed_order": reversed_, "offset_order": off_c,
            "offset_log_difference": lh - lo_, "ln4": math.log(4.0), "enumeration": fc}


def planted_margin_check(d_sets: list) -> dict:
    """Gate item I8: identical reruns must halt; planted reruns give a positive margin."""
    mm = {m: molar_mass(MOL[m]["formula"]) for m in MOL_IDS}
    dens = {m: MOL[m]["rho_paper"] for m in MOL_IDS}
    ref = reference_from_constants()["molecules"]
    out = {}
    same = {m: [d_sets[0][m]] * 3 for m in MOL_IDS}
    try:
        rerun_margin(same, mm, dens, ref)
        out["identical_halts"] = False
    except WrongVarianceSource:
        out["identical_halts"] = True
    three = rerun_margin({m: [s[m] for s in d_sets[:3]] for m in MOL_IDS}, mm, dens, ref)
    two = rerun_margin({m: [s[m] for s in d_sets[:2]] for m in MOL_IDS}, mm, dens, ref)
    out.update({"three_reruns": three, "two_reruns": two})
    out["passed"] = (out["identical_halts"] and three["n_picks"] == 6561 and three["margin_sd"] > 0
                     and two["n_picks"] == 256 and two["margin_sd"] > 0)
    return out


def planted_labels_check(nondiff_slope, band) -> dict:
    """Check (d): known order passes, reversed refutes, a density 5% off fails the gate,
    and a planted t^0.7 slope gets the non-diffusive flag."""
    ref = reference_from_constants()["molecules"]
    etas = {m: ref[m]["eta_ref_mPa_s"] for m in MOL_IDS}
    known = rho_vs_ref(etas, ref)
    rev = rho_vs_ref({m: 1.0 / etas[m] for m in MOL_IDS}, ref)
    lab_pass, _ = e3_decide(known)
    lab_ref, _ = e3_decide(rev)
    tab = {m: {"density_mean": ref[m]["rho_paper_g_cm3"] * (1.05 if m == MOL_IDS[0] else 1.0),
               "density_each": [ref[m]["rho_paper_g_cm3"]]} for m in MOL_IDS}
    gate = e2_density_gate(tab, ref)["decision"]
    tab_ok = {m: {"density_mean": ref[m]["rho_paper_g_cm3"], "density_each": [ref[m]["rho_paper_g_cm3"]]}
              for m in MOL_IDS}
    gate_ok = e2_density_gate(tab_ok, ref)["decision"]
    nondiff = not (band[0] <= nondiff_slope <= band[1])
    reached = {"main_pass": lab_pass == "PASS" and known == 1.0, "main_refuted": lab_ref.startswith("REFUTED") and rev == -1.0,
               "gate_fail": gate == "FAIL" and gate_ok == "PASS", "non_diffusive": nondiff}
    return {"passed": all(reached.values()), "reached": reached, "rho_known": known, "rho_reversed": rev}


def fgn(rng, n: int, width: int, hurst: float):
    """Fractional Gaussian noise by circulant embedding: unit variance, exact covariance."""
    import numpy as np
    k = np.arange(n + 1, dtype=float)
    gam = 0.5 * (np.abs(k + 1) ** (2 * hurst) - 2 * np.abs(k) ** (2 * hurst) + np.abs(k - 1) ** (2 * hurst))
    row = np.concatenate([gam, gam[-2:0:-1]])
    lam = np.fft.fft(row).real
    if lam.min() < -1e-8 * lam.max():
        raise StageError("the fractional-noise generator found a negative eigenvalue")
    lam = np.clip(lam, 0.0, None)
    m = row.size
    z = rng.normal(size=(m, width)) + 1j * rng.normal(size=(m, width))
    y = np.fft.fft(np.sqrt(lam / m)[:, None] * z, axis=0)
    return y.real[:n]


def planted_cell(rng, n_mol: int, n_frames: int, d_a2ps: float, kind: str = "ordinary"):
    """Planted centres, (frames, molecules, 3). Ordinary walks or MSD growing as t^0.7.
    The set's shared centre does not wander; a known common drift is then added."""
    import numpy as np
    sd = math.sqrt(2.0 * d_a2ps * FRAME_PS)
    if kind == "ordinary":
        inc = rng.normal(0.0, sd, size=(n_frames - 1, n_mol, 3))
    else:
        inc = fgn(rng, n_frames - 1, n_mol * 3, EXPONENT_C / 2.0).reshape(n_frames - 1, n_mol, 3) * sd
    inc = (inc - inc.mean(axis=1, keepdims=True)) * math.sqrt(n_mol / (n_mol - 1.0))
    start = rng.uniform(0.0, 50.0, size=(1, n_mol, 3))
    pos = np.concatenate([start, start + np.cumsum(inc, axis=0)], axis=0)
    t = (np.arange(n_frames, dtype=float) * FRAME_PS)[:, None, None]
    return pos + t * np.asarray(PLANTED_DRIFT)[None, None, :]


def frames_from_array(X, com_every: int = 500, step0: int = 0):
    return [(step0 + i * com_every, array("d", X[i].reshape(-1).tolist())) for i in range(X.shape[0])]


def run_planted_checks(log=print) -> dict:
    """Planted checks (a)-(d), and queued controls I3, I5 part 1, I7, I8 and I10."""
    import numpy as np
    rng = np.random.default_rng(PLANTED_SEED)
    out = {}
    counts = [MOL[m]["n_mol"] for m in MOL_IDS]

    # (a) and I10: 20 ensembles x 8 cells, 0..1000 ps, analysis window 0.2-1.0 ns.
    t0 = time.time()
    a_rows, d_sets = [], []
    agree = None
    for e in range(N_ENS_A):
        dset = {}
        for m, n in zip(MOL_IDS, counts):
            X = planted_cell(rng, n, 1001, PLANTED_D)
            fr = frames_from_array(X)
            res = analyze_frames(fr, n, 2.0, WINDOW_MAIN_PS, FITS_MAIN, backend="numpy")
            if res["issues"]:
                raise StageError(f"planted check (a): the analysis flagged a planted cell: {res['issues']}")
            if agree is None:
                sub = 20
                fr_sub = [(s, array("d", v[:3 * sub])) for s, v in fr]
                rn = analyze_frames(fr_sub, sub, 2.0, WINDOW_MAIN_PS, {"main": FITS_MAIN["main"]}, backend="numpy")
                rp = analyze_frames(fr_sub, sub, 2.0, WINDOW_MAIN_PS, {"main": FITS_MAIN["main"]}, backend="plain")
                worst = max(abs(a - b) / max(abs(b), 1e-300) for a, b in zip(rn["msd"][1:], rp["msd"][1:]))
                agree = {"cells_compared": 1, "molecules": sub, "worst_relative_difference": worst,
                         "passed": worst <= 1e-9}
            row = {"ensemble": e, "molecule": m, "n_molecules": n, "D_true": PLANTED_D}
            for w in FITS_MAIN:
                row[f"D_{w}"] = res["fits"][w]["D_A2_per_ps"]
            row["loglog_slope_main"] = res["fits"]["main"]["loglog_slope"]
            a_rows.append(row)
            dset[m] = res["fits"]["main"]["D_A2_per_ps"]
        d_sets.append(dset)
    a = bias_check([r["D_main"] for r in a_rows], [PLANTED_D] * len(a_rows))
    a["fast_and_plain_msd_agree"] = agree
    a["passed"] = a["passed"] and agree["passed"]
    a["rows"] = a_rows
    out["a"] = a
    out["I10"] = {"alt_short_0p05_0p2_ns": bias_check([r["D_alt_short"] for r in a_rows], [PLANTED_D] * len(a_rows)),
                  "alt_late_0p2_0p4_ns": bias_check([r["D_alt_late"] for r in a_rows], [PLANTED_D] * len(a_rows))}
    out["I10"]["passed"] = out["I10"]["alt_short_0p05_0p2_ns"]["passed"] and out["I10"]["alt_late_0p2_0p4_ns"]["passed"]
    log(f"[planted] (a) and I10 done in {time.time() - t0:.1f}s")

    # (b) and (c): 200 ordinary and 200 t^0.7 single cells, counts in turn.
    t0 = time.time()
    s_ord, s_sub = [], []
    for i in range(N_ENS_BC):
        n = counts[i % len(counts)]
        X = planted_cell(rng, n, 1001, PLANTED_D, "ordinary")
        s_ord.append(analyze_frames(frames_from_array(X), n, 2.0, WINDOW_MAIN_PS, {"main": FITS_MAIN["main"]},
                                    backend="numpy")["fits"]["main"]["loglog_slope"])
    for i in range(N_ENS_BC):
        n = counts[i % len(counts)]
        X = planted_cell(rng, n, 1001, PLANTED_D, "power")
        s_sub.append(analyze_frames(frames_from_array(X), n, 2.0, WINDOW_MAIN_PS, {"main": FITS_MAIN["main"]},
                                    backend="numpy")["fits"]["main"]["loglog_slope"])
    band, h = slope_band(s_ord)
    inside_ord = sum(1 for s in s_ord if band[0] <= s <= band[1]) / len(s_ord)
    outside_sub = sum(1 for s in s_sub if not (band[0] <= s <= band[1])) / len(s_sub)
    out["b"] = {"band": list(band), "half_width": h, "fraction_ordinary_inside": inside_ord,
                "passed": inside_ord >= BAND_FRACTION, "slopes": s_ord}
    out["c"] = {"fraction_power_law_outside": outside_sub, "exponent": EXPONENT_C,
                "passed": outside_sub >= BAND_FRACTION, "slopes": s_sub,
                "median_slope": statistics.median(s_sub)}
    log(f"[planted] (b) and (c) done in {time.time() - t0:.1f}s; band {band[0]:.4f}-{band[1]:.4f}")

    # (d): every decision label reachable.
    out["d"] = planted_labels_check(statistics.median(s_sub), band)

    # I3, I7 and I8.
    out["I3"] = planted_proxy_check()
    out["I7"] = planted_family_check()
    out["I8"] = planted_margin_check(d_sets)

    # I5 part 1: 2.0 ns planted runs, written as two centre files split at 1.0 ns.
    t0 = time.time()
    i5_rows = []
    with tempfile.TemporaryDirectory(prefix="cp1_planted_") as td:
        td = Path(td)
        for e in range(N_ENS_A):
            for m, n in zip(MOL_IDS, counts):
                X = planted_cell(rng, n, 2001, PLANTED_D)
                steps = [i * 500 for i in range(2001)]
                flat = [X[i].reshape(-1).tolist() for i in range(2001)]
                p1, p2 = td / "part1.dat", td / "part2.dat"
                p1.write_text(format_com_text(steps[:1001], flat[:1001], n))
                p2.write_text(format_com_text(steps[1000:], flat[1000:], n))
                f1 = parse_com_file(p1.read_text())["frames"]
                f2 = parse_com_file(p2.read_text())["frames"]
                jc = join_check(f1, f2, n)
                res = analyze_frames(merge_parts(f1, f2), n, 2.0, WINDOW_EXT_PS, FITS_EXT, backend="numpy")
                if res["issues"]:
                    raise StageError(f"planted I5: the analysis flagged a planted cell: {res['issues']}")
                i5_rows.append({"ensemble": e, "molecule": m, "n_molecules": n, "D_true": PLANTED_D,
                                "D_long": res["fits"]["long"]["D_A2_per_ps"], "join_passed": jc["passed"],
                                "join_jump_A": jc["join_jump_A"]})
    i5 = bias_check([r["D_long"] for r in i5_rows], [PLANTED_D] * len(i5_rows))
    i5["all_joins_pass"] = all(r["join_passed"] for r in i5_rows)
    i5["passed"] = i5["passed"] and i5["all_joins_pass"]
    i5["rows"] = i5_rows
    out["I5_part1"] = i5
    log(f"[planted] I5 part 1 done in {time.time() - t0:.1f}s")
    out["all_passed"] = all(out[k]["passed"] for k in ("a", "b", "c", "d", "I3", "I5_part1", "I7", "I8", "I10"))
    return out


# ---------------------------------------------------------------------------
# Engine trial (used on the box to pick the path, and optionally on this workstation)
# ---------------------------------------------------------------------------
def engine_candidates(help_info: dict, cpu_count: int) -> list:
    pk = set(help_info.get("packages") or [])
    out = []
    # The trial itself checks that the card was used, so KOKKOS is tried whenever it is installed.
    if "KOKKOS" in pk:
        out.append(("GPU (KOKKOS package, CUDA)", ["-k", "on", "g", "1", "-sf", "kk"], {"OMP_NUM_THREADS": "1"}))
    if "GPU" in pk:
        out.append(("GPU (GPU package)", ["-sf", "gpu", "-pk", "gpu", "1"], {"OMP_NUM_THREADS": "1"}))
    k = max(1, cpu_count // WAVE_SIZE)
    if "OPENMP" in pk:
        out.append((f"CPU (OPENMP package, {k} threads per run)", ["-sf", "omp", "-pk", "omp", str(k)],
                    {"OMP_NUM_THREADS": str(k)}))
    else:
        out.append(("CPU (plain, one thread per run)", [], {"OMP_NUM_THREADS": "1"}))
    return out


def accel_evidence(name: str, text: str) -> list:
    lines = text.splitlines()
    if name.startswith("GPU (KOKKOS"):
        hits = [ln.strip() for ln in lines if "KOKKOS mode" in ln or "GPU(s) per node" in ln]
        ok = any("KOKKOS mode" in h for h in hits) and any("GPU" in h for h in hits)
        return hits if ok else []
    if name.startswith("GPU (GPU package"):
        hits = [ln.strip() for ln in lines if "Using acceleration for" in ln or "GPU package" in ln or
                "Device 0" in ln]
        return hits
    return ["processor path: no accelerator evidence needed"]


def trial_run(lmp, name, switches, env_extra, bundle: Path, workdir: Path, timeout_s: int) -> dict:
    mol = MOL_IDS[0]
    box = bundle / mol / f"pack{PACK_SEEDS[1]}"
    safe = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")
    rundir = workdir / f"trial_{safe}"
    if rundir.exists():
        shutil.rmtree(rundir)
    rundir.mkdir(parents=True)
    for f in ("in.init", "in.settings", "in.data"):
        shutil.copy2(box / f, rundir / f)
    shutil.copy2(bundle / "deck_main_cp1.in", rundir / "deck.in")
    cmd = [str(lmp)] + list(switches) + ["-in", "deck.in"] + \
        engine_vars("main", 1, rundir, overrides=TRIAL_VARS) + ["-log", "log.lammps"]
    env = os.environ.copy()
    env.update(env_extra)
    t0 = time.monotonic()
    try:
        with open(rundir / "screen.out", "wb") as fh:
            p = subprocess.run(cmd, cwd=rundir, stdout=fh, stderr=subprocess.STDOUT, env=env, timeout=timeout_s)
        rc = p.returncode
    except subprocess.TimeoutExpired:
        rc = "timeout"
    wall = time.monotonic() - t0
    names = cell_file_names("main", 1)
    log_text = (rundir / names["log"]).read_text(errors="replace") if (rundir / names["log"]).exists() else ""
    screen = (rundir / "screen.out").read_text(errors="replace")
    pl = parse_lammps_log(log_text)
    issues = []
    if rc != 0:
        issues.append(f"exit {rc}")
    errs = parse_lammps_log(screen)["errors"] + pl["errors"]
    if errs:
        issues.append(errs[0][:200])
    if len(pl["loops"]) != 4:
        issues.append(f"{len(pl['loops'])} finished loops; expected 4")
    if not pl["density_prints"]:
        issues.append("no final-window density line")
    try:
        com = parse_com_file((rundir / names["com"]).read_text()) if (rundir / names["com"]).exists() else None
    except ParseError as e:
        com, _ = None, issues.append(f"centre file malformed: {e}")
    want_frames = TRIAL_VARS["npt_steps"] // TRIAL_VARS["com_every"] + 1
    if com is None:
        issues.append("no centre file")
    else:
        if (len(com["frames"]) not in (want_frames - 1, want_frames) or com["rows_per_frame"] != [MOL[mol]["n_mol"]]
                or com["frames"][-1][0] != TRIAL_VARS["npt_steps"]):
            issues.append(f"centre file holds {len(com['frames'])} frames of {com['rows_per_frame']} rows; "
                          f"expected {want_frames} of {MOL[mol]['n_mol']}, the last at step {TRIAL_VARS['npt_steps']}")
    evidence = accel_evidence(name, screen + "\n" + log_text + "\n" +
                              ((rundir / "log.lammps").read_text(errors="replace")
                               if (rundir / "log.lammps").exists() else ""))
    if not evidence:
        issues.append("no sign in the logs that this accelerator was used")
    return {"path": name, "switches": list(switches), "env": dict(env_extra), "exit_code": rc, "wall_seconds": wall,
            "issues": issues, "ok": not issues, "evidence": evidence[:10], "run_dir": rel(rundir),
            "screen_head": screen[:3000], "screen_tail": screen[-3000:], "command": cmd}


# ---------------------------------------------------------------------------
# Stages
# ---------------------------------------------------------------------------
def default_outdir(prelaunch: bool = False) -> Path:
    return HERE / OUT_REL / PRELAUNCH_NAME if prelaunch else HERE / OUT_REL


def load_bundle_status(bundle: Path) -> dict:
    p = bundle / "prelaunch_status.json"
    if not p.exists():
        raise StageError(f"the bundle has no pre-launch status file at {rel(p)}")
    return read_json(p)


def stage_budget(args) -> int:
    """Price and budget, before anything else; then the time limit T."""
    outdir = Path(args.outdir)
    guard_not_prelaunch(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    raw_p, raw_b = os.environ.get("PRICE_USD_PER_HOUR"), os.environ.get("BUDGET_LEFT_USD")
    try:
        up = read_uptime_s()
    except Exception:
        up = None
    try:
        price = parse_positive_number(raw_p, "PRICE_USD_PER_HOUR")
        budget = parse_positive_number(raw_b, "BUDGET_LEFT_USD")
    except BudgetError as e:
        write_record(outdir, cell={"stage": "budget"}, inputs=[], metric="price and budget variables",
                     values={"PRICE_USD_PER_HOUR": raw_p, "BUDGET_LEFT_USD": raw_b, "error": str(e),
                             "uptime_s": up},
                     decision_rule="both variables present, numeric, finite and above zero; else exit at once",
                     decision="FAIL", notes=str(e))
        print(f"[budget] FATAL: {e}")
        return 3
    t_h = time_limit_h(price, budget)
    values = {"price_usd_per_hour": str(price), "budget_left_usd": str(budget),
              "price": float(price), "budget": float(budget),
              "time_limit_h": float(t_h), "time_limit_h_exact": f"{t_h.numerator}/{t_h.denominator}",
              "time_limit_terms_h": [float(Fraction(18) / price), float(budget / price - Fraction(3, 4))],
              "remote_timeout_s_expected": remote_timeout_s(t_h), "worst_case_usd": float(worst_case_usd(price, t_h)),
              "launch_rule_min_h": float(LAUNCH_MIN_T_H), "uptime_s_at_check": up}
    ok = t_h >= LAUNCH_MIN_T_H
    write_record(outdir, cell={"stage": "budget"}, inputs=[], metric="time limit T from price and budget",
                 values=values, threshold={"T_min_h": 6.29},
                 decision_rule=("T = min(18.0/P, B/P - 0.75) hours from box boot; the launch rule forbids T "
                                "under 6.29 h, so the runner stops at once if it is"),
                 decision="PASS" if ok else "FAIL_LAUNCH_RULE",
                 notes="" if ok else "T is under 6.29 h; the gate's launch rule says this box should not run")
    print(f"[budget] P={float(price)} B={float(budget)} T={float(t_h):.3f} h "
          f"REMOTE_TIMEOUT={remote_timeout_s(t_h)} s")
    return 0 if ok else 4


def stage_verify(args) -> int:
    outdir, bundle = Path(args.outdir), Path(args.bundle)
    guard_not_prelaunch(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    problems, rows = [], []
    man_p = bundle / "manifest.json"
    if not man_p.exists():
        problems.append("the bundle has no manifest")
        man = {"files": {}}
    else:
        man = read_json(man_p)
    for relp, want in sorted(man.get("files", {}).items()):
        p = bundle / relp
        got = sha256_file(p) if p.exists() else None
        rows.append({"file": relp, "expected": want, "found": got, "match": got == want})
        if got != want:
            problems.append(f"{relp}: {'missing' if got is None else 'hash differs'}")
    try:
        status = load_bundle_status(bundle)
        if not status.get("all_passed"):
            problems.append("the pre-launch checks did not all pass")
        if not status.get("slope_band"):
            problems.append("the pre-launch status holds no slope band")
    except StageError as e:
        problems.append(str(e))
    n_boxes = len({r["file"].rsplit("/", 1)[0] for r in rows if r["file"].endswith("in.data")})
    if n_boxes != len(MOL_IDS) * len(RERUNS):
        problems.append(f"the manifest lists {n_boxes} boxes; expected 24")
    write_record(outdir, cell={"stage": "verify"}, inputs=[describe(man_p)] if man_p.exists() else [],
                 metric="shipped box files against the hashes recorded before launch",
                 values={"n_files": len(rows), "problems": problems,
                         "manifest_sha256": sha256_file(man_p) if man_p.exists() else None},
                 decision_rule="every listed file present with its recorded hash; 24 boxes; pre-launch checks passed",
                 decision="PASS" if not problems else "FAIL", notes="; ".join(problems), rows=rows)
    print(f"[verify] {len(rows)} files; {'all match' if not problems else 'PROBLEMS: ' + '; '.join(problems)}")
    return 0 if not problems else 6


def stage_engine(args) -> int:
    outdir, bundle = Path(args.outdir), Path(args.bundle)
    guard_not_prelaunch(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    lmp = Path(args.lmp)
    work = Path(args.work)
    try:
        h = subprocess.run([str(lmp), "-h"], capture_output=True, text=True, timeout=300)
        help_text = h.stdout + h.stderr
    except Exception as e:
        help_text = f"could not run {lmp} -h: {e}"
    info = parse_lmp_help(help_text)
    smi = ""
    try:
        smi = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=60).stdout
    except Exception as e:
        smi = f"nvidia-smi unavailable: {e}"
    write_record(outdir, cell={"stage": "engine", "part": "versions"}, inputs=[],
                 metric="engine version, installed packages and accelerators",
                 values={"lmp": str(lmp), "version_line": info["version"], "packages": info["packages"],
                         "accelerators": info["accelerators"], "install_note": args.install_note,
                         "python": sys.version, "nvidia_smi": smi[:4000], "help_head": help_text[:4000]},
                 decision_rule="recorded as soon as known; no verdict", decision="RECORDED")
    chosen, trials = None, []
    for name, sw, env in engine_candidates(info, os.cpu_count() or 1):
        print(f"[engine] trial: {name}")
        tr = trial_run(lmp, name, sw, env, bundle, work, args.trial_timeout)
        trials.append(tr)
        print(f"[engine]   {'ok' if tr['ok'] else 'failed: ' + '; '.join(tr['issues'])} ({tr['wall_seconds']:.0f}s)")
        if tr["ok"]:
            chosen = tr
            break
    eng = {"lmp": str(lmp), "path": chosen["path"] if chosen else None,
           "switches": chosen["switches"] if chosen else None, "env": chosen["env"] if chosen else None,
           "gpu": bool(chosen and chosen["path"].startswith("GPU")), "chosen_utc": utc_now()}
    if chosen:
        write_json_atomic(outdir / ENGINE_NAME, eng)
    write_record(outdir, cell={"stage": "engine", "part": "path"}, inputs=[],
                 metric="acceleration path that passed a short trial of the edited deck",
                 values={"chosen": eng, "trials": trials,
                         "gpu_path_verified_before_launch": False},
                 decision_rule=("try the GPU path first with command-line switches only, then the processor path; "
                                "the first path whose trial exits cleanly with complete outputs is used"),
                 decision=(("GPU" if eng["gpu"] else "CPU_FALLBACK") if chosen else "NO_PATH_WORKS"))
    return 0 if chosen else 5


def stage_generate(args) -> int:
    importlib.import_module("numpy")  # the per-run analysis needs it; fail before any run starts
    outdir, bundle = Path(args.outdir), Path(args.bundle)
    guard_not_prelaunch(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    status = load_bundle_status(bundle)
    if not status.get("all_passed"):
        void_run(outdir, "the pre-launch checks did not all pass")
        print("[generate] FATAL: the pre-launch checks did not all pass; nothing runs")
        return 2
    budget_p = outdir / (provenance().cell_slug({"stage": "budget"}) + ".json")
    eng_p = outdir / ENGINE_NAME
    if not budget_p.exists() or not eng_p.exists():
        print("[generate] FATAL: run the budget and engine stages first")
        return 2
    brec = read_json(budget_p)
    if brec["decision"] != "PASS":
        print("[generate] FATAL: the budget check did not pass")
        return 2
    t_h = Fraction(brec["values"]["time_limit_h_exact"])
    eng = read_json(eng_p)
    engine = RealEngine(eng["lmp"], eng["switches"], dict(eng["env"], CUDA_CACHE_MAXSIZE="4294967296"),
                        bundle, Path(args.work))
    clock = RealClock()

    def on_cell_done(run, h, rc, wave_size, stopped):
        res = process_cell(run, rc, handle=h, outdir=outdir, wave_size=wave_size, engine_info=eng,
                           stopped=stopped)
        if res["ok"] and run["kind"] == "main":
            engine.finished_dirs[run_key(run)] = h["rundir"]
        print(f"[cell] {run_name(run)}: {res['status']}")
        return res

    def on_probe(res):
        snap = ""
        try:
            snap = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=60).stdout
        except Exception as e:
            snap = f"nvidia-smi unavailable: {e}"
        dec = {"measured": "FITS" if res.get("fits") else "STOP", "deferred": "DEFERRED"}[res["state"]]
        write_record(outdir, cell={"stage": "probe"}, inputs=[], metric="combined step rate in the first wave",
                     values=dict(res, acceleration_path=eng["path"], nvidia_smi=snap[:4000]),
                     threshold={"spare_h": SPARE_H, "remaining_steps": PROBE_REMAINING_STEPS},
                     decision_rule=("hours used so far plus 9.0 million remaining tier-1 steps divided by the "
                                    "measured rate must fit the time limit with 15 minutes spare; else every "
                                    "run stops and the run is reported as not run to the end"),
                     decision=dec)
        print(f"[probe] {dec}: {res.get('rate_steps_per_s', 0):.1f} steps/s (guessed 530)")

    def on_wave_done(wave_rec, tiers_done):
        write_json_atomic(outdir / PROGRESS_NAME, {"last_wave": wave_rec, "tiers_done": tiers_done,
                                                   "utc": utc_now()})

    res = run_schedule(build_tiers(), engine, clock, float(t_h), poll_s=args.poll, on_cell_done=on_cell_done,
                       on_probe=on_probe, on_wave_done=on_wave_done)
    if not res["tier1_complete"]:
        void_run(outdir, f"incomplete run: tier 1 did not finish ({res['stop_reason']})", LABEL_INCOMPLETE)
    write_record(outdir, cell={"stage": "generate"}, inputs=[], metric="tiers run under the clock rule",
                 values=dict(res, acceleration_path=eng["path"], rerun_note=LABEL_RERUNS),
                 decision_rule=("tiers run in order, four runs per wave; a wave starts only if the clock rule allows "
                                "and every higher tier is done; tier 1 must finish for any verdict"),
                 decision=("COMPLETE" if res["stop_reason"] is None else
                           ("STOPPED_AFTER_TIER1" if res["tier1_complete"] else "NOT_RUN_TO_THE_END")),
                 notes=res["stop_reason"] or "")
    print(f"[generate] tiers done {res['tiers_done']}; stop: {res['stop_reason']}")
    return 0 if res["tier1_complete"] else 4


def stage_endpoints(args) -> int:
    outdir, bundle = Path(args.outdir), Path(args.bundle)
    guard_not_prelaunch(outdir)
    status = load_bundle_status(bundle)
    reference = read_json(bundle / "reference.json")
    if not (outdir / STATE_NAME).exists() and not status.get("all_passed"):
        void_run(outdir, "the pre-launch checks did not all pass")
    inputs = [describe(bundle / "reference.json"), describe(bundle / "prelaunch_status.json")]
    res = run_endpoints(outdir, reference, status, inputs)
    for n, d in res["decisions"].items():
        print(f"[endpoint {n}] {d['decision']}" + (f" ({'; '.join(d['labels'])})" if d["labels"] else ""))
    print(f"[summary] run_valid={res['run_valid']}")
    return 0


def _move_aside(p: Path) -> None:
    if p.exists():
        dest = p.with_name(p.name + "_old_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
        p.rename(dest)
        print(f"[extract] moved {rel(p)} aside to {rel(dest)}")


def _run_builder(job):
    cmd, env, timeout = job["cmd"], job["env"], job["timeout"]
    t0 = time.monotonic()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=timeout)
        rc, so, se = p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        rc, so, se = "timeout", (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""), "timeout"
    return dict(job, rc=rc, stdout=so, stderr=se, wall_seconds=time.monotonic() - t0)


def stage_extract(args) -> int:
    """The directive's pre-launch steps, in order, on this workstation, at no cost."""
    import numpy
    outdir, bundle = Path(args.outdir), Path(args.bundle)
    if (outdir.exists() and any(outdir.iterdir())) or bundle.exists():
        if not args.fresh:
            print(f"[extract] {rel(outdir)} or {rel(bundle)} already exists; rerun with --fresh to move them aside")
            return 2
        _move_aside(outdir)
        _move_aside(bundle)
    outdir.mkdir(parents=True, exist_ok=True)
    bundle.mkdir(parents=True, exist_ok=True)
    tb = Path(args.toolchain_bin)
    lmp, py, packmol = tb / "lmp", Path(args.builder_python), tb / "packmol"
    status = {"all_passed": False, "launch": "DO NOT LAUNCH", "failed_step": None, "steps": {},
              "created_utc": utc_now()}

    def save_status():
        write_json_atomic(bundle / "prelaunch_status.json", status)

    def summary(decision, notes=""):
        write_record(outdir, cell={"stage": "prelaunch-summary"}, inputs=[], metric="pre-launch steps",
                     values=status, decision_rule="every pre-launch step passes; else do not launch",
                     decision=decision, notes=notes)

    def fail(step, reason):
        status["steps"][step] = "FAIL"
        status["failed_step"], status["failure"] = step, reason
        void_run(outdir, f"pre-launch step failed: {step}: {reason}")
        save_status()
        summary("DO_NOT_LAUNCH", reason)
        print(f"[extract] STOP before launch: {step}: {reason}")
        return 3

    # Step 0: the committed inputs and the binding texts, by hash.
    rows0, bad0 = [], []
    for key, (p, want) in list(COMMITTED.items()) + list(BINDING.items()):
        got = sha256_file(HERE / p) if (HERE / p).exists() else None
        rows0.append({"name": key, "path": p, "expected": want, "found": got, "match": got == want})
        if got != want:
            bad0.append(f"{p}: {'missing' if got is None else 'hash differs'}")
    for tool in (lmp, py, packmol):
        if not tool.exists():
            bad0.append(f"toolchain program missing: {rel(tool)}")
    write_record(outdir, cell={"stage": "prelaunch", "step": "inputs"}, inputs=[describe(HERE / r["path"]) for r in rows0],
                 metric="committed inputs and binding texts against their recorded hashes", values={"problems": bad0},
                 decision_rule="every file present with its recorded hash; the local toolchain present",
                 decision="PASS" if not bad0 else "FAIL", rows=rows0)
    if bad0:
        return fail("inputs", "; ".join(bad0))
    status["steps"]["inputs"] = "PASS"

    # Endpoint 1: the data-only pre-check.
    ds_text = (HERE / COMMITTED["dataset"][0]).read_text()
    pr_text = (HERE / COMMITTED["predictions"][0]).read_text()
    e1 = data_precheck(ds_text, pr_text)
    write_record(outdir, cell={"stage": "prelaunch", "step": "data-precheck", "endpoint": 1},
                 inputs=[describe(HERE / COMMITTED["dataset"][0], 835), describe(HERE / COMMITTED["predictions"][0])],
                 metric="Spearman rho between the two committed reference columns, the order, and the free orderings",
                 values={k: v for k, v in e1.items() if k != "rows_by_id"}, threshold={"rho": 1.0},
                 decision_rule=RULES[1], decision="PASS" if e1["passed"] else "FAIL",
                 notes=LABEL_E1 if e1["passed"] else "; ".join(e1["problems"]),
                 rows=[dict(v, molecule=k) for k, v in e1["rows_by_id"].items()])
    if not e1["passed"]:
        return fail("data-precheck", "endpoint 1 failed: " + "; ".join(e1["problems"] or ["order or rho differs"]))
    status["steps"]["data-precheck"] = "PASS"
    status["e1"] = {"passed": True, "rho_between_files": e1["rho_between_files"], "order": e1["order_dataset"],
                    "free_orderings": e1["free_orderings"], "label": LABEL_E1}
    reference = build_reference(e1)
    write_json_atomic(bundle / "reference.json", reference)

    # The decks the box will use.
    deck_text = (HERE / COMMITTED["deck"][0]).read_text()
    main_deck = edit_main_deck(deck_text)
    (bundle / "equilibrate.in").write_text(deck_text)
    (bundle / "deck_main_cp1.in").write_text(main_deck)
    (bundle / "deck_extension_cp1.in").write_text(EXTENSION_DECK)
    (bundle / "deck_zero_step_cp1.in").write_text(ZERO_STEP_DECK)
    diff = list(difflib.unified_diff(deck_text.splitlines(), main_deck.splitlines(), "equilibrate.in",
                                     "deck_main_cp1.in", lineterm=""))
    write_record(outdir, cell={"stage": "prelaunch", "step": "decks"},
                 inputs=[describe(HERE / COMMITTED["deck"][0])], metric="the design's listed deck edits, as a diff",
                 values={"main_deck_sha256": sha256_text(main_deck), "extension_deck_sha256": sha256_text(EXTENSION_DECK),
                         "zero_step_deck_sha256": sha256_text(ZERO_STEP_DECK), "diff": diff,
                         "set_on_the_command_line": RUN_KINDS},
                 decision_rule="only the listed edits: remove the density-matching stage; write centres every 1 ps",
                 decision="RECORDED")

    # Step 1: build 24 boxes with the committed builder.
    env = os.environ.copy()
    env["PATH"] = str(tb) + os.pathsep + env.get("PATH", "")
    jobs = []
    for m in MOLECULES:
        for r in RERUNS:
            seed = PACK_SEEDS[r]
            out_b = bundle / m["id"] / f"pack{seed}"
            cmd = [str(py), str(HERE / COMMITTED["builder"][0]), "--smiles", m["smiles"], "--n", str(m["n_mol"]),
                   "--density", str(PACK_DENSITY), "--seed", str(seed), "--out", str(out_b)]
            jobs.append({"mol": m["id"], "rerun": r, "seed": seed, "out": out_b, "cmd": cmd, "env": env,
                         "timeout": args.build_timeout})
    print(f"[extract] building {len(jobs)} boxes, {args.jobs} at a time")
    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as ex:
        built = list(ex.map(_run_builder, jobs))
    bad1 = []
    for b in built:
        files = {}
        for f in ("in.data", "in.init", "in.settings", "metadata.json"):
            p = b["out"] / f
            files[f] = sha256_file(p) if p.exists() else None
        ok = b["rc"] == 0 and all(files.values())
        if not ok:
            bad1.append(f"{b['mol']} seed {b['seed']}: exit {b['rc']}")
        write_record(outdir, cell={"stage": "prelaunch", "step": "build", "molecule": b["mol"], "pack_seed": b["seed"]},
                     inputs=[describe(HERE / COMMITTED["builder"][0])], metric="one box built by the committed builder",
                     values={"command": [str(c) for c in b["cmd"]], "exit_code": b["rc"], "stdout": b["stdout"],
                             "stderr": b["stderr"], "wall_seconds": b["wall_seconds"], "files_sha256": files,
                             "packing_density_g_cm3": PACK_DENSITY},
                     decision_rule="the builder exits 0 and writes all four files", decision="PASS" if ok else "FAIL")
    if bad1:
        return fail("build", "; ".join(bad1))
    status["steps"]["build"] = "PASS"

    # Step 2: net charge per molecule near zero, and the counts, from the builder's metadata.
    rows2, bad2 = [], []
    for m in MOLECULES:
        for r in RERUNS:
            md = parse_builder_metadata((bundle / m["id"] / f"pack{PACK_SEEDS[r]}" / "metadata.json").read_text())
            apm = sum(m["formula"].values())
            ok = (abs(md["net_charge_per_molecule"]) <= CHARGE_TOL and md["n_molecules"] == m["n_mol"]
                  and md["atoms_per_molecule"] == apm and md["density_g_cm3"] == PACK_DENSITY
                  and md["smiles"] == m["smiles"])
            rows2.append({"molecule": m["id"], "pack_seed": PACK_SEEDS[r], "net_charge": md["net_charge_per_molecule"],
                          "n_molecules": md["n_molecules"], "atoms_per_molecule": md["atoms_per_molecule"],
                          "density_g_cm3": md["density_g_cm3"], "box_length_A": md.get("box_length_angstrom"),
                          "ok": ok})
            if not ok:
                bad2.append(f"{m['id']} seed {PACK_SEEDS[r]}")
    write_record(outdir, cell={"stage": "prelaunch", "step": "charge"}, inputs=[],
                 metric="net charge per molecule and counts from the builder's metadata",
                 values={"problems": bad2}, threshold={"abs_net_charge_max": CHARGE_TOL},
                 decision_rule=("net charge per molecule within 1e-6 of zero; the design's molecule count; the "
                                "formula's atom count; packing density 0.75"),
                 decision="PASS" if not bad2 else "FAIL", rows=rows2)
    if bad2:
        return fail("charge", "; ".join(bad2))
    status["steps"]["charge"] = "PASS"

    # Steps 3 and 4: zero-step read with the local LAMMPS, then the density by hand.
    rows3, bad3, rows4, bad4 = [], [], [], []
    zwork = HERE / WORK_REL / "prelaunch_zero_step"
    zwork.mkdir(parents=True, exist_ok=True)
    zenv = os.environ.copy()
    zenv.update({"OMP_NUM_THREADS": "1", "OMPI_MCA_plm": "isolated", "OMPI_MCA_rmaps_base_oversubscribe": "yes",
                 "OMPI_MCA_btl_vader_single_copy_mechanism": "none"})
    for m in MOLECULES:
        for r in RERUNS:
            box = bundle / m["id"] / f"pack{PACK_SEEDS[r]}"
            wd = zwork / f"{m['id']}_pack{PACK_SEEDS[r]}"
            if wd.exists():
                shutil.rmtree(wd)
            wd.mkdir(parents=True)
            cmd = [str(lmp), "-in", str(bundle / "deck_zero_step_cp1.in"), "-var", "system_dir", str(box),
                   "-log", str(wd / "log.lammps"), "-screen", str(wd / "screen.out")]
            try:
                p = subprocess.run(cmd, cwd=wd, capture_output=True, text=True, env=zenv, timeout=1800)
                rc = p.returncode
            except subprocess.TimeoutExpired:
                rc = "timeout"
            log_text = (wd / "log.lammps").read_text(errors="replace") if (wd / "log.lammps").exists() else ""
            pl = parse_lammps_log(log_text)
            blk = pl["blocks"][-1] if pl["blocks"] else None
            dens = atoms = None
            if blk and blk["rows"]:
                hdr = blk["header"]
                if "Density" in hdr and "Atoms" in hdr:
                    dens = blk["rows"][0][hdr.index("Density")]
                    atoms = int(blk["rows"][0][hdr.index("Atoms")])
            want_atoms = m["n_mol"] * sum(m["formula"].values())
            ok3 = rc == 0 and not pl["errors"] and atoms == want_atoms and dens is not None
            rows3.append({"molecule": m["id"], "pack_seed": PACK_SEEDS[r], "exit_code": rc, "atoms": atoms,
                          "expected_atoms": want_atoms, "density_step0": dens, "errors": pl["errors"],
                          "warnings": pl["warnings"], "log_verbatim": log_text, "ok": ok3})
            if not ok3:
                bad3.append(f"{m['id']} seed {PACK_SEEDS[r]}")
                continue
            hand = parse_lammps_data((box / "in.data").read_text())
            relerr = abs(hand["density_g_cm3"] / dens - 1.0)
            ok4 = relerr <= I2_TOL
            rows4.append({"molecule": m["id"], "pack_seed": PACK_SEEDS[r], "density_by_hand": hand["density_g_cm3"],
                          "density_lammps_step0": dens, "relative_difference": relerr,
                          "total_mass_amu": hand["total_mass_amu"], "volume_A3": hand["volume_A3"], "ok": ok4})
            if not ok4:
                bad4.append(f"{m['id']} seed {PACK_SEEDS[r]}")
    write_record(outdir, cell={"stage": "prelaunch", "step": "zero-step-read"}, inputs=[],
                 metric="zero-step read of every box with the local LAMMPS build", values={"problems": bad3},
                 decision_rule="exit 0, no error line, the expected atom count, a step-0 density",
                 decision="PASS" if not bad3 else "FAIL", rows=rows3)
    if bad3:
        return fail("zero-step-read", "; ".join(bad3))
    status["steps"]["zero-step-read"] = "PASS"
    write_record(outdir, cell={"stage": "prelaunch", "step": "density-by-hand"}, inputs=[],
                 metric="density by hand from each data file against LAMMPS at step 0", values={"problems": bad4},
                 threshold={"relative_tolerance": I2_TOL},
                 decision_rule="total atom mass over box volume, in g/cm3, within 0.1% of LAMMPS's step-0 density",
                 decision="PASS" if not bad4 else "FAIL", rows=rows4)
    if bad4:
        return fail("density-by-hand", "; ".join(bad4))
    status["steps"]["density-by-hand"] = "PASS"

    # Step 5: the planted known-truth check and the queued planted controls.
    pl = run_planted_checks()
    names = {"a": "planted (a): recovered-D bias, 0.1-0.4 ns", "b": "planted (b): slope band",
             "c": "planted (c): t^0.7 walks labelled non-diffusive", "d": "planted (d): every label reachable",
             "I3": "planted proxy path", "I5_part1": "planted 1.8 ns window split at 1.0 ns",
             "I7": "planted family orderings and the 576 enumeration",
             "I8": "planted rerun margin: halt on identical reruns, positive otherwise",
             "I10": "planted (a) at the two other lag windows"}
    for k, label in names.items():
        v = pl[k]
        write_record(outdir, cell={"stage": "prelaunch", "step": "planted", "check": k}, inputs=[],
                     metric=label, values={kk: vv for kk, vv in v.items() if kk not in ("rows",)},
                     decision_rule={"a": "mean relative bias within 2 standard errors over 160 planted cells",
                                    "b": "narrowest band around 1 holding at least 95% of 200 ordinary slopes",
                                    "c": "at least 95% of 200 t^0.7 slopes fall outside the band",
                                    "d": "known order passes, reversed refutes, a 5% density error fails the gate, "
                                         "a t^0.7 slope is flagged",
                                    "I3": "every planted viscosity back within 1 part in 1e6; rho +1, and -1 reversed",
                                    "I5_part1": "bias within 2 standard errors; every planted join passes",
                                    "I7": "12, 0 and 12 with a log offset of ln 4; 26 and 68 of 576",
                                    "I8": "identical reruns halt WRONG_VARIANCE_SOURCE; planted reruns give a positive "
                                          "margin over 6,561 picks, and 256 with two",
                                    "I10": "bias within 2 standard errors at 0.05-0.2 and 0.2-0.4 ns"}[k],
                     decision="PASS" if v["passed"] else "FAIL", rows=v.get("rows"))
    status["planted"] = {"all_passed": pl["all_passed"],
                         "checks": {k: {"passed": pl[k]["passed"]} for k in names},
                         "slope_band": pl["b"]["band"], "a_bias": pl["a"]["mean_relative_bias"],
                         "a_standard_error": pl["a"]["standard_error"]}
    status["slope_band"] = pl["b"]["band"]
    if not pl["all_passed"]:
        return fail("planted", "failed: " + ", ".join(k for k in names if not pl[k]["passed"]))
    status["steps"]["planted"] = "PASS"

    # Step 6: hashes of every bundle file and the tool versions.
    versions = {"python": sys.version, "numpy": numpy.__version__}
    try:
        import rdkit
        versions["rdkit"] = rdkit.__version__
    except Exception as e:
        versions["rdkit"] = f"not importable here: {e}"
    meta_dir = tb.parent / "conda-meta"
    for pkgname in ("lammps", "packmol", "rdkit", "numpy", "python", "openmpi"):
        hits = sorted(meta_dir.glob(f"{pkgname}-[0-9]*.json")) if meta_dir.exists() else []
        if hits:
            d = read_json(hits[0])
            versions[f"conda:{pkgname}"] = f"{d.get('version')} {d.get('build')}"
    try:
        versions["lmp -h"] = parse_lmp_help(subprocess.run([str(lmp), "-h"], capture_output=True, text=True,
                                                           timeout=300, env=zenv).stdout)["version"]
    except Exception as e:
        versions["lmp -h"] = f"failed: {e}"
    status["tool_versions"] = versions
    status["all_passed"] = True
    status["launch"] = "LAUNCH ALLOWED"
    save_status()
    files = {}
    for p in sorted(bundle.rglob("*")):
        if p.is_file() and p.name != "manifest.json":
            files[str(p.relative_to(bundle))] = sha256_file(p)
    write_json_atomic(bundle / "manifest.json", {"files": files, "created_utc": utc_now()})
    write_record(outdir, cell={"stage": "prelaunch", "step": "hashes-and-versions"}, inputs=[],
                 metric="sha256 of every shipped file, and the version of every tool used",
                 values={"n_files": len(files), "tool_versions": versions,
                         "manifest_sha256": sha256_file(bundle / "manifest.json")},
                 decision_rule="recorded; the box checks every shipped file against these hashes",
                 decision="RECORDED", rows=[{"file": k, "sha256": v} for k, v in files.items()])
    status["steps"]["hashes-and-versions"] = "PASS"
    summary("LAUNCH_ALLOWED")
    print(f"[extract] all pre-launch steps passed; bundle {rel(bundle)} ({len(files)} files) is ready to ship")
    return 0


def stage_decktrial(args) -> int:
    """Optional, local, free: a few hundred steps of the edited deck on one box with the
    local processor build. It judges nothing; it only catches deck errors before launch."""
    outdir, bundle = Path(args.outdir), Path(args.bundle)
    lmp = Path(args.toolchain_bin) / "lmp"
    env = {"OMP_NUM_THREADS": "1", "OMPI_MCA_plm": "isolated", "OMPI_MCA_rmaps_base_oversubscribe": "yes",
           "OMPI_MCA_btl_vader_single_copy_mechanism": "none"}
    tr = trial_run(lmp, "CPU (local deck trial)", [], env, bundle, HERE / WORK_REL / "prelaunch_deck_trial",
                   args.trial_timeout)
    write_record(outdir, cell={"stage": "prelaunch", "step": "deck-trial"}, inputs=[describe(bundle / "deck_main_cp1.in")],
                 metric="optional local trial of the edited deck (judges nothing)", values=tr,
                 decision_rule="the edited deck runs a few hundred steps and writes complete outputs",
                 decision="PASS" if tr["ok"] else "FAIL", notes="; ".join(tr["issues"]))
    print(f"[decktrial] {'ok' if tr['ok'] else 'FAILED: ' + '; '.join(tr['issues'])}")
    return 0 if tr["ok"] else 7


# ---------------------------------------------------------------------------
# Selftest: standard library only, planted rows with known decisions
# ---------------------------------------------------------------------------
_PLANTED_XGB = {"mol_00105": 8.730885530105278, "mol_00305": 24.81221580505371, "mol_00400": 11.987561853147511,
                "mol_00426": 26.304483501588013, "mol_00557": 2.4852394175543613, "mol_00764": 16.0765839457935,
                "mol_00942": 4.83047062110704, "mol_01025": 5.215729689763804}


def _planted_csvs(swap_experimental=False):
    ds = ["molecule_id,molecule_name,canonical_smiles,density_40c,viscosity_40c",
          "mol_99999,decoy,CCCC,0.5,1.0"]
    pr = ["molecule_id,canonical_smiles,experimental_40C_mPa_s,xgboost_descriptors_40C",
          "mol_99999,CCCC,1.0,1.0"]
    for m in MOLECULES:
        eta = m["eta_ref"]
        ds.append(f"{m['id']},{m['name'].replace(',', ' ')},{m['smiles']},{m['rho_ref']},{eta}")
        ex = eta
        if swap_experimental and m["id"] == "mol_00105":
            ex = 15.9
        pr.append(f"{m['id']},{m['smiles']},{ex},{_PLANTED_XGB[m['id']]}")
    return "\n".join(ds) + "\n", "\n".join(pr) + "\n"


def _plant_cell_record(outdir, mol, rerun, kind, *, d_main, density, exponent=1.0, d_alt=None, status="finished",
                       join_passed=True, spacing_passed=True, wall=3600.0):
    n_lags = 900 if kind == "extension" else 400
    rows = [{"lag_ps": float(k), "msd_A2": (0.0 if k == 0 else 6.0 * d_main * (k ** exponent))}
            for k in range(n_lags + 1)]
    d = {"main": d_main, "alt_short": (d_alt or {}).get("alt_short", d_main),
         "alt_late": (d_alt or {}).get("alt_late", d_main)}
    slopes = {"main": exponent, "alt_short": exponent, "alt_late": exponent}
    if kind == "extension":
        d, slopes = {"long": d_main}, {"long": exponent}
    values = {"status": status, "kind": kind, "molecule": mol, "rerun": rerun, "D_A2_per_ps": d,
              "loglog_slope": slopes, "density_final_window_g_cm3": density, "box_hours_share": wall / 3600 / 4,
              "thermo_stage": {"density_mean_0p20_0p45_ns": density * 0.999, "temperature_mean_K": 313.1}}
    if kind == "extension":
        values["join_check"] = {"passed": join_passed, "join_jump_A": 0.5 if join_passed else 40.0,
                                "inner_max_part1_A": 0.9, "inner_max_part2_A": 0.8}
    if kind == "timestep_1fs":
        values["frame_spacing_check"] = {"passed": spacing_passed, "spacing_ps_min": 1.0 if spacing_passed else 2.0}
    cell = {"stage": "cell", "molecule": mol, "rerun": rerun, "kind": kind, "attempt": 1}
    return write_record(outdir, cell=cell, inputs=[], metric="planted cell", values=values,
                        decision_rule="planted", decision=status.upper(), rows=rows)


def _plant_run(outdir, *, factors=None, density_scale=None, reverse=False, exponents=None, alt=None,
               skip=(), ext=True, one_fs=True, identical=False, join_bad=(), d1fs_factor=1.0):
    """Write planted cell records for all eight molecules."""
    ref = reference_from_constants(_PLANTED_XGB)["molecules"]
    default_f = {1: 1.00, 2: 1.03, 3: 0.97}
    wobble = {"mol_00105": (1.00, 1.06, 0.96), "mol_00426": (1.00, 0.95, 1.05)}
    for m in MOL_IDS:
        eta = ref[m]["eta_ref_mPa_s"]
        if reverse:
            eta = 1.0 / eta
        rho = ref[m]["rho_paper_g_cm3"] * ((density_scale or {}).get(m, 1.0))
        d0 = planted_d_a2ps(eta, ref[m]["molar_mass_g_mol"], rho)
        for r in RERUNS:
            if (m, r) in skip:
                continue
            f = 1.0 if identical else (factors or {}).get((m, r), wobble.get(m, (1.0, 1.0, 1.0))[r - 1] * default_f[r])
            dalt = None
            if alt and m in alt:
                dalt = {"alt_short": d0 * alt[m]}
            _plant_cell_record(outdir, m, r, "main", d_main=d0 * f, density=rho,
                               exponent=(exponents or {}).get(m, 1.0), d_alt=dalt)
        if ext:
            _plant_cell_record(outdir, m, 1, "extension", d_main=d0, density=rho, join_passed=m not in join_bad)
    if one_fs:
        ref_m = ref[TIMESTEP_MOL]
        d0 = planted_d_a2ps(ref_m["eta_ref_mPa_s"], ref_m["molar_mass_g_mol"], ref_m["rho_paper_g_cm3"])
        _plant_cell_record(outdir, TIMESTEP_MOL, 1, "timestep_1fs", d_main=d0 * d1fs_factor,
                           density=ref_m["rho_paper_g_cm3"])
    return ref


class _FakeClock:
    def __init__(self, start_h):
        self.t = start_h * 3600.0

    def now(self):
        return self.t

    def uptime_h(self):
        return self.t / 3600.0

    def sleep(self, s):
        self.t += s


class _FakeEngine:
    """Simulated runs: each run advances at a fixed per-run step rate."""

    def __init__(self, clock, per_run_rate, fail_plan=None, slow=None):
        self.clock, self.rate = clock, per_run_rate
        self.fail_plan = dict(fail_plan or {})
        self.slow = dict(slow or {})
        self.killed = []

    def start(self, run):
        k = run_key(run)
        rate = self.rate / self.slow.get(k, 1.0)
        fail = self.fail_plan.get(k, 0) >= run["attempt"]
        return {"run": run, "t0": self.clock.t, "dur": TOTAL_STEPS[run["kind"]] / rate, "rate": rate, "fail": fail,
                "killed": False}

    def poll(self, h):
        if h["killed"]:
            return -9
        if self.clock.t >= h["t0"] + h["dur"]:
            return 1 if h["fail"] else 0
        return None

    def progress(self, h):
        if h["run"]["kind"] != "main":
            return None
        done = min(TOTAL_STEPS["main"], (self.clock.t - h["t0"]) * h["rate"])
        s3 = done - PRE_STAGE3_STEPS["main"]
        return int(s3 // 500 * 500) if s3 >= 0 else None

    def kill(self, h):
        h["killed"] = True
        self.killed.append(run_name(h["run"]))


def selftest() -> int:
    fails = []
    n_checks = [0]

    def check(name, cond, extra=""):
        n_checks[0] += 1
        if not cond:
            fails.append(f"{name} {extra}".strip())

    def approx(a, b, tol=1e-9):
        return a is not None and b is not None and abs(a - b) <= tol * max(1.0, abs(b))

    # --- Budget, clock and plan arithmetic ---------------------------------------------
    table = {"1.29": (13.953, 52032, 18.97), "1.50": (11.917, 44700, 19.00), "1.99": (8.798, 33471, 19.00)}
    for p, (t_want, rt_want, wc_want) in table.items():
        P, B = parse_positive_number(p, "P"), parse_positive_number("19.0", "B")
        T = time_limit_h(P, B)
        check(f"T at ${p}", round(float(T), 3) == t_want, f"{float(T)}")
        check(f"REMOTE_TIMEOUT at ${p}", remote_timeout_s(T) == rt_want, f"{remote_timeout_s(T)}")
        check(f"worst case at ${p}", round(float(worst_case_usd(P, T)), 2) == wc_want, f"{float(worst_case_usd(P, T))}")
        check(f"worst case at ${p} never above B", worst_case_usd(P, T) <= B)
    check("launch rule allows $2.69", time_limit_h(Fraction("2.69"), Fraction(19)) >= LAUNCH_MIN_T_H)
    check("launch rule refuses $2.70", time_limit_h(Fraction("2.70"), Fraction(19)) < LAUNCH_MIN_T_H)
    check("design rule up to $1.33", time_limit_h(Fraction("1.33"), Fraction(19)) == Fraction(18) / Fraction("1.33"))
    for bad in (None, "", "abc", "0", "-1.2", "nan", "inf", "1e999999"):
        try:
            parse_positive_number(bad, "X")
            ok = bad == "1e999999"
        except BudgetError:
            ok = True
        check(f"price parser rejects {bad!r}", ok)
    tiers = build_tiers()
    steps_by_tier = {n: sum(TOTAL_STEPS[r["kind"]] for r in runs) for n, runs in tiers}
    check("tier step totals", steps_by_tier == {1: 9_600_000, 2: 4_000_000, 3: 4_800_000, 4: 1_150_000},
          str(steps_by_tier))
    check("probe remainder", steps_by_tier[1] - 4 * (PRE_STAGE3_STEPS["main"] + PROBE_STAGE3_STEPS) == 9_000_000)
    check("main run is 600,000 steps", 50000 + 50000 + 500000 == TOTAL_STEPS["main"])
    check("planned cost", 3 * NS_PER_RUN == 3.375 and round(3 * NS_PER_RUN / 80 * 100, 1) == 4.2)
    for kind in ("main", "timestep_1fs", "extension"):
        s = RUN_KINDS[kind]
        check(f"{kind}: frames 1 ps apart", approx(s["com_every"] * s["timestep_fs"] / 1000.0, 1.0))
        check(f"{kind}: density window 250 ps",
              approx(s["density_sample_every"] * s["density_sample_repeat"] * s["timestep_fs"] / 1000.0, 250.0)
              and s["density_sample_freq"] == s["density_sample_every"] * s["density_sample_repeat"])
        end = s.get("npt_steps", 1000000 if kind == "extension" else None)
        check(f"{kind}: window ends at the stage end", s["density_avg_start"] + s["density_sample_freq"] == end)
    check("velocity seed formula", velocity_seed(2) == 4928459 + 20014)

    # --- Chance counts, rank arithmetic -------------------------------------------------
    k8, tot = chance_at_least(0.8)
    k6, _ = chance_at_least(0.6)
    check("chance of rho >= 0.8 is 439/40320", (k8, tot) == (439, 40320), f"{k8}/{tot}")
    check("chance of rho >= 0.6 is 2318/40320", k6 == 2318, f"{k6}")
    fc = family_chance_counts()
    check("family chance 26 and 68 of 576", (fc["ge10"], fc["ge9"], fc["total"]) == (26, 68, 576), str(fc))
    check("spearman +1", spearman([1, 2, 3, 4], [10, 20, 30, 40]) == 1.0)
    check("spearman -1", spearman([1, 2, 3, 4], [4, 3, 2, 1]) == -1.0)
    check("average ranks with ties", average_ranks([3, 1, 3, 2]) == [3.5, 1.0, 3.5, 2.0])
    check("spearman with ties", approx(spearman([1, 2, 2, 3], [1, 2, 3, 4]), 0.9486832980505138))
    check("spearman undefined on constant input", spearman([1, 1, 1], [1, 2, 3]) is None)

    # --- Chemistry, the data-only pre-check and the free orderings --------------------------
    for m in MOLECULES:
        f = formula_from_smiles(m["smiles"])
        check(f"formula of {m['name']}", f == m["formula"], f"{formula_text(f)}")
    for bad in ("C[NH]", "CCl", "C1CC", "C(C"):
        try:
            formula_from_smiles(bad)
            check(f"formula parser rejects {bad}", False)
        except ValueError:
            check(f"formula parser rejects {bad}", True)
    ds, pr = _planted_csvs()
    e1 = data_precheck(ds, pr)
    check("pre-check passes on the committed values", e1["passed"], str(e1["problems"]))
    check("pre-check order", e1.get("order_dataset") == REFERENCE_ORDER)
    fo = e1.get("free_orderings", {})
    check("free ordering: molar mass 0.524", round(fo.get("molar_mass", 0), 3) == 0.524, str(fo))
    check("free ordering: reference density 0.048", round(fo.get("reference_density", 0), 3) == 0.048, str(fo))
    check("free ordering: XGBoost 0.738", round(fo.get("xgboost", 0), 3) == 0.738, str(fo))
    ds2, pr2 = _planted_csvs(swap_experimental=True)
    e1b = data_precheck(ds2, pr2)
    check("pre-check fails when the two files order differently", not e1b["passed"])
    check("pre-check fails on a changed molecule code", not data_precheck(ds.replace("CCOCCOCCOCCOCCOCC,1.069",
                                                                                     "CCOCCOCCOCCOCCOC,1.069"), pr)["passed"])

    # --- I3: the planted proxy path -------------------------------------------------------
    i3 = planted_proxy_check()
    check("I3 planted proxy path", i3["passed"], f"worst {i3['worst_relative_error']}")
    check("proxy units: 1e-10 m2/s at R=5 A", approx(KB_J_PER_K * T_KELVIN / (6 * math.pi * 1e-10 * 5e-10) * 1e3,
                                                    proxy_mpas(0.01, 1.0, 1.0) * sphere_radius_m(1.0, 1.0) / 5e-10, 1e-12))
    # --- I7 -------------------------------------------------------------------------------
    check("I7 planted family orderings", planted_family_check()["passed"])

    # --- Parsers ----------------------------------------------------------------------------
    com_txt = format_com_text([0, 500, 1000], [[0.0, 0.0, 0.0, 1.0, 1.0, 1.0], [0.5, 0, 0, 1, 1.5, 1],
                                               [1.0, 0, 0, 1, 2.0, 1]], 2)
    pc = parse_com_file(com_txt)
    check("centre parser: frames", [s for s, _ in pc["frames"]] == [0, 500, 1000] and pc["rows_per_frame"] == [2])
    check("centre parser: values", list(pc["frames"][1][1]) == [0.5, 0.0, 0.0, 1.0, 1.5, 1.0])
    cut = "\n".join(com_txt.splitlines()[:-1]) + "\n"
    pcut = parse_com_file(cut)
    check("centre parser: cut-off last frame flagged", pcut["truncated_last_frame"] and len(pcut["frames"]) == 2)
    short_row = "\n".join(com_txt.splitlines()[:-1] + [" ".join(com_txt.splitlines()[-1].split()[:3])]) + "\n"
    for bad, label in ((short_row, "a short row"),
                       (com_txt.replace("\n2 1 1.5 1\n", "\n3 1 1.5 1\n"), "a row index out of order"),
                       ("1 0.0 0.0 0.0\n", "a row before a header"),
                       (com_txt.replace("500 2", "500 1"), "more rows than declared")):
        try:
            parse_com_file(bad)
            check(f"centre parser rejects {label}", False)
        except ParseError:
            check(f"centre parser rejects {label}", True)
    check("centre tail reader", last_header_step_from_tail(com_txt, True) == 1000)
    check("centre tail reader ignores a half-written header",
          last_header_step_from_tail(com_txt + "1500 2", True) == 1000)
    check("centre tail reader drops a cut first line",
          last_header_step_from_tail("00 2\n1 0 0 0\n", False) is None)
    log_txt = "\n".join([
        "LAMMPS (29 Aug 2024 - Update 1)", "KOKKOS mode with Kokkos version 4.3.1 is enabled",
        "  will use up to 1 GPU(s) per node",
        "   Step          Temp          Press          Density         Volume",
        "         0   313.15        1.0            0.80            1000", "WARNING: Shake determinant < 0.0",
        "      5000   313.20        2.0            0.81            990",
        "Loop time of 12.5 on 1 procs for 5000 steps with 15000 atoms", "",
        "Performance: 34.560 ns/day, 0.694 hours/ns, 400.000 timesteps/s, 98.7% CPU use with 1 MPI tasks",
        "   Step          Temp          Press          Density         Volume",
        "         0   313.0          1.0            0.81            990",
        "    100000   313.1          1.5            0.812           985",
        "    225000   313.2          1.0            0.814           984",
        "    375000   313.2          1.0            0.815           983",
        "    500000   313.2          1.0            0.816           982",
        "Loop time of 900.0 on 1 procs for 500000 steps with 15000 atoms",
        'print           "NPT average density target from final window: ${rho_target} g/cm^3"',
        "NPT average density target from final window: 0.815500000000 g/cm^3",
        "ERROR: Lost atoms: original 15000 current 14999", "Total wall time: 0:15:12"])
    pl = parse_lammps_log(log_txt)
    check("log parser: blocks", len(pl["blocks"]) == 2 and len(pl["blocks"][0]["rows"]) == 2, str(len(pl["blocks"])))
    check("log parser: loops", [x["steps"] for x in pl["loops"]] == [5000, 500000])
    check("log parser: speed", pl["performance"] == [400.0])
    check("log parser: density print", pl["density_prints"] == [0.8155])
    check("log parser: errors and warnings", len(pl["errors"]) == 1 and len(pl["warnings"]) == 1)
    check("log parser: wall time", pl["total_wall_time"] == "0:15:12")
    th = stage3_thermo(pl["blocks"][-1], 2.0, "main")
    check("thermo readout: 0.20-0.45 ns", approx(th["density_mean_0p20_0p45_ns"], (0.812 + 0.814) / 2))
    check("thermo readout: last 250 ps", approx(th["density_mean_last_250_ps_thermo"], (0.815 + 0.816) / 2))
    check("density file parser", parse_density_file("# x\n# TimeStep v_rho\n375000 0.81\n500000 0.82\n")
          == [(375000, 0.81), (500000, 0.82)])
    data_txt = "\n".join(["LAMMPS data file generated by smiles2loplsaa", "", "3 atoms", "2 atom types", "",
                          "0.000000 10.000000 xlo xhi", "0.000000 10.000000 ylo yhi", "0.000000 10.000000 zlo zhi",
                          "", "Masses", "", "    1    12.011000   # ct", "    2     1.008000   # hc", "", "Atoms", "",
                          "1 1 1 -0.1 1 1 1", "2 1 2 0.05 2 2 2", "3 1 2 0.05 3 3 3", "", "Bonds", "",
                          "1 1 1 2", ""])
    hd = parse_lammps_data(data_txt)
    check("data parser: mass and volume", approx(hd["total_mass_amu"], 14.027) and approx(hd["volume_A3"], 1000.0))
    check("data parser: density by hand", approx(hd["density_g_cm3"], 14.027 / 1000.0 / 0.602214076))
    try:
        parse_lammps_data(data_txt.replace("3 atoms", "4 atoms"))
        check("data parser rejects a count mismatch", False)
    except ParseError:
        check("data parser rejects a count mismatch", True)
    md = parse_builder_metadata(json.dumps({"n_molecules": 163, "atoms_per_molecule": 92, "net_charge_per_molecule": 0.0,
                                            "density_g_cm3": 0.75, "smiles": "C"}))
    check("builder metadata parser", md["atoms_per_molecule"] == 92)
    try:
        parse_builder_metadata("{}")
        check("builder metadata parser rejects missing keys", False)
    except ParseError:
        check("builder metadata parser rejects missing keys", True)
    help_txt = ("\nLarge-scale Atomic/Molecular Massively Parallel Simulator - 29 Aug 2024 - Update 1\n\n"
                "Accelerator configuration:\n\nKOKKOS package API: CUDA Serial\nKOKKOS package precision: double\n"
                "OPENMP package API: OpenMP\n\nInstalled packages:\n\nASPHERE KOKKOS KSPACE MOLECULE \nOPENMP RIGID\n\n"
                "List of individual style options included in this LAMMPS executable\n")
    hi = parse_lmp_help(help_txt)
    check("help parser: version", hi["version"] == "29 Aug 2024 - Update 1")
    check("help parser: packages", {"KOKKOS", "OPENMP", "KSPACE"} <= set(hi["packages"]) and "List" not in hi["packages"])
    cands = engine_candidates(hi, 32)
    check("engine order: KOKKOS GPU first, then processor", [c[0][:3] for c in cands] == ["GPU", "CPU"]
          and cands[0][1] == ["-k", "on", "g", "1", "-sf", "kk"] and cands[1][1][-1] == "8")
    check("KOKKOS evidence", bool(accel_evidence(cands[0][0], log_txt)))
    check("no KOKKOS evidence in a processor log", not accel_evidence(cands[0][0], "LAMMPS (29 Aug 2024)\n"))
    check("engine order without KOKKOS: processor only", [c[0][:3] for c in engine_candidates(
        {"packages": ["KSPACE", "MOLECULE"]}, 8)] == ["CPU"])
    check("uptime parser", parse_uptime("12345.67 54321.00\n") == 12345.67)
    try:
        parse_uptime("")
        check("uptime parser rejects empty text", False)
    except ParseError:
        check("uptime parser rejects empty text", True)

    # --- Deck edits ---------------------------------------------------------------------------
    mini = "\n".join(["fix eq_npt all npt", DECK_RUN_NPT, "unfix           eq_npt", DECK_REMOVE_FIRST,
                      "reset_timestep  0", "run             ${deform_steps}", DECK_REMOVE_LAST,
                      "unfix           constrain_h", "write_restart   x"])
    ed = edit_main_deck(mini)
    check("deck edit: density-matching stage removed", "deform_steps" not in ed and "reset_timestep" not in ed)
    check("deck edit: centre output before the constant-pressure run",
          ed.index("cp1_com_out") < ed.index(DECK_RUN_NPT) and "write_restart" in ed)
    try:
        edit_main_deck(mini + "\n" + DECK_RUN_NPT)
        check("deck edit refuses a doubled anchor", False)
    except DeckEditError:
        check("deck edit refuses a doubled anchor", True)
    real_deck = HERE / COMMITTED["deck"][0]
    if real_deck.exists() and sha256_file(real_deck) == COMMITTED["deck"][1]:
        rd = real_deck.read_text()
        er = edit_main_deck(rd)
        removed = [ln for ln in difflib.ndiff(rd.splitlines(), er.splitlines()) if ln.startswith("- ")]
        added = [ln for ln in difflib.ndiff(rd.splitlines(), er.splitlines()) if ln.startswith("+ ")]
        check("committed deck: only the listed edits", len(added) == len(COM_BLOCK)
              and all("deform" in ln or "target" in ln or "scale" in ln or "rho_now" in ln or "eq_nvt" in ln
                      or ln.strip() in ("-", "- reset_timestep  0", "- run             ${deform_steps}")
                      or "match_density" in ln or ln.strip().startswith("- x final") or ln.strip().startswith("- y final")
                      or ln.strip().startswith("- z final") for ln in removed), str(removed))
        check("committed deck: write_restart kept", "write_restart" in er and "reset_timestep  0" in er)
    ev = engine_vars("main", 2, "/tmp/x")
    evd = dict(zip(ev[1::3], ev[2::3]))
    check("engine variables: 2 fs and 500,000 constant-pressure steps",
          evd["timestep_fs"] == "2.0" and evd["npt_steps"] == "500000" and evd["run_id"] == "2" and evd["T"] == "313.15")

    # --- Trajectory arithmetic and the degeneracy checks --------------------------------------
    n2 = 2
    ball = [(i * 500, array("d", [0.1 * i, 0, 0, -0.1 * i, 0, 0])) for i in range(1001)]
    res_b = analyze_frames(ball, n2, 2.0, WINDOW_MAIN_PS, {"main": (100.0, 400.0)}, backend="plain")
    check("ballistic MSD is exact", approx(res_b["msd"][10], 0.01 * 100) and approx(res_b["msd"][300], 0.01 * 90000))
    check("ballistic log-log slope is 2", approx(res_b["fits"]["main"]["loglog_slope"], 2.0, 1e-9))
    drifted = [(s, array("d", [v[0] + 0.3 * k, v[1] - 0.2 * k, v[2], v[3] + 0.3 * k, v[4] - 0.2 * k, v[5]]))
               for k, (s, v) in enumerate(ball)]
    res_d = analyze_frames(drifted, n2, 2.0, WINDOW_MAIN_PS, {"main": (100.0, 400.0)}, backend="plain")
    check("drift removal leaves the MSD unchanged", all(approx(a, b, 1e-9) for a, b in zip(res_d["msd"], res_b["msd"])))
    lin = [0.0] + [6 * 0.02 * k + 0.5 for k in range(1, 401)]
    fl = fit_msd(lin, 100, 400)
    check("linear fit returns D", approx(fl["D_A2_per_ps"], 0.02))
    pw = [0.0] + [3.0 * k ** 0.7 for k in range(1, 401)]
    check("power-law log-log slope", approx(fit_msd(pw, 100, 400)["loglog_slope"], 0.7, 1e-9))
    rw = random.Random(3)
    walk, pos = [], [0.0] * 9
    for i in range(1001):
        walk.append((i * 500, array("d", pos)))
        pos = [p + rw.gauss(0, 0.1) for p in pos]
    rw_res = analyze_frames(walk, 3, 2.0, WINDOW_MAIN_PS, {"main": (100.0, 400.0)}, backend="plain")
    sel = remove_drift_plain([v for _, v in walk[200:1001]], 3)
    brute = sum(sum((sel[t + 7][k] - sel[t][k]) ** 2 for k in range(9)) for t in range(801 - 7)) / ((801 - 7) * 3)
    check("MSD over all time origins", approx(rw_res["msd"][7], brute, 1e-12))
    check("degenerate: frozen molecule", analyze_frames([(s, array("d", [0, 0, 0, v[3], v[4], v[5]])) for s, v in ball],
                                                        2, 2.0, WINDOW_MAIN_PS, {"main": (100.0, 400.0)})["issues"] != [])
    tele = [(s, array("d", list(v))) for s, v in walk]
    tele[600][1][0] += 25.0
    check("degenerate: a centre jumps 25 angstroms",
          any("jumped" in x for x in analyze_frames(tele, 3, 2.0, WINDOW_MAIN_PS, {"main": (100.0, 400.0)})["issues"]))
    gap = walk[:500] + walk[501:]
    check("degenerate: a missing frame", any("spacing" in x for x in
                                             analyze_frames(gap, 3, 2.0, WINDOW_MAIN_PS, {"main": (100.0, 400.0)})["issues"]))
    short = walk[:900]
    check("degenerate: window not covered", any("not fully covered" in x for x in
                                                analyze_frames(short, 3, 2.0, WINDOW_MAIN_PS, {"main": (100.0, 400.0)})["issues"]))
    nanw = [(s, array("d", list(v))) for s, v in walk]
    nanw[300][1][2] = float("nan")
    check("degenerate: a non-finite position", any("finite" in x for x in
                                                   analyze_frames(nanw, 3, 2.0, WINDOW_MAIN_PS, {"main": (100.0, 400.0)})["issues"]))
    back = list(walk)
    back[10], back[11] = back[11], back[10]
    check("degenerate: steps out of order", any("increase" in x for x in
                                                analyze_frames(back, 3, 2.0, WINDOW_MAIN_PS, {"main": (100.0, 400.0)})["issues"]))
    check("degenerate: wrong row count", any("one row per molecule" in x for x in
                                             analyze_frames(walk, 4, 2.0, WINDOW_MAIN_PS, {"main": (100.0, 400.0)})["issues"]))
    check("degenerate: engine exit code", degenerate_engine(1, {"errors": [], "loops": [{}] * 4}, "main") != [])
    check("degenerate: error line", degenerate_engine(0, {"errors": ["ERROR: x"], "loops": [{}] * 4}, "main") != [])
    check("degenerate: loop count", degenerate_engine(0, {"errors": [], "loops": [{}] * 3}, "main") != [])
    check("clean engine output", degenerate_engine(0, {"errors": [], "loops": [{}]}, "extension") == [])
    check("degenerate: stopped run", degenerate_engine(None, {"errors": [], "loops": []}, "main", True) != [])
    check("degenerate: no density", degenerate_density(None, [], 500000)[1] != [])
    check("degenerate: density sources disagree", degenerate_density(0.8, [(500000, 0.9)], 500000)[1] != [])
    check("clean density", degenerate_density(0.8, [(375000, 0.7), (500000, 0.8000001)], 500000) == (0.8, []))
    check("degenerate: density file lacks the final row", degenerate_density(0.8, [(375000, 0.7)], 500000)[1] != [])
    wave = [2.0 * math.sin(2 * math.pi * k / 400.0) for k in range(400)]
    osc = [(i * 500, array("d", [wave[i % 400], 0, 0, -wave[i % 400], 0, 0])) for i in range(1001)]
    osc_issues = analyze_frames(osc, 2, 2.0, WINDOW_MAIN_PS, {"main": (100.0, 400.0)})["issues"]
    check("degenerate: a fitted D that is not positive", any("not positive" in x and "D" in x for x in osc_issues),
          str(osc_issues))
    check("degenerate: an MSD of zero at a fitted lag", any("MSD is not positive" in x for x in osc_issues))
    check("degenerate: temperature runaway", degenerate_temperature(400.0) != [] and degenerate_temperature(None) != [])
    check("clean temperature", degenerate_temperature(313.5) == [])
    check("degenerate: centre file missing", degenerate_com(None, 2, 1000) != [])
    check("degenerate: centre file cut off", degenerate_com(pcut, 2, 1000) != [])
    check("degenerate: centre rows", degenerate_com(pc, 3, 1000) != [])
    check("degenerate: centre file ends early", degenerate_com(pc, 2, 1500) != [])
    check("clean centre file", degenerate_com(pc, 2, 1000) == [])

    # --- I5 part 2 (join check) and I12 (time axis) --------------------------------------------
    p1, p2 = walk[:501], walk[500:]
    jc = join_check(p1, p2, 3)
    check("join check passes on a clean split", jc["passed"] and approx(jc.get("duplicate_frame_difference_A"), 0.0))
    shifted = [(s, array("d", [x + (40.0 if k % 3 == 0 else 0.0) for k, x in enumerate(v)])) for s, v in p2]
    jbad = join_check(p1, shifted, 3)
    check("join check fails on a lost periodic image", not jbad["passed"] and jbad["join_jump_A"] > 35.0)
    merged = merge_parts(p1, p2)
    check("merge drops the duplicate frame", [s for s, _ in merged] == [s for s, _ in walk])
    one_fs = [(i * 1000, v) for i, (_, v) in enumerate(walk)]
    check("I12: 1 fs frames are 1.000 ps apart", spacing_check(one_fs, 1.0)["passed"])
    check("I12: frame count is never used for time", not spacing_check(one_fs, 2.0)["passed"])

    # --- Planted check logic: bias, band, labels (d), margin halt (I8) ----------------------
    bc = bias_check([1.01, 0.99, 1.0, 1.02, 0.98], [1.0] * 5)
    check("bias check passes when centred", bc["passed"])
    check("bias check fails when shifted", not bias_check([1.10, 1.11, 1.09, 1.10, 1.12], [1.0] * 5)["passed"])
    band, h = slope_band([1.0 + 0.001 * k for k in range(-50, 50)] + [1.5] * 0)
    check("slope band is the narrowest symmetric 95% band", approx(h, 0.047) and band[0] < 1 < band[1], str(h))
    dlab = planted_labels_check(0.7, (0.95, 1.05))
    check("planted (d): every label reachable", dlab["passed"], str(dlab["reached"]))
    dsets = []
    rs = random.Random(PLANTED_SEED)
    for _ in range(3):
        dsets.append({m: PLANTED_D * (1 + rs.gauss(0, 0.03)) for m in MOL_IDS})
    i8 = planted_margin_check(dsets)
    check("I8: identical reruns halt WRONG_VARIANCE_SOURCE", i8["identical_halts"])
    check("I8: 6,561 picks and 256 with two reruns", i8["three_reruns"]["n_picks"] == 6561
          and i8["two_reruns"]["n_picks"] == 256 and i8["passed"])
    check("E3 decisions", e3_decide(0.81)[0] == "PASS" and e3_decide(0.79)[0] == "REFUTED"
          and e3_decide(0.59)[0] == "REFUTED_BELOW_ABANDON_LINE" and LABEL_D1_REFUTED in e3_decide(0.7)[1])
    check("E8 decisions", e8_decide(0.70, 0.738, 0.01)[0] == "REFUTED" and e8_decide(0.738, 0.738, 0.01)[0] == "REFUTED"
          and e8_decide(0.745, 0.738, 0.01) == ("DOWNGRADED", [LABEL_E8_NOISE])
          and e8_decide(0.80, 0.738, 0.01)[0] == "PASS")
    check("E8 ablation labels", e8_ablation_labels(0.8, 0.8, 0.5) == [LABEL_SIZE]
          and e8_ablation_labels(0.8, 0.7, 0.81) == [LABEL_DIFFUSION] and e8_ablation_labels(0.8, 0.7, 0.7) == [])
    check("E9 label at 3, none at 2", nondiffusive_labels(3) == [LABEL_NONDIFF.format(n=3)] and nondiffusive_labels(2) == [])
    check("E10 labels", e10_labels({"main": 0.83, "alt_short": 0.79, "alt_late": 0.9}) == [LABEL_WINDOW]
          and e10_labels({"main": 0.83, "alt_short": 0.81, "alt_late": 0.9}) == [LABEL_ROBUST]
          and e10_labels({"main": 0.7, "alt_short": 0.9, "alt_late": 0.9}) == [])

    # --- The scheduler, with a simulated engine and clock ----------------------------------
    def sched(price, rate, fail_plan=None, slow=None, start_h=1.0):
        T = float(time_limit_h(Fraction(price), Fraction(19)))
        clk = _FakeClock(start_h)
        eng = _FakeEngine(clk, rate, fail_plan, slow)
        got = []

        def done(run, h, rc, ws, stopped):
            got.append((run_name(run), rc, stopped))
            return {"ok": rc == 0 and not stopped}
        probes = []
        res = run_schedule(build_tiers(), eng, clk, T, poll_s=15.0, on_cell_done=done, on_probe=probes.append,
                           log=lambda *_: None)
        return res, got, eng, probes

    per_run = GUESSED_RATE / 4
    r_fast, got, _, pr_ = sched("1.29", per_run * 2)
    check("scheduler: a fast box runs every tier", r_fast["tiers_done"] == [1, 2, 3, 4] and r_fast["stop_reason"] is None
          and len(got) == 33, f"{r_fast['tiers_done']} {r_fast['stop_reason']}")
    check("scheduler: the probe fits on a fast box", pr_ and pr_[0]["state"] == "measured" and pr_[0]["fits"])
    check("scheduler: probe rate is the combined rate", pr_ and abs(pr_[0]["rate_steps_per_s"] / (4 * per_run * 2) - 1) < 0.05,
          str(pr_[0]["rate_steps_per_s"] if pr_ else None))
    r_slow, got_s, eng_s, pr_s = sched("1.50", per_run / 3)
    check("scheduler: a box 3x slower stops at the probe", not r_slow["tier1_complete"]
          and "speed probe" in (r_slow["stop_reason"] or "") and len(eng_s.killed) == 4, str(r_slow["stop_reason"]))
    want_h = 1.0 + (PRE_STAGE3_STEPS["main"] + PROBE_STAGE3_STEPS) / (per_run / 3) / 3600.0
    check("scheduler: the slow probe stops once wave 1 reaches the probe point",
          want_h <= r_slow["uptime_h_end"] <= want_h + 2 * 15.0 / 3600, f"{r_slow['uptime_h_end']} vs {want_h}")
    r_199, _, _, _ = sched("1.99", per_run)
    check("scheduler: at $1.99 and the guessed speed, tiers 1 and 2 fit", r_199["tiers_done"] == [1, 2]
          and "clock rule" in (r_199["stop_reason"] or ""), f"{r_199['tiers_done']} {r_199['stop_reason']}")
    r_ret, got_r, _, _ = sched("1.29", per_run * 2, fail_plan={("mol_00105", 1, "main"): 1})
    check("scheduler: a failed run is repeated once", r_ret["tiers_done"] == [1, 2, 3, 4]
          and sum(1 for g in got_r if g[0].startswith("mol_00105 rerun 1 main")) == 2)
    r_two, _, _, _ = sched("1.29", per_run * 2, fail_plan={("mol_00105", 1, "main"): 2})
    check("scheduler: a run failing twice leaves tier 1 unfinished", not r_two["tier1_complete"]
          and "tier 1 did not finish" in (r_two["stop_reason"] or ""))
    r_lim, got_l, _, _ = sched("1.29", per_run * 2, slow={("mol_00105", 3, "main"): 40.0})
    check("scheduler: the time limit stops a wave that overruns", r_lim["tiers_done"] == [1, 2]
          and "time limit" in (r_lim["stop_reason"] or "") and any(g[2] for g in got_l), str(r_lim["stop_reason"]))

    # --- Endpoints end to end on planted records, with the void rules ----------------------
    status_ok = {"e1": {"passed": True}, "planted": {"all_passed": True}, "slope_band": [0.95, 1.05]}
    with tempfile.TemporaryDirectory(prefix="cp1_selftest_") as td:
        td = Path(td)
        # A: everything passes.
        oa = td / "a"
        oa.mkdir()
        _plant_run(oa)
        refd = reference_from_constants(_PLANTED_XGB)
        ra = run_endpoints(oa, refd, status_ok)
        d = {k: v["decision"] for k, v in ra["decisions"].items()}
        check("planted pass: run valid", ra["run_valid"])
        check("planted pass: gate", d[2] == "PASS", d[2])
        check("planted pass: main", d[3] == "PASS", d[3])
        check("planted pass: stability", d[4] == "PASS", d[4])
        check("planted pass: longer run", d[5] == "PASS", d[5])
        check("planted pass: cost label", d[6] == "MET_BY_PLAN" and LABEL_COST in ra["decisions"][6]["labels"])
        check("planted pass: family", d[7] == "PASS", d[7])
        check("planted pass: added value", d[8] == "PASS", d[8])
        check("planted pass: no non-diffusive label", d[9] == "NO_LABEL", d[9])
        check("planted pass: windows robust", d[10] == "ROBUST", d[10])
        check("planted pass: timestep", d[12] == "PASS", d[12])
        check("planted pass: pre-check label", LABEL_E1 in ra["decisions"][1]["labels"])
        f2v = json.loads((oa / "readout-extension-slope_stage-endpoints.json").read_text())["values"]["rows"]
        check("planted pass: extension slopes reported", all(approx(r["loglog_slope_0p1_0p9_ns"], 1.0) for r in f2v))
        dsv = json.loads((oa / "readout-density-settling_stage-endpoints.json").read_text())["values"]["rows"]
        check("planted pass: density settling readout", all(approx(r["mean_0p20_0p45_ns"],
                                                                   0.999 * r["mean_last_250_ps_deck_window"]) for r in dsv))
        recs_a = {p.name: json.loads(p.read_text()) for p in oa.glob("*.json") if p.name != STATE_NAME}
        check("every record carries a validity field", all("run_valid" in r for r in recs_a.values()))
        check("a summary record exists", "stage-summary.json" in recs_a)
        check("the summary reports a valid run", recs_a["stage-summary.json"]["decision"] == "RUN_VALID")
        e8v = recs_a["endpoint-8_stage-endpoints.json"]["values"]
        check("planted pass: margin over 6,561 picks", e8v["margin"]["n_picks"] == 6561 and e8v["margin"]["margin_sd"] > 0)

        # B: one molecule's density is 5% off; the gate fails and the void reaches every record.
        ob = td / "b"
        ob.mkdir()
        _plant_run(ob, density_scale={"mol_00105": 1.05})
        before = {p.name: json.loads(p.read_text())["run_valid"] for p in ob.glob("*.json")}
        check("cells start out valid", all(before.values()))
        rb = run_endpoints(ob, refd, status_ok)
        after = {p.name: json.loads(p.read_text()) for p in ob.glob("*.json") if p.name != STATE_NAME}
        check("planted gate failure: the run is void", not rb["run_valid"])
        check("planted gate failure: every record is void", all(r["run_valid"] is False for r in after.values()),
              str([n for n, r in after.items() if r["run_valid"] is not False]))
        check("planted gate failure: every cell file is void",
              all(r["run_valid"] is False and r["run_valid_voided_retroactively"] is True
                  for n, r in after.items() if "stage-cell" in n))
        check("planted gate failure: the gate record reads FAIL",
              after["endpoint-2_stage-endpoints.json"]["values"]["rule_outcome_untrusted"] == "FAIL")
        check("planted gate failure: the main claim gets no verdict",
              after["endpoint-3_stage-endpoints.json"]["decision"] == "NO_VERDICT"
              and LABEL_UNTRUSTED in after["endpoint-3_stage-endpoints.json"]["values"]["labels"])
        check("planted gate failure: the summary reports the void", after["stage-summary.json"]["decision"] == "RUN_VOID")
        st_b = read_state(ob)
        write_record(ob, cell={"stage": "late"}, inputs=[], metric="m", values={}, decision_rule="r", decision="X")
        check("a void reaches records written later",
              json.loads((ob / "stage-late.json").read_text())["run_valid"] is False and not st_b["run_valid"])
        void_run(ob, "another reason")
        check("a void is never undone", read_state(ob)["run_valid"] is False and len(read_state(ob)["voided_by"]) == 2)

        # C: reversed order; refuted with the narrowed label, below the abandon line.
        oc = td / "c"
        oc.mkdir()
        _plant_run(oc, reverse=True)
        rc_ = run_endpoints(oc, refd, status_ok)
        check("planted reversed: refuted below the abandon line",
              rc_["decisions"][3]["decision"] == "REFUTED_BELOW_ABANDON_LINE"
              and LABEL_ABANDON in rc_["decisions"][3]["labels"], str(rc_["decisions"][3]))
        check("planted reversed: family refuted with discordant pairs",
              rc_["decisions"][7]["decision"] == "REFUTED")
        check("planted reversed: added value refuted", rc_["decisions"][8]["decision"] == "REFUTED")
        check("planted reversed: the run stays valid", rc_["run_valid"])

        # D: identical reruns; both dispersion rules halt WRONG_VARIANCE_SOURCE.
        od = td / "d"
        od.mkdir()
        _plant_run(od, identical=True)
        rd_ = run_endpoints(od, refd, status_ok)
        check("planted zero dispersion: the margin halts", rd_["decisions"][8]["decision"] == WRONG_VARIANCE_SOURCE,
              rd_["decisions"][8]["decision"])
        check("planted zero dispersion: the timestep spread halts",
              rd_["decisions"][12]["decision"] == WRONG_VARIANCE_SOURCE, rd_["decisions"][12]["decision"])

        # E: tier 1 incomplete; descriptive only, no verdict, everywhere.
        oe = td / "e"
        oe.mkdir()
        _plant_run(oe, skip={("mol_00942", 2)}, ext=False, one_fs=False)
        re_ = run_endpoints(oe, refd, status_ok)
        recs_e = {p.name: json.loads(p.read_text()) for p in oe.glob("*.json") if p.name != STATE_NAME}
        check("planted incomplete run: void", not re_["run_valid"])
        check("planted incomplete run: every record void", all(r["run_valid"] is False for r in recs_e.values()))
        check("planted incomplete run: label on verdicts",
              LABEL_INCOMPLETE in recs_e["endpoint-3_stage-endpoints.json"]["values"]["labels"]
              and recs_e["endpoint-3_stage-endpoints.json"]["decision"] == "NO_VERDICT")
        check("planted incomplete run: the longer-run endpoint is not judged",
              recs_e["endpoint-5_stage-endpoints.json"]["values"]["rule_outcome_untrusted"] == "NOT_JUDGED")

        # F: labels: window-dependent, non-diffusive, a failed join, a stretched 1 fs D.
        of = td / "f"
        of.mkdir()
        alt = {"mol_00105": 0.2, "mol_00426": 0.2, "mol_00400": 5.0, "mol_00557": 0.1}
        _plant_run(of, alt=alt, exponents={"mol_00105": 0.7, "mol_00764": 0.7, "mol_00305": 0.7},
                   join_bad=("mol_00942",), d1fs_factor=1.5)
        rf = run_endpoints(of, refd, status_ok)
        check("planted labels: window-dependent", LABEL_WINDOW in rf["decisions"][3]["labels"]
              and rf["decisions"][10]["decision"] == "WINDOW_DEPENDENT", str(rf["decisions"][10]))
        check("planted labels: non-diffusive for 3 of 8", LABEL_NONDIFF.format(n=3) in rf["decisions"][3]["labels"]
              and rf["decisions"][9]["decision"] == "LABEL")
        check("planted labels: a failed join leaves the longer run not judged",
              rf["decisions"][5]["decision"] == "NOT_JUDGED")
        check("planted labels: a shifted 1 fs D makes the result conditional",
              rf["decisions"][12]["decision"] == "CONDITIONAL_ON_TIMESTEP")
        check("planted labels: non-diffusive never refutes", rf["decisions"][3]["decision"] == "PASS")
        o12 = td / "g"
        o12.mkdir()
        _plant_run(o12)
        bad1fs = json.loads((o12 / "attempt-1_kind-timestep_1fs_molecule-mol_00557_rerun-1_stage-cell.json").read_text())
        bad1fs["values"]["frame_spacing_check"] = {"passed": False}
        write_json_atomic(o12 / "attempt-1_kind-timestep_1fs_molecule-mol_00557_rerun-1_stage-cell.json", bad1fs)
        rg = run_endpoints(o12, refd, status_ok)
        check("I12: a bad time axis leaves the timestep endpoint not judged", rg["decisions"][12]["decision"] == "NOT_JUDGED")

        # The budget and hash-check stages, end to end, with planted variables and a planted bundle.
        saved = {k: os.environ.get(k) for k in ("PRICE_USD_PER_HOUR", "BUDGET_LEFT_USD")}
        try:
            ob_ = td / "box_out"
            for env_p, env_b, want_rc in (("1.29", "19.0", 0), (None, "19.0", 3), ("abc", "19.0", 3),
                                          ("1.29", "0", 3), ("2.70", "19.0", 4)):
                for k, v in (("PRICE_USD_PER_HOUR", env_p), ("BUDGET_LEFT_USD", env_b)):
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v
                got_rc = stage_budget(argparse.Namespace(outdir=str(ob_ / f"b{env_p}_{env_b}")))
                check(f"budget stage with P={env_p} B={env_b}", got_rc == want_rc, str(got_rc))
            brec = json.loads((ob_ / "b1.29_19.0" / "stage-budget.json").read_text())
            check("budget record: T and timeout", round(brec["values"]["time_limit_h"], 3) == 13.953
                  and brec["values"]["remote_timeout_s_expected"] == 52032 and "run_valid" in brec)
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        bun = td / "bundle"
        files = {}
        for m in MOL_IDS:
            for r in RERUNS:
                f = bun / m / f"pack{PACK_SEEDS[r]}" / "in.data"
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(f"planted {m} {r}\n")
                files[str(f.relative_to(bun))] = sha256_file(f)
        write_json_atomic(bun / "prelaunch_status.json", {"all_passed": True, "slope_band": [0.95, 1.05]})
        files["prelaunch_status.json"] = sha256_file(bun / "prelaunch_status.json")
        write_json_atomic(bun / "manifest.json", {"files": files})
        check("hash-check stage passes on an intact bundle",
              stage_verify(argparse.Namespace(outdir=str(td / "v1"), bundle=str(bun))) == 0)
        (bun / MOL_IDS[3] / "pack61454" / "in.data").write_text("tampered\n")
        check("hash-check stage fails on a changed file",
              stage_verify(argparse.Namespace(outdir=str(td / "v2"), bundle=str(bun))) == 6)
        try:
            stage_verify(argparse.Namespace(outdir=str(td / "prelaunch"), bundle=str(bun)))
            check("box stages refuse a folder named prelaunch", False)
        except SystemExit:
            check("box stages refuse a folder named prelaunch", True)

        # No output describes reruns with the forbidden word.
        word = "repli" + "cat"
        texts = [p.read_text().lower() for p in td.rglob("*.json")]
        check("no output calls reruns by the forbidden word", not any(word in t for t in texts))
        check("no label calls reruns by the forbidden word",
              not any(word in v.lower() for k, v in globals().items() if k.startswith("LABEL_") and isinstance(v, str)))

    # --- The frozen record writer's own selftest -----------------------------------------------
    try:
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            prc = provenance()._selftest()
        check("the frozen record writer's selftest", prc == 0, buf.getvalue())
    except Exception as e:
        check("the frozen record writer's selftest", False, str(e))

    heavy = [m for m in ("numpy", "rdkit") if m in sys.modules]
    check("selftest imported no heavy package", not heavy, str(heavy))
    for f in fails:
        print(f"FAIL {f}")
    print(f"selftest: {n_checks[0]} checks, " + ("PASS" if not fails else f"{len(fails)} FAILURES"))
    return 1 if fails else 0


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if "--selftest" in argv:
        return selftest()
    ap = argparse.ArgumentParser(description="Runner for run cp1. See the module text for the stages.")
    sub = ap.add_subparsers(dest="stage", required=True)

    def common(p, prelaunch=False):
        p.add_argument("--outdir", default=str(default_outdir(prelaunch)))
        p.add_argument("--bundle", default=str(HERE / BUNDLE_REL))

    p = sub.add_parser("extract", help="pre-launch steps on this workstation")
    common(p, prelaunch=True)
    p.add_argument("--toolchain-bin", default=str(HERE / TOOLCHAIN_BIN_REL))
    p.add_argument("--builder-python", default=str(HERE / TOOLCHAIN_BIN_REL / "python"))
    p.add_argument("--jobs", type=int, default=min(4, os.cpu_count() or 1))
    p.add_argument("--build-timeout", type=int, default=BUILD_TIMEOUT_S)
    p.add_argument("--fresh", action="store_true", help="move earlier pre-launch output aside first")
    p = sub.add_parser("decktrial", help="optional local trial of the edited deck")
    common(p, prelaunch=True)
    p.add_argument("--toolchain-bin", default=str(HERE / TOOLCHAIN_BIN_REL))
    p.add_argument("--trial-timeout", type=int, default=TRIAL_TIMEOUT_S)
    p = sub.add_parser("budget", help="on the box: price, budget and the time limit")
    common(p)
    p = sub.add_parser("engine", help="on the box: pick the acceleration path by a short trial")
    common(p)
    p.add_argument("--lmp", required=True)
    p.add_argument("--work", default=str(HERE / WORK_REL))
    p.add_argument("--trial-timeout", type=int, default=TRIAL_TIMEOUT_S)
    p.add_argument("--install-note", default="")
    p = sub.add_parser("verify", help="on the box: shipped files against their hashes")
    common(p)
    p = sub.add_parser("generate", help="on the box: the simulations")
    common(p)
    p.add_argument("--work", default=str(HERE / WORK_REL))
    p.add_argument("--poll", type=float, default=POLL_S)
    p = sub.add_parser("endpoints", help="the endpoints and the summary")
    common(p)
    args = ap.parse_args(argv)
    fn = {"extract": stage_extract, "decktrial": stage_decktrial, "budget": stage_budget, "engine": stage_engine,
          "verify": stage_verify, "generate": stage_generate, "endpoints": stage_endpoints}[args.stage]
    try:
        return fn(args)
    except StageError as e:
        print(f"[{args.stage}] FATAL: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
