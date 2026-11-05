import os,json,hashlib,math
from pathlib import Path

def main():
 from pinder.eval.dockq import BiotiteDockQ
 s=json.loads(os.environ['CMP_INPUT_SPEC']); ref=s['reference']
 root=Path(os.environ['CMP_PRIVATE']).resolve(); native=(root/ref['name']).resolve()
 if not native.is_relative_to(root): raise ValueError('Invalid native path')
 raw=native.read_bytes()
 if len(raw)!=ref['bytes'] or hashlib.sha256(raw).hexdigest()!=''.join(ref['sha256']): raise ValueError('Native size/checksum mismatch')
 chains=[]
 for line in raw.splitlines():
  if line[:6].strip() in (b'ATOM',b'HETATM'):
   ch=line[21:22].decode()
   if ch not in chains: chains.append(ch)
 if 'R' in chains and 'L' in chains: nr,nl='R','L'
 elif len(chains)==2: nr,nl=chains
 else: raise ValueError('Native must have two receptor/ligand chains')
 models=[Path(os.environ['CMP_ARM_OUT'])/f'model_{r}.pdb' for r in range(1,51)]
 for p in models:
  if not p.is_file(): raise FileNotFoundError(p)
 df=BiotiteDockQ(native=native,decoys=models,native_receptor_chain=[nr],native_ligand_chain=[nl],decoy_receptor_chain=['R'],decoy_ligand_chain=['L'],parallel_io=False).calculate()
 by_name={str(row['model_name']):float(row['DockQ']) for _,row in df.iterrows()}
 values=[by_name[p.stem] for p in models]
 if not all(math.isfinite(x) for x in values): raise ValueError('Nonfinite DockQ output')
 out=Path(os.environ['CMP_EVAL_OUT'])
 df.to_csv(out/'details.csv',index=False)
 (out/'dockq.json').write_text(json.dumps(values,allow_nan=False)+'\n')
if __name__=='__main__':main()
