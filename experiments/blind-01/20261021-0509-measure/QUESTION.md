# QUESTION: do the card's unmeasured load-bearing inputs hold on its own protocol?

Compiled by launch.js measure from `experiments/blind-01/20261021-0116-loop/out/r1/card/result.json` (sha256 d4538bfe7fb86d888780206819a7f75846595034bc18ad47e65848d954359813); no one read the card to write this. Card seed:idea:1: "Motif calls emitted for Capsida NR001–NR005 and Lir Starfish binding-assay readouts"; plan USD 506.83333333333326; calibration state calibration_required.

## The question

For each load-bearing input the card's cost rests on, measure it on the card's own protocol on one rented box, within the owner's calibration cap, and read the result against the card's own gate. The card's planned run is not executed.

## Committed data

- `experiments/blind-01/20261021-0116-loop/out/r1/card/result.json`: sha256 d4538bfe7fb86d888780206819a7f75846595034bc18ad47e65848d954359813; its calibration record is copied to `CARD.json`.
- Input 1: af2_h_per_run, basis PROXY, value 0.5, measured in phase p1_pilot (line l_pilot: 6 h, USD 95.52); spend through that phase USD 107.5; the budget is reached at 5.32x; differs from its source in: monomer timing formula, not a 750–1000-residue hetero-multimer with 5 models and up to 20 recycles, Lambda A100 SXM 40 GB instead of an A40.
- Input 2: md_ns_per_day_a100, basis PROXY, value 129, measured in phase p1_pilot (line l_pilot: 6 h, USD 95.52); spend through that phase USD 107.5; the budget is reached at 4.483x; differs from its source in: our system is a docked capsid–receptor complex in explicit solvent, roughly 120k–180k atoms, Lambda A100 SXM 40 GB.
- Input 3: aux_h_per_pair, basis GUESS, value 1, measured in phase p1_pilot (line l_pilot: 6 h, USD 95.52); spend through that phase USD 107.5; the budget is reached at 7.48x.
- Input 4: n_storage_gib, basis GUESS, value 200, measured in phase p2_main (line l_main: 24 h, USD 382.1); spend through that phase USD 498.9; the budget is reached at 53.84x.

## Anchor

Redocking AAVR-PKD2 onto AAV2 must place it beside the threefold spike matching PDB 6IHB contacts; serial and parallel pilots must match calls. Published value PKD2 bound to the AAV2 spike region adjacent to the icosahedral three-fold axis (PDB 6IHB), tolerance >=50% contact overlap at the published 4.5 Å cutoff or interface backbone RMSD <=5 Å; serial versus parallel top-pose RMSD <=2 Å with identical bind/no-bind calls [s_aavr_struct]. The run reproduces it first; a miss stops the run before the inputs are measured.

## What would refute each claim

- C1: measured af2_h_per_run outside [0.2, 1.25] (PROXY: band 2.5x either side). the card's gate af2_h_per_run <= 1 is then applied to the measured value, else "take the docking-plus-MD fallback line with one AlphaFold-Multimer seed per pair, or move the grid to 12 pairs".
- C2: measured md_ns_per_day_a100 outside [51.6, 322.5] (PROXY: band 2.5x either side). the card's gate af2_h_per_run <= 1 is then applied to the measured value, else "take the docking-plus-MD fallback line with one AlphaFold-Multimer seed per pair, or move the grid to 12 pairs".
- C3: measured aux_h_per_pair outside [0.3333, 3] (GUESS: band 3x either side). the card's gate af2_h_per_run <= 1 is then applied to the measured value, else "take the docking-plus-MD fallback line with one AlphaFold-Multimer seed per pair, or move the grid to 12 pairs".
- C4: measured n_storage_gib outside [66.67, 600] (GUESS: band 3x either side). the card names no gate on it.

## Scope

One rented box; the measuring phase's protocol as the card states it: Run the 54-run pilot (3 capsids x 3 receptors) on 8x A100 and measure af2_h_per_run, md_ns_per_day_a100, aux_h_per_pair and seed-to-seed SD of calls.; Run the 216-run main grid on 8x A100; emit the plate-layout call table and bead-panel CSV with bind/no-bind, score, interface residues, distance to nearest threefold axis and site class.. Cost cap: the lesser of the phase's own line and the owner's calibration cap (USD 10 without re-approval; above USD 20 needs approval before launch). No production phase runs.

## Declared construct risks

- af2_h_per_run is a PROXY: its source setting differs in monomer timing formula, not a 750–1000-residue hetero-multimer with 5 models and up to 20 recycles, Lambda A100 SXM 40 GB instead of an A40.
- md_ns_per_day_a100 is a PROXY: its source setting differs in our system is a docked capsid–receptor complex in explicit solvent, roughly 120k–180k atoms, Lambda A100 SXM 40 GB.
- aux_h_per_pair is a GUESS: no page states it; the card's value is the producer's estimate.
- n_storage_gib is a GUESS: no page states it; the card's value is the producer's estimate.
- The producer's own local pilots, if any, ran on a shared CPU host and are not GPU measurements.
- One sample on one box unless the phase repeats; run-to-run spread is not measured.

## How the card maps onto this record

Card key seed:idea:1. Predictions: if_lever "Balanced accuracy 0.80 at 432 runs versus 0.55 at 54, with five of six known binders within 5 Å of published sites."; if_not "Accuracy moves under 0.05 between 54 and 432 runs and at most three of six binders reach published sites; extra runs resample the wrong basin."; noise rule "Three independent seed sets per run level, mean and SD reported; a gap counts only if it exceeds 2x the SD across seed sets and a paired permutation test over the 13 labels gives p < 0.05."; the producer expects if_not. This run resolves the inputs only; the card's own decision rule is not evaluated here.
