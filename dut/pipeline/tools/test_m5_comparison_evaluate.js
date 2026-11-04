#!/usr/bin/env node
'use strict'

// Black-box contract tests for the sealed comparison on the box (U57b): m5/SCHEMAS.md "Sealed comparison (U57,
// U58)", bullet "Evaluate, comparison mode (U57)" (separated users, versions, rounds, job files and tokens, the
// wrapper, the private-data removal, timeouts, compute), the scorer's output file and "Evaluate status in
// comparison mode". "Values" (metric values) and the scorer's own rules (U58) are covered elsewhere. Never inspect
// pipeline.js, score_comparison.py, cmp_users.sh, cmp_system.py, cmp_wrap.py, idea/wf.js or git history.
//
// The fake box (as in tools/test_m5_comparison_pipeline.js) really executes every box command locally, in a
// temporary shared run directory. Programs that cannot run for real here are replaced by logging fakes first on the
// box PATH: sudo (runs the command as the box user; `-u` marks the part user in the environment and records the
// process for pkill/pgrep), the account tools (useradd, adduser, usermod, groupadd, gpasswd, chown, chgrp, install
// with an owner), iptables and ip6tables (a rule table), pkill and pgrep (the processes started through `sudo -u`),
// find (the `-writable` listing of `/` comes from the fixture; `-user cmp-arm`/`-user cmp-eval` stand for the
// entries named `cmparm-*`/`cmpeval-*`, the fixture's marker of what that user created), nvidia-smi (two fixed
// GPUs), lscpu, ldd, id, getent and ipcrm. Every fake appends its arguments to the case's fake log.
// This file is also the stub agent module (WF_STUB): with args.harness_from only intake is called.
// Conventions the contract leaves open, fixed here: rounds are numbered from 1 within their kind (w1.., r1.., as in
// tools/test_m5_comparison_score.py) in the job file, the fetch folders and the compute rows; a round's pairs are
// shuffled from arm-major order; `env -i` may carry a working-directory option (-C) before the variables; the
// writable listing may use -print0; the evaluator part's streams may be logged as log/evaluator.*; boxrun's remote
// files of a command are the top-level files of the shared run directory named <receipt name>.<suffix>.
// The fakes also stand in for ipcs, ipcmk and ipcrm (a fixture table of System V objects, see the ipc fake).
// Usage: node tools/test_m5_comparison_evaluate.js [case-name regex] [keep | debug [log count]]
const fs = require('node:fs')
const path = require('node:path')
const os = require('node:os')
const crypto = require('node:crypto')
const assert = require('node:assert/strict')
const { spawn, spawnSync } = require('node:child_process')

const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex')
const read = file => JSON.parse(fs.readFileSync(file, 'utf8'))
const rows = file => fs.existsSync(file) ? fs.readFileSync(file, 'utf8').split('\n').filter(Boolean).map(JSON.parse) : []
const clone = value => JSON.parse(JSON.stringify(value))
function writeFile(file, text, mode) {
  fs.mkdirSync(path.dirname(file), { recursive: true })
  fs.writeFileSync(file, text, mode ? { mode } : undefined)
}

const ANCHORS = [{ id: 'first', published_value: 100, tolerance: 1, quantity: 'fixture', source: 'fixture' },
  { id: 'second', published_value: 0, tolerance: 0, quantity: 'fixture', source: 'fixture' }]

// ---- Stub agents ------------------------------------------------------------------------------------------
module.exports = {
  async run(options) {
    const root = process.env.M5_CE_ROOT
    const title = options.title
    const view = options.isolation && typeof options.isolation.directory === 'string' ? options.isolation.directory : null
    fs.appendFileSync(process.env.M5_CE_CALLS, JSON.stringify({ label: title, isolated: Boolean(view) }) + '\n')
    let facts = { v: `${title} stub` }
    if (title === 'intake') {
      facts = { found: true, anchors_count: ANCHORS.length, data: 'available', licence: 'permitted', stock_environment: true, size: 'tiny' }
      const intake = {
        'benchmark.json': { identity: 'contract fixture', arms: [{ id: 'A1', source: 'https://example.org/a1', pin: 'v1', commands: [['true']] }] },
        'data.json': { availability: 'available', licences: ['MIT'], required_inputs: ['fixture'] },
        'anchors.json': ANCHORS,
        'baseline.json': { repo: 'https://example.org/fixture', pin: 'fixture-v1', build_commands: ['true'], run_commands: ['true'], published_configuration: { n: 10 } },
        'EXECUTION.json': { representative_scale: { n: 10 }, inputs: ['fixture'], outputs: ['quantity'], timing_scope: 'whole process' },
      }
      for (const [name, value] of Object.entries(intake)) writeFile(path.join(view ?? path.join(root, 'agent'), 'intake', name), JSON.stringify(value) + '\n')
    }
    return { text: JSON.stringify(facts), json: facts, jsonError: null, sessionID: 'stub',
      tokens: { input: 10, output: 5, reasoning: 0 }, cost: 0.001, tools: 0, ms: 5, errors: [], refusal: false }
  },
  async exportSession(id, file) { fs.writeFileSync(file, '{}') },
}
if (require.main !== module) return

const ROOT = path.resolve(__dirname, '..')
const STAGES = ['intake', 'reproduce', 'profile', 'seal', 'propose', 'implement', 'evaluate', 'takeaways']
const FACTS = ['validity_pass', 'equivalence_pass', 'performance_pass', 'equal_cost', 'speedup_published',
  'speedup_tuned', 'cost_ratio', 'prediction_ratio', 'curve_points', 'tokens_known', 'gpu_busy_known']
const PROBE = 'comparison-evaluate-probe-73215'
const PRICE = 2.5
const BOX_USER = os.userInfo().username, BOX_UID = String(process.getuid())
const GPUS = [
  { index: '0', name: 'Fake GPU Alpha', uuid: 'GPU-11111111-2222-3333-4444-555555555555', 'memory.total': '81559', 'utilization.gpu': '30', driver_version: '550.54.15', count: '2' },
  { index: '1', name: 'Fake GPU Alpha', uuid: 'GPU-66666666-7777-8888-9999-000000000000', 'memory.total': '81559', 'utilization.gpu': '20', driver_version: '550.54.15', count: '2' },
]
const SAMPLE = 0.5 // one utilization sample: (30 + 20) / 100 GPU-seconds
const DRIVER = '550.54.15', CUDA = '12.4', CPU_MODEL = 'Fake CPU Model 9000', CPU_COUNT = 12
// Top-level entries of the shared run directory that run/ never links (SCHEMAS.md "Each invocation").
const NOT_LINKED = ['out', 'profiler', 'concurrency-work', 'evaluation-work', 'units-check', 'comparison-work', 'comparison-jobs', 'cmp-private']
const COMPARISON_OPS = ['comparison-users', 'versions', 'comparison-job', 'comparison', 'comparison-private-remove']
const WRAP_KEYS = ['adapter_rc', 'adapter_wall_s', 'commands', 'eval_gpu_busy_known', 'eval_gpu_busy_s', 'eval_rc', 'eval_status', 'eval_wall_s', 'gpu_busy_known', 'gpu_busy_s', 'status']
const COMMAND_KEYS = ['argv', 'executable', 'rc', 'sha256', 'wall_s']
const JOB_KEYS = ['arm', 'arm_timeout_s', 'eval_timeout_s', 'input', 'left_s', 'mode', 'round']
const INV_KEYS = ['arm', 'attributed_usd', 'eval_gpu_busy_s', 'eval_status', 'eval_wall_s', 'gpu_busy_known', 'gpu_busy_s', 'input', 'round', 'status', 'wall_s']
const ARM_KEYS = ['arm', 'attributed_usd', 'eval_gpu_busy_s', 'eval_wall_s', 'gpu_busy_known', 'gpu_busy_s', 'invocations', 'wall_s']
const namesArm = text => /(^|[^A-Za-z0-9])A[0-9]([^A-Za-z0-9]|$)/.test(String(text))
const near = (actual, expected, label) => assert.ok(typeof actual === 'number' && Math.abs(actual - expected) <= 1e-9 * Math.max(1, Math.abs(expected)), `${label}: ${actual} != ${expected}`)
const modeOf = file => (fs.statSync(file).mode & 0o7777).toString(8)
const q = text => `'${String(text).replace(/'/g, `'\\''`)}'`
const sh = body => '#!/usr/bin/env bash\nset -eu\n' + body + '\n'
const escapePath = text => text.replace(/[*?[\\]/g, match => '\\' + match)

function realTool(name) {
  for (const directory of (process.env.PATH ?? '').split(path.delimiter)) {
    const file = path.join(directory, name)
    try { fs.accessSync(file, fs.constants.X_OK); if (fs.statSync(file).isFile()) return file } catch {}
  }
  return null
}
const REAL = Object.fromEntries(['find', 'id', 'getent', 'pkill', 'pgrep', 'ldd', 'install'].map(name => [name, realTool(name)]))

// ---- Fakes (python3), each with its case configuration inlined ------------------------------------------------
const PRELUDE = String.raw`#!/usr/bin/env python3
import json, os, signal, sys, time
CFG = json.loads(CFG_JSON)
UIDS = {"cmp-arm": 64901, "cmp-eval": 64902}
def context():
    return os.environ.get("FAKE_SUDO_USER") or ("root" if os.environ.get("FAKE_SUDO_ROOT") == "1" else None)
def log(tool, **extra):
    try:
        cwd = os.getcwd()
    except OSError:
        cwd = None
    row = dict(tool=tool, argv=sys.argv[1:], ctx=context(), cwd=cwd, t=time.time(), pid=os.getpid())
    row.update(extra)
    with open(CFG["log"], "a") as handle:
        handle.write(json.dumps(row) + "\n")
def real(name, argv=None):
    target = CFG["real"].get(name)
    if not target:
        sys.stderr.write("fake: no real " + name + "\n")
        sys.exit(127)
    os.execv(target, [name] + (sys.argv[1:] if argv is None else argv))
def users():
    try:
        with open(CFG["users"]) as handle:
            return json.load(handle)
    except OSError:
        return []
def save_users(value):
    tmp = CFG["users"] + ".%d" % os.getpid()
    with open(tmp, "w") as handle:
        json.dump(value, handle)
    os.replace(tmp, CFG["users"])
def is_root():
    return os.environ.get("FAKE_SUDO_ROOT") == "1"
`
const FAKES = {
  sudo: String.raw`
args = sys.argv[1:]
opts, target, i = [], None, 0
while i < len(args):
    a = args[i]
    if a == "--":
        i += 1
        break
    if a == "-u" and i + 1 < len(args):
        target = args[i + 1]
        i += 2
        continue
    if a.startswith("-") and len(a) > 1:
        opts.append(a)
        i += 1
        continue
    break
cmd = args[i:]
log("sudo", target=target, cmd=cmd)
if "-n" not in opts or not cmd:
    sys.stderr.write("fake sudo: -n and a command are required\n")
    sys.exit(1)
env = dict(os.environ)
if target in (None, "root"):
    env["FAKE_SUDO_ROOT"] = "1"
    env.pop("FAKE_SUDO_USER", None)
    os.execvpe(cmd[0], cmd, env)
if target not in users():
    sys.stderr.write("sudo: unknown user " + target + "\n")
    sys.exit(1)
procs = os.path.join(CFG["state"], "procs-" + target)
os.makedirs(procs, exist_ok=True)
with open("/proc/self/stat") as handle:
    start = handle.read().rsplit(")", 1)[1].split()[19]
with open(os.path.join(procs, str(os.getpid())), "w") as handle:
    handle.write(start)
name = os.path.basename(cmd[0])
if name == "test" and "-r" in cmd and target == "cmp-arm":
    j = cmd.index("-r") + 1
    if j < len(cmd) and os.path.basename(os.path.normpath(cmd[j])) == "cmp-private":
        sys.exit(0 if CFG["privateReadable"] else 1)
env.pop("FAKE_SUDO_ROOT", None)
env.update(SUDO_USER=CFG["boxUser"], SUDO_UID=CFG["boxUid"], SUDO_COMMAND=" ".join(cmd), HOME="/nonexistent-fake-sudo-home", FAKE_SUDO_USER=target)
os.execvpe(cmd[0], cmd, env)
`,
  account: String.raw`
tool = os.path.basename(sys.argv[0])
a = sys.argv[1:]
log(tool)
known = users()
def known_name(name):
    return not name.startswith("cmp-") or name in known
if tool in ("chown", "chgrp"):
    spec = next((x for x in a if not x.startswith("-")), "")
    owner = spec.split(":", 1)[0] if tool == "chown" else ""
    group = (spec.split(":", 1)[1] if ":" in spec else "") if tool == "chown" else spec
    if not all(known_name(n) for n in (owner, group) if n):
        sys.stderr.write(tool + ": invalid user or group: " + spec + "\n")
        sys.exit(1)
    if not is_root() and (owner not in ("", CFG["boxUser"], CFG["boxUid"]) or group.startswith("cmp-") or group == "root"):
        sys.stderr.write(tool + ": Operation not permitted\n")
        sys.exit(1)
    if CFG["failChown"] and tool == "chown" and owner in (CFG["boxUser"], CFG["boxUid"]):
        paths = [os.path.abspath(x).rstrip("/") for x in a if not x.startswith("-")][1:]
        if any("/comparison-work/i" in p and (p.endswith("/out") or p.endswith("/run")) for p in paths):
            sys.stderr.write("chown: changing ownership: Operation not permitted (fixture)\n")
            sys.exit(1)
    sys.exit(0)
if tool in ("useradd", "adduser"):
    if not is_root():
        sys.stderr.write(tool + ": Permission denied\n")
        sys.exit(1)
    if a[-1] in known:
        sys.stderr.write(tool + ": user exists\n")
        sys.exit(9)
    save_users(known + [a[-1]])
    sys.exit(0)
if tool in ("usermod", "groupadd", "gpasswd", "addgroup"):
    sys.exit(0 if is_root() else 1)
if tool == "install":
    rest, j = [], 0
    while j < len(a):
        if a[j] in ("-o", "-g", "--owner", "--group"):
            j += 2
            continue
        if a[j].startswith("--owner=") or a[j].startswith("--group="):
            j += 1
            continue
        rest.append(a[j])
        j += 1
    real("install", rest)
sys.exit(0)
`,
  rules: String.raw`
tool = os.path.basename(sys.argv[0])
a = [x for x in sys.argv[1:] if x not in ("-w", "--wait")]
log(tool)
if not is_root():
    sys.stderr.write(tool + ": Permission denied (you must be root)\n")
    sys.exit(4)
table = "filter"
rest = []
j = 0
while j < len(a):
    if a[j] in ("-t", "--table") and j + 1 < len(a):
        table = a[j + 1]
        j += 2
        continue
    rest.append(a[j])
    j += 1
longs = {"--append": "-A", "--insert": "-I", "--check": "-C", "--delete": "-D", "--list-rules": "-S", "--list": "-L"}
rest = [longs.get(x, x) for x in rest]
store = os.path.join(CFG["state"], tool + ".json")
try:
    with open(store) as handle:
        rules = json.load(handle)
except OSError:
    rules = []
op = next((x for x in rest if x in ("-A", "-I", "-C", "-D", "-S", "-L")), None)
if op is None:
    sys.exit(0)
k = rest.index(op)
spec = rest[k + 1:]
if op == "-I" and len(spec) > 1 and spec[1].isdigit():
    spec = spec[:1] + spec[2:]
key = json.dumps([table] + spec)
if op in ("-A", "-I"):
    if not CFG["brokenRules"].get(tool) and key not in rules:
        rules.append(key)
        with open(store, "w") as handle:
            json.dump(rules, handle)
    sys.exit(0)
if op == "-C":
    if key in rules:
        sys.exit(0)
    sys.stderr.write(tool + ": Bad rule (does a matching rule exist in that chain?).\n")
    sys.exit(1)
if op == "-D":
    if key in rules:
        rules.remove(key)
        with open(store, "w") as handle:
            json.dump(rules, handle)
        sys.exit(0)
    sys.exit(1)
for rule in rules:
    print(" ".join(json.loads(rule)))
sys.exit(0)
`,
  procs: String.raw`
tool = os.path.basename(sys.argv[0])
a = sys.argv[1:]
log(tool)
target = None
for j, x in enumerate(a):
    if x == "-u" and j + 1 < len(a):
        target = a[j + 1]
    elif x.startswith("-u") and len(x) > 2:
        target = x[2:]
if target not in UIDS:
    real(tool)
def stat(pid):
    try:
        with open("/proc/%d/stat" % pid) as handle:
            rest = handle.read().rsplit(")", 1)[1].split()
        return rest[0], int(rest[1]), rest[19]
    except (OSError, ValueError, IndexError):
        return None
def alive():
    directory = os.path.join(CFG["state"], "procs-" + target)
    roots = []
    for name in (os.listdir(directory) if os.path.isdir(directory) else []):
        s = stat(int(name))
        try:
            with open(os.path.join(directory, name)) as handle:
                start = handle.read()
        except OSError:
            continue
        if s and s[2] == start and s[0] != "Z":
            roots.append(int(name))
    children = {}
    for name in os.listdir("/proc"):
        if name.isdigit():
            s = stat(int(name))
            if s and s[0] != "Z":
                children.setdefault(s[1], []).append(int(name))
    found, todo = [], list(roots)
    while todo:
        pid = todo.pop()
        if pid in found:
            continue
        found.append(pid)
        todo += children.get(pid, [])
    return found
if tool == "pgrep":
    if CFG["stuck"] == target:
        print(4242)
        sys.exit(0)
    pids = alive()
    for pid in pids:
        print(pid)
    sys.exit(0 if pids else 1)
if not is_root():
    sys.stderr.write("pkill: killing processes of " + target + " failed: Operation not permitted\n")
    sys.exit(1)
pids = alive()
for pid in pids:
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        pass
sys.exit(0 if pids else 1)
`,
  find: String.raw`
a = sys.argv[1:]
log("find")
if "-writable" in a and a[:1] == ["/"]:
    end = "\0" if "-print0" in a else "\n"
    for directory in CFG["writable"].get(os.environ.get("FAKE_SUDO_USER") or "", []):
        sys.stdout.write(directory + end)
    sys.exit(0)
if "-user" in a:
    j = a.index("-user")
    if j + 1 < len(a) and a[j + 1] in CFG["marks"]:
        if "-delete" in a and not is_root():
            sys.stderr.write("find: cannot delete: Permission denied\n")
            sys.exit(1)
        a = a[:j] + ["-name", CFG["marks"][a[j + 1]] + "*"] + a[j + 2:]
real("find", a)
`,
  'nvidia-smi': String.raw`
a = sys.argv[1:]
query = next((x.split("=", 1)[1] for x in a if x.startswith("--query-gpu=")), None)
if query is None or "utilization.gpu" not in query:
    log("nvidia-smi")
gpus = CFG["gpus"]
if a == ["-L"]:
    for j in range(CFG["gpuLines"].get(os.environ.get("FAKE_SUDO_USER") or "", len(gpus))):
        print("GPU %d: %s (UUID: %s)" % (j, gpus[j % len(gpus)]["name"], gpus[j % len(gpus)]["uuid"]))
    sys.exit(0)
if query is not None:
    fmt = next((x.split("=", 1)[1] for x in a if x.startswith("--format=")), "csv")
    fields = query.split(",")
    for field in fields:
        if field not in gpus[0]:
            sys.stderr.write('Field "%s" is not a valid field to query.\n' % field)
            sys.exit(2)
    if "noheader" not in fmt:
        print(", ".join(fields))
    for gpu in gpus:
        values = []
        for field in fields:
            value = gpu[field]
            if field == "utilization.gpu":
                value = "[N/A]" if CFG["utilNA"] else (value if "nounits" in fmt else value + " %")
            if field == "memory.total" and "nounits" not in fmt:
                value += " MiB"
            values.append(value)
        print(", ".join(values))
    sys.exit(0)
if "-q" in a or "--query" in a:
    print("==============NVSMI LOG==============")
    print("Driver Version                            : " + CFG["driver"])
    print("CUDA Version                              : " + CFG["cuda"])
    print("Attached GPUs                             : %d" % len(gpus))
    sys.exit(0)
print("+-----------------------------------------------------------------------------------------+")
print("| NVIDIA-SMI %s              Driver Version: %s      CUDA Version: %s     |" % (CFG["driver"], CFG["driver"], CFG["cuda"]))
print("|-----------------------------------------+------------------------+----------------------+")
for gpu in gpus:
    print("|   %s  %s                 On  |   00000000:00:0%s.0 Off |                    0 |" % (gpu["index"], gpu["name"], gpu["index"]))
