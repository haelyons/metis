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

  python3 run_m4.py --selftest     # no graphics processor, no network, standard library only
  python3 run_m4.py --run          # the real run; only on the rented box, through onbox_m4.sh

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
# recomputed here; the selftest checks them against the band arithmetic.
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
    "install": 1800,
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
}

DEFAULT_REMOTE_TIMEOUT_S = 7200
DEFAULT_BUDGET_LEFT_USD = 5.0
DEFAULT_PRICE_USD_PER_HOUR = 1.99
BOOTSTRAP_ASSUMED_S = 300

# The gap between the inner tool kill and the outer kill, so the inner fires first.
OUTER_KILL_SLACK_S = 600
INNER_KILL_SLACK_S = 700

# ---------------------------------------------------------------------------
# Fixed label and note strings. These are compared by the selftest, so they live
# in one place.
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
    "M4_APT_SECONDS",
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

REQUIRED_LABEL_KEYS = {
    kind: {"machine": MACHINE_KEYS, "engine": ENGINE_KEYS} for kind in MEASURED_KINDS
}
REQUIRED_LABEL_KEYS.update(
    {kind: {"machine": MACHINE_KEYS, "engine": ()} for kind in CONTROL_KINDS}
)

# The nine labels the directive names, each by a word that must appear in the
# name of at least one key the record kinds carry between them.
NINE_LABEL_WORDS = (
    "instance",   # instance type
    "gpu",        # graphics processor name
    "driver",     # its driver
    "cuda",       # the driver's CUDA version, and the JAX CUDA plugin's version
    "version",    # engine versions
    "flags",      # build flags; "tags" also satisfies this label
    "start",      # start wall-clock, in UTC
    "end",        # end wall-clock, in UTC
    "price",      # price per hour
)
NINE_LABEL_ALTERNATIVES = {"flags": ("flags", "tags")}


def label_keys_cover_nine(required=None) -> list:
    """Which of the nine labels no key name covers. Empty means all are covered."""
    required = required or REQUIRED_LABEL_KEYS
    names = set()
    for spec in required.values():
        for group in spec.values():
            names.update(group)
    missing = []
    for word in NINE_LABEL_WORDS:
        words = NINE_LABEL_ALTERNATIVES.get(word, (word,))
        if not any(any(w in name for w in words) for name in names):
            missing.append(word)
    return missing


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

# Packages installed with pip, every one pinned to an exact version. The smoke
# check on the box decides whether the forms chosen here really carry what is
# needed; nothing is substituted if one fails, and a failure is exit 2.
#
# WHICH FORM WAS CHOSEN FOR THE DYNAMICS ENGINE, AND WHY IT IS STATED HERE.
# The engine's plain wheel does not always carry the graphics-processor
# platform the run needs. The form chosen here is THE SIBLING PACKAGE: two
# pinned entries, the plain engine release "openmm==8.1.1" and the separate
# package "openmm-cuda==8.1.1.12" that carries the CUDA platform.
# SIBLING REQUIRES ENGINE VERSION: 8.1.1
# The sibling's own version number reads as that engine release, so the two are
# pinned as one pair. The earlier pairing with engine release 8.2.0 was
# withdrawn: the installer refuses that sibling beside 8.2.0.
# A bracketed extra, written "openmm[cuda12]==8.1.1", is not used and is refused
# by the check below, because the engine release declares no extras.
# This pairing, and the one bracketed extra in the list below (the graphics
# plugin's "with_cuda", the project's own way of bringing the CUDA runtime
# libraries from the package index), are INFERENCES MADE BY THE REVIEW BOARD,
# not verified facts. They are drawn from these records, which this program
# never opens: the board's report "gate_report_build13.md", the installer
# output "pip_pins_resolve_build11.txt", and launch 1's own install log
# "install_pip_install.log" under launch1/results_m4/out/tool_logs/.
# Three checks, none of them this comment, decide whether the form works. The
# operator resolves these exact requirements together with the installer in a
# clean Python 3.10 environment, once before this program is edited and once
# before the next launch (the test of record, directive item 66). The smoke
# check then asks the installed engine for its CUDA platform on the box. If the
# platform is missing, the smoke check fails and the run ends as broken
# infrastructure before any measurement. Nothing falls back.
#
# The prediction stack takes the form whose published metadata carries what the
# smoke check imports: "colabfold" supplies the command line and "alphafold-
# colabfold" supplies the alphafold module it imports, with the JAX build pinned
# to the version that release is built against.
PIP_PINS = [
    "jax==0.4.35",
    "jaxlib==0.4.35",
    "jax-cuda12-plugin[with_cuda]==0.4.35",
    "jax-cuda12-pjrt==0.4.35",
    "colabfold==1.5.5",
    "alphafold-colabfold==2.3.6",
    "openmm==8.1.1",
    "openmm-cuda==8.1.1.12",
    "lightdock==0.9.4",
]

# The smallest pip that can report what it downloaded. An older one gets one
# recorded bootstrap, and no other upgrade of pip happens anywhere.
PIP_REPORT_MIN = (22, 2)
PIP_BOOTSTRAP_VERSION = "24.0"


def parse_pin(spec: str) -> dict:
    """Read one pinned requirement: its name, any extras, and its exact version."""
    text = str(spec).strip()
    m = re.match(r"^([A-Za-z0-9._-]+)\s*(?:\[([^\]]*)\])?\s*==\s*([^\s;]+)$", text)
    if not m:
        raise ParseError(f"requirement {spec!r} is not pinned as name==version")
    extras = [e.strip() for e in (m.group(2) or "").split(",") if e.strip()]
    return {"name": m.group(1), "extras": extras, "version": m.group(3)}


def pip_pins_problems(pins: list) -> list:
    """What is wrong with a list of pinned requirements, in plain words.

    Three things are checked: every requirement names an exact version, the
    dynamics engine and a sibling package whose name begins "openmm-cuda" are
    pinned together as a pair (neither alone), and the engine itself carries no
    bracketed extra, because its pinned release declares none.
    """
    problems = []
    parsed = []
    for spec in pins:
        try:
            parsed.append(parse_pin(spec))
        except ParseError as exc:
            problems.append(str(exc))
    names = {p["name"].lower().replace("_", "-") for p in parsed}
    openmm = [p for p in parsed if p["name"].lower() == "openmm"]
    sibling = [n for n in names if n.startswith("openmm-cuda")]
    if openmm and openmm[0]["extras"]:
        problems.append(
            "the dynamics engine is pinned with a bracketed extra "
            "(%s), which its pinned release does not declare"
            % ",".join(openmm[0]["extras"])
        )
    if openmm and not sibling:
        problems.append(
            "the dynamics engine is pinned without a form that carries the "
            "graphics-processor platform: no openmm-cuda sibling"
        )
    if sibling and not openmm:
        problems.append(
            "the openmm-cuda sibling is pinned without the plain dynamics "
            "engine beside it, and the two install only as a pair"
        )
    return problems


def parse_pip_version(text: str):
    """Read `pip --version`: the version as numbers, or None if unreadable."""
    m = re.search(r"\bpip\s+([0-9]+)\.([0-9]+)(?:\.([0-9]+))?", str(text or ""))
    if not m:
        return None
    return tuple(int(g) for g in m.groups() if g is not None)


def pip_needs_bootstrap(version_text: str) -> bool:
    """True when the environment's own pip is too old to report its downloads."""
    version = parse_pip_version(version_text)
    if version is None:
        raise HarnessFailure(
            "the python package installer did not report a readable version",
            f"got {version_text!r}",
        )
    return version[:2] < PIP_REPORT_MIN

# Packages installed with the system package manager, declared here and in
# onbox_m4.sh. The shell installs them; this program records their versions.
# The last two are the C compiler and the python headers, needed because the
# docking code ships no ready-built package for this python and is compiled from
# its source archive by the package installer on the box.
APT_PACKAGES = ["python3-venv", "aria2", "curl", "build-essential", "python3-dev"]

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
        # A short name for the marker, so a reader can tell an install failure
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
# the graphics processor or the clock, so the selftest can plant inputs.
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


def parse_pip_report(text: str) -> list:
    """Read `pip install --report` output: one entry per installed wheel.

    Each entry keeps the address it came from and the archive hash pip recorded,
    so the download is auditable without trusting the index.
    """
    try:
        doc = json.loads(text)
    except Exception as exc:
        raise ParseError(f"pip report is not JSON: {exc}")
    if not isinstance(doc, dict) or "install" not in doc:
        raise ParseError("pip report has no 'install' list")
    out = []
    for item in doc["install"]:
        info = item.get("download_info") or {}
        archive = info.get("archive_info") or {}
        digest = archive.get("hash") or ""
        if not digest and isinstance(archive.get("hashes"), dict):
            sha = archive["hashes"].get("sha256")
            digest = f"sha256={sha}" if sha else ""
        meta = item.get("metadata") or {}
        out.append(
            {
                "name": meta.get("name"),
                "version": meta.get("version"),
                "url": info.get("url"),
                "archive_hash": digest or None,
            }
        )
    if not out:
        raise ParseError("pip report installed nothing")
    return out


def parse_apt_cache_show(text: str) -> dict:
    """Read `apt-cache show <pkg>`: the version and the archive's SHA256."""
    version = None
    sha = None
    for line in text.splitlines():
        if version is None and line.startswith("Version:"):
            version = line.split(":", 1)[1].strip()
        if sha is None and line.startswith("SHA256:"):
            sha = line.split(":", 1)[1].strip()
    return {"version": version, "sha256": sha}


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


def parse_rank_table(text: str) -> list:
    """Read a docking tool's own ranked list of poses.

    The table must name its ranking: either a rank column or a score column. A
    table without one is refused, because the first line of a file is not a
    ranking and must never stand in for one.
    """
    rows = []
    header = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if header is None:
            lowered = [p.lower() for p in parts]
            has_rank = any(p == "rank" for p in lowered)
            has_score = any(p in ("scoring", "score", "energy") for p in lowered)
            if not (has_rank or has_score):
                raise ParseError(
                    "docking rank table has neither a rank nor a score column"
                )
            header = parts
            continue
        if len(parts) != len(header):
            continue
        rows.append(dict(zip(header, parts)))
    if header is None:
        raise ParseError("docking rank table has no header line")
    if not rows:
        raise ParseError("docking rank table has a header but no rows")
    return rows


def top_ranked_row(rows: list) -> dict:
    """The tool's own first-ranked pose: lowest rank, else best score."""
    if not rows:
        raise ParseError("no rows in the docking rank table")
    keys = list(rows[0].keys())
    rank_key = next((k for k in keys if k.lower() == "rank"), None)
    if rank_key is not None:
        try:
            return min(rows, key=lambda r: float(r[rank_key]))
        except (TypeError, ValueError):
            raise ParseError("rank column is not numeric")
    score_key = next(
        (k for k in keys if k.lower() in ("scoring", "score", "energy")), None
    )
    if score_key is None:
        raise ParseError("docking rank table has neither a rank nor a score column")
    try:
        return max(rows, key=lambda r: float(r[score_key]))
    except (TypeError, ValueError):
        raise ParseError("score column is not numeric")


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
    """Everything the stages share, injected so the selftest can fake it."""

    def __init__(self, outdir, workdir, datadir, clock=None, now=None,
                 env=None, runner=None, provenance=None):
        self.outdir = Path(outdir)
        self.workdir = Path(workdir)
        self.datadir = Path(datadir)
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
        self.install_seconds_used = _env_float(self.env, "M4_APT_SECONDS", 0.0)
        self.install_total_exhausted = False
        # True only once the pinned install of this run has finished and proved
        # itself. Until then no version is read from an installed package,
        # because the box image carries packages this run did not install.
        self.install_completed = False
        self.pip_report_path = None
        self.pip_report_sha256 = None
        self.apt_hash_path = None
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

# The packages whose versions the records carry: the name the installer knows
# them by, and the key used here. Every version comes from this run's own
# install; see read_package_versions.
PACKAGE_VERSION_NAMES = (
    ("jax", "jax"),
    ("jaxlib", "jaxlib"),
    ("jax-cuda12-plugin", "jax_cuda12_plugin"),
    ("openmm", "openmm"),
    ("lightdock", "lightdock"),
    ("colabfold", "colabfold"),
)

# Why a version label is null on a run whose install never finished.
LABEL_NOT_INSTALLED = "not installed: the install stage failed"


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
    # A version label is null whenever this run's own install did not supply it,
    # and the reason says which of the two cases it is: the install never
    # finished, or it finished and that package still named no version.
    installed_here = bool(versions.get("versions_from_this_run"))

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
            "the pip download report named no wheel for the JAX packages"
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
        "pinned_requirements": list(PIP_PINS),
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
    """The versions this run installed, from this run's own install and nothing else.

    Two sources are allowed, both of this run: the report the package installer
    wrote while installing, and the metadata of the packages the virtual
    environment holds once that install has finished and started once. Nothing
    is read before then, and no constant stands in as a default, because the box
    image arrives with packages of its own: launch 1 wrote the image's prediction
    library version into records of a run that installed nothing. A version
    neither source gives is absent here, and the caller writes it as null with
    the reason beside it.
    """
    out = {}
    from_report = {}
    report_path = getattr(state, "pip_report_path", None)
    if report_path and Path(report_path).exists():
        try:
            entries = parse_pip_report(Path(report_path).read_text())
        except (OSError, ParseError):
            entries = []
        for entry in entries:
            name = str(entry.get("name") or "").strip().lower().replace("_", "-")
            if name and entry.get("version"):
                from_report[name] = entry["version"]
    for name, key in PACKAGE_VERSION_NAMES:
        if from_report.get(name):
            out[key] = from_report[name]
    installed = bool(getattr(state, "install_completed", False))
    if installed and any(key not in out for _n, key in PACKAGE_VERSION_NAMES):
        out.update(installed_package_versions(state, skip=set(out)))
    out["versions_from_this_run"] = bool(installed or from_report)
    out["version_sources"] = {
        "pip_report": sorted(from_report),
        "installed_metadata": installed,
    }
    out["params_sha256"] = getattr(state, "params_sha256", None)
    out["wheel_build_tags"] = getattr(state, "wheel_build_tags", None)
    return out


