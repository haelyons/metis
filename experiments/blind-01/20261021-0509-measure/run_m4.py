#!/usr/bin/env python3
"""Measure four cost inputs of one research card on one rented GPU box.

WHAT THIS PROGRAM IS FOR

A research card plans a large structure-prediction study. Its cost rests on four
numbers that nobody measured. This program measures those four numbers once, on
one rented box, and reads each against the band the card itself allows.

The four numbers, with the card's own value and band:

  C1  hours of wall-clock per AlphaFold-Multimer prediction run   0.5   [0.2, 1.25]
  C2  molecular-dynamics speed, nanoseconds simulated per day     129   [51.6, 322.5]
  C3  auxiliary hours per capsid-receptor pair                    1     [0.3333, 3]
  C4  storage in gibibytes for the planned grid of 216 runs       200   [66.67, 600]

Before any of the four is measured the program must reproduce a published
result: redocking the receptor domain AAVR-PKD2 onto the capsid AAV2 must land
beside the same spike as Protein Data Bank entry 6IHB. That check is called the
anchor. A missed anchor voids every later number.

WHAT THIS PROGRAM DOES NOT DO

It does not run the card's planned study. It does not run the card's 54-run
pilot or its 216-run grid. It measures a stand-in protocol built from chains of
one structure, on one graphics processor, and says so in every file it writes.
Two runs on the same box are two samples of one box; this program never calls
that replication.

HOW A READER CHECKS IT

Every number has exactly one home: a result record written by the shared record
writer in frozen/provenance.py. Each record carries the rule that decides it,
written before the values, the files it was computed from with their hashes, the
labels of the machine it ran on, and a true-or-false field `run_valid`. When the
anchor misses, or the timing harness itself is shown to be wrong, `run_valid`
becomes false in that record and in every record written after it, not only in
the summary. A void that lives in one file is not a void.

Raw measurements are saved one per line, verbatim, beside the records.

USAGE

  python3 run_m4.py --run          # the real run; only on the rented box, through onbox_m4.sh

The measurement logic is checked by tests/tests_m4.py, written by someone who
never saw this program and run on the box before any physics.

Decision words used in records: PASS (inside the band), FAIL (outside it), VOID
(not decidable: too few samples, a marginal value, a stop, or a wrong machine).

Exit codes: 0 finished; 2 broken infrastructure or a broken harness; 3 a guard,
a stage ceiling or a timeout stopped the run; 4 the anchor missed.
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
import tempfile
import time
from pathlib import Path

TAG = "m4"

# ---------------------------------------------------------------------------
# The card's own numbers. These are copied from the design record and are not
# recomputed here; the tests written from the directive check them.
# ---------------------------------------------------------------------------

CARD = {
    "C1": {
        "key": "af2_h_per_run",
        "unit": "hours per AlphaFold-Multimer run",
        "card_value": 0.5,
        "band": [0.2, 1.25],
        "basis": "PROXY",
    },
    "C2": {
        "key": "md_ns_per_day_a100",
        "unit": "nanoseconds simulated per day",
        "card_value": 129,
        "band": [51.6, 322.5],
        "basis": "PROXY",
    },
    "C3": {
        "key": "aux_h_per_pair",
        "unit": "hours per capsid-receptor pair",
        "card_value": 1,
        "band": [0.3333, 3],
        "basis": "GUESS",
    },
    "C4": {
        "key": "n_storage_gib",
        "unit": "gibibytes",
        "card_value": 200,
        "band": [66.67, 600],
        "basis": "GUESS",
    },
}

INPUT_IDS = ["C1", "C2", "C3", "C4"]

# The card's gate. It is applied to C1 only; C2 and C3 say so in words.
GATE_EXPRESSION = "af2_h_per_run <= 1"
GATE_ELSE = (
    "take the docking-plus-MD fallback line with one AlphaFold-Multimer seed "
    "per pair, or move the grid to 12 pairs"
)
GATE_NOT_APPLICABLE = "not applicable: the card's gate is on af2_h_per_run"

# Anchor tolerances, from the published comparison.
ANCHOR_OVERLAP_MIN = 0.50
ANCHOR_IFACE_RMSD_MAX = 5.0
ANCHOR_SERIAL_PARALLEL_RMSD_MAX = 2.0
CONTACT_CUTOFF_A = 4.5

# A value this close to a band edge is reported as marginal, not decided.
MARGINAL_FRACTION = 0.10

# Harness controls.
SLEEP_CONTROL_S = 60.0
SLEEP_CONTROL_TOLERANCE = 0.05
EMPTY_RUN_MAX_S = 2.0
EMPTY_RUN_MAX_BYTES = 1024 * 1024
SEED_SPREAD_HIGH_RSD = 0.50

# The planned grid the storage number is scaled to.
GRID_RUNS = 216
GRID_RUNS_ALT = 432
BYTES_PER_GIB = 2 ** 30

# Sample sizes and protocol constants.
N_PAIRS = 3
AF2_SEEDS = [0, 1, 2]
AF2_MODELS = 5
AF2_RECYCLES = 20
MD_VELOCITY_SEED = 0
MD_PRODUCTION_NS = 0.5
MD_TIMESTEP_FS = 2.0
# The trajectory is written every 5,000 steps, which at a two femtosecond step
# is one frame every 10 picoseconds, fifty frames over the half-nanosecond
# segment. The interval is declared here and recorded on every row and in the
# storage record; it is never tuned to move the storage figure into the band.
MD_REPORT_INTERVAL_STEPS = 5000
MD_FRAME_INTERVAL_PS = MD_REPORT_INTERVAL_STEPS * MD_TIMESTEP_FS / 1000.0
MD_ATOMS_MIN = 120000
MD_ATOMS_MAX = 180000
PAIR_RESIDUES_MIN = 750
PAIR_RESIDUES_MAX = 1000
PAIR_LENGTH_SPREAD_MIN = 20
PAIR_TARGET_LENGTHS = [780, 870, 960]

# Smallest sample each input needs before it can be decided at all.
MIN_AF2_RUNS = 3
MIN_MD_COMPLEXES = 2
MIN_AUX_PAIRS = 2

# ---------------------------------------------------------------------------
# Time and money ceilings, in seconds and dollars.
# ---------------------------------------------------------------------------

TOTAL_CEILING_S = 7200
FETCH_MARGIN_S = 400
ENDPOINTS_SLOT_S = 100

STAGE_CEILING_S = {
    # Setting the environment up, checking what it can do and fetching the
    # declared files share one running total of 1,500 seconds.
    "setup": 1500,
    "tests": 300,          # the hidden author's tests, run before any physics
    "controls": 700,       # the controls and the anchor share this ceiling
    "anchor": 700,
    "aux": 600,
    "af2": 2000,
    "md": 1600,
    "storage": 100,
    "endpoints": ENDPOINTS_SLOT_S,
}
PER_PAIR_DOCKING_CEILING_S = 250
PER_COMPLEX_MD_CEILING_S = 600

# Floor estimates, used before any unit of that kind has finished.
UNIT_FLOOR_S = {
    "anchor_serial": 60,
    "anchor_parallel": 60,
    "docking_pair": 60,
    "af2_run": 120,
    "md_complex": 150,
    "storage": 20,
    "endpoints": 30,
    "tests": 60,
}

DEFAULT_REMOTE_TIMEOUT_S = 7200
DEFAULT_BUDGET_LEFT_USD = 5.0
DEFAULT_PRICE_USD_PER_HOUR = 1.99
BOOTSTRAP_ASSUMED_S = 300

# The gap between the inner tool kill and the outer kill, so the inner fires first.
OUTER_KILL_SLACK_S = 600
INNER_KILL_SLACK_S = 700

# ---------------------------------------------------------------------------
# Fixed label and note strings. They live in one place so that every record
# wording is read from here and never retyped.
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
# Written when a fixer changed the environment on the box and the run restarted
# against a lock that no longer matches the one the launcher forwarded.
LABEL_FIXER_CHANGED_ENV = "environment changed by the fixer on the box; lock %s"
LABEL_HOLD_NOT_FORWARDED = "HOLD_SECONDS not forwarded; no hold"
LABEL_TIMEOUT_NOT_FORWARDED = "REMOTE_TIMEOUT not forwarded; default 7200 used"
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

# Secret-bearing variables. Downloads may use them; no child process sees them.
SECRET_ENV_KEYS = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")

# Non-secret variables that may be echoed into the environment record.
ENV_RECORD_KEYS = (
    "INSTANCE_TYPE",
    "LAMBDA_INSTANCE_ID",
    "GIT_COMMIT",
    "PRICE_USD_PER_HOUR",
    "BUDGET_LEFT_USD",
    "REMOTE_TIMEOUT",
    "M4_T0_EPOCH",
    "M4_PRE_T0_SECONDS",
    "M4_BOOTSTRAP_ASSUMED",
    "M4_SETUP_SECONDS",
    "ENV_DIR",
    "ENV_LOCK_SHA256",
    "HOLD_SECONDS",
    "M4_VENV",
    "PATH",
    "TMPDIR",
    "PIP_CACHE_DIR",
    "XDG_CACHE_HOME",
    "MPLCONFIGDIR",
)

# ---------------------------------------------------------------------------
# LABELS EVERY RECORD CARRIES
#
# A record that does not say which machine and which software produced it is a
# number without a home. Each kind of record this program writes declares here
# exactly which keys its `values.machine` (and, where it applies, its
# `values.engine`) must hold. A key is never left out: a value that could not be
# read is null and `values.null_reasons[<key>]` says why in words.
# ---------------------------------------------------------------------------

# What machine ran it. Every kind of record carries all of these.
MACHINE_KEYS = (
    "instance_type",            # the rented box's own type name
    "gpu_name",                 # the graphics processor, from a runtime query
    "gpu_driver",               # its driver version
    "cuda_runtime_version",     # the "CUDA Version" field of the nvidia-smi banner
    "cuda_plugin_version",      # the version of the installed JAX CUDA plugin package
    "start_utc",                # when the stage that produced the value started
    "end_utc",                  # when it ended; never the record's write time
    "price_usd_per_hour",       # what the box costs per hour
    "expected_lock_sha256",     # the lock the launcher forwarded for the environment
    "observed_lock_sha256",     # the lock computed from the environment on the box
    "venv_path",                # where that environment lives on the attached disk
    "environment_changed_by_fixer",   # true after a fixer changed it and the run restarted
    "held_attempts",            # how many attempts were held open for a fixer
)

# What software produced it. The anchor and the four inputs carry all of these.
ENGINE_KEYS = (
    "alphafold_implementation",
    "alphafold_params_sha256",
    "jax_version",
    "jaxlib_version",
    "jax_cuda_plugin_version",
    "jax_wheel_build_tags",
    "docking_code",
    "docking_version",
    "md_engine",
    "md_engine_version",
    "md_precision",
    "md_platform",
    "build_flags",
)

CONTROL_KINDS = ("control_sleep", "control_empty_run", "control_unit_and_scale")
MEASURED_KINDS = ("anchor", "C1", "C2", "C3", "C4")
# The environment check and the hidden author's tests are records too, and they
# carry the machine-level keys, the lock fields among them.
SETUP_KINDS = ("env_check", "tests")

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

# ---------------------------------------------------------------------------
# Allowed download sources. Nothing else may be fetched.
# ---------------------------------------------------------------------------

PDB_ENTRY = "6IHB"
PDB_URL = "https://files.rcsb.org/download/6IHB.pdb"
AF_PARAMS_URL = (
    "https://storage.googleapis.com/alphafold/alphafold_params_2022-12-06.tar"
)
ALLOWED_DOWNLOAD_HOSTS = ("files.rcsb.org", "storage.googleapis.com")

DOCKING_CODE = "lightdock"

# The docking parameters, identical for the anchor and for every pair, and never
# restrained toward the published interface: the anchor has to find the place on
# its own or it has not reproduced anything.
DOCKING_SWARMS = 2
DOCKING_GLOWWORMS = 20
DOCKING_STEPS = 20

# The order of docking commands: prepare, search, build the structures of the
# poses found, then let the tool rank them. The conformation-generating step is
# what turns the search's numbers into pose files; without it there is no pose
# to compare and the run would end as broken infrastructure at the anchor.
DOCKING_ORDER = [
    "lightdock3_setup.py (prepare)",
    "lightdock3.py (simulate)",
    "lgd_generate_conformations.py (generate the pose structures)",
    "lgd_rank.py (rank)",
]
DOCKING_CORE_STEPS = ["simulate", "generate_conformations", "rank"]

MD_ENGINE = "OpenMM"
MD_PRECISION = "mixed"
MD_PLATFORM = "CUDA"
AF2_IMPLEMENTATION = "ColabFold (colabfold_batch) running AlphaFold-Multimer"


# ---------------------------------------------------------------------------
# Failure kinds. Which one is raised decides the exit code.
# ---------------------------------------------------------------------------


class HarnessFailure(Exception):
    """Broken infrastructure or a broken harness. Exit code 2."""

    def __init__(self, reason: str, detail: str = "", kind: str = ""):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail
        # A short name for the marker, so a reader can tell a setup failure
        # from a tool failure without reading prose.
        self.kind = kind or re.sub(r"[^a-z0-9]+", "_", reason.lower()).strip("_")[:40]


class GuardStop(Exception):
    """A guard, a stage ceiling or a timeout stopped work. Exit code 3."""

    def __init__(self, reason: str, stage: str = "", detail: str = ""):
        super().__init__(reason)
        self.reason = reason
        self.stage = stage
        self.detail = detail


class AnchorMiss(Exception):
    """The anchor was compared and missed its tolerance. Exit code 4."""

    def __init__(self, reason: str, values: dict | None = None):
        super().__init__(reason)
        self.reason = reason
        self.values = values or {}


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


def labelled(value, reason: str):
    """A value that could not be read is null and says why, never omitted."""
    if value is None:
        return None, reason
    return value, None


def apparent_bytes(path) -> int:
    """Sum of the apparent sizes of every regular file under a path.

    Apparent size is the file's length, not the blocks it occupies, because the
    card's storage figure is about data written, not about one filesystem.
    """
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
# PARSERS
# Each one takes text and returns plain data. Nothing here touches the network,
# the graphics processor or the clock, so a reader can follow one input through.
# ===========================================================================


class ParseError(Exception):
    """A tool's output could not be read in the shape this program assumes."""


def parse_nvidia_smi_header(text: str) -> dict:
    """Read the driver version and the driver's CUDA version from the banner.

    The banner line of `nvidia-smi` looks like:
      | NVIDIA-SMI 570.148.08   Driver Version: 570.148.08   CUDA Version: 12.8 |
    The CUDA version there is the highest runtime the driver supports.
    """
    driver = None
    cuda = None
    m = re.search(r"Driver Version:\s*([0-9][0-9.]*)", text)
    if m:
        driver = m.group(1)
    m = re.search(r"CUDA Version:\s*([0-9][0-9.]*)", text)
    if m:
        cuda = m.group(1)
    return {"driver_version": driver, "cuda_version_header": cuda}


def parse_nvidia_smi_query(text: str) -> dict:
    """Read one comma-separated line of `--query-gpu=name,driver_version`."""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2:
            return {"gpu_name": parts[0], "driver_version": parts[1]}
        if parts:
            return {"gpu_name": parts[0], "driver_version": None}
    return {"gpu_name": None, "driver_version": None}


def is_a100(gpu_name) -> bool:
    """True only when the graphics processor is an A100 of some form."""
    if not gpu_name:
        return False
    return "a100" in str(gpu_name).lower()


def parse_etimes(text: str):
    """Read `ps -o etimes=`: whole seconds since a process started, or None."""
    s = (text or "").strip()
    if not s:
        return None
    if not re.fullmatch(r"[0-9]+", s):
        return None
    return int(s)


def parse_colabfold_log(text: str) -> dict:
    """Read a ColabFold run log: per-model seconds, and any download inside it.

    A timed prediction call that downloads or unpacks parameters is not a timing
    of prediction. Such a run is flagged and never counted.
    """
    per_model = []
    for m in re.finditer(r"took\s+([0-9]+(?:\.[0-9]+)?)\s*s", text):
        per_model.append(float(m.group(1)))
    downloaded = bool(
        re.search(
            r"(downloading|download complete|extracting|untarring|fetching params)",
            text,
            re.IGNORECASE,
        )
    )
    return {"per_model_s": per_model, "download_in_timed_call": downloaded}


def parse_reporter_file(text: str) -> dict:
    """Read a molecular-dynamics state reporter file and take its speed column.

    The reporter writes comma-separated columns with a commented header, for
    example:
      #"Step","Potential Energy (kJ/mole)","Temperature (K)","Speed (ns/day)"
    The last row that carries a positive speed is the engine's own rate.
    """
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return {"ns_per_day": None, "n_rows": 0, "reason": "reporter file is empty"}
    header = lines[0].lstrip("#").strip()
    cols = [c.strip().strip('"').strip("'") for c in header.split(",")]
    speed_idx = None
    for i, name in enumerate(cols):
        if "speed" in name.lower() and "ns/day" in name.lower().replace(" ", ""):
            speed_idx = i
            break
    if speed_idx is None:
        for i, name in enumerate(cols):
            if "speed" in name.lower():
                speed_idx = i
                break
    if speed_idx is None:
        return {
            "ns_per_day": None,
            "n_rows": max(0, len(lines) - 1),
            "reason": "no speed column in the reporter header",
        }
    rate = None
    n_rows = 0
    for ln in lines[1:]:
        parts = [p.strip().strip('"') for p in ln.split(",")]
        if len(parts) <= speed_idx:
            continue
        n_rows += 1
        try:
            value = float(parts[speed_idx])
        except ValueError:
            continue
        if value > 0:
            rate = value
    reason = None if rate is not None else "no positive speed value in any row"
    return {"ns_per_day": rate, "n_rows": n_rows, "reason": reason}