print("+-----------------------------------------------------------------------------------------+")
`,
  lscpu: String.raw`
a = sys.argv[1:]
log("lscpu")
fields = [("Architecture:", "x86_64"), ("CPU op-mode(s):", "32-bit, 64-bit"), ("Byte Order:", "Little Endian"),
          ("CPU(s):", str(CFG["cpuCount"])), ("On-line CPU(s) list:", "0-%d" % (CFG["cpuCount"] - 1)),
          ("Vendor ID:", "FakeVendor"), ("Model name:", CFG["cpuModel"]), ("Thread(s) per core:", "2"),
          ("Core(s) per socket:", str(CFG["cpuCount"] // 2)), ("Socket(s):", "1")]
if "-J" in a or "--json" in a:
    print(json.dumps({"lscpu": [dict(field=f, data=d) for f, d in fields]}))
    sys.exit(0)
if any(x.startswith("-p") or x.startswith("--parse") or x.startswith("-e") or x.startswith("--extended") for x in a):
    print("# CPU")
    for j in range(CFG["cpuCount"]):
        print(j)
    sys.exit(0)
for f, d in fields:
    print("%-33s %s" % (f, d))
`,
  ldd: String.raw`
a = [x for x in sys.argv[1:] if not x.startswith("-")]
log("ldd")
if len(a) == 1:
    target = os.path.realpath(a[0])
    if target.startswith(CFG["caseDir"] + "/"):
        base = os.path.basename(target)
        shared = os.path.dirname(os.path.dirname(target))
        if base == "solver-1.0":
            print("\tlinux-vdso.so.1 (0x00007ffd4b3f2000)")
            print("\tlibfake.so.1 => %s/lib/libfake.so.1 (0x00007f1a2b000000)" % shared)
            print("\tlibalias.so.2 => %s/lib/libalias.so.2 (0x00007f1a2a000000)" % shared)
            print("\tlibmissing.so.3 => not found")
            print("\t/lib64/ld-linux-x86-64.so.2 (0x00007f1a2c000000)")
            sys.exit(0)
        if base == "scorer":
            print("\tstatically linked")
            sys.exit(0)
        sys.stderr.write("\tnot a dynamic executable\n")
        sys.exit(1)
real("ldd")
`,
  id: String.raw`
a = sys.argv[1:]
names = [x for x in a if not x.startswith("-")]
if names and names[-1] in UIDS:
    log("id")
    name = names[-1]
    if name not in users():
        sys.stderr.write("id: '%s': no such user\n" % name)
        sys.exit(1)
    uid = UIDS[name]
    flags = "".join(x.lstrip("-") for x in a if x.startswith("-"))
    if "n" in flags and ("u" in flags or "g" in flags or "G" in flags):
        print(name)
    elif "u" in flags or "g" in flags or "G" in flags:
        print(uid)
    else:
        print("uid=%d(%s) gid=%d(%s) groups=%d(%s)" % (uid, name, uid, name, uid, name))
    sys.exit(0)
real("id")
`,
  getent: String.raw`
a = sys.argv[1:]
if len(a) >= 2 and a[0] in ("passwd", "group") and a[1] in UIDS:
    log("getent")
    if a[1] not in users():
        sys.exit(2)
    uid = UIDS[a[1]]
    print("%s:x:%d:%d::/nonexistent:/usr/sbin/nologin" % (a[1], uid, uid) if a[0] == "passwd" else "%s:x:%d:" % (a[1], uid))
    sys.exit(0)
real("getent")
`,
  // System V IPC: ipcmk creates an object owned by the calling (part) user in the fixture's table; ipcs lists the
  // table in util-linux's format (with -c as creators/owners); ipcrm removes by id, key or --all, as root or as
  // the object's owner, and logs what it removed.
  ipc: String.raw`
tool = os.path.basename(sys.argv[0])
a = sys.argv[1:]
store = os.path.join(CFG["state"], "ipc.json")
try:
    with open(store) as handle:
        objects = json.load(handle)
except OSError:
    objects = []
def save():
    tmp = store + ".%d" % os.getpid()
    with open(tmp, "w") as handle:
        json.dump(objects, handle)
    os.replace(tmp, store)
def part_user():
    # A part runs under env -i, which drops FAKE_SUDO_USER: its user is the one whose sudo process is an ancestor.
    starts = {}
    for target in UIDS:
        directory = os.path.join(CFG["state"], "procs-" + target)
        for name in (os.listdir(directory) if os.path.isdir(directory) else []):
            try:
                with open(os.path.join(directory, name)) as handle:
                    starts[int(name)] = (target, handle.read())
            except (OSError, ValueError):
                pass
    pid = os.getpid()
    while pid > 1:
        try:
            with open("/proc/%d/stat" % pid) as handle:
                rest = handle.read().rsplit(")", 1)[1].split()
        except OSError:
            return None
        if pid in starts and starts[pid][1] == rest[19]:
            return starts[pid][0]
        pid = int(rest[1])
    return None
me = os.environ.get("FAKE_SUDO_USER") or ("root" if is_root() else (part_user() or CFG["boxUser"]))
live = [o for o in objects if not o["removed"]]
if tool == "ipcmk":
    kind = "m" if ("-M" in a or "--shmem" in a) else "q" if ("-Q" in a or "--queue" in a) else "s"
    ident = 32768 + len(objects)
    key = "0x%08x" % (0x51ab0000 + len(objects))
    objects.append(dict(kind=kind, id=ident, key=key, owner=me, removed=False))
    save()
    log("ipcmk", id=ident, owner=me)
    print({"m": "Shared memory id: %d", "q": "Message queue id: %d", "s": "Semaphore id: %d"}[kind] % ident)
    sys.exit(0)
if tool == "ipcs":
    log("ipcs")
    kinds = [k for k, flags in (("m", ("-m", "--shmems")), ("q", ("-q", "--queues")), ("s", ("-s", "--semaphores"))) if any(f in a for f in flags)] or ["m", "q", "s"]
    creators = "-c" in a or "--creator" in a
    titles = {"m": "Shared Memory Segments", "q": "Message Queues", "s": "Semaphore Arrays"}
    names = {"m": "shmid", "q": "msqid", "s": "semid"}
    for k in ["q", "m", "s"]:
        if k not in kinds:
            continue
        rows = [o for o in live if o["kind"] == k]
        print("")
        if creators:
            print("------ %s Creators/Owners --------" % {"m": "Shared Memory Segment", "q": "Message Queues", "s": "Semaphore Arrays"}[k])
            print("%-10s %-10s %-10s %-10s %-10s %-10s" % (names[k], "perms", "cuid", "cgid", "uid", "gid"))
            for o in rows:
                print("%-10d %-10s %-10s %-10s %-10s %-10s" % (o["id"], "600", o["owner"], o["owner"], o["owner"], o["owner"]))
        else:
            print("------ %s --------" % titles[k])
            extra = {"m": "bytes      nattch     status", "q": "used-bytes   messages", "s": "nsems"}[k]
            print("%-10s %-10s %-10s %-10s %s" % ("key", names[k], "owner", "perms", extra))
            for o in rows:
                tail = {"m": "4096       0", "q": "0            0", "s": "1"}[k]
                print("%-10s %-10d %-10s %-10s %s" % (o["key"], o["id"], o["owner"], "600", tail))
        print("")
    sys.exit(0)
# ipcrm
removed, failed, j = [], False, 0
def drop(match):
    global failed
    hit = [o for o in live if match(o) and not o["removed"]]
    for o in hit:
        if is_root() or o["owner"] == me:
            o["removed"] = True
            removed.append(o["id"])
        else:
            failed = True
    if not hit:
        failed = True
idflags = {"-m": "m", "--shmem-id": "m", "-q": "q", "--queue-id": "q", "-s": "s", "--semaphore-id": "s"}
keyflags = {"-M": "m", "--shmem-key": "m", "-Q": "q", "--queue-key": "q", "-S": "s", "--semaphore-key": "s"}
while j < len(a):
    x, value = a[j], None
    if "=" in x and x.startswith("--"):
        x, value = x.split("=", 1)
    if x in idflags or x in keyflags:
        if value is None:
            j += 1
            value = a[j] if j < len(a) else ""
        kind = idflags.get(x) or keyflags.get(x)
        if x in idflags:
            drop(lambda o: o["kind"] == kind and str(o["id"]) == value)
        else:
            drop(lambda o: o["kind"] == kind and o["key"].lower() == value.lower())
    elif x in ("-a", "--all"):
        want = {"shm": "m", "msg": "q", "sem": "s"}.get(value or "", None)
        for o in live:
            if (want is None or o["kind"] == want) and (is_root() or o["owner"] == me) and not o["removed"]:
                o["removed"] = True
                removed.append(o["id"])
    elif x in ("shm", "msg", "sem") and j + 1 < len(a):
        kind = {"shm": "m", "msg": "q", "sem": "s"}[x]
        for value in a[j + 1:]:
            drop(lambda o: o["kind"] == kind and str(o["id"]) == value)
        break
    j += 1
save()
log("ipcrm", removed=removed)
sys.exit(1 if failed else 0)
`,
}
// The user database for Python programs on the box (no -I): pwd and grp also know cmp-arm and cmp-eval once created.
const SITECUSTOMIZE = String.raw`import grp, json, pwd
_USERS = USERS_JSON
_UIDS = {"cmp-arm": 64901, "cmp-eval": 64902}
def _known():
    try:
        with open(_USERS) as handle:
            return json.load(handle)
    except OSError:
        return []
_getpwnam, _getpwuid, _getgrnam, _getgrgid = pwd.getpwnam, pwd.getpwuid, grp.getgrnam, grp.getgrgid
def _pw(name):
    return pwd.struct_passwd((name, "x", _UIDS[name], _UIDS[name], "", "/nonexistent", "/usr/sbin/nologin"))
def getpwnam(name):
    if name in _UIDS and name in _known():
        return _pw(name)
    return _getpwnam(name)
def getpwuid(uid):
    for name, value in _UIDS.items():
        if uid == value and name in _known():
            return _pw(name)
    return _getpwuid(uid)
def getgrnam(name):
    if name in _UIDS and name in _known():
        return grp.struct_group((name, "x", _UIDS[name], []))
    return _getgrnam(name)
def getgrgid(gid):
    for name, value in _UIDS.items():
        if gid == value and name in _known():
            return grp.struct_group((name, "x", value, []))
    return _getgrgid(gid)
pwd.getpwnam, pwd.getpwuid, grp.getgrnam, grp.getgrgid = getpwnam, getpwuid, getgrnam, getgrgid
`
const FAKE_FILES = { sudo: 'sudo', 'nvidia-smi': 'nvidia-smi', iptables: 'rules', ip6tables: 'rules', pkill: 'procs', pgrep: 'procs',
  lscpu: 'lscpu', ldd: 'ldd', find: 'find', id: 'id', getent: 'getent', ipcrm: 'ipc', ipcs: 'ipc', ipcmk: 'ipc',
  chown: 'account', chgrp: 'account', useradd: 'account', adduser: 'account', usermod: 'account', groupadd: 'account', gpasswd: 'account', install: 'account' }

// ---- Programs and harness scripts on the box ------------------------------------------------------------------
// The published program of the fixture. It records its arguments, environment, working directory and standard
// output/error targets in out/solver-<rec>.json, then behaves as --mode says.
const SOLVER = String.raw`#!/usr/bin/env bash
set -u
fd1=$(readlink /proc/$$/fd/1)
fd2=$(readlink /proc/$$/fd/2)
FAKE_FD1=$fd1 FAKE_FD2=$fd2 python3 -c 'import json, os, sys
argv = sys.argv[1:]
rec = argv[argv.index("--rec") + 1] if "--rec" in argv else "x"
env = {k: v for k, v in os.environ.items() if not k.startswith("FAKE_FD")}
row = dict(argv=argv, env=env, cwd=os.getcwd(), fd1=os.environ["FAKE_FD1"], fd2=os.environ["FAKE_FD2"])
with open(os.path.join(os.environ["CMP_OUT"], "solver-" + rec + ".json"), "w") as handle:
    json.dump(row, handle)' "$@"
rec=x mode=ok out=/dev/null cs=none
while [[ $# -gt 0 ]]; do
  case $1 in
    --rec) rec=$2; shift;;
    --mode) mode=$2; shift;;
    --out) out=$2; shift;;
    --case) cs=$2; shift;;
  esac
  shift
done
printf 'solver-out %s\n' "$rec"
printf 'solver-err %s\n' "$rec" >&2
case $mode in
  fail) exit 3;;
  sleep) sleep 120; exit 0;;
esac
printf 'result for %s\n' "$cs" > "$out"
if [[ $rec == one ]]; then
  printf 'wide\n' > "$CMP_OUT/wide.txt"
  chmod 666 "$CMP_OUT/wide.txt"
  mkdir -p "$CMP_OUT/closed"
  printf 'inner\n' > "$CMP_OUT/closed/inner.txt"
  chmod 600 "$CMP_OUT/closed/inner.txt"
  chmod 700 "$CMP_OUT/closed"
fi
case $mode in
  symlink) ln -s /etc/hostname "$CMP_OUT/link";;
  hidelink) mkdir -p "$CMP_OUT/hid"; ln -s /etc/hostname "$CMP_OUT/hid/link"; chmod 000 "$CMP_OUT/hid";;
  hideout) ln -s /etc/hostname "$CMP_OUT/hlink"; chmod 000 "$CMP_OUT";;
  evalfail) printf x > "$CMP_OUT/evalfail";;
  evalsleep) printf x > "$CMP_OUT/evalsleep";;
esac
exit 0
`
const ADAPTER_PY = String.raw`import json, os
S = os.path.dirname(os.path.realpath("harness"))
inv = os.path.dirname(os.getcwd())
out = os.environ["CMP_OUT"]
def mode(p):
    return format(os.stat(p).st_mode & 0o7777, "o")
def names(p):
    return sorted(os.listdir(p)) if os.path.isdir(p) else None
run = {n: (os.readlink(n) if os.path.islink(n) else "notlink") for n in os.listdir(".")}
row = dict(env={k: v for k, v in os.environ.items() if not k.startswith("FAKE_FD")}, cwd=os.getcwd(), S=S, inv=inv,
    fd1=os.environ["FAKE_FD1"], fd2=os.environ["FAKE_FD2"], invList=names(inv), invMode=mode(inv),
    logMode=mode(os.path.join(inv, "log")), outList=names(out), evalList=names(os.path.join(inv, "eval")),
    homeList=names(os.environ.get("HOME", "/nonexistent")), ehomeList=names(os.path.join(inv, "ehome")), run=run, shared=names(S),
    boxFiles={n: mode(os.path.join(S, n)) for n in os.listdir(S) if os.path.isfile(os.path.join(S, n)) and not os.path.islink(os.path.join(S, n))})
with open(os.path.join(out, "adapter.json"), "w") as handle:
    json.dump(row, handle)`
// Adapter mode useleft: sleep until 0.6 s before the invocation's left_s runs out, counted from the creation of
// run/'s links (right after the wrapper starts), so that the arm part ends ok with less than 1 s left.
const USELEFT_PY = String.raw`import json, os, time
inv = os.path.dirname(os.getcwd())
S = os.path.dirname(os.path.realpath("harness"))
with open(os.path.join(S, "comparison-jobs", os.path.basename(inv) + ".json")) as handle:
    job = json.load(handle)
end = os.lstat("harness").st_mtime + job["left_s"] - 0.6
time.sleep(max(0.0, end - time.time()))`
const EVAL_PY = String.raw`import json, os
def ancestors():
    found, pid = [], os.getppid()
    while pid > 1 and len(found) < 12:
        try:
            with open("/proc/%d/cmdline" % pid, "rb") as handle:
                cmd = [part.decode("utf-8", "replace") for part in handle.read().split(b"\0") if part]
            with open("/proc/%d/stat" % pid) as handle:
                parent = int(handle.read().rsplit(")", 1)[1].split()[1])
        except (OSError, ValueError):
            break
        if any("idea/wf.js" in part for part in cmd):
            break
        found.append(cmd)
        pid = parent
    return found
P = os.environ.get("CMP_PRIVATE", "")
private = {}
for top, dirs, files in os.walk(P):
    for name in dirs + files:
        p = os.path.join(top, name)
        st = os.lstat(p)
        kind = "link" if os.path.islink(p) else "dir" if os.path.isdir(p) else "file"
        private[os.path.relpath(p, P)] = [format(st.st_mode & 0o7777, "o"), kind]
row = dict(env={k: v for k, v in os.environ.items() if not k.startswith("FAKE_FD")}, cwd=os.getcwd(), ancestors=ancestors(),
    private=private, privateMode=format(os.stat(P).st_mode & 0o7777, "o") if os.path.isdir(P) else None,
    armOut=sorted(os.listdir(os.environ["CMP_ARM_OUT"])), evalList=sorted(os.listdir(os.environ["CMP_EVAL_OUT"])),
    homeList=sorted(os.listdir(os.environ["HOME"])) if os.path.isdir(os.environ.get("HOME", "")) else None,
    fd1=os.environ["FAKE_FD1"], fd2=os.environ["FAKE_FD2"])
