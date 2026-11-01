# Independent review of run10 unit harness

Verdict: **needs_fix** under literal current contract. Unit coverage, order, output ownership and recorded costs pass. Docking/scoring executable paths, per-job configuration, explicit environment and parallelism settings remain unchanged. Candidate adds preprocessing, input checks and private preprocessing outputs. Subset byte equality and exhaustive write confinement remain **unknown**. Listed compound identifiers have no established native selector. Both scripts also construct absolute run-local paths, contrary to literal relative-path rule.

## Scope and evidence labels

Review date: 2026-11-01. Writes confined to `run10_review/`; existing launcher files left untouched. No workload, harness execution, box contact, network request or git command. No credentials, `.keys` or `~/.codex/` read. `bash -n` only parses shell syntax; embedded Python was compiled, never executed. Review's own Python reads saved records, compares bytes and writes review artifacts.

**Measured** below means file inspection/comparison or arithmetic over saved evidence. **Read** means statements directly supported by code/documents. **Inferred** means consequences, not observed execution of candidate. Paths relative to current directory unless absolute. `O` = `run9/agent/harness/run_command.sh`; `U` = `run10_harness/run_units.sh`. Line numbers count LF separators, including logs with carriage-return progress updates.

Contract read at `/home/hal/dev/interp/metis-wt/dut/pipeline/m5/SCHEMAS.md:47–58`: exact measured command/environment at 54; relative paths and out/temp writes at 55; optional unit shape/native selection/same command/order/exit rules at 56; inherited MPS at 57. Concurrency context at 91, 102–114: separate work directories with shared source/data links, fixed per-unit configuration, frozen-baseline byte comparison, then repeat/separate/concurrent comparisons. Those comparisons are validation requirements, not evidence already obtained for this candidate.

Measured sizes before selective reads: `run9/agent/harness/` 1.3 MiB, `run9/agent/results/` 6.2 GiB, reproduce `out/` 2.1 GiB; reproduce `out/results/` 330 MiB, `out/run_command/` 669 MiB, `out/tmp/` 1.1 GiB. Profile decoy tree measured 329 MiB before reading only its listed PDBs. No raw-decoy archives or profiler databases read. Source-name inventory under `run9/agent/` found no complete `.py`, native source or source archive; available source evidence is preserved patch, setup script and intake descriptions. Dependency behavior cannot be reconstructed exhaustively.

Machine-readable measurements: `run10_review/audit.json`. Exact independently generated diff: `run10_review/run_units.diff`, also reproduced below. Neither artifact executes candidate.

## Copies and original baseline

**Measured:** all six original harness files match run10 copies byte for byte, permission mode and nanosecond mtime. Names: `setup.sh`, `run_anchors.sh`, `run_command.sh`, `run_evaluation.sh`, `pinder_inputs.tsv`, `pinder_frodock_fixes.patch`. Sizes/hashes in `audit.json` independently match writer's table (`run10_harness/REPORT.md:15–24`). Original command SHA-256: `08d645d90c83ce0548f72e9a0b6a6e2a038bf188f8c6f13eefae1f385f231ae5`.

**Read:** saved configuration is eight fixed systems, holo then apo, 50 candidates/job, MPI ranks 8, `force: false` (`run9/agent/intake/EXECUTION.json:3–5,11–19`; reproduce `out/run_command/frodock_config.yaml:1–3`). Setup record pins PINDER commit `ebeb28a2f8411363cef722b7d293c978f7442672`, FroDock archive identity and owner-approved unverified-mirror provenance (`out/setup/setup_record.json:2–16`). Original-source distribution identity remains conditional; candidate introduces no new source download or binary.

**Measured/read:** saved applied patch equals harness patch. Patch `:16–20` loads `results_dir/frodock_setup.csv` using pandas and iterates records in order; `:24–30` stages inputs in fresh temporary working directory; `:35` keeps `mpirun -np {mpi_np} --use-hwthread-cpus`; `:43–48` copies each unit's PDBs to its own system/kind directory; `:53–64` resolves receptor/ligand relative to data directory and takes configured solution/MPI counts. These are excerpts, not complete source audit.

## 1. Every changed line and classification

Complete diff below gives every addition/deletion. Table explains all hunks; unchanged lines only shift position.

