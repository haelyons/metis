#!/usr/bin/env bash
set -euo pipefail
# Internal evaluator entry point: each invocation execs a fresh Python process.
if [[ ${1:-} == --child ]]; then
    shift
    export OMP_NUM_THREADS=26 OMP_DYNAMIC=FALSE OPENBLAS_NUM_THREADS=1
    export MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 LC_ALL=C LANG=C
    export CUDA_VISIBLE_DEVICES='' GPU_COUNT=0 PYTHONDONTWRITEBYTECODE=1
    export XDG_CACHE_HOME="$PWD/out/cache" TMPDIR="$PWD/out/tmp"
    mkdir -p out/tmp out/cache
    exec baseline-published/venv/bin/python - "$@" <<'PYCHILD'
import pathlib,json,sys,math,time,os
from pinder.eval.dockq import BiotiteDockQ
P=pathlib.Path
case_id,job_s,kind=sys.argv[1:]; job=P(job_s); job.mkdir(parents=True,exist_ok=True)
c=next(c for c in json.loads(P('data/manifest.json').read_text())['data']['cases'] if c['id']==case_id)
native=P('data/2024-02')/c['reference']
poses=[native] if kind=='smoke' else [P('out')/c['system_id'][:4]/'poses'/f'model_{i}.pdb' for i in range(1,51)]
evaluator=BiotiteDockQ(native=native,decoys=poses,native_receptor_chain=['R'],native_ligand_chain=['L'],decoy_receptor_chain=['R'],decoy_ligand_chain=['L'],parallel_io=False)
if kind=='mapping':
    # Capture actual runtime correspondence objects without parsing implementation text.
    def serial(x,seen=None,depth=0):
        if seen is None: seen=set()
        if x is None or isinstance(x,(str,int,float,bool)): return x
        if depth>7 or id(x) in seen: return repr(x)
        seen.add(id(x))
        if isinstance(x,dict): return {str(k):serial(v,seen,depth+1) for k,v in x.items()}
        if isinstance(x,(list,tuple)): return [serial(v,seen,depth+1) for v in x]
        if hasattr(x,'tolist'): return x.tolist()
        if hasattr(x,'__dict__'): return {str(k):serial(v,seen,depth+1) for k,v in vars(x).items()}
        return repr(x)
    (job/'correspondence.json').write_text(json.dumps(serial(evaluator),default=str,indent=2)+'\n')
    for path in [native,*poses[:1]]:
        residues={}
        for line in path.read_text().splitlines():
            if line.startswith(('ATOM  ','HETATM')): residues.setdefault(line[21],set()).add((line[22:27],line[17:20]))
        (job/(path.stem+'-residues.json')).write_text(json.dumps({k:sorted(v) for k,v in residues.items()},indent=2))
    sys.exit(0)
t=time.monotonic(); df=evaluator.calculate(); calc=time.monotonic()-t
values=[float(v) for v in df.DockQ]
assert len(values)==(1 if kind=='smoke' else 50) and all(math.isfinite(v) for v in values),'Invalid DockQ rows'
if kind!='smoke': assert len(set(df.model_name))==50 and set(df.model_name)=={f'model_{i}' for i in range(1,51)},'Missing scored pose'
with (job/'dockq.csv').open('w') as f:
    df.to_csv(f,index=False); f.flush(); os.fsync(f.fileno())
(job/'calculation.json').write_text(json.dumps({'calculation_wall_s':calc,'n_scored':len(values),'DockQ':values,'check':'DESIGN native-self identity' if kind=='smoke' else None})+'\n')
if kind=='smoke': assert abs(values[0]-1)<=1e-6, 'DESIGN native-self DockQ != 1'
PYCHILD
fi
if [[ -n ${EVAL_MODE:-} && ${EVAL_MODE} != anchors ]]; then
    exec bash harness/run_evaluation.sh "$@"
