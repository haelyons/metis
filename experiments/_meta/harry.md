# Next ideas for the card pipeline (2026-10-18)

## What works

1. Cards pass when the truth is exact and outside the model. Simulator success flags, the Lean kernel and planted contamination scored verifiable 4 or 5. Battery scored 3: its truth is a predictor plus NEB, not measured conductivity.
2. A number quoted from its page anchors a card: LIBERO 98.2%, SAPG 35.7 regrasps, MatterGen 38.57% S.U.N.
3. Most rejects are citation slips, not bad ideas. W14 gave true numbers without a source. In run 2, 16 of 17 rejects were one uncited derived cost. The OpenCode I1 card used the seed's MATH-500 figure (0.953) uncited, so the judge compared it with the SMT-LIB page (0.960).
4. One reject was substantive. SEAS-3D said the prior stopped at 4 cells per process zone; the paper's own data reaches about 24.
5. Uncited novelty claims ("no one has measured...") are flagged on nearly every card but block unevenly. Battery and R3·I2 passed with that flag. Citing the prior's own future-work sentence fixes it.
6. One-line seeds collapse toward the nearest easy benchmark. The food note became a $104 width sweep of an archived home-recipe ranker. Battery held because the note named the gap: transport properties.
7. A frame check helps only when it quotes a gap from an active programme. Battery's did: MatterGen conditions on band gap and bulk modulus, not conductivity. Yet the card's cited prior, "Ferrogen", could not be found.
8. Cheap judges saturate. The cheap frame set gave battery and food 15/15 each, despite food's archived repository. In run F, `open` was 5 on 18 of 19 cards and `reshape` 1 on 15.
9. Lever points need a tenfold span bought by compute, method fixed. Food (8x), W14 (8x) and PAR-RL (6x) lost points; MPC (256x) did not.

## Independent ideas

Written before reading the two idea files.

- **Y1. Open-model evolutionary search on maths bounds.** AlphaEvolve-style loops write programs that a verifier scores exactly (circle packing, autocorrelation inequalities). More GPUs buy samples per problem, about 10^3 to 10^5, from a small open model. Anchor: a published circle-packing bound. Programmes: AlphaEvolve, ShinkaEvolve, OpenEvolve.
- **Y2. Learned AC optimal power flow proxies.** An AC power-flow solve gives exact feasibility and cost for a network's predicted dispatch. More compute buys training instances (OPFData has 300k per grid) and model size. Unknown: whether constraint violations fall with scale or hit a floor.
- **Y3. Rollout horizon of PDE surrogates on The Well.** Polymathic AI's simulated fluid fields come with published one-step error baselines. More compute buys model size. Unknown: whether larger surrogates stay valid longer on chaotic flows.
- **Y4 (interp). KataGo's blind spot on cyclic groups.** Adversarial policies beat superhuman KataGo through cyclic groups. Probe the network for group life status while search visits vary from 1 to 10^4. Unknown: whether the error sits in the representation or search repairs it.

## Comparison

Prog: an active programme with a stated gap. Truth: what the result is scored against. Anchor: a published number to reproduce. 10x: a compute quantity that can vary tenfold within $1,000. Asker: interest shown in the 10-26 note. Web checks covered Y1, Y2, C1 and N4 only.

| Idea | Prog | Truth | Anchor | 10x | Not done | Distinct | Asker | Reason |
|---|---|---|---|---|---|---|---|---|
| Y1 maths bounds search | yes | exact | yes | yes | partly | yes | n/a | ThetaEvolve (ICML 2026) already took an open 8B model to new bounds. |
| Y2 OPF proxies | yes | exact | yes | yes | partly | yes | n/a | A January 2026 paper already fits ACOPF scaling laws and finds feasibility lags. |
| Y3 PDE surrogates | yes | exact | yes | unsure | unsure | yes | n/a | Training tenfold larger surrogates may not fit the budget. |
| Y4 KataGo probes | weak | exact | yes | yes | unsure | yes | n/a | Exact and cheap, but no industrial programme would change. |
| C1 ensemble extremes | yes | ERA5, stations | yes | yes | partly | yes | n/a | Open operational weights; an EMS 2026 abstract poses the extremes question. |
| C2 Rubin brokers | yes | spectra | unsure | yes | unsure | yes | n/a | Few spectroscopic labels may hide any gain; no anchor found yet. |
| C3 methane plumes | yes | known releases | yes | weak | unsure | yes | n/a | The sensor, not compute per scene, likely sets the detection limit. |
| N1 plastic replacements | unsure | weak | unsure | unsure | unsure | yes | low | A bare line with no gap; likely to collapse as food did. |
| N2 paper review | yes | partly | yes | yes | no | no | high | Run F's R1 root already produced seven cards on it. |
| N3 markets, War Thunder | weak | future prices | no | yes | unsure | yes | high | Data and programmes are private; nothing published to reproduce. |
| N4 immersion coolants | yes | measured properties | to find | yes | no prior found | yes | medium | PFAS exit leaves a dated gap; a Toronto lab names mixture search as next. |
| N5 neuron searches | yes | simulator score | yes | yes | partly | yes | medium | Scores come from a simulator model, so truth is not independent. |
| N6 accelerator search | yes | cost model | yes | weak | unsure | partly | low | The search runs on CPUs, so GPU time is not the lever. |

## Picks

**1. Generative search for single-phase immersion coolants (asker, N4).** Seed: `experiments/_meta/picks/immersion-coolants.json`. It is the only note idea that clears most columns. It returns to transport properties, the twist that made battery the best card so far. The gap is dated: PFAS rules ended Novec production, and the market is moving to hydrocarbons and esters. Sinton's Toronto self-driving lab measures these properties and names mixture search as its next step. Risk: no anchor number is named yet. The seed pins truth to measured data, so the card is less likely to shrink to a predictor benchmark.

**2. Ensemble size for rare extremes in AIFS-ENS (director, C1).** Seed: `experiments/_meta/picks/ml-ensemble-extremes.json`. It has the strongest truth and programme of any row. ECMWF runs AIFS-ENS with 50 members, and the weights are on Hugging Face. The member count is the compute quantity itself, from 10 to 1,000. Risk: HENS ran 7,424 members of another model, so the card must cite it as the closest prior.

The asker's most personal idea, the market note, is not competitive as written. It has no public programme and no number to reproduce.
