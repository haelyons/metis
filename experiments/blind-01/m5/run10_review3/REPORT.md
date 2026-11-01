Independent harness3 review — 2026-11-01

Prepared-record selection conforms to amended U50 mechanism. No new per-unit computation, environment, scale, output-path or entry-point change found. All 16 units, 800 owned paths and recorded costs pass independent checks. Earlier native-selector objection and inherited absolute-path objection no longer establish a new unit-file defect under amended contract.

Overall certification remains **unknown**, rather than a demonstrated **needs_fix**: future subset PDB byte equality and exhaustive inherited dependency write confinement cannot be established from these records. `contract_met=unknown` and `verdict=unknown` preserve those limits; they do not mean CSV selection violates amended U50. No implementation correction identified. Files provide a statically conforming candidate for U51; this review does not supply U51's result or certify later concurrency.

**Scope and evidence.** Writes only inside `run10_review3/`. No workload or harness execution, box contact, network fetch, git command, credential, `.keys`, or `~/.codex/` read. `bash -n` parsed five shell files. Three embedded Python blocks parsed with `ast.parse`; only detached standard-library CSV selector executed, against review-owned CSV fixtures. Configuration validator, docking, chain repair and scoring never executed.

**Measured** means local byte/file comparison, syntax check, fixture check or arithmetic over recorded outputs. **Read** means source, configuration, log or contract statement. **Inferred** means consequence, not observed candidate behavior. Paths relative to experiment directory unless absolute. `O` = `run9/agent/harness/run_command.sh`; `U` = `run10_harness3/run_units.sh`; `R` = `run9/agent/results/reproduce/out/`. Log line numbers count LF separators, retaining embedded carriage-return progress updates.

Read `run10_harness3/REPORT.md`, `run10_diff/REPORT.md`, both earlier review reports and unit/output reader reports. Relevant assertions checked against actual files. Unrelated earlier resource/profiling analyses were not repeated. Current contract read directly at `/home/hal/dev/interp/metis-wt/dut/pipeline/m5/SCHEMAS.md:47–79,102–116`: exact command/environment at 54, path/write rules at 55, amended U50 at 56, MPS at 57, U51 at 70–79, sampling at 114. No contract copy or pipeline file changed.

Measured sizes before selective reads: reproduce 2.1 GiB, including results 330 MiB, run_command 669 MiB, temporary tree 1.1 GiB; agent workflow 4.3 MiB; harness 1.3 MiB. Profile final-decoy tree 329 MiB. Read named logs/configuration/source events and listed final PDBs. No profiler database/capture, native temporary outputs or raw-decoy archive opened. Retained source archives outside run9 measured 22 MiB PINDER and 26 MiB FroDock; read selected source members only.

Review artifacts: `audit.py`, `audit.json`, `run_units.diff`, `sample_frodock_setup.csv`, selected primary-source copies under `evidence/`. Audit records every unit's paths, hashes, costs and evidence lines. Audit imports no experiment package. All checks passed.

**Original copies and source identity — measured/read.** All six files from `run9/agent/harness/` match harness3 bytes, permission modes and nanosecond mtimes. Their hashes match writer's table at `run10_harness3/REPORT.md:15–20`; full measurements in `audit.json`. In particular, original command SHA-256 is `08d645d90c83ce0548f72e9a0b6a6e2a038bf188f8c6f13eefae1f385f231ae5`. Manifest bytes match `run10_harness/units.json`; SHA-256 `2dc822ae36db864b407cdb1c2e4878c933a286d42975b1317b3694935856ec55`.

