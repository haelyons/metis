Run10 harness2 explanation — 2026-11-01

Most important failure: **subset_not_published_option**. Corrected wrapper selects rows itself; published predict selector does not select them. No changed per-unit numerical procedure demonstrated. Remaining computation/write unknowns concern evidence limits. Literal inherited absolute-path violation also remains, separately.

Scope: read all four requested REPORT.md/status.json pairs, earlier unit/output reports, named harness/source records and contract. Wrote only run10_why/. No workload, harness invocation, box contact, network fetch, git command, credential/.keys/~/.codex read. File inspection, hashing and standard-library arithmetic only. Paths below relative to experiment directory unless absolute. Log lines count LF bytes, preserving CR progress updates.

**Answers and status meanings**

| Question | Finding | Status |
| --- | --- | --- |
| 1. Most important failure? | Actual restriction is wrapper-side CSV filtering, without effective program subset option. Native compound identifiers also unsupported by shown selector. | subset_not_published_option |
| 2. Baseline entry selects units? Other equivalent published entry? | Predict documents and accepts selection parameters but ignores them. Preprocess implements selection, does no docking. No other published subset-selecting CLI for same FroDock computation found in pinned methods runner. Same underlying Python per-job callable exists; distinction below. | no / no |
| 3. Unit-file-only fix? | No conforming fix for complete literal contract with measured baseline unchanged. Source/contract change needed; changing ids alone insufficient. | no |
| 4. Would wrong computation be caught? | Changed/missing listed sample outputs caught at first comparison; internally different work producing identical listed outputs passes. | partly |
| 5. Realistic risk? | Wasted unit-probe attempt if subset/state/write behavior causes failure or output mismatch. No specific changed numerical computation or misleading factor demonstrated. This is risk assessment, not prediction of failure. | wasted_run |
| 6. Why unknowns? | Missing execution/state/write evidence; conditional write branches do not show they execute with prepared inputs. Separate known selector/path defects do not establish those two unknown properties. | static_reading_limit |

**Measured here: source identity and unchanged code**

Earlier reviews searched saved run9 files. Additional local source archive survives at `/home/hal/.cache/blind01/intake_check_dl/codex/pinder_code.1.body`, identified by `intake_mirror/verify.py:64–66`. Read cached archive, fetched nothing. SHA-256 **b577532820ebbe5c16432b78c5e9c197690e863cb70a0a35a8ebcbe5277b76dd** matches `run9/agent/intake/baseline.json:4–5`, pin **ebeb28a2f8411363cef722b7d293c978f7442672**. Selected five members only; their bytes match corresponding cached extracted sources. Unmodified copies preserved under `run10_why/evidence/` with original line numbering:

| Copy | Original member beneath `pinder-<pin>/` |
| --- | --- |
| evidence/main.py.txt | src/pinder-methods/pinder/methods/main.py |
| evidence/methods_README.md.txt | src/pinder-methods/pinder/methods/README.md |
| evidence/preprocess.py.txt | src/pinder-methods/pinder/methods/preprocess/__init__.py |
| evidence/predict.py.txt | src/pinder-methods/pinder/methods/run/frodock/predict.py |
| evidence/pyproject.toml.txt | pyproject.toml |

These are published source bytes before recorded run9 fixes. Applied fixes remain `run9/agent/harness/pinder_frodock_fixes.patch:3–20,24–64`; they change two main.py lines, not selection handling. No source imported or executed.

Independent byte comparisons confirm `run9/agent/harness/run_command.sh` equals `run10_harness2/run_command.sh`; baseline environment lines 21–48 equal corrected run_units.sh lines 23–50; output setup lines 50–81 equal 52–83; complete predict/repair/scoring suffix lines 117–185 equals 132–200. Thus same explicit binaries, commands, environment, per-job scale and MPI/scoring settings retained. New row selection is principal operational change.

Parsed current units.json: 16 unique safe identifiers, exactly expected keys, 50 distinct outputs each, positive finite costs. Order equals frozen reproduce setup CSV's 16 rows. All 800 listed frozen paths exist. No PDB contents, profiler databases or raw archives needed for this assessment. Prior 800/800 byte equality is **earlier measurement**, not repeated here: `run9_outputs/REPORT.md:25–35`, `run10_review2/REPORT.md:63` report 342,779,850 bytes/run matching between reproduce and profile, both full runs in same order. That does not establish candidate behavior.

**Read from code/documents: exact failure and selector distinction**

Contract `/home/hal/dev/interp/metis-wt/dut/pipeline/m5/SCHEMAS.md:54–56` requires exact measured command/environment/scale, program's own subset selection in argument order, native unit identity, same result paths and exit propagation. Line 56 says id is string “by which the published program selects that unit” and wrapper runs measured command “using the published program's own subset selection”. This is stronger than merely passing reduced input manifest to unchanged computation.

Corrected `run10_harness2/run_units.sh:113–122`:

```python
requested = sys.argv[10:]
keys = [pid + ":" + kind for pid, kind in zip(jobs["id"], jobs["kind"])]
# duplicate, regex and membership checks follow
jobs = jobs.iloc[[keys.index(key) for key in requested]]
jobs.to_csv(sys.argv[2], index=False)
```

Predict command at `:134–135` receives no requested ids:

```sh
"$VPY" "$VENV/bin/pinder_methods" predict --method "$METHOD" --data_dir data/frodock \
    --results_dir "$RESULTS" --subset pinder-s --pairs all --config "$RUN_DIR/frodock_config.yaml"
```

Published README `evidence/methods_README.md.txt:7–11` advertises prediction by id list. Source `evidence/main.py.txt:80–98` declares `ids`, `subset`, `pairs` and documents intended filtering. But **entire predict body**, lines 102–140, never reads these three parameters. Lines 122–136 select adapter by method, add data/results directories, read setup CSV and iterate **every** record. Applied patch `pinder_frodock_fixes.patch:3–20` repairs enum comparison and pandas reader only. Therefore adding documented `--ids` to this installed entry would not restrict existing manifest. `entry_point_has_subset_option=no` means **no effective published way through that option**, not absence of an advertised/accepted parameter. This resolves previous reports' “not established” using complete pinned source.

Preprocess really consumes `ids/pairs`: `evidence/main.py.txt:29–55` forwards them to `prepare_inference_inputs`; `evidence/preprocess.py.txt:22–30` selects system ids, then `:33–56` prepares monomer inputs and rows. It constructs set(ids), so arbitrary input order is not inherently retained. It does **not** call prediction or numerical FroDock stages. Setup invokes this route at `run9/agent/harness/setup.sh:3975–4004`, explicitly outside docking timing. Earlier reader claim `published_option` refers to this route (`run9_units/REPORT.md:56–60`; `run9_outputs/REPORT.md:56–69`), not effective predict filtering or acceptance of `ID:kind` tokens. Those compound strings are invented wrapper keys; native preprocessing takes system id plus separate pairing.

Registered entry `pinder_methods = "pinder.methods.main:main"` appears at `evidence/pyproject.toml.txt:36–45`; main dispatches preprocess/train/predict (`evidence/main.py.txt:143–156`). Pinned methods sources expose no second subset-selecting inference CLI for FroDock. Preprocess is another action, not equivalent per-unit computation. Published lower-level callable **does** exist: `predict_frodock(complex_config, params)` at `evidence/predict.py.txt:175–233`, with per-job docstring; it calls `frodock(...)`. Main dynamically dispatches exactly that function (`evidence/main.py.txt:122–125,135–136`). Thus another callable can perform identical numerical work. It is not a separate published subset selector/CLI: no id-list option, CLI driver or alternate published launch command. The `other_published_entry_same_computation=no` status concerns qualifying alternative subset-running entry, not denial that underlying callable exists. Invoking that callable from a new Python launcher changes measured entry and still leaves wrapper doing selection.

First harness generated private inputs via preprocess before selecting original records (`run10_harness/run_units.sh:108–134`; `run10_harness/REPORT.md:69–83`). First review identified extra action/output/timing work, compound id limitation and inherited absolute paths (`run10_review/REPORT.md:60–120`). Correction removed preprocessing and its signal conversion, preserving original inputs and numerical suffix. Second review correctly identifies remaining CSV-only mechanism (`run10_review2/REPORT.md:94–96`). Writer's `subset_mechanism=other` accurately describes that mechanism; it does not imply changed docking algorithm.

**Read from code: computation, paths, exits and write limits**

Same complete rows reach same `predict_frodock`; adapter extracts id/kind/input paths, solution count, MPI count and force (`evidence/predict.py.txt:209–233`). Applied patch resolves original relative inputs against unchanged data_dir (`pinder_frodock_fixes.patch:53–64`). Both wrappers create fresh result trees before prediction, avoiding force=false reuse (`run_command.sh:59–82`, run_units.sh:61–85).

Same eight native stages, SOAP input, eight MPI ranks and 50 retained solutions (`evidence/predict.py.txt:79–153`, patch `:33–40`). Per-job temporary directory and input staging at patch `:24–30`. Same final path formula at patch `:43–48`. Same wrapper chain repair/scoring suffix established bytewise. No per-unit parameter or native binary substitution found. Combined score/leaderboard CSVs depend on selected set and are intentionally absent from unit outputs.

No-id guard at corrected `:21`; duplicate/unsafe/unknown ids rejected at `:115–120`. Prediction status captured/returned at `:133–139`; scoring program status captured via `${PIPESTATUS[1]}` and returned at `:194–199`. No new exit-status failure found. Existing native adapter uses subprocess.run without check=True (`evidence/predict.py.txt:126–137`): wrapper propagates published entry's status, not independent guarantees for each native stage. Missing resulting PDBs still fail probe comparison.

Additional literal defect: baseline `run_command.sh:47,66` and corrected `run_units.sh:49,68` derive absolute run-local PATH/TMPDIR using $PWD. SCHEMAS:55 forbids absolute paths into run directory. This is concrete inherited path-rule mismatch, **not** evidence of writing outside out/temp. TMPDIR points inside private out/. Paths derive from each current invocation, so no demonstrated stale-root portability failure. Blindly making PATH relative can break native binary lookup after adapter chdir. Editing only unit environment also violates required baseline environment parity.

