#!/usr/bin/env python3
"""Measure four cost inputs of one research plan on one rented GPU box.

WHAT THIS IS. A research plan (the "card") prices a protein-structure study.
Its price rests on four numbers nobody measured. This program measures them
once, on one rented machine, and reads each against the band the plan itself
allows. The plan's own study is not run.

THE FOUR INPUTS, in the plan's own units:

  C1  af2_h_per_run        hours of one AlphaFold-Multimer prediction call
  C2  md_ns_per_day_a100   simulated nanoseconds per day of molecular dynamics
  C3  aux_h_per_pair       hours per pair of everything that is neither of those
  C4  n_storage_gib        gibibytes written by the plan's 216-run grid

Each has a stated value and a band. A measured number inside the band is PASS,
outside is FAIL, within 10 percent of a band edge is VOID and marked marginal.
The plan also states a gate on C1 alone: at most 1 hour per run. The gate is
reported. This program never branches on it.

THE ANCHOR COMES FIRST. Before any input is measured, the program redocks a
receptor fragment onto a virus capsid fragment and compares the result with the
published structure (Protein Data Bank entry 6IHB). If that redocking misses,
every input record is written VOID and the whole run is marked not valid.

STAND-IN WORK, NOT THE PLAN'S WORK. The pairs measured here are built from
chains of that one published entry. They are not the plan's own pairs. Serial
and parallel runs here are repeats on one machine; they are not independent
checks of each other, and nothing here is a second laboratory's confirmation.

HOW TO RUN

  python3 run_m4.py --selftest                 # standard library only, no GPU, no network
  python3 run_m4.py --stage extract            # downloads, controls, anchor
  python3 run_m4.py --stage generate           # docking, AlphaFold, dynamics, storage
  python3 run_m4.py --stage endpoints          # the four decisions and the summary

Each stage reads its own saved state and can run on its own, in that order.

WHAT IT WRITES, under results_m4/out/ beside this file

  endpoint-anchor_tag-m4.json      the redocking check
  endpoint-C1_tag-m4.json ...C4    one record per input
  endpoint-control-*.json          the planted-sleep, empty-run and unit checks
  rows_<arm>_tag-m4.jsonl          one line per timed run, docking, segment, byte count
  RUN_VALID.json                   whether the run is valid, and why not
  m4_summary.json                  every record restated, with no new decision
  RUN_DONE                         the exit code
  logs/                            every tool's output, saved whole

EXIT CODES
  0 finished   2 broken machine or broken harness   3 cost or time guard stop   4 anchor miss

TWO KINDS OF BAD ENDING, KEPT APART. A broken install, download, start check or
tool is the machine failing: the run is marked not valid and every input is
written as not decided. Running out of clock or money is not: the inputs that
finished keep their decisions, the rest are written as not decided and carry
the words "incomplete run", the run stays valid, and the code is 3.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Fixed numbers. Every one of these comes from the design record or the
# execution directive. None of them is computed here, and none is adjustable.
# ---------------------------------------------------------------------------

TAG = "m4"
SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS = SCRIPT_DIR / "results_m4" / "out"
LOGS = RESULTS / "logs"
WORK = SCRIPT_DIR / "work_m4"
STATE_PATH = RESULTS / "state_m4.json"

# The plan's own stated value and allowed band for each input.
CARD = {
    "C1": {"name": "af2_h_per_run", "value": 0.5, "band": [0.2, 1.25], "unit": "hours per run"},
    "C2": {"name": "md_ns_per_day_a100", "value": 129, "band": [51.6, 322.5], "unit": "nanoseconds per day"},
    "C3": {"name": "aux_h_per_pair", "value": 1, "band": [0.3333, 3], "unit": "hours per pair"},
    "C4": {"name": "n_storage_gib", "value": 200, "band": [66.67, 600], "unit": "gibibytes"},
}
GATE_INPUT = "C1"
GATE_VALUE = 1
GATE_ELSE = ("take the docking-plus-MD fallback line with one AlphaFold-Multimer seed per pair, "
             "or move the grid to 12 pairs")
GATE_NOT_APPLICABLE = "not applicable: the card's gate is on af2_h_per_run"
GATE_NONE = "none: the card names no gate on n_storage_gib"

MARGINAL_FRACTION = 0.10          # a value this close to a band edge is not decided
SLEEP_SECONDS = 60.0              # the planted sleep the timer must reproduce
SLEEP_TOLERANCE = 0.05            # at most 5 percent error
EMPTY_MAX_SECONDS = 2.0           # an empty run must take less than this
EMPTY_MAX_BYTES = 1024 * 1024     # and write less than this
SPREAD_HIGH = 0.50                # relative spread above this gets a warning label

N_PAIRS = 3                       # three stand-in pairs, one per capsid slot
AF_SEEDS = [0, 1, 2]
PAIR_TARGET_LENGTHS = [780, 875, 970]   # spread over the required 750 to 1000 residues
PAIR_MIN_RESIDUES = 750
PAIR_MAX_RESIDUES = 1000

AF_MODELS = 5
AF_RECYCLES = 20
AF_EARLY_STOP_TOLERANCE = 0.0     # zero turns early stopping off: all 20 recycles run

MD_TIMESTEP_FS = 2.0
MD_PRODUCTION_NS = 0.5
MD_PRODUCTION_STEPS = int(round(MD_PRODUCTION_NS * 1e6 / MD_TIMESTEP_FS))   # 250000
MD_EQUIL_STEPS = 5000             # a short settling run, not timed as production
MD_MINIMISE_STEPS = 500
MD_REPORT_INTERVAL = 5000         # frames and log lines every 10 picoseconds
MD_ATOMS_MIN = 120000
MD_ATOMS_MAX = 180000
MD_PADDINGS_NM = [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 2.0]
MD_RATE_DISAGREE = 0.05           # above this the two speed readings are both reported and labelled

GRID_RUNS = 216                   # the plan's main grid
GRID_RUNS_ALT = 432               # the other reading of the same grid, reported as information
GIB = float(1 << 30)

CONTACT_CUTOFF_A = 4.5            # heavy-atom contact distance, the published cutoff
ANCHOR_OVERLAP_MIN = 0.50
ANCHOR_RMSD_MAX = 5.0
ANCHOR_SERIAL_PARALLEL_RMSD_MAX = 2.0
BIND_CALL_MIN_CONTACTS = 10       # our reading: this many residue contact pairs means "bind"

# Minimum work below which an input is not decided.
MINIMUMS = {
    "C1": "at least 3 completed AlphaFold runs covering all 3 pairs",
    "C2": "at least 2 complexes",
    "C3": "at least 2 pairs",
    "C4": "at least one measured run of each artifact type",
}

# Stage ceilings in seconds, and the whole-run cap. From the gate checklist.
# 1800 + 700 + 600 + 2000 + 1600 + 100 + 400 of margin = 7200.
CEILINGS = {
    "install": 1800,
    "controls_anchor": 700,
    "aux": 600,
    "af2": 2000,
    "md": 1600,
    "endpoints": 100,
}
AUX_PER_PAIR_CEILING = 250
MD_PER_COMPLEX_CEILING = 600
MARGIN_SECONDS = 400
TOTAL_CAP_SECONDS = 7200

# How long a tool inside a stage may run, counted back from the moment the money or
# the clock cap is reached. The on-box script kills the whole run 600 seconds before
# that moment, so this inner cap of 700 seconds always fires first, by 100 seconds.
OUTER_KILL_RESERVE_SECONDS = 600
INNER_TOOL_RESERVE_SECONDS = 700

DEFAULT_PRICE = 1.99
MAX_BUDGET_PER_LAUNCH = 5.0
MAX_TIMEOUT = 7200

EXIT_OK = 0
EXIT_INFRA = 2
EXIT_GUARD = 3
EXIT_ANCHOR = 4

# Allowed download sources. Nothing else may be fetched.
URL_STRUCTURE = "https://files.rcsb.org/download/6IHB.cif"
URL_AF_PARAMS = "https://storage.googleapis.com/alphafold/alphafold_params_colab_2022-12-06.tar"

PDB_ENTRY = "6IHB"

# Labels every measured input record carries, in plain words.
LABEL_STANDIN = "stand-in pairs built from 6IHB chains, not the card's pairs"
LABEL_ONE_BOX = "one GPU; one box; 3 pairs; no multi-GPU scaling"
LABEL_C1_MSA = "no-MSA: alignment search time excluded; understates the card's setting"
LABEL_C3_READING = "producer's reading of aux hours"
LABEL_C4_SCALE = "linear in runs; intermediates kept; MD length 0.5 ns"
LABEL_NOT_A100 = "not an A100"
LABEL_OVERHEAD = "setup overhead subtracted"
LABEL_SPREAD_HIGH = "seed spread high; mean is uncertain"
LABEL_ZERO_SPREAD = "zero spread across seeds: wrong variance source"
LABEL_MD_DISAGREE = "engine rate and wall-clock disagree"
LABEL_UNMEASURED = "unmeasured, not holding"
LABEL_INCOMPLETE_RUN = "incomplete run: unmeasured inputs are VOID, not holding"
LABEL_SP_WHOLE_CHAIN = ("the serial-versus-parallel distance is over the whole receptor chain, "
                        "not over the interface only")
LABEL_TIMEOUT_NOT_FORWARDED = "REMOTE_TIMEOUT not forwarded; default 7200 used"
WRONG_VARIANCE_SOURCE = "WRONG_VARIANCE_SOURCE"

# Chain roles. Contacts are keyed by what a chain is, never by the letter a file
# happens to give it, so a receptor written as "A", "B" or "C" compares the same.
ROLE_CAPSID = "capsid"
ROLE_RECEPTOR = "receptor"
CHAIN_ID_CAPSID = "A"      # the letter the capsid half gets in every file we write
CHAIN_ID_RECEPTOR = "B"    # the letter the receptor half gets in every file we write

# Secrets that must never reach a child process. Downloads use no token at all.
SECRET_ENV_NAMES = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN")

# Decision rules. Each is written here, before any value is known.
RULE_INPUT = (
    "Read the measured number against the card's own band. Inside the band is PASS. Outside is FAIL. "
    "Within 10 percent of either band edge is VOID and marked marginal. VOID also when: the run is not "
    "valid, the input was never measured, fewer runs finished than the stated minimum, the seed-to-seed "
    "spread is exactly zero, or (for C1 and C2 only) the GPU is not an A100. The card's gate on "
    "af2_h_per_run is reported beside C1 and never decides anything."
)
RULE_ANCHOR = (
    "Pass when the redocked pose reproduces the published interface: contact overlap at the 4.5 Angstrom "
    "cutoff at least 0.50, or interface backbone RMSD at most 5.0 Angstrom. That distance is taken over "
    "the backbone atoms (N, CA, C, O) of the receptor residues that touch the capsid in the published "
    "entry, in the capsid's own frame, with no refitting. Pass also requires the serial "
    "and the parallel top pose to agree: RMSD at most 2.0 Angstrom and the same bind or no-bind call. "
    "Anything else is a miss, which voids all four inputs and marks the run not valid."
)
RULE_SLEEP = (
    "Time a planted sleep of 60 seconds through the same timer the inputs use. Pass when the error is at "
    "most 5 percent. A larger error means the timer is wrong, so the run is marked not valid and stops."
)
RULE_EMPTY = (
    "Run the harness over empty input. Pass when it takes under 2 seconds and writes under 1 mebibyte. "
    "Otherwise subtract the excess from later values and label every later record."
)
RULE_UNITS = (
    "Print the raw readings beside the converted numbers, before any band is compared: raw AlphaFold "
    "seconds, each dynamics engine rate line beside the wall-clock nanoseconds per day, and raw bytes per "
    "artifact. This record has no pass or fail; it exists so the unit and scale choices can be rechecked."
)

ARTIFACT_TYPES = ["alphafold_run", "docking_pair", "md_segment"]
INTERMEDIATE_HINTS = ("unrelaxed", "_env", ".pickle", ".pkl", "swarm", "gso_", "init_",
                      "checkpoint", "equil", "_tmp", "tmp_", ".npz")


class ToolError(Exception):
    """A declared tool, install or download failed. Never patched around."""


class GuardStop(Exception):
    """The cost or time guard refused to start more work."""


class AnchorMiss(Exception):
    """The redocking did not reproduce the published interface."""


class HarnessInvalid(Exception):
    """A control that proves the harness itself failed."""


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def now() -> float:
    return time.time()


def utc(ts: float = None) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts if ts is not None else now()))


def hours(seconds: float) -> float:
    """Seconds to hours. 1800 seconds is 0.5 hours."""
    return seconds / 3600.0


def mean(xs):
    return sum(xs) / float(len(xs)) if xs else None


def median(xs):
    return statistics.median(xs) if xs else None


def rel_sd(xs) -> float:
    """Spread of repeats divided by their mean. Zero means the repeats are identical."""
    if not xs or len(xs) < 2:
        return 0.0
    m = mean(xs)
    if m == 0:
        return 0.0
    return statistics.stdev(xs) / abs(m)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def apparent_bytes(paths) -> int:
    """Bytes a reader would see. Files of 1000 and 24 bytes sum to 1024."""
    total = 0
    for p in paths:
        p = Path(p)
        if p.is_file():
            total += p.stat().st_size
        elif p.is_dir():
            for sub in p.rglob("*"):
                if sub.is_file():
                    total += sub.stat().st_size
    return total


def split_final_and_intermediate(root: Path):
    """Bytes kept if intermediates are deleted, and bytes of intermediates."""
    final_b = 0
    inter_b = 0
    for sub in Path(root).rglob("*"):
        if not sub.is_file():
            continue
        name = sub.name.lower()
        # Only the part below the directory being measured counts. The name of
        # the directory itself says nothing about what is inside it.
        rel = str(sub.relative_to(Path(root))).lower()
        is_inter = any(h in name or h in rel for h in INTERMEDIATE_HINTS)
        if is_inter:
            inter_b += sub.stat().st_size
        else:
            final_b += sub.stat().st_size
    return final_b, inter_b


def jdump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True))


def append_row(arm: str, row: dict, results: Path = None) -> None:
    """One raw line per timed run, docking, segment or byte count. Never summarised away."""
    results = results or RESULTS
    results.mkdir(parents=True, exist_ok=True)
    path = results / "rows_%s_tag-%s.jsonl" % (arm, TAG)
    row = dict(row)
    row.setdefault("written_utc", utc())
    with open(path, "a") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")


# ---------------------------------------------------------------------------
# Parsers. Each one is pure: text in, numbers out, so the selftest can plant
# input with a known answer.
# ---------------------------------------------------------------------------

def parse_nvidia_smi(text: str) -> dict:
    """Read GPU name and driver from `nvidia-smi --query-gpu=name,driver_version`."""
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("name"):
            continue
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2:
            return {"gpu_name": parts[0], "driver_version": parts[1]}
    return {"gpu_name": None, "driver_version": None}


def gpu_is_a100(gpu_name) -> bool:
    return bool(gpu_name) and "a100" in str(gpu_name).lower()


def parse_cuda_version(text: str):
    """Read the CUDA runtime version out of `nvcc --version` or nvidia-smi text."""
    m = re.search(r"release\s+(\d+\.\d+)", text)
    if m:
        return m.group(1)
    m = re.search(r"CUDA Version:\s*(\d+\.\d+)", text)
    return m.group(1) if m else None


def parse_engine_rate_lines(text: str):
    """Read every speed value from a dynamics engine log.

    The engine writes comma separated columns with a header naming
    `Speed (ns/day)`. Returns the speeds in order, oldest first.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    idx = None
    out = []
    for ln in lines:
        if "Speed" in ln and "ns/day" in ln:
            header = [c.strip().strip('"').strip("#").strip('"') for c in ln.lstrip("#").split(",")]
            for i, col in enumerate(header):
                if "speed" in col.lower():
                    idx = i
                    break
            continue
        if idx is None:
            continue
        cells = [c.strip().strip('"') for c in ln.split(",")]
        if len(cells) <= idx:
            continue
        try:
            out.append(float(cells[idx]))
        except ValueError:
            continue
    return out


def ns_per_day_from_wallclock(steps: int, timestep_fs: float, wall_seconds: float):
    """Speed from first principles: how much simulated time per day of real time.

    250000 steps of 2 femtoseconds in 335 seconds is 128.96 nanoseconds per day.
    """
    if wall_seconds is None or wall_seconds <= 0:
        return None
    simulated_ns = steps * timestep_fs / 1e6
    return simulated_ns / wall_seconds * 86400.0


def parse_af_model_times(text: str):
    """Read per-model times from an AlphaFold run log.

    The log writes one `... model_<k>_... took <seconds>s` line per model.
    Returns a list of (model number, seconds) in log order.
    """
    out = []
    for m in re.finditer(r"model_(\d+)\S*\s+took\s+([0-9]+(?:\.[0-9]+)?)s", text):
        out.append((int(m.group(1)), float(m.group(2))))
    return out


def compile_excluded_seconds(model_times):
    """Total prediction seconds with the first model's one-off compilation removed.

    The first model pays for compiling the maths kernels. We replace its time
    with the mean of the later models and keep the rest as measured. With model
    times 300, 60, 62, 58, 60 this gives 300.0 seconds instead of 540.0.
    """
    if len(model_times) < 2:
        return None
    later = [t for _, t in model_times[1:]]
    return mean(later) + sum(later)


def parse_pip_report(text: str):
    """Read what pip actually installed, from the report it writes with --report.

    Returns one entry per package: name, version, the address it came from and
    the hash of the archive. This is the record of where the code came from.
    """
    try:
        report = json.loads(text)
    except ValueError:
        return []
    out = []
    for item in report.get("install", []):
        meta = item.get("metadata") or {}
        dl = item.get("download_info") or {}
        archive = (dl.get("archive_info") or {})
        digests = archive.get("hashes") or {}
        out.append({"name": meta.get("name"), "version": meta.get("version"),
                    "url": dl.get("url"),
                    "sha256": digests.get("sha256") or archive.get("hash")})
    return out


def parse_apt_versions(text: str):
    """Read package name, version and hash from the lines the install step saved."""
    out = []
    for ln in text.splitlines():
        parts = [p.strip() for p in ln.split("|")]
        if len(parts) >= 3 and parts[0]:
            out.append({"name": parts[0], "version": parts[1], "sha256": parts[2]})
    return out


def parse_docking_rank_table(text: str):
    """Read a docking ranking table: whitespace columns, last numeric column is the score.

    Returns a list of dicts with the swarm, the pose number and the score,
    best score first.
    """
    rows = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or ln.lower().startswith(("swarm", "#")):
            continue
        parts = ln.split()
        nums = []
        for p in parts:
            try:
                nums.append(float(p))
            except ValueError:
                nums.append(None)
        if len(parts) < 3 or nums[0] is None or nums[-1] is None:
            continue
        rows.append({"swarm": int(nums[0]), "pose": int(nums[1]) if nums[1] is not None else None,
                     "score": nums[-1]})
    rows.sort(key=lambda r: -r["score"])
    return rows


# ---------------------------------------------------------------------------
# Structure reading. Pure standard library, so the geometry is testable with
# no third-party package installed.
# ---------------------------------------------------------------------------

THREE_TO_ONE = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C", "GLN": "Q", "GLU": "E",
    "GLY": "G", "HIS": "H", "ILE": "I", "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F",
    "PRO": "P", "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
}
BACKBONE = ("N", "CA", "C", "O")


def cif_tokens(line: str):
    """Split one line of a structure file, keeping quoted names such as "O5'" whole."""
    toks = []
    i, n = 0, len(line)
    while i < n:
        c = line[i]
        if c in " \t":
            i += 1
            continue
        if c in "'\"":
            q = c
            i += 1
            start = i
            while i < n and not (line[i] == q and (i + 1 >= n or line[i + 1] in " \t")):
                i += 1
            toks.append(line[start:i])
            i += 1
        else:
            start = i
            while i < n and line[i] not in " \t":
                i += 1
            toks.append(line[start:i])
    return toks


