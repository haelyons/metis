"""Public-source fetch audit. Downloads stay in the authorized cache."""
import concurrent.futures, datetime, hashlib, json, pathlib, subprocess, threading, time
CACHE = pathlib.Path('/home/hal/.cache/blind01/intake_check_dl/codex')
LOG = pathlib.Path('/home/hal/dev/interp/metis/experiments/blind-01/m5/intake_check_codex/fetch_attempts.jsonl')
LOCK = threading.Lock()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def fetch(label, url, method='GET', retries=3, phase='A', timeout=240):
    for attempt in range(1,retries+2):
        start=now(); base=CACHE/f'{label}.{attempt}'; body=pathlib.Path(str(base)+'.body'); hdr=pathlib.Path(str(base)+'.headers')
        cmd=['curl','--silent','--show-error','--location','--connect-timeout','25','--max-time',str(timeout),'--dump-header',str(hdr),'--output',str(body),'--write-out','%{json}',url]
        if method=='HEAD': cmd.insert(1,'--head')
        cp=subprocess.run(cmd,capture_output=True,text=True)
        try: result=json.loads(cp.stdout)
        except ValueError: result={}
        size=body.stat().st_size if body.exists() else 0
        sha=hashlib.file_digest(body.open('rb'),'sha256').hexdigest() if body.exists() and method=='GET' else None
        r=dict(phase=phase,label=label,url=url,method=method,attempt=attempt,started=start,ended=now(),curl_exit=cp.returncode,http=result.get('http_code'),effective_url=result.get('url_effective'),bytes=size,sha256=sha,error=cp.stderr.strip(),body=str(body),headers=str(hdr),transfer_bytes=result.get('size_download'),elapsed=result.get('time_total'))
        with LOCK:
            with LOG.open('a') as f: f.write(json.dumps(r)+'\n')
            print(json.dumps({k:r[k] for k in ['label','attempt','http','curl_exit','bytes','ended']}),flush=True)
        if cp.returncode==0 and 200<=r.get('http',0)<300: return r
        # A rate limit/access barrier is not retried through another path.
        if r.get('http') in (401,403,429): return r
        if attempt<=retries: time.sleep(60)
    return r
if __name__=='__main__':
    pin='ebeb28a2f8411363cef722b7d293c978f7442672'
    jobs=[('index','https://pinderdata.org/2024-02/index.parquet','GET'),('metadata','https://pinderdata.org/2024-02/metadata.parquet','GET'),('test_zip','https://pinderdata.org/2024-02/test_set_pdbs.zip','GET'),('full_pdb_head','https://pinderdata.org/2024-02/pdbs.zip','HEAD'),('maps_head','https://pinderdata.org/2024-02/mappings.zip','HEAD'),('frodock_old','https://chaconlab.org/modeling/frodock/frodock-donwload','GET')]
    jobs += [(x,f'https://files.rcsb.org/download/{x}.cif','GET') for x in ['6IHB','6JCQ','6JCS']]
    jobs += [('pinder_code',f'https://codeload.github.com/pinder-org/pinder/tar.gz/{pin}','GET')]
    jobs += [('frodock_readme','https://raw.githubusercontent.com/chaconlab/FRODOCK/main/README.md','GET')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex: list(ex.map(lambda x:fetch(*x),jobs))