with open(os.path.join(os.environ["CMP_EVAL_OUT"], "eval-record.json"), "w") as handle:
    json.dump(row, handle)`
const FETCH_PY = String.raw`import json, os, sys
home = os.environ.get("HOME", "")
row = dict(env=dict(os.environ), cwd=os.getcwd(), homeList=sorted(os.listdir(home)) if os.path.isdir(home) else None)
with open(sys.argv[1], "w") as handle:
    json.dump(row, handle)`
const RECORD = 'fd1=$(readlink /proc/$$/fd/1)\nfd2=$(readlink /proc/$$/fd/2)\n'
const SETUP_BASE = String.raw`mkdir -p out baseline-published data bin lib
printf 'published\n' > baseline-published/pin
printf 'input\n' > data/input
printf 'fake library one\n' > lib/libfake.so.1
printf 'fake library alias target\n' > lib/libfake.so.1.0
ln -sfn libfake.so.1.0 lib/libalias.so.2
printf 'wide\n' > data/wide.txt
chmod 666 data/wide.txt
printf 'tool\n' > data/tool.sh
chmod 744 data/tool.sh
mkdir -p data/closed data/groupw
printf 'closed inner\n' > data/closed/inner.txt
chmod 600 data/closed/inner.txt
chmod 700 data/closed
chmod 775 data/groupw`
const program = (file, text) => `printf %s ${q(Buffer.from(text).toString('base64'))} | base64 -d > ${file}\nchmod 755 ${file}`
const COMMAND_OK = 'test -f baseline-published/pin\nmkdir -p out\nprintf \'command ran\\n\' >> out/command-calls.log'
const ANCHORS_OK = 'bash harness/run_command.sh\nprintf \'%s\\n\' \'{"first":100,"second":0}\' > out/anchors_measured.json'

// ---- Designs -----------------------------------------------------------------------------------------------
const WALL = { name: 'wall', unit: 's', what: 'invocation wall', source: 'trusted_wall', reduce: null, expect_count: null }
const RES = { name: 'res', what: 'result file', format: 'bytes', select: null }
const solverCommand = (mode, extra = []) => ['bin/solver', '--rec', 'one', '--mode', mode, '--case', '{spec:/case}', ...extra, '--out', '{out}/result.txt']
const MAIN = {
  arms: [
    { id: 'A0', what: 'published baseline', commands: [solverCommand('{spec:/a0}', ['--n', '{spec:/n}'])], env: null },
    { id: 'A1', what: 'published alternative', commands: [
      solverCommand('{spec:/a1}', ['--tag', '{spec:/a~1b}', '--tiny', '{spec:/tiny}', '--big', '{spec:/big}', '--second', '{spec:/list/1}',
        '--input', '{input}', '--run', '{run}', '--lit', 'x{{y}}z']),
      ['bash', 'bin/solver', '--rec', 'two', '--mode', 'ok', '--case', '{spec:/case}', '--out', '{out}/second.txt']],
    env: { OMP_NUM_THREADS: '4', CASE_DIR: '{run}/cases/{input}', N_STR: 'n={spec:/n}', LIT: '{{x}}' } },
  ],
  inputs: [
    { id: 'case-1', spec: { case: 'alpha', n: 10, 'a/b': 'x', tiny: 1e-7, big: 1e21, list: [1, 2], a0: 'ok', a1: 'ok' } },
    { id: 'case_2.b', spec: { case: 'beta', n: 2.5, 'a/b': 'y', tiny: 0.5, big: -3, list: [3, 4.5], a0: 'evalfail', a1: 'fail' } },
    { id: 'case-3', spec: { case: 'gamma', n: 1, 'a/b': 'z', tiny: 7, big: 8, list: [0, 9], a0: 'symlink', a1: 'sleep' } },
    { id: 'case-4', spec: { case: 'delta', n: 4, 'a/b': 'w', tiny: 5, big: 6, list: [0, 1], a0: 'evalsleep', a1: 'adapterfail' } },
  ],
  outputs: [RES], metrics: [WALL],
  evaluator: { what: 'published scorer', spec: { program: 'scorer', pin: 'v2' }, timeout_s: 5 },
  replicates: 1, warmup: 1, order_seed: 4242,
  timeout_s: { A0: 99999, A1: { 'case-1': 600, 'case_2.b': 600, 'case-3': 4, 'case-4': 600 } },
  budget_s: 3000, bootstrap_seed: 1, bootstrap_resamples: 1000,
  comparisons: [{ id: 'K1', arm: 'A1', against: 'A0', measure: { output: 'res', comparator: 'exact' }, criterion: 'agreement', direction: 'two_sided',
    unit: 'per_input_each', pairing: 'paired_replicate', rule: 'all_pairs', confidence: null, margin: null, threshold: null, strict: null,
    reference: null, missing: 'void', given: [], parts: ['main'] }],
}
// The status each (arm, input) of MAIN must end with (SCHEMAS.md wrapper step 4).
const MAIN_EXPECT = {
  'A0|case-1': { status: 'ok', adapter_rc: 0, rcs: [0], eval: 'ok', eval_rc: 0 },
  'A1|case-1': { status: 'ok', adapter_rc: 0, rcs: [0, 0], eval: 'ok', eval_rc: 0 },
  'A0|case_2.b': { status: 'ok', adapter_rc: 0, rcs: [0], eval: 'failed', eval_rc: 4 },
  'A1|case_2.b': { status: 'failed', adapter_rc: 0, rcs: [3], eval: 'skipped', eval_rc: null },
  'A0|case-3': { status: 'invalid', adapter_rc: 0, rcs: [0], eval: 'skipped', eval_rc: null },
  'A1|case-3': { status: 'timeout', adapter_rc: 0, rcs: [null], eval: 'skipped', eval_rc: null },
  'A0|case-4': { status: 'ok', adapter_rc: 0, rcs: [0], eval: 'timeout', eval_rc: null },
  'A1|case-4': { status: 'failed', adapter_rc: 5, rcs: [], eval: 'skipped', eval_rc: null },
}
const simpleArms = ids => ids.map(id => ({ id, what: `arm ${id}`, commands: [solverCommand('{spec:/' + id.toLowerCase() + '}')], env: null }))
const NOEVAL = {
  arms: simpleArms(['A0', 'A1', 'A2']).map(arm => arm.id === 'A1' ? { ...arm, env: { X_ARM_INPUT: '{input}' } } : arm),
  inputs: [{ id: 'only', spec: { case: 'solo', a0: 'ok', a1: 'ok', a2: 'ok' } }],
  outputs: [RES], metrics: [WALL], evaluator: null, replicates: 2, warmup: 2, order_seed: -7,
  timeout_s: { A0: 600, A1: 5000, A2: { only: 7 } }, budget_s: 900, bootstrap_seed: 0, bootstrap_resamples: 1000, comparisons: [],
}
const BUDGET = {
  arms: simpleArms(['A0', 'A1']), inputs: [{ id: 'x', spec: { case: 'k', a0: 'ok', a1: 'sleep' } }],
  outputs: [RES], metrics: [WALL], evaluator: null, replicates: 3, warmup: 0, order_seed: null /* chosen below */,
  timeout_s: null, budget_s: 45, bootstrap_seed: 0, bootstrap_resamples: 1000, comparisons: [],
}
const SMALL = {
  arms: simpleArms(['A0', 'A1']), inputs: [{ id: 'x', spec: { case: 'k', a0: 'ok', a1: 'ok' } }],
  outputs: [RES], metrics: [WALL], evaluator: { what: 'published scorer', spec: { program: 'scorer' }, timeout_s: null },
  replicates: 2, warmup: 0, order_seed: 3, timeout_s: 600, budget_s: 40, bootstrap_seed: 0, bootstrap_resamples: 1000, comparisons: [],
}

// Python's json.dumps of a finite number, for the numbers of these designs.
const pyNumber = value => Number.isInteger(value) && Math.abs(value) < 1e16 ? String(value) : String(value).replace(/e([+-])(\d)$/, 'e$10$2')
function pointer(spec, text) {
  let value = spec
  for (const raw of text.split('/').slice(1)) value = value[raw.replace(/~1/g, '/').replace(/~0/g, '~')]
  return value
}
function substitute(text, { input, spec, run, out }) {
  return text.replace(/\{\{|\}\}|\{([^{}]*)\}/g, (match, name) => {
    if (match === '{{') return '{'
    if (match === '}}') return '}'
    if (name === 'input') return input
    if (name === 'run') return run
    if (name === 'out') return out
    const value = pointer(spec, name.slice('spec:'.length))
    return typeof value === 'string' ? value : pyNumber(value)
  })
}
// The scheduled order: warmup rounds, then replicate rounds; each round shuffles the (arm, input) pairs, arm-major,
// with one random.Random(order_seed) stream. Rounds are numbered from 1 within their kind (w1.., r1..), the
// convention tools/test_m5_comparison_score.py fixes for the fetched round folders.
function python(code, arg) {
  const result = spawnSync('python3', ['-I', '-c', code, JSON.stringify(arg)], { encoding: 'utf8' })
  if (result.status !== 0) throw new Error(`python oracle failed: ${result.stderr}`)
  return JSON.parse(result.stdout)
}
const ORDER_PY = String.raw`import json, random, sys
a = json.loads(sys.argv[1])
rng = random.Random(a["seed"])
pairs = [(arm, inp) for arm in a["arms"] for inp in a["inputs"]]
out = []
for r in range(a["warmup"] + a["replicates"]):
    p = list(pairs)
    rng.shuffle(p)
    warm = r < a["warmup"]
    out += [dict(arm=x, input=y, mode="warmup" if warm else "replicate", round=r + 1 if warm else r - a["warmup"] + 1) for x, y in p]
print(json.dumps(out))`
const scheduled = design => python(ORDER_PY, { seed: design.order_seed, arms: design.arms.map(arm => arm.id), inputs: design.inputs.map(item => item.id), warmup: design.warmup, replicates: design.replicates })
// BUDGET: a seed whose first round runs A0 before A1, so that A1's sleeping invocation uses up the budget second.
BUDGET.order_seed = python(String.raw`import random
for s in range(1000):
    p = [("A0", "x"), ("A1", "x")]
    random.Random(s).shuffle(p)
    if p[0][0] == "A0":
        print(s)
        break`, null)
// Time left (SCHEMAS.md Timeouts): with an evaluator and no timeouts, A0 runs first. LEFT_SKIP: A0's adapter sleeps
// until 0.6 s before left_s runs out, so the evaluator part has less than 1 s. LEFT_CAP: A0's adapter sleeps 5 s and
// its evaluator part would sleep 120 s, beyond left_s.
const EVALUATOR_UNCAPPED = { what: 'published scorer', spec: { program: 'scorer' }, timeout_s: null }
const LEFT_SKIP = { ...BUDGET, evaluator: EVALUATOR_UNCAPPED, replicates: 1, inputs: [{ id: 'x', spec: { case: 'k', a0: 'ok', a1: 'ok', adapter_a0: 'useleft' } }] }
const LEFT_CAP = { ...BUDGET, evaluator: EVALUATOR_UNCAPPED, replicates: 1, inputs: [{ id: 'x', spec: { case: 'k', a0: 'evalsleep', a1: 'ok', adapter_a0: 'sleep5' } }] }
// Wrapper step 2: A0 leaves a symbolic link in an unreadable subdirectory of out/, A1 one in an unreadable out/.
const HIDE = { ...SMALL, replicates: 1, budget_s: 120, inputs: [{ id: 'x', spec: { case: 'k', a0: 'hidelink', a1: 'hideout' } }] }
// wrap.json validity: each input's fetched wrap.json (both arms) is replaced by a record the contract says is
// invalid, except f-valid's, a valid record whose values must reach the compute file and the scorer.
const FORGED = {
  arms: simpleArms(['A0', 'A1']), outputs: [RES], metrics: [WALL], evaluator: EVALUATOR_UNCAPPED,
  inputs: ['f-valid', 'f-okrc', 'f-empty', 'f-negwall', 'f-nanwall', 'f-infwall', 'f-rowmissing', 'f-rowextra', 'f-evalrc']
    .map(id => ({ id, spec: { case: 'k', a0: 'ok', a1: 'ok' } })),
  replicates: 1, warmup: 0, order_seed: 11, timeout_s: 600, budget_s: 900, bootstrap_seed: 0, bootstrap_resamples: 1000,
  comparisons: [{ id: 'K1', arm: 'A1', against: 'A0', measure: { metric: 'wall' }, criterion: 'non_inferiority', direction: 'lower_better',
    unit: 'per_input_each', pairing: 'unpaired', rule: 'all_pairs', confidence: null, margin: null, threshold: null, strict: null,
    reference: null, missing: 'void', given: [], parts: ['main'] }],
}
const FORGERIES = (() => {
  const base = () => ({ status: 'ok', adapter_rc: 0, adapter_wall_s: 0.5,
    commands: [{ argv: ['bin/solver', '--mode', 'ok'], rc: 0, wall_s: 1.0, executable: '/usr/bin/true', sha256: '0'.repeat(64) }],
    gpu_busy_s: 1.0, gpu_busy_known: true, eval_status: 'ok', eval_rc: 0, eval_wall_s: 0.25, eval_gpu_busy_s: 0.5, eval_gpu_busy_known: true })
  const edit = change => { const value = base(); change(value); return JSON.stringify(value) + '\n' }
  return {
    'f-valid': edit(() => {}),
    'f-okrc': edit(value => { value.adapter_rc = 3 }),
    'f-empty': edit(value => { value.commands = [] }),
    'f-negwall': edit(value => { value.adapter_wall_s = -1 }),
    'f-nanwall': edit(() => {}).replace('"adapter_wall_s":0.5', '"adapter_wall_s":NaN'),
    'f-infwall': edit(() => {}).replace('"wall_s":1,', '"wall_s":1e999,'),
    'f-rowmissing': edit(value => { delete value.commands[0].sha256 }),
    'f-rowextra': edit(value => { value.commands[0].note = 'x' }),
    'f-evalrc': edit(value => { value.eval_rc = 2 }),
  }
})()

// ---- One workflow run -------------------------------------------------------------------------------------
const scratch = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), 'test_m5_comparison_evaluate_')))
const pipeline = path.join(scratch, 'pipeline')
const ONLY = process.argv[2] ? new RegExp(process.argv[2]) : null
const DEBUG = process.argv[3] === 'debug'
let checks = 0, failures = 0
function check(label, test) {
  if (ONLY && !ONLY.test(label)) return
  checks++
  try { test(); console.log(`ok ${label}`) }
  catch (error) { failures++; console.log(`FAIL ${label}: ${String(error.message).replace(/\s*\n\s*/g, ' ').slice(0, 1500)}`) }
}

// spec: { design (null: no args.comparison), boxName, ceiling, box ('none' | 'open' | 'refresh'), stub, usersExist,
// privateReadable, brokenRules, gpuLines, utilNA, stuck, setupExtra, fetchExtra, ipc (every adapter and evaluate.sh
// leave a System V shared-memory segment), failChown (chown of an invocation's run/ or out/ to the box user fails),
// forge (input id -> wrap.json text written over every fetched wrap.json of that input) }
async function execute(name, spec) {
  if (ONLY && !ONLY.test(name)) return null
  const caseDir = path.join(scratch, name)
  const root = path.join(caseDir, 'run'), agent = path.join(root, 'agent'), control = path.join(root, 'control')
  const box = path.join(caseDir, spec.boxName ?? 'box')
  const world = path.join(caseDir, 'world'), boxHome = path.join(caseDir, 'boxhome')
  const fake = path.join(caseDir, 'fake'), fakeBin = path.join(fake, 'bin'), state = path.join(fake, 'state')
  const source = path.join(caseDir, 'previous run', 'A', 'harness')
  const designFile = path.join(caseDir, 'science', 'design.json')
  for (const directory of [box, path.join(world, 'tmp', 'sub'), path.join(world, 'shm'), path.join(world, 'etmp'), boxHome, fakeBin, state, path.join(root, 'home'), source])
    fs.mkdirSync(directory, { recursive: true })
  const design = spec.design ?? null
  const evaluator = Boolean(design?.evaluator)
  const privateBytes = `PRIVATE-LABELS-${name}-7d1c0a\n`, privateSecond = `PRIVATE-SECOND-${name}-93be41\n`
  const writable = { 'cmp-arm': [path.join(world, 'tmp'), box, path.join(world, 'shm'), path.join(world, 'tmp', 'sub')], 'cmp-eval': [path.join(world, 'etmp'), path.join(world, 'tmp')] }
  const cfg = { log: path.join(fake, 'log.jsonl'), state, users: path.join(state, 'users.json'), real: REAL, boxUser: BOX_USER, boxUid: BOX_UID,
    privateReadable: Boolean(spec.privateReadable), brokenRules: spec.brokenRules ?? {}, gpuLines: spec.gpuLines ?? {}, utilNA: Boolean(spec.utilNA),
    stuck: spec.stuck ?? null, writable, marks: { 'cmp-arm': 'cmparm-', 'cmp-eval': 'cmpeval-' }, gpus: GPUS, driver: DRIVER, cuda: CUDA,
    cpuModel: CPU_MODEL, cpuCount: CPU_COUNT, caseDir, failChown: Boolean(spec.failChown) }
  if (spec.usersExist) fs.writeFileSync(cfg.users, JSON.stringify(['cmp-arm', 'cmp-eval']))
  for (const [tool, kind] of Object.entries(FAKE_FILES))
    writeFile(path.join(fakeBin, tool), PRELUDE.replace('CFG_JSON', () => JSON.stringify(JSON.stringify(cfg))) + FAKES[kind], 0o755)
  const fakePython = path.join(fake, 'python')
  writeFile(path.join(fakePython, 'sitecustomize.py'), SITECUSTOMIZE.replace('USERS_JSON', () => JSON.stringify(cfg.users)))

  // Harness (args.harness_from).
  const files = {
    'setup.sh': sh([SETUP_BASE, program('bin/solver-1.0', SOLVER), 'ln -sfn solver-1.0 bin/solver',
      program('bin/alt', sh('echo alt')), program('bin/scorer', sh('echo scorer')), ...(spec.setupExtra ? [spec.setupExtra({ privateBytes, privateSecond, world })] : [])].join('\n')),
    'run_command.sh': sh(COMMAND_OK), 'run_anchors.sh': sh(ANCHORS_OK),
  }
  if (design) {
    for (const arm of design.arms) {
      const key = arm.id.toLowerCase()
      // Separated users run for every comparison, so the arm part always leaves files for the cleanup.
      const worldWrites = [
        `touch ${q(box)}/cmparm-stray-$$ ${q(path.join(world, 'tmp'))}/cmparm-x-$$ ${q(path.join(world, 'tmp', 'sub'))}/cmparm-y-$$ ${q(path.join(world, 'shm'))}/cmparm-z-$$`,
        'touch data/cmparm-keep-$$ "$CMP_OUT/cmparm-out-$$"']
      files[`arms/${arm.id}.sh`] = '#!/usr/bin/env bash\nset -u\n' + RECORD + `FAKE_FD1=$fd1 FAKE_FD2=$fd2 python3 -c ${q(ADAPTER_PY)}\n` +
        `printf 'adapter-out %s\\n' ${arm.id}\nprintf 'adapter-err %s\\n' ${arm.id} >&2\nprintf '%s\\n' "$CMP_INPUT" > "$CMP_OUT/input.txt"\n` +
        worldWrites.join('\n') + '\n' + (spec.ipc ? 'ipcmk -M 4096 >/dev/null\n' : '') +
        `mode=$(python3 -c ${q(`import json, os\ns = json.loads(os.environ["CMP_INPUT_SPEC"])\nprint(s.get("${key}", "ok") if isinstance(s, dict) else "ok")`)})\n` +
        `amode=$(python3 -c ${q(`import json, os\ns = json.loads(os.environ["CMP_INPUT_SPEC"])\nprint(s.get("adapter_${key}", "") if isinstance(s, dict) else "")`)})\n` +
        `if [[ $amode == sleep5 ]]; then sleep 5; fi\nif [[ $amode == useleft ]]; then python3 -c ${q(USELEFT_PY)}; fi\n` +
        'if [[ $mode == adapterfail ]]; then exit 5; fi\nexit 0\n'
    }
    files['cmp_files.json'] = JSON.stringify({ files: Object.fromEntries(design.arms.map(arm => [arm.id, { res: 'out/result.txt' }])) }) + '\n'
    files['cmp_extract.json'] = JSON.stringify({ rules: [] }) + '\n'
    const versions = { A0: { version: '1.0', executable: 'bin/solver' }, A1: { version: '1.1-alt', executable: '@PWD@/bin/alt' },
      A2: { version: '0.9', executable: 'bin/missing-tool' }, evaluator: { version: '2.0', executable: 'bin/scorer' } }
    const printed = Object.fromEntries(Object.entries(versions).filter(([key]) => key === 'evaluator' ? evaluator : design.arms.some(arm => arm.id === key)))
    files['versions.sh'] = sh(`python3 -c 'import os, sys; print(sys.argv[1].replace("@PWD@", os.getcwd()))' ${q(JSON.stringify(printed))}`)
    if (evaluator) {
      files['fetch_private.sh'] = '#!/usr/bin/env bash\nset -eu\n' + `python3 -c ${q(FETCH_PY)} ${q(path.join(caseDir, 'fetch-record.json'))}\n` +
        `printf %s ${q(privateBytes)} > private.dat\nmkdir -p sub\nprintf %s ${q(privateSecond)} > sub/labels.txt\n` +
        `touch "$HOME/cmpeval-home-$$" ${q(path.join(world, 'etmp'))}/cmpeval-fetch-$$\n` + (spec.fetchExtra ?? '') + '\n'
      files['evaluate.sh'] = '#!/usr/bin/env bash\nset -u\n' + RECORD + `FAKE_FD1=$fd1 FAKE_FD2=$fd2 python3 -c ${q(EVAL_PY)}\n` +
        `printf 'evaluated\\n'\nprintf 'evaluator-err\\n' >&2\ntouch ${q(path.join(world, 'etmp'))}/cmpeval-x-$$ ${q(path.join(world, 'tmp'))}/cmpeval-t-$$\n` +
        (spec.ipc ? 'ipcmk -M 4096 >/dev/null\n' : '') +
        'if [[ -e $CMP_ARM_OUT/evalfail ]]; then exit 4; fi\nif [[ -e $CMP_ARM_OUT/evalsleep ]]; then sleep 120; fi\n' +
        'printf \'{"score": 1}\\n\' > "$CMP_EVAL_OUT/score.json"\nexit 0\n'
    }
    writeFile(designFile, JSON.stringify(design, null, 1) + '\n')
  }
  for (const [file, text] of Object.entries(files)) writeFile(path.join(source, file), text, 0o700)

  // Allocation record (SCHEMAS.md "Compute metadata").
  const sharedBox = path.join(root, 'home', '.cache', 'metis-serve', 'box.json')
  const started = new Date(Date.now() - 3600 * 1000).toISOString().replace(/\.\d+Z$/, 'Z')
  const allocation = { type: 'gpu_1x_a10', region: 'fixture-region', price_usd_h: PRICE, started_utc: started }
  const ended = { ...allocation, ended_utc: new Date(Date.now() + 7200 * 1000).toISOString().replace(/\.\d+Z$/, 'Z'), hours: 1.75 }
  if ((spec.box ?? 'open') !== 'none') writeFile(sharedBox, JSON.stringify(allocation) + '\n')

  const args = { run_root: root, tag: name, harness_from: source, ...(spec.stub ? { stub: spec.stub } : {}) }
  if (design) args.comparison = { design: designFile }
  if (spec.ceiling !== undefined) args.run_ceiling_s = spec.ceiling
  writeFile(path.join(control, 'args.json'), JSON.stringify(args, null, 1) + '\n')

  // The box: as tools/test_m5_comparison_pipeline.js, with the fakes first on PATH, a box home, variables that must
  // not reach a part, and (spec.box 'refresh') the allocation's confirmed end once cmp-private is handled.
  const replaceProbe = path.join(caseDir, 'replace-probe.js')
  const originalProbe = fs.readFileSync(path.join(ROOT, 'm5/box_probe.sh'), 'utf8')
  const probeJSON = JSON.stringify({ kernel: PROBE, nvcc: [], cmake: null, sudo_nopasswd: true })
  const fakeProbe = `#!/usr/bin/env bash\nset -eu\nmkdir -p out\nprintf '%s\\n' '${probeJSON}' > out/probe.json\n`
  fs.writeFileSync(replaceProbe, `
const fs = require('node:fs'), path = require('node:path')
const boxWalk = require(${JSON.stringify(path.join(ROOT, 'tools/m5_box_walk.js'))})
const skip = new Set(['comparison-work', 'comparison-jobs', 'cmp-private', 'reproduce-out'])
function visit(directory, depth) {
  for (const entry of boxWalk.entries(directory)) {
    const file = path.join(directory, entry.name)
    if (entry.isDirectory()) { if (depth < 3 && !skip.has(entry.name)) visit(file, depth + 1) }
    else if (entry.isFile() && entry.name.endsWith('.sh') && boxWalk.text(file) === ${JSON.stringify(originalProbe)}) fs.writeFileSync(file, ${JSON.stringify(fakeProbe)})
  }
}
visit(process.env.BOX_ROOT, 0)
`)
  const refresh = spec.box === 'refresh' ? `if [[ $command == *cmp-private* ]]; then printf '%s\\n' ${q(JSON.stringify(ended))} > ${q(sharedBox)}; fi\n` : ''
  // The box runs every command under umask 022 (a common default), so files a command creates without an explicit
  // mode are readable by other users.
  writeFile(path.join(caseDir, 'bin/box'), sh('command=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\numask 022\n' +
    `export PATH=${q(fakeBin)}:"$PATH"\nexport HOME=${q(boxHome)}\nexport PYTHONPATH=${q(fakePython)}\nexport CMP_LEAK=leaked SUDO_LEAK=leaked FAKE_KEEP=keepme\n` +
    'cd -- "$BOX_ROOT"\nbash -c "$command"\n"$M5_TEST_NODE" "$M5_REPLACE_PROBE"\n' + refresh +
    'if [[ $command == *timeout* ]]; then\n  for ((end=SECONDS+1800; SECONDS<end; )); do\n    pending=false\n    for file in "$BOX_ROOT"/m5-*/*.sh; do\n      [[ -f $file ]] || continue\n      [[ -f ${file%.sh}.rc ]] || pending=true\n    done\n    [[ $pending == true ]] || break\n    sleep 0.01\n  done\nfi\nexit 0'), 0o700)
  // spec.forge: after each copy, every fetched wrap.json whose sibling out/input.txt names a forged input is
  // replaced by the forged text (the pipeline then reads a wrap.json the contract says is invalid).
  const forgeScript = path.join(caseDir, 'forge.js')
  fs.writeFileSync(forgeScript, `
const fs = require('node:fs'), path = require('node:path')
const forge = ${JSON.stringify(spec.forge ?? {})}
function visit(directory) {
  let entries = []
  try { entries = fs.readdirSync(directory, { withFileTypes: true }) } catch { return }
  for (const entry of entries) {
    const file = path.join(directory, entry.name)
    if (entry.isDirectory()) visit(file)
    else if (entry.isFile() && entry.name === 'wrap.json') {
      let input = null
      try { input = fs.readFileSync(path.join(directory, 'out', 'input.txt'), 'utf8').trim() } catch {}
      if (input !== null && Object.hasOwn(forge, input)) fs.writeFileSync(file, forge[input])
    }
  }
}
visit(process.argv[2])
`)
  writeFile(path.join(caseDir, 'bin/fetch'), sh('source=${1//\\/tmp\\/m5-/$BOX_ROOT\\/m5-}\ncd -- "$BOX_ROOT"\nrc=0\ncp -r -- "$source" "$2" || rc=$?\n' +
    (spec.forge ? `"$M5_TEST_NODE" ${q(forgeScript)} "$2"\n` : '') + 'exit $rc'), 0o700)

  const callsFile = path.join(caseDir, 'calls.jsonl'), stderrFile = path.join(caseDir, 'stderr.log')
  const stdout = fs.openSync(path.join(caseDir, 'stdout.log'), 'w'), stderr = fs.openSync(stderrFile, 'w')
  const startMs = Date.now()
  let child
  try {
    child = await new Promise(resolve => {
      const proc = spawn(process.execPath, [path.join(pipeline, 'idea/wf.js'), '--script', path.join(pipeline, 'm5/pipeline.js'),
        '--args', path.join(control, 'args.json'), '--out', path.join(agent, 'wf'), '--disable-family', 'claude'], {
        cwd: pipeline, timeout: 1800000, killSignal: 'SIGKILL', stdio: ['ignore', stdout, stderr],
        env: { ...process.env, HOME: path.join(root, 'home'), M5_RAIDS_LEDGER: path.join(scratch, 'raids.jsonl'),
          WF_STUB: __filename, M5_CE_ROOT: root, M5_CE_CALLS: callsFile, M5_TEST_NODE: process.execPath, M5_REPLACE_PROBE: replaceProbe,
          BOX_ROOT: box, BOX: path.join(caseDir, 'bin/box'), FETCH: path.join(caseDir, 'bin/fetch') },
      })
      let error
      proc.on('error', value => { error = value })
      proc.on('close', (status, signal) => resolve({ status, signal, error }))
    })
  } finally { fs.closeSync(stdout); fs.closeSync(stderr) }
  check(`${name}: workflow completes`, () => {
    assert.ifError(child.error)
    assert.equal(child.status, 0, `signal ${child.signal}; ${fs.readFileSync(stderrFile, 'utf8').slice(-1000)}`)
  })
  const records = rows(path.join(root, 'operator/signatures.jsonl')).map(row => ({ ...row.signature, facts: row.facts }))
  const receiptDir = path.join(control, 'receipts')
  const receipts = fs.existsSync(receiptDir) ? fs.readdirSync(receiptDir).sort().filter(file => file.endsWith('.json'))
    .map(file => ({ operation: file.slice(5, -5), ...read(path.join(receiptDir, file)) })) : []
  const S = fs.readdirSync(box).filter(entry => entry.startsWith('m5-') && fs.statSync(path.join(box, entry)).isDirectory()).map(entry => path.join(box, entry))[0] ?? null
  const order = design ? scheduled(design) : []
  const jobs = order.map((_, i) => S && fs.existsSync(path.join(S, 'comparison-jobs', `i${i + 1}.json`)) ? read(path.join(S, 'comparison-jobs', `i${i + 1}.json`)) : null)
  const inv = i => path.join(S ?? '/nonexistent', 'comparison-work', `i${i + 1}`)
  const wrapAt = i => fs.existsSync(path.join(inv(i), 'wrap.json')) ? read(path.join(inv(i), 'wrap.json')) : null
  const fetched = job => path.join(agent, 'results', 'evaluate', 'comparison', `${job.mode === 'warmup' ? 'w' : 'r'}${job.round}`, job.arm, job.input)
  if (DEBUG) {
    // Diagnostics only (argument 3 "debug"): evaluate's logs and the fake log of the first invocation.
    const results = path.join(agent, 'results', 'evaluate')
    const seen = []
    ;(function visit(directory, depth) {
      for (const entry of fs.existsSync(directory) ? fs.readdirSync(directory, { withFileTypes: true }) : []) {
        const file = path.join(directory, entry.name)
        if (entry.isDirectory() && depth < 2 && entry.name !== 'comparison') visit(file, depth + 1)
        else if (entry.isFile() && /\.(log|stderr|stdout)$/.test(entry.name)) seen.push(file)
      }
    })(results, 0)
    for (const file of seen.slice(0, Number(process.argv[4] ?? 12))) console.log(`DEBUG ${name} ${path.relative(results, file)}:\n${fs.readFileSync(file, 'utf8').slice(-2500)}`)
    console.log(`DEBUG ${name} stderr: ${fs.readFileSync(stderrFile, 'utf8').slice(-1500)}`)
    const log = rows(cfg.log), first = log.findIndex(row => JSON.stringify(row).includes('/comparison-work/i1/'))
    for (const row of log.slice(Math.max(0, first - 3), first + 40)) console.log(`DEBUG ${name} fake ${row.tool} ${row.ctx} ${JSON.stringify(row.argv).slice(0, 300)}`)
    for (const row of log.filter(item => ['iptables', 'ip6tables'].includes(item.tool) || item.argv.includes('-writable'))) console.log(`DEBUG ${name} fake ${row.tool} ${row.ctx} ${JSON.stringify(row.argv)}`)
    const writableFile = S0 => path.join(S0, 'profiler', 'cmp_writable.json')
    for (const entry of fs.readdirSync(box)) if (entry.startsWith('m5-') && fs.existsSync(writableFile(path.join(box, entry)))) console.log(`DEBUG ${name} cmp_writable.json ${fs.readFileSync(writableFile(path.join(box, entry)), 'utf8')}`)
  }
  return { name, spec, caseDir, root, agent, control, box, world, boxHome, fakeBin, source, design, evaluator, records, receipts, S, order, jobs,
    inv, wrapAt, fetched, startMs, privateBytes, privateSecond, writable, files, sharedBox, allocation, ended,
    log: rows(cfg.log), calls: rows(callsFile), stage: label => records.find(row => row.stage === label),
    ops: receipts.map(receipt => receipt.operation) }
}