def parse_cif_atoms(text: str):
    """Read protein atoms from a structure file in the crystallographic text format.

    Keeps the first model and the first alternate position only. Returns a list
    of atom dicts: chain, residue number, residue name, atom name, element, x, y, z.
    """
    atoms = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip() != "loop_":
            i += 1
            continue
        j = i + 1
        headers = []
        while j < len(lines) and lines[j].strip().startswith("_"):
            headers.append(lines[j].strip())
            j += 1
        if not headers or not headers[0].startswith("_atom_site."):
            i = j
            continue
        cols = {h.strip().split(".", 1)[1]: k for k, h in enumerate(headers)}
        need = ("group_PDB", "label_atom_id", "label_comp_id", "Cartn_x", "Cartn_y", "Cartn_z")
        if any(c not in cols for c in need):
            i = j
            continue
        chain_col = cols.get("auth_asym_id", cols.get("label_asym_id"))
        seq_col = cols.get("auth_seq_id", cols.get("label_seq_id"))
        alt_col = cols.get("label_alt_id")
        model_col = cols.get("pdbx_PDB_model_num")
        elem_col = cols.get("type_symbol")
        k = j
        while k < len(lines):
            raw = lines[k]
            s = raw.strip()
            if not s or s.startswith("#") or s.startswith("_") or s == "loop_":
                break
            toks = cif_tokens(raw)
            if len(toks) < len(headers):
                k += 1
                continue
            if toks[cols["group_PDB"]] != "ATOM":
                k += 1
                continue
            if model_col is not None and toks[model_col] not in (".", "?", "1"):
                k += 1
                continue
            if alt_col is not None and toks[alt_col] not in (".", "?", "A"):
                k += 1
                continue
            resn = toks[cols["label_comp_id"]]
            if resn not in THREE_TO_ONE:
                k += 1
                continue
            try:
                atoms.append({
                    "chain": toks[chain_col] if chain_col is not None else "A",
                    "resseq": int(toks[seq_col]) if seq_col is not None else 0,
                    "resname": resn,
                    "atom": toks[cols["label_atom_id"]],
                    "element": toks[elem_col] if elem_col is not None else toks[cols["label_atom_id"]][0],
                    "x": float(toks[cols["Cartn_x"]]),
                    "y": float(toks[cols["Cartn_y"]]),
                    "z": float(toks[cols["Cartn_z"]]),
                })
            except (ValueError, IndexError):
                pass
            k += 1
        i = k
    return atoms


def chains_from_atoms(atoms):
    """Group atoms by chain, in the order the chains first appear."""
    out = {}
    for a in atoms:
        out.setdefault(a["chain"], []).append(a)
    return out


def chain_sequence(chain_atoms):
    """One-letter sequence of a chain, read from its alpha carbons in order."""
    seen = []
    done = set()
    for a in chain_atoms:
        if a["atom"] != "CA":
            continue
        key = a["resseq"]
        if key in done:
            continue
        done.add(key)
        seen.append(THREE_TO_ONE.get(a["resname"], "X"))
    return "".join(seen)


def heavy_atoms(atoms):
    return [a for a in atoms if (a.get("element") or "C").upper() != "H"]


def residue_key(a):
    return (a["chain"], a["resseq"])


