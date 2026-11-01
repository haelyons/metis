Independent review, 2026-11-01. Verdict: **needs_fix** under current literal U50 contract. Coverage, order, own-file lists and costs pass. Explicit per-job binary, input mapping, parameters, environment, MPI ranks, scoring workers and working directory match baseline. Candidate now filters prepared CSV rows itself; it does **not** invoke published subset selection. Absolute run-local PATH/TMPDIR entries remain. Subset byte identity and exhaustive write confinement remain **unknown**.

Evidence labels: **Measured** = comparisons, file inventories, syntax parsing or arithmetic over saved records. **Read** = code/document statements. **Inferred** = consequences, never a candidate execution. Paths relative to experiment directory unless absolute. `O` = `run9/agent/harness/run_command.sh`; `U` = `run10_harness2/run_units.sh`; `R` = `run9/agent/results/reproduce/out/`. Line numbers count LF separators; embedded carriage-return progress updates do not add lines.

Review writes confined to `run10_review2/`. No harness/workload execution, network fetch, box contact, git command, credentials, `.keys` or `~/.codex/` reads. `bash -n` parses only; embedded Python parsed with `ast.parse`, never imported or run. Review script uses standard-library file reads/comparisons/arithmetic. Existing launcher artifacts left untouched.

Measured directory sizes before selective reads: run9 6.2 GiB, agent results 6.2 GiB, harness 1.3 MiB, agent workflow 4.3 MiB; reproduce out 2.1 GiB, including results 330 MiB, tmp 1.1 GiB and run_command 669 MiB. Read final listed PDBs for required repeatability check, small configuration/summary/log files and two named source-bearing workflow events. No large profiler database, profiler capture, temporary native intermediates or raw-decoy archive read.

Contract read: `/home/hal/dev/interp/metis-wt/dut/pipeline/m5/SCHEMAS.md:54–57` and `:88–117`. Relevant requirements: exact measured binary/configuration/environment/scale; relative paths and writes under out/temp; unique native selection ids; published program's own subset selection in argument order; original per-unit output paths; unchanged MPS; exit propagation. Unit-mode arms use fresh sibling work directories with shared source/data links (`:91,104–110`), compare first subset with frozen full-run files (`:111`), then compare separate/concurrent arms. Those future comparisons are validation, not results already obtained.

Read owner brief `run9/agent/intake/brief.md:1–63`, intake baseline/configuration, writer `run10_harness2/REPORT.md`, first review `run10_review/REPORT.md`, and unit/output readers. Earlier conclusions treated as claims to verify. Supporting artifacts here: `audit.py`, `audit.json`, `run_units.diff`, `unit_evidence.md`, four decoded saved-source excerpts. Audit records hashes, copy checks, syntax checks and every unit's evidence.

**Measured: unchanged copies and baseline identity.** All six original harness files match candidate copies byte for byte, permission modes and nanosecond mtimes: `setup.sh`, `run_anchors.sh`, `run_command.sh`, `run_evaluation.sh`, `pinder_inputs.tsv`, `pinder_frodock_fixes.patch`. Original command SHA-256 `08d645d90c83ce0548f72e9a0b6a6e2a038bf188f8c6f13eefae1f385f231ae5`. Saved applied patch `R/setup/pinder_frodock_fixes.applied.patch` matches harness patch bytewise. Every hash in writer's copy table agrees with independent audit.

**Read:** `R/setup/setup_record.json:2–16,27–35` records PINDER commit `ebeb28a2f8411363cef722b7d293c978f7442672`, compiled FroDock binaries, SOAP hash, Python/package versions and Open MPI 4.1.2. Candidate retains same binary paths; installed executable bytes/source trees are not present for a fresh binary hash audit. FroDock original-study material identity remains conditional on owner-approved unverified mirror (`baseline.json:68`, brief `:34–40`); this does not imply a difference between candidate and saved measured baseline.

**Every changed line and classification.** Complete mechanically generated diff appears at end. Unchanged lines shift positions only.