def parse_engine_rate_line(text: str):
    """Read a single engine speed line, for example `Speed (ns/day): 128.96`."""
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*ns/day", text, re.IGNORECASE)
    if m:
        return float(m.group(1))
    m = re.search(r"ns/day[^0-9\-]*([0-9]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return None


def ns_per_day_from_wallclock(steps: int, timestep_fs: float, wallclock_s: float):
    """Speed implied by the work done and the clock, independent of the engine.

    steps x timestep is simulated femtoseconds; 86,400 seconds make a day.
    """
    if wallclock_s is None or wallclock_s <= 0:
        return None
    simulated_ns = steps * timestep_fs * 1e-6
    return simulated_ns / wallclock_s * 86400.0


def rates_disagree(engine_rate, wallclock_rate, fraction: float = 0.05) -> bool:
    """True when the engine's own speed and the clock's speed differ too much."""
    if engine_rate is None or wallclock_rate is None:
        return False
    if wallclock_rate == 0:
        return True
    return abs(engine_rate - wallclock_rate) / abs(wallclock_rate) > fraction


SCORE_COLUMN_NAMES = ("scoring", "score", "energy")


class RankTable(list):
    """A docking tool's ranked list, with how its columns were read kept beside it.

    It behaves as a plain list of rows, so `len()` counts the rows the tool
    wrote. The extra attributes say how the fields were named (`by_name` when
    the header names them, `positional` when the rows carry a different number
    of fields and the last column is the score), what the header tokens were,
    and how many fields each data row held.
    """

    def __init__(self, rows, header=(), mapping="", field_count=0,
                 raw_lines=(), rank_key=None, score_key=None):
        super().__init__(rows)
        self.header = list(header)
        self.mapping = mapping
        self.field_count = field_count
        self.raw_lines = list(raw_lines)
        self.rank_key = rank_key
        self.score_key = score_key

    def columns(self) -> dict:
        """What to write into the record, so a reader sees how it was read."""
        return {"header": list(self.header), "row_field_count": self.field_count,
                "mapping": self.mapping}


def header_tokens(line: str) -> list:
    """The header's own words: one leading hash and the blanks around it go."""
    text = line.strip()
    if text.startswith("#"):
        text = text[1:].strip()
    return text.split()


def first_raw_lines(text: str, count: int = 5) -> str:
    """The start of a file, printed exactly as it stands, for an error to carry."""
    lines = text.splitlines()[:count]
    return "first %d raw lines: %s" % (count, "; ".join(repr(l) for l in lines))


def split_fields(line: str) -> list:
    """Split one line of a rank table into the tool's own columns.

    Blanks separate columns, except inside a bracketed group. The docking code
    writes a pose's position as one column holding several numbers in round
    brackets, "(2.088, -26.883, ...)", with blanks inside it. That column is
    one field, not one field for every number in it. Counting its numbers as
    separate fields made a real table of 12 columns look 18 fields wide, so it
    no longer matched its own 12-word header; the row was then read by position
    instead of by name, the column naming the pose file was lost, and the run
    ended with a table the tool had written correctly.
    """
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
    """A data row is any line of at least two fields ending in a number."""
    parts = split_fields(line)
    if len(parts) < 2:
        return False
    try:
        float(parts[-1])
    except ValueError:
        return False
    return True


def rank_table_shape(text: str) -> dict:
    """What a rank table looks like, without judging it. Used for evidence.

    This never raises. It is what the diagnostic file and every error message
    report: the header, how many data rows there were, and how many fields each
    of them held.
    """
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


def parse_rank_table(text: str) -> RankTable:
    """Read a docking tool's own ranked list of poses, exactly as written.

    The first line that holds anything is the header. No data row is ever
    dropped for holding a different number of fields than the header: either
    every row matches the header, and the header names the fields, or every row
    shares one other count, and the fields are numbered from the left with the
    last one as the score. Rows of differing counts, or a table with no data
    row at all, are errors that say what was seen; a table is never silently
    read as empty, which is how one earlier run lost a table the tool had
    written correctly.
    """
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
            "the header; %s" % (after, first_raw_lines(text))
        )

    counts = sorted(set(len(fields) for fields in rows_fields))
    if len(counts) > 1:
        raise ParseError(
            "docking rank table rows hold different numbers of fields (%s); %s"
            % (", ".join(str(c) for c in counts), first_raw_lines(text))
        )
    width = counts[0]
    lowered_header = [token.lower() for token in header]

    if width == len(header):
        mapping = "by_name"
        rows = [dict(zip(header, fields)) for fields in rows_fields]
        rank_key = next((t for t in header if t.lower() == "rank"), None)
        score_key = next(
            (t for t in header if t.lower() in SCORE_COLUMN_NAMES), None
        )
        if rank_key is None and score_key is None:
            raise ParseError(
                "docking rank table names neither a rank nor a score column; %s"
                % first_raw_lines(text)
            )
    else:
        mapping = "positional"
        if not lowered_header or lowered_header[-1] not in SCORE_COLUMN_NAMES:
            raise ParseError(
                "docking rank table has %d header tokens over rows of %d fields, "
                "and its last header token is not a score column; %s"
                % (len(header), width, first_raw_lines(text))
            )
        names = ["col%d" % i for i in range(width)]
        rows = [dict(zip(names, fields)) for fields in rows_fields]
        rank_key = None
        score_key = names[-1]

    return RankTable(rows, header=header, mapping=mapping, field_count=width,
                     raw_lines=raw_lines, rank_key=rank_key, score_key=score_key)


def is_monotone(values: list) -> bool:
    """True when a column only rises, or only falls, down the file."""
    rising = all(b >= a for a, b in zip(values, values[1:]))
    falling = all(b <= a for a, b in zip(values, values[1:]))
    return rising or falling


def top_ranked_row(rows: list) -> dict:
    """The tool's own first-ranked pose.

    With a rank column, it is the lowest rank. Without one, it is the first row
    the tool wrote, and the score column must only rise or only fall down the
    file; a score that rises and then falls means the file is not a ranking,
    and is refused rather than guessed at.
    """
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
        score_key = next(
            (k for k in keys if k.lower() in SCORE_COLUMN_NAMES), None
        )
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
            "order; " + first_raw_lines(raw_text)
        )
    return rows[0]


def parse_af2_timing_rows(rows: list) -> dict:
    """Mean wall-clock hours over the prediction runs that may be counted.

    A run that was cut short, or that downloaded inside its timed call, is kept
    in the raw rows and left out of the mean.
    """
    good = [
        r
        for r in rows
        if not r.get("incomplete")
        and not r.get("download_in_timed_call")
        and r.get("wallclock_s") is not None
    ]
    hours = [r["wallclock_s"] / 3600.0 for r in good]
    return {
        "n": len(good),
        "mean_h": (sum(hours) / len(hours)) if hours else None,
        "hours": hours,
        "pairs": sorted({r.get("pair") for r in good if r.get("pair") is not None}),
    }


# ===========================================================================
# STRUCTURE FILE READING AND THE ANCHOR ARITHMETIC
# ===========================================================================

BACKBONE_ATOMS = ("N", "CA", "C", "O")


def read_pdb_atoms(text: str) -> list:
    """Read atom records of a structure file into plain dictionaries.

    Column positions are those of the Protein Data Bank format. Hydrogens are
    kept; callers that want heavy atoms only filter on the element.
    """
    atoms = []
    for line in text.splitlines():
        if not (line.startswith("ATOM") or line.startswith("HETATM")):
            continue
        if len(line) < 54:
            continue
        try:
            x = float(line[30:38])
            y = float(line[38:46])
            z = float(line[46:54])
        except ValueError:
            continue
        name = line[12:16].strip()
        element = line[76:78].strip() if len(line) >= 78 else ""
        if not element:
            element = name[0] if name else ""
        try:
            resseq = int(line[22:26])
        except ValueError:
            continue
        atoms.append(
            {
                "record": line[0:6].strip(),
                "serial": line[6:11].strip(),
                "name": name,
                "resname": line[17:20].strip(),
                "chain": line[21:22].strip(),
                "resseq": resseq,
                "icode": line[26:27].strip(),
                "x": x,
                "y": y,
                "z": z,
                "element": element.upper(),
            }
        )
    return atoms


def write_pdb(atoms: list) -> str:
    """Write atom records back out in the same column layout."""
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
                rec=a.get("record", "ATOM"),
                serial=i,
                name=name,
                alt=" ",
                resn=a["resname"][:3],
                chain=(a["chain"] or " ")[:1],
                resi=a["resseq"],
                icode=(a.get("icode") or " ")[:1] or " ",
                x=a["x"],
                y=a["y"],
                z=a["z"],
                occ=1.00,
                bfac=0.00,
                elem=(a.get("element") or "")[:2],
            )
        )
    out.append("END")
    return "\n".join(out) + "\n"


def heavy_atoms(atoms: list) -> list:
    return [a for a in atoms if a.get("element") != "H"]


