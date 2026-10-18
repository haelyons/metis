<a id="card-seed-idea-1"></a>**IC-V3 · MD verification inserted into Org-Mol's ester shortlist before synthesis.** seed pick · compute tested: yes · plan expects: the lever · REJECT

**Question.** Does molecular-dynamics verification of viscosity and thermal conductivity reorder a machine-learning ester shortlist, or merely confirm it, and does the best coolant keep improving?

**What is known.** Org-Mol screened 461 monoester cooling candidates with a transformer and measured only two by synthesis; none were molecular-dynamics-verified for viscosity or thermal conductivity [s1]. No published work runs Green-Kubo viscosity and thermal conductivity over a 100-to-1000 candidate ester shortlist, so whether MD reorders the ML ranking is untested.

**Hypothesis.** Molecular dynamics will reorder the shortlist because the machine-learning viscosity error (22.5% MAPE) exceeds MD's, so better esters appear only after verification.

**Restructuring.** Each candidate's viscosity waits on one long trajectory; the ranking waits on 100, 300, then 1000 candidates. Run each candidate as parallel short replicas on separate GPUs and block-average the Green-Kubo integrals, so wall-clock shrinks by the replica count.

**If compute is the lever.** By 100 candidates the replica ranking matches the sequential baseline and diverges from ML; the best figure keeps improving through 1000.

**If not.** Replicas only match the sequential baseline by 300 candidates, and MD then merely confirms the ML ranking, unchanged from 100 through 1000.

**Test.** Rent an 8-GPU A100 node; run OPLS-AA Green-Kubo viscosity and thermal conductivity for the top 100 then 300 of Org-Mol's 461 monoesters; compare ML-vs-MD rank correlation and whether the best cooling figure keeps climbing; time a 45 ns single-trajectory baseline against parallel 5 ns replicas.

*Compute axis.* MD-verified monoester candidates: 100–1,000 candidates, 3 levels. Closest prior: 0 [s1], beyond it.

**Check first.** Green-Kubo MD (OPLS-AA) reproduces Org-Mol Ester 1's measured 40 C viscosity 6.41 cSt Tolerance: ±25% on viscosity; ±20% on thermal conductivity 0.141 W/m K.

**Would not show.** Shows single-phase ranking only, under one force field and 15 ns sampling; no synthesis, dielectric, flammability, compatibility, or stability checks.

*Cost.* Plans $984.16 of the $1,000 budget over 61.8 machine-hours, leaving $15.84. Main guess: GROMACS throughput on A100 for a 20,000-atom liquid [p], measured after $20 of spend; the budget is reached if it is 1.0× lower. 1 cost flag in the block.
