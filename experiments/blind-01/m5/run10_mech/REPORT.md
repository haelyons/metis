Run10 mechanism assessment — 2026-11-01

Mechanism: wrapper restricts prepared CSV records, then invokes the same measured prediction entry, repair code and evaluator. It does not directly call internal functions, replace prediction with native executables, or reimplement docking. Published Python entry remains the same **run9-patched** entry. Literal claim that every executed per-unit line is unmodified upstream code is false: run9 already applies adapter fixes and performs harness-written PDB chain repair. Candidate adds no further per-unit source changes.

Scope: read requested `run10_why/`, `run10_review2/` and `run10_harness2/` reports/status first, plus candidate script, then selected saved source, harness, timing records and manifest. Writes confined to `run10_mech/`. No workload or harness invocation, box contact, network access, git command, credential, `.keys` or `~/.codex/` read. No model contents, raw-decoy archives or profiler databases read. Paths below relative to experiment directory. Log line numbers count LF bytes; embedded CR progress updates do not add lines.

Evidence types: **Measured here** means local byte comparison or arithmetic over saved records, never a new docking measurement. **Read** means code/document/record statements. **Inferred** means conclusions from that evidence. Future subset, isolated and concurrent execution results remain unknown.

| Question / status key | Answer and scope | Value |
| --- | --- | --- |
| 1 / mechanism | Ordered CSV restriction before the original CLI. Shell wrapper is adapted; published Python entry is not replaced or copied for selection. | other |
| 2 / per_unit_code_unmodified | No, literally relative to pristine published source. Existing run9 adapter patches and harness repair remain. Relative to measured run9 per-unit code, no new change found. | no |
| 3 / non_unit_share | Under 5% of the measured full command. Conservative reproduce residual bound about 2.09%; includes more than strictly shared work. Provisioning/setup.sh lies outside that command. | under_5pct |
| 4 / skipped_steps_affect_unit_files | For requested units, no computation stage removed; repair and shared scoring also remain. Unrequested units omitted; shared score contents change with selected set. | no_steps_skipped |
| 5 / partial_catch_reason | Final PDBs omit intermediate and evaluation results; identical PDB bytes cannot establish equal cost. | both |
| 6 / cost_check_possible | Yes, compare the same per-job start/copy intervals in later serial logs. Whole invocation seconds have a broader scope. Agreement corroborates comparable work, not proof of execution identity. | yes |

**Read: exact mechanism and relation to published computation**

`run10_harness2/run_units.sh:88–110` reads the original full `data/frodock/frodock_setup.csv` and validates the fixed universe/configuration. Lines 113–122 select complete original rows, preserving requested order:

```python
requested = sys.argv[10:]
keys = [pid + ":" + kind for pid, kind in zip(jobs["id"], jobs["kind"])]
# Lines 115–120 reject duplicate, unsafe and unknown keys and prior validation errors.
jobs = jobs.iloc[[keys.index(key) for key in requested]]
jobs.to_csv(sys.argv[2], index=False)
```

The result replaces the original wrapper's full-manifest copy (`run9/agent/harness/run_command.sh:82`) at the same `out/results/frodock_setup.csv` path. Compound `system_id:kind` keys are wrapper keys; predictor receives original separate `id`, `kind`, `receptor`, `ligand` columns. Input PDBs are not regenerated. CSV serialization changes representation, not selected field values.

Candidate lines 134–135 still invoke:

```sh
"$VPY" "$VENV/bin/pinder_methods" predict --method "$METHOD" --data_dir data/frodock \
    --results_dir "$RESULTS" --subset pinder-s --pairs all --config "$RUN_DIR/frodock_config.yaml"
```

No requested identifiers reach this command. Saved upstream `run10_why/evidence/main.py.txt:80–98` declares/documents ids/subset/pairs, but the entire body at 102–140 does not consume them. Lines 122–125 import `pinder.methods.run.frodock.predict` and obtain `predict_frodock`; lines 130–136 set directories, read setup CSV and loop over every record. Run9 patch corrects enum handling and CSV reader, retaining that loop (`run9/agent/harness/pinder_frodock_fixes.patch:3–20`):

```python
inference_config = pd.read_csv(Path(results_dir) / f"{method}_setup.csv")
for complex_config in inference_config.to_dict("records"):
    predict_method(complex_config, config_dict)
```

