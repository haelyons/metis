# MD

Everything here is deliberately generic: one script that builds a LAMMPS box from a
SMILES string, and three input decks that take all site-specific settings on the
command line. There is no scheduler code; chain the jobs however your cluster does it.

## Building a box

```
python builder/smiles2loplsaa.py -smiles "CCCCCCCCCC1CCCCC1" \
    --target-atoms 15000 --density 0.3 --out systems/cyclohexylnonane
```

This assigns L-OPLS-AA parameters, generates a conformer with RDKit and packs the box
with Packmol (both installed by the root `environment.yml`). Boxes are packed dilute
on purpose; equilibration compresses them to the real density. The parameterisation
covers alkanes, alkenes, esters, dialkyl ethers and aromatics, including fused rings.
Anything outside that raises a `ParameterError` naming the missing type instead of
guessing. For a new molecule, check `net_charge_per_molecule` is ~0 in the
`metadata.json` it writes and run a zero-step `read_data` in LAMMPS before using it.

## Running the decks

One equilibration per molecule and temperature:

```
mpirun -np 24 lmp -in lammps/equilibrate.in \
    -var system_dir systems/cyclohexylnonane -var T 313.15
```

Then each replica is segment 1 followed by continuations, 2 ns per segment. `run_id`
sets the velocity seed; the paper used ten replicas of four segments (8 ns) per
molecule and temperature.

```
mpirun -np 24 lmp -in lammps/tdm.in \
    -var system_dir systems/cyclohexylnonane -var dump_dir runs/run_1 \
    -var T 313.15 -var run_id 1 -var seg 1

mpirun -np 24 lmp -in lammps/tdm_continue.in \
    -var system_dir systems/cyclohexylnonane -var dump_dir runs/run_1 \
    -var T 313.15 -var run_id 1 -var seg 2 -var prev_seg 1
```

Production is NVT with SHAKE on the C-H bonds and writes the pressure tensor and heat
flux every 5 steps. Viscosity and thermal conductivity come from the Green-Kubo
integrals of those series, as described in the paper. Every other knob (timestep,
damping, output rates) has its default at the top of each deck and is overridden the
same way with `-var`.

LAMMPS needs PPPM, `fix shake` and `compute centroid/stress/atom`; we used the
29Aug2024 release.

## Analysing the output

```
python analyse_tdm.py runs/cyclohexylnonane --system-dir systems/cyclohexylnonane -T 313.15
```

Reads every `run_<i>/` under the given directory and prints viscosity, thermal
conductivity and density with their uncertainties, using the Green-Kubo method
described in the paper (double-exponential fit of the running stress integral with a
bootstrap over replicas for the viscosity; a noise-floor window read of the heat-flux
integral for the thermal conductivity). Also writes `results_T<T>K.json` next to the
runs.