def installed_package_versions(state: RunState, skip=()) -> dict:
    """Ask the packages the virtual environment holds for their own versions."""
    code = (
        "import json\n"
        "out={}\n"
        "from importlib.metadata import version, PackageNotFoundError\n"
        "for name,key in (('jax','jax'),('jaxlib','jaxlib'),"
        "('jax-cuda12-plugin','jax_cuda12_plugin'),('openmm','openmm'),"
        "('lightdock','lightdock'),('colabfold','colabfold')):\n"
        "    try: out[key]=version(name)\n"
        "    except Exception: out[key]=None\n"
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

    Every record cites the raw rows it rests on, the record of what pip
    downloaded, and the record of the system packages. Records about the pairs
    also cite the pair evidence file.
    """
    prov = state.provenance
    inputs = []
    if rows_file:
        p = Path(rows_file)
        n = sum(1 for _ in open(p)) if p.exists() else None
        inputs.append(prov.describe_input(p, n_items=n))
    if state.pip_report_path:
        inputs.append(prov.describe_input(state.pip_report_path))
        inputs.append({"path": str(state.pip_report_path),
                       "sha256_full": state.pip_report_sha256,
                       "what": "pip download report, full sha256"})
    if state.apt_hash_path:
        inputs.append(prov.describe_input(state.apt_hash_path))
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

    Kept behind one object so the selftest can inject a fake that never starts a
    real program.
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


def install_call_limit_s(state: RunState, own_limit_s: float, allowance_s: float) -> float:
    """How long one install step may take, inside the running install total.

    Installing is one budget, not a budget per command: every package manager
    call, download, unpacking step and check draws on the same 1,800 seconds.
    """
    left_in_total = STAGE_CEILING_S["install"] - state.install_seconds_used
    return min(float(own_limit_s), left_in_total, float(allowance_s))


def spend_install_seconds(state: RunState, seconds: float) -> None:
    state.install_seconds_used += max(0.0, float(seconds))
    if state.install_seconds_used >= STAGE_CEILING_S["install"]:
        state.install_total_exhausted = True


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
# STAGE: INSTALL, DOWNLOAD, UNPACK, SMOKE CHECK
# Everything that must work before a single number is measured. Any failure
# here is broken infrastructure: exit 2, never a substitution.
# ===========================================================================


def stage_install(state: RunState) -> dict:
    """Install the pinned tools, fetch the declared files, and prove they work.

    One budget covers the whole stage. Every step draws on it, and running it
    out ends the stage as broken infrastructure, not as a guard stop, because a
    half-installed box cannot measure anything.
    """
    started = state.clock()
    allowance = guard_before_stage(state, "install", UNIT_FLOOR_S["endpoints"])
    runner = state.runner
    log = {"steps": [], "downloads": [], "started_utc": utc_of(started)}

    def step(cmd, own_limit_s, name, **kw):
        limit = install_call_limit_s(state, own_limit_s, allowance)
        if limit <= 0 or state.install_total_exhausted:
            raise HarnessFailure(
                "the install budget of 1,800 seconds ran out",
                f"used {state.install_seconds_used:.1f}s before step {name}",
            )
        res = runner.capture(cmd, limit_s=limit, stage="install", name=name, **kw)
        spend_install_seconds(state, res.get("seconds", 0.0))
        log["steps"].append(
            {"name": name, "cmd": res.get("cmd"), "rc": res.get("rc"),
             "seconds": round(res.get("seconds", 0.0), 3),
             "timed_out": res.get("timed_out"), "log": res.get("log")}
        )
        if state.install_total_exhausted and not res.get("ok"):
            raise HarnessFailure(
                "the install budget of 1,800 seconds ran out",
                f"step {name} ended at {state.install_seconds_used:.1f}s",
            )
        return res

    # -- system packages: versions and archive hashes, recorded, not installed here
    apt_entries = []
    for pkg in APT_PACKAGES:
        res = step(["apt-cache", "show", pkg], 60, f"apt_cache_show_{pkg}")
        info = parse_apt_cache_show(res.get("stdout", "")) if res.get("ok") else {}
        apt_entries.append({"package": pkg, "version": info.get("version"),
                            "sha256": info.get("sha256")})
    apt_path = state.outdir / f"apt_packages_tag-{TAG}.json"
    atomic_write_json(apt_path, {"declared_packages": APT_PACKAGES,
                                 "entries": apt_entries,
                                 "installed_by": "onbox_m4.sh"})
    state.apt_hash_path = apt_path

    # -- the pinned requirements are checked before anything is installed
    pin_problems = pip_pins_problems(PIP_PINS)
    if pin_problems:
        raise HarnessFailure("the pinned requirements are not usable as written",
                             "; ".join(pin_problems))

    # -- the one recorded bootstrap of the installer itself
    #
    # The report of what was downloaded is the only auditable record of every
    # wheel, and an installer older than 22.2 cannot write one. Such an
    # installer is replaced exactly once, from a download that is itself
    # recorded with its address, its hash and its seconds, inside the same
    # install budget. There is no other upgrade of the installer anywhere.
    version_res = step([state.python_executable(), "-m", "pip", "--version"],
                       60, "pip_version")
    if not version_res.get("ok"):
        raise HarnessFailure("the python package installer would not report its version",
                             f"exit {version_res.get('rc')}")
    version_text = (version_res.get("stdout", "") or "").strip()
    log["pip_version_line"] = version_text
    if pip_needs_bootstrap(version_text):
        log["pip_bootstrap"] = pip_bootstrap(state, step, version_text)
    else:
        log["pip_bootstrap"] = {"ran": False, "version_line": version_text,
                                "why": "the installer can already report downloads"}

    # -- python packages, pinned, with a full report of what was downloaded
    report_path = state.outdir / f"pip_report_tag-{TAG}.json"
    res = step(
        [state.python_executable(), "-m", "pip", "install", "--disable-pip-version-check",
         "--no-input", "-q", "--report", str(report_path)] + PIP_PINS,
        1200, "pip_install",
    )
    if not res.get("ok"):
        raise HarnessFailure(
            "installing the pinned python packages failed",
            f"exit {res.get('rc')}, see {res.get('log')}",
        )
    if not report_path.exists():
        raise HarnessFailure("pip wrote no download report", str(report_path))
    state.pip_report_path = report_path
    state.pip_report_sha256 = sha256_file(report_path)
    try:
        entries = parse_pip_report(report_path.read_text())
    except ParseError as exc:
        raise HarnessFailure("the pip download report could not be read", str(exc))
    log["pip_packages"] = entries
    tags = [
        e["url"].rsplit("/", 1)[-1]
        for e in entries
        if e.get("url") and "jax" in (e.get("name") or "").lower()
    ]
    state.wheel_build_tags = ",".join(tags) if tags else None

    # -- the published structure
    pdb_path = state.datadir / f"{PDB_ENTRY}.pdb"
    if not pdb_path.exists():
        res = step(["curl", "-fsSL", "--retry", "3", "-o", str(pdb_path), PDB_URL],
                   300, "download_pdb")
        if not res.get("ok") or not pdb_path.exists():
            raise HarnessFailure(
                f"downloading the published structure {PDB_ENTRY} failed",
                f"exit {res.get('rc')} from {PDB_URL}",
            )
    log["downloads"].append({"what": f"PDB entry {PDB_ENTRY}", "url": PDB_URL,
                             "path": str(pdb_path), "sha256": sha256_file(pdb_path),
                             "bytes": pdb_path.stat().st_size})

    # -- the prediction parameters, fetched and unpacked before anything is timed
    params_dir = state.datadir / "params"
    params_dir.mkdir(parents=True, exist_ok=True)
    archive = state.datadir / "alphafold_params.tar"
    if not archive.exists():
        res = step(["curl", "-fsSL", "--retry", "3", "-o", str(archive), AF_PARAMS_URL],
                   900, "download_params")
        if not res.get("ok") or not archive.exists():
            raise HarnessFailure(
                "downloading the AlphaFold parameter archive failed",
                f"exit {res.get('rc')} from {AF_PARAMS_URL}",
            )
    state.params_sha256 = sha256_file(archive)
    log["downloads"].append({"what": "AlphaFold parameter archive",
                             "url": AF_PARAMS_URL, "path": str(archive),
                             "sha256": state.params_sha256,
                             "bytes": archive.stat().st_size})
    res = step(["tar", "-xf", str(archive), "-C", str(params_dir)], 600, "extract_params")
    if not res.get("ok"):
        raise HarnessFailure("unpacking the parameter archive failed",
                             f"exit {res.get('rc')}")
    missing = missing_multimer_params(params_dir)
    if missing:
        raise HarnessFailure(
            "the unpacked parameters do not hold a file for every model",
            "missing: " + ", ".join(missing),
        )
    log["params_dir"] = str(params_dir)
    log["params_files"] = sorted(p.name for p in params_dir.glob("params_*multimer*.npz"))
    markers = write_parameter_markers(state, params_dir)
    log["params_markers"] = markers
    atomic_write_json(state.outdir / f"params_markers_tag-{TAG}.json", markers)

    # -- the smoke check: the tools must start and see the graphics processor
    smoke = smoke_check(state, step, params_dir)
    log["smoke_check"] = smoke
    if not smoke["ok"]:
        raise HarnessFailure("the smoke check failed", json.dumps(smoke["problems"]))
    # Past this line the pinned packages are installed and have started once, so
    # their own metadata may be read for the version labels, and not before.
    state.install_completed = True

    # -- the stand-in pairs, built and checked before any time is spent on them
    pairs = build_pairs(pdb_path.read_text())
    assert_pairs(pairs)
    state.pairs = pairs
    write_pair_evidence(state, pairs, pdb_path)
    log["pairs"] = [{"pair": p["pair"], "residues": p["total_residues"]} for p in pairs]

    log["install_seconds_used"] = round(state.install_seconds_used, 3)
    log["finished_utc"] = utc_of(state.clock())
    atomic_write_json(state.outdir / f"install_log_tag-{TAG}.json", log)
    state.stages_done.append("install")
    return log


def parse_pip_download_log(text: str):
    """Read the address a download of one wheel came from, out of a verbose log."""
    urls = re.findall(r"(https?://\S+?\.whl)", str(text or ""))
    return urls[-1] if urls else None


def pip_bootstrap(state: RunState, step, version_text: str) -> dict:
    """Fetch one installer wheel, record it in full, and install it from disk.

    The wheel is downloaded with the verbose log kept, hashed here rather than
    trusted from the log, written into this run's download record, and then
    installed from the local file with the index switched off, so nothing else
    can be pulled in behind it.
    """
    target = state.workdir / "pip_bootstrap"
    target.mkdir(parents=True, exist_ok=True)
    started = state.clock()
    res = step(
        [state.python_executable(), "-m", "pip", "download",
         f"pip=={PIP_BOOTSTRAP_VERSION}", "--no-deps", "--no-input", "-v",
         "--dest", str(target)],
        300, "pip_bootstrap_download",
    )
    if not res.get("ok"):
        raise HarnessFailure("the one allowed installer download failed",
                             f"exit {res.get('rc')}, see {res.get('log')}")
    wheels = sorted(target.glob("pip-*.whl"))
    if not wheels:
        raise HarnessFailure("the installer download left no wheel", str(target))
    wheel = wheels[0]
    entry = {
        "ran": True,
        "why": f"the environment reported {version_text!r}, which cannot report "
               "what it downloads",
        "what": f"pip {PIP_BOOTSTRAP_VERSION}, the one allowed installer bootstrap",
        "url": parse_pip_download_log(
            (res.get("stdout") or "") + (res.get("stderr") or "")
            + (Path(res["log"]).read_text()
               if res.get("log") and Path(res["log"]).exists() else "")),
        "path": str(wheel),
        "sha256": sha256_file(wheel),
        "bytes": wheel.stat().st_size,
        "seconds": round(state.clock() - started, 3),
        "verbose_log": res.get("log"),
    }
    install = step(
        [state.python_executable(), "-m", "pip", "install", "--no-input", "-q",
         "--no-index", str(wheel)],
        300, "pip_bootstrap_install",
    )
    if not install.get("ok"):
        raise HarnessFailure("installing the downloaded installer wheel failed",
                             f"exit {install.get('rc')}, see {install.get('log')}")
    entry["seconds"] = round(state.clock() - started, 3)
    entry["installed"] = True
    return entry


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
    try:
        rows = parse_rank_table(table_path.read_text())
        top = top_ranked_row(rows)
    except ParseError as exc:
        raise HarnessFailure("the docking rank table could not be read",
                             f"{exc}; raw table kept at {kept}")
    pose = pose_path_from_row(work, top)
    if pose is None or not Path(pose).exists():
        raise HarnessFailure(
            "the docking rank table names no pose file that exists",
            f"top row {top}; raw table kept at {kept}",
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
                       "restrained_to_the_published_interface": False},
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
        "install_seconds_used": round(state.install_seconds_used, 3),
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
# stages by injection so the selftest can run it with fakes.
# ===========================================================================


DEFAULT_STAGES = [
    ("install", stage_install),
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

    state = RunState(outdir, workdir, datadir, provenance=provenance)
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
    parser.add_argument("--selftest", action="store_true",
                        help="run the standard-library checks and exit")
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
    if args.selftest:
        return selftest()
    if args.run or args.finalize:
        return do_run(args)
    parser.print_help()
    return EXIT_INFRA


# ===========================================================================
# SELFTEST
# Standard library only, no graphics processor, no network, no real tool run.
# Every parser, every arithmetic rule and every exit route is planted here with
# an answer known in advance.
# ===========================================================================


class Checks:
    """A running tally of planted cases and what they returned."""

    def __init__(self):
        self.passed = 0
        self.failed = []

    def ok(self, name: str, condition: bool, detail: str = "") -> bool:
        if condition:
            self.passed += 1
            return True
        self.failed.append(f"{name}{(': ' + detail) if detail else ''}")
        return False

    def eq(self, name: str, got, want, tol=None) -> bool:
        if tol is not None and isinstance(got, (int, float)) and got is not None:
            good = abs(got - want) <= tol
        else:
            good = got == want
        return self.ok(name, good, f"got {got!r}, wanted {want!r}")

    def raises(self, name: str, fn, exc_type) -> bool:
        try:
            fn()
        except exc_type:
            return self.ok(name, True)
        except Exception as exc:
            return self.ok(name, False, f"raised {type(exc).__name__}: {exc}")
        return self.ok(name, False, "nothing was raised")

    @property
    def total(self) -> int:
        return self.passed + len(self.failed)


def _atom(chain, resseq, name, x, y, z, resname="ALA", element=None):
    return {"record": "ATOM", "serial": "1", "name": name, "resname": resname,
            "chain": chain, "resseq": resseq, "icode": "", "x": float(x),
            "y": float(y), "z": float(z),
            "element": element or (name[0] if name else "C")}


def _residue(chain, resseq, x, y, z, resname="ALA"):
    return [_atom(chain, resseq, nm, x + i, y, z, resname)
            for i, nm in enumerate(BACKBONE_ATOMS)]


def planted_complex(receptor_chain="B", shift_receptor=(0.0, 0.0, 0.0),
                    drop_receptor_residues=(), extra_far_residue_shift=None):
    """A small complex with exactly six contacting residue pairs.

    Each capsid residue sits four angstrom from its own receptor residue and
    fifty angstrom from every other pair, so the contact count is known.
    """
    atoms = []
    for i in range(1, 7):
        atoms.extend(_residue("A", i, 0.0, 0.0, 50.0 * i))
    for i in range(1, 7):
        resseq = 100 + i
        if resseq in drop_receptor_residues:
            z = 50.0 * i + 500.0        # moved right out of contact
        else:
            z = 50.0 * i
        atoms.extend(_residue(receptor_chain, resseq,
                              0.0 + shift_receptor[0], 4.0 + shift_receptor[1],
                              z + shift_receptor[2]))
    far = _residue(receptor_chain, 200, 0.0, 300.0, 0.0)
    if extra_far_residue_shift:
        far = [dict(a, x=a["x"] + extra_far_residue_shift) for a in far]
    atoms.extend(far)
    chain_map = {"A": "capsid", receptor_chain: "receptor"}
    return atoms, chain_map


def selftest_parsers(c: Checks) -> None:
    """Every parser, on output that looks real and on output that does not."""
    smi = ("Tue Oct 21 00:00:00 2026\n"
           "+-----------------------------------------------------------------+\n"
           "| NVIDIA-SMI 570.148.08   Driver Version: 570.148.08   CUDA Version: 12.8 |\n")
    h = parse_nvidia_smi_header(smi)
    c.eq("nvidia-smi banner driver version", h["driver_version"], "570.148.08")
    c.eq("nvidia-smi banner CUDA version", h["cuda_version_header"], "12.8")
    bad = parse_nvidia_smi_header("no banner here at all")
    c.eq("nvidia-smi banner without a driver line", bad["driver_version"], None)
    c.eq("nvidia-smi banner without a CUDA line", bad["cuda_version_header"], None)
    q = parse_nvidia_smi_query("NVIDIA A100-SXM4-40GB, 570.148.08\n")
    c.eq("nvidia-smi query GPU name", q["gpu_name"], "NVIDIA A100-SXM4-40GB")
    c.eq("nvidia-smi query driver", q["driver_version"], "570.148.08")
    c.eq("A100 recognised", is_a100("NVIDIA A100-SXM4-40GB"), True)
    c.eq("a different GPU is not an A100", is_a100("NVIDIA L40S"), False)
    c.eq("a missing GPU name is not an A100", is_a100(None), False)

    report = json.dumps({"install": [
        {"download_info": {"url": "https://files.pythonhosted.org/x/jax-0.4.35.whl",
                           "archive_info": {"hash": "sha256=abc123"}},
         "metadata": {"name": "jax", "version": "0.4.35"}},
        {"download_info": {"url": "https://files.pythonhosted.org/y/openmm-8.2.0.whl",
                           "archive_info": {"hashes": {"sha256": "def456"}}},
         "metadata": {"name": "openmm", "version": "8.2.0"}}]})
    entries = parse_pip_report(report)
    c.eq("pip report entry count", len(entries), 2)
    c.eq("pip report address", entries[0]["url"],
         "https://files.pythonhosted.org/x/jax-0.4.35.whl")
    c.eq("pip report archive hash", entries[0]["archive_hash"], "sha256=abc123")
    c.eq("pip report hash from the hashes map", entries[1]["archive_hash"],
         "sha256=def456")
    c.raises("pip report that is not JSON is refused",
             lambda: parse_pip_report("not json at all"), ParseError)
    c.raises("pip report with no install list is refused",
             lambda: parse_pip_report('{"version": "1"}'), ParseError)

    apt = parse_apt_cache_show(
        "Package: python3-venv\nVersion: 3.10.6-1~22.04\nSHA256: 0123abc\n")
    c.eq("apt package version", apt["version"], "3.10.6-1~22.04")
    c.eq("apt package archive hash", apt["sha256"], "0123abc")
    c.eq("apt output without a hash", parse_apt_cache_show("Package: x\n")["sha256"],
         None)

    c.eq("elapsed-seconds reading", parse_etimes("  412 \n"), 412)
    c.eq("elapsed-seconds reading of rubbish", parse_etimes("not-a-number"), None)
    c.eq("elapsed-seconds reading of nothing", parse_etimes(""), None)

    log = ("Query 1/1: pair1 (length 870)\n"
           "alphafold2_multimer_v3_model_1_seed_000 took 412.5s (19 recycles)\n"
           "alphafold2_multimer_v3_model_2_seed_000 took 300.0s (19 recycles)\n"
           "Done\n")
    parsed = parse_colabfold_log(log)
    c.eq("prediction log per-model times", parsed["per_model_s"], [412.5, 300.0])
    c.eq("a clean prediction log shows no download",
         parsed["download_in_timed_call"], False)
    dirty = parse_colabfold_log(log + "Downloading alphafold2_multimer_v3 weights\n")
    c.eq("a prediction log that downloads is flagged",
         dirty["download_in_timed_call"], True)
    c.eq("a prediction log with no timings", parse_colabfold_log("nothing")["per_model_s"],
         [])

    reporter = ('#"Step","Potential Energy (kJ/mole)","Temperature (K)","Speed (ns/day)"\n'
                '5000,-1.2e6,300.1,0\n'
                '10000,-1.2e6,299.8,127.4\n'
                '15000,-1.2e6,300.2,128.96\n')
    r = parse_reporter_file(reporter)
    c.eq("reporter file speed column", r["ns_per_day"], 128.96)
    c.eq("reporter file row count", r["n_rows"], 3)
    no_rate = parse_reporter_file('#"Step","Temperature (K)"\n5000,300.1\n')
    c.eq("reporter file with no speed column", no_rate["ns_per_day"], None)
    c.ok("reporter file with no speed column says why", bool(no_rate["reason"]))
    empty = parse_reporter_file("")
    c.eq("empty reporter file", empty["ns_per_day"], None)
    c.eq("engine rate line", parse_engine_rate_line("Speed (ns/day): 128.96"), 128.96)
    c.eq("engine rate line the other way round",
         parse_engine_rate_line("rate 42.5 ns/day achieved"), 42.5)
    c.eq("engine rate line that is absent",
         parse_engine_rate_line("no speed reported"), None)

    c.eq("speed from steps, timestep and clock",
         round(ns_per_day_from_wallclock(250000, 2.0, 335), 2), 128.96)
    c.eq("speed from a zero clock", ns_per_day_from_wallclock(250000, 2.0, 0), None)
    c.eq("engine and clock speeds that agree",
         rates_disagree(128.96, 128.0), False)
    c.eq("engine and clock speeds that disagree", rates_disagree(129, 100), True)
    c.eq("a missing engine speed cannot disagree", rates_disagree(None, 100), False)

    table = ("Swarm  Conformation  Receptor_ID  Ligand_ID  Scoring\n"
             "0      7             0            0          12.5\n"
             "1      3             0            0          19.75\n")
    rows = parse_rank_table(table)
    c.eq("rank table row count", len(rows), 2)
    top = top_ranked_row(rows)
    c.eq("best-scoring pose is taken", top["Conformation"], "3")
    ranked = parse_rank_table("Rank Swarm Conformation Scoring\n2 0 7 12.5\n1 1 3 19.75\n")
    c.eq("an explicit rank column wins", top_ranked_row(ranked)["Conformation"], "3")
    c.raises("a table with no rank and no score column is refused",
             lambda: parse_rank_table("Swarm Conformation\n0 7\n"), ParseError)
    c.raises("a table with a header but no rows is refused",
             lambda: parse_rank_table("Swarm Conformation Scoring\n"), ParseError)
    c.eq("pose file named by swarm and conformation",
         pose_path_from_row(Path("/w"), {"Swarm": "1", "Conformation": "3"}).name,
         "lightdock_3.pdb")

    af_rows = [
        {"pair": "pair1", "wallclock_s": 1800.0},
        {"pair": "pair2", "wallclock_s": 1800.0},
        {"pair": "pair3", "wallclock_s": 1800.0},
        {"pair": "pair1", "wallclock_s": 9999.0, "incomplete": True},
        {"pair": "pair2", "wallclock_s": 9999.0, "download_in_timed_call": True},
    ]
    s = parse_af2_timing_rows(af_rows)
    c.eq("timing rows counted", s["n"], 3)
    c.eq("1,800 seconds per run is half an hour", s["mean_h"], 0.5)
    c.eq("a cut-short run is not counted", 9999.0 / 3600.0 in s["hours"], False)
    c.eq("timing rows cover three pairs", s["pairs"], ["pair1", "pair2", "pair3"])


def selftest_bytes_and_storage(c: Checks) -> None:
    """Byte counting and the scaling to the planned grid."""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "a.bin").write_bytes(b"x" * 1000)
        (d / "b.bin").write_bytes(b"y" * 24)
        c.eq("files of 1,000 and 24 bytes sum to 1,024", apparent_bytes(d), 1024)
        tree = d / "docking"
        (tree / "swarm_0").mkdir(parents=True)
        (tree / "setup.json").write_bytes(b"z" * 100)
        (tree / "swarm_0" / "lightdock_3.pdb").write_bytes(b"w" * 400)
        (tree / "swarm_0" / "gso_20.out").write_bytes(b"v" * 24)
        c.eq("a docking tree with a nested swarm directory sums every file",
             apparent_bytes(tree), 524)
        c.eq("a path that does not exist holds no bytes",
             apparent_bytes(d / "nope"), 0)

    for per_run, gib216, gib432, want in (
        (BYTES_PER_GIB, 216.0, 432.0, "PASS"),
        (int(0.1 * BYTES_PER_GIB), 21.6, 43.2, "FAIL"),
        (int(4.0 * BYTES_PER_GIB), 864.0, 1728.0, "FAIL"),
        (int(2.9 * BYTES_PER_GIB), 626.4, 1252.8, "VOID"),
        (int(0.35 * BYTES_PER_GIB), 75.6, 151.2, "PASS"),
    ):
        scaled = storage_from_bytes(per_run)
        c.eq(f"storage of {per_run} bytes per run over 216 runs",
             round(scaled["gib_216_runs"], 4), round(gib216, 4), tol=1e-6)
        c.eq(f"storage of {per_run} bytes per run over 432 runs",
             round(scaled["gib_432_runs"], 4), round(gib432, 4), tol=1e-6)
        c.eq(f"storage of {gib216} GiB is {want}",
             decide_band(scaled["gib_216_runs"], CARD["C4"]["band"])["decision"], want)


def selftest_bands(c: Checks) -> None:
    """The four inputs' arithmetic on planted values with known decisions."""
    c1 = CARD["C1"]["band"]
    for value, want, gate_pass in (
        (0.5, "PASS", True), (1.5, "FAIL", False), (0.1, "FAIL", True),
        (1.2, "VOID", False), (0.21, "VOID", True),
        (1.1, "PASS", False), (0.9, "PASS", True),
    ):
        outcome = decide_band(value, c1)
        c.eq(f"prediction hours {value} is {want}", outcome["decision"], want)
        gate = gate_on_c1(value, outcome["decision"], outcome["marginal"])
        c.eq(f"prediction hours {value} gate", gate["gate_pass"], gate_pass)
    c.eq("a marginal 1.2 hours is marked marginal",
         decide_band(1.2, c1)["marginal"], True)
    c.eq("1.1 hours fails the card's gate and keeps the fallback text",
         gate_on_c1(1.1, "PASS", False)["gate_else"], GATE_ELSE)
    c.eq("the gate is not evaluated without a measurement",
         gate_on_c1(None, "VOID", False)["gate_pass"], None)
    c.eq("the gate is not evaluated on a void that is not marginal",
         gate_on_c1(0.5, "VOID", False)["gate_pass"], None)

    c2 = CARD["C2"]["band"]
    c.eq("median of 100, 129 and 500 is 129", statistics.median([100, 129, 500]), 129)
    for value, want in ((129, "PASS"), (40, "FAIL"), (400, "FAIL"),
                        (56, "VOID"), (60, "PASS"), (330, "VOID")):
        c.eq(f"dynamics speed {value} is {want}",
             decide_band(value, c2)["decision"], want)

    c3 = CARD["C3"]["band"]
    c.eq("three pair clocks of 3,600 s give one hour",
         sum([3600.0, 3600.0, 3600.0]) / 3 / 3600.0, 1.0)
    for value, want in ((1.0, "PASS"), (0.2, "FAIL"), (4.0, "FAIL"),
                        (0.3333, "VOID"), (3.2, "VOID"), (0.5, "PASS"), (2.5, "PASS")):
        c.eq(f"auxiliary hours {value} is {want}",
             decide_band(value, c3)["decision"], want)
    c.eq("7,200 s of installing plus 1,800 s of docking counts only the docking",
         1800.0 / 3600.0, 0.5)

    c.eq("a value with no measurement is void",
         decide_band(None, c3)["decision"], "VOID")
    c.eq("a value exactly on an edge is marginal", is_marginal(0.2, c1), True)
    c.eq("a value a long way inside is not marginal", is_marginal(0.6, c1), False)

    c.eq("atom count 150,000 is inside the required range",
         MD_ATOMS_MIN <= 150000 <= MD_ATOMS_MAX, True)
    c.eq("atom count 119,999 is outside the required range",
         MD_ATOMS_MIN <= 119999 <= MD_ATOMS_MAX, False)
    c.eq("atom count 180,001 is outside the required range",
         MD_ATOMS_MIN <= 180001 <= MD_ATOMS_MAX, False)


def selftest_harness_rules(c: Checks) -> None:
    """The sleep check, the spread rule and the empty-run thresholds."""
    for measured, want in ((62.9, True), (63.1, False), (57.1, True), (56.9, False)):
        error = abs(measured - SLEEP_CONTROL_S) / SLEEP_CONTROL_S
        c.eq(f"a 60 s sleep read back as {measured} s passes: {want}",
             error <= SLEEP_CONTROL_TOLERANCE, want)

    good = spread_check({"pair1": [1800.0, 1830.0, 1790.0]})
    c.eq("timings that differ pass the spread check", good["zero_spread_pairs"], [])
    c.eq("timings that differ do not halt", good["halt"], None)
    bad = spread_check({"pair1": [1800.0, 1800.0, 1800.0]})
    c.eq("identical timings are caught", bad["zero_spread_pairs"], ["pair1"])
    c.eq("identical timings halt on the variance source", bad["halt"],
         WRONG_VARIANCE_SOURCE)
    high = spread_check({"pair1": [50.0, 100.0, 200.0]})
    c.ok("a wide spread is flagged, not halted",
         high["halt"] is None and bool(high["high_spread_pairs"]))
    c.eq("relative spread of identical values is zero",
         relative_sd([5.0, 5.0, 5.0]), 0.0)

    c.eq("an empty run of 0.5 s passes", 0.5 < EMPTY_RUN_MAX_S, True)
    c.eq("an empty run of 5 s does not", 5.0 < EMPTY_RUN_MAX_S, False)
    c.eq("an empty run writing 100 KiB passes", 100 * 1024 < EMPTY_RUN_MAX_BYTES, True)
    c.eq("an empty run writing 2 MiB does not",
         2 * 1024 * 1024 < EMPTY_RUN_MAX_BYTES, False)


def selftest_cost_and_time(c: Checks) -> None:
    """The money and clock arithmetic, and the refusal to start work that will not fit."""
    c.eq("3,600 s at 1.99 dollars an hour", round(cost_usd(3600, 1.99), 2), 1.99)
    c.eq("7,200 s at 1.99 dollars an hour", round(cost_usd(7200, 1.99), 2), 3.98)

    caps = stop_at_seconds(1.99, 5.0, 7200)
    c.eq("at 1.99 dollars an hour the money cap is past the clock cap",
         round(caps["dollar_cap_s"], 0), 9045.0)
    c.eq("at 1.99 dollars an hour the clock cap binds", caps["stop_at_s"], 7200.0)
    c.eq("at 1.99 dollars an hour the binding cap is the clock", caps["binding"], "time")
    caps = stop_at_seconds(2.50, 5.0, 7200)
    c.eq("at 2.50 dollars an hour both caps coincide", caps["stop_at_s"], 7200.0)
    caps = stop_at_seconds(3.00, 5.0, 7200)
    c.eq("at 3.00 dollars an hour the money cap stops at 6,000 s",
         caps["stop_at_s"], 6000.0)
    c.eq("at 3.00 dollars an hour the binding cap is the money",
         caps["binding"], "dollars")

    c.eq("the per-stage ceilings and the margin fill the whole cap",
         (STAGE_CEILING_S["install"] + STAGE_CEILING_S["controls"]
          + STAGE_CEILING_S["aux"] + STAGE_CEILING_S["af2"] + STAGE_CEILING_S["md"]
          + STAGE_CEILING_S["endpoints"] + FETCH_MARGIN_S), TOTAL_CEILING_S)
    c.eq("the controls and the anchor share one ceiling",
         STAGE_CEILING_S["controls"], STAGE_CEILING_S["anchor"])
    c.eq("the inner tool limit is at least 100 s inside the outer kill",
         INNER_KILL_SLACK_S - OUTER_KILL_SLACK_S, 100)


def selftest_anchor(c: Checks) -> None:
    """The anchor's geometry and its three non-overlapping outcomes."""
    for overlap, rmsd, want in ((0.50, 9.0, "PASS"), (0.49, 5.0, "PASS"),
                                (0.49, 5.01, "FAIL")):
        v = anchor_decision(overlap, rmsd, 1.0, True)
        c.eq(f"placement overlap {overlap} with interface RMSD {rmsd} is {want}",
             v["decision"], want)
    c.eq("serial and parallel 2.0 angstrom apart with the same call pass",
         anchor_decision(0.9, 1.0, 2.0, True)["decision"], "PASS")
    c.eq("serial and parallel 2.01 angstrom apart fail",
         anchor_decision(0.9, 1.0, 2.01, True)["decision"], "FAIL")
    c.eq("serial and parallel identical but with different calls fail",
         anchor_decision(0.9, 1.0, 0.0, False)["decision"], "FAIL")
    c.raises("the anchor is never decided without a pose",
             lambda: anchor_decision(None, None, 1.0, True), HarnessFailure)

    native, chain_map = planted_complex("B")
    native_roles = map_chain_roles(native, chain_map)
    ref = contact_pairs_by_index(native_roles)
    c.eq("the planted complex has six contacting residue pairs", len(ref), 6)

    half, half_map = planted_complex("B", drop_receptor_residues=(104, 105, 106))
    half_roles = map_chain_roles(half, half_map)
    c.eq("three of six contacts give an overlap of 0.5",
         contact_overlap(ref, contact_pairs_by_index(half_roles)), 0.5)

    for letter in ("B", "C", "A"):
        if letter == "A":
            moved = [dict(a, chain=("Z" if a["chain"] == "A" else "A"))
                     for a in half]
            moved_map = {"Z": "capsid", "A": "receptor"}
        else:
            moved, moved_map = planted_complex(
                letter, drop_receptor_residues=(104, 105, 106))
        roles = map_chain_roles(moved, moved_map)
        c.eq(f"the same pose with receptor chain {letter!r} still gives 0.5",
             contact_overlap(ref, contact_pairs_by_index(roles)), 0.5)

    round_trip = read_pdb_atoms(write_pdb(half))
    rt_roles = map_chain_roles(round_trip, half_map)
    overlap_rt = contact_overlap(ref, contact_pairs_by_index(rt_roles))
    c.eq("writing and reading the pose back does not change its overlap",
         overlap_rt, 0.5)
    c.ok("a pose with real overlap never scores zero", overlap_rt != 0.0)

    shifted, shifted_map = planted_complex("B", shift_receptor=(5.0, 0.0, 0.0))
    shifted_roles = map_chain_roles(shifted, shifted_map)
    c.eq("a 5.0 angstrom shift along x gives an interface RMSD of 5.0",
         round(interface_backbone_rmsd(native_roles, shifted_roles), 4), 5.0)

    far, far_map = planted_complex("B", extra_far_residue_shift=20.0)
    far_roles = map_chain_roles(far, far_map)
    c.eq("moving only non-interface receptor atoms leaves the interface RMSD at zero",
         round(interface_backbone_rmsd(native_roles, far_roles), 4), 0.0)
    c.ok("moving only non-interface receptor atoms still moves the whole chain",
         whole_chain_rmsd(native_roles, far_roles) > 0)
    c.eq("the whole-chain comparison is labelled as such",
         "whole receptor chain" in LABEL_SERIAL_PARALLEL_WHOLE_CHAIN, True)
    c.eq("the anchor names the second docking code as not run",
         ANCHOR_INDEPENDENT_CODE, "not run: single docking code")


def selftest_environment(c: Checks) -> None:
    """Secrets never reach a child, and tools resolve through the installed set."""
    planted = {"HF_TOKEN": "hf_secret", "HUGGING_FACE_HUB_TOKEN": "hf_secret",
               "PATH": "/usr/bin", "INSTANCE_TYPE": "gpu_1x_a100_sxm4"}
    with tempfile.TemporaryDirectory() as d:
        bin_dir = Path(d) / "venv" / "bin"
        bin_dir.mkdir(parents=True)
        stub = bin_dir / "colabfold_batch"
        stub.write_text("#!/bin/sh\nexit 0\n")
        os.chmod(str(stub), 0o755)
        env = child_env(planted, bin_dir)
        c.eq("a download token never reaches a child", "HF_TOKEN" in env, False)
        c.eq("the second download token never reaches a child",
             "HUGGING_FACE_HUB_TOKEN" in env, False)
        c.eq("the parent dictionary is not altered", planted["HF_TOKEN"], "hf_secret")
        c.eq("non-secret variables are passed through",
             env["INSTANCE_TYPE"], "gpu_1x_a100_sxm4")
        c.eq("the installed tools come first on the search path",
             env["PATH"].split(os.pathsep)[0], str(bin_dir))
        c.eq("a planted tool resolves through that path",
             shutil.which("colabfold_batch", path=env["PATH"]), str(stub))
        c.eq("the same tool is not on the bare inherited path",
             shutil.which("colabfold_batch", path="/usr/bin"), None)
    c.eq("no variable that can hold a token is in the environment note",
         [k for k in ENV_RECORD_KEYS if k in SECRET_ENV_KEYS], [])


def selftest_process_groups(c: Checks) -> None:
    """A tool that overruns is killed with its children, and stale entries are not."""
    with tempfile.TemporaryDirectory() as d:
        state = make_state(Path(d))
        runner = ToolRunner(state)
        marker = Path(d) / "child_marker"
        script = (f"sh -c 'sleep 30 > {marker} 2>&1 &' ; sleep 30")
        res = runner.capture(["sh", "-c", script], limit_s=2, stage="selftest",
                             name="overrun")
        c.eq("a tool that runs past its limit is reported as timed out",
             res["timed_out"], True)
        c.eq("a tool that runs past its limit is not reported as succeeding",
             res["ok"], False)
        c.ok("the overrun left a log", Path(res["log"]).exists())
        c.eq("no process group is left registered", len(runner.groups), 0)

        fake_pgid = 999999
        runner.groups[fake_pgid] = {
            "pid": os.getpid(),
            "identity": {"present": True, "comm": "not-this-process",
                         "starttime": "1"},
        }
        c.eq("a stale process-group entry is not signalled",
             runner.kill_group(fake_pgid), False)
        c.ok("the skipped signal is written down", bool(runner.skipped_signals))
        identity = proc_identity(os.getpid())
        c.eq("this process can be identified", identity["present"], True)
        c.eq("this process matches its own identity",
             same_process(os.getpid(), identity), True)
        c.eq("a process does not match a different start time",
             same_process(os.getpid(), dict(identity, starttime="0")), False)

        res = runner.capture(["sh", "-c", "exit 7"], limit_s=10, stage="selftest",
                             name="nonzero")
        c.eq("a tool that exits non-zero is not reported as succeeding",
             res["ok"], False)
        c.eq("a tool's exit code is kept", res["rc"], 7)
        res = runner.capture(["this-program-does-not-exist"], limit_s=5,
                             stage="selftest", name="missing")
        c.eq("a tool that cannot start is reported as not started",
             res["started"], False)


def selftest_outer_timeout(c: Checks) -> None:
    """The launcher's own timeout routes to a stop, not to a failure."""
    with tempfile.TemporaryDirectory() as d:
        clock = FakeClock(1000.0)
        state = make_state(Path(d), clock=clock,
                           env={"REMOTE_TIMEOUT": "7200", "M4_T0_EPOCH": "1000"})
        c.eq("a plain outer timeout is a stop", handle_outer_rc(state, 124), EXIT_GUARD)
        clock.t = 1000.0 + (7200 - OUTER_KILL_SLACK_S)
        c.eq("a kill at the outer deadline is a stop",
             handle_outer_rc(state, 137), EXIT_GUARD)
        clock.t = 1000.0 + 100
        c.eq("a kill a hundred seconds in is a failure",
             handle_outer_rc(state, 137), EXIT_INFRA)
        clock.t = 1000.0
        c.eq("a clean outer code is neither", handle_outer_rc(state, 0), EXIT_OK)


def selftest_guards(c: Checks) -> None:
    """A stage or a unit that will not fit is not started."""
    with tempfile.TemporaryDirectory() as d:
        clock = FakeClock(0.0)
        state = make_state(Path(d), clock=clock,
                           env={"REMOTE_TIMEOUT": "7200", "M4_T0_EPOCH": "0",
                                "PRICE_USD_PER_HOUR": "1.99", "BUDGET_LEFT_USD": "5"})
        c.eq("the clock cap binds at 1.99 dollars an hour", state.stop_at_s, 7200.0)
        c.ok("a stage that fits is allowed",
             guard_before_stage(state, "af2", 120) > 0)
        clock.t = 7200 - FETCH_MARGIN_S - ENDPOINTS_SLOT_S - 100
        c.raises("a stage that needs 150 s with 100 s left is not started",
                 lambda: guard_before_stage(state, "md", 150), GuardStop)
        c.raises("a unit that needs 150 s with 100 s left is not started",
                 lambda: guard_before_unit(state, "md", "md_complex", 100, 150),
                 GuardStop)
        clock.t = 0.0
        c.eq("before any unit finishes the floor estimate is used",
             state.unit_estimate("md_complex"), float(UNIT_FLOOR_S["md_complex"]))
        state.note_unit("md_complex", 300.0)
        state.note_unit("md_complex", 100.0)
        c.eq("after units finish their mean is the estimate",
             state.unit_estimate("md_complex"), 200.0)
        c.eq("every unit kind declares a floor",
             sorted(UNIT_FLOOR_S), ["af2_run", "anchor_parallel", "anchor_serial",
                                    "docking_pair", "endpoints", "md_complex",
                                    "storage"])

        state.install_seconds_used = 0.0
        limits = []
        for want in (900, 900, 900):
            lim = install_call_limit_s(state, want, 1800)
            limits.append(lim)
            spend_install_seconds(state, lim)
        c.eq("install calls that ask for 2,700 s in total stop at 1,800 s",
             sum(limits), 1800.0)
        c.eq("the install budget is then exhausted", state.install_total_exhausted, True)

        timeout_state = make_state(Path(d) / "b", env={})
        c.eq("an unforwarded timeout falls back to 7,200 s",
             timeout_state.remote_timeout_s, 7200.0)
        c.eq("an unforwarded timeout is labelled",
             timeout_state.remote_timeout_forwarded, False)
        high = make_state(Path(d) / "c", env={"REMOTE_TIMEOUT": "99999",
                                              "BUDGET_LEFT_USD": "99"})
        c.eq("a forwarded timeout above the cap is clipped",
             high.remote_timeout_s, 7200.0)
        c.eq("a forwarded budget above the cap is clipped",
             high.budget_left_usd, 5.0)
        moved = make_state(Path(d) / "e", env={"M4_T0_EPOCH": "12345"})
        c.eq("a planted bootstrap time moves the start of the clock",
             moved.t0, 12345.0)
        assumed = make_state(Path(d) / "f", env={"M4_BOOTSTRAP_ASSUMED": "1"})
        c.eq("an unreadable bootstrap time is labelled",
             assumed.bootstrap_assumed, True)


class FakeClock:
    """A clock the selftest moves by hand."""

    def __init__(self, t=0.0):
        self.t = float(t)

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += float(dt)


def _provenance_module():
    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here / "frozen"))
    import provenance
    return provenance