Primary source independently recovered from retained local archives, without fetching. PINDER `/home/hal/.cache/blind01/intake_check_dl/codex/pinder_code.1.body` SHA-256 `b577532820ebbe5c16432b78c5e9c197690e863cb70a0a35a8ebcbe5277b76dd`; FroDock `/home/hal/.cache/blind01/intake_check_dl/acquire/gcp_mirror_package.body` SHA-256 `91b9aeff747346046c7f8c4c92fa5749c9f082d8122ee9d2d4769855d35368f4`. Both match `R/setup/setup_record.json:2–7`. PINDER pin `ebeb28a2f8411363cef722b7d293c978f7442672`. Selected copies match earlier `run10_inputs/evidence/` files wherever present. These copies preserve original source line numbers.

Run9's own saved source event corroborates adapter: `run9/agent/wf/agents/0006-anchors-repair/codex-1.jsonl:103`, completed command `exec-188fbfc5-f134-441e-ad67-2c7cf9c1c1a3`, exit 0. Decoded adapter matches archived source ignoring final whitespace. Event 129 corroborates core-location excerpt. Decoded outputs saved under `evidence/run9_source_event_{103,129}.txt`; their historical commands were read, never executed.

`R/setup/setup.log:14–18` records applying fixes to main.py and adapter. Applied patch `R/setup/pinder_frodock_fixes.applied.patch` equals original harness patch byte for byte. `O:126–174` additionally restores ligand HETATM chain labels. Successful measured log `R/run_command/run_command.log:11116–11117,16201` records `PREDICT_EXIT=0`, `CHAIN_LABELS_RESTORED models=100 atoms=2700`, `EVAL_EXIT=0`. These repairs belong to measured reference, as amended U50 requires. Original-study mirror identity remains unresolved (`R/setup/setup_record.json:7`; brief materials section); that inherited provenance limit is distinct from candidate-versus-measured-reference parity.

**1. Every difference and classification.** Complete independently generated unified diff appears below and in `run_units.diff`. Only three diff hunks exist. Original lines 21–116 equal U23–118 byte for byte; entire O117–185 equals U149–217 byte for byte.

| O lines | U lines | Difference | Classification |
| --- | --- | --- | --- |
| 2 | 2 | Comment names restricted prepared records. | Message/comment text |
| 4–6 | 4–7 | Invocation documents positional ids; comments disclose inherited absolute PATH/TMPDIR. | Argument handling; message/comment text; no cwd change |
| 10 | 11 | Comment describes requested jobs. | Subset description; no per-unit scale change |
| 12 | 13 | Comment describes 50 decoys per selected job. | Subset description; message/comment text |
| after 19 | 21 | No ids prints stderr error, exits 2 before environment/output initialization. | Argument handling; message text |
| after 116 | 118–120 | Additional blank/comments explain selection and existing input route. | Message/comment text; subset description |
| after 116 | 121 | Same Python interpreter receives target CSV and quoted `"$@"`. | Argument handling; subset selection |
| after 116 | 122–126 | Imports csv, io, Path, re, sys. | Argument/subset implementation |
| after 116 | 127,148 | Added blank separators. | Formatting accompanying selection; no additional behavior |
| after 116 | 128–129 | Reads target path and requested ids. | Argument handling; subset selection |
| after 116 | 130–131 | Rejects empty/duplicate requests. | Argument handling; message text |
| after 116 | 132–134 | Reads original raw lines; parses CSV for mapping only. | Subset selection |
| after 116 | 135–138 | Rejects unexpected schema, empty source or non-original physical-record layout. | Subset validation; message text |
| after 116 | 139–141 | Maps original id/kind to wrapper key; rejects duplicate source keys. | Subset selection/validation; message text |
| after 116 | 142–144 | Rejects invalid or unknown requested keys. | Argument handling; subset validation; message text |
| after 116 | 145 | Overwrites same private target with original header and original selected byte lines, argument order. | Subset selection; no output-location change |
| after 116 | 146 | Prints `RESTRICTED_UNITS=` to existing command log. | Message text; same log path |
| after 116 | 147 | Closes helper heredoc. | Subset implementation |

