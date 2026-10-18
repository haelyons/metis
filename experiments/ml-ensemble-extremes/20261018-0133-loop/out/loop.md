# Idea loop: Ensemble size for rare extremes in a machine-learned weather ensemble

Root question: Do more members of a machine-learned weather ensemble buy better forecasts of rare extremes, or does error shared by all members cap the skill?

## Screen (option-critic panel, medians)

| Option | stakes | open | reshape | total | changes |
|---|---|---|---|---|---|
| O Ensemble size for rare extremes in a machine-learned weather ensemble | 5 | 5 | 1 | 10 |  |
| V1 Ensemble size for rare extremes in the HENS SFNO large ensemble | 5 | 3 | 1 | 8 | System studied: SFNO instead of AIFS-ENS. Answers HENS's unresolved question of whether its 7,424-member 4-sigma tail finding converts into ERA5-scored top-percentile probability skill and where that skill saturates. |
| V2 Ensemble size for rare extremes across a multi-season AIFS-ENS sample | 5 | 5 | 1 | 10 | Quantity more compute buys: synoptic-date and seasonal coverage at fixed member count, instead of members on seven dates. Closes the card's own 'applies to 7 dates; not a multi-season reforecast' gap, and its result is usable by ECMWF's operational AIFS-ENS verification. |
| V3 AIFS-ENS ensemble size judged against the operational physical ensemble | 5 | 5 | 1 | 10 | Comparison judged against: the operational ECMWF IFS ENS instead of ERA5 alone. Matters to ECMWF's operational ensemble design by asking whether member count can substitute for physical spread. |

No variant scored higher than the original; no second card.

## Rounds

**r0:** card PASS 2/2, critic sum 19/25 (lever 3, open 5, stakes 5, verifiable 5, internals —, reshape 1, baseline —), $963 at p_score · plan $963 · 1 GUESS. Frame: no grounded programme.
