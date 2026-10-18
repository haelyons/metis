# Idea loop: Generative search for single-phase immersion coolants

Root question: generative pipeline for discovery of single phase immersion coolants

## Screen (option-critic panel, medians)

| Option | stakes | open | reshape | total | changes |
|---|---|---|---|---|---|
| O Generative search for single-phase immersion coolants | 5 | 4 | 1 | 9 |  |
| V1 Force-field error floor for coolant MD: an enlarged C10–C50 benchmark scored against measurement | 5 | 5 | 1 | 10 | Changes the comparison it is judged against and what compute buys: instead of a hit rate over novel candidates versus commercial fluids, it is MD-versus-measurement error over an enlarged C10–C50 benchmark that includes commercial coolants. Answers the gap that the Ewen group's MD verification covers only 8 representative molecules with no coolant figure of merit, and measures the ~10% force-field error the original card only assumes. |
| V2 MD-ranked coolant shortlist judged against a self-driving lab's measured property panel | 5 | 4 | 1 | 9 | Changes the comparison it is judged against: a self-driving lab's measured viscosity/density/heat-capacity/thermal-conductivity/dielectric panel rather than only held-out literature values for known fluids. Answers the Sinton Lab / FL01 gap (they verify experimentally and by CFD, not with MD) and turns the MD output into a shortlist a named programme can actually test. |
| V3 MD verification inserted into Org-Mol's ester shortlist before synthesis | 5 | 5 | 1 | 10 | Changes the system studied: esters only, inside a synthetically accessible space, instead of esters plus hydrocarbons, with the candidate count anchored to the existing 461-candidate shortlist. Answers the gap that the Org-Mol/SINOPEC team ML-filtered millions of esters but manually picked only two to synthesise and never MD-verified the shortlist; also partially probes whether the best figure of merit still improves from ~100 to ~1000 verified candidates. |

Variant V1 scored higher than the original and got its own card.

## Rounds

**r0:** card REJECT (2 blocking), critic sum 18/25 (lever 3, open 5, stakes 4, verifiable 5, internals —, reshape 1, baseline —), $874 at score · plan $874 · 3 GUESS. Frame: Ewen group (Imperial College London / University of Bath) — MD benchmarking of organic-liquid thermophysical properties, fit 4, change 3, new 4 (11/15).

**r1:** card halted: cost record broken, critic sum 0/25 (), . Frame: no grounded programme.
