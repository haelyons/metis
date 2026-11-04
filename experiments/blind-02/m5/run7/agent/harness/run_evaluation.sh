#!/usr/bin/env bash
set -euo pipefail
# Comparison invocations use the published DockQ interface directly.
if [[ -n "${CMP_ARM_OUT:-}" ]]; then exec bash harness/evaluate.sh; fi
: "${EVAL_OUT:?}" "${EVAL_INPUTS:?}" "${EVAL_SEEDS:?}" "${EVAL_PROTOCOL:?}" "${BASELINE_DIR:?}"
mkdir -p "$EVAL_OUT"
python3 - <<'PY'
import os,json,pathlib,subprocess,time,math
root=pathlib.Path.cwd()
private=os.environ.get('CMP_PRIVATE')
if not private:raise RuntimeError('Published DockQ evaluation requires CMP_PRIVATE populated by fetch_private.sh')
specs={'f1a19': {'pinder_release': '2024-02', 'pinder_system': '1a19__A1_P11540--1a19__B1_P11540', 'kind': 'holo test-set monomers', 'receptor_source': {'name': 'test_set_pdbs/1a19__A1_P11540-R.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1a19__A1_P11540-R.pdb', 'bytes': 58320, 'sha256': '08cba0488510ac98b618ab9b963306d7d67459bcab501b54e9dd8214f8f63e63'}, 'ligand_source': {'name': 'test_set_pdbs/1a19__B1_P11540-L.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1a19__B1_P11540-L.pdb', 'bytes': 58320, 'sha256': '9d02d5646d3ba8b13699e83d11ec1d4ed833888e1aa2522d944de0393332bde7'}, 'prepared': {'receptor': 'data/fixtures/f1a19/R.pdb', 'ligand': 'data/fixtures/f1a19/L.pdb'}, 'reference': {'access': 'evaluator private data only', 'name': 'pdbs/1a19__A1_P11540--1a19__B1_P11540.pdb', 'url': 'https://pinderdata.org/2024-02/pdbs/1a19__A1_P11540--1a19__B1_P11540.pdb', 'bytes': 116559, 'sha256': '9b112ee5082081cb9c111a3015449c72161332819251d200f6971e3f3336c7f2'}}, 'f1dtd': {'pinder_release': '2024-02', 'pinder_system': '1dtd__A1_P48052--1dtd__B1_P81511', 'kind': 'holo test-set monomers', 'receptor_source': {'name': 'test_set_pdbs/1dtd__A1_P48052-R.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1dtd__A1_P48052-R.pdb', 'bytes': 192132, 'sha256': '2075e71ae732971c2f78286b554a5baad632f38b383decb8ff8859cd88807394'}, 'ligand_source': {'name': 'test_set_pdbs/1dtd__B1_P81511-L.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1dtd__B1_P81511-L.pdb', 'bytes': 38313, 'sha256': 'b693ffc0dc24f0cf4ba456bcb7ca115a8f1879e747aa3c87245aeec727315797'}, 'prepared': {'receptor': 'data/fixtures/f1dtd/R.pdb', 'ligand': 'data/fixtures/f1dtd/L.pdb'}, 'reference': {'access': 'evaluator private data only', 'name': 'pdbs/1dtd__A1_P48052--1dtd__B1_P81511.pdb', 'url': 'https://pinderdata.org/2024-02/pdbs/1dtd__A1_P48052--1dtd__B1_P81511.pdb', 'bytes': 230364, 'sha256': '95c095234280fb888c3ef9441f3393fc816223a960131f7dcddab2c0dbae9706'}}, 'f1glj': {'pinder_release': '2024-02', 'pinder_system': '1glj__A1_P0A6F3--1glj__B1_P0A6F3', 'kind': 'holo test-set monomers', 'receptor_source': {'name': 'test_set_pdbs/1glj__A1_P0A6F3-R.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1glj__A1_P0A6F3-R.pdb', 'bytes': 316791, 'sha256': '7131a9741f10136dce36e02b8282a5df0cafc97021fd932c7cf0a92cf8eae87a'}, 'ligand_source': {'name': 'test_set_pdbs/1glj__B1_P0A6F3-L.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1glj__B1_P0A6F3-L.pdb', 'bytes': 316791, 'sha256': '887d53373e51eaa7a717841c3038ebb2e6c31796aad2927a93b698f379c72ca5'}, 'prepared': {'receptor': 'data/fixtures/f1glj/R.pdb', 'ligand': 'data/fixtures/f1glj/L.pdb'}, 'reference': {'access': 'evaluator private data only', 'name': 'pdbs/1glj__A1_P0A6F3--1glj__B1_P0A6F3.pdb', 'url': 'https://pinderdata.org/2024-02/pdbs/1glj__A1_P0A6F3--1glj__B1_P0A6F3.pdb', 'bytes': 633501, 'sha256': 'b9650bb0452f3f6def3954f96a30be7e2fa5f246bf308385dcd0b6ea7756903c'}}, 'f1ht8': {'pinder_release': '2024-02', 'pinder_system': '1ht8__A1_P05979--1ht8__B1_P05979', 'kind': 'holo test-set monomers', 'receptor_source': {'name': 'test_set_pdbs/1ht8__A1_P05979-R.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1ht8__A1_P05979-R.pdb', 'bytes': 362718, 'sha256': 'b51981e47c916bb095d67a38bdbab04464a3581d85e51898c33bb2ad44bd5da0'}, 'ligand_source': {'name': 'test_set_pdbs/1ht8__B1_P05979-L.pdb', 'url': 'https://pinderdata.org/2024-02/test_set_pdbs/1ht8__B1_P05979-L.pdb', 'bytes': 362718, 'sha256': '02e7cb2b1d019063502be0dac261bcc39c8f2b7c558a58af9d9e77ab0b7838d7'}, 'prepared': {'receptor': 'data/fixtures/f1ht8/R.pdb', 'ligand': 'data/fixtures/f1ht8/L.pdb'}, 'reference': {'access': 'evaluator private data only', 'name': 'pdbs/1ht8__A1_P05979--1ht8__B1_P05979.pdb', 'url': 'https://pinderdata.org/2024-02/pdbs/1ht8__A1_P05979--1ht8__B1_P05979.pdb', 'bytes': 725355, 'sha256': 'db9192a30142d9d8f364ff13b4191841af7f4aa0ecd85b688fb8b9cef70fffd9'}}}
out=pathlib.Path(os.environ['EVAL_OUT']);out.mkdir(parents=True,exist_ok=True)
protocol=json.loads(pathlib.Path(os.environ['EVAL_PROTOCOL']).read_text())
ids=json.loads(os.environ['EVAL_INPUTS'])['ids']
seed_spec=json.loads(os.environ['EVAL_SEEDS'])
if seed_spec['kind']=='paired_median': seeds=seed_spec['seeds']
elif seed_spec['kind']=='deterministic':seeds=[None]
else:raise RuntimeError('Unknown seed protocol')
known=('f1a19','f1dtd','f1glj','f1ht8')
if any(i not in known for i in ids):raise RuntimeError('Unsealed input identity')
env=os.environ.copy();env.update(OMP_NUM_THREADS='26',OMP_DYNAMIC='FALSE',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',LC_ALL='C',LANG='C',CUDA_VISIBLE_DEVICES='0')
base=pathlib.Path(os.environ['BASELINE_DIR']).resolve()
# BASELINE_DIR names the staged published tree in the evaluation interface.
if not (base/'megadock/megadock').is_file() and (base/'baseline-published/megadock/megadock').is_file():base=base/'baseline-published'
records=[];begin=time.monotonic()
for si,seed in enumerate(seeds):
    for ident in ids:
        wd=out/f'seed-{si}'/ident;wd.mkdir(parents=True,exist_ok=False)
        (wd/'baseline-published').symlink_to(base,target_is_directory=True)
        (wd/'data').symlink_to((root/'data').resolve(),target_is_directory=True)
        (wd/'out').mkdir()
        r=f'data/fixtures/{ident}/R.pdb';l=f'data/fixtures/{ident}/L.pdb'
        args=['baseline-published/megadock/megadock','-R',r,'-L',l,'-o','out/docking.out','-N','50','-t','1','-v','1.2','-e','1.0','-d','1.0','-a','-45.0','-b','1.0','-f','3','-r','3600']
        reconstruct=['bash','-c','set -euo pipefail; for r in $(seq 1 50); do baseline-published/megadock/decoygen "lig_$r.pdb" "$2" "$0/docking.out" "$r" > "decoygen_$r.log" 2>&1; grep -v \'^END\' "$1" > "$0/model_$r.pdb"; grep -v -E \'^(END|ENDMDL)\' "lig_$r.pdb" >> "$0/model_$r.pdb"; echo END >> "$0/model_$r.pdb"; done','out',r,l]
        t=time.monotonic()
        with (wd/'stdout.log').open('w') as log:
            subprocess.run(args,cwd=wd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=max(1,1150-(time.monotonic()-begin)))
            subprocess.run(reconstruct,cwd=wd,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=max(1,1150-(time.monotonic()-begin)))
        eval_env=env.copy();eval_env.update(CMP_INPUT=ident,CMP_INPUT_SPEC=json.dumps(specs[ident]),CMP_PRIVATE=private,CMP_ARM_OUT=str((wd/'out').resolve()),CMP_EVAL_OUT=str((wd/'eval').resolve()))
        subprocess.run(['bash',str(root/'harness/evaluate.sh')],cwd=wd,env=eval_env,check=True,timeout=max(1,1150-(time.monotonic()-begin)))
        wall=time.monotonic()-t
        # A0 uses CPU FFTW; no CUDA work is launched by this executable.
        rows=[]
        for line in (wd/'out/docking.out').read_text().splitlines():
            parts=line.split()
            if len(parts)!=7:continue
            try:values=list(map(float,parts))
            except ValueError:continue
            if not all(math.isfinite(x) for x in values):raise RuntimeError('Invalid docking output')
            rows.append(values)
        if len(rows)!=50:raise RuntimeError('Missing ranked output')
        records.append({'input_id':ident,'seed':seed,'metrics':{'wall':wall}})
result={'records':records,'timing_scope':protocol['timing_scope'],'gpu_count':0,'wall_s':time.monotonic()-begin,'compute_budget':None}
if os.environ.get('EVAL_COMPUTE_BUDGET'):
    result['compute_budget']=json.loads(os.environ['EVAL_COMPUTE_BUDGET'])
(out/'evaluation.json').write_text(json.dumps(result,allow_nan=False)+'\n')
PY