Conditional outside-out writes exist in dependencies: `run10_review2/saved_core_utils_excerpt.py.txt:24–26` creates release directory if missing; `:63–65` documents index download; `run10_review2/saved_eval_method_81_260.py.txt:163–171` creates/downloads missing native data. Baseline and candidate share PINDER_BASE_DIR=data. Prepared setup plus successful full reproduction do not establish that these branches run on next sibling invocation. Wrapper's explicit writes stay in out/, fresh native stage temp directory inherits TMPDIR, and bytecode disabled. No observed outside write or exhaustive dependency write trace here.

**Measured records, not new workload results**

Frozen reproduce log `run9/agent/results/reproduce/out/run_command/run_command.log`:

```text
:4 CONFIG method=frodock subset=pinder-s pairs=holo,apo n_jobs=16 n_solutions=50 mpi_np=8 force=False CUDA_VISIBLE_DEVICES='' host_nproc=26 PINDER_BASE_DIR=data
:7 2026-11-01 07:13:52,222 ... Running FroDock (50 solutions) on complex 1a19__A1_P11540--1a19__B1_P11540 holo ...
:700 2026-11-01 07:14:34,609 ... Copying the results to out/results/frodock/1a19__A1_P11540--1a19__B1_P11540/holo_decoys
:11116 PREDICT_EXIT=0
:11117 CHAIN_LABELS_RESTORED models=100 atoms=2700
:16201 EVAL_EXIT=0
```

Ellipses above omit logger prefix/input paths only. Existing log records successful full computation, not candidate subset success. Costs record Running FroDock → Copying results, excluding later repair/scoring (`run_anchors.sh:109–116,128–134`).

**Inferred: what probe catches and realistic risk**

Apply specified U50 protocol, SCHEMAS:102–113, not command-mode no-output-check rule at :100. Four-unit sample from current costs, zero-based manifest positions **3,5,9,15**, all apo: 1aua, 1ax2, 1dv1, 1nr5. Recorded docking-cost sum **1008.9430003166199 s**, not predicted total wall. Probe first runs all four in **one** invocation. Every one of their **200** listed PDBs must equal frozen full-run reproduce file byte for byte. Nonzero exit, missing file or differing byte prevents all later arms. A repeatable but wrong subset cannot pass merely by agreeing with itself. Later comparisons test separate/concurrent outputs against that frozen-validated a-1 reference.

This catches computational errors **when they alter compared sample outputs**. It cannot prove internal work identity: different intermediates, redundant/omitted work with unchanged final PDBs, changed unlisted scoring outputs, unsampled-unit problems or silent shared writes can escape output comparison. Output equivalence is not an execution trace. Hence `partly`, not universal yes. No such hidden altered-work mechanism demonstrated in this candidate; source shows same per-row calls and numerical parameters. Hypothetical equal-output differences alone do not establish misleading-result risk here.

Realistic evidenced failure mode is spending probe time then getting failed/baseline_mismatch/outputs_mismatch or no usable factor. `wasted_run` describes that risk; it does not claim failure measured, guarantee harmless shared state, or certify future factor. Actual outcome remains unknown. Neither concrete changed algorithm nor evidence that factor necessarily measures different numerical workload was found. A valid measured factor would concern these fixed sample units under complete wrapper invocation, including launch/validation/repair/scoring overhead; it would not establish improved scientific docking recovery.

Reviews' `same_computation_per_unit=unknown` combines established call-level parity with untested native/library/sequence state and bitwise invariance. Their `writes_only_out_or_temp=unknown` reflects untraced conditional dependency behavior. Static evidence supports intended computation, but cannot settle these future runtime properties. Selector noncompliance and absolute-path mismatch are concrete **separate** findings; neither proves different PDB computation or actual forbidden write. Therefore unknowns_reason=static_reading_limit.

**Smallest fix; no edits made outside this report**

No evidence-backed strict-contract repair confined to run_units.sh/units.json. Adding --ids leaves unused parameter; stripping pairing suffix creates duplicates; preprocessing adds timed work absent from measured command; new API launcher changes entry and still supplies wrapper-selected rows. Complete literal path-rule repair also conflicts with unchanged baseline environment.

Smallest change preserving intended experiment: owner explicitly permit ordered restriction of original prepared rows and wrapper `(system_id,kind)` identities in U50, and reconcile relative-path rule with existing cwd-derived PATH/TMPDIR. Current code could then retain same per-job calls, while required frozen/later-arm comparisons establish runtime output equality. This is contract change, not a claim current files comply, and was not performed. If native option requirement stays literal, add effective native selector, update/remeasure baseline as needed, then construct unit wrapper against that measured entry. Lower-level callable existence does not by itself satisfy existing exact-command rule. Omitting optional files avoids unit mode but does not deliver requested unit experiment and does not repair inherited path discrepancy.
