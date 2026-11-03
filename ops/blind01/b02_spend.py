"""Box spend against the owner's combined ceiling for blind-02's calibration and main runs (owner 2026-11-03: USD 100,
including setup, failed attempts and idle time). Counts whole allocations, not a run's share: every box allocation
started at or after the ledger start, from start to termination (the archived state's name carries the termination
time), plus a live allocation up to now, at its hourly price. Prints totals only.
Usage: python3 ~/.cache/blind01/b02_spend.py [--need <usd>]   (exit 3 when spent + need would pass the ceiling)
"""
import datetime as dt, glob, json, os, re, sys

START, CEILING = dt.datetime(2026, 11, 3, 11, 30, tzinfo=dt.timezone.utc), 100.0
C = os.path.expanduser("~/.cache/metis-serve")
t = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
now = dt.datetime.now(dt.timezone.utc)
rows = []
for f in glob.glob(f"{C}/state.*.json"):
    m = re.search(r"\.(\d{8}T\d{6}Z)\.json$", f)
    d = json.load(open(f))
    end = dt.datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=dt.timezone.utc)
    rows.append((t(d["started_utc"]), end, float(d["price_usd_h"]), False))
if os.path.exists(f"{C}/state.json"):
    d = json.load(open(f"{C}/state.json"))
    rows.append((t(d["started_utc"]), now, float(d["price_usd_h"]), True))
rows = [r for r in rows if r[0] >= START]
hours = sum((e - s).total_seconds() / 3600 for s, e, _, _ in rows)
usd = sum((e - s).total_seconds() / 3600 * p for s, e, p, _ in rows)
need = float(sys.argv[sys.argv.index("--need") + 1]) if "--need" in sys.argv else 0.0
print(f"allocations {len(rows)} (live {sum(r[3] for r in rows)}) hours {hours:.2f} spent USD {usd:.2f} of {CEILING:.0f}; "
      f"left {CEILING - usd:.2f}" + (f"; need {need:.2f}: {'OK' if usd + need <= CEILING else 'OVER'}" if need else ""))
sys.exit(3 if usd + need > CEILING else 0)
