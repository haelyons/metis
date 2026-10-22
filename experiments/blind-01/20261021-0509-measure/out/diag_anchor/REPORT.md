# Anchor diagnostics on the saved result of launch 10 (local, CPU, no launch)

Question answered: why did the anchor FAIL on launches 9 and 10 - is the scoring or the
correspondence wrong, or did the saved pose itself miss the published placement?

**Answer: the saved pose itself misses. Scoring and correspondence are correct for this
result. Locus `computation`, confidence high.** One narrow, general-purpose gap exists in
the frame step (d2, rotation not recovered); it is provably not exercised by the saved
result and cannot be the cause of the anchor miss (see d2 and "the d2 gap" below).

Method: `run_m4.py` (build 26) was imported read-only and only its own scoring functions
were called; the search and the computation were not re-run. All checks ran locally on CPU
under `M/.venv/bin/python`. Only `out/diag_anchor/diag.json` and this file were written.
Check order d0, d5, d1, d2, d4, d3, `diag.json` rewritten after each.

## Files of record

| role | file | sha256 |
|---|---|---|
| anchor record | `out/launch10/results_m4/out/endpoint-anchor_tag-m4.json` | f82e17515279... |
| saved anchor result (serial) | `out/launch10/results_m4/out/pose_anchor_serial_tag-m4.pdb` | 019645e87b12eaf200d2436060a9ddeb7b1021f03c4a25c133a42e3f2bf11c23 |
| saved anchor result (parallel) | `out/launch10/results_m4/out/pose_anchor_parallel_tag-m4.pdb` | 019645e87b12... (byte-identical to serial) |
| reference copy | `out/launch10/results_m4/out/pair_pair1_tag-m4.pdb`, chains A and R | 587a0f7c5104f2d8eba0c4dbeed7f8eaee7c144b5bacc09c0d2733276053fb76 |
| reference provenance | `out/launch10/results_m4/out/pairs_tag-m4.json` | 6de141e83e44... |

The reference copy: the launcher fetches `results_m4/out/` only (`lambda_run_m4.sh` fetch
lines), so the box's fetched `data/6IHB.pdb` (sha256 d3f489cc062d0a4a92490774a51f85782439d5ffd9bfae9445f4f10bf7e0f2c4)
was not copied back; no local file has that hash. The pair evidence file carries the
reference: `build_pairs` (`run_m4.py:2287`) writes the first capsid piece with
`x_shift_a: 0.0` and the receptor unshifted (`pairs_tag-m4.json`), so `pair_pair1` chains
A (capsid, residues 219-735) and R (receptor, residues 144-237) are the fetched 6IHB's two
chains at the fetched coordinates. Chain B is the stand-in copy shifted 60 A and is
excluded from the reference. Functional identity is proven by d5: scoring the saved result
against these chains reproduces the anchor record to 14 digits, so every compared atom is
the atom the box scored.

## d0 provenance - PASS

- reference copy sha256 `587a0f7c5104...` equals the hash recorded for it in
  `pairs_tag-m4.json` (`pairs[0].pdb_sha256`): match.
- `pairs_tag-m4.json` `source_pdb_sha256` `d3f489cc062d...` equals the hash in the anchor
  record's inputs for `/home/ubuntu/m4_run/data/6IHB.pdb` (`d3f489cc062d`) and the
  downloads record's full hash: match.
- `rows_anchor_tag-m4.jsonl` sha256 `49ee351bd498...` and `downloads_tag-m4.json` sha256
  `97dec50a01a5...` match the anchor record's input hashes: match.
- saved results are the files the anchor rows name (`pose_path`:
  `pose_anchor_serial_tag-m4.pdb`, `pose_anchor_parallel_tag-m4.pdb`), both present;
  serial and parallel are byte-identical (019645e87b12...).
- caveat recorded: the raw fetched 6IHB.pdb (d3f489cc062d...) is not in the fetched
  results (fetch scope); the pair file is the local copy of the reference's coordinates.

## d5 rescore - PASS (the record comes from these files)

Runner functions: `score_pose_against_native` (`run_m4.py:3689`) with native roles from
`map_chain_roles` (`run_m4.py:1017`), reference = pair1 chains A+R.

| metric | rescored now | launch 10 record | abs diff |
|---|---|---|---|
| contact_overlap | 0.0 | 0.0 | 0 |
| interface_backbone_rmsd_a | 38.61633372529515 | 38.61633372529515 | 0 |
| n_reference_contacts | 34 | 34 (rows_anchor) | 0 |
| n_pose_contacts | 114 | - | - |
| serial_parallel_rmsd_a (`whole_chain_rmsd`, :1132) | 0.0 | 0.0 | 0 |
| calls | no-bind, identical | no-bind, identical | equal |

Frame step in the rescore: `pose_frame_shift` (`run_m4.py:3640`) shift
(20.814, 14.832, 102.682) A, basis "capsid atoms matched by chain, residue and atom name",
4142 atoms matched.

## d1 round trip - PASS

Reference scored against itself (`score_pose_against_native`): contact_overlap 1.0,
interface_backbone_rmsd_a 0.0, frame shift (0, 0, 0), 34 reference contacts = 34 pose
contacts, call "bind". Perfect.

## d2 known transformation - FAIL (one metric; hand checks exact)

All values from the runner's own functions.

