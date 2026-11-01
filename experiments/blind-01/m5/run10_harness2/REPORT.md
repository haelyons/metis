# Run10 harness2: restricted measured command, incomplete contract certification

Date: 2026-11-01. This candidate removes the extra preprocessing and its extra outputs from run10's unit command. It retains the exact measured prediction, repair and evaluation commands, all original per-job parameters, the original prepared inputs and the original final output paths. Selection now restricts the setup CSV that the published prediction loop actually consumes.

**Not every review finding can be resolved from the permitted evidence and immutable baseline.** Effective native CLI selection of the 16 compound identifiers is not established; this candidate uses the published CSV input mechanism instead. Exhaustive dependency-write confinement and equivalence under isolation/reordering remain unknown. The copied original command constructs absolute PATH and TMPDIR entries, violating the literal path rule. Changing those entries only in the unit script would violate the requested environment parity; changing the original is prohibited. Status therefore reports `some`, `other`, and the relevant `unknown` values. This is a reviewable partial correction, not certification that the optional U50 interface meets its full literal contract.

## Scope and evidence

Read `run10_review/REPORT.md` and `status.json` first, then `run10_harness/REPORT.md`, `run9_units/REPORT.md`, `run9_outputs/REPORT.md`, the requested SCHEMAS sections, saved harness/source/configuration, and selected reproduce logs and outputs. Contract: `/home/hal/dev/interp/metis-wt/dut/pipeline/m5/SCHEMAS.md:54–57` and `:102–114`. Full run's frozen-output comparison and subsequent U50 arms are validation still to be performed by the pipeline.

Only `run10_harness2/` was written. No workload, harness execution, network fetch, box contact, git command, credential, `.keys` file or `~/.codex/` access. Checks used file reads, comparisons, arithmetic, Python compilation, and `bash -n`. Existing launcher logs were left untouched. Directory sizes measured before selective reads: run9 harness 1.3 MiB, results 6.2 GiB, reproduce out 2.1 GiB (results 330 MiB, temporary files 1.1 GiB, command records/history 669 MiB); saved agent workflow 4.3 MiB. No large profiler database, archive or model PDB contents were read.

Paths below are relative to this experiment directory unless stated otherwise. `O` denotes `run9/agent/harness/run_command.sh`; `U` denotes `run10_harness2/run_units.sh`. Source-line citations distinguish upstream lines from local shell/patch lines.

### Additional saved source found

The review's claim that retained source contains only patch excerpts is too broad. `run9/agent/wf/agents/0006-anchors-repair/codex-1.jsonl:103`, completed command `exec-188fbfc5-f134-441e-ad67-2c7cf9c1c1a3`, embeds the published `src/pinder-methods/pinder/methods/run/frodock/predict.py`, upstream lines 1–233, an excerpt of `src/pinder-eval/pinder/eval/dockq/method.py`, lines 81–260, and `src/pinder-eval/pinder/eval/run.py`, lines 1–104. The recorded fetch command specifies PINDER commit `ebeb28a2f8411363cef722b7d293c978f7442672`. These were read from the saved local record, never fetched again or executed. JSON decoding preserves source string escapes; no replacement of literal `\\n` was used to derive citations.

The same JSONL record `:129` preserves `src/pinder-core/pinder/core/index/utils.py` excerpts: `get_pinder_location`, `get_pinder_bucket_root`, `get_index_location`, and the beginning of `get_index`. This is additional dependency evidence, not a complete dependency audit. No complete retained `pinder.methods.main` source or native numerical source was located. Its relevant prediction loop is preserved in `run9/agent/harness/pinder_frodock_fixes.patch:12–20` and the identical saved applied patch.

These are recorded source observations, not fresh upstream hash verification. Installed identity is tied to the saved setup record, pin and applied patch. FroDock's identity with the original study distribution remains conditional on the previously owner-approved unverified mirror; this candidate changes no software source or binary.

## Exact copies