| O lines | U lines | Difference | Classification |
| --- | --- | --- | --- |
| 2 | 2 | Description changes from exact full command to restricted prepared rows. | Message/comment text; subset description |
| 4–6 | 4–7 | Invocation adds positional `system_id:kind`; comments disclose absolute PATH/TMPDIR, retain same sibling-working-directory description. | Argument handling; message/comment text; no cwd change |
| 10 | 11 | All 16 jobs described as requested jobs. | Subset description; no per-job scale change |
| 12 | 13 | 800 decoys described as 50 per selected job. | Subset description; no per-job scale change |
| after 19 | 21 | Missing arguments print error to stderr, exit 2 before environment/output setup. | Argument handling; message text |
| 82 | 84–85 | Removes full-CSV `cp`; comments describe selection in validator. Same output CSV written later at U122. | Subset implementation; comment text; no output-location change |
| 86 | 89 | Appends quoted `"$@"` to existing validator's arguments. | Argument handling |
| 87 | 90 | Adds standard-library `re` import. | Argument validation |
| 90 | 93 | Reads full prepared CSV directly from `data/frodock/frodock_setup.csv`, instead of its full copy at results path. | Subset implementation; no new input tree |
| 99 | 102 | Compares `[4:10]`, retaining same six fixed parameters, excluding appended ids. | Argument handling; no parameter change |
| after 107 | 111–112 | Comments explain complete-row selection and recorded predictor loop. | Message/comment text; subset description |
| after 107 | 113 | Reads requested ids from `sys.argv[10:]`. | Argument handling |
| after 107 | 114 | Builds wrapper keys `pid + ':' + kind` from full manifest. | Subset implementation; argument handling |
| after 107 | 115 | Rejects duplicate prepared keys. | Subset validation; message text |
| after 107 | 116 | Rejects duplicate requested ids. | Argument handling; message text |
| after 107 | 117–118 | Rejects invalid-regex or unknown keys. | Argument handling; subset validation; message text |
| after 107 | 119–120 | Exits on accumulated full-configuration/selection errors before CSV write and CONFIG print. Original final error check remains at U126–127. | Argument/subset validation; failure-message ordering |
| after 107 | 121 | Selects rows through `jobs.iloc[[keys.index(key) for key in requested]]`. | Wrapper-side subset selection, preserving requested order |
| after 107 | 122 | Serializes selected rows to same `out/results/frodock_setup.csv`. | Subset implementation; no output-location change |

**Measured:** complete environment `O:21–48` equals `U:23–50`; output setup `O:50–81` equals `U:52–83`; entire docking/repair/scoring suffix `O:117–185` equals `U:132–200`. Both embedded Python blocks parse; all five shell scripts pass `bash -n`. Syntax does not establish runtime success.

Status classification: argument handling **yes**, subset selection **yes**, messages/log paths **yes**. Last flag reflects changed comments and added errors; existing log path remains `out/run_command/run_command.log` (`O64/U66`). Subset flag records actual CSV filtering, **not** compliance with published-option requirement. Output locations, environment, thread setting, configuration/scale, binary/entry, cwd and other differences all **no**. Selected job count is intentional subset dimension, not per-job scale change. CSV serialization/validation belongs to subset implementation; no additional uncategorized numerical change. No added published preprocess entry/action or new preprocess output tree survives from first attempt.

**Per-unit computation: explicit call parity established; byte identity unknown.**

**Read:** both scripts use `baseline-published/venv/bin/python`, same `pinder_methods predict` entry/action, `--method frodock --data_dir data/frodock --results_dir out/results --subset pinder-s --pairs all`, same YAML path (`O:119–120/U:134–135`). Both run same `pinder_eval` entry with eight workers (`O180/U195`) and same chain restoration/archive/validation (`O:132–174/U:147–189`). Neither wrapper changes cwd.

