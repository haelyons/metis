Here is a research idea, the card a planner wrote for it, and a check of which existing research or industrial programmes would use its result, with the gaps that check found.

Root question: Battery crystal discovery? Crystal foundation models: there's hella, for battery generation, transport properties are different.
Idea: {"title":"Battery crystal discovery","text":"Battery crystal discovery? Crystal foundation models: there's hella, for battery generation, transport properties are different. (from the user's notes; no further detail given)","root_link":"is the root question","compute_open":"not given (seed idea from notes)","sequential":"not given (seed idea from notes)"}
Card:
<a id="card-seed-idea-1"></a>**B1 · Battery crystal discovery.** seed pick · compute tested: yes · plan expects: the lever · PASS

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

Card verdict: PASS 1/2
Programme check: [{"name":"Microsoft Research AI for Science — MatterGen / Azure Quantum Elements (with PNNL battery collaboration)","step":"The candidate-proposal front-end of the battery-materials discovery pipeline: turning a design target (high ionic conductivity) directly into new candidate structures. Today Azure Quantum Elements proposes battery electrolytes by screening 32 million enumerated candidates, and MatterGen generates structures conditioned only on chemistry/symmetry/stability and properties like magnetic density, band gap, and bulk modulus — not ionic conductivity.","sum":15},{"name":"DTU Energy — Bhowmik / García Lastra group, 'Deep Generative Models for Inverse Design of Solid Electrolytes' (MatterGen for battery materials)","step":"The generative structure-sampling step of their MatterGen -> MatterSim -> DFT battery-discovery pipeline, and specifically their stated 'inverse design of solid electrolytes' ambition. They sample MatterGen conditioned on stability (energy above hull) and Li chemistry, then screen with MatterSim/DFT; their electrolyte-specific ML (the 400k-structure halide database) is used to fine-tune a foundation model for property prediction and MD, not for conductivity-conditioned generation.","sum":12}]
Gaps found: ["The card's cited prior 'Ferrogen (NeurIPS 2026)' could not be located; the nearest published analog (KIST / Jung-Hoon Lee, diffusion-model discovery of ferroelectrics with MatterGen) targets ferroelectric polarization, not battery electrolytes, so the transport-conditioning precedent the card leans on is unverified.","MatterGen's <=20-atom unit-cell limit and its stable, ordered-crystal training set conflict with the disordered, partially-occupied structures where fast Li conductors actually live (DTU explicitly states domain-specific training data is necessary for structurally disordered halide configurations), so both programmes would still need a disorder-aware generation step beyond this card.","The card validates with NEB migration barriers and predicted log-conductivity, not the measured conductivity that both PNNL (synthesized and measured NaxLi3-xYCl6) and DTU ultimately need, leaving a label/validation gap between the card's outcome and programme practice."]

Propose three close variants of the idea. Each changes one thing (the system studied, the quantity more compute buys, the comparison it is judged against, or the programme it is aimed at) so that its result would matter more to a named programme or close a named gap. Keep the rest of the idea. Name only systems, tools and programmes that appear above or that you are sure exist. Decide only from the text above; do not use tools.
Return only JSON: {"variants": [{"id": "V1", "title": "", "text": "the idea in three to five sentences, in the form of the original", "root_link": "", "compute_open": "", "sequential": "", "changes": "what differs from the original and which gap or programme it answers"}]}