# ml-ensemble-extremes

Root question: do more members of a machine-learned weather ensemble buy better forecasts of rare extremes, or does
error shared by all members cap the skill?

Proposed by the director session (`../_meta/ideas-claude.md`, C1) and picked by the idea memo (`../_meta/harry.md`):
the strongest independent truth (reanalysis and station data) and an active operational programme; the closest prior
(a very large ensemble of a different model) must be cited. `seed.json` is the memo's option record.

| Run | Kind | Result |
|---|---|---|
| `20261018-0059-loop` | loop | card done; frame check crashed on the frame.js bug |
| `20261018-0133-loop` | loop, reusing that card | card PASS 2/2, critic 19/25 (stakes 5, lever 3, verifiable 5, open 5, reshape 1), plan $963; frame researcher's JSON did not parse twice (fixed in 9a7ba5f); no variant beat the original |
| `20261018-0141-frame` | frame check of that card | ECMWF AIFS ENS 15/15 (operational since July 2025; ECMWF flags extreme-event skill as not yet assessed), HENS 11, Anemoi 11 (step flagged) |