**Read:** complete explicit environment remains CPU-only `CUDA_VISIBLE_DEVICES=''`, GPU count 0, `N_SOLUTIONS=50`, `MPI_NP=8`, `FORCE=false`, `EVAL_MAX_WORKERS=8`, method frodock, `PINDER_BASE_DIR=data`, release `2024-02`, INFO logging, unbuffered Python, unset `PINDER_DATA_DIR`, identical CUDA-layout/PATH discovery, disabled Python bytecode and same TMPDIR construction. YAML matches saved `R/run_command/frodock_config.yaml:1–3`. MPI ranks fixed at eight; evaluation workers fixed at eight. Total native/helper/library thread population and inherited thread environment are not established, but no explicit thread-setting difference exists. Native `--th 10` is retained docking parameter, not evidence of ten threads.

**Measured/read:** each saved prepared row has exactly four nonempty string fields `id,kind,receptor,ligand` (`R/results/frodock_setup.csv:1–17`). U93 reads original table; U108–110 validates full eight-system/two-kind universe before selection; U121 selects complete records without changing field values, U122 writes at predictor's existing CSV path. Pandas can change CSV formatting; program consumes parsed records. Data directory remains `data/frodock`; input structures are not regenerated. Original source data tree is not retained locally, so original-input byte hashes cannot be independently recomputed here.

**Read from saved published source:** first review's source-availability statement was too broad. Full FroDock Python adapter survives inside `run9/agent/wf/agents/0006-anchors-repair/codex-1.jsonl:103`, completed event `exec-188fbfc5-f134-441e-ad67-2c7cf9c1c1a3`. Recorded command names pinned source commit above; event exit is 0. JSON `aggregatedOutput` decoded as actual newlines, with no literal backslash replacement. It contains upstream `predict.py:1–233`, eval `dockq/method.py:81–260`, eval `run.py:1–104`. Saved source is copied here for review, never fetched or executed. Record line129 supplies core index utility excerpt. Excerpts are recorded source observations, not fresh verification of upstream or complete installed/native/dependency audit.

For **every** listed unit, same computation follows at call level:

1. Harness patch `:13–20` sets same `data_dir/results_dir`, reads results setup CSV and iterates `to_dict('records')` in row order, calling same `predict_method(complex_config, config_dict)`.
2. Saved adapter `predict.py:209–216` extracts id, kind, receptor, ligand, results, solution count, MPI count and force; applied patch `:53–64` resolves relative inputs against same `data_dir`. `:218–233` performs same skip check/call. Both wrappers move prior results aside and create fresh results (`O:59–82/U:61–85`), avoiding force=false reuse.
3. Adapter `:54–57` creates fresh temporary job directory. Patch `:24–30` copies current original receptor/ligand there before changing cwd. Adapter `:59–89` resolves same native executables and sets same `OMPI_ALLOW_RUN_AS_ROOT=1` and `OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1` on every job. No new wrapper environment change.
4. Adapter `:91–137` runs same eight native stages: four grids, docking, clustering, viewing and coordinate generation; same MPI ranks, SOAP input, `--th 10` and 50-solution settings. `:139–166` generates ranked models and restores cwd. Patch `:43–48` copies models to same `results/frodock/<id>/<kind>_decoys/`.
5. Unchanged wrapper repair processes each selected job's own PDB bytes and restores same chain labels. Unchanged scorer evaluates selected output tree. Combined score/leaderboard CSVs depend on selected cases/missing penalties; they cannot match full-run shared CSVs and are correctly excluded from manifest.

**Measured:** all **800/800** listed saved reproduce PDBs match corresponding profile PDBs byte for byte, **342,779,850 bytes per run**. Both actual final trees contain exactly those 800 files; setup CSVs also match bytes. Independently verifies relevant repeated-full-run claim from `run9_units/REPORT.md:62–68` and `run9_outputs/REPORT.md:25–35`. It does not test changed unit invocation.

