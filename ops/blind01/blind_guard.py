"""PreToolUse guard: keeps the operator blind to the content of every blind experiment (experiments/blind-NN:
blind-01, blind-02 and any later one).

File tools may touch only the operator's own files (predictions/*.md) and the takeaway and
launcher log of a run. Grep and Glob may not search a blind experiment or any directory above it.
Bash may mention a blind experiment only to launch a chain, run the blind reader, create a run, or handle
the operator's own predictions files. Anything else that names one is denied.
Limit: a shell command that reaches a blind experiment without naming it (a recursive grep over
experiments/, a glob) is not caught; that stays the operator's discipline.
"""
import json, os, re, sys

EXP = "/home/hal/dev/interp/metis/experiments"
NAME = r"blind-\d\d"
BLIND = re.escape(EXP) + "/" + NAME
READ_OK = [r"/m5/predictions/[\w.-]+\.md", r"/m5/run\d+/operator/OPERATOR_TAKEAWAY\.md",
           r"/m5/run\d+/devbox_up\.log"]
WRITE_OK = [r"/m5/predictions/[\w.-]+\.md"]
BASH_OK = [
    r"^bash ~/\.cache/blind01/retry\d+\.sh " + BLIND + r"/m5/run\d+ ",
    r"^python3 (~|/home/hal)/\.cache/blind01/blind_read\.py " + BLIND + r"/m5/run\d+$",
    r"^python3 (~|/home/hal)/\.cache/blind01/new_run\.py " + BLIND + r"/m5/run\d+( --addendum(=intake_check_codex|=intake_acquire|=intake_mirror|=b01_materials)?| --brief-from=s\d\d)?"
    r"( --harness-from=[A-Za-z0-9_]+)?( --stop-after-(profile|reproduce))?( --units-(check|probe)=run\d+)?$",
    r"^bash ~/\.cache/blind01/commit_run\.sh " + BLIND + r"/m5/run\d+ ",
]
TOKEN = re.compile(r"[^\s'\"=;|&()<>]*" + NAME + r"[^\s'\"=;|&()<>]*")


def blind_dir(path):
    """The blind experiment directory at or above path, or None."""
    m = re.match(BLIND + r"(?=/|$)", path)
    return m.group(0) if m else None


def decide(data):
    tool, inp = data.get("tool_name"), data.get("tool_input") or {}
    if tool in ("Read", "Edit", "Write", "NotebookEdit"):
        path = os.path.abspath(os.path.expanduser(inp.get("file_path") or inp.get("notebook_path") or ""))
        if not blind_dir(path):
            return None
        rules = READ_OK if tool == "Read" else WRITE_OK
        return None if any(re.fullmatch(BLIND + r, path) for r in rules) else "file outside the blind allowlist"
    if tool in ("Grep", "Glob"):
        base = os.path.abspath(os.path.expanduser(inp.get("path") or data.get("cwd") or os.getcwd()))
        text = " ".join(str(v) for v in inp.values())
        if blind_dir(base) or (EXP + "/").startswith(base.rstrip("/") + "/") or re.search(NAME, text):
            return "search would cover a blind experiment; narrow the path (for example metis/dut/pipeline)"
        return None
    if tool == "Bash":
        cmd = (inp.get("command") or "").strip()
        in_blind = bool(blind_dir(data.get("cwd") or ""))
        if not re.search(NAME, cmd) and not in_blind:
            return None
        # The bare word "blind-NN" (a commit message, a chain message) touches no file; any path naming one must be allowlisted.
        paths = [t for t in TOKEN.findall(cmd) if not re.fullmatch(NAME, t)]
        body = re.sub(r"^cd [^;&]+&& *", "", cmd)
        if not in_blind and any(re.match(p, body) for p in BASH_OK) \
                and all(re.fullmatch(BLIND + r"/m5/run\d+", t) for t in paths):
            return None
        if not in_blind and re.match(r"^(cd [^;&]+&& *)?git (add|commit|push|ls-remote|rev-parse|log --oneline)", cmd) \
                and all(re.search(r"experiments/" + NAME + r"/m5/predictions/[\w.-]+\.md$", t) for t in paths):
            return None
        return "command names a blind experiment outside the allowlist; use ~/.cache/blind01/blind_read.py <run_root>"
    return None


raw = sys.stdin.read()
try:
    reason = decide(json.loads(raw))
except Exception:
    reason = "guard could not parse the call" if re.search(NAME, raw) else None
if reason:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": "blind guard: " + reason}}))
