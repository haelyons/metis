#!/usr/bin/env python3
"""Runner for one pre-registered measurement (tag m3): how fast the coolant card's own simulation
protocol runs on one rented A100 GPU box.

WHAT IS MEASURED, IN PLAIN WORDS
  A liquid box of 250 nonylcyclohexane molecules (11,250 atoms) is relaxed to its liquid density
  (the "equilibration"). It is then simulated three times for 200 ps each, all three starting
  from the same relaxed state, with the LAMMPS molecular dynamics engine and its GPU package.
  Speed is read in simulated nanoseconds per day (ns/day) from the "Performance:" line LAMMPS
  prints after each run. The three runs differ only in how much they sample:
    run a (prod_a)  the committed production deck as written: pressure tensor and heat flux
                    written every 5 steps;
    run b (prod_b)  pressure tensor only (listed edit 1);
    run c (prod_c)  no per-step sampling at all (listed edit 2).
  The three runs share one box and one starting state, so they are not independent samples.
  The card assumed 250 ns/day and gates its plan on 150 ns/day.

STAGES (each runnable on its own; onbox_m3.sh calls them in this order)
  guard --stage S     cost and time check; prints allowed_seconds=N; exit 3 means stop
  extract             reads what the install left (lmp -h, micromamba list, nvidia-smi), checks
                      that the GPU package is listed, writes the run labels, builds the edited
                      deck copies, and re-checks the pre-launch build gate (endpoint E1)
  generate --stage S  S = dryrun | copy | equilibrate | prod_a | prod_b | prod_c
                      equilibrate: if the committed deck stops with an error naming comm_style,
                      balance, tiled or rcb, its three load-balancing lines are deleted in a copy
                      (listed edit 3, results_m3/decks/equilibrate_noballance.in) and the
                      equilibration is run once more from that copy; any other error stops the run
  endpoints           every endpoint and instrument-control record, from saved outputs only
  summary             m3_summary.json: restates the records; decides nothing
  void --reason R     marks the run invalid
  --selftest          standard library only; runs no LAMMPS

VALIDITY
  Every record carries a run_valid field. These set run_valid=false in RUN_VALID.json: the
  pre-launch build gate failing, the density anchor failing or not being readable, the install
  failing or lacking the GPU package, a stage stopping the run, or the cost or time guard
  stopping the run. Every record written afterwards carries run_valid=false: endpoint records,
  per-run records and raw rows alike. When the run ends early (a nonzero exit code), the summary
  labels every finished run "incomplete run: descriptive only, no verdict".

EXIT CODES
  0  finished (the optional runs b and c may have been cut by the time or cost guard)
  2  install failed or the GPU package is not listed
  3  stopped by the cost or time guard (or price or budget missing)
  4  the pre-launch build gate failed
  10 dry run   11 box copy   12 equilibration   13 run a   14 run b   15 run c
  16 endpoints failed   17 extract failed   1 usage or unexpected error
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # never leave a cache folder beside the frozen record writer

import argparse
import collections
import contextlib
import difflib
import hashlib
import importlib.util
import io
import json
import math
import os
import platform
import re
import shutil
import socket
import subprocess
import tempfile
import time
import traceback
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "m3"

# ---------------------------------------------------------------------------------------------
# The design, as numbers. Every value below is copied from the design record or the execution
# note (EXEC_NOTE.md); none is tuned here.
# ---------------------------------------------------------------------------------------------
BOX_NAME = "box_mol00557_n250_d0.30_s61453"
T_STR = "313.15"
TIMESTEP_FS = Decimal("2.0")

EQUIL_VARS = (("T", "313.15"), ("P", "1.0"), ("timestep_fs", "2.0"), ("pushoff_steps", "50000"),
              ("settle_steps", "100000"), ("npt_steps", "250000"), ("deform_steps", "100000"),
              ("density_avg_start", "125000"), ("density_sample_every", "100"),
              ("density_sample_repeat", "1250"), ("density_sample_freq", "250000"),
              ("thermo_every", "5000"), ("run_id", "1"))
PROD_VARS = (("T", "313.15"), ("timestep_fs", "2.0"), ("warmup_steps", "25000"), ("prod_steps", "100000"),
             ("dump_every", "5"), ("thermo_every", "5000"), ("run_id", "1"), ("seg", "1"))
# The dry-run deck reuses tdm.in's own variable lines, so it takes the same production values.
DRY_VARS = (("T", "313.15"), ("timestep_fs", "2.0"), ("dump_every", "5"), ("thermo_every", "5000"),
            ("run_id", "1"), ("seg", "1"))

NPT_STEPS = 250000
DRIFT_WINDOW_STEPS = 125000          # the last 250 ps of the NPT run at 2 fs
DRIFT_SPAN_PS = Decimal("100")
DRIFT_FRACTION = Decimal("0.01")
WARMUP_STEPS = 25000
PROD_STEPS = 100000
DRY_WARM_STEPS = 1000
DRY_TIMED_STEPS = 1000
R1_TOLERANCE = Decimal("0.05")
REF_DENSITY = Decimal("0.805")
DENSITY_BAND = Decimal("0.04")
CLAIM_A_LOW = Decimal("100")
CLAIM_A_HIGH = Decimal("625")
GATE_NS_DAY = Decimal("150")
PLAN_USD = Decimal("941")
PROXY_NS_DAY = Decimal("250")
CAP_USD = Decimal("1000")
CAP_THRESHOLD_NS_DAY = Decimal("235.3")
T_TARGET_K = Decimal("313.15")
T_TOLERANCE_K = Decimal("5")
E8_PATTERNS = ("Lost atoms", "SHAKE", "Bond atom missing", "ERROR")
REFUSAL_NAMES = ("centroid/stress/atom", "stress/atom", "heat/flux")
NET_CHARGE_LIMIT = Decimal("1e-3")
ATOMS_EXPECTED = 11250
L_DRY_SECONDS = 4 * 3600
EXPECTED_SAMPLE_ROWS_PROD_A = 20000

LABEL_BOX = "one box, 11,250 atoms"
LABEL_ENGINE = "LAMMPS 2024.08.29, conda-forge CUDA build, GPU package"
LABEL_R1 = "Performance line and wall-clock disagree"
LABEL_ANCHOR = "descriptive only; anchor failed"
LABEL_UNSTABLE = "descriptive only; unstable run"
LABEL_VISC = "viscosity-only protocol; the deck's heat flux does not run on the GPU pair style"
FLAG_TC = "the card's thermal-conductivity arm: unpriced on the GPU"
LABEL_DRIFT = "density still drifting"
CARD_GATE_FAIL_TEXT = "drop the extension tier and re-plan with 48 molecules at 3 replicas"
LABEL_INCOMPLETE = "incomplete run: descriptive only, no verdict"

# Listed edit 3 (EXEC_NOTE.md item 3b, gate addendum A6): the equilibration deck's load-balancing lines.
EDIT3_NAMES = ("comm_style", "balance", "tiled", "rcb")
EDIT3_DECK = "equilibrate_noballance.in"     # the file name exactly as the execution note spells it
EDIT3_DIFF = "equilibrate_noballance.diff"

# File names the committed decks write, given the -var values above (T 313.15, run_id 1, seg 1).
DENSITY_FILE = f"density_npt_T{T_STR}K_run1.dat"
EQUIL_LOG = f"log_equilibrate_T{T_STR}K_run1.out"
RESTART_FILE = f"equilibrated_T{T_STR}K.restart"
EQUIL_DATA = f"equilibrated_T{T_STR}K.data"
TDM_LOG = f"log_tdm_T{T_STR}K_run1_seg1.out"
STRESS_FILE = f"Stress_perstep_T{T_STR}K_run1_seg1.out"
HEATFLUX_FILE = f"HeatFlux_perstep_T{T_STR}K_run1_seg1.out"
VOLUME_FILE = f"volume_T{T_STR}K_run1.txt"

PROD_VARIANTS = ("prod_a", "prod_b", "prod_c")
VARIANT_WORDS = {
    "dryrun": "timed dry run (1,000 warm-up and 1,000 timed steps with tdm.in's sampling lines)",
    "equilibrate": ("equilibration (committed equilibrate.in; on the one allowed second attempt, its copy "
                    "with listed edit 3)"),
    "prod_a": "run a: committed tdm.in as written (pressure tensor and heat flux every 5 steps)",
    "prod_b": "run b: tdm.in with listed edit 1 (pressure tensor only)",
    "prod_c": "run c: tdm.in with listed edit 2 (no per-step sampling)",
}
STAGE_EXIT = {"dryrun": 10, "copy": 11, "equilibrate": 12, "prod_a": 13, "prod_b": 14, "prod_c": 15,
              "endpoints": 16, "extract": 17}
EXIT_INSTALL = 2
EXIT_GUARD = 3
EXIT_GATE = 4

# ---------------------------------------------------------------------------------------------
# Cost and time guard. These are build choices, not design numbers: the design fixes only the
# caps (REMOTE_TIMEOUT, BUDGET_LEFT_USD) and the trim order (run c first, then run b).
# ---------------------------------------------------------------------------------------------
STAGE_ORDER = ("install", "extract", "dryrun", "copy", "equilibrate", "prod_a", "prod_b", "prod_c", "endpoints")
EST_FIXED_S = {"install": 0.0, "extract": 5.0, "dryrun": 300.0, "copy": 10.0, "endpoints": 60.0}
EST_RATE_MARGIN = 1.25          # stage estimates use the slowest measured rate, times this
EST_LMP_OVERHEAD_S = 60.0       # engine start, GPU set-up and file output per LAMMPS stage
GUARD_MARGIN_S = 120.0          # kept free before REMOTE_TIMEOUT for the summary and RUN_DONE
BILLING_TAIL_S = 600.0          # box time billed outside the on-box run (boot, fetch, teardown)
FALLBACK_NS_PER_DAY = 100.0     # rate assumed before any rate is measured (lower edge of claim A)
EQUIL_STEPS_EST = 510000        # 500,000 MD steps plus at most 10,000 minimiser force evaluations
PROD_STEPS_EST = WARMUP_STEPS + PROD_STEPS
DEFAULT_REMOTE_TIMEOUT_S = 5400

STATE_NAME = "RUN_VALID.json"
STAGES_NAME = "stages.json"
LABELS_NAME = "labels.json"
SUMMARY_NAME = "m3_summary.json"
NOT_RECORDS = {STATE_NAME, STAGES_NAME, LABELS_NAME, SUMMARY_NAME}


# =============================================================================================
# Small tools
# =============================================================================================
class ParseError(ValueError):
    """An output could not be read as the format it should have."""


class Degenerate(ValueError):
    """An output was read but cannot carry a decision: empty, wrong run, not finite, and so on."""


class DeckError(ValueError):
    """The committed deck does not contain the lines a listed edit names."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path) -> str | None:
    p = Path(path)
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path) -> str | None:
    p = Path(path)
    try:
        return p.read_text(errors="replace")
    except (FileNotFoundError, IsADirectoryError, NotADirectoryError):
        return None


def write_json_atomic(path, obj) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, sort_keys=True))
    os.replace(tmp, path)


def clean(obj):
    """JSON-safe copy: Decimals become exact strings, non-finite floats become null."""
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if isinstance(obj, set):
        return [clean(v) for v in sorted(obj, key=str)]
    return obj


def dec(x) -> Decimal:
    try:
        return Decimal(str(x).strip())
    except (InvalidOperation, ValueError):
        raise ParseError(f"not a number: {x!r}")


def finite_positive(d: Decimal, what: str) -> Decimal:
    if not d.is_finite() or d <= 0:
        raise Degenerate(f"{what} is {d}, not a finite positive number")
    return d


def qround(d: Decimal, places: int) -> Decimal:
    return d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def round_sig(d: Decimal, sig: int) -> Decimal:
    if d == 0 or not d.is_finite():
        return d
    return d.quantize(Decimal(1).scaleb(d.adjusted() - (sig - 1)), rounding=ROUND_HALF_UP)


def sci4(d: Decimal) -> str:
    return f"{float(d):.4e}"


def unique(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def copy_if_exists(src, dst) -> bool:
    src, dst = Path(src), Path(dst)
    if src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        return True
    return False


def reset_dir(d) -> Path:
    d = Path(d)
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True, exist_ok=True)
    return d


# =============================================================================================
# The frozen record writer
# =============================================================================================
_PROV = None


def provenance():
    """frozen/provenance.py beside this file. Loaded without writing cache files next to it."""
    global _PROV
    if _PROV is None:
        cand = HERE / "frozen" / "provenance.py"
        if not cand.is_file():
            raise SystemExit(f"the frozen record writer is missing: {cand}")
        spec = importlib.util.spec_from_file_location("m3_frozen_provenance", cand)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _PROV = mod
    return _PROV


def describe(path, n_items=None) -> dict:
    return provenance().describe_input(path, n_items)


# =============================================================================================
# Where things live (the box layout from EXEC_NOTE.md; --root moves the whole tree for tests)
# =============================================================================================
class Paths:
    def __init__(self, root):
        root = Path(root).resolve()
        self.root = root
        self.data = root / "data"
        self.box = self.data / BOX_NAME
        self.decks_src = self.data / "MD-ML-thermophysical" / "MD" / "lammps"
        self.res = root / "results_m3"
        self.out = self.res / "out"
        self.system = self.res / "system"
        self.decks = self.res / "decks"
        self.runs = self.res / "runs"
        self.engine = root / "engine"
        self.lmp = self.engine / "bin" / "lmp"
        # The pre-launch record and its read_data log live on the workstation only; the launcher's
        # payload does not ship out/. They are read when present (a local endpoints pass).
        self.prelaunch = root / "out" / "prelaunch_build_mol00557.json"


# =============================================================================================
# Run validity, stage book-keeping, records and raw rows
# =============================================================================================
def read_state(P) -> dict:
    p = P.out / STATE_NAME
    if p.is_file():
        st = json.loads(p.read_text())
        return {"run_valid": bool(st.get("run_valid", True)), "voided_by": list(st.get("voided_by", [])),
                "labels": list(st.get("labels", [])), "voided_at_utc": st.get("voided_at_utc"),
                "created_utc": st.get("created_utc")}
    return {"run_valid": True, "voided_by": [], "labels": [], "voided_at_utc": None, "created_utc": None}


def init_state(P) -> None:
    P.out.mkdir(parents=True, exist_ok=True)
    if not (P.out / STATE_NAME).is_file():
        st = read_state(P)
        st["created_utc"] = utc_now()
        write_json_atomic(P.out / STATE_NAME, st)


def void_run(P, reason: str, label: str | None = None) -> dict:
    """run_valid=false for good. Every record and row written after this carries it."""
    st = read_state(P)
    st["run_valid"] = False
    if reason not in st["voided_by"]:
        st["voided_by"].append(reason)
    if label and label not in st["labels"]:
        st["labels"].append(label)
    st["voided_at_utc"] = st["voided_at_utc"] or utc_now()
    write_json_atomic(P.out / STATE_NAME, st)
    print(f"[void] run_valid=false: {reason}")
    return st


def add_label(P, label: str) -> None:
    st = read_state(P)
    if label not in st["labels"]:
        st["labels"].append(label)
        write_json_atomic(P.out / STATE_NAME, st)


def read_stages(P) -> dict:
    p = P.out / STAGES_NAME
    base = {"stages": {}, "trimmed": [], "prod_b_required": False, "dry_rate_steps_per_s": None,
            "restart_sha256": None}
    if p.is_file():
        base.update(json.loads(p.read_text()))
    return base


def write_stages(P, s: dict) -> None:
    s = dict(s)
    s["run_valid"] = read_state(P)["run_valid"]
    write_json_atomic(P.out / STAGES_NAME, clean(s))


def set_stage(P, name: str, **fields) -> dict:
    s = read_stages(P)
    s["stages"].setdefault(name, {}).update(clean(fields))
    write_stages(P, s)
    return s


def write_record(P, *, cell, inputs, metric, values, threshold, decision_rule, decision, notes="",
                 rows=None) -> Path:
    """One record through the frozen writer, then the validity fields at top level."""
    prov = provenance()
    st = read_state(P)
    full = {"tag": TAG}
    full.update(cell)
    path = P.out / (prov.cell_slug(full) + ".json")
    prov.write_result(path, cell=full, inputs=list(inputs), metric=metric, values=clean(values),
                      threshold=clean(threshold or {}), decision_rule=decision_rule, decision=decision,
                      notes=notes, rows=clean(rows) if rows is not None else None)
    rec = json.loads(path.read_text())
    rec["run_valid"] = st["run_valid"]
    rec["run_valid_voided_by"] = list(st["voided_by"])
    rec["run_labels"] = list(st["labels"])
    write_json_atomic(path, rec)
    return path


def load_record(P, cell) -> dict | None:
    full = {"tag": TAG}
    full.update(cell)
    p = P.out / (provenance().cell_slug(full) + ".json")
    return json.loads(p.read_text()) if p.is_file() else None


def append_rows(P, name: str, rows) -> None:
    st = read_state(P)
    P.out.mkdir(parents=True, exist_ok=True)
    with open(P.out / name, "a") as fh:
        for r in rows:
            r = clean(dict(r))
            r["run_valid"] = st["run_valid"]
            r["run_labels"] = list(st["labels"])
            r["written_utc"] = utc_now()
            fh.write(json.dumps(r, sort_keys=True) + "\n")


# =============================================================================================
# Parsers
# =============================================================================================
_PERF_RE = re.compile(r"^Performance:\s*(\S+?),?\s+ns/day")
_LOOP_RE = re.compile(r"^Loop time of\s+(\S+)\s+on\s+(\d+)\s+procs\s+for\s+(\d+)\s+steps\s+with\s+(\d+)\s+atoms")
_EQ_DONE_RE = re.compile(r"^Equilibration done: wrote (\S+), target_density=(\S+) g/cm\^3, "
                         r"final_density=(\S+) g/cm\^3")
_NPT_TARGET_RE = re.compile(r"^NPT average density target from final window:\s*(\S+)\s*g/cm\^3")


def parse_performance_line(line: str) -> Decimal:
    """'Performance: 123.456 ns/day, ...' -> Decimal('123.456')."""
    m = _PERF_RE.match(line.strip())
    if not m:
        raise ParseError(f"not a Performance line: {line!r}")
    return dec(m.group(1))


def parse_loop_line(line: str) -> dict:
    m = _LOOP_RE.match(line.strip())
    if not m:
        raise ParseError(f"not a Loop time line: {line!r}")
    return {"seconds": m.group(1), "procs": int(m.group(2)), "steps": int(m.group(3)), "atoms": int(m.group(4))}


def _isnum(tok: str) -> bool:
    try:
        float(tok)
        return True
    except ValueError:
        return False


def parse_lammps_log(text: str | None) -> dict:
    """Thermo blocks ("runs") with their rows, Loop line, Performance line and the lines that
    preceded each block (the echoed commands); plus ERROR and WARNING lines."""
    lines = (text or "").splitlines()
    runs, errors, warnings = [], [], []
    wall = None
    cur = None
    prev_end = -1
    for i, raw in enumerate(lines):
        s = raw.strip()
        if not s:
            continue
        if s.startswith("ERROR"):
            errors.append(s)
        elif s.startswith("WARNING"):
            warnings.append(s)
        if s.startswith("Total wall time:"):
            wall = s.split(":", 1)[1].strip()
            continue
        if s.startswith("Loop time of"):
            try:
                loop = parse_loop_line(s)
            except ParseError:
                loop = None
            if cur is not None:
                cur["loop"], cur["loop_line"], cur["end_line"] = loop, i, i
                runs.append(cur)
                cur = None
                prev_end = i
            continue
        if s.startswith("Performance:"):
            if cur is None and runs and runs[-1]["performance_line"] is None:
                runs[-1]["performance_line"] = s
                try:
                    runs[-1]["performance_ns_day"] = str(parse_performance_line(s))
                except ParseError:
                    runs[-1]["performance_ns_day"] = None
            continue
        toks = s.split()
        if toks[0] == "Step" and len(toks) >= 2 and not any(_isnum(t) for t in toks):
            if cur is not None:              # a block that never reached its Loop line
                cur["end_line"] = i - 1
                runs.append(cur)
                prev_end = i - 1
            cur = {"index": len(runs), "header": toks, "header_line": i, "rows": [], "row_lines": [],
                   "loop": None, "loop_line": None, "end_line": None, "performance_line": None,
                   "performance_ns_day": None,
                   "preceding": [ln.strip() for ln in lines[prev_end + 1:i] if ln.strip()]}
            continue
        if cur is not None and len(toks) == len(cur["header"]) and all(_isnum(t) for t in toks):
            cur["rows"].append(toks)
            cur["row_lines"].append(i)
    if cur is not None:
        cur["end_line"] = len(lines) - 1
        runs.append(cur)
    return {"lines": lines, "runs": runs, "errors": errors, "warnings": warnings, "total_wall_time": wall}


def error_lines(text: str | None) -> list:
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip().startswith("ERROR")]


def column(block: dict, name: str) -> list:
    if name not in block["header"]:
        raise ParseError(f"the thermo block has no {name} column (header {block['header']})")
    k = block["header"].index(name)
    return [dec(r[k]) for r in block["rows"]]


def block_summary(b: dict) -> dict:
    loop = b.get("loop") or {}
    return {"index": b["index"], "header": b["header"], "n_rows": len(b["rows"]),
            "first_step": b["rows"][0][0] if b["rows"] else None,
            "last_step": b["rows"][-1][0] if b["rows"] else None,
            "steps": loop.get("steps"), "loop_s": loop.get("seconds"), "atoms": loop.get("atoms"),
            "performance_ns_day": b.get("performance_ns_day"), "performance_line": b.get("performance_line"),
            "finished": b.get("loop") is not None}


def parse_density_file(text: str | None) -> list:
    """Rows of a LAMMPS fix ave/time file (scalar mode): '# ...' comments, then 'step value'."""
    rows = []
    for raw in (text or "").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        parts = s.split()
        if len(parts) != 2:
            raise ParseError(f"a density row must be a step and one value: {s!r}")
        try:
            step = int(parts[0])
        except ValueError:
            raise ParseError(f"a density row must start with an integer step: {s!r}")
        rows.append((step, parts[1]))
    return rows


def density_file_value(text: str | None) -> Decimal:
    """The deck writes exactly one value: the NPT mean over the last 250 ps."""
    if text is None:
        raise Degenerate("the density file is missing")
    rows = parse_density_file(text)
    if len(rows) != 1:
        raise Degenerate(f"the density file holds {len(rows)} data rows; the deck writes exactly one")
    return finite_positive(dec(rows[0][1]), "the NPT mean density")


def parse_metadata(text: str) -> dict:
    d = json.loads(text)
    need = ("n_molecules", "atoms_per_molecule", "net_charge_per_molecule", "density_g_cm3", "smiles")
    missing = [k for k in need if k not in d]
    if missing:
        raise ParseError(f"the builder metadata lacks {missing}")
    return d


def _section(lines, i):
    j = i + 1
    while j < len(lines) and not lines[j].strip():
        j += 1
    out = []
    while j < len(lines) and lines[j].strip():
        out.append(lines[j].strip())
        j += 1
    return out


def parse_lmp_help(text: str | None) -> dict:
    lines = (text or "").splitlines()
    version, gpu_present = None, None
    packages, accel = [], []
    for i, raw in enumerate(lines):
        s = raw.strip()
        m = re.search(r"Large-scale Atomic/Molecular Massively Parallel Simulator - (.+)$", s)
        if m and version is None:
            version = m.group(1).strip()
        if s.startswith("Compatible GPU present:"):
            gpu_present = s.split(":", 1)[1].strip()
        if s == "Installed packages:":
            for ln in _section(lines, i):
                packages.extend(ln.split())
        if s == "Accelerator configuration:":
            accel = _section(lines, i)
    return {"version": version, "packages": packages, "accelerator_configuration": accel,
            "compatible_gpu_present": gpu_present}