**Inferred/unknown:** identical explicit per-row calls support intended per-unit parity. Complete native numerical source, dependency/cache state, random initialization and sequence dependence remain unaudited. Both observed full runs preserve same order. No isolated, reordered or concurrent candidate run authorized/performed. Therefore `same_computation_per_unit=unknown` for requested stronger conclusion that listed files **would** be byte-identical. No evidence demonstrates a changed numerical result either. U50 frozen-baseline and later-arm comparisons remain necessary (`SCHEMAS:111`); absence of those results is not itself a claim that comparison failed.

**Writes, absolute paths, MPS and exits.**

**Read:** all explicit wrapper writes target out/: logs/history/moves `U:53–66`; tmp `67–68`; YAML `79–83`; selected setup CSV `122`; prediction/repair/archive/manifest/scoring `134–195`. No new output location or explicit shared-data/source write added. Adapter uses fresh `tempfile.mkdtemp()`; inherited TMPDIR directs normal temporary stage files to invocation's `out/tmp/`. `PYTHONDONTWRITEBYTECODE=1` prevents normal Python bytecode writes.

**Unknown:** exhaustive dependency writes. Core source excerpt from workflow line129, copied here as `saved_core_utils_excerpt.py.txt:24–26`, conditionally creates data release directory outside out/temp; `:63–65` documents index load/download. Eval source upstream `method.py:231–235,243–251` (local excerpt `:151–155,163–171`) invokes `PinderSystem` and creates/downloads missing native data. Setup populated inputs and saved reproduction succeeded, but no complete retained dependency source or filesystem-write trace establishes all read/cache paths for future sibling invocations. Conditional write code is not proof that condition occurs with prepared run9 state. Thus `writes_only_out_or_temp=unknown`, not unconditional yes or observed outside-write no.

**Read: literal absolute-path mismatch**, inherited unchanged:

```sh
# U49, O47
export PATH="$PWD/baseline-published/frodock/bin:$PWD/$VENV/bin:$PATH"
# U68, O66
export TMPDIR="$PWD/out/tmp"
```

These become absolute paths into each invocation's run/work directory. They derive from current cwd, not a fixed prior `/tmp/m5-...` root, and TMPDIR still targets allowed out/. Nevertheless literal `SCHEMAS:55–56` says never absolute paths into run directory. This is definite contract mismatch. No dedicated status key exists, so it affects `contract_met`, not `writes_only_out_or_temp`. Dynamic construction alone is not a demonstrated portability bug. Relative PATH replacements can fail after adapter's temp-directory `chdir` (`predict.py:57`); do not prescribe blind substitution. Environment parity makes this inherited discrepancy relevant even though `diff_environment=no`.

**Read:** U contains no `CUDA_MPS_*` assignment, unset or override and no daemon control. Only comment states inheritance; unchanged full adapter source adds no MPS operation. `mps_untouched=yes`. CUDA visibility setting is separate and unchanged.

**Read:** missing ids exits 2 (`U21`); invalid/duplicate/unknown ids abort before prediction (`115–120`). Prediction exit captured and returned (`133–139`); scorer exit uses `${PIPESTATUS[1]}` and returned (`194–199`), same as original. Other helper failures subject to errexit/pipefail. Adapter's pre-existing native stage `subprocess.run(cmd, shell=True)` lacks `check=True` (`predict.py:127–137`), so wrapper propagates published entry status rather than proving each native stage's success. No new status conversion remains from old preprocessing. No runtime or signal failure tests performed.

**Manifest, native selection and every cost.**

**Measured:** JSON has exactly one top-level `units` key, 16 entries, each exactly `id,outputs,cost_s`; duplicate JSON keys rejected by audit. All ids unique and match required regex. All outputs nonempty, unique, safe relative components, no `.` or `..`; all unit output sets disjoint. Each unit lists exactly its own ranks 1–50 and actual directory file set. No shared setup CSV, summary, log, config, archive, metrics or leaderboard listed. Paths are relative to out/, e.g. `units.json:6` names `results/frodock/1a19__A1_P11540--1a19__B1_P11540/holo_decoys/model_1.pdb`, consistent with patch `:43–48`. Hence `outputs_own_files_only=yes`.

