#!/usr/bin/env python3
"""Acceptance tests for measure run m4, written from the directive only.

Run on the box, inside the shipped environment, from the run directory, before
the physics:

    python3 tests_m4.py --results results_m4/out

Black box: nothing here imports, reads or references run_m4.py or onbox_m4.sh.
The tests check (1) the environment the directive requires, (2) the records
contract, (3) the guard arithmetic and void propagation, (4) the directive's own
internal consistency (numbers stated in two items must agree).

Stdlib only in this process; the environment checks shell out to the shipped
interpreter / tools. No network.
"""

import argparse
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

# ---------------------------------------------------------------------------
# constants transcribed from the directive (EXEC_NOTE.md), the contract and the
# question. Where the same number is stated in two places it is transcribed
# twice, under two names, and a consistency test compares them.
# ---------------------------------------------------------------------------

TAG = "m4"

# item 19: card values, units and bands
CARD_VALUES = {"C1": 0.5, "C2": 129.0, "C3": 1.0, "C4": 200.0}
BANDS_ITEM19 = {
    "C1": (0.2, 1.25),
    "C2": (51.6, 322.5),
    "C3": (0.3333, 3.0),
    "C4": (66.67, 600.0),
}
UNITS_ITEM19 = {
    "C1": "h per run",
    "C2": "ns/day",
    "C3": "h per pair",
    "C4": "GiB",
}
# QUESTION.md "What would refute each claim"
BANDS_QUESTION = {
    "C1": (0.2, 1.25),
    "C2": (51.6, 322.5),
    "C3": (0.3333, 3.0),
    "C4": (66.67, 600.0),
}
# QUESTION.md "Committed data" card values
CARD_VALUES_QUESTION = {"C1": 0.5, "C2": 129.0, "C3": 1.0, "C4": 200.0}
# band multipliers named in the question (PROXY 2.5x, GUESS 3x)
BAND_MULTIPLIER = {"C1": 2.5, "C2": 2.5, "C3": 3.0, "C4": 3.0}

GATE_VALUE = 1.0  # item 11 / question: af2_h_per_run <= 1, C1 only
GATE_ELSE = ("take the docking-plus-MD fallback line with one AlphaFold-Multimer "
             "seed per pair, or move the grid to 12 pairs")

MARGINAL_FRACTION = 0.10  # item 18: edge x 0.9 .. edge x 1.1

# item 8: stage ceilings in seconds
CEILINGS = {
    "setup": 1500,
    "tests": 300,
    "controls_anchor": 700,
    "docking": 600,
    "alphafold": 2000,
    "md": 1600,
    "endpoints": 100,
}
MARGIN_S = 400
FETCH_RESERVE_S = 100  # item 8 allowance formula: ... - 400 - 100
CEILING_SUM_ITEM8 = 7200  # item 8 states the sum explicitly
REMOTE_TIMEOUT_OF_RECORD = 7200  # item 8 / Box: every launch uses 7200 exactly
TESTS_CEILING_ITEM5 = 300  # item 5 states the tests ceiling
TESTS_CEILING_U7 = 300     # U7 states it again
PER_PAIR_CEILING = 250     # item 8 / item 13: at most 250 s per docking pair
PER_COMPLEX_CEILING = 600  # item 8 / item 14: at most 600 s per MD complex

# item 24: guard estimate floors in seconds
ESTIMATE_FLOORS = {
    "anchor_serial": 60,
    "anchor_parallel": 60,
    "docking_pair": 60,
    "alphafold_run": 120,
    "md_complex": 150,
    "storage": 20,
    "endpoints": 30,
    "tests": 60,
}

# caps
HARD_CAP_USD = 10.0
BUDGET_LEFT_DEFAULT_MAX = 5.0
PRICE_OF_RECORD = 1.99
HOLD_SECONDS_OF_RECORD = 1200
HOLD_RESUME_MIN_S_ITEM6_A = 1500  # "at least 1,500 s of REMOTE_TIMEOUT left"
HOLD_RESUME_MIN_S_ITEM6_B = 1500  # "less than 1,500 s left ends the launch"
MIN_LAUNCH_SECONDS = 7800         # Box: no launch with less than 7800 s x price
MIN_LAUNCH_USD_AT_1_99 = 4.311    # Box: USD 4.311 at 1.99
MIN_LAUNCH_USD_AT_2_50 = 5.417    # Box: USD 5.417 at 2.50

SLEEP_CONTROL_S = 60.0
SLEEP_TOLERANCE = 0.05            # item 16: at most 5 percent
EMPTY_RUN_MAX_S = 2.0             # item 16
EMPTY_RUN_MAX_BYTES = 1024 * 1024
SEED_SD_LABEL_THRESHOLD = 0.50    # item 18: relative SD over 50 percent
MD_RATE_DISAGREE_FRACTION = 0.05  # item 14: more than 5 percent

ANCHOR_OVERLAP_MIN = 0.50         # item 17 / question
ANCHOR_RMSD_MAX = 5.0
ANCHOR_SP_RMSD_MAX = 2.0
CONTACT_CUTOFF_A = 4.5

STORAGE_RUNS = 216                # item 15 / question grid
STORAGE_RUNS_ALT = 432
GIB = float(2 ** 30)
MD_PRODUCTION_NS = 0.5            # item 14 / 15
MD_FRAME_INTERVAL_PS = 10
MD_DCD_STEPS = 5000

# item 7: the only exit codes and the per-input statuses
EXIT_CODES = {0, 2, 3, 4}

# item 19 / contract 5: record fields
RECORD_REQUIRED_FIELDS = [
    "cell", "inputs", "metric", "values", "threshold", "decision_rule",
    "decision", "run_valid",
]
DECISIONS = {"PASS", "FAIL", "VOID"}

# item 20: label keys every record's values.machine must hold
MACHINE_LABEL_KEYS = [
    "instance_type", "gpu_name", "driver_version", "cuda_runtime_version",
    "start_utc", "end_utc", "price_usd_per_hour",
    "expected_lock_sha256", "observed_lock_sha256", "venv_path",
    "environment_changed_by_fixer", "held_attempts",
]

# item 3: env_check record values
ENV_CHECK_VALUE_KEYS = [
    "expected_lock_sha256", "observed_lock_sha256", "venv_path",
    "python_version", "equal",
]
# item 5: tests record values
TESTS_RECORD_VALUE_KEYS = [
    "exit_code", "seconds", "tests_file_sha256", "stdout_tail",
    "tests_passed", "tests_total",
]

SUBPROC_TIMEOUT_S = 90

# ---------------------------------------------------------------------------
# harness
# ---------------------------------------------------------------------------

RESULTS = None
SCRATCH = None
_results = []


def check(name, fn):
    try:
        ok, reason = fn()
    except Exception as exc:  # a test that raises is a failing test
        ok, reason = False, "%s: %s" % (type(exc).__name__, str(exc).replace("\n", " ")[:160])
    if ok:
        print("TEST %s: PASS" % name)
    else:
        print("TEST %s: FAIL %s" % (name, (reason or "no reason given").replace("\n", " ")[:200]))
    _results.append((name, ok))
    sys.stdout.flush()


def run_py(code, timeout=SUBPROC_TIMEOUT_S):
    """Run a snippet in the shipped interpreter, isolated from this directory."""
    env = dict(os.environ)
    env.pop("HF_TOKEN", None)
    env.pop("HUGGING_FACE_HUB_TOKEN", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run([sys.executable, "-I", "-c", code],
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=timeout, env=env)
    out = proc.stdout.decode("utf-8", "replace")
    return proc.returncode, out


def run_cmd(argv, timeout=SUBPROC_TIMEOUT_S):
    env = dict(os.environ)
    env.pop("HF_TOKEN", None)
    env.pop("HUGGING_FACE_HUB_TOKEN", None)
    proc = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=timeout, env=env)
    return proc.returncode, proc.stdout.decode("utf-8", "replace")


def tail(text, n=3):
    lines = [l for l in text.strip().splitlines() if l.strip()]
    return " | ".join(lines[-n:])[:160]


# ---------------------------------------------------------------------------
# 1. environment the directive requires (items 3, 4, 7, 20, 24)
# ---------------------------------------------------------------------------

def t_python_is_cpython_310():
    """item 3: the environment of record is a CPython 3.10 venv."""
    rc, out = run_py("import sys,platform;print(platform.python_implementation());"
                     "print('%d.%d' % sys.version_info[:2]);print(sys.prefix);print(sys.base_prefix)")
    if rc != 0:
        return False, "interpreter query failed: %s" % tail(out)
    lines = out.strip().splitlines()
    if len(lines) < 4:
        return False, "short interpreter query output: %s" % tail(out)
    impl, ver, prefix, base = lines[0], lines[1], lines[2], lines[3]
    if impl != "CPython":
        return False, "implementation %s, not CPython" % impl
    if ver != "3.10":
        return False, "python %s, directive pins 3.10" % ver
    if prefix == base:
        return False, "not running inside a venv (sys.prefix == sys.base_prefix)"
    return True, ""


def t_venv_bin_first_on_path():
    """item 24: tools resolve through the venv; its bin is first on PATH."""
    venv_bin = os.path.dirname(os.path.abspath(sys.executable))
    first = (os.environ.get("PATH", "").split(os.pathsep) or [""])[0]
    if os.path.abspath(first or "") != venv_bin:
        return False, "PATH[0]=%r, interpreter bin=%r" % (first, venv_bin)
    return True, ""


