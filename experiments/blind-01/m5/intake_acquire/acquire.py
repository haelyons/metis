"""Read-only HTTP acquisition audit. Response bodies stay in the download cache."""
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys
import threading

ROOT = pathlib.Path(__file__).resolve().parent
CACHE = pathlib.Path('/home/hal/.cache/blind01/intake_check_dl/acquire')
CACHE.mkdir(parents=True, exist_ok=True)
LOCK = threading.Lock()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def fetch(job):
    label, url = job[:2]
    timeout = job[2] if len(job) > 2 else 45
    options = job[3] if len(job) > 3 else {}
    body = CACHE / (label + '.body')
    headers = CACHE / (label + '.headers')
    if body.exists():
        raise ValueError('Use a new label for each attempt: ' + label)
    started = now()
    command = ['curl', '--globoff', '--silent', '--show-error', '--location', '--max-redirs', '5',
               '--connect-timeout', '15', '--max-time', str(timeout),
               '--proto', '=https,http', '--proto-redir', '=https,http',
               '--dump-header', str(headers), '--output', str(body),
               '--write-out', '%{http_code}\n%{url_effective}\n%{size_download}']
    if options.get('json') is not None:
        command += ['--request', 'POST', '--header', 'Content-Type: application/json',
                    '--data-binary', json.dumps(options['json'])]
    command.append(url)
    result = subprocess.run(command, capture_output=True, text=True)
    lines = result.stdout.splitlines()
    data = body.read_bytes() if body.exists() else b''
    record = dict(label=label, url=url, method='POST search' if options else 'GET',
                  request_json=options.get('json'), started_utc=started, ended_utc=now(),
                  curl_exit=result.returncode, http_status=lines[0] if lines else '000',
                  effective_url=lines[1] if len(lines) > 1 else None,
                  bytes=len(data), sha256=hashlib.sha256(data).hexdigest() if data else None,
                  cache_body=str(body), cache_headers=str(headers), error=result.stderr.strip())
    with LOCK:
        with (ROOT / 'fetch_attempts.jsonl').open('a') as out:
            out.write(json.dumps(record) + '\n')
        print(json.dumps({k:v for k,v in record.items() if not k.startswith('cache_')}), flush=True)
    return record


if __name__ == '__main__':
    jobs = json.loads(pathlib.Path(sys.argv[1]).read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        list(pool.map(fetch, jobs))
