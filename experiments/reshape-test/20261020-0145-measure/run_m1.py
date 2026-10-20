#!/usr/bin/env python3
"""Runner for measurement m1: time one batched GR4J forward pass on one rented GPU box.

Plain-words summary
-------------------
GR4J is a daily rainfall-runoff model with four parameters, X1 to X4.
airGR is the reference R package for GR4J; its source tarball is committed under data/.
A planning card guessed two costs and promised to measure them first.
  * One forward pass over 2,684 parallel chains on one GPU: guessed 2 ms.
  * The matching vectorized CPU time for 100,000 iterations: guessed 3 hours.
This runner measures both on the box, puts them into the card's own formula, and reads its rule.

Two anchors must hold before any timing number counts.
  * airGR itself gives an efficiency score of 0.495 +/- 0.02 on its own worked example.
  * The JAX copy of GR4J gives the same score and matches airGR's daily flow within 1%.
The efficiency score is the Nash-Sutcliffe efficiency (NSE): 1 minus squared error over observed variance.

Stages, each runnable on its own:
  extract    parse the committed data and airGR source, draw parameters, write the R script.
  generate   take measurements one part at a time; every measurement becomes one JSON line.
  endpoints  derive the remaining records from those raw lines.

Validity travels with every row and record.
RUN_VALID.json holds the current state; every writer stamps it into what it writes.
A failed anchor or gate sets run_valid false in everything written after it.
An early stop rewrites every finished row and record with the incomplete-run label.

A short summary file, m1_summary.json, restates run validity, labels and every decision.
It is written after the endpoints stage and after any early stop. It decides nothing.
The launcher fetches it first, before the larger files.

Toolchain on the box: the image's preinstalled JAX is used as is, never installed or upgraded.
The only Python install is pyreadr, a second reader of the committed data file.

Usage:
  python3 run_m1.py --selftest                      standard library only; no JAX, no R
  python3 run_m1.py extract   [--out DIR]
  python3 run_m1.py generate  --part PART [--backend gpu|cpu] [--out DIR]
  python3 run_m1.py endpoints [--out DIR]
  python3 run_m1.py guard     --stage STAGE [--out DIR]   (exit 10 means stop)
  python3 run_m1.py gpu-check [--out DIR]                 (exit 3 means JAX sees no GPU)
  python3 run_m1.py stop      --reason TEXT [--out DIR]   (marks the run incomplete, writes the summary)
  python3 run_m1.py void      --reason TEXT [--out DIR]
  python3 run_m1.py summary   [--out DIR]                 (restates the records in m1_summary.json)
  python3 run_m1.py versions  --label NAME [--compare-to FILE] [--out DIR]
                              (exit 2 if jax, jaxlib or numpy changed since FILE)
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # never leave a bytecode cache beside the frozen record writer

import argparse
import bz2
import datetime as dt
import gzip
import hashlib
import json
import lzma
import math
import os
import random
import re
import shutil
import statistics
import struct
import subprocess
import tarfile
import tempfile
import time
import traceback
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "frozen"))
import provenance  # noqa: E402  frozen record writer, standard library only

# ----------------------------------------------------------------------------------------------
# Fixed inputs and design numbers. Every number here comes from the design record or the
# execution directive, unless its comment says it is a build choice.
# ----------------------------------------------------------------------------------------------
TAG = "m1"
DATA_RDA = HERE / "data" / "L0123001.rda"
DATA_TARBALL = HERE / "data" / "airGR_1.7.9.tar.gz"
RDA_SHA256 = "e82399bbea6e95d0395adfa792c6db7c7345a476b580fdfe2d050ed5cce1afaa"
TARBALL_SHA256 = "7af0d1858a116f7525f2615c392acbd2d91baa6d8df3ba2d667bb2ddb3d8b082"
RDA_ROWS = 10593  # 1984-01-01 to 2012-12-31, one row per day
DEFAULT_OUT = HERE / "results_m1" / "out"

ANCHOR_X = (165.05, 6.46, 422.50, 2.45)     # the airGR page's calibrated set ("Michel set")
GENERALIST_X = (291.0, 0.30, 109.10, 2.01)  # the airGR page's best generalist set
CAL_PERIOD = ("1990-01-01", "1990-02-28")   # the page's calibration period, 59 days
VAL_PERIOD = ("1990-03-01", "1999-12-31")   # the page's validation period
ANCHOR_NSE, ANCHOR_TOL = 0.495, 0.02
GENERALIST_CAL_NSE, MICHEL_VAL_NSE, HELDOUT_TOL = 0.336, 0.57, 0.02
MARE_MAX = 0.01                             # mean absolute relative error of daily flow, < 1%

AIRGR_CASES = (
    {"id": "anchor_cal", "set": "anchor", "X": ANCHOR_X, "period": CAL_PERIOD, "page_nse": ANCHOR_NSE},
    {"id": "generalist_cal", "set": "generalist", "X": GENERALIST_X, "period": CAL_PERIOD,
     "page_nse": GENERALIST_CAL_NSE},
    {"id": "michel_val", "set": "michel", "X": ANCHOR_X, "period": VAL_PERIOD, "page_nse": MICHEL_VAL_NSE},
)

SIZES = (268, 1340, 2684)
N_MAX = 2684
N_DAYS = 7300
SHORT_DAYS = 730
SEEDS = (1, 2, 3)          # each seed is the forcing's tiling offset, in days
REPEATS = 10               # timed passes per seed per size per backend
PROBE_ITERS = 1000
PROBE_BLOCK = 100          # build choice: one raw row per 100 iterations
PROPOSAL_FRACTION = 0.05   # proposal scale = 0.05 of each parameter's airGR range
PARAM_DRAW_SEED = 0        # build choice: the one fixed seed of the 2,684-vector draw
ITERATIONS_MAIN = 100000
DESIGN_OVERHEAD = 4.0
E3_BAND = (0.67, 6.0)
E4_BAND = (1.0, 9.0)
E5_HOURS_MIN, E5_SPEEDUP_MIN = 1.0, 20.0
E6_GATE_HOURS = 6.0
E7_TARGET_RATIO, E7_TOL = 10.0, 0.20
I3_SLEEP_MS, I3_TOL_MS = 100.0, 5.0
I4_BAND = (0.07, 0.13)

LABEL_PAGE_ONLY_RUN = "anchor by page value"
LABEL_E2_PAGE_ONLY = "page value only; no independent code ran"
LABEL_ANCHOR_FAILED = "descriptive only; anchor failed"
LABEL_INCOMPLETE = "incomplete run: descriptive only, no verdict"
GATE_STOP_TEXT = "Stop and replan: full Bayesian 671 is not affordable on one GPU"

SUMMARY_FILE = "m1_summary.json"  # restates the records for the launcher's criticals-first fetch
ALL_IDS = ("E1", "E2", "E3", "E4", "E5", "E6", "E7", "I1", "I2", "I3", "I4", "I5", "I6", "I7")
PINNED_PACKAGES = ("jax", "jaxlib", "numpy")  # preinstalled on the image; installing pyreadr must not change them
IMPORTED_PACKAGES = PINNED_PACKAGES + ("pyreadr",)
VERSION_PACKAGES = IMPORTED_PACKAGES + ("pandas", "narwhals")  # the last two: metadata only, never imported
SELFTEST_BLOCKED = ("jax", "jaxlib", "numpy", "pyreadr", "pandas", "narwhals")

# Cost guard. Stage lengths are build guesses used only to project spend before a stage starts.
STAGE_EST_H = {
    "preflight": 0.0, "pip": 0.1, "r_install": 0.2, "extract": 0.02, "anchor_airgr": 0.02,
    "anchor_jax": 0.05, "timers": 0.05, "timing_gpu": 0.1, "timing_cpu": 0.3, "probe_gpu": 0.2,
    "probe_cpu": 0.5, "endpoints": 0.02,
}
FETCH_MARGIN_H = 0.1       # build guess: billed time after the run, for fetch and teardown
MIN_SECONDS_LEFT = 60      # do not start a stage with less time than this before the cap

EXIT_OK, EXIT_CRASH, EXIT_ENV, EXIT_NO_GPU, EXIT_STOPPED, EXIT_HALT, EXIT_GUARD_STOP = 0, 1, 2, 3, 4, 5, 10

# ----------------------------------------------------------------------------------------------
# GR4J constants, read from the committed airGR 1.7.9 source (checked by verify_source_constants).
# ----------------------------------------------------------------------------------------------
# frun_GR4J.f90 declares "doubleprecision, parameter :: B=0.9". The literal 0.9 has default
# (single) precision, so the double B holds the single-precision value of 0.9.
B_SPLIT = struct.unpack("<f", struct.pack("<f", 0.9))[0]
D_EXP = 2.5                  # frun_GR4J.f90: D=2.5, the unit-hydrograph exponent
PERC_CONST = 25.62890625     # frun_GR4J.f90: stored_val, (9/4)**4
WS_MAX = 13.0                # frun_GR4J.f90: IF(WS.GT.13.) WS=13.
NH = 20                      # frun_GR4J.f90: NH=20 (UH1 has 20 ordinates, UH2 has 40)
X1X3_MIN, X4_MIN = 1e-2, 0.5  # RunModel_GR4J.R: lower clamps on X1, X3 and X4
INI_PROD, INI_ROUT = 0.3, 0.5  # CreateRunOptions.R: default IniResLevels c(0.3, 0.5, NA, NA)

SOURCE_CHECKS = (
    ("airGR/src/frun_GR4J.f90", "doubleprecision, parameter :: B=0.9"),
    ("airGR/src/frun_GR4J.f90", "doubleprecision, parameter :: stored_val=25.62890625"),
    ("airGR/src/frun_GR4J.f90", "IF(WS.GT.13.) WS=13."),
    ("airGR/src/frun_GR4J.f90", "D=2.5"),
    ("airGR/src/frun_GR4J.f90", "integer, parameter :: NH=20,NMISC=30"),
    ("airGR/src/frun_GR4J.f90", "QD=MAX(0.d0,StUH2(1)+EXCH)"),
    ("airGR/src/utils_D.f90", "SS1=(FI/C)**D"),
    ("airGR/src/utils_D.f90", "SS2=0.5*(FI/C)**D"),
    ("airGR/src/utils_D.f90", "SS2=1.-0.5*(2.-FI/C)**D"),
    ("airGR/R/RunModel_GR4J.R", "Param_X1X3_threshold <- 1e-2"),
    ("airGR/R/RunModel_GR4J.R", "Param_X4_threshold   <- 0.5"),
    ("airGR/R/CreateRunOptions.R", "IniResLevels <- as.double(c(0.3, 0.5, NA, NA))"),
    ("airGR/R/CreateRunOptions.R", "TmpDateR <- TmpDateR0 - 365 * 24 * 60 * 60"),
    ("airGR/R/ErrorCrit_NSE.R", "Crit <- (1 - Emod / Eref)"),
)
TRANSFO_MEMBER = "airGR/R/TransfoParam_GR4J.R"
CALIB_MEMBER = "airGR/R/CreateCalibOptions.R"

# ----------------------------------------------------------------------------------------------
# Decision rules, fixed before any value exists. Records copy these texts verbatim.
# ----------------------------------------------------------------------------------------------
RULES = {
    "E1": ("airGR on L0123001, X=(165.05, 6.46, 422.50, 2.45), run period 1990-01-01..1990-02-28, default "
           "warm-up and initial states, NSE on Qmm: PASS if |NSE - 0.495| <= 0.02, else FAIL (page or period "
           "misread; timing void, run_valid false from here on). NOT_RUN if R or airGR could not be "
           "installed or run; the error text is kept and the run is labelled 'anchor by page value'."),
    "E2": ("JAX GR4J on the same inputs and period, on the GPU and on the CPU backend: PASS if every backend "
           "gives |NSE - 0.495| <= 0.02 AND mean absolute relative error of daily flow versus airGR < 0.01 "
           "on matching dates, with no non-finite or all-zero flow; else FAIL (timed model is not GR4J; "
           "timing void, run_valid false from here on). If airGR did not run, the NSE band alone decides, "
           "labelled 'page value only; no independent code ran'."),
    "E3": ("Median of the 30 timed GPU passes at 2,684 chains (3 seeds x 10 repeats, distinct parameters, "
           "7,300 days): HOLDS if 0.67 <= median <= 6 ms, else REFUTED (card guess off by more than 3x)."),
    "E4": ("cpu_671_hours = 100000 * (median of the 30 timed CPU passes at 2,684 chains, ms) / 1000 / 3600 * "
           "measured CPU overhead: HOLDS if 1 <= hours <= 9, else REFUTED."),
    "E5": ("main_run_hours = 100000 * GPU median ms / 1000 / 3600 * measured GPU overhead; speedup = "
           "cpu_671_hours / main_run_hours. Decision if_not if main_run_hours >= 1 OR speedup < 20, else "
           "if_lever (the card's expected outcome is refuted). A sensitivity line repeats this with the "
           "design overhead 4 on both backends; it does not decide."),
    "E6": ("Card gate: pass if main_run_hours <= 6 (measured GPU overhead). Otherwise the card's text applies, "
           "'Stop and replan: full Bayesian 671 is not affordable on one GPU', and every later record is "
           "written run_valid false."),
    "E7": ("GPU chain-steps per second = n_chains * 7300 / (median ms / 1000) at 268, 1,340 and 2,684 chains; "
           "ratio = throughput(2,684) / throughput(268). Report only: 'linear' if 8 <= ratio <= 12; "
           "'GPU saturates below 2,684 chains' if ratio < 8; 'above linear' if ratio > 12."),
    "I1": ("airGR held-out values: generalist X=(291, 0.30, 109.10, 2.01) on 1990-01-01..1990-02-28 gives "
           "NSE 0.336 +/- 0.02 AND the Michel set X=(165.05, 6.46, 422.50, 2.45) on 1990-03-01..1999-12-31 "
           "gives NSE 0.57 +/- 0.02: PASS, else FAIL (run_valid false from here on). NOT_RUN if airGR "
           "did not run."),
    "I2": ("JAX on GPU and CPU reproduces both held-out values (same bands) AND matches airGR daily flow with "
           "MARE < 0.01 on both periods (skipped and labelled if airGR did not run), AND the planted model "
           "rows pass: zero rain gives zero quickflow; unit-hydrograph ordinates sum to 1 within 1e-9; mass "
           "balance closes within 1e-6 mm over a planted year. PASS, else FAIL (run_valid false from here on)."),
    "I3": ("On each backend, a 100 ms time.sleep measured through the timing harness reads within 95..105 ms: "
           "PASS, else FAIL (run_valid false from here on)."),
    "I4": ("On each backend at 2,684 chains, median of 10 timed 730-day passes / median of 10 timed 7,300-day "
           "passes lies in [0.07, 0.13]: PASS, else FAIL (run_valid false from here on)."),
    "I5": ("Planted arithmetic: ms 2 with overhead 4 gives main_run_hours 0.2222; ms 20 gives 2.2222; with "
           "cpu_hours 3 the speedups are 13.5 and 1.35. PASS if the endpoint code reproduces all four."),
    "I6": ("Planted gate rows: main_run_hours 5.9 gives pass and 6.1 gives 'Stop and replan...'; the planted "
           "gate-failure row sets run_valid false in every record and row written after it (scratch "
           "folder). PASS if all hold."),
    "I7": ("Planted arithmetic: 2,684 x 7,300 chain-steps in 60 ms gives 3.2655e8 chain-steps per second; "
           "equal planted times at 268 and 2,684 chains give a ratio of 10 (to one decimal) read as linear. "
           "PASS if both hold."),
}
METRICS = {
    "E1": "airGR NSE on the 59-day run period (anchor)",
    "E2": "JAX GR4J NSE on the 59-day run period and daily-flow MARE versus airGR (anchor)",
    "E3": "batched_forward_ms: median GPU forward-pass time at 2,684 chains",
    "E4": "cpu_671_hours derived from the CPU forward-pass time and measured CPU overhead",
    "E5": "card decision: main_run_hours and GPU-over-CPU speedup",
    "E6": "card gate: main_run_hours <= 6",
    "E7": "GPU throughput scaling, chain-steps per second at 268, 1,340, 2,684 chains",
    "I1": "control: airGR reproduces the page's held-out NSE values",
    "I2": "control: JAX reproduces the held-out values and airGR daily flow; planted model rows",
    "I3": "control: timing harness reads a 100 ms sleep correctly on each backend",
    "I4": "control: a 730-day scan takes 7% to 13% of a 7,300-day scan on each backend",
    "I5": "control: planted arithmetic for the card decision",
    "I6": "control: planted gate rows and run_valid propagation",
    "I7": "control: planted arithmetic for throughput and scaling ratio",
}
THRESHOLDS = {
    "E1": {"center": ANCHOR_NSE, "tolerance": ANCHOR_TOL},
    "E2": {"nse_center": ANCHOR_NSE, "nse_tolerance": ANCHOR_TOL, "mare_max": MARE_MAX},
    "E3": {"low_ms": E3_BAND[0], "high_ms": E3_BAND[1]},
    "E4": {"low_hours": E4_BAND[0], "high_hours": E4_BAND[1]},
    "E5": {"main_run_hours_min_for_if_not": E5_HOURS_MIN, "speedup_min_for_if_lever": E5_SPEEDUP_MIN},
    "E6": {"max_main_run_hours": E6_GATE_HOURS},
    "E7": {"target_ratio": E7_TARGET_RATIO, "relative_tolerance": E7_TOL},
    "I1": {"generalist_cal_nse": GENERALIST_CAL_NSE, "michel_val_nse": MICHEL_VAL_NSE, "tolerance": HELDOUT_TOL},
    "I2": {"generalist_cal_nse": GENERALIST_CAL_NSE, "michel_val_nse": MICHEL_VAL_NSE,
           "tolerance": HELDOUT_TOL, "mare_max": MARE_MAX, "uh_sum_tol": 1e-9, "mass_balance_tol_mm": 1e-6},
    "I3": {"sleep_ms": I3_SLEEP_MS, "tolerance_ms": I3_TOL_MS},
    "I4": {"low_ratio": I4_BAND[0], "high_ratio": I4_BAND[1]},
    "I5": {"main_run_hours_ms2": 0.2222, "main_run_hours_ms20": 2.2222, "speedups": [13.5, 1.35]},
    "I6": {"pass_at": 5.9, "stop_at": 6.1},
    "I7": {"chain_steps_per_s": 3.2655e8, "ratio": 10.0},
}
TIMING_RECORDS = ("E3", "E4", "E5", "E6", "E7", "I3", "I4")
HW_KEYS = ("instance_type", "gpu_name", "gpu_count", "driver_version", "jax_version", "jaxlib_version",
           "vcpu_count", "price_usd_per_hour", "lambda_instance_id", "dtype")


class Halt(Exception):
    """A degenerate-output detector fired. The run stops; `code` names the cause."""

    def __init__(self, code: str, detail: str):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail = code, detail


class StopRun(Exception):
    """The cost or time guard asked for a clean stop."""


_LOG = {"quiet": False, "prefix": ""}


def log(msg: str) -> None:
    if not _LOG["quiet"]:
        print(_LOG["prefix"] + msg, flush=True)


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


# ----------------------------------------------------------------------------------------------
# JSON helpers. Non-finite numbers become null so every file stays strict JSON.
# ----------------------------------------------------------------------------------------------
def clean(x):
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    if isinstance(x, dict):
        return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [clean(v) for v in x]
    return x


def dump_json(path: Path, obj) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(clean(obj), indent=1, sort_keys=True, allow_nan=False))
    os.replace(tmp, path)


def load_json(path: Path):
    return json.loads(Path(path).read_text())


def append_jsonl(path: Path, row: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(clean(row), sort_keys=True, allow_nan=False)
    with open(path, "a") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


def read_jsonl(path: Path, strict: bool = True):
    """Parse one JSON object per line. Strict mode raises on any bad line."""
    path = Path(path)
    if not path.exists():
        return [] if strict else ([], [])
    rows, bad = [], []
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError("line is not a JSON object")
            rows.append(obj)
        except ValueError as e:
            if strict:
                raise ValueError(f"{path}: line {n} is not valid JSON ({e})") from None
            bad.append(line)
    return rows if strict else (rows, bad)


# ----------------------------------------------------------------------------------------------
# Run validity state, stamped into every row and record at write time.
# ----------------------------------------------------------------------------------------------
class RunState:
    FILE = "RUN_VALID.json"

    def __init__(self, out):
        self.out = Path(out)
        self.path = self.out / self.FILE

    def load(self) -> dict:
        if self.path.exists():
            return load_json(self.path)
        return {"tag": TAG, "run_valid": True, "labels": [], "timing_labels": [], "void_reasons": [],
                "incomplete": False, "events": []}

    def save(self, st: dict) -> None:
        st["updated_utc"] = now_utc()
        dump_json(self.path, st)

    def ensure(self) -> None:
        if not self.path.exists():
            self.save(self.load())

    def void(self, reason: str, timing_label: str | None = None) -> None:
        st = self.load()
        st["run_valid"] = False
        if reason not in st["void_reasons"]:
            st["void_reasons"].append(reason)
        if timing_label and timing_label not in st["timing_labels"]:
            st["timing_labels"].append(timing_label)
        st["events"].append({"utc": now_utc(), "event": "void", "reason": reason})
        self.save(st)
        log(f"[run_valid] set false: {reason}")

    def add_label(self, label: str) -> None:
        st = self.load()
        if label not in st["labels"]:
            st["labels"].append(label)
            st["events"].append({"utc": now_utc(), "event": "label", "label": label})
            self.save(st)

    def mark_incomplete(self, reason: str) -> None:
        st = self.load()
        st["incomplete"] = True
        st["run_valid"] = False
        if LABEL_INCOMPLETE not in st["labels"]:
            st["labels"].append(LABEL_INCOMPLETE)
        if reason not in st["void_reasons"]:
            st["void_reasons"].append(reason)
        st["events"].append({"utc": now_utc(), "event": "incomplete", "reason": reason})
        self.save(st)

    def stamp(self, d: dict, timing: bool = False) -> dict:
        st = self.load()
        labels = list(st["labels"]) + (list(st["timing_labels"]) if timing else [])
        out = dict(d)
        out["run_valid"] = bool(st["run_valid"])
        out["run_labels"] = labels
        out["run_void_reasons"] = list(st["void_reasons"])
        return out


def write_row(out, name: str, row: dict, timing: bool = False) -> dict:
    r = RunState(out).stamp(row, timing)
    r["written_utc"] = now_utc()
    append_jsonl(Path(out) / "raw" / name, r)
    return r


def record_path(out, rid: str) -> Path:
    kind = "endpoint" if rid.startswith("E") else "control"
    cell = {"tag": TAG, "kind": kind, "id": rid}
    return Path(out) / "records" / (provenance.cell_slug(cell) + ".json")


def write_record(out, rid: str, values: dict, decision: str, inputs: list, notes: str = "",
                 rows: list | None = None) -> Path:
    kind = "endpoint" if rid.startswith("E") else "control"
    cell = {"tag": TAG, "kind": kind, "id": rid}
    vals = RunState(out).stamp(values, timing=rid in TIMING_RECORDS)
    path = record_path(out, rid)
    provenance.write_result(path, cell=cell, inputs=inputs, metric=METRICS[rid], values=clean(vals),
                            threshold=THRESHOLDS[rid], decision_rule=RULES[rid], decision=decision,
                            notes=notes, rows=clean(rows) if rows is not None else None)
    log(f"[record] {rid}: {decision} (run_valid={vals['run_valid']})")
    return path


def stamp_incomplete(out, reason: str) -> dict:
    """Mark the run incomplete and relabel every finished row and record."""
    out = Path(out)
    RunState(out).mark_incomplete(reason)
    counts = {"rows": 0, "records": 0, "unparseable_lines": 0}
    for p in sorted((out / "raw").glob("*.jsonl")):
        rows, bad = read_jsonl(p, strict=False)
        lines = []
        for r in rows:
            r["run_valid"] = False
            labels = list(r.get("run_labels") or [])
            if LABEL_INCOMPLETE not in labels:
                labels.append(LABEL_INCOMPLETE)
            r["run_labels"] = labels
            lines.append(json.dumps(clean(r), sort_keys=True, allow_nan=False))
            counts["rows"] += 1
        lines.extend(bad)  # a line cut off mid-write is kept verbatim; it cannot be stamped
        counts["unparseable_lines"] += len(bad)
        tmp = p.with_name(p.name + ".tmp")
        tmp.write_text("".join(x + "\n" for x in lines))
        os.replace(tmp, p)
    for p in sorted((out / "records").glob("*.json")):
        rec = load_json(p)
        vals = rec.setdefault("values", {})
        vals["run_valid"] = False
        labels = list(vals.get("run_labels") or [])
        if LABEL_INCOMPLETE not in labels:
            labels.append(LABEL_INCOMPLETE)
        vals["run_labels"] = labels
        p.write_text(json.dumps(clean(rec), indent=2, sort_keys=True))
        counts["records"] += 1
    log(f"[stop] run marked incomplete ({reason}); relabelled {counts}")
    return counts


def summary_path(out) -> Path:
    return Path(out) / SUMMARY_FILE


def _flat_values(vals: dict) -> dict:
    """Top-level scalars of a record's values, plus one-level dicts that hold only scalars."""
    skip = {"run_valid", "run_labels", "run_void_reasons"}
    scalar = (str, int, float, bool, type(None))
    out = {}
    for k, v in (vals or {}).items():
        if k in skip:
            continue
        if isinstance(v, scalar):
            out[k] = v
        elif isinstance(v, dict) and all(isinstance(x, scalar) for x in v.values()):
            out[k] = dict(v)
    return out


