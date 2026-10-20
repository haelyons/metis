# Frame check: card

Root question: Can molecular mapping of AAV capsid-receptor interactions on brain microvascular endothelial cells determine which AAV variants transcytose across the blood-brain barrier versus remain intracellular, and for which capsid-receptor binding signatures?

Models: research opencode-go/mimo-v2.6-pro; dramaturgs opencode-go/deepseek-v4.1-flash, opencode-go/glm-5.3-flash; critics opencode-go/qwen3.8-flash, opencode-go/mimo-v2.6-flash, opencode-go/minimax-m3.
Cost $0.142 · 485,161 tokens · 14.3 min wall time.

**Best fit:** Voyager Therapeutics — TRACER capsid discovery platform / NeuroShuttle, at "Identification of the cell-surface receptor each BBB-penetrant TRACER capsid engages on brain vasculature, and whether that binding initiates receptor-mediated transcytosis, so capsids with a human-conserved receptor can be nominated as IV-delivered CNS gene therapy vectors (e.g. VY1706 tau-silencing program, ALPL-VYGR-NeuroShuttle).". Fit 3, change 3, new 5: 11 of 15.

## 1. Voyager Therapeutics — TRACER capsid discovery platform / NeuroShuttle

https://www.voyagertherapeutics.com/science-tracer/

**Step:** Identification of the cell-surface receptor each BBB-penetrant TRACER capsid engages on brain vasculature, and whether that binding initiates receptor-mediated transcytosis, so capsids with a human-conserved receptor can be nominated as IV-delivered CNS gene therapy vectors (e.g. VY1706 tau-silencing program, ALPL-VYGR-NeuroShuttle).