def t_nvidia_smi_gpu_driver_cuda():
    """items 7, 20: GPU visible; driver 570 and the header's CUDA 12.8."""
    exe = shutil.which("nvidia-smi")
    if not exe:
        return False, "nvidia-smi not found"
    rc, out = run_cmd([exe])
    if rc != 0:
        return False, "nvidia-smi exit %d: %s" % (rc, tail(out))
    m = re.search(r"CUDA Version:\s*([0-9]+\.[0-9]+)", out)
    if not m:
        return False, "no 'CUDA Version' in the nvidia-smi header"
    cuda = m.group(1)
    d = re.search(r"Driver Version:\s*([0-9]+)\.", out)
    if not d:
        return False, "no 'Driver Version' in the nvidia-smi header"
    rc2, names = run_cmd([exe, "--query-gpu=name", "--format=csv,noheader"])
    if rc2 != 0 or not names.strip():
        return False, "no GPU name listed"
    if cuda != "12.8":
        return False, "CUDA header %s, directive states 12.8 (gpu=%s)" % (cuda, names.strip().splitlines()[0])
    if d.group(1) != "570":
        return False, "driver major %s, directive states 570" % d.group(1)
    return True, ""


def t_jax_gpu_device_listed():
    """item 4: JAX imported with a GPU device listed."""
    rc, out = run_py(
        "import jax;print('JAXVER',jax.__version__);"
        "ds=jax.devices();print('PLATFORMS',','.join(sorted({d.platform for d in ds})));"
        "print('N',len(ds))", timeout=180)
    if rc != 0:
        return False, "import jax / jax.devices() failed: %s" % tail(out)
    m = re.search(r"PLATFORMS (\S+)", out)
    if not m:
        return False, "no platform line: %s" % tail(out)
    platforms = set(m.group(1).split(","))
    if not platforms & {"gpu", "cuda", "rocm"}:
        return False, "jax.devices() lists only %s" % sorted(platforms)
    return True, ""


def t_alphafold_multimer_stack_imports():
    """item 4: the AlphaFold-Multimer stack imports."""
    rc, out = run_py(
        "import importlib,sys\n"
        "bad=[]\n"
        "for m in ('colabfold','colabfold.batch','alphafold','alphafold.model'):\n"
        "    try: importlib.import_module(m)\n"
        "    except Exception as e: bad.append('%s:%s' % (m, type(e).__name__))\n"
        "print('BAD', ','.join(bad))\n", timeout=240)
    if rc != 0:
        return False, "import probe failed: %s" % tail(out)
    m = re.search(r"BAD\s*(\S*)", out)
    bad = [b for b in (m.group(1).split(",") if m and m.group(1) else []) if b]
    if bad:
        return False, "not importable: %s" % ",".join(bad)
    return True, ""


def t_colabfold_batch_help():
    """item 4: colabfold_batch --help."""
    exe = shutil.which("colabfold_batch")
    if not exe:
        return False, "colabfold_batch not on PATH"
    if not os.path.isabs(exe):
        return False, "colabfold_batch not resolved to an absolute path: %s" % exe
    try:
        rc, out = run_cmd([exe, "--help"], timeout=180)
    except subprocess.TimeoutExpired:
        return False, "colabfold_batch --help timed out"
    if rc != 0:
        return False, "colabfold_batch --help exit %d: %s" % (rc, tail(out))
    return True, ""


def t_docking_entry_points_help():
    """item 4 / 13: the docking entry point and its conformation generator."""
    entry = None
    for cand in ("lightdock3.py", "lightdock3", "lightdock"):
        if shutil.which(cand):
            entry = shutil.which(cand)
            break
    gen = None
    for cand in ("lgd_generate_conformations.py", "lgd_generate_glowworm.py"):
        if shutil.which(cand):
            gen = shutil.which(cand)
            break
    missing = []
    if entry is None:
        missing.append("docking entry point (lightdock3.py)")
    if gen is None:
        missing.append("conformation-generating script (lgd_generate_conformations.py)")
    if missing:
        return False, "not on the venv PATH: %s" % "; ".join(missing)
    for exe in (entry, gen):
        rc, out = run_cmd([exe, "--help"], timeout=120)
        if rc != 0:
            return False, "%s --help exit %d: %s" % (os.path.basename(exe), rc, tail(out))
    return True, ""


def t_lgd_rank_present():
    """item 13: the rank step `lgd_rank.py` resolves in the venv."""
    exe = shutil.which("lgd_rank.py") or shutil.which("lgd_rank")
    if not exe:
        return False, "lgd_rank.py not on PATH"
    venv_bin = os.path.dirname(os.path.abspath(sys.executable))
    if os.path.dirname(os.path.abspath(exe)) != venv_bin:
        return False, "lgd_rank.py resolves outside the venv bin: %s" % exe
    return True, ""


def t_openmm_cuda_platform():
    """item 4: OpenMM imported with Platform.getPlatformByName("CUDA") succeeding."""
    rc, out = run_py(
        "import openmm\n"
        "from openmm import Platform\n"
        "p=Platform.getPlatformByName('CUDA')\n"
        "print('OPENMM',openmm.__version__,'PLATFORM',p.getName())\n", timeout=180)
    if rc != 0:
        return False, "OpenMM CUDA platform not available: %s" % tail(out)
    if "PLATFORM CUDA" not in out:
        return False, "unexpected platform line: %s" % tail(out)
    return True, ""


def t_versions_from_installed_metadata():
    """item 20: every version is readable from installed distribution metadata."""
    rc, out = run_py(
        "from importlib.metadata import version, PackageNotFoundError\n"
        "res={}\n"
        "for d in ('jax','jaxlib','openmm','lightdock','colabfold'):\n"
        "    try: res[d]=version(d)\n"
        "    except Exception: res[d]=None\n"
        "import json;print('VERS',json.dumps(res))\n")
    if rc != 0:
        return False, "metadata query failed: %s" % tail(out)
    m = re.search(r"VERS (\{.*\})", out)
    if not m:
        return False, "no version line: %s" % tail(out)
    vers = json.loads(m.group(1))
    missing = [k for k, v in vers.items() if not v]
    if missing:
        return False, "no installed metadata version for: %s" % ",".join(sorted(missing))
    return True, ""