Status conventions: argument handling **yes**, subset selection **yes**, messages/log paths **yes**. Last flag reflects added messages/comments, not relocated log. Output locations, environment, thread setting, configuration/scale, binary/entry, cwd and other differences all **no**. New stdlib helper is selection logic, not an additional published prediction/preprocess entry. Reduced number of records is authorized subset dimension; all per-unit scale values remain fixed. Comments and blank lines do not count as independent `diff_other` behavior.

**2. Same explicit per-unit computation; future byte identity unknown.**

**Read/measured:** same interpreter `baseline-published/venv/bin/python`, same console script `baseline-published/venv/bin/pinder_methods`, same action and arguments (`O119–120/U151–152`):

```sh
"$VPY" "$VENV/bin/pinder_methods" predict --method "$METHOD" --data_dir data/frodock \
    --results_dir "$RESULTS" --subset pinder-s --pairs all --config "$RUN_DIR/frodock_config.yaml"
```

Same YAML path and contents: `n_solutions: 50`, `mpi_np: 8`, `force: false` (`O75–82/U77–84`; saved `R/run_command/frodock_config.yaml:1–3`). Same native executable lookup, four FroDock binaries and SOAP file (`O45–48,71–72/U47–50,73–74`). Saved build log `R/setup/setup.log:22–26` records compiled-binary hashes and SOAP verification; unit wrapper requests those same installed paths, with no source/binary edit.

Same explicit environment (`O21–48/U23–50`): zero GPUs, `CUDA_VISIBLE_DEVICES=''`, release 2024-02, `PINDER_BASE_DIR=data`, INFO log level, unbuffered Python, unset `PINDER_DATA_DIR`, same CUDA discovery/PATH, `PYTHONDONTWRITEBYTECODE=1`. Same `TMPDIR` construction (`O66/U68`). No wrapper `cd`. Fresh work directory supplied by U51/probe; original adapter's per-job temporary cwd unchanged.

Same eight MPI ranks and eight scoring workers; no new OMP/MKL/OpenBLAS setting. Actual total helper/library thread counts remain unestablished, but no configured-thread difference exists. Native `--th 10` remains unchanged docking argument; do not infer ten OS threads from that spelling.

For each original record, same installed driver passes same parsed id/kind/receptor/ligand fields and parameters. `evidence/main.py.txt:102–140`, interpreted with recorded patch `:3–20`, loads results setup CSV and iterates `to_dict("records")` in order. Adapter `evidence/predict.py.txt:209–233`, interpreted with patch `:53–64`, uses original structural paths under same data_dir. Adapter fresh stage directory and staged inputs retained (source `:54–57`, patch `:24–30`), same MPI/native stages and SOAP input (`:79–137`), same pose assembly (`:139–166`), same final paths (patch `:43–48`). No selected-unit numerical code changed.

Same chain restoration/archive/validation (`O126–174/U158–206`) and same `pinder_eval --max_workers 8` (`O180/U212`). Repair examines each selected unit's own files. Scoring combines selected metrics and missing-case penalties; shared metrics/leaderboard generally differ from full run. Manifest correctly excludes them. Evaluator source writes these CSVs under eval_dir (`evidence/eval_run.py.txt:82–100`); shown scorer does not feed summary back into docking PDBs.

**Measured:** 800/800 listed final reproduce PDBs equal corresponding profile PDBs byte for byte, **342,779,850 bytes per run**. Both full prepared CSVs also match. Independent repeat of earlier readers' byte comparison, not merely trust in hashes/reports. Both saved executions use same full ordering; no candidate subset execution occurred.

**Read/inferred:** source contains remaining wall-clock dependence. Adapter desolvation grids use `-m 3` (`evidence/predict.py.txt:100–106`), grid calls `ASA::localSAS` (`evidence/frodockgrid.cpp.txt:395–427`), SAS seeds `CRandomMersenne` with `time(0)` (`evidence/sas.cpp.txt:683–690`), conditional geometry rotation consumes random value (`:747–759`). Grid places SAS values in ASA PDB occupancy (`evidence/frodockgrid.cpp.txt:456–458`), subsequently consumed by docking. MPI build enables `MPI_RELEASE` and links `lsas_gcc` (saved make fragments `grid_MPI_GCC_subdir.mk.txt:20`, `grid_MPI_GCC_objects.mk.txt:7`). This is inherited behavior, not a new subset seed policy. It neither proves selected structures enter that branch nor proves final PDB mismatch.