**Practice claims and checks:**
- DISPUTED [PARTIAL, UNSUPPORTED] Receptor mechanism is determined today by RNA-guided in vivo biopanning at library scale: a ~4E7-variant AAV9 peptide-display library is passaged in cynomolgus macaques and reduced to a focused set for further work, by the Capsid Discovery team (Tyler Moyer, Mathieu Nonnenmacher, Todd Carter). (https://www.cell.com/molecular-therapy-family/molecular-therapy/fulltext/S1525-0016(25)00373-9)
- VERIFIED [SUPPORTED, SUPPORTED] Capsid-receptor binding and the pH-release step are measured by surface plasmon resonance at the two pH values of the transcytosis pathway, one pair at a time, rather than by simulation. (https://www.cell.com/molecular-therapy-family/molecular-therapy/fulltext/S1525-0016(25)00373-9)
- VERIFIED [SUPPORTED, SUPPORTED] Transcytosis versus retention is decided with a cell-barrier assay, not with molecular simulation. (https://www.cell.com/molecular-therapy-family/molecular-therapy/fulltext/S1525-0016(25)00373-9)
- VERIFIED [SUPPORTED, SUPPORTED] Receptor knowledge is used operationally to build potency-assay cell lines overexpressing the capsid-specific receptor. (https://www.voyagertherapeutics.com/wp-content/uploads/2026/05/POSTER_Voyager_ExploitinganAAVCapsidSpecificReceptortoDevelopStableCellLinesforTransductionBasedAssaysforGeneTherapies_May_2026_FINAL.pdf)

**Activity:** active [PARTIAL, SUPPORTED] Voyager reported Q2 2026 results on 6 August 2026: FDA cleared the IND for VY1706, a TRACER-derived BBB-crossing capsid gene therapy, with dosing expected in Q4 2026; the capsid discovery team presented eight ASGCT 2026 abstracts including receptor-based potency-assay cell lines.

**If the lever:** If 32 ten-ns replicas give AUC ≥ 0.9 and pH ratio > 2, computed pH contact-survival would become a pre-filter ahead of SPR pH 7.4/5.5 dissociation and the MDCK-Transwell assay: among the ~1,500 TRACER variants of interest and the second-generation ALPL-family capsids, the team could rank pairs predicted to release at endosomal pH (transcytose) versus remain bound/retained, and only express and assay the top pairs, converting its one-pair-at-a-time pH kinetics (VCAP-102–ALPL) into a screening-grade prediction.

**If not:** Nothing would change: at AUC ≤ 0.75 with no pH difference, ten-ns contact-survival cannot substitute for SPR pH dissociation or the Transwell transcytosis model, and Voyager would keep determining transcytosis versus retention by wet-lab binding/trafficking assays plus in vivo TRACER biopanning.

**Already done:** partly [SUPPORTED, SUPPORTED] Voyager has already run the wet-lab analogue of the card's target: the single published pH-resolved capsid-receptor kinetics pair (VCAP-102 binding ALPL at pH 7.4 with rapid dissociation at pH 5.5) plus an ALPL-dependent Transwell transcytosis readout, but it has not published computed pH-resolved MD contact lifetimes classifying transcytosis versus retention across variants.

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 3 | 3, 3, 3 | 0 |
| change | 3 | 3, 4, 3 | 1 |
| new | 5 | 5, 4, 5 | 1 |

- fit, opencode-go/qwen3.8-flash: Computed pH-contact MD is a stand-in for capsid-cell transcytosis assays; programme uses SPR/Transwell and full capsids.
- fit, opencode-go/mimo-v2.6-flash: Simulated peptide-domain pH proxy feeds receptor-mechanism step only through SPR and Transwell stand-ins, at a different scale.
- fit, opencode-go/minimax-m3: Card tests LRP6 peptide-domain fragments; Voyager's TRACER pipeline screens full ALPL/TRACER capsids. Outcome feeds receptor-mapping step through a stand-in.
- change, opencode-go/qwen3.8-flash: Positive pH score could pre-filter variants; negative leaves current SPR/Transwell unchanged, so only one outcome changes.
- change, opencode-go/mimo-v2.6-flash: Positive outcome would rank ~1,500 variants before SPR/Transwell, changing which pairs to express; negative outcome changes nothing.
- change, opencode-go/minimax-m3: If lever holds, MD score pre-filters SPR one-pair-at-a-time work; if-not preserves current practice. Only the positive outcome changes a choice.
- new, opencode-go/qwen3.8-flash: Supported practice uses SPR/Transwell, not pH-resolved MD contact lifetimes; lacks measurement.
- new, opencode-go/mimo-v2.6-flash: Wet-lab pH-release and Transwell analogue exists for one pair, but no computed MD classifier across variants; partly answered.
- new, opencode-go/minimax-m3: Supported claims show Voyager lacks computed pH-resolved MD classification; only wet-lab SPR pH 7.4/5.5 kinetics and Transwell assays are in place.

## 2. Dyno Therapeutics — AI capsid design with BBB-mechanism diversity

https://www.dynotx.com/approach

**Step:** The BBB mechanism layer of AI capsid design: determining which blood-brain-barrier transport receptor an engineered capsid engages (human TfR1 for Dyno-yp2, ALPL for Dyno-9zh, or other Dyno-discovered receptors) and whether that engagement is conserved in human orthologues, before capsids are handed to CNS gene therapy partners.

**Practice claims and checks:**
- VERIFIED [SUPPORTED, SUPPORTED] Today the capsid-to-mechanism step is anchored in high-throughput in vivo screening at industrial scale rather than in molecular simulation. (https://dynotx.substack.com/p/a-computational-leap-over-an-in-vivo)
- VERIFIED [SUPPORTED, SUPPORTED] Design models are trained on in vivo measurement data from NHP experiments, optimized for cross-species translatability among other properties. (https://www.dynotx.com/news/dyno-therapeutics-launches-two-new-aav-capsids-and-ai-platform-for-rare-disease-therapeutic-development-at-the-2026-american-society-of-gene-cell-therapy-asgct-annual-meeting)
- VERIFIED [PARTIAL, SUPPORTED] Receptor mechanism for a released capsid is validated empirically by binding of the capsid to human and NHP receptor orthologues, not by computing pH-resolved contact lifetimes. (https://www.dynotx.com/news/dyno-therapeutics-launches-two-new-aav-capsids-and-ai-platform-for-rare-disease-therapeutic-development-at-the-2026-american-society-of-gene-cell-therapy-asgct-annual-meeting)
- VERIFIED [SUPPORTED, SUPPORTED] Structure-based reasoning is available in Dyno's stack through open-weight protein structure models run on its Dyno Phi agentic platform, which would be the natural insertion point for a computed transcytosis-versus-retention score. (https://www.dynotx.com/news/dyno-therapeutics-launches-two-new-aav-capsids-and-ai-platform-for-rare-disease-therapeutic-development-at-the-2026-american-society-of-gene-cell-therapy-asgct-annual-meeting)

**Activity:** active [SUPPORTED, SUPPORTED] Dyno announced two new capsids and AI-platform updates at the ASGCT Annual Meeting on 13 May 2026, including Dyno-9zh which crosses the BBB via ALPL binding, and presented further multi-mechanism data in October 2026.

**If the lever:** A validated pH contact-survival score would be added as a filter or design objective in the LEAP/Psi/Phi model stack when engineering capsids for a chosen BBB receptor (ALPL, hTfR1, or Dyno-discovered receptors): capsids predicted to bind yet remain intracellular would be discarded in silico before the 10^4–10^7 pooled in vivo screens and before NHP single-capsid validation, and the ALPL-, TfR1- and novel-receptor mechanisms could be ranked by predicted release at endosomal pH.

**If not:** No change in practice: Dyno would keep training on in vivo measurements and confirming mechanism by receptor-orthologue binding and NHP biodistribution; a ten-ns contact-survival proxy with AUC ≤ 0.75 and no pH difference would not be admitted into LEAP design filters or product claims.

**Already done:** unknown [SUPPORTED, SUPPORTED] Dyno publicly describes sequence- and structure-based generative design plus empirical receptor validation for its BBB capsids, but no public page, paper or repository shows a pH-resolved MD contact-lifetime classification of transcytosis versus retention; whether such a compute experiment has been run internally is not public.

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 3 | 3, 3, 3 | 0 |
| change | 3 | 3, 4, 3 | 1 |
| new | 5 | 3, 5, 5 | 2 |

- fit, opencode-go/qwen3.8-flash: Feeds AI mechanism layer only through peptide-domain MD proxy; not validated on engineered capsids or human conservation.
- fit, opencode-go/mimo-v2.6-flash: Card models LRP6/ALPL peptides in water; step validates orthologue binding and relies on in vivo screens, needing bridging.
- fit, opencode-go/minimax-m3: Card measures LRP6 peptide pairs; Dyno pipeline centers TfR1/ALPL on full capsids via in vivo screens. Outcome bridges through stand-in systems and scales.
- change, opencode-go/qwen3.8-flash: Positive score could filter in-silico before screens; negative keeps in-vivo training, so only one outcome changes.
- change, opencode-go/mimo-v2.6-flash: A validated score would filter designs before 10^4-10^7 in vivo screens, but needs cell-level validation the card omits.
- change, opencode-go/minimax-m3: If lever holds, MD score enters LEAP/Phi as a pre-screen; if-not preserves in vivo training. Only one outcome changes practice.
- new, opencode-go/qwen3.8-flash: Public practice lacks computed pH MD; internal state unknown, so only partly unclear.
- new, opencode-go/mimo-v2.6-flash: No public work shows pH-resolved MD classification of transcytosis versus retention; practice is in vivo screening plus orthologue binding.
- new, opencode-go/minimax-m3: Supported claim: no public pH-resolved MD contact-lifetime classifier exists in Dyno's stack; current practice uses in vivo screening and orthologue binding.

## 3. Gradinaru laboratory, California Institute of Technology — AAV capsid–receptor mapping program

https://glab.caltech.edu/gene-delivery/

**Step:** Unbiased mapping of the human cell-surface and secreted proteins each engineered AAV binds (capsid–receptor interactome on brain endothelium-relevant receptors such as LRP6), plus structural and computational resolution of the capsid–receptor binding site, to explain which engineered capsids cross the BBB and by what binding signature.

**Practice claims and checks:**
- VERIFIED [SUPPORTED, SUPPORTED] The receptor-discovery step runs at proteome scale: a pooled six-capsid screen against over 6400 human proteins covering more than 90% of the membrane proteome and secretome, with hits deconvoluted per capsid. (https://www.nature.com/articles/s41467-024-52149-0)
- VERIFIED [SUPPORTED, SUPPORTED] Binding signatures are assigned computationally with AlphaFold-Multimer models of capsid peptides against receptor domains, using 5 structural models per peptide — the exact computation the card's check-first test targets. (https://www.nature.com/articles/s41467-024-52149-0)
- VERIFIED [SUPPORTED, SUPPORTED] Predicted domain usage is confirmed experimentally by SPR of receptor domain fragments rather than by simulation of contact kinetics. (https://www.nature.com/articles/s41467-024-52149-0)
- VERIFIED [SUPPORTED, SUPPORTED] Structural work is at atomic resolution and used for rational capsid engineering: cryo-EM structures of CAP-B10 and AAV9-X1.1 with AAVR PKD2 at 2.2–2.2 Å guided variant design validated in vivo. (https://doi.org/10.1016/j.ymthe.2026.03.030)
- VERIFIED [SUPPORTED, SUPPORTED] Transcytosis relevance is validated in cells and animals (Lrp6 conditional knockout mice, human and macaque primary brain microvascular endothelial cells, hPSC-derived neurons), not by computed contact lifetimes. (https://www.nature.com/articles/s41467-024-52149-0)

**Activity:** active [PARTIAL, PARTIAL] The lab continues to publish on AAV capsid–receptor structure and BBB tropism: Brittain et al. in Molecular Therapy (28 March 2026) on the structural basis of liver de-targeting and neuronal tropism of CNS-targeted capsids, after Lin et al. in Cell Reports (31 October 2025) on human CA-IV-targeted AAVs.

**If the lever:** If the compute lever holds, the lab would triage its interactome hits with computed epitope geometry plus pH contact-survival before SPR domain-fragment assays, cryo-ET/cryo-EM and Lrp6-knockout or PBMEC validation, turning AlphaFold-Multimer epitope calls from descriptive models into a transcytosis-versus-retention classifier, and would expand from the six published peptide–domain pairs to larger computed panels.

**If not:** Practice is unchanged: AlphaFold-Multimer would remain an epitope-hypothesis generator that must be confirmed by SPR of LRP6-E1E2 versus E3E4 fragments and in vivo/primary-cell assays, and ten-ns replica MD with AUC ≤ 0.75 would not replace those experiments or inform which capsids cross the BBB.

**Already done:** partly [SUPPORTED, SUPPORTED] This lab has already run the card's check-first computation and its experimental counterpart — AlphaFold-Multimer of X1 and CAP-Mac peptides against LRP6 domains predicting YWTD domain 1, confirmed by SPR binding LRP6-E1E2 but not E3E4 — but has not published pH-resolved MD contact lifetimes or any replica-MD classifier of transcytosis versus intracellular retention.

| Criterion | Median | Scores | Spread |
|---|---|---|---|
| fit | 4 | 3, 4, 5 | 2 |
| change | 3 | 3, 4, 3 | 1 |
| new | 3 | 3, 4, 3 | 1 |

- fit, opencode-go/qwen3.8-flash: Uses programme's peptide-LRP6 AlphaFold stand-in, but transcytosis classifier is computed proxy, not endothelial/capsid validation.
- fit, opencode-go/mimo-v2.6-flash: Card reproduces the lab's own AlphaFold-Multimer LRP6 check on identical peptide-domain systems, but substitutes MD for SPR confirmation.
- fit, opencode-go/minimax-m3: Card's AlphaFold-Multimer check-first directly mirrors Gradinaru's 5-models-per-peptide LRP6 epitope mapping on the same receptor system.
- change, opencode-go/qwen3.8-flash: Positive pH-MD could reorder triage before SPR; negative leaves AlphaFold-only epitope generation, so one outcome changes.
- change, opencode-go/mimo-v2.6-flash: Computed pH score would triage interactome hits before SPR and cryo-EM, though cell-level validation the card lacks remains required.
- change, opencode-go/minimax-m3: If lever holds, AlphaFold calls become a transcytosis classifier preceding SPR/EM/KO validation; if_not keeps status. Only one outcome changes practice.
- new, opencode-go/qwen3.8-flash: AlphaFold check-first partly done, but pH-resolved MD classifier for variants is unsupported/missing.
- new, opencode-go/mimo-v2.6-flash: Lab already ran the check-first AlphaFold/SPR half, but has published no pH-resolved replica-MD classifier; partly answered.
- new, opencode-go/minimax-m3: Lab already ran AlphaFold-Multimer on X1/CAP-Mac vs LRP6 domains (part of card), but supported claims show no published pH-resolved MD replica classifier.

## Gaps named by the researcher

- No programme has published a computed classifier of AAV capsid transcytosis versus endothelial retention validated against cell-level transcytosis; both Voyager and the Gradinaru lab decide this with Transwell assays, knockout mice or NHP in vivo screens, so the card's AUC is measured against its own labels and is uncalibrated to their decision endpoints.
- The card tests peptide–receptor-domain fragments in water and so does not cover the glycosylated capsid–receptor–glycan complexes its title claims: GPI-anchored ALPL, glycosylated LRP6 and CA-IV, and the full 60-mer capsid context are absent.
- Only one measured pH-kinetics pair exists (VCAP-102–ALPL, Voyager/Moyer 2025) to anchor the pH-ratio > 2 criterion; transferability of that release mechanism to LRP6-, TfR1- or CA-IV-binding capsids is untested.
- The compute axis (8–32 replicas of 10 ns per condition) is orders of magnitude below the screening scales these programmes operate at (~4E7-variant TRACER libraries, >6400-protein interactome screens, 10^4–10^7 pooled in vivo capsid designs at Dyno), so even a working score is not yet a screening tool.
- Ten-ns contact-survival proxies are not the millisecond-scale off-rates or endosomal release steps that determine transcytosis; if the pH ratio does not separate, the card's 'if not' outcome is likely, leaving all three programmes unchanged.
- Species context is unaddressed: the card uses human fragments only, while all three programmes select on orthologue binding and humanized or NHP models (LRP6 ~98% human/mouse identity, ALPL >92% across species, CA-IV only ~55% mouse/human).
