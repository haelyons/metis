# Run10 harness source

Date: 2026-11-01. Writes confined to `run10_harness/`. No workload, script invocation, box contact, network fetch, or git command. No credential, `.keys`, or `~/.codex/` file read. Existing launcher logs left untouched.

## Evidence and source location

Read `run9_units/REPORT.md`, `run9_outputs/REPORT.md`, `run9_par/REPORT.md` first. Requested `run9/A/` does not exist; saved equivalent is `run9/agent/`, as those reports explain. No paths outside destination changed to hide that difference.

Read `/home/hal/dev/interp/metis-wt/dut/pipeline/m5/SCHEMAS.md:47–58`, especially Optional unit files U50 at 56 and run_command rules at 54–57; also Unit mode U50 at 102–114. Native unique-unit-identifier requirement remains unresolved, as detailed below.

Measured directory sizes before selective inspection: harness 1.3 MiB, reproduce 2.1 GiB. Read small manifest and anchors-details JSON, selected harness code, and grep-selected timing/configuration/exit lines from reproduce command log. No large profiler database, archive, or pose-file contents read.

## Exact copies

Ran `cp -p run9/agent/harness/* run10_harness/`. Source has these six regular files and no hidden files. All six copies remain unchanged. Verified byte equality, permission modes and nanosecond modification times.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| pinder_frodock_fixes.patch | 2710 | 295af03d22550b21c1e0852f723f324c35e9f5caa75e1759ba82bee5ed0259c3 |
| pinder_inputs.tsv | 594653 | 0bf8878fc67eb4fd8eece475f05a76e189f7a086529d7c1616d54db572219645 |
| run_anchors.sh | 8346 | 2870d3e3befdca2874da392c7a92aba9c9474dd5694279d0bc878bff427171eb |
| run_command.sh | 10284 | 08d645d90c83ce0548f72e9a0b6a6e2a038bf188f8c6f13eefae1f385f231ae5 |
| run_evaluation.sh | 12480 | 438dcb8dfd43d204723f05daf37cb3caaf725a9389ed4edaf7322f44019a477f |
| setup.sh | 620353 | b917551e17ce2fe1aa9ae56cbbef43b17256e98cbbfa3797957911c6c44f8c20 |

## Unit manifest

`run9/agent/results/reproduce/out/results/frodock_setup.csv:2–17` lists full processing order: eight system IDs in ascending order, holo then apo for each. `pinder_frodock_fixes.patch:16–20` shows prediction iterating manifest records in order. Reproduce `out/run_command/run_command.log:4` records 16 jobs, 50 solutions, eight MPI ranks. Start/copy pairs below confirm actual order; successful `PREDICT_EXIT=0` and `EVAL_EXIT=0` appear at lines 11116 and 16201.

One unit is one manifest row `(system_id, kind)`. `units.json` covers all 16 rows with exactly `{id, outputs, cost_s}`, beneath sole top-level `units` key. Row keys use `system_id:kind`, the convention in saved `run_evaluation.sh:98–103`. These are wrapper identifiers; native `--ids` acceptance of the compound token is NOT established.

Each unit lists exactly 50 paths relative to `out/`:

```text
results/frodock/<system_id>/<kind>_decoys/model_1.pdb
...
results/frodock/<system_id>/<kind>_decoys/model_50.pdb
```

Derivation: `run_command.sh:51–52,119–120` fixes `out/results`; `pinder_frodock_fixes.patch:43–48` builds per-system/per-kind directory and copies model files. Chain repair at `run_command.sh:132–174` remains unchanged.

Checked all 800 listed paths exist as files in `run9/agent/results/reproduce/out/`. Every unit directory contains exactly its listed 50 filenames. Output sets are disjoint. Combined metrics, leaderboard, manifest, summary, logs and raw-decoy archive are excluded. Earlier `run9_outputs/REPORT.md` sections 1–3 establish saved serial byte repeatability; no new pose-byte comparison or workload was run.

## Recorded costs