def parse_micromamba_list(text: str | None) -> dict:
    """Table output of `micromamba list`: name, version, build, channel per package row."""
    pk = {}
    for raw in (text or "").splitlines():
        s = raw.strip()
        if not s or s.startswith("List of packages") or s.split()[0] == "Name":
            continue
        if set(s) <= set("─━-=+| "):
            continue
        toks = s.split()
        if len(toks) < 3:
            continue
        pk[toks[0]] = {"name": toks[0], "version": toks[1], "build": toks[2],
                       "channel": toks[3] if len(toks) > 3 else None, "line": s}
    return pk


def parse_nvidia_smi(text: str | None) -> dict:
    t = text or ""
    d = re.search(r"Driver Version:\s*([0-9.]+)", t)
    c = re.search(r"CUDA Version:\s*([0-9.]+)", t)
    return {"driver_version": d.group(1) if d else None, "cuda_version": c.group(1) if c else None}


def parse_nvidia_query(text: str | None) -> dict:
    for raw in (text or "").splitlines():
        parts = [p.strip() for p in raw.split(",")]
        if len(parts) >= 2 and parts[0]:
            return {"gpu_name": parts[0], "driver_version": parts[1]}
    return {"gpu_name": None, "driver_version": None}


def parse_epoch(text: str | None) -> Decimal:
    """`date +%s.%N` output -> seconds since 1970, exact."""
    s = (text or "").strip()
    if not s:
        raise ParseError("empty time stamp")
    return finite_positive(dec(s.split()[0]), "the time stamp")


def epoch_span_seconds(start: Decimal, end: Decimal) -> Decimal:
    d = end - start
    if d < 0:
        raise Degenerate(f"the end stamp {end} is before the start stamp {start}")
    return d


def parse_kv(text: str | None) -> dict:
    out = {}
    for raw in (text or "").splitlines():
        if "=" in raw:
            k, v = raw.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def parse_units(text: str | None) -> str | None:
    m = re.search(r"^\s*units\s+(\S+)", text or "", re.M)
    return m.group(1) if m else None


def parse_pair_style(text: str | None) -> str | None:
    m = re.search(r"^\s*pair_style\s+(\S+)", text or "", re.M)
    return m.group(1) if m else None


def gpu_pair_style(init_text: str | None) -> str | None:
    ps = parse_pair_style(init_text)
    return f"{ps}/gpu" if ps else None


def read_head(path, n_lines: int = 60) -> str | None:
    p = Path(path)
    if not p.is_file():
        return None
    out = []
    with open(p, errors="replace") as fh:
        for _ in range(n_lines):
            ln = fh.readline()
            if not ln:
                break
            out.append(ln)
    return "".join(out)


def parse_data_header_atoms(head_text: str | None) -> int:
    for raw in (head_text or "").splitlines()[1:]:
        m = re.match(r"^\s*(\d+)\s+atoms\s*$", raw)
        if m:
            return int(m.group(1))
    raise ParseError("the data file header has no atom count")


def parse_read_data_atoms(text: str | None) -> int | None:
    lines = (text or "").splitlines()
    for i, raw in enumerate(lines):
        if raw.strip() == "reading atoms ...":
            for nxt in lines[i + 1:i + 4]:
                m = re.match(r"^\s*(\d+)\s+atoms\s*$", nxt)
                if m:
                    return int(m.group(1))
    return None


def parse_equilibration_done(text: str | None) -> dict | None:
    for raw in (text or "").splitlines():
        m = _EQ_DONE_RE.match(raw.strip())
        if m:
            return {"restart": m.group(1), "target_density": m.group(2), "final_density": m.group(3),
                    "line": raw.strip()}
    return None


def parse_npt_target(text: str | None) -> str | None:
    for raw in (text or "").splitlines():
        m = _NPT_TARGET_RE.match(raw.strip())
        if m:
            return m.group(1)
    return None


def device_lines(text: str | None) -> list:
    return [ln.strip() for ln in (text or "").splitlines()
            if re.match(r"^\s*Device\s+\d+\s*:", ln) or ln.strip().startswith("- Using acceleration for")]


def classify_refusal(errors: list, gpu_pair: str | None) -> str | None:
    """The first error line naming centroid/stress/atom, stress/atom, heat/flux or the GPU pair style."""
    names = list(REFUSAL_NAMES) + ([gpu_pair] if gpu_pair else [])
    for line in errors:
        low = line.lower()
        if any(n.lower() in low for n in names):
            return line
    return None


def run_status(res: dict, errors: list, gpu_pair: str | None, refusal_allowed: bool):
    """RUNS, REFUSED (a listed refusal), FAILED (any other error) or STOPPED (time guard)."""
    if res.get("timed_out"):
        return "STOPPED", "stopped by the time or cost guard's deadline during the run"
    if res.get("rc") != 0 or errors:
        line = classify_refusal(errors, gpu_pair) if refusal_allowed else None
        if line:
            return "REFUSED", line
        if errors:
            return "FAILED", errors[0]
        return "FAILED", f"exit code {res.get('rc')} with no ERROR line ({res.get('start_error') or 'no start error'})"
    return "RUNS", None


def head_tail(path, n: int = 5) -> dict:
    p = Path(path)
    if not p.is_file():
        return {"present": False, "data_rows": None, "lines": None, "head": [], "tail": []}
    head, tail = [], collections.deque(maxlen=n)
    rows = total = 0
    with open(p, errors="replace") as fh:
        for raw in fh:
            ln = raw.rstrip("\n")
            if total < n:
                head.append(ln)
            tail.append(ln)
            total += 1
            s = ln.strip()
            if s and not s.startswith("#"):
                rows += 1
    return {"present": True, "data_rows": rows, "lines": total, "head": head, "tail": list(tail)}


# =============================================================================================
# Decisions and arithmetic (each is a function of measured values only)
# =============================================================================================
def _absent(why: str) -> dict:
    return {"present": False, "value": None, "pass": None, "why_absent": why}


def _last_attempt(prelaunch: dict):
    keys = sorted((k for k in prelaunch if re.fullmatch(r"attempt_\d+", k)), key=lambda k: int(k.split("_")[1]))
    return (keys[-1], prelaunch[keys[-1]]) if keys else (None, None)


def e1_parts(meta: dict | None, data_atoms: int | None, prelaunch: dict | None, read0_text: str | None) -> dict:
    """The pre-launch build gate, part by part. A part whose input is absent is recorded as absent."""
    not_shipped = "lives in the workstation's pre-launch record, which the box payload does not carry"
    p = {}
    if meta is not None:
        q = dec(meta["net_charge_per_molecule"])
        p["net_charge_per_molecule"] = {"present": True, "value": str(q), "pass": abs(q) < NET_CHARGE_LIMIT,
                                        "rule": "|net charge per molecule| < 1e-3 e"}
        n = int(meta["n_molecules"]) * int(meta["atoms_per_molecule"])
        p["atoms_from_metadata"] = {"present": True, "value": n, "pass": n == ATOMS_EXPECTED,
                                    "rule": "n_molecules x atoms_per_molecule = 11,250"}
    else:
        p["net_charge_per_molecule"] = _absent("metadata.json is missing")
        p["atoms_from_metadata"] = _absent("metadata.json is missing")
    if data_atoms is not None:
        p["atoms_in_data_file_header"] = {"present": True, "value": data_atoms, "pass": data_atoms == ATOMS_EXPECTED,
                                          "rule": "11,250 atoms in the in.data header"}
    else:
        p["atoms_in_data_file_header"] = _absent("in.data is missing or has no atom count")
    if prelaunch is not None:
        name, att = _last_attempt(prelaunch)
        code = (att or {}).get("exit_code")
        p["builder_exit_code"] = {"present": code is not None, "value": code, "pass": code == 0 if code is not None else None,
                                  "attempt": name, "rule": "the builder run that wrote the box exited 0"}
    else:
        p["builder_exit_code"] = _absent(not_shipped)
    if read0_text is not None:
        errs = error_lines(read0_text)
        atoms = parse_read_data_atoms(read0_text)
        p["zero_step_read_data"] = {"present": True, "value": {"error_lines": errs, "atoms": atoms},
                                    "pass": (not errs) and atoms == ATOMS_EXPECTED,
                                    "rule": "zero-step read_data in CPU LAMMPS: no ERROR line and 11,250 atoms"}
    else:
        p["zero_step_read_data"] = _absent(not_shipped)
    return p


def e1_decide(parts: dict) -> str:
    present = {k: v for k, v in parts.items() if v["present"]}
    if any(v["pass"] is not True for v in present.values()):
        return "FAIL"
    if len(present) < len(parts):
        return "PASS_ON_PARTS_PRESENT"
    return "PASS"


def e2_decide(rho: Decimal) -> str:
    return "WITHIN_BAND" if abs(rho - REF_DENSITY) <= REF_DENSITY * DENSITY_BAND else "OUTSIDE_BAND"


def lsq_slope(xs: list, ys: list) -> Decimal:
    n = len(xs)
    if n < 2:
        raise Degenerate(f"a slope needs at least 2 points; got {n}")
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        raise Degenerate("all time points are equal")
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


def density_drift(npt_block: dict, mean: Decimal) -> dict:
    steps = column(npt_block, "Step")
    dens = column(npt_block, "Density")
    if not steps:
        raise Degenerate("the NPT thermo block has no rows")
    last = max(steps)
    sel = [(s, d) for s, d in zip(steps, dens) if s >= last - DRIFT_WINDOW_STEPS]
    xs = [s * TIMESTEP_FS / 1000 for s, _ in sel]          # ps
    ys = [d for _, d in sel]
    if any(not y.is_finite() for y in ys):
        raise Degenerate("a thermo density in the window is not finite")
    slope = lsq_slope(xs, ys)
    change = abs(slope) * DRIFT_SPAN_PS
    limit = DRIFT_FRACTION * mean
    return {"n_rows": len(sel), "first_step": str(sel[0][0]), "last_step": str(sel[-1][0]),
            "slope_g_cm3_per_ps": slope, "change_over_100_ps": change, "limit_1pct_of_mean": limit,
            "drifting": change > limit}


def e3_decide(ns: Decimal) -> str:
    if ns < CLAIM_A_LOW:
        return "REFUTED_BELOW"
    if ns > CLAIM_A_HIGH:
        return "REFUTED_ABOVE"
    return "HOLDS"


def e3b_decide(ns: Decimal) -> str:
    return "PASS" if ns >= GATE_NS_DAY else "FAIL"


def e3c_reprice(ns: Decimal) -> dict:
    cost = qround(PLAN_USD * PROXY_NS_DAY / ns, 2)
    return {"cost_usd": cost, "decision": "WITHIN_CAP" if cost <= CAP_USD else "ABOVE_CAP",
            "under_pricing_ratio_250_over_measured": qround(PROXY_NS_DAY / ns, 4),
            "measured_at_or_above_235_3": ns >= CAP_THRESHOLD_NS_DAY}


def ratio4(num: Decimal, den: Decimal) -> Decimal:
    return qround(num / den, 4)


def per_atom_step_rate(atoms: int, ns: Decimal, ts_fs: Decimal = TIMESTEP_FS) -> Decimal:
    """atoms x ns_per_day x 1e-9 / (timestep_fs x 1e-15) / 86,400, in atom-steps per second."""
    return Decimal(atoms) * ns * Decimal("1e-9") / (ts_fs * Decimal("1e-15")) / Decimal(86400)


def r1_agreement(perf_ns: Decimal, wall_s: Decimal, steps: int = DRY_TIMED_STEPS) -> dict:
    """Performance-line ns/day against steps x 2e-6 ns / (wall seconds / 86,400)."""
    wall_ns = Decimal(steps) * TIMESTEP_FS * Decimal("1e-6") / (wall_s / Decimal(86400))
    rel = abs(perf_ns - wall_ns) / wall_ns
    return {"wall_clock_ns_per_day": wall_ns, "relative_difference": rel, "agree": rel <= R1_TOLERANCE}


def segment_lines(lines: list, block: dict) -> list:
    """The output of one production run: its thermo header through its Loop line (or the end)."""
    end = block["loop_line"] if block.get("loop_line") is not None else len(lines) - 1
    return lines[block["header_line"]:end + 1]


def e8_check(block: dict | None, span: list, restart_ok) -> dict:
    reasons = []
    mean = None
    temp_ok = False
    if block is None:
        reasons.append("no production run in the log")
    else:
        try:
            temps = column(block, "Temp")
            if not temps:
                raise Degenerate("no thermo rows in the production run")
            mean = sum(temps) / len(temps)
            if not mean.is_finite():
                raise Degenerate("the mean temperature is not a finite number")
            temp_ok = abs(mean - T_TARGET_K) <= T_TOLERANCE_K
            if not temp_ok:
                reasons.append(f"mean temperature {mean} K is outside 313.15 +/- 5 K")
        except (ParseError, Degenerate) as e:
            reasons.append(str(e))
    hits = [ln.strip() for ln in span if any(pat in ln for pat in E8_PATTERNS)]
    if hits:
        reasons.append(f"{len(hits)} line(s) match 'Lost atoms', 'SHAKE', 'Bond atom missing' or 'ERROR'")
    if restart_ok is not True:
        reasons.append("the run did not start from the recorded equilibrated restart")
    return {"mean_temp_K": mean, "n_thermo_rows": len(block["rows"]) if block else 0, "temperature_ok": temp_ok,
            "matching_lines": hits, "restart_ok": restart_ok,
            "pass": bool(temp_ok and not hits and restart_ok is True), "reasons": reasons}


def production_block(parsed: dict, expected_steps: int, index: int = 1) -> dict:
    """The timed run: run number index+1 of the log, which must have taken expected_steps."""
    runs = parsed["runs"]
    if len(runs) <= index:
        raise Degenerate(f"the log holds {len(runs)} run(s); the timed run is run {index + 1}")
    b = runs[index]
    if b["loop"] is None:
        raise Degenerate(f"run {index + 1} has no 'Loop time' line: it did not finish")
    if b["loop"]["steps"] != expected_steps:
        raise Degenerate(f"run {index + 1} took {b['loop']['steps']} steps, not {expected_steps}: the wrong run")
    if b["performance_ns_day"] is None:
        raise Degenerate(f"no Performance line after run {index + 1}")
    finite_positive(dec(b["performance_ns_day"]), "the Performance-line ns/day")
    return b


def find_npt_block(parsed: dict) -> dict:
    hits = [b for b in parsed["runs"] if any(re.match(r"^fix\s+eq_npt\s", ln) for ln in b["preceding"])]
    if len(hits) != 1:
        raise Degenerate(f"found {len(hits)} thermo blocks after the deck's 'fix eq_npt' line; expected 1")
    b = hits[0]
    if b["loop"] is None or b["loop"]["steps"] != NPT_STEPS:
        raise Degenerate("the NPT run did not finish its 250,000 steps")
    return b


# =============================================================================================
# Deck copies: the two listed edits and the dry-run driver deck (originals are never edited)
# =============================================================================================
def strip_comment(s: str) -> str:
    quote = None
    for i, ch in enumerate(s):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#":
            return s[:i]
    return s


def deck_commands(text: str):
    """Physical lines, and commands (a command spans continuation lines ending in '&')."""
    lines = text.splitlines(keepends=True)
    cmds = []
    i = 0
    while i < len(lines):
        start = i
        while lines[i].rstrip().endswith("&") and i + 1 < len(lines):
            i += 1
        joined = " ".join(ln.rstrip().rstrip("&").strip() for ln in lines[start:i + 1])
        code = strip_comment(joined)
        cmds.append({"start": start, "end": i, "text": joined, "code": code, "tokens": code.split()})
        i += 1
    return lines, cmds


def _refers_to(code: str, name: str) -> bool:
    e = re.escape(name)
    pats = [rf"\bc_{e}\b", rf"\bv_{e}\b", rf"\$\{{{e}\}}"]
    if len(name) == 1:
        pats.append(rf"\${e}(?![A-Za-z0-9_])")
    return any(re.search(p, code) for p in pats) or name in code.split()


def _apply_deletions(lines, cmds, deleted: set):
    drop = set()
    for k in deleted:
        drop.update(range(cmds[k]["start"], cmds[k]["end"] + 1))
    kept = "".join(ln for j, ln in enumerate(lines) if j not in drop)
    gone = [cmds[k]["text"] for k in sorted(deleted)]
    return kept, gone


def edit1_pressure_only(text: str):
    """Listed edit 1: delete the lines from 'compute myKE' through 'compute redJkZ', the three Jtot
    variables, and 'fix flux_raw' (with its continuation line)."""
    lines, cmds = deck_commands(text)
    def find(t0, t1):
        for k, c in enumerate(cmds):
            if c["tokens"][:2] == [t0, t1]:
                return k
        raise DeckError(f"the committed tdm.in has no '{t0} {t1}' line")
    i0, i1 = find("compute", "myKE"), find("compute", "redJkZ")
    if i1 < i0:
        raise DeckError("'compute redJkZ' comes before 'compute myKE'")
    span_first, span_last = cmds[i0]["start"], cmds[i1]["end"]
    deleted = {k for k, c in enumerate(cmds) if c["start"] >= span_first and c["end"] <= span_last}
    for t in (["variable", "Jtot_x"], ["variable", "Jtot_y"], ["variable", "Jtot_z"], ["fix", "flux_raw"]):
        deleted.add(find(*t))
    return _apply_deletions(lines, cmds, deleted)


def edit2_no_sampling(text: str):
    """Listed edit 2: delete both fix ave/time commands, then every compute and variable line that
    exists only for them (referenced only from deleted lines). Thermostat, restarts, thermo stay."""
    lines, cmds = deck_commands(text)
    deleted = {k for k, c in enumerate(cmds)
               if len(c["tokens"]) >= 4 and c["tokens"][0] == "fix" and c["tokens"][3] == "ave/time"}
    if len(deleted) != 2:
        raise DeckError(f"the committed tdm.in has {len(deleted)} fix ave/time commands, not 2")
    changed = True
    while changed:
        changed = False
        for k, c in enumerate(cmds):
            if k in deleted or len(c["tokens"]) < 2 or c["tokens"][0] not in ("compute", "variable"):
                continue
            refs = [j for j, d in enumerate(cmds) if j != k and _refers_to(d["code"], c["tokens"][1])]
            if refs and all(j in deleted for j in refs):
                deleted.add(k)
                changed = True
    return _apply_deletions(lines, cmds, deleted)


def edit3_no_balance(text: str):
    """Listed edit 3: delete exactly the committed equilibrate.in's 'comm_style tiled', 'balance ... rcb'
    and 'fix load_balance ... rcb' lines. Every other line, comments included, stays as it is."""
    lines, cmds = deck_commands(text)
    wanted = (("comm_style tiled", lambda t: t[:2] == ["comm_style", "tiled"]),
              ("balance ... rcb", lambda t: t[:1] == ["balance"] and "rcb" in t),
              ("fix load_balance ... rcb", lambda t: t[:2] == ["fix", "load_balance"] and "rcb" in t))
    deleted = set()
    for label, pred in wanted:
        hits = [k for k, c in enumerate(cmds) if c["tokens"] and pred(c["tokens"])]
        if len(hits) != 1:
            raise DeckError(f"the committed equilibrate.in has {len(hits)} '{label}' lines, not exactly 1")
        deleted.add(hits[0])
    return _apply_deletions(lines, cmds, deleted)


def names_balance_lines(line: str | None) -> bool:
    """True if an error line names comm_style, balance, tiled or rcb (any letter case)."""
    low = (line or "").lower()
    return any(n in low for n in EDIT3_NAMES)


def build_dryrun_deck(tdm_text: str, tdm_sha: str) -> str:
    """The timed dry-run driver deck, built from tdm.in's own lines (copied verbatim)."""
    lines, cmds = deck_commands(tdm_text)
    verb = lambda c: "".join(lines[c["start"]:c["end"] + 1])
    first = lambda pred: next((c for c in cmds if c["tokens"] and pred(c["tokens"])), None)
    log_cmd = first(lambda t: t[0] == "log")
    if log_cmd is None:
        raise DeckError("the committed tdm.in has no log line")
    top_vars = [c for c in cmds if c["end"] < log_cmd["start"] and c["tokens"] and c["tokens"][0] == "variable"]
    shake = first(lambda t: t[:2] == ["fix", "constrain_h"])
    velocity = first(lambda t: t[0] == "velocity")
    thermo = first(lambda t: t[0] == "thermo")
    thermo_style = first(lambda t: t[0] == "thermo_style")
    nvt = first(lambda t: t[:2] == ["fix", "prod"])
    if None in (shake, velocity, thermo, thermo_style, nvt):
        raise DeckError("the committed tdm.in lacks a shake, velocity, thermo, thermo_style or 'fix prod' line")
    sampling = [c for c in cmds if c["start"] > log_cmd["end"] and c["tokens"] and c["tokens"][0] in ("compute", "variable")]
    avetime = [c for c in cmds if len(c["tokens"]) >= 4 and c["tokens"][0] == "fix" and c["tokens"][3] == "ave/time"]
    out = [
        "# Timed dry run, written by run_m3.py (tag m3). Not a committed deck.\n",
        f"# Built from the committed tdm.in (sha256 {tdm_sha}); every line marked 'verbatim' is copied from it.\n",
        "# 1,000 warm-up steps, then 1,000 timed steps bracketed by date stamps, under fix nvt,\n",
        "# with tdm.in's computes, variables and fix ave/time lines active throughout.\n",
        "# --- verbatim: tdm.in's variable lines\n",
    ]
    out += [verb(c) for c in top_vars]
    out += ["\n",
            "include         ${system_dir}/in.init\n",
            "read_data       ${system_dir}/in.data\n",
            "include         ${system_dir}/in.settings\n",
            "timestep        2.0\n",
            "# --- verbatim: SHAKE, velocities, thermo\n",
            verb(shake), verb(velocity), verb(thermo), verb(thermo_style),
            "# --- verbatim: tdm.in's computes and variables\n"]
    out += [verb(c) for c in sampling]
    out += ["# --- verbatim: tdm.in's thermostat and fix ave/time lines\n", verb(nvt)]
    out += [verb(c) for c in avetime]
    out += ["\n",
            f"run             {DRY_WARM_STEPS}\n",
            "shell           date +%s.%N > ${dump_dir}/dryrun_t0.epoch\n",
            f"run             {DRY_TIMED_STEPS} pre no\n",
            "shell           date +%s.%N > ${dump_dir}/dryrun_t1.epoch\n"]
    return "".join(out)


def unified_diff(a: str, b: str, a_name: str, b_name: str) -> str:
    return "".join(difflib.unified_diff(a.splitlines(keepends=True), b.splitlines(keepends=True),
                                        fromfile=a_name, tofile=b_name))


def build_edit3_deck(P) -> dict:
    """Write the listed edit 3 copy of equilibrate.in and its diff under results_m3/decks/ (and out/decks/)."""
    src = P.decks_src / "equilibrate.in"
    text = src.read_text()
    new_text, gone = edit3_no_balance(text)
    diff = unified_diff(text, new_text, "equilibrate.in", EDIT3_DECK)
    P.decks.mkdir(parents=True, exist_ok=True)
    (P.decks / EDIT3_DECK).write_text(new_text)
    (P.decks / EDIT3_DIFF).write_text(diff)
    for nm in (EDIT3_DECK, EDIT3_DIFF):
        copy_if_exists(P.decks / nm, P.out / "decks" / nm)
    return {"equilibrate_in": str(src), "equilibrate_in_sha256": sha256_file(src),
            "edited_copy": str(P.decks / EDIT3_DECK), "edited_copy_sha256": sha256_file(P.decks / EDIT3_DECK),
            "deleted_commands": gone, "diff": diff}


