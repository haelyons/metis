# Run10 harness3

2026-11-01. Prepared-list selection implemented against measured run9 baseline, including its existing repairs. No workload or harness script executed. No box contact, network fetch, git command, credential, `.keys`, or `~/.codex/` read. All authored files and temporary verification files stayed inside `run10_harness3/`; verification temporary directory was removed.

Read all eight requested earlier reports and their status files before writing: `run10_harness/`, `run10_harness2/`, `run10_review/`, `run10_review2/`, `run10_why/`, `run10_mech/`, `run10_inputs/`, and especially `run10_diff/REPORT.md`. Read current `/home/hal/dev/interp/metis-wt/dut/pipeline/m5/SCHEMAS.md:47–80`, including run_command rules, amended U50, and U51; also read unit sample rule at line 114. Earlier native-selector and pristine-upstream requirements are superseded by amended U50. Existing measured repairs remain part of reference.

Evidence below is static file inspection, byte comparison, syntax parsing, or arithmetic on recorded outputs. Runtime equivalence remains unmeasured here. Paths are relative to experiment directory unless absolute. `O` means `run9/agent/harness/run_command.sh`; `U` means `run10_harness3/run_units.sh`; `R` means `run9/agent/results/reproduce/out/`. Log line numbers count LF separators, retaining embedded carriage-return progress updates.

## Exact copies

Ran `cp -p run9/agent/harness/* run10_harness3/`. Source contains exactly six regular files, with no hidden entries. Each destination matches original bytes, permission mode, and nanosecond mtime. All six remain unchanged.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| pinder_frodock_fixes.patch | 2710 | 295af03d22550b21c1e0852f723f324c35e9f5caa75e1759ba82bee5ed0259c3 |
| pinder_inputs.tsv | 594653 | 0bf8878fc67eb4fd8eece475f05a76e189f7a086529d7c1616d54db572219645 |
| run_anchors.sh | 8346 | 2870d3e3befdca2874da392c7a92aba9c9474dd5694279d0bc878bff427171eb |
| run_command.sh | 10284 | 08d645d90c83ce0548f72e9a0b6a6e2a038bf188f8c6f13eefae1f385f231ae5 |
| run_evaluation.sh | 12480 | 438dcb8dfd43d204723f05daf37cb3caaf725a9389ed4edaf7322f44019a477f |
| setup.sh | 620353 | b917551e17ce2fe1aa9ae56cbbef43b17256e98cbbfa3797957911c6c44f8c20 |

## Restricted list and existing input route

`O:82`, retained at `U:84`, copies `data/frodock/frodock_setup.csv` to `out/results/frodock_setup.csv`. Full-universe/configuration validation remains unchanged through `O:115` / `U:117`. Restriction occurs after that validation, before prediction. Full CONFIG diagnostic still describes validated 16-row source universe; subsequent `RESTRICTED_UNITS` diagnostic identifies actual requested records in order.

`U:21` requires positional ids and exits 2 before environment/output setup when none is supplied. `U:121` passes all arguments, quoted, to selection helper using unchanged baseline Python interpreter. `U:128–144` reads copied list as bytes, parses CSV only to map `id + ':' + kind` to original records, and rejects empty/duplicate requests, duplicate source keys, unknown/invalid ids, unexpected schema, or unexpected record layout. Recorded format is UTF-8 CSV, header `id,kind,receptor,ligand`, one newline-terminated physical line per record. `U:132–138` checks this layout.

`U:145` writes original header followed by selected original byte lines in argument order. No CSV writer, pandas serialization, input regeneration, preprocessing call, new numerical parameter, seed, or structural-input copy is introduced. `system_id:kind` identifies original row through its two original fields; it is a wrapper key permitted by current U50.

List stays at existing private `out/results/frodock_setup.csv`. `U:151–152` retains exact measured invocation:

```sh
"$VPY" "$VENV/bin/pinder_methods" predict --method "$METHOD" --data_dir data/frodock \
    --results_dir "$RESULTS" --subset pinder-s --pairs all --config "$RUN_DIR/frodock_config.yaml"
```