Each `cost_s` is copied without rounding from that row's `docking_wall_s` in successful reproduce `out/anchors_details.json`. Source therefore `reproduce_outputs`, not profile timings. Definition at JSON line 6 and parser at `run_anchors.sh:109–116,128–134`: logger timestamp from “Running FroDock” to “Copying the results”. Excludes completed copy-out, chain repair and scoring; not full unit lifecycle wall time.

Table cites anchor-details JSON cost line and reproduce `out/run_command/run_command.log` start/copy lines.

| Position | Wrapper unit key | cost_s | JSON line | Log start / copy lines |
| ---: | --- | ---: | ---: | --- |
| 1 | 1a19__A1_P11540--1a19__B1_P11540:holo | 42.38700008392334 | 42 | 7 / 700 |
| 2 | 1a19__A1_P11540--1a19__B1_P11540:apo | 40.5 | 68 | 701 / 1437 |
| 3 | 1aua__A1_P24280--1aua__A2_P24280:holo | 198.0659999847412 | 94 | 1438 / 2131 |
| 4 | 1aua__A1_P24280--1aua__A2_P24280:apo | 207.37600016593933 | 120 | 2132 / 2825 |
| 5 | 1ax2__A1_P16404--1ax2__A2_P16404:holo | 150.6159999370575 | 146 | 2826 / 3519 |
| 6 | 1ax2__A1_P16404--1ax2__A2_P16404:apo | 235.1909999847412 | 172 | 3520 / 4213 |
| 7 | 1dtd__A1_P48052--1dtd__B1_P81511:holo | 77.67400002479553 | 198 | 4214 / 4891 |
| 8 | 1dtd__A1_P48052--1dtd__B1_P81511:apo | 156.01600003242493 | 224 | 4892 / 5569 |
| 9 | 1dv1__A1_P24182--1dv1__B1_P24182:holo | 559.922000169754 | 250 | 5570 / 6263 |
| 10 | 1dv1__A1_P24182--1dv1__B1_P24182:apo | 241.19400000572205 | 276 | 6264 / 6941 |
| 11 | 1glj__A1_P0A6F3--1glj__B1_P0A6F3:holo | 442.63899993896484 | 302 | 6942 / 7635 |
| 12 | 1glj__A1_P0A6F3--1glj__B1_P0A6F3:apo | 401.63499999046326 | 328 | 7636 / 8329 |
| 13 | 1ht8__A1_P05979--1ht8__B1_P05979:holo | 549.3090000152588 | 354 | 8330 / 9023 |
| 14 | 1ht8__A1_P05979--1ht8__B1_P05979:apo | 582.4049999713898 | 380 | 9024 / 9726 |
| 15 | 1nr5__A1_P07547--1nr5__A2_P07547:holo | 326.07100009918213 | 406 | 9727 / 10420 |
| 16 | 1nr5__A1_P07547--1nr5__A2_P07547:apo | 325.1820001602173 | 432 | 10421 / 11114 |

## Published subset route

Saved setup `setup.sh:3973–4004`, especially 3981–3984, invokes published `pinder_methods preprocess --ids <JSON system-ID list> --pairs holo|apo`. Evaluation adapter uses single-system form at `run_evaluation.sh:115–128`. Intake `baseline.json:22` claims predict has `--ids`, but preserved predict loop does not establish filtering of its loaded manifest; no unsupported direct predict filtering was invented.

Candidate `run_units.sh` reads each positional compound key, validates it against prepared full manifest, then obtains native system ID and pairing. Published preprocessing is invoked once per requested row, in requested order. Example only, not executed:

```sh
"$VPY" "$VENV/bin/pinder_methods" preprocess --method "$METHOD"   --data_dir out/run_command/unit-preprocess-<private-suffix>   --ids '["1a19__A1_P11540--1a19__B1_P11540"]' --pairs holo
```

