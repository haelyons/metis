"""A0 evaluation adapter; comparison-mode scheduling is owned by the pipeline."""
import json
import os
import subprocess
import time
from pathlib import Path


def main():
    started = time.monotonic()
    work = Path.cwd()
    view = json.loads((work / 'harness/published.json').read_text())
    fixtures = {item['id']: item['spec'] for item in view['inputs']}
    protocol = json.loads(Path(os.environ['EVAL_PROTOCOL']).read_text())
    inputs = json.loads(os.environ['EVAL_INPUTS'])['ids']
    seed_spec = json.loads(os.environ['EVAL_SEEDS'])
    if seed_spec['kind'] == 'deterministic':
        seeds = [None]
    elif seed_spec['kind'] == 'paired_median':
        seeds = seed_spec['seeds']
        if any(type(seed) is not int for seed in seeds):
            raise ValueError('Invalid execution seed')
    else:
        raise ValueError('Unknown seed protocol')
    if os.environ.get('EVAL_MODE') == 'curve':
        raise ValueError('Published comparison defines no curve or compute budget')
    private = Path(os.environ['CMP_PRIVATE']).resolve()
    out = Path(os.environ['EVAL_OUT']).resolve()
    arm = view['arms'][0]
    env = os.environ.copy()
    env.update(arm['env'])
    # Each executable is a CPU process; no GPU is used by A0 or DockQ.
    records = []
    for si, seed in enumerate(seeds):
        for input_id in inputs:
            spec = fixtures[input_id]
            invocation = out / f'seed_{si}' / input_id
            invocation.mkdir(parents=True, exist_ok=False)
            for tree in ['baseline-published', 'data', 'harness']:
                (invocation / tree).symlink_to(work / tree, target_is_directory=True)
            arm_out = invocation / 'out'
            eval_out = invocation / 'eval'
            arm_out.mkdir()
            local_env = env.copy()
            local_env.update(CMP_INPUT=input_id, CMP_INPUT_SPEC=json.dumps(spec), CMP_ARM_OUT=str(arm_out), CMP_OUT=str(arm_out), CMP_EVAL_OUT=str(eval_out), CMP_PRIVATE=str(private))
            before = time.monotonic()
            with (invocation / 'invocation.log').open('w') as log:
                subprocess.run(['bash', 'harness/arms/A0.sh'], cwd=invocation, env=local_env, stdout=log, stderr=subprocess.STDOUT, check=True)
                for template in arm['commands']:
                    command = []
                    for argument in template:
                        argument = argument.replace('{out}', 'out')
                        for role in ['receptor', 'ligand']:
                            argument = argument.replace('{spec:/prepared/' + role + '}', spec['prepared'][role])
                        command.append(argument)
                    subprocess.run(command, cwd=invocation, env=local_env, stdout=log, stderr=subprocess.STDOUT, check=True)
                subprocess.run(['bash', 'harness/evaluate.sh'], cwd=invocation, env=local_env, stdout=log, stderr=subprocess.STDOUT, check=True)
            elapsed = time.monotonic() - before
            records.append({'input_id': input_id, 'seed': seed, 'metrics': {'wall': elapsed}})
    result = {'records': records, 'timing_scope': protocol['timing_scope'], 'gpu_count': 0, 'wall_s': time.monotonic() - started, 'compute_budget': None}
    (out / 'evaluation.json').write_text(json.dumps(result, allow_nan=False) + '\n')


if __name__ == '__main__':
    main()