def make_state(base: Path, clock=None, env=None, runner=None) -> RunState:
    """A run state pointed at a temporary directory, for planted flows."""
    base = Path(base)
    state = RunState(
        base / "out", base / "work", base / "data",
        clock=clock or FakeClock(0.0),
        env=env if env is not None else {},
        provenance=_provenance_module(),
    )
    state.runner = runner or ToolRunner(state)
    return state


class FakeRunner:
    """Stands in for the tool runner: no real program is ever started.

    It answers each call the way the real tool would, writes the files the real
    tool would write, and moves the planted clock forward. Stage bodies cannot
    tell the difference, which is the point: the real stage bodies are what the
    selftest exercises.
    """

    def __init__(self, state: RunState, durations=None, failures=None,
                 timeouts=(), pose_text=None, rank_table=None, atoms=150000,
                 reporter_rate=128.96, smoke_problems=(), default_seconds=1.0,
                 skip_generation=False, pip_version="pip 24.0 from /v/pip (python 3.10)"):
        self.state = state
        self.skip_generation = skip_generation
        self.pip_version = pip_version
        self.durations = dict(durations or {})
        self.failures = dict(failures or {})
        self.timeouts = set(timeouts)
        self.pose_text = pose_text
        self.rank_table = rank_table or (
            "Swarm  Conformation  Receptor_ID  Ligand_ID  Scoring\n"
            "1      3             0            0          19.75\n"
            "0      7             0            0          12.50\n")
        self.atoms = atoms
        self.reporter_rate = reporter_rate
        self.smoke_problems = list(smoke_problems)
        self.default_seconds = default_seconds
        self.calls = []
        self.groups = {}
        self.skipped_signals = []
        self.log_dir = state.outdir / "tool_logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def kill_all_groups(self):
        return []

    def capture(self, cmd, *, limit_s, stage, name, cwd=None, extra_env=None):
        cmd = [str(x) for x in cmd]
        self.calls.append({"stage": stage, "name": name, "cmd": cmd})
        want = float(self.durations.get(name, self.default_seconds))
        timed_out = name in self.timeouts or want > limit_s
        taken = min(want, max(0.0, float(limit_s)))
        if hasattr(self.state.clock, "advance"):
            self.state.clock.advance(taken)
        log = self.log_dir / f"{stage}_{name}.log"
        atomic_write_text(log, "planted call: " + " ".join(cmd) + "\n")
        result = {"ok": False, "rc": 1, "timed_out": timed_out, "started": True,
                  "seconds": taken, "stdout": "", "stderr": "", "log": str(log),
                  "cmd": cmd}
        if timed_out:
            return result
        if name in self.failures:
            result["rc"] = self.failures[name]
            return result
        result["ok"] = True
        result["rc"] = 0
        result["stdout"] = self._side_effects(cmd, name, cwd)
        return result

    # -- what each planted tool leaves behind ------------------------------

    def _side_effects(self, cmd, name, cwd):
        work = Path(cwd) if cwd else self.state.workdir
        base = os.path.basename(cmd[0])
        if "--help" in cmd:
            return f"usage: {base}\n"
        if base == "nvidia-smi":
            if "--query-gpu=name,driver_version" in " ".join(cmd):
                return "NVIDIA A100-SXM4-40GB, 570.148.08\n"
            return ("| NVIDIA-SMI 570.148.08   Driver Version: 570.148.08   "
                    "CUDA Version: 12.8 |\n")
        if base == "apt-cache":
            return "Package: x\nVersion: 1.2.3-1\nSHA256: 00ff\n"
        if "pip" in cmd and "--version" in cmd:
            return self.pip_version + "\n"
        if "pip" in cmd and "download" in cmd:
            dest = Path(cmd[cmd.index("--dest") + 1])
            dest.mkdir(parents=True, exist_ok=True)
            (dest / f"pip-{PIP_BOOTSTRAP_VERSION}-py3-none-any.whl").write_bytes(
                b"planted installer wheel")
            return ("Collecting pip\n  Downloading "
                    f"https://files.pythonhosted.org/pip-{PIP_BOOTSTRAP_VERSION}"
                    "-py3-none-any.whl (2.1 MB)\n")
        if "--report" in cmd:
            path = Path(cmd[cmd.index("--report") + 1])
            atomic_write_text(path, json.dumps({"install": [
                {"download_info": {
                    "url": "https://files.pythonhosted.org/jax-0.4.35-cp310.whl",
                    "archive_info": {"hash": "sha256=aa11"}},
                 "metadata": {"name": "jax", "version": "0.4.35"}}]}))
            return ""
        if base == "curl":
            out = Path(cmd[cmd.index("-o") + 1])
            url = cmd[-1]
            out.parent.mkdir(parents=True, exist_ok=True)
            if url.endswith(".pdb"):
                out.write_text(planted_pdb_text())
            else:
                out.write_bytes(b"planted archive")
            return ""
        if base == "tar":
            target = Path(cmd[cmd.index("-C") + 1])
            target.mkdir(parents=True, exist_ok=True)
            for i in range(1, AF2_MODELS + 1):
                (target / f"params_model_{i}_multimer_v3.npz").write_bytes(b"p" * 64)
            return ""
        if name == "smoke_imports":
            return json.dumps({"problems": self.smoke_problems,
                               "found": {"jax": "0.4.35", "openmm": "8.2.0",
                                         "jax_devices": ["cuda"]}}) + "\n"
        if name == "package_versions":
            return json.dumps({"jax": "0.4.35", "jaxlib": "0.4.35",
                               "jax_cuda12_plugin": "0.4.35", "openmm": "8.2.0",
                               "lightdock": "0.9.4", "colabfold": "1.5.5"}) + "\n"
        if base.startswith("lightdock3_setup"):
            (work / "setup.json").write_text("{}")
            (work / "swarm_1").mkdir(parents=True, exist_ok=True)
            return "setup written\n"
        if base.startswith("lightdock3.py"):
            (work / "swarm_1").mkdir(parents=True, exist_ok=True)
            (work / "swarm_1" / "gso_20.out").write_text("planted swarm output\n")
            return "simulation done\n"
        if base.startswith("lgd_generate_conformations"):
            # The real step turns the search's numbers into pose structures.
            # A planted run that skips it leaves no pose file, which is how the
            # selftest checks that a missing pose ends the run as a failure.
            if not self.skip_generation:
                (work / "lightdock_3.pdb").write_text(
                    self.pose_text if self.pose_text is not None
                    else planted_pose_text())
            return "conformations written\n"
        if base.startswith("lgd_rank"):
            (work / "rank_by_scoring.list").write_text(self.rank_table)
            return "ranked\n"
        if base == "colabfold_batch":
            out_dir = Path(cmd[-1])
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "ranked_0.pdb").write_bytes(b"m" * 4096)
            return ("Query 1/1: pair (length 870)\n"
                    "model_1 took 120.0s (19 recycles)\n"
                    "model_2 took 100.0s (19 recycles)\nDone\n")
        if "--mode" in cmd and "build" in cmd:
            out = Path(cmd[cmd.index("--out") + 1])
            atomic_write_json(out, {"mode": "build", "atoms": self.atoms,
                                    "waters": 40000, "padding_nm": 1.5,
                                    "system_xml": str(work / "system.xml"),
                                    "solvated_pdb": str(work / "solvated.pdb")})
            return ""
        if "--mode" in cmd and "run" in cmd:
            out = Path(cmd[cmd.index("--out") + 1])
            steps = int(cmd[cmd.index("--steps") + 1])
            reporter = work / "md_reporter.csv"
            rate = "" if self.reporter_rate is None else f",{self.reporter_rate}"
            header = '#"Step","Temperature (K)"' + (
                ',"Speed (ns/day)"' if self.reporter_rate is not None else "")
            atomic_write_text(reporter, header + "\n" + f"5000,300.1{rate}\n")
            interval = int(cmd[cmd.index("--report-interval") + 1]) \
                if "--report-interval" in cmd else MD_REPORT_INTERVAL_STEPS
            trajectory = work / "md_trajectory.dcd"
            trajectory.write_bytes(b"t" * 1000)
            (work / "system.xml").write_bytes(b"s" * 5000)
            (work / "solvated.pdb").write_bytes(b"p" * 7000)
            atomic_write_json(out, {"mode": "run", "atoms": self.atoms,
                                    "steps": steps, "timestep_fs": MD_TIMESTEP_FS,
                                    "production_s": 335.0, "minimise_s": 10.0,
                                    "equilibrate_s": 5.0,
                                    "reporter_path": str(reporter),
                                    "trajectory_path": str(trajectory),
                                    "report_interval_steps": interval,
                                    "frame_interval_ps":
                                        interval * MD_TIMESTEP_FS / 1000.0,
                                    "platform": "CUDA", "precision": "mixed",
                                    "openmm_version": "8.2.0", "seed": 0})
            return ""
        return ""