**Inferred classification:** `other` describes input-manifest restriction through the same CLI. Internal calls happen inside the original program, not through a new internal-API launcher. Native FroDock executables remain downstream calls of that program, not an alternative selector. `run_units.sh` is a modified copy of the measured shell wrapper; this does not make it a modified copy of the published Python entry point. No new docking implementation exists in the selection block. This distinguishes these meanings of “entry point” without asserting that the wrapper satisfies the earlier published-subset-option contract. `run10_why/REPORT.md:38–63` and `run10_review2/REPORT.md:94–96` make that contract distinction.

**Measured here: parity with measured baseline**

Byte comparisons established:

| Baseline `run9/agent/harness/run_command.sh` | Candidate `run10_harness2/run_units.sh` | Result |
| --- | --- | --- |
| 21–48, complete environment | 23–50 | Identical |
| 50–81, output setup/configuration | 52–83 | Identical |
| 117–185, entire prediction/repair/scoring suffix | 132–200 | Identical |

Harness patch also equals saved `run9/agent/results/reproduce/out/setup/pinder_frodock_fixes.applied.patch` byte for byte. These measurements establish retained code/commands, not candidate runtime output equality or a fresh audit of installed native binaries.

**Read: per-unit code and the literal unmodified-code question**

`run10_why/evidence/predict.py.txt:209–233` extracts per-row fields/configuration and calls `frodock`; lines 218–223 skip an already existing model only when force is false. Both wrappers move old results aside and create fresh result trees (`run_command.sh:59–82`, candidate `:61–85`). No new cached-decoy shortcut added.

Adapter lines 54–89 create a fresh temporary directory, resolve executables and form MPI command. Lines 91–137 execute eight native stages: four potential maps, docking, clustering, visualization, coordinate generation. Lines 139–166 assemble/rename ranked receptor–ligand poses and restore cwd. Same configuration remains 50 solutions, eight MPI ranks, force false; same SOAP input and native docking parameters remain. Model path depends on id/kind, not selected-set position (`:169–172`, patched below). Grids and clustering occur per job; no shown cross-unit selection determines its 50 PDB poses.

However, literal **all lines unmodified upstream** is disproved by retained run9 fixes:

| Patch lines in `run9/agent/harness/pinder_frodock_fixes.patch` | Existing change |
| --- | --- |
| 3–20 | Repair action enum comparison and `pd.from_csv` to `pd.read_csv(Path(...))` in published main. |
| 24–30 | Copy original receptor/ligand into job temporary directory before chdir. |
| 33–40 | Repair executable prefix by appending `/`. |
| 43–48 | Replace wildcard `shutil.copy` with sorted glob/copy loop. |
| 53–64 | Resolve relative receptor/ligand paths against data_dir. |

Example changed per-unit lines:

```python
# Patch 28–29, new upstream-relative input staging:
for _src in (complex_receptor, complex_ligand):
    shutil.copy(Path(_src).absolute(), output_dir / Path(_src).name)
# Patch 47–48, changed result copy:
for _model in sorted(output_dir.glob("*.pdb")):
    shutil.copy(_model, results_path_complete)
```

Setup applies this patch before installation (`run9/agent/harness/setup.sh:208–212`); frozen setup record identifies source pin `ebeb28a2f8411363cef722b7d293c978f7442672` and recorded fixes (`run9/agent/results/reproduce/out/setup/setup_record.json:2–5,16–22`). Candidate uses that same environment, not a fresh pristine upstream installation.

Additionally, harness-written repair is per-unit, output-affecting code: baseline `run_command.sh:132–174`, identical candidate `:147–189`. It archives affected originals, restores blank ligand HETATM chain labels and validates chains. Candidate `:179–183` edits PDB column 22 and writes the PDB back. This is retained baseline repair, not published adapter code. Thus `per_unit_code_unmodified=no` has a concrete meaning; it must not be read as a newly changed docking procedure in candidate. Complete native/library source identity and sequence-state behavior remain unaudited.

**Read: full command work beyond docking; no selected-unit stage omitted**

Full measured wrapper performs environment/tool checks, output history preservation, fresh output/temp tree creation, YAML writing, full CSV copy, index/universe/configuration validation, diagnostic/version printing, serial prediction over 16 rows, chain repair/archive/manifest, then published evaluation with eight workers (`run_command.sh:21–115,117–185`). Candidate retains those stages for selected rows, replacing only manifest copy/selection logic and adding argument checks. Its entire prediction-through-evaluation suffix matches baseline bytes.