def map_chain_roles(atoms: list, chain_map: dict) -> list:
    """Replace each atom's chain letter with the part it plays.

    Docking tools rename chains. Keying contacts by the letter in the file would
    compare a pose with itself under another name, so both the published
    structure and the pose pass through this one function first.
    """
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
    """Residue pairs across the two parts whose heavy atoms nearly touch.

    A contact is a capsid residue and a receptor residue with at least one pair
    of heavy atoms no further apart than the cutoff.
    """
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
    """Contacts keyed by the part played and the residue number only.

    The chain letter is dropped, so the same pose scores the same whatever the
    docking tool renamed its chains to.
    """
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
    """Receptor residue numbers with any heavy atom near the capsid."""
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
    """Root-mean-square distance between paired points, as they stand.

    No rotation or translation is fitted. The pose is already in the capsid's
    frame, so fitting would hide exactly the error being measured.
    """
    if not coords_a or len(coords_a) != len(coords_b):
        raise ParseError("cannot compare point sets of different size")
    total = 0.0
    for (ax, ay, az), (bx, by, bz) in zip(coords_a, coords_b):
        total += (ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2
    return math.sqrt(total / len(coords_a))


def interface_backbone_rmsd(reference_role_atoms: list, pose_role_atoms: list,
                            cutoff: float = CONTACT_CUTOFF_A) -> float:
    """Backbone displacement of the receptor residues that form the interface.

    Only the nitrogen, alpha carbon, carbon and oxygen atoms of the receptor
    residues that touch the capsid in the published structure are compared, in
    the capsid's frame, with no superposition.
    """
    residues = interface_receptor_residues(reference_role_atoms, cutoff)
    ref_idx = _backbone_index(reference_role_atoms, residues)
    pose_idx = _backbone_index(pose_role_atoms, residues)
    keys = sorted(set(ref_idx) & set(pose_idx))
    if not keys:
        raise ParseError("no shared interface backbone atoms to compare")
    return rmsd_no_superposition([ref_idx[k] for k in keys], [pose_idx[k] for k in keys])


def whole_chain_rmsd(atoms_a: list, atoms_b: list, role: str = "receptor") -> float:
    """Displacement over every atom of one part, as the files stand."""
    a_idx = {(x["resseq"], x["name"]): (x["x"], x["y"], x["z"])
             for x in atoms_a if x.get("role") == role}
    b_idx = {(x["resseq"], x["name"]): (x["x"], x["y"], x["z"])
             for x in atoms_b if x.get("role") == role}
    keys = sorted(set(a_idx) & set(b_idx))
    if not keys:
        raise ParseError("no shared receptor atoms to compare")
    return rmsd_no_superposition([a_idx[k] for k in keys], [b_idx[k] for k in keys])


def anchor_decision(overlap: float, iface_rmsd: float, serial_parallel_rmsd: float,
                    calls_identical: bool) -> dict:
    """Did the redocking reproduce the published placement?

    Pass needs two things at once: the pose matches the published contacts
    (enough contact overlap, or a small enough interface backbone displacement),
    and running the same docking serially and in parallel gave the same answer.
    """
    if overlap is None or iface_rmsd is None:
        raise HarnessFailure(
            "anchor_decision called without a pose",
            "a missing pose is broken infrastructure, never an anchor miss",
        )
    placement_ok = (overlap >= ANCHOR_OVERLAP_MIN) or (iface_rmsd <= ANCHOR_IFACE_RMSD_MAX)
    agreement_ok = (
        serial_parallel_rmsd is not None
        and serial_parallel_rmsd <= ANCHOR_SERIAL_PARALLEL_RMSD_MAX
        and bool(calls_identical)
    )
    return {
        "overlap": overlap,
        "interface_backbone_rmsd_a": iface_rmsd,
        "serial_parallel_rmsd_a": serial_parallel_rmsd,
        "calls_identical": bool(calls_identical),
        "placement_ok": placement_ok,
        "agreement_ok": agreement_ok,
        "decision": "PASS" if (placement_ok and agreement_ok) else "FAIL",
    }


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
    """Read one measured number against the card's band for it.

    Marginal first: a value near an edge is not decided either way. Then inside
    the band is PASS, outside is FAIL.
    """
    if value is None:
        return {"decision": "VOID", "marginal": False, "reason": "no measured value"}
    if is_marginal(value, band):
        return {
            "decision": "VOID",
            "marginal": True,
            "reason": "within 10 percent of a band edge",
        }
    inside = band[0] <= value <= band[1]
    return {
        "decision": "PASS" if inside else "FAIL",
        "marginal": False,
        "reason": None if inside else "outside the card's band",
    }


def gate_on_c1(value, decision: str, marginal: bool) -> dict:
    """Apply the card's own gate to the AlphaFold timing, and only to it.

    The gate is read, never acted on: this run does not branch on it.
    """
    holds_measurement = decision in ("PASS", "FAIL") or (decision == "VOID" and marginal)
    if value is None or not holds_measurement:
        return {
            "gate_value": GATE_EXPRESSION,
            "gate_pass": None,
            "gate_else": GATE_ELSE,
            "gate": None,
        }
    passed = value <= 1.0
    return {
        "gate_value": GATE_EXPRESSION,
        "gate_pass": bool(passed),
        "gate_else": GATE_ELSE,
        "gate": None,
    }


def relative_sd(values: list):
    """Spread across repeats of one cell, as a fraction of the mean."""
    clean = [v for v in values if v is not None]
    if len(clean) < 2:
        return None
    mean = sum(clean) / len(clean)
    if mean == 0:
        return None
    return statistics.stdev(clean) / mean


def spread_check(per_pair_times: dict) -> dict:
    """Reruns of one cell must differ; identical numbers mean a wrong source.

    If a pair's repeated timings are bit-identical, the thing being varied is not
    the thing that varies, and the run halts on that pair.
    """
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
    return {
        "per_pair": details,
        "zero_spread_pairs": zero_spread_pairs,
        "high_spread_pairs": high_spread_pairs,
        "halt": WRONG_VARIANCE_SOURCE if zero_spread_pairs else None,
    }


def storage_from_bytes(bytes_per_run: int) -> dict:
    """Scale one run's bytes to the planned grid, in gibibytes."""
    return {
        "bytes_per_run": bytes_per_run,
        "gib_216_runs": bytes_per_run * GRID_RUNS / float(BYTES_PER_GIB),
        "gib_432_runs": bytes_per_run * GRID_RUNS_ALT / float(BYTES_PER_GIB),
    }


def cost_usd(elapsed_s: float, price_per_hour: float) -> float:
    """Dollars spent for a number of seconds at an hourly price."""
    return elapsed_s / 3600.0 * price_per_hour


def stop_at_seconds(price_per_hour: float, budget_left_usd: float,
                    remote_timeout_s: float) -> dict:
    """The earlier of the money cap and the clock cap, in seconds from the start."""
    if price_per_hour and price_per_hour > 0:
        dollar_cap_s = budget_left_usd / price_per_hour * 3600.0
    else:
        dollar_cap_s = float(remote_timeout_s)
    stop_at = min(float(remote_timeout_s), dollar_cap_s)
    return {
        "dollar_cap_s": dollar_cap_s,
        "time_cap_s": float(remote_timeout_s),
        "stop_at_s": stop_at,
        "binding": "dollars" if dollar_cap_s < remote_timeout_s else "time",
    }


# ===========================================================================
# RUN STATE
# One object holds everything a stage needs: where to write, what time it is,
# how to start a tool, and whether the run is still valid.
# ===========================================================================


class RunState:
    """Everything the stages share: where to write, the clock, and the tools."""

    def __init__(self, outdir, workdir, datadir, clock=None, now=None,
                 env=None, runner=None, provenance=None, base=None):
        self.outdir = Path(outdir)
        self.workdir = Path(workdir)
        self.datadir = Path(datadir)
        # The payload directory: where the tests the hidden author wrote live.
        self.base = Path(base) if base is not None else self.outdir.parent.parent
        self.outdir.mkdir(parents=True, exist_ok=True)
        self.workdir.mkdir(parents=True, exist_ok=True)
        self.env = dict(env if env is not None else os.environ)
        self.clock = clock or time.time          # wall clock, seconds since epoch
        self.now = now or utc_now                # the same instant, as text
        self.runner = runner                     # set below if not injected
        self.provenance = provenance             # the record writer module

        # Money and time, read from the environment through defaults.
        self.price_usd_per_hour = _env_float(
            self.env, "PRICE_USD_PER_HOUR", DEFAULT_PRICE_USD_PER_HOUR
        )
        self.budget_left_usd = min(
            _env_float(self.env, "BUDGET_LEFT_USD", DEFAULT_BUDGET_LEFT_USD),
            DEFAULT_BUDGET_LEFT_USD,
        )
        raw_timeout = self.env.get("REMOTE_TIMEOUT", "")
        self.remote_timeout_forwarded = bool(str(raw_timeout).strip())
        self.remote_timeout_s = min(
            _env_float(self.env, "REMOTE_TIMEOUT", DEFAULT_REMOTE_TIMEOUT_S),
            DEFAULT_REMOTE_TIMEOUT_S,
        )
        self.t0 = _env_float(self.env, "M4_T0_EPOCH", None) or self.clock()
        self.pre_t0_seconds = _env_float(self.env, "M4_PRE_T0_SECONDS", 0.0)
        self.bootstrap_assumed = str(
            self.env.get("M4_BOOTSTRAP_ASSUMED", "")
        ).strip() in ("1", "true", "yes")

        caps = stop_at_seconds(
            self.price_usd_per_hour, self.budget_left_usd, self.remote_timeout_s
        )
        self.caps = caps
        self.stop_at_s = caps["stop_at_s"]

        # Validity and the trail of why.
        self.run_valid = True
        self.run_valid_voided_by = None
        self.stopped = False                 # a guard, ceiling or timeout fired
        self.stop_events = []
        self.stages_done = []
        self.notes = []

        # Measurements as they arrive.
        self.rows = {}                       # arm -> list of rows (also on disk)
        self.inputs_status = {
            cid: {"state": "unmeasured",
                  "status": "unmeasured_by_stop:stage_not_reached",
                  "reason": "stage not reached", "decision": None,
                  "voided_by": None}
            for cid in INPUT_IDS
        }
        # Filled in when something breaks or the anchor misses, so the closing
        # stage can write the right status word against every input.
        self.failure_kind = None
        self.anchor_missed = None
        self.records_written = []
        self.labels_cache = None
        # Setting up, checking what the environment can do and fetching the
        # declared files share one running total. The shell's own setup seconds,
        # spent verifying the environment before this program started, are part
        # of it and arrive in the environment.
        self.setup_seconds_used = _env_float(self.env, "M4_SETUP_SECONDS", 0.0)
        self.setup_total_exhausted = False
        self.download_record_path = None
        # The environment of record: where it lives, the lock the launcher
        # expects, the lock the box observed, and whether a fixer changed it.
        self.venv_path = (self.env.get("M4_VENV")
                          or str(self.venv_bin().parent) or None)
        self.expected_lock_sha256 = (
            str(self.env.get("ENV_LOCK_SHA256", "")).strip() or None)
        self.observed_lock_sha256 = (
            str(self.env.get("M4_ENV_LOCK_OBSERVED", "")).strip() or None)
        self.environment_changed_by_fixer = str(
            self.env.get("M4_ENV_CHANGED_BY_FIXER", "")
        ).strip() in ("1", "true", "yes")
        self.held_attempts = int(_env_float(self.env, "M4_HELD_ATTEMPTS", 0.0) or 0)
        self.changes_log_sha256 = (
            str(self.env.get("M4_CHANGES_LOG_SHA256", "")).strip() or None)
        self.tests_record = None
        self.pairs_path = None
        self.pairs = []
        self.overhead_s = 0.0
        self.overhead_bytes = 0
        self.overhead_labels = []
        self.anchor = None
        self.gpu_is_a100 = None
        self.unit_times = {}                 # kind -> list of finished seconds

    # -- where the tools live ---------------------------------------------

    def venv_bin(self) -> Path:
        """The directory holding the installed tools.

        Taken from the interpreter that is running, so the tools found are the
        ones in this virtual environment and never a different copy on the
        wider search path.
        """
        override = self.env.get("M4_VENV_BIN")
        if override:
            return Path(override)
        return Path(sys.executable).resolve().parent

    def python_executable(self) -> str:
        candidate = self.venv_bin() / "python3"
        if candidate.exists():
            return str(candidate)
        return sys.executable

    # -- clock -------------------------------------------------------------

    def elapsed_s(self) -> float:
        return max(0.0, self.clock() - self.t0)

    def time_left_s(self) -> float:
        return self.stop_at_s - self.elapsed_s()

    def spend_usd(self) -> float:
        """Dollars spent since the run's own start.

        The start already counts the seconds the box spent booting, so those
        seconds are reported beside this figure and never added to it again.
        """
        return cost_usd(self.elapsed_s(), self.price_usd_per_hour)

    # -- validity ----------------------------------------------------------

    def void_run(self, reason: str) -> None:
        """Mark the whole run invalid, from here on, for a stated reason."""
        if self.run_valid:
            self.run_valid = False
            self.run_valid_voided_by = reason
        self.notes.append(f"run_valid set false: {reason}")

    def record_stop(self, kind: str, stage: str, detail: str) -> None:
        """Note that a guard, a ceiling or a timeout cut work short."""
        self.stopped = True
        self.stop_events.append(
            {"kind": kind, "stage": stage, "reason": detail, "detail": detail,
             "elapsed_s": round(self.elapsed_s(), 3), "at_utc": self.now()}
        )

    # -- per-input bookkeeping --------------------------------------------

    # Exactly one of five status words stands against each input in the marker
    # the launcher reads: decided, void by a rule, left unmeasured by a stop,
    # voided because the anchor missed, or voided because something broke.

    def set_decided(self, cid: str, decision: str, reason=None) -> None:
        if decision == "VOID":
            self.inputs_status[cid] = {
                "state": "void_by_rule",
                "status": f"void_by_rule:{reason}",
                "reason": reason,
                "decision": "VOID",
                "voided_by": reason,
            }
        else:
            self.inputs_status[cid] = {
                "state": "decided", "status": "decided",
                "reason": reason, "decision": decision, "voided_by": None,
            }

    def set_unmeasured(self, cid: str, stop_kind: str) -> None:
        self.inputs_status[cid] = {
            "state": "unmeasured",
            "status": f"unmeasured_by_stop:{stop_kind}",
            "reason": stop_kind,
            "decision": "VOID",
            "voided_by": stop_kind,
        }

    def set_void_by_anchor_miss(self, cid: str, reason: str) -> None:
        self.inputs_status[cid] = {
            "state": "void_by_anchor_miss", "status": "void_by_anchor_miss",
            "reason": reason, "decision": "VOID", "voided_by": reason,
        }

    def set_void_by_failure(self, cid: str, kind: str, reason: str) -> None:
        self.inputs_status[cid] = {
            "state": "void_by_failure", "status": f"void_by_failure:{kind}",
            "reason": reason, "decision": "VOID", "voided_by": reason,
        }

    def last_stop_kind(self) -> str:
        """What kind of stop cut the most recent piece of work short."""
        if not self.stop_events:
            return "stop_not_recorded"
        return str(self.stop_events[-1].get("kind") or "stop_not_recorded")

    def unmeasured_inputs(self) -> list:
        """The inputs a stop left unmeasured, which is what decides exit 3."""
        return sorted(cid for cid, s in self.inputs_status.items()
                      if str(s.get("status", "")).startswith("unmeasured_by_stop"))

    def unit_estimate(self, kind: str) -> float:
        """How long one more unit of this kind should take.

        The mean of the units of that kind that already finished, and before any
        has finished, the floor this program declares for that kind.
        """
        done = [t for t in self.unit_times.get(kind, []) if t is not None]
        if done:
            return sum(done) / len(done)
        return float(UNIT_FLOOR_S[kind])

    def note_unit(self, kind: str, seconds: float) -> None:
        self.unit_times.setdefault(kind, []).append(seconds)


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
# Every measured record says which machine produced it and with what software.
# ===========================================================================

# The packages whose versions the records carry: the name the distribution is
# installed under, and the key used here. Every version is read from the
# installed distribution's own metadata in the environment of record, never
# from a constant; see read_package_versions.
PACKAGE_VERSION_NAMES = (
    ("jax", "jax"),
    ("jaxlib", "jaxlib"),
    ("jax-cuda12-plugin", "jax_cuda12_plugin"),
    ("openmm", "openmm"),
    ("lightdock", "lightdock"),
    ("colabfold", "colabfold"),
)

# Why a version label is null when the environment of record holds no such
# distribution to ask.
LABEL_NOT_INSTALLED = "no such distribution in the environment of record"


def collect_labels(state: RunState) -> dict:
    """Read the machine's own description, once, from runtime queries only.

    Nothing here is a literal copied from the card. A value that cannot be read
    is null and carries the reason it is null, in a word or two of plain text.
    Returns one flat dictionary; `labels_for_record` sorts it into the machine
    block and the engine block the records carry.
    """
    if state.labels_cache is not None:
        return dict(state.labels_cache)

    labels = {k: None for k in MACHINE_KEYS + ENGINE_KEYS}
    reasons = {}

    labels["instance_type"] = state.env.get("INSTANCE_TYPE") or None
    if labels["instance_type"] is None:
        reasons["instance_type"] = "INSTANCE_TYPE was not forwarded to the box"
    labels["price_usd_per_hour"] = state.price_usd_per_hour

    # The environment of record: which directory, which lock was expected, which
    # lock the box computed, and whether a fixer changed it between attempts.
    labels["venv_path"] = state.venv_path
    if labels["venv_path"] is None:
        reasons["venv_path"] = "the environment directory was not forwarded"
    labels["expected_lock_sha256"] = state.expected_lock_sha256
    if labels["expected_lock_sha256"] is None:
        reasons["expected_lock_sha256"] = "ENV_LOCK_SHA256 was not forwarded to the box"
    labels["observed_lock_sha256"] = state.observed_lock_sha256
    if labels["observed_lock_sha256"] is None:
        reasons["observed_lock_sha256"] = (
            "the on-box script recorded no observed lock for this attempt"
        )
    labels["environment_changed_by_fixer"] = bool(state.environment_changed_by_fixer)
    labels["held_attempts"] = state.held_attempts

    smi_query = state.runner.capture(
        ["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
        limit_s=30, stage="labels", name="nvidia_smi_query",
    )
    smi_header = state.runner.capture(
        ["nvidia-smi"], limit_s=30, stage="labels", name="nvidia_smi_header"
    )
    q = parse_nvidia_smi_query(smi_query.get("stdout", "")) if smi_query.get("ok") else {}
    h = parse_nvidia_smi_header(smi_header.get("stdout", "")) if smi_header.get("ok") else {}

    labels["gpu_name"] = q.get("gpu_name")
    if labels["gpu_name"] is None:
        reasons["gpu_name"] = "nvidia-smi did not report a graphics-processor name"
    labels["gpu_driver"] = q.get("driver_version") or h.get("driver_version")
    if labels["gpu_driver"] is None:
        reasons["gpu_driver"] = "nvidia-smi did not report a driver version"
    labels["cuda_runtime_version"] = h.get("cuda_version_header")
    if labels["cuda_runtime_version"] is None:
        reasons["cuda_runtime_version"] = (
            "the nvidia-smi banner carried no CUDA Version field"
        )

    versions = read_package_versions(state)
    # A version label is null whenever the environment of record did not supply
    # it, and the reason says which case it is: the environment could not be
    # asked at all, or it answered and that distribution named no version.
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
            "the JAX CUDA plugin package did not report a version"
        )
        reasons["cuda_plugin_version"] = version_reason(
            "the JAX CUDA plugin package did not report a version"
        )
    labels["jax_wheel_build_tags"] = versions.get("wheel_build_tags")
    if labels["jax_wheel_build_tags"] is None:
        reasons["jax_wheel_build_tags"] = version_reason(
            "the installed JAX distributions carry no wheel tag in their metadata"
        )
    labels["alphafold_implementation"] = AF2_IMPLEMENTATION
    labels["alphafold_params_sha256"] = versions.get("params_sha256")
    if labels["alphafold_params_sha256"] is None:
        reasons["alphafold_params_sha256"] = (
            "the parameter archive was not hashed in this run"
        )
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

    # One place that holds how the software was built, so a reader can tell two
    # otherwise identical numbers apart.
    labels["build_flags"] = {
        "alphafold_implementation": labels["alphafold_implementation"],
        "alphafold_params_sha256": labels["alphafold_params_sha256"],
        "jax_version": labels["jax_version"],
        "jaxlib_version": labels["jaxlib_version"],
        "jax_cuda_plugin_version": labels["jax_cuda_plugin_version"],
        "jax_wheel_build_tags": labels["jax_wheel_build_tags"],
        "docking_code": labels["docking_code"],
        "docking_version": labels["docking_version"],
        "md_engine": labels["md_engine"],
        "md_engine_version": labels["md_engine_version"],
        "md_precision": labels["md_precision"],
        "md_platform": labels["md_platform"],
        "environment_lock_sha256": labels["observed_lock_sha256"],
        "alphafold_models": AF2_MODELS,
        "alphafold_recycles": AF2_RECYCLES,
        "alphafold_early_stopping": "off",
        "alphafold_msa_mode": "single_sequence",
    }

    labels["start_utc"] = utc_of(state.t0)
    labels["end_utc"] = None
    reasons["end_utc"] = "filled in per record from the stage that produced it"

    labels["null_reasons"] = reasons
    state.labels_cache = dict(labels)
    state.gpu_is_a100 = is_a100(labels["gpu_name"])
    return dict(labels)


def read_package_versions(state: RunState) -> dict:
    """The versions of the environment of record, from its own metadata.

    One source is allowed: the metadata of the distributions installed in the
    environment the launcher attached, read on the box. No constant stands in as
    a default, because a remembered version is a label that can be stale: launch
    1 wrote the box image's prediction library version into records of a run
    that installed nothing. A version the metadata does not give is absent here,
    and the caller writes it as null with the reason beside it.
    """
    out = dict(installed_package_versions(state))
    wheel_tags = out.pop("wheel_build_tags", None)
    out["versions_from_environment_of_record"] = any(
        out.get(key) for _name, key in PACKAGE_VERSION_NAMES
    )
    out["version_sources"] = {"installed_metadata": True}
    out["params_sha256"] = getattr(state, "params_sha256", None)
    out["wheel_build_tags"] = wheel_tags
    return out


def installed_package_versions(state: RunState, skip=()) -> dict:
    """Ask the distributions in the environment of record for their own labels.

    Each version comes from the distribution's installed metadata. The wheel
    tags of the prediction libraries come from the same place: the `Tag:` lines
    of the record a wheel leaves behind when it is installed.
    """
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
        "print(json.dumps(out))\n"
    )
    res = state.runner.capture(
        [state.python_executable(), "-c", code],
        limit_s=120, stage="labels", name="package_versions",
    )
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
    """The labels for one record, with the stage's own start and end times.

    The times are those of the stage or run that produced the value, never the
    moment the record happened to be written.
    """
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
    """Sort one flat label dictionary into what a record of this kind carries.

    Returns the `machine` block, the `engine` block where the kind needs one,
    and the reasons for whatever is null. Nothing is left out: a key that could
    not be read is present and null, with its reason beside it.
    """
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
# Records go through frozen/provenance.py, then gain the fields this run needs
# that the shared writer does not know about.
# ===========================================================================


def write_record(state: RunState, name: str, *, kind: str, cell: dict, inputs: list,
                 metric: str, values: dict, threshold: dict, decision_rule: str,
                 decision: str, notes: str = "", labels: dict | None = None,
                 extra_notes: list | None = None):
    """Write one result record and remember it.

    The shared writer owns the record's shape. The labels, the validity and the
    incomplete-run note are added here, because every reader of a single file
    must see them without opening the summary. `kind` says which list of label
    keys this record must carry.
    """
    prov = state.provenance
    path = state.outdir / name
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
    prov.write_result(
        tmp,
        cell=cell,
        inputs=inputs,
        metric=metric,
        values=values,
        threshold=threshold,
        decision_rule=decision_rule,
        decision=decision,
        notes=notes,
    )
    rec = json.loads(Path(tmp).read_text())
    os.remove(str(tmp))

    note_list = list(extra_notes or [])
    if state.stopped and LABEL_INCOMPLETE not in note_list:
        note_list.append(LABEL_INCOMPLETE)
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
    if problems:                      # a label gap is a defect, not a silent pass
        rec["label_problems"] = problems
    atomic_write_json(path, rec)
    state.records_written.append(name)
    return path


def record_inputs(state: RunState, rows_file=None, pair_evidence: bool = False,
                  extra_paths=None) -> list:
    """The files a record was computed from, each with its content hash.

    Every record cites the raw rows it rests on, the record of what was
    downloaded with its hashes, and the lock of the environment of record.
    Records about the pairs also cite the pair evidence file.
    """
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
    """Save one measurement verbatim, one line per measurement."""
    path = state.outdir / f"rows_{arm}_tag-{TAG}.jsonl"
    row = dict(row)
    row.setdefault("arm", arm)
    row.setdefault("at_utc", state.now())
    row.setdefault("run_valid_at_write", bool(state.run_valid))
    append_jsonl(path, row)
    state.rows.setdefault(arm, []).append(row)
    return path


# ===========================================================================
# RUNNING A TOOL
# Every external tool runs in its own process group, with a copied environment
# that carries no secret, and with a kill that reaches its children.
# ===========================================================================


def child_env(parent_env: dict, venv_bin, extra: dict | None = None) -> dict:
    """The environment a tool is given: no secrets, the tools first on the path.

    The two variables that may carry a download token are removed outright, so
    no tool and no log can ever see them. The virtual environment's programs go
    first on the search path, so the pinned tool is the one that runs.
    """
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
    """The command name and start time of a process, as the kernel reports them.

    A process identifier is reused. Signalling one that has been reused would
    kill an unrelated process, so the start time is recorded and re-checked.
    """
    try:
        raw = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return {"present": False, "comm": None, "starttime": None}
    try:
        close = raw.rindex(")")
        comm = raw[raw.index("(") + 1:close]
        fields = raw[close + 2:].split()
        starttime = fields[19]     # field 22 of the stat line, 1-based
    except (ValueError, IndexError):
        return {"present": True, "comm": None, "starttime": None}
    return {"present": True, "comm": comm, "starttime": starttime}


def same_process(pid: int, identity: dict) -> bool:
    """True only when the live process is still the one that was recorded."""
    current = proc_identity(pid)
    if not current["present"]:
        return False
    if identity.get("comm") is None or identity.get("starttime") is None:
        return False
    return (current["comm"] == identity["comm"]
            and current["starttime"] == identity["starttime"])


class ToolRunner:
    """Starts tools, times them, kills them, and keeps every log.

    Kept behind one object so every tool call is started, timed and killed the
    same way, and every log lands in the same place.
    """

    def __init__(self, state: RunState):
        self.state = state
        self.groups = {}           # process group id -> recorded identity
        self.log_dir = state.outdir / "tool_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.skipped_signals = []

    # -- registry of running process groups --------------------------------

    def register(self, pgid: int, pid: int) -> None:
        self.groups[pgid] = {"pid": pid, "identity": proc_identity(pid)}
        self._publish()

    def unregister(self, pgid: int) -> None:
        self.groups.pop(pgid, None)
        self._publish()

    def _publish(self) -> None:
        """Leave the live process groups on disk, so the shell can clean up.

        If the launcher's own timeout kills this program, the shell that
        started it still has to stop the tools. It can only do that safely if
        each group's leader is written down with the start time that identifies
        it.
        """
        try:
            atomic_write_json(
                self.state.outdir / "process_groups.json",
                {"groups": [
                    {"pgid": pgid, "pid": e["pid"],
                     "comm": e["identity"].get("comm"),
                     "starttime": e["identity"].get("starttime")}
                    for pgid, e in sorted(self.groups.items())
                ]},
            )
        except OSError:
            pass

    def kill_group(self, pgid: int) -> bool:
        """Signal a whole process group, but only if it is still the one recorded."""
        entry = self.groups.get(pgid)
        if entry is None:
            self.skipped_signals.append({"pgid": pgid, "why": "not registered"})
            return False
        pid = entry["pid"]
        if not same_process(pid, entry["identity"]):
            self.skipped_signals.append(
                {"pgid": pgid, "pid": pid,
                 "why": "leader gone or replaced; not signalled"}
            )
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

    # -- running -----------------------------------------------------------

    def capture(self, cmd: list, *, limit_s: float, stage: str, name: str,
                cwd=None, extra_env: dict | None = None) -> dict:
        """Run one program to completion or to its limit; keep its output.

        Returns a plain dictionary. A program that exceeds its limit is killed
        with its children and reported as timed out, which the caller treats as
        a ceiling stop, not as a broken tool.
        """
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
                [str(c) for c in cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(cwd) if cwd else None,
                env=env,
                text=True,
                start_new_session=True,
            )
        except (OSError, ValueError) as exc:
            finished = state.clock()
            atomic_write_text(out_path, f"failed to start: {exc}\n")
            return {
                "ok": False, "rc": None, "timed_out": False, "started": False,
                "seconds": finished - started, "stdout": "", "stderr": str(exc),
                "log": str(out_path), "cmd": [str(c) for c in cmd],
            }
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
            + "\n--- stderr ---\n" + (stderr or "") + "\n",
        )
        return {
            "ok": (rc == 0 and not timed_out),
            "rc": rc,
            "timed_out": timed_out,
            "started": True,
            "seconds": finished - started,
            "stdout": stdout or "",
            "stderr": stderr or "",
            "log": str(out_path),
            "cmd": [str(c) for c in cmd],
        }


# ===========================================================================
# GUARDS
# A guard never trusts a planned number. It reads the clock, the price and the
# units that already finished, and refuses to start work that will not fit.
# ===========================================================================