def write_summary(out) -> Path:
    """Restate run validity, labels and every record's decision in one small file.

    The launcher fetches this file first. It decides nothing. Every value is copied from
    RUN_VALID.json or from a record on disk; a record that does not exist is listed as missing.
    """
    out = Path(out)
    st = RunState(out).load()
    decisions, missing = {}, []
    for rid in ALL_IDS:
        p = record_path(out, rid)
        if not p.exists():
            missing.append(rid)
            continue
        try:
            rec = load_json(p)
        except (OSError, ValueError) as e:
            decisions[rid] = {"record": p.name, "unreadable": repr(e)}
            continue
        vals = rec.get("values") or {}
        decisions[rid] = {"record": p.name, "record_sha256": sha256_file(p), "metric": rec.get("metric"),
                          "decision": rec.get("decision"), "run_valid": vals.get("run_valid"),
                          "run_labels": vals.get("run_labels"), "values_restated": _flat_values(vals)}
    summ = {"tag": TAG, "written_utc": now_utc(),
            "what_this_is": ("a restatement of RUN_VALID.json and of the records under records/, for the "
                             "launcher's criticals-first fetch; it decides nothing, the records do"),
            "run_valid": bool(st.get("run_valid")), "incomplete": bool(st.get("incomplete")),
            "labels": list(st.get("labels") or []), "timing_labels": list(st.get("timing_labels") or []),
            "void_reasons": list(st.get("void_reasons") or []), "decisions": decisions,
            "records_present": len(decisions), "records_missing": missing}
    path = summary_path(out)
    dump_json(path, summ)
    log(f"[summary] wrote {path.name}: run_valid={summ['run_valid']}, {len(decisions)} records, "
        f"{len(missing)} missing")
    return path


# ----------------------------------------------------------------------------------------------
# Parser: R save files (.rda), XDR format version 2 or 3, standard library only.
# ----------------------------------------------------------------------------------------------
class RdaError(ValueError):
    pass


def _decompress(raw: bytes) -> bytes:
    if raw[:2] == b"\x1f\x8b":
        return gzip.decompress(raw)
    if raw[:3] == b"BZh":
        return bz2.decompress(raw)
    if raw[:6] == b"\xfd7zXZ\x00":
        return lzma.decompress(raw)
    return raw


def parse_rda_bytes(raw: bytes) -> dict:
    """Return {object name: R object}. An R object is a dict with type, values and attrs."""
    buf = _decompress(raw)
    if buf[:5] not in (b"RDX2\n", b"RDX3\n"):
        raise RdaError("not an R save file (missing RDX2/RDX3 header)")
    if buf[5:7] != b"X\n":
        raise RdaError("only the XDR (binary big-endian) save format is supported")
    pos = [7]
    refs: list = []

    def i32() -> int:
        if pos[0] + 4 > len(buf):
            raise RdaError("file ends inside an integer")
        v = struct.unpack_from(">i", buf, pos[0])[0]
        pos[0] += 4
        return v

    def length() -> int:
        n = i32()
        if n == -1:
            hi, lo = i32(), i32()
            n = (hi << 32) + lo
        if n < 0:
            raise RdaError("negative vector length")
        return n

    version = i32()
    i32()  # R version that wrote the file
    i32()  # minimal R version that can read it
    if version == 3:
        nelen = i32()
        pos[0] += nelen  # native encoding name
    elif version != 2:
        raise RdaError(f"unsupported serialization version {version}")

    def item():
        flags = i32()
        t = flags & 0xFF
        has_attr = bool(flags & (1 << 9))
        has_tag = bool(flags & (1 << 10))
        if t == 254:  # NULL
            return None
        if t in (241, 242, 250, 251, 252, 253):  # environments and markers we never need
            return {"type": "special", "code": t}
        if t == 255:  # reference to an earlier symbol
            idx = flags >> 8
            if idx == 0:
                idx = i32()
            return refs[idx - 1]
        if t == 1:  # symbol
            name = item()
            sym = {"type": "symbol", "name": name}
            refs.append(sym)
            return sym
        if t == 2:  # pairlist, read iteratively along its tail
            head = {"type": "pairlist", "items": []}
            while True:
                attr = item() if has_attr else None
                tag = item() if has_tag else None
                car = item()
                head["items"].append((tag["name"] if isinstance(tag, dict) else None, car, attr))
                nflags = struct.unpack_from(">i", buf, pos[0])[0]
                if (nflags & 0xFF) != 2:
                    tail = item()
                    if tail is not None:
                        raise RdaError("pairlist with a non-NULL tail is not supported")
                    return head
                pos[0] += 4
                has_attr = bool(nflags & (1 << 9))
                has_tag = bool(nflags & (1 << 10))
        if t == 9:  # character string
            n = i32()
            if n == -1:
                return None
            s = buf[pos[0]:pos[0] + n].decode("utf-8", "replace")
            pos[0] += n
            return s
        if t in (10, 13):
            n = length()
            vals = list(struct.unpack_from(f">{n}i", buf, pos[0]))
            pos[0] += 4 * n
            obj = {"type": "int" if t == 13 else "lgl", "values": vals}
        elif t == 14:
            n = length()
            vals = list(struct.unpack_from(f">{n}d", buf, pos[0]))
            pos[0] += 8 * n
            obj = {"type": "real", "values": vals}
        elif t == 16:
            n = length()
            obj = {"type": "str", "values": [item() for _ in range(n)]}
        elif t in (19, 20):
            n = length()
            obj = {"type": "list", "values": [item() for _ in range(n)]}
        else:
            raise RdaError(f"unsupported R object type {t}")
        obj["attrs"] = _pairlist_dict(item()) if has_attr else {}
        return obj

    top = item()
    if pos[0] != len(buf):
        raise RdaError(f"{len(buf) - pos[0]} trailing bytes after the saved objects")
    if not (isinstance(top, dict) and top.get("type") == "pairlist"):
        raise RdaError("top level is not a pairlist of named objects")
    return _pairlist_dict(top)


def _pairlist_dict(pl) -> dict:
    if pl is None:
        return {}
    if not (isinstance(pl, dict) and pl.get("type") == "pairlist"):
        raise RdaError("attributes are not a pairlist")
    return {name: val for name, val, _ in pl["items"]}


