**I1 · Drift probes on the autoformalizer.** seed pick · compute tested: yes · plan expects: unsure · REJECT

**Question.** Can a linear probe read Lean autoformalization drift from generator activations, and does synthetic-drift training transfer to human-audited natural misformalizations?

**What is known.** A linear SAE probe reached 0.960 AUROC against an SMT-LIB solver oracle but 0.679 against intent labels; largest compute: 950 encodings, one 27B verifier. No one has measured drift readability in Lean (only SMT-LIB), scored a probe against human audit labels, or tested synthetic-to-natural drift transfer.

**Hypothesis.** Generators encode drift they cannot verbalize: a linear probe predicts trace correctness at 0.953, so Lean misformalizations should be linearly readable.

**Restructuring.** Expert-labelled faithful/drifted pairs, one forward pass per statement, probe fit, held-out evaluation — four steps. Synthetic drift is generated in parallel by counterfactual perturbation, and forward passes over many statements run side-by-side on separate GPUs.

**If compute is the lever.** Synthetic-drift probes transfer to natural Lean misformalizations: parallel GPUs reach AUROC ≥ 0.80 at 5,000 statement-runs, sooner than one sequential GPU.

**If not.** Drift is weakly readable in Lean: probe AUROC on natural misformalizations stays near 0.679 even at 150,000 statement-runs, so it never crosses the flagging threshold.

**Test.** Cache a 7B Lean autoformalizer's hidden states over 100k+ runs; train logistic probes on synthetic drift, test on 200 human-audited natural misformalizations; time parallel 4-GPU vs sequential and sharded-copy baselines; compare AUROC to SMT-LIB 0.960/0.679.

*Compute axis.* Statement-runs (forward passes whose activations are cached and probed): 2,000–150,000 statement-runs, 3 levels. Closest prior: 950 [s_genv_oracle], beyond it.

**Check first.** Planted synthetic-drift probe hits AUROC ≥ 0.90; 4-shard parallel caching matches single-GPU sequential caching within ±0.05 AUROC; shuffle control 0.50.

**Would not show.** Shows readability, not a causal fix, and only within Lean. Cannot prove synthetic-to-natural transfer beyond the audited 200 pairs.

*Cost.* Plans $489.21 of the $1,000 budget over 198 machine-hours, leaving $510.79. Main guess: 7B generation throughput [g], measured after $2.18 of spend; the budget is reached if it is 3.2× lower.