| Original lines | Candidate lines | Change | Classification |
| --- | --- | --- | --- |
| 2 | 2 | Script-description comment names restricted preprocessing route. | Message/comment text |
| 4 | 4 | Invocation comment adds compound positional ids. | Argument handling; message/comment text |
| 10 | 10 | Comment replaces all 16 jobs with requested jobs. | Subset selection; message/comment text |
| 12 | 12 | Comment replaces 800 decoys with 50 per selected job. | Subset selection; message/comment text; no per-job scale change |
| after 19 | 20 | Empty argument list prints error to stderr, exits 2 before environment/output setup. | Argument handling; message text |
| 82 | 83–84 | Full-manifest `cp` removed; comments describe native preprocessing and preserved original inputs. | Subset selection |
| 82 | 85–90 | New Python helper receives program/method/output directories and all ids; imports CSV/JSON/regex/subprocess/temp/path helpers. | Argument handling; subset selection |
| 82 | 91–100 | Reads prepared full manifest; maps original rows by `id + ':' + kind`; rejects duplicate prepared keys. | Argument handling; subset selection |
| 82 | 101–105 | Rejects duplicate requested ids; requires safe regex and membership in prepared rows. | Argument handling; message text |
| 82 | 106–114 | Iterates requested order; extracts native system id and kind; creates `out/run_command/unit-preprocess-*`; constructs native `preprocess --ids <JSON [system_id]> --pairs <kind>`. | Subset selection; additional published entry/action; additional output locations |
| 82 | 115–118 | Runs preprocessing; ordinary nonzero subprocess return code exits helper/shell. | Subset selection; failure propagation |
| 82 | 119–129 | Requires exactly selected native row, safe/equal receptor/ligand paths and byte-equal regenerated inputs. | Subset selection validation; message text |
| 82 | 130–134 | Appends original prepared rows, then serializes selected CSV in requested order at same `out/results/frodock_setup.csv` path. | Subset selection; no final result relocation |
| 82 | 135–136 | Prints `REQUESTED_UNITS=<JSON>` and closes helper. | Message text |
| 86 | 140 | Forwards ids to original configuration validator. | Argument handling |
| 99 | 153 | Checks six fixed parameters with `[4:10]`, excluding appended ids. | Argument handling; same six parameter values |
| 105–107 | 159–161 | Replaces full-universe job assertions with exact requested order and membership in unchanged eight-system/two-kind universe. | Subset selection validation; message text |

**Measured:** original environment block `O:21–48` equals `U:22–49` byte for byte; entire suffix `O:117–185` equals `U:171–239` byte for byte. Every other change appears in table/diff.

Classification conventions for status:

- `diff_argument_handling=yes`; `diff_subset_selection=yes`.
- `diff_messages_or_log_paths=yes` because messages/comments/check errors change and preprocessing emits additional logs. Existing log filename/location stays `out/run_command/run_command.log` (`O:64`, `U:65`). No relocated log sink.
- `diff_output_locations=yes` because new preprocessing directories/CSVs/PDBs appear beneath `out/run_command/unit-preprocess-*` (`U:110,113–114,119,128`). Original final result locations remain unchanged. Flag includes additional intermediate output locations.
- `diff_binary_or_entry=yes` counts added published `pinder_methods preprocess` action/entry at `U:113–116`. Python/console-script paths and measured `predict`/`pinder_eval` entries are unchanged. This flag does **not** mean native docking binary was replaced.
- Environment, thread setting, per-unit configuration/scale and working-directory differences: all `no`. Requested job count changes only as intended subset selection. No new `cd` or environment override. Additional preprocessing has its own work; no new OMP/MKL/OpenBLAS cap.
- `diff_other=no`: changes all covered above. Input-validation and failure handling are part of selection/argument implementation, not undisclosed computational changes.

## 2. Per-unit computation and byte equality

**Read:** same `VPY=baseline-published/venv/bin/python`; same `pinder_methods predict` invocation (`O:119–120`, `U:173–174`), `--data_dir data/frodock`, result directory, `--subset pinder-s`, `--pairs all`, YAML config. Same native binary search path and required binary names (`O:45–48,71–72`; `U:46–49,72–73`). Same `pinder_eval` and worker count (`O:180`, `U:234`). Same chain-label restoration, raw-original archive and validation (`O:126–174`, `U:180–228`).

