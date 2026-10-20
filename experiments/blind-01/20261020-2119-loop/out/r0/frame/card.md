Root question: Can molecular mapping of AAV capsid-receptor interactions on brain microvascular endothelial cells determine which AAV variants transcytose across the blood-brain barrier versus remain intracellular, and for which capsid-receptor binding signatures?

**Structural coverage of capsid–receptor–glycan complexes · Structural coverage of capsid–receptor–glycan complexes.** seed pick · compute tested: yes · plan expects: unsure · PASS

**Question.** Can computed capsid–receptor structures and pH-resolved MD contact lifetimes classify which AAV capsids cross brain endothelium versus stay inside cells?

**What is known.** Adaptive-sampling Markov models matched one long villin run with up to 5,000 parallel simulations per iteration [s_bowman]; capsid work used 5 AlphaFold models per peptide [s_lrp6]. Whether computed pH-resolved contact lifetimes classify transcytosis versus retention at all; only one pair has measured pH kinetics [s_moyer].

**Hypothesis.** Epitope geometry from AlphaFold plus pH contact survival from many short replicas separates transcytosing LRP6/ALPL binders from retained capsids [s_lrp6][s_moyer].

**Restructuring.** One trajectory's 10^9–10^12 ordered 2-fs steps, each frame waiting on the last [s_jones]. Many short independent replicas run at once; contacts decorrelate inside each replica, so weak scaling beats one long run [s_kasson][s_kutzner_ens].

**If compute is the lever.** At 32 ten-ns replicas per condition the score reaches AUC ≥ 0.9 and pH ratio > 2, matching the 320-ns run [s_moyer].

**If not.** At 8–32 replicas the score stays at AUC ≤ 0.75 with no pH difference; the 320-ns run agrees, so more replicas do not help.

**Test.** ColabFold AlphaFold-Multimer on 24 peptide–receptor complexes, then 32 ten-ns GROMACS replicas per pair at pH 7.4 and 5.5 on 8 V100s; compared with 320-ns sequential runs and published binding, domain and pH-release results [s_lrp6][s_moyer].

*Compute axis.* Independent 10-ns MD replicas per (peptide, receptor, pH) condition: 8–32 replicas, 3 levels. Closest prior: 5,000 [s_bowman], not beyond it.

**Check first.** Reproduce the published AlphaFold-Multimer result: capsid peptides X1 and CAP-Mac bind LRP6 domain 1, not domains 3 and 4 [s_lrp6]. Tolerance: top-ranked of 5 models docks E1 not E3E4 for both peptides, at least 4 of 5 models agree.

**Would not show.** Ten-ns contact-survival proxies, not millisecond off-rates. Peptide–domain fragments in water, not full glycosylated capsids. Six pairs, no cell-level transcytosis measured.

*Cost.* Plans $945.84 of the $1,000 budget over 142 machine-hours, leaving $54.16. Main guess: MEM throughput on a two-V100 node, two independent runs [p], measured after $88.96 of spend; the budget is reached if it is 1.1× lower. 2 cost flags in the block.
