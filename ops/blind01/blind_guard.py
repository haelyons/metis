"""PreToolUse guard: keeps the operator blind to experiments/blind-01 content.

File tools may touch only the operator's own files (predictions/*.md) and the takeaway and
launcher log of a run. Grep and Glob may not search blind-01 or any directory above it.
Bash may mention blind-01 only to launch a chain, run the blind reader, or handle the
operator's own predictions files. Anything else that names blind-01 is denied.
Limit: a shell command that reaches blind-01 without naming it (a recursive grep over
experiments/, a glob) is not caught; that stays the operator's discipline.
"""
import json, os, re, sys

BLIND = "/home/hal/dev/interp/metis/experiments/blind-01"
READ_OK = [r"/m5/predictions/[\w.-]+\.md", r"/m5/run\d+/operator/OPERATOR_TAKEAWAY\.md",
           r"/m5/run\d+/devbox_up\.log"]
WRITE_OK = [r"/m5/predictions/[\w.-]+\.md"]
BASH_OK = [
    r"^bash ~/\.cache/blind01/retry\d+\.sh " + re.escape(BLIND) + r"/m5/run\d+ ",
    r"^python3 (~|/home/hal)/\.cache/blind01/blind_read\.py " + re.escape(BLIND) + r"/m5/run\d+$",
    r"^python3 (~|/home/hal)/\.cache/blind01/new_run\.py " + re.escape(BLIND) + r"/m5/run\d+( --addendum(=intake_check_codex|=intake_acquire)?)?$",
    r"^bash ~/\.cache/blind01/commit_run\.sh " + re.escape(BLIND) + r"/m5/run\d+ ",
]
TOKEN = re.compile(r"[^\s'\"=;|&()<>]*blind-01[^\s'\"=;|&()<>]*")


def decide(data):
    tool, inp = data.get("tool_name"), data.get("tool_input") or {}
    if tool in ("Read", "Edit", "Write", "NotebookEdit"):
        path = os.path.abspath(os.path.expanduser(inp.get("file_path") or inp.get("notebook_path") or ""))
        if not path.startswith(BLIND):
            return None
        rules = READ_OK if tool == "Read" else WRITE_OK
        return None if any(re.fullmatch(re.escape(BLIND) + r, path) for r in rules) else "file outside the blind allowlist"
    if tool in ("Grep", "Glob"):
        base = os.path.abspath(os.path.expanduser(inp.get("path") or data.get("cwd") or os.getcwd()))
        text = " ".join(str(v) for v in inp.values())
        if base == BLIND or base.startswith(BLIND + "/") or BLIND.startswith(base + "/") or "blind-01" in text:
            return "search would cover blind-01; narrow the path (for example metis/dut/pipeline)"
        return None
    if tool == "Bash":
        cmd = (inp.get("command") or "").strip()
        cwd = data.get("cwd") or ""
        in_blind = cwd == BLIND or cwd.startswith(BLIND + "/")
        if "blind-01" not in cmd and not in_blind:
            return None
        # The bare word "blind-01" (a commit message, a chain message) touches no file; any path naming it must be allowlisted.
        paths = [t for t in TOKEN.findall(cmd) if t != "blind-01"]
        body = re.sub(r"^cd [^;&]+&& *", "", cmd)
        if not in_blind and any(re.match(p, body) for p in BASH_OK) \
                and all(re.fullmatch(re.escape(BLIND) + r"/m5/run\d+", t) for t in paths):
            return None
        if not in_blind and re.match(r"^(cd [^;&]+&& *)?git (add|commit|push|ls-remote|rev-parse|log --oneline)", cmd) \
                and all(re.search(r"experiments/blind-01/m5/predictions/[\w.-]+\.md$", t) for t in paths):
            return None
        return "command names blind-01 outside the allowlist; use ~/.cache/blind01/blind_read.py <run_root>"
    return None


raw = sys.stdin.read()
try:
    reason = decide(json.loads(raw))
except Exception:
    reason = "guard could not parse the call" if "blind-01" in raw else None
if reason:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": "blind guard: " + reason}}))
