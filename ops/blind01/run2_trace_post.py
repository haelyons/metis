"""After the run2_trace authorized reader: validate its status.json against the fixed enums and print only the
validated values, the agent's turn/token counts, and a secret-pattern scan count. Never file names or agent text.
No commit (the operator's commits are paused). Usage: python3 ~/.cache/blind01/run2_trace_post.py
"""
import json, os, re

P = "/home/hal/dev/interp/metis/experiments/blind-02/m5/run2_trace"
ENUMS = {
    "stop_cause": {"no_feasible_menu_method", "seal_failed", "ballots", "infra", "other", "unknown"},
    "propose_model_calls": {"none", "some", "unknown"},
    "seal_predictions": {"empty", "nonempty", "unknown"},
    "seed_question_kind": {"single_baseline_throughput", "configuration_comparison", "outcome_vs_compute", "mixed", "other", "unknown"},
    "comparisons_requested": {"none", "one", "two", "three", "four_or_more", "unknown"},
    "comparisons_at_intake": {"all", "some", "none", "unknown"},
    "comparisons_changed": {"none", "some", "all", "unknown"},
    "comparisons_measured": {"all", "some", "none", "unknown"},
    "first_drop_stage": {"intake", "reproduce", "profile", "seal", "propose", "none", "unknown"},
    "bottleneck": {"gpu_saturated", "host_bound", "io_bound", "mixed", "undetermined", "unknown"},
    "units_decomposable": {"yes", "no", "unknown"},
    "units_in_harness": {"yes", "no", "unknown"},
    "curve_could_serve": {"as_sealed", "with_arms_from_seed", "no", "unknown"},
    "smallest_intervention": {"existing_mechanism", "contract_change", "new_seed", "unknown"},
    "mechanism": {"units_probe", "per_configuration_runs", "addendum", "other_existing", "none", "unknown"},
    "calibration_box_hours": {"under_1", "1_to_3", "3_to_6", "over_6", "unknown"},
}
try:
    s = json.load(open(os.path.join(P, "status.json")))
    ok = isinstance(s, dict) and set(s) == set(ENUMS) and all(s[k] in ENUMS[k] for k in ENUMS)
    print("STATUS " + json.dumps(dict(sorted(s.items())), sort_keys=True) if ok else "STATUS_INVALID")
except Exception:
    print("STATUS_MISSING")
print("report present:", os.path.isfile(os.path.join(P, "REPORT.md")),
      "report bytes:", os.path.getsize(os.path.join(P, "REPORT.md")) if os.path.isfile(os.path.join(P, "REPORT.md")) else 0)
try:
    rows = [json.loads(l) for l in open(os.path.join(P, "codex.jsonl")) if l.strip()]
    usage = next((r for r in reversed(rows) if isinstance(r, dict) and ("usage" in r or r.get("type") == "turn.completed")), None)
    print("agent events", len(rows), "usage", json.dumps(usage.get("usage") if usage else None))
except Exception:
    print("agent transcript unreadable")
TOKEN = re.compile(rb"(sk-[A-Za-z0-9_-]{20,}|hf_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"
                   rb"|secret_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|Bearer [A-Za-z0-9._-]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY)")
held = sum(1 for root, _, names in os.walk(P) for n in names if TOKEN.search(open(os.path.join(root, n), "rb").read()))
print("files with a secret pattern:", held)
