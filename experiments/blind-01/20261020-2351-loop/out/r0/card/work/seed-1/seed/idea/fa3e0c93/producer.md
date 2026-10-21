# producer.md — endosome-md plan (working file)

Option: "pH-resolved capsid and glycan dynamics from molecular simulation" (id endosome-md).
Budget: up to $1,000 of Lambda on-demand GPU credit. Prices as supplied in the run (read 2026-10-21, https://lambda.ai/pricing).

## What to build

All-atom explicit-solvent MD of the VP3 trimer (the icosahedral 3-fold unit) of four capsids
— AAV9, AAV2, BR1, BR1N — at endosomal pH 7.4, 5.5 and 4.0, plus AAV9 with terminal
galactose (Gal-NAc, pose from PDB 7MTZ/7MUA) at pH 7.4 and 5.5.

Why the trimer: the 3-fold unit contains (a) the AAV9 galactose pocket (Asn470, Asp271,
Asn272, Tyr446, Trp503 — "located in a pocket in the proximity of the 3-fold axis, on the
surface wall of the 3-fold spikes", Penzes 2021) and (b) the BR1/BR1N insertion site
(NRGTEWD between R588 and Q589, variable region VIII) whose single Q587N difference flips
BBB fate (Kawabata 2023). The 5-fold pore descriptor of Minzoni 2026 is out of budget
(needs a pentamer arm; listed in full_scale).

pH is modeled by discrete protonation states per condition (PROPKA3; review His229, His423,
His629, Glu564 — the pH-sensitive residues of the cryo-EM series).

Descriptors per trajectory (pre-registered, no fishing):
- spike loop 585-595 RMSF (BR1/BR1N region)
- VRI 263-269 order (BBB-related loop; ordered by galactose binding in cryo-EM)
- pH-quartet contact occupancy (Glu564/Arg391/Tyr705/His527 region)
- N-terminal 201-213 exposure (cryo-EM "column"/externalization proxy)
- Gal-NAc contact occupancy with Trp503 and interaction energy (glycan arm)

## Baseline

Published pH-resolved AAV capsid MD: 500 ns x 2 serotypes x 3 pHs = 3 us aggregate on AAV8/AAV9
5-fold assemblies, no glycans, no fate labels (Minzoni 2026,
https://doi.org/10.3390/pharmaceutics18091053 / open copy
https://digitalcommons.mtu.edu/michigantech-p2/2986/).

Sequential baseline timed: one 150-ns replica at a time on one A100.
Copies baseline timed: one replica per A100 on the 8-GPU instance, no MPS.
Parallel version: two replicas per GPU via CUDA MPS (steps of independent replicas interleave).

## How we check it is right

1. Anchor (published value): AAV9 stays galactose-bound at pH 5.5 and glycan binding orders
   VRI (Penzes 2021, PMC8428384). Our Gal-NAc arm must keep a Trp503 contact in >= 80% of
   frames of the last 100 ns at pH 5.5 and 7.4, and VRI RMSF with glycan must drop vs apo.
2. Anchor (structure): cryo-EM Cα RMSD pH 4.0 vs 7.4 is 0.5 A; our averaged structures must
   differ by <= 1.0 A over the VP3 core.
3. Cross-code: one 20-ns GROMACS repeat (same force field, same protonation states) must agree
   within 10% on Gal-NAc contact occupancy.
4. Equilibration: Cα RMSD plateau < 2 A over final 2 ns of a 5-ns NPT equilibration.
5. Noise: independent velocity seeds; class gaps must exceed 2 pooled replica SDs and keep sign
   in both halves of each trajectory.

## Cost (Lambda, A100 SXM 40GB at $1.99/GPU-h)

Throughput proxy (PROXY, measured in pilot): 180 ns/day per A100 for a ~175k-atom trimer,
conservatively below the power-law interpolation of the official OpenMM A100 benchmarks
(ApoA1 92,224 atoms = 445.35 ns/day; Cellulose 408,609 atoms = 126.69 ns/day;
https://github.com/openmm/openmm-org/issues/94). MPS packing gain 1.25 (PROXY from
https://github.com/openmm/openmm/issues/3082: ApoA1 on A100, 203.198 ns/day single vs
256.53 ns/day with 2 MPS processes = 1.26x).

Design: 14 conditions x 2 replicas x 150 ns = 28 trajectories = 4.2 us aggregate.
need_main_h = 24*4200/(180*1.25*8) = 56.0 h wall-clock on one 8-GPU instance.
Time box 58 h at 8 x $1.99 = $923.36. Pilot 4 h x 1 GPU = $7.96. Storage 30 GiB x 14 d = $2.80.
Contingency allotment $40. total_stated = $974.12; spend_cap_usd = 1000.

Baselines for the parallel claim: copies (8 GPUs, 1 rep/GPU) = 24*4200/(180*8) = 70 h;
single chain (1 GPU) = 24*4200/180 = 560 h.

Optional top-up (16 h, $254.72): 8 more replicas so the four capsids reach 4 replicas at pH 5.5.
Full scale (not affordable here): 4 replicas on all conditions (56 trajectories) and a VP3
pentamer arm for the 5-fold pore descriptor.

## Predictions (same measured quantity: class-separation ratio at pH 5.5)

- if_lever: at 28 trajectories the separation ratio exceeds 3.0; packed GPUs reach it in 56 h
  versus 70 copy-hours and 560 sequential hours.
- if_not: at 28 trajectories the ratio stays below 1.5 or sign-flips across replica halves;
  packing then buys no earlier conclusion, only more noisy replicas.
- expected: unsure — BR1 and BR1N differ by one residue, so any capsid-intrinsic signature is
  small and 150-ns replicas may be too short to resolve it.

## Execution notes

No local compute tool was available in this run (no shell), so no pilot was executed locally and
no number has basis MEASURED; ns_day_a100 and packing_gain are PROXY with measured_by = pilot,
and the pilot phase gate stops or shrinks the campaign if throughput is below plan.

Sources fetched this run: PMC8428384 (Penzes 2021), PMC10036519 (Kawabata 2023), the NVIDIA MPS
OpenMM blog, openmm/openmm-org#94, openmm/openmm#3082, the Minzoni 2026 abstract via
digitalcommons.mtu.edu and doi.org, and the Lambda price sheet text supplied in the prompt.