// ---- Checks -------------------------------------------------------------------------------------------------
const CMP_PASS = [['intake', 'PASS'], ['reproduce', 'PASS'], ['profile', 'SKIPPED'], ['seal', 'SKIPPED'], ['propose', 'SKIPPED'],
  ['implement', 'SKIPPED'], ['evaluate', 'PASS'], ['takeaways', 'PASS']]
function statuses(r, wanted) {
  check(`${r.name}: stage statuses ${wanted.map(([stage, status]) => `${stage}=${status}`).join(' ')}`, () => {
    const got = r.records.filter(row => wanted.some(([stage]) => stage === row.stage)).map(row => [row.stage, row.status])
    assert.deepEqual(got, wanted, JSON.stringify({ reproduce: r.stage('reproduce')?.error_class, evaluate: r.stage('evaluate')?.error_class }))
  })
}
const comparisonOps = r => r.ops.filter(op => COMPARISON_OPS.includes(op))
const runCount = r => r.jobs.filter(Boolean).length
const anyEvaluated = r => Array.from({ length: runCount(r) }, (_, i) => r.wrapAt(i)).some(wrap => wrap && wrap.eval_status !== 'skipped')
// Where a log row's path arguments point (relative ones from its working directory).
const resolveArg = (row, arg) => path.resolve(row.cwd ?? '/', arg)
const chownRows = (r, from = 0, to = r.log.length) => r.log.slice(from, to).map((row, index) => ({ row, index: index + from })).filter(({ row }) => row.tool === 'chown')
function chownOwner(row) {
  const spec = row.argv.find(arg => !arg.startsWith('-')) ?? ''
  const [owner, group = null] = spec.split(':')
  return { owner, group, recursive: row.argv.includes('-R') || row.argv.includes('--recursive'),
    paths: row.argv.filter(arg => !arg.startsWith('-')).slice(1).map(arg => resolveArg(row, arg).replace(/\/+$/, '')) }
}
const isBoxUser = owner => owner === BOX_USER || owner === BOX_UID
const tokenIndex = (r, k) => r.log.findIndex(row => JSON.stringify([row.argv, row.cmd ?? null, row.cwd]).includes(`/comparison-work/i${k}/`) ||
  JSON.stringify([row.argv, row.cmd ?? null]).includes(`/comparison-work/i${k}"`))
// [from, to) of the fake log rows written while invocation k ran (from the first row naming its directory).
function segment(r, k) {
  const from = tokenIndex(r, k)
  let to = r.log.length
  for (let j = k + 1; j <= r.order.length; j++) { const next = tokenIndex(r, j); if (next >= 0) { to = next; break } }
  const removal = r.log.findLastIndex(row => row.tool === 'sudo' && row.cmd?.[0] === 'rm' && row.cmd.some(arg => /cmp-private\/?$/.test(arg)))
  if (removal > from && removal < to) to = removal
  return [from, to]
}
const partRows = (r, from, to, user, scriptEnd) => r.log.slice(from, to).map((row, index) => ({ row, index: index + from }))
  .filter(({ row }) => row.tool === 'sudo' && row.target === user && (!scriptEnd || row.cmd?.at(-1)?.endsWith(scriptEnd)))
// `env -i [-C <dir>] <variables> <argv>` (a working-directory option of env may precede the variables):
// { vars, argv, chdir }.
function envCommand(cmd) {
  let i = 2, chdir = null
  while (i < cmd.length) {
    if (cmd[i] === '-C' || cmd[i] === '--chdir') { chdir = cmd[i + 1]; i += 2; continue }
    if (cmd[i].startsWith('--chdir=')) { chdir = cmd[i].slice(8); i++; continue }
    break
  }
  const vars = []
  while (i < cmd.length && /^[A-Za-z_][A-Za-z0-9_]*=/.test(cmd[i])) vars.push(cmd[i++])
  return { vars, argv: cmd.slice(i), chdir }
}
const envOfSudo = cmd => envCommand(cmd).vars

// SCHEMAS.md Timeouts: a wrap.json is valid only with exactly the wrapper keys and their types, `status` "ok" exactly
// when adapter_rc and every command's rc are 0 and the arm has as many command rows as commands, and `eval_status`
// "ok" only when eval_rc is 0. An invalid one gives status invalid and missing values.
const finiteOrNull = value => value === null || (typeof value === 'number' && Number.isFinite(value) && value >= 0)
const intOrNull = value => value === null || Number.isInteger(value)
function wrapValid(wrap, commandCount) {
  if (!wrap || typeof wrap !== 'object' || Array.isArray(wrap)) return false
  if (JSON.stringify(Object.keys(wrap).sort()) !== JSON.stringify(WRAP_KEYS)) return false
  if (!['ok', 'failed', 'timeout', 'invalid'].includes(wrap.status) || !['ok', 'failed', 'timeout', 'skipped'].includes(wrap.eval_status)) return false
  if (!intOrNull(wrap.adapter_rc) || !intOrNull(wrap.eval_rc)) return false
  for (const key of ['adapter_wall_s', 'gpu_busy_s', 'eval_wall_s', 'eval_gpu_busy_s']) if (!finiteOrNull(wrap[key])) return false
  if (typeof wrap.gpu_busy_known !== 'boolean' || typeof wrap.eval_gpu_busy_known !== 'boolean') return false
  if (!Array.isArray(wrap.commands)) return false
  for (const row of wrap.commands) {
    if (!row || typeof row !== 'object' || JSON.stringify(Object.keys(row).sort()) !== JSON.stringify(COMMAND_KEYS)) return false
    if (!Array.isArray(row.argv) || !row.argv.every(item => typeof item === 'string') || !intOrNull(row.rc) || !finiteOrNull(row.wall_s)) return false
    if (!(row.executable === null || typeof row.executable === 'string') || !(row.sha256 === null || typeof row.sha256 === 'string')) return false
  }
  const allZero = wrap.adapter_rc === 0 && wrap.commands.every(row => row.rc === 0) && wrap.commands.length === commandCount
  if ((wrap.status === 'ok') !== allZero) return false
  if (wrap.eval_status === 'ok' && wrap.eval_rc !== 0) return false
  return true
}
const commandCountOf = (r, job) => r.design.arms.find(arm => arm.id === job.arm).commands.length
const armWallOf = wrap => (wrap.adapter_wall_s ?? 0) + wrap.commands.reduce((sum, row) => sum + (row.wall_s ?? 0), 0)
// The box files of the receipt (SCHEMAS.md "Remote command files"): top-level files of the shared run directory
// named <receipt name>.<suffix> (script, log, GPU samples, exit status).
const receiptFiles = (names, receipt) => names.filter(name => name.startsWith(`${receipt.name}.`))
const evaluateReceipts = r => {
  const from = r.ops.lastIndexOf('reproduce-freeze') + 1
  const to = r.ops.reduce((last, op, i) => COMPARISON_OPS.includes(op) ? i : last, -1)
  return from > 0 && to >= from ? r.receipts.slice(from, to + 1) : []
}
// Users step 3 grants other users read access to every file of the shared run directory, so only the files of the
// evaluate stage's commands after comparison-users keep the mode they were created with.
const afterUsersReceipts = r => {
  const receipts = evaluateReceipts(r)
  const users = receipts.findIndex(receipt => receipt.operation === 'comparison-users')
  return users >= 0 ? receipts.slice(users + 1) : []
}

// The run's clock starts at the latest when the pipeline writes C/comparison.json (before intake), so the time left
// before the ceiling is at most the ceiling minus the time since then (the process spawn is too early under load).
const runStartBound = r => fs.statSync(path.join(r.control, 'comparison.json')).mtimeMs

