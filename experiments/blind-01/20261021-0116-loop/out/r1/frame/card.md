Root question: Can molecular mapping of AAV capsid-receptor interactions on brain microvascular endothelial cells determine which AAV variants transcytose across the blood-brain barrier versus remain intracellular, and for which capsid-receptor binding signatures?

**V3 · Motif calls emitted for Capsida NR001–NR005 and Lir Starfish binding-assay readouts.** seed pick · compute tested: yes · plan expects: not the lever · PASS

**Question.** Can computed capsid–receptor binding calls for ALPL, AAVR and LRP6 reproduce published bind/no-bind readouts with interfaces at the threefold axis?

**What is known.** Shay and colleagues in 2024 ran five AlphaFold-Multimer models per peptide and used cryo-ET to map where LRP6 and IL3 bind engineered capsids, with SPR binding labels [s_shay_af]. Whether hundreds of pose and seed runs improve bind/no-bind agreement with threefold-axis geometry across a full capsid-by-receptor grid remains untested [s_shay_af].

**Hypothesis.** Pairs that bind in plate- and bead-based assays share threefold-axis or insert-loop engagement geometry, so pose enumeration recovers published bind/no-bind labels [s_aavr_struct].

**If compute is the lever.** Balanced accuracy 0.80 at 432 runs versus 0.55 at 54, with five of six known binders within 5 Å of published sites.

**If not.** Accuracy moves under 0.05 between 54 and 432 runs and at most three of six binders reach published sites; extra runs resample the wrong basin.

**Test.** Thirty-six capsid–receptor pairs run docking, three AlphaFold-Multimer seeds, two 5-ns MD relaxations; calls and threefold-site geometry scored on published labels; parallel wall-clock versus serial one-GPU and independent-copy baselines.

*Compute axis.* Independent capsid–receptor model runs (docking, AlphaFold-Multimer, MD relaxation) the answer needs: 54–432 model runs, 3 levels. Closest prior: 10 [s_shay_af], beyond it.

*Restructuring.* none.

**Check first.** Redocking AAVR-PKD2 onto AAV2 must place it beside the threefold spike matching PDB 6IHB contacts; serial and parallel pilots must match calls. Tolerance: >=50% contact overlap at the published 4.5 Å cutoff or interface backbone RMSD <=5 Å; serial versus parallel top-pose RMSD <=2 Å with identical bind/no-bind calls.

**Would not show.** Binding-call agreement and interface geometry only; no transcytosis or affinity. Public labels cover 13 of 36 pairs; NR001–NR005 and Starfish assays are proprietary.

*Cost.* Plans $506.83 of the $1,000 budget over 40 machine-hours, leaving $493.17. Main guess: GROMACS throughput on one A100 [p], measured after $107.46 of spend; the budget is reached if it is 4.5× lower.