`RESULTS=out/results` remains unchanged (`O:52`, `U:54`). Existing `--results_dir` therefore passes directory containing restricted list through program's accepted input mechanism. No new flag or path override is needed. Installed reader is `pd.read_csv(Path(results_dir) / f"{method}_setup.csv")`, then record-order prediction loop: copied `pinder_frodock_fixes.patch:13–20`; saved main source `run10_why/evidence/main.py.txt:130–136` interpreted with that applied repair. Complete body at source lines 102–140 does not consume declared ids/subset/pairs selection parameters. Source provenance and differential assessment are documented in `run10_diff/REPORT.md`.

Byte comparisons establish `O:21–116` equals `U:23–118`, and entire prediction/repair/scoring suffix `O:117–185` equals `U:149–217`. Same binary/interpreter paths, environment, cwd, CUDA visibility, 50 solutions per unit, eight MPI ranks, force=false, eight scoring workers, YAML, structural paths, SOAP input, installed source, native stages, chain repair, evaluator, output paths, and exit handling remain. No new `cd` or environment export. No `CUDA_MPS_*` operation added.

Baseline source repairs in copied patch and output-affecting HETATM chain restoration (`O:126–174`, `U:158–206`) are inherited measured code. `new_code_change=no` refers to measured program/per-unit code; required wrapper selection helper is new selection logic expressly allowed by U50. `command_differs_only_in_selection=yes` describes verified static command parity and selection changes, including comments, argument checks, byte-list construction and its diagnostic.

Prediction status is captured/returned unchanged (`U:150–156`); scorer status is captured using `${PIPESTATUS[1]}` and returned unchanged (`U:211–217`). Selection failure propagates via existing shell errexit. Only new selection write is existing `out/results/frodock_setup.csv`; `adds_writes_outside_out=no`. Existing history, log, YAML, archive, repair manifest, evaluation outputs, and temporary stage handling are retained.

## Reused units.json

After validation, ran `cp -p run10_harness/units.json run10_harness3/units.json`; bytes match exactly. Sole top key is `units`; all 16 full-run units appear in original CSV order, one per original `(id,kind)` record, holo then apo for each of eight systems (`R/results/frodock_setup.csv:2–17`). Each entry has exactly `id`, `outputs`, `cost_s`; ids satisfy contract regex and are unique. Current U50 requires ids understood by wrapper, so compound keys need no change.

Each unit owns exactly `results/frodock/<system_id>/<kind>_decoys/model_1.pdb` through `model_50.pdb`, relative to out/. Validated all 800 files exist under R, every output directory contains exactly its 50 listed files, paths satisfy component rules, and output sets are disjoint. No shared CSV, log, summary, config, archive, or manifest is listed. Output construction is supported by copied patch lines 43–48 and unchanged repair loop `O:140–142` / `U:172–174`.

Each finite positive cost equals corresponding `R/anchors_details.json` job's `docking_wall_s` exactly. Independently reconstructed same float from recorded start/copy timestamps in `R/run_command/run_command.log`, using baseline parser's epoch-timestamp subtraction (`run_anchors.sh:109–116,128–134`). Full logged start order also equals manifest order. Costs measure Running FroDock to Copying results, excluding completed copy-out, later repair/scoring and wrapper overhead; definition is `R/anchors_details.json:6`. Total recorded cost: 4536.183000564575 s.

## Inherited path conflict — separate from selection

Definite literal relative-path-rule conflict is inherited unchanged:

```sh
# O:47 / U:49
export PATH="$PWD/baseline-published/frodock/bin:$PWD/$VENV/bin:$PATH"
# O:66 / U:68
export TMPDIR="$PWD/out/tmp"
```

Both construct absolute paths into current invocation directory, contrary to SCHEMAS.md:55. TMPDIR still names private out/tmp; PATH entries are binary lookup locations. Neither proves a write outside out/temp. Current U50 expressly records baseline path conflicts separately; preserving measured environment retains these lines. `inherited_path_conflict=yes` records this definite path-spelling conflict. Earlier run10_diff status used unknown for broader forbidden-dependency-write question; it also explicitly established this separate absolute-path conflict. Unit selection adds no such conflict.