def build_decks(P) -> dict:
    """Write the dry-run deck and the two edited copies under results_m3/decks/, with diffs; copy
    them into results_m3/out/decks/ so they come back with the results."""
    tdm = P.decks_src / "tdm.in"
    text = tdm.read_text()
    tdm_sha = sha256_file(tdm)
    P.decks.mkdir(parents=True, exist_ok=True)
    b_text, b_gone = edit1_pressure_only(text)
    c_text, c_gone = edit2_no_sampling(text)
    d_text = build_dryrun_deck(text, tdm_sha)
    files = {"tdm_prod_b.in": b_text, "tdm_prod_c.in": c_text, "dryrun.in": d_text,
             "tdm_prod_b.diff": unified_diff(text, b_text, "tdm.in", "tdm_prod_b.in"),
             "tdm_prod_c.diff": unified_diff(text, c_text, "tdm.in", "tdm_prod_c.in")}
    for name, body in files.items():
        (P.decks / name).write_text(body)
        copy_if_exists(P.decks / name, P.out / "decks" / name)
    return {"tdm_in": str(tdm), "tdm_in_sha256": tdm_sha,
            "equilibrate_in_sha256": sha256_file(P.decks_src / "equilibrate.in"),
            "prod_b_deck_sha256": sha256_file(P.decks / "tdm_prod_b.in"),
            "prod_c_deck_sha256": sha256_file(P.decks / "tdm_prod_c.in"),
            "dryrun_deck_sha256": sha256_file(P.decks / "dryrun.in"),
            "prod_b_deleted_commands": b_gone, "prod_c_deleted_commands": c_gone,
            "prod_b_diff": files["tdm_prod_b.diff"], "prod_c_diff": files["tdm_prod_c.diff"]}


# =============================================================================================
# Cost and time guard
# =============================================================================================
class Clock:
    """Seconds since boot, and seconds since this on-box run began. onbox_m3.sh exports its own
    process id as M3_WINDOW_PID; that process was started by the launcher's `timeout`, so its
    start time is the start of the REMOTE_TIMEOUT window."""

    def uptime(self) -> float:
        return float(Path("/proc/uptime").read_text().split()[0])

    def window_elapsed(self) -> float:
        pid = os.environ.get("M3_WINDOW_PID", "").strip()
        if pid.isdigit():
            try:
                stat = Path(f"/proc/{pid}/stat").read_text()
                fields = stat[stat.rindex(")") + 2:].split()
                return self.uptime() - int(fields[19]) / os.sysconf("SC_CLK_TCK")
            except (OSError, ValueError, IndexError):
                pass
        return 0.0


CLOCK = Clock()


def steps_per_s_from_ns_day(ns: float) -> float:
    return ns * 1e6 / float(TIMESTEP_FS) / 86400.0


def stage_estimates(stages: dict) -> dict:
    r = stages.get("dry_rate_steps_per_s") or steps_per_s_from_ns_day(FALLBACK_NS_PER_DAY)
    est = dict(EST_FIXED_S)
    est["equilibrate"] = EST_RATE_MARGIN * EQUIL_STEPS_EST / r + EST_LMP_OVERHEAD_S
    pa = EST_RATE_MARGIN * PROD_STEPS_EST / r + EST_LMP_OVERHEAD_S
    S = stages.get("stages", {})
    def measured(v):
        x = S.get(v, {})
        return float(x["wall_s"]) if x.get("status") == "RUNS" and x.get("wall_s") else None
    wa, wb = measured("prod_a"), measured("prod_b")
    est["prod_a"] = pa
    est["prod_b"] = EST_RATE_MARGIN * wa if wa else pa
    est["prod_c"] = EST_RATE_MARGIN * (wb or wa) if (wb or wa) else pa
    return est


def guard_decide(stage: str, stages: dict, *, elapsed_s: float, uptime_s: float, timeout_s: float,
                 price, budget) -> dict:
    """go, trim (an optional run is cut) or stop. Trims run c first, then run b."""
    out = {"kind": "guard", "stage": stage, "elapsed_window_s": round(elapsed_s, 1), "uptime_s": round(uptime_s, 1),
           "timeout_s": timeout_s, "price_usd_per_hour": price, "budget_left_usd": budget, "trims": [],
           "allowed_seconds": 0}
    if price is None or budget is None:
        out.update(decision="stop", reason="PRICE_USD_PER_HOUR or BUDGET_LEFT_USD is missing or not a positive number")
        return out
    S = stages.get("stages", {})
    trimmed = set(stages.get("trimmed", []))
    if stage in trimmed:
        out.update(decision="trim", reason=f"{stage} was already cut by the guard")
        return out
    est = stage_estimates(stages)
    out["estimates_s"] = {k: round(v, 1) for k, v in est.items()}
    done = {k for k, v in S.items() if v.get("status")}
    if S.get("dryrun", {}).get("status") == "REFUSED":
        done.add("prod_a")
    i = STAGE_ORDER.index(stage)
    plan = [s for s in STAGE_ORDER[i:] if s == stage or (s not in done and s not in trimmed)]
    optional = {"prod_c"} if stages.get("prod_b_required") else {"prod_b", "prod_c"}
    remaining = timeout_s - elapsed_s
    budget_s = float(budget) / float(price) * 3600.0 - uptime_s - BILLING_TAIL_S
    avail = min(remaining, budget_s)
    out["seconds_left_in_window"] = round(remaining, 1)
    out["seconds_left_before_budget"] = round(budget_s, 1)
    need = lambda p: sum(est[s] for s in p) + GUARD_MARGIN_S
    while need(plan) > avail:
        cand = next((c for c in ("prod_c", "prod_b") if c in plan and c in optional), None)
        if cand is None:
            out.update(decision="stop", reason=(f"the {stage} stage and the stages that must follow need about "
                                                f"{need(plan):.0f} s; {avail:.0f} s are left before the time or "
                                                f"budget limit"))
            return out
        plan.remove(cand)
        out["trims"].append(cand)
    if stage not in plan:
        out.update(decision="trim", reason=f"{stage} cut so that the required stages fit")
        return out
    later_required = [s for s in plan[plan.index(stage) + 1:] if s not in optional]
    allowed = avail - sum(est[s] for s in later_required) - GUARD_MARGIN_S
    if allowed <= 0:
        out.update(decision="stop", reason=f"no time is left for the {stage} stage")
        return out
    out.update(decision="go", allowed_seconds=int(allowed), reason="fits")
    return out


def parse_positive(raw) -> Decimal | None:
    try:
        d = Decimal(str(raw).strip())
    except (InvalidOperation, ValueError):
        return None
    return d if d.is_finite() and d > 0 else None


def run_guard(P, stage: str) -> dict:
    init_state(P)
    stages = read_stages(P)
    price = parse_positive(os.environ.get("PRICE_USD_PER_HOUR", ""))
    budget = parse_positive(os.environ.get("BUDGET_LEFT_USD", ""))
    tmo = parse_positive(os.environ.get("REMOTE_TIMEOUT", "")) or Decimal(DEFAULT_REMOTE_TIMEOUT_S)
    g = guard_decide(stage, stages, elapsed_s=CLOCK.window_elapsed(), uptime_s=CLOCK.uptime(),
                     timeout_s=float(tmo), price=price, budget=budget)
    if g["trims"]:
        s = read_stages(P)
        s["trimmed"] = sorted(set(s.get("trimmed", [])) | set(g["trims"]))
        write_stages(P, s)
        for v in g["trims"]:
            add_label(P, f"{VARIANT_WORDS[v]}: cut by the time or cost guard ({v})")
    append_rows(P, "guard_rows.jsonl", [g])
    print(f"[guard] {stage}: {g['decision']} allowed_seconds={g['allowed_seconds']} ({g.get('reason', '')})")
    return g


def guard_stop(P, stage: str, g: dict) -> int:
    void_run(P, f"stopped by the cost or time guard before the {stage} stage: {g.get('reason')}")
    set_stage(P, stage, status="STOPPED", reason=g.get("reason"))
    return EXIT_GUARD


# =============================================================================================
# Running LAMMPS: `lmp -sf gpu -pk gpu 1 -in <deck> -var ... -log <log>` from the box directory
# =============================================================================================
def lammps_cmd(lmp, deck, var_pairs, cli_log) -> list:
    cmd = [str(lmp), "-sf", "gpu", "-pk", "gpu", "1", "-in", str(deck)]
    for k, v in var_pairs:
        cmd += ["-var", k, str(v)]
    return cmd + ["-log", str(cli_log)]


def run_lammps(lmp, deck, var_pairs, cli_log, screen, cwd, timeout_s) -> dict:
    cmd = lammps_cmd(lmp, deck, var_pairs, cli_log)
    res = {"cmd": cmd, "rc": None, "timed_out": False, "start_error": None}
    t0 = time.time()
    with open(screen, "w") as fh:
        try:
            p = subprocess.run(cmd, cwd=str(cwd), stdin=subprocess.DEVNULL, stdout=fh, stderr=subprocess.STDOUT,
                               timeout=timeout_s)
            res["rc"] = p.returncode
        except subprocess.TimeoutExpired:
            res["timed_out"] = True
        except OSError as e:
            res["rc"] = 127
            res["start_error"] = repr(e)
    t1 = time.time()
    res.update(start_epoch=f"{t0:.6f}", end_epoch=f"{t1:.6f}", wall_s=round(t1 - t0, 3))
    return res


LAMMPS_RUNNER = run_lammps    # the selftest swaps in a planted engine; nothing else does


def base_run_values(variant, res, deck, var_pairs, cwd, status, line, errors, parsed) -> dict:
    return {"variant": variant, "what": VARIANT_WORDS[variant], "deck": str(deck), "deck_sha256": sha256_file(deck),
            "vars": dict(var_pairs), "command": res.get("cmd"), "cwd": str(cwd), "status": status,
            "status_line": line, "exit_code": res.get("rc"), "timed_out": res.get("timed_out"),
            "start_error": res.get("start_error"), "start_epoch": res.get("start_epoch"),
            "end_epoch": res.get("end_epoch"), "stage_wall_s": res.get("wall_s"), "error_lines": errors,
            "warning_lines": parsed["warnings"][:50], "blocks": [block_summary(b) for b in parsed["runs"]],
            "total_wall_time_line": parsed["total_wall_time"], "degenerate": [], "attempt": 1}


def thermo_rows(variant: str, parsed: dict, log_name: str, attempt: int = 1) -> list:
    keys = {"Step": "step", "Temp": "temp", "Press": "press", "Density": "density", "Volume": "vol", "TotEng": "etotal"}
    out = []
    for b in parsed["runs"]:
        for toks, li in zip(b["rows"], b["row_lines"]):
            row = {"kind": "thermo", "variant": variant, "log": log_name, "block": b["index"], "line_no": li + 1,
                   "raw": parsed["lines"][li], "attempt": attempt}
            for h, t in zip(b["header"], toks):
                if h in keys:
                    row[keys[h]] = t
            out.append(row)
    return out


def run_row(values: dict) -> dict:
    keep = ("variant", "attempt", "deck", "deck_sha256", "vars", "status", "status_line", "exit_code", "stage_wall_s",
            "performance_ns_day", "performance_line", "loop_s", "atoms", "mean_temp_K", "final_density", "blocks")
    row = {k: values.get(k) for k in keep}
    row["kind"] = "run"
    row["steps"] = [b.get("steps") for b in values.get("blocks", [])]
    return row


def load_labels(P) -> dict:
    p = P.out / LABELS_NAME
    return json.loads(p.read_text()) if p.is_file() else {}


def throughput_labels(P, run_vals: dict, variant_read: str) -> dict:
    lab = dict(load_labels(P))
    lab["variant_read"] = variant_read
    lab["timestep_fs"] = str(TIMESTEP_FS)
    lab["atom_count"] = run_vals.get("atoms") or lab.get("atom_count")
    lab["per_atom_step_rate_atom_steps_per_s"] = run_vals.get("per_atom_step_rate")
    st = read_state(P)
    lab["run_labels_at_write"] = list(st["labels"])
    return lab


# =============================================================================================
# Stage: extract (lmp -h and GPU check, labels, decks, pre-launch gate)
# =============================================================================================
def write_env_txt(P) -> None:
    keys = ("INSTANCE_TYPE", "LAMBDA_INSTANCE_ID", "GIT_COMMIT", "PRICE_USD_PER_HOUR", "BUDGET_LEFT_USD",
            "REMOTE_TIMEOUT", "CONDA_OVERRIDE_CUDA", "MAMBA_ROOT_PREFIX", "M3_WINDOW_PID")
    lines = [f"written_utc: {utc_now()}", f"host: {socket.gethostname()}", f"python: {sys.version.split()[0]}",
             f"platform: {platform.platform()}", f"run_m3.py sha256: {sha256_file(Path(__file__))}"]
    lines += [f"{k}: {os.environ.get(k, '')}" for k in keys]
    P.out.mkdir(parents=True, exist_ok=True)
    (P.out / "env.txt").write_text("\n".join(lines) + "\n")


def cmd_extract(P) -> int:
    init_state(P)
    g = run_guard(P, "extract")
    if g["decision"] != "go":
        return guard_stop(P, "extract", g)
    write_env_txt(P)
    inst = parse_kv(read_text(P.out / "install_record.txt"))
    try:
        install_wall = epoch_span_seconds(parse_epoch(inst.get("start_epoch")), parse_epoch(inst.get("end_epoch")))
    except (ParseError, Degenerate) as e:
        install_wall = None
        inst["wall_clock_not_read"] = str(e)
    mm = parse_micromamba_list(read_text(P.out / "micromamba_list.txt"))
    helptext = read_text(P.out / "lmp_help.txt")
    hp = parse_lmp_help(helptext)
    nv = parse_nvidia_smi(read_text(P.out / "nvidia_smi.txt"))
    nq = parse_nvidia_query(read_text(P.out / "nvidia_smi_query.txt"))
    init_text = read_text(P.box / "in.init")
    try:
        data_atoms = parse_data_header_atoms(read_head(P.box / "in.data"))
    except ParseError:
        data_atoms = None
    lam = mm.get("lammps")
    cudart = mm.get("cuda-cudart")
    cudaver = mm.get("cuda-version")
    labels = {
        "instance_type": os.environ.get("INSTANCE_TYPE") or None,
        "gpu_name": nq["gpu_name"], "gpu_driver": nq["driver_version"] or nv["driver_version"],
        "cuda_version_reported_by_driver": nv["cuda_version"],
        "cuda_runtime_version": cudart["version"] if cudart else (cudaver["version"] if cudaver else None),
        "cuda_runtime_source": ("micromamba list: cuda-cudart" if cudart else
                                "micromamba list: cuda-version (cuda-cudart not listed)" if cudaver else
                                "neither cuda-cudart nor cuda-version is listed"),
        "lammps_build": lam["line"] if lam else None,
        "lammps_build_string": lam["build"] if lam else None,
        "lmp_help_version": hp["version"], "lmp_help_packages": hp["packages"],
        "lmp_help_accelerator_configuration": hp["accelerator_configuration"],
        "lmp_help_compatible_gpu_present": hp["compatible_gpu_present"],
        "timestep_fs": str(TIMESTEP_FS), "atom_count": data_atoms,
        "install_wall_clock_s": install_wall, "install_spec_used": inst.get("spec_used"),
        "price_usd_per_hour": os.environ.get("PRICE_USD_PER_HOUR") or None,
        "labels": [LABEL_BOX, LABEL_ENGINE],
        "units_in_in_init": parse_units(init_text),
    }
    write_json_atomic(P.out / LABELS_NAME, clean(labels))
    gpu_listed = "GPU" in hp["packages"]
    if not gpu_listed:
        void_run(P, "the GPU package is not listed by lmp -h")
    write_record(P, cell={"control": "gpu_package"},
                 inputs=[describe(P.out / "lmp_help.txt", len(hp["packages"])),
                         describe(P.out / "micromamba_list.txt", len(mm)), describe(P.out / "install_record.txt")],
                 metric="GPU package listed by lmp -h; installed LAMMPS build", values={**labels, "install_record": inst},
                 threshold={"package": "GPU"},
                 decision_rule=("LISTED if 'GPU' appears under 'Installed packages' in lmp -h; NOT_LISTED otherwise, "
                                "which voids the run and stops it with code 2."),
                 decision="LISTED" if gpu_listed else "NOT_LISTED")
    if not gpu_listed:
        set_stage(P, "extract", status="FAILED", reason="GPU package not listed")
        return EXIT_INSTALL
    if lam is None:
        void_run(P, "micromamba list shows no lammps package")
        set_stage(P, "extract", status="FAILED", reason="no lammps package listed")
        return EXIT_INSTALL
    deck_info = build_decks(P)
    write_record(P, cell={"control": "deck_edits"},
                 inputs=[describe(P.decks_src / "tdm.in"), describe(P.decks / "tdm_prod_b.in"),
                         describe(P.decks / "tdm_prod_c.in"), describe(P.decks / "dryrun.in")],
                 metric="edited deck copies and the dry-run deck, with sha256 and unified diffs",
                 values=deck_info, threshold={},
                 decision_rule=("BUILT when listed edit 1 (run b) and listed edit 2 (run c) apply to the committed "
                                "tdm.in and the dry-run deck is built from its lines; the originals are not edited."),
                 decision="BUILT")
    # The pre-launch build gate, re-checked on whatever of its inputs is present here.
    meta_text = read_text(P.box / "metadata.json")
    meta = parse_metadata(meta_text) if meta_text is not None else None
    pre = json.loads(P.prelaunch.read_text()) if P.prelaunch.is_file() else None
    read0_path = (P.root / pre["read0"]["log"]) if pre and isinstance(pre.get("read0"), dict) and pre["read0"].get("log") else None
    read0_text = read_text(read0_path) if read0_path else None
    parts = e1_parts(meta, data_atoms, pre, read0_text)
    d1 = e1_decide(parts)
    if d1 == "FAIL":
        void_run(P, "the pre-launch build gate failed")
    write_record(P, cell={"endpoint": "E1"},
                 inputs=[describe(P.box / "metadata.json"), describe(P.box / "in.data"), describe(P.prelaunch)]
                 + ([describe(read0_path)] if read0_path else []),
                 metric=("pre-launch build: builder exit code at 0.3 g/cm3; |net_charge_per_molecule|; zero-step "
                         "read_data in CPU LAMMPS; atom count"),
                 values={"parts": parts, "pre_launch_record": pre}, threshold={
                     "net_charge_abs_below": "1e-3", "atoms": ATOMS_EXPECTED, "builder_exit_code": 0},
                 decision_rule=("FAIL if any part present fails (builder exit 0; |net charge| < 1e-3 e; zero-step "
                                "read_data without an ERROR line and with 11,250 atoms; 11,250 atoms in metadata and "
                                "in the data file header). PASS if every part is present and passes. "
                                "PASS_ON_PARTS_PRESENT if the parts present pass and the rest live only in the "
                                "workstation's pre-launch record. FAIL voids the run and stops it with code 4."),
                 decision=d1)
    if d1 == "FAIL":
        set_stage(P, "extract", status="FAILED", reason="pre-launch build gate failed")
        return EXIT_GATE
    set_stage(P, "extract", status="DONE")
    return 0


# =============================================================================================
# Stage: generate
# =============================================================================================
def stage_dryrun(P) -> int:
    g = run_guard(P, "dryrun")
    if g["decision"] != "go":
        return guard_stop(P, "dryrun", g)
    deck = P.decks / "dryrun.in"
    if not deck.is_file():
        build_decks(P)
    dump = reset_dir(P.runs / "dryrun")
    var_pairs = list(DRY_VARS) + [("system_dir", str(P.box)), ("dump_dir", str(dump))]
    res = LAMMPS_RUNNER(P.lmp, deck, var_pairs, P.out / "dryrun.lammps.log", P.out / "dryrun.screen.txt", P.box,
                        g["allowed_seconds"])
    return ingest_dryrun(P, res, deck, var_pairs)


def ingest_dryrun(P, res, deck, var_pairs) -> int:
    dump = Path(dict(var_pairs)["dump_dir"])
    log_text = read_text(P.out / "dryrun.lammps.log") or ""
    screen_text = read_text(P.out / "dryrun.screen.txt") or ""
    parsed = parse_lammps_log(log_text)
    errors = unique(error_lines(screen_text) + parsed["errors"])
    init_text = read_text(P.box / "in.init")
    units = parse_units(init_text)
    status, line = run_status(res, errors, gpu_pair_style(init_text), refusal_allowed=True)
    for nm in ("dryrun_t0.epoch", "dryrun_t1.epoch"):
        copy_if_exists(dump / nm, P.out / nm)
    v = base_run_values("dryrun", res, deck, var_pairs, P.box, status, line, errors, parsed)
    v["device_lines"] = device_lines(screen_text)
    v["units_in_in_init"] = units
    v["units_real_confirmed"] = units == "real"
    v["read_data_atoms"] = parse_read_data_atoms(log_text)
    timing = {"read": False}
    rate = None
    if status == "RUNS":
        try:
            b = production_block(parsed, DRY_TIMED_STEPS, index=1)
            perf = dec(b["performance_ns_day"])
            loop_s = finite_positive(dec(b["loop"]["seconds"]), "the timed run's loop time")
            t0 = parse_epoch(read_text(dump / "dryrun_t0.epoch"))
            t1 = parse_epoch(read_text(dump / "dryrun_t1.epoch"))
            wall = finite_positive(epoch_span_seconds(t0, t1), "the timed run's wall-clock")
            timing = {"read": True, "performance_ns_day": perf, "performance_line": b["performance_line"],
                      "loop_s": loop_s, "steps": b["loop"]["steps"], "atoms": b["loop"]["atoms"],
                      "start_epoch": str(t0), "end_epoch": str(t1), "wall_s": wall, **r1_agreement(perf, wall)}
            rate = Decimal(DRY_TIMED_STEPS) / loop_s
            v.update(performance_ns_day=perf, performance_line=b["performance_line"], loop_s=loop_s,
                     atoms=b["loop"]["atoms"], per_atom_step_rate=sci4(per_atom_step_rate(b["loop"]["atoms"], perf)))
            temps = column(b, "Temp")
            v["mean_temp_K"] = sum(temps) / len(temps) if temps else None
        except (ParseError, Degenerate, InvalidOperation) as e:
            v["degenerate"].append(str(e))
    v["timing"] = timing
    if status == "STOPPED":
        void_run(P, "the time or cost deadline stopped the dry run")
    elif status == "FAILED":
        void_run(P, f"the dry run stopped with a LAMMPS error: {line}")
    if timing.get("read") and not timing["agree"]:
        add_label(P, LABEL_R1)
    s = read_stages(P)
    s["stages"]["dryrun"] = clean({"status": status, "line": line, "wall_s": res.get("wall_s"),
                                   "refusal_line": line if status == "REFUSED" else None})
    if rate is not None:
        s["dry_rate_steps_per_s"] = float(rate)
    if status == "REFUSED":
        s["prod_b_required"] = True
    write_stages(P, s)
    append_rows(P, "raw_runs.jsonl", [run_row(v)])
    append_rows(P, "raw_thermo.jsonl", thermo_rows("dryrun", parsed, "dryrun.lammps.log"))
    inputs = [describe(deck), describe(P.out / "dryrun.lammps.log", len(parsed["lines"])),
              describe(P.out / "dryrun.screen.txt"), describe(P.out / "dryrun_t0.epoch"), describe(P.out / "dryrun_t1.epoch")]
    if timing.get("read"):
        v["labels"] = throughput_labels(P, v, "dryrun")
    write_record(P, cell={"run": "dryrun"}, inputs=inputs, metric="timed dry run: status, Performance line, timing",
                 values=v, threshold={}, decision_rule="The run's status: RUNS, REFUSED, FAILED or STOPPED.",
                 decision=status)
    if status == "RUNS":
        r1 = ("RUNS_AGREE" if timing["agree"] else "RUNS_DISAGREE") if timing.get("read") else "RUNS_TIMING_NOT_READ"
    else:
        r1 = status
    write_record(P, cell={"control": "R1"}, inputs=inputs,
                 metric=("timed dry run: Performance-line ns/day of the 1,000 timed steps against 1000 x 2e-6 ns / "
                         "(wall seconds / 86400); runs or refused; units from in.init"),
                 values={"status": status, "status_line": line, "units_in_in_init": units,
                         "units_real_confirmed": units == "real", "timing": timing, "device_lines": v["device_lines"],
                         "degenerate": v["degenerate"], "labels": v.get("labels")},
                 threshold={"relative_difference_at_most": str(R1_TOLERANCE), "timed_steps": DRY_TIMED_STEPS},
                 decision_rule=("RUNS_AGREE if the dry run finished and |Performance ns/day - wall-clock ns/day| / "
                                "wall-clock ns/day <= 0.05, the wall-clock from date stamps written just before and "
                                "just after the timed run; RUNS_DISAGREE otherwise, and every later ns/day then "
                                "carries 'Performance line and wall-clock disagree'; RUNS_TIMING_NOT_READ if the "
                                "timing output is degenerate; REFUSED if an error line names centroid/stress/atom, "
                                "stress/atom, heat/flux or the GPU pair style (run a is then not run); FAILED for any "
                                "other error, which stops the run; STOPPED if the guard's deadline ended it."),
                 decision=r1)
    if status == "STOPPED":
        return EXIT_GUARD
    if status == "FAILED":
        return STAGE_EXIT["dryrun"]
    return 0


