"""Enumerate original benchmark inputs without running the benchmark."""
import concurrent.futures,hashlib,json,pathlib,sys,zipfile
import pandas as pd
import gemmi
from fetch import fetch,CACHE
OUT=pathlib.Path(__file__).parent
idx=pd.read_parquet(CACHE/'index.1.body')
sub=idx[idx.pinder_s].sort_values('id')
paired=sub[sub.apo_R & sub.apo_L]
summary={'index_rows':len(idx),'pinder_s_cases':len(sub),'paired_apo_cases':len(paired)}
sub.to_csv(OUT/'pinder_s_cases.csv',index=False)
meta=pd.read_parquet(CACHE/'metadata.1.body')
summary['metadata_rows']=len(meta)
summary['metadata_missing_ids']=sorted(set(sub.id)-set(meta.id))
z=zipfile.ZipFile(CACHE/'test_zip.1.body')
summary['test_zip_entries']=len(z.infolist());summary['test_zip_uncompressed_bytes']=sum(x.file_size for x in z.infolist());summary['test_zip_crc_failure']=z.testzip()
required={}
def add(key,case,role):
    if key not in required: required[key]={'key':key,'cases':[],'roles':[]}
    required[key]['cases'].append(case)
    if role not in required[key]['roles']: required[key]['roles'].append(role)
for row in sub.to_dict('records'):
    add('pdbs/'+row['id']+'.pdb',row['id'],'native')
    for role in ['holo_R','holo_L','apo_R','apo_L']:
        name=row[role+'_pdb']
        if not isinstance(name,str) or not name: continue
        folder='test_set_pdbs' if role.startswith('holo') else 'pdbs'
        add(folder+'/'+name,row['id'],role)
        add('mappings/'+name.replace('.pdb','.parquet'),row['id'],role+'_mapping')
records=[];jobs=[]
for i,(key,info) in enumerate(sorted(required.items())):
    if key in z.namelist():
        data=z.read(key); p=CACHE/'selected_from_zip'/key;p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(data)
        records.append(dict(info,source='test_set_pdbs.zip',body=str(p),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    else: jobs.append((f'input_{i:04d}', 'https://pinderdata.org/2024-02/'+key,info))
summary['required_unique_files']=len(required);summary['files_from_test_zip']=len(records);summary['individual_downloads_required']=len(jobs)
(OUT/'input_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(OUT/'required_input_keys.json').write_text(json.dumps(list(required.values()),indent=2)+'\n')
print(json.dumps(summary),flush=True)
def worker(x):
 label,url,info=x;r=fetch(label,url)
 return dict(info,source=url,**{k:r[k] for k in ['body','bytes','sha256','http','ended']})
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool: records+=list(pool.map(worker,jobs))
for r in records:
    p=pathlib.Path(r['body'])
    if r.get('http',200)!=200: r['validation']='unreachable';continue
    try:
        if r['key'].endswith('.pdb'):
            st=gemmi.read_pdb(str(p));atoms=sum(1 for m in st for ch in m for res in ch for a in res)
            r['atoms']=atoms;r['chains']=[ch.name for ch in st[0]]
            if atoms==0: raise ValueError('no atoms')
            if 'native' in r['roles'] and set(r['chains'])!={'R','L'}: raise ValueError('native chains not R,L')
        else:
            table=pd.read_parquet(p);r['rows']=len(table);r['columns']=list(table.columns)
            if len(table)==0: raise ValueError('empty mapping')
        r['validation']='parsed_nonempty'
    except Exception as e: r['validation']='error: '+str(e)
    r['md5']=hashlib.file_digest(p.open('rb'),'md5').hexdigest()
(OUT/'input_inventory.json').write_text(json.dumps(records,indent=2)+'\n')
summary['validation_failures']=[{'key':r['key'],'validation':r['validation']} for r in records if r['validation']!='parsed_nonempty']
for x in ['6IHB','6JCQ','6JCS']:
    doc=gemmi.cif.read(str(CACHE/f'{x}.1.body'));b=doc.sole_block();st=gemmi.make_structure_from_block(b)
    summary[x]={'block':b.name,'atoms':sum(1 for m in st for ch in m for r in ch for a in r),'chains':[ch.name for ch in st[0]],'revisions':list(b.find_values('_pdbx_audit_revision_history.revision_date'))}
(OUT/'input_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print('COMPLETE',json.dumps(summary),flush=True)