Used `cp -p run9/agent/harness/* run10_harness2/`. Source has six regular files and no hidden entries. All six destination files match bytes, permission modes and nanosecond modification times. None was edited.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| pinder_frodock_fixes.patch | 2710 | 295af03d22550b21c1e0852f723f324c35e9f5caa75e1759ba82bee5ed0259c3 |
| pinder_inputs.tsv | 594653 | 0bf8878fc67eb4fd8eece475f05a76e189f7a086529d7c1616d54db572219645 |
| run_anchors.sh | 8346 | 2870d3e3befdca2874da392c7a92aba9c9474dd5694279d0bc878bff427171eb |
| run_command.sh | 10284 | 08d645d90c83ce0548f72e9a0b6a6e2a038bf188f8c6f13eefae1f385f231ae5 |
| run_evaluation.sh | 12480 | 438dcb8dfd43d204723f05daf37cb3caaf725a9389ed4edaf7322f44019a477f |
| setup.sh | 620353 | b917551e17ce2fe1aa9ae56cbbef43b17256e98cbbfa3797957911c6c44f8c20 |

## Review findings and disposition

| Review finding | Correction or remaining limit |
| --- | --- |
| Added published preprocess entry/action inside measured invocation | Removed completely. `U:134–135` equals `O:119–120`; the whole predict/repair/score suffix is byte-identical. The existing configuration-validation Python process also writes the selected setup CSV; no new Python process or published action was added. |
| Additional private preprocessing output locations | Removed completely. No `unit-preprocess-*`, regenerated input PDBs or preprocess logs. The sole selection write is the existing `out/results/frodock_setup.csv` (`U:122`), replacing the original full-manifest copy. Every other explicit output path is unchanged. |
| Extra setup work contaminates timing | Input regeneration, per-unit subprocess startup and regenerated-input byte comparisons are gone. Reading/serializing the subset CSV remains selection overhead; no time estimate is fabricated. |
| Unestablished same per-unit work | Original complete manifest rows are selected without altering any field, in argument order (`U:113–122`). The preserved published loop calls the same per-job function with the same row and parameters. Newly located full adapter source strengthens this proof, detailed below. Native numerical state/dependencies and isolated/reordered byte equality are still not certified. |
| Exhaustive out/temp write confinement unknown | Selection adds only the existing results CSV write. Explicit wrapper and adapter writes are under out/temp. Dependency source also reveals conditional shared-data creation/download paths; absence of all such writes is not established. Status remains `unknown`. |
| Literal absolute paths inherited from original | Preserved to obey exact-copy and environment-parity instructions. `O:47,66` / `U:49,68` construct `$PWD`-based absolute PATH/TMPDIR entries. Header no longer falsely says every path is relative. Literal relative-only requirement remains unresolved. |
| Compound unit ids lack established native option acceptance | No undocumented `predict --ids <ID:kind>` call was invented. CSV rows use separate native `id` and `kind`. The wrapper resolves the compound key to an original row. This is classified `other`, not `published_option`; strict native-identifier/CLI-option requirement remains unresolved. |
| Native preprocessing signal status converted incorrectly through Python | Added preprocessing subprocesses and their exception/status conversion were removed. Prediction and evaluation retain original direct shell status capture. No signal-path execution was performed. |
| Copies, manifest coverage/order, own outputs and recorded costs pass | Preserved and checked again. No evidence-backed correction to manifest shape, paths, costs or order is needed. Native compound-id acceptance is a distinct unresolved issue, not a reason to invent new ids or redefine scientific units. |
| Candidate success/subset byte equality not observed | No workload was authorized here. Syntax and static checks are reported separately from runtime validation. Previous readers' two full-run byte comparisons do not establish reordered, isolated or concurrent equality. |

## Subset mechanism and unchanged command

The saved patched `pinder.methods.main` code reads `Path(results_dir) / f"{method}_setup.csv"` and immediately iterates `inference_config.to_dict("records")`, calling `predict_method(complex_config, config_dict)` for each record (`pinder_frodock_fixes.patch:13–20`, upstream main.py around 130–136). The retained excerpt provides no filtering of those records by `--ids` or `--pairs`. Intake `baseline.json:22,25` describes a predict `--ids` interface, but this does not establish that it filters an already-prepared full setup CSV, accepts a compound key, or preserves arbitrary requested order. A full effective CLI selector for this measured entry point cannot be established from the retained source.

