"""Compare retrieved bytes against publisher manifests."""
import base64,gzip,hashlib,json,pathlib
from fetch import CACHE
OUT=pathlib.Path(__file__).parent
root={r['key']:r for r in map(json.loads,gzip.open(CACHE/'manifest_root.1.body','rt'))}
checks=[]
for name,label in [('index.parquet','index'),('metadata.parquet','metadata'),('test_set_pdbs.zip','test_zip')]:
    p=CACHE/f'{label}.1.body';r=root[name];md5=base64.b64encode(hashlib.file_digest(p.open('rb'),'md5').digest()).decode()
    checks.append({'key':name,'expected_size':r['size'],'actual_size':p.stat().st_size,'published_md5_base64':r['md5'],'actual_md5_base64':md5,'size_match':p.stat().st_size==r['size'],'md5_match':md5==r['md5']})
needed={r['key'] for r in json.loads((OUT/'required_input_keys.json').read_text())}
manifest_records={};manifest_counts={}
for directory in ['pdbs','mappings','test_set_pdbs']:
    count=0
    with gzip.open(CACHE/f'manifest_{directory}.1.body','rt') as f:
        for line in f:
            r=json.loads(line); count+=1
            if r['key'] in needed: manifest_records[r['key']]=r
    manifest_counts[directory]=count
(OUT/'selected_published_checksums.json').write_text(json.dumps(manifest_records,indent=2)+'\n')
summary={'root_files':checks,'directory_manifest_entries':manifest_counts,'required_files':len(needed),'required_files_with_published_checksums':len(manifest_records),'required_files_absent_from_manifest':sorted(needed-set(manifest_records))}
inv=OUT/'input_inventory.json'
if inv.exists():
    checks=[]
    for r in json.loads(inv.read_text()):
        e=manifest_records.get(r['key'])
        if not e: checks.append({'key':r['key'],'error':'no published manifest entry'});continue
        p=pathlib.Path(r['body']);actual=base64.b64encode(hashlib.file_digest(p.open('rb'),'md5').digest()).decode()
        if r['bytes']!=e['size'] or actual!=e['md5']: checks.append({'key':r['key'],'expected':e,'actual_size':r['bytes'],'actual_md5_base64':actual})
    summary['individual_file_failures']=checks
    summary['individual_files_checked']=len(json.loads(inv.read_text()))
(OUT/'checksum_verification.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