Therefore same explicit calls/parameters/inputs **yes**; stronger requested guarantee that every listed unit's future files **would** be byte-identical **unknown**. Code parity and two full-run matches cannot establish all isolation/order/concurrency outcomes. `same_computation_per_unit=unknown` uses that stronger question, not a finding of altered algorithm. Original remote structural-input and installed executable trees were not retained for independent fresh rehashing.

**3 and 6. Writes, absolute paths, MPS, inherited conflict.**

**Read:** every explicit wrapper write stays under out/: log/history/results moves (`U53–66`), temp directory (`U67–68`), YAML/list (`U77–84,145`), decoys/repair/archive/manifest/scoring (`U151–215`). Selector adds one write to existing `out/results/frodock_setup.csv`; no new path or data/source write. Native temporary work uses fresh tempfile directory; unchanged TMPDIR directs it under invocation's out/tmp. Bytecode disabled. Relative output formulas unchanged.

**Read:** definite absolute-path conflict already in original:

```sh
# O47 / U49
export PATH="$PWD/baseline-published/frodock/bin:$PWD/$VENV/bin:$PATH"
# O66 / U68
export TMPDIR="$PWD/out/tmp"
```

These construct absolute paths into current invocation's run/work directory, conflicting with literal SCHEMAS line 55. They are not fixed paths to a previous run. TMPDIR still targets allowed out/. Same paths preserved in both files, and new helper uses relative target only. Thus `inherited_path_conflict=yes`, `unit_files_add_path_conflict=no`. Amended line 56 explicitly records inherited conflict separately; do not reintroduce earlier reviews' rejection of candidate solely for that inheritance. Replacing only U's exports would change measured environment; no such fix recommended.

**Unknown:** whole dependency write confinement. Primary core source can create missing release directory (`evidence/core_index_utils.py.txt:28–55`), download/write missing index (`:90–134`) or metadata (`:151–193`). Existing evaluator can create native directory/download missing native (`evidence/eval_method.py.txt:231–251`). Setup prepares inputs and saved runs succeeded, so these conditions are not evidence they occur on prepared run9 trees. No complete runtime write trace or complete audit of every transitive dependency establishes absence either. `writes_only_out_or_temp=unknown` means this inherited end-to-end uncertainty, not a demonstrated forbidden selector write. No new missing-data branch, downloader, preprocessing or dependency introduced.

**Read:** U contains no `CUDA_MPS_*` read/assignment/unset/override or daemon control; same retained measured code has no added MPS operation. Thus `mps_untouched=yes`. Empty CUDA visibility is inherited separate setting.

Exit handling retained exactly: U150–156 captures/returns prediction status; U211–217 uses `${PIPESTATUS[1]}` and returns scorer status. Selection errors propagate through original errexit. No-ids exits 2 before output setup. Adapter's inherited native `subprocess.run(cmd, shell=True)` lacks `check=True` (`evidence/predict.py.txt:127–137`); wrapper propagates published entry status, not an independently checked status from every native stage. This limitation is unchanged.

**4. Manifest completeness, order, ids, own paths and costs.**

**Measured:** JSON has no duplicate keys, sole top key `units`, 16 entries, each exactly `{id, outputs, cost_s}`. All ids unique and match amended regex. Manifest order equals all 16 rows of `R/results/frodock_setup.csv:2–17`, anchors job order and logged prediction start order: eight sorted systems, holo then apo. One unit is one prepared input record, not one candidate pose or MPI rank.

