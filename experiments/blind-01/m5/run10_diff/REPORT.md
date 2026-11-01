Run10 differential assessment — 2026-11-01

Prepared-record selection route exists relative to **recorded run9 baseline**. Run9 already contains source patches, environment deviations and harness-written chain repair. Neither corrected harness2 selection nor input-list restriction requires another change to installed prediction code or selected units' explicit parameters/structural inputs. Pristine-upstream purity and measured-baseline parity are different comparisons.

Scope: read requested five REPORT.md/status.json pairs first; inspected relevant run9 harness, setup/anchors logs, applied patch, repair records, saved source, numerical YAML and prepared CSV. Local standard-library byte/CSV audit only. No workload, harness invocation, box contact, network fetch, git command, credential/.keys/~/.codex read. Writes confined to run10_diff/. Large trees inspected through named files and manifest-listed outputs; no profiler database, native intermediate tree or raw-decoy archive read.

Evidence labels: **Measured here** means comparisons of existing local files, not new docking runs. **Read** means source/configuration/log/document statements. **Inferred** means consequences. Paths relative to current experiment directory unless absolute. Log line numbers count LF separators, retaining embedded CR progress updates.

| Question | Answer | Status value |
| --- | --- | --- |
| 1. Baseline versus pristine upstream | Both source patches and configuration/environment choices. | baseline_vs_upstream=both |
| 2. Harness2 per-unit code difference reported by mech | Inherited from measured run9. Wrapper adds selection/validation, no new per-unit numerical/repair change. | harness2_change_origin=inherited |
| 3. Inputs report's published-code difference | Inherited from measured run9; input-list route needs no further published-source patch. | inputs_change_origin=inherited |
| 4. Command-line selector | ids/subset/pairs declared and exposed, ignored by prediction body; prepared CSV controls jobs. | cli_selector=present_ineffective |
| 5. Prepared list read | Yes, results_dir/frodock_setup.csv. | prepared_list_read=yes |
| 6. List redirectable | Yes through existing --results_dir. Measured wrapper already uses out/results, outside published tree. | list_redirectable=yes |
| 7. Original-record-only restricted list | Yes, exact original header plus selected original record bytes in requested order. | restricted_list_original_records=yes |
| 8. Inherited forbidden writes | No explicit wrapper write outside out/temp. Actual end-to-end dependency writes not fully established; no observed forbidden write proved. Absolute-path spelling conflict is definite but separate. | inherited_path_conflict=unknown |
| 9. New forbidden write from route | No. Selection writes only existing private out/results/frodock_setup.csv; source/data stay unchanged. | route_adds_path_conflict=no |
| 10. Selected-unit computation/result dependence | Unknown for final owned PDB bytes. Same explicit calls; native wall-clock seed and conditional random rotation prevent proving invariance. | selection_affects_unit_results=unknown; selection_effect_basis=code |
| 11. Full-run byte repeatability evidence | Two actual saved full runs compared, reproduce versus profile: 800/800 files equal. | full_run_repeatability_basis=two_runs_compared |
| 12. Narrow measured-baseline route | Yes, as record selection with installed measured program unchanged. Subset bitwise equivalence remains unmeasured. | narrow_route_exists=yes |

**Read: inherited baseline changes and their origin (questions 1–3).**

Run9 source pin: ebeb28a2f8411363cef722b7d293c978f7442672, source archive SHA-256 b577532820ebbe5c16432b78c5e9c197690e863cb70a0a35a8ebcbe5277b76dd (`run9/agent/results/reproduce/out/setup/setup_record.json:2–5`). Saved setup log explicitly records applying patch to both Python source files (`out/setup/setup.log:14–18`). Harness `setup.sh:208–213` copies applied patch record and applies it before installation; `setup.sh:275–286` installs patched source, fire, and refreshed dependencies.

Existing `run9/agent/harness/pinder_frodock_fixes.patch` changes:

