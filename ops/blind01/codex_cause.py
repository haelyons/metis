"""Why a science step's Codex call failed, as fixed phrase counts only (no text printed)."""
import re, sys
D = f"/home/hal/dev/interp/metis/experiments/blind-{sys.argv[1]}/science/{sys.argv[2]}"
t = ""
for f in ("codex_stderr.log", "codex.jsonl"):
    try:
        t += open(f"{D}/{f}", errors="replace").read()
    except Exception:
        pass
for name, rx in {"usage_limit": r"usage limit|hit your usage", "rate_limit": r"rate[ _-]?limit|429", "auth": r"unauthori[sz]ed|401|login",
                 "timeout": r"timed? ?out", "network": r"ECONN|network error|stream disconnected", "context": r"context (length|window)"}.items():
    print(name, len(re.findall(rx, t, re.I)))
print("events", t.count('"type"'), "bytes", len(t))