Each entry lists exactly its own 50 files `results/frodock/<system_id>/<kind>_decoys/model_1.pdb` through `model_50.pdb`, in rank order, relative to out/. Actual full decoy tree contains exactly those 800 files. All path components valid, no `.`/`..`, duplicate/shared paths, combined summaries, CSVs, logs, archive or manifest. Output sets disjoint. `units_complete_and_ordered=yes`, `outputs_own_files_only=yes`.

Question's original wording asks ids accepted by published option. Native prediction flags do not implement this restriction, and no claim made that `ID:kind` is native `--ids` token. Current amended SCHEMAS line 56 instead requires ids identifying units **to run_units.sh**, permits original prepared-record restriction, and therefore accepts these wrapper keys. U139 maps each key to original separate native fields; raw records passed to published program retain those fields exactly. Wrapper acceptance checked for all 16 keys. Old native-id condition cannot override explicit amendment.

Every cost finite positive and exactly equals its own `R/anchors_details.json` `docking_wall_s`, independently reconstructed from logged start/copy timestamps using same epoch-float subtraction as original parser (`run_anchors.sh:109–116,128–134`). Total **4536.183000564575 s**. Definition `R/anchors_details.json:6` ends at “Copying the results”, before copy completes; excludes later repair/scoring and wrapper overhead. These are actual recorded own-job seconds, not total future invocation estimates. `costs_match_records=yes`.

Table indices zero-based. Manifest id/cost lines refer to harness3 `units.json`; details cost line to `R/anchors_details.json`; start/copy lines to `R/run_command/run_command.log`.

| Index | Unit | CSV line | Manifest id/cost lines | Details cost line | cost_s | Log start/copy lines |
| ---: | --- | ---: | --- | ---: | ---: | --- |
| 0 | `1a19__A1_P11540--1a19__B1_P11540:holo` | 2 | 4/57 | 42 | 42.38700008392334 | 7/700 |
| 1 | `1a19__A1_P11540--1a19__B1_P11540:apo` | 3 | 60/113 | 68 | 40.5 | 701/1437 |
| 2 | `1aua__A1_P24280--1aua__A2_P24280:holo` | 4 | 116/169 | 94 | 198.0659999847412 | 1438/2131 |
| 3 | `1aua__A1_P24280--1aua__A2_P24280:apo` | 5 | 172/225 | 120 | 207.37600016593933 | 2132/2825 |
| 4 | `1ax2__A1_P16404--1ax2__A2_P16404:holo` | 6 | 228/281 | 146 | 150.6159999370575 | 2826/3519 |
| 5 | `1ax2__A1_P16404--1ax2__A2_P16404:apo` | 7 | 284/337 | 172 | 235.1909999847412 | 3520/4213 |
| 6 | `1dtd__A1_P48052--1dtd__B1_P81511:holo` | 8 | 340/393 | 198 | 77.67400002479553 | 4214/4891 |
| 7 | `1dtd__A1_P48052--1dtd__B1_P81511:apo` | 9 | 396/449 | 224 | 156.01600003242493 | 4892/5569 |
| 8 | `1dv1__A1_P24182--1dv1__B1_P24182:holo` | 10 | 452/505 | 250 | 559.922000169754 | 5570/6263 |
| 9 | `1dv1__A1_P24182--1dv1__B1_P24182:apo` | 11 | 508/561 | 276 | 241.19400000572205 | 6264/6941 |
| 10 | `1glj__A1_P0A6F3--1glj__B1_P0A6F3:holo` | 12 | 564/617 | 302 | 442.63899993896484 | 6942/7635 |
| 11 | `1glj__A1_P0A6F3--1glj__B1_P0A6F3:apo` | 13 | 620/673 | 328 | 401.63499999046326 | 7636/8329 |
| 12 | `1ht8__A1_P05979--1ht8__B1_P05979:holo` | 14 | 676/729 | 354 | 549.3090000152588 | 8330/9023 |
| 13 | `1ht8__A1_P05979--1ht8__B1_P05979:apo` | 15 | 732/785 | 380 | 582.4049999713898 | 9024/9726 |
| 14 | `1nr5__A1_P07547--1nr5__A2_P07547:holo` | 16 | 788/841 | 406 | 326.07100009918213 | 9727/10420 |
| 15 | `1nr5__A1_P07547--1nr5__A2_P07547:apo` | 17 | 844/897 | 432 | 325.1820001602173 | 10421/11114 |