| Patch lines | Existing baseline change |
| --- | --- |
| 3–20 | Enum comparison repaired; pd.from_csv replaced by pd.read_csv(Path(results_dir) / filename). |
| 24–30 | Original receptor/ligand copied into per-job temporary stage before chdir. |
| 33–40 | Native executable prefix gains trailing slash. |
| 43–48 | Literal wildcard shutil.copy replaced by sorted glob/copy loop. |
| 53–64 | Relative structural input paths resolved against data_dir. |

Patch SHA-256 295af03d22550b21c1e0852f723f324c35e9f5caa75e1759ba82bee5ed0259c3; **measured here** identical to `run9/agent/results/reproduce/out/setup/pinder_frodock_fixes.applied.patch` (`run10_diff/audit.py:29–30`). These are source changes, not merely configuration.

Environment/build deviations also explicitly recorded: fire dependency, SCM pretend version, --no-build-isolation, fresh networkx/pandas/scikit-learn with numpy<2 (`setup_record.json:16–22`). Measured representative configuration fixes eight systems, holo/apo, 50 solutions, eight MPI ranks, force false, eight scoring workers, CPU-only CUDA visibility (`run_command.sh:22–33,99–107`; `setup_record.json:36–50`). Numerical saved YAML `run9/agent/results/reproduce/out/run_command/frodock_config.yaml:1–3` is n_solutions: 50, mpi_np: 8, force: false. Baseline versus pristine upstream therefore **both**.

Additional inherited output-affecting harness code restores blank ligand HETATM chain labels, archives originals and validates chains (`run_command.sh:126–174`, especially :162–172). Actual successful baseline reports `CHAIN_LABELS_RESTORED models=100 atoms=2700` (`out/run_command/run_command.log:11117`), corroborated by saved `chain_labels_restored.json` and local audit.

Repair history distinguishes this from selection work. `run9/agent/wf/agents/0006-anchors-repair/codex-1.jsonl:98,185,260` records scoring chain failure and targeted chain repair. `0007-anchors-repair/codex-1.jsonl:85,165,223` records removing invalid atom-count assumption, retaining emitted-chain boundary and targeted HETATM correction; final record says 800 saved decoys validated. Earlier anchors attempt `run9/agent/results/reproduce/0112-anchors.log:11117–11129` reached prediction exit 0 but evaluation exit 1. Attempt `0114-anchors.log:11117–11120` reached prediction exit 0 then failed added atom-count check. Final `0116-anchors.log:11117–11118,16202–16203,16215` records prediction success, chain restoration, evaluation/command exit 0 and completion. Comparing failed attempts without their different repair states would not establish repeatability of final measured files.

`run10_mech/REPORT.md:3,12,67–90` itself states pristine-relative changes inherited; `run10_inputs/REPORT.md:17,99–101` states same. Their negative unmodified-code flags do **not** imply additional per-unit source edits for subsetting. Harness2 changes shell argument validation and selected CSV construction (`run10_harness2/run_units.sh:21,89–122`). **Measured here:** baseline environment :21–48 equals candidate :23–50; output setup :50–81 equals :52–83; entire prediction/chain-repair/scoring suffix :117–185 equals :132–200 byte for byte (`audit.py:18–31`, `audit.json`). Original run_command.sh copy also equals run9 bytes. Thus both origins **inherited**, while selection wrapper logic is necessarily new.

**Read: real selector and list location (questions 4–6).**

Pinned main source preserved at `run10_why/evidence/main.py.txt:80–98` declares ids/subset/pairs. Complete prediction body :102–140 never consumes them. Fire dispatch exposes predict at :143–151. Existing run9 patch only repairs enum/CSV calls; it does not add selection. Installed loop reconstructed directly from source and applied patch:

```python
config_dict["data_dir"] = data_dir
config_dict["results_dir"] = results_dir
inference_config = pd.read_csv(Path(results_dir) / f"{method}_setup.csv")
for complex_config in inference_config.to_dict("records"):
    predict_method(complex_config, config_dict)
```

Evidence: main source :130–136; run9 patch :13–20. Source archive identity and source-copy provenance recorded in `run10_why/REPORT.md:20–30` and `run10_inputs/audit.json`. FroDock adapter saved directly in run9 source-bearing event `0006-anchors-repair/codex-1.jsonl:103` matches `run10_inputs/evidence/predict.py.txt` ignoring trailing whitespace (**measured here**, `audit.py:58–73`). Installed absolute package paths and current loop call also appear in successful run9 log :20–35. Source copies are upstream bytes with applied patch interpreted separately, not mislabeled pristine installed code.

Preprocess consumes selection but belongs to setup: `run9/agent/harness/setup.sh:3975–4004` runs it separately for holo/apo, then sorts/combines records. It is explicitly excluded from docking timing. Re-running preprocess would regenerate inputs and add work; narrow route needs none.

Measured wrapper sets `RESULTS=out/results` and `RUN_DIR=out/run_command` (:51–52), then copies full prepared list (:82):

```sh
cp data/frodock/frodock_setup.csv "$RESULTS/frodock_setup.csv"
```

Measured prediction (:119–120):

```sh
"$VPY" "$VENV/bin/pinder_methods" predict --method "$METHOD" --data_dir data/frodock \
    --results_dir "$RESULTS" --subset pinder-s --pairs all --config "$RUN_DIR/frodock_config.yaml"
```

Hence list location derives from already accepted --results_dir, not fixed path inside baseline-published/. It already is invocation-private out/results/frodock_setup.csv; no redirect flag needs adding and no results relocation needed. Supplying another results_dir could relocate it, but keeping measured out/results preserves exact required output paths. YAML ids cannot override loop; adding --ids leaves same prepared rows running. Entire unedited run_command.sh would overwrite any prior restricted target and insists on full universe; insertion must follow full validation, before prediction.

**Measured here and read: original records (question 7).**

Frozen `run9/agent/results/reproduce/out/results/frodock_setup.csv:1–17` has header `id,kind,receptor,ligand`, 16 one-line records, all original field values. For example :2 holo and :3 apo of 1a19 use original relative `.../inputs/<kind>/1a19_<kind>_{R,L}.pdb` spellings. Source full list is `data/frodock/frodock_setup.csv`, copied by baseline; frozen output is surviving recorded copy. Original full data tree/input PDBs are not retained here for independent fresh input hashing.

`audit.py:33–46` checked each singleton and reversed four-record selection in memory. Original header plus original raw lines parse to exactly selected original dictionaries, in requested order. All 17 cases pass. No CSV reserialization needed. Existing harness2 uses pandas serialization (:121–122), preserving values but not promising raw row bytes; byte-copy variant below satisfies stricter byte-for-byte requirement without modifying predictor.

**Read and inference: writes and path-rule distinction (questions 8–9).**

Every explicit measured wrapper write is under out/: histories/results moves/log tee :50–66; YAML :75–81; list :82; repair/archive/manifest :132–174; scorer --eval_dir out/results :180. Adapter creates fresh tempfile directory, stages inputs there, runs native stages there, restores cwd and copies models into results_dir (`run10_inputs/evidence/predict.py.txt:54–57,91–172`; applied patch :24–30,43–48). TMPDIR is invocation out/tmp (`run_command.sh:65–66`), PYTHONDONTWRITEBYTECODE=1 (:48). No direct measured wrapper write inside published source/install tree found. Setup does write/install there, explicitly separate stage; it is not run by run_command.sh.