def stage_allowance_s(state: RunState, stage: str) -> float:
    """Seconds this stage may use. Never negative.

    One formula, and it is the guarantee the seven ceilings are not:

        allowance = max(0, min(ceiling, whole_run - elapsed - 400 - 100))

    where 400 seconds is the margin that lets results be written and fetched
    and 100 seconds is the slot the closing stage needs. `whole_run` is the
    timeout the launcher forwards, or the earlier money cap when the price
    makes dollars bind first; a cap can only tighten this, never loosen it.
    """
    ceiling = float(STAGE_CEILING_S[stage])
    whole_run = min(float(state.remote_timeout_s), float(state.stop_at_s))
    remaining = whole_run - state.elapsed_s() - FETCH_MARGIN_S - ENDPOINTS_SLOT_S
    return max(0.0, min(ceiling, remaining))


def guard_before_stage(state: RunState, stage: str, estimated_s: float) -> float:
    """Decide whether a stage may start, and say how long it may take.

    Raises a stop when the estimate does not fit. The estimate is always a
    measured mean of finished units of that kind, or this program's declared
    floor before any has finished.
    """
    allowance = stage_allowance_s(state, stage)
    if allowance <= 0:
        raise GuardStop(
            f"no time left for the {stage} stage",
            stage=stage,
            detail=(f"allowance {allowance:.1f}s, elapsed {state.elapsed_s():.1f}s, "
                    f"stop_at {state.stop_at_s:.1f}s"),
        )
    if estimated_s > allowance:
        raise GuardStop(
            f"estimated {estimated_s:.1f}s for the {stage} stage exceeds its "
            f"allowance of {allowance:.1f}s",
            stage=stage,
            detail=(f"elapsed {state.elapsed_s():.1f}s, stop_at {state.stop_at_s:.1f}s, "
                    f"price {state.price_usd_per_hour}/h, "
                    f"budget {state.budget_left_usd}"),
        )
    return allowance


def guard_before_unit(state: RunState, stage: str, kind: str, allowance_left_s: float,
                      estimated_s: float | None = None) -> float:
    """Decide whether one more unit of work inside a stage may start."""
    estimate = state.unit_estimate(kind) if estimated_s is None else estimated_s
    budget = min(allowance_left_s, stage_allowance_s(state, stage))
    if estimate > budget:
        raise GuardStop(
            f"estimated {estimate:.1f}s for one {kind} exceeds the {budget:.1f}s left "
            f"in the {stage} stage",
            stage=stage,
            detail=f"elapsed {state.elapsed_s():.1f}s",
        )
    return budget


def inner_tool_limit_s(state: RunState, wanted_s: float) -> float:
    """How long a tool may run so the inner kill always beats the outer one.

    The launcher kills the whole box after a fixed time. The tool's own limit is
    set at least 100 seconds inside that, so this program is always the one that
    stops the tool and can still write a record about it.
    """
    inner_cap = state.stop_at_s - state.elapsed_s() - INNER_KILL_SLACK_S
    return max(1.0, min(float(wanted_s), inner_cap))


def outer_kill_deadline_s(state: RunState) -> float:
    return state.stop_at_s - state.elapsed_s() - OUTER_KILL_SLACK_S


def setup_call_limit_s(state: RunState, own_limit_s: float, allowance_s: float) -> float:
    """How long one setup step may take, inside the running setup total.

    Setting up is one budget, not a budget per command: checking the
    environment, asking every tool what it can do, downloading the declared
    files and unpacking them all draw on the same 1,500 seconds.
    """
    left_in_total = STAGE_CEILING_S["setup"] - state.setup_seconds_used
    return min(float(own_limit_s), left_in_total, float(allowance_s))


def spend_setup_seconds(state: RunState, seconds: float) -> None:
    state.setup_seconds_used += max(0.0, float(seconds))
    if state.setup_seconds_used >= STAGE_CEILING_S["setup"]:
        state.setup_total_exhausted = True


# ===========================================================================
# THE STAND-IN PAIRS
# The card's own capsid-receptor pairs are not available. Three stand-in pairs
# are built from the chains of one published structure, and every file says so.
# ===========================================================================

THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q",
    "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K",
    "MET": "M", "PHE": "F", "PRO": "P", "SER": "S", "THR": "T", "TRP": "W",
    "TYR": "Y", "VAL": "V", "MSE": "M", "SEC": "U", "PYL": "O",
}


def chain_residues(atoms: list) -> dict:
    """Residues of each chain, in file order, as (number, name) pairs."""
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
        chains.setdefault(a["chain"], []).append((a["resseq"], a["icode"], a["resname"]))
    return chains


def residue_sequence(residues: list) -> str:
    return "".join(THREE_TO_ONE.get(name, "X") for (_n, _i, name) in residues)


def pick_roles(chains: dict) -> dict:
    """Decide which chains stand for the capsid and which for the receptor.

    The longest chains are the capsid; the shortest chain of at least fifty
    residues is the receptor. This is a rule over the file, not a hard-coded
    chain letter, so a re-released structure does not silently change meaning.
    """
    usable = {c: r for c, r in chains.items() if len(r) >= 20}
    if len(usable) < 2:
        raise HarnessFailure(
            "the published structure has fewer than two usable chains",
            f"chains found: { {c: len(r) for c, r in chains.items()} }",
        )
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
    """Build three stand-in complexes of a declared size from one structure.

    Each complex is the receptor chain plus as much capsid chain as the target
    length needs. Copies of a capsid chain are allowed, and are moved apart so
    they do not sit on top of each other. Nothing is silently clamped: a target
    that cannot be met stops the run.
    """
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
                "pair assertion failed: the receptor chain alone is longer than the "
                f"target length {target}",
                f"receptor {receptor_chain} has {receptor_len} residues",
            )
        taken = []           # (source chain, chain id used, residues kept)
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
            taken.append(
                {"source_chain": source, "chain_id": chain_id,
                 "n_residues": keep, "x_shift_a": shift}
            )
            remaining -= keep
            copy_number += 1
            if copy_number > 20:
                raise HarnessFailure(
                    "pair assertion failed: could not reach the target length with "
                    "twenty capsid chain copies",
                    f"target {target}, receptor {receptor_len}",
                )

        pair_atoms = []
        chain_map = {}
        sequences = {}
        for piece in taken:
            source_res = chains[piece["source_chain"]][: piece["n_residues"]]
            keys = {(n, i) for (n, i, _nm) in source_res}
            picked = [
                a for a in atoms_by_chain[piece["source_chain"]]
                if (a["resseq"], a["icode"]) in keys
            ]
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
        pairs.append(
            {
                "pair": f"pair{index}",
                "capsid_slot": index,
                "target_residues": target,
                "total_residues": total_len,
                "receptor_chain": receptor_chain,
                "receptor_residues": receptor_len,
                "capsid_pieces": taken,
                "chain_map": chain_map,
                "sequences": sequences,
                "sequence_joined": ":".join(
                    sequences[c] for c in sorted(sequences)
                ),
                "atoms": pair_atoms,
            }
        )
    return pairs


def _next_chain_letter(used: set) -> str:
    for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789":
        if ch not in used:
            return ch
    raise HarnessFailure("ran out of chain letters while building the stand-in pairs")


def assert_pairs(pairs: list) -> None:
    """Check the three stand-in complexes before any time is spent on them.

    The card's setting is a hetero-multimer of 750 to 1,000 residues, and three
    identical complexes would measure one complex three times. Both are checked
    here, and a failure stops the run rather than shrinking the requirement.
    """
    if len(pairs) != N_PAIRS:
        raise HarnessFailure(
            f"pair assertion failed: {len(pairs)} pairs built, {N_PAIRS} wanted"
        )
    lengths = []
    seqs = []
    for p in pairs:
        n = p["total_residues"]
        lengths.append(n)
        seqs.append(p["sequence_joined"])
        if not (PAIR_RESIDUES_MIN <= n <= PAIR_RESIDUES_MAX):
            raise HarnessFailure(
                "pair assertion failed: total length outside 750 to 1,000 residues",
                f"{p['pair']} has {n} residues",
            )
        roles = set(p["chain_map"].values())
        if roles != {"capsid", "receptor"}:
            raise HarnessFailure(
                "pair assertion failed: a pair does not hold both a capsid-role and "
                "a receptor-role chain set",
                f"{p['pair']} roles: {sorted(roles)}",
            )
        if sum(1 for v in p["chain_map"].values() if v == "receptor") != 1:
            raise HarnessFailure(
                "pair assertion failed: a pair must hold exactly one receptor-role chain",
                f"{p['pair']} chain map: {p['chain_map']}",
            )
    if len(set(seqs)) != len(seqs):
        raise HarnessFailure(
            "pair assertion failed: two stand-in pairs have the same sequence"
        )
    for i in range(len(lengths)):
        for j in range(i + 1, len(lengths)):
            if abs(lengths[i] - lengths[j]) < PAIR_LENGTH_SPREAD_MIN:
                raise HarnessFailure(
                    "pair assertion failed: two pair lengths are closer than 20 residues",
                    f"{lengths[i]} and {lengths[j]}",
                )


def write_pair_evidence(state: RunState, pairs: list, source_pdb) -> Path:
    """Write what each stand-in complex is, so a reader can rebuild it."""
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
        entries.append(
            {
                "pair": p["pair"],
                "capsid_slot": p["capsid_slot"],
                "chain_map": p["chain_map"],
                "receptor_chain": p["receptor_chain"],
                "capsid_pieces": p["capsid_pieces"],
                "sequences": p["sequences"],
                "lengths": {c: len(s) for c, s in p["sequences"].items()},
                "total_residues": p["total_residues"],
                "fasta_path": str(fasta_path),
                "fasta_sha256": sha256_file(fasta_path),
                "pdb_path": str(pdb_path),
                "pdb_sha256": sha256_file(pdb_path),
            }
        )
    doc = {
        "what": "three stand-in capsid-receptor complexes built from the chains of "
                f"PDB entry {PDB_ENTRY}; not the card's own pairs",
        "source_pdb": str(source_pdb),
        "source_pdb_sha256": sha256_file(source_pdb) if Path(source_pdb).exists() else None,
        "pairs": entries,
    }
    path = state.outdir / f"pairs_tag-{TAG}.json"
    atomic_write_json(path, doc)
    state.pairs_path = path
    return path


# ===========================================================================
# THE MOLECULAR-DYNAMICS WORKER
# Written to the results directory and run by the virtual environment's own
# interpreter, so this program itself never imports a heavy library.
# ===========================================================================