Actual saved log evidence:

```text
R/run_command/run_command.log:4 CONFIG method=frodock subset=pinder-s pairs=holo,apo n_jobs=16 n_solutions=50 mpi_np=8 force=False CUDA_VISIBLE_DEVICES='' host_nproc=26 PINDER_BASE_DIR=data
:7 2026-11-01 07:13:52,222 | pinder.methods.run.frodock.predict:50 | INFO : Running FroDock (50 solutions) on complex 1a19__A1_P11540--1a19__B1_P11540 holo data/frodock/1a19__A1_P11540--1a19__B1_P11540/inputs/holo/1a19_holo_R.pdb data/frodock/1a19__A1_P11540--1a19__B1_P11540/inputs/holo/1a19_holo_L.pdb
:700 2026-11-01 07:14:34,609 | pinder.methods.run.frodock.predict:173 | INFO : Copying the results to out/results/frodock/1a19__A1_P11540--1a19__B1_P11540/holo_decoys
:11115 2026-11-01 08:29:28,603 | pinder.methods.main:137 | INFO : Success! Finished docking 16 systems
:11116 PREDICT_EXIT=0
:11117 CHAIN_LABELS_RESTORED models=100 atoms=2700
:16201 EVAL_EXIT=0
```

**5. Faithful restricted list and accepted input — measured/read.**

Baseline O82 copies original prepared CSV into results. Candidate retains that exact copy at U84, retains full original validator at U87–117, then selects at U121–147. Actual retained CSV is UTF-8, header `id,kind,receptor,ligand`, 16 newline-terminated one-line records. Selector parses only to find indices; U145 emits original raw header plus selected raw records. No pandas/CSV serialization, field change, preprocessing, structural-input generation, code patch, seed change or extra model entry.

Existing measured `--results_dir out/results` already supplies input path: recorded patch `:13–20` reads `pd.read_csv(Path(results_dir) / f"{method}_setup.csv")`. Therefore same command receives restricted list through accepted argument; no newly invented input interface. Main's declared ids/subset/pairs parameters (`evidence/main.py.txt:80–98`) are unused by complete prediction body (`:102–140`), so effective native selection unavailable. Amended fallback applies directly. `restricted_list_faithful=yes`.

Detached exact selector passed 19 independent fixture checks: all 16 singletons, full order, U51 sample, reversed sample. Every emitted byte equals original header plus requested original byte lines; no extra row. Empty/duplicate/unknown requests each rejected without modifying fixture. Original retained CSV SHA-256 `9e29837be20fb33f8cd891dea4ee36cf3bbaa62c3d9339cab6beb7d7b4fd6f56`.

Sample rule (`SCHEMAS:114`) independently gives indices **3,5,9,15**, in that order: apo units for 1aua, 1ax2, 1dv1, 1nr5. Cost sum **1008.9430003166199 s**, 200 owned files. Saved sample CSV is 644 bytes, SHA-256 `f34c87e11bc77f02997f41aaae17cf6958ce02976b9621886d96c03029b27af0`. Fixture byte success establishes list construction only, not subset docking success.

**7. Amended contract, U51 and disposition.**

No additional demonstrated authoring defect found. Static requirements for shape, at least four units, identifiers, record selection/order/bytes, per-unit code/parameters/inputs, paths, MPS and published-entry exit propagation pass. No runtime outcome fabricated. Unknown whole-program write confinement and future per-unit bytes prevent unqualified overall certification; hence overall unknown values rather than previous reviews' `no/needs_fix`.