def load_basin(path: Path) -> dict:
    """Read BasinObs from the committed L0123001.rda into plain lists (NA becomes NaN)."""
    objs = parse_rda_bytes(Path(path).read_bytes())
    if "BasinObs" not in objs:
        raise RdaError("BasinObs not found in the save file")
    obs = objs["BasinObs"]
    if obs.get("type") != "list" or "data.frame" not in obs["attrs"].get("class", {}).get("values", []):
        raise RdaError("BasinObs is not a data frame")
    names = obs["attrs"]["names"]["values"]
    cols = dict(zip(names, obs["values"]))
    for need in ("DatesR", "P", "E", "Qmm"):
        if need not in cols:
            raise RdaError(f"column {need} missing")
    d = cols["DatesR"]
    if "POSIXct" not in d["attrs"].get("class", {}).get("values", []):
        raise RdaError("DatesR is not POSIXct")
    tz = (d["attrs"].get("tzone") or {}).get("values", [""])
    if tz[0] not in ("UTC", "GMT"):
        raise RdaError(f"DatesR time zone is {tz[0]!r}, expected UTC")
    secs = d["values"]
    epoch = dt.date(1970, 1, 1)
    dates = []
    for i, s in enumerate(secs):
        if not finite(s) or s % 86400 != 0:
            raise RdaError(f"date {i} is not a UTC midnight")
        dates.append((epoch + dt.timedelta(days=int(s // 86400))).isoformat())
    for i in range(1, len(dates)):
        if (dt.date.fromisoformat(dates[i]) - dt.date.fromisoformat(dates[i - 1])).days != 1:
            raise RdaError(f"dates are not consecutive days at row {i}")
    P = [float(x) for x in cols["P"]["values"]]
    E = [float(x) for x in cols["E"]["values"]]
    Q = [float(x) for x in cols["Qmm"]["values"]]
    if not (len(dates) == len(P) == len(E) == len(Q)):
        raise RdaError("columns have different lengths")
    info = objs.get("BasinInfo")
    area = None
    if info and info.get("type") == "list":
        inames = info["attrs"]["names"]["values"]
        ivals = dict(zip(inames, info["values"]))
        if "BasinArea" in ivals:
            area = ivals["BasinArea"]["values"][0]
    return {"dates": dates, "P": P, "E": E, "Qmm": Q, "basin_area_km2": area, "n_rows": len(dates)}


def pyreadr_crosscheck(path: Path, basin: dict) -> dict:
    """Read the same file with pyreadr (installed on the box) and compare it with the reader above.

    Rain, evaporation and observed flow must agree exactly; a mismatch stops the run.
    Dates are compared too but only reported, since pyreadr's time-zone handling may differ.
    """
    try:
        import pyreadr
    except Exception as e:  # noqa: BLE001
        return {"ran": False, "reason": f"pyreadr not importable: {e!r}"}
    try:
        df = pyreadr.read_r(str(path))["BasinObs"]
        P = [float(x) for x in df["P"]]
        E = [float(x) for x in df["E"]]
        Q = [float(x) for x in df["Qmm"]]
        dates = [str(x)[:10] for x in df["DatesR"]]
    except Exception as e:  # noqa: BLE001
        return {"ran": False, "reason": f"pyreadr could not read the file: {e!r}"}
    same_q = len(Q) == len(basin["Qmm"]) and all(
        (math.isnan(a) and math.isnan(b)) or a == b for a, b in zip(Q, basin["Qmm"]))
    return {"ran": True, "pyreadr_version": getattr(pyreadr, "__version__", None),
            "values_agree": P == basin["P"] and E == basin["E"] and same_q, "dates_agree": dates == basin["dates"]}


# ----------------------------------------------------------------------------------------------
# Parser: airGR source files read straight out of the committed tarball (never executed).
# ----------------------------------------------------------------------------------------------
def read_members(tar_path: Path, names) -> dict:
    want, got = set(names), {}
    with tarfile.open(tar_path, "r:gz") as tf:
        for m in tf:
            if m.name in want and m.isfile():
                got[m.name] = tf.extractfile(m).read().decode("utf-8")
    missing = want - set(got)
    if missing:
        raise ValueError(f"tarball members missing: {sorted(missing)}")
    return got


def verify_source_constants(members: dict) -> list:
    """Return the GR4J constants this file hardcodes that are NOT found verbatim in the source."""
    return [f"{m}: {s!r}" for m, s in SOURCE_CHECKS if s not in members.get(m, "")]


_NUM = r"([-+]?\d+(?:\.\d+)?)"


def parse_transfo_ranges(transfo_text: str, calib_text: str) -> dict:
    """Parameter ranges as airGR defines them.

    CreateCalibOptions.R bounds every transformed parameter to [lo, hi] (airGR uses -9.99..9.99).
    TransfoParam_GR4J.R maps a transformed value T to the model parameter ("TR" direction).
    Range of Xk = [TR_k(lo), TR_k(hi)]; every map in the file is increasing.
    """
    m = re.search(r"ParamT\s*<-\s*matrix\(c\(rep\(" + _NUM + r",\s*NParam\),\s*rep\(" + _NUM + r",\s*NParam\)\)",
                  calib_text)
    if not m:
        raise ValueError("transformed-space bounds not found in CreateCalibOptions.R")
    lo, hi = float(m.group(1)), float(m.group(2))
    if not lo < hi:
        raise ValueError("transformed-space bounds are not increasing")
    block = re.search(r'if \(Direction == "TR"\) \{(.*?)\n  \}', transfo_text, re.S)
    if not block:
        raise ValueError("TR block not found in TransfoParam_GR4J.R")
    maps = {}
    for line in block.group(1).splitlines():
        line = line.split("###")[0].strip()
        mm = re.match(r"ParamOut\[, *(\d)\] *<- *(.+)$", line)
        if not mm:
            continue
        k, expr = int(mm.group(1)), mm.group(2).strip()
        e = re.match(r"^(exp|sinh)\(ParamIn\[, *(\d)\]\)$", expr)
        a = re.match(r"^" + _NUM + r" *\+ *" + _NUM + r" *\* *\(ParamIn\[, *(\d)\] *- *" + _NUM + r"\) */ *"
                     + _NUM + r"$", expr)
        if e and int(e.group(2)) == k:
            fn = math.exp if e.group(1) == "exp" else math.sinh
            maps[k] = (e.group(1), fn, None)
        elif a and int(a.group(3)) == k:
            A, Bv, C, Dv = float(a.group(1)), float(a.group(2)), float(a.group(4)), float(a.group(5))
            maps[k] = ("affine", (lambda T, A=A, Bv=Bv, C=C, Dv=Dv: A + Bv * (T - C) / Dv), (A, Bv, C, Dv))
        else:
            raise ValueError(f"unsupported transformation for parameter {k}: {expr!r}")
    if sorted(maps) != [1, 2, 3, 4]:
        raise ValueError(f"expected four parameter maps, found {sorted(maps)}")
    for k, (kind, _fn, consts) in maps.items():
        if kind == "affine" and (abs(consts[2] - hi) > 1e-12 or abs(consts[3] - (hi - lo)) > 1e-12):
            raise ValueError("the affine map's constants disagree with the calibration bounds")
    ranges = {}
    for k in (1, 2, 3, 4):
        kind, fn, _ = maps[k]
        a_, b_ = fn(lo), fn(hi)
        if not a_ < b_:
            raise ValueError(f"map for X{k} is not increasing")
        ranges[f"X{k}"] = [a_, b_]
    return {"ranges": ranges, "transformed_bounds": [lo, hi],
            "maps": {f"X{k}": maps[k][0] for k in maps}}


def draw_params(ranges: dict, n: int, seed: int) -> list:
    """Uniform draws within each parameter's range, in parameter units; one fixed seed."""
    rng = random.Random(seed)
    keys = ("X1", "X2", "X3", "X4")
    return [[ranges[k][0] + (ranges[k][1] - ranges[k][0]) * rng.random() for k in keys] for _ in range(n)]


def check_params(params: list, ranges: dict) -> None:
    if len({tuple(p) for p in params}) != len(params):
        raise Halt("DEGENERATE_PARAMS", "parameter vectors are not all distinct")
    keys = ("X1", "X2", "X3", "X4")
    for p in params:
        for k, v in zip(keys, p):
            if not (ranges[k][0] <= v <= ranges[k][1]):
                raise Halt("DEGENERATE_PARAMS", f"{k}={v} lies outside its range {ranges[k]}")


# ----------------------------------------------------------------------------------------------
# Parsers: install status, nvidia-smi, environment money values, airGR output JSON.
# ----------------------------------------------------------------------------------------------
def parse_install_status(text: str) -> dict:
    kv = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"install status line without '=': {line!r}")
        k, v = line.split("=", 1)
        kv[k.strip()] = v.strip()
    if "apt_rc" not in kv or "rcmd_rc" not in kv:
        raise ValueError("install status needs apt_rc and rcmd_rc")
    return {"apt_rc": kv["apt_rc"], "rcmd_rc": kv["rcmd_rc"], "r_libs_user": kv.get("r_libs_user"),
            "ok": kv["apt_rc"] == "0" and kv["rcmd_rc"] == "0"}


def install_error_text(out, status: dict | None, tail_lines: int = 25) -> str:
    parts = []
    if status is None:
        parts.append("install status file missing: the R install step did not run")
    else:
        parts.append(f"apt-get exit code {status['apt_rc']}; R CMD INSTALL exit code {status['rcmd_rc']}")
    for name in ("apt_r.log", "r_cmd_install.log"):
        p = Path(out) / "logs" / name
        if p.exists():
            tail = p.read_text(errors="replace").splitlines()[-tail_lines:]
            parts.append(f"--- last lines of {name} ---\n" + "\n".join(tail))
    return "\n".join(parts)


def parse_nvidia_smi_csv(text: str) -> list:
    gpus = []
    for line in text.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError(f"unexpected nvidia-smi line: {line!r}")
        gpus.append({"name": parts[0], "driver_version": parts[1]})
    if not gpus:
        raise ValueError("nvidia-smi listed no GPU")
    return gpus


def parse_money(name: str, environ) -> float:
    v = environ.get(name)
    if v is None or not str(v).strip():
        raise ValueError(f"{name} is not set")
    try:
        x = float(str(v).strip())
    except ValueError:
        raise ValueError(f"{name}={v!r} is not a number") from None
    if not math.isfinite(x) or x <= 0:
        raise ValueError(f"{name}={v!r} must be a positive number")
    return x


def parse_airgr_json(text: str) -> dict:
    d = json.loads(text)
    for k in ("r_version", "airgr_version", "cases"):
        if k not in d:
            raise ValueError(f"airGR output lacks {k}")
    by = {}
    for c in d["cases"]:
        by[c.get("id")] = c
    for exp in AIRGR_CASES:
        c = by.get(exp["id"])
        if c is None:
            raise ValueError(f"airGR output lacks case {exp['id']}")
        if len(c.get("X", [])) != 4 or any(abs(a - b) > 1e-9 for a, b in zip(c["X"], exp["X"])):
            raise ValueError(f"case {exp['id']}: parameters {c.get('X')} differ from {exp['X']}")
        n = len(c.get("dates", []))
        if n == 0 or n != len(c.get("qsim", [])) or n != len(c.get("qobs", [])):
            raise ValueError(f"case {exp['id']}: dates, qsim and qobs lengths differ or are zero")
        if c["dates"][0] != exp["period"][0] or c["dates"][-1] != exp["period"][1]:
            raise ValueError(f"case {exp['id']}: period {c['dates'][0]}..{c['dates'][-1]} is not {exp['period']}")
        if c.get("nse") is not None and not finite(c["nse"]):
            raise ValueError(f"case {exp['id']}: NSE is not a number")
        for q in c["qsim"]:
            if q is not None and not finite(q):
                raise ValueError(f"case {exp['id']}: qsim holds a non-number")
    d["by_id"] = by
    return d


# ----------------------------------------------------------------------------------------------
# Package versions. The image's JAX is used as is; installing pyreadr must not change it.
# ----------------------------------------------------------------------------------------------
def dist_version(name: str):
    """Version from installed package metadata, without importing the package."""
    try:
        from importlib import metadata
        return metadata.version(name)
    except Exception:  # noqa: BLE001
        return None


def jaxlib_version(mod=None) -> tuple:
    """(version, where it was read). jaxlib keeps its version string in the jaxlib.version module."""
    if mod is None:
        try:
            import jaxlib as mod
        except Exception as e:  # noqa: BLE001
            return None, f"jaxlib not importable: {e!r}"
        try:
            import importlib
            importlib.import_module("jaxlib.version")
        except Exception:  # noqa: BLE001
            pass
    v = getattr(mod, "__version__", None)
    if isinstance(v, str) and v:
        return v, "jaxlib.__version__"
    v = getattr(getattr(mod, "version", None), "__version__", None)
    if isinstance(v, str) and v:
        return v, "jaxlib.version.__version__"
    d = dist_version("jaxlib")
    if d:
        return d, "installed package metadata"
    return None, "no version attribute found"


def package_versions() -> dict:
    """Module version and installed-metadata version of each listed package. Never raises."""
    import importlib
    vers = {}
    for name in VERSION_PACKAGES:
        e = {"module_version": None, "module_version_source": None, "dist_version": dist_version(name),
             "file": None, "import_error": None}
        if name in IMPORTED_PACKAGES:
            try:
                m = importlib.import_module(name)
                e["file"] = getattr(m, "__file__", None)
                if name == "jaxlib":
                    e["module_version"], e["module_version_source"] = jaxlib_version()
                else:
                    e["module_version"] = getattr(m, "__version__", None)
                    e["module_version_source"] = f"{name}.__version__"
            except Exception as ex:  # noqa: BLE001
                e["import_error"] = repr(ex)
        vers[name] = e
    return vers


def _one_version(entry):
    if not isinstance(entry, dict):
        return None
    return entry.get("module_version") or entry.get("dist_version")


def pinned_versions_changed(before: dict, after: dict) -> list:
    """Which of jax, jaxlib and numpy read a different version after the install than before it."""
    changed = []
    for name in PINNED_PACKAGES:
        a, b = _one_version(before.get(name)), _one_version(after.get(name))
        if a != b:
            changed.append(f"{name}: {a} -> {b}")
    return changed


# ----------------------------------------------------------------------------------------------
# Periods, warm-up and forcing rules.
# ----------------------------------------------------------------------------------------------
def default_warmup_start(dates: list, i_run0: int) -> int:
    """Index of the first warm-up day, as CreateRunOptions sets it by default.

    Up to one year before the run start: 365 days back, one more if the day of month shifts
    (a leap day in between). No warm-up when the run starts on the first day.
    """
    if i_run0 == 0:
        return 0
    d0 = dt.date.fromisoformat(dates[i_run0])
    tmp = d0 - dt.timedelta(days=365)
    if tmp.day != d0.day:
        tmp -= dt.timedelta(days=1)
    first = max(dt.date.fromisoformat(dates[0]), tmp)
    return dates.index(first.isoformat())


def case_window(dates: list, case: dict):
    i0 = dates.index(case["period"][0])
    i1 = dates.index(case["period"][1])
    return i0, i1, default_warmup_start(dates, i0)


def forcing_window(series: list, offset: int, n_days: int) -> list:
    """Committed tiling rule: day t of every chain reads series[(offset + t) mod N]."""
    n = len(series)
    return [series[(offset + t) % n] for t in range(n_days)]


def check_forcing_windows(basin: dict) -> None:
    wins = {tuple(forcing_window(basin["P"], s, N_DAYS)) for s in SEEDS}
    if len(wins) != len(SEEDS):
        raise Halt("DEGENERATE_FORCING", "different seeds give identical forcing windows")


# ----------------------------------------------------------------------------------------------
# GR4J, one day step, written once for two back ends: plain floats and JAX arrays.
# Follows airGR 1.7.9 frun_GR4J.f90 (MOD_GR4J) and utils_D.f90 (UH1, UH2, SS1, SS2).
# ----------------------------------------------------------------------------------------------
class ScalarOps:
    """Plain Python floats; branches are evaluated lazily, like the Fortran IF blocks."""

    @staticmethod
    def select(c, f, g):
        return f() if c else g()

    @staticmethod
    def select_tuple(c, f, g):
        return f() if c else g()

    minimum = staticmethod(min)
    maximum = staticmethod(max)
    exp = staticmethod(math.exp)
    sqrt = staticmethod(math.sqrt)

    @staticmethod
    def head(u):
        return u[0]

    @staticmethod
    def uh_shift(u, ords, inflow):
        n = len(u)
        return [u[k + 1] + ords[k] * inflow for k in range(n - 1)] + [ords[n - 1] * inflow]

    def uh_ordinates(self, X4):
        s1 = [ss1(i, X4, self) for i in range(NH + 1)]
        s2 = [ss2(i, X4, self) for i in range(2 * NH + 1)]
        return ([s1[k] - s1[k - 1] for k in range(1, NH + 1)],
                [s2[k] - s2[k - 1] for k in range(1, 2 * NH + 1)])

    @staticmethod
    def zeros(n_uh: int, like=None):
        return [0.0] * n_uh


class ArrayOps:
    """JAX arrays, chains on the leading axis; both branches are computed, then selected."""

    def __init__(self, jnp):
        self.jnp = jnp

    def select(self, c, f, g):
        return self.jnp.where(c, f(), g())

    def select_tuple(self, c, f, g):
        a, b = f(), g()
        return tuple(self.jnp.where(c, x, y) for x, y in zip(a, b))

    def minimum(self, a, b):
        return self.jnp.minimum(a, b)

    def maximum(self, a, b):
        return self.jnp.maximum(a, b)

    def exp(self, x):
        return self.jnp.exp(x)

    def sqrt(self, x):
        return self.jnp.sqrt(x)

    @staticmethod
    def head(u):
        return u[:, 0]

    def uh_shift(self, u, ords, inflow):
        jnp = self.jnp
        shifted = jnp.concatenate([u[:, 1:], jnp.zeros_like(u[:, :1])], axis=1)
        return shifted + ords * inflow[:, None]

    def uh_ordinates(self, X4):
        jnp = self.jnp
        c = X4[:, None]
        i1 = jnp.arange(NH + 1, dtype=X4.dtype)[None, :]
        i2 = jnp.arange(2 * NH + 1, dtype=X4.dtype)[None, :]
        s1 = ss1(i1, c, self)
        s2 = ss2(i2, c, self)
        return s1[:, 1:] - s1[:, :-1], s2[:, 1:] - s2[:, :-1]


SCALAR = ScalarOps()


def ss1(i, C, ops):
    """S-curve of unit hydrograph 1 (utils_D.f90 SS1)."""
    return ops.select(i <= 0, lambda: 0.0,
                      lambda: ops.select(i < C, lambda: (i / C) ** D_EXP, lambda: 1.0))


def ss2(i, C, ops):
    """S-curve of unit hydrograph 2 (utils_D.f90 SS2)."""
    return ops.select(
        i <= 0, lambda: 0.0,
        lambda: ops.select(
            i <= C, lambda: 0.5 * (i / C) ** D_EXP,
            lambda: ops.select(i < 2.0 * C, lambda: 1.0 - 0.5 * (2.0 - i / C) ** D_EXP, lambda: 1.0)))


def prepare_params(X1, X2, X3, X4, ops):
    """RunModel_GR4J.R clamps, then CreateRunOptions.R default store levels."""
    X1 = ops.maximum(X1, X1X3_MIN)
    X3 = ops.maximum(X3, X1X3_MIN)
    X4 = ops.maximum(X4, X4_MIN)
    return X1, X2, X3, X4, INI_PROD * X1, INI_ROUT * X3


def gr4j_step(ops, state, p, e, X1, X2, X3, ord1, ord2):
    """One day of MOD_GR4J. state = (production store, routing store, UH1 states, UH2 states)."""
    S, R, U1, U2 = state
    is_dry = p <= e

    def dry():  # IF (P1 <= E): net evaporation draws on the production store
        en = e - p
        ws = ops.minimum(en / X1, WS_MAX)
        ew = ops.exp(2.0 * ws)
        tws = (ew - 1.0) / (ew + 1.0)
        sr = S / X1
        er = S * (2.0 - sr) * tws / (1.0 + (1.0 - sr) * tws)
        zero = 0.0 * p
        return S - er, zero, zero, zero, er + p          # S, PN, PS, PR, AE

    def wet():  # ELSE: net rainfall partly fills the production store
        pn = p - e
        ws = ops.minimum(pn / X1, WS_MAX)
        ew = ops.exp(2.0 * ws)
        tws = (ew - 1.0) / (ew + 1.0)
        sr = S / X1
        ps = X1 * (1.0 - sr * sr) * tws / (1.0 + sr * tws)
        return S + ps, pn, ps, pn - ps, e + 0.0 * p

    S, PN, PS, PR, AE = ops.select_tuple(is_dry, dry, wet)
    S = ops.maximum(S, 0.0)
    sr = S / X1
    sr = sr * sr
    sr = sr * sr
    perc = S * (1.0 - 1.0 / ops.sqrt(ops.sqrt(1.0 + sr / PERC_CONST)))
    S = S - perc
    PR = PR + perc
    U1 = ops.uh_shift(U1, ord1, PR * B_SPLIT)
    U2 = ops.uh_shift(U2, ord2, PR * (1.0 - B_SPLIT))
    q9, q1 = ops.head(U1), ops.head(U2)
    rr = R / X3
    exch = X2 * rr * rr * rr * ops.sqrt(rr)
    aexch1 = ops.select(R + q9 + exch < 0.0, lambda: -R - q9, lambda: exch)
    R = ops.maximum(R + q9 + exch, 0.0)
    rr = R / X3
    rr = rr * rr
    rr = rr * rr
    qr = R * (1.0 - 1.0 / ops.sqrt(ops.sqrt(1.0 + rr)))
    R = R - qr
    aexch2 = ops.select(q1 + exch < 0.0, lambda: -q1, lambda: exch)
    qd = ops.maximum(0.0, q1 + exch)
    q = ops.maximum(qr + qd, 0.0)
    out = {"Q": q, "QR": qr, "QD": qd, "PN": PN, "PS": PS, "PR": PR, "PERC": perc, "AE": AE,
           "EXCH": exch, "AEXCH1": aexch1, "AEXCH2": aexch2, "Q9": q9, "Q1": q1}
    return (S, R, U1, U2), out


def run_scalar(X, P, E, init=None):
    """Plain-float GR4J over a series. init=(production, routing) overrides the default levels."""
    X1, X2, X3, X4, S0, R0 = prepare_params(*X, SCALAR)
    ord1, ord2 = SCALAR.uh_ordinates(X4)
    if init is not None:
        S0, R0 = init
    state = (S0, R0, [0.0] * NH, [0.0] * (2 * NH))
    outs = []
    for p, e in zip(P, E):
        state, o = gr4j_step(SCALAR, state, p, e, X1, X2, X3, ord1, ord2)
        o = dict(o)
        o["S"], o["R"] = state[0], state[1]
        o["UH_store"] = sum(state[2][1:]) + sum(state[3][1:])  # element 0 has already left the UH
        outs.append(o)
    return outs, (S0, R0)


def make_forward(jnp, lax):
    """Batched GR4J forward pass: params (chains, 4), P and E (days, chains) -> Q (days, chains)."""
    ops = ArrayOps(jnp)

    def forward(params, P, E):
        X1, X2, X3, X4, S0, R0 = prepare_params(params[:, 0], params[:, 1], params[:, 2], params[:, 3], ops)
        ord1, ord2 = ops.uh_ordinates(X4)
        n = params.shape[0]
        U1 = jnp.zeros((n, NH), dtype=params.dtype)
        U2 = jnp.zeros((n, 2 * NH), dtype=params.dtype)

        def body(state, pe):
            new_state, out = gr4j_step(ops, state, pe[0], pe[1], X1, X2, X3, ord1, ord2)
            return new_state, out["Q"]

        _, Q = lax.scan(body, (S0, R0, U1, U2), (P, E))
        return Q

    return forward


# ----------------------------------------------------------------------------------------------
# Scores: NSE as airGR's ErrorCrit_NSE computes it; mean absolute relative error of flow.
# ----------------------------------------------------------------------------------------------
def nse(sim: list, obs: list):
    """airGR ErrorCrit_NSE on untransformed flow: days with a non-finite value are ignored."""
    pairs = [(s, o) for s, o in zip(sim, obs) if finite(s) and finite(o)]
    if not pairs:
        return None
    m = sum(o for _, o in pairs) / len(pairs)
    emod = sum((s - o) ** 2 for s, o in pairs)
    eref = sum((o - m) ** 2 for _, o in pairs)
    if emod == 0 and eref == 0:
        return 0.0
    if eref == 0:
        return None
    c = 1.0 - emod / eref
    return c if math.isfinite(c) else None


def mare(sim: list, ref: list):
    """Mean |sim - ref| / ref over days where ref > 0. Returns (value, days excluded)."""
    used, total, excluded = 0, 0.0, 0
    for s, r in zip(sim, ref):
        if not (finite(r) and r > 0):
            excluded += 1
            continue
        if not finite(s):
            return math.inf, excluded
        total += abs(s - r) / r
        used += 1
    if len(sim) != len(ref):
        return math.inf, excluded
    return (total / used if used else None), excluded


def in_band(x, center: float, tol: float) -> bool:
    return finite(x) and abs(x - center) <= tol + 1e-12


def spread(xs: list):
    xs = sorted(x for x in xs if finite(x))
    if not xs:
        return None
    q = statistics.quantiles(xs, n=4, method="inclusive") if len(xs) >= 2 else [xs[0]] * 3
    return {"n": len(xs), "median": statistics.median(xs), "min": xs[0], "q1": q[0], "q3": q[2], "max": xs[-1]}


def main_run_hours(ms: float, overhead: float) -> float:
    return ITERATIONS_MAIN * ms / 1000.0 / 3600.0 * overhead


def card_decision(main_h: float, speedup: float) -> str:
    return "if_not" if (main_h >= E5_HOURS_MIN or speedup < E5_SPEEDUP_MIN) else "if_lever"


def gate_decision(main_h: float) -> str:
    return "pass" if main_h <= E6_GATE_HOURS else GATE_STOP_TEXT


def guess_band(x: float, band) -> str:
    return "HOLDS" if band[0] <= x <= band[1] else "REFUTED"


def chain_steps_per_s(n_chains: int, ms: float, n_days: int = N_DAYS) -> float:
    return n_chains * n_days / (ms / 1000.0)


def scaling_label(ratio: float) -> str:
    lo, hi = E7_TARGET_RATIO * (1 - E7_TOL), E7_TARGET_RATIO * (1 + E7_TOL)
    if lo <= ratio <= hi:
        return "linear"
    if ratio < lo:
        return "GPU saturates below 2,684 chains"
    return "above linear"


# ----------------------------------------------------------------------------------------------
# Degenerate-output detectors.
# ----------------------------------------------------------------------------------------------
def check_timing_cell(rows: list, what: str) -> None:
    ms = [r.get("ms") for r in rows]
    bad = [m for m in ms if not (finite(m) and m > 0)]
    if bad:
        raise Halt("DEGENERATE_TIMING", f"{what}: {len(bad)} pass times are missing, non-finite or not positive")
    if len(ms) >= 2 and max(ms) == min(ms):
        raise Halt("WRONG_VARIANCE_SOURCE",
                   f"{what}: all {len(ms)} timed passes read exactly {ms[0]} ms; zero spread means the timer "
                   "is not timing the passes")


def check_probe_seed(rows: list, what: str) -> None:
    blocks = [r for r in rows if not r.get("warmup")]
    if not blocks:
        raise Halt("DEGENERATE_PROBE", f"{what}: no timed probe blocks")
    for r in blocks:
        if not (isinstance(r.get("iterations"), int) and r["iterations"] > 0 and finite(r.get("ms"))
                and r["ms"] > 0):
            raise Halt("DEGENERATE_PROBE", f"{what}: a probe block has no iterations or no positive time")
    if len(blocks) >= 2 and len({r["ms"] for r in blocks}) == 1:
        raise Halt("WRONG_VARIANCE_SOURCE", f"{what}: every probe block reads exactly {blocks[0]['ms']} ms")


def flow_flags(q: list) -> dict:
    nonfinite = sum(1 for x in q if not finite(x))
    all_zero = bool(q) and all(finite(x) and x == 0 for x in q)
    return {"nonfinite_days": nonfinite, "all_zero_flow": all_zero}


# ----------------------------------------------------------------------------------------------
# Planted model rows (standard library; float64): checked in the selftest and inside the I2 record.
# ----------------------------------------------------------------------------------------------
def planted_year():
    P = [20.0 if t % 9 == 0 else (4.0 if t % 4 == 1 else 0.0) for t in range(365)]
    E = [1.5 + 1.0 * math.sin(2 * math.pi * t / 365.0) for t in range(365)]
    return P, E


def planted_model_checks() -> dict:
    res = {}
    worst = 0.0
    for x4 in (0.5, 1.0, 2.45, 7.3, 13.0, 19.99, 20.0):
        o1, o2 = SCALAR.uh_ordinates(x4)
        worst = max(worst, abs(sum(o1) - 1.0), abs(sum(o2) - 1.0))
    res["uh_sum_max_abs_error"] = worst
    res["uh_sum_pass"] = worst <= 1e-9
    zeros, twos = [0.0] * 365, [2.0] * 365
    outs, _ = run_scalar(ANCHOR_X, zeros, twos, init=(0.0, 0.0))
    outs_d, _ = run_scalar(ANCHOR_X, zeros, twos)
    res["zero_rain_max_quickflow_empty_stores"] = max(abs(o["QD"]) for o in outs)
    res["zero_rain_max_total_flow_empty_stores"] = max(abs(o["Q"]) for o in outs)
    res["zero_rain_max_net_rain_default_stores"] = max(abs(o["PN"]) + abs(o["PS"]) for o in outs_d)
    res["zero_rain_pass"] = (res["zero_rain_max_quickflow_empty_stores"] == 0.0
                             and res["zero_rain_max_total_flow_empty_stores"] == 0.0
                             and res["zero_rain_max_net_rain_default_stores"] == 0.0)
    P, E = planted_year()
    outs, (S0, R0) = run_scalar(ANCHOR_X, P, E)
    store0 = S0 + R0
    end = outs[-1]
    store1 = end["S"] + end["R"] + end["UH_store"]
    flux = sum(P) - sum(o["AE"] for o in outs) - sum(o["Q"] for o in outs) \
        + sum(o["AEXCH1"] + o["AEXCH2"] for o in outs)
    res["mass_balance_residual_mm"] = flux - (store1 - store0)
    res["mass_balance_pass"] = abs(res["mass_balance_residual_mm"]) <= 1e-6
    res["all_pass"] = res["uh_sum_pass"] and res["zero_rain_pass"] and res["mass_balance_pass"]
    return res


# ----------------------------------------------------------------------------------------------
# Cost and time guard.
# ----------------------------------------------------------------------------------------------
def projected_usd(uptime_s: float, next_s: float, price: float) -> float:
    return ((uptime_s + next_s) / 3600.0 + FETCH_MARGIN_H) * price


def guard_verdict(uptime_s, budget_next_s, price, budget, now_s, deadline_s, time_next_s):
    proj = projected_usd(uptime_s, budget_next_s, price)
    if proj >= budget:
        return False, f"projected spend USD {proj:.3f} reaches the budget USD {budget:.3f}"
    if deadline_s is not None and now_s + time_next_s > deadline_s:
        return False, (f"time cap: the next step needs about {time_next_s:.0f} s but "
                       f"{max(0.0, deadline_s - now_s):.0f} s are left")
    return True, f"projected spend USD {proj:.3f} is below the budget USD {budget:.3f}"


def box_uptime_s():
    try:
        return float(Path("/proc/uptime").read_text().split()[0])
    except (OSError, ValueError, IndexError):
        return None


class Guard:
    def __init__(self, environ=None):
        env = os.environ if environ is None else environ
        self.price = parse_money("PRICE_USD_PER_HOUR", env)
        self.budget = parse_money("BUDGET_LEFT_USD", env)
        d = env.get("M1_DEADLINE_EPOCH")
        self.deadline = float(d) if d not in (None, "") else None
        self.t0 = time.time()

    def uptime_s(self) -> float:
        u = box_uptime_s()
        return u if u is not None else time.time() - self.t0

    def check(self, next_s: float) -> None:
        ok, why = guard_verdict(self.uptime_s(), next_s, self.price, self.budget, time.time(), self.deadline,
                                next_s)
        if not ok:
            raise StopRun(why)


# ----------------------------------------------------------------------------------------------
# The R script for the airGR anchor. run_m1.py writes it; Rscript runs it on the box.
# ----------------------------------------------------------------------------------------------
R_SCRIPT = r'''# Anchor arm for measurement m1, written by run_m1.py. Do not edit by hand.
# Usage: Rscript anchor_airgr.R <path to L0123001.rda> <output json path>
# Runs airGR's own GR4J (installed on this box from the committed tarball) on three cases.
# Warm-up and initial states are the CreateRunOptions defaults. NSE is ErrorCrit_NSE on Qmm.
args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 2L) stop("usage: Rscript anchor_airgr.R <rda> <out.json>")
suppressPackageStartupMessages(library(airGR))
load(args[1L])
jnum <- function(x) {
  s <- ifelse(is.finite(x), sprintf("%.17g", x), "null")
  paste0("[", paste(s, collapse = ","), "]")
}
jone <- function(x) if (length(x) == 1L && is.finite(x)) sprintf("%.17g", x) else "null"
jstr <- function(x) paste0("\"", gsub("[\"\\\\]", "_", x), "\"")
jstrs <- function(x) paste0("[", paste(vapply(x, jstr, character(1)), collapse = ","), "]")
day_index <- function(ddmmyyyy) {
  which(format(BasinObs$DatesR, format = "%d/%m/%Y %H:%M") == paste(ddmmyyyy, "00:00"))
}
InputsModel <- CreateInputsModel(FUN_MOD = RunModel_GR4J, DatesR = BasinObs$DatesR,
                                 Precip = BasinObs$P, PotEvap = BasinObs$E)
cases <- list(
  list(id = "anchor_cal", set = "anchor", X = c(165.05, 6.46, 422.50, 2.45),
       from = "01/01/1990", to = "28/02/1990"),
  list(id = "generalist_cal", set = "generalist", X = c(291, 0.30, 109.10, 2.01),
       from = "01/01/1990", to = "28/02/1990"),
  list(id = "michel_val", set = "michel", X = c(165.05, 6.46, 422.50, 2.45),
       from = "01/03/1990", to = "31/12/1999")
)
parts <- character(0)
for (cs in cases) {
  Ind <- seq(day_index(cs$from), day_index(cs$to))
  RunOptions <- CreateRunOptions(FUN_MOD = RunModel_GR4J, InputsModel = InputsModel,
                                 IndPeriod_Run = Ind)
  InputsCrit <- CreateInputsCrit(FUN_CRIT = ErrorCrit_NSE, InputsModel = InputsModel,
                                 RunOptions = RunOptions, Obs = BasinObs$Qmm[Ind])
  OutputsModel <- RunModel_GR4J(InputsModel = InputsModel, RunOptions = RunOptions, Param = cs$X)
  OutputsCrit <- ErrorCrit_NSE(InputsCrit = InputsCrit, OutputsModel = OutputsModel, verbose = FALSE)
  wu <- RunOptions$IndPeriod_WarmUp
  wu_n <- if (identical(wu, 0L)) 0L else length(wu)
  wu_first <- if (wu_n == 0L) "none" else format(BasinObs$DatesR[wu[1L]], "%Y-%m-%d")
  parts <- c(parts, paste0(
    "{\"id\":", jstr(cs$id), ",\"set\":", jstr(cs$set), ",\"X\":", jnum(cs$X),
    ",\"warmup_n\":", wu_n, ",\"warmup_first\":", jstr(wu_first),
    ",\"ini_res_levels\":", jnum(RunOptions$IniResLevels),
    ",\"nse\":", jone(OutputsCrit$CritValue),
    ",\"crit_name\":", jstr(OutputsCrit$CritName),
    ",\"dates\":", jstrs(format(OutputsModel$DatesR, "%Y-%m-%d")),
    ",\"qsim\":", jnum(OutputsModel$Qsim),
    ",\"qobs\":", jnum(BasinObs$Qmm[Ind]), "}"))
}
writeLines(paste0("{\"r_version\":", jstr(R.version.string),
                  ",\"airgr_version\":", jstr(as.character(packageVersion("airGR"))),
                  ",\"cases\":[", paste(parts, collapse = ","), "]}"), args[2L])
cat("anchor_airgr: wrote", args[2L], "\n")
'''


# ----------------------------------------------------------------------------------------------
# Paths inside the output folder.
# ----------------------------------------------------------------------------------------------
def paths(out) -> dict:
    out = Path(out)
    return {
        "basin": out / "extract" / "basin.json",
        "ranges": out / "extract" / "param_ranges.json",
        "params": out / "extract" / "params_distinct.json",
        "rscript": out / "extract" / "anchor_airgr.R",
        "rules": out / "decision_rules.json",
        "install_status": out / "airgr_install_status.txt",
        "airgr_output": out / "raw" / "airgr_output.json",
        "anchor_rows": out / "raw" / "anchor_rows.jsonl",
        "anchor_daily": out / "raw" / "anchor_daily.jsonl",
        "timer_rows": out / "raw" / "timer_rows.jsonl",
        "timing_rows": out / "raw" / "timing_rows.jsonl",
        "probe_blocks": out / "raw" / "probe_blocks.jsonl",
        "hardware": out / "hardware_labels.json",
    }


def inp(path, n_items=None) -> dict:
    return provenance.describe_input(path, n_items)


def inp_rows(path) -> dict:
    p = Path(path)
    n = len(read_jsonl(p, strict=False)[0]) if p.exists() else None
    return provenance.describe_input(p, n)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_basin_extract(out) -> dict:
    b = load_json(paths(out)["basin"])
    b["Qmm"] = [math.nan if v is None else v for v in b["Qmm"]]
    return b


# ----------------------------------------------------------------------------------------------
# Stage: extract.
# ----------------------------------------------------------------------------------------------
def stage_extract(out) -> None:
    out = Path(out)
    pt = paths(out)
    RunState(out).ensure()
    dump_json(pt["rules"], {"tag": TAG, "written_utc": now_utc(), "rules": RULES, "thresholds": THRESHOLDS})
    for path, want in ((DATA_RDA, RDA_SHA256), (DATA_TARBALL, TARBALL_SHA256)):
        got = sha256_file(path)
        if got != want:
            raise ValueError(f"{path.name}: sha256 {got} differs from the committed {want}")
    basin = load_basin(DATA_RDA)
    if basin["n_rows"] != RDA_ROWS:
        raise ValueError(f"expected {RDA_ROWS} daily rows, found {basin['n_rows']}")
    dump_json(pt["basin"], basin)
    xc = pyreadr_crosscheck(DATA_RDA, basin)
    dump_json(out / "extract" / "rda_crosscheck.json", xc)
    log(f"[extract] second reading of the data file with pyreadr: {xc}")
    if xc["ran"] and not xc["values_agree"]:
        raise ValueError("pyreadr and the built-in reader disagree on rain, evaporation or flow")
    members = read_members(DATA_TARBALL, {m for m, _ in SOURCE_CHECKS} | {TRANSFO_MEMBER, CALIB_MEMBER})
    missing = verify_source_constants(members)
    if missing:
        raise ValueError("hardcoded GR4J constants not found in the committed source: " + "; ".join(missing))
    rng = parse_transfo_ranges(members[TRANSFO_MEMBER], members[CALIB_MEMBER])
    rng["sources"] = {TRANSFO_MEMBER: hashlib.sha256(members[TRANSFO_MEMBER].encode()).hexdigest(),
                      CALIB_MEMBER: hashlib.sha256(members[CALIB_MEMBER].encode()).hexdigest()}
    rng["reading"] = ("range of Xk = [TR_k(lo), TR_k(hi)] with TR_k the 'TR' map in TransfoParam_GR4J.R and "
                      "[lo, hi] the transformed-space bounds in CreateCalibOptions.R; draws are uniform on "
                      "these ranges in parameter units")
    dump_json(pt["ranges"], rng)
    params = draw_params(rng["ranges"], N_MAX, PARAM_DRAW_SEED)
    check_params(params, rng["ranges"])
    check_forcing_windows(basin)
    dump_json(pt["params"], {"seed": PARAM_DRAW_SEED, "rng": "python random.Random, uniform per parameter",
                             "n": len(params), "order": ["X1", "X2", "X3", "X4"], "params": params})
    pt["rscript"].parent.mkdir(parents=True, exist_ok=True)
    pt["rscript"].write_text(R_SCRIPT)
    log(f"[extract] {basin['n_rows']} days {basin['dates'][0]}..{basin['dates'][-1]}; ranges "
        f"{ {k: [float(f'{v:.6g}') for v in vv] for k, vv in rng['ranges'].items()} }; {len(params)} parameter "
        f"vectors (seed {PARAM_DRAW_SEED})")


# ----------------------------------------------------------------------------------------------
# Record writers for each endpoint and control. Measurement code and the selftest share them.
# ----------------------------------------------------------------------------------------------
def anchor_inputs(out) -> list:
    pt = paths(out)
    return [inp(DATA_RDA, RDA_ROWS), inp(DATA_TARBALL), inp(pt["rscript"]), inp(pt["install_status"]),
            inp(pt["airgr_output"], 3), inp_rows(pt["anchor_rows"])]


def write_e1_i1(out, airgr: dict | None, error_text: str | None) -> dict:
    st = RunState(out)
    ins = anchor_inputs(out)
    if airgr is None:
        st.add_label(LABEL_PAGE_ONLY_RUN)
        vals = {"nse": None, "page_value": ANCHOR_NSE, "error_text": error_text}
        note = ("R or airGR could not be installed or run. The JAX anchor falls back to the page value 0.495; "
                "every later record carries the label 'anchor by page value'.")
        write_record(out, "E1", vals, "NOT_RUN", ins, notes=note)
        write_record(out, "I1", {"error_text": error_text}, "NOT_RUN", ins, notes=note)
        return {"E1": "NOT_RUN", "I1": "NOT_RUN"}
    by = airgr["by_id"]
    a = by["anchor_cal"]
    e1_ok = in_band(a["nse"], ANCHOR_NSE, ANCHOR_TOL)
    vals = {"nse": a["nse"], "page_value": ANCHOR_NSE, "abs_difference": None if a["nse"] is None
            else abs(a["nse"] - ANCHOR_NSE), "warmup_first": a.get("warmup_first"), "warmup_n": a.get("warmup_n"),
            "ini_res_levels": a.get("ini_res_levels"), "n_run_days": len(a["dates"]),
            "airgr_version": airgr["airgr_version"], "r_version": airgr["r_version"]}
    if not e1_ok:
        st.void(f"anchor endpoint E1 failed: airGR NSE {a['nse']} outside 0.495 +/- 0.02",
                timing_label=LABEL_ANCHOR_FAILED)
    rows = [{k: c.get(k) for k in ("id", "set", "X", "nse", "warmup_first", "warmup_n")} for c in airgr["cases"]]
    write_record(out, "E1", vals, "PASS" if e1_ok else "FAIL", ins, rows=rows)
    g, m = by["generalist_cal"]["nse"], by["michel_val"]["nse"]
    i1_ok = in_band(g, GENERALIST_CAL_NSE, HELDOUT_TOL) and in_band(m, MICHEL_VAL_NSE, HELDOUT_TOL)
    if not i1_ok:
        st.void(f"control I1 failed: airGR held-out NSE generalist {g}, Michel {m}",
                timing_label=LABEL_ANCHOR_FAILED)
    write_record(out, "I1", {"generalist_cal_nse": g, "michel_val_nse": m,
                             "michel_val_n_obs_days": sum(1 for x in by["michel_val"]["qobs"] if x is not None)},
                 "PASS" if i1_ok else "FAIL", ins, rows=rows)
    return {"E1": "PASS" if e1_ok else "FAIL", "I1": "PASS" if i1_ok else "FAIL"}


def make_anchor_jax_row(backend: str, case: dict, q_run: list, dates_run: list, obs_run: list, warm: tuple,
                        airgr_case: dict | None, dtype: str) -> dict:
    flags = flow_flags(q_run)
    row = {"arm": "anchor_jax", "backend": backend, "case": case["id"], "set": case["set"], "X": list(case["X"]),
           "period_first": dates_run[0], "period_last": dates_run[-1], "warmup_first": warm[0],
           "warmup_n": warm[1], "n_days": len(q_run), "nse": nse(q_run, obs_run), "page_nse": case["page_nse"],
           "airgr_available": airgr_case is not None, "dtype": dtype, **flags}
    if airgr_case is not None:
        match = list(airgr_case["dates"]) == list(dates_run)
        m, excl = mare(q_run, airgr_case["qsim"]) if match else (None, None)
        row.update({"dates_match_airgr": match, "mare_vs_airgr": m, "mare_excluded_days": excl,
                    "airgr_nse": airgr_case.get("nse")})
    else:
        row.update({"dates_match_airgr": None, "mare_vs_airgr": None, "mare_excluded_days": None,
                    "airgr_nse": None})
    return row


def _jax_case_ok(r: dict | None, center: float, airgr_ran: bool) -> tuple:
    if r is None:
        return False, "no row"
    why = []
    if not in_band(r.get("nse"), center, ANCHOR_TOL if center == ANCHOR_NSE else HELDOUT_TOL):
        why.append(f"NSE {r.get('nse')} outside {center} band")
    if r.get("nonfinite_days") or r.get("all_zero_flow"):
        why.append("degenerate flow (non-finite or all zero)")
    if airgr_ran:
        if not r.get("dates_match_airgr"):
            why.append("dates differ from airGR")
        m = r.get("mare_vs_airgr")
        if not (finite(m) and m < MARE_MAX):
            why.append(f"MARE {m} not below {MARE_MAX}")
    return (not why), "; ".join(why) or "ok"


def write_e2_i2(out, airgr_ran: bool) -> dict:
    st = RunState(out)
    pt = paths(out)
    rows = [r for r in read_jsonl(pt["anchor_rows"]) if r.get("arm") == "anchor_jax"]
    ins = anchor_inputs(out) + [inp_rows(pt["anchor_daily"])]

    def get(b, cid):
        hits = [r for r in rows if r["backend"] == b and r["case"] == cid]
        return hits[-1] if hits else None

    per = {}
    for b in ("gpu", "cpu"):
        ok, why = _jax_case_ok(get(b, "anchor_cal"), ANCHOR_NSE, airgr_ran)
        r = get(b, "anchor_cal") or {}
        per[b] = {"pass": ok, "why": why, "nse": r.get("nse"), "mare_vs_airgr": r.get("mare_vs_airgr")}
    e2_ok = all(per[b]["pass"] for b in per)
    suffix = "" if airgr_ran else f" ({LABEL_E2_PAGE_ONLY})"
    if not e2_ok:
        st.void("anchor endpoint E2 failed: " + "; ".join(f"{b}: {per[b]['why']}" for b in per),
                timing_label=LABEL_ANCHOR_FAILED)
    write_record(out, "E2", {"per_backend": per, "airgr_ran": airgr_ran,
                             "e2_label": None if airgr_ran else LABEL_E2_PAGE_ONLY},
                 ("PASS" if e2_ok else "FAIL") + suffix, ins,
                 notes="" if airgr_ran else LABEL_E2_PAGE_ONLY,
                 rows=[r for r in rows if r["case"] == "anchor_cal"])
    planted = planted_model_checks()
    per2 = {}
    for b in ("gpu", "cpu"):
        g_ok, g_why = _jax_case_ok(get(b, "generalist_cal"), GENERALIST_CAL_NSE, airgr_ran)
        m_ok, m_why = _jax_case_ok(get(b, "michel_val"), MICHEL_VAL_NSE, airgr_ran)
        per2[b] = {"generalist_cal": {"pass": g_ok, "why": g_why,
                                      "nse": (get(b, "generalist_cal") or {}).get("nse"),
                                      "mare_vs_airgr": (get(b, "generalist_cal") or {}).get("mare_vs_airgr")},
                   "michel_val": {"pass": m_ok, "why": m_why, "nse": (get(b, "michel_val") or {}).get("nse"),
                                  "mare_vs_airgr": (get(b, "michel_val") or {}).get("mare_vs_airgr")}}
    i2_ok = all(per2[b][c]["pass"] for b in per2 for c in per2[b]) and planted["all_pass"]
    if not i2_ok:
        st.void("control I2 failed: JAX held-out values, airGR match or planted model rows",
                timing_label=LABEL_ANCHOR_FAILED)
    write_record(out, "I2", {"per_backend": per2, "planted_model_rows": planted, "airgr_ran": airgr_ran},
                 ("PASS" if i2_ok else "FAIL") + suffix, ins,
                 notes="" if airgr_ran else "MARE part skipped: " + LABEL_E2_PAGE_ONLY,
                 rows=[r for r in rows if r["case"] != "anchor_cal"])
    return {"E2": e2_ok, "I2": i2_ok}


def hw_from_rows(rows: list) -> dict:
    if not rows:
        return {"hardware": None, "hardware_consistent": None}
    first = {k: rows[0].get(k) for k in HW_KEYS}
    same = all({k: r.get(k) for k in HW_KEYS} == first for r in rows)
    return {"hardware": first, "hardware_consistent": same}


def write_i3_i4(out) -> dict:
    st = RunState(out)
    pt = paths(out)
    rows = read_jsonl(pt["timer_rows"])
    ins = [inp_rows(pt["timer_rows"]), inp(pt["hardware"])]
    i3 = {}
    for b in ("gpu", "cpu"):
        s = [r for r in rows if r.get("control") == "I3" and r.get("backend") == b]
        ms = s[-1]["ms"] if s else None
        i3[b] = {"ms": ms, "pass": finite(ms) and abs(ms - I3_SLEEP_MS) <= I3_TOL_MS}
    i3_ok = all(v["pass"] for v in i3.values())
    if not i3_ok:
        st.void(f"control I3 failed: sleep readings {i3}")
    write_record(out, "I3", {"per_backend": i3, **hw_from_rows(rows)}, "PASS" if i3_ok else "FAIL", ins,
                 rows=[r for r in rows if r.get("control") == "I3"])
    i4 = {}
    for b in ("gpu", "cpu"):
        def med(nd):
            v = [r["ms"] for r in rows if r.get("control") == "I4" and r.get("backend") == b
                 and r.get("n_days") == nd and not r.get("warmup")]
            return (statistics.median(v), len(v)) if v else (None, 0)
        m730, n730 = med(SHORT_DAYS)
        m7300, n7300 = med(N_DAYS)
        ratio = m730 / m7300 if (finite(m730) and finite(m7300) and m7300 > 0) else None
        i4[b] = {"median_ms_730": m730, "median_ms_7300": m7300, "n_730": n730, "n_7300": n7300, "ratio": ratio,
                 "pass": ratio is not None and I4_BAND[0] <= ratio <= I4_BAND[1]}
    i4_ok = all(v["pass"] for v in i4.values())
    if not i4_ok:
        st.void(f"control I4 failed: scan-length ratios {i4}")
    write_record(out, "I4", {"per_backend": i4, **hw_from_rows(rows)}, "PASS" if i4_ok else "FAIL", ins,
                 rows=[r for r in rows if r.get("control") == "I4"])
    return {"I3": i3_ok, "I4": i4_ok}


def check_i5() -> tuple:
    a, b = main_run_hours(2.0, DESIGN_OVERHEAD), main_run_hours(20.0, DESIGN_OVERHEAD)
    s1, s2 = 3.0 / a, 3.0 / b
    ok = round(a, 4) == 0.2222 and round(b, 4) == 2.2222 and abs(s1 - 13.5) < 1e-9 and abs(s2 - 1.35) < 1e-9
    return ok, {"main_run_hours_ms2": a, "main_run_hours_ms20": b, "speedup_ms2": s1, "speedup_ms20": s2}


def check_i7() -> tuple:
    tp = chain_steps_per_s(2684, 60.0)
    ratio = chain_steps_per_s(2684, 50.0) / chain_steps_per_s(268, 50.0)
    ok = f"{tp:.4e}" == "3.2655e+08" and round(ratio, 1) == 10.0 and scaling_label(ratio) == "linear"
    return ok, {"chain_steps_per_s": tp, "equal_time_ratio": ratio, "equal_time_label": scaling_label(ratio)}


def write_e6(out, main_h, inputs: list, verdict_prefix: str = "", rows=None, extra: dict | None = None) -> str:
    """Card gate. A failing gate voids the run before its own record is written."""
    st = RunState(out)
    if main_h is None:
        write_record(out, "E6", {"main_run_hours": None, **(extra or {})},
                     "NOT_COMPUTABLE: main_run_hours missing", inputs, rows=rows)
        return "NOT_COMPUTABLE"
    d = gate_decision(main_h)
    if d != "pass":
        st.void(f"card gate E6 failed: main_run_hours {main_h:.4f} > 6")
    write_record(out, "E6", {"main_run_hours": main_h, "gate_reading": d, **(extra or {})},
                 (verdict_prefix + d) if verdict_prefix else d, inputs, rows=rows)
    return d


def check_i6() -> tuple:
    d1, d2 = gate_decision(5.9), gate_decision(6.1)
    detail = {"decision_at_5_9": d1, "decision_at_6_1": d2}
    ok = d1 == "pass" and d2 == GATE_STOP_TEXT
    saved = _LOG["prefix"]
    _LOG["prefix"] = "[planted check in a scratch folder; not this run] "
    try:
        with tempfile.TemporaryDirectory() as td:
            ok, detail = _i6_scratch(Path(td), ok, detail)
    finally:
        _LOG["prefix"] = saved
    return ok, detail


def _i6_scratch(o: Path, ok: bool, detail: dict) -> tuple:
    RunState(o).ensure()
    write_e6(o, 5.9, [])
    r1 = load_json(record_path(o, "E6"))
    row_a = write_row(o, "planted.jsonl", {"planted": "before gate failure"})
    write_e6(o, 6.1, [])
    r2 = load_json(record_path(o, "E6"))
    write_record(o, "E7", {"planted": True}, "planted follow-up record", [])
    r3 = load_json(record_path(o, "E7"))
    row_b = write_row(o, "planted.jsonl", {"planted": "after gate failure"}, timing=True)
    detail.update({"record_at_5_9_run_valid": r1["values"]["run_valid"],
                   "row_before_run_valid": row_a["run_valid"],
                   "record_at_6_1_run_valid": r2["values"]["run_valid"],
                   "record_after_run_valid": r3["values"]["run_valid"],
                   "row_after_run_valid": row_b["run_valid"],
                   "final_state_run_valid": RunState(o).load()["run_valid"]})
    ok = ok and r1["values"]["run_valid"] and row_a["run_valid"] and r1["decision"] == "pass" \
        and r2["decision"] == GATE_STOP_TEXT and not r2["values"]["run_valid"] \
        and not r3["values"]["run_valid"] and not row_b["run_valid"] \
        and not detail["final_state_run_valid"]
    return ok, detail


def write_control(out, rid: str, ok: bool, detail: dict) -> bool:
    if not ok:
        RunState(out).void(f"control {rid} failed: planted arithmetic or propagation check")
    write_record(out, rid, detail, "PASS" if ok else "FAIL", [inp(Path(__file__))],
                 notes="planted rows evaluated by this file's endpoint code")
    return ok


def forward_stats(timing: list, backend: str, n: int) -> dict:
    rows = [r for r in timing if r.get("backend") == backend and r.get("n_chains") == n
            and r.get("params_mode") == "distinct" and not r.get("warmup") and r.get("n_days") == N_DAYS]
    s = spread([r["ms"] for r in rows])
    return {"rows": rows, "spread": s, "median_ms": s["median"] if s else None,
            "complete": len(rows) == len(SEEDS) * REPEATS}


def overhead_stats(probe: list, backend: str, fwd_ms) -> dict:
    per_seed = []
    complete = True
    for s in SEEDS:
        blocks = [r for r in probe if r.get("backend") == backend and r.get("seed") == s and not r.get("warmup")]
        iters = sum(r["iterations"] for r in blocks)
        if iters != PROBE_ITERS:
            complete = False
        if iters <= 0 or not finite(fwd_ms) or fwd_ms <= 0:
            continue
        ms = sum(r["ms"] for r in blocks)
        per_iter = ms / iters
        acc = sum(r.get("accepted", 0) for r in blocks)
        n_ch = blocks[0].get("n_chains") or N_MAX
        per_seed.append({"seed": s, "iterations": iters, "total_ms": ms, "ms_per_iteration": per_iter,
                         "overhead": per_iter / fwd_ms, "acceptance_rate": acc / (iters * n_ch)})
    ov = statistics.median([p["overhead"] for p in per_seed]) if per_seed else None
    return {"overhead": ov, "per_seed": per_seed, "complete": complete and len(per_seed) == len(SEEDS),
            "forward_ms": fwd_ms}


def _reading(no_verdict: str | None, complete: bool, reading: str, missing: str) -> str:
    if no_verdict:
        return f"{no_verdict}{reading})"
    if not complete:
        return f"NOT_COMPUTABLE: {missing}"
    return reading


def stage_endpoints(out) -> None:
    out = Path(out)
    pt = paths(out)
    st = RunState(out)
    st.ensure()
    for rid in ("E1", "I1", "E2", "I2", "I3", "I4"):
        if not record_path(out, rid).exists():
            if not st.load()["incomplete"]:
                st.void(f"record {rid} missing when endpoints ran")
            write_record(out, rid, {}, "NOT_RUN: the run stopped before this stage", [],
                         notes="placeholder so that a missing cell is visible")
    write_control(out, "I5", *check_i5())
    write_control(out, "I6", *check_i6())
    write_control(out, "I7", *check_i7())

    timing = read_jsonl(pt["timing_rows"])
    probe = read_jsonl(pt["probe_blocks"])
    halt = None
    try:
        for b in ("gpu", "cpu"):
            for n in SIZES:
                cell = forward_stats(timing, b, n)["rows"]
                if cell:
                    check_timing_cell(cell, f"{b} backend, {n} chains")
            for s in SEEDS:
                prow = [r for r in probe if r.get("backend") == b and r.get("seed") == s]
                if prow:
                    check_probe_seed(prow, f"{b} backend probe, seed {s}")
    except Halt as h:
        halt = h
        st.void(f"{h.code}: {h.detail}")
    if halt is not None:
        nv = f"HALTED {halt.code}: no verdict (descriptive reading: "
    elif st.load()["incomplete"]:
        nv = "NO_VERDICT: incomplete run (descriptive reading: "
    else:
        nv = None
    t_ins = [inp_rows(pt["timing_rows"]), inp_rows(pt["probe_blocks"]), inp(pt["params"], N_MAX),
             inp(pt["ranges"]), inp(pt["basin"], RDA_ROWS)]

    gpu = forward_stats(timing, "gpu", N_MAX)
    cpu = forward_stats(timing, "cpu", N_MAX)
    ov_g = overhead_stats(probe, "gpu", gpu["median_ms"])
    ov_c = overhead_stats(probe, "cpu", cpu["median_ms"])
    hw_g = hw_from_rows(gpu["rows"])

    # Batched forward time on the GPU.
    e3 = guess_band(gpu["median_ms"], E3_BAND) if finite(gpu["median_ms"]) else None
    write_record(out, "E3", {"batched_forward_ms": gpu["median_ms"], "spread_ms": gpu["spread"],
                             "n_passes": len(gpu["rows"]), "card_guess_ms": 2.0, **hw_g},
                 _reading(nv, gpu["complete"] and e3 is not None, str(e3),
                          f"{len(gpu['rows'])} of 30 GPU passes at 2,684 chains"), t_ins, rows=gpu["rows"])

    # CPU hours with the measured CPU overhead.
    cpu_h = main_run_hours(cpu["median_ms"], ov_c["overhead"]) if (finite(cpu["median_ms"])
                                                                    and finite(ov_c["overhead"])) else None
    e4 = guess_band(cpu_h, E4_BAND) if cpu_h is not None else None
    write_record(out, "E4", {"cpu_671_hours": cpu_h, "cpu_forward_ms": cpu["median_ms"],
                             "cpu_spread_ms": cpu["spread"], "overhead_cpu": ov_c["overhead"],
                             "overhead_cpu_per_seed": ov_c["per_seed"], "card_guess_hours": 3.0,
                             **hw_from_rows(cpu["rows"])},
                 _reading(nv, cpu["complete"] and ov_c["complete"] and e4 is not None, str(e4),
                          "CPU passes or CPU probe blocks missing"), t_ins,
                 rows=cpu["rows"] + [r for r in probe if r.get("backend") == "cpu"])

    # Card decision, measured overhead, plus the design-overhead sensitivity line.
    main_h = main_run_hours(gpu["median_ms"], ov_g["overhead"]) if (finite(gpu["median_ms"])
                                                                     and finite(ov_g["overhead"])) else None
    speed = cpu_h / main_h if (cpu_h is not None and main_h) else None
    e5 = card_decision(main_h, speed) if (main_h is not None and speed is not None) else None
    sens = None
    if finite(gpu["median_ms"]) and finite(cpu["median_ms"]):
        m4 = main_run_hours(gpu["median_ms"], DESIGN_OVERHEAD)
        c4 = main_run_hours(cpu["median_ms"], DESIGN_OVERHEAD)
        sens = {"label": "sensitivity line: design overhead 4 on both backends; does not decide",
                "overhead": DESIGN_OVERHEAD, "main_run_hours": m4, "cpu_671_hours": c4, "speedup": c4 / m4,
                "reading": card_decision(m4, c4 / m4)}
    complete5 = gpu["complete"] and cpu["complete"] and ov_g["complete"] and ov_c["complete"] and e5 is not None
    write_record(out, "E5", {"main_run_hours": main_h, "cpu_671_hours": cpu_h, "speedup": speed,
                             "batched_forward_ms": gpu["median_ms"], "cpu_forward_ms": cpu["median_ms"],
                             "overhead_gpu": ov_g["overhead"], "overhead_cpu": ov_c["overhead"],
                             "overhead_gpu_per_seed": ov_g["per_seed"], "overhead_cpu_per_seed": ov_c["per_seed"],
                             "card_expected": "if_not", "sensitivity_overhead_4": sens, **hw_g},
                 _reading(nv, complete5, str(e5), "timing or probe rows missing on a backend"), t_ins,
                 rows=ov_g["per_seed"] + ov_c["per_seed"])

    # Card gate.
    if main_h is not None and nv:
        d = gate_decision(main_h)
        if d != "pass":
            st.void(f"card gate E6 failed: main_run_hours {main_h:.4f} > 6")
        write_record(out, "E6", {"main_run_hours": main_h, "gate_reading": d, **hw_g}, nv + d + ")", t_ins)
    else:
        write_e6(out, main_h, t_ins, extra=hw_g)

    # Throughput scaling on the GPU.
    tp, med = {}, {}
    for n in SIZES:
        fs = forward_stats(timing, "gpu", n)
        med[n] = fs["median_ms"]
        tp[n] = chain_steps_per_s(n, fs["median_ms"]) if finite(fs["median_ms"]) else None
    ratio = tp[N_MAX] / tp[268] if (tp.get(N_MAX) and tp.get(268)) else None
    complete7 = all(forward_stats(timing, "gpu", n)["complete"] for n in SIZES) and ratio is not None
    write_record(out, "E7", {"chain_steps_per_s": {str(k): v for k, v in tp.items()},
                             "median_ms": {str(k): v for k, v in med.items()}, "ratio_2684_over_268": ratio,
                             "scaling_reading": scaling_label(ratio) if ratio is not None else None, **hw_g},
                 "REPORT_ONLY: " + _reading(nv, complete7,
                                            scaling_label(ratio) if ratio is not None else "none",
                                            "GPU passes missing at some size"),
                 t_ins, rows=[r for r in timing if r.get("backend") == "gpu" and not r.get("warmup")])
    log(f"[endpoints] done; run_valid={RunState(out).load()['run_valid']}")
    write_summary(out)
    if halt is not None:
        raise halt


# ----------------------------------------------------------------------------------------------
# Stage: generate (box only: JAX, numpy, R).
# ----------------------------------------------------------------------------------------------
def vcpu_count() -> int:
    try:
        return len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        return os.cpu_count() or 0


def hardware_labels(out, jax_mod) -> dict:
    p = paths(out)["hardware"]
    if p.exists():
        return load_json(p)
    gpus, err = [], None
    try:
        txt = subprocess.run(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
                             capture_output=True, text=True, timeout=60).stdout
        gpus = parse_nvidia_smi_csv(txt)
    except Exception as e:  # noqa: BLE001
        err = repr(e)
    try:
        price = parse_money("PRICE_USD_PER_HOUR", os.environ)
    except ValueError:
        price = None
    jlv, jlv_src = jaxlib_version()
    inst = os.environ.get("INSTANCE_TYPE") or (
        f"not forwarded to the box; nvidia-smi shows {len(gpus)}x {gpus[0]['name']}" if gpus else "unknown")
    labels = {"instance_type": inst, "gpu_name": gpus[0]["name"] if gpus else None, "gpu_count": len(gpus),
              "driver_version": gpus[0]["driver_version"] if gpus else None, "jax_version": jax_mod.__version__,
              "jaxlib_version": jlv, "jaxlib_version_source": jlv_src, "vcpu_count": vcpu_count(),
              "price_usd_per_hour": price,
              "lambda_instance_id": os.environ.get("LAMBDA_INSTANCE_ID") or None,
              "git_commit": os.environ.get("GIT_COMMIT") or None, "dtype": "float32 (JAX default)",
              "jax_devices": [str(d) for d in jax_mod.devices()], "nvidia_smi_error": err}
    dump_json(p, labels)
    return labels


def refuse_if_rows(path: Path, pred, what: str) -> None:
    """Appending a second set of measurements to the same file would mix them; refuse instead."""
    if any(pred(r) for r in read_jsonl(path, strict=False)[0]):
        raise ValueError(f"{what}: rows already exist in {path}; use a fresh --out folder")


def _jax():
    import numpy as np
    import jax
    import jax.numpy as jnp
    from jax import lax
    return np, jax, jnp, lax


def _device(jax, backend: str):
    return jax.devices("gpu")[0] if backend == "gpu" else jax.devices("cpu")[0]


def _timed(jax, fn, *args):
    t0 = time.perf_counter()
    res = fn(*args)
    jax.block_until_ready(res)
    return res, (time.perf_counter() - t0) * 1000.0


def _hw(hw: dict) -> dict:
    return {k: hw.get(k) for k in HW_KEYS}


def gen_anchor_airgr(out) -> None:
    out = Path(out)
    pt = paths(out)
    refuse_if_rows(pt["anchor_rows"], lambda r: r.get("arm") == "anchor_airgr", "airGR anchor")
    status, error_text, airgr = None, None, None
    if pt["install_status"].exists():
        try:
            status = parse_install_status(pt["install_status"].read_text())
        except ValueError as e:
            error_text = f"install status unreadable: {e}"
    if status is None or not status["ok"]:
        error_text = (error_text + "\n" if error_text else "") + install_error_text(out, status)
    else:
        rscript = shutil.which("Rscript")
        if rscript is None:
            error_text = "Rscript not found on PATH after the install step"
        else:
            pt["airgr_output"].parent.mkdir(parents=True, exist_ok=True)
            try:
                proc = subprocess.run([rscript, str(pt["rscript"]), str(DATA_RDA), str(pt["airgr_output"])],
                                      capture_output=True, text=True, timeout=900)
            except subprocess.TimeoutExpired as e:
                proc = subprocess.CompletedProcess(e.cmd, 124, e.stdout or "", f"Rscript timed out after {e.timeout} s")
            logp = out / "logs" / "anchor_airgr_R.log"
            logp.parent.mkdir(parents=True, exist_ok=True)
            logp.write_text(f"exit {proc.returncode}\n--- stdout ---\n{proc.stdout}\n--- stderr ---\n{proc.stderr}")
            if proc.returncode != 0:
                error_text = f"Rscript exit code {proc.returncode}:\n" + "\n".join(proc.stderr.splitlines()[-25:])
            else:
                try:
                    airgr = parse_airgr_json(pt["airgr_output"].read_text())
                except (ValueError, OSError) as e:
                    error_text = f"airGR output unreadable: {e}"
    if airgr is not None:
        for c in airgr["cases"]:
            exp = next(x for x in AIRGR_CASES if x["id"] == c["id"])
            write_row(out, "anchor_rows.jsonl", {
                "arm": "anchor_airgr", "backend": "R", "case": c["id"], "set": c["set"], "X": c["X"],
                "period_first": c["dates"][0], "period_last": c["dates"][-1], "warmup_first": c.get("warmup_first"),
                "warmup_n": c.get("warmup_n"), "n_days": len(c["dates"]), "nse": c["nse"],
                "page_nse": exp["page_nse"], "mare_vs_airgr": None, "airgr_version": airgr["airgr_version"],
                "r_version": airgr["r_version"]})
    write_e1_i1(out, airgr, error_text)


def gen_anchor_jax(out) -> None:
    out = Path(out)
    pt = paths(out)
    refuse_if_rows(pt["anchor_rows"], lambda r: r.get("arm") == "anchor_jax", "JAX anchor")
    np, jax, jnp, lax = _jax()
    hw = hardware_labels(out, jax)
    basin = load_basin_extract(out)
    airgr = None
    e1 = load_json(record_path(out, "E1")) if record_path(out, "E1").exists() else None
    if e1 is not None and e1["decision"] != "NOT_RUN" and pt["airgr_output"].exists():
        airgr = parse_airgr_json(pt["airgr_output"].read_text())
    fwd = jax.jit(make_forward(jnp, lax))
    dates = basin["dates"]
    for backend in ("gpu", "cpu"):
        dev = _device(jax, backend)
        for case in AIRGR_CASES:
            i0, i1, w0 = case_window(dates, case)
            P = np.asarray(basin["P"][w0:i1 + 1], np.float32)[:, None]
            E = np.asarray(basin["E"][w0:i1 + 1], np.float32)[:, None]
            prm = np.asarray([case["X"]], np.float32)
            Q, ms = _timed(jax, fwd, jax.device_put(prm, dev), jax.device_put(P, dev), jax.device_put(E, dev))
            q = [float(x) for x in np.asarray(Q)[:, 0]]
            q_run = q[i0 - w0:]
            ac = airgr["by_id"][case["id"]] if airgr is not None else None
            row = make_anchor_jax_row(backend, case, q_run, dates[i0:i1 + 1], basin["Qmm"][i0:i1 + 1],
                                      (dates[w0] if w0 < i0 else "none", i0 - w0), ac, hw["dtype"])
            row.update({"device": str(dev), "first_call_ms_including_compile": ms, **_hw(hw)})
            write_row(out, "anchor_rows.jsonl", row)
            write_row(out, "anchor_daily.jsonl", {"arm": "anchor_jax", "backend": backend, "case": case["id"],
                                                  "dates_first": dates[i0], "dates_last": dates[i1],
                                                  "qsim": q_run})
            log(f"[anchor_jax] {backend} {case['id']}: NSE {row['nse']} MARE {row['mare_vs_airgr']}")
    write_e2_i2(out, airgr is not None)


def _tiled(np, series: list, seed: int, n_days: int, n_chains: int):
    w = np.asarray(forcing_window(series, seed, n_days), np.float32)
    return np.ascontiguousarray(np.tile(w[:, None], (1, n_chains)))


def gen_timers(out) -> None:
    out = Path(out)
    refuse_if_rows(paths(out)["timer_rows"], lambda r: True, "timer checks")
    np, jax, jnp, lax = _jax()
    hw = hardware_labels(out, jax)
    basin = load_basin_extract(out)
    params = load_json(paths(out)["params"])["params"]
    fwd = jax.jit(make_forward(jnp, lax))
    guard = Guard()
    last = 0.0
    for backend in ("gpu", "cpu"):
        dev = _device(jax, backend)
        x = jax.device_put(np.zeros((1,), np.float32), dev)
        _, ms = _timed(jax, lambda a: (time.sleep(0.1), a)[1], x)
        write_row(out, "timer_rows.jsonl", {"control": "I3", "backend": backend, "kind": "sleep_100ms", "ms": ms,
                                            "device": str(dev), **_hw(hw)}, timing=True)
        prm = jax.device_put(np.asarray(params[:N_MAX], np.float32), dev)
        P = _tiled(np, basin["P"], 1, N_DAYS, N_MAX)
        E = _tiled(np, basin["E"], 1, N_DAYS, N_MAX)
        data = {N_DAYS: (jax.device_put(P, dev), jax.device_put(E, dev)),
                SHORT_DAYS: (jax.device_put(np.ascontiguousarray(P[:SHORT_DAYS]), dev),
                             jax.device_put(np.ascontiguousarray(E[:SHORT_DAYS]), dev))}
        for nd in (SHORT_DAYS, N_DAYS):
            for rep in range(-1, REPEATS):  # rep -1 is the compile warm-up, excluded
                guard.check(1.5 * last)
                _, ms = _timed(jax, fwd, prm, *data[nd])
                last = ms / 1000.0
                write_row(out, "timer_rows.jsonl", {"control": "I4", "backend": backend, "n_days": nd,
                                                    "n_chains": N_MAX, "seed": 1, "repeat": rep, "ms": ms,
                                                    "warmup": rep < 0, "params_mode": "distinct",
                                                    "device": str(dev), **_hw(hw)}, timing=True)
        del data
    write_i3_i4(out)


def gen_timing(out, backend: str) -> None:
    out = Path(out)
    refuse_if_rows(paths(out)["timing_rows"], lambda r: r.get("backend") == backend, f"{backend} timing")
    np, jax, jnp, lax = _jax()
    hw = hardware_labels(out, jax)
    basin = load_basin_extract(out)
    params = load_json(paths(out)["params"])["params"]
    fwd = jax.jit(make_forward(jnp, lax))
    dev = _device(jax, backend)
    guard = Guard()
    last = 0.0
    arm = f"{backend}_timing"
    for n in SIZES:
        prm = jax.device_put(np.asarray(params[:n], np.float32), dev)
        forcing = {s: (jax.device_put(_tiled(np, basin["P"], s, N_DAYS, n), dev),
                       jax.device_put(_tiled(np, basin["E"], s, N_DAYS, n), dev)) for s in SEEDS}
        jax.block_until_ready(forcing)
        guard.check(1.5 * last)
        _, ms = _timed(jax, fwd, prm, *forcing[SEEDS[0]])
        last = ms / 1000.0
        base = {"arm": arm, "backend": backend, "n_chains": n, "n_days": N_DAYS, "device": str(dev), **_hw(hw)}
        write_row(out, "timing_rows.jsonl", {**base, "seed": SEEDS[0], "repeat": -1, "ms": ms, "warmup": True,
                                             "params_mode": "distinct", "forcing_offset_days": SEEDS[0]},
                  timing=True)
        cell = []
        for s in SEEDS:
            for rep in range(REPEATS):
                guard.check(1.5 * last)
                _, ms = _timed(jax, fwd, prm, *forcing[s])
                last = ms / 1000.0
                cell.append(write_row(out, "timing_rows.jsonl",
                                      {**base, "seed": s, "repeat": rep, "ms": ms, "warmup": False,
                                       "params_mode": "distinct", "forcing_offset_days": s}, timing=True))
        check_timing_cell(cell, f"{backend} backend, {n} chains")
        ident = jax.device_put(np.tile(np.asarray(ANCHOR_X, np.float32), (n, 1)), dev)
        guard.check(1.5 * last)
        _, ms = _timed(jax, fwd, ident, *forcing[SEEDS[0]])
        write_row(out, "timing_rows.jsonl", {**base, "seed": SEEDS[0], "repeat": 0, "ms": ms, "warmup": False,
                                             "params_mode": "identical_chains", "forcing_offset_days": SEEDS[0]},
                  timing=True)
        med = statistics.median(r["ms"] for r in cell)
        log(f"[timing] {backend} {n} chains: median {med:.3f} ms over {len(cell)} passes; identical chains "
            f"{ms:.3f} ms")
        del forcing


def make_probe(jax, jnp, lax):
    """Batched random-walk Metropolis with a Gaussian likelihood written through NSE.

    log-likelihood = -0.5 * n_obs * (1 - NSE) = -0.5 * SSE / variance(observed flow).
    The prior is uniform on the airGR ranges; a proposal outside them is rejected.
    """
    forward = make_forward(jnp, lax)

    def loglik(Q, obs):
        valid = jnp.isfinite(obs)
        o = jnp.where(valid, obs, 0.0)
        n = valid.sum(axis=0)
        mean = o.sum(axis=0) / n
        sse = jnp.where(valid, (Q - o) ** 2, 0.0).sum(axis=0)
        sst = jnp.where(valid, (o - mean) ** 2, 0.0).sum(axis=0)
        return -0.5 * n * (sse / sst)

    def init(theta, P, E, obs):
        return loglik(forward(theta, P, E), obs)

    def step(carry, P, E, obs, lo, hi, scale):
        key, theta, ll, n_acc = carry
        key, k1, k2 = jax.random.split(key, 3)
        prop = theta + scale * jax.random.normal(k1, theta.shape, theta.dtype)
        inside = jnp.all((prop >= lo) & (prop <= hi), axis=1)
        ll_prop = jnp.where(inside, loglik(forward(prop, P, E), obs), -jnp.inf)
        u = jax.random.uniform(k2, ll.shape, theta.dtype)
        accept = jnp.log(u) < ll_prop - ll
        theta = jnp.where(accept[:, None], prop, theta)
        ll = jnp.where(accept, ll_prop, ll)
        return key, theta, ll, n_acc + accept.sum().astype(jnp.int32)

    return jax.jit(init), jax.jit(step)


def gen_probe(out, backend: str) -> None:
    out = Path(out)
    refuse_if_rows(paths(out)["probe_blocks"], lambda r: r.get("backend") == backend, f"{backend} probe")
    np, jax, jnp, lax = _jax()
    hw = hardware_labels(out, jax)
    basin = load_basin_extract(out)
    params = load_json(paths(out)["params"])["params"]
    ranges = load_json(paths(out)["ranges"])["ranges"]
    keys = ("X1", "X2", "X3", "X4")
    lo_np = np.asarray([ranges[k][0] for k in keys], np.float32)
    hi_np = np.asarray([ranges[k][1] for k in keys], np.float32)
    scale_np = np.asarray([PROPOSAL_FRACTION * (ranges[k][1] - ranges[k][0]) for k in keys], np.float32)
    init, step = make_probe(jax, jnp, lax)
    dev = _device(jax, backend)
    lo, hi, scale = (jax.device_put(a, dev) for a in (lo_np, hi_np, scale_np))
    guard = Guard()
    last = 0.0
    for s in SEEDS:
        P = jax.device_put(_tiled(np, basin["P"], s, N_DAYS, N_MAX), dev)
        E = jax.device_put(_tiled(np, basin["E"], s, N_DAYS, N_MAX), dev)
        obs = jax.device_put(_tiled(np, basin["Qmm"], s, N_DAYS, N_MAX), dev)
        theta = jax.device_put(np.asarray(params[:N_MAX], np.float32), dev)
        ll = init(theta, P, E, obs)
        carry = (jax.device_put(jax.random.PRNGKey(s), dev), theta, ll, jax.device_put(np.int32(0), dev))
        jax.block_until_ready(carry)
        base = {"arm": "overhead_probe", "backend": backend, "seed": s, "n_chains": N_MAX, "n_days": N_DAYS,
                "proposal_fraction": PROPOSAL_FRACTION, "device": str(dev), **_hw(hw)}
        guard.check(1.5 * last)
        carry, ms = _timed(jax, step, carry, P, E, obs, lo, hi, scale)  # compile warm-up, excluded
        rows = [write_row(out, "probe_blocks.jsonl", {**base, "block": -1, "iterations": 1, "ms": ms,
                                                       "warmup": True, "accepted": None}, timing=True)]
        for b in range(PROBE_ITERS // PROBE_BLOCK):
            guard.check(1.5 * last)
            acc0 = int(carry[3])
            t0 = time.perf_counter()
            for _ in range(PROBE_BLOCK):
                carry = step(carry, P, E, obs, lo, hi, scale)
            jax.block_until_ready(carry)
            ms = (time.perf_counter() - t0) * 1000.0
            last = ms / 1000.0
            acc = int(carry[3]) - acc0
            rows.append(write_row(out, "probe_blocks.jsonl", {
                **base, "block": b, "iterations": PROBE_BLOCK, "ms": ms, "ms_per_iteration": ms / PROBE_BLOCK,
                "warmup": False, "accepted": acc, "acceptance_rate": acc / (PROBE_BLOCK * N_MAX)}, timing=True))
        check_probe_seed(rows, f"{backend} backend probe, seed {s}")
        per_it = sum(r["ms"] for r in rows if not r["warmup"]) / PROBE_ITERS
        log(f"[probe] {backend} seed {s}: {per_it:.3f} ms per iteration")
        del P, E, obs


def cmd_gpu_check(out) -> int:
    RunState(out).ensure()
    err = None
    try:
        import jax
        gpus = [d for d in jax.devices() if d.platform == "gpu"]
        log(f"[gpu-check] jax {jax.__version__}; jaxlib {jaxlib_version()[0]}; devices {jax.devices()}")
    except Exception as e:  # noqa: BLE001
        gpus, err = [], repr(e)
    if not gpus:
        RunState(out).void(f"JAX sees no GPU; a silent CPU fallback is not allowed ({err or 'no gpu device'})")
        return EXIT_NO_GPU
    return EXIT_OK


def cmd_versions(out, label: str, compare_to: str | None) -> int:
    """Log package versions to logs/versions_<label>.json; compare jax, jaxlib, numpy with an earlier file."""
    vers = {"label": label, "utc": now_utc(), "python": sys.version.split()[0], "packages": package_versions()}
    dump_json(Path(out) / "logs" / f"versions_{label}.json", vers)
    for name, e in vers["packages"].items():
        log(f"[versions {label}] {name}: module version {e['module_version']} (read from "
            f"{e['module_version_source']}); installed metadata {e['dist_version']}"
            + (f"; import failed: {e['import_error']}" if e["import_error"] else ""))
    if compare_to:
        changed = pinned_versions_changed(load_json(compare_to)["packages"], vers["packages"])
        if changed:
            log("[versions] a preinstalled package changed: " + "; ".join(changed))
            return EXIT_ENV
        log("[versions] jax, jaxlib and numpy are unchanged")
    return EXIT_OK


def cmd_guard(out, stage: str) -> int:
    try:
        g = Guard()
    except ValueError as e:
        log(f"[guard] cannot read the price or the budget: {e}")
        RunState(out).void(f"cost guard cannot run: {e}")
        return EXIT_ENV
    ok, why = guard_verdict(g.uptime_s(), STAGE_EST_H[stage] * 3600.0, g.price, g.budget, time.time(),
                            g.deadline, MIN_SECONDS_LEFT)
    log(f"[guard] before {stage}: {why} (box up {g.uptime_s() / 3600.0:.3f} h, price USD {g.price}/h)")
    return EXIT_OK if ok else EXIT_GUARD_STOP


# ----------------------------------------------------------------------------------------------
# Selftest: standard library only. Parsers, detectors, model rows, endpoint arithmetic, records.
# ----------------------------------------------------------------------------------------------
def selftest() -> int:
    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond), detail))
        print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not cond else ""),
              flush=True)

    def raises(fn, exc, code=None):
        try:
            fn()
        except exc as e:  # noqa: PERF203
            return code is None or getattr(e, "code", None) == code
        except Exception:  # noqa: BLE001
            return False
        return False

    t_start = time.time()
    _LOG["quiet"] = True  # the planted pipelines would print one line per record
    for m in SELFTEST_BLOCKED:  # standard library only: these imports now fail for the whole selftest
        sys.modules[m] = None
    try:
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)

            # --- Parsers: committed data file and planted bytes ---------------------------------
            basin = load_basin(DATA_RDA)
            check("rda parser reads 10,593 days 1984-01-01..2012-12-31",
                  basin["n_rows"] == RDA_ROWS and basin["dates"][0] == "1984-01-01"
                  and basin["dates"][-1] == "2012-12-31", f"{basin['n_rows']} {basin['dates'][0]}")
            check("rda parser keeps 802 missing observed flows as NaN",
                  sum(1 for q in basin["Qmm"] if math.isnan(q)) == 802)
            check("rda parser: no missing rain or evaporation",
                  all(finite(x) for x in basin["P"]) and all(finite(x) for x in basin["E"]))
            check("rda parser reads the basin area 360 km2", basin["basin_area_km2"] == 360.0)

            def planted_rda(dates_secs, tz="UTC"):
                b = bytearray(b"RDX2\nX\n")

                def i(v):
                    b.extend(struct.pack(">i", v))

                def chars(s):
                    i(9 | (1 << 15)); i(len(s)); b.extend(s.encode())

                def strvec(vals):
                    i(16); i(len(vals))
                    for s in vals:
                        chars(s)

                def sym(name):
                    i(1); chars(name)

                def realvec(vals, attrs=None):
                    i(14 | ((1 << 9) if attrs else 0)); i(len(vals))
                    b.extend(struct.pack(f">{len(vals)}d", *vals))
                    if attrs:
                        attrs()

                i(2); i(197634); i(131840)
                i(2 | (1 << 10)); sym("BasinObs")
                i(19 | (1 << 8) | (1 << 9)); i(4)

                def dattr():
                    i(2 | (1 << 10)); sym("class"); strvec(["POSIXct", "POSIXt"])
                    i(2 | (1 << 10)); sym("tzone"); strvec([tz]); i(254)
                realvec(dates_secs, dattr)
                realvec([1.0, 2.0])
                realvec([0.5, 0.5])
                realvec([0.3, float("nan")])
                i(2 | (1 << 10)); sym("names"); strvec(["DatesR", "P", "E", "Qmm"])
                i(2 | (1 << 10)); sym("class"); strvec(["data.frame"]); i(254)
                i(254)
                return gzip.compress(bytes(b))

            pr = td / "planted.rda"
            pr.write_bytes(planted_rda([0.0, 86400.0]))
            pb = load_basin(pr)
            check("rda parser reads a planted two-day frame",
                  pb["dates"] == ["1970-01-01", "1970-01-02"] and pb["P"] == [1.0, 2.0] and math.isnan(pb["Qmm"][1]))
            pr.write_bytes(planted_rda([0.0, 2 * 86400.0]))
            check("rda parser rejects a date gap", raises(lambda: load_basin(pr), RdaError))
            pr.write_bytes(planted_rda([0.0, 86400.0], tz="Europe/Paris"))
            check("rda parser rejects a non-UTC time zone", raises(lambda: load_basin(pr), RdaError))
            check("rda parser rejects a non-R file", raises(lambda: parse_rda_bytes(b"hello world"), RdaError))
            check("heavy imports are blocked for the whole selftest",
                  all(raises(lambda m=m: __import__(m), ImportError) for m in SELFTEST_BLOCKED))
            xc = pyreadr_crosscheck(DATA_RDA, basin)
            check("pyreadr guard: without pyreadr the second reading says why it did not run",
                  not xc["ran"] and "not importable" in xc["reason"], str(xc))
            frame = {"P": list(basin["P"]), "E": list(basin["E"]), "Qmm": list(basin["Qmm"]),
                     "DatesR": [d + " 00:00:00" for d in basin["dates"]]}
            fake = types.ModuleType("pyreadr")
            fake.__version__ = "planted"
            fake.read_r = lambda path: {"BasinObs": frame}
            sys.modules["pyreadr"] = fake
            try:
                xa = pyreadr_crosscheck(DATA_RDA, basin)
                kq = next(i for i, q in enumerate(basin["Qmm"]) if finite(q))
                frame["Qmm"][kq] += 0.001
                xb = pyreadr_crosscheck(DATA_RDA, basin)

                def _fail(path):
                    raise ValueError("planted read failure")
                fake.read_r = _fail
                xf = pyreadr_crosscheck(DATA_RDA, basin)
            finally:
                sys.modules["pyreadr"] = None
            check("pyreadr comparison: a planted identical frame agrees on values and dates",
                  xa["ran"] and xa["values_agree"] and xa["dates_agree"] and xa["pyreadr_version"] == "planted", str(xa))
            check("pyreadr comparison: one changed flow value is caught", xb["ran"] and not xb["values_agree"], str(xb))
            check("pyreadr comparison: a read failure is reported, not raised",
                  not xf["ran"] and "could not read" in xf["reason"], str(xf))

            members = read_members(DATA_TARBALL, {m for m, _ in SOURCE_CHECKS} | {TRANSFO_MEMBER, CALIB_MEMBER})
            check("every hardcoded GR4J constant appears verbatim in the committed airGR source",
                  not verify_source_constants(members), "; ".join(verify_source_constants(members)))
            rng = parse_transfo_ranges(members[TRANSFO_MEMBER], members[CALIB_MEMBER])
            r = rng["ranges"]
            check("range parser: transformed bounds -9.99..9.99 from CreateCalibOptions.R",
                  rng["transformed_bounds"] == [-9.99, 9.99])
            check("range parser: X1 and X3 = [exp(-9.99), exp(9.99)]",
                  r["X1"] == [math.exp(-9.99), math.exp(9.99)] and r["X3"] == r["X1"])
            check("range parser: X2 = [sinh(-9.99), sinh(9.99)]", r["X2"] == [math.sinh(-9.99), math.sinh(9.99)])
            check("range parser: X4 = [0.5, 20]", abs(r["X4"][0] - 0.5) < 1e-12 and abs(r["X4"][1] - 20.0) < 1e-12,
                  str(r["X4"]))
            bad_tr = members[TRANSFO_MEMBER].replace("exp(ParamIn[, 1])", "log1p(ParamIn[, 1])", 1)
            check("range parser rejects an unknown transformation",
                  raises(lambda: parse_transfo_ranges(bad_tr, members[CALIB_MEMBER]), ValueError))
            check("range parser rejects missing calibration bounds",
                  raises(lambda: parse_transfo_ranges(members[TRANSFO_MEMBER], "nothing here"), ValueError))

            st = parse_install_status("apt_rc=0\nrcmd_rc=0\nr_libs_user=/x\n")
            check("install status parser: both steps ok", st["ok"] and st["r_libs_user"] == "/x")
            st = parse_install_status("apt_rc=100\nrcmd_rc=not_tried\n")
            check("install status parser: apt failure is not ok", not st["ok"] and st["apt_rc"] == "100")
            check("install status parser rejects a missing field",
                  raises(lambda: parse_install_status("apt_rc=0\n"), ValueError))
            g = parse_nvidia_smi_csv("NVIDIA A10, 570.148.08\n")
            check("nvidia-smi parser", g == [{"name": "NVIDIA A10", "driver_version": "570.148.08"}])
            check("nvidia-smi parser rejects empty output", raises(lambda: parse_nvidia_smi_csv(""), ValueError))
            check("jaxlib version read from jaxlib.__version__",
                  jaxlib_version(types.SimpleNamespace(__version__="0.6.0")) == ("0.6.0", "jaxlib.__version__"))
            check("jaxlib version read from the jaxlib.version module",
                  jaxlib_version(types.SimpleNamespace(version=types.SimpleNamespace(__version__="0.6.0")))
                  == ("0.6.0", "jaxlib.version.__version__"))
            jv = jaxlib_version()
            check("jaxlib version: an unimportable jaxlib is reported, not raised",
                  jv[0] is None and "not importable" in jv[1], str(jv))
            pv = package_versions()
            check("package versions: one entry per package; blocked imports recorded as errors; pandas never imported",
                  sorted(pv) == sorted(VERSION_PACKAGES) and pv["jax"]["import_error"] and pv["jaxlib"]["import_error"]
                  and pv["numpy"]["import_error"] and pv["pandas"]["import_error"] is None, str(pv))
            vb = {"jax": {"module_version": "0.6.0"}, "jaxlib": {"module_version": None, "dist_version": "0.6.0"},
                  "numpy": {"module_version": "1.26.4"}, "pyreadr": {"module_version": None}}
            va = json.loads(json.dumps(vb))
            va["pyreadr"] = {"module_version": "0.5.3"}
            check("version comparison: installing pyreadr alone changes nothing pinned",
                  pinned_versions_changed(vb, va) == [])
            va["numpy"] = {"module_version": "2.2.6"}
            check("version comparison: a numpy upgrade is caught",
                  pinned_versions_changed(vb, va) == ["numpy: 1.26.4 -> 2.2.6"], str(pinned_versions_changed(vb, va)))
            va = json.loads(json.dumps(vb))
            va["jax"] = {"module_version": None, "dist_version": None, "import_error": "planted"}
            check("version comparison: a jax that stops importing is caught",
                  pinned_versions_changed(vb, va) == ["jax: 0.6.0 -> None"])
            vo = td / "versions_run"
            rc_b = cmd_versions(vo, "before_pip", None)
            rc_same = cmd_versions(vo, "after_pip", str(vo / "logs" / "versions_before_pip.json"))
            planted_before = load_json(vo / "logs" / "versions_before_pip.json")
            planted_before["packages"]["numpy"] = {"module_version": "0.0.planted", "dist_version": None}
            dump_json(vo / "logs" / "versions_planted.json", planted_before)
            rc_diff = cmd_versions(vo, "after_pip", str(vo / "logs" / "versions_planted.json"))
            check("versions command: an unchanged reading exits 0; a planted numpy change exits 2",
                  rc_b == EXIT_OK and rc_same == EXIT_OK and rc_diff == EXIT_ENV, f"{rc_b} {rc_same} {rc_diff}")
            ng = td / "no_gpu"
            check("GPU check: when JAX cannot list a GPU it exits 3 and RUN_VALID.json says false",
                  cmd_gpu_check(ng) == EXIT_NO_GPU and RunState(ng).load()["run_valid"] is False)
            check("price parser reads 1.29", parse_money("PRICE_USD_PER_HOUR", {"PRICE_USD_PER_HOUR": "1.29"}) == 1.29)
            check("price parser rejects unset, text, zero and negative values",
                  all(raises(lambda v=v: parse_money("X", v), ValueError)
                      for v in ({}, {"X": ""}, {"X": "abc"}, {"X": "0"}, {"X": "-1"})))
            jl = td / "rows.jsonl"
            jl.write_text('{"a": 1}\n\n{"a": 2}\n')
            check("raw-row reader skips blank lines", [x["a"] for x in read_jsonl(jl)] == [1, 2])
            jl.write_text('{"a": 1}\n{"a": 2')
            check("raw-row reader refuses a truncated line in strict mode", raises(lambda: read_jsonl(jl), ValueError))
            check("raw-row reader keeps a truncated line aside in lenient mode",
                  len(read_jsonl(jl, strict=False)[1]) == 1)
            jl.write_text('{"backend": "gpu"}\n')
            check("a second measurement set into the same file is refused",
                  raises(lambda: refuse_if_rows(jl, lambda x: x.get("backend") == "gpu", "t"), ValueError)
                  and not raises(lambda: refuse_if_rows(jl, lambda x: x.get("backend") == "cpu", "t"), ValueError))

            # --- Periods, warm-up and forcing --------------------------------------------------
            dates = basin["dates"]
            i0, i1, w0 = case_window(dates, AIRGR_CASES[0])
            check("calibration warm-up: 1989-01-01, 365 days", dates[w0] == "1989-01-01" and i0 - w0 == 365)
            i0v, i1v, w0v = case_window(dates, AIRGR_CASES[2])
            check("validation warm-up: 1989-03-01, 365 days", dates[w0v] == "1989-03-01" and i0v - w0v == 365)
            ileap = dates.index("1992-03-01")
            wl = default_warmup_start(dates, ileap)
            check("leap-year warm-up: 1991-03-01, 366 days", dates[wl] == "1991-03-01" and ileap - wl == 366)
            check("no warm-up when the run starts on day one", default_warmup_start(dates, 0) == 0)
            fw = forcing_window(basin["P"], 2, N_DAYS)
            check("forcing rule: offset 2 starts on series day 2", fw[0] == basin["P"][2] and len(fw) == N_DAYS)
            check("forcing rule wraps around the record", forcing_window([1, 2, 3], 2, 4) == [3, 1, 2, 3])
            check("forcing detector passes three distinct seed windows",
                  not raises(lambda: check_forcing_windows(basin), Halt))
            check("forcing detector fires on constant forcing",
                  raises(lambda: check_forcing_windows({"P": [1.0] * 10000}), Halt, "DEGENERATE_FORCING"))

            params = draw_params(r, N_MAX, PARAM_DRAW_SEED)
            check("parameter draw: 2,684 distinct vectors inside the ranges",
                  len(params) == N_MAX and not raises(lambda: check_params(params, r), Halt))
            check("parameter draw is fixed by its seed", draw_params(r, 5, PARAM_DRAW_SEED) == params[:5])
            check("parameter detector fires on duplicates",
                  raises(lambda: check_params([params[0], params[0]], r), Halt, "DEGENERATE_PARAMS"))
            check("parameter detector fires outside a range",
                  raises(lambda: check_params([[1e9, 0, 1, 1]], r), Halt, "DEGENERATE_PARAMS"))

            # --- Model: planted rows and the page values ----------------------------------------
            pm = planted_model_checks()
            check("planted: unit-hydrograph ordinates sum to 1 within 1e-9", pm["uh_sum_pass"],
                  str(pm["uh_sum_max_abs_error"]))
            check("planted: zero rain gives zero quickflow", pm["zero_rain_pass"])
            check("planted: mass balance closes within 1e-6 mm over a planted year", pm["mass_balance_pass"],
                  str(pm["mass_balance_residual_mm"]))
            flows = {}
            for case in AIRGR_CASES:
                a0, a1, aw = case_window(dates, case)
                outs, _ = run_scalar(case["X"], basin["P"][aw:a1 + 1], basin["E"][aw:a1 + 1])
                flows[case["id"]] = [o["Q"] for o in outs][a0 - aw:]
                v = nse(flows[case["id"]], basin["Qmm"][a0:a1 + 1])
                check(f"build check, not an endpoint: float64 shared equations give {case['id']} NSE "
                      f"{case['page_nse']} +/- 0.02", in_band(v, case["page_nse"], 0.02), f"{v}")
            o1, o2 = SCALAR.uh_ordinates(2.45)
            check("UH1 has 3 nonzero ordinates and UH2 has 5 for X4 = 2.45",
                  sum(1 for x in o1 if x > 0) == 3 and sum(1 for x in o2 if x > 0) == 5)
            check("Fortran single-precision split B is used", B_SPLIT != 0.9 and abs(B_SPLIT - 0.9) < 1e-7)

            # --- Scores and detectors ------------------------------------------------------------
            check("NSE: perfect simulation gives 1", nse([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == 1.0)
            check("NSE: the observed mean gives 0", abs(nse([2.0, 2.0, 2.0], [1.0, 2.0, 3.0])) < 1e-15)
            check("NSE ignores a missing observation",
                  nse([1.0, 99.0, 3.0], [1.0, math.nan, 3.0]) == 1.0)
            check("MARE: 1% off everywhere gives 0.01", abs(mare([1.01, 2.02], [1.0, 2.0])[0] - 0.01) < 1e-12)
            check("MARE: a non-finite simulated day gives infinity", mare([math.nan, 1.0], [1.0, 1.0])[0] == math.inf)
            check("band edges are inclusive: 0.515 passes, 0.5151 fails",
                  in_band(0.515, 0.495, 0.02) and not in_band(0.5151, 0.495, 0.02))
            check("flow detector flags non-finite and all-zero flow",
                  flow_flags([0.0, 0.0])["all_zero_flow"] and flow_flags([math.nan, 1.0])["nonfinite_days"] == 1
                  and not flow_flags([0.1, 0.0])["all_zero_flow"])
            good = [{"ms": 3.0 + 0.01 * k} for k in range(30)]
            check("timing detector passes a cell with spread", not raises(lambda: check_timing_cell(good, "x"), Halt))
            check("planted zero-dispersion timing cell halts WRONG_VARIANCE_SOURCE",
                  raises(lambda: check_timing_cell([{"ms": 3.0}] * 30, "x"), Halt, "WRONG_VARIANCE_SOURCE"))
            check("timing detector halts on a non-positive or missing time",
                  raises(lambda: check_timing_cell([{"ms": 0.0}, {"ms": 1.0}], "x"), Halt, "DEGENERATE_TIMING")
                  and raises(lambda: check_timing_cell([{"ms": None}, {"ms": 1.0}], "x"), Halt, "DEGENERATE_TIMING"))
            pblocks = [{"iterations": 100, "ms": 300.0 + k} for k in range(10)]
            check("probe detector passes blocks with spread", not raises(lambda: check_probe_seed(pblocks, "p"), Halt))
            check("planted zero-dispersion probe blocks halt WRONG_VARIANCE_SOURCE",
                  raises(lambda: check_probe_seed([{"iterations": 100, "ms": 5.0}] * 10, "p"), Halt,
                         "WRONG_VARIANCE_SOURCE"))
            check("probe detector halts on an empty block",
                  raises(lambda: check_probe_seed([{"iterations": 0, "ms": 5.0}], "p"), Halt, "DEGENERATE_PROBE"))

            # --- Endpoint arithmetic on planted numbers ------------------------------------------
            ok5, d5 = check_i5()
            check("I5 planted: ms 2 -> 0.2222 h, ms 20 -> 2.2222 h, speedups 13.5 and 1.35", ok5, str(d5))
            ok6, d6 = check_i6()
            check("I6 planted: 5.9 h pass, 6.1 h 'Stop and replan', later records and rows run_valid false", ok6,
                  str(d6))
            ok7, d7 = check_i7()
            check("I7 planted: 3.2655e8 chain-steps per second; equal times give ratio 10", ok7, str(d7))
            check("card decision: 0.5 h with speedup 25 is if_lever", card_decision(0.5, 25.0) == "if_lever")
            check("card decision: exactly 1 h is if_not", card_decision(1.0, 100.0) == "if_not")
            check("card decision: speedup exactly 20 below 1 h is if_lever", card_decision(0.9, 20.0) == "if_lever")
            check("card decision: speedup 19.9 is if_not", card_decision(0.1, 19.9) == "if_not")
            check("card guess bands are inclusive",
                  guess_band(0.67, E3_BAND) == "HOLDS" and guess_band(6.0, E3_BAND) == "HOLDS"
                  and guess_band(6.01, E3_BAND) == "REFUTED" and guess_band(0.9, E4_BAND) == "REFUTED")
            check("gate: exactly 6 h passes", gate_decision(6.0) == "pass")
            check("scaling reading: ratio 7.9 saturates, 12.1 above, 8 and 12 linear",
                  scaling_label(7.9) == "GPU saturates below 2,684 chains" and scaling_label(12.1) == "above linear"
                  and scaling_label(8.0) == "linear" and scaling_label(12.0) == "linear")
            ok, why = guard_verdict(3600.0, 1800.0, 1.29, 5.0, 0.0, None, 60.0)
            check("cost guard: 1 h up plus 0.5 h at USD 1.29/h stays under USD 5", ok, why)
            ok, why = guard_verdict(3.5 * 3600.0, 0.3 * 3600.0, 1.29, 5.0, 0.0, None, 60.0)
            check("cost guard: 3.5 h up plus 0.3 h at USD 1.29/h stops before USD 5", not ok, why)
            ok, why = guard_verdict(600.0, 60.0, 1.29, 5.0, 1000.0, 1050.0, 60.0)
            check("time guard: 50 s left for a 60 s step stops", not ok, why)
            check("projected spend arithmetic: (1 h + 0.5 h + 0.1 h) x 1.29 = 2.064",
                  abs(projected_usd(3600.0, 1800.0, 1.29) - 2.064) < 1e-12)

            # --- Extract stage on the committed files, into a scratch folder ---------------------
            ex = td / "extract_run"
            stage_extract(ex)
            pe = paths(ex)
            check("extract writes basin, ranges, parameters, R script and decision rules",
                  all(pe[k].exists() for k in ("basin", "ranges", "params", "rscript", "rules")))
            check("extract's parameter file holds 2,684 vectors", load_json(pe["params"])["n"] == N_MAX)
            rs = pe["rscript"].read_text()
            check("R script: default warm-up and states, NSE on Qmm, three cases, page date selection",
                  "IndPeriod_WarmUp" not in rs.split("CreateRunOptions(")[1].split(")")[0]
                  and "ErrorCrit_NSE" in rs and rs.count("list(id =") == 3 and "%d/%m/%Y %H:%M" in rs
                  and "IniStates" not in rs)

            # --- Planted pipelines: records, validity and labels ---------------------------------
            def planted_airgr(nse_anchor=None):
                cases = []
                for case in AIRGR_CASES:
                    a0, a1, aw = case_window(dates, case)
                    v = nse(flows[case["id"]], basin["Qmm"][a0:a1 + 1])
                    if nse_anchor is not None and case["id"] == "anchor_cal":
                        v = nse_anchor
                    cases.append({"id": case["id"], "set": case["set"], "X": list(case["X"]), "warmup_n": a0 - aw,
                                  "warmup_first": dates[aw], "ini_res_levels": [0.3, 0.5, None, None], "nse": v,
                                  "crit_name": "NSE[Q]", "dates": dates[a0:a1 + 1], "qsim": flows[case["id"]],
                                  "qobs": [None if math.isnan(x) else x for x in basin["Qmm"][a0:a1 + 1]]})
                return parse_airgr_json(json.dumps({"r_version": "planted", "airgr_version": "1.7.9", "cases": cases}))

            check("airGR output parser accepts the planted three-case output", planted_airgr()["by_id"])
            bad = json.loads(json.dumps({"r_version": "x", "airgr_version": "y", "cases": []}))
            check("airGR output parser rejects a missing case",
                  raises(lambda: parse_airgr_json(json.dumps(bad)), ValueError))

            def planted_pipeline(name, airgr_mode="ok", gpu_ms=3.0, cpu_ms=90.0, ov_g=1.2, ov_c=1.1,
                                 stop_after_gpu=False, flat=False):
                o = td / name
                RunState(o).ensure()
                if airgr_mode == "install_fails":
                    (o / "logs").mkdir(parents=True)
                    (o / "logs" / "apt_r.log").write_text("E: Unable to locate package r-base-core\n")
                    (o / "airgr_install_status.txt").write_text("apt_rc=100\nrcmd_rc=not_tried\n")
                    ag = None
                    gen_anchor_airgr(o)  # the real stage; with a failed install it never starts R
                else:
                    ag = planted_airgr(0.40 if airgr_mode == "anchor_fails" else None)
                    write_e1_i1(o, ag, None)
                for b in ("gpu", "cpu"):
                    for case in AIRGR_CASES:
                        a0, a1, aw = case_window(dates, case)
                        q = [x * (1.0 + 2e-6) for x in flows[case["id"]]]
                        row = make_anchor_jax_row(b, case, q, dates[a0:a1 + 1], basin["Qmm"][a0:a1 + 1],
                                                  (dates[aw], a0 - aw), ag["by_id"][case["id"]] if ag else None,
                                                  "planted")
                        write_row(o, "anchor_rows.jsonl", row)
                write_e2_i2(o, ag is not None)
                for b, base in (("gpu", gpu_ms), ("cpu", cpu_ms)):
                    write_row(o, "timer_rows.jsonl", {"control": "I3", "backend": b, "ms": 100.3}, timing=True)
                    for nd, scale in ((SHORT_DAYS, 0.1), (N_DAYS, 1.0)):
                        for rep in range(-1, REPEATS):
                            write_row(o, "timer_rows.jsonl", {"control": "I4", "backend": b, "n_days": nd,
                                                              "repeat": rep, "warmup": rep < 0,
                                                              "ms": base * scale * (1 + 0.001 * rep)}, timing=True)
                write_i3_i4(o)
                for b, base, ov in (("gpu", gpu_ms, ov_g), ("cpu", cpu_ms, ov_c)):
                    if stop_after_gpu and b == "cpu":
                        break
                    for n in SIZES:
                        bms = base if b == "gpu" else base * n / N_MAX
                        for s in SEEDS:
                            for rep in range(REPEATS):
                                ms = bms if flat else bms * (1 + 0.002 * ((s * 7 + rep) % 5 - 2))
                                write_row(o, "timing_rows.jsonl", {
                                    "arm": f"{b}_timing", "backend": b, "n_chains": n, "n_days": N_DAYS, "seed": s,
                                    "repeat": rep, "ms": ms, "warmup": False, "params_mode": "distinct",
                                    "instance_type": "planted", "gpu_name": "planted GPU"}, timing=True)
                    for s in SEEDS:
                        for blk in range(PROBE_ITERS // PROBE_BLOCK):
                            write_row(o, "probe_blocks.jsonl", {
                                "arm": "overhead_probe", "backend": b, "seed": s, "block": blk,
                                "iterations": PROBE_BLOCK, "n_chains": N_MAX, "warmup": False, "accepted": 10,
                                "ms": base * ov * PROBE_BLOCK * (1 + 0.001 * (blk - 4.5))}, timing=True)
                if stop_after_gpu:
                    stamp_incomplete(o, "planted early stop")
                stage_endpoints(o)
                return o

            def recs(o):
                return {p.stem.split("id-")[1].split("_")[0]: load_json(p) for p in (o / "records").glob("*.json")}

            def rows_of(o, name):
                return read_jsonl(o / "raw" / name)

            ids = ["E1", "E2", "E3", "E4", "E5", "E6", "E7", "I1", "I2", "I3", "I4", "I5", "I6", "I7"]
            check("summary lists the same 14 cells as the records", list(ALL_IDS) == ids)

            def summary_matches(o):
                """The summary decides nothing: each decision and validity equals the record's own."""
                sm = load_json(summary_path(o))
                rc_ = recs(o)
                same = sorted(sm["decisions"]) == sorted(rc_) and all(
                    sm["decisions"][k]["decision"] == rc_[k]["decision"]
                    and sm["decisions"][k]["run_valid"] == rc_[k]["values"]["run_valid"]
                    and sm["decisions"][k]["run_valid"] is not None for k in rc_)
                return sm, same

            o = planted_pipeline("all_good")
            rc = recs(o)
            check("good run: one record per endpoint and control, 14 in all", sorted(rc) == sorted(ids), str(sorted(rc)))
            check("good run: every record has run_valid true",
                  all(rc[k]["values"]["run_valid"] is True for k in rc),
                  str({k: rc[k]["values"]["run_valid"] for k in rc}))
            check("good run: every record carries a decision rule and a decision",
                  all(rc[k]["decision_rule"] and rc[k]["decision"] for k in rc))
            check("good run: anchors and controls pass",
                  all(rc[k]["decision"] == "PASS" for k in ("E1", "E2", "I1", "I2", "I3", "I4", "I5", "I6", "I7")),
                  str({k: rc[k]["decision"] for k in rc}))
            check("good run: E3 median 3.0 ms holds", rc["E3"]["decision"] == "HOLDS"
                  and abs(rc["E3"]["values"]["batched_forward_ms"] - 3.0) < 1e-9, rc["E3"]["decision"])
            e5v = rc["E5"]["values"]
            check("good run: overheads 1.2 (GPU) and 1.1 (CPU) recovered from probe blocks",
                  abs(e5v["overhead_gpu"] - 1.2) < 1e-3 and abs(e5v["overhead_cpu"] - 1.1) < 1e-3,
                  f"{e5v['overhead_gpu']} {e5v['overhead_cpu']}")
            check("good run: main_run_hours 0.1, CPU hours 2.75, speedup 27.5, if_lever",
                  abs(e5v["main_run_hours"] - 0.1) < 1e-3 and abs(e5v["cpu_671_hours"] - 2.75) < 3e-3
                  and rc["E5"]["decision"] == "if_lever" and rc["E4"]["decision"] == "HOLDS",
                  f"{e5v['main_run_hours']} {e5v['cpu_671_hours']} {rc['E5']['decision']}")
            check("good run: sensitivity line with overhead 4 is present and labelled",
                  e5v["sensitivity_overhead_4"]["overhead"] == 4.0
                  and "sensitivity" in e5v["sensitivity_overhead_4"]["label"])
            check("good run: gate passes and scaling reads linear",
                  rc["E6"]["decision"] == "pass" and rc["E7"]["decision"] == "REPORT_ONLY: linear", rc["E7"]["decision"])
            check("good run: timing records carry instance type and GPU name",
                  rc["E3"]["values"]["hardware"]["instance_type"] == "planted"
                  and rc["E3"]["values"]["hardware"]["gpu_name"] == "planted GPU")
            check("good run: records keep input hashes", any(i.get("sha256") for i in rc["E1"]["inputs"]))
            check("good run: RUN_VALID.json says valid", RunState(o).load()["run_valid"] is True)
            sm, same = summary_matches(o)
            check("summary after the endpoints stage: all 14 decisions restated exactly, none missing",
                  same and sm["records_missing"] == [] and sm["records_present"] == 14, str(sm.get("records_missing")))
            check("summary on a good run: run_valid true, no labels, no void reasons",
                  sm["run_valid"] is True and sm["labels"] == [] and sm["void_reasons"] == [] and not sm["incomplete"])
            e5s = sm["decisions"]["E5"]["values_restated"]
            check("summary restates headline numbers verbatim, the sensitivity line included",
                  e5s["main_run_hours"] == rc["E5"]["values"]["main_run_hours"]
                  and e5s["sensitivity_overhead_4"]["overhead"] == 4.0
                  and sm["decisions"]["E3"]["values_restated"]["hardware"]["gpu_name"] == "planted GPU")
            check("summary: the launcher's fetch pattern '*summary*.json' finds it and nothing else",
                  [x.name for x in o.glob("*summary*.json")] == [SUMMARY_FILE])

            o = planted_pipeline("anchor_fails", airgr_mode="anchor_fails")
            rc = recs(o)
            check("failed anchor: E1 FAIL", rc["E1"]["decision"] == "FAIL")
            later = [k for k in ids if k != "E1"]
            check("failed anchor: every record written after it has run_valid false",
                  all(rc[k]["values"]["run_valid"] is False for k in later + ["E1"]))
            tr = rows_of(o, "timing_rows.jsonl")
            check("failed anchor: timing rows say 'descriptive only; anchor failed' and run_valid false",
                  tr and all(LABEL_ANCHOR_FAILED in r["run_labels"] and r["run_valid"] is False for r in tr))
            check("failed anchor: timing records carry the same label",
                  LABEL_ANCHOR_FAILED in rc["E5"]["values"]["run_labels"])
            sm, same = summary_matches(o)
            check("summary after a failed anchor: run_valid false, timing label restated, decisions match",
                  same and sm["run_valid"] is False and LABEL_ANCHOR_FAILED in sm["timing_labels"]
                  and sm["decisions"]["E1"]["decision"] == "FAIL")

            o = planted_pipeline("r_install_fails", airgr_mode="install_fails")
            rc = recs(o)
            check("failed R install: E1 NOT_RUN with the error text",
                  rc["E1"]["decision"] == "NOT_RUN" and "Unable to locate package" in rc["E1"]["values"]["error_text"])
            check("failed R install: E2 decided on the page value alone, labelled",
                  rc["E2"]["decision"] == f"PASS ({LABEL_E2_PAGE_ONLY})", rc["E2"]["decision"])
            check("failed R install: every record carries 'anchor by page value'",
                  all(LABEL_PAGE_ONLY_RUN in rc[k]["values"]["run_labels"] for k in rc))
            check("failed R install: every raw row carries 'anchor by page value'",
                  all(LABEL_PAGE_ONLY_RUN in r["run_labels"] for r in rows_of(o, "timing_rows.jsonl")))
            sm, same = summary_matches(o)
            check("summary after a failed R install: 'anchor by page value' and E1 NOT_RUN restated",
                  same and LABEL_PAGE_ONLY_RUN in sm["labels"] and sm["decisions"]["E1"]["decision"] == "NOT_RUN")

            o = planted_pipeline("gate_fails", gpu_ms=200.0, cpu_ms=900.0)
            rc = recs(o)
            check("failed gate: E6 reads 'Stop and replan' at main_run_hours 6.67",
                  rc["E6"]["decision"] == GATE_STOP_TEXT, rc["E6"]["decision"])
            check("failed gate: records written before it stay valid, E6 and E7 are run_valid false",
                  rc["E5"]["values"]["run_valid"] is True and rc["E6"]["values"]["run_valid"] is False
                  and rc["E7"]["values"]["run_valid"] is False)
            check("failed gate: RUN_VALID.json says invalid", RunState(o).load()["run_valid"] is False)
            sm, same = summary_matches(o)
            check("summary after a failed gate: 'Stop and replan' restated, run_valid false",
                  same and sm["run_valid"] is False and sm["decisions"]["E6"]["decision"] == GATE_STOP_TEXT)

            o = planted_pipeline("early_stop", stop_after_gpu=True)
            rc = recs(o)
            tr = rows_of(o, "timing_rows.jsonl")
            check("early stop: finished rows relabelled 'incomplete run: descriptive only, no verdict'",
                  tr and all(LABEL_INCOMPLETE in r["run_labels"] and r["run_valid"] is False for r in tr))
            check("early stop: records written before the stop relabelled",
                  LABEL_INCOMPLETE in rc["E1"]["values"]["run_labels"] and rc["E1"]["values"]["run_valid"] is False)
            check("early stop: verdict endpoints give no verdict",
                  all(rc[k]["decision"].startswith("NO_VERDICT") for k in ("E3", "E4", "E5")),
                  str({k: rc[k]["decision"] for k in ("E3", "E4", "E5")}))
            sm, same = summary_matches(o)
            check("summary after an early stop: incomplete, labelled, run_valid false, decisions match",
                  same and sm["incomplete"] is True and LABEL_INCOMPLETE in sm["labels"] and sm["run_valid"] is False)

            check("planted zero-dispersion run halts WRONG_VARIANCE_SOURCE at endpoints",
                  raises(lambda: planted_pipeline("zero_dispersion", flat=True), Halt, "WRONG_VARIANCE_SOURCE"))
            rc = recs(td / "zero_dispersion")
            check("halted run: timing records still written, marked HALTED with no verdict, run_valid false",
                  all(rc[k]["decision"].replace("REPORT_ONLY: ", "").startswith("HALTED WRONG_VARIANCE_SOURCE")
                      and rc[k]["values"]["run_valid"] is False for k in ("E3", "E4", "E5", "E6", "E7")),
                  str({k: rc[k]["decision"][:40] for k in ("E3", "E7")}))
            sm, same = summary_matches(td / "zero_dispersion")
            check("summary after a halt: written before the halt propagates, decisions match records",
                  same and sm["run_valid"] is False and sm["decisions"]["E3"]["decision"].startswith("HALTED"))

            o = td / "stopped_early"
            rc_stop = main(["stop", "--reason", "planted stop before any stage", "--out", str(o)])
            sm = load_json(summary_path(o)) if summary_path(o).exists() else {}
            check("summary after a stop before any stage: written, run_valid false, all 14 listed missing",
                  rc_stop == EXIT_OK and sm.get("run_valid") is False and sm.get("incomplete") is True
                  and sm.get("records_missing") == ids and sm.get("decisions") == {})
            rc_end = main(["endpoints", "--out", str(o)])
            rc_sum = main(["summary", "--out", str(o)])
            rc = recs(o)
            sm, same = summary_matches(o)
            check("summary after the follow-up endpoints run: 14 records restated, none missing",
                  rc_end == EXIT_OK and rc_sum == EXIT_OK and same and sm["records_missing"] == [])
            check("stop before any stage: all 14 cells still get a record", sorted(rc) == sorted(ids), str(sorted(rc)))
            check("stop before any stage: missing gate records say NOT_RUN",
                  rc["E1"]["decision"].startswith("NOT_RUN") and rc["I4"]["decision"].startswith("NOT_RUN"))

            # --- Wording: same-box repeats are never called replication -------------------------
            word = "repl" + "icat"
            texts = [p.read_text().lower() for p in td.rglob("*") if p.is_file() and p.suffix in (".json", ".jsonl")]
            texts += [json.dumps(RULES).lower(), R_SCRIPT.lower(), LABEL_INCOMPLETE.lower()]
            check("no output calls same-box repeats replication", not any(word in t for t in texts))
    except Exception as e:  # noqa: BLE001  a crash is a failure line, never a silent pass
        traceback.print_exc()
        check(f"selftest ran to its end without an exception ({type(e).__name__}: {e})", False)

    n_fail = sum(1 for _, ok, _ in results if not ok)
    print(f"selftest: {len(results) - n_fail}/{len(results)} checks passed in {time.time() - t_start:.1f} s; "
          + ("PASS" if n_fail == 0 else f"{n_fail} FAILURES"), flush=True)
    return 0 if n_fail == 0 else 1


# ----------------------------------------------------------------------------------------------
# Command line.
# ----------------------------------------------------------------------------------------------
PARTS = ("anchor_airgr", "anchor_jax", "timers", "timing", "probe")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Runner for measurement m1 (see the module docstring).")
    ap.add_argument("--selftest", action="store_true", help="standard-library selftest; no JAX, no R")
    sub = ap.add_subparsers(dest="cmd")
    for name in ("extract", "endpoints", "gpu-check", "summary"):
        sub.add_parser(name).add_argument("--out", default=str(DEFAULT_OUT))
    v = sub.add_parser("versions")
    v.add_argument("--label", required=True, choices=("before_pip", "after_pip", "env"))
    v.add_argument("--compare-to", default=None)
    v.add_argument("--out", default=str(DEFAULT_OUT))
    g = sub.add_parser("generate")
    g.add_argument("--part", required=True, choices=PARTS)
    g.add_argument("--backend", choices=("gpu", "cpu"))
    g.add_argument("--out", default=str(DEFAULT_OUT))
    gu = sub.add_parser("guard")
    gu.add_argument("--stage", required=True, choices=sorted(STAGE_EST_H))
    gu.add_argument("--out", default=str(DEFAULT_OUT))
    for name in ("stop", "void"):
        p = sub.add_parser(name)
        p.add_argument("--reason", required=True)
        p.add_argument("--out", default=str(DEFAULT_OUT))
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if args.cmd is None:
        ap.print_help()
        return EXIT_ENV
    out = Path(args.out)
    if args.cmd == "guard":
        return cmd_guard(out, args.stage)
    if args.cmd == "gpu-check":
        return cmd_gpu_check(out)
    if args.cmd == "stop":
        stamp_incomplete(out, args.reason)
        write_summary(out)
        return EXIT_OK
    if args.cmd == "summary":
        write_summary(out)
        return EXIT_OK
    if args.cmd == "versions":
        return cmd_versions(out, args.label, args.compare_to)
    if args.cmd == "void":
        RunState(out).void(args.reason)
        return EXIT_OK
    try:
        if args.cmd == "extract":
            stage_extract(out)
        elif args.cmd == "endpoints":
            stage_endpoints(out)
        elif args.cmd == "generate":
            if args.part in ("timing", "probe") and args.backend is None:
                raise SystemExit("--backend is required for this part")
            {"anchor_airgr": lambda: gen_anchor_airgr(out), "anchor_jax": lambda: gen_anchor_jax(out),
             "timers": lambda: gen_timers(out), "timing": lambda: gen_timing(out, args.backend),
             "probe": lambda: gen_probe(out, args.backend)}[args.part]()
    except StopRun as e:
        log(f"[guard] clean stop inside the stage: {e}")
        stamp_incomplete(out, f"stopped by the cost or time guard: {e}")
        write_summary(out)
        return EXIT_STOPPED
    except Halt as e:
        log(f"[halt] {e.code}: {e.detail}")
        RunState(out).void(f"{e.code}: {e.detail}")
        stamp_incomplete(out, f"halted: {e.code}")
        write_summary(out)
        return EXIT_HALT
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        return EXIT_CRASH
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
