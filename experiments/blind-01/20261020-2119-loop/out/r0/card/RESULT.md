# Result

Picks 1 · PASS 1 · on-goal cards U4 1 · U3 1 · halts: none

## Table

| Pick | Result | Picked | Expected | Lever | Open → | Stakes → | Verifiable | Internals | Reshape → | Baseline | Decides at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [seed·idea·1](#card-seed-idea-1) Structural coverage of capsid–receptor–glycan complexes | PASS 2/2 | seed | unsure | 3 | — → 5 | — → 3 | 5 | — | — → 5 | 5 | $946 at p_score · plan $946 · 2 GUESS |

## Frontier (listed, not produced)

None.

## Cards

<a id="card-seed-idea-1"></a>**Structural coverage of capsid–receptor–glycan complexes · Structural coverage of capsid–receptor–glycan complexes.** seed pick · compute tested: yes · plan expects: unsure · PASS

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

**Judges.** Dramaturg: PASS 2/2. Decides at: $946 at p_score · plan $946 · 2 GUESS (critic: Decision rule needs AUC/ratio over 8,16,32; p_score assembles those, unlike pilot/anchor phases).

**Cost block.**
```
COST: computed by the pipeline from the plan's inputs
Tags: [q] set by the question [c] cited [p] cited for a different setting [m] measured by the producer [d] plan's choice [g] guess [=] computed
Budget     [q] $1,000 Lambda on-demand credit · storage covered · tax not covered · prices read 2026-10-20 · filesystem $0.20/GiB-month [q]
Spend      p_setup  Build 24 peptide–receptor models and 12 solvated systems near 80,000 atoms at pH 7.4 and 5.5; record atom counts.  8x NVIDIA Tesla V100 16GB 8×$0.79=$6.32/h  2 h  $12.64  l_setup need 1 h in a 2 h box
           p_af  ColabFold AlphaFold-Multimer: 24 complexes, 5 models each, up to 20 recycles; check the LRP6 E1 anchor before any MD.  8x NVIDIA A100 SXM 40GB 8×$1.99=$15.92/h  4 h  $63.68  l_af need 3 h in a 4 h box
           p_pilot  Two 10-ns replicas on two V100s for ALPL–VCAP-102 at both pH values; measure ns/day and contact autocorrelation tau.  8x NVIDIA Tesla V100 16GB 8×$0.79=$6.32/h  2 h  $12.64  l_pilot need 1.6 h in a 2 h box
           p_ensemble  Run 384 ten-ns replicas (32 per condition over 12 conditions) across 8 V100 GPUs.  8x NVIDIA Tesla V100 16GB 8×$0.79=$6.32/h  80 h  $505.60  l_ensemble need 76.6 h in a 80 h box
           p_baselines  Time both baselines: 8 sequential 320-ns trajectories (one per anchored condition) on the 8 V100s, plus the side-by-side copies timing.  8x NVIDIA Tesla V100 16GB 8×$0.79=$6.32/h  52 h  $328.64  l_baselines need 51.1 h in a 52 h box
           p_score  Assemble the score at N = 8, 16, 32; split-half noise; compare with published labels and the pH pair; write the report.  8x NVIDIA Tesla V100 16GB 8×$0.79=$6.32/h  2 h  $22.64  l_score need 1 h in a 2 h box
           p_ensemble  32 extra replicas on the four binder conditions  8x NVIDIA Tesla V100 16GB 8×$0.79=$6.32/h  26 h [d]  $164.32  time box; need 38.3 h (margin 0.68×)  optional
           Planned $945.84 · unallocated $54.16 · with options $1,110.16 · cap $1,000
           Instead of l_baselines: fallback: 8 sequential 80-ns anchors only, 8x NVIDIA Tesla V100 16GB 8×$0.79=$6.32/h, 13 h, $82.16 → plan $699.36
Rests on   MEM throughput on a two-V100 node, two independent runs 301 ns/day [p] "2 | Gold6148F × 2 ‡ | 2 × 20 | 2.4 | V100×2 | 300.76 | 19.95 | 23 200 | and: running N simulations on nodes with N GPUs in parallel ... and reporting the aggregate performance, i.e. the sum of the performances of the individual simulations." · differs: our system is a soluble peptide–receptor–glycan complex of about 80,000 atoms, not a membrane protein, Lambda V100 instance CPUs differ from a dual Gold6148F node · measured in p_pilot ($88.96 spent by then) · gate MD throughput per GPU for one replica ≥ 80 in p_ensemble (now 150, passes; uncut plan at it $1,634.72), else set n_replicas_max to 16 and take the short baseline instead of full sequential anchors. · budget reached at 273 (1.1× lower) · box overflows at 1.0×
           GPU-hours per AlphaFold complex 1 hours [g] rests on: ChimeraX AlphaFold timing table: a 96-residue chain takes 0.02 h and a 382-residue complex about 2.5 h on an A40, with ColabFold 2 to 10 times faster than AlphaFold 2; our 200–500-residue complexes at 20 recycles should sit near an hour. · measured in p_af ($76.32 spent by then) · budget reached at 2.33 (2.3× higher) · box overflows at 1.3×
           contact autocorrelation time in a replica 1 ns [g] rests on: peptide–surface hydrogen bonds typically break and reform within nanoseconds, far shorter than a 10-ns replica · measured in p_pilot ($88.96 spent by then) · gate contact autocorrelation time in a replica ≤ 2 in p_pilot (now 1, passes; uncut plan at it $945.84), else switch to 8 replicas of 40 ns per condition and 6 conditions, then recompute cost. · budget not reached within 1000×
           gate share of peptides whose top model binds LRP6 E1 not E3E4 ≥ 1 in p_af (now 1, passes; uncut plan at it $945.84), else stop and report that the pipeline cannot reproduce the published epitope assignment; no MD spend.
Scenarios  pilot measures half the proxied throughput; replicas halved to keep the budget → $952.16 · pilot measures about 250 ns/day per GPU; deeper replica pool → $945.84
Buys       replicas per condition at the top level: 32 [d] · pilot measures half the proxied throughput; replicas halved to keep the budget: 16 · pilot measures about 250 ns/day per GPU; deeper replica pool: 48
           MD conditions (pair x pH): 12 [d] · pilot measures half the proxied throughput; replicas halved to keep the budget: 12 · pilot measures about 250 ns/day per GPU; deeper replica pool: 12
           aggregate simulated time bought: 3.84 [=] · pilot measures half the proxied throughput; replicas halved to keep the budget: 1.92 · pilot measures about 250 ns/day per GPU; deeper replica pool: 5.76
           total AlphaFold models produced: 120 [=] · pilot measures half the proxied throughput; replicas halved to keep the budget: 120 · pilot measures about 250 ns/day per GPU; deeper replica pool: 120
Flags      uncut plan at the p_ensemble gate threshold costs $1,634.72, over budget; the plan relies on: set n_replicas_max to 16 and take the short baseline instead of full sequential anchors.
           thin headroom: the budget is reached if MEM throughput on a two-V100 node, two independent runs is 1.1× lower
Full scale One 1-μs trajectory per condition (12 μs total) to measure true pH-resolved k_off: $1,512.97 = 1.51× budget = 394× aggregate simulated time bought · inputs 1 c, 1 p ([p] MEM throughput on a two-V100 node, two independent runs)
           Full glycosylated 60-mer capsid–receptor complex near 5 million atoms, same 384 replicas: $7,298.89 = 7.3× budget = 1,900× aggregate simulated time bought · inputs 1 c, 1 p, 3 d ([p] 2M-atom ribosome throughput on a two-V100 node)
           200 capsid variants x 4 receptors x 2 pH at 32 replicas each (16,000 conditions): $64,600 = 64.6× budget = 5,380× MD conditions (pair x pH) · inputs 1 c, 1 p, 2 d ([p] MEM throughput on a two-V100 node, two independent runs)
Outside    human time: system building, analysis, writing: 24 person-hours · local machine time for analysis scripts (no local GPU): 6 hours · ColabFold MSA server and public PDB/AlphaFold databases: 1 free external services · sales tax, VAT or GST on Lambda charges: 1 not included in line totals
```

**Derivations.**
```
Derivations: each computed number with its inputs substituted
inst_usd_h_v100 = 8 * per_gpu_v100_usd_h = 8 * 0.79 = 6.32 usd/hour
inst_usd_h_a100 = 8 * per_gpu_a100_usd_h = 8 * 1.99 = 15.92 usd/hour
md_ns_gpu_day = mem_bench_aggr_ns_day / 2 = 300.76 / 2 = 150.38 ns/day/gpu
big_ns_gpu_day = rib_aggr_ns_day_v100x2 / 2 = 19.95 / 2 = 9.975 ns/day/gpu
replica_h = replica_ns * 24 / md_ns_gpu_day = 10 * 24 / 150.38 = 1.59596 hours
ensemble_gpu_h = n_replicas_max * n_conditions * replica_h = 32 * 12 * 1.59596 = 612.847 gpu-hours
ensemble_inst_h = ensemble_gpu_h / 8 = 612.847 / 8 = 76.6059 hours
baseline_agg_ns = n_replicas_max * replica_ns = 32 * 10 = 320 ns
baseline_seq_h = baseline_agg_ns * 24 / md_ns_gpu_day = 320 * 24 / 150.38 = 51.0706 hours
af_complexes = n_pairs * n_receptors = 6 * 4 = 24 complexes
af_gpu_h = af_complexes * af_h_per_complex = 24 * 1 = 24 gpu-hours
af_inst_h = ceil(af_gpu_h / 8) = ceil(24 / 8) = 3 hours
af_models_total = af_complexes * af_models = 24 * 5 = 120 models
agg_sim_us = n_replicas_max * n_conditions * replica_ns / 1000 = 32 * 12 * 10 / 1000 = 3.84 microseconds
l_setup.usd = 2 * inst_usd_h_v100 = 2 * 6.32 = 12.64 usd
l_af.need = af_inst_h = 3 = 3 h
l_af.usd = 4 * inst_usd_h_a100 = 4 * 15.92 = 63.68 usd
l_pilot.need = replica_h = 1.59596 = 1.59596 h
l_pilot.usd = 2 * inst_usd_h_v100 = 2 * 6.32 = 12.64 usd
l_ensemble.need = ensemble_inst_h = 76.6059 = 76.6059 h
l_ensemble.usd = 80 * inst_usd_h_v100 = 80 * 6.32 = 505.6 usd
l_baselines.need = baseline_seq_h = 51.0706 = 51.0706 h
l_baselines.usd = 52 * inst_usd_h_v100 = 52 * 6.32 = 328.64 usd
l_score.usd = 2 * inst_usd_h_v100 = 2 * 6.32 = 12.64 usd
l_storage.usd = storage_gib * fs_usd_gib_month = 50 * 0.2 = 10 usd
l_baseline_short.need = n_anchored_conds * replica_h = 8 * 1.59596 = 12.7677 h
l_baseline_short.usd = 13 * inst_usd_h_v100 = 13 * 6.32 = 82.16 usd
l_replicas_extra.need = 32 * n_pairs * replica_h / 8 = 32 * 6 * 1.59596 / 8 = 38.303 h
l_replicas_extra.usd = 26 * inst_usd_h_v100 = 26 * 6.32 = 164.32 usd
fs_us_per_cond = 12 * 1000 * 24 / md_ns_gpu_day / 8 * inst_usd_h_v100 = 12 * 1000 * 24 / 150.38 / 8 * 6.32 = 1512.97 usd
fs_full_capsid = n_replicas_max * n_conditions * replica_ns * 24 / big_ns_gpu_day / 8 * inst_usd_h_v100 = 32 * 12 * 10 * 24 / 9.975 / 8 * 6.32 = 7298.89 usd
fs_many_variants = 200 * 4 * 2 * n_replicas_max * replica_ns * 24 / md_ns_gpu_day / 8 * inst_usd_h_v100 = 200 * 4 * 2 * 32 * 10 * 24 / 150.38 / 8 * 6.32 = 64553.3 usd
```

**Dramaturg, not SUPPORTED.**
- sample 1 · `card:left_open` PARTIAL · page: "We observed direct capsid-receptor interaction in a cell-free assay using Surface Plasmon Resonance (SPR) analysis with recombinant ALPL, showing that VCAP-102 directly interacts with ALPL with an affinity (KD) of ∼20nm at pH7.4 (Fig. 4c). Rapid dissociation of the ALPL-VCAP-102 complex was observed at pH 5.5." · note: The quote appears on the bioRxiv preprint (PDF text retrieved via search index; direct fetch returned 429) and supports that one capsid-receptor pair (VCAP-102/ALPL) has measured pH-resolved kinetics. The open question itself needs no source. But the exclusivity claim 'only one pair has measured pH kinetics' is not stated on the page; the same preprint notes such behavior is common among other known receptor-ligand transport systems ('VCAP-102 binds ALPL with an affinity of ~20 nM at pH 7.4 and is rapidly released at pH 5. These properties are common among other known receptor ligands...'), so the quote supports one pair but not 'only one' across the field.

**Critic.**
- stakes 3 · `card:limits` "Ten-ns contact-survival proxies, not millisecond off-rates. Peptide–domain fragments in water, not full glycosylated capsids. Six pairs, no cell-level transcytosis measured." · Computed proxies only; transcytosis choice needs full capsids and cell data, so outcome affects next step indirectly.
- lever 3 · `plan:compute_axis.levels` "[8,16,32]" · Replica levels 8–32 span only 4×, below required 10× compute span, though held_fixed otherwise supports.
- verifiable 5 · `plan:scored_against` "Published labels: LRP6-dependent BBB potency of AAV9-X1.1 and CAP-Mac versus AAV9 [s_lrp6_pbmec], the E1-not-E3E4 domain assignment [s_lrp6_spr], and the measured ALPL–VCAP-102 pH release [s_moyer]." · External published labels, with prior anchor reproduction within tolerance, independently verify outcomes.
- open 5 · `card:left_open` "Whether computed pH-resolved contact lifetimes classify transcytosis versus retention at all; only one pair has measured pH kinetics [s_moyer]." · Prior villin/capsid work lacks AAV pH-resolved classification; stated gap makes result open.
- reshape 5 · `plan:restructuring.condition_phase` "p_pilot" · Pilot measures tau before ensemble; method replaces sequential dependency; prior lacks AAV system.
- baseline 5 · `plan:phases` "[{"id":"p_setup","what":"Build 24 peptide–receptor models and 12 solvated systems near 80,000 atoms at pH 7.4 and 5.5; record atom counts.","stop_rule":"2-hour timer on the 8xV100 instance."},{"id":"p_af","what":"ColabFold AlphaFold-Multime…" · Tuned baseline, same-GPU copies, occupancy check, and timed phases give measured gains.

**Producer says (not judged).** expected unsure (AlphaFold already separates binders from non-binders [s_lrp6], but ten-ns contact survival may be too short to recover the measured pH-5.5 release [s_moyer].); compute_tested yes (The test varies independent replicas per condition, exactly the quantity parallel GPU compute buys; 8, 16 and 32 are nested subsets of one 384-replica run.); decides partly; searched yes.

**Annotations.**
- uncut plan at the p_ensemble gate threshold costs $1,634.72, over budget; the plan relies on: set n_replicas_max to 16 and take the short baseline instead of full sequential anchors.
- thin headroom: the budget is reached if MEM throughput on a two-V100 node, two independent runs is 1.1× lower
- predictions.if_not: a sentence of 23 words
- test_summary: a sentence of 34 words
- novelty.closest_prior: a sentence of 26 words
- anchor.what: rewritten by the field repair
- card field anchor.what still fails: coined codes: X1
- dramaturg-2 findings failed G-find after a resample; decided as returned

**Root question (null).** Can molecular mapping of AAV capsid-receptor interactions on brain microvascular endothelial cells determine which AAV variants transcytose across the blood-brain barrier versus remain intracellular, and for which capsid-receptor binding signatures?

**Producer file.** [producer.md](/home/hal/dev/interp/metis/experiments/blind-01/20261020-2119-loop/out/r0/card/work/seed-1/seed/idea/8614e855/producer.md)

## Inventory

| Option | Title | Distance | Cluster | Total | Status | Reason |
|---|---|---|---|---|---|---|

## Log

```
pool: 0 candidate cluster(s); picked 0
seed:idea:seed: uncut plan at the p_ensemble gate threshold costs $1,634.72, over budget; the plan relies on: set n_replicas_max to 16 and take the short baseline instead of full sequential anchors.
seed:idea:seed: thin headroom: the budget is reached if MEM throughput on a two-V100 node, two independent runs is 1.1× lower
seed:idea:seed: predictions.if_not: a sentence of 23 words
seed:idea:seed: test_summary: a sentence of 34 words
seed:idea:seed: novelty.closest_prior: a sentence of 26 words
seed:idea:seed: card fields failing: anchor.what (coined codes: X1, E1)
seed:idea:seed: anchor.what: rewritten by the field repair
seed:idea:seed: card field anchor.what still fails: coined codes: X1
seed:idea:seed: dramaturg-2: degenerate: card:question; degenerate: card:if_not; degenerate: card:limits
seed:idea:seed: dramaturg-2 (resample): degenerate: card:question; degenerate: card:if_not; degenerate: card:limits
seed:idea:seed: dramaturg-2 findings failed G-find after a resample; decided as returned
```