def planted_pdb_text(capsid_residues=100, receptor_residues=60) -> str:
    """A small stand-in for the published structure, with two chains."""
    atoms = []
    for i in range(1, capsid_residues + 1):
        atoms.extend(_residue("A", i, 0.0, 0.0, 3.0 * i))
    for i in range(1, receptor_residues + 1):
        atoms.extend(_residue("B", 500 + i, 0.0, 4.0, 3.0 * i))
    return write_pdb(atoms)


def planted_pose_text() -> str:
    """A docked pose of the receptor that sits where the published one does."""
    atoms = []
    for i in range(1, 61):
        atoms.extend(_residue("B", 500 + i, 0.0, 4.0, 3.0 * i))
    return write_pdb(atoms)


# ---------------------------------------------------------------------------
# Planted stage flows: the whole order of stages, run with fakes.
# ---------------------------------------------------------------------------


def _fake_stage(name, action=None, decides=None, raises=None, stop=None):
    def fn(state):
        if raises is not None:
            raise raises
        if stop is not None:
            state.record_stop("ceiling_or_guard", name, stop)
        if action is not None:
            action(state)
        for cid, value in (decides or {}).items():
            emit_input_record(state, cid, value, n=3, rows_arm=None,
                              start_epoch=state.clock(), end_epoch=state.clock())
        if stop is None:
            state.stages_done.append(name)
    return (name, fn)


def _flow_state(tmp: Path, name: str, **runner_kwargs):
    state = make_state(tmp / name, clock=FakeClock(0.0),
                       env={"REMOTE_TIMEOUT": "7200", "M4_T0_EPOCH": "0",
                            "PRICE_USD_PER_HOUR": "1.99", "BUDGET_LEFT_USD": "5",
                            "INSTANCE_TYPE": "gpu_1x_a100_sxm4"})
    state.runner = FakeRunner(state, **runner_kwargs)
    return state


