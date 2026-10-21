Here is a research card, written to answer this root question: Can molecular mapping of AAV capsid-receptor interactions on brain microvascular endothelial cells determine which AAV variants transcytose across the blood-brain barrier versus remain intracellular, and for which capsid-receptor binding signatures?

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

Find the existing research or industrial programmes this card's result would feed: named labs, companies, open-source projects or consortia doing this work now. Pick one to three. For each, use its own pages, papers or repositories to describe the step of its pipeline the card targets, and how it handles that step today: at what scale, with which tools or people. Describe that step in the programme's own words, and copy the sentence from its own page that describes it (step_url, step_quote). Say whether the programme is active now: cite its most recent release, commit, paper or announcement, or a statement that it was archived or stopped (activity). Say what each of the card's two predicted outcomes would change in that programme's practice, or that it would change nothing. Check whether that programme, or work it relies on, has already run this experiment. Cite a URL for every factual claim and copy the sentence from that page that supports it. If no programme would use the result, return no programmes and say why. Write your working notes to notes.md in your working directory.
Return only JSON: {"programmes": [{"name": "", "url": "", "step": "", "step_url": "", "step_quote": "", "activity": {"state": "active | inactive | unknown", "claim": "", "url": "", "quote": ""}, "practice": [{"claim": "", "url": "", "quote": ""}], "if_lever_changes": "", "if_not_changes": "", "already_done": {"status": "yes | partly | no | unknown", "claim": "", "url": "", "quote": ""}}], "gaps": [""], "no_programme_reason": ""}