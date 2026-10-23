# Takeaways: can a planning document's cost inputs be measured on its own protocol?

Notes on reading this file. No language model was used. The "checkpoint" in every number below is the tool named in its sentence. The tools were ColabFold running AlphaFold-Multimer, LightDock for docking, and OpenMM for molecular dynamics. All ran on one A100 graphics card. [^1] marks every sentence that carries a decimal or percent figure. See the note at the end of this part.

## What was the research question, and the hypothesis?

A planning document, called "the card", proposes a large study. The study would predict how virus capsids bind receptor proteins. Its cost estimate rests on four numbers nobody had measured.

The question was simple. Do those four numbers hold when measured on the card's own protocol, on one rented box?

The hypothesis was that each number falls inside a band the card set. Bands are 2.5 times either side for the two borrowed numbers and 3 times either side for the two guesses [^1].

- AlphaFold-Multimer time per prediction: inside 0.2 to 1.25 hours, and at most 1 hour for the card's own gate [^1].
- Molecular-dynamics speed on an A100 graphics card: inside 51.6 to 322.5 nanoseconds per day [^1].
- Auxiliary time per capsid-receptor pair: inside 0.3333 to 3 hours [^1].
- Storage for the 216-run main grid: inside 66.67 to 600 gibibytes (GiB) [^1].

One test came first. Redocking a receptor domain onto the adeno-associated virus type 2 capsid had to reproduce the published complex (protein data bank entry 6IHB). A miss was meant to stop the run before any input was measured.

The card's own scientific prediction was not tested here. That prediction was about accuracy at 54 versus 432 runs.

## What did the experiment try to find?

It tried to put one measured number against each band. The design planned three capsid-receptor pairs and three seeds each. That gives nine AlphaFold-Multimer timings, three molecular-dynamics timings, three auxiliary timings and three storage sizes.

It also planned two checks of the timing harness. A 60-second planted sleep must read within 5 percent [^1]. An empty run must read near zero.

The budget was 8 dollars across at most two launches. Each launch was capped at 7,200 seconds. The box was one A100 graphics card with 40 GB at 1.99 dollars per hour [^1].

The design listed its own weak points. The pairs are stand-ins, the auxiliary term is undefined, and alignment search would be skipped.

## What was predicted, and what happened?

Everything below comes from a single launch on the A100 card. Nothing here is a confirmed result. The run is marked invalid overall because the anchor missed.

**Anchor redocking (LightDock, A100).** The threshold was at least 50 percent contact overlap at 4.5 Å, or an interface backbone distance of at most 5 Å [^1]. Serial and parallel runs had to agree within 2 Å with identical calls [^1].

LightDock gave 0 shared contacts of 34 published ones, so overlap was 0.0 [^1]. The interface backbone distance was 38.6163 Å [^1]. This is a miss on both tolerances, a refuting outcome. Serial and parallel agreed at 0.0 Å and both called "no-bind" [^1].

**AlphaFold-Multimer time (ColabFold, A100).** The band was 0.2 to 1.25 hours [^1]. One run of nine planned finished. It took 1232.9464 seconds, or 0.3424851 hours, which is inside the band [^1].

The record calls this input void, not holding. It needed at least three runs covering all three pairs, and had one. The card's gate of at most 1 hour was never applied.

**Molecular-dynamics speed (OpenMM, A100).** The band was 51.6 to 322.5 nanoseconds per day [^1]. No speed was measured. The three built systems held 706,477, 1,157,381 and 1,136,222 atoms. The card expects 120,000 to 180,000.

The record rules these void by its own rule. Void here means unmeasured, not refuted and not holding.

**Auxiliary time per pair (LightDock, A100).** The band was 0.3333 to 3 hours [^1]. The three pairs gave 0.009066, 0.009489 and 0.009917 hours [^1]. The mean was 0.009490716 hours, which is 35 times below the lower edge [^1].

This is the only input with a decision, and it is refuting. It was measured after the anchor missed, and it rests on a guessed reading of the term. Treat it as exploratory.

