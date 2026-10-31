"""Render complete fetch audit for the owner's report."""
import collections,datetime,json,pathlib
out=pathlib.Path(__file__).parent
rows=[json.loads(s) for s in (out/'fetch_attempts.jsonl').read_text().splitlines()]
lines=['# Fetch attempt ledger','','Every attempt issued by the audited downloader is listed below, including failures and retries. Times are UTC. Each label maps to one public source URL; payloads and response headers are in the authorized download cache. HEAD byte counts describe saved response headers, not object size. SHA-256 applies only to GET response bodies. The machine-readable ledger is `fetch_attempts.jsonl`. Browser/search discovery is listed separately in the owner report.','', '| Phase | Label | Attempt | Started (UTC) | Ended (UTC) | Method | HTTP / curl exit | Bytes received | SHA-256 | Source |','| --- | --- | ---: | --- | --- | --- | --- | ---: | --- | --- |']
for r in sorted(rows,key=lambda r:r['started']):
    lines.append('| '+' | '.join(str(x) for x in [r['phase'],r['label'],r['attempt'],r['started'],r['ended'],r['method'],f"{r['http']} / {r['curl_exit']}",r['bytes'],r['sha256'] or 'n/a',r['url']])+' |')
(out/'FETCH_LEDGER.md').write_text('\n'.join(lines)+'\n')
print('ledger rows',len(rows))
