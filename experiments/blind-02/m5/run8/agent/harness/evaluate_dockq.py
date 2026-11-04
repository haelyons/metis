import hashlib
import json
import math
import os
from pathlib import Path


def main():
    # Keep all interpreter caches and temporary files inside CMP_EVAL_OUT.
    out = Path(os.environ['CMP_EVAL_OUT']).resolve()
    out.mkdir(parents=True, exist_ok=True)
    os.chdir(out)
    os.environ['TMPDIR'] = str(out / 'tmp')
    from pinder.eval.dockq import BiotiteDockQ

    metadata = json.loads((Path(__file__).resolve().parent / 'inputs.json').read_text())
    input_id = os.environ['CMP_INPUT']
    known = {item['id']: item['spec'] for item in metadata}
    spec = json.loads(os.environ['CMP_INPUT_SPEC']) if os.environ.get('CMP_INPUT_SPEC') else known[input_id]
    if input_id not in known:
        raise ValueError('Unknown fixture ' + input_id)
    reference = spec['reference']
    private = Path(os.environ['CMP_PRIVATE']).resolve()
    native = (private / reference['name']).resolve()
    if not native.is_relative_to(private):
        raise ValueError('Native path escapes CMP_PRIVATE')
    data = native.read_bytes()
    if len(data) != reference['bytes'] or hashlib.sha256(data).hexdigest() != reference['sha256']:
        raise ValueError('Invalid private native complex')
    chains = {line[21:22].decode('ascii') for line in data.splitlines() if line.startswith((b'ATOM  ', b'HETATM'))}
    if {'R', 'L'} <= chains:
        receptor, ligand = 'R', 'L'
    else:
        left, right = spec['pinder_system'].split('--')
        receptor = left.split('__')[1][0]
        ligand = right.split('__')[1][0]
        if receptor == ligand or receptor not in chains or ligand not in chains:
            raise ValueError('Native receptor/ligand chain mapping is ambiguous')
    arm_out = Path(os.environ['CMP_ARM_OUT']).resolve()
    models = [arm_out / f'model_{rank}.pdb' for rank in range(1, 51)]
    for model in models:
        if not model.is_file():
            raise FileNotFoundError(model)
    scorer = BiotiteDockQ(
        native=native,
        decoys=models,
        native_receptor_chain=[receptor],
        native_ligand_chain=[ligand],
        decoy_receptor_chain=['R'],
        decoy_ligand_chain=['L'],
        parallel_io=False,
    )
    frame = scorer.calculate()
    if len(frame) != len(models) or frame['model_name'].duplicated().any():
        raise ValueError('Missing or duplicate evaluator output')
    by_name = frame.set_index('model_name')
    values = [float(by_name.loc[model.stem, 'DockQ']) for model in models]
    if not all(math.isfinite(value) for value in values):
        raise ValueError('Nonfinite DockQ output')
    frame.to_csv(out / 'details.csv', index=False)
    (out / 'chain_mapping.json').write_text(json.dumps({'native_receptor': receptor, 'native_ligand': ligand, 'decoy_receptor': 'R', 'decoy_ligand': 'L'}) + '\n')
    (out / 'dockq.json').write_text(json.dumps(values, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
