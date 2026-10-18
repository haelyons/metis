# Ideas on two runtimes (2026-10-17)

Claude Code Workflow runs (run 2, run F) against the OpenCode runs of the same day. Numbers come from the stored results;
the scripts that read them are in the session that wrote this, not in the repo.

## What ran

| Run | Runtime and models | Ideas | Cards judged | PASS |
|---|---|---|---|---|
| run 2 | Claude, Opus | generated roots, 20 picks | 20 | 3 (16 of 17 rejects on an uncited derived cost) |
| run F | Claude: Fable framers and branches, Opus after; Sonnet critic | 5 fixed roots, 23 picks | 19 (4 halted on the cost-record defect) | 13 |
| OpenCode | DeepSeek V4 Pro producer, cheap judges | I1 again; battery and food seeds from the 10-26 note | 3 | 1 (battery, 1 of 2 checks) |

## Same idea on both runtimes: I1, drift probes on the autoformalizer

| | Claude card (run F) | OpenCode card |
|---|---|---|
| Verdict | PASS 2/2 | REJECT: the hypothesis uses AUROC 0.953 (a MATH-500 figure from another study) without its source, so the checker read it against the cited SMT-LIB page, which says 0.960 |
| Critic | Sonnet: stakes 4, lever 4, verifiable 4, open 5, reshape 4 | GLM 5.3 Flash alone: 5, 5, 3, 5, 5 |
| Plan | $535 | $489 |
| Producer context | median 6.5M tokens per run-F producer | 0.73M with cache, $0.28 |

The OpenCode producer had no shell, so no pilot measurements: it guessed 40 tokens/s for a 7B model (batched serving
runs far faster) and framed the lever as speed ("sooner than one GPU"). Its loop's best variant, probing against the
production judges, is the gap the Kimi-set frame check named for the Claude card.

## Critic scores

- Run F, 19 judged cards: stakes mean 3.2, lever 3.8, verifiable 4.7, open 5.0 (18 of 19 at 5), reshape 1.5 (15 at 1).
- OpenCode with the three-model panel, two cards: battery stakes 3, lever 5, verifiable 3, open 5, reshape 2; food 3, 3, 5, 5, 1.
- One cheap critic alone (I1) was the most lenient. `open` saturates on both runtimes.

## Frame checks

- Claude I1 card, Kimi-set frame: Goedel-Prover 12, Kimina 12, AlphaProof 11 of 15; all 13 claims checked by both checkers.
- OpenCode cards, cheap frame set: battery 15 (Microsoft MatterGen / Azure Quantum Elements) and 12 (DTU); food 15 (Meta
  GISMo) and 15 (Imperial Hyperfoods).
- The new rules applied to the stored results move only food's GISMo (15 to 13: a checker contradicted "not done") and
  flag both food steps as written in the card's terms. These runs did not research programme activity, so the archived-
  repository cap on GISMo needs a rerun.

## What the ideas became

- **Battery crystals: the best result of the day.** The producer turned the note into conditioning crystal generators on
  ionic conductivity. The frame researcher found MatterGen conditions on properties such as band gap and bulk modulus,
  not conductivity. Chosen variant: disordered Li-halide electrolytes with DTU's halide database (round 1 stopped).
- **Food ingredients: collapsed.** The producer shrank it to a $104 width sweep of a recipe model whose repository the
  researcher found archived; the card says it measures nothing about industrial formulation or footprint. REJECT.
- **I1:** stronger on Claude (pass) than on OpenCode (citation reject); the idea itself held up on both.

## Cost

- OpenCode: card $0.32 to $0.52; frame check $0.14 (cheap set) to $1.03 (Kimi set); loop calls $0.02 to $0.05. The
  day's $3.09 filled the Go 5-hour pool, which is shared across models.
- Claude run F: median context per agent 6.5M tokens (producer), 6.1M (framer), 0.19M (dramaturg), on a subscription.

## Fixes prepared for the next run

1. The frame researcher reports programme activity with a source; checkers check it; an inactive programme caps
   `change` at 1 (script).
2. A checker contradicting "not done" caps `new` at 3 (script).
3. The programme's step must be quoted from its own page and is checked; a step in the card's terms is flagged and the
   `fit` anchor caps it at 3.
4. One-line seeds go through FRAMER and WIDENER first; the screen takes the strongest option labelled SAME. The
   original in every screen is then a full option record, which removes the screen's bias towards variants.
5. The loop stops when the first card is not judged.

Still worth doing: the cheap frame set on run F's 13 PASS cards (about $2, one 5-hour window), to compare runtimes on
identical cards.

## Day 2: the memo's picks (2026-10-18)

| Experiment | Card | Frame check (best of three) | Loop |
|---|---|---|---|
| immersion-coolants (from the note) | REJECT: 2 core sources unreachable, 3 claims uncited; critic 18/25; plan $874 | 11/15, three groups at 11 (Imperial/Bath MD benchmarking, Toronto self-driving lab, SINOPEC Org-Mol) | variant scored higher; its card halted on a cost record ($7,654 against $967 stated) |
| ml-ensemble-extremes (director C1) | PASS 2/2; critic 19/25; plan $963 | 15/15 ECMWF AIFS ENS, 11 HENS, 11 Anemoi | no variant beat it |

The new frame rules ran for the first time. Activity was researched and checked for all six programmes (all active).
The step flag fired on four of six, so researchers still describe steps in the card's terms; it does not cap scores.
No inactive programme or contradicted "not done" came up, so neither cap applied. Two pipeline bugs surfaced and were
fixed: a JavaScript statement run-on in frame.js, and replies with a JSON syntax error being parsed as an inner fragment.