function commonChecks(r) {
  statuses(r, CMP_PASS)
  check(`${r.name}: evaluate facts keep every existing key, each null in comparison mode (gpu_busy_known and tokens_known included), with receipts present`, () => {
    const facts = r.stage('evaluate')?.facts
    assert.ok(facts, 'no evaluate record')
    assert.ok(evaluateReceipts(r).length > 0, 'no evaluate receipt')
    for (const key of FACTS) assert.ok(Object.hasOwn(facts, key), `facts lack ${key}`)
    for (const key of FACTS) assert.equal(facts[key], null, `facts.${key}`)
  })
  check(`${r.name}: every box command of the evaluate stage after comparison-users keeps its remote files (script, log, GPU samples, exit status) at mode 600 under umask 022, the job command's script included`, () => {
    const receipts = afterUsersReceipts(r)
    assert.ok(receipts.length > 0, 'no evaluate receipt after comparison-users')
    const names = fs.readdirSync(r.S, { withFileTypes: true }).filter(entry => entry.isFile()).map(entry => entry.name)
    let jobScripts = 0
    for (const receipt of receipts) {
      const mine = receiptFiles(names, receipt)
      assert.ok(mine.length > 0, `${receipt.name}: no remote file named after the receipt`)
      for (const name of mine) assert.equal(modeOf(path.join(r.S, name)), '600', `${name} (${receipt.operation})`)
      if (receipt.operation === 'comparison-job') { assert.ok(mine.includes(`${receipt.name}.sh`), `${receipt.name}: no command script`); jobScripts++ }
    }
    assert.equal(jobScripts, runCount(r), 'comparison-job receipts')
  })
  check(`${r.name}: while an arm part runs, the remote files of the evaluate stage's box commands after comparison-users already on the box (its own comparison command's script and log included) are at mode 600`, () => {
    const receipts = afterUsersReceipts(r), comparisons = receipts.filter(receipt => receipt.operation === 'comparison')
    let seen = 0
    for (let i = 0; i < runCount(r); i++) {
      const file = path.join(r.inv(i), 'out', 'adapter.json')
      if (!fs.existsSync(file)) continue
      const boxFiles = read(file).boxFiles ?? {}
      const names = Object.keys(boxFiles)
      for (const receipt of receipts) for (const name of receiptFiles(names, receipt)) assert.equal(boxFiles[name], '600', `i${i + 1}: ${name} at mode ${boxFiles[name]} while the arm part ran`)
      const own = comparisons[i]
      assert.ok(own && receiptFiles(names, own).includes(`${own.name}.sh`), `i${i + 1}: its comparison command's script is not on the box while it runs`)
      seen++
    }
    assert.ok(seen > 0, 'no adapter record')
  })
  check(`${r.name}: only intake is called (harness_from); every call is isolated`, () => {
    assert.deepEqual(r.calls.map(call => call.label), ['intake'])
    assert.ok(r.calls.every(call => call.isolated))
  })
  check(`${r.name}: evaluate runs the comparison, not the sealed-protocol evaluation (no evaluate-* operation)`, () => {
    assert.deepEqual(r.ops.filter(op => op.startsWith('evaluate-')), [])
    assert.equal(fs.existsSync(path.join(r.control, 'evaluate', 'manifest.json')), false)
  })
  check(`${r.name}: C/comparison_scored.json written ({comparison_sha256, comparisons, totals}, sealed hash, design order); evaluate PASS whatever the outcomes`, () => {
    const scored = read(path.join(r.control, 'comparison_scored.json'))
    assert.deepEqual(Object.keys(scored).sort(), ['comparison_sha256', 'comparisons', 'totals'])
    assert.equal(scored.comparison_sha256, read(path.join(r.control, 'comparison_seal.json')).comparison_sha256)
    assert.deepEqual(scored.comparisons.map(row => row.id), r.design.comparisons.map(row => row.id))
    assert.deepEqual(Object.keys(scored.totals).sort(), ['inconclusive', 'not_supported', 'supported', 'void'])
    assert.equal(r.stage('evaluate')?.status, 'PASS')
  })
  check(`${r.name}: the comparison operations: versions, then per invocation comparison-job and comparison, in order`, () => {
    const ops = comparisonOps(r).filter(op => op !== 'comparison-users' && op !== 'comparison-private-remove')
    assert.ok(runCount(r) > 0, 'no job file')
    assert.deepEqual(ops, ['versions', ...Array.from({ length: runCount(r) }, () => ['comparison-job', 'comparison']).flat()])
  })
  check(`${r.name}: job files comparison-jobs/i<k>.json follow random.Random(order_seed): warmups, then replicates, one shuffle per round`, () => {
    const run = runCount(r)
    assert.ok(r.jobs.slice(0, run).every(Boolean) && r.jobs.slice(run).every(job => job === null), 'job files are not i1..i<n>')
    assert.equal(fs.existsSync(path.join(r.S, 'comparison-jobs', `i${r.order.length + 1}.json`)), false, 'more job files than scheduled invocations')
    r.jobs.slice(0, run).forEach((job, i) => {
      assert.deepEqual(Object.keys(job).sort(), JOB_KEYS, `i${i + 1} keys`)
      const want = r.order[i]
      assert.deepEqual([job.arm, job.input, job.mode, job.round], [want.arm, want.input, want.mode, want.round], `i${i + 1}`)
    })
  })
  check(`${r.name}: job left_s: the time left in budget_s (and before the run ceiling), positive, never growing; the resolved timeouts never exceed it`, () => {
    let previous = Infinity
    r.jobs.slice(0, runCount(r)).forEach((job, i) => {
      assert.ok(typeof job.left_s === 'number' && Number.isFinite(job.left_s) && job.left_s > 0 && job.left_s <= r.design.budget_s, `i${i + 1} left_s ${job.left_s}`)
      assert.ok(job.left_s <= previous + 1e-9, `i${i + 1}: left_s grew (${previous} -> ${job.left_s})`)
      previous = job.left_s
      if (r.spec.ceiling !== undefined) {
        const written = fs.statSync(path.join(r.S, 'comparison-jobs', `i${i + 1}.json`)).mtimeMs
        assert.ok(job.left_s <= r.spec.ceiling - (written - runStartBound(r)) / 1000 + 5, `i${i + 1}: left_s ${job.left_s} above the time left before the ceiling`)
      }
      assert.ok(job.arm_timeout_s <= job.left_s + 1, `i${i + 1}: arm_timeout_s ${job.arm_timeout_s} above left_s ${job.left_s}`)
      if (r.evaluator) assert.ok(job.eval_timeout_s <= job.left_s + 1, `i${i + 1}: eval_timeout_s ${job.eval_timeout_s} above left_s ${job.left_s}`)
    })
  })
  check(`${r.name}: neither part runs past left_s: the arm part's wall plus the evaluator part's wall stay within the job's left_s`, () => {
    for (let i = 0; i < runCount(r); i++) {
      const wrap = r.wrapAt(i), job = r.jobs[i]
      if (!wrap || !job) continue
      const total = armWallOf(wrap) + (wrap.eval_wall_s ?? 0)
      assert.ok(total <= job.left_s + 2, `i${i + 1}: ${total} s of parts with left_s ${job.left_s}`)
    }
  })
  check(`${r.name}: job files at mode 600 in comparison-jobs/ (700); comparison-work/ at 711; invocation directories i<k> only for jobs run`, () => {
    assert.equal(modeOf(path.join(r.S, 'comparison-jobs')), '700')
    assert.equal(modeOf(path.join(r.S, 'comparison-work')), '711')
    for (let i = 0; i < runCount(r); i++) assert.equal(modeOf(path.join(r.S, 'comparison-jobs', `i${i + 1}.json`)), '600', `i${i + 1}`)
    assert.deepEqual(fs.readdirSync(path.join(r.S, 'comparison-work')).sort(), Array.from({ length: runCount(r) }, (_, i) => `i${i + 1}`).sort())
  })
  check(`${r.name}: wrap.json at mode 600, written in an invocation directory at mode 700, exactly the wrapper keys`, () => {
    for (let i = 0; i < runCount(r); i++) {
      assert.equal(modeOf(r.inv(i)), '700', `i${i + 1} directory`)
      assert.equal(modeOf(path.join(r.inv(i), 'wrap.json')), '600', `i${i + 1} wrap.json`)
      const wrap = r.wrapAt(i)
      assert.deepEqual(Object.keys(wrap).sort(), WRAP_KEYS, `i${i + 1}`)
      assert.ok(Array.isArray(wrap.commands), `i${i + 1} commands`)
      for (const row of wrap.commands) assert.deepEqual(Object.keys(row).sort(), COMMAND_KEYS, `i${i + 1} command row`)
      for (const value of [wrap.adapter_wall_s, ...wrap.commands.map(row => row.wall_s)]) assert.ok(typeof value === 'number' && value >= 0, `i${i + 1} wall ${value}`)
    }
  })
  check(`${r.name}: out/, log/ and wrap.json are fetched to A/results/evaluate/comparison/<w<r>|r<r>>/<arm>/<input>/ from the token's job`, () => {
    for (let i = 0; i < runCount(r); i++) {
      const at = r.fetched(r.order[i])
      assert.ok(fs.readFileSync(path.join(at, 'wrap.json')).equals(fs.readFileSync(path.join(r.inv(i), 'wrap.json'))), `${at}: wrap.json is not i${i + 1}'s`)
      for (const name of fs.readdirSync(path.join(r.inv(i), 'log')))
        assert.ok(fs.readFileSync(path.join(at, 'log', name)).equals(fs.readFileSync(path.join(r.inv(i), 'log', name))), `${at}: log/${name}`)
      for (const entry of fs.readdirSync(path.join(r.inv(i), 'out'), { withFileTypes: true })) if (entry.isFile())
        assert.ok(fs.readFileSync(path.join(at, 'out', entry.name)).equals(fs.readFileSync(path.join(r.inv(i), 'out', entry.name))), `${at}: out/${entry.name}`)
      assert.ok(fs.statSync(path.join(at, 'eval')).isDirectory(), `${at}: no eval/`)
    }
  })
  check(`${r.name}: the adapter and the commands run in run/, a fresh directory of symbolic links to the shared run directory's entries (never out, profiler, the work and job folders or cmp-private)`, () => {
    for (let i = 0; i < runCount(r); i++) {
      const record = read(path.join(r.inv(i), 'out', 'adapter.json'))
      assert.equal(record.cwd, path.join(r.inv(i), 'run'), `i${i + 1} cwd`)
      assert.equal(record.S, r.S)
      const linked = Object.keys(record.run)
      for (const name of NOT_LINKED) assert.ok(!linked.includes(name), `i${i + 1}: run/${name}`)
      for (const name of linked) {
        assert.ok(record.shared.includes(name), `i${i + 1}: run/${name} is not in the shared run directory`)
        assert.notEqual(record.run[name], 'notlink', `i${i + 1}: run/${name} is not a symbolic link`)
        assert.equal(path.resolve(path.join(r.inv(i), 'run'), record.run[name]), path.join(r.S, name), `i${i + 1}: run/${name} -> ${record.run[name]}`)
      }
      const missing = record.shared.filter(name => !NOT_LINKED.includes(name) && !linked.includes(name) && !/\.(gpu|log|rc|sh|out|err|pid|json|tmp)$/.test(name))
      assert.deepEqual(missing, [], `i${i + 1}: entries not linked`)
      for (const name of ['harness', 'bin', 'data', 'lib', 'baseline-published', 'reproduce-out']) assert.ok(linked.includes(name), `i${i + 1}: run/${name} missing`)
    }
  })
  check(`${r.name}: the invocation directory (711) holds run/, empty out/, log/ (700), empty eval/, empty home/ and ehome/ when the adapter starts`, () => {
    for (let i = 0; i < runCount(r); i++) {
      const record = read(path.join(r.inv(i), 'out', 'adapter.json'))
      assert.deepEqual(record.invList, ['ehome', 'eval', 'home', 'log', 'out', 'run'], `i${i + 1}`)
      assert.equal(record.invMode, '711', `i${i + 1} directory mode`)
      assert.equal(record.logMode, '700', `i${i + 1} log/ mode`)
      assert.deepEqual([record.outList, record.evalList, record.homeList, record.ehomeList], [[], [], [], []], `i${i + 1}`)
    }
  })
  check(`${r.name}: part environment of the adapter: the wrapper's variables without CMP_, SUDO_ or HOME, HOME=home/, CMP_INPUT, CMP_INPUT_SPEC, CMP_OUT`, () => {
    for (let i = 0; i < runCount(r); i++) {
      const env = read(path.join(r.inv(i), 'out', 'adapter.json')).env, job = r.order[i]
      armEnv(r, env, i, job, `i${i + 1} adapter`)
    }
  })
  check(`${r.name}: the wrapper opens the logs: adapter standard output and error are log/adapter.stdout and log/adapter.stderr`, () => {
    for (let i = 0; i < runCount(r); i++) {
      const record = read(path.join(r.inv(i), 'out', 'adapter.json')), at = r.fetched(r.order[i])
      assert.equal(record.fd1, path.join(r.inv(i), 'log', 'adapter.stdout'))
      assert.equal(record.fd2, path.join(r.inv(i), 'log', 'adapter.stderr'))
      assert.equal(fs.readFileSync(path.join(at, 'log', 'adapter.stdout'), 'utf8'), `adapter-out ${r.order[i].arm}\n`)
      assert.equal(fs.readFileSync(path.join(at, 'log', 'adapter.stderr'), 'utf8'), `adapter-err ${r.order[i].arm}\n`)
    }
  })
  check(`${r.name}: each command runs after placeholder substitution, with the arm's env, logs log/cmd<k>.stdout|stderr, and wrap.json records argv, executable and SHA-256`, () => {
    for (let i = 0; i < runCount(r); i++) {
      const job = r.order[i], wrap = r.wrapAt(i)
      const arm = r.design.arms.find(item => item.id === job.arm), input = r.design.inputs.find(item => item.id === job.input)
      const where = { input: job.input, spec: input.spec, run: path.join(r.inv(i), 'run'), out: path.join(r.inv(i), 'out') }
      wrap.commands.forEach((row, c) => {
        const argv = arm.commands[c].map(word => substitute(word, where))
        assert.deepEqual(row.argv, argv, `i${i + 1} command ${c + 1} argv`)
        const executable = argv[0].includes('/') ? fs.realpathSync(path.join(r.S, argv[0])) : fs.realpathSync([r.fakeBin, ...(process.env.PATH ?? '').split(path.delimiter)].map(dir => path.join(dir, argv[0])).find(file => fs.existsSync(file)))
        assert.ok(typeof row.executable === 'string' && path.isAbsolute(row.executable), `i${i + 1} command ${c + 1} executable ${row.executable}`)
        assert.equal(fs.realpathSync(row.executable), executable, `i${i + 1} command ${c + 1} executable`)
        assert.equal(row.sha256, sha(fs.readFileSync(executable)), `i${i + 1} command ${c + 1} sha256`)
        const rec = argv.includes('--rec') ? argv[argv.indexOf('--rec') + 1] : null
        const record = read(path.join(r.inv(i), 'out', `solver-${rec}.json`))
        assert.deepEqual(record.argv, argv.slice(argv[0] === 'bash' ? 2 : 1), `i${i + 1} command ${c + 1} arguments received`)
        assert.equal(record.cwd, path.join(r.inv(i), 'run'), `i${i + 1} command ${c + 1} cwd`)
        assert.equal(record.fd1, path.join(r.inv(i), 'log', `cmd${c + 1}.stdout`))
        assert.equal(record.fd2, path.join(r.inv(i), 'log', `cmd${c + 1}.stderr`))
        armEnv(r, record.env, i, job, `i${i + 1} command ${c + 1}`)
        for (const [key, value] of Object.entries(arm.env ?? {})) assert.equal(record.env[key], substitute(value, where), `i${i + 1} env ${key}`)
        const at = r.fetched(job)
        assert.equal(fs.readFileSync(path.join(at, 'log', `cmd${c + 1}.stdout`), 'utf8'), `solver-out ${rec}\n`)
        assert.equal(fs.readFileSync(path.join(at, 'log', `cmd${c + 1}.stderr`), 'utf8'), `solver-err ${rec}\n`)
      })
      // The contract leaves the evaluator part's streams open; they may sit beside the arm's logs as evaluator.*.
      assert.deepEqual(fs.readdirSync(path.join(r.inv(i), 'log')).filter(name => !name.startsWith('evaluator.')).sort(),
        ['adapter.stderr', 'adapter.stdout', ...wrap.commands.flatMap((_, c) => [`cmd${c + 1}.stderr`, `cmd${c + 1}.stdout`])].sort(), `i${i + 1} log/`)
    }
  })
  check(`${r.name}: versions: out/comparison/versions.json from harness/versions.sh; system.json exactly {cpu_model, cpu_logical, kernel, driver_version, cuda_version, gpus, executables}`, () => {
    const versions = read(path.join(r.S, 'out', 'comparison', 'versions.json'))
    const keys = [...r.design.arms.map(arm => arm.id), ...(r.evaluator ? ['evaluator'] : [])]
    assert.deepEqual(Object.keys(versions).sort(), keys.sort())
    const system = read(path.join(r.S, 'out', 'comparison', 'system.json'))
    assert.deepEqual(Object.keys(system).sort(), ['cpu_logical', 'cpu_model', 'cuda_version', 'driver_version', 'executables', 'gpus', 'kernel'])
    assert.equal(system.cpu_model, CPU_MODEL)
    assert.equal(system.cpu_logical, CPU_COUNT)
    assert.equal(system.kernel, os.release())
    assert.equal(system.driver_version, DRIVER)
    assert.equal(system.cuda_version, CUDA)
    assert.equal(system.gpus.length, GPUS.length)
    system.gpus.forEach((row, g) => {
      assert.deepEqual(Object.keys(row).sort(), ['index', 'memory_total', 'name', 'uuid'], `gpu ${g}`)
      assert.ok(row.index === g || row.index === String(g), `gpu ${g} index ${row.index}`)
      assert.equal(row.name, GPUS[g].name)
      assert.equal(row.uuid, GPUS[g].uuid)
      assert.ok([81559, '81559', '81559 MiB'].includes(row.memory_total), `gpu ${g} memory_total ${row.memory_total}`)
    })
    assert.deepEqual(Object.keys(system.executables).sort(), keys.sort())
    for (const key of keys) {
      const row = system.executables[key]
      assert.deepEqual(Object.keys(row).sort(), ['executable', 'libraries', 'sha256', 'version'], key)
      assert.equal(row.version, versions[key].version, `${key} version`)
      assert.equal(row.executable, versions[key].executable, `${key} executable`)
    }
    const file = name => path.join(r.S, name)
    assert.equal(system.executables.A0.sha256, sha(fs.readFileSync(file('bin/solver-1.0'))), 'A0 sha256 of the resolved executable')
    assert.deepEqual(system.executables.A0.libraries, [
      { name: 'libfake.so.1', path: file('lib/libfake.so.1'), sha256: sha(fs.readFileSync(file('lib/libfake.so.1'))) },
      { name: 'libalias.so.2', path: file('lib/libalias.so.2'), sha256: sha(fs.readFileSync(file('lib/libfake.so.1.0'))) }], 'A0 libraries')
    assert.equal(system.executables.A1.executable, file('bin/alt'))
    assert.equal(system.executables.A1.sha256, sha(fs.readFileSync(file('bin/alt'))), 'A1 sha256 (absolute path)')
    assert.deepEqual(system.executables.A1.libraries, [], 'A1: ldd fails')
    if (r.evaluator) {
      assert.equal(system.executables.evaluator.sha256, sha(fs.readFileSync(file('bin/scorer'))))
      assert.deepEqual(system.executables.evaluator.libraries, [], 'evaluator: static')
    }
    if (versions.A2) assert.equal(system.executables.A2.sha256, null, 'A2: missing executable')
  })
  check(`${r.name}: comparison_compute.json exactly {invocations, arms, all_invocations, system, versions, allocation}, attribution from wrap.json`, () => computeChecks(r))
  check(`${r.name}: the harness on the box is unchanged by the comparison`, () => {
    for (const [name, text] of Object.entries(r.files)) assert.equal(fs.readFileSync(path.join(r.S, 'harness', name), 'utf8'), text, name)
  })
}
function armEnv(r, env, i, job, where) {
  const spec = r.design.inputs.find(item => item.id === job.input).spec
  assert.equal(env.HOME, path.join(r.inv(i), 'home'), `${where}: HOME`)
  assert.equal(env.CMP_INPUT, job.input, `${where}: CMP_INPUT`)
  assert.deepEqual(JSON.parse(env.CMP_INPUT_SPEC), spec, `${where}: CMP_INPUT_SPEC`)
  assert.equal(env.CMP_OUT, path.join(r.inv(i), 'out'), `${where}: CMP_OUT`)
  assert.deepEqual(Object.keys(env).filter(key => key.startsWith('CMP_')).sort(), ['CMP_INPUT', 'CMP_INPUT_SPEC', 'CMP_OUT'], `${where}: CMP_ variables`)
  assert.deepEqual(Object.keys(env).filter(key => key.startsWith('SUDO_')), [], `${where}: SUDO_ variables`)
  assert.equal(env.FAKE_KEEP, 'keepme', `${where}: the wrapper's environment is not passed`)
  assert.equal(env.FAKE_SUDO_USER, undefined, `${where}: the environment is not built with env -i`)
  assert.equal(env.FAKE_SUDO_ROOT, undefined, `${where}: the part runs as root`)
}
function invalidRow(row, where) {
  assert.equal(row.status, 'invalid', `${where} status`)
  for (const key of ['wall_s', 'gpu_busy_s', 'eval_wall_s', 'eval_gpu_busy_s']) assert.equal(row[key], null, `${where} ${key}`)
  assert.ok(row.attributed_usd === null || row.attributed_usd === 0, `${where} attributed_usd ${row.attributed_usd}`)
  assert.ok(row.gpu_busy_known === null || row.gpu_busy_known === false, `${where} gpu_busy_known ${row.gpu_busy_known}`)
}
function computeChecks(r) {
  const compute = read(path.join(r.agent, 'results', 'evaluate', 'comparison_compute.json'))
  assert.deepEqual(Object.keys(compute).sort(), ['all_invocations', 'allocation', 'arms', 'invocations', 'system', 'versions'])
  const price = (r.spec.box ?? 'open') === 'none' ? null : PRICE
  assert.equal(compute.invocations.length, r.order.length, 'one row per scheduled invocation')
  compute.invocations.forEach((row, i) => {
    const job = r.order[i], wrap = i < runCount(r) ? r.wrapAt(i) : null
    assert.deepEqual(Object.keys(row).sort(), INV_KEYS, `row ${i + 1}`)
    assert.deepEqual([row.round, row.arm, row.input], [job.round, job.arm, job.input], `row ${i + 1}`)
    if (!wrap) {
      assert.equal(row.status, 'not_run', `row ${i + 1}`)
      for (const key of ['wall_s', 'gpu_busy_s', 'eval_wall_s', 'eval_gpu_busy_s', 'attributed_usd']) assert.equal(row[key], null, `row ${i + 1} ${key}`)
      return
    }
    if (!wrapValid(wrap, commandCountOf(r, job))) {
      // An invalid wrap.json (for example status "invalid" with every exit status 0): status invalid, missing values.
      invalidRow(row, `row ${i + 1}`)
      return
    }
    assert.equal(row.status, wrap.status, `row ${i + 1} status`)
    const wall = (wrap.adapter_wall_s ?? 0) + wrap.commands.reduce((sum, item) => sum + (item.wall_s ?? 0), 0)
    near(row.wall_s, wall, `row ${i + 1} wall_s`)
    assert.equal(row.gpu_busy_s, wrap.gpu_busy_s, `row ${i + 1} gpu_busy_s`)
    assert.equal(row.gpu_busy_known, wrap.gpu_busy_known, `row ${i + 1} gpu_busy_known`)
    assert.equal(row.eval_status, wrap.eval_status, `row ${i + 1} eval_status`)
    assert.equal(row.eval_wall_s, wrap.eval_wall_s, `row ${i + 1} eval_wall_s`)
    assert.equal(row.eval_gpu_busy_s, wrap.eval_gpu_busy_s, `row ${i + 1} eval_gpu_busy_s`)
    if (price === null) assert.equal(row.attributed_usd, null, `row ${i + 1} attributed_usd without a price`)
    else near(row.attributed_usd, (wall + (wrap.eval_wall_s ?? 0)) / 3600 * price, `row ${i + 1} attributed_usd`)
  })
  const sum = (list, key) => list.reduce((total, row) => total + (row[key] ?? 0), 0)
  assert.deepEqual(compute.arms.map(row => row.arm), r.design.arms.map(arm => arm.id), 'arms rows')
  for (const row of compute.arms) {
    assert.deepEqual(Object.keys(row).sort(), ARM_KEYS, row.arm)
    const mine = compute.invocations.filter((item, i) => r.order[i].arm === row.arm && r.order[i].mode === 'replicate')
    assert.equal(row.invocations, mine.length, `${row.arm} invocations (replicates, whatever their status)`)
    for (const key of ['wall_s', 'gpu_busy_s', 'eval_wall_s', 'eval_gpu_busy_s', 'attributed_usd']) near(row[key], sum(mine, key), `${row.arm} ${key}`)
    assert.equal(row.gpu_busy_known, mine.every(item => item.gpu_busy_known === true), `${row.arm} gpu_busy_known`)
  }
  assert.deepEqual(Object.keys(compute.all_invocations).sort(), ['attributed_usd', 'eval_wall_s', 'invocations', 'wall_s'])
  assert.equal(compute.all_invocations.invocations, r.order.length)
  for (const key of ['wall_s', 'eval_wall_s', 'attributed_usd']) near(compute.all_invocations[key], sum(compute.invocations, key), `all_invocations ${key}`)
  assert.deepEqual(compute.system, read(path.join(r.S, 'out', 'comparison', 'system.json')), 'system')
  assert.deepEqual(compute.versions, read(path.join(r.S, 'out', 'comparison', 'versions.json')), 'versions')
  const a = compute.allocation
  assert.deepEqual(Object.keys(a).sort(), ['ended_utc', 'final', 'hours', 'price_usd_h', 'started_utc', 'type', 'usd'])
  if (price === null) {
    assert.deepEqual(a, { type: null, price_usd_h: null, started_utc: null, ended_utc: null, hours: null, usd: null, final: false }, 'allocation unavailable')
    return
  }
  assert.deepEqual([a.type, a.price_usd_h, a.started_utc], [r.allocation.type, PRICE, r.allocation.started_utc], 'allocation from C/box.json')
  if (r.spec.box === 'refresh') {
    assert.deepEqual([a.ended_utc, a.hours, a.final], [r.ended.ended_utc, r.ended.hours, true], 'the confirmed end (takeaways rewrite)')
  } else {
    const written = fs.statSync(path.join(r.agent, 'results', 'evaluate', 'comparison_compute.json')).mtimeMs
    assert.equal(a.ended_utc, null)
    assert.equal(a.final, false)
    assert.ok(Math.abs(a.hours - (written - Date.parse(r.allocation.started_utc)) / 3600000) < 120 / 3600, `hours ${a.hours}`)
  }
  near(a.usd, a.hours * PRICE, 'allocation usd')
}
// Part runs of a separated-users run.
function sudoPartChecks(r) {
  check(`${r.name}: arm parts run as sudo -n -u cmp-arm -- env -i <variables> bash harness/arms/<arm>.sh and the commands; HOME once, home/; no CMP_ or SUDO_ variable of the wrapper`, () => {
    for (let k = 1; k <= runCount(r); k++) {
      const [from, to] = segment(r, k), job = r.order[k - 1], wrap = r.wrapAt(k - 1)
      const parts = partRows(r, from, to, 'cmp-arm').filter(({ row }) => row.cmd[0] === 'env')
      assert.ok(parts.length >= 1, `i${k}: no arm part through sudo`)
      for (const { row } of parts) {
        assert.deepEqual(row.argv.slice(0, 4), ['-n', '-u', 'cmp-arm', '--'], `i${k}: sudo options`)
        assert.deepEqual(row.cmd.slice(0, 2), ['env', '-i'], `i${k}`)
        const vars = envOfSudo(row.cmd)
        assert.deepEqual(vars.filter(item => item.startsWith('HOME=')), [`HOME=${path.join(r.inv(k - 1), 'home')}`], `i${k} HOME`)
        assert.deepEqual(vars.filter(item => /^(SUDO_|CMP_LEAK)/.test(item)), [], `i${k} leaked variables`)
      }
      const tails = parts.map(({ row }) => envCommand(row.cmd).argv)
      for (const { row } of parts) assert.ok([null, path.join(r.inv(k - 1), 'run')].includes(envCommand(row.cmd).chdir), `i${k}: env -C ${envCommand(row.cmd).chdir}`)
      assert.deepEqual(tails[0], ['bash', `harness/arms/${job.arm}.sh`], `i${k}: adapter`)
      assert.deepEqual(tails.slice(1), wrap.commands.map(item => item.argv), `i${k}: commands`)
    }
  })
  if (!r.evaluator) check(`${r.name}: without an evaluator, nothing runs as cmp-eval`, () => {
    assert.deepEqual(r.log.filter(row => row.ctx === 'cmp-eval' || (row.tool === 'sudo' && row.target === 'cmp-eval')).map(row => [row.tool, row.argv]), [])
  })
  if (r.evaluator) check(`${r.name}: the evaluator part runs only after an ok arm part, as sudo -n -u cmp-eval -- env -i <variables> bash <shared>/harness/evaluate.sh from the shared run directory`, () => {
    for (let k = 1; k <= runCount(r); k++) {
      const [from, to] = segment(r, k), wrap = r.wrapAt(k - 1)
      const parts = partRows(r, from, to, 'cmp-eval', '/harness/evaluate.sh')
      if (wrap.status !== 'ok') { assert.equal(parts.length, 0, `i${k}: evaluator ran after ${wrap.status}`); assert.equal(wrap.eval_status, 'skipped', `i${k}`); continue }
      assert.equal(parts.length, 1, `i${k}: evaluator parts`)
      const { row } = parts[0]
      assert.deepEqual(row.argv.slice(0, 4), ['-n', '-u', 'cmp-eval', '--'])
      assert.deepEqual(row.cmd.slice(0, 2), ['env', '-i'])
      assert.deepEqual(envCommand(row.cmd).argv, ['bash', path.join(r.S, 'harness', 'evaluate.sh')], `i${k}`)
      assert.ok([null, r.S].includes(envCommand(row.cmd).chdir), `i${k}: env -C`)
      const record = read(path.join(r.fetched(r.order[k - 1]), 'eval', 'eval-record.json'))
      const env = record.env, base = r.inv(k - 1)
      assert.equal(record.cwd, r.S, `i${k} cwd`)
      assert.deepEqual(Object.fromEntries(Object.entries(env).filter(([key]) => key.startsWith('CMP_'))), {
        CMP_INPUT: r.order[k - 1].input, CMP_INPUT_SPEC: env.CMP_INPUT_SPEC, CMP_ARM_OUT: path.join(base, 'out'),
        CMP_EVAL_OUT: path.join(base, 'eval'), CMP_PRIVATE: path.join(r.S, 'cmp-private') }, `i${k} CMP_ variables`)
      assert.deepEqual(JSON.parse(env.CMP_INPUT_SPEC), r.design.inputs.find(item => item.id === r.order[k - 1].input).spec)
      assert.equal(env.HOME, path.join(base, 'ehome'), `i${k} HOME`)
      assert.deepEqual(Object.keys(env).filter(key => key.startsWith('SUDO_')), [], `i${k} SUDO_`)
      assert.equal(env.FAKE_KEEP, 'keepme')
      assert.equal(env.FAKE_SUDO_USER, undefined, 'not built with env -i')
      assert.deepEqual([record.evalList, record.homeList], [[], []], `i${k}: eval/ and ehome/ not empty`)
    }
  })
  check(`${r.name}: no path, argument or environment variable of the evaluator part names the arm`, () => {
    let seen = 0
    for (let k = 1; k <= runCount(r); k++) {
      const [from, to] = segment(r, k)
      for (const { row } of partRows(r, from, to, 'cmp-eval')) for (const arg of row.argv) assert.ok(!namesArm(arg), `i${k}: sudo argument ${arg}`)
      const file = path.join(r.fetched(r.order[k - 1]), 'eval', 'eval-record.json')
      if (!fs.existsSync(file)) continue
      seen++
      const record = read(file)
      for (const [key, value] of Object.entries(record.env)) assert.ok(!namesArm(key) && !namesArm(value), `i${k}: ${key}=${value}`)
      assert.ok(!namesArm(record.cwd))
      // From evaluate.sh up to the wrapper and the process that started it.
      const upTo = record.ancestors.findIndex(cmd => cmd.some(part => part.endsWith('cmp_wrap.py')))
      assert.ok(upTo >= 0, `i${k}: the wrapper is not an ancestor of the evaluator: ${JSON.stringify(record.ancestors).slice(0, 400)}`)
      assert.deepEqual(record.ancestors[upTo].slice(-2).at(-1), `i${k}`, `i${k}: the wrapper's only argument is the token`)
      for (const cmd of record.ancestors.slice(0, upTo + 2)) for (const part of cmd) assert.ok(!namesArm(part), `i${k}: process argument ${part}`)
    }
    assert.ok(seen > 0 || !anyEvaluated(r), 'no evaluator record')
  })
  check(`${r.name}: per invocation: run/, out/, home/ chowned to cmp-arm and eval/, ehome/ to cmp-eval before the arm part; after it, cleanup (pkill -KILL -u cmp-arm until pgrep -u cmp-arm finds none, find -delete outside the shared run directory), then run/ and out/ chowned -R to the box user; the same for cmp-eval and eval/`, () => {
    for (let k = 1; k <= runCount(r); k++) {
      const [from, to] = segment(r, k), base = r.inv(k - 1), wrap = r.wrapAt(k - 1)
      const armParts = partRows(r, from, to, 'cmp-arm').filter(({ row }) => row.cmd[0] === 'env')
      const firstArm = armParts[0].index, lastArm = armParts.at(-1).index
      const chowns = chownRows(r, from, to).map(({ row, index }) => ({ index, ...chownOwner(row), ctx: row.ctx }))
      const covered = (list, dir) => list.some(item => item.paths.includes(path.join(base, dir)))
      const toArm = chowns.filter(item => item.owner === 'cmp-arm' && item.index < firstArm)
      for (const dir of ['run', 'out', 'home']) assert.ok(covered(toArm, dir), `i${k}: ${dir}/ not chowned to cmp-arm before the arm part`)
      const toEval = chowns.filter(item => item.owner === 'cmp-eval' && item.index < firstArm)
      if (r.evaluator) for (const dir of ['eval', 'ehome']) assert.ok(covered(toEval, dir), `i${k}: ${dir}/ not chowned to cmp-eval before the arm part`)
      assert.ok(chowns.every(item => item.ctx === 'root'), `i${k}: chown without sudo`)
      const killArm = r.log.slice(lastArm, to).findIndex(row => row.tool === 'pkill' && row.ctx === 'root' && JSON.stringify(row.argv) === JSON.stringify(['-KILL', '-u', 'cmp-arm']))
      assert.ok(killArm >= 0, `i${k}: no pkill -KILL -u cmp-arm (as root) after the arm part`)
      const after = lastArm + killArm
      assert.ok(r.log.slice(after, to).some(row => row.tool === 'pgrep' && row.argv.includes('-u') && row.argv.includes('cmp-arm')), `i${k}: no pgrep -u cmp-arm`)
      const back = chowns.filter(item => isBoxUser(item.owner) && item.recursive && item.index > after)
      for (const dir of ['run', 'out']) assert.ok(covered(back, dir), `i${k}: ${dir}/ not chowned -R back to the box user after the cleanup`)
      const backIndex = Math.min(...back.filter(item => covered([item], 'run') || covered([item], 'out')).map(item => item.index))
      const finds = r.log.slice(after, backIndex).filter(row => row.tool === 'find' && row.argv.includes('-delete') && row.argv.includes('cmp-arm'))
      assert.ok(finds.length > 0, `i${k}: no cleanup find for cmp-arm before the chown back`)
      const evalParts = partRows(r, from, to, 'cmp-eval', '/harness/evaluate.sh')
      if (wrap.status === 'ok' && r.evaluator && !(wrap.eval_status === 'timeout' && wrap.eval_wall_s === null)) {
        assert.ok(evalParts.length === 1 && evalParts[0].index > backIndex, `i${k}: the evaluator part does not follow the chown back`)
        const killEval = r.log.slice(evalParts[0].index, to).findIndex(row => row.tool === 'pkill' && row.ctx === 'root' && JSON.stringify(row.argv) === JSON.stringify(['-KILL', '-u', 'cmp-eval']))
        assert.ok(killEval >= 0, `i${k}: no pkill -KILL -u cmp-eval after the evaluator part`)
        const evalBack = chowns.filter(item => isBoxUser(item.owner) && item.recursive && item.index > evalParts[0].index + killEval && covered([item], 'eval'))
        assert.ok(evalBack.length > 0, `i${k}: eval/ not chowned -R to the box user after the evaluator's cleanup`)
      }
    }
  })
  check(`${r.name}: cleanup find: one find per listed top-level directory, exactly find <dir> -mindepth 1 -user <user> ! -path <S> ! -path <S>/* -delete with <S> escaped`, () => {
    const S = escapePath(r.S)
    const tops = user => {
      const list = r.writable[user]
      return list.filter(dir => !list.some(other => other !== dir && dir.startsWith(other + '/'))).sort()
    }
    for (let k = 1; k <= runCount(r); k++) {
      const [from, to] = segment(r, k)
      const wrap = r.wrapAt(k - 1)
      const evaluated = r.evaluator && wrap.status === 'ok' && !(wrap.eval_status === 'timeout' && wrap.eval_wall_s === null)
      for (const user of ['cmp-arm', ...(evaluated ? ['cmp-eval'] : [])]) {
        const finds = r.log.slice(from, to).filter(row => row.tool === 'find' && row.argv.includes('-delete') && row.argv.includes(user))
        assert.deepEqual(finds.map(row => row.argv[0]).sort(), tops(user), `i${k} ${user}: directories`)
        for (const row of finds) assert.deepEqual(row.argv, [row.argv[0], '-mindepth', '1', '-user', user, '!', '-path', S, '!', '-path', S + '/*', '-delete'], `i${k} ${user}`)
        assert.ok(finds.every(row => row.ctx === 'root'), `i${k}: cleanup without sudo`)
      }
    }
  })
  check(`${r.name}: cleanup removes what the part users left outside the shared run directory and never touches the shared run directory`, () => {
    const left = dir => fs.readdirSync(dir).filter(name => /^cmp(arm|eval)-/.test(name))
    for (const dir of [r.box, ...['tmp', 'tmp/sub', 'shm', 'etmp'].map(name => path.join(r.world, name))]) assert.deepEqual(left(dir), [], dir)
    const adapters = r.log.filter(row => row.tool === 'sudo' && row.target === 'cmp-arm' && /harness\/arms\/A\d\.sh$/.test(row.cmd?.at(-1) ?? '')).length
    assert.equal(fs.readdirSync(path.join(r.S, 'data')).filter(name => name.startsWith('cmparm-keep-')).length, adapters, 'files the arm part left in the shared run directory')
    for (let i = 0; i < runCount(r); i++) assert.equal(fs.readdirSync(path.join(r.inv(i), 'out')).filter(name => name.startsWith('cmparm-out-')).length, 1, `i${i + 1} out/`)
  })
  check(`${r.name}: after the arm part, home/ is removed and run/ is at mode 700; after the evaluator, ehome/ is removed; out/ loses group and other write and gains other read and search`, () => {
    for (let i = 0; i < runCount(r); i++) {
      const base = r.inv(i), wrap = r.wrapAt(i)
      assert.equal(fs.existsSync(path.join(base, 'home')), false, `i${i + 1} home/`)
      assert.equal(modeOf(path.join(base, 'run')), '700', `i${i + 1} run/`)
      if (wrap.eval_status !== 'skipped') assert.equal(fs.existsSync(path.join(base, 'ehome')), false, `i${i + 1} ehome/`)
      if (wrap.status === 'ok') {
        assert.equal(modeOf(path.join(base, 'out', 'wide.txt')), '644', `i${i + 1} out/wide.txt`)
        assert.equal(modeOf(path.join(base, 'out', 'closed')), '705', `i${i + 1} out/closed`)
        assert.equal(modeOf(path.join(base, 'out', 'closed', 'inner.txt')), '604', `i${i + 1} out/closed/inner.txt`)
      }
    }
  })
  check(`${r.name}: the evaluator reads cmp-private: owned root:cmp-eval, directories 750, files 640, without .home`, () => {
    let seen = 0
    for (let i = 0; i < runCount(r); i++) {
      const file = path.join(r.fetched(r.order[i]), 'eval', 'eval-record.json')
      if (!fs.existsSync(file)) continue
      seen++
      const record = read(file)
      assert.equal(record.privateMode, '750')
      assert.deepEqual(record.private, { 'private.dat': ['640', 'file'], sub: ['750', 'dir'], 'sub/labels.txt': ['640', 'file'] })
    }
    assert.ok(seen > 0 || !anyEvaluated(r), 'no evaluator record')
  })
  if (!r.evaluator) check(`${r.name}: without an evaluator, no cmp-private, no private-data fetch and no comparison-private-remove`, () => {
    assert.ok(!comparisonOps(r).includes('comparison-private-remove'), JSON.stringify(comparisonOps(r)))
    assert.equal(fs.existsSync(path.join(r.S, 'cmp-private')), false)
    assert.ok(!r.log.some(row => row.tool === 'sudo' && (row.cmd ?? []).some(arg => /fetch_private\.sh$/.test(arg))), 'fetch_private.sh ran')
    // Naming cmp-private in step 3's exclusion is allowed; creating or handing it to a user is not.
    assert.ok(!r.log.some(row => ['chown', 'install'].includes(row.tool) && row.argv.some(arg => /cmp-private/.test(arg))), 'cmp-private created or chowned')
    assert.ok(!r.log.some(row => row.tool === 'sudo' && ['mkdir', 'install', 'chown'].includes(row.cmd?.[0]) && row.cmd.some(arg => /cmp-private/.test(arg))), 'cmp-private created through sudo')
  })
  if (r.evaluator) check(`${r.name}: after the last invocation, comparison-private-remove removes cmp-private with sudo -n rm -rf`, () => {
    const ops = comparisonOps(r)
    assert.equal(ops.at(-1), 'comparison-private-remove')
    assert.equal(ops.filter(op => op === 'comparison-private-remove').length, 1)
    const removal = r.log.findLastIndex(row => row.tool === 'sudo' && row.cmd?.[0] === 'rm' && row.cmd.some(arg => /^-[a-z]*r[a-z]*f|^-[a-z]*f[a-z]*r/.test(arg)) &&
      row.cmd.some(arg => !arg.startsWith('-') && resolveArg(row, arg).replace(/\/+$/, '') === path.join(r.S, 'cmp-private')))
    assert.ok(removal >= 0, 'no sudo -n rm -rf of cmp-private')
    assert.ok(removal > tokenIndex(r, runCount(r)), 'removed before the last invocation')
    assert.equal(fs.existsSync(path.join(r.S, 'cmp-private')), false)
  })
}
// The comparison-users command of a separated-users run that passed it.
function usersChecks(r, { created }) {
  const S = r.S
  const before = (a, b, label) => assert.ok(a >= 0 && b >= 0 && a < b, `${label} (${a}, ${b})`)
  const idx = test => r.log.findIndex(test)
  const sudoTo = (user, test) => idx(row => row.tool === 'sudo' && row.target === user && test(row.cmd))
  check(`${r.name}: comparison-users runs before the first invocation, as one box command`, () => {
    const ops = comparisonOps(r)
    assert.equal(ops.filter(op => op === 'comparison-users').length, 1)
    assert.ok(ops.indexOf('comparison-users') < ops.indexOf('comparison-job'))
  })
  const partUsers = r.evaluator ? ['cmp-arm', 'cmp-eval'] : ['cmp-arm']
  check(`${r.name}: users step 1: ${created ? `creates the system user${r.evaluator ? 's cmp-arm and cmp-eval' : ' cmp-arm (and no cmp-eval: no evaluator)'} without login shell or home` : 'existing users are not created again'}`, () => {
    const adds = r.log.filter(row => ['useradd', 'adduser'].includes(row.tool))
    if (!created) { assert.deepEqual(adds, []); return }
    if (!r.evaluator) assert.deepEqual(adds.filter(row => row.argv.includes('cmp-eval')).map(row => row.argv), [], 'cmp-eval created without an evaluator')
    for (const user of partUsers) {
      const row = adds.find(item => item.argv.at(-1) === user)
      assert.ok(row, `${user} not created`)
      assert.equal(row.ctx, 'root', `${user}: without sudo`)
      assert.ok(row.argv.includes('-r') || row.argv.includes('--system'), `${user}: not a system user: ${row.argv}`)
      assert.ok(!row.argv.includes('-m') && !row.argv.includes('--create-home'), `${user}: home created`)
      const shell = row.argv.findIndex(arg => arg === '-s' || arg === '--shell')
      const shellValue = shell >= 0 ? row.argv[shell + 1] : (row.argv.find(arg => arg.startsWith('--shell=')) ?? '').slice(8)
      assert.match(shellValue, /(nologin|\/false)$/, `${user}: login shell`)
    }
  })
  const ruleOf = row => {
    const a = row.argv.filter(arg => arg !== '-w' && arg !== '--wait')
    const op = a.findIndex(arg => ['-A', '-I', '-C', '--append', '--insert', '--check'].includes(arg))
    if (op < 0) return null
    const spec = a.slice(op + 1)
    // An insert position after the chain is not part of the rule.
    if (['-I', '--insert'].includes(a[op]) && /^\d+$/.test(spec[1] ?? '')) spec.splice(1, 1)
    return { op: a[op], spec }
  }
  check(`${r.name}: users step 2: an owner-match rule rejects cmp-arm's outgoing packets except on lo, in iptables and ip6tables`, () => {
    for (const tool of ['iptables', 'ip6tables']) {
      const add = r.log.find(row => row.tool === tool && ['-A', '-I', '--append', '--insert'].includes(ruleOf(row)?.op))
      assert.ok(add, `${tool}: no rule added`)
      assert.equal(add.ctx, 'root', `${tool}: without sudo`)
      const spec = ruleOf(add).spec
      assert.equal(spec[0], 'OUTPUT', `${tool} chain`)
      const owner = spec.indexOf('--uid-owner')
      assert.ok(owner > 0 && ['cmp-arm', '64901'].includes(spec[owner + 1]), `${tool}: no --uid-owner cmp-arm: ${spec}`)
      assert.ok(spec.includes('owner'), `${tool}: no owner match`)
      const out = spec.findIndex((arg, i) => arg === '!' && ['-o', '--out-interface'].includes(spec[i + 1]) && spec[i + 2] === 'lo')
      assert.ok(out >= 0, `${tool}: loopback not excepted: ${spec}`)
      assert.equal(spec[spec.indexOf('-j') + 1], 'REJECT', `${tool}: target`)
    }
  })
  check(`${r.name}: users step 3: the shared run directory loses group and other write and gains o+rX (chmod -R go-w,o+rX)`, () => {
    const want = { 'data/wide.txt': '644', 'data/tool.sh': '745', 'data/closed': '705', 'data/closed/inner.txt': '604', 'data/groupw': '755', 'bin/solver-1.0': '755' }
    for (const [file, mode] of Object.entries(want)) assert.equal(modeOf(path.join(S, file)), mode, file)
  })
  check(`${r.name}: users step 4: profiler/cmp_writable.json maps each user to the sorted directories printed by sudo -n -u <user> find / \\( -path /proc -o -path /sys -o -path <S> \\) -prune -o -type d -writable -print`, () => {
    assert.deepEqual(read(path.join(S, 'profiler', 'cmp_writable.json')), Object.fromEntries(partUsers.map(user => [user, [...r.writable[user]].sort()])))
    for (const user of partUsers) {
      const row = r.log.find(item => item.tool === 'find' && item.ctx === user && item.argv.includes('-writable'))
      assert.ok(row, `${user}: no listing`)
      const shared = row.argv[9], print = row.argv.at(-1)
      assert.ok(shared === S || shared === escapePath(S), `${user}: -path ${shared}`)
      // -print0 lists the same directories, NUL-separated.
      assert.ok(print === '-print' || print === '-print0', `${user}: ${print}`)
      assert.deepEqual(row.argv, ['/', '(', '-path', '/proc', '-o', '-path', '/sys', '-o', '-path', shared, ')', '-prune', '-o', '-type', 'd', '-writable', print], user)
      assert.ok(r.log.some(item => item.tool === 'sudo' && item.target === user && item.cmd[0] === 'find' && item.argv.includes('-n')), `${user}: listing not through sudo -n -u`)
    }
  })
  if (!r.evaluator) {
    check(`${r.name}: without an evaluator, users steps 5 to 7 do not run: no cmp-private, no fetch_private.sh, no chown to cmp-eval`, () => {
      assert.ok(!r.log.some(row => row.tool === 'sudo' && (row.cmd ?? []).some(arg => /fetch_private\.sh$/.test(arg))), 'fetch_private.sh ran')
      assert.ok(!r.log.some(row => row.tool === 'chown' && row.argv.some(arg => /cmp-eval|cmp-private/.test(arg))), 'chown to cmp-eval or of cmp-private')
      assert.ok(!r.log.some(row => row.tool === 'install' && row.argv.some(arg => /cmp-private/.test(arg))), 'cmp-private created')
      assert.equal(fs.existsSync(path.join(S, 'cmp-private')), false)
    })
    check(`${r.name}: without an evaluator, users step 8: nvidia-smi -L as cmp-arm, iptables -C and ip6tables -C of the added rules; no test -r of cmp-private; users, rules, listing, checks in order`, () => {
      const nvidia = sudoTo('cmp-arm', cmd => JSON.stringify(cmd) === '["nvidia-smi","-L"]')
      const listing = idx(row => row.tool === 'find' && row.argv.includes('-writable'))
      const user = created ? idx(row => ['useradd', 'adduser'].includes(row.tool)) : 0
      const rule = idx(row => row.tool === 'iptables' && ['-A', '-I', '--append', '--insert'].includes(ruleOf(row)?.op))
      before(user, rule, 'users before rules'); before(rule, listing, 'rules before the listing'); before(listing, nvidia, 'listing before nvidia-smi -L')
      assert.equal(sudoTo('cmp-arm', cmd => cmd[0] === 'test'), -1, 'test -r without cmp-private')
      for (const tool of ['iptables', 'ip6tables']) {
        const add = r.log.find(row => row.tool === tool && ['-A', '-I', '--append', '--insert'].includes(ruleOf(row)?.op))
        const checkAt = r.log.findLastIndex(row => row.tool === tool && ['-C', '--check'].includes(ruleOf(row)?.op) && JSON.stringify(ruleOf(row).spec) === JSON.stringify(ruleOf(add).spec))
        before(listing, checkAt, `${tool} -C of the added rule`)
      }
      const firstPart = sudoTo('cmp-arm', cmd => cmd[0] === 'env')
      before(nvidia, firstPart, 'checks before the first arm part')
    })
    return
  }
  check(`${r.name}: users step 5: fetch_private.sh runs as cmp-eval (env -i) in cmp-private with HOME and TMPDIR cmp-private/.home, which is empty and removed afterwards; then cmp-eval is cleaned up`, () => {
    const fetchAt = sudoTo('cmp-eval', cmd => cmd.at(-1) === path.join(S, 'harness', 'fetch_private.sh'))
    assert.ok(fetchAt >= 0, 'fetch_private.sh not run through sudo -u cmp-eval')
    const row = r.log[fetchAt]
    assert.deepEqual(row.cmd.slice(0, 2), ['env', '-i'])
    assert.deepEqual(envCommand(row.cmd).argv, ['bash', path.join(S, 'harness', 'fetch_private.sh')])
    assert.ok([null, path.join(S, 'cmp-private')].includes(envCommand(row.cmd).chdir), 'env -C')
    const record = read(path.join(r.caseDir, 'fetch-record.json'))
    assert.equal(record.cwd, path.join(S, 'cmp-private'))
    assert.equal(record.env.HOME, path.join(S, 'cmp-private', '.home'))
    assert.equal(record.env.TMPDIR, path.join(S, 'cmp-private', '.home'))
    assert.deepEqual(record.homeList, [])
    assert.deepEqual(Object.keys(record.env).filter(key => /^(CMP_|SUDO_)/.test(key) || key === 'FAKE_SUDO_USER'), [], 'variables the part must not get')
    const kill = r.log.slice(fetchAt).findIndex(item => item.tool === 'pkill' && item.ctx === 'root' && JSON.stringify(item.argv) === JSON.stringify(['-KILL', '-u', 'cmp-eval']))
    assert.ok(kill >= 0, 'no pkill -KILL -u cmp-eval after the fetch')
    assert.ok(r.log.slice(fetchAt).some(item => item.tool === 'find' && item.argv.includes('-delete') && item.argv.includes('cmp-eval')), 'no cleanup find for cmp-eval after the fetch')
  })
  check(`${r.name}: users step 6: cmp-private (created for cmp-eval before the fetch) is then chowned -R root:cmp-eval`, () => {
    const fetchAt = sudoTo('cmp-eval', cmd => cmd.at(-1) === path.join(S, 'harness', 'fetch_private.sh'))
    const chowns = chownRows(r).map(({ row, index }) => ({ index, ...chownOwner(row), ctx: row.ctx }))
    const privateDir = path.join(S, 'cmp-private')
    const toEval = chowns.find(item => item.owner === 'cmp-eval' && item.paths.includes(privateDir))
    const install = r.log.findIndex(row => row.tool === 'install' && row.argv.includes('cmp-eval') && row.argv.some(arg => !arg.startsWith('-') && resolveArg(row, arg) === privateDir))
    assert.ok((toEval && toEval.index < fetchAt) || (install >= 0 && install < fetchAt), 'cmp-private not given to cmp-eval before the fetch')
    const toRoot = chowns.find(item => item.owner === 'root' && item.group === 'cmp-eval' && item.recursive && item.paths.includes(privateDir))
    assert.ok(toRoot && toRoot.index > fetchAt && toRoot.ctx === 'root', 'cmp-private not chowned -R root:cmp-eval after the fetch')
  })
  check(`${r.name}: users step 8: nvidia-smi -L as each user, test -r cmp-private as cmp-arm, iptables -C and ip6tables -C, all after the fetch`, () => {
    const fetchAt = sudoTo('cmp-eval', cmd => cmd.at(-1) === path.join(S, 'harness', 'fetch_private.sh'))
    for (const user of ['cmp-arm', 'cmp-eval']) before(fetchAt, sudoTo(user, cmd => JSON.stringify(cmd) === '["nvidia-smi","-L"]'), `${user}: nvidia-smi -L`)
    const testAt = sudoTo('cmp-arm', cmd => cmd[0] === 'test' && cmd[1] === '-r')
    before(fetchAt, testAt, 'test -r as cmp-arm')
    assert.equal(resolveArg(r.log[testAt], r.log[testAt].cmd[2]).replace(/\/+$/, ''), path.join(S, 'cmp-private'), 'test -r of cmp-private')
    for (const tool of ['iptables', 'ip6tables']) {
      const add = r.log.find(row => row.tool === tool && ['-A', '-I', '--append', '--insert'].includes(ruleOf(row)?.op))
      const checkAt = r.log.findLastIndex(row => row.tool === tool && ['-C', '--check'].includes(ruleOf(row)?.op) && JSON.stringify(ruleOf(row).spec) === JSON.stringify(ruleOf(add).spec))
      before(fetchAt, checkAt, `${tool} -C of the added rule`)
    }
  })
  check(`${r.name}: users steps in order: users, rules, writable listing, fetch, chown root:cmp-eval, checks`, () => {
    const user = created ? idx(row => ['useradd', 'adduser'].includes(row.tool)) : 0
    const rule = idx(row => row.tool === 'iptables' && ['-A', '-I', '--append', '--insert'].includes(ruleOf(row)?.op))
    const listing = idx(row => row.tool === 'find' && row.argv.includes('-writable'))
    const fetchAt = sudoTo('cmp-eval', cmd => cmd.at(-1) === path.join(S, 'harness', 'fetch_private.sh'))
    const owned = chownRows(r).find(({ row }) => chownOwner(row).owner === 'root' && chownOwner(row).group === 'cmp-eval')?.index ?? -1
    const test = sudoTo('cmp-arm', cmd => cmd[0] === 'test')
    before(user, rule, 'users before rules'); before(rule, listing, 'rules before the listing'); before(listing, fetchAt, 'listing before the fetch')
    before(fetchAt, owned, 'fetch before chown'); before(owned, test, 'chown before the checks')
  })
}
// Users-step failures: evaluate fails with infra before any invocation.
function usersFailure(r, label, evidence) {
  if (!r) return
  statuses(r, [['intake', 'PASS'], ['reproduce', 'PASS'], ['evaluate', r.stage('evaluate')?.status === 'VOID' ? 'VOID' : 'FAIL'], ['takeaways', 'PASS']])
  check(`${r.name}: ${label}: evaluate fails with error_class infra (exit_code 2)`, () => {
    const evaluate = r.stage('evaluate')
    assert.ok(['FAIL', 'VOID'].includes(evaluate?.status), `status ${evaluate?.status}`)
    assert.equal(evaluate.error_class, 'infra')
    assert.equal(evaluate.exit_code, 2)
  })
  check(`${r.name}: ${label}: comparison-users ran and no invocation followed (no comparison-job, comparison or scored file)`, () => {
    const ops = comparisonOps(r)
    assert.ok(ops.includes('comparison-users'), JSON.stringify(r.ops))
    assert.deepEqual(ops.filter(op => op === 'comparison-job' || op === 'comparison'), [])
    assert.equal(fs.existsSync(path.join(r.S, 'comparison-work', 'i1')), false)
    assert.equal(fs.existsSync(path.join(r.control, 'comparison_scored.json')), false)
    assert.ok(r.log.every(row => !(row.tool === 'sudo' && row.target === 'cmp-arm' && row.cmd?.[0] === 'env')), 'an arm part ran')
  })
  check(`${r.name}: ${label}: the failing check ran`, () => evidence(r))
}

