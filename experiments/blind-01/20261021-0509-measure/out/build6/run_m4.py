#!/usr/bin/env python3
"""Measure four cost inputs of one design card on a single rented GPU box (tag m4).

WHAT THIS PROGRAM IS FOR. A design card costs out a protein-structure study. Four
numbers carry that cost: how long one AlphaFold-Multimer prediction takes (hours
per run), how fast a molecular-dynamics simulation runs (nanoseconds of simulated
time per day), how many hours of side work each protein pair needs, and how much
disk one full grid of runs would use. The card asserts those four numbers. Nobody
measured them. This program measures them once, on the card's own protocol, and
calls each one PASS, FAIL or VOID against the band the card itself implies.

WHAT IT DOES NOT DO. It does not run the card's study. It runs three stand-in
protein pairs, not the card's nine. One graphics processor, one box. So the
result decides the stand-in protocol only, and every record says so.

THE ANCHOR COMES FIRST. Before any input is measured, the docking tool must
re-dock a known complex (receptor AAVR-PKD2 onto capsid AAV2) and land close to
the published structure, entry 6IHB of the Protein Data Bank. If it misses, every
input is written VOID and the whole run is marked invalid.

STAGES, EACH RUNNABLE ALONE (state is kept in results_m4/out/run_state.json):

    python3 run_m4.py --stage extract     install, download, check the tools, run
                                          the timer and empty-input controls
    python3 run_m4.py --stage generate    anchor, then the four measurements
    python3 run_m4.py --stage endpoints   write the four decisions and the summary
    python3 run_m4.py --stage all         all of the above, in order
    python3 run_m4.py --selftest          standard library only; no GPU, no network

EXIT CODES. 0 every input decided by measurement. 2 broken infrastructure or a
broken harness. 3 a guard, a stage ceiling or a timeout stopped the run with some
input unmeasured. 4 the anchor missed.

VALIDITY. Every record carries a run_valid field. An anchor miss, a failed timer
check or broken infrastructure sets it false, and it stays false in every record
written afterwards -- in the per-input files, not only in the summary. A guard
stop does NOT set it false: it voids the unfinished inputs and keeps the finished
ones.

LANGUAGE. Repeats on this one box are repeats, never replication: one box cannot
replicate itself.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import signal
import statistics
import subprocess
import sys
import time
from pathlib import Path

TAG = "m4"
HERE = Path(__file__).resolve().parent
OUT_DIR = Path(os.environ.get("M4_OUT_DIR") or (HERE / f"results_{TAG}" / "out"))
STATE_PATH_NAME = "run_state.json"

# ---------------------------------------------------------------------------
# The card's four inputs. Value, unit and band come from the design record and
# are not recomputed here; they are the thing being tested, so they are frozen.
# ---------------------------------------------------------------------------

CARDS = {
    "C1": {
        "name": "AlphaFold-Multimer hours per prediction run (af2_h_per_run)",
        "unit": "hours per prediction run",
        "card_value": 0.5,
        "band": [0.2, 1.25],
    },
    "C2": {
        "name": "molecular-dynamics speed on an A100 (md_ns_per_day_a100)",
        "unit": "nanoseconds of simulated time per day",
        "card_value": 129,
        "band": [51.6, 322.5],
    },
    "C3": {
        "name": "auxiliary hours per protein pair (aux_h_per_pair)",
        "unit": "hours per pair",
        "card_value": 1,
        "band": [0.3333, 3],
    },
    "C4": {
        "name": "storage for the full grid of runs (n_storage_gib)",
        "unit": "gibibytes",
        "card_value": 200,
        "band": [66.67, 600],
    },
}

# The card's own gate. It is applied to the AlphaFold timing only; the run never
# branches on it. The other inputs say so in their own records.
GATE_CEILING_H = 1.0
GATE_ELSE = (
    "take the docking-plus-MD fallback line with one AlphaFold-Multimer seed per "
    "pair, or move the grid to 12 pairs"
)
GATE_NOT_APPLICABLE = "not applicable: the card's gate is on af2_h_per_run"

# ---------------------------------------------------------------------------
# Labels that must appear verbatim. A label is a plain sentence a later reader
# needs in order to know what the number is and is not.
# ---------------------------------------------------------------------------

LABEL_UNMEASURED = "unmeasured, not holding"
LABEL_INCOMPLETE = "incomplete run: unmeasured inputs are VOID, not holding"
LABEL_STANDIN = "stand-in pairs built from 6IHB chains, not the card's pairs"
LABEL_ONE_GPU = "one GPU; one box; 3 pairs; no multi-GPU scaling"
LABEL_NO_MSA = (
    "no-MSA: alignment search time excluded; understates the card's setting"
)
LABEL_AUX_READING = "producer's reading of aux hours"
LABEL_STORAGE = "linear in runs; intermediates kept; MD length 0.5 ns"
LABEL_NOT_A100 = "not an A100"
LABEL_ZERO_SPREAD = "zero spread across seeds: wrong variance source"
LABEL_SPREAD_HIGH = "seed spread high; mean is uncertain"
LABEL_OVERHEAD_SUBTRACTED = "setup overhead subtracted"
LABEL_RATE_DISAGREE = "engine rate and wall-clock disagree"
LABEL_SP_WHOLE_CHAIN = (
    "serial-versus-parallel RMSD is over the whole receptor chain"
)
LABEL_SAME_BOX = (
    "serial and parallel are repeats on one box, not replication"
)
LABEL_TIMEOUT_DEFAULT = "REMOTE_TIMEOUT not forwarded; default 7200 used"
LABEL_STANDIN_ONLY = (
    "this run decides the stand-in protocol only, not the card's own grid"
)

# The detector token for a dispersion failure. Repeated timings that agree to the
# last digit are not measurements of run-to-run variation; they mean the harness
# timed the same cached thing three times.
WRONG_VARIANCE_SOURCE = "WRONG_VARIANCE_SOURCE"

# ---------------------------------------------------------------------------
# Caps and ceilings, in seconds and dollars. Every number here is the gate's.
# ---------------------------------------------------------------------------

DEFAULT_REMOTE_TIMEOUT = 7200
DEFAULT_BUDGET_LEFT_USD = 5.0
DEFAULT_PRICE_USD_PER_HOUR = 1.99

FETCH_MARGIN_S = 400          # kept back so results can be written and fetched
ENDPOINTS_SLOT_S = 100        # kept back so the decisions always get written
OUTER_KILL_BACKOFF_S = 600    # outer kill fires at stop_at minus this
INNER_TOOL_BACKOFF_S = 700    # inner tool stop fires first, 100 s earlier

# The timer-and-anchor allowance is one shared 700 seconds, not 700 each. The
# storage stage has no ceiling of its own: it is bounded only by the time left,
# because the gate's ceilings already account for the whole 7,200 seconds.
STAGE_CEILING_S = {
    "install": 1800,          # install, downloads and the smoke check
    "controls": 700,          # shared with the anchor
    "anchor": 700,            # shared with the timer and empty-input controls
    "aux": 600,               # all docking and interface analysis
    "af2": 2000,
    "md": 1600,
    "storage": None,
    "endpoints": ENDPOINTS_SLOT_S,
}
STAGE_CEILING_GROUP = {"controls": "controls_anchor", "anchor": "controls_anchor"}
CEILING_SUM_S = 1800 + 700 + 600 + 2000 + 1600 + ENDPOINTS_SLOT_S + FETCH_MARGIN_S
PER_PAIR_DOCK_CEILING_S = 250
PER_COMPLEX_MD_CEILING_S = 600

# Minimum evidence below which an input is VOID rather than decided.
MIN_AF2_RUNS = 3
MIN_AF2_PAIRS = 3
MIN_MD_COMPLEXES = 2
MIN_AUX_PAIRS = 2

# Protocol constants from the design record.
AF2_SEEDS = [0, 1, 2]
AF2_MODELS = 5
AF2_RECYCLES = 20
MD_TIMESTEP_FS = 2.0
MD_PRODUCTION_NS = 0.5
MD_VELOCITY_SEED = 0
MD_ATOMS_MIN = 120000
MD_ATOMS_MAX = 180000
GRID_RUNS = 216
GRID_RUNS_DOUBLE = 432
CONTACT_CUTOFF_A = 4.5
ANCHOR_OVERLAP_MIN = 0.50
ANCHOR_RMSD_MAX_A = 5.0
ANCHOR_SERIAL_PARALLEL_RMSD_MAX_A = 2.0
SLEEP_CHECK_S = 60.0
SLEEP_CHECK_TOLERANCE = 0.05
EMPTY_RUN_MAX_S = 2.0
EMPTY_RUN_MAX_BYTES = 1024 * 1024
SPREAD_HIGH_RELATIVE_SD = 0.50
MARGINAL_FRACTION = 0.10
RATE_DISAGREEMENT_FRACTION = 0.05

# ---------------------------------------------------------------------------
# Tools. Every package is pinned. The smoke check in the install stage decides
# whether they work; nothing here is trusted from memory.
# ---------------------------------------------------------------------------

APT_PACKAGES = ["aria2", "ca-certificates"]

PIP_INSTALL_GROUPS = [
    # Order matters: the prediction stack first, then the exact JAX build it
    # needs, so the resolver cannot leave a JAX behind that it cannot import.
    ["numpy==1.26.4"],
    ["colabfold==1.5.5"],
    ["jax[cuda12]==0.4.35"],
    # The OpenMM wheel on the Python package index carries the CUDA platform;
    # no substitute engine is used.
    ["openmm==8.2.0", "pdbfixer==1.10"],
    ["lightdock==0.9.4"],
]

DOWNLOADS = {
    "pdb_6ihb": "https://files.rcsb.org/download/6IHB.pdb",
    "alphafold_params": (
        "https://storage.googleapis.com/alphafold/alphafold_params_2022-12-06.tar"
    ),
}
ALLOWED_DOWNLOAD_HOSTS = {"files.rcsb.org", "storage.googleapis.com"}

SECRET_ENV_NAMES = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")
NAMED_NON_SECRET_ENV = (
    "PRICE_USD_PER_HOUR",
    "BUDGET_LEFT_USD",
    "REMOTE_TIMEOUT",
    "INSTANCE_TYPE",
    "LAMBDA_INSTANCE_ID",
    "GIT_COMMIT",
    "CUDA_VISIBLE_DEVICES",
    "M4_T0",
)


# ===========================================================================
# Small helpers
# ===========================================================================


def log(msg: str) -> None:
    """One progress line. A silent hour reads as a hang to the operator."""
    print(f"[{TAG}] {msg}", flush=True)


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def atomic_write_text(path, text: str) -> None:
    """Write through a temporary file and rename, so a killed run never leaves
    a half-written record that still parses as JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text)
    os.replace(tmp, path)


def atomic_write_json(path, obj) -> None:
    atomic_write_text(path, json.dumps(obj, indent=2, sort_keys=True))


def child_env(source=None) -> dict:
    """A copy of the environment for a child process, with the download tokens
    removed. The tokens are for the downloads and for nothing else."""
    env = dict(os.environ if source is None else source)
    for name in SECRET_ENV_NAMES:
        env.pop(name, None)
    return env


def read_float_env(name: str, default: float):
    """Read one number from the environment. An unset or unreadable value gives
    the default and says so, rather than guessing a larger cap."""
    raw = os.environ.get(name, "")
    if raw is None or str(raw).strip() == "":
        return default, True
    try:
        return float(str(raw).strip()), False
    except ValueError:
        return default, True


# ===========================================================================
# Run state: the one place that knows what has happened so far
# ===========================================================================


def new_state(out_dir=None) -> dict:
    out_dir = Path(out_dir or OUT_DIR)
    t0_env, _ = read_float_env("M4_T0", 0.0)
    return {
        "tag": TAG,
        "out_dir": str(out_dir),
        "t0": t0_env if t0_env > 0 else time.time(),
        "run_valid": True,
        "run_valid_voided_by": None,
        "stages_done": [],
        "stops": [],              # one entry per guard, ceiling or timeout stop
        "unmeasured": [],         # input ids with no measurement
        "labels": [],             # run-wide labels, e.g. the overhead subtraction
        "measurements": {},       # raw per-input results, before the decisions
        "machine": {},            # instance, GPU, engine versions; filled on box
        "process_groups": [],     # group ids of every tool started
        "caps": {},
        "exit_code": 0,
    }


def state_path(state) -> Path:
    return Path(state["out_dir"]) / STATE_PATH_NAME


def save_state(state) -> None:
    atomic_write_json(state_path(state), state)


def load_state(out_dir=None) -> dict:
    out_dir = Path(out_dir or OUT_DIR)
    p = out_dir / STATE_PATH_NAME
    if p.exists():
        try:
            return json.loads(p.read_text())
        except ValueError:
            pass
    return new_state(out_dir)


def elapsed_s(state) -> float:
    return max(0.0, time.time() - float(state["t0"]))


def stopped_early(state) -> bool:
    """True once any guard, ceiling or timeout stop has been recorded."""
    return bool(state.get("stops"))


def void_run(state, reason: str) -> None:
    """Mark the whole run invalid. Only an anchor miss, a failed timer check or
    broken infrastructure may call this. It never un-sets itself."""
    if state["run_valid"]:
        state["run_valid"] = False
        state["run_valid_voided_by"] = reason
    save_state(state)


def record_stop(state, stage: str, kind: str, detail: str) -> None:
    """A guard, ceiling or timeout stop. This does not invalidate the run; it
    voids the inputs that never got measured."""
    state["stops"].append({"stage": stage, "kind": kind, "detail": detail,
                           "elapsed_s": round(elapsed_s(state), 1)})
    save_state(state)


class GuardStop(Exception):
    """Raised when a stage must not start or must stop: time, cost or ceiling."""

    def __init__(self, stage: str, kind: str, detail: str):
        super().__init__(f"{stage}: {kind}: {detail}")
        self.stage = stage
        self.kind = kind
        self.detail = detail


class FailStop(Exception):
    """Raised when infrastructure or the harness is broken, or the anchor missed.
    Exit code 2 or 4; both set run_valid false."""

    def __init__(self, stage: str, detail: str, code: int = 2):
        super().__init__(f"{stage}: {detail}")
        self.stage = stage
        self.detail = detail
        self.code = code


# ===========================================================================
# Cost and time arithmetic
# ===========================================================================


def cost_usd(seconds: float, price_per_hour: float) -> float:
    """Dollars for a stretch of box time."""
    return seconds / 3600.0 * price_per_hour


def budget_seconds(budget_usd: float, price_per_hour: float) -> float:
    """How many seconds of box time the money left buys."""
    if price_per_hour <= 0:
        return float("inf")
    return budget_usd / price_per_hour * 3600.0


def compute_caps(env=None) -> dict:
    """Read the caps from the environment and work out when the run must stop.

    The stopping point is whichever cap bites first: the launcher's wall-clock
    limit, or the money left at the box's hourly price. Nothing here defaults
    above the gate's own ceilings.
    """
    env = os.environ if env is None else env
    saved = None
    if env is not os.environ:
        saved, os.environ = os.environ, dict(env)
    try:
        price, price_defaulted = read_float_env(
            "PRICE_USD_PER_HOUR", DEFAULT_PRICE_USD_PER_HOUR)
        budget, budget_defaulted = read_float_env(
            "BUDGET_LEFT_USD", DEFAULT_BUDGET_LEFT_USD)
        timeout, timeout_defaulted = read_float_env(
            "REMOTE_TIMEOUT", float(DEFAULT_REMOTE_TIMEOUT))
    finally:
        if saved is not None:
            os.environ = saved

    # Never read a cap larger than the gate's own, whatever the environment says.
    budget = min(budget, DEFAULT_BUDGET_LEFT_USD)
    timeout = min(timeout, float(DEFAULT_REMOTE_TIMEOUT))

    by_money = budget_seconds(budget, price)
    stop_at = min(timeout, by_money)
    caps = {
        "price_usd_per_hour": price,
        "budget_left_usd": budget,
        "remote_timeout_s": timeout,
        "remote_timeout_defaulted": timeout_defaulted,
        "price_defaulted": price_defaulted,
        "budget_defaulted": budget_defaulted,
        "seconds_the_money_buys": by_money,
        "stop_at_s": stop_at,
        "binding_cap": "time" if timeout <= by_money else "cost",
    }
    return caps


def stage_ceiling_s(state, stage: str):
    """This stage's own ceiling, with the shared timer-and-anchor allowance
    reduced by whatever the other stage in that pair already used."""
    ceiling = STAGE_CEILING_S.get(stage)
    if ceiling is None:
        return None
    group = STAGE_CEILING_GROUP.get(stage)
    if group:
        spent = sum(sec for name, sec in (state.get("stage_seconds") or {}).items()
                    if STAGE_CEILING_GROUP.get(name) == group and name != stage)
        return max(0.0, float(ceiling) - spent)
    return float(ceiling)


def stage_allowance_s(state, stage: str) -> float:
    """Seconds this stage may use: its own ceiling, or what is left after the
    fetch margin and the slot the decisions need, whichever is smaller."""
    caps = state["caps"]
    left = caps["stop_at_s"] - elapsed_s(state) - FETCH_MARGIN_S
    if stage != "endpoints":
        left -= ENDPOINTS_SLOT_S
    ceiling = stage_ceiling_s(state, stage)
    return left if ceiling is None else min(ceiling, left)


def guard_before_stage(state, stage: str, estimated_s: float = 0.0) -> float:
    """Decide whether a stage may start, and for how long.

    A stage whose estimated remaining time exceeds the time left is not started.
    Returns the allowance in seconds; raises GuardStop when the stage must not
    begin.
    """
    allowance = stage_allowance_s(state, stage)
    if allowance <= 0:
        raise GuardStop(stage, "time_guard",
                        f"no time left for this stage (allowance {allowance:.0f} s)")
    if estimated_s > 0 and estimated_s > allowance:
        raise GuardStop(
            stage, "time_guard",
            f"estimated {estimated_s:.0f} s exceeds the {allowance:.0f} s left")
    return allowance


def inner_tool_timeout_s(state) -> float:
    """How long a single tool call may run. It fires at least 100 s before the
    outer kill, so the inner stop is the one that happens."""
    return max(0.0, state["caps"]["stop_at_s"] - elapsed_s(state)
               - INNER_TOOL_BACKOFF_S)


def outer_kill_s(state) -> float:
    return max(0.0, state["caps"]["stop_at_s"] - elapsed_s(state)
               - OUTER_KILL_BACKOFF_S)


# ===========================================================================
# Decisions against the card's band
# ===========================================================================


def is_marginal(value: float, band) -> bool:
    """A value sitting within 10 percent of either edge of the band is too close
    to the edge to call. The raw number is kept either way."""
    for edge in band:
        if edge * (1 - MARGINAL_FRACTION) <= value <= edge * (1 + MARGINAL_FRACTION):
            return True
    return False


def decide_band(value, band):
    """PASS inside the band, FAIL outside, VOID within 10 percent of an edge.

    Returns (decision, marginal).
    """
    if value is None or not isinstance(value, (int, float)) or \
            isinstance(value, bool) or math.isnan(float(value)):
        return "VOID", False
    value = float(value)
    if is_marginal(value, band):
        return "VOID", True
    if band[0] <= value <= band[1]:
        return "PASS", False
    return "FAIL", False