def stage_copy(P) -> int:
    g = run_guard(P, "copy")
    if g["decision"] != "go":
        return guard_stop(P, "copy", g)
    P.system.mkdir(parents=True, exist_ok=True)
    rows = []
    for src in sorted(P.box.iterdir()):
        if src.is_file():
            dst = P.system / src.name
            shutil.copyfile(src, dst)
            a, b = sha256_file(src), sha256_file(dst)
            rows.append({"file": src.name, "source_sha256": a, "copy_sha256": b, "identical": a == b})
    ok = bool(rows) and all(r["identical"] for r in rows)
    if not ok:
        void_run(P, "the box copy is empty or differs from the shipped box")
    set_stage(P, "copy", status="DONE" if ok else "FAILED")
    write_record(P, cell={"run": "copy"}, inputs=[describe(P.box / r["file"]) for r in rows],
                 metric="the shipped box copied to the writable results_m3/system/", values={"files": rows},
                 threshold={}, decision_rule="DONE if every file was copied and hashes the same; FAILED otherwise.",
                 decision="DONE" if ok else "FAILED", rows=rows)
    return 0 if ok else STAGE_EXIT["copy"]


def run_equilibration(P, deck, var_pairs, allowed_s) -> dict:
    for nm in (DENSITY_FILE, RESTART_FILE, EQUIL_LOG, EQUIL_DATA):
        (P.system / nm).unlink(missing_ok=True)
    return LAMMPS_RUNNER(P.lmp, deck, var_pairs, P.out / "equilibrate.lammps.log", P.out / "equilibrate.screen.txt",
                         P.system, allowed_s)


def equilibration_errors(P) -> list:
    """ERROR lines of the equilibration just run: the screen capture first (it holds every line LAMMPS
    printed, in order), then the command-line log and the deck's own log."""
    return unique(error_lines(read_text(P.out / "equilibrate.screen.txt"))
                  + error_lines(read_text(P.out / "equilibrate.lammps.log"))
                  + error_lines(read_text(P.system / EQUIL_LOG)))


def balance_line_error(res: dict, errors: list) -> str | None:
    """The line that triggers listed edit 3: the run ended with an error and its first ERROR line names
    comm_style, balance, tiled or rcb. A guard deadline never triggers it; neither does any other error."""
    if res.get("timed_out") or (res.get("rc") == 0 and not errors):
        return None
    if errors and names_balance_lines(errors[0]):
        return errors[0]
    return None


def keep_first_attempt(P, res, deck, var_pairs, trigger: str) -> dict:
    """The first equilibration's output, moved aside so the second attempt cannot overwrite it."""
    for a, b in (("equilibrate.lammps.log", "equilibrate_attempt1.lammps.log"),
                 ("equilibrate.screen.txt", "equilibrate_attempt1.screen.txt")):
        if (P.out / a).is_file():
            os.replace(P.out / a, P.out / b)
    copy_if_exists(P.system / EQUIL_LOG, P.out / "equilibrate_attempt1.deck.log")
    log_text = read_text(P.out / "equilibrate_attempt1.deck.log") or ""
    parsed = parse_lammps_log(log_text)
    errors = unique(error_lines(read_text(P.out / "equilibrate_attempt1.screen.txt"))
                    + error_lines(read_text(P.out / "equilibrate_attempt1.lammps.log")) + parsed["errors"])
    v = base_run_values("equilibrate", res, deck, var_pairs, P.system, "ERROR_ON_BALANCE_LINES", trigger, errors, parsed)
    v["attempt"] = 1
    append_rows(P, "raw_runs.jsonl", [run_row(v)])
    append_rows(P, "raw_thermo.jsonl", thermo_rows("equilibrate", parsed, "equilibrate_attempt1.deck.log", attempt=1))
    set_stage(P, "equilibrate", attempt1={"status": "ERROR_ON_BALANCE_LINES", "line": trigger,
                                          "wall_s": res.get("wall_s")})
    print(f"[equilibrate] the first attempt stopped on a load-balancing line: {trigger}")
    return {"trigger_error_line_verbatim": trigger,
            "first_attempt": {k: v.get(k) for k in ("deck", "deck_sha256", "command", "exit_code", "status",
                                                     "status_line", "error_lines", "stage_wall_s", "blocks")},
            "first_attempt_outputs": ["equilibrate_attempt1.lammps.log", "equilibrate_attempt1.screen.txt",
                                      "equilibrate_attempt1.deck.log"]}


def write_edit3_record(P, edit3: dict | None, decision: str, second: dict | None) -> None:
    vals = dict(edit3 or {})
    vals["second_attempt"] = second
    inputs = [describe(P.decks_src / "equilibrate.in")]
    if edit3:
        inputs += [describe(P.decks / EDIT3_DECK), describe(P.out / "equilibrate_attempt1.screen.txt"),
                   describe(P.out / "equilibrate_attempt1.deck.log")]
    write_record(P, cell={"control": "equilibrate_edit3"}, inputs=inputs,
                 metric=("listed edit 3: does the committed equilibration deck stop on its load-balancing lines "
                         "under the GPU package"),
                 values=vals, threshold={"trigger_names": list(EDIT3_NAMES)},
                 decision_rule=("NOT_TRIGGERED if the committed equilibrate.in did not stop with an error whose first "
                                "ERROR line names comm_style, balance, tiled or rcb. APPLIED if it did: that line is "
                                "kept verbatim; exactly the lines 'comm_style tiled', 'balance 1.1 rcb' and 'fix "
                                "load_balance ... rcb' are deleted in the copy results_m3/decks/"
                                "equilibrate_noballance.in (sha256 and diff kept); the equilibration runs once more "
                                "from the copy, and any error in that second attempt stops the run. "
                                "APPLIED_NOT_RERUN if the cost or time guard stopped the run before the second attempt."),
                 decision=decision)


def stage_equilibrate(P) -> int:
    g = run_guard(P, "equilibrate")
    if g["decision"] != "go":
        return guard_stop(P, "equilibrate", g)
    var_pairs = list(EQUIL_VARS) + [("system_dir", str(P.system))]
    deck = P.decks_src / "equilibrate.in"
    res = run_equilibration(P, deck, var_pairs, g["allowed_seconds"])
    trigger = balance_line_error(res, equilibration_errors(P))
    if trigger is None:
        return ingest_equilibrate(P, res, deck, var_pairs, None)
    # Listed edit 3 (EXEC_NOTE.md item 3b): keep the first attempt's output, delete the three
    # load-balancing lines in a copy, and run the equilibration once more from that copy.
    edit3 = keep_first_attempt(P, res, deck, var_pairs, trigger)
    edit3.update(build_edit3_deck(P))
    g2 = run_guard(P, "equilibrate")
    if g2["decision"] != "go":
        rc = guard_stop(P, "equilibrate", g2)
        write_edit3_record(P, edit3, "APPLIED_NOT_RERUN", None)
        return rc
    deck2 = P.decks / EDIT3_DECK
    res2 = run_equilibration(P, deck2, var_pairs, g2["allowed_seconds"])
    return ingest_equilibrate(P, res2, deck2, var_pairs, edit3)


def ingest_equilibrate(P, res, deck, var_pairs, edit3) -> int:
    copy_if_exists(P.system / EQUIL_LOG, P.out / "equilibrate.deck.log")
    copy_if_exists(P.system / DENSITY_FILE, P.out / DENSITY_FILE)
    log_text = read_text(P.system / EQUIL_LOG) or ""
    screen_text = read_text(P.out / "equilibrate.screen.txt") or ""
    cli_text = read_text(P.out / "equilibrate.lammps.log") or ""
    parsed = parse_lammps_log(log_text)
    errors = unique(error_lines(screen_text) + error_lines(cli_text) + parsed["errors"])
    status, line = run_status(res, errors, None, refusal_allowed=False)
    v = base_run_values("equilibrate", res, deck, var_pairs, P.system, status, line, errors, parsed)
    v["attempt"] = 2 if edit3 else 1
    v["edit3_applied"] = bool(edit3)
    v["edit3_trigger_error_line"] = edit3["trigger_error_line_verbatim"] if edit3 else None
    v["equilibration_done"] = parse_equilibration_done(log_text)
    v["npt_target_line_value"] = parse_npt_target(log_text)
    restart_sha = sha256_file(P.system / RESTART_FILE)
    v["restart_file"] = str(P.system / RESTART_FILE)
    v["restart_sha256"] = restart_sha
    npt = None
    try:
        npt = find_npt_block(parsed)
        v["npt_block_index"] = npt["index"]
        v["performance_ns_day"] = npt["performance_ns_day"]
        temps = column(npt, "Temp")
        v["mean_temp_K"] = sum(temps) / len(temps) if temps else None
    except (ParseError, Degenerate) as e:
        v["degenerate"].append(str(e))
    if parsed["runs"] and parsed["runs"][-1]["rows"]:
        try:
            v["final_density"] = column(parsed["runs"][-1], "Density")[-1]
        except ParseError as e:
            v["degenerate"].append(str(e))
    if status == "STOPPED":
        void_run(P, "the time or cost deadline stopped the equilibration")
    elif status != "RUNS":
        void_run(P, f"the equilibration stopped with a LAMMPS error: {line}")
    s = read_stages(P)
    s["stages"].setdefault("equilibrate", {}).update(clean({"status": status, "line": line, "wall_s": res.get("wall_s"),
                                                            "attempt": v["attempt"], "edit3_applied": bool(edit3)}))
    s["restart_sha256"] = restart_sha
    write_stages(P, s)
    append_rows(P, "raw_runs.jsonl", [run_row(v)])
    append_rows(P, "raw_thermo.jsonl", thermo_rows("equilibrate", parsed, "equilibrate.deck.log", attempt=v["attempt"]))
    log_inputs = [describe(deck), describe(P.out / "equilibrate.deck.log", len(parsed["lines"])),
                  describe(P.out / "equilibrate.screen.txt"), describe(P.out / "equilibrate.lammps.log")]
    write_record(P, cell={"run": "equilibrate"}, inputs=log_inputs,
                 metric="equilibration run: status, blocks, restart sha256, 'Equilibration done' line",
                 values=v, threshold={}, decision_rule="The run's status: RUNS, FAILED or STOPPED.", decision=status)
    write_edit3_record(P, edit3, "APPLIED" if edit3 else "NOT_TRIGGERED",
                       {"status": status, "status_line": line, "deck_sha256": v["deck_sha256"]} if edit3 else None)
    # The density anchor (E2), read now so its outcome reaches every later record.
    dens_text = read_text(P.out / DENSITY_FILE)
    e2v = {"reference_g_cm3": REF_DENSITY, "band_fraction": DENSITY_BAND,
           "density_file_text": dens_text, "equilibration_done": v["equilibration_done"],
           "npt_target_line_value": v["npt_target_line_value"]}
    drifting = False
    if status != "RUNS":
        d2 = "NOT_READ"
        e2v["not_read_because"] = f"the equilibration did not finish ({status}: {line})"
    else:
        try:
            rho = density_file_value(dens_text)
            e2v["npt_mean_density_g_cm3"] = rho
            e2v["relative_difference"] = (rho - REF_DENSITY) / REF_DENSITY
            d2 = e2_decide(rho)
            try:
                if npt is None:
                    raise Degenerate("the NPT thermo block was not found")
                dr = density_drift(npt, rho)
                e2v["drift"] = dr
                drifting = dr["drifting"]
            except (ParseError, Degenerate) as e:
                e2v["drift_not_read_because"] = str(e)
        except (ParseError, Degenerate) as e:
            d2 = "NOT_READ"
            e2v["not_read_because"] = str(e)
    if d2 != "WITHIN_BAND":
        void_run(P, f"the density anchor did not pass ({d2})", label=LABEL_ANCHOR)
    if drifting:
        add_label(P, LABEL_DRIFT)
    e2v["labels"] = ([LABEL_DRIFT] if drifting else []) + ([LABEL_ANCHOR] if d2 != "WITHIN_BAND" else [])
    write_record(P, cell={"endpoint": "E2"},
                 inputs=[describe(P.out / DENSITY_FILE, len(parse_density_file(dens_text)) if dens_text else None)] + log_inputs,
                 metric="anchor: NPT mean density over the last 250 ps (the deck's density file) against 0.805 g/cm3",
                 values=e2v, threshold={"reference_g_cm3": "0.805", "band": "+/-4%",
                                        "drift_label_if_change_over_100_ps_above": "1% of the mean"},
                 decision_rule=("WITHIN_BAND if |NPT mean density - 0.805| <= 0.04 x 0.805 g/cm3, the mean being the "
                                "single value in the deck's density file; OUTSIDE_BAND otherwise; NOT_READ if the "
                                "equilibration did not finish or the file does not hold exactly one finite positive "
                                "value. OUTSIDE_BAND or NOT_READ voids the run and labels throughput rows 'descriptive "
                                "only; anchor failed'; claims B and C (E3b, E3c) then read NOT_READ. Separately: "
                                "'density still drifting' if |least-squares slope of the thermo density over the last "
                                "250 ps| x 100 ps > 1% of the mean."),
                 decision=d2)
    write_control(P, "I2")
    if status == "STOPPED":
        return EXIT_GUARD
    if status != "RUNS":
        return STAGE_EXIT["equilibrate"]
    return 0


def prod_optional(stages: dict, variant: str) -> bool:
    return variant == "prod_c" or (variant == "prod_b" and not stages.get("prod_b_required"))


def write_prod_not_run(P, variant: str, status: str, reason: str, refusal_line: str | None = None) -> None:
    v = {"variant": variant, "what": VARIANT_WORDS[variant], "status": status, "status_line": reason,
         "refusal_line": refusal_line, "degenerate": [], "blocks": []}
    set_stage(P, variant, status=status, line=reason, refusal_line=refusal_line)
    append_rows(P, "raw_runs.jsonl", [run_row(v)])
    write_record(P, cell={"run": variant}, inputs=[], metric=f"{VARIANT_WORDS[variant]}: status", values=v,
                 threshold={}, decision_rule="The run's status: NOT_RUN or TRIMMED, with the reason.", decision=status)


def stage_prod(P, variant: str) -> int:
    stages = read_stages(P)
    dry = stages["stages"].get("dryrun", {})
    if variant == "prod_a" and dry.get("status") == "REFUSED":
        write_prod_not_run(P, variant, "NOT_RUN", "the dry run was refused (early compatibility reading)",
                           refusal_line=dry.get("refusal_line"))
        return 0
    g = run_guard(P, variant)
    if g["decision"] == "trim":
        write_prod_not_run(P, variant, "TRIMMED", f"cut by the time or cost guard: {g.get('reason')}")
        return 0
    if g["decision"] != "go":
        return guard_stop(P, variant, g)
    deck = {"prod_a": P.decks_src / "tdm.in", "prod_b": P.decks / "tdm_prod_b.in", "prod_c": P.decks / "tdm_prod_c.in"}[variant]
    if not deck.is_file():
        build_decks(P)
    dump = reset_dir(P.runs / variant)
    recorded = stages.get("restart_sha256")
    restart_ok = recorded is not None and sha256_file(P.system / RESTART_FILE) == recorded
    var_pairs = list(PROD_VARS) + [("system_dir", str(P.system)), ("dump_dir", str(dump))]
    res = LAMMPS_RUNNER(P.lmp, deck, var_pairs, P.out / f"{variant}.lammps.log", P.out / f"{variant}.screen.txt",
                        P.system, g["allowed_seconds"])
    return ingest_prod(P, variant, res, deck, var_pairs, restart_ok)


def _write_head_tail(P, variant: str, label: str, ht: dict) -> None:
    if not ht["present"]:
        return
    body = [f"# first {len(ht['head'])} lines of the {label} file ({ht['lines']} lines, {ht['data_rows']} data rows)"]
    body += ht["head"] + [f"# last {len(ht['tail'])} lines"] + ht["tail"]
    (P.out / f"{variant}.{label}.head_tail.txt").write_text("\n".join(body) + "\n")


def ingest_prod(P, variant, res, deck, var_pairs, restart_ok) -> int:
    dump = Path(dict(var_pairs)["dump_dir"])
    copy_if_exists(dump / TDM_LOG, P.out / f"{variant}.deck.log")
    copy_if_exists(dump / VOLUME_FILE, P.out / f"{variant}.volume.txt")
    stress, heat = head_tail(dump / STRESS_FILE), head_tail(dump / HEATFLUX_FILE)
    _write_head_tail(P, variant, "Stress", stress)
    _write_head_tail(P, variant, "HeatFlux", heat)
    log_text = read_text(dump / TDM_LOG) or ""
    screen_text = read_text(P.out / f"{variant}.screen.txt") or ""
    cli_text = read_text(P.out / f"{variant}.lammps.log") or ""
    parsed = parse_lammps_log(log_text)
    errors = unique(error_lines(screen_text) + error_lines(cli_text) + parsed["errors"])
    stages = read_stages(P)
    status, line = run_status(res, errors, gpu_pair_style(read_text(P.system / "in.init")),
                              refusal_allowed=(variant == "prod_a"))
    if status == "STOPPED" and prod_optional(stages, variant):
        status = "TRIMMED"
    v = base_run_values(variant, res, deck, var_pairs, P.system, status, line, errors, parsed)
    v["restart_ok"] = restart_ok
    v["restart_sha256_recorded_once"] = stages.get("restart_sha256")
    v["stress_rows"] = stress["data_rows"]
    v["heatflux_rows"] = heat["data_rows"]
    v["expected_rows_each_for_run_a_per_note"] = EXPECTED_SAMPLE_ROWS_PROD_A if variant == "prod_a" else None
    v["device_lines"] = device_lines(screen_text)
    if status == "REFUSED":                     # run a refused: marked NOT_RUN, line kept verbatim
        v["refusal_line"] = line
        status = "NOT_RUN"
        v["status"] = status
    block = parsed["runs"][1] if len(parsed["runs"]) > 1 else None
    if status == "RUNS":
        v["e8"] = e8_check(block, segment_lines(parsed["lines"], block) if block else [], restart_ok)
        try:
            b = production_block(parsed, PROD_STEPS, index=1)
            perf = dec(b["performance_ns_day"])
            v.update(performance_ns_day=perf, performance_line=b["performance_line"], loop_s=b["loop"]["seconds"],
                     atoms=b["loop"]["atoms"], per_atom_step_rate=sci4(per_atom_step_rate(b["loop"]["atoms"], perf)),
                     mean_temp_K=v["e8"]["mean_temp_K"])
            wall = dec(res["wall_s"]) if res.get("wall_s") else None
            if wall and wall > 0:
                v["whole_stage_wall_clock_ns_per_day"] = (Decimal(WARMUP_STEPS + PROD_STEPS) * TIMESTEP_FS * Decimal("1e-6")
                                                          / (wall / Decimal(86400)))
            dens = column(b, "Density")
            v["final_density"] = dens[-1] if dens else None
        except (ParseError, Degenerate, InvalidOperation) as e:
            v["degenerate"].append(str(e))
        if not v["e8"]["pass"]:
            v["segment_label"] = LABEL_UNSTABLE
        v["labels"] = throughput_labels(P, v, variant)
    if status == "STOPPED":
        void_run(P, f"the time or cost deadline stopped {variant}, which the run cannot do without")
    elif status == "FAILED":
        void_run(P, f"{variant} stopped with a LAMMPS error: {line}")
    s = read_stages(P)
    s["stages"][variant] = clean({"status": status, "line": line, "wall_s": res.get("wall_s"),
                                  "refusal_line": v.get("refusal_line")})
    if variant == "prod_a" and v.get("refusal_line"):
        s["prod_b_required"] = True
    write_stages(P, s)
    append_rows(P, "raw_runs.jsonl", [run_row(v)])
    append_rows(P, "raw_thermo.jsonl", thermo_rows(variant, parsed, f"{variant}.deck.log"))
    write_record(P, cell={"run": variant},
                 inputs=[describe(deck), describe(P.out / f"{variant}.deck.log", len(parsed["lines"])),
                         describe(P.out / f"{variant}.screen.txt"), describe(dump / STRESS_FILE, stress["data_rows"]),
                         describe(dump / HEATFLUX_FILE, heat["data_rows"])],
                 metric=f"{VARIANT_WORDS[variant]}: status, Performance line, sanity control, sample row counts",
                 values=v, threshold={"mean_temp_K": "313.15 +/- 5"},
                 decision_rule=("The run's status: RUNS, NOT_RUN (run a refused by a listed error; the line kept), "
                                "TRIMMED (an optional run cut by the guard), FAILED or STOPPED."),
                 decision=status)
    if status == "STOPPED":
        return EXIT_GUARD
    if status == "FAILED":
        return STAGE_EXIT[variant]
    return 0


def cmd_generate(P, stage: str) -> int:
    init_state(P)
    try:
        if stage == "dryrun":
            return stage_dryrun(P)
        if stage == "copy":
            return stage_copy(P)
        if stage == "equilibrate":
            return stage_equilibrate(P)
        if stage in PROD_VARIANTS:
            return stage_prod(P, stage)
        print(f"unknown stage {stage!r}", file=sys.stderr)
        return 1
    except Exception as e:  # noqa: BLE001 - a crash is a stage failure, recorded and voided
        traceback.print_exc()
        void_run(P, f"the {stage} stage raised an unexpected error: {e!r}")
        set_stage(P, stage, status="FAILED", line=repr(e))
        return STAGE_EXIT.get(stage, 1)