Published prediction itself loads YAML, dispatches adapter, reads records, loops and logs completion (`run10_why/evidence/main.py.txt:102–138`). It does not combine docking outputs across units. Published evaluator validates coverage and chains, computes metrics and writes combined CSVs and leaderboard (`run10_review2/saved_eval_run.py.txt:85–100`). Saved coverage code enumerates expected subset/monomer counts and asks whether missing systems should receive penalties (`saved_eval_method_81_260.py.txt:57–72,124–148`). Both wrappers pipe `yes y` to evaluator and retain missing-system penalties (`run_command.sh:176–184`, candidate `:191–199`).

**Inferred:** cross-unit coverage, penalties, metrics table and leaderboard change when fewer units are present. They are still computed; this mechanism does not bypass aggregation. No shown aggregation feeds back into model PDB generation or repair. For selected units no step is omitted, hence `no_steps_skipped`; omission of unrequested rows is the subset operation itself. This is static stage retention, not a guarantee against unobserved sequence/cache effects on future outputs.

Initial provisioning and published input preprocessing occur separately in `setup.sh:3975–4004`, explicitly “excluded from docking timing.” Frozen setup record `:52–53` reports 12 seconds preprocessing and 239 seconds total setup. Neither full measured `run_command.sh` nor candidate reruns that setup. `non_unit_share` below concerns the measured command, not setup-plus-command lifecycle; initial setup time cannot be silently charged as omitted candidate work.

**Measured here from saved timing records: non-unit share under 5%**

Run9 own-cost definition: logger timestamp “Running FroDock” to “Copying the results” (`run9/agent/results/reproduce/out/anchors_details.json:6`; parser `run9/agent/harness/run_anchors.sh:109–116,128–134`). Includes adapter staging/native stages/pose assembly; ends before copy-out completion, later repair, evaluation and wrapper overhead. All 16 manifest costs exactly equal corresponding frozen details costs. Sum is **4536.183000564575 s** (`anchors_details.json:441`); independently summing timestamp differences gives **4536.183 s**, rounding difference from epoch-float subtraction only.

Saved enclosing reproduce anchors invocation:

```text
run9/agent/results/reproduce/out/run_anchors.log:1
== run_anchors.sh start 2026-11-01T07:13:43Z
run9/agent/results/reproduce/out/run_anchors.log:16215
== run_anchors.sh done 2026-11-01T08:30:56Z
```

Enclosing duration **4633 s**; residual **96.816999435425 s**, **2.0897258674%**. `run_anchors.sh:29–40,166` places measured command inside these markers, followed by anchor parsing. Residual includes copy completion, per-unit repair/scoring as well as shared work and external anchor parsing. It is therefore a conservative bound for strictly non-unit work, not an exact measurement of aggregation alone. Second-resolution markers do not threaten the 5% boundary. For command duration T inside enclosure and fixed observed own intervals C, `(T-C)/T <= (4633-C)/4633`; using enclosure cannot understate this residual fraction.

Supporting frozen command-log lines, path `run9/agent/results/reproduce/out/run_command/run_command.log`:

```text
:4 CONFIG method=frodock subset=pinder-s pairs=holo,apo n_jobs=16 n_solutions=50 mpi_np=8 force=False CUDA_VISIBLE_DEVICES='' host_nproc=26 PINDER_BASE_DIR=data
:7 2026-11-01 07:13:52,222 | pinder.methods.run.frodock.predict:50 | INFO : Running FroDock (50 solutions) on complex 1a19__A1_P11540--1a19__B1_P11540 holo [input paths omitted]
:700 2026-11-01 07:14:34,609 | pinder.methods.run.frodock.predict:173 | INFO : Copying the results to out/results/frodock/1a19__A1_P11540--1a19__B1_P11540/holo_decoys
:11114 2026-11-01 08:29:28,591 | pinder.methods.run.frodock.predict:173 | INFO : Copying the results to out/results/frodock/1nr5__A1_P07547--1nr5__A2_P07547/apo_decoys
:11115 2026-11-01 08:29:28,603 | pinder.methods.main:137 | INFO : Success! Finished docking 16 systems
:11116 PREDICT_EXIT=0
:11117 CHAIN_LABELS_RESTORED models=100 atoms=2700
:16200 2026-11-01 08:30:28,159 | pinder.eval.dockq.method:461 | ERROR : frodock is missing 127 systems from pinder_af2 predicted
:16201 EVAL_EXIT=0
```

