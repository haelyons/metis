#!/usr/bin/env python3
"""Measure four cost inputs of one research card on one rented GPU box.

The four numbers, with the card's own value and band:

  C1  hours of wall-clock per AlphaFold-Multimer prediction run   0.5   [0.2, 1.25]
  C2  molecular-dynamics speed, nanoseconds simulated per day     129   [51.6, 322.5]
  C3  auxiliary hours per capsid-receptor pair                    1     [0.3333, 3]
  C4  storage in gibibytes for the planned grid of 216 runs       200   [66.67, 600]

Before any of the four is measured the program must reproduce a published
result: redocking the receptor domain AAVR-PKD2 onto the capsid AAV2 must land
beside the same spike as Protein Data Bank entry 6IHB. That check is called the
anchor. A missed anchor does not stop the measuring: the four inputs are still
measured, every record written after the miss says the run is void, and the run
exits 4 at the end unless a worse row of the exit table applies.

It does not run the card's planned study. It measures a stand-in protocol built
from chains of one structure, on one graphics processor, and says so in every
file it writes. Two runs on the same box are two samples of one box; this
program never calls that replication.

Usage:

  python3 run_m4.py --run                    # the whole run, on the rented box
  python3 run_m4.py --stage NAME --in DIR --out DIR    # exactly one stage
  python3 run_m4.py --selftest               # stdlib-only checks, no GPU

Importing this file does no work. Every parser takes a path and returns a dict,
raising ParseError (a ValueError) on malformed input. Decision words used in
records: PASS (inside the band), FAIL (outside it), VOID (not decidable).

Exit codes: 0 finished; 2 broken infrastructure or a broken harness; 3 a guard,
a stage ceiling or a timeout stopped the run short; 4 the anchor was compared
and missed its tolerance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shlex
import shutil
import signal
import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path

TAG = "m4"

# ---------------------------------------------------------------------------
# The card's own numbers, copied from the design record.
# ---------------------------------------------------------------------------

CARD = {
    "C1": {"key": "af2_h_per_run",
           "unit": "hours per AlphaFold-Multimer run",
           "card_value": 0.5, "band": [0.2, 1.25], "basis": "PROXY"},
    "C2": {"key": "md_ns_per_day_a100",
           "unit": "nanoseconds simulated per day",
           "card_value": 129, "band": [51.6, 322.5], "basis": "PROXY"},
    "C3": {"key": "aux_h_per_pair",
           "unit": "hours per capsid-receptor pair",
           "card_value": 1, "band": [0.3333, 3], "basis": "GUESS"},
    "C4": {"key": "n_storage_gib",
           "unit": "gibibytes",
           "card_value": 200, "band": [66.67, 600], "basis": "GUESS"},
}

INPUT_IDS = ["C1", "C2", "C3", "C4"]

GATE_VALUE = 1
GATE_EXPRESSION = "af2_h_per_run <= 1"
GATE_ELSE = (
    "take the docking-plus-MD fallback line with one AlphaFold-Multimer seed "
    "per pair, or move the grid to 12 pairs"
)
GATE_NOT_APPLICABLE = "not applicable: the card's gate is on af2_h_per_run"

ANCHOR_OVERLAP_MIN = 0.50
ANCHOR_IFACE_RMSD_MAX = 5.0
ANCHOR_SERIAL_PARALLEL_RMSD_MAX = 2.0
CONTACT_CUTOFF_A = 4.5

FRAME_RESIDUAL_MAX_A = 0.1
FRAME_MATCH_FRACTION_MIN = 0.99

MARGINAL_FRACTION = 0.10

SLEEP_CONTROL_S = 60.0
SLEEP_CONTROL_TOLERANCE = 0.05
EMPTY_RUN_MAX_S = 2.0
EMPTY_RUN_MAX_BYTES = 1024 * 1024
SEED_SPREAD_HIGH_RSD = 0.50

GRID_RUNS = 216
GRID_RUNS_ALT = 432
BYTES_PER_GIB = 2 ** 30

N_PAIRS = 3
AF2_SEEDS = [0, 1, 2]
AF2_MODELS = 5
AF2_RECYCLES = 20
MD_VELOCITY_SEED = 0
MD_PRODUCTION_NS = 0.5
MD_TIMESTEP_FS = 2.0
MD_REPORT_INTERVAL_STEPS = 5000
MD_FRAME_INTERVAL_PS = MD_REPORT_INTERVAL_STEPS * MD_TIMESTEP_FS / 1000.0
MD_PRODUCTION_STEPS = int(round(MD_PRODUCTION_NS * 1e6 / MD_TIMESTEP_FS))
MD_EQUIL_STEPS = 2000
MD_ATOMS_MIN = 120000
MD_ATOMS_MAX = 180000
PAIR_RESIDUES_MIN = 750
PAIR_RESIDUES_MAX = 1000
PAIR_LENGTH_SPREAD_MIN = 20
PAIR_TARGET_LENGTHS = [780, 870, 960]
PAIR_FASTA_MIN = 750
PAIR_FASTA_MAX = 1000

MIN_AF2_RUNS = 3
MIN_MD_COMPLEXES = 2
MIN_AUX_PAIRS = 2

TOTAL_CEILING_S = 7200
FETCH_MARGIN_S = 400
ENDPOINTS_SLOT_S = 100

STAGE_ORDER = [
    "capability", "downloads", "controls", "anchor",
    "aux", "af2", "md", "storage", "endpoints",
]

STAGE_CEILING_S = {
    "capability": 1500,
    "downloads": 1500,
    "controls": 1000,
    "anchor": 1000,
    "aux": 600,
    "af2": 2000,
    "md": 1600,
    "storage": 100,
    "endpoints": ENDPOINTS_SLOT_S,
}
STAGE_GROUPS = {
    "setup": (1500.0, ("capability", "downloads")),
    "controls_anchor": (1000.0, ("controls", "anchor")),
}
PER_PAIR_DOCKING_CEILING_S = 250
PER_COMPLEX_MD_CEILING_S = 600

UNIT_FLOOR_S = {
    "anchor_serial": 60,
    "anchor_parallel": 60,
    "docking_pair": 60,
    "af2_run": 120,
    "md_complex": 150,
    "storage": 20,
    "endpoints": 30,
}

DEFAULT_REMOTE_TIMEOUT_S = 7200
DEFAULT_BUDGET_LEFT_USD = 5.0
DEFAULT_PRICE_USD_PER_HOUR = 1.99
BOOTSTRAP_ASSUMED_S = 300

OUTER_KILL_SLACK_S = 600
INNER_KILL_SLACK_S = 700

# ---------------------------------------------------------------------------
# Fixed label strings, in one place.
# ---------------------------------------------------------------------------

LABEL_UNMEASURED = "unmeasured, not holding"
LABEL_INCOMPLETE = "incomplete run: unmeasured inputs are VOID, not holding"
LABEL_STAND_IN = "stand-in pairs built from 6IHB chains, not the card's pairs"
LABEL_ONE_GPU = "one GPU; one box; 3 pairs; no multi-GPU scaling"
LABEL_NO_MSA = "no-MSA: alignment search time excluded; understates the card's setting"
LABEL_AUX_READING = "producer's reading of aux hours"
LABEL_STORAGE = "linear in runs; intermediates kept; MD length 0.5 ns"
LABEL_NOT_A100 = "not an A100"
LABEL_ZERO_SPREAD = "zero spread across seeds: wrong variance source"
LABEL_SPREAD_HIGH = "seed spread high; mean is uncertain"
LABEL_OVERHEAD_SUBTRACTED = "setup overhead subtracted"
LABEL_RATE_DISAGREE = "engine rate and wall-clock disagree"
LABEL_RATE_MISSING = "engine rate line missing"
LABEL_SERIAL_PARALLEL_WHOLE_CHAIN = (
    "serial-versus-parallel RMSD is over the whole receptor chain, not the interface"
)
LABEL_BOOTSTRAP_ASSUMED = "bootstrap time assumed 300 s"
LABEL_FIXER_CHANGED_ENV = "environment changed by the fixer on the box; lock %s"
LABEL_TIMEOUT_NOT_FORWARDED = "REMOTE_TIMEOUT not forwarded; default 7200 used"
LABEL_AFTER_ANCHOR_MISS = (
    "measured after an anchor miss; run_valid false, voided by the anchor; "
    "calibration_valid decided by this record's own checks only"
)
LABEL_ANCHOR_UNDECIDED = "anchor undecided"
LABEL_DIAGNOSTICS = "diagnostics do not change the verdict"
LABEL_ANCHOR_NOT_REACHED = "anchor stage not reached"
WRONG_VARIANCE_SOURCE = "WRONG_VARIANCE_SOURCE"
ANCHOR_INDEPENDENT_CODE = "not run: single docking code"

WHAT_THIS_RUN_DECIDES = (
    "This run decides the stand-in protocol only: four cost inputs measured once "
    "on one rented single-GPU box, on pairs built from chains of PDB entry 6IHB, "
    "not on the card's own pairs and not on the card's 8-GPU setting. It does not "
    "run the card's 54-run pilot or its 216-run grid, and it does not evaluate the "
    "card's own prediction. Two runs on the same box are two samples of one box, "
    "never a replication."
)

SECRET_ENV_KEYS = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")

ENV_RECORD_KEYS = (
    "INSTANCE_TYPE", "LAMBDA_INSTANCE_ID", "GIT_COMMIT",
    "PRICE_USD_PER_HOUR", "BUDGET_LEFT_USD", "REMOTE_TIMEOUT",
    "M4_T0_EPOCH", "M4_PRE_T0_SECONDS", "M4_BOOTSTRAP_ASSUMED",
    "M4_SETUP_SECONDS", "ENV_DIR", "ENV_LOCK_SHA256", "HOLD_SECONDS",
    "M4_VENV", "PATH", "TMPDIR", "PIP_CACHE_DIR", "XDG_CACHE_HOME",
    "MPLCONFIGDIR",
)

MACHINE_KEYS = (
    "instance_type", "gpu_name", "gpu_driver", "cuda_runtime_version",
    "cuda_plugin_version", "start_utc", "end_utc", "price_usd_per_hour",
    "expected_lock_sha256", "observed_lock_sha256", "venv_path",
    "environment_changed_by_fixer", "held_attempts",
)

ENGINE_KEYS = (
    "alphafold_implementation", "alphafold_params_sha256", "jax_version",
    "jaxlib_version", "jax_cuda_plugin_version", "jax_wheel_build_tags",
    "docking_code", "docking_version", "md_engine", "md_engine_version",
    "md_precision", "md_platform", "build_flags",
)

CONTROL_KINDS = ("control_sleep", "control_empty_run", "control_unit_and_scale")
MEASURED_KINDS = ("anchor", "C1", "C2", "C3", "C4")
SETUP_KINDS = ("env_check",)

REQUIRED_LABEL_KEYS = {
    kind: {"machine": MACHINE_KEYS, "engine": ENGINE_KEYS} for kind in MEASURED_KINDS
}
REQUIRED_LABEL_KEYS.update(
    {kind: {"machine": MACHINE_KEYS, "engine": ()}
     for kind in CONTROL_KINDS + SETUP_KINDS}
)


def label_problems(kind: str, values: dict) -> list:
    """What a record's labels are missing: absent keys, or nulls with no reason."""
    spec = REQUIRED_LABEL_KEYS.get(kind)
    if spec is None:
        return [f"no label keys are declared for a record of kind {kind}"]
    problems = []
    reasons = values.get("null_reasons") or {}
    for group, keys in spec.items():
        if not keys:
            continue
        block = values.get(group)
        if not isinstance(block, dict):
            problems.append(f"{kind}: values.{group} is missing")
            continue
        for key in keys:
            if key not in block:
                problems.append(f"{kind}: values.{group} does not carry {key}")
            elif block[key] is None and not str(reasons.get(key) or "").strip():
                problems.append(f"{kind}: {key} is null with no reason given")
    return problems


PDB_ENTRY = "6IHB"
PDB_URL = "https://files.rcsb.org/download/6IHB.pdb"
AF_PARAMS_URL = (
    "https://storage.googleapis.com/alphafold/alphafold_params_2022-12-06.tar"
)
ALLOWED_DOWNLOAD_HOSTS = ("files.rcsb.org", "storage.googleapis.com")

DOCKING_CODE = "lightdock"
DOCKING_SWARMS = 2
DOCKING_GLOWWORMS = 20
DOCKING_STEPS = 20
DOCKING_SETUP_FLAGS = ["--noxt", "--noh"]

DOCKING_ORDER = [
    "lightdock3_setup.py (prepare)",
    "lightdock3.py (simulate)",
    "lgd_generate_conformations.py (generate the pose structures)",
    "lgd_rank.py (rank)",
]

MD_ENGINE = "OpenMM"
MD_PRECISION = "mixed"
MD_PLATFORM = "CUDA"
AF2_IMPLEMENTATION = "ColabFold (colabfold_batch) running AlphaFold-Multimer"

TOOL_ENV_VARS = {
    "colabfold_batch": "M4_COLABFOLD",
    "lightdock3_setup.py": "M4_LIGHTDOCK_SETUP",
    "lightdock3.py": "M4_LIGHTDOCK",
    "lgd_generate_conformations.py": "M4_LGD_GENERATE",
    "lgd_rank.py": "M4_LGD_RANK",
    "md_worker": "M4_MD_WORKER",
    "nvidia-smi": "M4_NVIDIA_SMI",
    "fetch": "M4_FETCH",
    "sleep": "M4_SLEEP",
    "python": "M4_PYTHON",
}


# ---------------------------------------------------------------------------
# Failure kinds. Which one is raised decides the exit code.
# ---------------------------------------------------------------------------


class ParseError(ValueError):
    """A tool's output could not be read in the shape this program assumes.

    It is a ValueError on purpose: the stage interface says every parser raises
    ValueError on malformed input.
    """


class HarnessFailure(Exception):
    """Broken infrastructure or a broken harness. Exit code 2."""

    def __init__(self, reason: str, detail: str = "", kind: str = ""):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail
        self.kind = kind or re.sub(r"[^a-z0-9]+", "_", reason.lower()).strip("_")[:40]


class GuardStop(Exception):
    """A guard, a stage ceiling or a timeout stopped work. Exit code 3."""

    def __init__(self, reason: str, stage: str = "", detail: str = ""):
        super().__init__(reason)
        self.reason = reason
        self.stage = stage
        self.detail = detail


class FrameGuardReject(Exception):
    """The pose's capsid does not sit where the shift says it should. Exit 2."""

    def __init__(self, reason: str, frame: dict):
        super().__init__(reason)
        self.reason = reason
        self.frame = frame


EXIT_OK = 0
EXIT_INFRA = 2
EXIT_GUARD = 3
EXIT_ANCHOR = 4


# ---------------------------------------------------------------------------
# Small shared helpers.
# ---------------------------------------------------------------------------


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def utc_of(epoch: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(epoch))


def atomic_write_text(path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text)
    os.replace(str(tmp), str(path))


def atomic_write_json(path, obj, sort_keys: bool = True) -> None:
    atomic_write_text(path, json.dumps(obj, indent=2, sort_keys=sort_keys) + "\n")


def append_jsonl(path, row: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def apparent_bytes(path) -> int:
    """Sum of the apparent sizes of every regular file under a path."""
    p = Path(path)
    if not p.exists():
        return 0
    if p.is_file():
        return p.stat().st_size
    total = 0
    for root, _dirs, files in os.walk(str(p)):
        for name in files:
            fp = Path(root) / name
            try:
                if fp.is_symlink():
                    continue
                total += fp.stat().st_size
            except OSError:
                continue
    return total


# ===========================================================================
# PARSERS. Each takes a path and returns a dict.
# ===========================================================================


def _read_text(path) -> str:
    try:
        return Path(path).read_text()
    except OSError as exc:
        raise ParseError(f"cannot read {path}: {exc}")


def parse_nvidia_smi_header(path) -> dict:
    """Read the driver version and the driver's CUDA version from the banner.

    Both fields must be present: a banner without them is malformed input.
    """
    text = _read_text(path)
    driver = None
    cuda = None
    m = re.search(r"Driver Version:\s*([0-9][0-9.]*)", text)
    if m:
        driver = m.group(1)
    m = re.search(r"CUDA Version:\s*([0-9][0-9.]*)", text)
    if m:
        cuda = m.group(1)
    if driver is None or cuda is None:
        raise ParseError(
            "nvidia-smi banner is malformed: it must carry both "
            f"Driver Version and CUDA Version; got driver={driver!r} "
            f"cuda={cuda!r}; {first_raw_lines(text, 3)}")
    return {"driver_version": driver, "cuda_version_header": cuda}


def parse_nvidia_smi_query(path) -> dict:
    """Read one comma-separated line of `--query-gpu=name,driver_version`.

    Both fields must be present on the line: anything else is malformed.
    """
    text = _read_text(path)
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2 and parts[0] and parts[1]:
            return {"gpu_name": parts[0], "driver_version": parts[1]}
        raise ParseError(
            "nvidia-smi query line is malformed: it must carry a name and a "
            f"driver version separated by a comma; got {line!r}")
    raise ParseError("nvidia-smi query output holds no line")


def parse_etimes(path) -> dict:
    """Read `ps -o etimes=`: whole seconds since a process started."""
    text = _read_text(path).strip()
    if not re.fullmatch(r"[0-9]+", text or ""):
        raise ParseError(f"etimes output is not one bare integer: {repr(text[:80])}")
    return {"seconds": int(text)}


def is_a100(gpu_name) -> bool:
    if not gpu_name:
        return False
    return "a100" in str(gpu_name).lower()


ERROR_SIGNATURE = re.compile(
    r"(traceback \(most recent call last\)|\berror\b|\bexception\b|\bfatal\b"
    r"|\bfail(?:ed|ure|s)?\b|out of memory)", re.IGNORECASE)


def parse_colabfold_log_text(text: str) -> dict:
    """Per-model seconds and any download seen in one prediction run log.

    A line that names `took` must carry a complete `took <number> s` timing
    and a name in front of it: a line with a field missing is malformed. A log
    that reports an error instead of timings is malformed input too: this
    parser never answers with a default for one.
    """
    if ERROR_SIGNATURE.search(text or ""):
        raise ParseError(
            "colabfold log is malformed: it reports an error instead of "
            "timings; " + first_raw_lines(text, 5))
    per_model = []
    for index, line in enumerate(text.splitlines(), start=1):
        if re.search(r"\btook\b", line):
            if re.match(r"^\s*took\b", line):
                raise ParseError(
                    "colabfold log line %d is malformed: the model name field "
                    f"is missing; got {line!r}" % index)
            m = re.search(r"\btook\s+([0-9]+(?:\.[0-9]+)?)\s*s", line)
            if m is None:
                raise ParseError(
                    "colabfold log line %d is malformed: the timing field "
                    f"is missing or incomplete; got {line!r}" % index)
            per_model.append(float(m.group(1)))
    downloaded = bool(
        re.search(
            r"(downloading|download complete|extracting|untarring|fetching params)",
            text, re.IGNORECASE))
    return {"per_model_s": per_model, "download_in_timed_call": downloaded}


def parse_colabfold_log(path) -> dict:
    """Read a prediction run log: per-model seconds, and any download inside it."""
    return parse_colabfold_log_text(_read_text(path))


def parse_reporter_file_text(text: str) -> dict:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return {"ns_per_day": None, "n_rows": 0, "reason": "reporter file is empty",
                "energies_finite": None, "last_step": None}
    header = lines[0].lstrip("#").strip()
    cols = [c.strip().strip('"').strip("'") for c in header.split(",")]
    speed_idx = step_idx = energy_idx = None
    for i, name in enumerate(cols):
        low = name.lower()
        if speed_idx is None and "speed" in low:
            speed_idx = i
        if step_idx is None and low.startswith("step"):
            step_idx = i
        if energy_idx is None and "energy" in low:
            energy_idx = i
    if speed_idx is None:
        return {"ns_per_day": None, "n_rows": max(0, len(lines) - 1),
                "reason": "no speed column in the reporter header",
                "energies_finite": None, "last_step": None}
    rate = None
    n_rows = 0
    last_step = None
    energies_finite = True
    width = len(cols)
    for ln in lines[1:]:
        parts = [p.strip().strip('"') for p in ln.split(",")]
        if len(parts) != width:
            raise ParseError(
                "reporter file is malformed: a data row holds %d fields "
                "against %d in the header; row %r"
                % (len(parts), width, ln[:120]))
        n_rows += 1
        if step_idx is not None and len(parts) > step_idx:
            try:
                last_step = int(float(parts[step_idx]))
            except ValueError:
                last_step = None
        if energy_idx is not None and len(parts) > energy_idx:
            try:
                ev = float(parts[energy_idx])
                if not math.isfinite(ev):
                    energies_finite = False
            except ValueError:
                energies_finite = False
        try:
            value = float(parts[speed_idx])
        except ValueError:
            continue
        if value > 0:
            rate = value
    reason = None if rate is not None else "no positive speed value in any row"
    return {"ns_per_day": rate, "n_rows": n_rows, "reason": reason,
            "energies_finite": energies_finite, "last_step": last_step}


def parse_reporter_file(path) -> dict:
    """Read a dynamics state reporter file and take its speed column."""
    return parse_reporter_file_text(_read_text(path))


def parse_engine_rate_line(path) -> dict:
    """Read the engine speed from a rate line or a reporter file.

    Accepted shapes: a number written next to `ns/day` on one line (for
    example `Speed (ns/day): 128.96`), and a state-reporter file whose header
    names a speed column. A file with no rate at all gives null and a reason.
    """
    text = _read_text(path)
    for line in text.splitlines():
        m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*ns/day", line, re.IGNORECASE)
        if m:
            return {"ns_per_day": float(m.group(1)), "reason": None}
        if re.search(r"ns/day", line, re.IGNORECASE):
            m = re.search(
                r"ns/day.*?:\s*([0-9]+(?:\.[0-9]+)?)", line, re.IGNORECASE)
            if m:
                return {"ns_per_day": float(m.group(1)), "reason": None}
    lines = text.splitlines()
    lowered = None
    header_index = None
    for index, line in enumerate(lines):
        stripped = line.strip().lstrip("#").strip()
        if not stripped:
            continue
        cols = [c.strip().strip('"').strip("'").lower() for c in stripped.split(",")]
        if any(("speed" in c and "ns/day" in c) or c == "ns/day" for c in cols):
            lowered = cols
            header_index = index
            break
    if lowered is not None:
        speed_idx = next(i for i, c in enumerate(lowered)
                         if ("speed" in c and "ns/day" in c) or c == "ns/day")
        width = len(lowered)
        rate = None
        for line in lines[header_index + 1:]:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip().strip('"') for p in line.split(",")]
            if len(parts) != width:
                raise ParseError(
                    "reporter file is malformed: a data row holds %d fields "
                    "against %d in the header; row %r"
                    % (len(parts), width, line[:120]))
            try:
                value = float(parts[speed_idx])
            except ValueError:
                continue
            if value > 0:
                rate = value
        if rate is not None:
            return {"ns_per_day": rate, "reason": None}
        return {"ns_per_day": None, "reason": "engine rate line missing"}
    return {"ns_per_day": None, "reason": "engine rate line missing"}


def ns_per_day_from_wallclock(steps: int, timestep_fs: float, wallclock_s: float):
    if wallclock_s is None or wallclock_s <= 0:
        return None
    simulated_ns = steps * timestep_fs * 1e-6
    return simulated_ns / wallclock_s * 86400.0


def rates_disagree(engine_rate, wallclock_rate, fraction: float = 0.05) -> bool:
    if engine_rate is None or wallclock_rate is None:
        return False
    if wallclock_rate == 0:
        return True
    return abs(engine_rate - wallclock_rate) / abs(wallclock_rate) > fraction


SCORE_COLUMN_NAMES = ("scoring", "score", "energy")


def header_tokens(line: str) -> list:
    text = line.strip()
    if text.startswith("#"):
        text = text[1:].strip()
    return text.split()


def first_raw_lines(text: str, count: int = 5) -> str:
    lines = text.splitlines()[:count]
    return "first %d raw lines: %s" % (count, "; ".join(repr(l) for l in lines))


def split_fields(line: str) -> list:
    """Split one line of a rank table; blanks inside round brackets stay one field."""
    fields = []
    current = []
    depth = 0
    for token in line.split():
        current.append(token)
        depth += token.count("(") - token.count(")")
        if depth <= 0:
            fields.append(" ".join(current))
            current = []
            depth = 0
    if current:
        fields.append(" ".join(current))
    return fields


def is_data_line(line: str) -> bool:
    parts = split_fields(line)
    if len(parts) < 2:
        return False
    try:
        float(parts[-1])
    except ValueError:
        return False
    return True


def rank_table_shape(text: str) -> dict:
    raw_lines = text.splitlines()
    header = None
    header_index = -1
    counts = []
    for index, raw in enumerate(raw_lines):
        line = raw.strip()
        if not line:
            continue
        if header is None:
            header = header_tokens(line)
            header_index = index
            continue
        if line.startswith("#"):
            continue
        if is_data_line(line):
            counts.append(len(split_fields(line)))
    return {"header": header or [], "header_index": header_index,
            "data_lines": len(counts), "field_counts": counts,
            "lines_after_header": max(0, len(raw_lines) - header_index - 1)
            if header is not None else 0,
            "raw_lines": raw_lines}


def is_monotone(values: list) -> bool:
    rising = all(b >= a for a, b in zip(values, values[1:]))
    falling = all(b <= a for a, b in zip(values, values[1:]))
    return rising or falling


class _RankRows(list):
    """Rows with the extra facts the top-row rule needs kept beside them."""


def top_ranked_row(rows) -> dict:
    """The tool's own first-ranked pose."""
    if not rows:
        raise ParseError("no rows in the docking rank table")
    raw_text = "\n".join(getattr(rows, "raw_lines", []))
    keys = list(rows[0].keys())
    rank_key = getattr(rows, "rank_key", None)
    if rank_key is None:
        rank_key = next((k for k in keys if k.lower() == "rank"), None)
    if rank_key is not None:
        try:
            return min(rows, key=lambda r: float(r[rank_key]))
        except (TypeError, ValueError):
            raise ParseError("rank column is not numeric; " + first_raw_lines(raw_text))
    score_key = getattr(rows, "score_key", None)
    if score_key is None:
        score_key = next((k for k in keys if k.lower() in SCORE_COLUMN_NAMES), None)
    if score_key is None:
        raise ParseError("docking rank table has neither a rank nor a score "
                         "column; " + first_raw_lines(raw_text))
    try:
        scores = [float(r[score_key]) for r in rows]
    except (TypeError, ValueError, KeyError):
        raise ParseError("score column is not numeric; " + first_raw_lines(raw_text))
    if not is_monotone(scores):
        raise ParseError(
            "the score column rises and then falls, so the file is not in rank "
            "order; " + first_raw_lines(raw_text))
    return rows[0]


def parse_rank_table(path) -> dict:
    """Read a docking tool's own ranked list of poses, exactly as written.

    The dict carries rows, columns, mapping and the top row. No data row is
    ever dropped for its field count.
    """
    text = _read_text(path)
    raw_lines = text.splitlines()
    header = None
    header_index = -1
    rows_fields = []
    for index, raw in enumerate(raw_lines):
        line = raw.strip()
        if not line:
            continue
        if header is None:
            header = header_tokens(line)
            header_index = index
            continue
        if line.startswith("#"):
            continue
        if not is_data_line(line):
            continue
        rows_fields.append(split_fields(line))

    if header is None:
        raise ParseError("docking rank table has no header line; "
                         + first_raw_lines(text))
    if not rows_fields:
        after = len(raw_lines) - header_index - 1
        raise ParseError(
            "docking rank table has a header but no data row: %d lines follow "
            "the header; %s" % (after, first_raw_lines(text)))

    counts = sorted(set(len(fields) for fields in rows_fields))
    if len(counts) > 1:
        raise ParseError(
            "docking rank table rows hold different numbers of fields (%s); %s"
            % (", ".join(str(c) for c in counts), first_raw_lines(text)))
    width = counts[0]
    lowered_header = [token.lower() for token in header]

    if width == len(header):
        mapping = "by_name"
        rows = [dict(zip(header, fields)) for fields in rows_fields]
        rank_key = next((t for t in header if t.lower() == "rank"), None)
        score_key = next((t for t in header if t.lower() in SCORE_COLUMN_NAMES), None)
        if rank_key is None and score_key is None:
            raise ParseError(
                "docking rank table names neither a rank nor a score column; %s"
                % first_raw_lines(text))
    else:
        mapping = "positional"
        if not lowered_header or lowered_header[-1] not in SCORE_COLUMN_NAMES:
            raise ParseError(
                "docking rank table has %d header tokens over rows of %d fields, "
                "and its last header token is not a score column; %s"
                % (len(header), width, first_raw_lines(text)))
        names = ["col%d" % i for i in range(width)]
        rows = [dict(zip(names, fields)) for fields in rows_fields]
        rank_key = None
        score_key = names[-1]

    wrapped = _RankRows(rows)
    wrapped.raw_lines = raw_lines
    wrapped.rank_key = rank_key
    wrapped.score_key = score_key
    top = top_ranked_row(wrapped)
    columns = {"header": list(header), "row_field_count": width, "mapping": mapping}
    return {"rows": rows, "columns": columns, "mapping": mapping, "top": top,
            "header": list(header), "field_count": width, "n_rows": len(rows),
            "rank_key": rank_key, "score_key": score_key, "raw_lines": raw_lines}


def parse_af2_timing_rows_text(rows: list) -> dict:
    good = [r for r in rows
            if not r.get("incomplete")
            and not r.get("download_in_timed_call")
            and r.get("wallclock_s") is not None]
    hours = [r["wallclock_s"] / 3600.0 for r in good]
    return {"n": len(good),
            "mean_h": (sum(hours) / len(hours)) if hours else None,
            "hours": hours,
            "pairs": sorted({r.get("pair") for r in good if r.get("pair") is not None})}


def parse_af2_timing_rows(path) -> dict:
    """Mean wall-clock hours over the runs that may be counted, from a rows file."""
    rows = []
    for line in _read_text(path).splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except ValueError as exc:
            raise ParseError(f"rows file {path} holds a line that is not JSON: {exc}")
    return parse_af2_timing_rows_text(rows)


def parse_pdb(path) -> dict:
    """Read atom records; atoms are keyed by chain, residue number, insertion
    code and atom name. A malformed or empty structure file is an error."""
    atoms = read_pdb_atoms(_read_text(path))
    by_key = {}
    for a in atoms:
        by_key.setdefault((a["chain"], a["resseq"], a.get("icode", ""), a["name"]), a)
    by_chain = {}
    for a in atoms:
        by_chain.setdefault(a["chain"], []).append(a)
    return {"atoms": atoms, "by_key": by_key, "by_chain": by_chain,
            "n_atoms": len(atoms)}


# ===========================================================================
# STRUCTURE FILE READING AND THE ANCHOR ARITHMETIC
# ===========================================================================

BACKBONE_ATOMS = ("N", "CA", "C", "O")


def read_pdb_atoms(text: str) -> list:
    """Read atom records of a structure file into plain dictionaries.

    Every ATOM or HETATM line must be complete: a short or unreadable line is
    malformed input, and a file with no atom record at all is malformed too.
    """
    atoms = []
    for index, line in enumerate(text.splitlines(), start=1):
        if not (line.startswith("ATOM") or line.startswith("HETATM")):
            continue
        if len(line) < 54:
            raise ParseError(
                f"structure file is malformed: atom line {index} is truncated; "
                f"got {line!r}")
        try:
            x = float(line[30:38])
            y = float(line[38:46])
            z = float(line[46:54])
            resseq = int(line[22:26])
        except ValueError:
            raise ParseError(
                f"structure file is malformed: atom line {index} does not carry "
                f"readable coordinates and residue number; got {line!r}")
        name = line[12:16].strip()
        element = line[76:78].strip() if len(line) >= 78 else ""
        if not element:
            element = name[0] if name else ""
        atoms.append({
            "record": line[0:6].strip(),
            "serial": line[6:11].strip(),
            "name": name,
            "resname": line[17:20].strip(),
            "chain": line[21:22].strip(),
            "resseq": resseq,
            "icode": line[26:27].strip(),
            "x": x, "y": y, "z": z,
            "element": element.upper(),
        })
    if not atoms:
        raise ParseError("structure file is malformed: it holds no atom record")
    return atoms


def write_pdb(atoms: list) -> str:
    out = []
    for i, a in enumerate(atoms, start=1):
        name = a["name"]
        if len(name) < 4:
            name = " " + name.ljust(3)
        else:
            name = name[:4]
        out.append(
            "{rec:<6}{serial:>5} {name:<4}{alt:1}{resn:>3} {chain:1}{resi:>4}{icode:1}   "
            "{x:8.3f}{y:8.3f}{z:8.3f}{occ:6.2f}{bfac:6.2f}          {elem:>2}".format(
                rec=a.get("record", "ATOM"), serial=i, name=name, alt=" ",
                resn=a["resname"][:3], chain=(a["chain"] or " ")[:1],
                resi=a["resseq"], icode=(a.get("icode") or " ")[:1] or " ",
                x=a["x"], y=a["y"], z=a["z"], occ=1.00, bfac=0.00,
                elem=(a.get("element") or "")[:2]))
    out.append("END")
    return "\n".join(out) + "\n"


