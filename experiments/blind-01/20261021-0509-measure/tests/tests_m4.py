#!/usr/bin/env python3
"""Tests of the measurement run m4, through the stage interface only.

The runner is called only as

    <python> <runner> --stage <name> --in <dir> --out <dir>

in fresh temporary directories (its working directory is a temporary copy of
the box's payload layout, i.e. a directory holding frozen/provenance.py), with
every external program replaced through the directive's environment variable
(M4_COLABFOLD, M4_LIGHTDOCK_SETUP, M4_LIGHTDOCK, M4_LGD_GENERATE, M4_LGD_RANK,
M4_MD_WORKER, M4_NVIDIA_SMI, M4_FETCH, M4_SLEEP, M4_PYTHON) by a small replay
program written into the temporary directory.  A replay prints the output
recorded on the box (tests/fixtures/) and writes the files the real program
writes into its working directory; it reads the files its own earlier calls
wrote, so a stage that mixes up working directories makes the replay fail the
way the real program would.  Parsers are imported from the --runner path.
The runner's source is never read.

Fixtures: tests/fixtures/MANIFEST.json (source path in the archive, sha256,
what each stands for, malformed or not).  Every fixture is hash-checked
before use.

Output: one line "TEST <name>: PASS" or "TEST <name>: FAIL <reason>" per test,
then "TESTS: <passed> of <total> passed" and "TESTS: PASS" or "TESTS: FAIL"
(exit code 1 on FAIL).  No GPU, no network.
"""

import argparse
import hashlib
import importlib.util
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
RUN_DIR = os.path.dirname(HERE)
FIXTURES = os.path.join(HERE, "fixtures")
PYTHON = sys.executable
LOCK = "f2b089a164ab725bdec6b06e97c79b2f45586bd0b68ff49600dbc90d1bf6c85d"
PDB_SHA = "d3f489cc062d0a4a92490774a51f85782439d5ffd9bfae9445f4f10bf7e0f2c4"
BOX_FAIL_RMSD = 38.61633372529515
STAGES = ["capability", "downloads", "controls", "anchor", "aux", "af2", "md", "storage", "endpoints"]
CARD = {"C1": (0.5, [0.2, 1.25]), "C2": (129, [51.6, 322.5]), "C3": (1, [0.3333, 3]), "C4": (200, [66.67, 600])}

RUNNER = None
_MOD = None
_MANIFEST = None
_CHECKED = set()
OUTSIDE_WRITES = []
WORLDS = []


class Fail(Exception):
    pass


def need(cond, msg):
    if not cond:
        raise Fail(msg)


# ------------------------------------------------------------------ files

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jload(path):
    with open(path) as f:
        return json.load(f)


def jlines(path):
    out = []
    with open(path) as f:
        for ln in f:
            if ln.strip():
                out.append(json.loads(ln))
    return out


def manifest():
    global _MANIFEST
    if _MANIFEST is None:
        _MANIFEST = {e["file"]: e for e in jload(os.path.join(FIXTURES, "MANIFEST.json"))}
    return _MANIFEST


def fx(name):
    """path of a fixture, after checking its sha256 against the manifest"""
    path = os.path.join(FIXTURES, name)
    if name not in _CHECKED:
        ent = manifest().get(name)
        need(ent is not None, "fixture %s is not in MANIFEST.json" % name)
        need(os.path.exists(path), "fixture %s is missing" % name)
        need(sha256_file(path) == ent["sha256"], "fixture %s does not match its manifest sha256" % name)
        _CHECKED.add(name)
    return path


def fx_text(name):
    with open(fx(name)) as f:
        return f.read()


# --------------------------------------------------------- generic search

def walk(obj, path=""):
    yield path, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            for item in walk(v, path + "." + str(k)):
                yield item
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            for item in walk(v, path + "[%d]" % i):
                yield item


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def find_keys(obj, pattern):
    """(path, value) for every dict key matching the regex"""
    rx = re.compile(pattern, re.I)
    out = []
    for p, v in walk(obj):
        if isinstance(v, dict):
            for k, val in v.items():
                if rx.search(str(k)):
                    out.append((p + "." + str(k), val))
    return out


def nums_at(obj, pattern):
    return [v for _, v in find_keys(obj, pattern) if is_num(v)]


def any_num_close(obj, pattern, target, tol):
    return any(abs(v - target) <= tol for v in nums_at(obj, pattern))