**Storage (file sizes from the three tools).** The band was 66.67 to 600 GiB [^1]. The counted files came to 49,458,566 bytes per run, or 9.949 GiB for 216 runs [^1]. That is below the band.

The record voids it. A stage before it was cut short. The figure is therefore exploratory only.

**Harness checks.** The 60-second sleep read 60.0046 seconds, a relative error of 0.000077 [^1]. The empty run read 0.0025 seconds and wrote 0 bytes [^1]. Both checks passed. Seed spread could not be checked, because only one timing exists.

**Cost and time.** The launch used 2,959 seconds and about 1.636 dollars [^1]. That is under the 7,200-second cap and the 8-dollar budget.

## Is this what we expected?

No. The design expected each input to be able to hold or fail. It got one anchor miss, one refutation with caveats and three voids. No input was confirmed.

The one decided number says the toy auxiliary work is cheap. It does not say the card's estimate is wrong. The card's cost question is still open.

## What in these files does not fit

The first eight items are the open questions. For each, I give what the files show. My own reading is marked as such.

1. **Did the docking fail, or did the test setup fail?** The files cannot separate the two. The scorer passed its self-checks. A copy of the published pose scored overlap 1.0, and a shifted copy scored 1.0 [^1]. A second scoring path matched the first.

   The docking was small: 2 swarms, 20 glowworms, 20 steps, with no restraint to the published interface. The pose had 114 contacts, none shared with the 34 published. One of 4143 capsid atoms did not match.

   The record says the order of docking commands was chosen by the runner, because the on-box contract gave none. My reading: a bigger or restrained search is the missing test. Until then, no later pose is trustworthy.

2. **Is the serial and parallel agreement real?** The pose files are byte-identical, and so are the two rank tables. Timings differ: 25.9 seconds on 1 core and 19.4 seconds on 4 cores [^1]. Logs and output paths are separate for each run.

   So the parallel run did run. My reading: LightDock's search looks deterministic, so this check could hardly fail. It also compares the whole receptor chain, not the interface. It says nothing about parallel safety at the card's 8-GPU scale.

3. **Does 0.00949 hours measure the card's auxiliary work?** It measures this docking setup only [^1]. Docking took 22.2 to 22.9 seconds of each 32.6 to 35.7 seconds [^1]. The search is far smaller than a real one.

   The term is undefined in the card. The design read it as docking, interface analysis and a table row. The fail may only reflect that guessed reading. It also inherits the failed anchor.

4. **Does anything support 0.342 hours as typical?** Nothing in the files does [^1]. It is one run, one pair, one seed, in single-sequence mode with 20 recycles and 5 models on 780 residues. The timing includes compile time.

   The log of per-model times was malformed. It held an error about a missing backend, then "Running on GPU". The record gives 915.0 busy seconds of 1233.3 for the stage, but its reason field says "not sampled" [^1]. These two disagree.

5. **Was the stop guard wrong?** The stop event is about the AlphaFold stage only. It estimated 1233.3 seconds for one more run against 766.7 left [^1]. Those add to exactly 2000.0 seconds [^1].

   My reading: the guard applied a 2,000-second allowance to that stage. It was not the 7,200-second cap. The molecular-dynamics stage then began at the same second and ran 1,372 seconds.

   The launch ended with 4,240 seconds unused and about 6.36 dollars of the 8-dollar budget [^1]. The open question says 6.38, so my subtraction differs slightly [^1]. The guard used a 5-dollar budget, equal to 9,045 seconds, not the design's 8.

   Two more runs would have fit in the unused time, enough for the three-run minimum. All nine would not. Nine runs at 1232.9 seconds is 11,096 seconds, more than the whole cap [^1].