def heavy_atoms(atoms: list) -> list:
    return [a for a in atoms if a.get("element") != "H"]


def map_chain_roles(atoms: list, chain_map: dict) -> list:
    out = []
    for a in atoms:
        role = chain_map.get(a["chain"])
        if role is None:
            continue
        b = dict(a)
        b["role"] = role
        out.append(b)
    return out


def _dist2(a, b) -> float:
    dx = a["x"] - b["x"]
    dy = a["y"] - b["y"]
    dz = a["z"] - b["z"]
    return dx * dx + dy * dy + dz * dz


def contact_pairs(role_atoms: list, cutoff: float = CONTACT_CUTOFF_A) -> set:
    cap = [a for a in heavy_atoms(role_atoms) if a["role"] == "capsid"]
    rec = [a for a in heavy_atoms(role_atoms) if a["role"] == "receptor"]
    cut2 = cutoff * cutoff
    pairs = set()
    for ca in cap:
        for ra in rec:
            if _dist2(ca, ra) <= cut2:
                pairs.add(((ca["chain"], ca["resseq"]), (ra["chain"], ra["resseq"])))
    return pairs


def contact_pairs_by_index(role_atoms: list, cutoff: float = CONTACT_CUTOFF_A) -> set:
    cap = [a for a in heavy_atoms(role_atoms) if a["role"] == "capsid"]
    rec = [a for a in heavy_atoms(role_atoms) if a["role"] == "receptor"]
    cut2 = cutoff * cutoff
    pairs = set()
    for ca in cap:
        for ra in rec:
            if _dist2(ca, ra) <= cut2:
                pairs.add((ca["resseq"], ra["resseq"]))
    return pairs


def contact_overlap(reference_contacts: set, pose_contacts: set) -> float:
    """Fraction of the published contacts the pose also makes."""
    if not reference_contacts:
        return 0.0
    return len(reference_contacts & pose_contacts) / float(len(reference_contacts))


def interface_receptor_residues(role_atoms: list, cutoff: float = CONTACT_CUTOFF_A) -> set:
    return {r for (_c, r) in contact_pairs_by_index(role_atoms, cutoff)}


def _backbone_index(role_atoms: list, residues: set) -> dict:
    idx = {}
    for a in role_atoms:
        if a["role"] != "receptor":
            continue
        if a["resseq"] not in residues:
            continue
        if a["name"] not in BACKBONE_ATOMS:
            continue
        idx[(a["resseq"], a["name"])] = (a["x"], a["y"], a["z"])
    return idx


def rmsd_no_superposition(coords_a: list, coords_b: list) -> float:
    """Root-mean-square distance between paired points, as they stand."""
    if not coords_a or len(coords_a) != len(coords_b):
        raise ParseError("cannot compare point sets of different size")
    total = 0.0
    for (ax, ay, az), (bx, by, bz) in zip(coords_a, coords_b):
        total += (ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2
    return math.sqrt(total / len(coords_a))


def interface_backbone_rmsd(reference_role_atoms: list, pose_role_atoms: list,
                            cutoff: float = CONTACT_CUTOFF_A) -> float:
    """Backbone displacement of the receptor residues that form the interface.

    Only N, CA, C and O of the receptor residues that touch the capsid in the
    published structure are compared, in the capsid's frame, no superposition.
    """
    residues = interface_receptor_residues(reference_role_atoms, cutoff)
    ref_idx = _backbone_index(reference_role_atoms, residues)
    pose_idx = _backbone_index(pose_role_atoms, residues)
    keys = sorted(set(ref_idx) & set(pose_idx))
    if not keys:
        raise ParseError("no shared interface backbone atoms to compare")
    return rmsd_no_superposition([ref_idx[k] for k in keys], [pose_idx[k] for k in keys])


def whole_chain_rmsd(atoms_a: list, atoms_b: list, role: str = "receptor") -> float:
    a_idx = {(x["resseq"], x["name"]): (x["x"], x["y"], x["z"])
             for x in atoms_a if x.get("role") == role}
    b_idx = {(x["resseq"], x["name"]): (x["x"], x["y"], x["z"])
             for x in atoms_b if x.get("role") == role}
    keys = sorted(set(a_idx) & set(b_idx))
    if not keys:
        raise ParseError("no shared receptor atoms to compare")
    return rmsd_no_superposition([a_idx[k] for k in keys], [b_idx[k] for k in keys])


def pose_frame_shift(native_capsid_atoms: list, pose_capsid_atoms: list) -> dict:
    """Translation that carries a docked pose into the published structure's frame.

    Atoms are matched by chain letter, residue number, insertion code and atom
    name. The shift is the mean displacement of the matched atoms, and the
    residual is what is left after it. There is no centre-of-atoms fallback and
    no branch that leaves the pose where it is: when nothing matches, the shift
    is zero, the matched count is zero, and the frame guard refuses the pose.
    """
    native_by_key = {}
    for a in native_capsid_atoms:
        native_by_key.setdefault(
            (a["chain"], a["resseq"], a.get("icode", ""), a["name"]), a)
    pose_by_key = {}
    for a in pose_capsid_atoms:
        pose_by_key.setdefault(
            (a["chain"], a["resseq"], a.get("icode", ""), a["name"]), a)
    keys = sorted(set(native_by_key) & set(pose_by_key))
    matched = len(keys)
    expected = max(len(native_by_key), len(pose_by_key))
    if not matched:
        return {"dx": 0.0, "dy": 0.0, "dz": 0.0, "matched_atoms": 0,
                "expected_atoms": expected, "residual_rmsd_a": None,
                "basis": "no capsid atoms matched by chain, residue and atom name"}
    sums = [0.0, 0.0, 0.0]
    for key in keys:
        a = native_by_key[key]
        b = pose_by_key[key]
        sums[0] += a["x"] - b["x"]
        sums[1] += a["y"] - b["y"]
        sums[2] += a["z"] - b["z"]
    dx, dy, dz = sums[0] / matched, sums[1] / matched, sums[2] / matched
    residual_sq = 0.0
    for key in keys:
        a = native_by_key[key]
        b = pose_by_key[key]
        residual_sq += ((a["x"] - (b["x"] + dx)) ** 2
                        + (a["y"] - (b["y"] + dy)) ** 2
                        + (a["z"] - (b["z"] + dz)) ** 2)
    residual = math.sqrt(residual_sq / matched)
    return {"dx": dx, "dy": dy, "dz": dz, "matched_atoms": matched,
            "expected_atoms": expected, "residual_rmsd_a": residual,
            "basis": "capsid atoms matched by chain, residue and atom name"}


def frame_guard(frame: dict) -> dict:
    """Refuse a pose whose rigid capsid is not where the shift puts it.

    The rejection is broken infrastructure with kind anchor_frame, never an
    anchor miss. The caller keeps the raw pose and these numbers.
    """
    matched = frame.get("matched_atoms") or 0
    expected = frame.get("expected_atoms") or 0
    residual = frame.get("residual_rmsd_a")
    if matched <= 0:
        raise FrameGuardReject(
            "no capsid atom matched by chain, residue number, insertion code "
            "and atom name", frame)
    if expected and matched / float(expected) < FRAME_MATCH_FRACTION_MIN:
        raise FrameGuardReject(
            "fewer than 99 percent of the capsid heavy atoms matched "
            f"({matched} of {expected})", frame)
    if residual is None or residual > FRAME_RESIDUAL_MAX_A:
        raise FrameGuardReject(
            f"the capsid residual after the frame shift is {residual} angstrom, "
            f"above {FRAME_RESIDUAL_MAX_A}", frame)
    return frame


def anchor_decision(overlap: float, iface_rmsd: float, serial_parallel_rmsd: float,
                    calls_identical: bool) -> dict:
    """Did the redocking reproduce the published placement?"""
    if overlap is None or iface_rmsd is None:
        raise HarnessFailure(
            "anchor_decision called without a pose",
            "a missing pose is broken infrastructure, never an anchor miss")
    placement_ok = (overlap >= ANCHOR_OVERLAP_MIN) or (iface_rmsd <= ANCHOR_IFACE_RMSD_MAX)
    agreement_ok = (
        serial_parallel_rmsd is not None
        and serial_parallel_rmsd <= ANCHOR_SERIAL_PARALLEL_RMSD_MAX
        and bool(calls_identical))
    return {"overlap": overlap,
            "interface_backbone_rmsd_a": iface_rmsd,
            "serial_parallel_rmsd_a": serial_parallel_rmsd,
            "calls_identical": bool(calls_identical),
            "placement_ok": placement_ok,
            "agreement_ok": agreement_ok,
            "decision": "PASS" if (placement_ok and agreement_ok) else "FAIL"}


def independent_anchor_score(reference_text: str, pose_text: str) -> dict:
    """Score the pose against the published placement with its own code.

    This function shares no code with the scoring above: it parses both files
    itself, estimates its own translation from its own atom matching, and finds
    the contacts with its own brute-force loop over heavy-atom pairs at 4.5
    angstrom. It is the check that the runner's scorer agrees with itself.
    """
    def parse(text):
        out = []
        for line in text.splitlines():
            if not (line.startswith("ATOM") or line.startswith("HETATM")):
                continue
            if len(line) < 54:
                continue
            try:
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                resseq = int(line[22:26])
            except ValueError:
                continue
            name = line[12:16].strip()
            elem = line[76:78].strip() if len(line) >= 78 else ""
            if not elem:
                elem = name[0] if name else ""
            out.append({"name": name, "chain": line[21:22].strip(),
                        "resseq": resseq, "icode": line[26:27].strip(),
                        "x": x, "y": y, "z": z, "element": elem.upper()})
        return out

    ref = parse(reference_text)
    pose = parse(pose_text)

    def key(a):
        return (a["chain"], a["resseq"], a["icode"], a["name"])

    def roles(atoms):
        counts = {}
        for a in atoms:
            counts[a["chain"]] = counts.get(a["chain"], 0) + 1
        if len(counts) < 2:
            raise ParseError("fewer than two chains in the structure")
        ordered = sorted(counts.items(), key=lambda kv: (kv[1], kv[0]))
        receptor_chain = ordered[0][0]
        return ({c: ("receptor" if c == receptor_chain else "capsid")
                 for c in counts}, receptor_chain)

    ref_roles, _ref_receptor = roles(ref)
    pose_roles, _pose_receptor = roles(pose)
    ref_cap = [a for a in ref if ref_roles[a["chain"]] == "capsid"
               and a["element"] != "H"]
    pose_cap = [a for a in pose if pose_roles[a["chain"]] == "capsid"
                and a["element"] != "H"]
    ref_rec = [a for a in ref if ref_roles[a["chain"]] == "receptor"
               and a["element"] != "H"]
    pose_rec = [a for a in pose if pose_roles[a["chain"]] == "receptor"
                and a["element"] != "H"]

    native_by = {}
    for a in ref_cap:
        native_by.setdefault(key(a), a)
    pose_by = {}
    for a in pose_cap:
        pose_by.setdefault(key(a), a)
    shared = sorted(set(native_by) & set(pose_by))
    if not shared:
        raise ParseError("no capsid atom matched; the two files cannot be compared")
    dx = sum(native_by[k]["x"] - pose_by[k]["x"] for k in shared) / len(shared)
    dy = sum(native_by[k]["y"] - pose_by[k]["y"] for k in shared) / len(shared)
    dz = sum(native_by[k]["z"] - pose_by[k]["z"] for k in shared) / len(shared)
    for a in pose_rec + pose_cap:
        a["x"] += dx
        a["y"] += dy
        a["z"] += dz

    cutoff2 = CONTACT_CUTOFF_A * CONTACT_CUTOFF_A

    def contacts(cap, rec):
        out = set()
        for ca in cap:
            for ra in rec:
                ddx = ca["x"] - ra["x"]
                ddy = ca["y"] - ra["y"]
                ddz = ca["z"] - ra["z"]
                if ddx * ddx + ddy * ddy + ddz * ddz <= cutoff2:
                    out.add((ca["resseq"], ra["resseq"]))
        return out

    ref_contacts = contacts(ref_cap, ref_rec)
    pose_contacts = contacts(pose_cap, pose_rec)
    overlap = (len(ref_contacts & pose_contacts) / float(len(ref_contacts))
               if ref_contacts else 0.0)

    iface_res = sorted({r for (_c, r) in ref_contacts})
    wanted = set(BACKBONE_ATOMS)

    def backbone(atoms, role_map):
        out = {}
        for a in atoms:
            if role_map[a["chain"]] != "receptor":
                continue
            if a["resseq"] not in iface_res or a["name"] not in wanted:
                continue
            out[(a["resseq"], a["name"])] = (a["x"], a["y"], a["z"])
        return out

    ref_bb = backbone(ref, ref_roles)
    pose_bb = backbone(pose, pose_roles)
    keys_bb = sorted(set(ref_bb) & set(pose_bb))
    if not keys_bb:
        raise ParseError("no shared interface backbone atoms")
    total = 0.0
    for k in keys_bb:
        total += ((ref_bb[k][0] - pose_bb[k][0]) ** 2
                  + (ref_bb[k][1] - pose_bb[k][1]) ** 2
                  + (ref_bb[k][2] - pose_bb[k][2]) ** 2)
    rmsd = math.sqrt(total / len(keys_bb))
    return {"overlap": overlap, "interface_backbone_rmsd_a": rmsd,
            "n_reference_contacts": len(ref_contacts),
            "n_pose_contacts": len(pose_contacts),
            "shift": {"dx": dx, "dy": dy, "dz": dz},
            "capsid_atoms_matched": len(shared)}


def scorer_agreement(runner: dict, independent: dict) -> dict:
    """Do the two scorings agree, within one percent or 0.01 near zero?"""
    def near(a, b):
        if a is None or b is None:
            return False
        if abs(a) < 1e-9 and abs(b) < 1e-9:
            return True
        if abs(b) < 1e-9:
            return abs(a) <= 0.01
        return abs(a - b) / abs(b) <= 0.01 or abs(a - b) <= 0.01

    ok = (near(runner.get("overlap"), independent.get("overlap"))
          and near(runner.get("interface_backbone_rmsd_a"),
                   independent.get("interface_backbone_rmsd_a")))
    return {"ok": ok,
            "overlap_runner": runner.get("overlap"),
            "overlap_independent": independent.get("overlap"),
            "rmsd_runner": runner.get("interface_backbone_rmsd_a"),
            "rmsd_independent": independent.get("interface_backbone_rmsd_a"),
            "scorer_disagreement": not ok}


# ===========================================================================
# BAND ARITHMETIC
# ===========================================================================


def is_marginal(value: float, band: list, fraction: float = MARGINAL_FRACTION) -> bool:
    """True when the value sits within one tenth of either edge of the band."""
    for edge in band:
        lo = edge * (1.0 - fraction)
        hi = edge * (1.0 + fraction)
        if lo <= value <= hi:
            return True
    return False


def decide_band(value, band: list) -> dict:
    """Read one measured number against the card's band for it."""
    if value is None:
        return {"decision": "VOID", "marginal": False, "reason": "no measured value"}
    if is_marginal(value, band):
        return {"decision": "VOID", "marginal": True,
                "reason": "within 10 percent of a band edge"}
    inside = band[0] <= value <= band[1]
    return {"decision": "PASS" if inside else "FAIL", "marginal": False,
            "reason": None if inside else "outside the card's band"}


def gate_on_c1(value, decision: str, marginal: bool) -> dict:
    """Apply the card's own gate to the AlphaFold timing, and only to it."""
    holds_measurement = decision in ("PASS", "FAIL") or (decision == "VOID" and marginal)
    if value is None or not holds_measurement:
        return {"gate_value": GATE_VALUE, "gate_pass": None,
                "gate_else": GATE_ELSE, "gate": None}
    passed = value <= 1.0
    return {"gate_value": GATE_VALUE, "gate_pass": bool(passed),
            "gate_else": GATE_ELSE, "gate": None}


def relative_sd(values: list):
    clean = [v for v in values if v is not None]
    if len(clean) < 2:
        return None
    mean = sum(clean) / len(clean)
    if mean == 0:
        return None
    return statistics.stdev(clean) / mean


def spread_check(per_pair_times: dict) -> dict:
    """Reruns of one cell must differ; identical numbers mean a wrong source."""
    zero_spread_pairs = []
    high_spread_pairs = []
    details = {}
    for pair, times in sorted(per_pair_times.items()):
        clean = [t for t in times if t is not None]
        if len(clean) < 2:
            details[pair] = {"n": len(clean), "relative_sd": None, "zero_spread": None}
            continue
        rsd = relative_sd(clean)
        zero = len(set(clean)) == 1
        details[pair] = {"n": len(clean), "relative_sd": rsd, "zero_spread": zero}
        if zero:
            zero_spread_pairs.append(pair)
        elif rsd is not None and rsd > SEED_SPREAD_HIGH_RSD:
            high_spread_pairs.append(pair)
    return {"per_pair": details,
            "zero_spread_pairs": zero_spread_pairs,
            "high_spread_pairs": high_spread_pairs,
            "halt": WRONG_VARIANCE_SOURCE if zero_spread_pairs else None}


def storage_from_bytes(bytes_per_run: int) -> dict:
    return {"bytes_per_run": bytes_per_run,
            "gib_216_runs": bytes_per_run * GRID_RUNS / float(BYTES_PER_GIB),
            "gib_432_runs": bytes_per_run * GRID_RUNS_ALT / float(BYTES_PER_GIB)}


def cost_usd(elapsed_s: float, price_per_hour: float) -> float:
    return elapsed_s / 3600.0 * price_per_hour


def stop_at_seconds(price_per_hour: float, budget_left_usd: float,
                    remote_timeout_s: float) -> dict:
    if price_per_hour and price_per_hour > 0:
        dollar_cap_s = budget_left_usd / price_per_hour * 3600.0
    else:
        dollar_cap_s = float(remote_timeout_s)
    stop_at = min(float(remote_timeout_s), dollar_cap_s)
    return {"dollar_cap_s": dollar_cap_s, "time_cap_s": float(remote_timeout_s),
            "stop_at_s": stop_at,
            "binding": "dollars" if dollar_cap_s < remote_timeout_s else "time"}


def stage_allowance_s(state, stage: str) -> float:
    """Seconds this stage may use. Never negative.

        allowance = max(0, min(ceiling(stage), remote_timeout - elapsed - 400 - 100))
    """
    ceiling = float(STAGE_CEILING_S[stage])
    whole_run = min(float(state.remote_timeout_s), float(state.stop_at_s))
    remaining = whole_run - state.elapsed_s() - FETCH_MARGIN_S - ENDPOINTS_SLOT_S
    shared = _shared_ceiling_left(state, stage)
    return max(0.0, min(ceiling, remaining, shared))


def _shared_ceiling_left(state, stage: str) -> float:
    for _name, (total, members) in STAGE_GROUPS.items():
        if stage in members:
            used = sum(state.group_seconds.get(m, 0.0) for m in members)
            return max(0.0, total - used)
    return float("inf")


# ===========================================================================
# CALIBRATION CHECKS. Each returns the checks with values and results, and
# their conjunction.
# ===========================================================================


def _check(name: str, value, result, null_reason=None) -> dict:
    entry = {"check": name, "value": value, "result": bool(result)}
    if not result:
        entry["null_reason"] = null_reason or "check failed"
    return entry


def _conclude(checks: list) -> dict:
    null_reasons = {}
    for c in checks:
        if not c["result"]:
            null_reasons[c["check"]] = c.get("null_reason") or "check failed"
    return {"checks": checks,
            "calibration_valid": all(c["result"] for c in checks),
            "null_reasons": null_reasons}


def _common_checks(ctx: dict, min_count: int, n_counted: int) -> list:
    return [
        _check("sleep_control_passed", ctx.get("sleep_ok"),
               bool(ctx.get("sleep_ok")), "the 60 s sleep control did not pass"),
        _check("gpu_visible", ctx.get("gpu_visible"),
               bool(ctx.get("gpu_visible")), "no graphics processor was visible"),
        _check("stages_before_not_cut", ctx.get("stages_before_ok", True),
               bool(ctx.get("stages_before_ok", True)),
               "a guard, ceiling or timeout cut an earlier stage short"),
        _check("minimum_count", n_counted, n_counted >= min_count,
               f"fewer than {min_count} counted units"),
    ]


def calibration_checks_c1(rows: list, ctx: dict) -> dict:
    counted = [r for r in rows if not r.get("incomplete")
               and not r.get("download_in_timed_call")
               and r.get("wallclock_s") is not None]
    checks = _common_checks(ctx, MIN_AF2_RUNS, len(counted))
    checks.append(_check("gpu_is_a100", ctx.get("gpu_name"),
                         bool(ctx.get("gpu_is_a100")), LABEL_NOT_A100))
    lengths_ok = all(
        PAIR_FASTA_MIN <= (r.get("fasta_length") or 0) <= PAIR_FASTA_MAX
        for r in counted) if counted else False
    checks.append(_check("fasta_length_in_range",
                         [r.get("fasta_length") for r in counted], lengths_ok,
                         "a counted run's pair length is outside 750 to 1000 residues"))
    protocol_ok = all(
        r.get("models") == AF2_MODELS and r.get("recycles") == AF2_RECYCLES
        and str(r.get("early_stopping", "off")) in ("off", "False", "0")
        and r.get("msa_mode") == "single_sequence"
        for r in counted) if counted else False
    checks.append(_check(
        "command_line_protocol",
        [{"models": r.get("models"), "recycles": r.get("recycles"),
          "early_stopping": r.get("early_stopping"),
          "msa_mode": r.get("msa_mode")} for r in counted],
        protocol_ok,
        "a counted run was not 5 models, 20 recycles, early stopping off, "
        "single-sequence"))
    exits_ok = all(r.get("rc") == 0 for r in counted) if counted else False
    checks.append(_check("colabfold_exit_zero", [r.get("rc") for r in counted],
                         exits_ok, "a counted prediction call did not exit zero"))
    files_ok = all(
        r.get("n_model_structures") == AF2_MODELS
        and r.get("n_score_files") == AF2_MODELS
        and bool(r.get("structures_parse_ok"))
        and bool(r.get("score_files_parse_ok"))
        for r in counted) if counted else False
    checks.append(_check(
        "structures_and_scores",
        [{"structures": r.get("n_model_structures"),
          "scores": r.get("n_score_files")} for r in counted],
        files_ok,
        "a counted run lacks a model structure or a score file, or one does "
        "not parse"))
    times_ok = all((r.get("per_model_s") is not None) or bool(r.get("per_model_s_reason"))
                   for r in counted) if counted else False
    checks.append(_check(
        "per_model_times_parsed_or_reasoned",
        [{"per_model_s": r.get("per_model_s"),
          "reason": r.get("per_model_s_reason")} for r in counted],
        times_ok, "per-model times are missing with no reason given"))
    no_download = not any(r.get("download_in_timed_call") for r in rows)
    checks.append(_check("no_download_in_timed_call",
                         [r.get("download_in_timed_call") for r in rows],
                         no_download, "download inside timed call"))
    pairs = sorted({r.get("pair") for r in counted if r.get("pair")})
    checks.append(_check(
        "runs_cover_all_pairs", pairs,
        len(counted) >= MIN_AF2_RUNS and len(pairs) >= N_PAIRS,
        f"fewer than {MIN_AF2_RUNS} counted runs covering all {N_PAIRS} pairs"))
    per_pair = {}
    for r in counted:
        per_pair.setdefault(r.get("pair"), []).append(r.get("wallclock_s"))
    spread = spread_check(per_pair)
    checks.append(_check("nonzero_seed_spread", spread["per_pair"],
                         not spread["zero_spread_pairs"], LABEL_ZERO_SPREAD))
    return _conclude(checks)


def calibration_checks_c2(rows: list, ctx: dict) -> dict:
    counted = [r for r in rows if r.get("atoms") and not r.get("incomplete")]
    finished = [r for r in counted if r.get("production_wallclock_s")]
    checks = _common_checks(ctx, MIN_MD_COMPLEXES, len(finished))
    checks.append(_check("gpu_is_a100", ctx.get("gpu_name"),
                         bool(ctx.get("gpu_is_a100")), LABEL_NOT_A100))
    sizes_ok = all(MD_ATOMS_MIN <= (r.get("atoms") or 0) <= MD_ATOMS_MAX
                   for r in counted) if counted else False
    checks.append(_check("atom_count_in_range", [r.get("atoms") for r in counted],
                         sizes_ok,
                         f"a built system is outside {MD_ATOMS_MIN} to "
                         f"{MD_ATOMS_MAX} atoms"))
    roles_ok = all(bool(r.get("roles_present")) and (r.get("capsid_heavy_atoms") or 0) > 0
                   for r in counted) if counted else False
    checks.append(_check(
        "both_roles_present",
        [{"roles_present": r.get("roles_present"),
          "capsid_heavy_atoms": r.get("capsid_heavy_atoms")} for r in counted],
        roles_ok, "a complex lacks a chain role or a capsid heavy atom"))
    target = MD_EQUIL_STEPS + MD_PRODUCTION_STEPS
    steps_ok = all((r.get("reporter_last_step") or 0) >= target
                   and bool(r.get("energies_finite"))
                   for r in finished) if finished else False
    checks.append(_check(
        "reporter_reached_production_and_finite",
        [{"last_step": r.get("reporter_last_step"),
          "energies_finite": r.get("energies_finite")} for r in finished],
        steps_ok,
        "a reporter file does not reach the equilibration plus 250,000 "
        "production steps, or holds a non-finite energy"))
    frames_ok = all(r.get("trajectory_frames") is not None
                    and abs((r.get("trajectory_frames") or 0) - 50) <= 1
                    for r in finished) if finished else False
    checks.append(_check("trajectory_frame_count",
                         [r.get("trajectory_frames") for r in finished], frames_ok,
                         "a trajectory does not hold 50 frames, plus or minus one"))
    platform_ok = all(r.get("platform") == MD_PLATFORM
                      and r.get("precision") == MD_PRECISION
                      for r in finished) if finished else False
    checks.append(_check(
        "platform_and_precision",
        [{"platform": r.get("platform"), "precision": r.get("precision")}
         for r in finished], platform_ok,
        "a segment did not run on the CUDA platform in mixed precision"))
    checks.append(_check("complex_count", len(finished),
                         len(finished) >= MIN_MD_COMPLEXES,
                         f"fewer than {MIN_MD_COMPLEXES} complexes finished"))
    return _conclude(checks)


def calibration_checks_c3(rows: list, ctx: dict) -> dict:
    counted = [r for r in rows if r.get("seconds") is not None
               and not r.get("truncated") and not r.get("incomplete")]
    checks = _common_checks(ctx, MIN_AUX_PAIRS, len(counted))
    anchor_params = ctx.get("anchor_docking_parameters") or {}
    params_ok = True
    for r in counted:
        got = r.get("docking_parameters") or {}
        for key in ("swarms", "glowworms", "steps", "setup_flags"):
            if key in anchor_params and got.get(key) != anchor_params.get(key):
                params_ok = False
    checks.append(_check(
        "docking_parameters_equal_the_anchor",
        [{"pair": r.get("pair"), "docking_parameters": r.get("docking_parameters")}
         for r in counted],
        bool(counted) and params_ok,
        "a pair's docking parameters differ from the anchor's"))
    rank_ok = all(bool(r.get("rank_table_parsed")) and (r.get("rank_rows") or 0) >= 1
                  and bool(r.get("top_pose_exists")) and bool(r.get("top_pose_roles_ok"))
                  for r in counted) if counted else False
    checks.append(_check(
        "rank_table_and_top_pose",
        [{"rank_table_parsed": r.get("rank_table_parsed"),
          "rank_rows": r.get("rank_rows"),
          "top_pose_exists": r.get("top_pose_exists"),
          "top_pose_roles_ok": r.get("top_pose_roles_ok")} for r in counted],
        rank_ok,
        "a pair's rank table does not parse, or its top pose is missing or "
        "lacks a chain role"))
    analysis_ok = all(
        bool(r.get("contacts_at_4p5")) and bool(r.get("interface_residues_written"))
        and bool(r.get("threefold_distance_written")) and bool(r.get("site_class_written"))
        and bool(r.get("call_table_row_written"))
        for r in counted) if counted else False
    checks.append(_check(
        "interface_analysis_complete",
        [{"pair": r.get("pair"), "contacts_at_4p5": r.get("contacts_at_4p5"),
          "call_table_row_written": r.get("call_table_row_written")}
         for r in counted],
        analysis_ok, "an interface analysis is missing a field or a call-table row"))
    limit_ok = all(not r.get("truncated") for r in rows)
    checks.append(_check(
        "no_pair_reached_its_limit",
        [{"pair": r.get("pair"), "truncated": r.get("truncated")} for r in rows],
        limit_ok, "a pair reached its 250 s limit"))
    pairs = sorted({r.get("pair") for r in counted if r.get("pair")})
    checks.append(_check("pair_count", pairs, len(pairs) >= MIN_AUX_PAIRS,
                         f"fewer than {MIN_AUX_PAIRS} pairs finished"))
    return _conclude(checks)


def calibration_checks_c4(rows: list, ctx: dict) -> dict:
    checks = _common_checks(ctx, 1, len(rows))
    kinds = {"af2": [], "docking": [], "md": []}
    for r in rows:
        kind = r.get("kind")
        if kind in kinds:
            kinds[kind].append(r)
    each_ok = True
    for _kind, entries in kinds.items():
        if not entries:
            each_ok = False
        if any((e.get("bytes") or 0) <= 0 for e in entries):
            each_ok = False
        if any(not e.get("counts_in") for e in entries):
            each_ok = False
    checks.append(_check(
        "each_artifact_type_nonzero_and_counted",
        {k: [{"bytes": e.get("bytes"), "counts_in": e.get("counts_in"),
              "source": e.get("source")} for e in v] for k, v in kinds.items()},
        each_ok,
        "an artifact type is missing, holds zero bytes, or comes from a run "
        "that does not count"))
    checks.append(_check("at_least_one_of_each_type",
                         {k: len(v) for k, v in kinds.items()},
                         all(len(v) >= 1 for v in kinds.values()),
                         "not every artifact type was produced"))
    setup_excluded = all(r.get("md_setup_bytes") is None or r.get("md_setup_bytes") >= 0
                         for r in rows)
    checks.append(_check("md_setup_bytes_excluded",
                         [r.get("md_setup_bytes") for r in rows], setup_excluded,
                         "set-up bytes leaked into the value"))
    return _conclude(checks)


CALIBRATION_CHECKS = {
    "C1": calibration_checks_c1,
    "C2": calibration_checks_c2,
    "C3": calibration_checks_c3,
    "C4": calibration_checks_c4,
}


# ===========================================================================
# RUN STATE
# ===========================================================================


class RunState:
    """Everything the stages share: where to write, the clock, and the tools."""

    def __init__(self, outdir, workdir, datadir, clock=None, now=None,
                 env=None, runner=None, provenance=None, base=None, indir=None):
        self.outdir = Path(outdir)
        self.workdir = Path(workdir)
        self.datadir = Path(datadir)
        self.indir = Path(indir) if indir is not None else self.outdir
        self.base = Path(base) if base is not None else self.outdir.parent.parent
        self.outdir.mkdir(parents=True, exist_ok=True)
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.env = dict(env if env is not None else os.environ)
        self.clock = clock or time.time
        self.now = now or utc_now
        self.runner = runner
        self.provenance = provenance

        self.price_usd_per_hour = _env_float(
            self.env, "PRICE_USD_PER_HOUR", DEFAULT_PRICE_USD_PER_HOUR)
        self.budget_left_usd = min(
            _env_float(self.env, "BUDGET_LEFT_USD", DEFAULT_BUDGET_LEFT_USD),
            DEFAULT_BUDGET_LEFT_USD)
        raw_timeout = self.env.get("REMOTE_TIMEOUT", "")
        self.remote_timeout_forwarded = bool(str(raw_timeout).strip())
        self.remote_timeout_s = min(
            _env_float(self.env, "REMOTE_TIMEOUT", DEFAULT_REMOTE_TIMEOUT_S),
            DEFAULT_REMOTE_TIMEOUT_S)
        self.t0 = _env_float(self.env, "M4_T0_EPOCH", None) or self.clock()
        self.pre_t0_seconds = _env_float(self.env, "M4_PRE_T0_SECONDS", 0.0)
        self.bootstrap_assumed = str(
            self.env.get("M4_BOOTSTRAP_ASSUMED", "")).strip() in ("1", "true", "yes")

        caps = stop_at_seconds(self.price_usd_per_hour, self.budget_left_usd,
                               self.remote_timeout_s)
        self.caps = caps
        self.stop_at_s = caps["stop_at_s"]

        self.run_valid = True
        self.run_valid_voided_by = None
        self.stopped = False
        self.stop_events = []
        self.stages_done = []
        self.notes = []
        self.group_seconds = {}

        self.rows = {}
        self.inputs_status = {
            cid: {"state": "not_measured",
                  "status": "void_by_rule:stage not reached in this invocation",
                  "reason": "the stage that measures it did not run here",
                  "decision": None,
                  "voided_by": None, "calibration_valid": False}
            for cid in INPUT_IDS}
        self.failure_kind = None
        self.anchor_missed = None
        self.records_written = []
        self.labels_cache = None
        self.setup_seconds_used = _env_float(self.env, "M4_SETUP_SECONDS", 0.0)
        self.setup_total_exhausted = False
        self.download_record_path = None
        self.venv_path = (self.env.get("M4_VENV")
                          or str(self.venv_bin().parent) or None)
        self.expected_lock_sha256 = (
            str(self.env.get("ENV_LOCK_SHA256", "")).strip() or None)
        self.observed_lock_sha256 = (
            str(self.env.get("M4_ENV_LOCK_OBSERVED", "")).strip() or None)
        self.environment_changed_by_fixer = str(
            self.env.get("M4_ENV_CHANGED_BY_FIXER", "")).strip() in ("1", "true", "yes")
        self.held_attempts = int(_env_float(self.env, "M4_HELD_ATTEMPTS", 0.0) or 0)
        self.changes_log_sha256 = (
            str(self.env.get("M4_CHANGES_LOG_SHA256", "")).strip() or None)
        self.pairs_path = None
        self.pairs = []
        self.overhead_s = 0.0
        self.overhead_bytes = 0
        self.overhead_labels = []
        self.anchor = None
        self.gpu_is_a100 = None
        self.gpu_name = None
        self.gpu_visible = None
        self.sleep_ok = None
        self.unit_times = {}
        self.compute = {}
        self.exit_code = None
        self.calibration = {}

    # -- tools -------------------------------------------------------------

    def venv_bin(self) -> Path:
        override = self.env.get("M4_VENV_BIN")
        if override:
            return Path(override)
        return Path(sys.executable).resolve().parent

    def python_executable(self) -> str:
        override = self.env.get("M4_PYTHON")
        if override:
            return override
        candidate = self.venv_bin() / "python3"
        if candidate.exists():
            return str(candidate)
        return sys.executable

    def tool(self, name: str) -> str:
        """One external program, through its environment variable if set."""
        key = TOOL_ENV_VARS.get(name, "")
        override = self.env.get(key) if key else None
        if override:
            return override
        if name == "md_worker":
            return ""
        if name == "fetch":
            return "curl"
        if name == "sleep":
            return "sleep"
        if name == "python":
            return self.python_executable()
        candidate = self.venv_bin() / name
        if candidate.exists():
            return str(candidate)
        return name

    def tool_command(self, name: str) -> list:
        value = self.tool(name)
        if not value:
            return []
        return shlex.split(value)

    # -- clock -------------------------------------------------------------

    def elapsed_s(self) -> float:
        return max(0.0, self.clock() - self.t0)

    def time_left_s(self) -> float:
        return self.stop_at_s - self.elapsed_s()

    def spend_usd(self) -> float:
        return cost_usd(self.elapsed_s(), self.price_usd_per_hour)

    # -- validity ----------------------------------------------------------

    def void_run(self, reason: str) -> None:
        if self.run_valid:
            self.run_valid = False
            self.run_valid_voided_by = reason
        self.notes.append(f"run_valid set false: {reason}")

    def record_stop(self, kind: str, stage: str, detail: str) -> None:
        self.stopped = True
        arithmetic = guard_arithmetic_line(self)
        reason = f"{detail}; {arithmetic}"
        self.stop_events.append(
            {"kind": kind, "stage": stage, "reason": reason, "detail": detail,
             "guard_arithmetic": arithmetic,
             "elapsed_s": round(self.elapsed_s(), 3), "at_utc": self.now()})

    def set_decided(self, cid: str, decision: str, reason=None,
                    calibration_valid=None) -> None:
        if decision == "VOID":
            self.inputs_status[cid] = {
                "state": "void_by_rule", "status": f"void_by_rule:{reason}",
                "reason": reason, "decision": "VOID", "voided_by": reason,
                "calibration_valid": calibration_valid}
        else:
            self.inputs_status[cid] = {
                "state": "decided", "status": "decided", "reason": reason,
                "decision": decision, "voided_by": None,
                "calibration_valid": calibration_valid}

    def set_unmeasured(self, cid: str, stop_kind: str,
                       calibration_valid=False) -> None:
        self.inputs_status[cid] = {
            "state": "unmeasured", "status": f"unmeasured_by_stop:{stop_kind}",
            "reason": stop_kind, "decision": "VOID", "voided_by": stop_kind,
            "calibration_valid": calibration_valid}

    def set_void_by_failure(self, cid: str, kind: str, reason: str,
                            calibration_valid=False) -> None:
        self.inputs_status[cid] = {
            "state": "void_by_failure", "status": f"void_by_failure:{kind}",
            "reason": reason, "decision": "VOID", "voided_by": reason,
            "calibration_valid": calibration_valid}

    def last_stop_kind(self) -> str:
        if not self.stop_events:
            return "stop_not_recorded"
        return str(self.stop_events[-1].get("kind") or "stop_not_recorded")

    def sweep_unmeasured_after_stop(self) -> None:
        """A stop leaves every input it never reached unmeasured, not void."""
        if not self.stop_events:
            return
        kind = self.last_stop_kind()
        for cid in INPUT_IDS:
            if (self.inputs_status.get(cid) or {}).get("state") == "not_measured":
                self.set_unmeasured(cid, kind, calibration_valid=False)

    def sweep_void_by_failure(self) -> None:
        """A failure voids every input it never reached (exit table, row one)."""
        if not self.failure_kind:
            return
        for cid in INPUT_IDS:
            if (self.inputs_status.get(cid) or {}).get("state") == "not_measured":
                self.set_void_by_failure(
                    cid, self.failure_kind,
                    self.run_valid_voided_by or self.failure_kind)

    def unmeasured_inputs(self) -> list:
        return sorted(cid for cid, s in self.inputs_status.items()
                      if str(s.get("status", "")).startswith("unmeasured_by_stop"))

    def unit_estimate(self, kind: str) -> float:
        done = [t for t in self.unit_times.get(kind, []) if t is not None]
        if done:
            return sum(done) / len(done)
        return float(UNIT_FLOOR_S[kind])

    def note_unit(self, kind: str, seconds: float) -> None:
        self.unit_times.setdefault(kind, []).append(seconds)

    def input_path(self, name: str):
        for root in (self.indir, self.outdir, self.datadir):
            p = Path(root) / name
            if p.exists():
                return p
        return None

    def need_input(self, name: str) -> Path:
        p = self.input_path(name)
        if p is None:
            raise HarnessFailure(
                f"the stage needs {name} and it is not in the inputs",
                f"looked in {self.indir} and {self.outdir}", kind="missing_input")
        return p


def _env_float(env: dict, key: str, default):
    raw = env.get(key, "")
    try:
        text = str(raw).strip()
        if not text:
            return default
        return float(text)
    except (TypeError, ValueError):
        return default


# ===========================================================================
# LABELS
# ===========================================================================

PACKAGE_VERSION_NAMES = (
    ("jax", "jax"), ("jaxlib", "jaxlib"), ("jax-cuda12-plugin", "jax_cuda12_plugin"),
    ("openmm", "openmm"), ("lightdock", "lightdock"), ("colabfold", "colabfold"),
)

LABEL_NOT_INSTALLED = "no such distribution in the environment of record"


def collect_labels(state: RunState) -> dict:
    if state.labels_cache is not None:
        return dict(state.labels_cache)

    labels = {k: None for k in MACHINE_KEYS + ENGINE_KEYS}
    reasons = {}

    labels["instance_type"] = state.env.get("INSTANCE_TYPE") or None
    if labels["instance_type"] is None:
        reasons["instance_type"] = "INSTANCE_TYPE was not forwarded to the box"
    labels["price_usd_per_hour"] = state.price_usd_per_hour
    labels["venv_path"] = state.venv_path
    if labels["venv_path"] is None:
        reasons["venv_path"] = "the environment directory was not forwarded"
    labels["expected_lock_sha256"] = state.expected_lock_sha256
    if labels["expected_lock_sha256"] is None:
        reasons["expected_lock_sha256"] = "ENV_LOCK_SHA256 was not forwarded to the box"
    labels["observed_lock_sha256"] = state.observed_lock_sha256
    if labels["observed_lock_sha256"] is None:
        reasons["observed_lock_sha256"] = (
            "the on-box script recorded no observed lock for this attempt")
    labels["environment_changed_by_fixer"] = bool(state.environment_changed_by_fixer)
    labels["held_attempts"] = state.held_attempts

    smi = state.tool_command("nvidia-smi")
    q = {}
    h = {}
    if smi:
        smi_query = state.runner.capture(
            smi + ["--query-gpu=name,driver_version", "--format=csv,noheader"],
            limit_s=30, stage="labels", name="nvidia_smi_query")
        smi_header = state.runner.capture(
            smi, limit_s=30, stage="labels", name="nvidia_smi_header")
        if smi_query.get("ok"):
            q_path = state.outdir / "tool_logs" / "labels_nvidia_smi_query.txt"
            atomic_write_text(q_path, smi_query.get("stdout", ""))
            q = parse_nvidia_smi_query(q_path)
        if smi_header.get("ok"):
            h_path = state.outdir / "tool_logs" / "labels_nvidia_smi_header.txt"
            atomic_write_text(h_path, smi_header.get("stdout", ""))
            h = parse_nvidia_smi_header(h_path)

    labels["gpu_name"] = q.get("gpu_name")
    if labels["gpu_name"] is None:
        reasons["gpu_name"] = "nvidia-smi did not report a graphics-processor name"
    labels["gpu_driver"] = q.get("driver_version") or h.get("driver_version")
    if labels["gpu_driver"] is None:
        reasons["gpu_driver"] = "nvidia-smi did not report a driver version"
    labels["cuda_runtime_version"] = h.get("cuda_version_header")
    if labels["cuda_runtime_version"] is None:
        reasons["cuda_runtime_version"] = (
            "the nvidia-smi banner carried no CUDA Version field")

    versions = read_package_versions(state)
    installed_here = bool(versions.get("versions_from_environment_of_record"))

    def version_reason(if_installed: str) -> str:
        return if_installed if installed_here else LABEL_NOT_INSTALLED

    labels["jax_version"] = versions.get("jax")
    if labels["jax_version"] is None:
        reasons["jax_version"] = version_reason("jax did not report a version")
    labels["jaxlib_version"] = versions.get("jaxlib")
    if labels["jaxlib_version"] is None:
        reasons["jaxlib_version"] = version_reason("jaxlib did not report a version")
    plugin = versions.get("jax_cuda12_plugin")
    labels["jax_cuda_plugin_version"] = plugin
    labels["cuda_plugin_version"] = plugin
    if plugin is None:
        reasons["jax_cuda_plugin_version"] = version_reason(
            "the JAX CUDA plugin package did not report a version")
        reasons["cuda_plugin_version"] = version_reason(
            "the JAX CUDA plugin package did not report a version")
    labels["jax_wheel_build_tags"] = versions.get("wheel_build_tags")
    if labels["jax_wheel_build_tags"] is None:
        reasons["jax_wheel_build_tags"] = version_reason(
            "the installed JAX distributions carry no wheel tag in their metadata")
    labels["alphafold_implementation"] = AF2_IMPLEMENTATION
    labels["alphafold_params_sha256"] = versions.get("params_sha256")
    if labels["alphafold_params_sha256"] is None:
        reasons["alphafold_params_sha256"] = (
            "the parameter archive was not hashed in this run")
    labels["docking_code"] = DOCKING_CODE
    labels["docking_version"] = versions.get("lightdock")
    if labels["docking_version"] is None:
        reasons["docking_version"] = version_reason(
            "the docking code did not report a version")
    labels["md_engine"] = MD_ENGINE
    labels["md_engine_version"] = versions.get("openmm")
    if labels["md_engine_version"] is None:
        reasons["md_engine_version"] = version_reason(
            "the dynamics engine did not report a version")
    labels["md_precision"] = MD_PRECISION
    labels["md_platform"] = MD_PLATFORM

    labels["build_flags"] = {
        "alphafold_implementation": labels["alphafold_implementation"],
        "alphafold_params_sha256": labels["alphafold_params_sha256"],
        "jax_version": labels["jax_version"], "jaxlib_version": labels["jaxlib_version"],
        "jax_cuda_plugin_version": labels["jax_cuda_plugin_version"],
        "jax_wheel_build_tags": labels["jax_wheel_build_tags"],
        "docking_code": labels["docking_code"],
        "docking_version": labels["docking_version"],
        "md_engine": labels["md_engine"],
        "md_engine_version": labels["md_engine_version"],
        "md_precision": labels["md_precision"], "md_platform": labels["md_platform"],
        "environment_lock_sha256": labels["observed_lock_sha256"],
        "alphafold_models": AF2_MODELS, "alphafold_recycles": AF2_RECYCLES,
        "alphafold_early_stopping": "off", "alphafold_msa_mode": "single_sequence",
    }

    labels["start_utc"] = utc_of(state.t0)
    labels["end_utc"] = None
    reasons["end_utc"] = "filled in per record from the stage that produced it"
    labels["null_reasons"] = reasons
    state.labels_cache = dict(labels)
    state.gpu_is_a100 = is_a100(labels["gpu_name"])
    state.gpu_name = labels["gpu_name"]
    state.gpu_visible = labels["gpu_name"] is not None
    return dict(labels)


def read_package_versions(state: RunState) -> dict:
    out = dict(installed_package_versions(state))
    wheel_tags = out.pop("wheel_build_tags", None)
    out["versions_from_environment_of_record"] = any(
        out.get(key) for _name, key in PACKAGE_VERSION_NAMES)
    out["version_sources"] = {"installed_metadata": True}
    out["params_sha256"] = getattr(state, "params_sha256", None)
    out["wheel_build_tags"] = wheel_tags
    return out


def installed_package_versions(state: RunState, skip=()) -> dict:
    code = (
        "import json\n"
        "out={}\n"
        "from importlib.metadata import version, distribution\n"
        "for name,key in (('jax','jax'),('jaxlib','jaxlib'),"
        "('jax-cuda12-plugin','jax_cuda12_plugin'),('openmm','openmm'),"
        "('lightdock','lightdock'),('colabfold','colabfold')):\n"
        "    try: out[key]=version(name)\n"
        "    except Exception: out[key]=None\n"
        "tags=[]\n"
        "for name in ('jax','jaxlib','jax-cuda12-plugin'):\n"
        "    try: text=distribution(name).read_text('WHEEL') or ''\n"
        "    except Exception: text=''\n"
        "    for line in text.splitlines():\n"
        "        if line.startswith('Tag:'):\n"
        "            tags.append(name+' '+line.split(':',1)[1].strip())\n"
        "out['wheel_build_tags']=', '.join(tags) if tags else None\n"
        "print(json.dumps(out))\n")
    res = state.runner.capture(
        [state.python_executable(), "-c", code],
        limit_s=120, stage="labels", name="package_versions")
    out = {}
    if res.get("ok"):
        for line in res.get("stdout", "").splitlines():
            line = line.strip()
            if line.startswith("{"):
                try:
                    out = json.loads(line)
                except ValueError:
                    out = {}
    return {k: v for k, v in out.items() if v and k not in set(skip)}


def labels_for_record(state: RunState, start_epoch, end_epoch, extra=None) -> dict:
    labels = collect_labels(state)
    reasons = dict(labels.get("null_reasons") or {})
    labels["start_utc"] = utc_of(start_epoch) if start_epoch else labels.get("start_utc")
    if labels["start_utc"] is None:
        reasons["start_utc"] = "the stage recorded no start time"
    else:
        reasons.pop("start_utc", None)
    labels["end_utc"] = utc_of(end_epoch) if end_epoch else None
    if end_epoch:
        reasons.pop("end_utc", None)
    else:
        reasons["end_utc"] = "the stage did not finish"
    if extra:
        labels.update(extra)
    labels["null_reasons"] = reasons
    return labels


def label_blocks(labels: dict, kind: str) -> dict:
    spec = REQUIRED_LABEL_KEYS.get(kind) or {"machine": MACHINE_KEYS,
                                             "engine": ENGINE_KEYS}
    labels = labels or {}
    reasons = dict(labels.get("null_reasons") or {})
    out = {"machine": {k: labels.get(k) for k in spec["machine"]}}
    if spec["engine"]:
        out["engine"] = {k: labels.get(k) for k in spec["engine"]}
    carried = set(out["machine"]) | set(out.get("engine", {}))
    out["null_reasons"] = {k: v for k, v in reasons.items() if k in carried}
    for key in carried:
        block = out["machine"] if key in out["machine"] else out["engine"]
        if block[key] is None and not str(out["null_reasons"].get(key) or "").strip():
            out["null_reasons"][key] = "not read on this box; no reason was recorded"
    return out


# ===========================================================================
# RECORD WRITING
# ===========================================================================


def write_record(state: RunState, name: str, *, kind: str, cell: dict, inputs: list,
                 metric: str, values: dict, threshold: dict, decision_rule: str,
                 decision: str, notes: str = "", labels: dict | None = None,
                 extra_notes: list | None = None):
    """Write one result record and remember it.

    A record already on disk is never rewritten: whatever it decided stands.
    """
    prov = state.provenance
    path = state.outdir / name
    if path.exists():
        state.records_written.append(name)
        return path
    tmp = state.outdir / (name + ".prov.tmp")
    labels = labels if labels is not None else labels_for_record(
        state, state.t0, state.clock())
    blocks = label_blocks(labels, kind)
    values = dict(values)
    values["machine"] = blocks["machine"]
    if "engine" in blocks:
        values["engine"] = blocks["engine"]
    reasons = dict(values.get("null_reasons") or {})
    reasons.update(blocks["null_reasons"])
    values["null_reasons"] = reasons
    prov.write_result(tmp, cell=cell, inputs=inputs, metric=metric, values=values,
                      threshold=threshold, decision_rule=decision_rule,
                      decision=decision, notes=notes)
    rec = json.loads(Path(tmp).read_text())
    os.remove(str(tmp))

    note_list = list(extra_notes or [])
    if state.stopped and LABEL_INCOMPLETE not in note_list:
        note_list.append(LABEL_INCOMPLETE)
    if state.anchor_missed and kind in MEASURED_KINDS:
        if LABEL_AFTER_ANCHOR_MISS not in note_list:
            note_list.append(LABEL_AFTER_ANCHOR_MISS)
    if state.environment_changed_by_fixer:
        changed = LABEL_FIXER_CHANGED_ENV % (state.observed_lock_sha256 or "unknown")
        if changed not in note_list:
            note_list.append(changed)
    rec["run_valid"] = bool(state.run_valid)
    rec["run_valid_voided_by"] = state.run_valid_voided_by
    rec["kind"] = kind
    rec["notes_list"] = note_list
    rec["tag"] = TAG
    problems = label_problems(kind, rec["values"])
    if problems:
        rec["label_problems"] = problems
    atomic_write_json(path, rec)
    state.records_written.append(name)
    return path


def record_inputs(state: RunState, rows_file=None, pair_evidence: bool = False,
                  extra_paths=None) -> list:
    prov = state.provenance
    inputs = []
    if rows_file:
        p = Path(rows_file)
        n = sum(1 for _ in open(p)) if p.exists() else None
        inputs.append(prov.describe_input(p, n_items=n))
    if state.download_record_path and Path(state.download_record_path).exists():
        inputs.append(prov.describe_input(state.download_record_path))
    inputs.append({"path": state.venv_path,
                   "sha256_full": state.observed_lock_sha256,
                   "what": "the environment of record, by its lock sha256",
                   "expected_lock_sha256": state.expected_lock_sha256})
    if pair_evidence and state.pairs_path:
        inputs.append(prov.describe_input(state.pairs_path, n_items=len(state.pairs)))
    for extra in extra_paths or []:
        inputs.append(prov.describe_input(extra))
    return inputs


def add_row(state: RunState, arm: str, row: dict) -> Path:
    path = state.outdir / f"rows_{arm}_tag-{TAG}.jsonl"
    row = dict(row)
    row.setdefault("arm", arm)
    row.setdefault("at_utc", state.now())
    row.setdefault("run_valid_at_write", bool(state.run_valid))
    append_jsonl(path, row)
    state.rows.setdefault(arm, []).append(row)
    return path


def load_rows(state: RunState, arm: str) -> list:
    rows = list(state.rows.get(arm) or [])
    if rows:
        return rows
    path = state.input_path(f"rows_{arm}_tag-{TAG}.jsonl")
    if path is not None:
        for index, line in enumerate(Path(path).read_text().splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except ValueError as exc:
                raise ParseError(
                    f"rows file {path} line {index} is not JSON: {exc}; "
                    f"got {line[:120]!r}")
    return rows


# ===========================================================================
# RUNNING A TOOL
# ===========================================================================


def child_env(parent_env: dict, venv_bin, extra: dict | None = None) -> dict:
    env = dict(parent_env)
    for key in SECRET_ENV_KEYS:
        env.pop(key, None)
    bin_dir = str(venv_bin)
    existing = env.get("PATH", "")
    env["PATH"] = bin_dir + (os.pathsep + existing if existing else "")
    if extra:
        env.update(extra)
    return env


def proc_identity(pid: int) -> dict:
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return {"present": False, "comm": None, "starttime": None}
    try:
        close = raw.rindex(")")
        comm = raw[raw.index("(") + 1:close]
        fields = raw[close + 2:].split()
        starttime = fields[19]
    except (ValueError, IndexError):
        return {"present": True, "comm": None, "starttime": None}
    return {"present": True, "comm": comm, "starttime": starttime}


def same_process(pid: int, identity: dict) -> bool:
    current = proc_identity(pid)
    if not current["present"]:
        return False
    if identity.get("comm") is None or identity.get("starttime") is None:
        return False
    return (current["comm"] == identity["comm"]
            and current["starttime"] == identity["starttime"])


class GpuSampler:
    """Counts graphics-processor busy seconds during one stage, every 5 s."""

    def __init__(self, state: RunState):
        self.state = state
        self.samples = []
        self.busy_s = None
        self.reason = None
        self._stop = threading.Event()
        self._thread = None

    def __enter__(self):
        if not self.state.tool("nvidia-smi"):
            self.reason = "no nvidia-smi is configured"
            return self
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=30)
        if self.reason is None:
            busy = 0.0
            for _ts, util in self.samples:
                if util and util > 0:
                    busy += 5.0
            self.busy_s = busy
            if not self.samples:
                self.reason = "the sampler took no reading"
        return False

    def _loop(self):
        while not self._stop.is_set():
            try:
                res = self.state.runner.capture(
                    self.state.tool_command("nvidia-smi")
                    + ["--query-gpu=utilization.gpu", "--format=csv,noheader"],
                    limit_s=20, stage="gpu_sampler", name="util")
                util = None
                for line in (res.get("stdout") or "").splitlines():
                    m = re.search(r"([0-9]+)", line)
                    if m:
                        util = int(m.group(1))
                        break
                self.samples.append((self.state.clock(), util))
            except Exception:
                self.reason = "the utilisation sampler could not run"
                return
            self._stop.wait(5.0)


class ToolRunner:
    """Starts tools, times them, kills them, and keeps every log."""

    def __init__(self, state: RunState):
        self.state = state
        self.groups = {}
        self.log_dir = state.outdir / "tool_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.skipped_signals = []

    def register(self, pgid: int, pid: int) -> None:
        self.groups[pgid] = {"pid": pid, "identity": proc_identity(pid)}
        self._publish()

    def unregister(self, pgid: int) -> None:
        self.groups.pop(pgid, None)
        self._publish()

    def _publish(self) -> None:
        try:
            atomic_write_json(
                self.state.outdir / "process_groups.json",
                {"groups": [
                    {"pgid": pgid, "pid": e["pid"],
                     "comm": e["identity"].get("comm"),
                     "starttime": e["identity"].get("starttime")}
                    for pgid, e in sorted(self.groups.items())]})
        except OSError:
            pass

    def kill_group(self, pgid: int) -> bool:
        entry = self.groups.get(pgid)
        if entry is None:
            self.skipped_signals.append({"pgid": pgid, "why": "not registered"})
            return False
        pid = entry["pid"]
        if not same_process(pid, entry["identity"]):
            self.skipped_signals.append(
                {"pgid": pgid, "pid": pid,
                 "why": "leader gone or replaced; not signalled"})
            self.unregister(pgid)
            return False
        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.killpg(pgid, sig)
            except ProcessLookupError:
                break
            except PermissionError:
                self.skipped_signals.append({"pgid": pgid, "why": "not permitted"})
                break
            time.sleep(0.2)
        self.unregister(pgid)
        return True

    def kill_all_groups(self) -> list:
        killed = []
        for pgid in list(self.groups):
            if self.kill_group(pgid):
                killed.append(pgid)
        return killed

    def capture(self, cmd: list, *, limit_s: float, stage: str, name: str,
                cwd=None, extra_env: dict | None = None) -> dict:
        state = self.state
        env = child_env(state.env, state.venv_bin(), extra_env)
        started = state.clock()
        out_path = self.log_dir / f"{stage}_{name}.log"
        timed_out = False
        rc = None
        stdout = ""
        stderr = ""
        try:
            proc = subprocess.Popen(
                [str(c) for c in cmd], stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, cwd=str(cwd) if cwd else None, env=env,
                text=True, start_new_session=True)
        except (OSError, ValueError) as exc:
            finished = state.clock()
            atomic_write_text(out_path, f"failed to start: {exc}\n")
            return {"ok": False, "rc": None, "timed_out": False, "started": False,
                    "seconds": finished - started, "stdout": "", "stderr": str(exc),
                    "log": str(out_path), "cmd": [str(c) for c in cmd]}
        pgid = os.getpgid(proc.pid)
        self.register(pgid, proc.pid)
        try:
            stdout, stderr = proc.communicate(timeout=max(1.0, float(limit_s)))
            rc = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            self.kill_group(pgid)
            try:
                stdout, stderr = proc.communicate(timeout=30)
            except Exception:
                stdout, stderr = "", ""
            rc = proc.returncode
        finally:
            self.unregister(pgid)
        finished = state.clock()
        atomic_write_text(
            out_path,
            "$ " + " ".join(str(c) for c in cmd) + "\n"
            + f"# exit {rc} timed_out={timed_out} seconds={finished - started:.3f}\n"
            + "--- stdout ---\n" + (stdout or "")
            + "\n--- stderr ---\n" + (stderr or "") + "\n")
        return {"ok": (rc == 0 and not timed_out), "rc": rc,
                "timed_out": timed_out, "started": True,
                "seconds": finished - started, "stdout": stdout or "",
                "stderr": stderr or "", "log": str(out_path),
                "cmd": [str(c) for c in cmd]}


# ===========================================================================
# GUARDS
# ===========================================================================


def guard_arithmetic_line(state: RunState, estimated_s=None, allowance_s=None) -> str:
    """Every number of the guard's arithmetic, in one line a reader can redo."""
    caps = state.caps or {}
    parts = [
        "guard arithmetic:",
        "REMOTE_TIMEOUT %g s" % state.remote_timeout_s,
        "elapsed %.0f s" % state.elapsed_s(),
        "pre_t0 %g s" % state.pre_t0_seconds,
        "price %g USD per hour" % state.price_usd_per_hour,
        "budget %g USD" % state.budget_left_usd,
        "dollar_cap %g s" % float(caps.get("dollar_cap_s") or 0.0),
        "time_cap %g s" % float(caps.get("time_cap_s") or 0.0),
        "stop_at %g s" % state.stop_at_s,
    ]
    if allowance_s is not None:
        parts.append("allowance %.0f s" % allowance_s)
    if estimated_s is not None:
        parts.append("estimate %.0f s" % estimated_s)
    return "; ".join(parts)


def guard_before_stage(state: RunState, stage: str, estimated_s: float) -> float:
    allowance = stage_allowance_s(state, stage)
    arithmetic = guard_arithmetic_line(state, estimated_s=estimated_s,
                                       allowance_s=allowance)
    if allowance <= 0:
        raise GuardStop(f"no time left for the {stage} stage", stage=stage,
                        detail=(f"allowance {allowance:.1f}s, "
                                f"elapsed {state.elapsed_s():.1f}s, "
                                f"stop_at {state.stop_at_s:.1f}s; {arithmetic}"))
    if estimated_s > allowance:
        raise GuardStop(
            f"estimated {estimated_s:.1f}s for the {stage} stage exceeds its "
            f"allowance of {allowance:.1f}s", stage=stage,
            detail=(f"elapsed {state.elapsed_s():.1f}s, "
                    f"stop_at {state.stop_at_s:.1f}s, "
                    f"price {state.price_usd_per_hour}/h, "
                    f"budget {state.budget_left_usd}; {arithmetic}"))
    return allowance


def guard_before_unit(state: RunState, stage: str, kind: str, allowance_left_s: float,
                      estimated_s: float | None = None) -> float:
    estimate = state.unit_estimate(kind) if estimated_s is None else estimated_s
    budget = min(allowance_left_s, stage_allowance_s(state, stage))
    if estimate > budget:
        raise GuardStop(
            f"estimated {estimate:.1f}s for one {kind} exceeds the {budget:.1f}s "
            f"left in the {stage} stage", stage=stage,
            detail=f"elapsed {state.elapsed_s():.1f}s; "
                   + guard_arithmetic_line(state, estimated_s=estimate,
                                           allowance_s=budget))
    return budget


def inner_tool_limit_s(state: RunState, wanted_s: float) -> float:
    inner_cap = state.stop_at_s - state.elapsed_s() - INNER_KILL_SLACK_S
    return max(1.0, min(float(wanted_s), inner_cap))


def setup_call_limit_s(state: RunState, own_limit_s: float, allowance_s: float) -> float:
    left_in_total = STAGE_CEILING_S["capability"] - state.setup_seconds_used
    return min(float(own_limit_s), left_in_total, float(allowance_s))


def spend_setup_seconds(state: RunState, seconds: float) -> None:
    state.setup_seconds_used += max(0.0, float(seconds))
    state.group_seconds["capability"] = state.group_seconds.get("capability", 0.0) \
        + max(0.0, float(seconds))
    if state.setup_seconds_used >= STAGE_CEILING_S["capability"]:
        state.setup_total_exhausted = True


# ===========================================================================
# THE STAND-IN PAIRS
# ===========================================================================

THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
    "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
    "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
    "TYR": "Y", "VAL": "V", "MSE": "M", "SEC": "U", "PYL": "O",
}