def selftest_stage_flow(c: Checks) -> None:
    """Every route out of the run, planted end to end with fake stages."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        decide_all = {"C1": 0.5, "C2": 129.0, "C3": 1.0, "C4": 216.0}

        # (a) every stage finishes
        st = _flow_state(tmp, "a")
        stages = [_fake_stage("install"), _fake_stage("controls"),
                  _fake_stage("anchor"),
                  _fake_stage("aux", decides={"C3": 1.0}),
                  _fake_stage("af2", decides={"C1": 0.5}),
                  _fake_stage("md", decides={"C2": 129.0}),
                  _fake_stage("storage", decides={"C4": 216.0})]
        code = run_stages(st, stages)
        c.eq("every stage finishing exits zero", code, EXIT_OK)
        c.eq("every stage finishing leaves the run valid", st.run_valid, True)
        c.eq("every input is then decided",
             sorted(k for k, v in st.inputs_status.items() if v["state"] == "decided"),
             INPUT_IDS)

        # (b) a time-guard stop part way through the prediction timings
        st = _flow_state(tmp, "b")
        def b_af2(state):
            add_row(state, "af2", {"pair": "pair1", "seed": 0, "wallclock_s": 1800.0})
            add_row(state, "af2", {"pair": "pair2", "seed": 0, "wallclock_s": 1810.0})
            emit_input_record(state, "C1", None, n=2, rows_arm="af2",
                              start_epoch=0, end_epoch=state.clock(),
                              void_reason=f"two of nine runs done; {LABEL_UNMEASURED}")
        stages = [_fake_stage("install"), _fake_stage("controls"),
                  _fake_stage("anchor"),
                  _fake_stage("aux", decides={"C3": 1.0}),
                  _fake_stage("af2", action=b_af2,
                              stop="the prediction stage ran out of time"),
                  _fake_stage("md", decides={"C2": 129.0}),
                  _fake_stage("storage", decides={"C4": 216.0})]
        code = run_stages(st, stages)
        c.eq("a guard stop in the prediction stage exits three", code, EXIT_GUARD)
        c.eq("a guard stop does not invalidate the run", st.run_valid, True)
        c.eq("the unfinished input is void",
             st.inputs_status["C1"]["decision"], "VOID")
        c.eq("the raw rows of the unfinished input are kept",
             (st.outdir / f"rows_af2_tag-{TAG}.jsonl").exists(), True)
        for cid in ("C2", "C3", "C4"):
            c.eq(f"{cid} is still decided after a stop elsewhere",
                 st.inputs_status[cid]["state"], "decided")
        rec = json.loads((st.outdir / f"endpoint-C2_tag-{TAG}.json").read_text())
        c.ok("a record written after a stop carries the incomplete-run label",
             LABEL_INCOMPLETE in rec["notes_list"])

        # (c) a tool timeout on the third complex of the dynamics stage
        st = _flow_state(tmp, "c")
        def c_md(state):
            emit_input_record(state, "C2", 129.0, n=2, rows_arm=None,
                              start_epoch=0, end_epoch=state.clock())
        stages = [_fake_stage("install"), _fake_stage("controls"),
                  _fake_stage("anchor"),
                  _fake_stage("aux", decides={"C3": 1.0}),
                  _fake_stage("af2", decides={"C1": 0.5}),
                  _fake_stage("md", action=c_md,
                              stop="a dynamics segment ran past the time allowed"),
                  _fake_stage("storage", decides={"C4": 216.0})]
        code = run_stages(st, stages)
        # A stop decides the exit code only through what it left unmeasured.
        # Here the dynamics input was still decided on two complexes and every
        # other input was decided too, so nothing is unmeasured and the run
        # ends at zero with the stop written down. That is what the two rules
        # about exit codes require: a stop is exit 3 when, and only when, it
        # "left at least one input unmeasured".
        c.eq("a tool timeout that left nothing unmeasured exits zero", code, EXIT_OK)
        c.eq("the stop is still written down", bool(st.stop_events), True)
        c.eq("the stage that stopped is not counted as done",
             "md" in st.stages_done, False)
        c.eq("a tool timeout does not invalidate the run", st.run_valid, True)
        c.eq("the dynamics input is still decided on two complexes",
             st.inputs_status["C2"]["state"], "decided")
        c.eq("the dynamics input records two complexes",
             json.loads((st.outdir / f"endpoint-C2_tag-{TAG}.json").read_text())
             ["values"]["n"], 2)

        # The same timeout, this time on a run where it did leave work
        # unmeasured: the storage input never gets its record, so the run ends
        # at three and that input is marked as left unmeasured by a stop.
        st = _flow_state(tmp, "c2")
        stages_c2 = [_fake_stage("install"), _fake_stage("controls"),
                     _fake_stage("anchor"),
                     _fake_stage("aux", decides={"C3": 1.0}),
                     _fake_stage("af2", decides={"C1": 0.5}),
                     _fake_stage("md", action=c_md,
                                 stop="a dynamics segment ran past the time allowed"),
                     _fake_stage("storage",
                                 stop="no time left for the storage stage")]
        code = run_stages(st, stages_c2)
        c.eq("a tool timeout that left an input unmeasured exits three",
             code, EXIT_GUARD)
        c.eq("a tool timeout that left an input unmeasured keeps the run valid",
             st.run_valid, True)
        c.eq("the input the stop left behind says a stop left it",
             st.inputs_status["C4"]["status"], "unmeasured_by_stop:ceiling_or_guard")
        c.eq("the inputs decided before the stop keep their decisions",
             [st.inputs_status[k]["state"] for k in ("C1", "C2", "C3")],
             ["decided", "decided", "decided"])

        # (d) a ceiling stop in the docking stage
        st = _flow_state(tmp, "d")
        stages = [_fake_stage("install"), _fake_stage("controls"),
                  _fake_stage("anchor"),
                  _fake_stage("aux", decides={"C3": 1.0},
                              stop="the docking stage reached its ceiling"),
                  _fake_stage("af2", decides={"C1": 0.5}),
                  _fake_stage("md", decides={"C2": 129.0}),
                  _fake_stage("storage", decides={"C4": 216.0})]
        code = run_stages(st, stages)
        c.eq("a ceiling stop in docking with everything decided exits zero",
             code, EXIT_OK)
        c.eq("the auxiliary input is still decided on the pairs that finished",
             st.inputs_status["C3"]["state"], "decided")
        c.eq("the docking stage that stopped is not counted as done",
             "aux" in st.stages_done, False)
        st = _flow_state(tmp, "d2")
        stages[3] = _fake_stage(
            "aux", action=lambda s: emit_input_record(
                s, "C3", None, n=1, rows_arm=None, start_epoch=0,
                end_epoch=s.clock(),
                void_reason=f"fewer than 2 pairs finished; {LABEL_UNMEASURED}"),
            stop="the docking stage reached its ceiling")
        code = run_stages(st, stages)
        c.eq("below two finished pairs the auxiliary input is void",
             st.inputs_status["C3"]["decision"], "VOID")
        c.eq("below two finished pairs the run still exits three", code, EXIT_GUARD)

        # (e) a real tool failure
        st = _flow_state(tmp, "e")
        stages = [_fake_stage("install"), _fake_stage("controls"),
                  _fake_stage("anchor",
                              raises=HarnessFailure("the docking run failed",
                                                    "exit 1")),
                  _fake_stage("aux", decides={"C3": 1.0})]
        code = run_stages(st, stages)
        c.eq("a real tool failure exits two", code, EXIT_INFRA)
        c.eq("a real tool failure invalidates the run", st.run_valid, False)
        c.eq("a real tool failure voids every input",
             sorted(k for k, v in st.inputs_status.items()
                    if v["decision"] == "VOID"), INPUT_IDS)
        for cid in INPUT_IDS:
            rec = json.loads((st.outdir / f"endpoint-{cid}_tag-{TAG}.json").read_text())
            c.eq(f"{cid}'s own file carries the invalid flag, not just the summary",
                 rec["run_valid"], False)
        write_run_done(st, code)
        done = json.loads((st.outdir / "RUN_DONE").read_text())
        for cid in INPUT_IDS:
            c.ok(f"the marker says {cid} was voided by a failure",
                 done["inputs"][cid]["status"].startswith("void_by_failure:"))
        c.ok("the marker names which failure voided it",
             "docking" in done["inputs"]["C1"]["status"])

        # (f) the anchor misses
        st = _flow_state(tmp, "f")
        def f_anchor(state):
            state.void_run("the anchor redocking missed its tolerance")
            raise AnchorMiss("the anchor redocking missed its tolerance")
        stages = [_fake_stage("install"), _fake_stage("controls"),
                  ("anchor", f_anchor), _fake_stage("aux", decides={"C3": 1.0})]
        code = run_stages(st, stages)
        c.eq("a missed anchor exits four", code, EXIT_ANCHOR)
        c.eq("a missed anchor invalidates the run", st.run_valid, False)
        c.eq("a missed anchor voids every input",
             sorted(k for k, v in st.inputs_status.items()
                    if v["decision"] == "VOID"), INPUT_IDS)
        write_run_done(st, code)
        done = json.loads((st.outdir / "RUN_DONE").read_text())
        c.eq("the marker says every input was voided by the anchor",
             sorted(k for k, v in done["inputs"].items()
                    if v["status"] == "void_by_anchor_miss"), INPUT_IDS)
        c.eq("after a missed anchor no input is said to be unmeasured by a stop",
             [k for k, v in done["inputs"].items()
              if str(v["status"]).startswith("unmeasured_by_stop")], [])
        c.ok("each voided input names what voided it",
             all(v.get("voided_by") for v in done["inputs"].values()))

        # (g) the planted sleep fails
        st = _flow_state(tmp, "g")
        def g_controls(state):
            state.void_run("the planted 60 s sleep read back wrong")
            raise HarnessFailure("the planted sleep check failed")
        code = run_stages(st, [_fake_stage("install"), ("controls", g_controls),
                               _fake_stage("anchor")])
        c.eq("a failed sleep check exits two", code, EXIT_INFRA)
        c.eq("a failed sleep check invalidates the run", st.run_valid, False)

        # (h) install, smoke check and download failures
        for label, reason in (("install", "installing the pinned packages failed"),
                              ("smoke check", "the smoke check failed"),
                              ("download", "downloading the published structure failed")):
            st = _flow_state(tmp, "h_" + label.replace(" ", "_"))
            code = run_stages(st, [_fake_stage("install",
                                               raises=HarnessFailure(reason)),
                                   _fake_stage("controls")])
            c.eq(f"a {label} failure exits two", code, EXIT_INFRA)
            c.eq(f"a {label} failure invalidates the run", st.run_valid, False)
            # The redocking check never ran, and its record says exactly that
            # instead of being absent, which is what launch 1 left behind.
            anchor_rec = json.loads(
                (st.outdir / f"endpoint-anchor_tag-{TAG}.json").read_text())
            for key in ("cell", "inputs", "metric", "values", "threshold",
                        "decision_rule", "decision", "run_valid"):
                c.ok(f"the anchor record after a {label} failure carries its {key}",
                     key in anchor_rec)
            c.eq(f"the anchor record after a {label} failure is void",
                 anchor_rec["decision"], "VOID")
            c.eq(f"the anchor record after a {label} failure has no measured value",
                 anchor_rec["values"]["measured"], None)
            c.ok(f"the anchor record after a {label} failure says it was not reached",
                 LABEL_ANCHOR_NOT_REACHED
                 in str(anchor_rec["values"]["null_reasons"].get("measured")))
            c.ok(f"the anchor record after a {label} failure names the published "
                 "placement", bool(anchor_rec["values"]["published"]))
            c.ok(f"the anchor record after a {label} failure carries its tolerance",
                 bool(anchor_rec["values"]["tolerance"]))
            c.eq(f"the anchor record after a {label} failure is invalid with the run",
                 anchor_rec["run_valid"], False)

        # (i) the launcher's own timeout
        st = _flow_state(tmp, "i")
        code = run_stages(st, [_fake_stage("install")], outer_rc=124)
        c.eq("the launcher's own timeout exits three", code, EXIT_GUARD)
        c.eq("the launcher's own timeout does not invalidate the run",
             st.run_valid, True)
        anchor_rec = json.loads(
            (st.outdir / f"endpoint-anchor_tag-{TAG}.json").read_text())
        c.eq("a run stopped before the anchor still leaves an anchor record",
             anchor_rec["decision"], "VOID")
        c.eq("that anchor record keeps the run's own validity",
             anchor_rec["run_valid"], True)

        # (j) the docking call in the anchor runs past its time
        st = _flow_state(tmp, "j")
        def j_anchor(state):
            raise GuardStop("the docking run ran past the time allowed for it",
                            stage="anchor")
        stages = [_fake_stage("install"), _fake_stage("controls"),
                  ("anchor", j_anchor), _fake_stage("aux", decides={"C3": 1.0}),
                  _fake_stage("af2", decides={"C1": 0.5})]
        code = run_stages(st, stages)
        c.eq("a docking timeout in the anchor exits three", code, EXIT_GUARD)
        c.eq("a docking timeout in the anchor leaves the run valid", st.run_valid, True)
        c.eq("a docking timeout in the anchor leaves the anchor undecided",
             "anchor" in st.stages_done, False)
        c.eq("no input is measured after an undecided anchor",
             sorted(k for k, v in st.inputs_status.items()
                    if v["state"] == "unmeasured"), INPUT_IDS)

        # (k) the docking leaves no readable pose
        st = _flow_state(tmp, "k")
        stages = [_fake_stage("install"), _fake_stage("controls"),
                  _fake_stage("anchor", raises=HarnessFailure(
                      "the docking rank table names no pose file that exists"))]
        code = run_stages(st, stages)
        c.eq("docking with no readable pose exits two", code, EXIT_INFRA)
        c.eq("docking with no readable pose invalidates the run", st.run_valid, False)

        # (l) void by rule, with no stop anywhere
        st = _flow_state(tmp, "l")
        def l_af2(state):
            emit_input_record(state, "C1", 0.5, n=9, rows_arm=None, start_epoch=0,
                              end_epoch=state.clock(), void_reason=LABEL_ZERO_SPREAD)
        def l_md(state):
            emit_input_record(state, "C2", 129.0, n=3, rows_arm=None, start_epoch=0,
                              end_epoch=state.clock(), void_reason=LABEL_NOT_A100)
        stages = [_fake_stage("install"), _fake_stage("controls"),
                  _fake_stage("anchor"), _fake_stage("aux", decides={"C3": 1.0}),
                  _fake_stage("af2", action=l_af2),
                  _fake_stage("md", action=l_md),
                  _fake_stage("storage", decides={"C4": 216.0})]
        code = run_stages(st, stages)
        c.eq("a void by rule with no stop exits zero", code, EXIT_OK)
        c.eq("a void by rule keeps the run valid", st.run_valid, True)
        c.eq("the wrong graphics processor voids the dynamics input",
             st.inputs_status["C2"]["decision"], "VOID")
        c.eq("zero spread across seeds voids the prediction input",
             st.inputs_status["C1"]["decision"], "VOID")
        done = json.loads((st.outdir / "RUN_DONE").read_text()) \
            if (st.outdir / "RUN_DONE").exists() else None
        write_run_done(st, code)
        done = json.loads((st.outdir / "RUN_DONE").read_text())
        c.eq("the marker carries the exit code", done["exit_code"], EXIT_OK)
        c.ok("the marker says why an input is void by rule",
             done["inputs"]["C1"]["status"].startswith("void_by_rule:"))
        c.ok("the marker names the rule that voided it",
             LABEL_ZERO_SPREAD in done["inputs"]["C1"]["status"])
        c.eq("the marker names a decided input",
             done["inputs"]["C3"]["status"], "decided")
        summary_text = (st.outdir / f"{TAG}_summary.json").read_text()
        c.eq("the summary's first key says what the run decides",
             list(json.loads(summary_text).keys())[0], "what_this_run_decides")
        c.ok("the summary's first key is first in the file as written",
             summary_text.index("what_this_run_decides")
             < summary_text.index("\"tag\""))
        c.ok("the summary never calls a same-box rerun a replication",
             "replication" not in summary_text.lower()
             or "never a replication" in summary_text)
        summary = json.loads(summary_text)
        c.eq("the summary does not present the fallback as triggered when the "
             "gate was not evaluated", summary["gate"]["fallback_triggered"], False)
        c.ok("the summary still carries the fallback text",
             summary["gate"]["fallback_text"] == GATE_ELSE)


def _planted_pair(name, total, seq, chain_map=None, receptor="B"):
    return {"pair": name, "capsid_slot": 1, "target_residues": total,
            "total_residues": total, "receptor_chain": receptor,
            "receptor_residues": 60, "capsid_pieces": [],
            "chain_map": chain_map or {"A": "capsid", receptor: "receptor"},
            "sequences": {"A": seq, receptor: "GG"},
            "sequence_joined": seq, "atoms": []}


def selftest_pairs(c: Checks) -> None:
    """The stand-in complexes are checked before any time is spent on them."""
    good = [_planted_pair("pair1", 780, "A" * 780),
            _planted_pair("pair2", 870, "B" * 870),
            _planted_pair("pair3", 960, "C" * 960)]
    try:
        assert_pairs(good)
        c.ok("three well-formed stand-in pairs pass every check", True)
    except HarnessFailure as exc:
        c.ok("three well-formed stand-in pairs pass every check", False, str(exc))

    short = [_planted_pair("pair1", 500, "A" * 500),
             _planted_pair("pair2", 870, "B" * 870),
             _planted_pair("pair3", 960, "C" * 960)]
    c.raises("a pair shorter than 750 residues is refused",
             lambda: assert_pairs(short), HarnessFailure)
    long_pair = [_planted_pair("pair1", 1200, "A" * 1200),
                 _planted_pair("pair2", 870, "B" * 870),
                 _planted_pair("pair3", 960, "C" * 960)]
    c.raises("a pair longer than 1,000 residues is refused",
             lambda: assert_pairs(long_pair), HarnessFailure)
    equal = [_planted_pair("pair1", 870, "A" * 870),
             _planted_pair("pair2", 875, "B" * 875),
             _planted_pair("pair3", 960, "C" * 960)]
    c.raises("two pair lengths closer than 20 residues are refused",
             lambda: assert_pairs(equal), HarnessFailure)
    same_seq = [_planted_pair("pair1", 780, "A" * 780),
                _planted_pair("pair2", 870, "A" * 780),
                _planted_pair("pair3", 960, "C" * 960)]
    c.raises("two pairs with the same sequence are refused",
             lambda: assert_pairs(same_seq), HarnessFailure)
    one_role = [dict(_planted_pair("pair1", 780, "A" * 780),
                     chain_map={"A": "capsid", "B": "capsid"}),
                _planted_pair("pair2", 870, "B" * 870),
                _planted_pair("pair3", 960, "C" * 960)]
    c.raises("a pair without a receptor-role chain is refused",
             lambda: assert_pairs(one_role), HarnessFailure)
    c.raises("two pairs instead of three are refused",
             lambda: assert_pairs(good[:2]), HarnessFailure)

    built = build_pairs(planted_pdb_text())
    c.eq("three stand-in pairs are built", len(built), 3)
    c.eq("the built lengths are the declared targets",
         [p["total_residues"] for p in built], PAIR_TARGET_LENGTHS)
    for p in built:
        c.ok(f"{p['pair']} is inside 750 to 1,000 residues",
             PAIR_RESIDUES_MIN <= p["total_residues"] <= PAIR_RESIDUES_MAX)
        c.ok(f"{p['pair']} holds both chain roles",
             set(p["chain_map"].values()) == {"capsid", "receptor"})
    try:
        assert_pairs(built)
        c.ok("the built pairs pass every assertion", True)
    except HarnessFailure as exc:
        c.ok("the built pairs pass every assertion", False, str(exc))
    c.raises("a structure with only one usable chain is refused",
             lambda: build_pairs(write_pdb(_residue("A", 1, 0, 0, 0))),
             HarnessFailure)


def selftest_dynamics_inputs(c: Checks) -> None:
    """The dynamics input must be the complex, and its speed must be read."""
    atoms, chain_map = planted_complex("B")
    pair = {"pair": "pair1", "chain_map": chain_map, "receptor_chain": "B",
            "atoms": atoms}
    receptor_only = [a for a in atoms if a["chain"] == "B"]
    merged = merge_capsid_and_pose(pair, receptor_only)
    roles = {("capsid" if a["chain"] == "A" else "receptor") for a in merged}
    c.eq("a merged complex holds both chain roles", roles, {"capsid", "receptor"})
    c.ok("a merged complex holds capsid heavy atoms",
         len(heavy_atoms([a for a in merged if a["chain"] == "A"])) > 0)
    empty_pair = {"pair": "p", "chain_map": {"B": "receptor"}, "receptor_chain": "B",
                  "atoms": receptor_only}
    c.raises("a receptor-only input is refused",
             lambda: merge_capsid_and_pose(empty_pair, receptor_only), HarnessFailure)
    c.raises("a complex with no docked pose is refused",
             lambda: merge_capsid_and_pose(pair, []), HarnessFailure)

    padding = water_padding_nm(merged)
    c.ok("the water padding is a sensible positive distance", 0.8 <= padding <= 10.0)
    c.raises("an empty complex cannot be given a water box",
             lambda: water_padding_nm([]), HarnessFailure)

    reporter = ('#"Progress (%)","Step","Potential Energy (kJ/mole)",'
                '"Temperature (K)","Speed (ns/day)","Time Remaining"\n'
                '2.0%,5000,-1234567.8,300.4,0,--\n'
                '100.0%,250000,-1234000.1,299.9,128.96,0:00\n')
    parsed = parse_reporter_file(reporter)
    c.eq("a reporter file in its real column layout parses",
         parsed["ns_per_day"], 128.96)
    no_rate = parse_reporter_file('#"Step","Temperature (K)"\n250000,300.0\n')
    c.eq("a reporter file with no rate line gives nothing", no_rate["ns_per_day"], None)
    c.eq("a reporter file with no rate line is labelled",
         LABEL_RATE_MISSING, "engine rate line missing")
    c.eq("129 against 100 fires the disagreement label",
         rates_disagree(129, 100), True)
    c.eq("the disagreement label is the one written down",
         LABEL_RATE_DISAGREE, "engine rate and wall-clock disagree")


def selftest_records(c: Checks) -> None:
    """Records go through the shared writer and carry every field a reader needs."""
    with tempfile.TemporaryDirectory() as d:
        st = _flow_state(Path(d), "rec")
        # A run that reached its measurements has finished its install, so the
        # installed packages may be asked for their versions.
        st.install_completed = True
        emit_input_record(st, "C1", 0.5, n=9, rows_arm=None,
                          start_epoch=0, end_epoch=100)
        rec = json.loads((st.outdir / f"endpoint-C1_tag-{TAG}.json").read_text())
        for key in ("cell", "inputs", "metric", "values", "threshold",
                    "decision_rule", "decision", "env", "run_valid", "kind"):
            c.ok(f"a record carries its {key}", key in rec)
        c.eq("a record's decision rule is stated before the values are known",
             rec["decision_rule"].startswith("inside"), True)
        c.eq("the measured value is in the card's unit",
             rec["values"]["unit"], CARD["C1"]["unit"])
        c.eq("the card's own value is carried", rec["values"]["card_value"], 0.5)
        c.eq("the card's own band is carried", rec["values"]["band"], [0.2, 1.25])
        c.eq("a passing value is decided PASS", rec["decision"], "PASS")
        c.eq("the card's gate is read on the prediction input",
             rec["values"]["gate_pass"], True)
        c.ok("the prediction input says alignment search time is excluded",
             LABEL_NO_MSA in rec["notes_list"])
        c.ok("every input record names the stand-in pairs",
             LABEL_STAND_IN in rec["notes_list"])
        c.ok("every input record names the single graphics processor",
             LABEL_ONE_GPU in rec["notes_list"])
        for key in MACHINE_KEYS:
            c.ok(f"a record's machine labels carry {key}", key in rec["values"]["machine"])
        for key in ENGINE_KEYS:
            c.ok(f"a record's engine labels carry {key}", key in rec["values"]["engine"])
        c.eq("a record's labels have nothing missing and no unexplained null",
             label_problems("C1", rec["values"]), [])
        c.eq("the graphics processor is named from a runtime query",
             rec["values"]["machine"]["gpu_name"], "NVIDIA A100-SXM4-40GB")
        c.eq("the driver's CUDA version is read from the banner",
             rec["values"]["machine"]["cuda_runtime_version"], "12.8")
        c.eq("the CUDA plugin's own version is carried beside it",
             rec["values"]["machine"]["cuda_plugin_version"], "0.4.35")
        c.eq("the start time is the stage's, not the write time",
             rec["values"]["machine"]["start_utc"], utc_of(0))
        c.ok("the build flags name the prediction implementation",
             "alphafold_implementation" in (rec["values"]["engine"]["build_flags"] or {}))

        emit_input_record(st, "C2", 129.0, n=3, rows_arm=None,
                          start_epoch=0, end_epoch=100)
        c2 = json.loads((st.outdir / f"endpoint-C2_tag-{TAG}.json").read_text())
        c.eq("the gate does not apply to the dynamics input",
             c2["values"]["gate"], GATE_NOT_APPLICABLE)
        emit_input_record(st, "C3", 1.0, n=3, rows_arm=None,
                          start_epoch=0, end_epoch=100)
        c3 = json.loads((st.outdir / f"endpoint-C3_tag-{TAG}.json").read_text())
        c.eq("the gate does not apply to the auxiliary input",
             c3["values"]["gate"], GATE_NOT_APPLICABLE)
        c.ok("the auxiliary input names whose reading it is",
             LABEL_AUX_READING in c3["notes_list"])
        emit_input_record(st, "C4", 216.0, n=3, rows_arm=None,
                          start_epoch=0, end_epoch=100)
        c4 = json.loads((st.outdir / f"endpoint-C4_tag-{TAG}.json").read_text())
        c.ok("the storage input names its scaling assumption",
             LABEL_STORAGE in c4["notes_list"])

        # the void propagates into every later file, not only the summary
        st.void_run("the anchor redocking missed its tolerance")
        emit_input_record(st, "C4", 216.0, n=3, rows_arm=None,
                          start_epoch=0, end_epoch=100)
        after = json.loads((st.outdir / f"endpoint-C4_tag-{TAG}.json").read_text())
        c.eq("a record written after the void carries the invalid flag",
             after["run_valid"], False)
        c.eq("the record names what voided it",
             after["run_valid_voided_by"].startswith("the anchor"), True)
        earlier = json.loads((st.outdir / f"endpoint-C1_tag-{TAG}.json").read_text())
        c.eq("a record written before the void still stands",
             earlier["run_valid"], True)

        st.record_stop("ceiling", "md", "the dynamics stage reached its ceiling")
        emit_input_record(st, "C2", None, n=0, rows_arm=None, start_epoch=0,
                          end_epoch=100, void_reason=f"{LABEL_UNMEASURED} (ceiling)")
        stopped = json.loads((st.outdir / f"endpoint-C2_tag-{TAG}.json").read_text())
        c.ok("a record written after a stop carries the incomplete-run label",
             LABEL_INCOMPLETE in stopped["notes_list"])
        c.eq("an unmeasured input is void, not holding",
             stopped["decision"], "VOID")
        c.ok("an unmeasured input says it is not holding",
             LABEL_UNMEASURED in str(stopped["values"]["void_reason"]))
        c.eq("the two labels are the ones written down",
             (LABEL_UNMEASURED, LABEL_INCOMPLETE),
             ("unmeasured, not holding",
              "incomplete run: unmeasured inputs are VOID, not holding"))

        write_run_valid(st)
        validity = json.loads((st.outdir / "RUN_VALID.json").read_text())
        c.eq("the validity file agrees with the records",
             validity["run_valid"], False)
        write_summary(st)
        summary = json.loads((st.outdir / f"{TAG}_summary.json").read_text())
        c.eq("the summary agrees with the validity file",
             summary["run_valid"], validity["run_valid"])
        c.ok("the summary carries the incomplete-run label",
             LABEL_INCOMPLETE in summary["notes"])
        c.ok("the summary restates every record",
             f"endpoint-C1_tag-{TAG}.json" in summary["records"])
        c.ok("the summary says a rerun on the same box is not a replication",
             "never a replication" in summary["no_relaunch_for_spread"])
        note = write_env_note(st).read_text()
        for key in SECRET_ENV_KEYS:
            c.ok(f"the environment note never prints {key}",
                 f"{key}=<not read" in note)
        c.ok("the environment note carries the timeout it saw",
             "remote_timeout_seen_s=" in note)
        c.ok("the environment note carries the bootstrap seconds",
             "pre_t0_seconds=" in note)

    # Where the version labels come from: this run's own install, or nothing.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        st = _flow_state(tmp, "versions_from_report")
        report = st.outdir / f"pip_report_tag-{TAG}.json"
        atomic_write_text(report, json.dumps({"install": [
            {"download_info": {
                "url": "https://files.pythonhosted.org/jax-0.4.35-cp310.whl",
                "archive_info": {"hash": "sha256=aa11"}},
             "metadata": {"name": "jax", "version": "0.4.35"}}]}))
        st.pip_report_path = report
        st.pip_report_sha256 = sha256_file(report)
        emit_input_record(st, "C1", 0.5, n=9, rows_arm=None,
                          start_epoch=0, end_epoch=100)
        rec = json.loads((st.outdir / f"endpoint-C1_tag-{TAG}.json").read_text())
        c.eq("a version named in this run's own download report is the one recorded",
             rec["values"]["engine"]["jax_version"], "0.4.35")
        c.eq("a package that report does not name carries no version",
             rec["values"]["engine"]["md_engine_version"], None)
        c.ok("that missing version still says why it is missing",
             bool(str(rec["values"]["null_reasons"].get("md_engine_version") or "")))

        # The install failed, so nothing was installed by this run: every
        # version is null with that reason, and no version is read from a
        # package the box image happened to carry.
        st2 = _flow_state(tmp, "versions_without_install")
        emit_input_record(
            st2, "C1", None, n=0, rows_arm=None, start_epoch=0, end_epoch=100,
            void_reason="the run ended on broken infrastructure: the install failed")
        rec2 = json.loads((st2.outdir / f"endpoint-C1_tag-{TAG}.json").read_text())
        for key in ("jax_version", "jaxlib_version", "jax_cuda_plugin_version"):
            c.eq(f"a failed install leaves {key} empty",
                 rec2["values"]["engine"][key], None)
            c.eq(f"a failed install says why {key} is empty",
                 rec2["values"]["null_reasons"][key], LABEL_NOT_INSTALLED)
        c.eq("a failed install leaves the CUDA plugin version empty",
             rec2["values"]["machine"]["cuda_plugin_version"], None)
        c.eq("a failed install says why the CUDA plugin version is empty",
             rec2["values"]["null_reasons"]["cuda_plugin_version"],
             LABEL_NOT_INSTALLED)
        c.eq("the reason a failed install gives is the one written down",
             LABEL_NOT_INSTALLED, "not installed: the install stage failed")
        c.ok("no installed package is asked for a version before the install finishes",
             not any(call["name"] == "package_versions" for call in st2.runner.calls))
        c.ok("no version label falls back to a constant",
             rec2["values"]["engine"]["build_flags"]["jax_version"] is None)


def selftest_real_stage_bodies(c: Checks) -> None:
    """The real stage bodies, with fake tools in a planted installed directory."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        bin_dir = tmp / "venv" / "bin"
        bin_dir.mkdir(parents=True)
        for tool in SMOKE_TOOLS + ["python3"]:
            p = bin_dir / tool
            p.write_text("#!/bin/sh\nexit 0\n")
            os.chmod(str(p), 0o755)

        durations = {"sleep60": 60.0, "empty_run": 0.5}
        for i, pair in enumerate(("pair1", "pair2", "pair3")):
            for seed in AF2_SEEDS:
                durations[f"af2_{pair}_seed{seed}"] = 180.0 + 3 * i + seed
        state = make_state(tmp / "run", clock=FakeClock(0.0),
                           env={"REMOTE_TIMEOUT": "7200", "M4_T0_EPOCH": "0",
                                "PRICE_USD_PER_HOUR": "1.99", "BUDGET_LEFT_USD": "5",
                                "INSTANCE_TYPE": "gpu_1x_a100_sxm4",
                                "M4_VENV_BIN": str(bin_dir),
                                "HF_TOKEN": "hf_secret"})
        state.runner = FakeRunner(state, durations=durations)

        # The installed prediction front end names its own completion marker;
        # the marker is written before any timed call, so the first timed call
        # cannot fetch its own parameters and stop being a timing.
        pkg = (bin_dir.parent / "lib" / "python3.10" / "site-packages" / "colabfold")
        pkg.mkdir(parents=True, exist_ok=True)
        (pkg / "download.py").write_text(
            'def download_alphafold_params(path):\n'
            '    if not os.path.isfile(f"{path}/download_complete.txt"):\n'
            '        fetch()\n')

        stage_install(state)
        c.eq("the install stage finishes", "install" in state.stages_done, True)
        params = state.datadir / "params"
        c.eq("the parameter files are in place before any timed call",
             missing_multimer_params(params), [])
        c.ok("the parameter archive was hashed", bool(state.params_sha256))
        c.ok("the completion marker the module names is written before any timing",
             (params / "download_complete.txt").exists())
        install_log = json.loads(
            (state.outdir / f"install_log_tag-{TAG}.json").read_text())
        c.eq("an installer that can report its downloads is not replaced",
             install_log["pip_bootstrap"]["ran"], False)
        c.eq("the marker names read from the module are recorded",
             install_log["params_markers"]["markers"], ["download_complete.txt"])
        resolved = install_log["smoke_check"]["found"]["resolved_tools"]
        for tool in SMOKE_TOOLS:
            c.eq(f"{tool} resolves through the installed directory",
                 resolved[tool], str(bin_dir / tool))
        c.ok("the download report is kept and hashed",
             state.pip_report_path.exists() and bool(state.pip_report_sha256))
        c.ok("the system package versions are kept", state.apt_hash_path.exists())
        pairs_doc = json.loads(state.pairs_path.read_text())
        c.eq("the pair evidence file lists three pairs", len(pairs_doc["pairs"]), 3)
        c.ok("the pair evidence carries a hash for each sequence file",
             all(p["fasta_sha256"] for p in pairs_doc["pairs"]))
        c.ok("each pair's sequence file was written",
             all(Path(p["fasta_path"]).exists() for p in pairs_doc["pairs"]))

        stage_controls(state)
        c.eq("the controls stage finishes", "controls" in state.stages_done, True)
        empty = json.loads(
            (state.outdir / f"control-empty-run_tag-{TAG}.json").read_text())
        c.eq("the empty run times the harness itself",
             empty["values"]["measured_s"], 0.5)
        c.eq("the empty run measures the bytes it created",
             empty["values"]["work_dir_bytes"], 0)
        c.eq("the empty run passes under two seconds", empty["decision"], "PASS")
        sleep_rec = json.loads(
            (state.outdir / f"control-sleep_tag-{TAG}.json").read_text())
        c.eq("the planted sleep reads back correctly", sleep_rec["decision"], "PASS")
        scale_rec = json.loads(
            (state.outdir / f"control-unit-and-scale_tag-{TAG}.json").read_text())
        c.eq("the units and the scale are stated before any band is compared",
             scale_rec["values"]["kind"], "worked_examples")
        raw_in = scale_rec["values"]["raw_values_in"]
        c.eq("it names the file that will hold the raw prediction seconds",
             raw_in["raw_alphafold_seconds_per_run"], f"rows_af2_tag-{TAG}.jsonl")
        c.eq("it names the file that will hold the engine rate lines",
             raw_in["md_engine_rate_lines_with_wallclock_beside_them"],
             f"rows_md_tag-{TAG}.jsonl")
        c.eq("it names the file that will hold the raw bytes per artifact",
             raw_in["raw_bytes_per_artifact"], f"rows_storage_tag-{TAG}.jsonl")
        for kind, fname in (("control_sleep", f"control-sleep_tag-{TAG}.json"),
                            ("control_empty_run",
                             f"control-empty-run_tag-{TAG}.json"),
                            ("control_unit_and_scale",
                             f"control-unit-and-scale_tag-{TAG}.json")):
            rec = json.loads((state.outdir / fname).read_text())
            c.eq(f"the {kind} record carries every label key it must",
                 label_problems(kind, rec["values"]), [])

        stage_anchor(state)
        c.eq("the anchor stage finishes", "anchor" in state.stages_done, True)
        anchor = json.loads(
            (state.outdir / f"endpoint-anchor_tag-{TAG}.json").read_text())
        c.eq("the anchor passes on a pose at the published placement",
             anchor["decision"], "PASS")
        c.eq("the anchor says the second docking code was not run",
             anchor["values"]["independent_code"], ANCHOR_INDEPENDENT_CODE)
        c.ok("the anchor's raw rank table is kept",
             any(p.name.startswith("rank_table_anchor")
                 for p in state.outdir.glob("*.list")))
        c.eq("the anchor record carries the docking parameters it used",
             anchor["values"]["docking_parameters"]["swarms"], DOCKING_SWARMS)
        c.eq("the anchor record carries the order the docking commands ran in",
             [s for s in anchor["values"]["docking_order_as_called"]
              if s in DOCKING_CORE_STEPS], DOCKING_CORE_STEPS)
        c.eq("the anchor record carries every label key it must",
             label_problems("anchor", anchor["values"]), [])

        stage_aux(state)
        c.eq("the auxiliary stage finishes", "aux" in state.stages_done, True)
        c.ok("a call-table row was written for each finished pair",
             (state.outdir / f"call_table_tag-{TAG}.json").exists())

        stage_af2(state)
        af2_rows = [json.loads(l) for l in
                    (state.outdir / f"rows_af2_tag-{TAG}.jsonl").read_text().splitlines()]
        c.eq("one raw row per timed prediction run", len(af2_rows), 9)
        c.ok("no timed prediction call downloaded anything",
             not any(r["download_in_timed_call"] for r in af2_rows))
        c1 = json.loads((state.outdir / f"endpoint-C1_tag-{TAG}.json").read_text())
        c.eq("the prediction input counts nine runs", c1["values"]["n"], 9)
        c.eq("the prediction input covers three pairs",
             len(c1["values"]["pairs_covered"]), 3)
        c.eq("the spread across seeds is not zero",
             c1["values"]["halt"], None)

        stage_md(state)
        md_rows = [json.loads(l) for l in
                   (state.outdir / f"rows_md_tag-{TAG}.jsonl").read_text().splitlines()]
        c.eq("one raw row per dynamics segment", len(md_rows), 3)
        c.eq("the engine's own speed is read from the reporter file",
             md_rows[0]["engine_ns_per_day"], 128.96)
        c.eq("each dynamics row says how often a frame was written",
             md_rows[0]["frame_interval_ps"], MD_FRAME_INTERVAL_PS)
        c.ok("the trajectory itself is counted",
             md_rows[0]["trajectory_bytes"] > 0)
        c.ok("the reporter file is kept beside the record",
             Path(md_rows[0]["reporter_file"]).exists())
        c.eq("the built system is inside the required atom range",
             MD_ATOMS_MIN <= md_rows[0]["atoms"] <= MD_ATOMS_MAX, True)
        c2 = json.loads((state.outdir / f"endpoint-C2_tag-{TAG}.json").read_text())
        c.eq("the dynamics input rests on three complexes", c2["values"]["n"], 3)
        c.eq("the dynamics input carries its timestep",
             c2["values"]["timestep_fs"], MD_TIMESTEP_FS)
        c.eq("the dynamics input carries its production length",
             c2["values"]["production_ns"], MD_PRODUCTION_NS)
        c.eq("the dynamics input carries each complex's atom count",
             len(c2["values"]["atom_counts"]), 3)
        c.eq("the dynamics input carries the engine precision",
             c2["values"]["engine_precision"], MD_PRECISION)

        stage_storage(state)
        storage_rows = [json.loads(l) for l in
                        (state.outdir / f"rows_storage_tag-{TAG}.jsonl")
                        .read_text().splitlines()]
        c.eq("one raw row per storage measurement", len(storage_rows), 3)
        c4 = json.loads((state.outdir / f"endpoint-C4_tag-{TAG}.json").read_text())
        c.ok("the storage input also reports the 432-run figure",
             c4["values"]["gib_432_runs"] is not None)
        c.ok("the storage input also reports the intermediates-deleted figure",
             c4["values"]["gib_216_runs_intermediates_deleted"] is not None)
        c.ok("the storage input reports bytes per nanosecond of dynamics",
             c4["values"]["md_bytes_per_ns"] is not None)
        c.eq("the storage input says how often a frame was written",
             c4["values"]["frame_interval_ps"], MD_FRAME_INTERVAL_PS)
        c.eq("the bytes the segment merely set up are reported apart",
             c4["values"]["md_setup_bytes"], 12000)
        c.ok("the segment's own bytes are the trajectory, the rate file and the logs",
             c4["values"]["md_bytes"] >= 1000)
        c.eq("the storage input carries every label key it must",
             label_problems("C4", c4["values"]), [])

        stage_endpoints(state)
        summary_text = (state.outdir / f"{TAG}_summary.json").read_text()
        c.eq("the summary's first key says what the run decides",
             list(json.loads(summary_text).keys())[0], "what_this_run_decides")
        c.eq("the run is still valid after the real stage bodies",
             state.run_valid, True)
        for log in (state.outdir / "tool_logs").glob("*.log"):
            c.ok(f"no download token appears in {log.name}",
                 "hf_secret" not in log.read_text())
            break