Independent supporting calculation on profile run: its own start/copy intervals in `run9/agent/results/profile/out/run_command/run_command.log` sum **5478.801 s**. Saved profile wall **5621.4601993279975 s** (`profile/out/profile/raw_wall_s.json:1`) leaves **142.659199328 s**, **2.537760551%**, also below 5%; profiler overhead is included in this broader residual. No reproduce cost was subtracted from profile wall. Exact time spent in each shared substage remains unknown; category is established by the reproduce bound without that breakdown.

**Read and inferred: why frozen byte comparison catches only partly**

Measured here: manifest has 16 units, each listing 50 final `model_*.pdb` files. Example `run10_harness2/units.json:4–57` lists ranks 1–50 for first unit. It does not list temporary grids/search/clustering files, native scores, repair archives/manifest, evaluator metrics or leaderboard. Adapter creates grids, `dock.dat`, `clust_dock.dat` and transformed coordinates (`run10_why/evidence/predict.py.txt:91–153`); evaluator writes scientific metrics separately (`saved_eval_run.py.txt:94–100`). Thus listed files do not cover everything computed for a unit.

Specified probe first compares each sampled unit's 50 final files against frozen reproduce outputs, stopping on missing/different bytes or failure. It would catch a changed sampled final structure, rank, chain label or other compared byte. Agreement across later arms then refers to that frozen-validated first subset result. No candidate comparison has yet happened. Earlier 800/800 full-run reproduce/profile equality is a prior measurement reported in `run10_review2/REPORT.md:63`, not evidence of subset success, and not repeated here.

Even complete equality of listed files does not prove same computational cost: changes to grid/search effort, repeated or omitted redundant operations, temporary I/O, process startup or cache behavior can preserve final PDBs. This is a logical limitation, not evidence that candidate makes any such numerical shortcut. Unchecked evaluator/intermediate results and unchanged-output cost differences both apply, hence `partial_catch_reason=both`. Four-unit sampling also leaves unsampled units untested.

**Read and inferred: feasible later serial-cost check**

`cost_check_possible=yes`: future serial candidate logs retain the same published start/copy markers because prediction code/logging is retained. For each sampled `(id,kind)`, subtract timestamp of “Running FroDock” from “Copying the results”, then compare with that unit's `units.json cost_s`. Require one matching start/end and same retained configuration. Compare each unit separately and their sum; do not substitute entire invocation wall time for this narrower interval.

For four sample positions stated in `run10_why/REPORT.md:94` (zero-based 3,5,9,15), independently read costs and baseline marker lines are:

| Unit | Manifest cost line | cost_s | Frozen command log start/copy lines |
| --- | ---: | ---: | --- |
| `1aua__A1_P24280--1aua__A2_P24280:apo` | 225 | 207.37600016593933 | 2132 / 2825 |
| `1ax2__A1_P16404--1ax2__A2_P16404:apo` | 337 | 235.1909999847412 | 3520 / 4213 |
| `1dv1__A1_P24182--1dv1__B1_P24182:apo` | 561 | 241.19400000572205 | 6264 / 6941 |
| `1nr5__A1_P07547--1nr5__A2_P07547:apo` | 897 | 325.1820001602173 | 10421 / 11114 |

Sum **1008.9430003166199 s**, docking intervals only. Future sum is unknown. Use equivalent machine/resource allocation and serial conditions; concurrent timings include contention. Whole serial invocation includes repeated startup, CSV validation, output work, repair and evaluator/missing-case handling; those costs can differ with grouping even with identical docking intervals. Saved full-run residual under 5% does not establish the same fraction for one-unit invocations.

Agreement of comparable serial intervals would support same approximate per-unit workload size alongside retained-code inspection and byte checks. It cannot prove identical instruction counts or hidden work: elapsed time varies with machine load, caching and measurement conditions, and different work may take similar time. No acceptance tolerance or future equality is fabricated here. Native instruction-level work, future output identity, and exact shared-stage timing remain unknown.