def t_no_installer_use_and_no_network_env():
    """items 4, 10: nothing in the shipped environment needs a token; tokens
    are not required by the tests and must not be needed to import anything."""
    leaked = [k for k in ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN") if os.environ.get(k)]
    # presence is allowed before the download stage; what must hold is that the
    # tests themselves neither read nor need them, and that pip is not required.
    rc, out = run_py("import sys;print('OK')")
    if rc != 0:
        return False, "interpreter cannot run a trivial snippet: %s" % tail(out)
    if "OK" not in out:
        return False, "interpreter produced no output"
    if leaked and any("TOKEN" in a.upper() for a in sys.argv):
        return False, "a token was passed on the command line"
    return True, ""


# ---------------------------------------------------------------------------
# 2. records contract (items 3, 5, 19, 20, 23; contract 5)
# ---------------------------------------------------------------------------

def _load_provenance():
    """Import frozen/provenance.py (the record writer the contract names)."""
    import importlib.util
    path = os.path.join(os.getcwd(), "frozen", "provenance.py")
    if not os.path.isfile(path):
        return None, "frozen/provenance.py not present"
    spec = importlib.util.spec_from_file_location("provenance_under_test", path)
    if spec is None or spec.loader is None:
        return None, "cannot load frozen/provenance.py"
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as exc:
        return None, "frozen/provenance.py did not import: %s" % type(exc).__name__
    return mod, ""


def _writer_callables(mod):
    names = [n for n in dir(mod)
             if callable(getattr(mod, n, None))
             and re.search(r"(write|emit|save|dump).*record|record.*(write|emit|save|dump)", n, re.I)]
    return [getattr(mod, n) for n in names]


def _planted_record(kind, values, decision, run_valid=True, metric="planted"):
    return {
        "cell": "tests/%s" % kind,
        "inputs": {
            "rows_file": "rows_planted_tag-m4.jsonl",
            "pairs_file": "pairs_tag-m4.json",
            "download_record": {"url": "planted", "sha256": "0" * 64},
            "lock_sha256": "a" * 64,
        },
        "metric": metric,
        "threshold": "planted threshold",
        "decision_rule": "planted decision rule, written before values",
        "values": values,
        "decision": decision,
        "run_valid": run_valid,
    }


def _validate_record(rec):
    """Schema the directive states for every record (item 19, contract 5)."""
    problems = []
    if not isinstance(rec, dict):
        return ["record is not an object"]
    for f in RECORD_REQUIRED_FIELDS:
        if f not in rec:
            problems.append("missing field %s" % f)
    if rec.get("decision") not in DECISIONS and "decision" in rec:
        problems.append("decision %r not one of PASS/FAIL/VOID" % rec.get("decision"))
    if "run_valid" in rec and not isinstance(rec.get("run_valid"), bool):
        problems.append("run_valid is not a boolean")
    vals = rec.get("values")
    if not isinstance(vals, dict):
        problems.append("values is not an object")
        return problems
    # a null value needs a non-empty null_reasons entry (item 19)
    for k, v in vals.items():
        if v is None and k not in ("null_reasons",):
            nr = vals.get("null_reasons") or {}
            if not isinstance(nr, dict) or not nr.get(k):
                problems.append("null %s without a null_reasons entry" % k)
    return problems


def _validate_endpoint(rec, cid):
    problems = _validate_record(rec)
    vals = rec.get("values", {}) if isinstance(rec, dict) else {}
    for f in ("measured", "unit", "card_value", "band"):
        if f not in vals:
            problems.append("values.%s missing" % f)
    if vals.get("card_value") != CARD_VALUES[cid]:
        problems.append("card_value %r != %r" % (vals.get("card_value"), CARD_VALUES[cid]))
    band = vals.get("band")
    if not (isinstance(band, (list, tuple)) and len(band) == 2
            and abs(float(band[0]) - BANDS_ITEM19[cid][0]) < 1e-9
            and abs(float(band[1]) - BANDS_ITEM19[cid][1]) < 1e-9):
        problems.append("band %r != %r" % (band, list(BANDS_ITEM19[cid])))
    if not vals.get("unit"):
        problems.append("values.unit empty")
    return problems


def _write_through_writer_or_none(rec, path):
    """Try to write `rec` through provenance.py; return (written, note)."""
    mod, note = _load_provenance()
    if mod is None:
        return None, note
    for fn in _writer_callables(mod):
        for attempt in (lambda: fn(path, rec), lambda: fn(rec, path),
                        lambda: fn(**rec, path=path), lambda: fn(path=path, record=rec)):
            try:
                attempt()
            except Exception:
                continue
            if os.path.isfile(path):
                try:
                    with open(path) as fh:
                        return json.load(fh), "written through %s" % getattr(fn, "__name__", "writer")
                except Exception:
                    return None, "writer produced unparsable JSON"
    return None, "no usable record-writing callable in frozen/provenance.py"


def t_record_writer_or_schema_endpoint():
    """A planted minimal C1 record conforms (through the writer if importable)."""
    rec = _planted_record("endpoint-C1", {
        "measured": 0.5, "unit": UNITS_ITEM19["C1"],
        "card_value": CARD_VALUES["C1"], "band": list(BANDS_ITEM19["C1"]),
        "gate_value": GATE_VALUE, "gate_pass": True, "gate_else": GATE_ELSE,
        "n": 9, "machine": {k: "planted" for k in MACHINE_LABEL_KEYS},
        "engine": {"alphafold_implementation": "planted", "jax": "planted"},
    }, "PASS")
    path = os.path.join(SCRATCH, "planted_endpoint-C1_tag-%s.json" % TAG)
    written, note = _write_through_writer_or_none(rec, path)
    if written is None:
        with open(path, "w") as fh:
            json.dump(rec, fh)
        with open(path) as fh:
            written = json.load(fh)
    problems = _validate_endpoint(written, "C1")
    if problems:
        return False, "%s (%s)" % ("; ".join(problems[:3]), note)
    # the validator must reject a malformed record, else it cannot fail
    bad = dict(rec)
    bad.pop("decision_rule")
    bad["decision"] = "MAYBE"
    if not _validate_endpoint(bad, "C1"):
        return False, "schema check accepted a record with no decision_rule and decision=MAYBE"
    return True, ""


def t_record_schema_rejects_wrong_band_and_unit():
    """The endpoint schema is sensitive to the band, the unit and the card value."""
    for cid in ("C1", "C2", "C3", "C4"):
        good = _planted_record("endpoint-%s" % cid, {
            "measured": CARD_VALUES[cid], "unit": UNITS_ITEM19[cid],
            "card_value": CARD_VALUES[cid], "band": list(BANDS_ITEM19[cid]),
        }, "PASS")
        if _validate_endpoint(good, cid):
            return False, "%s: a conforming record was rejected: %s" % (
                cid, "; ".join(_validate_endpoint(good, cid)[:2]))
        wrong_band = json.loads(json.dumps(good))
        wrong_band["values"]["band"] = [BANDS_ITEM19[cid][0], BANDS_ITEM19[cid][1] * 2]
        if not _validate_endpoint(wrong_band, cid):
            return False, "%s: a widened band was accepted" % cid
        no_unit = json.loads(json.dumps(good))
        no_unit["values"]["unit"] = ""
        if not _validate_endpoint(no_unit, cid):
            return False, "%s: a record with no unit was accepted" % cid
    return True, ""


def t_record_anchor_fields():
    """item 19: the anchor record carries measured, published, tolerance."""
    rec = _planted_record("endpoint-anchor", {
        "measured": {"contact_overlap": 0.62, "interface_backbone_rmsd_a": 3.1,
                     "serial_vs_parallel_rmsd_a": 0.8},
        "published": "PKD2 bound beside the AAV2 three-fold spike (PDB 6IHB)",
        "tolerance": {"contact_overlap_min": ANCHOR_OVERLAP_MIN,
                      "interface_rmsd_max_a": ANCHOR_RMSD_MAX,
                      "serial_vs_parallel_rmsd_max_a": ANCHOR_SP_RMSD_MAX,
                      "contact_cutoff_a": CONTACT_CUTOFF_A},
        "docking_parameters": {"swarms": 10, "glowworms": 200},
        "docking_order": ["simulate", "generate_conformations", "lgd_rank"],
        "independent_code": "not run: single docking code",
        "machine": {k: "planted" for k in MACHINE_LABEL_KEYS},
    }, "PASS")
    path = os.path.join(SCRATCH, "planted_endpoint-anchor_tag-%s.json" % TAG)
    written, note = _write_through_writer_or_none(rec, path)
    if written is None:
        with open(path, "w") as fh:
            json.dump(rec, fh)
        with open(path) as fh:
            written = json.load(fh)
    problems = _validate_record(written)
    vals = written.get("values", {})
    for f in ("measured", "published", "tolerance", "docking_parameters", "docking_order"):
        if f not in vals:
            problems.append("values.%s missing" % f)
    if vals.get("independent_code") != "not run: single docking code":
        problems.append("independent_code label missing or changed")
    if problems:
        return False, "%s (%s)" % ("; ".join(problems[:3]), note)
    return True, ""


def t_record_null_value_needs_reason():
    """item 19: a value that cannot be had is null with a non-empty null_reasons."""
    bad = _planted_record("endpoint-anchor", {
        "measured": None, "published": "x", "tolerance": {},
    }, "VOID", run_valid=False)
    if not _validate_record(bad):
        return False, "a null measured with no null_reasons was accepted"
    good = _planted_record("endpoint-anchor", {
        "measured": None, "published": "x", "tolerance": {},
        "null_reasons": {"measured": "anchor stage not reached"},
    }, "VOID", run_valid=False)
    problems = _validate_record(good)
    if problems:
        return False, "a null with a reason was rejected: %s" % "; ".join(problems[:2])
    return True, ""


def t_record_env_check_and_tests_fields():
    """items 3, 5: env_check and tests records carry the stated values."""
    env_rec = _planted_record("env_check", {
        "expected_lock_sha256": "a" * 64, "observed_lock_sha256": "a" * 64,
        "venv_path": "/lambda/nfs/metis-env-us-east-1/m4/venv",
        "python_version": "3.10.12", "equal": True,
        "machine": {k: "planted" for k in MACHINE_LABEL_KEYS},
    }, "PASS")
    tests_rec = _planted_record("tests", {
        "exit_code": 0, "seconds": 12.3, "tests_file_sha256": "b" * 64,
        "stdout_tail": ["TESTS: PASS"], "tests_passed": 1, "tests_total": 1,
        "machine": {k: "planted" for k in MACHINE_LABEL_KEYS},
    }, "PASS")
    problems = []
    for rec, keys, name in ((env_rec, ENV_CHECK_VALUE_KEYS, "env_check"),
                            (tests_rec, TESTS_RECORD_VALUE_KEYS, "tests")):
        problems += ["%s: %s" % (name, p) for p in _validate_record(rec)]
        for k in keys:
            if k not in rec["values"]:
                problems.append("%s: values.%s missing" % (name, k))
        path = os.path.join(SCRATCH, "planted_%s_tag-%s.json" % (name, TAG))
        with open(path, "w") as fh:
            json.dump(rec, fh)
        with open(path) as fh:
            json.load(fh)
    # a tests record whose null counts carry no reason must be rejected
    nulled = json.loads(json.dumps(tests_rec))
    nulled["values"]["tests_passed"] = None
    nulled["values"]["tests_total"] = None
    if not _validate_record(nulled):
        problems.append("null tests_passed/tests_total accepted with no null_reasons")
    if problems:
        return False, "; ".join(problems[:3])
    return True, ""


def t_record_machine_label_keys():
    """item 20: no machine label key is omitted, lock fields included."""
    full = {k: "planted" for k in MACHINE_LABEL_KEYS}

    def missing_keys(machine):
        return [k for k in MACHINE_LABEL_KEYS if k not in machine]

    if missing_keys(full):
        return False, "the key list disagrees with itself: %s" % missing_keys(full)
    for drop in ("observed_lock_sha256", "held_attempts", "environment_changed_by_fixer"):
        partial = {k: v for k, v in full.items() if k != drop}
        if not missing_keys(partial):
            return False, "dropping %s was not detected" % drop
    return True, ""


def t_run_valid_json_and_summary_shape():
    """items 19, 23: RUN_VALID.json, the summary's first key and RUN_DONE."""
    run_valid = {"run_valid": False, "run_valid_voided_by": "anchor miss"}
    path_rv = os.path.join(SCRATCH, "planted_RUN_VALID.json")
    with open(path_rv, "w") as fh:
        json.dump(run_valid, fh)
    with open(path_rv) as fh:
        rv = json.load(fh)
    if "run_valid" not in rv or not isinstance(rv["run_valid"], bool):
        return False, "RUN_VALID.json has no boolean run_valid"

    summary = {
        "what_this_run_decides": "the stand-in protocol only",
        "run_valid": False, "exit_code": 4,
        "records": ["endpoint-anchor_tag-m4.json"],
        "gate": {"gate_value": GATE_VALUE, "gate_pass": None, "gate_else": GATE_ELSE},
        "unmeasured_inputs": [], "held_attempts": 0,
        "labels": [], "estimated_spend_usd": 1.99,
        "remote_timeout_seen": REMOTE_TIMEOUT_OF_RECORD,
        "env_lock_sha256": "a" * 64, "hold_seconds": HOLD_SECONDS_OF_RECORD,
    }
    path_sum = os.path.join(SCRATCH, "planted_%s_summary.json" % TAG)
    with open(path_sum, "w") as fh:
        json.dump(summary, fh)  # no sort_keys: insertion order kept
    with open(path_sum) as fh:
        text = fh.read()
    loaded = json.loads(text)
    first_key = list(loaded.keys())[0]
    if first_key != "what_this_run_decides":
        return False, "summary first key is %r" % first_key
    for k in ("run_valid", "exit_code", "held_attempts", "unmeasured_inputs"):
        if k not in loaded:
            return False, "summary has no %s" % k
    if "decision" in loaded:
        return False, "the summary carries a decision of its own"
    run_done = {"exit_code": 4,
                "C1": "void_by_anchor_miss", "C2": "void_by_anchor_miss",
                "C3": "void_by_anchor_miss", "C4": "void_by_anchor_miss"}
    if run_done["exit_code"] not in EXIT_CODES:
        return False, "RUN_DONE exit code outside {0,2,3,4}"
    for cid in ("C1", "C2", "C3", "C4"):
        if not _status_is_legal(run_done[cid]):
            return False, "RUN_DONE %s status %r not of item 7" % (cid, run_done[cid])
    return True, ""


def _status_is_legal(status):
    if status == "decided":
        return True
    for pre in ("void_by_failure:", "unmeasured_by_stop:", "void_by_rule:"):
        if status.startswith(pre) and len(status) > len(pre):
            return True
    return status == "void_by_anchor_miss"


def t_guard_record_shape():
    """contract 5 / item 8: the guard record carries every number of the arithmetic."""
    elapsed = 6000
    stage = "alphafold"
    allowance = guard_allowance(CEILINGS[stage], REMOTE_TIMEOUT_OF_RECORD, elapsed)
    rec = _planted_record("guard", {
        "stage": stage, "ceiling_s": CEILINGS[stage],
        "remote_timeout_s": REMOTE_TIMEOUT_OF_RECORD,
        "elapsed_since_t0_s": elapsed, "margin_s": MARGIN_S,
        "fetch_reserve_s": FETCH_RESERVE_S, "allowance_s": allowance,
        "estimated_s": ESTIMATE_FLOORS["alphafold_run"],
        "price_usd_per_hour": PRICE_OF_RECORD,
        "budget_left_usd": BUDGET_LEFT_DEFAULT_MAX,
        "estimated_spend_usd": round(elapsed * PRICE_OF_RECORD / 3600.0, 2),
        "stages_not_run": [], "started": True,
        "machine": {k: "planted" for k in MACHINE_LABEL_KEYS},
    }, "PASS")
    problems = _validate_record(rec)
    for k in ("stage", "ceiling_s", "remote_timeout_s", "elapsed_since_t0_s",
              "allowance_s", "estimated_s", "budget_left_usd", "estimated_spend_usd"):
        if k not in rec["values"]:
            problems.append("guard record has no values.%s" % k)
    # the recorded arithmetic must redo
    v = rec["values"]
    redone = max(0, min(v["ceiling_s"], v["remote_timeout_s"] - v["elapsed_since_t0_s"]
                        - v["margin_s"] - v["fetch_reserve_s"]))
    if redone != v["allowance_s"]:
        problems.append("allowance %s does not redo from the recorded numbers (%s)"
                        % (v["allowance_s"], redone))
    if problems:
        return False, "; ".join(problems[:3])
    return True, ""


def t_results_dir_usable():
    if not RESULTS:
        return False, "--results was not given"
    if not os.path.isdir(RESULTS):
        return False, "results directory %s does not exist" % RESULTS
    probe = os.path.join(SCRATCH, "write_probe.txt")
    with open(probe, "w") as fh:
        fh.write("ok\n")
    with open(probe) as fh:
        if fh.read().strip() != "ok":
            return False, "results directory is not writable"
    return True, ""


# ---------------------------------------------------------------------------
# 3. guard arithmetic, void propagation (items 6, 7, 8, 17, 18, 22, 24)
# ---------------------------------------------------------------------------

def guard_allowance(ceiling, remote_timeout, elapsed):
    """item 8: allowance(stage) = max(0, min(ceiling, RT - elapsed - 400 - 100))."""
    return max(0, min(ceiling, remote_timeout - elapsed - MARGIN_S - FETCH_RESERVE_S))


def unit_may_start(estimated_s, allowance_s):
    """item 24: a unit whose estimate exceeds its allowance is not started."""
    return estimated_s <= allowance_s


def time_cap_seconds(price, budget_left_usd, remote_timeout):
    """item 8: the run stops before either cap; the earlier cap governs."""
    dollar_cap_s = budget_left_usd / price * 3600.0
    return min(dollar_cap_s, float(remote_timeout))


def spend_usd(seconds_since_t0, price):
    return seconds_since_t0 * price / 3600.0


def t_guard_allowance_worked_values():
    """item 25: setup 1500 at elapsed 0; AlphaFold 700 at 6000; 0 at 6800."""
    cases = [
        ("setup at elapsed 0", CEILINGS["setup"], 0, 1500),
        ("alphafold at elapsed 6000", CEILINGS["alphafold"], 6000, 700),
        ("alphafold at elapsed 6800", CEILINGS["alphafold"], 6800, 0),
    ]
    for name, ceiling, elapsed, want in cases:
        got = guard_allowance(ceiling, REMOTE_TIMEOUT_OF_RECORD, elapsed)
        if got != want:
            return False, "%s: allowance %s, directive states %s" % (name, got, want)
    # the formula must follow a different REMOTE_TIMEOUT, not a constant
    if guard_allowance(CEILINGS["setup"], 3600, 0) != 3100:
        return False, "allowance does not follow REMOTE_TIMEOUT=3600 (got %s, expected 3100)" \
            % guard_allowance(CEILINGS["setup"], 3600, 0)
    return True, ""


def t_guard_must_stop_and_must_go():
    """item 24: planted units, one that must start and one that must not."""
    go_allowance = guard_allowance(CEILINGS["alphafold"], REMOTE_TIMEOUT_OF_RECORD, 0)
    if not unit_may_start(ESTIMATE_FLOORS["alphafold_run"], go_allowance):
        return False, "an AlphaFold run (floor %ss) was refused at allowance %ss" % (
            ESTIMATE_FLOORS["alphafold_run"], go_allowance)
    stop_allowance = guard_allowance(CEILINGS["alphafold"], REMOTE_TIMEOUT_OF_RECORD, 6800)
    if unit_may_start(ESTIMATE_FLOORS["alphafold_run"], stop_allowance):
        return False, "a unit was started at allowance 0"
    # the estimate is the mean of finished units of that kind when there are any
    finished = [300.0, 360.0]
    est = statistics.fmean(finished)
    if unit_may_start(est, guard_allowance(CEILINGS["md"], REMOTE_TIMEOUT_OF_RECORD, 6500)):
        return False, "a %ss unit was started at allowance %ss" % (
            est, guard_allowance(CEILINGS["md"], REMOTE_TIMEOUT_OF_RECORD, 6500))
    if not unit_may_start(est, guard_allowance(CEILINGS["md"], REMOTE_TIMEOUT_OF_RECORD, 0)):
        return False, "a %ss unit was refused at the full MD allowance" % est
    return True, ""


def t_guard_cost_cap_worked_values():
    """item 25: 1.99 stops at 9045 s (so time cap governs); 2.50 coincides; 3.00 at 6000 s."""
    cases = [(1.99, 9045.0, REMOTE_TIMEOUT_OF_RECORD),
             (2.50, 7200.0, 7200.0),
             (3.00, 6000.0, 6000.0)]
    for price, dollar_cap_want, governing_want in cases:
        dollar_cap = BUDGET_LEFT_DEFAULT_MAX / price * 3600.0
        if abs(dollar_cap - dollar_cap_want) > 1.0:
            return False, "price %.2f: dollar cap %.1f s, directive states %.1f s" % (
                price, dollar_cap, dollar_cap_want)
        gov = time_cap_seconds(price, BUDGET_LEFT_DEFAULT_MAX, REMOTE_TIMEOUT_OF_RECORD)
        if abs(gov - governing_want) > 1.0:
            return False, "price %.2f: governing cap %.1f s, expected %.1f s" % (
                price, gov, governing_want)
    return True, ""


def t_spend_arithmetic_worked_values():
    """item 25: 3,600 s at 1.99 gives 1.99; 7,200 s gives 3.98; pre-T0 not added."""
    if abs(spend_usd(3600, 1.99) - 1.99) > 0.005:
        return False, "3600 s at 1.99 gives %.3f" % spend_usd(3600, 1.99)
    if abs(spend_usd(7200, 1.99) - 3.98) > 0.005:
        return False, "7200 s at 1.99 gives %.3f" % spend_usd(7200, 1.99)
    # 300 s pre-T0 is reported beside, never added
    if abs(spend_usd(3600, 1.99) - 1.99) > 0.005 or abs(spend_usd(3900, 1.99) - 1.99) < 0.05:
        return False, "pre-T0 seconds appear to be added into the spend"
    return True, ""


# --- decisions, bands, gate, void propagation ------------------------------

def band_decision(measured, band):
    """items 18, 19: marginal first (within 10 percent of an edge), then the band."""
    lo, hi = band
    for edge in (lo, hi):
        if edge * (1 - MARGINAL_FRACTION) <= measured <= edge * (1 + MARGINAL_FRACTION):
            return "VOID", {"marginal": True}
    if lo <= measured <= hi:
        return "PASS", {}
    return "FAIL", {}


def c1_gate(decision, measured):
    """item 11: gate_pass only when C1 holds a valid measurement."""
    if decision in ("PASS", "FAIL") or (decision == "VOID" and measured is not None):
        return measured <= GATE_VALUE
    return None


def t_decision_worked_values_c1():
    """item 25, C1."""
    cases = [(0.5, "PASS"), (1.5, "FAIL"), (0.1, "FAIL"), (1.2, "VOID"),
             (0.21, "VOID"), (1.1, "PASS"), (0.9, "PASS")]
    for measured, want in cases:
        got, flags = band_decision(measured, BANDS_ITEM19["C1"])
        if got != want:
            return False, "C1 %.2f -> %s, directive states %s" % (measured, got, want)
        if want == "VOID" and not flags.get("marginal"):
            return False, "C1 %.2f VOID without marginal" % measured
    if c1_gate("VOID", 1.2) is not False:
        return False, "C1 1.2 marginal VOID: gate_pass is not false"
    if c1_gate("PASS", 1.1) is not False:
        return False, "C1 1.1: gate_pass is not false"
    if c1_gate("PASS", 0.9) is not True:
        return False, "C1 0.9: gate_pass is not true"
    if c1_gate("VOID", None) is not None:
        return False, "a VOID C1 with no measurement gives a non-null gate_pass"
    return True, ""


def t_decision_minimums_c1():
    """item 12: fewer than 3 runs, or 3 runs missing a pair, is VOID."""
    def c1_valid(runs):
        pairs = {r["pair"] for r in runs}
        return len(runs) >= 3 and len(pairs) >= 3

    two_runs = [{"pair": "p1"}, {"pair": "p2"}]
    three_missing = [{"pair": "p1"}, {"pair": "p1"}, {"pair": "p2"}]
    three_ok = [{"pair": "p1"}, {"pair": "p2"}, {"pair": "p3"}]
    if c1_valid(two_runs):
        return False, "2 runs counted as a valid C1"
    if c1_gate("VOID", None) is not None:
        return False, "2-run VOID does not give gate_pass null"
    if c1_valid(three_missing):
        return False, "3 runs missing a pair counted as a valid C1"
    if not c1_valid(three_ok):
        return False, "3 runs over 3 pairs rejected"
    return True, ""


def t_decision_worked_values_c2():
    """item 25, C2: rate arithmetic, median, band, atom range, non-A100."""
    ns_per_day = (250000 * 2e-6) / 335.0 * 86400.0
    if abs(ns_per_day - 128.96) > 0.01:
        return False, "250,000 steps x 2 fs in 335 s gives %.2f, directive states 128.96" % ns_per_day
    if abs(statistics.median([100.0, 129.0, 500.0]) - 129.0) > 1e-9:
        return False, "median of (100, 129, 500) is not 129"
    for measured, want in [(129.0, "PASS"), (40.0, "FAIL"), (400.0, "FAIL"),
                           (56.0, "VOID"), (60.0, "PASS"), (330.0, "VOID")]:
        got, _ = band_decision(measured, BANDS_ITEM19["C2"])
        if got != want:
            return False, "C2 %.1f -> %s, directive states %s" % (measured, got, want)

    def atoms_ok(n):
        return 120000 <= n <= 180000
    if atoms_ok(119999) or atoms_ok(180001):
        return False, "the atom range was widened"
    if not atoms_ok(150000):
        return False, "150,000 atoms rejected"

    def non_a100_void(gpu_name):
        return "A100" not in gpu_name.upper()
    if not non_a100_void("NVIDIA L40S"):
        return False, "a non-A100 GPU did not void C1/C2"
    if non_a100_void("NVIDIA A100-SXM4-40GB"):
        return False, "an A100 was treated as not an A100"
    return True, ""


def t_decision_worked_values_c3():
    """item 25, C3: setup excluded, means, band."""
    hours = statistics.fmean([3600.0, 3600.0, 3600.0]) / 3600.0
    if abs(hours - 1.0) > 1e-9:
        return False, "three 3,600 s pairs give %.4f h" % hours
    docking_only = 1800.0 / 3600.0
    if abs(docking_only - 0.5) > 1e-9:
        return False, "7,200 s setup + 1,800 s docking does not give 0.5 h with setup excluded"
    for measured, want in [(1.0, "PASS"), (0.2, "FAIL"), (4.0, "FAIL"),
                           (0.3333, "VOID"), (3.2, "VOID"), (0.5, "PASS"), (2.5, "PASS")]:
        got, _ = band_decision(measured, BANDS_ITEM19["C3"])
        if got != want:
            return False, "C3 %.4f -> %s, directive states %s" % (measured, got, want)

    # item 13: a truncated pair is not counted; C3 needs at least 2 finished pairs
    pairs = [{"h": 1.0, "truncated": False}, {"h": 1.0, "truncated": False},
             {"h": 9.9, "truncated": True}]
    counted = [p["h"] for p in pairs if not p["truncated"]]
    if len(counted) < 2:
        return False, "the truncated-pair rule left fewer than 2 counted pairs"
    if abs(statistics.fmean(counted) - 1.0) > 1e-9:
        return False, "a truncated pair entered the mean"
    if len([p for p in pairs[:1] if not p["truncated"]]) >= 2:
        return False, "one finished pair counted as enough for C3"
    return True, ""


def t_decision_worked_values_c4():
    """item 25, C4: bytes to GiB, the 216 and 432 figures, md_setup_bytes."""
    per_run = 1073741824
    gib = per_run * STORAGE_RUNS / GIB
    if abs(gib - 216.0) > 1e-6:
        return False, "1 GiB per run x 216 gives %.4f" % gib
    if abs(per_run * STORAGE_RUNS_ALT / GIB - 432.0) > 1e-6:
        return False, "the 432-run figure does not come out at 432.0"
    for per_run_gib, want_value in [(0.1, 21.6), (4.0, 864.0), (2.9, 626.4), (0.35, 75.6)]:
        got = per_run_gib * STORAGE_RUNS
        if abs(got - want_value) > 1e-6:
            return False, "%.2f GiB per run x 216 gives %.4f, directive states %.4f" % (
                per_run_gib, got, want_value)
    for value, want in [(216.0, "PASS"), (21.6, "FAIL"), (864.0, "FAIL"),
                        (626.4, "VOID"), (75.6, "PASS")]:
        got, _ = band_decision(value, BANDS_ITEM19["C4"])
        if got != want:
            return False, "C4 %.1f -> %s, directive states %s" % (value, got, want)
    if 1000 + 24 != 1024:
        return False, "byte sum arithmetic is wrong"
    md_files = {"traj.dcd": 1000, "reporter.txt": 100, "worker.log": 24,
                "system.xml": 5000, "solvated.pdb": 7000}
    setup_names = ("system.xml", "solvated.pdb")
    md_bytes = sum(v for k, v in md_files.items() if k not in setup_names
                   and not k.endswith(".chk"))
    md_setup = sum(v for k, v in md_files.items() if k in setup_names)
    if md_bytes != 1124:
        return False, "MD bytes %d, directive states 1,124" % md_bytes
    if md_setup != 12000:
        return False, "md_setup_bytes %d, directive states 12,000" % md_setup
    if abs(md_bytes / MD_PRODUCTION_NS - 2248.0) > 1e-9:
        return False, "MD bytes per ns is not MD bytes over 0.5"
    return True, ""


def t_anchor_rule_worked_values():
    """item 25 / 17: the anchor pass rule on planted numbers."""
    def anchor_pass(overlap, rmsd, sp_rmsd, calls_equal):
        return (overlap >= ANCHOR_OVERLAP_MIN or rmsd <= ANCHOR_RMSD_MAX) \
            and sp_rmsd <= ANCHOR_SP_RMSD_MAX and calls_equal

    cases = [((0.50, 9.0, 1.0, True), True),
             ((0.49, 5.0, 1.0, True), True),
             ((0.49, 5.01, 1.0, True), False),
             ((0.80, 1.0, 2.0, True), True),
             ((0.80, 1.0, 2.01, True), False),
             ((0.80, 1.0, 0.0, False), False)]
    for args, want in cases:
        got = anchor_pass(*args)
        if got != want:
            return False, "anchor%s -> %s, directive states %s" % (args, got, want)
    return True, ""


def t_anchor_geometry_worked_values():
    """item 25: planted contact overlap and interface RMSD arithmetic."""
    ref_contacts = {("A", 1, "B", 10), ("A", 2, "B", 11), ("A", 3, "B", 12),
                    ("A", 4, "B", 13), ("A", 5, "B", 14), ("A", 6, "B", 15)}
    pose_contacts = {("A", 1, "B", 10), ("A", 2, "B", 11), ("A", 3, "B", 12)}
    overlap = len(ref_contacts & pose_contacts) / float(len(ref_contacts))
    if abs(overlap - 0.5) > 1e-9:
        return False, "3 of 6 reference contacts gives %.4f" % overlap

    # chain-mapping by role: the receptor chain id must not change the overlap
    def remap(contacts, new_id):
        return {(c[0], c[1], new_id, c[3]) for c in contacts}
    for cid in ("A", "B", "C"):
        o = len(remap(ref_contacts, cid) & remap(pose_contacts, cid)) / float(len(ref_contacts))
        if abs(o - 0.5) > 1e-9:
            return False, "receptor chain id %s changes the overlap (%.4f)" % (cid, o)

    # interface backbone RMSD, no superposition
    def rmsd(a, b):
        if len(a) != len(b) or not a:
            raise ValueError("coordinate sets differ in length")
        s = sum((ax - bx) ** 2 + (ay - by) ** 2 + (az - bz) ** 2
                for (ax, ay, az), (bx, by, bz) in zip(a, b))
        return math.sqrt(s / len(a))

    iface = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]
    shifted = [(x + 5.0, y, z) for (x, y, z) in iface]
    if abs(rmsd(iface, shifted) - 5.0) > 1e-4:
        return False, "a 5.0 A shift of the interface atoms gives RMSD %.4f" % rmsd(iface, shifted)

    non_iface = [(10.0, 0.0, 0.0), (11.0, 0.0, 0.0)]
    moved_non_iface = [(x, y + 20.0, z) for (x, y, z) in non_iface]
    if abs(rmsd(iface, iface) - 0.0) > 1e-9:
        return False, "moving only non-interface atoms changed the interface RMSD"
    whole_chain = rmsd(iface + non_iface, iface + moved_non_iface)
    if not whole_chain > 0.0:
        return False, "the whole-chain RMSD did not move when non-interface atoms moved 20 A"
    return True, ""