**Measured:** manifest order equals original 16 prepared rows (`R/results/frodock_setup.csv:2–17`), anchors job order, and actual logged prediction start order. Eight ascending native system ids, holo then apo. `units_complete_and_ordered=yes` covers full measured-run universe/order. Identifier qualification remains separate unresolved part of contract.

**Read: published-option requirement unmet.** U134–135 is byte-identical original prediction command and contains no requested-id option. Fixed `--subset pinder-s --pairs all` selects no requested `id:kind` list. Actual restriction happens in wrapper's `jobs.iloc[...]`/`to_csv` at U121–122. Published program consumes that prepared CSV; this is wrapper-side manifest editing, not its own subset-selection option. Calling existing CSV format a published input mechanism does not satisfy requested option requirement.

First manifest id is `1a19__A1_P11540--1a19__B1_P11540:holo` (`units.json:4`). U114 invents compound key from separate native fields; published predictor receives separate original `id/kind` fields, never that key as native selector. Native option acceptance of compound keys is **unknown**. Saved setup genuinely invokes published `preprocess --ids <system-id list> --pairs <kind>` (`setup.sh:3973–3984`, saved preprocess logs); subsequent assembly sorts original rows (`:3987–4004`). Earlier unit/output readers establish that two-option preprocessing route, not compound-id acceptance or effective direct prediction filtering. Intake describes predict `--ids` (`baseline.json:22,25`), but preserved patched loop `patch:13–20` does not establish such filtering. No direct native selector was fabricated or run. Stronger native-id condition cannot be certified; known wrapper-selection mismatch already makes overall contract **no**.

**Measured/read:** all costs finite positive, equal corresponding `R/anchors_details.json` job `docking_wall_s` exactly, and independently equal epoch-timestamp subtraction from corresponding start/copy markers, preserving parser's float rounding. Sum **4536.183000564575 s**. Definition `anchors_details.json:6` and parser `run_anchors.sh:109–116,128–134`: Running FroDock timestamp to Copying the results timestamp, before copy completion, later repair/scoring and wrapper overhead. Contract asks recorded own seconds; narrower interval satisfies that metadata requirement. Costs do not estimate complete U50 invocation runtime. `costs_match_records=yes`.

Example actual log lines:

```text
R/run_command/run_command.log:4 CONFIG method=frodock subset=pinder-s pairs=holo,apo n_jobs=16 n_solutions=50 mpi_np=8 force=False CUDA_VISIBLE_DEVICES='' host_nproc=26 PINDER_BASE_DIR=data
:7 2026-11-01 07:13:52,222 | pinder.methods.run.frodock.predict:50 | INFO : Running FroDock (50 solutions) on complex 1a19__A1_P11540--1a19__B1_P11540 holo data/frodock/1a19__A1_P11540--1a19__B1_P11540/inputs/holo/1a19_holo_R.pdb data/frodock/1a19__A1_P11540--1a19__B1_P11540/inputs/holo/1a19_holo_L.pdb
:700 2026-11-01 07:14:34,609 | pinder.methods.run.frodock.predict:173 | INFO : Copying the results to out/results/frodock/1a19__A1_P11540--1a19__B1_P11540/holo_decoys
:11116 PREDICT_EXIT=0
:11117 CHAIN_LABELS_RESTORED models=100 atoms=2700
:16201 EVAL_EXIT=0
```

Per-unit table follows. CSV = `R/results/frodock_setup.csv`; manifest = `run10_harness2/units.json`; details = `R/anchors_details.json`; log = `R/run_command/run_command.log`. Each row owns exactly `results/frodock/<system-id>/<kind>_decoys/model_1.pdb` through `model_50.pdb`.