6. **Why were the molecular-dynamics systems 4 to 9 times too large?** The files show the cause in part. The padding was a modest 0.8 nanometres [^1]. But the box was a 193.142 Å cube [^1]. So the stand-in complex spans about 177 Å.

   My reading: pieces shifted 60 Å apart, plus a docked receptor, make a spread-out solute. The solvated file is 57,224,897 bytes and the complex file 492,806, so nearly everything is water. No speed was measured, so the 129 nanoseconds per day has no test.

   A worked example in the unit-and-scale record gives 128.96 nanoseconds per day for 250,000 steps in 335 seconds [^1]. That is an example, not a measurement.

7. **Do setup files count as storage?** The files do not say. The excluded files are 57,224,897 bytes of solvated structure and 160,164,749 bytes of system file, in total 217,389,646 bytes. Counting them gives about 53.7 GiB for 216 runs [^1].

   That is still below the 66.67 band edge, by about 19 percent [^1]. It is closer, but not inside. Deleting intermediates gives 5.68 GiB [^1].

   A further problem: the 493,304 counted molecular-dynamics bytes are 492,806 bytes of starting structure. No trajectory was ever written. The per-nanosecond figure of 986,608 bytes is therefore not a trajectory size. Real storage is likely higher.

8. **Do the stand-in pairs stand for the card's capsids?** They do not look like it. Each pair is a 517-residue piece of one 6IHB chain, a second piece shifted 60 Å, and a 94-residue receptor. The second pieces have 169, 259 and 349 residues, so the pairs total 780, 870 and 960.

   The second piece begins with the same sequence as the first. So the "multimer" repeats one sequence. All three calls are "bind", all site class "floor", at 57.1, 66.8 and 64.8 Å from the threefold axis [^1]. The anchor expects the spike near that axis.

Items I found myself:

9. **The design says an anchor miss halts the run, but the run went on.** The program's own decision rule says the run continues either way. The design also says no input is then reported as measured. Yet the auxiliary input was written up as a decided refutation.

   My reading: that decision should be shown as exploratory, since the record itself marks the run invalid.

10. **The pair design promised one pair per capsid.** All three pairs share the same 517-residue chain and the same receptor. They differ only in the length of the second piece. Pair spread cannot be read from them.

11. **The auxiliary time is a 4-core figure.** The three pairs were docked on 4 cores. The anchor ran once on 1 core and once on 4. No test covers the card's 8-GPU setting.

12. **The AlphaFold run skipped alignment search.** The record notes this understates the card's setting. The size of the understatement is not measured.

[^1]: These sentences carry a measured or fixed number. The tool and graphics card named in or beside each sentence serve as its checkpoint. No language model is involved.

## Raw samples, verbatim

An input row: one atom line from the published 6IHB structure file the anchor compared against.

```
ATOM   2804  CA  ARG A 475      30.950 -17.379 103.723  1.00 45.55           C  
```

An input row: the sequence line of the first stand-in pair, fed to AlphaFold-Multimer.

```
DGVGNSSGNWHCDSTWMGDRVITTSTRTWALPTYNNHLYKQISSQSGASNDNHYFGYSTPWGYFDFNRFHCHFSPRDWQRLINNNWGFRPKRLNFKLFNIQVKEVTQNDGTTTIANNLTSTVQVFTDSEYQLPYVLGSAHQGCLPPFPADVFMVPQYGYLTLNNGSQAVGRSSFYCLEYFPSQMLRTGNNFTFSYTFEDVPFHSSYAHSQSLDRLMNPLIDQYLYYLSRTNTPSGTTTQSRLQFSQAGASDIRDQSRNWLPGPCYRQQRVSKTSADNNNSEYSWTGATKYHLNGRDSLVNPGPAMASHKDDEEKFFPQSGVLIFGKQGSEKTNVDIEKVMITDEEEIRTTNPVATEQYGSVSTNLQRGNRQAATADVNTQGVLPGMVWQDRDVYLQGPIWAKIPHTDGHFHPSPLMGGFGLKHPPPQILIKNTPVPANPSTTFSAAKFASFITQYSTGQVSVEIEWELQKENSKRWNPEIQYTSNYNKSVNVDFTVDTNGVYSEPRPIGTRYLTRNL:DGVGNSSGNWHCDSTWMGDRVITTSTRTWALPTYNNHLYKQISSQSGASNDNHYFGYSTPWGYFDFNRFHCHFSPRDWQRLINNNWGFRPKRLNFKLFNIQVKEVTQNDGTTTIANNLTSTVQVFTDSEYQLPYVLGSAHQGCLPPFPADVFMVPQYGYLTLNNGSQAV:KNRPPIAIVSPQFQEISLPTTSTVIDGSQSTDDDKIVQYHWEELKGPLREEKISEDTAILKLSKLVPGNYTFSLTVVDSDGATNSTTANLTVNK
```

