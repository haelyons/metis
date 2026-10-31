"""After an authorized reader: validate its status files, scan for secrets, commit and push its folder. Prints only
validated enum statuses, an addendum prefix check, an independence-order check, counts, the agent's cost or tokens,
and push status; never file names or agent text.

Usage: python3 ~/.cache/blind01/intake_check_post.py [--dir intake_check|intake_check_codex|intake_acquire|intake_mirror|run5_diag|run6_diag|run6_diag2|run6_diag3|run7_diag|run7_diag2] [--transcript NAME] [--check-only]
"""
import argparse, json, os, re, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("--dir", default="intake_check", choices=["intake_check", "intake_check_codex", "intake_acquire", "intake_mirror", "run5_diag", "run6_diag", "run6_diag2", "run6_diag3", "run7_diag", "run7_diag2"])
ap.add_argument("--transcript", default="transcript.jsonl", choices=["transcript.jsonl", "codex.jsonl"])
ap.add_argument("--check-only", action="store_true")
a = ap.parse_args()

M = "/home/hal/dev/interp/metis"
D = "experiments/blind-01/m5/" + a.dir
P = os.path.join(M, D)
ENUMS = {
    "prerequisite": {"data", "licence_evidence", "data_and_licence_evidence", "other", "none_found"},
    "cause": {"transient_unreachable", "source_moved", "gated_access", "source_choice", "materials_missing", "other"},
    "materials_usable": {True, False},
    "run5_brief": {"addendum", "original"},
    "owner_action": {"none", "supply_materials", "obtain_access", "decide"},
}
if a.dir != "intake_check":
    ENUMS["alternative"] = {"none", "official_new_location", "archive_snapshot", "author_deposit", "verified_mirror",
                            "unverified_mirror"} | ({"regenerated_official"} if a.dir in ("intake_acquire", "intake_mirror") else set())
if a.dir == "run5_diag":
    ENUMS = {
        "failed_step": {"probe", "harness_agent", "harness_upload", "setup", "other", "unknown"},
        "upload_error": {"e2big", "other", "none", "unknown"},
        "upload_command_bytes": {"under_128k", "over_128k", "unknown"},
        "large_content": {"embedded_hashes", "embedded_data", "other", "not_large"},
        "hash_checks_requested": {True, False},
    }
if a.dir == "run6_diag":
    ENUMS = {
        "failure_point": {"script_error", "probe_paths", "missing_tool", "fetch_materials", "hash_mismatch", "build", "other", "unknown"},
        "same_cause_all_attempts": {True, False},
        "tail_had_cause": {"all", "some", "none", "unknown"},
        "repairs_targeted_cause": {"all", "some", "none", "unknown"},
        "mirror_from_box": {"reached_ok", "reached_failed", "not_reached", "unknown"},
        "fix_needs": {"harness_repair", "pipeline_repair_inputs", "materials", "brief", "box_image", "unknown"},
    }
if a.dir == "run6_diag2":
    ENUMS = {
        "tool_kind": {"downloader", "archive", "hash", "build", "cuda", "python_package", "other", "unknown"},
        "installable": {"apt_listed_source", "pip", "apt_unlisted_source", "not_installable", "unknown"},
        "rules_allow_fix": {"yes", "no", "unclear", "unknown"},
        "repair_lacked": {"probe_fact", "permission", "log_context", "nothing", "unknown"},
        "smallest_fix": {"probe_reports_tool", "rules_permit_install", "rules_clarify", "repair_prompt_context", "box_image", "unknown"},
    }
if a.dir == "run6_diag3":
    ENUMS = {
        "ubuntu_archive": {"main", "universe", "no", "unknown"},
        "pypi": {"yes", "no", "unknown"},
        "role": {"fetch_or_unpack", "build", "runtime_library", "other", "unknown"},
        "changes_stock_python": {"yes", "no", "unknown"},
    }
if a.dir == "run7_diag":
    point = {"script_error", "probe_paths", "missing_tool", "apt_install", "fetch_materials", "hash_mismatch", "build", "other", "unknown"}
    ENUMS = {
        "attempt1_point": point,
        "attempt2_point": point,
        "attempt3_point": point,
        "run6_library": {"installed_apt", "installed_other", "present_already", "not_needed", "failed", "unknown"},
        "furthest_phase": {"tool_install", "fetch_materials", "hash_check", "build", "smoke_or_anchor_prep", "other", "unknown"},
        "repair_regressed": {"yes", "no", "unknown"},
        "tail_had_cause": {"all", "some", "none", "unknown"},
        "repairs_targeted_cause": {"all", "some", "none", "unknown"},
        "mirror_from_box": {"reached_ok", "reached_failed", "not_reached", "unknown"},
        "hash_checks": {"all_passed", "some_failed", "not_reached", "unknown"},
        "fix_needs": {"harness_repair", "pipeline_repair_inputs", "pipeline_rules", "materials", "brief", "box_image", "unknown"},
    }
if a.dir == "run7_diag2":
    kind = {"syntax", "unbound_variable", "wrong_path", "command_usage", "control_flow", "environment", "other", "unknown"}
    ENUMS = {
        "error_kind_1": kind,
        "error_kind_2": kind,
        "error_kind_3": kind,
        "distinct_errors": {"all_distinct", "some_repeat", "same", "unknown"},
        "static_catch": {"all", "some", "none", "unknown"},
        "rule_induced": {"yes", "no", "unknown"},
        "rerun_refetches": {"yes", "partly", "no", "unknown"},
        "third_fix_outlook": {"likely_passes_setup", "likely_another_error", "unknown"},
        "smallest_fix": {"more_repairs", "static_check_before_upload", "harness_prompt_rule", "repair_prompt_context", "setup_split", "unknown"},
    }