# =============================================================================================
# Planted outputs: realistic LAMMPS-shaped text with known answers. The instrument controls
# (I1 to I10) run them on the box; the selftest runs them locally.
# =============================================================================================
TDM_HDR = ["Step", "Temp", "Press", "Density", "Volume", "TotEng"]
EQ_HDR = ["Step", "Temp", "Press", "Density", "Volume", "Lx", "Ly", "Lz", "PotEng", "TotEng"]
PLANTED_DENSITY_TEXT = "# Time-averaged data for fix npt_density\n# TimeStep v_rho\n250000 0.80312345678\n"
PLANTED_PERF_LINE = "Performance: 123.456 ns/day, 0.194 hours/ns, 714.444 timesteps/s, 8037.500 katom-step/s"
PLANTED_REFUSAL = ("ERROR: Compute centroid/stress/atom is not supported by pair style lj/cut/coul/long/gpu "
                   "(planted line)")
PLANTED_EPOCHS = ("1760954400.250000000", "1760955012.750000000")
PLANTED_READ0_OK = ("LAMMPS (29 Aug 2024)\nReading data file ...\n  orthogonal box = (0 0 0) to (66.2788 66.2788 66.2788)\n"
                    "  reading atoms ...\n  11250 atoms\n  reading bonds ...\n  11250 bonds\nTotal wall time: 0:00:00\n")
PLANTED_META_OK = {"n_molecules": 250, "atoms_per_molecule": 45, "net_charge_per_molecule": 0.0,
                   "density_g_cm3": 0.3, "smiles": "CCCCCCCCCC1CCCCC1"}


def fake_block_lines(header, rows, steps, loop_s, ns_day, atoms=ATOMS_EXPECTED, inside=()) -> list:
    out = ["Setting up Verlet run ...", "  Unit style    : real", "  Current step  : 0", "  Time step     : 2",
           "Per MPI rank memory allocation (min/avg/max) = 52.1 | 52.1 | 52.1 Mbytes",
           "  " + " ".join(f"{h:>13}" for h in header)]
    for k, r in enumerate(rows):
        out.append("  " + " ".join(f"{x:>13}" for x in r))
        if k == 0:
            out.extend(inside)
    out += [f"Loop time of {loop_s} on 1 procs for {steps} steps with {atoms} atoms", ""]
    if ns_day is not None:
        out.append(f"Performance: {ns_day} ns/day, 0.100 hours/ns, 1000.000 timesteps/s, 11250.000 katom-step/s")
    out += ["98.9% CPU use with 1 MPI tasks x 1 OpenMP threads", "", "Total # of neighbors = 3274567",
            "Dangerous builds = 0", ""]
    return out


def fake_tdm_log(temps, ns_day="300.000", loop_s="57.600", inside=(), prod_steps=PROD_STEPS) -> str:
    lines = ["LAMMPS (29 Aug 2024)", "read_restart    ${system_dir}/equilibrated_T${T}K.restart",
             "fix             constrain_h all shake ${shake_tol} ${shake_iter} ${shake_order} m 1.008",
             "Finding SHAKE clusters ...", "     250 = # of size 2 clusters",
             "fix             warmup all nvt temp ${T} ${T} 100.0", "run             ${warmup_steps}",
             "run             25000"]
    warm = [[str(st), "313.40", "12.5", "0.80100", "290000.0", "-1234.5"] for st in (0, WARMUP_STEPS)]
    lines += fake_block_lines(TDM_HDR, warm, WARMUP_STEPS, "14.400", ns_day)
    lines += ["fix             prod all nvt temp ${T} ${T} 100.0", "run             ${prod_steps}",
              f"run             {prod_steps}"]
    n = len(temps)
    steps = [round(k * prod_steps / (n - 1)) if n > 1 else 0 for k in range(n)]
    rows = [[str(st), t, "10.0", "0.80100", "290000.0", "-1200.0"] for st, t in zip(steps, temps)]
    lines += fake_block_lines(TDM_HDR, rows, prod_steps, loop_s, ns_day, inside=inside)
    lines += ['print           "TDM segment complete: run_id=${run_id}, seg=${seg}, prod_steps=${prod_steps}"',
              f"TDM segment complete: run_id=1, seg=1, prod_steps={prod_steps}", "Total wall time: 0:01:20"]
    return "\n".join(lines) + "\n"


def fake_dryrun_log(perf="216.000", loop_s="0.800", refuse_line=None) -> str:
    lines = ["LAMMPS (29 Aug 2024)", "include         ${system_dir}/in.init", "read_data       ${system_dir}/in.data",
             "Reading data file ...", "  orthogonal box = (0 0 0) to (66.2788 66.2788 66.2788)",
             "  1 by 1 by 1 MPI processor grid", "  reading atoms ...", "  11250 atoms", "  reading bonds ...",
             "  11250 bonds", "Finding SHAKE clusters ...", "     250 = # of size 2 clusters"]
    if refuse_line:
        lines += ["run             1000", "Setting up Verlet run ...", refuse_line, "Last command: run             1000"]
        return "\n".join(lines) + "\n"
    r1 = [[str(st), "313.0", "5.0", "0.30000", "291161.0", "-100.0"] for st in (0, DRY_WARM_STEPS)]
    lines += ["run             1000"] + fake_block_lines(TDM_HDR, r1, DRY_WARM_STEPS, "0.810", perf)
    lines += ["shell           date +%s.%N > ${dump_dir}/dryrun_t0.epoch", "run             1000 pre no"]
    r2 = [[str(st), "313.2", "5.0", "0.30000", "291161.0", "-100.0"] for st in (DRY_WARM_STEPS, DRY_WARM_STEPS + DRY_TIMED_STEPS)]
    lines += fake_block_lines(TDM_HDR, r2, DRY_TIMED_STEPS, loop_s, perf)
    lines += ["shell           date +%s.%N > ${dump_dir}/dryrun_t1.epoch", "Total wall time: 0:00:03"]
    return "\n".join(lines) + "\n"


def fake_equil_log(npt_densities, target, final, system_dir="/planted") -> str:
    def r(st, d):
        return [str(st), "313.20", "1.0", d, "290000.0", "66.0", "66.0", "66.0", "-500.0", "-200.0"]
    lines = ["LAMMPS (29 Aug 2024)", "include         ${system_dir}/in.init", "read_data       ${system_dir}/in.data",
             "Reading data file ...", "  reading atoms ...", "  11250 atoms", "minimize        1.0e-4 1.0e-6 1000 10000"]
    lines += fake_block_lines(EQ_HDR, [r(0, "0.30000"), r(1000, "0.30000")], 1000, "30.0", None)
    lines += ["  Minimization stats:", "  Energy initial, next-to-last, final = ", "     -100.0  -500.0  -500.1",
              "fix             constrain_h all shake ${shake_tol} ${shake_iter} ${shake_order} m 1.008",
              "Finding SHAKE clusters ...", "fix             relax_int  all nve/limit 0.1",
              "run             ${pushoff_steps}", "run             50000"]
    lines += fake_block_lines(EQ_HDR, [r(0, "0.30000"), r(50000, "0.31000")], 50000, "40.0", "108.000")
    lines += ["fix             nvt_settle all nvt temp ${T} ${T} ${tdamp}", "run             ${settle_steps}",
              "run             100000"]
    lines += fake_block_lines(EQ_HDR, [r(0, "0.31000"), r(100000, "0.31000")], 100000, "80.0", "216.000")
    lines += ["reset_timestep  0",
              "fix             npt_density all ave/time ${density_sample_every} ${density_sample_repeat} "
              "${density_sample_freq} v_rho file ${system_dir}/density_npt_T${T}K_run${run_id}.dat ave one start "
              "${density_avg_start}",
              "fix             eq_npt all npt temp ${T} ${T} ${tdamp} iso ${P} ${P} ${pdamp} nreset 1000",
              "run             ${npt_steps}", "run             250000"]
    lines += fake_block_lines(EQ_HDR, [r(5000 * k, d) for k, d in enumerate(npt_densities)], NPT_STEPS, "200.0", "216.000")
    lines += ['print           "NPT average density target from final window: ${rho_target} g/cm^3"',
              f"NPT average density target from final window: {target} g/cm^3",
              "fix             match_density all deform 1 x final 0 1 y final 0 1 z final 0 1 units box remap x",
              "run             ${deform_steps}", "run             100000"]
    lines += fake_block_lines(EQ_HDR, [r(0, target), r(100000, final)], 100000, "80.0", "216.000")
    lines += ['print           "Equilibration done: wrote ${system_dir}/equilibrated_T${T}K.restart, '
              'target_density=${rho_target} g/cm^3, final_density=$(density:%.6f) g/cm^3"',
              f"Equilibration done: wrote {system_dir}/equilibrated_T313.15K.restart, target_density={target} g/cm^3, "
              f"final_density={final} g/cm^3", "Total wall time: 0:06:40"]
    return "\n".join(lines) + "\n"


CONTROL_FOR = {"I1": "E1", "I2": "E2", "I3": "E3", "I4": "E3b", "I5": "E3c", "I6": "E4", "I7": "E5", "I8": "E6",
               "I9": "E7", "I10": "E8"}


def _case(case: str, expected, actual, numeric: bool = False) -> dict:
    if numeric:
        try:
            ok = Decimal(str(expected)) == Decimal(str(actual))
        except InvalidOperation:
            ok = False
    else:
        ok = str(expected) == str(actual)
    return {"case": case, "expected": str(expected), "actual": str(actual), "pass": ok}


def planted_controls() -> dict:
    """The planted cases of the execution note's checklist item 9, exactly as listed there."""
    C = {}
    bad = dict(PLANTED_META_OK, net_charge_per_molecule=0.01)
    C["I1"] = [
        _case("planted net charge 0.01 e per molecule fails", "FAIL", e1_decide(e1_parts(bad, 11250, None, None))),
        _case("planted ERROR line in the zero-step read_data log fails", "FAIL",
              e1_decide(e1_parts(PLANTED_META_OK, 11250, None, PLANTED_READ0_OK + "ERROR: planted read_data failure\n")))]
    C["I2"] = [
        _case("planted density file in the deck's ave/time format gives the exact mean", "0.80312345678",
              density_file_value(PLANTED_DENSITY_TEXT)),
        _case("0.805 x 1.03 holds", "WITHIN_BAND", e2_decide(REF_DENSITY * Decimal("1.03"))),
        _case("0.805 x 1.05 fails", "OUTSIDE_BAND", e2_decide(REF_DENSITY * Decimal("1.05")))]
    C["I3"] = [
        _case("planted Performance line 123.456 parsed", "123.456", parse_performance_line(PLANTED_PERF_LINE)),
        _case("300 ns/day holds", "HOLDS", e3_decide(Decimal("300"))),
        _case("90 ns/day is below", "REFUTED_BELOW", e3_decide(Decimal("90"))),
        _case("700 ns/day is above", "REFUTED_ABOVE", e3_decide(Decimal("700")))]
    C["I4"] = [_case("150.0 passes", "PASS", e3b_decide(Decimal("150.0"))),
               _case("149.9 fails", "FAIL", e3b_decide(Decimal("149.9")))]
    r250, r125, r2353 = e3c_reprice(Decimal("250")), e3c_reprice(Decimal("125")), e3c_reprice(Decimal("235.3"))
    C["I5"] = [_case("250 ns/day -> USD 941.00", "941.00", r250["cost_usd"]),
               _case("250 ns/day is within the cap", "WITHIN_CAP", r250["decision"]),
               _case("125 ns/day -> USD 1,882.00", "1882.00", r125["cost_usd"]),
               _case("125 ns/day is above the cap", "ABOVE_CAP", r125["decision"]),
               _case("235.3 ns/day -> USD 999.79", "999.79", r2353["cost_usd"]),
               _case("235.3 ns/day is within the cap", "WITHIN_CAP", r2353["decision"])]
    C["I6"] = [_case("120 / 100 -> 1.2000", "1.2000", ratio4(Decimal(120), Decimal(100)))]
    rate = per_atom_step_rate(11250, Decimal(200), Decimal("2"))
    C["I7"] = [_case("200 / 100 -> 2.0000", "2.0000", ratio4(Decimal(200), Decimal(100))),
               _case("11,250 atoms at 200 ns/day and 2 fs -> 1.3021e7 atom-steps per second (the planted value as "
                     "corrected by the gate's addendum; the formula of checklist item 6, compared at 5 significant "
                     "digits)", "1.3021e7", round_sig(rate, 5), numeric=True)]
    st_ref, ln_ref = run_status({"rc": 1, "timed_out": False}, [PLANTED_REFUSAL], "lj/cut/coul/long/gpu", True)
    st_ok, _ = run_status({"rc": 0, "timed_out": False}, [], "lj/cut/coul/long/gpu", True)
    C["I8"] = [_case("planted refusal line -> REFUSED", "REFUSED", st_ref),
               _case("the refusal line is kept verbatim", PLANTED_REFUSAL, ln_ref),
               _case("clean output -> RUNS", "RUNS", st_ok)]
    C["I9"] = [_case("planted epochs -> seconds", "612.5",
                     epoch_span_seconds(parse_epoch(PLANTED_EPOCHS[0]), parse_epoch(PLANTED_EPOCHS[1])), numeric=True)]
    # The committed pre-launch record lives on the workstation only (the box payload does not carry out/).
    committed = HERE / "out" / "prelaunch_build_mol00557.json"
    if committed.is_file():
        pre = json.loads(committed.read_text())
        rl = (pre.get("read0") or {}).get("log")
        real = HERE / "data" / BOX_NAME
        parts = e1_parts(parse_metadata((real / "metadata.json").read_text()),
                         parse_data_header_atoms(read_head(real / "in.data")), pre, read_text(HERE / rl) if rl else None)
        C["I1"].append(_case("the committed pre-launch record and metadata.json reproduce the E1 decision", "PASS",
                             e1_decide(parts)))
        C["I9"].append(_case("builder wall-clock read from the committed pre-launch record, in seconds", "12",
                             (_last_attempt(pre)[1] or {}).get("wall_s"), numeric=True))

    def seg(temps, inside=()):
        parsed = parse_lammps_log(fake_tdm_log(temps, inside=inside))
        b = parsed["runs"][1]
        return e8_check(b, segment_lines(parsed["lines"], b), True)["pass"]
    C["I10"] = [_case("planted thermo mean 313.0 passes", "True", seg(["312.0", "314.0"])),
                _case("planted thermo mean 320.0 fails", "False", seg(["319.0", "321.0"])),
                _case("planted 'Lost atoms' line fails", "False",
                      seg(["312.0", "314.0"], inside=("WARNING: Lost atoms: original 11250 current 11249 (planted)",)))]
    return C


def write_control(P, cid: str) -> None:
    cases = planted_controls()[cid]
    ok = all(c["pass"] for c in cases)
    write_record(P, cell={"control": cid}, inputs=[describe(Path(__file__))],
                 metric=f"instrument check for endpoint {CONTROL_FOR[cid]}: planted cases with known answers",
                 values={"validates": CONTROL_FOR[cid], "cases": cases}, threshold={"every_case_passes": True},
                 decision_rule="PASS if every planted case gives its known answer; FAIL otherwise. Recorded only.",
                 decision="PASS" if ok else "FAIL", rows=cases)


# =============================================================================================
# Stage: endpoints (reads only what generate saved under results_m3/out/)
# =============================================================================================
def run_values(P, variant: str) -> dict | None:
    r = load_record(P, {"run": variant})
    return r.get("values") if r else None


def reading(vals: dict | None):
    if not vals:
        return None, "no record: the run was not reached"
    if vals.get("status") != "RUNS":
        return None, f"status {vals.get('status')}: {vals.get('status_line')}"
    if vals.get("degenerate"):
        return None, "degenerate output: " + "; ".join(vals["degenerate"])
    ns = vals.get("performance_ns_day")
    if ns is None:
        return None, "no Performance value"
    return dec(ns), None


def e6_reading(dry: dict | None, a: dict | None):
    if dry and dry.get("status") == "REFUSED":
        return "REFUSED", dry.get("status_line"), "the dry run"
    if a and a.get("refusal_line"):
        return "REFUSED", a["refusal_line"], "run a"
    if a and a.get("status") == "RUNS":
        return "RUNS", None, "run a"
    if dry and dry.get("status") == "RUNS":
        return "RUNS", None, f"the dry run (run a status: {a.get('status') if a else 'not reached'})"
    return "NOT_READ", None, None


def compute_endpoints(P) -> None:
    dry, A, B, C = (run_values(P, v) for v in ("dryrun", "prod_a", "prod_b", "prod_c"))
    e2 = load_record(P, {"endpoint": "E2"})
    anchor = e2["decision"] if e2 else "NOT_READ"
    anchor_ok = anchor == "WITHIN_BAND"
    r1_dis = LABEL_R1 in read_state(P)["labels"]
    slug = lambda v: P.out / (provenance().cell_slug({"tag": TAG, "run": v}) + ".json")
    run_in = lambda *vs: [describe(slug(v)) for v in vs] + [describe(P.out / f"{v}.deck.log") for v in vs if v != "dryrun"]

    def labels_for(vals):
        out = []
        if not anchor_ok:
            out.append(LABEL_ANCHOR)
        if r1_dis:
            out.append(LABEL_R1)
        if vals and vals.get("e8") and not vals["e8"]["pass"]:
            out.append(LABEL_UNSTABLE)
        return out

    # Compatibility: does the deck as written run with the GPU package?
    e6, e6_line, e6_src = e6_reading(dry, A)
    flags = [FLAG_TC] if e6 == "REFUSED" else []
    write_record(P, cell={"endpoint": "E6"}, inputs=run_in("dryrun", "prod_a"),
                 metric="compatibility: does the deck as written run with the GPU package",
                 values={"reading": e6, "error_line_verbatim": e6_line, "read_from": e6_src, "flags": flags,
                         "dry_run_status": dry.get("status") if dry else None,
                         "run_a_status": A.get("status") if A else None},
                 threshold={"refusal_names": list(REFUSAL_NAMES) + ["the GPU pair style (lj/cut/coul/long/gpu)"]},
                 decision_rule=("REFUSED if the dry run or run a stopped with an error line naming centroid/stress/atom, "
                                "stress/atom, heat/flux or the GPU pair style; the line is kept verbatim, run a is "
                                "NOT_RUN, E3 reads run b with the label 'viscosity-only protocol...', and the card's "
                                "thermal-conductivity arm is flagged unpriced on the GPU. RUNS if run a (or, when run a "
                                "was not reached, the dry run) finished without such an error. NOT_READ otherwise."),
                 decision=e6)

    # Claim A: the card's PROXY 250 ns/day.
    src = "prod_b" if e6 == "REFUSED" else "prod_a"
    sv = B if src == "prod_b" else A
    ns, why = reading(sv)
    e3_labels = ([LABEL_VISC] if src == "prod_b" else []) + labels_for(sv)
    measured_unread = None
    if ns is not None and not sv["e8"]["pass"]:
        measured_unread, ns = ns, None
        why = f"{LABEL_UNSTABLE}: the sanity control failed for {src}, so E3 is not read from it"
    d3 = e3_decide(ns) if ns is not None else "NOT_READ"
    tl = throughput_labels(P, sv or {}, src)
    write_record(P, cell={"endpoint": "E3"}, inputs=run_in(src),
                 metric="card PROXY throughput_ns_day = 250: ns/day of the deck as written on one A100, Performance line",
                 values={"variant_read": src, "ns_per_day": ns, "ns_per_day_measured_but_not_read": measured_unread,
                         "not_read_because": why, "performance_line": (sv or {}).get("performance_line"),
                         "loop_s": (sv or {}).get("loop_s"), "stage_wall_clock_s": (sv or {}).get("stage_wall_s"),
                         "whole_stage_wall_clock_ns_per_day": (sv or {}).get("whole_stage_wall_clock_ns_per_day"),
                         "direction": {"REFUTED_BELOW": "below 100", "REFUTED_ABOVE": "above 625"}.get(d3),
                         "stress_rows": (sv or {}).get("stress_rows"), "heatflux_rows": (sv or {}).get("heatflux_rows"),
                         "expected_rows_each_for_run_a_per_note": EXPECTED_SAMPLE_ROWS_PROD_A,
                         "labels": e3_labels, "flags": flags, "throughput_labels": tl},
                 threshold={"holds_if_within_ns_per_day": ["100", "625"]},
                 decision_rule=("Read run a (deck as written); if E6 is REFUSED, read run b with the label "
                                "'viscosity-only protocol; the deck's heat flux does not run on the GPU pair style'. "
                                "NOT_READ if that run did not finish, its output is degenerate, or it failed the "
                                "sanity control (E8). HOLDS if 100 <= ns/day <= 625; REFUTED_BELOW below 100; "
                                "REFUTED_ABOVE above 625."),
                 decision=d3)

    # Claim B: the card's gate p_bench, ns/day >= 150.
    gate_why = None if anchor_ok else f"the density anchor did not pass ({anchor})"
    if gate_why is None and ns is None:
        gate_why = f"E3 was not read ({why})"
    d3b = e3b_decide(ns) if gate_why is None else "NOT_READ"
    write_record(P, cell={"endpoint": "E3b"}, inputs=run_in(src),
                 metric="card gate p_bench: measured ns/day >= 150",
                 values={"ns_per_day": ns, "variant_read": src, "not_read_because": gate_why,
                         "card_text_applies": CARD_GATE_FAIL_TEXT if d3b == "FAIL" else None,
                         "labels": e3_labels, "throughput_labels": tl},
                 threshold={"pass_if_ns_per_day_at_least": "150"},
                 decision_rule=("NOT_READ if the density anchor (E2) did not pass or E3 was not read. PASS if "
                                "ns/day >= 150; FAIL otherwise, and the card's own text applies: 'drop the extension "
                                "tier and re-plan with 48 molecules at 3 replicas'."),
                 decision=d3b)

    # Claim C: the card's USD 941 plan, re-priced.
    rp = e3c_reprice(ns) if gate_why is None else None
    write_record(P, cell={"endpoint": "E3c"}, inputs=run_in(src),
                 metric="card plan re-priced: USD 941 x 250 / measured ns/day (GPU-hour lines scale with 1/throughput)",
                 values={"ns_per_day": ns, "variant_read": src, "not_read_because": gate_why, "reprice": rp,
                         "labels": e3_labels, "throughput_labels": tl},
                 threshold={"cap_usd": "1000", "about_ns_per_day": "235.3"},
                 decision_rule=("NOT_READ as for E3b. Re-priced plan = USD 941 x 250 / ns/day, rounded half-up to 2 "
                                "decimals. WITHIN_CAP if it is at most USD 1,000 (measured at or above about 235.3 "
                                "ns/day); ABOVE_CAP otherwise: the plan is under-priced by 250 / measured. A cost "
                                "reading, not a card prediction."),
                 decision=rp["decision"] if rp else "NOT_READ")

    # Sampling cost: run b and run c against run a.
    na, why_a = reading(A)
    for eid, variant, vals in (("E4", "prod_b", B), ("E5", "prod_c", C)):
        n, w = reading(vals)
        ratio = ratio4(n, na) if (n is not None and na is not None) else None
        vlabels = labels_for(vals)
        values = {"variant": variant, "ns_per_day": n, "not_read_because": w, "run_a_ns_per_day": na,
                  "ratio_to_run_a": ratio, "ratio_not_read_because": None if ratio is not None else (w or f"run a: {why_a}"),
                  "performance_line": (vals or {}).get("performance_line"),
                  "stage_wall_clock_s": (vals or {}).get("stage_wall_s"),
                  "whole_stage_wall_clock_ns_per_day": (vals or {}).get("whole_stage_wall_clock_ns_per_day"),
                  "per_atom_step_rate_atom_steps_per_s": (vals or {}).get("per_atom_step_rate"),
                  "stress_rows": (vals or {}).get("stress_rows"), "heatflux_rows": (vals or {}).get("heatflux_rows"),
                  "labels": vlabels, "throughput_labels": throughput_labels(P, vals or {}, variant)}
        what = "pressure tensor only" if eid == "E4" else "no per-step sampling"
        write_record(P, cell={"endpoint": eid}, inputs=run_in("prod_a", variant),
                     metric=(f"run {variant[-1]} ({what}) ns/day and ratio to run a"
                             + ("; per-atom step rate (atom-steps per second)" if eid == "E5" else "")),
                     values=values, threshold={"report": True},
                     decision_rule=(f"REPORTED: ns/day of run {variant[-1]} and the ratio run {variant[-1]} / run a "
                                    "to 4 decimals (the ratio is NOT_READ when run a was not read); NOT_READ if run "
                                    f"{variant[-1]} did not run or its output is degenerate. Descriptive only."),
                     decision="REPORTED" if n is not None else "NOT_READ")

    # Install and build readings, beside the card's 4 h l_dry time box.
    inst = parse_kv(read_text(P.out / "install_record.txt"))
    try:
        install_s = epoch_span_seconds(parse_epoch(inst.get("start_epoch")), parse_epoch(inst.get("end_epoch")))
    except (ParseError, Degenerate):
        install_s = None
    pre = json.loads(P.prelaunch.read_text()) if P.prelaunch.is_file() else None
    att_name, att = _last_attempt(pre) if pre else (None, None)
    write_record(P, cell={"endpoint": "E7"},
                 inputs=[describe(P.out / "install_record.txt"), describe(P.prelaunch), describe(slug("dryrun"))],
                 metric="install and build readings: LAMMPS install wall-clock; builder wall-clock; dry-run outcome",
                 values={"install_wall_clock_s": install_s, "install_record": inst,
                         "install_fraction_of_4h": (install_s / Decimal(L_DRY_SECONDS)) if install_s is not None else None,
                         "builder_wall_clock_s": (att or {}).get("wall_s"), "builder_attempt": att_name,
                         "builder_wall_clock_source": ("the workstation's pre-launch record" if pre else
                                                       "not on the box: the pre-launch record is not in the payload"),
                         "dry_run_status": dry.get("status") if dry else None,
                         "dry_run_success": (dry or {}).get("status") == "RUNS", "l_dry_seconds": L_DRY_SECONDS},
                 threshold={"report_against_seconds": L_DRY_SECONDS},
                 decision_rule=("REPORTED: the install wall-clock (from date stamps in install_record.txt), the "
                                "builder wall-clock and the dry-run outcome, each beside the card's 4 h time box for "
                                "'build LAMMPS ... dry-run one molecule'. Descriptive only."),
                 decision="REPORTED")

    # Sanity control, per production run.
    segs = []
    for variant, vals in (("prod_a", A), ("prod_b", B), ("prod_c", C)):
        if vals and vals.get("status") == "RUNS" and vals.get("e8"):
            e = dict(vals["e8"])
            segs.append({"variant": variant, "status": "RUNS", "pass": e["pass"], "mean_temp_K": e["mean_temp_K"],
                         "matching_lines": e["matching_lines"], "restart_ok": e["restart_ok"], "reasons": e["reasons"],
                         "segment_label": None if e["pass"] else LABEL_UNSTABLE})
        else:
            segs.append({"variant": variant, "status": (vals or {}).get("status", "NOT_REACHED"), "pass": None})
    ran = [s for s in segs if s["pass"] is not None]
    d8 = "NOT_READ" if not ran else ("PASS" if all(s["pass"] for s in ran) else "FAIL")
    write_record(P, cell={"endpoint": "E8"}, inputs=run_in("prod_a", "prod_b", "prod_c"),
                 metric="sanity control: temperature within 313.15 +/- 5 K over each production run; no error or "
                        "lost-atom lines; all from the same equilibrated restart",
                 values={"segments": segs, "restart_sha256_recorded_once": read_stages(P).get("restart_sha256")},
                 threshold={"mean_temp_K": "313.15 +/- 5", "patterns": list(E8_PATTERNS)},
                 decision_rule=("Per production run: pass if the mean thermo temperature of the 200 ps run is within "
                                "313.15 +/- 5 K, no line of that run's output (its thermo header through its Loop "
                                "line) contains 'Lost atoms', 'SHAKE', 'Bond atom missing' or 'ERROR', and the run "
                                "started from the restart whose sha256 was recorded once after equilibration. PASS if "
                                "every run that ran passes; FAIL otherwise; NOT_READ if none ran. A failing run is "
                                "'descriptive only; unstable run' and E3 is not read from it."),
                 decision=d8, rows=segs)

    for cid in ("I1", "I3", "I4", "I5", "I6", "I7", "I8", "I9", "I10"):
        write_control(P, cid)