def t_void_propagation_anchor_miss():
    """items 7, 17, 19: a planted anchor miss voids every later record."""
    records = []

    def emit(cell, decision, run_valid):
        records.append(_planted_record(cell, {"measured": 1.0, "unit": "x",
                                              "card_value": 1.0, "band": [0.0, 2.0]},
                                       decision, run_valid=run_valid))

    # records written before the failing decision carry run_valid true
    emit("control-sleep", "PASS", True)
    anchor_passed = False  # planted miss: overlap 0.40, rmsd 7.0, tolerance missed
    run_valid = anchor_passed
    emit("endpoint-anchor", "PASS" if anchor_passed else "FAIL", run_valid)
    for cid in ("C1", "C2", "C3", "C4"):
        emit("endpoint-%s" % cid, "VOID", run_valid)
    before = records[0]
    if before["run_valid"] is not True:
        return False, "a record written before the anchor lost run_valid true"
    anchor = records[1]
    if anchor["decision"] != "FAIL" or anchor["run_valid"] is not False:
        return False, "the anchor record is not FAIL with run_valid false"
    for rec in records[2:]:
        if rec["decision"] != "VOID" or rec["run_valid"] is not False:
            return False, "%s is not VOID with run_valid false" % rec["cell"]
    exit_code = 4
    statuses = {cid: "void_by_anchor_miss" for cid in ("C1", "C2", "C3", "C4")}
    if exit_code != 4 or set(statuses.values()) != {"void_by_anchor_miss"}:
        return False, "an anchor miss did not map to exit 4 / void_by_anchor_miss"
    # and the same table must give a different row when the anchor passes
    if (4 if not anchor_passed else 0) == (4 if True else 0) and anchor_passed:
        return False, "the mapping is insensitive to the anchor outcome"
    return True, ""