def chain_residues(atoms: list) -> dict:
    chains = {}
    seen = {}
    for a in atoms:
        if a["record"] != "ATOM":
            continue
        if a["resname"] not in THREE_TO_ONE:
            continue
        key = (a["chain"], a["resseq"], a["icode"])
        if key in seen:
            continue
        seen[key] = True
        chains.setdefault(a["chain"], []).append(
            (a["resseq"], a["icode"], a["resname"]))
    return chains


def residue_sequence(residues: list) -> str:
    return "".join(THREE_TO_ONE.get(name, "X") for (_n, _i, name) in residues)


def pick_roles(chains: dict) -> dict:
    usable = {c: r for c, r in chains.items() if len(r) >= 20}
    if len(usable) < 2:
        raise HarnessFailure(
            "the published structure has fewer than two usable chains",
            f"chains found: { {c: len(r) for c, r in chains.items()} }")
    by_len = sorted(usable.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    receptor_candidates = [c for c, r in by_len if len(r) >= 50]
    receptor = receptor_candidates[-1] if receptor_candidates else by_len[-1][0]
    capsid = [c for c, _r in by_len if c != receptor]
    if not capsid:
        raise HarnessFailure("no capsid-role chain left after choosing the receptor")
    return {"capsid_chains": capsid, "receptor_chain": receptor}


def _shift_atoms(atoms: list, dx: float, chain_id: str) -> list:
    out = []
    for a in atoms:
        b = dict(a)
        b["x"] = a["x"] + dx
        b["chain"] = chain_id
        out.append(b)
    return out


def build_pairs(pdb_text: str, target_lengths=None) -> list:
    targets = list(target_lengths or PAIR_TARGET_LENGTHS)
    atoms = read_pdb_atoms(pdb_text)
    chains = chain_residues(atoms)
    roles = pick_roles(chains)
    receptor_chain = roles["receptor_chain"]
    capsid_chains = roles["capsid_chains"]

    atoms_by_chain = {}
    for a in atoms:
        if a["record"] != "ATOM":
            continue
        if a["resname"] not in THREE_TO_ONE:
            continue
        atoms_by_chain.setdefault(a["chain"], []).append(a)

    receptor_res = chains[receptor_chain]
    receptor_len = len(receptor_res)
    receptor_atoms = atoms_by_chain[receptor_chain]

    pairs = []
    used_letters = set(chains)
    for index, target in enumerate(targets, start=1):
        want_cap = target - receptor_len
        if want_cap <= 0:
            raise HarnessFailure(
                "pair assertion failed: the receptor chain alone is longer than "
                f"the target length {target}",
                f"receptor {receptor_chain} has {receptor_len} residues")
        taken = []
        remaining = want_cap
        source_cycle = list(capsid_chains)
        copy_number = 0
        while remaining > 0:
            source = source_cycle[copy_number % len(source_cycle)]
            source_res = chains[source]
            if copy_number < len(source_cycle):
                chain_id = source
                shift = 0.0
            else:
                chain_id = _next_chain_letter(used_letters)
                used_letters.add(chain_id)
                shift = 60.0 * (1 + copy_number - len(source_cycle))
            keep = min(remaining, len(source_res))
            taken.append({"source_chain": source, "chain_id": chain_id,
                          "n_residues": keep, "x_shift_a": shift})
            remaining -= keep
            copy_number += 1
            if copy_number > 20:
                raise HarnessFailure(
                    "pair assertion failed: could not reach the target length "
                    "with twenty capsid chain copies",
                    f"target {target}, receptor {receptor_len}")

        pair_atoms = []
        chain_map = {}
        sequences = {}
        for piece in taken:
            source_res = chains[piece["source_chain"]][: piece["n_residues"]]
            keys = {(n, i) for (n, i, _nm) in source_res}
            picked = [a for a in atoms_by_chain[piece["source_chain"]]
                      if (a["resseq"], a["icode"]) in keys]
            if piece["x_shift_a"]:
                picked = _shift_atoms(picked, piece["x_shift_a"], piece["chain_id"])
            else:
                picked = [dict(a, chain=piece["chain_id"]) for a in picked]
            pair_atoms.extend(picked)
            chain_map[piece["chain_id"]] = "capsid"
            sequences[piece["chain_id"]] = residue_sequence(source_res)
        pair_atoms.extend([dict(a) for a in receptor_atoms])
        chain_map[receptor_chain] = "receptor"
        sequences[receptor_chain] = residue_sequence(receptor_res)

        total_len = sum(p["n_residues"] for p in taken) + receptor_len
        pairs.append({
            "pair": f"pair{index}", "capsid_slot": index,
            "target_residues": target, "total_residues": total_len,
            "receptor_chain": receptor_chain, "receptor_residues": receptor_len,
            "capsid_pieces": taken, "chain_map": chain_map,
            "sequences": sequences,
            "sequence_joined": ":".join(sequences[c] for c in sorted(sequences)),
            "atoms": pair_atoms})
    return pairs


def _next_chain_letter(used: set) -> str:
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789":
        if ch not in used:
            return ch
    raise HarnessFailure("ran out of chain letters while building the stand-in pairs")


def assert_pairs(pairs: list) -> None:
    if len(pairs) != N_PAIRS:
        raise HarnessFailure(
            f"pair assertion failed: {len(pairs)} pairs built, {N_PAIRS} wanted")
    lengths = []
    seqs = []
    for p in pairs:
        n = p["total_residues"]
        lengths.append(n)
        seqs.append(p["sequence_joined"])
        if not (PAIR_RESIDUES_MIN <= n <= PAIR_RESIDUES_MAX):
            raise HarnessFailure(
                "pair assertion failed: total length outside 750 to 1,000 residues",
                f"{p['pair']} has {n} residues")
        roles = set(p["chain_map"].values())
        if roles != {"capsid", "receptor"}:
            raise HarnessFailure(
                "pair assertion failed: a pair does not hold both a capsid-role "
                "and a receptor-role chain set",
                f"{p['pair']} roles: {sorted(roles)}")
        if sum(1 for v in p["chain_map"].values() if v == "receptor") != 1:
            raise HarnessFailure(
                "pair assertion failed: a pair must hold exactly one receptor-role "
                "chain", f"{p['pair']} chain map: {p['chain_map']}")
    if len(set(seqs)) != len(seqs):
        raise HarnessFailure(
            "pair assertion failed: two stand-in pairs have the same sequence")
    for i in range(len(lengths)):
        for j in range(i + 1, len(lengths)):
            if abs(lengths[i] - lengths[j]) < PAIR_LENGTH_SPREAD_MIN:
                raise HarnessFailure(
                    "pair assertion failed: two pair lengths are closer than "
                    "20 residues", f"{lengths[i]} and {lengths[j]}")


def write_pair_evidence(state: RunState, pairs: list, source_pdb) -> Path:
    entries = []
    for p in pairs:
        pdb_path = state.outdir / f"pair_{p['pair']}_tag-{TAG}.pdb"
        fasta_path = state.outdir / f"pair_{p['pair']}_tag-{TAG}.fasta"
        atomic_write_text(pdb_path, write_pdb(p["atoms"]))
        fasta_lines = [f">{p['pair']}"]
        fasta_lines.append(":".join(p["sequences"][c] for c in sorted(p["sequences"])))
        atomic_write_text(fasta_path, "\n".join(fasta_lines) + "\n")
        p["pdb_path"] = str(pdb_path)
        p["fasta_path"] = str(fasta_path)
        p["fasta_length"] = sum(len(s) for s in p["sequences"].values())
        entries.append({
            "pair": p["pair"], "capsid_slot": p["capsid_slot"],
            "chain_map": p["chain_map"], "receptor_chain": p["receptor_chain"],
            "capsid_pieces": p["capsid_pieces"], "sequences": p["sequences"],
            "lengths": {c: len(s) for c, s in p["sequences"].items()},
            "total_residues": p["total_residues"],
            "fasta_length": p["fasta_length"],
            "fasta_path": str(fasta_path), "fasta_sha256": sha256_file(fasta_path),
            "pdb_path": str(pdb_path), "pdb_sha256": sha256_file(pdb_path)})
    doc = {"what": "three stand-in capsid-receptor complexes built from the "
                   f"chains of PDB entry {PDB_ENTRY}; not the card's own pairs",
           "source_pdb": str(source_pdb),
           "source_pdb_sha256": (sha256_file(source_pdb)
                                 if Path(source_pdb).exists() else None),
           "pairs": entries}
    path = state.outdir / f"pairs_tag-{TAG}.json"
    atomic_write_json(path, doc)
    state.pairs_path = path
    return path


def load_pairs(state: RunState) -> list:
    """Rebuild the pair objects from the evidence file and the pair structures."""
    if state.pairs:
        return state.pairs
    path = state.need_input(f"pairs_tag-{TAG}.json")
    doc = json.loads(Path(path).read_text())
    pairs = []
    for entry in doc.get("pairs", []):
        pdb_path = state.input_path(Path(entry["pdb_path"]).name) \
            or Path(entry["pdb_path"])
        fasta_path = state.input_path(Path(entry["fasta_path"]).name) \
            or Path(entry["fasta_path"])
        atoms = read_pdb_atoms(Path(pdb_path).read_text())
        pairs.append({
            "pair": entry["pair"], "capsid_slot": entry.get("capsid_slot"),
            "chain_map": entry.get("chain_map") or {},
            "receptor_chain": entry.get("receptor_chain"),
            "total_residues": entry.get("total_residues"),
            "sequences": entry.get("sequences") or {}, "atoms": atoms,
            "pdb_path": str(pdb_path), "fasta_path": str(fasta_path),
            "fasta_length": entry.get("fasta_length")
            or sum(len(s) for s in (entry.get("sequences") or {}).values())})
    state.pairs = pairs
    state.pairs_path = path
    return pairs


# ===========================================================================
# THE MOLECULAR-DYNAMICS WORKER
# ===========================================================================

MD_WORKER_SOURCE = r'''#!/usr/bin/env python3
"""Build and run one short explicit-solvent segment, and report its speed."""
import argparse, json, os, sys, time

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["build", "run"], required=True)
    ap.add_argument("--pdb")
    ap.add_argument("--work", required=True)
    ap.add_argument("--padding-nm", type=float, default=1.2)
    ap.add_argument("--steps", type=int, default=250000)
    ap.add_argument("--timestep-fs", type=float, default=2.0)
    ap.add_argument("--equil-steps", type=int, default=2000)
    ap.add_argument("--report-interval", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from openmm import app, unit, Platform, LangevinMiddleIntegrator, XmlSerializer
    os.makedirs(args.work, exist_ok=True)
    system_xml = os.path.join(args.work, "system.xml")
    solvated_pdb = os.path.join(args.work, "solvated.pdb")
    forcefield = app.ForceField("amber14-all.xml", "amber14/tip3pfb.xml")

    if args.mode == "build":
        pdb = app.PDBFile(args.pdb)
        modeller = app.Modeller(pdb.topology, pdb.positions)
        modeller.deleteWater()
        modeller.addHydrogens(forcefield)
        modeller.addSolvent(forcefield, model="tip3p",
                            padding=args.padding_nm * unit.nanometer,
                            neutralize=True)
        system = forcefield.createSystem(
            modeller.topology, nonbondedMethod=app.PME,
            nonbondedCutoff=1.0 * unit.nanometer,
            constraints=app.HBonds, rigidWater=True)
        with open(system_xml, "w") as fh:
            fh.write(XmlSerializer.serialize(system))
        with open(solvated_pdb, "w") as fh:
            app.PDBFile.writeFile(modeller.topology, modeller.positions, fh)
        n_atoms = modeller.topology.getNumAtoms()
        n_water = sum(1 for r in modeller.topology.residues()
                      if r.name in ("HOH", "WAT"))
        json.dump({"mode": "build", "atoms": n_atoms, "waters": n_water,
                   "padding_nm": args.padding_nm, "system_xml": system_xml,
                   "solvated_pdb": solvated_pdb}, open(args.out, "w"), indent=2)
        return 0

    pdb = app.PDBFile(solvated_pdb)
    with open(system_xml) as fh:
        system = XmlSerializer.deserialize(fh.read())
    integrator = LangevinMiddleIntegrator(
        300 * unit.kelvin, 1.0 / unit.picosecond,
        args.timestep_fs * unit.femtosecond)
    integrator.setRandomNumberSeed(args.seed)
    platform = Platform.getPlatformByName("CUDA")
    properties = {"Precision": "mixed"}
    sim = app.Simulation(pdb.topology, system, integrator, platform, properties)
    sim.context.setPositions(pdb.positions)

    t_min = time.time()
    sim.minimizeEnergy(maxIterations=500)
    minimise_s = time.time() - t_min

    sim.context.setVelocitiesToTemperature(300 * unit.kelvin, args.seed)
    t_eq = time.time()
    sim.step(args.equil_steps)
    equilibrate_s = time.time() - t_eq

    reporter_path = os.path.join(args.work, "md_reporter.csv")
    sim.reporters.append(app.StateDataReporter(
        reporter_path, args.report_interval, step=True, potentialEnergy=True,
        temperature=True, speed=True, elapsedTime=True, totalSteps=args.steps))
    trajectory_path = os.path.join(args.work, "md_trajectory.dcd")
    sim.reporters.append(app.DCDReporter(trajectory_path, args.report_interval))
    t_prod = time.time()
    sim.step(args.steps)
    production_s = time.time() - t_prod

    json.dump({
        "mode": "run", "atoms": pdb.topology.getNumAtoms(),
        "steps": args.steps, "timestep_fs": args.timestep_fs,
        "production_s": production_s, "minimise_s": minimise_s,
        "equilibrate_s": equilibrate_s, "reporter_path": reporter_path,
        "trajectory_path": trajectory_path,
        "report_interval_steps": args.report_interval,
        "frame_interval_ps": args.report_interval * args.timestep_fs / 1000.0,
        "platform": platform.getName(), "precision": "mixed",
        "openmm_version": __import__("openmm").version.version,
        "seed": args.seed}, open(args.out, "w"), indent=2)
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

MD_SETUP_FILE_NAMES = ("system.xml", "solvated.pdb")
MD_SETUP_SUFFIXES = (".chk", ".checkpoint")


def md_bytes_breakdown(md_dir, extra_log_paths=()) -> dict:
    md_dir = Path(md_dir)
    written = 0
    setup = 0
    files = []
    if md_dir.exists():
        for root, _dirs, names in os.walk(str(md_dir)):
            for nm in sorted(names):
                fp = Path(root) / nm
                try:
                    if fp.is_symlink():
                        continue
                    size = fp.stat().st_size
                except OSError:
                    continue
                is_setup = (nm in MD_SETUP_FILE_NAMES
                            or nm.endswith(MD_SETUP_SUFFIXES))
                if is_setup:
                    setup += size
                else:
                    written += size
                files.append({"file": str(fp), "bytes": size,
                              "counted": not is_setup})
    for extra in extra_log_paths or ():
        p = Path(extra)
        if p.exists() and p.is_file():
            size = p.stat().st_size
            written += size
            files.append({"file": str(p), "bytes": size, "counted": True})
    return {"md_bytes": written, "md_setup_bytes": setup, "files": files}


def water_padding_nm(atoms: list, target_atoms: int = 150000) -> float:
    if not atoms:
        raise HarnessFailure("cannot size a water box around an empty complex")
    xs = [a["x"] for a in atoms]
    ys = [a["y"] for a in atoms]
    zs = [a["z"] for a in atoms]
    extent = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    solute_atoms = len(atoms) * 2
    water_atoms = max(1000, target_atoms - solute_atoms)
    volume_a3 = water_atoms / 0.1
    side = volume_a3 ** (1.0 / 3.0)
    padding_a = max(8.0, (side - extent) / 2.0)
    return round(padding_a / 10.0, 3)


def merge_capsid_and_pose(pair: dict, pose_atoms: list) -> list:
    capsid_ids = [c for c, role in pair["chain_map"].items() if role == "capsid"]
    capsid_atoms = [dict(a) for a in pair["atoms"] if a["chain"] in capsid_ids]
    if not capsid_atoms:
        raise HarnessFailure(
            "the molecular-dynamics input holds no capsid-role chain",
            f"{pair['pair']} chain map: {pair['chain_map']}")
    if not heavy_atoms(capsid_atoms):
        raise HarnessFailure(
            "the molecular-dynamics input holds no capsid heavy atom",
            f"{pair['pair']}")
    receptor_id = pair["receptor_chain"]
    receptor = [dict(a, chain=receptor_id) for a in pose_atoms]
    if not receptor:
        raise HarnessFailure(
            "the molecular-dynamics input holds no receptor-role chain",
            f"{pair['pair']}: the docked pose contributed no atoms")
    merged = capsid_atoms + receptor
    roles = {("capsid" if a["chain"] in capsid_ids else "receptor") for a in merged}
    if roles != {"capsid", "receptor"}:
        raise HarnessFailure(
            "the merged complex does not hold both chain roles",
            f"roles: {sorted(roles)}")
    return merged


# ===========================================================================
# THE COMPUTE TABLE
# ===========================================================================


def compute_row(stage: str) -> dict:
    return {"stage": stage, "ran": False, "reason": "not started",
            "start_utc": None, "end_utc": None, "wall_clock_s": None,
            "gpu_busy_s": None, "gpu_busy_reason": "not sampled",
            "gpu_name": None, "exit_code": None}


def build_compute_table(state: RunState) -> dict:
    rows = []
    for stage in STAGE_ORDER:
        entry = dict(state.compute.get(stage) or compute_row(stage))
        entry["stage"] = stage
        if entry.get("gpu_name") is None:
            entry["gpu_name"] = state.gpu_name
        rows.append(entry)
    return {"stages": rows,
            "instance_type": state.env.get("INSTANCE_TYPE") or None,
            "price_usd_per_hour": state.price_usd_per_hour,
            "elapsed_since_t0_s": round(state.elapsed_s(), 3),
            "estimated_spend_usd": round(state.spend_usd(), 4),
            "pre_t0_seconds": state.pre_t0_seconds,
            "anchor_decision": (state.anchor or {}).get("verdict", {}).get("decision")}


def write_compute_table(state: RunState) -> Path:
    path = state.outdir / f"compute_table_tag-{TAG}.json"
    atomic_write_json(path, build_compute_table(state), sort_keys=False)
    return path


class StageTimer:
    """Opens one compute row when a stage starts and closes it when it ends."""

    def __init__(self, state: RunState, stage: str, gpu: bool = False):
        self.state = state
        self.stage = stage
        self.gpu = gpu
        self.started = None
        self.sampler = None

    def __enter__(self):
        self.started = self.state.clock()
        entry = compute_row(self.stage)
        entry.update({"ran": True, "reason": None,
                      "start_utc": utc_of(self.started),
                      "gpu_name": self.state.gpu_name})
        self.state.compute[self.stage] = entry
        write_compute_table(self.state)
        if self.gpu:
            self.sampler = GpuSampler(self.state)
            self.sampler.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        finished = self.state.clock()
        entry = self.state.compute.get(self.stage) or compute_row(self.stage)
        entry["end_utc"] = utc_of(finished)
        entry["wall_clock_s"] = round(finished - (self.started or finished), 3)
        if self.gpu and self.sampler is not None:
            self.sampler.__exit__(exc_type, exc, tb)
            entry["gpu_busy_s"] = self.sampler.busy_s
            entry["gpu_busy_reason"] = self.sampler.reason
        else:
            entry["gpu_busy_s"] = None
            entry["gpu_busy_reason"] = "not a graphics-processor stage"
        entry["gpu_name"] = self.state.gpu_name
        if exc_type is None:
            entry["exit_code"] = 0
        elif issubclass(exc_type, GuardStop):
            entry["exit_code"] = EXIT_GUARD
            entry["reason"] = "cut short by a guard, a ceiling or a timeout"
        elif issubclass(exc_type, (HarnessFailure, FrameGuardReject)):
            entry["exit_code"] = EXIT_INFRA
            entry["reason"] = "the stage failed"
        else:
            entry["exit_code"] = EXIT_INFRA
            entry["reason"] = "the stage raised"
        self.state.group_seconds[self.stage] = (
            self.state.group_seconds.get(self.stage, 0.0) + entry["wall_clock_s"])
        write_compute_table(self.state)
        return False


# ===========================================================================
# STAGE HELPERS
# ===========================================================================


def make_setup_step(state: RunState, allowance: float, log: dict, stage: str):
    def step(cmd, own_limit_s, name, **kw):
        limit = setup_call_limit_s(state, own_limit_s, allowance)
        if limit <= 0 or state.setup_total_exhausted:
            raise HarnessFailure(
                "the setup budget of 1,500 seconds ran out",
                f"used {state.setup_seconds_used:.1f}s before step {name}",
                kind="setup_total_ceiling")
        res = state.runner.capture(cmd, limit_s=limit, stage=stage, name=name, **kw)
        spend_setup_seconds(state, res.get("seconds", 0.0))
        log["steps"].append(
            {"name": name, "cmd": res.get("cmd"), "rc": res.get("rc"),
             "seconds": round(res.get("seconds", 0.0), 3),
             "timed_out": res.get("timed_out"), "log": res.get("log")})
        if state.setup_total_exhausted and not res.get("ok"):
            raise HarnessFailure(
                "the setup budget of 1,500 seconds ran out",
                f"step {name} ended at {state.setup_seconds_used:.1f}s",
                kind="setup_total_ceiling")
        return res
    return step


SMOKE_PY = r'''
import json, sys
out = {"problems": [], "found": {}}
try:
    import jax
    out["found"]["jax"] = jax.__version__
    devices = [d.platform for d in jax.devices()]
    out["found"]["jax_devices"] = devices
    if not any(p in ("gpu", "cuda") for p in devices):
        out["problems"].append("jax lists no graphics-processor device")
except Exception as exc:
    out["problems"].append("jax unusable: %s" % exc)
try:
    import alphafold
    out["found"]["alphafold"] = getattr(alphafold, "__version__", "present")
except Exception as exc:
    out["problems"].append("the AlphaFold-Multimer stack is unusable: %s" % exc)
try:
    import colabfold
    out["found"]["colabfold"] = getattr(colabfold, "__version__", "present")
except Exception as exc:
    out["problems"].append("colabfold unusable: %s" % exc)
try:
    import openmm
    from openmm import Platform
    out["found"]["openmm"] = openmm.version.version
    Platform.getPlatformByName("CUDA")
    out["found"]["openmm_cuda"] = True
except Exception as exc:
    out["problems"].append("OpenMM has no CUDA platform: %s" % exc)
print(json.dumps(out))
'''

SMOKE_TOOLS = ["colabfold_batch", "lightdock3.py", "lightdock3_setup.py",
               "lgd_generate_conformations.py", "lgd_rank.py"]
SMOKE_HELP_TOOLS = ("colabfold_batch", "lightdock3.py",
                    "lgd_generate_conformations.py")


def smoke_check(state: RunState, step, params_dir) -> dict:
    problems = []
    found = {}
    res = step([state.python_executable(), "-c", SMOKE_PY], 300, "smoke_imports")
    if res.get("ok"):
        payload = {}
        for line in res.get("stdout", "").splitlines():
            if line.strip().startswith("{"):
                try:
                    payload = json.loads(line)
                except ValueError:
                    payload = {}
        problems.extend(payload.get("problems", []))
        found.update(payload.get("found", {}))
        if not payload:
            problems.append("the import check printed nothing readable")
    else:
        problems.append(f"the import check did not run: exit {res.get('rc')}")

    env = child_env(state.env, state.venv_bin())
    resolved = {}
    for tool in SMOKE_TOOLS:
        override = state.env.get(TOOL_ENV_VARS.get(tool, ""))
        path = override or shutil.which(tool, path=env["PATH"])
        resolved[tool] = path
        if path is None:
            problems.append(f"{tool} is not on the virtual environment's search path")
    found["resolved_tools"] = resolved

    for tool in SMOKE_HELP_TOOLS:
        path = resolved.get(tool)
        if not path:
            continue
        res = step([path, "--help"], 120, f"smoke_help_{tool.replace('.', '_')}")
        if not res.get("ok"):
            problems.append(f"{tool} --help exited {res.get('rc')}")

    if params_dir is not None:
        found["params_dir"] = str(params_dir)
        found["params_present"] = not missing_multimer_params(params_dir)
        if not found["params_present"]:
            problems.append("model parameter files are missing after unpacking")
    return {"ok": not problems, "problems": problems, "found": found}


# ===========================================================================
# STAGE: CAPABILITY (the environment record and the capability check)
# ===========================================================================


def compute_lock_sha256(state: RunState):
    """sha256 of the stdout bytes of the environment's own package list."""
    cmd = [state.python_executable(), "-m", "pip", "freeze"]
    try:
        res = state.runner.capture(cmd, limit_s=120, stage="capability",
                                   name="pip_freeze")
    except Exception:
        return None
    if not res.get("started"):
        return None
    stdout = res.get("stdout") or ""
    return sha256_text(stdout)


def stage_capability(state: RunState) -> dict:
    """Write the environment record, then ask every tool what it can do."""
    started = state.clock()
    allowance = guard_before_stage(state, "capability", UNIT_FLOOR_S["endpoints"])
    computed_lock = compute_lock_sha256(state)
    if computed_lock:
        state.observed_lock_sha256 = computed_lock
    log = {"steps": [], "started_utc": utc_of(started),
           "venv_path": state.venv_path,
           "expected_lock_sha256": state.expected_lock_sha256,
           "observed_lock_sha256": state.observed_lock_sha256,
           "installs_run": "none: this program installs nothing"}
    write_env_check_record(state, started)
    if not is_lock_hash(state.expected_lock_sha256):
        raise HarnessFailure(
            "the lock of the environment of record was not forwarded",
            "ENV_LOCK_SHA256 must be 64 hexadecimal characters and has no "
            f"default; it was {state.expected_lock_sha256!r}", kind="env_lock")
    if state.expected_lock_sha256 != state.observed_lock_sha256:
        # A repair on the box changes the package list, so the hash differs on
        # purpose. The shell says so, and then the difference is recorded and
        # labelled, not fatal. Any other difference stops the run.
        if state.environment_changed_by_fixer:
            log["lock_mismatch_after_fixer"] = (
                LABEL_FIXER_CHANGED_ENV % (state.observed_lock_sha256 or "unknown"))
        else:
            raise HarnessFailure(
                "the environment lock does not match",
                f"expected {state.expected_lock_sha256}, observed "
                f"{state.observed_lock_sha256}", kind="env_lock")
    step = make_setup_step(state, allowance, log, "capability")
    # Ask the box for its labels first: this is what reads nvidia-smi and sets
    # the graphics-processor flag. Without it the flag is still unset here, and
    # a working processor is reported as missing.
    collect_labels(state)
    capability = smoke_check(state, step, None)
    if not state.gpu_visible:
        capability["problems"].append(
            "nvidia-smi reported no graphics processor")
        capability["ok"] = False
    log["capability_check"] = capability
    if not capability["ok"]:
        raise HarnessFailure("the capability check failed",
                             json.dumps(capability["problems"]),
                             kind="capability_check")
    log["setup_seconds_used"] = round(state.setup_seconds_used, 3)
    log["finished_utc"] = utc_of(state.clock())
    atomic_write_json(state.outdir / f"setup_log_tag-{TAG}.json", log)
    state.stages_done.append("capability")
    return log


def is_lock_hash(value) -> bool:
    """True only for the 64 hexadecimal characters of a sha256 sum."""
    text = str(value or "").strip()
    return len(text) == 64 and all(c in "0123456789abcdefABCDEF" for c in text)


def write_env_check_record(state: RunState, started) -> Path:
    """The one record of the environment lock check (item 3)."""
    name = f"env_check_tag-{TAG}.json"
    if (state.outdir / name).exists():
        return state.outdir / name
    equal = (state.expected_lock_sha256 is not None
             and state.expected_lock_sha256 == state.observed_lock_sha256)
    values = {
        "kind": "environment_check",
        "expected_lock_sha256": state.expected_lock_sha256,
        "observed_lock_sha256": state.observed_lock_sha256,
        "venv_path": state.venv_path,
        "python_version": "%d.%d.%d" % sys.version_info[:3],
        "equal": bool(equal),
        "null_reasons": {},
    }
    if state.expected_lock_sha256 is None:
        values["null_reasons"]["expected_lock_sha256"] = (
            "ENV_LOCK_SHA256 was unset or malformed")
    return write_record(
        state, name, kind="env_check",
        cell={"stage": "environment check", "tag": TAG},
        inputs=record_inputs(state),
        metric="the sha256 of the package list of the environment of record",
        values=values,
        threshold={"expected_lock_sha256": state.expected_lock_sha256},
        decision_rule=("the environment is the one of record only when the hash "
                       "of its package list equals the lock the launcher "
                       "forwarded; anything else stops the run"),
        decision="PASS" if equal else "FAIL",
        labels=labels_for_record(state, started, state.clock()))


# ===========================================================================
# STAGE: DOWNLOADS
# ===========================================================================


def recorded_download_sha256(state: RunState, path) -> str:
    record = Path(state.outdir).parent / "held_attempt_1" / f"downloads_tag-{TAG}.json"
    if not record.exists():
        return ""
    try:
        doc = json.loads(record.read_text())
    except (OSError, ValueError):
        return ""
    for entry in doc.get("downloads", []):
        if entry.get("path") == str(path):
            return entry.get("sha256") or ""
    return ""


def may_reuse_download(state: RunState, path) -> bool:
    path = Path(path)
    if not path.exists():
        return False
    recorded = recorded_download_sha256(state, path)
    if not recorded:
        return False
    return sha256_file(path) == recorded


def stage_downloads(state: RunState) -> dict:
    """Fetch the declared files, unpack the parameters, and build the pairs."""
    started = state.clock()
    allowance = guard_before_stage(state, "downloads", UNIT_FLOOR_S["endpoints"])
    log = {"steps": [], "downloads": [], "started_utc": utc_of(started)}
    step = make_setup_step(state, allowance, log, "downloads")
    download_dir = Path(getattr(state, "download_dir", None) or state.datadir)
    download_dir.mkdir(parents=True, exist_ok=True)

    pdb_path = download_dir / f"{PDB_ENTRY}.pdb"
    pdb_reused = may_reuse_download(state, pdb_path)
    if not pdb_reused:
        res = step(state.tool_command("fetch")
                   + ["-fsSL", "--retry", "3", "-o", str(pdb_path), PDB_URL],
                   300, "download_pdb")
        if not res.get("ok") or not pdb_path.exists():
            raise HarnessFailure(
                f"downloading the published structure {PDB_ENTRY} failed",
                f"exit {res.get('rc')} from {PDB_URL}", kind="download")
    log["downloads"].append({"what": f"PDB entry {PDB_ENTRY}", "url": PDB_URL,
                             "path": str(pdb_path), "sha256": sha256_file(pdb_path),
                             "reused": pdb_reused,
                             "bytes": pdb_path.stat().st_size})

    # The published file is copied into the results byte for byte: the launcher
    # fetches only that directory, and a reader needs the file itself.
    kept_pdb = state.outdir / f"{PDB_ENTRY}_tag-{TAG}.pdb"
    shutil.copyfile(str(pdb_path), str(kept_pdb))

    params_dir = download_dir / "params"
    params_dir.mkdir(parents=True, exist_ok=True)
    archive = download_dir / "alphafold_params.tar"
    archive_reused = may_reuse_download(state, archive)
    if not archive_reused:
        res = step(state.tool_command("fetch")
                   + ["-fsSL", "--retry", "3", "-o", str(archive), AF_PARAMS_URL],
                   900, "download_params")
        if not res.get("ok") or not archive.exists():
            raise HarnessFailure(
                "downloading the AlphaFold parameter archive failed",
                f"exit {res.get('rc')} from {AF_PARAMS_URL}", kind="download")
    state.params_sha256 = sha256_file(archive)
    log["downloads"].append({"what": "AlphaFold parameter archive",
                             "url": AF_PARAMS_URL, "path": str(archive),
                             "sha256": state.params_sha256,
                             "reused": archive_reused,
                             "bytes": archive.stat().st_size})
    res = step(["tar", "-xf", str(archive), "-C", str(params_dir)],
               600, "extract_params")
    if not res.get("ok"):
        raise HarnessFailure("unpacking the parameter archive failed",
                             f"exit {res.get('rc')}", kind="download")
    missing = missing_multimer_params(params_dir)
    if missing:
        raise HarnessFailure(
            "the unpacked parameters do not hold a file for every model",
            "missing: " + ", ".join(missing), kind="download")
    log["params_dir"] = str(params_dir)
    log["params_files"] = sorted(
        p.name for p in params_dir.glob("params_*multimer*.npz"))
    markers = write_parameter_markers(state, params_dir)
    log["params_markers"] = markers
    atomic_write_json(state.outdir / f"params_markers_tag-{TAG}.json", markers)

    download_record = state.outdir / f"downloads_tag-{TAG}.json"
    atomic_write_json(download_record, {
        "sources": list(ALLOWED_DOWNLOAD_HOSTS),
        "downloads": log["downloads"], "params_dir": str(params_dir),
        "params_files": log["params_files"],
        "note": ("the only two sources this run fetches from; no package index "
                 "is used anywhere, because nothing is installed on the box")})
    state.download_record_path = download_record

    pairs = build_pairs(pdb_path.read_text())
    assert_pairs(pairs)
    state.pairs = pairs
    write_pair_evidence(state, pairs, pdb_path)
    log["pairs"] = [{"pair": p["pair"], "residues": p["total_residues"]}
                    for p in pairs]
    log["setup_seconds_used"] = round(state.setup_seconds_used, 3)
    log["finished_utc"] = utc_of(state.clock())
    atomic_write_json(state.outdir / f"download_log_tag-{TAG}.json", log)
    state.stages_done.append("downloads")
    return log


MARKER_NAME_PATTERN = re.compile(
    r"([A-Za-z0-9_\-]*(?:download|complete|finished)[A-Za-z0-9_\-]*\.txt)",
    re.IGNORECASE)


def colabfold_marker_names(source_text: str) -> list:
    names = []
    for name in MARKER_NAME_PATTERN.findall(str(source_text or "")):
        if name not in names:
            names.append(name)
    return names


def find_download_module(state: RunState):
    bin_dir = state.venv_bin()
    roots = [bin_dir.parent / "lib"]
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.glob("python3*/site-packages/colabfold/download.py")):
            return path
        for path in sorted(root.glob("**/colabfold/download.py")):
            return path
    return None


def write_parameter_markers(state: RunState, params_dir) -> dict:
    module = find_download_module(state)
    if module is None:
        return {"module": None, "markers": [],
                "note": "no download module was found in the installed packages"}
    names = colabfold_marker_names(Path(module).read_text())
    if not names:
        return {"module": str(module), "markers": [], "note": "no marker named"}
    written = []
    for name in names:
        path = Path(params_dir) / name
        atomic_write_text(path, "parameters unpacked by run_m4.py before any "
                                "timed call; written because the installed "
                                "download module checks for this file\n")
        written.append(str(path))
    return {"module": str(module), "markers": names, "written": written,
            "note": "marker names read from the installed module's own source"}


def missing_multimer_params(params_dir) -> list:
    present = {p.name for p in Path(params_dir).rglob("*.npz")}
    missing = []
    for i in range(1, AF2_MODELS + 1):
        wanted = [n for n in present if f"model_{i}" in n and "multimer" in n]
        if not wanted:
            missing.append(f"model_{i} multimer parameters")
    return missing


# ===========================================================================
# STAGE: CONTROLS
# ===========================================================================


def timed_call(state: RunState, name: str, cmd: list, limit_s: float, stage: str,
               cwd=None, extra_env=None) -> dict:
    work = state.workdir / f"{stage}_{name}"
    work.mkdir(parents=True, exist_ok=True)
    before = state.clock()
    res = state.runner.capture(
        cmd, limit_s=inner_tool_limit_s(state, limit_s), stage=stage, name=name,
        cwd=cwd or work, extra_env=extra_env)
    after = state.clock()
    res["work_dir"] = str(work)
    res["work_dir_bytes"] = apparent_bytes(work)
    res["harness_seconds"] = after - before
    return res


def corrected_seconds(state: RunState, seconds: float) -> float:
    if state.overhead_s <= 0:
        return seconds
    return max(0.0, seconds - state.overhead_s)


def stage_controls(state: RunState) -> dict:
    """The planted sleep, the empty run, and the statement of units and scale."""
    started = state.clock()
    guard_before_stage(state, "controls", SLEEP_CONTROL_S + UNIT_FLOOR_S["endpoints"])
    out = {}

    sleep_started = state.clock()
    res = timed_call(state, "sleep60",
                     state.tool_command("sleep") + [str(int(SLEEP_CONTROL_S))],
                     SLEEP_CONTROL_S + 120, "controls")
    sleep_finished = state.clock()
    measured = res.get("harness_seconds")
    error = abs(measured - SLEEP_CONTROL_S) / SLEEP_CONTROL_S if measured else None
    add_row(state, "controls",
            {"control": "planted_sleep", "planted_s": SLEEP_CONTROL_S,
             "measured_s": measured, "relative_error": error,
             "rc": res.get("rc"), "timed_out": res.get("timed_out")})
    sleep_ok = bool(res.get("ok")) and error is not None \
        and error <= SLEEP_CONTROL_TOLERANCE
    state.sleep_ok = sleep_ok
    if not sleep_ok:
        state.void_run(
            f"the planted {int(SLEEP_CONTROL_S)} s sleep read back as "
            f"{measured:.3f} s, an error of "
            f"{(error if error is not None else float('nan')):.4f}")
    write_record(
        state, f"control-sleep_tag-{TAG}.json", kind="control_sleep",
        cell={"stage": "controls", "control": "planted_sleep", "tag": TAG},
        inputs=record_inputs(state, state.outdir / f"rows_controls_tag-{TAG}.jsonl"),
        metric="relative error of a planted 60 s sleep timed by the run's own harness",
        values={"planted_s": SLEEP_CONTROL_S, "measured_s": measured,
                "relative_error": error, "unit": "seconds"},
        threshold={"max_relative_error": SLEEP_CONTROL_TOLERANCE},
        decision_rule=("relative error at most 0.05 -> PASS and the timings may "
                       "be trusted; otherwise FAIL, every timing in this run is "
                       "invalid, and the run stops"),
        decision="PASS" if sleep_ok else "FAIL",
        labels=labels_for_record(state, sleep_started, sleep_finished))
    out["sleep"] = {"measured_s": measured, "relative_error": error, "ok": sleep_ok}
    if not sleep_ok:
        raise HarnessFailure(
            "the planted sleep check failed; the timing harness is not trustworthy",
            f"measured {measured} s against {SLEEP_CONTROL_S} s",
            kind="sleep_check")

    empty_started = state.clock()
    res = timed_call(state, "empty_run", ["true"], 60, "controls")
    empty_finished = state.clock()
    empty_s = res.get("harness_seconds")
    empty_bytes = res.get("work_dir_bytes", 0)
    add_row(state, "controls", {"control": "empty_run", "measured_s": empty_s,
                                "work_dir_bytes": empty_bytes,
                                "rc": res.get("rc")})
    labels_extra = []
    if empty_s is not None and empty_s >= EMPTY_RUN_MAX_S:
        state.overhead_s = empty_s
        labels_extra.append(LABEL_OVERHEAD_SUBTRACTED)
    if empty_bytes >= EMPTY_RUN_MAX_BYTES:
        state.overhead_bytes = empty_bytes
        if LABEL_OVERHEAD_SUBTRACTED not in labels_extra:
            labels_extra.append(LABEL_OVERHEAD_SUBTRACTED)
    state.overhead_labels = labels_extra
    empty_ok = (empty_s is not None and empty_s < EMPTY_RUN_MAX_S
                and empty_bytes < EMPTY_RUN_MAX_BYTES)
    write_record(
        state, f"control-empty-run_tag-{TAG}.json", kind="control_empty_run",
        cell={"stage": "controls", "control": "empty_run", "tag": TAG},
        inputs=record_inputs(state, state.outdir / f"rows_controls_tag-{TAG}.jsonl"),
        metric="wall-clock seconds and bytes written by the harness around a "
               "command that does nothing",
        values={"measured_s": empty_s, "work_dir_bytes": empty_bytes,
                "unit": "seconds and bytes",
                "overhead_subtracted_s": state.overhead_s,
                "overhead_subtracted_bytes": state.overhead_bytes},
        threshold={"max_seconds": EMPTY_RUN_MAX_S, "max_bytes": EMPTY_RUN_MAX_BYTES},
        decision_rule=("under 2 s and under 1 MiB -> PASS and nothing is "
                       "subtracted; otherwise VOID for this control, and exactly "
                       "that much harness overhead is taken off later values, "
                       "labelled"),
        decision="PASS" if empty_ok else "VOID",
        labels=labels_for_record(state, empty_started, empty_finished),
        extra_notes=labels_extra)
    out["empty_run"] = {"measured_s": empty_s, "bytes": empty_bytes, "ok": empty_ok}

    unit_started = state.clock()
    scale = {
        "af2_hours_from_seconds": {
            "rule": "wall-clock seconds of one prediction call divided by 3,600",
            "worked_example": {"seconds": 1800, "hours": 1800 / 3600.0},
            "unit": CARD["C1"]["unit"]},
        "md_ns_per_day_from_steps": {
            "rule": "steps times the timestep gives simulated femtoseconds; "
                    "divided by the production wall-clock and scaled to 86,400 "
                    "seconds",
            "worked_example": {
                "steps": 250000, "timestep_fs": 2.0, "wallclock_s": 335,
                "ns_per_day": round(ns_per_day_from_wallclock(250000, 2.0, 335), 2)},
            "engine_rate_line_example": "Speed (ns/day) column of the reporter "
                                        "file, read beside the wall-clock figure",
            "unit": CARD["C2"]["unit"]},
        "aux_hours_from_seconds": {
            "rule": "wall-clock seconds of docking, interface analysis and "
                    "writing the call-table row for one pair, divided by 3,600",
            "worked_example": {"seconds": 3600, "hours": 1.0},
            "unit": CARD["C3"]["unit"]},
        "storage_gib_from_bytes": {
            "rule": f"apparent bytes written by one run times {GRID_RUNS} "
                    "divided by 2 to the power 30",
            "worked_example": {
                "bytes_per_run": BYTES_PER_GIB,
                "gib_216_runs": storage_from_bytes(BYTES_PER_GIB)["gib_216_runs"],
                "gib_432_runs": storage_from_bytes(BYTES_PER_GIB)["gib_432_runs"]},
            "unit": CARD["C4"]["unit"]},
        "kind": "worked_examples",
        "raw_values_in": {
            "raw_alphafold_seconds_per_run": f"rows_af2_tag-{TAG}.jsonl",
            "md_engine_rate_lines_with_wallclock_beside_them": f"rows_md_tag-{TAG}.jsonl",
            "raw_bytes_per_artifact": f"rows_storage_tag-{TAG}.jsonl",
            "note": ("this control holds worked examples only; the raw values "
                     "live in the row files named here")},
    }
    atomic_write_json(state.outdir / f"unit_and_scale_tag-{TAG}.json", scale)
    write_record(
        state, f"control-unit-and-scale_tag-{TAG}.json",
        kind="control_unit_and_scale",
        cell={"stage": "controls", "control": "unit_and_scale", "tag": TAG},
        inputs=record_inputs(state),
        metric="the raw units each input is read in, and the arithmetic that "
               "turns raw output into the card's unit",
        values=scale,
        threshold={"required": "stated before any band is compared"},
        decision_rule=("this control decides nothing; it exists so a reader can "
                       "re-derive every later number from raw output"),
        decision="RECORDED",
        labels=labels_for_record(state, unit_started, state.clock()))
    out["unit_and_scale"] = scale
    out["seconds"] = state.clock() - started
    state.stages_done.append("controls")
    return out


# ===========================================================================
# DOCKING
# ===========================================================================


def pose_path_from_row(work: Path, row: dict):
    """Where the tool says its first-ranked pose was written."""
    keys = {k.lower(): k for k in row}
    swarm = row.get(keys.get("swarm", ""), None)
    conformation = None
    for name in ("conformation", "conformationid", "glowworm", "id"):
        if name in keys:
            conformation = row[keys[name]]
            break
    for name in ("pose", "file", "filename", "structure"):
        if name in keys and row[keys[name]]:
            return Path(work) / str(row[keys[name]])
    if swarm is None or conformation is None:
        return None
    return Path(work) / f"swarm_{swarm}" / f"lightdock_{conformation}.pdb"


def write_rank_table_diagnostic(state: RunState, name: str, text: str, work) -> Path:
    shape = rank_table_shape(text)
    work = Path(work)
    try:
        entries = sorted(p.name for p in work.iterdir())
    except OSError as exc:
        entries = ["<could not be listed: %s>" % exc]
    swarm_dirs = sorted(p for p in work.glob("swarm_*") if p.is_dir())
    if swarm_dirs:
        try:
            swarm_entries = sorted(p.name for p in swarm_dirs[0].iterdir())
        except OSError as exc:
            swarm_entries = ["<could not be listed: %s>" % exc]
        swarm_name = swarm_dirs[0].name
    else:
        swarm_entries = []
        swarm_name = "<no swarm_* directory>"
    lines = [
        "rank table diagnostic for %s" % name,
        "written because the table could not be read, or named no pose file",
        "",
        "first 8 raw lines of the table, exactly as written:",
    ]
    lines += ["  %s" % repr(l) for l in shape["raw_lines"][:8]] or ["  <no lines>"]
    lines += [
        "", "data lines: %d" % shape["data_lines"],
        "field counts of the data lines: %s"
        % ", ".join(str(c) for c in shape["field_counts"]),
        "header tokens: %s" % ", ".join(shape["header"]),
        "", "names in the docking working directory (depth 1):",
    ]
    lines += ["  %s" % e for e in entries] or ["  <empty>"]
    lines += ["", "names in %s (depth 1):" % swarm_name]
    lines += ["  %s" % e for e in swarm_entries] or ["  <none>"]
    path = state.outdir / f"rank_table_diagnostic_{name}_tag-{TAG}.txt"
    atomic_write_text(path, "\n".join(lines) + "\n")
    return path


def write_frame_diagnostic(state: RunState, name: str, frame: dict, pose_text: str) -> Path:
    path = state.outdir / f"anchor_frame_diagnostic_tag-{TAG}.txt"
    lines = [
        "frame guard diagnostic for %s" % name,
        "the pose was not scored; this is broken infrastructure, never an "
        "anchor miss",
        "",
        "frame shift, matched atoms and residual:",
        "  %s" % json.dumps(frame, sort_keys=True, default=str),
        "",
        "the raw pose is kept beside this file",
    ]
    if path.exists():
        old = Path(path).read_text()
        atomic_write_text(path, old + "\n" + "\n".join(lines) + "\n")
    else:
        atomic_write_text(path, "\n".join(lines) + "\n")
    return path


def run_docking(state: RunState, name: str, receptor_pdb: Path, ligand_pdb: Path,
                work: Path, limit_s: float, cores: int, stage: str) -> dict:
    """Dock one receptor onto one capsid and return the tool's own best pose."""
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    local_receptor = work / Path(receptor_pdb).name
    local_ligand = work / Path(ligand_pdb).name
    for src, dest in ((receptor_pdb, local_receptor), (ligand_pdb, local_ligand)):
        if Path(src).resolve() != dest.resolve():
            shutil.copyfile(str(src), str(dest))
    receptor_pdb, ligand_pdb = local_receptor, local_ligand
    swarms, glowworms, steps = DOCKING_SWARMS, DOCKING_GLOWWORMS, DOCKING_STEPS
    started = state.clock()
    budget = limit_s
    order = []

    def call(cmd, step_name, cwd=None):
        nonlocal budget
        order.append(step_name)
        left = inner_tool_limit_s(state, budget)
        res = state.runner.capture(cmd, limit_s=max(1.0, left), stage=stage,
                                   name=f"{name}_{step_name}", cwd=cwd or work)
        budget -= res.get("seconds", 0.0)
        return res

    setup = call(
        state.tool_command("lightdock3_setup.py")
        + [str(receptor_pdb), str(ligand_pdb),
           "-s", str(swarms), "-g", str(glowworms)]
        + list(DOCKING_SETUP_FLAGS), "setup")
    if setup.get("timed_out"):
        raise GuardStop("the docking setup ran past the time allowed for it",
                        stage=stage, detail=setup.get("log", ""))
    if not setup.get("ok"):
        raise HarnessFailure("the docking setup failed",
                             f"exit {setup.get('rc')}, see {setup.get('log')}")
    setup_errors = [line.strip() for line in setup.get("stdout", "").splitlines()
                    if "ERROR" in line]
    if setup_errors:
        raise HarnessFailure(
            "the docking setup failed",
            f"exit {setup.get('rc')} with an error line in its output: "
            f"{setup_errors[0]}; see {setup.get('log')}")

    sim = call(state.tool_command("lightdock3.py")
               + ["setup.json", str(steps), "-c", str(max(1, cores))], "simulate")
    if sim.get("timed_out"):
        raise GuardStop("the docking run ran past the time allowed for it",
                        stage=stage, detail=sim.get("log", ""))
    if not sim.get("ok"):
        raise HarnessFailure("the docking run failed",
                             f"exit {sim.get('rc')}, see {sim.get('log')}")

    swarm_dirs = sorted(p for p in work.glob("swarm_*") if p.is_dir())
    if not swarm_dirs:
        raise HarnessFailure(
            "the docking run left no swarm directory to build poses from",
            f"nothing matching swarm_* in {work}")
    for swarm_dir in swarm_dirs:
        gen = call(state.tool_command("lgd_generate_conformations.py")
                   + [str(receptor_pdb), str(ligand_pdb),
                      f"gso_{steps}.out", str(glowworms)],
                   "generate_conformations", cwd=swarm_dir)
        if gen.get("timed_out"):
            raise GuardStop("building the docked pose structures ran past the "
                            "time allowed for it", stage=stage,
                            detail=gen.get("log", ""))
        if not gen.get("ok"):
            raise HarnessFailure("building the docked pose structures failed",
                                 f"exit {gen.get('rc')}, see {gen.get('log')}")

    rank = call(state.tool_command("lgd_rank.py") + [str(swarms), str(steps)], "rank")
    if rank.get("timed_out"):
        raise GuardStop("ranking the docked poses ran past the time allowed",
                        stage=stage, detail=rank.get("log", ""))
    if not rank.get("ok"):
        raise HarnessFailure("ranking the docked poses failed",
                             f"exit {rank.get('rc')}, see {rank.get('log')}")

    table_path = None
    for candidate in sorted(work.glob("rank_by_scoring.list")) + sorted(
            work.glob("rank_*.list")):
        table_path = candidate
        break
    if table_path is None:
        raise HarnessFailure("the docking run left no ranked list of poses",
                             f"nothing matching rank_*.list in {work}")
    kept = state.outdir / f"rank_table_{name}_tag-{TAG}.list"
    shutil.copyfile(str(table_path), str(kept))
    table_text = table_path.read_text()
    shape = rank_table_shape(table_text)
    counts_text = ", ".join(str(c) for c in shape["field_counts"]) or "none"
    try:
        parsed = parse_rank_table(kept)
        top = parsed["top"]
        n_rows = parsed["n_rows"]
        columns = parsed["columns"]
    except ParseError as exc:
        diagnostic = write_rank_table_diagnostic(state, name, table_text, work)
        raise HarnessFailure(
            "the docking rank table could not be read",
            f"{exc}; field counts of the data lines: {counts_text}; "
            f"{first_raw_lines(table_text)}; raw table kept at {kept}; "
            f"diagnostic at {diagnostic}")
    pose = pose_path_from_row(work, top)
    if pose is None or not Path(pose).exists():
        diagnostic = write_rank_table_diagnostic(state, name, table_text, work)
        raise HarnessFailure(
            "the docking rank table names no pose file that exists",
            f"top row {top}; field counts of the data lines: {counts_text}; "
            f"{first_raw_lines(table_text)}; raw table kept at {kept}; "
            f"diagnostic at {diagnostic}")
    pose_kept = state.outdir / f"pose_{name}_tag-{TAG}.pdb"
    shutil.copyfile(str(pose), str(pose_kept))
    seconds = state.clock() - started
    return {
        "name": name, "seconds": seconds, "cores": cores,
        "rank_table": str(kept), "rank_rows": n_rows, "top_row": top,
        "pose_path": str(pose_kept), "pose_text": Path(pose_kept).read_text(),
        "call_order": order,
        "parameters": {"swarms": swarms, "glowworms": glowworms, "steps": steps,
                       "cores": cores, "setup_flags": list(DOCKING_SETUP_FLAGS),
                       "restrained_to_the_published_interface": False,
                       "rank_table_columns": columns}}


def split_published_structure(state: RunState, pdb_text: str) -> dict:
    atoms = read_pdb_atoms(pdb_text)
    chains = chain_residues(atoms)
    roles = pick_roles(chains)
    chain_map = {c: "capsid" for c in roles["capsid_chains"]}
    chain_map[roles["receptor_chain"]] = "receptor"
    native = map_chain_roles(atoms, chain_map)
    capsid_atoms = [a for a in atoms if chain_map.get(a["chain"]) == "capsid"]
    receptor_atoms = [a for a in atoms if chain_map.get(a["chain"]) == "receptor"]
    cap_path = state.workdir / "anchor_capsid.pdb"
    rec_path = state.workdir / "anchor_receptor.pdb"
    atomic_write_text(cap_path, write_pdb(capsid_atoms))
    atomic_write_text(rec_path, write_pdb(receptor_atoms))
    return {"chain_map": chain_map, "native_role_atoms": native,
            "capsid_pdb": cap_path, "receptor_pdb": rec_path,
            "receptor_chain": roles["receptor_chain"],
            "capsid_chains": roles["capsid_chains"]}


def score_pose_against_native(native_role_atoms: list, pose_text: str,
                              capsid_atoms: list) -> dict:
    """Compare one docked pose with the published placement.

    The pose's chains are renamed to the parts they play, the pose is moved
    into the published frame by the capsid match, and the frame guard refuses
    the pose when that match is not rigid enough.
    """
    pose_atoms = read_pdb_atoms(pose_text)
    chains_in_pose = sorted({a["chain"] for a in pose_atoms})
    capsid_ids = sorted({a["chain"] for a in capsid_atoms})
    pose_map = {}
    for c in chains_in_pose:
        pose_map[c] = "capsid" if c in capsid_ids else "receptor"
    if "receptor" not in set(pose_map.values()):
        raise HarnessFailure("the docked pose holds no receptor-role chain",
                             f"chains in the pose: {chains_in_pose}")
    pose_roles = map_chain_roles(pose_atoms, pose_map)
    pose_capsid = [a for a in pose_roles if a["role"] == "capsid"]
    native_capsid = [a for a in native_role_atoms if a["role"] == "capsid"]
    shift = pose_frame_shift(native_capsid, pose_capsid)
    frame_guard(shift)
    pose_roles = [dict(a, x=a["x"] + shift["dx"], y=a["y"] + shift["dy"],
                       z=a["z"] + shift["dz"]) for a in pose_roles]
    reference_contacts = contact_pairs_by_index(native_role_atoms)
    pose_contacts = contact_pairs_by_index(pose_roles)
    overlap = contact_overlap(reference_contacts, pose_contacts)
    iface = interface_backbone_rmsd(native_role_atoms, pose_roles)
    return {"overlap": overlap, "interface_backbone_rmsd_a": iface,
            "n_reference_contacts": len(reference_contacts),
            "n_pose_contacts": len(pose_contacts),
            "call": "bind" if (overlap >= ANCHOR_OVERLAP_MIN
                               or iface <= ANCHOR_IFACE_RMSD_MAX) else "no-bind",
            "frame": shift, "pose_role_atoms": pose_roles}


# ===========================================================================
# WRITING ONE INPUT'S RECORD
# ===========================================================================


def calibration_context(state: RunState) -> dict:
    if state.gpu_name is None:
        try:
            collect_labels(state)
        except Exception:
            pass
    return {
        "sleep_ok": bool(state.sleep_ok),
        "gpu_visible": bool(state.gpu_visible),
        "gpu_name": state.gpu_name,
        "gpu_is_a100": bool(state.gpu_is_a100),
        "stages_before_ok": not state.stopped,
        "anchor_docking_parameters": ((state.anchor or {}).get("verdict", {})
                                      .get("docking_parameters")
                                      or (state.anchor or {}).get("docking_parameters")
                                      or {}),
    }


def emit_input_record(state: RunState, cid: str, measured, *, n, rows_arm,
                      start_epoch, end_epoch, extra_values=None, extra_notes=None,
                      void_reason=None, labels_extra=None, stop_kind=None,
                      rows=None, calibration=None):
    """Write the record for one of the four inputs, with its own checks."""
    spec = CARD[cid]
    notes = [LABEL_STAND_IN, LABEL_ONE_GPU] + list(extra_notes or [])
    if cid == "C1":
        notes.append(LABEL_NO_MSA)
    if cid == "C3":
        notes.append(LABEL_AUX_READING)
    if cid == "C4":
        notes.append(LABEL_STORAGE)

    if rows is None:
        rows = load_rows(state, rows_arm) if rows_arm else []
    if calibration is None:
        checker = CALIBRATION_CHECKS[cid]
        calibration = checker(rows, calibration_context(state))
    state.calibration[cid] = calibration
    calibration_valid = bool(calibration.get("calibration_valid"))

    if void_reason:
        outcome = {"decision": "VOID", "marginal": False, "reason": void_reason}
    elif not calibration_valid:
        failed = ", ".join(sorted(calibration.get("null_reasons") or {}))
        outcome = {"decision": "VOID", "marginal": False,
                   "reason": f"calibration checks failed: {failed}"}
    else:
        outcome = decide_band(measured, spec["band"])

    values = {
        "measured": measured,
        "unit": spec["unit"],
        "card_value": spec["card_value"],
        "band": spec["band"],
        "basis": spec["basis"],
        "n": n,
        "marginal": outcome["marginal"],
        "void_reason": outcome["reason"] if outcome["decision"] == "VOID" else None,
        "voided_by": None,
        "calibration_valid": calibration_valid,
        "calibration_checks": calibration.get("checks"),
        "null_reasons": dict(calibration.get("null_reasons") or {}),
    }
    if outcome["decision"] == "VOID":
        why = str(void_reason or outcome["reason"] or "no measured value")
        values["voided_by"] = why
        if measured is None:
            values["null_reasons"]["measured"] = why
    if cid == "C1":
        gate = gate_on_c1(measured, outcome["decision"], outcome["marginal"])
        if gate["gate_pass"] is None:
            reason = void_reason or outcome["reason"] or "no measured value"
            gate["gate"] = f"not evaluated: C1 VOID ({reason})"
        values.update(gate)
    elif cid in ("C2", "C3"):
        values["gate"] = GATE_NOT_APPLICABLE
    values.update(extra_values or {})

    rows_file = state.outdir / f"rows_{rows_arm}_tag-{TAG}.jsonl" if rows_arm else None
    write_record(
        state, f"endpoint-{cid}_tag-{TAG}.json", kind=cid,
        cell={"stage": "endpoints", "input": cid, "key": spec["key"], "tag": TAG},
        inputs=record_inputs(state, rows_file, pair_evidence=True),
        metric=f"{spec['key']} measured on the stand-in protocol, in {spec['unit']}",
        values=values,
        threshold={"band": spec["band"], "card_value": spec["card_value"],
                   "marginal_fraction": MARGINAL_FRACTION},
        decision_rule=(
            f"inside {spec['band']} -> PASS; outside -> FAIL; within 10 percent "
            "of either edge -> VOID and marginal; a record whose own calibration "
            "checks fail is VOID with the raw value kept; below the minimum "
            "sample, on a wrong graphics processor, or left unmeasured by a stop "
            "-> VOID with the raw rows kept"),
        decision=outcome["decision"],
        labels=labels_for_record(state, start_epoch, end_epoch, labels_extra),
        extra_notes=notes)

    # Exactly one status word per input, from the one table. There is no
    # void-by-anchor-miss word: after a miss the inputs keep their own standing.
    if state.failure_kind and not values["calibration_valid"] \
            and (void_reason and str(void_reason).startswith("the run ended")):
        state.set_void_by_failure(cid, state.failure_kind,
                                  state.run_valid_voided_by or state.failure_kind,
                                  calibration_valid)
    elif void_reason and LABEL_UNMEASURED in str(void_reason):
        state.set_unmeasured(cid, stop_kind or state.last_stop_kind(),
                             calibration_valid=False)
    elif void_reason and str(void_reason).startswith("the run ended on broken"):
        state.set_void_by_failure(cid, state.failure_kind or "failure",
                                  state.run_valid_voided_by or str(void_reason),
                                  calibration_valid)
    elif void_reason or outcome["decision"] == "VOID":
        state.set_decided(cid, "VOID", void_reason or outcome["reason"],
                          calibration_valid)
    else:
        state.set_decided(cid, outcome["decision"], None, calibration_valid)
    return outcome


# ===========================================================================
# STAGE: ANCHOR (redocking, serial then parallel, then the diagnostics)
# ===========================================================================


def _translate(atoms, dx, dy, dz):
    return [dict(a, x=a["x"] + dx, y=a["y"] + dy, z=a["z"] + dz) for a in atoms]


def _rotation_matrix(axis, angle):
    x, y, z = axis
    n = math.sqrt(x * x + y * y + z * z) or 1.0
    x, y, z = x / n, y / n, z / n
    c = math.cos(angle)
    s = math.sin(angle)
    t = 1 - c
    return [[t * x * x + c, t * x * y - s * z, t * x * z + s * y],
            [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
            [t * x * z - s * y, t * y * z + s * x, t * z * z + c]]


def _rotate(atoms, matrix):
    out = []
    for a in atoms:
        x = (matrix[0][0] * a["x"] + matrix[0][1] * a["y"] + matrix[0][2] * a["z"])
        y = (matrix[1][0] * a["x"] + matrix[1][1] * a["y"] + matrix[1][2] * a["z"])
        z = (matrix[2][0] * a["x"] + matrix[2][1] * a["y"] + matrix[2][2] * a["z"])
        out.append(dict(a, x=x, y=y, z=z))
    return out


def anchor_diagnostics(state: RunState, split: dict, scored: dict,
                       reference_text: str, pose_text: str, allowance_left: float):
    """The checks behind the anchor's own scoring. They never move the verdict.

    When less than sixty seconds of the anchor's allowance are left they are
    skipped, with that fact recorded, rather than eating the measuring time.
    """
    if allowance_left < 60:
        return {"skipped": True,
                "note": "fewer than 60 s of the anchor allowance remained",
                LABEL_DIAGNOSTICS: True}
    diag = {}
    native = split["native_role_atoms"]
    native_capsid = [a for a in native if a["role"] == "capsid"]

    def run_one(name, fn):
        try:
            entry = fn()
            entry["ok"] = bool(entry.get("ok", True))
            return entry
        except Exception as exc:
            return {"ok": False, "diagnostic_failed": True,
                    "null_reasons": {"error": str(exc)},
                    "note": LABEL_DIAGNOSTICS}

    def self_score():
        again = score_pose_against_native(native, reference_text, native_capsid)
        ok = (abs(again["overlap"] - 1.0) < 1e-6
              and again["interface_backbone_rmsd_a"] < 1e-6
              and again["n_reference_contacts"] == again["n_pose_contacts"])
        return {"ok": ok, "overlap": again["overlap"],
                "interface_backbone_rmsd_a": again["interface_backbone_rmsd_a"],
                "reference_contacts_equal_pose_contacts":
                    again["n_reference_contacts"] == again["n_pose_contacts"]}

    def translated_copy():
        moved = _translate(native, 12.5, -30.0, 20.0)
        moved_text = write_pdb(moved)
        again = score_pose_against_native(native, moved_text, native_capsid)
        shift_len = math.sqrt(12.5 ** 2 + 30.0 ** 2 + 20.0 ** 2)
        ok = (shift_len <= 50.0 and abs(again["overlap"] - 1.0) < 1e-6
              and again["interface_backbone_rmsd_a"] < 1e-6)
        return {"ok": ok, "translation_a": [12.5, -30.0, 20.0],
                "translation_length_a": shift_len, "overlap": again["overlap"],
                "interface_backbone_rmsd_a": again["interface_backbone_rmsd_a"]}

    def rotated_copy():
        matrix = _rotation_matrix((1.0, 1.0, 0.0), math.radians(35.0))
        moved = _translate(_rotate(native, matrix), 5.0, 5.0, 5.0)
        moved_capsid = [a for a in moved if a["role"] == "capsid"]
        try:
            shift = pose_frame_shift(native_capsid, moved_capsid)
            frame_guard(shift)
        except FrameGuardReject as rej:
            return {"ok": True, "frame_guard_rejected": True,
                    "residual": rej.frame.get("residual_rmsd_a")}
        return {"ok": False, "frame_guard_rejected": False,
                "residual": None, "note": "the guard accepted a rotated copy"}

    def pairing():
        pose_atoms = read_pdb_atoms(pose_text)
        capsid_ids = {a["chain"] for a in native_capsid}
        pose_capsid = [a for a in pose_atoms if a["chain"] in capsid_ids]
        pose_receptor = [a for a in pose_atoms if a["chain"] not in capsid_ids]
        frame = scored.get("frame") or {}
        ref_capsid_expected = len(heavy_atoms(native_capsid))
        ref_receptor_expected = len(heavy_atoms(
            [a for a in native if a["role"] == "receptor"]))
        iface = interface_receptor_residues(native)
        ref_bb = _backbone_index(native, iface)
        moved = [dict(a, x=a["x"] + frame.get("dx", 0.0),
                      y=a["y"] + frame.get("dy", 0.0),
                      z=a["z"] + frame.get("dz", 0.0)) for a in pose_atoms]
        pose_roles = [dict(a, role=("capsid" if a["chain"] in capsid_ids
                                    else "receptor")) for a in moved]
        pose_bb = _backbone_index(pose_roles, iface)
        shared_bb = len(set(ref_bb) & set(pose_bb))
        return {"ok": True,
                "capsid_atoms_matched": frame.get("matched_atoms"),
                "capsid_atoms_expected": frame.get("expected_atoms")
                or ref_capsid_expected,
                "receptor_atoms_paired": len(heavy_atoms(pose_receptor)),
                "receptor_atoms_expected": ref_receptor_expected,
                "interface_backbone_atoms_paired": shared_bb,
                "interface_backbone_atoms_expected": len(ref_bb),
                "reference_contacts": scored.get("n_reference_contacts"),
                "pose_contacts": scored.get("n_pose_contacts"),
                "shared_contacts": (None if scored.get("overlap") is None else
                                    int(round(scored.get("overlap", 0.0)
                                              * (scored.get("n_reference_contacts")
                                                 or 0))))}

    def independent():
        indep = independent_anchor_score(reference_text, pose_text)
        agree = scorer_agreement(
            {"overlap": scored.get("overlap"),
             "interface_backbone_rmsd_a": scored.get("interface_backbone_rmsd_a")},
            indep)
        return {"ok": agree["ok"], **agree}

    diag["self_score"] = run_one("self_score", self_score)
    diag["translated_copy"] = run_one("translated_copy", translated_copy)
    diag["rotated_copy"] = run_one("rotated_copy", rotated_copy)
    diag["pairing"] = run_one("pairing", pairing)
    diag["independent_scoring"] = run_one("independent_scoring", independent)
    for entry in diag.values():
        if isinstance(entry, dict) and not entry.get("ok", True):
            entry["diagnostic_failed"] = True
            entry.setdefault("null_reasons", {})
            entry["null_reasons"].setdefault(
                "why", "this diagnostic did not hold")
            entry["note"] = LABEL_DIAGNOSTICS
    diag["note"] = LABEL_DIAGNOSTICS
    return diag


def stage_anchor(state: RunState) -> dict:
    """Redock the receptor onto the capsid and check it lands where it should."""
    started = state.clock()
    estimate = state.unit_estimate("anchor_serial") + state.unit_estimate("anchor_parallel")
    allowance = guard_before_stage(state, "anchor", estimate)
    pdb_path = state.input_path(f"{PDB_ENTRY}_tag-{TAG}.pdb") \
        or state.input_path(f"{PDB_ENTRY}.pdb")
    if pdb_path is None:
        raise HarnessFailure("the published structure is missing before the anchor",
                             str(state.datadir / f"{PDB_ENTRY}.pdb"))
    reference_text = Path(pdb_path).read_text()
    split = split_published_structure(state, reference_text)
    capsid_atoms = [a for a in read_pdb_atoms(reference_text)
                    if split["chain_map"].get(a["chain"]) == "capsid"]

    results = {}
    for name, cores, kind in (("serial", 1, "anchor_serial"),
                              ("parallel", 4, "anchor_parallel")):
        guard_before_unit(state, "anchor", kind, allowance - (state.clock() - started))
        unit_started = state.clock()
        dock = run_docking(
            state, f"anchor_{name}", split["capsid_pdb"], split["receptor_pdb"],
            state.workdir / f"anchor_{name}",
            limit_s=min(allowance - (state.clock() - started),
                        PER_PAIR_DOCKING_CEILING_S),
            cores=cores, stage="anchor")
        state.note_unit(kind, state.clock() - unit_started)
        try:
            scored = score_pose_against_native(
                split["native_role_atoms"], dock["pose_text"], capsid_atoms)
        except FrameGuardReject as rej:
            kept = state.outdir / f"pose_{dock['name']}_tag-{TAG}.pdb"
            atomic_write_text(kept, dock["pose_text"])
            diagnostic = write_frame_diagnostic(
                state, dock["name"], rej.frame, dock["pose_text"])
            raise HarnessFailure(
                "the frame guard refused the docked pose",
                f"{rej.reason}; frame {rej.frame}; raw pose kept at {kept}; "
                f"diagnostic at {diagnostic}", kind="anchor_frame")
        results[name] = {"dock": dock, "scored": scored}
        add_row(state, "anchor", {
            "which": name, "cores": cores, "seconds": dock["seconds"],
            "overlap": scored["overlap"],
            "interface_backbone_rmsd_a": scored["interface_backbone_rmsd_a"],
            "n_reference_contacts": scored["n_reference_contacts"],
            "call": scored["call"], "rank_table": dock["rank_table"],
            "pose_path": dock["pose_path"], "top_row": dock["top_row"],
            "frame": scored["frame"]})

    serial = results["serial"]["scored"]
    parallel = results["parallel"]["scored"]
    sp_rmsd = whole_chain_rmsd(serial["pose_role_atoms"], parallel["pose_role_atoms"])
    calls_identical = serial["call"] == parallel["call"]
    verdict = anchor_decision(serial["overlap"], serial["interface_backbone_rmsd_a"],
                              sp_rmsd, calls_identical)
    verdict["docking_parameters"] = results["serial"]["dock"]["parameters"]
    finished = state.clock()

    if verdict["decision"] != "PASS":
        state.void_run(
            "the anchor redocking missed its tolerance against the published "
            f"placement: overlap {verdict['overlap']:.4f}, interface backbone "
            f"RMSD {verdict['interface_backbone_rmsd_a']:.4f} A, "
            f"serial-versus-parallel RMSD {sp_rmsd:.4f} A, calls identical "
            f"{calls_identical}")

    diagnostics = anchor_diagnostics(
        state, split, serial, reference_text,
        results["serial"]["dock"]["pose_text"],
        allowance - (state.clock() - started))

    write_record(
        state, f"endpoint-anchor_tag-{TAG}.json", kind="anchor",
        cell={"stage": "anchor", "endpoint": "anchor", "tag": TAG},
        inputs=record_inputs(state, state.outdir / f"rows_anchor_tag-{TAG}.jsonl",
                             extra_paths=[pdb_path]),
        metric=("contact overlap with the published complex at 4.5 angstrom, or "
                "interface backbone displacement, with serial and parallel agreement"),
        values={
            "measured": verdict["overlap"],
            "published": (f"AAVR-PKD2 bound to the AAV2 spike region adjacent to "
                          f"the icosahedral three-fold axis (PDB {PDB_ENTRY})"),
            "tolerance": {
                "min_contact_overlap": ANCHOR_OVERLAP_MIN,
                "max_interface_backbone_rmsd_a": ANCHOR_IFACE_RMSD_MAX,
                "max_serial_parallel_rmsd_a": ANCHOR_SERIAL_PARALLEL_RMSD_MAX,
                "calls_must_be_identical": True},
            "contact_overlap": verdict["overlap"],
            "interface_backbone_rmsd_a": verdict["interface_backbone_rmsd_a"],
            "serial_parallel_rmsd_a": sp_rmsd,
            "serial_call": serial["call"], "parallel_call": parallel["call"],
            "calls_identical": calls_identical,
            "unit": "fraction of published contacts, and angstrom",
            "independent_code": ANCHOR_INDEPENDENT_CODE,
            "docking_order": DOCKING_ORDER,
            "docking_order_as_called": results["serial"]["dock"]["call_order"],
            "docking_order_source": (
                "the on-box execution contract states no order for the docking "
                "commands, so the order is prepare, search, build the poses, rank"),
            "docking_parameters": results["serial"]["dock"]["parameters"],
            "docking_parameters_same_for_pairs": True,
            "frame": serial.get("frame"),
            "diagnostics": diagnostics,
            "calibration_valid": True,
            "calibration_checks": [
                {"check": "both_poses_obtained_and_compared", "result": True,
                 "value": True}],
        },
        threshold={"min_contact_overlap": ANCHOR_OVERLAP_MIN,
                   "max_interface_backbone_rmsd_a": ANCHOR_IFACE_RMSD_MAX,
                   "max_serial_parallel_rmsd_a": ANCHOR_SERIAL_PARALLEL_RMSD_MAX},
        decision_rule=("PASS when the pose reproduces the published placement "
                       "(contact overlap at least 0.50 or interface backbone RMSD "
                       "at most 5.0 angstrom) AND serial and parallel agree "
                       "(top-pose RMSD at most 2.0 angstrom with identical bind or "
                       "no-bind calls); otherwise FAIL; the run continues either "
                       "way and the exit table decides the code"),
        decision=verdict["decision"],
        labels=labels_for_record(state, started, finished),
        extra_notes=[LABEL_SERIAL_PARALLEL_WHOLE_CHAIN])
    state.anchor = {"verdict": verdict,
                    "serial_parallel_rmsd_a": sp_rmsd,
                    "calls_identical": calls_identical,
                    "docking_parameters": results["serial"]["dock"]["parameters"]}
    if verdict["decision"] != "PASS":
        # The miss is recorded and the run goes on: the four inputs are still
        # measured, and the exit table decides the code at the end.
        state.anchor_missed = (
            f"the anchor redocking missed its tolerance: overlap "
            f"{verdict['overlap']:.4f}, interface backbone RMSD "
            f"{verdict['interface_backbone_rmsd_a']:.4f} A")
    else:
        state.stages_done.append("anchor")
    return {"verdict": verdict, "missed": bool(state.anchor_missed)}


# ===========================================================================
# STAGE: PER-PAIR DOCKING AND INTERFACE ANALYSIS (INPUT C3)
# ===========================================================================


def threefold_axis_distance(points: list) -> float:
    if not points:
        return float("nan")
    n = float(len(points))
    centre = (sum(p[0] for p in points) / n, sum(p[1] for p in points) / n,
              sum(p[2] for p in points) / n)
    root3 = math.sqrt(3.0)
    best = None
    for sx in (1.0, -1.0):
        for sy in (1.0, -1.0):
            axis = (sx / root3, sy / root3, 1.0 / root3)
            dot = sum(c * a for c, a in zip(centre, axis))
            perp = [c - dot * a for c, a in zip(centre, axis)]
            d = math.sqrt(sum(v * v for v in perp))
            best = d if best is None else min(best, d)
    return best


def interface_analysis(native_role_atoms: list, pose_role_atoms: list) -> dict:
    contacts = contact_pairs_by_index(pose_role_atoms)
    residues = sorted({r for (_c, r) in contacts})
    coords = [(a["x"], a["y"], a["z"]) for a in pose_role_atoms
              if a["role"] == "receptor" and a["resseq"] in set(residues)]
    distance = threefold_axis_distance(coords)
    site_class = "spike" if distance <= 25.0 else "floor"
    reference = contact_pairs_by_index(native_role_atoms)
    return {"n_contacts": len(contacts), "interface_residues": residues,
            "n_interface_residues": len(residues),
            "distance_to_nearest_threefold_axis_a": distance,
            "site_class": site_class,
            "contact_overlap_with_published": contact_overlap(reference, contacts),
            "call": "bind" if contacts else "no-bind"}


def stage_aux(state: RunState) -> dict:
    """Time docking, interface analysis and the call-table row, per pair."""
    started = state.clock()
    allowance = guard_before_stage(state, "aux", state.unit_estimate("docking_pair"))
    pdb_path = state.input_path(f"{PDB_ENTRY}_tag-{TAG}.pdb") \
        or state.input_path(f"{PDB_ENTRY}.pdb")
    if pdb_path is None:
        raise HarnessFailure("the published structure is missing before the "
                             "per-pair docking", "no 6IHB file in the inputs")
    split = split_published_structure(state, Path(pdb_path).read_text())
    pairs = load_pairs(state)
    capsid_for_frame = [a for a in split["native_role_atoms"] if a["role"] == "capsid"]
    call_table = []
    finished_pairs = []
    stopped = None

    for pair in pairs:
        left = allowance - (state.clock() - started)
        try:
            guard_before_unit(state, "aux", "docking_pair", left)
        except GuardStop as stop:
            stopped = stop
            break
        pair_cap = min(PER_PAIR_DOCKING_CEILING_S, left)
        unit_started = state.clock()
        work = state.workdir / f"aux_{pair['pair']}"
        capsid_ids = [c for c, r in pair["chain_map"].items() if r == "capsid"]
        capsid_atoms = [a for a in pair["atoms"] if a["chain"] in capsid_ids]
        receptor_atoms = [a for a in pair["atoms"]
                          if a["chain"] == pair["receptor_chain"]]
        work.mkdir(parents=True, exist_ok=True)
        cap_pdb = work / "capsid.pdb"
        rec_pdb = work / "receptor.pdb"
        atomic_write_text(cap_pdb, write_pdb(capsid_atoms))
        atomic_write_text(rec_pdb, write_pdb(receptor_atoms))
        pair_role_atoms = [
            dict(a, role=("capsid" if a["chain"] in capsid_ids else "receptor"))
            for a in pair["atoms"]]
        truncated = False
        try:
            dock = run_docking(state, f"aux_{pair['pair']}", cap_pdb, rec_pdb, work,
                               limit_s=pair_cap, cores=4, stage="aux")
        except GuardStop as stop:
            truncated = True
            add_row(state, "aux", {
                "pair": pair["pair"], "seconds": state.clock() - unit_started,
                "truncated": True, "incomplete": True, "why": stop.reason,
                "frame_interval_ps": None})
            stopped = stop
            continue
        try:
            scored = score_pose_against_native(
                pair_role_atoms, dock["pose_text"], capsid_atoms)
        except FrameGuardReject as rej:
            diagnostic = write_frame_diagnostic(
                state, f"aux_{pair['pair']}", rej.frame, dock["pose_text"])
            raise HarnessFailure(
                "the frame guard refused the docked pose of a pair",
                f"{rej.reason}; diagnostic at {diagnostic}", kind="anchor_frame")
        analysis = interface_analysis(split["native_role_atoms"],
                                      scored["pose_role_atoms"])
        row_for_table = {
            "pair": pair["pair"], "capsid_slot": pair["capsid_slot"],
            "call": analysis["call"], "score": dock["top_row"],
            "n_interface_residues": analysis["n_interface_residues"],
            "interface_residues": analysis["interface_residues"],
            "distance_to_nearest_threefold_axis_a":
                analysis["distance_to_nearest_threefold_axis_a"],
            "site_class": analysis["site_class"]}
        call_table.append(row_for_table)
        atomic_write_json(state.outdir / f"call_table_tag-{TAG}.json", call_table)
        seconds = state.clock() - unit_started
        state.note_unit("docking_pair", seconds)
        pair["pose_text"] = dock["pose_text"]
        pair["pose_path"] = dock["pose_path"]
        add_row(state, "aux", {
            "pair": pair["pair"], "seconds": seconds,
            "seconds_corrected": corrected_seconds(state, seconds),
            "docking_seconds": dock["seconds"], "truncated": truncated,
            "hours": corrected_seconds(state, seconds) / 3600.0,
            "n_interface_residues": analysis["n_interface_residues"],
            "site_class": analysis["site_class"],
            "pose_path": dock["pose_path"], "rank_table": dock["rank_table"],
            "frame": scored["frame"],
            "docking_parameters": dock["parameters"],
            "rank_table_parsed": True, "rank_rows": dock["rank_rows"],
            "top_pose_exists": True,
            "top_pose_roles_ok": bool(scored["pose_role_atoms"]),
            "contacts_at_4p5": True,
            "interface_residues_written": bool(analysis["interface_residues"]),
            "threefold_distance_written":
                analysis["distance_to_nearest_threefold_axis_a"] is not None,
            "site_class_written": bool(analysis["site_class"]),
            "call_table_row_written": True})
        finished_pairs.append(corrected_seconds(state, seconds))

    finished = state.clock()
    if stopped is not None:
        state.record_stop("ceiling_or_guard", "aux", stopped.reason)

    n = len(finished_pairs)
    measured = (sum(finished_pairs) / n / 3600.0) if n else None
    void_reason = None
    if n < MIN_AUX_PAIRS:
        void_reason = (f"fewer than {MIN_AUX_PAIRS} pairs finished; "
                       f"{LABEL_UNMEASURED}" if stopped else
                       f"fewer than {MIN_AUX_PAIRS} pairs finished")
    emit_input_record(
        state, "C3", measured, n=n, rows_arm="aux",
        start_epoch=started, end_epoch=finished,
        extra_values={"per_pair_hours": [s / 3600.0 for s in finished_pairs],
                      "pairs_finished": n},
        extra_notes=list(state.overhead_labels)
        + ([] if state.gpu_is_a100 else [f"{LABEL_NOT_A100}: C3 is still decided"]),
        void_reason=void_reason)
    if stopped is None:
        state.stages_done.append("aux")
    return {"n": n, "measured": measured, "stopped": bool(stopped)}


# ===========================================================================
# STAGE: ALPHAFOLD-MULTIMER TIMINGS (INPUT C1)
# ===========================================================================


def af2_command(state: RunState, fasta: Path, out_dir: Path, seed: int) -> list:
    return state.tool_command("colabfold_batch") + [
        "--num-models", str(AF2_MODELS),
        "--num-recycle", str(AF2_RECYCLES),
        "--recycle-early-stop-tolerance", "0.0",
        "--model-type", "alphafold2_multimer_v3",
        "--msa-mode", "single_sequence",
        "--num-seeds", "1",
        "--random-seed", str(seed),
        "--data", str(state.datadir),
        str(fasta), str(out_dir),
    ]


def inspect_af2_outputs(out_dir: Path) -> dict:
    """What one prediction call left behind: five structures and five scores."""
    structures = sorted(Path(out_dir).glob("*_relaxed_rank_*.pdb")) \
        or sorted(Path(out_dir).glob("*.pdb"))
    scores = sorted(Path(out_dir).glob("*_scores_rank_*.json")) \
        or sorted(Path(out_dir).glob("*scores*.json"))
    structures_ok = 0
    for p in structures:
        try:
            text = p.read_text()
        except OSError:
            continue
        if any(ln.startswith("ATOM") for ln in text.splitlines()) and p.stat().st_size > 0:
            structures_ok += 1
    scores_ok = 0
    for p in scores:
        try:
            if p.stat().st_size > 0:
                json.loads(p.read_text())
                scores_ok += 1
        except (OSError, ValueError):
            continue
    return {"n_model_structures": len(structures), "n_score_files": len(scores),
            "structures_parse_ok": structures_ok == len(structures) and structures_ok > 0,
            "score_files_parse_ok": scores_ok == len(scores) and scores_ok > 0}


def stage_af2(state: RunState) -> dict:
    """Time one whole prediction call per pair per seed, seed by seed."""
    started = state.clock()
    allowance = guard_before_stage(state, "af2", state.unit_estimate("af2_run"))
    pairs = load_pairs(state)
    rows = []
    per_pair_times = {}
    stopped = None

    for seed in AF2_SEEDS:
        if stopped:
            break
        for pair in pairs:
            left = allowance - (state.clock() - started)
            try:
                guard_before_unit(state, "af2", "af2_run", left)
            except GuardStop as stop:
                stopped = stop
                break
            out_dir = state.workdir / f"af2_{pair['pair']}_seed{seed}"
            out_dir.mkdir(parents=True, exist_ok=True)
            unit_started = state.clock()
            res = timed_call(
                state, f"af2_{pair['pair']}_seed{seed}",
                af2_command(state, Path(pair["fasta_path"]), out_dir, seed),
                limit_s=left, stage="af2")
            seconds = res.get("harness_seconds")
            log_text = (res.get("stdout", "") or "") + (res.get("stderr", "") or "")
            try:
                parsed = parse_colabfold_log_text(log_text)
                parse_error = None
            except ParseError as exc:
                parsed = {"per_model_s": [], "download_in_timed_call": False}
                parse_error = str(exc)
            outputs = inspect_af2_outputs(out_dir)
            row = {
                "pair": pair["pair"], "seed": seed,
                "wallclock_s": seconds,
                "wallclock_s_corrected": corrected_seconds(state, seconds),
                "hours": corrected_seconds(state, seconds) / 3600.0,
                "per_model_s": parsed["per_model_s"] or None,
                "per_model_s_reason": (None if parsed["per_model_s"] else
                                       (parse_error
                                        or "the log gave no per-model times")),
                "compile_excluded_s": (sum(parsed["per_model_s"][1:])
                                       if len(parsed["per_model_s"]) > 1 else None),
                "download_in_timed_call": parsed["download_in_timed_call"],
                "incomplete": bool(res.get("timed_out")),
                "rc": res.get("rc"),
                "models": AF2_MODELS, "recycles": AF2_RECYCLES,
                "early_stopping": "off", "msa_mode": "single_sequence",
                "fasta_length": pair.get("fasta_length"),
                "out_dir_bytes": res.get("work_dir_bytes"),
                "log": res.get("log"),
            }
            row.update(outputs)
            add_row(state, "af2", row)
            rows.append(row)
            if res.get("timed_out"):
                stopped = GuardStop("a prediction call ran past the time allowed "
                                    "for it", stage="af2", detail=res.get("log", ""))
                break
            if not res.get("ok"):
                raise HarnessFailure("a prediction call failed",
                                     f"exit {res.get('rc')}, see {res.get('log')}")
            state.note_unit("af2_run", state.clock() - unit_started)
            per_pair_times.setdefault(pair["pair"], []).append(
                corrected_seconds(state, seconds))
            pair.setdefault("af2_out_dirs", []).append(str(out_dir))

    finished = state.clock()
    if stopped is not None:
        state.record_stop("ceiling_or_guard", "af2", stopped.reason)

    summary = parse_af2_timing_rows_text(rows)
    spread = spread_check(per_pair_times)
    state.af2_spread = spread
    measured = summary["mean_h"]
    n = summary["n"]
    notes = list(state.overhead_labels)
    void_reason = None

    if any(r.get("download_in_timed_call") for r in rows):
        void_reason = "download inside timed call"
    elif n < MIN_AF2_RUNS or len(summary["pairs"]) < N_PAIRS:
        void_reason = (f"fewer than {MIN_AF2_RUNS} completed runs covering all "
                       f"{N_PAIRS} pairs")
        if stopped:
            void_reason += f"; {LABEL_UNMEASURED}"
    elif spread["zero_spread_pairs"]:
        void_reason = LABEL_ZERO_SPREAD
        notes.append(LABEL_ZERO_SPREAD)
    if spread["high_spread_pairs"]:
        notes.append(LABEL_SPREAD_HIGH)
    if not state.gpu_is_a100:
        notes.append(LABEL_NOT_A100)

    emit_input_record(
        state, "C1", measured, n=n, rows_arm="af2",
        start_epoch=started, end_epoch=finished,
        extra_values={
            "runs_counted": n, "pairs_covered": summary["pairs"],
            "per_run_hours": summary["hours"], "seed_spread": spread["per_pair"],
            "halt": spread["halt"], "models": AF2_MODELS, "recycles": AF2_RECYCLES,
            "early_stopping": "off", "msa_mode": "single_sequence",
            "compile_included": True},
        extra_notes=notes, void_reason=void_reason)
    if stopped is None:
        state.stages_done.append("af2")
    return {"n": n, "measured": measured, "stopped": bool(stopped), "spread": spread}


# ===========================================================================
# STAGE: MOLECULAR-DYNAMICS SPEED (INPUT C2)
# ===========================================================================


def md_worker_path(state: RunState) -> Path:
    path = state.outdir / f"md_worker_tag-{TAG}.py"
    if not path.exists():
        atomic_write_text(path, MD_WORKER_SOURCE)
    return path


def load_pose_text(state: RunState, pair: dict):
    """One pair's docked pose, from this run's memory or from the files on disk."""
    if pair.get("pose_text"):
        return pair["pose_text"]
    candidates = [f"pose_aux_{pair['pair']}_tag-{TAG}.pdb",
                  f"pose_{pair['pair']}_tag-{TAG}.pdb"]
    for name in candidates:
        p = state.input_path(name)
        if p is not None:
            return Path(p).read_text()
    rows = load_rows(state, "aux")
    for r in rows:
        if r.get("pair") != pair["pair"]:
            continue
        for key in ("pose_path", "pose", "top_pose"):
            value = r.get(key)
            if not value:
                continue
            p = state.input_path(Path(str(value)).name) or (
                Path(value) if Path(value).exists() else None)
            if p is not None:
                return Path(p).read_text()
    return None


def md_reporter_file(work, done) -> Path:
    """The segment's state-reporter file: named by the worker, else by shape.

    A worker summary that names no reporter is not a crash: the file is found
    in the working directory by name or by pattern, and when none exists the
    caller records that fact with a reason instead of a rate.
    """
    if isinstance(done, dict):
        for key in ("reporter_path", "reporter_file", "reporter",
                    "state_data_path", "state_data"):
            value = done.get(key)
            if not value:
                continue
            for candidate in (Path(str(value)), Path(work) / str(value)):
                if candidate.exists():
                    return candidate
    for name in ("md_reporter.csv", "reporter.csv", "state_data.csv"):
        candidate = Path(work) / name
        if candidate.exists():
            return candidate
    for pattern in ("*reporter*.csv", "*reporter*.txt", "*state*.csv"):
        hits = sorted(Path(work).glob(pattern))
        if hits:
            return hits[0]
    return None


def md_trajectory_file(work, done) -> Path:
    if isinstance(done, dict):
        for key in ("trajectory_path", "trajectory_file", "trajectory", "dcd"):
            value = done.get(key)
            if not value:
                continue
            for candidate in (Path(str(value)), Path(work) / str(value)):
                if candidate.exists():
                    return candidate
    for name in ("md_trajectory.dcd", "trajectory.dcd"):
        candidate = Path(work) / name
        if candidate.exists():
            return candidate
    for pattern in ("*.dcd",):
        hits = sorted(Path(work).glob(pattern))
        if hits:
            return hits[0]
    return None


def dcd_frame_count(path, atoms=None):
    """How many frames a trajectory file holds.

    A trajectory file in the DCD format opens with an 84-byte block that
    carries the tag "CORD" and the number of frames written. That number is
    read first, because it is what the writer itself recorded. Where the tag
    is absent the count is estimated from the file size: each frame holds
    three blocks of 4-byte numbers, one per axis, and each block is wrapped
    in two 4-byte markers.
    """
    p = Path(path)
    try:
        size = p.stat().st_size
        with open(str(p), "rb") as fh:
            head = fh.read(12)
    except OSError:
        return None
    if len(head) >= 12 and head[4:8] == b"CORD":
        for order in ("little", "big"):
            if int.from_bytes(head[0:4], order) == 84:
                return max(0, int.from_bytes(head[8:12], order, signed=True))
    if not atoms:
        return None
    per_frame = 12 * int(atoms) + 24
    return max(0, int(round((size - 276) / float(per_frame))))


def _first_present(source: dict, keys: tuple, fallback=None):
    for key in keys:
        value = source.get(key) if isinstance(source, dict) else None
        if value is not None:
            return value
    return fallback


def stage_md(state: RunState) -> dict:
    """Time one short production segment per docked complex and read its speed."""
    started = state.clock()
    allowance = guard_before_stage(state, "md", state.unit_estimate("md_complex"))
    worker = md_worker_path(state)
    worker_prefix = state.tool_command("md_worker") or \
        [state.python_executable(), str(worker)]
    steps = MD_PRODUCTION_STEPS
    rates = []
    rows = []
    stopped = None
    any_size_fault = None

    for pair in load_pairs(state):
        left = allowance - (state.clock() - started)
        try:
            guard_before_unit(state, "md", "md_complex", left)
        except GuardStop as stop:
            stopped = stop
            break
        pose_text = load_pose_text(state, pair)
        if not pose_text:
            add_row(state, "md", {"complex": pair["pair"], "atoms": None,
                                  "steps": None, "production_wallclock_s": None,
                                  "engine_ns_per_day": None,
                                  "frame_interval_ps": MD_FRAME_INTERVAL_PS,
                                  "skipped": "no docked pose for this pair"})
            continue
        unit_started = state.clock()
        cap = min(PER_COMPLEX_MD_CEILING_S, left)
        work = state.workdir / f"md_{pair['pair']}"
        work.mkdir(parents=True, exist_ok=True)
        pose_atoms = read_pdb_atoms(pose_text)
        merged = merge_capsid_and_pose(pair, pose_atoms)
        merged_pdb = work / "complex.pdb"
        atomic_write_text(merged_pdb, write_pdb(merged))
        capsid_heavy = len(heavy_atoms(
            [a for a in merged if a["chain"] in
             [c for c, r in pair["chain_map"].items() if r == "capsid"]]))

        padding = water_padding_nm(merged)
        built = None
        for attempt in (1, 2):
            out_json = work / f"build_{attempt}.json"
            res = state.runner.capture(
                worker_prefix + ["--mode", "build", "--pdb", str(merged_pdb),
                                 "--work", str(work),
                                 "--padding-nm", f"{padding:.3f}",
                                 "--out", str(out_json)],
                limit_s=inner_tool_limit_s(
                    state, cap - (state.clock() - unit_started)),
                stage="md", name=f"build_{pair['pair']}_{attempt}", cwd=work)
            if res.get("timed_out"):
                stopped = GuardStop("building the solvated complex ran past its time",
                                    stage="md", detail=res.get("log", ""))
                break
            if not res.get("ok") or not out_json.exists():
                raise HarnessFailure("building the solvated complex failed",
                                     f"exit {res.get('rc')}, see {res.get('log')}")
            built = json.loads(out_json.read_text())
            if MD_ATOMS_MIN <= built["atoms"] <= MD_ATOMS_MAX:
                break
            if attempt == 1:
                scale = (150000.0 / max(1, built["atoms"])) ** (1.0 / 3.0)
                padding = max(0.8, round(padding * scale, 3))
            else:
                any_size_fault = built["atoms"]
        if stopped:
            break
        if built is None:
            continue
        if not (MD_ATOMS_MIN <= built["atoms"] <= MD_ATOMS_MAX):
            add_row(state, "md", {"complex": pair["pair"], "atoms": built["atoms"],
                                  "steps": None, "production_wallclock_s": None,
                                  "engine_ns_per_day": None,
                                  "frame_interval_ps": MD_FRAME_INTERVAL_PS,
                                  "atom_count_out_of_range": True,
                                  "range": [MD_ATOMS_MIN, MD_ATOMS_MAX]})
            continue

        out_json = work / "run.json"
        res = state.runner.capture(
            worker_prefix + ["--mode", "run", "--work", str(work),
                             "--steps", str(steps),
                             "--timestep-fs", str(MD_TIMESTEP_FS),
                             "--seed", str(MD_VELOCITY_SEED),
                             "--report-interval", str(MD_REPORT_INTERVAL_STEPS),
                             "--out", str(out_json)],
            limit_s=inner_tool_limit_s(state, cap - (state.clock() - unit_started)),
            stage="md", name=f"run_{pair['pair']}", cwd=work)
        if res.get("timed_out"):
            add_row(state, "md", {"complex": pair["pair"], "atoms": built["atoms"],
                                  "steps": steps, "incomplete": True,
                                  "frame_interval_ps": MD_FRAME_INTERVAL_PS,
                                  "why": "the segment ran past the time allowed"})
            stopped = GuardStop("a dynamics segment ran past the time allowed "
                                "for it", stage="md", detail=res.get("log", ""))
            break
        if not res.get("ok") or not out_json.exists():
            raise HarnessFailure("the dynamics segment failed",
                                 f"exit {res.get('rc')}, see {res.get('log')}")
        done = json.loads(out_json.read_text()) if out_json.exists() else {}
        if not isinstance(done, dict):
            done = {}
        reporter_src = md_reporter_file(work, done)
        reporter_kept = state.outdir / f"md_reporter_{pair['pair']}_tag-{TAG}.csv"
        if reporter_src is not None and Path(reporter_src).exists():
            shutil.copyfile(str(reporter_src), str(reporter_kept))
            parsed = parse_reporter_file(reporter_kept)
        else:
            parsed = {"ns_per_day": None, "n_rows": 0,
                      "reason": "the engine wrote no reporter file",
                      "energies_finite": None, "last_step": None}
        done_steps = _first_present(done, ("steps", "n_steps",
                                           "production_steps"), steps)
        done_timestep = _first_present(done, ("timestep_fs", "timestep"),
                                       MD_TIMESTEP_FS)
        production_s = _first_present(
            done, ("production_s", "production_wallclock_s", "wallclock_s",
                   "wall_clock_s", "production_seconds"),
            res.get("seconds"))
        done_atoms = _first_present(done, ("atoms", "n_atoms", "atom_count"),
                                    built.get("atoms"))
        wall_rate = ns_per_day_from_wallclock(
            done_steps, done_timestep,
            corrected_seconds(state, production_s))
        disagree = rates_disagree(parsed["ns_per_day"], wall_rate)
        traj = md_trajectory_file(work, done)
        frames = None
        if traj is not None and Path(traj).exists():
            frames = dcd_frame_count(traj, built.get("atoms"))
        row = {
            "complex": pair["pair"], "atoms": done_atoms, "steps": done_steps,
            "timestep_fs": done_timestep,
            "production_ns": done_steps * done_timestep * 1e-6,
            "production_wallclock_s": production_s,
            "minimise_s": _first_present(done, ("minimise_s", "minimize_s")),
            "equilibrate_s": _first_present(done, ("equilibrate_s",)),
            "engine_ns_per_day": parsed["ns_per_day"],
            "wallclock_ns_per_day": wall_rate,
            "rates_disagree": disagree,
            "reporter_file": str(reporter_kept),
            "reporter_last_step": parsed.get("last_step"),
            "energies_finite": parsed.get("energies_finite"),
            "trajectory_file": str(traj) if traj is not None else None,
            "trajectory_bytes": apparent_bytes(traj or ""),
            "trajectory_frames": frames,
            "roles_present": True, "capsid_heavy_atoms": capsid_heavy,
            "frame_interval_ps": _first_present(
                done, ("frame_interval_ps",), MD_FRAME_INTERVAL_PS),
            "report_interval_steps": _first_present(
                done, ("report_interval_steps", "report_interval"),
                MD_REPORT_INTERVAL_STEPS),
            "platform": _first_present(done, ("platform",), MD_PLATFORM),
            "precision": _first_present(done, ("precision",), MD_PRECISION),
            "engine_version": _first_present(
                done, ("openmm_version", "engine_version")),
            "padding_nm": built.get("padding_nm"), "waters": built.get("waters"),
            "seed": MD_VELOCITY_SEED, "tool_log": res.get("log"),
        }
        add_row(state, "md", row)
        rows.append(row)
        rates.append(wall_rate)
        state.note_unit("md_complex", state.clock() - unit_started)
        pair["md_work"] = str(work)
        pair["md_logs"] = [p for p in [res.get("log")] if p]

    finished = state.clock()
    if stopped is not None:
        state.record_stop("ceiling_or_guard", "md", stopped.reason)

    clean = [r for r in rates if r is not None]
    n = len(clean)
    measured = statistics.median(clean) if clean else None
    notes = list(state.overhead_labels)
    void_reason = None
    if not state.gpu_is_a100:
        notes.append(LABEL_NOT_A100)
    if any_size_fault is not None and n == 0:
        void_reason = (f"the built system held {any_size_fault} atoms, outside "
                       f"{MD_ATOMS_MIN} to {MD_ATOMS_MAX}; the range is not widened")
    elif n < MIN_MD_COMPLEXES:
        void_reason = f"fewer than {MIN_MD_COMPLEXES} complexes finished"
        if stopped:
            void_reason += f"; {LABEL_UNMEASURED}"
    if any(r.get("rates_disagree") for r in rows):
        notes.append(LABEL_RATE_DISAGREE)
    if any(r.get("engine_ns_per_day") is None for r in rows):
        notes.append(LABEL_RATE_MISSING)

    emit_input_record(
        state, "C2", measured, n=n, rows_arm="md",
        start_epoch=started, end_epoch=finished,
        extra_values={
            "complexes": [{"complex": r.get("complex"), "atoms": r.get("atoms"),
                           "production_wallclock_s": r.get("production_wallclock_s"),
                           "engine_ns_per_day": r.get("engine_ns_per_day"),
                           "wallclock_ns_per_day": r.get("wallclock_ns_per_day")}
                          for r in rows if r.get("atoms")],
            "atom_counts": [r.get("atoms") for r in rows if r.get("atoms")],
            "timestep_fs": MD_TIMESTEP_FS, "production_ns": MD_PRODUCTION_NS,
            "engine_precision": MD_PRECISION, "engine_platform": MD_PLATFORM,
            "engine_version": next((r.get("engine_version") for r in rows
                                    if r.get("engine_version")), None),
            "frame_interval_ps": MD_FRAME_INTERVAL_PS,
            "velocity_seed": MD_VELOCITY_SEED,
            "decision_value": "median over complexes of the wall-clock figure"},
        extra_notes=notes, void_reason=void_reason)
    if stopped is None:
        state.stages_done.append("md")
    return {"n": n, "measured": measured, "stopped": bool(stopped)}


# ===========================================================================
# STAGE: STORAGE (INPUT C4)
# ===========================================================================


def stage_storage(state: RunState) -> dict:
    """Measure what one run of the grid actually writes, and scale it up."""
    started = state.clock()
    guard_before_stage(state, "storage", state.unit_estimate("storage"))
    pairs = load_pairs(state)
    roots = [state.workdir, Path(state.indir) / f"work_{TAG}"]

    def find_dir(name):
        for root in roots:
            candidate = Path(root) / name
            if candidate.exists():
                return candidate
        return None

    artifacts = []

    af2_dirs = [d for p in pairs for d in p.get("af2_out_dirs", [])]
    af2_dirs = [find_dir(f"af2_{p['pair']}_seed0") or find_dir(f"af2_{p['pair']}_seed1")
                for p in pairs] + list(af2_dirs)
    af2_dirs = [d for d in af2_dirs if d]
    if af2_dirs:
        b = apparent_bytes(af2_dirs[0])
        artifacts.append({"artifact": "prediction outputs of one run",
                          "path": str(af2_dirs[0]), "bytes": b, "kind": "af2",
                          "counts_in": True, "intermediate": False,
                          "source": str(af2_dirs[0])})
    docking_dirs = [find_dir(f"aux_{p['pair']}") for p in pairs]
    docking_dirs = [d for d in docking_dirs if d]
    if docking_dirs:
        b = apparent_bytes(docking_dirs[0])
        artifacts.append({"artifact": "whole docking output tree of one pair",
                          "path": str(docking_dirs[0]), "bytes": b, "kind": "docking",
                          "counts_in": True, "intermediate": True,
                          "source": str(docking_dirs[0])})
    md_dirs = [p.get("md_work") or find_dir(f"md_{p['pair']}") for p in pairs]
    md_dirs = [Path(d) for d in md_dirs if d]
    md_bytes = 0
    md_setup_bytes = 0
    md_breakdown = None
    if md_dirs:
        first = md_dirs[0]
        md_logs = []
        for p in pairs:
            if p.get("md_logs"):
                md_logs = list(p["md_logs"])
        md_breakdown = md_bytes_breakdown(first, md_logs)
        md_bytes = md_breakdown["md_bytes"]
        md_setup_bytes = md_breakdown["md_setup_bytes"]
        artifacts.append({"artifact": "dynamics trajectory and every log of one "
                                      f"{MD_PRODUCTION_NS} ns segment",
                          "path": str(first), "bytes": md_bytes,
                          "kind": "md", "counts_in": True, "intermediate": True,
                          "md_setup_bytes": md_setup_bytes,
                          "source": str(first)})

    for a in artifacts:
        add_row(state, "storage", a)

    finished = state.clock()
    n = len(artifacts)
    measured = None
    void_reason = None
    scaled = {}
    if n < 1:
        void_reason = f"no artifact of any type was produced; {LABEL_UNMEASURED}"
    else:
        total = sum(a["bytes"] for a in artifacts)
        total = max(0, total - state.overhead_bytes)
        scaled = storage_from_bytes(total)
        measured = scaled["gib_216_runs"]
        kept_only = sum(a["bytes"] for a in artifacts if not a["intermediate"])
        scaled["gib_216_runs_intermediates_deleted"] = (
            max(0, kept_only - state.overhead_bytes) * GRID_RUNS / float(BYTES_PER_GIB))
        scaled["md_bytes_per_ns"] = (md_bytes / MD_PRODUCTION_NS) if md_bytes else None
        if n < 3:
            void_reason = ("not every artifact type was produced: "
                           f"{n} of 3; {LABEL_UNMEASURED}" if state.stopped
                           else f"not every artifact type was produced: {n} of 3")

    emit_input_record(
        state, "C4", measured, n=n, rows_arm="storage",
        start_epoch=started, end_epoch=finished,
        extra_values={
            "artifacts": artifacts,
            "bytes_per_run": scaled.get("bytes_per_run"),
            "gib_216_runs": scaled.get("gib_216_runs"),
            "gib_432_runs": scaled.get("gib_432_runs"),
            "gib_216_runs_intermediates_deleted":
                scaled.get("gib_216_runs_intermediates_deleted"),
            "md_bytes": md_bytes, "md_setup_bytes": md_setup_bytes,
            "md_bytes_breakdown": md_breakdown,
            "md_bytes_per_ns": scaled.get("md_bytes_per_ns"),
            "frame_interval_ps": MD_FRAME_INTERVAL_PS,
            "grid_runs_used_for_the_decision": GRID_RUNS},
        extra_notes=list(state.overhead_labels)
        + ([] if state.gpu_is_a100 else [f"{LABEL_NOT_A100}: C4 is still decided"]),
        void_reason=void_reason)
    state.stages_done.append("storage")
    return {"n": n, "measured": measured}


# ===========================================================================
# STAGE: ENDPOINTS
# Always runs. Writes a record for every input that has none, then the
# environment note, the summary and the validity file.
# ===========================================================================


def emit_anchor_void_record(state: RunState, *, start_epoch, end_epoch,
                            why: str = LABEL_ANCHOR_NOT_REACHED) -> Path:
    pdb_path = state.input_path(f"{PDB_ENTRY}_tag-{TAG}.pdb") \
        or state.input_path(f"{PDB_ENTRY}.pdb")
    reason = str(why or LABEL_ANCHOR_NOT_REACHED)
    return write_record(
        state, f"endpoint-anchor_tag-{TAG}.json", kind="anchor",
        cell={"stage": "anchor", "endpoint": "anchor", "tag": TAG},
        inputs=record_inputs(state, state.outdir / f"rows_anchor_tag-{TAG}.jsonl",
                             extra_paths=[pdb_path] if pdb_path else None),
        metric=("contact overlap with the published complex at 4.5 angstrom, or "
                "interface backbone displacement, with serial and parallel agreement"),
        values={
            "measured": None,
            "published": (f"AAVR-PKD2 bound to the AAV2 spike region adjacent to "
                          f"the icosahedral three-fold axis (PDB {PDB_ENTRY})"),
            "tolerance": {"min_contact_overlap": ANCHOR_OVERLAP_MIN,
                          "max_interface_backbone_rmsd_a": ANCHOR_IFACE_RMSD_MAX,
                          "max_serial_parallel_rmsd_a":
                              ANCHOR_SERIAL_PARALLEL_RMSD_MAX,
                          "calls_must_be_identical": True},
            "unit": "fraction of published contacts, and angstrom",
            "independent_code": ANCHOR_INDEPENDENT_CODE,
            "docking_order": DOCKING_ORDER,
            "void_reason": reason, "voided_by": reason,
            "calibration_valid": False,
            "calibration_checks": [
                {"check": "both_poses_obtained_and_compared", "result": False,
                 "value": False, "null_reason": reason}],
            "null_reasons": {"measured": reason}},
        threshold={"min_contact_overlap": ANCHOR_OVERLAP_MIN,
                   "max_interface_backbone_rmsd_a": ANCHOR_IFACE_RMSD_MAX,
                   "max_serial_parallel_rmsd_a": ANCHOR_SERIAL_PARALLEL_RMSD_MAX},
        decision_rule=("PASS when the pose reproduces the published placement "
                       "and serial and parallel agree; VOID when the run ended "
                       "before the check could be made"),
        decision="VOID",
        labels=labels_for_record(state, start_epoch, end_epoch),
        extra_notes=[LABEL_SERIAL_PARALLEL_WHOLE_CHAIN])


def decide_exit_code(state: RunState) -> int:
    """The exit table's precedence: 2, then 4, then 3, then 0.

    Row 3 applies only when a guard, a ceiling or a timeout actually stopped
    work and left an input unmeasured. An input a stage simply does not measure
    is not a stop.
    """
    if state.failure_kind or (not state.run_valid and not state.anchor_missed):
        return EXIT_INFRA
    if state.anchor_missed:
        return EXIT_ANCHOR
    if state.unmeasured_inputs() and state.stop_events:
        return EXIT_GUARD
    return EXIT_OK


def measure_from_rows(state: RunState, cid: str, rows: list):
    """One input's decision value, from the raw rows alone."""
    if cid == "C1":
        summary = parse_af2_timing_rows_text(rows)
        return summary["mean_h"], summary["n"]
    if cid == "C2":
        rates = []
        for r in rows:
            if r.get("incomplete") or not r.get("atoms"):
                continue
            rate = r.get("wallclock_ns_per_day")
            if rate is None and r.get("production_wallclock_s"):
                rate = ns_per_day_from_wallclock(
                    r.get("steps") or MD_PRODUCTION_STEPS,
                    r.get("timestep_fs") or MD_TIMESTEP_FS,
                    r.get("production_wallclock_s"))
            if rate is not None:
                rates.append(rate)
        return (statistics.median(rates) if rates else None), len(rates)
    if cid == "C3":
        hours = []
        for r in rows:
            if r.get("truncated") or r.get("incomplete") or r.get("seconds") is None:
                continue
            hours.append(r.get("hours")
                         if r.get("hours") is not None
                         else r.get("seconds") / 3600.0)
        return ((sum(hours) / len(hours)) if hours else None), len(hours)
    if cid == "C4":
        counted = [r for r in rows
                   if r.get("counts_in") is not False and r.get("bytes") is not None]
        total = sum(int(r.get("bytes") or 0) for r in counted)
        if not counted:
            return None, 0
        scaled = storage_from_bytes(max(0, total - state.overhead_bytes))
        return scaled["gib_216_runs"], len(counted)
    return None, 0


def stage_endpoints(state: RunState) -> dict:
    """Close the run: every input gets a record, then the summary is written."""
    started = state.clock()
    anchor_name = f"endpoint-anchor_tag-{TAG}.json"
    present = any(state.input_path(f"rows_{arm}_tag-{TAG}.jsonl") is not None
                  for arm in ("af2", "md", "aux", "storage")) \
        or state.input_path(f"pairs_tag-{TAG}.json") is not None \
        or state.input_path(anchor_name) is not None
    if not present and not state.failure_kind and not state.stop_events:
        raise HarnessFailure(
            f"the stage needs rows_af2_tag-{TAG}.jsonl and it is not in the inputs",
            f"looked in {state.indir} and {state.outdir}", kind="missing_input")
    ensure_anchor_record(
        state, why=(f"{LABEL_ANCHOR_NOT_REACHED}: "
                    + (state.run_valid_voided_by or state.failure_kind
                       or "; ".join(e["reason"] for e in state.stop_events)
                       or "the run ended before the anchor stage")))
    for cid in INPUT_IDS:
        name = f"endpoint-{cid}_tag-{TAG}.json"
        if name in state.records_written or (state.outdir / name).exists():
            continue
        rows_arm = {"C1": "af2", "C2": "md", "C3": "aux", "C4": "storage"}[cid]
        rows = load_rows(state, rows_arm)
        measured, n = measure_from_rows(state, cid, rows)
        if state.failure_kind:
            why = ("the run ended on broken infrastructure: "
                   f"{state.run_valid_voided_by or state.failure_kind}")
        elif state.stopped and measured is None:
            stop_names = "; ".join(e["reason"] for e in state.stop_events)
            why = f"{LABEL_UNMEASURED} ({stop_names})"
        else:
            why = None
        emit_input_record(
            state, cid, measured, n=n, rows_arm=rows_arm,
            start_epoch=started, end_epoch=state.clock(),
            void_reason=why, rows=rows, stop_kind=state.last_stop_kind())
    state.sweep_unmeasured_after_stop()
    state.exit_code = decide_exit_code(state)
    write_env_note(state)
    write_summary(state)
    write_run_valid(state)
    state.stages_done.append("endpoints")
    return {"records": list(state.records_written), "exit_code": state.exit_code}


def write_env_note(state: RunState) -> Path:
    lines = [
        "# Named non-secret variables only. Nothing here is dumped wholesale and",
        "# no variable that can carry a download token is listed.",
    ]
    for key in ENV_RECORD_KEYS:
        value = state.env.get(key, "")
        if key == "REMOTE_TIMEOUT" and not state.remote_timeout_forwarded:
            value = f"{int(DEFAULT_REMOTE_TIMEOUT_S)} ({LABEL_TIMEOUT_NOT_FORWARDED})"
        lines.append(f"{key}={value}")
    lines.append(f"remote_timeout_seen_s={state.remote_timeout_s}")
    lines.append(f"pre_t0_seconds={state.pre_t0_seconds}")
    lines.append(f"stop_at_s={state.stop_at_s}")
    lines.append(f"binding_cap={state.caps['binding']}")
    lines.append(f"venv_path={state.venv_path}")
    lines.append(f"expected_lock_sha256={state.expected_lock_sha256}")
    lines.append(f"observed_lock_sha256={state.observed_lock_sha256}")
    lines.append(f"environment_changed_by_fixer="
                 f"{bool(state.environment_changed_by_fixer)}")
    lines.append(f"held_attempts={state.held_attempts}")
    if state.bootstrap_assumed:
        lines.append(f"bootstrap_note={LABEL_BOOTSTRAP_ASSUMED}")
    for key in SECRET_ENV_KEYS:
        lines.append(f"{key}=<not read, not printed, removed from every child>")
    path = state.outdir / "env.txt"
    atomic_write_text(path, "\n".join(lines) + "\n")
    return path


def summary_object(state: RunState) -> dict:
    """The summary's contents, in order. It restates records; it decides nothing."""
    records = {}
    for name in sorted(set(state.records_written)):
        try:
            records[name] = json.loads((state.outdir / name).read_text())
        except (OSError, ValueError):
            records[name] = {"unreadable": True}

    c1 = records.get(f"endpoint-C1_tag-{TAG}.json", {})
    c1_values = c1.get("values", {}) if isinstance(c1, dict) else {}
    gate_pass = c1_values.get("gate_pass")
    if gate_pass is None:
        gate_block = {
            "gate": GATE_EXPRESSION, "applied_to": "C1 only", "gate_pass": None,
            "gate_value": GATE_VALUE,
            "gate_note": c1_values.get("gate")
            or "not evaluated: C1 holds no valid measurement",
            "fallback_text": GATE_ELSE, "fallback_triggered": False,
            "fallback_note": ("the fallback is not presented as triggered, "
                              "because the gate was not evaluated")}
    else:
        gate_block = {
            "gate": GATE_EXPRESSION, "applied_to": "C1 only",
            "gate_pass": bool(gate_pass), "gate_value": GATE_VALUE,
            "gate_note": None, "fallback_text": GATE_ELSE,
            "fallback_triggered": not gate_pass}

    spread = getattr(state, "af2_spread", None) or \
        {"per_pair": {}, "high_spread_pairs": []}
    notes = []
    if spread.get("high_spread_pairs"):
        notes.append(LABEL_SPREAD_HIGH)
    if state.stopped:
        notes.append(LABEL_INCOMPLETE)
    if state.overhead_labels:
        notes.extend(state.overhead_labels)
    if not state.remote_timeout_forwarded:
        notes.append(LABEL_TIMEOUT_NOT_FORWARDED)
    if state.bootstrap_assumed:
        notes.append(LABEL_BOOTSTRAP_ASSUMED)
    if state.environment_changed_by_fixer:
        notes.append(LABEL_FIXER_CHANGED_ENV % (state.observed_lock_sha256 or "unknown"))
    for label in str(state.env.get("M4_HOLD_LABELS", "")).split("|"):
        if label.strip():
            notes.append(label.strip())

    unmeasured = {cid: state.inputs_status.get(cid, {})
                  for cid in state.unmeasured_inputs()}

    obj = {}
    obj["what_this_run_decides"] = WHAT_THIS_RUN_DECIDES
    obj["tag"] = TAG
    obj["run_valid"] = bool(state.run_valid)
    obj["run_valid_voided_by"] = state.run_valid_voided_by
    obj["exit_code"] = state.exit_code if state.exit_code is not None \
        else decide_exit_code(state)
    obj["records"] = records
    obj["inputs_status"] = state.inputs_status
    obj["gate"] = gate_block
    obj["unmeasured_inputs"] = unmeasured
    obj["held_attempts"] = state.held_attempts
    obj["seed_spread"] = spread
    obj["anchor"] = state.anchor
    obj["environment"] = {
        "venv_path": state.venv_path,
        "expected_lock_sha256": state.expected_lock_sha256,
        "observed_lock_sha256": state.observed_lock_sha256,
        "environment_changed_by_fixer": bool(state.environment_changed_by_fixer),
        "hold_seconds_forwarded": state.env.get("HOLD_SECONDS") or None,
        "changes_log_sha256": state.changes_log_sha256,
        "note": ("the python environment is an artifact on the attached "
                 "filesystem; this run installs nothing and pins nothing")}
    obj["stop_events"] = state.stop_events
    obj["guard_arithmetic"] = guard_arithmetic_line(state)
    obj["stages_done"] = state.stages_done
    obj["notes"] = notes
    obj["incomplete_run_label"] = LABEL_INCOMPLETE if state.stopped else None
    obj["no_relaunch_for_spread"] = (
        "A high spread across seeds is labelled, never answered with another "
        "launch on this box; two runs on the same box are two samples of one "
        "box, never a replication.")
    obj["timing"] = {
        "t0_utc": utc_of(state.t0),
        "elapsed_s": round(state.elapsed_s(), 3),
        "pre_t0_seconds": state.pre_t0_seconds,
        "remote_timeout_seen_s": state.remote_timeout_s,
        "remote_timeout_forwarded": state.remote_timeout_forwarded,
        "stop_at_s": state.stop_at_s, "binding_cap": state.caps["binding"],
        "price_usd_per_hour": state.price_usd_per_hour,
        "budget_left_usd": state.budget_left_usd,
        "estimated_spend_usd": round(state.spend_usd(), 4),
        "estimated_spend_note": (
            "seconds since the run's own start times the hourly price; the "
            "bootstrap seconds are reported beside this and are not added again"),
        "pre_t0_seconds_reported_not_added": state.pre_t0_seconds,
        "setup_seconds_used": round(state.setup_seconds_used, 3)}
    obj["compute"] = build_compute_table(state)
    obj["files_written"] = sorted(
        p.name for p in state.outdir.glob("*") if p.is_file())
    return obj


def write_summary(state: RunState) -> Path:
    path = state.outdir / f"{TAG}_summary.json"
    atomic_write_text(path, json.dumps(summary_object(state), indent=2) + "\n")
    return path


def write_run_valid(state: RunState) -> Path:
    state.sweep_void_by_failure()
    path = state.outdir / "RUN_VALID.json"
    atomic_write_json(path, {
        "run_valid": bool(state.run_valid),
        "voided_by": state.run_valid_voided_by,
        "stopped": state.stopped, "stop_events": state.stop_events,
        "inputs_status": state.inputs_status, "tag": TAG})
    return path


def write_run_done(state: RunState, exit_code: int) -> Path:
    state.sweep_void_by_failure()
    per_input = {}
    for cid, status in state.inputs_status.items():
        entry = {"status": status.get("status", "unmeasured_by_stop:unknown"),
                 "decision": status.get("decision"),
                 "reason": status.get("reason"),
                 "calibration_valid": status.get("calibration_valid")}
        if status.get("voided_by"):
            entry["voided_by"] = status["voided_by"]
        per_input[cid] = entry
    path = state.outdir / "RUN_DONE"
    atomic_write_text(path, json.dumps({
        "exit_code": exit_code, "run_valid": bool(state.run_valid),
        "voided_by": state.run_valid_voided_by,
        "stopped_by": [e["reason"] for e in state.stop_events],
        "guard_arithmetic": guard_arithmetic_line(state),
        "failure_kind": state.failure_kind,
        "anchor_missed": bool(state.anchor_missed),
        "held_attempts": state.held_attempts, "inputs": per_input,
        "notes": ([LABEL_INCOMPLETE] if state.stopped else []),
        "tag": TAG, "finished_utc": state.now()}, indent=2) + "\n")
    return path


# ===========================================================================
# CLOSING A RUN THE LAUNCHER'S OWN TIMER ENDED
# ===========================================================================


def record_status_from_disk(rec) -> dict:
    if not isinstance(rec, dict):
        return {"state": "unmeasured", "decision": None,
                "reason": "no record was written for this input"}
    decision = rec.get("decision")
    values = rec.get("values") or {}
    reason = str(values.get("void_reason") or values.get("voided_by") or "")
    notes = " ".join(str(n) for n in (rec.get("notes_list") or []))
    if decision in ("PASS", "FAIL"):
        return {"state": "decided", "decision": decision, "reason": None,
                "calibration_valid": values.get("calibration_valid")}
    if decision == "VOID":
        if LABEL_UNMEASURED in reason or LABEL_UNMEASURED in notes:
            return {"state": "unmeasured", "decision": "VOID",
                    "reason": reason or LABEL_UNMEASURED,
                    "calibration_valid": values.get("calibration_valid")}
        if values.get("marginal") or reason:
            return {"state": "void_by_rule", "decision": "VOID",
                    "reason": reason or "within 10 percent of a band edge",
                    "calibration_valid": values.get("calibration_valid")}
        return {"state": "unmeasured", "decision": "VOID",
                "reason": "the record names no rule that voided it",
                "calibration_valid": values.get("calibration_valid")}
    return {"state": "unmeasured", "decision": decision,
            "reason": "the record carries no decision",
            "calibration_valid": values.get("calibration_valid")}


def finalize_from_disk(state: RunState, outer_rc=None) -> int:
    state.record_stop("outer_timeout", "outer",
                      f"the launcher's own timeout returned {outer_rc}")
    state.notes.append("closed from the records on disk after the launcher's own timer")

    validity_path = state.outdir / "RUN_VALID.json"
    run_valid = True
    voided_by = None
    if validity_path.exists():
        try:
            doc = json.loads(validity_path.read_text())
            if doc.get("run_valid") is False:
                run_valid = False
                voided_by = doc.get("voided_by") or \
                    "the validity file says the run is invalid"
        except (OSError, ValueError):
            pass

    anchor_decision_on_disk = None
    existing = {}
    for name in ["endpoint-anchor"] + [f"endpoint-{cid}" for cid in INPUT_IDS]:
        path = state.outdir / f"{name}_tag-{TAG}.json"
        rec = None
        if path.exists():
            try:
                rec = json.loads(path.read_text())
            except (OSError, ValueError):
                rec = None
        existing[name] = rec
        if isinstance(rec, dict) and rec.get("run_valid") is False:
            run_valid = False
            voided_by = voided_by or rec.get("run_valid_voided_by") or \
                "a record on disk says the run is invalid"
        if name == "endpoint-anchor" and isinstance(rec, dict):
            anchor_decision_on_disk = rec.get("decision")
            if rec.get("decision") == "FAIL":
                state.anchor_missed = (
                    str(rec.get("values", {}).get("voided_by")
                        or "the anchor record on disk is FAIL"))
            state.anchor = {"verdict": {"decision": rec.get("decision")},
                            "values": rec.get("values")}

    if (not run_valid and voided_by
            and "anchor" not in str(voided_by).lower()):
        state.failure_kind = state.failure_kind or "failure_recorded_on_disk"
    state.run_valid = run_valid
    state.run_valid_voided_by = voided_by
    state.records_written = [p.name for p in state.outdir.glob("endpoint-*.json")]

    for cid in INPUT_IDS:
        status = record_status_from_disk(existing.get(f"endpoint-{cid}"))
        if status["state"] == "decided":
            state.set_decided(cid, status["decision"], None,
                              status.get("calibration_valid"))
        elif status["state"] == "void_by_rule":
            state.set_decided(cid, "VOID", status["reason"],
                              status.get("calibration_valid"))
        else:
            state.set_unmeasured(cid, "outer_timeout",
                                 calibration_valid=False)

    if not (state.outdir / f"endpoint-anchor_tag-{TAG}.json").exists():
        emit_anchor_void_record(
            state, start_epoch=state.t0, end_epoch=state.clock(),
            why=(f"{LABEL_ANCHOR_NOT_REACHED}: the launcher's own timer ended "
                 f"the run before the anchor was compared"))
    for cid in INPUT_IDS:
        path = state.outdir / f"endpoint-{cid}_tag-{TAG}.json"
        if path.exists():
            continue
        emit_input_record(
            state, cid, None, n=0, rows_arm=None,
            start_epoch=state.t0, end_epoch=state.clock(),
            void_reason=f"{LABEL_UNMEASURED} (the launcher's own timer ended "
                        f"the run)",
            stop_kind="outer_timeout")
    state.exit_code = decide_exit_code(state)
    write_env_note(state)
    write_summary(state)
    write_run_valid(state)
    return state.exit_code


# ===========================================================================
# THE STAGE FLOW
# ===========================================================================


STAGE_FUNCTIONS = {
    "capability": (stage_capability, False),
    "downloads": (stage_downloads, False),
    "controls": (stage_controls, False),
    "anchor": (stage_anchor, True),
    "aux": (stage_aux, True),
    "af2": (stage_af2, True),
    "md": (stage_md, True),
    "storage": (stage_storage, True),
    "endpoints": (stage_endpoints, False),
}


def run_stages(state: RunState, stages=None, outer_rc=None) -> int:
    """Run the stages in order and return the exit code the box should report."""
    order = stages or [name for name in STAGE_ORDER if name != "endpoints"]
    failure = None

    if outer_rc is not None:
        handled = handle_outer_rc(state, outer_rc)
        if handled == EXIT_INFRA:
            failure = EXIT_INFRA
            state.void_run(f"the run was killed with code {outer_rc} well before "
                           f"the deadline")
            state.failure_kind = "killed_early"
        elif handled == EXIT_GUARD:
            state.record_stop("outer_timeout", "outer",
                              f"the launcher's own timeout returned {outer_rc}")

    if failure is None:
        for name in order:
            fn, gpu = STAGE_FUNCTIONS[name]
            try:
                with StageTimer(state, name, gpu=gpu):
                    fn(state)
            except GuardStop as stop:
                state.record_stop("guard", stop.stage or name, stop.reason)
                continue
            except FrameGuardReject as rej:
                state.void_run(f"the frame guard refused a pose: {rej.reason}")
                state.failure_kind = "anchor_frame"
                failure = EXIT_INFRA
                break
            except HarnessFailure as exc:
                state.void_run(f"{exc.reason}: {exc.detail}" if exc.detail
                               else exc.reason)
                state.failure_kind = exc.kind
                failure = EXIT_INFRA
                break
            except (ParseError, ValueError) as exc:
                state.void_run(f"broken tool output could not be read: {exc}")
                state.failure_kind = "parse_error"
                failure = EXIT_INFRA
                break

    try:
        with StageTimer(state, "endpoints", gpu=False):
            stage_endpoints(state)
    except Exception as exc:
        state.notes.append(f"the closing stage itself failed: {exc}")
        if failure is None:
            failure = EXIT_INFRA
            state.void_run(f"the closing stage failed: {exc}")
        try:
            ensure_anchor_record(state)
            write_env_note(state)
            write_summary(state)
            write_run_valid(state)
        except Exception as exc2:
            state.notes.append(f"the closing fallback failed: {exc2}")

    code = decide_exit_code(state)
    if failure == EXIT_INFRA:
        return EXIT_INFRA
    return code


def handle_outer_rc(state: RunState, rc: int) -> int:
    if rc == 124:
        return EXIT_GUARD
    if rc == 137:
        deadline_since_t0 = state.stop_at_s - OUTER_KILL_SLACK_S
        return EXIT_GUARD if state.elapsed_s() >= deadline_since_t0 - 5 else EXIT_INFRA
    if rc not in (0, None):
        return EXIT_INFRA
    return EXIT_OK


def load_prior_state(state: RunState) -> None:
    """Recover what earlier stages already decided, from the files on disk.

    Every stage runs as its own invocation, so the anchor's verdict, the run's
    validity and the controls' results must be read back before any later
    record is written.
    """
    def read_doc(name):
        p = state.input_path(name)
        if p is None:
            return None, None
        try:
            return json.loads(Path(p).read_text()), p
        except (OSError, ValueError):
            return None, p

    valid, _p = read_doc("RUN_VALID.json")
    if isinstance(valid, dict):
        if valid.get("run_valid") is False:
            state.run_valid = False
            state.run_valid_voided_by = valid.get("voided_by") or \
                "a record on disk says the run is invalid"
        if valid.get("stopped"):
            state.stopped = True
        for event in valid.get("stop_events") or []:
            if isinstance(event, dict) and event.get("reason"):
                state.stop_events.append(event)

    anchor, anchor_path = read_doc(f"endpoint-anchor_tag-{TAG}.json")
    if isinstance(anchor, dict):
        state.anchor = {"verdict": {"decision": anchor.get("decision")},
                        "values": anchor.get("values") or {},
                        "docking_parameters": (anchor.get("values") or {}).get(
                            "docking_parameters")}
        if anchor.get("decision") == "FAIL":
            state.anchor_missed = (
                anchor.get("run_valid_voided_by")
                or (anchor.get("values") or {}).get("voided_by")
                or (anchor.get("values") or {}).get("void_reason")
                or "the anchor record on disk is FAIL")
            state.run_valid = False
            state.run_valid_voided_by = state.anchor_missed
        elif anchor.get("run_valid") is False:
            state.run_valid = False
            state.run_valid_voided_by = anchor.get("run_valid_voided_by")

    sleep, _p = read_doc(f"control-sleep_tag-{TAG}.json")
    if isinstance(sleep, dict):
        state.sleep_ok = (sleep.get("decision") == "PASS")

    for name in (f"env_check_tag-{TAG}.json", f"control-sleep_tag-{TAG}.json",
                 f"control-empty-run_tag-{TAG}.json",
                 f"endpoint-anchor_tag-{TAG}.json"):
        doc, _p = read_doc(name)
        if not isinstance(doc, dict):
            continue
        machine = (doc.get("values") or {}).get("machine") or {}
        gpu = machine.get("gpu_name")
        if gpu:
            state.gpu_name = gpu
            state.gpu_visible = True
            state.gpu_is_a100 = is_a100(gpu)
            break


# ===========================================================================
# ENTRY POINTS
# ===========================================================================


def build_state(argv, indir=None) -> "tuple":
    base = Path(argv.base or os.environ.get("M4_BASE") or ".").resolve()
    outdir = Path(argv.outdir) if getattr(argv, "outdir", None) \
        else base / f"results_{TAG}" / "out"
    # Every working file lives under --out: a stage writes nowhere else.
    workdir = Path(argv.workdir) if getattr(argv, "workdir", None) \
        else Path(outdir) / f"work_{TAG}"
    datadir = Path(argv.datadir) if getattr(argv, "datadir", None) else base / "data"
    # A stage invocation writes only under --out: its downloads land there too.
    if getattr(argv, "datadir", None):
        download_dir = Path(argv.datadir)
    elif getattr(argv, "outdir", None):
        download_dir = Path(outdir) / "data"
    else:
        download_dir = datadir
    sys.path.insert(0, str(base / "frozen"))
    try:
        import provenance
    except ImportError as exc:
        print(f"[m4] FATAL: the record writer frozen/provenance.py is missing: {exc}",
              file=sys.stderr)
        return None, None
    state = RunState(outdir, workdir, datadir, provenance=provenance, base=base,
                     indir=indir)
    state.download_dir = download_dir
    state.runner = ToolRunner(state)
    load_prior_state(state)
    return state, base


STAGE_INPUT_ID = {"aux": "C3", "af2": "C1", "md": "C2", "storage": "C4"}


def ensure_anchor_record(state: RunState, why: str = LABEL_ANCHOR_NOT_REACHED) -> None:
    """One anchor record per run: written if absent, copied if only in --in.

    A verdict already on disk is never changed by a later stage.
    """
    name = f"endpoint-anchor_tag-{TAG}.json"
    out_path = state.outdir / name
    found = state.input_path(name)
    if found is not None:
        if Path(found).resolve() != out_path.resolve() and not out_path.exists():
            try:
                atomic_write_text(out_path, Path(found).read_text())
            except OSError:
                pass
        return
    emit_anchor_void_record(state, start_epoch=state.t0, end_epoch=state.clock(),
                            why=why)


def close_stage_invocation(state: RunState, stage: str, exit_code: int) -> int:
    """Write what a single-stage run owes before it returns."""
    cid = STAGE_INPUT_ID.get(stage)
    try:
        if cid is not None:
            name = f"endpoint-{cid}_tag-{TAG}.json"
            if name not in state.records_written and not (state.outdir / name).exists():
                rows_arm = {"C1": "af2", "C2": "md", "C3": "aux", "C4": "storage"}[cid]
                if state.failure_kind:
                    why = ("the run ended on broken infrastructure: "
                           f"{state.run_valid_voided_by or state.failure_kind}")
                elif state.stopped:
                    why = f"{LABEL_UNMEASURED} ({state.last_stop_kind()})"
                else:
                    why = f"{LABEL_UNMEASURED} (the stage did not record a value)"
                emit_input_record(
                    state, cid, None, n=0, rows_arm=rows_arm,
                    start_epoch=state.t0, end_epoch=state.clock(),
                    void_reason=why, stop_kind=state.last_stop_kind())
        if exit_code in (EXIT_INFRA, EXIT_GUARD):
            try:
                ensure_anchor_record(
                    state, why=(f"{LABEL_ANCHOR_NOT_REACHED}: "
                                + (state.run_valid_voided_by or state.failure_kind
                                   or "; ".join(e["reason"] for e in state.stop_events)
                                   or "the run ended before the anchor stage")))
            except Exception as exc:
                state.notes.append(f"the anchor record could not be closed: {exc}")
        for step in (write_env_note, write_run_valid, write_summary):
            try:
                step(state)
            except Exception as exc:
                state.notes.append(f"{step.__name__} failed: {exc}")
    except Exception as exc:
        state.notes.append(f"closing the stage invocation failed: {exc}")
    state.sweep_unmeasured_after_stop()
    write_run_done(state, exit_code)
    return exit_code


def do_stage(argv) -> int:
    """Run exactly one stage on the inputs in --in, writing only under --out."""
    stage = argv.stage
    if stage not in STAGE_FUNCTIONS:
        print(f"[m4] FATAL: no stage named {stage}", file=sys.stderr)
        return EXIT_INFRA
    state, base = build_state(argv, indir=Path(argv.indir) if argv.indir else None)
    if state is None:
        return EXIT_INFRA
    if argv.indir:
        state.indir = Path(argv.indir)
        load_prior_state(state)
    fn, gpu = STAGE_FUNCTIONS[stage]
    try:
        with StageTimer(state, stage, gpu=gpu):
            fn(state)
    except GuardStop as stop:
        state.record_stop("guard", stop.stage or stage, stop.reason)
        state.exit_code = EXIT_GUARD
    except (FrameGuardReject, HarnessFailure, ParseError, ValueError) as exc:
        if isinstance(exc, FrameGuardReject):
            reason = f"the frame guard refused a pose: {exc.reason}"
            state.failure_kind = "anchor_frame"
        elif isinstance(exc, HarnessFailure):
            reason = f"{exc.reason}: {exc.detail}" if exc.detail else exc.reason
            state.failure_kind = exc.kind
        else:
            reason = f"broken tool output could not be read: {exc}"
            state.failure_kind = "parse_error"
        state.void_run(reason)
        state.exit_code = EXIT_INFRA
        print(f"[m4] {stage} failed: {reason}", file=sys.stderr)
    if state.exit_code is None:
        if stage == "endpoints":
            state.exit_code = decide_exit_code(state)
        elif state.anchor_missed and stage == "anchor":
            state.exit_code = EXIT_ANCHOR
        else:
            state.exit_code = EXIT_OK
    close_stage_invocation(state, stage, state.exit_code)
    return state.exit_code


def do_run(argv) -> int:
    state, base = build_state(argv)
    if state is None:
        return EXIT_INFRA
    if argv.finalize:
        code = finalize_from_disk(state, outer_rc=argv.outer_rc or 124)
        write_run_done(state, code)
        print(f"[m4] closed after the launcher's timeout: exit {code}")
        return code
    print(f"[m4] start {utc_now()} stop_at {state.stop_at_s:.0f}s "
          f"({state.caps['binding']} cap), price {state.price_usd_per_hour}/h")
    code = run_stages(state, outer_rc=argv.outer_rc)
    try:
        state.runner.kill_all_groups()
    except Exception:
        pass
    write_run_done(state, code)
    print(f"[m4] done exit {code} run_valid {state.run_valid} "
          f"elapsed {state.elapsed_s():.0f}s")
    return code


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", action="store_true", help="run on the rented box")
    parser.add_argument("--stage", default=None, help="run exactly one stage")
    parser.add_argument("--in", dest="indir", default=None,
                        help="the directory holding the stage's inputs")
    parser.add_argument("--out", dest="outdir", default=None,
                        help="the directory the stage writes to")
    parser.add_argument("--base", default=None, help="the payload directory")
    parser.add_argument("--workdir", default=None)
    parser.add_argument("--datadir", default=None)
    parser.add_argument("--outer-rc", type=int, default=None,
                        help="exit code of the launcher's own timeout, if it fired")
    parser.add_argument("--finalize", action="store_true",
                        help="write the closing records after the launcher's own "
                             "timeout ended the measuring run")
    parser.add_argument("--selftest", action="store_true",
                        help="run the stdlib-only checks and exit")
    args = parser.parse_args(argv)
    if args.selftest:
        return selftest()
    if args.stage:
        return do_stage(args)
    if args.run or args.finalize:
        return do_run(args)
    parser.print_help()
    return EXIT_INFRA


# ===========================================================================
# SELFTEST
# Stdlib only: no graphics processor, no network, no heavy library is
# imported. Every parser, every degenerate-output detector and each input's
# arithmetic are checked on planted values with known outcomes.
# ===========================================================================


class _FakeRunner:
    """A tool runner that starts nothing: labels fall back to null and reason."""

    def capture(self, cmd, **kw):
        return {"ok": False, "rc": None, "timed_out": False, "started": False,
                "seconds": 0.0, "stdout": "", "stderr": "selftest runs no tool",
                "log": "", "cmd": [str(c) for c in cmd]}

    def kill_all_groups(self):
        return []


class _FakeProvenance:
    """The record writer's shape, without reading the frozen file."""

    @staticmethod
    def describe_input(path, n_items=None):
        p = Path(path)
        if not p.exists():
            return {"path": str(p), "present": False, "sha256": None,
                    "n_items": n_items}
        return {"path": str(p), "present": True, "sha256": sha256_file(p)[:12],
                "bytes": p.stat().st_size, "n_items": n_items}

    @staticmethod
    def write_result(out_path, *, cell, inputs, metric, values, threshold,
                     decision_rule, decision, notes="", rows=None):
        rec = {"cell": cell, "inputs": inputs, "metric": metric, "values": values,
               "threshold": threshold, "decision_rule": decision_rule,
               "decision": decision, "notes": notes,
               "env": {"timestamp_utc": "2026-01-01T00:00:00Z", "host": "selftest",
                       "python": "3", "git_rev": None}}
        if rows is not None:
            rec["rows"] = rows
        Path(out_path).write_text(json.dumps(rec, indent=2, sort_keys=True))
        return Path(out_path)


def _selftest_parsers(tmp: Path) -> list:
    fails = []

    def write(name, text):
        p = tmp / name
        p.write_text(text)
        return p

    got = parse_nvidia_smi_header(write(
        "smi.txt",
        "| NVIDIA-SMI 570.148.08   Driver Version: 570.148.08   CUDA Version: 12.8 |\n"))
    if got != {"driver_version": "570.148.08", "cuda_version_header": "12.8"}:
        fails.append(f"parse_nvidia_smi_header: {got}")
    got = parse_nvidia_smi_query(write("q.txt", "NVIDIA A100-SXM4-40GB, 570.148.08\n"))
    if got != {"gpu_name": "NVIDIA A100-SXM4-40GB", "driver_version": "570.148.08"}:
        fails.append(f"parse_nvidia_smi_query: {got}")
    if parse_etimes(write("et.txt", "300\n")) != {"seconds": 300}:
        fails.append("parse_etimes good")
    try:
        parse_etimes(write("et_bad.txt", "abc\n"))
        fails.append("parse_etimes accepted a non-integer")
    except ValueError:
        pass
    got = parse_colabfold_log(write("cf.log", "model 1 took 12.5 s\n"
                                              "model 2 took 13.0 s\n"))
    if got["per_model_s"] != [12.5, 13.0] or got["download_in_timed_call"]:
        fails.append(f"parse_colabfold_log: {got}")
    got = parse_colabfold_log(write("cf2.log", "downloading params\n"))
    if not got["download_in_timed_call"]:
        fails.append("parse_colabfold_log missed a download")
    rep = ('#"Step","Potential Energy (kJ/mole)","Speed (ns/day)"\n'
           '5000,-1.0,128.96\n252000,-2.0,129.10\n')
    got = parse_reporter_file(write("rep.csv", rep))
    if got["ns_per_day"] != 129.10 or got["last_step"] != 252000 \
            or not got["energies_finite"]:
        fails.append(f"parse_reporter_file: {got}")
    rep_nan = ('#"Step","Potential Energy (kJ/mole)","Speed (ns/day)"\n'
               '5000,nan,128.96\n')
    got = parse_reporter_file(write("rep_nan.csv", rep_nan))
    if got["energies_finite"]:
        fails.append("parse_reporter_file missed a NaN energy")
    got = parse_engine_rate_line(write("rate.txt", "Speed (ns/day): 128.96\n"))
    if got["ns_per_day"] != 128.96:
        fails.append(f"parse_engine_rate_line: {got}")
    got = parse_engine_rate_line(write("rate_none.txt", "no rate here\n"))
    if got["ns_per_day"] is not None or not got["reason"]:
        fails.append(f"parse_engine_rate_line missing: {got}")

    # Rank table: the planted shapes of the directive.
    t1 = ("#Coordinates RecID LigID Luciferin Neighbor's number Vision Range Scoring\n"
          "1 1 1 1 5 10 2.5\n2 2 2 2 6 11 1.5\n")
    got = parse_rank_table(write("rank1.list", t1))
    if got["n_rows"] != 2 or got["mapping"] != "positional":
        fails.append(f"rank1: {got['n_rows']} {got['mapping']}")
    if got["top"] != got["rows"][0]:
        fails.append("rank1: top row is not the first row written")
    if len(got["rows"]) != 2:
        fails.append("rank1: rows were dropped")
    t2 = ("Swarm Glowworm Scoring\n1 3 -123.4\n2 4 -120.0\n")
    got = parse_rank_table(write("rank2.list", t2))
    if got["mapping"] != "by_name":
        fails.append(f"rank2 mapping: {got['mapping']}")
    pose = pose_path_from_row(Path("/work"), got["top"])
    if pose != Path("/work/swarm_1/lightdock_3.pdb"):
        fails.append(f"rank2 pose path: {pose}")
    try:
        parse_rank_table(write("rank3.list", "Swarm Glowworm Scoring\n"))
        fails.append("rank3: a header with no data row was accepted")
    except ValueError as exc:
        if "0 lines follow" not in str(exc) and "1 lines follow" not in str(exc):
            fails.append(f"rank3: the error text lacks the line count: {exc}")
        if "first 5 raw lines" not in str(exc):
            fails.append(f"rank3: the error text lacks the raw lines: {exc}")
    try:
        parse_rank_table(write("rank4.list",
                               "A B C D E F Scoring\n1 2 3 4 5 6 1.0\n"
                               "1 2 3 4 5 6 7 1.0\n"))
        fails.append("rank4: mixed field counts were accepted")
    except ValueError as exc:
        if "6" not in str(exc) or "7" not in str(exc):
            fails.append(f"rank4: the error text lacks both counts: {exc}")
    try:
        parse_rank_table(write("rank5.list",
                               "Swarm Glowworm Scoring\n1 1 1.0\n2 2 3.0\n"
                               "3 3 2.0\n"))
        fails.append("rank5: a rising-then-falling score column was accepted")
    except ValueError:
        pass
    try:
        parse_rank_table(write("rank6.list", "Swarm Glowworm Scoring\nx y z\n"))
        fails.append("rank6: a non-numeric last column was accepted as data")
    except ValueError:
        pass

    pdb_text = ("ATOM      1  N   ALA A   1       0.000   0.000   0.000  1.00  0.00           N\n"
                "ATOM      2  CA  ALA A   1       1.000   0.000   0.000  1.00  0.00           C\n"
                "ATOM      3  C   ALA A   1       2.000   0.000   0.000  1.00  0.00           C\n"
                "ATOM      4  O   ALA A   1       3.000   0.000   0.000  1.00  0.00           O\n"
                "END\n")
    got = parse_pdb(write("mini.pdb", pdb_text))
    if got["n_atoms"] != 4 or ("A", 1, "", "CA") not in got["by_key"]:
        fails.append(f"parse_pdb: {got['n_atoms']}")

    rows_file = write("rows.jsonl", '{"pair":"p1","wallclock_s":1800}\n')
    got = parse_af2_timing_rows(rows_file)
    if got["n"] != 1 or abs(got["mean_h"] - 0.5) > 1e-9:
        fails.append(f"parse_af2_timing_rows: {got}")
    return fails


def _selftest_anchor(tmp: Path) -> list:
    fails = []
    atoms_a = []
    atoms_b = []
    for i in range(6):
        atoms_a.append({"name": "CA", "chain": "A", "resseq": i + 1, "icode": "",
                        "x": float(i), "y": 0.0, "z": 0.0, "element": "C",
                        "resname": "ALA", "record": "ATOM", "serial": str(i)})
        # Receptor residues 1 to 3 sit at the interface; 4 to 6 sit far away.
        y = 2.0 if i < 3 else 20.0
        atoms_b.append({"name": "CA", "chain": "B", "resseq": i + 1, "icode": "",
                        "x": float(i), "y": y, "z": 0.0, "element": "C",
                        "resname": "ALA", "record": "ATOM", "serial": str(i)})
    for coll in (atoms_a, atoms_b):
        for a in coll:
            a.setdefault("role", "capsid" if a["chain"] == "A" else "receptor")
    native = atoms_a + atoms_b
    ref = contact_pairs_by_index(native)
    if not ref:
        fails.append("the planted complex makes no reference contact")
    if abs(contact_overlap({1, 2, 3, 4, 5, 6}, {1, 2, 3}) - 0.5) > 1e-9:
        fails.append("contact_overlap 3 of 6 is not 0.5")
    if abs(contact_overlap(ref, ref) - 1.0) > 1e-9:
        fails.append("contact_overlap self is not 1.0")

    moved = [dict(a, x=a["x"] + 5.0) for a in native
             if a["role"] == "receptor"]
    iface = interface_backbone_rmsd(native, atoms_a + moved)
    if abs(iface - 5.0) > 1e-6:
        fails.append(f"interface_backbone_rmsd 5 A shift: {iface}")
    far = [dict(a, x=a["x"] + 20.0) for a in native if a["role"] == "receptor"
           and a["resseq"] not in (1, 2, 3)]
    near = [a for a in native if a["role"] == "receptor" and a["resseq"] in (1, 2, 3)]
    iface = interface_backbone_rmsd(native, atoms_a + near + far)
    if abs(iface) > 1e-9:
        fails.append(f"interface RMSD must ignore non-interface atoms: {iface}")
    whole = whole_chain_rmsd(native, atoms_a + near + far)
    if whole <= 0:
        fails.append("whole-chain RMSD must see the moved non-interface atoms")

    v = anchor_decision(0.50, 9.0, 1.0, True)
    if v["decision"] != "PASS":
        fails.append("anchor (0.50, 9.0) must pass")
    v = anchor_decision(0.49, 5.0, 1.0, True)
    if v["decision"] != "PASS":
        fails.append("anchor (0.49, 5.0) must pass")
    v = anchor_decision(0.49, 5.01, 1.0, True)
    if v["decision"] != "FAIL":
        fails.append("anchor (0.49, 5.01) must fail")
    v = anchor_decision(0.9, 1.0, 2.0, True)
    if v["decision"] != "PASS":
        fails.append("serial-parallel 2.0 with equal calls must pass")
    v = anchor_decision(0.9, 1.0, 2.01, True)
    if v["decision"] != "FAIL":
        fails.append("serial-parallel 2.01 must fail")
    v = anchor_decision(0.9, 1.0, 0.0, False)
    if v["decision"] != "FAIL":
        fails.append("different calls must fail")

    # The frame: a translation scores perfectly and passes the guard.
    shift = pose_frame_shift(atoms_a, [dict(a, x=a["x"] - 12.0, y=a["y"] + 3.0)
                                       for a in atoms_a])
    frame_guard(shift)
    if abs(shift["residual_rmsd_a"]) > 1e-6:
        fails.append(f"translated copy residual: {shift['residual_rmsd_a']}")
    self_shift = pose_frame_shift(atoms_a, atoms_a)
    if (self_shift["dx"], self_shift["dy"], self_shift["dz"]) != (0.0, 0.0, 0.0):
        fails.append(f"self-score shift must be zero: {self_shift}")
    frame_guard(self_shift)
    rotated = _rotate(native, _rotation_matrix((0.0, 0.0, 1.0), math.radians(35.0)))
    rot_cap = [a for a in rotated if a["role"] == "capsid"]
    try:
        frame_guard(pose_frame_shift(atoms_a, rot_cap))
        fails.append("a rotated copy passed the frame guard")
    except FrameGuardReject:
        pass
    try:
        frame_guard(pose_frame_shift(atoms_a, atoms_a[1:]))
        fails.append("a pose missing too many capsid atoms passed the guard")
    except FrameGuardReject:
        pass
    many = [dict(a, resseq=i + 1, x=float(i), y=0.0, z=0.0)
            for i in range(200)]
    one_missing = pose_frame_shift(many, many[:-1])
    frame_guard(one_missing)

    # The independent scorer agrees with the runner's on a self-score and a
    # 5 angstrom shift.
    text = write_pdb([dict(a, record="ATOM", resname="ALA") for a in native])
    moved_text = write_pdb(
        [dict(a, record="ATOM", resname="ALA",
              x=a["x"] + (5.0 if a["role"] == "receptor" else 0.0))
         for a in native])
    indep = independent_anchor_score(text, text)
    if abs(indep["overlap"] - 1.0) > 1e-9 or indep["interface_backbone_rmsd_a"] > 1e-6:
        fails.append(f"independent self-score: {indep}")
    indep2 = independent_anchor_score(text, moved_text)
    if abs(indep2["interface_backbone_rmsd_a"] - 5.0) > 1e-6:
        fails.append(f"independent 5 A shift: {indep2}")
    runner = score_pose_against_native(native, text, atoms_a)
    if abs(runner["overlap"] - 1.0) > 1e-9:
        fails.append(f"runner self-score overlap: {runner['overlap']}")
    agree = scorer_agreement(runner, indep)
    if not agree["ok"]:
        fails.append(f"scorers disagree on the self-score: {agree}")
    return fails


def _selftest_band(tmp: Path) -> list:
    fails = []
    for value, want in [(0.5, "PASS"), (1.5, "FAIL"), (0.1, "FAIL"),
                        (1.2, "VOID"), (0.21, "VOID"), (1.1, "PASS"),
                        (0.9, "PASS")]:
        got = decide_band(value, CARD["C1"]["band"])
        if got["decision"] != want:
            fails.append(f"decide_band C1 {value} -> {got['decision']} want {want}")
    g = gate_on_c1(1.2, "VOID", True)
    if g["gate_pass"] is not False:
        fails.append("gate on a marginal 1.2 must be false")
    g = gate_on_c1(1.1, "PASS", False)
    if g["gate_pass"] is not False or g["gate_else"] != GATE_ELSE:
        fails.append(f"gate on 1.1: {g}")
    g = gate_on_c1(0.9, "PASS", False)
    if g["gate_pass"] is not True:
        fails.append("gate on 0.9 must be true")
    g = gate_on_c1(None, "VOID", False)
    if g["gate_pass"] is not None or g["gate_value"] != 1:
        fails.append(f"gate on a void: {g}")

    for value, want in [(100.0, "PASS"), (40.0, "FAIL"), (400.0, "FAIL"),
                        (56.0, "VOID"), (60.0, "PASS"), (330.0, "VOID"),
                        (129.0, "PASS")]:
        got = decide_band(value, CARD["C2"]["band"])
        if got["decision"] != want:
            fails.append(f"decide_band C2 {value} -> {got['decision']} want {want}")
    rate = ns_per_day_from_wallclock(250000, 2.0, 335)
    if abs(rate - 128.96) > 0.01:
        fails.append(f"ns/day from 335 s: {rate}")
    if statistics.median([100, 129, 500]) != 129:
        fails.append("median of (100, 129, 500)")

    for value, want in [(1.0, "PASS"), (0.2, "FAIL"), (4.0, "FAIL"),
                        (0.3333, "VOID"), (3.2, "VOID"), (0.5, "PASS"),
                        (2.5, "PASS")]:
        got = decide_band(value, CARD["C3"]["band"])
        if got["decision"] != want:
            fails.append(f"decide_band C3 {value} -> {got['decision']} want {want}")

    s = storage_from_bytes(BYTES_PER_GIB)
    if abs(s["gib_216_runs"] - 216.0) > 1e-9 or abs(s["gib_432_runs"] - 432.0) > 1e-9:
        fails.append(f"storage from 1 GiB: {s}")
    for value, want in [(216.0, "PASS"), (21.6, "FAIL"), (864.0, "FAIL"),
                        (626.4, "VOID"), (75.6, "PASS")]:
        got = decide_band(value, CARD["C4"]["band"])
        if got["decision"] != want:
            fails.append(f"decide_band C4 {value} -> {got['decision']} want {want}")

    if abs(cost_usd(3600, 1.99) - 1.99) > 1e-9:
        fails.append(f"cost 3600 s at 1.99: {cost_usd(3600, 1.99)}")
    if abs(cost_usd(7200, 1.99) - 3.98) > 1e-9:
        fails.append(f"cost 7200 s at 1.99: {cost_usd(7200, 1.99)}")
    caps = stop_at_seconds(1.99, 5, 7200)
    if caps["stop_at_s"] != 7200 or caps["binding"] != "time":
        fails.append(f"caps at 1.99: {caps}")
    caps = stop_at_seconds(2.50, 5, 7200)
    if caps["stop_at_s"] != 7200:
        fails.append(f"caps at 2.50: {caps}")
    caps = stop_at_seconds(3.00, 5, 7200)
    if caps["stop_at_s"] != 6000 or caps["binding"] != "dollars":
        fails.append(f"caps at 3.00: {caps}")

    class _S:
        remote_timeout_s = 7200.0
        stop_at_s = 7200.0
        group_seconds = {}
        def elapsed_s(self):
            return self._elapsed
    st = _S()
    st._elapsed = 0.0
    if stage_allowance_s(st, "capability") != 1500:
        fails.append(f"setup allowance at 0: {stage_allowance_s(st, 'capability')}")
    if stage_allowance_s(st, "controls") != 1000:
        fails.append(f"controls allowance at 0: {stage_allowance_s(st, 'controls')}")
    if stage_allowance_s(st, "anchor") != 1000:
        fails.append(f"anchor allowance at 0: {stage_allowance_s(st, 'anchor')}")
    st._elapsed = 6000.0
    if stage_allowance_s(st, "af2") != 700:
        fails.append(f"af2 allowance at 6000: {stage_allowance_s(st, 'af2')}")
    st._elapsed = 6800.0
    if stage_allowance_s(st, "af2") != 0:
        fails.append(f"af2 allowance at 6800: {stage_allowance_s(st, 'af2')}")
    return fails


def _selftest_harness(tmp: Path) -> list:
    fails = []
    error = abs(62.9 - 60.0) / 60.0
    if error > SLEEP_CONTROL_TOLERANCE:
        fails.append("62.9 s must pass the sleep check")
    error = abs(63.1 - 60.0) / 60.0
    if error <= SLEEP_CONTROL_TOLERANCE:
        fails.append("63.1 s must fail the sleep check")
    spread = spread_check({"p1": [1800, 1830, 1790]})
    if spread["halt"] is not None or spread["zero_spread_pairs"]:
        fails.append(f"spread (1800, 1830, 1790): {spread}")
    spread = spread_check({"p1": [1800, 1800, 1800]})
    if spread["halt"] != WRONG_VARIANCE_SOURCE:
        fails.append(f"zero spread must halt as {WRONG_VARIANCE_SOURCE}: {spread}")
    rsd = relative_sd([1000.0, 2474.0])
    if rsd is None or not (0.55 <= rsd <= 0.65):
        fails.append(f"relative sd of the planted pair must be about 0.6: {rsd}")
    spread = spread_check({"p1": [1000.0, 2474.0]})
    if spread["halt"] is not None or not spread["high_spread_pairs"]:
        fails.append(f"a 0.6 relative sd gives the spread label only: {spread}")
    if not rates_disagree(100.0, 129.0):
        fails.append("rates 100 and 129 must disagree")
    if rates_disagree(129.0, 129.0):
        fails.append("equal rates must agree")
    md = md_bytes_breakdown  # noqa: F841  (named for the reader)
    return fails


def _selftest_calibration(tmp: Path) -> list:
    fails = []
    ctx = {"sleep_ok": True, "gpu_visible": True, "gpu_name": "A100",
           "gpu_is_a100": True, "stages_before_ok": True,
           "anchor_docking_parameters": {"swarms": 2, "glowworms": 20,
                                         "steps": 20, "setup_flags": ["--noxt", "--noh"]}}

    def af2_row(pair, seed, wall=1800, **kw):
        row = {"pair": pair, "seed": seed, "wallclock_s": wall,
               "fasta_length": 870, "models": 5, "recycles": 20,
               "early_stopping": "off", "msa_mode": "single_sequence",
               "rc": 0, "n_model_structures": 5, "n_score_files": 5,
               "structures_parse_ok": True, "score_files_parse_ok": True,
               "per_model_s": [10.0, 9.0], "download_in_timed_call": False,
               "incomplete": False}
        row.update(kw)
        return row

    rows = [af2_row("pair1", 0), af2_row("pair1", 1, 1830),
            af2_row("pair1", 2, 1790), af2_row("pair2", 0),
            af2_row("pair2", 1, 1830), af2_row("pair2", 2, 1790),
            af2_row("pair3", 0), af2_row("pair3", 1, 1830),
            af2_row("pair3", 2, 1790)]
    cal = calibration_checks_c1(rows, ctx)
    if not cal["calibration_valid"]:
        fails.append(f"well-formed C1 rows must be calibration-valid: {cal}")
    bad = [af2_row("pair1", 0, n_score_files=4, score_files_parse_ok=False)]
    cal = calibration_checks_c1(bad, ctx)
    if cal["calibration_valid"]:
        fails.append("a missing score file must void the C1 record")
    zero = [af2_row("pair1", 0), af2_row("pair1", 1),
            af2_row("pair1", 2), af2_row("pair2", 0),
            af2_row("pair2", 1), af2_row("pair2", 2),
            af2_row("pair3", 0), af2_row("pair3", 1),
            af2_row("pair3", 2)]
    cal = calibration_checks_c1(zero, ctx)
    if cal["calibration_valid"]:
        fails.append("zero spread across seeds must void the C1 record")
    if LABEL_ZERO_SPREAD not in json.dumps(cal):
        fails.append("zero spread must name the wrong-variance-source reason")

    def md_row(complex_, atoms=150000, **kw):
        row = {"complex": complex_, "atoms": atoms, "incomplete": False,
               "production_wallclock_s": 335.0,
               "roles_present": True, "capsid_heavy_atoms": 4000,
               "reporter_last_step": 252000, "energies_finite": True,
               "trajectory_frames": 50, "platform": "CUDA",
               "precision": "mixed"}
        row.update(kw)
        return row

    rows = [md_row("pair1"), md_row("pair2")]
    cal = calibration_checks_c2(rows, ctx)
    if not cal["calibration_valid"]:
        fails.append(f"well-formed C2 rows must be calibration-valid: {cal}")
    cal = calibration_checks_c2([md_row("pair1", 119999), md_row("pair2")], ctx)
    if cal["calibration_valid"]:
        fails.append("119,999 atoms must void the C2 record")
    cal = calibration_checks_c2(
        [md_row("pair1", energies_finite=False), md_row("pair2")], ctx)
    if cal["calibration_valid"]:
        fails.append("a NaN energy must void the C2 record")
    cal = calibration_checks_c2(
        [md_row("pair1", trajectory_frames=48), md_row("pair2")], ctx)
    if cal["calibration_valid"]:
        fails.append("48 frames must void the C2 record")

    def aux_row(pair, **kw):
        row = {"pair": pair, "seconds": 1800.0, "truncated": False,
               "incomplete": False,
               "docking_parameters": {"swarms": 2, "glowworms": 20, "steps": 20,
                                      "setup_flags": ["--noxt", "--noh"]},
               "rank_table_parsed": True, "rank_rows": 2,
               "top_pose_exists": True, "top_pose_roles_ok": True,
               "contacts_at_4p5": True, "interface_residues_written": True,
               "threefold_distance_written": True, "site_class_written": True,
               "call_table_row_written": True}
        row.update(kw)
        return row

    rows = [aux_row("pair1"), aux_row("pair2")]
    cal = calibration_checks_c3(rows, ctx)
    if not cal["calibration_valid"]:
        fails.append(f"well-formed C3 rows must be calibration-valid: {cal}")
    cal = calibration_checks_c3(
        [aux_row("pair1", docking_parameters={"swarms": 3}),
         aux_row("pair2")], ctx)
    if cal["calibration_valid"]:
        fails.append("docking parameters unlike the anchor's must void C3")
    cal = calibration_checks_c3([aux_row("pair1", truncated=True), aux_row("pair2")], ctx)
    if cal["calibration_valid"]:
        fails.append("a pair that hit its limit must void C3")

    rows = [{"kind": "af2", "bytes": 1000, "counts_in": True, "source": "a"},
            {"kind": "docking", "bytes": 1000, "counts_in": True, "source": "d"},
            {"kind": "md", "bytes": 1000, "counts_in": True, "source": "m",
             "md_setup_bytes": 12000}]
    cal = calibration_checks_c4(rows, ctx)
    if not cal["calibration_valid"]:
        fails.append(f"well-formed C4 rows must be calibration-valid: {cal}")
    cal = calibration_checks_c4(
        [{"kind": "af2", "bytes": 0, "counts_in": True, "source": "a"},
         {"kind": "docking", "bytes": 10, "counts_in": True, "source": "d"},
         {"kind": "md", "bytes": 10, "counts_in": True, "source": "m"}], ctx)
    if cal["calibration_valid"]:
        fails.append("a zero-byte artifact type must void C4")
    return fails


def _selftest_gate_and_records(tmp: Path) -> list:
    """A planted gate failure must set run_valid false in every later record."""
    fails = []
    outdir = tmp / "out"
    workdir = tmp / "work"
    datadir = tmp / "data"
    env = {"PRICE_USD_PER_HOUR": "1.99", "BUDGET_LEFT_USD": "5",
           "REMOTE_TIMEOUT": "7200", "M4_T0_EPOCH": str(time.time()),
           "INSTANCE_TYPE": "gpu_1x_a100_sxm4", "ENV_LOCK_SHA256": "0" * 64,
           "M4_ENV_LOCK_OBSERVED": "0" * 64}
    state = RunState(outdir, workdir, datadir, env=env,
                     provenance=_FakeProvenance, clock=time.time)
    state.runner = _FakeRunner()
    state.sleep_ok = True
    state.gpu_visible = True
    state.gpu_name = "NVIDIA A100-SXM4-40GB"
    state.gpu_is_a100 = True
    # The gate fails: the anchor missed its tolerance.
    state.void_run("the anchor redocking missed its tolerance against the "
                   "published placement")
    state.anchor_missed = "the anchor redocking missed its tolerance"
    rows = [{"pair": f"pair{i % 3 + 1}", "seed": i % 3,
             "wallclock_s": 1800 + 30 * (i % 3), "fasta_length": 870,
             "models": 5, "recycles": 20, "early_stopping": "off",
             "msa_mode": "single_sequence", "rc": 0,
             "n_model_structures": 5, "n_score_files": 5,
             "structures_parse_ok": True, "score_files_parse_ok": True,
             "per_model_s": [10.0], "download_in_timed_call": False,
             "incomplete": False} for i in range(9)]
    emit_input_record(state, "C1", 0.5, n=9, rows_arm="af2",
                      start_epoch=state.t0, end_epoch=state.clock(),
                      rows=rows, extra_values={"runs_counted": 9})
    rec = json.loads((outdir / "endpoint-C1_tag-m4.json").read_text())
    if rec.get("run_valid") is not False:
        fails.append(f"a gate failure must set run_valid false: {rec.get('run_valid')}")
    if not rec.get("run_valid_voided_by"):
        fails.append("a gate failure must name what voided the run")
    if LABEL_AFTER_ANCHOR_MISS not in json.dumps(rec.get("notes_list") or []):
        fails.append("a record after an anchor miss must carry that label")
    if rec.get("decision") not in ("PASS", "FAIL", "VOID"):
        fails.append(f"the decision word is wrong: {rec.get('decision')}")
    if not rec["values"].get("calibration_checks"):
        fails.append("the record must carry its calibration checks")
    if rec.get("calibration_valid") is False and rec["values"]["measured"] != 0.5:
        fails.append("a void must keep the raw value in measured")
    status = state.inputs_status["C1"]["status"]
    if status.startswith("void_by_anchor_miss"):
        fails.append(f"there is no void-by-anchor-miss status: {status}")
    return fails


def _selftest_compute(tmp: Path) -> list:
    fails = []
    outdir = tmp / "compute_out"
    workdir = tmp / "compute_work"
    datadir = tmp / "compute_data"
    env = {"PRICE_USD_PER_HOUR": "1.99", "REMOTE_TIMEOUT": "7200"}
    state = RunState(outdir, workdir, datadir, env=env,
                     provenance=_FakeProvenance, clock=time.time)
    with StageTimer(state, "controls", gpu=False):
        pass
    table = build_compute_table(state)
    names = [e["stage"] for e in table["stages"]]
    if names != STAGE_ORDER:
        fails.append(f"the compute table lists {names}")
    for entry in table["stages"]:
        if entry["stage"] == "controls":
            if not entry["ran"] or entry["wall_clock_s"] is None:
                fails.append(f"the run stage was not closed: {entry}")
        elif entry["ran"]:
            fails.append(f"a stage that did not run is marked ran: {entry}")
        elif not entry.get("reason"):
            fails.append(f"a stage that did not run carries no reason: {entry}")
    if "instance_type" not in table or "estimated_spend_usd" not in table:
        fails.append("the compute table lacks the money fields")
    return fails


def selftest() -> int:
    """Check the parsers, the detectors and the arithmetic. Exit non-zero on a
    failure. Nothing here describes two runs on one box as replication."""
    import tempfile
    fails = []
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        fails += _selftest_parsers(tmp)
        fails += _selftest_anchor(tmp)
        fails += _selftest_band(tmp)
        fails += _selftest_harness(tmp)
        fails += _selftest_calibration(tmp)
        fails += _selftest_gate_and_records(tmp)
        fails += _selftest_compute(tmp)
    for f in fails:
        print("FAIL", f)
    print("selftest:", "PASS" if not fails else f"{len(fails)} FAILURES")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