Native preprocessing selection does exist: `setup.sh:3973–3984` invokes `preprocess --ids <JSON system-id list> --pairs holo|apo`, and `:3987–4004` assembles the original full setup CSV. Successful saved preprocess logs contain eight systems per pairing. That route regenerates inputs and introduces another action/output tree inside the timed invocation, exactly the first review defect. It was therefore removed.

The fallback is the **published prediction input-manifest mechanism**: prepare only the requested original records at the same setup-CSV path, then invoke exactly the original predict command. This is a wrapper-side manifest restriction, not the published program's own CLI subset option. It uses the program's existing record-consumption mechanism without modifying its code. Consequently `subset_mechanism=other`. The user explicitly allowed a documented alternative published mechanism where the measured entry point cannot select the subset; the stronger literal U50 native-option requirement is still not certified here.

All full-universe/configuration checks remain: eight preregistered system ids, holo and apo rows, 50 solutions, eight MPI ranks, force false, zero visible GPUs, eight evaluation workers, same release and data root. Only after checking the full manifest does `U:113–122` validate unique, safe requested keys, reject unknown keys and write selected complete rows in argument order. This retains all columns, receptor/ligand paths and values. Pandas may reserialize CSV text; the published computation consumes parsed records, not CSV formatting. Input structures are neither regenerated nor copied to another input tree.

No arguments exits 2 before environment/output setup (`U:21`). Duplicate/unknown ids fail before prediction. Successful selection uses the same `baseline-published/venv/bin/python`, console entry, `--method frodock`, `--data_dir data/frodock`, `--results_dir out/results`, `--subset pinder-s`, `--pairs all`, and YAML path. No new working-directory change, configuration override, thread cap, environment export, MPS operation or result relocation. The complete original environment block compares byte for byte. The suffix beginning “published docking command” also compares byte for byte, including prediction status capture, chain restoration, raw archive, evaluation pipeline and evaluation status propagation.

`command_differs_only_in_subset=yes` describes this verified command/environment parity and subset-only operational change. It does not certify a native CLI selector, the literal path rule, or runtime result equality. Shell status propagation still reports the published program's exit status, not individual native stages: upstream adapter `predict.py:127–137` uses `subprocess.run(cmd, shell=True)` without `check=True`; that pre-existing behavior was not changed.

## Evidence for each unit's per-job computation

The following chain applies to all 16 entries, not only the first sampled job:

1. `U:93,108–122` reads the same prepared full CSV, verifies the original complete universe and selects whole rows by `(id, kind)` in requested order. No per-row parameter or receptor/ligand value is edited. The original input root remains `data/frodock`.
2. Preserved main.py patch `:13–20` supplies identical `data_dir` and `results_dir`, loads that setup CSV, and passes each row to the same published `predict_method` with the same configuration dictionary. There is no adapter substitution or separate per-unit numerical implementation.
3. Saved upstream `predict.py:209–216` extracts `id`, `kind`, receptor, ligand, results directory, solution count, MPI count and force directly from those records/parameters. Applied patch `:53–64` resolves relative receptor/ligand paths against unchanged `data_dir`. Source `:218–233` performs the same existing-output test and passes exactly those arguments to `frodock`. Both wrappers create a fresh results tree, so force=false does not reuse previous decoys (`O:59–82`, `U:61–85`).
4. Upstream `predict.py:54–57` creates a fresh temporary directory for each job; applied patch `:24–30` stages that job's original inputs before changing directory. Upstream `:59–89` resolves the same binaries, sets the same two OMPI root variables on every job, and builds the same MPI command. No CUDA MPS variable is touched. These OMPI assignments belong to the unchanged program, not new wrapper overrides.
5. Upstream `predict.py:91–124,126–137` defines and executes the same eight stages: four grids, docking with `--th 10` and the same SOAP file, clustering with the same 50-solution count, visualization and coordinate generation. Eight MPI ranks remain fixed. `--th 10` is not treated as evidence of ten threads.
6. Upstream `predict.py:139–166` loads the current job's receptor/transformed ligands, writes ranked poses, removes temporary extra PDBs and restores cwd. Upstream `:169–172`, with applied patch `:43–48`, copies models to `results_dir/frodock/<id>/<kind>_decoys/`. That expression has no job index or selected-set component.
7. `U:147–189` equals `O:132–174`: chain restoration reads that job's own CSV row and PDB bytes, preserves all coordinates/ranks, and writes at the same PDB path. `U:195` equals `O:180`: published evaluation still runs with eight workers. Combined score CSVs depend on selected cases and are correctly excluded from per-unit outputs.