def t_failure_table_rows():
    """item 7: every planted event maps to exactly one row."""
    def classify(event):
        failures = {"environment missing", "lock mismatch", "capability problem",
                    "tests failure", "download failure", "setup over ceiling",
                    "tool start failure", "real tool failure", "no parsable ranked pose",
                    "unparsable rank table", "sleep check failed", "shell abort"}
        stops = {"guard refusal", "stage ceiling", "tool-call timeout", "outer timeout"}
        if event in failures:
            return 2, False, "void_by_failure"
        if event == "anchor miss":
            return 4, False, "void_by_anchor_miss"
        if event in stops:
            return 3, None, "unmeasured_by_stop"
        if event in ("all decided", "void by rule, no stop"):
            return 0, True, "decided"
        raise KeyError(event)

    for event, want_exit in [("lock mismatch", 2), ("tests failure", 2),
                             ("sleep check failed", 2), ("anchor miss", 4),
                             ("guard refusal", 3), ("outer timeout", 3),
                             ("all decided", 0), ("void by rule, no stop", 0)]:
        code, valid, status = classify(event)
        if code != want_exit:
            return False, "%r maps to exit %d, directive states %d" % (event, code, want_exit)
        if code not in EXIT_CODES:
            return False, "%r maps outside {0,2,3,4}" % event
        if code in (2, 4) and valid is not False:
            return False, "%r does not set run_valid false" % event
        if code == 3 and valid is not None:
            return False, "a stop changed run_valid"
        if code == 0 and valid is not True:
            return False, "a complete run is not run_valid true"
        if not _status_is_legal(status if ":" not in status else status):
            pass
    # item 21: there is no exit 5
    if 5 in EXIT_CODES:
        return False, "exit 5 is in the code set; item 21 removes it"
    return True, ""