def selftest_docking_routes(c: Checks) -> None:
    """The three ways a docking call can end, and they never overlap."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        bin_dir = tmp / "bin"
        bin_dir.mkdir(parents=True)
        for tool in SMOKE_TOOLS + ["python3"]:
            (bin_dir / tool).write_text("#!/bin/sh\nexit 0\n")

        def fresh(sub, **kw):
            st = make_state(tmp / sub, clock=FakeClock(0.0),
                            env={"REMOTE_TIMEOUT": "7200", "M4_T0_EPOCH": "0",
                                 "INSTANCE_TYPE": "gpu_1x_a100_sxm4",
                                 "M4_VENV_BIN": str(bin_dir)})
            st.runner = FakeRunner(st, **kw)
            return st

        st = fresh("timeout", timeouts=("anchor_x_simulate",))
        c.raises("a docking call over its allowance is a ceiling stop",
                 lambda: run_docking(st, "anchor_x", tmp / "r.pdb", tmp / "l.pdb",
                                     tmp / "w1", 250, 1, "anchor"), GuardStop)
        st = fresh("failure", failures={"anchor_x_simulate": 1})
        c.raises("a docking tool that fails is broken infrastructure",
                 lambda: run_docking(st, "anchor_x", tmp / "r.pdb", tmp / "l.pdb",
                                     tmp / "w2", 250, 1, "anchor"), HarnessFailure)
        st = fresh("unparsable",
                   rank_table="Swarm Conformation\n0 7\n")
        c.raises("a rank table with no rank column is broken infrastructure",
                 lambda: run_docking(st, "anchor_x", tmp / "r.pdb", tmp / "l.pdb",
                                     tmp / "w3", 250, 1, "anchor"), HarnessFailure)
        st = fresh("ok")
        result = run_docking(st, "anchor_x", tmp / "r.pdb", tmp / "l.pdb",
                             tmp / "w4", 250, 1, "anchor")
        c.eq("a good docking call returns the tool's own first-ranked pose",
             result["top_row"]["Conformation"], "3")
        c.ok("the pose file is kept beside the record",
             Path(result["pose_path"]).exists())
        c.ok("the raw rank table is kept beside the record",
             Path(result["rank_table"]).exists())


def selftest_install_ceiling(c: Checks) -> None:
    """Install steps that together ask for more than the budget stop at the budget."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        bin_dir = tmp / "bin"
        bin_dir.mkdir(parents=True)
        for tool in SMOKE_TOOLS + ["python3"]:
            p = bin_dir / tool
            p.write_text("#!/bin/sh\nexit 0\n")
            os.chmod(str(p), 0o755)
        st = make_state(tmp / "run", clock=FakeClock(0.0),
                        env={"REMOTE_TIMEOUT": "7200", "M4_T0_EPOCH": "0",
                             "INSTANCE_TYPE": "gpu_1x_a100_sxm4",
                             "M4_VENV_BIN": str(bin_dir)})
        st.runner = FakeRunner(st, durations={
            "apt_cache_show_python3-venv": 60.0, "apt_cache_show_aria2": 60.0,
            "apt_cache_show_curl": 60.0, "pip_install": 1200.0,
            "download_pdb": 300.0, "download_params": 900.0,
        })
        c.raises("install steps that ask for more than 1,800 s stop at 1,800 s",
                 lambda: stage_install(st), HarnessFailure)
        c.ok("the install budget is reported as used up",
             st.install_seconds_used >= STAGE_CEILING_S["install"])


def selftest_label_keys(c: Checks) -> None:
    """Every record kind says what machine and what software produced it."""
    c.eq("the nine labels are all covered by a key name",
         label_keys_cover_nine(), [])
    for kind in MEASURED_KINDS:
        c.ok(f"{kind} records declare an engine block",
             bool(REQUIRED_LABEL_KEYS[kind]["engine"]))
    for kind in CONTROL_KINDS:
        c.eq(f"{kind} records need only the machine block",
             REQUIRED_LABEL_KEYS[kind]["engine"], ())
    c.ok("the machine block covers instance, processor, driver, CUDA, times and price",
         all(any(word in k for k in MACHINE_KEYS)
             for word in ("instance", "gpu", "driver", "cuda", "start", "end", "price")))

    with tempfile.TemporaryDirectory() as d:
        st = _flow_state(Path(d), "labels")
        emit_input_record(st, "C1", 0.5, n=9, rows_arm=None, start_epoch=0,
                          end_epoch=100)
        stage_controls_records = {
            "C1": f"endpoint-C1_tag-{TAG}.json",
        }
        rec = json.loads((st.outdir / stage_controls_records["C1"]).read_text())
        c.eq("a complete record has no label problem",
             label_problems("C1", rec["values"]), [])

        # a planted record with one key taken out must fail the check
        broken = json.loads(json.dumps(rec["values"]))
        broken["machine"].pop("gpu_name")
        problems = label_problems("C1", broken)
        c.ok("a record missing one label key fails the check", bool(problems))
        c.ok("the failure names the missing key",
             any("gpu_name" in p for p in problems))

        # a planted null with no reason must fail the check
        nulled = json.loads(json.dumps(rec["values"]))
        nulled["machine"]["gpu_driver"] = None
        nulled["null_reasons"].pop("gpu_driver", None)
        problems = label_problems("C1", nulled)
        c.ok("a null label with no reason fails the check", bool(problems))
        c.ok("the failure says the reason is missing",
             any("no reason" in p for p in problems))

        # a null with a reason is allowed, because a key is never left out
        excused = json.loads(json.dumps(rec["values"]))
        excused["machine"]["gpu_driver"] = None
        excused["null_reasons"]["gpu_driver"] = "the driver did not report itself"
        c.eq("a null label with a reason passes", label_problems("C1", excused), [])

        c.ok("an unknown record kind is refused rather than passed",
             bool(label_problems("not-a-kind", rec["values"])))


def selftest_pip_pins(c: Checks) -> None:
    """The pinned requirements, the installer's version, and the one bootstrap."""
    pin = parse_pin("openmm[cuda12]==8.2.0")
    c.eq("a pinned requirement with an extra names its package", pin["name"], "openmm")
    c.eq("a pinned requirement with an extra names the extra", pin["extras"], ["cuda12"])
    c.eq("a pinned requirement names its exact version", pin["version"], "8.2.0")
    c.eq("a pinned requirement without an extra parses",
         parse_pin("jax==0.4.35")["extras"], [])
    c.raises("a requirement without an exact version is refused",
             lambda: parse_pin("openmm"), ParseError)
    c.raises("a requirement pinned only by a range is refused",
             lambda: parse_pin("openmm>=8.2"), ParseError)

    c.eq("this run's own pinned requirements are usable as written",
         pip_pins_problems(PIP_PINS), [])
    c.eq("the dynamics engine with a CUDA sibling package passes",
         pip_pins_problems(["openmm==8.2.0", "openmm-cuda==8.1.1.12"]), [])
    c.eq("a differently named CUDA sibling package also passes",
         pip_pins_problems(["openmm==8.2.0", "openmm-cuda-12==8.2.0"]), [])
    c.ok("the dynamics engine carrying a bracketed extra is refused",
         bool(pip_pins_problems(["openmm[cuda12]==8.2.0"])))
    c.ok("a bracketed extra is refused even beside a CUDA sibling",
         bool(pip_pins_problems(["openmm[cuda12]==8.2.0",
                                 "openmm-cuda==8.1.1.12"])))
    c.ok("the plain dynamics engine with no CUDA form is refused",
         bool(pip_pins_problems(["openmm==8.2.0"])))
    c.ok("an entry without an exact version fails the check",
         bool(pip_pins_problems(["openmm==8.2.0", "openmm-cuda==8.1.1.12",
                                 "lightdock"])))
    c.ok("the CUDA sibling package pinned on its own is refused",
         bool(pip_pins_problems(["openmm-cuda==8.1.1.12"])))
    c.eq("this run installs exactly the nine requirements it was given, in order",
         list(PIP_PINS),
         ["jax==0.4.35",
          "jaxlib==0.4.35",
          "jax-cuda12-plugin[with_cuda]==0.4.35",
          "jax-cuda12-pjrt==0.4.35",
          "colabfold==1.5.5",
          "alphafold-colabfold==2.3.6",
          "openmm==8.1.1",
          "openmm-cuda==8.1.1.12",
          "lightdock==0.9.4"])
    c.ok("this run pins the plain dynamics engine, with no extra",
         "openmm==8.1.1" in PIP_PINS)
    c.ok("this run pins the CUDA sibling package of the dynamics engine",
         any(p.startswith("openmm-cuda") for p in PIP_PINS))
    source_text = Path(__file__).read_text()
    c.ok("the chosen form is stated in the file beside the pins",
         "THE SIBLING PACKAGE" in source_text)
    c.ok("the comment beside the pins says the pairing was inferred, not verified",
         "INFERENCES MADE BY THE REVIEW BOARD" in source_text)
    for named in ("gate_report_build13.md", "pip_pins_resolve_build11.txt",
                  "install_pip_install.log"):
        c.ok(f"the comment beside the pins names the record {named}",
             named in source_text)
    quoted = re.search(r"SIBLING REQUIRES ENGINE VERSION:\s*([0-9][0-9.]*)",
                       source_text)
    c.ok("the comment states which engine release the sibling package needs",
         quoted is not None)
    c.eq("the engine is pinned to the release the comment says the sibling needs",
         parse_pin([p for p in PIP_PINS if p.startswith("openmm==")][0])["version"],
         quoted.group(1) if quoted else None)
    extras_in_list = {parse_pin(p)["name"]: parse_pin(p)["extras"]
                      for p in PIP_PINS if parse_pin(p)["extras"]}
    c.eq("the graphics plugin is the only requirement asked for with an extra",
         extras_in_list, {"jax-cuda12-plugin": ["with_cuda"]})
    c.eq("the requirements with that one extra are usable as written",
         pip_pins_problems(PIP_PINS), [])

    c.eq("an installer that can report downloads needs no bootstrap",
         pip_needs_bootstrap("pip 23.0.1 from /usr/lib/python3/dist-packages/pip "
                             "(python 3.10)"), False)
    c.eq("an older installer is bootstrapped once",
         pip_needs_bootstrap("pip 22.0.2 from /usr/lib/python3/dist-packages/pip "
                             "(python 3.10)"), True)
    c.eq("the first version that can report is not bootstrapped",
         pip_needs_bootstrap("pip 22.2 from /x (python 3.10)"), False)
    c.raises("an unreadable installer version stops the run",
             lambda: pip_needs_bootstrap("not a version at all"), HarnessFailure)
    # The whole install stage, run with an installer too old to report its
    # downloads: the one allowed bootstrap happens and is recorded in full.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        bin_dir = tmp / "venv" / "bin"
        bin_dir.mkdir(parents=True)
        for tool in SMOKE_TOOLS + ["python3"]:
            p = bin_dir / tool
            p.write_text("#!/bin/sh\nexit 0\n")
            os.chmod(str(p), 0o755)
        st = make_state(tmp / "run", clock=FakeClock(0.0),
                        env={"REMOTE_TIMEOUT": "7200", "M4_T0_EPOCH": "0",
                             "INSTANCE_TYPE": "gpu_1x_a100_sxm4",
                             "M4_VENV_BIN": str(bin_dir)})
        st.runner = FakeRunner(st, pip_version="pip 22.0.2 from /usr/lib (python 3.10)")
        stage_install(st)
        entry = json.loads(
            (st.outdir / f"install_log_tag-{TAG}.json").read_text())["pip_bootstrap"]
        c.eq("an installer that cannot report downloads is replaced once",
             entry["ran"], True)
        c.ok("the bootstrap records the address it came from",
             str(entry["url"]).startswith("https://"))
        c.eq("the bootstrap records a full hash of the wheel",
             len(str(entry["sha256"])), 64)
        c.ok("the bootstrap records how long it took", entry["seconds"] >= 0)
        c.ok("the bootstrap keeps its verbose log",
             Path(entry["verbose_log"]).exists())
        names = [call["name"] for call in st.runner.calls]
        c.eq("the installer is downloaded once and installed once",
             [names.count("pip_bootstrap_download"),
              names.count("pip_bootstrap_install")], [1, 1])
        c.eq("the pinned install still writes its own download report",
             st.pip_report_path.exists(), True)

    c.eq("the address of a downloaded wheel is read from the verbose log",
         parse_pip_download_log(
             "Collecting pip\n  Downloading "
             "https://files.pythonhosted.org/pip-24.0-py3-none-any.whl (2.1 MB)\n"),
         "https://files.pythonhosted.org/pip-24.0-py3-none-any.whl")
    c.eq("a verbose log with no wheel address gives nothing",
         parse_pip_download_log("Collecting pip\n"), None)