**Read:** same explicit environment: `CUDA_VISIBLE_DEVICES=''`, GPU count 0, solutions 50, MPI ranks 8, force false, evaluation workers 8, method frodock, `PINDER_BASE_DIR=data`, release `2024-02`, log level INFO, unbuffered Python, unset `PINDER_DATA_DIR`, identical CUDA-layout/PATH selection, no bytecode, same TMPDIR (`O:22–48,65–66`, `U:23–49,66–67`). Configured parallelism is fixed; total native/helper/library thread population is not established by an eight-rank setting. `--th 10` in intake's stage command is not evidence of ten threads (`baseline.json:33`). No changed explicit thread control found.

**Read/inferred:** `U:130` appends original row, not regenerated row. Thus successful selector passes original prepared input paths to unchanged prediction. `U:123–129` first requires regenerated receptor/ligand paths and bytes to match originals. Guard failure aborts rather than silently changing inputs. Actual `data/frodock/` source tree was not saved locally; guard success cannot be checked here. Extra subprocesses finish before prediction, so their Python environment mutations do not directly alter parent shell; cache/filesystem side effects remain possible and unaudited.

**Measured:** all 800 listed reproduce PDBs match corresponding saved profile PDBs byte for byte: 342,779,850 bytes/run; no mismatches. Saved full-run setup CSVs also match bytes. This independently confirms narrow serial repeatability claim in `run9_outputs/REPORT.md:27–35` and writer `REPORT.md:42`. It does not establish subset/reordered/concurrent equality.

**Inferred/unknown:** same explicit per-job computation is preserved conditional on selection/guards succeeding and absence of sequence-dependent state. Full native/dependency source unavailable; no candidate run, isolated-unit run or reordered run observed. Therefore `same_computation_per_unit=unknown`, not an assertion of changed numerical work. Combined metrics/leaderboard will describe different selected sets and missing-case penalties; contract excludes these shared files from manifest, correctly. Equality claim concerns listed PDBs only.

Extra preprocessing was setup-only in original protocol (`setup.sh:3975–3984`; `EXECUTION.json:35`), but candidate invokes it once per requested unit inside probe's timed process. Adds input regeneration, byte reads and logs beyond measured command. Cost metadata still satisfies recorded-docking-cost requirement; those costs do not estimate all new overhead. No amount or performance impact inferred.

## 3. Writes, absolute paths, MPS, status propagation

**Read:** explicit wrapper writes all stay under `out/`: history/moves/log (`U:52–65`), temp directory (`66–67`), YAML (`78–82`), private preprocess output (`110–114`), selected CSV (`131–134`), decoys/restoration archive/manifest and scoring (`173–234`). Patch stages native work in `tempfile.mkdtemp()`; inherited TMPDIR directs ordinary temporary files to current invocation's `out/tmp/`. No explicit source/data write in candidate helper. Preprocess receives private output directory, not shared prepared input directory.

**Unknown:** complete program/dependency/cache writes. Shared `PINDER_BASE_DIR=data` plus imports of `get_index` and new preprocessing can access shared state. Saved code excerpts/logs are not a filesystem-write trace or complete dependency source. Neither forbidden write nor exhaustive absence established. Thus `writes_only_out_or_temp=unknown`. This confirms writer's caveat at `REPORT.md:105`; do not reduce it to unconditional yes based on shell redirections alone.

**Read — literal contract mismatch:** absolute run-local paths **are constructed**, inherited unchanged from original:

```sh
# U:48; original O:47
export PATH="$PWD/baseline-published/frodock/bin:$PWD/$VENV/bin:$PATH"
# U:67; original O:66
export TMPDIR="$PWD/out/tmp"
```

These resolve relative to each invocation's working directory; no hard-coded previous `/tmp/m5-...` run path is embedded. They support sibling work isolation, and TMPDIR still targets permitted out/. Nevertheless they are absolute paths into invocation's run directory. Literal SCHEMAS `:55–56` forbids these. Writer's blanket “All paths are relative” (`U:5–6`; `REPORT.md:83`) is false literally. Distinguish dynamic absolute paths from nonportable hard-coded run paths; practical portability problem is not demonstrated. No dedicated absolute-path status field exists; literal mismatch contributes to `contract_met=no`. It is inherited, so `diff_environment=no` and `diff_working_directory=no` remain correct.

**Read:** candidate contains no `CUDA_MPS_*` assignment, unset, override or daemon command; only prose says variables inherited. `mps_untouched=yes` for reviewed wrapper. Empty CUDA visibility is unrelated to MPS variables. Native CPU-only behavior gives no contrary saved evidence.