U51 is pipeline-owned validation, not another file author must add to harness. Current files are compatible with specified fresh sibling work tree and `bash harness/run_units.sh <four sample ids>`. Baseline source/data/harness symlinks remain readable, private out/ holds restricted CSV and outputs, and no fixed previous run root introduced. U51 compares all 200 sample output bytes against previous recorded reference. If subset exits 0 but mismatches, it runs usual anchors/full-run variability control; `full_match` and `subset_vs_full_match` then distinguish comparisons. No control is run when subset exits nonzero or already matches (`SCHEMAS:75–79`). Both full and subset can vary; do not infer a cause solely from mismatch or change criterion after observation.

Exact next validation specified by contract: pipeline U51 using reference directory `run9/agent/results/reproduce/out/` resolved from correct pipeline cwd; retain authored harness bytes and sample rule. Record actual subset status/matches and conditional full control. This review ran none and supplies no result. U51 covers sampled units, not a proof for every unsampled future invocation. Later unit-mode concurrency adds its own separate/serial/concurrent comparisons. No new seed, numerical repair, selector-source patch, altered criterion or preprocessing should be introduced merely to force a match.

No change to `run_units.sh` or `units.json` presently justified by demonstrated defect. Do not remove them solely for superseded native-selector or inherited-path objections. Exhaustive confinement would require additional evidence about inherited runtime/dependency writes in prepared work trees; no unsupported claim of safety or violation made. User's workload prohibition remains observed.

**Writer/earlier-report assertions checked.** Harness3 copy hashes/modes/mtimes, unchanged ranges, fallback route, raw-record construction, manifest reuse/order/ownership/costs, sample indices/bytes/hash, syntax and stated runtime limits independently confirmed. Its statement of no new code change correctly refers to measured program/per-unit code; wrapper selection helper is new and authorized. Author's historical actions and claimed lack of past network/workloads cannot be independently proven from file content; this review certifies only its own conduct and observable artifacts. Minor citation imprecision: writer line 24 describes configuration validation “through O115/U117”; those endpoints include version diagnostic, while actual validator ends at O113/U115. No behavioral defect.

`run10_diff` correctly distinguishes measured baseline from pristine upstream, ineffective CLI selector from accepted CSV input, definite absolute-path spelling conflict from unknown forbidden dependency writes, and observed full/full equality from unknown subset equality. Independently verified primary-source hashes, recorded patch application, prepared input route, native wall-clock code and 800/800 saved-file comparison support those relevant claims. Earlier review2's `inherited_path_conflict` terminology lacked current dedicated key; present **yes** records definite absolute exports, not an observed outside write.

First review's extra preprocessing/output trees and signal-code conversion concern first candidate, absent here. Second review's CSV-only rejection and native compound-id objection used older contract; amended line 56 now explicitly allows this route and wrapper ids. Both reviews' warnings against extrapolating full-run byte equality to isolation and against asserting complete dependency confinement remain valid evidence limits. Unit/output readers' relevant unit definition, 16-job order, 50-file ownership, narrower timing interval and saved full-run equality independently confirmed. Their older “published_option” label describes setup preprocessing, not current predictor's ineffective CLI filter. Profiling/headroom and broader scientific-expansion claims lie outside this harness review and were not used for its verdict.

Complete independently generated diff follows.

