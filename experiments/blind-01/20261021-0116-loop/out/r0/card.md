**Option 1: Exhaustive capsid–receptor complex enumeration (docking and AlphaFold-Multimer) · Exhaustive capsid–receptor complex enumeration (docking and AlphaFold-Multimer).** seed pick · compute tested: yes · plan expects: not the lever · PASS

**Question.** Does exhaustive modeling of AAV capsid–receptor complexes reveal a shared interface motif, like 3-fold-axis GPI-receptor engagement, that marks which capsids transcytose the BBB?

**What is known.** The earlier APPRAISE-AAV study used AlphaFold-Multimer, ten replicate models per matrix, to rank capsid peptides against the receptors LY6A, LY6C1 and CA4, validating one PHP.eB–LY6A pose [s_appraise]. Whether a shared 3-fold-axis GPI-engagement motif marks transcytosis-competent pairs across a whole capsid panel, or whether deeper pose sampling changes that call [s_appraise].

**Hypothesis.** Transcytosis-competent capsids engage GPI-anchored BBB receptors at the capsid 3-fold spike with a shared anchor geometry, unlike non-cognate pairs [s_appraise].

**If compute is the lever.** At 2,880 models the competent-minus-retained GPI-engagement gap reaches 0.50 or more, while at 144 models it stays below 0.25.

**If not.** The gap stays within 0.15 of its 144-model value at every depth; added poses change nothing because insert location already fixes the 3-fold site [s_cat].

**Test.** Run 72 pairs at 144, 720, 2,880 pose models on 8x A100s [s_lambda], anchored on the published PHP.eB–LY6A complex [s_appraise]; compare with the ten-model published baseline and the 144-model shallow arm against phenotype labels [s_alpl].

*Compute axis.* Capsid–receptor pose models computed per panel sweep (rigid-docking poses plus AlphaFold-Multimer seed models): 144–2,880 pose models, 3 levels. Closest prior: 10 [s_appraise_rep], beyond it.

*Restructuring.* none.

**Check first.** Rebuild the published PHP.eB peptide–LY6A complex and require its validated contacts and capsid fit before any library spend [s_appraise]. Tolerance: capsid-fragment RMSD to PDB 7WQO at most 1.5 Å (published engineered-loop RMSD is 1.36 Å) and at least 2 of the 3 named contacts (peptide Pro5', Phe6', LY6A Ala58) within 5 Å.

**Would not show.** Predicted interface geometry only, not transcytosis rates or post-binding fate; weak avidity-dependent contacts may evade prediction [s_appraise]; twelve capsids, six receptors.

*Cost.* Plans $955.84 of the $1,000 budget over 59 machine-hours, leaving $44.16. Main guess: wall minutes per AlphaFold-Multimer seed job [g], measured after $51.74 of spend; the budget is reached if it is 1.1× higher. 2 cost flags in the block.