def gate_result(af2_hours):
    """The card's own gate, applied to the AlphaFold timing only."""
    if af2_hours is None:
        return {"gate_value": GATE_CEILING_H, "gate_pass": None,
                "gate_else": GATE_ELSE}
    return {
        "gate_value": GATE_CEILING_H,
        "gate_pass": bool(float(af2_hours) <= GATE_CEILING_H),
        "gate_else": GATE_ELSE,
    }


def decision_rule_text(key: str) -> str:
    """Written before the values are known. This is the argument, not a
    computation over the numbers."""
    card = CARDS[key]
    lo, hi = card["band"]
    base = (
        f"The measured value, in {card['unit']}, is compared with the card's band "
        f"[{lo}, {hi}]. Inside the band is PASS. Outside is FAIL. Within 10 percent "
        f"of either edge is VOID and marked marginal. Too few completed runs, a "
        f"missed anchor, or a stage that never ran is VOID with the raw rows kept."
    )
    if key == "C1":
        base += (
            f" The card's separate gate (at most {GATE_CEILING_H} hour per run) is "
            f"reported beside the decision and never changes it; the run does not "
            f"branch on it."
        )
    if key == "C2":
        base += (
            f" An atom count outside {MD_ATOMS_MIN} to {MD_ATOMS_MAX}, or a graphics "
            f"processor that is not an A100, is VOID with the raw number kept."
        )
    return base


# ===========================================================================
# Record writing. The frozen writer owns the shape; this adds the validity
# fields the on-box contract requires and makes the write atomic.
# ===========================================================================


def _provenance():
    """Import the frozen record writer. Kept in a function so --selftest can run
    before anything heavy, and so a missing writer is a clear failure."""
    sys.path.insert(0, str(HERE / "frozen"))
    sys.path.insert(0, str(HERE))
    import provenance  # noqa: E402
    return provenance


def machine_labels(state) -> dict:
    """Everything a later reader needs to know about the box and the tools.
    Read from runtime queries at measurement time, never copied from the card."""
    m = dict(state.get("machine") or {})
    m.setdefault("instance_type", os.environ.get("INSTANCE_TYPE") or None)
    m.setdefault("price_usd_per_hour", state.get("caps", {}).get(
        "price_usd_per_hour"))
    return m


def common_labels(state, key=None):
    labels = [LABEL_STANDIN, LABEL_ONE_GPU]
    if key == "C1":
        labels.append(LABEL_NO_MSA)
    if key == "C3":
        labels.append(LABEL_AUX_READING)
    if key == "C4":
        labels.append(LABEL_STORAGE)
    labels.extend(state.get("labels", []))
    if stopped_early(state):
        labels.append(LABEL_INCOMPLETE)
    out = []
    for lab in labels:
        if lab not in out:
            out.append(lab)
    return out