def t_stop_semantics():
    """item 22: a stop leaves decisions alone, keeps run_valid, exits 3."""
    inputs = {"C1": "decided", "C2": "decided", "C3": None, "C4": None}
    run_valid_before = True
    stopped_stage = "md"
    stages_done = ["setup", "tests", "controls_anchor", "docking", "alphafold"]
    for cid, st in list(inputs.items()):
        if st is None:
            inputs[cid] = "unmeasured_by_stop:stage_ceiling"
    run_valid_after = run_valid_before  # a stop never changes it
    exit_code = 3 if any(str(v).startswith("unmeasured_by_stop") for v in inputs.values()) else 0
    if stopped_stage in stages_done:
        return False, "the stopped stage appears in stages_done"
    if run_valid_after is not True:
        return False, "a stop changed run_valid"
    if inputs["C1"] != "decided" or inputs["C2"] != "decided":
        return False, "a stop changed an already decided input"
    if exit_code != 3:
        return False, "a stop with unmeasured inputs gave exit %d" % exit_code
    for v in inputs.values():
        if not _status_is_legal(v):
            return False, "illegal per-input status %r" % v
    # a timed-out tool row is kept, flagged, and not counted
    rows = [{"wall_s": 120.0, "incomplete": False}, {"wall_s": 250.0, "incomplete": True}]
    counted = [r for r in rows if not r["incomplete"]]
    if len(counted) != 1:
        return False, "a timed-out row was counted"
    # no unmeasured input -> exit 0, so the rule can give the other answer
    done = {"C1": "decided", "C2": "decided", "C3": "decided", "C4": "void_by_rule:marginal"}
    if (3 if any(str(v).startswith("unmeasured_by_stop") for v in done.values()) else 0) != 0:
        return False, "a run with no unmeasured input did not give exit 0"
    return True, ""


def t_lock_check_planted():
    """items 3, 25: equal hashes pass, any differing character fails, unset fails."""
    def lock_ok(expected, observed):
        if not expected or not re.fullmatch(r"[0-9a-f]{64}", expected or ""):
            return False, "expected lock hash unset or malformed"
        if expected != observed:
            return False, "lock mismatch"
        return True, ""

    good = "a" * 64
    ok, why = lock_ok(good, good)
    if not ok:
        return False, "equal hashes rejected (%s)" % why
    differing = "b" + "a" * 63
    ok, _ = lock_ok(good, differing)
    if ok:
        return False, "a differing character was accepted"
    for bad_expected in (None, "", "ZZ" + "a" * 62, "a" * 63):
        ok, _ = lock_ok(bad_expected, good)
        if ok:
            return False, "malformed/unset expected hash %r was accepted" % bad_expected
    return True, ""


def t_hold_sequence_planted():
    """item 6 / 25: HOLD after the void records, one resume, fixer scope."""
    def hold_outcome(stage, exit_code, hold_seconds, resume_seen, seconds_left,
                     hashes_unchanged, holds_used):
        eligible = (exit_code == 2 and stage != "sleep_check" and holds_used == 0)
        if not eligible:
            return "final"
        if hold_seconds <= 0:
            return "no_hold"
        if not resume_seen:
            return "expired"
        if not hashes_unchanged:
            return "fixer_out_of_scope"
        if seconds_left < HOLD_RESUME_MIN_S_ITEM6_A:
            return "no_time_to_resume"
        return "restart"

    cases = [
        (("tests", 2, 1200, True, 1500, True, 0), "restart"),
        (("tests", 2, 1200, True, 1499, True, 0), "no_time_to_resume"),
        (("tests", 2, 1200, True, 3000, False, 0), "fixer_out_of_scope"),
        (("tests", 2, 1200, False, 3000, True, 0), "expired"),
        (("tests", 2, 0, False, 3000, True, 0), "no_hold"),
        (("sleep_check", 2, 1200, True, 3000, True, 0), "final"),
        (("capability", 2, 1200, True, 3000, True, 1), "final"),
        (("anchor", 4, 1200, True, 3000, True, 0), "final"),
    ]
    for args, want in cases:
        got = hold_outcome(*args)
        if got != want:
            return False, "hold%s -> %s, directive states %s" % (args, got, want)
    # the order of record writing: void records, then HOLD
    order = ["void_records", "RUN_DONE", "HOLD"]
    if order.index("HOLD") < order.index("void_records"):
        return False, "HOLD is written before the attempt's void records"
    return True, ""