All explicit retained wrapper writes are under out/. Full dependency write confinement remains unknown: core helper conditionally creates release directory/downloads index (`run10_review2/saved_core_utils_excerpt.py.txt:24–26,62–65`); evaluator can create/download missing natives (`run10_inputs/evidence/eval_method.py.txt:231–251`). Available records do not prove those branches occur or never occur with prepared setup. Selection introduces no new shared-data operation; no exhaustive runtime write trace was collected. Setup's existing installations/downloads are unchanged, outside measured command, and were not executed here.

## Verification and limits

Each of five shell files passed its own separate `bash -n` invocation. All three embedded Python blocks parsed with `ast.parse`. Baseline validation and PDB-repair Python were never executed during checks. Exact selection block alone was compiled/executed against private CSV fixtures using Python standard library, with no workload imports or subprocesses.

Applied contract's median-cost sample rule: zero-based manifest indices 3, 5, 9, 15, in that order. These are apo rows for 1aua, 1ax2, 1dv1, 1nr5. Sample has 200 owned outputs; recorded cost sum 1008.9430003166199 s. Exact helper wrote 644-byte list consisting only of original header and those four original byte-identical records in order. Original prepared-copy SHA-256: `9e29837be20fb33f8cd891dea4ee36cf3bbaa62c3d9339cab6beb7d7b4fd6f56`. Sample-list SHA-256: `f34c87e11bc77f02997f41aaae17cf6958ce02976b9621886d96c03029b27af0`.

Nineteen successful selection checks covered actual four-unit sample, reversed sample, complete original order, and all sixteen singletons. Compared output bytes against direct original-byte concatenation, checked each record separately against original parsed record, and checked absence of any additional records. Three rejection checks covered empty, duplicate, and unknown requests, each leaving fixture unchanged. Frozen reference remained unchanged. Test fixtures were confined to temporary child of destination and removed.

Not established: future prediction/scoring success, subset/full/reordered/isolated/concurrent output equality, resource behavior, or future timings. No U51 comparison has run here. Prior report `run10_diff/REPORT.md` measured 800/800 final files identical between recorded reproduce and profile full runs; that comparison was not repeated here and establishes neither subset equivalence nor independence from order. Native SAS code has existing wall-clock seeding and conditional random rotations (`run10_inputs/evidence/sas.cpp.txt:683–690,747–759`), so source parity alone cannot prove byte invariance. No seed/code change attempted.

Original remote data tree and installed executable bytes were not rehashed: local checks use recorded full list preserved by baseline's exact copy, saved output paths/costs, retained source evidence, and unchanged setup/binary paths. No independent fresh structural-input or remote-binary identity claim is made. Baseline native subprocess behavior lacks independent `check=True` enforcement, as documented by earlier readers; shell still propagates original published-entry and scorer statuses. These are inherited limits. U51 first compares requested sample's actual files byte for byte with run9 reference; if needed, its full-run variability control distinguishes future subset mismatch from ordinary variability. No expected comparison outcome is fabricated.

## Every line difference

| Original O | Unit script U | Difference |
| --- | --- | --- |
| 2 | 2 | Description identifies original-record restriction. |
| 4–6 | 4–7 | Positional-id invocation and disclosure of inherited absolute paths; comments only. |
| 10, 12 | 11, 13 | Comments state requested jobs and unchanged 50 decoys per job. |
| after 19 | 21 | Nonempty argument guard, exit 2. |
| 20–116 | 22–118 | Unchanged original blank/environment/output setup/full-list copy/full validation/version diagnostic. |
| after 116 | 119–148 | Selection comments, helper invocation/imports, id/schema/layout validation, raw-byte record selection/write and diagnostic. |
| 117–185 | 149–217 | Entire prediction, status, inherited repair/archive, scorer and final exit unchanged. |

No other differences. Mechanically generated complete unified diff follows.


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