**Read:** no ids exits 2 (`U:20`). Prediction failure returns captured code (`173–178`); scoring uses `${PIPESTATUS[1]}` and returns scoring code (`233–238`); shell pipefail/errexit catches other wrapper failures. Added preprocessing's ordinary nonzero exit propagates through `sys.exit(exc.returncode)` (`115–118`). No failure-swallowing change in prediction/scoring. Signal termination is a separate edge: negative Python subprocess return code would become shell's low-eight-bit exit value rather than conventional `128+signal`; not exercised, and not proof of successful execution.

## 4. Manifest: coverage, ordering, own files, costs, native identifiers

**Measured:** sole top key `units`; 16 entries, each exactly `id`, `outputs`, `cost_s`; all ids unique and match required regex; all costs finite positive; each output list nonempty, unique, safe relative components without `.`/`..`; output sets disjoint. Paths are relative to out/, e.g. manifest `:6` names `results/frodock/.../holo_decoys/model_1.pdb`. Native final output construction agrees with patch `:43–48` and restoration code.

**Measured:** every full manifest row (`reproduce/out/results/frodock_setup.csv:2–17`), anchors job and actual logged start appears once in identical order: eight ascending native system ids, holo then apo. Thus `units_complete_and_ordered=yes` for full 16-job coverage/order. Native acceptance is assessed separately below; this flag does not certify it.

**Measured:** each entry lists exactly its 50 `model_1.pdb` through `model_50.pdb`, matching complete file set of its own directory. All 800 files exist. No combined CSV, summary, log, config, tarball or shared manifest listed. `outputs_own_files_only=yes`.

**Measured/read:** every `cost_s` equals corresponding `anchors_details.json` `docking_wall_s` float exactly, and equals independent subtraction of log timestamps converted to epoch seconds, reproducing parser's floating-point rounding. `costs_match_records=yes`; sum 4536.183000564575 s agrees with details `:441`. Parser definition: `run_anchors.sh:109–116,128–134,151`; first “Running FroDock” to “Copying the results”, before copy completion, repair and scoring. Cost is recorded per-job docking interval, not total wrapper lifecycle time. Table below independently cross-references every entry.

**Read — native identifier qualification unresolved:** first manifest id is `1a19__A1_P11540--1a19__B1_P11540:holo` (`units.json:4`). Candidate gets original `id` and `kind` separately (`U:108–109`) and passes only native system id to `--ids`, plus `--pairs holo` (`113–114`). Compound string is a wrapper key, never passed verbatim to published selector. Setup successfully used native system-id list and separate kind (`setup.sh:3973–3984`; reproduce `out/setup/preprocess_{holo,apo}.log:2`); evaluation wrapper's split convention (`run_evaluation.sh:98–103,115–128`) is agent-authored interface, not native identifier proof. Intake's claim of predict `--ids` (`baseline.json:22,25`) does not show its effect on an existing full setup CSV; preserved predict loop reads CSV directly.

No saved native source or successful command establishes published option accepts compound keys verbatim. Native acceptance required by question 4/SCHEMAS is **unknown**, not certified, and no fabricated direct `predict --ids <compound>` fix is proposed. Writer openly marks this unresolved (`REPORT.md:30,101–107`); earlier readers establish two-option selection route, not native compound-id support. Functionally candidate uses genuine published preprocess selection followed by ordered original-row assembly; that fact does not establish stronger literal identifier condition.

## 5. Required changes and limits

No changed numerical configuration, binary replacement, native thread setting or working directory found. Syntax/shape checks pass. No workload evidence establishes new selector success, private dependency writes or frozen-output match. Reports must preserve these unknowns. Copying six old files correctly does not waive optional-file contract.

Exact disposition under current literal contract: **omit `run_units.sh` and `units.json` from harness used for launch until unresolved native-id and absolute-path requirements are settled**. Optional-file absence selects existing command-mode probe (SCHEMAS `:102`). This withdraws uncertified optional feature; it does not repair original command's inherited absolute-path discrepancy or provide working unit mode. No files removed or changed by review.

To keep intended 16-job unit interface, owner must first choose a supported contract/interface; no evidence-backed two-file-only repair can be certified from retained source:

1. For current implementation, amend id requirement explicitly to allow wrapper key `(system_id, kind)` encoded as `system_id:kind`, decoded to native `preprocess --ids [system_id] --pairs kind`. Retain current 16 entries, original rows, counts, paths and recorded costs. Otherwise replace this route only after pinned native source proves a selector accepting each listed unique job id; do not assume undocumented compound-id support or patch published program.
2. Resolve literal absolute-path rule explicitly: allow runtime-derived absolute PATH entries and TMPDIR anchored to current work directory, while forbidding fixed paths to previous/shared run roots. Existing original and candidate then need no PATH/TMPDIR code edit. If literal ban must remain, both original and candidate require source-informed adapter/launch redesign. Blind replacement with relative PATH entries can break adapter's temporary-directory `chdir`; no safe exact replacement can be established without complete adapter source. Changing candidate alone would also break required original-environment parity.
3. Before certifying usable unit mode, inspect pinned preprocess/dependency source for shared writes and test generated-input guards plus frozen-baseline byte equality and subsequent U50 arms. This review deliberately ran none. Passing only repeated full runs is insufficient. These are remaining evidence requirements, not permission request or claimed failures.
4. For conventional signal-status parity with original shell-launched commands, replace `U:118` with `sys.exit(exc.returncode if exc.returncode >= 0 else 128 - exc.returncode)`. Ordinary exit codes stay unchanged; signal 9 then yields 137 rather than 247. No signal behavior was exercised here.

Changing grouping to eight native system ids would require redefining units, including both pairings' files and re-deriving each grouped unit's own interval from logs; simply deleting `:holo`/`:apo` creates duplicate ids and wrong output/cost ownership. No such redesign performed.

## Check against writer's report

- `:15–24`, exact copies/hashes/modes/mtimes: independently verified.
- `:28–42`, 16 jobs/order, 50 owned files each, omission of shared outputs: independently verified against CSV, directory contents and actual starts.
- `:46–67`, each cost and cited log/details lines: independently verified; narrower timing scope confirmed.
- `:71–79`, native preprocessing route and original input preservation: code supports construction and guards; candidate preprocessing success unknown.
- `:81`, no-ids and ordinary exit behavior: read from code, not executed. Signal-exit caveat above.
- `:83,89–97`, unchanged explicit environment/suffix and diff inventory: verified. Additional preprocessing outputs/action recorded above. Blanket relative-path wording needs correction.
- `:101–107`, native compound ids, dependency writes, isolated/reordered byte equality unresolved: agree; no native acceptance or runtime success inferred.
- `:111`, structural/static checks: independently repeated five `bash -n` checks and compilation of three embedded Python blocks; all passed. These prove syntax only.

## Per-unit evidence table

Full ids, exact costs and locations follow. Manifest id/cost line numbers reference `run10_harness/units.json`; details cost line references `run9/agent/results/reproduce/out/anchors_details.json`; start/copy lines reference `run9/agent/results/reproduce/out/run_command/run_command.log`.

| Position | Unit id | cost_s | Manifest id / cost lines | Details cost line | Log start / copy lines |
| ---: | --- | ---: | --- | ---: | --- |
| 1 | `1a19__A1_P11540--1a19__B1_P11540:holo` | 42.38700008392334 | 4 / 57 | 42 | 7 / 700 |
| 2 | `1a19__A1_P11540--1a19__B1_P11540:apo` | 40.5 | 60 / 113 | 68 | 701 / 1437 |
| 3 | `1aua__A1_P24280--1aua__A2_P24280:holo` | 198.0659999847412 | 116 / 169 | 94 | 1438 / 2131 |
| 4 | `1aua__A1_P24280--1aua__A2_P24280:apo` | 207.37600016593933 | 172 / 225 | 120 | 2132 / 2825 |
| 5 | `1ax2__A1_P16404--1ax2__A2_P16404:holo` | 150.6159999370575 | 228 / 281 | 146 | 2826 / 3519 |
| 6 | `1ax2__A1_P16404--1ax2__A2_P16404:apo` | 235.1909999847412 | 284 / 337 | 172 | 3520 / 4213 |
| 7 | `1dtd__A1_P48052--1dtd__B1_P81511:holo` | 77.67400002479553 | 340 / 393 | 198 | 4214 / 4891 |
| 8 | `1dtd__A1_P48052--1dtd__B1_P81511:apo` | 156.01600003242493 | 396 / 449 | 224 | 4892 / 5569 |
| 9 | `1dv1__A1_P24182--1dv1__B1_P24182:holo` | 559.922000169754 | 452 / 505 | 250 | 5570 / 6263 |
| 10 | `1dv1__A1_P24182--1dv1__B1_P24182:apo` | 241.19400000572205 | 508 / 561 | 276 | 6264 / 6941 |
| 11 | `1glj__A1_P0A6F3--1glj__B1_P0A6F3:holo` | 442.63899993896484 | 564 / 617 | 302 | 6942 / 7635 |
| 12 | `1glj__A1_P0A6F3--1glj__B1_P0A6F3:apo` | 401.63499999046326 | 620 / 673 | 328 | 7636 / 8329 |
| 13 | `1ht8__A1_P05979--1ht8__B1_P05979:holo` | 549.3090000152588 | 676 / 729 | 354 | 8330 / 9023 |
| 14 | `1ht8__A1_P05979--1ht8__B1_P05979:apo` | 582.4049999713898 | 732 / 785 | 380 | 9024 / 9726 |
| 15 | `1nr5__A1_P07547--1nr5__A2_P07547:holo` | 326.07100009918213 | 788 / 841 | 406 | 9727 / 10420 |
| 16 | `1nr5__A1_P07547--1nr5__A2_P07547:apo` | 325.1820001602173 | 844 / 897 | 432 | 10421 / 11114 |