if a.dir == "intake_mirror":
    ENUMS["hashes_recorded"] = {True, False}
    ENUMS["refetch"] = {"match", "mismatch", "unreachable", "not_done"}


def git(*args):
    return subprocess.run(["git", "-C", M, *args], capture_output=True, text=True)


def load(name):
    try:
        s = json.load(open(os.path.join(P, name)))
        ok = isinstance(s, dict) and set(s) == set(ENUMS) and all(
            type(s[k]) is type(next(iter(v))) and s[k] in v for k, v in ENUMS.items())
    except Exception:
        s, ok = None, False
    return (s if ok else None)


status = load("status.json")
print("STATUS " + json.dumps(status, sort_keys=True) if status else "STATUS_INVALID")
if a.check_only:
    raise SystemExit(0)
if a.dir == "intake_check_codex":
    independent = load("status_independent.json")
    print("INDEPENDENT " + json.dumps(independent, sort_keys=True) if independent else "INDEPENDENT_INVALID")

addendum = os.path.join(P, "BRIEF_run5.md")
if a.dir in ("run5_diag", "run6_diag", "run6_diag2", "run6_diag3", "run7_diag", "run7_diag2"):
    pass
elif os.path.exists(addendum):
    original = open(os.path.join(M, "experiments/blind-01/m5/BRIEF.md"), "rb").read()
    text = open(addendum, "rb").read()
    print("addendum present; starts with original brief:", text.startswith(original) and len(text) > len(original),
          "; status agrees:", bool(status) and status["run5_brief"] == "addendum")
    if a.dir == "intake_mirror":
        extra = text[len(original):]
        print("addendum section heading:", b"## Materials (owner decision 2026-10-31; recorded by an authorized reader agent)" in extra,
              "; names unverified_mirror:", b"unverified_mirror" in extra,
              "; sha256 values:", len(set(re.findall(rb"\b[0-9a-f]{64}\b", extra))))
else:
    print("addendum absent; status agrees:", bool(status) and status["run5_brief"] == "original")

try:
    rows = [json.loads(line) for line in open(os.path.join(P, a.transcript)) if line.strip()]
    if a.transcript == "codex.jsonl":
        usage = [r.get("usage") or {} for r in rows if r.get("type") == "turn.completed"]
        print("agent turns", len(usage), "tokens_in", sum(u.get("input_tokens", 0) for u in usage),
              "tokens_out", sum(u.get("output_tokens", 0) for u in usage))
        # Phase A must write status_independent.json before any command or edit touches the Opus reader's folder.
        # Only the command text and edited paths count, not command output (a listing may name the folder).
        items = [r.get("item") or {} for r in rows if r.get("type") == "item.completed"]
        acts = [it.get("command", "") if it.get("type") == "command_execution" else json.dumps(it.get("changes"))
                for it in items if it.get("type") in ("command_execution", "file_change")]
        opus = next((i for i, t in enumerate(acts) if re.search(r"intake_check/", t)), None)
        wrote = next((i for i, t in enumerate(acts) if "status_independent.json" in t), None)
        if a.dir == "intake_check_codex":
            print("independent status written before touching the Opus reader's folder:",
                  "unknown" if wrote is None else (opus is None or wrote < opus))
    else:
        last = rows[-1]
        print("agent turns", last.get("num_turns"), "usd", round(last.get("total_cost_usd") or 0, 2),
              "error", last.get("is_error"))
except Exception:
    print("agent result unreadable")

keys = []
for line in open("/home/hal/dev/interp/dm_hack/.keys"):
    line = line.strip()
    if "=" in line and not line.startswith("#"):
        value = line.split("=", 1)[1].strip().strip("'\"")
        if len(value) >= 12:
            keys.append(value.encode())
TOKEN = re.compile(rb"(sk-[A-Za-z0-9_-]{20,}|hf_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"
                   rb"|secret_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|Bearer [A-Za-z0-9._-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY)")
keep, held = [], 0
for root, _, names in os.walk(P):
    for name in names:
        f = os.path.join(root, name)
        data = open(f, "rb").read()
        if os.path.getsize(f) > 95 * 1024 * 1024 or any(k in data for k in keys) or TOKEN.search(data):
            held += 1
        else:
            keep.append(os.path.relpath(f, M))
print("files to commit", len(keep), "held back (secret pattern or >95 MB)", held)
if keep:
    git("add", "-f", "--", *keep)
    c = git("commit", "-q", "-m", f"blind-01 m5: authorized {a.dir.replace('_', ' ')} (reader agent; operator sees enum status only)\n\n"
            "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
            "Claude-Session: https://claude.ai/code/session_01R9EPikyZNGLiuyGF2iw3X3")
    git("push", "-q", "origin", "main")
    git("fetch", "-q", "origin")
    head, remote = git("rev-parse", "HEAD").stdout.strip(), git("rev-parse", "origin/main").stdout.strip()
    print("PUSH_OK " + head[:8] if c.returncode == 0 and head == remote else "COMMIT_OR_PUSH_FAILED")
