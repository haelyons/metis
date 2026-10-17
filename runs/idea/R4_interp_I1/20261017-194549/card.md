Root question: What actually stops us from autoformalizing most of published math into Lean? Is it gaps in Mathlib coverage, the step of translating informal proofs where authors skip things that are 'obvious', or something deeper about how mathematicians write? The Lean kernel is a free and perfect verifier, so this looks like one of the few domains where brute-force search can't fool itself. Could you split every paper into tiny lemma-sized subgoals and throw many different open-source prover models at each one in parallel, with each model scoped to a known failure mode like wrong definitions, mismatched conventions or silently strengthened hypotheses? Is compute a major blocker at some level, and could a shit ton of GPU parallelism fix it, or is the real bottleneck checking that the formal statement means the same thing as the English one?

**I1 · Drift probes on the autoformalizer.** R4 · interp · top pick · distance SAME · compute tested: yes · plan expects: not the lever · PASS

**Question.** Can probes on open Lean autoformalizers, trained on cheap machine-made errors, flag real misformalizations as well as probes trained on scarce expert labels?

**What is known.** FormalAlign trained a 7B alignment scorer using hidden states on synthetic Lean misalignments, about 20 per statement, but tested only on synthetic negatives, not expert-labelled real errors [formalalign]. Whether probes trained on machine-made Lean errors, at any volume, catch real expert-found misformalizations, and beat text-only classifiers already reaching 0.83 on corrected miniF2F pairs.

**Hypothesis.** Formalizers internally register statement errors, as math reasoners do [err_abs], so probes trained on machine-made errors should catch expert-found real ones.

**Restructuring.** Experts read and label statement pairs one at a time: about 1,000 labels before any probe exists. Labels need no human queue: machine-made errors and Lean-checked formalizer outputs are generated and verified simultaneously across GPUs and CPUs.

**If compute is the lever.** By 8,000 machine-labelled pairs (one node-day), probe AUROC on real errors is within 0.03 of the expert-trained probe and ≥0.70.

**If not.** Up to 32,000 pairs, the machine-trained probe stays ≥0.05 AUROC below the expert-trained probe and flat, having learned edit artifacts rather than meaning.

**Test.** Cache activations of three open Lean formalizers (7B, 8B, 32B); train linear probes on 500 to 32,000 machine-labelled pairs; score on expert-found real errors against an expert-label-trained probe and that probe copied across models side by side, plus text-only baselines.

*Compute axis.* Machine-labelled training pairs per arm, bought with parallel GPU generation and proving plus parallel Lean checks on CPU: 500–32,000 pairs, 4 levels. Closest prior: not on this axis.

**Check first.** Probe trained on machine-made errors versus probe trained on expert labels, both scored on the same held-out real misformalizations; agreement within 0.03 AUROC. Tolerance: ±0.03 AUROC, judged by the paired-bootstrap 95% CI of the difference.

**Would not show.** Reads given statements under teacher forcing, not live writing. Competition and conjecture statements, not new research definitions. Errors in the English source stay invisible. Open models up to 32B only.

*Cost.* Plans $535.16 of the $1,000 budget over 34 machine-hours, leaving $464.84. Main guess: Average GPU utilisation in mixed generation, proving and Lean pipelines [g], measured after $415.26 of spend; the budget is reached if it is 2.5× lower. 1 cost flag in the block.