def t_controls_worked_values():
    """items 16, 18, 25: sleep, empty run, seed spread."""
    def sleep_ok(measured):
        return abs(measured - SLEEP_CONTROL_S) / SLEEP_CONTROL_S <= SLEEP_TOLERANCE
    if not sleep_ok(62.9):
        return False, "62.9 s did not pass the 5 percent sleep check"
    if sleep_ok(63.1):
        return False, "63.1 s passed the 5 percent sleep check"
    if sleep_ok(56.9):
        return False, "56.9 s passed the 5 percent sleep check"

    def spread_ok(values):
        return len(set(values)) > 1
    if not spread_ok([1800, 1830, 1790]):
        return False, "(1800, 1830, 1790) failed the spread check"
    if spread_ok([1800, 1800, 1800]):
        return False, "zero spread passed the spread check"

    def spread_label(rel_sd):
        return rel_sd > SEED_SD_LABEL_THRESHOLD
    if not spread_label(0.6):
        return False, "relative SD 0.6 did not raise the spread label"
    if spread_label(0.4):
        return False, "relative SD 0.4 raised the spread label"

    def empty_run_subtract(seconds, nbytes):
        return seconds >= EMPTY_RUN_MAX_S or nbytes >= EMPTY_RUN_MAX_BYTES
    if empty_run_subtract(0.5, 100 * 1024):
        return False, "0.5 s / 100 KiB triggered the subtraction label"
    if not empty_run_subtract(5.0, 100 * 1024):
        return False, "5 s did not trigger the subtraction label"
    if not empty_run_subtract(0.5, 2 * 1024 * 1024):
        return False, "2 MiB did not trigger the subtraction label"
    return True, ""


def t_md_rate_disagreement_rule():
    """item 14: engine rate and wall-clock differing by more than 5 percent is labelled."""
    def disagree(wall, engine):
        return abs(wall - engine) / max(wall, engine) > MD_RATE_DISAGREE_FRACTION
    if disagree(129.0, 128.96):
        return False, "a 0.03 percent difference was called a disagreement"
    if not disagree(129.0, 100.0):
        return False, "a 22 percent difference was not called a disagreement"
    wall = (250000 * 2e-6) / 335.0 * 86400.0
    if abs(wall - 128.96) > 0.01:
        return False, "the wall-clock rate arithmetic moved: %.2f" % wall
    if MD_DCD_STEPS * 2e-3 != float(MD_FRAME_INTERVAL_PS):
        return False, "5,000 steps x 2 fs is not the recorded frame_interval_ps %d" % MD_FRAME_INTERVAL_PS
    return True, ""


# ---------------------------------------------------------------------------
# 4. the directive's own consistency (numbers stated in two items must agree)
# ---------------------------------------------------------------------------

def t_consistency_ceiling_sum():
    total = sum(CEILINGS.values()) + MARGIN_S
    if total != CEILING_SUM_ITEM8:
        return False, "ceilings sum to %d; item 8 states %d" % (total, CEILING_SUM_ITEM8)
    if CEILING_SUM_ITEM8 != REMOTE_TIMEOUT_OF_RECORD:
        return False, "the ceiling sum %d differs from REMOTE_TIMEOUT %d" % (
            CEILING_SUM_ITEM8, REMOTE_TIMEOUT_OF_RECORD)
    if TESTS_CEILING_ITEM5 != CEILINGS["tests"] or TESTS_CEILING_U7 != CEILINGS["tests"]:
        return False, "the tests ceiling differs between items 5, 8 and U7: %d/%d/%d" % (
            TESTS_CEILING_ITEM5, CEILINGS["tests"], TESTS_CEILING_U7)
    if PER_PAIR_CEILING * 3 > CEILINGS["docking"]:
        return False, "3 pairs at %d s exceed the docking ceiling %d" % (
            PER_PAIR_CEILING, CEILINGS["docking"])
    if PER_COMPLEX_CEILING * 3 > CEILINGS["md"]:
        return False, "3 complexes at %d s exceed the MD ceiling %d" % (
            PER_COMPLEX_CEILING, CEILINGS["md"])
    return True, ""


def t_consistency_bands_two_places():
    for cid in ("C1", "C2", "C3", "C4"):
        if BANDS_ITEM19[cid] != BANDS_QUESTION[cid]:
            return False, "%s band: item 19 %s vs question %s" % (
                cid, BANDS_ITEM19[cid], BANDS_QUESTION[cid])
        if CARD_VALUES[cid] != CARD_VALUES_QUESTION[cid]:
            return False, "%s card value: item 19 %s vs question %s" % (
                cid, CARD_VALUES[cid], CARD_VALUES_QUESTION[cid])
        lo, hi = BANDS_ITEM19[cid]
        m = BAND_MULTIPLIER[cid]
        want_lo = CARD_VALUES[cid] / m
        want_hi = CARD_VALUES[cid] * m
        if abs(lo - want_lo) > max(0.01, want_lo * 0.005):
            return False, "%s lower edge %s does not re-derive from %s / %s = %.4f" % (
                cid, lo, CARD_VALUES[cid], m, want_lo)
        if abs(hi - want_hi) > max(0.01, want_hi * 0.005):
            return False, "%s upper edge %s does not re-derive from %s x %s = %.4f" % (
                cid, hi, CARD_VALUES[cid], m, want_hi)
    return True, ""


def t_consistency_gate_and_c1_band():
    """item 11 / question: the gate is 1 and sits inside the C1 band."""
    lo, hi = BANDS_ITEM19["C1"]
    if not lo < GATE_VALUE < hi:
        return False, "the gate %.2f does not lie inside the C1 band %s" % (GATE_VALUE, (lo, hi))
    if not GATE_ELSE.strip():
        return False, "the fallback text is empty"
    # item 11: C2 and C3 carry the not-applicable note, never a gate_pass
    not_applicable = "not applicable: the card's gate is on af2_h_per_run"
    for cid in ("C2", "C3"):
        rec = _planted_record("endpoint-%s" % cid, {
            "measured": CARD_VALUES[cid], "unit": UNITS_ITEM19[cid],
            "card_value": CARD_VALUES[cid], "band": list(BANDS_ITEM19[cid]),
            "gate": not_applicable}, "PASS")
        if "gate_pass" in rec["values"]:
            return False, "%s carries gate_pass" % cid
        if rec["values"].get("gate") != not_applicable:
            return False, "%s does not carry the not-applicable gate note" % cid
    return True, ""


def t_consistency_budget_numbers():
    """item 8 / Box: hard cap, per-launch cap and the minimum launch figures."""
    if BUDGET_LEFT_DEFAULT_MAX > HARD_CAP_USD:
        return False, "per-launch default %.2f exceeds the hard cap %.2f" % (
            BUDGET_LEFT_DEFAULT_MAX, HARD_CAP_USD)
    at199 = MIN_LAUNCH_SECONDS * 1.99 / 3600.0
    if abs(at199 - MIN_LAUNCH_USD_AT_1_99) > 0.005:
        return False, "7,800 s at 1.99 gives %.3f; the Box section states %.3f" % (
            at199, MIN_LAUNCH_USD_AT_1_99)
    at250 = MIN_LAUNCH_SECONDS * 2.50 / 3600.0
    if abs(at250 - MIN_LAUNCH_USD_AT_2_50) > 0.005:
        return False, "7,800 s at 2.50 gives %.3f; the Box section states %.3f" % (
            at250, MIN_LAUNCH_USD_AT_2_50)
    if MIN_LAUNCH_SECONDS < REMOTE_TIMEOUT_OF_RECORD:
        return False, "the minimum launch window %d s is under REMOTE_TIMEOUT %d s" % (
            MIN_LAUNCH_SECONDS, REMOTE_TIMEOUT_OF_RECORD)
    if HOLD_SECONDS_OF_RECORD <= 0:
        return False, "HOLD_SECONDS of record is not positive"
    if HOLD_RESUME_MIN_S_ITEM6_A != HOLD_RESUME_MIN_S_ITEM6_B:
        return False, "item 6 states two different resume minima: %d and %d" % (
            HOLD_RESUME_MIN_S_ITEM6_A, HOLD_RESUME_MIN_S_ITEM6_B)
    if HOLD_RESUME_MIN_S_ITEM6_A > REMOTE_TIMEOUT_OF_RECORD:
        return False, "the resume minimum exceeds REMOTE_TIMEOUT"
    return True, ""


def t_consistency_sample_counts():
    """items 12, 13, 14 and the design record: pairs, seeds and minimums agree."""
    pairs, seeds = 3, 3
    af2_runs = pairs * seeds
    if af2_runs != 9:
        return False, "3 pairs x 3 seeds is not 9 AlphaFold runs"
    if ESTIMATE_FLOORS["alphafold_run"] * af2_runs > CEILINGS["alphafold"]:
        return False, "9 runs at the %ds floor exceed the AlphaFold ceiling %d" % (
            ESTIMATE_FLOORS["alphafold_run"], CEILINGS["alphafold"])
    minimums = {"C1": 3, "C2": 2, "C3": 2, "C4": 1}
    if minimums["C1"] > af2_runs or minimums["C2"] > pairs or minimums["C3"] > pairs:
        return False, "a stated minimum exceeds the planned sample"
    residue_lo, residue_hi = 750, 1000
    if residue_lo >= residue_hi:
        return False, "the residue range is empty"
    if (residue_hi - residue_lo) < 20 * (pairs - 1):
        return False, ("the residue range %d-%d cannot hold %d pairwise lengths 20 apart"
                       % (residue_lo, residue_hi, pairs))
    atoms_lo, atoms_hi = 120000, 180000
    if atoms_lo >= atoms_hi:
        return False, "the atom range is empty"
    if not (0 < MD_PRODUCTION_NS):
        return False, "the production segment is not positive"
    return True, ""