def selftest_parameter_markers(c: Checks) -> None:
    """The completion markers are read from the installed module, never recalled."""
    one = ('def download_alphafold_params(path):\n'
           '    if not os.path.isfile(f"{path}/download_complete.txt"):\n'
           '        fetch()\n')
    c.eq("a module naming one marker yields that one name",
         colabfold_marker_names(one), ["download_complete.txt"])
    two = (one + '    if not os.path.isfile(f"{path}/download_finished.txt"):\n'
                 '        fetch()\n')
    c.eq("a module naming two markers yields both",
         colabfold_marker_names(two),
         ["download_complete.txt", "download_finished.txt"])
    c.eq("a module naming no marker yields none",
         colabfold_marker_names("def download(path):\n    fetch()\n"), [])
    c.eq("the same name twice is named once",
         colabfold_marker_names(one + one), ["download_complete.txt"])

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        bin_dir = tmp / "venv" / "bin"
        bin_dir.mkdir(parents=True)
        pkg = tmp / "venv" / "lib" / "python3.10" / "site-packages" / "colabfold"
        pkg.mkdir(parents=True)
        (pkg / "download.py").write_text(two)
        st = make_state(tmp / "run", env={"M4_VENV_BIN": str(bin_dir)})
        params = st.datadir / "params"
        params.mkdir(parents=True, exist_ok=True)
        found = write_parameter_markers(st, params)
        c.eq("both markers the module names are written", found["markers"],
             ["download_complete.txt", "download_finished.txt"])
        c.ok("the marker files are on disk beside the parameters",
             all((params / n).exists() for n in found["markers"]))

        empty_pkg = tmp / "venv2" / "lib" / "python3.10" / "site-packages" / "colabfold"
        empty_pkg.mkdir(parents=True)
        (empty_pkg / "download.py").write_text("def download(path):\n    fetch()\n")
        st2 = make_state(tmp / "run2",
                         env={"M4_VENV_BIN": str(tmp / "venv2" / "bin")})
        (tmp / "venv2" / "bin").mkdir(parents=True, exist_ok=True)
        params2 = st2.datadir / "params"
        params2.mkdir(parents=True, exist_ok=True)
        found2 = write_parameter_markers(st2, params2)
        c.eq("a module naming no marker writes none", found2["markers"], [])
        c.eq("and the record says so", found2["note"], "no marker named")


def selftest_storage_details(c: Checks) -> None:
    """What one dynamics segment writes, and what it merely set up."""
    with tempfile.TemporaryDirectory() as d:
        md = Path(d) / "md_pair1"
        md.mkdir(parents=True)
        (md / "md_trajectory.dcd").write_bytes(b"t" * 1000)
        (md / "md_reporter.csv").write_bytes(b"r" * 100)
        (md / "md_run.log").write_bytes(b"l" * 24)
        (md / "system.xml").write_bytes(b"s" * 5000)
        (md / "solvated.pdb").write_bytes(b"p" * 7000)
        split = md_bytes_breakdown(md)
        c.eq("the segment's own bytes are the trajectory, the rate file and the log",
             split["md_bytes"], 1124)
        c.eq("the system and the solvated structure are set-up bytes",
             split["md_setup_bytes"], 12000)
        (md / "state.chk").write_bytes(b"c" * 999)
        c.eq("a checkpoint is set-up bytes too",
             md_bytes_breakdown(md)["md_setup_bytes"], 12999)
        c.eq("a checkpoint does not change the written bytes",
             md_bytes_breakdown(md)["md_bytes"], 1124)
        extra = Path(d) / "tool.log"
        extra.write_bytes(b"x" * 10)
        c.eq("the tool's own log counts towards the written bytes",
             md_bytes_breakdown(md, [extra])["md_bytes"], 1134)

    c.ok("the dynamics worker writes a trajectory",
         "DCDReporter" in MD_WORKER_SOURCE)
    c.eq("a frame every 5,000 steps at two femtoseconds is one every 10 picoseconds",
         MD_FRAME_INTERVAL_PS, 10.0)
    c.eq("fifty frames make up the half-nanosecond segment",
         int(round(MD_PRODUCTION_NS * 1e6 / MD_TIMESTEP_FS / MD_REPORT_INTERVAL_STEPS)),
         50)


def selftest_allowances(c: Checks) -> None:
    """One formula decides how long a stage may take, and it is never negative."""
    with tempfile.TemporaryDirectory() as d:
        clock = FakeClock(0.0)
        st = make_state(Path(d), clock=clock,
                        env={"REMOTE_TIMEOUT": "7200", "M4_T0_EPOCH": "0",
                             "PRICE_USD_PER_HOUR": "1.99", "BUDGET_LEFT_USD": "5"})
        c.eq("at the start the install stage may use its whole ceiling",
             stage_allowance_s(st, "install"), 1800.0)
        clock.t = 6000.0
        c.eq("with 1,200 s of the run left the prediction stage may use 700 s",
             stage_allowance_s(st, "af2"), 700.0)
        clock.t = 6800.0
        c.eq("with 400 s left the allowance is zero, never negative",
             stage_allowance_s(st, "af2"), 0.0)
        c.raises("a stage with no allowance is not started",
                 lambda: guard_before_stage(st, "af2", 120), GuardStop)
        clock.t = 0.0
        # The seven slots the directive names: installing, the controls and the
        # anchor together, the per-pair docking, the prediction timings, the
        # dynamics timings, the closing stage and the margin. The controls and
        # the anchor each get their own 700 s allowance, so in practice the
        # pair can use about 770 s and the margin absorbs the difference. The
        # storage stage's own 100 s is not one of the seven. This sum is an
        # arithmetic check on the slots, not the guarantee: the guarantee is
        # the allowance formula checked just above.
        c.eq("the seven slots sum to the whole cap",
             (STAGE_CEILING_S["install"] + STAGE_CEILING_S["controls"]
              + STAGE_CEILING_S["aux"] + STAGE_CEILING_S["af2"]
              + STAGE_CEILING_S["md"] + STAGE_CEILING_S["endpoints"]
              + FETCH_MARGIN_S), TOTAL_CEILING_S)
        c.eq("the controls and the anchor each have the same allowance",
             STAGE_CEILING_S["anchor"], STAGE_CEILING_S["controls"])

        st.install_seconds_used = 0.0
        limits = []
        for _ in range(3):
            lim = install_call_limit_s(st, 1000, stage_allowance_s(st, "install"))
            limits.append(lim)
            spend_install_seconds(st, lim)
        c.eq("three install calls asking 1,000 s each get 1,000, 800 and 0",
             limits, [1000.0, 800.0, 0.0])
        c.eq("the install budget is then exhausted", st.install_total_exhausted, True)


def selftest_spend(c: Checks) -> None:
    """What the run reports it has spent, with the bootstrap counted exactly once."""
    with tempfile.TemporaryDirectory() as d:
        clock = FakeClock(0.0)
        st = make_state(Path(d), clock=clock,
                        env={"M4_T0_EPOCH": "0", "PRICE_USD_PER_HOUR": "1.99",
                             "M4_PRE_T0_SECONDS": "300", "REMOTE_TIMEOUT": "7200"})
        clock.t = 3600.0
        c.eq("an hour since the run's start at 1.99 an hour is 1.99",
             round(st.spend_usd(), 2), 1.99)
        c.eq("the bootstrap seconds are reported, not added again",
             st.pre_t0_seconds, 300.0)
        clock.t = 7200.0
        c.eq("two hours since the run's start is 3.98",
             round(st.spend_usd(), 2), 3.98)


def selftest_docking_order(c: Checks) -> None:
    """Prepare, search, build the poses, rank: in that order, and the poses exist."""
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        bin_dir = tmp / "bin"
        bin_dir.mkdir(parents=True)
        for tool in SMOKE_TOOLS + ["python3"]:
            (bin_dir / tool).write_text("#!/bin/sh\nexit 0\n")

        def fresh(sub, **kw):
            st = make_state(tmp / sub, clock=FakeClock(0.0),
                            env={"REMOTE_TIMEOUT": "7200", "M4_T0_EPOCH": "0",
                                 "INSTANCE_TYPE": "gpu_1x_a100_sxm4",
                                 "M4_VENV_BIN": str(bin_dir)})
            st.runner = FakeRunner(st, **kw)
            return st

        st = fresh("order")
        result = run_docking(st, "anchor_x", tmp / "r.pdb", tmp / "l.pdb",
                             tmp / "w", 250, 1, "anchor")
        core = [s for s in result["call_order"] if s in DOCKING_CORE_STEPS]
        c.eq("the docking steps are search, build the poses, then rank",
             core, DOCKING_CORE_STEPS)
        c.eq("the search is prepared first", result["call_order"][0], "setup")
        c.eq("the docking parameters are the declared ones",
             [result["parameters"]["swarms"], result["parameters"]["glowworms"],
              result["parameters"]["steps"]],
             [DOCKING_SWARMS, DOCKING_GLOWWORMS, DOCKING_STEPS])
        c.eq("the docking is never restrained toward the published interface",
             result["parameters"]["restrained_to_the_published_interface"], False)

        st = fresh("nogen", skip_generation=True)
        c.raises("a docking run that builds no pose is broken infrastructure",
                 lambda: run_docking(st, "anchor_x", tmp / "r.pdb", tmp / "l.pdb",
                                     tmp / "w2", 250, 1, "anchor"), HarnessFailure)

        # one failing tool is called once: no second tool and no second source
        st = fresh("once", failures={"anchor_x_simulate": 1})
        try:
            run_docking(st, "anchor_x", tmp / "r.pdb", tmp / "l.pdb",
                        tmp / "w3", 250, 1, "anchor")
        except HarnessFailure:
            pass
        tried = [call for call in st.runner.calls
                 if call["name"] == "anchor_x_simulate"]
        c.eq("a failing tool is called once and nothing else is tried",
             len(tried), 1)
        c.eq("no later docking step runs after the failure",
             [call["name"] for call in st.runner.calls
              if call["name"].endswith(("_rank", "_generate_conformations"))], [])


def selftest_docking_pair_loop(c: Checks) -> None:
    """A pair that reaches its cap is kept, left out of the mean, and not the end."""
    def planted_aux_state(tmp: Path, name: str, timeouts=()):
        bin_dir = tmp / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        for tool in SMOKE_TOOLS + ["python3"]:
            p = bin_dir / tool
            p.write_text("#!/bin/sh\nexit 0\n")
            os.chmod(str(p), 0o755)
        st = make_state(tmp / name, clock=FakeClock(0.0),
                        env={"REMOTE_TIMEOUT": "7200", "M4_T0_EPOCH": "0",
                             "INSTANCE_TYPE": "gpu_1x_a100_sxm4",
                             "M4_VENV_BIN": str(bin_dir)})
        st.runner = FakeRunner(st, timeouts=timeouts)
        st.datadir.mkdir(parents=True, exist_ok=True)
        (st.datadir / f"{PDB_ENTRY}.pdb").write_text(planted_pdb_text())
        st.pairs = build_pairs(planted_pdb_text())
        write_pair_evidence(st, st.pairs, st.datadir / f"{PDB_ENTRY}.pdb")
        return st

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        st = planted_aux_state(tmp, "one_capped",
                               timeouts=("aux_pair1_simulate",))
        out = stage_aux(st)
        attempted = {call["name"].split("_")[1] for call in st.runner.calls
                     if call["name"].startswith("aux_pair")}
        c.eq("all three pairs are attempted when the first one is capped",
             sorted(attempted), ["pair1", "pair2", "pair3"])
        c.eq("the capped pair is left out of the mean", out["n"], 2)
        c.eq("the auxiliary input is still decided on two pairs",
             st.inputs_status["C3"]["state"], "decided")
        rows = [json.loads(l) for l in
                (st.outdir / f"rows_aux_tag-{TAG}.jsonl").read_text().splitlines()]
        capped = [r for r in rows if r.get("truncated")]
        c.eq("the capped pair is kept as a row", len(capped), 1)
        c.ok("the capped pair's row says it did not finish",
             capped[0].get("incomplete") is True)

        st = planted_aux_state(tmp, "two_capped",
                               timeouts=("aux_pair1_simulate", "aux_pair2_simulate"))
        out = stage_aux(st)
        attempted = {call["name"].split("_")[1] for call in st.runner.calls
                     if call["name"].startswith("aux_pair")}
        c.eq("all three pairs are attempted when two are capped",
             sorted(attempted), ["pair1", "pair2", "pair3"])
        c.eq("one finished pair is below the minimum", out["n"], 1)
        c.eq("below two finished pairs the auxiliary input is void",
             st.inputs_status["C3"]["decision"], "VOID")


def selftest_finalize(c: Checks) -> None:
    """Closing a run after the launcher's timer keeps what was already decided."""
    def planted_out(tmp: Path, name: str, records: dict, validity=None):
        st = make_state(tmp / name, clock=FakeClock(100.0),
                        env={"REMOTE_TIMEOUT": "7200", "M4_T0_EPOCH": "0",
                             "INSTANCE_TYPE": "gpu_1x_a100_sxm4"})
        st.runner = FakeRunner(st)
        for fname, body in records.items():
            atomic_write_json(st.outdir / fname, body)
        if validity is not None:
            atomic_write_json(st.outdir / "RUN_VALID.json", validity)
        return st

    def c3_record(decision="PASS"):
        return {"cell": {"stage": "endpoints", "input": "C3", "tag": TAG},
                "inputs": [], "metric": "aux_h_per_pair", "decision": decision,
                "values": {"measured": 1.0, "unit": CARD["C3"]["unit"],
                           "card_value": 1, "band": CARD["C3"]["band"],
                           "n": 3, "marginal": False, "void_reason": None},
                "threshold": {}, "decision_rule": "inside the band -> PASS",
                "notes_list": [], "run_valid": True, "env": {}, "kind": "C3"}

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        st = planted_out(tmp, "one_decided",
                         {f"endpoint-C3_tag-{TAG}.json": c3_record()})
        before = (st.outdir / f"endpoint-C3_tag-{TAG}.json").read_bytes()
        code = finalize_from_disk(st, outer_rc=124)
        c.eq("a timer that left three inputs unmeasured exits three", code, EXIT_GUARD)
        c.eq("the input decided before the timer keeps its decision",
             st.inputs_status["C3"]["status"], "decided")
        c.eq("its record is not rewritten",
             (st.outdir / f"endpoint-C3_tag-{TAG}.json").read_bytes(), before)
        for cid in ("C1", "C2", "C4"):
            c.eq(f"{cid} says the timer left it unmeasured",
                 st.inputs_status[cid]["status"], "unmeasured_by_stop:outer_timeout")
            rec = json.loads((st.outdir / f"endpoint-{cid}_tag-{TAG}.json").read_text())
            c.ok(f"{cid}'s new record carries the incomplete-run label",
                 LABEL_INCOMPLETE in rec["notes_list"])
            c.eq(f"{cid}'s new record is void", rec["decision"], "VOID")
        c.eq("the run is still valid after a timer stop", st.run_valid, True)
        summary = json.loads((st.outdir / f"{TAG}_summary.json").read_text())
        c.eq("the closing summary says what the run decides",
             list(summary.keys())[0], "what_this_run_decides")
        c.ok("the closing summary says the run is incomplete",
             LABEL_INCOMPLETE in summary["notes"])
        write_run_done(st, code)
        marker = json.loads((st.outdir / "RUN_DONE").read_text())
        c.ok("the closing marker says the run is incomplete",
             LABEL_INCOMPLETE in marker["notes"])
        c.eq("the closing marker carries the exit code", marker["exit_code"],
             EXIT_GUARD)

        anchor_fail = {"cell": {"stage": "anchor", "tag": TAG}, "inputs": [],
                       "metric": "anchor", "decision": "FAIL",
                       "values": {"measured": 0.1}, "threshold": {},
                       "decision_rule": "overlap or RMSD", "notes_list": [],
                       "run_valid": False, "env": {}, "kind": "anchor"}
        st = planted_out(tmp, "anchor_failed",
                         {f"endpoint-anchor_tag-{TAG}.json": anchor_fail})
        c.eq("a missed anchor on disk closes as a missed anchor",
             finalize_from_disk(st, outer_rc=124), EXIT_ANCHOR)
        c.eq("a missed anchor on disk leaves the run invalid", st.run_valid, False)

        all_four = {f"endpoint-C{i}_tag-{TAG}.json":
                    dict(c3_record(), cell={"stage": "endpoints", "input": f"C{i}",
                                            "tag": TAG})
                    for i in (1, 2, 3, 4)}
        st = planted_out(tmp, "all_decided", all_four)
        c.eq("a run with every input decided closes at zero",
             finalize_from_disk(st, outer_rc=124), EXIT_OK)

        st = planted_out(tmp, "invalid",
                         {f"endpoint-C3_tag-{TAG}.json": c3_record()},
                         validity={"run_valid": False, "voided_by": "the sleep check"})
        c.eq("a run already marked invalid closes as broken infrastructure",
             finalize_from_disk(st, outer_rc=124), EXIT_INFRA)

        st = planted_out(tmp, "unmeasured_record", {
            f"endpoint-C3_tag-{TAG}.json": dict(
                c3_record("VOID"),
                values={"measured": None, "unit": CARD["C3"]["unit"],
                        "card_value": 1, "band": CARD["C3"]["band"], "n": 0,
                        "void_reason": f"{LABEL_UNMEASURED} (ceiling)"})})
        code = finalize_from_disk(st, outer_rc=124)
        c.eq("a record that says it was never measured stays unmeasured",
             st.inputs_status["C3"]["status"], "unmeasured_by_stop:outer_timeout")
        c.eq("and the run closes as a stop", code, EXIT_GUARD)


SHELL_STUB = """#!/bin/sh
# A planted stand-in for the measuring program. It records that it was called,
# optionally writes the marker and the validity file the real program writes,
# and returns whatever exit code the planted case asks for.
echo "$@" >> "$M4_STUB_CALLS"
case "$*" in
  *--finalize*)
    echo "finalize" >> "$M4_STUB_FINALIZE_CALLS"
    exit 0 ;;
esac
if [ -n "${M4_STUB_RECORD:-}" ]; then
  mkdir -p "$M4_STUB_OUT"
  printf '%s' "$M4_STUB_RECORD" > "$M4_STUB_RECORD_PATH"
fi
if [ "${M4_STUB_WRITE:-0}" = "1" ]; then
  mkdir -p "$M4_STUB_OUT"
  printf '%s' "$M4_STUB_RUN_DONE" > "$M4_STUB_OUT/RUN_DONE"
  printf '%s' "$M4_STUB_RUN_VALID" > "$M4_STUB_OUT/RUN_VALID.json"
fi
exit "${M4_STUB_RC:-0}"
"""

SUDO_STUB_OK = "#!/bin/sh\nexit 0\n"
SUDO_STUB_SLOW = "#!/bin/sh\nexec sleep 60\n"