Each preprocessing directory is private under `out/run_command/`. Its CSV must select exactly requested native ID/pairing. Generated receptor/ligand path fields and bytes must equal original prepared inputs. Candidate then writes selected ORIGINAL rows in argument order to `out/results/frodock_setup.csv`. Thus prediction keeps original `--data_dir data/frodock`, original relative input paths and original input bytes.

No arguments exits 2 before environment changes or output writes. Unknown/duplicate unit keys fail. Ordinary nonzero preprocessing exits propagate through Python and shell. Original prediction and scoring exit handling remains unchanged: prediction failure exits with its status; successful prediction proceeds to original repair/scoring; scoring pipeline's program status propagates.

Complete environment block and entire suffix beginning “published docking command” compare byte for byte with original. Same interpreter, published entrypoints, native binaries, 50 solutions/job, eight MPI ranks, force=false, GPU visibility, eight scoring workers, config, chain repair, relative paths and working-directory conventions. No new environment variables exported, no `CUDA_MPS_*` changes, no new `cd`. Explicit added writes stay under `out/`; inherited `TMPDIR=$PWD/out/tmp` remains unchanged.

## Line-by-line differences

Numbers refer to original copied `run_command.sh` and final `run_units.sh`; complete diff follows.

- Original 2, 4, 10, 12: comments describe subset invocation and per-job output count.
- After original 19 / candidate 20: reject empty argument list, exit 2.
- Original 21–81: unchanged environment, output setup, binary checks and config, shifted +1.
- Original 82 / candidate 83–136: replace full manifest copy with published preprocess selection, native ID/pairing and input byte/path validation, and ordered original-row assembly.
- Original 86 / candidate 140: forward argument keys to configuration validator.
- Original 99 / candidate 153: fixed-parameter comparison covers original six parameters, excluding forwarded keys.
- Original 105–107 / candidate 159–161: replace mandatory full-16-row assertions with exact requested order and membership in original eight-system/two-pairing universe. Full-universe selection checks remain.
- Original 117–185 / candidate 171–239: predict, status handling, chain repair and scoring suffix unchanged byte for byte.
- Every other line unchanged except position shifts.

## Limitations and status interpretation

Strict native-identifier requirement cannot be certified. Native `--ids` selects system ID; `--pairs` selects pairing. Eight native system IDs identify 16 measured jobs only when paired with second option. No saved evidence shows a published option accepting unique `system_id:kind` token verbatim, or direct predict flags filtering/reordering loaded full manifest. Wrapper convention comes from saved evaluation adapter, not proof of native token support.

This directory therefore provides documented candidate, NOT a claim of full strict-contract compliance. `subset_mechanism=published_option` describes actual published preprocess `--ids`/`--pairs` calls. `command_differs_only_in_subset=no` flags added preprocessing and compound-key interpretation rather than direct sole restriction by native unique unit identifiers. `units_listed=all_units` describes coverage of all 16 recorded jobs, not native-ID certification. Available evidence cannot supply direct unique native per-job selector without fabrication.

Candidate preprocessing route, guards, subset order, frozen-output equality, concurrent behavior and exit propagation were not exercised. Full installed PINDER/FroDock/dependency source unavailable in saved records. Shared-cache writes through `data/` and cross-unit state cannot be excluded by static inspection. Baseline already imports `get_index`; added published preprocess calls have incompletely documented cache behavior. Explicit script writes are private; exhaustive dependency-write audit remains unknown.

If owner accepts candidate's compound-key interface or adjusts identifier contract, pipeline must still validate frozen-baseline and later arm byte equality. No runtime or concurrency success is claimed here.

## Static verification

All six copies match bytes/modes/mtimes. JSON parses, exact keys checked; 16 unique safe wrapper keys, finite positive recorded costs, 50 unique safe paths/unit, all 800 paths present, disjoint output sets and exact directory filename sets. All three embedded Python blocks compile without executing. Complete environment and measured predict/repair/scoring suffix match original. Bash syntax checked separately for all five scripts via `bash -n`; every exit 0. No workload or harness script executed.

## Complete diff

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
