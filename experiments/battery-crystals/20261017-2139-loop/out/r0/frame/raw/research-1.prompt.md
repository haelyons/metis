Here is a research card, written to answer this root question: Battery crystal discovery? Crystal foundation models: there's hella, for battery generation, transport properties are different.

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

Find the existing research or industrial programmes this card's result would feed: named labs, companies, open-source projects or consortia doing this work now. Pick one to three. For each, use its own pages, papers or repositories to describe the step of its pipeline the card targets, and how it handles that step today: at what scale, with which tools or people. Say what each of the card's two predicted outcomes would change in that programme's practice, or that it would change nothing. Check whether that programme, or work it relies on, has already run this experiment. Cite a URL for every factual claim and copy the sentence from that page that supports it. If no programme would use the result, return no programmes and say why. Write your working notes to notes.md in your working directory.
Return only JSON: {"programmes": [{"name": "", "url": "", "step": "", "practice": [{"claim": "", "url": "", "quote": ""}], "if_lever_changes": "", "if_not_changes": "", "already_done": {"status": "yes | partly | no | unknown", "claim": "", "url": "", "quote": ""}}], "gaps": [""], "no_programme_reason": ""}