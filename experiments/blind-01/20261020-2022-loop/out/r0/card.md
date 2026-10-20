**W1 · In-silico enumeration of capsid–receptor complexes (AlphaFold-class sampling).** seed pick · compute tested: yes · plan expects: unsure · halted: cost record broken

**Question.** Does deep AlphaFold sampling of capsid peptides against receptor ectodomains converge on one transferable binding footprint that separates BBB-crossing from intracellular AAVs [S2]?

**What is known.** AFsample generated about 6000 AlphaFold-Multimer models per CASP15 target, raising mean DockQ from 0.41 to 0.55 versus 25 defaults, but never tested capsid–receptor footprint convergence [S3]. Whether many seeds converge on one capsid–receptor interface footprint or keep alternating; the only AAV application found its PHP.C2–LY6C1 pose changed with AlphaFold-Multimer version [S2].

**Hypothesis.** Deep sampling to 480 predictions per pair reveals one dominant footprint per receptor class, since the validated PHP.eB–LY6A pose was stable [S2].

**If compute is the lever.** At 480 predictions per pair, split-half contact Jaccard reaches 0.7 and one footprint holds 80% of poses across weight sets.

**If not.** Even at 480 predictions per pair, split-half contact Jaccard stays below 0.4 with two footprints alternating, as PHP.C2–LY6C1 poses changed with AlphaFold version [S2].

**Test.** Sample 36 capsid-peptide × receptor-ectodomain pairs at 30, 150 and 480 AlphaFold-Multimer predictions each; compare footprints against a default 25-prediction run and sequential versus eight-copy pipelines; score contacts against mutagenesis and PDB 7WQO [S2,S8].

*Compute axis.* AlphaFold-Multimer predictions sampled per capsid-peptide x receptor-ectodomain pair (seeds x five models x runs): 30–480 predictions per pair, 3 levels. Closest prior: 6,000 [s3].

*Restructuring.* none.

**Check first.** Our PHP.eB capsid model must match cryo-EM PDB 7WQO within 1.4 Å backbone RMSD and put LY6A A58 at the peptide interface [S2]. Tolerance: backbone RMSD <= 1.4 Å (published 0.36 Å overall, 1.36 Å in the engineered loop) and LY6A A58 within 5 Å in >= 80% of top-decile poses.

**Would not show.** Predicted footprints cannot show which AAVs transcytose across brain endothelium; cell and animal assays must do that [S2]. Glycan contacts and full-capsid trimer poses are outside this budget.

*Cost.* The cost record did not evaluate (7 errors); see the cost block.

**Halted at cost record broken.** reserved at numbers.budget_usd: budget_usd is set by the question; refer to it, do not define it; reserved at numbers.fs_usd_gib_month: fs_usd_gib_month is set by the question; refer to it, do not define it; undefined at full_scale.fs_afsample_scale.ratio_to: "budget_usd" is not a number id; undefined at full_scale.fs_trimer_pipeline.ratio_to: "budget_usd" is not a number id; undefined at full_scale.fs_wetlab_bmbc.ratio_to: "budget_usd" is not a number id

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $1,000 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-10-20
Errors     reserved at numbers.budget_usd: budget_usd is set by the question; refer to it, do not define it
           reserved at numbers.fs_usd_gib_month: fs_usd_gib_month is set by the question; refer to it, do not define it
           undefined at full_scale.fs_afsample_scale.ratio_to: "budget_usd" is not a number id
           undefined at full_scale.fs_trimer_pipeline.ratio_to: "budget_usd" is not a number id
           undefined at full_scale.fs_wetlab_bmbc.ratio_to: "budget_usd" is not a number id
           quote at numbers.min_per_pred_ppi.quote: 13.5 does not appear in the quote "As expected, reduced sampling allowed us to save approximately 4.7 times the GPU hours, translating to over 8 days in total for screening 856 interactions."; a value transformed from the page belongs in a DERIVED number
           quote at numbers.min_per_pred_colabfold.quote: 1.44 does not appear in the quote "ColabFold's 40 - 60× faster search and optimized model use allows predicting close to a thousand structures per day on a server with one GPU."; a value transformed from the page belongs in a DERIVED number
```

**Derivations.**
```
Derivations: the cost record did not evaluate.
```

**Producer says (not judged).** expected unsure (One AAV pose was mutagenesis-consistent while another changed with AlphaFold-Multimer version [S2], so convergence looks pair-specific.); compute_tested yes (Levels 30/150/480 predictions per pair differ only in how many independent seed x model jobs run side by side; that is exactly what more parallel compute buys [S1].); decides no; searched yes.

**Annotations.**
- cost record repaired: 3 expression(s) rewritten; unknown ids ignored: fs_afsample_scale, fs_trimer_pipeline, fs_wetlab_bmbc
- quote at numbers.min_per_pred_ppi.quote: 13.5 does not appear in the quote "As expected, reduced sampling allowed us to save approximately 4.7 times the GPU hours, translating to over 8 days in total for screening 856 interactions."; a value transformed from the page belongs in a DERIVED number
- quote at numbers.min_per_pred_colabfold.quote: 1.44 does not appear in the quote "ColabFold's 40 - 60× faster search and optimized model use allows predicting close to a thousand structures per day on a server with one GPU."; a value transformed from the page belongs in a DERIVED number
- question cites unknown source S2
- hypothesis cites unknown source S2
- predictions.if_not cites unknown source S2
- test_summary cites unknown source S2, S8
- novelty.closest_prior cites unknown source S3
- novelty.left_open cites unknown source S2
- anchor.what cites unknown source S2
- limits cites unknown source S2
- prose over 240 words (268)

**Root question (null).** Can molecular mapping of AAV capsid-receptor interactions on brain microvascular endothelial cells determine which AAV variants transcytose across the blood-brain barrier versus remain intracellular, and for which capsid-receptor binding signatures?

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/blind-01/20261020-2022-loop/out/r0/card/work/seed-1/seed/idea/8ff84fa5/producer.md)