MD_WORKER_SOURCE = r'''#!/usr/bin/env python3
"""Build and run one short explicit-solvent segment, and report its speed.

Two modes. `build` wraps the complex in water and says how many atoms the
result has, so the caller can check the size before paying for a run. `run`
minimises, equilibrates briefly, then times one production segment and writes
the engine's own speed column to a reporter file.
"""
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
        modeller.addSolvent(
            forcefield,
            model="tip3p",
            padding=args.padding_nm * unit.nanometer,
            neutralize=True,
        )
        system = forcefield.createSystem(
            modeller.topology,
            nonbondedMethod=app.PME,
            nonbondedCutoff=1.0 * unit.nanometer,
            constraints=app.HBonds,
            rigidWater=True,
        )
        with open(system_xml, "w") as fh:
            fh.write(XmlSerializer.serialize(system))
        with open(solvated_pdb, "w") as fh:
            app.PDBFile.writeFile(modeller.topology, modeller.positions, fh)
        n_atoms = modeller.topology.getNumAtoms()
        n_water = sum(1 for r in modeller.topology.residues() if r.name in ("HOH", "WAT"))
        json.dump({"mode": "build", "atoms": n_atoms, "waters": n_water,
                   "padding_nm": args.padding_nm, "system_xml": system_xml,
                   "solvated_pdb": solvated_pdb},
                  open(args.out, "w"), indent=2)
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
        temperature=True, speed=True, elapsedTime=True, totalSteps=args.steps,
    ))
    # The trajectory itself. One frame every args.report_interval steps, which
    # at a two femtosecond step is one frame every ten picoseconds: fifty
    # frames over the half-nanosecond segment. This interval is declared by the
    # caller and is never changed to move the storage figure.
    trajectory_path = os.path.join(args.work, "md_trajectory.dcd")
    sim.reporters.append(app.DCDReporter(trajectory_path, args.report_interval))
    t_prod = time.time()
    sim.step(args.steps)
    production_s = time.time() - t_prod

    json.dump({
        "mode": "run",
        "atoms": pdb.topology.getNumAtoms(),
        "steps": args.steps,
        "timestep_fs": args.timestep_fs,
        "production_s": production_s,
        "minimise_s": minimise_s,
        "equilibrate_s": equilibrate_s,
        "reporter_path": reporter_path,
        "trajectory_path": trajectory_path,
        "report_interval_steps": args.report_interval,
        "frame_interval_ps": args.report_interval * args.timestep_fs / 1000.0,
        "platform": platform.getName(),
        "precision": "mixed",
        "openmm_version": __import__("openmm").version.version,
        "seed": args.seed,
    }, open(args.out, "w"), indent=2)
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''


# Files a dynamics working directory holds that are built once to start the
# segment, not written by the segment. They are reported separately and are not
# in the storage figure the card is read against.
MD_SETUP_FILE_NAMES = ("system.xml", "solvated.pdb")
MD_SETUP_SUFFIXES = (".chk", ".checkpoint")


def md_bytes_breakdown(md_dir, extra_log_paths=()) -> dict:
    """Split what one dynamics segment left behind into written and set-up bytes.

    Written: the trajectory, the engine's own rate file, the tool's logs and the
    worker's build and run records. Those are what a grid run really writes per
    segment. Set up once and reported separately: the serialised system, the
    solvated structure and any checkpoint.
    """
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
    """Choose how much water to add so the finished system is the wanted size.

    Water is about 0.1 atoms per cubic angstrom. The box has to hold the
    complex and enough water to reach the target, so the needed box side
    follows from the target directly, and the padding is half the difference
    between that side and the complex's own extent.
    """
    if not atoms:
        raise HarnessFailure("cannot size a water box around an empty complex")
    xs = [a["x"] for a in atoms]
    ys = [a["y"] for a in atoms]
    zs = [a["z"] for a in atoms]
    extent = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    solute_atoms = len(atoms) * 2          # hydrogens are added at build time
    water_atoms = max(1000, target_atoms - solute_atoms)
    volume_a3 = water_atoms / 0.1
    side = volume_a3 ** (1.0 / 3.0)
    padding_a = max(8.0, (side - extent) / 2.0)
    return round(padding_a / 10.0, 3)      # angstrom to nanometre


def merge_capsid_and_pose(pair: dict, pose_atoms: list) -> list:
    """Put the pair's capsid chains and the best docked receptor pose together.

    The molecular-dynamics input must be the complex, not either half. Both
    parts are checked here, because a receptor-only file would still run and
    would quietly measure the speed of the wrong system.
    """
    capsid_ids = [c for c, role in pair["chain_map"].items() if role == "capsid"]
    capsid_atoms = [dict(a) for a in pair["atoms"] if a["chain"] in capsid_ids]
    if not capsid_atoms:
        raise HarnessFailure(
            "the molecular-dynamics input holds no capsid-role chain",
            f"{pair['pair']} chain map: {pair['chain_map']}",
        )
    if not heavy_atoms(capsid_atoms):
        raise HarnessFailure(
            "the molecular-dynamics input holds no capsid heavy atom",
            f"{pair['pair']}",
        )
    receptor_id = pair["receptor_chain"]
    receptor = [dict(a, chain=receptor_id) for a in pose_atoms]
    if not receptor:
        raise HarnessFailure(
            "the molecular-dynamics input holds no receptor-role chain",
            f"{pair['pair']}: the docked pose contributed no atoms",
        )
    merged = capsid_atoms + receptor
    roles = {("capsid" if a["chain"] in capsid_ids else "receptor") for a in merged}
    if roles != {"capsid", "receptor"}:
        raise HarnessFailure(
            "the merged complex does not hold both chain roles", f"roles: {sorted(roles)}"
        )
    return merged


# ===========================================================================
# STAGE: SETUP, TESTS, DOWNLOADS
# Everything that must work before a single number is measured. The python
# environment itself is not built here: it is an artifact on the attached
# filesystem, activated and checked by onbox_m4.sh. Nothing in this program
# installs anything. Any failure here is broken infrastructure: exit 2, never
# a substitution.
# ===========================================================================


def make_setup_step(state: RunState, allowance: float, log: dict, stage: str):
    """One timed command inside the shared setup budget of 1,500 seconds.

    Checking what the environment can do and fetching the declared files are one
    budget, not a budget per command. Running that budget out ends the run as
    broken infrastructure, not as a guard stop, because a box that is not ready
    cannot measure anything.
    """

    def step(cmd, own_limit_s, name, **kw):
        limit = setup_call_limit_s(state, own_limit_s, allowance)
        if limit <= 0 or state.setup_total_exhausted:
            raise HarnessFailure(
                "the setup budget of 1,500 seconds ran out",
                f"used {state.setup_seconds_used:.1f}s before step {name}",
                kind="setup_total_ceiling",
            )
        res = state.runner.capture(cmd, limit_s=limit, stage=stage, name=name, **kw)
        spend_setup_seconds(state, res.get("seconds", 0.0))
        log["steps"].append(
            {"name": name, "cmd": res.get("cmd"), "rc": res.get("rc"),
             "seconds": round(res.get("seconds", 0.0), 3),
             "timed_out": res.get("timed_out"), "log": res.get("log")}
        )
        if state.setup_total_exhausted and not res.get("ok"):
            raise HarnessFailure(
                "the setup budget of 1,500 seconds ran out",
                f"step {name} ended at {state.setup_seconds_used:.1f}s",
                kind="setup_total_ceiling",
            )
        return res

    return step


def stage_setup(state: RunState) -> dict:
    """Ask the environment of record, on this box, whether it can do the work.

    The environment was built once on the attached filesystem and its lock was
    checked by onbox_m4.sh before this program started. Here every tool the run
    needs is resolved on that environment's search path and asked what it can
    do. A problem is broken infrastructure, never a fallback.
    """
    started = state.clock()
    allowance = guard_before_stage(state, "setup", UNIT_FLOOR_S["endpoints"])
    log = {"steps": [], "started_utc": utc_of(started),
           "venv_path": state.venv_path,
           "expected_lock_sha256": state.expected_lock_sha256,
           "observed_lock_sha256": state.observed_lock_sha256,
           "installs_run": "none: this program installs nothing"}
    step = make_setup_step(state, allowance, log, "setup")

    capability = smoke_check(state, step, None)
    log["capability_check"] = capability
    if not capability["ok"]:
        raise HarnessFailure("the capability check failed",
                             json.dumps(capability["problems"]),
                             kind="capability_check")

    log["setup_seconds_used"] = round(state.setup_seconds_used, 3)
    log["finished_utc"] = utc_of(state.clock())
    atomic_write_json(state.outdir / f"setup_log_tag-{TAG}.json", log)
    state.stages_done.append("setup")
    return log


TESTS_COUNT_PATTERN = re.compile(r"\btests:\s*(\d+)\s+of\s+(\d+)\s+passed\b")
TESTS_RELATIVE_PATH = f"tests/tests_{TAG}.py"
TESTS_RESULTS_ARGUMENT = f"results_{TAG}/out"


def parse_tests_tally(text: str) -> dict:
    """Read the line `tests: N of M passed`, if the tests printed one."""
    m = TESTS_COUNT_PATTERN.search(str(text or ""))
    if not m:
        return {"tests_passed": None, "tests_total": None}
    return {"tests_passed": int(m.group(1)), "tests_total": int(m.group(2))}


def last_lines(text: str, count: int = 20) -> str:
    """The last few lines of an output, kept verbatim."""
    lines = str(text or "").splitlines()
    return "\n".join(lines[-count:])


def stage_tests(state: RunState) -> dict:
    """Run the tests written by someone who never saw this program.

    The tests come from the execution directive, the on-box contract, the design
    record and the question, written by an author kept away from this program's
    source. This program starts them, times them, keeps their output and records
    what they said. It neither imports them nor interprets them. A non-zero
    exit, a timeout or a missing file ends the run as broken infrastructure.
    There is no skip and no retry.
    """
    started = state.clock()
    allowance = guard_before_stage(state, "tests", UNIT_FLOOR_S["tests"])
    tests_file = state.base / TESTS_RELATIVE_PATH
    values = {
        "kind": "tests_stage",
        "tests_file": str(tests_file),
        "tests_file_sha256": None,
        "exit_code": None,
        "seconds": None,
        "stdout_tail": None,
        "tests_passed": None,
        "tests_total": None,
        "null_reasons": {},
    }

    def close(decision: str, why: str, fail: bool):
        """Write the record, then end the run if the stage failed."""
        if fail:
            # The run is marked invalid before the failing record is written, so
            # that record, the validity file and every later record agree.
            state.void_run(why)
        write_record(
            state, f"tests_tag-{TAG}.json", kind="tests",
            cell={"stage": "tests", "tag": TAG},
            inputs=record_inputs(state, extra_paths=(
                [tests_file] if tests_file.exists() else None)),
            metric=("the exit code of the tests written from the directive by an "
                    "author who never saw this program"),
            values=values,
            threshold={"exit_code": 0, "ceiling_s": STAGE_CEILING_S["tests"]},
            decision_rule=("the tests pass only by exiting zero inside their "
                           "ceiling; a non-zero exit, a timeout or a missing "
                           "file ends the run as broken infrastructure"),
            decision=decision,
            notes=why,
            labels=labels_for_record(state, started, state.clock()),
        )
        if fail:
            raise HarnessFailure(why, f"see {values.get('log') or tests_file}",
                                 kind="tests")

    if not tests_file.exists():
        values["null_reasons"]["exit_code"] = "the tests file was not on the box"
        values["null_reasons"]["seconds"] = "the tests never started"
        values["null_reasons"]["tests_file_sha256"] = "the tests file was not on the box"
        values["null_reasons"]["stdout_tail"] = "the tests never started"
        values["null_reasons"]["tests_passed"] = "the tests never started"
        values["null_reasons"]["tests_total"] = "the tests never started"
        close("VOID", f"the tests file {TESTS_RELATIVE_PATH} is not on the box", True)

    values["tests_file_sha256"] = sha256_file(tests_file)
    limit = inner_tool_limit_s(state, min(allowance, STAGE_CEILING_S["tests"]))
    res = state.runner.capture(
        [state.python_executable(), str(tests_file),
         "--results", TESTS_RESULTS_ARGUMENT],
        limit_s=limit, stage="tests", name=f"tests_{TAG}", cwd=state.base,
    )
    seconds = float(res.get("seconds", 0.0))
    output = (res.get("stdout") or "") + "\n" + (res.get("stderr") or "")
    tally = parse_tests_tally(output)
    values["exit_code"] = res.get("rc")
    values["seconds"] = round(seconds, 3)
    values["stdout_tail"] = last_lines(res.get("stdout"), 20)
    values["tests_passed"] = tally["tests_passed"]
    values["tests_total"] = tally["tests_total"]
    values["timed_out"] = bool(res.get("timed_out"))
    values["log"] = res.get("log")
    if tally["tests_passed"] is None:
        reason = "the tests printed no line reading 'tests: N of M passed'"
        values["null_reasons"]["tests_passed"] = reason
        values["null_reasons"]["tests_total"] = reason
    if values["exit_code"] is None:
        values["null_reasons"]["exit_code"] = "the tests never reported an exit code"
    state.note_unit("tests", seconds)
    state.tests_record = dict(values)

    if res.get("timed_out"):
        close("VOID", f"the tests did not finish inside {limit:.0f} seconds", True)
    if not res.get("started"):
        close("VOID", "the tests could not be started", True)
    if res.get("rc") != 0:
        close("FAIL", f"the tests exited {res.get('rc')}", True)
    close("PASS", "the tests passed", False)
    state.stages_done.append("tests")
    return dict(values)


def recorded_download_sha256(state: RunState, path) -> str:
    """The hash the held first attempt recorded for this file, or an empty string."""
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
    """True when the file on disk is the one a held attempt already fetched.

    After the box is held open and the run restarts, a file that is already
    here and still hashes to what the first attempt recorded is used again
    rather than fetched again. Anything else is fetched.
    """
    path = Path(path)
    if not path.exists():
        return False
    recorded = recorded_download_sha256(state, path)
    if not recorded:
        return False
    return sha256_file(path) == recorded


def stage_downloads(state: RunState) -> dict:
    """Fetch the declared files, unpack the parameters, and build the pairs.

    Only the two sources the design names are fetched, each recorded with its
    address and its hash. Nothing is downloaded inside any timed call later, so
    every file a timed call needs is here, complete, before the first one runs.
    """
    started = state.clock()
    allowance = guard_before_stage(state, "setup", UNIT_FLOOR_S["endpoints"])
    log = {"steps": [], "downloads": [], "started_utc": utc_of(started)}
    step = make_setup_step(state, allowance, log, "downloads")

    # -- the published structure
    pdb_path = state.datadir / f"{PDB_ENTRY}.pdb"
    pdb_reused = may_reuse_download(state, pdb_path)
    if not pdb_reused:
        res = step(["curl", "-fsSL", "--retry", "3", "-o", str(pdb_path), PDB_URL],
                   300, "download_pdb")
        if not res.get("ok") or not pdb_path.exists():
            raise HarnessFailure(
                f"downloading the published structure {PDB_ENTRY} failed",
                f"exit {res.get('rc')} from {PDB_URL}",
                kind="download",
            )
    log["downloads"].append({"what": f"PDB entry {PDB_ENTRY}", "url": PDB_URL,
                             "path": str(pdb_path), "sha256": sha256_file(pdb_path),
                             "reused": pdb_reused,
                             "bytes": pdb_path.stat().st_size})

    # -- the prediction parameters, fetched and unpacked before anything is timed
    params_dir = state.datadir / "params"
    params_dir.mkdir(parents=True, exist_ok=True)
    archive = state.datadir / "alphafold_params.tar"
    archive_reused = may_reuse_download(state, archive)
    if not archive_reused:
        res = step(["curl", "-fsSL", "--retry", "3", "-o", str(archive), AF_PARAMS_URL],
                   900, "download_params")
        if not res.get("ok") or not archive.exists():
            raise HarnessFailure(
                "downloading the AlphaFold parameter archive failed",
                f"exit {res.get('rc')} from {AF_PARAMS_URL}",
                kind="download",
            )
    state.params_sha256 = sha256_file(archive)
    log["downloads"].append({"what": "AlphaFold parameter archive",
                             "url": AF_PARAMS_URL, "path": str(archive),
                             "sha256": state.params_sha256,
                             "reused": archive_reused,
                             "bytes": archive.stat().st_size})
    res = step(["tar", "-xf", str(archive), "-C", str(params_dir)], 600, "extract_params")
    if not res.get("ok"):
        raise HarnessFailure("unpacking the parameter archive failed",
                             f"exit {res.get('rc')}", kind="download")
    missing = missing_multimer_params(params_dir)
    if missing:
        raise HarnessFailure(
            "the unpacked parameters do not hold a file for every model",
            "missing: " + ", ".join(missing),
            kind="download",
        )
    log["params_dir"] = str(params_dir)
    log["params_files"] = sorted(p.name for p in params_dir.glob("params_*multimer*.npz"))
    markers = write_parameter_markers(state, params_dir)
    log["params_markers"] = markers
    atomic_write_json(state.outdir / f"params_markers_tag-{TAG}.json", markers)

    # -- the one record of what came down the wire, cited by every later record
    download_record = state.outdir / f"downloads_tag-{TAG}.json"
    atomic_write_json(download_record, {
        "sources": list(ALLOWED_DOWNLOAD_HOSTS),
        "downloads": log["downloads"],
        "params_dir": str(params_dir),
        "params_files": log["params_files"],
        "note": ("the only two sources this run fetches from; no package index "
                 "is used anywhere, because nothing is installed on the box"),
    })
    state.download_record_path = download_record

    # -- the stand-in pairs, built and checked before any time is spent on them
    pairs = build_pairs(pdb_path.read_text())
    assert_pairs(pairs)
    state.pairs = pairs
    write_pair_evidence(state, pairs, pdb_path)
    log["pairs"] = [{"pair": p["pair"], "residues": p["total_residues"]} for p in pairs]

    log["setup_seconds_used"] = round(state.setup_seconds_used, 3)
    log["finished_utc"] = utc_of(state.clock())
    atomic_write_json(state.outdir / f"download_log_tag-{TAG}.json", log)
    state.stages_done.append("downloads")
    return log


MARKER_NAME_PATTERN = re.compile(
    r"([A-Za-z0-9_\-]*(?:download|complete|finished)[A-Za-z0-9_\-]*\.txt)",
    re.IGNORECASE,
)


def colabfold_marker_names(source_text: str) -> list:
    """The completion-marker file names a download module says it checks.

    The names are read out of the installed module's own source, never recalled
    from memory, because a name that is remembered wrong makes the first timed
    prediction call fetch its own parameters and stop being a timing.
    """
    names = []
    for name in MARKER_NAME_PATTERN.findall(str(source_text or "")):
        if name not in names:
            names.append(name)
    return names


def find_download_module(state: RunState):
    """Where the installed prediction front end keeps its download module."""
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
    """Write exactly the completion markers the installed module looks for."""
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
        atomic_write_text(path, "parameters unpacked by run_m4.py before any timed "
                                "call; written because the installed download "
                                "module checks for this file\n")
        written.append(str(path))
    return {"module": str(module), "markers": names, "written": written,
            "note": "marker names read from the installed module's own source"}


def missing_multimer_params(params_dir) -> list:
    """Which of the five model parameter files are absent."""
    present = {p.name for p in Path(params_dir).rglob("*.npz")}
    missing = []
    for i in range(1, AF2_MODELS + 1):
        wanted = [n for n in present if f"model_{i}" in n and "multimer" in n]
        if not wanted:
            missing.append(f"model_{i} multimer parameters")
    return missing


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

# The tools asked to print their own help before any money is spent on them.
SMOKE_HELP_TOOLS = ("colabfold_batch", "lightdock3.py",
                    "lgd_generate_conformations.py")


def smoke_check(state: RunState, step, params_dir) -> dict:
    """Ask every tool, on this box, whether it can do what the run needs.

    Recollection does not decide this; the tools do. A tool that cannot be
    found on the virtual environment's search path, cannot print its own help,
    or cannot see the graphics processor, stops the run here.
    """
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
        path = shutil.which(tool, path=env["PATH"])
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

    # The parameters are fetched after this check, so they are reported here
    # only when a directory is given; whether they are complete is decided in
    # the download stage, which is the stage that unpacks them.
    if params_dir is not None:
        found["params_dir"] = str(params_dir)
        found["params_present"] = not missing_multimer_params(params_dir)
        if not found["params_present"]:
            problems.append("model parameter files are missing after unpacking")
    return {"ok": not problems, "problems": problems, "found": found}


# ===========================================================================
# STAGE: CONTROLS
# Before any band is compared, the timing harness itself is shown to be honest.
# ===========================================================================


def timed_call(state: RunState, name: str, cmd: list, limit_s: float, stage: str,
               cwd=None, extra_env=None) -> dict:
    """One timed tool call, with its own working directory, through the harness.

    The same wrapper times the planted sleep, the empty run and every real tool,
    so the overhead the controls measure is the overhead the measurements carry.
    """
    work = state.workdir / f"{stage}_{name}"
    work.mkdir(parents=True, exist_ok=True)
    before = state.clock()
    res = state.runner.capture(
        cmd, limit_s=inner_tool_limit_s(state, limit_s), stage=stage, name=name,
        cwd=cwd or work, extra_env=extra_env,
    )
    after = state.clock()
    res["work_dir"] = str(work)
    res["work_dir_bytes"] = apparent_bytes(work)
    res["harness_seconds"] = after - before
    return res


def corrected_seconds(state: RunState, seconds: float) -> float:
    """Take off the harness overhead the empty-input control measured, if any."""
    if state.overhead_s <= 0:
        return seconds
    return max(0.0, seconds - state.overhead_s)


def stage_controls(state: RunState) -> dict:
    """Run the three checks that decide whether any later number means anything.

    First a sleep of known length, timed by the same harness: if sixty seconds
    do not read back as sixty seconds the harness is wrong and the run stops.
    Then an empty run, which times the harness around a command that does
    nothing, so setup time and setup bytes are known and can be taken off. Then
    a statement of the units and the scale, written before any band is compared.
    """
    started = state.clock()
    guard_before_stage(state, "controls", SLEEP_CONTROL_S + UNIT_FLOOR_S["endpoints"])
    out = {}

    # -- the planted sleep
    sleep_started = state.clock()
    res = timed_call(state, "sleep60", ["sleep", str(int(SLEEP_CONTROL_S))],
                     SLEEP_CONTROL_S + 120, "controls")
    sleep_finished = state.clock()
    measured = res.get("harness_seconds")
    error = abs(measured - SLEEP_CONTROL_S) / SLEEP_CONTROL_S if measured else None
    add_row(state, "controls", {"control": "planted_sleep", "planted_s": SLEEP_CONTROL_S,
                                "measured_s": measured, "relative_error": error,
                                "rc": res.get("rc"), "timed_out": res.get("timed_out")})
    sleep_ok = bool(res.get("ok")) and error is not None and error <= SLEEP_CONTROL_TOLERANCE
    if not sleep_ok:
        state.void_run(
            f"the planted {int(SLEEP_CONTROL_S)} s sleep read back as "
            f"{measured:.3f} s, an error of "
            f"{(error if error is not None else float('nan')):.4f}"
        )
    write_record(
        state, f"control-sleep_tag-{TAG}.json", kind="control_sleep",
        cell={"stage": "controls", "control": "planted_sleep", "tag": TAG},
        inputs=record_inputs(state, state.outdir / f"rows_controls_tag-{TAG}.jsonl"),
        metric="relative error of a planted 60 s sleep timed by the run's own harness",
        values={"planted_s": SLEEP_CONTROL_S, "measured_s": measured,
                "relative_error": error, "unit": "seconds"},
        threshold={"max_relative_error": SLEEP_CONTROL_TOLERANCE},
        decision_rule=("relative error at most 0.05 -> PASS and the timings may be "
                       "trusted; otherwise FAIL, every timing in this run is invalid, "
                       "and the run stops"),
        decision="PASS" if sleep_ok else "FAIL",
        labels=labels_for_record(state, sleep_started, sleep_finished),
    )
    out["sleep"] = {"measured_s": measured, "relative_error": error, "ok": sleep_ok}
    if not sleep_ok:
        raise HarnessFailure(
            "the planted sleep check failed; the timing harness is not trustworthy",
            f"measured {measured} s against {SLEEP_CONTROL_S} s",
            # Named, because this is the one failure the box is never held open
            # for: a clock this run cannot trust is not a thing a fixer mends.
            kind="sleep_check",
        )

    # -- the empty-input run
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
        metric="wall-clock seconds and bytes written by the harness around a command "
               "that does nothing",
        values={"measured_s": empty_s, "work_dir_bytes": empty_bytes,
                "unit": "seconds and bytes",
                "overhead_subtracted_s": state.overhead_s,
                "overhead_subtracted_bytes": state.overhead_bytes},
        threshold={"max_seconds": EMPTY_RUN_MAX_S, "max_bytes": EMPTY_RUN_MAX_BYTES},
        decision_rule=("under 2 s and under 1 MiB -> PASS and nothing is subtracted; "
                       "otherwise VOID for this control, and exactly that much harness "
                       "overhead is taken off later values, labelled"),
        decision="PASS" if empty_ok else "VOID",
        labels=labels_for_record(state, empty_started, empty_finished),
        extra_notes=labels_extra,
    )
    out["empty_run"] = {"measured_s": empty_s, "bytes": empty_bytes, "ok": empty_ok}

    # -- the statement of units and scale
    unit_started = state.clock()
    scale = {
        "af2_hours_from_seconds": {
            "rule": "wall-clock seconds of one prediction call divided by 3,600",
            "worked_example": {"seconds": 1800, "hours": 1800 / 3600.0},
            "unit": CARD["C1"]["unit"],
        },
        "md_ns_per_day_from_steps": {
            "rule": "steps times the timestep gives simulated femtoseconds; divided "
                    "by the production wall-clock and scaled to 86,400 seconds",
            "worked_example": {
                "steps": 250000, "timestep_fs": 2.0, "wallclock_s": 335,
                "ns_per_day": round(ns_per_day_from_wallclock(250000, 2.0, 335), 2),
            },
            "engine_rate_line_example": "Speed (ns/day) column of the reporter file, "
                                        "read beside the wall-clock figure",
            "unit": CARD["C2"]["unit"],
        },
        "aux_hours_from_seconds": {
            "rule": "wall-clock seconds of docking, interface analysis and writing "
                    "the call-table row for one pair, divided by 3,600",
            "worked_example": {"seconds": 3600, "hours": 1.0},
            "unit": CARD["C3"]["unit"],
        },
        "storage_gib_from_bytes": {
            "rule": f"apparent bytes written by one run times {GRID_RUNS} divided by "
                    "2 to the power 30",
            "worked_example": {
                "bytes_per_run": BYTES_PER_GIB,
                "gib_216_runs": storage_from_bytes(BYTES_PER_GIB)["gib_216_runs"],
                "gib_432_runs": storage_from_bytes(BYTES_PER_GIB)["gib_432_runs"],
            },
            "unit": CARD["C4"]["unit"],
        },
    }
    # What this record holds, said plainly: worked examples of each conversion,
    # and the names of the files where the raw numbers themselves will appear.
    # The raw numbers cannot be in this record: the order of stages puts the
    # controls before any prediction, dynamics or storage measurement exists,
    # so copying them here would mean copying them from nowhere.
    scale["kind"] = "worked_examples"
    scale["raw_values_in"] = {
        "raw_alphafold_seconds_per_run": f"rows_af2_tag-{TAG}.jsonl",
        "md_engine_rate_lines_with_wallclock_beside_them": f"rows_md_tag-{TAG}.jsonl",
        "raw_bytes_per_artifact": f"rows_storage_tag-{TAG}.jsonl",
        "note": ("this control holds worked examples only; the raw values live in "
                 "the row files named here, which are written later in the run"),
    }
    atomic_write_json(state.outdir / f"unit_and_scale_tag-{TAG}.json", scale)
    write_record(
        state, f"control-unit-and-scale_tag-{TAG}.json",
        kind="control_unit_and_scale",
        cell={"stage": "controls", "control": "unit_and_scale", "tag": TAG},
        inputs=record_inputs(state),
        metric="the raw units each input is read in, and the arithmetic that turns "
               "raw output into the card's unit",
        values=scale,
        threshold={"required": "stated before any band is compared"},
        decision_rule=("this control decides nothing; it exists so a reader can "
                       "re-derive every later number from raw output"),
        decision="RECORDED",
        labels=labels_for_record(state, unit_started, state.clock()),
    )
    out["unit_and_scale"] = scale
    out["seconds"] = state.clock() - started
    state.stages_done.append("controls")
    return out


# ===========================================================================
# DOCKING
# One docking code. The pose that is used is always the one the tool itself
# ranked first; there is no fallback to whichever file sorts first by name.
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
    """Keep what the table and the working directory looked like, before raising.

    A reader who never saw this run must be able to tell, from this one file,
    what the tool actually wrote and what it left on disk. Only names are
    listed, never contents.
    """
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
        "",
        "data lines: %d" % shape["data_lines"],
        "field counts of the data lines: %s"
        % ", ".join(str(c) for c in shape["field_counts"]),
        "header tokens: %s" % ", ".join(shape["header"]),
        "",
        "names in the docking working directory (depth 1):",
    ]
    lines += ["  %s" % e for e in entries] or ["  <empty>"]
    lines += ["", "names in %s (depth 1):" % swarm_name]
    lines += ["  %s" % e for e in swarm_entries] or ["  <none>"]
    path = state.outdir / f"rank_table_diagnostic_{name}_tag-{TAG}.txt"
    atomic_write_text(path, "\n".join(lines) + "\n")
    return path


def run_docking(state: RunState, name: str, receptor_pdb: Path, ligand_pdb: Path,
                work: Path, limit_s: float, cores: int, stage: str) -> dict:
    """Dock one receptor onto one capsid and return the tool's own best pose.

    Three outcomes, and they never overlap. Running past the time allowed is a
    ceiling stop. A tool that fails, or that leaves no readable ranked list or
    no named pose file, is broken infrastructure. Only a pose that was obtained
    and compared can miss the anchor.
    """
    work = Path(work)
    work.mkdir(parents=True, exist_ok=True)
    # Each docking run gets its own copy of the two structures inside its own
    # working directory. The preparation step writes its processed files beside
    # the structure files it is given; with one shared copy the second run finds
    # the first run's files already there, reports an error, and writes no
    # configuration file for the search step to open.
    local_receptor = work / Path(receptor_pdb).name
    local_ligand = work / Path(ligand_pdb).name
    for src, dest in ((receptor_pdb, local_receptor), (ligand_pdb, local_ligand)):
        if Path(src).resolve() != dest.resolve():
            shutil.copyfile(str(src), str(dest))
    receptor_pdb, ligand_pdb = local_receptor, local_ligand
    bin_dir = state.venv_bin()
    swarms, glowworms, steps = DOCKING_SWARMS, DOCKING_GLOWWORMS, DOCKING_STEPS
    started = state.clock()
    budget = limit_s
    order = []

    def call(cmd, step_name, cwd=None):
        nonlocal budget
        order.append(step_name)
        left = inner_tool_limit_s(state, budget)
        res = state.runner.capture(
            cmd, limit_s=max(1.0, left), stage=stage,
            name=f"{name}_{step_name}", cwd=cwd or work,
        )
        budget -= res.get("seconds", 0.0)
        return res

    setup = call(
        [str(bin_dir / "lightdock3_setup.py"), str(receptor_pdb), str(ligand_pdb),
         "-s", str(swarms), "-g", str(glowworms), "--noxt", "--noh"],
        "setup",
    )
    if setup.get("timed_out"):
        raise GuardStop("the docking setup ran past the time allowed for it",
                        stage=stage, detail=setup.get("log", ""))
    if not setup.get("ok"):
        raise HarnessFailure("the docking setup failed",
                             f"exit {setup.get('rc')}, see {setup.get('log')}")
    # The preparation step can report an error in its output and still exit 0.
    # An error line means it wrote no configuration file, so it is a failure.
    setup_errors = [line.strip() for line in setup.get("stdout", "").splitlines()
                    if "ERROR" in line]
    if setup_errors:
        raise HarnessFailure(
            "the docking setup failed",
            f"exit {setup.get('rc')} with an error line in its output: "
            f"{setup_errors[0]}; see {setup.get('log')}")

    sim = call(
        [str(bin_dir / "lightdock3.py"), "setup.json", str(steps), "-c", str(max(1, cores))],
        "simulate",
    )
    if sim.get("timed_out"):
        raise GuardStop("the docking run ran past the time allowed for it",
                        stage=stage, detail=sim.get("log", ""))
    if not sim.get("ok"):
        raise HarnessFailure("the docking run failed",
                             f"exit {sim.get('rc')}, see {sim.get('log')}")

    # The search leaves numbers; this step turns them into pose structures.
    # Without it there is no pose file to compare, and the run would end as
    # broken infrastructure at the anchor with nothing to show for the money.
    swarm_dirs = sorted(p for p in work.glob("swarm_*") if p.is_dir())
    if not swarm_dirs:
        raise HarnessFailure(
            "the docking run left no swarm directory to build poses from",
            f"nothing matching swarm_* in {work}")
    for swarm_dir in swarm_dirs:
        gen = call(
            [str(bin_dir / "lgd_generate_conformations.py"),
             str(receptor_pdb), str(ligand_pdb),
             f"gso_{steps}.out", str(glowworms)],
            "generate_conformations", cwd=swarm_dir,
        )
        if gen.get("timed_out"):
            raise GuardStop("building the docked pose structures ran past the "
                            "time allowed for it",
                            stage=stage, detail=gen.get("log", ""))
        if not gen.get("ok"):
            raise HarnessFailure("building the docked pose structures failed",
                                 f"exit {gen.get('rc')}, see {gen.get('log')}")

    rank = call([str(bin_dir / "lgd_rank.py"), str(swarms), str(steps)], "rank")
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
        rows = parse_rank_table(table_text)
        top = top_ranked_row(rows)
    except ParseError as exc:
        diagnostic = write_rank_table_diagnostic(state, name, table_text, work)
        raise HarnessFailure(
            "the docking rank table could not be read",
            f"{exc}; field counts of the data lines: {counts_text}; "
            f"{first_raw_lines(table_text)}; raw table kept at {kept}; "
            f"diagnostic at {diagnostic}",
        )
    pose = pose_path_from_row(work, top)
    if pose is None or not Path(pose).exists():
        diagnostic = write_rank_table_diagnostic(state, name, table_text, work)
        raise HarnessFailure(
            "the docking rank table names no pose file that exists",
            f"top row {top}; field counts of the data lines: {counts_text}; "
            f"{first_raw_lines(table_text)}; raw table kept at {kept}; "
            f"diagnostic at {diagnostic}",
        )
    pose_kept = state.outdir / f"pose_{name}_tag-{TAG}.pdb"
    shutil.copyfile(str(pose), str(pose_kept))
    seconds = state.clock() - started
    return {
        "name": name,
        "seconds": seconds,
        "cores": cores,
        "rank_table": str(kept),
        "rank_rows": len(rows),
        "top_row": top,
        "pose_path": str(pose_kept),
        "pose_text": Path(pose_kept).read_text(),
        "call_order": order,
        "parameters": {"swarms": swarms, "glowworms": glowworms, "steps": steps,
                       "cores": cores, "setup_flags": ["--noxt", "--noh"],
                       "restrained_to_the_published_interface": False,
                       "rank_table_columns": rows.columns()},
    }


def split_published_structure(state: RunState, pdb_text: str) -> dict:
    """Separate the published complex into the two halves the anchor redocks."""
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
    return {
        "chain_map": chain_map,
        "native_role_atoms": native,
        "capsid_pdb": cap_path,
        "receptor_pdb": rec_path,
        "receptor_chain": roles["receptor_chain"],
        "capsid_chains": roles["capsid_chains"],
    }


def pose_frame_shift(native_capsid_atoms: list, pose_capsid_atoms: list) -> dict:
    """Translation that carries a docked pose into the published structure's frame.

    The docking code works in a frame of its own, centred on the origin, and
    writes its poses there. Scoring such a pose against the published structure
    without moving it first measures the gap between two coordinate frames, not
    how well the pose reproduces the published placement. The capsid half is
    held rigid by the docking code and appears in both files, so the shift that
    puts the pose's capsid atoms onto the published capsid atoms is the shift
    the whole pose needs. Atoms are matched by chain letter, residue number,
    insertion code and atom name; preparation drops atoms, so only atoms present
    in both are used, and their mean displacement is the shift.
    """
    native_by_key = {}
    for a in native_capsid_atoms:
        native_by_key.setdefault(
            (a["chain"], a["resseq"], a.get("icode", ""), a["name"]), a)
    sums = [0.0, 0.0, 0.0]
    matched = 0
    for b in pose_capsid_atoms:
        a = native_by_key.get(
            (b["chain"], b["resseq"], b.get("icode", ""), b["name"]))
        if a is None:
            continue
        matched += 1
        sums[0] += a["x"] - b["x"]
        sums[1] += a["y"] - b["y"]
        sums[2] += a["z"] - b["z"]
    if matched:
        return {"dx": sums[0] / matched, "dy": sums[1] / matched,
                "dz": sums[2] / matched, "matched_atoms": matched,
                "basis": "capsid atoms matched by chain, residue and atom name"}
    if native_capsid_atoms and pose_capsid_atoms:
        # The docking code may rename chains or renumber residues. The capsid is
        # the same body in both files, so its centre still fixes the shift.
        def centre(atoms):
            n = float(len(atoms))
            return (sum(a["x"] for a in atoms) / n,
                    sum(a["y"] for a in atoms) / n,
                    sum(a["z"] for a in atoms) / n)
        nx, ny, nz = centre(native_capsid_atoms)
        px, py, pz = centre(pose_capsid_atoms)
        return {"dx": nx - px, "dy": ny - py, "dz": nz - pz,
                "matched_atoms": 0,
                "basis": "centres of the capsid atoms; no atom names matched"}
    return {"dx": 0.0, "dy": 0.0, "dz": 0.0, "matched_atoms": 0,
            "basis": "no capsid atoms in the pose; the pose is left where it is"}


def score_pose_against_native(native_role_atoms: list, pose_text: str,
                              capsid_atoms: list, receptor_chain_guess=None) -> dict:
    """Compare one docked pose with the published placement.

    The pose's chains are renamed to the parts they play before anything is
    compared, so a tool that relabels its output cannot change the score.
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
    # The pose is written in the docking code's own frame. Put it back into the
    # published structure's frame before any contact or distance is computed.
    shift = pose_frame_shift(capsid_atoms,
                             [a for a in pose_roles if a["role"] == "capsid"])
    pose_roles = [dict(a, x=a["x"] + shift["dx"], y=a["y"] + shift["dy"],
                       z=a["z"] + shift["dz"]) for a in pose_roles]
    if not [a for a in pose_roles if a["role"] == "capsid"]:
        pose_roles = pose_roles + [
            dict(a, role="capsid") for a in map_chain_roles(
                capsid_atoms, {c: "capsid" for c in capsid_ids})
        ]
    reference_contacts = contact_pairs_by_index(native_role_atoms)
    pose_contacts = contact_pairs_by_index(pose_roles)
    overlap = contact_overlap(reference_contacts, pose_contacts)
    iface = interface_backbone_rmsd(native_role_atoms, pose_roles)
    return {
        "overlap": overlap,
        "interface_backbone_rmsd_a": iface,
        "n_reference_contacts": len(reference_contacts),
        "n_pose_contacts": len(pose_contacts),
        "call": "bind" if (overlap >= ANCHOR_OVERLAP_MIN
                           or iface <= ANCHOR_IFACE_RMSD_MAX) else "no-bind",
        "frame_shift": shift,
        "pose_role_atoms": pose_roles,
    }


# ===========================================================================
# WRITING ONE INPUT'S RECORD
# ===========================================================================


def emit_input_record(state: RunState, cid: str, measured, *, n, rows_arm,
                      start_epoch, end_epoch, extra_values=None, extra_notes=None,
                      void_reason=None, labels_extra=None, stop_kind=None):
    """Write the record for one of the four inputs, decided against its own band.

    A value that cannot be decided keeps its raw number and says why it is void,
    because a void with the number thrown away cannot be checked later.
    """
    spec = CARD[cid]
    notes = [LABEL_STAND_IN, LABEL_ONE_GPU] + list(extra_notes or [])
    if cid == "C1":
        notes.append(LABEL_NO_MSA)
    if cid == "C3":
        notes.append(LABEL_AUX_READING)
    if cid == "C4":
        notes.append(LABEL_STORAGE)

    if void_reason:
        outcome = {"decision": "VOID", "marginal": False, "reason": void_reason}
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
        "null_reasons": {},
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
            f"inside {spec['band']} -> PASS; outside -> FAIL; within 10 percent of "
            "either edge -> VOID and marginal; below the minimum sample, on a wrong "
            "graphics processor, with zero spread across seeds, or left unmeasured by "
            "a stop -> VOID with the raw rows kept"
        ),
        decision=outcome["decision"],
        labels=labels_for_record(state, start_epoch, end_epoch, labels_extra),
        extra_notes=notes,
    )
    # Exactly one status word, from the one table the directive gives.
    if state.anchor_missed:
        state.set_void_by_anchor_miss(cid, state.anchor_missed)
    elif state.failure_kind:
        state.set_void_by_failure(cid, state.failure_kind,
                                  state.run_valid_voided_by or state.failure_kind)
    elif void_reason and LABEL_UNMEASURED in str(void_reason):
        state.set_unmeasured(cid, stop_kind or state.last_stop_kind())
    elif void_reason or outcome["decision"] == "VOID":
        state.set_decided(cid, "VOID", void_reason or outcome["reason"])
    else:
        state.set_decided(cid, outcome["decision"], None)
    return outcome


# ===========================================================================
# STAGE: ANCHOR
# ===========================================================================


def stage_anchor(state: RunState) -> dict:
    """Redock the receptor onto the capsid and check it lands where it should.

    This runs before any input is measured. Serial first, then in parallel on
    the same box, and the two must agree. A miss here voids every input.
    """
    started = state.clock()
    estimate = state.unit_estimate("anchor_serial") + state.unit_estimate("anchor_parallel")
    allowance = guard_before_stage(state, "anchor", estimate)
    pdb_path = state.datadir / f"{PDB_ENTRY}.pdb"
    if not pdb_path.exists():
        raise HarnessFailure("the published structure is missing before the anchor",
                             str(pdb_path))
    split = split_published_structure(state, pdb_path.read_text())
    capsid_atoms = [a for a in read_pdb_atoms(pdb_path.read_text())
                    if split["chain_map"].get(a["chain"]) == "capsid"]

    results = {}
    for name, cores, kind in (("serial", 1, "anchor_serial"), ("parallel", 4, "anchor_parallel")):
        guard_before_unit(state, "anchor", kind, allowance - (state.clock() - started))
        unit_started = state.clock()
        dock = run_docking(
            state, f"anchor_{name}", split["capsid_pdb"], split["receptor_pdb"],
            state.workdir / f"anchor_{name}", limit_s=min(
                allowance - (state.clock() - started), PER_PAIR_DOCKING_CEILING_S),
            cores=cores, stage="anchor",
        )
        state.note_unit(kind, state.clock() - unit_started)
        scored = score_pose_against_native(
            split["native_role_atoms"], dock["pose_text"], capsid_atoms)
        results[name] = {"dock": dock, "scored": scored}
        add_row(state, "anchor", {
            "which": name, "cores": cores, "seconds": dock["seconds"],
            "overlap": scored["overlap"],
            "interface_backbone_rmsd_a": scored["interface_backbone_rmsd_a"],
            "n_reference_contacts": scored["n_reference_contacts"],
            "call": scored["call"], "rank_table": dock["rank_table"],
            "pose_path": dock["pose_path"], "top_row": dock["top_row"],
        })

    serial = results["serial"]["scored"]
    parallel = results["parallel"]["scored"]
    sp_rmsd = whole_chain_rmsd(serial["pose_role_atoms"], parallel["pose_role_atoms"])
    calls_identical = serial["call"] == parallel["call"]
    verdict = anchor_decision(serial["overlap"], serial["interface_backbone_rmsd_a"],
                              sp_rmsd, calls_identical)
    finished = state.clock()

    if verdict["decision"] != "PASS":
        state.void_run(
            "the anchor redocking missed its tolerance against the published "
            f"placement: overlap {verdict['overlap']:.4f}, interface backbone RMSD "
            f"{verdict['interface_backbone_rmsd_a']:.4f} A, serial-versus-parallel "
            f"RMSD {sp_rmsd:.4f} A, calls identical {calls_identical}"
        )

    write_record(
        state, f"endpoint-anchor_tag-{TAG}.json", kind="anchor",
        cell={"stage": "anchor", "endpoint": "anchor", "tag": TAG},
        inputs=record_inputs(state, state.outdir / f"rows_anchor_tag-{TAG}.jsonl",
                             extra_paths=[pdb_path]),
        metric=("contact overlap with the published complex at 4.5 angstrom, or "
                "interface backbone displacement, with serial and parallel agreement"),
        values={
            "measured": verdict["overlap"],
            "published": (f"AAVR-PKD2 bound to the AAV2 spike region adjacent to the "
                          f"icosahedral three-fold axis (PDB {PDB_ENTRY})"),
            "tolerance": {
                "min_contact_overlap": ANCHOR_OVERLAP_MIN,
                "max_interface_backbone_rmsd_a": ANCHOR_IFACE_RMSD_MAX,
                "max_serial_parallel_rmsd_a": ANCHOR_SERIAL_PARALLEL_RMSD_MAX,
                "calls_must_be_identical": True,
            },
            "contact_overlap": verdict["overlap"],
            "interface_backbone_rmsd_a": verdict["interface_backbone_rmsd_a"],
            "serial_parallel_rmsd_a": sp_rmsd,
            "serial_call": serial["call"],
            "parallel_call": parallel["call"],
            "calls_identical": calls_identical,
            "unit": "fraction of published contacts, and angstrom",
            "independent_code": ANCHOR_INDEPENDENT_CODE,
            "docking_order": DOCKING_ORDER,
            "docking_order_as_called": results["serial"]["dock"]["call_order"],
            "docking_order_source": (
                "the on-box execution contract states no order for the docking "
                "commands, so the order is prepare, search, build the poses, rank"
            ),
            "docking_parameters": results["serial"]["dock"]["parameters"],
            "docking_parameters_same_for_pairs": True,
        },
        threshold={"min_contact_overlap": ANCHOR_OVERLAP_MIN,
                   "max_interface_backbone_rmsd_a": ANCHOR_IFACE_RMSD_MAX,
                   "max_serial_parallel_rmsd_a": ANCHOR_SERIAL_PARALLEL_RMSD_MAX},
        decision_rule=("PASS when the pose reproduces the published placement "
                       "(contact overlap at least 0.50 or interface backbone RMSD at "
                       "most 5.0 angstrom) AND serial and parallel agree (top-pose "
                       "RMSD at most 2.0 angstrom with identical bind or no-bind "
                       "calls); otherwise FAIL, every input is void and the run stops"),
        decision=verdict["decision"],
        labels=labels_for_record(state, started, finished),
        extra_notes=[LABEL_SERIAL_PARALLEL_WHOLE_CHAIN],
    )
    state.anchor = {"verdict": verdict, "serial_parallel_rmsd_a": sp_rmsd,
                    "calls_identical": calls_identical}
    if verdict["decision"] != "PASS":
        raise AnchorMiss("the anchor redocking missed its tolerance", verdict)
    state.stages_done.append("anchor")
    return state.anchor


# ===========================================================================
# STAGE: PER-PAIR DOCKING AND INTERFACE ANALYSIS (INPUT C3)
# ===========================================================================


def threefold_axis_distance(points: list) -> float:
    """Distance from a set of points' centre to the nearest three-fold axis.

    An icosahedral capsid is deposited in the two-fold setting: its three-fold
    axes are the four lines through the origin along the body diagonals of the
    coordinate cube. The distance reported is from the centre of the interface
    to the nearest of those four lines, which is the quantity the card's call
    table asks for.
    """
    if not points:
        return float("nan")
    n = float(len(points))
    centre = (sum(p[0] for p in points) / n,
              sum(p[1] for p in points) / n,
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
    """Describe the interface a docked pose makes, in the terms the card uses."""
    contacts = contact_pairs_by_index(pose_role_atoms)
    residues = sorted({r for (_c, r) in contacts})
    coords = [
        (a["x"], a["y"], a["z"])
        for a in pose_role_atoms
        if a["role"] == "receptor" and a["resseq"] in set(residues)
    ]
    distance = threefold_axis_distance(coords)
    site_class = "spike" if distance <= 25.0 else "floor"
    reference = contact_pairs_by_index(native_role_atoms)
    return {
        "n_contacts": len(contacts),
        "interface_residues": residues,
        "n_interface_residues": len(residues),
        "distance_to_nearest_threefold_axis_a": distance,
        "site_class": site_class,
        "contact_overlap_with_published": contact_overlap(reference, contacts),
        "call": "bind" if contacts else "no-bind",
    }


def stage_aux(state: RunState) -> dict:
    """Time everything per pair that is neither prediction nor dynamics.

    What is timed: docking, the interface analysis, and writing the pair's row
    of the call table. Installs, downloads and setup are not in it.
    """
    started = state.clock()
    allowance = guard_before_stage(state, "aux", state.unit_estimate("docking_pair"))
    pdb_path = state.datadir / f"{PDB_ENTRY}.pdb"
    split = split_published_structure(state, pdb_path.read_text())
    call_table = []
    finished_pairs = []
    stopped = None

    for pair in state.pairs:
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
        truncated = False
        try:
            dock = run_docking(state, f"aux_{pair['pair']}", cap_pdb, rec_pdb, work,
                               limit_s=pair_cap, cores=4, stage="aux")
        except GuardStop as stop:
            # A pair that reaches its own 250 s cap is kept as a row, is left
            # out of the mean, and the loop goes on to the next pair. Stopping
            # the whole stage on one slow pair would throw away the pairs that
            # would have finished, and the input needs only two of them.
            truncated = True
            add_row(state, "aux", {
                "pair": pair["pair"], "seconds": state.clock() - unit_started,
                "truncated": True, "incomplete": True, "why": stop.reason,
            })
            stopped = stop
            continue
        pose_roles = score_pose_against_native(
            split["native_role_atoms"], dock["pose_text"], capsid_atoms)
        analysis = interface_analysis(split["native_role_atoms"],
                                      pose_roles["pose_role_atoms"])
        row_for_table = {
            "pair": pair["pair"],
            "capsid_slot": pair["capsid_slot"],
            "call": analysis["call"],
            "score": dock["top_row"],
            "n_interface_residues": analysis["n_interface_residues"],
            "interface_residues": analysis["interface_residues"],
            "distance_to_nearest_threefold_axis_a":
                analysis["distance_to_nearest_threefold_axis_a"],
            "site_class": analysis["site_class"],
        }
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
        })
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
        void_reason=void_reason,
    )
    if stopped is None:
        state.stages_done.append("aux")
    return {"n": n, "measured": measured, "stopped": bool(stopped)}


# ===========================================================================
# STAGE: ALPHAFOLD-MULTIMER TIMINGS (INPUT C1)
# ===========================================================================


def af2_command(state: RunState, fasta: Path, out_dir: Path, seed: int) -> list:
    """The prediction command line, with the card's own protocol settings.

    Five models, exactly twenty recycles, early stopping off, and single
    sequences only: no sequence database is downloaded and no remote alignment
    service is contacted. That last choice makes the measured hours lower than
    the card's real setting, and every record says so.
    """
    return [
        str(state.venv_bin() / "colabfold_batch"),
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


def stage_af2(state: RunState) -> dict:
    """Time one whole prediction call per pair per seed, seed by seed.

    Seed-major order means the first pass already covers all three pairs, so a
    stop part way through still leaves a sample that spans the pairs rather
    than three repeats of one pair.
    """
    started = state.clock()
    allowance = guard_before_stage(state, "af2", state.unit_estimate("af2_run"))
    rows = []
    per_pair_times = {}
    stopped = None

    for seed in AF2_SEEDS:
        if stopped:
            break
        for pair in state.pairs:
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
                limit_s=left, stage="af2",
            )
            seconds = res.get("harness_seconds")
            parsed = parse_colabfold_log(res.get("stdout", "") + res.get("stderr", ""))
            row = {
                "pair": pair["pair"], "seed": seed,
                "wallclock_s": seconds,
                "wallclock_s_corrected": corrected_seconds(state, seconds),
                "hours": corrected_seconds(state, seconds) / 3600.0,
                "per_model_s": parsed["per_model_s"],
                "compile_excluded_s": (sum(parsed["per_model_s"][1:])
                                       if len(parsed["per_model_s"]) > 1 else None),
                "download_in_timed_call": parsed["download_in_timed_call"],
                "incomplete": bool(res.get("timed_out")),
                "rc": res.get("rc"),
                "models": AF2_MODELS, "recycles": AF2_RECYCLES,
                "msa_mode": "single_sequence",
                "out_dir_bytes": res.get("work_dir_bytes"),
                "log": res.get("log"),
            }
            add_row(state, "af2", row)
            rows.append(row)
            if res.get("timed_out"):
                stopped = GuardStop(
                    "a prediction call ran past the time allowed for it",
                    stage="af2", detail=res.get("log", ""))
                break
            if not res.get("ok"):
                raise HarnessFailure(
                    "a prediction call failed",
                    f"exit {res.get('rc')}, see {res.get('log')}")
            state.note_unit("af2_run", state.clock() - unit_started)
            per_pair_times.setdefault(pair["pair"], []).append(
                corrected_seconds(state, seconds))
            pair.setdefault("af2_out_dirs", []).append(str(out_dir))

    finished = state.clock()
    if stopped is not None:
        state.record_stop("ceiling_or_guard", "af2", stopped.reason)

    summary = parse_af2_timing_rows(rows)
    spread = spread_check(per_pair_times)
    state.af2_spread = spread
    measured = summary["mean_h"]
    n = summary["n"]
    notes = list(state.overhead_labels)
    labels_extra = None
    void_reason = None

    if any(r.get("download_in_timed_call") for r in rows):
        void_reason = "download inside timed call"
    elif not state.gpu_is_a100:
        void_reason = LABEL_NOT_A100
        notes.append(LABEL_NOT_A100)
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

    emit_input_record(
        state, "C1", measured, n=n, rows_arm="af2",
        start_epoch=started, end_epoch=finished,
        extra_values={
            "runs_counted": n,
            "pairs_covered": summary["pairs"],
            "per_run_hours": summary["hours"],
            "seed_spread": spread["per_pair"],
            "halt": spread["halt"],
            "models": AF2_MODELS, "recycles": AF2_RECYCLES,
            "early_stopping": "off", "msa_mode": "single_sequence",
            "compile_included": True,
        },
        extra_notes=notes, void_reason=void_reason, labels_extra=labels_extra,
    )
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


def stage_md(state: RunState) -> dict:
    """Time one short production segment per docked complex and read its speed.

    Two speeds are taken for each complex: the engine's own, from its reporter
    file, and one worked out from the steps done and the clock. The clock
    figure decides; when the two differ by more than a twentieth, both are
    reported and labelled.
    """
    started = state.clock()
    allowance = guard_before_stage(state, "md", state.unit_estimate("md_complex"))
    worker = md_worker_path(state)
    steps = int(round(MD_PRODUCTION_NS * 1e6 / MD_TIMESTEP_FS))
    rates = []
    rows = []
    stopped = None
    any_size_fault = None

    for pair in state.pairs:
        left = allowance - (state.clock() - started)
        try:
            guard_before_unit(state, "md", "md_complex", left)
        except GuardStop as stop:
            stopped = stop
            break
        if not pair.get("pose_text"):
            rows.append({"complex": pair["pair"], "skipped": "no docked pose"})
            add_row(state, "md", {"complex": pair["pair"],
                                  "skipped": "no docked pose for this pair"})
            continue
        unit_started = state.clock()
        cap = min(PER_COMPLEX_MD_CEILING_S, left)
        work = state.workdir / f"md_{pair['pair']}"
        work.mkdir(parents=True, exist_ok=True)
        pose_atoms = [a for a in read_pdb_atoms(pair["pose_text"])
                      if a["chain"] != pair["receptor_chain"] or True]
        receptor_pose = [a for a in pose_atoms
                         if a["chain"] not in
                         [c for c, r in pair["chain_map"].items() if r == "capsid"]]
        merged = merge_capsid_and_pose(pair, receptor_pose or pose_atoms)
        merged_pdb = work / "complex.pdb"
        atomic_write_text(merged_pdb, write_pdb(merged))

        padding = water_padding_nm(merged)
        built = None
        for attempt in (1, 2):
            out_json = work / f"build_{attempt}.json"
            res = state.runner.capture(
                [state.python_executable(), str(worker), "--mode", "build",
                 "--pdb", str(merged_pdb), "--work", str(work),
                 "--padding-nm", f"{padding:.3f}", "--out", str(out_json)],
                limit_s=inner_tool_limit_s(state, cap - (state.clock() - unit_started)),
                stage="md", name=f"build_{pair['pair']}_{attempt}", cwd=work,
            )
            if res.get("timed_out"):
                stopped = GuardStop("building the solvated complex ran past its time",
                                    stage="md", detail=res.get("log", ""))
                break
            if not res.get("ok") or not out_json.exists():
                raise HarnessFailure(
                    "building the solvated complex failed",
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
                                  "atom_count_out_of_range": True,
                                  "range": [MD_ATOMS_MIN, MD_ATOMS_MAX]})
            continue

        out_json = work / "run.json"
        res = state.runner.capture(
            [state.python_executable(), str(worker), "--mode", "run",
             "--work", str(work), "--steps", str(steps),
             "--timestep-fs", str(MD_TIMESTEP_FS), "--seed", str(MD_VELOCITY_SEED),
             "--report-interval", str(MD_REPORT_INTERVAL_STEPS),
             "--out", str(out_json)],
            limit_s=inner_tool_limit_s(state, cap - (state.clock() - unit_started)),
            stage="md", name=f"run_{pair['pair']}", cwd=work,
        )
        if res.get("timed_out"):
            add_row(state, "md", {"complex": pair["pair"], "atoms": built["atoms"],
                                  "steps": steps, "incomplete": True,
                                  "why": "the segment ran past the time allowed"})
            stopped = GuardStop("a dynamics segment ran past the time allowed for it",
                                stage="md", detail=res.get("log", ""))
            break
        if not res.get("ok") or not out_json.exists():
            raise HarnessFailure("the dynamics segment failed",
                                 f"exit {res.get('rc')}, see {res.get('log')}")
        done = json.loads(out_json.read_text())
        reporter_src = Path(done["reporter_path"])
        reporter_kept = state.outdir / f"md_reporter_{pair['pair']}_tag-{TAG}.csv"
        if reporter_src.exists():
            shutil.copyfile(str(reporter_src), str(reporter_kept))
            parsed = parse_reporter_file(reporter_kept.read_text())
        else:
            parsed = {"ns_per_day": None, "n_rows": 0,
                      "reason": "the engine wrote no reporter file"}
        wall_rate = ns_per_day_from_wallclock(done["steps"], done["timestep_fs"],
                                              corrected_seconds(state, done["production_s"]))
        disagree = rates_disagree(parsed["ns_per_day"], wall_rate)
        row = {
            "complex": pair["pair"], "atoms": done["atoms"], "steps": done["steps"],
            "timestep_fs": done["timestep_fs"],
            "production_ns": done["steps"] * done["timestep_fs"] * 1e-6,
            "production_wallclock_s": done["production_s"],
            "minimise_s": done.get("minimise_s"),
            "equilibrate_s": done.get("equilibrate_s"),
            "engine_ns_per_day": parsed["ns_per_day"],
            "wallclock_ns_per_day": wall_rate,
            "rates_disagree": disagree,
            "reporter_file": str(reporter_kept),
            "trajectory_file": done.get("trajectory_path"),
            "trajectory_bytes": apparent_bytes(done.get("trajectory_path") or ""),
            "frame_interval_ps": done.get("frame_interval_ps",
                                          MD_FRAME_INTERVAL_PS),
            "report_interval_steps": done.get("report_interval_steps",
                                              MD_REPORT_INTERVAL_STEPS),
            "platform": done.get("platform"), "precision": done.get("precision"),
            "engine_version": done.get("openmm_version"),
            "padding_nm": built.get("padding_nm"), "waters": built.get("waters"),
            "seed": MD_VELOCITY_SEED,
            "tool_log": res.get("log"),
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
        void_reason = LABEL_NOT_A100
        notes.append(LABEL_NOT_A100)
    elif any_size_fault is not None and n == 0:
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
            "complexes": [
                {"complex": r.get("complex"), "atoms": r.get("atoms"),
                 "production_wallclock_s": r.get("production_wallclock_s"),
                 "engine_ns_per_day": r.get("engine_ns_per_day"),
                 "wallclock_ns_per_day": r.get("wallclock_ns_per_day")}
                for r in rows if r.get("atoms")
            ],
            "atom_counts": [r.get("atoms") for r in rows if r.get("atoms")],
            "timestep_fs": MD_TIMESTEP_FS,
            "production_ns": MD_PRODUCTION_NS,
            "engine_precision": MD_PRECISION,
            "engine_platform": MD_PLATFORM,
            "engine_version": next((r.get("engine_version") for r in rows
                                    if r.get("engine_version")), None),
            "frame_interval_ps": MD_FRAME_INTERVAL_PS,
            "velocity_seed": MD_VELOCITY_SEED,
            "decision_value": "median over complexes of the wall-clock figure",
        },
        extra_notes=notes, void_reason=void_reason,
    )
    if stopped is None:
        state.stages_done.append("md")
    return {"n": n, "measured": measured, "stopped": bool(stopped)}


# ===========================================================================
# STAGE: STORAGE (INPUT C4)
# ===========================================================================


def stage_storage(state: RunState) -> dict:
    """Measure what one run of the grid actually writes, and scale it up.

    One run means: the prediction outputs of a single prediction call, the whole
    docking output tree of one pair with every setup file, copied structure,
    swarm directory, rank table and pose, and the trajectory and logs of one
    half-nanosecond segment. Intermediates are kept, because the card's figure
    is about what sits on disk during a grid.
    """
    started = state.clock()
    guard_before_stage(state, "storage", state.unit_estimate("storage"))
    artifacts = []

    af2_dirs = [d for p in state.pairs for d in p.get("af2_out_dirs", [])]
    if af2_dirs:
        b = apparent_bytes(af2_dirs[0])
        artifacts.append({"artifact": "prediction outputs of one run",
                          "path": af2_dirs[0], "bytes": b, "intermediate": False})
    docking_dirs = [str(state.workdir / f"aux_{p['pair']}") for p in state.pairs
                    if Path(state.workdir / f"aux_{p['pair']}").exists()]
    if docking_dirs:
        b = apparent_bytes(docking_dirs[0])
        artifacts.append({"artifact": "whole docking output tree of one pair",
                          "path": docking_dirs[0], "bytes": b, "intermediate": True})
    md_pairs = [p for p in state.pairs if p.get("md_work")]
    md_bytes = 0
    md_setup_bytes = 0
    md_breakdown = None
    if md_pairs:
        first = md_pairs[0]
        md_breakdown = md_bytes_breakdown(first["md_work"], first.get("md_logs") or [])
        md_bytes = md_breakdown["md_bytes"]
        md_setup_bytes = md_breakdown["md_setup_bytes"]
        artifacts.append({"artifact": "dynamics trajectory and every log of one "
                                      f"{MD_PRODUCTION_NS} ns segment",
                          "path": first["md_work"], "bytes": md_bytes,
                          "intermediate": True,
                          "frame_interval_ps": MD_FRAME_INTERVAL_PS,
                          "setup_bytes_not_counted": md_setup_bytes})

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
            "md_bytes": md_bytes,
            "md_setup_bytes": md_setup_bytes,
            "md_bytes_breakdown": md_breakdown,
            "md_bytes_per_ns": scaled.get("md_bytes_per_ns"),
            "frame_interval_ps": MD_FRAME_INTERVAL_PS,
            "grid_runs_used_for_the_decision": GRID_RUNS,
        },
        extra_notes=list(state.overhead_labels)
        + ([] if state.gpu_is_a100 else [f"{LABEL_NOT_A100}: C4 is still decided"]),
        void_reason=void_reason,
    )
    state.stages_done.append("storage")
    return {"n": n, "measured": measured}


# ===========================================================================
# STAGE: ENDPOINTS
# Always runs, whatever stopped the run. Writes a record for every input that
# has none, then the environment note, the summary and the validity file.
# ===========================================================================

# Why the anchor's record holds no measured value on a run that ended first.
LABEL_ANCHOR_NOT_REACHED = "anchor stage not reached"


def emit_anchor_void_record(state: RunState, *, start_epoch, end_epoch,
                            why: str = LABEL_ANCHOR_NOT_REACHED) -> Path:
    """Write the anchor's record as void when the run ended before it decided.

    A run that ends in the install stage never reaches the redocking check, and
    launch 1 then left no anchor file at all: a reader could not tell a check
    that was never run from one that was skipped. Every run that ends on broken
    infrastructure or on a stop now leaves this file, with no measured value and
    the reason it has none written beside it.
    """
    pdb_path = state.datadir / f"{PDB_ENTRY}.pdb"
    reason = str(why or LABEL_ANCHOR_NOT_REACHED)
    return write_record(
        state, f"endpoint-anchor_tag-{TAG}.json", kind="anchor",
        cell={"stage": "anchor", "endpoint": "anchor", "tag": TAG},
        inputs=record_inputs(state, state.outdir / f"rows_anchor_tag-{TAG}.jsonl",
                             extra_paths=[pdb_path]),
        metric=("contact overlap with the published complex at 4.5 angstrom, or "
                "interface backbone displacement, with serial and parallel agreement"),
        values={
            "measured": None,
            "published": (f"AAVR-PKD2 bound to the AAV2 spike region adjacent to the "
                          f"icosahedral three-fold axis (PDB {PDB_ENTRY})"),
            "tolerance": {
                "min_contact_overlap": ANCHOR_OVERLAP_MIN,
                "max_interface_backbone_rmsd_a": ANCHOR_IFACE_RMSD_MAX,
                "max_serial_parallel_rmsd_a": ANCHOR_SERIAL_PARALLEL_RMSD_MAX,
                "calls_must_be_identical": True,
            },
            "unit": "fraction of published contacts, and angstrom",
            "independent_code": ANCHOR_INDEPENDENT_CODE,
            "docking_order": DOCKING_ORDER,
            "void_reason": reason,
            "voided_by": reason,
            "null_reasons": {"measured": reason},
        },
        threshold={"min_contact_overlap": ANCHOR_OVERLAP_MIN,
                   "max_interface_backbone_rmsd_a": ANCHOR_IFACE_RMSD_MAX,
                   "max_serial_parallel_rmsd_a": ANCHOR_SERIAL_PARALLEL_RMSD_MAX},
        decision_rule=("PASS when the pose reproduces the published placement "
                       "(contact overlap at least 0.50 or interface backbone RMSD at "
                       "most 5.0 angstrom) AND serial and parallel agree (top-pose "
                       "RMSD at most 2.0 angstrom with identical bind or no-bind "
                       "calls); otherwise FAIL, every input is void and the run stops; "
                       "VOID when the run ended before the check could be made"),
        decision="VOID",
        labels=labels_for_record(state, start_epoch, end_epoch),
        extra_notes=[LABEL_SERIAL_PARALLEL_WHOLE_CHAIN],
    )


def stage_endpoints(state: RunState) -> dict:
    """Close the run: every input gets a record, then the summary is written."""
    started = state.clock()
    anchor_name = f"endpoint-anchor_tag-{TAG}.json"
    if not (state.outdir / anchor_name).exists():
        # The anchor was not compared, so its record says so rather than being
        # absent. The anchor's own decision, when it has one, is never touched.
        emit_anchor_void_record(
            state, start_epoch=started, end_epoch=state.clock(),
            why=(f"{LABEL_ANCHOR_NOT_REACHED}: "
                 + (state.run_valid_voided_by or state.failure_kind
                    or "; ".join(e["reason"] for e in state.stop_events)
                    or "the run ended before the anchor stage")),
        )
    for cid in INPUT_IDS:
        name = f"endpoint-{cid}_tag-{TAG}.json"
        if name in state.records_written or (state.outdir / name).exists():
            continue
        stop_names = "; ".join(e["reason"] for e in state.stop_events) or \
            "the stage that measures it did not run"
        # emit_input_record puts the one right status word against the input:
        # voided by the anchor, voided by a failure, or left unmeasured by a
        # stop. Nothing here overrides it.
        if state.anchor_missed:
            why = f"the anchor missed its tolerance: {state.anchor_missed}"
        elif state.failure_kind:
            why = ("the run ended on broken infrastructure: "
                   f"{state.run_valid_voided_by or state.failure_kind}")
        else:
            why = f"{LABEL_UNMEASURED} ({stop_names})"
        emit_input_record(
            state, cid, None, n=0, rows_arm=None,
            start_epoch=started, end_epoch=state.clock(),
            void_reason=why,
        )
    write_env_note(state)
    write_summary(state)
    write_run_valid(state)
    state.stages_done.append("endpoints")
    return {"records": list(state.records_written)}


def write_env_note(state: RunState) -> Path:
    """List the named, non-secret variables this run read. Never a whole dump."""
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
    lines.append(f"environment_changed_by_fixer={bool(state.environment_changed_by_fixer)}")
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
            "gate": GATE_EXPRESSION,
            "applied_to": "C1 only",
            "gate_pass": None,
            "gate_note": c1_values.get("gate")
            or "not evaluated: C1 holds no valid measurement",
            "fallback_text": GATE_ELSE,
            "fallback_triggered": False,
            "fallback_note": "the fallback is not presented as triggered, because the "
                             "gate was not evaluated",
        }
    else:
        gate_block = {
            "gate": GATE_EXPRESSION,
            "applied_to": "C1 only",
            "gate_pass": bool(gate_pass),
            "gate_note": None,
            "fallback_text": GATE_ELSE,
            "fallback_triggered": not gate_pass,
        }

    spread = getattr(state, "af2_spread", None) or {"per_pair": {}, "high_spread_pairs": []}
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

    obj = {}
    obj["what_this_run_decides"] = WHAT_THIS_RUN_DECIDES
    obj["tag"] = TAG
    obj["run_valid"] = bool(state.run_valid)
    obj["run_valid_voided_by"] = state.run_valid_voided_by
    obj["records"] = records
    obj["inputs_status"] = state.inputs_status
    obj["gate"] = gate_block
    obj["seed_spread"] = spread
    obj["anchor"] = state.anchor
    obj["held_attempts"] = state.held_attempts
    obj["environment"] = {
        "venv_path": state.venv_path,
        "expected_lock_sha256": state.expected_lock_sha256,
        "observed_lock_sha256": state.observed_lock_sha256,
        "environment_changed_by_fixer": bool(state.environment_changed_by_fixer),
        "hold_seconds_forwarded": state.env.get("HOLD_SECONDS") or None,
        "changes_log_sha256": state.changes_log_sha256,
        "note": ("the python environment is an artifact on the attached "
                 "filesystem; this run installs nothing and pins nothing"),
    }
    obj["tests"] = state.tests_record
    obj["stop_events"] = state.stop_events
    obj["stages_done"] = state.stages_done
    obj["notes"] = notes
    obj["no_relaunch_for_spread"] = (
        "A high spread across seeds is labelled, never answered with another launch "
        "on this box; two runs on the same box are two samples of one box, never a "
        "replication."
    )
    obj["timing"] = {
        "t0_utc": utc_of(state.t0),
        "elapsed_s": round(state.elapsed_s(), 3),
        "pre_t0_seconds": state.pre_t0_seconds,
        "remote_timeout_seen_s": state.remote_timeout_s,
        "remote_timeout_forwarded": state.remote_timeout_forwarded,
        "stop_at_s": state.stop_at_s,
        "binding_cap": state.caps["binding"],
        "price_usd_per_hour": state.price_usd_per_hour,
        "budget_left_usd": state.budget_left_usd,
        "estimated_spend_usd": round(state.spend_usd(), 4),
        "estimated_spend_note": (
            "seconds since the run's own start times the hourly price; the "
            "bootstrap seconds are reported beside this and are not added "
            "again, because the start already counts them"
        ),
        "pre_t0_seconds_reported_not_added": state.pre_t0_seconds,
        "setup_seconds_used": round(state.setup_seconds_used, 3),
    }
    obj["files_written"] = sorted(p.name for p in state.outdir.glob("*") if p.is_file())
    return obj


def write_summary(state: RunState) -> Path:
    """Write the summary with its keys in the order they were built, not sorted."""
    path = state.outdir / f"{TAG}_summary.json"
    atomic_write_text(path, json.dumps(summary_object(state), indent=2) + "\n")
    return path


def write_run_valid(state: RunState) -> Path:
    path = state.outdir / "RUN_VALID.json"
    atomic_write_json(path, {
        "run_valid": bool(state.run_valid),
        "voided_by": state.run_valid_voided_by,
        "stopped": state.stopped,
        "stop_events": state.stop_events,
        "inputs_status": state.inputs_status,
        "tag": TAG,
    })
    return path


def write_run_done(state: RunState, exit_code: int) -> Path:
    """The marker a reader opens first: what happened to each of the four inputs."""
    # Exactly one status word per input, from the one table: decided, void by a
    # rule, left unmeasured by a stop, voided because the anchor missed, or
    # voided because something broke. A reader needs no other file to tell
    # which of those happened.
    per_input = {}
    for cid, status in state.inputs_status.items():
        entry = {"status": status.get("status", "unmeasured_by_stop:unknown"),
                 "decision": status.get("decision"),
                 "reason": status.get("reason")}
        if status.get("voided_by"):
            entry["voided_by"] = status["voided_by"]
        per_input[cid] = entry
    path = state.outdir / "RUN_DONE"
    atomic_write_text(path, json.dumps({
        "exit_code": exit_code,
        "run_valid": bool(state.run_valid),
        "voided_by": state.run_valid_voided_by,
        "stopped_by": [e["reason"] for e in state.stop_events],
        # Which stage broke, in one word, so the on-box script can tell a
        # failure that may be held open for a fixer from one that may not.
        "failure_kind": state.failure_kind,
        "held_attempts": state.held_attempts,
        "inputs": per_input,
        "notes": ([LABEL_INCOMPLETE] if state.stopped else []),
        "tag": TAG,
        "finished_utc": state.now(),
    }, indent=2) + "\n")
    return path


# ===========================================================================
# CLOSING A RUN THE LAUNCHER'S OWN TIMER ENDED
#
# The records already on disk are the run's results. This rebuilds what is
# known from those files, writes only what is missing, and never touches a
# record that already holds a decision.
# ===========================================================================


def record_status_from_disk(rec) -> dict:
    """What one record on disk says about its input: decided, void by rule, or not done."""
    if not isinstance(rec, dict):
        return {"state": "unmeasured", "decision": None,
                "reason": "no record was written for this input"}
    decision = rec.get("decision")
    values = rec.get("values") or {}
    reason = str(values.get("void_reason") or values.get("voided_by") or "")
    notes = " ".join(str(n) for n in (rec.get("notes_list") or []))
    if decision in ("PASS", "FAIL"):
        return {"state": "decided", "decision": decision, "reason": None}
    if decision == "VOID":
        if LABEL_UNMEASURED in reason or LABEL_UNMEASURED in notes:
            return {"state": "unmeasured", "decision": "VOID",
                    "reason": reason or LABEL_UNMEASURED}
        if values.get("marginal") or reason:
            return {"state": "void_by_rule", "decision": "VOID",
                    "reason": reason or "within 10 percent of a band edge"}
        return {"state": "unmeasured", "decision": "VOID",
                "reason": "the record names no rule that voided it"}
    return {"state": "unmeasured", "decision": decision,
            "reason": "the record carries no decision"}


def finalize_from_disk(state: RunState, outer_rc=None) -> int:
    """Rebuild the run's standing from the files, then close it. Returns the exit code.

    An input that was decided before the timer fired keeps its decision and its
    file, byte for byte. An input with no record, or with a record that says it
    was never measured, is void and says a stop left it that way. Nothing here
    measures anything.
    """
    state.record_stop("outer_timeout", "outer",
                      f"the launcher's own timeout returned {outer_rc}")
    state.notes.append("closed from the records on disk after the launcher's own timer")

    # What the validity file and the records already say.
    validity_path = state.outdir / "RUN_VALID.json"
    run_valid = True
    voided_by = None
    if validity_path.exists():
        try:
            doc = json.loads(validity_path.read_text())
            if doc.get("run_valid") is False:
                run_valid = False
                voided_by = doc.get("voided_by") or "the validity file says the run is invalid"
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
            state.anchor = {"decision_from_disk": rec.get("decision"),
                            "values": rec.get("values")}

    state.run_valid = run_valid
    state.run_valid_voided_by = voided_by
    state.records_written = [p.name for p in state.outdir.glob("endpoint-*.json")]

    for cid in INPUT_IDS:
        status = record_status_from_disk(existing.get(f"endpoint-{cid}"))
        if status["state"] == "decided":
            state.set_decided(cid, status["decision"], None)
        elif status["state"] == "void_by_rule":
            state.set_decided(cid, "VOID", status["reason"])
        else:
            state.set_unmeasured(cid, "outer_timeout")

    # Only the records that are missing are written; nothing already decided is
    # rewritten, so a finished result is byte-identical afterwards.
    if not (state.outdir / f"endpoint-anchor_tag-{TAG}.json").exists():
        emit_anchor_void_record(
            state, start_epoch=state.t0, end_epoch=state.clock(),
            why=(f"{LABEL_ANCHOR_NOT_REACHED}: the launcher's own timer ended the "
                 "run before the anchor was compared"),
        )
    for cid in INPUT_IDS:
        path = state.outdir / f"endpoint-{cid}_tag-{TAG}.json"
        if path.exists():
            continue
        emit_input_record(
            state, cid, None, n=0, rows_arm=None,
            start_epoch=state.t0, end_epoch=state.clock(),
            void_reason=f"{LABEL_UNMEASURED} (the launcher's own timer ended the run)",
            stop_kind="outer_timeout",
        )
    write_env_note(state)
    write_summary(state)
    write_run_valid(state)

    if str(anchor_decision_on_disk) == "FAIL":
        return EXIT_ANCHOR
    if not state.run_valid:
        return EXIT_INFRA
    if state.unmeasured_inputs():
        return EXIT_GUARD
    return EXIT_OK


# ===========================================================================
# THE STAGE FLOW
# The order is fixed and every stage is a gate for the next. The flow takes its
# stages by injection, so the order is one list a reader can check.
# ===========================================================================


DEFAULT_STAGES = [
    ("setup", stage_setup),
    ("tests", stage_tests),
    ("downloads", stage_downloads),
    ("controls", stage_controls),
    ("anchor", stage_anchor),
    ("aux", stage_aux),
    ("af2", stage_af2),
    ("md", stage_md),
    ("storage", stage_storage),
]


def run_stages(state: RunState, stages=None, endpoints=None, outer_rc=None) -> int:
    """Run the stages in order and return the exit code the box should report.

    Which failure happened decides the code, and the three kinds never overlap.
    Broken infrastructure or a broken harness is 2 and makes the run invalid. A
    missed anchor is 4 and makes the run invalid. A guard, a stage ceiling or a
    timeout is 3 and leaves validity exactly as it was: finished inputs keep
    their decisions and the work the stop cut off is void, not holding. A value
    that is void by rule alone, with no stop anywhere, still ends at 0.
    """
    stages = stages if stages is not None else DEFAULT_STAGES
    endpoints = endpoints or stage_endpoints
    failure = None
    gated_on_anchor = {"aux", "af2", "md", "storage"}

    if outer_rc is not None:
        handled = handle_outer_rc(state, outer_rc)
        if handled == EXIT_INFRA:
            failure = EXIT_INFRA
            state.void_run(
                f"the run was killed with code {outer_rc} well before the deadline")
        elif handled == EXIT_GUARD:
            state.record_stop("outer_timeout", "outer",
                              f"the launcher's own timeout returned {outer_rc}")
            failure = "outer"

    if failure is None:
        for name, fn in stages:
            if name in gated_on_anchor and "anchor" not in state.stages_done:
                state.record_stop(
                    "anchor_not_decided", name,
                    "the anchor did not finish, so this stage did not start")
                continue
            try:
                fn(state)
            except GuardStop as stop:
                state.record_stop("guard", stop.stage or name, stop.reason)
                continue
            except AnchorMiss as miss:
                state.anchor_missed = miss.reason
                failure = EXIT_ANCHOR
                break
            except HarnessFailure as exc:
                state.void_run(f"{exc.reason}: {exc.detail}" if exc.detail else exc.reason)
                state.failure_kind = exc.kind
                failure = EXIT_INFRA
                break

    try:
        endpoints(state)
    except Exception as exc:                    # the closing stage must not be skipped
        state.notes.append(f"the closing stage itself failed: {exc}")
        if failure is None:
            failure = EXIT_INFRA
            state.void_run(f"the closing stage failed: {exc}")

    # The exit code follows one table. Broken infrastructure is 2 and a missed
    # anchor is 4, whatever else happened. A stop is 3 only when it actually
    # left an input unmeasured: a stop that cost nothing measurable, because
    # every input was already decided, ends at 0 with the stop written down.
    if failure in (EXIT_INFRA, EXIT_ANCHOR):
        return failure
    if state.unmeasured_inputs():
        return EXIT_GUARD
    return EXIT_OK


def handle_outer_rc(state: RunState, rc: int) -> int:
    """Route the exit code of the launcher's own timeout around this program.

    A plain timeout is a guard stop. A kill is only a guard stop when it lands
    at the deadline; a kill that arrives much earlier is a failure, because
    something other than the timer ended the run.
    """
    if rc == 124:
        return EXIT_GUARD
    if rc == 137:
        deadline_since_t0 = state.stop_at_s - OUTER_KILL_SLACK_S
        return EXIT_GUARD if state.elapsed_s() >= deadline_since_t0 - 5 else EXIT_INFRA
    if rc not in (0, None):
        return EXIT_INFRA
    return EXIT_OK


# ===========================================================================
# ENTRY POINT FOR A REAL RUN
# ===========================================================================


def do_run(argv) -> int:
    base = Path(argv.base or os.environ.get("M4_BASE") or ".").resolve()
    outdir = Path(argv.outdir) if argv.outdir else base / f"results_{TAG}" / "out"
    workdir = Path(argv.workdir) if argv.workdir else base / f"work_{TAG}"
    datadir = Path(argv.datadir) if argv.datadir else base / "data"
    datadir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(base / "frozen"))
    try:
        import provenance
    except ImportError as exc:
        print(f"[m4] FATAL: the record writer frozen/provenance.py is missing: {exc}",
              file=sys.stderr)
        return EXIT_INFRA

    state = RunState(outdir, workdir, datadir, provenance=provenance, base=base)
    state.runner = ToolRunner(state)
    if argv.finalize:
        # The launcher's own timeout ended the measuring run. Nothing is
        # measured here: what the records on disk already decided stands, and
        # every input without a record is written as unmeasured, not holding.
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
    parser.add_argument("--base", default=None, help="the payload directory")
    parser.add_argument("--outdir", default=None)
    parser.add_argument("--workdir", default=None)
    parser.add_argument("--datadir", default=None)
    parser.add_argument("--outer-rc", type=int, default=None,
                        help="exit code of the launcher's own timeout, if it fired")
    parser.add_argument("--finalize", action="store_true",
                        help="write the closing records after the launcher's own "
                             "timeout ended the measuring run")
    args = parser.parse_args(argv)
    if args.run or args.finalize:
        return do_run(args)
    parser.print_help()
    return EXIT_INFRA


if __name__ == "__main__":
    sys.exit(main())
