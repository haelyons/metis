# Working notes — B1 · Battery crystal discovery

## Task
Find programmes whose pipeline the card's result (fine-tuning a crystal foundation model
adapter on predicted ionic conductivity to generate Li-ion solid electrolytes, then
comparing hit rate vs. unconditioned generation and ICSD screening) would feed.

## Card essentials
- Prior cited: "Ferrogen (NeurIPS 2026)" — fine-tuned MatterGen on a polarization proxy.
  Could NOT be located via web search (results returned ferroelectrics LC papers, iron
  supplements, unrelated). Closest published analog found: KIST / Jung-Hoon Lee,
  "Diffusion-Model-Driven Discovery of Ferroelectrics" using MatterGen (12,800 candidates,
  ferroelectric polarization, NOT battery). See IAS abstract PDF.
- Card's "Check first" numbers (MatterGen 38.57% S.U.N., 0.021 Å RMSD on 1,024 samples)
  match the MatterGen GitHub benchmark table exactly (MatterGen 38.57 / 0.021).
- Core claim to test: no published result fine-tunes a crystal foundation model to
  generate battery materials conditioned on a transport property (ionic conductivity).

## Selected programmes (2)

### 1. Microsoft Research AI for Science — MatterGen / Azure Quantum Elements (with PNNL)
- MatterGen is the open-source crystal diffusion model (microsoft/mattergen, MIT).
- Released fine-tuned checkpoints: chemical_system, space_group, dft_mag_density,
  dft_band_gap, ml_bulk_modulus, dft_mag_density_hhi_score, chemical_system_energy_above_hull.
  -> NO transport / ionic-conductivity checkpoint. (GitHub README)
- Battery electrolyte discovery today is SCREENING, not conditioned generation:
  32.6M candidates -> ~500k stable -> 18 promising -> NaxLi3-xYCl6 synthesized & conductivity
  measured; ~1,000 cloud VMs, <80 hours. (arXiv 2401.04070; Azure blog)
- Explicit forward plan: "Future optimization of the workflow beyond screening will be based
  on the direct generation of materials with given properties, such as the method recently
  demonstrated by MatterGen." (arXiv 2401.04070)
- Baker vision: "generative materials where I can ask for list of new battery compounds with
  my desired attributes." (Microsoft Source news)
- So: card targets the candidate-proposal step (conductivity-conditioned generation) that
  MS says it is moving toward but has not built for transport properties.

### 2. DTU Energy — Bhowmik / García Lastra group ("Deep Generative Models for Inverse
   Design of Solid Electrolytes"; "Mining Chemical Space with Generative Models for
   Battery Materials")
- Pipeline: MatterGen sampling -> MatterSim MLFF screening -> DFT validation.
  Generation conditioned on stability (energy above hull) + Li chemistry, NOT conductivity.
  32,600 structures -> 12,550 S.U.N. -> 817 Li -> 91 stable -> 2 novel CATHODE candidates.
- Electrolyte-specific ML: 400k-structure halide (Li3MX6) database used to fine-tune the
  MACE-MP-0b2-large foundation model for PROPERTY PREDICTION (RMSE 154.8->10.0 meV/atom),
  i.e. prediction + MD, not conductivity-conditioned generation.
- Thesis title is literally "inverse design of solid electrolytes" but the generative
  chapter (Ch.5) delivers CATHODES; electrolytes handled by MLIP/doping/MD.
- So: card targets exactly the missing step — conditioning the generator on conductivity to
  produce electrolytes — which this group has not done.

## already_done assessment
- Microsoft: NO. Fine-tuned on mag density/band gap/bulk modulus (not transport); battery
  work was screening-based. Future-tense plan confirms not yet done.
- DTU: PARTLY. Ran MatterGen for battery generation (cathodes) and fine-tuned a foundation
  model for halide electrolyte prediction, but never conductivity-conditioned generation
  of electrolytes.

## Gaps
- Ferrogen (NeurIPS 2026) unverifiable; nearest analog is ferroelectrics, not battery.
- MatterGen ≤20-atom unit cell + stable/ordered training data conflicts with disordered,
  partially-occupied structures where fast Li conductors live (DTU: disorder essential).
- NEB barrier / predicted log-conductivity proxy ≠ measured σ that PNNL/DTU need.