## Complete independent diff

```diff
--- run9/agent/harness/run_command.sh
+++ run10_harness/run_units.sh
@@ -1,15 +1,15 @@
 #!/usr/bin/env bash
-# run_command.sh - the exact measured baseline command and its complete environment.
+# run_units.sh - the measured baseline restricted through published preprocessing selection.
 #
-# Invoked as:  bash harness/run_command.sh   (working directory = the shared run directory, or a sibling
+# Invoked as:  bash harness/run_units.sh <system_id:holo|system_id:apo>...   (working directory = the shared run directory, or a sibling
 # work directory that links baseline-published/, data/ and harness/). All paths are relative to that
 # working directory. PATH entries are resolved from this working directory because the published
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
@@ -17,6 +17,7 @@
 #   scores:  out/results/frodock_metrics.csv, out/results/frodock_leaderboard.csv
 # Exit status: nonzero if either published command fails.
 set -Eeuo pipefail
+[ "$#" -gt 0 ] || { echo "ERROR: at least one system_id:holo or system_id:apo is required" >&2; exit 2; }
 
 # ------------------------------------------------------------------ complete environment
 export CUDA_VISIBLE_DEVICES=""          # CPU/MPI-only baseline
@@ -79,11 +80,64 @@
 mpi_np: $MPI_NP
 force: $FORCE
 EOF
-cp data/frodock/frodock_setup.csv "$RESULTS/frodock_setup.csv"   # predict reads <results_dir>/frodock_setup.csv
+# Select through the published preprocess --ids / --pairs interface into private out/.
+# Keep the original prepared input paths and bytes used by the measured command.
+"$VPY" - "$VENV/bin/pinder_methods" "$METHOD" "$RUN_DIR" "$RESULTS" "$@" <<'PY'
+import csv, json, re, subprocess, sys, tempfile
+from pathlib import Path
+
+program, method, run_dir, results = sys.argv[1:5]
+requested = sys.argv[5:]
+with open("data/frodock/frodock_setup.csv", newline="") as stream:
+    reader = csv.DictReader(stream)
+    fields = reader.fieldnames
+    full = list(reader)
+by_key = {}
+for row in full:
+    key = row["id"] + ":" + row["kind"]
+    if key in by_key:
+        sys.exit(f"ERROR: duplicate prepared unit {key}")
+    by_key[key] = row
+if len(set(requested)) != len(requested):
+    sys.exit("ERROR: duplicate requested unit")
+for key in requested:
+    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:+=-]{0,127}", key) or key not in by_key:
+        sys.exit(f"ERROR: unknown unit {key!r}")
+selected = []
+for key in requested:
+    original = by_key[key]
+    pid, kind = original["id"], original["kind"]
+    prep = Path(tempfile.mkdtemp(prefix="unit-preprocess-", dir=run_dir))
+    if prep.is_absolute():
+        prep = prep.relative_to(Path.cwd())
+    command = [sys.executable, program, "preprocess", "--method", method,
+               "--data_dir", str(prep), "--ids", json.dumps([pid]), "--pairs", kind]
+    try:
+        subprocess.run(command, check=True)
+    except subprocess.CalledProcessError as exc:
+        sys.exit(exc.returncode)
+    with open(prep / "frodock_setup.csv", newline="") as stream:
+        rows = list(csv.DictReader(stream))
+    if len(rows) != 1 or (rows[0]["id"], rows[0]["kind"]) != (pid, kind):
+        sys.exit(f"ERROR: published preprocess did not select exactly {key}")
+    for column in ("receptor", "ligand"):
+        relative = Path(original[column])
+        fresh_relative = Path(rows[0][column])
+        if relative.is_absolute() or ".." in relative.parts or fresh_relative != relative:
+            sys.exit(f"ERROR: preprocessing changed the prepared input path for {key} {column}")
+        if (prep / relative).read_bytes() != (Path("data/frodock") / relative).read_bytes():
+            sys.exit(f"ERROR: preprocessing changed the prepared input bytes for {key} {column}")
+    selected.append(original)
+with open(Path(results) / "frodock_setup.csv", "w", newline="") as stream:
+    writer = csv.DictWriter(stream, fieldnames=fields)
+    writer.writeheader()
+    writer.writerows(selected)
+print("REQUESTED_UNITS=" + json.dumps(requested))
+PY
 
 # ------------------------------------------------------------------ printed configuration (validated)
 "$VPY" - "$RUN_DIR/frodock_config.yaml" "$RESULTS/frodock_setup.csv" data/selection.json \
-    "$METHOD" "$N_SOLUTIONS" "$MPI_NP" "$FORCE" "$EVAL_MAX_WORKERS" "$BASELINE_GPU_COUNT" <<'PY'
+    "$METHOD" "$N_SOLUTIONS" "$MPI_NP" "$FORCE" "$EVAL_MAX_WORKERS" "$BASELINE_GPU_COUNT" "$@" <<'PY'
 import json, os, sys, yaml
 import pandas as pd
 from pinder.core import get_index
@@ -96,15 +150,15 @@
 print(f"PINDER_S_APO_PAIRED_COUNT={apo['id'].nunique()}")
 print("SELECTED_IDS=" + json.dumps(ids))
 errs = []
-if sys.argv[4:] != ["frodock", "50", "8", "false", "8", "0"]: errs.append("actual command parameters differ from fixed configuration")
+if sys.argv[4:10] != ["frodock", "50", "8", "false", "8", "0"]: errs.append("actual command parameters differ from fixed configuration")
 if os.environ.get("CUDA_VISIBLE_DEVICES") != "": errs.append("CPU baseline must expose zero GPUs")
 if os.environ.get("PINDER_BASE_DIR") != "data" or os.environ.get("PINDER_RELEASE") != "2024-02": errs.append("dataset environment differs from fixed configuration")
 if ids != sel["ids"]: errs.append("selection from index differs from data/selection.json")
 if sel["n"] != 8 or len(ids) != 8: errs.append("representative scale must contain exactly 8 systems")
 if cfg != {"n_solutions": 50, "mpi_np": 8, "force": False}: errs.append(f"config {cfg} is not the published representative config")
-if sorted(set(jobs["id"])) != sorted(ids): errs.append("frodock_setup.csv ids differ from selection")
-if sorted(set(jobs["kind"])) != ["apo", "holo"] or len(jobs) != 2 * len(ids): errs.append("frodock_setup.csv is not holo+apo for every id")
-if set(zip(jobs["id"], jobs["kind"])) != {(pid, kind) for pid in ids for kind in ("holo", "apo")}: errs.append("frodock_setup.csv lacks an expected id/pairing")
+requested = sys.argv[10:]
+if [pid + ":" + kind for pid, kind in zip(jobs["id"], jobs["kind"])] != requested: errs.append("frodock_setup.csv differs from requested unit order")
+if not set(zip(jobs["id"], jobs["kind"])).issubset({(pid, kind) for pid in ids for kind in ("holo", "apo")}): errs.append("frodock_setup.csv has a unit outside the fixed selection")
 print(f"CONFIG method=frodock subset=pinder-s pairs=holo,apo n_jobs={len(jobs)} n_solutions={cfg.get('n_solutions')} "
       f"mpi_np={cfg.get('mpi_np')} force={cfg.get('force')} CUDA_VISIBLE_DEVICES='{os.environ.get('CUDA_VISIBLE_DEVICES')}' "
       f"host_nproc={os.cpu_count()} PINDER_BASE_DIR={os.environ.get('PINDER_BASE_DIR')}")
```