def _write_executable(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    os.chmod(str(path), 0o755)
    return path


def _run_onbox(root: Path, *, rc, write=False, run_done="", run_valid="",
               remote_timeout="7200", sudo=SUDO_STUB_OK, install_ceiling=None,
               timeout_s=120, record=None, record_name=None):
    """Run the on-box script itself, under its test hook, with planted answers."""
    script = Path(__file__).with_name(f"onbox_{TAG}.sh")
    bin_dir = root / "testbin"
    _write_executable(bin_dir / "sudo", sudo)
    stub = _write_executable(root / "runner_stub.sh", SHELL_STUB)
    out = root / f"results_{TAG}" / "out"
    env = dict(os.environ)
    env.update({
        "M4_SHELL_TEST": "1",
        "M4_TEST_ROOT": str(root),
        "M4_TEST_RUNNER": f"/bin/sh {stub}",
        "M4_TEST_BIN": str(bin_dir),
        "M4_STUB_CALLS": str(root / "calls.txt"),
        "M4_STUB_FINALIZE_CALLS": str(root / "finalize_calls.txt"),
        "M4_STUB_OUT": str(out),
        "M4_STUB_RC": str(rc),
        "M4_STUB_WRITE": "1" if write else "0",
        "M4_STUB_RUN_DONE": run_done,
        "M4_STUB_RUN_VALID": run_valid,
        "REMOTE_TIMEOUT": remote_timeout,
        "PRICE_USD_PER_HOUR": "1.99",
        "BUDGET_LEFT_USD": "5",
        "INSTANCE_TYPE": "gpu_1x_a100_sxm4",
    })
    if install_ceiling is not None:
        env["M4_TEST_INSTALL_CEILING_S"] = str(install_ceiling)
    if record is not None:
        env["M4_STUB_RECORD"] = record
        env["M4_STUB_RECORD_PATH"] = str(out / (record_name or ""))
    started = time.time()
    proc = subprocess.run(["bash", str(script)], env=env, cwd=str(root),
                          capture_output=True, text=True, timeout=timeout_s)
    return {"rc": proc.returncode, "seconds": time.time() - started, "out": out,
            "stdout": proc.stdout, "stderr": proc.stderr,
            "finalize_calls": (root / "finalize_calls.txt")}


def _read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


def selftest_shell_routes(c: Checks) -> None:
    """The on-box script itself: its test hook, its routes and what it writes.

    This is the one part of the selftest that runs the shell script. Every
    route out of it is planted here, because the exit code and the validity
    file it leaves behind are what the operator reads afterwards.
    """
    script = Path(__file__).with_name(f"onbox_{TAG}.sh")
    if not script.exists():
        c.ok("the on-box script is beside this program", False, str(script))
        return
    text = script.read_text()

    # -- the test hook is one block, and nothing outside it reads a test variable
    begin = "# BEGIN TEST HOOKS"
    end = "# END TEST HOOKS"
    c.ok("the on-box script marks where its test hook begins", begin in text)
    c.ok("the on-box script marks where its test hook ends", end in text)
    if begin in text and end in text:
        lo = text.index(begin)
        hi = text.index(end)
        c.ok("the test hook block is not empty and is the right way round", lo < hi)
        first_line = text[lo + len(begin):hi].strip().splitlines()[0]
        c.ok("the test hook's first line asks whether this is a test",
             "M4_SHELL_TEST" in first_line, first_line)
        outside = [m.start() for m in re.finditer(r"M4_TEST_", text)
                   if not (lo < m.start() < hi)]
        c.eq("no test variable is read outside the test hook block", outside, [])

    # -- no line that starts the measuring program lets a non-zero status escape
    joined = re.sub(r"\\\n\s*", " ", text)
    runner_lines = [ln for ln in joined.splitlines() if "${RUNNER_CMD[@]}" in ln]
    c.ok("the on-box script starts the measuring program", bool(runner_lines))
    unguarded = [ln.strip() for ln in runner_lines if "|| RC=$?" not in ln]
    c.eq("every line that starts the measuring program catches its exit code",
         unguarded, [])
    c.ok("the script never turns on abort-on-error", "\nset -e" not in text)

    if shutil.which("bash") is None:
        c.ok("bash is available to run the on-box script", False,
             "no bash on this machine")
        return

    done_zero = json.dumps({"exit_code": 0, "run_valid": True,
                            "inputs": {k: {"status": "decided"} for k in INPUT_IDS}},
                           indent=2)
    valid_true = json.dumps({"run_valid": True, "voided_by": None}, indent=2)

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)

        # (1) the program finished and left its own marker
        r = _run_onbox(tmp / "ok", rc=0, write=True, run_done=done_zero,
                       run_valid=valid_true)
        c.eq("a finished run exits zero", r["rc"], 0)
        c.eq("the marker the program wrote is left exactly as it was",
             (r["out"] / "RUN_DONE").read_text(), done_zero)
        c.eq("the validity file the program wrote is left exactly as it was",
             (r["out"] / "RUN_VALID.json").read_text(), valid_true)

        # (2) a stop, with the program's own files already written
        done_three = json.dumps({"exit_code": 3, "run_valid": True,
                                 "inputs": {k: {"status":
                                                "unmeasured_by_stop:ceiling"}
                                            for k in INPUT_IDS}}, indent=2)
        r = _run_onbox(tmp / "stop_with_files", rc=3, write=True,
                       run_done=done_three, run_valid=valid_true)
        c.eq("a stop with the program's own files exits three", r["rc"], 3)
        c.eq("the stop's marker is untouched",
             (r["out"] / "RUN_DONE").read_text(), done_three)
        c.eq("the stop's validity file is untouched",
             (r["out"] / "RUN_VALID.json").read_text(), valid_true)

        # (3) a stop with nothing written: the shell writes the void itself
        r = _run_onbox(tmp / "stop_no_files", rc=3)
        c.eq("a stop with no files exits three", r["rc"], 3)
        validity = _read_json(r["out"] / "RUN_VALID.json")
        c.eq("a stop leaves the run valid", (validity or {}).get("run_valid"), True)
        done = _read_json(r["out"] / "RUN_DONE")
        c.eq("the marker carries the stop's exit code", (done or {}).get("exit_code"), 3)
        c.ok("the marker says the run is incomplete",
             LABEL_INCOMPLETE in json.dumps(done))
        for cid in INPUT_IDS:
            rec = _read_json(r["out"] / f"endpoint-{cid}_tag-{TAG}.json")
            c.eq(f"{cid} has a record with the card's unit",
                 (rec or {}).get("values", {}).get("unit"), CARD[cid]["unit"])
            c.eq(f"{cid}'s record carries the card's own value",
                 (rec or {}).get("values", {}).get("card_value"),
                 CARD[cid]["card_value"])
            c.eq(f"{cid}'s record carries the card's band",
                 (rec or {}).get("values", {}).get("band"), CARD[cid]["band"])
            c.eq(f"{cid}'s record is void", (rec or {}).get("decision"), "VOID")
            c.eq(f"{cid}'s record says whether the run is valid",
                 (rec or {}).get("run_valid"), True)
            for key in ("cell", "inputs", "metric", "values", "threshold",
                        "decision_rule", "decision", "env"):
                c.ok(f"{cid}'s record carries its {key}", key in (rec or {}))
        anchor = _read_json(r["out"] / f"endpoint-anchor_tag-{TAG}.json")
        c.eq("the anchor record is void too", (anchor or {}).get("decision"), "VOID")
        summary = _read_json(r["out"] / f"{TAG}_summary.json")
        c.eq("the shell's summary says what the run decides",
             list((summary or {}).keys())[0] if summary else None,
             "what_this_run_decides")
        env_txt = (r["out"] / "env.txt").read_text()
        c.ok("the shell's environment note carries the timeout it saw",
             "REMOTE_TIMEOUT_SEEN=7200" in env_txt)
        c.ok("the shell's environment note carries the bootstrap seconds",
             "PRE_T0_SECONDS=" in env_txt)
        c.ok("the shell's environment note never prints a download token",
             "HF_TOKEN=<not read" in env_txt)

        # (4) the anchor missed
        r = _run_onbox(tmp / "anchor", rc=4)
        c.eq("a missed anchor exits four", r["rc"], 4)
        c.eq("a missed anchor leaves the run invalid",
             (_read_json(r["out"] / "RUN_VALID.json") or {}).get("run_valid"), False)
        done = _read_json(r["out"] / "RUN_DONE")
        c.eq("the marker says the anchor voided every input",
             done["inputs"]["C1"]["status"], "void_by_anchor_miss")

        # (5) broken infrastructure
        r = _run_onbox(tmp / "broken", rc=2)
        c.eq("broken infrastructure exits two", r["rc"], 2)
        c.eq("broken infrastructure leaves the run invalid",
             (_read_json(r["out"] / "RUN_VALID.json") or {}).get("run_valid"), False)

        # (6) a program that returns zero without leaving a marker
        r = _run_onbox(tmp / "silent", rc=0)
        c.eq("a zero with no marker is treated as broken infrastructure", r["rc"], 2)
        c.eq("and the run is invalid",
             (_read_json(r["out"] / "RUN_VALID.json") or {}).get("run_valid"), False)

        # (7) the launcher's own timer fired
        r = _run_onbox(tmp / "timer", rc=124)
        c.eq("the launcher's own timer closes the run as a stop", r["rc"], 3)
        calls = r["finalize_calls"]
        c.eq("the closing call is made exactly once",
             len(calls.read_text().splitlines()) if calls.exists() else 0, 1)
        c.eq("a timer stop leaves the run valid",
             (_read_json(r["out"] / "RUN_VALID.json") or {}).get("run_valid"), True)

        # (8) a kill long before the deadline
        r = _run_onbox(tmp / "killed", rc=137)
        c.eq("a kill well before the deadline is broken infrastructure", r["rc"], 2)
        c.eq("and it leaves the run invalid",
             (_read_json(r["out"] / "RUN_VALID.json") or {}).get("run_valid"), False)

        # (9) no time left at all
        r = _run_onbox(tmp / "no_time", rc=0, remote_timeout="10")
        c.eq("a run with no time left for any measurement exits three", r["rc"], 3)
        c.eq("and it leaves the run valid",
             (_read_json(r["out"] / "RUN_VALID.json") or {}).get("run_valid"), True)
        c.eq("the measuring program is never started",
             (tmp / "no_time" / "calls.txt").exists(), False)

        # (10) a system package call that hangs past the install budget
        r = _run_onbox(tmp / "slow_apt", rc=0, sudo=SUDO_STUB_SLOW,
                       install_ceiling=3, timeout_s=60)
        c.eq("a package call over the install budget is broken infrastructure",
             r["rc"], 2)
        c.ok("and it ends quickly, not at the launcher's own timeout",
             r["seconds"] < 30, f"{r['seconds']:.1f}s")
        c.eq("a void record is left behind",
             (_read_json(r["out"] / "RUN_DONE") or {}).get("exit_code"), 2)
        c.eq("the hung install leaves the run invalid",
             (_read_json(r["out"] / "RUN_VALID.json") or {}).get("run_valid"), False)

        # (11) and (12) an input already decided keeps its decision when the
        # shell writes the void. Only the inputs with no record of their own
        # take the shell's status.
        decided_c3 = json.dumps(
            {"cell": {"stage": "endpoints", "input": "C3", "tag": TAG},
             "inputs": [], "metric": "aux_h_per_pair",
             "values": {"measured": 1.0, "unit": CARD["C3"]["unit"],
                        "card_value": CARD["C3"]["card_value"],
                        "band": CARD["C3"]["band"], "n": 3},
             "threshold": {"band": CARD["C3"]["band"]},
             "decision_rule": "inside the band is PASS", "decision": "PASS",
             "run_valid": True, "env": {"timestamp_utc": "2026-10-21T00:00:00Z"}},
            indent=2)
        record_name = f"endpoint-C3_tag-{TAG}.json"

        r = _run_onbox(tmp / "decided_fail", rc=2, record=decided_c3,
                       record_name=record_name)
        c.eq("broken infrastructure after one decided input still exits two",
             r["rc"], 2)
        c.eq("and the run is invalid",
             (_read_json(r["out"] / "RUN_VALID.json") or {}).get("run_valid"), False)
        c.eq("the decided input's record is left exactly as it was",
             (r["out"] / record_name).read_text(), decided_c3)
        done = _read_json(r["out"] / "RUN_DONE")
        c.eq("the decided input stays decided in the marker",
             done["inputs"]["C3"]["status"], "decided")
        c.eq("the decided input keeps its decision in the marker",
             done["inputs"]["C3"]["decision"], "PASS")
        c.eq("an input with no record of its own is void by failure",
             done["inputs"]["C1"]["status"], "void_by_failure:runner_exit_2")
        validity = _read_json(r["out"] / "RUN_VALID.json")
        c.eq("the validity file keeps the decided input decided",
             validity["inputs_status"]["C3"]["status"], "decided")
        c.eq("the validity file voids the inputs with no record",
             [validity["inputs_status"][k]["status"] for k in ("C2", "C4")],
             ["void_by_failure:runner_exit_2"] * 2)
        summary = _read_json(r["out"] / f"{TAG}_summary.json")
        c.eq("the summary the shell writes keeps the decided input decided",
             summary["inputs_status"]["C3"]["status"], "decided")

        r = _run_onbox(tmp / "decided_stop", rc=3, record=decided_c3,
                       record_name=record_name)
        c.eq("a stop after one decided input exits three", r["rc"], 3)
        c.eq("and the run stays valid",
             (_read_json(r["out"] / "RUN_VALID.json") or {}).get("run_valid"), True)
        c.eq("the decided input's record survives the stop untouched",
             (r["out"] / record_name).read_text(), decided_c3)
        done = _read_json(r["out"] / "RUN_DONE")
        c.eq("the decided input stays decided after a stop",
             done["inputs"]["C3"]["status"], "decided")
        c.eq("the inputs with no record are unmeasured after a stop",
             [done["inputs"][k]["status"] for k in ("C1", "C2", "C4")],
             ["unmeasured_by_stop:outer_timeout"] * 3)


def selftest_consistency(c: Checks) -> None:
    """The run's own numbers must agree with each other.

    If two requirements of the design contradict, the selftest fails on the
    contradiction rather than quietly picking one of them.
    """
    c.eq("the card's bands are the ones in the design record",
         [CARD[k]["band"] for k in INPUT_IDS],
         [[0.2, 1.25], [51.6, 322.5], [0.3333, 3], [66.67, 600]])
    c.eq("the card's values are the ones in the design record",
         [CARD[k]["card_value"] for k in INPUT_IDS], [0.5, 129, 1, 200])
    c.eq("the prediction band is the card's value 2.5 times either way",
         [round(0.5 / 2.5, 4), round(0.5 * 2.5, 4)], [0.2, 1.25])
    c.eq("the dynamics band is the card's value 2.5 times either way",
         [round(129 / 2.5, 4), round(129 * 2.5, 4)], [51.6, 322.5])
    c.eq("the auxiliary band is the card's value 3 times either way",
         [round(1 / 3.0, 4), 1 * 3], [0.3333, 3])
    c.eq("the storage band is the card's value 3 times either way",
         [round(200 / 3.0, 2), 200 * 3], [66.67, 600])
    c.eq("the gate is the card's own", GATE_EXPRESSION, "af2_h_per_run <= 1")
    c.eq("the per-pair docking cap is the one the design names",
         PER_PAIR_DOCKING_CEILING_S, 250)
    c.eq("the docking stage total is the one the design names",
         STAGE_CEILING_S["aux"], 600)
    c.ok("three pairs at the per-pair cap cannot all fit, so the stage total binds",
         PER_PAIR_DOCKING_CEILING_S * N_PAIRS > STAGE_CEILING_S["aux"])
    c.eq("the per-complex cap times three is inside the dynamics ceiling",
         PER_COMPLEX_MD_CEILING_S * N_PAIRS > STAGE_CEILING_S["md"], True)
    c.eq("the production segment is half a nanosecond at a two femtosecond step",
         int(round(MD_PRODUCTION_NS * 1e6 / MD_TIMESTEP_FS)), 250000)
    c.eq("there are nine timing runs planned", N_PAIRS * len(AF2_SEEDS), 9)
    c.eq("the default budget never exceeds five dollars",
         DEFAULT_BUDGET_LEFT_USD, 5.0)
    c.eq("the default timeout never exceeds 7,200 seconds",
         DEFAULT_REMOTE_TIMEOUT_S, 7200)
    c.eq("only the sources the design names may be downloaded",
         sorted(ALLOWED_DOWNLOAD_HOSTS), ["files.rcsb.org", "storage.googleapis.com"])
    for url in (PDB_URL, AF_PARAMS_URL):
        host = url.split("/")[2]
        c.ok(f"{host} is an allowed source", host in ALLOWED_DOWNLOAD_HOSTS)
    c.ok("no package is installed without a pinned version",
         all("==" in p for p in PIP_PINS))
    c.ok("the package manager is asked for the virtual environment package",
         "python3-venv" in APT_PACKAGES)
    source = Path(__file__).read_text()
    upgrade_pip = "--upgrade" + " pip"
    c.ok("nothing in this program upgrades pip",
         source.count(upgrade_pip) == 1)          # only this check names it
    c.ok("nothing in this program reads the key store",
         not re.search(r"[\"'/]\.keys\b", source))
    dump_names = ["print" + "env", "env" + " -0", "set" + " -x"]
    c.ok("nothing in this program dumps the environment",
         all(source.count(n) <= 1 for n in dump_names))   # only this check names them
    dump_names = ["print" + "env", "env" + " -0", "set" + " -x"]
    onbox = Path(__file__).with_name(f"onbox_{TAG}.sh")
    if onbox.exists():
        text = onbox.read_text()
        c.ok("the on-box script unsets the download token",
             "unset HF_TOKEN" in text)
        c.ok("the on-box script declares its system packages",
             "python3-venv" in text)

        # The system packages are declared in one place in the shell's own text,
        # and this program records exactly those. Five, no more and no fewer:
        # the last two compile the docking code, which ships no ready-built
        # package for this python.
        def declared_apt(shell_text):
            m = re.search(r'APT_PACKAGES="([^"]*)"', shell_text)
            return m.group(1).split() if m else []

        five = ["python3-venv", "aria2", "curl", "build-essential", "python3-dev"]
        c.eq("the on-box script declares exactly the five system packages",
             declared_apt(text), five)
        c.eq("this program records the same five system packages",
             APT_PACKAGES, five)
        c.ok("a sixth system package in the shell's list fails the check",
             declared_apt('APT_PACKAGES="python3-venv aria2 curl build-essential '
                          'python3-dev gcc"') != five)
        c.ok("a missing system package in the shell's list fails the check",
             declared_apt('APT_PACKAGES="python3-venv aria2 curl '
                          'build-essential"') != five)
        c.eq("the shell installs the declared list in one call and nothing else",
             [ln.strip() for ln in text.splitlines()
              if ln.strip().startswith("apt-get install")],
             ["apt-get install -y -qq $APT_PACKAGES >>\"$LOG\" 2>&1 || rc=$?"])
        c.ok("the on-box script never upgrades pip", "--upgrade pip" not in text)
        c.ok("the on-box script reads the forwarded timeout",
             "REMOTE_TIMEOUT" in text)
        c.ok("the on-box script sets its exit trap before building the environment",
             text.index("trap ") < text.index("-m venv"))
        c.ok("the on-box script never dumps the environment",
             all(n not in text for n in dump_names))


def selftest() -> int:
    """Run every planted case and report the tally, the file hashes and the verdict."""
    c = Checks()
    started = time.time()
    for part in (selftest_consistency, selftest_parsers, selftest_bytes_and_storage,
                 selftest_bands, selftest_harness_rules, selftest_cost_and_time,
                 selftest_anchor, selftest_environment, selftest_process_groups,
                 selftest_outer_timeout, selftest_guards, selftest_pairs,
                 selftest_dynamics_inputs, selftest_records, selftest_stage_flow,
                 selftest_docking_routes, selftest_install_ceiling,
                 selftest_label_keys, selftest_pip_pins,
                 selftest_parameter_markers, selftest_storage_details,
                 selftest_allowances, selftest_spend, selftest_docking_order,
                 selftest_docking_pair_loop, selftest_finalize,
                 selftest_shell_routes, selftest_real_stage_bodies):
        try:
            part(c)
        except Exception as exc:                       # a crash is a failed check
            import traceback
            c.ok(f"the group {part.__name__} ran to the end", False,
                 f"{type(exc).__name__}: {exc}\n"
                 + "".join(traceback.format_exc().splitlines(True)[-4:]))

    for failure in c.failed:
        print(f"FAIL {failure}")
    print(f"selftest: {c.passed} of {c.total} checks passed")

    me = Path(__file__).resolve()
    onbox = me.with_name(f"onbox_{TAG}.sh")
    onbox_hash = sha256_file(onbox) if onbox.exists() else "missing"
    print(f"selftest: files sha256 run_{TAG}.py {sha256_file(me)} "
          f"onbox_{TAG}.sh {onbox_hash}")
    print(f"selftest: elapsed {time.time() - started:.1f}s")
    print("selftest: " + ("PASS" if not c.failed else "FAIL"))
    return 0 if not c.failed else 1


if __name__ == "__main__":
    sys.exit(main())