End-to-end absence of inherited forbidden writes cannot be established from available records. `run10_review2/saved_core_utils_excerpt.py.txt:24–26,62–65` conditionally creates data release directory/downloads absent index; evaluator `run10_inputs/evidence/eval_method.py.txt:231–251` creates native.parent and downloads absent natives. Prepared setup likely avoids these branches; no write trace establishes that for every dependency. Therefore inherited_path_conflict **unknown** for forbidden-write question, while direct shell writes are statically confined. This is not affirmative evidence of a forbidden write.

Separate definite inherited *absolute-path spelling* conflict: `run_command.sh:47` exports `$PWD/baseline-published/frodock/bin:$PWD/$VENV/bin:$PATH`, :66 exports `$PWD/out/tmp`. SCHEMAS.md:55 at `/home/hal/dev/interp/metis-wt/dut/pipeline/m5/SCHEMAS.md` prohibits absolute run-local paths. PATH contains read locations; TMPDIR still points inside out/. Neither export proves a forbidden write. Prior strict contract failures at `run10_review2/REPORT.md:73–82` and `run10_inputs/REPORT.md:180–185` include this inherited wording conflict; it should not be recast as new selection write. No path/environment repair attempted.

Restricted-list route adds one write to **existing out/results/frodock_setup.csv only**. Original data/prepared structures, index, SOAP file, binaries and installed source untouched. Same suffix/dependencies remain; no new missing-native/index demand introduced by removing rows. Thus route_adds_path_conflict **no**, without asserting complete baseline dependency confinement. Any inherited cache/download behavior remains baseline limitation for owner to judge separately.

**Read from code and inference: selected-unit effects (question 10).**

Same row supplies id/kind/receptor/ligand; same parameter dict supplies results_dir/50/8/false (`run10_inputs/evidence/predict.py.txt:209–233`; patch :53–64). Each job has fresh temporary directory and native subprocesses. Same eight stages and SOAP file remain (:91–137); pose assembly/ranking :139–166 and path :169–172 use current unit, not job count/index. No cross-record mean, shared docking RNG, set-based seed, shuffle or parameter mutation appears in shown prediction driver/adapter. Fresh results tree prevents force=false cache skip (`run_command.sh:59–82`; adapter :218–223). Unchanged chain repair reads current row/model only (:140–171).

Concrete remaining dependence: receptor/ligand desolvation grids use -m 3 (adapter :100–106). Grid MPI code calls ASA::localSAS (`run10_inputs/evidence/frodockgrid.cpp.txt:395–427`). SAS routine seeds generator from wall clock:

```cpp
int32 seed = (int32)time(0);        // random seed
CRandomMersenne rg(seed);
```

`run10_inputs/evidence/sas.cpp.txt:683–690`, with conditional random geometry rotation :747–759, `spheres_rotation(..., rg.Random())`, before area computation. Generator seeding executes 37 BRandom calls (`mersenne.h.txt:173–183`). Grid copies SAS area into occupancy (:456–458); adapter docking consumes resulting ASA PDBs (:109–110). Build uses MPI_RELEASE and links lsas_gcc (`grid_MPI_GCC_subdir.mk.txt:20`, `grid_MPI_GCC_objects.mk.txt:7`); setup compiles archived tools (`setup.sh:225–242`, saved setup log :21–25). Native source provenance/digests preserved in `run10_inputs/audit.json`, tied to setup's recorded archive. No new native/source identity claim against original study mirror is made.

**Inference:** removing/reordering earlier records can change launch seconds and seed. Whether selected structures enter conditional rotation, whether arithmetic changes survive file precision, or whether any selected final model differs remains unknown. This dependence already exists between ordinary full runs; selection adds no new RNG policy. Code supports caveat, not measured mismatch. Therefore selection_affects_unit_results=unknown, selection_effect_basis=code.

Scorer combines metrics and applies missing-system penalties; shared metrics/leaderboard generally change with selected set (`eval_method.py.txt:376–393,423–482,601–631`; `run10_review2/saved_eval_run.py.txt:94–100`). These shared CSVs are not unit-owned files. No shown scoring path writes final PDBs or feeds aggregation back into docking. Normal file/OS caches can change cost; no isolated/reordered/concurrent execution evidence supplied here.

