# autoformalizer-drift

Root question (R4 of run F): What actually stops us from autoformalizing most of published math into Lean? Is it gaps in Mathlib coverage, the step of translating informal proofs where authors skip things that are 'obvious', or something deeper about how mathematicians write? The Lean kernel is a free and perfect verifier, so this looks like one of the few domains where brute-force search can't fool itself. Could you split every paper into tiny lemma-sized subgoals and throw many different open-source prover models at each one in parallel, with each model scoped to a known failure mode like wrong definitions, mismatched conventions or silently strengthened hypotheses? Is compute a major blocker at some level, and could a shit ton of GPU parallelism fix it, or is the real bottleneck checking that the formal statement means the same thing as the English one?

Idea (option I1 of run F, `seed.json`): **Drift probes on the autoformalizer.** Probe the autoformalizer's activations while it writes definitions and statements, to flag when it has quietly strengthened a hypothesis or guessed a convention. In math, generators often 'know' they are wrong: a linear probe predicts trace correctness at 0.953 AUROC on MATH-500, against 0.674 for verbalized confidence. But transfer to other domains is weak (0.54/0.55 from MATH to ARC), the signal is 'diagnostic, not causal', and the only interp study of autoformalization (SMT-LIB, not Lean) gets 0.960 against a solver oracle but 0.679 against an LLM proxy for intent. No one has measured this on Lean, and the labels it needs are the human audit itself.

| Run | Kind | Result |
|---|---|---|
| `20261017-1945-frame` | frame check of the Claude card | Goedel-Prover 12, Kimina 12, AlphaProof 11 of 15; all 13 practice claims checked |
| `20261017-2029-card` | OpenCode card | REJECT: the hypothesis quotes an uncited AUROC (0.953; the page says 0.960); plan $489 |
| `20261017-2135-loop` | neighbours and screen | variant "probe against the production judges" tied the original at 13; no second card |

Run F's Claude card for the same idea passed 2/2 (stakes 4, lever 4, verifiable 4, open 5, reshape 4; plan $535).