| # | Unit | CSV line | Manifest id/cost lines | Details cost line | cost_s | Log start/copy lines |
| ---: | --- | ---: | --- | ---: | ---: | --- |
| 1 | `1a19__A1_P11540--1a19__B1_P11540:holo` | 2 | 4/57 | 42 | 42.38700008392334 | 7/700 |
| 2 | `1a19__A1_P11540--1a19__B1_P11540:apo` | 3 | 60/113 | 68 | 40.5 | 701/1437 |
| 3 | `1aua__A1_P24280--1aua__A2_P24280:holo` | 4 | 116/169 | 94 | 198.0659999847412 | 1438/2131 |
| 4 | `1aua__A1_P24280--1aua__A2_P24280:apo` | 5 | 172/225 | 120 | 207.37600016593933 | 2132/2825 |
| 5 | `1ax2__A1_P16404--1ax2__A2_P16404:holo` | 6 | 228/281 | 146 | 150.6159999370575 | 2826/3519 |
| 6 | `1ax2__A1_P16404--1ax2__A2_P16404:apo` | 7 | 284/337 | 172 | 235.1909999847412 | 3520/4213 |
| 7 | `1dtd__A1_P48052--1dtd__B1_P81511:holo` | 8 | 340/393 | 198 | 77.67400002479553 | 4214/4891 |
| 8 | `1dtd__A1_P48052--1dtd__B1_P81511:apo` | 9 | 396/449 | 224 | 156.01600003242493 | 4892/5569 |
| 9 | `1dv1__A1_P24182--1dv1__B1_P24182:holo` | 10 | 452/505 | 250 | 559.922000169754 | 5570/6263 |
| 10 | `1dv1__A1_P24182--1dv1__B1_P24182:apo` | 11 | 508/561 | 276 | 241.19400000572205 | 6264/6941 |
| 11 | `1glj__A1_P0A6F3--1glj__B1_P0A6F3:holo` | 12 | 564/617 | 302 | 442.63899993896484 | 6942/7635 |
| 12 | `1glj__A1_P0A6F3--1glj__B1_P0A6F3:apo` | 13 | 620/673 | 328 | 401.63499999046326 | 7636/8329 |
| 13 | `1ht8__A1_P05979--1ht8__B1_P05979:holo` | 14 | 676/729 | 354 | 549.3090000152588 | 8330/9023 |
| 14 | `1ht8__A1_P05979--1ht8__B1_P05979:apo` | 15 | 732/785 | 380 | 582.4049999713898 | 9024/9726 |
| 15 | `1nr5__A1_P07547--1nr5__A2_P07547:holo` | 16 | 788/841 | 406 | 326.07100009918213 | 9727/10420 |
| 16 | `1nr5__A1_P07547--1nr5__A2_P07547:apo` | 17 | 844/897 | 432 | 325.1820001602173 | 10421/11114 |

**Writer and earlier-review claims checked.**

- Writer `REPORT.md:23–34,118–137`: copies, hashes, syntax and complete diff agree with independent checks.
- Writer `:38–49,53–77`: removal of preprocessing/new output trees and unchanged call-level parity verified; native-option compliance and runtime equality correctly remain uncertified. Its `:57` describes authorization for alternative mechanism in its earlier task; that does not amend current requested SCHEMAS contract.
- Writer `:81–104`: coverage, paths, values and cost sum correct. Log start/copy line table `:87–102` is wrong under LF line numbering except first start. It counts carriage-return progress updates: first copy claimed 823, actual 700; final claimed start/copy 13129/13947, actual 10421/11114. Use table here. Writer's exit citations `:104` are correct. Costs unaffected.
- Writer `:106`: independently repeated saved full-run comparison; 800 matches and byte count correct. No extrapolation to subset/reordering.
- Writer `:108–116`: explicit out/temp writes, shared-data conditional-write uncertainty, absolute paths and unresolved compound native ids confirmed from files/source.
- First review correctly identified extra preprocessing, extra outputs and signal-conversion issue in earlier candidate. Those are absent here. Its inherited path/native-id/runtime limits remain relevant. Its claim that retained source consists only of patch excerpts was incomplete: full Python FroDock adapter and eval excerpts survive in recorded workflow event. Full native source/dependency audit still unavailable.
- Earlier unit/output readers' relevant scale, paths, ownership, order, timing and full-run repeatability claims independently confirmed. Their profiling-resource analysis is outside this review's contract questions and was not rerun. Their `published_option` classification concerns preprocessing route and does not certify present CSV-only implementation.