**Measured here: two real full runs compared (question 11).**

Read exactly 800 manifest-listed PDB paths from both `run9/agent/results/reproduce/out/` and `run9/agent/results/profile/out/`. Direct byte equality passed **800/800**, **342,779,850 bytes per run**. Full setup CSVs also match. `audit.py:45–56` performs direct byte comparison, not merely hash equality; `audit.json` preserves each path, byte count and SHA-256.

Both command logs show same full configuration at :4 and 16 start markers. Reproduce first start :7 = 2026-11-01 07:13:52,222; completion :11115 = 08:29:28,603. Profile first start :7 = 10:47:05,978; completion :11115 = 12:18:25,028. Both :11116 prediction exit 0, :11117 chain repair 100 models/2700 atoms, :16201 evaluation exit 0. Different start times and full marker sequences support two actual executions; this is not source-only determinism reasoning. Profile is instrumented full execution, not second unprofiled replicate. Both preserve same record order; no subset/reorder guarantee follows. Earlier 800/800 comparison at `run10_review2/REPORT.md:63` independently agrees.

**Exact prospective run_units.sh route (question 12).**

Copy measured wrapper into run_units.sh. Add early nonempty argument check. Preserve environment/output initialization, full original CSV copy and full universe validation (:21–115). Immediately after :115 and before unchanged prediction suffix :117–185, select complete original records at existing private target. Keep installed source, binaries, data_dir, all YAML values, launch flags, chain repair, scoring workers, output formulas and exit propagation unchanged. No preprocess step, direct internal-function launcher, published source edit, new seed or new environment setting.

Illustrative insertion, **design only; not installed or executed as workload here**:

```sh
"$VPY" - "$RESULTS/frodock_setup.csv" "$@" <<'PY'
import csv
import io
from pathlib import Path
import re
import sys

target = Path(sys.argv[1])
requested = sys.argv[2:]
if not requested or len(set(requested)) != len(requested):
    sys.exit("ERROR: provide distinct system_id:kind keys")
raw = target.read_bytes().splitlines(keepends=True)
rows = list(csv.DictReader(io.StringIO(b"".join(raw).decode("utf-8"))))
if not rows or list(rows[0]) != ["id", "kind", "receptor", "ligand"]:
    sys.exit("ERROR: unexpected prepared manifest schema")
if len(raw) != len(rows) + 1:
    sys.exit("ERROR: expected original one-line-per-record format")
keys = [r["id"] + ":" + r["kind"] for r in rows]
if len(set(keys)) != len(keys):
    sys.exit("ERROR: duplicate prepared unit")
if any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:+=-]{0,127}", k)
       or k not in keys for k in requested):
    sys.exit("ERROR: unknown or invalid requested unit")
target.write_bytes(raw[0] + b"".join(raw[keys.index(k) + 1] for k in requested))
print("RESTRICTED_UNITS=" + ",".join(requested))
PY
```

Full CONFIG print would still describe validated source universe; added RESTRICTED_UNITS line identifies actual selected records. `system_id:kind` is wrapper key mapping to original separate fields, not falsely claimed native --ids value. Requested order becomes CSV/prediction order. Selection mutates only target file already written by measured wrapper; resulting selected output paths remain `out/results/frodock/<id>/<kind>_decoys/model_1.pdb` through model_50.pdb.

What writes outside out/temp? Selection: **nothing**. Explicit retained wrapper/adapter operations: none identified. Entire retained dependency execution: unknown inherited conditional cache/download behavior described above. New wrapper selection code is required, but no new measured program/per-unit code patch is required. Narrow contract permits original-record selection and judges inherited baseline conflicts separately, so operational route **yes**; this does not certify bitwise subset results before required comparison or erase existing baseline limits.