1. Random rigid rotation + translation of the whole reference (seed 0), scored against the
   untransformed reference: contact_overlap **1.0 (perfect)** but
   interface_backbone_rmsd_a **53.284488450165284 A** (expected 0.0). After the runner's
   frame step the capsid residual is **39.709 A**: `pose_frame_shift` (`run_m4.py:3640`)
   recovers a **translation only** (mean displacement of matched capsid atoms) and cannot
   undo a rotation. Criterion "every metric must stay perfect": not met - **FAIL**.
2. Translation-only rigid transform (the case the frame step targets): overlap 1.0,
   interface RMSD 1.4e-12 A. Perfect.
3. Hand perturbations, expected values computed from the definition (EXEC_NOTE items 17
   and 25), returned exactly by the runner:
   - reference interface backbone atoms shifted +5.0 A along x: runner returns
     interface_backbone_rmsd_a **5.0000** (expected 5.0000).
   - only non-interface receptor atoms moved 20 A: interface RMSD **0.0**, whole-chain
     RMSD (`whole_chain_rmsd`) **18.315 A** > 0 (as item 25 states).
   - 3 of 6 reference contacts kept: `contact_overlap` (`run_m4.py:1076`) returns **0.5**.

## d4 correspondence - FULL

| element | expected to pair | paired |
|---|---|---|
| reference capsid atoms (chain A) | 4143 | 4142 (frame-shift match, `pose_frame_shift`) |
| reference receptor atoms (chain R) | 725 | 725 |
| interface backbone atoms (N, CA, C, O of the 15 reference-interface residues) | 60 | 60 (`_backbone_index`, `run_m4.py:1088`) |

The single unpaired reference capsid atom is (735, OXT), dropped by the docking
preparation's `--noxt`; the frame step's own rule ("only atoms present in both are used")
covers it. Identifiers line up: pose chains A/R are the reference's letters; capsid
residues 219-735 and receptor residues 144-237 in both files; contacts are keyed by chain
role and residue number (`contact_pairs_by_index`, `run_m4.py:1059`) so chain letters
cannot change the pairing. Pose contacts can therefore pair with all 34 reference
contacts; it makes 114 contacts of its own and shares **0** of the 34.

## d3 independent scoring - AGREE (within 1 %, differences 0)

Independent implementation written from EXEC_NOTE item 17 only (own PDB column parser,
own heavy-atom pair loop at 4.5 A, own capsid-frame translation from matched capsid atoms,
no call to or copy of the runner's scoring code):

| metric | independent | runner | abs diff | agree |
|---|---|---|---|---|
| contact_overlap | 0.0 | 0.0 | 0 | yes (abs 0.01 rule near zero) |
| interface_backbone_rmsd_a | 38.61633372529515 | 38.61633372529515 | 0 | yes |
| n_reference_contacts | 34 | 34 | 0 | yes |
| n_pose_contacts | 114 | 114 | 0 | yes |

Overlap is unchanged (0.0) when the receptor chain letter is relabelled A, B or C (item
17's parenthetical), and unchanged when both parts' letters are relabelled. Independent
capsid-frame check: per-atom capsid residual after the frame translation 1.06e-11 A - the
saved result's capsid differs from the reference capsid by a **pure translation**, so the
frame step's translation-only estimate is exact here.

## The d2 gap, and why it is not the anchor's failure

The runner's frame step is translation-only (`pose_frame_shift`, `run_m4.py:3640`; applied
in `score_pose_against_native`, `run_m4.py:3689`; used by `stage_anchor`,
`run_m4.py:3826`). A pose file whose capsid is rotated relative to the reference is
therefore scored in the wrong frame (d2: 53.28 A residual instead of 0). Smallest code
change that would fix the gap: in `pose_frame_shift`, replace "their mean displacement is
the shift" with a rigid superposition (rotation + translation, e.g. Kabsch) of the matched
capsid atoms and apply that rigid motion to the whole pose. Not made here.

But this gap cannot be why the anchor failed on launches 9 and 10: the saved result's
capsid and the reference capsid differ by a pure translation (per-atom residual
1.06e-11 A over 4142 matched atoms), so the rigid fix returns the same rotation (identity)
and the same shift, and every value in the anchor record is already exact (d5, d3). A
rigid-alignment fix would leave the launch 10 verdict unchanged.

## Locus: computation, confidence high

- d0 PASS: the reference is the fetched 6IHB's own chains and the saved result is the file
  the anchor rows name (reference locus excluded).
- d5 PASS and d3 AGREE: the recorded values are exactly what these files score, under the
  runner's functions and under an independent implementation (scorer excluded for this
  result).
- d1 PASS and d2's hand checks exact: the metric machinery returns perfect and hand-computed
  values on known inputs.
- d4 FULL: every element the definition pairs is paired and identifiers line up
  (correspondence excluded).
- What is left is the saved result itself: after an exact capsid-frame re-seating the pose's
  receptor interface backbone sits **38.62 A** from the published placement and the pose
  shares **0 of 34** published contacts while making 114 contacts at another surface patch
  (tolerance: overlap >= 0.50 or RMSD <= 5.0 A). The redocking (2 swarms x 20 glowworms x
  20 steps, seed 0, per the anchor record's `docking_parameters`) landed the receptor away
  from the published site; serial and parallel agree (byte-identical poses, RMSD 0.0).

Launch 9 for comparison: same verdict (FAIL, overlap 0.0, calls identical) with
interface_backbone_rmsd_a 121.4976 A before build 26's frame step; launch 10's 38.62 A is
the same kind of miss measured in a corrected frame. The expectation that a correct run
would give ~0 A is not met by the docked pose, not by the measurement.