This establishes the same explicit per-row call, inputs, parameters, native stages, repair and output mapping. It does **not** establish every native/library state effect or bitwise equivalence after reordering/isolation. The complete native numerical implementation and all dependencies are not retained; no allowed run tests those effects. Thus the broader `same_computation_per_unit` status remains conservatively `unknown`, despite the demonstrated call-level parity.

### Every listed unit

`units.json` was copied byte-for-byte with `cp -p` from `run10_harness/units.json`. It retains 16 safe unique wrapper keys in full-run order, 50 disjoint model paths per unit, and the exact recorded positive finite `docking_wall_s` floats. Each full output path set was checked against its saved directory's exact filenames; all 800 files exist. No combined CSV, log, summary or archive is included. Deleting pairing suffixes would create duplicate ids; regrouping to eight systems would redefine units, outputs, order and costs. Neither is an evidence-backed identifier-only correction.

The table links every key to its unchanged source record, recorded cost and actual full-run start/copy markers. CSV lines refer to `run9/agent/results/reproduce/out/results/frodock_setup.csv`; log lines refer to `run9/agent/results/reproduce/out/run_command/run_command.log`. For each row, owned outputs are exactly `results/frodock/<system-id>/<kind>_decoys/model_1.pdb` through `model_50.pdb`, relative to out/.

| Position | Unit id | Original CSV line | cost_s | Full log start / copy |
| ---: | --- | ---: | ---: | --- |
| 1 | `1a19__A1_P11540--1a19__B1_P11540:holo` | 2 | 42.38700008392334 | 7 / 823 |
| 2 | `1a19__A1_P11540--1a19__B1_P11540:apo` | 3 | 40.5 | 824 / 1673 |
| 3 | `1aua__A1_P24280--1aua__A2_P24280:holo` | 4 | 198.0659999847412 | 1674 / 2664 |
| 4 | `1aua__A1_P24280--1aua__A2_P24280:apo` | 5 | 207.37600016593933 | 2665 / 3717 |
| 5 | `1ax2__A1_P16404--1ax2__A2_P16404:holo` | 6 | 150.6159999370575 | 3718 / 4526 |
| 6 | `1ax2__A1_P16404--1ax2__A2_P16404:apo` | 7 | 235.1909999847412 | 4527 / 5354 |
| 7 | `1dtd__A1_P48052--1dtd__B1_P81511:holo` | 8 | 77.67400002479553 | 5355 / 6134 |
| 8 | `1dtd__A1_P48052--1dtd__B1_P81511:apo` | 9 | 156.01600003242493 | 6135 / 6901 |
| 9 | `1dv1__A1_P24182--1dv1__B1_P24182:holo` | 10 | 559.922000169754 | 6902 / 7735 |
| 10 | `1dv1__A1_P24182--1dv1__B1_P24182:apo` | 11 | 241.19400000572205 | 7736 / 8543 |
| 11 | `1glj__A1_P0A6F3--1glj__B1_P0A6F3:holo` | 12 | 442.63899993896484 | 8544 / 9558 |
| 12 | `1glj__A1_P0A6F3--1glj__B1_P0A6F3:apo` | 13 | 401.63499999046326 | 9559 / 10524 |
| 13 | `1ht8__A1_P05979--1ht8__B1_P05979:holo` | 14 | 549.3090000152588 | 10525 / 11431 |
| 14 | `1ht8__A1_P05979--1ht8__B1_P05979:apo` | 15 | 582.4049999713898 | 11432 / 12303 |
| 15 | `1nr5__A1_P07547--1nr5__A2_P07547:holo` | 16 | 326.07100009918213 | 12304 / 13128 |
| 16 | `1nr5__A1_P07547--1nr5__A2_P07547:apo` | 17 | 325.1820001602173 | 13129 / 13947 |

