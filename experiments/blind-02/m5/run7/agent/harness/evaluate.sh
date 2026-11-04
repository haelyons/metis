#!/usr/bin/env bash
set -euo pipefail
: "${CMP_INPUT:?}" "${CMP_INPUT_SPEC:?}" "${CMP_PRIVATE:?}" "${CMP_ARM_OUT:?}" "${CMP_EVAL_OUT:?}"
mkdir -p "$CMP_EVAL_OUT"
# The interpreter and installed evaluator live beside the shared published source.
VPY="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../baseline-published/evaluator-venv/bin/python"
export PYTHONDONTWRITEBYTECODE=1
export XDG_CACHE_HOME="$CMP_EVAL_OUT/cache" MPLCONFIGDIR="$CMP_EVAL_OUT/matplotlib"
export TMPDIR="$CMP_EVAL_OUT/tmp"
mkdir -p "$TMPDIR"
"$VPY" - <<'PY' >> "$CMP_EVAL_OUT/evaluator.log" 2>&1
import os,json,pathlib,hashlib,math
from pinder.eval.dockq import BiotiteDockQ
from pinder.core.structure.atoms import atom_array_from_pdb_file
spec=json.loads(os.environ['CMP_INPUT_SPEC'])
private=pathlib.Path(os.environ['CMP_PRIVATE']).resolve()
ref=spec['reference'];native=(private/ref['name']).resolve()
if not native.is_relative_to(private):raise RuntimeError('Reference outside CMP_PRIVATE')
b=native.read_bytes()
if len(b)!=ref['bytes'] or hashlib.sha256(b).hexdigest()!=ref['sha256']:raise RuntimeError('Native checksum mismatch')
arm=pathlib.Path(os.environ['CMP_ARM_OUT']).resolve()
out=pathlib.Path(os.environ['CMP_EVAL_OUT']).resolve()
chains=list(dict.fromkeys(atom_array_from_pdb_file(native).chain_id.tolist()))
if 'R' in chains and 'L' in chains: receptor,ligand='R','L'
elif len(chains)==2: receptor,ligand=chains
else: raise RuntimeError('Native receptor/ligand chain mapping is ambiguous')
models=[arm/f'model_{r}.pdb' for r in range(1,51)]
for p in models:
    if not p.is_file():raise RuntimeError('Missing model: '+str(p))
result=BiotiteDockQ(native=native,decoys=models,
    native_receptor_chain=[receptor],native_ligand_chain=[ligand],
    decoy_receptor_chain=['R'],decoy_ligand_chain=['L']).calculate()
# Upstream can reorder unequal atom-count models; restore the sealed rank order.
result=result.set_index('model_name').loc[[p.stem for p in models]].reset_index()
values=[float(x) for x in result['DockQ']]
if len(values)!=50 or not all(math.isfinite(x) for x in values):raise RuntimeError('Invalid DockQ output')
result.to_csv(out/'components.csv',index=False)
(out/'dockq.json').write_text(json.dumps(values,allow_nan=False)+'\n')
PY