def plain(obj):
    if isinstance(obj, dict):
        return {str(k): plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [plain(v) for v in obj]
    return obj


def text_of(obj):
    return json.dumps(plain(obj), default=str)


# ------------------------------------------------------------------ PDB

def pdb_atoms(path):
    out = []
    with open(path) as f:
        for ln in f:
            if ln.startswith(("ATOM  ", "HETATM")):
                out.append(ln.rstrip("\n"))
    return out


def atom_xyz(ln):
    return float(ln[30:38]), float(ln[38:46]), float(ln[46:54])


def set_xyz(ln, xyz):
    return ln[:30] + "%8.3f%8.3f%8.3f" % xyz + ln[54:]


def chain_of(ln):
    return ln[21]


def reference_lines():
    """the hash-verified reference: chains A and R of pair_pair1 (equal to 6IHB's A and R)"""
    pairs = jload(fx("pairs_tag-m4.json"))
    p1 = [p for p in pairs["pairs"] if p["pair"] == "pair1"][0]
    need(sha256_file(fx("pair_pair1_tag-m4.pdb")) == p1["pdb_sha256"],
         "reference copy pair_pair1 does not match the sha256 recorded on the box")
    return [ln for ln in pdb_atoms(fx("pair_pair1_tag-m4.pdb")) if chain_of(ln) in "AR"]


def rot_matrix(axis, deg):
    x, y, z = axis
    n = math.sqrt(x * x + y * y + z * z)
    x, y, z = x / n, y / n, z / n
    a = math.radians(deg)
    c, s, t = math.cos(a), math.sin(a), 1 - math.cos(a)
    return [[t * x * x + c, t * x * y - s * z, t * x * z + s * y],
            [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
            [t * x * z - s * y, t * y * z + s * x, t * z * z + c]]


def transform_lines(lines, rot=None, shift=(0.0, 0.0, 0.0), centre=(0.0, 0.0, 0.0), only_chain=None):
    out = []
    for ln in lines:
        if only_chain is not None and chain_of(ln) != only_chain:
            out.append(ln)
            continue
        x, y, z = atom_xyz(ln)
        x, y, z = x - centre[0], y - centre[1], z - centre[2]
        if rot is not None:
            x, y, z = (rot[0][0] * x + rot[0][1] * y + rot[0][2] * z,
                       rot[1][0] * x + rot[1][1] * y + rot[1][2] * z,
                       rot[2][0] * x + rot[2][1] * y + rot[2][2] * z)
            x, y, z = x + centre[0], y + centre[1], z + centre[2]
        out.append(set_xyz(ln, (x + shift[0], y + shift[1], z + shift[2])))
    return out


def write_pdb(path, lines):
    with open(path, "w") as f:
        for ln in lines:
            f.write(ln + "\n")
        f.write("END\n")


# ---------------------------------------------------------- the runner

def runner_module():
    global _MOD
    if _MOD is None:
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("m4_runner_under_test", RUNNER)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            raise Fail("importing the runner raised %s: %s" % (type(e).__name__, e))
        _MOD = mod
    return _MOD


def parser(name):
    fn = getattr(runner_module(), name, None)
    need(callable(fn), "the runner has no module-level function %s" % name)
    return fn


def parse_ok(name, path):
    try:
        got = parser(name)(path)
    except Exception as e:
        raise Fail("%s raised on the recorded output %s: %s: %s" % (name, os.path.basename(path), type(e).__name__, str(e)[:200]))
    need(isinstance(got, dict), "%s returned %s, not a dict" % (name, type(got).__name__))
    return got


def parse_bad(name, path):
    try:
        got = parser(name)(path)
    except ValueError as e:
        return str(e)
    except Exception as e:
        raise Fail("%s on malformed %s raised %s, not ValueError" % (name, os.path.basename(path), type(e).__name__))
    raise Fail("%s accepted malformed %s and returned %s" % (name, os.path.basename(path), text_of(got)[:160]))


# ------------------------------------------------------- replay programs

REPLAY_CORE = r'''
import json, math, os, shutil, sys, tarfile, io, time

BIN = os.path.dirname(os.path.abspath(__file__))


def cfg():
    with open(os.path.join(BIN, "config.json")) as f:
        return json.load(f)


def bump(key):
    p = os.path.join(BIN, "state.json")
    st = {}
    if os.path.exists(p):
        with open(p) as f:
            st = json.load(f)
    st[key] = st.get(key, 0) + 1
    with open(p + ".tmp", "w") as f:
        json.dump(st, f)
    os.replace(p + ".tmp", p)
    return st[key]


def current(key):
    p = os.path.join(BIN, "state.json")
    if not os.path.exists(p):
        return 0
    with open(p) as f:
        return json.load(f).get(key, 0)


class Call(object):
    def __init__(self, tool):
        self.tool = tool
        self.seq = bump("all")
        self.tool_seq = bump("tool:" + tool)
        self.t0 = time.time()
        self.rec = {"tool": tool, "seq": self.seq, "tool_seq": self.tool_seq, "argv": sys.argv[1:], "cwd": os.getcwd(), "t0": self.t0}

    def done(self, rc=0, **extra):
        self.rec.update(extra)
        self.rec["t1"] = time.time()
        self.rec["rc"] = rc
        with open(os.path.join(BIN, "calls.jsonl"), "a") as f:
            f.write(json.dumps(self.rec) + "\n")
        sys.stdout.flush()
        sys.exit(rc)


def cat(path):
    with open(path) as f:
        sys.stdout.write(f.read())


def atoms(path):
    out = []
    with open(path) as f:
        for ln in f:
            if ln.startswith(("ATOM  ", "HETATM")):
                out.append(ln.rstrip("\n"))
    return out


def xyz(ln):
    return float(ln[30:38]), float(ln[38:46]), float(ln[46:54])


def setxyz(ln, p):
    return ln[:30] + "%8.3f%8.3f%8.3f" % p + ln[54:]


def centre(lines):
    n = float(len(lines))
    s = [0.0, 0.0, 0.0]
    for ln in lines:
        p = xyz(ln)
        for i in range(3):
            s[i] += p[i]
    return [round(s[i] / n, 3) for i in range(3)]


def moved(lines, d):
    return [setxyz(ln, tuple(xyz(ln)[i] + d[i] for i in range(3))) for ln in lines]


def rotated(lines, m, c):
    out = []
    for ln in lines:
        x, y, z = (xyz(ln)[i] - c[i] for i in range(3))
        out.append(setxyz(ln, (m[0][0] * x + m[0][1] * y + m[0][2] * z + c[0],
                               m[1][0] * x + m[1][1] * y + m[1][2] * z + c[1],
                               m[2][0] * x + m[2][1] * y + m[2][2] * z + c[2])))
    return out


def rot(axis, deg):
    x, y, z = axis
    n = math.sqrt(x * x + y * y + z * z)
    x, y, z = x / n, y / n, z / n
    a = math.radians(deg)
    c, s, t = math.cos(a), math.sin(a), 1 - math.cos(a)
    return [[t * x * x + c, t * x * y - s * z, t * x * z + s * y],
            [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
            [t * x * z - s * y, t * y * z + s * x, t * z * z + c]]


def write_lines(path, lines, remark=None):
    with open(path, "w") as f:
        if remark:
            f.write("REMARK   1 %s\n" % remark)
        for ln in lines:
            f.write(ln + "\n")
        f.write("END\n")


def help_or(call, text_path, usage):
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        if text_path:
            cat(text_path)
        else:
            print(usage)
        call.done(0, help=True)


def docking_conf(c, run):
    runs = c.get("docking_runs", [])
    d = dict(c.get("docking_default", {}))
    i = run - c.get("docking_offset", 0)
    if 1 <= i <= len(runs) and runs[i - 1]:
        d.update(runs[i - 1])
    return d


# ----------------------------------------------------------------- tools

def nvidia_smi(c, call):
    n = c["nvidia_smi"]
    args = sys.argv[1:]
    q = [a for a in args if a.startswith("--query-gpu=")]
    if n.get("rc", 0):
        cat(n["error"])
        call.done(n["rc"], form="error")
    if not q:
        if "-L" in args:
            print("GPU 0: NVIDIA A100-SXM4-40GB (UUID: GPU-00000000-0000-0000-0000-000000000000)")
            call.done(0, form="list")
        cat(n["header"])
        call.done(0, form="header")
    fields = q[0].split("=", 1)[1].split(",")
    if fields == ["name", "driver_version"]:
        cat(n["query"])
        call.done(0, form="query")
    nounits = any("nounits" in a for a in args)
    vals = {"name": "NVIDIA A100-SXM4-40GB", "driver_version": "570.148.08",
            "utilization.gpu": "0" if nounits else "0 %", "memory.used": "0" if nounits else "0 MiB",
            "memory.total": "40960" if nounits else "40960 MiB", "count": "1"}
    print(", ".join(vals.get(f.strip(), "[N/A]") for f in fields))
    call.done(0, form="query:" + ",".join(fields))


def python_probe(c, call):
    p = c["python"]
    args = sys.argv[1:]
    if args[:1] in (["--version"], ["-V"]):
        print("Python 3.10.12")
        call.done(0, probe="version")
    if "-m" in args and "pip" in args and "freeze" in args:
        cat(p["pip_freeze"])
        call.done(0, probe="pip_freeze")
    if "-c" in args:
        code = args[args.index("-c") + 1] if len(args) > args.index("-c") + 1 else ""
        if "jax" in code and "devices" in code:
            cat(p["imports"])
            call.done(0, probe="imports")
        if "importlib.metadata" in code or "distribution(" in code:
            cat(p["versions"])
            call.done(0, probe="versions")
        if any(w in code for w in ("jax", "openmm", "colabfold", "alphafold", "lightdock")):
            sys.stderr.write("replay: this probe was not recorded on the box\n")
            call.done(1, probe="unrecorded")
        r = __import__("subprocess").run([sys.executable, "-I"] + args)
        call.done(r.returncode, probe="generic")
    sys.stderr.write("replay python: not a recorded probe: %r\n" % (args,))
    call.done(1, probe="unknown")


def fetch(c, call):
    args = sys.argv[1:]
    out = None
    url = None
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-o", "--output", "-O") and i + 1 < len(args):
            out = args[i + 1]
            i += 2
            continue
        if a.startswith("http://") or a.startswith("https://"):
            url = a
        i += 1
    if url is None or out is None:
        sys.stderr.write("replay fetch: no url or no -o in %r\n" % (args,))
        call.done(2, url=url, out=out)
    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    f = c["fetch"]
    if url.endswith("6IHB.pdb"):
        shutil.copyfile(f["pdb"], out)
    elif url.endswith(".tar"):
        with tarfile.open(out, "w") as tf:
            names = ["params_model_%d_multimer_v3.npz" % m for m in range(1, 6)] + ["params_model_1.npz", "LICENSE"]
            for nm in names:
                data = (nm + " replay\n").encode()
                ti = tarfile.TarInfo(nm)
                ti.size = len(data)
                tf.addfile(ti, io.BytesIO(data))
    else:
        sys.stderr.write("curl: (22) The requested URL returned error: 404\n")
        call.done(22, url=url, out=out)
    call.done(0, url=url, out=out)


def sleep_(c, call):
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    want = float(args[0]) if args else 0.0
    s = c.get("sleep", {})
    secs = s.get("seconds", want * s.get("factor", 1.0))
    time.sleep(secs)
    call.done(0, slept=secs, asked=want)


# docking: one docking run = one lightdock3_setup.py call and what follows it

def ld_setup(c, call):
    help_or(call, None, "usage: lightdock3_setup.py [-h] receptor_pdb ligand_pdb [-s SWARMS] [-g GLOWWORMS] [--noxt] [--noh]")
    run = bump("docking_run")
    args = sys.argv[1:]
    pos = []
    opts = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-s", "--swarms", "-g", "--glowworms", "--seed_points", "-sp", "--seed_anm"):
            opts[a] = args[i + 1]
            i += 2
            continue
        if not a.startswith("-"):
            pos.append(a)
        i += 1
    if len(pos) < 2:
        sys.stderr.write("lightdock3_setup.py: error: the following arguments are required: receptor_pdb, ligand_pdb\n")
        call.done(2, docking_run=run)
    rec, lig = pos[0], pos[1]
    swarms = int(opts.get("-s", opts.get("--swarms", 10)))
    glow = int(opts.get("-g", opts.get("--glowworms", 200)))
    noxt = "--noxt" in args
    noh = "--noh" in args

    def keep(ln):
        name = ln[12:16].strip()
        if noxt and name == "OXT":
            return False
        if noh and (ln[76:78].strip() == "H" or name.startswith("H")):
            return False
        return True
    ra = [ln for ln in atoms(rec) if keep(ln)]
    la = [ln for ln in atoms(lig) if keep(ln)]
    cr, cl = centre(ra), centre(la)
    write_lines("lightdock_" + os.path.basename(rec), moved(ra, [-v for v in cr]))
    write_lines("lightdock_" + os.path.basename(lig), moved(la, [-v for v in cl]))
    os.makedirs("init", exist_ok=True)
    for s in range(swarms):
        os.makedirs("swarm_%d" % s, exist_ok=True)
        with open(os.path.join("init", "initial_positions_%d.dat" % s), "w") as f:
            for g in range(glow):
                f.write("%.3f %.3f %.3f 1.0 0.0 0.0 0.0\n" % (s, g, 0))
    with open(os.path.join("init", "swarm_centers.pdb"), "w") as f:
        f.write("ATOM      1  H   SWR A   1       0.000   0.000   0.000  1.00  0.00           H\nEND\n")
    setup = {"setup_version": "0.9.4", "receptor_pdb": rec, "ligand_pdb": lig, "swarms": swarms, "glowworms": glow,
             "starting_points_seed": 324324, "use_anm": False, "noxt": noxt, "noh": noh, "now": False,
             "replay_docking_run": run, "replay_receptor_centre": cr, "replay_ligand_centre": cl,
             "replay_work": os.getcwd()}
    with open("setup.json", "w") as f:
        json.dump(setup, f, indent=4)
    cat(c["docking_stdout"]["setup"])
    call.done(0, docking_run=run, swarms=swarms, glowworms=glow, receptor=rec, ligand=lig)


def own_setup(call, run, where="."):
    p = os.path.join(where, "setup.json")
    if not os.path.exists(p):
        sys.stderr.write("replay: setup.json not found in %s\n" % os.path.abspath(where))
        call.done(1, docking_run=run, error="no setup.json")
    with open(p) as f:
        s = json.load(f)
    if s.get("replay_docking_run") != run:
        sys.stderr.write("replay: setup.json in %s belongs to docking run %s, this is run %s\n" % (os.path.abspath(where), s.get("replay_docking_run"), run))
        call.done(1, docking_run=run, error="setup.json of another run")
    return s


def ld_simulate(c, call):
    help_or(call, c["help"].get("lightdock3.py"), "usage: lightdock3.py setup_file steps")
    run = current("docking_run")
    args = [a for a in sys.argv[1:]]
    pos = []
    i = 0
    while i < len(args):
        if args[i] in ("-c", "--cores", "-s", "-sg", "-t", "-r", "-f", "-ns", "-l"):
            i += 2
            continue
        if not args[i].startswith("-"):
            pos.append(args[i])
        i += 1
    setup_file = pos[0] if pos else "setup.json"
    steps = int(pos[1]) if len(pos) > 1 else 100
    s = own_setup(call, run, os.path.dirname(os.path.abspath(setup_file)))
    with open("lightdock.info", "w") as f:
        f.write("replay docking run %d steps %d\n" % (run, steps))
    for sw in range(s["swarms"]):
        d = "swarm_%d" % sw
        os.makedirs(d, exist_ok=True)
        for st in sorted(set([0] + list(range(10, steps + 1, 10)) + [steps])):
            with open(os.path.join(d, "gso_%d.out" % st), "w") as f:
                f.write("#Coordinates  RecID  LigID  Luciferin  Neighbor's number  Vision Range  Scoring\n")
                for g in range(s["glowworms"]):
                    f.write("(%.3f, %.3f, %.3f, 1.000, 0.000, 0.000, 0.000)    0    0  %.5f  0 5.000  %.3f\n" % (sw, g, st, -30.0 - g, -20.0 - g))
                f.write("#replay docking run %d swarm %d step %d\n" % (run, sw, st))
    cat(c["docking_stdout"]["simulate"])
    call.done(0, docking_run=run, steps=steps)


def gso_run(path):
    with open(path) as f:
        for ln in f:
            if ln.startswith("#replay docking run"):
                return int(ln.split()[3])
    return None


def ld_generate(c, call):
    help_or(call, c["help"].get("lgd_generate_conformations.py"), "usage: lgd_generate_conformations.py receptor ligand lightdock_output glowworms")
    run = current("docking_run")
    args = sys.argv[1:]
    pos = []
    i = 0
    while i < len(args):
        if args[i] in ("--setup", "-s"):
            i += 2
            continue
        if not args[i].startswith("-"):
            pos.append(args[i])
        i += 1
    if len(pos) < 4:
        sys.stderr.write("lgd_generate_conformations.py: error: arguments required\n")
        call.done(2, docking_run=run)
    rec, lig, gso, n = pos[0], pos[1], pos[2], int(pos[3])
    gso_abs = os.path.abspath(gso)
    outdir = os.path.dirname(gso_abs)
    if not os.path.exists(gso_abs) or gso_run(gso_abs) != run:
        sys.stderr.write("replay: %s is not the output of this docking run (%s)\n" % (gso_abs, run))
        call.done(1, docking_run=run, error="gso of another run", gso=gso_abs)
    work = os.path.dirname(outdir)
    s = own_setup(call, run, work)
    prec = os.path.join(os.path.dirname(os.path.abspath(rec)), "lightdock_" + os.path.basename(rec))
    plig = os.path.join(os.path.dirname(os.path.abspath(lig)), "lightdock_" + os.path.basename(lig))
    for p in (prec, plig):
        if not os.path.exists(p):
            sys.stderr.write("replay: processed structure %s missing\n" % p)
            call.done(1, docking_run=run, error="no processed structure")
    swarm = int(os.path.basename(outdir).split("_")[-1]) if os.path.basename(outdir).startswith("swarm_") else 0
    d = docking_conf(c, run)
    top = d.get("top", [0, 15])
    ra, la = atoms(prec), atoms(plig)
    cr, cl = s["replay_receptor_centre"], s["replay_ligand_centre"]
    native_lig = moved(la, [cl[i] - cr[i] for i in range(3)])
    mode = d.get("pose", "native")
    if mode == "file":
        best = atoms(d["pose_file"])
    elif mode == "self":
        best = moved(ra, cr) + moved(native_lig, cr)
    else:
        best = ra + moved(native_lig, d.get("ligand_shift", [0.0, 0.0, 0.0]))
    if d.get("rotate_deg"):
        best = rotated(best, rot(d.get("rotate_axis", [1.0, 2.0, 3.0]), d["rotate_deg"]), centre(best))
    if d.get("whole_shift"):
        best = moved(best, d["whole_shift"])
    decoy = ra + moved(native_lig, [40.0, 0.0, 0.0])
    wrote = []
    for g in range(n):
        p = os.path.join(outdir, "lightdock_%d.pdb" % g)
        is_top = (swarm == top[0] and g == top[1])
        lines = best if is_top else decoy
        if is_top and d.get("truncate_pose"):
            with open(p, "w") as f:
                f.write(("\n".join(lines) + "\n")[: d["truncate_pose"]])
        else:
            write_lines(p, lines, "replay docking run %d swarm %d glowworm %d" % (run, swarm, g))
        wrote.append(p)
    cat(c["docking_stdout"]["generate"])
    call.done(0, docking_run=run, swarm=swarm, outdir=outdir, n=n)


def ld_rank(c, call):
    run = current("docking_run")
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if len(args) < 2:
        sys.stderr.write("lgd_rank.py: error: num_swarms and steps required\n")
        call.done(2, docking_run=run)
    nsw, steps = int(args[0]), int(args[1])
    for sw in range(nsw):
        p = os.path.abspath(os.path.join("swarm_%d" % sw, "gso_%d.out" % steps))
        if not os.path.exists(p) or gso_run(p) != run:
            sys.stderr.write("replay: %s is not the output of this docking run (%s)\n" % (p, run))
            call.done(1, docking_run=run, error="gso of another run")
    d = docking_conf(c, run)
    with open(d.get("rank_table", c["docking_default"]["rank_table"])) as f:
        table = f.read()
    for nm in ("rank_by_scoring.list", "rank_by_luciferin.list", "rank_by_rmsd.list"):
        with open(nm, "w") as f:
            f.write(table)
    cat(c["docking_stdout"]["rank"])
    call.done(0, docking_run=run, table=d.get("rank_table"), cwd_table=os.path.abspath("rank_by_scoring.list"))


# AlphaFold through colabfold_batch

FLAGS = set(["--templates", "--amber", "--zip", "--save-all", "--save-recycles", "--use-gpu-relax", "--overwrite-existing-results",
             "--disable-unified-memory", "--use-dropout", "--disable-cluster-profile", "--save-single-representations",
             "--save-pair-representations", "--debug-logging", "--no-use-probs-extra"])


def colabfold(c, call):
    help_or(call, c["help"].get("colabfold_batch"), "usage: colabfold_batch input results")
    args = sys.argv[1:]
    pos = []
    opts = {}
    i = 0
    while i < len(args):
        a = args[i]
        if a.startswith("--") and "=" in a:
            k, v = a.split("=", 1)
            opts[k] = v
        elif a.startswith("-") and a not in FLAGS and i + 1 < len(args) and not args[i + 1].startswith("--"):
            opts[a] = args[i + 1]
            i += 1
        elif not a.startswith("-"):
            pos.append(a)
        i += 1
    cf = c["colabfold"]
    if len(pos) < 2:
        sys.stderr.write("colabfold_batch: error: input and results required\n")
        call.done(2)
    inp, res = os.path.abspath(pos[0]), os.path.abspath(pos[-1])
    seed = int(opts.get("--random-seed", 0))
    header = None
    with open(inp) as f:
        for ln in f:
            if ln.startswith(">"):
                header = ln[1:].strip()
                break
    job = "".join(ch if (ch.isalnum() or ch in "_.-") else "_" for ch in (header or "query"))
    os.makedirs(res, exist_ok=True)
    k = call.tool_seq
    times = [round(cf.get("base_model_s", 30.0) + 10.0 * k + m + 0.5, 1) for m in range(5)]
    lines = ["2026-10-21 23:00:00,001 Running on GPU",
             "2026-10-21 23:00:00,010 Query 1/1: %s (length %d)" % (header, 0)]
    data = opts.get("--data")
    downloaded = False
    if data and not os.path.exists(os.path.join(data, "params", "download_complexes_multimer_v3_finished.txt")):
        lines.append("2026-10-21 23:00:00,020 Downloading alphafold2_multimer_v3 weights to %s: 100%%|##########| 3.47G/3.47G" % data)
        downloaded = True
    mode = cf.get("mode", "ok")
    if mode == "error":
        lines.append("Traceback (most recent call last):")
        lines.append("jaxlib.xla_extension.XlaRuntimeError: RESOURCE_EXHAUSTED: Out of memory")
        txt = "\n".join(lines) + "\n"
        with open(os.path.join(res, "log.txt"), "w") as f:
            f.write(txt)
        sys.stdout.write(txt)
        call.done(1, pair=header, seed=seed, results=res, mode=mode)
    for m, t in enumerate(times, 1):
        lines.append("2026-10-21 23:0%d:00,000 alphafold2_multimer_v3_model_%d_seed_%03d recycle=20 pLDDT=41.2 pTM=0.312 ipTM=0.101" % (m, m, seed))
        if mode == "field_missing" and m == 3:
            lines.append("2026-10-21 23:0%d:01,000 alphafold2_multimer_v3_model_%d_seed_%03d took s (20 recycles)" % (m, m, seed))
        else:
            lines.append("2026-10-21 23:0%d:01,000 alphafold2_multimer_v3_model_%d_seed_%03d took %.1fs (20 recycles)" % (m, m, seed, t))
    lines.append("2026-10-21 23:06:00,000 reranking models by 'multimer' metric")
    for r in range(1, 6):
        lines.append("2026-10-21 23:06:00,%03d rank_%03d_alphafold2_multimer_v3_model_%d_seed_%03d pLDDT=41.2 pTM=0.312 ipTM=0.101" % (r, r, r, seed))
    lines.append("2026-10-21 23:06:01,000 Done")
    txt = "\n".join(lines) + "\n"
    with open(os.path.join(res, "log.txt"), "w") as f:
        f.write(txt)
    with open(os.path.join(res, "config.json"), "w") as f:
        json.dump({"num_models": 5, "num_recycles": 20, "recycle_early_stop_tolerance": 0.0, "msa_mode": "single_sequence",
                   "model_type": "alphafold2_multimer_v3", "random_seed": seed, "replay_call": k}, f)
    skip_score = cf.get("skip_score_call") == k
    for r in range(1, 6):
        stem = "%s_%%s_rank_%03d_alphafold2_multimer_v3_model_%d_seed_%03d" % (job, r, r, seed)
        with open(os.path.join(res, stem % "unrelaxed" + ".pdb"), "w") as f:
            f.write("REMARK   1 replay call %d\n" % k)
            f.write("ATOM      1  N   ASP A   1      %6.3f   0.000   0.000  1.00 41.20           N\n" % (k / 10.0))
            f.write("ATOM      2  CA  ASP A   1      %6.3f   1.458   0.000  1.00 41.20           C\n" % (k / 10.0))
            f.write("END\n")
        if not (skip_score and r == 1):
            with open(os.path.join(res, stem % "scores" + ".json"), "w") as f:
                json.dump({"plddt": [41.2, 41.2], "max_pae": 31.0, "pae": [[0.0, 1.0], [1.0, 0.0]], "ptm": 0.312, "iptm": 0.101, "replay_call": k}, f)
    with open(os.path.join(res, "%s_predicted_aligned_error_v1.json" % job), "w") as f:
        json.dump({"replay_call": k}, f)
    with open(os.path.join(res, "%s.done.txt" % job), "w") as f:
        f.write("")
    with open(os.path.join(res, "cite.bibtex"), "w") as f:
        f.write("@article{replay}\n")
    sys.stdout.write(txt)
    time.sleep(cf.get("sleep_s", 0.25) * k)
    call.done(0, pair=header, seed=seed, results=res, times=times, downloaded=downloaded, mode=mode, skipped_score=skip_score)


# molecular dynamics through the worker command (--mode build|run --pdb --work --out, its --help)

def md_opts(args):
    o = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--") and i + 1 < len(args) and not args[i + 1].startswith("--"):
            o[args[i]] = args[i + 1]
            i += 2
        else:
            i += 1
    return o


def md_worker(c, call):
    args = sys.argv[1:]
    if any(a in ("-h", "--help") for a in args):
        print("usage: md_worker [-h] --mode {build,run} [--pdb PDB] --work WORK [--steps STEPS] --out OUT")
        call.done(0, help=True)
    o = md_opts(args)
    m = c.get("md", {})
    mode = o.get("--mode")
    work = os.path.abspath(o.get("--work", "."))
    out = os.path.abspath(o["--out"]) if "--out" in o else None
    os.makedirs(work, exist_ok=True)
    k = bump("md:" + mode) if mode else 0
    atoms_list = m.get("atoms", [150000, 150000, 150000])
    n_atoms = atoms_list[(k - 1) % len(atoms_list)]
    if mode == "build":
        with open(os.path.join(work, "system.xml"), "w") as f:
            f.write("<System replay='%d'/>\n" % k + " " * 5000)
        with open(os.path.join(work, "solvated.pdb"), "w") as f:
            f.write("REMARK replay build %d\n" % k + " " * 7000 + "\nEND\n")
        res = {"mode": "build", "atoms": n_atoms, "n_atoms": n_atoms, "padding_nm": float(o.get("--padding-nm", 1.0)),
               "padding_angstrom": 10.0 * float(o.get("--padding-nm", 1.0)),
               "roles_present": ["capsid", "receptor"], "capsid_heavy_atoms": 5510, "system_xml": os.path.join(work, "system.xml"),
               "solvated_pdb": os.path.join(work, "solvated.pdb"), "pdb": o.get("--pdb"), "replay_call": k}
        if out:
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "w") as f:
                json.dump(res, f)
        print(json.dumps(res))
        call.done(0, mode="build", atoms=n_atoms, work=work, out=out)
    rates = m.get("rates", [128.96, 100.0, 160.0])
    rate = rates[(k - 1) % len(rates)]
    steps = int(o.get("--steps", 250000))
    eq = int(o.get("--equil-steps", 0))
    every = int(o.get("--report-interval", 5000))
    dt = float(o.get("--timestep-fs", 2.0))
    hdr = '#"Step","Time (ps)","Potential Energy (kJ/mole)","Kinetic Energy (kJ/mole)","Total Energy (kJ/mole)","Temperature (K)","Speed (ns/day)"'
    rows = [hdr]
    nan_at = m.get("nan_call") == k
    # the StateDataReporter covers minimisation, the short equilibration and the
    # 0.5 ns production segment, its step counter continuing (item 12: the last
    # step reaches the equilibration plus 250,000 production steps)
    eq_rep = int(m.get("reporter_equil_steps", 50000))
    last = int(m.get("reporter_last_step", eq + eq_rep + steps))
    for i, st in enumerate(range(every, last + 1, every)):
        pe = "nan" if (nan_at and i == 10) else "%.1f" % (-2051234.5 + i)
        rows.append("%d,%.1f,%s,371234.5,%.1f,300.12,%s" % (st, st * dt / 1000.0, pe, -1680000.0 + i, "--" if i == 0 else "%.2f" % rate))
    rep = os.path.join(work, "md_state.csv")
    with open(rep, "w") as f:
        f.write("\n".join(rows) + "\n")
    dcd = os.path.join(work, "trajectory.dcd")
    nframes = steps // every
    import struct
    natom = n_atoms
    with open(dcd, "wb") as f:
        # the layout OpenMM's DCDReporter writes: a CORD header of 20 words (frame count,
        # first step, interval, ..., time step as a float, unit-cell flag), a title block,
        # the atom count, then per frame a unit-cell block and three coordinate blocks
        f.write(struct.pack("<i4c9if10ii", 84, b"C", b"O", b"R", b"D", nframes, every, every, 0, 0, 0, 0, 0, 0,
                            dt / 1000.0 / 0.04888821, 1, 0, 0, 0, 0, 0, 0, 0, 0, 24, 84))
        title = b"REMARKS replay DCD".ljust(80)
        f.write(struct.pack("<ii", 164, 2) + title + title + struct.pack("<i", 164))
        f.write(struct.pack("<iii", 4, natom, 4))
        for fr in range(nframes):
            f.write(struct.pack("<i6di", 48, 4.0, 0.0, 4.0, 0.0, 0.0, 4.0, 48))
            for axis in range(3):
                # the coordinates of a 150,000-atom system are a sparse run of zeros
                f.write(struct.pack("<i", 4 * natom))
                f.seek(4 * natom, 1)
                f.write(struct.pack("<i", 4 * natom))
        f.truncate(f.tell())
    with open(os.path.join(work, "md_stdout.log"), "w") as f:
        f.write("production %d steps\n" % steps)
    wall = 0.2 + 0.05 * k
    time.sleep(wall)
    res = {"mode": "run", "atoms": n_atoms, "n_atoms": n_atoms, "steps": steps, "production_steps": steps, "equil_steps": eq,
           "timestep_fs": dt, "production_s": wall, "production_wall_clock_s": wall, "wall_clock_s": wall,
           "engine_ns_per_day": rate, "rate_ns_per_day": rate, "ns_per_day": rate,
           "frame_interval_ps": every * dt / 1000.0, "dcd": dcd, "dcd_path": dcd, "dcd_frames": nframes,
           "trajectory_file": dcd, "trajectory_path": dcd,
           "reporter": rep, "reporter_file": rep, "reporter_path": rep,
           "platform": "CUDA", "precision": "mixed", "seed": int(o.get("--seed", 0)), "replay_call": k}
    if out:
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w") as f:
            json.dump(res, f)
    print(json.dumps(res))
    call.done(0, mode="run", rate=rate, atoms=n_atoms, work=work, out=out)


TOOLS = {"nvidia-smi": nvidia_smi, "python": python_probe, "fetch": fetch, "sleep": sleep_,
         "lightdock3_setup.py": ld_setup, "lightdock3.py": ld_simulate, "lgd_generate_conformations.py": ld_generate,
         "lgd_rank.py": ld_rank, "colabfold_batch": colabfold, "md_worker": md_worker}


def main(tool):
    c = cfg()
    call = Call(tool)
    try:
        TOOLS[tool](c, call)
    except SystemExit:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        call.done(70, error="%s: %s" % (type(e).__name__, e))
'''

TOOL_ENV = {
    "M4_COLABFOLD": "colabfold_batch",
    "M4_LIGHTDOCK_SETUP": "lightdock3_setup.py",
    "M4_LIGHTDOCK": "lightdock3.py",
    "M4_LGD_GENERATE": "lgd_generate_conformations.py",
    "M4_LGD_RANK": "lgd_rank.py",
    "M4_MD_WORKER": "md_worker",
    "M4_NVIDIA_SMI": "nvidia-smi",
    "M4_FETCH": "fetch",
    "M4_SLEEP": "sleep",
    "M4_PYTHON": "python",
}


class Result(object):
    def __init__(self, stage, rc, out, err, outdir, calls, seconds):
        self.stage, self.rc, self.stdout, self.stderr = stage, rc, out, err
        self.outdir, self.calls, self.seconds = outdir, calls, seconds

    def path(self, name):
        return os.path.join(self.outdir, name)

    def has(self, name):
        return os.path.exists(self.path(name))

    def rec(self, name):
        p = self.path(name)
        need(os.path.exists(p), "%s: %s was not written" % (self.stage, name))
        try:
            return jload(p)
        except Exception as e:
            raise Fail("%s: %s is not JSON: %s" % (self.stage, name, e))

    def records(self):
        out = {}
        for fn in sorted(os.listdir(self.outdir)):
            if fn.endswith(".json"):
                try:
                    d = jload(self.path(fn))
                except Exception:
                    continue
                if isinstance(d, dict):
                    out[fn] = d
        return out

    def done(self):
        return self.rec("RUN_DONE")

    def tools(self, tool):
        return [c for c in self.calls if c["tool"] == tool]

    def why(self):
        msg = ""
        if self.has("RUN_DONE"):
            try:
                d = jload(self.path("RUN_DONE"))
                msg = "voided_by=%s failure_kind=%s" % (str(d.get("voided_by"))[:160], d.get("failure_kind"))
            except Exception:
                pass
        tail = (self.stderr or "").strip().splitlines()[-1:] or [""]
        return "%s; stderr: %s" % (msg, tail[0][:160])


class World(object):
    """one temporary box: payload layout, replay programs, a fake venv"""

    def __init__(self, label):
        self.root = tempfile.mkdtemp(prefix="m4t_%s_" % label)
        WORLDS.append(self.root)
        self.pay = os.path.join(self.root, "m4_run")
        self.bin = os.path.join(self.root, "replay")
        self.venv = os.path.join(self.root, "venv")
        for d in (os.path.join(self.pay, "frozen"), self.bin, os.path.join(self.venv, "bin"), os.path.join(self.root, "tmp")):
            os.makedirs(d)
        shutil.copyfile(os.path.join(RUN_DIR, "frozen", "provenance.py"), os.path.join(self.pay, "frozen", "provenance.py"))
        # the box's ~/m4_run/data after the downloads stage (6IHB and extracted parameters with colabfold's marker),
        # so a stage reading the payload's data/ and a stage reading --in both find them
        params = os.path.join(self.pay, "data", "params")
        os.makedirs(params)
        shutil.copyfile(fx("6IHB.pdb"), os.path.join(self.pay, "data", "6IHB.pdb"))
        for i in range(1, 6):
            with open(os.path.join(params, "params_model_%d_multimer_v3.npz" % i), "w") as f:
                f.write("replay parameters\n")
        with open(os.path.join(params, "download_complexes_multimer_v3_finished.txt"), "w") as f:
            f.write("")
        with open(os.path.join(self.bin, "replay_core.py"), "w") as f:
            f.write(REPLAY_CORE)
        for tool in sorted(set(TOOL_ENV.values())):
            p = os.path.join(self.bin, tool)
            with open(p, "w") as f:
                f.write("#!%s -I\nimport sys\nsys.path.insert(0, %r)\nimport replay_core\nreplay_core.main(%r)\n" % (PYTHON, self.bin, tool))
            os.chmod(p, 0o755)
        for name, tool in (("colabfold_batch", "colabfold_batch"), ("lightdock3_setup.py", "lightdock3_setup.py"),
                           ("lightdock3.py", "lightdock3.py"), ("lgd_generate_conformations.py", "lgd_generate_conformations.py"),
                           ("lgd_rank.py", "lgd_rank.py"), ("nvidia-smi", "nvidia-smi"), ("python", "python"),
                           ("python3", "python"), ("curl", "fetch")):
            os.symlink(os.path.join(self.bin, tool), os.path.join(self.venv, "bin", name))
        self.config = default_config()
        self.save()

    def save(self):
        with open(os.path.join(self.bin, "config.json"), "w") as f:
            json.dump(self.config, f, indent=1)

    def set(self, **kw):
        self.config.update(kw)
        self.save()

    def docking(self, runs):
        """per-docking-run replay settings, counted from the next lightdock3_setup.py call"""
        p = os.path.join(self.bin, "state.json")
        done = jload(p).get("docking_run", 0) if os.path.exists(p) else 0
        self.config["docking_runs"] = runs
        self.config["docking_offset"] = done
        self.save()

    def all_calls(self):
        p = os.path.join(self.bin, "calls.jsonl")
        return jlines(p) if os.path.exists(p) else []

    def env(self, elapsed=60.0, **extra):
        e = {
            "PATH": os.path.join(self.venv, "bin") + os.pathsep + "/usr/bin:/bin",
            "HOME": self.root,
            "TMPDIR": os.path.join(self.root, "tmp"),
            "LANG": "C.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PRICE_USD_PER_HOUR": "1.99",
            "BUDGET_LEFT_USD": "5",
            "REMOTE_TIMEOUT": "7200",
            "INSTANCE_TYPE": "gpu_1x_a100_sxm4",
            "ENV_LOCK_SHA256": LOCK,
            "ENV_DIR": os.path.dirname(self.venv),
            "HOLD_SECONDS": "0",
            "M4_T0_EPOCH": str(int(time.time() - elapsed)),
            "M4_PRE_T0_SECONDS": "58",
            "M4_VENV": self.venv,
            "M4_VENV_BIN": os.path.join(self.venv, "bin"),
        }
        for var, tool in TOOL_ENV.items():
            e[var] = os.path.join(self.bin, tool)
        for k, v in extra.items():
            if v is None:
                e.pop(k, None)
            else:
                e[k] = str(v)
        return e

    def run(self, stage, indir, outdir=None, elapsed=60.0, timeout=300, **extra):
        if outdir is None:
            outdir = tempfile.mkdtemp(prefix="out_%s_" % stage, dir=self.root)
        os.makedirs(outdir, exist_ok=True)
        before_calls = len(self.all_calls())
        snap_pay = tree_state(self.pay, skip=("frozen", "data"))
        snap_run = run_dir_state()
        snap_data = tree_state(os.path.join(self.pay, "data"))
        t0 = time.time()
        cmd = [PYTHON, RUNNER, "--stage", stage, "--in", indir, "--out", outdir]
        try:
            p = subprocess.run(cmd, cwd=self.pay, env=self.env(elapsed, **extra), stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, universal_newlines=True, timeout=timeout)
            rc, so, se = p.returncode, p.stdout, p.stderr
        except subprocess.TimeoutExpired as e:
            rc, so, se = 124, "", "test timeout after %s s" % timeout
        secs = time.time() - t0
        new_pay = sorted(set(tree_state(self.pay, skip=("frozen", "data")).items()) - set(snap_pay.items()))
        new_pay += [("data/" + k, v) for k, v in sorted(set(tree_state(os.path.join(self.pay, "data")).items()) - set(snap_data.items()))]
        new_run = sorted(set(run_dir_state().items()) - set(snap_run.items()))
        if new_pay or new_run:
            OUTSIDE_WRITES.append((stage, [k for k, _ in new_pay][:3], [k for k, _ in new_run][:3]))
        calls = self.all_calls()[before_calls:]
        return Result(stage, rc, so, se, outdir, calls, secs)


def tree_state(root, skip=()):
    st = {}
    for dp, dns, fns in os.walk(root):
        rel = os.path.relpath(dp, root)
        if rel.split(os.sep)[0] in skip:
            continue
        st[rel + "/"] = 0
        for fn in fns:
            p = os.path.join(dp, fn)
            try:
                s = os.lstat(p)
                st[os.path.relpath(p, root)] = (s.st_size, s.st_mtime_ns)
            except OSError:
                pass
    return st


def run_dir_state():
    st = {}
    for fn in os.listdir(RUN_DIR):
        p = os.path.join(RUN_DIR, fn)
        if os.path.isfile(p):
            s = os.stat(p)
            st[fn] = (s.st_size, s.st_mtime_ns)
    for sub in ("data", "work_m4", "results_m4", "frozen", "tmp", "cache"):
        d = os.path.join(RUN_DIR, sub)
        if os.path.isdir(d):
            for k, v in tree_state(d).items():
                st[sub + "/" + k] = v
    return st


def default_config():
    return {
        "nvidia_smi": {"header": fx("nvidia_smi_header.txt"), "query": fx("nvidia_smi_query.txt"), "rc": 0,
                       "error": fx("nvidia_smi_header_error.txt")},
        "python": {"pip_freeze": fx("env_pip_freeze.txt"), "imports": fx("probe_imports_stdout.txt"),
                   "versions": fx("probe_package_versions_stdout.txt")},
        "help": {"colabfold_batch": fx("help_colabfold_batch.txt"), "lightdock3.py": fx("help_lightdock3_py.txt"),
                 "lgd_generate_conformations.py": fx("help_lgd_generate_conformations_py.txt")},
        "fetch": {"pdb": fx("6IHB.pdb")},
        "sleep": {"factor": 1.0},
        "docking_stdout": {"setup": fx("lightdock_setup_stdout.txt"), "simulate": fx("lightdock_simulate_stdout.txt"),
                           "generate": fx("lightdock_generate_stdout.txt"), "rank": fx("lightdock_rank_stdout.txt")},
        "docking_default": {"rank_table": fx("rank_table_anchor_serial_tag-m4.list"), "top": [0, 15], "pose": "native"},
        "docking_runs": [],
        "colabfold": {"mode": "ok", "sleep_s": 0.12, "base_model_s": 30.0},
        "md": {"rates": [128.96, 100.0, 160.0]},
    }


# ------------------------------------------------------------ --in dirs

BOX_INPUTS = [
    "pairs_tag-m4.json", "pair_pair1_tag-m4.pdb", "pair_pair2_tag-m4.pdb", "pair_pair3_tag-m4.pdb",
    "pair_pair1_tag-m4.fasta", "pair_pair2_tag-m4.fasta", "pair_pair3_tag-m4.fasta",
    "downloads_tag-m4.json", "download_log_tag-m4.json", "params_markers_tag-m4.json", "env_check_tag-m4.json",
    "control-sleep_tag-m4.json", "control-empty-run_tag-m4.json", "control-unit-and-scale_tag-m4.json",
    "rows_controls_tag-m4.jsonl",
]


def make_in(world, label, layers=(), extra_files=None, drop=(), early=True):
    """an --in directory: the box's records of the early stages, the runner's own capability and controls
    outputs (early=True), then the outputs of the earlier stages given as layers"""
    d = tempfile.mkdtemp(prefix="in_%s_" % label, dir=world.root)
    if early:
        layers = [pipe("capability"), pipe("controls")] + list(layers)
    for name in BOX_INPUTS:
        if name not in drop:
            shutil.copyfile(fx(name), os.path.join(d, name))
    if "6IHB" not in drop:
        shutil.copyfile(fx("6IHB.pdb"), os.path.join(d, "6IHB_tag-m4.pdb"))
        os.makedirs(os.path.join(d, "data", "params"))
        shutil.copyfile(fx("6IHB.pdb"), os.path.join(d, "data", "6IHB.pdb"))
        for i in range(1, 6):
            with open(os.path.join(d, "data", "params", "params_model_%d_multimer_v3.npz" % i), "w") as f:
                f.write("replay parameters\n")
        with open(os.path.join(d, "data", "params", "download_complexes_multimer_v3_finished.txt"), "w") as f:
            f.write("")
    for layer in layers:
        overlay(layer.outdir if isinstance(layer, Result) else layer, d)
    for name, src in (extra_files or {}).items():
        dst = os.path.join(d, name)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if isinstance(src, bytes):
            with open(dst, "wb") as f:
                f.write(src)
        else:
            shutil.copyfile(src, dst)
    return d


def overlay(src, dst):
    """copy a stage's --out into an --in; the compute table accumulates as in a full run"""
    for dp, dns, fns in os.walk(src):
        rel = os.path.relpath(dp, src)
        for fn in fns:
            if rel == "." and fn == "RUN_DONE":
                continue
            target = os.path.join(dst, rel, fn)
            if rel == "." and fn == "compute_table_tag-m4.json" and os.path.exists(target):
                try:
                    old, new = jload(target), jload(os.path.join(dp, fn))
                    by = dict((e.get("stage"), e) for e in old.get("stages", []))
                    for e in new.get("stages", []):
                        if e.get("ran") or e.get("stage") not in by:
                            by[e.get("stage")] = e
                    new["stages"] = [by[k] for k in [e.get("stage") for e in new.get("stages", [])] if k in by]
                    with open(target, "w") as f:
                        json.dump(new, f, indent=1)
                    continue
                except (ValueError, AttributeError, TypeError):
                    pass
            os.makedirs(os.path.dirname(target), exist_ok=True)
            shutil.copyfile(os.path.join(dp, fn), target)


def empty_in(world, label):
    return tempfile.mkdtemp(prefix="in_%s_" % label, dir=world.root)


# ---------------------------------------------------------- record checks

def failed_explicitly(res, label):
    need(res.rc == 2, "%s: exit %s, expected 2 (%s)" % (label, res.rc, res.why()))
    need(res.has("RUN_DONE"), "%s: no RUN_DONE after the failure" % label)
    d = res.done()
    need(d.get("exit_code") == 2, "%s: RUN_DONE exit_code %r, expected 2" % (label, d.get("exit_code")))
    need(d.get("run_valid") is False, "%s: RUN_DONE run_valid %r after a failure" % (label, d.get("run_valid")))
    need(d.get("failure_kind") or d.get("voided_by"), "%s: RUN_DONE names no failure" % label)
    return d


def ran_clean(res, label):
    """the stage finished its own work: exit 0, or exit 3 that records no stop of its own
    (the inputs another stage measures shown as not reached; the exit code itself is
    checked by test stage_exit_code_on_success)"""
    if res.rc == 0:
        return
    need(res.rc == 3 and res.has("RUN_DONE"), "%s: exit %s (%s)" % (label, res.rc, res.why()))
    d = res.done()
    st = [str(v.get("status")) for v in d.get("inputs", {}).values() if isinstance(v, dict)]
    need(not d.get("stopped_by") and all(not x.startswith("unmeasured_by_stop:") or x.endswith(":stage_not_reached") for x in st),
         "%s: exit 3 with a stop recorded (%s; %s)" % (label, d.get("stopped_by"), st))


def stage_records(res):
    """records the stage wrote that carry values (provenance records)"""
    return {k: v for k, v in res.records().items() if isinstance(v.get("values"), dict)}


def anchor_values(res):
    return res.rec("endpoint-anchor_tag-m4.json").get("values", {})


def calib(rec):
    """calibration_valid of a record: at its top level or in its values"""
    if "calibration_valid" in rec:
        return rec["calibration_valid"]
    return rec.get("values", {}).get("calibration_valid", "absent")


def num_close(v, target, tol):
    return is_num(v) and abs(v - target) <= tol


def endpoint(res, i):
    return res.rec("endpoint-C%d_tag-m4.json" % i)


# ----------------------------------------------------------- the pipeline

_rng = random.Random(20261022)
RIGID_SHIFT = [round(_rng.uniform(-28.0, 28.0), 3) for _ in range(3)]


class Pipe(object):
    """one chain of stages on the replays, built once and shared by the tests"""
    world = None
    res = {}
    errors = {}


def pipe(stage):
    if stage in Pipe.errors:
        raise Fail("pipeline stage %s could not be produced: %s" % (stage, Pipe.errors[stage]))
    if stage in Pipe.res:
        return Pipe.res[stage]
    if Pipe.world is None:
        Pipe.world = World("pipe")
    w = Pipe.world
    try:
        if stage == "downloads":
            wd = World("downloads")
            shutil.rmtree(os.path.join(wd.pay, "data"))
            r = wd.run("downloads", make_in(wd, "dl", early=False, drop=("6IHB", "downloads_tag-m4.json", "download_log_tag-m4.json", "params_markers_tag-m4.json")))
            Pipe.res[stage] = r
            return r
        if stage == "capability":
            r = w.run("capability", empty_in(w, "cap"))
        elif stage == "controls":
            r = w.run("controls", make_in(w, "ctl", early=False, drop=("control-sleep_tag-m4.json", "control-empty-run_tag-m4.json",
                                                                       "control-unit-and-scale_tag-m4.json", "rows_controls_tag-m4.jsonl")))
        elif stage == "anchor_pass":
            w.docking([{"pose": "native", "whole_shift": RIGID_SHIFT}, {"pose": "native", "whole_shift": RIGID_SHIFT}])
            r = w.run("anchor", make_in(w, "anc_pass"))
        elif stage == "anchor_fail":
            w.docking([{"pose": "file", "pose_file": fx("pose_anchor_serial_tag-m4.pdb")},
                                {"pose": "file", "pose_file": fx("pose_anchor_serial_tag-m4.pdb")}])
            r = w.run("anchor", make_in(w, "anc_fail"))
        elif stage in ("aux_pass", "aux_fail"):
            anc = pipe("anchor_" + stage.split("_")[1])
            w.docking([])
            r = w.run("aux", make_in(w, stage, [anc]))
        elif stage in ("af2_pass", "af2_fail"):
            anc = pipe("anchor_" + stage.split("_")[1])
            r = w.run("af2", make_in(w, stage, [anc]))
        elif stage in ("md_pass", "md_fail"):
            kind = stage.split("_")[1]
            r = w.run("md", make_in(w, stage, [pipe("anchor_" + kind), pipe("aux_" + kind)]))
        elif stage in ("storage_pass", "storage_fail"):
            kind = stage.split("_")[1]
            r = w.run("storage", make_in(w, stage, [pipe("anchor_" + kind), pipe("aux_" + kind), pipe("af2_" + kind), pipe("md_" + kind)]))
        elif stage in ("endpoints_pass", "endpoints_fail"):
            kind = stage.split("_")[1]
            r = w.run("endpoints", make_in(w, stage, [pipe("anchor_" + kind), pipe("aux_" + kind), pipe("af2_" + kind),
                                                       pipe("md_" + kind), pipe("storage_" + kind)]))
        else:
            raise Fail("unknown pipeline stage %s" % stage)
    except Fail as e:
        Pipe.errors[stage] = str(e)
        raise
    Pipe.res[stage] = r
    return r


# ================================================================= tests
# item 1: every parser on the real output, and on malformed copies

def test_parse_nvidia_smi_header():
    got = parse_ok("parse_nvidia_smi_header", fx("nvidia_smi_header.txt"))
    t = text_of(got)
    need("570.148.08" in t, "driver 570.148.08 of the recording not in %s" % t[:200])
    need(re.search(r'"12\.8"|: 12\.8\b', t), "CUDA Version 12.8 of the recording not in %s" % t[:200])
    for bad in ("nvidia_smi_header_truncated.txt", "nvidia_smi_header_field_missing.txt", "nvidia_smi_header_error.txt"):
        parse_bad("parse_nvidia_smi_header", fx(bad))


def test_parse_nvidia_smi_query():
    got = parse_ok("parse_nvidia_smi_query", fx("nvidia_smi_query.txt"))
    t = text_of(got)
    need("NVIDIA A100-SXM4-40GB" in t and "570.148.08" in t, "GPU name or driver of the recording missing: %s" % t[:200])
    for bad in ("nvidia_smi_query_field_missing.txt", "nvidia_smi_query_error.txt", "nvidia_smi_query_truncated.txt"):
        parse_bad("parse_nvidia_smi_query", fx(bad))


def test_parse_etimes():
    got = parse_ok("parse_etimes", fx("etimes_ps.txt"))
    need(28 in [v for _, v in walk(got) if is_num(v)], "etimes 28 not parsed: %s" % text_of(got))
    for bad in ("etimes_error.txt", "etimes_truncated.txt"):
        parse_bad("parse_etimes", fx(bad))


def test_parse_rank_table_recorded():
    got = parse_ok("parse_rank_table", fx("rank_table_anchor_serial_tag-m4.list"))
    rows = got.get("rows")
    need(isinstance(rows, list) and len(rows) == 40, "40 data rows recorded, parsed %s" % (len(rows) if isinstance(rows, list) else rows))
    top = got.get("top", got.get("top_row"))
    need(isinstance(top, dict), "no top row in %s" % sorted(got))
    tt = text_of(top)
    need("lightdock_15.pdb" in tt and "-23.455" in tt, "top row should be swarm 0 glowworm 15 lightdock_15.pdb score -23.455, got %s" % tt[:200])
    need(str(top.get("Swarm")) == "0" and str(top.get("Glowworm")) == "15", "top row swarm/glowworm not 0/15: %s" % tt[:200])
    need(got.get("mapping") == "by_name", "mapping %r, the box recorded by_name" % got.get("mapping"))
    need("Scoring" in text_of(got.get("columns")), "columns do not carry the header: %s" % text_of(got.get("columns"))[:200])


def test_parse_rank_table_malformed():
    first = fx_text("rank_table_anchor_serial_tag-m4.list").splitlines()[0]
    for bad in ("rank_table_truncated_tag-m4.list", "rank_table_field_missing_tag-m4.list", "rank_table_error_tag-m4.list"):
        msg = parse_bad("parse_rank_table", fx(bad))
        raw = fx_text(bad).splitlines()[0]
        need(repr(raw) in msg or raw.strip() in msg, "%s: parse error does not carry the first raw lines: %s" % (bad, msg[:200]))
    msg = parse_bad("parse_rank_table", fx("rank_table_header_only_tag-m4.list"))
    need(re.search(r"\b0\b", msg), "header-only table: error does not state the 0 lines after the header: %s" % msg[:200])
    msg = parse_bad("parse_rank_table", fx("rank_table_mixed_counts_tag-m4.list"))
    need("6" in msg and "7" in msg, "mixed 6/7 fields: error does not name both counts: %s" % msg[:200])
    parse_bad("parse_rank_table", fx("rank_table_nonmonotone_tag-m4.list"))
    got = parse_ok("parse_rank_table", fx("rank_table_positional_tag-m4.list"))
    need(len(got.get("rows", [])) == 2 and got.get("mapping") == "positional",
         "planted 9-token header over 7-field rows: expected 2 rows, positional; got %s rows, %r" % (len(got.get("rows", [])), got.get("mapping")))
    need("-3.5" in text_of(got.get("top", got.get("top_row"))), "positional table: top row is not the first row written")
    del first


def pdb_counts(got):
    atoms = got.get("atoms")
    if isinstance(atoms, list) and atoms and isinstance(atoms[0], dict):
        counts = {}
        for a in atoms:
            counts[a.get("chain")] = counts.get(a.get("chain"), 0) + 1
        return counts, atoms
    raise Fail("parse_pdb returned no atom list (keys %s)" % sorted(got)[:8])


def test_parse_pdb():
    got = parse_ok("parse_pdb", fx("pose_anchor_serial_tag-m4.pdb"))
    counts, atoms = pdb_counts(got)
    need(counts == {"A": 4142, "R": 725}, "recorded pose has A 4142 and R 725 atoms, parsed %s" % counts)
    a0 = atoms[0]
    need(a0.get("chain") == "A" and int(a0.get("resseq")) == 219 and a0.get("name") == "N" and a0.get("icode", "") in ("", " ")
         and abs(float(a0["x"]) + 16.842) < 1e-6 and abs(float(a0["y"]) - 25.012) < 1e-6 and abs(float(a0["z"]) + 26.624) < 1e-6,
         "first atom of the recorded pose is A 219 N (-16.842, 25.012, -26.624), parsed %s" % text_of(a0)[:200])
    got = parse_ok("parse_pdb", fx("pair_pair1_tag-m4.pdb"))
    counts, _ = pdb_counts(got)
    need(counts == {"A": 4143, "B": 1368, "R": 725}, "pair1 has A 4143, B 1368, R 725 atoms, parsed %s" % counts)
    parse_bad("parse_pdb", fx("pose_truncated_tag-m4.pdb"))


def test_parse_colabfold_log():
    # The real log parses to the times it records.  A structurally broken copy
    # (truncated mid-line, a time field missing) is malformed input and must
    # raise ValueError.  The error-line copy is a well-formed log of a run that
    # died after model 1 started: it holds no completed per-model time, and
    # item 12 says per-model times are "parsed (or null with a reason, not a
    # failure)", so the parser may report none or raise, but it may never
    # invent a number (item 5: never a default).
    got = parse_ok("parse_colabfold_log", fx("colabfold_log.txt"))
    want = [96.4, 61.2, 60.8, 61.0, 60.9]
    lists = [v for _, v in walk(got) if isinstance(v, list) and len(v) == 5 and all(is_num(x) for x in v)]
    lists += [[v[k] for k in sorted(v)] for _, v in walk(got) if isinstance(v, dict) and len(v) == 5 and all(is_num(x) for x in v.values())]
    need(any(all(abs(a - b) < 1e-6 for a, b in zip(l, want)) for l in lists), "per-model times %s not parsed: %s" % (want, text_of(got)[:240]))
    for bad in ("colabfold_log_field_missing.txt", "colabfold_log_truncated.txt"):
        parse_bad("parse_colabfold_log", fx(bad))
    try:
        g = parser("parse_colabfold_log")(fx("colabfold_log_error.txt"))
    except ValueError:
        return
    except Exception as e:
        raise Fail("parse_colabfold_log on the error-line log raised %s: %s" % (type(e).__name__, str(e)[:120]))
    need(isinstance(g, dict), "parse_colabfold_log returned %s on the error-line log" % type(g).__name__)
    inv = [l for _, l in walk(g) if isinstance(l, (list, tuple)) and all(is_num(x) for x in l)]
    inv += [[v[k] for k in sorted(v)] for _, v in walk(g) if isinstance(v, dict) and v and all(is_num(x) for x in v.values())]
    need(not inv, "parse_colabfold_log invented per-model times %s on a log with no completed model time (item 12: 'or null with a reason, not a failure')" % (inv[:2],))


def test_parse_reporter_file():
    got = parse_ok("parse_reporter_file", fx("reporter_file.txt"))
    t = text_of(got)
    need(250000 in [v for _, v in walk(got) if is_num(v)], "last step 250000 not parsed: %s" % t[:240])
    need(any(v is True for _, v in find_keys(got, "finite")) or not any(v is False for _, v in find_keys(got, "finite")),
         "energies of the planted file are finite, parsed %s" % t[:240])
    for bad in ("reporter_file_field_missing.txt", "reporter_file_truncated.txt", "reporter_file_error.txt"):
        parse_bad("parse_reporter_file", fx(bad))


def test_parse_engine_rate_line():
    # The directive names parse_engine_rate_line as a parser of a path that yields the
    # engine's ns/day rate, ValueError on malformed input, and item 15 states the rule
    # for a file without a rate line (an explicit null, never a value).  The recorded
    # StateDataReporter file states its rate as 128.96 ns/day; the parser may read that
    # rate or report an explicit null with a reason, but it may never invent a number.
    got = parse_ok("parse_engine_rate_line", fx("reporter_file.txt"))
    named = [(p, v) for p, v in walk(got) if re.search(r"rate|ns_per_day|speed", p, re.I)]
    nums = [v for _, v in named if is_num(v)]
    need(all(abs(v - 128.96) < 1e-6 for v in nums),
         "parse_engine_rate_line on the recorded reporter file returned rate value(s) %s: the file states 128.96 ns/day, a parser may never invent a value" % nums)
    need(nums or any(v is None for _, v in named),
         "parse_engine_rate_line on the recorded reporter file returned neither the stated rate 128.96 nor an explicit null: %s" % text_of(got)[:200])
    for bad in ("reporter_file_field_missing.txt", "reporter_file_error.txt", "reporter_file_truncated.txt"):
        try:
            g = parser("parse_engine_rate_line")(fx(bad))
        except ValueError:
            continue
        except Exception as e:
            raise Fail("parse_engine_rate_line on %s raised %s, not ValueError" % (bad, type(e).__name__))
        rates = [v for p, v in walk(g) if is_num(v) and re.search("rate|ns_per_day|speed", p, re.I)]
        need(not rates, "%s: a malformed rate line gave the number(s) %s instead of an error or an explicit null" % (bad, rates))


def test_parse_af2_timing_rows():
    r = pipe("af2_pass")
    p = r.path("rows_af2_tag-m4.jsonl")
    need(os.path.exists(p), "af2 stage wrote no rows_af2_tag-m4.jsonl (%s)" % r.why())
    got = parse_ok("parse_af2_timing_rows", p)
    cf = [c for c in r.tools("colabfold_batch") if not c.get("help")]
    need(len(cf) == 9, "the af2 stage made %d prediction calls, expected 9" % len(cf))
    need(got.get("n") == 9 or 9 in nums_at(got, r"^n(_runs)?$"), "parsed n is not 9: %s" % text_of(got)[:200])
    secs = [c["t1"] - c["t0"] for c in cf]
    mean_h = sum(secs) / len(secs) / 3600.0
    need(any_num_close(got, "mean", mean_h, 0.6 / 3600.0), "parsed mean hours %s differ from the calls' mean %.6f h" % (nums_at(got, "mean"), mean_h))
    with open(p) as f:
        text = f.read()
    tp = os.path.join(r.outdir, "..", "rows_af2_truncated.jsonl")
    with open(tp, "w") as f:
        f.write(text[: len(text) - 40])
    parse_bad("parse_af2_timing_rows", tp)


# item 1, the stage side: a malformed output makes the stage fail explicitly

def test_stage_fails_on_malformed_rank_table():
    for bad in ("rank_table_truncated_tag-m4.list", "rank_table_field_missing_tag-m4.list", "rank_table_error_tag-m4.list"):
        w = World("badrank")
        w.docking([{"rank_table": fx(bad)}, {"rank_table": fx(bad)}])
        r = w.run("anchor", make_in(w, "badrank"))
        failed_explicitly(r, "anchor with %s" % bad)
        need(r.has("rank_table_diagnostic_anchor_serial_tag-m4.txt"), "%s: no rank_table_diagnostic_anchor_serial_tag-m4.txt" % bad)
        need(r.has("rank_table_anchor_serial_tag-m4.list") and open(r.path("rank_table_anchor_serial_tag-m4.list")).read() == fx_text(bad),
             "%s: the raw table was not kept as written" % bad)
        if r.has("endpoint-anchor_tag-m4.json"):
            a = r.rec("endpoint-anchor_tag-m4.json")
            need(a.get("decision") not in ("PASS", "FAIL"), "%s: anchor decided %s on an unparsable table" % (bad, a.get("decision")))
            need(not is_num(a.get("values", {}).get("measured")), "%s: anchor measured a default %r" % (bad, a.get("values", {}).get("measured")))


def test_stage_fails_on_truncated_pose():
    w = World("badpose")
    w.docking([{"truncate_pose": 2030}, {"truncate_pose": 2030}])
    r = w.run("anchor", make_in(w, "badpose"))
    failed_explicitly(r, "anchor with a truncated pose")
    a = r.rec("endpoint-anchor_tag-m4.json")
    need(a.get("decision") not in ("PASS", "FAIL"), "anchor decided %s on a truncated pose" % a.get("decision"))


def test_stage_fails_on_malformed_nvidia_smi():
    for header, query in (("nvidia_smi_header_truncated.txt", "nvidia_smi_query.txt"),
                          ("nvidia_smi_header_field_missing.txt", "nvidia_smi_query.txt"),
                          ("nvidia_smi_header.txt", "nvidia_smi_query_field_missing.txt")):
        w = World("badsmi")
        w.config["nvidia_smi"].update(header=fx(header), query=fx(query))
        w.save()
        r = w.run("capability", empty_in(w, "badsmi"))
        failed_explicitly(r, "capability with %s / %s" % (header, query))
        for fn, rec in stage_records(r).items():
            m = rec["values"].get("machine", {})
            if header != "nvidia_smi_header.txt":
                need(m.get("cuda_runtime_version") in (None, ""), "%s: %s carries a CUDA version %r from a malformed header" % (header, fn, m.get("cuda_runtime_version")))
    w = World("smierr")
    w.config["nvidia_smi"].update(rc=9)
    w.save()
    failed_explicitly(w.run("capability", empty_in(w, "smierr")), "capability with nvidia-smi failing")


def test_stage_fails_on_colabfold_error():
    w = World("cferr")
    w.config["colabfold"]["mode"] = "error"
    w.save()
    r = w.run("af2", make_in(w, "cferr", [pipe("anchor_pass")]))
    failed_explicitly(r, "af2 with a failing prediction call")
    c1 = r.rec("endpoint-C1_tag-m4.json") if r.has("endpoint-C1_tag-m4.json") else None
    if c1:
        need(c1.get("decision") not in ("PASS", "FAIL"), "C1 decided %s after a failed prediction call" % c1.get("decision"))


def test_stage_never_defaults_colabfold_field():
    w = World("cfmiss")
    w.config["colabfold"]["mode"] = "field_missing"
    w.save()
    r = w.run("af2", make_in(w, "cfmiss", [pipe("anchor_pass")]))
    if r.rc == 2:
        failed_explicitly(r, "af2 with a log missing a model time")
        return
    need(r.has("rows_af2_tag-m4.jsonl"), "af2 wrote no rows (%s)" % r.why())
    for row in jlines(r.path("rows_af2_tag-m4.jsonl")):
        per = [v for p, v in find_keys(row, "per_model|model_s|model_times") if isinstance(v, (list, dict))]
        for v in per:
            vals = v if isinstance(v, list) else [v[k] for k in sorted(v)]
            need(not (len(vals) == 5 and all(is_num(x) for x in vals)), "a model time missing from the log became the number %r in %s" % (vals, text_of(row)[:200]))
        need(per == [] or row.get("null_reasons") or find_keys(row, "null_reason|reason"), "per-model times without a null reason: %s" % text_of(row)[:200])


def test_stage_fails_on_malformed_af2_rows():
    r0 = pipe("af2_pass")
    p = r0.path("rows_af2_tag-m4.jsonl")
    need(os.path.exists(p), "no rows_af2_tag-m4.jsonl to corrupt (%s)" % r0.why())
    with open(p, "rb") as f:
        text = f.read()
    w = Pipe.world
    r = w.run("endpoints", make_in(w, "badrows", [pipe("anchor_pass"), pipe("aux_pass"), r0, pipe("md_pass"), pipe("storage_pass")],
                                    extra_files={"rows_af2_tag-m4.jsonl": text[: len(text) - 40]}))
    d = failed_explicitly(r, "endpoints with truncated AlphaFold rows")
    # item 7: every input not decided before the failure is void_by_failure:<kind> in RUN_DONE; a C1
    # record, when the stage wrote one, is never a band decision
    st = str(d.get("inputs", {}).get("C1", {}).get("status"))
    need(st.startswith("void_by_failure:"), "RUN_DONE C1 status %r after truncated AlphaFold rows, expected void_by_failure:<kind>" % st)
    if r.has("endpoint-C1_tag-m4.json"):
        need(r.rec("endpoint-C1_tag-m4.json").get("decision") not in ("PASS", "FAIL"), "C1 decided on truncated rows")


def test_stage_reports_missing_inputs():
    w = World("missing")
    shutil.rmtree(os.path.join(w.pay, "data"))
    bad = []
    for stage in ("anchor", "aux", "af2", "md", "storage", "endpoints"):
        r = w.run(stage, empty_in(w, "missing_" + stage))
        d = r.done() if r.has("RUN_DONE") else {}
        why = "%s %s" % (d.get("voided_by"), r.stderr[-400:])
        if r.rc != 2 or not re.search(r"[\w.-]+_tag-m4\.(json|jsonl|pdb|fasta)|6IHB", why):
            bad.append("%s exit %s (%s)" % (stage, r.rc, str(d.get("voided_by"))[:60]))
    need(not bad, "a stage with an empty --in must exit 2 naming the missing file: " + "; ".join(bad))


# item 2: stages that call a program more than once keep every call apart

def check_docking_runs_separate(calls, label):
    setups = [c for c in calls if c["tool"] == "lightdock3_setup.py" and not c.get("help")]
    cwds = [c["cwd"] for c in setups]
    need(len(set(cwds)) == len(cwds), "%s: docking setups share a working directory: %s" % (label, cwds))
    for c in calls:
        need(c.get("rc") == 0, "%s: %s call %d failed in the replay (%s): it read another call's output or none" % (label, c["tool"], c["tool_seq"], c.get("error")))
    by_run = {}
    for c in calls:
        if c["tool"] in ("lightdock3.py", "lgd_rank.py", "lightdock3_setup.py") and not c.get("help"):
            by_run.setdefault(c["docking_run"], set()).add(c["cwd"])
    for run, ws in by_run.items():
        need(len(ws) == 1, "%s: docking run %d ran in several directories %s" % (label, run, sorted(ws)))


def anchor_rows(res):
    need(res.has("rows_anchor_tag-m4.jsonl"), "no rows_anchor_tag-m4.jsonl (%s)" % res.why())
    rows = jlines(res.path("rows_anchor_tag-m4.jsonl"))
    out = {}
    for row in rows:
        t = text_of(row)
        which = "parallel" if "parallel" in t else ("serial" if "serial" in t else None)
        out[which] = row
    return out


def test_anchor_calls_kept_apart():
    w = World("anc2")
    second = fx("rank_table_anchor_serial_tag-m4.list")
    lines = fx_text("rank_table_anchor_serial_tag-m4.list").splitlines(True)
    alt = os.path.join(w.root, "rank_minus_first_row.list")
    with open(alt, "w") as f:
        f.write(lines[0] + "".join(lines[2:]))
    w.docking([{"pose": "native", "rank_table": second, "top": [0, 15]},
                        {"pose": "native", "rank_table": alt, "top": [0, 11], "ligand_shift": [1.5, 0.0, 0.0]},
                        {"pose": "native", "rank_table": alt, "top": [0, 11]},
                        {"pose": "native", "rank_table": second, "top": [0, 15], "ligand_shift": [0.0, 1.2, 0.0]}])
    r1 = w.run("anchor", make_in(w, "anc2a"))
    snap1 = tree_state(r1.outdir)
    ran_clean(r1, "first anchor run")
    check_docking_runs_separate(r1.calls, "anchor run 1")
    need(len([c for c in r1.calls if c["tool"] == "lightdock3_setup.py"]) == 2, "anchor run 1 did not dock twice (serial, parallel)")
    need(open(r1.path("rank_table_anchor_serial_tag-m4.list")).read() == open(second).read(), "serial rank table kept is not the serial call's table")
    need(open(r1.path("rank_table_anchor_parallel_tag-m4.list")).read() == open(alt).read(), "parallel rank table kept is not the parallel call's table")
    rows = anchor_rows(r1)
    need("-23.455" in text_of(rows.get("serial")) and "lightdock_15.pdb" in text_of(rows.get("serial")), "serial row does not carry its own top row (glowworm 15)")
    need("-23.517" in text_of(rows.get("parallel")) and "lightdock_11.pdb" in text_of(rows.get("parallel")), "parallel row does not carry its own top row (glowworm 11)")
    v = anchor_values(r1)
    sp = nums_at(v, "serial.*parallel.*rmsd|serial_parallel")
    need(any(abs(x - 1.5) < 1e-3 for x in sp), "serial-versus-parallel RMSD %s, the parallel pose was planted 1.5 A away" % sp)
    r2 = w.run("anchor", make_in(w, "anc2b"))
    ran_clean(r2, "second anchor run")
    need(tree_state(r1.outdir) == snap1, "the second anchor run changed the first run's --out")
    need(open(r2.path("rank_table_anchor_serial_tag-m4.list")).read() == open(alt).read(), "second run kept the first run's serial table")
    sp2 = nums_at(anchor_values(r2), "serial.*parallel.*rmsd|serial_parallel")
    need(any(abs(x - 1.2) < 1e-3 for x in sp2), "second run serial-versus-parallel RMSD %s, planted 1.2 A" % sp2)
    check_docking_runs_separate(w.all_calls(), "two anchor runs (separate --out)")


def test_aux_calls_kept_apart():
    w = World("aux2")
    tables = []
    lines = fx_text("rank_table_anchor_serial_tag-m4.list").splitlines(True)
    for k in range(6):
        p = os.path.join(w.root, "rank_%d.list" % k)
        with open(p, "w") as f:
            f.write(lines[0] + "".join(lines[1 + k:]))
        tables.append(p)
    tops = []
    for k in range(6):
        row = lines[1 + k].split()
        tops.append([int(row[0]), int(row[1])])
    w.docking([{"rank_table": tables[k], "top": tops[k], "ligand_shift": [0.3 * k, 0.0, 0.0]} for k in range(6)])
    anc = make_in(w, "aux2", [pipe("anchor_pass")])
    r1 = w.run("aux", anc)
    ran_clean(r1, "aux run 1")
    snap1 = tree_state(r1.outdir)
    check_docking_runs_separate(r1.calls, "aux run 1")
    need(len([c for c in r1.calls if c["tool"] == "lightdock3_setup.py"]) == 3, "aux did not dock the 3 pairs")
    kept = sorted(fn for fn in os.listdir(r1.outdir) if fn.startswith("rank_table_") and fn.endswith("_tag-m4.list"))
    need(len(kept) == 3, "aux kept %d rank tables, expected one per pair: %s" % (len(kept), kept))
    contents = sorted(open(os.path.join(r1.outdir, fn)).read() for fn in kept)
    need(contents == sorted(open(t).read() for t in tables[:3]), "the kept rank tables are not the three calls' own tables")
    r2 = w.run("aux", anc)
    ran_clean(r2, "aux run 2")
    need(tree_state(r1.outdir) == snap1, "the second aux run changed the first run's --out")
    contents2 = sorted(open(os.path.join(r2.outdir, fn)).read() for fn in os.listdir(r2.outdir) if fn.startswith("rank_table_") and fn.endswith("_tag-m4.list"))
    need(contents2 == sorted(open(t).read() for t in tables[3:6]), "the second aux run kept tables of the first run")
    check_docking_runs_separate(w.all_calls(), "two aux runs (separate --out)")


def af2_rows_match_calls(res, label):
    need(res.has("rows_af2_tag-m4.jsonl"), "%s: no rows_af2_tag-m4.jsonl (%s)" % (label, res.why()))
    rows = jlines(res.path("rows_af2_tag-m4.jsonl"))
    calls = [c for c in res.tools("colabfold_batch") if not c.get("help")]
    need(len(calls) == 9, "%s: %d prediction calls, expected 9 (3 pairs x 3 seeds)" % (label, len(calls)))
    need(len(set(c["results"] for c in calls)) == 9, "%s: prediction calls share a results directory" % label)
    need(len(rows) == 9, "%s: %d AlphaFold rows, expected 9" % (label, len(rows)))
    for row in rows:
        pair = row.get("pair")
        seed = row.get("seed")
        mine = [c for c in calls if c["pair"] == pair and c["seed"] == seed]
        need(len(mine) == 1, "%s: row pair %r seed %r matches %d calls" % (label, pair, seed, len(mine)))
        c = mine[0]
        lists = [v for _, v in walk(row) if isinstance(v, list) and len(v) == 5 and all(is_num(x) for x in v)]
        need(any(all(abs(a - b) < 1e-6 for a, b in zip(l, c["times"])) for l in lists),
             "%s: row %s/%s does not carry its own call's model times %s" % (label, pair, seed, c["times"]))
        wall = c["t1"] - c["t0"]
        others = [x["t1"] - x["t0"] for x in calls if x is not c]
        cand = [v for p, v in walk(row) if is_num(v) and re.search(r"wall|second|_s$", p.split(".")[-1], re.I) and abs(v - wall) < 0.3]
        need(cand, "%s: row %s/%s has no wall-clock near its call's %.2f s" % (label, pair, seed, wall))
        del others
    return rows


def test_af2_calls_kept_apart():
    w = World("af2x")
    anc = make_in(w, "af2x", [pipe("anchor_pass")])
    r1 = w.run("af2", anc)
    ran_clean(r1, "af2 run 1")
    af2_rows_match_calls(r1, "af2 run 1")
    snap1 = tree_state(r1.outdir)
    w.config["colabfold"]["base_model_s"] = 300.0
    w.save()
    r2 = w.run("af2", anc)
    ran_clean(r2, "af2 run 2")
    af2_rows_match_calls(r2, "af2 run 2")
    need(tree_state(r1.outdir) == snap1, "the second af2 run changed the first run's --out")


def test_md_calls_kept_apart():
    r = pipe("md_pass")
    calls = [c for c in r.tools("md_worker") if c.get("mode") == "run"]
    builds = [c for c in r.tools("md_worker") if c.get("mode") == "build"]
    need(len(calls) >= 2, "md made %d production worker calls, expected one per complex (%s)" % (len(calls), r.why()))
    need(len(set(c["work"] for c in calls)) == len(calls), "md worker calls share a work directory: %s" % [c["work"] for c in calls])
    need(len(set(c["work"] for c in builds)) == len(builds), "md build calls share a work directory")
    ran_clean(r, "md")
    rows = [row for row in jlines(r.path("rows_md_tag-m4.jsonl")) if not row.get("skipped")]
    for c in calls:
        need(any(any_num_close(row, "engine", c["rate"], 1e-6) for row in rows), "no MD row carries call %d's own engine rate %s" % (c["tool_seq"], c["rate"]))
    rates = sorted(set(nums_at(rows, "engine")))
    need(len(rates) == len(calls), "MD rows repeat an engine rate: %s" % rates)
    w = World("md2")
    md_in = make_in(w, "md2", [pipe("anchor_pass"), pipe("aux_pass")])
    m1 = w.run("md", md_in)
    snap1 = tree_state(m1.outdir)
    w.config["md"]["rates"] = [90.5, 91.5, 92.5]
    w.save()
    m2 = w.run("md", md_in)
    runs2 = [c for c in m2.tools("md_worker") if c.get("mode") == "run"]
    need(runs2, "the second md run called no worker (%s)" % m2.why())
    need(not set(c["work"] for c in runs2) & set(c["work"] for c in m1.tools("md_worker")), "two md runs share a worker work directory")
    need(tree_state(m1.outdir) == snap1, "the second md run changed the first run's --out")
    rows2 = [row for row in jlines(m2.path("rows_md_tag-m4.jsonl")) if not row.get("skipped")]
    need(sorted(set(nums_at(rows2, "engine"))) == sorted(c["rate"] for c in runs2), "the second md run's rows do not carry its own rates")


def test_downloads_calls_kept_apart():
    w = World("dl2")
    shutil.rmtree(os.path.join(w.pay, "data"))
    drop = ("6IHB", "downloads_tag-m4.json", "download_log_tag-m4.json", "params_markers_tag-m4.json")
    r1 = w.run("downloads", make_in(w, "dl2a", early=False, drop=drop))
    fetches = [c for c in r1.tools("fetch")]
    need(len(fetches) == 2, "downloads made %d fetch calls, expected 2 (6IHB, parameter archive)" % len(fetches))
    need(len(set(c["out"] for c in fetches)) == 2, "both downloads wrote the same path")
    ran_clean(r1, "downloads")
    need(PDB_SHA in text_of(r1.records()), "the downloads record does not carry 6IHB's own sha256 %s" % PDB_SHA[:12])
    need(r1.has("6IHB_tag-m4.pdb") and sha256_file(r1.path("6IHB_tag-m4.pdb")) == PDB_SHA, "6IHB_tag-m4.pdb is not the byte copy of the download")
    snap1 = tree_state(r1.outdir)
    w.config["fetch"]["pdb"] = fx("pair_pair1_tag-m4.pdb")
    w.save()
    r2 = w.run("downloads", make_in(w, "dl2b", early=False, drop=drop))
    other = sha256_file(fx("pair_pair1_tag-m4.pdb"))
    need(other in text_of(r2.records()), "the second downloads run did not record its own file's sha256 (%s)" % r2.why())
    need(tree_state(r1.outdir) == snap1, "the second downloads run changed the first run's --out")
    need(sha256_file(r1.path("6IHB_tag-m4.pdb")) == PDB_SHA, "the first run's 6IHB copy was overwritten")
    need(not r2.has("6IHB_tag-m4.pdb") or sha256_file(r2.path("6IHB_tag-m4.pdb")) == other, "the second run's 6IHB copy is not its own download")


def test_capability_calls_kept_apart():
    # item 4's capability check calls several external programs (two nvidia-smi forms,
    # the interpreter probes, and the tools' --help); run it twice and with two calls
    # inside one run and check every call's outputs stay separate and every call reads
    # its own output.
    w = World("cap2")
    r1 = w.run("capability", empty_in(w, "cap2a"))
    ran_clean(r1, "capability run 1")
    need(r1.has("env_check_tag-m4.json"), "capability run 1 wrote no env_check_tag-m4.json (%s)" % r1.why())
    smi1 = [c for c in r1.calls if c["tool"] == "nvidia-smi"]
    need(len(smi1) >= 2, "capability run 1 made %d nvidia-smi calls, expected the header and the query" % len(smi1))
    need(len(set(c.get("form") for c in smi1)) >= 2, "the nvidia-smi calls of one run are not two distinct calls: %s" % [c.get("form") for c in smi1])
    need(all(c.get("rc") == 0 for c in r1.calls), "a capability call failed in the replay: %s" % [c.get("error") for c in r1.calls if c.get("rc")])
    helps = sorted(c["tool"] for c in r1.calls if c.get("help"))
    for tool in ("colabfold_batch", "lightdock3.py", "lgd_generate_conformations.py"):
        need(tool in helps, "capability run 1 did not run %s --help (%s)" % (tool, helps))
    probes = [c.get("probe") for c in r1.calls if c["tool"] == "python"]
    need(len(set(probes)) == len(probes) and len(probes) >= 2,
         "the interpreter probes of one run are not one call each: %s" % probes)
    t1 = text_of(r1.records())
    need("570.148.08" in t1 and re.search(r'"12\.8"|: 12\.8\b', t1), "run 1 records do not carry its own nvidia-smi outputs: %s" % t1[:200])
    snap1 = tree_state(r1.outdir)
    h2 = os.path.join(w.root, "smi_header_run2.txt")
    q2 = os.path.join(w.root, "smi_query_run2.txt")
    with open(fx("nvidia_smi_header.txt")) as f, open(h2, "w") as g:
        g.write(f.read().replace("570.148.08", "580.65.1").replace("CUDA Version: 12.8", "CUDA Version: 13.0"))
    with open(fx("nvidia_smi_query.txt")) as f, open(q2, "w") as g:
        g.write(f.read().replace("570.148.08", "580.65.1"))
    w.config["nvidia_smi"].update(header=h2, query=q2)
    w.save()
    r2 = w.run("capability", empty_in(w, "cap2b"))
    ran_clean(r2, "capability run 2")
    t2 = text_of(r2.records())
    need("580.65.1" in t2 and re.search(r'"13\.0"|: 13\.0\b', t2),
         "run 2 records do not carry the outputs of its own nvidia-smi calls: %s" % t2[:200])
    need("570.148.08" not in t2, "run 2 records carry run 1's driver: the calls' outputs were mixed")
    need(tree_state(r1.outdir) == snap1, "the second capability run changed the first run's --out")
    need("570.148.08" in text_of(r1.records()), "the first run's records lost their own nvidia-smi outputs")


# item 3: the guard, from the planted environment

def out_numbers(res):
    """every number the stage left in --out: JSON values, numbers inside JSON strings, env.txt and RUN_DONE"""
    nums = []
    for dp, dns, fns in os.walk(res.outdir):
        for fn in fns:
            p = os.path.join(dp, fn)
            if not (fn.endswith((".json", ".txt", ".jsonl")) or fn == "RUN_DONE"):
                continue
            try:
                with open(p) as f:
                    text = f.read()
            except (OSError, UnicodeDecodeError):
                continue
            for m in re.findall(r"(?<![\w.])-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", text):
                try:
                    nums.append(float(m))
                except ValueError:
                    pass
    return nums


def has_near(nums, target, tol):
    return any(abs(x - target) <= tol for x in nums)


def guard_arithmetic(res, timeout, elapsed, allowance, estimates, label):
    nums = out_numbers(res)
    miss = []
    if not has_near(nums, timeout, 1e-6):
        miss.append("REMOTE_TIMEOUT %s" % timeout)
    if not has_near(nums, elapsed, 6):
        miss.append("elapsed %s s" % elapsed)
    if not has_near(nums, allowance, 6):
        miss.append("allowance %s s" % allowance)
    if not any(has_near(nums, e, 1e-6) for e in estimates):
        miss.append("estimate %s s" % " or ".join(str(e) for e in estimates))
    need(not miss, "%s: the record does not carry the guard arithmetic: %s missing" % (label, ", ".join(miss)))


def guard_input_statuses(d):
    return dict((k, v.get("status") if isinstance(v, dict) else v) for k, v in (d.get("inputs") or {}).items())


def test_guard_stops_by_time():
    # the guard refuses the stage whose estimate exceeds its allowance; item 24:
    # its unfinished inputs are unmeasured_by_stop:<kind> with VOID records
    # carrying the full incomplete-run label and calibration_valid false,
    # run_valid is not changed, and the record carries the arithmetic.
    w = World("gstop")
    r = w.run("af2", make_in(w, "gstop", [pipe("anchor_pass")]), elapsed=2450, REMOTE_TIMEOUT=3000)
    need(r.rc == 3, "af2 with 49 to 50 s of allowance (3000 - 2450 - 400 - 100) exit %s, expected 3 (%s)" % (r.rc, r.why()))
    need(not [c for c in r.calls if c["tool"] == "colabfold_batch"], "the guard refused the stage but a prediction call was made")
    d = r.done()
    need(d.get("stopped_by"), "RUN_DONE names no stop")
    st = guard_input_statuses(d)
    need(str(st.get("C1", "")).startswith("unmeasured_by_stop:"), "C1 after a guard stop of af2 is not unmeasured_by_stop: %s" % st)
    c1 = (d.get("inputs") or {}).get("C1") or {}
    need(c1.get("calibration_valid") is False, "C1 after a guard stop: calibration_valid %r, expected false" % c1.get("calibration_valid"))
    need("incomplete run" in text_of(d), "RUN_DONE lacks the incomplete-run label after a stop")
    need(d.get("run_valid") is not False, "a guard stop changed run_valid to false")
    guard_arithmetic(r, 3000, 2450, 50, (120,), "time stop")
    rec = r.rec("endpoint-C1_tag-m4.json")
    need(rec.get("decision") == "VOID" and "incomplete run" in text_of(rec), "C1 after a guard stop is not VOID with the incomplete-run label")


def test_guard_anchor_stop_undecided():
    # a stop before the anchor leaves the anchor undecided: the anchor record is
    # VOID "unmeasured, not holding" (item 18), never a PASS or a FAIL
    w = World("ganchor")
    r = w.run("anchor", make_in(w, "ganchor"), elapsed=2450, REMOTE_TIMEOUT=3000)
    need(r.rc == 3, "anchor with 50 s of allowance exit %s, expected 3 (%s)" % (r.rc, r.why()))
    need(not [c for c in r.calls if c["tool"].startswith("l")], "the guard refused the stage but docking was called")
    a = r.rec("endpoint-anchor_tag-m4.json")
    t = text_of(a)
    need(a.get("decision") == "VOID" and "unmeasured" in t and "not holding" in t,
         "anchor after a guard stop is not VOID 'unmeasured, not holding': %s" % str(a.get("decision")))
    need(not is_num(a.get("values", {}).get("measured")), "anchor after a stop measured %r" % a.get("values", {}).get("measured"))


def test_guard_goes_by_time():
    w = World("ggo")
    w.docking([{"rank_table": fx("rank_table_error_tag-m4.list")}])
    r = w.run("anchor", make_in(w, "ggo"), elapsed=1000, REMOTE_TIMEOUT=3000)
    need([c for c in r.calls if c["tool"] == "lightdock3_setup.py"],
         "with 1500 s left before the margins (3000 - 1000 - 500; ceiling 1000) the anchor did not start (exit %s, %s)" % (r.rc, r.why()))
    need(not (r.has("RUN_DONE") and r.done().get("stopped_by")), "the guard stopped a stage with ample allowance: %s" % r.done().get("stopped_by"))


def test_guard_stops_by_budget():
    w = World("gbud")
    r = w.run("anchor", make_in(w, "gbud"), elapsed=6050, REMOTE_TIMEOUT=100000, PRICE_USD_PER_HOUR="3.00", BUDGET_LEFT_USD="5")
    need(r.rc == 3, "price 3.00 and budget 5 stop at 6000 s; at 6050 s the anchor exit %s, expected 3 (%s)" % (r.rc, r.why()))
    need(not [c for c in r.calls if c["tool"].startswith("l")], "the budget guard refused but docking was called")
    w2 = World("gbud2")
    w2.docking([{"rank_table": fx("rank_table_error_tag-m4.list")}])
    r2 = w2.run("anchor", make_in(w2, "gbud2"), elapsed=6050, REMOTE_TIMEOUT=100000, PRICE_USD_PER_HOUR="1.99", BUDGET_LEFT_USD="5")
    need([c for c in r2.calls if c["tool"] == "lightdock3_setup.py"], "price 1.99 stops at 9045 s; at 6050 s the anchor did not start (exit %s, %s)" % (r2.rc, r2.why()))
    nums = out_numbers(r)
    miss = [n for n, t, tol in (("stop_at 6000 s", 6000, 1e-3), ("elapsed 6050 s", 6050, 6), ("price 3.00", 3.0, 1e-9), ("budget 5", 5.0, 1e-9)) if not has_near(nums, t, tol)]
    need(not miss, "budget stop: the record does not carry the arithmetic: %s missing" % ", ".join(miss))


# item 4: the anchor

def check_perfect(res, label):
    ran_clean(res, label)
    a = res.rec("endpoint-anchor_tag-m4.json")
    v = a.get("values", {})
    need(a.get("decision") == "PASS", "%s: decision %s, expected PASS" % (label, a.get("decision")))
    ov = nums_at(v, "^(contact_)?overlap$|^measured$")
    need(ov and all(abs(x - 1.0) < 1e-9 for x in ov), "%s: overlap %s, expected 1.0" % (label, ov))
    rm = nums_at(v, "^interface_backbone_rmsd")
    need(rm and all(abs(x) < 1e-6 for x in rm), "%s: interface RMSD %s, expected under 1e-6" % (label, rm))
    need(a.get("run_valid") is True, "%s: run_valid %r after a PASS" % (label, a.get("run_valid")))
    return a


def test_anchor_reference_against_itself():
    w = World("self")
    w.docking([{"pose": "self"}, {"pose": "self"}])
    a = check_perfect(w.run("anchor", make_in(w, "self")), "reference against itself")
    fr = a["values"].get("frame")
    need(isinstance(fr, dict), "no values.frame in the anchor record")
    sh = [v for _, v in walk(fr) if isinstance(v, list) and len(v) == 3 and all(is_num(x) for x in v)]
    if all(is_num(fr.get(k)) for k in ("dx", "dy", "dz")):
        sh.append([fr["dx"], fr["dy"], fr["dz"]])
    need(sh and all(abs(x) < 1e-6 for x in sh[0]), "frame shift %s, expected (0, 0, 0)" % (sh[:1],))


def test_anchor_reference_against_rigid_copy():
    r = pipe("anchor_pass")
    a = check_perfect(r, "reference translated (lightdock's centring plus a seeded %s A)" % RIGID_SHIFT)
    res = nums_at(a["values"].get("frame", {}), "resid")
    need(res and all(x < 1e-6 for x in res), "frame residual %s, expected under 1e-6" % res)
    matched = nums_at(a["values"].get("frame", {}), "match")
    need(4142 in matched, "frame matched count %s, expected 4142 capsid atoms (OXT dropped by --noxt)" % matched)


def test_anchor_diagnostics_recorded():
    for label, res in (("pass", pipe("anchor_pass")), ("fail", pipe("anchor_fail"))):
        dg = anchor_values(res).get("diagnostics")
        need(isinstance(dg, dict), "%s: no values.diagnostics" % label)
        for k in ("self_score", "translated_copy", "rotated_copy", "pairing", "independent_scoring"):
            need(isinstance(dg.get(k), dict), "%s: diagnostics lack %s" % (label, k))
            need(dg[k].get("ok") is True, "%s: diagnostic %s not ok: %s" % (label, k, text_of(dg[k])[:200]))
        need(dg["rotated_copy"].get("frame_guard_rejected") is True, "%s: the rotated copy was not rejected by the frame guard" % label)
        for k in ("self_score", "translated_copy"):
            ov = nums_at(dg[k], "overlap")
            rm = nums_at(dg[k], "rmsd")
            need(ov and all(abs(x - 1) < 1e-9 for x in ov) and rm and all(x < 1e-6 for x in rm), "%s: %s not perfect: %s" % (label, k, text_of(dg[k])[:200]))


def test_anchor_box_pose_fails():
    r = pipe("anchor_fail")
    need(r.rc == 4, "anchor on the box's recorded pose exit %s, expected 4 (%s)" % (r.rc, r.why()))
    a = r.rec("endpoint-anchor_tag-m4.json")
    v = a["values"]
    need(a.get("decision") == "FAIL", "decision %s on the recorded pose, expected FAIL" % a.get("decision"))
    need(any(abs(x - BOX_FAIL_RMSD) < 1e-6 for x in nums_at(v, "^interface_backbone_rmsd")),
         "interface RMSD %s, the box recorded %.6f" % (nums_at(v, "^interface_backbone_rmsd"), BOX_FAIL_RMSD))
    need(any(abs(x) < 1e-12 for x in nums_at(v, "^(contact_)?overlap$")), "overlap %s, the box recorded 0.0" % nums_at(v, "^(contact_)?overlap$"))
    need(a.get("run_valid") is False and a.get("run_valid_voided_by"), "anchor FAIL record: run_valid %r, voided_by %r" % (a.get("run_valid"), a.get("run_valid_voided_by")))
    rv = r.rec("RUN_VALID.json")
    need(rv.get("run_valid") is False, "RUN_VALID.json run_valid %r after the miss" % rv.get("run_valid"))
    need("void_by_anchor_miss" not in text_of(r.done()), "RUN_DONE uses the withdrawn status void_by_anchor_miss")


def test_anchor_rotated_copy_is_frame_failure():
    w = World("rot")
    w.docking([{"pose": "native", "rotate_deg": 40.0}, {"pose": "native", "rotate_deg": 40.0}])
    r = w.run("anchor", make_in(w, "rot"))
    d = failed_explicitly(r, "anchor on a rotated copy")
    need(d.get("failure_kind") == "anchor_frame", "failure kind %r, expected anchor_frame" % d.get("failure_kind"))
    need(r.has("anchor_frame_diagnostic_tag-m4.txt"), "no anchor_frame_diagnostic_tag-m4.txt")
    a = r.rec("endpoint-anchor_tag-m4.json")
    need(a.get("decision") != "FAIL" and a.get("decision") != "PASS", "a frame rejection was scored as %s" % a.get("decision"))


def later_records(res):
    return {fn: rec for fn, rec in stage_records(res).items() if fn != "endpoint-anchor_tag-m4.json"}


def test_after_miss_every_later_record_invalid():
    fail = pipe("anchor_fail")
    text = fail.rec("endpoint-anchor_tag-m4.json").get("run_valid_voided_by")
    bad = []
    for st in ("aux_fail", "af2_fail", "md_fail", "storage_fail", "endpoints_fail"):
        r = pipe(st)
        recs = later_records(r)
        if not recs:
            bad.append("%s wrote no record (exit %s, %s)" % (st, r.rc, r.why()[:80]))
        for fn, rec in recs.items():
            if rec.get("run_valid") is not False:
                bad.append("%s %s run_valid %r" % (st, fn, rec.get("run_valid")))
            elif rec.get("run_valid_voided_by") != text:
                bad.append("%s %s run_valid_voided_by %r" % (st, fn, str(rec.get("run_valid_voided_by"))[:40]))
            elif "measured after an anchor miss" not in text_of(rec):
                bad.append("%s %s lacks the label 'measured after an anchor miss'" % (st, fn))
    need(not bad, "; ".join(bad[:4]))
    e = pipe("endpoints_fail")
    need(e.rc == 4, "endpoints after an anchor miss with well-formed inputs exit %s, expected 4 (%s)" % (e.rc, e.why()))


def test_after_miss_calibration_by_own_checks():
    ok, ko = pipe("endpoints_pass"), pipe("endpoints_fail")
    bad = []
    for i in (1, 2, 3, 4):
        a, b = endpoint(ok, i), endpoint(ko, i)
        if calib(a) is not True:
            bad.append("C%d calibration_valid %r on well-formed inputs after a PASS" % (i, calib(a)))
        if calib(b) != calib(a):
            bad.append("C%d calibration_valid %r after the miss, %r after the PASS" % (i, calib(b), calib(a)))
        if b.get("decision") != a.get("decision") or b.get("decision") not in ("PASS", "FAIL"):
            bad.append("C%d decision %s after the miss, %s after the PASS (band decisions expected)" % (i, b.get("decision"), a.get("decision")))
        if not isinstance(b.get("values", {}).get("calibration_checks"), (list, dict)) or not b["values"]["calibration_checks"]:
            bad.append("C%d has no calibration_checks" % i)
    need(not bad, "; ".join(bad[:4]))


def test_after_miss_own_check_failure_stays_own():
    w = World("noscore")
    w.config["colabfold"]["skip_score_call"] = 2
    w.save()
    fail = pipe("anchor_fail")
    af2 = w.run("af2", make_in(w, "noscore", [fail]))
    need(af2.rc != 2, "af2 exit 2 (%s)" % af2.why())
    e = w.run("endpoints", make_in(w, "noscore_end", [fail, pipe("aux_fail"), af2, pipe("md_fail"), pipe("storage_fail")]))
    need(e.rc == 4, "endpoints exit %s, expected 4 (%s)" % (e.rc, e.why()))
    c1 = endpoint(e, 1)
    need(calib(c1) is False and c1.get("decision") == "VOID", "C1 with a run lacking a score file: calibration_valid %r decision %s" % (calib(c1), c1.get("decision")))
    need(is_num(c1.get("values", {}).get("measured")), "C1 VOID by its own check lost the raw measured value")
    ref = pipe("endpoints_fail")
    for i in (2, 3, 4):
        need(calib(endpoint(e, i)) == calib(endpoint(ref, i)), "C%d calibration_valid changed by C1's check" % i)
    a0, a1 = fail.rec("endpoint-anchor_tag-m4.json"), (e.rec("endpoint-anchor_tag-m4.json") if e.has("endpoint-anchor_tag-m4.json") else None)
    if a1 is not None:
        need(a1.get("decision") == "FAIL" and a1.get("values", {}).get("measured") == a0.get("values", {}).get("measured")
             and a1.get("values", {}).get("interface_backbone_rmsd_a") == a0.get("values", {}).get("interface_backbone_rmsd_a"),
             "the anchor record changed after later stages: %s / %s" % (a1.get("decision"), a1.get("values", {}).get("measured")))


def test_anchor_verdict_unchanged_by_later_stages():
    a0 = pipe("anchor_fail").rec("endpoint-anchor_tag-m4.json")
    e = pipe("endpoints_fail")
    a1 = e.rec("endpoint-anchor_tag-m4.json")
    for k in ("decision", "run_valid", "run_valid_voided_by"):
        need(a1.get(k) == a0.get(k), "anchor %s changed from %r to %r" % (k, a0.get(k), a1.get(k)))
    for k in ("measured", "contact_overlap", "interface_backbone_rmsd_a", "serial_parallel_rmsd_a"):
        need(a1.get("values", {}).get(k) == a0.get("values", {}).get(k), "anchor values.%s changed" % k)
    rv = e.rec("RUN_VALID.json")
    need(rv.get("run_valid") is False, "RUN_VALID.json run_valid %r at the end of a run with an anchor miss" % rv.get("run_valid"))
    s = e.rec("m4_summary.json")
    need("FAIL" in text_of(s.get("compute", s)) or "FAIL" in text_of(s), "summary does not carry the anchor's FAIL")


def test_md_reporter_nan_and_atoms_calibration():
    ref = pipe("endpoints_pass")
    bad = []
    for label, md in (("an MD complex of 119,999 atoms", {"atoms": [119999, 150000, 150000]}),
                      ("a reporter file with a NaN energy", {"nan_call": 1})):
        w = World("mdcal")
        w.config["md"].update(md)
        w.save()
        m = w.run("md", make_in(w, "mdcal", [pipe("anchor_pass"), pipe("aux_pass")]))
        if not [c for c in m.tools("md_worker") if c.get("mode") == "run"]:
            bad.append("%s: the md stage ran no worker (exit %s, %s)" % (label, m.rc, m.why()[:80]))
            continue
        e = w.run("endpoints", make_in(w, "mdcal_end", [pipe("anchor_pass"), pipe("aux_pass"), pipe("af2_pass"), m, pipe("storage_pass")]))
        c2 = endpoint(e, 2)
        if calib(c2) is not False:
            bad.append("%s: C2 calibration_valid %r" % (label, calib(c2)))
        elif c2.get("decision") != "VOID" or not is_num(c2.get("values", {}).get("measured")):
            bad.append("%s: C2 decision %s measured %r (VOID with the raw value expected)" % (label, c2.get("decision"), c2.get("values", {}).get("measured")))
        for i in (1, 3, 4):
            if calib(endpoint(e, i)) != calib(endpoint(ref, i)):
                bad.append("%s changed C%d calibration_valid" % (label, i))
    need(not bad, "; ".join(bad[:3]))


# item 5: the records

MACHINE_KEYS = ["instance_type", "gpu_name", "gpu_driver", "cuda_runtime_version", "start_utc", "end_utc", "price_usd_per_hour",
                "observed_lock_sha256", "expected_lock_sha256", "venv_path", "environment_changed_by_fixer", "held_attempts"]
RECORD_KEYS = ["cell", "inputs", "metric", "values", "threshold", "decision_rule", "decision", "run_valid"]


def unit_states(unit, key):
    """values.unit states the card's unit (item 21): the token or its spelling"""
    t = str(unit or "").strip().lower()
    if not t or t == "none":
        return False
    if key == "C1":
        return "run" in t and ("hour" in t or "h/" in t or t.startswith("h ") or t.endswith(" h") or "h per" in t)
    if key == "C2":
        return "day" in t and ("ns/day" in t or "ns per day" in t or "nanosecond" in t)
    if key == "C3":
        return "pair" in t and ("hour" in t or "h/" in t or t.startswith("h ") or t.endswith(" h") or "h per" in t)
    return "gib" in t


def check_record(rec, fn, extra=()):
    miss = [k for k in RECORD_KEYS if k not in rec]
    need(not miss, "%s lacks %s" % (fn, miss))
    need(isinstance(rec["inputs"], list) and rec["inputs"], "%s has no inputs" % fn)
    need(all(("sha256" in i or "sha256_full" in i) for i in rec["inputs"] if isinstance(i, dict) and i.get("present", True)), "%s: an input without a hash" % fn)
    m = rec["values"].get("machine")
    need(isinstance(m, dict), "%s: no values.machine" % fn)
    miss = [k for k in MACHINE_KEYS if k not in m]
    need(not miss, "%s: values.machine lacks %s" % (fn, miss))
    for k in extra:
        need(k in rec["values"], "%s: values lack %s" % (fn, k))


def test_records_controls():
    r = pipe("controls")
    ran_clean(r, "controls with a planted 60 s sleep")
    s = r.rec("control-sleep_tag-m4.json")
    check_record(s, "control-sleep_tag-m4.json")
    sl = [c for c in r.tools("sleep")]
    need(len(sl) == 1, "the sleep control called the sleep program %d times" % len(sl))
    secs = sl[0]["t1"] - sl[0]["t0"]
    need(any(abs(v - secs) < 1.0 for v in nums_at(s["values"], "measured|seconds|_s$")), "sleep record does not carry the %.1f s the program slept" % secs)
    e = r.rec("control-empty-run_tag-m4.json")
    check_record(e, "control-empty-run_tag-m4.json")
    u = r.rec("control-unit-and-scale_tag-m4.json")
    check_record(u, "control-unit-and-scale_tag-m4.json")
    need(u["values"].get("kind") == "worked_examples", "unit-and-scale values.kind %r" % u["values"].get("kind"))
    need("rows_af2_tag-m4.jsonl" in text_of(u["values"].get("raw_values_in")), "unit-and-scale raw_values_in does not name rows_af2_tag-m4.jsonl")
    need(r.has("rows_controls_tag-m4.jsonl"), "no rows_controls_tag-m4.jsonl")


def test_sleep_control_failure():
    w = World("sleepbad")
    w.set(sleep={"seconds": 0.0})
    r = w.run("controls", make_in(w, "sleepbad", early=False))
    failed_explicitly(r, "controls with a sleep that returns at once")
    s = r.rec("control-sleep_tag-m4.json")
    need(s.get("run_valid") is False or s.get("decision") in ("FAIL", "VOID"), "sleep record does not show the failed check")


def test_records_env_check_and_lock():
    r = pipe("capability")
    ran_clean(r, "capability on the recorded probes")
    e = r.rec("env_check_tag-m4.json")
    v = e.get("values", {})
    for k in ("expected_lock_sha256", "observed_lock_sha256", "venv_path", "python_version", "equal"):
        need(k in v, "env_check values lack %s" % k)
    need(v["observed_lock_sha256"] == LOCK and v["equal"] is True, "observed lock %r equal %r on the recorded pip freeze" % (v["observed_lock_sha256"], v["equal"]))
    t = text_of(r.records())
    smi = [c for c in r.tools("nvidia-smi") if c.get("form") in ("header", "query")]
    need(len(set(c["form"] for c in smi)) == 2, "capability did not read both nvidia-smi outputs (header and query)")
    for want, src in (("NVIDIA A100-SXM4-40GB", "the query"), ("570.148.08", "the query and header"), ("12.8", "the header")):
        need(want in t, "%s from %s of nvidia-smi is not in the capability records" % (want, src))
    w = World("lock")
    r2 = w.run("capability", empty_in(w, "lock"), ENV_LOCK_SHA256=LOCK[:-1] + ("0" if LOCK[-1] != "0" else "1"))
    failed_explicitly(r2, "capability with a different lock hash")
    v2 = r2.rec("env_check_tag-m4.json").get("values", {})
    need(v2.get("equal") is False, "env_check equal %r on a lock mismatch" % v2.get("equal"))
    r3 = w.run("capability", empty_in(w, "lock3"), ENV_LOCK_SHA256=None)
    failed_explicitly(r3, "capability with ENV_LOCK_SHA256 unset")


def test_records_anchor_fields():
    r = pipe("anchor_pass")
    ran_clean(r, "anchor on the native pose")
    a = r.rec("endpoint-anchor_tag-m4.json")
    check_record(a, "endpoint-anchor_tag-m4.json", ("measured", "published", "tolerance", "diagnostics", "frame", "docking_parameters", "docking_order"))
    dp = a["values"]["docking_parameters"]
    need(isinstance(dp.get("rank_table_columns"), dict) and "mapping" in dp["rank_table_columns"], "docking_parameters lack rank_table_columns with its mapping")
    need((dp.get("swarms"), dp.get("glowworms"), dp.get("steps")) == (2, 20, 20), "docking parameters %s, of record 2 swarms, 20 glowworms, 20 steps" % ((dp.get("swarms"), dp.get("glowworms"), dp.get("steps")),))
    need(a["values"].get("independent_code") == "not run: single docking code" or a.get("independent_code") == "not run: single docking code",
         "independent_code text missing")
    need(isinstance(a["values"].get("engine"), dict), "anchor values lack engine labels")
    need(r.has("rank_table_anchor_serial_tag-m4.list") and r.has("rank_table_anchor_parallel_tag-m4.list"), "raw rank tables not kept")


def test_records_endpoints():
    r = pipe("endpoints_pass")
    ran_clean(r, "endpoints after a PASS on well-formed inputs")
    units = {"C1": "h", "C2": "ns/day", "C3": "h", "C4": "GiB"}
    for i in (1, 2, 3, 4):
        fn = "endpoint-C%d_tag-m4.json" % i
        rec = r.rec(fn)
        check_record(rec, fn, ("measured", "unit", "card_value", "band", "calibration_checks"))
        v = rec["values"]
        cv, band = CARD["C%d" % i]
        need(is_num(v["measured"]), "%s measured %r is not a number" % (fn, v["measured"]))
        need(unit_states(v["unit"], "C%d" % i), "%s unit %r does not state the card's unit (%s)" % (fn, v["unit"], units["C%d" % i]))
        need(v["card_value"] == cv and [float(x) for x in v["band"]] == band, "%s card_value/band %r %r" % (fn, v["card_value"], v["band"]))
        need(rec["decision"] in ("PASS", "FAIL", "VOID"), "%s decision %r" % (fn, rec["decision"]))
        lo, hi = band
        if not (lo * 0.9 <= v["measured"] <= lo * 1.1 or hi * 0.9 <= v["measured"] <= hi * 1.1):
            need(rec["decision"] == ("PASS" if lo <= v["measured"] <= hi else "FAIL"), "%s measured %s in band %s decided %s" % (fn, v["measured"], band, rec["decision"]))
        need(calib(rec) in (True, False), "%s lacks calibration_valid" % fn)
        need("n" in v, "%s values lack n" % fn)
    c1 = endpoint(r, 1)["values"]
    need(c1.get("gate_value") == 1 and "gate_pass" in c1 and "fallback" in str(c1.get("gate_else", "")) or "fallback line" in str(c1.get("gate_else", "")),
         "C1 lacks gate_value 1, gate_pass and the fallback text")
    for i in (2, 3):
        need(endpoint(r, i)["values"].get("gate") == "not applicable: the card's gate is on af2_h_per_run", "C%d gate text" % i)
    d = r.done()
    need(d.get("exit_code") == r.rc, "RUN_DONE exit_code %r, the process exited %s" % (d.get("exit_code"), r.rc))
    for i in (1, 2, 3, 4):
        s = d.get("inputs", {}).get("C%d" % i, {})
        need(re.match(r"^(decided|void_by_rule:.+|unmeasured_by_stop:.+)$", str(s.get("status"))) and "calibration_valid" in s,
             "RUN_DONE C%d status %r" % (i, s))
    s = r.rec("m4_summary.json")
    need(list(s)[0] == "what_this_run_decides", "summary first key %r" % list(s)[:1])
    comp = s.get("compute")
    stages = comp.get("stages") if isinstance(comp, dict) else comp
    need(isinstance(stages, list) and [x.get("stage") for x in stages] == STAGES, "compute table stages %s" % ([x.get("stage") for x in stages] if isinstance(stages, list) else comp,))
    for x in stages:
        miss = [k for k in ("start_utc", "end_utc", "wall_clock_s", "gpu_busy_s", "gpu_name", "exit_code", "ran") if k not in x]
        need(not miss, "compute entry %s lacks %s" % (x.get("stage"), miss))
    for k in ("instance_type", "price_usd_per_hour", "elapsed_since_t0_s", "estimated_spend_usd"):
        need(k in text_of(comp), "compute table lacks %s" % k)
    need(r.rec("RUN_VALID.json").get("run_valid") is True, "RUN_VALID.json after a PASS run")
    need(r.has("env.txt") and "7200" in open(r.path("env.txt")).read(), "env.txt does not record REMOTE_TIMEOUT 7200")


def test_records_downloads():
    r = pipe("downloads")
    ran_clean(r, "downloads")
    need(r.has("6IHB_tag-m4.pdb") and sha256_file(r.path("6IHB_tag-m4.pdb")) == PDB_SHA, "6IHB_tag-m4.pdb is not the downloaded file byte for byte")
    dl = r.rec("downloads_tag-m4.json")
    t = text_of(dl)
    for want in ("https://files.rcsb.org/download/6IHB.pdb", PDB_SHA, "alphafold_params"):
        need(want in t, "downloads record lacks %s" % want[:40])
    pr = r.rec("pairs_tag-m4.json")
    pairs = pr.get("pairs")
    need(isinstance(pairs, list) and len(pairs) == 3, "pairs_tag-m4.json does not hold 3 pairs")
    lens = []
    for p in pairs:
        for k in ("chain_map", "sequences", "lengths", "fasta_sha256", "pdb_sha256"):
            need(k in p, "pair %s lacks %s" % (p.get("pair"), k))
        fa = r.path(os.path.basename(p.get("fasta_path", "pair_%s_tag-m4.fasta" % p.get("pair"))))
        pd = r.path(os.path.basename(p.get("pdb_path", "pair_%s_tag-m4.pdb" % p.get("pair"))))
        need(os.path.exists(fa) and sha256_file(fa) == p["fasta_sha256"], "FASTA of %s missing or not the hash recorded" % p.get("pair"))
        need(os.path.exists(pd) and sha256_file(pd) == p["pdb_sha256"], "PDB of %s missing or not the hash recorded" % p.get("pair"))
        tot = p.get("total_residues", sum(p["lengths"].values()))
        need(750 <= tot <= 1000, "pair %s has %s residues, outside 750 to 1000" % (p.get("pair"), tot))
        need(set(p["chain_map"].values()) == {"capsid", "receptor"}, "pair %s roles %s" % (p.get("pair"), p["chain_map"]))
        lens.append(tot)
    lens.sort()
    need(all(b - a >= 20 for a, b in zip(lens, lens[1:])), "pair lengths %s are not 20 residues apart" % lens)
    need([p["total_residues"] for p in jload(fx("pairs_tag-m4.json"))["pairs"]] == [p.get("total_residues") for p in pairs],
         "pairs built from the same 6IHB differ from the pairs recorded on the box")


def test_records_rows():
    bad = []
    a = pipe("af2_pass")
    if not a.has("rows_af2_tag-m4.jsonl"):
        bad.append("no rows_af2_tag-m4.jsonl")
    else:
        for row in jlines(a.path("rows_af2_tag-m4.jsonl")):
            for k in ("pair", "seed", "incomplete", "download_in_timed_call"):
                if k not in row:
                    bad.append("af2 row lacks %s" % k)
            if row.get("download_in_timed_call") is not False:
                bad.append("af2 row download_in_timed_call %r with the parameters in place" % row.get("download_in_timed_call"))
    m = pipe("md_pass")
    if not m.has("rows_md_tag-m4.jsonl"):
        bad.append("no rows_md_tag-m4.jsonl")
    else:
        for row in jlines(m.path("rows_md_tag-m4.jsonl")):
            if "frame_interval_ps" not in text_of(row) or "complex" not in row:
                bad.append("md row lacks complex or frame_interval_ps: %s" % text_of(row)[:80])
    x = pipe("aux_pass")
    if not x.has("rows_aux_tag-m4.jsonl"):
        bad.append("no rows_aux_tag-m4.jsonl (%s)" % x.why())
    s = pipe("storage_pass")
    if not s.has("rows_storage_tag-m4.jsonl"):
        bad.append("no rows_storage_tag-m4.jsonl (%s)" % s.why())
    need(not bad, "; ".join(sorted(set(bad))[:4]))


def test_writes_only_under_out():
    pipe("anchor_pass")
    need(not OUTSIDE_WRITES, "stages wrote outside --out: " + "; ".join("%s: %s %s" % (s, a, b) for s, a, b in OUTSIDE_WRITES[:3]))


def test_stage_exit_code_on_success():
    r = pipe("anchor_pass")
    need(anchor_values(r).get("measured") == 1.0, "the anchor on the native pose did not pass (%s)" % r.why())
    d = r.done()
    need(r.rc == 0 and d.get("exit_code") == 0,
         "a stage that did all its work exits %s (RUN_DONE %s, statuses %s); item 7 has exit 3 only for a guard, ceiling or timeout stop"
         % (r.rc, d.get("exit_code"), sorted(set(str(v.get("status")) for v in d.get("inputs", {}).values() if isinstance(v, dict)))))


TESTS = [
    ("stage_exit_code_on_success", test_stage_exit_code_on_success),
    ("parse_nvidia_smi_header", test_parse_nvidia_smi_header),
    ("parse_nvidia_smi_query", test_parse_nvidia_smi_query),
    ("parse_etimes", test_parse_etimes),
    ("parse_rank_table_recorded", test_parse_rank_table_recorded),
    ("parse_rank_table_malformed", test_parse_rank_table_malformed),
    ("parse_pdb", test_parse_pdb),
    ("parse_colabfold_log", test_parse_colabfold_log),
    ("parse_reporter_file", test_parse_reporter_file),
    ("parse_engine_rate_line", test_parse_engine_rate_line),
    ("parse_af2_timing_rows", test_parse_af2_timing_rows),
    ("stage_fails_on_malformed_rank_table", test_stage_fails_on_malformed_rank_table),
    ("stage_fails_on_truncated_pose", test_stage_fails_on_truncated_pose),
    ("stage_fails_on_malformed_nvidia_smi", test_stage_fails_on_malformed_nvidia_smi),
    ("stage_fails_on_colabfold_error", test_stage_fails_on_colabfold_error),
    ("stage_never_defaults_colabfold_field", test_stage_never_defaults_colabfold_field),
    ("stage_fails_on_malformed_af2_rows", test_stage_fails_on_malformed_af2_rows),
    ("stage_reports_missing_inputs", test_stage_reports_missing_inputs),
    ("anchor_calls_kept_apart", test_anchor_calls_kept_apart),
    ("aux_calls_kept_apart", test_aux_calls_kept_apart),
    ("af2_calls_kept_apart", test_af2_calls_kept_apart),
    ("md_calls_kept_apart", test_md_calls_kept_apart),
    ("downloads_calls_kept_apart", test_downloads_calls_kept_apart),
    ("capability_calls_kept_apart", test_capability_calls_kept_apart),
    ("guard_stops_by_time", test_guard_stops_by_time),
    ("guard_anchor_stop_undecided", test_guard_anchor_stop_undecided),
    ("guard_goes_by_time", test_guard_goes_by_time),
    ("guard_stops_by_budget", test_guard_stops_by_budget),
    ("anchor_reference_against_itself", test_anchor_reference_against_itself),
    ("anchor_reference_against_rigid_copy", test_anchor_reference_against_rigid_copy),
    ("anchor_diagnostics_recorded", test_anchor_diagnostics_recorded),
    ("anchor_box_pose_fails", test_anchor_box_pose_fails),
    ("anchor_rotated_copy_is_frame_failure", test_anchor_rotated_copy_is_frame_failure),
    ("after_miss_every_later_record_invalid", test_after_miss_every_later_record_invalid),
    ("after_miss_calibration_by_own_checks", test_after_miss_calibration_by_own_checks),
    ("after_miss_own_check_failure_stays_own", test_after_miss_own_check_failure_stays_own),
    ("anchor_verdict_unchanged_by_later_stages", test_anchor_verdict_unchanged_by_later_stages),
    ("md_reporter_nan_and_atoms_calibration", test_md_reporter_nan_and_atoms_calibration),
    ("records_controls", test_records_controls),
    ("sleep_control_failure", test_sleep_control_failure),
    ("records_env_check_and_lock", test_records_env_check_and_lock),
    ("records_anchor_fields", test_records_anchor_fields),
    ("records_endpoints", test_records_endpoints),
    ("records_downloads", test_records_downloads),
    ("records_rows", test_records_rows),
    ("writes_only_under_out", test_writes_only_under_out),
]


def main():
    global RUNNER
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--runner", required=True)
    ap.add_argument("--only", default=None, help="comma-separated test names (for a partial run)")
    ap.add_argument("--keep", action="store_true", help="keep the temporary directories")
    args = ap.parse_args()
    RUNNER = os.path.abspath(args.runner)
    chosen = TESTS
    if args.only:
        names = set(args.only.split(","))
        chosen = [t for t in TESTS if t[0] in names]
    passed = 0
    t_start = time.time()
    for name, fn in chosen:
        try:
            if not os.path.exists(RUNNER):
                raise Fail("runner %s does not exist" % RUNNER)
            fn()
            print("TEST %s: PASS" % name)
            passed += 1
        except Fail as e:
            print("TEST %s: FAIL %s" % (name, " ".join(str(e).split())[:400]))
        except Exception as e:
            tb = traceback.extract_tb(sys.exc_info()[2])[-1]
            print("TEST %s: FAIL test error %s: %s (line %s)" % (name, type(e).__name__, " ".join(str(e).split())[:300], tb.lineno))
        sys.stdout.flush()
    if not args.keep:
        for d in WORLDS:
            shutil.rmtree(d, ignore_errors=True)
    total = len(chosen)
    sys.stderr.write("tests took %.0f s\n" % (time.time() - t_start))
    print("TESTS: %d of %d passed" % (passed, total))
    ok = passed == total and total > 0
    print("TESTS: PASS" if ok else "TESTS: FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
