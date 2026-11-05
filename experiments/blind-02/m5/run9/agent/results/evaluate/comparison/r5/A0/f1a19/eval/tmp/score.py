import os,json,hashlib,math
from pathlib import Path
from pinder.eval.dockq import BiotiteDockQ

def main():
 spec=json.loads(os.environ['CMP_INPUT_SPEC'])
 private=Path(os.environ['CMP_PRIVATE']).resolve()
 ref=(private/spec['reference']['name']).resolve()
 if not ref.is_relative_to(private): raise ValueError('Reference escapes private directory')
 blob=ref.read_bytes();s=spec['reference']
 if len(blob)!=s['bytes'] or hashlib.sha256(blob).hexdigest()!=s['sha256']: raise RuntimeError('Reference integrity failure')
 chains=list(dict.fromkeys(line[21:22].decode() for line in blob.splitlines() if line.startswith((b'ATOM  ',b'HETATM'))))
 if 'R' in chains and 'L' in chains: rec,lig='R','L'
 elif len(chains)==2: rec,lig=chains
 else: raise ValueError('Native must contain receptor and ligand chains')
 models=[Path(os.environ['CMP_ARM_OUT'])/f'model_{r}.pdb' for r in range(1,51)]
 for p in models:
  if not p.is_file(): raise FileNotFoundError(p)
 dq=BiotiteDockQ(native=ref,decoys=models,native_receptor_chain=[rec],native_ligand_chain=[lig],decoy_receptor_chain=['R'],decoy_ligand_chain=['L'],parallel_io=False)
 df=dq.calculate()
 by_name={str(row['model_name']):float(row['DockQ']) for _,row in df.iterrows()}
 values=[by_name[p.stem] for p in models]
 if len(df)!=50 or not all(math.isfinite(x) for x in values): raise RuntimeError('Missing or invalid DockQ output')
 out=Path(os.environ['CMP_EVAL_OUT'])
 df.to_csv(out/'details.csv',index=False)
 (out/'dockq.json').write_text(json.dumps(values,allow_nan=False)+'\n')
if __name__=='__main__': main()