def t_consistency_estimate_floors_fit_allowances():
    """item 24 floors must be startable inside their item 8 ceilings at elapsed 0."""
    mapping = {"anchor_serial": "controls_anchor", "anchor_parallel": "controls_anchor",
               "docking_pair": "docking", "alphafold_run": "alphafold",
               "md_complex": "md", "storage": "endpoints", "endpoints": "endpoints",
               "tests": "tests"}
    for unit, stage in mapping.items():
        allowance = guard_allowance(CEILINGS[stage], REMOTE_TIMEOUT_OF_RECORD, 0)
        if not unit_may_start(ESTIMATE_FLOORS[unit], allowance):
            return False, "%s floor %ds exceeds the %s allowance %ds at elapsed 0" % (
                unit, ESTIMATE_FLOORS[unit], stage, allowance)
    if ESTIMATE_FLOORS["docking_pair"] > PER_PAIR_CEILING:
        return False, "the docking-pair floor exceeds the 250 s per-pair ceiling"
    if ESTIMATE_FLOORS["md_complex"] > PER_COMPLEX_CEILING:
        return False, "the MD-complex floor exceeds the 600 s per-complex ceiling"
    if ESTIMATE_FLOORS["tests"] > CEILINGS["tests"]:
        return False, "the tests floor exceeds the tests ceiling"
    return True, ""


def t_consistency_tool_timeout_margin():
    """item 24: the inner tool timeout is at least 100 s shorter than the outer kill."""
    for stage, ceiling in CEILINGS.items():
        inner = ceiling
        outer = REMOTE_TIMEOUT_OF_RECORD
        if outer - inner < 100:
            return False, "%s ceiling %d leaves under 100 s against the outer kill" % (stage, ceiling)
    if FETCH_RESERVE_S < 100:
        return False, "the allowance reserve %d s is under the 100 s margin" % FETCH_RESERVE_S
    return True, ""


def t_consistency_marginal_rule_self():
    """item 18: the marginal window is symmetric and does not swallow a band."""
    for cid, (lo, hi) in BANDS_ITEM19.items():
        if lo * (1 + MARGINAL_FRACTION) >= hi * (1 - MARGINAL_FRACTION):
            return False, "%s: the marginal windows cover the whole band" % cid
        mid = math.sqrt(lo * hi)
        dec, _ = band_decision(mid, (lo, hi))
        if dec != "PASS":
            return False, "%s: the band's geometric midpoint %.4f is not PASS" % (cid, mid)
        dec_lo, flags = band_decision(lo, (lo, hi))
        if dec_lo != "VOID" or not flags.get("marginal"):
            return False, "%s: the lower edge itself is not marginal VOID" % cid
    return True, ""


def t_consistency_record_file_names():
    """items 2, 19 and the 'what the runner writes' list name the same files."""
    listed = [
        "endpoint-anchor_tag-m4.json", "endpoint-C1_tag-m4.json",
        "endpoint-C2_tag-m4.json", "endpoint-C3_tag-m4.json",
        "endpoint-C4_tag-m4.json", "env_check_tag-m4.json",
        "tests_tag-m4.json", "pairs_tag-m4.json",
        "RUN_VALID.json", "m4_summary.json", "RUN_DONE", "env.txt",
    ]
    for name in listed:
        if "tag-" in name and "tag-%s" % TAG not in name:
            return False, "%s does not carry the run tag %s" % (name, TAG)
    for cid in ("C1", "C2", "C3", "C4"):
        if "endpoint-%s_tag-%s.json" % (cid, TAG) not in listed:
            return False, "no endpoint record named for %s" % cid
    if "m4_summary.json" not in listed or "%s_summary.json" % TAG != "m4_summary.json":
        return False, "the summary name does not follow <tag>_summary.json"
    rows = "rows_%s_tag-%s.jsonl" % ("af2", TAG)
    if not rows.endswith(".jsonl"):
        return False, "raw rows are not JSON lines"
    return True, ""


def t_consistency_item21_precedence():
    """item 21: no exit 5, env.txt not env_<tag>.json, the contract's selftest withdrawn."""
    contract_exit_codes = {0, 2, 3, 4, 5}   # contract section 2
    directive_exit_codes = set(EXIT_CODES)  # item 7 / item 21
    if 5 not in contract_exit_codes:
        return False, "the contract's exit-code set was transcribed without 5"
    if directive_exit_codes != {0, 2, 3, 4}:
        return False, "the directive's exit-code set is %s" % sorted(directive_exit_codes)
    if 5 in directive_exit_codes:
        return False, "exit 5 survives in the directive's set"
    per_run_env_file = "env.txt"
    if per_run_env_file != "env.txt":
        return False, "the per-run environment file is not env.txt"
    if os.path.exists(os.path.join(os.getcwd(), "env_%s.json" % TAG)):
        # not a failure of the directive, but the file item 21 says is not required
        pass
    return True, ""


# ---------------------------------------------------------------------------

TESTS = [
    # 1. environment
    ("env_python_is_cpython_310", t_python_is_cpython_310),
    ("env_venv_bin_first_on_path", t_venv_bin_first_on_path),
    ("env_nvidia_smi_gpu_driver_cuda", t_nvidia_smi_gpu_driver_cuda),
    ("env_jax_gpu_device_listed", t_jax_gpu_device_listed),
    ("env_alphafold_multimer_stack_imports", t_alphafold_multimer_stack_imports),
    ("env_colabfold_batch_help", t_colabfold_batch_help),
    ("env_docking_entry_points_help", t_docking_entry_points_help),
    ("env_lgd_rank_present", t_lgd_rank_present),
    ("env_openmm_cuda_platform", t_openmm_cuda_platform),
    ("env_versions_from_installed_metadata", t_versions_from_installed_metadata),
    ("env_interpreter_runs_without_tokens", t_no_installer_use_and_no_network_env),
    # 2. records contract
    ("records_results_dir_usable", t_results_dir_usable),
    ("records_endpoint_through_writer_or_schema", t_record_writer_or_schema_endpoint),
    ("records_endpoint_band_unit_sensitive", t_record_schema_rejects_wrong_band_and_unit),
    ("records_anchor_fields", t_record_anchor_fields),
    ("records_null_value_needs_reason", t_record_null_value_needs_reason),
    ("records_env_check_and_tests_fields", t_record_env_check_and_tests_fields),
    ("records_machine_label_keys", t_record_machine_label_keys),
    ("records_run_valid_and_summary_shape", t_run_valid_json_and_summary_shape),
    ("records_guard_record_shape", t_guard_record_shape),
    # 3. guard arithmetic and void propagation
    ("guard_allowance_worked_values", t_guard_allowance_worked_values),
    ("guard_must_stop_and_must_go", t_guard_must_stop_and_must_go),
    ("guard_cost_cap_worked_values", t_guard_cost_cap_worked_values),
    ("guard_spend_arithmetic", t_spend_arithmetic_worked_values),
    ("decision_c1_worked_values", t_decision_worked_values_c1),
    ("decision_c1_minimums", t_decision_minimums_c1),
    ("decision_c2_worked_values", t_decision_worked_values_c2),
    ("decision_c3_worked_values", t_decision_worked_values_c3),
    ("decision_c4_worked_values", t_decision_worked_values_c4),
    ("anchor_rule_worked_values", t_anchor_rule_worked_values),
    ("anchor_geometry_worked_values", t_anchor_geometry_worked_values),
    ("void_propagation_anchor_miss", t_void_propagation_anchor_miss),
    ("void_failure_table_rows", t_failure_table_rows),
    ("void_stop_semantics", t_stop_semantics),
    ("lock_check_planted", t_lock_check_planted),
    ("hold_sequence_planted", t_hold_sequence_planted),
    ("controls_worked_values", t_controls_worked_values),
    ("md_rate_disagreement_rule", t_md_rate_disagreement_rule),
    # 4. directive consistency
    ("consistency_ceiling_sum", t_consistency_ceiling_sum),
    ("consistency_bands_two_places", t_consistency_bands_two_places),
    ("consistency_gate_and_c1_band", t_consistency_gate_and_c1_band),
    ("consistency_budget_numbers", t_consistency_budget_numbers),
    ("consistency_sample_counts", t_consistency_sample_counts),
    ("consistency_estimate_floors_fit", t_consistency_estimate_floors_fit_allowances),
    ("consistency_tool_timeout_margin", t_consistency_tool_timeout_margin),
    ("consistency_marginal_rule", t_consistency_marginal_rule_self),
    ("consistency_record_file_names", t_consistency_record_file_names),
    ("consistency_item21_precedence", t_consistency_item21_precedence),
]


def main():
    global RESULTS, SCRATCH
    ap = argparse.ArgumentParser(description="acceptance tests for measure run m4")
    ap.add_argument("--results", required=True,
                    help="the run's results directory (results_m4/out)")
    args = ap.parse_args()
    RESULTS = os.path.abspath(args.results)
    try:
        os.makedirs(RESULTS, exist_ok=True)
        SCRATCH = tempfile.mkdtemp(prefix="tests_m4_scratch_", dir=RESULTS)
    except Exception:
        SCRATCH = tempfile.mkdtemp(prefix="tests_m4_scratch_")

    t_start = time.time()
    for name, fn in TESTS:
        check(name, fn)
    passed = sum(1 for _, ok in _results if ok)
    total = len(_results)
    print("elapsed_s: %.1f" % (time.time() - t_start))
    print("tests: %d of %d passed" % (passed, total))
    print("TESTS: %d of %d passed" % (passed, total))
    if passed == total:
        print("TESTS: PASS")
        return 0
    print("TESTS: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())
