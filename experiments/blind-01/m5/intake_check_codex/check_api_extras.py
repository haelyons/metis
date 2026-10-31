"""Check eager PinderSystem downloads for the prioritized 93 cases."""
import base64,concurrent.futures,gzip,hashlib,json,pathlib
import gemmi,pandas as pd
from fetch import fetch,CACHE
OUT=pathlib.Path(__file__).parent
keys=json.loads((OUT/'api_extra_keys.json').read_text())
records={}
for directory in ['pdbs','mappings']:
    wanted={k for k in keys if k.startswith(directory+'/')}
    for line in gzip.open(CACHE/f'manifest_{directory}.1.body','rt'):
        r=json.loads(line)
        if r['key'] in wanted: records[r['key']]=r

def work(pair):
    i,key=pair;r=fetch(f'api_extra_{i:04d}','https://pinderdata.org/2024-02/'+key)
    p=pathlib.Path(r['body']);expected=records.get(key);data=p.read_bytes()
    result=dict(key=key,expected=expected,body=r['body'],bytes=r['bytes'],sha256=r['sha256'],http=r['http'],ended=r['ended'])
    result['size_match']=expected is not None and len(data)==expected['size']
    result['md5_match']=expected is not None and base64.b64encode(hashlib.md5(data).digest()).decode()==expected['md5']
    try:
        if key.endswith('.pdb'):
            st=gemmi.read_pdb(str(p));result['atoms']=sum(1 for m in st for c in m for res in c for a in res);assert result['atoms']>0
        else: result['rows']=len(pd.read_parquet(p));assert result['rows']>0
        result['parsed_nonempty']=True
    except Exception as e: result['parsed_nonempty']=False;result['parse_error']=str(e)
    return result
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool: results=list(pool.map(work,enumerate(keys)))
(OUT/'api_extra_inventory.json').write_text(json.dumps(results,indent=2)+'\n')
summary={'files':len(results),'bytes':sum(r['bytes'] for r in results),'failures':[r['key'] for r in results if r['http']!=200 or not r['md5_match'] or not r['size_match'] or not r['parsed_nonempty']]}
(OUT/'api_extra_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary),flush=True)