```diff
--- run9/agent/harness/run_command.sh
+++ run10_harness3/run_units.sh
@@ -1,15 +1,16 @@
 #!/usr/bin/env bash
-# run_command.sh - the exact measured baseline command and its complete environment.
+# run_units.sh - the measured baseline restricted to original prepared input records.
 #
-# Invoked as:  bash harness/run_command.sh   (working directory = the shared run directory, or a sibling
-# work directory that links baseline-published/, data/ and harness/). All paths are relative to that
-# working directory. PATH entries are resolved from this working directory because the published
+# Invoked as:  bash harness/run_units.sh <system_id:kind>...   (working directory = the shared run directory, or a sibling
+# work directory that links baseline-published/, data/ and harness/). Command paths are relative;
+# absolute PATH entries and TMPDIR are inherited from run_command.sh (see REPORT.md).
+# PATH entries are resolved from this working directory because the published
 # FroDock adapter changes directory into a temporary stage directory.
 #
 # Representative scale (EXECUTION.json, fixed): the 8 preregistered PINDER-S apo-paired systems in
-# data/selection.json, holo and apo pairings (16 docking jobs), n_solutions=50, mpi_np=8, force=false,
+# data/selection.json; requested holo/apo jobs only, n_solutions=50, mpi_np=8, force=false,
 # docked by the published `pinder_methods predict --method frodock` and scored by the published
-# `pinder_eval` (800 decoys). FroDock is CPU + MPI only: no GPU is used (CUDA_VISIBLE_DEVICES="",
+# `pinder_eval` (50 decoys per selected job). FroDock is CPU + MPI only: no GPU is used (CUDA_VISIBLE_DEVICES="",
 # GPU count 0). CUDA MPS variables are inherited unchanged.
 #
 # Output (stdout+stderr of both published commands): out/run_command/run_command.log
@@ -17,6 +18,7 @@
 #   scores:  out/results/frodock_metrics.csv, out/results/frodock_leaderboard.csv
 # Exit status: nonzero if either published command fails.
 set -Eeuo pipefail
+[ "$#" -gt 0 ] || { echo "ERROR: at least one system_id:kind is required" >&2; exit 2; }
 
 # ------------------------------------------------------------------ complete environment
 export CUDA_VISIBLE_DEVICES=""          # CPU/MPI-only baseline
@@ -113,6 +115,36 @@
 PY
 echo "GPU_COUNT=$BASELINE_GPU_COUNT CUDA_SELECTION=$CUDA_SEL MPIRUN=$(command -v mpirun) FRODOCK_BIN=$(dirname "$(command -v frodock_mpi_gcc)")"
 echo "PINDER_VERSION=$("$VPY" -c 'import importlib.metadata as m;print(m.version("pinder"))')"
+
+# Restrict the validated prepared list; retain its header and original record bytes.
+# The unchanged prediction command reads this path through its existing --results_dir.
+"$VPY" - "$RESULTS/frodock_setup.csv" "$@" <<'PY'
+import csv
+import io
+from pathlib import Path
+import re
+import sys
+
+target = Path(sys.argv[1])
+requested = sys.argv[2:]
+if not requested or len(set(requested)) != len(requested):
+    sys.exit("ERROR: provide one or more distinct system_id:kind keys")
+raw = target.read_bytes().splitlines(keepends=True)
+reader = csv.DictReader(io.StringIO(b"".join(raw).decode("utf-8"), newline=""), strict=True)
+rows = list(reader)
+if reader.fieldnames != ["id", "kind", "receptor", "ligand"] or not rows:
+    sys.exit("ERROR: unexpected prepared manifest schema")
+if len(raw) != len(rows) + 1 or any(not line.endswith(b"\n") for line in raw):
+    sys.exit("ERROR: expected the original newline-terminated one-line-per-record format")
+keys = [row["id"] + ":" + row["kind"] for row in rows]
+if len(set(keys)) != len(keys):
+    sys.exit("ERROR: duplicate prepared unit")
+if any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:+=-]{0,127}", key)
+       or key not in keys for key in requested):
+    sys.exit("ERROR: unknown or invalid requested unit")
+target.write_bytes(raw[0] + b"".join(raw[keys.index(key) + 1] for key in requested))
+print("RESTRICTED_UNITS=" + ",".join(requested))
+PY
 
 # ------------------------------------------------------------------ published docking command
 set +e
```
