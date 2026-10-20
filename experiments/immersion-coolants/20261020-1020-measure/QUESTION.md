# QUESTION: does the coolant card's GPU throughput proxy hold on its own protocol, and does its p_bench gate pass?

## The question

The card "Force-field error floor for coolant MD: an enlarged C10-C50 benchmark scored against measurement" prices
every phase by one number it did not measure: `throughput_ns_day = 250` per GPU, a PROXY taken from Amber's JAC
benchmark (23,558 atoms, one A100, 611 ns/day) with "a safety factor of about 2.4". Its own `p_bench` gate reads
`throughput_ns_day >= 150`, else "drop the extension tier and re-plan with 48 molecules at 3 replicas". **Measure
the throughput of the card's own protocol on one A100 and read that gate.** The protocol, from the card's held_fixed
and the committed decks: LOPLS-AA, a 250-molecule box, 313.15 K and 1 atm, 2 fs timestep, PPPM electrostatics, SHAKE
on C-H bonds, Green-Kubo sampling of the pressure tensor and the heat flux every 5 steps, LAMMPS 29Aug2024.

Also read, on the same trajectory: the first part of the card's anchor (liquid density within 4% of the reference at
40 C), the cost of the per-5-step sampling (the Amber proxy has none; the card lists this difference itself), and
whether the deck's heat-flux compute runs on the GPU pair style at all. And measure the step the coolant pilot halted
on: packing the box.

Both outcomes are informative. A throughput at or above 150 ns/day confirms the card's plan as priced. Below 150, the
card's own else-branch applies and its USD 941 plan is under-priced by the ratio 250 / measured.

## Committed data

| File (under `data/`) | sha256 | Source |
|---|---|---|
| `MD-ML-thermophysical/MD/builder/smiles2loplsaa.py` (SMILES to LAMMPS LOPLS-AA builder) | `91cac1d5307eb3a0ab54be1cfd2fac3d01919bdd1cd35e7c75929bd016977008` | github fionn-carman/MD-ML-thermophysical @ 23121719 (Zenodo 10.5281/zenodo.21824121), copied from `../../coolant-proxy/data` and re-hashed |
| `MD-ML-thermophysical/MD/lammps/equilibrate.in` | `1e79c3f7669b8ae2e994caacc6f56dc4bfac19737f6f61a3b0f68a94269816cb` | same |
| `MD-ML-thermophysical/MD/lammps/tdm.in` (Green-Kubo production, segment 1) | `4d6a778e7148335a35bf680829a934c7ce4cc864fc6e050a3f23ed9854058a98` | same |
| `MD-ML-thermophysical/MD/lammps/tdm_continue.in` | in `out/INPUT_HASHES.txt` | same |
| `MD-ML-thermophysical/MD/README.md`, `README.md`, `environment.yml` | in `out/INPUT_HASHES.txt` | same |
| `MD-ML-thermophysical/ML/data/dataset.csv` (835-molecule reference set; row `mol_00557`) | `962d1c7e9517b04b97f73f7a016e102eb1cacbd13a190222c0f1e30aa33cded0` | same |
| `box_mol00557_n250_d0.30_s61453/{in.data,in.init,in.settings,metadata.json}` (the built box; see Pre-launch build) | appended to `out/INPUT_HASHES.txt` after the build, before triage | built here by the committed builder |

Molecule: 1-cyclohexylnonane (nonylcyclohexane), `mol_00557`, SMILES `CCCCCCCCCC1CCCCC1`, C15H30, 45 atoms. Reference
density at 40 C: **0.805 g/cm3** (dataset.csv, `density_40c`, source Experimental). 250 molecules = 11,250 atoms.

## Pre-launch build (the coolant pilot's halt point, now measured)

On this workstation, in a fresh micromamba env matching the dataset's `environment.yml` (rdkit 2025.09.5, packmol):
`smiles2loplsaa.py -smiles CCCCCCCCCC1CCCCC1 -n 250 --density 0.3 --seed 61453`. 0.3 g/cm3 is the dataset README's
own packing density ("dilute on purpose; equilibration compresses them to the real density"). Recorded: exit code,
wall-clock, `net_charge_per_molecule` from metadata.json, and a zero-step `read_data` in LAMMPS 2024.08.29 (CPU build).
The pilot packed at 0.75 g/cm3 and Packmol ended without perfect packing on all 24 boxes.

## Anchor