fi
mkdir -p out
# The canonical file owns its environment. Never duplicate its workload here.
python3 - <<'PYPARENT'
import pathlib,json,subprocess,time,os,signal,math,hashlib,re,csv,collections,sys
P=pathlib.Path
m=json.loads(P('data/manifest.json').read_text()); cases=m['data']['cases']; checks=json.loads(P('data/setup_checks.json').read_text())
start=time.monotonic(); records=[]; smokes={}; stage={}
result={'protocol':'CPU-standard PINDER evaluator calibration s03','protocol_sha256':hashlib.sha256(json.dumps(m['EXECUTION'],sort_keys=True).encode()).hexdigest(),'cases':[c['id'] for c in cases],'configuration':m['baseline']['published_configuration'],'pins':checks['pins'],'setup_checks':checks,'native_self_smoke':smokes,'records':records,'T_s':None,'per_case_maxima':{},'allowance60_screen':'unknown','scope':'CPU-standard-only','stage_walls':stage,'allocation_projection':m['EXECUTION']['budget'],'allocation_receipts':None,'current_tariff':None,'invoice':None,'lifecycle_assurance':'External operator obligation; not verified by harness','primary_timing_scope':m['EXECUTION']['timing_scope']['primary']}
def save():
    result['stage_walls']['anchors_elapsed_s']=time.monotonic()-start
    complete=[r['wall_s'] for r in records if r['status']=='complete']
    result['T_s']=max(complete) if len(complete)==16 else None
    result['per_case_maxima']={c['id']:max([r['wall_s'] for r in records if r['case_id']==c['id'] and r['status']=='complete'],default=None) for c in cases}
    witness=any((r['wall_s'] or r['lower_bound_s'] or 0)>60 for r in records)
    result['allowance60_screen']='fail' if witness else ('pass' if len(complete)==16 else 'unknown')
    P('out/calibration.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def child(c,job,kind):
    job.mkdir(parents=True,exist_ok=True)
    with (job/'child.log').open('a') as log:
        begin=time.monotonic()
        p=subprocess.Popen(['bash','harness/run_anchors.sh','--child',c['id'],str(job),kind],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            rc=p.wait(timeout=180)
        except subprocess.TimeoutExpired:
            lower=time.monotonic()-begin
            os.killpg(p.pid,signal.SIGKILL); p.wait()
            return {'status':'timeout','wall_s':None,'lower_bound_s':lower,'n_scored':0}
        if rc!=0: return {'status':'failed','wall_s':None,'lower_bound_s':None,'n_scored':0}
        if kind=='mapping': return {'status':'complete','wall_s':time.monotonic()-begin,'lower_bound_s':None,'n_scored':0}
        output=job/'dockq.csv'
        if not output.is_file() or output.stat().st_size==0: return {'status':'invalid_output','wall_s':None,'lower_bound_s':None,'n_scored':0}
        wall=time.monotonic()-begin
        rows=list(csv.DictReader(output.open()))
        assert len(rows)==(1 if kind=='smoke' else 50) and all(math.isfinite(float(r['DockQ'])) for r in rows)
        if kind!='smoke': assert len({r['model_name'] for r in rows})==50 and {r['model_name'] for r in rows}=={f'model_{i}' for i in range(1,51)}
        return {'status':'complete','wall_s':wall,'lower_bound_s':None,'n_scored':len(rows)}
def inventory(p):
    rows=[l for l in p.read_text().splitlines() if l.startswith(('ATOM  ','HETATM'))]
    assert rows, 'Empty structure: '+str(p)
    for l in rows: assert all(math.isfinite(float(l[i:i+8])) for i in [30,38,46])
    return collections.Counter((l[:6],l[12:27]) for l in rows)
try:
    # Verify bytes, never parse or assert on source text.
    for name,expected in json.loads(P('data/verified_hashes.json').read_text()).items():
        if name.startswith('harness/'):
            continue  # Scripts may receive authorized harness repairs; record current bytes below.
        assert digest(P(name))==expected, 'Identity changed: '+name
    result['script_hashes']={str(p):digest(p) for p in P('harness').glob('*.sh')}
    for repo,pin in checks['pins'].items():
        assert subprocess.check_output(['git','-C','baseline-published/'+repo,'rev-parse','HEAD'],text=True).strip()==pin
    t=time.monotonic()
    with P('out/run_command.log').open('a') as log:
        subprocess.run(['bash','harness/run_command.sh'],stdout=log,stderr=subprocess.STDOUT,check=True)
    stage['docking_and_reconstruction_s']=time.monotonic()-t
    if m['anchors']==[]: P('out/anchors_measured.json').write_text('{}\n')
    for c in cases:
        prefix=c['system_id'][:4]; job=P('out')/prefix
        lines=(job/'docking.out').read_text().splitlines()
        assert len(lines)==54, 'Expected four header lines and 50 rows'
        header=[float(x) for x in lines[0].split()]
        assert len(header)>=2 and header[0]>0 and abs(header[1]-1.2)<1e-6,'Invalid grid/voxel output'
        for line in lines[4:]:
            fields=[float(x) for x in line.split()]; assert len(fields)==7 and all(math.isfinite(x) for x in fields)
        log=(job/'docking.log').read_text()
        # Read binary output; accept cosmetic label variations, require printed values.
        def printed(label,value):
            relevant=[l for l in log.splitlines() if re.search(label,l,re.I)]
            assert relevant and any(re.search(r'(?<![\d.])'+str(value)+r'(?![\d.])',l) for l in relevant), 'Missing/invalid printed '+label
        printed(r'rotat|angle',3600); printed(r'thread|OpenMP',26)
        expected=inventory(P('data/inputs')/(prefix+'_R.pdb'))+inventory(P('data/inputs')/(prefix+'_L.pdb'))
        for i in range(1,51):
            pose=job/'poses'/f'model_{i}.pdb'; assert inventory(pose)==expected, 'Pose atom inventory changed'
            chains={l[21] for l in pose.read_text().splitlines() if l.startswith(('ATOM  ','HETATM'))}; assert chains=={'R','L'}
        assert child(c,job/'mapping','mapping')['status']=='complete','Correspondence capture failed'
        smoke=child(c,job/'native-self','smoke'); smokes[c['id']]=smoke
        data=job/'native-self/calculation.json'
        if data.exists(): smoke['measured']=json.loads(data.read_text())
        save(); assert smoke['status']=='complete','Native-self smoke failed'
    for block in range(1,5):
        for c in cases:
            if time.monotonic()-start>=5400: raise RuntimeError('Science lifecycle budget exhausted')
            record={'case_id':c['id'],'block':block,**child(c,P('out')/c['system_id'][:4]/f'block_{block}','score')}
            records.append(record); save()
    assert len(records)==16 and all(r['status']=='complete' for r in records),'Incomplete/invalid evaluator output'
    # No published anchor IDs exist in this intake. Do not synthesize them.
    assert m['anchors']==[], 'Unexpected anchor schema: harness requires regeneration'
    P('out/anchors_measured.json').write_text('{}\n')
except BaseException as e:
    result['failure']=str(e); save(); raise
save()
PYPARENT