Costs exactly match `run9/agent/results/reproduce/out/anchors_details.json` job records. They measure “Running FroDock” to “Copying the results”, as defined at `:6` and parsed by `run_anchors.sh:109–116,128–134`; they exclude completed copy-out, later chain repair/scoring and wrapper startup. Sum: 4536.183000564575 seconds. Full reproduce reports 16 jobs and the fixed parameters at command log `:4`; prediction and evaluation exit 0 at `:11116,16201`.

Earlier `run9_units/REPORT.md` and `run9_outputs/REPORT.md` independently report 800/800 final PDB files byte-identical between two saved full serial runs, 342,779,850 bytes per run. That comparison was not repeated here. It supports saved full-run repeatability, not new subset success or absence of sequence dependence.

## Writes, paths and remaining uncertainties

All explicit new selection writes target `out/results/frodock_setup.csv`. Original logs/history/configuration, results, raw-decoy archive, repair manifest and score CSVs remain under out/. Original TMPDIR still points to the invocation's out/tmp; the adapter uses `tempfile.mkdtemp()` and writes its grids/search files/models there. `PYTHONDONTWRITEBYTECODE=1` remains unchanged. No wrapper assignment, unset or override of any `CUDA_MPS_*` variable or daemon command was introduced.

This is not an exhaustive confinement proof. Saved core-utils source (`codex-1.jsonl:129`, function `get_pinder_location`) conditionally creates the shared data release directory when absent; `get_index` documents downloading missing data. Saved evaluation source (`:103`, upstream `method.py:243–251`) conditionally creates a native-data directory and calls `download_entry` if the native PDB is missing; `:231–235` delegates that to `PinderSystem`. Setup inventories/prepares inputs, and saved reproduction succeeded, but no complete missing-input/cache behavior or filesystem trace proves every dependency avoids shared writes in the next invocation. No forbidden write was observed by this static assessment. `writes_only_out_or_temp=unknown` is intentional.

The literal absolute-path violation is definite: `export PATH="$PWD/baseline-published/frodock/bin:$PWD/$VENV/bin:$PATH"` and `export TMPDIR="$PWD/out/tmp"` remain at `U:49,68`. These are derived from the invocation cwd, not hard-coded previous run roots, and keep ordinary temp files private; nevertheless they are absolute run-local paths. Making PATH entries relative can break binary lookup after the published adapter changes cwd. No safe environment-identical repair of this literal violation is possible while also preserving the original bytes and environment. It remains explicitly unresolved.

Native compound-id acceptance, effective direct predict CLI filtering, full dependency confinement, native state independence, missing-input behavior, and subset/reorder/concurrency byte equality were not established. No source patch, download, sandbox launcher or environment change was introduced to manufacture those properties. The pipeline's frozen-baseline and repeated-arm comparisons remain necessary; nothing in this report claims they passed.

## Static verification and line-by-line differences

All six required copies match bytes/modes/mtime_ns. Unit JSON bytes match run10 exactly; schema, safe keys/paths, order, costs and all 800 output filenames pass. `bash -n` passed separately for all five shell scripts. Both embedded Python blocks in `run_units.sh` compile without execution. The entire environment block and entire predict/repair/evaluation suffix match the original byte for byte. These are static checks only; neither `run_units.sh` nor any workload was invoked.

Remaining differences:

| Original | Unit script | Difference |
| --- | --- | --- |
| 2, 4–6, 10, 12 | 2, 4–7, 11, 13 | Comments identify subset invocation/scale and disclose inherited absolute paths. |
| after 19 | 21 | Require at least one positional id; empty list exits 2. |
| 82 | 84–85 | Full-manifest copy replaced by explanation; the existing validator writes selected manifest instead. |
| 86 | 89 | Forward unit arguments to existing validator. |
| 87 | 90 | Import stdlib regex for argument validation. |
| 90 | 93 | Read original prepared full CSV directly rather than its full copy at the output path. |
| 99 | 102 | Check the same six fixed parameters separately from appended ids. |
| after 107 | 111–122 | Validate compound keys/duplicates/membership; select unchanged complete rows in requested order; write existing output CSV. |
| 21–48 | 23–50 | Unchanged environment, shifted only. |
| 117–185 | 132–200 | Entire measured predict/repair/evaluation suffix unchanged, shifted only. |

Every other line is unchanged apart from position shifts. Complete mechanically generated unified diff follows.

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