Density. After the deck's equilibration (minimise, 25 ps strain relaxation, 200 ps NVT, **0.5 ns NPT** at 313.15 K and
1 atm, then the deck's deform-to-mean-density step), the NPT mean density over the last 250 ps must be within **+/-4%**
of 0.805 g/cm3 (the card's anchor tolerance: "density within 4%"). The paper reports density plateaus within about
0.2 ns. Out of band: the timed system is not the liquid the card describes; throughput rows are "descriptive only;
anchor failed" (the step rate is still a fact about this box).

## What would refute each claim

- Claim A (card PROXY `throughput_ns_day = 250`): the production throughput of the deck as written (pressure tensor
  and heat flux every 5 steps), from LAMMPS's own `Performance:` line over a 200 ps segment after a 50 ps warm-up, on
  one A100 with the GPU package. Holds if within [100, 625] ns/day (2.5x either way); refuted outside.
- Claim B (card gate `throughput_ns_day >= 150`): pass or fail, read on the same number. Fail means the card's own
  text: "drop the extension tier and re-plan with 48 molecules at 3 replicas".
- Claim C (card plan USD 941 at 250 ns/day): the plan's GPU hours scale as 250 / measured. Recomputed plan cost
  reported; "under-priced" if the recomputed cost exceeds the card's USD 1,000 cap (measured below about 235).
- Claim D (card anchor, density within 4%): as in the Anchor section.
- Compatibility reading (report only, decides nothing but which variant Claim A reads): does `compute
  centroid/stress/atom` run with the GPU pair style? If LAMMPS refuses it, the deck as written cannot run on the GPU;
  Claim A is then read from the pressure-tensor-only variant with the label "viscosity-only protocol; the deck's heat
  flux does not run on the GPU pair style", and the card's thermal-conductivity arm is flagged as unpriced.
- Sampling-cost reading (report only): ns/day of three 200 ps production variants on the same equilibrated box:
  (a) deck as written; (b) pressure tensor only; (c) no per-step sampling. Ratios (c)/(a) and (b)/(a).
- Build reading (report only): Packmol wall-clock at 0.3 g/cm3 and exit code; LAMMPS install wall-clock on the box
  (the card's `l_dry` line buys 4 h for "build LAMMPS ... dry-run one molecule").

## Scope

One molecule (nonylcyclohexane), one box of 250 molecules, one GPU (A100 SXM4 40 GB, the card's GPU, at the card's
rate), one equilibration, three 200 ps production variants. The card's `p_bench` throughput only. Out of scope: the
replica spread `eta_se_frac` (3 replicas x 8 ns), the 8-molecule anchor `eta_anchor_err`, viscosity or thermal
conductivity values themselves, any CPU-only floor, the other seven molecules, p_core and beyond.

## Declared construct risks

- Throughput depends on the engine build. The conda-forge LAMMPS CUDA build (GPU package: pair and k-space on the
  GPU; bonds, SHAKE and per-atom computes on the CPU) is what is measured; a KOKKOS or a hand-compiled build could
  differ by 2x. Stated as "LAMMPS 2024.08.29, conda-forge CUDA build, GPU package, one A100".
- One molecule of 45 atoms; the card's eight anchor molecules range to 92 atoms (squalane), so boxes of 250 molecules
  range from about 11,000 to 23,000 atoms. Throughput for the larger boxes is not measured; the per-atom step rate is
  reported so a reader can scale.
- 200 ps segments: the LAMMPS Performance line averages the segment; the first seconds include neighbour-list and
  GPU warm-up. Three segments on one box are same-box reruns, not replication.
- The density anchor after 0.5 ns NPT is a plateau check, not the paper's 1 ns protocol.

## How the card maps onto this record

| Card (PLAN) field | Here |
|---|---|
| `numbers[throughput_ns_day]` PROXY 250, `measured_by: p_bench` | Claim A |
| `phases[p_bench].gate` (>= 150) | Claim B |
| `cost.lines[*]` (hours divide by throughput), `spend_cap_usd` 1000 | Claim C |
| `anchor` (density within 4%) | Claim D |
| `numbers[throughput_ns_day].differs_in` ("no per-step stress-tensor autocorrelation accumulation") | Sampling-cost reading |
| `held_fixed` (LOPLS-AA, 250 molecules, 313.15 K, 2 fs, PME, Green-Kubo estimators) | Protocol |
| `cost.lines[l_dry]` (4 h: build LAMMPS, dry-run one molecule) | Build reading |
| `numbers[eta_se_frac]`, `numbers[eta_anchor_err]`, p_core, p_ext, p_score | not measured |