def write_record(state, filename, *, cell, inputs, metric, values, threshold,
                 decision_rule, decision, notes="", rows=None):
    """Write one record through the frozen writer, then add the validity fields.

    The validity fields live in the file itself. A void recorded only in a
    summary is not a void: a reader opening one input's file must see it.
    """
    prov = _provenance()
    out_dir = Path(state["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    final = out_dir / filename
    staging = out_dir / (filename + ".staging")

    values = dict(values)
    values["run_valid"] = bool(state["run_valid"])
    if stopped_early(state) and LABEL_INCOMPLETE not in json.dumps(
            values.get("labels", [])):
        labels = list(values.get("labels", []))
        labels.append(LABEL_INCOMPLETE)
        values["labels"] = labels

    prov.write_result(
        staging, cell=cell, inputs=inputs, metric=metric, values=values,
        threshold=threshold, decision_rule=decision_rule, decision=decision,
        notes=notes, rows=rows,
    )
    rec = json.loads(staging.read_text())
    staging.unlink()
    rec["run_valid"] = bool(state["run_valid"])
    rec["run_valid_voided_by"] = state["run_valid_voided_by"]
    rec["tag"] = TAG
    if stopped_early(state):
        rec["incomplete_run"] = LABEL_INCOMPLETE
    atomic_write_text(final, json.dumps(rec, indent=2, sort_keys=True))
    return final


def append_row(state, arm: str, row: dict) -> Path:
    """One raw row, one JSON line. Rows are kept even when the value they feed
    is VOID: the raw stays."""
    out_dir = Path(state["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / f"rows_{arm}_tag-{TAG}.jsonl"
    with open(p, "a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    return p


def describe_inputs(paths, counts=None):
    prov = _provenance()
    counts = counts or {}
    return [prov.describe_input(p, n_items=counts.get(str(p)))
            for p in paths]


# ===========================================================================
# Parsers. Each one is given a real-looking line and a malformed one in the
# selftest, because a parser that silently returns nothing is the quiet way a
# run produces a confident wrong number.
# ===========================================================================


_RATE_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?(?:[eE][-+]?[0-9]+)?)\s*ns/day",
                      re.IGNORECASE)


def parse_engine_rate_line(line: str):
    """Pull the simulated-nanoseconds-per-day figure out of one engine log line.

    Handles the two shapes the engine writes: a labelled line ("Speed: 128.9
    ns/day") and a comma-separated row whose header named a speed column.
    Returns None when the line carries no rate.
    """
    if not line:
        return None
    m = _RATE_RE.search(line)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    return None


def parse_md_log(text: str):
    """Read an engine log: every speed figure, and the atom count if printed.

    The engine writes a comma-separated table whose header names its columns;
    the speed column is the one whose name mentions nanoseconds per day.
    Returns {"speeds": [...], "atoms": int or None, "steps": int or None}.
    """
    speeds = []
    atoms = None
    steps = None
    speed_col = None
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.search(r"\batoms\s*[:=]\s*([0-9]+)", line, re.IGNORECASE)
        if m:
            atoms = int(m.group(1))
            continue
        m = re.search(r"\bproduction[_ ]steps\s*[:=]\s*([0-9]+)", line,
                      re.IGNORECASE)
        if m:
            steps = int(m.group(1))
            continue
        if line.startswith("#") and "," in line:
            cols = [c.strip().strip('"') for c in line.lstrip("#").split(",")]
            for i, c in enumerate(cols):
                if "ns/day" in c.lower():
                    speed_col = i
            continue
        rate = parse_engine_rate_line(line)
        if rate is not None:
            speeds.append(rate)
            continue
        if speed_col is not None and "," in line and not line.startswith("#"):
            cols = [c.strip().strip('"') for c in line.split(",")]
            if len(cols) > speed_col:
                try:
                    speeds.append(float(cols[speed_col]))
                except ValueError:
                    pass
    return {"speeds": speeds, "atoms": atoms, "steps": steps}


def ns_per_day_from_wallclock(steps: int, timestep_fs: float, seconds: float):
    """Simulated nanoseconds per day of wall-clock, from the run itself.

    This is the figure the decision uses. It is computed from what the run
    actually did -- steps taken, step size, seconds spent -- not from what the
    engine reported about itself.
    """
    if not steps or seconds is None or seconds <= 0:
        return None
    simulated_ns = steps * timestep_fs * 1e-6
    return simulated_ns * 86400.0 / seconds


def rates_disagree(engine_rate, wallclock_rate) -> bool:
    """True when the engine's own figure and the wall-clock figure differ by
    more than 5 percent of the wall-clock figure."""
    if engine_rate is None or wallclock_rate in (None, 0):
        return False
    return abs(engine_rate - wallclock_rate) / abs(wallclock_rate) > \
        RATE_DISAGREEMENT_FRACTION


_AF2_TOOK_RE = re.compile(
    r"(?P<model>[A-Za-z0-9_.\-]*model[A-Za-z0-9_.\-]*)\s+took\s+"
    r"(?P<sec>[0-9]+(?:\.[0-9]+)?)\s*s", re.IGNORECASE)
_AF2_QUERY_RE = re.compile(
    r"Query\s+\d+\s*/\s*\d+:\s*(?P<name>\S+)\s*\(length\s+(?P<len>[0-9]+)\)",
    re.IGNORECASE)


def parse_af2_timing_rows(text: str):
    """Per-model times and query lengths from a prediction log.

    Returns {"models": [(name, seconds), ...], "queries": [(name, length), ...]}.
    The whole-call wall-clock is measured by this program, not read from the
    log; the per-model times are extra detail for the rows.
    """
    models = []
    queries = []
    for line in (text or "").splitlines():
        m = _AF2_QUERY_RE.search(line)
        if m:
            queries.append((m.group("name"), int(m.group("len"))))
        m = _AF2_TOOK_RE.search(line)
        if m:
            models.append((m.group("model"), float(m.group("sec"))))
    return {"models": models, "queries": queries}


def compile_excluded_seconds(wallclock_s: float, model_times):
    """The whole-call time with the first model's one-off compilation taken off.

    The first model pays for compiling the computation; later models do not. The
    difference between the first model and the middle of the rest is that
    one-off cost. Returns None when the log gave too few per-model times.
    """
    if wallclock_s is None or not model_times or len(model_times) < 2:
        return None
    times = [float(t) for _, t in model_times]
    first, rest = times[0], times[1:]
    overhead = first - statistics.median(rest)
    if overhead <= 0:
        return float(wallclock_s)
    return float(wallclock_s) - overhead


_NVIDIA_NAME_RE = re.compile(r"^\s*(?P<name>[A-Za-z0-9 _\-]+?)\s*,\s*"
                             r"(?P<driver>[0-9.]+)\s*(?:,\s*(?P<cuda>[0-9.]+))?\s*$")


def parse_nvidia_smi(text: str):
    """Graphics processor name, driver version and reported CUDA version.

    Expects the query form `nvidia-smi --query-gpu=name,driver_version
    --format=csv,noheader`. Returns a dict with None where the line was unusable.
    """
    out = {"gpu_name": None, "driver_version": None, "cuda_version": None}
    for line in (text or "").splitlines():
        if not line.strip() or line.lower().startswith("name"):
            continue
        m = _NVIDIA_NAME_RE.match(line)
        if m:
            out["gpu_name"] = m.group("name").strip()
            out["driver_version"] = m.group("driver")
            if m.group("cuda"):
                out["cuda_version"] = m.group("cuda")
            break
    return out


def is_a100(gpu_name) -> bool:
    """True only for an A100. Anything else means the speeds are not A100
    speeds, and the two speed-bound inputs are VOID."""
    return bool(gpu_name) and "a100" in str(gpu_name).lower()


def parse_pip_report(text):
    """Every wheel a pip install actually took, with its address and hash.

    pip writes this report itself, so the record does not depend on anyone
    remembering what was installed.
    """
    try:
        doc = json.loads(text) if isinstance(text, str) else text
    except ValueError:
        return []
    items = []
    for inst in (doc or {}).get("install", []) or []:
        meta = inst.get("metadata") or {}
        dl = inst.get("download_info") or {}
        archive = (dl.get("archive_info") or {})
        digests = archive.get("hashes") or {}
        items.append({
            "name": meta.get("name"),
            "version": meta.get("version"),
            "url": dl.get("url"),
            "sha256": digests.get("sha256") or archive.get("hash", "").replace(
                "sha256=", "") or None,
        })
    return items


def parse_apt_cache_show(text: str):
    """Package name, version and archive hash, as the package index states them."""
    out = []
    cur = {}
    for line in (text or "").splitlines():
        if not line.strip():
            if cur.get("name"):
                out.append(cur)
            cur = {}
            continue
        if line.startswith("Package:"):
            if cur.get("name"):
                out.append(cur)
            cur = {"name": line.split(":", 1)[1].strip()}
        elif line.startswith("Version:"):
            cur["version"] = line.split(":", 1)[1].strip()
        elif line.startswith("SHA256:"):
            cur["sha256"] = line.split(":", 1)[1].strip()
    if cur.get("name"):
        out.append(cur)
    return out


def parse_docking_table(text: str):
    """Ranked docking results: rank, score and the pose file for each.

    Expects whitespace-separated rows with a header naming the columns, which is
    what the docking tool writes.
    """
    rows = []
    header = None
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if header is None:
            low = [p.lower() for p in parts]
            if "rank" in low or "scoring" in low or "score" in low:
                header = low
                continue
        if header is None:
            continue
        try:
            idx_rank = header.index("rank") if "rank" in header else 0
            rank = int(float(parts[idx_rank]))
        except (ValueError, IndexError):
            continue
        score = None
        for name in ("score", "scoring"):
            if name in header:
                try:
                    score = float(parts[header.index(name)])
                except (ValueError, IndexError):
                    score = None
                break
        pose = None
        for p in parts:
            if p.lower().endswith(".pdb"):
                pose = p
        rows.append({"rank": rank, "score": score, "pose": pose})
    rows.sort(key=lambda r: r["rank"])
    return rows


def top_pose(text: str):
    """The best-ranked pose file, or None when the table named none."""
    rows = parse_docking_table(text)
    return rows[0]["pose"] if rows else None


def parse_contact_table(text: str):
    """Residue-residue contacts written as `chain resseq chain resseq distance`."""
    out = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        try:
            out.append({
                "chain_a": parts[0], "res_a": int(parts[1]),
                "chain_b": parts[2], "res_b": int(parts[3]),
                "distance_a": float(parts[4]) if len(parts) > 4 else None,
            })
        except ValueError:
            continue
    return out


def apparent_bytes(paths) -> int:
    """Bytes the files claim to be, summed. Apparent size, not blocks on disk:
    the card's number is about data written, not about the filesystem."""
    total = 0
    for p in paths:
        p = Path(p)
        if p.is_dir():
            for sub in p.rglob("*"):
                if sub.is_file():
                    total += sub.stat().st_size
        elif p.is_file():
            total += p.stat().st_size
    return total


def gib_for_grid(bytes_per_run: int, runs: int = GRID_RUNS) -> float:
    """Scale one run's bytes to the whole grid, in gibibytes."""
    return bytes_per_run * runs / float(1 << 30)


# ===========================================================================
# Structure files and the anchor geometry
#
# The anchor asks one question: when the docking tool is given the two partners
# of a known complex, does it put them back together the way the published
# structure has them? Two readouts answer it -- how many of the published
# residue-residue contacts the pose reproduces, and how far the contacting part
# of the receptor sits from where it should be.
# ===========================================================================

BACKBONE_ATOMS = ("N", "CA", "C", "O")


def read_pdb_atoms(text: str):
    """Read atom lines of a structure file into plain dictionaries.

    Only the fields the anchor needs are kept: which chain, which residue, which
    atom, which element, and where it is.
    """
    atoms = []
    for line in (text or "").splitlines():
        if not (line.startswith("ATOM") or line.startswith("HETATM")):
            continue
        if len(line) < 54:
            continue
        try:
            resseq = int(line[22:26])
            x = float(line[30:38])
            y = float(line[38:46])
            z = float(line[46:54])
        except ValueError:
            continue
        name = line[12:16].strip()
        element = line[76:78].strip() if len(line) >= 78 else ""
        if not element:
            # Fall back to the atom name's leading letter when the file omits
            # the element column, which older files do.
            element = "".join(c for c in name if c.isalpha())[:1]
        atoms.append({
            "record": line[:6].strip(),
            "serial": line[6:11].strip(),
            "name": name,
            "resname": line[17:20].strip(),
            "chain": line[21:22].strip(),
            "resseq": resseq,
            "x": x, "y": y, "z": z,
            "element": element.upper(),
        })
    return atoms


def write_pdb(atoms) -> str:
    """Write atom lines back out, in the fixed-column layout the tools read."""
    lines = []
    for i, a in enumerate(atoms, start=1):
        name = a["name"]
        # Atom names are padded so the element letter lands in its own column;
        # a tool that reads the column would otherwise mis-type the atom.
        if len(name) >= 4:
            name_f = name[:4]
        else:
            name_f = " " + name.ljust(3)
        lines.append(
            "{rec:<6}{ser:>5} {nm}{alt:1}{res:>3} {ch:1}{seq:>4}{icode:1}   "
            "{x:8.3f}{y:8.3f}{z:8.3f}{occ:6.2f}{b:6.2f}          {el:>2}".format(
                rec=a.get("record") or "ATOM", ser=i % 100000, nm=name_f, alt=" ",
                res=a.get("resname", "UNK")[:3], ch=(a.get("chain") or " ")[:1],
                seq=a["resseq"], icode=" ", x=a["x"], y=a["y"], z=a["z"],
                occ=1.0, b=0.0, el=(a.get("element") or "")[:2].upper(),
            )
        )
    lines.append("END")
    return "\n".join(lines) + "\n"


def apply_roles(atoms, role_of_chain):
    """Attach a role -- receptor or capsid -- to every atom, by chain.

    Everything downstream is keyed by role, never by the chain letter in the
    file. Docking tools renumber and rename chains, so a pose whose receptor is
    chain C must compare equal to a reference whose receptor is chain B.
    """
    out = []
    for a in atoms:
        role = role_of_chain.get(a["chain"])
        if role is None:
            continue
        b = dict(a)
        b["role"] = role
        out.append(b)
    return out


def _heavy(atoms):
    return [a for a in atoms if a.get("element") != "H"]


def _dist2(a, b):
    return (a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2 + (a["z"] - b["z"]) ** 2


def residue_contacts(role_atoms, cutoff=CONTACT_CUTOFF_A):
    """Pairs of residues, one from each partner, that touch.

    Two residues touch when any pair of their heavy atoms is within the cutoff.
    The returned keys name the role, not the chain letter.
    """
    cut2 = cutoff * cutoff
    rec = _heavy([a for a in role_atoms if a["role"] == "receptor"])
    cap = _heavy([a for a in role_atoms if a["role"] == "capsid"])
    found = set()
    for r in rec:
        for c in cap:
            if _dist2(r, c) <= cut2:
                found.add((("receptor", r["resseq"]), ("capsid", c["resseq"])))
    return found


def contact_overlap(reference_contacts, pose_contacts) -> float:
    """The share of the published contacts the pose reproduces.

    Zero when the reference has no contacts, because then there is nothing to
    reproduce and a high score would be an artefact.
    """
    if not reference_contacts:
        return 0.0
    shared = len(set(reference_contacts) & set(pose_contacts))
    return shared / float(len(reference_contacts))


def interface_residues(role_atoms, cutoff=CONTACT_CUTOFF_A):
    """Receptor residues that touch the capsid in the reference structure."""
    return {r for (r, _c) in
            {(p[0][1], p[1][1]) for p in residue_contacts(role_atoms, cutoff)}}


def _backbone_index(role_atoms, resseqs):
    idx = {}
    for a in role_atoms:
        if a["role"] != "receptor":
            continue
        if a["resseq"] in resseqs and a["name"] in BACKBONE_ATOMS:
            idx[(a["resseq"], a["name"])] = a
    return idx


def _rmsd_over(index_a, index_b):
    keys = sorted(set(index_a) & set(index_b))
    if not keys:
        return None
    total = sum(_dist2(index_a[k], index_b[k]) for k in keys)
    return math.sqrt(total / len(keys))


def interface_backbone_rmsd(reference_role_atoms, pose_role_atoms,
                            cutoff=CONTACT_CUTOFF_A):
    """How far the contacting part of the receptor is from where it should be.

    Measured over the four backbone atoms of the receptor residues that form the
    reference interface, in the capsid's own frame, with no fitting: the point
    is where the receptor sits relative to the capsid, so superposing the two
    would erase exactly the error being measured.
    """
    resseqs = interface_residues(reference_role_atoms, cutoff)
    if not resseqs:
        return None
    return _rmsd_over(_backbone_index(reference_role_atoms, resseqs),
                      _backbone_index(pose_role_atoms, resseqs))


def whole_chain_rmsd(role_atoms_a, role_atoms_b, role="receptor"):
    """Distance over every matched atom of one partner, with no fitting.

    This is the serial-versus-parallel readout: it must see a shift anywhere in
    the chain, not only at the interface.
    """
    ia = {(a["resseq"], a["name"]): a for a in role_atoms_a if a["role"] == role}
    ib = {(a["resseq"], a["name"]): a for a in role_atoms_b if a["role"] == role}
    return _rmsd_over(ia, ib)


def bind_call(role_atoms, cutoff=CONTACT_CUTOFF_A) -> bool:
    """Does this pose have the two partners touching at all?"""
    return len(residue_contacts(role_atoms, cutoff)) > 0


def anchor_decision(overlap, interface_rmsd, serial_parallel_rmsd,
                    call_serial, call_parallel):
    """Did the docking tool reproduce the published complex, and agree with
    itself when run the other way round on the same box?

    Passes when the pose reproduces at least half the published contacts OR sits
    within 5 Angstrom at the interface, AND the serial and parallel repeats put
    the receptor within 2 Angstrom of each other with the same touching call.
    """
    reasons = []
    close_enough = False
    if overlap is not None and overlap >= ANCHOR_OVERLAP_MIN:
        close_enough = True
        reasons.append(f"contact overlap {overlap:.4f} at or above "
                       f"{ANCHOR_OVERLAP_MIN}")
    if interface_rmsd is not None and interface_rmsd <= ANCHOR_RMSD_MAX_A:
        close_enough = True
        reasons.append(f"interface backbone RMSD {interface_rmsd:.4f} at or "
                       f"below {ANCHOR_RMSD_MAX_A} Angstrom")
    if not close_enough:
        reasons.append("neither the contact overlap nor the interface RMSD met "
                       "its threshold")

    agrees = (serial_parallel_rmsd is not None
              and serial_parallel_rmsd <= ANCHOR_SERIAL_PARALLEL_RMSD_MAX_A
              and bool(call_serial) == bool(call_parallel))
    if not agrees:
        if serial_parallel_rmsd is None:
            reasons.append("the serial and parallel poses could not be compared")
        elif serial_parallel_rmsd > ANCHOR_SERIAL_PARALLEL_RMSD_MAX_A:
            reasons.append(
                f"serial and parallel differ by {serial_parallel_rmsd:.4f} "
                f"Angstrom, above {ANCHOR_SERIAL_PARALLEL_RMSD_MAX_A}")
        else:
            reasons.append("serial and parallel disagree on whether the "
                           "partners touch")
    return bool(close_enough and agrees), reasons


# ===========================================================================
# Harness controls. These run before any band is compared, because a timer that
# is wrong makes every timing wrong in the same invisible way.
# ===========================================================================


def sleep_check(measured_s, planted_s=SLEEP_CHECK_S):
    """Does the clock the timings use report a known wait correctly?

    Returns (ok, relative_error). More than 5 percent off invalidates every
    timing in the run.
    """
    if measured_s is None or planted_s <= 0:
        return False, None
    err = abs(float(measured_s) - planted_s) / planted_s
    return err <= SLEEP_CHECK_TOLERANCE, err


def empty_run_check(seconds, bytes_written):
    """What an empty input costs: the time and bytes that are setup, not work.

    Under 2 seconds and under 1 mebibyte is noise and is ignored. Above either,
    the excess is subtracted from later measurements and the records say so.
    """
    over_time = max(0.0, float(seconds) - EMPTY_RUN_MAX_S)
    over_bytes = max(0, int(bytes_written) - EMPTY_RUN_MAX_BYTES)
    clean = (float(seconds) < EMPTY_RUN_MAX_S
             and int(bytes_written) < EMPTY_RUN_MAX_BYTES)
    return {
        "clean": clean,
        "overhead_s": over_time,
        "overhead_bytes": over_bytes,
        "label": None if clean else LABEL_OVERHEAD_SUBTRACTED,
    }


def spread_check(timings):
    """Do repeated timings of the same work differ at all?

    Repeats that agree to the last digit are not three measurements; they are
    one measurement reported three times, which means the harness is timing the
    wrong thing. That halts the AlphaFold input and nothing else.
    """
    vals = [float(t) for t in (timings or []) if t is not None]
    if len(vals) < 2:
        return {"status": "TOO_FEW", "relative_sd": None, "label": None}
    spread = max(vals) - min(vals)
    mean = statistics.fmean(vals)
    rel_sd = (statistics.stdev(vals) / mean) if mean > 0 else None
    if spread == 0:
        return {"status": WRONG_VARIANCE_SOURCE, "relative_sd": rel_sd,
                "label": LABEL_ZERO_SPREAD}
    label = (LABEL_SPREAD_HIGH
             if rel_sd is not None and rel_sd > SPREAD_HIGH_RELATIVE_SD
             else None)
    return {"status": "OK", "relative_sd": rel_sd, "label": label}


# ===========================================================================
# Running a tool. Every tool call gets its own process group, so a stop kills
# the tool and everything it started, by group id and never by name.
# ===========================================================================


class ToolResult(dict):
    """What one tool call did: its exit code, whether it was stopped, how long
    it took, and where its output went."""

    @property
    def ok(self):
        return self.get("returncode") == 0 and not self.get("timed_out")


def run_tool(cmd, *, timeout_s, log_path, state=None, cwd=None, env=None,
             label=None):
    """Start one tool, wait for it, stop it if it runs past its allowance.

    The child gets an environment copy with the download tokens removed, and its
    own process group so the stop reaches its children too.
    """
    log_path = Path(log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    environment = child_env(env)
    started = time.time()
    timed_out = False
    pgid = None
    with open(log_path, "ab") as fh:
        fh.write(("\n$ " + " ".join(str(c) for c in cmd) + "\n").encode())
        fh.flush()
        proc = subprocess.Popen(
            [str(c) for c in cmd], cwd=str(cwd) if cwd else None,
            env=environment, stdout=fh, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, start_new_session=True,
        )
        try:
            pgid = os.getpgid(proc.pid)
        except OSError:
            pgid = proc.pid
        if state is not None and pgid not in state.get("process_groups", []):
            state.setdefault("process_groups", []).append(pgid)
            try:
                with open(Path(state["out_dir"]) / "process_groups.txt", "a") as pg:
                    pg.write(f"{pgid}\n")
            except OSError:
                pass
        try:
            rc = proc.wait(timeout=max(0.0, float(timeout_s)))
        except subprocess.TimeoutExpired:
            timed_out = True
            rc = None
            _kill_group(pgid, proc)
    seconds = time.time() - started
    return ToolResult({
        "cmd": [str(c) for c in cmd],
        "label": label,
        "returncode": rc,
        "timed_out": timed_out,
        "seconds": seconds,
        "log": str(log_path),
        "pgid": pgid,
    })


def _kill_group(pgid, proc=None):
    """Stop a tool and everything it started, by process group id."""
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            if pgid:
                os.killpg(pgid, sig)
            elif proc is not None:
                proc.kill()
        except (OSError, ProcessLookupError):
            break
        deadline = time.time() + (3.0 if sig == signal.SIGTERM else 2.0)
        while time.time() < deadline:
            if proc is not None and proc.poll() is not None:
                return
            time.sleep(0.05)
    if proc is not None:
        try:
            proc.wait(timeout=2)
        except Exception:  # noqa: BLE001 - the group is already gone
            pass


# ===========================================================================
# Turning the gathered measurements into the four decisions.
#
# These functions read only what the stages recorded, so the selftest can plant
# rows with known answers and check the arithmetic without any tool.
# ===========================================================================


def _gpu_name(state):
    return (state.get("machine") or {}).get("gpu_name")


def _void(measured, labels, notes):
    return {"measured": measured, "decision": "VOID", "marginal": False,
            "labels": labels, "void_reason": notes}


def decide_c1(state):
    """AlphaFold hours per run: the mean whole-call wall-clock over the runs."""
    data = (state.get("measurements") or {}).get("C1") or {}
    runs = [r for r in data.get("runs", []) if not r.get("incomplete")]
    labels = []
    seconds = [float(r["wallclock_s"]) for r in runs]
    measured = (statistics.fmean(seconds) / 3600.0) if seconds else None

    if data.get("stopped") or not runs:
        return _void(measured, labels, f"AlphaFold timings {LABEL_UNMEASURED}")

    # Repeats of the same pair that agree exactly are not three measurements.
    for pair, pair_runs in _group(runs, "pair").items():
        sp = spread_check([r["wallclock_s"] for r in pair_runs])
        if sp["status"] == WRONG_VARIANCE_SOURCE:
            return _void(measured, [LABEL_ZERO_SPREAD],
                         f"{WRONG_VARIANCE_SOURCE}: pair {pair} timings identical")
        if sp["label"]:
            labels.append(sp["label"])

    if not is_a100(_gpu_name(state)):
        return _void(measured, labels + [LABEL_NOT_A100],
                     f"the graphics processor is {_gpu_name(state)}, not an A100")
    if len(runs) < MIN_AF2_RUNS:
        return _void(measured, labels,
                     f"only {len(runs)} completed runs, below {MIN_AF2_RUNS}")
    if len({r["pair"] for r in runs}) < MIN_AF2_PAIRS:
        return _void(measured, labels,
                     f"the completed runs cover {len({r['pair'] for r in runs})} "
                     f"pairs, below {MIN_AF2_PAIRS}")

    decision, marginal = decide_band(measured, CARDS["C1"]["band"])
    return {"measured": measured, "decision": decision, "marginal": marginal,
            "labels": labels, "void_reason": None, "n": len(runs)}


def decide_c2(state):
    """Molecular-dynamics speed: the middle value over the complexes, taken
    from the wall-clock of the production segment."""
    data = (state.get("measurements") or {}).get("C2") or {}
    comps = [c for c in data.get("complexes", []) if not c.get("incomplete")]
    labels = []
    rates = [float(c["wallclock_ns_per_day"]) for c in comps
             if c.get("wallclock_ns_per_day") is not None]
    measured = statistics.median(rates) if rates else None

    if data.get("stopped") or not comps:
        return _void(measured, labels,
                     f"molecular-dynamics timings {LABEL_UNMEASURED}")
    for c in comps:
        atoms = c.get("atoms")
        if atoms is None or not (MD_ATOMS_MIN <= int(atoms) <= MD_ATOMS_MAX):
            return _void(measured, labels,
                         f"complex {c.get('complex')} has {atoms} atoms, outside "
                         f"{MD_ATOMS_MIN} to {MD_ATOMS_MAX}")
        if rates_disagree(c.get("engine_ns_per_day"),
                          c.get("wallclock_ns_per_day")):
            if LABEL_RATE_DISAGREE not in labels:
                labels.append(LABEL_RATE_DISAGREE)
    if not is_a100(_gpu_name(state)):
        return _void(measured, labels + [LABEL_NOT_A100],
                     f"the graphics processor is {_gpu_name(state)}, not an A100")
    if len(comps) < MIN_MD_COMPLEXES:
        return _void(measured, labels,
                     f"only {len(comps)} complexes, below {MIN_MD_COMPLEXES}")

    decision, marginal = decide_band(measured, CARDS["C2"]["band"])
    return {"measured": measured, "decision": decision, "marginal": marginal,
            "labels": labels, "void_reason": None, "n": len(comps)}


def decide_c3(state):
    """Auxiliary hours per pair: docking, interface analysis and writing the
    call-table row. Installs, downloads and setup are not counted."""
    data = (state.get("measurements") or {}).get("C3") or {}
    pairs = [p for p in data.get("pairs", []) if not p.get("truncated")]
    seconds = [float(p["seconds"]) for p in pairs]
    measured = (statistics.fmean(seconds) / 3600.0) if seconds else None
    if data.get("stopped") and not pairs:
        return _void(measured, [], f"auxiliary timings {LABEL_UNMEASURED}")
    if len(pairs) < MIN_AUX_PAIRS:
        return _void(measured, [],
                     f"only {len(pairs)} finished pairs, below {MIN_AUX_PAIRS}")
    decision, marginal = decide_band(measured, CARDS["C3"]["band"])
    return {"measured": measured, "decision": decision, "marginal": marginal,
            "labels": [], "void_reason": None, "n": len(pairs)}


def decide_c4(state):
    """Storage for the whole grid: one run's bytes, scaled to 216 runs."""
    data = (state.get("measurements") or {}).get("C4") or {}
    arts = data.get("artifacts", [])
    kinds = {a.get("kind") for a in arts}
    per_run = sum(int(a["bytes"]) for a in arts)
    measured = gib_for_grid(per_run, GRID_RUNS) if arts else None
    extra = {
        "bytes_per_grid_run": per_run,
        "gib_432_runs": gib_for_grid(per_run, GRID_RUNS_DOUBLE) if arts else None,
        "gib_intermediates_deleted": (
            gib_for_grid(sum(int(a["bytes"]) for a in arts
                             if not a.get("intermediate")), GRID_RUNS)
            if arts else None),
        "md_bytes_per_ns": (
            sum(int(a["bytes"]) for a in arts if a.get("kind") == "md")
            / MD_PRODUCTION_NS if any(a.get("kind") == "md" for a in arts)
            else None),
    }
    if data.get("stopped") and not arts:
        out = _void(measured, [], f"storage measurements {LABEL_UNMEASURED}")
        out.update(extra)
        return out
    missing = {"af2", "docking", "md"} - kinds
    if missing:
        out = _void(measured, [],
                    "no measurement for artifact types: " + ", ".join(sorted(missing)))
        out.update(extra)
        return out
    decision, marginal = decide_band(measured, CARDS["C4"]["band"])
    out = {"measured": measured, "decision": decision, "marginal": marginal,
           "labels": [], "void_reason": None, "n": len(arts)}
    out.update(extra)
    return out


DECIDERS = {"C1": decide_c1, "C2": decide_c2, "C3": decide_c3, "C4": decide_c4}


def _group(rows, key):
    out = {}
    for r in rows:
        out.setdefault(r.get(key), []).append(r)
    return out


# ===========================================================================
# Writing the four input records, the validity file and the summary
# ===========================================================================


def write_input_record(state, key, result):
    card = CARDS[key]
    values = {
        "measured": result.get("measured"),
        "unit": card["unit"],
        "card_value": card["card_value"],
        "band": card["band"],
        "n": result.get("n"),
        "marginal": bool(result.get("marginal")),
        "labels": common_labels(state, key) + list(result.get("labels") or []),
        "machine": machine_labels(state),
        "void_reason": result.get("void_reason"),
    }
    if result.get("void_reason") and result.get("decision") == "VOID":
        if LABEL_UNMEASURED in str(result["void_reason"]):
            values["labels"].append(LABEL_UNMEASURED)
    if key == "C1":
        values["gate"] = gate_result(result.get("measured"))
        values.update(gate_result(result.get("measured")))
    elif key in ("C2", "C3"):
        values["gate"] = GATE_NOT_APPLICABLE
    if key == "C2":
        values["timestep_fs"] = MD_TIMESTEP_FS
        values["production_ns"] = MD_PRODUCTION_NS
    if key == "C4":
        for extra in ("bytes_per_grid_run", "gib_432_runs",
                      "gib_intermediates_deleted", "md_bytes_per_ns"):
            values[extra] = result.get(extra)
        values["grid_runs"] = GRID_RUNS
    rows_file = Path(state["out_dir"]) / f"rows_{key}_tag-{TAG}.jsonl"
    return write_record(
        state, f"endpoint-{key}_tag-{TAG}.json",
        cell={"tag": TAG, "input": key, "arm": key, "stage": "endpoints"},
        inputs=describe_inputs([rows_file]),
        metric=card["name"],
        values=values,
        threshold={"band": card["band"], "card_value": card["card_value"],
                   "unit": card["unit"]},
        decision_rule=decision_rule_text(key),
        decision=result.get("decision", "VOID"),
        notes=LABEL_STANDIN_ONLY,
    )


def write_run_valid(state, exit_code):
    atomic_write_json(Path(state["out_dir"]) / "RUN_VALID.json", {
        "tag": TAG,
        "run_valid": bool(state["run_valid"]),
        "run_valid_voided_by": state["run_valid_voided_by"],
        "stops": state["stops"],
        "stages_done": state["stages_done"],
        "unmeasured_inputs": state["unmeasured"],
        "exit_code": exit_code,
        "incomplete_run": LABEL_INCOMPLETE if stopped_early(state) else None,
    })


def write_summary(state, results, exit_code):
    """The summary restates; it never decides. Every number in it has its own
    record, and the reader is told what the run does and does not cover."""
    summary = {
        "what_this_run_decides": (
            "This run decides the stand-in protocol only. It measured three "
            "stand-in protein pairs built from the chains of structure 6IHB on "
            "one graphics processor on one rented box. It did not run the "
            "card's own grid, and it is not a replication of anything: repeats "
            "here are repeats on one box."
        ),
        "tag": TAG,
        "run_valid": bool(state["run_valid"]),
        "run_valid_voided_by": state["run_valid_voided_by"],
        "exit_code": exit_code,
        "remote_timeout_s_seen": state["caps"].get("remote_timeout_s"),
        "remote_timeout_label": (
            LABEL_TIMEOUT_DEFAULT
            if state["caps"].get("remote_timeout_defaulted") else None),
        "caps": state["caps"],
        "elapsed_s": round(elapsed_s(state), 1),
        "cost_usd_so_far": round(
            cost_usd(elapsed_s(state),
                     state["caps"].get("price_usd_per_hour", 0.0)), 4),
        "stages_done": state["stages_done"],
        "stops": state["stops"],
        "unmeasured_inputs": state["unmeasured"],
        "incomplete_run": LABEL_INCOMPLETE if stopped_early(state) else None,
        "labels": common_labels(state),
        "machine": machine_labels(state),
        "anchor": (state.get("measurements") or {}).get("anchor"),
        "controls": (state.get("measurements") or {}).get("controls"),
        "records": {},
        "gate": {
            "applies_to": "C1 only (the card's gate is on af2_h_per_run)",
            "gate_value": GATE_CEILING_H,
            "gate_pass": (results.get("C1") or {}).get("gate_pass"),
            "gate_else": GATE_ELSE,
        },
        "files_written": sorted(
            p.name for p in Path(state["out_dir"]).glob("*") if p.is_file()),
    }
    for key, res in results.items():
        card = CARDS[key]
        summary["records"][key] = {
            "record_file": f"endpoint-{key}_tag-{TAG}.json",
            "metric": card["name"],
            "measured": res.get("measured"),
            "unit": card["unit"],
            "card_value": card["card_value"],
            "band": card["band"],
            "decision": res.get("decision"),
            "marginal": bool(res.get("marginal")),
            "n": res.get("n"),
            "labels": list(res.get("labels") or []),
            "void_reason": res.get("void_reason"),
        }
    if (results.get("C1") or {}).get("measured") is not None:
        summary["gate"]["gate_pass"] = gate_result(
            results["C1"]["measured"])["gate_pass"]
    atomic_write_json(Path(state["out_dir"]) / f"{TAG}_summary.json", summary)
    return summary


def write_run_done(state, exit_code):
    atomic_write_text(Path(state["out_dir"]) / "RUN_DONE", f"{exit_code}\n")


# ===========================================================================
# The stage flow
# ===========================================================================

STAGE_INPUT = {"aux": "C3", "af2": "C1", "md": "C2", "storage": "C4"}
ALL_INPUTS = ["C1", "C2", "C3", "C4"]


def mark_unmeasured(state, key, reason):
    """This input has no usable measurement. It is VOID, not holding."""
    if not key:
        return
    if key not in state["unmeasured"]:
        state["unmeasured"].append(key)
    meas = state.setdefault("measurements", {}).setdefault(key, {})
    meas["stopped"] = reason
    save_state(state)


def mark_after_stop(state, key, reason):
    """A guard, ceiling or timeout stopped this stage. Whether the input still
    has a decision depends on how much of it got measured before the stop.

    An input whose remaining evidence meets the stated minimum keeps its
    decision; one that is left short is VOID and unmeasured.
    """
    if not key:
        return
    meas = state.setdefault("measurements", {}).setdefault(key, {})
    meas["stopped_note"] = reason
    save_state(state)
    if DECIDERS[key](state).get("decision") == "VOID":
        mark_unmeasured(state, key, reason)


def run_stages(state, stages, tool_runner, endpoints_fn, settle_inputs=True):
    """Run the stages in order, with a guard before each one.

    Three kinds of thing can go wrong, and they are not the same kind of thing.

    Broken infrastructure or a broken harness (exit 2) and a missed anchor
    (exit 4) mean the run's numbers cannot be trusted: the run is marked invalid
    and every later record says so.

    A guard, a stage ceiling or a timeout (exit 3) means the run ran out of time
    or money. The numbers already taken stand; the inputs that were never
    measured are VOID, not holding. Later stages that still have time still run,
    and the decisions are always written.
    """
    fail_code = None
    for name, fn in stages:
        if fail_code is not None:
            mark_unmeasured(state, STAGE_INPUT.get(name),
                            f"{name} did not run after a failure")
            continue
        started = time.time()
        try:
            log(f"{name}: start, elapsed {elapsed_s(state):.0f} s")
            fn(state, tool_runner)
            state["stages_done"].append(name)
            save_state(state)
        except GuardStop as stop:
            log(f"{name}: stopped ({stop.kind}) {stop.detail}")
            record_stop(state, name, stop.kind, stop.detail)
            mark_after_stop(state, STAGE_INPUT.get(name),
                            f"{stop.kind}: {stop.detail}")
        except FailStop as fail:
            log(f"{name}: failed: {fail.detail}")
            void_run(state, f"{name}: {fail.detail}")
            fail_code = fail.code
            mark_unmeasured(state, STAGE_INPUT.get(name), fail.detail)
        except Exception as exc:  # noqa: BLE001 - any other break is infrastructure
            log(f"{name}: failed: {exc!r}")
            void_run(state, f"{name}: {exc!r}")
            fail_code = 2
            mark_unmeasured(state, STAGE_INPUT.get(name), repr(exc))
        finally:
            state.setdefault("stage_seconds", {})[name] = time.time() - started
            save_state(state)

    if fail_code is not None:
        for key in ALL_INPUTS:
            if key not in state["unmeasured"]:
                mark_unmeasured(state, key, "the run failed before this input "
                                            "was decided")

    # The exit code is settled before the decisions are written, so the summary
    # and the validity file carry the code the operator will see. A marginal
    # VOID is a decision made on a measurement, so it does not give exit 3.
    # Exit 0 means every one of the four inputs got a decision made on a
    # measurement. A VOID that comes from sitting too close to a band edge is
    # such a decision; a VOID from missing evidence is not.
    unresolved = []
    if settle_inputs:
        for key in ALL_INPUTS:
            preview = DECIDERS[key](state)
            if preview.get("decision") == "VOID" and not preview.get("marginal"):
                unresolved.append(key)

    prior = state.get("exit_code") or 0
    if fail_code is not None:
        exit_code = fail_code
    elif not state["run_valid"] and prior in (2, 4):
        # An earlier part of this run already failed. Writing the decisions
        # afterwards must not downgrade that into a mere guard stop.
        exit_code = prior
    elif state["unmeasured"] or state["stops"] or unresolved:
        # Some planned work never happened, even if the inputs that remain are
        # still decidable. The operator must be told the run was cut short.
        exit_code = 3
    else:
        exit_code = 0
    state["exit_code"] = exit_code
    save_state(state)

    results = endpoints_fn(state, tool_runner)
    return exit_code, results


def stage_endpoints(state, tool_runner):
    """Always runs. Writes the four decisions, the validity file and the
    summary, whatever happened before it."""
    results = {}
    for key in ALL_INPUTS:
        if key in state["unmeasured"]:
            meas = (state.get("measurements") or {}).get(key) or {}
            res = DECIDERS[key](state)
            if res.get("decision") != "VOID":
                res = _void(res.get("measured"), res.get("labels") or [],
                            f"{meas.get('stopped') or 'stage did not finish'}: "
                            f"{LABEL_UNMEASURED}")
            elif LABEL_UNMEASURED not in str(res.get("void_reason")):
                res["void_reason"] = (f"{meas.get('stopped') or res['void_reason']}"
                                      f": {LABEL_UNMEASURED}")
        else:
            res = DECIDERS[key](state)
        if key == "C1":
            res["gate_pass"] = gate_result(res.get("measured"))["gate_pass"]
        results[key] = res
        write_input_record(state, key, res)
    write_unit_and_scale_record(state, final=True)
    exit_code = state.get("exit_code", 0)
    write_run_valid(state, exit_code)
    write_summary(state, results, exit_code)
    return results


# ===========================================================================
# Building the three stand-in pairs out of the published structure
# ===========================================================================

THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
    "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
    "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
    "TYR": "Y", "VAL": "V", "MSE": "M",
}
PAIR_TARGET_LENGTHS = [780, 875, 975]   # spread over the 750 to 1000 range


def chain_residues(atoms, chain):
    seen = {}
    for a in atoms:
        if a["chain"] == chain and a["name"] == "CA":
            seen.setdefault(a["resseq"], a["resname"])
    return [(seq, seen[seq]) for seq in sorted(seen)]


def sequence_of(residues) -> str:
    return "".join(THREE_TO_ONE.get(rn, "X") for _seq, rn in residues)


def choose_anchor_chains(atoms):
    """Work out which chain is the capsid and which is the receptor.

    The capsid chain is the longest. The receptor is the short chain that
    actually touches it -- a domain of roughly a hundred residues. Both ids are
    recorded, because the file's letters are an accident of the deposition.
    """
    lengths = {c: len(chain_residues(atoms, c))
               for c in sorted({a["chain"] for a in atoms}) if c}
    lengths = {c: n for c, n in lengths.items() if n > 0}
    if len(lengths) < 2:
        raise FailStop("anchor", "the structure file has fewer than two chains "
                                 "with residues", 2)
    capsid = max(lengths, key=lambda c: lengths[c])
    best, best_contacts = None, -1
    for c, n in lengths.items():
        if c == capsid:
            continue
        roles = {capsid: "capsid", c: "receptor"}
        n_contacts = len(residue_contacts(apply_roles(atoms, roles)))
        if n_contacts > best_contacts:
            best, best_contacts = c, n_contacts
    if best is None:
        raise FailStop("anchor", "no second chain to use as the receptor", 2)
    return {"capsid_chain": capsid, "receptor_chain": best,
            "capsid_residues": lengths[capsid], "receptor_residues": lengths[best],
            "reference_contacts": best_contacts}


def build_standin_pairs(atoms, chains):
    """Three stand-in complexes, one per capsid slot, 750 to 1,000 residues.

    Each is the receptor domain plus a stretch of the capsid chain, with the
    three stretches chosen so the three total lengths are spread over the range.
    These are stand-ins: they are not the card's pairs, and every record says so.
    """
    cap = chain_residues(atoms, chains["capsid_chain"])
    rec = chain_residues(atoms, chains["receptor_chain"])
    pairs = []
    for slot, target in enumerate(PAIR_TARGET_LENGTHS):
        want_cap = max(1, min(len(cap), target - len(rec)))
        start = min(max(0, len(cap) - want_cap), slot * 40)
        cap_slice = cap[start:start + want_cap]
        cap_keep = {s for s, _ in cap_slice}
        pair_atoms = [a for a in atoms
                      if (a["chain"] == chains["receptor_chain"])
                      or (a["chain"] == chains["capsid_chain"]
                          and a["resseq"] in cap_keep)]
        pairs.append({
            "pair": f"pair{slot + 1}",
            "capsid_slot": slot,
            "receptor_chain": chains["receptor_chain"],
            "capsid_chain": chains["capsid_chain"],
            "receptor_length": len(rec),
            "capsid_length": len(cap_slice),
            "total_length": len(rec) + len(cap_slice),
            "receptor_sequence": sequence_of(rec),
            "capsid_sequence": sequence_of(cap_slice),
            "atoms": pair_atoms,
        })
    return pairs


ICOSAHEDRAL_THREEFOLD_AXES = None


def _threefold_axes():
    """The ten three-fold directions of an icosahedral shell, in the standard
    orientation (two-fold axes along the coordinate axes)."""
    global ICOSAHEDRAL_THREEFOLD_AXES
    if ICOSAHEDRAL_THREEFOLD_AXES is None:
        phi = (1 + math.sqrt(5)) / 2
        raw = [(1, 1, 1), (1, 1, -1), (1, -1, 1), (1, -1, -1),
               (0, 1 / phi, phi), (0, 1 / phi, -phi),
               (1 / phi, phi, 0), (1 / phi, -phi, 0),
               (phi, 0, 1 / phi), (-phi, 0, 1 / phi)]
        axes = []
        for v in raw:
            n = math.sqrt(sum(c * c for c in v))
            axes.append(tuple(c / n for c in v))
        ICOSAHEDRAL_THREEFOLD_AXES = axes
    return ICOSAHEDRAL_THREEFOLD_AXES


def distance_to_nearest_threefold(point, centre):
    """Shortest distance from a point to any three-fold symmetry axis of the
    shell, measured as reported, in the standard orientation."""
    v = (point[0] - centre[0], point[1] - centre[1], point[2] - centre[2])
    best = None
    for ax in _threefold_axes():
        along = sum(v[i] * ax[i] for i in range(3))
        perp2 = sum((v[i] - along * ax[i]) ** 2 for i in range(3))
        d = math.sqrt(max(0.0, perp2))
        best = d if best is None else min(best, d)
    return best


def site_class(distance_a):
    """Name the binding site by where it sits relative to the symmetry axes."""
    if distance_a is None:
        return "unknown"
    if distance_a < 15.0:
        return "at or near a three-fold axis"
    if distance_a < 30.0:
        return "on the shoulder of a three-fold axis"
    return "away from the three-fold axes"


def centroid(atoms):
    if not atoms:
        return (0.0, 0.0, 0.0)
    return (statistics.fmean(a["x"] for a in atoms),
            statistics.fmean(a["y"] for a in atoms),
            statistics.fmean(a["z"] for a in atoms))


def interface_analysis(role_atoms):
    """The side work the card calls auxiliary: who touches whom, where the site
    is, and the one row that goes into the call table."""
    contacts = residue_contacts(role_atoms)
    iface = sorted(interface_residues(role_atoms))
    cap = [a for a in role_atoms if a["role"] == "capsid"]
    iface_atoms = [a for a in role_atoms
                   if a["role"] == "receptor" and a["resseq"] in set(iface)]
    dist = distance_to_nearest_threefold(centroid(iface_atoms), centroid(cap))
    return {
        "n_contacts": len(contacts),
        "n_interface_residues": len(iface),
        "interface_residues": iface,
        "contact_cutoff_angstrom": CONTACT_CUTOFF_A,
        "distance_to_nearest_threefold_angstrom": dist,
        "site_class": site_class(dist),
        "call": "bind" if contacts else "no-bind",
    }


# ===========================================================================
# The worker that runs the dynamics. Written to the working directory at run
# time, so the payload stays the two files the directive names.
# ===========================================================================

MD_WORKER_PY = r'''
"""Solvate one docked complex, settle it, then run a short production segment.

Prints the three facts the measurement needs: how many atoms the system has,
how many production steps were taken, and how long the production segment took.
The engine's own speed line is also printed, so the two figures can be compared.
"""
import json
import sys
import time

from openmm import app, unit, Platform, LangevinMiddleIntegrator, MonteCarloBarostat
from openmm.app import PDBFile, ForceField, Modeller, Simulation, StateDataReporter
import openmm
from pdbfixer import PDBFixer

pose_pdb, out_json, steps_s, timestep_fs, seed_s = sys.argv[1:6]
steps = int(steps_s)
timestep = float(timestep_fs)
seed = int(seed_s)

fixer = PDBFixer(filename=pose_pdb)
fixer.findMissingResidues()
fixer.findMissingAtoms()
fixer.addMissingAtoms()
fixer.addMissingHydrogens(7.0)

forcefield = ForceField("amber14-all.xml", "amber14/tip3pfb.xml")
platform = Platform.getPlatformByName("CUDA")

# Pick the water shell so the system lands inside the atom-count window the
# protocol fixes. Too small and the speed is flattering; too large and it is not
# the same quantity.
chosen = None
for padding_nm in (1.0, 1.2, 1.4, 1.6, 0.8):
    modeller = Modeller(fixer.topology, fixer.positions)
    modeller.addSolvent(forcefield, model="tip3p",
                        padding=padding_nm * unit.nanometer,
                        ionicStrength=0.15 * unit.molar)
    n_atoms = modeller.topology.getNumAtoms()
    chosen = chosen or (padding_nm, modeller, n_atoms)
    if 120000 <= n_atoms <= 180000:
        chosen = (padding_nm, modeller, n_atoms)
        break
padding_nm, modeller, n_atoms = chosen
print("atoms:", n_atoms)
print("water_padding_nm:", padding_nm)

system = forcefield.createSystem(
    modeller.topology, nonbondedMethod=app.PME,
    nonbondedCutoff=1.0 * unit.nanometer, constraints=app.HBonds,
    rigidWater=True, hydrogenMass=1.0 * unit.amu)
system.addForce(MonteCarloBarostat(1 * unit.bar, 300 * unit.kelvin, 100))
integrator = LangevinMiddleIntegrator(300 * unit.kelvin, 1 / unit.picosecond,
                                      timestep * unit.femtosecond)
integrator.setRandomNumberSeed(seed)
sim = Simulation(modeller.topology, system, integrator, platform,
                 {"Precision": "mixed", "DeterministicForces": "false"})
sim.context.setPositions(modeller.positions)
print("precision: mixed")
print("platform:", sim.context.getPlatform().getName())
print("openmm_version:", openmm.version.version)

sim.minimizeEnergy(maxIterations=2000)
sim.context.setVelocitiesToTemperature(300 * unit.kelvin, seed)
sim.step(5000)                       # short equilibration, not timed

traj = out_json + ".dcd"
sim.reporters.append(app.DCDReporter(traj, 5000))   # frame every 10 ps
sim.reporters.append(StateDataReporter(
    out_json + ".log", 5000, step=True, time=True, potentialEnergy=True,
    temperature=True, speed=True, separator=","))
print("frame_interval_steps: 5000")
print("production_steps:", steps)

sim.context.setTime(0)
t0 = time.time()
sim.step(steps)
wall = time.time() - t0
print("production_wallclock_s:", wall)

json.dump({"atoms": n_atoms, "steps": steps, "timestep_fs": timestep,
           "wallclock_s": wall, "padding_nm": padding_nm,
           "trajectory": traj, "log": out_json + ".log",
           "frame_interval_steps": 5000,
           "openmm_version": openmm.version.version,
           "precision": "mixed", "platform": "CUDA"},
          open(out_json, "w"), indent=2)
'''

SMOKE_CHECK_PY = r'''
"""Ask every tool, now, whether it works. Recollection is not evidence."""
import json
import subprocess
import sys

report = {}
import jax
report["jax_version"] = jax.__version__
devices = [str(d) for d in jax.devices()]
report["jax_devices"] = devices
if not any("cuda" in d.lower() or "gpu" in d.lower() for d in devices):
    print("FATAL: JAX lists no graphics device:", devices, file=sys.stderr)
    sys.exit(2)

import alphafold
report["alphafold_module"] = getattr(alphafold, "__file__", "imported")
import colabfold
report["colabfold_version"] = getattr(colabfold, "__version__", "unknown")

import openmm
from openmm import Platform
report["openmm_version"] = openmm.version.version
Platform.getPlatformByName("CUDA")
report["openmm_cuda_platform"] = "available"

import lightdock
report["lightdock_version"] = getattr(lightdock, "__version__", "unknown")

for tool in (["colabfold_batch", "--help"], ["lightdock3.py", "--help"]):
    rc = subprocess.run(tool, capture_output=True).returncode
    report[tool[0] + "_help_rc"] = rc
    if rc != 0:
        print("FATAL:", tool[0], "did not answer --help", file=sys.stderr)
        sys.exit(2)

json.dump(report, open(sys.argv[1], "w"), indent=2)
print("smoke check passed")
'''


# ===========================================================================
# The stages that run on the box
# ===========================================================================


def work_dir(state) -> Path:
    p = Path(state["out_dir"]).parent.parent / f"work_{TAG}"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _require(result, stage, what):
    """A tool that fails is broken infrastructure. It is never patched around
    and no substitute is tried."""
    if result.get("timed_out"):
        raise GuardStop(stage, "tool_timeout", f"{what} ran past its allowance")
    if result.get("returncode") != 0:
        raise FailStop(stage, f"{what} failed with exit "
                              f"{result.get('returncode')}", 2)
    return result


def stage_install(state, tool_runner):
    """Preflight, installs, downloads and the smoke check, in one allowance."""
    allowance = guard_before_stage(state, "install")
    out = Path(state["out_dir"])
    wd = work_dir(state)
    logs = out / "install.log"

    smi = tool_runner(
        ["nvidia-smi", "--query-gpu=name,driver_version",
         "--format=csv,noheader"],
        timeout_s=min(60, allowance), log_path=out / "preflight.log", state=state,
        label="nvidia-smi")
    if not smi.ok:
        raise FailStop("install", "no graphics processor is visible", 2)
    smi_text = (out / "preflight.log").read_text(errors="replace")
    state["machine"].update(parse_nvidia_smi(smi_text))
    state["machine"]["instance_type"] = os.environ.get("INSTANCE_TYPE")
    state["machine"]["python"] = sys.version.split()[0]
    state["machine"]["disk_free_bytes"] = shutil.disk_usage(str(wd)).free
    save_state(state)

    # The system packages are declared in onbox_m4.sh and handed over here, so
    # the declaration and the install cannot drift apart.
    packages = (os.environ.get("M4_APT_PACKAGES") or "").split() or APT_PACKAGES
    apt_cmd = ["sudo", "-n", "env", "DEBIAN_FRONTEND=noninteractive",
               "apt-get", "-y", "-o", "DPkg::Lock::Timeout=300", "install"] \
        + packages
    _require(tool_runner(["sudo", "-n", "env", "DEBIAN_FRONTEND=noninteractive",
                          "apt-get", "-y", "-o", "DPkg::Lock::Timeout=300",
                          "update"],
                         timeout_s=stage_allowance_s(state, "install"),
                         log_path=logs, state=state, label="apt-get update"),
             "install", "the package index update")
    _require(tool_runner(apt_cmd, timeout_s=stage_allowance_s(state, "install"),
                         log_path=logs, state=state, label="apt-get install"),
             "install", "the declared system packages")
    apt_show = out / "apt_packages.txt"
    tool_runner(["apt-cache", "show"] + packages,
                timeout_s=60, log_path=apt_show, state=state, label="apt-cache")
    apt_records = parse_apt_cache_show(apt_show.read_text(errors="replace"))

    pip_reports = []
    for i, group in enumerate(PIP_INSTALL_GROUPS):
        report = out / f"pip_report_{i}.json"
        _require(tool_runner(
            [sys.executable, "-m", "pip", "install", "-q", "--report",
             str(report)] + group,
            timeout_s=stage_allowance_s(state, "install"), log_path=logs,
            state=state, label="pip install " + " ".join(group)),
            "install", "the pinned Python packages " + " ".join(group))
        if report.exists():
            pip_reports.append({
                "file": report.name,
                "sha256": sha256_file(report),
                "wheels": parse_pip_report(report.read_text(errors="replace")),
            })

    downloads = []
    for name, url in DOWNLOADS.items():
        host = url.split("/")[2]
        if host not in ALLOWED_DOWNLOAD_HOSTS:
            raise FailStop("install", f"{host} is not an allowed source", 2)
        dest = wd / Path(url).name
        if not dest.exists():
            _require(tool_runner(
                ["curl", "-fsSL", "--retry", "3", "-o", str(dest), url],
                timeout_s=stage_allowance_s(state, "install"), log_path=logs,
                state=state, label="download " + name),
                "install", f"the download of {name}")
        downloads.append({"name": name, "url": url, "sha256": sha256_file(dest),
                          "bytes": dest.stat().st_size, "path": str(dest)})
    state["downloads"] = downloads
    state["machine"]["pip_reports"] = pip_reports
    state["machine"]["apt_packages"] = apt_records
    save_state(state)

    smoke_py = wd / "smoke_check.py"
    smoke_py.write_text(SMOKE_CHECK_PY)
    smoke_json = out / "smoke_check.json"
    _require(tool_runner([sys.executable, str(smoke_py), str(smoke_json)],
                         timeout_s=stage_allowance_s(state, "install"),
                         log_path=out / "smoke_check.log", state=state,
                         label="smoke check"),
             "install", "the smoke check of the installed tools")
    if smoke_json.exists():
        state["machine"]["engines"] = json.loads(smoke_json.read_text())
    save_state(state)

    write_record(
        state, f"control-install_tag-{TAG}.json",
        cell={"tag": TAG, "arm": "install", "stage": "install"},
        inputs=describe_inputs([smoke_json] + [wd / Path(d["url"]).name
                                               for d in downloads]),
        metric="installs, downloads and the smoke check of every tool",
        values={"downloads": downloads, "apt_packages": apt_records,
                "pip_reports": pip_reports,
                "engines": state["machine"].get("engines"),
                "machine": machine_labels(state),
                "labels": common_labels(state)},
        threshold={"every_tool_must_start": True,
                   "allowed_hosts": sorted(ALLOWED_DOWNLOAD_HOSTS)},
        decision_rule=(
            "Every declared package installs at its pinned version, every "
            "download comes from an allowed source with its hash recorded, and "
            "every tool answers a start-up check. Any failure is PASS nowhere: "
            "it stops the run with exit 2 and no substitute is tried."),
        decision="PASS",
        notes=LABEL_STANDIN_ONLY,
    )


def stage_controls(state, tool_runner):
    """The timer check, the empty-input run and the unit-and-scale record."""
    guard_before_stage(state, "controls")
    out = Path(state["out_dir"])
    wd = work_dir(state)

    started = time.time()
    res = tool_runner(["sleep", "60"], timeout_s=min(
        120, max(1.0, inner_tool_timeout_s(state))),
        log_path=out / "controls.log", state=state, label="planted 60 s sleep")
    measured = time.time() - started
    ok, err = sleep_check(measured)
    append_row(state, "controls", {"control": "planted_sleep",
                                   "planted_s": SLEEP_CHECK_S,
                                   "measured_s": measured,
                                   "relative_error": err,
                                   "returncode": res.get("returncode")})
    write_record(
        state, f"control-sleep_tag-{TAG}.json",
        cell={"tag": TAG, "arm": "controls", "stage": "sleep_check"},
        inputs=describe_inputs([out / f"rows_controls_tag-{TAG}.jsonl"]),
        metric="a planted 60 second wait, timed by the same clock as every "
               "measurement",
        values={"planted_s": SLEEP_CHECK_S, "measured_s": measured,
                "relative_error": err, "machine": machine_labels(state),
                "labels": common_labels(state)},
        threshold={"max_relative_error": SLEEP_CHECK_TOLERANCE},
        decision_rule=(
            "The clock must report a known 60 second wait within 5 percent. "
            "More than that means every timing in this run is wrong by an "
            "unknown amount, so the run is invalid and stops with exit 2."),
        decision="PASS" if ok else "FAIL",
    )
    if not ok:
        raise FailStop("controls", f"the timer check was off by {err:.3%}", 2)

    empty_dir = wd / "empty_input"
    empty_out = wd / "empty_output"
    empty_dir.mkdir(exist_ok=True)
    empty_out.mkdir(exist_ok=True)
    t0 = time.time()
    tool_runner(["colabfold_batch", "--help"],
                timeout_s=min(120, max(1.0, inner_tool_timeout_s(state))),
                log_path=out / "controls.log", state=state,
                label="empty-input run")
    empty_s = time.time() - t0
    empty_bytes = apparent_bytes([empty_out])
    empty = empty_run_check(empty_s, empty_bytes)
    if empty["label"] and empty["label"] not in state["labels"]:
        state["labels"].append(empty["label"])
    state.setdefault("measurements", {})["controls"] = {
        "sleep": {"measured_s": measured, "relative_error": err},
        "empty_run": dict(empty, seconds=empty_s, bytes=empty_bytes),
    }
    save_state(state)
    append_row(state, "controls", {"control": "empty_run", "seconds": empty_s,
                                   "bytes": empty_bytes, **empty})
    write_record(
        state, f"control-empty-run_tag-{TAG}.json",
        cell={"tag": TAG, "arm": "controls", "stage": "empty_run"},
        inputs=describe_inputs([out / f"rows_controls_tag-{TAG}.jsonl"]),
        metric="the time and bytes an empty input costs before any real work",
        values={"seconds": empty_s, "bytes": empty_bytes,
                "overhead_s": empty["overhead_s"],
                "overhead_bytes": empty["overhead_bytes"],
                "machine": machine_labels(state),
                "labels": common_labels(state) + (
                    [empty["label"]] if empty["label"] else [])},
        threshold={"max_seconds": EMPTY_RUN_MAX_S,
                   "max_bytes": EMPTY_RUN_MAX_BYTES},
        decision_rule=(
            "An empty input should cost under 2 seconds and under 1 mebibyte. "
            "Any excess is setup, not work: it is subtracted from the later "
            "measurements and every affected record is labelled."),
        decision="PASS" if empty["clean"] else "VOID",
    )
    write_unit_and_scale_record(state, final=False)


def write_unit_and_scale_record(state, final=False):
    """Show the raw numbers next to the converted ones, in both directions.

    Written once before any band is compared, and again at the end with the raw
    figures the run actually produced. A unit error is the cheapest way to pass
    or fail a band for no reason, and this record is what catches it.
    """
    meas = state.get("measurements") or {}
    c1_rows = [r for r in (meas.get("C1") or {}).get("runs", [])]
    c2_rows = [c for c in (meas.get("C2") or {}).get("complexes", [])]
    c4_rows = [a for a in (meas.get("C4") or {}).get("artifacts", [])]
    values = {
        "worked_examples": {
            "1800 seconds per prediction run is hours": 1800 / 3600.0,
            "250000 steps of 2 fs in 335 seconds is ns/day":
                ns_per_day_from_wallclock(250000, 2.0, 335.0),
            "1073741824 bytes per run over 216 runs is GiB":
                gib_for_grid(1073741824, GRID_RUNS),
            "3600 seconds at USD 1.99 per hour is USD":
                cost_usd(3600, 1.99),
        },
        "raw_alphafold_seconds": [r.get("wallclock_s") for r in c1_rows],
        "raw_alphafold_hours": [(r.get("wallclock_s") or 0) / 3600.0
                                for r in c1_rows],
        "md_engine_rate_lines": [
            {"complex": c.get("complex"),
             "engine_ns_per_day": c.get("engine_ns_per_day"),
             "wallclock_ns_per_day": c.get("wallclock_ns_per_day"),
             "steps": c.get("steps"), "seconds": c.get("wallclock_s")}
            for c in c2_rows],
        "raw_bytes_per_artifact": [
            {"artifact": a.get("artifact"), "kind": a.get("kind"),
             "bytes": a.get("bytes")} for a in c4_rows],
        "machine": machine_labels(state),
        "labels": common_labels(state),
        "stage": "endpoints" if final else "controls",
    }
    return write_record(
        state, f"control-unit-and-scale_tag-{TAG}.json",
        cell={"tag": TAG, "arm": "controls", "stage": "unit_and_scale"},
        inputs=describe_inputs([Path(state["out_dir"]) /
                                f"rows_controls_tag-{TAG}.jsonl"]),
        metric="raw readings beside the converted values, for every unit the "
               "run uses",
        values=values,
        threshold={"no_band_is_compared_before_this_record_exists": True},
        decision_rule=(
            "This record makes no call. It exists so a reader can redo every "
            "conversion from the raw reading. It is written before any band is "
            "compared, and written again at the end carrying the run's own raw "
            "numbers."),
        decision="RECORDED",
        notes=("Written in the controls stage before any comparison; rewritten "
               "in the decisions stage with the raw figures the run produced."),
    )


def _overhead_s(state) -> float:
    ctl = ((state.get("measurements") or {}).get("controls") or {})
    return float((ctl.get("empty_run") or {}).get("overhead_s") or 0.0)


def adjusted_seconds(state, seconds: float) -> float:
    """Take the measured setup overhead off a timed run, when the empty-input
    control showed there was any. The records say when this happened."""
    return max(0.0, float(seconds) - _overhead_s(state))


DOCK_SETUP = "lightdock3_setup.py"
DOCK_RUN = "lightdock3.py"
DOCK_CONFORMATIONS = "lgd_generate_conformations.py"
DOCK_RANK = "lgd_rank.py"
DOCK_SWARMS = 10
DOCK_GLOWWORMS = 10
DOCK_STEPS = 10


def dock(state, tool_runner, *, stage, fixed_pdb, mobile_pdb, outdir, cores,
         timeout_s, label):
    """Dock one pair: set up, search, build the poses, rank them.

    Returns the best-ranked pose file, the ranking table and the seconds spent.
    The search seeds are all fixed at 0, so serial and parallel differ only in
    how many cores the search used.
    """
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    logs = Path(state["out_dir"]) / "docking.log"
    started = time.time()
    steps = [
        ([DOCK_SETUP, str(fixed_pdb), str(mobile_pdb),
          "-s", str(DOCK_SWARMS), "-g", str(DOCK_GLOWWORMS),
          "--noxt", "--noh", "--now",
          "-rs", "0", "-ls", "0", "-sp", "0"], "set up the docking"),
        ([DOCK_RUN, "setup.json", str(DOCK_STEPS), "-c", str(cores),
          "-s", "fastdfire"], "run the docking search"),
        ([DOCK_CONFORMATIONS, str(fixed_pdb), str(mobile_pdb),
          f"swarm_0/gso_{DOCK_STEPS}.out", str(DOCK_GLOWWORMS)],
         "build the docked poses"),
        ([DOCK_RANK, str(DOCK_SWARMS), str(DOCK_STEPS)], "rank the poses"),
    ]
    for cmd, what in steps:
        left = min(timeout_s - (time.time() - started),
                   max(1.0, inner_tool_timeout_s(state)))
        if left <= 0:
            return {"timed_out": True, "seconds": time.time() - started,
                    "pose": None, "table": ""}
        res = tool_runner(cmd, timeout_s=left, log_path=logs, state=state,
                          cwd=outdir, label=f"{label}: {what}")
        if res.get("timed_out"):
            return {"timed_out": True, "seconds": time.time() - started,
                    "pose": None, "table": ""}
        if res.get("returncode") != 0:
            raise FailStop(stage, f"{what} failed with exit "
                                  f"{res.get('returncode')}", 2)
    table_path = outdir / "rank_by_scoring.list"
    table = table_path.read_text(errors="replace") if table_path.exists() else ""
    pose = top_pose(table)
    pose_path = (outdir / pose) if pose else None
    if pose_path is not None and not pose_path.exists():
        found = sorted(outdir.glob("swarm_0/lightdock_*.pdb"))
        pose_path = found[0] if found else None
    return {"timed_out": False, "seconds": time.time() - started,
            "pose": str(pose_path) if pose_path else None, "table": table,
            "cores": cores}


def _pose_role_atoms(capsid_atoms, pose_text):
    """One docked complex as role-tagged atoms.

    The pose file holds the partner that moved. Whatever chain letter the tool
    gave it, it is the receptor here; the capsid is the fixed partner's own
    atoms. Keying by role is what makes a renamed chain harmless.
    """
    pose_atoms = read_pdb_atoms(pose_text)
    pose_chains = {a["chain"] for a in pose_atoms}
    roles = {c: "receptor" for c in pose_chains}
    out = apply_roles(pose_atoms, roles)
    cap_chain = capsid_atoms[0]["chain"] if capsid_atoms else "A"
    out += apply_roles(capsid_atoms, {cap_chain: "capsid"})
    return out


def stage_anchor(state, tool_runner):
    """Re-dock the published complex, serially and then in parallel.

    This is the gate for everything else: if the tool cannot put a known complex
    back together, the four inputs are not worth measuring.
    """
    allowance = guard_before_stage(state, "anchor")
    out = Path(state["out_dir"])
    wd = work_dir(state)
    pdb_path = wd / Path(DOWNLOADS["pdb_6ihb"]).name
    if not pdb_path.exists():
        raise FailStop("anchor", "the published structure file is missing", 2)
    native = read_pdb_atoms(pdb_path.read_text(errors="replace"))
    chains = choose_anchor_chains(native)
    roles = {chains["capsid_chain"]: "capsid",
             chains["receptor_chain"]: "receptor"}
    reference = apply_roles(native, roles)
    reference_contacts = residue_contacts(reference)

    capsid_atoms = [a for a in native if a["chain"] == chains["capsid_chain"]]
    receptor_atoms = [a for a in native if a["chain"] == chains["receptor_chain"]]
    capsid_pdb = wd / "anchor_capsid.pdb"
    receptor_pdb = wd / "anchor_receptor.pdb"
    capsid_pdb.write_text(write_pdb(capsid_atoms))
    receptor_pdb.write_text(write_pdb(receptor_atoms))

    half = max(1.0, allowance / 2.0)
    serial = dock(state, tool_runner, stage="anchor", fixed_pdb=capsid_pdb,
                  mobile_pdb=receptor_pdb, outdir=wd / "anchor_serial", cores=1,
                  timeout_s=half, label="anchor, one job at a time")
    parallel = dock(state, tool_runner, stage="anchor", fixed_pdb=capsid_pdb,
                    mobile_pdb=receptor_pdb, outdir=wd / "anchor_parallel",
                    cores=max(2, os.cpu_count() or 2),
                    timeout_s=half, label="anchor, jobs in parallel")

    overlap = iface_rmsd = sp_rmsd = None
    call_serial = call_parallel = None
    if serial["pose"] and parallel["pose"]:
        pose_s = _pose_role_atoms(
            capsid_atoms, Path(serial["pose"]).read_text(errors="replace"))
        pose_p = _pose_role_atoms(
            capsid_atoms, Path(parallel["pose"]).read_text(errors="replace"))
        overlap = contact_overlap(reference_contacts, residue_contacts(pose_s))
        iface_rmsd = interface_backbone_rmsd(reference, pose_s)
        sp_rmsd = whole_chain_rmsd(pose_s, pose_p)
        call_serial = bind_call(pose_s)
        call_parallel = bind_call(pose_p)

    passed, reasons = anchor_decision(overlap, iface_rmsd, sp_rmsd,
                                      call_serial, call_parallel)
    for arm, res in (("serial", serial), ("parallel", parallel)):
        append_row(state, "anchor", {
            "arm": arm, "cores": res.get("cores"), "seconds": res["seconds"],
            "pose": res["pose"], "timed_out": res["timed_out"],
            "incomplete": bool(res["timed_out"]), "seed": 0,
        })
    state.setdefault("measurements", {})["anchor"] = {
        "contact_overlap": overlap, "interface_backbone_rmsd": iface_rmsd,
        "serial_parallel_rmsd": sp_rmsd, "call_serial": call_serial,
        "call_parallel": call_parallel, "passed": passed, "reasons": reasons,
        "chains": chains,
    }
    save_state(state)
    state["standin_chains"] = chains

    write_record(
        state, f"endpoint-anchor_tag-{TAG}.json",
        cell={"tag": TAG, "arm": "anchor", "stage": "anchor"},
        inputs=describe_inputs([pdb_path, out / f"rows_anchor_tag-{TAG}.jsonl"]),
        metric="re-docking a known complex: share of the published contacts "
               "reproduced, or how far the interface sits from the published "
               "position",
        values={
            "measured": overlap,
            "contact_overlap": overlap,
            "interface_backbone_rmsd_angstrom": iface_rmsd,
            "serial_parallel_rmsd_angstrom": sp_rmsd,
            "published": {"entry": "6IHB", "source": DOWNLOADS["pdb_6ihb"],
                          "sha256": sha256_file(pdb_path),
                          "reference_contacts": len(reference_contacts)},
            "tolerance": {"min_contact_overlap": ANCHOR_OVERLAP_MIN,
                          "max_interface_rmsd_angstrom": ANCHOR_RMSD_MAX_A,
                          "max_serial_parallel_rmsd_angstrom":
                              ANCHOR_SERIAL_PARALLEL_RMSD_MAX_A},
            "call_serial": call_serial, "call_parallel": call_parallel,
            "reasons": reasons,
            "chains": chains,
            "independent_code": "not run: single docking code",
            "machine": machine_labels(state),
            "labels": common_labels(state) + [LABEL_SP_WHOLE_CHAIN,
                                              LABEL_SAME_BOX],
        },
        threshold={"min_contact_overlap": ANCHOR_OVERLAP_MIN,
                   "max_interface_rmsd_angstrom": ANCHOR_RMSD_MAX_A,
                   "max_serial_parallel_rmsd_angstrom":
                       ANCHOR_SERIAL_PARALLEL_RMSD_MAX_A},
        decision_rule=(
            "The re-docked pose passes when it reproduces at least 50 percent "
            "of the published residue-residue contacts, or sits within 5 "
            "Angstrom of the published interface, and when the serial and the "
            "parallel repeat put the receptor within 2 Angstrom of each other "
            "with the same touching call. Contacts are keyed by role, not by "
            "the chain letter in the file. The interface distance is measured "
            "in the capsid's frame with no fitting. A miss writes all four "
            "inputs VOID, marks the run invalid and exits 4."),
        decision="PASS" if passed else "FAIL",
        notes=("Serial and parallel are two repeats on one box, not a "
               "replication. A second, independent docking code was not run."),
    )
    if not passed:
        raise FailStop("anchor", "the re-docking missed: " + "; ".join(reasons), 4)


def _standin_pairs(state):
    wd = work_dir(state)
    pdb_path = wd / Path(DOWNLOADS["pdb_6ihb"]).name
    native = read_pdb_atoms(pdb_path.read_text(errors="replace"))
    chains = state.get("standin_chains") or choose_anchor_chains(native)
    return native, chains, build_standin_pairs(native, chains)


def stage_aux(state, tool_runner):
    """The side work per pair: docking, interface analysis, call-table row.

    Installs, downloads and setup are deliberately outside this timing: the card
    means the per-pair work, not the one-off cost of the box.
    """
    allowance = guard_before_stage(state, "aux")
    out = Path(state["out_dir"])
    wd = work_dir(state)
    native, chains, pairs = _standin_pairs(state)
    capsid_atoms = [a for a in native if a["chain"] == chains["capsid_chain"]]
    rows = []
    call_table = out / f"call_table_tag-{TAG}.jsonl"
    started_stage = time.time()

    for pair in pairs:
        used = time.time() - started_stage
        if used >= allowance:
            record_stop(state, "aux", "stage_ceiling",
                        f"the docking stage reached its {allowance:.0f} s "
                        f"allowance after {len(rows)} pairs")
            break
        pair_dir = wd / pair["pair"]
        pair_dir.mkdir(parents=True, exist_ok=True)
        rec_pdb = pair_dir / "receptor.pdb"
        cap_pdb = pair_dir / "capsid.pdb"
        rec_pdb.write_text(write_pdb(
            [a for a in pair["atoms"] if a["chain"] == pair["receptor_chain"]]))
        cap_pdb.write_text(write_pdb(
            [a for a in pair["atoms"] if a["chain"] == pair["capsid_chain"]]))

        budget = min(PER_PAIR_DOCK_CEILING_S, allowance - used)
        t0 = time.time()
        res = dock(state, tool_runner, stage="aux", fixed_pdb=cap_pdb,
                   mobile_pdb=rec_pdb, outdir=pair_dir / "dock", cores=1,
                   timeout_s=budget, label=f"docking {pair['pair']}")
        analysis = None
        if res["pose"]:
            pose_atoms = _pose_role_atoms(
                capsid_atoms, Path(res["pose"]).read_text(errors="replace"))
            analysis = interface_analysis(pose_atoms)
            with open(call_table, "a") as fh:
                fh.write(json.dumps({"pair": pair["pair"],
                                     "capsid_slot": pair["capsid_slot"],
                                     **analysis}, sort_keys=True) + "\n")
        seconds = adjusted_seconds(state, time.time() - t0)
        truncated = bool(res["timed_out"]) or seconds >= PER_PAIR_DOCK_CEILING_S
        row = {
            "pair": pair["pair"], "capsid_slot": pair["capsid_slot"],
            "seconds": seconds, "hours": seconds / 3600.0,
            "truncated": truncated, "incomplete": bool(res["timed_out"]),
            "pose": res["pose"], "cores": 1,
            "receptor_chain": pair["receptor_chain"],
            "capsid_chain": pair["capsid_chain"],
            "receptor_length": pair["receptor_length"],
            "capsid_length": pair["capsid_length"],
            "total_length": pair["total_length"],
            "analysis": analysis,
            "excludes": "installs, downloads and setup are not in this time",
        }
        rows.append(row)
        append_row(state, "C3", row)
        state.setdefault("measurements", {}).setdefault(
            "C3", {}).setdefault("pairs", []).append(row)
        state["measurements"]["C3"]["poses"] = [
            r["pose"] for r in rows if r.get("pose")]
        save_state(state)
        if truncated:
            log(f"aux: {pair['pair']} hit its {PER_PAIR_DOCK_CEILING_S} s cap; "
                f"kept as a row, not counted in the mean")

    finished = [r for r in rows if not r["truncated"]]
    if len(finished) < MIN_AUX_PAIRS:
        raise GuardStop("aux", "stage_ceiling",
                        f"only {len(finished)} pairs finished inside the "
                        f"allowance, below {MIN_AUX_PAIRS}")


def stage_af2(state, tool_runner):
    """Time the structure predictions: three pairs, three seeds, seed first.

    Seed-major order means every pair is seen once before any pair is seen
    twice, so a stop part way through still covers all three pairs.
    """
    allowance = guard_before_stage(state, "af2")
    out = Path(state["out_dir"])
    wd = work_dir(state)
    _native, _chains, pairs = _standin_pairs(state)
    started_stage = time.time()
    rows = []

    for pair in pairs:
        fasta = wd / f"{pair['pair']}.fasta"
        fasta.write_text(
            f">{pair['pair']}\n"
            f"{pair['receptor_sequence']}:{pair['capsid_sequence']}\n")

    for seed in AF2_SEEDS:
        for pair in pairs:
            used = time.time() - started_stage
            done = len(rows)
            remaining = len(AF2_SEEDS) * len(pairs) - done
            if rows:
                mean_so_far = statistics.fmean(r["wallclock_s"] for r in rows)
                if used + mean_so_far > allowance:
                    raise GuardStop(
                        "af2", "time_guard",
                        f"the next run needs about {mean_so_far:.0f} s and only "
                        f"{allowance - used:.0f} s of this stage is left; "
                        f"{done} of {done + remaining} runs finished")
            if used >= allowance:
                raise GuardStop("af2", "stage_ceiling",
                                f"the prediction stage reached its "
                                f"{allowance:.0f} s allowance")
            run_out = wd / f"af2_{pair['pair']}_seed{seed}"
            log_path = out / f"af2_{pair['pair']}_seed{seed}.log"
            cmd = [
                "colabfold_batch",
                "--num-models", str(AF2_MODELS),
                "--num-recycle", str(AF2_RECYCLES),
                "--recycle-early-stop-tolerance", "-1",
                "--msa-mode", "single_sequence",
                "--model-type", "alphafold2_multimer_v3",
                "--num-seeds", "1",
                "--random-seed", str(seed),
                "--data", str(wd),
                str(wd / f"{pair['pair']}.fasta"), str(run_out),
            ]
            budget = min(allowance - used, max(1.0, inner_tool_timeout_s(state)))
            t0 = time.time()
            res = tool_runner(cmd, timeout_s=budget, log_path=log_path,
                              state=state, label=f"predict {pair['pair']} "
                                                 f"seed {seed}")
            wall = adjusted_seconds(state, time.time() - t0)
            parsed = parse_af2_timing_rows(
                log_path.read_text(errors="replace") if log_path.exists() else "")
            row = {
                "pair": pair["pair"], "seed": seed, "wallclock_s": wall,
                "hours": wall / 3600.0,
                "per_model_seconds": parsed["models"],
                "compile_excluded_s": compile_excluded_seconds(
                    wall, parsed["models"]),
                "queries": parsed["queries"],
                "incomplete": bool(res["timed_out"]),
                "returncode": res.get("returncode"),
                "models": AF2_MODELS, "recycles": AF2_RECYCLES,
                "early_stopping": False, "msa_mode": "single_sequence",
                "total_length": pair["total_length"],
                "output_dir": str(run_out),
            }
            append_row(state, "C1", row)
            state.setdefault("measurements", {}).setdefault(
                "C1", {}).setdefault("runs", []).append(row)
            save_state(state)
            if res["timed_out"]:
                raise GuardStop("af2", "tool_timeout",
                                f"{pair['pair']} seed {seed} ran past its "
                                f"allowance; its row is kept and not counted")
            if res.get("returncode") != 0:
                raise FailStop("af2", f"the prediction of {pair['pair']} seed "
                                      f"{seed} failed with exit "
                                      f"{res.get('returncode')}", 2)
            rows.append(row)


def stage_md(state, tool_runner):
    """Time the dynamics: one docked complex per pair, one 0.5 ns segment."""
    allowance = guard_before_stage(state, "md")
    out = Path(state["out_dir"])
    wd = work_dir(state)
    worker = wd / "md_worker.py"
    worker.write_text(MD_WORKER_PY)
    poses = ((state.get("measurements") or {}).get("C3") or {}).get("poses") or []
    if not poses:
        raise GuardStop("md", "time_guard",
                        "no docked pose was produced, so there is nothing to "
                        "simulate")
    steps = int(round(MD_PRODUCTION_NS * 1e6 / MD_TIMESTEP_FS))
    started_stage = time.time()
    rows = []

    for i, pose in enumerate(poses[:3]):
        used = time.time() - started_stage
        if used >= allowance:
            raise GuardStop("md", "stage_ceiling",
                            f"the dynamics stage reached its {allowance:.0f} s "
                            f"allowance after {len(rows)} complexes")
        name = f"complex{i + 1}"
        result_json = wd / f"md_{name}.json"
        log_path = out / f"md_{name}.log"
        budget = min(PER_COMPLEX_MD_CEILING_S, allowance - used,
                     max(1.0, inner_tool_timeout_s(state)))
        res = tool_runner(
            [sys.executable, str(worker), str(pose), str(result_json),
             str(steps), str(MD_TIMESTEP_FS), str(MD_VELOCITY_SEED)],
            timeout_s=budget, log_path=log_path, state=state,
            label=f"dynamics on {name}")
        text = log_path.read_text(errors="replace") if log_path.exists() else ""
        parsed = parse_md_log(text)
        payload = {}
        if result_json.exists():
            try:
                payload = json.loads(result_json.read_text())
            except ValueError:
                payload = {}
        wall = payload.get("wallclock_s")
        atoms = payload.get("atoms", parsed["atoms"])
        engine_rate = parsed["speeds"][-1] if parsed["speeds"] else None
        wallclock_rate = ns_per_day_from_wallclock(
            payload.get("steps", steps), MD_TIMESTEP_FS, wall)
        row = {
            "complex": name, "pose": str(pose), "atoms": atoms,
            "steps": payload.get("steps", steps),
            "timestep_fs": MD_TIMESTEP_FS,
            "wallclock_s": wall,
            "engine_ns_per_day": engine_rate,
            "wallclock_ns_per_day": wallclock_rate,
            "rates_disagree": rates_disagree(engine_rate, wallclock_rate),
            "water_padding_nm": payload.get("padding_nm"),
            "frame_interval_steps": payload.get("frame_interval_steps"),
            "precision": payload.get("precision"),
            "platform": payload.get("platform"),
            "engine_version": payload.get("openmm_version"),
            "velocity_seed": MD_VELOCITY_SEED,
            "incomplete": bool(res["timed_out"]) or wall is None,
            "returncode": res.get("returncode"),
            "trajectory": payload.get("trajectory"),
            "log": str(log_path),
        }
        append_row(state, "C2", row)
        state.setdefault("measurements", {}).setdefault(
            "C2", {}).setdefault("complexes", []).append(row)
        save_state(state)
        if res["timed_out"]:
            raise GuardStop("md", "tool_timeout",
                            f"{name} ran past its allowance; its row is kept "
                            f"and not counted")
        if res.get("returncode") != 0:
            raise FailStop("md", f"the dynamics run on {name} failed with exit "
                                 f"{res.get('returncode')}", 2)
        rows.append(row)


def stage_storage(state, tool_runner):
    """Measure what one run of the grid writes, then scale it to the grid."""
    guard_before_stage(state, "storage")
    wd = work_dir(state)
    meas = state.get("measurements") or {}
    arts = []

    af2_runs = (meas.get("C1") or {}).get("runs") or []
    if af2_runs:
        d = Path(af2_runs[0]["output_dir"])
        arts.append({"artifact": str(d), "kind": "af2",
                     "bytes": apparent_bytes([d]), "intermediate": False,
                     "what": "the structure-prediction outputs of one run"})
    dock_pairs = (meas.get("C3") or {}).get("pairs") or []
    if dock_pairs and dock_pairs[0].get("pose"):
        d = Path(dock_pairs[0]["pose"]).parent
        arts.append({"artifact": str(d), "kind": "docking",
                     "bytes": apparent_bytes([d]), "intermediate": True,
                     "what": "the docking poses and tables of one pair"})
    md_rows = (meas.get("C2") or {}).get("complexes") or []
    if md_rows:
        files = [p for p in (md_rows[0].get("trajectory"),
                             md_rows[0].get("log")) if p]
        arts.append({"artifact": ", ".join(files) or str(wd), "kind": "md",
                     "bytes": apparent_bytes(files), "intermediate": False,
                     "simulated_ns": MD_PRODUCTION_NS,
                     "what": "the trajectory and logs of one 0.5 ns segment"})
    for a in arts:
        append_row(state, "C4", a)
    state.setdefault("measurements", {}).setdefault("C4", {})["artifacts"] = arts
    save_state(state)
    if not arts:
        raise GuardStop("storage", "stage_ceiling",
                        "no artifact of any kind was produced to measure")


ONBOX_STAGES = [
    ("install", stage_install),
    ("controls", stage_controls),
    ("anchor", stage_anchor),
    ("aux", stage_aux),
    ("af2", stage_af2),
    ("md", stage_md),
    ("storage", stage_storage),
]
STAGE_GROUPS = {
    "extract": ["install", "controls"],
    "generate": ["anchor", "aux", "af2", "md", "storage"],
    "endpoints": [],
    "all": [name for name, _ in ONBOX_STAGES],
}


# ===========================================================================
# Entry point
# ===========================================================================


def prepare_state(stage_name):
    state = load_state()
    state["out_dir"] = str(OUT_DIR)
    Path(state["out_dir"]).mkdir(parents=True, exist_ok=True)
    state["caps"] = compute_caps()
    if state["caps"]["remote_timeout_defaulted"] and \
            LABEL_TIMEOUT_DEFAULT not in state["labels"]:
        state["labels"].append(LABEL_TIMEOUT_DEFAULT)
    atomic_write_json(Path(state["out_dir"]) / f"caps_tag-{TAG}.json",
                      state["caps"])
    log(f"stage {stage_name}: caps {json.dumps(state['caps'], sort_keys=True)}")
    save_state(state)
    return state


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Measure four cost inputs of one design card on one box.")
    parser.add_argument("--selftest", action="store_true",
                        help="run the standard-library checks and exit")
    parser.add_argument("--stage", default="all", choices=sorted(STAGE_GROUPS),
                        help="which part of the run to do")
    parser.add_argument("--after-timeout", action="store_true",
                        help="the outer timeout fired; write the decisions and "
                             "report a guard stop")
    args = parser.parse_args(argv)

    if args.selftest:
        return selftest()

    stage_name = "endpoints" if args.after_timeout else args.stage
    state = prepare_state(stage_name)
    wanted = STAGE_GROUPS[stage_name]
    stages = [(name, fn) for name, fn in ONBOX_STAGES if name in wanted]

    if args.after_timeout:
        record_stop(state, "outer_timeout", "outer_timeout",
                    "the launcher's outer timeout fired (return code 124); the "
                    "tools were stopped by process group and the decisions are "
                    "written from what finished")

    writes_decisions = stage_name in ("all", "endpoints")
    endpoints_fn = stage_endpoints if writes_decisions else (lambda s, t: {})
    exit_code, _results = run_stages(state, stages, run_tool, endpoints_fn,
                                     settle_inputs=writes_decisions)
    if writes_decisions:
        write_run_done(state, exit_code)
    log(f"stage {stage_name}: finished with exit code {exit_code}")
    return exit_code


# ===========================================================================
# Selftest. Standard library only, no graphics processor, no network, no tool.
#
# Every parser gets a real-looking input and a malformed one. Every decision
# gets planted rows whose answer is known in advance. The stage flow itself is
# run with stand-in stages, so the paths through a stop are exercised, not just
# the arithmetic inside them.
# ===========================================================================


class Checks:
    """Counts checks and remembers what failed, so the last line is honest."""

    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failures = []

    def ok(self, condition, label):
        self.total += 1
        if condition:
            self.passed += 1
        else:
            self.failures.append(label)
        return bool(condition)

    def eq(self, got, want, label, tol=None):
        if tol is None:
            good = got == want
        else:
            good = (got is not None and want is not None
                    and abs(float(got) - float(want)) <= tol)
        return self.ok(good, f"{label}: got {got!r}, wanted {want!r}")


def _planted_residue(chain, resseq, x, y, z, resname="ALA"):
    """Four backbone atoms of one residue, at and just past a given point."""
    out = []
    for i, name in enumerate(BACKBONE_ATOMS):
        out.append({"record": "ATOM", "name": name, "resname": resname,
                    "chain": chain, "resseq": resseq,
                    "x": x + 0.5 * i, "y": y, "z": z, "element": name[0]})
    return out


def _planted_complex(receptor_chain="B", capsid_chain="A", receptor_x=4.0,
                     contacting=(1, 2, 3, 4, 5, 6), far=(7, 8, 9)):
    """A toy complex: six receptor residues touch six capsid residues, and
    three more receptor residues sit well away from the capsid."""
    capsid, receptor = [], []
    for i in range(1, 7):
        capsid += _planted_residue(capsid_chain, i, 0.0, i * 10.0, 0.0)
    for i in contacting:
        receptor += _planted_residue(receptor_chain, i, receptor_x, i * 10.0, 0.0)
    for i in far:
        receptor += _planted_residue(receptor_chain, i, receptor_x, i * 10.0,
                                     100.0)
    return capsid, receptor


def _roled(capsid, receptor, capsid_chain="A", receptor_chain="B"):
    return (apply_roles(capsid, {capsid_chain: "capsid"})
            + apply_roles(receptor, {receptor_chain: "receptor"}))


def _shift(atoms, dx=0.0, dy=0.0, dz=0.0, only=None):
    out = []
    for a in atoms:
        b = dict(a)
        if only is None or a["resseq"] in only:
            b["x"] += dx
            b["y"] += dy
            b["z"] += dz
        out.append(b)
    return out


def _af2_runs(hours, pairs=("pair1", "pair2", "pair3"), seeds=(0, 1, 2)):
    """Nine planted prediction timings whose mean is exactly the wanted hours,
    with a real spread of ten seconds across the seeds of each pair."""
    centre = hours * 3600.0
    rows = []
    for pair in pairs:
        for offset, seed in zip((-10.0, 0.0, 10.0), seeds):
            rows.append({"pair": pair, "seed": seed,
                         "wallclock_s": centre + offset, "incomplete": False})
    return rows


def _md_complexes(rates, atoms=150000):
    return [{"complex": f"complex{i + 1}", "atoms": atoms, "steps": 250000,
             "wallclock_ns_per_day": r, "engine_ns_per_day": r,
             "incomplete": False}
            for i, r in enumerate(rates)]


def _aux_pairs(seconds_list):
    return [{"pair": f"pair{i + 1}", "seconds": s, "truncated": False}
            for i, s in enumerate(seconds_list)]


def _storage_artifacts(total_bytes):
    """One artifact of each kind, together making the wanted total."""
    share = total_bytes // 3
    rest = total_bytes - 2 * share
    return [{"artifact": "af2", "kind": "af2", "bytes": share,
             "intermediate": False},
            {"artifact": "docking", "kind": "docking", "bytes": share,
             "intermediate": True},
            {"artifact": "md", "kind": "md", "bytes": rest,
             "intermediate": False}]


def _fresh_state(tmp, gpu="NVIDIA A100-SXM4-40GB"):
    state = new_state(tmp)
    state["caps"] = {"price_usd_per_hour": 1.99, "budget_left_usd": 5.0,
                     "remote_timeout_s": 7200.0, "stop_at_s": 7200.0,
                     "remote_timeout_defaulted": False,
                     "seconds_the_money_buys": budget_seconds(5.0, 1.99),
                     "binding_cap": "time"}
    state["machine"] = {"gpu_name": gpu, "driver_version": "570.148.08",
                        "instance_type": "gpu_1x_a100_sxm4"}
    return state


def _decide(key, state, measurements):
    state.setdefault("measurements", {})[key] = measurements
    return DECIDERS[key](state)


def selftest():  # noqa: C901 - one long list of planted cases, read top to bottom
    import tempfile

    c = Checks()

    # --- the directive's own numbers must add up -------------------------
    c.eq(CEILING_SUM_S, 7200,
         "the stage ceilings plus the margin and the decisions slot")
    c.eq(INNER_TOOL_BACKOFF_S - OUTER_KILL_BACKOFF_S, 100,
         "the inner tool stop fires 100 s before the outer kill")
    c.ok(DEFAULT_BUDGET_LEFT_USD <= 5 and DEFAULT_REMOTE_TIMEOUT <= 7200,
         "no default cap exceeds the gate's own")

    # --- parsers ---------------------------------------------------------
    c.eq(parse_engine_rate_line("Speed: 128.96 ns/day"), 128.96, "rate line")
    c.eq(parse_engine_rate_line("#\"Step\",\"Speed (ns/day)\""), None,
         "a header is not a rate line")
    c.eq(parse_engine_rate_line("nothing to see"), None, "malformed rate line")
    md_log = (
        'atoms: 150000\n'
        'production_steps: 250000\n'
        '#"Step","Time (ps)","Speed (ns/day)"\n'
        '5000,10.0,120.5\n'
        '10000,20.0,128.96\n'
    )
    parsed = parse_md_log(md_log)
    c.eq(parsed["atoms"], 150000, "atom count from the engine log")
    c.eq(parsed["steps"], 250000, "production steps from the engine log")
    c.eq(parsed["speeds"][-1], 128.96, "last speed from the engine log")
    c.eq(parse_md_log("garbage\n")["speeds"], [], "malformed engine log")
    c.eq(round(ns_per_day_from_wallclock(250000, 2.0, 335.0), 2), 128.96,
         "250000 steps of 2 fs in 335 s")
    c.eq(ns_per_day_from_wallclock(250000, 2.0, 0), None, "a zero wall-clock")
    c.ok(not rates_disagree(129.0, 128.96), "engine and wall-clock agree")
    c.ok(rates_disagree(200.0, 100.0), "engine and wall-clock disagree")

    af2_log = (
        "2026-10-21 10:00:00,000 Query 1/3: pair1 (length 912)\n"
        "2026-10-21 10:05:00,000 alphafold2_multimer_v3_model_1_seed_000 took "
        "500.0s (19 recycles) with pLDDT 80.1 and ptmscore 0.70\n"
        "2026-10-21 10:06:40,000 alphafold2_multimer_v3_model_2_seed_000 took "
        "100.0s (19 recycles) with pLDDT 79.0 and ptmscore 0.69\n"
        "2026-10-21 10:08:20,000 alphafold2_multimer_v3_model_3_seed_000 took "
        "100.0s (19 recycles) with pLDDT 78.5 and ptmscore 0.68\n"
        "2026-10-21 10:10:00,000 alphafold2_multimer_v3_model_4_seed_000 took "
        "100.0s (19 recycles) with pLDDT 78.0 and ptmscore 0.67\n"
        "2026-10-21 10:11:40,000 alphafold2_multimer_v3_model_5_seed_000 took "
        "100.0s (19 recycles) with pLDDT 77.5 and ptmscore 0.66\n"
    )
    rows = parse_af2_timing_rows(af2_log)
    c.eq(len(rows["models"]), 5, "five per-model times")
    c.eq(rows["queries"], [("pair1", 912)], "query name and length")
    c.eq(parse_af2_timing_rows("not a log at all")["models"], [],
         "malformed prediction log")
    c.eq(compile_excluded_seconds(1800.0, rows["models"]), 1400.0,
         "the first model's one-off compilation taken off")
    c.eq(compile_excluded_seconds(1800.0, []), None,
         "no per-model times means no compile-excluded figure")

    smi = parse_nvidia_smi("NVIDIA A100-SXM4-40GB, 570.148.08")
    c.eq(smi["gpu_name"], "NVIDIA A100-SXM4-40GB", "graphics processor name")
    c.eq(smi["driver_version"], "570.148.08", "driver version")
    c.ok(is_a100(smi["gpu_name"]), "an A100 is recognised")
    c.ok(not is_a100("NVIDIA L40S"), "an L40S is not an A100")
    c.eq(parse_nvidia_smi("no such line")["gpu_name"], None,
         "malformed processor line")

    pip_report = json.dumps({"install": [{
        "metadata": {"name": "openmm", "version": "8.2.0"},
        "download_info": {
            "url": "https://files.pythonhosted.org/packages/openmm-8.2.0.whl",
            "archive_info": {"hashes": {"sha256": "abc123"}}}}]})
    wheels = parse_pip_report(pip_report)
    c.eq(wheels[0]["url"],
         "https://files.pythonhosted.org/packages/openmm-8.2.0.whl",
         "wheel address from the install report")
    c.eq(wheels[0]["sha256"], "abc123", "wheel hash from the install report")
    c.eq(parse_pip_report("not json"), [], "malformed install report")

    apt = parse_apt_cache_show(
        "Package: aria2\nVersion: 1.36.0-1\nSHA256: deadbeef\n\n"
        "Package: ca-certificates\nVersion: 20230311\nSHA256: cafe1234\n")
    c.eq(len(apt), 2, "two system packages described")
    c.eq(apt[0]["sha256"], "deadbeef", "system package hash")
    c.eq(parse_apt_cache_show("junk"), [], "malformed package description")

    dock_table = ("Rank Swarm Glowworm Scoring\n"
                  "1 0 7 lightdock_7.pdb 12.5\n"
                  "2 0 3 lightdock_3.pdb 11.0\n")
    dock_rows = parse_docking_table(dock_table)
    c.eq(len(dock_rows), 2, "two ranked poses")
    c.eq(top_pose(dock_table), "lightdock_7.pdb", "best-ranked pose file")
    c.eq(parse_docking_table("nonsense here"), [], "malformed ranking table")
    c.eq(top_pose("nonsense here"), None, "no pose from a malformed table")

    contacts = parse_contact_table("# chain res chain res dist\n"
                                   "A 12 B 44 3.8\nA 13 B 45 4.2\n")
    c.eq(len(contacts), 2, "two contacts parsed")
    c.eq(contacts[0]["res_b"], 44, "contact residue number")
    c.eq(parse_contact_table("A 12\n"), [], "malformed contact row")

    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "a.bin").write_bytes(b"x" * 1000)
        (d / "b.bin").write_bytes(b"y" * 24)
        c.eq(apparent_bytes([d / "a.bin", d / "b.bin"]), 1024,
             "files of 1,000 and 24 bytes")
        c.eq(apparent_bytes([d]), 1024, "the same two files as a directory")

    # --- the marginal rule and the band ----------------------------------
    c.ok(is_marginal(1.2, [0.2, 1.25]), "1.2 is within 10 percent of 1.25")
    c.ok(not is_marginal(1.1, [0.2, 1.25]), "1.1 is clear of both edges")
    c.eq(decide_band(float("nan"), [0.2, 1.25])[0], "VOID",
         "a missing number is VOID")

    # --- AlphaFold hours per run -----------------------------------------
    with tempfile.TemporaryDirectory() as d:
        st = _fresh_state(d)
        for hours, want, gate in ((0.5, "PASS", True), (1.5, "FAIL", False),
                                  (0.1, "FAIL", True), (1.2, "VOID", False),
                                  (0.21, "VOID", True), (1.1, "PASS", False),
                                  (0.9, "PASS", True)):
            res = _decide("C1", st, {"runs": _af2_runs(hours)})
            c.eq(res["decision"], want, f"C1 at {hours} h")
            c.eq(round(res["measured"], 6), hours, f"C1 measured {hours} h")
            c.eq(gate_result(res["measured"])["gate_pass"], gate,
                 f"C1 gate at {hours} h")
        c.eq(gate_result(1.1)["gate_else"], GATE_ELSE,
             "the card's fallback text comes with a failed gate")
        res = _decide("C1", st, {"runs": _af2_runs(0.5)[:2]})
        c.eq(res["decision"], "VOID", "C1 with only two completed runs")
        three_runs = [{"pair": "pair1", "seed": 0, "wallclock_s": 1790.0,
                       "incomplete": False},
                      {"pair": "pair1", "seed": 1, "wallclock_s": 1810.0,
                       "incomplete": False},
                      {"pair": "pair2", "seed": 0, "wallclock_s": 1800.0,
                       "incomplete": False}]
        res = _decide("C1", st, {"runs": three_runs})
        c.eq(res["decision"], "VOID", "C1 with three runs missing a pair")
        flat = _af2_runs(0.5)
        for r in flat:
            r["wallclock_s"] = 1800.0
        res = _decide("C1", st, {"runs": flat})
        c.eq(res["decision"], "VOID", "C1 with no spread across seeds")
        c.ok(LABEL_ZERO_SPREAD in res["labels"],
             "the zero-spread label is on the record")
        c.ok(WRONG_VARIANCE_SOURCE in str(res["void_reason"]),
             "the zero-spread halt names the wrong variance source")
        st_other = _fresh_state(d, gpu="NVIDIA L40S")
        res = _decide("C1", st_other, {"runs": _af2_runs(0.5)})
        c.eq(res["decision"], "VOID", "C1 on a processor that is not an A100")
        c.ok(LABEL_NOT_A100 in res["labels"], "the not-an-A100 label on C1")
        c.eq(round(res["measured"], 6), 0.5, "the raw number is kept anyway")

    # --- dynamics speed ---------------------------------------------------
    with tempfile.TemporaryDirectory() as d:
        st = _fresh_state(d)
        res = _decide("C2", st, {"complexes": _md_complexes([100, 129, 500])})
        c.eq(res["measured"], 129, "the middle of 100, 129 and 500")
        c.eq(res["decision"], "PASS", "C2 at 129 ns/day")
        for rate, want in ((40, "FAIL"), (400, "FAIL"), (56, "VOID"),
                           (60, "PASS"), (330, "VOID")):
            res = _decide("C2", st, {"complexes": _md_complexes([rate] * 3)})
            c.eq(res["decision"], want, f"C2 at {rate} ns/day")
        for atoms, want in ((119999, "VOID"), (180001, "VOID"),
                            (150000, "PASS")):
            res = _decide("C2", st,
                          {"complexes": _md_complexes([129] * 3, atoms=atoms)})
            c.eq(res["decision"], want, f"C2 with {atoms} atoms")
        res = _decide("C2", st, {"complexes": _md_complexes([129] * 1)})
        c.eq(res["decision"], "VOID", "C2 with only one complex")
        comps = _md_complexes([129] * 3)
        comps[0]["engine_ns_per_day"] = 200.0
        res = _decide("C2", st, {"complexes": comps})
        c.ok(LABEL_RATE_DISAGREE in res["labels"],
             "the disagreeing-rate label is on the record")
        st_other = _fresh_state(d, gpu="NVIDIA L40S")
        res = _decide("C2", st_other, {"complexes": _md_complexes([129] * 3)})
        c.eq(res["decision"], "VOID", "C2 on a processor that is not an A100")

    # --- auxiliary hours per pair ----------------------------------------
    with tempfile.TemporaryDirectory() as d:
        st = _fresh_state(d)
        res = _decide("C3", st, {"pairs": _aux_pairs([3600.0] * 3)})
        c.eq(res["measured"], 1.0, "three pairs of 3,600 seconds")
        c.eq(res["decision"], "PASS", "C3 at 1 hour per pair")
        for hours, want in ((0.2, "FAIL"), (4.0, "FAIL"), (0.3333, "VOID"),
                            (3.2, "VOID"), (0.5, "PASS"), (2.5, "PASS")):
            res = _decide("C3", st,
                          {"pairs": _aux_pairs([hours * 3600.0] * 3)})
            c.eq(res["decision"], want, f"C3 at {hours} h per pair")
        pairs = _aux_pairs([1800.0] * 3)
        for p in pairs:
            p["install_seconds_not_counted"] = 7200.0
        res = _decide("C3", st, {"pairs": pairs})
        c.eq(res["measured"], 0.5,
             "7,200 s of installing plus 1,800 s of docking is 0.5 h of "
             "auxiliary work")
        res = _decide("C3", st, {"pairs": _aux_pairs([3600.0])})
        c.eq(res["decision"], "VOID", "C3 with only one finished pair")
        truncated = _aux_pairs([3600.0] * 3)
        truncated[2]["truncated"] = True
        res = _decide("C3", st, {"pairs": truncated})
        c.eq(res["decision"], "PASS", "C3 still decided on two finished pairs")
        c.eq(res["n"], 2, "a pair that hit its cap is not counted in the mean")

    # --- storage ----------------------------------------------------------
    with tempfile.TemporaryDirectory() as d:
        st = _fresh_state(d)
        one_gib = 1073741824
        res = _decide("C4", st, {"artifacts": _storage_artifacts(one_gib)})
        c.eq(res["measured"], 216.0, "1 GiB per run over 216 runs")
        c.eq(res["gib_432_runs"], 432.0, "the same at 432 runs")
        c.eq(res["decision"], "PASS", "C4 at 216 GiB")
        for per_run, want_gib, want in ((0.1, 21.6, "FAIL"), (4.0, 864.0, "FAIL"),
                                        (2.9, 626.4, "VOID"), (0.35, 75.6,
                                                               "PASS")):
            res = _decide("C4", st, {"artifacts": _storage_artifacts(
                int(round(per_run * one_gib)))})
            c.eq(round(res["measured"], 4), want_gib,
                 f"C4 at {per_run} GiB per run")
            c.eq(res["decision"], want, f"C4 decision at {per_run} GiB per run")
        res = _decide("C4", st, {"artifacts": _storage_artifacts(one_gib)[:2]})
        c.eq(res["decision"], "VOID", "C4 with no dynamics artifact measured")
        res = _decide("C4", st, {"artifacts": _storage_artifacts(one_gib)})
        c.eq(res["md_bytes_per_ns"],
             _storage_artifacts(one_gib)[2]["bytes"] / MD_PRODUCTION_NS,
             "bytes per simulated nanosecond")

    # --- harness controls -------------------------------------------------
    c.ok(sleep_check(62.9)[0], "a 62.9 s reading of a 60 s wait passes")
    c.ok(not sleep_check(63.1)[0], "a 63.1 s reading of a 60 s wait fails")
    c.eq(spread_check([1800, 1830, 1790])["status"], "OK",
         "timings that differ pass the spread check")
    c.eq(spread_check([1800, 1800, 1800])["status"], WRONG_VARIANCE_SOURCE,
         "identical timings halt as the wrong variance source")
    c.eq(spread_check([40, 100, 160])["label"], LABEL_SPREAD_HIGH,
         "a relative spread of 0.6 is labelled, not halted")
    c.eq(spread_check([40, 100, 160])["status"], "OK",
         "a wide but nonzero spread still passes")
    c.ok(empty_run_check(0.5, 100 * 1024)["clean"],
         "an empty run of 0.5 s and 100 KiB is clean")
    c.eq(empty_run_check(5.0, 100)["label"], LABEL_OVERHEAD_SUBTRACTED,
         "a 5 s empty run is subtracted and labelled")
    c.eq(empty_run_check(0.5, 2 * 1024 * 1024)["label"],
         LABEL_OVERHEAD_SUBTRACTED,
         "a 2 MiB empty run is subtracted and labelled")
    c.eq(empty_run_check(5.0, 100)["overhead_s"], 3.0,
         "the excess seconds are what gets subtracted")

    # --- cost and time ----------------------------------------------------
    c.eq(round(cost_usd(3600, 1.99), 2), 1.99, "one hour at USD 1.99")
    c.eq(round(cost_usd(7200, 1.99), 2), 3.98, "two hours at USD 1.99")
    for price, want_stop, want_cap in ((1.99, 7200.0, "time"),
                                       (2.50, 7200.0, "time"),
                                       (3.00, 6000.0, "cost")):
        caps = compute_caps({"PRICE_USD_PER_HOUR": str(price),
                             "BUDGET_LEFT_USD": "5", "REMOTE_TIMEOUT": "7200"})
        c.eq(round(caps["stop_at_s"], 1), want_stop,
             f"the run stops at {want_stop} s when the price is {price}")
        c.eq(caps["binding_cap"], want_cap, f"which cap binds at {price}")
    caps = compute_caps({"PRICE_USD_PER_HOUR": "1.99", "BUDGET_LEFT_USD": "5",
                         "REMOTE_TIMEOUT": "3600"})
    c.eq(caps["stop_at_s"], 3600.0,
         "a different forwarded timeout changes the arithmetic")
    c.ok(not caps["remote_timeout_defaulted"],
         "a forwarded timeout is not reported as defaulted")
    caps = compute_caps({"PRICE_USD_PER_HOUR": "1.99", "BUDGET_LEFT_USD": "5"})
    c.eq(caps["remote_timeout_s"], 7200.0,
         "an unset timeout falls back to 7,200 s")
    c.ok(caps["remote_timeout_defaulted"],
         "an unset timeout is labelled as defaulted")
    caps = compute_caps({"PRICE_USD_PER_HOUR": "1.99",
                         "BUDGET_LEFT_USD": "500", "REMOTE_TIMEOUT": "99999"})
    c.ok(caps["budget_left_usd"] <= 5 and caps["remote_timeout_s"] <= 7200,
         "an over-large forwarded cap is clamped to the gate's own")

    with tempfile.TemporaryDirectory() as d:
        st = _fresh_state(d)
        st["t0"] = time.time() - 6600          # 600 s left of the 7,200
        try:
            guard_before_stage(st, "af2", estimated_s=900)
            c.ok(False, "a stage that cannot fit must not start")
        except GuardStop as stop:
            c.eq(stop.kind, "time_guard",
                 "a stage that cannot fit is refused by the time guard")
        st["t0"] = time.time()
        c.eq(stage_allowance_s(st, "af2"), 2000.0,
             "a stage early in the run gets its full ceiling")
        st["stage_seconds"] = {"controls": 300.0}
        c.eq(stage_allowance_s(st, "anchor"), 400.0,
             "the anchor gets what the controls left of the shared 700 s")
        c.eq(round(inner_tool_timeout_s(st) - outer_kill_s(st)), -100,
             "the inner stop is 100 s before the outer kill")

    # --- the anchor geometry ---------------------------------------------
    capsid, receptor = _planted_complex()
    reference = _roled(capsid, receptor)
    ref_contacts = residue_contacts(reference)
    c.eq(len(ref_contacts), 6, "the planted complex has six contacts")
    c.eq(contact_overlap(ref_contacts, ref_contacts), 1.0,
         "the published pose reproduces itself")
    half = _roled(capsid, _shift(receptor, dx=50.0, only={4, 5, 6}))
    c.eq(contact_overlap(ref_contacts, residue_contacts(half)), 0.5,
         "three of six contacts is an overlap of 0.5")
    c.ok(contact_overlap(ref_contacts, residue_contacts(half)) != 0.0,
         "a pose with real overlap must not score zero")
    shifted = _roled(capsid, _shift(receptor, dx=5.0))
    c.eq(round(interface_backbone_rmsd(reference, shifted), 4), 5.0,
         "a 5 Angstrom shift gives an interface distance of 5.0")
    outer_only = _roled(capsid, _shift(receptor, dx=20.0, only={7, 8, 9}))
    c.eq(round(interface_backbone_rmsd(reference, outer_only), 4), 0.0,
         "moving only non-interface atoms leaves the interface distance at 0")
    c.ok(whole_chain_rmsd(reference, outer_only) > 0,
         "the whole-chain distance does see that move")
    c.eq(sorted(interface_residues(reference)), [1, 2, 3, 4, 5, 6],
         "the interface is the six contacting residues")

    # The chain letter in the file must not matter: the same pose scores the
    # same whether its receptor is called B, C or A, and it survives being
    # written out and read back in.
    for letter in ("B", "C", "A"):
        moved = _shift(receptor, dx=50.0, only={4, 5, 6})
        renamed = [dict(a, chain=letter) for a in moved]
        round_trip = read_pdb_atoms(write_pdb(renamed))
        pose = _pose_role_atoms(capsid, write_pdb(renamed))
        c.eq(round(contact_overlap(ref_contacts, residue_contacts(pose)), 4), 0.5,
             f"the same pose with receptor chain {letter}")
        c.eq(len(round_trip), len(renamed),
             f"every atom survives the write and read with chain {letter}")
        c.eq(round(round_trip[0]["x"], 3), round(renamed[0]["x"], 3),
             f"coordinates survive the write and read with chain {letter}")

    for overlap, rmsd, want in ((0.50, 9.0, True), (0.49, 5.0, True),
                                (0.49, 5.01, False)):
        got, _why = anchor_decision(overlap, rmsd, 1.0, True, True)
        c.eq(got, want, f"anchor at overlap {overlap} and distance {rmsd}")
    for sp, call_a, call_b, want in ((2.0, True, True, True),
                                     (2.01, True, True, False),
                                     (0.0, True, False, False)):
        got, _why = anchor_decision(0.9, 1.0, sp, call_a, call_b)
        c.eq(got, want,
             f"serial against parallel at {sp} Angstrom, calls {call_a}/{call_b}")
    c.ok(bind_call(reference), "the planted complex is called touching")
    c.ok(not bind_call(_roled(capsid, _shift(receptor, dx=500.0))),
         "a receptor 500 Angstrom away is called not touching")

    # --- the environment handed to a child -------------------------------
    planted = {"PATH": os.environ.get("PATH", ""), "HF_TOKEN": "secret-one",
               "HUGGING_FACE_HUB_TOKEN": "secret-two", "INSTANCE_TYPE": "box"}
    child = child_env(planted)
    c.ok("HF_TOKEN" not in child and "HUGGING_FACE_HUB_TOKEN" not in child,
         "a child gets no download token")
    c.ok(child.get("INSTANCE_TYPE") == "box",
         "a child keeps the non-secret variables")

    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        st = _fresh_state(d)
        saved = dict(os.environ)
        os.environ["HF_TOKEN"] = "secret-one"
        os.environ["HUGGING_FACE_HUB_TOKEN"] = "secret-two"
        try:
            res = run_tool(
                [sys.executable, "-c",
                 "import os,sys; sys.stdout.write(','.join(sorted(os.environ)))"],
                timeout_s=30, log_path=d / "env_child.log", state=st,
                label="child environment")
            text = (d / "env_child.log").read_text(errors="replace")
            c.ok(res.ok, "the planted child ran")
            c.ok("HF_TOKEN" not in text and "HUGGING_FACE_HUB_TOKEN" not in text,
                 "the real child environment carries no download token")
        finally:
            os.environ.clear()
            os.environ.update(saved)

    # --- a tool that runs past its allowance, and its own child ----------
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        st = _fresh_state(d)
        marker = d / "child_ran_on.txt"
        code = (
            "import subprocess,sys,time\n"
            "subprocess.Popen([sys.executable,'-c',"
            "\"import sys,time; time.sleep(5); open(sys.argv[1],'w').write('x')\","
            f"{str(marker)!r}])\n"
            "time.sleep(30)\n"
        )
        res = run_tool([sys.executable, "-c", code], timeout_s=1.0,
                       log_path=d / "slow.log", state=st, label="a slow tool")
        c.ok(res["timed_out"], "a tool past its allowance is stopped")
        c.ok(res["pgid"] in st["process_groups"],
             "the stopped tool's process group is recorded")
        time.sleep(7)
        c.ok(not marker.exists(),
             "the stopped tool's own child is stopped with it")
        try:
            _require(res, "af2", "the slow tool")
            c.ok(False, "a stopped tool must become a ceiling stop")
        except GuardStop as stop:
            c.eq(stop.kind, "tool_timeout",
                 "a stopped tool becomes a ceiling stop, not a failure")
        except FailStop:
            c.ok(False, "a stopped tool must not be read as broken "
                        "infrastructure")

    # --- the stage flow, with stand-in stages ----------------------------
    flow = _selftest_stage_flow(c)
    c.total += flow.total
    c.passed += flow.passed
    c.failures.extend(flow.failures)

    for failure in c.failures:
        print(f"selftest: FAILED {failure}")
    print(f"selftest: {c.passed} of {c.total} checks passed")
    print("selftest: files sha256 run_m4.py "
          f"{sha256_file(Path(__file__).resolve())} onbox_{TAG}.sh "
          f"{_onbox_hash()}")
    print("selftest: " + ("PASS" if c.passed == c.total else "FAIL"))
    return 0 if c.passed == c.total else 1


def _onbox_hash():
    p = HERE / f"onbox_{TAG}.sh"
    return sha256_file(p) if p.exists() else "missing"


def _selftest_stage_flow(_outer):  # noqa: C901 - one case per planted route
    """Run the whole flow with stand-in stages, once per route through it.

    The point is the route, not the arithmetic: which exit code comes out, what
    happens to the validity flag, which inputs keep a decision and which go VOID
    with the incomplete-run label.
    """
    import tempfile

    c = Checks()
    one_gib = 1073741824

    def good(key, payload):
        def fn(state, tools):
            state.setdefault("measurements", {}).setdefault(key, {}).update(
                payload())
            save_state(state)
        return fn

    def noop(state, tools):
        return None

    def planted_stages(**overrides):
        base = {
            "install": noop,
            "controls": noop,
            "anchor": noop,
            "aux": good("C3", lambda: {"pairs": _aux_pairs([3600.0] * 3)}),
            "af2": good("C1", lambda: {"runs": _af2_runs(0.5)}),
            "md": good("C2", lambda: {"complexes": _md_complexes([129] * 3)}),
            "storage": good("C4",
                            lambda: {"artifacts": _storage_artifacts(one_gib)}),
        }
        base.update(overrides)
        return [(name, base[name]) for name, _ in ONBOX_STAGES]

    def fake_tool(*a, **k):
        return ToolResult({"returncode": 0, "timed_out": False, "seconds": 0.0})

    def run_case(name, stages, tmp):
        state = _fresh_state(tmp)
        state["out_dir"] = str(tmp)
        save_state(state)
        code, results = run_stages(state, stages, fake_tool, stage_endpoints)
        return state, code, results

    def record_text(tmp, key):
        return (Path(tmp) / f"endpoint-{key}_tag-{TAG}.json").read_text()

    # (a) every stage finishes
    with tempfile.TemporaryDirectory() as t:
        st, code, res = run_case("all finish", planted_stages(), Path(t))
        c.eq(code, 0, "every stage finishing gives exit 0")
        c.ok(st["run_valid"], "every stage finishing leaves the run valid")
        for key in ALL_INPUTS:
            c.ok(res[key]["decision"] in ("PASS", "FAIL"),
                 f"{key} is decided when every stage finishes")
            c.ok(LABEL_INCOMPLETE not in record_text(t, key),
                 f"{key} carries no incomplete-run label on a complete run")
        c.ok(json.loads(record_text(t, "C1"))["run_valid"] is True,
             "the validity flag is in the per-input file, not only the summary")
        summary = json.loads(
            (Path(t) / f"{TAG}_summary.json").read_text())
        c.ok("stand-in" in summary["what_this_run_decides"],
             "the summary says first that this is the stand-in protocol only")
        c.ok("replication" not in summary["what_this_run_decides"].replace(
             "not a replication", ""),
             "the summary never calls a same-box repeat a replication")
        c.eq(summary["records"]["C1"]["measured"], 0.5,
             "the summary restates the measured value")
        c.ok((Path(t) / f"control-unit-and-scale_tag-{TAG}.json").exists(),
             "the unit-and-scale record is written")

    # (b) the time guard stops the predictions after two of nine runs
    def guard_af2(state, tools):
        state.setdefault("measurements", {})["C1"] = {
            "runs": _af2_runs(0.5)[:2]}
        append_row(state, "C1", {"pair": "pair1", "seed": 0,
                                 "wallclock_s": 1790.0})
        save_state(state)
        raise GuardStop("af2", "time_guard",
                        "the next run does not fit in the time left")

    with tempfile.TemporaryDirectory() as t:
        st, code, res = run_case("guard in af2",
                                 planted_stages(af2=guard_af2), Path(t))
        c.eq(code, 3, "a time-guard stop gives exit 3")
        c.ok(st["run_valid"], "a time-guard stop leaves the run valid")
        c.eq(res["C1"]["decision"], "VOID", "C1 is VOID after the guard stop")
        c.ok(LABEL_UNMEASURED in record_text(t, "C1"),
             "the C1 record says unmeasured, not holding")
        c.ok(LABEL_INCOMPLETE in record_text(t, "C1"),
             "the C1 record carries the incomplete-run label")
        c.ok((Path(t) / f"rows_C1_tag-{TAG}.jsonl").exists(),
             "the raw rows of the stopped stage are kept")
        for key in ("C2", "C3", "C4"):
            c.ok(res[key]["decision"] in ("PASS", "FAIL"),
                 f"{key} is still decided after the guard stop")
            c.ok(LABEL_INCOMPLETE in record_text(t, key),
                 f"{key} still carries the incomplete-run label")
        c.ok(LABEL_INCOMPLETE in (Path(t) / f"{TAG}_summary.json").read_text(),
             "the summary carries the incomplete-run label")

    # (c) a tool stops on the third complex; two are enough to decide
    def timeout_md(state, tools):
        comps = _md_complexes([129] * 2)
        comps.append({"complex": "complex3", "atoms": 150000, "steps": 250000,
                      "wallclock_ns_per_day": None, "engine_ns_per_day": None,
                      "incomplete": True})
        state.setdefault("measurements", {})["C2"] = {"complexes": comps}
        save_state(state)
        raise GuardStop("md", "tool_timeout",
                        "complex3 ran past its allowance")

    with tempfile.TemporaryDirectory() as t:
        st, code, res = run_case("timeout in md",
                                 planted_stages(md=timeout_md), Path(t))
        c.eq(code, 3, "a tool stop gives exit 3")
        c.ok(st["run_valid"], "a tool stop leaves the run valid")
        c.eq(res["C2"]["decision"], "PASS", "C2 is still decided")
        c.eq(res["C2"]["n"], 2, "C2 is decided on the two complexes that ran")
        for key in ("C1", "C3", "C4"):
            c.ok(res[key]["decision"] in ("PASS", "FAIL"),
                 f"{key} is untouched by the stop in the dynamics stage")

    # (d) the docking stage hits its ceiling
    def ceiling_aux_two(state, tools):
        state.setdefault("measurements", {})["C3"] = {
            "pairs": _aux_pairs([3600.0] * 2)}
        save_state(state)
        raise GuardStop("aux", "stage_ceiling", "the docking stage ran out")

    def ceiling_aux_one(state, tools):
        state.setdefault("measurements", {})["C3"] = {
            "pairs": _aux_pairs([3600.0])}
        save_state(state)
        raise GuardStop("aux", "stage_ceiling", "the docking stage ran out")

    with tempfile.TemporaryDirectory() as t:
        st, code, res = run_case("ceiling in docking",
                                 planted_stages(aux=ceiling_aux_two), Path(t))
        c.eq(code, 3, "a ceiling stop gives exit 3")
        c.eq(res["C3"]["decision"], "PASS", "C3 is decided on two finished pairs")
    with tempfile.TemporaryDirectory() as t:
        st, code, res = run_case("ceiling in docking, one pair",
                                 planted_stages(aux=ceiling_aux_one), Path(t))
        c.eq(res["C3"]["decision"], "VOID", "C3 is VOID below two pairs")
        c.ok(LABEL_UNMEASURED in record_text(t, "C3"),
             "the C3 record says unmeasured, not holding")

    # (e) a tool really fails
    def failing_af2(state, tools):
        raise FailStop("af2", "the prediction tool exited 1", 2)

    with tempfile.TemporaryDirectory() as t:
        st, code, res = run_case("tool failure",
                                 planted_stages(af2=failing_af2), Path(t))
        c.eq(code, 2, "a real tool failure gives exit 2")
        c.ok(not st["run_valid"], "a real tool failure makes the run invalid")
        for key in ALL_INPUTS:
            c.eq(res[key]["decision"], "VOID",
                 f"{key} is VOID after a tool failure")
            c.ok(json.loads(record_text(t, key))["run_valid"] is False,
                 f"the invalid flag is written into the {key} file itself")

    # (f) the anchor misses
    def missed_anchor(state, tools):
        raise FailStop("anchor", "the re-docking missed", 4)

    with tempfile.TemporaryDirectory() as t:
        st, code, res = run_case("anchor miss",
                                 planted_stages(anchor=missed_anchor), Path(t))
        c.eq(code, 4, "a missed anchor gives exit 4")
        c.ok(not st["run_valid"], "a missed anchor makes the run invalid")
        for key in ALL_INPUTS:
            c.eq(res[key]["decision"], "VOID",
                 f"{key} is VOID after a missed anchor")
            c.ok(json.loads(record_text(t, key))["run_valid"] is False,
                 f"the missed anchor voids the {key} file")
        c.ok(json.loads((Path(t) / "RUN_VALID.json").read_text())["run_valid"]
             is False, "the validity file says the run is invalid")

    # (g) the timer check fails
    def failing_sleep(state, tools):
        raise FailStop("controls", "the timer check was off by 5.2 percent", 2)

    with tempfile.TemporaryDirectory() as t:
        st, code, res = run_case("timer failure",
                                 planted_stages(controls=failing_sleep), Path(t))
        c.eq(code, 2, "a failed timer check gives exit 2")
        c.ok(not st["run_valid"], "a failed timer check makes the run invalid")

    # (h) the install, the smoke check and a download each fail
    for what, detail in (("install", "the declared packages did not install"),
                         ("smoke check", "a tool did not start"),
                         ("download", "the structure file did not arrive")):
        def failing_install(state, tools, _detail=detail):
            raise FailStop("install", _detail, 2)

        with tempfile.TemporaryDirectory() as t:
            st, code, res = run_case(what,
                                     planted_stages(install=failing_install),
                                     Path(t))
            c.eq(code, 2, f"a failure of the {what} gives exit 2")
            c.ok(not st["run_valid"], f"a failure of the {what} voids the run")
            c.eq(res["C1"]["decision"], "VOID",
                 f"C1 is VOID after a failure of the {what}")

    # (i) the outer timeout fired and only the decisions are left to write
    with tempfile.TemporaryDirectory() as t:
        state = _fresh_state(Path(t))
        state["out_dir"] = str(t)
        state["measurements"] = {
            "C1": {"runs": _af2_runs(0.5)},
            "C2": {"complexes": _md_complexes([129] * 3)},
            "C3": {"pairs": _aux_pairs([3600.0] * 3)},
            "C4": {"artifacts": _storage_artifacts(one_gib)},
        }
        save_state(state)
        record_stop(state, "outer_timeout", "outer_timeout",
                    "the outer timeout fired (return code 124)")
        code, res = run_stages(state, [], fake_tool, stage_endpoints)
        c.eq(code, 3, "the outer-timeout route gives exit 3")
        c.ok(state["run_valid"], "the outer-timeout route leaves the run valid")
        c.ok(LABEL_INCOMPLETE in record_text(t, "C2"),
             "records written after the outer timeout carry the full label")

    # (j) nothing was measured at all
    with tempfile.TemporaryDirectory() as t:
        state = _fresh_state(Path(t))
        state["out_dir"] = str(t)
        save_state(state)
        code, res = run_stages(state, [], fake_tool, stage_endpoints)
        c.eq(code, 3, "nothing measured gives exit 3, never 0")
        for key in ALL_INPUTS:
            c.eq(res[key]["decision"], "VOID",
                 f"{key} is VOID when nothing was measured")

    # (k) a part of the run on its own: installing and checking the harness is
    #     not a verdict on any input, so it does not report inputs missing
    with tempfile.TemporaryDirectory() as t:
        state = _fresh_state(Path(t))
        state["out_dir"] = str(t)
        save_state(state)
        code, _res = run_stages(state, [("install", noop), ("controls", noop)],
                                fake_tool, lambda s, tl: {},
                                settle_inputs=False)
        c.eq(code, 0, "installing and checking the harness alone gives exit 0")

    # (l) a value too close to a band edge is still a decision on a measurement
    with tempfile.TemporaryDirectory() as t:
        st, code, res = run_case(
            "marginal C1",
            planted_stages(af2=good("C1", lambda: {"runs": _af2_runs(1.2)})),
            Path(t))
        c.eq(res["C1"]["decision"], "VOID", "C1 at 1.2 h is VOID as marginal")
        c.ok(res["C1"]["marginal"], "C1 at 1.2 h is marked marginal")
        c.eq(code, 0, "a marginal VOID is a measured decision, so exit stays 0")

    return c


if __name__ == "__main__":
    sys.exit(main())