**Exact disposition and changes needed.**

Do not certify current optional files as usable under literal contract. Concrete safe launch disposition: **omit both `run_units.sh` and `units.json` from harness selected for launch** until requirements are reconciled. Both optional files absent selects existing command-mode behavior (`SCHEMAS:102`). This withdraws uncertified unit mode; it does not fix original command's inherited path discrepancy. Review changed neither candidate nor earlier harnesses.

To retain current sixteen units, two exact contract decisions are necessary before an evidence-backed implementation can be certified:

1. Either replace U111–122 with an effective **documented native** selector that accepts each listed unique job id and preserves argument order, with same prepared inputs/command, or explicitly change `SCHEMAS:56` to allow wrapper ids `system_id:kind` mapped to original `(id,kind)` records and ordered restriction of existing prepared results CSV. No such native selector accepting compound keys is established by retained evidence. Simply adding `--ids` or stripping pairing suffixes is not a valid fix: effect on loaded CSV is unproven; suffix removal creates duplicates and merges distinct jobs. Reintroducing timed preprocessing repeats prior extra-action/input-regeneration defect. Current CSV implementation would fit the explicit revised mechanism, but does not fit current rule.
2. Either revise `SCHEMAS:55–56` to permit absolute PATH/TMPDIR entries derived exclusively from current invocation cwd, while continuing to prohibit fixed paths into another run/work directory, or redesign **both** baseline and unit launch/adapter path handling with evidence that it preserves binary lookup after temporary `chdir`. Editing only U49/U68 changes environment relative to immutable original. No two-file-only environment-identical code change can remove inherited absolute construction. No schema/baseline change authorized or performed here.

Further certification requires establishing dependency write confinement for prepared sibling trees and pipeline frozen-baseline/subsequent-arm byte comparisons. Preserve unknowns until evidence exists. Current lack of those comparisons is expected before probe, not invented mismatch. Correct writer's table to LF line numbers above. No changes needed to current 16-unit coverage/order, 800 owned output paths or recorded cost values. Report does not request workload execution during this review.

Complete independent diff:

```diff
--- run9/agent/harness/run_command.sh
+++ run10_harness2/run_units.sh
@@ -1,15 +1,16 @@
 #!/usr/bin/env bash
-# run_command.sh - the exact measured baseline command and its complete environment.
+# run_units.sh - the measured baseline restricted to original prepared manifest rows.
 #
-# Invoked as:  bash harness/run_command.sh   (working directory = the shared run directory, or a sibling
-# work directory that links baseline-published/, data/ and harness/). All paths are relative to that
-# working directory. PATH entries are resolved from this working directory because the published
+# Invoked as:  bash harness/run_units.sh <system_id:kind>...   (working directory = the shared run directory, or a sibling
+# work directory that links baseline-published/, data/ and harness/). Command paths are relative.
+# Runtime absolute PATH entries and TMPDIR are inherited from run_command.sh; see REPORT.md.
+# PATH entries are resolved from this working directory because the published
 # FroDock adapter changes directory into a temporary stage directory.
 #
 # Representative scale (EXECUTION.json, fixed): the 8 preregistered PINDER-S apo-paired systems in
-# data/selection.json, holo and apo pairings (16 docking jobs), n_solutions=50, mpi_np=8, force=false,
+# data/selection.json, requested holo/apo jobs only, n_solutions=50, mpi_np=8, force=false,
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
@@ -79,15 +81,16 @@
 mpi_np: $MPI_NP
 force: $FORCE
 EOF
-cp data/frodock/frodock_setup.csv "$RESULTS/frodock_setup.csv"   # predict reads <results_dir>/frodock_setup.csv
+# The published predict loop reads this CSV directly; select original rows below.
+# No preprocessing, regenerated inputs, extra prediction entry point, or output tree.
 
 # ------------------------------------------------------------------ printed configuration (validated)
 "$VPY" - "$RUN_DIR/frodock_config.yaml" "$RESULTS/frodock_setup.csv" data/selection.json \
-    "$METHOD" "$N_SOLUTIONS" "$MPI_NP" "$FORCE" "$EVAL_MAX_WORKERS" "$BASELINE_GPU_COUNT" <<'PY'
-import json, os, sys, yaml
+    "$METHOD" "$N_SOLUTIONS" "$MPI_NP" "$FORCE" "$EVAL_MAX_WORKERS" "$BASELINE_GPU_COUNT" "$@" <<'PY'
+import json, os, re, sys, yaml
 import pandas as pd
 from pinder.core import get_index
-cfg = yaml.safe_load(open(sys.argv[1])); jobs = pd.read_csv(sys.argv[2]); sel = json.load(open(sys.argv[3]))
+cfg = yaml.safe_load(open(sys.argv[1])); jobs = pd.read_csv("data/frodock/frodock_setup.csv"); sel = json.load(open(sys.argv[3]))
 idx = get_index()
 s = idx[idx["pinder_s"].astype(bool)]
 apo = s[s["apo_R"].astype(bool) & s["apo_L"].astype(bool)]
@@ -96,7 +99,7 @@
 print(f"PINDER_S_APO_PAIRED_COUNT={apo['id'].nunique()}")
 print("SELECTED_IDS=" + json.dumps(ids))
 errs = []
-if sys.argv[4:] != ["frodock", "50", "8", "false", "8", "0"]: errs.append("actual command parameters differ from fixed configuration")
+if sys.argv[4:10] != ["frodock", "50", "8", "false", "8", "0"]: errs.append("actual command parameters differ from fixed configuration")
 if os.environ.get("CUDA_VISIBLE_DEVICES") != "": errs.append("CPU baseline must expose zero GPUs")
 if os.environ.get("PINDER_BASE_DIR") != "data" or os.environ.get("PINDER_RELEASE") != "2024-02": errs.append("dataset environment differs from fixed configuration")
 if ids != sel["ids"]: errs.append("selection from index differs from data/selection.json")
@@ -105,6 +108,18 @@
 if sorted(set(jobs["id"])) != sorted(ids): errs.append("frodock_setup.csv ids differ from selection")
 if sorted(set(jobs["kind"])) != ["apo", "holo"] or len(jobs) != 2 * len(ids): errs.append("frodock_setup.csv is not holo+apo for every id")
 if set(zip(jobs["id"], jobs["kind"])) != {(pid, kind) for pid in ids for kind in ("holo", "apo")}: errs.append("frodock_setup.csv lacks an expected id/pairing")
+# Select only complete, original records in the requested order. The published
+# entry point consumes this setup CSV (preserved source patch, lines 17-20).
+requested = sys.argv[10:]
+keys = [pid + ":" + kind for pid, kind in zip(jobs["id"], jobs["kind"])]
+if len(set(keys)) != len(keys): errs.append("duplicate prepared unit")
+if len(set(requested)) != len(requested): errs.append("duplicate requested unit")
+if any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:+=-]{0,127}", key) or key not in keys for key in requested):
+    errs.append("unknown or invalid unit id")
+if errs:
+    sys.exit("ERROR: " + "; ".join(errs))
+jobs = jobs.iloc[[keys.index(key) for key in requested]]
+jobs.to_csv(sys.argv[2], index=False)
 print(f"CONFIG method=frodock subset=pinder-s pairs=holo,apo n_jobs={len(jobs)} n_solutions={cfg.get('n_solutions')} "
       f"mpi_np={cfg.get('mpi_np')} force={cfg.get('force')} CUDA_VISIBLE_DEVICES='{os.environ.get('CUDA_VISIBLE_DEVICES')}' "
       f"host_nproc={os.cpu_count()} PINDER_BASE_DIR={os.environ.get('PINDER_BASE_DIR')}")
```

