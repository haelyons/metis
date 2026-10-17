**B1 · Battery crystal discovery.** seed pick · compute tested: yes · plan expects: the lever · PASS

**Question.** Can a crystal foundation model fine-tuned on a transport proxy generate Li-ion solid electrolytes with higher conductivity than unconditioned generation or database screening?

**What is known.** Ferrogen (NeurIPS 2026) fine-tuned MatterGen on a polarization proxy with ML labels, achieving ~80x search efficiency over exhaustive screening; it never targeted ionic conductivity. No published result fine-tunes a crystal foundation model to generate battery materials conditioned on a transport property like ionic conductivity.

**Hypothesis.** Conditioning MatterGen's adapter on predicted ionic conductivity gives low-barrier candidates at higher hit rate than screening; transport labels are scarce but learnable.

**Restructuring.** The fine-tune, generate, screen, validate loop, ~3 rounds; each diffusion sample's ~1,000 sequential denoising timesteps. None: the loop's costly steps (generating, screening, NEB-validating thousands of candidates) are embarrassingly parallel; the plan splits each across GPUs, no reordering.

**If compute is the lever.** Scaling candidates to 100,000 makes the conditioned generator's hit-rate advantage over both baselines significant; at 1,000 it is within noise.

**If not.** Scaling candidates does not separate conditioned from baseline hit rates; the gap stays within seed noise at every level, so fine-tuning adds nothing.

**Test.** Fine-tune the adapter of the open-source MatterGen crystal model on predicted log conductivity; generate and screen 1k-100k candidates in each arm; NEB-validate the top ten; compare hit rate against unconditioned generation and screening of the ICSD database (about $576).

*Compute axis.* Generated candidate crystal structures screened per arm: 1,000–100,000 candidates, 3 levels. Closest prior: not on this axis.

**Check first.** Reproduce MatterGen's 38.57% S.U.N. and 0.021 Angstrom RMSD on 1,024 samples; reproduce the npj predictor's 0.85 log10 sigma MAE. Tolerance: S.U.N. within +/-3 percentage points; RMSD <= 0.1 Angstrom; predictor MAE within +/-0.1 log10 sigma..

**Would not show.** Shows predicted-conductivity and migration-barrier rankings, not measured sigma; Li conductors only; no synthesis, cycle-life, or interface data.

*Cost.* Plans $575.76 of the $1,000 budget over 174 machine-hours, leaving $424.24. Main guess: DFT-NEB cost per material [g], measured after $575.76 of spend; the budget is reached if it is 1.0× higher. 7 cost flags in the block.
