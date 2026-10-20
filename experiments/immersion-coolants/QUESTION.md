# immersion-coolants

From the 10-26 rolling note, verbatim: "generative pipeline for discovery of single phase immersion coolants" (noted
from an open review the asker attended).

Picked by the idea memo (`../_meta/harry.md`) over the note's other ideas: it returns to transport properties
(viscosity, thermal conductivity), the twist behind the best card so far, and the field is being pushed to new fluids
as fluorinated coolants are phased out. `seed.json` is the memo's option record; the root question is the note line.

## Measure runs (added 2026-10-20)

A PASS card's load-bearing number, run as a latent_skeptic run inside this experiment, so the card's own prediction or
gate is resolved by a measurement and lands in `../_meta/LEDGER.jsonl`.

| Run | Card | Phase | Outcome | Lambda |
|---|---|---|---|---|
| `20261020-1020-measure` | V1 "Force-field error floor" (`20261018-0342-card-2`, PASS 2/2) | p_bench throughput on the card's own protocol (LOPLS-AA, 250-molecule nonylcyclohexane box, 313.15 K, 2 fs, PPPM, SHAKE, pressure tensor and heat flux every 5 steps), one A100 SXM4, LAMMPS 29Aug2024 compiled on the box with the GPU package | card PROXY 250 ns/day **refuted**: 12.6 ns/day measured (19.8x below); the card's own p_bench gate (>= 150) **fails** and its re-plan text applies; plan re-prices from USD 941 to USD 18,671; anchor density 0.795 g/cm3 vs 0.805 (-1.2%, within 4%); the heat-flux sampling costs 32% of throughput (18.4 ns/day without it); the deck's load balancing cannot run under pppm/gpu; the coolant pilot's packing halt closes: the box packs in 12 s at the README's 0.3 g/cm3 | USD 3.26 (2 launches; the first stopped by the cost/time guard) |


| Run | Kind | Result |
|---|---|---|
| `20261018-0037-loop` | loop | card done ($0.37); frame check crashed on a frame.js bug (fixed in 5360255) |
| `20261018-0100-loop` | loop, reusing that card | card REJECT (2 sources unreachable, 3 claims uncited), critic 18/25, plan $874; frame: Ewen group 11, Sinton Lab 11, Org-Mol 11 of 15; variant V1 (force-field error floor against measured data) won the screen but its card halted on a broken cost record ($7,654 computed against $967 stated) |
| `20261018-0230-card` | card for variant V1 (`seeds/V1.json`: force-field error floor against measured data) | no card: DeepSeek V4 Pro's provider blocked the producer's reply twice ("content filter"); halted |
| `20261018-0231-card` | card for variant V3 (`seeds/V3.json`: MD check of Org-Mol's ester shortlist before synthesis) | REJECT on one uncited premise (an ML viscosity error of 22.5%, not on the cited page); otherwise lever 5, verifiable 5, open 5, reshape 5, stakes 3; anchor is Org-Mol's measured Ester 1 (6.41 cSt, 0.141 W/m K); plan $984 |
| `20261018-0303-frame` | frame check of the V3 card | Org-Mol (SINOPEC, DP Technology) 15/15, LG AI Research GATE 12, Imperial/Bath MD benchmarking 11 |
| `20261018-0342-card` | V3 again (same seed, producer DeepSeek V4 Pro) | PASS 2/2: lever 5, verifiable 5, open 5, reshape 5, stakes 3; anchor tolerance widened to ±40% on the cited force-field error; plan $984; cost $0.87 |
| `20261018-0342-card-2` | V1 again, producer MiMo v2.6 Pro (`--main`) | PASS 2/2: lever 4, verifiable 5, open 5, reshape 1, stakes 3; scored only against measured data from a public 835-molecule set, after repeating a published 8-molecule run; plan $941; cost $0.30; one dramaturg resample timed out |

