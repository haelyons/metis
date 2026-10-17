# Idea loop: Drift probes on the autoformalizer

Root question: What actually stops us from autoformalizing most of published math into Lean? Is it gaps in Mathlib coverage, the step of translating informal proofs where authors skip things that are 'obvious', or something deeper about how mathematicians write? The Lean kernel is a free and perfect verifier, so this looks like one of the few domains where brute-force search can't fool itself. Could you split every paper into tiny lemma-sized subgoals and throw many different open-source prover models at each one in parallel, with each model scoped to a known failure mode like wrong definitions, mismatched conventions or silently strengthened hypotheses? Is compute a major blocker at some level, and could a shit ton of GPU parallelism fix it, or is the real bottleneck checking that the formal statement means the same thing as the English one?

## Screen (option-critic panel, medians)

| Option | stakes | open | internals | reshape | total | changes |
|---|---|---|---|---|---|---|
| O Drift probes on the autoformalizer | 3 | 5 | 5 | 5 | 13 |  |
| V1 Probe vs the production judge ensembles | 5 | 5 | 3 | 3 | 13 | Changes the comparison axis: head-to-head against the production judge ensembles (Qwen2.5-72B, QwQ-32B, negation-proving, triviality filters) rather than text-only baselines. Answers gap 5 and aims the result at Goedel-Prover and Project Numina / Kimina. |
| V2 Frozen linear probes vs fine-tuned hidden-state evaluators across open formalizers | 4 | 3 | 3 | 2 | 10 | Changes the system studied: frozen linear probes vs Fine-tuned FormalAlign-style evaluators, restricted to open formalizers with an explicit cross-model transfer arm. Answers gap 3 and, by proxy, the activation-access half of gap 2. |
| V3 Drift probes on research-level definitions (OEIS / Erdős) | 4 | 4 | 3 | 3 | 11 | Changes the programme and test distribution: research-level definition formalization for AlphaProof-Nexus (OEIS/Erdős), with an independently built expert-labelled set. Answers gap 4 and the label-availability half of gap 1. |

No variant scored higher than the original; no second card.

## Rounds

**r0:** card REJECT (1 blocking), critic sum 23/25 (lever 5, open 5, stakes 5, verifiable 3, internals —, reshape 5, baseline 3), $7 at transfer-gate · plan $489 · 5 GUESS. Frame: Goedel-Prover (Goedel-LM: Princeton Language and Intelligence with Tsinghua, Amazon, Meta FAIR, Numina), fit 3, change 4, new 5 (12/15).