def cmd_endpoints(P) -> int:
    init_state(P)
    g = run_guard(P, "endpoints")
    if g["decision"] != "go":
        return guard_stop(P, "endpoints", g)
    try:
        compute_endpoints(P)
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        void_run(P, f"the endpoints stage raised an unexpected error: {e!r}")
        set_stage(P, "endpoints", status="FAILED", line=repr(e))
        cmd_summary(P, note="endpoints failed")
        return STAGE_EXIT["endpoints"]
    set_stage(P, "endpoints", status="DONE")
    cmd_summary(P, note="written after the endpoints stage")
    return 0


# =============================================================================================
# Summary, void, guard, dispatch
# =============================================================================================
def cmd_summary(P, exit_code=None, note: str = "") -> int:
    init_state(P)
    incomplete = exit_code not in (None, 0)
    if incomplete:
        add_label(P, LABEL_INCOMPLETE)
    st, stages = read_state(P), read_stages(P)
    endpoints, controls, runs = {}, {}, {}
    for p in sorted(P.out.glob("*.json")):
        if p.name in NOT_RECORDS:
            continue
        try:
            r = json.loads(p.read_text())
        except (OSError, ValueError):
            continue
        if not (isinstance(r, dict) and "cell" in r and "decision_rule" in r):
            continue
        entry = {"decision": r.get("decision"), "file": p.name, "run_valid": r.get("run_valid")}
        cell = r["cell"]
        if "run" in cell:
            vals = r.get("values") or {}
            entry["performance_ns_day"] = vals.get("performance_ns_day")
            entry["label"] = LABEL_INCOMPLETE if incomplete else None
        for key, bucket in (("endpoint", endpoints), ("control", controls), ("run", runs)):
            if key in cell:
                bucket[cell[key]] = entry
    summary = {"tag": TAG, "written_utc": utc_now(), "run_valid": st["run_valid"], "voided_by": st["voided_by"],
               "run_labels": st["labels"], "labels": load_labels(P), "exit_code": exit_code, "note": note,
               "stages": stages.get("stages", {}), "trimmed_by_guard": stages.get("trimmed", []),
               "endpoints": endpoints, "controls": controls, "runs": runs,
               "incomplete_run_label": LABEL_INCOMPLETE if incomplete else None,
               "what_this_file_is": ("A restatement of the record files in this folder. It decides nothing; each "
                                     "decision lives in its own record.")}
    write_json_atomic(P.out / SUMMARY_NAME, clean(summary))
    if not (P.out / "env.txt").is_file():
        write_env_txt(P)
    print(f"[summary] run_valid={st['run_valid']} endpoints="
          + ", ".join(f"{k}:{v['decision']}" for k, v in sorted(endpoints.items())))
    return 0


def cmd_guard(P, stage: str) -> int:
    g = run_guard(P, stage)
    print(f"decision={g['decision']}")
    print(f"allowed_seconds={g['allowed_seconds']}")
    if g["decision"] == "stop":
        return guard_stop(P, stage, g)
    return 0


def dispatch(P, cmd: str, stage: str | None = None, **kw) -> int:
    if cmd == "guard":
        return cmd_guard(P, stage)
    if cmd == "extract":
        try:
            return cmd_extract(P)
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            init_state(P)
            void_run(P, f"the extract stage raised an unexpected error: {e!r}")
            set_stage(P, "extract", status="FAILED", line=repr(e))
            return STAGE_EXIT["extract"]
    if cmd == "generate":
        return cmd_generate(P, stage)
    if cmd == "endpoints":
        return cmd_endpoints(P)
    if cmd == "summary":
        return cmd_summary(P, kw.get("exit_code"), kw.get("note", ""))
    if cmd == "void":
        init_state(P)
        void_run(P, kw["reason"])
        return 0
    raise SystemExit(f"unknown command {cmd!r}")


# =============================================================================================
# Selftest: standard library only; no LAMMPS. Planted outputs with known decisions.
# =============================================================================================
PLANTED_LMP_HELP = """
Large-scale Atomic/Molecular Massively Parallel Simulator - 29 Aug 2024 - Update 1

Usage example: lmp -var t 300 -echo screen -in in.alloy

OS: Linux "Ubuntu 22.04.5 LTS" 6.8.0 x86_64

Accelerator configuration:

GPU package API: CUDA
GPU package precision: mixed

Compatible GPU present: yes

Installed packages:

COLVARS EXTRA-COMPUTE GPU KSPACE MANYBODY MOLECULE OPENMP RIGID
EXTRA-MOLECULE

List of individual style options included in this LAMMPS executable
"""
PLANTED_MM_LIST = ("List of packages in environment: \"/home/ubuntu/m3_run/engine\"\n\n"
                   "  Name          Version     Build                           Channel\n"
                   + "─" * 72 + "\n"
                   "  cuda-cudart   12.6.77     h5888daf_0                      conda-forge\n"
                   "  lammps        2024.08.29  cuda126_py310_h894d002_nompi_2  conda-forge\n"
                   "  python        3.10.16     he725a3c_1_cpython              conda-forge\n")
PLANTED_NVSMI = ("+-----------------------------------------------------------------------------------------+\n"
                 "| NVIDIA-SMI 570.148.08             Driver Version: 570.148.08     CUDA Version: 12.8     |\n"
                 "|-----------------------------------------+------------------------+----------------------+\n")
PLANTED_INSTALL = ("start_epoch=1760954400.000000000\nmicromamba_sha256=planted\nconda_override_cuda=12.8\n"
                   "spec_used=lammps=2024.08.29=cuda126_py310_h894d002_nompi_2\nend_epoch=1760954712.500000000\n"
                   "install_ok=1\n")
SELFTEST_ENV = ("PRICE_USD_PER_HOUR", "BUDGET_LEFT_USD", "REMOTE_TIMEOUT", "INSTANCE_TYPE", "M3_WINDOW_PID")


class FakeClock:
    def __init__(self, elapsed=100.0, uptime=400.0, seq=None):
        self._e, self._u, self._seq = elapsed, uptime, list(seq or [])

    def uptime(self):
        return self._u

    def window_elapsed(self):
        return self._seq.pop(0) if self._seq else self._e


class FakeLammps:
    """Writes planted LAMMPS-shaped output where the committed decks would write it."""

    def __init__(self, **kw):
        self.kw = {"dry_perf": "216.000", "dry_loop": "0.800", "dry_wall": "0.810", "dry_refuse": None,
                   "npt_density": "0.80123", "npt_rows": None, "equil_error": None, "equil_errors": [],
                   "refuse_a": None,
                   "temps": {"prod_a": ["313.0", "313.3", "312.9"], "prod_b": ["313.1", "313.2", "313.0"],
                             "prod_c": ["313.2", "313.0", "313.1"]},
                   "perf": {"prod_a": "300.000", "prod_b": "330.000", "prod_c": "360.000"},
                   "inside": {}, "prod_wall": 150.0}
        self.kw.update(kw)
        self.calls = []
        self.n_equil = 0

    def __call__(self, lmp, deck, var_pairs, cli_log, screen, cwd, timeout_s):
        v, name, K = dict(var_pairs), Path(deck).name, self.kw
        cmd = lammps_cmd(lmp, deck, var_pairs, cli_log)
        self.calls.append({"deck": name, "vars": v, "cwd": str(cwd), "timeout_s": timeout_s, "cmd": cmd})
        res = {"cmd": cmd, "rc": 0, "timed_out": False, "start_error": None,
               "start_epoch": "1760954400.000000", "end_epoch": "1760954500.000000", "wall_s": 100.0}
        if name == "dryrun.in":
            dump = Path(v["dump_dir"])
            text = fake_dryrun_log(K["dry_perf"], K["dry_loop"], K["dry_refuse"])
            Path(cli_log).write_text(text)
            Path(screen).write_text("Device 0: NVIDIA A100-SXM4-40GB, 108 CUs, 39/40 GB, 1.4 GHZ (Mixed Precision)\n" + text)
            if K["dry_refuse"]:
                res["rc"] = 1
            else:
                (dump / "dryrun_t0.epoch").write_text("1760954400.000000000\n")
                (dump / "dryrun_t1.epoch").write_text(f"{Decimal('1760954400.000000000') + Decimal(K['dry_wall'])}\n")
            res["wall_s"] = 5.0
        elif name in ("equilibrate.in", EDIT3_DECK):
            sysd = Path(v["system_dir"])
            k, self.n_equil = self.n_equil, self.n_equil + 1
            self.calls[-1]["deck_text"] = Path(deck).read_text()
            err = K["equil_error"] or (K["equil_errors"][k] if k < len(K["equil_errors"]) else None)
            if err:
                text = "LAMMPS (29 Aug 2024)\nReading data file ...\n" + err + "\n"
                res["rc"] = 1
            else:
                rows = K["npt_rows"] or [K["npt_density"]] * 51
                text = fake_equil_log(rows, K["npt_density"], K["npt_density"], str(sysd))
                (sysd / DENSITY_FILE).write_text(f"# Time-averaged data for fix npt_density\n# TimeStep v_rho\n"
                                                 f"250000 {K['npt_density']}\n")
                (sysd / RESTART_FILE).write_bytes(b"planted restart\n")
            (sysd / EQUIL_LOG).write_text(text)
            Path(cli_log).write_text("LAMMPS (29 Aug 2024)\n")
            Path(screen).write_text(text)
            res["wall_s"] = 200.0
        else:
            variant = {"tdm.in": "prod_a", "tdm_prod_b.in": "prod_b", "tdm_prod_c.in": "prod_c"}[name]
            dump = Path(v["dump_dir"])
            if variant == "prod_a" and K["refuse_a"]:
                text = "LAMMPS (29 Aug 2024)\nFinding SHAKE clusters ...\nSetting up Verlet run ...\n" + K["refuse_a"] + "\n"
                res["rc"] = 1
            else:
                text = fake_tdm_log(K["temps"][variant], ns_day=K["perf"][variant], inside=K["inside"].get(variant, ()))
                if variant in ("prod_a", "prod_b"):
                    (dump / STRESS_FILE).write_text("# Time-averaged data for fix stress_raw\n# TimeStep v_Pxx v_Pyy "
                                                    "v_Pzz v_Pxy v_Pxz v_Pyz\n"
                                                    + "".join(f"{5 * k} 1 2 3 4 5 6\n" for k in range(7)))
                if variant == "prod_a":
                    (dump / HEATFLUX_FILE).write_text("# Time-averaged data for fix flux_raw\n# TimeStep v_Jtot_x "
                                                      "v_Jtot_y v_Jtot_z\n" + "".join(f"{5 * k} 1 2 3\n" for k in range(7)))
                (dump / VOLUME_FILE).write_text("290000.0\n")
            (dump / TDM_LOG).write_text(text)
            Path(cli_log).write_text("LAMMPS (29 Aug 2024)\n")
            Path(screen).write_text(text)
            res["wall_s"] = K["prod_wall"]
        return res


def _swap(runner, clock):
    global LAMMPS_RUNNER, CLOCK
    old = (LAMMPS_RUNNER, CLOCK)
    LAMMPS_RUNNER, CLOCK = runner, clock
    return old


def _fake_root(root, *, net_charge=0.0, prelaunch=True, gpu_listed=True) -> Paths:
    root = Path(root)
    P = Paths(root)
    real_box = HERE / "data" / BOX_NAME
    real_decks = HERE / "data" / "MD-ML-thermophysical" / "MD" / "lammps"
    P.box.mkdir(parents=True)
    for nm in ("in.init", "in.settings"):
        shutil.copyfile(real_box / nm, P.box / nm)
    meta = json.loads((real_box / "metadata.json").read_text())
    meta["net_charge_per_molecule"] = net_charge
    (P.box / "metadata.json").write_text(json.dumps(meta, indent=2))
    (P.box / "in.data").write_text(read_head(real_box / "in.data", 40))   # the header is all any reader here uses
    P.decks_src.mkdir(parents=True)
    for nm in ("equilibrate.in", "tdm.in"):
        shutil.copyfile(real_decks / nm, P.decks_src / nm)
    if prelaunch:
        (root / "out").mkdir()
        pre = {"attempt_1": {"exit_code": 2, "wall_s": 1}, "attempt_2": {"exit_code": 0, "wall_s": 12},
               "read0": {"log": "out/prelaunch_read0_mol00557.out"}}
        (root / "out" / "prelaunch_build_mol00557.json").write_text(json.dumps(pre))
        (root / "out" / "prelaunch_read0_mol00557.out").write_text(PLANTED_READ0_OK)
    P.out.mkdir(parents=True)
    (P.out / "install_record.txt").write_text(PLANTED_INSTALL)
    (P.out / "micromamba_list.txt").write_text(PLANTED_MM_LIST)
    (P.out / "lmp_help.txt").write_text(PLANTED_LMP_HELP if gpu_listed else PLANTED_LMP_HELP.replace(" GPU ", " "))
    (P.out / "nvidia_smi.txt").write_text(PLANTED_NVSMI)
    (P.out / "nvidia_smi_query.txt").write_text("NVIDIA A100-SXM4-40GB, 570.148.08\n")
    return P


def _scenario(base, name, fake, *, clock=None, **root_kw):
    P = _fake_root(Path(base) / name, **root_kw)
    old_env = {k: os.environ.get(k) for k in SELFTEST_ENV}
    os.environ.update({"PRICE_USD_PER_HOUR": "1.99", "BUDGET_LEFT_USD": "5", "REMOTE_TIMEOUT": "5400",
                       "INSTANCE_TYPE": "gpu_1x_a100_sxm4"})
    os.environ.pop("M3_WINDOW_PID", None)
    old = _swap(fake, clock or FakeClock())
    codes, buf = {}, io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            init_state(P)
            for stage in ("extract", "dryrun", "copy", "equilibrate", "prod_a", "prod_b", "prod_c", "endpoints"):
                cmd = stage if stage in ("extract", "endpoints") else "generate"
                codes[stage] = dispatch(P, cmd, stage)
                if codes[stage] != 0:
                    break
            final = next((c for c in codes.values() if c != 0), 0)
            dispatch(P, "summary", exit_code=final, note=f"selftest scenario {name}")
    finally:
        _swap(*old)
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return P, codes, buf.getvalue()


def _records(P) -> dict:
    out = {}
    for p in sorted(P.out.glob("*.json")):
        if p.name in NOT_RECORDS:
            continue
        r = json.loads(p.read_text())
        if isinstance(r, dict) and "cell" in r:
            out[p.name] = r
    return out


def _rec(P, **cell):
    return load_record(P, cell)


def _jsonl(P, name) -> list:
    p = P.out / name
    return [json.loads(ln) for ln in p.read_text().splitlines()] if p.is_file() else []


