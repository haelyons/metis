"""Anonymous HTTPS HEAD checks only; no payload downloads or logins."""
import concurrent.futures
import datetime
import json
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
records = json.loads((OUT / "records.json").read_text())

def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def check(record):
    command = ["curl", "-q", "-f", "-s", "-S", "-I", "-L",
               "--proto", "=https", "--proto-redir", "=https",
               "--connect-timeout", "10", "--max-time", "30",
               "--write-out", "\nCHECK_META %{http_code} %{url_effective} %{size_download}\n",
               record["url"]]
    start = utc()
    result = subprocess.run(command, capture_output=True, text=True, timeout=35)
    end = utc()
    output = result.stdout
    meta = output.rsplit("\nCHECK_META ", 1)[-1].strip().split()
    code = int(meta[0]) if meta and meta[0].isdigit() else 0
    return {"input": record["input"], "url": record["url"],
            "provenance": record["provenance"], "method": "anonymous HTTPS HEAD, curl -q -fsSIL",
            "started_utc": start, "completed_utc": end, "curl_exit": result.returncode,
            "http_status": code, "effective_url": meta[1] if len(meta) > 1 else None,
            "downloaded_payload_bytes": int(meta[2]) if len(meta) > 2 else None,
            "reachable": result.returncode == 0 and 200 <= code < 300,
            "headers": output.split("\nCHECK_META ", 1)[0], "stderr": result.stderr}

checks = []
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(check, r) for r in records["files"]]
    for f in concurrent.futures.as_completed(futures):
        r = f.result()
        checks.append(r)
        if not r["reachable"]:
            print(json.dumps({k: r[k] for k in ("input", "curl_exit", "http_status", "stderr")}), flush=True)
checks.sort(key=lambda r: r["input"])
(OUT / "reachability.json").write_text(json.dumps({"provenance_note": "FroDock distribution remains unverified_mirror.", "checks": checks}, indent=2) + "\n")
print(json.dumps({"locations": len(checks), "reachable": sum(r["reachable"] for r in checks),
                  "payload_bytes_downloaded": sum(r["downloaded_payload_bytes"] or 0 for r in checks),
                  "started_utc": min(r["started_utc"] for r in checks),
                  "completed_utc": max(r["completed_utc"] for r in checks)}, indent=2))