def contact_pairs(atoms_a, atoms_b, cutoff=CONTACT_CUTOFF_A):
    """Residue pairs with at least one heavy-atom pair within the cutoff.

    Uses a grid of cutoff-sized boxes so large structures stay quick.
    """
    a_h = heavy_atoms(atoms_a)
    b_h = heavy_atoms(atoms_b)
    if not a_h or not b_h:
        return set()
    cell = cutoff
    grid = {}
    for a in a_h:
        key = (int(math.floor(a["x"] / cell)), int(math.floor(a["y"] / cell)),
               int(math.floor(a["z"] / cell)))
        grid.setdefault(key, []).append(a)
    cut2 = cutoff * cutoff
    pairs = set()
    for b in b_h:
        bx = int(math.floor(b["x"] / cell))
        by = int(math.floor(b["y"] / cell))
        bz = int(math.floor(b["z"] / cell))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for a in grid.get((bx + dx, by + dy, bz + dz), ()):
                        d2 = ((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2 +
                              (a["z"] - b["z"]) ** 2)
                        if d2 <= cut2:
                            pairs.add((residue_key(a), residue_key(b)))
    return pairs


def as_role(atoms, role):
    """Relabel a set of atoms by what the chain is, not by the letter in the file.

    The published entry calls the receptor chain one thing and a docking tool
    calls it another. Keying contacts by the letter would then compare two key
    sets that can never meet. Every comparison here goes through this function
    first, so the same pose scores the same whatever letter it carries.
    """
    out = []
    for a in atoms:
        b = dict(a)
        b["chain"] = role
        out.append(b)
    return out


def interface_residues(reference_capsid, reference_receptor, cutoff=CONTACT_CUTOFF_A):
    """Residue numbers of the receptor residues that touch the capsid in the reference.

    These are the residues the published interface is made of: any heavy atom
    within the cutoff of the capsid.
    """
    pairs = contact_pairs(as_role(reference_capsid, ROLE_CAPSID),
                          as_role(reference_receptor, ROLE_RECEPTOR), cutoff)
    return sorted(set(resseq for (_, resseq) in (p[1] for p in pairs)))


def interface_backbone_rmsd(reference_receptor, pose_receptor, resseqs):
    """Distance between reference and pose over the published interface only.

    Backbone atoms (N, CA, C, O) of the named receptor residues, matched by
    residue number and atom name, in the capsid's own frame, with no refitting.
    Moving receptor atoms that are not at the interface does not change it.
    """
    want = set(resseqs)

    def table(atoms):
        out = {}
        for a in atoms:
            if a["atom"] in BACKBONE and a["resseq"] in want:
                out[(a["resseq"], a["atom"])] = (a["x"], a["y"], a["z"])
        return out

    ref, pose = table(reference_receptor), table(pose_receptor)
    keys = sorted(set(ref) & set(pose))
    if not keys:
        return None
    return rmsd_direct([ref[k] for k in keys], [pose[k] for k in keys])


def contact_overlap(native_pairs, pose_pairs) -> float:
    """Fraction of the published contacts the pose makes. 3 of 6 gives 0.5."""
    native = set(native_pairs)
    if not native:
        return 0.0
    return len(native & set(pose_pairs)) / float(len(native))


def rmsd_direct(coords_a, coords_b):
    """Root-mean-square distance between matched atoms, with no refitting.

    A rigid 5 Angstrom shift along one axis gives exactly 5.0.
    """
    if not coords_a or len(coords_a) != len(coords_b):
        return None
    total = 0.0
    for (x1, y1, z1), (x2, y2, z2) in zip(coords_a, coords_b):
        total += (x1 - x2) ** 2 + (y1 - y2) ** 2 + (z1 - z2) ** 2
    return math.sqrt(total / len(coords_a))


def backbone_coords(atoms):
    out = []
    for a in atoms:
        if a["atom"] in BACKBONE:
            out.append((a["x"], a["y"], a["z"]))
    return out


def centroid(points):
    if not points:
        return None
    n = float(len(points))
    return (sum(p[0] for p in points) / n, sum(p[1] for p in points) / n,
            sum(p[2] for p in points) / n)


def threefold_axis(chain_centroids):
    """The local three-fold symmetry axis of three capsid copies.

    The axis runs through the middle of the three chain centres, along the
    normal of the plane they define. Fewer than three copies: no axis.
    """
    if len(chain_centroids) < 3:
        return None
    p, q, r = chain_centroids[:3]
    u = (q[0] - p[0], q[1] - p[1], q[2] - p[2])
    v = (r[0] - p[0], r[1] - p[1], r[2] - p[2])
    nx = u[1] * v[2] - u[2] * v[1]
    ny = u[2] * v[0] - u[0] * v[2]
    nz = u[0] * v[1] - u[1] * v[0]
    norm = math.sqrt(nx * nx + ny * ny + nz * nz)
    if norm == 0:
        return None
    mid = centroid([p, q, r])
    return (mid, (nx / norm, ny / norm, nz / norm))


def distance_to_axis(point, axis):
    """Perpendicular distance from a point to the axis line."""
    if axis is None or point is None:
        return None
    (ax, ay, az), (dx, dy, dz) = axis
    wx, wy, wz = point[0] - ax, point[1] - ay, point[2] - az
    dot = wx * dx + wy * dy + wz * dz
    px, py, pz = wx - dot * dx, wy - dot * dy, wz - dot * dz
    return math.sqrt(px * px + py * py + pz * pz)


def site_class(distance_a):
    """Our reading of the plan's site class column, from the axis distance."""
    if distance_a is None:
        return "undetermined: fewer than three capsid copies in the entry"
    if distance_a <= 15.0:
        return "threefold-spike-proximal"
    if distance_a <= 30.0:
        return "shoulder"
    return "floor"


def bind_call(n_contact_pairs: int) -> str:
    """Our reading of the plan's bind or no-bind column."""
    return "bind" if n_contact_pairs >= BIND_CALL_MIN_CONTACTS else "no-bind"


def write_pdb(atoms, path: Path, chain_map=None) -> None:
    """Write atoms in the fixed-column structure format the tools read."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    serial = 1
    for a in atoms:
        ch = (chain_map or {}).get(a["chain"], a["chain"])[:1] or "A"
        name = a["atom"]
        name_f = (" %-3s" % name) if len(name) < 4 else name
        elem = (a.get("element") or name[0])[:2].rjust(2)
        lines.append("ATOM  %5d %4s %3s %1s%4d    %8.3f%8.3f%8.3f%6.2f%6.2f          %2s" % (
            serial % 100000, name_f, a["resname"], ch, a["resseq"] % 10000,
            a["x"], a["y"], a["z"], 1.00, 0.00, elem))
        serial += 1
    lines.append("END")
    path.write_text("\n".join(lines) + "\n")


def read_pdb_atoms(text: str):
    """Read back a fixed-column structure file written by us or by a tool."""
    atoms = []
    for ln in text.splitlines():
        if not ln.startswith(("ATOM  ", "HETATM")):
            continue
        try:
            atoms.append({
                "atom": ln[12:16].strip(),
                "resname": ln[17:20].strip(),
                "chain": ln[21:22].strip() or "A",
                "resseq": int(ln[22:26]),
                "x": float(ln[30:38]), "y": float(ln[38:46]), "z": float(ln[46:54]),
                "element": (ln[76:78].strip() or ln[12:16].strip()[:1]),
            })
        except ValueError:
            continue
    return atoms


# ---------------------------------------------------------------------------
# Decisions. All pure, all planted in the selftest.
# ---------------------------------------------------------------------------

def band_decision(value, band, frac=MARGINAL_FRACTION):
    """PASS inside the band, FAIL outside, VOID within 10 percent of an edge.

    Returns the decision and whether the value was too close to an edge to call.
    """
    if value is None:
        return "VOID", False
    lo, hi = band
    for edge in (lo, hi):
        if edge * (1.0 - frac) <= value <= edge * (1.0 + frac):
            return "VOID", True
    if lo <= value <= hi:
        return "PASS", False
    return "FAIL", False


def gate_result(value):
    """The plan's own gate on C1: at most 1 hour per run. Reported, never acted on."""
    if value is None:
        return {"gate_value": GATE_VALUE, "gate_pass": None, "gate_else": GATE_ELSE}
    return {"gate_value": GATE_VALUE, "gate_pass": bool(value <= GATE_VALUE), "gate_else": GATE_ELSE}


def sleep_check(measured_seconds):
    """Does the timer reproduce a planted 60 second sleep within 5 percent?"""
    error = abs(measured_seconds - SLEEP_SECONDS) / SLEEP_SECONDS
    return {"measured_s": measured_seconds, "planted_s": SLEEP_SECONDS,
            "relative_error": error, "pass": error <= SLEEP_TOLERANCE}


def empty_run_check(seconds, bytes_written):
    """Does an empty run cost nothing worth counting?"""
    ok = (seconds < EMPTY_MAX_SECONDS) and (bytes_written < EMPTY_MAX_BYTES)
    return {"seconds": seconds, "bytes": bytes_written, "pass": ok,
            "subtract_time_s": 0.0 if ok else float(seconds),
            "subtract_bytes": 0 if ok else int(bytes_written),
            "labels": [] if ok else [LABEL_OVERHEAD]}


def spread_check(per_pair_times):
    """Repeats of one cell must differ. Identical repeats mean the wrong source of variance.

    Input: a mapping of pair name to its list of per-seed seconds.
    """
    out = {"zero_spread_pairs": [], "high_spread_pairs": [], "rel_sd": {}, "halt": None,
           "labels": []}
    for pair, times in sorted(per_pair_times.items()):
        if len(times) < 2:
            continue
        r = rel_sd(times)
        out["rel_sd"][pair] = r
        if r == 0.0:
            out["zero_spread_pairs"].append(pair)
        elif r > SPREAD_HIGH:
            out["high_spread_pairs"].append(pair)
    if out["zero_spread_pairs"]:
        out["halt"] = WRONG_VARIANCE_SOURCE
        out["labels"].append(LABEL_ZERO_SPREAD)
    if out["high_spread_pairs"]:
        out["labels"].append(LABEL_SPREAD_HIGH)
    return out


def labels_for_rel_sd(value):
    """A high but nonzero spread only warns. It changes no decision."""
    if value == 0.0:
        return [LABEL_ZERO_SPREAD]
    return [LABEL_SPREAD_HIGH] if value > SPREAD_HIGH else []


def anchor_decision(overlap, rmsd_a, serial_parallel_rmsd, call_serial, call_parallel):
    """The redocking check. Both halves must hold."""
    reproduces = (overlap is not None and overlap >= ANCHOR_OVERLAP_MIN) or \
                 (rmsd_a is not None and rmsd_a <= ANCHOR_RMSD_MAX)
    agree = (serial_parallel_rmsd is not None and
             serial_parallel_rmsd <= ANCHOR_SERIAL_PARALLEL_RMSD_MAX and
             call_serial == call_parallel)
    return {"reproduces_published": bool(reproduces), "serial_parallel_agree": bool(agree),
            "pass": bool(reproduces and agree)}


def atom_count_ok(n_atoms) -> bool:
    """The plan's own system size window for the dynamics run."""
    return n_atoms is not None and MD_ATOMS_MIN <= n_atoms <= MD_ATOMS_MAX


def c1_minimum_ok(rows):
    """At least 3 finished AlphaFold runs, and every one of the 3 pairs covered."""
    done = [r for r in rows if r.get("status") == "ok"]
    pairs = set(r.get("pair") for r in done)
    return len(done) >= 3 and len(pairs) >= N_PAIRS


def storage_gib(bytes_per_run, runs=GRID_RUNS):
    """Bytes of one run scaled to the grid. 1073741824 bytes over 216 runs is 216.0 GiB."""
    if bytes_per_run is None:
        return None
    return bytes_per_run / GIB * runs


def md_rate_disagreement(engine_rate, wallclock_rate):
    """Do the engine's own speed line and the stopwatch agree within 5 percent?"""
    if engine_rate is None or wallclock_rate is None or wallclock_rate == 0:
        return None, False
    rel = abs(engine_rate - wallclock_rate) / abs(wallclock_rate)
    return rel, rel > MD_RATE_DISAGREE


# ---------------------------------------------------------------------------
# Cost and time guard
# ---------------------------------------------------------------------------

def cost_usd(elapsed_seconds, price_per_hour):
    """What the box has cost so far. 3600 seconds at 1.99 is 1.99 dollars."""
    return price_per_hour * elapsed_seconds / 3600.0


def stop_at_seconds(price_per_hour, budget_usd, timeout_seconds):
    """The earlier of the money cap and the clock cap, in seconds from the start."""
    if price_per_hour <= 0:
        return float(timeout_seconds)
    money_seconds = budget_usd / price_per_hour * 3600.0
    return min(float(timeout_seconds), money_seconds)


def guard_check(elapsed, est_stage_seconds, price, budget, timeout, margin=None):
    """May the next stage start? Returns the verdict and the seconds left.

    A stage's allowance is the lesser of its ceiling and the time left minus the
    margin (400 s) and the endpoints slot (100 s), so the margin default here is
    500 seconds.
    """
    if margin is None:
        margin = MARGIN_SECONDS + CEILINGS["endpoints"]
    stop_at = stop_at_seconds(price, budget, timeout)
    left = stop_at - elapsed - margin
    return {"may_start": est_stage_seconds <= left, "seconds_left": left,
            "stop_at_s": stop_at, "cost_so_far_usd": cost_usd(elapsed, price),
            "estimate_s": est_stage_seconds}


def tool_allowance_seconds(elapsed, price, budget, timeout):
    """Seconds one tool call may run: stop_at minus elapsed minus 700.

    The on-box script kills the whole run at stop_at minus elapsed minus 600.
    This inner stop is 100 seconds shorter, so it always fires first and the
    call is ended as a ceiling stop rather than by the outer kill.
    """
    stop_at = stop_at_seconds(price, budget, timeout)
    return stop_at - elapsed - INNER_TOOL_RESERVE_SECONDS


# ---------------------------------------------------------------------------
# State: what the run knows so far. Each stage reads it and writes it back.
# ---------------------------------------------------------------------------

def default_state():
    return {
        "tag": TAG,
        "t0": None,
        "run_valid": True,
        "run_valid_reasons": [],
        "stages_done": [],
        "stops": [],
        "labels": [],
        "hardware": {},
        "versions": {},
        "downloads": [],
        "pairs": [],
        "controls": {},
        "anchor": {},
        "overhead": {"subtract_time_s": 0.0, "subtract_bytes": 0},
        "measured": {},
        "records_written": [],
        "exit_code": 0,
    }


def load_state(results: Path = None) -> dict:
    results = results or RESULTS
    path = results / "state_m4.json"
    if path.exists():
        st = json.loads(path.read_text())
        base = default_state()
        base.update(st)
        return base
    st = default_state()
    st["t0"] = read_t0(results)
    return st


def save_state(state: dict, results: Path = None) -> None:
    results = results or RESULTS
    jdump(results / "state_m4.json", state)


def read_t0(results: Path) -> float:
    """The moment the box started working, written by the on-box script."""
    p = Path(results) / "t0.txt"
    if p.exists():
        try:
            return float(p.read_text().strip())
        except ValueError:
            pass
    return now()


def elapsed_of(state) -> float:
    return now() - (state.get("t0") or now())


def caps_from_env():
    """Read the caps the operator set. Never above one launch's ceiling."""
    def num(name, default):
        raw = os.environ.get(name, "").strip()
        try:
            return float(raw) if raw else float(default)
        except ValueError:
            return float(default)
    price = num("PRICE_USD_PER_HOUR", DEFAULT_PRICE)
    budget = min(num("BUDGET_LEFT_USD", MAX_BUDGET_PER_LAUNCH), MAX_BUDGET_PER_LAUNCH)
    timeout_seen = os.environ.get("REMOTE_TIMEOUT", "").strip()
    timeout = min(num("REMOTE_TIMEOUT", MAX_TIMEOUT), MAX_TIMEOUT)
    caps = {"price_usd_per_hour": price, "budget_left_usd": budget, "remote_timeout_s": timeout,
            "remote_timeout_seen": timeout_seen or None,
            "instance_type": os.environ.get("INSTANCE_TYPE", "") or None}
    if not timeout_seen:
        caps["labels"] = [LABEL_TIMEOUT_NOT_FORWARDED]
    return caps


def record_stop(state, stage: str, kind: str, reason: str) -> None:
    """Note that the clock, the money or a stage ceiling stopped work.

    A stop of this kind does not make the run invalid. It means some planned
    work never happened, so those inputs are not decided, and the run ends with
    the guard-stop exit code.
    """
    state.setdefault("stops", []).append(
        {"stage": stage, "kind": kind, "reason": str(reason)[:1000], "at_utc": utc()})
    if LABEL_INCOMPLETE_RUN not in state.setdefault("labels", []):
        state["labels"].append(LABEL_INCOMPLETE_RUN)


def was_stopped(state) -> bool:
    return bool(state.get("stops"))


def set_run_invalid(state, reason: str) -> None:
    """Mark the whole run not valid. Every record written after this says so."""
    if state["run_valid"]:
        state["run_valid"] = False
    state["run_valid_reasons"].append({"reason": reason, "at_utc": utc()})
    write_run_valid(state)


def write_run_valid(state, results: Path = None) -> None:
    results = results or RESULTS
    jdump(results / "RUN_VALID.json", {
        "run_valid": state["run_valid"],
        "reasons": state["run_valid_reasons"],
        "tag": TAG,
        "written_utc": utc(),
    })


# ---------------------------------------------------------------------------
# Record writing, through the project's own record writer.
# ---------------------------------------------------------------------------

def load_provenance():
    import importlib.util
    path = SCRIPT_DIR / "frozen" / "provenance.py"
    if not path.exists():
        raise ToolError("record writer missing: %s" % path)
    spec = importlib.util.spec_from_file_location("m4_provenance", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_record(state, name, *, cell, inputs, metric, values, threshold, decision_rule,
                 decision, notes="", rows=None, results: Path = None):
    """Write one self-describing record, stamped with whether the run is valid.

    The validity flag goes in two places on purpose: at the top of the record
    and beside the values. A reader of either half cannot miss it.
    """
    prov = load_provenance()
    results = results or RESULTS
    results.mkdir(parents=True, exist_ok=True)
    values = dict(values)
    values["run_valid"] = bool(state["run_valid"])
    if was_stopped(state):
        labels = list(values.get("labels") or [])
        if LABEL_INCOMPLETE_RUN not in labels:
            labels.append(LABEL_INCOMPLETE_RUN)
        values["labels"] = labels
        values["stops"] = state.get("stops")
    cell = dict(cell)
    cell["run_valid"] = bool(state["run_valid"])
    path = results / ("%s_tag-%s.json" % (name, TAG))
    prov.write_result(path, cell=cell, inputs=inputs, metric=metric, values=values,
                      threshold=threshold, decision_rule=decision_rule, decision=decision,
                      notes=notes, rows=rows)
    rec = json.loads(path.read_text())
    rec["run_valid"] = bool(state["run_valid"])
    path.write_text(json.dumps(rec, indent=2, sort_keys=True))
    if name not in state["records_written"]:
        state["records_written"].append(name)
    save_state(state, results)
    return path


def hardware_block(state):
    """The labels every measured record must carry about the machine."""
    hw = dict(state.get("hardware") or {})
    caps = state.get("caps") or caps_from_env()
    hw.setdefault("instance_type", caps.get("instance_type"))
    hw["price_usd_per_hour"] = caps.get("price_usd_per_hour")
    return hw


def describe_inputs(prov, paths_with_counts):
    return [prov.describe_input(p, n_items=n) for p, n in paths_with_counts]


# ---------------------------------------------------------------------------
# Running declared tools. Every call is saved whole.
# ---------------------------------------------------------------------------

def child_env(base=None, extra=None):
    """The environment a child tool gets: a copy, with both tokens removed.

    No tool run here needs a token, and a token in a child's environment is a
    token one crash report away from a log file.
    """
    out = dict(os.environ if base is None else base)
    for name in SECRET_ENV_NAMES:
        out.pop(name, None)
    if extra:
        out.update(extra)
    return out


def record_process_group(pgid, results: Path = None, remove=False) -> None:
    """Keep the list of process groups we started, so a killed run leaves nothing.

    The on-box script reads this file after an outer kill and stops each group
    by its number. A name match would kill a stranger's process; a number does
    not.
    """
    results = results or RESULTS
    results.mkdir(parents=True, exist_ok=True)
    path = results / "process_groups.txt"
    have = [ln.strip() for ln in path.read_text().splitlines()] if path.exists() else []
    have = [ln for ln in have if ln and ln != str(pgid)]
    if not remove:
        have.append(str(pgid))
    path.write_text("\n".join(have) + ("\n" if have else ""))


def kill_process_group(pgid, grace=5.0) -> None:
    """Stop a tool and every child it started. Polite first, then not."""
    import signal
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(pgid, sig)
        except (ProcessLookupError, PermissionError, OSError):
            return
        deadline = now() + grace
        while now() < deadline:
            try:
                os.killpg(pgid, 0)
            except (ProcessLookupError, OSError):
                return
            time.sleep(0.1)


def run_tool(argv, log_name, timeout_s, cwd=None, env=None, results: Path = None,
             allow_timeout=False):
    """Run one declared tool in its own process group. Save its output whole.

    A tool that exits non-zero is a real failure and raises. A tool that runs
    past the seconds it was given is a different thing: the whole group is
    killed, and the caller is told so. With allow_timeout set, that is returned
    instead of raised, because running out of the clock is a guard stop and not
    a broken machine. Nothing here retries, substitutes or patches a tool.
    """
    results = results or RESULTS
    logs = results / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    started = now()
    full_env = child_env(extra=env)
    timed_out = False
    pgid = None
    try:
        proc = subprocess.Popen(argv, cwd=str(cwd) if cwd else None, env=full_env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                start_new_session=True)
        try:
            pgid = os.getpgid(proc.pid)
            record_process_group(pgid, results)
        except OSError:
            pgid = None
        try:
            out = proc.communicate(timeout=timeout_s)[0].decode("utf-8", "replace")
            code = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            if pgid is not None:
                kill_process_group(pgid)
            else:
                proc.kill()
            try:
                out = proc.communicate(timeout=30)[0].decode("utf-8", "replace")
            except Exception:                     # noqa: BLE001
                out = ""
            code = -9
    except OSError as exc:
        out = "could not start: %s" % exc
        code = -1
    finally:
        if pgid is not None:
            record_process_group(pgid, results, remove=True)
    ended = now()
    log_path = logs / ("%s.log" % log_name)
    log_path.write_text("$ %s\nstarted %s\nexit %s timed_out %s\n\n%s" % (
        " ".join(argv), utc(started), code, timed_out, out))
    result = {"argv": argv, "exit_code": code, "timed_out": timed_out,
              "wall_s": ended - started, "log": str(log_path), "output": out,
              "started_utc": utc(started), "ended_utc": utc(ended)}
    if timed_out and allow_timeout:
        return result
    if code != 0:
        raise ToolError("%s failed with exit %s (log %s): %s" % (
            argv[0], code, log_path, out.strip().splitlines()[-1:] or ""))
    return result


def download(url, dest: Path, timeout_s=900, results: Path = None):
    """Fetch one file from one of the two allowed sources. Record what arrived."""
    allowed = (URL_STRUCTURE, URL_AF_PARAMS)
    if url not in allowed:
        raise ToolError("download source not allowed: %s" % url)
    dest.parent.mkdir(parents=True, exist_ok=True)
    started = now()
    try:
        with urllib.request.urlopen(url, timeout=timeout_s) as resp, open(dest, "wb") as fh:
            shutil.copyfileobj(resp, fh)
    except Exception as exc:
        raise ToolError("download failed: %s (%s)" % (url, exc))
    rec = {"url": url, "path": str(dest), "sha256": sha256_file(dest),
           "bytes": dest.stat().st_size, "wall_s": now() - started, "fetched_utc": utc(started)}
    append_row("download", rec, results)
    return rec


def safe_extract_tar(tar_path: Path, dest: Path):
    """Unpack an archive without letting it write outside the target directory."""
    import tarfile
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path) as tf:
        for member in tf.getmembers():
            name = member.name
            if name.startswith("/") or ".." in Path(name).parts:
                raise ToolError("archive member escapes the target directory: %s" % name)
        tf.extractall(dest)


def venv_python() -> str:
    """The interpreter the on-box script installed the tools into."""
    cand = SCRIPT_DIR / ".venv" / "bin" / "python"
    return str(cand) if cand.exists() else sys.executable


def venv_bin(name: str) -> str:
    cand = SCRIPT_DIR / ".venv" / "bin" / name
    return str(cand) if cand.exists() else name


def package_version(pkg: str):
    try:
        out = subprocess.run([venv_python(), "-c",
                              "import importlib.metadata as m;print(m.version(%r))" % pkg],
                             stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=60)
        v = out.stdout.decode().strip()
        return v or None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Stage: downloads and the stand-in pairs
# ---------------------------------------------------------------------------

def build_pairs(atoms, target_lengths=PAIR_TARGET_LENGTHS):
    """Build three stand-in complexes from the chains of the published entry.

    Each complex is one capsid slot plus the receptor chain. The receptor is
    taken whole. Capsid copies are added, and the last one trimmed, until the
    complex has the target number of residues. Targets are spread over the
    750 to 1000 residues the plan's setting calls for.
    """
    chains = chains_from_atoms(atoms)
    seqs = {c: chain_sequence(a) for c, a in chains.items()}
    ordered = sorted(seqs.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    ordered = [(c, s) for c, s in ordered if len(s) >= 20]
    if len(ordered) < 2:
        raise ToolError("entry has fewer than two usable protein chains")
    capsid_len = len(ordered[0][1])
    capsid_chains = [c for c, s in ordered if len(s) == capsid_len]
    receptor_chains = [c for c, s in ordered if len(s) != capsid_len]
    if not receptor_chains:
        raise ToolError("entry has no second distinct chain to act as the receptor")
    receptor = receptor_chains[0]
    receptor_seq = seqs[receptor]
    pairs = []
    for i, target in enumerate(target_lengths):
        slot = capsid_chains[i % len(capsid_chains)]
        capsid_seq = seqs[slot]
        need = target - len(receptor_seq)
        if need < 1:
            raise ToolError("receptor chain alone already exceeds the target length")
        copies = []
        while need > 0:
            take = min(need, len(capsid_seq))
            copies.append(capsid_seq[:take])
            need -= take
        total = len(receptor_seq) + sum(len(c) for c in copies)
        if not (PAIR_MIN_RESIDUES <= total <= PAIR_MAX_RESIDUES):
            raise ToolError("built complex of %d residues, outside 750 to 1000" % total)
        pairs.append({
            "pair": "pair%d" % (i + 1),
            "capsid_slot_chain": slot,
            "receptor_chain": receptor,
            "capsid_copies": len(copies),
            "chain_lengths": [len(c) for c in copies] + [len(receptor_seq)],
            "total_residues": total,
            "sequences": copies + [receptor_seq],
            "sequence_sha256": sha256_text(":".join(copies + [receptor_seq])),
            "file_sha256": sha256_text(">%s\n%s\n" % ("pair%d" % (i + 1),
                                                      ":".join(copies + [receptor_seq]))),
        })
    return pairs


def stage_downloads(state):
    """Install check, GPU labels, the published entry and the AlphaFold parameters."""
    results = RESULTS
    caps = caps_from_env()
    state["caps"] = caps
    el = elapsed_of(state)
    if el > CEILINGS["install"]:
        raise GuardStop("install and downloads passed its %d second ceiling" % CEILINGS["install"])

    smi = run_tool(["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
                   "nvidia_smi", 120)
    hw = parse_nvidia_smi(smi["output"])
    try:
        cu = run_tool(["nvidia-smi"], "nvidia_smi_full", 120)
        hw["cuda_runtime"] = parse_cuda_version(cu["output"])
    except ToolError:
        hw["cuda_runtime"] = None
    hw["instance_type"] = caps["instance_type"]
    hw["price_usd_per_hour"] = caps["price_usd_per_hour"]
    state["hardware"] = hw
    if not gpu_is_a100(hw.get("gpu_name")):
        state["labels"].append(LABEL_NOT_A100)

    state["versions"] = {
        "alphafold_implementation": "ColabFold colabfold_batch (AlphaFold-Multimer weights)",
        "colabfold_version": package_version("colabfold"),
        "alphafold_colabfold_version": package_version("alphafold-colabfold"),
        "jax_version": package_version("jax"),
        "jaxlib_version": package_version("jaxlib"),
        "docking_code": "LightDock",
        "lightdock_version": package_version("lightdock"),
        "md_engine": "OpenMM",
        "openmm_version": package_version("openmm"),
        "md_precision": "mixed",
        "md_platform": "CUDA",
        "md_build": "pip wheel",
        "python": sys.version.split()[0],
    }

    WORK.mkdir(parents=True, exist_ok=True)
    cif = WORK / ("%s.cif" % PDB_ENTRY)
    if not cif.exists():
        state["downloads"].append(download(URL_STRUCTURE, cif, results=results))
    params_tar = WORK / "alphafold_params.tar"
    data_dir = WORK / "af_data"
    if not (data_dir / "params").exists():
        if not params_tar.exists():
            state["downloads"].append(download(URL_AF_PARAMS, params_tar, results=results))
        safe_extract_tar(params_tar, data_dir / "params")
    state["af_data_dir"] = str(data_dir)
    state["structure_path"] = str(cif)
    state["structure_sha256"] = sha256_file(cif)

    atoms = parse_cif_atoms(cif.read_text())
    if not atoms:
        raise ToolError("no protein atoms read from %s" % cif)
    state["pairs"] = build_pairs(atoms)
    for p in state["pairs"]:
        append_row("pairs", p, results)
    state["versions"]["af_params_archive_sha256"] = (
        state["downloads"][-1]["sha256"] if state["downloads"] else None)
    state["stages_done"].append("downloads")
    save_state(state)
    return state


# ---------------------------------------------------------------------------
# Stage: the three controls
# ---------------------------------------------------------------------------

def timed(fn):
    """The one stopwatch every measurement uses, so the sleep check tests them all."""
    start = now()
    out = fn()
    return out, now() - start


def stage_controls(state):
    """A planted sleep, an empty run, and the unit print. No band is read yet."""
    prov = load_provenance()
    results = RESULTS

    # Planted sleep: the stopwatch must reproduce a known 60 seconds.
    sleep_started = utc()
    _, slept = timed(lambda: time.sleep(SLEEP_SECONDS))
    chk = sleep_check(slept)
    append_row("control", {"control": "planted_sleep", **chk}, results)
    state["controls"]["sleep"] = chk
    if not chk["pass"]:
        set_run_invalid(state, "planted 60 second sleep was timed as %.3f s, error %.3f"
                        % (slept, chk["relative_error"]))
    write_record(state, "endpoint-control-sleep",
                 cell={"control": "planted_sleep", "tag": TAG, "arm": "control"},
                 inputs=[],
                 metric="Measured seconds for a planted 60 second sleep",
                 values={"measured_s": slept, "planted_s": SLEEP_SECONDS,
                         "relative_error": chk["relative_error"],
                         "started_utc": sleep_started, "ended_utc": utc(),
                         "labels": list(state["labels"]), **hardware_block(state)},
                 threshold={"max_relative_error": SLEEP_TOLERANCE},
                 decision_rule=RULE_SLEEP,
                 decision="PASS" if chk["pass"] else "FAIL",
                 notes="The timer is the same one every input measurement uses.")
    if not chk["pass"]:
        raise HarnessInvalid("planted sleep check failed")

    # Empty run: the harness over nothing at all.
    empty_dir = WORK / "empty_run"
    if empty_dir.exists():
        shutil.rmtree(empty_dir)
    empty_dir.mkdir(parents=True, exist_ok=True)

    def _empty():
        subprocess.run([sys.executable, "-c", "pass"], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=60)
    empty_started = utc()
    _, empty_s = timed(_empty)
    empty_b = apparent_bytes([empty_dir])
    emp = empty_run_check(empty_s, empty_b)
    append_row("control", {"control": "empty_run", **emp}, results)
    state["controls"]["empty"] = emp
    state["overhead"] = {"subtract_time_s": emp["subtract_time_s"],
                         "subtract_bytes": emp["subtract_bytes"]}
    for lab in emp["labels"]:
        if lab not in state["labels"]:
            state["labels"].append(lab)
    write_record(state, "endpoint-control-empty",
                 cell={"control": "empty_run", "tag": TAG, "arm": "control"},
                 inputs=[],
                 metric="Seconds and bytes an empty harness run costs",
                 values={"seconds": empty_s, "bytes": empty_b,
                         "subtract_time_s": emp["subtract_time_s"],
                         "subtract_bytes": emp["subtract_bytes"],
                         "started_utc": empty_started, "ended_utc": utc(),
                         "labels": list(state["labels"]), **hardware_block(state)},
                 threshold={"max_seconds": EMPTY_MAX_SECONDS, "max_bytes": EMPTY_MAX_BYTES},
                 decision_rule=RULE_EMPTY,
                 decision="PASS" if emp["pass"] else "FAIL",
                 notes="A failing empty run does not stop the run. Its cost is subtracted.")

    # Unit and scale print. The record of the same thing is written later, once
    # raw readings exist, and before any band is compared.
    print("unit and scale: 1800 raw seconds is %.4f hours" % hours(1800))
    print("unit and scale: %d steps of %.1f fs in 335 s is %.2f ns/day"
          % (MD_PRODUCTION_STEPS, MD_TIMESTEP_FS,
             ns_per_day_from_wallclock(MD_PRODUCTION_STEPS, MD_TIMESTEP_FS, 335.0)))
    print("unit and scale: %d raw bytes per run over %d runs is %.2f GiB"
          % (1 << 30, GRID_RUNS, storage_gib(float(1 << 30), GRID_RUNS)))
    append_row("control", {"control": "unit_and_scale_print",
                           "hours_per_1800_s": hours(1800),
                           "ns_per_day_250000_steps_335_s":
                               ns_per_day_from_wallclock(MD_PRODUCTION_STEPS, MD_TIMESTEP_FS, 335.0),
                           "gib_per_gib_run_216": storage_gib(float(1 << 30), GRID_RUNS)}, results)
    state["stages_done"].append("controls")
    save_state(state)
    return state


# ---------------------------------------------------------------------------
# Stage: the anchor redocking
# ---------------------------------------------------------------------------

def dock(receptor_pdb: Path, ligand_pdb: Path, outdir: Path, cores: int, timeout_s: int,
         tag: str, swarms=2, glowworms=20, steps=20, allow_timeout=False, runner=None):
    """Run the declared docking code once and return its top pose.

    The flags are recorded with the result. Nothing is retried or substituted.
    With allow_timeout set, a call that runs past the seconds it was given
    returns a result marked timed out instead of raising: that is a ceiling
    stop, not a broken machine.
    """
    runner = runner or run_tool
    outdir.mkdir(parents=True, exist_ok=True)
    rec_local = outdir / "receptor.pdb"
    lig_local = outdir / "ligand.pdb"
    shutil.copy(receptor_pdb, rec_local)
    shutil.copy(ligand_pdb, lig_local)
    started = now()
    deadline = started + timeout_s

    def left():
        return max(1, int(deadline - now()))

    setup = runner([venv_bin("lightdock3_setup.py"), "receptor.pdb", "ligand.pdb",
                    "-s", str(swarms), "-g", str(glowworms), "--noxt", "--noh", "--now",
                    "-sp", "0"],
                   "dock_%s_setup" % tag, left(), cwd=outdir, allow_timeout=allow_timeout)
    if setup.get("timed_out"):
        return {"timed_out": True, "wall_s": now() - started, "log": setup["log"]}
    runlog = runner([venv_bin("lightdock3.py"), "setup.json", str(steps),
                     "-c", str(cores), "-s", "fastdfire"],
                    "dock_%s_run" % tag, left(), cwd=outdir, allow_timeout=allow_timeout)
    if runlog.get("timed_out"):
        return {"timed_out": True, "wall_s": now() - started, "log": runlog["log"]}
    gso = outdir / "swarm_0" / ("gso_%d.out" % steps)
    if not gso.exists():
        raise ToolError("docking produced no result file: %s" % gso)
    poses = runner([venv_bin("lgd_generate_conformations.py"), "receptor.pdb", "ligand.pdb",
                    str(gso), "1"], "dock_%s_poses" % tag, left(), cwd=outdir,
                   allow_timeout=allow_timeout)
    if poses.get("timed_out"):
        return {"timed_out": True, "wall_s": now() - started, "log": poses["log"]}
    pose = None
    for cand in sorted((outdir / "swarm_0").glob("lightdock_*.pdb")):
        pose = cand
        break
    if pose is None:
        raise ToolError("docking wrote no pose file in %s" % (outdir / "swarm_0"))
    wall = now() - started
    atoms = read_pdb_atoms(pose.read_text())
    return {"pose_path": str(pose), "pose_atoms": atoms, "wall_s": wall, "timed_out": False,
            "flags": {"swarms": swarms, "glowworms": glowworms, "steps": steps,
                      "cores": cores, "scoring": "fastdfire", "seed_points": 0},
            "setup_log": setup["log"], "run_log": runlog["log"]}


def write_pair_components(state, pair, outdir: Path):
    """Write the two halves of one stand-in complex as structure files."""
    atoms = parse_cif_atoms(Path(state["structure_path"]).read_text())
    chains = chains_from_atoms(atoms)
    cap = chains[pair["capsid_slot_chain"]]
    rec = chains[pair["receptor_chain"]]
    outdir.mkdir(parents=True, exist_ok=True)
    cap_path = outdir / "capsid.pdb"
    rec_path = outdir / "receptor.pdb"
    write_pdb(cap, cap_path, {pair["capsid_slot_chain"]: "A"})
    write_pdb(rec, rec_path, {pair["receptor_chain"]: "B"})
    return cap_path, rec_path, cap, rec


def stage_anchor(state):
    """Redock the receptor onto the capsid and compare with the published entry."""
    results = RESULTS
    caps = state.get("caps") or caps_from_env()
    el = elapsed_of(state)
    g = guard_check(el, 300, caps["price_usd_per_hour"], caps["budget_left_usd"],
                    caps["remote_timeout_s"])
    if not g["may_start"]:
        raise GuardStop("no time left for the anchor: %s" % json.dumps(g))

    atoms = parse_cif_atoms(Path(state["structure_path"]).read_text())
    chains = chains_from_atoms(atoms)
    pair = state["pairs"][0]
    anchor_dir = WORK / "anchor"
    cap_path, rec_path, cap_atoms, rec_atoms = write_pair_components(state, pair, anchor_dir)

    # Everything below is keyed by chain role, never by the letter in a file.
    cap_role = as_role(cap_atoms, ROLE_CAPSID)
    rec_role = as_role(rec_atoms, ROLE_RECEPTOR)
    native_pairs = contact_pairs(cap_role, rec_role)
    native_interface = interface_residues(cap_atoms, rec_atoms)
    native_backbone = backbone_coords(rec_atoms)
    started = utc()

    def anchor_void(reason):
        """The anchor was never decided. A stopped tool is a ceiling stop, not a miss."""
        prov_local = load_provenance()
        write_record(state, "endpoint-anchor",
                     cell={"endpoint": "anchor", "tag": TAG, "arm": "anchor"},
                     inputs=describe_inputs(prov_local,
                                            [(state["structure_path"], len(atoms))]),
                     metric=("Contact overlap with the published entry %s at the %.1f "
                             "Angstrom cutoff, and interface backbone RMSD"
                             % (PDB_ENTRY, CONTACT_CUTOFF_A)),
                     values={
                         "measured": None,
                         "published": ("PKD2 bound to the AAV2 spike region adjacent to the "
                                       "icosahedral three-fold axis (PDB %s)" % PDB_ENTRY),
                         "tolerance": ("contact overlap at least %.2f at the %.1f Angstrom "
                                       "cutoff, or interface backbone RMSD at most %.1f "
                                       "Angstrom; serial versus parallel top-pose RMSD at "
                                       "most %.1f Angstrom with identical bind or no-bind "
                                       "calls"
                                       % (ANCHOR_OVERLAP_MIN, CONTACT_CUTOFF_A,
                                          ANCHOR_RMSD_MAX,
                                          ANCHOR_SERIAL_PARALLEL_RMSD_MAX)),
                         "unmeasured": True,
                         "independent_code": "not run: single docking code",
                         "labels": list(state["labels"]) + [LABEL_STANDIN, LABEL_UNMEASURED],
                         "started_utc": started, "ended_utc": utc(),
                         **hardware_block(state), **state["versions"]},
                     threshold={"overlap_min": ANCHOR_OVERLAP_MIN,
                                "rmsd_max_a": ANCHOR_RMSD_MAX,
                                "serial_parallel_rmsd_max_a":
                                    ANCHOR_SERIAL_PARALLEL_RMSD_MAX},
                     decision_rule=RULE_ANCHOR, decision="VOID", notes=reason)

    inner = tool_allowance_seconds(elapsed_of(state), caps["price_usd_per_hour"],
                                   caps["budget_left_usd"], caps["remote_timeout_s"])
    anchor_allow = int(max(1, min(CEILINGS["controls_anchor"], inner)))
    serial = dock(cap_path, rec_path, anchor_dir / "serial", cores=1,
                  timeout_s=anchor_allow, tag="anchor_serial", allow_timeout=True)
    if serial.get("timed_out"):
        record_stop(state, "anchor", "timeout",
                    "the serial anchor docking was stopped at its %d second allowance"
                    % anchor_allow)
        anchor_void("the anchor docking was stopped at its allowance")
        raise GuardStop("anchor docking stopped at its allowance")
    ncores = max(2, (os.cpu_count() or 2))
    parallel = dock(cap_path, rec_path, anchor_dir / "parallel", cores=ncores,
                    timeout_s=anchor_allow, tag="anchor_parallel", allow_timeout=True)
    if parallel.get("timed_out"):
        record_stop(state, "anchor", "timeout",
                    "the parallel anchor docking was stopped at its %d second allowance"
                    % anchor_allow)
        anchor_void("the anchor docking was stopped at its allowance")
        raise GuardStop("anchor docking stopped at its allowance")

    def readout(d):
        pose_atoms = d["pose_atoms"]
        pose_role = as_role(pose_atoms, ROLE_RECEPTOR)
        pairs_found = contact_pairs(cap_role, pose_role)
        ov = contact_overlap(native_pairs, pairs_found)
        rm = interface_backbone_rmsd(rec_atoms, pose_atoms, native_interface)
        whole = rmsd_direct(native_backbone, backbone_coords(pose_atoms)) \
            if len(backbone_coords(pose_atoms)) == len(native_backbone) else None
        return {"overlap": ov, "interface_backbone_rmsd": rm,
                "whole_chain_backbone_rmsd": whole,
                "n_interface_residues_reference": len(native_interface),
                "n_contact_pairs": len(pairs_found), "call": bind_call(len(pairs_found))}

    r_ser = readout(serial)
    r_par = readout(parallel)
    sp_rmsd = rmsd_direct(backbone_coords(serial["pose_atoms"]),
                          backbone_coords(parallel["pose_atoms"]))
    for name, d, r in (("serial", serial, r_ser), ("parallel", parallel, r_par)):
        append_row("anchor", {"mode": name, "wall_s": d["wall_s"], "flags": d["flags"],
                              "pose_path": d["pose_path"], **r}, results)

    dec = anchor_decision(r_ser["overlap"], r_ser["interface_backbone_rmsd"], sp_rmsd,
                          r_ser["call"], r_par["call"])
    state["anchor"] = {"serial": r_ser, "parallel": r_par, "serial_parallel_rmsd": sp_rmsd,
                       **dec}
    prov = load_provenance()
    write_record(state, "endpoint-anchor",
                 cell={"endpoint": "anchor", "tag": TAG, "arm": "anchor"},
                 inputs=describe_inputs(prov, [(state["structure_path"], len(atoms))]),
                 metric=("Contact overlap with the published entry %s at the %.1f Angstrom cutoff, "
                         "and interface backbone RMSD" % (PDB_ENTRY, CONTACT_CUTOFF_A)),
                 values={
                     "measured": r_ser["overlap"],
                     "published": ("PKD2 bound to the AAV2 spike region adjacent to the "
                                   "icosahedral three-fold axis (PDB %s)" % PDB_ENTRY),
                     "tolerance": ("contact overlap at least %.2f at the %.1f Angstrom cutoff, or "
                                   "interface backbone RMSD at most %.1f Angstrom; serial versus "
                                   "parallel top-pose RMSD at most %.1f Angstrom with identical "
                                   "bind or no-bind calls"
                                   % (ANCHOR_OVERLAP_MIN, CONTACT_CUTOFF_A, ANCHOR_RMSD_MAX,
                                      ANCHOR_SERIAL_PARALLEL_RMSD_MAX)),
                     "interface_backbone_rmsd": r_ser["interface_backbone_rmsd"],
                     "interface_backbone_rmsd_is_over": (
                         "the N, CA, C and O atoms of the receptor residues that touch the "
                         "capsid in the published entry, in the capsid frame, with no refitting"),
                     "n_interface_residues_reference": len(native_interface),
                     "serial_parallel_rmsd": sp_rmsd,
                     "serial_parallel_rmsd_is_over": LABEL_SP_WHOLE_CHAIN,
                     "call_serial": r_ser["call"], "call_parallel": r_par["call"],
                     "n_native_contact_pairs": len(native_pairs),
                     "independent_code": "not run: single docking code",
                     "labels": list(state["labels"]) + [LABEL_STANDIN, LABEL_SP_WHOLE_CHAIN],
                     "started_utc": started, "ended_utc": utc(),
                     "note": ("the serial and parallel runs are repeats on one box; "
                              "they are not independent confirmation"),
                     **hardware_block(state), **state["versions"]},
                 threshold={"overlap_min": ANCHOR_OVERLAP_MIN, "rmsd_max_a": ANCHOR_RMSD_MAX,
                            "serial_parallel_rmsd_max_a": ANCHOR_SERIAL_PARALLEL_RMSD_MAX},
                 decision_rule=RULE_ANCHOR,
                 decision="PASS" if dec["pass"] else "FAIL")
    state["stages_done"].append("anchor")
    save_state(state)
    if not dec["pass"]:
        set_run_invalid(state, "anchor redocking did not reproduce the published interface")
        raise AnchorMiss("anchor miss")
    return state


# ---------------------------------------------------------------------------
# Stage: docking and analysis per pair, which is the auxiliary time
# ---------------------------------------------------------------------------

def interface_analysis(cap_atoms, pose_atoms, capsid_chain_centroids):
    """Contacts, interface residues, axis distance and site class for one pose."""
    pairs_found = contact_pairs(as_role(cap_atoms, ROLE_CAPSID),
                                as_role(pose_atoms, ROLE_RECEPTOR))
    iface_capsid = sorted(set(p[0] for p in pairs_found))
    iface_ligand = sorted(set(p[1] for p in pairs_found))
    iface_resseqs = set(r for _, r in iface_ligand)
    iface_points = [(a["x"], a["y"], a["z"]) for a in pose_atoms
                    if a["resseq"] in iface_resseqs]
    axis = threefold_axis(capsid_chain_centroids)
    dist = distance_to_axis(centroid(iface_points), axis) if iface_points else None
    return {"n_contact_pairs": len(pairs_found),
            "interface_residues_capsid": ["%s%d" % (c, r) for c, r in iface_capsid],
            "interface_residues_receptor": ["%s%d" % (c, r) for c, r in iface_ligand],
            "distance_to_nearest_threefold_axis_a": dist,
            "site_class": site_class(dist),
            "call": bind_call(len(pairs_found))}


def stage_aux(state):
    """Time docking, interface analysis and the call-table row, per pair."""
    results = RESULTS
    caps = state.get("caps") or caps_from_env()
    atoms = parse_cif_atoms(Path(state["structure_path"]).read_text())
    chains = chains_from_atoms(atoms)
    cap_len = max(len(chain_sequence(v)) for v in chains.values())
    capsid_centroids = [centroid([(a["x"], a["y"], a["z"]) for a in v])
                        for k, v in sorted(chains.items())
                        if len(chain_sequence(v)) == cap_len]
    table_path = results / "call_table_tag-%s.csv" % TAG
    if not table_path.exists():
        table_path.write_text("pair,bind_call,score,n_interface_residues,"
                              "distance_to_nearest_threefold_axis_a,site_class\n")
    done = list(state["measured"].get("C3_rows") or [])
    stage_start = now()
    for pair in state["pairs"]:
        if any(r.get("pair") == pair["pair"] for r in done):
            continue
        el = elapsed_of(state)
        stage_left = CEILINGS["aux"] - (now() - stage_start)
        inner = tool_allowance_seconds(el, caps["price_usd_per_hour"],
                                       caps["budget_left_usd"], caps["remote_timeout_s"])
        g = guard_check(el, min(AUX_PER_PAIR_CEILING, max(stage_left, 0)),
                        caps["price_usd_per_hour"], caps["budget_left_usd"],
                        caps["remote_timeout_s"])
        if stage_left < 30:
            record_stop(state, "aux", "ceiling",
                        "docking and analysis reached its %d second ceiling"
                        % CEILINGS["aux"])
            save_state(state)
            raise GuardStop("docking and analysis reached its ceiling")
        if not g["may_start"]:
            record_stop(state, "aux", "guard",
                        "no time left for another pair: %s" % json.dumps(g))
            save_state(state)
            raise GuardStop("no time left for another pair")
        pdir = WORK / "aux" / pair["pair"]
        cap_path, rec_path, cap_atoms, rec_atoms = write_pair_components(state, pair, pdir)
        start = now()
        allowance = int(max(1, min(AUX_PER_PAIR_CEILING, stage_left, inner)))
        d = dock(cap_path, rec_path, pdir / "dock", cores=max(2, os.cpu_count() or 2),
                 timeout_s=allowance, tag="aux_%s" % pair["pair"], allow_timeout=True)
        if d.get("timed_out"):
            # The pair reached its own cap. Its row is kept and marked, and it is
            # not counted in the mean. This is a ceiling stop, not a failure.
            row = {"pair": pair["pair"], "status": "truncated", "truncated": True,
                   "wall_s": now() - start, "allowance_s": allowance,
                   "note": "docking reached its %d second per-pair cap" % AUX_PER_PAIR_CEILING}
            append_row("aux", row, results)
            record_stop(state, "aux", "ceiling",
                        "pair %s reached its %d second cap" % (pair["pair"],
                                                               AUX_PER_PAIR_CEILING))
            save_state(state)
            continue
        ana = interface_analysis(cap_atoms, d["pose_atoms"], capsid_centroids)
        with open(table_path, "a") as fh:
            fh.write("%s,%s,%s,%d,%s,%s\n" % (
                pair["pair"], ana["call"], "", len(ana["interface_residues_receptor"]),
                "" if ana["distance_to_nearest_threefold_axis_a"] is None
                else "%.2f" % ana["distance_to_nearest_threefold_axis_a"],
                ana["site_class"]))
        wall = now() - start - state["overhead"]["subtract_time_s"]
        row = {"pair": pair["pair"], "wall_s": wall, "hours": hours(wall),
               "docking_wall_s": d["wall_s"], "flags": d["flags"],
               "pose_path": d["pose_path"], "status": "ok", **ana}
        append_row("aux", row, results)
        done.append(row)
        state.setdefault("md_inputs", []).append(
            {"pair": pair["pair"], "capsid_pdb": str(cap_path), "pose_pdb": d["pose_path"]})
        save_state(state)
    state["measured"]["C3_rows"] = done
    state["stages_done"].append("aux")
    save_state(state)
    return state


# ---------------------------------------------------------------------------
# Stage: AlphaFold timings, seed first
# ---------------------------------------------------------------------------

def write_pair_fasta(pair, path: Path):
    """One entry per complex. The colon separates the chains of the complex."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(">%s\n%s\n" % (pair["pair"], ":".join(pair["sequences"])))
    return path


def stage_af2(state):
    """Time whole prediction calls, one seed at a time across all three pairs."""
    results = RESULTS
    caps = state.get("caps") or caps_from_env()
    stage_start = now()
    rows = list(state.get("af_rows") or [])
    per_run_estimate = 700.0   # a planning number only, replaced by the first measurement
    for seed in AF_SEEDS:
        for pair in state["pairs"]:
            if any(r["pair"] == pair["pair"] and r["seed"] == seed for r in rows):
                continue
            done_ok = [r["wall_s"] for r in rows if r.get("status") == "ok"]
            est = mean(done_ok) if done_ok else per_run_estimate
            stage_left = CEILINGS["af2"] - (now() - stage_start)
            inner = tool_allowance_seconds(elapsed_of(state), caps["price_usd_per_hour"],
                                           caps["budget_left_usd"], caps["remote_timeout_s"])
            g = guard_check(elapsed_of(state), est, caps["price_usd_per_hour"],
                            caps["budget_left_usd"], caps["remote_timeout_s"])
            if est > stage_left:
                state["af_rows"] = rows
                record_stop(state, "af2", "ceiling",
                            "AlphaFold timings reached their %d second ceiling with %d of %d "
                            "runs done" % (CEILINGS["af2"], len(rows),
                                           len(AF_SEEDS) * len(state["pairs"])))
                save_state(state)
                raise GuardStop("AlphaFold stage ceiling reached")
            if not g["may_start"]:
                state["af_rows"] = rows
                record_stop(state, "af2", "guard",
                            "no time left for another AlphaFold run: %s" % json.dumps(g))
                save_state(state)
                raise GuardStop("AlphaFold time guard")
            outdir = WORK / "af2" / ("%s_seed%d" % (pair["pair"], seed))
            fasta = write_pair_fasta(pair, outdir / "input.fasta")
            argv = [venv_bin("colabfold_batch"),
                    "--msa-mode", "single_sequence",
                    "--model-type", "alphafold2_multimer_v3",
                    "--num-models", str(AF_MODELS),
                    "--num-recycle", str(AF_RECYCLES),
                    "--recycle-early-stop-tolerance", str(AF_EARLY_STOP_TOLERANCE),
                    "--num-seeds", "1",
                    "--random-seed", str(seed),
                    "--data", state["af_data_dir"],
                    str(fasta), str(outdir / "out")]
            allowance = int(max(1, min(stage_left, inner)))
            timed_out = False
            try:
                res = run_tool(argv, "af2_%s_seed%d" % (pair["pair"], seed), allowance,
                               allow_timeout=True)
                timed_out = bool(res.get("timed_out"))
                wall = res["wall_s"] - state["overhead"]["subtract_time_s"]
                mt = parse_af_model_times(res["output"])
                ce = compile_excluded_seconds(mt)
                row = {"pair": pair["pair"], "seed": seed,
                       "status": "incomplete" if timed_out else "ok",
                       "incomplete": timed_out, "allowance_s": allowance,
                       "wall_s": wall, "hours": hours(wall),
                       "model_times_s": mt,
                       "compile_excluded_s": ce,
                       "compile_excluded_hours": hours(ce) if ce is not None else None,
                       "n_models": AF_MODELS, "recycles": AF_RECYCLES,
                       "early_stopping": "off", "msa_mode": "single_sequence",
                       "outdir": str(outdir), "log": res["log"], "argv": argv}
            except ToolError as exc:
                row = {"pair": pair["pair"], "seed": seed, "status": "failed",
                       "error": str(exc)[:2000], "argv": argv}
            append_row("af2", row, results)
            rows.append(row)
            state["af_rows"] = rows
            save_state(state)
            if row["status"] == "failed":
                raise ToolError("AlphaFold run failed: %s" % row["error"][:400])
            if row["status"] == "incomplete":
                # The call outlived the seconds the guard gave it. The row stays,
                # marked, and is not counted in the mean. The stage stops here.
                record_stop(state, "af2", "timeout",
                            "an AlphaFold call was stopped at its %d second allowance"
                            % allowance)
                save_state(state)
                raise GuardStop("AlphaFold call stopped at its allowance")
    state["af_rows"] = rows
    state["stages_done"].append("af2")
    save_state(state)
    return state


# ---------------------------------------------------------------------------
# Stage: dynamics speed
# ---------------------------------------------------------------------------

MD_WORKER_DOC = """Build, settle and time one explicit-solvent dynamics segment."""


def md_worker(spec_path: Path) -> int:
    """Run one dynamics segment in a separate process, so a cap can stop it.

    Heavy packages are imported here and nowhere else, which keeps the selftest
    free of them.
    """
    spec = json.loads(Path(spec_path).read_text())
    out = {"status": "failed", "error": None}
    try:
        from openmm import app, unit, LangevinMiddleIntegrator, Platform
        import openmm
        pdb = app.PDBFile(spec["complex_pdb"])
        ff = app.ForceField("amber14-all.xml", "amber14/tip3pfb.xml")
        chosen = None
        for pad in spec["paddings_nm"]:
            modeller = app.Modeller(pdb.topology, pdb.positions)
            modeller.deleteWater()
            modeller.addHydrogens(ff)
            modeller.addSolvent(ff, padding=pad * unit.nanometer, model="tip3p",
                                ionicStrength=0.15 * unit.molar)
            n_atoms = modeller.topology.getNumAtoms()
            if spec["atoms_min"] <= n_atoms <= spec["atoms_max"]:
                chosen = (pad, modeller, n_atoms)
                break
            if n_atoms > spec["atoms_max"]:
                chosen = (pad, modeller, n_atoms)
                break
        if chosen is None:
            raise RuntimeError("no padding produced a system inside the size window")
        pad, modeller, n_atoms = chosen
        out["padding_nm"] = pad
        out["n_atoms"] = n_atoms
        system = ff.createSystem(modeller.topology, nonbondedMethod=app.PME,
                                 nonbondedCutoff=1.0 * unit.nanometer,
                                 constraints=app.HBonds, rigidWater=True)
        integrator = LangevinMiddleIntegrator(300 * unit.kelvin, 1.0 / unit.picosecond,
                                              spec["timestep_fs"] * unit.femtoseconds)
        platform = Platform.getPlatformByName("CUDA")
        props = {"Precision": "mixed"}
        sim = app.Simulation(modeller.topology, system, integrator, platform, props)
        sim.context.setPositions(modeller.positions)
        out["platform"] = sim.context.getPlatform().getName()
        out["precision"] = "mixed"
        out["openmm_version"] = openmm.version.version
        sim.minimizeEnergy(maxIterations=spec["minimise_steps"])
        sim.context.setVelocitiesToTemperature(300 * unit.kelvin, spec["velocity_seed"])
        sim.step(spec["equil_steps"])
        traj = str(Path(spec["outdir"]) / "production.dcd")
        log = str(Path(spec["outdir"]) / "production_state.csv")
        sim.reporters.append(app.DCDReporter(traj, spec["report_interval"]))
        sim.reporters.append(app.StateDataReporter(
            log, spec["report_interval"], step=True, potentialEnergy=True,
            temperature=True, speed=True))
        t0 = time.time()
        sim.step(spec["production_steps"])
        out["production_wall_s"] = time.time() - t0
        out["trajectory"] = traj
        out["state_log"] = log
        out["frame_interval_steps"] = spec["report_interval"]
        out["frame_interval_ps"] = spec["report_interval"] * spec["timestep_fs"] / 1000.0
        out["engine_rate_lines"] = parse_engine_rate_lines(Path(log).read_text())
        out["status"] = "ok"
    except Exception as exc:                      # noqa: BLE001
        out["error"] = "%s: %s" % (type(exc).__name__, exc)
    Path(spec["result_path"]).write_text(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out["status"] == "ok" else 1


def build_complex_pdb(capsid_pdb: Path, pose_pdb: Path, out_path: Path):
    """Join the capsid half and the docked receptor pose into one file."""
    atoms = read_pdb_atoms(Path(capsid_pdb).read_text())
    for a in atoms:
        a["chain"] = "A"
    pose = read_pdb_atoms(Path(pose_pdb).read_text())
    for a in pose:
        a["chain"] = "B"
    write_pdb(atoms + pose, out_path)
    return out_path


def stage_md(state):
    """Time a half-nanosecond production segment on each docked complex."""
    results = RESULTS
    caps = state.get("caps") or caps_from_env()
    stage_start = now()
    rows = list(state.get("md_rows") or [])
    for item in (state.get("md_inputs") or []):
        if any(r["pair"] == item["pair"] for r in rows):
            continue
        stage_left = CEILINGS["md"] - (now() - stage_start)
        budget = min(MD_PER_COMPLEX_CEILING, stage_left)
        inner = tool_allowance_seconds(elapsed_of(state), caps["price_usd_per_hour"],
                                       caps["budget_left_usd"], caps["remote_timeout_s"])
        g = guard_check(elapsed_of(state), budget, caps["price_usd_per_hour"],
                        caps["budget_left_usd"], caps["remote_timeout_s"])
        if budget <= 0:
            record_stop(state, "md", "ceiling",
                        "the dynamics timings reached their %d second ceiling with %d of %d "
                        "complexes done" % (CEILINGS["md"], len(rows),
                                            len(state.get("md_inputs") or [])))
            save_state(state)
            raise GuardStop("dynamics stage ceiling reached")
        if not g["may_start"]:
            record_stop(state, "md", "guard",
                        "no time left for another complex: %s" % json.dumps(g))
            save_state(state)
            raise GuardStop("dynamics time guard")
        outdir = WORK / "md" / item["pair"]
        outdir.mkdir(parents=True, exist_ok=True)
        complex_pdb = build_complex_pdb(Path(item["capsid_pdb"]), Path(item["pose_pdb"]),
                                        outdir / "complex.pdb")
        spec_path = outdir / "spec.json"
        result_path = outdir / "md_result.json"
        jdump(spec_path, {
            "complex_pdb": str(complex_pdb), "outdir": str(outdir),
            "result_path": str(result_path),
            "paddings_nm": MD_PADDINGS_NM, "atoms_min": MD_ATOMS_MIN, "atoms_max": MD_ATOMS_MAX,
            "timestep_fs": MD_TIMESTEP_FS, "production_steps": MD_PRODUCTION_STEPS,
            "equil_steps": MD_EQUIL_STEPS, "minimise_steps": MD_MINIMISE_STEPS,
            "report_interval": MD_REPORT_INTERVAL, "velocity_seed": 0,
        })
        allowance = int(max(1, min(budget, inner)))
        try:
            res_tool = run_tool([venv_python(), str(Path(__file__).resolve()), "--worker", "md",
                                 "--spec", str(spec_path)],
                                "md_%s" % item["pair"], allowance, allow_timeout=True)
        except ToolError as exc:
            row = {"pair": item["pair"], "status": "failed", "error": str(exc)[:2000]}
            append_row("md", row, results)
            rows.append(row)
            state["md_rows"] = rows
            save_state(state)
            raise
        if res_tool.get("timed_out"):
            # The segment outlived its allowance and was stopped with its children.
            # The row is kept, marked, and left out of the median.
            row = {"pair": item["pair"], "status": "incomplete", "incomplete": True,
                   "allowance_s": allowance, "wall_s": res_tool["wall_s"],
                   "note": "the dynamics worker was stopped at its allowance"}
            append_row("md", row, results)
            rows.append(row)
            state["md_rows"] = rows
            record_stop(state, "md", "timeout",
                        "a dynamics segment was stopped at its %d second allowance" % allowance)
            save_state(state)
            raise GuardStop("dynamics segment stopped at its allowance")
        res = json.loads(result_path.read_text())
        if res["status"] != "ok":
            row = {"pair": item["pair"], "status": "failed", "error": res.get("error")}
            append_row("md", row, results)
            rows.append(row)
            state["md_rows"] = rows
            save_state(state)
            raise ToolError("dynamics run failed: %s" % res.get("error"))
        wall = res["production_wall_s"] - state["overhead"]["subtract_time_s"]
        wc_rate = ns_per_day_from_wallclock(MD_PRODUCTION_STEPS, MD_TIMESTEP_FS, wall)
        engine_rates = res.get("engine_rate_lines") or []
        engine_rate = median(engine_rates) if engine_rates else None
        rel, disagree = md_rate_disagreement(engine_rate, wc_rate)
        row = {"pair": item["pair"], "status": "ok", "n_atoms": res.get("n_atoms"),
               "padding_nm": res.get("padding_nm"), "steps": MD_PRODUCTION_STEPS,
               "timestep_fs": MD_TIMESTEP_FS, "production_wall_s": wall,
               "ns_per_day_wallclock": wc_rate, "ns_per_day_engine": engine_rate,
               "engine_rate_lines": engine_rates, "rate_relative_difference": rel,
               "atom_count_in_window": atom_count_ok(res.get("n_atoms")),
               "frame_interval_steps": res.get("frame_interval_steps"),
               "frame_interval_ps": res.get("frame_interval_ps"),
               "trajectory": res.get("trajectory"), "state_log": res.get("state_log"),
               "platform": res.get("platform"), "precision": res.get("precision"),
               "openmm_version": res.get("openmm_version"),
               "labels": [LABEL_MD_DISAGREE] if disagree else []}
        append_row("md", row, results)
        rows.append(row)
        state["md_rows"] = rows
        save_state(state)
    state["md_rows"] = rows
    state["stages_done"].append("md")
    save_state(state)
    return state


# ---------------------------------------------------------------------------
# Stage: storage
# ---------------------------------------------------------------------------

def stage_storage(state):
    """Measure the bytes one grid run writes, by artifact type."""
    results = RESULTS
    rows = []
    af_ok = [r for r in (state.get("af_rows") or []) if r.get("status") == "ok"]
    md_ok = [r for r in (state.get("md_rows") or []) if r.get("status") == "ok"]
    aux_ok = state["measured"].get("C3_rows") or []
    sub = state["overhead"]["subtract_bytes"]

    if af_ok:
        d = Path(af_ok[0]["outdir"])
        final_b, inter_b = split_final_and_intermediate(d)
        rows.append({"artifact": "alphafold_run", "path": str(d),
                     "apparent_bytes": max(0, apparent_bytes([d]) - sub),
                     "final_bytes": final_b, "intermediate_bytes": inter_b})
    if aux_ok:
        d = Path(aux_ok[0]["pose_path"]).parent.parent
        final_b, inter_b = split_final_and_intermediate(d)
        rows.append({"artifact": "docking_pair", "path": str(d),
                     "apparent_bytes": max(0, apparent_bytes([d]) - sub),
                     "final_bytes": final_b, "intermediate_bytes": inter_b})
    if md_ok:
        files = [p for p in (md_ok[0].get("trajectory"), md_ok[0].get("state_log")) if p]
        b = max(0, apparent_bytes(files) - sub)
        rows.append({"artifact": "md_segment", "path": ";".join(files),
                     "apparent_bytes": b, "final_bytes": b, "intermediate_bytes": 0,
                     "segment_ns": MD_PRODUCTION_NS,
                     "bytes_per_ns": b / MD_PRODUCTION_NS,
                     "frame_interval_steps": md_ok[0].get("frame_interval_steps")})
    for r in rows:
        append_row("storage", r, results)
    state["storage_rows"] = rows
    state["stages_done"].append("storage")
    save_state(state)
    return state


# ---------------------------------------------------------------------------
# Stage: the four decisions, the summary and the markers
# ---------------------------------------------------------------------------

def base_labels(state, which):
    labs = [LABEL_STANDIN, LABEL_ONE_BOX]
    labs += [l for l in state.get("labels", []) if l not in labs]
    if was_stopped(state) and LABEL_INCOMPLETE_RUN not in labs:
        labs.append(LABEL_INCOMPLETE_RUN)
    if which == "C1":
        labs.append(LABEL_C1_MSA)
    if which == "C3":
        labs.append(LABEL_C3_READING)
    if which == "C4":
        labs.append(LABEL_C4_SCALE)
    if which in ("C3", "C4"):
        labs.append("GPU: %s" % (state.get("hardware", {}).get("gpu_name") or "unknown"))
    return labs


def engine_block(state, which):
    v = state.get("versions") or {}
    if which == "C1":
        keys = ["alphafold_implementation", "colabfold_version", "alphafold_colabfold_version",
                "jax_version", "jaxlib_version", "af_params_archive_sha256"]
    elif which == "C2":
        keys = ["md_engine", "openmm_version", "md_precision", "md_platform", "md_build"]
    elif which == "C3":
        keys = ["docking_code", "lightdock_version"]
    else:
        keys = list(v.keys())
    block = {k: v.get(k) for k in keys}
    if which == "C1":
        block["af_params_archive_url"] = URL_AF_PARAMS
        block["build_flags"] = ["--msa-mode single_sequence",
                                "--model-type alphafold2_multimer_v3",
                                "--num-models %d" % AF_MODELS,
                                "--num-recycle %d" % AF_RECYCLES,
                                "--recycle-early-stop-tolerance %s" % AF_EARLY_STOP_TOLERANCE]
    if which == "C2":
        block["build_flags"] = ["PME", "1.0 nm cutoff", "HBonds constraints",
                                "LangevinMiddle integrator", "%s fs timestep" % MD_TIMESTEP_FS]
    if which == "C3":
        block["build_flags"] = ["fastdfire scoring", "seed_points 0", "--noxt --noh --now"]
    return block


def is_unmeasured(value, reasons) -> bool:
    """Was this input left without a measurement, rather than decided on one?

    A value that exists and met its minimum was measured, even when the band
    call is VOID because it sits near an edge. A missing value, or one below
    the stated minimum of finished work, was not.
    """
    return bool(value is None or any(r == LABEL_UNMEASURED or "below the minimum" in r
                                     for r in reasons))


def decide_c1(state):
    rows = [r for r in (state.get("af_rows") or []) if r.get("status") == "ok"]
    labels = base_labels(state, "C1")
    per_pair = {}
    for r in rows:
        per_pair.setdefault(r["pair"], []).append(r["wall_s"])
    spread = spread_check(per_pair)
    value = mean([r["hours"] for r in rows]) if rows else None
    decision, marginal = band_decision(value, CARD["C1"]["band"])
    reasons = []
    if not state["run_valid"]:
        decision, reasons = "VOID", reasons + ["run not valid"]
    if value is None:
        decision, reasons = "VOID", reasons + [LABEL_UNMEASURED]
    elif not c1_minimum_ok(rows):
        decision, reasons = "VOID", reasons + ["below the minimum: %s" % MINIMUMS["C1"]]
    if spread["halt"] == WRONG_VARIANCE_SOURCE:
        decision, reasons = "VOID", reasons + [LABEL_ZERO_SPREAD]
        labels.append(LABEL_ZERO_SPREAD)
    if spread["high_spread_pairs"]:
        labels.append(LABEL_SPREAD_HIGH)
    if not gpu_is_a100(state.get("hardware", {}).get("gpu_name")):
        decision, reasons = "VOID", reasons + [LABEL_NOT_A100]
        if LABEL_NOT_A100 not in labels:
            labels.append(LABEL_NOT_A100)
    ce = [r["compile_excluded_hours"] for r in rows if r.get("compile_excluded_hours")]
    values = {
        "measured": value, "unit": CARD["C1"]["unit"],
        "card_value": CARD["C1"]["value"], "band": CARD["C1"]["band"],
        "n": len(rows), "pairs_covered": sorted(per_pair.keys()),
        "per_run_hours": [r["hours"] for r in rows],
        "compile_excluded_mean_hours": mean(ce) if ce else None,
        "relative_sd_per_pair": spread["rel_sd"],
        "marginal": marginal, "void_reasons": reasons, "labels": labels,
        "unmeasured": is_unmeasured(value, reasons),
        "minimum": MINIMUMS["C1"],
        **gate_result(value),
    }
    return decision, values, rows


def decide_c2(state):
    rows = [r for r in (state.get("md_rows") or []) if r.get("status") == "ok"]
    labels = base_labels(state, "C2")
    wc = [r["ns_per_day_wallclock"] for r in rows if r.get("ns_per_day_wallclock")]
    value = median(wc) if wc else None
    decision, marginal = band_decision(value, CARD["C2"]["band"])
    reasons = []
    if not state["run_valid"]:
        decision, reasons = "VOID", reasons + ["run not valid"]
    if value is None:
        decision, reasons = "VOID", reasons + [LABEL_UNMEASURED]
    elif len(rows) < 2:
        decision, reasons = "VOID", reasons + ["below the minimum: %s" % MINIMUMS["C2"]]
    bad_atoms = [r["pair"] for r in rows if not atom_count_ok(r.get("n_atoms"))]
    if bad_atoms:
        decision, reasons = "VOID", reasons + ["atom count outside %d to %d for %s"
                                               % (MD_ATOMS_MIN, MD_ATOMS_MAX, ",".join(bad_atoms))]
    if any(LABEL_MD_DISAGREE in (r.get("labels") or []) for r in rows):
        labels.append(LABEL_MD_DISAGREE)
    if not gpu_is_a100(state.get("hardware", {}).get("gpu_name")):
        decision, reasons = "VOID", reasons + [LABEL_NOT_A100]
        if LABEL_NOT_A100 not in labels:
            labels.append(LABEL_NOT_A100)
    values = {
        "measured": value, "unit": CARD["C2"]["unit"],
        "card_value": CARD["C2"]["value"], "band": CARD["C2"]["band"],
        "n": len(rows),
        "ns_per_day_wallclock": wc,
        "ns_per_day_engine": [r.get("ns_per_day_engine") for r in rows],
        "atom_counts": [r.get("n_atoms") for r in rows],
        "atom_count_window": [MD_ATOMS_MIN, MD_ATOMS_MAX],
        "precision": "mixed", "marginal": marginal, "void_reasons": reasons,
        "unmeasured": is_unmeasured(value, reasons),
        "labels": labels, "minimum": MINIMUMS["C2"],
        "gate": GATE_NOT_APPLICABLE,
    }
    return decision, values, rows


def decide_c3(state):
    rows = state["measured"].get("C3_rows") or []
    labels = base_labels(state, "C3")
    value = mean([r["hours"] for r in rows]) if rows else None
    decision, marginal = band_decision(value, CARD["C3"]["band"])
    reasons = []
    if not state["run_valid"]:
        decision, reasons = "VOID", reasons + ["run not valid"]
    if value is None:
        decision, reasons = "VOID", reasons + [LABEL_UNMEASURED]
    elif len(rows) < 2:
        decision, reasons = "VOID", reasons + ["below the minimum: %s" % MINIMUMS["C3"]]
    values = {
        "measured": value, "unit": CARD["C3"]["unit"],
        "card_value": CARD["C3"]["value"], "band": CARD["C3"]["band"],
        "n": len(rows), "per_pair_hours": [r["hours"] for r in rows],
        "included": ("docking, interface analysis (contacts at 4.5 Angstrom, interface residues, "
                     "distance to the nearest threefold axis, site class) and writing the "
                     "call-table row"),
        "excluded": "installs, downloads and setup",
        "marginal": marginal, "void_reasons": reasons, "labels": labels,
        "unmeasured": is_unmeasured(value, reasons),
        "minimum": MINIMUMS["C3"], "gate": GATE_NOT_APPLICABLE,
    }
    return decision, values, rows


def decide_c4(state):
    rows = state.get("storage_rows") or []
    labels = base_labels(state, "C4")
    by_type = {r["artifact"]: r for r in rows}
    have_all = all(t in by_type for t in ARTIFACT_TYPES)
    per_run = sum(r["apparent_bytes"] for r in rows) if rows else None
    per_run_final = sum(r["final_bytes"] for r in rows) if rows else None
    value = storage_gib(per_run, GRID_RUNS) if have_all else None
    decision, marginal = band_decision(value, CARD["C4"]["band"])
    reasons = []
    if not state["run_valid"]:
        decision, reasons = "VOID", reasons + ["run not valid"]
    if value is None:
        decision, reasons = "VOID", reasons + [LABEL_UNMEASURED]
    elif not have_all:
        decision, reasons = "VOID", reasons + ["below the minimum: %s" % MINIMUMS["C4"]]
    md_row = by_type.get("md_segment")
    values = {
        "measured": value, "unit": CARD["C4"]["unit"],
        "card_value": CARD["C4"]["value"], "band": CARD["C4"]["band"],
        "n": len(rows),
        "bytes_per_run": per_run,
        "gib_432_runs": storage_gib(per_run, GRID_RUNS_ALT) if per_run else None,
        "gib_216_runs_intermediates_deleted":
            storage_gib(per_run_final, GRID_RUNS) if per_run_final else None,
        "md_bytes_per_ns": md_row.get("bytes_per_ns") if md_row else None,
        "md_frame_interval_steps": md_row.get("frame_interval_steps") if md_row else None,
        "per_artifact": rows, "marginal": marginal, "void_reasons": reasons,
        "unmeasured": is_unmeasured(value, reasons),
        "labels": labels, "minimum": MINIMUMS["C4"], "gate": GATE_NONE,
    }
    return decision, values, rows


DECIDERS = {"C1": decide_c1, "C2": decide_c2, "C3": decide_c3, "C4": decide_c4}
METRICS = {
    "C1": "Mean wall-clock hours of one whole AlphaFold-Multimer prediction call (af2_h_per_run)",
    "C2": "Median wall-clock nanoseconds per day over complexes (md_ns_per_day_a100)",
    "C3": "Mean wall-clock hours per pair of docking and analysis (aux_h_per_pair)",
    "C4": "Gibibytes the 216-run grid writes, scaled from one measured run (n_storage_gib)",
}


def write_unit_scale_record(state):
    """Raw readings beside converted ones. Written before any band is compared."""
    af = [r for r in (state.get("af_rows") or []) if r.get("status") == "ok"]
    md = [r for r in (state.get("md_rows") or []) if r.get("status") == "ok"]
    st = state.get("storage_rows") or []
    values = {
        "raw_alphafold_seconds": [r["wall_s"] for r in af],
        "alphafold_hours": [r["hours"] for r in af],
        "alphafold_model_times_s": [r.get("model_times_s") for r in af],
        "md_engine_rate_lines_with_wallclock": [
            {"pair": r["pair"], "engine_rate_lines": r.get("engine_rate_lines"),
             "ns_per_day_engine": r.get("ns_per_day_engine"),
             "ns_per_day_wallclock": r.get("ns_per_day_wallclock"),
             "production_wall_s": r.get("production_wall_s"),
             "steps": r.get("steps"), "timestep_fs": r.get("timestep_fs")}
            for r in md],
        "raw_bytes_per_artifact": [{"artifact": r["artifact"],
                                    "apparent_bytes": r["apparent_bytes"]} for r in st],
        "worked_conversions": {
            "1800_s_to_hours": hours(1800),
            "250000_steps_2_fs_335_s_to_ns_per_day":
                ns_per_day_from_wallclock(250000, 2.0, 335.0),
            "1_gib_per_run_over_216_runs": storage_gib(float(1 << 30), GRID_RUNS),
        },
        "labels": base_labels(state, "units"),
        "started_utc": utc(state.get("t0")), "ended_utc": utc(),
        **hardware_block(state),
    }
    return write_record(state, "endpoint-control-unit-scale",
                        cell={"control": "unit_and_scale", "tag": TAG, "arm": "control"},
                        inputs=[], metric="Raw readings beside the converted numbers",
                        values=values, threshold={}, decision_rule=RULE_UNITS,
                        decision="NOT_A_DECISION",
                        notes="No band is compared before this record exists.")


def write_input_record(state, which, decision, values, rows):
    prov = load_provenance()
    rows_path = RESULTS / ("rows_%s_tag-%s.jsonl" % (
        {"C1": "af2", "C2": "md", "C3": "aux", "C4": "storage"}[which], TAG))
    inputs = describe_inputs(prov, [(rows_path, len(rows))])
    if state.get("structure_path"):
        inputs += describe_inputs(prov, [(state["structure_path"], None)])
    # What was installed and from where: the pip report names every wheel's URL
    # and archive hash, the apt file every package's version and hash.
    for extra in ("pip_report.json", "apt_packages.txt", "smoke_check.txt"):
        if (RESULTS / extra).exists():
            inputs += describe_inputs(prov, [(RESULTS / extra, None)])
    values = dict(values)
    values.update(hardware_block(state))
    values.update(engine_block(state, which))
    values.setdefault("started_utc", utc(state.get("t0")))
    values["ended_utc"] = utc()
    return write_record(state, "endpoint-%s" % which,
                        cell={"endpoint": which, "input": CARD[which]["name"], "tag": TAG,
                              "arm": {"C1": "af2", "C2": "md", "C3": "aux",
                                      "C4": "storage"}[which]},
                        inputs=inputs, metric=METRICS[which], values=values,
                        threshold={"band": CARD[which]["band"],
                                   "marginal_fraction_of_edge": MARGINAL_FRACTION,
                                   "card_value": CARD[which]["value"],
                                   "minimum": MINIMUMS[which]},
                        decision_rule=RULE_INPUT, decision=decision,
                        rows=rows if which != "C1" else [
                            {k: v for k, v in r.items() if k != "output"} for r in rows])


def void_unmeasured(state, reason):
    """Write a not-decided record for every input that has none yet."""
    for which in ("C1", "C2", "C3", "C4"):
        if ("endpoint-%s" % which) in state["records_written"]:
            continue
        values = {"measured": None, "unit": CARD[which]["unit"],
                  "card_value": CARD[which]["value"], "band": CARD[which]["band"],
                  "n": 0, "marginal": False, "unmeasured": True,
                  "void_reasons": [LABEL_UNMEASURED, reason],
                  "labels": base_labels(state, which), "minimum": MINIMUMS[which]}
        if which == "C1":
            values.update(gate_result(None))
        elif which in ("C2", "C3"):
            values["gate"] = GATE_NOT_APPLICABLE
        else:
            values["gate"] = GATE_NONE
        write_input_record(state, which, "VOID", values, [])


def write_summary(state, exit_code):
    """Restate every record. Add no decision of its own."""
    records = {}
    for path in sorted(RESULTS.glob("endpoint-*_tag-%s.json" % TAG)):
        rec = json.loads(path.read_text())
        records[path.name] = {"metric": rec.get("metric"), "decision": rec.get("decision"),
                              "run_valid": rec.get("run_valid"),
                              "measured": (rec.get("values") or {}).get("measured"),
                              "unit": (rec.get("values") or {}).get("unit"),
                              "band": (rec.get("values") or {}).get("band"),
                              "card_value": (rec.get("values") or {}).get("card_value"),
                              "labels": (rec.get("values") or {}).get("labels"),
                              "void_reasons": (rec.get("values") or {}).get("void_reasons")}
    c1 = json.loads((RESULTS / ("endpoint-C1_tag-%s.json" % TAG)).read_text()) \
        if (RESULTS / ("endpoint-C1_tag-%s.json" % TAG)).exists() else {}
    c1v = c1.get("values") or {}
    per_pair = {}
    for r in (state.get("af_rows") or []):
        if r.get("status") == "ok":
            per_pair.setdefault(r["pair"], []).append(r["wall_s"])
    spread = spread_check(per_pair)
    high = [{"pair": p, "relative_sd": spread["rel_sd"].get(p), "label": LABEL_SPREAD_HIGH}
            for p in spread["high_spread_pairs"]]
    summary = {
        "what_this_run_decides": (
            "This run decides the stand-in protocol only. The pairs are built from chains of one "
            "published entry, not from the card's own pairs. The card's 54-run pilot and 216-run "
            "grid were not run, and the card's own decision rule was not evaluated."),
        "repeat_note": ("Serial and parallel runs here are repeats on one box. They are not "
                        "independent confirmation of each other."),
        "incomplete_run": was_stopped(state),
        "incomplete_run_label": LABEL_INCOMPLETE_RUN if was_stopped(state) else None,
        "stops": state.get("stops"),
        "remote_timeout_s_seen": (state.get("caps") or {}).get("remote_timeout_seen"),
        "remote_timeout_s_used": (state.get("caps") or {}).get("remote_timeout_s"),
        "remote_timeout_label": (state.get("caps") or {}).get("labels"),
        "tag": TAG,
        "run_valid": state["run_valid"],
        "run_valid_reasons": state["run_valid_reasons"],
        "exit_code": exit_code,
        "records": records,
        "gate": {"applies_to": GATE_INPUT, "gate_value": GATE_VALUE,
                 "gate_pass": c1v.get("gate_pass"), "gate_else": GATE_ELSE,
                 "note": "The gate is reported. The run never branched on it."},
        "high_spread_pairs": high,
        "stages_done": state.get("stages_done"),
        "hardware": hardware_block(state),
        "versions": state.get("versions"),
        "downloads": state.get("downloads"),
        "pairs": state.get("pairs"),
        "caps": state.get("caps"),
        "cost_so_far_usd": cost_usd(elapsed_of(state),
                                    (state.get("caps") or caps_from_env())["price_usd_per_hour"]),
        "elapsed_s": elapsed_of(state),
        "this_summary_makes_no_decision_of_its_own": True,
        "written_utc": utc(),
    }
    jdump(RESULTS / ("%s_summary.json" % TAG), summary)
    return summary


def stage_endpoints(state):
    """The unit record first, then the four decisions, then the summary."""
    write_unit_scale_record(state)
    for which in ("C1", "C2", "C3", "C4"):
        decision, values, rows = DECIDERS[which](state)
        write_input_record(state, which, decision, values, rows)
    state["stages_done"].append("endpoints")
    save_state(state)
    return state


def finish(state, exit_code):
    write_run_valid(state)
    write_summary(state, exit_code)
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "RUN_DONE").write_text("%d\n" % exit_code)
    state["exit_code"] = exit_code
    save_state(state)
    return exit_code


# ---------------------------------------------------------------------------
# Stage driving
# ---------------------------------------------------------------------------

COARSE = {
    "extract": ["downloads", "controls", "anchor"],
    "generate": ["aux", "af2", "md", "storage"],
    "endpoints": ["endpoints"],
}
FINE = {
    "downloads": stage_downloads,
    "controls": stage_controls,
    "anchor": stage_anchor,
    "aux": stage_aux,
    "af2": stage_af2,
    "md": stage_md,
    "storage": stage_storage,
    "endpoints": stage_endpoints,
}


STAGE_ESTIMATES = {"downloads": 600, "controls": 120, "anchor": 400, "aux": 600,
                   "af2": 700, "md": 600, "storage": 60, "endpoints": 60}


def _run_stages(names, stages=None, state=None, estimates=None):
    """Run the named stages in order and return the exit code.

    The stage functions come in as an argument so the selftest can run this
    whole flow with stand-ins and check what each kind of stop produces.

    Three kinds of ending, kept apart on purpose:
      * A stop by the clock, the money or a stage ceiling. The work that
        finished keeps its decision, the rest is not decided, the run stays
        valid, and the code is 3.
      * A missed anchor or a failed timer control or a broken tool. Every input
        is not decided, the run is marked not valid, and the code is 4 or 2.
      * Everything measured. Code 0.
    """
    stages = stages or FINE
    estimates = estimates or STAGE_ESTIMATES
    state = state if state is not None else load_state()
    if state.get("t0") is None:
        state["t0"] = read_t0(RESULTS)
    save_state(state)
    try:
        for name in names:
            if name == "endpoints":
                continue              # the endpoints stage always runs, at the end
            caps = state.get("caps") or caps_from_env()
            state["caps"] = caps
            est = estimates.get(name, 60)
            g = guard_check(elapsed_of(state), est, caps["price_usd_per_hour"],
                            caps["budget_left_usd"], caps["remote_timeout_s"])
            if not g["may_start"]:
                # The guard refuses to start this stage. Later stages may still
                # fit, so the loop goes on; this stage's inputs stay undecided.
                record_stop(state, name, "guard",
                            "stage %s not started: %s" % (name, json.dumps(g)))
                save_state(state)
                continue
            print("[%s] start, elapsed %.0f s, cost so far USD %.2f"
                  % (name, elapsed_of(state), g["cost_so_far_usd"]))
            try:
                state = stages[name](state)
            except GuardStop as exc:
                # The stage stopped itself on the clock or on its ceiling. It is
                # not in the finished list; the next stage still gets its turn.
                print("[guard] %s" % exc)
                if not was_stopped(state):
                    record_stop(state, name, "guard", str(exc))
                save_state(state)
                continue
    except AnchorMiss as exc:
        if state["run_valid"]:
            set_run_invalid(state, "anchor redocking did not reproduce the published "
                                   "interface: %s" % exc)
        void_unmeasured(state, "anchor miss")
        return finish(state, EXIT_ANCHOR)
    except HarnessInvalid as exc:
        set_run_invalid(state, "harness control failed: %s" % exc)
        void_unmeasured(state, "harness control failed")
        return finish(state, EXIT_INFRA)
    except ToolError as exc:
        print("[infra] %s" % exc)
        set_run_invalid(state, "declared tool, install or download failed: %s" % exc)
        void_unmeasured(state, "declared tool, install or download failed")
        return finish(state, EXIT_INFRA)
    except Exception as exc:                      # noqa: BLE001
        print("[infra] unexpected failure: %s: %s" % (type(exc).__name__, exc))
        set_run_invalid(state, "harness failure: %s: %s" % (type(exc).__name__, exc))
        void_unmeasured(state, "harness failure")
        return finish(state, EXIT_INFRA)

    # The endpoint stage runs whatever stopped above, whenever it was asked for.
    if "endpoints" in names:
        try:
            if "endpoints" not in state["stages_done"]:
                state = stages["endpoints"](state)
        except Exception as exc:                  # noqa: BLE001
            print("[infra] the endpoint stage failed: %s: %s" % (type(exc).__name__, exc))
            set_run_invalid(state, "endpoint stage failed: %s: %s" % (type(exc).__name__, exc))
            void_unmeasured(state, "endpoint stage failed")
            return finish(state, EXIT_INFRA)
        void_unmeasured(state, "not reached before the run ended")
        return finish(state, EXIT_GUARD if was_stopped(state) else EXIT_OK)
    write_run_valid(state)
    save_state(state)
    return EXIT_GUARD if was_stopped(state) else EXIT_OK


def run_stages(names, stages=None, state=None, estimates=None, runner=None):
    """Drive the flow with the stage functions and the tool runner injected.

    Both come in as arguments so the selftest can run the whole flow with
    stand-ins. When a tool runner is given, every tool call the stages make
    goes through it instead of the real one.
    """
    global run_tool
    saved_runner = run_tool
    if runner is not None:
        run_tool = runner
    try:
        return _run_stages(names, stages, state, estimates)
    finally:
        run_tool = saved_runner


def fail_stage(stage, reason, exit_code):
    """Record, from the on-box script, that a stage ended badly, then stop.

    A broken install, download, smoke check or tool is the machine failing: the
    run is not valid. Running out of clock or money is not: the finished inputs
    keep their decisions and only the unfinished ones are left undecided.
    """
    state = load_state()
    if exit_code in (EXIT_INFRA, EXIT_ANCHOR):
        set_run_invalid(state, "%s failed: %s" % (stage, reason))
    else:
        record_stop(state, stage, "timeout", reason)
    void_unmeasured(state, "%s: %s" % (stage, reason))
    return finish(state, exit_code)


# ---------------------------------------------------------------------------
# Selftest. Standard library only. No GPU. No network. No tool runs.
# ---------------------------------------------------------------------------

def _selftest() -> int:
    sys.dont_write_bytecode = True    # leave no compiled copies beside the checked-in files
    checks = []

    def check(name, got, want):
        ok = got == want
        checks.append((name, ok, got, want))

    def close(name, got, want, tol=1e-6):
        ok = got is not None and abs(got - want) <= tol
        checks.append((name, ok, got, want))

    # --- units and simple arithmetic ---------------------------------------
    close("1800 seconds is 0.5 hours", hours(1800), 0.5)
    close("7200 s install excluded, 1800 s docking is 0.5 h", hours(9000 - 7200), 0.5)
    close("250000 steps of 2 fs in 335 s is 128.96 ns/day",
          round(ns_per_day_from_wallclock(250000, 2.0, 335.0), 2), 128.96)
    check("median of 100, 129, 500 is 129", median([100, 129, 500]), 129)
    close("3600 s at 1.99 costs 1.99", cost_usd(3600, 1.99), 1.99)
    close("7200 s at 1.99 costs 3.98", cost_usd(7200, 1.99), 3.98)

    # --- cost and time guard -----------------------------------------------
    close("price 1.99 budget 5 timeout 7200 stops at the clock cap",
          stop_at_seconds(1.99, 5, 7200), 7200.0)
    check("price 1.99 money cap is later than the clock cap",
          round(5 / 1.99 * 3600) > 7200, True)
    close("price 2.50 makes both caps coincide", stop_at_seconds(2.50, 5, 7200), 7200.0)
    close("price 3.00 stops at the money cap", stop_at_seconds(3.00, 5, 7200), 6000.0)
    g = guard_check(6000, 900, 1.99, 5, 7200)
    check("a stage longer than the time left is not started", g["may_start"], False)
    g2 = guard_check(100, 300, 1.99, 5, 7200)
    check("a stage inside the time left is started", g2["may_start"], True)

    # --- the inner and outer stop arithmetic (the checklist's own numbers) ---
    close("the stage allowance keeps the margin and the endpoints slot back",
          guard_check(0, 1, 1.99, 5, 7200)["seconds_left"], 7200 - 500.0)
    close("the inner tool stop is stop_at minus elapsed minus 700",
          tool_allowance_seconds(0, 1.99, 5, 7200), 6500.0)
    close("the outer kill is stop_at minus elapsed minus 600",
          stop_at_seconds(1.99, 5, 7200) - 0 - OUTER_KILL_RESERVE_SECONDS, 6600.0)
    close("the inner stop fires 100 seconds before the outer kill",
          (stop_at_seconds(1.99, 5, 7200) - OUTER_KILL_RESERVE_SECONDS)
          - tool_allowance_seconds(0, 1.99, 5, 7200), 100.0)
    close("a planted 3600 second cap moves the inner stop with it",
          tool_allowance_seconds(100, 1.99, 5, 3600), 3600 - 100 - 700.0)

    # --- band decisions, input 1 -------------------------------------------
    b1 = CARD["C1"]["band"]
    check("C1 0.5 passes", band_decision(0.5, b1)[0], "PASS")
    check("C1 1.5 fails", band_decision(1.5, b1)[0], "FAIL")
    check("C1 0.1 fails", band_decision(0.1, b1)[0], "FAIL")
    check("C1 1.2 is too near an edge", band_decision(1.2, b1), ("VOID", True))
    check("C1 0.21 is too near an edge", band_decision(0.21, b1), ("VOID", True))
    check("C1 1.1 passes", band_decision(1.1, b1)[0], "PASS")
    check("C1 1.1 misses the card's gate", gate_result(1.1)["gate_pass"], False)
    check("C1 1.1 carries the fallback text", gate_result(1.1)["gate_else"], GATE_ELSE)
    check("C1 0.9 passes the card's gate", gate_result(0.9)["gate_pass"], True)
    check("C1 0.9 passes the band", band_decision(0.9, b1)[0], "PASS")

    # --- band decisions, inputs 2 to 4 -------------------------------------
    b2 = CARD["C2"]["band"]
    check("C2 129 passes", band_decision(129, b2)[0], "PASS")
    check("C2 40 fails", band_decision(40, b2)[0], "FAIL")
    check("C2 400 fails", band_decision(400, b2)[0], "FAIL")
    check("C2 56 is too near an edge", band_decision(56, b2), ("VOID", True))
    check("C2 60 passes", band_decision(60, b2)[0], "PASS")
    check("C2 330 is too near an edge", band_decision(330, b2), ("VOID", True))
    b3 = CARD["C3"]["band"]
    check("C3 1.0 passes", band_decision(1.0, b3)[0], "PASS")
    check("C3 0.2 fails", band_decision(0.2, b3)[0], "FAIL")
    check("C3 4.0 fails", band_decision(4.0, b3)[0], "FAIL")
    check("C3 0.3333 is too near an edge", band_decision(0.3333, b3), ("VOID", True))
    check("C3 3.2 is too near an edge", band_decision(3.2, b3), ("VOID", True))
    check("C3 0.5 passes", band_decision(0.5, b3)[0], "PASS")
    check("C3 2.5 passes", band_decision(2.5, b3)[0], "PASS")
    b4 = CARD["C4"]["band"]
    check("C4 216.0 passes", band_decision(216.0, b4)[0], "PASS")
    check("C4 21.6 fails", band_decision(21.6, b4)[0], "FAIL")
    check("C4 864.0 fails", band_decision(864.0, b4)[0], "FAIL")
    check("C4 626.4 is too near an edge", band_decision(626.4, b4), ("VOID", True))
    check("C4 75.6 passes", band_decision(75.6, b4)[0], "PASS")

    # --- storage arithmetic -------------------------------------------------
    close("1 GiB per run over 216 runs is 216 GiB", storage_gib(float(1 << 30), 216), 216.0)
    close("1 GiB per run over 432 runs is 432 GiB", storage_gib(float(1 << 30), 432), 432.0)
    close("0.1 GiB per run is 21.6 GiB", storage_gib(0.1 * GIB, 216), 21.6, 1e-9)
    close("4.0 GiB per run is 864 GiB", storage_gib(4.0 * GIB, 216), 864.0, 1e-9)
    close("2.9 GiB per run is 626.4 GiB", storage_gib(2.9 * GIB, 216), 626.4, 1e-9)
    close("0.35 GiB per run is 75.6 GiB", storage_gib(0.35 * GIB, 216), 75.6, 1e-9)
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "a.bin").write_bytes(b"x" * 1000)
        (d / "b.bin").write_bytes(b"y" * 24)
        check("files of 1000 and 24 bytes sum to 1024", apparent_bytes([d]), 1024)
        (d / "model_unrelaxed.pdb").write_bytes(b"z" * 100)
        fin, inter = split_final_and_intermediate(d)
        check("intermediate files are counted apart", (fin, inter), (1024, 100))

    # --- parsers ------------------------------------------------------------
    smi = "NVIDIA A100-SXM4-40GB, 570.148.08\n"
    check("GPU name is read", parse_nvidia_smi(smi)["gpu_name"], "NVIDIA A100-SXM4-40GB")
    check("driver is read", parse_nvidia_smi(smi)["driver_version"], "570.148.08")
    check("an A100 is recognised", gpu_is_a100("NVIDIA A100-SXM4-40GB"), True)
    check("another GPU is not an A100", gpu_is_a100("NVIDIA L40S"), False)
    check("CUDA runtime is read", parse_cuda_version("CUDA Version: 12.8 "), "12.8")
    md_log = ('#"Step","Potential Energy (kJ/mole)","Temperature (K)","Speed (ns/day)"\n'
              '5000,-1.2e6,300.1,101.5\n10000,-1.2e6,299.8,128.96\n')
    check("engine rate lines are read", parse_engine_rate_lines(md_log), [101.5, 128.96])
    check("engine rate median", median(parse_engine_rate_lines(md_log)), 115.23)
    af_log = ("alphafold2_multimer_v3_model_1_seed_000 took 300.0s (20 recycles)\n"
              "alphafold2_multimer_v3_model_2_seed_000 took 60.0s (20 recycles)\n"
              "alphafold2_multimer_v3_model_3_seed_000 took 62.0s (20 recycles)\n"
              "alphafold2_multimer_v3_model_4_seed_000 took 58.0s (20 recycles)\n"
              "alphafold2_multimer_v3_model_5_seed_000 took 60.0s (20 recycles)\n")
    mt = parse_af_model_times(af_log)
    check("five model times are read", len(mt), 5)
    close("the model times sum to 540 s", sum(t for _, t in mt), 540.0)
    close("compilation excluded gives 300 s", compile_excluded_seconds(mt), 300.0)
    rank = "swarm pose score\n0 1 12.5\n0 2 30.0\n"
    check("the docking table is ranked best first", parse_docking_rank_table(rank)[0]["score"], 30.0)

    # --- structure reading and geometry ------------------------------------
    mini_cif = (
        "data_test\nloop_\n_atom_site.group_PDB\n_atom_site.id\n_atom_site.type_symbol\n"
        "_atom_site.label_atom_id\n_atom_site.label_alt_id\n_atom_site.label_comp_id\n"
        "_atom_site.auth_asym_id\n_atom_site.auth_seq_id\n_atom_site.Cartn_x\n"
        "_atom_site.Cartn_y\n_atom_site.Cartn_z\n_atom_site.pdbx_PDB_model_num\n"
        "ATOM 1 N N . ALA A 1 0.000 0.000 0.000 1\n"
        "ATOM 2 C CA . ALA A 1 1.000 0.000 0.000 1\n"
        "ATOM 3 C CA . GLY A 2 2.000 0.000 0.000 1\n"
        "ATOM 4 C CA . VAL B 1 3.000 0.000 0.000 1\n"
        "HETATM 5 O O . HOH A 3 9.000 0.000 0.000 1\n"
        "ATOM 6 C CA . ALA A 1 1.000 0.000 0.000 2\n"
        "#\n")
    atoms = parse_cif_atoms(mini_cif)
    check("only model one protein atoms are read", len(atoms), 4)
    ch = chains_from_atoms(atoms)
    check("two chains are found", sorted(ch.keys()), ["A", "B"])
    check("chain A reads as a two residue sequence", chain_sequence(ch["A"]), "AG")
    check("quoted atom names survive", cif_tokens("ATOM \"O5'\" 1"), ["ATOM", "O5'", "1"])
    a_set = [{"chain": "A", "resseq": 1, "atom": "CA", "element": "C", "x": 0.0, "y": 0, "z": 0},
             {"chain": "A", "resseq": 2, "atom": "CA", "element": "C", "x": 10.0, "y": 0, "z": 0}]
    b_set = [{"chain": "B", "resseq": 1, "atom": "CA", "element": "C", "x": 3.0, "y": 0, "z": 0}]
    check("a contact inside 4.5 Angstrom is found", len(contact_pairs(a_set, b_set)), 1)
    native = {(("A", i), ("B", 1)) for i in range(1, 7)}
    pose = {(("A", i), ("B", 1)) for i in range(1, 4)}
    close("3 of 6 published contacts is an overlap of 0.5", contact_overlap(native, pose), 0.5)
    base = [(0.0, 0.0, 0.0), (1.0, 2.0, 3.0)]
    shifted = [(5.0, 0.0, 0.0), (6.0, 2.0, 3.0)]
    close("a 5 Angstrom shift along x gives an RMSD of 5.0", rmsd_direct(base, shifted), 5.0)
    axis = threefold_axis([(0.0, 0.0, 0.0), (3.0, 0.0, 0.0), (0.0, 3.0, 0.0)])
    close("the axis distance is the in-plane distance",
          distance_to_axis((1.0, 1.0, 50.0), axis), 0.0, 1e-9)
    close("a point off the axis is measured", distance_to_axis((1.0, 5.0, 0.0), axis), 4.0, 1e-9)
    check("no axis without three copies", threefold_axis([(0, 0, 0), (1, 1, 1)]), None)
    check("site class far from the axis", site_class(40.0), "floor")
    check("site class next to the axis", site_class(5.0), "threefold-spike-proximal")
    check("ten contacts is a bind call", bind_call(10), "bind")
    check("nine contacts is a no-bind call", bind_call(9), "no-bind")
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.pdb"
        write_pdb(atoms, p)
        back = read_pdb_atoms(p.read_text())
        check("a written structure reads back with the same atom count", len(back), len(atoms))
        close("a written coordinate survives the round trip", back[1]["x"], 1.0, 1e-3)

    # --- the anchor's planted cases ----------------------------------------
    check("overlap 0.50 with a bad RMSD still passes",
          anchor_decision(0.50, 9.0, 1.0, "bind", "bind")["pass"], True)
    check("overlap 0.49 with RMSD 5.0 passes",
          anchor_decision(0.49, 5.0, 1.0, "bind", "bind")["pass"], True)
    check("overlap 0.49 with RMSD 5.01 misses",
          anchor_decision(0.49, 5.01, 1.0, "bind", "bind")["pass"], False)
    check("serial and parallel 2.0 apart with equal calls passes",
          anchor_decision(0.6, 9.0, 2.0, "bind", "bind")["pass"], True)
    check("serial and parallel 2.01 apart misses",
          anchor_decision(0.6, 9.0, 2.01, "bind", "bind")["pass"], False)
    check("identical poses with different calls miss",
          anchor_decision(0.6, 9.0, 0.0, "bind", "no-bind")["pass"], False)

    # --- harness controls ---------------------------------------------------
    check("62.9 s for a 60 s sleep passes", sleep_check(62.9)["pass"], True)
    check("63.1 s for a 60 s sleep fails", sleep_check(63.1)["pass"], False)
    sp_ok = spread_check({"pair1": [1800.0, 1830.0, 1790.0]})
    check("timings that differ pass the spread check", sp_ok["halt"], None)
    sp_zero = spread_check({"pair1": [1800.0, 1800.0, 1800.0]})
    check("identical timings halt as the wrong variance source",
          sp_zero["halt"], WRONG_VARIANCE_SOURCE)
    check("identical timings carry the zero spread label",
          LABEL_ZERO_SPREAD in sp_zero["labels"], True)
    check("a relative spread of 0.6 only warns", labels_for_rel_sd(0.6), [LABEL_SPREAD_HIGH])
    check("a relative spread of 0.1 says nothing", labels_for_rel_sd(0.1), [])
    check("an empty run of 0.5 s and 100 KiB passes",
          empty_run_check(0.5, 100 * 1024)["pass"], True)
    check("an empty run of 5 s triggers the subtraction",
          empty_run_check(5.0, 1000)["labels"], [LABEL_OVERHEAD])
    check("an empty run writing 2 MiB triggers the subtraction",
          empty_run_check(0.5, 2 * 1024 * 1024)["labels"], [LABEL_OVERHEAD])
    check("the subtracted time is the measured excess",
          empty_run_check(5.0, 1000)["subtract_time_s"], 5.0)

    # --- minimums and size windows -----------------------------------------
    three_pairs = [{"pair": "pair%d" % i, "status": "ok"} for i in (1, 2, 3)]
    check("three runs over three pairs meet the minimum", c1_minimum_ok(three_pairs), True)
    check("two runs do not meet the minimum", c1_minimum_ok(three_pairs[:2]), False)
    missing = [{"pair": "pair1", "status": "ok"}, {"pair": "pair1", "status": "ok"},
               {"pair": "pair2", "status": "ok"}]
    check("three runs missing a pair do not meet the minimum", c1_minimum_ok(missing), False)
    check("119999 atoms is outside the window", atom_count_ok(119999), False)
    check("180001 atoms is outside the window", atom_count_ok(180001), False)
    check("150000 atoms is inside the window", atom_count_ok(150000), True)
    rel, dis = md_rate_disagreement(100.0, 94.0)
    check("rates 6 percent apart disagree", dis, True)
    rel2, dis2 = md_rate_disagreement(100.0, 98.0)
    check("rates 2 percent apart agree", dis2, False)

    # --- record writing and the propagation of a void ----------------------
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        global RESULTS
        saved = RESULTS
        RESULTS = d
        try:
            st = default_state()
            st["t0"] = now()
            st["hardware"] = {"gpu_name": "NVIDIA A100-SXM4-40GB", "driver_version": "570.148.08",
                              "cuda_runtime": "12.8", "instance_type": "gpu_1x_a100_sxm4"}
            st["caps"] = {"price_usd_per_hour": 1.99, "budget_left_usd": 5.0,
                          "remote_timeout_s": 7200, "instance_type": "gpu_1x_a100_sxm4"}
            st["versions"] = {"md_engine": "OpenMM"}
            p = write_record(st, "endpoint-control-sleep",
                             cell={"control": "planted_sleep", "tag": TAG},
                             inputs=[], metric="m", values={"measured_s": 60.1},
                             threshold={}, decision_rule=RULE_SLEEP, decision="PASS")
            rec = json.loads(p.read_text())
            check("a record carries its own validity flag", rec["run_valid"], True)
            check("the validity flag is beside the values too",
                  rec["values"]["run_valid"], True)
            for key in ("cell", "inputs", "metric", "values", "threshold", "decision_rule",
                        "decision", "env"):
                check("the record carries %s" % key, key in rec, True)

            # A missed anchor must reach every later record, not only the summary.
            set_run_invalid(st, "anchor redocking missed")
            void_unmeasured(st, "anchor miss")
            for which in ("C1", "C2", "C3", "C4"):
                rec = json.loads((d / ("endpoint-%s_tag-%s.json" % (which, TAG))).read_text())
                check("%s is void after an anchor miss" % which, rec["decision"], "VOID")
                check("%s says the run is not valid" % which, rec["run_valid"], False)
                check("%s says so beside its values too" % which,
                      rec["values"]["run_valid"], False)
            check("the earlier record keeps its own true flag",
                  json.loads((d / ("endpoint-control-sleep_tag-%s.json" % TAG)).read_text())
                  ["run_valid"], True)
            rv = json.loads((d / "RUN_VALID.json").read_text())
            check("the validity file says the run is not valid", rv["run_valid"], False)
            summary = write_summary(st, EXIT_ANCHOR)
            check("the summary leads with the stand-in scope",
                  summary["what_this_run_decides"].startswith("This run decides the stand-in"),
                  True)
            check("the summary makes no decision of its own",
                  summary["this_summary_makes_no_decision_of_its_own"], True)
            check("the summary carries the fallback text", summary["gate"]["gate_else"],
                  GATE_ELSE)
            check("the summary carries the run validity", summary["run_valid"], False)
            text = json.dumps(summary).lower()
            check("no output calls a same-box repeat a replication",
                  ("replicat" in text), False)
            check("the summary names the repeat honestly",
                  "not independent confirmation" in summary["repeat_note"], True)
            check("the exit code marks an anchor miss", EXIT_ANCHOR, 4)

            # A guard stop voids the unfinished inputs and leaves validity alone.
            st2 = default_state()
            st2["t0"] = now()
            st2["hardware"] = st["hardware"]
            st2["caps"] = st["caps"]
            st2["measured"]["C3_rows"] = [{"pair": "pair1", "hours": 1.0},
                                          {"pair": "pair2", "hours": 1.0}]
            for f in d.glob("endpoint-C*"):
                f.unlink()
            dec3, val3, rows3 = decide_c3(st2)
            write_input_record(st2, "C3", dec3, val3, rows3)
            void_unmeasured(st2, "guard stop")
            check("a finished input keeps its decision after a guard stop",
                  json.loads((d / ("endpoint-C3_tag-%s.json" % TAG)).read_text())["decision"],
                  "PASS")
            check("an unfinished input is void after a guard stop",
                  json.loads((d / ("endpoint-C1_tag-%s.json" % TAG)).read_text())["decision"],
                  "VOID")
            check("a guard stop does not mark the run invalid", st2["run_valid"], True)
            check("the unfinished input says it was not measured",
                  LABEL_UNMEASURED in json.loads(
                      (d / ("endpoint-C1_tag-%s.json" % TAG)).read_text())
                  ["values"]["void_reasons"], True)

            # Input 1 on planted rows, including the zero spread case.
            st3 = default_state()
            st3["t0"] = now()
            st3["hardware"] = st["hardware"]
            st3["caps"] = st["caps"]
            st3["af_rows"] = [
                {"pair": "pair1", "seed": 0, "status": "ok", "wall_s": 1800.0, "hours": 0.5},
                {"pair": "pair2", "seed": 0, "status": "ok", "wall_s": 1830.0, "hours": 0.5},
                {"pair": "pair3", "seed": 0, "status": "ok", "wall_s": 1790.0, "hours": 0.5}]
            dec1, val1, _ = decide_c1(st3)
            check("three good runs over three pairs give a pass", dec1, "PASS")
            close("the measured mean is 0.5 hours", val1["measured"], 0.5)
            check("the gate result rides along", val1["gate_pass"], True)
            st3["af_rows"] = st3["af_rows"][:2]
            check("two runs are void", decide_c1(st3)[0], "VOID")
            st3["af_rows"] = [
                {"pair": "pair1", "seed": 0, "status": "ok", "wall_s": 1800.0, "hours": 0.5},
                {"pair": "pair1", "seed": 1, "status": "ok", "wall_s": 1800.0, "hours": 0.5},
                {"pair": "pair2", "seed": 0, "status": "ok", "wall_s": 1800.0, "hours": 0.5}]
            dec_missing, val_missing, _ = decide_c1(st3)
            check("three runs missing a pair are void", dec_missing, "VOID")
            st3["af_rows"] = [
                {"pair": "pair%d" % p, "seed": s, "status": "ok", "wall_s": 1800.0, "hours": 0.5}
                for p in (1, 2, 3) for s in (0, 1)]
            dec_zero, val_zero, _ = decide_c1(st3)
            check("identical seed timings make input 1 void", dec_zero, "VOID")
            check("and say why", LABEL_ZERO_SPREAD in val_zero["void_reasons"], True)
            st3["hardware"] = {"gpu_name": "NVIDIA L40S", "driver_version": "570.148.08"}
            st3["af_rows"] = [
                {"pair": "pair%d" % p, "seed": 0, "status": "ok",
                 "wall_s": 1800.0 + p, "hours": 0.5} for p in (1, 2, 3)]
            dec_gpu, val_gpu, _ = decide_c1(st3)
            check("a non-A100 GPU voids input 1", dec_gpu, "VOID")
            check("and keeps the raw number", round(val_gpu["measured"], 3), 0.5)
            check("and says it was not an A100", LABEL_NOT_A100 in val_gpu["labels"], True)
            st4 = default_state()
            st4["t0"] = now()
            st4["hardware"] = {"gpu_name": "NVIDIA L40S"}
            st4["caps"] = st["caps"]
            st4["md_rows"] = [{"pair": "pair1", "status": "ok", "n_atoms": 150000,
                               "ns_per_day_wallclock": 129.0},
                              {"pair": "pair2", "status": "ok", "n_atoms": 150000,
                               "ns_per_day_wallclock": 129.0}]
            check("a non-A100 GPU voids input 2", decide_c2(st4)[0], "VOID")
            st4["hardware"] = st["hardware"]
            check("an A100 with good atom counts decides input 2", decide_c2(st4)[0], "PASS")
            st4["md_rows"][0]["n_atoms"] = 119999
            check("an atom count below the window voids input 2", decide_c2(st4)[0], "VOID")
            st4["md_rows"][0]["n_atoms"] = 180001
            check("an atom count above the window voids input 2", decide_c2(st4)[0], "VOID")
            st4["md_rows"] = st4["md_rows"][:1]
            st4["md_rows"][0]["n_atoms"] = 150000
            check("one complex is below the minimum for input 2", decide_c2(st4)[0], "VOID")
            st5 = default_state()
            st5["t0"] = now()
            st5["hardware"] = st["hardware"]
            st5["caps"] = st["caps"]
            st5["measured"]["C3_rows"] = [{"pair": "pair1", "hours": 1.0},
                                          {"pair": "pair2", "hours": 1.0},
                                          {"pair": "pair3", "hours": 1.0}]
            check("three pair hours of 1.0 pass input 3", decide_c3(st5)[0], "PASS")
            st5["measured"]["C3_rows"] = st5["measured"]["C3_rows"][:1]
            check("one pair is below the minimum for input 3", decide_c3(st5)[0], "VOID")
            st6 = default_state()
            st6["t0"] = now()
            st6["hardware"] = st["hardware"]
            st6["caps"] = st["caps"]
            st6["storage_rows"] = [
                {"artifact": "alphafold_run", "apparent_bytes": (1 << 30) - 2000,
                 "final_bytes": 1000, "intermediate_bytes": 10},
                {"artifact": "docking_pair", "apparent_bytes": 1000, "final_bytes": 1000,
                 "intermediate_bytes": 0},
                {"artifact": "md_segment", "apparent_bytes": 1000, "final_bytes": 1000,
                 "intermediate_bytes": 0, "bytes_per_ns": 2000.0}]
            dec4, val4, _ = decide_c4(st6)
            close("one gibibyte per run scales to 216 GiB", val4["measured"], 216.0, 1e-6)
            check("that passes", dec4, "PASS")
            close("the other grid reading is 432 GiB", val4["gib_432_runs"], 432.0, 1e-6)
            st6["storage_rows"] = st6["storage_rows"][:2]
            check("a missing artifact type voids input 4", decide_c4(st6)[0], "VOID")

            # An install or download failure must void everything and say so.
            st7 = default_state()
            st7["t0"] = now()
            st7["hardware"] = st["hardware"]
            st7["caps"] = st["caps"]
            for f in d.glob("endpoint-C*"):
                f.unlink()
            set_run_invalid(st7, "install failed: pip returned 1")
            void_unmeasured(st7, "install failed")
            rec = json.loads((d / ("endpoint-C2_tag-%s.json" % TAG)).read_text())
            check("an install failure voids input 2", rec["decision"], "VOID")
            check("an install failure marks the run not valid", rec["run_valid"], False)
            st8 = default_state()
            st8["t0"] = now()
            st8["hardware"] = st["hardware"]
            st8["caps"] = st["caps"]
            for f in d.glob("endpoint-C*"):
                f.unlink()
            set_run_invalid(st8, "download failed: the archive did not arrive")
            void_unmeasured(st8, "download failed")
            check("a download failure voids input 4",
                  json.loads((d / ("endpoint-C4_tag-%s.json" % TAG)).read_text())["decision"],
                  "VOID")
            st9 = default_state()
            st9["t0"] = now()
            st9["hardware"] = st["hardware"]
            st9["caps"] = st["caps"]
            for f in d.glob("endpoint-C*"):
                f.unlink()
            set_run_invalid(st9, "planted sleep check failed")
            void_unmeasured(st9, "harness control failed")
            check("a failed sleep check voids input 1",
                  json.loads((d / ("endpoint-C1_tag-%s.json" % TAG)).read_text())["decision"],
                  "VOID")
            check("a failed sleep check marks the run not valid", st9["run_valid"], False)
            check("the exit code for a broken harness is 2", EXIT_INFRA, 2)
            check("the exit code for a guard stop is 3", EXIT_GUARD, 3)
        finally:
            RESULTS = saved

    # --- what a child tool is given ----------------------------------------
    planted_env = {"PATH": "/usr/bin", "HF_TOKEN": "a-secret",
                   "HUGGING_FACE_HUB_TOKEN": "a-secret"}
    kid = child_env(planted_env)
    check("no token reaches a child tool",
          [k for k in SECRET_ENV_NAMES if k in kid], [])
    check("the rest of the environment still reaches it", kid.get("PATH"), "/usr/bin")

    # --- the caps come from the environment, never from a constant ----------
    saved_env = {k: os.environ.get(k) for k in
                 ("REMOTE_TIMEOUT", "BUDGET_LEFT_USD", "PRICE_USD_PER_HOUR")}
    try:
        os.environ["REMOTE_TIMEOUT"] = "3600"
        close("a forwarded 3600 second cap is used as given",
              caps_from_env()["remote_timeout_s"], 3600.0)
        guard_short = guard_check(3000, 1000, 1.99, 5, caps_from_env()["remote_timeout_s"])
        check("and the guard follows it, not a constant", guard_short["may_start"], False)
        os.environ["REMOTE_TIMEOUT"] = "99999"
        close("a larger cap is cut back to 7200", caps_from_env()["remote_timeout_s"], 7200.0)
        os.environ.pop("REMOTE_TIMEOUT")
        caps_unset = caps_from_env()
        close("an unforwarded cap falls back to 7200", caps_unset["remote_timeout_s"], 7200.0)
        check("and the record says it was not forwarded",
              caps_unset.get("labels"), [LABEL_TIMEOUT_NOT_FORWARDED])
        os.environ["BUDGET_LEFT_USD"] = "50"
        close("a budget above one launch is cut back to 5",
              caps_from_env()["budget_left_usd"], 5.0)
    finally:
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    # --- contacts keyed by role, not by the letter in the file --------------
    def planted_capsid():
        out = []
        for i in range(1, 7):
            out.append({"chain": "Z", "resseq": i, "resname": "ALA", "atom": "CA",
                        "element": "C", "x": 0.0, "y": float(i) * 10.0, "z": 0.0})
        return out

    def planted_receptor(letter, contacts, offset=0.0):
        """A receptor that touches the first `contacts` capsid residues."""
        out = []
        for i in range(1, 7):
            near = i <= contacts
            out.append({"chain": letter, "resseq": i, "resname": "ALA", "atom": "CA",
                        "element": "C", "x": (3.0 if near else 60.0) + offset,
                        "y": float(i) * 10.0, "z": 0.0})
        return out

    cap_atoms_t = planted_capsid()
    native_t = contact_pairs(as_role(cap_atoms_t, ROLE_CAPSID),
                             as_role(planted_receptor("R", 6), ROLE_RECEPTOR))
    check("the planted reference has six contacts", len(native_t), 6)
    for letter in ("B", "C", "A"):
        pose_t = contact_pairs(as_role(cap_atoms_t, ROLE_CAPSID),
                               as_role(planted_receptor(letter, 3), ROLE_RECEPTOR))
        close("a pose written with chain %s still overlaps 0.5" % letter,
              contact_overlap(native_t, pose_t), 0.5)
        check("and its overlap is not zero",
              contact_overlap(native_t, pose_t) > 0.0, True)
    with tempfile.TemporaryDirectory() as d:
        pose_file = Path(d) / "pose.pdb"
        write_pdb(planted_receptor("R", 3), pose_file, {"R": "B"})
        read_back = read_pdb_atoms(pose_file.read_text())
        round_trip = contact_pairs(as_role(cap_atoms_t, ROLE_CAPSID),
                                   as_role(read_back, ROLE_RECEPTOR))
        close("the same pose read back from a file still overlaps 0.5",
              contact_overlap(native_t, round_trip), 0.5)
        check("the written file carries the letter B, and it does not matter",
              sorted(set(a["chain"] for a in read_back)), ["B"])

    # --- the interface distance is over the interface only ------------------
    ref_rec = []
    for i in range(1, 7):
        for name in BACKBONE:
            ref_rec.append({"chain": "R", "resseq": i, "resname": "ALA", "atom": name,
                            "element": "C" if name != "O" else "O",
                            "x": 3.0 if i <= 3 else 60.0, "y": float(i) * 10.0, "z": 0.0})
    iface_t = interface_residues(cap_atoms_t, ref_rec)
    check("the reference interface is the three touching residues", iface_t, [1, 2, 3])
    moved = []
    for a in ref_rec:
        b = dict(a)
        if b["resseq"] > 3:                       # move only what is not at the interface
            b["x"] += 20.0
        moved.append(b)
    close("moving atoms away from the interface leaves the interface distance at zero",
          interface_backbone_rmsd(ref_rec, moved, iface_t), 0.0)
    check("while the whole chain has clearly moved",
          rmsd_direct(backbone_coords(ref_rec), backbone_coords(moved)) > 0.0, True)
    shifted_iface = []
    for a in ref_rec:
        b = dict(a)
        if b["resseq"] <= 3:
            b["x"] += 5.0
        shifted_iface.append(b)
    close("a 5 Angstrom shift of the interface gives 5.0",
          interface_backbone_rmsd(ref_rec, shifted_iface, iface_t), 5.0)

    # --- what pip and apt installed, read back from their own records -------
    pip_report = json.dumps({"install": [{
        "metadata": {"name": "openmm", "version": "8.2.0"},
        "download_info": {"url": "https://files.pythonhosted.org/openmm-8.2.0.whl",
                          "archive_info": {"hashes": {"sha256": "a" * 64}}}}]})
    got_pip = parse_pip_report(pip_report)
    check("the pip report names the wheel", got_pip[0]["name"], "openmm")
    check("and its address", got_pip[0]["url"],
          "https://files.pythonhosted.org/openmm-8.2.0.whl")
    check("and its hash", got_pip[0]["sha256"], "a" * 64)
    check("a broken pip report reads as nothing", parse_pip_report("not json"), [])
    apt_line = "build-essential | 12.9ubuntu3 | %s\n" % ("b" * 64)
    check("the apt record names version and hash",
          parse_apt_versions(apt_line)[0]["version"], "12.9ubuntu3")

    # --- a tool that outlives its allowance is stopped, with its children ----
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        marker = d / "child_heartbeat.txt"
        tool = d / "planted_tool.py"
        tool.write_text(
            "import subprocess, sys, time\n"
            "child = subprocess.Popen([sys.executable, '-c',\n"
            "  \"import time,sys\\nwhile True:\\n open(sys.argv[1],'w').write(str(time.time()))\\n"
            " time.sleep(0.2)\", sys.argv[1]])\n"
            "time.sleep(120)\n")
        res_kill = run_tool([sys.executable, str(tool), str(marker)], "planted_sleeper", 3,
                            results=d, allow_timeout=True)
        check("the tool is stopped at its allowance", res_kill["timed_out"], True)
        check("and that is reported, not raised", res_kill["exit_code"], -9)
        time.sleep(1.0)
        beat_one = marker.read_text() if marker.exists() else ""
        time.sleep(1.0)
        beat_two = marker.read_text() if marker.exists() else ""
        check("the child it started is stopped too", beat_one, beat_two)
        check("and no process group is left on the list",
              (d / "process_groups.txt").read_text().strip(), "")

    # --- the whole stage flow, with stand-in stages -------------------------
    def flow_state():
        st = default_state()
        st["t0"] = now()
        st["hardware"] = {"gpu_name": "NVIDIA A100-SXM4-40GB", "driver_version": "570.148.08",
                          "cuda_runtime": "12.8", "instance_type": "gpu_1x_a100_sxm4"}
        st["caps"] = {"price_usd_per_hour": 1.99, "budget_left_usd": 5.0,
                      "remote_timeout_s": 7200, "instance_type": "gpu_1x_a100_sxm4"}
        st["versions"] = {"md_engine": "OpenMM"}
        st["pairs"] = [{"pair": "pair%d" % i} for i in (1, 2, 3)]
        return st

    def af_rows_for(n):
        out = []
        for seed in (0, 1, 2):
            for p in (1, 2, 3):
                if len(out) >= n:
                    return out
                secs = 1800.0 + seed * 10 + p
                out.append({"pair": "pair%d" % p, "seed": seed, "status": "ok",
                            "wall_s": secs, "hours": 0.5})
        return out

    def md_rows_for(n):
        return [{"pair": "pair%d" % i, "status": "ok", "n_atoms": 150000,
                 "ns_per_day_wallclock": 129.0, "ns_per_day_engine": 129.0}
                for i in range(1, n + 1)]

    def aux_rows_for(n):
        return [{"pair": "pair%d" % i, "hours": 1.0, "status": "ok"}
                for i in range(1, n + 1)]

    storage_rows_full = [
        {"artifact": "alphafold_run", "apparent_bytes": (1 << 30) - 2000,
         "final_bytes": 1000, "intermediate_bytes": 10},
        {"artifact": "docking_pair", "apparent_bytes": 1000, "final_bytes": 1000,
         "intermediate_bytes": 0},
        {"artifact": "md_segment", "apparent_bytes": 1000, "final_bytes": 1000,
         "intermediate_bytes": 0, "bytes_per_ns": 2000.0}]

    def plain(name):
        def f(st):
            st["stages_done"].append(name)
            return st
        return f

    def filler(name, key, value):
        def f(st):
            if key == "C3":
                st["measured"]["C3_rows"] = value
            else:
                st[key] = value
            st["stages_done"].append(name)
            return st
        return f

    def stopper(name, kind, key, value, reason):
        """A stage that does some of its work and then meets a stop."""
        def f(st):
            if key == "C3":
                st["measured"]["C3_rows"] = value
            else:
                st[key] = value
            record_stop(st, name, kind, reason)
            raise GuardStop(reason)
        return f

    def raiser(exc):
        def f(st):
            raise exc
        return f

    FLOW_NAMES = ["downloads", "controls", "anchor", "aux", "af2", "md", "storage",
                  "endpoints"]

    def flow_stages(**over):
        base = {"downloads": plain("downloads"), "controls": plain("controls"),
                "anchor": plain("anchor"),
                "aux": filler("aux", "C3", aux_rows_for(3)),
                "af2": filler("af2", "af_rows", af_rows_for(9)),
                "md": filler("md", "md_rows", md_rows_for(3)),
                "storage": filler("storage", "storage_rows", list(storage_rows_full)),
                "endpoints": stage_endpoints}
        base.update(over)
        return base

    def run_flow(stages, st=None):
        st = st or flow_state()
        code = run_stages(FLOW_NAMES, stages=stages, state=st)
        decisions = {}
        for which in ("C1", "C2", "C3", "C4"):
            path = RESULTS / ("endpoint-%s_tag-%s.json" % (which, TAG))
            decisions[which] = json.loads(path.read_text()) if path.exists() else None
        return code, st, decisions

    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        saved_results = RESULTS
        RESULTS = d
        try:
            # (a) every stage finishes.
            code_a, st_a, dec_a = run_flow(flow_stages())
            check("a finished run exits zero", code_a, EXIT_OK)
            check("a finished run stays valid", st_a["run_valid"], True)
            check("input 1 is decided", dec_a["C1"]["decision"], "PASS")
            check("input 2 is decided", dec_a["C2"]["decision"], "PASS")
            check("input 3 is decided", dec_a["C3"]["decision"], "PASS")
            check("input 4 is decided", dec_a["C4"]["decision"], "PASS")
            check("a finished run carries no incomplete label",
                  LABEL_INCOMPLETE_RUN in (dec_a["C1"]["values"].get("labels") or []), False)

            # (b) the clock stops the AlphaFold timings after two of nine runs.
            for f in d.glob("endpoint-*"):
                f.unlink()
            code_b, st_b, dec_b = run_flow(flow_stages(
                af2=stopper("af2", "guard", "af_rows", af_rows_for(2),
                            "no time left for another AlphaFold run")))
            check("a time-guard stop exits three", code_b, EXIT_GUARD)
            check("a time-guard stop leaves the run valid", st_b["run_valid"], True)
            check("the unfinished input is not decided", dec_b["C1"]["decision"], "VOID")
            check("its raw rows are kept", len(st_b["af_rows"]), 2)
            check("the finished inputs keep their decisions",
                  [dec_b[k]["decision"] for k in ("C2", "C3", "C4")],
                  ["PASS", "PASS", "PASS"])
            check("every record says the run is incomplete",
                  all(LABEL_INCOMPLETE_RUN in (dec_b[k]["values"].get("labels") or [])
                      for k in ("C1", "C2", "C3", "C4")), True)

            # (c) a dynamics segment is stopped at its allowance on the third complex.
            for f in d.glob("endpoint-*"):
                f.unlink()
            code_c, st_c, dec_c = run_flow(flow_stages(
                md=stopper("md", "timeout", "md_rows", md_rows_for(2),
                           "a dynamics segment was stopped at its allowance")))
            check("a stopped tool exits three", code_c, EXIT_GUARD)
            check("a stopped tool leaves the run valid", st_c["run_valid"], True)
            check("input 2 is decided on the two complexes that finished",
                  (dec_c["C2"]["decision"], dec_c["C2"]["values"]["n"]), ("PASS", 2))
            check("the other inputs are untouched",
                  [dec_c[k]["decision"] for k in ("C1", "C3", "C4")],
                  ["PASS", "PASS", "PASS"])

            # (d) docking hits its ceiling: two pairs decide input 3, one does not.
            for f in d.glob("endpoint-*"):
                f.unlink()
            code_d, st_d, dec_d = run_flow(flow_stages(
                aux=stopper("aux", "ceiling", "C3", aux_rows_for(2),
                            "docking and analysis reached its ceiling")))
            check("a ceiling stop exits three", code_d, EXIT_GUARD)
            check("two finished pairs still decide input 3", dec_d["C3"]["decision"], "PASS")
            for f in d.glob("endpoint-*"):
                f.unlink()
            code_d1, st_d1, dec_d1 = run_flow(flow_stages(
                aux=stopper("aux", "ceiling", "C3", aux_rows_for(1),
                            "docking and analysis reached its ceiling")))
            check("one finished pair is below the minimum", dec_d1["C3"]["decision"], "VOID")
            check("and the run still exits three", code_d1, EXIT_GUARD)

            # (e) a tool really fails.
            for f in d.glob("endpoint-*"):
                f.unlink()
            code_e, st_e, dec_e = run_flow(flow_stages(
                af2=raiser(ToolError("colabfold_batch failed with exit 1"))))
            check("a failed tool exits two", code_e, EXIT_INFRA)
            check("a failed tool makes the run not valid", st_e["run_valid"], False)
            check("every input is void after a failed tool",
                  [dec_e[k]["decision"] for k in ("C1", "C2", "C3", "C4")],
                  ["VOID"] * 4)
            check("and every record says the run is not valid",
                  all(dec_e[k]["run_valid"] is False for k in ("C1", "C2", "C3", "C4")), True)

            # (f) the anchor misses.
            for f in d.glob("endpoint-*"):
                f.unlink()
            code_f, st_f, dec_f = run_flow(flow_stages(anchor=raiser(AnchorMiss("anchor miss"))))
            check("a missed anchor exits four", code_f, EXIT_ANCHOR)
            check("a missed anchor makes the run not valid", st_f["run_valid"], False)
            check("a missed anchor voids all four inputs",
                  [dec_f[k]["decision"] for k in ("C1", "C2", "C3", "C4")], ["VOID"] * 4)
            check("and every one of those records says so, not only the summary",
                  all(dec_f[k]["run_valid"] is False and
                      dec_f[k]["values"]["run_valid"] is False
                      for k in ("C1", "C2", "C3", "C4")), True)

            # (g) the planted sleep check fails.
            for f in d.glob("endpoint-*"):
                f.unlink()
            code_g, st_g, _ = run_flow(flow_stages(
                controls=raiser(HarnessInvalid("planted sleep check failed"))))
            check("a failed timer check exits two", code_g, EXIT_INFRA)
            check("a failed timer check makes the run not valid", st_g["run_valid"], False)

            # (h) install, smoke check and download failures.
            for stage_name, text in (("downloads", "the declared packages did not install"),
                                     ("downloads", "the smoke check did not start the tools"),
                                     ("downloads", "the archive did not arrive")):
                for f in d.glob("endpoint-*"):
                    f.unlink()
                code_h, st_h, dec_h = run_flow(flow_stages(
                    downloads=raiser(ToolError(text))))
                check("%s exits two" % text, code_h, EXIT_INFRA)
                check("%s voids input 1" % text, dec_h["C1"]["decision"], "VOID")
                check("%s makes the run not valid" % text, st_h["run_valid"], False)

            # (i) the outer kill: the box ran out of clock while work was running.
            for f in d.glob("endpoint-*"):
                f.unlink()
            st_i = flow_state()
            st_i["measured"]["C3_rows"] = aux_rows_for(3)
            save_state(st_i)
            stage_endpoints(st_i)
            code_i = fail_stage("generate", "the outer timeout stopped the run", EXIT_GUARD)
            check("the outer timeout route exits three", code_i, EXIT_GUARD)
            rv_i = json.loads((d / "RUN_VALID.json").read_text())
            check("the outer timeout route leaves the run valid", rv_i["run_valid"], True)
            check("and the marker carries the code",
                  (d / "RUN_DONE").read_text().strip(), "3")
            summary_i = json.loads((d / ("%s_summary.json" % TAG)).read_text())
            check("and the summary carries the incomplete label",
                  summary_i["incomplete_run_label"], LABEL_INCOMPLETE_RUN)
        finally:
            RESULTS = saved_results

    # --- the tool runner is injected into the flow the same way -------------
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        saved_results = RESULTS
        RESULTS = d
        try:
            calls = []

            def fake_runner(argv, log_name, timeout_s, **kw):
                calls.append(list(argv))
                return {"argv": list(argv), "exit_code": 0, "timed_out": False,
                        "wall_s": 0.01, "log": "", "output": "", "started_utc": utc(),
                        "ended_utc": utc()}

            def tool_stage(st):
                run_tool(["planted-tool"], "planted", 5, results=d)
                st["stages_done"].append("downloads")
                return st

            st_inj = flow_state()
            code_inj = run_stages(["downloads"], stages={"downloads": tool_stage},
                                  state=st_inj, runner=fake_runner)
            check("the injected tool runner serves the flow's tool calls",
                  calls, [["planted-tool"]])
            check("and the flow still ends cleanly", code_inj, EXIT_OK)
        finally:
            RESULTS = saved_results

    # --- the download allow list -------------------------------------------
    try:
        download("https://example.invalid/thing.tar", Path(tempfile.gettempdir()) / "x")
        check("an unlisted download source is refused", True, False)
    except ToolError:
        check("an unlisted download source is refused", True, True)

    # --- the three stand-in pairs ------------------------------------------
    cap_seq_len, rec_seq_len = 540, 240
    fake_atoms = []
    for ch_id, n in (("A", cap_seq_len), ("B", cap_seq_len), ("C", cap_seq_len),
                     ("R", rec_seq_len)):
        for i in range(1, n + 1):
            fake_atoms.append({"chain": ch_id, "resseq": i, "resname": "ALA", "atom": "CA",
                               "element": "C", "x": float(i), "y": 0.0, "z": 0.0})
    pairs = build_pairs(fake_atoms)
    check("three stand-in pairs are built", len(pairs), 3)
    check("every pair is inside 750 to 1000 residues",
          all(PAIR_MIN_RESIDUES <= p["total_residues"] <= PAIR_MAX_RESIDUES for p in pairs), True)
    check("the pair lengths are spread, not equal",
          len(set(p["total_residues"] for p in pairs)), 3)
    check("each pair names its capsid slot and its receptor chain",
          all(p["capsid_slot_chain"] and p["receptor_chain"] for p in pairs), True)
    check("each pair records a sequence hash",
          all(len(p["sequence_sha256"]) == 64 for p in pairs), True)

    failed = [c for c in checks if not c[1]]
    for name, ok, got, want in failed:
        print("FAIL %s: got %r, wanted %r" % (name, got, want))
    print("selftest: %d of %d checks passed" % (len(checks) - len(failed), len(checks)))
    # Tie this log to the two files it was run against, so a reader can tell
    # whether the log belongs to the files in front of them.
    def _hash_or_missing(p: Path):
        return sha256_file(p) if p.exists() else "missing"
    print("selftest: files sha256 run_m4.py %s onbox_m4.sh %s" % (
        _hash_or_missing(Path(__file__).resolve()),
        _hash_or_missing(Path(__file__).resolve().parent / "onbox_m4.sh")))
    print("selftest: %s" % ("PASS" if not failed else "FAIL"))
    return 0 if not failed else 1


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Measure four cost inputs on one rented GPU box.")
    ap.add_argument("--selftest", action="store_true",
                    help="run the standard library checks and exit")
    ap.add_argument("--stage", default=None,
                    choices=["extract", "generate", "endpoints", "all"] + list(FINE.keys()),
                    help="which stage to run")
    ap.add_argument("--worker", default=None, choices=["md"],
                    help="internal: run one dynamics segment in this process")
    ap.add_argument("--spec", default=None, help="internal: the worker's job file")
    ap.add_argument("--fail-stage", default=None,
                    help="record that a named stage failed, then stop")
    ap.add_argument("--reason", default="", help="what failed")
    ap.add_argument("--exit-code", type=int, default=EXIT_INFRA, help="exit code to record")
    args = ap.parse_args(argv)

    if args.selftest:
        return _selftest()
    if args.worker == "md":
        if not args.spec:
            print("--worker md needs --spec")
            return EXIT_INFRA
        return md_worker(Path(args.spec))
    if args.fail_stage:
        return fail_stage(args.fail_stage, args.reason, args.exit_code)
    if not args.stage:
        print(__doc__)
        return 0
    if args.stage == "all":
        names = COARSE["extract"] + COARSE["generate"] + COARSE["endpoints"]
    elif args.stage in COARSE:
        names = COARSE[args.stage]
    else:
        names = [args.stage]
    return run_stages(names)


if __name__ == "__main__":
    sys.exit(main())