def selftest() -> int:
    checks = []
    section = ["?"]

    def check(name, cond, detail=""):
        checks.append((section[0], name, bool(cond), detail))

    def sec(name):
        section[0] = name

    pycache = HERE / "frozen" / "__pycache__"
    pycache_before = pycache.exists()

    # ---- parsers -----------------------------------------------------------------------------
    sec("parsers")
    check("Performance line: ns/day read exactly", parse_performance_line(PLANTED_PERF_LINE) == Decimal("123.456"))
    try:
        parse_performance_line("Loop time of 1.0 on 1 procs for 10 steps with 5 atoms")
        check("a non-Performance line is refused", False)
    except ParseError:
        check("a non-Performance line is refused", True)
    lp = parse_loop_line("Loop time of 57.600 on 1 procs for 100000 steps with 11250 atoms")
    check("Loop line: seconds, steps, atoms", lp == {"seconds": "57.600", "procs": 1, "steps": 100000, "atoms": 11250})
    tdm_log = fake_tdm_log(["313.0", "313.3", "312.9"])
    pl = parse_lammps_log(tdm_log)
    check("thermo blocks: warm-up and production found", len(pl["runs"]) == 2)
    check("thermo block: production rows read", len(pl["runs"][1]["rows"]) == 3 and pl["runs"][1]["header"] == TDM_HDR)
    check("thermo block: Performance tied to its own run", pl["runs"][1]["performance_ns_day"] == "300.000")
    check("thermo block: echoed commands kept before each block",
          any(ln.startswith("fix             prod") for ln in pl["runs"][1]["preceding"]))
    rows = thermo_rows("prod_a", pl, "x.log")
    check("thermo rows kept verbatim (step, temp, press, density, vol, etotal, raw line)",
          rows[2]["temp"] == "313.0" and rows[2]["step"] == "0" and "313.0" in rows[2]["raw"]
          and {"press", "density", "vol", "etotal"} <= set(rows[2]))
    check("density file: the single value read exactly", density_file_value(PLANTED_DENSITY_TEXT) == Decimal("0.80312345678"))
    for label, text in (("no data rows", "# Time-averaged\n# TimeStep v_rho\n"),
                        ("two data rows", PLANTED_DENSITY_TEXT + "500000 0.81\n"),
                        ("a NaN value", "# x\n250000 nan\n"), ("a negative value", "# x\n250000 -0.8\n"),
                        ("a missing file", None)):
        try:
            density_file_value(text)
            check(f"density file degenerate ({label}) detected", False)
        except Degenerate:
            check(f"density file degenerate ({label}) detected", True)
    try:
        parse_density_file("# x\n250000 0.8 0.9\n")
        check("density file: a malformed row is refused", False)
    except ParseError:
        check("density file: a malformed row is refused", True)
    real_box = HERE / "data" / BOX_NAME
    meta = parse_metadata((real_box / "metadata.json").read_text())
    check("metadata.json: net charge 0.0, 250 x 45 atoms",
          meta["net_charge_per_molecule"] == 0.0 and meta["n_molecules"] * meta["atoms_per_molecule"] == 11250)
    try:
        parse_metadata('{"n_molecules": 250}')
        check("metadata.json: missing keys refused", False)
    except ParseError:
        check("metadata.json: missing keys refused", True)
    hp = parse_lmp_help(PLANTED_LMP_HELP)
    check("lmp -h: package list read across lines", hp["packages"][:3] == ["COLVARS", "EXTRA-COMPUTE", "GPU"]
          and "EXTRA-MOLECULE" in hp["packages"])
    check("lmp -h: version, accelerator lines, GPU present", hp["version"].startswith("29 Aug 2024")
          and "GPU package API: CUDA" in hp["accelerator_configuration"] and hp["compatible_gpu_present"] == "yes")
    check("lmp -h without an 'Installed packages' section lists nothing (degenerate)",
          parse_lmp_help("Large-scale Atomic/Molecular Massively Parallel Simulator - 29 Aug 2024\n")["packages"] == [])
    mm = parse_micromamba_list(PLANTED_MM_LIST)
    check("micromamba list: lammps build string", mm["lammps"]["build"] == "cuda126_py310_h894d002_nompi_2"
          and mm["lammps"]["version"] == "2024.08.29")
    check("micromamba list: CUDA runtime version", mm["cuda-cudart"]["version"] == "12.6.77")
    mm_cv = parse_micromamba_list(PLANTED_MM_LIST.replace("cuda-cudart   12.6.77", "cuda-version  12.6   "))
    check("micromamba list: cuda-version read when cuda-cudart is absent",
          "cuda-cudart" not in mm_cv and mm_cv["cuda-version"]["version"] == "12.6")
    check("micromamba list: header and rule lines skipped", "Name" not in mm and len(mm) == 3)
    check("micromamba list without lammps: no lammps entry (degenerate)",
          "lammps" not in parse_micromamba_list(PLANTED_MM_LIST.replace("lammps ", "other ")))
    nv = parse_nvidia_smi(PLANTED_NVSMI)
    check("nvidia-smi: driver and CUDA version", nv == {"driver_version": "570.148.08", "cuda_version": "12.8"})
    check("nvidia-smi query: GPU name", parse_nvidia_query("NVIDIA A100-SXM4-40GB, 570.148.08\n")["gpu_name"]
          == "NVIDIA A100-SXM4-40GB")
    check("epochs: seconds between two date stamps, exact",
          epoch_span_seconds(parse_epoch(PLANTED_EPOCHS[0]), parse_epoch(PLANTED_EPOCHS[1])) == Decimal("612.5"))
    try:
        epoch_span_seconds(parse_epoch(PLANTED_EPOCHS[1]), parse_epoch(PLANTED_EPOCHS[0]))
        check("epochs: an end before the start is degenerate", False)
    except Degenerate:
        check("epochs: an end before the start is degenerate", True)
    try:
        parse_epoch("")
        check("epochs: an empty stamp is refused", False)
    except ParseError:
        check("epochs: an empty stamp is refused", True)
    check("key=value install record", parse_kv(PLANTED_INSTALL)["spec_used"].endswith("nompi_2"))
    init_text = (real_box / "in.init").read_text()
    check("in.init: units real", parse_units(init_text) == "real")
    check("in.init: GPU pair style name", gpu_pair_style(init_text) == "lj/cut/coul/long/gpu")
    check("in.data header: 11,250 atoms", parse_data_header_atoms(read_head(real_box / "in.data")) == 11250)
    real_read0 = HERE / "out" / "prelaunch_read0_mol00557.out"
    if real_read0.is_file():
        t = real_read0.read_text()
        check("committed zero-step read_data log: 11,250 atoms, no ERROR line",
              parse_read_data_atoms(t) == 11250 and not error_lines(t))
    eq_log = fake_equil_log(["0.80123"] * 51, "0.80123", "0.801230")
    ed = parse_equilibration_done(eq_log)
    check("'Equilibration done' line: target and final density (the echoed print line is skipped)",
          ed and ed["target_density"] == "0.80123" and ed["final_density"] == "0.801230")
    check("NPT target line", parse_npt_target(eq_log) == "0.80123")
    peq = parse_lammps_log(eq_log)
    check("equilibration log: five blocks (minimise, push-off, settle, NPT, deform)", len(peq["runs"]) == 5)
    nb = find_npt_block(peq)
    check("NPT block found from the deck's 'fix eq_npt' line", nb["index"] == 3 and len(nb["rows"]) == 51)
    try:
        find_npt_block(parse_lammps_log(eq_log.replace("eq_npt", "eq_xxx")))
        check("NPT block missing is degenerate", False)
    except Degenerate:
        check("NPT block missing is degenerate", True)
    check("refusal: a centroid/stress/atom error is a listed refusal",
          classify_refusal([PLANTED_REFUSAL], "lj/cut/coul/long/gpu") == PLANTED_REFUSAL)
    check("refusal: a GPU pair style error is a listed refusal",
          classify_refusal(["ERROR: Pair style lj/cut/coul/long/gpu cannot do this (planted)"], "lj/cut/coul/long/gpu"))
    check("refusal: a lost-atoms error is not a listed refusal",
          classify_refusal(["ERROR: Lost atoms: original 11250 current 11249"], "lj/cut/coul/long/gpu") is None)
    st_, _ = run_status({"rc": 1, "timed_out": False}, ["ERROR: Lost atoms (planted)"], "x/gpu", True)
    check("run status: any other error is FAILED", st_ == "FAILED")
    st_, _ = run_status({"rc": -9, "timed_out": False}, [], "x/gpu", True)
    check("run status: a nonzero exit with no ERROR line is FAILED", st_ == "FAILED")
    st_, _ = run_status({"rc": None, "timed_out": True}, [], "x/gpu", True)
    check("run status: a guard deadline is STOPPED", st_ == "STOPPED")
    st_, _ = run_status({"rc": 1, "timed_out": False}, [PLANTED_REFUSAL], "x/gpu", False)
    check("run status: a refusal outside run a and the dry run is FAILED", st_ == "FAILED")
    bal = "ERROR: GPU package does not (yet) work with comm_style tiled (planted)"
    check("listed edit 3 trigger: an error naming comm_style tiled", balance_line_error({"rc": 1}, [bal]) == bal)
    check("listed edit 3 trigger: 'Fix balance ... rcb' in any letter case",
          balance_line_error({"rc": 1}, ["ERROR: Fix Balance RCB needs something (planted)"]) is not None)
    check("listed edit 3 trigger: a lost-atoms error is not a trigger",
          balance_line_error({"rc": 1}, ["ERROR: Lost atoms: original 11250 current 11249 (planted)", bal]) is None)
    check("listed edit 3 trigger: a guard deadline is not a trigger",
          balance_line_error({"rc": None, "timed_out": True}, [bal]) is None)
    check("listed edit 3 trigger: a clean run is not a trigger", balance_line_error({"rc": 0}, []) is None)
    check("GPU device line kept", device_lines("Device 0: NVIDIA A100-SXM4-40GB, 108 CUs\n- Using acceleration for pppm:\n")
          == ["Device 0: NVIDIA A100-SXM4-40GB, 108 CUs", "- Using acceleration for pppm:"])
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "s.out"
        f.write_text("# a\n# b\n" + "".join(f"{k} 1\n" for k in range(12)))
        ht = head_tail(f)
        check("Stress/HeatFlux head and tail: 5 lines each, data rows counted",
              ht["data_rows"] == 12 and ht["head"][0] == "# a" and ht["tail"][-1] == "11 1" and len(ht["tail"]) == 5)
        check("Stress/HeatFlux file missing: no row count", head_tail(Path(d) / "none")["data_rows"] is None)

    # ---- degenerate-output detectors on the timed run -----------------------------------------
    sec("degenerate outputs")
    for label, text, steps in (("wrong run read (step count)", tdm_log, 50000),
                               ("no Performance line", tdm_log.replace("Performance:", "Perf-missing:"), PROD_STEPS),
                               ("NaN Performance", re.sub(r"Performance: \S+", "Performance: nan", tdm_log), PROD_STEPS),
                               ("unfinished run", tdm_log.replace("for 100000 steps", "for 100000 stepz"), PROD_STEPS),
                               ("only one run in the log", fake_dryrun_log(refuse_line="ERROR: x"), PROD_STEPS)):
        try:
            production_block(parse_lammps_log(text), steps, 1)
            check(f"timed run degenerate ({label}) detected", False)
        except Degenerate:
            check(f"timed run degenerate ({label}) detected", True)
    check("timed run: the correct run passes", production_block(pl, PROD_STEPS, 1)["index"] == 1)
    blk = parse_lammps_log(fake_tdm_log(["nan", "313.0"])) ["runs"][1]
    check("sanity control: a NaN temperature fails", not e8_check(blk, [], True)["pass"])
    empty = dict(pl["runs"][1], rows=[])
    check("sanity control: no thermo rows fails", not e8_check(empty, [], True)["pass"])
    check("sanity control: no production block fails", not e8_check(None, [], True)["pass"])
    good = pl["runs"][1]
    check("sanity control: a restart mismatch fails", not e8_check(good, segment_lines(pl["lines"], good), False)["pass"])
    span = segment_lines(pl["lines"], good)
    check("sanity control: 'Finding SHAKE clusters' before the production run is outside its output",
          e8_check(good, span, True)["pass"] and any("Finding SHAKE clusters" in ln for ln in pl["lines"]))
    for pat in E8_PATTERNS:
        p2 = parse_lammps_log(fake_tdm_log(["313.0", "313.1"], inside=(f"WARNING: planted {pat} line",)))
        b2 = p2["runs"][1]
        check(f"sanity control: a '{pat}' line inside the production run fails", not e8_check(b2, segment_lines(p2["lines"], b2), True)["pass"])
    cut = parse_lammps_log(fake_tdm_log(["313.0", "313.1"]).split("Loop time of 57.600")[0] + "ERROR: Lost atoms: planted\n")
    bcut = cut["runs"][1]
    check("sanity control: an aborted run's ERROR line counts (output runs to the end of the log)",
          not e8_check(bcut, segment_lines(cut["lines"], bcut), True)["pass"])

    # ---- endpoint arithmetic ------------------------------------------------------------------
    sec("arithmetic")
    pc = planted_controls()
    check("the committed pre-launch record is present, so I1 and I9 also read it",
          (HERE / "out" / "prelaunch_build_mol00557.json").is_file() and len(pc["I1"]) == 3 and len(pc["I9"]) == 2)
    for cid in sorted(pc, key=lambda c: int(c[1:])):
        for c in pc[cid]:
            check(f"{cid} ({CONTROL_FOR[cid]}): {c['case']}", c["pass"], f"expected {c['expected']}, got {c['actual']}")
    ag = r1_agreement(Decimal("216.000"), Decimal("0.810"))
    check("timed dry run: 216.000 ns/day against 0.810 s for 1,000 steps agrees within 5%",
          ag["agree"] and qround(ag["wall_clock_ns_per_day"], 3) == Decimal("213.333"))
    check("timed dry run: 216.000 ns/day against 1.200 s disagrees", not r1_agreement(Decimal("216"), Decimal("1.2"))["agree"])
    flat = parse_lammps_log(fake_equil_log(["0.80000"] * 51, "0.8", "0.8"))
    dr0 = density_drift(find_npt_block(flat), Decimal("0.8"))
    check("density drift: a flat window is not drifting (26 rows, slope 0)",
          dr0["n_rows"] == 26 and dr0["slope_g_cm3_per_ps"] == 0 and not dr0["drifting"])
    def ramp_drift(per_row):
        ramp = [f"{Decimal('0.70') + Decimal(per_row) * k:.4f}" for k in range(51)]
        return density_drift(find_npt_block(parse_lammps_log(fake_equil_log(ramp, "0.8", "0.8"))), Decimal("0.8"))
    dr1 = ramp_drift("0.0004")
    check("density drift: 0.0004 g/cm3 per 10 ps is a slope of 4e-5 per ps, 0.004 per 100 ps, under the 0.008 limit",
          dr1["slope_g_cm3_per_ps"] == Decimal("0.00004") and not dr1["drifting"])
    dr2 = ramp_drift("0.0010")
    check("density drift: 0.0010 g/cm3 per 10 ps is 0.01 per 100 ps, over 1% of 0.8, so drifting",
          dr2["change_over_100_ps"] == Decimal("0.01") and dr2["drifting"])
    check("E3c threshold: 235.25 ns/day costs exactly USD 1,000.00, within the cap",
          e3c_reprice(Decimal("235.25"))["cost_usd"] == Decimal("1000.00")
          and e3c_reprice(Decimal("235.25"))["decision"] == "WITHIN_CAP")
    check("E3c: the under-pricing ratio at 125 ns/day is 2.0000",
          e3c_reprice(Decimal("125"))["under_pricing_ratio_250_over_measured"] == Decimal("2.0000"))
    check("E1: all parts present and passing -> PASS",
          e1_decide(e1_parts(PLANTED_META_OK, 11250, {"attempt_2": {"exit_code": 0}}, PLANTED_READ0_OK)) == "PASS")
    check("E1: pre-launch record absent (as on the box) -> PASS_ON_PARTS_PRESENT",
          e1_decide(e1_parts(PLANTED_META_OK, 11250, None, None)) == "PASS_ON_PARTS_PRESENT")
    check("E1: builder exit 2 on the last attempt -> FAIL",
          e1_decide(e1_parts(PLANTED_META_OK, 11250, {"attempt_1": {"exit_code": 0}, "attempt_2": {"exit_code": 2}}, None)) == "FAIL")
    check("E1: 11,205 atoms in the data header -> FAIL", e1_decide(e1_parts(PLANTED_META_OK, 11205, None, None)) == "FAIL")

    # ---- deck copies ---------------------------------------------------------------------------
    sec("decks")
    tdm = (HERE / "data" / "MD-ML-thermophysical" / "MD" / "lammps" / "tdm.in").read_text()
    b_text, _ = edit1_pressure_only(tdm)
    c_text, _ = edit2_no_sampling(tdm)
    firsts = lambda t: [c["tokens"][:2] for c in deck_commands(t)[1] if c["tokens"]]
    has = lambda t, a, b: [a, b] in firsts(t)
    for nm in ("myKE", "myPE", "stressC", "stressK", "fluxC", "redJkX", "redJkY", "redJkZ"):
        check(f"edit 1: compute {nm} gone", not has(b_text, "compute", nm))
    for nm in ("nktv2p_real", "JkXa", "JkYa", "JkZa", "Jtot_x", "Jtot_y", "Jtot_z"):
        check(f"edit 1: variable {nm} gone", not has(b_text, "variable", nm))
    check("edit 1: fix flux_raw and its file line gone", not has(b_text, "fix", "flux_raw") and "HeatFlux_perstep" not in b_text)
    check("edit 1: pressure tensor kept (compute TT, compute myP, Pxx..Pyz, fix stress_raw with its file line)",
          has(b_text, "compute", "TT") and has(b_text, "compute", "myP") and has(b_text, "fix", "stress_raw")
          and all(has(b_text, "variable", f"P{x}") for x in ("xx", "yy", "zz", "xy", "xz", "yz"))
          and "Stress_perstep" in b_text)
    for t, nm in ((b_text, "edit 1"), (c_text, "edit 2")):
        check(f"{nm}: thermostat, warm-up, restart, thermo, runs, SHAKE, write_restart kept",
              has(t, "fix", "prod") and has(t, "fix", "warmup") and ["restart", "${restart_every}"] in firsts(t)
              and firsts(t).count(["thermo", "${thermo_every}"]) == 2 and ["run", "${warmup_steps}"] in firsts(t)
              and ["run", "${prod_steps}"] in firsts(t) and has(t, "fix", "constrain_h")
              and any(f[0] == "write_restart" for f in firsts(t)) and any(f[0] == "velocity" for f in firsts(t)))
        check(f"{nm}: no dangling continuation line", all(f[0] != "file" for f in firsts(t)))
    check("edit 2: no compute line left", all(f[0] != "compute" for f in firsts(c_text)))
    check("edit 2: no fix ave/time left, no sample files named", "ave/time" not in c_text and "perstep" not in c_text)
    for nm in ("Pxx", "Pyz", "Jtot_x", "JkXa", "nktv2p_real", "dump_every"):
        check(f"edit 2: sampling-only variable {nm} gone", not has(c_text, "variable", nm))
    check("edit 2: variables used elsewhere kept (dump_dir, seed, T, prod_steps)",
          all(has(c_text, "variable", n) for n in ("dump_dir", "seed", "T", "prod_steps", "restart_every")))
    check("edit 2: the volume print kept", 'print           "$(vol)"' in c_text)
    dr_text = build_dryrun_deck(tdm, "planted")
    tdm_lines, tdm_cmds = deck_commands(tdm)
    verbatim = lambda c: "".join(tdm_lines[c["start"]:c["end"] + 1])
    check("dry-run deck: in.init, in.data, in.settings, timestep 2.0",
          all(s in dr_text for s in ("include         ${system_dir}/in.init\n", "read_data       ${system_dir}/in.data\n",
                                     "include         ${system_dir}/in.settings\n", "timestep        2.0\n")))
    for c in tdm_cmds:
        tk = c["tokens"]
        if tk and (tk[0] == "compute" or (tk[0] == "variable") or (tk[0] == "fix" and len(tk) > 3 and tk[3] == "ave/time")
                   or tk[:2] in (["fix", "constrain_h"], ["fix", "prod"]) or tk[0] == "velocity"):
            check(f"dry-run deck: verbatim '{' '.join(tk[:2])}'", verbatim(c) in dr_text)
    check("dry-run deck: 1,000 warm-up then 1,000 timed steps between date stamps",
          dr_text.index("run             1000\n") < dr_text.index("dryrun_t0.epoch") < dr_text.index("run             1000 pre no\n")
          < dr_text.index("dryrun_t1.epoch"))
    check("dry-run deck: no restart read or written, no log command",
          all(f[0] not in ("read_restart", "restart", "write_restart", "log") for f in firsts(dr_text)))
    eq_src = (HERE / "data" / "MD-ML-thermophysical" / "MD" / "lammps" / "equilibrate.in").read_text()
    e3_text, e3_gone = edit3_no_balance(eq_src)
    e3_toks = [t.split()[:2] for t in e3_gone]
    check("edit 3: exactly comm_style tiled, balance 1.1 rcb and fix load_balance deleted",
          e3_toks == [["comm_style", "tiled"], ["balance", "1.1"], ["fix", "load_balance"]], f"{e3_gone}")
    e3_diff = unified_diff(eq_src, e3_text, "equilibrate.in", EDIT3_DECK).splitlines()
    minus = [ln for ln in e3_diff if ln.startswith("-") and not ln.startswith("---")]
    plus = [ln for ln in e3_diff if ln.startswith("+") and not ln.startswith("+++")]
    check("edit 3: the diff removes 3 lines and adds none", len(minus) == 3 and not plus, f"{minus} {plus}")
    gone_lines = {"comm_style      tiled", "balance         1.1 rcb",
                  "fix             load_balance all balance 2000 1.05 rcb"}
    check("edit 3: every other line kept, in order, comments included",
          e3_text.splitlines() == [ln for ln in eq_src.splitlines() if ln not in gone_lines]
          and "# rebalance MPI domains (dilute packing)" in e3_text)
    e3_first = firsts(e3_text)
    check("edit 3: minimise, SHAKE, the four runs, the NPT density fix, deform and write_restart kept",
          ["minimize", "1.0e-4"] in e3_first and has(e3_text, "fix", "constrain_h") and has(e3_text, "fix", "npt_density")
          and has(e3_text, "fix", "eq_npt") and has(e3_text, "fix", "match_density")
          and sum(1 for f in e3_first if f[0] == "run") == 4 and any(f[0] == "write_restart" for f in e3_first)
          and not has(e3_text, "comm_style", "tiled") and not any(f[0] == "balance" for f in e3_first))
    try:
        edit3_no_balance(eq_src.replace("comm_style      tiled\n", ""))
        check("edit 3: a deck without the comm_style line is refused", False)
    except DeckError:
        check("edit 3: a deck without the comm_style line is refused", True)
    check("dry-run deck: commands only from LAMMPS's vocabulary used here",
          {f[0] for f in firsts(dr_text)} <= {"variable", "include", "read_data", "timestep", "fix", "velocity", "thermo",
                                              "thermo_style", "compute", "run", "shell"})

    # ---- guard -----------------------------------------------------------------------------------
    sec("guard")
    measured = {"stages": {"dryrun": {"status": "RUNS"}}, "trimmed": [], "prod_b_required": False,
                "dry_rate_steps_per_s": 1250.0}
    gd = lambda st, s, e, **k: guard_decide(st, s, elapsed_s=e, uptime_s=k.get("u", 400.0), timeout_s=5400.0,
                                           price=k.get("price", Decimal("1.99")), budget=k.get("budget", Decimal("5")))
    g0 = gd("install", {"stages": {}, "trimmed": []}, 100.0)
    check("guard: plenty of time -> go, with time kept back for the required stages",
          g0["decision"] == "go" and 0 < g0["allowed_seconds"] < 5300)
    g1 = gd("prod_a", measured, 4900.0)
    check("guard: short of time -> run c cut first, then run b", g1["decision"] == "go" and g1["trims"] == ["prod_c", "prod_b"])
    g1b = gd("prod_a", measured, 4820.0)
    check("guard: a little more time -> only run c cut", g1b["decision"] == "go" and g1b["trims"] == ["prod_c"])
    check("guard: run a does not fit -> stop", gd("prod_a", measured, 5100.0)["decision"] == "stop")
    req = dict(measured, prod_b_required=True)
    g2 = gd("prod_a", req, 4900.0)
    check("guard: when run b stands in for run a it is never cut", g2["decision"] == "stop" and g2["trims"] == ["prod_c"])
    check("guard: missing price -> stop", gd("install", {"stages": {}}, 0.0, price=None)["decision"] == "stop")
    check("guard: budget too small -> stop", gd("install", {"stages": {}}, 0.0, budget=Decimal("0.2"))["decision"] == "stop")
    check("guard: an already cut stage stays cut", gd("prod_c", dict(measured, trimmed=["prod_c"]), 10.0)["decision"] == "trim")
    check("parse_positive: rejects empty, zero, negative, text", all(parse_positive(x) is None for x in ("", "0", "-1", "abc", "nan")))

    # ---- whole runs on planted engines: records, validity propagation, decisions -----------------
    with tempfile.TemporaryDirectory() as base:
        sec("scenario: everything passes")
        fake = FakeLammps()
        P, codes, log = _scenario(base, "pass", fake)
        check("every stage exits 0", set(codes.values()) == {0} and len(codes) == 8, f"{codes}")
        decks = [c["deck"] for c in fake.calls]
        check("LAMMPS runs in order: dry run, equilibration, runs a, b, c",
              decks == ["dryrun.in", "equilibrate.in", "tdm.in", "tdm_prod_b.in", "tdm_prod_c.in"], f"{decks}")
        check("every LAMMPS command is 'lmp -sf gpu -pk gpu 1 -in <deck> -var ... -log <log>'",
              all(c["cmd"][1:7] == ["-sf", "gpu", "-pk", "gpu", "1", "-in"] and c["cmd"][-2] == "-log" for c in fake.calls))
        eqc = fake.calls[1]
        check("equilibration -var values exactly as the note lists",
              eqc["vars"] == dict(EQUIL_VARS, system_dir=str(P.system)), f"{eqc['vars']}")
        for c, v in zip(fake.calls[2:], PROD_VARIANTS):
            check(f"{v}: -var values exactly as the note lists, from the box copy, own dump dir",
                  c["vars"] == dict(PROD_VARS, system_dir=str(P.system), dump_dir=str(P.runs / v)) and c["cwd"] == str(P.system))
        check("dry run runs from the shipped box directory", fake.calls[0]["cwd"] == str(P.box))
        check("committed decks unedited", sha256_file(P.decks_src / "tdm.in") == sha256_file(HERE / "data" / "MD-ML-thermophysical" / "MD" / "lammps" / "tdm.in"))
        R = lambda **c: (_rec(P, **c) or {})
        check("E1 PASS (pre-launch record present)", R(endpoint="E1").get("decision") == "PASS")
        check("R1 RUNS_AGREE", R(control="R1").get("decision") == "RUNS_AGREE")
        check("E2 WITHIN_BAND, density 0.80123", R(endpoint="E2").get("decision") == "WITHIN_BAND"
              and R(endpoint="E2")["values"]["npt_mean_density_g_cm3"] == "0.80123")
        e3 = R(endpoint="E3")
        check("E3 HOLDS at 300.000 ns/day from run a", e3.get("decision") == "HOLDS" and e3["values"]["ns_per_day"] == "300.000"
              and e3["values"]["variant_read"] == "prod_a")
        tl = e3["values"]["throughput_labels"]
        check("E3 carries every label the note lists",
              tl["instance_type"] == "gpu_1x_a100_sxm4" and tl["gpu_name"] == "NVIDIA A100-SXM4-40GB"
              and tl["gpu_driver"] == "570.148.08" and tl["cuda_runtime_version"] == "12.6.77"
              and "cuda126_py310_h894d002_nompi_2" in tl["lammps_build"] and "GPU" in tl["lmp_help_packages"]
              and tl["timestep_fs"] == "2.0" and tl["atom_count"] == 11250 and tl["variant_read"] == "prod_a"
              and tl["per_atom_step_rate_atom_steps_per_s"] == "1.9531e+07" and tl["install_wall_clock_s"] == "312.500000000"
              and tl["price_usd_per_hour"] == "1.99" and tl["labels"] == [LABEL_BOX, LABEL_ENGINE], f"{tl}")
        check("E3b PASS", R(endpoint="E3b").get("decision") == "PASS")
        check("E3c WITHIN_CAP at USD 784.17", R(endpoint="E3c").get("decision") == "WITHIN_CAP"
              and R(endpoint="E3c")["values"]["reprice"]["cost_usd"] == "784.17")
        check("E4 ratio 1.1000", R(endpoint="E4")["values"]["ratio_to_run_a"] == "1.1000")
        check("E5 ratio 1.2000 and a per-atom rate", R(endpoint="E5")["values"]["ratio_to_run_a"] == "1.2000"
              and R(endpoint="E5")["values"]["per_atom_step_rate_atom_steps_per_s"] == "2.3438e+07")
        check("E6 RUNS", R(endpoint="E6").get("decision") == "RUNS")
        check("E7 REPORTED with install 312.5 s and builder 12 s",
              R(endpoint="E7").get("decision") == "REPORTED" and R(endpoint="E7")["values"]["install_wall_clock_s"] == "312.500000000"
              and R(endpoint="E7")["values"]["builder_wall_clock_s"] == 12)
        check("E8 PASS, restart hash recorded once", R(endpoint="E8").get("decision") == "PASS"
              and R(endpoint="E8")["values"]["restart_sha256_recorded_once"] == sha256_file(P.system / RESTART_FILE))
        for cid in pc:
            want = "PASS" if all(c["pass"] for c in pc[cid]) else "FAIL"
            check(f"control {cid} record matches its planted cases ({want})", R(control=cid).get("decision") == want)
        recs = _records(P)
        check("one record per endpoint E1 to E8 (E3, E3b, E3c apart) and per control R1, I1 to I10",
              all(R(endpoint=e) for e in ("E1", "E2", "E3", "E3b", "E3c", "E4", "E5", "E6", "E7", "E8"))
              and all(R(control=c) for c in ["R1"] + [f"I{k}" for k in range(1, 11)]))
        check("every record has cell, inputs, metric, values, threshold, decision_rule, decision, run_valid",
              all({"cell", "inputs", "metric", "values", "threshold", "decision_rule", "decision", "env", "run_valid"} <= set(r)
                  for r in recs.values()))
        check("every record valid", all(r["run_valid"] is True for r in recs.values()))
        rows_all = _jsonl(P, "raw_runs.jsonl") + _jsonl(P, "raw_thermo.jsonl")
        check("raw rows: one per run and one per thermo line, each valid",
              len(_jsonl(P, "raw_runs.jsonl")) == 5 and all(r["run_valid"] is True for r in rows_all) and len(rows_all) > 60)
        summ = json.loads((P.out / SUMMARY_NAME).read_text())
        check("summary: run_valid true and every endpoint restated", summ["run_valid"] is True and len(summ["endpoints"]) == 10)
        check("summary: a finished run carries no incomplete-run label",
              summ["incomplete_run_label"] is None and all(r["label"] is None for r in summ["runs"].values())
              and summ["runs"]["prod_a"]["performance_ns_day"] == "300.000")
        check("logs kept: deck logs, density file, head/tail of the sample files, decks and diffs",
              all((P.out / n).is_file() for n in ("equilibrate.deck.log", DENSITY_FILE, "prod_a.deck.log", "prod_a.Stress.head_tail.txt",
                                                  "prod_a.HeatFlux.head_tail.txt", "decks/tdm_prod_b.diff", "decks/dryrun.in",
                                                  "env.txt", STATE_NAME, "dryrun_t0.epoch")))
        check("sample row counts carried by the throughput endpoints", R(endpoint="E3")["values"]["stress_rows"] == 7
              and R(endpoint="E3")["values"]["heatflux_rows"] == 7 and R(endpoint="E4")["values"]["heatflux_rows"] is None)
        check("run a sample row counts recorded", R(run="prod_a")["values"]["stress_rows"] == 7
              and R(run="prod_a")["values"]["heatflux_rows"] == 7 and R(run="prod_b")["values"]["heatflux_rows"] is None)
        check("no secret written to env.txt", "HF_TOKEN" not in (P.out / "env.txt").read_text())

        sec("scenario: the density anchor fails (planted gate-failure row)")
        P, codes, log = _scenario(base, "anchor", FakeLammps(npt_density="0.84525"), prelaunch=False)
        recs = _records(P)
        check("the run continues to the endpoints", set(codes.values()) == {0} and len(codes) == 8, f"{codes}")
        check("E2 OUTSIDE_BAND", (_rec(P, endpoint="E2") or {}).get("decision") == "OUTSIDE_BAND")
        check("RUN_VALID.json false with the anchor reason", read_state(P)["run_valid"] is False
              and any("density anchor" in r for r in read_state(P)["voided_by"]))
        after = ["endpoint-E2_tag-m3.json", "control-I2_tag-m3.json", "run-prod_a_tag-m3.json", "run-prod_b_tag-m3.json",
                 "run-prod_c_tag-m3.json"] + [f"endpoint-{e}_tag-m3.json" for e in ("E3", "E3b", "E3c", "E4", "E5", "E6", "E7", "E8")] \
            + [f"control-I{k}_tag-m3.json" for k in (1, 3, 4, 5, 6, 7, 8, 9, 10)]
        check("every record written after the failure carries run_valid=false, per-run files included",
              all(n in recs and recs[n]["run_valid"] is False for n in after),
              str([n for n in after if n not in recs or recs[n]["run_valid"] is not False]))
        late_rows = [r for r in _jsonl(P, "raw_runs.jsonl") + _jsonl(P, "raw_thermo.jsonl") if r["variant"] in PROD_VARIANTS]
        check("every raw row written after the failure carries run_valid=false", late_rows and all(r["run_valid"] is False for r in late_rows))
        check("summary run_valid false", json.loads((P.out / SUMMARY_NAME).read_text())["run_valid"] is False)
        check("claims B and C NOT_READ", _rec(P, endpoint="E3b")["decision"] == "NOT_READ" and _rec(P, endpoint="E3c")["decision"] == "NOT_READ")
        check("E3 still reported as a step rate with 'descriptive only; anchor failed'",
              _rec(P, endpoint="E3")["decision"] == "HOLDS" and LABEL_ANCHOR in _rec(P, endpoint="E3")["values"]["labels"])
        check("E1 PASS_ON_PARTS_PRESENT without the pre-launch record", _rec(P, endpoint="E1")["decision"] == "PASS_ON_PARTS_PRESENT")

        sec("scenario: the dry run is refused by the heat-flux compute")
        fake = FakeLammps(dry_refuse=PLANTED_REFUSAL)
        P, codes, log = _scenario(base, "dryrefuse", fake)
        check("every stage exits 0", set(codes.values()) == {0}, f"{codes}")
        check("R1 REFUSED", _rec(P, control="R1")["decision"] == "REFUSED")
        check("run a NOT_RUN with the line verbatim", _rec(P, run="prod_a")["decision"] == "NOT_RUN"
              and _rec(P, run="prod_a")["values"]["refusal_line"] == PLANTED_REFUSAL)
        check("run a never started", "tdm.in" not in [c["deck"] for c in fake.calls])
        e6 = _rec(P, endpoint="E6")
        check("E6 REFUSED, error line verbatim, thermal-conductivity arm flagged",
              e6["decision"] == "REFUSED" and e6["values"]["error_line_verbatim"] == PLANTED_REFUSAL and FLAG_TC in e6["values"]["flags"])
        e3 = _rec(P, endpoint="E3")
        check("E3 read from run b with the viscosity-only label",
              e3["values"]["variant_read"] == "prod_b" and e3["values"]["ns_per_day"] == "330.000" and LABEL_VISC in e3["values"]["labels"])
        check("the run stays valid", read_state(P)["run_valid"] is True)

        sec("scenario: run a is refused after a clean dry run")
        P, codes, log = _scenario(base, "arefuse", FakeLammps(refuse_a="ERROR: Compute heat/flux cannot run here (planted)"))
        check("every stage exits 0", set(codes.values()) == {0}, f"{codes}")
        check("E6 REFUSED from run a", _rec(P, endpoint="E6")["decision"] == "REFUSED" and _rec(P, endpoint="E6")["values"]["read_from"] == "run a")
        check("E3 from run b", _rec(P, endpoint="E3")["values"]["variant_read"] == "prod_b")
        check("E4 ratio not read without run a", _rec(P, endpoint="E4")["values"]["ratio_to_run_a"] is None)

        sec("scenario: the pre-launch build gate fails")
        fake = FakeLammps()
        P, codes, log = _scenario(base, "e1fail", fake, net_charge=0.01)
        check("extract stops with code 4", codes == {"extract": 4}, f"{codes}")
        check("E1 FAIL carrying run_valid=false", _rec(P, endpoint="E1")["decision"] == "FAIL" and _rec(P, endpoint="E1")["run_valid"] is False)
        check("no LAMMPS run", fake.calls == [])
        check("summary run_valid false", json.loads((P.out / SUMMARY_NAME).read_text())["run_valid"] is False)

        sec("scenario: run a fails its sanity control")
        P, codes, log = _scenario(base, "unstable", FakeLammps(temps={"prod_a": ["319.0", "321.0"], "prod_b": ["313.0", "313.1"],
                                                                         "prod_c": ["313.0", "313.1"]}))
        check("every stage exits 0", set(codes.values()) == {0}, f"{codes}")
        check("E8 FAIL", _rec(P, endpoint="E8")["decision"] == "FAIL")
        check("run a labelled 'descriptive only; unstable run'", _rec(P, run="prod_a")["values"]["segment_label"] == LABEL_UNSTABLE)
        check("E3 not read from run a; E3b and E3c NOT_READ",
              _rec(P, endpoint="E3")["decision"] == "NOT_READ" and _rec(P, endpoint="E3b")["decision"] == "NOT_READ"
              and _rec(P, endpoint="E3c")["decision"] == "NOT_READ"
              and _rec(P, endpoint="E3")["values"]["ns_per_day_measured_but_not_read"] == "300.000")
        check("a failed sanity control does not void the run", read_state(P)["run_valid"] is True)

        sec("scenario: Performance line and wall-clock disagree")
        P, codes, log = _scenario(base, "r1dis", FakeLammps(dry_wall="1.200"))
        check("R1 RUNS_DISAGREE", _rec(P, control="R1")["decision"] == "RUNS_DISAGREE")
        check("every later ns/day carries the label", all(LABEL_R1 in _rec(P, **c)["run_labels"] for c in
                                                          ({"endpoint": "E3"}, {"endpoint": "E4"}, {"endpoint": "E5"}, {"run": "prod_a"}))
              and LABEL_R1 in _rec(P, endpoint="E3")["values"]["labels"])

        sec("scenario: the equilibration stops with a LAMMPS error")
        fake = FakeLammps(equil_error="ERROR: Lost atoms: original 11250 current 11249 (planted)")
        P, codes, log = _scenario(base, "eqfail", fake)
        check("the run stops with code 12", codes.get("equilibrate") == 12 and "prod_a" not in codes, f"{codes}")
        check("E2 NOT_READ, run void", _rec(P, endpoint="E2")["decision"] == "NOT_READ" and read_state(P)["run_valid"] is False)
        check("no production run started", [c["deck"] for c in fake.calls] == ["dryrun.in", "equilibrate.in"])

        check("no second attempt and the edit 3 record says NOT_TRIGGERED",
              _rec(P, control="equilibrate_edit3")["decision"] == "NOT_TRIGGERED"
              and not (P.out / "decks" / EDIT3_DECK).exists())

        sec("scenario: the equilibration stops on a load-balancing line, then runs from the edited copy")
        bal = "ERROR: GPU package does not (yet) work with comm_style tiled (planted)"
        fake = FakeLammps(equil_errors=[bal, None])
        P, codes, log = _scenario(base, "edit3", fake)
        check("every stage exits 0", set(codes.values()) == {0} and len(codes) == 8, f"{codes}")
        decks = [c["deck"] for c in fake.calls]
        check("LAMMPS runs: dry run, committed equilibrate.in, its edited copy, then runs a, b, c",
              decks == ["dryrun.in", "equilibrate.in", EDIT3_DECK, "tdm.in", "tdm_prod_b.in", "tdm_prod_c.in"], f"{decks}")
        two = len(fake.calls) >= 3 and fake.calls[2]["deck"] == EDIT3_DECK
        check("the second attempt has the same -var values and command form",
              two and fake.calls[2]["vars"] == fake.calls[1]["vars"] and fake.calls[2]["cmd"][1:7] == fake.calls[1]["cmd"][1:7])
        check("the copy that ran lacks exactly the three load-balancing lines",
              two and fake.calls[2]["deck_text"] == edit3_no_balance(fake.calls[1]["deck_text"])[0]
              and "comm_style" not in fake.calls[2]["deck_text"] and "rcb" not in fake.calls[2]["deck_text"])
        er = _rec(P, control="equilibrate_edit3") or {}
        ev = er.get("values", {})
        check("edit 3 record: APPLIED, error line verbatim, diff, copy sha256, second attempt RUNS",
              er.get("decision") == "APPLIED" and ev.get("trigger_error_line_verbatim") == bal
              and "-comm_style      tiled" in ev.get("diff", "") and ev.get("edited_copy_sha256") == sha256_file(P.decks / EDIT3_DECK)
              and (ev.get("second_attempt") or {}).get("status") == "RUNS", f"{er.get('decision')}")
        check("the first attempt's output kept apart; the copy and its diff returned with the results",
              all((P.out / n).is_file() for n in ("equilibrate_attempt1.screen.txt", "equilibrate_attempt1.deck.log",
                                                  "equilibrate_attempt1.lammps.log", "decks/" + EDIT3_DECK, "decks/" + EDIT3_DIFF)))
        eqr = (_rec(P, run="equilibrate") or {}).get("values", {})
        check("the equilibration record is the second attempt, from the copy", eqr.get("attempt") == 2
              and str(eqr.get("deck")).endswith(EDIT3_DECK) and eqr.get("edit3_trigger_error_line") == bal)
        eq_rows = [r for r in _jsonl(P, "raw_runs.jsonl") if r["variant"] == "equilibrate"]
        check("one raw row per equilibration attempt",
              [r["attempt"] for r in eq_rows] == [1, 2] and eq_rows[0]["status"] == "ERROR_ON_BALANCE_LINES"
              and eq_rows[1]["status"] == "RUNS")
        check("E2 read from the second attempt; the run stays valid",
              (_rec(P, endpoint="E2") or {}).get("decision") == "WITHIN_BAND" and read_state(P)["run_valid"] is True)
        check("the committed equilibrate.in is unedited", sha256_file(P.decks_src / "equilibrate.in")
              == sha256_file(HERE / "data" / "MD-ML-thermophysical" / "MD" / "lammps" / "equilibrate.in"))

        sec("scenario: the edited copy also stops with an error")
        fake = FakeLammps(equil_errors=[bal, "ERROR: Lost atoms: original 11250 current 11249 (planted)"])
        P, codes, log = _scenario(base, "edit3fail", fake)
        check("the run stops with code 12 after one second attempt", codes.get("equilibrate") == 12
              and [c["deck"] for c in fake.calls] == ["dryrun.in", "equilibrate.in", EDIT3_DECK], f"{codes}")
        er = _rec(P, control="equilibrate_edit3") or {}
        check("edit 3 record APPLIED, second attempt FAILED, carrying run_valid=false",
              er.get("decision") == "APPLIED" and ((er.get("values") or {}).get("second_attempt") or {}).get("status") == "FAILED"
              and er.get("run_valid") is False)
        check("E2 NOT_READ and the run void", _rec(P, endpoint="E2")["decision"] == "NOT_READ"
              and read_state(P)["run_valid"] is False)

        sec("scenario: the time guard cuts runs c and b")
        fake = FakeLammps()
        clock = FakeClock(seq=[100.0, 110.0, 120.0, 130.0, 4900.0, 4950.0, 4960.0, 4970.0])
        P, codes, log = _scenario(base, "trim", fake, clock=clock)
        check("every stage exits 0", set(codes.values()) == {0}, f"{codes}")
        check("runs b and c TRIMMED", _rec(P, run="prod_b")["decision"] == "TRIMMED" and _rec(P, run="prod_c")["decision"] == "TRIMMED")
        check("only run a ran", [c["deck"] for c in fake.calls] == ["dryrun.in", "equilibrate.in", "tdm.in"])
        check("E4 and E5 NOT_READ; E3 still read", _rec(P, endpoint="E4")["decision"] == "NOT_READ"
              and _rec(P, endpoint="E5")["decision"] == "NOT_READ" and _rec(P, endpoint="E3")["decision"] == "HOLDS")
        check("the run stays valid", read_state(P)["run_valid"] is True)
        check("run a got a deadline below the time left", 0 < fake.calls[2]["timeout_s"] <= 5400 - 4900)

        sec("scenario: the time guard stops the run before run a")
        clock = FakeClock(seq=[100.0, 110.0, 120.0, 130.0, 5100.0])
        P, codes, log = _scenario(base, "stop", FakeLammps(), clock=clock)
        check("the run stops with code 3", codes.get("prod_a") == 3, f"{codes}")
        check("the run is void and summarised", read_state(P)["run_valid"] is False
              and json.loads((P.out / SUMMARY_NAME).read_text())["run_valid"] is False)
        sm = json.loads((P.out / SUMMARY_NAME).read_text())
        check("an early stop labels every finished run 'incomplete run: descriptive only, no verdict'",
              sm["incomplete_run_label"] == LABEL_INCOMPLETE and sm["runs"]
              and all(r["label"] == LABEL_INCOMPLETE for r in sm["runs"].values())
              and LABEL_INCOMPLETE in sm["run_labels"])

        sec("scenario: lmp -h does not list the GPU package")
        P, codes, log = _scenario(base, "nogpu", FakeLammps(), gpu_listed=False)
        check("extract stops with code 2", codes == {"extract": 2}, f"{codes}")
        check("the GPU check record says NOT_LISTED and the run is void",
              _rec(P, control="gpu_package")["decision"] == "NOT_LISTED" and read_state(P)["run_valid"] is False)

        sec("all scenarios")
        words_ok, every_valid_field = True, True
        for sd in Path(base).iterdir():
            for f in (sd / "results_m3" / "out").rglob("*"):
                if f.is_file():
                    txt = f.read_text(errors="replace")
                    if re.search(r"replicat", txt, re.I):
                        words_ok = False
                    if f.suffix == ".json" and f.name not in (STATE_NAME, LABELS_NAME, SUMMARY_NAME, STAGES_NAME):
                        r = json.loads(txt)
                        every_valid_field &= ("run_valid" in r)
                    if f.suffix == ".jsonl":
                        every_valid_field &= all("run_valid" in json.loads(ln) for ln in txt.splitlines())
        check("no output presents the three same-box runs as independent repeats", words_ok)
        check("every record and every raw row carries run_valid", every_valid_field)

    sec("command line (as onbox_m3.sh calls it)")
    with tempfile.TemporaryDirectory() as base:
        P = _fake_root(Path(base) / "cli")
        old_env = {k: os.environ.get(k) for k in SELFTEST_ENV}
        buf = io.StringIO()
        try:
            os.environ.update({"PRICE_USD_PER_HOUR": "1.99", "BUDGET_LEFT_USD": "5", "REMOTE_TIMEOUT": "5400"})
            os.environ["M3_WINDOW_PID"] = str(os.getpid())
            el = Clock().window_elapsed()
            check("window clock: this process's age read from /proc", 0 <= el < Clock().uptime())
            # The guard counts box uptime as billed time, true on a freshly launched box; a planted
            # clock stands in for it here, since this workstation has been up far longer.
            old_rc = _swap(LAMMPS_RUNNER, FakeClock(elapsed=100.0, uptime=400.0))
            try:
                with contextlib.redirect_stdout(buf):
                    rc_go = main(["--root", str(P.root), "guard", "--stage", "install"])
            finally:
                _swap(*old_rc)
            out = buf.getvalue()
            check("guard --stage install: code 0 and an allowed_seconds=N line",
                  rc_go == 0 and re.search(r"^allowed_seconds=[1-9][0-9]*$", out, re.M) is not None, out[-200:])
            os.environ["PRICE_USD_PER_HOUR"] = ""
            old_rc = _swap(LAMMPS_RUNNER, FakeClock(elapsed=100.0, uptime=400.0))
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    rc_stop = main(["--root", str(P.root), "guard", "--stage", "install"])
            finally:
                _swap(*old_rc)
            check("guard with no price: code 3 and the run void", rc_stop == 3 and read_state(P)["run_valid"] is False)
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--root", str(P.root), "void", "--reason", "planted reason"])
                rc_sum = main(["--root", str(P.root), "summary", "--exit-code", "3", "--note", "planted stop"])
            sm = json.loads((P.out / SUMMARY_NAME).read_text())
            check("void and summary: the reason kept, code and run_valid restated",
                  rc_sum == 0 and "planted reason" in sm["voided_by"] and sm["exit_code"] == 3 and sm["run_valid"] is False)
            check("summary writes env.txt when missing", (P.out / "env.txt").is_file())
        finally:
            for k, v in old_env.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    sec("environment")
    heavy = [m for m in ("numpy", "torch", "transformers", "scipy", "pandas") if m in sys.modules]
    check("standard library only (no heavy module imported)", not heavy, f"{heavy}")
    check("no cache folder written beside the frozen record writer", pycache.exists() == pycache_before)

    fails = [c for c in checks if not c[2]]
    by_sec = collections.OrderedDict()
    for s, n, ok, d in checks:
        by_sec.setdefault(s, [0, 0])[0 if ok else 1] += 1
    for s, (ok, bad) in by_sec.items():
        print(f"[{s}] {ok} passed, {bad} failed")
    for s, n, ok, d in fails:
        print(f"FAIL [{s}] {n}" + (f" -- {d}" if d else ""))
    print(f"selftest: {len(checks) - len(fails)} of {len(checks)} checks passed")
    print("selftest: PASS" if not fails else f"selftest: FAILED ({len(fails)} failing)")
    return 0 if not fails else 1


# =============================================================================================
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Runner for the m3 throughput measurement (see the module docstring).")
    ap.add_argument("--selftest", action="store_true", help="standard library only; runs no LAMMPS")
    ap.add_argument("--root", default=str(HERE), help="the run folder (default: this file's folder)")
    sub = ap.add_subparsers(dest="cmd")
    g = sub.add_parser("guard")
    g.add_argument("--stage", required=True, choices=STAGE_ORDER)
    sub.add_parser("extract")
    gen = sub.add_parser("generate")
    gen.add_argument("--stage", required=True, choices=("dryrun", "copy", "equilibrate") + PROD_VARIANTS)
    sub.add_parser("endpoints")
    s = sub.add_parser("summary")
    s.add_argument("--exit-code", type=int, default=None)
    s.add_argument("--note", default="")
    v = sub.add_parser("void")
    v.add_argument("--reason", required=True)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.cmd:
        ap.print_help()
        return 1
    P = Paths(a.root)
    return dispatch(P, a.cmd, getattr(a, "stage", None), exit_code=getattr(a, "exit_code", None),
                    note=getattr(a, "note", ""), reason=getattr(a, "reason", None))


if __name__ == "__main__":
    sys.exit(main())