// ---- Main ---------------------------------------------------------------------------------------------------
async function inParallel(jobs, width = 6) {
  const results = new Array(jobs.length)
  let next = 0
  await Promise.all(Array.from({ length: width }, async () => {
    while (next < jobs.length) { const i = next++; results[i] = await jobs[i]() }
  }))
  return results
}

async function main() {
  try {
    for (const directory of ['m5', 'idea', 'measure']) fs.cpSync(path.join(ROOT, directory), path.join(pipeline, directory), {
      recursive: true, filter: source => !['experiments', 'raids_used.jsonl'].includes(path.basename(source)),
    })
    const fetched = r => r.log.some(row => row.tool === 'sudo' && row.target === 'cmp-eval' && /fetch_private\.sh$/.test(row.cmd?.at(-1) ?? ''))
    const [main, noeval, budget, stuck, plain, ...failed] = await inParallel([
      // Evaluator; brackets in the box root, so <S> must be escaped in the cleanup's -path patterns; the allocation
      // record gains its confirmed end before takeaways.
      () => execute('main', { design: MAIN, boxName: 'box[1]', box: 'refresh' }),
      () => execute('noeval', { design: NOEVAL, ceiling: NOEVAL.budget_s + 1 }),
      () => execute('budget', { design: BUDGET, box: 'none', utilNA: true }),
      () => execute('stuck', { design: SMALL, usersExist: true, stuck: 'cmp-arm' }),
      () => execute('plain', { design: null, stub: { profile: 'PASS', seal: 'PASS', propose: 'PASS', implement: 'PASS' } }),
      () => execute('fail-gpu-lines', { design: SMALL, gpuLines: { 'cmp-eval': 1 } }),
      () => execute('fail-private-readable', { design: SMALL, privateReadable: true }),
      () => execute('fail-rules', { design: SMALL, brokenRules: { ip6tables: true } }),
      () => execute('fail-dup-home', { design: SMALL, setupExtra: ({ privateBytes }) => `mkdir -p "$HOME/stash"\nprintf %s ${q(privateBytes)} > "$HOME/stash/copy.dat"` }),
      () => execute('fail-dup-run', { design: SMALL, setupExtra: ({ privateSecond }) => `printf %s ${q(privateSecond)} > data/copy.dat` }),
      () => execute('fail-dup-armdir', { design: SMALL, setupExtra: ({ privateBytes, world }) => `printf %s ${q(privateBytes)} > ${q(path.join(world, 'tmp', 'sub', 'copy.dat'))}` }),
      () => execute('fail-nonregular', { design: SMALL, fetchExtra: 'ln -s private.dat alias.dat' }),
      () => execute('fail-fetch', { design: SMALL, fetchExtra: 'exit 3' }),
    ])
    // Users step 1: a sealed harness file changed on the box after the upload (setup.sh runs after it).
    const tamper = file => ({ design: SMALL, setupExtra: () => `printf '\\n# changed on the box after upload\\n' >> ${q('harness/' + file)}` })
    const [tamperAdapter, tamperEvaluate, tamperVersions, leftSkip, leftCap, hide, chownFail, ipc, forged] = await inParallel([
      () => execute('tamper-adapter', tamper('arms/A1.sh')),
      () => execute('tamper-evaluate', tamper('evaluate.sh')),
      () => execute('tamper-versions', tamper('versions.sh')),
      () => execute('left-skip', { design: LEFT_SKIP }),
      () => execute('left-cap', { design: LEFT_CAP }),
      () => execute('hide', { design: HIDE }),
      () => execute('chown-fail', { design: SMALL, failChown: true }),
      () => execute('ipc', { design: SMALL, ipc: true }),
      () => execute('forged', { design: FORGED, forge: FORGERIES }),
    ])
    for (const [r, file] of [[tamperAdapter, 'harness/arms/A1.sh'], [tamperEvaluate, 'harness/evaluate.sh'], [tamperVersions, 'harness/versions.sh']]) {
      usersFailure(r, `${file} changed on the box after the upload`, value => {
        assert.deepEqual(value.log.filter(row => ['useradd', 'adduser'].includes(row.tool)).map(row => row.argv), [], 'users created before the hash check')
        const harnessRuns = value.log.filter(row => row.tool === 'sudo' && ['cmp-arm', 'cmp-eval'].includes(row.target) && (row.cmd ?? []).some(arg => /harness\//.test(arg)))
        assert.deepEqual(harnessRuns.map(row => row.cmd), [], 'a harness script ran as a part user')
      })
    }
    if (leftSkip) {
      commonChecks(leftSkip)
      check('left-skip: when the arm part used up the time left, the evaluator part is not run: eval_status "timeout", eval_rc and eval_wall_s null', () => {
        assert.ok(runCount(leftSkip) >= 1, 'no invocation')
        assert.equal(leftSkip.order[0].arm, 'A0')
        const wrap = leftSkip.wrapAt(0), job = leftSkip.jobs[0]
        assert.equal(wrap.status, 'ok', 'the arm part ends ok before left_s')
        assert.ok(armWallOf(wrap) <= job.left_s, `arm wall ${armWallOf(wrap)} with left_s ${job.left_s}`)
        assert.deepEqual([wrap.eval_status, wrap.eval_rc, wrap.eval_wall_s], ['timeout', null, null])
        const [from, to] = segment(leftSkip, 1)
        assert.deepEqual(partRows(leftSkip, from, to, 'cmp-eval', '/harness/evaluate.sh').map(({ row }) => row.cmd), [], 'the evaluator part ran')
      })
    }
    if (leftCap) {
      commonChecks(leftCap)
      check('left-cap: the wrapper caps the evaluator part by left_s minus the seconds since it started (a 5 s arm part, then an evaluator that sleeps)', () => {
        const wrap = leftCap.wrapAt(0), job = leftCap.jobs[0]
        assert.equal(leftCap.order[0].arm, 'A0')
        assert.equal(wrap.status, 'ok')
        assert.ok(armWallOf(wrap) >= 4.5, `arm wall ${armWallOf(wrap)}`)
        assert.equal(wrap.eval_status, 'timeout')
        assert.ok(typeof wrap.eval_wall_s === 'number' && wrap.eval_wall_s >= 1, `eval_wall_s ${wrap.eval_wall_s}`)
        assert.ok(armWallOf(wrap) + wrap.eval_wall_s <= job.left_s + 1.5, `parts ${armWallOf(wrap) + wrap.eval_wall_s} s with left_s ${job.left_s}`)
      })
    }
    if (hide) {
      commonChecks(hide)
      check('hide: a symbolic link in an unreadable subdirectory of out/ (A0) or in an unreadable out/ (A1) makes the invocation invalid; the evaluator does not run', () => {
        assert.equal(runCount(hide), 2)
        for (let i = 0; i < 2; i++) {
          const wrap = hide.wrapAt(i)
          assert.deepEqual([wrap.status, wrap.eval_status], ['invalid', 'skipped'], `i${i + 1} ${hide.order[i].arm}`)
        }
        assert.deepEqual(hide.log.filter(row => row.tool === 'sudo' && row.target === 'cmp-eval' && /evaluate\.sh$/.test(row.cmd?.at(-1) ?? '')).map(row => row.cmd), [])
      })
      check('hide: owner access is restored under out/ (chmod -R u+rwX): the unreadable directories are readable again', () => {
        for (let i = 0; i < 2; i++) {
          const out = path.join(hide.inv(i), 'out')
          assert.ok(fs.readdirSync(out).length > 0, `i${i + 1} out/`)
          if (hide.order[i].arm === 'A0') assert.deepEqual(fs.readdirSync(path.join(out, 'hid')), ['link'])
        }
      })
    }
    if (chownFail) {
      check('chown-fail: a failed ownership change of run/ or out/ after the arm part makes every invocation invalid; the evaluator does not run', () => {
        assert.ok(runCount(chownFail) > 0, 'no invocation')
        assert.ok(chownFail.log.some(row => row.tool === 'chown' && isBoxUser(chownOwner(row).owner) && chownOwner(row).paths.some(p => /\/comparison-work\/i\d+\/(out|run)$/.test(p))), 'no chown back to the box user')
        for (let i = 0; i < runCount(chownFail); i++) assert.deepEqual([chownFail.wrapAt(i)?.status, chownFail.wrapAt(i)?.eval_status], ['invalid', 'skipped'], `i${i + 1}`)
        assert.deepEqual(chownFail.log.filter(row => row.tool === 'sudo' && row.target === 'cmp-eval' && /evaluate\.sh$/.test(row.cmd?.at(-1) ?? '')).map(row => row.cmd), [])
        assert.equal(chownFail.stage('evaluate')?.status, 'PASS')
      })
    }
    if (ipc) {
      commonChecks(ipc)
      check('ipc: every System V shared-memory segment an arm part or an evaluator part leaves is removed before the next part runs', () => {
        const made = ipc.log.map((row, index) => ({ row, index })).filter(({ row }) => row.tool === 'ipcmk')
        assert.ok(made.some(({ row }) => row.owner === 'cmp-arm'), 'no segment of an arm part')
        assert.ok(made.some(({ row }) => row.owner === 'cmp-eval'), 'no segment of an evaluator part')
        const starts = ipc.log.map((row, index) => ({ row, index })).filter(({ row }) => row.tool === 'sudo' && row.cmd?.[0] === 'env' &&
          (/\/harness\/evaluate\.sh$/.test(row.cmd.at(-1)) || /harness\/arms\/A\d\.sh$/.test(row.cmd.at(-1)))).map(({ index }) => index)
        for (const { row, index } of made) {
          const removed = ipc.log.findIndex((item, j) => j > index && item.tool === 'ipcrm' && (item.removed ?? []).includes(row.id))
          assert.ok(removed > index, `segment ${row.id} of ${row.owner} never removed`)
          const next = starts.find(start => start > index)
          if (next !== undefined) assert.ok(removed < next, `segment ${row.id} of ${row.owner} removed only after the next part started`)
        }
      })
    }
    if (forged) {
      check('forged: comparison_compute.json: each invalid wrap.json (ok with a nonzero adapter_rc, no command rows, a negative, NaN or infinite wall, a command row with a missing or extra key, eval ok with a nonzero eval_rc) gives status invalid and null values; the valid control is used', () => {
        const compute = read(path.join(forged.agent, 'results', 'evaluate', 'comparison_compute.json'))
        assert.equal(compute.invocations.length, forged.order.length)
        compute.invocations.forEach((row, i) => {
          const job = forged.order[i], where = `row ${i + 1} ${job.arm}/${job.input}`
          if (job.input === 'f-valid') {
            assert.equal(row.status, 'ok', `${where} status (the forged valid record was not read)`)
            near(row.wall_s, 1.5, `${where} wall_s`)
            near(row.eval_wall_s, 0.25, `${where} eval_wall_s`)
            near(row.attributed_usd, 1.75 / 3600 * PRICE, `${where} attributed_usd`)
          } else invalidRow(row, where)
        })
      })
      check('forged: through the scorer, each invalid wrap.json is a missing value (void, missing_values); the valid control is supported', () => {
        const rows = read(path.join(forged.control, 'comparison_scored.json')).comparisons[0].rows
        for (const row of rows) {
          if (row.input === 'f-valid') assert.equal(row.outcome, 'supported', row.input)
          else assert.deepEqual([row.outcome, row.reason], ['void', 'missing_values'], row.input)
        }
        assert.deepEqual(rows.map(row => row.input), FORGED.inputs.map(item => item.id))
      })
    }

    if (main) {
      commonChecks(main)
      sudoPartChecks(main)
      usersChecks(main, { created: true })
      check('main: rounds: one warmup and one replicate round of all 8 (arm, input) pairs', () => {
        assert.equal(runCount(main), 16)
        assert.deepEqual(main.order.map(job => job.mode), [...Array(8).fill('warmup'), ...Array(8).fill('replicate')])
      })
      check('main: wrap.json statuses ok, failed (command, adapter), timeout and invalid (a symbolic link in out/); eval_status ok, failed, timeout, skipped', () => {
        for (let i = 0; i < runCount(main); i++) {
          const job = main.order[i], wrap = main.wrapAt(i), want = MAIN_EXPECT[`${job.arm}|${job.input}`]
          const where = `i${i + 1} ${job.arm}/${job.input}`
          assert.equal(wrap.status, want.status, where)
          assert.equal(wrap.adapter_rc, want.adapter_rc, `${where} adapter_rc`)
          assert.deepEqual(wrap.commands.map(row => row.rc), want.rcs, `${where} commands rc (stop at the first nonzero exit; null on timeout)`)
          assert.equal(wrap.eval_status, want.eval, `${where} eval_status`)
          assert.equal(wrap.eval_rc, want.eval_rc, `${where} eval_rc`)
          if (want.eval !== 'skipped') assert.ok(typeof wrap.eval_wall_s === 'number' && wrap.eval_wall_s >= 0, `${where} eval_wall_s`)
        }
      })
      check('main: the arm part times out at its timeout_s (4 s) and the evaluator part at evaluator.timeout_s (5 s); every process of the part user is killed', () => {
        for (let i = 0; i < runCount(main); i++) {
          const job = main.order[i], wrap = main.wrapAt(i)
          const armWall = wrap.adapter_wall_s + wrap.commands.reduce((sum, row) => sum + row.wall_s, 0)
          if (wrap.status === 'timeout') {
            assert.ok(armWall >= 3.5 && armWall < 25, `i${i + 1} arm wall ${armWall}`)
            const [from, to] = segment(main, i + 1)
            assert.ok(main.log.slice(from, to).some(row => row.tool === 'pkill' && row.argv.includes('cmp-arm')), `i${i + 1}: no pkill of cmp-arm`)
          } else assert.ok(armWall < 20, `i${i + 1} arm wall ${armWall}`)
          if (wrap.eval_status === 'timeout') assert.ok(wrap.eval_wall_s >= 4.5 && wrap.eval_wall_s < 25, `i${i + 1} eval wall ${wrap.eval_wall_s}`)
          assert.ok(job)
        }
      })
      check('main: job timeouts: arm_timeout_s from timeout_s (A1) or the time left in budget_s (A0, timeout_s 99999); eval_timeout_s from evaluator.timeout_s', () => {
        let previous = Infinity
        main.jobs.forEach((job, i) => {
          if (job.arm === 'A1') assert.equal(job.arm_timeout_s, MAIN.timeout_s.A1[job.input], `i${i + 1}`)
          else {
            assert.ok(job.arm_timeout_s <= MAIN.budget_s && job.arm_timeout_s > MAIN.budget_s - 900, `i${i + 1} A0 ${job.arm_timeout_s}`)
            assert.ok(job.arm_timeout_s <= previous, `i${i + 1}: the time left grew`)
            previous = job.arm_timeout_s
          }
          assert.equal(job.eval_timeout_s, 5, `i${i + 1}`)
        })
      })
      check('main: GPU-busy seconds sampled separately for the arm part and the evaluator part (0.5 per sample of the two GPUs)', () => {
        for (let i = 0; i < runCount(main); i++) {
          const wrap = main.wrapAt(i)
          const armWall = wrap.adapter_wall_s + wrap.commands.reduce((sum, row) => sum + row.wall_s, 0)
          assert.equal(wrap.gpu_busy_known, true, `i${i + 1}`)
          assert.ok(wrap.gpu_busy_s >= SAMPLE && Number.isInteger(wrap.gpu_busy_s / SAMPLE) && wrap.gpu_busy_s <= SAMPLE * (armWall + 3), `i${i + 1} gpu_busy_s ${wrap.gpu_busy_s} (wall ${armWall})`)
          if (wrap.eval_status !== 'skipped') {
            assert.equal(wrap.eval_gpu_busy_known, true, `i${i + 1} eval`)
            assert.ok(wrap.eval_gpu_busy_s >= SAMPLE && Number.isInteger(wrap.eval_gpu_busy_s / SAMPLE) && wrap.eval_gpu_busy_s <= SAMPLE * (wrap.eval_wall_s + 3), `i${i + 1} eval_gpu_busy_s ${wrap.eval_gpu_busy_s}`)
          }
        }
      })
      check('main: the fetched eval/ holds the evaluator\'s files; its standard output is not in the arm\'s logs', () => {
        for (let i = 0; i < runCount(main); i++) {
          const wrap = main.wrapAt(i), at = main.fetched(main.order[i])
          if (wrap.eval_status === 'ok') assert.equal(fs.readFileSync(path.join(at, 'eval', 'score.json'), 'utf8'), '{"score": 1}\n', `i${i + 1}`)
          if (wrap.eval_status === 'skipped') assert.deepEqual(fs.readdirSync(path.join(at, 'eval')), [], `i${i + 1}`)
          for (const name of fs.readdirSync(path.join(at, 'log')).filter(item => !item.startsWith('evaluator.')))
            assert.ok(!fs.readFileSync(path.join(at, 'log', name), 'utf8').includes('evaluated'), `i${i + 1} log/${name}`)
        }
      })
      check('main: scorer output: K1 (exact agreement per input) supported on case-1 and void elsewhere; totals', () => {
        const scored = read(path.join(main.control, 'comparison_scored.json'))
        const k1 = scored.comparisons[0]
        assert.equal(k1.outcome, 'per_input')
        assert.deepEqual(k1.rows.map(row => [row.input, row.outcome]), [['case-1', 'supported'], ['case_2.b', 'void'], ['case-3', 'void'], ['case-4', 'void']])
        assert.deepEqual(scored.totals, { supported: 1, not_supported: 0, inconclusive: 0, void: 3 })
      })
      check('main: the cmp_users.sh, cmp_system.py and cmp_wrap.py the pipeline writes are on the box under profiler/', () => {
        for (const file of ['cmp_users.sh', 'cmp_system.py', 'cmp_wrap.py']) assert.ok(fs.existsSync(path.join(main.S, 'profiler', file)), file)
      })
    }

    if (noeval) {
      commonChecks(noeval)
      // Separated users run for every comparison: cmp-arm only, without an evaluator.
      sudoPartChecks(noeval)
      usersChecks(noeval, { created: true })
      check('noeval: without an evaluator, comparison-users still runs once, before the first invocation, and every arm part runs as cmp-arm', () => {
        const ops = comparisonOps(noeval)
        assert.equal(ops.filter(op => op === 'comparison-users').length, 1, JSON.stringify(ops))
        assert.ok(ops.indexOf('comparison-users') < ops.indexOf('comparison-job'))
        const adapters = noeval.log.filter(row => row.tool === 'sudo' && /harness\/arms\/A\d\.sh$/.test(row.cmd?.at(-1) ?? ''))
        assert.equal(adapters.length, runCount(noeval))
        assert.ok(adapters.every(row => row.target === 'cmp-arm'), 'an adapter not run as cmp-arm')
        const solver = noeval.log.filter(row => row.tool === 'sudo' && row.cmd?.[0] === 'env' && envCommand(row.cmd).argv[0] === 'bin/solver')
        assert.equal(solver.length, runCount(noeval))
        assert.ok(solver.every(row => row.target === 'cmp-arm'), 'a command not run as cmp-arm')
      })
      check('noeval: two warmup rounds (w1, w2) and two replicate rounds of three arms, every invocation ok and eval skipped', () => {
        assert.equal(runCount(noeval), 12)
        assert.deepEqual(noeval.order.map(job => `${job.mode[0]}${job.round}`), ['w1', 'w1', 'w1', 'w2', 'w2', 'w2', 'r1', 'r1', 'r1', 'r2', 'r2', 'r2'])
        for (let i = 0; i < 12; i++) {
          const wrap = noeval.wrapAt(i)
          assert.deepEqual([wrap.status, wrap.adapter_rc, wrap.commands.map(row => row.rc), wrap.eval_status, wrap.eval_rc], ['ok', 0, [0], 'skipped', null], `i${i + 1}`)
        }
      })
      check('noeval: arm_timeout_s is the smallest of timeout_s, the time left in budget_s and the time left before the run ceiling', () => {
        noeval.jobs.forEach((job, i) => {
          const written = fs.statSync(path.join(noeval.S, 'comparison-jobs', `i${i + 1}.json`)).mtimeMs
          const ceilingLeft = NOEVAL.budget_s + 1 - (written - runStartBound(noeval)) / 1000
          if (job.arm === 'A0') assert.equal(job.arm_timeout_s, 600, `i${i + 1}`)
          if (job.arm === 'A2') assert.equal(job.arm_timeout_s, 7, `i${i + 1}`)
          if (job.arm === 'A1') assert.ok(job.arm_timeout_s > 0 && job.arm_timeout_s <= ceilingLeft + 5, `i${i + 1}: ${job.arm_timeout_s} above the time left before the ceiling (${ceilingLeft})`)
        })
      })
      check('noeval: GPU-busy seconds of the arm part are sampled', () => {
        for (let i = 0; i < runCount(noeval); i++) {
          const wrap = noeval.wrapAt(i)
          assert.equal(wrap.gpu_busy_known, true)
          assert.ok(wrap.gpu_busy_s >= SAMPLE && Number.isInteger(wrap.gpu_busy_s / SAMPLE), `i${i + 1} ${wrap.gpu_busy_s}`)
        }
      })
      check('noeval: scorer output with no comparison: empty comparisons, zero totals', () => {
        const scored = read(path.join(noeval.control, 'comparison_scored.json'))
        assert.deepEqual(scored.comparisons, [])
        assert.deepEqual(scored.totals, { supported: 0, not_supported: 0, inconclusive: 0, void: 0 })
      })
    }

    if (budget) {
      commonChecks(budget)
      check('budget: A0 runs, A1\'s sleep times out at the time left in budget_s, and the rest are not run (no job file, status not_run)', () => {
        assert.equal(runCount(budget), 2, `run ${runCount(budget)}`)
        assert.deepEqual([budget.order[0].arm, budget.order[1].arm], ['A0', 'A1'])
        assert.equal(budget.wrapAt(0).status, 'ok')
        const timed = budget.wrapAt(1)
        assert.equal(timed.status, 'timeout')
        assert.deepEqual(timed.commands.map(row => row.rc), [null])
        assert.ok(budget.jobs[1].arm_timeout_s <= BUDGET.budget_s && budget.jobs[1].arm_timeout_s >= 1, `arm_timeout_s ${budget.jobs[1].arm_timeout_s}`)
        const wall = timed.adapter_wall_s + timed.commands.reduce((sum, row) => sum + row.wall_s, 0)
        assert.ok(Math.abs(wall - budget.jobs[1].arm_timeout_s) < 5, `wall ${wall} vs timeout ${budget.jobs[1].arm_timeout_s}`)
        const compute = read(path.join(budget.agent, 'results', 'evaluate', 'comparison_compute.json'))
        assert.deepEqual(compute.invocations.map(row => row.status), ['ok', 'timeout', 'not_run', 'not_run', 'not_run', 'not_run'])
      })
      check('budget: without utilization samples, gpu_busy_known is false and gpu_busy_s 0', () => {
        for (let i = 0; i < runCount(budget); i++) assert.deepEqual([budget.wrapAt(i).gpu_busy_known, budget.wrapAt(i).gpu_busy_s], [false, 0], `i${i + 1}`)
      })
    }

    if (stuck) {
      commonChecks(stuck)
      sudoPartChecks(stuck)
      usersChecks(stuck, { created: false })
      check('stuck: processes of cmp-arm still left after the cleanup (for the rest of budget_s) make the invocation invalid; the rest are not run', () => {
        assert.equal(runCount(stuck), 1)
        const wrap = stuck.wrapAt(0)
        assert.equal(wrap.status, 'invalid')
        assert.equal(wrap.eval_status, 'skipped')
        const [from, to] = segment(stuck, 1)
        assert.ok(stuck.log.slice(from, to).filter(row => row.tool === 'pkill' && row.argv.includes('cmp-arm')).length >= 2, 'pkill not repeated')
        const compute = read(path.join(stuck.agent, 'results', 'evaluate', 'comparison_compute.json'))
        assert.deepEqual(compute.invocations.map(row => row.status), ['invalid', 'not_run', 'not_run', 'not_run'])
      })
    }

    if (plain) {
      check('plain: workflow reaches evaluate without args.comparison', () => assert.ok(plain.stage('evaluate'), 'no evaluate record'))
      check('plain: without args.comparison evaluate keeps its facts and runs no comparison operation or file', () => {
        assert.deepEqual(Object.keys(plain.stage('evaluate').facts).filter(key => FACTS.includes(key)).sort(), [...FACTS].sort())
        assert.deepEqual(comparisonOps(plain), [])
        for (const file of ['control/comparison_scored.json', 'agent/results/evaluate/comparison_compute.json', 'agent/results/evaluate/comparison'])
          assert.equal(fs.existsSync(path.join(plain.root, file)), false, file)
        assert.deepEqual(plain.log.filter(row => row.tool === 'sudo'), [])
      })
      check('plain: without args.comparison boxrun\'s remote files are as before: under umask 022 each command\'s log and exit status are created readable (644)', () => {
        const names = fs.readdirSync(plain.S, { withFileTypes: true }).filter(entry => entry.isFile()).map(entry => entry.name)
        let seen = 0
        for (const receipt of plain.receipts) for (const suffix of ['.log', '.rc']) {
          if (!names.includes(receipt.name + suffix)) continue
          seen++
          assert.equal(modeOf(path.join(plain.S, receipt.name + suffix)), '644', receipt.name + suffix)
        }
        assert.ok(seen > 0, 'no remote log or exit status named after a receipt')
      })
    }

    const [gpu, readable, rules, dupHome, dupRun, dupArm, nonregular, fetchFail] = failed
    usersFailure(gpu, 'cmp-eval sees fewer GPU lines than the box user', r => {
      assert.ok(r.log.some(row => row.tool === 'sudo' && row.target === 'cmp-eval' && JSON.stringify(row.cmd) === '["nvidia-smi","-L"]'))
    })
    usersFailure(readable, 'cmp-arm can read cmp-private', r => {
      assert.ok(r.log.some(row => row.tool === 'sudo' && row.target === 'cmp-arm' && row.cmd?.[0] === 'test' && row.cmd[1] === '-r'))
    })
    usersFailure(rules, 'the ip6tables rule is missing', r => {
      assert.ok(r.log.some(row => row.tool === 'ip6tables' && (row.argv.includes('-C') || row.argv.includes('--check'))))
    })
    for (const [r, label] of [[dupHome, 'a private file is duplicated under the box user\'s home'], [dupRun, 'a private file is duplicated in the shared run directory'],
      [dupArm, 'a private file is duplicated below a directory cmp-arm can write'], [nonregular, 'cmp-private holds a symbolic link'],
      [fetchFail, 'fetch_private.sh exits nonzero']])
      usersFailure(r, label, value => assert.ok(fetched(value), 'fetch_private.sh did not run as cmp-eval'))
  } catch (error) { failures++; console.log(`FAIL test harness: ${error.stack}`) }
  finally {
    if (process.argv[3] === 'keep') console.log(`scratch kept: ${scratch}`)
    else {
      // Directories an arm part made unreadable (case hide) are opened again before the removal.
      ;(function unlock(directory) {
        try { fs.chmodSync(directory, 0o700) } catch {}
        let entries = []
        try { entries = fs.readdirSync(directory, { withFileTypes: true }) } catch { return }
        for (const entry of entries) if (entry.isDirectory()) unlock(path.join(directory, entry.name))
      })(scratch)
      fs.rmSync(scratch, { recursive: true, force: true })
    }
  }
  console.log(failures ? `${failures} failure(s) (${checks} checks)` : `all ${checks} checks passed`)
  process.exitCode = failures ? 1 : 0
}
main()