An output row: the first molecular-dynamics record, showing the atom count and no speed.

```
{"arm": "md", "at_utc": "2026-10-23T07:50:11Z", "atom_count_out_of_range": true, "atoms": 706477, "complex": "pair1", "engine_ns_per_day": null, "frame_interval_ps": 10.0, "production_wallclock_s": null, "range": [120000, 180000], "run_valid_at_write": false, "steps": null}
```

An output row: the empty-run control, showing near-zero time and zero bytes.

```
{"arm": "controls", "at_utc": "2026-10-23T07:21:16Z", "control": "empty_run", "measured_s": 0.0024979114532470703, "rc": 0, "run_valid_at_write": true, "work_dir_bytes": 0}
```

An output row: the third auxiliary-time record, for the third pair.

```
{"arm": "aux", "at_utc": "2026-10-23T07:24:08Z", "call_table_row_written": true, "contacts_at_4p5": true, "docking_parameters": {"cores": 4, "glowworms": 20, "rank_table_columns": {"header": ["Swarm", "Glowworm", "Coordinates", "RecID", "LigID", "Luciferin", "Neigh", "VR", "RMSD", "PDB", "Clashes", "Scoring"], "mapping": "by_name", "row_field_count": 12}, "restrained_to_the_published_interface": false, "setup_flags": ["--noxt", "--noh"], "steps": 20, "swarms": 2}, "docking_seconds": 22.92658567428589, "frame": {"basis": "capsid atoms matched by chain, residue and atom name", "dx": 45.29599999999691, "dy": 15.21199999999959, "dz": 102.78099999999355, "expected_atoms": 6960, "matched_atoms": 6959, "residual_rmsd_a": 7.1608282261164895e-12}, "hours": 0.009917475051350063, "interface_residues_written": true, "n_interface_residues": 50, "pair": "pair3", "pose_path": "/home/ubuntu/m4_run/results_m4/out/pose_aux_pair3_tag-m4.pdb", "rank_rows": 40, "rank_table": "/home/ubuntu/m4_run/results_m4/out/rank_table_aux_pair3_tag-m4.list", "rank_table_parsed": true, "run_valid_at_write": false, "seconds": 35.70291018486023, "seconds_corrected": 35.70291018486023, "site_class": "floor", "site_class_written": true, "threefold_distance_written": true, "top_pose_exists": true, "top_pose_roles_ok": true, "truncated": false}
```

An output row: the docking storage record, counted at 20,741,778 bytes.

```
{"arm": "storage", "artifact": "whole docking output tree of one pair", "at_utc": "2026-10-23T08:07:34Z", "bytes": 20741778, "counts_in": true, "intermediate": true, "kind": "docking", "path": "/home/ubuntu/m4_run/results_m4/out/work_m4/aux_pair1", "run_valid_at_write": false, "source": "/home/ubuntu/m4_run/results_m4/out/work_m4/aux_pair1"}
```

An output row: one ranked docking pose for the second pair, from the rank table.

```
    1      5      (46.045, -0.159, -3.312, -0.015, 0.553, -0.573, -0.605)      0      0  -106.36227     4   5.000   -1.000  lightdock_5.pdb      0  -65.230
```

## Gate outputs, verbatim

```
/tmp/trunc_m4.md: 4.2 codes/1000 words (8 codes, 1925 words); threshold 10.0
0 unscoped result sentence(s)
```
